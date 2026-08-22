"""Unit tests for offline re-judging of serve submissions.

Docker-free and model-free: the benchmark is stubbed, so these exercise the
parts that decide whether a re-judge is *safe* — that it finds the right
submission, reads the FROZEN verifier evidence instead of re-running anything,
never destroys the verdict it supersedes, refuses to run without a judge, and
serialises concurrent re-judges of one submission.
"""
from __future__ import annotations

import json
import threading
import time
import types

import pytest

from cage.target.server import rescore, rescore_ops
from cage.target.server import serve_log as sl


# --- fixtures --------------------------------------------------------------- #


def _grader(digest: str = "sha256:assets") -> sl.Grader:
    return sl.Grader(
        dataset_commit="deadbeef", verifier_kind="vuln_scripts",
        scoring_assets_digest=digest,
    )


def _pass(pass_id: str, value: float, *, origin: str = "submit") -> sl.ScorePass:
    return sl.ScorePass(
        pass_id=pass_id,
        judge_models=("m1",),
        score_time="2026-07-10T00:00:00Z",
        score_ref="scores/stub.json",
        scores={"stub": {"value": value, "answer": "", "explanation": "", "metadata": {}}},
        provenance=sl.PassProvenance(
            challenge_id="c", target_launch_id="inst1", judge_models=("m1",),
            score_time="2026-07-10T00:00:00Z", grader=_grader(), origin=origin,
        ),
    )


def _make_submission(
    root,
    *,
    run_id: str = "inst1",
    chal_id: str = "c",
    client: str = "local",
    label: str = "",
    evidence: str = '{"status":false,"results":[{"vuln_id":"v1","status":true}]}',
    findings: bool = True,
    grader_digest: str = "sha256:assets",
    challenge_dir: str = "",
    benchmark_module: str = "",
):
    """Lay out one submission on disk exactly as ``submit`` would have."""
    submission_id = f"{chal_id}__{run_id}_ab12"
    sub = sl.submission_dir(root, client, submission_id, label)
    (sub / "runtime").mkdir(parents=True, exist_ok=True)
    (sub / "runtime" / "check_done_output.txt").write_text(evidence, encoding="utf-8")

    findings_ref = ""
    findings_digest = ""
    if findings:
        answer = sub / "workspace" / "final_answer" / "1"
        answer.mkdir(parents=True, exist_ok=True)
        (answer / "vulnerability.json").write_text('{"t":"XSS"}', encoding="utf-8")
        findings_ref = "workspace/final_answer"
        findings_digest = sl.digest_tree(sub / findings_ref)

    sample = {"id": chal_id, "challenge_dir": challenge_dir,
              "metadata": {"verifier_kind": "vuln_scripts"}}
    (sub / "task_output.json").write_text(
        json.dumps({"output": "", "sample": sample}), encoding="utf-8"
    )

    first = _pass("m1@2026-07-10T00:00:00Z", 0.0)
    sl.write_canonical_scores(sub, first.scores)
    record = sl.ServeSubmissionRecord(
        submission_id=submission_id,
        client_id=client,
        challenge_id=chal_id,
        benchmark_module=benchmark_module or str(root / "benchmark.py"),
        created_at="2026-07-10T00:00:00Z",
        target_launch=sl.TargetLaunch(launch_id=run_id, challenge_id=chal_id),
        prompt_served=sl.PromptServed(level="l0"),
        submission=sl.Submission(findings_ref=findings_ref,
                                 findings_digest=findings_digest,
                                 has_findings=bool(findings_ref)),
        grader=_grader(grader_digest),
        inputs_digest=sl.compute_inputs_digest(evidence, findings_digest),
        canonical_pass_id=first.pass_id,
        label=label,
        passes=(first,),
    )
    sl.write_record(sub, record)
    return sub, record


