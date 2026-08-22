"""Turn one trial's ``proxy.jsonl`` into complete-conversation training rows.

The unit of output is a **segment**: one self-consistent conversation, prefix
taken verbatim from a real request, every assistant turn supervised.

Why the prefix can be taken verbatim
------------------------------------
Every recorded request carries its full message history. So the *last* request
of a stretch of conversation already contains every earlier turn of that
stretch, exactly as the model received it. Appending that request's own response
yields the complete conversation with nothing reassembled and nothing invented.

Why a trial can produce more than one segment
---------------------------------------------
When the context fills, the harness compacts: it asks the model to summarise,
then **replaces** the history with that summary. No single context the model ever
saw spans both sides of that boundary, so a linear conversation joining them
would be a fabrication. Each side is complete on its own, so N compactions give
N+1 segments.

What is deliberately *not* decided here
---------------------------------------
Whether a segment is worth training on. Failed trials, summary-opened segments,
low-reasoning trajectories all come out tagged and are somebody else's call.
"""

from __future__ import annotations

import json
import re
from collections.abc import Iterator, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from cage.corpus.records import Segment
from cage.corpus.redact import (
    Redactor,
    primary_workdir,
    redaction_rewrites_workdir,
    system_prompt,
)
from cage.corpus.render import (
    assistant_content,
    repair_think_tags,
    think_tags_balanced,
    tool_result_text,
)
from cage.proxy.sidecar import _DIR_WRAP

# --------------------------------------------------------------------------- #
# Harness signatures
# --------------------------------------------------------------------------- #

# The director's injected block, anchored on the wrapper the sidecar itself
# writes. Deriving it from that constant instead of restating the sentence means
# a change to the injection cannot silently start leaking hints into corpora.
_DIR_LEAD = _DIR_WRAP.split("{hint}")[0].split(".")[0].strip()
_DIR_BLOCK = re.compile(
    r"\n*<system-reminder>\s*" + re.escape(_DIR_LEAD) + r".*?</system-reminder>",
    re.S,
)

# Any reminder block, for the non-strict view that strips them wholesale —
# including ones embedded inside a tool result, which a standalone-block match
# would miss.
_ANY_REMINDER = re.compile(r"\n*<system-reminder>.*?</system-reminder>", re.S)

# A subagent's system prompt introduces it as a delegate. Used only by the
# ``system_prompt`` splitter; the ``forest`` splitter answers the same question
# structurally and works on harnesses this phrasing does not cover.
_SUBAGENT_RE = re.compile(
    r"You are an? [^.\n]{0,80}for Claude Code, Anthropic's official CLI for Claude"
)
_SUBAGENT_MARKERS = ("specialist for Claude Code", "READ-ONLY exploration task")

# The compaction CALL: the harness asks for a summary and forbids tool use.
_COMPACTION_INSTRUCTION_MARKERS = (
    ("Do NOT call any tools", "<summary>"),
    ("Respond with plain text only",),
)
# The continuation: the summary re-enters as a user text block opening with this.
_CONTINUATION_MARKER = "this session is being continued from a previous conversation"


def request_of(entry: dict[str, Any]) -> dict[str, Any]:
    """The body that went upstream — what the model was actually given.

    ``openai_request`` first, and the name is a historical misnomer: the field
    holds whatever the proxy sent on, which is a translated OpenAI body on the
    translation path and the agent's own bytes on a passthrough. Either way it
    is the model's input.

    ``anthropic_request`` is the *translation input* — what the agent produced
    before the proxy touched it — and the two differ. Some sidecar builds strip
    Claude Code's per-call billing header on the way out, so the agent's body
    carries a line the model never saw; measured on real runs, that is an 86
    character difference in the system prompt, present in some runs and absent
    in others depending on the image. Reading the upstream body is right for all
    of them without knowing which transforms that build applied.
    """

    for key in ("openai_request", "anthropic_request"):
        candidate = entry.get(key)
        # Must actually be a request body. The same field also holds stubs for
        # records that carry no conversation — a websocket upgrade logs
        # ``{"_websocket": true, "path": …}`` — and preferring one of those
        # would silently produce an empty prefix.
        if isinstance(candidate, dict) and candidate.get("messages"):
            return candidate
    return {}


