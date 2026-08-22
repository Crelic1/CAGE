"""Run-scoped concurrency scheduler + cooperative stop signal.

A single :class:`RunScheduler` owns every piece of shared admission/concurrency
state for one ``run_experiment`` call:

* the cooperative **stop event** — the cross-cutting cancellation token threads
  poll to bail out of gates and waits when the user presses Ctrl+C;
* the **admission gate** — a :class:`~cage.sandbox.admission.HostMemoryGate`
  that pauses new trials while host memory is saturated;
* a **two-level trial concurrency gate** — a global cap on simultaneous trials
  (``runtime.max_trials_global``) plus a per-agent cap (``AgentInstance.max_concurrent``);
* a **target-setup gate** — limits concurrent target-stack launches without
  limiting agent testing.

These used to be six module globals in ``orchestrator.py``; collapsing them into
one object means the conductor builds it once and threads the *same reference*
through trial execution and cleanup (a mutable global can't be re-exported across
modules, an object reference can). An :meth:`RunScheduler.inactive` instance with
no semaphores makes every gate a no-op, so call sites never need ``None`` guards
when no run is active (unit tests, leaf classifiers).
"""

from __future__ import annotations

import contextlib
import logging
import threading
from typing import Any

from cage.sandbox.admission import HostMemoryGate, null_gate

logger = logging.getLogger(__name__)

# Mirrors conductor's sentinel for "no per-agent cap"; a cap equal to it is
# not a real bound and must not shrink the reported capacity.
_UNLIMITED_AGENT_CAP = 100_000


def _cap_text(cap: int | None) -> str:
    if cap is None:
        return "uncapped"
    return "drained" if cap == 0 else str(cap)


class EndpointPool:
    """Per-agent endpoint slots, where taking a slot IS choosing the endpoint.

    A multi-source agent used to pick its endpoint by ``trial_index % n`` and
    gate concurrency separately, which meant a 4-slot box and a 32-slot box got
    the same share of trials — the small one thrashed while the big one idled.
    Folding the two decisions together fixes that without a weighting formula:
    a trial waits for *some* endpoint to have room, and whichever has room is
    the one it uses. A saturated endpoint simply stops being handed work, so a
    slow box de-weights itself.

    ``capacity`` semantics, per entry:

    * ``None`` — uncapped. Never blocks; only the agent/global gates apply.
      This is what an undeclared source gets: the framework does not invent a
      number for a box whose size it cannot know.
    * ``0`` — drained. Never selected, so in-flight trials finish while no new
      ones start. This is how an endpoint is retired without interrupting work.
    * ``N > 0`` — at most N trials in flight against that endpoint.

    Selection picks the endpoint with the fewest in-flight trials (ties go to
    the earlier one), which keeps a mixed pool balanced instead of letting an
    uncapped entry starve the capped ones.
    """

    def __init__(self, entries: list[tuple[Any, int | None]]) -> None:
        self._entries = list(entries)
        self._active = [0] * len(self._entries)
        self._cv = threading.Condition()

    def __len__(self) -> int:
        return len(self._entries)

    @property
    def total_slots(self) -> int | None:
        """Sum of capacities, or ``None`` when any endpoint is uncapped."""
        total = 0
        for _model, cap in self._entries:
            if cap is None:
                return None
            total += max(0, cap)
        return total

    def endpoint(self, index: int) -> Any:
        return self._entries[index][0]

    def capacity(self, index: int) -> int | None:
        return self._entries[index][1]

    def in_flight(self) -> list[int]:
        with self._cv:
            return list(self._active)

    def _pick_locked(self) -> int | None:
        best: int | None = None
        for i, (_model, cap) in enumerate(self._entries):
            if cap is not None and self._active[i] >= cap:
                continue
            if best is None or self._active[i] < self._active[best]:
                best = i
        return best

    def acquire(self, stop: threading.Event) -> int | None:
        """Block until an endpoint has room; return its index, or None if stopped."""
        with self._cv:
            while True:
                index = self._pick_locked()
                if index is not None:
                    self._active[index] += 1
                    return index
                if stop.is_set():
                    return None
                self._cv.wait(0.5)

    def release(self, index: int) -> None:
        with self._cv:
            self._active[index] = max(0, self._active[index] - 1)
            self._cv.notify()

    def reconfigure(self, entries: list[tuple[Any, int | None]]) -> list[str]:
        """Swap in new endpoints/capacities, keeping in-flight counts intact.

        Endpoints are matched by id, so raising a box's capacity or adding a new
        one does not disturb the trials already running on the others. An
        endpoint that vanishes from ``entries`` while it still has work is kept
        at capacity 0 rather than dropped — removing it outright would orphan
        the release() its in-flight trials still owe us.

        Returns one human-readable line per change, for the caller to log.
        """
        with self._cv:
            previous = {
                str(getattr(model, "id", "")): (i, cap)
                for i, (model, cap) in enumerate(self._entries)
            }
            changes: list[str] = []
            new_entries: list[tuple[Any, int | None]] = []
            new_active: list[int] = []
            seen: set[str] = set()

            for model, cap in entries:
                mid = str(getattr(model, "id", ""))
                seen.add(mid)
                prior = previous.get(mid)
                if prior is None:
                    changes.append(f"{mid}: added ({_cap_text(cap)})")
                    new_active.append(0)
                else:
                    index, old_cap = prior
                    if old_cap != cap:
                        changes.append(
                            f"{mid}: {_cap_text(old_cap)} -> {_cap_text(cap)}"
                        )
                    new_active.append(self._active[index])
                new_entries.append((model, cap))

            for mid, (index, old_cap) in previous.items():
                if mid in seen:
                    continue
                if self._active[index] > 0:
                    changes.append(
                        f"{mid}: {_cap_text(old_cap)} -> drained "
                        f"({self._active[index]} still running)"
                    )
                    new_entries.append((self._entries[index][0], 0))
                    new_active.append(self._active[index])
                else:
                    changes.append(f"{mid}: removed")

            self._entries = new_entries
            self._active = new_active
            # Capacity may have gone UP or an endpoint been added, so every
            # waiter has to re-evaluate, not just one.
            self._cv.notify_all()
            return changes


