"""build_target — a role-aware artifact benchmark for CAGE.

Each task declares deployment files, source, player-visible attachments, and
Writeups separately. The benchmark selects a build profile from that material
shape and combines it with a category profile (currently Web, Pwn, or generic),
so an existing official Compose stack is repaired instead of being thrown away
and an attachment-only task is not mistaken for a source rebuild.

The scorer snapshots the produced files and independently runs
``docker compose up --build`` in an isolated project. R3 covers build/liveness;
R4 additionally executes source-backed HTTP/TCP semantic probes. With the
optional exploit gate enabled, R5 injects a fresh random flag and runs the
committed ``solve/`` from a player-side container. Live checks expose objective
checkpoint evidence, and final scoring repeats the R5 replay with a new flag.

The structured verdict (failure_class / retryable / feedback) rides in
Score.metadata until the framework grows first-class artifact-task fields.
"""

from __future__ import annotations

import copy
import hashlib
import ipaddress
import json
import logging
import os
import re
import secrets
import shlex
import shutil
import socket
import subprocess
import sys
import threading
import time
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import TYPE_CHECKING, Any, Callable, Iterator

import yaml

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from cage.artifacts.live_success import record_live_success
from cage.benchmarks import Benchmark, render_prompt
from cage.scoring import Score, Scorer, ScoringContext
from examples.build_target.pipeline_routes import resolve_route
from examples.build_target.runtime_probes import (
    ProbeContractError,
    execute_runtime_probes,
    normalize_runtime_probes,
)

if TYPE_CHECKING:
    from cage.sandbox.containers import Container

logger = logging.getLogger(__name__)

PROMPTS_DIR = Path(__file__).resolve().parent / "prompts"
DATASETS_DIR = Path(__file__).resolve().parent / "datasets"
RUNTIME_CATALOG_PATH = Path(__file__).resolve().parent / "pwn_runtime_catalog.json"
GUIDES_SOURCE_DIR = Path(__file__).resolve().parent / "guides"
WORKSPACE_DIR = "/home/agent/workspace"
PWN_RUNTIME_DIR = "/opt/cage/pwn-runtimes"
GUIDES_AGENT_DIR = "/opt/cage/build-target-guides"
CHECK_CLIENT_PATH = Path(__file__).resolve().parent / "serve" / "cage-check"
CLAUDE_BASH_GUARD_PATH = (
    Path(__file__).resolve().parent / "serve" / "claude_bash_guard.py"
)
CLAUDE_CONFIG_DIR = "/home/agent/.claude"
CLAUDE_BASH_GUARD_AGENT_PATH = (
    f"{CLAUDE_CONFIG_DIR}/cage-build-target-bash-guard.py"
)
CLAUDE_SETTINGS_PATH = f"{CLAUDE_CONFIG_DIR}/settings.json"
LIVE_WORKSPACE_ENV = "CAGE_BUILD_TARGET_LIVE_WORKSPACE"
VALIDATOR_PUBLIC_HOST = "host.docker.internal"

# Graceful pre-cap flush for the joint environment+exploit pipeline.  Like the
# CyberGym gendesc hook, this is an offset from the resolved hard cap rather
# than an absolute round.  The proxy repeats the reminder on each still-
# forwarded request at the start of the final window, giving the agent twenty real turns to
# preserve its best artifacts and write the required metadata before the next
# request would be rejected.  Twenty turns is intentionally large enough for
# complex VM/browser builds to finish one already-supported change and still
# serialize the root contracts; the 30-task calibration showed that five turns
# only induced transcript/schema searches at the cap.
DEFAULT_FULL_PIPELINE_WRAPUP_BEFORE = 20
DEFAULT_FULL_PIPELINE_STARTUP_REMINDER_AT = 4
DEFAULT_FULL_PIPELINE_STARTUP_REMINDER_UNTIL = 16


def _full_pipeline_task_appendix(sample: dict[str, Any]) -> str:
    """Render exact routed report literals and required output image tags."""

    route = resolve_route(sample)
    literals: list[tuple[str, Any]] = [
        ("data_tier", sample.get("data_tier")),
        ("data_tier_source", sample.get("data_tier_source")),
        ("build_profile", sample.get("build_profile")),
        ("category_profile", sample.get("category_profile")),
        ("material_profile", route.profile),
        ("pipeline_route", route.route),
        ("build_source", route.build_source),
        ("exploit_source", route.exploit_source),
    ]
    material_priority = sample.get("pwn_material_priority") or {}
    if material_priority.get("id"):
        literals.append(("pwn_runtime.material_priority", material_priority["id"]))

    rendered_literals = "\n".join(
        f"- `{key}`: `{value}`" for key, value in literals if value is not None
    )
    image_names = [
        str(value)
        for value in (sample.get("image_names") or [])
        if str(value).strip()
    ]
    rendered_images = "\n".join(f"- `{value}`" for value in image_names)
    output_contract = ""
    if rendered_images:
        output_contract = (
            "\n\n# EXACT REQUIRED OUTPUT IMAGES\n\n"
            "Use each tag below as a Compose service-level `image:` next to "
            "that service's `build:`; never use it as a Dockerfile `FROM`:\n\n"
            f"{rendered_images}"
        )
    return (
        "# EXACT TASK-SPECIFIC REPORT LITERALS\n\n"
        "Copy these values verbatim into the corresponding report fields; do "
        "not search the earlier transcript for them:\n\n"
        f"{rendered_literals}"
        f"{output_contract}"
    )


def _full_pipeline_wrapup_message(sample: dict[str, Any] | None = None) -> str:
    """Return the full-pipeline pre-cap reminder plus exact routed literals."""

    cached = getattr(_full_pipeline_wrapup_message, "_cache", None)
    if cached is None:
        cached = (PROMPTS_DIR / "wrapup_full.txt").read_text(encoding="utf-8").strip()
        _full_pipeline_wrapup_message._cache = cached
    if sample is None:
        return cached
    return f"{cached}\n\n{_full_pipeline_task_appendix(sample)}"


def _full_pipeline_startup_message(sample: dict[str, Any] | None = None) -> str:
    """Return the repeated early delivery gate plus exact task literals."""

    cached = getattr(_full_pipeline_startup_message, "_cache", None)
    if cached is None:
        cached = (PROMPTS_DIR / "startup_full.txt").read_text(encoding="utf-8").strip()
        _full_pipeline_startup_message._cache = cached
    if sample is None:
        return cached
    return f"{cached}\n\n{_full_pipeline_task_appendix(sample)}"

# Seconds to let the stack settle before checking it is still running — long
# enough for a service that crashes on startup to have crashed.
_SETTLE_SECONDS = 4

# Compose network creation happens after subnet selection, so merely scanning
# the daemon is racy: several validator threads can observe the same free /24
# and all write it into their managed Compose files.  Keep the short allocation
# window reserved in-process; the reservation is released as soon as
# ``docker compose up`` returns, when Docker either owns the subnet or the
# attempt has failed.  A project-derived starting offset also spreads separate
# CAGE processes that cannot share this lock.
_MANAGED_SUBNET_LOCK = threading.Lock()
_MANAGED_SUBNET_RESERVATIONS: set[ipaddress.IPv4Network] = set()
_MAX_MANAGED_NETWORK_RETRIES = 3

# These failures describe the host validator rather than the candidate.  Live
# checks retry them without spending one of the agent's bounded repair
# attempts.  Keep this in sync with the tiny in-container ``cage-check``
# client, which hides the same transients from the model.
_HOST_TRANSIENT_FAILURES = frozenset(
    {
        "host_runtime_network_exhausted",
        "host_runtime_docker_timeout",
        "validator_internal_error",
    }
)

_COMPOSE_NAMES = ("docker-compose.yml", "docker-compose.yaml", "compose.yml", "compose.yaml")
_MATERIAL_ROLES = ("deployment", "source", "exploit", "attachments", "writeups")
# CAGE-owned runtime for the R5 exploit-capture sidecar.  The human-readable
# tag is validated and resolved to an immutable image ID once, before any
# agent-authored Compose build can mutate daemon tags.  Keep the legacy alias
# so old challenge.json files transparently use the pinned CAGE image instead
# of whatever mutable image happens to own that historical tag.
DEFAULT_SOLVER_IMAGE = "cage/build-target-solver:2026-08-v1"
LEGACY_DEFAULT_SOLVER_IMAGES = frozenset({"buildtarget/solver:latest"})
DEFAULT_SOLVER_IMAGE_ALIASES = frozenset(
    {DEFAULT_SOLVER_IMAGE, *LEGACY_DEFAULT_SOLVER_IMAGES}
)
DEFAULT_SOLVER_CONTRACT_LABEL = "io.cage.build-target.solver-contract"
DEFAULT_SOLVER_CONTRACT_VALUE = "pwn-python-v1"
DEFAULT_EXPLOIT_ATTEMPTS = 5
# A candidate target can execute attacker-controlled input during both live
# checks and final R5 replay.  Without a container PID ceiling, a malformed
# emulator payload or fork bomb can exhaust the host-wide task table before
# the validator timeout gets a chance to tear the stack down.  Four thousand
# tasks is far above the normal footprint of the VM/browser targets in this
# benchmark while keeping eight concurrent validator slots bounded.
DEFAULT_VALIDATOR_PIDS_LIMIT = 4096
# A solver that continuously floods output can otherwise make
# ``Popen.communicate`` retain gigabytes before its wall-clock timeout. Keep
# enough head/tail evidence for diagnosis, but fail and remove the sidecar once
# the combined stream exceeds this hard player-process contract.
_SOLVER_OUTPUT_LIMIT_BYTES = 8 * 1024 * 1024
_SOLVER_OUTPUT_HEAD_BYTES = 32 * 1024
_SOLVER_OUTPUT_TAIL_BYTES = 64 * 1024
_SOLVER_CAPTURE_EXIT_GRACE_SECONDS = 1.0
_FLAG_INJECT_METHODS = frozenset({"file", "env"})
_DATA_TIERS = {f"D{level}" for level in range(6)}
_LIVE_RUNTIME_SIGNATURE_IGNORES = frozenset(
    {
        "service_output.txt",
        "build_report.json",
        "solve_report.json",
        "education.json",
    }
)
_BUILD_PROFILES = {
    "official_deployment",
    "source_rebuild",
    "artifact_rehost",
    "triage",
}
_BUILD_PROFILE_ALIASES = {
    "official": "official_deployment",
    "existing_deployment": "official_deployment",
    "reuse_deployment": "official_deployment",
    "source": "source_rebuild",
    "source-based": "source_rebuild",
    "source_based": "source_rebuild",
    "inferred": "artifact_rehost",
    "attachment_rehost": "artifact_rehost",
    "insufficient": "triage",
}
_SOURCE_SUFFIXES = {
    ".c",
    ".cc",
    ".cpp",
    ".cxx",
    ".go",
    ".h",
    ".hpp",
    ".java",
    ".js",
    ".php",
    ".pl",
    ".py",
    ".rb",
    ".rs",
    ".sh",
    ".ts",
}

_PWN_MATERIAL_PRIORITIES = {
    "dockerfile_writeup_attachments": {
        "rank": 0,
        "label": "Dockerfile + Writeup + attachments",
        "authenticity": "strongest build candidate; cross-check deployment and Writeup",
    },
    "dockerfile_attachments": {
        "rank": 1,
        "label": "Dockerfile + attachments",
        "authenticity": "strong deployment evidence; exploit path remains unverified",
    },
    "writeup_attachments": {
        "rank": 2,
        "label": "Writeup + attachments",
        "authenticity": "runtime must be inferred from Writeup evidence",
    },
    "source_attachments": {
        "rank": 3,
        "label": "source + attachments, without Dockerfile or Writeup",
        "authenticity": "service logic is available but historical runtime remains uncertain",
    },
    "attachments_only": {
        "rank": 4,
        "label": "attachments only",
        "authenticity": "historical runtime is unverified until EXP validation",
    },
    "incomplete": {
        "rank": 5,
        "label": "incomplete Pwn material combination",
        "authenticity": "insufficient evidence for the preferred Pwn build queue",
    },
}


def _target_rehost_level(sample: dict[str, Any]) -> int:
    target = sample.get("target_maturity") or {}
    if not isinstance(target, dict):
        return 3
    raw = str(target.get("rehost") or "R3").strip().upper()
    match = re.fullmatch(r"R([0-5])", raw)
    return int(match.group(1)) if match else 3


def _runtime_probe_required(sample: dict[str, Any]) -> bool:
    return _target_rehost_level(sample) >= 4


class _LiveRuntime:
    def __init__(
        self,
        *,
        project: str,
        workspace: Path,
        compose_path: Path,
        compose_files: list[Path] | None = None,
        agent_container: str,
        network_name: str | None,
        service_targets: list[dict[str, Any]] | None = None,
        image_manifest: str | None = None,
        runtime_id: str | None = None,
        generation: int = 0,
    ) -> None:
        self.project = project
        self.workspace = workspace
        self.compose_path = compose_path
        self.compose_files = list(compose_files or [compose_path])
        self.agent_container = agent_container
        self.network_name = network_name
        self.service_targets = list(service_targets or [])
        self.image_manifest = image_manifest
        self.runtime_id = runtime_id or uuid.uuid4().hex
        self.generation = int(generation)


class _LiveTrialContext:
    def __init__(
        self,
        *,
        trial_id: str,
        trial_dir: Path,
        workspace: Path,
        sample: dict[str, Any],
        agent_container: str,
        token: str,
    ) -> None:
        self.trial_id = trial_id
        self.trial_dir = trial_dir
        self.workspace = workspace
        self.sample = sample
        self.agent_container = agent_container
        self.token = token
        self.lock = threading.Lock()
        self.check_count = 0
        self.last_runtime: _LiveRuntime | None = None
        self.last_runtime_signature: str | None = None
        self.last_submission_id: str | None = None
        self.last_submission_digest: str | None = None
        self.last_pass_payload: dict[str, Any] | None = None
        self.terminal_payload: dict[str, Any] | None = None
        self.runtime_generation = 0
        self.last_invalidated_runtime_id: str | None = None


class _WorkspaceChangedDuringSnapshot(RuntimeError):
    """The agent changed score-relevant files while a check was freezing them."""


def _safe_relative_path(raw_path: str) -> Path:
    """Return a normalized dataset-relative path or reject path traversal."""

    normalized = str(raw_path).strip()
    path = Path(normalized)
    if not normalized or path.is_absolute() or ".." in path.parts:
        raise ValueError(f"material path must stay inside material_root: {raw_path!r}")
    return path


def _path_list(value: Any, *, field: str) -> list[str]:
    if value is None:
        return []
    if not isinstance(value, list):
        raise ValueError(f"{field} must be a list of relative paths")
    paths: list[str] = []
    for raw_path in value:
        if not isinstance(raw_path, str):
            raise ValueError(f"{field} entries must be strings")
        paths.append(_safe_relative_path(raw_path).as_posix())
    return paths


def _dedupe_paths(paths: list[str]) -> list[str]:
    return list(dict.fromkeys(paths))


def _looks_like_deployment(path: str) -> bool:
    name = Path(path).name.lower()
    return name in _COMPOSE_NAMES or name.startswith("dockerfile") or name == ".dockerignore"


def _looks_like_writeup(path: str) -> bool:
    lowered = path.lower()
    return any(part in lowered for part in ("writeup", "solution", "/solve", "solver/"))


def _normalize_materials(meta: dict[str, Any]) -> dict[str, list[str]]:
    """Normalize the role-aware material contract while keeping legacy tasks valid."""

    raw_materials = meta.get("materials") or {}
    if not isinstance(raw_materials, dict):
        raise ValueError("materials must be an object keyed by material role")

    materials = {
        role: _path_list(raw_materials.get(role), field=f"materials.{role}")
        for role in _MATERIAL_ROLES
    }
    explicitly_assigned = {path for paths in materials.values() for path in paths}

    # ``attachments`` was the original build_target contract. Keep it as a
    # compatibility input, but classify unassigned entries so old datasets also
    # benefit from profile routing.
    legacy_paths = _path_list(meta.get("attachments"), field="attachments")
    for path in legacy_paths:
        if path in explicitly_assigned:
            continue
        if _looks_like_deployment(path):
            materials["deployment"].append(path)
        elif _looks_like_writeup(path):
            materials["writeups"].append(path)
        elif Path(path).suffix.lower() in _SOURCE_SUFFIXES:
            materials["source"].append(path)
        else:
            materials["attachments"].append(path)

    return {role: _dedupe_paths(paths) for role, paths in materials.items()}


def _infer_data_tier(materials: dict[str, list[str]]) -> str:
    """Infer the legacy task tier from the strongest material role present."""

    if materials["deployment"] and materials["attachments"] and materials["writeups"]:
        return "D5"
    if materials["deployment"]:
        return "D4"
    if materials["source"]:
        return "D3"
    if materials["attachments"]:
        return "D2"
    if materials["writeups"]:
        return "D1"
    return "D0"


def _normalize_data_tier(
    meta: dict[str, Any], materials: dict[str, list[str]]
) -> tuple[str, str, str]:
    """Return selected tier, its provenance, and the role-derived comparison tier."""

    inferred = _infer_data_tier(materials)
    raw = str(meta.get("data_tier") or "").strip().upper()
    if not raw:
        return inferred, "inferred_from_material_roles", inferred
    if raw not in _DATA_TIERS:
        raise ValueError("data_tier must be one of D0, D1, D2, D3, D4, or D5")
    return raw, "declared", inferred


def _pwn_material_priority(
    category_profile: str,
    materials: dict[str, list[str]],
    material_root: Path,
) -> dict[str, Any]:
    if category_profile != "pwn":
        return {
            "id": "not_applicable",
            "rank": 100,
            "label": "not a Pwn task",
            "authenticity": "use the category-specific material policy",
            "has_dockerfile": False,
        }

    has_dockerfile = False
    for raw_path in materials["deployment"]:
        relative_path = _safe_relative_path(raw_path)
        candidate = material_root / relative_path
        if relative_path.name.lower().startswith("dockerfile"):
            has_dockerfile = True
            break
        if candidate.is_dir() and any(
            path.is_file() and path.name.lower().startswith("dockerfile")
            for path in candidate.rglob("*")
        ):
            has_dockerfile = True
            break
    has_writeup = bool(materials["writeups"])
    has_attachments = bool(materials["attachments"])
    if has_dockerfile and has_writeup and has_attachments:
        priority_id = "dockerfile_writeup_attachments"
    elif has_dockerfile and has_attachments:
        priority_id = "dockerfile_attachments"
    elif has_writeup and has_attachments:
        priority_id = "writeup_attachments"
    elif materials["deployment"]:
        priority_id = "incomplete"
    elif materials["source"] and has_attachments:
        priority_id = "source_attachments"
    elif has_attachments:
        priority_id = "attachments_only"
    else:
        priority_id = "incomplete"
    return {
        "id": priority_id,
        **_PWN_MATERIAL_PRIORITIES[priority_id],
        "has_dockerfile": has_dockerfile,
    }


def _load_runtime_catalog() -> list[dict[str, Any]]:
    raw = json.loads(RUNTIME_CATALOG_PATH.read_text(encoding="utf-8"))
    bundles = raw.get("bundles") if isinstance(raw, dict) else None
    if not isinstance(bundles, list):
        raise ValueError(f"{RUNTIME_CATALOG_PATH} must contain a bundles list")
    return [dict(bundle) for bundle in bundles if isinstance(bundle, dict)]


def _resolve_runtime_cache(raw_path: str | Path | None) -> Path | None:
    configured = raw_path or os.environ.get("CAGE_BUILD_TARGET_PWN_RUNTIME_CACHE")
    if not configured:
        return None
    path = Path(configured).expanduser()
    if not path.is_absolute():
        path = Path(__file__).resolve().parent / path
    return path.resolve()


def _load_pwn_runtime_cache(cache_root: Path | None) -> dict[str, Any]:
    """Expose local runtime choices without pretending they prove historical truth."""

    catalog = _load_runtime_catalog()
    public = {
        "agent_path": PWN_RUNTIME_DIR,
        "selection_method": "infer_from_deployment_or_writeup",
        "bundles": catalog,
    }
    if cache_root is None:
        return {**public, "status": "not_configured"}

    manifest_path = cache_root / "manifest.json"
    if not manifest_path.is_file():
        return {**public, "status": "missing"}
    raw = json.loads(manifest_path.read_text(encoding="utf-8"))
    bundles = raw.get("bundles") if isinstance(raw, dict) else None
    if not isinstance(bundles, list):
        raise ValueError(f"invalid Pwn runtime manifest: {manifest_path}")

    required_ids = {str(bundle.get("id")) for bundle in catalog}
    present_ids: set[str] = set()
    normalized: list[dict[str, Any]] = []
    for raw_bundle in bundles:
        if not isinstance(raw_bundle, dict):
            raise ValueError(f"invalid Pwn runtime bundle in {manifest_path}")
        bundle = dict(raw_bundle)
        bundle_id = str(bundle.get("id") or "").strip()
        libc = bundle.get("libc")
        loader = bundle.get("loader")
        if not bundle_id or not isinstance(libc, dict) or not isinstance(loader, dict):
            raise ValueError(f"incomplete Pwn runtime bundle in {manifest_path}")
        for label, artifact in (("libc", libc), ("loader", loader)):
            relative_path = _safe_relative_path(str(artifact.get("path") or ""))
            if not (cache_root / relative_path).is_file():
                raise FileNotFoundError(
                    f"Pwn runtime {bundle_id} {label} is missing: {cache_root / relative_path}"
                )
        present_ids.add(bundle_id)
        normalized.append(bundle)
    missing_ids = sorted(required_ids - present_ids)
    if missing_ids:
        raise ValueError(
            "Pwn runtime cache is incomplete; missing bundles: " + ", ".join(missing_ids)
        )
    return {**public, "status": "ready", "bundles": normalized}


def _resolve_build_profile(meta: dict[str, Any], materials: dict[str, list[str]]) -> str:
    explicit = str(meta.get("build_profile") or meta.get("build_strategy") or "").strip().lower()
    if explicit:
        profile = _BUILD_PROFILE_ALIASES.get(explicit, explicit)
        if profile not in _BUILD_PROFILES:
            allowed = ", ".join(sorted(_BUILD_PROFILES))
            raise ValueError(f"unknown build_profile {explicit!r}; expected one of: {allowed}")
        return profile
    if materials["deployment"]:
        return "official_deployment"
    if materials["source"]:
        return "source_rebuild"
    if materials["attachments"]:
        return "artifact_rehost"
    return "triage"


def _resolve_category_profile(category: Any) -> str:
    normalized = re.sub(r"[^a-z0-9]+", "_", str(category or "").strip().lower()).strip("_")
    if normalized in {"pwn", "binary", "binary_exploitation", "exploitation"}:
        return "pwn"
    if normalized in {"web", "web_exploitation", "web_security"}:
        return "web"
    return "generic"


def _normalize_service_contract(meta: dict[str, Any], category_profile: str) -> dict[str, Any]:
    raw = meta.get("service_contract") or meta.get("service") or {}
    if not isinstance(raw, dict):
        raise ValueError("service_contract must be an object")
    contract = dict(raw)
    internal_port = contract.get("internal_port", meta.get("internal_port"))
    if internal_port not in (None, "", 0, "0"):
        contract["internal_port"] = int(internal_port)
    else:
        contract.pop("internal_port", None)
    contract.setdefault("protocol", "http" if category_profile == "web" else "tcp")
    return contract


def _public_flag_contract(meta: dict[str, Any]) -> dict[str, Any]:
    raw = meta.get("flag_contract") or {}
    if not isinstance(raw, dict):
        raise ValueError("flag_contract must be an object")
    # A prompt may describe where/how a flag is injected, but never receives a
    # secret value from metadata. Historical flag files remain ordinary input
    # material and must not be treated as validation truth.
    contract = {
        key: value
        for key, value in raw.items()
        if key.lower() not in {"flag", "secret", "value", "expected"}
    }
    contract.setdefault("format", meta.get("flag_format", "flag{...}"))
    return contract


def _mint_random_flag(format_hint: str = "FAKE{...}") -> str:
    """Mint a fresh random flag for one R5 replay.

    The value never leaves the validator until the exploit captures it, so a
    hardcoded or writeup-copied flag cannot pass: each ``cage score`` mints a new
    one.  Preserve the declared challenge prefix when it has the ordinary
    ``PREFIX{...}`` shape; the body is always replaced with private random data.
    Invalid or unusually-shaped hints fall back to the obvious harness prefix.
    """
    match = re.match(
        r"^([A-Za-z0-9][A-Za-z0-9_.:+-]{0,63})\{",
        str(format_hint).strip(),
    )
    prefix = match.group(1) if match else "FAKE"
    return prefix + "{" + secrets.token_hex(12) + "}"


def _normalize_flag_contract(
    raw: Any, *, default_service: str | None
) -> dict[str, Any]:
    """Resolve the agent's flag-injection declaration, filling safe defaults.

    Shape: ``{inject: "file"|"env", service, path (file), env (env), format}``.
    Absent or partial declarations default to a read-only ``/flag.txt``
    bind-mount on the first target service — the mechanism proven for socat pwn
    targets.  ``format`` is retained so the minted validator token agrees with
    the public contract rather than surprising a correct prefix-aware solver.
    """
    data = raw if isinstance(raw, dict) else {}
    inject = str(data.get("inject") or "file").strip().lower()
    if inject not in _FLAG_INJECT_METHODS:
        inject = "file"
    service = str(data.get("service") or "").strip() or (default_service or "")
    format_hint = str(data.get("format") or "FAKE{...}").strip() or "FAKE{...}"
    contract: dict[str, Any] = {
        "inject": inject,
        "service": service,
        "format": format_hint,
    }
    if inject == "file":
        path = str(data.get("path") or "/flag.txt").strip() or "/flag.txt"
        contract["path"] = path if path.startswith("/") else "/" + path
    else:
        contract["env"] = str(data.get("env") or "FLAG").strip() or "FLAG"
    return contract