def response_blocks_of(entry: dict[str, Any]) -> list[Any]:
    """What the model produced, as Anthropic-shaped blocks.

    The raw upstream reply first — that is the model's actual output, before the
    proxy translated it back. Falls back to the translated view when the raw
    reply yields nothing renderable, so a record written by a generation that
    only kept one of the two still produces a turn instead of vanishing.
    """

    for key in ("upstream_response", "anthropic_response"):
        candidate = entry.get(key)
        if not isinstance(candidate, dict):
            continue
        blocks = response_blocks(candidate)
        if blocks:
            return blocks
    return []


def is_openai_shaped(request: dict[str, Any]) -> bool:
    """Does this body speak OpenAI chat completions rather than Anthropic messages?

    Decided from the body, never from the field name: an Anthropic-native
    endpoint is recorded under ``openai_request`` too. A top-level ``system``
    key means Anthropic; a ``system``-role message means OpenAI.
    """

    if "system" in request:
        return False
    return any(
        isinstance(m, dict) and m.get("role") in ("system", "tool")
        for m in request.get("messages") or []
    )


def response_blocks(response: dict[str, Any]) -> list[Any]:
    """Assistant content as Anthropic-shaped blocks, from any recorded dialect."""

    content = response.get("content")
    if isinstance(content, list) and content:
        return content

    choices = response.get("choices")
    if isinstance(choices, list) and choices:
        message = choices[0].get("message") if isinstance(choices[0], dict) else None
        if isinstance(message, dict):
            return _blocks_from_chat_message(message)
    return []


def _blocks_from_chat_message(message: dict[str, Any]) -> list[dict[str, Any]]:
    blocks: list[dict[str, Any]] = []
    text = message.get("content")
    if isinstance(text, str) and text:
        blocks.append({"type": "text", "text": text})
    elif isinstance(text, list):
        blocks.extend(b for b in text if isinstance(b, dict))
    for call in message.get("tool_calls") or []:
        if not isinstance(call, dict):
            continue
        function = call.get("function") if isinstance(call.get("function"), dict) else {}
        arguments = function.get("arguments", call.get("arguments", {}))
        if isinstance(arguments, str):
            try:
                arguments = json.loads(arguments) if arguments else {}
            except json.JSONDecodeError:
                arguments = {"raw": arguments}
        blocks.append({
            "type": "tool_use",
            "id": str(call.get("id") or ""),
            "name": function.get("name") or call.get("name") or "",
            "input": arguments if isinstance(arguments, dict) else {"raw": arguments},
        })
    return blocks


def _is_subagent_request(request: dict[str, Any]) -> bool:
    system = system_text(request)
    return bool(_SUBAGENT_RE.search(system)) or any(m in system for m in _SUBAGENT_MARKERS)


def system_text(request: dict[str, Any]) -> str:
    """The request's system prompt, in any of the three shapes it is recorded in.

    A top-level string, a top-level block list, or — on the OpenAI translation
    path — the leading ``system``-role message.
    """

    system = request.get("system", "")
    if isinstance(system, list):
        return "\n".join(b.get("text", "") for b in system if isinstance(b, dict))
    if isinstance(system, str) and system:
        return system
    for message in request.get("messages") or []:
        if isinstance(message, dict) and message.get("role") == "system":
            content = message.get("content")
            return content if isinstance(content, str) else str(content or "")
    return str(system or "")


def _is_reminder(text: str) -> bool:
    return isinstance(text, str) and text.lstrip().startswith("<system-reminder>")


def _is_director_text(text: str) -> bool:
    return isinstance(text, str) and _DIR_LEAD in text


