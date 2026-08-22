"""Offline re-judging of a persisted serve submission.

``POST /submit`` scores once, against a live target: it gathers verifier
evidence while the containers are still up, freezes that evidence, and runs the
scorer over it. The verdict is then locked in — which is right for the agent
(one submission per instance, no fishing for a pass) and wrong for the
*operator*, whose judge can fail for reasons that have nothing to do with the
agent: an expired API key, a rate limit, a judge model swapped out.

This module re-runs the **offline half** of that scoring:

  - the verifier signal is NOT re-run. Its verdicts were produced against the
    running target and are frozen in ``runtime/check_done_output.txt``; the
    scorer reads them from there, so a re-judge reproduces them exactly. A
    verifier whose *script* changed is a different problem, and one this module
    deliberately does not pretend to solve — it reports ``grader_drift`` so the
    caller can see that a real re-verification (a fresh launch) is needed.
  - the ``LLM_judge`` signal IS re-run, against the persisted findings in
    ``workspace/final_answer`` — the inputs :func:`serve_log.persist_inputs`
    froze for exactly this purpose.

Nothing here needs a running instance: a submission whose target was torn down
weeks ago re-judges the same as one still up.

Every re-judge is **appended**, never substituted: the earlier verdict keeps its
own archived score file and stays in ``record.passes``, and the new pass records
the judge models and score time that produced it. What moves is
``canonical_pass_id`` and the canonical ``scores/<scorer>.json``, so readers
looking at the stable path see the current verdict.

Layer-1 clean: the benchmark is loaded from the module path the record itself
carries. No benchmark is named here.
"""
from __future__ import annotations

import json
import logging
import threading
import time
from pathlib import Path
from typing import Any, Iterable, Mapping

from cage.benchmarks.loader import load_benchmark_from_module
from cage.scoring import ScoringContext
from cage.target.server import serve_log
from cage.target.server.submit import (
    SubmissionError,
    _judge_model_ids,
    resolve_benchmark_module,
)

logger = logging.getLogger(__name__)


class RescoreError(Exception):
    """A submission could not be re-judged (unknown run_id, no judge, …)."""


# One re-judge at a time per submission: two concurrent passes would race on
# record.json and on the canonical score file. Keyed by resolved submission dir.
_locks: dict[str, threading.Lock] = {}
_locks_guard = threading.Lock()


def _submission_lock(sub_dir: Path) -> threading.Lock:
    key = str(Path(sub_dir).resolve())
    with _locks_guard:
        return _locks.setdefault(key, threading.Lock())


# ---------------------------------------------------------------------------
# locating a submission from the launch id
# ---------------------------------------------------------------------------
def discover_serve_roots(
    challenges: Mapping[str, Any] | None = None,
    benchmark_root: Path | None = None,
) -> list[Path]:
    """The ``.cage_serve`` trees this server writes submissions into.

    A submission lands next to the benchmark that owns the challenge
    (``<benchmark>/.cage_serve/``), so the roots are derived the same way
    :func:`submit.score_submission` derives the one it writes to: walk from the
    challenge up to its ``benchmark.py``. ``benchmark_root`` is used as a
    fallback for the same walk, so lookup still works when the challenge
    registry is unavailable.
    """
    roots: list[Path] = []

    def add(base: Path) -> None:
        root = Path(base) / serve_log.SERVE_ROOT_DIRNAME
        if root.is_dir() and root not in roots:
            roots.append(root)

    for challenge in (challenges or {}).values():
        if not isinstance(challenge, Mapping):
            continue
        try:
            add(resolve_benchmark_module(challenge).parent)
        except (SubmissionError, OSError):
            continue

    if benchmark_root:
        here = Path(benchmark_root).resolve()
        for parent in [here, *here.parents]:
            if (parent / "benchmark.py").is_file():
                add(parent)
                break
    return roots


