"""Async idempotent launch operations (issue #4).

Exercises the operation lifecycle without Docker: the provisioning / health /
prompt / cleanup functions are replaced with fakes via ``launch_ops.configure``,
and the durable store points at a tmp dir. Covers the acceptance criteria — lost
202, duplicate POST, 409 conflict, restart recovery, cancellation before a
run_id exists, missing build_prompt, startup failure, and the poll-to-ready flow.
"""

from __future__ import annotations

import threading
import time

import pytest

from cage.target.server import launch_ops


# --------------------------------------------------------------------------- #
# Fakes + harness
# --------------------------------------------------------------------------- #

class FakeResp:
    def __init__(self, run_id, entry_urls=None, container_addr=None):
        self.run_id = run_id
        self.entry_urls = entry_urls or []
        self.container_addr = container_addr or []
        self.network_name = "net"
        self.network_subnet = "172.30.0.0/24"


class Harness:
    """Configurable fakes + counters wired into the orchestrator."""

    def __init__(self):
        self.provision_calls = 0
        self.cleanup_calls = []
        self.purge_calls = []
        self.gate = None            # optional threading.Event to block provisioning
        self.provision_error = None  # set to raise inside provisioning
        self.healthy = True
        self.prompt = ("BRIEFING for the agent", "TEMPLATE")
        self.entry_urls = [{"name": "web", "role": "web", "url": "http://10.0.0.1:32101",
                            "host": "10.0.0.1", "port": 32101, "protocol": "http"}]
        self.container_addr = ["172.30.0.2:80"]
        self.instance = {"services": [], "entry_service_keys": ["web"],
                         "public_intent": True, "external_ports": {"web": 32101}}
        # Teardown fidelity: a successful cleanup/purge actually removes the
        # cage_run_id-labelled resources, so a later has_resources() probe sees
        # them gone. ``teardown_error`` forces both to raise (and NOT clear the
        # resources) to exercise the failed-cleanup path.
        self.resources_alive = True
        self.teardown_error = None

    def provision(self, **kwargs):
        self.provision_calls += 1
        self._last_kwargs = kwargs
        if self.gate is not None:
            self.gate.wait(timeout=10)
        if self.provision_error is not None:
            raise self.provision_error
        net_only = bool(kwargs.get("network_only"))
        return FakeResp(
            run_id=f"{kwargs['chal_id']}_run",
            entry_urls=[] if net_only else self.entry_urls,
            container_addr=self.container_addr,
        )

    def health(self, run_id):
        return self.healthy

    def get_instance(self, run_id):
        return self.instance

    def load_challenges(self):
        return {"pb-x": {"id": "pb-x", "full_path": "/x"}}

    def render_prompt(self, run_id, instance, challenge, *, prompt_level="l0", public_host=""):
        return self.prompt

    def cleanup_instance(self, chal_id, run_id):
        self.cleanup_calls.append((chal_id, run_id))
        if self.teardown_error is not None:
            raise self.teardown_error
        self.resources_alive = False

    def purge_by_run_id(self, cage_run_id):
        self.purge_calls.append(cage_run_id)
        if self.teardown_error is not None:
            raise self.teardown_error
        self.resources_alive = False
        return 1

    def has_resources(self, cage_run_id):
        return self.resources_alive


@pytest.fixture
def orch(tmp_path, monkeypatch):
    h = Harness()
    o = launch_ops.reset_for_test(tmp_path / "ops")
    launch_ops.configure(
        provision=h.provision, health=h.health, get_instance=h.get_instance,
        load_challenges=h.load_challenges, render_prompt=h.render_prompt,
        cleanup_instance=h.cleanup_instance, purge_by_run_id=h.purge_by_run_id,
        has_resources=h.has_resources,
    )
    o.harness = h  # type: ignore[attr-defined]
    yield o
    o.shutdown()


def _params(**over):
    p = {"cage_run_id": "arena-1", "challenge_id": "pb-x", "target_scope": "per_agent",
         "network_only": False, "prompt_level": "l0"}
    p.update(over)
    return p


def _wait(orch, launch_id, states, timeout=5.0):
    deadline = time.time() + timeout
    while time.time() < deadline:
        op = orch.store.get(launch_id)
        if op is not None and op.status in states:
            return op
        time.sleep(0.02)
    op = orch.store.get(launch_id)
    raise AssertionError(f"op {launch_id} stuck at {op.status if op else None}, wanted {states}")


# --------------------------------------------------------------------------- #
# Happy path + ready guarantees
# --------------------------------------------------------------------------- #

