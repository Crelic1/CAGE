"""Target-range management surface: ``GET /instances`` projection + console.

These exercise the console-facing endpoints without Docker: ``TestClient`` is
built WITHOUT the context-manager form, so FastAPI's lifespan (network setup,
startup GC, health monitor) never fires, and ``probe`` defaults off so no
per-instance health check touches the daemon. The instance registry is an
in-memory dict we seed directly.
"""

from __future__ import annotations

import time
from datetime import datetime

import pytest
from fastapi.testclient import TestClient

from cage.target.server import challenge_server as cs
from cage.target.server import server_state as ss
from cage.target.server.schemas import ServiceInfo


def _seed(**over):
    # The registry stores ServiceInfo objects (see launch.py: final_services =
    # [ServiceInfo(**item) ...]), so seed the same type _build_entry_urls reads.
    base = {
        "chal_id": "SIYUCMS", "run_id": "run-01", "project_name": "p",
        "network_name": "cage_bench_default",
        "network_subnet": "172.30.0.0/24", "network_gateway": "172.30.0.1",
        "services": [ServiceInfo(service_name="web", alias="web", ip="1.2.3.4",
                                 inner_ip="172.30.0.5", internal_port=80,
                                 external_port=32101, external_host="0.0.0.0",
                                 host="9.9.9.9", port=32101, protocol="tcp")],
        "lifecycle_state": "running", "target_scope": "per_agent",
        "cage_run_id": "", "audience": "external",
        "entry_service_keys": ["web"], "created_at": time.time() - 60,
    }
    base.update(over)
    return base


@pytest.fixture(autouse=True)
def _clean_registry():
    with ss.running_instances_lock:
        ss.running_instances.clear()
    yield
    with ss.running_instances_lock:
        ss.running_instances.clear()


def test_project_instance_published_gets_entry_urls_and_uptime():
    # A PUBLISHED instance (host ports on 0.0.0.0) advertises entry_urls. Under
    # the server-level model this is keyed on the instance, not the caller — so
    # it holds for internal and external audiences alike.
    info = _seed(public_intent=True)
    for audience in ("external", "internal"):
        summ = cs._project_instance(info, audience=audience, challenges={}, probe_health=False)
        assert summ.chal_id == "SIYUCMS"
        assert summ.run_id == "run-01"
        assert summ.service_count == 1
        assert summ.healthy is None  # not probed
        assert summ.uptime_s is not None and summ.uptime_s >= 60
        # serve-only network output: the isolated docker network + internal address
        assert summ.network_name == "cage_bench_default"
        assert summ.network_subnet == "172.30.0.0/24"
        assert summ.network_gateway == "172.30.0.1"
        assert summ.container_addr == ["172.30.0.5:80"]  # internal ip:port on the network
        assert len(summ.entry_urls) == 1
        assert summ.entry_urls[0].url.startswith("http://")
        assert summ.public is True


def test_project_instance_network_only_has_no_entry_urls():
    # A network-only instance (no host port published) has no entry_urls for
    # anyone; the docker network output (subnet + container_addr) is still there.
    for audience in ("internal", "external"):
        summ = cs._project_instance(_seed(), audience=audience, challenges={}, probe_health=False)
        assert summ.entry_urls == []
        assert summ.public is False
        assert summ.container_addr == ["172.30.0.5:80"]
        assert summ.network_subnet == "172.30.0.0/24"


def test_project_instance_pulls_benchmark_from_challenge_meta():
    challenges = {"SIYUCMS": {"benchmark": "agent_pentest_bench", "category": "real-world-web"}}
    summ = cs._project_instance(_seed(), audience="internal", challenges=challenges, probe_health=False)
    assert summ.benchmark == "agent_pentest_bench"
    assert summ.category == "real-world-web"


def test_instances_endpoint_lists_running_targets():
    ss.set_running_instance("run-01", _seed(run_id="run-01"))
    ss.set_running_instance("run-02", _seed(run_id="run-02", chal_id="range-1",
                                            target_scope="per_challenge", audience="internal"))
    client = TestClient(cs.app)  # no context manager → no lifespan/docker
    r = client.get("/instances")
    assert r.status_code == 200
    body = r.json()
    assert {i["run_id"] for i in body} == {"run-01", "run-02"}
    # sorted by (chal_id, run_id) — plain ASCII, so uppercase 'SIYUCMS' < 'range-1'
    assert [i["chal_id"] for i in body] == ["SIYUCMS", "range-1"]


