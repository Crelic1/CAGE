#!/usr/bin/env python3
"""Batch-run gendesc preflight without any agent/model calls.

This script reuses ``examples/cybergym/benchmark.py::_run_gendesc_preflight``
directly, so it exercises the same vulnerable-binary reproduction path as the
gendesc pipeline, but stops before any prompt staging or model invocation.

Primary use case:
  * scan a large ARVO binary corpus quickly;
  * identify projects/cases whose extracted binary bundle is not sufficient to
    reach the real crash site (for example, startup/runtime-tree failures).
"""

from __future__ import annotations

import argparse
import concurrent.futures as cf
import importlib.util
import json
import os
import re
import sys
import threading
import time
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


_RUNTIME_TREE_PATTERNS = [
    re.compile(r"DeploymentException", re.I),
    re.compile(r"defaultBootstrap_InitialComponentContext", re.I),
    re.compile(r"cppuhelper::ServiceManager::readRdbDirectory", re.I),
    re.compile(r"framework::Desktop", re.I),
    re.compile(r"Desktop::create", re.I),
]

_SHARED_LIBRARY_PATTERNS = [
    re.compile(r"error while loading shared libraries", re.I),
    re.compile(r"cannot open shared object file", re.I),
    re.compile(r"\.so(?:\.[0-9]+)*: cannot", re.I),
]

