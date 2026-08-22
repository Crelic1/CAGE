"""Walk selected runs and write their trajectories out as training rows.

Two rules shape this module.

**Contamination is refused, preference is filtered.** A benchmark's admission
gates say a trajectory would be wrong to learn from; those refuse by default and
only open under an explicit ``--allow <code>``. Everything else — did it pass,
how much reasoning, how many per task — is a selection preference belonging to
whoever assembles the training mix, so it is off unless asked for. Exporting
less than was asked for, silently, is the one failure this design will not
tolerate: every drop is counted and reported.

**Cheap questions first.** Most filters (agent, model, task, pass/fail) are
answerable from small per-trial files. Segment shape, reasoning ratio and turn
counts need the proxy log, which routinely exceeds 100 MB. Applying the cheap
filters before parsing anything is what makes a dry run over a 2,500-trial run
finish in seconds instead of an hour.
"""

from __future__ import annotations

import collections
import fnmatch
import json
import random
from collections.abc import Iterator, Sequence
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from cage.artifacts.run_storage import RunRef, discover_runs, iter_live_trial_dirs
from cage.corpus.build import BuildOptions, build_segments
from cage.corpus.records import Segment, TrainingAdmission, TrialCorpusView


@dataclass
class Selection:
    """Every filter the exporter understands.

    The benchmark-specific ones are deliberately two generic knobs rather than
    named flags: ``allow`` matches gate codes and ``where`` matches provenance
    keys, both opaque strings the benchmark chose. A framework flag named after
    one domain's gate would be a layering violation and would need editing every
    time a benchmark gained a rule.
    """

    run_ids: tuple[str, ...] = ()
    run_globs: tuple[str, ...] = ()
    benchmarks: tuple[str, ...] = ()
    agents: tuple[str, ...] = ()
    models: tuple[str, ...] = ()
    served_models: tuple[str, ...] = ()
    tasks: tuple[str, ...] = ()

    passed: bool | None = None
    allow: frozenset[str] = frozenset()
    where: tuple[tuple[str, str], ...] = ()

    compacted: bool | None = None
    first_segment_only: bool = False
    segment: int | None = None
    min_turns: int | None = None
    max_turns: int | None = None
    think_ratio_min: float | None = None

    per_task_cap: int | None = None
    limit: int | None = None
    sample: int | None = None
    seed: int = 0

    def matches_run(self, ref: RunRef) -> bool:
        if self.run_ids and ref.run_id not in self.run_ids:
            return False
        if self.run_globs and not any(
            fnmatch.fnmatch(ref.run_id, g) for g in self.run_globs
        ):
            return False
        if self.benchmarks and ref.benchmark not in self.benchmarks:
            return False
        if self.agents and ref.agent not in self.agents:
            return False
        if self.models and ref.model not in self.models:
            return False
        return True


@dataclass
class Tally:
    """Why rows did not make it out. Reported, never silent."""

    runs: int = 0
    trials_seen: int = 0
    trials_kept: int = 0
    rows: int = 0
    gates: collections.Counter = field(default_factory=collections.Counter)
    filters: collections.Counter = field(default_factory=collections.Counter)
    problems: collections.Counter = field(default_factory=collections.Counter)
    by_run: collections.Counter = field(default_factory=collections.Counter)
    by_model: collections.Counter = field(default_factory=collections.Counter)
    tasks: set = field(default_factory=set)
    compacted_rows: int = 0
    summary_opened_rows: int = 0
    director_hint_rows: int = 0
    bytes_written: int = 0

    def as_dict(self) -> dict[str, Any]:
        return {
            "runs": self.runs,
            "trials_seen": self.trials_seen,
            "trials_kept": self.trials_kept,
            "rows": self.rows,
            "unique_tasks": len(self.tasks),
            "compacted_rows": self.compacted_rows,
            "summary_opened_rows": self.summary_opened_rows,
            "director_hint_rows": self.director_hint_rows,
            "bytes_written": self.bytes_written,
            "rejected_by_gate": dict(self.gates.most_common()),
            "dropped_by_filter": dict(self.filters.most_common()),
            "build_problems": dict(self.problems.most_common()),
            "rows_by_run": dict(self.by_run.most_common()),
            "rows_by_model": dict(self.by_model.most_common()),
        }


