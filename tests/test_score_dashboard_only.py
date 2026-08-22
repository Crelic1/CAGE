"""``cage score --dashboard-only`` rebuilds the inspector view without scoring.

The inspector serves a finished run's cached ``dashboard_view.json``, so a
change to a benchmark's ``build_dashboard`` is invisible on existing runs until
that file is rewritten. This flag rewrites it from the artifacts already on
disk. The contract worth pinning: it must call ``build_dashboard`` and must NOT
call the scorer — re-scoring can cost LLM judge calls and may need live targets.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from click.testing import CliRunner

from cage.cli.commands.score import (
    _rebuild_dashboard_views,
    _refresh_dashboard_usage,
    score,
)
from cage.experiment.engine.reporting import write_dashboard_view


class _StubSpec:
    def __init__(self, payload: dict) -> None:
        self.payload = payload

    def write(self, path: Path) -> None:
        path.write_text(json.dumps(self.payload), encoding="utf-8")


class _StubBenchmark:
    """Minimal stand-in: records what was asked of it."""

    name = "stub"

    def __init__(self, spec: _StubSpec | None = None) -> None:
        self.spec = spec
        self.dashboard_calls: list[Path] = []
        self.scorer_calls = 0

    def build_dashboard(self, run_dir: Path):
        self.dashboard_calls.append(run_dir)
        return self.spec

    def scorer(self):
        self.scorer_calls += 1
        raise AssertionError("--dashboard-only must not build a scorer")


def test_write_dashboard_view_persists_the_spec(tmp_path: Path) -> None:
    benchmark = _StubBenchmark(_StubSpec({"sections": [{"kind": "summary"}]}))

    path = write_dashboard_view(benchmark, tmp_path)

    assert path == tmp_path / "dashboard_view.json"
    assert json.loads(path.read_text(encoding="utf-8")) == {
        "sections": [{"kind": "summary"}]
    }
    assert benchmark.dashboard_calls == [tmp_path]


def test_write_dashboard_view_survives_a_raising_benchmark(tmp_path: Path) -> None:
    """A broken build_dashboard must not propagate — the caller has other work."""

    class _Boom(_StubBenchmark):
        def build_dashboard(self, run_dir: Path):
            raise RuntimeError("bad row")

    assert write_dashboard_view(_Boom(), tmp_path) is None
    assert not (tmp_path / "dashboard_view.json").exists()


def test_write_dashboard_view_returns_none_when_benchmark_opts_out(
    tmp_path: Path,
) -> None:
    assert write_dashboard_view(_StubBenchmark(None), tmp_path) is None
    assert not (tmp_path / "dashboard_view.json").exists()


def test_dashboard_only_rewrites_a_stale_view_without_scoring(
    tmp_path: Path,
    monkeypatch,
) -> None:
    """The end-to-end promise: old file replaced, scorer never constructed."""
    run_dir = tmp_path / "run"
    run_dir.mkdir()
    stale = run_dir / "dashboard_view.json"
    stale.write_text(json.dumps({"sections": [{"stats": ["Mean score"]}]}), "utf-8")

    benchmark = _StubBenchmark(_StubSpec({"sections": [{"stats": ["pass@3 (max)"]}]}))

    class _Config:
        pass

    config = _Config()
    config.benchmark = benchmark

    import cage.config.experiment as experiment_config

    monkeypatch.setattr(
        experiment_config, "resolve", lambda *a, **kw: config, raising=False
    )

    project = tmp_path / "project.yml"
    project.write_text("project:\n  name: stub\n", encoding="utf-8")

    result = CliRunner().invoke(
        score, [str(run_dir), "--dashboard-only", "--project", str(project)]
    )

    assert result.exit_code == 0, result.output
    assert json.loads(stale.read_text(encoding="utf-8")) == {
        "sections": [{"stats": ["pass@3 (max)"]}]
    }
    assert benchmark.dashboard_calls == [run_dir]
    assert benchmark.scorer_calls == 0
    assert "nothing re-scored" in result.output


class _SelectiveBenchmark(_StubBenchmark):
    """Renders a dashboard only for run dirs named ``live``."""

    def build_dashboard(self, run_dir: Path):
        self.dashboard_calls.append(run_dir)
        return _StubSpec({"ok": True}) if run_dir.name == "live" else None


def test_partial_rebuild_is_not_a_failure(tmp_path: Path) -> None:
    """Aborted runs and their archives have no dashboard — skipping them is normal.

    Exiting non-zero here would make the routine case (a tree with a few
    never-started runs in it) look like the refresh broke.
    """
    empty = tmp_path / "empty"
    empty.mkdir()
    live = tmp_path / "live"
    live.mkdir()
    benchmark = _SelectiveBenchmark()

    _rebuild_dashboard_views([empty, live], benchmark, "")

    assert (live / "dashboard_view.json").is_file()
    assert not (empty / "dashboard_view.json").exists()
    assert benchmark.dashboard_calls == [empty, live]


def test_rebuilding_nothing_at_all_is_a_failure(tmp_path: Path) -> None:
    """A sweep that refreshed zero runs must not report success."""
    empty = tmp_path / "empty"
    empty.mkdir()

    with pytest.raises(SystemExit) as excinfo:
        _rebuild_dashboard_views([empty], _SelectiveBenchmark(), "")

    assert excinfo.value.code == 1


def test_dashboard_only_fails_loudly_when_the_benchmark_cannot_be_loaded(
    tmp_path: Path,
) -> None:
    """Silently writing nothing would read as 'refreshed' when it wasn't."""
    run_dir = tmp_path / "run"
    run_dir.mkdir()

    result = CliRunner().invoke(score, [str(run_dir), "--dashboard-only"])

    assert result.exit_code == 1
    assert "--dashboard-only needs the benchmark" in result.output


