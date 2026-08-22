#!/usr/bin/env python3
"""Build an auditable CAGE build-target queue from static CTF material records."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from collections import Counter, defaultdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Iterable

SCHEMA_VERSION = "cage-build-task-list-v1"
TASK_SCHEMA_VERSION = "cage-build-task-v1"
MAIN_TIERS = {"D3", "D4", "D5"}
DEFERRED_TIERS = {"D2"}
DROPPED_TIERS = {"D0", "D1"}
AVAILABLE_STATES = {"candidate", "confirmed"}
MATERIAL_NAMES = ("deploy", "source", "attachment", "writeup", "exp")
CLOSURE_RANK = {
    "closed": 0,
    "external": 1,
    "review": 2,
    "missing": 3,
    "no_deploy": 4,
}
PWN_PRIORITIES = {
    "dockerfile_writeup_attachments": (
        0,
        "Dockerfile + Writeup + attachments",
    ),
    "dockerfile_attachments": (1, "Dockerfile + attachments"),
    "writeup_attachments": (2, "Writeup + attachments"),
    "source_attachments": (
        3,
        "source + attachments without Dockerfile or Writeup",
    ),
    "attachments_only": (4, "attachments only"),
    "incomplete": (5, "other D3+ Pwn material shape"),
}


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def canonical_sha256(value: Any) -> str:
    encoded = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode()
    return hashlib.sha256(encoded).hexdigest()


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as stream:
        for line_number, line in enumerate(stream, 1):
            if not line.strip():
                continue
            value = json.loads(line)
            if not isinstance(value, dict):
                raise ValueError(f"{path}:{line_number} must contain a JSON object")
            rows.append(value)
    return rows


def slugify(value: Any) -> str:
    return re.sub(r"[^a-z0-9]+", "-", str(value or "").lower()).strip("-")


def display_path(path: Path, root: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return str(path.resolve())


def normalize_tier(value: Any) -> str:
    tier = str(value or "").strip().upper()
    if tier not in MAIN_TIERS | DEFERRED_TIERS | DROPPED_TIERS:
        raise ValueError(f"unsupported data tier: {value!r}")
    return tier


def load_completion_manifests(
    paths: Iterable[Path],
    *,
    source_repo: Path,
) -> dict[str, list[dict[str, Any]]]:
    completed: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for raw_path in paths:
        path = raw_path.expanduser().resolve()
        payload = json.loads(path.read_text(encoding="utf-8"))
        environments = payload.get("environments") if isinstance(payload, dict) else None
        if not isinstance(environments, list):
            raise ValueError(f"{path} must contain an environments list")
        manifest_evidence = {
            "manifest": display_path(path, source_repo),
            "manifest_sha256": file_sha256(path),
            "batch_id": payload.get("batch_id"),
            "admission": payload.get("admission") or payload.get("status"),
        }
        for entry in environments:
            if not isinstance(entry, dict):
                raise ValueError(f"{path} contains a non-object environment entry")
            env_id = str(entry.get("env_id") or "").strip()
            if not env_id:
                raise ValueError(f"{path} contains an environment without env_id")
            images = entry.get("images")
            if images is None and entry.get("image"):
                images = [entry["image"]]
            if images is None and entry.get("primary_image"):
                images = [entry["primary_image"]]
            if not isinstance(images, list):
                images = []
            completed[env_id].append(
                {
                    **manifest_evidence,
                    "maturity": entry.get("maturity") or payload.get("maturity"),
                    "images": [str(image) for image in images],
                }
            )
    return dict(completed)


def load_prior_runtime_failures(
    paths: Iterable[Path],
    *,
    source_repo: Path,
) -> dict[str, list[dict[str, Any]]]:
    failures: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for raw_path in paths:
        path = raw_path.expanduser().resolve()
        payload = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            continue
        for replacement in payload.get("runtime_replacements") or []:
            if not isinstance(replacement, dict):
                continue
            env_id = str(replacement.get("removed") or "").strip()
            reason = str(replacement.get("reason") or "").strip()
            if not env_id or not reason:
                continue
            failures[env_id].append(
                {
                    "manifest": display_path(path, source_repo),
                    "batch_id": payload.get("batch_id"),
                    "stage": "cage_runtime_smoke",
                    "reason": reason,
                }
            )
    return dict(failures)


def material_available(row: dict[str, Any], name: str) -> bool:
    return str(row["materials"][name].get("state")) in AVAILABLE_STATES


def safe_relative_path(raw_path: Any) -> Path | None:
    if not isinstance(raw_path, str) or not raw_path.strip():
        return None
    path = Path(raw_path.strip())
    if path.is_absolute() or ".." in path.parts:
        return None
    return path


def evidence_path(
    raw_path: Any,
    *,
    challenge_dir: Path,
    source_repo: Path,
) -> Path | None:
    if not isinstance(raw_path, str) or not raw_path.strip():
        return None
    path = Path(raw_path)
    candidates: list[Path] = []
    if path.is_absolute():
        candidates.append(path)
    else:
        candidates.extend((challenge_dir / path, source_repo / path))
    for candidate in candidates:
        try:
            relative = candidate.resolve().relative_to(challenge_dir.resolve())
        except (OSError, ValueError):
            continue
        resolved = challenge_dir / relative
        if resolved.exists():
            return relative
    return None


def static_material_paths(
    row: dict[str, Any],
    name: str,
    *,
    challenge_dir: Path,
) -> list[Path]:
    material = row["materials"][name]
    paths: list[Path] = []
    for key in ("files", "candidate_files"):
        for entry in material.get(key) or []:
            if not isinstance(entry, dict):
                continue
            relative = safe_relative_path(entry.get("path"))
            if relative is not None and (challenge_dir / relative).exists():
                paths.append(relative)
    return paths


def writeup_paths(
    row: dict[str, Any],
    *,
    challenge_dir: Path,
    source_repo: Path,
) -> list[Path]:
    if not material_available(row, "writeup"):
        return []
    paths: list[Path] = []
    for entry in row["materials"]["writeup"].get("evidence") or []:
        if not isinstance(entry, dict):
            continue
        raw_paths = [entry.get("local_path")]
        for local_file in entry.get("local_files") or []:
            if isinstance(local_file, dict):
                raw_paths.extend((local_file.get("local_path"), local_file.get("path")))
        for raw_path in raw_paths:
            relative = evidence_path(
                raw_path,
                challenge_dir=challenge_dir,
                source_repo=source_repo,
            )
            if relative is not None:
                paths.append(relative)
    return sorted(set(paths), key=lambda path: path.as_posix())


def compact_role_paths(
    paths: Iterable[Path],
    *,
    role: str,
    challenge_dir: Path,
) -> list[str]:
    compacted: list[Path] = []
    for path in paths:
        if role == "deployment" and path.parts:
            if path.parts[0] == "deploy" and (challenge_dir / "deploy").is_dir():
                compacted.append(Path("deploy"))
                continue
            if path.parts[0] == "source" and (challenge_dir / "source").is_dir():
                compacted.append(Path("source"))
                continue
        if role == "attachments" and path.parts:
            if path.parts[0] == "public" and (challenge_dir / "public").is_dir():
                compacted.append(Path("public"))
                continue
        compacted.append(path)
    return sorted({path.as_posix() for path in compacted})


def task_materials(
    row: dict[str, Any],
    *,
    challenge_dir: Path,
    source_repo: Path,
) -> dict[str, list[str]]:
    deployment_paths = static_material_paths(
        row,
        "deploy",
        challenge_dir=challenge_dir,
    )
    for entry in row.get("docker_closure", {}).get("entries") or []:
        if not isinstance(entry, dict):
            continue
        relative = safe_relative_path(entry.get("path"))
        if relative is not None and (challenge_dir / relative).exists():
            deployment_paths.append(relative)
    if material_available(row, "deploy") and not deployment_paths:
        if (challenge_dir / "deploy").is_dir():
            deployment_paths.append(Path("deploy"))
        elif (challenge_dir / "source").is_dir() and any(
            path.is_file()
            and (
                path.name.lower().startswith("dockerfile")
                or path.name.lower()
                in {
                    "docker-compose.yml",
                    "docker-compose.yaml",
                    "compose.yml",
                    "compose.yaml",
                }
            )
            for path in (challenge_dir / "source").rglob("*")
        ):
            deployment_paths.append(Path("source"))

    source_paths = static_material_paths(row, "source", challenge_dir=challenge_dir)
    if material_available(row, "source") and (challenge_dir / "source").is_dir():
        source_paths.append(Path("source"))

    attachment_paths = static_material_paths(
        row,
        "attachment",
        challenge_dir=challenge_dir,
    )
    if (
        material_available(row, "attachment")
        and not attachment_paths
        and (challenge_dir / "public").is_dir()
    ):
        attachment_paths.append(Path("public"))

    return {
        "deployment": compact_role_paths(
            deployment_paths,
            role="deployment",
            challenge_dir=challenge_dir,
        ),
        "source": compact_role_paths(
            source_paths,
            role="source",
            challenge_dir=challenge_dir,
        ),
        "attachments": compact_role_paths(
            attachment_paths,
            role="attachments",
            challenge_dir=challenge_dir,
        ),
        "writeups": compact_role_paths(
            writeup_paths(
                row,
                challenge_dir=challenge_dir,
                source_repo=source_repo,
            ),
            role="writeups",
            challenge_dir=challenge_dir,
        ),
    }


def contains_dockerfile(challenge_dir: Path, paths: Iterable[str]) -> bool:
    for raw_path in paths:
        path = challenge_dir / raw_path
        if path.is_file() and path.name.lower().startswith("dockerfile"):
            return True
        if path.is_dir() and any(
            child.is_file() and child.name.lower().startswith("dockerfile")
            for child in path.rglob("*")
        ):
            return True
    return False


def pwn_priority(
    *,
    category: str,
    materials: dict[str, list[str]],
    challenge_dir: Path,
) -> dict[str, Any]:
    if category != "pwn":
        return {
            "id": "web_data_tier",
            "rank": 0,
            "label": "Web tasks ordered by D tier and Docker closure",
            "has_dockerfile": contains_dockerfile(
                challenge_dir,
                materials["deployment"],
            ),
        }

    has_dockerfile = contains_dockerfile(challenge_dir, materials["deployment"])
    has_writeup = bool(materials["writeups"])
    has_attachments = bool(materials["attachments"])
    has_source = bool(materials["source"])
    has_deployment = bool(materials["deployment"])
    if has_dockerfile and has_writeup and has_attachments:
        priority_id = "dockerfile_writeup_attachments"
    elif has_dockerfile and has_attachments:
        priority_id = "dockerfile_attachments"
    elif has_writeup and has_attachments:
        priority_id = "writeup_attachments"
    elif has_deployment:
        priority_id = "incomplete"
    elif has_source and has_attachments:
        priority_id = "source_attachments"
    elif has_attachments:
        priority_id = "attachments_only"
    else:
        priority_id = "incomplete"
    rank, label = PWN_PRIORITIES[priority_id]
    return {
        "id": priority_id,
        "rank": rank,
        "label": label,
        "has_dockerfile": has_dockerfile,
    }


def build_profile(materials: dict[str, list[str]]) -> str:
    if materials["deployment"]:
        return "official_deployment"
    if materials["source"]:
        return "source_rebuild"
    if materials["attachments"]:
        return "artifact_rehost"
    return "triage"


def image_slugs(rows: Iterable[dict[str, Any]]) -> tuple[dict[str, str], dict[str, Any]]:
    rows = list(rows)
    by_base: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        category = str(row["identity"]["category"]).lower()
        base = slugify(row["identity"].get("name")) or slugify(row["challenge_id"])
        by_base[(category, base)].append(row)

    result: dict[str, str] = {}
    collision_details: dict[str, list[str]] = {}
    for (category, base), grouped in sorted(by_base.items()):
        if len(grouped) == 1:
            result[grouped[0]["challenge_id"]] = base
            continue
        collision_details[f"{category}/{base}"] = sorted(row["challenge_id"] for row in grouped)
        by_year: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for row in grouped:
            by_year[str(row["identity"].get("year") or "unknown")].append(row)
        for year, year_rows in by_year.items():
            for row in year_rows:
                suffix = slugify(year)
                if len(year_rows) > 1:
                    suffix += "-" + hashlib.sha256(row["challenge_id"].encode()).hexdigest()[:6]
                result[row["challenge_id"]] = f"{base}-{suffix}"
    return result, {
        "base_collision_count": len(collision_details),
        "affected_task_count": sum(len(ids) for ids in collision_details.values()),
        "collisions": collision_details,
    }


def material_states(row: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        name: {
            "state": row["materials"][name].get("state"),
            "search_status": row["materials"][name].get("search_status"),
            "count": int(row["materials"][name].get("count") or 0),
        }
        for name in MATERIAL_NAMES
    }


def blocker_codes(row: dict[str, Any]) -> list[str]:
    codes = {
        item.get("code")
        for item in (
            list(row.get("blockers") or [])
            + list(row.get("docker_closure", {}).get("blockers") or [])
        )
        if isinstance(item, dict) and item.get("code")
    }
    return sorted(str(code) for code in codes)


def make_task_record(
    row: dict[str, Any],
    *,
    source_repo: Path,
    static_materials: Path,
    wave: str,
    image_slug: str,
    queue_name: str,
    selected_tier_source: str = "confirmed",
    prior_runtime_failures: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    env_id = str(row["challenge_id"])
    identity = row["identity"]
    category = str(identity["category"]).lower()
    candidate_tier = normalize_tier(row["data_tier"]["candidate"])
    confirmed_tier = normalize_tier(row["data_tier"]["confirmed"])
    if selected_tier_source not in {"candidate", "confirmed"}:
        raise ValueError("selected_tier_source must be candidate or confirmed")
    selected_tier = {
        "candidate": candidate_tier,
        "confirmed": confirmed_tier,
    }[selected_tier_source]
    challenge_dir = (source_repo / "sources" / category / "challenges" / env_id).resolve()
    if not challenge_dir.is_dir():
        raise FileNotFoundError(f"missing challenge material root: {challenge_dir}")
    materials = task_materials(
        row,
        challenge_dir=challenge_dir,
        source_repo=source_repo,
    )
    priority = pwn_priority(
        category=category,
        materials=materials,
        challenge_dir=challenge_dir,
    )
    closure_status = str(row.get("docker_closure", {}).get("status") or "unknown")
    prior_runtime_failures = list(prior_runtime_failures or [])
    tier_rank = -int(candidate_tier[1:])
    category_rank = 0 if category == "pwn" else 1
    sort_key = [
        category_rank,
        1 if prior_runtime_failures else 0,
        int(priority["rank"]),
        tier_rank,
        CLOSURE_RANK.get(closure_status, 9),
        env_id,
    ]
    task = {
        "schema_version": TASK_SCHEMA_VERSION,
        "id": env_id,
        "name": identity.get("name") or env_id,
        "category": category,
        "description": (
            f"{identity.get('event') or 'Unknown event'} "
            f"{identity.get('year') or 'unknown year'} {category} challenge "
            f"{identity.get('name') or env_id}. Reconstruct a faithful CAGE target "
            "from the supplied classified evidence."
        ),
        "data_tier": selected_tier,
        "data_tier_evidence": {
            "selected_from": selected_tier_source,
            "candidate": candidate_tier,
            "confirmed": confirmed_tier,
        },
        "target_maturity": {
            "data": selected_tier,
            "rehost": "R3",
            "exploit": "X0",
        },
        "build_profile": build_profile(materials),
        "material_root": str(challenge_dir),
        "materials": materials,
        "material_states": material_states(row),
        "docker_closure": {
            "status": closure_status,
            "selection_status": row.get("docker_closure", {}).get("selection_status"),
            "missing_ref_count": len(row.get("docker_closure", {}).get("missing_refs") or []),
            "review_ref_count": len(row.get("docker_closure", {}).get("review_refs") or []),
        },
        "static_evidence": {
            "manifest_path": row.get("manifest_path"),
            "blocker_codes": blocker_codes(row),
            "review_flags": sorted(str(flag) for flag in row.get("review_flags") or []),
            "prior_runtime_failures": prior_runtime_failures,
        },
        "queue_priority": {
            **priority,
            "known_prior_runtime_blocker": bool(prior_runtime_failures),
            "sort_key": sort_key,
        },
        "service_contract": {
            "protocol": "tcp" if category == "pwn" else "http",
        },
        "flag_contract": {
            "format": "flag{...}",
            "evidence_state": row.get("flag_contract", {}).get("state", "not_searched"),
        },
        "build_environment": {
            "network": "restricted",
        },
        "image_name": (f"ctfenv/{category}-{image_slug}-{wave}:{selected_tier.lower()}-r3-x0"),
    }
    return {
        "schema_version": SCHEMA_VERSION,
        "queue": queue_name,
        "env_id": env_id,
        "priority": task["queue_priority"],
        "task": task,
        "provenance": {
            "static_materials": display_path(static_materials, source_repo),
            "static_record_sha256": canonical_sha256(row),
            "snapshot_as_of": row.get("snapshot_as_of"),
            "wave_id": row.get("wave_id"),
        },
    }


def queue_sort_key(record: dict[str, Any]) -> tuple[Any, ...]:
    return tuple(record["priority"]["sort_key"])


def build_artifacts(
    *,
    static_materials: Path,
    source_repo: Path,
    completion_manifests: Iterable[Path],
    wave: str,
) -> dict[str, Any]:
    source_repo = source_repo.expanduser().resolve()
    static_materials = static_materials.expanduser().resolve()
    completion_manifests = list(completion_manifests)
    wave = slugify(wave)
    if not wave or not wave.startswith("wave"):
        raise ValueError("wave must normalize to a name beginning with wave")

    rows = read_jsonl(static_materials)
    ids = [str(row.get("challenge_id") or "") for row in rows]
    if not all(ids) or len(ids) != len(set(ids)):
        raise ValueError("static material records must have unique non-empty challenge_id")
    completed = load_completion_manifests(
        completion_manifests,
        source_repo=source_repo,
    )
    prior_runtime_failures = load_prior_runtime_failures(
        completion_manifests,
        source_repo=source_repo,
    )
    unknown_completed = sorted(set(completed) - set(ids))
    if unknown_completed:
        raise ValueError(
            "completion manifests reference unknown challenge IDs: " + ", ".join(unknown_completed)
        )

    active_rows = [
        row
        for row in rows
        if row["challenge_id"] not in completed
        and (
            normalize_tier(row["data_tier"]["confirmed"]) in MAIN_TIERS
            or normalize_tier(row["data_tier"]["confirmed"]) in DEFERRED_TIERS
            or normalize_tier(row["data_tier"]["candidate"]) in DEFERRED_TIERS
        )
    ]
    slugs, collision_summary = image_slugs(active_rows)

    main: list[dict[str, Any]] = []
    deferred: list[dict[str, Any]] = []
    excluded: list[dict[str, Any]] = []
    completed_rows: list[dict[str, Any]] = []
    candidate_only: list[dict[str, Any]] = []
    for row in rows:
        env_id = row["challenge_id"]
        category = row["identity"]["category"]
        candidate_tier = normalize_tier(row["data_tier"]["candidate"])
        confirmed_tier = normalize_tier(row["data_tier"]["confirmed"])
        base = {
            "env_id": env_id,
            "category": category,
            "candidate_data_tier": candidate_tier,
            "confirmed_data_tier": confirmed_tier,
        }
        if env_id in completed:
            completed_record = {
                **base,
                "reason": "already_generated_r3",
                "completion_evidence": completed[env_id],
            }
            completed_rows.append(completed_record)
            excluded.append(completed_record)
        elif confirmed_tier in MAIN_TIERS:
            main.append(
                make_task_record(
                    row,
                    source_repo=source_repo,
                    static_materials=static_materials,
                    wave=wave,
                    image_slug=slugs[env_id],
                    queue_name="build",
                    selected_tier_source="confirmed",
                    prior_runtime_failures=prior_runtime_failures.get(env_id),
                )
            )
        elif confirmed_tier in DEFERRED_TIERS or candidate_tier in DEFERRED_TIERS:
            record = make_task_record(
                row,
                source_repo=source_repo,
                static_materials=static_materials,
                wave=wave,
                image_slug=slugs[env_id],
                queue_name="deferred_d2",
                selected_tier_source=(
                    "confirmed" if confirmed_tier in DEFERRED_TIERS else "candidate"
                ),
                prior_runtime_failures=prior_runtime_failures.get(env_id),
            )
            record["defer_reason"] = "policy_defer_d2_no_default_build_attempt"
            deferred.append(record)
        elif candidate_tier in MAIN_TIERS:
            record = {
                **base,
                "reason": "candidate_tier_not_confirmed_for_build",
                "material_states": material_states(row),
                "docker_closure": {
                    "status": row.get("docker_closure", {}).get("status"),
                    "selection_status": row.get("docker_closure", {}).get("selection_status"),
                },
                "blocker_codes": blocker_codes(row),
                "review_flags": sorted(str(flag) for flag in row.get("review_flags") or []),
                "manifest_path": row.get("manifest_path"),
            }
            candidate_only.append(record)
            excluded.append(record)
        elif confirmed_tier in DROPPED_TIERS:
            excluded.append(
                {
                    **base,
                    "reason": "policy_drop_d0_d1",
                    "blocker_codes": blocker_codes(row),
                }
            )
        else:
            raise AssertionError(
                f"unhandled data tier pair: candidate={candidate_tier}, confirmed={confirmed_tier}"
            )

    main.sort(key=queue_sort_key)
    deferred.sort(key=queue_sort_key)
    completed_rows.sort(key=lambda row: row["env_id"])
    candidate_only.sort(key=lambda row: row["env_id"])
    excluded.sort(key=lambda row: (row["reason"], row["env_id"]))
    for position, record in enumerate(main, 1):
        record["position"] = position
    for position, record in enumerate(deferred, 1):
        record["position"] = position

    accounted = len(main) + len(deferred) + len(excluded)
    if accounted != len(rows):
        raise AssertionError(f"queue accounting mismatch: {accounted} != {len(rows)}")

    summary = {
        "schema_version": SCHEMA_VERSION,
        "generated_at": datetime.now(UTC).isoformat(),
        "wave": wave,
        "policy": {
            "main_data_tiers": sorted(MAIN_TIERS),
            "main_admission_field": "confirmed_data_tier",
            "task_prompt_tier_field": "confirmed_data_tier",
            "deferred_data_tiers": sorted(DEFERRED_TIERS),
            "dropped_data_tiers": sorted(DROPPED_TIERS),
            "category_order": ["pwn", "web"],
            "pwn_material_order": [
                priority_id
                for priority_id, _ in sorted(
                    PWN_PRIORITIES.items(),
                    key=lambda item: item[1][0],
                )
            ],
            "tie_breakers": [
                "known_prior_runtime_blocker_last",
                "candidate_material_tier_desc",
                "docker_closure_quality",
                "env_id",
            ],
        },
        "input": {
            "static_materials": display_path(static_materials, source_repo),
            "static_materials_sha256": file_sha256(static_materials),
            "record_count": len(rows),
            "completion_manifests": [
                display_path(path.expanduser().resolve(), source_repo)
                for path in completion_manifests
            ],
        },
        "counts": {
            "input": len(rows),
            "build": len(main),
            "deferred_d2": len(deferred),
            "completed": len(completed_rows),
            "candidate_tier_not_confirmed": len(candidate_only),
            "policy_dropped_d0_d1": sum(
                record["reason"] == "policy_drop_d0_d1" for record in excluded
            ),
            "confirmed_d0_d1_total": sum(
                record["confirmed_data_tier"] in DROPPED_TIERS
                for record in excluded
                if record["reason"] != "already_generated_r3"
            ),
            "build_with_prior_runtime_blocker": sum(
                bool(record["task"]["static_evidence"]["prior_runtime_failures"]) for record in main
            ),
            "excluded_total": len(excluded),
        },
        "build_counts_by_category": dict(
            sorted(Counter(record["task"]["category"] for record in main).items())
        ),
        "build_counts_by_data_tier": dict(
            sorted(Counter(record["task"]["data_tier"] for record in main).items())
        ),
        "build_counts_by_candidate_data_tier": dict(
            sorted(
                Counter(
                    record["task"]["data_tier_evidence"]["candidate"] for record in main
                ).items()
            )
        ),
        "build_counts_by_category_and_tier": {
            f"{category}/{tier}": count
            for (category, tier), count in sorted(
                Counter(
                    (
                        record["task"]["category"],
                        record["task"]["data_tier"],
                    )
                    for record in main
                ).items()
            )
        },
        "pwn_counts_by_material_priority": dict(
            sorted(
                Counter(
                    record["priority"]["id"]
                    for record in main
                    if record["task"]["category"] == "pwn"
                ).items(),
                key=lambda item: PWN_PRIORITIES[item[0]][0],
            )
        ),
        "image_name_collisions": collision_summary,
        "integrity": {
            "build_env_ids_sha256": canonical_sha256([record["env_id"] for record in main]),
            "deferred_env_ids_sha256": canonical_sha256([record["env_id"] for record in deferred]),
            "completed_env_ids_sha256": canonical_sha256(
                [record["env_id"] for record in completed_rows]
            ),
        },
    }
    return {
        "build": main,
        "deferred": deferred,
        "excluded": excluded,
        "completed": completed_rows,
        "candidate_only": candidate_only,
        "summary": summary,
    }


def write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    text = "".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows)
    path.write_text(text, encoding="utf-8")


def write_compact_task_lists(
    output_dir: Path,
    records: list[dict[str, Any]],
) -> None:
    (output_dir / "build_task_ids.txt").write_text(
        "".join(f"{record['env_id']}\n" for record in records),
        encoding="utf-8",
    )
    header = (
        "position\tenv_id\tcategory\tcandidate_data_tier\tconfirmed_data_tier"
        "\tmaterial_priority\tdocker_closure\tprior_runtime_blocker\timage_name\n"
    )
    lines = [header]
    for record in records:
        task = record["task"]
        lines.append(
            "\t".join(
                (
                    str(record["position"]),
                    record["env_id"],
                    task["category"],
                    task["data_tier_evidence"]["candidate"],
                    task["data_tier_evidence"]["confirmed"],
                    record["priority"]["id"],
                    task["docker_closure"]["status"],
                    str(bool(task["static_evidence"]["prior_runtime_failures"])).lower(),
                    task["image_name"],
                )
            )
            + "\n"
        )
    (output_dir / "build_tasks.tsv").write_text(
        "".join(lines),
        encoding="utf-8",
    )


def render_readme(summary: dict[str, Any]) -> str:
    counts = summary["counts"]
    category_counts = summary["build_counts_by_category"]
    priority_counts = summary["pwn_counts_by_material_priority"]
    priority_lines = "\n".join(
        f"| {priority_id} | {count} |" for priority_id, count in priority_counts.items()
    )
    return f"""# {summary["wave"]} build-target queue

