"""Per-endpoint concurrency: taking a slot IS choosing the endpoint.

A multi-source agent used to pick its endpoint by ``trial_index % n`` and gate
concurrency separately, so a 4-slot box and a 32-slot box received the same
share of trials. These tests pin the behaviour that replaced it.
"""

from __future__ import annotations

import threading
from collections import Counter
from dataclasses import dataclass

import pytest

from cage.cli.ui.progress_reporter import _live_slot_capacity
from cage.cli.ui.run import RunAgentContract, RunContract, _format_endpoints
from cage.config.experiment import _agent_model_entries, _parse_source_entry
from cage.experiment.engine.scheduler import EndpointPool, RunScheduler


@dataclass
class _Endpoint:
    id: str


def _pool(*entries: tuple[str, int | None]) -> EndpointPool:
    return EndpointPool([(_Endpoint(name), cap) for name, cap in entries])


class TestEndpointPool:
    def test_capacity_decides_share_not_position(self) -> None:
        pool = _pool(("big", 16), ("small", 4))
        stop = threading.Event()
        taken = Counter(pool.endpoint(pool.acquire(stop)).id for _ in range(20))
        # round-robin would have given these 10 each
        assert taken["small"] == 4
        assert taken["big"] == 16

    def test_uncapped_endpoint_never_blocks_but_stays_balanced(self) -> None:
        pool = _pool(("capped", 2), ("free", None))
        stop = threading.Event()
        taken = Counter(pool.endpoint(pool.acquire(stop)).id for _ in range(10))
        assert taken["capped"] == 2
        assert taken["free"] == 8
        assert pool.total_slots is None  # unbounded ⇒ no honest total

    def test_zero_capacity_drains_without_interrupting(self) -> None:
        # An endpoint set to 0 must stop receiving work while whatever is
        # already on it keeps running — that is how a box is retired mid-run.
        pool = _pool(("live", 4), ("draining", 0))
        stop = threading.Event()
        taken = {pool.endpoint(pool.acquire(stop)).id for _ in range(4)}
        assert taken == {"live"}

    def test_blocks_when_full_and_resumes_on_release(self) -> None:
        pool = _pool(("only", 1))
        stop = threading.Event()
        held = pool.acquire(stop)
        got: list[int | None] = []
        waiter = threading.Thread(target=lambda: got.append(pool.acquire(stop)), daemon=True)
        waiter.start()
        waiter.join(0.8)
        assert waiter.is_alive() and not got, "a full pool must block"
        pool.release(held)
        waiter.join(3.0)
        assert not waiter.is_alive() and got == [0]

    def test_cancellation_releases_a_blocked_waiter(self) -> None:
        # Without this a Ctrl+C on a saturated pool would hang the run.
        pool = _pool(("only", 1))
        stop = threading.Event()
        pool.acquire(stop)
        got: list[int | None] = []
        waiter = threading.Thread(target=lambda: got.append(pool.acquire(stop)), daemon=True)
        waiter.start()
        waiter.join(0.3)
        stop.set()
        waiter.join(3.0)
        assert not waiter.is_alive() and got == [None]

    def test_total_slots_sums_declared_capacity(self) -> None:
        assert _pool(("a", 16), ("b", 4), ("c", 32)).total_slots == 52
        assert _pool(("a", 16), ("b", 0)).total_slots == 16


class TestSchedulerGate:
    def test_gate_yields_the_endpoint_it_reserved(self) -> None:
        agent = object()
        pool = _pool(("box1", 1))
        sched = RunScheduler(endpoint_pools={id(agent): pool})
        with sched.concurrency_gate(agent) as endpoint:
            assert endpoint is not None and endpoint.id == "box1"
            assert pool.in_flight() == [1]
        assert pool.in_flight() == [0], "leaving the gate must free the slot"

    def test_gate_yields_none_without_a_pool(self) -> None:
        # Single-endpoint agents keep the old behaviour: the caller resolves
        # its own model positionally.
        sched = RunScheduler()
        with sched.concurrency_gate(object()) as endpoint:
            assert endpoint is None

    def test_slot_is_released_even_when_the_trial_raises(self) -> None:
        agent = object()
        pool = _pool(("box1", 1))
        sched = RunScheduler(endpoint_pools={id(agent): pool})
        with pytest.raises(RuntimeError, match="boom"):
            with sched.concurrency_gate(agent):
                raise RuntimeError("boom")
        assert pool.in_flight() == [0]


