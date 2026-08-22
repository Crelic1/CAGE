#!/usr/bin/env python3
"""Export portable ARVO gendesc records from a materialized local snapshot.

The snapshot contains host-local paths into `.cage_runs` and `cybergym-bin`.
This tool copies the review evidence and rewrites those paths to bundle-relative
ones, so the output can be sent to a collaborator without this checkout.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import shutil
from pathlib import Path
from typing import Any


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def _write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def _safe_id(task_id: str) -> str:
    return task_id.replace(":", "_").replace("/", "_")


def _copy_file(source: str | None, dest: Path) -> str | None:
    if not source:
        return None
    src = Path(source)
    if not src.is_file():
        return None
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dest)
    return str(dest)


def _copy_evidence(row: dict[str, Any], out_dir: Path) -> dict[str, str]:
    task_dir = out_dir / "evidence" / _safe_id(row["task_id"])
    source = row.get("gendesc", {}).get("artifacts", {})
    copies: dict[str, str] = {}
    candidates = {
        "descriptions.json": source.get("runtime_descriptions_json") or source.get("workspace_descriptions_json"),
        "understanding.md": source.get("runtime_understanding_md") or source.get("workspace_understanding_md"),
    }
    for filename, src in candidates.items():
        target = task_dir / filename
        if _copy_file(src, target):
            copies[filename] = str(target.relative_to(out_dir))
    return copies


def _copy_environment(row: dict[str, Any], out_dir: Path) -> dict[str, str]:
    artifacts = row.get("environment", {}).get("artifacts", {})
    vul_binary = artifacts.get("vul_binary")
    if not vul_binary:
        return {}
    env_dir = Path(vul_binary).parent.parent
    if not env_dir.is_dir():
        return {}
    target = out_dir / "environments" / _safe_id(row["task_id"])
    shutil.copytree(env_dir, target, dirs_exist_ok=True)
    return {
        "environment_dir": str(target.relative_to(out_dir)),
        "vul_binary": str((target / "vul" / "arvo").relative_to(out_dir)),
        "fix_binary": str((target / "fix" / "arvo").relative_to(out_dir)),
        "reference_poc": str((target / "poc").relative_to(out_dir)),
    }


def _portable_row(row: dict[str, Any], evidence: dict[str, str], environment: dict[str, str]) -> dict[str, Any]:
    portable = copy.deepcopy(row)
    portable["bundle_artifacts"] = {"evidence": evidence}
    if environment:
        portable["bundle_artifacts"]["environment"] = environment
    # Do not leak paths meaningful only inside this host's run workspace.
    portable.get("gendesc", {}).pop("artifacts", None)
    portable.get("environment", {}).pop("artifacts", None)
    portable.get("gendesc", {}).get("run", {}).pop("run_dir", None)
    return portable


def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--snapshot-dir", type=Path, required=True)
    ap.add_argument("--out-dir", type=Path, required=True)
    ap.add_argument("--task-id", action="append", default=[], help="repeatable; defaults to every snapshot row")
    ap.add_argument("--include-binaries", action="store_true")
    ap.add_argument("--completed-only", action="store_true")
    return ap.parse_args()


def main() -> None:
    args = parse_args()
    snapshot = args.snapshot_dir.expanduser().resolve()
    source = snapshot / "ready_envs_merged.jsonl"
    if not source.is_file():
        raise SystemExit(f"missing merged snapshot: {source}")
    out_dir = args.out_dir.expanduser().resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    selected = set(args.task_id)
    rows = _read_jsonl(source)
    if selected:
        rows = [row for row in rows if row["task_id"] in selected]
        missing = selected - {row["task_id"] for row in rows}
        if missing:
            raise SystemExit(f"task ids not present in snapshot: {', '.join(sorted(missing))}")
    if args.completed_only:
        rows = [row for row in rows if row.get("gendesc", {}).get("trial", {}).get("status") == "completed"]

    exported: list[dict[str, Any]] = []
    for row in rows:
        evidence = _copy_evidence(row, out_dir)
        environment = _copy_environment(row, out_dir) if args.include_binaries else {}
        exported.append(_portable_row(row, evidence, environment))
    _write_jsonl(out_dir / "dataset.jsonl", exported)
    digest = hashlib.sha256((out_dir / "dataset.jsonl").read_bytes()).hexdigest()
    _write_json(out_dir / "manifest.json", {
        "source_snapshot": snapshot.name,
        "selected_task_ids": [row["task_id"] for row in exported],
        "counts": {
            "rows": len(exported),
            "with_descriptions": sum(bool(row["bundle_artifacts"]["evidence"].get("descriptions.json")) for row in exported),
            "with_understanding": sum(bool(row["bundle_artifacts"]["evidence"].get("understanding.md")) for row in exported),
            "with_binaries": sum(bool(row["bundle_artifacts"].get("environment")) for row in exported),
        },
        "dataset_sha256": digest,
    })
    print(f"exported {len(exported)} task(s) to {out_dir}")


if __name__ == "__main__":
    main()
