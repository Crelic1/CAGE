"""Trial termination classification.

Maps a trial's exit conditions onto a stable ``TerminationInfo`` verdict
(status / reason / source). Value types live in :mod:`termination_model`;
proxy-log signals in :mod:`proxy_signals`.
"""
from __future__ import annotations

from cage.contracts.agent_output import agent_failure_first_line
from cage.contracts.exceptions import (
    AgentSetupError,
    BenchmarkError,
    CageInterrupt,
    ConfigError,
    ContainerError,
    ProxyError,
    ScoringError,
    TargetError,
    TrialError,
    TrialTimeout,
)
from cage.contracts.trial_phase import TrialPhase
from cage.experiment.engine.termination_model import (  # re-exported
    TerminationInfo,
    TerminationReason,
    TerminationSource,
    TerminationStatus,
)
from cage.experiment.engine.proxy_signals import (  # classify_upstream_error re-exported
    RoundBudgetUsage,
    _last_proxy_error_signal,
    _proxy_budget_usage,
    _proxy_round_budget_usage,
    classify_upstream_error,
)


__all__ = [
    "TerminationInfo",
    "TerminationReason",
    "TerminationSource",
    "TerminationStatus",
    "_token_cost_budget_termination",
    "cancelled_before_start_termination",
    "classify_trial_termination",
    "classify_upstream_error",
    "completed_termination",
    "looks_like_model_timeout",
    "max_cost_reached_termination",
    "max_input_tokens_reached_termination",
    "max_output_tokens_reached_termination",
    "max_rounds_reached_termination",
    "target_unavailable_termination",
    "termination_info_from_exception",
    "user_interrupted_termination",
]


def completed_termination() -> TerminationInfo:
    return TerminationInfo(
        status=TerminationStatus.COMPLETED,
        reason=TerminationReason.COMPLETED,
        detail="Task finished",
        source=TerminationSource.AGENT,
    )


def user_interrupted_termination() -> TerminationInfo:
    return TerminationInfo(
        status=TerminationStatus.INTERRUPTED,
        reason=TerminationReason.USER_INTERRUPTED,
        # Signal-agnostic on purpose: this path covers Ctrl+C *and* a plain
        # ``kill``/``pkill`` (SIGTERM) of the run. Naming only Ctrl+C made a
        # SIGTERM-killed trial read as something the user never did.
        detail="Interrupted before the agent finished",
        source=TerminationSource.USER,
    )


def cancelled_before_start_termination() -> TerminationInfo:
    return TerminationInfo(
        status=TerminationStatus.CANCELLED,
        reason=TerminationReason.CANCELLED_BEFORE_START,
        detail="Run interrupted before this trial started",
        source=TerminationSource.USER,
    )


def target_unavailable_termination(detail: str) -> TerminationInfo:
    """The external target stack failed to launch — agent exec was skipped."""
    return TerminationInfo(
        status=TerminationStatus.FAILED,
        reason=TerminationReason.TARGET_UNAVAILABLE,
        detail=detail or "Target failed to launch",
        source=TerminationSource.ORCHESTRATOR,
    )


def _round_budget_phrase(usage: RoundBudgetUsage, max_rounds: int) -> str:
    """Describe a budget hit without collapsing counters into each other.

    ``{billed}/{max_rounds} upstream calls`` is the comparison the proxy
    actually made — the old ``476/500`` reported root rounds over the budget
    and so read as an agent that stopped 24 rounds early, when it had in fact
    exhausted the budget exactly.

    The breakdown follows only when there is one, and names each part in the
    reader's terms: "3 compaction, 21 tool-side calls" says what was spent on
    folding up context and what a tool spent on the agent's behalf, where the
    lumped "24 auxiliary/compaction" invited reading it as 24 compactions.
    Parts that are zero are left out; what remains always sums to ``billed``.
    """
    phrase = f"{usage.billed}/{max_rounds} upstream calls"
    if usage.root_rounds <= 0 or usage.billed <= usage.root_rounds:
        return phrase
    parts = [f"{usage.root_rounds} root round{'' if usage.root_rounds == 1 else 's'}"]
    if usage.compaction:
        parts.append(f"{usage.compaction} compaction")
    if usage.tool_side:
        parts.append(
            f"{usage.tool_side} tool-side call{'' if usage.tool_side == 1 else 's'}"
        )
    return f"{phrase} ({', '.join(parts)})"