def _local_module(recorded: Path, benchmark: str) -> Path:
    """Map a recorded benchmark module path onto this checkout.

    A run records absolute paths, so replaying its spec verbatim loads whatever
    code sits at those paths *now* — usually another checkout, whose gates may
    be older than the ones being asked for. Configuration should come from the
    run; the code implementing it should come from here. When this checkout has
    the same benchmark package, its copy wins.
    """

    from cage.benchmarks.registry import EXAMPLES_DIR

    for name in {benchmark, recorded.parent.name}:
        if not name:
            continue
        candidate = EXAMPLES_DIR / name / recorded.name
        if candidate.is_file():
            return candidate
    return recorded


def _benchmark_block(project_file: Path) -> dict[str, Any] | None:
    from cage.benchmarks.registry import load_project_yaml

    try:
        raw = load_project_yaml(project_file)
    except Exception:
        return None
    eval_raw = raw.get("eval", {})
    block = eval_raw.get("benchmark", eval_raw) if isinstance(eval_raw, dict) else {}
    return block if isinstance(block, dict) and "module" in block else None


def _load_benchmark_for_run(ref: RunRef) -> Any | None:
    """Build the Benchmark this run used: its configuration, our code.

    The run wrote its whole effective ``project.yml`` next to its artifacts, so
    the gates see the catalog, materials overlay and tier the run really had —
    not whatever the repo's committed project file says today. Falls back to the
    registry entry for runs that predate that snapshot.

    Constructed without ``setup()``: exporting a corpus reads finished runs and
    must not start the machinery for producing new ones.
    """

    from cage.benchmarks.loader import load_benchmark_from_module
    from cage.benchmarks import registry

    candidates: list[Path] = [ref.run_dir / "project.yml"]
    try:
        candidates.append(registry.resolve_benchmark(ref.benchmark).resolved_project_file)
    except Exception:
        pass

    for project_file in candidates:
        if not project_file.is_file():
            continue
        block = _benchmark_block(project_file)
        if block is None:
            continue
        recorded = Path(block["module"])
        if not recorded.is_absolute():
            recorded = project_file.parent / recorded
        module = _local_module(recorded, ref.benchmark)
        kwargs = {k: v for k, v in block.items() if k not in ("module", "class")}
        try:
            benchmark = load_benchmark_from_module(
                module, class_name=block.get("class"), kwargs=kwargs
            )
        except Exception:
            continue
        if benchmark is not None:
            return benchmark
    return None


def run_ref_for(run_dir: Path) -> RunRef | None:
    """Locate one run by its directory, for callers that hold a path.

    The web inspector addresses runs by path, not by the coordinates
    :func:`discover_runs` yields. Rather than re-derive the naming convention
    here, ask storage for the runs under this run's own ``.cage_runs`` and pick
    the match — so a layout change lands in one place, as it does everywhere
    else on this path.
    """

    cage_runs = run_dir.parent.parent
    for ref in discover_runs(cage_runs):
        if ref.run_dir == run_dir:
            return ref
    return None


def _served_model(proxy_path: Path) -> str:
    """The model name the upstream actually answered as.

    A model slot is our label for an endpoint and can be repointed between runs;
    reproducing a result later needs the name the endpoint reported, and only
    the proxy record has it.
    """

    if not proxy_path.is_file():
        return ""
    try:
        with open(proxy_path, errors="replace") as handle:
            for line in handle:
                if not line.strip():
                    continue
                entry = json.loads(line)
                request = entry.get("openai_request") or entry.get("anthropic_request") or {}
                upstream = entry.get("upstream_response") or {}
                return str(request.get("model") or upstream.get("model") or "")
    except Exception:
        return ""
    return ""


def _is_terminal(trial_dir: Path, view: TrialCorpusView) -> bool:
    """Has this trial finished?

    A run creates every trial directory during planning, so an unfinished trial
    is indistinguishable from a failed one by directory alone. Exporting one
    mid-flight would capture a truncated trajectory and — worse for any caller
    that caches by trial id — record that verdict permanently.
    """

    if view.scores:
        return True
    status = str(view.meta.get("status") or "")
    return status in ("completed", "failed")


def _matches_task(trial_id: str, wanted: Sequence[str]) -> bool:
    """Match a task filter against a trial id, flat or nested.

    A nested id is ``<task>/<variant>``, so ``--task foo`` selects every variant
    of ``foo`` as well as a flat trial named ``foo``. The ``_``→``:`` form is
    accepted too, because that is how several benchmarks spell a task id.
    """

    head = trial_id.split("/", 1)[0]
    candidates = {trial_id, head, head.replace("_", ":", 1), trial_id.replace("_", ":", 1)}
    return any(t in candidates for t in wanted)