# --- usage counts: the other projection a settled run serves ----------------
#
# The run overview reads each trial's call/token counts from dashboard.json,
# not from the trial's own artifacts. So when the parser that produced them was
# wrong, every finished run keeps quoting the wrong number — the trial page,
# which re-reads proxy.jsonl on every view, quotes the right one. Rebuilding
# the dashboard has to cover this half too, or the two pages keep disagreeing.


def _write_trial_proxy_log(
    run_dir: Path,
    trial_id: str,
    *,
    records: int,
    tokens_in: int,
    progress: dict | None = None,
) -> None:
    proxy_dir = run_dir / "trials" / trial_id / "proxy"
    proxy_dir.mkdir(parents=True, exist_ok=True)
    lines = [
        json.dumps({
            "request_id": f"req-{i}",
            "status": "success",
            "upstream_response": {
                "usage": {"prompt_tokens": tokens_in // records, "completion_tokens": 2},
            },
        })
        for i in range(records)
    ]
    (proxy_dir / "proxy.jsonl").write_text("\n".join(lines) + "\n", encoding="utf-8")
    if progress is not None:
        (proxy_dir / "progress.json").write_text(json.dumps(progress), encoding="utf-8")


def _write_dashboard_with_usage(run_dir: Path, usage_by_trial: dict[str, dict]) -> Path:
    path = run_dir / "dashboard.json"
    path.write_text(
        json.dumps({
            "agents": {
                "stub:model:stateless": {
                    "trials": [
                        {"trial_id": trial_id, "usage": usage}
                        for trial_id, usage in usage_by_trial.items()
                    ]
                }
            }
        }),
        encoding="utf-8",
    )
    return path


def _usage_in(path: Path, trial_id: str) -> dict:
    payload = json.loads(path.read_text(encoding="utf-8"))
    for info in payload["agents"]["stub:model:stateless"]["trials"]:
        if info["trial_id"] == trial_id:
            return info["usage"]
    raise AssertionError(f"{trial_id} missing from {path}")


def test_stale_usage_is_re_derived_from_the_proxy_log(tmp_path: Path) -> None:
    run_dir = tmp_path / "run"
    run_dir.mkdir()
    _write_trial_proxy_log(
        run_dir, "t1", records=5, tokens_in=500,
        progress={"total_requests": 5, "success": 5, "successful_requests": 5},
    )
    path = _write_dashboard_with_usage(run_dir, {
        # what a record-dropping parser recorded when the run ended
        "t1": {"num_requests": 3, "total_requests": 3, "input_tokens": 300,
               "output_tokens": 6, "reasoning_tokens": 0, "errors": 0},
    })

    changes = _refresh_dashboard_usage(run_dir)

    assert [trial_id for trial_id, _, _ in changes] == ["t1"]
    assert _usage_in(path, "t1")["num_requests"] == 5
    assert _usage_in(path, "t1")["input_tokens"] == 500


def test_usage_already_matching_the_proxy_is_left_alone(tmp_path: Path) -> None:
    """Idempotent, and cheap: a correct run must not pay to re-read its log."""
    run_dir = tmp_path / "run"
    run_dir.mkdir()
    _write_trial_proxy_log(
        run_dir, "t1", records=4, tokens_in=400,
        progress={"total_requests": 4, "success": 4, "successful_requests": 4},
    )
    usage = {"num_requests": 4, "total_requests": 4, "input_tokens": 400,
             "output_tokens": 8, "reasoning_tokens": 0, "errors": 0}
    path = _write_dashboard_with_usage(run_dir, {"t1": dict(usage)})
    before = path.read_text(encoding="utf-8")

    assert _refresh_dashboard_usage(run_dir) == []
    assert path.read_text(encoding="utf-8") == before, "no diff means no write"


def test_missing_progress_file_falls_back_to_re_deriving(tmp_path: Path) -> None:
    """No cheap answer available — re-derive rather than trust the projection."""
    run_dir = tmp_path / "run"
    run_dir.mkdir()
    _write_trial_proxy_log(run_dir, "t1", records=6, tokens_in=600)  # no progress.json
    path = _write_dashboard_with_usage(run_dir, {
        "t1": {"num_requests": 2, "total_requests": 2, "input_tokens": 200,
               "output_tokens": 4, "reasoning_tokens": 0, "errors": 0},
    })

    assert len(_refresh_dashboard_usage(run_dir)) == 1
    assert _usage_in(path, "t1")["num_requests"] == 6


def test_trial_without_a_proxy_log_is_skipped(tmp_path: Path) -> None:
    """A trial that died before its first call has nothing to re-derive from."""
    run_dir = tmp_path / "run"
    run_dir.mkdir()
    path = _write_dashboard_with_usage(run_dir, {
        "t1": {"num_requests": 0, "total_requests": 0, "input_tokens": 0,
               "output_tokens": 0, "reasoning_tokens": 0, "errors": 0},
    })
    before = path.read_text(encoding="utf-8")

    assert _refresh_dashboard_usage(run_dir) == []
    assert path.read_text(encoding="utf-8") == before


def test_dashboard_only_refreshes_usage_end_to_end(tmp_path: Path, monkeypatch) -> None:
    """Through the real CLI: one flag rebuilds every projection, still no scoring."""
    run_dir = tmp_path / "run"
    run_dir.mkdir()
    _write_trial_proxy_log(
        run_dir, "t1", records=5, tokens_in=500,
        progress={"total_requests": 5, "success": 5, "successful_requests": 5},
    )
    dashboard = _write_dashboard_with_usage(run_dir, {
        "t1": {"num_requests": 3, "total_requests": 3, "input_tokens": 300,
               "output_tokens": 6, "reasoning_tokens": 0, "errors": 0},
    })

    benchmark = _StubBenchmark(_StubSpec({"sections": []}))

    class _Config:
        pass

    config = _Config()
    config.benchmark = benchmark

    import cage.config.experiment as experiment_config

    monkeypatch.setattr(
        experiment_config, "resolve", lambda *a, **kw: config, raising=False
    )
    project = tmp_path / "project.yml"
    project.write_text("project:\n  name: stub\n", encoding="utf-8")

    result = CliRunner().invoke(
        score, [str(run_dir), "--dashboard-only", "--project", str(project)]
    )

    assert result.exit_code == 0, result.output
    assert _usage_in(dashboard, "t1")["num_requests"] == 5
    assert "t1 usage: 3 calls / 0.00M in → 5 calls / 0.00M in" in result.output
    assert "1 trial usage blocks" in result.output
    assert benchmark.scorer_calls == 0