def max_rounds_reached_termination(detail: str = "") -> TerminationInfo:
    """Agent hit its configured per-trial round budget — natural stop.

    Treated as a *valid* outcome (status=completed) so resume keeps it.

    Two paths emit this:

    1. **Agent-side** — benchmark or per-agent output parser recognizes
       the agent's max-rounds marker (e.g. a sentinel line in stdout)
       and constructs this termination explicitly.

    2. **Classifier-side** — :func:`classify_trial_termination` detects
       it structurally from on-disk artifacts: admitted proxy calls
       (successful, minus tagged compact rewrites) >= max_rounds with a
       non-zero exit. The in-container proxy enforces the budget by
       403-rejecting the next request, but the rejection short-circuits
       *before* ``ProxyRecorder.record()`` and is therefore not in
       proxy.jsonl itself — the admitted-call count is the structural
       signal, and it is the enforcer's own counter, so subagent,
       auxiliary and compaction calls count exactly as they did when the
       budget was spent. Upstream failures do not.

    The classifier check runs before the upstream-error scan so a stray
    transient 5xx mid-run can't outvote a deterministic budget hit.
    """
    return TerminationInfo(
        status=TerminationStatus.COMPLETED,
        reason=TerminationReason.MAX_ROUNDS_REACHED,
        detail=detail or "Agent reached the configured max-rounds budget",
        source=TerminationSource.AGENT,
    )


def max_input_tokens_reached_termination(detail: str = "") -> TerminationInfo:
    return TerminationInfo(
        status=TerminationStatus.COMPLETED,
        reason=TerminationReason.MAX_INPUT_TOKENS_REACHED,
        detail=detail or "Agent reached the configured input-token budget",
        source=TerminationSource.AGENT,
    )


def max_output_tokens_reached_termination(detail: str = "") -> TerminationInfo:
    return TerminationInfo(
        status=TerminationStatus.COMPLETED,
        reason=TerminationReason.MAX_OUTPUT_TOKENS_REACHED,
        detail=detail or "Agent reached the configured output-token budget",
        source=TerminationSource.AGENT,
    )


def max_cost_reached_termination(detail: str = "") -> TerminationInfo:
    return TerminationInfo(
        status=TerminationStatus.COMPLETED,
        reason=TerminationReason.MAX_COST_REACHED,
        detail=detail or "Agent reached the configured cost budget",
        source=TerminationSource.AGENT,
    )


def _token_cost_budget_termination(
    proxy_jsonl_path: object,
    *,
    max_input_tokens: int | None = None,
    max_output_tokens: int | None = None,
    max_cost: float | None = None,
) -> TerminationInfo | None:
    usage = _proxy_budget_usage(proxy_jsonl_path)
    input_tokens = int(usage.get("input_tokens", 0) or 0)
    output_tokens = int(usage.get("output_tokens", 0) or 0)
    cost_usd = float(usage.get("cost_usd", 0.0) or 0.0)

    if max_input_tokens is not None and max_input_tokens > 0 and input_tokens >= max_input_tokens:
        return max_input_tokens_reached_termination(
            f"Hit input-token budget - {input_tokens}/{max_input_tokens} tokens used; "
            "proxy 403-rejected the next call"
        )
    if (
        max_output_tokens is not None
        and max_output_tokens > 0
        and output_tokens >= max_output_tokens
    ):
        return max_output_tokens_reached_termination(
            f"Hit output-token budget - {output_tokens}/{max_output_tokens} tokens used; "
            "proxy 403-rejected the next call"
        )
    if max_cost is not None and max_cost > 0 and cost_usd >= max_cost:
        return max_cost_reached_termination(
            f"Hit cost budget - ${cost_usd:.4f}/${max_cost:.4f} used; "
            "proxy 403-rejected the next call"
        )
    return None


