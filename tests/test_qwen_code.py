"""Tests for the Qwen Code agent config bridge."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from cage.agents.qwen_code import QwenCodeAgent
from cage.models import load_models


class _FakeContainer:
    """Minimal container double that records writes."""

    def __init__(self) -> None:
        self.exec_calls: list[str] = []
        self.files: dict[str, str] = {}

    def exec(self, cmd: str, *_: Any, **__: Any) -> Any:
        self.exec_calls.append(cmd)

        class _Result:
            exit_code = 0
            stdout = ""
            stderr = ""

        return _Result()

    def write_file(self, path: str, content: str) -> None:
        self.files[path] = content


def test_qwen_agent_renders_generation_config_from_models_yml(tmp_path: Path) -> None:
    container = _FakeContainer()
    models_yml = tmp_path / "models.yml"
    models_yml.write_text(
        """
models:
  qwen3.6-max-preview:
    provider: openai
    model: qwen3.6-max-preview
    base_url: https://dashscope.aliyuncs.com/compatible-mode/v1
    api_key: sk-test
    max_context_size: 262144
    enable_thinking: true
    thinking_budget: 81920
    preserve_thinking: true
    custom_headers:
      X-Cage-Test: enabled
""",
        encoding="utf-8",
    )
    model = load_models(models_yml)["qwen3.6-max-preview"]

    env = QwenCodeAgent().env_vars(
        proxy_url="http://127.0.0.1:8877",
        model=model,
        container=container,
        home_dir="/home/agent",
    )

    settings = json.loads(container.files["/home/agent/.qwen/settings.json"])
    provider = settings["modelProviders"]["openai"][0]
    generation = provider["generationConfig"]

    assert env["QWEN_CODE_API_KEY"] == "sk-test"
    assert env["OPENAI_MODEL"] == "qwen3.6-max-preview"
    assert provider["id"] == "qwen3.6-max-preview"
    assert provider["baseUrl"] == "http://127.0.0.1:8877/v1"
    assert provider["envKey"] == "QWEN_CODE_API_KEY"
    assert settings["model"]["name"] == "qwen3.6-max-preview"
    assert generation["contextWindowSize"] == 262144
    assert generation["customHeaders"] == {"X-Cage-Test": "enabled"}
    assert generation["extra_body"] == {
        "enable_thinking": True,
        "thinking_budget": 81920,
        "preserve_thinking": True,
    }


def test_qwen_streams_its_transcript_so_a_killed_trial_still_has_one() -> None:
    """A buffered format loses the whole run the moment a trial times out.

    ``--output-format json`` prints its single object at process *exit*, and a
    trial killed at its timeout never reaches exit. Measured against qwen-code
    0.15.11 with one prompt and one 75s kill: ``json`` left 0 bytes on stdout,
    ``stream-json`` left 60 events. That is the difference between a two-hour
    trial whose agent output is a startup warning and one whose transcript
    survives, so the flag is pinned here rather than left to taste.
    """

    command = QwenCodeAgent().build_launch_command("do the thing", model=None)
    assert "--output-format stream-json" in command
    assert "--output-format json" not in command


def test_qwen_reads_the_stream_it_asks_for() -> None:
    """Event shapes are verbatim from qwen-code 0.15.11 ``-o stream-json``."""

    from cage.sandbox.exec import ExecResult

    stdout = "\n".join([
        json.dumps({"type": "system", "subtype": "init", "model": "qwen3.7-max"}),
        json.dumps({
            "type": "assistant",
            "message": {"role": "assistant", "content": [
                {"type": "text", "text": "Ran STEP1; it printed STEP1."},
            ]},
        }),
        json.dumps({
            "type": "assistant",
            "message": {"role": "assistant", "content": [
                {"type": "text", "text": "Ran STEP2; it printed STEP2."},
            ]},
        }),
    ])
    parsed = QwenCodeAgent().parse_output(
        ExecResult(command="qwen", stdout=stdout, stderr="", exit_code=-1, duration_ms=1),
    )
    # No ``result`` event: the process was killed mid-run, so the latest
    # assistant turn is the honest answer.
    assert parsed == "Ran STEP2; it printed STEP2."


def test_qwen_never_reports_a_raw_event_stream_as_the_agents_answer() -> None:
    """Machine noise in the answer slot reads as an answer. Say nothing instead."""

    from cage.sandbox.exec import ExecResult

    stdout = json.dumps({"type": "system", "subtype": "init", "model": "qwen3.7-max"})
    parsed = QwenCodeAgent().parse_output(
        ExecResult(command="qwen", stdout=stdout, stderr="", exit_code=0, duration_ms=1),
    )
    assert parsed == ""
