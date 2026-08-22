"""Asynchronous re-judge operations — the same contract shape as ``/launches``.

A re-judge is one model call per submitted finding. That is far quicker than a
launch, but still long enough to outlive a proxy's patience on a submission with
many findings, so it gets the same operation-resource treatment
:mod:`launch_ops` gives provisioning::

    POST /rescores            → 202 + status_url, work runs in the background
    GET  /rescores/{run_id}   → one authoritative status

State machine::

    queued ─▶ running ─▶ done
                      └▶ failed

The operation id is the ``run_id`` being re-judged, which makes concurrent
re-judges of one submission impossible by construction — they would race on
``record.json`` and on the canonical score file. Re-POSTing while an operation
is still pending returns that same operation instead of starting a second.

Where this deliberately differs from :mod:`launch_ops`:

  - **Re-POSTing a finished operation starts a new one.** A launch is returned
    verbatim once terminal, because repeating it would build a second container
    set. Re-judging is idempotent in the way that matters — it never mutates the
    agent's submission, only appends a verdict — and "judge this again with the
    key I just fixed" is precisely the operation being asked for.
  - **No cancel, no teardown.** A re-judge owns no containers; there is nothing
    to tear down, and nothing that keeps running after it returns.
  - **Operations are in-memory.** :mod:`launch_ops` persists because a lost
    launch record strands real containers. Here the durable artifact is the
    submission record itself: after a restart, ``GET`` answers from
    ``record.json``, which is the actual ground truth about whether a re-judge
    landed. An operation record would only be a less reliable copy of it.

Layer-1: knows no benchmark. It owns the operation lifecycle around a callable.
"""
from __future__ import annotations

import logging
import os
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, Optional

logger = logging.getLogger(__name__)

QUEUED = "queued"
RUNNING = "running"
DONE = "done"
FAILED = "failed"

_PENDING_STATES = frozenset({QUEUED, RUNNING})

# Polling hint (seconds) handed to callers while an operation is pending. A
# re-judge is tens of seconds, not the ~20 minutes a heavy launch can take, so
# this is much shorter than the launch-op hint.
RETRY_AFTER_S = int(os.getenv("TARGET_SERVER_RESCORE_OP_RETRY_AFTER_S", "5"))
# Re-judges run inside a serve process that is also provisioning targets, and
# each one internally fans out to several judge calls of its own. Keep the
# outer concurrency small so a batch of re-judges cannot crowd out launches.
_MAX_WORKERS = int(os.getenv("TARGET_SERVER_RESCORE_OP_WORKERS", "2"))


def _now() -> float:
    return time.time()


@dataclass
class RescoreOp:
    """One re-judge operation."""

    run_id: str
    status: str = QUEUED
    result: Optional[Dict[str, Any]] = None
    error: Optional[Dict[str, Any]] = None
    attempts: int = 0
    created_at: float = field(default_factory=_now)
    updated_at: float = field(default_factory=_now)

    def is_pending(self) -> bool:
        return self.status in _PENDING_STATES


class RescoreOrchestrator:
    """Runs re-judges off the request thread, one at a time per submission."""

    def __init__(self, max_workers: int = _MAX_WORKERS):
        self._ops: Dict[str, RescoreOp] = {}
        self._guard = threading.Lock()
        self._pool = ThreadPoolExecutor(
            max_workers=max(1, max_workers), thread_name_prefix="rescore-op"
        )

    def get(self, run_id: str) -> Optional[RescoreOp]:
        with self._guard:
            return self._ops.get(str(run_id))

    def submit(
        self, run_id: str, work: Callable[[], Dict[str, Any]]
    ) -> tuple[RescoreOp, bool]:
        """Queue a re-judge. Returns ``(op, started)``.

        ``started`` is False when an operation for this ``run_id`` was already
        pending — the caller is handed that one rather than a second re-judge of
        the same submission.
        """
        run_id = str(run_id)
        with self._guard:
            existing = self._ops.get(run_id)
            if existing is not None and existing.is_pending():
                return existing, False
            op = RescoreOp(
                run_id=run_id,
                status=QUEUED,
                attempts=(existing.attempts if existing else 0) + 1,
            )
            self._ops[run_id] = op
        self._pool.submit(self._run, run_id, work)
        return op, True

    def _update(self, run_id: str, **changes: Any) -> None:
        with self._guard:
            op = self._ops.get(run_id)
            if op is None:
                return
            for key, value in changes.items():
                setattr(op, key, value)
            op.updated_at = _now()

    def _run(self, run_id: str, work: Callable[[], Dict[str, Any]]) -> None:
        self._update(run_id, status=RUNNING)
        try:
            result = work()
        except Exception as exc:  # noqa: BLE001 — surfaced as the op's error
            logger.warning("rescore op %s failed: %s", run_id, exc)
            self._update(
                run_id,
                status=FAILED,
                error={"code": type(exc).__name__, "message": str(exc)},
            )
            return
        self._update(run_id, status=DONE, result=result, error=None)

    def shutdown(self) -> None:
        self._pool.shutdown(wait=False)


_orchestrator: Optional[RescoreOrchestrator] = None
_orchestrator_guard = threading.Lock()


def get_orchestrator() -> RescoreOrchestrator:
    global _orchestrator
    with _orchestrator_guard:
        if _orchestrator is None:
            _orchestrator = RescoreOrchestrator()
        return _orchestrator


def reset_for_test() -> RescoreOrchestrator:
    """Drop any existing orchestrator so a test starts from a clean registry."""
    global _orchestrator
    with _orchestrator_guard:
        if _orchestrator is not None:
            _orchestrator.shutdown()
        _orchestrator = RescoreOrchestrator()
        return _orchestrator


def status_view(op: RescoreOp, *, base_path: str = "/rescores") -> Dict[str, Any]:
    """Public status representation returned by GET/POST ``/rescores``."""
    body: Dict[str, Any] = {
        "run_id": op.run_id,
        "status": op.status,
        "status_url": f"{base_path}/{op.run_id}",
        "attempts": op.attempts,
    }
    if op.is_pending():
        body["retry_after"] = RETRY_AFTER_S
    if op.result is not None:
        body["result"] = op.result
    if op.error is not None:
        body["error"] = op.error
    return body