This queue is generated from the {counts["input"]:,}-record Pwn/Web static-material index.
It excludes environments that already have R3 build plus CAGE launch/address/close
evidence. Only confirmed D3-D5 records enter the runnable queue. D0 and D1 are
policy-dropped, candidate-only upgrades are not treated as confirmed, and D2 is
kept outside the runnable queue.

| Bucket | Count |
|---|---:|
| Build tasks | {counts["build"]} |
| Pwn build tasks | {category_counts.get("pwn", 0)} |
| Web build tasks | {category_counts.get("web", 0)} |
| Build tasks with a known prior runtime blocker | {counts["build_with_prior_runtime_blocker"]} |
| Deferred D2 | {counts["deferred_d2"]} |
| Already generated | {counts["completed"]} |
| Candidate D3-D5 but confirmed D0/D1 | {counts["candidate_tier_not_confirmed"]} |
| Dropped D0/D1 | {counts["policy_dropped_d0_d1"]} |

Pwn ordering:

| Material priority | Count |
|---|---:|
{priority_lines}

Files:

- build_tasks.jsonl: runnable D3-D5 queue in deterministic order.
- build_tasks.tsv: compact reader-facing task list.
- build_task_ids.txt: one ordered environment ID per line.
- deferred_d2.jsonl: retained for audit, not part of the default run.
- candidate_only.jsonl: apparent D3-D5 material shapes that remain confirmed D0/D1.
- completed.jsonl: prior R3 successes removed from the queue.
- excluded.jsonl: completed plus D0/D1 policy exclusions.
- summary.json: counts, policy, source hashes, and queue ID hashes.

