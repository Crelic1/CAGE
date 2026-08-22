"""External-access mode: serving targets to an agent that is not on this host.

Covers the four things that mode has to get right, none of which need Docker:
the publishing decision (which services get a host port), the advertised address
(what an agent is told to dial), the host-published instance cap, and the lease
that keeps a capped slot from being held forever.

``TestClient`` is built WITHOUT the context-manager form so FastAPI's lifespan
(docker network setup, GC, monitors) never fires; the instance registry is an
in-memory dict seeded directly.
"""

from __future__ import annotations

import io
import json
import tarfile
import time

import pytest
from fastapi.testclient import TestClient

from cage.target.server import challenge_server as cs
from cage.target.server import launch as launch_mod
from cage.target.server import public_access as pa
from cage.target.server import server_state as ss
from cage.target.server.launch_runtime import materialize_compose_runtime
from cage.target.server.schemas import ServiceInfo


@pytest.fixture(autouse=True)
def _clean_registry():
    with ss.running_instances_lock:
        ss.running_instances.clear()
    yield
    with ss.running_instances_lock:
        ss.running_instances.clear()


@pytest.fixture
def external_access(monkeypatch):
    """Server started with ``--public-host`` (address derived per request)."""
    monkeypatch.setattr(ss, "PUBLIC_HOST", pa.PUBLIC_HOST_AUTO, raising=False)
    monkeypatch.setattr(ss, "HOST_IP", "127.0.0.1", raising=False)
    monkeypatch.setattr(ss, "MAX_PUBLIC_INSTANCES", 1, raising=False)


def _service(**over):
    base = dict(
        service_name="web", alias="web", ip="1.2.3.4", inner_ip="172.30.0.5",
        inner_host="web", inner_port=80, internal_port=80,
        external_port=32101, external_host="0.0.0.0",
        host="0.0.0.0", port=32101, protocol="tcp",
    )
    base.update(over)
    return ServiceInfo(**base)


def _instance(**over):
    base = {
        "chal_id": "SIYUCMS", "run_id": "run-01", "project_name": "p",
        "network_name": "n", "network_subnet": "172.30.0.0/24",
        "services": [_service()], "entry_service_keys": ["web"],
        "lifecycle_state": "running", "target_scope": "per_agent",
        "audience": "external", "public_intent": True,
        "external_ports": {"web": 32101},
        "created_at": time.time() - 60,
    }
    base.update(over)
    return base


# --------------------------------------------------------------------------- #
# Mode switch: who gets a host port by default
# --------------------------------------------------------------------------- #

def test_mode_is_off_unless_operator_turns_it_on(monkeypatch):
    monkeypatch.setattr(ss, "PUBLIC_HOST", "", raising=False)
    assert pa.external_access_enabled() is False
    # Off: every launch keeps network-only isolation by default.
    assert pa.default_network_only() is True


def test_mode_flips_the_default_to_publish_for_every_launch(external_access):
    # Publishing is a property of the SERVER, not of who is calling. On a
    # --public-host server the network_only default flips to False for every
    # launch — loopback callers included — because such a server is dedicated
    # to serving off-host agents.
    assert pa.external_access_enabled() is True
    assert pa.default_network_only() is False


def test_publishing_is_keyed_on_server_flag_not_on_caller_or_auth(external_access):
    # Neither the caller's address nor the external token decides publishing.
    # The token only gates who may call the API. cage run is unaffected because
    # its embedded server never sets --public-host, so external_access_enabled()
    # is False there and its default stays network-only.
    assert pa.external_access_enabled() is True
    assert pa.default_network_only() is False        # every launch publishes
    monkeypatch_off = pa._server_state
    # (sanity) with the flag cleared, back to network-only for everyone
    prev = monkeypatch_off.PUBLIC_HOST
    try:
        monkeypatch_off.PUBLIC_HOST = ""
        assert pa.default_network_only() is True
    finally:
        monkeypatch_off.PUBLIC_HOST = prev


# --------------------------------------------------------------------------- #
# Publishing scope: only declared entries reach the host
# --------------------------------------------------------------------------- #