def test_instances_created_at_is_rfc3339_on_the_wire():
    """``created_at`` crosses the wire as an RFC 3339 string, never a number.

    The registry keeps epoch seconds because uptime arithmetic needs a number,
    but a client parses this field as a timestamp — emitting the raw float made
    strict decoders blow up. ``uptime_s`` must keep working off the raw value.
    """
    ss.set_running_instance("run-01", _seed(created_at=1784477577.5390918))
    r = TestClient(cs.app).get("/instances")
    assert r.status_code == 200
    inst = r.json()[0]

    assert inst["created_at"] == "2026-07-19T16:12:57Z"   # UTC, so TZ-independent
    assert isinstance(inst["created_at"], str)
    # Parses as a real timestamp — the property the float form lacked.
    datetime.fromisoformat(inst["created_at"].replace("Z", "+00:00"))
    # Duration still derives from the numeric registry value, not the string.
    assert isinstance(inst["uptime_s"], float)


def test_instances_created_at_null_when_registry_has_no_timestamp():
    seed = _seed()
    seed.pop("created_at")
    ss.set_running_instance("run-01", seed)
    inst = TestClient(cs.app).get("/instances").json()[0]
    assert inst["created_at"] is None
    assert inst["uptime_s"] is None


def test_instances_openapi_declares_created_at_as_date_time_string():
    """The published spec must advertise the type, not just the field name.

    A bare ``{"type": "number"}`` with no description is what let a consumer
    codegen the wrong type in the first place.
    """
    prop = cs.app.openapi()["components"]["schemas"]["InstanceSummary"]["properties"]["created_at"]
    assert {"type": "string"} in prop["anyOf"]
    assert prop["format"] == "date-time"
    assert "RFC 3339" in prop["description"]


def test_instances_bearer_rejected_when_no_token_configured(monkeypatch):
    monkeypatch.setattr(ss, "EXTERNAL_TOKEN", None, raising=False)
    client = TestClient(cs.app)
    r = client.get("/instances", headers={"Authorization": "Bearer whatever"})
    assert r.status_code == 401


def test_console_index_served_at_root():
    client = TestClient(cs.app)
    r = client.get("/")
    assert r.status_code == 200
    assert "text/html" in r.headers["content-type"]
    assert "TARGET RANGE" in r.text


def test_submit_is_one_shot_per_instance(monkeypatch):
    # The verdict locks in on the first submit; a repeat returns it unchanged
    # (already_submitted=True) and does NOT re-score, so an agent cannot resubmit
    # to fish for a pass.
    ss.set_running_instance("pb-x_r1", {"chal_id": "pb-x", "services": []})
    monkeypatch.setattr(cs, "load_all_challenges", lambda: {"pb-x": {"id": "pb-x", "full_path": "/x"}})
    calls = {"n": 0}

    def _fake_score(**kwargs):
        calls["n"] += 1
        return {"benchmark_module": "m", "scores": {"s": {"value": float(calls["n"])}}, "run_dir": "rd"}

    monkeypatch.setattr(cs, "score_submission", _fake_score)
    try:
        client = TestClient(cs.app)  # no context manager → no lifespan/docker
        r1 = client.post("/submit/pb-x_r1")
        r2 = client.post("/submit/pb-x_r1")
    finally:
        ss.pop_running_instance("pb-x_r1")

    assert r1.status_code == 200 and r2.status_code == 200
    assert r1.json()["already_submitted"] is False
    assert r1.json()["scores"]["s"]["value"] == 1.0
    assert r2.json()["already_submitted"] is True
    assert r2.json()["scores"]["s"]["value"] == 1.0   # the locked-in first verdict
    assert calls["n"] == 1                            # scored once; the repeat is cached


def test_prompt_endpoint_uses_instance_bound_level(monkeypatch):
    # The hint tier is bound to the instance at launch; GET /prompt renders at
    # THAT level, winning over the server-wide default (env).
    monkeypatch.setenv("TARGET_SERVER_PROMPT_LEVEL", "l0")  # server default
    ss.set_running_instance(
        "pb-x_r1", {"chal_id": "pb-x", "services": [], "prompt_level": "l2"},
    )
    monkeypatch.setattr(
        cs, "load_all_challenges",
        lambda: {"pb-x": {"id": "pb-x", "full_path": "/x", "task_profile": "single_target"}},
    )
    seen = {}

    def _fake_render(run_id, instance, challenge, *, prompt_level="l0", public_host=""):
        seen["level"] = prompt_level
        return (f"BRIEFING for {challenge['id']} @ {prompt_level}", "BRIEFING @ {{TARGET}}")

    monkeypatch.setattr(cs, "render_task_prompt", _fake_render)
    try:
        client = TestClient(cs.app)
        r = client.get("/prompt/pb-x_r1")
    finally:
        ss.pop_running_instance("pb-x_r1")

    assert r.status_code == 200
    body = r.json()
    assert body["task_prompt"] == "BRIEFING for pb-x @ l2"
    assert body["task_prompt_template"] == "BRIEFING @ {{TARGET}}"
    assert body["prompt_level"] == "l2"       # instance-bound, not the l0 default
    assert body["task_profile"] == "single_target"
    assert seen["level"] == "l2"


