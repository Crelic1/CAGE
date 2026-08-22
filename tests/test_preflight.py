from __future__ import annotations

from types import SimpleNamespace

from cage.contracts.logging import LoggingConfig
from cage.experiment.engine import preflight


def test_run_preflight_terminal_ui_prints_plain_status(capsys):
    config = SimpleNamespace(
        agents=[],
        metadata={},
        logging=LoggingConfig(terminal_ui=True),
    )

    result = preflight.run_preflight(config)

    output = capsys.readouterr().err
    assert result.passed == 0
    assert "Pre-flight checks" in output
    assert "Ready: 0 passed, 0 warnings" in output
    assert "[info" not in output
    assert "PRE-FLIGHT CHECKS" not in output


def test_run_preflight_terminal_ui_can_emit_ansi_color(capsys, monkeypatch):
    monkeypatch.setenv("CAGE_COLOR", "always")
    config = SimpleNamespace(
        agents=[],
        metadata={},
        logging=LoggingConfig(terminal_ui=True),
    )

    preflight.run_preflight(config)

    output = capsys.readouterr().err
    assert "\033[" in output
    assert "Pre-flight checks" in output
    assert "Ready: 0 passed, 0 warnings" in output


def test_run_preflight_skips_model_chain_when_zero_rounds(monkeypatch):
    calls: list[str] = []

    def fake_check_image(_image, result):
        calls.append("image")
        preflight._pass("Docker image", result)

    def fake_check_container_boot(_image, _network_mode, result):
        calls.append("boot")
        preflight._pass("Container boot", result)

    def fail_model_chain(*_args, **_kwargs):
        raise AssertionError("zero-round runs must not probe the model")

    model = SimpleNamespace(
        base_url="http://127.0.0.1:1/v1",
        api_key="test-key",
        protocol="openai",
        model="demo-model",
        id="demo",
        auth_source="",
    )
    agent = SimpleNamespace(
        effective_image="demo-image",
        model=model,
        max_rounds=-1,
        agent_type=SimpleNamespace(name="codex"),
    )
    config = SimpleNamespace(
        agents=[agent],
        metadata={},
        logging=LoggingConfig(terminal_ui=True),
        execution=SimpleNamespace(agent_network_mode="bridge", max_rounds=0),
        proxy=SimpleNamespace(enabled=True, upstream_http_proxy=""),
    )

    monkeypatch.setattr(preflight, "_check_image", fake_check_image)
    monkeypatch.setattr(preflight, "_check_container_boot", fake_check_container_boot)
    monkeypatch.setattr(preflight, "_check_agent_chain", fail_model_chain)
    monkeypatch.setattr(preflight, "_check_model_api", fail_model_chain)

    result = preflight.run_preflight(config, samples=[{"id": "sample", "max_rounds": 150}])

    assert calls == ["image", "boot"]
    assert result.failed == 0
    assert result.warnings == 1
    assert any("max_rounds=0" in detail for detail in result.details)


def test_image_preflight_reports_a_genuinely_missing_image(monkeypatch):
    monkeypatch.setattr(
        preflight,
        "_run_cmd",
        lambda *_args, **_kwargs: (
            1,
            "",
            "Error response from daemon: No such image: demo:latest",
        ),
    )
    result = preflight.PreflightResult()

    preflight._check_image("demo:latest", result)

    assert result.failed == 1
    assert "Not found. Run: cage agent build" in result.details[0]


def test_image_preflight_does_not_misreport_docker_timeout_as_missing(monkeypatch):
    monkeypatch.setattr(
        preflight,
        "_run_cmd",
        lambda *_args, **_kwargs: (-1, "", "timeout"),
    )
    monkeypatch.setattr(preflight.time, "sleep", lambda _seconds: None)
    result = preflight.PreflightResult()

    preflight._check_image("demo:latest", result)

    assert result.failed == 1
    assert "Docker inspect unavailable: timeout" in result.details[0]
    assert "does not prove the image is missing" in result.details[0]
    assert "cage agent build" not in result.details[0]
    assert "after 3 attempts" in result.details[0]


def test_image_preflight_retries_transient_timeout_then_passes(monkeypatch):
    inspect_count = 0

    def fake_run_cmd(cmd, timeout=None):
        nonlocal inspect_count
        assert cmd[:3] == ["docker", "image", "inspect"]
        assert timeout == preflight.PREFLIGHT_IMAGE_INSPECT_TIMEOUT
        inspect_count += 1
        if inspect_count == 1:
            return -1, "", "timeout"
        return 0, "[]", ""

    monkeypatch.setattr(preflight, "_run_cmd", fake_run_cmd)
    monkeypatch.setattr(preflight.time, "sleep", lambda _seconds: None)
    result = preflight.PreflightResult()

    preflight._check_image("demo:latest", result)

    assert inspect_count == 2
    assert result.failed == 0
    assert result.passed == 1
    assert "attempt=2/3" in result.details[0]


