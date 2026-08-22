"""Upstream-error and budget signals read from the proxy jsonl log.

Structural classification of the proxy's terminal record (was the last LLM
call an upstream error?) and budget/cost accounting, kept separate from the
termination classifier that consumes them.
"""
from __future__ import annotations

from dataclasses import dataclass

from cage.contracts.jsonio import iter_jsonl_entries
from cage.experiment.engine.termination_model import TerminationReason


_ERROR_TYPE_RULES: tuple[tuple[TerminationReason, tuple[str, ...]], ...] = (
    (TerminationReason.MODEL_QUOTA_EXHAUSTED, (
        "usage_limit",           # codex: "usage_limit_reached"
        "insufficient_quota",    # openai
        "billing_hard_limit",    # openai
        "quota_exceeded",        # generic
        "credit_exhausted",      # some openai-compatible proxies
    )),
    (TerminationReason.MODEL_RATE_LIMITED, (
        "rate_limit",            # openai: "rate_limit_exceeded", anthropic: "rate_limit_error"
        "too_many_requests",
    )),
    (TerminationReason.MODEL_CONTEXT_OVERFLOW, (
        "context_length",        # openai: "context_length_exceeded"
        "string_too_long",       # some proxies
        "input_too_long",        # some proxies
        "prompt_too_long",
        "max_tokens_exceeded",
    )),
    (TerminationReason.MODEL_AUTH_ERROR, (
        "authentication",        # openai/anthropic: "authentication_error"
        "invalid_api_key",
        "permission_denied",
        "invalid_credentials",
    )),
    (TerminationReason.MODEL_TIMEOUT, (
        "timeout",               # generic timeout error type
        "deadline_exceeded",
    )),
    (TerminationReason.MODEL_BAD_GATEWAY, (
        "overloaded",            # anthropic: "overloaded_error"
        "service_unavailable",
        "bad_gateway",
        "bad_response_status_code",  # cage proxy passthrough for upstream 5xx
        "upstream_error",
    )),
)


_TEXT_FALLBACK_RULES: tuple[tuple[TerminationReason, tuple[str, ...]], ...] = (
    (TerminationReason.MODEL_QUOTA_EXHAUSTED, (
        "you've hit your usage limit",
        "you have hit your usage limit",
        "monthly quota",
    )),
    (TerminationReason.MODEL_RATE_LIMITED, (
        "rate limit",
        "too many requests",
    )),
    (TerminationReason.MODEL_BAD_GATEWAY, (
        "bad gateway",
        "service unavailable",
        "gateway timeout",
        "name or service not known",
        "connection refused",
        "connection reset",
        "no route to host",
    )),
    (TerminationReason.MODEL_AUTH_ERROR, (
        "unauthorized",
    )),
    (TerminationReason.MODEL_CONTEXT_OVERFLOW, (
        "maximum context length",
        "context window",
    )),
    (TerminationReason.MODEL_TIMEOUT, (
        "read operation timed out",
        "request timed out",
    )),
)


def _classify_by_error_type(error_type: str) -> TerminationReason | None:
    """Match the upstream JSON's ``error.type`` against known substrings."""
    et = (error_type or "").lower().strip()
    if not et:
        return None
    for reason, substrings in _ERROR_TYPE_RULES:
        if any(s in et for s in substrings):
            return reason
    return None


def _classify_by_http_status(
    http_status: int | None, *, error_message: str = ""
) -> TerminationReason | None:
    """Map a known HTTP status code to a termination reason.

    For 429 we disambiguate quota vs rate-limit by looking at the message:
    quota errors mention "usage limit" / "monthly" / "quota", everything
    else defaults to rate-limited (safer — rate limit retries in seconds,
    quota retries in days, and treating quota as rate-limit just wastes a
    couple resume attempts; the reverse is worse).
    """
    if http_status is None:
        return None
    if http_status in (401, 403):
        return TerminationReason.MODEL_AUTH_ERROR
    if http_status == 429:
        em = (error_message or "").lower()
        if any(k in em for k in ("usage limit", "monthly", "quota", "billing")):
            return TerminationReason.MODEL_QUOTA_EXHAUSTED
        return TerminationReason.MODEL_RATE_LIMITED
    if http_status in (408, 504):
        return TerminationReason.MODEL_TIMEOUT
    if 500 <= http_status < 600:
        return TerminationReason.MODEL_BAD_GATEWAY
    if http_status == 413:
        return TerminationReason.MODEL_CONTEXT_OVERFLOW
    if 400 <= http_status < 500:
        return TerminationReason.MODEL_ERROR
    return None