def classify_trial_termination(
    *,
    exit_code: int,
    timed_out: bool,
    terminated_by_limit: bool,
    terminated_by_max_rounds: bool = False,
    error: str = "",
    timeout_seconds: int | float = 0,
    output: str = "",
    exception: BaseException | None = None,
    proxy_jsonl_path: object = None,
    max_rounds: int = 0,
    max_input_tokens: int | None = None,
    max_output_tokens: int | None = None,
    max_cost: float | None = None,
    interrupted: bool = False,
    error_type: str = "",
    failed_phase: str = "",
) -> TerminationInfo:
    """Classify raw execution signals into stable trial termination metadata.

    Detection order is intentional: orchestrator-level signals (exception,
    timeout, tool-limit, interrupt, proxy-enforced max-rounds stop, error)
    win over output parsing, then OOM detection from exit code, then
    max-rounds budget check, then upstream-error classification from
    proxy.jsonl + output, then the catch-all ``agent_exit_nonzero``.

    ``interrupted`` is the structural Ctrl+C signal: the SIGINT handler
    force-removed the container while the agent was mid-trial. Caller
    derives it from process-level state (``_RUN_STOP_EVENT``) and/or
    ``StateSnapshot.has_failures`` (container disappeared before
    snapshot). We trust the bool — never re-derive it from exit_code,
    because ``docker exec`` returns 0 in some Docker versions when the
    underlying container is force-removed mid-stream, which would
    otherwise be misread as a clean ``completed``.
    """
    if exception is not None:
        return termination_info_from_exception(exception, failed_phase=failed_phase)
    if timed_out:
        timeout_label = f"{timeout_seconds:g}s" if timeout_seconds else "the configured timeout"
        return TerminationInfo(
            status=TerminationStatus.FAILED,
            reason=TerminationReason.EXECUTION_TIMEOUT,
            detail=f"Agent execution exceeded {timeout_label}",
            source=TerminationSource.ORCHESTRATOR,
        )
    if terminated_by_limit:
        return TerminationInfo(
            status=TerminationStatus.INTERRUPTED,
            reason=TerminationReason.TOOL_LIMIT,
            detail="Stopped after reaching the configured tool-call limit",
            source=TerminationSource.ORCHESTRATOR,
        )
    if interrupted:
        return user_interrupted_termination()
    if terminated_by_max_rounds:
        usage = _proxy_round_budget_usage(proxy_jsonl_path)
        if max_rounds > 0 and usage.billed > 0:
            detail = (
                f"Hit round budget - {_round_budget_phrase(usage, max_rounds)}; "
                "orchestrator stopped the agent after proxy enforced the limit"
            )
        else:
            detail = "Orchestrator stopped the agent after proxy enforced max_rounds"
        return max_rounds_reached_termination(detail=detail)
    if error:
        return _error_string_termination(
            error=error,
            error_type=error_type,
            failed_phase=failed_phase,
            proxy_jsonl_path=proxy_jsonl_path,
        )

    # Process killed by OOM-killer / external SIGKILL → exit 128+9 = 137.
    # Containers also bubble up 137 when the docker daemon kills the process
    # (resource constraint, hostmem squeeze). Treat as infra failure.
    if exit_code == 137:
        return TerminationInfo(
            status=TerminationStatus.FAILED,
            reason=TerminationReason.OOM_KILLED,
            detail=(str(output or "").strip()[:500] or
                    "Process killed by SIGKILL (exit 137) — likely OOM"),
            source=TerminationSource.ORCHESTRATOR,
        )

    # Max rounds reached — structural signal from proxy.jsonl + max_rounds.
    #
    # The in-container proxy enforces ``max_rounds`` by 403-rejecting the
    # next request once its own counter — successful upstream calls minus the
    # compact rewrites it tags — reaches the configured budget. It does NOT
    # call ``record()`` for the rejection (see ``sidecar.py``'s
    # ``_send_json(FORBIDDEN)`` branch — it ``return``s before recording), so
    # the admitted-call count is the structural signal that the budget ran out.
    #
    # Reproduce *that* counter here, not the root-only round count: this
    # branch is asking "did the proxy stop it?", and only the enforcer's own
    # arithmetic answers that. Root rounds go in the detail text instead, where
    # they say how much of the budget was real agent thinking.
    #
    # We check this BEFORE the proxy-error scan so a stray 502 / 503 in
    # the middle doesn't outvote the budget hit. A non-zero exit is the
    # gate: a clean exit at exactly max_rounds means the agent finished
    # the task within budget and shouldn't be relabelled.
    if exit_code != 0 and max_rounds > 0:
        usage = _proxy_round_budget_usage(proxy_jsonl_path)
        if usage.billed >= max_rounds:
            return max_rounds_reached_termination(
                detail=(
                    f"Hit round budget - {_round_budget_phrase(usage, max_rounds)}; "
                    f"proxy 403-rejected the next call"
                ),
            )

    if exit_code != 0:
        budget_termination = _token_cost_budget_termination(
            proxy_jsonl_path,
            max_input_tokens=max_input_tokens,
            max_output_tokens=max_output_tokens,
            max_cost=max_cost,
        )
        if budget_termination is not None:
            return budget_termination

    # Upstream model error detection — structural only, single source of truth.
    #
    # Rule: a trial is a "model error" iff its final proxy.jsonl entry is
    # a non-200 upstream response. Earlier transient upstream errors followed
    # by later successes are recovered calls, not the terminal cause.
    # Subtype refinement uses ``error.type`` substring + HTTP status code;
    # when neither pins it to a specific category, we still mark it
    # ``MODEL_ERROR`` (generic) so resume re-runs it by default.
    #
    # We do NOT scan agent stdout for "502" / "quota" / "rate limit" — those
    # phrases can appear in normal agent reasoning (e.g. while debugging a
    # target's web service) and would falsely classify a real agent failure
    # as a model error. If the proxy log shows no upstream error, the failure
    # is local → falls through to AGENT_EXIT_NONZERO below.
    if exit_code != 0:
        signal = _last_proxy_error_signal(proxy_jsonl_path)
        if signal is not None:
            upstream_reason = classify_upstream_error(
                http_status=signal.http_status,
                error_type=signal.error_type,
                error_message=signal.error_message,
            )
            if upstream_reason is None:
                # Proxy saw a non-200 but we couldn't pin the subtype — still
                # an upstream failure, still retry-worthy.
                upstream_reason = TerminationReason.MODEL_ERROR
            return TerminationInfo(
                status=TerminationStatus.FAILED,
                reason=upstream_reason,
                detail=(signal.error_message or signal.raw_text or "").strip()[:500]
                       or f"Upstream returned HTTP {signal.http_status}",
                source=TerminationSource.MODEL_PROXY,
            )

    if exit_code == 0:
        return completed_termination()
    # "Agent exited with code 1" names the symptom and nothing else. When the
    # agent died before writing any stdout its own stderr was captured into the
    # recorded output; promoting that first line makes the difference between a
    # rejected CLI flag, a config the CLI refuses to parse, and a missing
    # binary visible in the results table instead of one click deeper.
    detail = f"Agent exited with code {exit_code}"
    first_line = agent_failure_first_line(output)
    if first_line:
        detail = f"{detail}: {first_line}"
    return TerminationInfo(
        status=TerminationStatus.FAILED,
        reason=TerminationReason.AGENT_EXIT_NONZERO,
        detail=detail,
        source=TerminationSource.AGENT,
    )