def _spec(tmp_path, *, exposure_mode="host_ports"):
    from cage.target.adapters.base import LaunchSpec

    compose = tmp_path / "docker-compose.yml"
    compose.write_text(
        "services:\n"
        "  web:\n    image: nginx\n    ports:\n      - '80'\n"
        "  evaluator:\n    image: eval\n"
        "  inner_db:\n    image: db\n",
        encoding="utf-8",
    )
    return LaunchSpec(
        mode="compose",
        compose_files=[str(compose)],
        working_directory=str(tmp_path),
        target_services=["web", "evaluator", "inner_db"],
        dependency_services=[],
        exposure_mode=exposure_mode,
        runtime_patches={
            "target_ports": {"web": 80, "evaluator": 9091, "inner_db": 3306},
            "parallel_mode": "network",
        },
    )


def _materialize(tmp_path, **kwargs):
    ports = iter(range(32101, 32200))
    return materialize_compose_runtime(
        spec=_spec(tmp_path, exposure_mode=kwargs.pop("exposure_mode", "host_ports")),
        project_name="cage_bench_default_x_runtime",
        docker_network="cage_bench_default",
        host_ip="127.0.0.1",
        runtime_compose_path=tmp_path / "runtime.yml",
        find_free_port_fn=lambda: next(ports),
        existing_external_ports=None,
        entry_service_keys={"web"},
        **kwargs,
    )


def test_entry_only_publishes_the_entry_and_nothing_else(tmp_path):
    plan = _materialize(tmp_path, audience="external", network_only=False,
                        publish_scope="entry_only")
    assert set(plan.external_ports) == {"web"}
    assert plan.public_service_names == ["web"]
    # The scoring sidecar and the inner database get no host port at all —
    # not even a 127.0.0.1 one.
    assert "ports" not in plan.config["services"]["evaluator"]
    assert "ports" not in plan.config["services"]["inner_db"]
    assert plan.config["services"]["web"]["ports"] == ["0.0.0.0:32101:80"]


def test_entry_only_overrides_a_range_declaring_exposure_internal(tmp_path):
    # ``exposure_mode: internal`` means "do not spill this whole topology onto
    # the host" — the entry point is still the way in, so external-access mode
    # publishes it. Every other service stays unpublished.
    plan = _materialize(tmp_path, exposure_mode="internal", audience="external",
                        network_only=False, publish_scope="entry_only")
    assert set(plan.external_ports) == {"web"}
    assert "ports" not in plan.config["services"]["inner_db"]


def test_declared_scope_is_unchanged_by_this_feature(tmp_path):
    # Default publish_scope: network_only still suppresses everything, and an
    # ``internal`` range still publishes nothing.
    plan = _materialize(tmp_path, audience="external", network_only=True,
                        publish_scope="declared")
    assert plan.external_ports == {}
    plan = _materialize(tmp_path, exposure_mode="internal", audience="external",
                        network_only=False, publish_scope="declared")
    assert plan.external_ports == {}


# --------------------------------------------------------------------------- #
# Advertised address
# --------------------------------------------------------------------------- #

def test_address_is_derived_from_the_address_the_caller_reached_us_at(external_access):
    host, source = pa.resolve_public_host("98.92.103.202:8000")
    assert (host, source) == ("98.92.103.202", pa.SOURCE_HOST_HEADER)
    # A different caller on the same server gets its own correct address.
    assert pa.resolve_public_host("range.example.com:8000")[0] == "range.example.com"


def test_pinned_address_wins_over_derivation(monkeypatch):
    monkeypatch.setattr(ss, "PUBLIC_HOST", "1.2.3.4", raising=False)
    assert pa.resolve_public_host("attacker.example.com:8000") == ("1.2.3.4", pa.SOURCE_FLAG)


def test_legacy_host_ip_env_still_honoured(monkeypatch):
    monkeypatch.setattr(ss, "PUBLIC_HOST", pa.PUBLIC_HOST_AUTO, raising=False)
    monkeypatch.setattr(ss, "HOST_IP", "192.0.2.10", raising=False)
    assert pa.resolve_public_host("whatever:8000") == ("192.0.2.10", pa.SOURCE_HOST_IP_ENV)


def test_ipv6_host_header_keeps_its_brackets(external_access):
    assert pa.host_from_header("[2001:db8::1]:8000") == "[2001:db8::1]"


