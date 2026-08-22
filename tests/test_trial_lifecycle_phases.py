"""Tests for the trial phase axis, the run heartbeat, and failure attribution.

These three cover one gap: the framework used to record *that* a trial was
running and *that* it later failed, but nothing about where it was in between —
so liveness had to be guessed from file mtimes, and every exception collapsed
into a single ``trial_error``.

Coverage:

  * ``TrialPhase`` vocabulary + ``TrialRecord`` phase round-trip, including
    legacy records written before the field existed.
  * ``ExperimentArtifactWriter.mark_trial_phase`` — advances, and refuses to
    resurrect a terminal record.
  * ``RunHeartbeat`` / ``run_process_is_alive`` — the tri-state contract that
    lets a quiet-but-healthy run stop reading as "Stopped".
  * ``termination_info_from_exception`` — typed exceptions and, for the untyped
    majority, phase-based attribution.
"""
from __future__ import annotations

import json
import os
import socket
import time
from pathlib import Path

import pytest

from cage.artifacts.records import _trial_record_from_mapping
from cage.artifacts.writer import ExperimentArtifactWriter
from cage.contracts.exceptions import (
    AgentSetupError,
    BenchmarkError,
    ConfigError,
    ContainerError,
    ScoringError,
    TargetError,
)
from cage.contracts.trial_phase import (
    ACTIVE_PHASES,
    TrialPhase,
    is_active_phase,
    phase_label,
)
from cage.experiment.engine.live.run_heartbeat import (
    RunHeartbeat,
    process_is_alive,
    read_run_process_status,
    run_process_is_alive,
    runtime_status_path,
)
from cage.experiment.engine.termination import (
    TerminationReason,
    TerminationSource,
    classify_trial_termination,
    termination_info_from_exception,
)
from cage.experiment.model import build_experiment_plan, load_experiment_spec
from cage.experiment.model.record import TrialRecord, trial_record_to_json
from cage.web.data import _classify_trial_status, build_trial_error_report


# ---------------------------------------------------------------------------
# phase vocabulary
# ---------------------------------------------------------------------------


def test_bookend_phases_are_not_active_and_everything_between_is():
    """Only ``planned`` and ``finished`` mean "no work in flight"."""
    assert not is_active_phase(TrialPhase.PLANNED)
    assert not is_active_phase(TrialPhase.FINISHED)
    for phase in TrialPhase:
        if phase in {TrialPhase.PLANNED, TrialPhase.FINISHED}:
            continue
        assert is_active_phase(phase), phase
    assert TrialPhase.PLANNED.value not in ACTIVE_PHASES
    assert TrialPhase.RUNNING_AGENT.value in ACTIVE_PHASES


def test_unknown_phase_is_humanized_rather_than_dropped():
    """A phase this build does not know must still render as something."""
    assert phase_label(TrialPhase.LAUNCHING_TARGET) == "Launching target"
    assert phase_label("some_future_stage") == "Some future stage"
    assert phase_label(None) == ""


# ---------------------------------------------------------------------------
# TrialRecord serialization
# ---------------------------------------------------------------------------


def _record(**overrides) -> TrialRecord:
    base = dict(
        schema_version="trial_record.v1",
        trial_id="t1",
        run_id="r1",
        plan_ref="plan.json",
        status="running",
        status_reason="",
        subject_id="agent:model:stateless",
        task_id="task1",
        pass_index=0,
    )
    base.update(overrides)
    return TrialRecord(**base)


def test_trial_record_round_trips_phase():
    record = _record(phase=TrialPhase.LAUNCHING_TARGET.value, phase_updated_at="2026-01-01T00:00:00")
    restored = _trial_record_from_mapping(json.loads(trial_record_to_json(record)))
    assert restored == record


def test_legacy_record_without_phase_derives_bookend_from_status():
    """Pre-phase records must not read as "never started" once finished."""
    payload = json.loads(trial_record_to_json(_record(status="completed")))
    payload.pop("phase", None)
    payload.pop("phase_updated_at", None)
    assert _trial_record_from_mapping(payload).phase == TrialPhase.FINISHED.value

    payload["status"] = "planned"
    assert _trial_record_from_mapping(payload).phase == TrialPhase.PLANNED.value


# ---------------------------------------------------------------------------
# writer.mark_trial_phase
# ---------------------------------------------------------------------------