def _normalize_solve_block(
    raw: Any, *, default_service: str | None, default_image: str
) -> dict[str, Any]:
    """Resolve the agent's ``solve`` declaration (how to run the exploit).

    Shape: ``{entry, service, image}``. ``entry`` is required for the R5 gate to
    run; without it the build simply stays at R3/R4. ``image`` defaults to the
    shared solver runtime; ``service`` to the first target service.
    """
    data = raw if isinstance(raw, dict) else {}
    entry = str(data.get("entry") or "").strip()
    service = str(data.get("service") or "").strip() or (default_service or "")
    image = str(data.get("image") or "").strip() or default_image
    return {"entry": entry, "service": service, "image": image}


def _exploit_validation_required(sample: dict[str, Any]) -> bool:
    """Whether this sample's route wants the R5 exploit-capture gate.

    Symmetric to ``_runtime_probe_required``; the route (A/W/P/B profile) is the
    authority. Whether the gate actually *executes* is additionally gated by the
    ``exploit_gate`` scorer flag — this only expresses route intent.
    """
    try:
        return bool(resolve_route(sample).exploit_required)
    except Exception:  # noqa: BLE001 - unroutable samples never gate
        return False


def _normalize_build_environment(meta: dict[str, Any]) -> dict[str, Any]:
    raw = meta.get("build_environment") or {}
    if not isinstance(raw, dict):
        raise ValueError("build_environment must be an object")
    environment = dict(raw)
    if "network" in environment:
        environment["network"] = str(environment["network"]).strip().lower()
    cached_images = environment.get("cached_images")
    if cached_images is not None:
        if not isinstance(cached_images, list) or not all(
            isinstance(image, str) for image in cached_images
        ):
            raise ValueError("build_environment.cached_images must be a list of image names")
        environment["cached_images"] = list(dict.fromkeys(cached_images))
    return environment


def _optional_metadata_object(meta: dict[str, Any], field: str) -> dict[str, Any]:
    raw = meta.get(field) or {}
    if not isinstance(raw, dict):
        raise ValueError(f"{field} must be an object")
    return dict(raw)


def _normalize_image_names(meta: dict[str, Any], build_profile: str) -> list[str]:
    raw_names = meta.get("image_names")
    if raw_names is None:
        raw_names = []
    if not isinstance(raw_names, list) or not all(isinstance(name, str) for name in raw_names):
        raise ValueError("image_names must be a list of tagged image names")
    names = [str(name).strip() for name in raw_names if str(name).strip()]
    singular = str(meta.get("image_name") or "").strip()
    if singular:
        names.insert(0, singular)
    names = list(dict.fromkeys(names))

    if build_profile != "triage" and not names:
        raise ValueError("a non-triage build_target task must declare image_name or image_names")
    for name in names:
        tail = name.rsplit("/", 1)[-1]
        if ":" not in tail or tail.endswith(":latest"):
            raise ValueError(
                f"image name must use an explicit non-latest tag for archival: {name!r}"
            )
    return names


def _run(
    cmd: list[str], *, cwd: Path | None = None, timeout: int | float | None = 120
) -> subprocess.CompletedProcess:
    return subprocess.run(
        cmd,
        cwd=str(cwd) if cwd else None,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout,
    )