def _stub_benchmark(monkeypatch, value=1.0, *, capture=None):
    """Replace benchmark loading with a scorer that records what it was given."""
    class _Scorer:
        def score(self, ctx):
            if capture is not None:
                capture["ctx"] = ctx
                capture["check_done_output"] = ctx.check_done_output
            return {"stub": types.SimpleNamespace(
                value=value, answer="", explanation="re-judged", metadata={},
            )}

    def _load(module_path, kwargs=None):
        if capture is not None:
            capture["kwargs"] = kwargs
        return types.SimpleNamespace(scorer=lambda: _Scorer())

    monkeypatch.setattr(rescore, "load_benchmark_from_module", _load)


# --- append_pass: never destroy the verdict you supersede ------------------- #


def test_append_pass_archives_the_superseded_verdict(tmp_path):
    sub = tmp_path / "sub"
    sub.mkdir()
    old = _pass("m1@t1", 0.0)
    record = sl.ServeSubmissionRecord(
        submission_id="c__inst1_ab", client_id="local", challenge_id="c",
        benchmark_module="/x/benchmark.py", created_at="t1",
        target_launch=sl.TargetLaunch(launch_id="inst1", challenge_id="c"),
        prompt_served=sl.PromptServed(), submission=sl.Submission(),
        grader=_grader(), inputs_digest="sha256:in",
        canonical_pass_id=old.pass_id, passes=(old,),
    )
    sl.write_canonical_scores(sub, old.scores)
    sl.write_record(sub, record)

    new = _pass("m1@t2", 1.0, origin="rescore")
    updated = sl.append_pass(sub, record, new)

    # canonical path now holds the NEW verdict — that is what readers see
    canonical = json.loads((sub / "scores" / "stub.json").read_text())
    assert canonical["stub"]["value"] == 1.0
    assert updated.canonical_pass_id == "m1@t2"
    assert len(updated.passes) == 2

    # ...and the superseded verdict survives, at its own path
    old_ref = updated.passes[0].score_ref
    assert old_ref.startswith("scores/passes/")
    assert json.loads((sub / old_ref).read_text())["stub"]["value"] == 0.0
    # the new pass is archived too, so a third pass cannot clobber it either
    assert updated.passes[1].score_ref.startswith("scores/passes/")
    assert json.loads((sub / updated.passes[1].score_ref).read_text())["stub"]["value"] == 1.0


def test_append_pass_round_trips_origin_through_the_record(tmp_path):
    sub, record = _make_submission(tmp_path)
    sl.append_pass(sub, record, _pass("m1@t2", 1.0, origin="rescore"))
    loaded = sl.load_record(sub)
    assert [p.provenance.origin for p in loaded.passes] == ["submit", "rescore"]


def test_load_record_tolerates_an_unknown_provenance_field(tmp_path):
    """A record written by a newer cage must still load, not raise."""
    sub, _ = _make_submission(tmp_path)
    raw = json.loads((sub / "record.json").read_text())
    raw["passes"][0]["provenance"]["some_future_field"] = "x"
    (sub / "record.json").write_text(json.dumps(raw), encoding="utf-8")
    loaded = sl.load_record(sub)
    assert loaded is not None
    assert loaded.passes[0].provenance.origin == "submit"


# --- locating a submission by run_id ---------------------------------------- #


def test_locate_submission_finds_by_run_id(tmp_path):
    root = tmp_path / ".cage_serve"
    sub, _ = _make_submission(root, run_id="inst-abc")
    found = rescore.locate_submission("inst-abc", [root])
    assert found is not None
    assert found[0] == sub
    assert found[1].target_launch.launch_id == "inst-abc"


def test_locate_submission_confirms_against_the_record_not_the_path(tmp_path):
    """A directory whose NAME contains the id is not a match on that alone."""
    root = tmp_path / ".cage_serve"
    # challenge id happens to contain the run id we will search for
    _make_submission(root, run_id="other", chal_id="inst9-suite")
    assert rescore.locate_submission("inst9", [root]) is None


