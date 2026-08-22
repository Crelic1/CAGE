"""Google Gemini CLI agent type.

Upstream: https://github.com/google-gemini/gemini-cli (binary: ``gemini``;
npm package ``@google/gemini-cli``). In API-key mode the CLI speaks
Google's **native** Generative Language API — it POSTs to
``{base}/v1beta/models/{model}:streamGenerateContent`` with a ``contents``
array and authenticates via the ``x-goog-api-key`` header. It does **not**
have an OpenAI/Anthropic client mode (that lives only in forks like
qwen-code), so Cage routes it as ``protocol = "google"``.

Wiring:

* ``GOOGLE_GEMINI_BASE_URL`` redirects every model call at the in-container
  proxy (verified in ``contentGenerator.ts``; reliable on gemini-cli
  >= ~0.40). The value is a bare origin (``http://host:port``) — the GenAI
  SDK appends the ``/v1beta/...`` path itself, so we pass ``proxy_url``
  without a ``/v1`` suffix.
* ``GEMINI_API_KEY`` is the AI-Studio key; the CLI sends it as
  ``x-goog-api-key`` and the proxy forwards that header verbatim (it must
  *not* also inject a Bearer token — Google 401s on dual auth).

The proxy forwards the Google call byte-for-byte to the real Gemini
endpoint but records an OpenAI-shaped projection so the web inspector can
parse the conversation, tokens, and tool calls (see ``proxy/sidecar.py``).

``max_rounds`` maps to gemini-cli's ``model.maxSessionTurns`` (settings
only — there is no CLI flag), and ``-o json`` yields a single
``{"response": ...}`` object we parse for the final answer.
"""

from __future__ import annotations

import json
from typing import Any

from cage.agents.base import AgentType, register_agent_type
from cage.agents.base.output import failure_banner
from cage.models import ModelConfig
from cage.sandbox.exec import ExecResult


def _gemini_settings(
    *,
    model: ModelConfig | None,
    max_rounds: int = -1,
) -> dict[str, Any]:
    """Build a headless-friendly ``~/.gemini/settings.json``.

    Disables the built-in sandbox (Cage provides its own Docker isolation),
    telemetry, and usage stats, and pre-selects API-key auth so the
    non-interactive ``-p`` run never bounces to the OAuth login flow. The
    nested-section schema matches gemini-cli >= 0.3.0.
    """
    settings: dict[str, Any] = {
        "security": {"auth": {"selectedType": "gemini-api-key"}},
        "tools": {"sandbox": False},
        "telemetry": {"enabled": False},
        "privacy": {"usageStatisticsEnabled": False},
        "model": {},
    }
    if model is not None and model.model:
        settings["model"]["name"] = model.model
    # maxSessionTurns is settings-only (no CLI flag); -1 ⇒ unbounded, the
    # CLI default, so only pin it when the user set a positive budget.
    if max_rounds and max_rounds > 0:
        settings["model"]["maxSessionTurns"] = int(max_rounds)
    return settings


def _stream_json_answer(stdout: str) -> tuple[str, bool]:
    """Reproduce ``-o json``'s ``response`` from an ``-o stream-json`` stream.

    Returns ``(answer, saw_json)``. gemini-cli's stream is NOT shaped like
    claude-code's, so the shared extractor cannot read it:

    - The answer arrives as ``{"type": "message", "role": "assistant",
      "content": <str>, "delta": true}`` events — **fragments**, not whole
      messages. Keeping the last one keeps the tail of a sentence.
    - The very first ``message`` event has ``"role": "user"`` and carries the
      prompt verbatim. A loop that ignores ``role`` renders the task
      description back as the agent's own answer.
    - ``{"type": "result"}`` never carries the text at all — success emits
      only ``status`` and ``stats``.

    So the CLI's own accounting is mirrored here (``packages/cli`` builds
    ``responseText`` the same way): concatenate assistant fragments, and clear
    the buffer at each ``tool_use`` so the answer is the prose *after* the
    last tool call. Its ``preToolResponseText`` fallback matters most for the
    trials that motivated the switch — an agent killed mid-tool-call has an
    empty buffer, and the words before it are all it left.
    """

    saw_json = False
    since_tool: list[str] = []
    before_tool = ""
    for line in stdout.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if not isinstance(event, dict):
            continue
        saw_json = True
        etype = event.get("type")
        if etype == "message" and event.get("role") == "assistant":
            content = event.get("content")
            if isinstance(content, str):
                since_tool.append(content)
        elif etype == "tool_use":
            text = "".join(since_tool).strip()
            if text:
                before_tool = text
            since_tool = []
    return ("".join(since_tool).strip() or before_tool), saw_json


