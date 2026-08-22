#!/usr/bin/env python3
"""Build a CyberGym *materials overlay* for the external-ARVO task set.

Why this exists
---------------
Upstream CyberGym ships four difficulty levels, each adding one more piece of
evidence to the agent's workspace::

    level0  repo-vul.tar.gz
    level1  + description.txt   (what the vulnerability is)
    level2  + error.txt         (the vulnerable program's sanitizer output)
    level3  + patch.diff, repo-fix.tar.gz

The external-ARVO payload tree (``datasets/payloads-arvo``) only ever carried
``repo-vul.tar.gz`` for real. Its ``description.txt`` is a template sentence
generated from ``meta.json`` ("An OSS-Fuzz libfuzzer fuzz target on the curl
project triggered UBSAN…") and its ``error.txt`` is a reconstructed stub, not a
sanitizer trace. Running level1/level2 against those files produces numbers that
are not comparable to the CyberGym report.

The gendesc runs closed that gap: for each environment an agent read the source,
the ground-truth PoC and the real crash, then wrote a four-tier description
ladder (level0 weakest hint → level3 fully specified), and the trial's startup
preflight captured the *real* sanitizer output by running the ground-truth PoC
against the exact vulnerable binary.

This script harvests both out of the run trees and writes a small, self-contained
overlay directory that the benchmark stages instead of the payload placeholders::

    <out>/manifest.json
    <out>/arvo/<id>/description.level0.txt … description.level3.txt
    <out>/arvo/<id>/error.txt

Point ``eval.benchmark.materials_dir`` at ``<out>`` and pick a tier with
``eval.benchmark.description_tier`` (or ``cage run … --description-tier level2``).

Usage
-----
    python3 external_arvo/scripts/build_materials_overlay.py \
        --run-dir '.cage_runs/claude_code:glm-5.2-sii:stateless/gendesc-…' \
        --out datasets/materials-arvo/20260728-gendesc-ready3074-c16
"""

from __future__ import annotations

import argparse
import json
import shutil
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]      # examples/cybergym/external_arvo
CYBERGYM = ROOT.parent                          # examples/cybergym

# Tier files written per task; index i in descriptions.json → level{i}, the same
# convention build_local_snapshot.py uses for ``description_by_level``.
MAX_TIERS = 4