def looks_like_model_timeout(text: str) -> bool:
    lowered = str(text or "").lower()
    timeout_markers = ("timed out", "timeout", "read operation timed out")
    upstream_markers = ("api error", "502", "proxy_error", "model", "upstream", "server-side")
    return any(marker in lowered for marker in timeout_markers) and any(
        marker in lowered for marker in upstream_markers
    )


# Which lifecycle phase an unrecognized exception escaped from → what kind of
# failure that most likely was. This is what makes the taxonomy useful *today*:
# the framework raises ~160 untyped ``RuntimeError``/``ValueError``s that would
# otherwise all land in ``TRIAL_ERROR``, and the phase is a signal already
# recorded at the point of failure. Typed exceptions are checked first and
# always win — this is the fallback, not the primary classifier.
#
# Phases not listed here (snapshotting, artifact collection, teardown, and the
# agent run itself) have no better answer than ``TRIAL_ERROR``: a failure there
# is genuinely a framework-side problem with no narrower owner.
_PHASE_FAILURE_REASONS: dict[str, tuple[TerminationReason, TerminationSource]] = {
    TrialPhase.STARTING_CONTAINER.value: (
        TerminationReason.CONTAINER_ERROR, TerminationSource.ORCHESTRATOR,
    ),
    TrialPhase.SETTING_UP_CONTAINER.value: (
        TerminationReason.CONTAINER_ERROR, TerminationSource.ORCHESTRATOR,
    ),
    TrialPhase.SETTING_UP_AGENT.value: (
        TerminationReason.AGENT_SETUP_ERROR, TerminationSource.AGENT,
    ),
    TrialPhase.LAUNCHING_TARGET.value: (
        TerminationReason.TARGET_UNAVAILABLE, TerminationSource.ORCHESTRATOR,
    ),
    TrialPhase.PREPARING_WORKSPACE.value: (
        TerminationReason.BENCHMARK_ERROR, TerminationSource.ORCHESTRATOR,
    ),
    TrialPhase.BUILDING_PROMPT.value: (
        TerminationReason.BENCHMARK_ERROR, TerminationSource.ORCHESTRATOR,
    ),
    TrialPhase.STARTING_PROXY.value: (
        TerminationReason.PROXY_ERROR, TerminationSource.MODEL_PROXY,
    ),
    TrialPhase.SCORING.value: (
        TerminationReason.SCORING_ERROR, TerminationSource.ORCHESTRATOR,
    ),
}