def _passes_where(provenance: dict[str, Any], where: Sequence[tuple[str, str]]) -> bool:
    for key, wanted in where:
        actual = provenance.get(key)
        if actual is None:
            return False
        if str(actual).lower() != wanted.lower():
            return False
    return True


def iter_rows(
    root: Path,
    selection: Selection,
    build_options: BuildOptions | None = None,
    tally: Tally | None = None,
    on_run: Callable[[RunRef], None] | None = None,
) -> Iterator[dict[str, Any]]:
    """Yield one export row per admitted segment across the selected runs."""

    build_options = build_options or BuildOptions()
    tally = tally if tally is not None else Tally()
    exported_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    per_task: collections.Counter = collections.Counter()

    for ref in discover_runs(root):
        if not selection.matches_run(ref):
            continue
        tally.runs += 1
        if on_run is not None:
            on_run(ref)
        benchmark = _load_benchmark_for_run(ref)

        # Storage owns where trials live. Asking it covers the flat layout, the
        # nested ``trials/<task>/<variant>/`` one a benchmark emitting a variant
        # key produces, and the legacy mode subdirectory — and it resolves
        # resume archives properly: a superseded attempt beside a live sibling
        # is skipped, but a trial that only ever produced archives still
        # surfaces its most recent one instead of vanishing.
        #
        # Walking ``trials/`` directly, as this did, silently exported nothing
        # at all from a nested run: the first level holds task directories,
        # which carry none of the trial marker files, so every one was filtered
        # out and the export finished successfully with zero rows.
        trials_root = ref.run_dir / "trials"
        for trial_dir in iter_live_trial_dirs(ref.run_dir):
            try:
                trial_id = trial_dir.relative_to(trials_root).as_posix()
            except ValueError:
                trial_id = trial_dir.name
            if selection.tasks and not _matches_task(trial_id, selection.tasks):
                continue
            tally.trials_seen += 1

            view = TrialCorpusView(
                trial_dir=trial_dir,
                run_dir=ref.run_dir,
                trial_id=trial_id,
                run_id=ref.run_id,
                benchmark=ref.benchmark,
                agent=ref.agent,
                model=ref.model,
            )
            if not _is_terminal(trial_dir, view):
                tally.filters["not finished yet"] += 1
                continue

            if benchmark is not None:
                try:
                    admission = benchmark.admit_for_training(view)
                except Exception as exc:  # noqa: BLE001
                    tally.problems[f"gate raised {type(exc).__name__}"] += 1
                    continue
            else:
                admission = TrainingAdmission.ok()

            blocking = [code for code in admission.reasons if code not in selection.allow]
            if blocking:
                for code in blocking:
                    tally.gates[code] += 1
                continue

            provenance = dict(admission.provenance)
            if selection.passed is not None:
                verdict = provenance.get("passed")
                if verdict is None:
                    # This benchmark does not answer in pass/fail terms. Saying
                    # "not passed" would be a claim its scorer never made.
                    tally.filters["no pass/fail verdict for this benchmark"] += 1
                    continue
                if bool(verdict) != selection.passed:
                    tally.filters["--passed/--failed"] += 1
                    continue
            if selection.where and not _passes_where(provenance, selection.where):
                tally.filters["--where"] += 1
                continue

            served = _served_model(view.proxy_log)
            if selection.served_models and served not in selection.served_models:
                tally.filters["served model"] += 1
                continue

            try:
                segments, problems = build_segments(view.proxy_log, build_options)
            except Exception as exc:  # noqa: BLE001
                tally.problems[f"build raised {type(exc).__name__}"] += 1
                continue
            for problem in problems:
                tally.problems[problem.split(":", 1)[-1].strip()[:60]] += 1
            if not segments:
                tally.filters["no usable segment"] += 1
                continue

            kept_any = False
            for segment in segments:
                if not _segment_wanted(segment, selection, tally):
                    continue
                task = provenance.get("task") or trial_id.replace("_", ":", 1)
                if selection.per_task_cap is not None:
                    if per_task[task] >= selection.per_task_cap:
                        tally.filters["--per-task-cap"] += 1
                        continue
                    per_task[task] += 1

                if not kept_any:
                    kept_any = True
                    tally.trials_kept += 1
                yield _row(
                    ref, view, segment, provenance, served, task, admission, exported_at
                )
                tally.rows += 1
                tally.by_run[ref.run_id] += 1
                tally.by_model[ref.model] += 1
                tally.tasks.add(task)
                if segment.n_segments > 1:
                    tally.compacted_rows += 1
                if segment.opens_with_summary:
                    tally.summary_opened_rows += 1
                if segment.stats.get("has_director_hint"):
                    tally.director_hint_rows += 1
                if selection.limit is not None and tally.rows >= selection.limit:
                    return