def test_image_preflight_preserves_other_daemon_errors(monkeypatch):
    monkeypatch.setattr(
        preflight,
        "_run_cmd",
        lambda *_args, **_kwargs: (125, "", "daemon is shutting down"),
    )
    monkeypatch.setattr(preflight.time, "sleep", lambda _seconds: None)
    result = preflight.PreflightResult()

    preflight._check_image("demo:latest", result)

    assert result.failed == 1
    assert "docker exit 125" in result.details[0]
    assert "daemon is shutting down" in result.details[0]
    assert "cage agent build" not in result.details[0]


def test_container_boot_failure_attempts_exact_cleanup(monkeypatch):
    commands: list[list[str]] = []

    def fake_run_cmd(cmd, timeout=None):
        commands.append(cmd)
        if cmd[:3] == ["docker", "run", "-d"]:
            return -1, "", "timeout"
        return 0, "", ""

    monkeypatch.setattr(preflight, "_run_cmd", fake_run_cmd)
    monkeypatch.setattr(preflight.time, "sleep", lambda _seconds: None)
    result = preflight.PreflightResult()

    preflight._check_container_boot("demo:latest", "bridge", result)

    docker_runs = [cmd for cmd in commands if cmd[:3] == ["docker", "run", "-d"]]
    assert len(docker_runs) == preflight.PREFLIGHT_CONTAINER_BOOT_ATTEMPTS
    container_names = [cmd[cmd.index("--name") + 1] for cmd in docker_runs]
    assert len(set(container_names)) == len(container_names)
    for container_name in container_names:
        assert commands.count(["docker", "rm", "-f", container_name]) == 2
    assert result.failed == 1
    assert all(container_name in result.details[0] for container_name in container_names)
    assert "timeout" in result.details[0]


def test_container_boot_retries_transient_timeout_then_passes(monkeypatch):
    commands: list[list[str]] = []
    run_count = 0

    def fake_run_cmd(cmd, timeout=None):
        nonlocal run_count
        commands.append(cmd)
        if cmd[:3] == ["docker", "run", "-d"]:
            run_count += 1
            if run_count == 1:
                return -1, "", "timeout"
            return 0, "container-id", ""
        return 0, "", ""

    monkeypatch.setattr(preflight, "_run_cmd", fake_run_cmd)
    monkeypatch.setattr(preflight.time, "sleep", lambda _seconds: None)
    result = preflight.PreflightResult()

    preflight._check_container_boot("demo:latest", "bridge", result)

    assert run_count == 2
    assert result.failed == 0
    assert result.passed == 1
    assert "attempt=2/3" in result.details[0]


def test_container_boot_does_not_retry_deterministic_failure(monkeypatch):
    commands: list[list[str]] = []

    def fake_run_cmd(cmd, timeout=None):
        commands.append(cmd)
        if cmd[:3] == ["docker", "run", "-d"]:
            return 125, "", "network demo not found"
        return 0, "", ""

    monkeypatch.setattr(preflight, "_run_cmd", fake_run_cmd)
    result = preflight.PreflightResult()

    preflight._check_container_boot("demo:latest", "demo", result)

    docker_runs = [cmd for cmd in commands if cmd[:3] == ["docker", "run", "-d"]]
    assert len(docker_runs) == 1
    assert result.failed == 1
    assert "network demo not found" in result.details[0]


