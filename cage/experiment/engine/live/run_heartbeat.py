"""Run heartbeat — the authoritative answer to "is this ``cage run`` alive?"

Every other liveness signal in the codebase is an *approximation*: a
``progress.json`` that ticks when the agent makes an LLM call, an
``experiment_record.json`` whose mtime moves at trial boundaries, a
``planned_trials.json`` written once at startup. Each proves life when it is
fresh, and proves nothing when it is stale — a run can be perfectly healthy
while pulling a multi-gigabyte target image, waiting out a model's rate-limit
backoff, or sitting inside a single long agent turn. Inferring death from a
quiet file is the reason a live run could be badged "Stopped".

This module records the one fact that actually answers the question: the
**process id** of the orchestrator, next to a periodically refreshed timestamp.

  * Same host → ``os.kill(pid, 0)`` is a definitive, real-time answer that no
    amount of filesystem quiet can confuse.
  * Different host (NAS-shared ``.cage_runs/``, where the pid is meaningless and
    might even collide with an unrelated local process) → fall back to heartbeat
    freshness, which is still far better than the old signals because the writer
    is a dedicated thread that ticks regardless of what the trial is doing.

Reads and writes ``<run_dir>/runtime_status.json`` only.
"""

from __future__ import annotations

import json
import os
import socket
import threading
import time
from dataclasses import dataclass
from pathlib import Path

RUNTIME_STATUS_FILENAME = "runtime_status.json"
RUNTIME_STATUS_SCHEMA = "runtime_status.v1"

#: How often the writer thread refreshes ``heartbeat_at``. Short enough that the
#: staleness window below stays tight, long enough to be free (one small write).
HEARTBEAT_INTERVAL_S = 15.0

#: A cross-host heartbeat older than this means the writer is gone. Three missed
#: ticks plus slack, so a loaded host or a slow NAS write cannot fake a death.
HEARTBEAT_STALE_AFTER_S = 90.0


@dataclass(frozen=True)
class RunProcessStatus:
    """What ``runtime_status.json`` says about the orchestrator process."""

    pid: int
    hostname: str
    started_at: str
    heartbeat_at_ms: int

    @property
    def is_local(self) -> bool:
        """True when this record was written by a process on *this* host."""

        return bool(self.hostname) and self.hostname == socket.gethostname()


def runtime_status_path(run_dir: Path) -> Path:
    """Path of the run's process-status file."""

    return Path(run_dir) / RUNTIME_STATUS_FILENAME