class TestConfigSurface:
    @pytest.mark.parametrize("entry,expected", [
        ("box1", ("box1", None)),
        ("box1:16", ("box1", 16)),
        ({"id": "box1", "concurrency": 16}, ("box1", 16)),
        ({"id": "box1"}, ("box1", None)),
    ])
    def test_source_entry_spellings(self, entry, expected) -> None:
        assert _parse_source_entry(entry) == expected

    def test_absent_capacity_means_uncapped(self) -> None:
        entries = _agent_model_entries([
            {"id": "glm", "sources": ["box1:16", "box2", {"id": "box3", "concurrency": 4}]}
        ])
        _mid, sources, conc, _ov = entries[0]
        assert sources == ["box1", "box2", "box3"]
        assert conc == {"box1": 16, "box3": 4}, "box2 absent ⇒ uncapped"


class TestBannerAndProgress:
    def test_banner_lists_the_pool_and_its_total(self) -> None:
        agent = RunAgentContract(endpoints=(("box1", 16), ("box2", 4)))
        assert _format_endpoints(agent) == "box1 x16  box2 x4   (2 sources, 20 slots total)"

    def test_banner_shouts_about_a_drained_endpoint(self) -> None:
        # "x0" is easy to skim past, and a drained box silently gets no work.
        agent = RunAgentContract(endpoints=(("box1", 16), ("box2", 0)))
        rendered = _format_endpoints(agent)
        assert "box2 DRAINED" in rendered
        assert "x0" not in rendered

    def test_banner_marks_an_unbounded_pool(self) -> None:
        agent = RunAgentContract(endpoints=(("box1", 16), ("box2", None)))
        assert "uncapped" in _format_endpoints(agent)
        assert "unbounded total" in _format_endpoints(agent)

    @pytest.mark.parametrize("agent,global_cap,expected", [
        (RunAgentContract(max_concurrent=40, endpoints=(("a", 16), ("b", 4))), 0, 20),
        (RunAgentContract(max_concurrent=8, endpoints=(("a", 16), ("b", 4))), 0, 8),
        (RunAgentContract(max_concurrent=40, endpoints=(("a", 16), ("b", 4))), 12, 12),
        (RunAgentContract(max_concurrent=8, endpoints=(("a", 16), ("b", None))), 0, 8),
        (RunAgentContract(max_concurrent="n/a"), 0, None),
        (RunAgentContract(max_concurrent=8), 0, 8),
    ])
    def test_progress_denominator_is_the_binding_cap(self, agent, global_cap, expected) -> None:
        contract = RunContract(max_trials_global=global_cap, agents=[agent])
        assert _live_slot_capacity(contract) == expected


class TestPoolMustBeInterchangeable:
    """Sources are chosen by free capacity, so a mixed pool is unreproducible."""

    @staticmethod
    def _models(**by_id):
        from cage.models.endpoint import ModelConfig
        return {
            mid: ModelConfig(id=mid, provider="openai", model=upstream,
                             base_url=f"http://{mid}/v1")
            for mid, upstream in by_id.items()
        }

    def test_same_upstream_model_is_accepted(self) -> None:
        from cage.config.experiment import _resolve_model_sources
        models = self._models(box1="glm-5.2", box2="glm-5.2")
        resolved = _resolve_model_sources("glm", ["box1", "box2"], models, "models.yml")
        assert [m.id for m in resolved] == ["box1", "box2"]

    def test_mixed_upstream_models_are_rejected(self) -> None:
        from cage.config.experiment import _resolve_model_sources
        models = self._models(box1="glm-5.2", box2="qwen3-32b")
        with pytest.raises(ValueError, match="same upstream model"):
            _resolve_model_sources("glm", ["box1", "box2"], models, "models.yml")


