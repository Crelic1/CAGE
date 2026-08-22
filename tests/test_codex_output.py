"""Tests for Codex CLI JSON event stream parsing."""

from __future__ import annotations

import json
import stat
from pathlib import Path
from typing import Any

from cage.agents.codex import CodexAgent
from cage.agents.codex.output import parse_codex_event_stream
from cage.models import ModelConfig
from cage.sandbox.exec import ExecResult
from cage.scoring import ScoringContext


def _codex_stream(*events: dict) -> str:
    return "\n".join(json.dumps(event) for event in events)


def test_parse_codex_event_stream_extracts_last_agent_message() -> None:
    stream = _codex_stream(
        {"type": "thread.started", "thread_id": "thread-1"},
        {
            "type": "item.completed",
            "item": {"id": "item_0", "type": "agent_message", "text": "First update"},
        },
        {
            "type": "item.completed",
            "item": {"id": "item_1", "type": "agent_message", "text": "Final update"},
        },
        {
            "type": "turn.failed",
            "error": {"message": "unexpected status 503 Service Unavailable"},
        },
    )

    summary = parse_codex_event_stream(stream)

    assert summary.is_event_stream is True
    assert summary.last_agent_message == "Final update"
    assert summary.terminal_error == "unexpected status 503 Service Unavailable"
    assert summary.final_output() == "Final update"


def test_codex_agent_parse_output_uses_parsed_final_message() -> None:
    stream = _codex_stream(
        {"type": "thread.started", "thread_id": "thread-1"},
        {
            "type": "item.completed",
            "item": {"id": "item_0", "type": "agent_message", "text": "Mapped the target"},
        },
        {
            "type": "item.completed",
            "item": {"id": "item_1", "type": "agent_message", "text": "Retrieved flag3"},
        },
        {
            "type": "turn.failed",
            "error": {"message": "unexpected status 503 Service Unavailable"},
        },
    )

    output = CodexAgent().parse_output(
        ExecResult(command="codex exec", stdout=stream, stderr="", exit_code=1)
    )

    assert output == "Retrieved flag3"


def test_load_scorer_context_normalizes_legacy_codex_output(tmp_path: Path) -> None:
    trial_dir = tmp_path / "run-fixed" / "trials" / "range1"
    trial_dir.mkdir(parents=True)
    stream = _codex_stream(
        {"type": "thread.started", "thread_id": "thread-1"},
        {
            "type": "item.completed",
            "item": {"id": "item_0", "type": "agent_message", "text": "First step"},
        },
        {
            "type": "item.completed",
            "item": {"id": "item_1", "type": "agent_message", "text": "Second step"},
        },
    )
    (trial_dir / "task_output.json").write_text(
        json.dumps({"output": stream, "exit_code": 1, "sample": {}}),
        encoding="utf-8",
    )

    context = ScoringContext.from_trial_dir(trial_dir)

    assert context is not None
    assert context.output == "Second step"


class _FakeContainer:
    """Minimal stand-in for Container that records exec/write_file calls."""

    def __init__(self) -> None:
        self.exec_calls: list[str] = []
        self.files: dict[str, str] = {}
        self.volumes: dict[str, str] = {}

    def exec(self, cmd: str, *_: Any, **__: Any) -> Any:
        self.exec_calls.append(cmd)

        class _Result:
            exit_code = 0
            stdout = ""
            stderr = ""

        return _Result()

    def write_file(self, path: str, content: str) -> None:
        self.files[path] = content


def test_setup_container_seeds_codex_config_toml() -> None:
    """Static codex config must live in ~/.codex/config.toml (not -c flags),
    and must match the known-working provider shape: ``model``,
    ``model_provider = "cage"``, and a ``[model_providers.cage]`` block with
    ``wire_api = "responses"``.
    """
    container = _FakeContainer()
    model = ModelConfig(
        id="gpt5", provider="openai", model="gpt-5.5",
        api_key="sk-real-key", base_url="https://example.invalid/v1",
    )

    CodexAgent().setup_container(container, home_dir="/home/agent", model=model)

    cfg = container.files["/home/agent/.codex/config.toml"]
    assert 'model = "gpt-5.5"' in cfg
    assert 'model_provider = "cage"' in cfg
    assert 'approval_policy = "never"' in cfg
    assert 'sandbox_mode = "danger-full-access"' in cfg
    assert "[model_providers.cage]" in cfg
    assert 'wire_api = "responses"' in cfg
    # base_url is dynamic per-trial and MUST be omitted from the static config.
    assert "base_url" not in cfg

    auth = json.loads(container.files["/home/agent/.codex/auth.json"])
    assert auth == {"OPENAI_API_KEY": "sk-real-key"}


