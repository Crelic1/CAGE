"""Asynchronous, idempotent launch operations — the orchestration-safe contract.

``GET /launch`` provisions a target inside one synchronous request. Standing up a
multi-host range is minutes of ``docker compose`` work, far longer than an
ordinary client/proxy timeout, and it is a side-effecting ``GET`` with no
operation resource: when the response is lost the caller cannot tell "not
accepted" from "accepted and still running", cannot retry safely, cannot poll,
and cannot cancel before a ``run_id`` exists. See issue #4.

This module models a launch as a durable **operation** instead:

    POST   /launches            → 202 + status_url, work runs in the background
    GET    /launches/{id}       → one authoritative status (a small state machine)
    DELETE /launches/{id}       → idempotent cancel + cleanup

State machine::

    queued ─▶ starting ─▶ ready
                       └▶ failed
    queued│starting│ready ─▶ closing ─▶ closed

The operation id is the caller's ``cage_run_id`` (a stable Fleet arena uuid), so
the contract is **idempotent**: repeating the same POST returns the same
operation and never builds a second container set; reusing the id with different
launch params is a ``409``. The record is **durable** — persisted to disk before
any work is enqueued and reconciled against Docker on startup — so a lost 202 or
a Cage restart never strands the caller: the status URL (or an idempotent
re-POST) always yields an authoritative answer.

An operation reaches ``ready`` only after the whole usable result is validated:
a non-empty ``run_id``, a healthy instance, a reachable target address
(host-published ``entry_urls`` when the launch publishes, else the docker-network
``container_addr``), and a non-empty ``task_prompt``. That is what lets a caller
treat ``ready`` as "go" without a second racy prompt-discovery step.

Layer-1: this knows no benchmark. It wraps the existing provisioning
(``_launch_challenge_impl``), the health probe, and the benchmark-supplied prompt
renderer, and owns only the operation lifecycle around them.
"""
from __future__ import annotations

import hashlib
import json
import logging
import os
import tempfile
import threading
import time
from concurrent.futures import Future, ThreadPoolExecutor
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

import cage.target.server.server_state as _server_state

logger = logging.getLogger(__name__)

# ---- states ---------------------------------------------------------------- #
QUEUED = "queued"
STARTING = "starting"
READY = "ready"
FAILED = "failed"
CLOSING = "closing"
CLOSED = "closed"

_PENDING_STATES = frozenset({QUEUED, STARTING})
_TERMINAL_STATES = frozenset({FAILED, CLOSED})
# States a fresh POST with matching params may hand straight back.
_RETURNABLE_STATES = frozenset({QUEUED, STARTING, READY, FAILED, CLOSED})

# Provisioning params that define "the same launch" for idempotency. Operational
# knobs that do not change the container set (ttl, audience, advertise host) are
# deliberately excluded, so re-POSTing with a fresh lease is not a conflict.
_FINGERPRINT_KEYS = (
    "challenge_id", "target_scope", "network_only", "prompt_level",
    "parallel_mode", "network_mode", "exposure_mode",
)

# A restart re-drives an interrupted op; cap redrives so a launch that always
# dies can't spin forever.
_MAX_ATTEMPTS = int(os.getenv("TARGET_SERVER_LAUNCH_OP_MAX_ATTEMPTS", "3"))
# Polling hint (seconds) handed to callers while an op is pending, returned as
# ``retry_after`` in the /launches status body. Sized for the ~20-min startup
# budget: a heavy target can take minutes to become ready, so a caller polling
# every 2s just hammers the server — 20s is a saner re-poll cadence.
RETRY_AFTER_S = int(os.getenv("TARGET_SERVER_LAUNCH_OP_RETRY_AFTER_S", "20"))


def _now() -> float:
    return time.time()


def _fingerprint(params: Dict[str, Any]) -> str:
    payload = {k: params.get(k) for k in _FINGERPRINT_KEYS}
    blob = json.dumps(payload, sort_keys=True, default=str)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()[:16]