def _is_summary_text(text: str) -> bool:
    return isinstance(text, str) and _CONTINUATION_MARKER in text.lstrip()[:400].lower()


def turn_reasoning(entry: dict[str, Any]) -> str:
    """This turn's real reasoning — never fabricated, empty when there was none.

    Sources in order of trust:

    1. the ``thinking`` block on the Anthropic-shaped response, which the proxy
       normalises every upstream dialect into, so it is right for all of them;
    2. the raw upstream chat fields, for records written before that
       normalisation existed. Vendors disagree on the name — ``reasoning_content``
       and ``reasoning`` both occur, and checking only the first silently zeroed
       out every turn from the deployments that use the second;
    3. the Responses-API ``reasoning`` item, for upstreams that speak it.

    Models that inline ``<think>`` in their content need no handling here: their
    reasoning already rides along in the response text.
    """

    response = entry.get("anthropic_response") or {}
    for block in (response.get("content") or []) if isinstance(response, dict) else []:
        if isinstance(block, dict) and block.get("type") == "thinking":
            text = (block.get("thinking") or "").strip()
            if text:
                return text

    upstream = entry.get("upstream_response") or {}
    try:
        message = upstream["choices"][0]["message"]
        text = (message.get("reasoning_content") or message.get("reasoning") or "").strip()
        if text:
            return text
    except Exception:
        pass

    output = upstream.get("output")
    if isinstance(output, list):
        parts: list[str] = []
        for item in output:
            if not isinstance(item, dict) or item.get("type") != "reasoning":
                continue
            for key in ("summary", "content"):
                value = item.get(key)
                if isinstance(value, list):
                    for block in value:
                        if isinstance(block, dict):
                            parts.append(str(block.get("text") or block.get("summary_text") or ""))
                        elif block:
                            parts.append(str(block))
                elif isinstance(value, str):
                    parts.append(value)
            if isinstance(item.get("text"), str):
                parts.append(item["text"])
        joined = "\n".join(p for p in parts if p).strip()
        if joined:
            return joined
    return ""


def _tools_of(entry: dict[str, Any]) -> list[Any]:
    """The tool schema for this call.

    Taken from the OpenAI-shaped request: the Anthropic request Claude Code
    sends carries none, and the training row needs the schema to be trainable.
    """

    return (entry.get("openai_request") or {}).get("tools") or []


# --------------------------------------------------------------------------- #
# Options
# --------------------------------------------------------------------------- #


@dataclass(frozen=True)
class BuildOptions:
    """Knobs that change what a segment contains.

    ``strict`` reproduces the real input: Claude Code's own ``<system-reminder>``
    blocks stay exactly where they were. The non-strict view strips all
    reminders, which is a *smaller* input than the model actually had; it exists
    for corpora that deliberately want the task without harness scaffolding.

    ``repair_think_tags`` prepends the ``<think>`` a chat template counted as
    prompt, so the tag pairs. Off by default for the same reason as the others:
    a model whose reasoning arrives inline emits only the closing tag, so that
    is what it produced and what its own history carried. Turning this on trades
    exactness for a corpus whose reasoning spans are delimited.

    ``strip_director`` and ``strip_billing_header`` are off by default. Both
    were genuinely in what the agent sent, and an export that quietly removes
    them is making a training decision on someone else's behalf. A caller who
    wants them gone can say so; a caller who receives a corpus they were already
    removed from cannot get them back.

    ``splitter`` selects how the main agent and the compaction boundaries are
    identified.

    ``"forest"`` (default) asks :mod:`cage.proxy.conversations`, which
    reconstructs the delegation tree and reads compaction off the request text.
    ``"system_prompt"`` reproduces the scripts this replaced: it recognises a
    subagent by a phrase in its system prompt and calls a drop in message count
    a compaction boundary. Both are wrong in the same way — a call that is
    neither the main spine nor a subagent still collapses the count. Claude
    Code's one-shot auxiliary calls carry the *main* agent's system prompt and
    three messages, so the phrase test passes them through and the count test
    reads each as a fresh compaction: one real trial with a single compaction
    came out as twelve near-duplicate segments of the same conversation
    (58, 59, 60 … 69 turns) instead of two. Structure answers this; a heuristic
    over message counts cannot.

    ``"system_prompt"`` is kept because it is the only way to reproduce an
    existing corpus byte-for-byte.
    """

    strict: bool = True
    splitter: str = "forest"
    redactor: Redactor = field(default_factory=Redactor)
    drop_compaction_call: bool = True
    strip_director: bool = False
    strip_billing_header: bool = False
    repair_think_tags: bool = False


