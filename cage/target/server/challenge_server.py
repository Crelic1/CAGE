#!/usr/bin/env python3
"""FastAPI entry point for the challenge server.

Routes, lifecycle handlers, and the background health monitor live here.
Lower-level functionality is split across:
  - server_state: env config, docker client, port pool, instance registry, challenge cache
  - schemas: Pydantic request/response models
  - network_admin: docker network/container helpers
  - health_probes: container/port/HTTP readiness checks
  - launch_workflow: launch and cleanup orchestration
"""
from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import os
import re
import shutil
import sys
import tarfile
import tempfile
import time
import zipfile
from pathlib import Path
from typing import Annotated, Optional

import uvicorn
from fastapi import Depends, FastAPI, File, HTTPException, Query, Request, Response, UploadFile
from fastapi.responses import FileResponse, HTMLResponse

try:
    from cage.target.server.path_bootstrap import ensure_repo_root_on_sys_path
except ModuleNotFoundError:
    from path_bootstrap import ensure_repo_root_on_sys_path

ensure_repo_root_on_sys_path(__file__)

# --- Re-exports for backward compatibility ---
# Tests and external callers patch / import these symbols from challenge_server.
# Keeping them here avoids breaking external mock.patch.object(challenge_server, "X") use.
from cage.target.server import server_state as _server_state  # noqa: F401
from cage.target.server.health_probes import (  # noqa: F401
    is_instance_healthy,
    is_port_open,
    probe_inner_service,
    wait_for_containers_running,
    wait_for_http_ready,
    wait_for_inner_services_ready,
    wait_for_ports_open,
    wait_for_services_healthy,
)
from cage.target.server.cleanup import (  # noqa: F401
    _cleanup_instance_impl,
    cleanup_instance,
    has_resources_for_cage_run_id,
    purge_by_cage_run_id,
)
from cage.target.server import launch_ops
from cage.target.server.launch import (  # noqa: F401
    _launch_challenge_impl,
    _reused_launch_response,
    resolve_parallel_mode,
    resolve_server_target_scope,
)
from cage.target.server.launch_workflow import (  # noqa: F401
    ensure_docker_cli_config_dir,
    load_env_file_vars,
    parse_internal_port,
    pydantic_to_dict,
)
from cage.contracts.challenge import range_objectives
from cage.target.server.network_debug import build_network_debug  # noqa: F401
from cage.target.server.network_admin import (  # noqa: F401
    _has_active_endpoints_error,
    cleanup_orphan_networks,
    cleanup_orphan_volumes,
    ensure_docker_network,
    list_project_containers,
    remove_network_with_retry,
    resolve_service_inner_ips,
    summarize_project_containers,
)
from cage.target.server.network_admin import (
    remove_own_docker_network as _remove_own_docker_network,
)
from cage.target.server.schemas import (  # noqa: F401
    ChallengeSummary,
    EntryUrl,
    InstanceSummary,
    LaunchOpRequest,
    LaunchOpStatus,
    LaunchResponse,
    PromptResponse,
    RescoreOpStatus,
    RescoreRequest,
    ServiceInfo,
    StopResponse,
    SubmitResponse,
    epoch_to_rfc3339,
)
from cage.target.server import rescore, rescore_ops
from cage.target.server.submit import (
    SubmissionError,
    render_task_prompt,
    score_submission,
)
from cage.target.server.network_debug import _build_entry_urls, build_container_addrs
from cage.target.server.public_access import (
    default_network_only,
    instance_expired,
    instance_is_public,
    resolve_public_host,
    ttl_remaining_s,
)
from cage.target.server.server_state import (  # noqa: F401
    BASE_DIR,
    BENCHMARK_ROOT,
    COMPOSE_UP_TIMEOUT_S,
    DOCKER_NETWORK,
    HEALTH_POLL_INTERVAL_S,
    HEALTH_TIMEOUT_S,
    HOST_IP,
    INSTANCE_HEALTH_TIMEOUT_S,
    NETWORK_REMOVE_RETRY_INTERVAL_S,
    NETWORK_REMOVE_RETRY_TIMEOUT_S,
    PORT_OPEN_STABILITY_CHECKS,
    STARTUP_POLL_INTERVAL_S,
    STARTUP_TIMEOUT_S,
    TARGET_SERVER_NAMESPACE,
    challenge_locks,
    find_free_port,
    get_docker_client,
    get_running_instance,
    invalidate_challenge_cache,
    load_all_challenges,
    load_benchmark_sources,
    pop_running_instance,
    recovery_coordinator,
    release_allocated_port,
    running_instances,
    running_instances_lock,
    set_running_instance,
    snapshot_running_instance_ids,
    update_running_instance,
)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# The serve API's own contract version — deliberately NOT the Python package
# version. ``info.version`` describes the HTTP contract a client codes against,
# and tying it to the distribution would both mis-describe it and make the
# committed schema (docs/openapi.json) depend on whether cage happens to be
# pip-installed in whoever regenerates it. Bump on a breaking change to the
# endpoints or their payloads; the repo versions its other contracts the same
# way (see ``serve_log.SCHEMA_VERSION``).
SERVE_API_VERSION = "1"

app = FastAPI(
    title="Cage target server",
    version=SERVE_API_VERSION,
    description=(
        "Serve (PULL) mode: an external agent lists challenges, launches an "
        "isolated target instance, attacks it, and submits its output for "
        "scoring — with no Cage-managed agent runtime.\n\n"
        "Endpoints are audience-gated: loopback callers are internal; "
        "non-loopback callers need `Authorization: Bearer <token>` when the "
        "server was started with `--external-token`.\n\n"
        "See `docs/serve-external-audience.md` in the Cage repo for the "
        "narrative contract, deployment model and worked examples."
    ),
)

# Self-contained management console (single HTML file, no build step, no CDN).
# Served at ``GET /`` so ``cage serve`` gives an operator a browsable target
# range, not just a JSON API. Its fetch calls hit the same audience-gated
# endpoints (/challenges, /instances, /launch), so serving the shell itself
# unauthenticated leaks nothing.
_CONSOLE_INDEX = os.path.join(os.path.dirname(__file__), "console", "index.html")


_LOOPBACK_HOSTS = {"127.0.0.1", "::1", "localhost"}


@app.get("/", include_in_schema=False)
def console():
    """Serve the target-range management console (falls back to a hint if absent)."""
    if os.path.isfile(_CONSOLE_INDEX):
        return FileResponse(_CONSOLE_INDEX, media_type="text/html")
    return HTMLResponse(
        "<h1>cage target server</h1><p>Console asset not found. "
        "API is up: <a href='/challenges'>/challenges</a>, "
        "<a href='/instances'>/instances</a>.</p>",
        status_code=200,
    )