def _pin_default_solver_image(image: str) -> str:
    """Validate the CAGE solver contract and return its immutable image ID.

    This runs before trial work.  Checking both an ownership label and the
    actual imports prevents a globally mutable Docker tag from silently
    changing the scorer's execution environment.  Returning the content ID
    also keeps an already-started batch stable if a later build retags the
    human-readable alias.
    """

    try:
        inspected = _run(["docker", "image", "inspect", image], timeout=30)
    except (OSError, subprocess.SubprocessError) as exc:
        raise RuntimeError(
            f"failed to inspect the build-target solver image {image!r}: {exc}"
        ) from exc
    if inspected.returncode != 0:
        detail = (inspected.stderr or inspected.stdout or "image is absent").strip()[-600:]
        raise RuntimeError(
            f"build-target solver image {image!r} is unavailable: {detail}. "
            "Build it with `docker build -f "
            "examples/build_target/serve/solver.Dockerfile "
            f"-t {DEFAULT_SOLVER_IMAGE} .`."
        )
    try:
        payload = json.loads(inspected.stdout or "[]")
        metadata = payload[0]
        image_id = str(metadata["Id"])
        labels = (metadata.get("Config") or {}).get("Labels") or {}
    except (IndexError, KeyError, TypeError, json.JSONDecodeError) as exc:
        raise RuntimeError(
            f"docker returned malformed metadata for solver image {image!r}"
        ) from exc
    actual_contract = str(labels.get(DEFAULT_SOLVER_CONTRACT_LABEL) or "")
    if actual_contract != DEFAULT_SOLVER_CONTRACT_VALUE:
        raise RuntimeError(
            f"build-target solver image {image!r} has contract label "
            f"{actual_contract!r}, expected {DEFAULT_SOLVER_CONTRACT_VALUE!r}; "
            "the tag may have been overwritten by a challenge build"
        )
    if not re.fullmatch(r"sha256:[0-9a-f]{64}", image_id):
        raise RuntimeError(
            f"build-target solver image {image!r} did not resolve to a content ID"
        )

    smoke_code = (
        "import Crypto, pwn, pwnlib, requests; "
        "print('solver-contract-ok', Crypto.__version__, pwnlib.__version__, "
        "requests.__version__)"
    )
    try:
        smoke = _run(
            [
                "docker",
                "run",
                "--rm",
                "--network",
                "none",
                image_id,
                "python3",
                "-c",
                smoke_code,
            ],
            timeout=60,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        raise RuntimeError(
            f"failed to smoke-test build-target solver image {image!r}: {exc}"
        ) from exc
    if smoke.returncode != 0 or "solver-contract-ok" not in (smoke.stdout or ""):
        detail = (smoke.stderr or smoke.stdout or "dependency smoke test failed").strip()[-800:]
        raise RuntimeError(
            f"build-target solver image {image!r} violates its dependency contract: {detail}"
        )
    return image_id


class _BoundedSolverOutput:
    """Thread-safe bounded capture with an optional exact success marker."""

    def __init__(self, limit: int, success_marker: bytes | None = None) -> None:
        self.limit = limit
        self.success_marker = bytes(success_marker or b"")
        self.total = 0
        self.exceeded = threading.Event()
        self.marker_seen = threading.Event()
        self.marker_seen_at: float | None = None
        self.lock = threading.Lock()
        self.streams = {
            "stdout": {
                "count": 0,
                "head": bytearray(),
                "tail": bytearray(),
                "marker_overlap": b"",
            },
            "stderr": {
                "count": 0,
                "head": bytearray(),
                "tail": bytearray(),
                "marker_overlap": b"",
            },
        }

    def append(self, stream_name: str, chunk: bytes) -> None:
        with self.lock:
            stream = self.streams[stream_name]
            if self.success_marker and not self.marker_seen.is_set():
                searchable = bytes(stream["marker_overlap"]) + chunk
                if self.success_marker in searchable:
                    self.marker_seen_at = time.monotonic()
                    self.marker_seen.set()
                overlap_size = max(0, len(self.success_marker) - 1)
                stream["marker_overlap"] = (
                    searchable[-overlap_size:] if overlap_size else b""
                )
            stream["count"] += len(chunk)
            self.total += len(chunk)
            head = stream["head"]
            if len(head) < _SOLVER_OUTPUT_HEAD_BYTES:
                head.extend(chunk[: _SOLVER_OUTPUT_HEAD_BYTES - len(head)])
            tail = stream["tail"]
            tail.extend(chunk)
            if len(tail) > _SOLVER_OUTPUT_TAIL_BYTES:
                del tail[: len(tail) - _SOLVER_OUTPUT_TAIL_BYTES]
            if self.total > self.limit:
                self.exceeded.set()

    def render(self, stream_name: str) -> str:
        with self.lock:
            stream = self.streams[stream_name]
            count = int(stream["count"])
            head = bytes(stream["head"])
            tail = bytes(stream["tail"])
        overlap = max(0, len(head) + len(tail) - count)
        if count <= len(head) + len(tail):
            payload = head + tail[overlap:]
        else:
            omitted = count - len(head) - len(tail)
            marker = f"\n... <{omitted} output bytes omitted> ...\n".encode()
            payload = head + marker + tail
        return payload.decode("utf-8", errors="replace")


def _run_managed_solver_sidecar(
    cmd: list[str],
    *,
    container_name: str,
    timeout: int | float,
    success_marker: bytes | None = None,
) -> tuple[subprocess.CompletedProcess, bool]:
    """Run a solver with a deadline, bounded output, and online flag capture."""

    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    collector = _BoundedSolverOutput(
        _SOLVER_OUTPUT_LIMIT_BYTES,
        success_marker=success_marker,
    )

    def drain(stream: Any, stream_name: str) -> None:
        if stream is None:
            return
        try:
            try:
                file_descriptor = stream.fileno()
            except (AttributeError, OSError):
                while chunk := stream.read(64 * 1024):
                    collector.append(stream_name, chunk)
            else:
                while chunk := os.read(file_descriptor, 64 * 1024):
                    collector.append(stream_name, chunk)
        except OSError:
            pass
        finally:
            try:
                stream.close()
            except OSError:
                pass

    readers = [
        threading.Thread(
            target=drain,
            args=(proc.stdout, "stdout"),
            daemon=True,
        ),
        threading.Thread(
            target=drain,
            args=(proc.stderr, "stderr"),
            daemon=True,
        ),
    ]
    for reader in readers:
        reader.start()

    deadline = time.monotonic() + max(0.001, float(timeout))
    timed_out = False
    output_limited = False
    capture_valid = False
    capture_deadline: float | None = None
    terminated_after_capture = False
    while proc.poll() is None:
        now = time.monotonic()
        marker_seen_at = collector.marker_seen_at
        if marker_seen_at is not None and marker_seen_at <= deadline:
            capture_valid = True
            if capture_deadline is None:
                capture_deadline = min(
                    deadline,
                    marker_seen_at + _SOLVER_CAPTURE_EXIT_GRACE_SECONDS,
                )
        if collector.exceeded.is_set():
            output_limited = True
            break
        if capture_valid and capture_deadline is not None and now >= capture_deadline:
            terminated_after_capture = True
            break
        active_deadline = (
            capture_deadline
            if capture_valid and capture_deadline is not None
            else deadline
        )
        remaining = active_deadline - now
        if remaining <= 0:
            if capture_valid:
                terminated_after_capture = True
            else:
                timed_out = True
            break
        try:
            proc.wait(timeout=min(0.1, remaining))
        except subprocess.TimeoutExpired:
            continue

    if proc.poll() is not None:
        for reader in readers:
            reader.join(timeout=5)
    marker_seen_at = collector.marker_seen_at
    if marker_seen_at is not None and marker_seen_at <= deadline:
        capture_valid = True
    if collector.exceeded.is_set():
        output_limited = True
    forced = timed_out or output_limited or terminated_after_capture
    cleanup_succeeded = False
    if forced:
        try:
            cleanup = _run(["docker", "rm", "-f", container_name], timeout=30)
            cleanup_succeeded = cleanup.returncode == 0
        except (OSError, subprocess.SubprocessError) as cleanup_exc:
            logger.warning(
                "failed to stop bounded solver sidecar %s: %s",
                container_name,
                cleanup_exc,
            )
        try:
            proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait()
        if not cleanup_succeeded:
            try:
                retry_cleanup = _run(
                    ["docker", "rm", "-f", container_name],
                    timeout=30,
                )
                if retry_cleanup.returncode != 0:
                    logger.warning(
                        "solver sidecar cleanup retry failed for %s: %s",
                        container_name,
                        _tail(retry_cleanup.stderr),
                    )
            except (OSError, subprocess.SubprocessError) as cleanup_exc:
                logger.warning(
                    "solver sidecar cleanup retry raised for %s: %s",
                    container_name,
                    cleanup_exc,
                )

    for reader in readers:
        reader.join(timeout=5)
    result = subprocess.CompletedProcess(
        cmd,
        None if forced else proc.returncode,
        collector.render("stdout"),
        collector.render("stderr"),
    )
    result.output_limited = output_limited
    result.output_bytes = collector.total
    result.marker_seen = capture_valid
    result.terminated_after_capture = terminated_after_capture
    return result, timed_out


def _normalize_timeout(timeout: int | float | None) -> int | float | None:
    if timeout in (None, 0, 0.0):
        return None
    return timeout


def _tail(text: str | None, n: int = 1500) -> str:
    text = text or ""
    return text[-n:]


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


# Host-administration / container-escape capabilities that a faithful archival
# CTF service should never need.  `docker compose config` resolves cap_add to an
# explicit list, so this denylist is checked against normalized upper-case caps.
_FORBIDDEN_CAP_ADD = frozenset(
    {
        "ALL",
        "SYS_ADMIN",
        "SYS_MODULE",
        "SYS_RAWIO",
        "SYS_PTRACE",
        "SYS_BOOT",
        "SYS_TIME",
        "DAC_READ_SEARCH",
        "NET_ADMIN",
        "BPF",
        "PERFMON",
        "CHECKPOINT_RESTORE",
    }
)

# security_opt values that disable a mandatory-access-control or syscall/proc
# confinement layer.  Compared after whitespace stripping, lower-casing, and
# normalizing the `key=value` form to `key:value`.
_FORBIDDEN_SECURITY_OPTS = frozenset(
    {
        "apparmor:unconfined",
        "seccomp:unconfined",
        "label:disable",
        "systempaths:unconfined",
    }
)

# A normalized probe marker shorter than this is too generic to prove the probe
# was lifted from real challenge material (e.g. "ok", "200", "<b").
_ANCHOR_MIN_LEN = 4
_ANCHOR_MAX_EVIDENCE_BYTES = 256 * 1024


def _normalize_anchor_text(text: str) -> str:
    """Lower-case and collapse whitespace for lenient marker/evidence matching."""

    return re.sub(r"\s+", " ", text.replace("\x00", " ")).strip().lower()


def _probe_expected_markers(probe: dict[str, Any]) -> list[str]:
    """The challenge-specific response strings a normalized probe asserts."""

    if probe.get("type") == "http":
        marker = str(probe.get("expect_body_contains") or "")
        return [marker] if marker else []
    markers: list[str] = []
    for step in probe.get("steps") or []:
        expected = step.get("expect_contains")
        if expected:
            markers.append(str(expected))
    return markers


def _normalize_security_opt(opt: Any) -> str:
    """Canonicalize a security_opt entry for denylist comparison."""

    return re.sub(r"\s+", "", str(opt)).lower().replace("=", ":")


# Bounded best-effort wait so a slow-but-correct service is not mis-scored as a
# probe failure just because it had not finished booting when probes started.
_READINESS_TIMEOUT_SECONDS = 30


def _await_target_readiness(
    targets: list[dict[str, Any]],
    *,
    deadline_seconds: int = _READINESS_TIMEOUT_SECONDS,
) -> dict[str, Any]:
    """Wait until each target's internal port accepts a TCP connection."""

    results: list[dict[str, Any]] = []
    deadline = time.monotonic() + max(1, deadline_seconds)
    for target in targets:
        host = str(target.get("container_addr") or "")
        port = target.get("internal_port")
        ready = False
        attempts = 0
        if host and port is not None:
            while time.monotonic() < deadline:
                attempts += 1
                try:
                    with socket.create_connection((host, int(port)), timeout=2):
                        ready = True
                        break
                except OSError:
                    remaining = deadline - time.monotonic()
                    if remaining <= 0:
                        break
                    time.sleep(min(1.0, remaining))
        results.append(
            {
                "service": target.get("service_name"),
                "container_addr": host or None,
                "internal_port": port,
                "ready": ready,
                "attempts": attempts,
            }
        )
    return {"deadline_seconds": deadline_seconds, "targets": results}


def _workspace_runtime_signature(workspace: Path) -> str:
    """Hash only files that can materially affect a rebuilt runtime."""

    digest = hashlib.sha256()
    digest.update(b"cage-build-target-live-runtime-v1\0")
    if not workspace.exists():
        digest.update(b"<missing>")
        return digest.hexdigest()

    for root, dirnames, filenames in os.walk(workspace, topdown=True, followlinks=False):
        root_path = Path(root)
        dirnames.sort()
        filenames.sort()

        kept_dirs: list[str] = []
        for dirname in dirnames:
            path = root_path / dirname
            rel = path.relative_to(workspace).as_posix()
            if rel in _LIVE_RUNTIME_SIGNATURE_IGNORES:
                continue
            if path.is_symlink():
                digest.update(f"symlink-dir:{rel}\0".encode("utf-8"))
                try:
                    digest.update(os.readlink(path).encode("utf-8", errors="surrogateescape"))
                except OSError:
                    digest.update(b"<unreadable>")
                continue
            kept_dirs.append(dirname)
        dirnames[:] = kept_dirs

        for filename in filenames:
            path = root_path / filename
            rel = path.relative_to(workspace).as_posix()
            if rel in _LIVE_RUNTIME_SIGNATURE_IGNORES:
                continue
            if path.is_symlink():
                digest.update(f"symlink-file:{rel}\0".encode("utf-8"))
                try:
                    digest.update(os.readlink(path).encode("utf-8", errors="surrogateescape"))
                except OSError:
                    digest.update(b"<unreadable>")
                continue
            if not path.is_file():
                continue
            try:
                mode = path.stat().st_mode & 0o7777
            except OSError:
                digest.update(f"missing-file:{rel}\0".encode("utf-8"))
                continue
            digest.update(f"file:{rel}\0mode:{mode:o}\0".encode("utf-8"))
            try:
                digest.update(_sha256_file(path).encode("ascii"))
            except OSError as exc:
                # The live agent may intentionally tighten a runtime artifact to
                # 0500/0600.  A permission bit must never crash the validator
                # HTTP handler before it can return structured feedback.  The
                # handler normally grants host-read permission first; this is a
                # stable defensive fallback for races and unusual filesystems.
                digest.update(
                    f"<unreadable:{type(exc).__name__}:{path.stat().st_size}>".encode(
                        "ascii", errors="replace"
                    )
                )
            digest.update(b"\0")
    return digest.hexdigest()


def _workspace_submission_digest(workspace: Path) -> str:
    """Hash every submitted path, mode, symlink target, and file byte."""

    digest = hashlib.sha256()
    digest.update(b"cage-build-target-submission-v1\0")
    if not workspace.exists():
        digest.update(b"<missing>")
        return digest.hexdigest()
    for path in sorted(
        workspace.rglob("*"),
        key=lambda item: item.relative_to(workspace).as_posix(),
    ):
        relative = path.relative_to(workspace).as_posix()
        metadata = path.lstat()
        digest.update(relative.encode("utf-8", errors="surrogateescape"))
        digest.update(b"\0")
        digest.update(f"{metadata.st_mode & 0o7777:o}".encode("ascii"))
        digest.update(b"\0")
        if path.is_symlink():
            digest.update(b"L\0")
            digest.update(os.readlink(path).encode("utf-8", errors="surrogateescape"))
        elif path.is_dir():
            digest.update(b"D")
        elif path.is_file():
            digest.update(b"F\0")
            digest.update(str(metadata.st_size).encode("ascii"))
            digest.update(b"\0")
            with path.open("rb") as handle:
                while chunk := handle.read(1024 * 1024):
                    digest.update(chunk)
        else:
            digest.update(b"O")
        digest.update(b"\n")
    return digest.hexdigest()


def _freeze_live_submission(
    ctx: _LiveTrialContext,
    *,
    check_number: int,
) -> tuple[_LiveTrialContext, str, str, str]:
    """Copy a stable check submission and return its frozen scoring context."""

    submission_id = f"check-{check_number:02d}-{uuid.uuid4().hex[:12]}"
    submission_root = ctx.trial_dir / "validator" / "submissions" / submission_id
    snapshot_workspace = submission_root / "workspace"
    submission_root.mkdir(parents=True, exist_ok=False)
    snapshot_workspace.mkdir()
    try:
        source_before = _workspace_submission_digest(ctx.workspace)
        copied = _run(
            [
                "cp",
                "--archive",
                "--reflink=auto",
                f"{ctx.workspace}/.",
                str(snapshot_workspace),
            ],
            timeout=300,
        )
        if copied.returncode != 0:
            raise RuntimeError(
                "failed to freeze cage-check workspace: "
                + _tail(copied.stderr or copied.stdout, 1200)
            )
        snapshot_digest = _workspace_submission_digest(snapshot_workspace)
        source_after = _workspace_submission_digest(ctx.workspace)
        if not (source_before == snapshot_digest == source_after):
            raise _WorkspaceChangedDuringSnapshot(
                "workspace bytes changed while cage-check was freezing the submission"
            )
        runtime_signature = _workspace_runtime_signature(snapshot_workspace)
        (submission_root / "submission.json").write_text(
            json.dumps(
                {
                    "schema_version": "cage-build-target-submission-v1",
                    "trial_id": ctx.trial_id,
                    "submission_id": submission_id,
                    "submission_digest": snapshot_digest,
                    "runtime_signature": runtime_signature,
                },
                indent=2,
                sort_keys=True,
            )
            + "\n",
            encoding="utf-8",
        )
    except Exception:
        shutil.rmtree(submission_root, ignore_errors=True)
        raise

    frozen = _LiveTrialContext(
        trial_id=ctx.trial_id,
        trial_dir=submission_root,
        workspace=snapshot_workspace,
        sample=copy.deepcopy(ctx.sample),
        agent_container=ctx.agent_container,
        token=ctx.token,
    )
    return frozen, submission_id, snapshot_digest, runtime_signature


def _workspace_is_host_readable(workspace: Path) -> bool:
    """Whether the host runner can traverse and read the live workspace."""

    if not os.access(workspace, os.R_OK | os.X_OK):
        return False
    try:
        for root, dirnames, filenames in os.walk(
            workspace, topdown=True, followlinks=False
        ):
            root_path = Path(root)
            if not os.access(root_path, os.R_OK | os.X_OK):
                return False
            for dirname in dirnames:
                path = root_path / dirname
                if not path.is_symlink() and not os.access(path, os.R_OK | os.X_OK):
                    return False
            for filename in filenames:
                path = root_path / filename
                if not path.is_symlink() and path.is_file() and not os.access(path, os.R_OK):
                    return False
    except OSError:
        return False
    return True


def _read_service_output(workspace: Path) -> str:
    path = workspace / "service_output.txt"
    if not path.is_file():
        return ""
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def _probe_hint_from_targets(targets: list[dict[str, Any]]) -> str:
    target = next((item for item in targets if item.get("container_addr")), None)
    if not isinstance(target, dict):
        return "probe the returned live target"

    addr = str(target.get("container_addr") or "")
    port = target.get("internal_port")
    proto = str(target.get("protocol") or "tcp").lower()
    if addr and port is not None and proto == "http":
        return f"curl -i http://{addr}:{port}/"
    if addr and port is not None:
        return f"nc -vz {addr} {port}"
    return f"probe {addr}".strip() or "probe the returned live target"


def _live_pass_feedback(
    *,
    targets: list[dict[str, Any]],
    runtime_reused: bool,
    validated_rehost_tier: str,
    runtime_probe_results: dict[str, Any] | None,
) -> str:
    if validated_rehost_tier == "R5":
        reuse = " The existing validated stack was reused." if runtime_reused else ""
        return (
            "Validator PASS through R5: CAGE built a clean target, minted and "
            "injected a private random flag, and the solve/ entry captured it from "
            "the player-side validation container."
            + reuse
            + " The final scorer will independently replay the same committed "
            "artifacts with a different random flag. Run `cage-check stop` and finish."
        )
    if validated_rehost_tier == "R4" and runtime_probe_results:
        first_probe = next(iter(runtime_probe_results.get("probes") or []), {})
        attempt = next(
            (
                item
                for item in first_probe.get("attempts") or []
                if item.get("passed")
            ),
            {},
        )
        excerpt = ""
        response = attempt.get("response") if isinstance(attempt, dict) else None
        if isinstance(response, dict):
            excerpt = str(response.get("body_excerpt") or "").strip()[:240]
            if response.get("status") is not None:
                excerpt = f"HTTP {response['status']} {excerpt}".strip()
        if not excerpt and isinstance(attempt, dict):
            step = next(
                (
                    item
                    for item in attempt.get("steps") or []
                    if item.get("matched")
                ),
                {},
            )
            excerpt = str(step.get("response_excerpt") or "").strip()[:240]
        reuse = " The existing validated stack was reused." if runtime_reused else ""
        return (
            "Validator PASS through R4: CAGE independently executed the "
            "challenge-specific, source-backed runtime probe."
            + reuse
            + (f" Probe excerpt: {excerpt!r}." if excerpt else "")
            + " Quote or summarize this validator result in your final response, "
            "run `cage-check stop`, and finish. Do not rerun or replace it with "
            "an agent-authored port check."
        )
    probe_hint = _probe_hint_from_targets(targets)
    reuse = " The existing stack was reused." if runtime_reused else ""
    return (
        "Validator PASS through R3 only: the image built and stayed up, but no "
        "independent challenge-specific runtime probe was required by this task."
        + reuse
        + f" A manual check such as {probe_hint!r} is review context only and cannot promote R4. "
        "Do not claim R4; run `cage-check stop` and finish."
    )


class BuildTarget(Benchmark):
    """Agent builds a bootable target from role-classified challenge material."""

    name = "build_target"
    artifact_task = True

    def __init__(
        self,
        benchmark_root: str | Path | None = None,
        pwn_runtime_cache: str | Path | None = None,
        agent_validation: bool = False,
        validation_host: str = "0.0.0.0",
        validation_port: int = 0,
        validation_build_timeout: int = 0,
        validation_max_concurrent: int = 1,
        validation_max_checks: int = 8,
        pipeline_prompts: bool = False,
        pipeline_stage: str = "env",
        exploit_gate: bool = False,
        exploit_timeout: int = 180,
        exploit_attempts: int = DEFAULT_EXPLOIT_ATTEMPTS,
        solver_image: str = DEFAULT_SOLVER_IMAGE,
    ) -> None:
        root = Path(benchmark_root).expanduser() if benchmark_root else DATASETS_DIR
        if not root.is_absolute():
            root = (Path(__file__).resolve().parent / root).resolve()
        if not root.is_dir():
            raise FileNotFoundError(f"build_target benchmark root is not a directory: {root}")
        self._datasets_dir = root
        self._pwn_runtime_cache_root = _resolve_runtime_cache(pwn_runtime_cache)
        self._pwn_runtime_cache = _load_pwn_runtime_cache(self._pwn_runtime_cache_root)
        self._agent_validation = bool(agent_validation)
        self._validation_host = str(validation_host or "0.0.0.0")
        self._validation_port = int(validation_port or 0)
        self._validation_build_timeout = int(validation_build_timeout or 0)
        self._validation_max_checks = max(1, int(validation_max_checks or 1))
        self._pipeline_prompts = bool(pipeline_prompts)
        _stage = str(pipeline_stage or "env").strip().lower()
        self._pipeline_stage = _stage if _stage in {"env", "exp", "full"} else "env"
        if self._pipeline_prompts and not (GUIDES_SOURCE_DIR / "INDEX.md").is_file():
            raise FileNotFoundError(
                f"missing build-target guide index: {GUIDES_SOURCE_DIR / 'INDEX.md'}"
            )
        self._exploit_gate = bool(exploit_gate)
        self._exploit_timeout = max(30, int(exploit_timeout or 180))
        self._exploit_attempts = max(1, int(exploit_attempts or 1))
        self._configured_solver_image = str(solver_image or DEFAULT_SOLVER_IMAGE).strip()
        self._pinned_solver_image_id: str | None = None
        self._solver_image_lock = threading.Lock()
        self._docker_gate = threading.Semaphore(max(1, int(validation_max_concurrent or 1)))
        self._validator_lock = threading.Lock()
        self._live_trials_lock = threading.Lock()
        self._validator_server: ThreadingHTTPServer | None = None
        self._validator_thread: threading.Thread | None = None
        self._validator_url: str | None = None
        self._live_trials: dict[str, _LiveTrialContext] = {}
        if self._agent_validation and not CHECK_CLIENT_PATH.is_file():
            raise FileNotFoundError(f"missing validator client script: {CHECK_CLIENT_PATH}")

    def _solver_image(self) -> str:
        """Return the run-stable solver image, pinning it once when R5 is on."""

        if not self._exploit_gate:
            return self._configured_solver_image
        with self._solver_image_lock:
            if self._pinned_solver_image_id is None:
                self._pinned_solver_image_id = _pin_default_solver_image(
                    self._configured_solver_image
                )
            return self._pinned_solver_image_id

    def iter_samples(self) -> Iterator[dict[str, Any]]:
        seen_ids: set[str] = set()
        records: list[dict[str, Any]] = []
        for sample_dir in sorted(p for p in self._datasets_dir.iterdir() if p.is_dir()):
            task_file = sample_dir / "task.json"
            if not task_file.is_file():
                continue
            meta = json.loads(task_file.read_text(encoding="utf-8"))
            if not isinstance(meta, dict):
                raise ValueError(f"{task_file} must contain a JSON object")

            sample_id = str(meta.get("id") or meta.get("name") or sample_dir.name).strip()
            if not sample_id:
                raise ValueError(f"{task_file} must declare a non-empty id or name")
            if sample_id in seen_ids:
                raise ValueError(f"duplicate build_target sample id: {sample_id!r}")
            seen_ids.add(sample_id)

            materials = _normalize_materials(meta)
            route = resolve_route({**meta, "materials": materials})
            declared_profile = str(meta.get("material_profile") or "").strip().upper()
            if declared_profile and declared_profile != route.profile:
                raise ValueError(
                    f"{task_file} declares material_profile {declared_profile!r} "
                    f"but pipeline_route resolves to profile {route.profile!r}"
                )
            build_profile = _resolve_build_profile(meta, materials)
            category = str(meta.get("category", "unknown"))
            category_profile = _resolve_category_profile(category)
            data_tier, data_tier_source, inferred_data_tier = _normalize_data_tier(meta, materials)
            service_contract = _normalize_service_contract(meta, category_profile)
            image_names = _normalize_image_names(meta, build_profile)

            raw_material_root = meta.get("material_root")
            material_root = sample_dir
            if raw_material_root:
                material_root = Path(str(raw_material_root)).expanduser()
                if not material_root.is_absolute():
                    material_root = sample_dir / material_root
                material_root = material_root.resolve()
            if not material_root.is_dir():
                raise FileNotFoundError(
                    f"material_root for {task_file} is not a directory: {material_root}"
                )
            pwn_material_priority = _pwn_material_priority(
                category_profile, materials, material_root
            )

            files = _dedupe_paths([path for role in _MATERIAL_ROLES for path in materials[role]])
            pipeline_reminder_sample = {
                "data_tier": data_tier,
                "data_tier_source": data_tier_source,
                "build_profile": build_profile,
                "category_profile": category_profile,
                "material_profile": route.profile,
                "pipeline_route": route.route,
                "pwn_material_priority": pwn_material_priority,
                "image_names": image_names,
                "service_contract": service_contract,
                "materials": materials,
            }
            records.append(
                {
                    "id": sample_id,
                    "name": meta.get("name", sample_dir.name),
                    "category": category,
                    "category_profile": category_profile,
                    "build_profile": build_profile,
                    "data_tier": data_tier,
                    "data_tier_source": data_tier_source,
                    "inferred_data_tier": inferred_data_tier,
                    "data_tier_evidence": _optional_metadata_object(meta, "data_tier_evidence"),
                    "target_maturity": _optional_metadata_object(meta, "target_maturity"),
                    "material_states": _optional_metadata_object(meta, "material_states"),
                    # Preserve the formal static-data routing contract.  Dropping
                    # these fields made build_prompt silently re-infer the route
                    # and hid profile/route drift from both prompt and scorer.
                    "material_profile": route.profile,
                    "pipeline_route": route.route,
                    "docker_closure": _optional_metadata_object(meta, "docker_closure"),
                    "static_evidence": _optional_metadata_object(meta, "static_evidence"),
                    "queue_priority": _optional_metadata_object(meta, "queue_priority"),
                    "pwn_material_priority": pwn_material_priority,
                    "pwn_runtime": self._pwn_runtime_cache,
                    "pwn_runtime_cache_path": (
                        str(self._pwn_runtime_cache_root)
                        if self._pwn_runtime_cache_root is not None
                        else None
                    ),
                    "description": meta.get("description", ""),
                    "content": meta.get("description", ""),
                    "flag": meta.get("flag", ""),
                    "flag_format": meta.get("flag_format", "flag{...}"),
                    "flag_contract": _public_flag_contract(meta),
                    "service_contract": service_contract,
                    "internal_port": int(service_contract.get("internal_port") or 0),
                    "build_environment": _normalize_build_environment(meta),
                    "image_name": image_names[0] if image_names else None,
                    "image_names": image_names,
                    "materials": materials,
                    "files": files,
                    "challenge_path": str(material_root),
                    "task_path": str(task_file),
                    # Full B+P episodes get the same graceful pre-cap flush as
                    # CyberGym gendesc: the framework resolves this offset
                    # against runtime.max_rounds and injects the message on
                    # every remaining forwarded request before the hard cap.
                    **(
                        {
                            "startup_reminder_at": (
                                DEFAULT_FULL_PIPELINE_STARTUP_REMINDER_AT
                            ),
                            "startup_reminder_until": (
                                DEFAULT_FULL_PIPELINE_STARTUP_REMINDER_UNTIL
                            ),
                            "startup_reminder_message": (
                                _full_pipeline_startup_message(
                                    pipeline_reminder_sample
                                )
                            ),
                            "wrapup_before": DEFAULT_FULL_PIPELINE_WRAPUP_BEFORE,
                            "wrapup_message": _full_pipeline_wrapup_message(
                                pipeline_reminder_sample
                            ),
                        }
                        if self._pipeline_prompts and self._pipeline_stage == "full"
                        else {}
                    ),
                }
            )

        # The current production wave prioritizes Pwn evidence shapes exactly as
        # declared in ``_PWN_MATERIAL_PRIORITIES``. D tier is only a tiebreaker:
        # it must never collapse the actual material-combination distinction.
        def queue_key(sample: dict[str, Any]) -> tuple[Any, ...]:
            declared_sort_key = (sample.get("queue_priority") or {}).get("sort_key")
            if declared_sort_key is not None:
                if not isinstance(declared_sort_key, list) or not declared_sort_key:
                    raise ValueError("queue_priority.sort_key must be a non-empty list")
                return tuple(declared_sort_key)
            is_pwn = sample["category_profile"] == "pwn"
            pwn_rank = int(sample["pwn_material_priority"]["rank"]) if is_pwn else 0
            tier_rank = -int(str(sample["data_tier"])[1:])
            return (0 if is_pwn else 1, pwn_rank, tier_rank, str(sample["id"]))

        yield from sorted(records, key=queue_key)

    def _validator_base_url(self) -> str:
        if not self._validator_url:
            raise RuntimeError("build_target validator is not running")
        return self._validator_url

    def _ensure_live_validator(self) -> None:
        if not self._agent_validation:
            return
        # Fail the batch before starting any agent-authored Docker build if the
        # host's default solver tag is absent, contaminated, or incomplete.
        self._solver_image()
        with self._validator_lock:
            if self._validator_server is not None:
                return

            benchmark = self

            class _Handler(BaseHTTPRequestHandler):
                def _send(self, code: int, payload: dict[str, Any]) -> None:
                    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
                    self.send_response(code)
                    self.send_header("Content-Type", "application/json")
                    self.send_header("Content-Length", str(len(body)))
                    self.end_headers()
                    try:
                        self.wfile.write(body)
                    except (BrokenPipeError, ConnectionResetError):
                        logger.info(
                            "build_target validator client disconnected before response"
                        )

                def _token(self, prefix: str) -> str | None:
                    path = self.path.split("?", 1)[0].strip("/")
                    parts = [part for part in path.split("/") if part]
                    if len(parts) == 2 and parts[0] == prefix:
                        return parts[1]
                    return None

                def do_GET(self) -> None:  # noqa: N802
                    if self.path.split("?", 1)[0].rstrip("/") == "/healthz":
                        self._send(200, {"ok": True})
                        return
                    self._send(404, {"error": "not found"})

                def do_POST(self) -> None:  # noqa: N802
                    token = self._token("check")
                    if token is not None:
                        try:
                            payload = benchmark._handle_live_check(token)
                        except KeyError:
                            self._send(404, {"passed": False, "feedback": "unknown trial token"})
                            return
                        except Exception as exc:  # noqa: BLE001 - HTTP safety boundary
                            logger.exception(
                                "unhandled build_target live-check error for token %s",
                                token[:8],
                            )
                            self._send(
                                500,
                                {
                                    "passed": False,
                                    "failure_class": "validator_internal_error",
                                    "retryable": True,
                                    "feedback": (
                                        "The CAGE validator hit an internal host error. "
                                        "Retry the same cage-check unchanged; do not edit "
                                        "candidate artifacts based on this host-only result."
                                    ),
                                    "evidence": {
                                        "attempt_consumed": False,
                                        "exception_type": type(exc).__name__,
                                    },
                                },
                            )
                            return
                        self._send(200, payload)
                        return
                    token = self._token("stop")
                    if token is not None:
                        try:
                            payload = benchmark._handle_live_stop(token)
                        except KeyError:
                            self._send(404, {"stopped": False, "feedback": "unknown trial token"})
                            return
                        except Exception as exc:  # noqa: BLE001 - HTTP safety boundary
                            logger.exception(
                                "unhandled build_target live-stop error for token %s",
                                token[:8],
                            )
                            self._send(
                                500,
                                {
                                    "stopped": False,
                                    "failure_class": "validator_internal_error",
                                    "retryable": True,
                                    "feedback": (
                                        "The CAGE validator hit an internal host error "
                                        "while stopping the live stack. Retry cage-check "
                                        "stop unchanged."
                                    ),
                                    "evidence": {
                                        "exception_type": type(exc).__name__,
                                    },
                                },
                            )
                            return
                        self._send(200, payload)
                        return
                    token = self._token("status")
                    if token is not None:
                        try:
                            payload = benchmark._handle_live_status(token)
                        except KeyError:
                            self._send(
                                404,
                                {
                                    "runtime_present": False,
                                    "error": "unknown trial token",
                                },
                            )
                            return
                        self._send(200, payload)
                        return
                    self._send(404, {"error": "not found"})

                def log_message(self, *args: Any) -> None:
                    pass

            server = ThreadingHTTPServer((self._validation_host, self._validation_port), _Handler)
            self._validator_server = server
            self._validator_url = f"http://{VALIDATOR_PUBLIC_HOST}:{server.server_port}"
            self._validator_thread = threading.Thread(
                target=server.serve_forever,
                name="build-target-validator",
                daemon=True,
            )
            self._validator_thread.start()
            logger.info("build_target validator listening on %s", self._validator_url)

    def _find_live_trial(self, token: str) -> _LiveTrialContext:
        with self._live_trials_lock:
            ctx = self._live_trials.get(token)
        if ctx is None:
            raise KeyError(token)
        return ctx

    def _find_live_trial_by_dir(self, trial_dir: Path) -> _LiveTrialContext | None:
        resolved = trial_dir.resolve()
        with self._live_trials_lock:
            for ctx in self._live_trials.values():
                if ctx.trial_dir.resolve() == resolved:
                    return ctx
        return None

    def _write_live_audit(
        self,
        ctx: _LiveTrialContext,
        action: str,
        payload: dict[str, Any],
    ) -> None:
        audit_path = ctx.trial_dir / "build_checks.jsonl"
        record = {
            "ts": int(time.time()),
            "trial_id": ctx.trial_id,
            "action": action,
            "payload": payload,
        }
        try:
            with audit_path.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")
        except OSError as exc:
            logger.warning("failed to append validator audit for %s: %s", ctx.trial_id, exc)

    def _live_validator_busy_payload(
        self,
        ctx: _LiveTrialContext,
        *,
        scope: str,
    ) -> dict[str, Any]:
        return {
            "passed": False,
            "failure_class": "validator_busy",
            "retryable": True,
            "check_count": ctx.check_count,
            "checks_remaining": max(
                0, self._validation_max_checks - ctx.check_count
            ),
            "evidence": {"busy_scope": scope, "attempt_consumed": False},
            "feedback": (
                "The host validator is already running a clean build/check. "
                "This scheduling response did not consume a validation attempt. "
                "Do not edit any artifact because of it. The cage-check client "
                "retries automatically; if this response is surfaced after its "
                "bounded wait, invoke the unchanged `cage-check --json` again."
            ),
        }

    def _stop_live_runtime(
        self,
        ctx: _LiveTrialContext,
        *,
        reason: str,
        docker_gate_already_acquired: bool = False,
    ) -> dict[str, Any]:
        runtime = ctx.last_runtime
        if runtime is None:
            payload = {"stopped": True, "reason": reason, "runtime_present": False}
            self._write_live_audit(ctx, "stop", payload)
            return payload
        scorer = _BootCheckScorer(
            build_timeout=self._validation_build_timeout,
            docker_gate=(
                None if docker_gate_already_acquired else self._docker_gate
            ),
        )
        payload = scorer.stop_live_runtime(runtime)
        payload["reason"] = reason
        payload["runtime_id"] = runtime.runtime_id
        payload["runtime_generation"] = runtime.generation
        ctx.last_invalidated_runtime_id = runtime.runtime_id
        ctx.last_runtime = None
        ctx.last_runtime_signature = None
        ctx.last_pass_payload = None
        self._write_live_audit(ctx, "stop", payload)
        return payload

    def _reused_live_payload(
        self,
        ctx: _LiveTrialContext,
        *,
        workspace_signature: str,
    ) -> dict[str, Any]:
        runtime = ctx.last_runtime
        payload = copy.deepcopy(ctx.last_pass_payload or {})
        if not payload:
            payload = {
                "passed": True,
                "value": 1.0,
                "failure_class": None,
                "explanation": "",
                "container_state": None,
                "container_addr": None,
                "network_name": runtime.network_name if runtime is not None else None,
                "targets": copy.deepcopy(runtime.service_targets if runtime is not None else []),
                "service_logs_tail": None,
                "retained_local_images": None,
                "image_manifest": runtime.image_manifest if runtime is not None else None,
                "review_files": {},
                "evidence": {},
            }
            payload["container_addr"] = next(
                (
                    str(target.get("container_addr"))
                    for target in payload["targets"]
                    if target.get("container_addr")
                ),
                None,
            )

        service_output = _read_service_output(ctx.workspace)
        runtime_probe_results = payload.get("runtime_probe_results")
        validated_rehost_tier = str(payload.get("validated_rehost_tier") or "R3")
        probe_evidence_present = bool(
            validated_rehost_tier == "R4"
            and isinstance(runtime_probe_results, dict)
            and runtime_probe_results.get("passed")
        )
        review_files = dict(payload.get("review_files") or {})
        review_files["agent_service_output"] = (
            str(ctx.workspace / "service_output.txt") if service_output.strip() else None
        )
        payload.update(
            {
                "passed": True,
                "failure_class": None,
                "check_count": ctx.check_count,
                "checks_remaining": max(
                    0, self._validation_max_checks - ctx.check_count
                ),
                "runtime_reused": True,
                "workspace_signature": workspace_signature,
                "submission_id": ctx.last_submission_id,
                "submission_digest": ctx.last_submission_digest,
                "runtime_id": runtime.runtime_id if runtime is not None else None,
                "runtime_generation": (
                    runtime.generation if runtime is not None else None
                ),
                "probe_evidence_present": probe_evidence_present,
                "agent_self_check_present": bool(service_output.strip()),
                "agent_service_output": service_output[-4000:] if service_output.strip() else "",
                "review_files": review_files,
                "feedback": _live_pass_feedback(
                    targets=payload.get("targets") or [],
                    runtime_reused=True,
                    validated_rehost_tier=validated_rehost_tier,
                    runtime_probe_results=(
                        runtime_probe_results
                        if isinstance(runtime_probe_results, dict)
                        else None
                    ),
                ),
            }
        )
        return payload

    def _handle_live_check(self, token: str) -> dict[str, Any]:
        ctx = self._find_live_trial(token)
        # One POST is one immutable submission.  Wait here instead of asking
        # the model-visible client to poll/re-submit and accidentally validate
        # different workspace bytes under the same logical check.
        ctx.lock.acquire()
        try:
            if ctx.terminal_payload is not None:
                payload = copy.deepcopy(ctx.terminal_payload)
                self._write_live_audit(ctx, "check_terminal_reused", payload)
                return payload
            # The bind-mounted workspace is authored by uid 1000 in the agent
            # image while the host runner commonly uses a different uid.  Keep
            # ownership with the agent, but add read/traverse permission before
            # the host hashes and validates real artifacts.  Dockerfile RUN
            # permissions inside the produced image are unaffected.
            if not _workspace_is_host_readable(ctx.workspace):
                try:
                    readable = _run(
                        [
                            "docker",
                            "exec",
                            "-u",
                            "0",
                            ctx.agent_container,
                            "chmod",
                            "-R",
                            "a+rX",
                            WORKSPACE_DIR,
                        ],
                        timeout=30,
                    )
                except subprocess.TimeoutExpired as exc:
                    payload = {
                        "passed": False,
                        "failure_class": "host_runtime_docker_timeout",
                        "retryable": True,
                        "feedback": (
                            "The CAGE host timed out while making the shared workspace "
                            "readable. Retry cage-check unchanged; do not edit candidate "
                            "artifacts based on this host-only result."
                        ),
                        "evidence": {
                            "attempt_consumed": False,
                            "timeout_seconds": exc.timeout,
                        },
                    }
                    self._write_live_audit(ctx, "check_host_transient", payload)
                    return payload
                if readable.returncode != 0:
                    payload = {
                        "passed": False,
                        "failure_class": "workspace_unreadable",
                        "retryable": True,
                        "feedback": (
                            "The host validator could not obtain read access to the "
                            "agent-authored workspace. Retry `cage-check`; do not "
                            "change challenge behavior to work around this."
                        ),
                        "evidence": {"stderr_tail": _tail(readable.stderr)},
                    }
                    self._write_live_audit(ctx, "check", payload)
                    return payload
            current_signature = _workspace_runtime_signature(ctx.workspace)
            if (
                ctx.last_runtime is not None
                and ctx.last_runtime_signature is not None
                and ctx.last_runtime_signature == current_signature
            ):
                payload = self._reused_live_payload(
                    ctx,
                    workspace_signature=current_signature,
                )
                self._write_live_audit(ctx, "check_reused", payload)
                return payload
            next_check = ctx.check_count + 1
            try:
                (
                    frozen_ctx,
                    submission_id,
                    submission_digest,
                    submission_runtime_signature,
                ) = _freeze_live_submission(ctx, check_number=next_check)
            except _WorkspaceChangedDuringSnapshot:
                payload = {
                    "passed": False,
                    "failure_class": "workspace_changed_during_snapshot",
                    "retryable": True,
                    "check_count": ctx.check_count,
                    "checks_remaining": max(
                        0, self._validation_max_checks - ctx.check_count
                    ),
                    "evidence": {"attempt_consumed": False},
                    "feedback": (
                        "The workspace changed while cage-check was freezing this "
                        "submission. No validation attempt was consumed. Let all "
                        "writes finish, then submit one unchanged cage-check."
                    ),
                }
                self._write_live_audit(ctx, "check_snapshot_changed", payload)
                return payload
            except (OSError, RuntimeError, subprocess.TimeoutExpired) as exc:
                payload = {
                    "passed": False,
                    "failure_class": "validator_submission_snapshot_failed",
                    "retryable": True,
                    "check_count": ctx.check_count,
                    "checks_remaining": max(
                        0, self._validation_max_checks - ctx.check_count
                    ),
                    "evidence": {
                        "attempt_consumed": False,
                        "exception_type": type(exc).__name__,
                    },
                    "feedback": (
                        "CAGE could not freeze an immutable validation submission. "
                        "No attempt was consumed; retry unchanged."
                    ),
                }
                self._write_live_audit(ctx, "check_snapshot_failed", payload)
                return payload
            self._docker_gate.acquire()
            try:
                if ctx.last_runtime is not None:
                    self._stop_live_runtime(
                        ctx,
                        reason="replaced_by_new_check",
                        docker_gate_already_acquired=True,
                    )
                ctx.check_count += 1
                scorer = _BootCheckScorer(
                    build_timeout=self._validation_build_timeout,
                    docker_gate=None,
                    exploit_gate=self._exploit_gate,
                    exploit_timeout=self._exploit_timeout,
                    exploit_attempts=self._exploit_attempts,
                    solver_image=self._solver_image(),
                )
                try:
                    payload = scorer.validate_live(
                        frozen_ctx,
                        check_label=f"check-{ctx.check_count:02d}",
                    )
                except Exception as exc:  # noqa: BLE001 - live-check safety boundary
                    logger.exception(
                        "unhandled build_target validation error for trial %s",
                        ctx.trial_id,
                    )
                    payload = {
                        "passed": False,
                        "failure_class": "validator_internal_error",
                        "retryable": True,
                        "feedback": (
                            "The CAGE validator hit an internal host error. Retry the "
                            "same cage-check unchanged; do not edit candidate artifacts "
                            "based on this host-only result."
                        ),
                        "evidence": {
                            "attempt_consumed": False,
                            "exception_type": type(exc).__name__,
                        },
                    }
                payload["submission_id"] = submission_id
                payload["submission_digest"] = submission_digest
                payload["workspace_signature"] = submission_runtime_signature
                if payload.get("failure_class") in _HOST_TRANSIENT_FAILURES:
                    # Host-only contention or a validator failure says nothing
                    # about the candidate and must not consume one of its
                    # bounded repair attempts.
                    ctx.check_count = max(0, ctx.check_count - 1)
                    payload["retryable"] = True
                    evidence = dict(payload.get("evidence") or {})
                    evidence["attempt_consumed"] = False
                    payload["evidence"] = evidence
                payload["check_count"] = ctx.check_count
                payload["checks_remaining"] = max(
                    0, self._validation_max_checks - ctx.check_count
                )
                if payload.get("failure_class") == "agent_reported_blocker":
                    # ``blocked`` is an honest, prompt-supported working state.
                    # It remains a final-score failure, but a premature live
                    # check must not permanently seal the trial after the agent
                    # later changes the same report to ``ready``.
                    payload["retryable"] = True
                    payload["feedback"] = (
                        "build_report.json still declares the working state "
                        "`blocked`, so this workspace was not validation-ready. "
                        "Keep the concrete blocker while working, change status "
                        "to `ready` only after the build contract is supported, "
                        "then run cage-check again. This live response did not "
                        "permanently seal the trial."
                    )
                runtime = payload.pop("_runtime", None)
                source_runtime_after = _workspace_runtime_signature(ctx.workspace)
                artifact_dirty = source_runtime_after != submission_runtime_signature
                payload["artifact_dirty"] = artifact_dirty
                if artifact_dirty:
                    submission_outcome = {
                        "passed": bool(payload.get("passed")),
                        "validated_rehost_tier": payload.get(
                            "validated_rehost_tier"
                        ),
                        "failure_class": payload.get("failure_class"),
                    }
                    if isinstance(runtime, _LiveRuntime):
                        scorer.stop_live_runtime(runtime)
                    runtime = None
                    ctx.check_count = max(0, ctx.check_count - 1)
                    payload.update(
                        {
                            "passed": False,
                            "failure_class": "workspace_changed_after_submission",
                            "retryable": True,
                            "check_count": ctx.check_count,
                            "checks_remaining": max(
                                0,
                                self._validation_max_checks - ctx.check_count,
                            ),
                            "submission_outcome": submission_outcome,
                            "feedback": (
                                "CAGE validated the frozen submission, but score-relevant "
                                "build/solve/contracts changed before its result returned. "
                                "That outcome is not attributed to the current workspace and "
                                "did not consume an attempt. Finish the edit, then submit one "
                                "new unchanged cage-check."
                            ),
                            "evidence": {
                                "attempt_consumed": False,
                                "submission_id": submission_id,
                                "submission_digest": submission_digest,
                            },
                        }
                    )
                ctx.last_runtime = runtime if isinstance(runtime, _LiveRuntime) else None
                if ctx.last_runtime is not None:
                    ctx.runtime_generation += 1
                    ctx.last_runtime.generation = ctx.runtime_generation
                    ctx.last_submission_id = submission_id
                    ctx.last_submission_digest = submission_digest
                    payload["runtime_id"] = ctx.last_runtime.runtime_id
                    payload["runtime_generation"] = ctx.last_runtime.generation
                if ctx.last_runtime is not None and payload.get("passed"):
                    ctx.last_runtime_signature = submission_runtime_signature
                    ctx.last_pass_payload = copy.deepcopy(payload)
                else:
                    ctx.last_runtime_signature = None
                    ctx.last_pass_payload = None
                    if payload.get("retryable") is False:
                        ctx.terminal_payload = copy.deepcopy(payload)
                    elif ctx.check_count >= self._validation_max_checks:
                        last_failure_class = payload.get("failure_class")
                        last_feedback = payload.get("feedback")
                        payload = {
                            **payload,
                            "passed": False,
                            "failure_class": "validation_attempt_budget_exhausted",
                            "retryable": False,
                            "feedback": (
                                f"CAGE validation used all {self._validation_max_checks} allowed "
                                "build/check attempts without reaching the requested maturity. "
                                f"The last result was {last_failure_class!r}: "
                                f"{last_feedback or 'no feedback returned'}. "
                                "Preserve that concrete result in a structured blocker and finish."
                            ),
                            "last_failure_class": last_failure_class,
                            "last_feedback": last_feedback,
                            "evidence": {
                                "check_count": ctx.check_count,
                                "last_failure_class": last_failure_class,
                                "last_feedback": last_feedback,
                            },
                        }
                        ctx.terminal_payload = copy.deepcopy(payload)
                self._write_live_audit(ctx, "check", payload)
                return payload
            finally:
                self._docker_gate.release()
        finally:
            ctx.lock.release()

    def _handle_live_stop(self, token: str) -> dict[str, Any]:
        ctx = self._find_live_trial(token)
        with ctx.lock:
            pass_payload = copy.deepcopy(ctx.last_pass_payload or {})
            runtime = ctx.last_runtime
            submitted_runtime_signature = ctx.last_runtime_signature
            current_runtime_signature = _workspace_runtime_signature(ctx.workspace)
            runtime_artifacts_unchanged = bool(
                submitted_runtime_signature
                and submitted_runtime_signature == current_runtime_signature
            )
            r5_passed = bool(
                pass_payload.get("passed")
                and pass_payload.get("validated_rehost_tier") == "R5"
            )
            payload = self._stop_live_runtime(ctx, reason="agent_requested_stop")
            payload["runtime_artifacts_unchanged"] = runtime_artifacts_unchanged
            payload["live_success_recorded"] = False
            if r5_passed and runtime_artifacts_unchanged and payload.get("stopped"):
                verdict = record_live_success(
                    trial_dir=ctx.trial_dir,
                    trial_id=ctx.trial_id,
                    benchmark="build_target",
                    mode="reactive",
                    source="build_target_r5_stop",
                    evidence={
                        "validated_rehost_tier": "R5",
                        "submission_id": ctx.last_submission_id,
                        "submission_digest": ctx.last_submission_digest,
                        "runtime_signature": submitted_runtime_signature,
                        "runtime_id": runtime.runtime_id if runtime is not None else None,
                        "runtime_generation": (
                            runtime.generation if runtime is not None else None
                        ),
                        "attempt_count": pass_payload.get(
                            "exploit_attempt_count"
                        ),
                        "successful_attempt": pass_payload.get(
                            "exploit_successful_attempt"
                        ),
                        "outcome_class": pass_payload.get(
                            "exploit_outcome_class"
                        ),
                        "solve_exit_clean": pass_payload.get(
                            "exploit_solve_exit_clean"
                        ),
                        "solver_outcome_class": pass_payload.get(
                            "exploit_solver_outcome_class"
                        ),
                    },
                )
                payload["live_success_recorded"] = True
                payload["live_success"] = verdict
                payload["feedback"] = (
                    "Live validation stack stopped and the immutable R5 "
                    "submission was sealed as the trial's live-success verdict."
                )
                ctx.terminal_payload = {
                    **pass_payload,
                    "runtime_present": False,
                    "live_success_recorded": True,
                }
            elif r5_passed and not runtime_artifacts_unchanged:
                payload["requires_revalidation"] = True
                payload["feedback"] = (
                    "The retained stack was stopped, but build/solve/contracts "
                    "changed after the passing submission. R5 was not sealed. "
                    "Run cage-check again on the finished artifacts before ending."
                )
            return payload

    def _handle_live_status(self, token: str) -> dict[str, Any]:
        ctx = self._find_live_trial(token)
        with ctx.lock:
            runtime = ctx.last_runtime
            if runtime is None:
                return {
                    "runtime_present": False,
                    "last_invalidated_runtime_id": ctx.last_invalidated_runtime_id,
                    "check_count": ctx.check_count,
                    "last_submission_id": ctx.last_submission_id,
                }
            attached = False
            inspect_error: str | None = None
            if runtime.network_name:
                try:
                    inspected = _run(
                        [
                            "docker",
                            "inspect",
                            "--format",
                            "{{json .NetworkSettings.Networks}}",
                            ctx.agent_container,
                        ],
                        timeout=30,
                    )
                    if inspected.returncode == 0:
                        networks = json.loads(inspected.stdout or "{}")
                        attached = runtime.network_name in networks
                    else:
                        inspect_error = _tail(inspected.stderr or inspected.stdout)
                except (OSError, subprocess.SubprocessError, json.JSONDecodeError) as exc:
                    inspect_error = f"{type(exc).__name__}: {exc}"
            return {
                "runtime_present": True,
                "runtime_id": runtime.runtime_id,
                "runtime_generation": runtime.generation,
                "network_name": runtime.network_name,
                "targets": copy.deepcopy(runtime.service_targets),
                "agent_attached": attached,
                "inspect_error": inspect_error,
                "check_count": ctx.check_count,
                "submission_id": ctx.last_submission_id,
            }

    def configure_trial_container(
        self,
        container: "Container",
        sample: dict[str, Any],
        *,
        trial_id: str,
        trial_dir: Path,
    ) -> None:
        if not self._agent_validation:
            return
        self._ensure_live_validator()
        workspace = trial_dir / "workspace"
        workspace.mkdir(parents=True, exist_ok=True)
        token = uuid.uuid4().hex
        with self._live_trials_lock:
            self._live_trials[token] = _LiveTrialContext(
                trial_id=trial_id,
                trial_dir=trial_dir,
                workspace=workspace,
                sample=dict(sample),
                agent_container=container.name,
                token=token,
            )
        for host_path, container_path in list(container.volumes.items()):
            if str(container_path).split(":", 1)[0] == WORKSPACE_DIR:
                container.volumes.pop(host_path)
        container.volumes[str(workspace)] = WORKSPACE_DIR
        container.env_vars[LIVE_WORKSPACE_ENV] = "1"
        container.env_vars["CAGE_CHECK_URL"] = f"{self._validator_base_url()}/check/{token}"
        container.env_vars["CAGE_CHECK_STOP_URL"] = f"{self._validator_base_url()}/stop/{token}"
        container.env_vars["CAGE_CHECK_STATUS_URL"] = (
            f"{self._validator_base_url()}/status/{token}"
        )
        build_timeout = self._validation_build_timeout or 1800
        container.env_vars["CAGE_CHECK_TIMEOUT_SECONDS"] = str(
            max(
                4 * 60 * 60,
                build_timeout
                + self._exploit_timeout * self._exploit_attempts
                + 600,
            )
        )

    def prepare_trial(
        self,
        container: "Container",
        sample: dict[str, Any],
        workspace_dir: str,
    ) -> None:
        container.exec(f"mkdir -p {shlex.quote(workspace_dir)}")
        challenge_dir = Path(sample["challenge_path"])
        for filename in sample.get("files", []):
            rel = _safe_relative_path(filename)
            source = challenge_dir / rel
            if not source.exists():
                raise FileNotFoundError(
                    f"declared material for sample {sample.get('id')!r} does not exist: {source}"
                )
            dest_parent = f"{workspace_dir}/{rel.parent.as_posix()}"
            container.exec(f"mkdir -p {shlex.quote(dest_parent)}")
            container.copy_to(str(source), f"{workspace_dir}/{rel.as_posix()}")
        if (
            sample.get("category_profile") == "pwn"
            and sample.get("pwn_runtime", {}).get("status") == "ready"
        ):
            cache_root = Path(str(sample["pwn_runtime_cache_path"]))
            container.exec(f"mkdir -p {shlex.quote(PWN_RUNTIME_DIR)}")
            container.copy_to(f"{cache_root}/.", PWN_RUNTIME_DIR)
            container.exec(f"chmod -R a+rX {shlex.quote(PWN_RUNTIME_DIR)}")
        if self._pipeline_prompts:
            container.exec(f"mkdir -p {shlex.quote(GUIDES_AGENT_DIR)}")
            container.copy_to(f"{GUIDES_SOURCE_DIR}/.", GUIDES_AGENT_DIR)
            container.exec(
                f"chmod -R a-w,a+rX {shlex.quote(GUIDES_AGENT_DIR)}"
            )
            # Prompt instructions are necessary context, but they cannot stop a
            # model that nevertheless emits an unbounded root search or starts a
            # local substitute target. Install a narrow Claude Code PreToolUse
            # guard as a second line of defence. It merges with any existing
            # settings and is inert for non-Claude agents.
            container.exec(f"mkdir -p {shlex.quote(CLAUDE_CONFIG_DIR)}")
            container.copy_to(
                str(CLAUDE_BASH_GUARD_PATH), CLAUDE_BASH_GUARD_AGENT_PATH
            )
            container.exec(
                f"chmod 0755 {shlex.quote(CLAUDE_BASH_GUARD_AGENT_PATH)} && "
                f"/usr/bin/python3 {shlex.quote(CLAUDE_BASH_GUARD_AGENT_PATH)} "
                f"--install --settings {shlex.quote(CLAUDE_SETTINGS_PATH)} "
                f"--script {shlex.quote(CLAUDE_BASH_GUARD_AGENT_PATH)} && "
                f"chown agent:agent {shlex.quote(CLAUDE_CONFIG_DIR)} "
                f"{shlex.quote(CLAUDE_BASH_GUARD_AGENT_PATH)} "
                f"{shlex.quote(CLAUDE_SETTINGS_PATH)}"
            )
        if self._agent_validation:
            container.copy_to(str(CHECK_CLIENT_PATH), "/usr/local/bin/cage-check")
            container.exec("chmod 0755 /usr/local/bin/cage-check")
        # docker cp creates root-owned files. Build-target agents must be able to
        # make minimal compatibility edits to the copied deployment tree. The
        # live host validator uses a different uid, so preserve host read/traverse
        # access while leaving ownership and write access with the agent.
        container.exec(f"chown -R agent:agent {shlex.quote(workspace_dir)}")
        container.exec(f"chmod -R a+rX {shlex.quote(workspace_dir)}")

    def on_agent_finish(
        self,
        container: "Container",
        sample: dict[str, Any],
        trial_dir: str,
    ) -> None:
        live_ctx = self._find_live_trial_by_dir(Path(trial_dir))
        if live_ctx is not None:
            with live_ctx.lock:
                if live_ctx.last_runtime is not None:
                    self._stop_live_runtime(live_ctx, reason="agent_finished")
            return
        # Materialize the agent's produced files (Dockerfile / compose / wrapper)
        # to the host BEFORE scoring, so the boot-check validator reads a frozen
        # snapshot from ``<trial_dir>/workspace`` instead of the live container.
        workspace_out = Path(trial_dir) / "workspace"
        workspace_out.mkdir(parents=True, exist_ok=True)
        try:
            container.copy_from(f"{WORKSPACE_DIR}/.", str(workspace_out), timeout=300.0)
        except Exception as exc:  # noqa: BLE001
            logger.warning("workspace copy_from failed: %s", exc)

    def on_trial_complete(
        self,
        container: "Container",
        sample: dict[str, Any],
        trial_dir: str,
    ) -> None:
        del container, sample
        live_ctx = self._find_live_trial_by_dir(Path(trial_dir))
        if live_ctx is None:
            return
        with live_ctx.lock:
            if live_ctx.last_runtime is not None:
                self._stop_live_runtime(live_ctx, reason="trial_complete")
        with self._live_trials_lock:
            self._live_trials.pop(live_ctx.token, None)

    def build_prompt(self, sample: dict[str, Any]) -> str:
        private_keys = {"flag", "pwn_runtime_cache_path"}
        instance_data = {key: value for key, value in sample.items() if key not in private_keys}
        if self._pipeline_prompts:
            route = resolve_route(sample)
            instance_data["route"] = {
                **route.to_contract(),
                "summary": route.summary,
                "env_context_roles": list(route.env_context_roles),
                "exp_context_roles": list(route.exp_context_roles),
            }
            return render_prompt(
                template_dir=PROMPTS_DIR / "pipelines" / self._pipeline_stage,
                template_type="instance",
                expected_substrings=(route.route,),
                instance_data=instance_data,
                workspace=WORKSPACE_DIR,
                command_docs="",
                skill_descriptions="",
            )
        return render_prompt(
            template_dir=PROMPTS_DIR,
            template_type="instance",
            expected_substrings=(
                str(instance_data["build_profile"]),
                str(instance_data["category_profile"]),
                str(instance_data["data_tier"]),
            ),
            instance_data=instance_data,
            workspace="/home/agent/workspace",
            command_docs="",
            skill_descriptions="",
        )

    def scorer(self) -> Scorer:
        return _BootCheckScorer(
            build_timeout=self._validation_build_timeout,
            docker_gate=self._docker_gate,
            exploit_gate=self._exploit_gate,
            exploit_timeout=self._exploit_timeout,
            exploit_attempts=self._exploit_attempts,
            solver_image=self._solver_image(),
        )

    def teardown(self) -> None:
        with self._live_trials_lock:
            live_trials = list(self._live_trials.values())
            self._live_trials.clear()
        for ctx in live_trials:
            with ctx.lock:
                if ctx.last_runtime is not None:
                    self._stop_live_runtime(ctx, reason="benchmark_teardown")
        with self._validator_lock:
            server = self._validator_server
            thread = self._validator_thread
            self._validator_server = None
            self._validator_thread = None
            self._validator_url = None
        if server is not None:
            server.shutdown()
            server.server_close()
        if thread is not None:
            thread.join(timeout=5.0)


class _BootCheckScorer(Scorer):
    """Independently validate build, runtime semantics, and optional exploit capture.

    R3 requires a retained local image and stable target containers. R4 also
    requires source-backed semantic probes executed by this host-side scorer.
    When ``exploit_gate`` is enabled, R5 runs the committed solve/ from a
    player-side container against a freshly minted flag.
    """

    name = "build_target"

    def __init__(
        self,
        *,
        build_timeout: int | float | None = 420,
        docker_gate: threading.Semaphore | None = None,
        exploit_gate: bool = False,
        exploit_timeout: int = 180,
        exploit_attempts: int = DEFAULT_EXPLOIT_ATTEMPTS,
        solver_image: str = DEFAULT_SOLVER_IMAGE,
    ) -> None:
        self._build_timeout = _normalize_timeout(build_timeout)
        self._docker_gate = docker_gate
        self._exploit_gate = bool(exploit_gate)
        self._exploit_timeout = max(30, int(exploit_timeout or 180))
        self._exploit_attempts = max(1, int(exploit_attempts or 1))
        self._solver_image = str(solver_image or DEFAULT_SOLVER_IMAGE).strip()

    def _fail(
        self,
        failure_class: str,
        summary: str,
        *,
        retryable: bool,
        evidence: dict[str, Any] | None = None,
        feedback: str = "",
    ) -> dict[str, Score]:
        return {
            "build_target": Score(
                value=0.0,
                answer="",
                explanation=summary,
                metadata={
                    "passed": False,
                    "failure_class": failure_class,
                    "retryable": retryable,
                    "feedback": feedback or summary,
                    "evidence": evidence or {},
                },
            )
        }

    def _host_runtime_timeout_failure(
        self,
        exc: subprocess.TimeoutExpired,
    ) -> dict[str, Score]:
        raw_command = exc.cmd
        if isinstance(raw_command, (list, tuple)):
            command = [str(part) for part in raw_command]
        else:
            command = [str(raw_command)]
        return self._fail(
            "host_runtime_docker_timeout",
            "A bounded CAGE host-runtime command timed out during validation.",
            retryable=True,
            evidence={
                "command": command,
                "timeout_seconds": exc.timeout,
            },
            feedback=(
                "The CAGE Docker control plane timed out while inspecting or managing "
                "the authoritative runtime. This is a host-only transient and does not "
                "show a candidate defect. Retry cage-check unchanged; do not edit "
                "candidate artifacts based on this result."
            ),
        )

    def _challenge_json_example(
        self,
        ctx: ScoringContext,
        *,
        service_names: list[str] | None = None,
    ) -> str:
        candidates = [str(name).strip() for name in (service_names or []) if str(name).strip()]
        target_service = candidates[0] if candidates else "challenge"
        target_ports: dict[str, int] = {}
        raw_port = ctx.sample.get("internal_port")
        try:
            if raw_port not in (None, ""):
                target_ports[target_service] = int(raw_port)
        except (TypeError, ValueError):
            target_ports = {}

        protocol = "tcp"
        service_contract = ctx.sample.get("service_contract")
        if isinstance(service_contract, dict):
            declared_protocol = str(service_contract.get("protocol") or "").strip().lower()
            if declared_protocol in {"tcp", "http", "https"}:
                protocol = declared_protocol

        example = {
            "compose_files": ["docker-compose.yml"],
            "compose_target_services": [target_service],
            "compose_dependency_services": [],
            "target_ports": target_ports,
            "target_port_protocols": (
                {target_service: protocol}
                if target_ports or protocol != "tcp"
                else {}
            ),
        }
        if _runtime_probe_required(ctx.sample):
            materials = ctx.sample.get("materials") or {}
            evidence_path = next(
                iter((materials.get("writeups") or materials.get("source") or [])),
                "replace/with/supplied/writeup-path",
            )
            if protocol in {"http", "https"}:
                example["runtime_probes"] = [
                    {
                        "id": "application-entry",
                        "type": "http",
                        "service": target_service,
                        "method": "GET",
                        "path": "/",
                        "expect_status": 200,
                        "expect_body_contains": "replace with real application marker",
                        "evidence": [
                            {
                                "path": evidence_path,
                                "basis": "supplied solve material identifies this entry response",
                            }
                        ],
                    }
                ]
            else:
                example["runtime_probes"] = [
                    {
                        "id": "challenge-prompt",
                        "type": "tcp",
                        "service": target_service,
                        "steps": [
                            {
                                "expect_contains": "replace with real challenge prompt",
                            }
                        ],
                        "evidence": [
                            {
                                "path": evidence_path,
                                "basis": "supplied solve material waits for this prompt",
                            }
                        ],
                    }
                ]
        return json.dumps(example, indent=2, ensure_ascii=False)

    def _challenge_json_feedback(
        self,
        ctx: ScoringContext,
        *,
        services: dict[str, Any] | None = None,
        summary: str,
    ) -> str:
        service_names = list((services or {}).keys())
        return (
            summary
            + " Use Compose service names as keys. `target_ports` values must be plain "
            + "integers, not strings, lists, or nested objects. Minimal valid shape:\n"
            + self._challenge_json_example(ctx, service_names=service_names)
        )

    def _runtime_policy_feedback(self) -> str:
        return (
            "The archival runtime contract forbids `privileged`, host "
            "networking/PID/IPC, `userns_mode: host`, sharing another container's "
            "PID/IPC namespace (`pid`/`ipc: container:` or `service:`), Docker socket "
            "mounts, host bind mounts (including host-backed named volumes whose "
            "`driver_opts` bind an absolute host `device`), devices, "
            "host-administration or "
            "container-escape capabilities such as `cap_add: [SYS_ADMIN]`, "
            "`[SYS_MODULE]`, `[SYS_RAWIO]`, `[SYS_PTRACE]`, `[NET_ADMIN]` or `[ALL]`, "
            "and confinement-disabling `security_opt` profiles such as "
            "`apparmor:unconfined`, `seccomp:unconfined`, `label:disable`, or "
            "`systempaths:unconfined`, plus fixed `container_name`. CAGE's reserved "
            f"solver aliases {sorted(DEFAULT_SOLVER_IMAGE_ALIASES)!r} may be referenced "
            "from challenge.json but must never appear on a Compose service with "
            "`build:`; remove that solver service and keep the exploit under `solve/`. "
            "Remove unsafe settings or return a structured blocker if the authentic "
            "target cannot run without them."
        )

    def _build_failure_feedback(
        self,
        stderr_tail: str,
        *,
        host_network_issue: bool = False,
    ) -> str:
        if host_network_issue:
            return (
                "CAGE could not create an isolated Docker network after bounded "
                "host-managed subnet retries. This is host infrastructure "
                "contention, not a defect in the candidate workspace. Do not edit "
                "Dockerfile, Compose, challenge metadata, or solve artifacts because "
                "of this result; retry the unchanged `cage-check --json`. Error tail:\n"
                + _tail(stderr_tail, 800)
            )
        base = (
            "The authoritative host-side `docker compose up --build` attempt "
            "failed. Do not reproduce or replace the target in the agent "
            "container. Obey the task's declared build-network and cached-image "
            "contract; identify the first fatal command or missing path in this "
            "tail, inspect the exact referenced workspace files, change one "
            "causal build-closure dimension, keep the revised candidate report "
            "`ready`, and let the next `cage-check` rebuild it. Error tail:\n"
            + _tail(stderr_tail, 800)
        )
        normalized = (stderr_tail or "").lower()
        if "all predefined address pools have been fully subnetted" in normalized:
            return (
                base
                + "\nHost Docker default address pools are exhausted. CAGE will retry with "
                + "a host-managed temporary subnet when possible."
            )
        return base

    def _service_failure_feedback(
        self,
        *,
        service_name: str,
        status: str,
        service_logs: str,
    ) -> str:
        return (
            f"Your image built but the service {service_name!r} did not stay up "
            f"(state={status!r}). This host-side container and its logs are "
            "authoritative; do not replace them with a locally launched target. "
            "Inspect the exact entrypoint, executable mode, interpreter/loader, "
            "user, working directory, and child stderr; change the first broken "
            "lifecycle link, then let the next `cage-check` rebuild it. Service "
            f"logs:\n{_tail(service_logs, 800)}"
        )

    def _compose_args(
        self,
        *,
        project: str,
        compose_files: list[Path],
        project_directory: Path | None = None,
    ) -> list[str]:
        args = ["docker", "compose"]
        if project_directory is not None:
            args.extend(["--project-directory", str(project_directory)])
        args.extend(["-p", project])
        for compose_file in compose_files:
            args.extend(["-f", str(compose_file)])
        return args

    def _is_address_pool_exhaustion(self, text: str) -> bool:
        # Docker reports network address-pool contention under several distinct
        # messages depending on version and whether the pool is exhausted or a
        # concurrently-created network overlapped. Any of them should route the
        # scorer onto its managed 10.240+/24 subnet allocation instead of a
        # false build_or_boot_failed — critical when other campaigns share the
        # host and crowd the default 172.x pool.
        normalized = (text or "").lower()
        return any(
            signature in normalized
            for signature in (
                "all predefined address pools have been fully subnetted",
                "could not find an available, non-overlapping ipv4 address pool",
                "pool overlaps with other one on this address space",
                "invalid pool request",
            )
        )

    def _list_reserved_ipv4_subnets(self) -> set[ipaddress.IPv4Network]:
        reserved: set[ipaddress.IPv4Network] = set()

        network_ls = _run(["docker", "network", "ls", "--format", "{{.ID}}"], timeout=60)
        network_ids = [
            line.strip() for line in (network_ls.stdout or "").splitlines() if line.strip()
        ]
        if network_ids:
            network_inspect = _run(
                ["docker", "network", "inspect", *network_ids],
                timeout=120,
            )
            if network_inspect.returncode == 0:
                try:
                    inspected = json.loads(network_inspect.stdout or "[]")
                except json.JSONDecodeError:
                    inspected = []
                if isinstance(inspected, dict):
                    inspected = [inspected]
                for item in inspected:
                    if not isinstance(item, dict):
                        continue
                    configs = ((item.get("IPAM") or {}).get("Config") or [])
                    for config in configs:
                        if not isinstance(config, dict):
                            continue
                        subnet = str(config.get("Subnet") or "").strip()
                        if not subnet:
                            continue
                        try:
                            reserved.add(ipaddress.ip_network(subnet, strict=False))
                        except ValueError:
                            continue

        host_routes = _run(["ip", "-4", "route", "show"], timeout=30)
        if host_routes.returncode == 0:
            for line in (host_routes.stdout or "").splitlines():
                route = line.strip().split()
                if not route:
                    continue
                destination = route[0]
                if destination == "default":
                    continue
                try:
                    reserved.add(ipaddress.ip_network(destination, strict=False))
                except ValueError:
                    continue

        return reserved

    def _managed_compose_network_names(self, config_data: dict[str, Any]) -> list[str]:
        managed: list[str] = []
        networks = config_data.get("networks")
        if isinstance(networks, dict) and networks:
            for name, raw_config in networks.items():
                config = raw_config if isinstance(raw_config, dict) else {}
                if bool(config.get("external")):
                    continue
                driver = str(config.get("driver") or "bridge").strip().lower() or "bridge"
                ipam = config.get("ipam") if isinstance(config.get("ipam"), dict) else {}
                ipam_config = ipam.get("config") or []
                if driver == "bridge" and not ipam_config:
                    managed.append(str(name))
            return managed
        return ["default"]

    def _allocate_managed_subnets(self, count: int, *, seed: str) -> list[str]:
        if count <= 0:
            return []
        reserved = self._list_reserved_ipv4_subnets()
        allocated: list[str] = []
        chosen: list[ipaddress.IPv4Network] = []
        candidates = [
            ipaddress.ip_network(f"10.{second}.{third}.0/24", strict=False)
            for second in range(240, 256)
            for third in range(0, 256)
        ]
        start = int(hashlib.sha256(seed.encode("utf-8")).hexdigest(), 16) % len(candidates)
        with _MANAGED_SUBNET_LOCK:
            in_process = set(_MANAGED_SUBNET_RESERVATIONS)
            for offset in range(len(candidates)):
                candidate = candidates[(start + offset) % len(candidates)]
                if any(candidate.overlaps(existing) for existing in reserved):
                    continue
                if any(candidate.overlaps(existing) for existing in in_process):
                    continue
                if any(candidate.overlaps(existing) for existing in chosen):
                    continue
                chosen.append(candidate)
                allocated.append(str(candidate))
                if len(allocated) >= count:
                    _MANAGED_SUBNET_RESERVATIONS.update(chosen)
                    return allocated
        return []

    def _release_managed_subnets(self, subnets: list[str]) -> None:
        if not subnets:
            return
        with _MANAGED_SUBNET_LOCK:
            for subnet in subnets:
                try:
                    candidate = ipaddress.ip_network(subnet, strict=False)
                except ValueError:
                    continue
                if isinstance(candidate, ipaddress.IPv4Network):
                    _MANAGED_SUBNET_RESERVATIONS.discard(candidate)

    def _write_managed_network_override(
        self,
        *,
        ctx: ScoringContext,
        project: str,
        config_data: dict[str, Any],
        retry_index: int,
    ) -> tuple[Path | None, list[str]]:
        if ctx.trial_dir is None:
            return None, []
        network_names = self._managed_compose_network_names(config_data)
        if not network_names:
            return None, []
        subnets = self._allocate_managed_subnets(
            len(network_names), seed=f"{project}:retry:{retry_index}"
        )
        if len(subnets) != len(network_names):
            return None, []
        override = {
            "networks": {
                network_name: {
                    "driver": "bridge",
                    "ipam": {"config": [{"subnet": subnet}]},
                }
                for network_name, subnet in zip(network_names, subnets, strict=True)
            }
        }
        override_dir = ctx.trial_dir / "validator"
        override_dir.mkdir(parents=True, exist_ok=True)
        override_path = override_dir / f"{project}-managed-networks.override.json"
        try:
            override_path.write_text(
                json.dumps(override, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
        except Exception:
            self._release_managed_subnets(subnets)
            raise
        return override_path, subnets

    def _inject_flag_into_services(
        self,
        *,
        services: dict[str, Any],
        managed_dir: Path,
        flag: str,
        flag_contract: dict[str, Any],
    ) -> None:
        """Inject a minted flag into the target service before boot.

        ``file`` -> write the flag to a temp file and bind-mount it read-only at
        the declared path (overwrites any placeholder baked into the image).
        ``env`` -> set the declared environment variable on the service. Applied
        to the declared service, or every service when none is named.
        """
        target = str(flag_contract.get("service") or "").strip()
        names = [target] if target in services else list(services)
        method = str(flag_contract.get("inject") or "file")
        for name in names:
            service = services.get(name)
            if not isinstance(service, dict):
                continue
            service = dict(service)
            if method == "env":
                env_name = str(flag_contract.get("env") or "FLAG")
                env = service.get("environment")
                if isinstance(env, list):
                    env = [e for e in env if not str(e).startswith(f"{env_name}=")]
                    env.append(f"{env_name}={flag}")
                elif isinstance(env, dict):
                    env = {**env, env_name: flag}
                else:
                    env = {env_name: flag}
                service["environment"] = env
            else:
                path = str(flag_contract.get("path") or "/flag.txt")
                flag_file = managed_dir / "cage-injected-flag"
                flag_file.write_text(flag, encoding="utf-8")
                volumes = list(service.get("volumes") or [])
                volumes = [
                    volume
                    for volume in volumes
                    if not (
                        (
                            isinstance(volume, dict)
                            and str(volume.get("target") or "") == path
                        )
                        or (
                            isinstance(volume, str)
                            and (
                                volume.endswith(f":{path}")
                                or f":{path}:" in volume
                            )
                        )
                    )
                ]
                # Compose short syntax cannot represent a host source path that
                # itself contains ":" (run directories include agent labels
                # such as ``claude_code:deepseek-v4-pro:stateless``). Long
                # syntax is unambiguous on every supported path.
                volumes.append(
                    {
                        "type": "bind",
                        "source": str(flag_file.resolve()),
                        "target": path,
                        "read_only": True,
                    }
                )
                service["volumes"] = volumes
            services[name] = service

    def _write_managed_runtime_compose(
        self,
        *,
        ctx: ScoringContext,
        project: str,
        workspace: Path,
        compose_path: Path,
        config_data: dict[str, Any],
        injected_flag: str | None = None,
        flag_contract: dict[str, Any] | None = None,
    ) -> tuple[Path | None, list[str]]:
        try:
            raw = yaml.safe_load(compose_path.read_text(encoding="utf-8")) or {}
        except (OSError, yaml.YAMLError):
            return None, []
        if not isinstance(raw, dict):
            return None, []

        services = raw.get("services")
        if not isinstance(services, dict):
            return None, []

        for service_name, service_config in list(services.items()):
            if not isinstance(service_config, dict):
                continue
            service_config = dict(service_config)
            service_config.pop("ports", None)

            # The managed runtime is an authority boundary, so an agent-authored
            # Compose file cannot opt out of the host safety ceiling.  Preserve a
            # stricter positive limit when one is already declared; normalize
            # missing, unlimited, malformed, or overly broad values to CAGE's cap.
            try:
                requested_pids_limit = int(service_config.get("pids_limit"))
            except (TypeError, ValueError):
                requested_pids_limit = DEFAULT_VALIDATOR_PIDS_LIMIT
            if not 1 <= requested_pids_limit <= DEFAULT_VALIDATOR_PIDS_LIMIT:
                requested_pids_limit = DEFAULT_VALIDATOR_PIDS_LIMIT
            service_config["pids_limit"] = requested_pids_limit
            services[service_name] = service_config

        network_names = self._managed_compose_network_names(config_data)
        subnets = self._allocate_managed_subnets(
            len(network_names), seed=f"{project}:initial"
        )
        if len(subnets) == len(network_names) and network_names:
            networks = raw.get("networks")
            if not isinstance(networks, dict):
                networks = {}
            for network_name, subnet in zip(network_names, subnets, strict=True):
                existing = networks.get(network_name)
                network_config = dict(existing) if isinstance(existing, dict) else {}
                if bool(network_config.get("external")):
                    continue
                network_config["driver"] = str(network_config.get("driver") or "bridge")
                network_config["ipam"] = {"config": [{"subnet": subnet}]}
                networks[network_name] = network_config
            raw["networks"] = networks

        if ctx.trial_dir is None:
            self._release_managed_subnets(subnets)
            return None, []
        managed_dir = ctx.trial_dir / "validator"
        managed_dir.mkdir(parents=True, exist_ok=True)
        if injected_flag and flag_contract:
            self._inject_flag_into_services(
                services=services,
                managed_dir=managed_dir,
                flag=injected_flag,
                flag_contract=flag_contract,
            )
        managed_path = managed_dir / ".cage-validator.compose.yml"
        try:
            managed_path.write_text(
                yaml.safe_dump(raw, sort_keys=False),
                encoding="utf-8",
            )
        except Exception:
            self._release_managed_subnets(subnets)
            raise
        return managed_path, subnets

    def _validate_build_report(
        self, ctx: ScoringContext, ws: Path
    ) -> tuple[dict[str, Any] | None, dict[str, Score] | None]:
        report_path = ws / "build_report.json"
        if not report_path.is_file():
            return None, self._fail(
                "contract_missing_build_report",
                "No build_report.json was produced in the workspace.",
                retryable=True,
                feedback="Create the required evidence report before requesting validation.",
            )
        try:
            report = json.loads(report_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            return None, self._fail(
                "build_report_invalid",
                "build_report.json is not valid JSON.",
                retryable=True,
                evidence={"error": str(exc)},
            )
        if not isinstance(report, dict):
            return None, self._fail(
                "build_report_invalid",
                "build_report.json must contain a JSON object.",
                retryable=True,
            )
        status = str(report.get("status") or "").strip().lower()
        if status == "blocked":
            blockers = report.get("blockers") or report.get("unresolved_blockers") or []
            if not isinstance(blockers, list) or not blockers:
                return None, self._fail(
                    "build_report_invalid",
                    "A blocked build_report.json must contain at least one structured blocker.",
                    retryable=True,
                    feedback=(
                        "Set blockers to a non-empty array of objects with code, stage, "
                        "reason, evidence, and next_action."
                    ),
                )
            invalid_blockers: list[dict[str, Any]] = []
            for index, blocker in enumerate(blockers):
                if not isinstance(blocker, dict):
                    invalid_blockers.append({"index": index, "error": "not_an_object"})
                    continue
                missing = [
                    field
                    for field in ("code", "stage", "reason", "evidence", "next_action")
                    if blocker.get(field) in (None, "", [])
                ]
                if missing:
                    invalid_blockers.append({"index": index, "missing_fields": missing})
            if invalid_blockers:
                return None, self._fail(
                    "build_report_invalid",
                    "The blocked build_report.json contains incomplete blocker records.",
                    retryable=True,
                    evidence={"invalid_blockers": invalid_blockers},
                    feedback=(
                        "Each blocker needs code, stage, reason, non-empty evidence, and "
                        "next_action so the task can be routed without more blind retries."
                    ),
                )
            return None, self._fail(
                "agent_reported_blocker",
                "The builder reported that the supplied evidence cannot support a ready target.",
                retryable=False,
                evidence={
                    "blockers": blockers,
                    "build_report": str(report_path),
                },
            )
        if status != "ready":
            return None, self._fail(
                "build_report_invalid",
                "build_report.json status must be ready or blocked.",
                retryable=True,
            )

        mismatches: dict[str, dict[str, Any]] = {}
        for field in ("data_tier", "build_profile", "category_profile"):
            expected = ctx.sample.get(field)
            if expected in (None, ""):
                continue
            actual = report.get(field)
            if actual != expected:
                mismatches[field] = {"expected": expected, "actual": actual}
        if mismatches:
            return None, self._fail(
                "build_report_contract_mismatch",
                "build_report.json does not preserve the routed task contract.",
                retryable=True,
                evidence={"mismatches": mismatches},
            )

        if ctx.sample.get("category_profile") != "pwn":
            return report, None

        runtime = report.get("pwn_runtime")
        if not isinstance(runtime, dict):
            return None, self._fail(
                "pwn_runtime_report_missing",
                "A ready Pwn target must record its runtime inference.",
                retryable=True,
                feedback=(
                    "Add build_report.json.pwn_runtime with material priority, evidence, "
                    "selection basis, selected bundle, confidence, and authenticity status."
                ),
            )
        required_fields = {
            "material_priority",
            "selection_basis",
            "evidence",
            "selected_bundle",
            "confidence",
            "authenticity_status",
        }
        missing_fields = sorted(required_fields - runtime.keys())
        if missing_fields:
            return None, self._fail(
                "pwn_runtime_report_invalid",
                "The Pwn runtime report is incomplete.",
                retryable=True,
                evidence={"missing_fields": missing_fields},
            )
        invalid_fields = [
            field
            for field in (
                "material_priority",
                "selection_basis",
                "confidence",
                "authenticity_status",
            )
            if not isinstance(runtime.get(field), str) or not runtime[field].strip()
        ]
        if not isinstance(runtime.get("evidence"), list):
            invalid_fields.append("evidence")
        if invalid_fields:
            return None, self._fail(
                "pwn_runtime_report_invalid",
                "The Pwn runtime report contains empty or incorrectly typed evidence fields.",
                retryable=True,
                evidence={"invalid_fields": sorted(invalid_fields)},
            )

        expected_priority = (ctx.sample.get("pwn_material_priority") or {}).get("id")
        if expected_priority and runtime.get("material_priority") != expected_priority:
            return None, self._fail(
                "pwn_runtime_report_invalid",
                "The Pwn material priority in build_report.json is incorrect.",
                retryable=True,
                evidence={
                    "expected": expected_priority,
                    "actual": runtime.get("material_priority"),
                },
            )
        if (
            expected_priority == "attachments_only"
            and runtime.get("authenticity_status") != "unverified_until_exp"
        ):
            return None, self._fail(
                "pwn_authenticity_overclaim",
                "Attachments-only Pwn input must remain unverified until EXP validation.",
                retryable=True,
                evidence={"actual": runtime.get("authenticity_status")},
            )

        selected_bundle = runtime.get("selected_bundle")
        if selected_bundle in (None, ""):
            return report, None
        if not isinstance(selected_bundle, str):
            return None, self._fail(
                "pwn_runtime_report_invalid",
                "pwn_runtime.selected_bundle must be a string or null.",
                retryable=True,
            )

        selected_files = runtime.get("selected_files")
        if not isinstance(selected_files, dict):
            return None, self._fail(
                "pwn_runtime_files_missing",
                "A selected Pwn runtime bundle must name its copied libc and loader files.",
                retryable=True,
            )
        expected_bundle = next(
            (
                bundle
                for bundle in (ctx.sample.get("pwn_runtime") or {}).get("bundles", [])
                if bundle.get("id") == selected_bundle
            ),
            None,
        )
        if expected_bundle is None and selected_bundle not in {
            "supplied_with_challenge",
            "external_verified",
        }:
            return None, self._fail(
                "pwn_runtime_bundle_unknown",
                f"Unknown Pwn runtime bundle: {selected_bundle!r}.",
                retryable=True,
            )

        workspace_root = ws.resolve()
        file_evidence: dict[str, Any] = {}
        for role in ("libc", "loader"):
            declared = selected_files.get(role)
            if not isinstance(declared, dict):
                return None, self._fail(
                    "pwn_runtime_files_missing",
                    f"pwn_runtime.selected_files.{role} is missing.",
                    retryable=True,
                )
            try:
                relative_path = _safe_relative_path(str(declared.get("path") or ""))
            except ValueError as exc:
                return None, self._fail(
                    "pwn_runtime_files_invalid",
                    f"Invalid selected {role} path.",
                    retryable=True,
                    evidence={"error": str(exc)},
                )
            artifact_path = (ws / relative_path).resolve()
            if not artifact_path.is_relative_to(workspace_root) or not artifact_path.is_file():
                return None, self._fail(
                    "pwn_runtime_files_missing",
                    f"Selected {role} file is absent from the build context.",
                    retryable=True,
                    evidence={"path": relative_path.as_posix()},
                )
            actual_sha256 = _sha256_file(artifact_path)
            reported_sha256 = str(declared.get("sha256") or "")
            expected_sha256 = ""
            if expected_bundle is not None:
                expected_artifact = expected_bundle.get(role)
                if not isinstance(expected_artifact, dict):
                    return None, self._fail(
                        "pwn_runtime_cache_unavailable",
                        "The selected local bundle is not populated with digest evidence.",
                        retryable=False,
                    )
                expected_sha256 = str(expected_artifact.get("sha256") or "")
            if actual_sha256 != reported_sha256 or (
                expected_sha256 and actual_sha256 != expected_sha256
            ):
                return None, self._fail(
                    "pwn_runtime_digest_mismatch",
                    f"Selected {role} SHA256 does not match its runtime bundle.",
                    retryable=True,
                    evidence={
                        "path": relative_path.as_posix(),
                        "actual_sha256": actual_sha256,
                        "reported_sha256": reported_sha256,
                        "expected_sha256": expected_sha256,
                    },
                )
            file_evidence[role] = {
                "path": relative_path.as_posix(),
                "sha256": actual_sha256,
            }
        runtime["validated_selected_files"] = file_evidence
        return report, None

    def _payload_from_scores(self, scores: dict[str, Score]) -> dict[str, Any]:
        score = next(iter(scores.values()), None)
        if score is None:
            return {"passed": False, "feedback": "scorer returned no score."}
        meta = getattr(score, "metadata", {}) or {}
        exploit_result = meta.get("exploit_result")
        if not isinstance(exploit_result, dict):
            exploit_result = {}
        exploit_captured = bool(meta.get("exploit_captured"))
        exploit_passed = bool(meta.get("exploit_passed"))
        public_attempts = [
            {
                "attempt": attempt.get("attempt"),
                "captured": bool(attempt.get("captured")),
                "passed": bool(attempt.get("passed")),
                "returncode": attempt.get("returncode"),
                "error": attempt.get("error"),
                "solve_exit_clean": bool(attempt.get("solve_exit_clean")),
                "solver_outcome_class": attempt.get("solver_outcome_class"),
                "terminated_after_capture": bool(
                    attempt.get("terminated_after_capture")
                ),
                "output_limited": bool(attempt.get("output_limited")),
                "output_bytes": attempt.get("output_bytes"),
            }
            for attempt in exploit_result.get("attempts") or []
            if isinstance(attempt, dict)
        ]
        return {
            "passed": bool(meta.get("passed")),
            "value": getattr(score, "value", 0.0),
            "failure_class": meta.get("failure_class"),
            "retryable": meta.get("retryable"),
            "explanation": getattr(score, "explanation", ""),
            "feedback": meta.get("feedback") or getattr(score, "explanation", ""),
            "container_state": meta.get("container_state"),
            "container_addr": meta.get("container_addr"),
            "network_name": meta.get("network_name"),
            "targets": meta.get("targets") or [],
            "service_logs_tail": meta.get("service_logs_tail"),
            "agent_self_check_present": meta.get("agent_self_check_present"),
            "agent_service_output": meta.get("agent_service_output"),
            "retained_local_images": meta.get("retained_local_images"),
            "image_manifest": meta.get("image_manifest"),
            "validated_rehost_tier": meta.get("validated_rehost_tier"),
            "runtime_probe_results": meta.get("runtime_probe_results"),
            "runtime_probe_evidence": meta.get("runtime_probe_evidence"),
            "managed_network_retries": meta.get("managed_network_retries"),
            # Live feedback exposes only factual exploit progress. Never return
            # solver output from any replay that surfaced the private minted
            # flag, including a capture followed by a dirty non-zero exit.
            "exploit_passed": exploit_passed,
            "exploit_captured": exploit_captured,
            "exploit_returncode": exploit_result.get("returncode"),
            "exploit_attempt_count": exploit_result.get("attempt_count"),
            "exploit_max_attempts": exploit_result.get("max_attempts"),
            "exploit_successful_attempt": exploit_result.get("successful_attempt"),
            "exploit_outcome_class": exploit_result.get("outcome_class"),
            "exploit_solve_exit_clean": exploit_result.get("solve_exit_clean"),
            "exploit_solver_outcome_class": exploit_result.get(
                "solver_outcome_class"
            ),
            "exploit_attempts": public_attempts,
            "exploit_observation": exploit_result.get("observation"),
            "exploit_stdout_tail": (
                None if exploit_captured else exploit_result.get("stdout_tail")
            ),
            "exploit_stderr_tail": (
                None if exploit_captured else exploit_result.get("stderr_tail")
            ),
            "review_files": meta.get("review_files"),
            "evidence": meta.get("evidence", {}),
        }

    def _validate_runtime_probe_evidence(
        self,
        ctx: ScoringContext,
        probes: list[dict[str, Any]],
    ) -> tuple[list[dict[str, Any]] | None, dict[str, Score] | None]:
        raw_root = str(ctx.sample.get("challenge_path") or "").strip()
        materials = ctx.sample.get("materials") or {}
        if not raw_root or not isinstance(materials, dict):
            return None, self._fail(
                "runtime_probe_evidence_invalid",
                "The task does not expose immutable source material for probe provenance.",
                retryable=False,
                feedback=(
                    "R4 probes must cite supplied source or Writeup files. The task dataset "
                    "must preserve challenge_path and role-classified materials."
                ),
            )

        material_root = Path(raw_root).resolve()
        if not material_root.is_dir():
            return None, self._fail(
                "runtime_probe_evidence_invalid",
                "The task's immutable material root is unavailable.",
                retryable=False,
                evidence={"challenge_path": raw_root},
            )

        declared_roots: list[tuple[str, Path]] = []
        for role in ("writeups", "source", "deployment", "attachments"):
            role_paths = materials.get(role) or []
            if not isinstance(role_paths, list):
                continue
            for raw_path in role_paths:
                try:
                    relative = _safe_relative_path(str(raw_path))
                except ValueError:
                    continue
                declared = (material_root / relative).resolve()
                if declared == material_root or declared.is_relative_to(material_root):
                    declared_roots.append((role, declared))

        writeup_available = any(role == "writeups" for role, _ in declared_roots)
        normalized: list[dict[str, Any]] = []
        for probe in probes:
            probe_evidence: list[dict[str, Any]] = []
            cited_roles: set[str] = set()
            cited_texts: list[str] = []
            for entry in probe.get("evidence") or []:
                try:
                    relative = _safe_relative_path(str(entry.get("path") or ""))
                except ValueError as exc:
                    return None, self._fail(
                        "runtime_probe_evidence_invalid",
                        "A runtime probe cites an invalid material path.",
                        retryable=True,
                        evidence={"probe_id": probe.get("id"), "error": str(exc)},
                    )
                source_path = (material_root / relative).resolve()
                if (
                    not source_path.is_relative_to(material_root)
                    or not source_path.is_file()
                ):
                    return None, self._fail(
                        "runtime_probe_evidence_invalid",
                        "A runtime probe cites a file that is not present in the supplied material.",
                        retryable=True,
                        evidence={
                            "probe_id": probe.get("id"),
                            "path": relative.as_posix(),
                        },
                    )
                role = next(
                    (
                        candidate_role
                        for candidate_role, declared in declared_roots
                        if source_path == declared
                        or (declared.is_dir() and source_path.is_relative_to(declared))
                    ),
                    None,
                )
                if role is None:
                    return None, self._fail(
                        "runtime_probe_evidence_invalid",
                        "A runtime probe cites a file outside the role-classified task inputs.",
                        retryable=True,
                        evidence={
                            "probe_id": probe.get("id"),
                            "path": relative.as_posix(),
                        },
                    )
                cited_roles.add(role)
                try:
                    cited_texts.append(
                        source_path.read_text(encoding="utf-8", errors="replace")[
                            :_ANCHOR_MAX_EVIDENCE_BYTES
                        ]
                    )
                except OSError:
                    pass
                probe_evidence.append(
                    {
                        "path": relative.as_posix(),
                        "role": role,
                        "basis": str(entry.get("basis") or "").strip(),
                        "sha256": _sha256_file(source_path),
                    }
                )
            if writeup_available and "writeups" not in cited_roles:
                return None, self._fail(
                    "runtime_probe_evidence_invalid",
                    "A Writeup is available, but the runtime probe does not cite it.",
                    retryable=True,
                    evidence={
                        "probe_id": probe.get("id"),
                        "cited_roles": sorted(cited_roles),
                    },
                    feedback=(
                        "Derive the expected menu, page, route, or response marker from a "
                        "supplied Writeup/solve artifact and cite that file in the probe's "
                        "evidence list."
                    ),
                )
            corpus = _normalize_anchor_text("\n".join(cited_texts))
            markers = _probe_expected_markers(probe)
            anchored_marker: str | None = None
            for marker in markers:
                normalized_marker = _normalize_anchor_text(marker)
                if len(normalized_marker.replace(" ", "")) < _ANCHOR_MIN_LEN:
                    continue
                if normalized_marker and normalized_marker in corpus:
                    anchored_marker = marker
                    break
            if anchored_marker is None:
                return None, self._fail(
                    "runtime_probe_marker_unanchored",
                    "A runtime probe asserts a response marker that is absent from every "
                    "cited material file.",
                    retryable=True,
                    evidence={
                        "probe_id": probe.get("id"),
                        "expected_markers": markers,
                        "cited_paths": [item["path"] for item in probe_evidence],
                    },
                    feedback=(
                        "R4 probe assertions must be lifted from real challenge material, not "
                        "invented. Make at least one probe expectation (an HTTP "
                        "`expect_body_contains` or a TCP step's `expect_contains`) a specific "
                        "string of at least four characters that actually appears in one of the "
                        "cited Writeup/source files, then assert exactly that string. A marker "
                        "the service echoes but no supplied file mentions cannot promote R4."
                    ),
                )
            probe["content_anchor"] = {
                "marker": anchored_marker,
                "cited_paths": [item["path"] for item in probe_evidence],
            }
            probe["evidence"] = probe_evidence
            normalized.append(probe)
        return normalized, None

    def _validate_challenge_contract(
        self,
        ctx: ScoringContext,
        ws: Path,
        compose_path: Path,
        services: dict[str, Any],
    ) -> tuple[dict[str, Any] | None, dict[str, Score] | None]:
        challenge_path = ws / "challenge.json"
        if not challenge_path.is_file():
            return None, self._fail(
                "contract_missing_challenge_json",
                "No challenge.json was produced in the workspace.",
                retryable=True,
                feedback=(
                    "Produce challenge.json in the workspace root so the target can be "
                    "served later. It must declare compose_files and compose_target_services."
                ),
            )
        try:
            challenge = json.loads(challenge_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            return None, self._fail(
                "challenge_json_invalid",
                "challenge.json is not valid JSON.",
                retryable=True,
                evidence={"error": str(exc)},
                feedback=self._challenge_json_feedback(
                    ctx,
                    services=services,
                    summary="challenge.json must be valid JSON.",
                ),
            )
        if not isinstance(challenge, dict):
            return None, self._fail(
                "challenge_json_invalid",
                "challenge.json must contain a JSON object.",
                retryable=True,
                feedback=self._challenge_json_feedback(
                    ctx,
                    services=services,
                    summary="challenge.json must contain a JSON object.",
                ),
            )

        compose_files = challenge.get("compose_files")
        if not isinstance(compose_files, list) or not compose_files:
            return None, self._fail(
                "challenge_json_invalid",
                "challenge.json.compose_files must be a non-empty list.",
                retryable=True,
                feedback=self._challenge_json_feedback(
                    ctx,
                    services=services,
                    summary="challenge.json.compose_files must be a non-empty list.",
                ),
            )
        declared_compose_names = {
            Path(str(entry)).name
            for entry in compose_files
            if isinstance(entry, str) and str(entry).strip()
        }
        if compose_path.name not in declared_compose_names:
            return None, self._fail(
                "challenge_json_contract_mismatch",
                "challenge.json does not reference the produced Compose file.",
                retryable=True,
                evidence={
                    "compose_file": compose_path.name,
                    "declared_compose_files": sorted(declared_compose_names),
                },
            )

        target_services = challenge.get("compose_target_services")
        if not isinstance(target_services, list) or not target_services:
            return None, self._fail(
                "challenge_json_invalid",
                "challenge.json.compose_target_services must be a non-empty list.",
                retryable=True,
                feedback=self._challenge_json_feedback(
                    ctx,
                    services=services,
                    summary="challenge.json.compose_target_services must be a non-empty list.",
                ),
            )
        normalized_targets = []
        for service in target_services:
            if not isinstance(service, str) or not service.strip():
                return None, self._fail(
                    "challenge_json_invalid",
                    "challenge.json.compose_target_services must contain service names.",
                    retryable=True,
                    feedback=self._challenge_json_feedback(
                        ctx,
                        services=services,
                        summary="challenge.json.compose_target_services must contain Compose service names.",
                    ),
                )
            normalized_targets.append(service.strip())

        dependency_services = challenge.get("compose_dependency_services") or []
        if not isinstance(dependency_services, list):
            return None, self._fail(
                "challenge_json_invalid",
                "challenge.json.compose_dependency_services must be a list when present.",
                retryable=True,
                feedback=self._challenge_json_feedback(
                    ctx,
                    services=services,
                    summary="challenge.json.compose_dependency_services must be a list when present.",
                ),
            )
        normalized_dependencies = []
        for service in dependency_services:
            if not isinstance(service, str) or not service.strip():
                return None, self._fail(
                    "challenge_json_invalid",
                    "challenge.json.compose_dependency_services must contain service names.",
                    retryable=True,
                    feedback=self._challenge_json_feedback(
                        ctx,
                        services=services,
                        summary="challenge.json.compose_dependency_services must contain Compose service names.",
                    ),
                )
            normalized_dependencies.append(service.strip())

        unknown_services = [
            service
            for service in [*normalized_targets, *normalized_dependencies]
            if service not in services
        ]
        if unknown_services:
            return None, self._fail(
                "challenge_json_contract_mismatch",
                "challenge.json references services that do not exist in Compose.",
                retryable=True,
                evidence={"unknown_services": unknown_services},
            )

        target_ports_raw = challenge.get("target_ports") or {}
        if not isinstance(target_ports_raw, dict):
            return None, self._fail(
                "challenge_json_invalid",
                "challenge.json.target_ports must be an object when present.",
                retryable=True,
                feedback=self._challenge_json_feedback(
                    ctx,
                    services=services,
                    summary="challenge.json.target_ports must be an object keyed by Compose service name.",
                ),
            )
        target_ports: dict[str, int] = {}
        try:
            for service_name, port in target_ports_raw.items():
                target_ports[str(service_name)] = int(port)
        except (TypeError, ValueError):
            return None, self._fail(
                "challenge_json_invalid",
                "challenge.json.target_ports values must be integers.",
                retryable=True,
                feedback=self._challenge_json_feedback(
                    ctx,
                    services=services,
                    summary="challenge.json.target_ports values must be integers.",
                ),
            )
        if not target_ports and len(normalized_targets) == 1 and ctx.sample.get("internal_port"):
            target_ports[normalized_targets[0]] = int(ctx.sample["internal_port"])

        # Published host ports are an orchestration concern, not part of the
        # target contract.  Agents occasionally copy the left-hand side of a
        # Compose mapping (for example 31337:1337) into target_ports.  Resolve
        # that unambiguous mistake from the rendered Compose model before the
        # managed runtime removes all host publications.
        target_port_resolution: list[dict[str, Any]] = []
        for service_name in normalized_targets:
            service_config = services.get(service_name) or {}
            compose_ports = (
                service_config.get("ports") or []
                if isinstance(service_config, dict)
                else []
            )
            mappings: list[tuple[int, int | None]] = []
            for entry in compose_ports:
                if not isinstance(entry, dict):
                    continue
                try:
                    internal = int(entry.get("target"))
                except (TypeError, ValueError):
                    continue
                try:
                    published = int(entry.get("published"))
                except (TypeError, ValueError):
                    published = None
                mappings.append((internal, published))

            declared = target_ports.get(service_name)
            published_match = next(
                (
                    internal
                    for internal, published in mappings
                    if declared is not None
                    and published == declared
                    and internal != declared
                ),
                None,
            )
            if published_match is not None:
                target_ports[service_name] = published_match
                target_port_resolution.append(
                    {
                        "service": service_name,
                        "declared_published_port": declared,
                        "resolved_internal_port": published_match,
                        "source": "compose_port_mapping",
                    }
                )
            elif declared is None:
                internal_candidates = sorted({internal for internal, _ in mappings})
                if len(internal_candidates) == 1:
                    target_ports[service_name] = internal_candidates[0]
                    target_port_resolution.append(
                        {
                            "service": service_name,
                            "declared_published_port": None,
                            "resolved_internal_port": internal_candidates[0],
                            "source": "compose_single_internal_port",
                        }
                    )

        target_protocols_raw = challenge.get("target_port_protocols") or {}
        if not isinstance(target_protocols_raw, dict):
            return None, self._fail(
                "challenge_json_invalid",
                "challenge.json.target_port_protocols must be an object when present.",
                retryable=True,
                feedback=self._challenge_json_feedback(
                    ctx,
                    services=services,
                    summary=(
                        "challenge.json.target_port_protocols must be an object keyed by "
                        "Compose service name."
                    ),
                ),
            )
        target_protocols = {
            str(service_name): str(protocol or "tcp").strip().lower() or "tcp"
            for service_name, protocol in target_protocols_raw.items()
        }

        probe_required = _runtime_probe_required(ctx.sample)
        try:
            runtime_probes = normalize_runtime_probes(
                challenge.get("runtime_probes"),
                target_services=normalized_targets,
                target_ports=target_ports,
                target_protocols=target_protocols,
                required=probe_required,
            )
        except ProbeContractError as exc:
            if not probe_required:
                # Optional probes on an R3 task are an R4 bonus, not a gate. A
                # malformed contract must not consume the build budget or block
                # R3 admission — drop the probes and validate the build at R3.
                runtime_probes = []
            else:
                failure_class = (
                    "runtime_probe_contract_missing"
                    if challenge.get("runtime_probes") in (None, [])
                    else "runtime_probe_contract_invalid"
                )
                return None, self._fail(
                    failure_class,
                    str(exc),
                    retryable=True,
                    evidence=getattr(exc, "evidence", {}) or {},
                    feedback=(
                        f"{exc}. Declare challenge-specific HTTP/TCP assertions with "
                        "source evidence; a port-open check cannot satisfy R4."
                    ),
                )
        if runtime_probes:
            runtime_probes, probe_failure = self._validate_runtime_probe_evidence(
                ctx,
                runtime_probes,
            )
            if probe_failure is not None:
                if not probe_required:
                    runtime_probes = []
                else:
                    return None, probe_failure

        default_service = normalized_targets[0] if normalized_targets else None
        try:
            route_contract = resolve_route(ctx.sample).to_contract()
        except Exception:  # noqa: BLE001 - unroutable samples carry no route keys
            route_contract = {}

        normalized_solve = _normalize_solve_block(
            challenge.get("solve"),
            default_service=default_service,
            default_image=self._solver_image,
        )
        if normalized_solve["image"] in DEFAULT_SOLVER_IMAGE_ALIASES:
            normalized_solve["image"] = self._solver_image

        return {
            "challenge_json": challenge,
            "challenge_path": str(challenge_path),
            "target_services": normalized_targets,
            "dependency_services": normalized_dependencies,
            "target_ports": target_ports,
            "target_port_resolution": target_port_resolution,
            "target_port_protocols": target_protocols,
            "runtime_probes_required": probe_required,
            "runtime_probes": runtime_probes or [],
            "agent_network_hint": str(challenge.get("agent_network") or "").strip() or None,
            # --- R5 exploit gate (additive; read only when exploit_gate is on) ---
            "flag_contract": _normalize_flag_contract(
                challenge.get("flag_contract"), default_service=default_service
            ),
            "solve": normalized_solve,
            **route_contract,
        }, None

    def _validate_compose_runtime_policy(
        self,
        services: dict[str, Any],
        volumes: dict[str, Any] | None = None,
    ) -> tuple[dict[str, Score] | None, list[dict[str, Any]]]:
        violations: list[dict[str, Any]] = []
        for service_name, service_config in services.items():
            if not isinstance(service_config, dict):
                continue
            image_name = str(service_config.get("image") or "").strip()
            if service_config.get("build") and image_name in DEFAULT_SOLVER_IMAGE_ALIASES:
                violations.append(
                    {
                        "service": service_name,
                        "field": "protected_solver_image_build",
                        "value": image_name,
                    }
                )
            if bool(service_config.get("privileged")):
                violations.append({"service": service_name, "field": "privileged", "value": True})

            if str(service_config.get("userns_mode") or "").strip().lower() == "host":
                violations.append(
                    {"service": service_name, "field": "userns_mode", "value": "host"}
                )

            for field in ("network_mode", "pid", "ipc"):
                value = str(service_config.get(field) or "").strip().lower()
                if value == "host":
                    violations.append({"service": service_name, "field": field, "value": "host"})
                elif field in ("pid", "ipc") and (
                    value.startswith("container:") or value.startswith("service:")
                ):
                    violations.append(
                        {"service": service_name, "field": field, "value": value}
                    )

            container_name = str(service_config.get("container_name") or "").strip()
            if container_name:
                violations.append(
                    {
                        "service": service_name,
                        "field": "container_name",
                        "value": container_name,
                    }
                )

            cap_add = service_config.get("cap_add") or []
            if isinstance(cap_add, str):
                cap_values = [cap_add]
            elif isinstance(cap_add, (list, tuple, set)):
                cap_values = list(cap_add)
            else:
                cap_values = []
            forbidden_caps = list(
                dict.fromkeys(
                    normalized
                    for normalized in (
                        str(cap).strip().upper()
                        for cap in cap_values
                        if str(cap).strip()
                    )
                    if normalized in _FORBIDDEN_CAP_ADD
                )
            )
            if forbidden_caps:
                violations.append(
                    {
                        "service": service_name,
                        "field": "cap_add",
                        "value": forbidden_caps,
                    }
                )

            security_opt = service_config.get("security_opt") or []
            if isinstance(security_opt, str):
                security_values = [security_opt]
            elif isinstance(security_opt, (list, tuple, set)):
                security_values = list(security_opt)
            else:
                security_values = []
            forbidden_security_opts = list(
                dict.fromkeys(
                    normalized
                    for normalized in (
                        _normalize_security_opt(opt)
                        for opt in security_values
                        if str(opt).strip()
                    )
                    if normalized in _FORBIDDEN_SECURITY_OPTS
                )
            )
            if forbidden_security_opts:
                violations.append(
                    {
                        "service": service_name,
                        "field": "security_opt",
                        "value": forbidden_security_opts,
                    }
                )

            devices = service_config.get("devices") or []
            if devices:
                violations.append(
                    {
                        "service": service_name,
                        "field": "devices",
                        "value": devices,
                    }
                )

            for volume in service_config.get("volumes") or []:
                if isinstance(volume, dict):
                    volume_type = str(volume.get("type") or "").strip().lower()
                    source = str(volume.get("source") or "").strip()
                    target = str(volume.get("target") or "").strip()
                    is_bind_mount = volume_type == "bind"
                else:
                    volume_type = ""
                    volume_spec = str(volume).strip()
                    parts = volume_spec.split(":")
                    source = parts[0].strip() if len(parts) >= 2 else ""
                    target = parts[1].strip() if len(parts) >= 2 else ""
                    is_bind_mount = bool(
                        source
                        and (
                            source.startswith("/")
                            or source.startswith("./")
                            or source.startswith("../")
                            or source.startswith("~/")
                        )
                    )
                if "docker.sock" in source or "docker.sock" in target:
                    violations.append(
                        {
                            "service": service_name,
                            "field": "docker_socket_mount",
                            "value": {"source": source, "target": target},
                        }
                    )
                elif is_bind_mount:
                    violations.append(
                        {
                            "service": service_name,
                            "field": "bind_mount",
                            "value": {"source": source, "target": target},
                        }
                    )

        # A named top-level volume can smuggle a host bind mount past the
        # per-service check via driver_opts (`type: none, o: bind, device: /host`
        # or any absolute-path device), so scan the declared volumes too.
        for volume_name, volume_config in (volumes or {}).items():
            if not isinstance(volume_config, dict):
                continue
            driver_opts = volume_config.get("driver_opts") or {}
            if not isinstance(driver_opts, dict):
                continue
            device = str(driver_opts.get("device") or "").strip()
            opt = str(driver_opts.get("o") or "").lower()
            opt_type = str(driver_opts.get("type") or "").strip().lower()
            if device.startswith("/") and ("bind" in opt or opt_type in ("", "none")):
                field = (
                    "docker_socket_volume"
                    if "docker.sock" in device
                    else "host_bind_volume"
                )
                violations.append(
                    {
                        "volume": volume_name,
                        "field": field,
                        "value": {"device": device, "o": opt or None},
                    }
                )

        if violations:
            return (
                self._fail(
                    "compose_runtime_unsafe",
                    "The Compose model requests forbidden runtime privileges, host mounts, "
                    "or a protected harness image tag.",
                    retryable=True,
                    evidence={"violations": violations},
                    feedback=self._runtime_policy_feedback(),
                ),
                violations,
            )
        return None, violations

    def _load_workspace_contract(
        self,
        ctx: ScoringContext,
    ) -> tuple[dict[str, Any] | None, dict[str, Score] | None]:
        if ctx.trial_dir is None:
            return None, self._fail(
                "no_workspace", "No trial_dir available for scoring.", retryable=False
            )
        ws = ctx.trial_dir / "workspace"
        if not ws.is_dir():
            return None, self._fail(
                "no_workspace", f"Agent workspace snapshot not found at {ws}.", retryable=False
            )

        build_report, report_failure = self._validate_build_report(ctx, ws)
        if report_failure is not None:
            return None, report_failure

        compose_path = next((ws / n for n in _COMPOSE_NAMES if (ws / n).is_file()), None)
        if compose_path is None:
            return None, self._fail(
                "contract_missing_compose",
                "No docker-compose.yml produced in the workspace.",
                retryable=True,
                feedback=(
                    "You did not produce a docker-compose.yml in your workspace root. "
                    "Write one that builds the target and declares its internal service port."
                ),
            )

        expected_images = [
            str(name).strip() for name in (ctx.sample.get("image_names") or []) if str(name).strip()
        ]
        if not expected_images:
            singular_image = str(ctx.sample.get("image_name") or "").strip()
            if singular_image:
                expected_images = [singular_image]
        if not expected_images:
            return None, self._fail(
                "contract_missing_image_name",
                "No archival image name was declared for this task.",
                retryable=False,
                feedback=(
                    "The task must declare image_name/image_names. Each expected image must "
                    "be attached to a Compose service with a build section."
                ),
            )

        compose_config = _run(
            [
                "docker",
                "compose",
                "-p",
                "buildcheck_contract",
                "-f",
                str(compose_path),
                "config",
                "--format",
                "json",
            ],
            cwd=ws,
            timeout=60,
        )
        if compose_config.returncode != 0:
            return None, self._fail(
                "compose_config_invalid",
                "docker compose config failed.",
                retryable=True,
                evidence={
                    "returncode": compose_config.returncode,
                    "stderr_tail": _tail(compose_config.stderr),
                },
            )
        try:
            config_data = json.loads(compose_config.stdout or "{}")
        except json.JSONDecodeError as exc:
            return None, self._fail(
                "compose_config_invalid",
                "docker compose config did not return valid JSON.",
                retryable=True,
                evidence={"error": str(exc), "stdout_tail": _tail(compose_config.stdout)},
            )

        services = config_data.get("services") or {}
        challenge_contract, challenge_failure = self._validate_challenge_contract(
            ctx, ws, compose_path, services
        )
        if challenge_failure is not None:
            return None, challenge_failure

        runtime_policy_failure, _violations = self._validate_compose_runtime_policy(
            services, config_data.get("volumes") or {}
        )
        if runtime_policy_failure is not None:
            return None, runtime_policy_failure

        build_services_by_image: dict[str, list[str]] = {}
        for service_name, service_config in services.items():
            if not isinstance(service_config, dict) or not service_config.get("build"):
                continue
            image_name = str(service_config.get("image") or "").strip()
            if image_name:
                build_services_by_image.setdefault(image_name, []).append(str(service_name))
        missing_build_images = [
            image for image in expected_images if image not in build_services_by_image
        ]
        if missing_build_images:
            return None, self._fail(
                "image_contract_mismatch",
                "The archival image contract is not backed by Compose build services.",
                retryable=True,
                evidence={
                    "expected_images": expected_images,
                    "build_services_by_image": build_services_by_image,
                    "missing_images": missing_build_images,
                },
                feedback=(
                    "Add each declared image_name to the appropriate Compose service's image "
                    "field and keep that service's build section."
                ),
            )

        return {
            "workspace": ws,
            "compose_path": compose_path,
            "build_report": build_report,
            "expected_images": expected_images,
            "config_data": config_data,
            "services": services,
            "build_services_by_image": build_services_by_image,
            **(challenge_contract or {}),
        }, None

    def _collect_service_logs(
        self,
        *,
        project: str,
        compose_files: list[Path],
        workspace: Path,
    ) -> str:
        logs = _run(
            [
                *self._compose_args(
                    project=project,
                    compose_files=compose_files,
                    project_directory=workspace,
                ),
                "logs",
                "--no-color",
                "--tail",
                "300",
            ],
            cwd=workspace,
            timeout=60,
        )
        return ((logs.stdout or "") + (logs.stderr or "")).strip()

    def _collect_image_evidence(
        self,
        *,
        expected_images: list[str],
        build_services_by_image: dict[str, list[str]],
    ) -> tuple[list[dict[str, Any]] | None, dict[str, Score] | None]:
        image_evidence: list[dict[str, Any]] = []
        for image_name in expected_images:
            inspected = _run(
                [
                    "docker",
                    "image",
                    "inspect",
                    image_name,
                    "--format",
                    "{{json .}}",
                ],
                timeout=60,
            )
            if inspected.returncode != 0:
                return None, self._fail(
                    "image_missing_after_build",
                    f"Expected local image was not present after build: {image_name}",
                    retryable=True,
                    evidence={
                        "image": image_name,
                        "stderr_tail": _tail(inspected.stderr),
                    },
                )
            try:
                raw_image = json.loads(inspected.stdout or "{}")
            except json.JSONDecodeError as exc:
                return None, self._fail(
                    "image_inspect_invalid",
                    f"Could not decode image metadata for {image_name}.",
                    retryable=True,
                    evidence={"image": image_name, "error": str(exc)},
                )
            image_evidence.append(
                {
                    "name": image_name,
                    "services": build_services_by_image[image_name],
                    "image_id": raw_image.get("Id"),
                    "repo_tags": raw_image.get("RepoTags") or [],
                    "repo_digests": raw_image.get("RepoDigests") or [],
                    "created": raw_image.get("Created"),
                    "size": raw_image.get("Size"),
                }
            )
        return image_evidence, None

    def _write_image_manifest(
        self,
        *,
        trial_dir: Path,
        trial_id: str,
        filename: str,
        image_evidence: list[dict[str, Any]],
    ) -> tuple[str | None, dict[str, Score] | None]:
        image_manifest_path = trial_dir / filename
        image_manifest = {
            "schema_version": "cage-build-target-image-manifest-v1",
            "trial_id": trial_id,
            "retained_locally": True,
            "images": image_evidence,
        }
        try:
            image_manifest_path.parent.mkdir(parents=True, exist_ok=True)
            image_manifest_path.write_text(
                json.dumps(image_manifest, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
        except OSError as exc:
            return None, self._fail(
                "image_manifest_write_failed",
                "Built images could not be recorded in the trial artifact.",
                retryable=False,
                evidence={"error": str(exc)},
            )
        return str(image_manifest_path), None

    def _write_runtime_probe_evidence(
        self,
        *,
        trial_dir: Path,
        trial_id: str,
        filename: str,
        results: dict[str, Any],
    ) -> tuple[str | None, dict[str, Score] | None]:
        evidence_path = trial_dir / filename
        payload = {
            **results,
            "trial_id": trial_id,
            "validator": "cage-host-side",
        }
        try:
            evidence_path.parent.mkdir(parents=True, exist_ok=True)
            evidence_path.write_text(
                json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
                encoding="utf-8",
            )
        except OSError as exc:
            return None, self._fail(
                "runtime_probe_evidence_write_failed",
                "Runtime probe evidence could not be retained.",
                retryable=False,
                evidence={"error": str(exc)},
            )
        return str(evidence_path), None

    def _choose_network(
        self,
        target_inspects: list[dict[str, Any]],
        *,
        hint: str | None,
    ) -> str | None:
        network_names = []
        for inspect_data in target_inspects:
            networks = (
                inspect_data.get("NetworkSettings", {}).get("Networks", {}) if inspect_data else {}
            )
            network_names.append(set(networks.keys()))
        if not network_names:
            return None
        if hint:
            for candidate in sorted(set.union(*network_names)):
                if candidate == hint or candidate.endswith(f"_{hint}"):
                    if all(candidate in names for names in network_names):
                        return candidate
        common = set.intersection(*network_names) if network_names else set()
        if common:
            return sorted(common)[0]
        first = next(iter(network_names[0]), None)
        return first

    def _connect_agent_to_network(
        self,
        *,
        network_name: str,
        agent_container: str,
    ) -> tuple[bool, str]:
        result = _run(
            ["docker", "network", "connect", network_name, agent_container],
            timeout=60,
        )
        if result.returncode == 0:
            return True, ""
        stderr = (result.stderr or "").lower()
        if "already exists" in stderr or "endpoint with name" in stderr:
            return True, ""
        return False, result.stderr or result.stdout or "docker network connect failed"

    def _disconnect_agent_from_network(
        self,
        *,
        network_name: str,
        agent_container: str,
    ) -> None:
        _run(
            ["docker", "network", "disconnect", "-f", network_name, agent_container],
            timeout=60,
        )

    def _compose_down(
        self,
        *,
        project: str,
        compose_files: list[Path],
        workspace: Path,
    ) -> None:
        _run(
            [
                *self._compose_args(
                    project=project,
                    compose_files=compose_files,
                    project_directory=workspace,
                ),
                "down",
                "-v",
                "--remove-orphans",
            ],
            cwd=workspace,
            timeout=120,
        )

    def _inspect_exploit_target_stack(
        self,
        *,
        project: str,
        compose_files: list[Path],
        workspace: Path,
        target_services: list[str],
        target_ports: dict[str, Any],
        target_port_protocols: dict[str, Any],
        network_hint: str | None,
    ) -> dict[str, Any]:
        """Resolve one newly-created target stack for a single R5 attempt.

        R5 retries must not inherit process, heap, VM, or volume state from an
        earlier exploit.  This helper records the concrete container IDs and
        endpoint after each recreation so the evidence proves that attempts
        really used distinct target instances.
        """

        service_cids: dict[str, str] = {}
        for service_name in target_services:
            ps = _run(
                [
                    *self._compose_args(
                        project=project,
                        compose_files=compose_files,
                        project_directory=workspace,
                    ),
                    "ps",
                    "-q",
                    service_name,
                ],
                cwd=workspace,
                timeout=60,
            )
            cid = next(
                (
                    line.strip()
                    for line in (ps.stdout or "").splitlines()
                    if line.strip()
                ),
                "",
            )
            if not cid:
                return {
                    "ok": False,
                    "error": "target_recreate_no_container",
                    "detail": (
                        f"Compose did not produce target service {service_name!r}: "
                        f"{_tail(ps.stderr or ps.stdout, 1200)}"
                    ),
                    "service_logs": "",
                }
            service_cids[service_name] = cid

        time.sleep(_SETTLE_SECONDS)
        service_logs = self._collect_service_logs(
            project=project,
            compose_files=compose_files,
            workspace=workspace,
        )
        inspect_map: dict[str, dict[str, Any]] = {}
        states: dict[str, str] = {}
        for service_name, cid in service_cids.items():
            inspected = _run(
                ["docker", "inspect", "--format", "{{json .}}", cid],
                timeout=30,
            )
            if inspected.returncode != 0:
                return {
                    "ok": False,
                    "error": "target_recreate_inspect_failed",
                    "detail": _tail(inspected.stderr or inspected.stdout, 1200),
                    "service_logs": service_logs,
                }
            try:
                inspect_data = json.loads(inspected.stdout or "{}")
            except json.JSONDecodeError as exc:
                return {
                    "ok": False,
                    "error": "target_recreate_inspect_invalid",
                    "detail": str(exc),
                    "service_logs": service_logs,
                }
            inspect_map[service_name] = inspect_data
            state = inspect_data.get("State", {}) or {}
            status = str(state.get("Status") or "unknown")
            states[service_name] = status
            if status != "running":
                return {
                    "ok": False,
                    "error": "target_recreate_service_not_running",
                    "detail": (
                        f"Target service {service_name!r} is {status!r} after "
                        f"recreation. Logs: {_tail(service_logs, 1200)}"
                    ),
                    "service_logs": service_logs,
                    "states": states,
                }

        target_inspects = [inspect_map[name] for name in target_services]
        network_name = self._choose_network(target_inspects, hint=network_hint)
        targets: list[dict[str, Any]] = []
        for service_name in target_services:
            inspect_data = inspect_map[service_name]
            networks = inspect_data.get("NetworkSettings", {}).get("Networks", {}) or {}
            ip_addr = ""
            if network_name and network_name in networks:
                ip_addr = str(networks[network_name].get("IPAddress") or "")
            elif networks:
                first_network = next(iter(networks.values()))
                ip_addr = str(first_network.get("IPAddress") or "")
            targets.append(
                {
                    "service_name": service_name,
                    "container_id": service_cids[service_name],
                    "container_addr": ip_addr or None,
                    "internal_port": target_ports.get(service_name),
                    "protocol": target_port_protocols.get(service_name, "tcp"),
                }
            )

        if not network_name or not any(
            target.get("container_addr") and target.get("internal_port") is not None
            for target in targets
        ):
            return {
                "ok": False,
                "error": "target_recreate_endpoint_unresolved",
                "detail": "The recreated target has no player-reachable network endpoint.",
                "service_logs": service_logs,
                "states": states,
                "targets": targets,
                "network_name": network_name,
            }

        return {
            "ok": True,
            "service_cids": service_cids,
            "service_logs": service_logs,
            "states": states,
            "network_name": network_name,
            "targets": targets,
            "container_addr": next(
                (
                    str(target.get("container_addr"))
                    for target in targets
                    if target.get("container_addr")
                ),
                None,
            ),
        }

    def _start_fresh_exploit_target(
        self,
        *,
        ctx: ScoringContext,
        project: str,
        workspace: Path,
        compose_path: Path,
        config_data: dict[str, Any],
        target_services: list[str],
        target_ports: dict[str, Any],
        target_port_protocols: dict[str, Any],
        network_hint: str | None,
        flag: str,
        flag_contract: dict[str, Any],
    ) -> dict[str, Any]:
        """Create a clean target container set without rebuilding its image."""

        managed_compose_path, pending_subnets = self._write_managed_runtime_compose(
            ctx=ctx,
            project=project,
            workspace=workspace,
            compose_path=compose_path,
            config_data=config_data,
            injected_flag=flag,
            flag_contract=flag_contract,
        )
        base_compose_path = managed_compose_path or compose_path
        compose_files = [base_compose_path]
        network_retry_count = 0
        auto_managed_network = bool(pending_subnets)

        while True:
            try:
                up = _run(
                    [
                        *self._compose_args(
                            project=project,
                            compose_files=compose_files,
                            project_directory=workspace,
                        ),
                        "up",
                        "-d",
                        "--no-build",
                        "--force-recreate",
                        "--renew-anon-volumes",
                    ],
                    cwd=workspace,
                    timeout=self._build_timeout,
                )
            except subprocess.TimeoutExpired:
                return {
                    "ok": False,
                    "error": "target_recreate_timeout",
                    "detail": "docker compose up --no-build timed out",
                    "compose_files": compose_files,
                    "managed_network_retries": network_retry_count,
                }
            finally:
                self._release_managed_subnets(pending_subnets)
                pending_subnets = []

            network_conflict = self._is_address_pool_exhaustion(up.stderr or "")
            if up.returncode == 0 or not network_conflict:
                break
            if network_retry_count >= _MAX_MANAGED_NETWORK_RETRIES:
                break

            next_retry_index = network_retry_count + 1
            override_path, pending_subnets = self._write_managed_network_override(
                ctx=ctx,
                project=project,
                config_data=config_data,
                retry_index=next_retry_index,
            )
            if override_path is None:
                break
            network_retry_count = next_retry_index
            self._compose_down(
                project=project,
                compose_files=compose_files,
                workspace=workspace,
            )
            compose_files = [base_compose_path, override_path]
            auto_managed_network = True

        if up.returncode != 0:
            return {
                "ok": False,
                "error": (
                    "target_recreate_network_exhausted"
                    if auto_managed_network and network_conflict
                    else "target_recreate_failed"
                ),
                "detail": _tail(up.stderr or up.stdout, 1600),
                "returncode": up.returncode,
                "compose_files": compose_files,
                "managed_network_retries": network_retry_count,
            }

        inspected = self._inspect_exploit_target_stack(
            project=project,
            compose_files=compose_files,
            workspace=workspace,
            target_services=target_services,
            target_ports=target_ports,
            target_port_protocols=target_port_protocols,
            network_hint=network_hint,
        )
        inspected["compose_files"] = compose_files
        inspected["managed_network_retries"] = network_retry_count
        return inspected

    def _pass(
        self,
        *,
        ctx: ScoringContext,
        compose_path: Path,
        container_state: str,
        container_addr: str | None,
        network_name: str | None,
        targets: list[dict[str, Any]],
        service_logs: str,
        agent_service_output: str,
        build_report: dict[str, Any] | None,
        image_evidence: list[dict[str, Any]],
        image_manifest: str | None,
        validated_rehost_tier: str,
        runtime_probe_results: dict[str, Any] | None,
        runtime_probe_evidence: str | None,
        review_files: dict[str, Any],
        exploit_result: dict[str, Any] | None = None,
        exploit_checkpoint_required: bool = False,
        managed_network_retries: int = 0,
    ) -> dict[str, Score]:
        score_metadata = {
            "compose_file": compose_path.name,
            "container_state": container_state,
            "container_addr": container_addr,
            "network_name": network_name,
            "targets": targets,
            "service_logs_tail": _tail(service_logs, 1500),
            "agent_self_check_present": bool(agent_service_output),
            "agent_service_output": agent_service_output,
            "build_report": str(
                (ctx.trial_dir or Path(".")) / "workspace" / "build_report.json"
            ),
            "pwn_runtime_evidence": (
                build_report.get("pwn_runtime") if build_report else None
            ),
            "retained_local_images": image_evidence,
            "image_manifest": image_manifest,
            "validated_rehost_tier": validated_rehost_tier,
            "runtime_probe_results": runtime_probe_results,
            "runtime_probe_evidence": runtime_probe_evidence,
            "exploit_passed": bool((exploit_result or {}).get("passed")),
            "exploit_captured": bool((exploit_result or {}).get("captured")),
            "exploit_result": exploit_result,
            "review_files": review_files,
            "managed_network_retries": managed_network_retries,
        }
        if exploit_checkpoint_required and validated_rehost_tier != "R5":
            observation = str((exploit_result or {}).get("observation") or "").strip()
            if not observation:
                observation = (
                    "No runnable solve entry was available for the independent "
                    "exploit-capture replay."
                )
            explanation = (
                f"Agent target built and stayed up through {validated_rehost_tier}, "
                "but this route requires independent R5 exploit capture."
            )
            score_metadata.update(
                {
                    "passed": False,
                    "failure_class": "exploit_capture_not_passed",
                    "retryable": True,
                    "feedback": (
                        f"BUILD/RUNTIME CHECKPOINT PASS through "
                        f"{validated_rehost_tier}; EXPLOIT_CAPTURE CHECKPOINT FAIL. "
                        f"{observation}"
                    ),
                    "evidence": {
                        "validated_rehost_tier": validated_rehost_tier,
                        "exploit_observation": observation,
                        "exploit_evidence": (exploit_result or {}).get("evidence"),
                    },
                }
            )
            return {
                "build_target": Score(
                    value=0.0,
                    answer=f"validated through {validated_rehost_tier}; R5 required",
                    explanation=explanation,
                    metadata=score_metadata,
                )
            }

        if validated_rehost_tier == "R5":
            tier_note = (
                "The intended exploit captured the exact freshly-minted flag from a "
                "clean instance — the rebuilt target is faithfully exploitable. Solver "
                "exit hygiene is recorded separately and does not change environment R5."
            )
        elif validated_rehost_tier == "R4":
            tier_note = "Independent challenge-specific runtime probes passed."
        else:
            tier_note = "No R4 semantic probe was required for this task."
        return {
            "build_target": Score(
                value=1.0,
                answer=f"validated through {validated_rehost_tier}",
                explanation="Agent target built and stayed up. " + tier_note,
                metadata={
                    **score_metadata,
                    "passed": True,
                    "failure_class": None,
                    "retryable": False,
                },
            )
        }

    @staticmethod
    def _exploit_observation(
        *,
        passed: bool,
        captured: bool,
        rc: int | None,
        host: str,
        port: Any,
        combined: str,
        error: str | None,
        solve_exit_clean: bool,
        solver_outcome_class: str,
        attempt_count: int,
        max_attempts: int,
        successful_attempt: int | None,
    ) -> str:
        """Factual, attribution-neutral summary of an R5 replay series."""
        if passed:
            hygiene = (
                "The solver also exited cleanly (rc=0)."
                if solve_exit_clean
                else (
                    "The environment is R5 because exact capture is authoritative; "
                    f"solver hygiene is recorded separately as {solver_outcome_class!r}."
                )
            )
            return (
                f"Attempt {successful_attempt}/{max_attempts} of the committed exploit "
                f"captured the exact minted flag from the live target at {host}:{port}. "
                f"The rebuilt (environment, exploit) pair is consistent. {hygiene}"
            )
        if error == "output_limit":
            capture_note = " after emitting the minted flag" if captured else ""
            return (
                f"None of {attempt_count}/{max_attempts} committed exploit attempt(s) "
                f"completed cleanly against {host}:{port}; the selected solver exceeded "
                f"the bounded output contract{capture_note} and was stopped. This is "
                "solver-process behavior, not evidence that the target failed to boot."
            )
        if error == "timeout":
            return (
                f"None of {attempt_count}/{max_attempts} committed exploit attempt(s) "
                f"captured the minted flag from {host}:{port}; the selected attempt did "
                "not return within its budget. Repeated timeouts still do not by "
                "themselves attribute the gap to the environment or the exploit."
            )
        if error and error.startswith("target_recreate"):
            return (
                f"None of {attempt_count}/{max_attempts} isolated exploit attempt(s) "
                "captured the minted flag; the selected attempt could not prepare a "
                f"fresh target instance ({error})."
            )
        tail = combined.strip().replace("\n", " ")[-300:]
        return (
            f"None of {attempt_count}/{max_attempts} committed exploit attempt(s) captured "
            f"the minted flag from {host}:{port}; the selected attempt exited rc={rc}. "
            + (f"Last output: {tail!r}. " if tail else "No output was produced. ")
            + "A missed (environment, exploit) pair is not attributed to one side from "
            "these replays alone."
        )

    def _run_exploit_validation(
        self,
        *,
        ws: Path,
        network_name: str | None,
        targets: list[dict[str, Any]],
        solve: dict[str, Any],
        flag: str,
        review_dir: Path,
        check_label: str,
        prepare_attempt: Callable[[int], dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        """R5 gate: replay ``solve/`` a bounded number of times from a player vantage.

        ``prepare_attempt`` recreates and re-flags the target before each solver
        invocation in the authoritative scorer path.  Keeping it optional makes
        this primitive independently testable, but production R5 validation must
        supply it. Each solver runs read-only and the environment gate passes as
        soon as one attempt emits that attempt's exact minted flag. Exit status
        and post-capture behavior are retained as separate solver-hygiene data.
        """
        service = str(solve.get("service") or "").strip()
        solve_dir = ws / "solve"
        if not solve_dir.is_dir():
            return {
                "passed": False,
                "captured": False,
                "attempt_count": 0,
                "max_attempts": self._exploit_attempts,
                "successful_attempt": None,
                "attempts": [],
                "observation": "R5 skipped: no solve/ directory committed.",
                "error": "no_solve_dir",
            }

        requested_image = str(solve.get("image") or self._solver_image)
        image = (
            self._solver_image
            if requested_image in DEFAULT_SOLVER_IMAGE_ALIASES
            else requested_image
        )
        entry = str(solve.get("entry") or "").strip()
        attempts: list[dict[str, Any]] = []
        successful_attempt: int | None = None
        for attempt_number in range(1, self._exploit_attempts + 1):
            prepared: dict[str, Any] = {
                "ok": True,
                "network_name": network_name,
                "targets": targets,
                "flag": flag,
                "fresh_target": False,
            }
            if prepare_attempt is not None:
                try:
                    candidate = prepare_attempt(attempt_number)
                    if not isinstance(candidate, dict):
                        raise TypeError("prepare_attempt must return an object")
                    prepared = candidate
                except Exception as exc:  # noqa: BLE001 - preserve validator evidence
                    prepared = {
                        "ok": False,
                        "error": "target_recreate_exception",
                        "detail": f"{type(exc).__name__}: {exc}",
                        "fresh_target": True,
                    }

            attempt_network = str(prepared.get("network_name") or "")
            attempt_targets = prepared.get("targets") or []
            attempt_flag = str(prepared.get("flag") or "")
            target = next(
                (
                    target
                    for target in attempt_targets
                    if target.get("service_name") == service
                    and target.get("container_addr")
                ),
                None,
            ) or next(
                (
                    target
                    for target in attempt_targets
                    if target.get("container_addr")
                ),
                None,
            )
            target_instance = dict(prepared.get("target_instance") or {})
            target_instance.setdefault(
                "fresh",
                bool(prepared.get("fresh_target") or prepare_attempt is not None),
            )
            target_instance.setdefault("network_name", attempt_network or None)
            target_instance.setdefault(
                "container_ids",
                [
                    str(item.get("container_id"))
                    for item in attempt_targets
                    if item.get("container_id")
                ],
            )
            if attempt_flag:
                target_instance.setdefault(
                    "flag_fingerprint",
                    hashlib.sha256(attempt_flag.encode("utf-8")).hexdigest()[:16],
                )

            preparation_error = str(prepared.get("error") or "").strip()
            if prepared.get("ok") is False or preparation_error:
                detail = str(prepared.get("detail") or preparation_error)
                attempts.append(
                    {
                        "attempt": attempt_number,
                        "captured": False,
                        "passed": False,
                        "returncode": None,
                        "error": preparation_error or "target_recreate_failed",
                        "stdout_tail": "",
                        "stderr_tail": _tail(detail, 2000),
                        "target": None,
                        "target_instance": target_instance,
                    }
                )
                continue

            if target is None or not attempt_network or not attempt_flag:
                attempts.append(
                    {
                        "attempt": attempt_number,
                        "captured": False,
                        "passed": False,
                        "returncode": None,
                        "error": "target_recreate_endpoint_unresolved",
                        "stdout_tail": "",
                        "stderr_tail": "Fresh target endpoint or flag was unresolved.",
                        "target": None,
                        "target_instance": target_instance,
                    }
                )
                continue

            host = str(target.get("container_addr"))
            port = target.get("internal_port")
            solver_container_name = f"cage-build-target-solver-{uuid.uuid4().hex[:12]}"
            cmd = [
                "docker", "run", "--rm",
                "--name", solver_container_name,
                "--network", attempt_network,
                "-e", "TERM=xterm",
                "-e", "PYTHONUNBUFFERED=1",
                "-e", f"TARGET_HOST={host}",
                "-e", f"TARGET_PORT={port if port is not None else ''}",
                # ``--volume host:container:ro`` is ambiguous when the run path
                # contains ":" (agent labels do). Long mount syntax keeps such
                # paths valid.
                "--mount", f"type=bind,src={solve_dir.resolve()},dst=/solve,readonly",
                "-w", "/solve",
                image, "sh", "-c", entry,
            ]
            error: str | None = None
            proc, timed_out = _run_managed_solver_sidecar(
                cmd,
                container_name=solver_container_name,
                timeout=self._exploit_timeout,
                success_marker=attempt_flag.encode("utf-8"),
            )
            stdout, stderr = proc.stdout or "", proc.stderr or ""
            rc = proc.returncode
            output_limited = bool(getattr(proc, "output_limited", False))
            terminated_after_capture = bool(
                getattr(proc, "terminated_after_capture", False)
            )
            if output_limited:
                error = "output_limit"
                rc = None
                output_note = (
                    "solver exceeded the bounded output contract "
                    f"({_SOLVER_OUTPUT_LIMIT_BYTES} bytes)"
                )
                stderr = f"{stderr}\n{output_note}".strip()
            elif timed_out:
                error = "timeout"
                rc = None
                timeout_note = f"solver exceeded {self._exploit_timeout}s"
                stderr = f"{stderr}\n{timeout_note}".strip()
            combined = f"{stdout}\n{stderr}"
            captured = bool(getattr(proc, "marker_seen", False)) or attempt_flag in combined
            passed = captured
            solve_exit_clean = bool(
                captured
                and rc == 0
                and not timed_out
                and not output_limited
                and not terminated_after_capture
            )
            if solve_exit_clean:
                solver_outcome_class = "clean_exit"
            elif captured and terminated_after_capture:
                solver_outcome_class = "terminated_after_capture"
            elif captured and output_limited:
                solver_outcome_class = "output_limited_after_capture"
            elif captured and timed_out:
                solver_outcome_class = "timeout_after_capture"
            elif captured:
                solver_outcome_class = "dirty_exit"
            elif output_limited:
                solver_outcome_class = "output_limited_without_capture"
            elif timed_out:
                solver_outcome_class = "timeout_without_capture"
            else:
                solver_outcome_class = "exited_without_capture"
            attempts.append(
                {
                    "attempt": attempt_number,
                    "captured": captured,
                    "passed": passed,
                    "returncode": rc,
                    "error": error,
                    "solve_exit_clean": solve_exit_clean,
                    "solver_outcome_class": solver_outcome_class,
                    "terminated_after_capture": terminated_after_capture,
                    "output_limited": output_limited,
                    "output_bytes": getattr(proc, "output_bytes", None),
                    "stdout_tail": _tail(stdout, 4000),
                    "stderr_tail": _tail(stderr, 2000),
                    "target": {
                        "service": target.get("service_name"),
                        "host": host,
                        "port": port,
                    },
                    "target_instance": target_instance,
                }
            )
            if passed:
                successful_attempt = attempt_number
                break

        passed = successful_attempt is not None
        captured = any(bool(attempt.get("captured")) for attempt in attempts)
        if successful_attempt == 1:
            outcome_class = "first_attempt_pass"
        elif successful_attempt is not None:
            outcome_class = "retry_rescued_pass"
        else:
            outcome_class = "not_passed"
        # On failure, prefer an attempt that reached the flag so the observation
        # exposes a dirty exit contract; otherwise the last attempt is the most
        # useful failure snapshot. On success, select the successful attempt.
        if successful_attempt is not None:
            selected = attempts[successful_attempt - 1]
        else:
            selected = next(
                (attempt for attempt in reversed(attempts) if attempt.get("captured")),
                attempts[-1],
            )
        rc = selected.get("returncode")
        error = selected.get("error")
        solve_exit_clean = bool(selected.get("solve_exit_clean"))
        solver_outcome_class = str(
            selected.get("solver_outcome_class") or "not_run"
        )
        stdout_tail = str(selected.get("stdout_tail") or "")
        stderr_tail = str(selected.get("stderr_tail") or "")
        combined = f"{stdout_tail}\n{stderr_tail}"
        selected_target = selected.get("target") or {}
        host = str(selected_target.get("host") or "<unresolved>")
        port = selected_target.get("port")
        observation = self._exploit_observation(
            passed=passed,
            captured=captured,
            rc=rc,
            host=host,
            port=port,
            combined=combined,
            error=error,
            solve_exit_clean=solve_exit_clean,
            solver_outcome_class=solver_outcome_class,
            attempt_count=len(attempts),
            max_attempts=self._exploit_attempts,
            successful_attempt=successful_attempt,
        )

        evidence = {
            "passed": passed,
            "captured": captured,
            "attempt_count": len(attempts),
            "max_attempts": self._exploit_attempts,
            "successful_attempt": successful_attempt,
            "outcome_class": outcome_class,
            "solve_exit_clean": solve_exit_clean,
            "solver_outcome_class": solver_outcome_class,
            "entry": entry,
            "image": image,
            "target": selected_target or None,
            "fresh_target_per_attempt": prepare_attempt is not None,
            "distinct_target_instances": len(
                {
                    tuple(
                        str(container_id)
                        for container_id in (
                            attempt.get("target_instance", {}).get("container_ids") or []
                        )
                    )
                    for attempt in attempts
                    if attempt.get("target_instance", {}).get("container_ids")
                }
            ),
            "distinct_flag_fingerprints": len(
                {
                    str(attempt.get("target_instance", {}).get("flag_fingerprint"))
                    for attempt in attempts
                    if attempt.get("target_instance", {}).get("flag_fingerprint")
                }
            ),
            "returncode": rc,
            "error": error,
            "stdout_tail": stdout_tail,
            "stderr_tail": stderr_tail,
            "attempts": attempts,
        }
        filename = (
            "exploit_evidence.json"
            if check_label == "score"
            else f"{check_label}-exploit_evidence.json"
        )
        evidence_path: Path | None = review_dir / filename
        try:
            evidence_path.write_text(
                json.dumps(evidence, ensure_ascii=False, indent=2), encoding="utf-8"
            )
        except OSError:
            evidence_path = None
        return {
            "passed": passed,
            "captured": captured,
            "attempt_count": len(attempts),
            "max_attempts": self._exploit_attempts,
            "successful_attempt": successful_attempt,
            "outcome_class": outcome_class,
            "solve_exit_clean": solve_exit_clean,
            "solver_outcome_class": solver_outcome_class,
            "attempts": attempts,
            "observation": observation,
            "fresh_target_per_attempt": prepare_attempt is not None,
            "distinct_target_instances": evidence["distinct_target_instances"],
            "distinct_flag_fingerprints": evidence["distinct_flag_fingerprints"],
            "returncode": rc,
            "error": error,
            "evidence": str(evidence_path) if evidence_path else None,
            "stdout_tail": _tail(stdout_tail, 2000),
            "stderr_tail": _tail(stderr_tail, 2000),
        }

    def _run_validation(
        self,
        ctx: ScoringContext,
        *,
        keep_runtime: bool,
        agent_container: str | None = None,
        check_label: str = "score",
    ) -> tuple[dict[str, Score], _LiveRuntime | None]:
        contract, failure = self._load_workspace_contract(ctx)
        if failure is not None:
            return failure, None

        ws = contract["workspace"]
        compose_path = contract["compose_path"]
        build_report = contract["build_report"]
        expected_images = contract["expected_images"]
        build_services_by_image = contract["build_services_by_image"]
        target_services = contract["target_services"]
        target_ports = contract["target_ports"]
        target_port_protocols = contract["target_port_protocols"]
        config_data = contract["config_data"]

        project = (
            "buildcheck_"
            + re.sub(r"[^a-z0-9]+", "", f"{ctx.trial_id}_{check_label}".lower())[:32]
            + "_"
            + uuid.uuid4().hex[:6]
        )
        gate_acquired = False
        runtime: _LiveRuntime | None = None

        # R5 exploit-capture gate: when the route wants it, the scorer flag is on,
        # and the agent committed a runnable solve/.  Live checks disclose only
        # capture status and failure evidence, never the minted value.  The final
        # offline score repeats this with a different flag and a clean instance.
        solve_block = contract.get("solve") or {}
        exploit_checkpoint_required = (
            self._exploit_gate and bool(contract.get("exploit_required"))
        )
        exploit_gate_active = (
            exploit_checkpoint_required
            and bool(solve_block.get("entry"))
            and (ws / "solve").is_dir()
        )
        flag_contract = contract.get("flag_contract") or {}
        minted_flag = (
            _mint_random_flag(str(flag_contract.get("format") or "FAKE{...}"))
            if exploit_gate_active
            else None
        )

        managed_compose_path, pending_subnets = self._write_managed_runtime_compose(
            ctx=ctx,
            project=project,
            workspace=ws,
            compose_path=compose_path,
            config_data=config_data,
            injected_flag=minted_flag,
            flag_contract=flag_contract if exploit_gate_active else None,
        )
        compose_files = [managed_compose_path or compose_path]
        try:
            if self._docker_gate is not None:
                self._docker_gate.acquire()
                gate_acquired = True

            network_retry_count = 0
            auto_managed_network = bool(pending_subnets)
            while True:
                try:
                    up = _run(
                        [
                            *self._compose_args(
                                project=project,
                                compose_files=compose_files,
                                project_directory=ws,
                            ),
                            "up",
                            "-d",
                            "--build",
                        ],
                        cwd=ws,
                        timeout=self._build_timeout,
                    )
                except subprocess.TimeoutExpired:
                    return self._fail(
                        "build_or_boot_timeout",
                        "docker compose up --build timed out.",
                        retryable=True,
                        feedback=(
                            "The authoritative host build did not finish in time. Do not "
                            "reproduce the target locally. Use the exact Dockerfile/build "
                            "closure and its bounded steps to remove one evidenced stall, "
                            "keep the revised candidate report `ready`, then let the next "
                            "`cage-check` rebuild it."
                        ),
                    ), None
                finally:
                    self._release_managed_subnets(pending_subnets)
                    pending_subnets = []

                network_conflict = self._is_address_pool_exhaustion(up.stderr or "")
                if up.returncode == 0 or not network_conflict:
                    break
                if network_retry_count >= _MAX_MANAGED_NETWORK_RETRIES:
                    break

                # Keep the managed runtime compose as the base for every
                # retry. Besides removing host ports it carries the fresh
                # file/env flag injection. A new override gets a newly reserved
                # subnet for this project and retry index.
                next_retry_index = network_retry_count + 1
                override_path, pending_subnets = self._write_managed_network_override(
                    ctx=ctx,
                    project=project,
                    config_data=config_data,
                    retry_index=next_retry_index,
                )
                if override_path is None:
                    break
                network_retry_count = next_retry_index
                self._compose_down(
                    project=project,
                    compose_files=compose_files,
                    workspace=ws,
                )
                compose_files = [managed_compose_path or compose_path, override_path]
                auto_managed_network = True

            if up.returncode != 0:
                stderr_tail = _tail(up.stderr)
                failure_class = "build_or_boot_failed"
                retryable = True
                if (
                    auto_managed_network
                    and self._is_address_pool_exhaustion(up.stderr or "")
                ):
                    failure_class = "host_runtime_network_exhausted"
                    retryable = True
                return self._fail(
                    failure_class,
                    "docker compose up --build failed.",
                    retryable=retryable,
                    evidence={
                        "returncode": up.returncode,
                        "stderr_tail": stderr_tail,
                        "stdout_tail": _tail(up.stdout),
                        "auto_managed_network": auto_managed_network,
                        "managed_network_retries": network_retry_count,
                    },
                    feedback=self._build_failure_feedback(
                        stderr_tail,
                        host_network_issue=(
                            auto_managed_network
                            and self._is_address_pool_exhaustion(up.stderr or "")
                        ),
                    ),
                ), None

            service_cids: dict[str, str] = {}
            for service_name in target_services:
                ps = _run(
                    [
                        *self._compose_args(
                            project=project,
                            compose_files=compose_files,
                            project_directory=ws,
                        ),
                        "ps",
                        "-q",
                        service_name,
                    ],
                    cwd=ws,
                    timeout=60,
                )
                cid = next((line.strip() for line in (ps.stdout or "").splitlines() if line.strip()), "")
                if not cid:
                    return self._fail(
                        "no_container",
                        f"Compose did not produce a running container for target service {service_name!r}.",
                        retryable=True,
                        evidence={"ps_stderr": _tail(ps.stderr)},
                    ), None
                service_cids[service_name] = cid

            time.sleep(_SETTLE_SECONDS)
            service_logs = self._collect_service_logs(
                project=project,
                compose_files=compose_files,
                workspace=ws,
            )
            inspect_map: dict[str, dict[str, Any]] = {}
            states: dict[str, str] = {}
            for service_name, cid in service_cids.items():
                inspected = _run(
                    ["docker", "inspect", "--format", "{{json .}}", cid],
                    timeout=30,
                )
                if inspected.returncode != 0:
                    return self._fail(
                        "inspect_failed",
                        f"docker inspect failed for target service {service_name!r}.",
                        retryable=True,
                        evidence={"stderr_tail": _tail(inspected.stderr)},
                    ), None
                inspect_data = json.loads(inspected.stdout or "{}")
                inspect_map[service_name] = inspect_data
                state = inspect_data.get("State", {}) or {}
                status = str(state.get("Status") or "unknown")
                states[service_name] = status
                if status != "running":
                    return self._fail(
                        "service_not_running",
                        f"Target service {service_name!r} is {status!r} shortly after boot.",
                        retryable=True,
                        evidence={
                            "service": service_name,
                            "container_state": status,
                            "service_logs_tail": _tail(service_logs),
                        },
                        feedback=self._service_failure_feedback(
                            service_name=service_name,
                            status=status,
                            service_logs=service_logs,
                        ),
                    ), None

            image_evidence, image_failure = self._collect_image_evidence(
                expected_images=expected_images,
                build_services_by_image=build_services_by_image,
            )
            if image_failure is not None:
                return image_failure, None

            agent_out_path = ws / "service_output.txt"
            agent_service_output = (
                agent_out_path.read_text(encoding="utf-8", errors="replace")[-4000:]
                if agent_out_path.is_file()
                else ""
            )

            review_dir = ctx.trial_dir or Path(".")
            if keep_runtime:
                review_dir = review_dir / "validator"
            review_dir.mkdir(parents=True, exist_ok=True)
            review_path = review_dir / (
                "service_logs.txt" if not keep_runtime else f"{check_label}-service_logs.txt"
            )
            try:
                review_path.write_text(service_logs, encoding="utf-8")
            except OSError:
                pass

            target_inspects = [inspect_map[service_name] for service_name in target_services]
            network_name = self._choose_network(
                target_inspects,
                hint=contract.get("agent_network_hint"),
            )
            targets: list[dict[str, Any]] = []
            for service_name in target_services:
                inspect_data = inspect_map[service_name]
                networks = inspect_data.get("NetworkSettings", {}).get("Networks", {}) or {}
                ip_addr = ""
                if network_name and network_name in networks:
                    ip_addr = str(networks[network_name].get("IPAddress") or "")
                elif networks:
                    first_network = next(iter(networks.values()))
                    ip_addr = str(first_network.get("IPAddress") or "")
                targets.append(
                    {
                        "service_name": service_name,
                        "container_id": service_cids[service_name],
                        "container_addr": ip_addr or None,
                        "internal_port": target_ports.get(service_name),
                        "protocol": target_port_protocols.get(service_name, "tcp"),
                    }
                )
            container_addr = next(
                (str(target.get("container_addr")) for target in targets if target.get("container_addr")),
                None,
            )

            runtime_probe_results: dict[str, Any] | None = None
            runtime_probe_evidence: str | None = None
            validated_rehost_tier = "R3"
            readiness = _await_target_readiness(targets)
            not_ready = [
                result
                for target, result in zip(
                    targets,
                    readiness.get("targets") or [],
                    strict=True,
                )
                if str(target.get("protocol") or "tcp").lower()
                in {"tcp", "http", "https"}
                and not result.get("ready")
            ]
            if not_ready:
                return self._fail(
                    "target_port_not_ready",
                    "Target containers stayed running but a declared TCP "
                    "endpoint never accepted a connection.",
                    retryable=True,
                    evidence={"readiness": readiness, "not_ready": not_ready},
                    feedback=(
                        "The container process is running, but CAGE could not reach "
                        "the declared internal TCP endpoint before the readiness "
                        "deadline. Check the real listener address/port, relay child, "
                        "entrypoint lifecycle, and startup logs; a running container "
                        "alone is not R3."
                    ),
                ), None
            runtime_probes = contract.get("runtime_probes") or []
            if runtime_probes:
                runtime_probe_results = execute_runtime_probes(
                    runtime_probes,
                    targets=targets,
                )
                runtime_probe_results["readiness"] = readiness
                probe_filename = (
                    "runtime_probe_evidence.json"
                    if not keep_runtime
                    else f"{check_label}-runtime_probe_evidence.json"
                )
                runtime_probe_evidence, probe_write_failure = (
                    self._write_runtime_probe_evidence(
                        trial_dir=review_dir,
                        trial_id=ctx.trial_id,
                        filename=probe_filename,
                        results=runtime_probe_results,
                    )
                )
                if probe_write_failure is not None:
                    return probe_write_failure, None
                if not runtime_probe_results.get("passed"):
                    if contract.get("runtime_probes_required"):
                        failed_probes = [
                            {
                                "id": result.get("id"),
                                "service": result.get("service"),
                                "last_attempt": (result.get("attempts") or [None])[-1],
                            }
                            for result in runtime_probe_results.get("probes") or []
                            if not result.get("passed")
                        ]
                        failed_probe_excerpt = _tail(
                            json.dumps(failed_probes, ensure_ascii=False, sort_keys=True),
                            1600,
                        )
                        return self._fail(
                            "runtime_probe_failed",
                            "The target stayed up but failed its challenge-specific runtime probe.",
                            retryable=True,
                            evidence={
                                "runtime_probe_evidence": runtime_probe_evidence,
                                "failed_probes": failed_probes,
                            },
                            feedback=(
                                "CAGE independently reached the built target, but the response "
                                "did not match the source-backed R4 assertion. The failed host-side "
                                f"attempt was: {failed_probe_excerpt}. Repair the real service "
                                "or correct an evidence-backed probe. Do not replace it with a port-only check."
                            ),
                        ), None
                    # Optional probe on an R3 task failed to match: the build
                    # still earns R3; the R4 bonus is simply not granted.
                    validated_rehost_tier = "R3"
                else:
                    validated_rehost_tier = "R4"

            # R5: prove the rebuilt target is faithfully exploitable by running
            # the agent's committed solve/ against it from a player vantage and
            # requiring one attempt to capture the minted flag and exit zero. A
            # bonus rung above R4 — it
            # only promotes; a failed exploit never regresses an R3/R4 build.
            exploit_result: dict[str, Any] | None = None
            exploit_attempt_service_logs: list[str] = []
            if exploit_gate_active and minted_flag:
                def prepare_exploit_attempt(attempt_number: int) -> dict[str, Any]:
                    nonlocal compose_files
                    nonlocal network_retry_count
                    nonlocal service_logs
                    nonlocal states
                    nonlocal network_name
                    nonlocal targets
                    nonlocal container_addr
                    nonlocal minted_flag

                    # The build image is retained, but every exploit invocation
                    # gets a new container/network/volume lifecycle and a new
                    # private flag. This prevents a crash, heap mutation, VM
                    # shutdown, or consumed one-shot session from poisoning the
                    # next attempt.
                    self._compose_down(
                        project=project,
                        compose_files=compose_files,
                        workspace=ws,
                    )
                    minted_flag = _mint_random_flag(
                        str(flag_contract.get("format") or "FAKE{...}")
                    )
                    fresh = self._start_fresh_exploit_target(
                        ctx=ctx,
                        project=project,
                        workspace=ws,
                        compose_path=compose_path,
                        config_data=config_data,
                        target_services=target_services,
                        target_ports=target_ports,
                        target_port_protocols=target_port_protocols,
                        network_hint=contract.get("agent_network_hint"),
                        flag=minted_flag,
                        flag_contract=flag_contract,
                    )
                    compose_files = list(fresh.get("compose_files") or compose_files)
                    network_retry_count += int(
                        fresh.get("managed_network_retries") or 0
                    )

                    attempt_log_name = (
                        f"exploit-attempt-{attempt_number}-service-logs.txt"
                        if check_label == "score"
                        else (
                            f"{check_label}-exploit-attempt-{attempt_number}"
                            "-service-logs.txt"
                        )
                    )
                    attempt_log_path = review_dir / attempt_log_name
                    attempt_logs = str(fresh.get("service_logs") or "")
                    try:
                        attempt_log_path.write_text(attempt_logs, encoding="utf-8")
                        exploit_attempt_service_logs.append(str(attempt_log_path))
                    except OSError:
                        attempt_log_path = None

                    if not fresh.get("ok"):
                        service_logs = attempt_logs
                        states = dict(fresh.get("states") or {})
                        if not states:
                            states = {
                                service_name: "recreate_failed"
                                for service_name in target_services
                            }
                        network_name = fresh.get("network_name")
                        targets = list(fresh.get("targets") or [])
                        container_addr = None
                        return {
                            **fresh,
                            "flag": minted_flag,
                            "fresh_target": True,
                            "target_instance": {
                                "attempt": attempt_number,
                                "project": project,
                                "network_name": network_name,
                                "container_ids": [],
                                "service_logs": (
                                    str(attempt_log_path) if attempt_log_path else None
                                ),
                            },
                        }

                    service_logs = attempt_logs
                    states = dict(fresh.get("states") or {})
                    network_name = str(fresh.get("network_name") or "") or None
                    targets = list(fresh.get("targets") or [])
                    container_addr = fresh.get("container_addr")
                    try:
                        review_path.write_text(service_logs, encoding="utf-8")
                    except OSError:
                        pass
                    return {
                        **fresh,
                        "flag": minted_flag,
                        "fresh_target": True,
                        "target_instance": {
                            "attempt": attempt_number,
                            "project": project,
                            "network_name": network_name,
                            "container_ids": [
                                str(target.get("container_id"))
                                for target in targets
                                if target.get("container_id")
                            ],
                            "service_logs": (
                                str(attempt_log_path) if attempt_log_path else None
                            ),
                        },
                    }

                exploit_result = self._run_exploit_validation(
                    ws=ws,
                    network_name=network_name,
                    targets=targets,
                    solve=solve_block,
                    flag=minted_flag,
                    review_dir=review_dir,
                    check_label=check_label,
                    prepare_attempt=prepare_exploit_attempt,
                )
                if exploit_result.get("passed"):
                    validated_rehost_tier = "R5"
                elif keep_runtime:
                    # The final failed exploit may have killed or mutated its
                    # target. Leave a fourth, untouched instance for the agent's
                    # evidence-driven diagnosis rather than returning a poisoned
                    # live stack.
                    diagnostic = prepare_exploit_attempt(
                        self._exploit_attempts + 1
                    )
                    exploit_result["diagnostic_target_recreated"] = bool(
                        diagnostic.get("ok")
                    )
                    exploit_result["diagnostic_target_error"] = (
                        None if diagnostic.get("ok") else diagnostic.get("error")
                    )

            manifest_name = (
                "image_manifest.json"
                if not keep_runtime
                else f"{check_label}-image_manifest.json"
            )
            image_manifest, manifest_failure = self._write_image_manifest(
                trial_dir=review_dir,
                trial_id=ctx.trial_id,
                filename=manifest_name,
                image_evidence=image_evidence or [],
            )
            if manifest_failure is not None:
                return manifest_failure, None

            if keep_runtime:
                if not network_name:
                    return self._fail(
                        "target_network_unresolved",
                        "Validator could not determine a Docker network for the built target.",
                        retryable=True,
                    ), None
                if not agent_container:
                    return self._fail(
                        "agent_container_missing",
                        "Validator cannot attach the agent container to the target network.",
                        retryable=False,
                    ), None
                connected, error = self._connect_agent_to_network(
                    network_name=network_name,
                    agent_container=agent_container,
                )
                if not connected:
                    return self._fail(
                        "agent_attach_failed",
                        "Validator could not attach the agent to the target network.",
                        retryable=True,
                        evidence={"error": error, "network_name": network_name},
                    ), None
                runtime = _LiveRuntime(
                    project=project,
                    workspace=ws,
                    compose_path=compose_path,
                    compose_files=compose_files,
                    agent_container=agent_container,
                    network_name=network_name,
                    service_targets=targets,
                    image_manifest=image_manifest,
                )

            scores = self._pass(
                ctx=ctx,
                compose_path=compose_path,
                container_state="; ".join(f"{name}={state}" for name, state in states.items()),
                container_addr=container_addr,
                network_name=network_name,
                targets=targets,
                service_logs=service_logs,
                agent_service_output=agent_service_output,
                build_report=build_report,
                image_evidence=image_evidence or [],
                image_manifest=image_manifest,
                validated_rehost_tier=validated_rehost_tier,
                runtime_probe_results=runtime_probe_results,
                runtime_probe_evidence=runtime_probe_evidence,
                exploit_result=exploit_result,
                # validate_live adds its recovery-oriented checkpoint payload
                # below. Final scoring must independently enforce the same R5
                # contract instead of treating an R3/R4 build as success.
                exploit_checkpoint_required=(
                    exploit_checkpoint_required and not keep_runtime
                ),
                managed_network_retries=network_retry_count,
                review_files={
                    "service_logs": str(review_path),
                    "agent_service_output": str(agent_out_path) if agent_out_path.is_file() else None,
                    "runtime_probe_evidence": runtime_probe_evidence,
                    "exploit_evidence": (exploit_result or {}).get("evidence"),
                    "exploit_attempt_service_logs": exploit_attempt_service_logs,
                },
            )
            return scores, runtime
        finally:
            self._release_managed_subnets(pending_subnets)
            if not keep_runtime or runtime is None:
                try:
                    self._compose_down(
                        project=project,
                        compose_files=compose_files,
                        workspace=ws,
                    )
                except Exception:
                    pass
            if gate_acquired and self._docker_gate is not None:
                self._docker_gate.release()

    def validate_live(
        self,
        ctx: _LiveTrialContext,
        *,
        check_label: str,
    ) -> dict[str, Any]:
        try:
            scores, runtime = self._run_validation(
                ScoringContext(
                    trial_id=ctx.trial_id,
                    trial_index=0,
                    sample=ctx.sample,
                    trial_dir=ctx.trial_dir,
                    run_dir=ctx.trial_dir,
                ),
                keep_runtime=True,
                agent_container=ctx.agent_container,
                check_label=check_label,
            )
        except subprocess.TimeoutExpired as exc:
            scores = self._host_runtime_timeout_failure(exc)
            runtime = None
        payload = self._payload_from_scores(scores)
        if runtime is not None:
            payload["_runtime"] = runtime
        if payload.get("passed") and payload.get("targets"):
            payload["runtime_reused"] = False
            runtime_probe_results = payload.get("runtime_probe_results")
            validated_rehost_tier = str(payload.get("validated_rehost_tier") or "R3")
            payload["probe_evidence_present"] = bool(
                validated_rehost_tier == "R4"
                and isinstance(runtime_probe_results, dict)
                and runtime_probe_results.get("passed")
            )
            payload["feedback"] = _live_pass_feedback(
                targets=payload.get("targets") or [],
                runtime_reused=False,
                validated_rehost_tier=validated_rehost_tier,
                runtime_probe_results=(
                    runtime_probe_results
                    if isinstance(runtime_probe_results, dict)
                    else None
                ),
            )
            exploit_checkpoint_required = (
                self._exploit_gate and _exploit_validation_required(ctx.sample)
            )
            if exploit_checkpoint_required:
                payload["required_checkpoint"] = "R5"
                payload["checkpoint"] = "exploit_capture"
                if validated_rehost_tier == "R5":
                    payload["checkpoint_status"] = "PASS"
                else:
                    observation = str(payload.get("exploit_observation") or "").strip()
                    stdout_tail = str(payload.get("exploit_stdout_tail") or "").strip()
                    stderr_tail = str(payload.get("exploit_stderr_tail") or "").strip()
                    diagnostic_target = next(
                        (
                            target
                            for target in payload.get("targets") or []
                            if target.get("container_addr")
                        ),
                        {},
                    )
                    diagnostic_host = str(
                        diagnostic_target.get("container_addr") or "<returned-host>"
                    )
                    diagnostic_port = diagnostic_target.get("internal_port")
                    diagnostic_endpoint = (
                        f"{diagnostic_host}:{diagnostic_port}"
                        if diagnostic_port is not None
                        else diagnostic_host
                    )
                    evidence = ""
                    if observation:
                        evidence += f" Observation: {observation}"
                    if stdout_tail:
                        evidence += f" Solver output tail: {stdout_tail[-1200:]!r}."
                    if stderr_tail:
                        evidence += f" Solver stderr tail: {stderr_tail[-800:]!r}."
                    if not observation:
                        evidence = (
                            " No runnable solve entry was validated. Create `solve/`, "
                            "set `challenge.json.solve.entry`, and target "
                            "`TARGET_HOST`/`TARGET_PORT`."
                        )
                    # R3/R4 remains valid evidence, but this live command is a
                    # recovery gate for a joint R5 episode and therefore exits
                    # non-zero until exploit capture itself is observed.
                    payload.update(
                        {
                            "passed": False,
                            "failure_class": "exploit_capture_not_passed",
                            "retryable": True,
                            "checkpoint_status": "FAIL",
                            "feedback": (
                                f"BUILD/RUNTIME CHECKPOINT PASS through "
                                f"{validated_rehost_tier}; EXPLOIT_CAPTURE "
                                f"CHECKPOINT FAIL.{evidence} Use this evidence, "
                                "then obey this recovery evidence gate before another "
                                "`cage-check`: name the last reached marker and first "
                                "missing marker. An explicit stage-specific error in "
                                "the returned tails can satisfy the gate. If the result "
                                "is only a timeout, EOF, empty output, or otherwise "
                                "ambiguous, do not edit the workspace yet: keep the "
                                "returned live stack unchanged and run the committed "
                                "solver, or the smallest unchanged prefix that reaches "
                                f"its next milestone, against {diagnostic_endpoint}. "
                                "Use explicit short deadlines for connection, prompt/"
                                "authentication, payload transfer, primitive, and flag-"
                                "read stages; emit each reached marker unbuffered. The "
                                "next validator replay may invoke the committed EXP "
                                f"up to {self._exploit_attempts} times, with a separate "
                                f"{self._exploit_timeout}s budget for each invocation. "
                                "Before every invocation it destroys the preceding "
                                "target and non-external volumes, recreates the target "
                                "from the already-built image, and injects a different "
                                "fresh flag; never rely on process, heap, VM, volume, "
                                "or session state carrying across attempts. "
                                "One exact fresh-flag capture is enough, and success "
                                "in every attempt is not required. Exit status and "
                                "post-capture behavior are separate solver-hygiene data. "
                                "The sum of "
                                "all stage deadlines and internal retries within one "
                                "invocation must fit its budget. Only then change one causal "
                                "dimension supported by that observation. A manual "
                                "diagnostic is not R5, and a timeout alone does not "
                                "classify the cause."
                            ),
                        }
                    )
        return payload

    def stop_live_runtime(self, runtime: _LiveRuntime) -> dict[str, Any]:
        gate_acquired = False
        errors: list[str] = []
        try:
            if self._docker_gate is not None:
                self._docker_gate.acquire()
                gate_acquired = True
            if runtime.network_name:
                try:
                    self._disconnect_agent_from_network(
                        network_name=runtime.network_name,
                        agent_container=runtime.agent_container,
                    )
                except Exception as exc:
                    errors.append(f"disconnect_failed: {exc}")
            try:
                self._compose_down(
                    project=runtime.project,
                    compose_files=runtime.compose_files,
                    workspace=runtime.workspace,
                )
            except Exception as exc:
                errors.append(f"compose_down_failed: {exc}")
        finally:
            if gate_acquired and self._docker_gate is not None:
                self._docker_gate.release()
        return {
            "stopped": not errors,
            "feedback": "Live validation stack stopped." if not errors else "Failed to stop live validation stack cleanly.",
            "project": runtime.project,
            "network_name": runtime.network_name,
            "errors": errors,
        }

    def score(self, ctx: ScoringContext) -> dict[str, Score]:
        try:
            scores, _runtime = self._run_validation(ctx, keep_runtime=False)
            return scores
        except subprocess.TimeoutExpired as exc:
            return self._host_runtime_timeout_failure(exc)
