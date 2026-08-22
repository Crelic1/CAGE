#!/usr/bin/env python3
"""Wait for a retry tmux session, then materialize its final ARVO snapshot.

This monitor intentionally keys completion on the retry session instead of the
shared run's `experiment_record.status`: an older interrupted process can keep
that record marked `running` even after the retry itself has finished.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from datetime import UTC, datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BUILD_SNAPSHOT = ROOT / "scripts" / "build_local_snapshot.py"
BUILD_SHOWCASE = ROOT / "scripts" / "build_description_showcase.py"


def session_exists(session: str) -> bool:
    return subprocess.run(
        ["tmux", "has-session", "-t", session],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    ).returncode == 0


def run(command: list[str]) -> None:
    print("+", " ".join(command), flush=True)
    subprocess.run(command, check=True)


def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--tmux-session", required=True)
    ap.add_argument("--run-dir", type=Path, required=True)
    ap.add_argument("--snapshot-id", required=True)
    ap.add_argument("--snapshot-root", type=Path, default=ROOT / "snapshots")
    ap.add_argument(
        "--update-existing",
        action="store_true",
        help="update an existing snapshot directory in place instead of creating a new one",
    )
    ap.add_argument("--poll-seconds", type=float, default=30.0)
    ap.add_argument("--showcase-count", type=int, default=200)
    return ap.parse_args()


def main() -> None:
    args = parse_args()
    out_dir = args.snapshot_root.expanduser().resolve() / args.snapshot_id
    if out_dir.exists() and not args.update_existing:
        raise SystemExit(f"refusing to overwrite existing snapshot: {out_dir}")
    if not session_exists(args.tmux_session):
        raise SystemExit(f"retry tmux session not found: {args.tmux_session}")

    print(f"monitoring retry session {args.tmux_session}", flush=True)
    while session_exists(args.tmux_session):
        print(f"{datetime.now(UTC).isoformat()} retry session still active", flush=True)
        time.sleep(args.poll_seconds)

    completed_at = datetime.now(UTC).isoformat()
    print(f"{completed_at} retry session exited; materializing snapshot", flush=True)
    run([
        sys.executable,
        str(BUILD_SNAPSHOT),
        "--run-dir", str(args.run_dir.expanduser().resolve()),
        "--out-dir", str(out_dir),
    ])
    run([
        sys.executable,
        str(BUILD_SHOWCASE),
        "--snapshot-dir", str(out_dir),
        "--out-dir", str(out_dir / f"showcase-{args.showcase_count}"),
        "--count", str(args.showcase_count),
    ])
    (out_dir / "MONITOR.json").write_text(json.dumps({
        "retry_tmux_session": args.tmux_session,
        "retry_session_exited_at": completed_at,
        "source_run_dir": str(args.run_dir.expanduser().resolve()),
        "snapshot_id": args.snapshot_id,
        "updated_existing_snapshot": args.update_existing,
        "showcase_count": args.showcase_count,
    }, indent=2) + "\n", encoding="utf-8")
    print(f"snapshot ready: {out_dir}", flush=True)


if __name__ == "__main__":
    main()