def _segment_wanted(segment: Segment, selection: Selection, tally: Tally) -> bool:
    if selection.first_segment_only and segment.index != 0:
        tally.filters["--first-segment-only"] += 1
        return False
    if selection.segment is not None and segment.index != selection.segment:
        tally.filters["--segment"] += 1
        return False
    if selection.compacted is not None and (segment.n_segments > 1) != selection.compacted:
        tally.filters["--compacted"] += 1
        return False
    turns = segment.n_turns
    if selection.min_turns is not None and turns < selection.min_turns:
        tally.filters["--min-turns"] += 1
        return False
    if selection.max_turns is not None and turns > selection.max_turns:
        tally.filters["--max-turns"] += 1
        return False
    if selection.think_ratio_min is not None:
        if segment.stats.get("think_ratio", 0.0) < selection.think_ratio_min:
            tally.filters["--think-ratio-min"] += 1
            return False
    return True


def _row(
    ref: RunRef,
    view: TrialCorpusView,
    segment: Segment,
    provenance: dict[str, Any],
    served_model: str,
    task: str,
    admission: TrainingAdmission,
    exported_at: str,
) -> dict[str, Any]:
    """One training row: the conversation, plus everything needed to trace it.

    ``run_id`` and ``trial_id`` locate the source directory exactly, so any row
    in a multi-gigabyte file can be taken back to the trial that produced it.
    """

    collected_at = ""
    try:
        collected_at = datetime.fromtimestamp(
            view.trial_dir.stat().st_mtime, timezone.utc
        ).isoformat(timespec="seconds")
    except OSError:
        pass

    meta = {
        "run_id": ref.run_id,
        "trial_id": view.trial_id,
        "task": task,
        "benchmark": ref.benchmark,
        "agent": ref.agent,
        "model_slot": ref.model,
        "served_model": served_model,
        "lifecycle": ref.lifecycle,
        "segment": segment.index,
        "n_segments": segment.n_segments,
        "compacted": segment.n_segments > 1,
        "opens_with_summary": segment.opens_with_summary,
        "real_task_present": segment.real_task_present,
        "task_present": segment.task_present,
        "allowed_gates": sorted(admission.reasons),
        "collected_at": collected_at,
        "exported_at": exported_at,
        **provenance,
        **segment.stats,
    }
    return {
        "messages": segment.messages,
        "tools": segment.tools,
        "id": f"{ref.run_id}/{view.trial_id}#{segment.index}",
        "task": task,
        "src_model": ref.model,
        "_view": "expert_trajectory",
        "_meta": meta,
    }


def write_jsonl(
    rows: Iterator[dict[str, Any]],
    out: Path,
    split_by: str = "",
    tally: Tally | None = None,
) -> dict[str, int]:
    """Write rows to one file, or to one file per run/model under a directory."""

    tally = tally if tally is not None else Tally()
    written: dict[str, int] = {}
    if not split_by:
        out.parent.mkdir(parents=True, exist_ok=True)
        with open(out, "w") as handle:
            for row in rows:
                line = json.dumps(row, ensure_ascii=False)
                handle.write(line + "\n")
                tally.bytes_written += len(line) + 1
        written[str(out)] = tally.rows
        return written

    out.mkdir(parents=True, exist_ok=True)
    handles: dict[str, Any] = {}
    key_of = (
        (lambda r: r["_meta"]["run_id"])
        if split_by == "run"
        else (lambda r: r["_meta"]["model_slot"])
    )
    try:
        for row in rows:
            key = key_of(row) or "unknown"
            handle = handles.get(key)
            if handle is None:
                handle = handles[key] = open(out / f"{key}.jsonl", "w")
            line = json.dumps(row, ensure_ascii=False)
            handle.write(line + "\n")
            tally.bytes_written += len(line) + 1
            written[key] = written.get(key, 0) + 1
    finally:
        for handle in handles.values():
            handle.close()
    return written


def reservoir_sample(rows: Iterator[dict[str, Any]], k: int, seed: int) -> list[dict[str, Any]]:
    """Take *k* rows uniformly without holding the whole corpus in memory."""

    rng = random.Random(seed)
    kept: list[dict[str, Any]] = []
    for index, row in enumerate(rows):
        if index < k:
            kept.append(row)
        else:
            j = rng.randint(0, index)
            if j < k:
                kept[j] = row
    return kept