def resolve_audience(request: Request) -> str:
    """Decide whether the caller is internal or external.

    Rules:
    - ``Authorization: Bearer <token>`` with a value matching the configured
      ``TARGET_SERVER_EXTERNAL_TOKEN`` → ``external``.
    - Bearer present but mismatched → 401.
    - No bearer + caller from 127.0.0.1/::1/localhost → ``internal``.
    - No bearer + non-loopback caller while a token IS configured → 401.
    - No bearer + token not configured (legacy mode) → ``internal`` (back-compat).
    """
    token_config = _server_state.EXTERNAL_TOKEN
    auth_header = request.headers.get("Authorization", "")
    bearer = ""
    if auth_header.startswith("Bearer "):
        bearer = auth_header[len("Bearer "):].strip()

    if bearer:
        if not token_config:
            # Token-not-configured server should not silently accept any bearer.
            raise HTTPException(
                status_code=401,
                detail="bearer auth not configured on this server",
            )
        if bearer != token_config:
            raise HTTPException(status_code=401, detail="invalid bearer token")
        return "external"

    client_host = request.client.host if request.client else "127.0.0.1"
    if client_host in _LOOPBACK_HOSTS:
        return "internal"

    if token_config:
        raise HTTPException(
            status_code=401,
            detail="bearer token required for non-loopback callers",
        )
    return "internal"


async def monitor_instances():
    """Background task: every minute, check every running instance and auto-restart unhealthy ones."""
    logger.info("Health monitor started.")
    while True:
        try:
            await asyncio.sleep(60)
            current_ids = snapshot_running_instance_ids()
            if not current_ids:
                continue

            logger.info(f"[Monitor] Scanning {len(current_ids)} instances for health...")

            for instance_key in current_ids:
                info = get_running_instance(instance_key)
                if info is None:
                    continue
                lifecycle_state = str(info.get("lifecycle_state", "") or "").strip().lower()
                if lifecycle_state in {"stopping", "cleanup", "restarting"}:
                    logger.info(
                        "[Monitor] Skipping instance %s because lifecycle_state=%s",
                        instance_key,
                        lifecycle_state,
                    )
                    continue
                # per_agent instances are owned by individual workers; skip auto-restart.
                target_scope = str(info.get("target_scope", "") or "").strip().lower()
                if target_scope == "per_agent":
                    continue
                chal_id = str(info.get("chal_id") or instance_key)

                if not is_instance_healthy(instance_key):
                    logger.warning(
                        f"[Monitor] 🚨 Instance {instance_key} (challenge {chal_id}) found UNHEALTHY. Initiating auto-restart..."
                    )
                    try:
                        update_running_instance(instance_key, lifecycle_state="restarting")
                        # Background monitor calls launch_challenge as a plain python
                        # function (not via FastAPI), so the Depends() default for
                        # ``audience`` isn't resolved. Recover whatever audience the
                        # instance was originally launched with so bind-IPs survive
                        # the restart.
                        restart_audience = str(info.get("audience") or "internal").lower()
                        # Preserve the instance's publish intent across the
                        # restart: a published instance re-publishes, a
                        # network-only one stays network-only.
                        restart_network_only = not bool(info.get("public_intent"))
                        if instance_key != chal_id:
                            await asyncio.to_thread(cleanup_instance, chal_id, instance_key)
                            await asyncio.to_thread(
                                launch_challenge,
                                chal_id=chal_id,
                                force_recreate=False,
                                audience=restart_audience,
                                network_only=restart_network_only,
                            )
                        else:
                            await asyncio.to_thread(
                                launch_challenge,
                                chal_id=chal_id,
                                force_recreate=True,
                                audience=restart_audience,
                                network_only=restart_network_only,
                            )
                        logger.info(f"[Monitor] ✅ Instance {instance_key} successfully restarted.")
                    except Exception as e:
                        logger.error(f"[Monitor] ❌ Failed to auto-restart {instance_key}: {e}")

        except asyncio.CancelledError:
            logger.info("[Monitor] Task cancelled, stopping.")
            break
        except Exception as e:
            logger.error(f"[Monitor] Unexpected error in monitor loop: {e}")
            await asyncio.sleep(5)


async def reap_expired_instances():
    """Background task: tear down instances whose ``?ttl=`` lease has run out.

    A lease is declared per launch, because how long a target is needed is a
    property of the attempt, not of the server. Without a reaper the lease would
    be decoration — and on an external-access server it is load-bearing: host
    -published slots are capped, so one agent that launches and walks away would
    otherwise block every other agent until the server restarts.

    In-flight instances are skipped: an instance still launching has not started
    its lease (``created_at`` is re-stamped when it goes ``running``), and one
    already stopping is somebody else's job.
    """
    interval = max(1.0, float(_server_state.INSTANCE_REAP_INTERVAL_S))
    while True:
        try:
            await asyncio.sleep(interval)
            for instance_key in snapshot_running_instance_ids():
                info = get_running_instance(instance_key)
                if info is None or not instance_expired(info):
                    continue
                lifecycle_state = str(info.get("lifecycle_state", "") or "").strip().lower()
                if lifecycle_state != "running":
                    continue
                chal_id = str(info.get("chal_id") or instance_key)
                logger.info(
                    "[Reaper] Instance %s (challenge %s) reached its %ss lease; removing.",
                    instance_key, chal_id, info.get("ttl_s"),
                )
                update_running_instance(instance_key, lifecycle_state="stopping")
                try:
                    await asyncio.to_thread(cleanup_instance, chal_id, instance_key)
                except Exception as exc:  # noqa: BLE001
                    logger.error("[Reaper] Failed to remove %s: %s", instance_key, exc)
        except asyncio.CancelledError:
            logger.info("[Reaper] Task cancelled, stopping.")
            break
        except Exception as exc:  # noqa: BLE001
            logger.error("[Reaper] Unexpected error: %s", exc)
            await asyncio.sleep(5)