def test_prompt_endpoint_falls_back_to_server_default(monkeypatch):
    # An instance launched without a bound level → the server --prompt-level default.
    monkeypatch.setenv("TARGET_SERVER_PROMPT_LEVEL", "l1")
    ss.set_running_instance("pb-x_r1", {"chal_id": "pb-x", "services": []})
    monkeypatch.setattr(
        cs, "load_all_challenges", lambda: {"pb-x": {"id": "pb-x", "full_path": "/x"}}
    )
    monkeypatch.setattr(
        cs, "render_task_prompt",
        lambda *a, prompt_level="l0", **k: (f"@{prompt_level}", "@tmpl"),
    )
    try:
        r = TestClient(cs.app).get("/prompt/pb-x_r1")
    finally:
        ss.pop_running_instance("pb-x_r1")
    assert r.json()["prompt_level"] == "l1"   # fell back to the server default


def test_prompt_endpoint_404_for_unknown_run():
    client = TestClient(cs.app)
    r = client.get("/prompt/nope")
    assert r.status_code == 404


# --- Launch lifecycle visibility (issue #2: a slow synchronous launch must be
# reconcilable via GET /instances while it is still in flight) -----------------

def test_project_instance_handles_minimal_launching_record():
    # The early-registered record carries no services / network / entry keys yet.
    # It must still project into a valid summary a reconciling caller can read.
    ss.set_running_instance(
        "range9_ab12",
        {
            "chal_id": "pb-postexp-range-9", "run_id": "range9_ab12",
            "project_name": "p", "cage_run_id": "manual-probe-1",
            "audience": "external", "target_scope": "per_agent",
            "prompt_level": "l0", "lifecycle_state": "launching",
            "created_at": time.time(),
        },
    )
    client = TestClient(cs.app)
    r = client.get("/instances")   # probe off — cheap cached lifecycle_state
    assert r.status_code == 200
    (row,) = r.json()
    assert row["run_id"] == "range9_ab12"
    assert row["lifecycle_state"] == "launching"
    assert row["cage_run_id"] == "manual-probe-1"
    assert row["service_count"] == 0
    assert row["entry_urls"] == [] and row["container_addr"] == []


def _drive_launch(monkeypatch, tmp_path, *, fail_readiness=False):
    """Drive ``_launch_challenge_impl`` with every Docker/heavy seam stubbed, so
    the registry lifecycle transitions can be observed without a daemon. Returns
    ``(chal_id, seen)`` where ``seen`` captures the visible lifecycle_state at
    compose-up time and at readiness-wait time."""
    from cage.target.adapters.base import LaunchSpec
    from cage.target.server import launch as lc
    from cage.target.server.launch_runtime import ComposeRuntimePlan

    chal_id = "pb-postexp-range-9"
    meta = {"adapter_kind": "challenge_json", "source_fields": {}, "category": "post-exploitation"}
    monkeypatch.setattr(lc, "load_all_challenges", lambda: {chal_id: meta})

    class _Adapter:
        def build_launch_spec(self, _m):
            return LaunchSpec(mode="compose", working_directory=str(tmp_path), runtime_patches={})

    monkeypatch.setattr(lc, "build_default_registry", lambda: type("R", (), {"get": lambda self, k: _Adapter()})())

    svc = {"service_name": "web", "alias": "web", "ip": "172.30.0.5",
           "inner_ip": "172.30.0.5", "internal_port": 80, "external_port": None}
    plan = ComposeRuntimePlan(compose_path=tmp_path / "c.yml", config={"networks": {}},
                              services=[svc], public_service_names=[], external_ports={},
                              agent_network_name="cage_bench_default")
    monkeypatch.setattr(lc, "materialize_compose_runtime", lambda **k: plan)
    for name, fn in {
        "self_heal_docker_network": lambda: None,
        "load_env_file_vars": lambda *a, **k: {},
        "ensure_docker_cli_config_dir": lambda env: None,
        "_missing_build_images": lambda plan, env: [],
        "resolve_service_inner_ips": lambda *a, **k: {},
        "capture_project_logs": lambda pn: {},
        "_purge_project_by_name": lambda pn: None,
        "_unlink_runtime_compose": lambda p: None,
        "wait_for_services_healthy": lambda **k: None,
        "build_network_debug": lambda **k: {"network": {"subnet": "172.30.0.0/24", "gateway": "172.30.0.1"}},
    }.items():
        monkeypatch.setattr(lc, name, fn)

    seen = {}

    def _lifecycle_now():
        rows = [v for v in ss.running_instances.values() if v["chal_id"] == chal_id]
        return rows[0]["lifecycle_state"] if rows else None

    def _fake_run(cmd, **kw):
        seen["at_up"] = _lifecycle_now()   # must already be visible as "launching"
        return type("R", (), {"returncode": 0, "stderr": "", "stdout": ""})()

    monkeypatch.setattr(lc.subprocess, "run", _fake_run)

    def _fake_containers(**kw):
        seen["at_wait"] = _lifecycle_now()   # advanced to "waiting_health"
        return None

    monkeypatch.setattr(lc, "wait_for_containers_running", _fake_containers)
    monkeypatch.setattr(lc, "wait_for_inner_services_ready",
                        lambda **k: ("inner probe failed" if fail_readiness else None))
    return chal_id, seen


