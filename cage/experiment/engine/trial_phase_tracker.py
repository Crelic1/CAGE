"""Runtime phase tracking for one in-flight trial.

The trial runner walks a fixed sequence of stages — gates, container, target,
workspace, proxy, agent, evidence, snapshot, scoring, teardown. Until this
existed, none of that was durable: the canonical record flipped to ``running``
at the start and to a terminal status at the end, with a multi-minute (often
multi-hour) blind spot in between.

:class:`TrialPhaseTracker` closes it. It owns two responsibilities that must
stay together:

* **Publish** each transition to the canonical ``TrialRecord`` (and the trial
  event log), so "what is this trial doing?" is answerable from disk.
* **Remember** the current phase in memory, so the runner's exception handlers
  can stamp ``failed_phase`` on a crash. An exception knows its message but not
  the stage it escaped from; that stage is usually the more useful half of the
  diagnosis.

Every write is best-effort. Phase tracking is observability: a trial must never
fail because its progress could not be recorded.
"""

from __future__ import annotations

import logging
import time
from typing import TYPE_CHECKING

from cage.artifacts.canonical_marks import plan_trial_id
from cage.artifacts.trial_session import TrialRuntimeSession
from cage.contracts.trial_phase import TrialPhase

if TYPE_CHECKING:  # pragma: no cover - typing only
    from cage.agents.base.instance import AgentInstance
    from cage.artifacts.run_storage import RunStorage
    from cage.experiment.model.trial import Trial

logger = logging.getLogger(__name__)


def _now() -> str:
    """Wall-clock stamp in the format the canonical records already use."""

    return time.strftime("%Y-%m-%dT%H:%M:%S")


class TrialPhaseTracker:
    """Track and persist the lifecycle phase of a single trial.

    Construct one per trial and call :meth:`enter` as the runner crosses each
    stage boundary. Read :attr:`current` from an exception handler to learn
    where the trial was when it died.
    """

    def __init__(
        self,
        *,
        storage: "RunStorage",
        agent: "AgentInstance",
        trial: "Trial",
    ) -> None:
        """Create a tracker bound to one planned trial's canonical record."""

        self._storage = storage
        self._trial = trial
        self._current = TrialPhase.PLANNED.value
        try:
            self._session: TrialRuntimeSession | None = TrialRuntimeSession(
                run_dir=storage.run_dir,
                trial_id=plan_trial_id(agent, trial),
            )
        except Exception as exc:  # noqa: BLE001
            # Legacy or partially-planned runs may have no canonical record to
            # bind to. In-memory tracking still works (so ``failed_phase`` is
            # still recorded on meta.json); only the durable publish is lost.
            logger.debug("phase tracking is memory-only for %s: %s", trial.id, exc)
            self._session = None

    @property
    def current(self) -> str:
        """The phase this trial most recently entered."""

        return self._current

    def enter(self, phase: TrialPhase | str) -> None:
        """Record entry into ``phase`` in memory and on disk.

        Re-entering the phase already current is a no-op. Two stages are marked
        from both ``run_trial_isolated`` and ``execute_trial`` — target launch,
        because either function may own it depending on the concurrency path,
        and teardown, because both have a ``finally``. Without this the timeline
        showed each of them twice and paid for a duplicate record write.

        Never raises. The in-memory update happens first and unconditionally, so
        a failed durable write still leaves ``failed_phase`` accurate.
        """

        value = phase.value if isinstance(phase, TrialPhase) else str(phase)
        if value == self._current:
            return
        self._current = value
        if self._session is None:
            return
        try:
            self._session.mark_phase(phase=value, timestamp=_now())
        except Exception as exc:  # noqa: BLE001
            logger.debug("phase mark %s skipped for %s: %s", value, self._trial.id, exc)


__all__ = ["TrialPhaseTracker"]