def test_proxy_chain_uses_configured_upstream_http_proxy(monkeypatch):
    docker_runs: list[list[str]] = []
    copied_config: dict[str, object] = {}
    container_name = ""

    def fake_run_cmd(cmd, timeout=None):
        nonlocal container_name
        if cmd[:3] == ["docker", "run", "-d"]:
            docker_runs.append(cmd)
            container_name = cmd[cmd.index("--name") + 1]
            return 0, "container-id", ""
        if cmd[:3] == ["docker", "rm", "-f"]:
            return 0, "", ""
        if cmd[:2] == ["docker", "cp"] and cmd[3] == f"{container_name}:/tmp/pc.json":
            import json
            from pathlib import Path

            copied_config.update(json.loads(Path(cmd[2]).read_text(encoding="utf-8")))
            return 0, "", ""
        if cmd[:3] == ["docker", "exec", container_name]:
            if cmd[-1].endswith("/healthz"):
                return 0, "ok", ""
            return 0, "", ""
        return 0, "", ""

    def fake_sleep(_seconds):
        return None

    model = SimpleNamespace(
        base_url="http://example.invalid/v1",
        api_key="test-key",
        protocol="openai",
        model="demo-model",
        id="demo",
    )
    result = preflight.PreflightResult()

    monkeypatch.setattr(preflight.time, "time", lambda: 12345)
    monkeypatch.setattr(preflight, "_run_cmd", fake_run_cmd)
    monkeypatch.setattr(preflight.time, "sleep", fake_sleep)

    preflight._check_proxy_chain(
        "demo-image",
        model,
        "bridge",
        result,
        upstream_http_proxy="http://host.docker.internal:7890",
    )

    assert docker_runs, "expected docker run to be invoked"
    assert "--add-host" in docker_runs[0]
    assert "host.docker.internal:host-gateway" in docker_runs[0]
    assert copied_config["http_proxy"] == "http://host.docker.internal:7890"


def test_validate_proxy_response_detects_proxy_error_body():
    # Real failure body from container_proxy.py on DNS / upstream failure.
    body = (
        '{"error": {"message": "[Errno -2] Name or service not known", '
        '"type": "proxy_error"}}'
    )
    ok, reason = preflight._validate_proxy_response(body, curl_exit=0)
    assert ok is False
    assert "Name or service not known" in reason


def test_validate_proxy_response_detects_upstream_error_body():
    # Real failure body from zai/bigmodel.cn upstream returning HTTP 400.
    body = '{"error": {"message": "Bad request", "code": 400}}'
    ok, reason = preflight._validate_proxy_response(body, curl_exit=0)
    assert ok is False
    assert "Bad request" in reason


def test_validate_proxy_response_accepts_real_completion():
    body = (
        '{"id": "cmpl-1", "choices": [{"message": '
        '{"role": "assistant", "content": "hi"}}], "model": "x"}'
    )
    ok, reason = preflight._validate_proxy_response(body, curl_exit=0)
    assert ok is True
    assert reason == ""


def test_validate_proxy_response_rejects_curl_failure():
    ok, reason = preflight._validate_proxy_response("", curl_exit=7)
    assert ok is False
    assert "curl" in reason


def test_validate_proxy_response_rejects_non_json():
    ok, reason = preflight._validate_proxy_response("upstream is down", curl_exit=0)
    assert ok is False
    assert "Non-JSON" in reason or "Empty" in reason


def test_validate_proxy_response_accepts_sse_stream():
    # Real /v1/responses SSE shape from a codex-relay endpoint.
    body = (
        'data: {"type": "response.created", "response": {"id": "resp_1"}}\n\n'
        'data: {"type": "response.output_text.delta", "delta": "hi"}\n\n'
        'data: {"type": "response.completed"}\n\n'
        'data: [DONE]\n\n'
    )
    ok, reason = preflight._validate_proxy_response(body, curl_exit=0)
    assert ok is True, reason


def test_validate_proxy_response_rejects_sse_error_event():
    body = (
        'data: {"type": "response.created", "response": {"id": "resp_1"}}\n\n'
        'data: {"type": "error", "error": '
        '{"message": "Stream must be set to true", "code": 400}}\n\n'
    )
    ok, reason = preflight._validate_proxy_response(body, curl_exit=0)
    assert ok is False
    assert "Stream must be set to true" in reason


def test_validate_proxy_response_rejects_sse_with_no_events():
    body = "data: \n\ndata: [DONE]\n\n"
    ok, reason = preflight._validate_proxy_response(body, curl_exit=0)
    assert ok is False
    assert "no parseable events" in reason


# ---------------------------------------------------------------------------
# agent → proxy → model chain check
# ---------------------------------------------------------------------------


def test_chain_result_summary_says_how_far_it_got():
    """A failure report is only useful if it says which link broke."""
    from cage.experiment.engine.agent_chain import ChainCheckResult

    ok = ChainCheckResult(
        ok=True, stage="ok", detail="reply received",
        reached=["container", "agent setup", "proxy", "model reply"],
    )
    assert "OK" in ok.summary()
    assert "model reply" in ok.summary()

    bad = ChainCheckResult(
        ok=False, stage="agent run", detail="agent CLI exited 1: bad config",
        reached=["container", "agent setup", "proxy"],
    )
    assert "agent run" in bad.summary()
    assert "bad config" in bad.summary()
    assert "reached: container, agent setup, proxy" in bad.summary()