def test_poll_to_ready_flow(orch):
    op, created = orch.submit("arena-1", _params())
    assert created is True
    assert op.status in (launch_ops.QUEUED, launch_ops.STARTING)
    ready = _wait(orch, "arena-1", {launch_ops.READY})
    r = ready.result
    # ready guarantees a real run_id, a reachable address, and a task prompt
    assert r["run_id"] == "pb-x_run"
    assert r["entry_urls"] and r["entry_urls"][0]["url"].startswith("http://")
    assert r["task_prompt"] == "BRIEFING for the agent"
    assert r["task_prompt_template"] == "TEMPLATE"
    assert orch.harness.provision_calls == 1


def test_ready_requires_non_empty_prompt(orch):
    orch.harness.prompt = ("", "")   # benchmark produced no prompt
    orch.submit("arena-1", _params())
    op = _wait(orch, "arena-1", {launch_ops.FAILED})
    assert op.error["code"] == "prompt_unavailable"
    assert op.error["retryable"] is False
    # a failed launch is cleaned up
    assert orch.harness.purge_calls == ["arena-1"]


def test_ready_requires_entry_urls_for_a_publishing_launch(orch):
    orch.harness.entry_urls = []     # publishing launch but nothing published
    orch.submit("arena-1", _params(network_only=False))
    op = _wait(orch, "arena-1", {launch_ops.FAILED})
    assert op.error["code"] == "entry_urls_unavailable"


def test_network_only_launch_is_ready_on_container_addr(orch):
    # A network-only launch has no entry_urls by design; container_addr suffices.
    orch.harness.entry_urls = []
    orch.harness.instance = {"services": [], "public_intent": False, "external_ports": {}}
    op, _ = orch.submit("arena-1", _params(network_only=True))
    ready = _wait(orch, "arena-1", {launch_ops.READY})
    assert ready.result["container_addr"] == ["172.30.0.2:80"]
    assert ready.result["entry_urls"] == []


# --------------------------------------------------------------------------- #
# Idempotency + lost-response recovery
# --------------------------------------------------------------------------- #

def test_duplicate_post_returns_same_op_no_second_build(orch):
    orch.submit("arena-1", _params())
    _wait(orch, "arena-1", {launch_ops.READY})
    # a lost 202 → the caller re-POSTs the identical request
    op2, created2 = orch.submit("arena-1", _params())
    assert created2 is False
    assert op2.status == launch_ops.READY
    assert orch.harness.provision_calls == 1   # NOT rebuilt


def test_conflicting_params_are_409(orch):
    orch.submit("arena-1", _params(prompt_level="l0"))
    with pytest.raises(launch_ops.LaunchOpError) as ei:
        orch.submit("arena-1", _params(prompt_level="l2"))   # same id, different params
    assert ei.value.http_status == 409
    assert ei.value.code == "idempotency_conflict"


def test_operational_knobs_are_not_a_conflict(orch):
    # ttl / advertise host don't change the container set, so re-POST with a
    # fresh lease is the same operation, not a conflict.
    orch.submit("arena-1", _params(ttl=600))
    _wait(orch, "arena-1", {launch_ops.READY})
    op2, created2 = orch.submit("arena-1", _params(ttl=1800))
    assert created2 is False and op2.status == launch_ops.READY


# --------------------------------------------------------------------------- #
# Failure handling
# --------------------------------------------------------------------------- #

def test_startup_failure_is_terminal_and_cleaned_up(orch):
    orch.harness.provision_error = RuntimeError("docker up failed")
    orch.submit("arena-1", _params())
    op = _wait(orch, "arena-1", {launch_ops.FAILED})
    assert op.error["code"] == "startup_failed"
    assert "docker up failed" in op.error["message"]
    assert orch.harness.purge_calls == ["arena-1"]


def test_unhealthy_instance_fails(orch):
    orch.harness.healthy = False
    orch.submit("arena-1", _params())
    op = _wait(orch, "arena-1", {launch_ops.FAILED})
    assert op.error["code"] == "unhealthy"


# --------------------------------------------------------------------------- #
# Cancellation — fenced, evidence-backed close (issue #5)
# --------------------------------------------------------------------------- #