class TestLiveRetune:
    """``cage run --tune`` changes capacity without disturbing in-flight work."""

    @staticmethod
    def _live(tmp_path, entries):
        from cage.experiment.engine.live.run_tuning import TuningWatcher

        pool = EndpointPool([(_Endpoint(n), c) for n, c in entries])
        agent = object()
        sched = RunScheduler(
            endpoint_pools={id(agent): pool},
            tuning_watcher=TuningWatcher(run_dir=tmp_path),
            agent_labels={id(agent): "L"},
        )
        return pool, agent, sched

    @staticmethod
    def _take(sched, agent, n, hold=False):
        names, held = [], []
        for _ in range(n):
            cm = sched.concurrency_gate(agent)
            names.append(cm.__enter__().id)
            held.append(cm) if hold else cm.__exit__(None, None, None)
        return Counter(names), held

    def test_a_tune_redirects_the_next_trials(self, tmp_path) -> None:
        from cage.experiment.engine.live.run_tuning import write_tuning

        pool, agent, sched = self._live(tmp_path, [("box1", 4), ("box2", 1)])
        write_tuning(tmp_path, {"agents": {"L": {"sources": {"box1": 0, "box2": 8}}}})
        counts, _ = self._take(sched, agent, 6)
        assert counts == Counter({"box2": 6}), "drained box1 must take no new work"

    def test_successive_tunes_of_equal_byte_length_are_both_seen(self, tmp_path) -> None:
        # Regression: a (mtime, size) signature missed this. Two tunes can write
        # identical-length JSON within one mtime tick, and the second was
        # silently dropped — the operator's change simply never happened.
        from cage.experiment.engine.live.run_tuning import write_tuning

        pool, agent, sched = self._live(tmp_path, [("box1", 4), ("box2", 1)])
        write_tuning(tmp_path, {"agents": {"L": {"sources": {"box1": 0, "box2": 8}}}})
        assert self._take(sched, agent, 4)[0] == Counter({"box2": 4})
        write_tuning(tmp_path, {"agents": {"L": {"sources": {"box1": 6, "box2": 8}}}})
        counts, _ = self._take(sched, agent, 4)
        assert counts["box1"] > 0, "second tune of the same byte length was dropped"

    def test_new_capacity_is_enforced_not_merely_preferred(self, tmp_path) -> None:
        from cage.experiment.engine.live.run_tuning import write_tuning

        pool, agent, sched = self._live(tmp_path, [("box1", 4), ("box2", 4)])
        write_tuning(tmp_path, {"agents": {"L": {"sources": {"box1": 2, "box2": 3}}}})
        counts, held = self._take(sched, agent, 5, hold=True)
        try:
            assert counts == Counter({"box1": 2, "box2": 3})
            assert pool.in_flight() == [2, 3]
        finally:
            for cm in held:
                cm.__exit__(None, None, None)

    def test_reconfigure_preserves_in_flight_counts(self) -> None:
        pool = EndpointPool([(_Endpoint("box1"), 4)])
        stop = threading.Event()
        pool.acquire(stop)
        pool.acquire(stop)
        pool.reconfigure([(_Endpoint("box1"), 8), (_Endpoint("box2"), 2)])
        assert pool.in_flight() == [2, 0], "raising a cap must not lose in-flight state"

    def test_vanished_endpoint_with_work_is_drained_not_dropped(self) -> None:
        # Dropping it would orphan the release() its running trial still owes.
        pool = EndpointPool([(_Endpoint("gone"), 4)])
        pool.acquire(threading.Event())
        changes = pool.reconfigure([(_Endpoint("fresh"), 2)])
        assert any("still running" in c for c in changes)
        assert len(pool) == 2 and pool.in_flight() == [0, 1]

    def test_unreadable_tuning_file_leaves_the_run_alone(self, tmp_path) -> None:
        from cage.experiment.engine.live.run_tuning import TuningWatcher, tuning_path

        tuning_path(tmp_path).write_text("{ this is not json", encoding="utf-8")
        assert TuningWatcher(run_dir=tmp_path).poll() is None