@pytest.fixture()
def planned_run(tmp_path: Path) -> tuple[Path, str]:
    """A run dir with one planned trial's canonical record on disk."""
    project_file = tmp_path / "project.yml"
    project_file.write_text(
        """
project:
  name: phase-demo
eval:
  benchmark:
    module: ./benchmark.py
    class: DemoBenchmark
runtime:
  max_rounds: 2
agents:
  - id: agent
    kind: codex
    model: model
""".lstrip(),
        encoding="utf-8",
    )
    spec = load_experiment_spec(project_file, sample_ids=("task1",))
    plan = build_experiment_plan(spec)
    run_dir = tmp_path / "run1"
    writer = ExperimentArtifactWriter(run_dir)
    writer.write_initial_snapshot(
        spec=spec, plan=plan, run_id="run1", created_at="2026-01-01T00:00:00",
    )
    trial_id = plan.trials[0].trial_id
    return run_dir, trial_id


def test_mark_trial_started_seeds_the_phase_axis(planned_run):
    run_dir, trial_id = planned_run
    record = ExperimentArtifactWriter(run_dir).mark_trial_started(
        trial_id, started_at="2026-01-01T00:00:00",
    )
    assert record.status == "running"
    assert record.phase == TrialPhase.STARTING_CONTAINER.value
    assert record.phase_updated_at == "2026-01-01T00:00:00"


def test_mark_trial_phase_advances_and_persists(planned_run):
    run_dir, trial_id = planned_run
    writer = ExperimentArtifactWriter(run_dir)
    writer.mark_trial_started(trial_id, started_at="2026-01-01T00:00:00")
    writer.mark_trial_phase(
        trial_id, phase=TrialPhase.RUNNING_AGENT.value, timestamp="2026-01-01T00:05:00",
    )
    # Re-read from disk: the point is durability, not the returned object.
    reread = ExperimentArtifactWriter(run_dir)._load_trial_record(
        reread_ref := ExperimentArtifactWriter(run_dir)._trial_record_ref(trial_id)
    )
    assert reread_ref
    assert reread.phase == TrialPhase.RUNNING_AGENT.value
    assert reread.phase_updated_at == "2026-01-01T00:05:00"
    assert reread.status == "running"  # phase is a separate axis from status


def test_mark_trial_phase_refuses_to_resurrect_a_finished_trial(planned_run):
    """A teardown-path phase mark must not undo a terminal status."""
    run_dir, trial_id = planned_run
    writer = ExperimentArtifactWriter(run_dir)
    writer.mark_trial_started(trial_id, started_at="2026-01-01T00:00:00")
    writer.mark_trial_finished(
        trial_id, status="completed", completed_at="2026-01-01T01:00:00",
    )
    writer.mark_trial_phase(
        trial_id, phase=TrialPhase.TEARING_DOWN.value, timestamp="2026-01-01T01:00:01",
    )
    record = writer._load_trial_record(writer._trial_record_ref(trial_id))
    assert record.status == "completed"
    assert record.phase == TrialPhase.FINISHED.value


# ---------------------------------------------------------------------------
# run heartbeat
# ---------------------------------------------------------------------------


def test_missing_status_file_is_unknown_not_dead(tmp_path):
    """``None`` is load-bearing: pre-heartbeat runs must fall back, not die."""
    assert run_process_is_alive(tmp_path / "nope") is None
    assert read_run_process_status(tmp_path / "nope") is None


def test_heartbeat_reports_live_then_clears_on_stop(tmp_path):
    run_dir = tmp_path / "run1"
    heartbeat = RunHeartbeat(interval_s=0.05)
    heartbeat.track(run_dir)
    heartbeat.start()
    try:
        assert run_process_is_alive(run_dir) is True
        status = read_run_process_status(run_dir)
        assert status is not None
        assert status.pid == os.getpid()
        assert status.is_local

        first = runtime_status_path(run_dir).stat().st_mtime_ns
        deadline = time.time() + 2.0
        while time.time() < deadline:
            if runtime_status_path(run_dir).stat().st_mtime_ns > first:
                break
            time.sleep(0.05)
        else:  # pragma: no cover - only on a pathologically slow machine
            pytest.fail("heartbeat never refreshed the status file")
    finally:
        heartbeat.stop()

    assert not runtime_status_path(run_dir).exists()
    assert run_process_is_alive(run_dir) is None


