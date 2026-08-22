"""Data shapes shared across the corpus pipeline.

Three types cross a layer boundary and so live here rather than beside their
producers:

  * :class:`TrainingAdmission` — what a benchmark answers when asked whether a
    trial may be used for training.
  * :class:`TrialCorpusView` — the read-only handle a benchmark gets to answer
    that question, so Layer 2 never reaches into storage layout itself.
  * :class:`Segment` — one complete conversation extracted from a trial.
"""

from __future__ import annotations

import json
import re
from collections.abc import Iterator, Mapping, Sequence
from dataclasses import dataclass, field
from functools import cached_property
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class TrainingAdmission:
    """A benchmark's verdict on whether one trial may enter a training corpus.

    ``reasons`` are **gate codes**, not prose: short stable identifiers the
    benchmark chooses (``"answer_in_workspace"``, ``"eval_set_leak"``, …). The
    framework
    matches them against ``--allow`` and prints them in reports, but never
    interprets one — that is the whole reason a benchmark can add a gate
    without the framework learning its name.

    ``detail`` carries the human sentence for each code, so a report can explain
    a rejection without the framework knowing what the code means.

    ``provenance`` is merged into every exported row's ``_meta`` and is
    filterable through ``--where key=value``. Same contract: opaque keys.
    """

    admitted: bool
    reasons: tuple[str, ...] = ()
    detail: Mapping[str, str] = field(default_factory=dict)
    provenance: Mapping[str, Any] = field(default_factory=dict)

    @classmethod
    def ok(cls, **provenance: Any) -> "TrainingAdmission":
        return cls(admitted=True, provenance=provenance)

    def rejected(self, code: str, why: str = "") -> "TrainingAdmission":
        """Return a copy carrying one more gate code (chainable)."""

        detail = dict(self.detail)
        if why:
            detail[code] = why
        return TrainingAdmission(
            admitted=False,
            reasons=(*self.reasons, code),
            detail=detail,
            provenance=self.provenance,
        )

    def with_provenance(self, **fields: Any) -> "TrainingAdmission":
        return TrainingAdmission(
            admitted=self.admitted,
            reasons=self.reasons,
            detail=self.detail,
            provenance={**self.provenance, **fields},
        )


@dataclass
class TrialCorpusView:
    """Read-only handle on one trial, for a benchmark's admission gates.

    Layer 2 asks questions here instead of joining paths itself, so a change to
    storage layout (packed runs, canonical artifact records) lands in one place.
    Every accessor is best-effort: a missing artifact answers empty, never
    raises — a half-written trial must not abort a corpus export.
    """

    trial_dir: Path
    run_dir: Path
    trial_id: str
    run_id: str
    benchmark: str = ""
    agent: str = ""
    model: str = ""

    @cached_property
    def workspace(self) -> Path:
        """The agent's captured workspace, if this run kept one."""

        return self.trial_dir / "workspace"

    @cached_property
    def scores(self) -> dict[str, Any]:
        """Raw per-scorer mapping (``{scorer_name: {...}}``); ``{}`` if unscored."""

        from cage.artifacts.run_storage import RunStorage

        try:
            return RunStorage(run_dir=self.run_dir).load_trial_scores(self.trial_dir)
        except Exception:
            return {}

    @cached_property
    def meta(self) -> dict[str, Any]:
        """Trial ``meta.json`` — status, timing, termination."""

        from cage.artifacts.run_storage import RunStorage

        try:
            return RunStorage(run_dir=self.run_dir).load_trial_meta(self.trial_dir)
        except Exception:
            return {}

    @cached_property
    def run_config(self) -> dict[str, Any]:
        """The run's effective configuration.

        ``project.yml`` is preferred: the run writes its whole resolved spec
        there, including the benchmark block. ``config.yaml`` is the short
        header (agent, model, paths) and only answers a fraction of what a gate
        may need to ask.
        """

        for name in ("project.yml", "config.yaml"):
            path = self.run_dir / name
            if not path.is_file():
                continue
            try:
                import yaml

                data = yaml.safe_load(path.read_text(errors="replace"))
            except Exception:
                continue
            if isinstance(data, dict):
                return data
        return {}

    def read_json(self, relative: str) -> dict[str, Any]:
        """Parse a JSON artifact under the trial dir; ``{}`` if missing/broken.

        For benchmark-private runtime records (``runtime/<name>.json``) that the
        framework has no reason to model.
        """

        path = self.trial_dir / relative
        if not path.is_file():
            return {}
        try:
            data = json.loads(path.read_text(errors="replace"))
        except Exception:
            return {}
        return data if isinstance(data, dict) else {}

    def read_text(self, relative: str) -> str:
        """Read a text artifact under the trial dir; ``""`` if missing."""

        path = self.trial_dir / relative
        try:
            return path.read_text(errors="replace") if path.is_file() else ""
        except OSError:
            return ""

    @cached_property
    def proxy_log(self) -> Path:
        from cage.artifacts.run_storage import RunStorage

        try:
            return RunStorage(run_dir=self.run_dir).load_trial_proxy_log(self.trial_dir)
        except Exception:
            return self.trial_dir / "proxy" / "proxy.jsonl"

    def scan_tool_commands(
        self, pattern: re.Pattern[str], limit: int | None = None
    ) -> list[str]:
        """Tool-call inputs in this trial whose JSON matches *pattern*.

        The mechanism is universal — walk the recorded ``tool_use`` blocks and
        match — while the pattern is domain knowledge the benchmark owns. That
        split is why "did the agent fetch the answer key off the internet?" can
        be asked without the framework knowing what an answer key looks like.

        Streams the log, and stops at *limit* hits: these files routinely exceed
        100 MB, and a gate almost always only needs to know *whether*.
        """

        hits: list[str] = []
        path = self.proxy_log
        if not path.is_file():
            return hits
        try:
            with open(path, errors="replace") as handle:
                for line in handle:
                    if not line.strip():
                        continue
                    try:
                        entry = json.loads(line)
                    except Exception:
                        continue
                    response = entry.get("anthropic_response") or {}
                    for block in response.get("content") or []:
                        if not isinstance(block, dict) or block.get("type") != "tool_use":
                            continue
                        payload = json.dumps(block.get("input") or {}, ensure_ascii=False)
                        if pattern.search(payload):
                            hits.append(payload[:400])
                            if limit is not None and len(hits) >= limit:
                                return hits
        except OSError:
            return hits
        return hits


@dataclass
class Segment:
    """One complete conversation lifted out of a trial.

    A trial with no compaction yields exactly one segment. Each compaction ends
    a segment and starts the next, because at that point the harness *replaces*
    the history rather than appending to it — there is no single context the
    model ever saw spanning both sides, so joining them would fabricate one.

    ``messages`` is already in export shape: ``role`` / ``content`` / ``loss``,
    with every assistant turn supervised.
    """

    index: int
    n_segments: int
    messages: list[dict[str, Any]]
    tools: list[Any] = field(default_factory=list)
    opens_with_summary: bool = False
    real_task_present: bool = False
    task_present: bool = False
    stats: dict[str, Any] = field(default_factory=dict)

    @property
    def n_turns(self) -> int:
        return sum(1 for m in self.messages if m.get("role") == "assistant")

    def iter_assistant(self) -> Iterator[dict[str, Any]]:
        for message in self.messages:
            if message.get("role") == "assistant":
                yield message


def as_sequence(value: Any) -> Sequence[Any]:
    """Coerce a maybe-scalar config value into a sequence."""

    if value is None:
        return ()
    if isinstance(value, (str, bytes)):
        return (value,)
    if isinstance(value, Sequence):
        return value
    return (value,)