def classify_upstream_error(
    text: str = "",
    *,
    http_status: int | None = None,
    error_type: str = "",
    error_message: str = "",
) -> TerminationReason | None:
    """Classify an upstream error using Tier 1 (structural) → Tier 2 (text).

    Callers should prefer passing the structured fields (``http_status``,
    ``error_type``, ``error_message``) from the proxy.jsonl entry. ``text``
    is a free-form blob (agent stdout, error_text) used only as Tier 2
    fallback when the structured fields are absent or don't match.
    """
    # Tier 1a: error.type — most reliable, set by the upstream server.
    reason = _classify_by_error_type(error_type)
    if reason is not None:
        return reason
    # Tier 1b: HTTP status (with message hint for the ambiguous 429 case).
    reason = _classify_by_http_status(http_status, error_message=error_message)
    if reason is not None:
        return reason
    # Tier 2: text keyword fallback — only when structural signals missed.
    lowered = (text or "").lower()
    if not lowered:
        return None
    for reason, substrings in _TEXT_FALLBACK_RULES:
        if any(s in lowered for s in substrings):
            return reason
    return None


@dataclass(frozen=True)
class _UpstreamErrorSignal:
    """Structured view of a proxy.jsonl error entry."""

    http_status: int | None
    error_type: str
    error_message: str
    raw_text: str  # full error_text + body, used for Tier 2 fallback


def _last_proxy_error_signal(proxy_jsonl_path: object) -> _UpstreamErrorSignal | None:
    """Extract structured signals when the trial's final proxy entry is an error."""
    import json as _json
    import re as _re

    if not proxy_jsonl_path:
        return None
    last_entry: dict | None = None
    try:
        for entry in iter_jsonl_entries(proxy_jsonl_path):
            last_entry = entry
    except OSError:
        return None
    if not last_entry or str(last_entry.get("status") or "").lower() != "error":
        return None

    err_text = str(last_entry.get("error_text") or last_entry.get("error") or "")
    # Structured fields take precedence; fall back to parsing the JSON body
    # embedded in error_text (cage's proxy writes
    # ``HTTP <code>: {"error":{...}}``).
    http_status = last_entry.get("upstream_status_code")
    if not isinstance(http_status, int):
        m = _re.search(r"\bHTTP\s+(\d{3})\b", err_text)
        if m:
            http_status = int(m.group(1))
        else:
            http_status = None
    error_type = ""
    error_message = ""
    body_str = ""
    for k in ("upstream_response_body", "upstream_text", "raw_response"):
        v = last_entry.get(k)
        if isinstance(v, str) and v:
            body_str = v
            break
        if isinstance(v, dict):
            body_str = _json.dumps(v, ensure_ascii=False)
            break
    # Try to parse the embedded JSON body to extract error.type
    # / error.message. Sources we've seen in practice:
    #   error_text = 'HTTP 429: {"error":{"type":"...","message":"..."}}'
    #   error_text = '{"error":{"type":"...","message":"..."}}'
    #   upstream_response_body = '{"error":{"type":"...","message":"..."}}'
    for candidate in (body_str, err_text):
        if not candidate:
            continue
        brace = candidate.find("{")
        if brace < 0:
            continue
        try:
            parsed = _json.loads(candidate[brace:])
        except _json.JSONDecodeError:
            continue
        if isinstance(parsed, dict):
            e = parsed.get("error")
            if isinstance(e, dict):
                error_type = str(e.get("type") or e.get("code") or "")
                error_message = str(e.get("message") or "")
                break
            if isinstance(e, str):
                error_message = e
                break
    return _UpstreamErrorSignal(
        http_status=http_status,
        error_type=error_type,
        error_message=error_message,
        raw_text=" | ".join(p for p in (err_text, body_str) if p),
    )