def test_stale_pid_from_a_crashed_run_reads_as_dead(tmp_path):
    """A crash leaves the file behind; the pid is what resolves it."""
    run_dir = tmp_path / "run1"
    run_dir.mkdir(parents=True)
    runtime_status_path(run_dir).write_text(
        json.dumps({
            "pid": 2**22,  # above the default pid_max; cannot be a live process
            "hostname": socket.gethostname(),
            "heartbeat_at_ms": int(time.time() * 1000),
        }),
        encoding="utf-8",
    )
    assert run_process_is_alive(run_dir) is False


def test_remote_host_falls_back_to_heartbeat_freshness(tmp_path):
    """A pid from another host is meaningless — only the timestamp counts."""
    run_dir = tmp_path / "run1"
    run_dir.mkdir(parents=True)

    def _write(age_s: float) -> None:
        runtime_status_path(run_dir).write_text(
            json.dumps({
                "pid": os.getpid(),
                "hostname": "some-other-host",
                "heartbeat_at_ms": int((time.time() - age_s) * 1000),
            }),
            encoding="utf-8",
        )

    _write(age_s=1.0)
    assert run_process_is_alive(run_dir) is True
    _write(age_s=600.0)
    assert run_process_is_alive(run_dir) is False


def test_process_is_alive_rejects_nonsense_pids():
    assert process_is_alive(0) is False
    assert process_is_alive(-1) is False
    assert process_is_alive(os.getpid()) is True


# ---------------------------------------------------------------------------
# TrialPhaseTracker
# ---------------------------------------------------------------------------


def _tracker(planned_run):
    from types import SimpleNamespace

    from cage.artifacts.run_storage import RunStorage
    from cage.experiment.engine.trial_phase_tracker import TrialPhaseTracker
    from cage.experiment.model import Trial, TrialType

    run_dir, trial_id = planned_run
    storage = RunStorage(run_dir, agent_label="a:m:stateless")
    trial = Trial(id=trial_id, index=0, type=TrialType.TASK, sample={"id": trial_id})
    agent = SimpleNamespace(label=lambda: "a:m:stateless")
    return TrialPhaseTracker(storage=storage, agent=agent, trial=trial), run_dir, trial_id


def _phase_events(run_dir: Path) -> list[str]:
    logs = list(run_dir.glob("trials/**/events.jsonl"))
    if not logs:
        return []
    return [
        json.loads(line)["phase"]
        for line in logs[0].read_text().splitlines()
        if line.strip() and json.loads(line)["type"] == "trial_phase"
    ]


def test_tracker_ignores_re_entering_the_same_phase(planned_run):
    """Target launch and teardown are marked from two functions each.

    ``run_trial_isolated`` and ``execute_trial`` both own part of the target
    lifecycle and both have a ``finally``, so each of those phases was marked
    twice — a duplicated timeline entry and a wasted record write per trial.
    """
    tracker, run_dir, trial_id = _tracker(planned_run)
    ExperimentArtifactWriter(run_dir).mark_trial_started(
        trial_id, started_at="2026-01-01T00:00:00",
    )
    tracker.enter(TrialPhase.LAUNCHING_TARGET)
    tracker.enter(TrialPhase.LAUNCHING_TARGET)
    tracker.enter(TrialPhase.RUNNING_AGENT)
    tracker.enter(TrialPhase.TEARING_DOWN)
    tracker.enter(TrialPhase.TEARING_DOWN)

    assert _phase_events(run_dir) == [
        TrialPhase.LAUNCHING_TARGET.value,
        TrialPhase.RUNNING_AGENT.value,
        TrialPhase.TEARING_DOWN.value,
    ]
    assert tracker.current == TrialPhase.TEARING_DOWN.value


def test_tracker_tracks_in_memory_even_without_a_canonical_record(tmp_path):
    """``failed_phase`` must survive a run with no record to publish to."""
    from types import SimpleNamespace

    from cage.artifacts.run_storage import RunStorage
    from cage.experiment.engine.trial_phase_tracker import TrialPhaseTracker
    from cage.experiment.model import Trial, TrialType

    storage = RunStorage(tmp_path / "bare", agent_label="a:m:stateless")
    trial = Trial(id="t1", index=0, type=TrialType.TASK, sample={"id": "t1"})
    tracker = TrialPhaseTracker(
        storage=storage, agent=SimpleNamespace(label=lambda: "a:m:stateless"), trial=trial,
    )
    tracker.enter(TrialPhase.STARTING_PROXY)
    assert tracker.current == TrialPhase.STARTING_PROXY.value


# ---------------------------------------------------------------------------
# how the phase reaches the UI
# ---------------------------------------------------------------------------