# --------------------------------------------------------------------------- #
# Reading
# --------------------------------------------------------------------------- #


def iter_entries(proxy_path: Path) -> Iterator[tuple[int, dict[str, Any]]]:
    """Stream ``(index, record)`` from a proxy log.

    Streamed rather than slurped because these files routinely pass 100 MB and a
    corpus export walks tens of thousands of them.
    """

    if not proxy_path.is_file():
        return
    with open(proxy_path, errors="replace") as handle:
        index = 0
        for line in handle:
            if not line.strip():
                continue
            try:
                entry = json.loads(line)
            except Exception:
                index += 1
                continue
            yield index, entry
            index += 1


# --------------------------------------------------------------------------- #
# Per-turn assembly
# --------------------------------------------------------------------------- #


@dataclass
class _Turn:
    """One supervised turn with its full real prefix."""

    entry_index: int
    messages: list[dict[str, Any]]
    tools: list[Any]
    has_reasoning: bool
    task_present: bool
    real_task_present: bool
    opens_with_summary: bool


def _prefix_messages(
    request_messages: Sequence[Any],
    options: BuildOptions,
) -> tuple[list[dict[str, Any]], bool, bool, bool]:
    """Convert one request's message array into prefix turns.

    Returns ``(messages, task_present, real_task_present, opens_with_summary)``.

    ``task_present`` is true when any non-director text block appeared — which in
    the strict view includes harness reminders, so it is a weak signal.
    ``real_task_present`` is the one worth trusting: a text block that is neither
    a reminder nor a compaction summary, i.e. an actual instruction from the
    user. They differ exactly on segments that begin after a compaction, where
    the original task statement is gone and a summary stands in its place.
    """

    redact = options.redactor
    out: list[dict[str, Any]] = []
    task_present = False
    real_task_present = False
    opens_with_summary = False

    for message in request_messages:
        if not isinstance(message, dict):
            continue
        role = message.get("role")
        content = message.get("content")
        blocks = (
            [{"type": "text", "text": content}] if isinstance(content, str) else (content or [])
        )

        if role == "user":
            text_parts: list[str] = []
            for block in blocks:
                if not isinstance(block, dict):
                    continue
                btype = block.get("type")
                if btype == "tool_result":
                    text = tool_result_text(block)
                    if not options.strict:
                        text = _ANY_REMINDER.sub("", text)
                    elif options.strip_director:
                        text = _DIR_BLOCK.sub("", text)
                    out.append({"role": "tool", "content": redact(text), "loss": None})
                elif btype == "text":
                    raw = block.get("text", "")
                    if options.strip_director and _is_director_text(raw):
                        continue
                    if not options.strict and _is_reminder(raw):
                        continue
                    if _is_summary_text(raw):
                        # A summary block anywhere in this request means the
                        # conversation resumed from one. Looking only at the
                        # first user message misses it: Claude Code replays the
                        # files it had read as reminder blocks and appends the
                        # summary after them, so it lands in the second user
                        # message, several blocks in.
                        opens_with_summary = True
                    elif not _is_reminder(raw):
                        real_task_present = True
                    text_parts.append(raw)
                    task_present = True
            if text_parts:
                # One newline, because that is what the model received. The
                # Anthropic→OpenAI translator flattens a user turn's text blocks
                # with "\n" before sending them upstream; joining with "\n\n"
                # here would train on a separator that never reached the model.
                out.append(
                    {"role": "user", "content": redact("\n".join(text_parts)), "loss": None}
                )

        elif role == "assistant":
            rendered = assistant_content(blocks, redact, drop_block=_director_stripper(options))
            if rendered:
                out.append({"role": "assistant", "content": rendered, "loss": None})

    return out, task_present, real_task_present, opens_with_summary