def test_chain_fingerprint_changes_with_the_things_that_matter(monkeypatch):
    """Cache identity must move when the image or the model config moves.

    Keyed on the image's content id rather than its tag: a rebuilt ``:latest``
    carries a different agent CLI, and a cache keyed on the tag would keep
    vouching for a version that no longer exists.
    """
    from types import SimpleNamespace

    from cage.experiment.engine import preflight
    from cage.models import ModelConfig

    image_id = {"value": "sha256:aaa"}
    monkeypatch.setattr(
        preflight, "_run_cmd",
        lambda *a, **k: (0, image_id["value"], ""),
    )
    agent = SimpleNamespace(
        effective_image="cage/kimi-code:latest",
        agent_type=SimpleNamespace(name="kimi_code"),
        version="", home="/home/agent/workspace", plugins=[], skill="",
        context_compaction_threshold=None,
    )
    model = ModelConfig(id="m", provider="vllm", model="m", max_context_size=1000)

    def fp(m=model):
        return preflight._agent_chain_fingerprint(
            agent=agent, model=m, network_mode="host", upstream_http_proxy="",
        )

    base = fp()
    assert base

    image_id["value"] = "sha256:bbb"          # image rebuilt under the same tag
    assert fp() != base
    image_id["value"] = "sha256:aaa"
    assert fp() == base

    from dataclasses import replace as _replace
    assert fp(_replace(model, max_context_size=2000)) != base   # config changed
    assert fp(_replace(model, base_url="http://other")) != base


def test_chain_fingerprint_is_empty_when_the_image_cannot_be_resolved(monkeypatch):
    """No fingerprint ⇒ never cached ⇒ the check simply always runs."""
    from types import SimpleNamespace

    from cage.experiment.engine import preflight
    from cage.models import ModelConfig

    monkeypatch.setattr(preflight, "_run_cmd", lambda *a, **k: (1, "", "no such image"))
    agent = SimpleNamespace(
        effective_image="nope:latest", agent_type=SimpleNamespace(name="x"),
        version="", home="", plugins=[], skill="", context_compaction_threshold=None,
    )
    assert preflight._agent_chain_fingerprint(
        agent=agent, model=ModelConfig(id="m", provider="vllm", model="m"),
        network_mode=None, upstream_http_proxy="",
    ) == ""


def test_chain_cache_roundtrips_and_only_hits_on_the_same_fingerprint(tmp_path, monkeypatch):
    from cage.experiment.engine import preflight

    monkeypatch.setattr(
        preflight, "_chain_check_cache_path", lambda: tmp_path / "chain.json",
    )
    assert preflight._chain_check_is_cached("abc") is False
    preflight._remember_chain_check("abc")
    assert preflight._chain_check_is_cached("abc") is True
    assert preflight._chain_check_is_cached("def") is False


def test_upstream_failure_names_the_endpoint_and_the_proxy_setting():
    """"Connection refused" is a symptom with no address attached.

    The endpoint, the protocol and whether an HTTP proxy was in play are all
    values Cage itself chose, so naming them is not knowledge-duplication — and
    a missing `--upstream-proxy` is one of the most common causes of an
    otherwise-inscrutable upstream failure.
    """
    from cage.experiment.engine.agent_chain import _upstream_failure_detail
    from cage.models import ModelConfig

    model = ModelConfig(
        id="m", provider="vllm", model="m",
        base_url="https://api.example.com/v1",
    )
    records = [{
        "status": "error",
        "upstream_status_code": 401,
        "error_text": 'HTTP 401: {"error":{"type":"authentication_error",'
                      '"message":"invalid api key"}}',
    }]

    detail = _upstream_failure_detail(records, model=model, upstream_http_proxy="")
    assert "model_auth_error" in detail           # classified, not raw
    assert "https://api.example.com/v1" in detail  # which endpoint
    assert "no HTTP proxy configured" in detail    # the common gotcha

    via = _upstream_failure_detail(
        records, model=model, upstream_http_proxy="http://10.0.0.1:7890",
    )
    assert "via HTTP proxy http://10.0.0.1:7890" in via


def test_upstream_failure_without_a_parsable_reply_still_says_where():
    from cage.experiment.engine.agent_chain import _upstream_failure_detail
    from cage.models import ModelConfig

    detail = _upstream_failure_detail(
        [{"status": "ok"}],
        model=ModelConfig(id="m", provider="vllm", model="m", base_url="http://u/v1"),
        upstream_http_proxy="",
    )
    assert "no upstream reply was recorded" in detail
    assert "http://u/v1" in detail


