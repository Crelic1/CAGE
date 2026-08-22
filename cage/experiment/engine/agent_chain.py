"""End-to-end verification of the path a trial actually takes.

    agent config valid → agent CLI starts → reaches the proxy → proxy reaches
    the model → a reply comes back

Preflight used to verify a *different* path: ``curl → proxy → model``. Nothing
in a real run ever uses curl, so the first two links — the agent's own config
and its CLI — went entirely unchecked. A model whose registry entry was missing
a field the agent's CLI requires passed preflight green and then failed every
single trial, each one paying for a container, a target stack and an agent
install before dying with the same message.

This module exercises the real chain instead, by driving the same objects a
trial drives: ``AgentType.setup_container`` writes the agent's own config,
``env_vars`` points it at the proxy, ``build_launch_command`` starts it, and
``parse_output`` reads the answer. That is the point — a check built from the
runtime's own parts cannot drift from the runtime, and it needs no per-agent
knowledge beyond the methods every ``AgentType`` already implements.

Deliberately **not** a validator. Cage does not re-implement what any agent CLI
already checks; it runs the CLI and reports what the CLI says. When a config is
wrong the CLI's own words are the diagnosis, which keeps this from becoming an
endless catalogue of "agent X requires field Y".
"""

from __future__ import annotations

import json
import logging
import os
import uuid
from dataclasses import dataclass, field
from typing import Any

from cage.agents.base import AgentInstance
from cage.artifacts.record_snapshots import AGENT_HOME
from cage.contracts.agent_output import agent_failure_first_line, compact_lines
from cage.models import ModelConfig
from cage.experiment.engine.trial_runner import (
    _append_session_args,
    _redirect_stdin,
    _stdin_prompt_path,
)
from cage.experiment.engine.proxy_signals import (
    _last_proxy_error_signal,
    classify_upstream_error,
)
from cage.proxy.host import ProxyInstanceConfig, start_container_proxy
from cage.sandbox.containers import Container

logger = logging.getLogger(__name__)

#: Prompt used for the ping. Short on purpose: the point is to prove the chain
#: carries a request and returns an answer, not to test the model's ability.
PING_PROMPT = "Reply with exactly: CAGE_OK"

#: Marker we ask for. Its presence proves a real completion came back through
#: the proxy — a reply that merely *arrived* is enough, so we do not require the
#: model to have obeyed exactly.
PING_MARKER = "CAGE_OK"


@dataclass
class ChainCheckResult:
    """Outcome of one end-to-end agent→proxy→model verification."""

    ok: bool
    stage: str
    detail: str = ""
    agent_output: str = ""
    #: Steps that succeeded, in order — so a failure report can say how far it got.
    reached: list[str] = field(default_factory=list)

    def summary(self) -> str:
        """One line suitable for a preflight row or a CLI banner."""

        if self.ok:
            return f"agent → proxy → model OK ({', '.join(self.reached)})"
        got = f" (reached: {', '.join(self.reached)})" if self.reached else ""
        return f"{self.stage}: {self.detail}{got}"


def _container_name() -> str:
    return f"cage-chaincheck-{uuid.uuid4().hex[:8]}"