def _director_stripper(options: BuildOptions):
    """Remove Cage's own injected hint block — only when asked to."""

    if not options.strip_director:
        return None
    return lambda text: _DIR_BLOCK.sub("", text)


def contains_director_hint(messages: Sequence[dict[str, Any]]) -> bool:
    """Does this conversation carry a hint Cage injected?

    Reported per row rather than acted on: shipping one silently would surprise
    a consumer, and removing one silently would surprise a different consumer.
    """

    return any(_DIR_LEAD in (m.get("content") or "") for m in messages)


def _prefix_from_openai(
    request_messages: Sequence[Any],
    options: BuildOptions,
) -> tuple[list[dict[str, Any]], bool, bool, bool]:
    """Convert an OpenAI-shaped history into prefix turns.

    This is the model's own view: the translator has already flattened blocks
    into strings, split each tool result into its own ``tool`` message, and
    moved tool calls into a structured field. Reading it directly is what makes
    a row match the input the model received, rather than matching the agent's
    request and hoping the two agree.
    """

    redact = options.redactor
    out: list[dict[str, Any]] = []
    task_present = False
    real_task_present = False
    opens_with_summary = False

    for message in request_messages:
        if not isinstance(message, dict):
            continue
        role = message.get("role")
        if role == "system":
            continue
        content = message.get("content")
        text = content if isinstance(content, str) else ""

        if role == "user":
            if options.strip_director and _is_director_text(text):
                continue
            if not options.strict:
                text = _ANY_REMINDER.sub("", text)
            elif options.strip_director:
                text = _DIR_BLOCK.sub("", text)
            if _is_summary_text(text):
                opens_with_summary = True
            elif not _is_reminder(text):
                real_task_present = True
            task_present = True
            out.append({"role": "user", "content": redact(text), "loss": None})
        elif role == "tool":
            if not options.strict:
                text = _ANY_REMINDER.sub("", text)
            elif options.strip_director:
                text = _DIR_BLOCK.sub("", text)
            out.append({"role": "tool", "content": redact(text), "loss": None})
        elif role == "assistant":
            rendered = assistant_content(
                _blocks_from_chat_message(message),
                redact,
                reasoning=(message.get("reasoning_content") or message.get("reasoning") or "").strip(),
                drop_block=_director_stripper(options),
            )
            if rendered:
                out.append({"role": "assistant", "content": rendered, "loss": None})

    return out, task_present, real_task_present, opens_with_summary


def _iter_turns(
    entries: Iterator[tuple[int, dict[str, Any]]],
    options: BuildOptions,
    main_indices: set[int] | None,
) -> Iterator[_Turn]:
    """Yield one supervised turn per main-agent call that produced content."""

    redact = options.redactor
    for index, entry in entries:
        request = request_of(entry)
        if main_indices is None:
            if _is_subagent_request(request):
                continue
        elif index not in main_indices:
            continue

        blocks = response_blocks_of(entry)
        if not blocks:
            continue

        reasoning = turn_reasoning(entry)
        target = assistant_content(
            blocks, redact, reasoning=reasoning, drop_block=_director_stripper(options)
        ).strip()
        if not target:
            continue

        parse = _prefix_from_openai if is_openai_shaped(request) else _prefix_messages
        prefix, task_present, real_task, opens_summary = parse(
            request.get("messages") or [], options
        )
        messages = [
            {
                "role": "system",
                "content": system_prompt(
                    system_text(request),
                    strip_billing_header=options.strip_billing_header,
                ),
                "loss": None,
            },
            *prefix,
            {"role": "assistant", "content": target, "loss": 1},
        ]
        yield _Turn(
            entry_index=index,
            messages=messages,
            tools=_tools_of(entry),
            has_reasoning=bool(reasoning),
            task_present=task_present,
            real_task_present=real_task,
            opens_with_summary=opens_summary,
        )