def test_instances_advertises_the_callers_own_address(external_access, monkeypatch):
    monkeypatch.setattr(ss, "EXTERNAL_TOKEN", "tok", raising=False)
    ss.set_running_instance("run-01", _instance())
    client = TestClient(cs.app)
    r = client.get(
        "/instances",
        headers={"Authorization": "Bearer tok", "Host": "range.example.com:8000"},
    )
    assert r.status_code == 200
    (summary,) = r.json()
    assert summary["entry_urls"][0]["url"] == "http://range.example.com:32101"
    assert summary["entry_url_source"] == pa.SOURCE_HOST_HEADER
    assert summary["public"] is True


# --------------------------------------------------------------------------- #
# The briefing has to name a reachable address
# --------------------------------------------------------------------------- #

def test_prompt_rewrites_docker_addresses_to_published_ones():
    prompt = (
        "Attack the application at http://web:80/login.\n"
        "Its API docs are at http://web:80/doc.html\n"
    )
    out = pa.rewrite_targets_for_public_host(
        prompt, services=[_service()], entry_service_keys=["web"],
        public_host="98.92.103.202",
    )
    assert "http://98.92.103.202:32101/login" in out
    assert "http://98.92.103.202:32101/doc.html" in out
    assert "web:80" not in out


def test_prompt_rewrite_matches_inner_ip_form_too():
    # Post-exploitation briefings name live inner IPs, not aliases.
    out = pa.rewrite_targets_for_public_host(
        "Entry host: http://172.30.0.5:80/",
        services=[_service()], entry_service_keys=["web"], public_host="1.2.3.4",
    )
    assert out == "Entry host: http://1.2.3.4:32101/"


def test_prompt_rewrite_does_not_match_across_token_boundaries():
    # ``web:80`` must not match inside ``web:8080`` or ``myweb:80``.
    text = "http://web:8080/ and http://myweb:80/"
    out = pa.rewrite_targets_for_public_host(
        text, services=[_service()], entry_service_keys=["web"], public_host="1.2.3.4",
    )
    assert out == text


def test_prompt_rewrites_for_any_caller_when_the_instance_is_published(monkeypatch, external_access):
    # A published instance is reached at its host address by every agent, so the
    # briefing is rewritten regardless of who fetches /prompt — an off-host agent
    # AND the operator polling from the serve host both see the public address.
    ss.set_running_instance("run-01", _instance())            # public_intent=True
    monkeypatch.setattr(
        cs, "load_all_challenges",
        lambda: {"SIYUCMS": {"id": "SIYUCMS", "full_path": "/x"}},
    )
    monkeypatch.setattr(
        cs, "render_task_prompt",
        lambda *a, prompt_level="l0", public_host="": (f"host={public_host!r}", "tmpl"),
    )
    monkeypatch.setattr(ss, "EXTERNAL_TOKEN", "tok", raising=False)
    client = TestClient(cs.app)

    external = client.get(
        "/prompt/run-01",
        headers={"Authorization": "Bearer tok", "Host": "range.example.com:8000"},
    )
    assert external.json()["task_prompt"] == "host='range.example.com'"

    # On-host caller: its loopback Host header is not a usable advertised address,
    # so the resolver falls back to the server's route IP — NON-empty, and not
    # the docker-internal address.
    on_host = TestClient(cs.app, client=("127.0.0.1", 51000))
    body = on_host.get("/prompt/run-01", headers={"Host": "localhost:8000"}).json()
    assert body["task_prompt"] not in ("host=''", "host='localhost'", "host='127.0.0.1'")


def test_prompt_not_rewritten_for_a_network_only_instance(monkeypatch, external_access):
    # A network-only instance has no host port; its agent joins the docker
    # network, so the briefing must keep the internal addresses for everyone.
    ss.set_running_instance(
        "run-02", _instance(run_id="run-02", public_intent=False, external_ports={}),
    )
    monkeypatch.setattr(
        cs, "load_all_challenges",
        lambda: {"SIYUCMS": {"id": "SIYUCMS", "full_path": "/x"}},
    )
    monkeypatch.setattr(
        cs, "render_task_prompt",
        lambda *a, prompt_level="l0", public_host="": (f"host={public_host!r}", "tmpl"),
    )
    monkeypatch.setattr(ss, "EXTERNAL_TOKEN", "tok", raising=False)
    client = TestClient(cs.app)
    body = client.get(
        "/prompt/run-02",
        headers={"Authorization": "Bearer tok", "Host": "range.example.com:8000"},
    ).json()
    assert body["task_prompt"] == "host=''"