def locate_submission(
    run_id: str, serve_roots: Iterable[Path]
) -> tuple[Path, serve_log.ServeSubmissionRecord] | None:
    """Find the submission a launch id was scored in, or ``None``.

    The directory name embeds the launch id (``<chal>__<run_id>_<hex>``, and a
    label may prefix it), which makes a cheap glob prefilter possible — but the
    match is always CONFIRMED against the record's own
    ``target_launch.launch_id``, so a challenge id or label that merely contains
    the same text can never be mistaken for the submission. If the prefilter
    finds nothing (a renamed directory), fall back to reading the records: the
    record, not the path, is the identity.
    """
    run_id = str(run_id or "")
    if not run_id:
        return None
    roots = [Path(r) for r in serve_roots]

    def confirm(sub_dir: Path) -> tuple[Path, serve_log.ServeSubmissionRecord] | None:
        try:
            record = serve_log.load_record(sub_dir)
        except (OSError, ValueError, KeyError, json.JSONDecodeError):
            return None
        if record is not None and record.target_launch.launch_id == run_id:
            return sub_dir, record
        return None

    for root in roots:
        for candidate in sorted(root.glob(f"*/*{run_id}*")):
            if candidate.is_dir() and (hit := confirm(candidate)):
                return hit
    for root in roots:
        for record_path in sorted(root.glob("*/*/record.json")):
            if hit := confirm(record_path.parent):
                return hit
    return None


# ---------------------------------------------------------------------------
# re-judging
# ---------------------------------------------------------------------------
def _frozen_inputs_digest(
    sub_dir: Path, record: serve_log.ServeSubmissionRecord
) -> str:
    """Recompute the digest over the inputs this submission froze at submit time.

    Read through the record's own declared refs rather than hardcoded paths, so
    the check follows whatever layout the record describes. A value differing
    from ``record.inputs_digest`` means the frozen evidence or the findings
    changed on disk since scoring — the re-judge is then no longer comparable to
    the original pass, and the caller is told so.
    """
    evidence = ""
    if record.verifier_evidence_ref:
        evidence_path = sub_dir / record.verifier_evidence_ref
        if evidence_path.is_file():
            evidence = evidence_path.read_text(encoding="utf-8", errors="replace")
    findings_digest = ""
    if record.submission.findings_ref:
        findings_digest = serve_log.digest_tree(sub_dir / record.submission.findings_ref)
    return serve_log.compute_inputs_digest(evidence, findings_digest)


