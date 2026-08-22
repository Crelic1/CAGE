"""Challenge launch: docker compose up, image build, post-start verification."""
from __future__ import annotations

import contextlib
import logging
import os
import subprocess
import time
import uuid
from cage.target.adapters.source_config import build_default_registry
from cage.target.scope import normalize_target_scope, resolve_target_scope
from cage.target.server.health_probes import (
    is_instance_healthy,
    wait_for_containers_running,
    wait_for_inner_services_ready,
    wait_for_services_healthy,
)
from cage.target.server.launch_runtime import (
    ComposeRuntimePlan,
    materialize_compose_runtime,
)
from cage.target.server.network_alloc import (
    allocate_octet_slot,
    attach_egress_proxy,
    expand_subnet_pool_vars,
    host_off_networks_enabled,
    release_octet_slot,
    release_reserved_project_local_subnet,
)
from cage.target.server.network_admin import (
    capture_project_logs,
    resolve_service_inner_ips,
    self_heal_docker_network,
)
from cage.target.server.public_access import (
    SOURCE_FLAG,
    external_access_enabled,
    instance_is_public,
    max_public_instances,
    resolve_public_host,
    ttl_remaining_s,
)
from cage.target.server.schemas import EntryUrl, LaunchResponse, ServiceInfo
from cage.target.server.server_state import (
    COMPOSE_UP_TIMEOUT_S,
    DOCKER_NETWORK,
    HOST_IP,
    STARTUP_POLL_INTERVAL_S,
    STARTUP_TIMEOUT_S,
    TARGET_SERVER_NAMESPACE,
    challenge_build_locks,
    find_free_port,
    get_running_instance,
    load_all_challenges,
    pop_running_instance,
    running_instances_lock,
    set_running_instance,
    snapshot_running_instance_ids,
    update_running_instance,
)
from fastapi import HTTPException
from pathlib import Path
from typing import Any, Dict, List, Optional
from cage.target.server.cleanup import (
    _cleanup_instance_impl,
    _purge_project_by_name,
    _unlink_runtime_compose,
)
from cage.target.server.network_debug import (
    _build_entry_urls,
    build_container_addrs,
    build_network_debug,
)
from cage.target.server.launch_workflow import (
    ensure_docker_cli_config_dir,
    load_env_file_vars,
)

logger = logging.getLogger(__name__)

def _entry_service_keys_from_meta(meta: Dict[str, Any]) -> set[str]:
    """Pick the user-facing entry services declared by the challenge.

    Web challenges declare them as ``application_service_keys``;
    post-exploitation ranges declare them as ``entry_services``. Fall back the
    same way ``submit._challenge_task`` (the agent prompt) and the
    ``GET /challenges`` count already do, so the launch response's
    ``container_addr``/``entry_urls`` advertise exactly the entries the prompt
    names — not every service that merely happens to sit on the agent network.
    A range that declares neither yields the empty set (see
    ``build_container_addrs``: no entries → every internal address is listed).
    The set form is only used for membership checks.
    """
    source_fields = meta.get("source_fields", {}) or {}
    keys = (
        source_fields.get("application_service_keys")
        or source_fields.get("entry_services")
        or []
    )
    if isinstance(keys, str):
        keys = [keys]
    return {str(k) for k in keys if k}


def _compose_up_cmd(
    *,
    chal_path: Path,
    project_name: str,
    runtime_compose_rel: str,
) -> list[str]:
    # ``up`` is always ``--no-build``: the caller has already executed
    # ``docker compose build`` under the per-challenge build lock (see
    # ``_compose_build_locked``) if a build was needed. Re-triggering build
    # here would race classic builder's tag-create step
    # (``AlreadyExists: image <tag> already exists``) — the exact failure
    # the build lock was introduced to prevent.
    return [
        "docker", "compose",
        "--project-directory", str(chal_path),
        "-p", project_name,
        "-f", runtime_compose_rel,
        "up", "-d",
        "--no-build",
        "--force-recreate",
    ]