_INPUT_WIRING_PATTERNS = [
    re.compile(r"Not a directory:\s*/tmp/poc", re.I),
    re.compile(r"argv\[0\] modified", re.I),
]


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _load_benchmark_module(path: Path):
    spec = importlib.util.spec_from_file_location("cybergym_benchmark", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"failed to load benchmark module from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _normalize_task_id(raw: str) -> str | None:
    line = raw.strip()
    if not line or line.startswith("#"):
        return None
    if line.startswith("arvo:"):
        return line
    if line.startswith("arvo_"):
        return "arvo:" + line.split("_", 1)[1]
    if line.isdigit():
        return "arvo:" + line
    raise ValueError(f"unsupported task id format: {raw!r}")


def _discover_task_ids(binary_dir: Path, payload_dir: Path) -> list[str]:
    tasks: list[str] = []
    arvo_binary_root = binary_dir / "arvo"
    arvo_payload_root = payload_dir / "arvo"
    if not arvo_binary_root.is_dir():
        raise FileNotFoundError(f"binary root not found: {arvo_binary_root}")
    if not arvo_payload_root.is_dir():
        raise FileNotFoundError(f"payload root not found: {arvo_payload_root}")
    for case_dir in sorted(arvo_binary_root.iterdir(), key=lambda p: int(p.name)):
        if not case_dir.is_dir():
            continue
        case_id = case_dir.name
        if not case_id.isdigit():
            continue
        payload_case = arvo_payload_root / case_id
        if not payload_case.is_dir():
            continue
        if not (case_dir / "poc").is_file():
            continue
        if not (payload_case / "meta.json").is_file():
            continue
        tasks.append(f"arvo:{case_id}")
    return tasks


def _load_task_ids(binary_dir: Path, payload_dir: Path, task_file: Path | None) -> list[str]:
    if task_file is None:
        return _discover_task_ids(binary_dir, payload_dir)
    tasks: list[str] = []
    for raw in task_file.read_text(encoding="utf-8").splitlines():
        task_id = _normalize_task_id(raw)
        if task_id is not None:
            tasks.append(task_id)
    return tasks


def _runtime_suspect_class(
    *,
    project: str,
    observed_output: str,
    report: dict[str, Any] | None,
) -> str:
    text = observed_output or ""
    if any(pattern.search(text) for pattern in _SHARED_LIBRARY_PATTERNS):
        return "shared_library_missing"
    if any(pattern.search(text) for pattern in _INPUT_WIRING_PATTERNS):
        return "input_wiring_issue"
    if project == "libreoffice" and any(pattern.search(text) for pattern in _RUNTIME_TREE_PATTERNS):
        return "runtime_tree_incomplete"
    observed = (report or {}).get("observed") or {}
    frames = " ".join(str(frame) for frame in (observed.get("frames") or []))
    if project == "libreoffice" and any(pattern.search(frames) for pattern in _RUNTIME_TREE_PATTERNS):
        return "runtime_tree_incomplete"
    return "none"


def _comparison_bucket(report: dict[str, Any] | None) -> str:
    if not report:
        return "none"
    comparison = report.get("comparison") or {}
    result = str(comparison.get("result") or "").strip().lower()
    return result or "none"


def _result_record(
    *,
    task_id: str,
    kind: str,
    message: str,
    report: dict[str, Any] | None,
    observed_output: str,
    duration_sec: float,
) -> dict[str, Any]:
    case_id = task_id.split(":", 1)[1]
    target = (report or {}).get("target") or {}
    observed = (report or {}).get("observed") or {}
    reference = ((report or {}).get("reference") or {}).get("signature") or {}
    project = str(target.get("project") or "")
    runtime_suspect = _runtime_suspect_class(
        project=project,
        observed_output=observed_output,
        report=report,
    )
    return {
        "task_id": task_id,
        "case_id": case_id,
        "kind": kind,
        "message": message,
        "duration_sec": round(duration_sec, 3),
        "project": project,
        "binary": target.get("binary"),
        "comparison_result": _comparison_bucket(report),
        "runtime_suspect": runtime_suspect,
        "observed_status": observed.get("status"),
        "observed_crash_type": observed.get("crash_type"),
        "observed_top_function": observed.get("top_function"),
        "reference_crash_type": reference.get("crash_type"),
        "reference_top_function": reference.get("top_function"),
        "observed_summary": observed.get("summary"),
        "reference_summary": reference.get("summary"),
    }


def _scan_one(
    module: Any,
    *,
    task_id: str,
    payload_dir: Path,
    binary_dir: Path,
    archive_dir: Path | None,
    cmd_timeout: int,
    docker_timeout: int,
    retry_cmd_timeout: int | None,
    retry_docker_timeout: int | None,
) -> dict[str, Any]:
    case_id = task_id.split(":", 1)[1]
    arvo_dir = payload_dir / "arvo" / case_id
    started = time.monotonic()
    try:
        result = module._run_gendesc_preflight(
            task_id,
            arvo_dir=arvo_dir,
            binary_dir=binary_dir,
            archive_dir=archive_dir,
            cmd_timeout=cmd_timeout,
            docker_timeout=docker_timeout,
            retry_cmd_timeout=retry_cmd_timeout,
            retry_docker_timeout=retry_docker_timeout,
        )
        report = result["report"]
        return _result_record(
            task_id=task_id,
            kind="ok",
            message="preflight passed",
            report=report,
            observed_output=str(result.get("observed_output") or ""),
            duration_sec=time.monotonic() - started,
        )
    except Exception as exc:  # benchmark-specific typed exceptions are internal
        report = getattr(exc, "report", None)
        observed_output = str(getattr(exc, "observed_output", "") or "")
        exc_type = type(exc).__name__
        message = f"{exc_type}: {exc}"
        kind = "error"
        if exc_type == "_GendescPreflightError":
            kind = "rejected"
        elif exc_type in {"_ImageUnavailable", "FileNotFoundError"}:
            kind = "infra_error"
        return _result_record(
            task_id=task_id,
            kind=kind,
            message=message,
            report=report,
            observed_output=observed_output,
            duration_sec=time.monotonic() - started,
        )


def _write_summary(out_dir: Path, rows: list[dict[str, Any]], argv: list[str]) -> None:
    kind_counts = Counter(row["kind"] for row in rows)
    suspect_counts = Counter(row["runtime_suspect"] for row in rows)
    project_kind: dict[str, Counter[str]] = defaultdict(Counter)
    for row in rows:
        project_kind[str(row["project"] or "")][row["kind"]] += 1
    summary = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "argv": argv,
        "totals": {
            "tasks": len(rows),
            "kind": dict(kind_counts),
            "runtime_suspect": dict(suspect_counts),
        },
        "projects": {
            project: dict(sorted(counter.items()))
            for project, counter in sorted(project_kind.items())
        },
    }
    (out_dir / "summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--benchmark-path",
        type=Path,
        default=Path("/mnt/olddata/home/yihe/workspace/CAGE-private/examples/cybergym/benchmark.py"),
    )
    parser.add_argument(
        "--payload-dir",
        type=Path,
        default=Path("/mnt/olddata/home/yihe/workspace/CAGE-private/examples/cybergym/datasets/payloads-arvo"),
    )
    parser.add_argument(
        "--binary-dir",
        type=Path,
        default=Path("/mnt/olddata/home/yihe/workspace/CAGE-private/examples/cybergym/datasets/server-binary-arvo"),
    )
    parser.add_argument(
        "--archive-dir",
        type=Path,
        default=Path("/mnt/olddata/home/yihe/workspace/arvo_env/metadata/upstream/ARVO-Meta/archive_data"),
    )
    parser.add_argument("--task-file", type=Path, help="Optional task list file.")
    parser.add_argument("--limit", type=int, default=0, help="Optional limit after loading tasks.")
    parser.add_argument("--workers", type=int, default=20, help="Concurrent preflight workers.")
    parser.add_argument("--cmd-timeout", type=int, default=30)
    parser.add_argument("--docker-timeout", type=int, default=300)
    parser.add_argument("--retry-cmd-timeout", type=int, default=60)
    parser.add_argument("--retry-docker-timeout", type=int, default=1800)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("/mnt/olddata/home/yihe/workspace/arvo_env/metadata/datasets/arvo/preflight_scan")
        / f"scan-{_utc_now()}",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    args.output_dir.mkdir(parents=True, exist_ok=True)

    module = _load_benchmark_module(args.benchmark_path)
    task_ids = _load_task_ids(args.binary_dir, args.payload_dir, args.task_file)
    if args.limit > 0:
        task_ids = task_ids[: args.limit]
    if not task_ids:
        print("No tasks found.", file=sys.stderr)
        return 1

    rows: list[dict[str, Any]] = []
    rows_lock = threading.Lock()
    results_path = args.output_dir / "results.jsonl"

    print(f"benchmark_path={args.benchmark_path}")
    print(f"payload_dir={args.payload_dir}")
    print(f"binary_dir={args.binary_dir}")
    print(f"archive_dir={args.archive_dir}")
    print(f"tasks={len(task_ids)}")
    print(f"workers={args.workers}")
    print(f"output_dir={args.output_dir}")
    sys.stdout.flush()

    with results_path.open("w", encoding="utf-8") as results_file:
        def _consume(record: dict[str, Any]) -> None:
            with rows_lock:
                rows.append(record)
                results_file.write(json.dumps(record, sort_keys=True) + "\n")
                results_file.flush()
                if len(rows) % 25 == 0 or len(rows) == len(task_ids):
                    kind_counts = Counter(row["kind"] for row in rows)
                    suspect_counts = Counter(row["runtime_suspect"] for row in rows)
                    print(
                        f"progress done={len(rows)}/{len(task_ids)} "
                        f"kind={dict(kind_counts)} runtime_suspect={dict(suspect_counts)}",
                        flush=True,
                    )

        with cf.ThreadPoolExecutor(max_workers=args.workers) as pool:
            futures = [
                pool.submit(
                    _scan_one,
                    module,
                    task_id=task_id,
                    payload_dir=args.payload_dir,
                    binary_dir=args.binary_dir,
                    archive_dir=args.archive_dir,
                    cmd_timeout=args.cmd_timeout,
                    docker_timeout=args.docker_timeout,
                    retry_cmd_timeout=args.retry_cmd_timeout,
                    retry_docker_timeout=args.retry_docker_timeout,
                )
                for task_id in task_ids
            ]
            for future in cf.as_completed(futures):
                _consume(future.result())

    _write_summary(args.output_dir, rows, argv or sys.argv[1:])
    print(f"wrote {results_path}")
    print(f"wrote {args.output_dir / 'summary.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
