"""The one wire marker shared between agent output parsing and classification.

``AgentType.parse_output`` records a banner when the agent process died without
producing any stdout of its own, so its captured stderr is not lost. The
termination classifier then recognises that banner to lift the agent's own first
line into the trial's ``termination_detail``.

Both sides need the exact same literal, and they live in different layers, so it
belongs here rather than being duplicated as a string in each.
"""

from __future__ import annotations

#: Prefix of the banner ``failure_banner`` emits. The exit code and the agent's
#: captured stderr follow on the same and subsequent lines.
AGENT_FAILURE_BANNER_PREFIX = "[Agent exited with code "

#: Marker ``failure_banner`` writes between the head and the tail of a stderr
#: too long to keep whole. It is bookkeeping, not something the agent said, so
#: :func:`agent_failure_first_line` drops it rather than promoting it into a
#: status detail.
STDERR_ELISION_MARKER = "[… stderr elided …]"


def agent_failure_first_line(
    output: str,
    *,
    limit: int = 300,
    max_lines: int = 3,
) -> str:
    """Opening lines of a dead agent's captured stderr; "" if none.

    Only reads output that actually carries the banner. A trial whose agent
    produced a normal transcript and *then* exited non-zero must not have a
    random line of that transcript promoted into its status detail.

    Takes the first few lines rather than exactly one, because which line is the
    diagnostic one differs per agent and per failure — kimi-cli leads with its
    config error but leads with a "to resume this session" hint on a connection
    failure. Picking the useful line would mean encoding each CLI's output
    conventions, which is precisely the open-ended maintenance this module
    exists to avoid. Taking a few costs a little noise and never loses the
    answer.
    """

    text = str(output or "")
    if not text.startswith(AGENT_FAILURE_BANNER_PREFIX):
        return ""
    body = [
        line for line in text.splitlines()[1:]
        if line.strip() != STDERR_ELISION_MARKER
    ]
    return compact_lines("\n".join(body), limit=limit, max_lines=max_lines)


def compact_lines(text: str, *, limit: int = 300, max_lines: int = 3) -> str:
    """Squeeze multi-line output into one readable line, or "" if empty.

    Used wherever an agent's own words have to fit a status field or a table
    cell. Keeps the opening lines rather than trying to identify the important
    one — see :func:`agent_failure_first_line` for why guessing is a trap.
    """

    collected: list[str] = []
    for line in str(text or "").splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        collected.append(stripped)
        if len(collected) >= max_lines:
            break
    return " · ".join(collected)[:limit]
