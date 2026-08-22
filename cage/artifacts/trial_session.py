"""Canonical trial record/event/resource writer.

``TrialRuntimeSession`` centralizes the durable ``TrialRecord``, trial event,
and resource-ledger transitions for one planned trial. It is pure persistence:
it owns a run directory and one canonical trial id, then delegates every write
to the artifact, event, and resource-ledger writers in this package. It holds no
Docker, target, proxy, or agent state, so it sits at the persistence layer and
is shared by the runtime trial runner, the resource recorders, and the canonical
record helpers without any of them depending on each other.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Mapping

from cage.artifacts.reader import ExperimentArtifactReader
from cage.artifacts.writer import ExperimentArtifactWriter, ExperimentEventWriter
from cage.artifacts.resources import ResourceLedgerWriter
from cage.experiment.model import (
    ResourceRecord,
    TrialEvent,
    TrialRecord,
    TrialTermination,
)

logger = logging.getLogger(__name__)


class TrialRuntimeSession:
    """Coordinate canonical lifecycle state for one planned trial.

    The session is intentionally resource-light: it owns a run directory and one
    canonical trial id, then delegates durable writes to the artifact and event
    writers. Future runtime code can expand this class to hold target, proxy,
    verifier, and agent sessions without changing the record/event API.
    """

    def __init__(self, *, run_dir: str | Path, trial_id: str) -> None:
        """Create a session for one canonical trial in one run directory."""

        self.run_dir = Path(run_dir).expanduser().resolve()
        self.trial_id = trial_id
        # A trial's record path is fixed the moment the run is planned, so it is
        # resolved once and reused. Without this every record write and every
        # lifecycle event would rescan the run record's full trial-ref list —
        # O(trials) per call, O(trials²) per run once phase marks made those
        # calls frequent.
        self._record_ref: str | None = None

    def mark_started(
        self,
        *,
        started_at: str,
        target_id: str | None = None,
        status_reason: str = "",
    ) -> TrialRecord:
        """Mark the trial as running and append a ``trial_started`` event.

        The returned ``TrialRecord`` is the updated durable record. Callers pass
        timestamps explicitly so tests, replay, and future deterministic runtime
        paths are not tied to wall-clock calls inside this coordinator.
        """

        record = ExperimentArtifactWriter(self.run_dir).mark_trial_started(
            self.trial_id,
            started_at=started_at,
            target_id=target_id,
            status_reason=status_reason,
        )
        self.append_event(
            phase="running",
            event_type="trial_started",
            timestamp=started_at,
        )
        return record

    def mark_phase(
        self,
        *,
        phase: str,
        timestamp: str,
        payload: Mapping[str, object] | None = None,
    ) -> TrialRecord:
        """Advance this trial's phase and append a ``trial_phase`` event.

        Two durable effects, deliberately both:

        * the **record** carries the current phase, so any consumer can ask
          "what is this trial doing right now?" without replaying a log; and
        * the **event log** gains a timestamped row, so "target launch took
          eight minutes" is answerable after the fact.

        Best-effort by design. A phase mark is observability, never correctness:
        losing one must not fail the trial it describes, so persistence errors
        are logged and swallowed. The caller gets the record it would have
        written, or the unchanged current one.
        """

        try:
            record = ExperimentArtifactWriter(self.run_dir).mark_trial_phase(
                self.trial_id,
                phase=phase,
                timestamp=timestamp,
                record_ref=self._resolve_record_ref(),
            )
        except Exception as exc:  # noqa: BLE001
            logger.debug(
                "trial phase mark %s skipped for %s in %s: %s",
                phase,
                self.trial_id,
                self.run_dir,
                exc,
            )
            return self.load_record()
        try:
            self.append_event(
                phase=phase,
                event_type="trial_phase",
                timestamp=timestamp,
                payload=payload,
                # Trial-local only: ~10 of these fire per trial, and the
                # run-level timeline is shared by every trial in the run.
                run_level=False,
            )
        except Exception as exc:  # noqa: BLE001
            logger.debug(
                "trial phase event %s skipped for %s in %s: %s",
                phase,
                self.trial_id,
                self.run_dir,
                exc,
            )
        return record

    def mark_finished(
        self,
        *,
        status: str,
        completed_at: str,
        status_reason: str = "",
        termination: TrialTermination | None = None,
        payload: Mapping[str, object] | None = None,
    ) -> TrialRecord:
        """Mark the trial terminal and append a ``trial_finished`` event.

        Runtime status and scoring status remain separate. This method updates
        only the trial execution lifecycle; score refs are still written through
        scoring-specific artifact APIs.
        """

        record = ExperimentArtifactWriter(self.run_dir).mark_trial_finished(
            self.trial_id,
            status=status,
            completed_at=completed_at,
            status_reason=status_reason,
            termination=termination,
        )
        self.append_event(
            phase=record.status,
            event_type="trial_finished",
            timestamp=completed_at,
            payload=payload,
        )
        return record

    def append_event(
        self,
        *,
        phase: str,
        event_type: str,
        timestamp: str,
        payload: Mapping[str, object] | None = None,
        artifact_refs: tuple[str, ...] = (),
        resource_refs: tuple[str, ...] = (),
        error: str | None = None,
        run_level: bool = True,
    ) -> TrialEvent:
        """Append a lifecycle event to run-level and trial-local logs.

        The run-level log answers "what happened across the whole experiment?"
        The trial-local log answers "what happened inside this trial?" without
        requiring consumers to scan and filter the global timeline. Both logs
        use the same ``TrialEvent`` schema so inspect, resume, score, and debug
        tools can share parsers during the migration.

        ``run_level=False`` writes only the trial-local log. High-frequency
        per-trial events must use it: every append derives its id by counting
        the existing lines in the target log, so writing them to the run-level
        timeline — which every trial in the run shares — costs O(events) per
        append and O(events²) per run. The trial-local log stays a few dozen
        lines, where that cost is irrelevant.
        """

        record = self.load_record()
        writer = ExperimentEventWriter(self.run_dir)
        event = writer.append_trial_event(
            run_id=record.run_id,
            trial_id=record.trial_id,
            phase=phase,
            event_type=event_type,
            timestamp=timestamp,
            subject_id=record.subject_id,
            task_id=record.task_id,
            payload=payload,
            artifact_refs=artifact_refs,
            resource_refs=resource_refs,
            error=error,
            log_ref=(
                "events.jsonl" if run_level else self._trial_event_log_ref()
            ),
        )
        if not run_level:
            return event
        writer.append_trial_event(
            run_id=record.run_id,
            trial_id=record.trial_id,
            phase=phase,
            event_type=event_type,
            timestamp=timestamp,
            subject_id=record.subject_id,
            task_id=record.task_id,
            payload=payload,
            artifact_refs=artifact_refs,
            resource_refs=resource_refs,
            error=error,
            log_ref=self._trial_event_log_ref(),
        )
        return event

    def record_resource(
        self,
        *,
        run_id: str,
        resource_id: str,
        kind: str,
        provider: str,
        external_id: str,
        status: str,
        cleanup_action: str,
        timestamp: str,
        metadata: Mapping[str, object] | None = None,
        cleanup_error: str | None = None,
    ) -> ResourceRecord:
        """Append a cleanup-ledger entry for a resource owned by this trial.

        Runtime code should call this when a container, network, proxy process,
        target stack, or verifier sidecar changes cleanup state. The session
        supplies the canonical ``trial_id`` so resource records stay linked to
        ``TrialRecord`` instead of legacy scheduler ids.

        A matching lifecycle event is appended after the ledger row so the
        event stream can tell a coherent story without reparsing
        ``resources.jsonl``. The event is best-effort: historical or partial
        runs may have a resource ledger before a readable ``TrialRecord``
        exists, and losing the event must not discard the cleanup record.
        """

        record = ResourceLedgerWriter(self.run_dir).append_resource(
            run_id=run_id,
            trial_id=self.trial_id,
            resource_id=resource_id,
            kind=kind,
            provider=provider,
            external_id=external_id,
            status=status,
            cleanup_action=cleanup_action,
            timestamp=timestamp,
            metadata=metadata,
            cleanup_error=cleanup_error,
        )
        ExperimentArtifactWriter(self.run_dir).refresh_trial_resource_projection(
            self.trial_id
        )
        self._append_resource_event(record)
        return record

    def load_record(self) -> TrialRecord:
        """Load this session's current canonical trial record."""

        record, _record_ref = self._load_record_and_ref()
        return record

    def _trial_event_log_ref(self) -> str:
        """Return the run-relative trial-local lifecycle event log path."""

        _record, record_ref = self._load_record_and_ref()
        return (Path(record_ref).parent / "events.jsonl").as_posix()

    def _load_record_and_ref(self) -> tuple[TrialRecord, str]:
        """Load the current trial record and its run-relative record ref."""

        record_ref = self._resolve_record_ref()
        record = ExperimentArtifactReader(self.run_dir).load_trial_record(record_ref)
        return record, record_ref

    def _resolve_record_ref(self) -> str:
        """Return this trial's run-relative record ref, resolving it once."""

        if self._record_ref is not None:
            return self._record_ref
        run_record = ExperimentArtifactReader(self.run_dir).load_record()
        for trial_ref in run_record.trials.records:
            if trial_ref.trial_id == self.trial_id:
                self._record_ref = trial_ref.record_ref
                return trial_ref.record_ref
        raise KeyError(f"unknown trial_id: {self.trial_id}")

    def _append_resource_event(self, record: ResourceRecord) -> None:
        """Append the lifecycle event corresponding to one resource ledger row."""

        status = _event_token(record.status)
        event_type = f"resource_{status}" if status else "resource_recorded"
        phase = f"resource:{status}" if status else "resource"
        try:
            self.append_event(
                phase=phase,
                event_type=event_type,
                timestamp=record.timestamp,
                payload={
                    "cleanup_action": record.cleanup_action,
                    "external_id": record.external_id,
                    "kind": record.kind,
                    "provider": record.provider,
                    "resource_id": record.resource_id,
                    "status": record.status,
                },
                resource_refs=(record.record_id,),
                error=record.cleanup_error,
            )
        except Exception as exc:  # noqa: BLE001
            logger.debug(
                "resource lifecycle event skipped for %s in %s: %s",
                record.resource_id,
                self.run_dir,
                exc,
            )


def _event_token(value: object) -> str:
    """Normalize a status string into a compact event-token component."""

    chars = [
        ch.lower() if ch.isalnum() else "_"
        for ch in str(value or "").strip()
    ]
    return "_".join(part for part in "".join(chars).split("_") if part)
