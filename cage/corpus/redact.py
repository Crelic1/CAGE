"""Text transforms applied on the way out, and the one rule about them.

**Export is faithful by default.** A row reproduces what the record says the
agent sent. Nothing is rewritten because it would be inconvenient to train on —
that judgement belongs to whoever builds the training mix, who can apply it to
a faithful corpus but cannot recover what an export already threw away.

So two things that look similar are kept apart:

* **Fidelity repairs** are on, because they make the row *more* like the real
  exchange. Restoring a ``<think>`` opening tag the chat template counted as
  prompt is not editing the model's output; it is undoing an artifact of how
  the output was framed.

* **Content edits** are off unless asked for. Claude Code's per-call billing
  header, and a director hint Cage injected, were both genuinely in the system
  prompt the agent sent. Whether they belong in a training set is a real
  question with a real answer — and it is not this layer's to give.

Host-path redaction is the exception, and on a different axis: it is neither
fidelity nor training but privacy. The machine that ran the experiment has
paths that must not ship. It stays on, and it must never touch the container's
own working directory — see :func:`redaction_rewrites_workdir` for why that is
checked as a rule rather than looked for in the output.
"""


from __future__ import annotations

import re
from collections.abc import Sequence
from dataclasses import dataclass

# The proxy stamps a per-call billing header as the first system line. It varies
# every call (it carries a cache key), so it is transport, not prompt.
_BILLING_LINE = re.compile(r"^x-anthropic-billing-header:[^\n]*\n?", re.M)

# The harness states the agent's working directory in the environment block.
# Parsing it beats hardcoding a path: agents declare their own home, and a
# corpus may span several of them.
_PRIMARY_WORKDIR = re.compile(r"Primary working directory:\s*(\S+)")

# Default private-path patterns, as regex fragments. They name a *shape* —
# a workspace root under ``/data``, with or without an owner segment and with
# or without a numbered suffix — and deliberately not any one machine's
# directories: a framework that ships its author's paths as the default is
# both wrong everywhere else and a leak here. An install whose runs live
# somewhere else passes its own roots to ``Redactor(host_path_patterns=...)``.
# Over-matching is the safe direction; under-matching ships a real host path
# into a training set, which is the one thing this layer exists to prevent.
DEFAULT_HOST_PATH_PATTERNS: tuple[str, ...] = (
    r"/data(?:/[^/\s]+)?/workspace(?:-\d+)?",
)
DEFAULT_TRAILING_SEGMENTS = 2
DEFAULT_REPLACEMENT = "/workspace/"


@dataclass(frozen=True)
class Redactor:
    """Applies host-path redaction to trajectory text.

    *host_path_patterns* are regex fragments naming private roots. Each is
    extended by up to *trailing_segments* further path components so that
    ``/data/team/workspace/alice/run7/poc.bin`` collapses to
    ``/workspace/poc.bin`` rather than leaking the user and run name.
    """

    host_path_patterns: Sequence[str] = DEFAULT_HOST_PATH_PATTERNS
    trailing_segments: int = DEFAULT_TRAILING_SEGMENTS
    replacement: str = DEFAULT_REPLACEMENT

    def __post_init__(self) -> None:
        joined = "|".join(f"(?:{p})" for p in self.host_path_patterns) or r"(?!)"
        compiled = re.compile(
            rf"(?:{joined})(?:/[^/\s]+){{0,{self.trailing_segments}}}/?"
        )
        object.__setattr__(self, "_pattern", compiled)

    def __call__(self, text: str) -> str:
        if not isinstance(text, str):
            return text
        return self._pattern.sub(self.replacement, text)


def system_prompt(system_text: str, *, strip_billing_header: bool = False) -> str:
    """The system prompt as recorded.

    Verbatim by default, including Claude Code's Agent-SDK preamble, its
    ``<system-reminder>`` documentation block, and the model identity line —
    all of which the agent really sent.

    ``strip_billing_header`` removes Claude Code's per-call
    ``x-anthropic-billing-header`` line. Off by default because the agent did
    send it: the proxy drops it only on the OpenAI translation path, to keep
    the prefix cacheable, and forwards it intact to an Anthropic upstream.
    """

    text = _BILLING_LINE.sub("", system_text) if strip_billing_header else system_text
    return text.strip()


def primary_workdir(system_text: str) -> str:
    """The agent's working directory as the system prompt declares it.

    Empty when the harness does not state one, in which case
    :func:`redaction_rewrites_workdir` has nothing to check and stays silent
    rather than guessing.
    """

    match = _PRIMARY_WORKDIR.search(system_text or "")
    return match.group(1).rstrip("/") if match else ""


def redaction_rewrites_workdir(redact: Redactor, workdir: str) -> str:
    """Would redaction rewrite the agent's own working directory?

    This is the invariant the corpus must never violate, and it is a property of
    the *rule*, not of any one trajectory: if a host-path pattern is broad
    enough to swallow the container's working directory, every sample it touches
    becomes self-contradictory — the system prompt declares one directory and
    the commands address another — and a model trained on it learns to ignore
    the system prompt and walk a path that does not exist. That is not
    hypothetical; it happened, and it cost every SFT run built before it was
    found.

    Checking the rule rather than the output is what makes this sound. The
    earlier attempt scanned assistant turns for the placeholder string and was
    wrong in both directions: a target application with its own ``/workspace``
    directory, or a Java source file quoting ``D:/workspace/img``, tripped it
    with nothing whatsoever having been rewritten. Substring evidence cannot
    distinguish "redaction rewrote a real path" from "the text legitimately says
    /workspace"; asking the redactor directly can.

    Returns the rewritten form when the rule is unsafe, ``""`` when it is fine.
    """

    if not workdir:
        return ""
    probe = f"{workdir}/probe.txt"
    rewritten = redact(probe)
    return rewritten if rewritten != probe else ""