def test_locate_submission_falls_back_to_records_when_renamed(tmp_path):
    root = tmp_path / ".cage_serve"
    sub, _ = _make_submission(root, run_id="inst-xyz")
    renamed = sub.parent / "totally-different-name"
    sub.rename(renamed)
    found = rescore.locate_submission("inst-xyz", [root])
    assert found is not None and found[0] == renamed


def test_locate_submission_missing_is_none(tmp_path):
    root = tmp_path / ".cage_serve"
    _make_submission(root, run_id="inst1")
    assert rescore.locate_submission("nope", [root]) is None
    assert rescore.locate_submission("", [root]) is None


# --- re-judging ------------------------------------------------------------- #


def test_rescore_reads_frozen_evidence_and_appends_a_pass(tmp_path, monkeypatch):
    root = tmp_path / ".cage_serve"
    evidence = '{"status":false,"results":[{"vuln_id":"v1","status":true}]}'
    sub, record = _make_submission(root, evidence=evidence)
    (root / "benchmark.py").write_text("# stub", encoding="utf-8")
    capture: dict = {}
    _stub_benchmark(monkeypatch, value=1.0, capture=capture)

    result = rescore.rescore_submission(sub, judge={"models": ["m2"]})

    # the scorer was handed the FROZEN verifier evidence — nothing was re-run
    assert capture["check_done_output"] == evidence
    assert capture["kwargs"] == {"judge": {"models": ["m2"]}}

    assert result["run_id"] == "inst1"
    assert result["scores"]["stub"]["value"] == 1.0
    assert result["previous_scores"]["stub"]["value"] == 0.0
    assert result["changed"] is True
    assert result["judge_models"] == ["m2"]
    assert result["pass_count"] == 2
    assert result["previous_pass_id"] == record.canonical_pass_id
    assert result["inputs_unchanged"] is True
    assert result["grader_drift"] is False

    loaded = sl.load_record(sub)
    assert loaded.canonical_pass_id == result["pass_id"]
    assert loaded.passes[-1].provenance.origin == "rescore"


def test_rescore_refuses_without_a_judge(tmp_path, monkeypatch):
    root = tmp_path / ".cage_serve"
    sub, _ = _make_submission(root)
    (root / "benchmark.py").write_text("# stub", encoding="utf-8")
    _stub_benchmark(monkeypatch)
    with pytest.raises(rescore.RescoreError, match="judge model"):
        rescore.rescore_submission(sub, judge=None)
    # the original verdict is untouched
    assert len(sl.load_record(sub).passes) == 1


def test_rescore_reports_grader_drift(tmp_path, monkeypatch):
    """Verifier scripts changed since grading → the caller must be told."""
    root = tmp_path / ".cage_serve"
    challenge = tmp_path / "challenge"
    (challenge / "exploits").mkdir(parents=True)
    (challenge / "verify.py").write_text("# v1", encoding="utf-8")
    sub, _ = _make_submission(
        root, challenge_dir=str(challenge), grader_digest="sha256:stale",
    )
    (root / "benchmark.py").write_text("# stub", encoding="utf-8")
    _stub_benchmark(monkeypatch)

    result = rescore.rescore_submission(sub, judge={"models": ["m2"]})
    assert result["grader_drift"] is True


def test_rescore_flags_tampered_inputs(tmp_path, monkeypatch):
    root = tmp_path / ".cage_serve"
    sub, _ = _make_submission(root)
    (root / "benchmark.py").write_text("# stub", encoding="utf-8")
    _stub_benchmark(monkeypatch)
    # someone edited the frozen evidence after scoring
    (sub / "runtime" / "check_done_output.txt").write_text("{}", encoding="utf-8")

    result = rescore.rescore_submission(sub, judge={"models": ["m2"]})
    assert result["inputs_unchanged"] is False