@dataclass
class LaunchOp:
    """One launch operation. Serialized verbatim to its ``<id>.json`` record."""

    launch_id: str
    cage_run_id: str
    challenge_id: str
    params: Dict[str, Any]
    fingerprint: str
    status: str = QUEUED
    run_id: str = ""
    result: Optional[Dict[str, Any]] = None
    error: Optional[Dict[str, Any]] = None
    attempts: int = 0
    # Durable cancellation intent (issue #5). A short-lived in-memory flag is not
    # enough: a worker that finishes provisioning AFTER cancel() returned must
    # still see the intent (and survive a restart) so it never publishes a result
    # or ``ready`` for a cancelled op.
    cancel_requested: bool = False
    created_at: float = field(default_factory=_now)
    updated_at: float = field(default_factory=_now)

    def is_pending(self) -> bool:
        return self.status in _PENDING_STATES

    def is_terminal(self) -> bool:
        return self.status in _TERMINAL_STATES


class LaunchOpError(Exception):
    """Carries an HTTP status + a structured error body."""

    def __init__(self, http_status: int, code: str, message: str):
        super().__init__(message)
        self.http_status = http_status
        self.code = code
        self.message = message


class LaunchOpStore:
    """Durable, process-restart-safe store of launch operations.

    One JSON file per operation under ``<root>/<namespace>/<launch_id>.json``,
    written atomically (temp file + ``os.replace``) so a crash mid-write never
    leaves a torn record. An in-memory cache mirrors disk for fast reads; disk is
    the source of truth across restarts. A per-``launch_id`` lock plus the store
    lock serialize the check-and-create that idempotency depends on.
    """

    def __init__(self, root: Path):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        self._id_locks: Dict[str, threading.Lock] = {}
        self._cache: Dict[str, LaunchOp] = {}
        self._load_all()

    # -- disk --------------------------------------------------------------- #
    def _path(self, launch_id: str) -> Path:
        # launch_id is a caller-supplied uuid; keep it a single safe path segment.
        safe = "".join(c if (c.isalnum() or c in "-_.") else "_" for c in str(launch_id))
        return self.root / f"{safe}.json"

    def _load_all(self) -> None:
        for p in self.root.glob("*.json"):
            try:
                data = json.loads(p.read_text(encoding="utf-8"))
                op = LaunchOp(**data)
                self._cache[op.launch_id] = op
            except Exception as exc:  # noqa: BLE001 — a torn record must not abort startup
                logger.warning("launch-op: skipping unreadable record %s: %s", p.name, exc)

    def _persist(self, op: LaunchOp) -> None:
        op.updated_at = _now()
        path = self._path(op.launch_id)
        fd, tmp = tempfile.mkstemp(dir=str(self.root), suffix=".tmp")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as fh:
                json.dump(asdict(op), fh, sort_keys=True)
            os.replace(tmp, path)  # atomic
        finally:
            if os.path.exists(tmp):
                os.unlink(tmp)

    # -- locks -------------------------------------------------------------- #
    def id_lock(self, launch_id: str) -> threading.Lock:
        with self._lock:
            lk = self._id_locks.get(launch_id)
            if lk is None:
                lk = threading.Lock()
                self._id_locks[launch_id] = lk
            return lk

    # -- accessors ---------------------------------------------------------- #
    def get(self, launch_id: str) -> Optional[LaunchOp]:
        with self._lock:
            return self._cache.get(launch_id)

    def put(self, op: LaunchOp) -> None:
        with self._lock:
            self._cache[op.launch_id] = op
            self._persist(op)

    def list_ids(self) -> List[str]:
        with self._lock:
            return list(self._cache.keys())

    def delete(self, launch_id: str) -> None:
        with self._lock:
            self._cache.pop(launch_id, None)
        try:
            self._path(launch_id).unlink()
        except FileNotFoundError:
            pass


# --------------------------------------------------------------------------- #
# Orchestrator
# --------------------------------------------------------------------------- #