class RunScheduler:
    """Concurrency gates + stop signal for a single run.

    Acquisition order in :meth:`concurrency_gate` is per-agent first (so an
    agent-blocked trial does NOT hold a global slot), then global; release in
    reverse. All semaphores are optional — an :meth:`inactive` scheduler leaves
    them ``None`` so every gate is a pass-through.
    """

    def __init__(
        self,
        *,
        trial_cap: int = 0,
        agent_caps: dict[int, int] | None = None,
        target_setup_cap: int = 0,
        admission: HostMemoryGate | None = None,
        endpoint_pools: dict[int, EndpointPool] | None = None,
        tuning_watcher: Any | None = None,
        agent_labels: dict[int, str] | None = None,
        models_file: str = "",
    ) -> None:
        self._models_file = str(models_file or "")
        self._stop = threading.Event()
        self._admission = admission
        self._endpoint_pools: dict[int, EndpointPool] = dict(endpoint_pools or {})
        self._tuning_watcher = tuning_watcher
        self._agent_labels: dict[int, str] = dict(agent_labels or {})
        self._tuning_lock = threading.Lock()
        self._trial_cap_value = int(trial_cap or 0)
        self._agent_caps = dict(agent_caps or {})
        self._trial_sem = (
            threading.BoundedSemaphore(trial_cap) if trial_cap and trial_cap > 0 else None
        )
        self._agent_sems: dict[int, threading.BoundedSemaphore] = {
            aid: threading.BoundedSemaphore(max(1, cap))
            for aid, cap in (agent_caps or {}).items()
        }
        self._target_setup_sem = (
            threading.BoundedSemaphore(target_setup_cap)
            if target_setup_cap and target_setup_cap > 0
            else None
        )

    @classmethod
    def inactive(cls) -> "RunScheduler":
        """Return a no-op scheduler: every gate passes through, stop never set."""
        return cls()

    # -- stop signal ----------------------------------------------------------

    @property
    def stop_event(self) -> threading.Event:
        """The cooperative cancellation token (always present, never ``None``)."""
        return self._stop

    def request_stop(self) -> None:
        """Signal every thread blocked in a gate or admission wait to bail."""
        self._stop.set()

    def is_stopped(self) -> bool:
        return self._stop.is_set()

    # -- admission ------------------------------------------------------------

    @property
    def admission(self) -> HostMemoryGate:
        """The host-memory admission gate, or a null gate when inactive."""
        return self._admission or null_gate()

    # -- concurrency ----------------------------------------------------------

    def live_slot_capacity(self) -> int | None:
        """Trials this run can hold in flight right now, or None if unbounded.

        Recomputed on demand rather than cached at launch, because a tune can
        add a box or resize one — a denominator frozen at startup would keep
        showing ``running=18/20`` after the pool had grown to 52, which is
        worse than showing no denominator at all.
        """
        if not self._endpoint_pools:
            return None
        total = 0
        for agent_id, pool in self._endpoint_pools.items():
            slots = pool.total_slots
            if slots is None:
                return None
            cap = self._agent_caps.get(agent_id)
            if cap and cap != _UNLIMITED_AGENT_CAP:
                slots = min(slots, cap)
            total += slots
        if self._trial_cap_value and self._trial_cap_value > 0:
            total = min(total, self._trial_cap_value)
        return total

    def endpoint_pool(self, agent: Any) -> EndpointPool | None:
        """The endpoint pool gating ``agent``, if it has more than one source."""
        return self._endpoint_pools.get(id(agent)) if agent is not None else None

    def apply_pending_tuning(self) -> None:
        """Apply a ``cage run --tune`` edit, if one has landed since last check.

        Called immediately before a trial takes its endpoint slot — the one
        moment where changing capacity is unambiguous, because the trial about
        to start is the first one that will see it and nothing already running
        is touched. Costs one ``stat`` when nothing has changed.

        A capacity for an endpoint the pool does not have is not ignored: the
        registry is re-read from disk so a machine registered AFTER this run
        started can be brought online. That is the whole point — you rarely know
        at launch which box you will add hours later. It must pass the same
        interchangeability checks the pool was built under (one protocol, one
        upstream model); a mismatch is refused and logged rather than quietly
        skewing the run.
        """
        watcher = self._tuning_watcher
        if watcher is None:
            return
        # One thread applies; the others simply proceed with whatever is live.
        if not self._tuning_lock.acquire(blocking=False):
            return
        try:
            payload = watcher.poll()
            if not payload:
                return
            from cage.experiment.engine.live.run_tuning import source_caps_for_agent

            for agent_id, pool in self._endpoint_pools.items():
                label = self._agent_labels.get(agent_id, "")
                caps = source_caps_for_agent(payload, label)
                if caps is None:
                    continue
                known = {str(pool.endpoint(i).id) for i in range(len(pool))}
                entries = [
                    (pool.endpoint(i), caps.get(str(pool.endpoint(i).id), pool.capacity(i)))
                    for i in range(len(pool))
                ]
                for sid in caps:
                    if sid in known:
                        continue
                    admitted = self._resolve_new_endpoint(sid, pool)
                    if admitted is not None:
                        entries.append((admitted, caps[sid]))
                changes = pool.reconfigure(entries)
                for line in changes:
                    logger.info("tuning: %s %s", label, line)
        except Exception as exc:  # noqa: BLE001 - control must never kill a run
            logger.warning("tuning could not be applied: %s", exc)
        finally:
            self._tuning_lock.release()

    def _resolve_new_endpoint(self, source_id: str, pool: EndpointPool) -> Any | None:
        """Load ``source_id`` from the registry on disk, if it may join ``pool``.

        Re-reads the file rather than the snapshot taken at launch, which is
        what lets a box registered mid-run be adopted. Returns ``None`` — with a
        reason logged — when it cannot be admitted; a tune must never be able to
        kill a running experiment.
        """
        if not self._models_file:
            logger.warning(
                "tuning: cannot add endpoint %r — this run has no model "
                "registry path recorded", source_id,
            )
            return None
        try:
            from cage.models import load_models

            registry = load_models(self._models_file)
        except Exception as exc:  # noqa: BLE001 - a bad registry must not kill the run
            logger.warning(
                "tuning: cannot add endpoint %r — registry %s did not load (%s)",
                source_id, self._models_file, exc,
            )
            return None

        candidate = registry.get(source_id)
        if candidate is None:
            logger.warning(
                "tuning: endpoint %r is not registered in %s — register it "
                "first (cage model list), then tune again",
                source_id, self._models_file,
            )
            return None

        # The pool's premise is that its members are interchangeable. Since a
        # trial lands on whichever box is free, admitting a different protocol
        # or a different upstream model would make results depend on timing.
        reference = pool.endpoint(0) if len(pool) else None
        if reference is not None:
            if getattr(candidate, "protocol", None) != getattr(reference, "protocol", None):
                logger.warning(
                    "tuning: refusing endpoint %r — protocol %s does not match "
                    "the pool's %s",
                    source_id,
                    getattr(candidate, "protocol", "?"),
                    getattr(reference, "protocol", "?"),
                )
                return None
            if str(getattr(candidate, "model", "")) != str(getattr(reference, "model", "")):
                logger.warning(
                    "tuning: refusing endpoint %r — it serves %r but the pool "
                    "serves %r; a mixed pool would make results depend on timing",
                    source_id,
                    str(getattr(candidate, "model", "")),
                    str(getattr(reference, "model", "")),
                )
                return None
        logger.info(
            "tuning: adopting endpoint %s (%s) from %s",
            source_id, getattr(candidate, "base_url", "?"), self._models_file,
        )
        return candidate

    @contextlib.contextmanager
    def concurrency_gate(self, agent: Any):
        """Acquire this trial's slots; yield the endpoint it may use.

        ``agent`` is the :class:`AgentInstance` whose budget gates this trial.
        Yields the endpoint chosen by the pool, or ``None`` when the agent has
        no pool (single-endpoint runs) and the caller resolves its own model.

        Acquisition order is per-agent, then global, then endpoint. The endpoint
        slot is taken LAST and released FIRST because it is the scarcest and
        most contended resource — holding a box's slot while queueing for a
        coarser gate would idle the very capacity the pool exists to allocate.
        Every thread acquires in this same order, so the three gates cannot
        deadlock against each other.

        All gates are optional — when the scheduler is inactive this is a no-op.
        Polls the stop event so a cancelled run releases blocked waiters.
        """
        agent_sem = self._agent_sems.get(id(agent)) if agent is not None else None
        trial_sem = self._trial_sem
        pool = self.endpoint_pool(agent)

        def _acquire(sem: threading.BoundedSemaphore | None) -> bool:
            if sem is None:
                return True
            while True:
                if sem.acquire(timeout=0.5):
                    return True
                if self._stop.is_set():
                    return False

        got_agent = _acquire(agent_sem)
        if not got_agent:
            raise RuntimeError("concurrency gate cancelled (per-agent)")
        got_trial = False
        endpoint_index: int | None = None
        try:
            got_trial = _acquire(trial_sem)
            if not got_trial:
                raise RuntimeError("concurrency gate cancelled (global)")
            if pool is not None:
                # Pick up a `--tune` edit before choosing, so a box added or
                # resized seconds ago is already in play for THIS trial.
                self.apply_pending_tuning()
                endpoint_index = pool.acquire(self._stop)
                if endpoint_index is None:
                    raise RuntimeError("concurrency gate cancelled (endpoint)")
                yield pool.endpoint(endpoint_index)
            else:
                yield None
        finally:
            if endpoint_index is not None and pool is not None:
                pool.release(endpoint_index)
            if got_trial and trial_sem is not None:
                try:
                    trial_sem.release()
                except ValueError:
                    pass
            if got_agent and agent_sem is not None:
                try:
                    agent_sem.release()
                except ValueError:
                    pass

    @contextlib.contextmanager
    def target_setup_gate(self, chal_id: str, trial_id: str = ""):
        """Limit concurrent target stack launches without limiting agent testing."""
        sem = self._target_setup_sem
        if sem is None:
            yield
            return

        while True:
            if sem.acquire(timeout=0.5):
                break
            if self._stop.is_set():
                raise RuntimeError("target setup gate cancelled")

        logger.info(
            "target setup gate acquired: chal_id=%s trial_id=%s",
            chal_id,
            trial_id,
        )
        try:
            yield
        finally:
            sem.release()
            logger.info(
                "target setup gate released: chal_id=%s trial_id=%s",
                chal_id,
                trial_id,
            )
