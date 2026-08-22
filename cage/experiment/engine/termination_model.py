"""Trial termination vocabulary: status / reason / source / info value types."""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class TerminationStatus(str, Enum):
    """How a trial ended — the terminal subset of ``TrialStatus``.

    Two enums describe one vocabulary, deliberately: ``TrialStatus`` covers a
    trial's whole life (including ``pending`` and ``running``), while this one
    is the answer to "how did it *end*" and so cannot hold a non-terminal value.

    Their four shared values must stay byte-identical — the classifier writes
    this enum into the same ``status`` field the runtime writes ``TrialStatus``
    into, so any drift would produce a status no consumer recognises. That
    agreement is asserted against ``contracts.trial_status.TERMINAL_TRIAL_STATUSES``
    in the test suite rather than left as a coincidence between two files.
    """

    COMPLETED = "completed"
    FAILED = "failed"
    INTERRUPTED = "interrupted"
    CANCELLED = "cancelled"


class TerminationReason(str, Enum):
    """Stable machine-readable reason a trial stopped.

    Reasons partition into three groups by how resume should treat them:

    1. **Expected** (resume keeps the result, does NOT re-run): the agent
       reached a natural stopping point.
       - ``COMPLETED``           agent exited 0 with no errors
       - ``MAX_ROUNDS_REACHED``  agent hit its per-trial round budget
                                 (detected structurally from successful
                                 non-compact proxy rounds —
                                 see ``max_rounds_reached_termination``)
       - ``MAX_INPUT_TOKENS_REACHED``  proxy-observed input token budget hit
       - ``MAX_OUTPUT_TOKENS_REACHED`` proxy-observed output token budget hit
       - ``MAX_COST_REACHED``          proxy-observed cost budget hit
       - ``EXECUTION_TIMEOUT``   wall-clock orchestrator cap
       - ``TOOL_LIMIT``          tool-call budget exhausted (legacy)

    2. **Unexpected / infra** (resume re-runs by default): something outside
       the agent's control prevented a real result.
       - ``MODEL_QUOTA_EXHAUSTED``  upstream returned 429 usage_limit_reached
       - ``MODEL_RATE_LIMITED``     upstream 429 rate-limit
       - ``MODEL_BAD_GATEWAY``      upstream 502/503/504
       - ``MODEL_AUTH_ERROR``       upstream 401/403
       - ``MODEL_CONTEXT_OVERFLOW`` request exceeded model context window
       - ``MODEL_TIMEOUT``          upstream request timed out
       - ``MODEL_ERROR``            other unclassified upstream HTTP error
       - ``OOM_KILLED``             container killed (SIGKILL / exit 137)
       - ``TARGET_UNAVAILABLE``     target stack failed to launch
       - ``TARGET_ERROR``           target stack died after coming up
       - ``CONTAINER_ERROR``        agent container lifecycle failed
       - ``PROXY_ERROR``            in-container LLM proxy failed to start/run
       - ``AGENT_SETUP_ERROR``      agent could not be prepared or launched
       - ``BENCHMARK_ERROR``        a Benchmark subclass raised (Layer 2 bug)
       - ``SCORING_ERROR``          a Scorer subclass raised (trial itself is fine)
       - ``TRIAL_ERROR``            orchestrator raised something unclassified

       The five middle reasons exist so "the trial errored" stops being one
       bucket holding five unrelated failures. They are produced either from a
       typed exception (``cage.contracts.exceptions``) or, for the many untyped
       ``RuntimeError``/``ValueError`` raises across the framework, inferred from
       the lifecycle phase the exception escaped from.

    2b. **Config** (resume re-runs, but only after the user acts):
       - ``CONFIG_ERROR``           project.yml / models.yml cannot be resolved

    3. **State** (resume policy depends on user intent):
       - ``USER_INTERRUPTED``       Ctrl+C while running
       - ``CANCELLED_BEFORE_START`` Ctrl+C before trial started (rerun)
       - ``AGENT_EXIT_NONZERO``     truly unclassified agent failure (keep)
    """

    # Expected
    COMPLETED = "completed"
    MAX_ROUNDS_REACHED = "max_rounds_reached"
    MAX_INPUT_TOKENS_REACHED = "max_input_tokens_reached"
    MAX_OUTPUT_TOKENS_REACHED = "max_output_tokens_reached"
    MAX_COST_REACHED = "max_cost_reached"
    EXECUTION_TIMEOUT = "execution_timeout"
    TOOL_LIMIT = "tool_limit"

    # Unexpected — upstream model proxy
    MODEL_QUOTA_EXHAUSTED = "model_quota_exhausted"
    MODEL_RATE_LIMITED = "model_rate_limited"
    MODEL_BAD_GATEWAY = "model_bad_gateway"
    MODEL_AUTH_ERROR = "model_auth_error"
    MODEL_CONTEXT_OVERFLOW = "model_context_overflow"
    MODEL_TIMEOUT = "model_timeout"
    MODEL_ERROR = "model_error"

    # Unexpected — infra
    OOM_KILLED = "oom_killed"
    TARGET_UNAVAILABLE = "target_unavailable"
    TARGET_ERROR = "target_error"
    CONTAINER_ERROR = "container_error"
    PROXY_ERROR = "proxy_error"
    AGENT_SETUP_ERROR = "agent_setup_error"
    BENCHMARK_ERROR = "benchmark_error"
    SCORING_ERROR = "scoring_error"
    TRIAL_ERROR = "trial_error"

    # Unexpected — configuration
    CONFIG_ERROR = "config_error"

    # State
    USER_INTERRUPTED = "user_interrupted"
    CANCELLED_BEFORE_START = "cancelled_before_start"
    AGENT_EXIT_NONZERO = "agent_exit_nonzero"