# Injected by challenge_server at import time to avoid a hard import cycle
# (challenge_server imports this module). Each is the real function; tests can
# monkeypatch them.
_PROVISION_FN: Optional[Callable[..., Any]] = None
_HEALTH_FN: Optional[Callable[[str], bool]] = None
_GET_INSTANCE_FN: Optional[Callable[[str], Optional[dict]]] = None
_LOAD_CHALLENGES_FN: Optional[Callable[[], Dict[str, dict]]] = None
_RENDER_PROMPT_FN: Optional[Callable[..., Any]] = None
_CLEANUP_INSTANCE_FN: Optional[Callable[..., Any]] = None
_PURGE_BY_RUN_ID_FN: Optional[Callable[[str], int]] = None
_HAS_RESOURCES_FN: Optional[Callable[[str], bool]] = None


def configure(
    *,
    provision,
    health,
    get_instance,
    load_challenges,
    render_prompt,
    cleanup_instance,
    purge_by_run_id,
    has_resources=None,
) -> None:
    """Wire in the provisioning/health/cleanup functions from challenge_server."""
    global _PROVISION_FN, _HEALTH_FN, _GET_INSTANCE_FN, _LOAD_CHALLENGES_FN
    global _RENDER_PROMPT_FN, _CLEANUP_INSTANCE_FN, _PURGE_BY_RUN_ID_FN, _HAS_RESOURCES_FN
    _PROVISION_FN = provision
    _HEALTH_FN = health
    _GET_INSTANCE_FN = get_instance
    _LOAD_CHALLENGES_FN = load_challenges
    _RENDER_PROMPT_FN = render_prompt
    _CLEANUP_INSTANCE_FN = cleanup_instance
    _PURGE_BY_RUN_ID_FN = purge_by_run_id
    _HAS_RESOURCES_FN = has_resources