def _read_json_or_none(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def _normalize_task_id(raw: Any) -> str:
    text = str(raw or "").strip()
    if not text:
        return ""
    if ":" in text:
        subset, _, num = text.partition(":")
        return f"{subset}:{num}"
    if "_" in text:
        subset, _, num = text.partition("_")
        return f"{subset}:{num}"
    return text


def _descriptions(path: Path) -> list[str]:
    """The agent's density ladder as a clean list, or ``[]``.

    Accepts the two shapes the gendesc scorer tolerates: a bare list of strings,
    or a list of ``{"text"/"description": …}`` objects.
    """
    data = _read_json_or_none(path)
    if isinstance(data, dict):
        data = data.get("descriptions") or data.get("candidates")
    if not isinstance(data, list):
        return []
    out: list[str] = []
    for item in data:
        text = item if isinstance(item, str) else str(
            (item or {}).get("text") or (item or {}).get("description") or ""
        )
        text = text.strip()
        if text:
            out.append(text)
    return out


@dataclass
class Candidate:
    """One trial's harvestable materials for one task."""

    task_id: str
    trial_dir: Path
    descriptions: list[str]
    crash_log: Path | None
    completed: bool
    mtime_ms: int

    @property
    def rank(self) -> tuple[int, int, int, int, int]:
        # Prefer a trial that produced descriptions, then a full ladder, then a
        # real crash log, then a completed trial, then the most recent one.
        return (
            1 if self.descriptions else 0,
            min(len(self.descriptions), MAX_TIERS),
            1 if self.crash_log else 0,
            1 if self.completed else 0,
            self.mtime_ms,
        )


def scan_run(run_dir: Path, *, include_archived: bool) -> list[Candidate]:
    trials_root = run_dir / "trials"
    if not trials_root.is_dir():
        raise SystemExit(f"not a run directory (no trials/): {run_dir}")
    out: list[Candidate] = []
    for trial_dir in sorted(trials_root.iterdir(), key=lambda p: p.name):
        if not trial_dir.is_dir():
            continue
        archived = ".before_resume_" in trial_dir.name
        if archived and not include_archived:
            continue
        meta = _read_json_or_none(trial_dir / "meta.json") or {}
        task_output = _read_json_or_none(trial_dir / "task_output.json") or {}
        sample = task_output.get("sample") if isinstance(task_output, dict) else {}
        sample = sample if isinstance(sample, dict) else {}
        task_id = _normalize_task_id(
            meta.get("task_id")
            or sample.get("task_id")
            or trial_dir.name.split(".before_resume_")[0]
        )
        if not task_id:
            continue

        # runtime/ is the scorer-curated copy (quality-filtered); workspace/ is
        # the agent's raw write. Prefer the curated one, fall back to the raw.
        runtime_desc = trial_dir / "runtime" / "descriptions.json"
        workspace_desc = trial_dir / "workspace" / "descriptions.json"
        descriptions = _descriptions(runtime_desc) or _descriptions(workspace_desc)

        crash = trial_dir / "workspace" / "observed-crash.txt"
        crash_log = crash if crash.is_file() and crash.stat().st_size > 0 else None

        mtime_source = runtime_desc if runtime_desc.is_file() else trial_dir / "meta.json"
        try:
            mtime_ms = int(mtime_source.stat().st_mtime * 1000)
        except OSError:
            mtime_ms = 0

        out.append(Candidate(
            task_id=task_id,
            trial_dir=trial_dir,
            descriptions=descriptions,
            crash_log=crash_log,
            completed=str(meta.get("status") or "") == "completed",
            mtime_ms=mtime_ms,
        ))
    return out


def best_by_task(candidates: list[Candidate]) -> dict[str, Candidate]:
    best: dict[str, Candidate] = {}
    for cand in candidates:
        prev = best.get(cand.task_id)
        if prev is None or cand.rank > prev.rank:
            best[cand.task_id] = cand
    return best


def _merge_crash_log(best: dict[str, Candidate], all_candidates: list[Candidate]) -> int:
    """Backfill a crash log from a sibling trial of the same task.

    The winning trial is picked on description quality; an earlier attempt of the
    same task may still hold the only captured sanitizer trace. The crash log is
    a property of the (PoC, vulnerable binary) pair, not of the agent's run, so
    borrowing it across attempts of the same task is sound.
    """
    borrowed = 0
    for cand in all_candidates:
        winner = best.get(cand.task_id)
        if winner is None or winner.crash_log is not None or cand.crash_log is None:
            continue
        winner.crash_log = cand.crash_log
        borrowed += 1
    return borrowed


def write_overlay(
    best: dict[str, Candidate],
    out_dir: Path,
    *,
    run_dirs: list[Path],
    include_archived: bool,
) -> dict[str, Any]:
    arvo_root = out_dir / "arvo"
    arvo_root.mkdir(parents=True, exist_ok=True)

    tier_counts: Counter[int] = Counter()
    written_desc = written_crash = 0
    tasks: dict[str, dict[str, Any]] = {}

    for task_id in sorted(best, key=lambda tid: (tid.split(":", 1)[0], int(tid.split(":", 1)[1]))):
        cand = best[task_id]
        subset, _, num = task_id.partition(":")
        if subset != "arvo":
            continue
        task_dir = out_dir / subset / num
        task_dir.mkdir(parents=True, exist_ok=True)

        tiers: list[str] = []
        for index, text in enumerate(cand.descriptions[:MAX_TIERS]):
            level = f"level{index}"
            (task_dir / f"description.{level}.txt").write_text(
                text.rstrip() + "\n", encoding="utf-8"
            )
            tiers.append(level)
        tier_counts[len(tiers)] += 1
        written_desc += 1 if tiers else 0

        has_crash = False
        if cand.crash_log is not None:
            shutil.copyfile(cand.crash_log, task_dir / "error.txt")
            has_crash = True
            written_crash += 1

        tasks[task_id] = {
            "description_tiers": tiers,
            "error": has_crash,
            "trial_dir": str(cand.trial_dir.resolve()),
        }
        if not tiers and not has_crash:
            # Nothing harvestable — do not leave an empty dir that reads as
            # "materials exist" to the benchmark's availability check.
            task_dir.rmdir()
            tasks.pop(task_id)

    manifest = {
        "kind": "cybergym-materials-overlay",
        "version": 1,
        "sources": {
            "run_dirs": [str(p.resolve()) for p in run_dirs],
            "include_archived": include_archived,
        },
        "counts": {
            "tasks": len(tasks),
            "with_descriptions": written_desc,
            "with_error": written_crash,
            "by_tier_count": {str(k): v for k, v in sorted(tier_counts.items())},
            "level1_ready": sum(1 for t in tasks.values() if t["description_tiers"]),
            "level2_ready": sum(
                1 for t in tasks.values() if t["description_tiers"] and t["error"]
            ),
            "full_ladder_ready": sum(
                1 for t in tasks.values()
                if len(t["description_tiers"]) == MAX_TIERS and t["error"]
            ),
        },
        "tasks": tasks,
    }
    (out_dir / "manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument(
        "--run-dir", action="append", required=True, type=Path,
        help="gendesc run directory (repeatable; later runs win ties)",
    )
    parser.add_argument(
        "--out", required=True, type=Path,
        help="overlay output directory (created; existing files are overwritten)",
    )
    parser.add_argument(
        "--include-archived", action="store_true",
        help="also scan .before_resume_* trial snapshots (more coverage, older material)",
    )
    parser.add_argument(
        "--task-ids", type=Path, default=None,
        help="optional task-id file (one 'arvo:1065' or 'arvo_1065' per line) to restrict the overlay",
    )
    args = parser.parse_args()

    wanted: set[str] | None = None
    if args.task_ids is not None:
        wanted = {
            _normalize_task_id(line)
            for line in args.task_ids.read_text(encoding="utf-8").splitlines()
            if line.strip() and not line.lstrip().startswith("#")
        }

    candidates: list[Candidate] = []
    for run_dir in args.run_dir:
        candidates.extend(scan_run(run_dir, include_archived=args.include_archived))
    if wanted is not None:
        candidates = [c for c in candidates if c.task_id in wanted]
    if not candidates:
        raise SystemExit("no trials matched; nothing to harvest")

    best = best_by_task(candidates)
    borrowed = _merge_crash_log(best, candidates)
    manifest = write_overlay(
        best, args.out, run_dirs=args.run_dir, include_archived=args.include_archived
    )

    counts = manifest["counts"]
    print(f"overlay written to {args.out}")
    print(f"  tasks                 {counts['tasks']}")
    print(f"  with descriptions     {counts['with_descriptions']}")
    print(f"  with real error.txt   {counts['with_error']} (borrowed across attempts: {borrowed})")
    print(f"  level1-ready          {counts['level1_ready']}")
    print(f"  level2-ready          {counts['level2_ready']}")
    print(f"  full 4-tier ladder    {counts['full_ladder_ready']}")
    print(f"  tier-count histogram  {counts['by_tier_count']}")


if __name__ == "__main__":
    main()
