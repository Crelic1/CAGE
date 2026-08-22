"""The task prompt must not sit in the agent's own command line.

An agent launched as ``cli -p '<the whole prompt>'`` keeps that prompt in its
``/proc/<pid>/cmdline`` for the whole trial. Agents routinely run
``pkill -f <pattern>`` to clean up something they started, and the pattern is
usually a phrase the prompt also contains (a port, a service name, a target
host) — so the sweep matches the agent's own process and the agent kills its
own session. Delivering the prompt on stdin removes the self-match.
"""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from cage.agents.claude_code.agent import ClaudeCodeAgent
from cage.agents.codex.agent import CodexAgent
from cage.agents.custom.agent import CustomAgent
from cage.agents.gemini_cli.agent import GeminiCliAgent
from cage.agents.hermes.agent import HermesAgent
from cage.agents.kimi_code.agent import KimiCodeAgent
from cage.agents.qwen_code.agent import QwenCodeAgent
from cage.experiment.engine.trial_runner import (
    STDIN_PROMPT_PATH,
    _append_session_args,
    _redirect_stdin,
    _stage_stdin_prompt,
    _stdin_prompt_path,
)
from cage.models import ModelConfig

#: Contains a phrase an agent would plausibly ``pkill -f`` on.
PROMPT = "Exploit the target. Clean up with pkill -f http.server when done."

STDIN_AGENTS = [
    ClaudeCodeAgent,
    CodexAgent,
    GeminiCliAgent,
    KimiCodeAgent,
    QwenCodeAgent,
]


def _model() -> ModelConfig:
    return ModelConfig(
        id="m", provider="vllm", model="test-model",
        base_url="http://localhost:8000/v1", api_key="k",
    )


@pytest.mark.parametrize("agent_cls", STDIN_AGENTS, ids=lambda c: c.name)
def test_stdin_prompt_keeps_the_prompt_out_of_argv(agent_cls) -> None:
    """The prompt is what ``pkill -f`` matches on — it must not be in argv."""
    command = agent_cls().build_launch_command(
        PROMPT, model=_model(), max_rounds=5, proxy_url="http://localhost:1/v1",
        stdin_prompt=True,
    )
    assert PROMPT not in command
    assert "http.server" not in command
    # Still a runnable invocation of the right CLI, not an empty string.
    assert command.split()[0]


@pytest.mark.parametrize("agent_cls", STDIN_AGENTS, ids=lambda c: c.name)
def test_argv_delivery_is_unchanged_by_default(agent_cls) -> None:
    """Default stays argv: only a caller that redirects stdin may drop it."""
    command = agent_cls().build_launch_command(
        PROMPT, model=_model(), max_rounds=5, proxy_url="http://localhost:1/v1",
    )
    assert PROMPT in command


@pytest.mark.parametrize("agent_cls", STDIN_AGENTS, ids=lambda c: c.name)
def test_stdin_agents_declare_support(agent_cls) -> None:
    """The declaration is what makes the framework stage the prompt file."""
    assert agent_cls.supports_stdin_prompt is True


@pytest.mark.parametrize("agent_cls", [HermesAgent, CustomAgent], ids=["hermes", "custom"])
def test_agents_without_stdin_support_do_not_declare_it(agent_cls) -> None:
    """``hermes chat`` reads its query only from ``-q``; custom is manifest-owned.

    Declaring support they do not have would launch them with no task at all.
    """
    assert agent_cls.supports_stdin_prompt is False


def test_claude_reads_positional_prompt_from_stdin() -> None:
    """``-p`` is a boolean flag; dropping the positional is what reads stdin."""
    command = ClaudeCodeAgent().build_launch_command(
        PROMPT, model=_model(), stdin_prompt=True,
    )
    assert command.startswith("claude -p --output-format stream-json")


def test_codex_uses_the_documented_stdin_marker() -> None:
    """``codex exec -`` is codex's documented "read instructions from stdin"."""
    command = CodexAgent().build_launch_command(
        PROMPT, model=_model(), stdin_prompt=True,
    )
    assert command.startswith("codex exec - --model ")


# --------------------------------------------------------------------------- #
# Framework side: staging the file and wiring it to stdin
# --------------------------------------------------------------------------- #


class _FakeContainer:
    """Records what the runner asks a container to do."""

    def __init__(self, *, fail_copy: bool = False) -> None:
        self.commands: list[str] = []
        self.copied: list[tuple[str, str]] = []
        self.fail_copy = fail_copy

    def exec(self, command, **kwargs):
        self.commands.append(command)
        return SimpleNamespace(command=command, stdout="", stderr="", exit_code=0)

    def copy_to(self, host_path, container_path):
        if self.fail_copy:
            raise RuntimeError("docker cp refused")
        self.copied.append((open(host_path, encoding="utf-8").read(), container_path))


def _agent(*, supports: bool) -> SimpleNamespace:
    return SimpleNamespace(agent_type=SimpleNamespace(supports_stdin_prompt=supports))


def test_staging_copies_the_prompt_without_putting_it_in_a_command() -> None:
    """``docker cp``, not a heredoc: even the staging command carries no prompt.

    ``Container.write_file`` would shell out ``cat > path << 'CAGE_EOF' …``,
    which puts the whole prompt into a command line — briefly, but for a
    long-running agent's own sweep that is still a live target.
    """
    container = _FakeContainer()
    path = _stage_stdin_prompt(container, PROMPT)

    assert path == STDIN_PROMPT_PATH
    assert container.copied == [(PROMPT, STDIN_PROMPT_PATH)]
    assert not any(PROMPT in command for command in container.commands)
    # Copied in as root; the agent runs unprivileged and must still read it.
    assert any("chown agent:agent" in command for command in container.commands)


def test_staging_lives_outside_the_workspace() -> None:
    """``reset_directory`` wipes the workspace and snapshots diff it."""
    assert not STDIN_PROMPT_PATH.startswith("/home/agent/workspace")


def test_no_staging_when_the_agent_cannot_read_stdin() -> None:
    container = _FakeContainer()
    assert _stdin_prompt_path(container, _agent(supports=False), PROMPT) == ""
    assert container.copied == []


def test_staging_failure_falls_back_to_argv(caplog) -> None:
    """A container that refuses the copy still runs the trial, the old way."""
    container = _FakeContainer(fail_copy=True)
    assert _stdin_prompt_path(container, _agent(supports=True), PROMPT) == ""
    assert "docker cp refused" in caplog.text


def test_redirect_attaches_after_env_exports_and_session_args() -> None:
    """Order matters: a ``<`` in the middle would strand the later arguments."""
    launch = _append_session_args("claude -p --verbose", ["--permission-mode", "bypass"])
    command = _redirect_stdin(f"FOO='bar' {launch}", STDIN_PROMPT_PATH)

    assert command == (
        "FOO='bar' claude -p --verbose --permission-mode bypass "
        f"< {STDIN_PROMPT_PATH}"
    )


def test_redirect_is_a_no_op_without_a_staged_prompt() -> None:
    assert _redirect_stdin("claude -p 'hi'", "") == "claude -p 'hi'"