def rescore_submission(
    sub_dir: str | Path,
    *,
    judge: dict[str, Any] | None,
    serve_root: str | Path | None = None,
    now: float | None = None,
) -> dict[str, Any]:
    """Re-judge one persisted submission and append the verdict as a new pass.

    ``judge`` is required: re-scoring without a judge model would silently
    produce a verifier-only verdict and overwrite a judged one with it, turning
    an operational retry into data loss. A caller with no judge configured gets
    an error instead.
    """
    sub_dir = Path(sub_dir)
    if not judge:
        raise RescoreError(
            "re-judging needs a judge model: configure the server's judge "
            "(TARGET_SERVER_JUDGE_JSON) or name one on the request"
        )

    with _submission_lock(sub_dir):
        record = serve_log.load_record(sub_dir)
        if record is None:
            raise RescoreError(f"no submission record at {sub_dir}")

        bench_module = Path(record.benchmark_module)
        if not bench_module.is_file():
            raise RescoreError(
                f"benchmark module is gone: {record.benchmark_module}"
            )

        task_output_path = sub_dir / "task_output.json"
        if not task_output_path.is_file():
            raise RescoreError(f"submission has no task_output.json: {sub_dir}")
        try:
            task_output = json.loads(task_output_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise RescoreError(f"unreadable task_output.json: {exc}") from exc
        sample = task_output.get("sample") or {}
        output = str(task_output.get("output") or "")

        benchmark = load_benchmark_from_module(bench_module, kwargs={"judge": judge})
        scorer = benchmark.scorer()

        root = Path(serve_root) if serve_root is not None else sub_dir.parent.parent
        # trial_dir is the submission dir, so the scorer reads the frozen
        # evidence and the persisted findings from exactly where submit put
        # them, and appends to the same scores/judge_io.jsonl audit log.
        ctx = ScoringContext(
            trial_id=record.submission_id,
            trial_index=0,
            sample=sample,
            output=output,
            exit_code=0,
            trial_dir=sub_dir,
            run_dir=root,
            canonical_trial_id=record.submission_id,
        )
        scores = scorer.score(ctx)
        scores_out = {
            name: serve_log.score_to_dict(score)
            for name, score in (scores or {}).items()
        }

        ts = now if now is not None else time.time()
        score_time = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(ts))
        judge_models = _judge_model_ids(judge)

        inputs_digest = _frozen_inputs_digest(sub_dir, record)
        # Did the verifier scripts / ground truth change since this submission
        # was graded? The frozen verdicts came from the OLD assets, so a drift
        # means this re-judge does not reflect the current grader — only a fresh
        # launch would.
        current_grader = serve_log.build_grader(
            {"full_path": str(sample.get("challenge_dir") or "")}, sample
        )
        grader_drift = bool(
            record.grader.scoring_assets_digest
            and current_grader.scoring_assets_digest
            and current_grader.scoring_assets_digest
            != record.grader.scoring_assets_digest
        )

        previous_pass_id = record.canonical_pass_id
        previous_scores = _canonical_pass_scores(record)

        new_pass = serve_log.ScorePass(
            pass_id=serve_log.make_pass_id(judge_models, score_time),
            judge_models=judge_models,
            score_time=score_time,
            score_ref="",  # assigned by append_pass when the pass is archived
            scores=scores_out,
            provenance=serve_log.PassProvenance(
                mode="serve",
                challenge_id=record.challenge_id,
                target_launch_id=record.target_launch.launch_id,
                project_name=record.target_launch.project_name,
                launch_time=record.target_launch.launch_time,
                client_id=record.client_id,
                prompt_level=record.prompt_served.level,
                prompt_digest=record.prompt_served.digest,
                inputs_digest=inputs_digest,
                grader=record.grader,
                judge_models=judge_models,
                score_time=score_time,
                origin="rescore",
            ),
        )
        updated = serve_log.append_pass(sub_dir, record, new_pass)

    return {
        "run_id": record.target_launch.launch_id,
        "chal_id": record.challenge_id,
        "submission_id": record.submission_id,
        "submission_dir": str(sub_dir),
        "benchmark_module": record.benchmark_module,
        "pass_id": new_pass.pass_id,
        "previous_pass_id": previous_pass_id,
        "pass_count": len(updated.passes),
        "judge_models": list(judge_models),
        "scores": scores_out,
        "previous_scores": previous_scores,
        "changed": _score_values(previous_scores) != _score_values(scores_out),
        "inputs_digest": inputs_digest,
        "inputs_unchanged": inputs_digest == record.inputs_digest,
        "grader_drift": grader_drift,
        "scored_at": ts,
    }


def _canonical_pass(
    record: serve_log.ServeSubmissionRecord,
) -> serve_log.ScorePass | None:
    """The record's current canonical pass — the verdict that counts."""
    for score_pass in record.passes:
        if score_pass.pass_id == record.canonical_pass_id:
            return score_pass
    return record.passes[-1] if record.passes else None


def _canonical_pass_scores(record: serve_log.ServeSubmissionRecord) -> dict[str, Any]:
    """The scores of the record's current canonical pass (``{}`` if none)."""
    current = _canonical_pass(record)
    return dict(current.scores or {}) if current is not None else {}


def record_result_view(
    sub_dir: str | Path, record: serve_log.ServeSubmissionRecord
) -> dict[str, Any]:
    """The submission's current verdict, read straight from its record.

    Answers a status query for which no in-flight operation exists — after a
    serve restart, or simply long after the re-judge finished. The record is the
    durable truth about what the last pass decided, so reporting it beats
    answering "unknown operation" for work that demonstrably completed.
    """
    current = _canonical_pass(record)
    return {
        "run_id": record.target_launch.launch_id,
        "chal_id": record.challenge_id,
        "submission_id": record.submission_id,
        "submission_dir": str(sub_dir),
        "benchmark_module": record.benchmark_module,
        "pass_id": record.canonical_pass_id,
        "pass_count": len(record.passes),
        "judge_models": list(current.judge_models) if current is not None else [],
        "scores": dict(current.scores or {}) if current is not None else {},
        "inputs_digest": record.inputs_digest,
        # This verdict was read back from disk, not produced by the operation
        # being polled — the caller should not read it as "the re-judge you
        # asked for just finished".
        "from_record": True,
    }


def _score_values(scores: Mapping[str, Any]) -> dict[str, Any]:
    """Just the numeric verdicts, for a cheap did-the-result-move comparison."""
    return {
        name: (payload or {}).get("value")
        for name, payload in (scores or {}).items()
    }