def _startup_gc_namespace_scoped() -> None:
    """Reclaim docker resources from non-running runs in this namespace.

    Runs label-sweep + liveness GC at server startup so that a server
    restart after SIGKILL / OOM / host reboot doesn't leave the host
    accumulating crashed-run containers / networks / named volumes.

    Strictly namespace-scoped (only touches resources whose
    ``cage.target.namespace`` label matches this server's
    namespace). Composes cleanly with the cross-namespace peer
    reclamation that lives in ``cleanup_orphan_networks`` on main —
    the two operate on disjoint label sets.

    Skipped (with a warning) when:
      * ``CAGE_STARTUP_GC=0`` (operator opt-out)
      * No ``.cage_runs/`` root is reachable from the server's working
        directory — without artifacts we can't distinguish alive from
        dead, and reclaiming everything would be catastrophic. The
        user can still invoke ``cage gc --apply --root <path>``
        explicitly when they want.
    """
    raw = os.getenv("CAGE_STARTUP_GC", "1").strip().lower()
    # Treat empty string as "use default" (on), not as opt-out — empty
    # env vars usually mean "the user exported without a value", not "I
    # explicitly want the feature off".
    if raw in {"0", "false", "no"}:
        logger.info("startup-gc: disabled via CAGE_STARTUP_GC=%r", raw)
        return

    from cage.gc.runner import default_cage_runs_roots, gc_all

    roots = default_cage_runs_roots()
    if not roots:
        logger.info(
            "startup-gc: no .cage_runs/ root discoverable from cwd=%s — skipping; "
            "set CAGE_RUNS_ROOT env or run `cage gc --apply --root <path>` "
            "manually to clean up after crashes",
            os.getcwd(),
        )
        return
    try:
        report = gc_all(namespace=TARGET_SERVER_NAMESPACE, apply=True, search_roots=roots)
    except Exception as exc:
        logger.warning("startup-gc failed: %s", exc)
        return
    summary = report.summary()
    if summary["removed"]["containers"] or summary["removed"]["networks"] or summary["removed"]["volumes"]:
        logger.info(
            "startup-gc: reclaimed containers=%d networks=%d volumes=%d "
            "(alive=%d dead=%d orphan=%d)",
            summary["removed"]["containers"],
            summary["removed"]["networks"],
            summary["removed"]["volumes"],
            summary["alive"],
            summary["dead"],
            summary["orphan"],
        )
    else:
        logger.info(
            "startup-gc: nothing to reclaim "
            "(alive=%d dead=%d orphan=%d)",
            summary["alive"],
            summary["dead"],
            summary["orphan"],
        )


@app.on_event("startup")
async def startup_event():
    # Order matters:
    #   1. cleanup_orphan_networks — namespace-scoped network sweep
    #      (uses ``cage.target.namespace`` label).
    #   2. cleanup_orphan_volumes — namespace-scoped volume sweep
    #      (now requires the namespace label to be present; legacy
    #      unlabelled volumes are left alone).
    #   3. ensure_docker_network — claims exclusive namespace ownership.
    #      If a peer server is alive on the same namespace, this fails
    #      and we abort before doing the heavier liveness-based GC,
    #      because we'd otherwise risk reclaiming the live peer's
    #      runs.
    #   4. _startup_gc_namespace_scoped — liveness-based reclamation
    #      keyed on .cage_runs/<rid>/. Only runs after this server has
    #      asserted ownership of the namespace, so a live peer cannot
    #      have its runs misclassified as dead. Runs in the BACKGROUND:
    #      on a real repo the .cage_runs tree can be enormous (many runs,
    #      100k+-file workspaces) and a blocking scan held the server from
    #      binding for minutes — an operator's `cage benchmark serve` would
    #      appear to hang. Ownership is already asserted above, so the GC is
    #      safe to run behind the live server; it targets dead runs only.
    await asyncio.to_thread(cleanup_orphan_networks)
    await asyncio.to_thread(cleanup_orphan_volumes)
    ensure_docker_network()
    asyncio.create_task(asyncio.to_thread(_startup_gc_namespace_scoped))
    asyncio.create_task(monitor_instances())
    asyncio.create_task(reap_expired_instances())
    # Reconcile durable launch operations against Docker after a restart: finish
    # interrupted teardowns, re-drive interrupted launches, leave terminal ones.
    # Runs in a thread — it may purge docker resources and re-enqueue work.
    asyncio.create_task(asyncio.to_thread(launch_ops.get_orchestrator().reconcile_on_startup))


@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Shutting down server, cleaning up all containers...")
    chal_ids = snapshot_running_instance_ids()
    if chal_ids:
        tasks = [asyncio.to_thread(cleanup_instance, cid) for cid in chal_ids]
        await asyncio.gather(*tasks, return_exceptions=True)
        with running_instances_lock:
            running_instances.clear()

    launch_ops.get_orchestrator().shutdown()
    await asyncio.to_thread(_remove_own_docker_network)


@app.delete("/launch/{chal_id}", response_model=StopResponse)
def stop_challenge(
    chal_id: str,
    run_id: Annotated[str, Query(description="Specific runtime instance id to stop. REQUIRED — DELETE always operates on exactly one instance.")],
):
    """Stop and clean up exactly one running challenge target.

    ``run_id`` is mandatory. A DELETE that didn't carry it used to fall
    through to ``cleanup_instance(chal_id, run_id=None)`` which, combined
    with the registry's old chal_id-fallback lookup, silently destroyed
    *some other agent's* per_agent instance. Both halves of that bug have
    been removed: registry helpers are now strict-key-only, and this
    endpoint refuses calls that don't name a specific instance.
    """
    if not run_id:
        raise HTTPException(
            status_code=400,
            detail="run_id query parameter is required (one DELETE = one target)",
        )
    if get_running_instance(run_id) is None:
        # Instance not in registry. Don't try to guess — could be already
        # cleaned up by a prior DELETE, or never registered (launch error
        # path took ``_purge_project_by_name`` before ``set_running_instance``).
        # Either way, nothing else to do.
        return StopResponse(
            status="stopped",
            chal_id=chal_id,
            message=f"Instance {run_id} not in memory; no action taken.",
        )

    update_running_instance(run_id, lifecycle_state="stopping")
    captured_logs = cleanup_instance(chal_id, run_id=run_id)
    return StopResponse(
        status="stopped",
        chal_id=chal_id,
        message="Instance stopped and removed.",
        container_logs=captured_logs or [],
    )


# DELETE /run/{cage_run_id} removed: batch teardown was the wrong shape.
# A single endpoint that killed every instance for a run amplified cleanup
# bugs (one stale call → N orphaned agents) and hid which trial owned what.
# Run-end teardown now happens client-side by iterating ``_runtime_cache``
# and issuing per-instance ``DELETE /launch?run_id=<id>``. Belt-and-
# suspenders label-sweep for crashed processes lives in
# ``cage.target.local_cleanup.sweep_run`` (orchestrator-side).