# Typed exception → terminal verdict. Ordered most specific first; ``TrialError``
# stays last among the ``CageError``s because several of the others could
# plausibly subclass it in future and the specific answer must win.
_EXCEPTION_REASONS: tuple[
    tuple[type[BaseException], TerminationReason, TerminationSource], ...
] = (
    (ConfigError, TerminationReason.CONFIG_ERROR, TerminationSource.ORCHESTRATOR),
    (ContainerError, TerminationReason.CONTAINER_ERROR, TerminationSource.ORCHESTRATOR),
    (AgentSetupError, TerminationReason.AGENT_SETUP_ERROR, TerminationSource.AGENT),
    (TargetError, TerminationReason.TARGET_ERROR, TerminationSource.ORCHESTRATOR),
    (BenchmarkError, TerminationReason.BENCHMARK_ERROR, TerminationSource.ORCHESTRATOR),
    (ScoringError, TerminationReason.SCORING_ERROR, TerminationSource.ORCHESTRATOR),
    (ProxyError, TerminationReason.PROXY_ERROR, TerminationSource.MODEL_PROXY),
    (TrialError, TerminationReason.TRIAL_ERROR, TerminationSource.ORCHESTRATOR),
)


#: Exception *class name* → verdict, for the many call sites that only ever see
#: a flattened error string plus its recorded ``error_type`` (meta.json rows,
#: offline reclassification, resume). Derived from ``_EXCEPTION_REASONS`` so the
#: two can never drift apart.
_EXCEPTION_REASONS_BY_NAME: dict[str, tuple[TerminationReason, TerminationSource]] = {
    exc_type.__name__: (reason, source)
    for exc_type, reason, source in _EXCEPTION_REASONS
}