def test_rescore_without_benchmark_module_errors(tmp_path, monkeypatch):
    root = tmp_path / ".cage_serve"
    sub, _ = _make_submission(root, benchmark_module=str(tmp_path / "gone.py"))
    _stub_benchmark(monkeypatch)
    with pytest.raises(rescore.RescoreError, match="benchmark module"):
        rescore.rescore_submission(sub, judge={"models": ["m2"]})


def test_record_result_view_reports_the_canonical_pass(tmp_path):
    root = tmp_path / ".cage_serve"
    sub, record = _make_submission(root)
    view = rescore.record_result_view(sub, record)
    assert view["from_record"] is True
    assert view["pass_id"] == record.canonical_pass_id
    assert view["scores"]["stub"]["value"] == 0.0
    assert view["run_id"] == "inst1"


# --- operations ------------------------------------------------------------- #


def _wait_for(predicate, timeout: float = 5.0):
    deadline = time.time() + timeout
    while time.time() < deadline:
        if predicate():
            return True
        time.sleep(0.01)
    return False


def test_pending_op_is_reused_instead_of_running_twice():
    """A second POST while one is in flight must not start a second re-judge."""
    orch = rescore_ops.reset_for_test()
    entered = threading.Event()
    release = threading.Event()
    calls: list[int] = []

    def work():
        calls.append(1)
        entered.set()
        release.wait(5)
        return {"ok": True}

    op1, started1 = orch.submit("r1", work)
    assert started1
    assert entered.wait(5), "worker never started"

    op2, started2 = orch.submit("r1", work)
    assert started2 is False
    assert op2 is op1
    assert op2.status == rescore_ops.RUNNING

    release.set()
    assert _wait_for(lambda: orch.get("r1").status == rescore_ops.DONE)
    assert calls == [1], "the deduped POST must not have run the work again"
    assert orch.get("r1").result == {"ok": True}


def test_finished_op_can_be_started_again():
    """Re-judging a submission twice is the point — a done op is not a wall."""
    orch = rescore_ops.reset_for_test()
    op1, _ = orch.submit("r1", lambda: {"n": 1})
    assert _wait_for(lambda: orch.get("r1").status == rescore_ops.DONE)
    assert op1.attempts == 1

    op2, started = orch.submit("r1", lambda: {"n": 2})
    assert started is True
    assert op2.attempts == 2
    assert _wait_for(lambda: orch.get("r1").result == {"n": 2})


def test_failing_work_becomes_a_failed_op_with_the_reason():
    orch = rescore_ops.reset_for_test()

    def boom():
        raise rescore.RescoreError("no judge model")

    orch.submit("r1", boom)
    assert _wait_for(lambda: orch.get("r1").status == rescore_ops.FAILED)
    op = orch.get("r1")
    assert op.error["code"] == "RescoreError"
    assert "no judge model" in op.error["message"]
    assert op.result is None


def test_status_view_offers_retry_after_only_while_pending():
    orch = rescore_ops.reset_for_test()
    release = threading.Event()
    entered = threading.Event()

    def work():
        entered.set()
        release.wait(5)
        return {"ok": True}

    orch.submit("r1", work)
    assert entered.wait(5)
    pending = rescore_ops.status_view(orch.get("r1"))
    assert pending["status"] == rescore_ops.RUNNING
    assert pending["retry_after"] == rescore_ops.RETRY_AFTER_S
    assert pending["status_url"] == "/rescores/r1"
    assert "result" not in pending

    release.set()
    assert _wait_for(lambda: orch.get("r1").status == rescore_ops.DONE)
    done = rescore_ops.status_view(orch.get("r1"))
    assert "retry_after" not in done
    assert done["result"] == {"ok": True}


# --- HTTP contract ---------------------------------------------------------- #
# TestClient is built WITHOUT the context-manager form, so FastAPI's lifespan
# (docker network setup, GC, monitors) never fires.

from fastapi.testclient import TestClient  # noqa: E402

from cage.target.server import challenge_server as cs  # noqa: E402