class LaunchOrchestrator:
    """Runs launch operations on a background pool and drives their state machine."""

    def __init__(self, store: LaunchOpStore, max_workers: int = 8):
        self.store = store
        self._pool = ThreadPoolExecutor(
            max_workers=max_workers, thread_name_prefix="cage-launch-op"
        )
        # The in-flight provisioning future per launch_id. Cancellation reads this
        # to tell whether a worker can still publish a result: while a worker is
        # active it OWNS teardown-after-provision, so cancel() must not declare
        # ``closed`` itself — it returns ``closing`` and lets the worker finalize.
        # The durable ``cancel_requested`` flag on the record — not this map — is
        # the authoritative intent (it survives a restart); this is only the
        # liveness signal for "is a worker still running right now".
        self._inflight: Dict[str, Future] = {}
        self._inflight_lock = threading.Lock()

    # -- submit (idempotent) ------------------------------------------------ #
    def submit(self, launch_id: str, params: Dict[str, Any]) -> tuple[LaunchOp, bool]:
        """Create-or-return the operation for ``launch_id``. Returns (op, created).

        Idempotent: an existing op with matching params is returned untouched
        (no second container set); one with different params raises 409.
        """
        fp = _fingerprint(params)
        with self.store.id_lock(launch_id):
            existing = self.store.get(launch_id)
            if existing is not None:
                if existing.fingerprint != fp:
                    raise LaunchOpError(
                        409, "idempotency_conflict",
                        f"cage_run_id {launch_id!r} already exists with different "
                        "launch parameters; use a fresh cage_run_id to launch again.",
                    )
                return existing, False
            op = LaunchOp(
                launch_id=launch_id,
                cage_run_id=str(params.get("cage_run_id") or launch_id),
                challenge_id=str(params.get("challenge_id") or ""),
                params=dict(params),
                fingerprint=fp,
                status=QUEUED,
            )
            self.store.put(op)
        self._enqueue(launch_id)
        return op, True

    def _enqueue(self, launch_id: str) -> None:
        fut = self._pool.submit(self._run, launch_id)
        with self._inflight_lock:
            self._inflight[launch_id] = fut
        fut.add_done_callback(lambda f, lid=launch_id: self._on_worker_done(lid, f))

    def _on_worker_done(self, launch_id: str, fut: Future) -> None:
        with self._inflight_lock:
            if self._inflight.get(launch_id) is fut:
                self._inflight.pop(launch_id, None)

    def _worker_active(self, launch_id: str) -> bool:
        """True while a provisioning worker for this op is still running.

        ``closed`` may not be declared while this is true: the worker may still be
        about to publish a ``run_id`` (and thus a live target). Cancellation of an
        op with an active worker returns ``closing`` and defers finalization to the
        worker's own post-provision fence.
        """
        with self._inflight_lock:
            fut = self._inflight.get(launch_id)
        return fut is not None and not fut.done()

    def _is_cancel_requested(self, launch_id: str) -> bool:
        op = self.store.get(launch_id)
        return bool(op is not None and op.cancel_requested)

    # -- cancel (idempotent) ----------------------------------------------- #
    def cancel(self, launch_id: str) -> Optional[LaunchOp]:
        """Cancel an operation. Idempotent; ``None`` if unknown.

        Records durable cancellation intent, then either finalizes now or defers:

        * If a provisioning worker is still active, it OWNS teardown of whatever
          it builds — declaring ``closed`` here could race it back to ``ready``.
          So we return ``closing``; the worker's post-provision fence tears its
          resources down and finalizes. Poll the status URL to ``closed``.
        * Otherwise (never started, or already finished) we finalize inline:
          tear down, then a final resource probe gates the ``closed`` write.

        ``closed`` is therefore only ever written once the worker is quiescent
        AND a probe confirms the ``cage_run_id`` resources are gone.
        """
        op = self.store.get(launch_id)
        if op is None:
            return None
        with self.store.id_lock(launch_id):
            op = self.store.get(launch_id)
            if op is None:
                return None
            if op.status == CLOSED:
                return op  # already fully closed — idempotent no-op
            op.cancel_requested = True
            if op.status != CLOSING:
                op.status = CLOSING
            self.store.put(op)
        if self._worker_active(launch_id):
            # Defer to the worker; it finalizes after it stops touching resources.
            return self.store.get(launch_id)
        return self._finalize_cancellation(launch_id)

    def _finalize_cancellation(self, launch_id: str) -> Optional[LaunchOp]:
        """Tear down a cancelled op and write ``closed`` only if resources are gone.

        Callers guarantee worker quiescence for this attempt (``cancel`` checks
        ``_worker_active``; the worker calls this from its own unwinding ``finally``;
        reconcile calls it single-threaded at startup). Teardown targets both the
        in-memory instance (if a ``run_id`` was recorded) and any docker resources
        tagged with the ``cage_run_id`` — covering resources a just-unwound worker
        created after cancellation. If teardown raises or a final probe still finds
        resources, the op stays ``closing`` with a retryable ``cleanup_incomplete``
        error; a repeated DELETE (or reconcile) retries until it is genuinely gone.
        """
        op = self.store.get(launch_id)
        if op is None or op.status == CLOSED:
            return op
        teardown_ok = self._teardown(op)
        present = False
        if _HAS_RESOURCES_FN is not None:
            try:
                present = bool(_HAS_RESOURCES_FN(op.cage_run_id))
            except Exception as exc:  # noqa: BLE001 — unknown → treat as still present
                logger.warning("launch-op %s: resource probe failed: %s", launch_id, exc)
                present = True
        with self.store.id_lock(launch_id):
            cur = self.store.get(launch_id) or op
            if cur.status == CLOSED:
                return cur
            if teardown_ok and not present:
                cur.status = CLOSED
                cur.result = None
                cur.error = {"code": "cancelled", "message": "launch cancelled",
                             "retryable": False}
            else:
                cur.status = CLOSING
                cur.error = {"code": "cleanup_incomplete",
                             "message": "cancellation cleanup did not confirm resource "
                                        "removal; retry DELETE", "retryable": True}
            self.store.put(cur)
            return cur

    def _teardown(self, op: LaunchOp) -> bool:
        """Tear down an op's resources. Returns True iff every step succeeded.

        A swallowed exception used to let a caller declare ``closed`` while
        containers remained (issue #5). Returning success/failure lets the
        cancellation path keep the op ``closing`` until cleanup actually works.
        """
        ok = True
        if op.run_id and _CLEANUP_INSTANCE_FN is not None:
            try:
                _CLEANUP_INSTANCE_FN(op.challenge_id, op.run_id)
            except Exception as exc:  # noqa: BLE001
                logger.warning("launch-op %s: cleanup_instance failed: %s", op.launch_id, exc)
                ok = False
        if _PURGE_BY_RUN_ID_FN is not None:
            try:
                _PURGE_BY_RUN_ID_FN(op.cage_run_id)
            except Exception as exc:  # noqa: BLE001
                logger.warning("launch-op %s: purge-by-label failed: %s", op.launch_id, exc)
                ok = False
        return ok

    # -- worker ------------------------------------------------------------- #
    def _run(self, launch_id: str) -> None:
        """Provision + validate an op, fenced against cancellation.

        Wraps ``_run_impl`` so that no matter which path the worker exits by
        (cancelled before start, cancelled mid-provision, superseded), a pending
        cancellation is always finalized from the worker's own thread — the point
        at which this attempt is guaranteed quiescent.
        """
        try:
            self._run_impl(launch_id)
        finally:
            op = self.store.get(launch_id)
            if op is not None and op.cancel_requested and op.status != CLOSED:
                self._finalize_cancellation(launch_id)

    def _run_impl(self, launch_id: str) -> None:
        op = self.store.get(launch_id)
        if op is None or op.status != QUEUED:
            return
        with self.store.id_lock(launch_id):
            op = self.store.get(launch_id)
            if op is None or op.status != QUEUED:
                return
            if op.cancel_requested:
                # Cancelled before we began — do not provision. The ``finally`` in
                # _run finalizes the cancellation (nothing to tear down yet).
                return
            op.status = STARTING
            op.attempts += 1
            my_gen = op.attempts   # this worker owns attempt ``my_gen``
            self.store.put(op)

        try:
            resp = _PROVISION_FN(  # type: ignore[misc]
                chal_id=op.challenge_id,
                force_recreate=False,
                parallel_mode=op.params.get("parallel_mode"),
                target_scope=op.params.get("target_scope"),
                network_mode=op.params.get("network_mode"),
                exposure_mode=op.params.get("exposure_mode"),
                cage_run_id=op.cage_run_id,
                audience=str(op.params.get("audience") or "internal"),
                network_only=bool(op.params.get("network_only")),
                prompt_level=str(op.params.get("prompt_level") or "l0"),
                public_host=str(op.params.get("public_host") or ""),
                public_host_source=str(op.params.get("public_host_source") or ""),
                ttl_s=op.params.get("ttl"),
            )
        except Exception as exc:  # noqa: BLE001
            if self._is_cancel_requested(launch_id):
                return  # cancellation raced in; _run's finally finalizes cleanup
            self._fail(launch_id, "startup_failed", str(exc)[:500], retryable=True, cleanup=True)
            return

        run_id = str(getattr(resp, "run_id", "") or "")
        # FENCE 1 — record the run_id we created (so teardown can target it) but
        # only KEEP driving toward ready if we still own the current attempt and
        # no cancellation landed. Otherwise bail; _run's finally tears it down.
        if not self._claim_attempt(launch_id, my_gen, run_id):
            return

        ok, result, err = self._validate_ready(op, resp, run_id)
        if not ok:
            if self._is_cancel_requested(launch_id):
                return
            self._fail(launch_id, err["code"], err["message"],
                       retryable=err.get("retryable", False), cleanup=True)
            return

        # FENCE 2 — publish ``ready`` only if this attempt still owns the op and no
        # cancellation landed while we were validating.
        with self.store.id_lock(launch_id):
            cur = self.store.get(launch_id)
            if cur is None:
                return
            if cur.cancel_requested or cur.status != STARTING or cur.attempts != my_gen:
                cur.run_id = run_id
                self.store.put(cur)
                return
            cur.status = READY
            cur.result = result
            cur.error = None
            cur.run_id = run_id
            self.store.put(cur)

    def _claim_attempt(self, launch_id: str, my_gen: int, run_id: str) -> bool:
        """Persist ``run_id`` and report whether this worker still owns the op.

        The ``run_id`` is written unconditionally so a subsequent teardown can
        target the resources this attempt created — even when ownership was lost.
        Ownership holds iff the op is still ``starting`` on this attempt and no
        cancellation has been requested.
        """
        with self.store.id_lock(launch_id):
            cur = self.store.get(launch_id)
            if cur is None:
                return False
            cur.run_id = run_id
            owned = (not cur.cancel_requested
                     and cur.status == STARTING
                     and cur.attempts == my_gen)
            self.store.put(cur)
            return owned

    def _validate_ready(self, op: LaunchOp, resp: Any, run_id: str):
        """Gate on the full usable result. Returns (ok, result_dict, error_dict)."""
        if not run_id:
            return False, None, {"code": "no_run_id",
                                 "message": "provisioning produced no run_id", "retryable": True}
        if _HEALTH_FN is not None and not _HEALTH_FN(run_id):
            return False, None, {"code": "unhealthy",
                                 "message": "instance did not become healthy", "retryable": True}

        entry_urls = [
            u if isinstance(u, dict) else (u.model_dump() if hasattr(u, "model_dump") else dict(u))
            for u in (getattr(resp, "entry_urls", None) or [])
        ]
        container_addr = list(getattr(resp, "container_addr", None) or [])
        network_only = bool(op.params.get("network_only"))
        # A publishing launch must expose a host-reachable entry_urls; a
        # network-only launch is reachable at its container_addr on the network.
        if not network_only and not entry_urls:
            return False, None, {
                "code": "entry_urls_unavailable",
                "message": "no host-published entry_urls resolved for a publishing launch",
                "retryable": True,
            }
        if network_only and not container_addr:
            return False, None, {
                "code": "container_addr_unavailable",
                "message": "no container_addr resolved for a network-only launch",
                "retryable": True,
            }

        task_prompt, task_prompt_template = self._render_prompt(op, run_id)
        if not task_prompt:
            return False, None, {
                "code": "prompt_unavailable",
                "message": "challenge did not produce a task prompt",
                "retryable": False,
            }

        result = {
            "run_id": run_id,
            "chal_id": op.challenge_id,
            "entry_urls": entry_urls,
            "container_addr": container_addr,
            "network_name": getattr(resp, "network_name", None),
            "network_subnet": getattr(resp, "network_subnet", None),
            "prompt_level": str(op.params.get("prompt_level") or "l0"),
            "task_prompt": task_prompt,
            "task_prompt_template": task_prompt_template,
        }
        return True, result, None

    def _render_prompt(self, op: LaunchOp, run_id: str) -> tuple[str, str]:
        if _RENDER_PROMPT_FN is None or _GET_INSTANCE_FN is None or _LOAD_CHALLENGES_FN is None:
            return "", ""
        try:
            instance = _GET_INSTANCE_FN(run_id)
            challenge = (_LOAD_CHALLENGES_FN() or {}).get(op.challenge_id)
            if instance is None or challenge is None:
                return "", ""
            public_host = str(op.params.get("public_host") or "")
            # Only rewrite to a public host when the instance is actually
            # published; a network-only instance keeps its docker addresses.
            from cage.target.server.public_access import instance_is_public
            if not instance_is_public(instance):
                public_host = ""
            return _RENDER_PROMPT_FN(
                run_id, instance, challenge,
                prompt_level=str(op.params.get("prompt_level") or "l0"),
                public_host=public_host,
            )
        except Exception as exc:  # noqa: BLE001
            logger.warning("launch-op %s: prompt render failed: %s", op.launch_id, exc)
            return "", ""

    def _fail(self, launch_id: str, code: str, message: str, *,
              retryable: bool, cleanup: bool) -> None:
        op = self.store.get(launch_id)
        if op is None:
            return
        if cleanup:
            self._teardown(op)
        with self.store.id_lock(launch_id):
            cur = self.store.get(launch_id)
            if cur is None:
                return
            cur.status = FAILED
            cur.error = {"code": code, "message": message, "retryable": retryable}
            self.store.put(cur)

    # -- restart reconciliation -------------------------------------------- #
    def reconcile_on_startup(self) -> None:
        """Bring persisted ops back in line with reality after a restart.

        A ``ready``/``failed``/``closed`` op is authoritative and left alone. An op
        carrying **cancellation intent** (``cancel_requested``, or a ``closing``
        record) is finalized — its resources are torn down by ``cage.run_id``
        label and it reaches ``closed`` only once a probe confirms they are gone
        (issue #5); it is never re-driven. A plain ``queued`` op never started, so
        it is re-enqueued. A plain ``starting`` op was interrupted mid-provision:
        its partial docker resources are purged and, unless it has exhausted its
        attempts, it is reset to ``queued`` and re-driven under the same id. This
        never resumes a half-built instance.
        """
        for launch_id in self.store.list_ids():
            op = self.store.get(launch_id)
            if op is None or op.is_terminal():
                continue
            # Cancellation intent survives a restart and takes precedence over any
            # re-drive: finalize (fenced, evidence-backed) instead of relaunching.
            if op.cancel_requested or op.status == CLOSING:
                self._finalize_cancellation(launch_id)
                continue
            if op.status == READY:
                # A ready op is only still valid if its containers survived the
                # restart (a crash). A graceful shutdown tore them down, so the
                # ready record is stale — mark it terminal so the caller relaunches
                # instead of dialing a target that is gone.
                if _HAS_RESOURCES_FN is not None and not _HAS_RESOURCES_FN(op.cage_run_id):
                    self._fail(launch_id, "instance_gone",
                               "the launched target no longer exists after a Cage restart",
                               retryable=True, cleanup=True)
                continue
            # queued or starting: purge any partial build, then re-drive.
            self._teardown(op)
            if op.attempts >= _MAX_ATTEMPTS:
                self._fail(launch_id, "restart_attempts_exhausted",
                           f"launch did not complete after {op.attempts} attempts across restarts",
                           retryable=False, cleanup=True)
                continue
            with self.store.id_lock(launch_id):
                cur = self.store.get(launch_id)
                if cur is None:
                    continue
                cur.status = QUEUED
                cur.run_id = ""
                self.store.put(cur)
            logger.info("launch-op %s: re-driving after restart (attempt %d)",
                        launch_id, op.attempts + 1)
            self._enqueue(launch_id)

    def shutdown(self) -> None:
        self._pool.shutdown(wait=False, cancel_futures=True)