def test_cancel_of_starting_op_returns_closing_and_never_becomes_ready(orch):
    """Issue #5 bug 1: a cancelled ``starting`` op must never be resurrected.

    The worker is blocked in provisioning until AFTER ``cancel()`` returns — the
    exact ordering under which the old short-lived ``_cancelled`` marker was
    already discarded, so ``_run`` wrote the op back to ``ready`` with a live
    target. Now: cancel returns ``closing`` (worker still active), and when the
    worker unwinds it tears down what it built and the op reaches ``closed`` —
    never ``ready``, no usable result.
    """
    gate = threading.Event()
    orch.harness.gate = gate
    orch.submit("arena-1", _params())
    _wait(orch, "arena-1", {launch_ops.STARTING})
    op = orch.cancel("arena-1")
    assert op.status == launch_ops.CLOSING          # worker still active → closing, not closed
    gate.set()                                      # release the blocked worker
    final = _wait(orch, "arena-1", {launch_ops.CLOSED})
    assert final.status == launch_ops.CLOSED        # never resurrected
    assert final.result is None                     # no usable result published
    assert "arena-1" in orch.harness.purge_calls    # resources it created were torn down
    assert orch.harness.resources_alive is False


def test_cancel_queued_op_prevents_provisioning(orch):
    """Issue #5: a queued op with cancellation intent must not provision at all."""
    from cage.target.server.launch_ops import LaunchOp, _fingerprint
    p = _params()
    op = LaunchOp(launch_id="arena-1", cage_run_id="arena-1", challenge_id="pb-x",
                  params={**p, "audience": "internal"}, fingerprint=_fingerprint(p),
                  status=launch_ops.QUEUED, cancel_requested=True)
    orch.store.put(op)
    orch._run("arena-1")                            # what the pool would call
    assert orch.harness.provision_calls == 0        # never provisioned
    assert orch.store.get("arena-1").status == launch_ops.CLOSED


def test_teardown_failure_stays_closing_not_closed(orch):
    """Issue #5 bug 2: ``closed`` is never written while resources remain."""
    orch.submit("arena-1", _params())
    _wait(orch, "arena-1", {launch_ops.READY})
    orch.harness.teardown_error = RuntimeError("forced cleanup failure")
    op = orch.cancel("arena-1")
    assert op.status == launch_ops.CLOSING          # cleanup failed → stay closing
    assert op.error["code"] == "cleanup_incomplete"
    assert orch.harness.resources_alive is True      # still present
    # once cleanup can succeed, a repeated DELETE finishes the close
    orch.harness.teardown_error = None
    op2 = orch.cancel("arena-1")
    assert op2.status == launch_ops.CLOSED
    assert orch.harness.resources_alive is False


def test_cancel_is_idempotent(orch):
    orch.submit("arena-1", _params())
    _wait(orch, "arena-1", {launch_ops.READY})
    a = orch.cancel("arena-1")
    b = orch.cancel("arena-1")
    assert a.status == launch_ops.CLOSED and b.status == launch_ops.CLOSED
    assert orch.cancel("does-not-exist") is None


def test_restart_preserves_cancellation_intent(orch):
    """Issue #5: a restart mid-cancel finalizes cleanup, never re-drives."""
    from cage.target.server.launch_ops import LaunchOp, _fingerprint
    p = _params()
    op = LaunchOp(launch_id="arena-1", cage_run_id="arena-1", challenge_id="pb-x",
                  params={**p, "audience": "internal"}, fingerprint=_fingerprint(p),
                  status=launch_ops.STARTING, run_id="pb-x_run",
                  cancel_requested=True, attempts=1)
    orch.store.put(op)
    orch.reconcile_on_startup()
    op = orch.store.get("arena-1")
    assert op.status == launch_ops.CLOSED           # finalized cleanup
    assert orch.harness.provision_calls == 0        # NOT re-driven
    assert "arena-1" in orch.harness.purge_calls


# --------------------------------------------------------------------------- #
# Durability + restart recovery
# --------------------------------------------------------------------------- #

def test_record_survives_restart_and_status_is_readable(orch, tmp_path):
    orch.submit("arena-1", _params())
    _wait(orch, "arena-1", {launch_ops.READY})
    orch.shutdown()
    # a brand-new orchestrator over the SAME store dir = a process restart
    o2 = launch_ops.reset_for_test(tmp_path / "ops")
    h = Harness()
    launch_ops.configure(
        provision=h.provision, health=h.health, get_instance=h.get_instance,
        load_challenges=h.load_challenges, render_prompt=h.render_prompt,
        cleanup_instance=h.cleanup_instance, purge_by_run_id=h.purge_by_run_id,
        has_resources=h.has_resources,
    )
    op = o2.store.get("arena-1")
    assert op is not None and op.status == launch_ops.READY   # survived
    assert op.result["run_id"] == "pb-x_run"
    o2.reconcile_on_startup()
    assert o2.store.get("arena-1").status == launch_ops.READY  # terminal left alone
    o2.shutdown()