def test_launch_transitions_launching_then_waiting_health_then_running(monkeypatch, tmp_path):
    from cage.target.server import launch as lc

    chal_id, seen = _drive_launch(monkeypatch, tmp_path)
    resp = lc._launch_challenge_impl(
        chal_id, force_recreate=False, target_scope="per_agent",
        audience="external", network_only=True, prompt_level="l0",
    )
    assert resp.status == "launched"
    # The instance was reconcilable at each slow stage, not just at the end.
    assert seen["at_up"] == "launching"
    assert seen["at_wait"] == "waiting_health"
    rows = [v for v in ss.running_instances.values() if v["chal_id"] == chal_id]
    assert len(rows) == 1 and rows[0]["lifecycle_state"] == "running"


def test_launch_failure_pops_early_record(monkeypatch, tmp_path):
    from fastapi import HTTPException

    from cage.target.server import launch as lc

    chal_id, seen = _drive_launch(monkeypatch, tmp_path, fail_readiness=True)
    with pytest.raises(HTTPException):
        lc._launch_challenge_impl(
            chal_id, force_recreate=False, target_scope="per_agent",
            audience="external", network_only=True, prompt_level="l0",
        )
    # It was visible mid-flight ...
    assert seen["at_up"] == "launching"
    # ... but a failed launch must leave NO phantom entry behind.
    assert [v for v in ss.running_instances.values() if v["chal_id"] == chal_id] == []


# --- container_addr / entry-url scope: advertise the declared entry services,
# not every host that merely sits on the agent network ------------------------

def test_entry_service_keys_fall_back_to_entry_services():
    from cage.target.server.launch import _entry_service_keys_from_meta
    # web declares application_service_keys
    assert _entry_service_keys_from_meta(
        {"source_fields": {"application_service_keys": ["web"]}}) == {"web"}
    # post-exploitation ranges declare entry_services — the launch response must
    # honor it (same field the agent prompt + GET /challenges count already read)
    assert _entry_service_keys_from_meta(
        {"source_fields": {"entry_services": ["cmsms-web", "activemq"]}}) == {"cmsms-web", "activemq"}
    # application_service_keys wins when both are present
    assert _entry_service_keys_from_meta(
        {"source_fields": {"application_service_keys": ["web"], "entry_services": ["x"]}}) == {"web"}
    # a range that declares neither → empty (build_container_addrs then lists all)
    assert _entry_service_keys_from_meta({"source_fields": {}}) == set()


def test_container_addr_scopes_to_declared_entries():
    from cage.target.server.network_debug import build_container_addrs
    svcs = [
        ServiceInfo(service_name="cmsms-web", alias="a", ip="1",
                    inner_ip="172.30.0.5", internal_port=80, external_port=None),
        ServiceInfo(service_name="backing-store", alias="b", ip="2",
                    inner_ip="172.30.0.9", internal_port=3306, external_port=None),
    ]
    # declared entry → only that address is advertised (backing-store excluded)
    assert build_container_addrs(svcs, {"cmsms-web"}) == ["172.30.0.5:80"]
    # no entries declared → whole internal topology is listed
    assert set(build_container_addrs(svcs, set())) == {"172.30.0.5:80", "172.30.0.9:3306"}
