#!/usr/bin/env python3
"""Materialize an audited R4 calibration subset from a generated build queue."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def read_ids(path: Path) -> list[str]:
    ids = [line.strip() for line in path.read_text(encoding="utf-8").splitlines()]
    ids = [item for item in ids if item and not item.startswith("#")]
    if len(ids) != len(set(ids)):
        raise ValueError("calibration id list contains duplicates")
    return ids


def previously_manifested_ids(run_root: Path | None) -> set[str]:
    if run_root is None or not run_root.exists():
        return set()
    ids: set[str] = set()
    for manifest in run_root.glob("**/*image_manifest.json"):
        parts = manifest.parts
        if "trials" in parts:
            index = parts.index("trials")
            if index + 1 < len(parts):
                ids.add(parts[index + 1])
    return ids


def promote_image_tag(image: str) -> str:
    promoted, count = re.subn(r"-r3-", "-r4-", image, count=1)
    if count != 1:
        raise ValueError(f"image tag does not contain an R3 maturity component: {image}")
    return promoted


def validate_record(record: dict[str, Any], *, manifested: set[str]) -> None:
    env_id = record["env_id"]
    task = record["task"]
    states = task.get("material_states") or {}
    closure = task.get("docker_closure") or {}
    if env_id in manifested:
        raise ValueError(f"{env_id} already has an image_manifest.json")
    if task.get("data_tier") not in {"D4", "D5"}:
        raise ValueError(f"{env_id} is not confirmed D4/D5")
    for role in ("deploy", "writeup"):
        if (states.get(role) or {}).get("state") != "confirmed":
            raise ValueError(f"{env_id} lacks confirmed {role} evidence")
    if int(closure.get("missing_ref_count") or 0) != 0:
        raise ValueError(f"{env_id} has missing Docker closure references")
    if (task.get("static_evidence") or {}).get("prior_runtime_failures"):
        raise ValueError(f"{env_id} has a known prior runtime blocker")
    if task.get("category") == "pwn":
        if (record.get("priority") or {}).get("id") != "dockerfile_writeup_attachments":
            raise ValueError(f"{env_id} is not in the strongest Pwn material class")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--queue", type=Path, required=True)
    parser.add_argument("--ids", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--run-root", type=Path)
    args = parser.parse_args()

    ids = read_ids(args.ids)
    if not ids:
        raise ValueError("calibration id list is empty")
    records = {record["env_id"]: record for record in read_jsonl(args.queue)}
    missing = [env_id for env_id in ids if env_id not in records]
    if missing:
        raise ValueError("ids missing from queue: " + ", ".join(missing))
    if args.output_dir.exists() and any(args.output_dir.iterdir()):
        raise FileExistsError(f"output directory is not empty: {args.output_dir}")

    manifested = previously_manifested_ids(args.run_root)
    selected: list[dict[str, Any]] = []
    args.output_dir.mkdir(parents=True, exist_ok=True)
    for position, env_id in enumerate(ids, 1):
        record = records[env_id]
        validate_record(record, manifested=manifested)
        task = json.loads(json.dumps(record["task"]))
        task["target_maturity"] = {
            "data": task["data_tier"],
            "rehost": "R4",
            "exploit": "X0",
        }
        task["image_name"] = promote_image_tag(task["image_name"])
        task_dir = args.output_dir / env_id
        task_dir.mkdir()
        (task_dir / "task.json").write_text(
            json.dumps(task, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        selected.append(
            {
                "position": position,
                "env_id": env_id,
                "category": task["category"],
                "data_tier": task["data_tier"],
                "target_rehost_tier": "R4",
                "image_name": task["image_name"],
                "material_priority": record["priority"]["id"],
                "docker_closure": task["docker_closure"],
            }
        )

    (args.output_dir / "SELECTION.json").write_text(
        json.dumps(
            {
                "schema_version": "cage-build-target-r4-calibration-v1",
                "source_queue": str(args.queue.resolve()),
                "count": len(selected),
                "tasks": selected,
            },
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    header = "position\tenv_id\tcategory\tdata_tier\ttarget\timage_name\n"
    rows = [
        "\t".join(
            (
                str(item["position"]),
                item["env_id"],
                item["category"],
                item["data_tier"],
                item["target_rehost_tier"],
                item["image_name"],
            )
        )
        + "\n"
        for item in selected
    ]
    (args.output_dir / "TASKS.tsv").write_text(header + "".join(rows), encoding="utf-8")
    print(f"materialized {len(selected)} R4 calibration tasks at {args.output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
