"""Render recorded content blocks into training-row text.

The wire carries structured blocks (thinking / text / tool_use). A training row
carries one string per turn. This module owns that flattening, and the two
repairs that come with it.
"""

from __future__ import annotations

import json
import re
from collections.abc import Sequence
from typing import Any


def tool_call_xml(name: str, arguments: Any) -> str:
    """One tool call in the XML form the training template expects."""

    parts = [f"<tool_call>\n<function={name}>"]
    for key, value in (arguments or {}).items():
        rendered = value if isinstance(value, str) else json.dumps(value, ensure_ascii=False)
        parts.append(f"<parameter={key}>\n{rendered}\n</parameter>")
    parts.append("</function>\n</tool_call>")
    return "\n".join(parts)


_TOOL_CALL_RE = re.compile(r"<tool_call>\s*(.*?)\s*</tool_call>", re.DOTALL)
_FUNCTION_RE = re.compile(r"<function=([^>\s]+)>(.*?)</function>", re.DOTALL)
_PARAMETER_RE = re.compile(r"<parameter=([^>\s]+)>(.*?)</parameter>", re.DOTALL)


def tool_call_arguments_of(content: str) -> list[tuple[str, dict[str, Any]]]:
    """Parse rendered tool calls back out of a turn — the inverse of :func:`tool_call_xml`.

    Exists so a fidelity check can compare an exported turn against the
    structured ``tool_calls`` the upstream received without either side
    privileging its own encoding. Values are recovered as JSON where they were
    serialised as JSON, and left as text where they were text.
    """

    out: list[tuple[str, dict[str, Any]]] = []
    for body in _TOOL_CALL_RE.findall(content or ""):
        for name, inner in _FUNCTION_RE.findall(body):
            arguments: dict[str, Any] = {}
            for key, value in _PARAMETER_RE.findall(inner):
                # The renderer wraps every value in exactly one newline on each
                # side; peel those, and only those, so a value that genuinely
                # begins or ends with whitespace survives the round trip.
                if value.startswith("\n"):
                    value = value[1:]
                if value.endswith("\n"):
                    value = value[:-1]
                try:
                    arguments[key] = json.loads(value)
                except (json.JSONDecodeError, ValueError):
                    arguments[key] = value
            out.append((name, arguments))
    return out


def tool_result_text(block: dict[str, Any]) -> str:
    """Flatten a ``tool_result`` block's content into plain text."""

    content = block.get("content", "")
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return "\n".join(
            item.get("text", "") if isinstance(item, dict) else str(item) for item in content
        )
    return str(content)


def repair_think_tags(text: str) -> tuple[str, bool]:
    """Restore the opening ``<think>`` a chat template counted as prompt.

    Qwen-style templates put the opening tag in the prompt prefix, so the model
    emits ``reasoning…</think> answer`` — closing tag only. Stored as-is the
    tags do not pair and the reasoning span cannot be recovered at training
    time. Returns ``(text, repaired)``.
    """

    if not text or "</think>" not in text or "<think>" in text:
        return text, False
    return "<think>\n" + text.lstrip("\n"), True


def think_tags_balanced(text: str) -> bool:
    return (text or "").count("<think>") == (text or "").count("</think>")


def assistant_content(
    blocks: Sequence[Any],
    redact,
    reasoning: str = "",
    drop_block=None,
) -> str:
    """Render one assistant turn.

    *reasoning* is the turn's real reasoning when the response carried it out of
    band (the OpenAI dialects put it beside the content rather than in it). It is
    **never** synthesised: an empty string means the model emitted none, and the
    turn gets no ``<think>`` block at all.

    Whether historical turns carry reasoning is likewise read off the blocks
    rather than decided here. Before the proxy replayed thinking, history
    genuinely carried none; now a reasoning-emitting upstream gets its own prior
    thinking replayed, so history genuinely does. Hardcoding either answer would
    misrepresent half of any corpus that spans the change.
    """

    segments: list[str] = []

    thinking = reasoning or "\n".join(
        block.get("thinking", "")
        for block in blocks
        if isinstance(block, dict) and block.get("type") == "thinking"
    ).strip()
    if thinking:
        segments.append(f"<think>\n{redact(thinking)}\n</think>")

    text = "\n".join(
        block.get("text", "")
        for block in blocks
        if isinstance(block, dict) and block.get("type") == "text"
    ).strip()
    if drop_block is not None:
        text = drop_block(text)
    if text:
        segments.append(redact(text))

    for block in blocks:
        if isinstance(block, dict) and block.get("type") == "tool_use":
            segments.append(
                redact(tool_call_xml(block.get("name", ""), block.get("input") or {}))
            )

    return "\n\n".join(segments)