# --------------------------------------------------------------------------- #
# Public-instance cap + lease
# --------------------------------------------------------------------------- #

def test_second_public_launch_is_refused_with_the_occupant_named(external_access):
    ss.set_running_instance("run-01", _instance())
    with pytest.raises(Exception) as excinfo:
        launch_mod._enforce_public_instance_limit("range-2")
    detail = excinfo.value.detail
    assert excinfo.value.status_code == 409
    assert detail["error"] == "public_instance_limit_reached"
    assert detail["max_public_instances"] == 1
    # An agent that is merely queued must learn WHOSE instance holds the slot.
    (occupant,) = detail["occupants"]
    assert occupant["run_id"] == "run-01"
    assert occupant["chal_id"] == "SIYUCMS"
    assert occupant["uptime_s"] >= 60


def test_network_only_instances_do_not_consume_a_public_slot(external_access):
    # Co-located container agents can keep running in parallel: their targets
    # have no host port, so they are not mutually discoverable.
    ss.set_running_instance(
        "run-01", _instance(public_intent=False, external_ports={}),
    )
    launch_mod._enforce_public_instance_limit("range-2")  # does not raise


def test_slot_is_claimed_by_intent_before_any_port_exists(external_access):
    # The record a launch writes first has no ports yet; if the cap only looked
    # at external_ports, two concurrent launches would both pass.
    ss.set_running_instance(
        "run-01",
        {"chal_id": "c", "run_id": "run-01", "audience": "external",
         "public_intent": True, "lifecycle_state": "launching"},
    )
    with pytest.raises(Exception) as excinfo:
        launch_mod._enforce_public_instance_limit("c2")
    assert excinfo.value.status_code == 409


def test_cap_of_zero_means_unlimited(external_access, monkeypatch):
    monkeypatch.setattr(ss, "MAX_PUBLIC_INSTANCES", 0, raising=False)
    ss.set_running_instance("run-01", _instance())
    ss.set_running_instance("run-02", _instance(run_id="run-02"))
    launch_mod._enforce_public_instance_limit("range-3")  # does not raise


def test_lease_countdown_and_expiry():
    fresh = _instance(ttl_s=1800, created_at=time.time() - 300)
    remaining = pa.ttl_remaining_s(fresh)
    assert 1490 <= remaining <= 1500
    assert pa.instance_expired(fresh) is False

    expired = _instance(ttl_s=60, created_at=time.time() - 120)
    assert pa.ttl_remaining_s(expired) == 0.0
    assert pa.instance_expired(expired) is True

    # No lease requested → runs until deleted; never reaped.
    assert pa.ttl_remaining_s(_instance()) is None
    assert pa.instance_expired(_instance()) is False


def test_instances_endpoint_reports_the_remaining_lease(external_access):
    ss.set_running_instance("run-01", _instance(ttl_s=600, created_at=time.time() - 100))
    client = TestClient(cs.app)
    (summary,) = client.get("/instances", headers={"Host": "h.example:8000"}).json()
    assert summary["ttl_s"] == 600
    assert 495 <= summary["ttl_remaining_s"] <= 500


# --------------------------------------------------------------------------- #
# Submission upload cap
# --------------------------------------------------------------------------- #