def _running_chip(phase: str | None) -> dict[str, str]:
    info: dict[str, object] = {"running": True}
    if phase is not None:
        info["phase"] = phase
    return _classify_trial_status(Path("/nonexistent"), info)


def test_running_chip_names_the_active_phase():
    """The whole point: "Running" alone says nothing for minutes at a time."""
    chip = _running_chip(TrialPhase.LAUNCHING_TARGET.value)
    assert chip["status_label"] == "Running · Launching target"
    assert chip["status_detail"] == "Launching target"
    assert chip["status_kind"] == "running"


def test_running_chip_stays_plain_for_bookend_or_missing_phase():
    """A pre-phase record reads back as ``planned``; "Running · Planned" is worse."""
    assert _running_chip(TrialPhase.PLANNED.value)["status_label"] == "Running"
    assert _running_chip(None)["status_label"] == "Running"


def test_running_agent_phase_still_prefers_the_proxy_status():
    """During the agent run the last upstream status is the more specific detail."""
    info = {
        "running": True,
        "phase": TrialPhase.RUNNING_AGENT.value,
        "progress": {"last_status": 200},
    }
    chip = _classify_trial_status(Path("/nonexistent"), info)
    assert chip["status_label"] == "Running · Running agent"
    assert chip["status_detail"] == "Last proxy status: 200"


# ---------------------------------------------------------------------------
# failure attribution
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "exc, expected_reason",
    [
        (ContainerError("c1", "docker daemon busy"), TerminationReason.CONTAINER_ERROR),
        (ConfigError("unknown model"), TerminationReason.CONFIG_ERROR),
        (AgentSetupError("no credentials"), TerminationReason.AGENT_SETUP_ERROR),
        (TargetError("service died"), TerminationReason.TARGET_ERROR),
        (BenchmarkError("prepare_trial raised"), TerminationReason.BENCHMARK_ERROR),
        (ScoringError("scorer raised"), TerminationReason.SCORING_ERROR),
    ],
)
def test_typed_exceptions_get_their_own_reason(exc, expected_reason):
    assert termination_info_from_exception(exc).reason is expected_reason


@pytest.mark.parametrize(
    "phase, expected_reason",
    [
        (TrialPhase.STARTING_CONTAINER, TerminationReason.CONTAINER_ERROR),
        (TrialPhase.SETTING_UP_CONTAINER, TerminationReason.CONTAINER_ERROR),
        (TrialPhase.SETTING_UP_AGENT, TerminationReason.AGENT_SETUP_ERROR),
        (TrialPhase.LAUNCHING_TARGET, TerminationReason.TARGET_UNAVAILABLE),
        (TrialPhase.PREPARING_WORKSPACE, TerminationReason.BENCHMARK_ERROR),
        (TrialPhase.BUILDING_PROMPT, TerminationReason.BENCHMARK_ERROR),
        (TrialPhase.STARTING_PROXY, TerminationReason.PROXY_ERROR),
        (TrialPhase.SCORING, TerminationReason.SCORING_ERROR),
    ],
)
def test_untyped_exception_is_attributed_by_phase(phase, expected_reason):
    """The ~160 bare RuntimeErrors in the framework classify by where they fired."""
    info = termination_info_from_exception(RuntimeError("boom"), failed_phase=phase.value)
    assert info.reason is expected_reason


def test_untyped_exception_without_a_phase_stays_generic():
    """No phase, no typed exception — honestly unclassified."""
    info = termination_info_from_exception(RuntimeError("boom"))
    assert info.reason is TerminationReason.TRIAL_ERROR
    info = termination_info_from_exception(RuntimeError("boom"), failed_phase="running_agent")
    assert info.reason is TerminationReason.TRIAL_ERROR


def test_typed_exception_outranks_phase_inference():
    """A raise site that named its cause must not be second-guessed."""
    info = termination_info_from_exception(
        ContainerError("c1", "no such container"),
        failed_phase=TrialPhase.SCORING.value,
    )
    assert info.reason is TerminationReason.CONTAINER_ERROR