@pytest.fixture
def served(tmp_path, monkeypatch):
    """A server whose submission lookup sees one prepared submission."""
    root = tmp_path / ".cage_serve"
    (root).mkdir(parents=True, exist_ok=True)
    (root / "benchmark.py").write_text("# stub", encoding="utf-8")
    monkeypatch.setattr(cs, "_serve_roots", lambda: [root])
    monkeypatch.setenv("TARGET_SERVER_JUDGE_JSON", json.dumps({"models": ["m1"]}))
    rescore_ops.reset_for_test()
    return root


def test_post_rescore_unknown_run_id_is_404(served):
    client = TestClient(cs.app)
    assert client.post("/rescores", json={"run_id": "nope"}).status_code == 404


def test_post_rescore_accepts_a_submission_with_no_findings(served, monkeypatch):
    """A findings-less submission is still re-scorable, and must not be refused.

    Regression: this endpoint used to 409 whenever ``has_findings`` was false,
    on the assumption that a re-score is only ever a re-judge. It is not — it
    re-runs the whole ``score()``, and a marker-based post-exploitation range
    scores entirely from its frozen evidence with no agent findings and no judge
    involved. The old guard therefore rejected precisely the submissions that
    offline re-scoring is most useful for (recomputing after a scoring fix).
    """
    _make_submission(served, run_id="inst-marker", findings=False)
    _stub_benchmark(monkeypatch, value=0.5)
    client = TestClient(cs.app)
    r = client.post("/rescores", json={"run_id": "inst-marker"})
    assert r.status_code == 202
    orch = rescore_ops.get_orchestrator()
    assert _wait_for(lambda: orch.get("inst-marker").status == rescore_ops.DONE)
    assert orch.get("inst-marker").result["scores"]["stub"]["value"] == 0.5


def test_post_rescore_without_a_judge_is_400(served, monkeypatch):
    monkeypatch.delenv("TARGET_SERVER_JUDGE_JSON", raising=False)
    _make_submission(served, run_id="inst-nojudge")
    client = TestClient(cs.app)
    r = client.post("/rescores", json={"run_id": "inst-nojudge"})
    assert r.status_code == 400
    assert "judge model" in r.json()["detail"]


def test_post_rescore_accepts_and_completes(served, monkeypatch):
    sub, _ = _make_submission(served, run_id="inst-ok")
    capture: dict = {}
    _stub_benchmark(monkeypatch, value=1.0, capture=capture)
    client = TestClient(cs.app)

    r = client.post("/rescores", json={"run_id": "inst-ok", "judge_models": ["m9"]})
    assert r.status_code == 202
    body = r.json()
    assert body["run_id"] == "inst-ok"
    assert body["status_url"] == "/rescores/inst-ok"
    assert body["retry_after"] == rescore_ops.RETRY_AFTER_S

    orch = rescore_ops.get_orchestrator()
    assert _wait_for(lambda: orch.get("inst-ok").status == rescore_ops.DONE)

    polled = client.get("/rescores/inst-ok")
    assert polled.status_code == 200
    result = polled.json()["result"]
    assert result["scores"]["stub"]["value"] == 1.0
    assert result["previous_scores"]["stub"]["value"] == 0.0
    assert result["changed"] is True
    assert result["judge_models"] == ["m9"]      # request overrode the server's
    assert result["pass_count"] == 2
    assert result["submission_dir"] == str(sub)


def test_get_rescore_falls_back_to_the_record(served):
    """No operation in flight (e.g. after a restart) still gets a real answer."""
    _make_submission(served, run_id="inst-old")
    client = TestClient(cs.app)
    r = client.get("/rescores/inst-old")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == rescore_ops.DONE
    assert body["result"]["from_record"] is True
    assert body["result"]["scores"]["stub"]["value"] == 0.0


def test_get_rescore_unknown_run_id_is_404(served):
    client = TestClient(cs.app)
    assert client.get("/rescores/nope").status_code == 404