def _compose_build_locked(
    *,
    chal_id: str,
    chal_path: Path,
    project_name: str,
    runtime_compose_rel: str,
    env: dict[str, str],
) -> subprocess.CompletedProcess[str]:
    """Run ``docker compose build`` under a per-challenge lock.

    Classic builder (``DOCKER_BUILDKIT=0``, our default — see comment above
    on ``DOCKER_BUILDKIT``) does not atomically swap the resulting image
    tag. When N concurrent ``compose up --build`` runs all finish a fresh
    build of the same Dockerfile, the daemon races on the tag-create step
    and fails one or more of them with
    ``AlreadyExists: image "<tag>" already exists``. Per-agent launches in
    a passk batch trigger exactly this pattern, since each parallel trial
    builds the same image set.

    Serialising the build phase via ``challenge_build_locks`` is enough to
    fix this: the first trial in the batch does the cold build, subsequent
    trials wait for the lock, then enter it against a fully warm layer
    cache and the build returns in seconds (no-op tag write — daemon
    confirms the existing tag still points at the same content sha). The
    much more expensive ``up`` step (container create + healthchecks)
    still runs without the lock, preserving fan-out parallelism.

    The build subprocess shares ``COMPOSE_UP_TIMEOUT_S`` with the up step;
    we don't introduce a separate build timeout because the budget is
    already sized for the slow path.
    """
    build_cmd = [
        "docker", "compose",
        "--project-directory", str(chal_path),
        "-p", project_name,
        "-f", runtime_compose_rel,
        "build",
    ]
    with challenge_build_locks.get_lock(chal_id):
        logger.info("compose build (locked) for chal=%s project=%s", chal_id, project_name)
        return subprocess.run(
            build_cmd,
            cwd=chal_path,
            env=env,
            capture_output=True,
            text=True,
            timeout=COMPOSE_UP_TIMEOUT_S,
        )


def _image_exists(image_name: str, env: dict[str, str]) -> bool:
    res = subprocess.run(
        ["docker", "image", "inspect", image_name],
        env=env,
        capture_output=True,
        text=True,
    )
    return res.returncode == 0


def _missing_build_images(runtime_plan: ComposeRuntimePlan, env: dict[str, str]) -> list[str]:
    """Return image tags that have a ``build:`` directive but no existing image.

    Used by ``_launch_challenge_impl`` to fail fast when a benchmark target was
    not prepared through ``cage benchmark build`` before launch.

    The presence of the explicit ``image:`` tag (required by the
    ``materialize_compose_runtime`` lint) is a high-fidelity signal that the
    benchmark build hook completed successfully at some point.
    """
    services = (runtime_plan.config.get("services") or {})
    missing: list[str] = []
    for _svc_name, svc_cfg in services.items():
        if not isinstance(svc_cfg, dict):
            continue
        if "build" not in svc_cfg:
            continue
        image = str(svc_cfg.get("image") or "").strip()
        # ``materialize_compose_runtime`` rejects build: without image:; this
        # function runs on already-materialized plans, so the field is
        # guaranteed non-empty.
        if not _image_exists(image, env=env):
            missing.append(image)
    return missing


def _missing_build_images_detail(
    *,
    chal_id: str,
    meta: dict[str, Any],
    missing_images: list[str],
) -> str:
    images = ", ".join(missing_images) if missing_images else "unknown"
    return (
        "Required target image(s) are missing and target launch does not build images. "
        f"Missing images: {images}. "
        f"Run: {_benchmark_build_command_hint(chal_id, meta)}"
    )


def _benchmark_build_command_hint(chal_id: str, meta: dict[str, Any]) -> str:
    source_fields = meta.get("source_fields", {}) or {}
    benchmark = (
        os.getenv("CAGE_BENCHMARK_ID", "").strip()
        or str(meta.get("benchmark_id") or source_fields.get("benchmark_id") or "").strip()
        or str(
            meta.get("benchmark")
            or meta.get("benchmark_name")
            or source_fields.get("benchmark")
            or source_fields.get("benchmark_name")
            or ""
        ).strip()
    )
    sample_id = str(
        source_fields.get("challenge_id")
        or source_fields.get("sample_id")
        or meta.get("id")
        or chal_id
    ).strip() or chal_id
    if benchmark:
        return f"cage benchmark build {benchmark} --sample {sample_id}"
    return f"cage benchmark build <benchmark> --sample {sample_id}"