def check_agent_model_chain(
    agent: AgentInstance,
    *,
    model: ModelConfig | None = None,
    image: str = "",
    network_mode: str | None = "host",
    upstream_http_proxy: str = "",
    timeout_s: float = 180.0,
) -> ChainCheckResult:
    """Run one ping through the full agent→proxy→model chain.

    Returns a structured result rather than raising: both callers (preflight and
    ``cage agent debug --check``) want to render the outcome themselves, and a
    failure here is a report about the user's configuration, not an exception in
    Cage.

    The container is always removed, including on failure — a check that leaks
    containers would be worse than no check.
    """

    resolved_model = model if model is not None else agent.model
    resolved_image = image or agent.image or agent.agent_type.default_image
    subscription_mode = bool(resolved_model.auth_source) and not resolved_model.base_url
    subscription_upstream = getattr(
        agent.agent_type, "subscription_upstream_base_url", "",
    )
    if subscription_mode and not subscription_upstream:
        return ChainCheckResult(
            ok=False,
            stage="proxy config",
            detail=(
                f"agent {agent.agent_type.name!r} does not support subscription "
                f"auth for model {resolved_model.id!r}"
            ),
        )
    # Some agents need resources that can only be attached before ``docker
    # run``.  In particular, subscription-backed Codex and Claude Code mount a
    # single host credential file read-only and deliberately refuse to copy it
    # into an already-running container.  A real trial asks the agent for these
    # resources in ``trial_runner._create_container``; the chain check must do
    # the same or it tests a container shape that no real trial uses.
    resources = agent.agent_type.container_resources(
        home_dir=AGENT_HOME,
        model=resolved_model,
    )
    container = Container(
        name=_container_name(),
        image=resolved_image,
        network_mode=network_mode,
        extra_hosts={"host.docker.internal": "host-gateway"},
        volumes=dict(resources.volumes),
        group_add=list(resources.group_add),
        privileged=resources.privileged,
    )
    result = ChainCheckResult(ok=False, stage="container", detail="")

    try:
        try:
            container.start()
            container.setup_workspace(agent.home)
        except Exception as exc:  # noqa: BLE001
            result.stage = "container boot"
            result.detail = str(exc)[:400]
            return result
        result.reached.append("container")

        # The agent's own preparation — credential seeding, config files. This
        # is where a config the CLI cannot parse gets written, so failures here
        # are already agent-attributable.
        try:
            agent.agent_type.setup_container(
                container, home_dir=AGENT_HOME, model=resolved_model,
            )
        except Exception as exc:  # noqa: BLE001
            result.stage = "agent setup"
            result.detail = str(exc)[:400]
            return result
        result.reached.append("agent setup")

        proxy = None
        try:
            proxy = start_container_proxy(
                container,
                ProxyInstanceConfig(
                    # Match trial_runner exactly: a subscription model leaves
                    # ``base_url`` empty so the CLI stays in OAuth mode, while
                    # the sidecar still needs the agent-specific real backend
                    # to forward that OAuth-bearing request to.
                    upstream_base_url=(
                        subscription_upstream
                        if subscription_mode
                        else resolved_model.base_url
                    ),
                    upstream_api_key=resolved_model.api_key,
                    upstream_protocol=resolved_model.protocol,
                    artifact_dir=None,
                    trial_id="chaincheck",
                    port=0,
                    http_proxy=upstream_http_proxy,
                    extra_headers=dict(resolved_model.extra_headers or {}),
                    upstream_extra_body=dict(resolved_model.upstream_extra_body or {}),
                    preserve_thinking=resolved_model.preserve_thinking,
                    logs_mounted=False,
                    # A ping is one round; the headroom absorbs an agent that
                    # opens with a probe or a compaction call. NOT 0 — the proxy
                    # treats any value >= 0 as a hard cap, so 0 rejects the very
                    # request this check exists to make, and the rejection then
                    # reads as an agent failure. Small on purpose: this bounds
                    # what a misbehaving agent can spend during a check.
                    max_requests=4,
                ),
            )
        except Exception as exc:  # noqa: BLE001
            result.stage = "proxy start"
            result.detail = str(exc)[:400]
            return result
        result.reached.append("proxy")

        try:
            outcome = _run_agent_ping(
                container,
                agent=agent,
                model=resolved_model,
                proxy=proxy,
                upstream_http_proxy=upstream_http_proxy,
                timeout_s=timeout_s,
            )
        finally:
            try:
                proxy.stop()
            except Exception as exc:  # noqa: BLE001
                logger.debug("chain-check proxy stop failed: %s", exc)
        return outcome
    finally:
        try:
            container.stop()
        except Exception as exc:  # noqa: BLE001
            logger.debug("chain-check container cleanup failed: %s", exc)


def _read_proxy_records(container: Container, proxy: Any) -> list[dict]:
    """Read the proxy's own request log out of the container; [] if none.

    This is Cage's own component reporting on itself, which is why consulting it
    is not the kind of knowledge-duplication this module avoids: the proxy sat
    in the middle of the call and recorded exactly what the upstream did.
    """

    try:
        out = container.exec(
            f"cat {proxy.log_dir}/proxy.jsonl 2>/dev/null || true", timeout=15.0,
        )
    except Exception as exc:  # noqa: BLE001
        logger.debug("chain-check could not read proxy log: %s", exc)
        return []
    records: list[dict] = []
    for line in (out.stdout or "").splitlines():
        line = line.strip()
        if not line.startswith("{"):
            continue
        try:
            entry = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(entry, dict):
            records.append(entry)
    return records


def _upstream_failure_detail(
    records: list[dict],
    *,
    model: ModelConfig,
    upstream_http_proxy: str,
) -> str:
    """Describe an upstream failure using what Cage itself configured.

    "Connection refused" alone is a symptom with no address attached. The
    endpoint, the protocol and whether an HTTP proxy was in play are all values
    Cage chose, so naming them costs nothing and turns the message into
    something actionable.
    """

    import tempfile

    signal = None
    try:
        with tempfile.NamedTemporaryFile("w", suffix=".jsonl", delete=False) as fh:
            for entry in records:
                fh.write(json.dumps(entry) + "\n")
            tmp_path = fh.name
        signal = _last_proxy_error_signal(tmp_path)
    except Exception as exc:  # noqa: BLE001
        logger.debug("chain-check upstream classification skipped: %s", exc)
    finally:
        try:
            os.unlink(tmp_path)
        except (OSError, NameError):
            pass

    where = model.base_url or "(no base_url configured)"
    via = (
        f"via HTTP proxy {upstream_http_proxy}"
        if upstream_http_proxy
        else "no HTTP proxy configured"
    )
    context = f"upstream {where} [{model.protocol}] ({via})"

    if signal is None:
        return f"the agent reached the proxy but no upstream reply was recorded — {context}"

    reason = classify_upstream_error(
        http_status=signal.http_status,
        error_type=signal.error_type,
        error_message=signal.error_message,
    )
    said = (signal.error_message or signal.raw_text or "").strip()
    label = reason.value if reason is not None else "upstream error"
    status = f"HTTP {signal.http_status} " if signal.http_status else ""
    return f"{label}: {status}{compact_lines(said, limit=200)} — {context}"


