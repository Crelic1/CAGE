"""``Benchmark.summarize_scores`` — Layer 2 owns what the headline number means.

Layer 1 collects results, writes ``summary.json``, and renders the run card. It
does not get to decide that "mean of per-trial score values" is the right
aggregate — that is domain knowledge. These tests pin the seam: the framework
asks, renders verbatim, and survives a benchmark that has no opinion or breaks.
"""

from __future__ import annotations

import types

from cage.contracts.scoring import Score
from cage.scoring.lifecycle import _benchmark_summary, _build_summary


def _result(sample_id: str, value: float, error: str = "") -> types.SimpleNamespace:
    return types.SimpleNamespace(
        sample_id=sample_id,
        scores={"demo": Score(value=value)},
        metadata={},
        error=error,
    )


class _Opinionated:
    def summarize_scores(self, results):
        return {
            "metrics": [
                {"label": "pass@3 (max)", "value": 0.5, "detail": "3 / 6 solved"},
                {"label": "pass@3 (avg)", "value": 0.25},
            ],
            "pass_at_k": {"demo": {"k": 3, "n_samples": 2, "pass@3": 0.5}},
        }


class _Silent:
    def summarize_scores(self, results):
        return None


class _Broken:
    def summarize_scores(self, results):
        raise RuntimeError("bad aggregate")


def test_benchmark_metrics_land_in_the_summary() -> None:
    summary = _build_summary([_result("s1", 1.0), _result("s2", 0.0)], _Opinionated())

    assert summary["score_metrics"] == [
        {"label": "pass@3 (max)", "value": 0.5, "detail": "3 / 6 solved"},
        {"label": "pass@3 (avg)", "value": 0.25},
    ]
    # The generic mean stays alongside — other consumers still read it.
    assert summary["mean_scores"] == {"demo": 0.5}


def test_a_benchmark_with_no_opinion_keeps_the_generic_mean() -> None:
    """Overriding is opt-in; every other benchmark must be unaffected."""
    summary = _build_summary([_result("s1", 1.0), _result("s2", 0.0)], _Silent())

    assert "score_metrics" not in summary
    assert summary["mean_scores"] == {"demo": 0.5}


def test_no_benchmark_at_all_still_summarizes() -> None:
    """The hook is optional plumbing, not a new required argument."""
    summary = _build_summary([_result("s1", 0.25)])

    assert "score_metrics" not in summary
    assert summary["mean_scores"] == {"demo": 0.25}


def test_a_broken_hook_never_fails_the_run() -> None:
    """A bad summary is not worth losing a finished run's artifacts over."""
    summary = _build_summary([_result("s1", 1.0)], _Broken())

    assert "score_metrics" not in summary
    assert summary["mean_scores"] == {"demo": 1.0}


def test_malformed_metrics_are_dropped_not_shipped() -> None:
    """Templates format ``value`` as a float; a bad entry must not reach them."""

    class _Sloppy:
        def summarize_scores(self, results):
            return {
                "metrics": [
                    {"label": "good", "value": 0.5},
                    {"label": "", "value": 0.9},        # no label
                    {"label": "no value"},               # missing value
                    {"label": "not a number", "value": "high"},
                    "not even a dict",
                ],
                "pass_at_k": "not a dict",               # wrong shape
            }

    assert _benchmark_summary([], _Sloppy()) == {
        "metrics": [{"label": "good", "value": 0.5}]
    }


def test_values_are_rounded_for_display() -> None:
    class _Precise:
        def summarize_scores(self, results):
            return {"metrics": [{"label": "m", "value": 0.11666666666}]}

    assert _benchmark_summary([], _Precise()) == {
        "metrics": [{"label": "m", "value": 0.1167}]
    }


def _passk_results() -> list[types.SimpleNamespace]:
    """Two samples, two attempts each. Nothing ever reaches a perfect 1.0."""
    return [
        _result("s1", 0.25),
        _result("s1", 0.50),
        _result("s2", 0.00),
        _result("s2", 0.00),
    ]


def test_benchmark_pass_at_k_replaces_the_generic_block() -> None:
    summary = _build_summary(_passk_results(), _Opinionated())

    assert summary["pass_at_k"] == {"demo": {"k": 3, "n_samples": 2, "pass@3": 0.5}}


def test_generic_pass_at_k_writes_off_partial_credit() -> None:
    """Why the hook exists: ``>= 1.0`` calls a half-solved run a total loss.

    This is the framework's honest generic answer for a benchmark it knows
    nothing about — and exactly the answer a partial-credit benchmark must be
    able to override.
    """
    summary = _build_summary(_passk_results())

    assert summary["pass_at_k"]["demo"]["pass@2"] == 0.0
    assert summary["pass_at_k"]["demo"]["pass@1"] == 0.1875


def test_a_benchmark_may_correct_one_aggregate_and_not_the_other() -> None:
    """Supplying only ``metrics`` must not blank out generic pass@k."""

    class _MetricsOnly:
        def summarize_scores(self, results):
            return {"metrics": [{"label": "solved", "value": 0.25}]}

    summary = _build_summary(_passk_results(), _MetricsOnly())

    assert summary["score_metrics"] == [{"label": "solved", "value": 0.25}]
    assert summary["pass_at_k"]["demo"]["pass@2"] == 0.0