# --------------------------------------------------------------------------- #
# Segmentation
# --------------------------------------------------------------------------- #


def _looks_like_compaction_call(turn: _Turn) -> bool:
    """Is this turn the harness asking for a summary rather than the agent acting?

    Two independent signals must agree, so an ordinary plain-text reply is not
    mistaken for one: the supervised output contains no tool call (the
    instruction forbids tools), and the instruction's own wording appears in the
    user message that prompted it.
    """

    messages = turn.messages
    if not messages:
        return False
    if "<tool_call>" in (messages[-1].get("content") or ""):
        return False
    for message in reversed(messages[:-1]):
        if message.get("role") != "user":
            continue
        text = message.get("content") or ""
        return any(all(m in text for m in group) for group in _COMPACTION_INSTRUCTION_MARKERS)
    return False


def _split_by_collapse(turns: list[_Turn]) -> list[list[_Turn]]:
    """Segment on the message count collapsing.

    A normal turn only ever grows the history (by two: the assistant turn and
    its tool results). A drop of more than four can only be the harness having
    reset the context.
    """

    if not turns:
        return []
    segments: list[list[_Turn]] = []
    current: list[_Turn] = [turns[0]]
    previous = len(turns[0].messages)
    for turn in turns[1:]:
        count = len(turn.messages)
        if count < previous - 4:
            segments.append(current)
            current = []
        current.append(turn)
        previous = count
    if current:
        segments.append(current)
    return segments


def _split_by_forest(
    turns: list[_Turn], continuation_indices: set[int]
) -> list[list[_Turn]]:
    """Segment on the boundaries the conversation reconstruction identified."""

    if not turns:
        return []
    segments: list[list[_Turn]] = []
    current: list[_Turn] = []
    for turn in turns:
        if current and turn.entry_index in continuation_indices:
            segments.append(current)
            current = []
        current.append(turn)
    if current:
        segments.append(current)
    return segments


def _forest_view(proxy_path: Path) -> tuple[set[int], set[int], set[int]]:
    """Ask the conversation reconstruction for structure.

    Returns ``(main_entry_indices, compaction_call_indices, continuation_indices)``
    as indices into the *raw* log. The reconstruction numbers its calls over the
    successful records only, so the mapping back is explicit here — getting it
    wrong shifts every boundary by one, which would supervise the summary turn
    and drop the first real turn after it.
    """

    from cage.proxy.conversations import reconstruct_forest

    raw_index_of_success: list[int] = []
    successes: list[dict[str, Any]] = []
    for index, entry in iter_entries(proxy_path):
        if str(entry.get("status") or "") != "success":
            continue
        raw_index_of_success.append(index)
        successes.append(entry)

    if not successes:
        return set(), set(), set()

    forest = reconstruct_forest(successes)
    root = next((c for c in forest.conversations if c.kind == "root"), None)
    if root is None:
        return set(), set(), set()

    def to_raw(indices) -> set[int]:
        return {
            raw_index_of_success[i] for i in indices if 0 <= i < len(raw_index_of_success)
        }

    return to_raw(root.call_indices), to_raw(root.compaction_calls), to_raw(root.compaction_at)


# --------------------------------------------------------------------------- #
# Public entry point
# --------------------------------------------------------------------------- #