def _run_agent_ping(
    container: Container,
    *,
    agent: AgentInstance,
    model: ModelConfig,
    proxy: Any,
    upstream_http_proxy: str,
    timeout_s: float,
) -> ChainCheckResult:
    """Launch the agent CLI against the proxy and read its answer back."""

    proxy_url = proxy.base_url
    result = ChainCheckResult(
        ok=False, stage="agent run", reached=["container", "agent setup", "proxy"],
    )
    try:
        env = agent.agent_type.env_vars(
            proxy_url=proxy_url,
            model=model,
            container=container,
            home_dir=AGENT_HOME,
            workspace_dir=agent.home,
            max_rounds=1,
            context_compaction_threshold=agent.context_compaction_threshold,
        )
        # Same prompt-delivery path as a real trial: if this agent's CLI in
        # this image cannot actually read its prompt from stdin, the check is
        # where that has to surface — a trial would just run with no task.
        prompt_path = _stdin_prompt_path(container, agent, PING_PROMPT)
        launch = agent.agent_type.build_launch_command(
            PING_PROMPT, model=model, max_rounds=1, proxy_url=proxy_url,
            stdin_prompt=bool(prompt_path),
        )
        # The trial appends the project's ``session_args`` here, so the check
        # must too — otherwise it runs a command no trial ever runs, which is
        # the exact failure mode this whole check exists to remove. It is also
        # what makes a bad ``session_args`` catchable: claude-code's
        # ``--output-format stream-json`` requires a ``--verbose`` that only
        # ``session_args`` supplies, so omitting them fails for a reason the
        # user's config had nothing to do with.
        launch = _append_session_args(launch, agent.session_args)
    except Exception as exc:  # noqa: BLE001
        result.stage = "agent launch command"
        result.detail = str(exc)[:400]
        return result

    exports = " ".join(f"{k}='{v}'" for k, v in env.items())
    agent_cmd = _redirect_stdin(
        f"{exports} {launch}" if exports else launch, prompt_path,
    )
    command = f"cd {agent.home} && {agent_cmd}"
    exec_result = container.exec(command, user="agent", timeout=timeout_s)

    output = agent.agent_type.parse_output(exec_result)
    result.agent_output = output

    # Whether the proxy recorded anything is the structural answer to "did the
    # agent get out of its own front door?". It beats reading exit codes, which
    # every CLI numbers differently, and it splits the two failures that look
    # identical from the outside: a config the CLI refused (nothing recorded)
    # versus an upstream that refused us (recorded, with the reason).
    records = _read_proxy_records(container, proxy)

    if exec_result.exit_code != 0:
        # The CLI's own words are the diagnosis, in the order the agent itself
        # makes them available: the banner (stderr, when the CLI wrote no stdout
        # at all), then whatever ``parse_output`` extracted — for a streaming CLI
        # the error arrives as an event, so the parsed output *is* the message —
        # then raw stderr as a last resort.
        if records:
            # It reached the proxy, so the agent and its config are fine; the
            # failure is on the far side and the proxy watched it happen.
            result.reached.append("upstream call")
            result.stage = "model call"
            result.detail = _upstream_failure_detail(
                records, model=model, upstream_http_proxy=upstream_http_proxy,
            )
            return result

        said = (
            agent_failure_first_line(output)
            or compact_lines(output)
            or compact_lines(exec_result.stderr)
        )
        result.stage = "agent run"
        result.detail = (
            f"the agent never reached the proxy — agent CLI exited "
            f"{exec_result.exit_code}"
            + (f": {said}" if said else "")
        )
        return result

    result.reached.append("model reply")
    result.ok = True
    result.stage = "ok"
    result.detail = (
        "reply received"
        if PING_MARKER in output
        else "reply received (marker absent; the chain works, the model just answered freely)"
    )
    return result


__all__ = [
    "PING_MARKER",
    "PING_PROMPT",
    "ChainCheckResult",
    "check_agent_model_chain",
]