class TestTuneCli:
    def test_capacity_must_be_explicit(self) -> None:
        import click

        from cage.cli.commands.tune import parse_source_caps

        assert parse_source_caps(("box1:16", "box2:0")) == {"box1": 16, "box2": 0}
        # A bare id at tune time is a typo, not "uncapped" — doing nothing
        # silently would be the worst answer.
        with pytest.raises(click.UsageError, match="capacity is required"):
            parse_source_caps(("box3",))


    def test_tuning_a_dead_run_tells_you_to_resume_instead(self, tmp_path) -> None:
        import click

        from cage.cli.commands.tune import apply_tune

        import json
        import socket

        run_dir = tmp_path / "claude_code:glm:stateless" / "R"
        run_dir.mkdir(parents=True)
        # Must claim THIS host, otherwise liveness falls back to heartbeat age
        # and answers "unknown" rather than "dead".
        (run_dir / "runtime_status.json").write_text(json.dumps({
            "schema_version": "runtime_status.v1",
            "pid": 999_999_999,          # nothing is running under this pid
            "hostname": socket.gethostname(),
            "heartbeat_at_ms": 0,
        }), encoding="utf-8")

        class _Ctx:
            params = {"model_sources": ()}
            def get_parameter_source(self, name):
                from click.core import ParameterSource
                return ParameterSource.COMMANDLINE

        with pytest.raises(click.UsageError, match="not running"):
            apply_tune(run_id="R", model_sources=("box1:8",), clear=False,
                       search_roots=[tmp_path], dry_run=False, echo=lambda *_a: None)


class TestAdoptingANewEndpoint:
    """A machine registered AFTER launch can be tuned into a running pool.

    Requiring every endpoint to be declared up front defeated the purpose: you
    rarely know at launch which box you will add hours later.
    """

    @staticmethod
    def _registry(path, ids, model="glm-5.2"):
        import yaml

        path.write_text(yaml.safe_dump({"models": {
            sid: {"provider": "openai", "model": m, "base_url": f"http://h/{sid}/v1",
                  "api_key": "k", "max_context_size": 131072}
            for sid, m in (ids.items() if isinstance(ids, dict) else {i: model for i in ids}.items())
        }}), encoding="utf-8")

    def _live(self, tmp_path, declared):
        from cage.experiment.engine.live.run_tuning import TuningWatcher
        from cage.models import load_models

        reg = tmp_path / "models.yml"
        self._registry(reg, declared)
        live = load_models(reg)
        pool = EndpointPool([(live[s], 4) for s in declared])
        agent = object()
        sched = RunScheduler(
            endpoint_pools={id(agent): pool},
            tuning_watcher=TuningWatcher(run_dir=tmp_path),
            agent_labels={id(agent): "L"},
            models_file=str(reg),
        )
        return reg, pool, agent, sched

    @staticmethod
    def _fill(sched, agent, n):
        names, held = [], []
        for _ in range(n):
            cm = sched.concurrency_gate(agent)
            names.append(cm.__enter__().id)
            held.append(cm)
        return Counter(names), held

    def test_endpoint_registered_after_launch_is_adopted(self, tmp_path) -> None:
        from cage.experiment.engine.live.run_tuning import write_tuning

        reg, pool, agent, sched = self._live(tmp_path, ["box1", "box2"])
        self._registry(reg, ["box1", "box2", "box3"])  # new machine comes online
        write_tuning(tmp_path, {"agents": {"L": {"sources": {"box3": 8}}}})

        counts, held = self._fill(sched, agent, 16)
        try:
            assert counts == Counter({"box1": 4, "box2": 4, "box3": 8})
            assert pool.total_slots == 16, "adopting must raise total capacity"
        finally:
            for cm in held:
                cm.__exit__(None, None, None)

    def test_a_different_upstream_model_is_refused(self, tmp_path) -> None:
        from cage.experiment.engine.live.run_tuning import write_tuning

        reg, pool, agent, sched = self._live(tmp_path, ["box1"])
        self._registry(reg, {"box1": "glm-5.2", "other": "qwen3-32b"})
        write_tuning(tmp_path, {"agents": {"L": {"sources": {"other": 8}}}})
        self._fill(sched, agent, 1)[1][0].__exit__(None, None, None)
        assert len(pool) == 1, "a mixed pool would make results depend on timing"

    def test_an_unregistered_id_is_refused_not_crashed(self, tmp_path) -> None:
        from cage.experiment.engine.live.run_tuning import write_tuning

        reg, pool, agent, sched = self._live(tmp_path, ["box1"])
        write_tuning(tmp_path, {"agents": {"L": {"sources": {"ghost": 8}}}})
        counts, held = self._fill(sched, agent, 2)
        try:
            assert len(pool) == 1 and set(counts) == {"box1"}
        finally:
            for cm in held:
                cm.__exit__(None, None, None)

    def test_cli_rejects_an_unregistered_endpoint_up_front(self, tmp_path) -> None:
        # The run would refuse it too, but only into its log — where whoever
        # just typed the command is not looking.
        import click

        from cage.cli.commands.tune import _registry_check

        reg = tmp_path / "models.yml"
        self._registry(reg, ["box1"])
        _registry_check({"box1": 8}, str(reg))  # fine
        with pytest.raises(click.UsageError, match="not registered"):
            _registry_check({"nope": 8}, str(reg))