def test_error_string_path_classifies_from_recorded_type_and_phase():
    """meta.json rows keep only strings; both signals must still work."""
    by_type = classify_trial_termination(
        exit_code=-1, timed_out=False, terminated_by_limit=False,
        error="kaboom", error_type="ContainerError",
    )
    assert by_type.reason is TerminationReason.CONTAINER_ERROR

    by_phase = classify_trial_termination(
        exit_code=-1, timed_out=False, terminated_by_limit=False,
        error="kaboom", failed_phase=TrialPhase.LAUNCHING_TARGET.value,
    )
    assert by_phase.reason is TerminationReason.TARGET_UNAVAILABLE

    generic = classify_trial_termination(
        exit_code=-1, timed_out=False, terminated_by_limit=False, error="kaboom",
    )
    assert generic.reason is TerminationReason.TRIAL_ERROR


def test_agent_phase_failure_is_attributed_to_the_upstream_error(tmp_path):
    """A crash during the agent run whose last LLM call 401'd is an auth failure.

    This is the case the old classifier could never reach: ``if error:`` returned
    ``trial_error`` before the proxy log was ever consulted, hiding the one
    detail that says whether re-running would help.
    """
    proxy_log = tmp_path / "proxy.jsonl"
    proxy_log.write_text(
        json.dumps({
            "status": "error",
            "upstream_status_code": 401,
            "error_text": 'HTTP 401: {"error":{"type":"authentication_error",'
                          '"message":"invalid api key"}}',
        }) + "\n",
        encoding="utf-8",
    )
    info = classify_trial_termination(
        exit_code=-1,
        timed_out=False,
        terminated_by_limit=False,
        error="agent process died",
        failed_phase=TrialPhase.RUNNING_AGENT.value,
        proxy_jsonl_path=proxy_log,
    )
    assert info.reason is TerminationReason.MODEL_AUTH_ERROR
    assert info.source is TerminationSource.MODEL_PROXY


def test_failed_trial_persists_a_readable_post_mortem(tmp_path):
    """The traceback must land in a trial artifact, not only the hidden run log.

    Before this, ``_trial_failure_result`` stored ``str(exc)`` and nothing else;
    the traceback went to ``<run_dir>/.cage.runlog`` which the inspector never
    rendered, so a failed trial showed one truncated line and no way to reach
    the cause.
    """
    from types import SimpleNamespace

    from cage.artifacts.run_storage import RunStorage
    from cage.experiment.engine.trial_runner import _trial_failure_result
    from cage.experiment.model import Trial, TrialType
    from cage.web.data import build_trial_error_report

    storage = RunStorage(tmp_path / "run1", agent_label="a:m:stateless")
    trial = Trial(id="t1", index=0, type=TrialType.TASK, sample={"id": "t1"})
    run = SimpleNamespace(execution=SimpleNamespace(timeout=0))

    try:
        raise ContainerError("cage-t1", "no such container")
    except ContainerError as exc:
        result = _trial_failure_result(
            exc=exc, run=run, started=0, storage=storage, trial=trial,
            trial_id="t1", failed_phase=TrialPhase.LAUNCHING_TARGET.value,
        )

    assert result.metadata["error_type"] == "ContainerError"
    assert result.metadata["failed_phase"] == TrialPhase.LAUNCHING_TARGET.value
    # Typed exception outranks the phase, so this is container_error rather than
    # the target_unavailable the phase alone would imply.
    assert result.metadata["termination_reason"] == "container_error"

    report = build_trial_error_report(storage.trial_dir("t1"))
    assert report is not None
    assert report["error_type"] == "ContainerError"
    assert report["phase_label"] == "Launching target"
    assert "ContainerError" in report["traceback"]
    assert "test_failed_trial_persists_a_readable_post_mortem" in report["traceback"]


def test_trial_error_report_absent_for_trials_that_did_not_raise(tmp_path):
    """No report is the signal "this did not fail through the exception path"."""
    trial_dir = tmp_path / "trials" / "t1"
    trial_dir.mkdir(parents=True)
    assert build_trial_error_report(trial_dir) is None


def test_non_agent_phase_ignores_a_stale_upstream_error(tmp_path):
    """An upstream error left over from a finished agent run is not the cause."""
    proxy_log = tmp_path / "proxy.jsonl"
    proxy_log.write_text(
        json.dumps({
            "status": "error",
            "upstream_status_code": 401,
            "error_text": 'HTTP 401: {"error":{"type":"authentication_error",'
                          '"message":"invalid api key"}}',
        }) + "\n",
        encoding="utf-8",
    )
    info = classify_trial_termination(
        exit_code=-1,
        timed_out=False,
        terminated_by_limit=False,
        error="scorer blew up",
        failed_phase=TrialPhase.SCORING.value,
        proxy_jsonl_path=proxy_log,
    )
    assert info.reason is TerminationReason.SCORING_ERROR