def test_reconcile_redrives_an_interrupted_launch(orch, tmp_path):
    # simulate a crash mid-provisioning: an op persisted in STARTING with no result
    from cage.target.server.launch_ops import LaunchOp, _fingerprint
    p = _params()
    op = LaunchOp(launch_id="arena-1", cage_run_id="arena-1", challenge_id="pb-x",
                  params={**p, "audience": "internal"}, fingerprint=_fingerprint(p),
                  status=launch_ops.STARTING, attempts=1)
    orch.store.put(op)
    orch.reconcile_on_startup()
    # partial build purged, then re-driven to completion under the same id
    assert "arena-1" in orch.harness.purge_calls
    ready = _wait(orch, "arena-1", {launch_ops.READY})
    assert ready.result["run_id"] == "pb-x_run"


def test_reconcile_gives_up_after_max_attempts(orch, monkeypatch):
    from cage.target.server.launch_ops import LaunchOp, _fingerprint
    p = _params()
    op = LaunchOp(launch_id="arena-1", cage_run_id="arena-1", challenge_id="pb-x",
                  params={**p, "audience": "internal"}, fingerprint=_fingerprint(p),
                  status=launch_ops.STARTING, attempts=launch_ops._MAX_ATTEMPTS)
    orch.store.put(op)
    orch.reconcile_on_startup()
    op = orch.store.get("arena-1")
    assert op.status == launch_ops.FAILED
    assert op.error["code"] == "restart_attempts_exhausted"


def test_reconcile_finishes_an_interrupted_teardown(orch):
    from cage.target.server.launch_ops import LaunchOp, _fingerprint
    p = _params()
    op = LaunchOp(launch_id="arena-1", cage_run_id="arena-1", challenge_id="pb-x",
                  params=p, fingerprint=_fingerprint(p), status=launch_ops.CLOSING,
                  run_id="pb-x_run")
    orch.store.put(op)
    orch.reconcile_on_startup()
    op = orch.store.get("arena-1")
    assert op.status == launch_ops.CLOSED
    assert "arena-1" in orch.harness.purge_calls


# --------------------------------------------------------------------------- #
# HTTP contract (POST/GET/DELETE /launches) via TestClient
# --------------------------------------------------------------------------- #

from fastapi.testclient import TestClient  # noqa: E402

from cage.target.server import challenge_server as cs  # noqa: E402
from cage.target.server import server_state as ss  # noqa: E402


@pytest.fixture
def http(tmp_path, monkeypatch):
    h = Harness()
    launch_ops.reset_for_test(tmp_path / "ops")
    launch_ops.configure(
        provision=h.provision, health=h.health, get_instance=h.get_instance,
        load_challenges=h.load_challenges, render_prompt=h.render_prompt,
        cleanup_instance=h.cleanup_instance, purge_by_run_id=h.purge_by_run_id,
        has_resources=h.has_resources,
    )
    monkeypatch.setattr(cs, "load_all_challenges", h.load_challenges)
    monkeypatch.setattr(ss, "EXTERNAL_TOKEN", None, raising=False)
    client = TestClient(cs.app)   # no context manager → no lifespan/docker
    yield client, h
    launch_ops.get_orchestrator().shutdown()


def _post(client, **over):
    body = {"cage_run_id": "arena-1", "challenge_id": "pb-x",
            "target_scope": "per_agent", "network_only": False, "prompt_level": "l0"}
    body.update(over)
    return client.post("/launches", json=body)


def _poll_ready(client, launch_id, timeout=5.0):
    deadline = time.time() + timeout
    while time.time() < deadline:
        r = client.get(f"/launches/{launch_id}")
        if r.json()["status"] in (launch_ops.READY, launch_ops.FAILED, launch_ops.CLOSED):
            return r
        time.sleep(0.02)
    raise AssertionError("did not settle")


def test_http_post_returns_202_with_location_and_retry_after(http):
    client, _ = http
    r = _post(client)
    assert r.status_code == 202
    assert r.headers["location"] == "/launches/arena-1"
    assert r.headers["retry-after"] == str(launch_ops.RETRY_AFTER_S)
    body = r.json()
    assert body["launch_id"] == "arena-1"
    assert body["status"] in (launch_ops.QUEUED, launch_ops.STARTING)
    assert body["status_url"] == "/launches/arena-1"


def test_http_fleet_polling_flow_to_ready(http):
    client, _ = http
    assert _post(client).status_code == 202
    r = _poll_ready(client, "arena-1")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ready"
    assert body["result"]["run_id"] == "pb-x_run"
    assert body["result"]["entry_urls"]
    assert body["result"]["task_prompt"] == "BRIEFING for the agent"