class TestLaunchBaselineAndClear:
    """The tuning file is the run's COMPLETE endpoint state, not a diff.

    Recording only what somebody tuned made the file misleading to read (the
    endpoints a run launched with were invisible) and left ``--tune-clear`` with
    nowhere to restore to.
    """

    def test_launch_state_is_recorded_so_the_file_reads_as_the_whole_picture(self, tmp_path) -> None:
        from cage.experiment.engine.live.run_tuning import read_tuning, write_launch_baseline

        write_launch_baseline(tmp_path, {"L": {"box1": 16, "box2": 4}})
        payload = read_tuning(tmp_path)
        assert payload["agents"]["L"]["sources"] == {"box1": 16, "box2": 4}
        assert payload["launch"]["L"] == {"box1": 16, "box2": 4}

    def test_uncapped_endpoints_are_omitted(self, tmp_path) -> None:
        # There is no number to restore for them and they were never capped.
        from cage.experiment.engine.live.run_tuning import read_tuning, write_launch_baseline

        write_launch_baseline(tmp_path, {"L": {"box1": 16, "box2": None}})
        assert read_tuning(tmp_path)["agents"]["L"]["sources"] == {"box1": 16}

    def test_an_existing_file_is_never_clobbered(self, tmp_path) -> None:
        # On --resume the operator's last tuning is the state worth keeping.
        from cage.experiment.engine.live.run_tuning import (
            read_tuning, write_launch_baseline, write_tuning,
        )

        write_tuning(tmp_path, {"agents": {"L": {"sources": {"box1": 99}}}})
        write_launch_baseline(tmp_path, {"L": {"box1": 16}})
        assert read_tuning(tmp_path)["agents"]["L"]["sources"] == {"box1": 99}

    def test_priming_the_watcher_suppresses_the_runs_own_write(self, tmp_path) -> None:
        # Otherwise the run would read its own launch write back as an operator
        # change and pointlessly reconfigure on the very first trial.
        from cage.experiment.engine.live.run_tuning import TuningWatcher, write_launch_baseline

        write_launch_baseline(tmp_path, {"L": {"box1": 16}})
        watcher = TuningWatcher(run_dir=tmp_path)
        watcher.prime()
        assert watcher.poll() is None

    @staticmethod
    def _ctx(*typed: str):
        """A click context where only ``typed`` flags count as user-supplied.

        Marking everything COMMANDLINE would be wrong in exactly the way the
        feature guards against: a tune must act only on flags actually typed.
        """
        class _Ctx:
            params = {"model_sources": ()}
            def get_parameter_source(self, name):
                from click.core import ParameterSource
                return (ParameterSource.COMMANDLINE if name in typed
                        else ParameterSource.DEFAULT)
        return _Ctx()

    @staticmethod
    def _run_dir(tmp_path):
        import json
        import os
        import socket

        run_dir = tmp_path / "L" / "R"
        run_dir.mkdir(parents=True)
        (run_dir / "runtime_status.json").write_text(json.dumps({
            "schema_version": "runtime_status.v1", "pid": os.getpid(),
            "hostname": socket.gethostname(), "heartbeat_at_ms": 0}), encoding="utf-8")
        return run_dir

    def test_clear_restores_the_launch_configuration(self, tmp_path) -> None:
        from cage.cli.commands.tune import apply_tune
        from cage.experiment.engine.live.run_tuning import read_tuning, write_launch_baseline

        run_dir = self._run_dir(tmp_path)
        write_launch_baseline(run_dir, {"L": {"box1": 16, "box2": 4}})
        # drift away from launch
        apply_tune(run_id="R", model_sources=("box1:32", "box2:0"), clear=False,
                   search_roots=[tmp_path], dry_run=False, echo=lambda *_a: None)
        assert read_tuning(run_dir)["agents"]["L"]["sources"] == {"box1": 32, "box2": 0}

        apply_tune(run_id="R", model_sources=(), clear=True,
                   search_roots=[tmp_path], dry_run=False, echo=lambda *_a: None)
        assert read_tuning(run_dir)["agents"]["L"]["sources"] == {"box1": 16, "box2": 4}

    def test_clear_refuses_to_be_combined_with_a_change(self, tmp_path) -> None:
        import click

        from cage.cli.commands.tune import apply_tune
        from cage.experiment.engine.live.run_tuning import write_launch_baseline

        run_dir = self._run_dir(tmp_path)
        write_launch_baseline(run_dir, {"L": {"box1": 16}})
        with pytest.raises(click.UsageError, match="cannot be combined"):
            apply_tune(run_id="R", model_sources=("box1:8",), clear=True,
                       search_roots=[tmp_path], dry_run=False, echo=lambda *_a: None)

    def test_clear_without_a_recorded_launch_says_so(self, tmp_path) -> None:
        import click

        from cage.cli.commands.tune import apply_tune

        self._run_dir(tmp_path)  # no baseline written
        with pytest.raises(click.UsageError, match="no launch configuration"):
            apply_tune(run_id="R", model_sources=(), clear=True,
                       search_roots=[tmp_path], dry_run=False, echo=lambda *_a: None)