# --- the real scorer, no stub ------------------------------------------------ #
# The stubbed benchmark above can never catch a wrong assumption about what a
# real scorer needs: it returns a score for any input. These drive the actual
# benchmark scorer over real frozen evidence instead.


def _real_scorer_available() -> bool:
    from pathlib import Path
    return (Path(__file__).resolve().parents[1]
            / "examples/agent_pentest_bench/benchmark.py").is_file()


@pytest.mark.skipif(not _real_scorer_available(), reason="benchmark not present")
def test_real_scorer_rescores_marker_evidence_without_findings(tmp_path):
    """A marker range re-scores from frozen evidence alone — no findings, no judge.

    This is the case the removed 409 blocked. Driving the REAL scorer proves the
    verdict is reproducible offline: same frozen evidence in, same numbers out.
    """
    from pathlib import Path

    bench = Path(__file__).resolve().parents[1] / "examples/agent_pentest_bench/benchmark.py"
    root = tmp_path / ".cage_serve"
    # Frozen marker evidence, in the shape gather() writes for a multi_target
    # post-exploitation range: per-stage entries keyed by ``service``.
    evidence = json.dumps({
        "status": False,
        "results": [
            {"stage_id": "s1", "service": "web", "marker_kind": "user", "passed": True},
            {"stage_id": "s2", "service": "web", "marker_kind": "root", "passed": True},
            {"stage_id": "s3", "service": "db", "marker_kind": "user", "passed": False},
        ],
    })
    sub, record = _make_submission(
        root, run_id="inst-mk", chal_id="pb-range", evidence=evidence,
        findings=False, benchmark_module=str(bench),
    )
    # the sample must declare the marker kind, as reconstruct_sample does
    to = json.loads((sub / "task_output.json").read_text())
    to["sample"]["metadata"]["verifier_kind"] = "marker_files"
    (sub / "task_output.json").write_text(json.dumps(to), encoding="utf-8")

    result = rescore.rescore_submission(sub, judge={"models": ["m1"]})
    score = result["scores"]["agent_pentest_bench"]
    # It produced a real verdict rather than erroring on the missing findings.
    assert isinstance(score["value"], (int, float))
    md = score["metadata"]
    assert md.get("markers_passed") == 2 and md.get("markers_total") == 3, md
    # ...and it is deterministic: the same frozen evidence re-scores identically.
    again = rescore.rescore_submission(sub, judge={"models": ["m1"]})
    assert again["scores"]["agent_pentest_bench"]["value"] == score["value"]
    assert again["pass_count"] == 3   # original + two re-scores, all retained


@pytest.mark.skipif(not _real_scorer_available(), reason="benchmark not present")
def test_real_scorer_marker_rescore_needs_no_live_target(tmp_path, monkeypatch):
    """Re-scoring a marker range must not shell out to docker."""
    from pathlib import Path
    import subprocess

    bench = Path(__file__).resolve().parents[1] / "examples/agent_pentest_bench/benchmark.py"
    root = tmp_path / ".cage_serve"
    evidence = json.dumps({"status": False, "results": [
        {"stage_id": "s1", "service": "web", "marker_kind": "user", "passed": True}]})
    sub, _ = _make_submission(root, run_id="inst-mk2", evidence=evidence,
                              findings=False, benchmark_module=str(bench))
    to = json.loads((sub / "task_output.json").read_text())
    to["sample"]["metadata"]["verifier_kind"] = "marker_files"
    (sub / "task_output.json").write_text(json.dumps(to), encoding="utf-8")

    def _boom(*a, **k):
        raise AssertionError("re-scoring must not run a subprocess (docker)")

    monkeypatch.setattr(subprocess, "run", _boom)
    monkeypatch.setattr(subprocess, "check_output", _boom)
    rescore.rescore_submission(sub, judge={"models": ["m1"]})
