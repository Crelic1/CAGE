"""Pre-flight checks — verify everything works before starting trials.

Three layers:

1. **Built-in (always run)** — image, container boot, model API, proxy→model chain.
   These are framework-level and never need user configuration.

2. **Framework-provided, user-enabled** — configured via ``preflight:`` in project.yml.
   The framework knows HOW to check these; the user just says WHAT to check.

   Example::

       preflight:
         # Check URLs are reachable (framework extracts from sample["target_url"])
         check_targets: true
         # Check internet is reachable via a proxy
         check_internet:
           proxy: http://127.0.0.1:7890
         # Arbitrary shell commands
         custom:
           - name: Redis is up
             command: redis-cli ping
             level: warn

3. **User custom commands** — under ``preflight.custom:``, arbitrary shell with
   ``{{image}}``, ``{{model_base_url}}`` etc. template variables.
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import re
import socket
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from cage.contracts.exceptions import CageError
from cage.experiment.engine.agent_chain import check_agent_model_chain
from cage.contracts.sample_keys import SAMPLE_MAX_ROUNDS_KEY
from cage.contracts.execution import CONTAINER_PROXY_SCRIPT_PATH, resolve_max_rounds
from cage.contracts.style import should_color, style
from cage.sandbox.containers import DEFAULT_CONTAINER_START_TIMEOUT

logger = logging.getLogger(__name__)

# Preflight is an admission check, not a trial container.  Reusing the runtime's
# ten-minute startup timeout makes one transient Docker stall look like a hung
# launch.  Three bounded attempts tolerate daemon jitter while still failing in
# a few minutes, before any trial is materialized.
PREFLIGHT_CONTAINER_BOOT_ATTEMPTS = 3
PREFLIGHT_CONTAINER_BOOT_TIMEOUT = min(DEFAULT_CONTAINER_START_TIMEOUT, 60.0)
PREFLIGHT_CONTAINER_BOOT_RETRY_DELAY = 2.0
PREFLIGHT_IMAGE_INSPECT_ATTEMPTS = 3
PREFLIGHT_IMAGE_INSPECT_TIMEOUT = 30.0
PREFLIGHT_IMAGE_INSPECT_RETRY_DELAY = 2.0


class PreflightError(CageError, RuntimeError):
    """Raised when a pre-flight check fails.

    A ``CageError`` because it is a user-fixable, fully-diagnosed condition —
    the check already printed which image, endpoint or target is wrong and what
    to run. The CLI renders those cleanly instead of burying them under a
    traceback. Kept a ``RuntimeError`` too so existing ``except RuntimeError``
    callers are unaffected.
    """


@dataclass
class PreflightResult:
    passed: int = 0
    failed: int = 0
    warnings: int = 0
    details: list[str] = field(default_factory=list)
    plain_output: bool = False
    color_enabled: bool = False
    stream: Any | None = field(default=None, repr=False, compare=False)

    def to_dict(self) -> dict[str, Any]:
        return {
            "passed": self.passed,
            "failed": self.failed,
            "warnings": self.warnings,
            "details": list(self.details),
        }

    def plain(self, message: str) -> None:
        print(message, file=self.stream or sys.stderr)


# ------------------------------------------------------------------
# Public entry point
# ------------------------------------------------------------------

def run_preflight(
    config: Any,
    samples: list[dict[str, Any]] | None = None,
) -> PreflightResult:
    """Run pre-flight checks. Raises PreflightError on critical failure."""
    terminal_ui = bool(getattr(getattr(config, "logging", None), "terminal_ui", False))
    result = PreflightResult(
        plain_output=terminal_ui,
        color_enabled=should_color(sys.stderr),
        stream=sys.stderr,
    )
    pf_cfg = config.metadata.get("preflight", {}) or {}
    # Backward compat: if preflight is a list, treat it as custom commands
    if isinstance(pf_cfg, list):
        pf_cfg = {"custom": pf_cfg}

    if result.plain_output:
        result.plain(
            style(
                "Pre-flight checks",
                "cyan",
                "bold",
                enabled=result.color_enabled,
            )
        )
    else:
        logger.info("=" * 60)
        logger.info("PRE-FLIGHT CHECKS")
        logger.info("=" * 60)

    # ---- Layer 1: Built-in (always) ----
    for agent in config.agents:
        _check_image(agent.effective_image, result)
        _check_container_boot(
            agent.effective_image,
            config.execution.agent_network_mode,
            result,
        )
        if not _agent_may_call_model(agent, samples, config):
            _warn(
                "Proxy → Model chain" if config.proxy.enabled else "Model API",
                result,
                "skipped (max_rounds=0): this run will not issue model-call rounds.",
            )
            continue
        # Multi-source (case 2): every source may serve a trial, so validate
        # each one — not just the representative. Single-source agents iterate a
        # one-element list, i.e. the unchanged behavior.
        for pf_model in (getattr(agent, "model_sources", None) or [agent.model]):
            if config.proxy.enabled:
                # The agent will reach the model via the in-container proxy, so
                # the host-level direct check is irrelevant (and may fail if the
                # host has no direct egress, which is the normal case for our
                # corporate-proxy setup). The proxy chain check exercises the
                # real call path end-to-end.
                #
                # Drive the *real* agent CLI, not a curl. A trial's call path is
                # agent → proxy → model; checking curl → proxy → model verified
                # a path nothing ever takes and left the agent's own config and
                # CLI completely unexercised, so a model entry missing a field
                # the CLI requires passed green here and then failed every trial.
                #
                # It also makes subscription/OAuth mode checkable. That case used
                # to be skipped with a warning because Anthropic only accepts
                # subscription tokens from the real Claude Code CLI — a bare curl
                # gets a fake ``rate_limit_error`` anti-abuse decoy. Running the
                # actual CLI is exactly what that mode needs.
                _check_agent_chain(
                    agent=agent,
                    model=pf_model,
                    network_mode=config.execution.agent_network_mode,
                    result=result,
                    upstream_http_proxy=config.proxy.upstream_http_proxy,
                )
            else:
                _check_model_api(pf_model, result)

    # ---- Layer 1 (cont.): target images for benchmarks that bring up a stack ----
    # Build-based targets must be built BEFORE the run (``cage benchmark build``
    # or ``cage run --build``); launch never builds. Without this check the run
    # boots, then every trial fails one-by-one with ``target_unavailable`` once
    # its stack tries to come up — looks like a "completed" run with 0 LLM calls.
    if getattr(getattr(config, "target", None), "enabled", False):
        _check_target_images(config, samples, result)
        _check_sealed_agent_network(config, result)

    # ---- Layer 2: Framework-provided, user-enabled ----
    internet_cfg = pf_cfg.get("check_internet")
    if internet_cfg:
        proxy_url = internet_cfg if isinstance(internet_cfg, str) else internet_cfg.get("proxy", "")
        _check_internet(proxy_url, result)

    # ---- Layer 3: User custom commands ----
    custom_checks = pf_cfg.get("custom", [])
    if custom_checks:
        template_vars = _build_template_vars(config)
        for check in custom_checks:
            if isinstance(check, str):
                check = {"name": check, "command": check}
            _run_user_check(
                name=check.get("name", "Custom"),
                command=_render_template(check.get("command", ""), template_vars),
                level=check.get("level", "error"),
                result=result,
            )

    # ---- Summary ----
    if not result.plain_output:
        logger.info("-" * 60)
    if result.failed > 0:
        if result.plain_output:
            result.plain(
                style(
                    f"Failed: {result.passed} passed, "
                    f"{result.failed} failed, {result.warnings} warnings",
                    "red",
                    "bold",
                    enabled=result.color_enabled,
                )
            )
        else:
            logger.error(
                "PRE-FLIGHT: %d passed, %d FAILED, %d warnings",
                result.passed, result.failed, result.warnings,
            )
        fail_details = [d for d in result.details if d.startswith("FAIL")]
        raise PreflightError(
            f"Pre-flight failed ({result.failed} errors):\n"
            + "\n".join(f"  - {d}" for d in fail_details)
        )

    if result.plain_output:
        summary_color = "yellow" if result.warnings else "green"
        result.plain(
            style(
                f"Ready: {result.passed} passed, {result.warnings} warnings",
                summary_color,
                "bold",
                enabled=result.color_enabled,
            )
        )
        result.plain("")
    else:
        logger.info(
            "PRE-FLIGHT: %d passed, %d warnings — all clear",
            result.passed, result.warnings,
        )
        logger.info("=" * 60)
    return result


# ------------------------------------------------------------------
# Round-budget helpers
# ------------------------------------------------------------------

def _agent_may_call_model(
    agent: Any,
    samples: list[dict[str, Any]] | None,
    config: Any,
) -> bool:
    planned_samples = samples or [{}]
    return any(
        _effective_preflight_max_rounds(agent, sample, config) != 0
        for sample in planned_samples
    )


def _effective_preflight_max_rounds(
    agent: Any,
    sample: dict[str, Any],
    config: Any,
) -> int:
    return resolve_max_rounds(
        getattr(agent, "max_rounds", -1),
        getattr(getattr(config, "execution", None), "max_rounds", -1),
        sample.get(SAMPLE_MAX_ROUNDS_KEY) if isinstance(sample, dict) else None,
    )


# ------------------------------------------------------------------
# Result helpers
# ------------------------------------------------------------------

def _pass(name: str, result: PreflightResult, msg: str = ""):
    result.passed += 1
    result.details.append(f"PASS: {name}" + (f" ({msg})" if msg else ""))
    if result.plain_output:
        status = style("PASS", "green", "bold", enabled=result.color_enabled)
        detail = f"{name}{f' - {msg}' if msg else ''}"
        result.plain(f"  {status} {detail}")
    else:
        logger.info("  [PASS] %s%s", name, f" — {msg}" if msg else "")


def _fail(name: str, result: PreflightResult, msg: str):
    result.failed += 1
    result.details.append(f"FAIL: {name} — {msg}")
    if result.plain_output:
        status = style("FAIL", "red", "bold", enabled=result.color_enabled)
        result.plain(f"  {status} {name} - {msg}")
    else:
        logger.error("  [FAIL] %s — %s", name, msg)


def _warn(name: str, result: PreflightResult, msg: str):
    result.warnings += 1
    result.details.append(f"WARN: {name} — {msg}")
    if result.plain_output:
        status = style("WARN", "yellow", "bold", enabled=result.color_enabled)
        result.plain(f"  {status} {name} - {msg}")
    else:
        logger.warning("  [WARN] %s — %s", name, msg)


def _run_cmd(cmd: list[str], timeout: float = 15.0) -> tuple[int, str, str]:
    try:
        r = subprocess.run(
            cmd, text=True, capture_output=True,
            stdin=subprocess.DEVNULL, timeout=timeout,
        )
        return r.returncode, r.stdout, r.stderr
    except subprocess.TimeoutExpired:
        return -1, "", "timeout"
    except Exception as e:
        return -1, "", str(e)


# ------------------------------------------------------------------
# Layer 1: Built-in checks
# ------------------------------------------------------------------

def _check_image(image: str, result: PreflightResult):
    name = f"Docker image [{image}]"
    rc = -1
    err = "unknown client error"
    attempts_used = 0
    for attempt in range(1, PREFLIGHT_IMAGE_INSPECT_ATTEMPTS + 1):
        attempts_used = attempt
        rc, _, err = _run_cmd(
            ["docker", "image", "inspect", image],
            timeout=PREFLIGHT_IMAGE_INSPECT_TIMEOUT,
        )
        if rc == 0:
            suffix = (
                f"attempt={attempt}/{PREFLIGHT_IMAGE_INSPECT_ATTEMPTS}"
                if attempt > 1 else ""
            )
            _pass(name, result, suffix)
            return
        if re.search(r"(?:no such image|no such object)", err, re.IGNORECASE):
            _fail(name, result, "Not found. Run: cage agent build")
            return
        if (
            attempt >= PREFLIGHT_IMAGE_INSPECT_ATTEMPTS
            or not _container_boot_failure_is_transient(rc, err)
        ):
            break
        logger.warning(
            "Transient Docker image-inspect failure on attempt %d/%d: %s",
            attempt,
            PREFLIGHT_IMAGE_INSPECT_ATTEMPTS,
            err[:200],
        )
        time.sleep(PREFLIGHT_IMAGE_INSPECT_RETRY_DELAY)

    attempts = (
        f" after {attempts_used} attempts"
        if attempts_used > 1 else ""
    )
    if rc == -1:
        _fail(
            name,
            result,
            "Docker inspect unavailable: "
            f"{err[:200] or 'unknown client error'}{attempts}. Check Docker daemon health "
            "before retrying; this does not prove the image is missing.",
        )
    else:
        _fail(
            name,
            result,
            f"Could not inspect image (docker exit {rc}): "
            f"{err[:200] or 'no stderr'}{attempts}. "
            "Check Docker daemon health before retrying.",
        )


def _container_boot_failure_is_transient(rc: int, error: str) -> bool:
    text = error.lower()
    if rc == -1 and "timeout" in text:
        return True
    return any(
        marker in text
        for marker in (
            "cannot connect to the docker daemon",
            "context deadline exceeded",
            "daemon is shutting down",
            "i/o timeout",
            "resource temporarily unavailable",
            "connection reset by peer",
        )
    )


def _check_container_boot(image: str, network_mode: str | None, result: PreflightResult):
    name = "Container boot"
    import uuid
    failures: list[str] = []
    for attempt in range(1, PREFLIGHT_CONTAINER_BOOT_ATTEMPTS + 1):
        # Use a fresh name per attempt.  A timed-out create can reach the daemon
        # after the client exits; reusing the name would turn that late request
        # into a misleading deterministic name-conflict failure.
        cname = f"cage-preflight-{uuid.uuid4().hex[:8]}"
        _run_cmd(["docker", "rm", "-f", cname], timeout=5.0)
        cmd = ["docker", "run", "-d", "--name", cname]
        if network_mode:
            cmd.extend(["--network", network_mode])
        cmd.extend([image, "sleep", "10"])

        rc, _, err = _run_cmd(cmd, timeout=PREFLIGHT_CONTAINER_BOOT_TIMEOUT)
        if rc == 0:
            rc2, _, _ = _run_cmd(
                ["docker", "exec", cname, "id", "agent"], timeout=5.0
            )
            _run_cmd(["docker", "rm", "-f", cname], timeout=10.0)
            if rc2 != 0:
                _fail(name, result, "User 'agent' not found in image")
            else:
                suffix = (
                    f", attempt={attempt}/{PREFLIGHT_CONTAINER_BOOT_ATTEMPTS}"
                    if attempt > 1 else ""
                )
                _pass(name, result, f"network={network_mode}{suffix}")
            return

        # Make a bounded exact cleanup attempt.  The fresh name is retained in
        # the diagnostic so a later health audit can reap a very-late create.
        _run_cmd(["docker", "rm", "-f", cname], timeout=10.0)
        failures.append(f"attempt {attempt} ({cname}): {err[:200]}")
        if (
            attempt >= PREFLIGHT_CONTAINER_BOOT_ATTEMPTS
            or not _container_boot_failure_is_transient(rc, err)
        ):
            break
        logger.warning(
            "Transient Docker preflight boot failure on attempt %d/%d: %s",
            attempt,
            PREFLIGHT_CONTAINER_BOOT_ATTEMPTS,
            err[:200],
        )
        time.sleep(PREFLIGHT_CONTAINER_BOOT_RETRY_DELAY)

    _fail(name, result, "Failed to start preflight container; " + "; ".join(failures))


# The probe lives in the sandbox layer next to the proxy it describes; kept
# importable from here because preflight is where a wrong answer gets caught.
from cage.sandbox.netproxy import host_holds_address_on  # noqa: E402


def _check_sealed_agent_network(config: Any, result: PreflightResult):
    """Under a sealed isolation policy, the agent's BASE network must be sealed too.

    ``per_trial_bridge_sealed`` only governs the network cage builds for the
    agent↔target leg. The container also keeps the network it was started on
    (``runtime.agent_network_mode``), and a stock bridge puts the docker host on
    that one — one ``curl 172.17.0.1:<port>`` and the seal is decoration. Catch
    it here, before a whole run believes it was contained.
    """
    from cage.target.provisioning import SEALED_TRIAL_BRIDGE

    if getattr(config.target, "agent_network_isolation", "") != SEALED_TRIAL_BRIDGE:
        return

    name = "Sealed agent network"
    remedy = (
        "create one with: python3 scripts/agent_netproxy.py up "
        "(it builds the network with inhibit_ipv4 and puts the egress proxy on "
        "the gateway address)"
    )
    network = config.execution.agent_network_mode or "bridge"
    if network == "host":
        _fail(name, result, f"runtime.agent_network_mode=host shares the host netns; {remedy}")
        return

    host_on = host_holds_address_on(network)
    if host_on is None:
        _fail(name, result, f"cannot determine whether the host is on network {network!r}")
    elif host_on:
        _fail(
            name, result,
            f"the host holds an address on {network}'s bridge, so the agent can "
            f"reach it (sshd, the inspector, other runs' published ports) and the "
            f"sealed per-trial bridge buys nothing; {remedy}",
        )
    else:
        _pass(name, result, f"host is not on {network}")


def _check_model_api(model: Any, result: PreflightResult):
    name = f"Model API [{model.id}]"
    url = f"{str(model.base_url).rstrip('/')}/models"
    rc, out, err = _run_cmd([
        "curl", "-s", "-o", "/dev/null", "-w", "%{http_code}",
        "--connect-timeout", "5", "--max-time", "10",
        url, "-H", f"Authorization: Bearer {model.api_key}",
    ])
    code = out.strip()
    if rc == 0 and code.startswith("2"):
        _pass(name, result, f"HTTP {code}")
    elif rc == 0:
        _warn(name, result, f"HTTP {code}")
    else:
        _fail(name, result, f"Unreachable: {err[:100]}")


def _validate_proxy_response(body: str, *, curl_exit: int) -> tuple[bool, str]:
    """Validate the proxy → model chain response body.

    Handles two response shapes:

    * **Plain JSON** — typical for ``/v1/chat/completions`` with
      ``stream: false``. FAIL on any top-level ``error`` key (covers both
      ``container_proxy``'s ``{"error": {"type": "proxy_error", ...}}``
      emitted on DNS/upstream failure, and upstream-returned envelopes
      like ``{"error": {"code": 400, ...}}``).

    * **SSE stream** — typical for ``/v1/responses`` against codex-relay
      endpoints that mandate streaming. Parse ``data:`` events; FAIL on
      any event that is itself an error envelope; PASS if at least one
      non-error event arrived.
    """
    if curl_exit != 0:
        return False, f"curl exited {curl_exit} (no response from proxy)"
    if not body or len(body) < 10:
        return False, f"Empty or truncated response ({len(body)} bytes)"

    if body.lstrip().startswith("data:") or "\ndata:" in body:
        events: list[Any] = []
        for line in body.splitlines():
            line = line.strip()
            if not line.startswith("data:"):
                continue
            payload = line[len("data:"):].strip()
            if not payload or payload == "[DONE]":
                continue
            try:
                event = json.loads(payload)
            except json.JSONDecodeError:
                continue
            events.append(event)
            if isinstance(event, dict) and (
                "error" in event or event.get("type") == "error"
            ):
                err = event.get("error", event)
                msg = (
                    (err.get("message") or err.get("type") or str(err))
                    if isinstance(err, dict) else str(err)
                )
                return False, f"Upstream SSE error: {str(msg)[:200]}"
        if not events:
            return False, f"SSE stream had no parseable events: {body[:200]}"
        return True, ""

    try:
        parsed = json.loads(body)
    except json.JSONDecodeError:
        return False, f"Non-JSON response: {body[:200]}"
    if isinstance(parsed, dict) and "error" in parsed:
        err = parsed["error"]
        if isinstance(err, dict):
            err_type = err.get("type") or ""
            err_msg = err.get("message") or ""
            msg = f"{err_type}: {err_msg}".strip(": ") or str(err)
        else:
            msg = str(err)
        return False, f"Proxy/upstream error: {str(msg)[:200]}"
    return True, ""


def _check_agent_chain(
    *,
    agent: Any,
    model: Any,
    network_mode: str | None,
    result: PreflightResult,
    upstream_http_proxy: str = "",
):
    """Verify agent → proxy → model end-to-end, skipping repeats via fingerprint.

    Split by determinism, which is what makes the cache safe:

    * **Whether this agent can drive this config** depends only on the image and
      the generated config — both captured by the fingerprint — so once proven
      it stays proven, and a repeat run pays nothing.
    * **Whether the endpoint is up, authorized and in credit** depends on the
      outside world and is *never* cached. ``_check_model_api`` covers it on
      every run.

    Caching the whole thing would silently skip the one check that catches an
    expired key or an exhausted quota — the failure mode this preflight already
    catches today.
    """

    name = "Agent → Proxy → Model chain"
    fingerprint = _agent_chain_fingerprint(
        agent=agent, model=model, network_mode=network_mode,
        upstream_http_proxy=upstream_http_proxy,
    )
    if fingerprint and _chain_check_is_cached(fingerprint):
        _pass(
            name, result,
            "cached — image and config unchanged since it last passed "
            "(endpoint health is still checked separately)",
        )
        return

    try:
        outcome = check_agent_model_chain(
            agent,
            model=model,
            image=getattr(agent, "effective_image", "") or "",
            network_mode=network_mode,
            upstream_http_proxy=upstream_http_proxy,
        )
    except Exception as exc:  # noqa: BLE001
        # The agent-driven check itself broke — a bug on our side, not a verdict
        # on the user's config. Blocking a run on that would be wrong, so fall
        # back to the older curl-based check: it verifies less (it cannot see
        # the agent's own config or CLI) but it is long-proven, and a partial
        # gate beats an accidental one. This path is also the signal that the
        # new check needs fixing for that agent.
        logger.warning("agent chain check failed to run, falling back to curl: %s", exc)
        _warn(name, result, f"agent-driven check unavailable ({str(exc)[:200]}); using curl")
        _check_proxy_chain(
            image=getattr(agent, "effective_image", "") or "",
            model=model,
            network_mode=network_mode,
            result=result,
            upstream_http_proxy=upstream_http_proxy,
        )
        return

    if outcome.ok:
        _pass(name, result, outcome.summary())
        if fingerprint:
            _remember_chain_check(fingerprint)
    else:
        _fail(name, result, outcome.summary())


def _agent_chain_fingerprint(
    *,
    agent: Any,
    model: Any,
    network_mode: str | None,
    upstream_http_proxy: str,
) -> str:
    """Identity of "this agent, this image, this config" — "" if it can't be taken.

    Includes the image's **content id**, not its tag: a rebuilt ``:latest``
    carries a new agent CLI, and a cache keyed on the tag would keep vouching
    for a version that no longer exists. Resolving it is one ``docker image
    inspect``; when that fails we return "" and the check simply always runs.
    """

    rc, out, _ = _run_cmd([
        "docker", "image", "inspect", "--format", "{{.Id}}",
        getattr(agent, "effective_image", "") or "",
    ], timeout=15.0)
    if rc != 0 or not out.strip():
        return ""
    parts = [
        out.strip(),
        str(getattr(agent.agent_type, "name", "")),
        str(getattr(agent, "version", "")),
        str(getattr(agent, "home", "")),
        ",".join(sorted(getattr(agent, "plugins", []) or [])),
        str(getattr(agent, "skill", "")),
        str(getattr(agent, "context_compaction_threshold", "")),
        str(network_mode or ""),
        str(bool(upstream_http_proxy)),
        # Model fields that shape the generated agent config / request.
        str(getattr(model, "id", "")),
        str(getattr(model, "model", "")),
        str(getattr(model, "base_url", "")),
        str(getattr(model, "protocol", "")),
        str(getattr(model, "max_context_size", "")),
        str(getattr(model, "reserved_context_size", "")),
        str(getattr(model, "auth_source", "")),
        json.dumps(getattr(model, "extra", {}) or {}, sort_keys=True),
    ]
    return hashlib.sha256("\x00".join(parts).encode()).hexdigest()


def _chain_check_cache_path() -> Path:
    return Path.home() / ".cache" / "cage" / "agent_chain_checks.json"


def _chain_check_is_cached(fingerprint: str) -> bool:
    """True when this exact agent+image+config already passed before."""

    try:
        data = json.loads(_chain_check_cache_path().read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return False
    return isinstance(data, dict) and fingerprint in (data.get("passed") or {})


def _remember_chain_check(fingerprint: str) -> None:
    """Record a passing fingerprint. Best-effort — a lost write only costs time."""

    path = _chain_check_cache_path()
    try:
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            data = {}
        if not isinstance(data, dict):
            data = {}
        passed = data.get("passed")
        if not isinstance(passed, dict):
            passed = {}
        passed[fingerprint] = time.strftime("%Y-%m-%dT%H:%M:%S")
        # Keep the file from growing without bound across months of image
        # rebuilds; the oldest entries are the least likely to be re-used.
        if len(passed) > 200:
            passed = dict(sorted(passed.items(), key=lambda kv: kv[1])[-200:])
        data["passed"] = passed
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    except OSError as exc:
        logger.debug("chain-check cache not written: %s", exc)


def _check_proxy_chain(
    image: str,
    model: Any,
    network_mode: str | None,
    result: PreflightResult,
    *,
    upstream_http_proxy: str = "",
):
    """Temp container → start proxy → send request → verify response."""
    name = "Proxy → Model chain"
    import uuid
    cname = f"cage-preflight-proxy-{uuid.uuid4().hex[:8]}"
    # Defensive: remove any leftover container with this name
    _run_cmd(["docker", "rm", "-f", cname], timeout=5.0)
    cmd = ["docker", "run", "-d", "--name", cname]
    if network_mode:
        cmd.extend(["--network", network_mode])
    cmd.extend(["--add-host", "host.docker.internal:host-gateway"])
    # TTL must outlive this check's own request budget: setup + up to two model
    # pings (``--max-time`` each, see below). A slow reasoning model (e.g. GLM
    # spends ~35s emitting reasoning_content even for a 5-token "hi") otherwise
    # exhausts a short TTL, the container exits, and the in-flight ``docker exec
    # curl`` is SIGKILLed -> a confusing "curl exited 137" instead of a clean
    # timeout. Removed in ``finally`` regardless.
    cmd.extend([image, "sleep", "240"])

    rc, _, err = _run_cmd(cmd, timeout=DEFAULT_CONTAINER_START_TIMEOUT)
    if rc != 0:
        _fail(name, result, f"Container failed: {err[:200]}")
        return

    try:
        # Write config. The proxy binary is whatever the image baked into
        # /opt/cage-proxy/container_proxy.py (the COPY in docker/*/Dockerfile);
        # preflight starts that baked copy as-is.

        # Subscription/OAuth fallback: the agent launch path uses the same rule —
        # when ``auth_source`` is set and no explicit ``base_url``, the
        # proxy forwards to ``api.anthropic.com``. Mirror that here or the
        # preflight curl ends up with an empty upstream URL.
        _sub_mode = bool(getattr(model, "auth_source", "")) and not model.base_url
        upstream_base_url = (
            "https://api.anthropic.com" if _sub_mode else str(model.base_url)
        )
        cfg = json.dumps({
            "upstream_base_url": upstream_base_url,
            "upstream_api_key": str(model.api_key),
            "upstream_protocol": getattr(model, "protocol", "openai"),
            "http_proxy": upstream_http_proxy,
            "extra_headers": {
                str(k): str(v)
                for k, v in (getattr(model, "extra_headers", {}) or {}).items()
            },
            "trial_id": "preflight",
        })

        # Write config via a temp file on host then docker cp (avoids shell escaping issues)
        tmp = tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False)
        tmp.write(cfg)
        tmp.close()
        _run_cmd(["docker", "exec", cname, "mkdir", "-p", "/tmp/pl"])
        _run_cmd(["docker", "exec", cname, "chmod", "777", "/tmp/pl"])
        _run_cmd(["docker", "cp", tmp.name, f"{cname}:/tmp/pc.json"])
        _run_cmd(["docker", "exec", cname, "chmod", "644", "/tmp/pc.json"])
        os.unlink(tmp.name)

        # Pick a free port (same mechanism as the real proxy)
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as _sock:
            _sock.bind(("127.0.0.1", 0))
            proxy_port = _sock.getsockname()[1]

        # Start proxy as agent
        _run_cmd(["docker", "exec", "-d", "-u", "agent", cname, "bash", "-c",
                   f"python3 {CONTAINER_PROXY_SCRIPT_PATH} --port {proxy_port} "
                   f"--config /tmp/pc.json --log-dir /tmp/pl "
                   f">/tmp/pl/stdout.log 2>/tmp/pl/stderr.log"])
        time.sleep(3)

        # Health check
        rc_h, out_h, _ = _run_cmd(
            ["docker", "exec", cname, "curl", "-s", f"http://localhost:{proxy_port}/healthz"],
            timeout=5.0,
        )
        if "ok" not in out_h:
            _, stderr_log, _ = _run_cmd(
                ["docker", "exec", cname, "cat", "/tmp/pl/stderr.log"], timeout=5.0,
            )
            _fail(name, result, f"Proxy failed to start on port {proxy_port}: {stderr_log[:300]}")
            return

        # Send test request — use the right endpoint for the protocol.
        # Pass the real upstream api_key just like a real agent CLI would; the
        # proxy is intentionally dumb about credentials, the harness is what
        # authenticates to the upstream.
        protocol = getattr(model, "protocol", "openai")
        upstream_key = str(model.api_key)
        # Strip Claude-Code's ``[effort]`` decorator (e.g. ``claude-opus-4-7
        # [xhigh]``). The CLI consumes it internally — translates to a
        # ``thinking`` config in the request body — and forwards the bare
        # model id to the API. Raw preflight curl has no such translation,
        # so we send the bare id ourselves.
        _model_bare = re.sub(r"\[[^\]]+\]$", "", str(model.model))
        if protocol == "anthropic":
            # Anthropic: /v1/messages
            payload = json.dumps({
                "model": _model_bare, "max_tokens": 5,
                "messages": [{"role": "user", "content": "hi"}],
            })
            rc_t, out_t, _ = _run_cmd(
                ["docker", "exec", cname, "curl", "-s", "--max-time", "90",
                 "-X", "POST", f"http://localhost:{proxy_port}/v1/messages",
                 "-H", "Content-Type: application/json",
                 "-H", f"x-api-key: {upstream_key}",
                 "-H", "anthropic-version: 2023-06-01",
                 "-d", payload],
                timeout=100.0,
            )
        elif protocol == "google":
            # Google Gemini: /v1beta/models/{model}:generateContent. Auth is
            # the ``x-goog-api-key`` header — Google 401s if a Bearer token is
            # attached alongside it, so the proxy must not inject one (it skips
            # injection when x-goog-api-key is present).
            payload = json.dumps({
                "contents": [{"parts": [{"text": "hi"}]}],
                "generationConfig": {"maxOutputTokens": 5},
            })
            rc_t, out_t, _ = _run_cmd(
                ["docker", "exec", cname, "curl", "-s", "--max-time", "90",
                 "-X", "POST",
                 f"http://localhost:{proxy_port}/v1beta/models/{_model_bare}:generateContent",
                 "-H", "Content-Type: application/json",
                 "-H", f"x-goog-api-key: {upstream_key}",
                 "-d", payload],
                timeout=100.0,
            )
        else:
            # OpenAI: /v1/chat/completions (standard) or /v1/responses
            payload = json.dumps({
                "model": _model_bare, "max_tokens": 5,
                "messages": [{"role": "user", "content": "hi"}],
            })
            rc_t, out_t, _ = _run_cmd(
                ["docker", "exec", cname, "curl", "-s", "--max-time", "90",
                 "-X", "POST", f"http://localhost:{proxy_port}/v1/chat/completions",
                 "-H", "Content-Type: application/json",
                 "-H", f"Authorization: Bearer {upstream_key}",
                 "-d", payload],
                timeout=100.0,
            )
            # If chat/completions fails (e.g. responses-only API), try
            # /v1/responses. Codex-relay endpoints mandate ``stream: true``
            # and reject ``stream: false`` outright, so send a streaming
            # request and let _validate_proxy_response parse the SSE.
            if rc_t != 0 or not out_t or '"error"' in out_t:
                payload_r = json.dumps({
                    "model": str(model.model),
                    "instructions": "hi",
                    "input": [{"type": "message", "role": "user",
                               "content": [{"type": "input_text", "text": "hi"}]}],
                    "store": False, "stream": True,
                })
                rc_t, out_t, _ = _run_cmd(
                    ["docker", "exec", cname, "curl", "-s", "--max-time", "90",
                     "-X", "POST", f"http://localhost:{proxy_port}/v1/responses",
                     "-H", "Content-Type: application/json",
                     "-H", f"Authorization: Bearer {upstream_key}",
                     "-d", payload_r],
                    timeout=100.0,
                )

        ok, fail_reason = _validate_proxy_response(out_t, curl_exit=rc_t)
        if ok:
            _pass(name, result, f"Response received ({len(out_t)} bytes)")
        else:
            _fail(name, result, fail_reason)

    finally:
        _run_cmd(["docker", "rm", "-f", cname], timeout=10.0)


def _image_exists_local(image: str) -> bool:
    rc, _, _ = _run_cmd(["docker", "image", "inspect", image], timeout=10.0)
    return rc == 0


def _check_target_images(config: Any, samples: list[dict[str, Any]] | None, result: PreflightResult):
    """Fail fast when a benchmark target needs build-images that aren't built.

    Mirrors the target server's launch-time ``_missing_build_images`` guard, but
    runs host-side BEFORE any trial starts: resolve each planned sample's target
    challenge, read its compose stack (no containers started), and flag every
    service that declares ``build:`` whose ``image:`` tag is absent locally.
    Pull-only services (``image:`` without ``build:``) are left to launch.
    """
    name = "Target images"
    try:
        from cage.target.adapters.roots import normalize_benchmark_sources
        from cage.target.adapters.source_config import build_default_registry
        from cage.target.compose_files import load_compose_stack
        from cage.target.provisioning import (
            discover_benchmark_root,
            target_challenge_id,
        )
    except Exception as exc:  # noqa: BLE001
        _warn(name, result, f"skipped (target modules unavailable: {exc})")
        return

    # Unique target challenges across the planned samples (same resolver the
    # trial runner uses: ``challenge_id`` else sample ``id``).
    chal_ids: list[str] = []
    seen: set[str] = set()
    for s in samples or []:
        cid = target_challenge_id(s) if isinstance(s, dict) else ""
        if cid and cid not in seen:
            seen.add(cid)
            chal_ids.append(cid)
    if not chal_ids:
        return

    bench_root = discover_benchmark_root(getattr(config, "benchmark", None))
    if bench_root is None:
        _warn(name, result, "skipped (no benchmark_root to resolve target challenges)")
        return

    try:
        registry = build_default_registry()
        sources = normalize_benchmark_sources(
            [{"adapter_kind": "challenge_json", "root": str(bench_root)}]
        )
        challenges = registry.discover_all(sources)
    except Exception as exc:  # noqa: BLE001
        _warn(name, result, f"skipped (could not load challenges: {exc})")
        return

    missing_by_chal: dict[str, list[str]] = {}
    verified_chals: set[str] = set()
    for cid in chal_ids:
        meta = challenges.get(cid)
        if not meta:
            continue  # not a server-launched target (e.g. static / external)
        try:
            adapter = registry.get(meta["adapter_kind"])
            spec = adapter.build_launch_spec(meta)
        except Exception:  # noqa: BLE001
            continue
        if getattr(spec, "mode", "") == "static" or not spec.compose_files:
            continue
        try:
            stack = load_compose_stack(spec.compose_files)
        except Exception:  # noqa: BLE001
            continue
        for _svc, cfg in (stack.get("services") or {}).items():
            if not isinstance(cfg, dict) or "build" not in cfg:
                continue
            image = str(cfg.get("image") or "").strip()
            # Unresolved ``${VAR}`` tags can't be checked statically — skip
            # rather than risk a false failure.
            if not image or "${" in image:
                continue
            # A challenge counts as "verified" only once it declares a real
            # build-image we could inspect — pull-only stacks (nothing to build)
            # contribute no PASS row and no failure.
            verified_chals.add(cid)
            if not _image_exists_local(image):
                missing_by_chal.setdefault(cid, [])
                if image not in missing_by_chal[cid]:
                    missing_by_chal[cid].append(image)

    if not verified_chals:
        return  # nothing build-based to verify in this run
    if not missing_by_chal:
        _pass(name, result, f"{len(verified_chals)} target(s) built")
        return

    all_imgs = sorted({img for imgs in missing_by_chal.values() for img in imgs})
    shown = ", ".join(all_imgs[:6]) + (f" (+{len(all_imgs) - 6} more)" if len(all_imgs) > 6 else "")
    bench_id = str((getattr(config, "metadata", {}) or {}).get("benchmark_id") or "").strip()
    sample_chal = next(iter(missing_by_chal))
    build_target = f"cage benchmark build {bench_id}".rstrip()
    _fail(
        name,
        result,
        f"{len(all_imgs)} image(s) missing for {len(missing_by_chal)} target(s): {shown}. "
        f"Build them first (e.g. `{build_target} --sample {sample_chal} ...`), "
        f"or pass `--build` to build at launch.",
    )


# ------------------------------------------------------------------
# Layer 2: Framework-provided, user-enabled
# ------------------------------------------------------------------


def _check_internet(proxy_url: str, result: PreflightResult):
    """Check internet reachability, optionally via HTTP proxy."""
    name = "Internet access" + (f" (via {proxy_url})" if proxy_url else "")
    cmd = [
        "curl", "-s", "-o", "/dev/null", "-w", "%{http_code}",
        "--connect-timeout", "5", "--max-time", "10",
    ]
    if proxy_url:
        cmd.extend(["-x", proxy_url])
    cmd.append("https://httpbin.org/status/200")

    rc, out, _ = _run_cmd(cmd)
    code = out.strip()
    if rc == 0 and code.startswith("2"):
        _pass(name, result)
    else:
        _warn(name, result, f"Not reachable (HTTP {code})")


# ------------------------------------------------------------------
# Layer 3: User custom commands
# ------------------------------------------------------------------

def _build_template_vars(config: Any) -> dict[str, str]:
    vs: dict[str, str] = {}
    if config.agents:
        a = config.agents[0]
        vs["image"] = a.effective_image
        vs["model_id"] = a.model.id
        vs["model_name"] = a.model.model
        vs["model_base_url"] = str(a.model.base_url)
        vs["model_api_key"] = str(a.model.api_key)
        vs["network_mode"] = config.execution.agent_network_mode or "bridge"
    return vs


def _render_template(command: str, vars: dict[str, str]) -> str:
    for k, v in vars.items():
        command = command.replace("{{" + k + "}}", v)
    return command


def _run_user_check(name: str, command: str, level: str, result: PreflightResult):
    try:
        r = subprocess.run(
            command, shell=True, text=True,
            capture_output=True, stdin=subprocess.DEVNULL, timeout=30.0,
        )
        if r.returncode == 0:
            _pass(name, result)
        else:
            msg = (r.stderr or r.stdout or "").strip()[:200] or f"exit {r.returncode}"
            (_warn if level == "warn" else _fail)(name, result, msg)
    except subprocess.TimeoutExpired:
        (_warn if level == "warn" else _fail)(name, result, "timeout (30s)")
    except Exception as e:
        (_warn if level == "warn" else _fail)(name, result, str(e)[:200])
