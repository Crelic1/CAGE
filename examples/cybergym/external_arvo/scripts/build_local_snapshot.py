#!/usr/bin/env python3
"""Build a compact local snapshot of ready external-ARVO envs + gendesc results.

Why this exists:
  * the *facts* about an environment live across multiple local files
    (`datasets/arvo*.json`, `external_arvo/environments.jsonl`,
    `datasets/arvo_binary_ready.txt`);
  * the *derived* gendesc outputs live inside large, run-scoped `.cage_runs/`
    trees that are good as evidence, but awkward as a working dataset.

This script keeps the raw evidence where it is and emits a small, normalized
snapshot directory for downstream inspection / upload / further collection.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CYBERGYM = ROOT.parent


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _read_json_or_none(path: Path) -> Any:
    try:
        return _read_json(path)
    except (OSError, json.JSONDecodeError):
        return None


def _read_text_or_none(path: Path) -> str | None:
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return None


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            rows.append(json.loads(line))
    return rows


def _write_json(path: Path, data: Any) -> None:
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def _normalize_task_id(raw: str | None) -> str | None:
    if not raw:
        return None
    text = str(raw).strip()
    if not text:
        return None
    if text.startswith("arvo:"):
        return text
    if text.startswith("arvo_"):
        return "arvo:" + text.split("_", 1)[1]
    if text.isdigit():
        return f"arvo:{text}"
    return text


def _id_num_from_task_id(task_id: str | None) -> str | None:
    norm = _normalize_task_id(task_id)
    if not norm or ":" not in norm:
        return None
    return norm.split(":", 1)[1]


def _load_ready_ids(path: Path) -> list[str]:
    out: list[str] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        task_id = _normalize_task_id(line)
        if task_id:
            out.append(task_id)
    return out


def _merge_catalog_entry(task_id: str, primary: dict[str, dict[str, Any]],
                         fallback: dict[str, dict[str, Any]]) -> dict[str, Any]:
    p = dict(primary.get(task_id) or {})
    f = dict(fallback.get(task_id) or {})
    if not p:
        return f
    for key, value in f.items():
        if p.get(key) in (None, ""):
            p[key] = value
    return p


def _load_environment_index(path: Path) -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    for row in _read_jsonl(path):
        task_id = _normalize_task_id(row.get("task_id"))
        if task_id:
            out[task_id] = row
    return out


def _candidate_level_map(values: list[str]) -> dict[str, str]:
    levels = {}
    for idx, value in enumerate(values):
        levels[f"level{idx}"] = value
    return levels


@dataclass
class RunInfo:
    run_id: str
    run_dir: Path
    agent_label: str
    run_status: str | None
    subject_status: str | None
    benchmark_id: str | None
    project_name: str | None
    order_index: int


def _load_run_info(run_dir: Path, order_index: int) -> RunInfo:
    record = _read_json_or_none(run_dir / "experiment_record.json") or {}
    spec = _read_json_or_none(run_dir / "experiment_spec.json") or {}
    subjects = record.get("subjects") if isinstance(record, dict) else None
    subject_status = None
    if isinstance(subjects, list) and subjects:
        first = subjects[0]
        if isinstance(first, dict):
            subject_status = first.get("status")
    benchmark = spec.get("benchmark") if isinstance(spec, dict) else {}
    if not isinstance(benchmark, dict):
        benchmark = {}
    return RunInfo(
        run_id=str(record.get("run_id") or run_dir.name),
        run_dir=run_dir.resolve(),
        agent_label=run_dir.parent.name,
        run_status=record.get("status") if isinstance(record, dict) else None,
        subject_status=subject_status,
        benchmark_id=benchmark.get("id"),
        project_name=benchmark.get("project_name"),
        order_index=order_index,
    )


def _description_payload(path: Path) -> tuple[list[str], dict[str, str]]:
    data = _read_json_or_none(path)
    if isinstance(data, list):
        values = [str(item).strip() for item in data if str(item).strip()]
        return values, _candidate_level_map(values)
    return [], {}


def _trial_sort_key(row: dict[str, Any]) -> tuple[int, int, int, int, int]:
    result = row.get("result") if isinstance(row, dict) else {}
    run = row.get("run") if isinstance(row, dict) else {}
    artifacts = row.get("artifacts") if isinstance(row, dict) else {}
    if not isinstance(result, dict):
        result = {}
    if not isinstance(run, dict):
        run = {}
    if not isinstance(artifacts, dict):
        artifacts = {}
    status = str(result.get("status") or "")
    has_desc = 1 if result.get("num_candidates", 0) > 0 else 0
    is_completed = 1 if status == "completed" else 0
    has_understanding = 1 if artifacts.get("runtime_understanding_md") else 0
    order_index = int(run.get("order_index") or 0)
    mtime_ms = int(result.get("mtime_ms") or 0)
    return (has_desc, is_completed, has_understanding, order_index, mtime_ms)


def build_ready_rows(
    ready_ids: list[str],
    arvo_catalog: dict[str, dict[str, Any]],
    restored_catalog: dict[str, dict[str, Any]],
    env_index: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for task_id in ready_ids:
        merged_catalog = _merge_catalog_entry(task_id, restored_catalog, arvo_catalog)
        env = env_index.get(task_id)
        rows.append({
            "task_id": task_id,
            "id_num": _id_num_from_task_id(task_id),
            "catalog": merged_catalog or None,
            "environment": env,
            "ready_binary": True,
        })
    return rows


def build_gendesc_rows(run_dirs: list[Path]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    trial_rows: list[dict[str, Any]] = []
    run_summaries: list[dict[str, Any]] = []
    for order_index, run_dir in enumerate(run_dirs):
        info = _load_run_info(run_dir, order_index)
        trials_root = run_dir / "trials"
        if not trials_root.is_dir():
            run_summaries.append({
                "run_id": info.run_id,
                "run_dir": str(info.run_dir),
                "agent_label": info.agent_label,
                "run_status": info.run_status,
                "subject_status": info.subject_status,
                "benchmark_id": info.benchmark_id,
                "project_name": info.project_name,
                "trial_dirs_scanned": 0,
                "rows_emitted": 0,
            })
            continue
        emitted = 0
        scanned = 0
        for trial_dir in sorted(trials_root.iterdir(), key=lambda p: p.name):
            if not trial_dir.is_dir():
                continue
            if ".before_resume_" in trial_dir.name:
                continue
            scanned += 1
            meta_path = trial_dir / "meta.json"
            task_output_path = trial_dir / "task_output.json"
            runtime_desc_path = trial_dir / "runtime" / "descriptions.json"
            runtime_understanding_path = trial_dir / "runtime" / "understanding.md"
            workspace_desc_path = trial_dir / "workspace" / "descriptions.json"
            workspace_understanding_path = trial_dir / "workspace" / "understanding.md"

            meta = _read_json_or_none(meta_path) or {}
            task_output = _read_json_or_none(task_output_path) or {}
            sample = task_output.get("sample") if isinstance(task_output, dict) else {}
            if not isinstance(sample, dict):
                sample = {}

            trial_id = str(meta.get("trial_id") or trial_dir.name)
            sample_id = str(meta.get("sample_id") or sample.get("id") or trial_dir.name)
            task_id = _normalize_task_id(
                meta.get("task_id") or sample.get("task_id") or trial_id or sample_id
            )
            if not task_id:
                continue

            descriptions, description_levels = _description_payload(runtime_desc_path)
            understanding_text = _read_text_or_none(runtime_understanding_path)
            mtime_source = runtime_desc_path if runtime_desc_path.is_file() else meta_path
            try:
                mtime_ms = int(mtime_source.stat().st_mtime * 1000)
            except OSError:
                mtime_ms = 0

            row = {
                "task_id": task_id,
                "id_num": _id_num_from_task_id(task_id),
                "trial_id": trial_id,
                "sample_id": sample_id,
                "run": {
                    "run_id": info.run_id,
                    "run_dir": str(info.run_dir),
                    "agent_label": info.agent_label,
                    "run_status": info.run_status,
                    "subject_status": info.subject_status,
                    "benchmark_id": info.benchmark_id,
                    "project_name": info.project_name,
                    "order_index": info.order_index,
                },
                "trial": {
                    "status": meta.get("status"),
                    "termination_reason": meta.get("termination_reason"),
                    "exit_code": meta.get("exit_code"),
                    "duration_ms": ((meta.get("timing") or {}).get("duration_ms")
                                    if isinstance(meta.get("timing"), dict) else None),
                },
                "artifacts": {
                    "meta_json": str(meta_path.resolve()) if meta_path.is_file() else None,
                    "task_output_json": str(task_output_path.resolve()) if task_output_path.is_file() else None,
                    "runtime_descriptions_json": str(runtime_desc_path.resolve()) if runtime_desc_path.is_file() else None,
                    "runtime_understanding_md": str(runtime_understanding_path.resolve()) if runtime_understanding_path.is_file() else None,
                    "workspace_descriptions_json": str(workspace_desc_path.resolve()) if workspace_desc_path.is_file() else None,
                    "workspace_understanding_md": str(workspace_understanding_path.resolve()) if workspace_understanding_path.is_file() else None,
                    "trial_dir": str(trial_dir.resolve()),
                },
                "result": {
                    "num_candidates": len(descriptions),
                    "descriptions": descriptions,
                    "description_by_level": description_levels,
                    "selected_description": descriptions[-1] if descriptions else None,
                    "task_output_message": task_output.get("output") if isinstance(task_output, dict) else None,
                    "has_understanding": understanding_text is not None,
                    "mtime_ms": mtime_ms,
                },
            }
            trial_rows.append(row)
            emitted += 1
        run_summaries.append({
            "run_id": info.run_id,
            "run_dir": str(info.run_dir),
            "agent_label": info.agent_label,
            "run_status": info.run_status,
            "subject_status": info.subject_status,
            "benchmark_id": info.benchmark_id,
            "project_name": info.project_name,
            "trial_dirs_scanned": scanned,
            "rows_emitted": emitted,
        })
    return trial_rows, run_summaries


def build_latest_by_task(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    best: dict[str, dict[str, Any]] = {}
    for row in rows:
        task_id = row["task_id"]
        prev = best.get(task_id)
        if prev is None or _trial_sort_key(row) > _trial_sort_key(prev):
            best[task_id] = row
    return [best[task_id] for task_id in sorted(best, key=lambda tid: int(tid.split(":", 1)[1]))]


def build_merged_ready_rows(
    ready_rows: list[dict[str, Any]],
    latest_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    latest_by_task = {row["task_id"]: row for row in latest_rows}
    out: list[dict[str, Any]] = []
    for row in ready_rows:
        merged = dict(row)
        merged["gendesc"] = latest_by_task.get(row["task_id"])
        out.append(merged)
    return out


def build_summary_markdown(
    ready_rows: list[dict[str, Any]],
    trial_rows: list[dict[str, Any]],
    latest_rows: list[dict[str, Any]],
    run_summaries: list[dict[str, Any]],
    out_dir: Path,
) -> str:
    latest_with_desc = sum(1 for row in latest_rows if (row["result"]["num_candidates"] > 0))
    latest_with_understanding = sum(
        1 for row in latest_rows if row["result"]["has_understanding"]
    )
    candidate_counts = Counter(row["result"]["num_candidates"] for row in latest_rows)
    vuln_counts = Counter(
        (row.get("environment") or {}).get("vuln_class") or "unknown"
        for row in ready_rows
    )
    lines = [
        "# Local Snapshot Summary",
        "",
        f"- output_dir: `{out_dir}`",
        f"- ready_env_rows: `{len(ready_rows)}`",
        f"- gendesc_trial_rows: `{len(trial_rows)}`",
        f"- latest_gendesc_rows: `{len(latest_rows)}`",
        f"- latest_with_descriptions: `{latest_with_desc}`",
        f"- latest_with_understanding: `{latest_with_understanding}`",
        "",
        "## Files",
        "",
        "- `manifest.json`: snapshot-level counts + source paths",
        "- `ready_envs_merged.jsonl`: ready environment row + latest gendesc row",
        "- `gendesc_attempts.jsonl`: optional; written only with `--keep-attempts`",
        "",
        "## Per-item fields",
        "",
        "Each line of `ready_envs_merged.jsonl` represents one `arvo:<id>` and has:",
        "",
        "| field | contents |",
        "|---|---|",
        "| `task_id`, `id_num`, `ready_binary` | stable identity and binary-ready flag |",
        "| `catalog` | ARVO catalog metadata: project, language, crash sanitizer, source, fix commit |",
        "| `environment` | executable facts: harness, vulnerability/input classes, grading, vulnerable/fixed binary paths, PoC path/size/SHA-256 |",
        "| `gendesc.trial` | latest trial status, termination reason, exit code, and duration |",
        "| `gendesc.result` | candidate count, `descriptions`, `description_by_level`, selected description, model output note, and understanding availability |",
        "| `gendesc.artifacts` | source trial directory plus paths to generated descriptions and understanding evidence |",
        "",
        "The optional `showcase-200/showcase.jsonl` is the human-review view. Its `artifacts` field additionally indexes vulnerable source tarballs, observed crash text, vulnerable/fixed binary paths, and the reference PoC.",
        "",
        "## Description coverage",
        "",
        "Each generated description has four progressively more specific views:",
        "`level0` (minimal flaw), `level1` (function/root cause), `level2` (trigger path),",
        "and `level3` (precise faulty logic and missing protection).",
        "",
        "| available descriptions | environments |",
        "|---:|---:|",
    ]
    for count in sorted(candidate_counts, reverse=True):
        lines.append(f"| {count} | {candidate_counts[count]} |")
    lines += [
        "",
        "## Vulnerability types",
        "",
        "| class | environments |",
        "|---|---:|",
    ]
    for name, count in vuln_counts.most_common():
        lines.append(f"| {name} | {count} |")
    lines += [
        "",
        "## Runs",
        "",
        "| run_id | agent_label | run_status | subject_status | rows_emitted |",
        "|---|---|---|---|---:|",
    ]
    for row in run_summaries:
        lines.append(
            f"| {row['run_id']} | {row['agent_label']} | "
            f"{row.get('run_status') or ''} | {row.get('subject_status') or ''} | "
            f"{row['rows_emitted']} |"
        )
    lines.append("")
    return "\n".join(lines) + "\n"


def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--arvo-catalog",
        type=Path,
        default=CYBERGYM / "datasets" / "arvo.json",
    )
    ap.add_argument(
        "--arvo-restored",
        type=Path,
        default=CYBERGYM / "datasets" / "arvo_local_restored.json",
    )
    ap.add_argument(
        "--ready-ids",
        type=Path,
        default=CYBERGYM / "datasets" / "arvo_binary_ready.txt",
    )
    ap.add_argument(
        "--environments-jsonl",
        type=Path,
        default=ROOT / "catalog" / "environments.jsonl",
    )
    ap.add_argument(
        "--run-dir",
        type=Path,
        action="append",
        default=[],
        help="repeatable; extract gendesc rows from each run dir",
    )
    ap.add_argument("--out-dir", type=Path, required=True)
    ap.add_argument(
        "--keep-attempts",
        action="store_true",
        help="also write every run attempt; omit for the compact default snapshot",
    )
    return ap.parse_args()


def main() -> None:
    args = parse_args()
    out_dir = args.out_dir.expanduser().resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    arvo_catalog = _read_json(args.arvo_catalog.expanduser().resolve())
    restored_catalog = _read_json(args.arvo_restored.expanduser().resolve())
    ready_ids = _load_ready_ids(args.ready_ids.expanduser().resolve())
    env_index = _load_environment_index(args.environments_jsonl.expanduser().resolve())
    run_dirs = [p.expanduser().resolve() for p in args.run_dir]

    ready_rows = build_ready_rows(ready_ids, arvo_catalog, restored_catalog, env_index)
    trial_rows, run_summaries = build_gendesc_rows(run_dirs)
    latest_rows = build_latest_by_task(trial_rows)
    merged_rows = build_merged_ready_rows(ready_rows, latest_rows)

    _write_jsonl(out_dir / "ready_envs_merged.jsonl", merged_rows)
    if args.keep_attempts:
        _write_jsonl(out_dir / "gendesc_attempts.jsonl", trial_rows)

    manifest = {
        "sources": {
            "arvo_catalog": str(args.arvo_catalog.expanduser().resolve()),
            "arvo_restored": str(args.arvo_restored.expanduser().resolve()),
            "ready_ids": str(args.ready_ids.expanduser().resolve()),
            "environments_jsonl": str(args.environments_jsonl.expanduser().resolve()),
            "run_dirs": [str(path) for path in run_dirs],
        },
        "counts": {
            "ready_env_rows": len(ready_rows),
            "gendesc_trial_rows": len(trial_rows),
            "latest_gendesc_rows": len(latest_rows),
            "latest_with_descriptions": sum(1 for row in latest_rows if row["result"]["num_candidates"] > 0),
            "latest_with_understanding": sum(1 for row in latest_rows if row["result"]["has_understanding"]),
        },
        "files": ["ready_envs_merged.jsonl"] + (
            ["gendesc_attempts.jsonl"] if args.keep_attempts else []
        ),
        "run_summaries": run_summaries,
    }
    _write_json(out_dir / "manifest.json", manifest)
    (out_dir / "SUMMARY.md").write_text(
        build_summary_markdown(ready_rows, trial_rows, latest_rows, run_summaries, out_dir),
        encoding="utf-8",
    )

    print(f"wrote snapshot to {out_dir}")
    print(f"  ready_env_rows           {len(ready_rows)}")
    print(f"  gendesc_trial_rows       {len(trial_rows)}")
    print(f"  latest_gendesc_rows      {len(latest_rows)}")
    print(
        "  latest_with_descriptions "
        f"{sum(1 for row in latest_rows if row['result']['num_candidates'] > 0)}"
    )
    print(
        "  latest_with_understanding "
        f"{sum(1 for row in latest_rows if row['result']['has_understanding'])}"
    )


if __name__ == "__main__":
    main()