def test_http_duplicate_post_after_ready_is_200_terminal(http):
    client, h = http
    _post(client)
    _poll_ready(client, "arena-1")
    r2 = _post(client)             # lost-202 replay, identical params
    assert r2.status_code == 200   # terminal representation, not 202
    assert r2.json()["status"] == "ready"
    assert h.provision_calls == 1  # never rebuilt


def test_http_conflicting_reuse_is_409(http):
    client, _ = http
    _post(client, prompt_level="l0")
    r = _post(client, prompt_level="l2")
    assert r.status_code == 409
    assert r.json()["detail"]["error"] == "idempotency_conflict"


def test_http_missing_cage_run_id_is_400(http):
    client, _ = http
    r = client.post("/launches", json={"cage_run_id": "", "challenge_id": "pb-x"})
    assert r.status_code == 400


def test_http_get_unknown_is_404(http):
    client, _ = http
    assert client.get("/launches/nope").status_code == 404


def test_http_delete_cancels_and_is_idempotent(http):
    client, _ = http
    _post(client)
    _poll_ready(client, "arena-1")
    d1 = client.delete("/launches/arena-1")
    assert d1.status_code == 200 and d1.json()["status"] == "closed"
    d2 = client.delete("/launches/arena-1")
    assert d2.json()["status"] == "closed"
    assert client.delete("/launches/unknown").status_code == 404


def test_http_delete_inflight_returns_202_closing_then_200_closed(http):
    """Issue #5: DELETE while provisioning → 202 closing; poll settles to 200 closed."""
    client, h = http
    h.gate = threading.Event()          # block provisioning so DELETE lands mid-flight
    assert _post(client).status_code == 202
    deadline = time.time() + 5
    while time.time() < deadline and \
            client.get("/launches/arena-1").json()["status"] != launch_ops.STARTING:
        time.sleep(0.02)
    d = client.delete("/launches/arena-1")
    assert d.status_code == 202                       # cannot finish immediately
    assert d.json()["status"] == launch_ops.CLOSING
    h.gate.set()                                      # release the worker
    deadline = time.time() + 5
    body = None
    while time.time() < deadline:
        r = client.get("/launches/arena-1")
        body = r.json()
        if body["status"] == launch_ops.CLOSED:
            assert r.status_code == 200
            break
        time.sleep(0.02)
    assert body is not None and body["status"] == launch_ops.CLOSED


def test_http_bearer_gating_on_launches(http, monkeypatch):
    client, _ = http
    monkeypatch.setattr(ss, "EXTERNAL_TOKEN", "tok", raising=False)
    # a bearer against a server with a token configured → accepted
    r = client.post("/launches", json={"cage_run_id": "arena-9", "challenge_id": "pb-x"},
                    headers={"Authorization": "Bearer tok"})
    assert r.status_code == 202
    # a wrong bearer → 401
    assert client.get("/launches/arena-9", headers={"Authorization": "Bearer nope"}).status_code == 401


def test_reconcile_marks_ready_op_gone_after_graceful_restart(orch):
    from cage.target.server.launch_ops import LaunchOp, _fingerprint
    p = _params()
    op = LaunchOp(launch_id="arena-1", cage_run_id="arena-1", challenge_id="pb-x",
                  params=p, fingerprint=_fingerprint(p), status=launch_ops.READY,
                  run_id="pb-x_run", result={"run_id": "pb-x_run", "task_prompt": "x"})
    orch.store.put(op)
    orch.harness.resources_alive = False   # graceful shutdown tore the containers down
    orch.reconcile_on_startup()
    op = orch.store.get("arena-1")
    assert op.status == launch_ops.FAILED
    assert op.error["code"] == "instance_gone"
    assert op.error["retryable"] is True


def test_reconcile_keeps_ready_op_whose_containers_survived_a_crash(orch):
    from cage.target.server.launch_ops import LaunchOp, _fingerprint
    p = _params()
    op = LaunchOp(launch_id="arena-1", cage_run_id="arena-1", challenge_id="pb-x",
                  params=p, fingerprint=_fingerprint(p), status=launch_ops.READY,
                  run_id="pb-x_run", result={"run_id": "pb-x_run", "task_prompt": "x"})
    orch.store.put(op)
    orch.harness.resources_alive = True    # SIGKILL crash: containers still labelled + up
    orch.reconcile_on_startup()
    assert orch.store.get("arena-1").status == launch_ops.READY
