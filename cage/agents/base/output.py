"""Shared output-parsing primitives for Claude-Code-shaped CLI streams.

``claude``, ``hermes`` and ``qwen`` emit the same NDJSON ``stream-json`` event
shapes (``type == "result"`` carrying the final answer, ``type == "assistant"``
messages carrying text blocks); their ``parse_output`` extraction loops were
line-identical twins. This module owns that skeleton once.

Deliberately NOT the whole story for the other agents: kimi's CLI schemas
churned across versions so its loop tolerates extra shapes (``role`` keys,
string content, bare ``message`` events), and codex has a dedicated
event-stream parser. Forcing those onto one extractor would change what each
agent accepts — they share only the :func:`failure_banner` guard. (qwen keeps
a tolerant scan *after* the shared extractor for the same reason, not instead
of it.)
"""

from __future__ import annotations

import json

from cage.contracts.agent_output import (
    AGENT_FAILURE_BANNER_PREFIX,
    STDERR_ELISION_MARKER,
)
from cage.sandbox.exec import ExecResult

#: How much of a dead agent's stderr the banner keeps, and how much of that
#: budget goes to the opening. Both ends matter and for opposite reasons: a
#: CLI that refuses to start says why in its *first* lines (kimi-cli's config
#: validation error), while a CLI killed mid-run says why in its *last* ones.
#: Keeping only the head — which this used to do — reduced every timeout kill
#: to whatever startup banner the CLI happened to print, e.g. qwen-code's
#: "running headless with --yolo" warning standing in as the agent's last
#: words for a two-hour trial.
_STDERR_BUDGET = 2000
_STDERR_HEAD = 700


def diagnostic_stderr(
    stderr: str, *, budget: int = _STDERR_BUDGET, head: int = _STDERR_HEAD,
) -> str:
    """A dead agent's stderr trimmed to its two informative ends."""

    text = str(stderr or "")
    if len(text) <= budget:
        return text
    tail = budget - head
    return f"{text[:head]}\n{STDERR_ELISION_MARKER}\n{text[-tail:]}"


def failure_banner(result: ExecResult) -> str | None:
    """The shared "agent died with no output" banner, or None to keep parsing."""

    if result.exit_code != 0 and not result.stdout.strip():
        return (
            f"{AGENT_FAILURE_BANNER_PREFIX}{result.exit_code}]\n"
            f"{diagnostic_stderr(result.stderr)}"
        )
    return None


def normalize_recorded_output(output: str) -> str:
    """Repair a recorded ``task_output.json`` output field on read.

    Runtime always runs ``AgentType.parse_output`` before persisting, but two
    sources still leave raw CLI streams in recorded outputs: run dirs written
    by older cage versions (re-scored offline via ``cage score``), and
    codex's parse-time fallback that keeps raw stdout when the event stream
    carried no final message. The knowledge of *which* recorded formats need
    repair belongs to the agents package — scorers call this one primitive
    and never learn an agent name.

    Today the only repair is the codex ``--json`` event stream.
    """

    try:
        from cage.agents.codex.output import parse_codex_event_stream

        summary = parse_codex_event_stream(output)
        if summary.is_event_stream:
            return summary.final_output()
    except Exception:
        pass
    return output


def extract_stream_json_text(stdout: str) -> tuple[str, bool]:
    """Extract the final result/assistant text from an NDJSON event stream.

    Returns ``(last_text, saw_json)`` — callers choose their own raw-stdout
    fallback when the stream carried no parseable answer.
    """

    last_text = ""
    saw_json = False
    for line in stdout.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
        except json.JSONDecodeError:
            continue
        saw_json = True

        # Final result event wins when present.
        if obj.get("type") == "result":
            result_text = obj.get("result", "")
            if result_text:
                last_text = result_text
            continue

        # Otherwise keep the latest assistant text block.
        if obj.get("type") == "assistant" and obj.get("message"):
            msg = obj["message"]
            content = msg.get("content", [])
            if isinstance(content, list):
                for block in content:
                    if isinstance(block, dict) and block.get("type") == "text":
                        last_text = block.get("text", "")
    return last_text, saw_json