@app.get("/launch/{chal_id}", response_model=LaunchResponse)
def launch_challenge(
    chal_id: str,
    request: Request = None,  # type: ignore[assignment]
    force_recreate: Annotated[bool, Query(description="If true, shutdown existing instance and create a fresh one.")] = False,
    parallel_mode: Annotated[Optional[str], Query(description="Parallelization strategy: network or alias.")] = None,
    target_scope: Annotated[Optional[str], Query(description="Target allocation scope: per_challenge or per_agent.")] = None,
    network_mode: Annotated[Optional[str], Query(description="Compose launch mode: compose_project_local or shared_external. Experiment default; challenge.json wins if it declares one.")] = None,
    exposure_mode: Annotated[Optional[str], Query(description="Service exposure: host_ports or internal. Experiment default; challenge.json wins if it declares one. Independent of network_only.")] = None,
    cage_run_id: Annotated[Optional[str], Query(description="Cage-side run id. Stamped as cage.run_id label on every container/network.")] = None,
    network_only: Annotated[Optional[bool], Query(description="Keep this target on the docker network only (no host port) — reach it via the returned container_addr. Default: on for a normal server, OFF on a --public-host server (which publishes every launch's declared entry). Pass network_only=true to keep one launch off the host even on a --public-host server; network_only=false to host-publish one launch on a normal server.")] = None,
    prompt_level: Annotated[Optional[str], Query(description="Hint tier (l0/l1/l2) bound to THIS instance for GET /prompt. l0 = no hints; l1/l2 progressively reveal vuln location / topology. Default: the server's --prompt-level. Set per-launch so instances on one server can differ without restarting serve.")] = None,
    ttl: Annotated[Optional[int], Query(description="Lease in seconds: reap this instance automatically once it expires. Declared per launch because how long a target is needed is a property of the attempt, not of the server. Omit to run until DELETEd. On an external-access server the lease is what stops an agent that walks away from holding a host-published slot forever.")] = None,
    audience: str = Depends(resolve_audience),
):
    # Network-only by default so an agent reaches a target over the isolated
    # docker network at its container_addr, never a host port. On a
    # ``--public-host`` server the default flips to PUBLISH — for every launch,
    # not just off-host callers: such a server is dedicated to serving off-host
    # agents (cage run never sets --public-host, so its trials stay network-only
    # regardless). Neither the caller's address nor the bearer token enters into
    # it. An explicit ?network_only= always wins.
    if network_only is None:
        network_only = default_network_only()

    # The address to advertise in entry_urls. Derived from the address THIS caller
    # just reached us at, unless the operator pinned one with --public-host.
    public_host, public_host_source = resolve_public_host(
        request.headers.get("host", "") if request is not None else ""
    )

    # Hint tier is bound to the instance at LAUNCH (read back by GET /prompt), so
    # varying it per launch never needs a serve restart. ``--prompt-level`` is the
    # server-wide default when a launch doesn't specify one.
    effective_prompt_level = _normalize_prompt_level(prompt_level, _resolve_prompt_level())

    # Resolve target_scope early to decide locking strategy. For per_agent each launch
    # gets a unique run_id, so the per-chal lock would needlessly serialize concurrent
    # samples and cause multi-minute startup delays under batch concurrency.
    effective_scope = "per_challenge"
    try:
        challenges = load_all_challenges()
        if chal_id in challenges:
            effective_scope = resolve_server_target_scope(challenges[chal_id], target_scope)
    except Exception:
        pass

    if effective_scope == "per_agent":
        return _launch_challenge_impl(
            chal_id=chal_id,
            force_recreate=force_recreate,
            parallel_mode=parallel_mode,
            target_scope=target_scope,
            network_mode=network_mode,
            exposure_mode=exposure_mode,
            cage_run_id=cage_run_id,
            audience=audience,
            network_only=network_only,
            prompt_level=effective_prompt_level,
            public_host=public_host,
            public_host_source=public_host_source,
            ttl_s=ttl,
        )

    lock = challenge_locks.get_lock(chal_id)

    if force_recreate:
        def is_healthy() -> bool:
            instance = get_running_instance(chal_id)
            return instance is not None and is_instance_healthy(chal_id)

        def recover_action() -> LaunchResponse:
            with lock:
                return _launch_challenge_impl(
                    chal_id=chal_id,
                    force_recreate=True,
                    parallel_mode=parallel_mode,
                    target_scope=target_scope,
                    network_mode=network_mode,
                    exposure_mode=exposure_mode,
                    cage_run_id=cage_run_id,
                    audience=audience,
                    network_only=network_only,
                    prompt_level=effective_prompt_level,
                    public_host=public_host,
                    public_host_source=public_host_source,
                    ttl_s=ttl,
                )

        result = recovery_coordinator.run_serialized_recovery(
            runtime_key=chal_id,
            is_healthy=is_healthy,
            recover_action=recover_action,
        )
        if result == "reused_recent":
            existing_instance = get_running_instance(chal_id)
            if existing_instance and is_instance_healthy(chal_id):
                logger.info("Reusing recently recovered instance for %s", chal_id)
                return _reused_launch_response(
                    chal_id,
                    existing_instance,
                    audience=audience,
                    public_host=public_host,
                    public_host_source=public_host_source,
                )
            with lock:
                return _launch_challenge_impl(
                    chal_id=chal_id,
                    force_recreate=True,
                    parallel_mode=parallel_mode,
                    target_scope=target_scope,
                    network_mode=network_mode,
                    exposure_mode=exposure_mode,
                    cage_run_id=cage_run_id,
                    audience=audience,
                    network_only=network_only,
                    prompt_level=effective_prompt_level,
                    public_host=public_host,
                    public_host_source=public_host_source,
                    ttl_s=ttl,
                )
        return result

    with lock:
        return _launch_challenge_impl(
            chal_id=chal_id,
            force_recreate=force_recreate,
            parallel_mode=parallel_mode,
            target_scope=target_scope,
            network_mode=network_mode,
            exposure_mode=exposure_mode,
            cage_run_id=cage_run_id,
            audience=audience,
            network_only=network_only,
            prompt_level=effective_prompt_level,
            public_host=public_host,
            public_host_source=public_host_source,
            ttl_s=ttl,
        )


# --------------------------------------------------------------------------- #
# Asynchronous, idempotent launch operations (issue #4)
# --------------------------------------------------------------------------- #
# Wire the orchestrator to the real provisioning/health/cleanup functions. Done
# here (not at launch_ops import) so the module stays free of a hard import cycle.
launch_ops.configure(
    provision=_launch_challenge_impl,
    health=is_instance_healthy,
    get_instance=get_running_instance,
    load_challenges=load_all_challenges,
    render_prompt=render_task_prompt,
    cleanup_instance=cleanup_instance,
    purge_by_run_id=purge_by_cage_run_id,
    has_resources=has_resources_for_cage_run_id,
)


def _launch_op_params(req: LaunchOpRequest, request: Request, audience: str) -> dict:
    """Freeze everything provisioning needs into the durable op record.

    ``audience`` and the advertised ``public_host`` are captured HERE, from this
    request, because the actual provisioning runs later on a worker thread with
    no request in scope.
    """
    public_host, public_host_source = resolve_public_host(
        request.headers.get("host", "") if request is not None else ""
    )
    network_only = req.network_only
    if network_only is None:
        network_only = default_network_only()
    return {
        "cage_run_id": req.cage_run_id,
        "challenge_id": req.challenge_id,
        "target_scope": req.target_scope,
        "network_only": bool(network_only),
        "prompt_level": _normalize_prompt_level(req.prompt_level, _resolve_prompt_level()),
        "parallel_mode": req.parallel_mode,
        "network_mode": req.network_mode,
        "exposure_mode": req.exposure_mode,
        "ttl": req.ttl,
        "audience": audience,
        "public_host": public_host,
        "public_host_source": public_host_source,
    }