def test_chain_ping_runs_the_same_command_a_trial_would():
    """The check must append ``session_args``, exactly as the trial runner does.

    Regression: it did not, so claude-code's ``--output-format stream-json``
    (which requires a ``--verbose`` that only ``session_args`` supplies) failed
    for a reason the user's config had nothing to do with. A check that runs a
    command no trial ever runs reintroduces the very drift it exists to remove.
    """
    from types import SimpleNamespace

    from cage.experiment.engine import agent_chain
    from cage.models import ModelConfig
    from cage.sandbox.exec import ExecResult

    seen: dict[str, str] = {}

    class _Container:
        def exec(self, command, **kwargs):
            if command.startswith("cat "):          # proxy-log read
                return ExecResult(command=command, stdout="", stderr="", exit_code=0,
                                  duration_ms=1)
            seen["command"] = command
            return ExecResult(command=command, stdout="CAGE_OK", stderr="",
                              exit_code=0, duration_ms=1)

    agent_type = SimpleNamespace(
        name="fake",
        supports_stdin_prompt=False,
        env_vars=lambda **kw: {"FOO": "bar"},
        build_launch_command=lambda prompt, **kw: "fakecli --print",
        parse_output=lambda result: result.stdout,
    )
    agent = SimpleNamespace(
        agent_type=agent_type,
        home="/home/agent/workspace",
        session_args=["--verbose", "--flag with space"],
        context_compaction_threshold=None,
    )

    outcome = agent_chain._run_agent_ping(
        _Container(),
        agent=agent,
        model=ModelConfig(id="m", provider="vllm", model="m"),
        proxy=SimpleNamespace(base_url="http://localhost:1234", log_dir="/tmp/p"),
        upstream_http_proxy="",
        timeout_s=5.0,
    )

    assert outcome.ok
    assert "fakecli --print" in seen["command"]
    assert "--verbose" in seen["command"]
    assert "'--flag with space'" in seen["command"]   # quoted, like the runner does
    assert "FOO='bar'" in seen["command"]


def test_chain_check_attaches_agent_resources_before_container_start(monkeypatch):
    """Subscription credentials are pre-start mounts, just like real trials."""
    from types import SimpleNamespace

    from cage.agents.base import AgentContainerResources
    from cage.experiment.engine import agent_chain
    from cage.models import ModelConfig

    seen = {}
    model = ModelConfig(
        id="subscription",
        provider="openai",
        model="model",
        auth_source="/host",
    )

    class _AgentType:
        default_image = "agent-image"
        name = "fake-subscription-agent"
        subscription_upstream_base_url = "https://subscription.example/backend"

        def container_resources(self, *, home_dir, model):
            assert home_dir == "/home/agent"
            assert model.id == "subscription"
            return AgentContainerResources(
                volumes={
                    "/host/auth.json": "/home/agent/.codex/auth.json:ro",
                },
                group_add=["1002"],
                privileged=True,
            )

        def setup_container(self, container, *, home_dir, model):
            assert container.volumes == {
                "/host/auth.json": "/home/agent/.codex/auth.json:ro",
            }

    class _Container:
        def __init__(self, **kwargs):
            seen.update(kwargs)
            self.volumes = kwargs["volumes"]

        def start(self):
            seen["started"] = True

        def setup_workspace(self, home):
            seen["workspace"] = home

        def stop(self):
            seen["stopped"] = True

    class _Proxy:
        def stop(self):
            seen["proxy_stopped"] = True

    expected = agent_chain.ChainCheckResult(
        ok=True,
        stage="ok",
        reached=["container", "agent setup", "proxy", "model reply"],
    )
    monkeypatch.setattr(agent_chain, "Container", _Container)
    def _start_proxy(container, config):
        seen["upstream_base_url"] = config.upstream_base_url
        return _Proxy()

    monkeypatch.setattr(agent_chain, "start_container_proxy", _start_proxy)
    monkeypatch.setattr(agent_chain, "_run_agent_ping", lambda *a, **kw: expected)

    agent = SimpleNamespace(
        model=model,
        image="",
        agent_type=_AgentType(),
        home="/home/agent/workspace",
    )
    outcome = agent_chain.check_agent_model_chain(agent)

    assert outcome is expected
    assert seen["volumes"] == {
        "/host/auth.json": "/home/agent/.codex/auth.json:ro",
    }
    assert seen["group_add"] == ["1002"]
    assert seen["privileged"] is True
    assert seen["upstream_base_url"] == "https://subscription.example/backend"
    assert seen["started"] is True
    assert seen["stopped"] is True