def test_every_taxonomy_reason_is_reachable():
    """No declared-but-unwritable categories.

    ``agent_setup_error`` shipped in the taxonomy with nothing able to produce
    it: agent preparation ran inside the container-setup phase, so credential
    and CLI-install failures were all attributed to the container. That is the
    same defect as a state machine whose states are never written — the
    vocabulary looks richer than the behaviour. This asserts each newly added
    reason has at least one route that yields it.
    """
    from cage.contracts.exceptions import (
        AgentSetupError, BenchmarkError, ConfigError, ContainerError,
        ProxyError, ScoringError, TargetError,
    )

    reachable = {
        termination_info_from_exception(exc).reason
        for exc in (
            ContainerError("c", "x"), ProxyError("x"), AgentSetupError("x"),
            TargetError("x"), BenchmarkError("x"), ScoringError("x"), ConfigError("x"),
        )
    }
    reachable |= {
        termination_info_from_exception(RuntimeError("x"), failed_phase=phase).reason
        for phase in ACTIVE_PHASES
    }
    for reason in (
        TerminationReason.CONTAINER_ERROR,
        TerminationReason.PROXY_ERROR,
        TerminationReason.AGENT_SETUP_ERROR,
        TerminationReason.TARGET_ERROR,
        TerminationReason.BENCHMARK_ERROR,
        TerminationReason.SCORING_ERROR,
        TerminationReason.CONFIG_ERROR,
    ):
        assert reason in reachable, f"{reason.value} is declared but unreachable"


# ---------------------------------------------------------------------------
# status vocabulary coherence
# ---------------------------------------------------------------------------


def test_the_three_status_vocabularies_agree():
    """`TrialStatus`, `TerminationStatus` and the contract sets are one vocabulary.

    Three files describe the same statuses: the runtime enum, the terminal enum
    the classifier writes, and the frozensets every consumer keys off. Nothing
    linked them, so a value added to one could silently produce a status the
    others do not recognise.
    """
    from cage.contracts.trial_status import TERMINAL_TRIAL_STATUSES
    from cage.experiment.engine.termination_model import TerminationStatus
    from cage.experiment.model.trial import TrialStatus

    termination = {member.value for member in TerminationStatus}
    runtime = {member.value for member in TrialStatus}

    assert termination == TERMINAL_TRIAL_STATUSES
    assert termination < runtime                      # strict terminal subset
    assert runtime - termination == {"pending", "running"}


def test_scoring_states_are_not_writable_as_a_runtime_status():
    """The two axes must not blur again.

    Scoring lives in ``TrialRecord.scoring.status``. Older runs put it in the
    runtime status, so readers still tolerate it — but a *new* write of
    ``status="scored"`` has to fail, or the separation is only a convention.
    """
    from cage.artifacts.records import _terminal_trial_status
    from cage.contracts.trial_status import (
        LEGACY_SCORING_TRIAL_STATUSES,
        TERMINAL_TRIAL_STATUSES,
        TERMINAL_TRIAL_STATUSES_ON_READ,
    )

    assert not (TERMINAL_TRIAL_STATUSES & LEGACY_SCORING_TRIAL_STATUSES)
    assert LEGACY_SCORING_TRIAL_STATUSES < TERMINAL_TRIAL_STATUSES_ON_READ

    for legacy in sorted(LEGACY_SCORING_TRIAL_STATUSES):
        with pytest.raises(ValueError, match="trial status must be one of"):
            _terminal_trial_status(legacy)
    assert _terminal_trial_status("completed") == "completed"


def test_legacy_runs_recording_scored_still_classify_as_completed():
    """Read tolerance is the point of the split — history must not re-bucket."""
    from cage.contracts.trial_status import classify_trial_status, count_trials

    assert classify_trial_status(status="scored") == "completed"
    assert classify_trial_status(status="not_scored") == "completed"

    counts = count_trials([
        {"status": "scored"}, {"status": "not_scored"},
        {"status": "completed"}, {"status": "failed"},
    ])
    assert (counts.completed, counts.failed, counts.running) == (3, 1, 0)


def test_legacy_scored_record_reads_back_as_finished_not_planned():
    """The phase bookend derivation must use the same tolerance."""
    payload = json.loads(trial_record_to_json(_record(status="completed")))
    payload.pop("phase", None)
    payload["status"] = "scored"
    assert _trial_record_from_mapping(payload).phase == TrialPhase.FINISHED.value