@app.post("/launches", response_model=LaunchOpStatus)
def create_launch(
    req: LaunchOpRequest,
    response: Response,
    request: Request = None,  # type: ignore[assignment]
    audience: str = Depends(resolve_audience),
):
    """Accept a launch as a durable async operation — the orchestration-safe path.

    Provisioning (minutes for a multi-host range) runs in the background; this
    returns immediately. The operation id is ``cage_run_id``, so the call is
    idempotent: a repeat with the same params returns the same operation and
    never builds a second container set (``202`` while pending, ``200`` with the
    terminal representation once ready/failed/closed); a repeat with different
    params is ``409``. Poll ``status_url`` (honouring ``Retry-After``) until
    ``ready`` — which guarantees a non-empty ``run_id``, a reachable target
    address, and a non-empty ``task_prompt``. See ``GET /launches/{id}``.
    """
    if not str(req.cage_run_id or "").strip():
        raise HTTPException(400, "cage_run_id is required (it is the launch operation's id)")
    if not str(req.challenge_id or "").strip():
        raise HTTPException(400, "challenge_id is required")
    try:
        load_all_challenges()  # surface a bad registry early
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(500, f"challenge registry unavailable: {exc}")

    orch = launch_ops.get_orchestrator()
    params = _launch_op_params(req, request, audience)
    try:
        op, created = orch.submit(req.cage_run_id, params)
    except launch_ops.LaunchOpError as exc:
        raise HTTPException(exc.http_status, {"error": exc.code, "message": exc.message})

    # 202 while the op is still doing work (new or a pending duplicate); 200 once
    # a duplicate POST finds an already-terminal operation.
    response.status_code = 202 if (created or op.is_pending()) else 200
    view = launch_ops.status_view(op)
    response.headers["Location"] = view["status_url"]
    if "retry_after" in view:
        response.headers["Retry-After"] = str(view["retry_after"])
    return view


@app.get("/launches/{launch_id}", response_model=LaunchOpStatus)
def get_launch(launch_id: str, _audience: str = Depends(resolve_audience)):
    """The one authoritative representation of a launch operation.

    ``status`` walks ``queued → starting → ready | failed`` (and ``… → closing →
    closed`` on cancel). While pending, ``200`` carries ``status`` +
    ``retry_after``; a terminal *operation* failure is still ``200`` with
    ``status=failed`` (the query itself succeeded). Only auth/'"unknown id"'
    are non-200 (401/404). A ``ready`` body carries the full ``result``.
    """
    op = launch_ops.get_orchestrator().store.get(launch_id)
    if op is None:
        raise HTTPException(404, f"no launch operation with id {launch_id!r}")
    return launch_ops.status_view(op)


@app.delete("/launches/{launch_id}", response_model=LaunchOpStatus)
def cancel_launch(launch_id: str, response: Response,
                  _audience: str = Depends(resolve_audience)):
    """Idempotently cancel + tear down a launch operation.

    Works in ``queued``, ``starting``, and ``ready`` — crucially even before an
    internal ``run_id`` exists (the case the ``run_id``-keyed ``DELETE /launch``
    cannot handle): teardown also purges any docker resources tagged with this
    ``cage_run_id``. Reaches ``closed`` only once containers/networks are
    confirmed gone.

    When cleanup cannot finish in the request — a provisioning worker is still
    in flight, or a first teardown left resources behind — this returns ``202``
    with ``status=closing``; poll the status URL (honouring ``Retry-After``)
    until ``200`` with ``status=closed``. Repeating it is idempotent throughout.
    """
    op = launch_ops.get_orchestrator().cancel(launch_id)
    if op is None:
        raise HTTPException(404, f"no launch operation with id {launch_id!r}")
    response.status_code = 202 if op.status == launch_ops.CLOSING else 200
    view = launch_ops.status_view(op)
    if "retry_after" in view:
        response.headers["Retry-After"] = str(view["retry_after"])
    return view


def _challenge_objectives(source_fields: dict) -> tuple[int, str]:
    """How many objectives a challenge is scored out of, and what one is called.

    A result's progress is ``achieved / objectives``, but the unit depends on the
    task's shape: a single-target app declares one objective per vulnerability, a
    multi-host range one per *host* it is possible to own. This must agree with
    what the scorer divides by, or a caller sees a denominator that never
    matches the score it later reads.

    A range's marker stages are not the count. Several stages can belong to one
    host (a user shell and then root), and a stage whose kind proves no
    ownership — a file read on a host with no execution path at all — is not an
    objective a run can ever complete. Counting stages would therefore advertise
    a denominator larger than the reachable one.

    Returns ``(0, "")`` when the challenge declares no objectives.
    """
    vulnerabilities = source_fields.get("vulnerabilities")
    if isinstance(vulnerabilities, list) and vulnerabilities:
        return len(vulnerabilities), "vulnerability"

    stages = source_fields.get("marker_stages")
    if isinstance(stages, list) and stages:
        declared, _ = range_objectives(stages)
        if declared:
            return len(declared), "host"
    return 0, ""


@app.get("/challenges", response_model=list[ChallengeSummary])
def list_challenges(
    benchmark: Annotated[Optional[str], Query(description="Filter by benchmark name (exact match).")] = None,
    category: Annotated[Optional[str], Query(description="Filter by category (exact match).")] = None,
    _audience: str = Depends(resolve_audience),
):
    """List challenges with public-safe metadata only.

    Strictly excludes flag, verify scripts, ``agent_input``, and any
    ``source_fields`` content. ``entry_service_count`` is the number of
    user-facing entry services (web challenges declare them as
    ``application_service_keys``, post-exploitation ranges as ``entry_services``):
    1 for a single-entry web challenge, 2+ for a multi-entry range.

    ``objective_count`` is what a result is scored out of, available here BEFORE
    anything is launched, with ``objective_kind`` naming the unit
    (``vulnerability`` / ``marker``). It is the same number the scorer later
    reports as ``objective_total``. Note that it is NOT ``entry_service_count``:
    a range can publish more entry services than it has objectives.

    Authentication is the same as ``/launch``: loopback OR bearer token.
    """
    try:
        challenges = load_all_challenges()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"failed to load challenges: {exc}")

    benchmark_filter = (benchmark or "").strip() or None
    category_filter = (category or "").strip() or None

    results: list[ChallengeSummary] = []
    for chal_id, meta in challenges.items():
        bench = str(meta.get("benchmark") or meta.get("benchmark_name") or "")
        cat = str(meta.get("category") or "unknown")
        if benchmark_filter and bench != benchmark_filter:
            continue
        if category_filter and cat != category_filter:
            continue
        source_fields = meta.get("source_fields", {}) or {}
        # Web challenges declare their user-facing entries as
        # ``application_service_keys``; post-exploitation ranges declare them as
        # ``entry_services``. Fall back the same way ``submit._challenge_task``
        # does so ``entry_service_count`` reflects post ranges (2+), not 0.
        entry_keys = (
            source_fields.get("application_service_keys")
            or source_fields.get("entry_services")
            or []
        )
        if isinstance(entry_keys, str):
            entry_keys = [entry_keys]
        objective_count, objective_kind = _challenge_objectives(source_fields)
        results.append(ChallengeSummary(
            id=str(chal_id),
            name=str(meta.get("name") or chal_id),
            benchmark=bench,
            category=cat,
            description=str(meta.get("description") or meta.get("task") or ""),
            task_profile=str(meta.get("task_profile") or ""),
            entry_service_count=len([k for k in entry_keys if k]),
            objective_count=objective_count,
            objective_kind=objective_kind,
        ))
    results.sort(key=lambda item: (item.benchmark, item.id))
    return results