def test_submit_rejects_an_oversized_upload(monkeypatch):
    # The body is read into memory to be unpacked, so it needs a ceiling.
    monkeypatch.setattr(ss, "MAX_SUBMIT_UPLOAD_BYTES", 1024, raising=False)
    monkeypatch.setattr(ss, "EXTERNAL_TOKEN", None, raising=False)
    ss.set_running_instance("pb-x_r1", {"chal_id": "pb-x", "services": []})
    monkeypatch.setattr(
        cs, "load_all_challenges", lambda: {"pb-x": {"id": "pb-x", "full_path": "/x"}}
    )
    scored = {"n": 0}
    monkeypatch.setattr(
        cs, "score_submission",
        lambda **kw: scored.__setitem__("n", scored["n"] + 1) or {
            "benchmark_module": "m", "scores": {}, "run_dir": "rd"},
    )
    client = TestClient(cs.app)
    r = client.post("/submit/pb-x_r1", files={"agent_output": ("big.tar.gz", b"x" * 5000)})
    assert r.status_code == 413
    assert "upload limit" in r.json()["detail"]
    assert scored["n"] == 0  # refused before any scoring work


def test_submit_accepts_a_normal_upload_under_the_cap(monkeypatch):
    monkeypatch.setattr(ss, "MAX_SUBMIT_UPLOAD_BYTES", 1024 * 1024, raising=False)
    monkeypatch.setattr(ss, "EXTERNAL_TOKEN", None, raising=False)
    ss.set_running_instance("pb-x_r2", {"chal_id": "pb-x", "services": []})
    monkeypatch.setattr(
        cs, "load_all_challenges", lambda: {"pb-x": {"id": "pb-x", "full_path": "/x"}}
    )
    monkeypatch.setattr(
        cs, "score_submission",
        lambda **kw: {"benchmark_module": "m", "scores": {"s": {"value": 1.0}}, "run_dir": "rd"},
    )
    # A real (tiny) archive: the cap must not disturb the normal path.
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w:gz") as tf:
        payload = json.dumps({"vuln_id": "v1"}).encode()
        member = tarfile.TarInfo("final_answer/v1.json")
        member.size = len(payload)
        tf.addfile(member, io.BytesIO(payload))
    client = TestClient(cs.app)
    r = client.post("/submit/pb-x_r2", files={"agent_output": ("ok.tar.gz", buf.getvalue())})
    assert r.status_code == 200
    assert r.json()["scores"]["s"]["value"] == 1.0


def test_public_instance_is_a_fact_about_ports_not_about_auth():
    # A token-less server publishes the same surface as a token-guarded one, so
    # "is this instance public" must not consult the launcher's audience —
    # otherwise the cap and the /prompt rewrite both silently skip it.
    token_less = _instance(audience="internal")
    assert pa.instance_is_public(token_less) is True
    assert pa.instance_is_public(
        _instance(audience="external", public_intent=False, external_ports={})
    ) is False


# --------------------------------------------------------------------------- #
# --public-host requires --external-token (control-plane exposure guard)
# --------------------------------------------------------------------------- #

def test_public_host_without_token_refuses_to_start():
    # Publishing target entries on the host also exposes the control API there,
    # so --public-host must be gated: the server refuses to start token-less.
    from cage.target import serve as serve_mod
    with pytest.raises(SystemExit):
        serve_mod.run_target_server(
            host="127.0.0.1", port=0, public_host="auto", external_token="",
        )


def test_public_host_with_token_passes_the_guard(monkeypatch):
    # With a token the guard passes and control reaches uvicorn.run. Stub it to
    # raise a sentinel so nothing ever binds a port, and let monkeypatch own the
    # env vars run_target_server writes so they are restored at teardown.
    import uvicorn

    class _ReachedUvicorn(Exception):
        pass

    def _boom(*a, **k):
        raise _ReachedUvicorn()

    for var in ("TARGET_SERVER_NAMESPACE", "TARGET_SERVER_EXTERNAL_TOKEN",
                "TARGET_SERVER_PUBLIC_HOST", "TARGET_SERVER_MAX_PUBLIC_INSTANCES"):
        monkeypatch.setenv(var, "")
    monkeypatch.setattr(uvicorn, "run", _boom)
    from cage.target import serve as serve_mod
    with pytest.raises(_ReachedUvicorn):   # got past the token guard, never bound
        serve_mod.run_target_server(
            host="127.0.0.1", port=0, namespace="guardtest",
            public_host="auto", external_token="tok",
        )


def test_cli_public_host_requires_token():
    from click.testing import CliRunner
    from cage.cli.commands.serve import serve
    res = CliRunner().invoke(serve, ["--public-host"])
    assert res.exit_code != 0
    assert "external-token" in res.output.lower()