def test_build_launch_command_only_overrides_dynamic_base_url() -> None:
    """All static codex config moved to config.toml — launch command should
    carry only ``--model`` and the proxy URL override.
    """
    model = ModelConfig(id="gpt5", provider="openai", model="gpt-5.5")
    cmd = CodexAgent().build_launch_command(
        "hello", model=model, proxy_url="http://localhost:8877",
    )
    assert "--model gpt-5.5" in cmd
    assert '-c model_providers.cage.base_url="http://localhost:8877/v1"' in cmd
    # Static keys must NOT appear as -c overrides anymore.
    assert "-c model_provider=" not in cmd
    assert "-c model_providers.cage.name" not in cmd
    assert "-c model_providers.cage.wire_api" not in cmd
    assert "-c model_providers.cage.env_key" not in cmd


def test_oauth_launch_uses_proxy_root_and_no_api_key_env() -> None:
    model = ModelConfig(
        id="sol-sub",
        provider="openai",
        model="gpt-5.6-sol",
        auth_source="/host/codex-profile",
    )

    cmd = CodexAgent().build_launch_command(
        "hello", model=model, proxy_url="http://localhost:8877/",
    )
    env = CodexAgent().env_vars(
        proxy_url="http://localhost:8877",
        model=model,
    )

    assert '-c model_providers.cage.base_url="http://localhost:8877"' in cmd
    assert "http://localhost:8877/v1" not in cmd
    assert env == {}


def test_oauth_setup_requires_mount_and_uses_openai_auth() -> None:
    container = _FakeContainer()
    container.volumes["/host/auth.json"] = "/home/agent/.codex/auth.json:ro"
    model = ModelConfig(
        id="sol-sub",
        provider="openai",
        model="gpt-5.6-sol",
        auth_source="/host/codex-profile",
    )

    CodexAgent().setup_container(container, home_dir="/home/agent", model=model)

    cfg = container.files["/home/agent/.codex/config.toml"]
    assert 'requires_openai_auth = true' in cfg
    assert 'wire_api = "responses"' in cfg
    assert "env_key" not in cfg
    assert "/home/agent/.codex/auth.json" not in container.files
    assert all("chown -R" not in call for call in container.exec_calls)


def test_oauth_setup_fails_closed_without_prestart_mount() -> None:
    container = _FakeContainer()
    model = ModelConfig(
        id="sol-sub",
        provider="openai",
        model="gpt-5.6-sol",
        auth_source="/host/codex-profile",
    )

    try:
        CodexAgent().setup_container(container, home_dir="/home/agent", model=model)
    except RuntimeError as exc:
        assert "refusing to copy OAuth credentials" in str(exc)
    else:
        raise AssertionError("OAuth setup accepted a missing credential mount")


def test_oauth_resources_mount_only_auth_json_readonly(tmp_path: Path) -> None:
    auth_path = tmp_path / "auth.json"
    auth_path.write_text(
        json.dumps({
            "auth_mode": "chatgpt",
            "tokens": {
                "access_token": "fake-access",
                "refresh_token": "fake-refresh",
            },
        }),
        encoding="utf-8",
    )
    auth_path.chmod(0o600)
    model = ModelConfig(
        id="sol-sub",
        provider="openai",
        model="gpt-5.6-sol",
        auth_source=str(tmp_path),
    )

    agent = CodexAgent()
    agent.validate_auth(model)
    resources = agent.container_resources(home_dir="/home/agent", model=model)

    assert resources.volumes == {
        str(auth_path): "/home/agent/.codex/auth.json:ro",
    }
    assert resources.group_add == [str(auth_path.stat().st_gid)]
    mode = stat.S_IMODE(auth_path.stat().st_mode)
    assert mode & stat.S_IRGRP
    assert not mode & stat.S_IWGRP
    assert ".codex" not in agent.state_paths
    assert all("auth.json" not in path for path in agent.state_paths)


def test_oauth_refresher_service_is_profile_scoped(tmp_path: Path) -> None:
    auth_path = tmp_path / "auth.json"
    auth_path.write_text(
        json.dumps({
            "tokens": {
                "access_token": "fake-access",
                "refresh_token": "fake-refresh",
            },
        }),
        encoding="utf-8",
    )
    model = ModelConfig(
        id="sol-sub",
        provider="openai",
        model="gpt-5.6-sol",
        auth_source=str(tmp_path),
    )

    service = CodexAgent().host_run_services(model)[0]

    assert service.name == "codex-oauth-refresh"
    assert service.dedup_key == str(auth_path)
    assert service.argv[service.argv.index("--creds") + 1] == str(auth_path)


def test_codex_ignores_claude_code_specific_model_alias() -> None:
    container = _FakeContainer()
    model = ModelConfig(
        id="deepseek-v4-pro",
        provider="openai",
        model="deepseek-v4-pro",
        api_key="sk-test",
        base_url="https://api.deepseek.com/v1",
        agent_model_names={"claude_code": "deepseek-v4-pro[1m]"},
    )

    cmd = CodexAgent().build_launch_command(
        "hello",
        model=model,
        proxy_url="http://localhost:8877",
    )
    CodexAgent().setup_container(container, home_dir="/home/agent", model=model)

    assert "--model deepseek-v4-pro" in cmd
    assert "[1m]" not in cmd
    assert 'model = "deepseek-v4-pro"' in container.files["/home/agent/.codex/config.toml"]
    assert "[1m]" not in container.files["/home/agent/.codex/config.toml"]