@register_agent_type
class GeminiCliAgent(AgentType):
    name = "gemini_cli"
    supports_stdin_prompt = True
    state_paths = [".gemini"]
    default_image = "cage/gemini-cli:pentestenv"
    dockerfile = "docker/gemini_cli/pentestenv.Dockerfile"

    def install_command(self, version: str = "latest") -> str:
        return f"npm install -g @google/gemini-cli@{version}"

    def version_command(self) -> str:
        return "gemini --version 2>/dev/null || echo unknown"

    @property
    def protocol(self) -> str:
        return "google"

    def build_launch_command(
        self, prompt: str, *, model: ModelConfig, max_rounds: int = -1, proxy_url: str = "",
        stdin_prompt: bool = False,
    ) -> str:
        """Launch ``gemini`` in non-interactive single-prompt mode.

        With ``stdin_prompt`` the ``-p`` flag is dropped entirely: a piped
        (non-TTY) stdin is itself what puts gemini-cli in headless mode, and
        the piped text becomes the prompt.

        ``-p`` forces headless (prompt-and-exit); ``--approval-mode=yolo``
        auto-approves every tool call so the run is unattended. The per-trial
        round budget rides in ``model.maxSessionTurns`` (written by
        ``env_vars``) because gemini-cli exposes no max-turns flag — the
        proxy's ``max_requests`` backstop is the hard cap regardless.

        ``-o stream-json`` rather than the ``-o json`` this used to pass:
        ``json`` builds one object in memory and prints it at process exit,
        so a trial killed at its timeout records nothing at all. Measured on
        gemini-cli 0.47.0 — killed 45s into a twelve-step task, ``json`` left
        0 bytes on stdout; and polled while still running, ``stream-json``
        already had 320 bytes on disk at t=4s. See :func:`_stream_json_answer`
        for the event contract that buys.
        """
        escaped = prompt.replace("'", "'\\''")
        prompt_flag = "" if stdin_prompt else f" -p '{escaped}'"
        cli_model = model.model_name_for_agent(self.name)
        return (
            f"gemini{prompt_flag}"
            f" -m {cli_model}"
            f" --approval-mode=yolo"
            f" -o stream-json"
        )

    def parse_output(self, result: ExecResult) -> str:
        """Extract the agent's answer from ``-o stream-json`` stdout.

        The live format is the NDJSON stream :meth:`build_launch_command`
        asks for; :func:`_stream_json_answer` owns its contract.

        The single-object branch below stays for run dirs recorded under
        ``-o json`` before the switch — ``cage score`` re-reads those — where
        the answer sits in a top-level ``response``.
        """
        banner = failure_banner(result)
        if banner is not None:
            return banner

        stdout = result.stdout.strip()
        if not stdout:
            return ""

        streamed, saw_json = _stream_json_answer(stdout)
        if streamed:
            return streamed

        try:
            obj = json.loads(stdout)
        except json.JSONDecodeError:
            obj = None

        if isinstance(obj, dict):
            for key in ("response", "result", "output", "text"):
                value = obj.get(key)
                if isinstance(value, str) and value.strip():
                    return value

        # Raw stdout is a readable last resort for ``-o text``, but an event
        # stream nobody could read as prose is machine noise, and machine
        # noise in the answer slot reads as an answer.
        return "" if saw_json else stdout[:4000]

    def env_vars(
        self,
        *,
        proxy_url: str,
        model: ModelConfig,
        container: Any = None,
        home_dir: str = "/home/agent",
        workspace_dir: str = "",
        max_rounds: int = -1,
        context_compaction_threshold: float | None = None,
    ) -> dict[str, str]:
        """Point gemini-cli's GenAI SDK at the in-container proxy.

        ``GOOGLE_GEMINI_BASE_URL`` takes a bare origin (no ``/v1``); the SDK
        appends ``/v1beta/...`` itself. ``GEMINI_API_KEY`` is sent by the CLI
        as ``x-goog-api-key`` and forwarded verbatim by the proxy. We also
        (re)write ``~/.gemini/settings.json`` each trial to carry this
        trial's ``maxSessionTurns`` and keep the sandbox/telemetry off.
        """
        if container is not None:
            self._patch_settings(
                container, home_dir=home_dir, model=model, max_rounds=max_rounds,
            )
        env: dict[str, str] = {
            "GEMINI_SANDBOX": "false",
            "GEMINI_TELEMETRY_ENABLED": "false",
            # gemini-cli >= ~0.44 gates tool use behind a "trusted folders"
            # check: in an untrusted dir it silently downgrades --approval-mode
            # from yolo back to "default" and a headless `-p` run exits 55
            # before making a single model call. The workspace is a throwaway
            # Cage container, so trust it unconditionally (the documented env
            # for headless/automated environments).
            "GEMINI_CLI_TRUST_WORKSPACE": "true",
        }
        if proxy_url:
            env["GOOGLE_GEMINI_BASE_URL"] = proxy_url.rstrip("/")
        elif model.base_url:
            env["GOOGLE_GEMINI_BASE_URL"] = model.base_url.rstrip("/")
        if model.api_key:
            env["GEMINI_API_KEY"] = model.api_key
        return env

    def _patch_settings(
        self, container: Any, *, home_dir: str,
        model: ModelConfig | None, max_rounds: int = -1,
    ) -> None:
        """Write a fresh ``~/.gemini/settings.json`` for this trial."""
        gemini_dir = f"{home_dir.rstrip('/')}/.gemini"
        container.exec(f"mkdir -p {gemini_dir}", timeout=5.0)
        container.write_file(
            f"{gemini_dir}/settings.json",
            json.dumps(
                _gemini_settings(model=model, max_rounds=max_rounds), indent=2,
            ),
        )
        container.exec(f"chown -R agent:agent {gemini_dir}", timeout=5.0)

    def setup_container(
        self, container: Any, *, home_dir: str,
        model: ModelConfig | None = None,
        context_compaction_threshold: float | None = None,
    ) -> None:
        """Seed ``~/.gemini/settings.json`` so the first ``-p`` run is clean.

        Without it gemini-cli's first launch can print one-time auth/theme
        UX to stdout and contaminate ``-o json`` parsing.
        """
        self._patch_settings(container, home_dir=home_dir, model=model)