def _project_instance(
    info: dict,
    *,
    audience: str,
    challenges: dict,
    probe_health: bool,
    public_host: str = "",
    public_host_source: str = "",
) -> InstanceSummary:
    """Project a running-instance registry dict into a public-safe summary.

    Mirrors ``_reused_launch_response``'s entry-url reconstruction so the
    console shows the same client-usable URLs a fresh launch would return,
    but strips scoring/debug internals. ``probe_health`` gates the (per
    instance, docker-touching) live health check; without it the console
    still gets the cheap ``lifecycle_state`` string.
    """
    chal_id = str(info.get("chal_id") or "")
    run_id = str(info.get("run_id") or "")
    meta = challenges.get(chal_id, {}) or {}
    # The registry keeps epoch seconds (arithmetic wants a number); the wire
    # carries RFC 3339 (readers want a timestamp). Compute uptime from the raw
    # value, then format for output — never the other way round.
    created_at = info.get("created_at")
    uptime = (time.time() - created_at) if isinstance(created_at, (int, float)) else None

    services = info.get("services") or []
    entry_keys = set(info.get("entry_service_keys") or [])
    entry_urls: list[EntryUrl] = []
    entry_url_source = ""
    if instance_is_public(info):
        advertise_host = public_host
        entry_url_source = public_host_source
        if not advertise_host:
            advertise_host, entry_url_source = resolve_public_host("")
        entry_urls = _build_entry_urls(
            services=services,
            entry_service_keys=entry_keys,
            host_ip=advertise_host,
        )

    healthy: Optional[bool] = None
    if probe_health and run_id:
        try:
            healthy = is_instance_healthy(run_id)
        except Exception:  # a flaky probe must not 500 the whole list
            healthy = None

    return InstanceSummary(
        run_id=run_id,
        chal_id=chal_id,
        benchmark=str(meta.get("benchmark") or meta.get("benchmark_name") or ""),
        category=str(meta.get("category") or ""),
        target_scope=str(info.get("target_scope") or ""),
        audience=str(info.get("audience") or ""),
        cage_run_id=str(info.get("cage_run_id") or ""),
        lifecycle_state=str(info.get("lifecycle_state") or ""),
        healthy=healthy,
        created_at=epoch_to_rfc3339(created_at),
        uptime_s=round(uptime, 1) if uptime is not None else None,
        network_name=info.get("network_name"),
        network_subnet=info.get("network_subnet"),
        network_gateway=info.get("network_gateway"),
        service_count=len(services),
        entry_urls=entry_urls,
        entry_url_source=entry_url_source if entry_urls else "",
        public=instance_is_public(info),
        ttl_s=info.get("ttl_s"),
        ttl_remaining_s=ttl_remaining_s(info),
        container_addr=build_container_addrs(services, entry_keys),
    )


@app.get("/instances", response_model=list[InstanceSummary])
def list_instances(
    request: Request = None,  # type: ignore[assignment]
    probe: Annotated[bool, Query(description="Run a live per-instance docker health check (slower). Default: report only the cached lifecycle_state.")] = False,
    audience: str = Depends(resolve_audience),
):
    """List every target instance this server currently has running.

    The management view the launch/stop API always lacked: without it a
    console can start and kill targets but never *see* what is up. Public-safe
    (no flag / verify / scoring secret) and audience-gated exactly like
    ``/challenges`` and ``/launch``.
    """
    try:
        challenges = load_all_challenges()
    except Exception:
        challenges = {}

    public_host, public_host_source = resolve_public_host(
        request.headers.get("host", "") if request is not None else ""
    )
    summaries: list[InstanceSummary] = []
    for key in snapshot_running_instance_ids():
        info = get_running_instance(key)
        if info is None:
            continue
        summaries.append(
            _project_instance(
                info,
                audience=audience,
                challenges=challenges,
                probe_health=probe,
                public_host=public_host,
                public_host_source=public_host_source,
            )
        )
    summaries.sort(key=lambda s: (s.chal_id, s.run_id))
    return summaries


async def _read_upload_capped(upload: UploadFile, content_length: str = "") -> bytes:
    """Read an uploaded archive, refusing anything over the size cap.

    The body is read into memory to be unpacked, so "however big the caller
    sent" is a memory lever any caller can pull. A declared ``Content-Length``
    over the cap is rejected before a byte is read; a lying or absent one is
    caught while streaming.
    """
    limit = int(_server_state.MAX_SUBMIT_UPLOAD_BYTES)
    if limit <= 0:
        return await upload.read()

    def _too_large(size_hint: str) -> HTTPException:
        return HTTPException(
            status_code=413,
            detail=(
                f"agent_output exceeds the {limit} byte upload limit ({size_hint}). "
                "Submit only the final_answer/ reports, not the whole workspace."
            ),
        )

    declared = str(content_length or "").strip()
    if declared.isdigit() and int(declared) > limit:
        raise _too_large(f"Content-Length {declared}")

    chunks: list[bytes] = []
    total = 0
    while True:
        chunk = await upload.read(1024 * 1024)
        if not chunk:
            break
        total += len(chunk)
        if total > limit:
            raise _too_large(f"body exceeded it after {total} bytes")
        chunks.append(chunk)
    return b"".join(chunks)