class TestProgressLineTracksTunes:
    """``running=N/cap`` must follow the pool, not the launch snapshot.

    A denominator frozen at startup keeps claiming the run is nearly full after
    a tune has doubled its capacity — worse than showing no denominator at all.
    """

    @staticmethod
    def _sched(tmp_path, entries):
        from cage.experiment.engine.live.run_tuning import TuningWatcher

        pool = EndpointPool([(_Endpoint(n), c) for n, c in entries])
        agent = object()
        sched = RunScheduler(
            endpoint_pools={id(agent): pool},
            tuning_watcher=TuningWatcher(run_dir=tmp_path),
            agent_labels={id(agent): "L"},
        )
        return pool, agent, sched

    @staticmethod
    def _land(sched, agent):
        cm = sched.concurrency_gate(agent)
        cm.__enter__()
        cm.__exit__(None, None, None)

    def test_capacity_grows_when_a_box_is_added(self, tmp_path) -> None:
        from cage.cli.ui.progress_reporter import RunProgressReporter
        from cage.experiment.engine.live.run_tuning import write_tuning

        _pool, agent, sched = self._sched(tmp_path, [("box1", 16), ("box2", 4)])
        reporter = RunProgressReporter(10, enabled=False)
        reporter.bind_capacity_source(sched.live_slot_capacity)
        assert reporter._current_slot_capacity() == 20

        write_tuning(tmp_path, {"agents": {"L": {"sources": {"box2": 36}}}})
        self._land(sched, agent)
        assert reporter._current_slot_capacity() == 52

    def test_capacity_shrinks_when_boxes_are_drained(self, tmp_path) -> None:
        from cage.cli.ui.progress_reporter import RunProgressReporter
        from cage.experiment.engine.live.run_tuning import write_tuning

        _pool, agent, sched = self._sched(tmp_path, [("box1", 16), ("box2", 4)])
        reporter = RunProgressReporter(10, enabled=False)
        reporter.bind_capacity_source(sched.live_slot_capacity)

        write_tuning(tmp_path, {"agents": {"L": {"sources": {"box1": 0}}}})
        self._land(sched, agent)
        assert reporter._current_slot_capacity() == 4

    def test_global_cap_still_clamps_the_denominator(self, tmp_path) -> None:
        from cage.cli.ui.progress_reporter import RunProgressReporter

        pool = EndpointPool([(_Endpoint("box1"), 40)])
        agent = object()
        sched = RunScheduler(trial_cap=12, endpoint_pools={id(agent): pool})
        reporter = RunProgressReporter(10, enabled=False)
        reporter.bind_capacity_source(sched.live_slot_capacity)
        assert reporter._current_slot_capacity() == 12

    def test_an_uncapped_endpoint_leaves_the_count_bare(self, tmp_path) -> None:
        from cage.cli.ui.progress_reporter import RunProgressReporter

        pool = EndpointPool([(_Endpoint("box1"), 16), (_Endpoint("box2"), None)])
        agent = object()
        sched = RunScheduler(endpoint_pools={id(agent): pool})
        reporter = RunProgressReporter(10, enabled=False)
        reporter.bind_capacity_source(sched.live_slot_capacity)
        assert reporter._current_slot_capacity() is None