def _enforce_public_instance_limit(chal_id: str) -> None:
    """Refuse a public launch when every host-published slot is taken.

    Call with ``running_instances_lock`` held: the caller claims the slot in the
    same critical section, so the check cannot be won twice.

    The 409 body names the occupants — an agent that is merely queued behind
    someone else needs to know whose instance is holding the slot and how long
    is left on its lease, otherwise its only option is to poll blindly.
    """
    limit = max_public_instances()
    if limit <= 0:  # 0 = operator explicitly accepted unlimited
        return
    occupants = []
    for key in snapshot_running_instance_ids():
        info = get_running_instance(key)
        if info is None or not instance_is_public(info):
            continue
        created_at = info.get("created_at")
        occupants.append({
            "run_id": str(info.get("run_id") or key),
            "chal_id": str(info.get("chal_id") or ""),
            "uptime_s": (
                round(time.time() - created_at, 1)
                if isinstance(created_at, (int, float)) else None
            ),
            "ttl_s": info.get("ttl_s"),
            "ttl_remaining_s": ttl_remaining_s(info),
        })
    if len(occupants) < limit:
        return
    raise HTTPException(
        status_code=409,
        detail={
            "error": "public_instance_limit_reached",
            "message": (
                f"cannot launch {chal_id!r}: {len(occupants)} of {limit} "
                "host-published instance slot(s) in use. Once entries are "
                "published on the host, concurrent instances are mutually "
                "discoverable by a port scan, so this server caps them. Wait "
                "for an occupant's lease to expire, DELETE one you own, or "
                "restart serve with a higher --max-public-instances."
            ),
            "max_public_instances": limit,
            "occupants": occupants,
        },
    )


def _resolve_advertise_host(public_host: str, public_host_source: str) -> tuple[str, str]:
    """Fill in the advertise address for call sites that carry no request.

    The endpoints resolve it from the caller's ``Host`` header; the background
    monitor and other in-process callers have no request, so they fall back to
    the pinned/derived server-side value.
    """
    if public_host:
        return public_host, (public_host_source or SOURCE_FLAG)
    return resolve_public_host("")


def _reused_launch_response(
    chal_id: str,
    instance: dict,
    *,
    audience: str = "internal",
    public_host: str = "",
    public_host_source: str = "",
) -> LaunchResponse:
    debug = instance.get("debug", {}) or {}
    network_debug = debug.get("network", {}) or {}
    services = instance["services"]
    entry_keys = set(instance.get("entry_service_keys") or [])
    entry_urls: List[EntryUrl] = []
    entry_url_source = ""
    if instance_is_public(instance):
        advertise_host, entry_url_source = _resolve_advertise_host(
            public_host, public_host_source
        )
        entry_urls = _build_entry_urls(
            services=services,
            entry_service_keys=entry_keys,
            host_ip=advertise_host,
        )
    return LaunchResponse(
        status="reused",
        chal_id=chal_id,
        run_id=instance.get("run_id"),
        project_name=instance["project_name"],
        network_name=instance.get("network_name"),
        network_subnet=instance.get("network_subnet") or network_debug.get("subnet"),
        network_gateway=instance.get("network_gateway") or network_debug.get("gateway"),
        scoring=instance.get("scoring", {}),
        debug=debug,
        services=services,
        entry_urls=entry_urls,
        entry_url_source=entry_url_source if entry_urls else "",
        container_addr=build_container_addrs(services, entry_keys),
        ttl_s=instance.get("ttl_s"),
        ttl_remaining_s=ttl_remaining_s(instance),
    )


def resolve_parallel_mode(meta: Dict[str, Any], requested_parallel_mode: Optional[str]) -> str:
    """Normalise/validate a requested parallel_mode, with universal default.

    ``network`` is the only sane default now that the framework defaults to
    ``compose_project_local`` network_mode — per-trial compose stacks each
    own their own bridge, so the IPAM-injection path in
    ``launch_runtime.materialize_compose_runtime`` (gated on
    ``parallel_mode == "network"``) must fire to keep subnets out of
    docker's global default /16 pool. Benchmarks that genuinely need the
    legacy alias-on-shared-bridge wiring (``network_mode:
    shared_external``) must opt in by setting ``parallel_mode: alias`` in
    their challenge.json / runtime_args.
    """
    requested = str(requested_parallel_mode or "").strip().lower()
    if requested:
        if requested not in {"network", "alias"}:
            raise HTTPException(status_code=400, detail=f"Unsupported parallel_mode: {requested_parallel_mode}")
        return requested
    return "network"


def resolve_server_target_scope(meta: Dict[str, Any], requested_target_scope: Optional[str]) -> str:
    requested = normalize_target_scope(requested_target_scope)
    if requested:
        return requested
    return resolve_target_scope(chal_data=meta, runtime_args={})