def _last_proxy_error_text(proxy_jsonl_path: object) -> str:
    """Read the most recent error entry from a trial's proxy.jsonl.

    Returns a flat string combining ``error_text`` and the upstream
    response body (when present). Returns ``""`` when the file is
    missing, unreadable, has no error entries, or anything goes wrong —
    classification falls back gracefully.

    Note: proxy.jsonl files can be hundreds of MB for long-running trials
    (codex sends the full conversation context with every request, so a
    single JSON line may be tens of MB). A naive tail-read can miss the
    last error line entirely, so we stream the whole file. That's still
    bounded by disk speed and runs once per trial — acceptable.
    """
    import json as _json

    if not proxy_jsonl_path:
        return ""
    last_error_parts: list[str] = []
    try:
        for entry in iter_jsonl_entries(proxy_jsonl_path):
            if str(entry.get("status") or "").lower() != "error":
                continue
            err = str(entry.get("error_text") or entry.get("error") or "")
            body = ""
            for k in ("upstream_response_body", "upstream_text", "raw_response"):
                v = entry.get(k)
                if isinstance(v, str) and v:
                    body = v
                    break
                if isinstance(v, dict):
                    body = _json.dumps(v, ensure_ascii=False)
                    break
            status_code = entry.get("upstream_status_code")
            sc = f"http {status_code}" if isinstance(status_code, int) else ""
            # Keep overwriting so we end up with the *last* error entry.
            last_error_parts = [p for p in (sc, err, body) if p]
    except OSError:
        return ""
    return " | ".join(last_error_parts)


@dataclass(frozen=True)
class RoundBudgetUsage:
    """How a trial's recorded calls map onto the ``max_rounds`` budget.

    Two numbers, because two different things are being asked:

    ``billed`` — what the **enforcer** counted. The in-container proxy admits a
    request only while its own counter is below ``max_rounds``, then
    429-rejects, and it publishes that counter as ``successful_requests`` in
    ``progress.json``. We read that number rather than recompute it: the
    sidecar may not import cage code (it ships as a lone file into every agent
    container), so any rule expressed in host code is a *second*
    implementation of it, and the two drift. They already did once — the host
    refined its recount to root-only turns, the enforcer kept charging every
    call, and a trial stopped at its 500th admitted call reported "476/500".
    Rules cross that boundary as data, not as duplicated code. Recomputing
    from ``proxy.jsonl`` stays only as the fallback for trials whose
    ``progress.json`` is missing.

    ``root_rounds`` — what the agent actually got to *decide*. The proxy log is
    flat and interleaved: subagent loops, the harness's own auxiliary calls
    (a WebSearch helper, a background title call) and context-compaction calls
    all land in it. Reconstructing the conversation forest (see
    :mod:`cage.proxy.conversations`) and counting only the root conversation's
    non-compaction turns says how much of the budget was real agent thinking.

    The rest of the budget is split rather than lumped, because the two kinds
    cost the same but mean opposite things: ``compaction`` is the agent's own
    context being folded up (a handful per trial), while ``tool_side`` is what
    the harness sent beside the main conversation on a tool's behalf — one
    single-message call per WebSearch, one per fetched page, a subagent's whole
    loop — which is where a budget quietly drains. Lumping them reads as "this
    trial compacted 24 times", which is exactly the kind of collapsed number
    this verdict already got wrong once.

    ``root_rounds + compaction + tool_side == billed`` always: ``tool_side``
    absorbs the few audit-only entries (bodyless retries) that ``root_rounds``
    drops, so the parts never fail to add up to the number that was enforced.
    """

    billed: int
    root_rounds: int
    compaction: int
    tool_side: int


def _enforcer_billed_rounds(proxy_jsonl_path: object) -> int | None:
    """The round count the in-container proxy itself charged, or None.

    ``progress.json`` sits beside ``proxy.jsonl`` and is written by the
    enforcer as it runs, so it answers "how many calls did this trial spend"
    without the host re-deriving the rule. ``successful_requests`` is exactly
    the admission counter (successes minus tagged compact rewrites); the older
    ``success`` field is accepted for logs written before it was split out.
    """
    from pathlib import Path as _Path

    from cage.contracts.jsonio import load_json_file

    if not proxy_jsonl_path:
        return None
    progress = load_json_file(_Path(str(proxy_jsonl_path)).with_name("progress.json"))
    if not isinstance(progress, dict):
        return None
    for key in ("successful_requests", "success"):
        value = progress.get(key)
        if isinstance(value, int) and value >= 0:
            return value
    return None