def build_segments(
    proxy_path: Path,
    options: BuildOptions | None = None,
) -> tuple[list[Segment], list[str]]:
    """Build every complete-conversation segment in one trial's proxy log.

    Returns ``(segments, problems)``. *problems* names build-time defects that
    made a segment unusable — unbalanced reasoning tags, a workspace the
    assistant addresses differently from the one the system prompt declares.
    They are returned rather than raised because one broken trial must not abort
    an export of ten thousand.
    """

    options = options or BuildOptions()
    problems: list[str] = []

    main_indices: set[int] | None = None
    compaction_calls: set[int] = set()
    continuations: set[int] = set()
    if options.splitter == "forest":
        main_indices, compaction_calls, continuations = _forest_view(proxy_path)

    turns = list(_iter_turns(iter_entries(proxy_path), options, main_indices))
    if not turns:
        return [], problems

    if options.splitter == "forest":
        groups = _split_by_forest(turns, continuations)
        if options.drop_compaction_call:
            groups = [[t for t in g if t.entry_index not in compaction_calls] for g in groups]
    else:
        groups = _split_by_collapse(turns)
        if options.drop_compaction_call:
            trimmed: list[list[_Turn]] = []
            for position, group in enumerate(groups):
                # The compaction call is always the turn immediately before the
                # collapse, so it can only ever be a group's last turn. A final
                # group ending in one means the trial stopped right after
                # compacting; drop it there too rather than supervising a
                # summary as if it were the agent's work.
                if group and len(group) > 1 and _looks_like_compaction_call(group[-1]):
                    group = group[:-1]
                trimmed.append(group)
            groups = trimmed

    groups = [g for g in groups if g]
    segments: list[Segment] = []
    for position, group in enumerate(groups):
        # The group's last turn already carries the whole group as its prefix,
        # so the complete conversation needs no reassembly — only supervising
        # every assistant turn instead of the single target one.
        last = group[-1]
        messages = [dict(m) for m in last.messages]

        repaired = 0
        unbalanced = False
        for message in messages:
            if message.get("role") != "assistant":
                message["loss"] = 0
                continue
            content = message.get("content") or ""
            if options.repair_think_tags:
                content, fixed = repair_think_tags(content)
                if fixed:
                    message["content"] = content
                    repaired += 1
            message["loss"] = 1
            if options.repair_think_tags and not think_tags_balanced(content):
                unbalanced = True

        if unbalanced:
            problems.append(f"segment {position}: unbalanced <think> tags")
            continue

        assistants = [m for m in messages if m.get("role") == "assistant"]
        if not assistants:
            problems.append(f"segment {position}: no assistant turn")
            continue

        workdir = primary_workdir(messages[0].get("content") or "")
        rewritten = redaction_rewrites_workdir(options.redactor, workdir)
        if rewritten:
            problems.append(
                f"segment {position}: redaction rewrites the agent's own working "
                f"directory ({workdir} -> {rewritten}); every sample would contradict "
                f"its own system prompt. Fix the host-path patterns."
            )
            continue

        with_think = sum(1 for m in assistants if "</think>" in (m.get("content") or ""))
        history = [t for t in group[:-1]]
        segments.append(
            Segment(
                index=position,
                n_segments=len(groups),
                messages=messages,
                tools=last.tools,
                opens_with_summary=group[0].opens_with_summary,
                real_task_present=group[0].real_task_present,
                task_present=group[0].task_present,
                stats={
                    "n_assistant": len(assistants),
                    "n_supervised": len(assistants),
                    "n_supervised_with_think": with_think,
                    "think_ratio": round(with_think / len(assistants), 4),
                    "n_think_tag_repaired": repaired,
                    "n_turns_in_segment": len(group),
                    "n_turns_with_reasoning": sum(1 for t in history if t.has_reasoning),
                    "workdir": workdir,
                    "has_director_hint": contains_director_hint(messages),
                    # Which recorded call this row is. Message counts repeat
                    # within a trial — a retry, a background call — so a count
                    # cannot identify the source, and anything checking a row
                    # against the body that produced it needs to say exactly
                    # which one that was.
                    "source_call_index": last.entry_index,
                },
            )
        )

    return segments, problems