def resolve_network_mode(meta: Dict[str, Any], requested_network_mode: Optional[str]) -> str:
    """Resolve compose ``network_mode`` with challenge-wins precedence.

    A ``network_mode`` declared in challenge.json is intrinsic to whether the
    challenge's topology works, so it wins. Only when the challenge is silent
    does the experiment-level value (``requested``, passed by the client from
    ``project.yml`` / CLI) apply. Empty result = let
    ``materialize_compose_runtime`` pick its own default
    (``compose_project_local``). This is the mirror image of
    ``resolve_server_target_scope`` (where the per-run request wins) on purpose.
    """
    declared = str((meta.get("source_fields", {}) or {}).get("network_mode", "") or "").strip()
    if declared:
        return declared
    return str(requested_network_mode or "").strip()


def resolve_exposure_mode(meta: Dict[str, Any], requested_exposure_mode: Optional[str]) -> str:
    """Resolve service ``exposure_mode`` with challenge-wins precedence.

    Same rule as :func:`resolve_network_mode`: challenge.json wins, else the
    experiment value, else the ``host_ports`` default. Independent of
    ``network_only`` — this states the *intended* exposure; ``network_only``
    is the per-launch gate that can additionally suppress host publishing.
    """
    declared = str((meta.get("source_fields", {}) or {}).get("exposure_mode", "") or "").strip()
    if declared:
        return declared
    requested = str(requested_exposure_mode or "").strip()
    if requested:
        return requested
    return "host_ports"