Each build record contains a task object that can be materialized as task.json
for the CAGE build_target benchmark. Image tags are explicit and never use latest.
"""


def write_artifacts(artifacts: dict[str, Any], output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    write_jsonl(output_dir / "build_tasks.jsonl", artifacts["build"])
    write_compact_task_lists(output_dir, artifacts["build"])
    write_jsonl(output_dir / "deferred_d2.jsonl", artifacts["deferred"])
    write_jsonl(output_dir / "candidate_only.jsonl", artifacts["candidate_only"])
    write_jsonl(output_dir / "completed.jsonl", artifacts["completed"])
    write_jsonl(output_dir / "excluded.jsonl", artifacts["excluded"])
    (output_dir / "summary.json").write_text(
        json.dumps(artifacts["summary"], ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (output_dir / "README.md").write_text(
        render_readme(artifacts["summary"]),
        encoding="utf-8",
    )


def materialize_tasks(
    records: Iterable[dict[str, Any]],
    output_dir: Path,
) -> None:
    if output_dir.exists() and any(output_dir.iterdir()):
        raise FileExistsError(f"materialized task directory is not empty: {output_dir}")
    output_dir.mkdir(parents=True, exist_ok=True)
    for record in records:
        task_dir = output_dir / record["env_id"]
        task_dir.mkdir()
        (task_dir / "task.json").write_text(
            json.dumps(record["task"], ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--static-materials", type=Path, required=True)
    parser.add_argument("--source-repo", type=Path, required=True)
    parser.add_argument(
        "--completed-manifest",
        type=Path,
        action="append",
        default=[],
        help="Repeat for every authoritative successful-build manifest.",
    )
    parser.add_argument("--wave", default="wave4")
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--materialize-dir", type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    artifacts = build_artifacts(
        static_materials=args.static_materials,
        source_repo=args.source_repo,
        completion_manifests=args.completed_manifest,
        wave=args.wave,
    )
    write_artifacts(artifacts, args.output_dir)
    if args.materialize_dir is not None:
        materialize_tasks(artifacts["build"], args.materialize_dir)
    print(json.dumps(artifacts["summary"], ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