def _safe_extract_upload(raw: bytes, dest: Path) -> None:
    """Unpack an uploaded agent-output archive into ``dest`` (tar.gz or zip).

    Path-traversal safe: tar uses the ``data`` filter (rejects absolute paths,
    ``..``, and special files); zip members are individually validated. A body
    that is neither archive is ignored — marker-only post-exploitation
    challenges submit no agent output at all.
    """
    if not raw:
        return
    import io

    bio = io.BytesIO(raw)
    if raw[:2] == b"PK":  # zip
        with zipfile.ZipFile(bio) as zf:
            for member in zf.namelist():
                target = (dest / member).resolve()
                if not str(target).startswith(str(dest.resolve())):
                    raise HTTPException(400, f"unsafe path in archive: {member}")
            zf.extractall(dest)
        return
    try:
        with tarfile.open(fileobj=bio, mode="r:*") as tf:
            tf.extractall(dest, filter="data")  # type: ignore[arg-type]
        return
    except tarfile.TarError as exc:
        raise HTTPException(400, f"unrecognized agent_output archive: {exc}")


def _resolve_submit_judge() -> Optional[dict]:
    """Optional judge-model config for the ``LLM_judge`` scoring signal.

    Read from ``TARGET_SERVER_JUDGE_JSON`` (inline JSON). Absent → verifier-only
    scoring; ``LLM_judge`` vulns then report "no judge model configured". This
    is the one piece of scoring that needs an API key, and it is injected
    server-side, never carried on the submission.
    """
    raw = os.getenv("TARGET_SERVER_JUDGE_JSON", "").strip()
    if not raw:
        return None
    try:
        parsed = json.loads(raw)
        return parsed if isinstance(parsed, dict) else None
    except json.JSONDecodeError:
        logger.warning("TARGET_SERVER_JUDGE_JSON is not valid JSON; ignoring")
        return None


def _resolve_prompt_level() -> str:
    """The server-wide DEFAULT hint tier for launches that don't specify one.

    Read from ``TARGET_SERVER_PROMPT_LEVEL`` (``l0``/``l1``/``l2``; default
    ``l0`` = no hints), set by ``cage benchmark serve --prompt-level``. The
    effective tier is bound per-instance at ``/launch`` (``?prompt_level=``) and
    falls back to this default — so varying it never needs a serve restart.
    """
    return _normalize_prompt_level(os.getenv("TARGET_SERVER_PROMPT_LEVEL", ""), "l0")


def _normalize_prompt_level(value: Optional[str], default: str) -> str:
    """Coerce a requested hint tier to ``l0``/``l1``/``l2``, else ``default``."""
    text = str(value or "").strip().lower()
    return text if text in {"l0", "l1", "l2"} else default


def _resolve_agent_id(request: Request) -> str:
    """Stable id for the external agent, used to scope its serve experiment run.

    An explicit ``X-Client-Id`` header wins (sanitized). Otherwise the bearer
    token identifies the agent — hashed, never stored raw. Loopback callers with
    neither are the single ``local`` agent. Each distinct id gets its own
    ``.cage_runs/serve__<agent_id>/serve/`` experiment that accumulates trials.
    """
    client_id = (request.headers.get("X-Client-Id") or "").strip()
    if client_id:
        return "agent_" + re.sub(r"[^A-Za-z0-9_.-]", "_", client_id)[:40]
    auth = request.headers.get("Authorization") or ""
    if auth.lower().startswith("bearer "):
        token = auth[7:].strip()
        if token:
            return "agent_" + hashlib.sha256(token.encode("utf-8")).hexdigest()[:12]
    return "local"


@app.post("/submit/{run_id}", response_model=SubmitResponse)
async def submit_challenge(
    run_id: str,
    request: Request,
    agent_output: Annotated[
        Optional[UploadFile],
        File(description="tar.gz/zip of the agent output dir (its final_answer/ holds per-vuln reports). Omit for marker-only post-exploitation challenges. Bodies over the server's upload limit (1 GiB default) are rejected with 413."),
    ] = None,
    close: Annotated[bool, Query(description="Tear the instance down (DELETE) after scoring. Default: keep it up (e.g. for inspection). One submission per instance either way.")] = False,
    label: Annotated[str, Query(description="Optional human-friendly name for this submission's record, for easy lookup (prefixes the .cage_serve dir). Not an identity — may be empty or repeat.")] = "",
    audience: str = Depends(resolve_audience),
):
    """Score one submission against a still-running serve-only instance.

    Closes the PULL benchmark loop: the agent launched an isolated instance,
    attacked it, and (for web) produced a ``final_answer/`` output — omit the
    upload entirely for marker-only post-exploitation ranges, which are scored
    from live target state. This gathers LIVE evidence against the still-up
    target and scores it with the challenge's benchmark scorer, writing a
    serve-native submission record under ``.cage_serve``. Gather needs the
    target alive, so scoring runs before any ``?close=true`` teardown.
    Audience-gated like ``/launch``.

    **One submission per instance.** The verdict is locked in on the first call;
    a repeat for the same ``run_id`` returns it unchanged (``already_submitted``)
    so an agent cannot resubmit to fish for a pass. Launch a fresh instance for
    another attempt.
    """
    instance = get_running_instance(run_id)
    if instance is None:
        raise HTTPException(404, f"no running instance for run_id={run_id!r}")
    chal_id = str(instance.get("chal_id") or "")

    # One submission per instance: return the locked-in verdict on any repeat.
    prior = instance.get("submission")
    if isinstance(prior, dict):
        return SubmitResponse(
            run_id=run_id,
            chal_id=chal_id,
            benchmark_module=prior.get("benchmark_module", ""),
            scores=prior.get("scores", {}),
            run_dir=prior.get("run_dir", ""),
            closed=False,
            already_submitted=True,
        )
    try:
        challenge = load_all_challenges().get(chal_id)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(500, f"challenge registry unavailable: {exc}")
    if challenge is None:
        raise HTTPException(404, f"challenge {chal_id!r} not found in registry")

    workdir = Path(tempfile.mkdtemp(prefix="cage_submit_"))
    try:
        if agent_output is not None:
            _safe_extract_upload(
                await _read_upload_capped(
                    agent_output,
                    request.headers.get("content-length", "") if request is not None else "",
                ),
                workdir,
            )
        try:
            result = score_submission(
                run_id=run_id,
                agent_output_dir=workdir,
                instance=instance,
                challenge=challenge,
                agent_id=_resolve_agent_id(request),
                label=label,
                judge=_resolve_submit_judge(),
            )
        except SubmissionError as exc:
            raise HTTPException(400, str(exc))
    finally:
        shutil.rmtree(workdir, ignore_errors=True)

    # Lock the verdict onto the instance so a repeat submit returns it unchanged.
    verdict = {
        "benchmark_module": result.get("benchmark_module", ""),
        "scores": result.get("scores", {}),
        "run_dir": result.get("run_dir", ""),
    }
    if get_running_instance(run_id) is not None:
        update_running_instance(run_id, submission=verdict)

    if close:
        update_running_instance(run_id, lifecycle_state="stopping")
        cleanup_instance(chal_id, run_id=run_id)

    return SubmitResponse(
        run_id=run_id,
        chal_id=chal_id,
        benchmark_module=verdict["benchmark_module"],
        scores=verdict["scores"],
        run_dir=verdict["run_dir"],
        closed=close,
        already_submitted=False,
    )


