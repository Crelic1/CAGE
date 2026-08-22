#!/usr/bin/env python3
"""Create a compact, diverse, human-readable description showcase from a snapshot."""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


def _read_rows(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def _pick(rows: list[dict[str, Any]], count: int, project_cap: int) -> list[dict[str, Any]]:
    eligible = [
        row for row in rows
        if row.get("gendesc", {}).get("trial", {}).get("status") == "completed"
        and row["gendesc"]["result"].get("num_candidates", 0) == 4
    ]
    buckets: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in eligible:
        buckets[row["environment"].get("input_class") or "unknown"].append(row)
    for bucket in buckets.values():
        bucket.sort(key=lambda row: (row["environment"].get("project") or "", int(row["id_num"])))

    chosen: list[dict[str, Any]] = []
    per_project: Counter[str] = Counter()
    names = sorted(buckets, key=lambda name: (len(buckets[name]), name))
    while len(chosen) < count:
        progressed = False
        for name in names:
            if len(chosen) >= count:
                break
            bucket = buckets[name]
            for index, row in enumerate(bucket):
                project = (row["environment"].get("project") or "unknown").lower()
                if per_project[project] >= project_cap:
                    continue
                chosen.append(row)
                per_project[project] += 1
                bucket.pop(index)
                progressed = True
                break
        if not progressed:
            break
    return chosen


def _portable(row: dict[str, Any]) -> dict[str, Any]:
    result = row["gendesc"]["result"]
    env = row["environment"]
    trial_artifacts = row["gendesc"].get("artifacts", {})
    trial_dir = Path(trial_artifacts.get("trial_dir") or "")

    def existing(relative: str) -> str | None:
        candidate = trial_dir / relative
        return str(candidate) if trial_dir and candidate.is_file() else None

    return {
        "task_id": row["task_id"],
        "project": env.get("project"),
        "harness": env.get("harness"),
        "vuln_class": env.get("vuln_class"),
        "input_class": env.get("input_class"),
        "description_by_level": result["description_by_level"],
        "selected_description": result["selected_description"],
        "artifacts": {
            "environment": env.get("artifacts", {}),
            "trial_dir": str(trial_dir) if trial_dir else None,
            "source": {
                "repo_vul_tar_gz": existing("workspace/repo-vul.tar.gz"),
                "repo_fix_tar_gz": existing("workspace/repo-fix.tar.gz"),
                "patch_diff": existing("workspace/patch.diff"),
            },
            "crash": {
                "crash_txt": existing("runtime/observed-crash.txt"),
                "reference_error_txt": existing("workspace/error.txt"),
            },
            "gendesc": {
                "descriptions_json": trial_artifacts.get("runtime_descriptions_json"),
                "understanding_md": trial_artifacts.get("runtime_understanding_md"),
            },
        },
    }


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--snapshot-dir", type=Path, required=True)
    ap.add_argument("--out-dir", type=Path, required=True)
    ap.add_argument("--count", type=int, default=200)
    ap.add_argument("--project-cap", type=int, default=2)
    args = ap.parse_args()
    rows = _read_rows(args.snapshot_dir / "ready_envs_merged.jsonl")
    selected = _pick(rows, args.count, args.project_cap)
    out_dir = args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    portable = [_portable(row) for row in selected]
    with (out_dir / "showcase.jsonl").open("w", encoding="utf-8") as fh:
        for row in portable:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")
    lines = ["# ARVO gendesc showcase", "", f"- samples: `{len(portable)}`", f"- max per project: `{args.project_cap}`", ""]
    for row in portable:
        lines += [
            f"## {row['task_id']} — {row['project']} / {row['harness']}",
            "",
            f"- class: `{row['vuln_class']}` / `{row['input_class']}`",
            f"- selected description: {row['selected_description']}",
            f"- vulnerable source: `{row['artifacts']['source']['repo_vul_tar_gz']}`",
            f"- crash report: `{row['artifacts']['crash']['crash_txt']}`",
            f"- vulnerable binary: `{row['artifacts']['environment'].get('vul_binary')}`",
            "",
        ]
    (out_dir / "SHOWCASE.md").write_text("\n".join(lines), encoding="utf-8")
    (out_dir / "manifest.json").write_text(json.dumps({
        "source_snapshot": args.snapshot_dir.name,
        "count": len(portable),
        "input_class_counts": Counter(row["input_class"] for row in portable),
        "project_cap": args.project_cap,
    }, ensure_ascii=False, indent=2, default=dict) + "\n", encoding="utf-8")
    print(f"wrote {len(portable)} showcase rows to {out_dir}")


if __name__ == "__main__":
    main()