# --------------------------------------------------------------------------- #
# Module singletons (built lazily so tests can point the store at a tmp dir)
# --------------------------------------------------------------------------- #
_STORE: Optional[LaunchOpStore] = None
_ORCH: Optional[LaunchOrchestrator] = None
_singleton_lock = threading.Lock()


def _default_root() -> Path:
    root = os.getenv("TARGET_SERVER_LAUNCH_OPS_DIR", "").strip()
    if root:
        base = Path(root)
    else:
        base = Path.cwd() / ".cage_launch_ops"
    return base / str(_server_state.TARGET_SERVER_NAMESPACE)


def get_orchestrator() -> LaunchOrchestrator:
    global _STORE, _ORCH
    with _singleton_lock:
        if _ORCH is None:
            _STORE = LaunchOpStore(_default_root())
            _ORCH = LaunchOrchestrator(_STORE)
        return _ORCH


def reset_for_test(root: Path) -> LaunchOrchestrator:
    """Rebuild the singletons against ``root`` — test helper only."""
    global _STORE, _ORCH
    with _singleton_lock:
        if _ORCH is not None:
            _ORCH.shutdown()
        _STORE = LaunchOpStore(root)
        _ORCH = LaunchOrchestrator(_STORE)
        return _ORCH


def status_view(op: LaunchOp, *, base_path: str = "/launches") -> Dict[str, Any]:
    """Public status representation returned by GET/POST /launches."""
    body: Dict[str, Any] = {
        "launch_id": op.launch_id,
        "cage_run_id": op.cage_run_id,
        "challenge_id": op.challenge_id,
        "status": op.status,
        "status_url": f"{base_path}/{op.launch_id}",
    }
    if op.status in _PENDING_STATES or op.status == CLOSING:
        body["retry_after"] = RETRY_AFTER_S
    if op.result is not None:
        body["result"] = op.result
    if op.error is not None:
        body["error"] = op.error
    return body