def _serve_roots() -> list[Path]:
    """The ``.cage_serve`` trees this server's submissions live in."""
    try:
        challenges = load_all_challenges()
    except Exception:  # noqa: BLE001 — lookup must survive a bad registry
        challenges = {}
    return rescore.discover_serve_roots(challenges, BENCHMARK_ROOT)


def _resolve_rescore_judge(models: list[str]) -> Optional[dict]:
    """Judge config for a re-judge: the caller's models, else the server's."""
    named = [m.strip() for m in (models or []) if str(m).strip()]
    if named:
        return {"models": named}
    return _resolve_submit_judge()


def _locate_submission_or_404(run_id: str):
    run_id = str(run_id or "").strip()
    if not run_id:
        raise HTTPException(400, "run_id is required")
    found = rescore.locate_submission(run_id, _serve_roots())
    if found is None:
        raise HTTPException(404, f"no scored submission for run_id={run_id!r}")
    return found


@app.post("/rescores", response_model=RescoreOpStatus, status_code=202)
def create_rescore(
    req: RescoreRequest,
    response: Response,
    _audience: str = Depends(resolve_audience),
):
    """Re-judge an already-scored submission, offline, as a background operation.

    Scoring a submission has two halves. The verifier half ran against the live
    target and is frozen on disk; the ``LLM_judge`` half is a model call, and a
    model call can fail for reasons that say nothing about the agent — an
    expired key, a rate limit, a model swapped out. This re-runs the judge half
    over the frozen inputs and appends the result as a new scoring pass.

    No instance needs to be alive: the findings and the verifier evidence were
    persisted at submit time precisely so this could happen later.

    The agent-facing "one submission per instance" rule is untouched — this
    changes no findings, only how they were judged. Every pass is retained, and
    the response reports ``grader_drift`` when the verifier scripts themselves
    have changed since grading, because no re-judge can account for that.
    """
    # No findings-based gate. Re-scoring runs the benchmark's whole ``score()``,
    # not just the judge, and a scorer that consumes no agent findings still has
    # something to recompute: a marker-based post-exploitation range scores
    # purely from the frozen evidence, so re-running it picks up any later fix to
    # that scoring logic. Refusing those submissions blocked exactly the case
    # offline re-scoring is most useful for. Whether a submission has anything to
    # judge is the scorer's call, not this endpoint's.
    sub_dir, record = _locate_submission_or_404(req.run_id)
    judge = _resolve_rescore_judge(req.judge_models)
    if not judge:
        raise HTTPException(
            400,
            "no judge model configured: name one in judge_models, or start the "
            "server with a judge (cage benchmark serve --judge-model)",
        )

    op, _started = rescore_ops.get_orchestrator().submit(
        record.target_launch.launch_id,
        lambda: rescore.rescore_submission(sub_dir, judge=judge),
    )
    body = rescore_ops.status_view(op)
    response.status_code = 202 if op.is_pending() else 200
    return body


@app.get("/rescores/{run_id}", response_model=RescoreOpStatus)
def get_rescore(run_id: str, _audience: str = Depends(resolve_audience)):
    """Authoritative status of a re-judge.

    With no operation in flight, this answers from the submission record itself
    — the durable truth about which pass is canonical — so a serve restart, or a
    query long after the work finished, still gets a real answer instead of
    "unknown operation". Such a result is flagged ``from_record``.
    """
    op = rescore_ops.get_orchestrator().get(str(run_id))
    if op is not None:
        return rescore_ops.status_view(op)
    sub_dir, record = _locate_submission_or_404(run_id)
    return {
        "run_id": record.target_launch.launch_id,
        "status": rescore_ops.DONE,
        "status_url": f"/rescores/{record.target_launch.launch_id}",
        "attempts": 0,
        "result": rescore.record_result_view(sub_dir, record),
    }


@app.get("/prompt/{run_id}", response_model=PromptResponse)
def prompt_challenge(
    run_id: str,
    request: Request = None,  # type: ignore[assignment]
    audience: str = Depends(resolve_audience),
):
    """The agent-facing task briefing for a launched instance.

    An external agent needs the same task framing a CAGE-managed agent gets —
    what to exploit, the live target address(es), and the ``final_answer`` output
    contract. This renders the challenge's own ``build_prompt`` against the
    running instance (so target/entry hosts are the ones the agent will reach),
    at the hint tier bound to the instance at ``/launch`` (``?prompt_level=``,
    defaulting to the server's ``--prompt-level``). Returns both the ready-to-use
    ``task_prompt`` (target filled in) and the un-filled ``task_prompt_template``.
    Audience-gated like ``/launch`` and ``/submit``.
    """
    instance = get_running_instance(run_id)
    if instance is None:
        raise HTTPException(404, f"no running instance for run_id={run_id!r}")
    chal_id = str(instance.get("chal_id") or "")
    try:
        challenge = load_all_challenges().get(chal_id)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(500, f"challenge registry unavailable: {exc}")
    if challenge is None:
        raise HTTPException(404, f"challenge {chal_id!r} not found in registry")

    # Hint tier bound to THIS instance at launch; fall back to the server default.
    level = _normalize_prompt_level(instance.get("prompt_level"), _resolve_prompt_level())
    # A briefing must name an address the reader can actually dial. The
    # challenge writes its targets as docker-internal addresses (``prestashop:80``,
    # or a post-exploitation range's live inner IPs) — correct for an agent on the
    # instance network, useless for a remote one. When this instance publishes its
    # entries on the host and the caller is external, rewrite those authorities to
    # the published ones so /prompt and /launch agree on where the target is.
    # A published instance is reached by every agent at its host-published
    # address, so rewrite the briefing's target authorities for ANY caller —
    # the operator polling /prompt from the serve host sees the same public
    # address the remote agent will dial.
    public_host = ""
    if instance_is_public(instance):
        public_host, _ = resolve_public_host(
            request.headers.get("host", "") if request is not None else ""
        )
    task_prompt, task_prompt_template = render_task_prompt(
        run_id, instance, challenge, prompt_level=level, public_host=public_host
    )
    return PromptResponse(
        run_id=run_id,
        chal_id=chal_id,
        task_profile=str(challenge.get("task_profile") or ""),
        prompt_level=level,
        task_prompt=task_prompt,
        task_prompt_template=task_prompt_template,
    )


if __name__ == "__main__":
    # Default to loopback so the server is not exposed to other hosts unless
    # the operator explicitly opts in by passing 0.0.0.0 (or another address).
    host = sys.argv[1] if len(sys.argv) > 1 else "127.0.0.1"
    port = int(sys.argv[2]) if len(sys.argv) > 2 else 8000
    uvicorn.run(app, host=host, port=port)