def _error_string_termination(
    *,
    error: str,
    error_type: str,
    failed_phase: str,
    proxy_jsonl_path: object,
) -> TerminationInfo:
    """Classify a trial that failed through the exception path.

    Three sources of truth, most authoritative first:

    1. **The proxy log, but only for a failure during the agent run.** A trial
       whose agent was mid-flight when the orchestrator raised, and whose last
       upstream call was a non-200, almost always died *of* that upstream
       failure — an expired key, a quota wall, a gateway flapping. Attributing
       it to a generic "trial error" hides the one detail that says whether to
       retry. The phase guard matters: an upstream error left over from a
       finished agent run says nothing about a crash during scoring or teardown.
    2. **The exception type**, when the raise site used the typed taxonomy.
    3. **The lifecycle phase**, which classifies the untyped majority.
    """

    if str(failed_phase or "").strip().lower() == TrialPhase.RUNNING_AGENT.value:
        signal = _last_proxy_error_signal(proxy_jsonl_path)
        if signal is not None:
            upstream_reason = classify_upstream_error(
                http_status=signal.http_status,
                error_type=signal.error_type,
                error_message=signal.error_message,
            ) or TerminationReason.MODEL_ERROR
            return TerminationInfo(
                status=TerminationStatus.FAILED,
                reason=upstream_reason,
                detail=(signal.error_message or signal.raw_text or error).strip()[:500]
                       or f"Upstream returned HTTP {signal.http_status}",
                source=TerminationSource.MODEL_PROXY,
            )

    resolved = _EXCEPTION_REASONS_BY_NAME.get(str(error_type or "").strip())
    if resolved is None:
        resolved = _PHASE_FAILURE_REASONS.get(
            str(failed_phase or "").strip().lower(),
            (TerminationReason.TRIAL_ERROR, TerminationSource.ORCHESTRATOR),
        )
    reason, source = resolved
    return TerminationInfo(
        status=TerminationStatus.FAILED,
        reason=reason,
        detail=error,
        source=source,
    )


def termination_info_from_exception(
    exc: BaseException,
    *,
    failed_phase: str = "",
) -> TerminationInfo:
    """Map Cage exceptions and common interrupts into TerminationInfo.

    ``failed_phase`` is the lifecycle stage the exception escaped from (see
    ``cage.contracts.trial_phase``). It is consulted only for exceptions the
    typed taxonomy does not recognize — which is most of them, since the bulk of
    the framework still raises bare ``RuntimeError``/``ValueError``. Without it
    every such failure reads as a generic ``trial_error``; with it, a docker
    failure during container setup and a benchmark bug in ``build_prompt`` are
    told apart without either raise site having to change.
    """
    if isinstance(exc, (CageInterrupt, KeyboardInterrupt)):
        return user_interrupted_termination()
    if isinstance(exc, TrialTimeout):
        return TerminationInfo(
            status=TerminationStatus.FAILED,
            reason=TerminationReason.EXECUTION_TIMEOUT,
            detail=str(exc),
            source=TerminationSource.ORCHESTRATOR,
        )
    if isinstance(exc, ProxyError) and looks_like_model_timeout(str(exc)):
        return TerminationInfo(
            status=TerminationStatus.FAILED,
            reason=TerminationReason.MODEL_TIMEOUT,
            detail=str(exc),
            source=TerminationSource.MODEL_PROXY,
        )
    for exc_type, reason, source in _EXCEPTION_REASONS:
        if isinstance(exc, exc_type):
            return TerminationInfo(
                status=TerminationStatus.FAILED,
                reason=reason,
                detail=str(exc),
                source=source,
            )

    reason, source = _PHASE_FAILURE_REASONS.get(
        str(failed_phase or "").strip().lower(),
        (TerminationReason.TRIAL_ERROR, TerminationSource.ORCHESTRATOR),
    )
    return TerminationInfo(
        status=TerminationStatus.FAILED,
        reason=reason,
        detail=str(exc),
        source=source,
    )