def _launch_challenge_impl(
    chal_id: str,
    force_recreate: bool,
    parallel_mode: Optional[str] = None,
    target_scope: Optional[str] = None,
    network_mode: Optional[str] = None,
    exposure_mode: Optional[str] = None,
    cage_run_id: Optional[str] = None,
    audience: str = "internal",
    network_only: bool = False,
    prompt_level: str = "l0",
    public_host: str = "",
    public_host_source: str = "",
    ttl_s: Optional[int] = None,
) -> LaunchResponse:
    """Launch (or reuse, or rebuild) the runtime instance for a challenge.

    - Existing healthy instance + not forced → reuse.
    - Existing instance unhealthy or force_recreate → cleanup and rebuild (port reuse).
    - First launch → allocate fresh ports.

    ``audience='external'`` pins non-entry services (scoring sidecars,
    internal databases) to 127.0.0.1 so external clients holding the
    bearer token cannot reach them. If a per_challenge instance was
    first launched with a different audience, it is force-recreated:
    swapping bind IPs without recreate would leave dangling 0.0.0.0
    publishes that defeat the isolation.

    A launch that will host-publish an entry for an external caller is a
    *public* launch: it consumes one of the server's ``--max-public-instances``
    slots (claimed atomically with the instance record below, so concurrent
    launches cannot both slip past the cap) and may carry a ``ttl_s`` lease so
    an agent that walks away cannot hold the slot forever.
    """
    challenges = load_all_challenges()
    if chal_id not in challenges:
        raise HTTPException(status_code=404, detail="Challenge not found")

    meta = challenges[chal_id]
    effective_parallel_mode = resolve_parallel_mode(meta, parallel_mode)
    effective_target_scope = resolve_server_target_scope(meta, target_scope)
    allow_parallel_runs = effective_target_scope == "per_agent"
    entry_service_keys = _entry_service_keys_from_meta(meta)

    # A PUBLIC launch = a --public-host server + this launch not opting back into
    # network-only. Publish exactly the declared entries on the host, claim one
    # of the server's public slots, and honour a lease. Publishing is a property
    # of the server, not of the caller or the token — every launch on a
    # --public-host server publishes unless it passed ?network_only=true.
    publish_scope = (
        "entry_only"
        if external_access_enabled() and not network_only
        else "declared"
    )
    public_intent = publish_scope == "entry_only"
    lease_s = int(ttl_s) if isinstance(ttl_s, (int, float)) and ttl_s > 0 else None

    existing_instance = None if allow_parallel_runs else get_running_instance(chal_id)
    should_recreate = False
    reason = ""

    if existing_instance:
        cached_audience = str(existing_instance.get("audience") or "internal").lower()
        cached_lifecycle = str(existing_instance.get("lifecycle_state") or "").lower()
        if force_recreate:
            should_recreate = True
            reason = "force_recreate=True"
        elif cached_lifecycle != "running":
            # Only a fully-launched ``running`` instance is reusable. A record in
            # ``launching``/``waiting_health`` is a launch still in flight (for
            # per_challenge, serialized by the lock, so this only happens if a
            # prior launch was hard-killed before its cleanup ran) or ``stopping``
            # a teardown in progress — recreate from scratch rather than hand back
            # a half-built instance whose services/network fields aren't populated.
            should_recreate = True
            reason = f"stale non-running record (lifecycle={cached_lifecycle or 'unset'})"
        elif not is_instance_healthy(chal_id):
            should_recreate = True
            reason = "instance unhealthy (port(s) closed)"
        elif cached_audience != audience:
            should_recreate = True
            reason = f"audience changed: {cached_audience} -> {audience}"
        else:
            logger.info(f"Reusing healthy instance for {chal_id}")
            return _reused_launch_response(
                chal_id,
                existing_instance,
                audience=audience,
                public_host=public_host,
                public_host_source=public_host_source,
            )

    if should_recreate:
        logger.info(f"Recreating {chal_id} because: {reason}. Cleaning up old instance...")
        _cleanup_instance_impl(chal_id)

    adapter = build_default_registry().get(meta["adapter_kind"])
    launch_spec = adapter.build_launch_spec(meta)
    launch_spec.runtime_patches["parallel_mode"] = effective_parallel_mode
    launch_spec.runtime_patches["target_scope"] = effective_target_scope
    # Compose launch mode + exposure: challenge.json wins, else experiment
    # (project.yml/CLI) value, else the framework default. Both flow through the
    # mutable runtime_patches dict (LaunchSpec is frozen) so materialize reads
    # the resolved values.
    effective_network_mode = resolve_network_mode(meta, network_mode)
    if effective_network_mode:
        launch_spec.runtime_patches["network_mode"] = effective_network_mode
    launch_spec.runtime_patches["exposure_mode"] = resolve_exposure_mode(meta, exposure_mode)
    chal_path = Path(launch_spec.working_directory)

    if launch_spec.mode == "static":
        return LaunchResponse(status="static", chal_id=chal_id, run_id=chal_id)

    safe_id = chal_id.replace('-', '_').lower()
    run_id = chal_id
    if allow_parallel_runs:
        run_id = f"{safe_id}_{uuid.uuid4().hex[:8]}"
        project_name = f"cage_bench_{TARGET_SERVER_NAMESPACE}_{safe_id}_{run_id.split('_')[-1]}_runtime"
        runtime_compose_filename = f"docker-compose.runtime.{TARGET_SERVER_NAMESPACE}.{run_id.split('_')[-1]}.yml"
    else:
        project_name = f"cage_bench_{TARGET_SERVER_NAMESPACE}_{safe_id}_runtime"
        runtime_compose_filename = f"docker-compose.runtime.{TARGET_SERVER_NAMESPACE}.yml"
    # Park materialized compose files under ``<chal_dir>/.cage_runtime/`` so
    # the challenge dir stays clean (matches the ``.cage_runs/`` convention).
    # We pass ``--project-directory <chal_dir>`` below to keep compose's
    # notion of "project root" (used for env_file / .env resolution) at the
    # challenge dir, regardless of where the materialized file lives.
    runtime_compose_dir = chal_path / ".cage_runtime"
    runtime_compose_dir.mkdir(parents=True, exist_ok=True)
    runtime_compose_path = runtime_compose_dir / runtime_compose_filename
    runtime_compose_rel = runtime_compose_path.relative_to(chal_path).as_posix()

    # Everything from compose materialization to readiness verification
    # acquires real resources: the materialized compose file, reserved
    # project-local subnets, an octet slot, then running containers. Each
    # is registered on the stack as it is acquired, so ANY exception (the
    # named HTTP error paths and unexpected ones alike) unwinds exactly
    # what exists so far — containers are purged by project_name before
    # subnets release because ``set_running_instance`` hasn't run yet and
    # ``cleanup_instance`` couldn't find the instance. ``pop_all()``
    # commits on success.
    with contextlib.ExitStack() as failure_cleanup:
        # Register the instance in a ``launching`` state up front, before any of
        # the slow work below. The launch is fully synchronous and standing up a
        # multi-host range (image pull + N containers + readiness probes) can
        # take minutes, far longer than a caller's client timeout. Without this
        # early record the in-flight instance is invisible to ``GET /instances``
        # until the very end, so a caller whose client timed out cannot tell a
        # slow-but-progressing launch from a failed one, and cannot safely retry
        # a side-effecting launch. The cleanup callback pops this record on ANY
        # failure so a crashed launch never leaves a phantom entry; ``pop_all()``
        # cancels it on success, and the full ``set_running_instance`` below
        # overwrites this minimal record with the ``running`` instance.
        #
        # The public-instance cap is checked and claimed inside the SAME lock
        # acquisition that writes this record: the slot is taken by intent,
        # before any port exists, so two concurrent external launches cannot
        # both read "0 public instances" and both proceed.
        with running_instances_lock:
            if public_intent:
                _enforce_public_instance_limit(chal_id)
            set_running_instance(
                run_id,
                {
                    "chal_id": chal_id,
                    "run_id": run_id,
                    "project_name": project_name,
                    "cage_run_id": cage_run_id or "",
                    "audience": audience,
                    "target_scope": effective_target_scope,
                    "prompt_level": prompt_level,
                    "public_intent": public_intent,
                    "ttl_s": lease_s,
                    "lifecycle_state": "launching",
                    "created_at": time.time(),
                },
            )
        failure_cleanup.callback(pop_running_instance, run_id)

        saved_existing_instance = existing_instance if should_recreate else None
        runtime_plan = materialize_compose_runtime(
            spec=launch_spec,
            project_name=project_name,
            docker_network=DOCKER_NETWORK,
            host_ip=HOST_IP,
            runtime_compose_path=runtime_compose_path,
            find_free_port_fn=find_free_port,
            existing_external_ports=(saved_existing_instance or {}).get("external_ports"),
            cage_run_id=cage_run_id or None,
            audience=audience,
            entry_service_keys=entry_service_keys,
            network_only=network_only,
            publish_scope=publish_scope,
            challenge_id=chal_id,
        )
        failure_cleanup.callback(_unlink_runtime_compose, runtime_compose_path)
        public_service_names = runtime_plan.public_service_names
        final_services = [ServiceInfo(**item) for item in runtime_plan.services]
        scoring = dict((meta.get("source_fields", {}) or {}).get("runtime_scoring", {}) or {})
        runtime_network_name = runtime_plan.agent_network_name or DOCKER_NETWORK

        # Collect project-local subnets BEFORE container start so error paths can release them
        # even when the instance is not yet registered.
        allocated_subnets: list[str] = []
        _runtime_networks = (runtime_plan.config.get("networks", {}) or {})
        for _net_name, _net_cfg in _runtime_networks.items():
            if not isinstance(_net_cfg, dict):
                continue
            if _net_cfg.get("external"):
                continue
            _ipam = _net_cfg.get("ipam", {}) or {}
            _ipam_cfgs = _ipam.get("config", []) or []
            for _ipam_entry in _ipam_cfgs:
                _subnet = str((_ipam_entry or {}).get("subnet", "") or "").strip()
                if _subnet:
                    allocated_subnets.append(_subnet)

        def _release_allocated_subnets_on_error():
            for _subnet in allocated_subnets:
                try:
                    release_reserved_project_local_subnet(_subnet)
                except Exception as _exc:
                    logger.warning(f"Failed to release subnet {_subnet} on error path: {_exc}")

        failure_cleanup.callback(_release_allocated_subnets_on_error)

        logger.info(f"Launching {project_name} (recreate={should_recreate})...")
        env = os.environ.copy()
        # BuildKit/bake can hang on some challenge contexts in this environment; default to classic builder.
        env["DOCKER_BUILDKIT"] = os.getenv("TARGET_SERVER_DOCKER_BUILDKIT", "0")
        env.update(launch_spec.runtime_patches.get("compose_env", {}) or {})

        # ``subnet_pool``: borrowed from upstream rangectl. challenge.json declares
        #     {first_octet, second_octet_range:[low,high], subnet_vars:[...],
        #      ordinal_start:1}
        # The hub reserves a free second-octet under a process-wide lock and
        # exports per-trial subnet prefix env vars, e.g.
        #     RANGE1_PUBLIC_NET_PREFIX=172.51.1
        # The compose then resolves ``${RANGE1_PUBLIC_NET_PREFIX}.20`` per service.
        # This lets N parallel trials of the same challenge each own a non-
        # overlapping /24 family without rewriting the compose.
        allocated_slot: int | None = None
        pool_spec = launch_spec.runtime_patches.get("subnet_pool")
        if isinstance(pool_spec, dict) and pool_spec.get("subnet_vars"):
            first_octet = int(pool_spec.get("first_octet", 172))
            rng = pool_spec.get("second_octet_range") or [50, 80]
            slot_range = (int(rng[0]), int(rng[1]))
            ordinal_start = int(pool_spec.get("ordinal_start", 1))
            subnet_vars = [str(v) for v in pool_spec.get("subnet_vars", [])]
            try:
                allocated_slot = allocate_octet_slot(
                    project_name,
                    first_octet=first_octet,
                    slot_range=slot_range,
                )
            except RuntimeError as exc:
                raise HTTPException(500, detail=f"subnet_pool exhausted: {exc}")
            expanded = expand_subnet_pool_vars(
                first_octet=first_octet,
                slot=allocated_slot,
                subnet_vars=subnet_vars,
                ordinal_start=ordinal_start,
            )
            env.update(expanded)
            logger.info(
                "subnet_pool: project=%s slot=%d vars=%s",
                project_name, allocated_slot, expanded,
            )

        env.update(load_env_file_vars(launch_spec.runtime_patches.get("env_file")))
        ensure_docker_cli_config_dir(env)

        def _release_slot_on_error() -> None:
            if allocated_slot is not None:
                release_octet_slot(project_name)

        failure_cleanup.callback(_release_slot_on_error)

        # Self-heal DOCKER_NETWORK before compose-up. The compose file declares it
        # as ``external: True``; if the docker daemon dropped it (race under heavy
        # concurrent compose, OS reboot, or external rm), every subsequent launch
        # would otherwise fail with "external network not found" until the server
        # is restarted. Cheap idempotent check, runs before every up.
        try:
            self_heal_docker_network()
        except Exception as exc:
            logger.warning("self_heal_docker_network failed (continuing): %s", exc)

        missing_images = _missing_build_images(runtime_plan, env)
        if missing_images:
            detail = _missing_build_images_detail(
                chal_id=chal_id,
                meta=meta,
                missing_images=missing_images,
            )
            logger.error("target launch rejected for chal=%s: %s", chal_id, detail)
            raise HTTPException(500, detail=detail)
        cmd = _compose_up_cmd(
            chal_path=chal_path,
            project_name=project_name,
            runtime_compose_rel=runtime_compose_rel,
        )
        failure_cleanup.callback(_purge_project_by_name, project_name)
        try:
            res = subprocess.run(cmd, cwd=chal_path, env=env, capture_output=True, text=True, timeout=COMPOSE_UP_TIMEOUT_S)
        except subprocess.TimeoutExpired:
            logger.error(f"Compose up timed out after {COMPOSE_UP_TIMEOUT_S}s for {project_name}")
            raise HTTPException(500, detail=f"Docker compose up timed out after {COMPOSE_UP_TIMEOUT_S}s")
        if res.returncode != 0:
            logger.error(f"Up failed:\n{res.stderr}")
            raise HTTPException(500, detail=f"Docker up failed: {res.stderr}")

        # The networks exist only now, and the range's services are already
        # starting — the proxy has to claim the gateway address before any of
        # them tries to reach the outside, or those attempts stall on ARP.
        if host_off_networks_enabled():
            try:
                attach_egress_proxy(project_name)
            except Exception as exc:
                logger.error("egress proxy attach failed for %s: %s", project_name, exc)
                raise HTTPException(500, detail=str(exc))

        # Containers created; the remaining time is spent probing readiness.
        # Advance the visible lifecycle so a reconciling caller can tell "still
        # pulling/creating" (``launching``) from "up, waiting to become ready"
        # (``waiting_health``).
        update_running_instance(run_id, lifecycle_state="waiting_health")

        # docker compose can return 0 even if containers exit immediately — verify before reporting success.
        try:
            containers_err = wait_for_containers_running(
                project_name=project_name,
                required_services=public_service_names if public_service_names else None,
                timeout_s=STARTUP_TIMEOUT_S,
                poll_interval_s=STARTUP_POLL_INTERVAL_S,
            )
            if containers_err:
                raise RuntimeError(containers_err)

            health_err = wait_for_services_healthy(
                project_name=project_name,
                required_services=public_service_names if public_service_names else None,
                timeout_s=STARTUP_TIMEOUT_S,
                poll_interval_s=STARTUP_POLL_INTERVAL_S,
            )
            if health_err:
                raise RuntimeError(health_err)

            service_inner_ips = resolve_service_inner_ips(project_name, runtime_network_name)
            for service in final_services:
                service.inner_ip = service_inner_ips.get(service.service_name)
                if (
                    str(meta.get("category", "") or "").lower() == "web"
                    and service.inner_port is not None
                    and str(service.protocol or "tcp").lower() == "tcp"
                ):
                    service.protocol = "http"

            inner_err = wait_for_inner_services_ready(
                services=final_services,
                network_name=runtime_network_name,
                timeout_s=STARTUP_TIMEOUT_S,
                poll_interval_s=STARTUP_POLL_INTERVAL_S,
            )
            if inner_err:
                raise RuntimeError(inner_err)
        except Exception as e:
            # Capture full container logs BEFORE the failure_cleanup ExitStack
            # purges the project on the way out (LIFO ``_purge_project_by_name``).
            # Without this the real crash cause (e.g. a JVM cgroup-v2 NPE that
            # kills the container on boot) is destroyed with the containers and
            # only the symptom ("service X unreachable") survives. ``error`` is
            # kept as a concise one-liner; the verbose per-service network dump
            # is dropped — the orchestrator persists ``containers`` (the logs)
            # as a trial artifact, so it must not be smashed into a truncated
            # error string.
            details = {
                "error": str(e),
                "project_name": project_name,
                "containers": capture_project_logs(project_name),
            }
            logger.error(f"[LaunchVerify] Instance {chal_id} failed to become ready: {e}")
            raise HTTPException(status_code=500, detail=details)

        failure_cleanup.pop_all()

    debug = build_network_debug(
        project_name=project_name,
        network_name=runtime_network_name,
        parallel_mode=effective_parallel_mode,
    )
    debug["target_scope"] = effective_target_scope
    network_debug = debug.get("network", {}) or {}
    network_subnet = network_debug.get("subnet")
    network_gateway = network_debug.get("gateway")

    all_subnets = []
    runtime_networks = (runtime_plan.config.get("networks", {}) or {})
    for _net_name, _net_cfg in runtime_networks.items():
        if not isinstance(_net_cfg, dict):
            continue
        if _net_cfg.get("external"):
            continue
        _ipam = _net_cfg.get("ipam", {}) or {}
        _ipam_cfgs = _ipam.get("config", []) or []
        for _ipam_entry in _ipam_cfgs:
            _subnet = str((_ipam_entry or {}).get("subnet", "") or "").strip()
            if _subnet:
                all_subnets.append(_subnet)

    set_running_instance(run_id, {
        "chal_id": chal_id,
        "run_id": run_id,
        "project_name": project_name,
        "network_name": runtime_network_name,
        "network_subnet": network_subnet,
        "network_gateway": network_gateway,
        "scoring": scoring,
        "debug": debug,
        "compose_path": runtime_compose_path,
        "services": final_services,
        "public_services": public_service_names,
        "external_ports": runtime_plan.external_ports,
        "lifecycle_state": "running",
        "target_scope": effective_target_scope,
        "all_subnets": all_subnets,
        "cage_run_id": cage_run_id or "",
        "octet_slot": allocated_slot,
        "audience": audience,
        # Hint tier bound to THIS instance at launch (GET /prompt reads it). Set
        # per-launch (?prompt_level=), so different instances on one server can
        # run at different tiers without restarting serve.
        "prompt_level": prompt_level,
        "entry_service_keys": sorted(entry_service_keys),
        # Holds one of the server's host-published slots (see
        # ``_enforce_public_instance_limit``); re-stated here because this
        # record replaces the ``launching`` one wholesale.
        "public_intent": public_intent,
        # Lease requested at launch (``?ttl=``). ``None`` = runs until deleted.
        "ttl_s": lease_s,
        # Wall-clock launch time, EPOCH SECONDS — the numeric form, because the
        # readers below do arithmetic on it. Both of them convert to RFC 3339
        # (``schemas.epoch_to_rfc3339``) before the value escapes this process:
        # ``GET /instances`` publishes it as ``created_at`` (and derives
        # ``uptime_s`` from the raw number), and ``serve_log`` records it as a
        # submission's ``launch_time``. It is also the start of the TTL lease —
        # stamped here, when the instance is actually up, so a slow launch does
        # not eat the agent's lease. Nothing in the trial path depends on it.
        "created_at": time.time(),
    })

    entry_urls: List[EntryUrl] = []
    entry_url_source = ""
    if public_intent or runtime_plan.external_ports:
        advertise_host, entry_url_source = _resolve_advertise_host(
            public_host, public_host_source
        )
        entry_urls = _build_entry_urls(
            services=final_services,
            entry_service_keys=entry_service_keys,
            host_ip=advertise_host,
        )

    status = "launched" if not should_recreate else "recreated"
    return LaunchResponse(
        status=status,
        chal_id=chal_id,
        run_id=run_id,
        project_name=project_name,
        network_name=runtime_network_name,
        network_subnet=network_subnet,
        network_gateway=network_gateway,
        scoring=scoring,
        debug=debug,
        services=final_services,
        entry_urls=entry_urls,
        entry_url_source=entry_url_source if entry_urls else "",
        container_addr=build_container_addrs(final_services, entry_service_keys),
        ttl_s=lease_s,
        ttl_remaining_s=float(lease_s) if lease_s else None,
    )