def read_run_process_status(run_dir: Path) -> RunProcessStatus | None:
    """Load ``runtime_status.json``; ``None`` when absent or unreadable.

    ``None`` means "this run predates the heartbeat, or never got far enough to
    write one" — callers must fall back to the older filesystem heuristics
    rather than concluding the run is dead.
    """

    try:
        data = json.loads(runtime_status_path(run_dir).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    if not isinstance(data, dict):
        return None
    try:
        pid = int(data.get("pid") or 0)
    except (TypeError, ValueError):
        pid = 0
    try:
        heartbeat_at_ms = int(data.get("heartbeat_at_ms") or 0)
    except (TypeError, ValueError):
        heartbeat_at_ms = 0
    return RunProcessStatus(
        pid=pid,
        hostname=str(data.get("hostname") or ""),
        started_at=str(data.get("started_at") or ""),
        heartbeat_at_ms=heartbeat_at_ms,
    )


def process_is_alive(pid: int) -> bool:
    """True when ``pid`` names a live process on this host.

    Signal 0 performs the permission and existence checks without delivering
    anything. ``PermissionError`` means the process exists but is owned by
    another user — still alive, which is the question being asked.
    """

    if pid <= 0:
        return False
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    except OSError:
        return False
    return True


def run_process_is_alive(run_dir: Path) -> bool | None:
    """Definitive liveness for a run, or ``None`` when it cannot be determined.

    Tri-state on purpose. ``True``/``False`` are answers a caller should trust
    over any filesystem heuristic; ``None`` means this module has nothing to say
    (no status file — a legacy or barely-started run) and the caller should fall
    back to its own signals. Collapsing ``None`` into ``False`` would mark every
    pre-heartbeat run dead.
    """

    status = read_run_process_status(run_dir)
    if status is None:
        return None
    if status.is_local:
        return process_is_alive(status.pid)
    if status.heartbeat_at_ms <= 0:
        return None
    age_s = (time.time() * 1000 - status.heartbeat_at_ms) / 1000.0
    return age_s < HEARTBEAT_STALE_AFTER_S


class RunHeartbeat:
    """Background writer that keeps each run dir's ``runtime_status.json`` fresh.

    One ``cage run`` writes into one directory *per agent subject*
    (``<cage_runs>/<agent>:<model>:<mode>/<run_id>/``), and the inspector treats
    each of those as its own run. A single writer therefore tracks a growing set
    of directories rather than one: :meth:`track` is called as each subject's
    run dir comes into existence, and every tick refreshes all of them.

    Started once per ``cage run`` and stopped in the conductor's teardown. The
    thread is a daemon so a hard exit can never be blocked by it, and every
    write is best-effort: losing a heartbeat degrades liveness reporting, it
    must never interfere with the run itself.
    """

    def __init__(self, *, interval_s: float = HEARTBEAT_INTERVAL_S) -> None:
        """Create a heartbeat writer with no directories tracked yet."""

        self.interval_s = interval_s
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None
        self._started_at = time.strftime("%Y-%m-%dT%H:%M:%S")
        self._lock = threading.RLock()
        self._run_dirs: set[Path] = set()

    def track(self, run_dir: Path) -> None:
        """Add ``run_dir`` to the heartbeat set and stamp it immediately.

        The immediate write matters: a subject must read as alive from the
        moment its run dir exists, not from the next tick — startup (image
        pulls, target boot, preflight) is precisely the window during which
        everything else on disk is quiet and the run used to look dead.
        """

        path = Path(run_dir)
        with self._lock:
            self._run_dirs.add(path)
        self._write_one(path)

    def start(self) -> None:
        """Begin refreshing tracked directories in the background."""

        if self._thread is not None:
            return
        thread = threading.Thread(
            target=self._loop,
            name="cage-run-heartbeat",
            daemon=True,
        )
        self._thread = thread
        thread.start()

    def stop(self) -> None:
        """Stop refreshing and remove every status file written.

        Removal is what makes a *clean* exit instantly observable: no file means
        no live process, with no staleness window to wait out. A crash leaves the
        file behind, which is the case ``run_process_is_alive`` resolves through
        the pid.
        """

        self._stop.set()
        thread = self._thread
        if thread is not None:
            thread.join(timeout=2.0)
            self._thread = None
        with self._lock:
            run_dirs = list(self._run_dirs)
            self._run_dirs.clear()
        for run_dir in run_dirs:
            try:
                runtime_status_path(run_dir).unlink(missing_ok=True)
            except OSError:
                pass

    def _loop(self) -> None:
        while not self._stop.wait(self.interval_s):
            with self._lock:
                run_dirs = list(self._run_dirs)
            for run_dir in run_dirs:
                self._write_one(run_dir)

    def _write_one(self, run_dir: Path) -> None:
        payload = {
            "schema_version": RUNTIME_STATUS_SCHEMA,
            "pid": os.getpid(),
            "hostname": socket.gethostname(),
            "started_at": self._started_at,
            "heartbeat_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "heartbeat_at_ms": int(time.time() * 1000),
            "heartbeat_interval_s": self.interval_s,
        }
        path = runtime_status_path(run_dir)
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            tmp = path.with_suffix(".json.tmp")
            tmp.write_text(
                json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            os.replace(tmp, path)
        except OSError:
            pass


__all__ = [
    "HEARTBEAT_INTERVAL_S",
    "HEARTBEAT_STALE_AFTER_S",
    "RUNTIME_STATUS_FILENAME",
    "RunHeartbeat",
    "RunProcessStatus",
    "process_is_alive",
    "read_run_process_status",
    "run_process_is_alive",
    "runtime_status_path",
]