def _proxy_round_budget_usage(proxy_jsonl_path: object) -> RoundBudgetUsage:
    """Read one trial's round counters: billed by the enforcer, split by us."""
    from cage.proxy.conversations import reconstruct_forest

    empty = RoundBudgetUsage(billed=0, root_rounds=0, compaction=0, tool_side=0)
    if not proxy_jsonl_path:
        return empty
    enforcer_billed = _enforcer_billed_rounds(proxy_jsonl_path)
    entries: list[dict] = []
    try:
        for entry in iter_jsonl_entries(proxy_jsonl_path):
            if str(entry.get("status") or "").lower() != "success":
                continue
            openai_request = entry.get("openai_request")
            if (
                isinstance(openai_request, dict)
                and openai_request.get("_proxy_compact_rewritten")
            ):
                continue
            entries.append(entry)
    except OSError:
        entries = []
    if not entries:
        # No usable log: the enforcer's own count is still the truth about the
        # budget, even when the records behind it are gone.
        if enforcer_billed:
            return RoundBudgetUsage(
                billed=enforcer_billed, root_rounds=0, compaction=0, tool_side=0
            )
        return empty
    forest = reconstruct_forest(entries)
    # Counting the log is the fallback, not the answer: it agrees with the
    # enforcer today, and re-deriving it here is how the two drifted before.
    billed = enforcer_billed if enforcer_billed is not None else len(entries)
    # The breakdown is ours to derive, but it is reported against the
    # enforcer's total — so clamp the parts to fit it. They only need clamping
    # when the log and the counter disagree (a truncated or trimmed log), and
    # then a breakdown that overflows its own total would be worse than a
    # conservative one.
    root_rounds = min(forest.root_rounds, billed)
    compaction = min(
        int(forest.structure.get("num_compactions", 0) or 0), billed - root_rounds
    )
    return RoundBudgetUsage(
        billed=billed,
        root_rounds=root_rounds,
        compaction=compaction,
        tool_side=billed - root_rounds - compaction,
    )


def _proxy_usage_cost(entry: dict) -> float | None:
    for key in ("usage_summary", "cage_usage"):
        usage = entry.get(key)
        if isinstance(usage, dict):
            for cost_key in ("cost_usd", "cost"):
                if cost_key in usage:
                    try:
                        return float(usage.get(cost_key) or 0.0)
                    except (TypeError, ValueError):
                        return 0.0

    for key in ("upstream_response", "anthropic_response"):
        response = entry.get(key) or {}
        if not isinstance(response, dict):
            continue
        usage = response.get("usage") or {}
        if not isinstance(usage, dict):
            continue
        for cost_key in ("cost_usd", "cost"):
            if cost_key not in usage:
                continue
            try:
                return float(usage.get(cost_key) or 0.0)
            except (TypeError, ValueError):
                return 0.0
    return None


def _proxy_budget_usage(proxy_jsonl_path: object) -> dict[str, float | int]:
    """Return cumulative token/cost usage from proxy artifacts.

    Prefer ``progress.json`` because the in-container proxy writes the
    already-normalized cumulative view there. Fall back to ``proxy.jsonl`` so
    older artifacts without progress snapshots still classify token budgets.
    """
    import json as _json
    from pathlib import Path as _Path

    usage: dict[str, float | int] = {
        "input_tokens": 0,
        "output_tokens": 0,
        "cost_usd": 0.0,
    }
    if not proxy_jsonl_path:
        return usage

    path = _Path(str(proxy_jsonl_path))
    progress_path = path.with_name("progress.json")
    if progress_path.is_file():
        try:
            progress = _json.loads(progress_path.read_text(encoding="utf-8"))
        except (_json.JSONDecodeError, OSError):
            progress = {}
        if isinstance(progress, dict):
            try:
                usage["input_tokens"] = int(progress.get("tokens_in", 0) or 0)
            except (TypeError, ValueError):
                usage["input_tokens"] = 0
            try:
                usage["output_tokens"] = int(progress.get("tokens_out", 0) or 0)
            except (TypeError, ValueError):
                usage["output_tokens"] = 0
            try:
                usage["cost_usd"] = float(progress.get("cost_usd", 0.0) or 0.0)
            except (TypeError, ValueError):
                usage["cost_usd"] = 0.0
            return usage

    if not path.is_file():
        return usage

    try:
        from cage.proxy.usage import extract_entry_usage

        for entry in iter_jsonl_entries(path):
            if str(entry.get("status") or "").lower() != "success":
                continue
            tokens = extract_entry_usage(entry)
            usage["input_tokens"] = int(usage["input_tokens"]) + tokens["input_tokens"]
            usage["output_tokens"] = int(usage["output_tokens"]) + tokens["output_tokens"]
            cost = _proxy_usage_cost(entry)
            if cost is not None:
                usage["cost_usd"] = float(usage["cost_usd"]) + cost
    except OSError:
        return usage
    return usage