#: Reasons under which the agent process stopped talking on its own terms, so
#: whatever it said last really is its answer.
#:
#: ``AGENT_EXIT_NONZERO`` belongs here: the agent chose to exit, and its parting
#: words are usually its own error message. ``SCORING_ERROR`` too — the trial
#: itself ran to completion and only the scorer afterwards blew up.
AGENT_FINISHED_SPEAKING = frozenset({
    "completed",
    "agent_exit_nonzero",
    "scoring_error",
})


def agent_was_cut_off(reason: str) -> bool:
    """Did something outside the agent stop it before it could conclude?

    Answers the question a reader of a trial's recorded output actually has:
    *is this a conclusion, or the middle of a sentence?* A timed-out agent's
    last words are typically a plan for a tool call whose result it never saw
    — real information about where it got to, but not an answer, and a panel
    labelled "Final Output" claims otherwise.

    Membership is an allowlist rather than a list of the ways to be cut off,
    so a reason added later defaults to "cut off". That errs toward
    under-claiming: presenting a conclusion as a fragment costs a reader
    nothing, presenting a fragment as a conclusion misleads them.

    No reason at all — a still-running trial, or a run dir written before
    this field existed — is not evidence of either, so it answers False. The
    allowlist decides between *known* endings; it does not turn silence into
    a claim.
    """

    text = str(reason or "").strip()
    return bool(text) and text not in AGENT_FINISHED_SPEAKING


class TerminationSource(str, Enum):
    """Component that produced the terminal condition."""

    AGENT = "agent"
    MODEL_PROXY = "model_proxy"
    ORCHESTRATOR = "orchestrator"
    USER = "user"


@dataclass(frozen=True)
class TerminationInfo:
    """Structured trial termination metadata shared by storage and UI."""

    status: TerminationStatus
    reason: TerminationReason
    detail: str
    source: TerminationSource

    def to_metadata(self) -> dict[str, str]:
        return {
            "status": self.status.value,
            "termination_reason": self.reason.value,
            "termination_detail": self.detail,
            "termination_source": self.source.value,
        }

