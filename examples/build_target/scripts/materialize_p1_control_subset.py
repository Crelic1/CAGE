#!/usr/bin/env python3
"""Select and materialize an audited AWPB/APB P1 control subset.

The canonical source of truth is ctf-env-collection's SQLite catalog:

* ``challenge_status_current`` supplies the formal material profile and route;
* one frozen v11 ``challenge_material_exports`` run supplies every local file.

No model is called and no R/X execution tier is inferred.  Selection is a
deterministic diversity-covering pass over the formal AWPB/APB population.
"""

from __future__ import annotations

import argparse
import bz2
import errno
import gzip
import hashlib
import json
import lzma
import os
import re
import shutil
import sqlite3
import struct
import subprocess
import tarfile
import zipfile
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path, PurePosixPath
from typing import Any, Iterable, Sequence

REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_SOURCE_ROOT = REPO_ROOT.parent / "ctf-env-collection"
DEFAULT_DATASET = REPO_ROOT / ".cage/build-target/p1-awpb-apb-30"
DEFAULT_ARTIFACT_ROOT = REPO_ROOT / "examples/build_target/task_lists/p1_control_30"
DEFAULT_MANIFEST = DEFAULT_ARTIFACT_ROOT / "manifest.json"
DEFAULT_REPORT = DEFAULT_ARTIFACT_ROOT / "README.md"

SCHEMA_VERSION = "cage-build-target-p1-control-subset-v1"
PROFILE_RULE = "pwn-material-profile-v2"
PLAN_SHA256 = "6930b606054cc605b461634fd34e11c7e838f5b4227b1c4a4529175715002c8e"
PROFILE_RUN_ID = (
    "pwn-material-profile:pwn-material-profile-v2:"
    "6930b606054cc605b461634f"
)
ENTITY_RULE = "pwn-material-file-classifier-v11"
ENTITY_RUN_ID = (
    "pwn-material-full:"
    "pwn-material-file-classifier-v11:"
    "ccf9eeb8f6100c25b772"
)
SELECTION_SEED = "cage-build-target-p1-awpb-apb-30-v1"

PROFILE_ROUTES = {
    "AWPB": "fast_track_full",
    "APB": "fast_track_no_writeup",
}
PROFILE_QUOTAS = {
    "AWPB": 15,
    "APB": 15,
}
EXPECTED_EXPORT_ROLES = {
    "AWPB": frozenset({"A", "W", "P", "B"}),
    "APB": frozenset({"A", "P", "B"}),
}
ROLE_DIRECTORIES = {
    "A": "attachments",
    "W": "writeups",
    "P": "exploit",
    "B": "deployment",
}
TASK_ROLE_KEYS = {
    "A": "attachments",
    "W": "writeups",
    "P": "exploit",
    "B": "deployment",
}

# Keep the observation set practical without collapsing it to tiny/easy tasks.
# The diversity policy below deliberately requests large and complex examples
# within these bounds.
MAX_MATERIAL_FILES = 256
MAX_MATERIAL_BYTES = 256 * 1024 * 1024
MAX_SINGLE_FILE_BYTES = 128 * 1024 * 1024

ARCHIVE_SUFFIXES = (
    ".tar.gz",
    ".tar.bz2",
    ".tar.xz",
    ".tar",
    ".tgz",
    ".tbz2",
    ".txz",
    ".zip",
    ".jar",
    ".war",
    ".apk",
    ".gz",
    ".bz2",
    ".xz",
    ".7z",
    ".rar",
)
SOURCE_SUFFIXES = {
    ".c",
    ".cc",
    ".cpp",
    ".cxx",
    ".h",
    ".hh",
    ".hpp",
    ".rs",
    ".go",
    ".py",
    ".sh",
    ".asm",
    ".s",
    ".java",
    ".js",
    ".ts",
}
COMPOSE_NAMES = {
    "docker-compose.yml",
    "docker-compose.yaml",
    "compose.yml",
    "compose.yaml",
}

# Marginal-coverage goals guide selection.  Required tags are a hard audit:
# every diversity family explicitly requested by the goal must appear.
COVERAGE_TARGETS = {
    "runtime:bundled_libc_loader": 4,
    "runtime:bundled_libc_only": 3,
    "runtime:system_libc": 4,
    "runtime:musl": 1,
    "runtime:static": 2,
    "exploit:stack_rop": 6,
    "exploit:heap": 4,
    "exploit:format_string": 3,
    "exploit:shellcode_seccomp": 3,
    "exploit:kernel": 1,
    "build_form:dockerfile_compose": 5,
    "build_form:dockerfile": 5,
    "build_mode:source_build": 5,
    "build_mode:prebuilt_rehost": 5,
    "build_mode:hybrid": 5,
    "topology:multi_service": 3,
    "complexity:small": 4,
    "complexity:medium": 10,
    "complexity:large": 4,
    "year_bucket:pre_2020": 2,
    "year_bucket:2020_2021": 4,
    "year_bucket:2022": 4,
    "year_bucket:2023": 4,
    "year_bucket:2024": 4,
    "year_bucket:2025_plus": 4,
}
REQUIRED_TAG_GROUPS = {
    "Dockerfile build material": {"build_form:dockerfile", "build_form:dockerfile_compose"},
    "compose build material": {"build_form:compose", "build_form:dockerfile_compose"},
    "source build": {"build_mode:source_build", "build_mode:hybrid"},
    "prebuilt binary": {"build_mode:prebuilt_rehost", "build_mode:hybrid"},
    "bundled libc and loader": {"runtime:bundled_libc_loader"},
    "bundled libc without loader": {"runtime:bundled_libc_only"},
    "system libc": {"runtime:system_libc"},
    "musl runtime": {"runtime:musl"},
    "static runtime": {"runtime:static"},
    "stack/ROP exploit": {"exploit:stack_rop"},
    "format-string exploit": {"exploit:format_string"},
    "heap exploit": {"exploit:heap"},
    "shellcode/seccomp exploit": {"exploit:shellcode_seccomp"},
    "single-service topology": {"topology:single_service"},
    "multi-service topology": {"topology:multi_service"},
}


class SubsetError(RuntimeError):
    """The source or generated subset violates the frozen contract."""


def profile_quotas_for_count(count: int) -> dict[str, int]:
    """Return the balanced AWPB/APB quotas for one control subset size."""

    if count <= 0 or count % 2:
        raise SubsetError(
            f"control subset count must be a positive even integer, got {count}"
        )
    return {"AWPB": count // 2, "APB": count // 2}


def expected_task_count() -> int:
    return sum(PROFILE_QUOTAS.values())


@dataclass(frozen=True)
class Material:
    challenge_id: str
    role: str
    logical_path: str
    source_kind: str
    file_kind: str
    size: int
    artifact_sha256: str
    storage_root_id: str
    export_relative_path: str
    export_state: str
    source_path: Path
    dataset_path: str

    def manifest_record(self) -> dict[str, Any]:
        return {
            "role": self.role,
            "logical_path": self.logical_path,
            "source_kind": self.source_kind,
            "file_kind": self.file_kind,
            "size": self.size,
            "sha256": self.artifact_sha256,
            "storage_root_id": self.storage_root_id,
            "source_relative_path": self.export_relative_path,
            "dataset_path": self.dataset_path,
        }


@dataclass
class Candidate:
    challenge_id: str
    dataset_abbr: str
    event: str
    year: str
    title: str
    source_repo: str
    source_reference: str
    source_path: str
    origin_repo_hint: str
    profile: str
    route: str
    status_source_run_id: str
    profile_evidence: dict[str, Any]
    role_states: dict[str, str]
    materials: list[Material] = field(default_factory=list)
    tags: set[str] = field(default_factory=set)
    feature_details: dict[str, Any] = field(default_factory=dict)
    material_fingerprint: str = ""
    selection_reason: list[str] = field(default_factory=list)

    @property
    def total_bytes(self) -> int:
        return sum(material.size for material in self.materials)

    @property
    def material_count(self) -> int:
        return len(self.materials)

    @property
    def source_label(self) -> str:
        return self.origin_repo_hint or self.source_repo or self.dataset_abbr


def json_dumps(value: Any, *, pretty: bool = True) -> str:
    if pretty:
        return json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def stable_hash(seed: str, *parts: object) -> int:
    body = "\0".join((seed, *(str(part) for part in parts)))
    return int(hashlib.sha256(body.encode()).hexdigest(), 16)


def connect_readonly(path: Path) -> sqlite3.Connection:
    if not path.is_file():
        raise FileNotFoundError(f"canonical catalog is missing: {path}")
    uri = f"{path.resolve().as_uri()}?mode=ro"
    connection = sqlite3.connect(uri, uri=True, timeout=60)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA query_only=ON")
    connection.execute("PRAGMA busy_timeout=60000")
    return connection


def parse_json(value: Any) -> dict[str, Any]:
    try:
        parsed = json.loads(value or "{}")
    except (TypeError, json.JSONDecodeError) as exc:
        raise SubsetError("canonical database contains malformed evidence_json") from exc
    if not isinstance(parsed, dict):
        raise SubsetError("canonical evidence_json must be an object")
    return parsed


def git_head(path: Path) -> str:
    result = subprocess.run(
        ["git", "-C", str(path), "rev-parse", "HEAD"],
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def source_metadata(
    connection: sqlite3.Connection,
    source_root: Path,
) -> dict[str, Any]:
    profile_run = connection.execute(
        """
        SELECT status,row_count,started_at,completed_at,metadata_json
        FROM ingest_runs WHERE ingest_run_id=?
        """,
        (PROFILE_RUN_ID,),
    ).fetchone()
    entity_run = connection.execute(
        """
        SELECT status,row_count,started_at,completed_at,metadata_json
        FROM ingest_runs WHERE ingest_run_id=?
        """,
        (ENTITY_RUN_ID,),
    ).fetchone()
    if profile_run is None or str(profile_run["status"]) != "complete":
        raise SubsetError(f"formal profile run is missing/incomplete: {PROFILE_RUN_ID}")
    if entity_run is None or str(entity_run["status"]) != "complete":
        raise SubsetError(f"entity export run is missing/incomplete: {ENTITY_RUN_ID}")

    profile_meta = parse_json(profile_run["metadata_json"])
    entity_meta = parse_json(entity_run["metadata_json"])
    if profile_meta.get("rule_version") != PROFILE_RULE:
        raise SubsetError("formal profile rule version differs from frozen contract")
    if profile_meta.get("plan_sha256") != PLAN_SHA256:
        raise SubsetError("formal profile plan SHA differs from frozen contract")
    if entity_meta.get("rule_version") != ENTITY_RULE:
        raise SubsetError("entity rule version differs from frozen contract")

    active_count = int(
        connection.execute(
            """
            SELECT COUNT(*) FROM challenges
            WHERE category='pwn' AND excluded=0 AND canonical_challenge_id IS NULL
            """
        ).fetchone()[0]
    )
    profile_counts = {
        str(row["state"]): int(row["count"])
        for row in connection.execute(
            """
            SELECT status.state,COUNT(*) AS count
            FROM challenge_status_current AS status
            JOIN challenges USING(challenge_id)
            WHERE status.status_domain='static_material_profile'
              AND challenges.category='pwn'
              AND challenges.excluded=0
              AND challenges.canonical_challenge_id IS NULL
            GROUP BY status.state
            ORDER BY status.state
            """
        )
    }
    if active_count != 6683:
        raise SubsetError(f"active canonical Pwn count drifted: {active_count} != 6683")
    if profile_counts.get("AWPB") != 762 or profile_counts.get("APB") != 1376:
        raise SubsetError(f"AWPB/APB population drifted: {profile_counts}")

    schema_version = int(
        connection.execute("SELECT MAX(schema_version) FROM schema_info").fetchone()[0]
    )
    return {
        "repository": "ctf-env-collection",
        "repository_commit": git_head(source_root),
        "database": "catalog/ctf_index.sqlite3",
        "database_schema_version": schema_version,
        "active_canonical_pwn_count": active_count,
        "profile_counts": profile_counts,
        "profile_rule": PROFILE_RULE,
        "profile_plan_sha256": PLAN_SHA256,
        "profile_run_id": PROFILE_RUN_ID,
        "profile_run_completed_at": str(profile_run["completed_at"]),
        "entity_rule": ENTITY_RULE,
        "entity_run_id": ENTITY_RUN_ID,
        "entity_run_completed_at": str(entity_run["completed_at"]),
        "entity_row_count": int(entity_run["row_count"]),
        "entity_selection_sha256": str(entity_meta.get("selection_sha256") or ""),
    }


def storage_roots(
    connection: sqlite3.Connection,
    source_root: Path,
) -> dict[str, Path]:
    roots: dict[str, Path] = {}
    for row in connection.execute("SELECT root_id,locator FROM storage_roots"):
        locator = Path(str(row["locator"]))
        roots[str(row["root_id"])] = (
            locator if locator.is_absolute() else source_root / locator
        )
    return roots


def safe_relative_path(value: str) -> PurePosixPath:
    path = PurePosixPath(value.replace("\\", "/"))
    if path.is_absolute() or any(part in {"", ".", ".."} for part in path.parts):
        raise SubsetError(f"unsafe relative material path: {value!r}")
    return path


def dataset_path_for(
    challenge_id: str,
    role: str,
    export_relative_path: str,
) -> str:
    relative = safe_relative_path(export_relative_path)
    parts = list(relative.parts)
    try:
        challenge_position = parts.index(challenge_id)
    except ValueError as exc:
        raise SubsetError(
            f"entity export path does not contain challenge id {challenge_id}: "
            f"{export_relative_path}"
        ) from exc
    tail = parts[challenge_position + 1 :]
    if tail and tail[0] in {"public", "writeups", "solve", "build"}:
        tail = tail[1:]
    if not tail:
        raise SubsetError(f"entity export has no file tail: {export_relative_path}")
    destination = PurePosixPath("materials", ROLE_DIRECTORIES[role], *tail)
    return destination.as_posix()


def load_candidates(
    connection: sqlite3.Connection,
    source_root: Path,
) -> tuple[list[Candidate], Counter[str]]:
    candidates: dict[str, Candidate] = {}
    rows = connection.execute(
        """
        SELECT challenge.challenge_id,challenge.dataset_abbr,
               challenge.event,challenge.year,challenge.title,
               challenge.source_repo,challenge.source_reference,
               challenge.source_path,challenge.origin_repo_hint,
               profile.state AS profile,route.state AS route,
               profile.is_formal,profile.source_run_id,profile.evidence_json,
               attachment.state AS attachment_state,
               writeup.state AS writeup_state,
               exploit.state AS exploit_state,
               build.state AS build_state
        FROM challenges AS challenge
        JOIN challenge_status_current AS profile
          ON profile.challenge_id=challenge.challenge_id
         AND profile.status_domain='static_material_profile'
        JOIN challenge_status_current AS route
          ON route.challenge_id=challenge.challenge_id
         AND route.status_domain='static_material_pipeline_route'
        JOIN challenge_status_current AS attachment
          ON attachment.challenge_id=challenge.challenge_id
         AND attachment.status_domain='static_material_attachment'
        JOIN challenge_status_current AS writeup
          ON writeup.challenge_id=challenge.challenge_id
         AND writeup.status_domain='static_material_writeup'
        JOIN challenge_status_current AS exploit
          ON exploit.challenge_id=challenge.challenge_id
         AND exploit.status_domain='static_material_exploit'
        JOIN challenge_status_current AS build
          ON build.challenge_id=challenge.challenge_id
         AND build.status_domain='static_material_build'
        WHERE challenge.category='pwn'
          AND challenge.excluded=0
          AND challenge.canonical_challenge_id IS NULL
          AND profile.state IN ('AWPB','APB')
        ORDER BY challenge.challenge_id
        """
    )
    for row in rows:
        profile = str(row["profile"])
        route = str(row["route"])
        evidence = parse_json(row["evidence_json"])
        if int(row["is_formal"]) != 1:
            raise SubsetError(f"non-formal profile in eligible pool: {row['challenge_id']}")
        if route != PROFILE_ROUTES[profile]:
            raise SubsetError(
                f"profile/route mismatch for {row['challenge_id']}: {profile}/{route}"
            )
        if str(row["source_run_id"]) != PROFILE_RUN_ID:
            raise SubsetError(
                f"profile source run mismatch for {row['challenge_id']}"
            )
        if (
            evidence.get("rule_version") != PROFILE_RULE
            or evidence.get("plan_sha256") != PLAN_SHA256
        ):
            raise SubsetError(
                f"profile evidence mismatch for {row['challenge_id']}"
            )
        role_states = {
            "attachment": str(row["attachment_state"]),
            "writeup": str(row["writeup_state"]),
            "exploit": str(row["exploit_state"]),
            "build": str(row["build_state"]),
        }
        required_local_roles = {"attachment", "exploit", "build"}
        if profile == "AWPB":
            required_local_roles.add("writeup")
        invalid_local = {
            role: role_states[role]
            for role in required_local_roles
            if role_states[role] != "confirmed_local"
        }
        # APB means no *local* W.  It may still retain confirmed_remote or
        # candidate writeup evidence without gaining the W profile letter.
        invalid_nonlocal_writeup = (
            profile == "APB" and role_states["writeup"] == "confirmed_local"
        )
        if invalid_local or invalid_nonlocal_writeup:
            raise SubsetError(
                f"formal role states contradict {profile} for "
                f"{row['challenge_id']}: {role_states}"
            )
        challenge_id = str(row["challenge_id"])
        candidates[challenge_id] = Candidate(
            challenge_id=challenge_id,
            dataset_abbr=str(row["dataset_abbr"] or ""),
            event=str(row["event"] or ""),
            year=str(row["year"] or ""),
            title=str(row["title"] or ""),
            source_repo=str(row["source_repo"] or ""),
            source_reference=str(row["source_reference"] or ""),
            source_path=str(row["source_path"] or ""),
            origin_repo_hint=str(row["origin_repo_hint"] or ""),
            profile=profile,
            route=route,
            status_source_run_id=str(row["source_run_id"]),
            profile_evidence=evidence,
            role_states=role_states,
        )

    roots = storage_roots(connection, source_root)
    material_rows = connection.execute(
        """
        SELECT file.challenge_id,export.role,file.logical_path,file.source_kind,
               file.file_kind,file.size,file.artifact_sha256,
               export.storage_root_id,export.relative_path,export.export_state
        FROM challenge_material_exports AS export
        JOIN challenge_material_files AS file USING(material_file_id)
        JOIN challenge_status_current AS profile
          ON profile.challenge_id=file.challenge_id
         AND profile.status_domain='static_material_profile'
        JOIN challenges AS challenge ON challenge.challenge_id=file.challenge_id
        WHERE export.source_run_id=?
          AND profile.state IN ('AWPB','APB')
          AND challenge.category='pwn'
          AND challenge.excluded=0
          AND challenge.canonical_challenge_id IS NULL
        ORDER BY file.challenge_id,export.role,export.relative_path
        """,
        (ENTITY_RUN_ID,),
    )
    for row in material_rows:
        challenge_id = str(row["challenge_id"])
        candidate = candidates.get(challenge_id)
        if candidate is None:
            raise SubsetError(f"entity export references non-pool task: {challenge_id}")
        role = str(row["role"])
        if role not in ROLE_DIRECTORIES:
            raise SubsetError(f"invalid entity role for {challenge_id}: {role}")
        root_id = str(row["storage_root_id"])
        if root_id not in roots:
            raise SubsetError(f"unknown storage root {root_id!r}")
        export_relative = str(row["relative_path"])
        source_path = roots[root_id] / safe_relative_path(export_relative)
        candidate.materials.append(
            Material(
                challenge_id=challenge_id,
                role=role,
                logical_path=str(row["logical_path"]),
                source_kind=str(row["source_kind"] or ""),
                file_kind=str(row["file_kind"] or ""),
                size=int(row["size"]),
                artifact_sha256=str(row["artifact_sha256"]),
                storage_root_id=root_id,
                export_relative_path=export_relative,
                export_state=str(row["export_state"]),
                source_path=source_path,
                dataset_path=dataset_path_for(
                    challenge_id, role, export_relative
                ),
            )
        )

    rejected: Counter[str] = Counter()
    eligible: list[Candidate] = []
    for candidate in candidates.values():
        reason = eligibility_failure(candidate)
        if reason:
            rejected[reason] += 1
            continue
        classify_candidate(candidate)
        eligible.append(candidate)
    return eligible, rejected


def eligibility_failure(candidate: Candidate) -> str | None:
    if not candidate.event or not candidate.year:
        return "missing_event_or_year"
    if not candidate.source_label or not candidate.source_reference:
        return "missing_source_provenance"
    roles = {material.role for material in candidate.materials}
    if roles != EXPECTED_EXPORT_ROLES[candidate.profile]:
        return "entity_role_set_mismatch"
    if not candidate.materials:
        return "no_material_files"
    if candidate.material_count > MAX_MATERIAL_FILES:
        return "too_many_material_files"
    if candidate.total_bytes > MAX_MATERIAL_BYTES:
        return "material_bytes_over_limit"
    destinations: set[str] = set()
    fingerprint = hashlib.sha256()
    for material in candidate.materials:
        if material.export_state not in {"hardlinked", "already_hardlinked"}:
            return "entity_export_not_materialized"
        if material.size <= 0:
            return "empty_material_file"
        if material.size > MAX_SINGLE_FILE_BYTES:
            return "single_file_over_limit"
        if material.dataset_path in destinations:
            return "dataset_path_collision"
        destinations.add(material.dataset_path)
        try:
            stat_result = material.source_path.stat()
        except OSError:
            return "missing_or_unreadable_material"
        if not material.source_path.is_file() or not os.access(
            material.source_path, os.R_OK
        ):
            return "missing_or_unreadable_material"
        if stat_result.st_size != material.size:
            return "material_size_mismatch"
        fingerprint.update(material.role.encode())
        fingerprint.update(b"\0")
        fingerprint.update(material.artifact_sha256.encode())
        fingerprint.update(b"\0")
        fingerprint.update(material.dataset_path.encode())
        fingerprint.update(b"\n")
    candidate.material_fingerprint = fingerprint.hexdigest()
    return None


def read_prefix(path: Path, limit: int = 512 * 1024) -> bytes:
    with path.open("rb") as handle:
        return handle.read(limit)


def elf_metadata(path: Path) -> dict[str, Any] | None:
    """Read just enough ELF structure to find PT_INTERP deterministically."""

    try:
        header = read_prefix(path, 64)
    except OSError:
        return None
    if len(header) < 52 or header[:4] != b"\x7fELF":
        return None
    elf_class = header[4]
    data_encoding = header[5]
    if elf_class not in {1, 2} or data_encoding not in {1, 2}:
        return {"is_elf": True, "interpreter": None, "static": False}
    endian = "<" if data_encoding == 1 else ">"
    try:
        elf_type = struct.unpack_from(endian + "H", header, 16)[0]
        if elf_class == 1:
            ph_offset = struct.unpack_from(endian + "I", header, 28)[0]
            ph_entry_size = struct.unpack_from(endian + "H", header, 42)[0]
            ph_count = struct.unpack_from(endian + "H", header, 44)[0]
        else:
            ph_offset = struct.unpack_from(endian + "Q", header, 32)[0]
            ph_entry_size = struct.unpack_from(endian + "H", header, 54)[0]
            ph_count = struct.unpack_from(endian + "H", header, 56)[0]
        table_size = ph_entry_size * ph_count
        if (
            ph_entry_size <= 0
            or ph_count > 8192
            or table_size > 8 * 1024 * 1024
        ):
            return {"is_elf": True, "interpreter": None, "static": False}
        with path.open("rb") as handle:
            handle.seek(ph_offset)
            table = handle.read(table_size)
            for index in range(ph_count):
                offset = index * ph_entry_size
                if offset + ph_entry_size > len(table):
                    break
                program_type = struct.unpack_from(endian + "I", table, offset)[0]
                if program_type != 3:  # PT_INTERP
                    continue
                if elf_class == 1:
                    interp_offset = struct.unpack_from(
                        endian + "I", table, offset + 4
                    )[0]
                    interp_size = struct.unpack_from(
                        endian + "I", table, offset + 16
                    )[0]
                else:
                    interp_offset = struct.unpack_from(
                        endian + "Q", table, offset + 8
                    )[0]
                    interp_size = struct.unpack_from(
                        endian + "Q", table, offset + 32
                    )[0]
                if interp_size <= 0 or interp_size > 4096:
                    break
                handle.seek(interp_offset)
                interpreter = (
                    handle.read(interp_size)
                    .split(b"\0", 1)[0]
                    .decode("utf-8", "replace")
                )
                return {
                    "is_elf": True,
                    "interpreter": interpreter,
                    "static": False,
                }
    except (OSError, struct.error):
        return {"is_elf": True, "interpreter": None, "static": False}
    return {
        "is_elf": True,
        "interpreter": None,
        "static": elf_type in {2, 3},
    }


def text_sample(materials: Iterable[Material], limit: int = 2 * 1024 * 1024) -> str:
    chunks: list[str] = []
    remaining = limit
    for material in materials:
        if remaining <= 0:
            break
        suffix = PurePosixPath(material.logical_path).suffix.casefold()
        if suffix not in {
            ".py",
            ".c",
            ".cc",
            ".cpp",
            ".rb",
            ".pl",
            ".sh",
            ".js",
            ".ts",
            ".md",
            ".txt",
        }:
            continue
        try:
            body = read_prefix(material.source_path, min(remaining, 512 * 1024))
        except OSError:
            continue
        remaining -= len(body)
        chunks.append(body.decode("utf-8", "ignore"))
    return "\n".join(chunks).casefold()


def compose_service_count(path: Path) -> int:
    try:
        text = read_prefix(path, 2 * 1024 * 1024).decode("utf-8", "ignore")
    except OSError:
        return 0
    lines = text.splitlines()
    for index, line in enumerate(lines):
        match = re.match(r"^(\s*)services\s*:\s*(?:#.*)?$", line)
        if not match:
            continue
        base_indent = len(match.group(1).replace("\t", "    "))
        candidates: list[tuple[int, str]] = []
        for child in lines[index + 1 :]:
            if not child.strip() or child.lstrip().startswith("#"):
                continue
            indent = len(child) - len(child.lstrip(" "))
            if indent <= base_indent:
                break
            key = re.match(r"^\s+([A-Za-z0-9_.-]+)\s*:\s*(?:#.*)?$", child)
            if key:
                candidates.append((indent, key.group(1)))
        if not candidates:
            return 0
        service_indent = min(indent for indent, _ in candidates)
        return len({key for indent, key in candidates if indent == service_indent})
    return 0


def year_bucket(year: str) -> str:
    try:
        value = int(year)
    except ValueError:
        return "unknown"
    if value < 2020:
        return "pre_2020"
    if value <= 2021:
        return "2020_2021"
    if value == 2022:
        return "2022"
    if value == 2023:
        return "2023"
    if value == 2024:
        return "2024"
    return "2025_plus"


def classify_candidate(candidate: Candidate) -> None:
    paths = [
        f"{material.logical_path} {material.export_relative_path}".casefold()
        for material in candidate.materials
    ]
    b_materials = [item for item in candidate.materials if item.role == "B"]
    a_materials = [item for item in candidate.materials if item.role == "A"]
    p_materials = [item for item in candidate.materials if item.role == "P"]

    has_dockerfile = any(
        re.fullmatch(r"dockerfile(?:\..+)?", PurePosixPath(item.logical_path).name, re.I)
        for item in b_materials
    )
    compose_materials = [
        item
        for item in b_materials
        if PurePosixPath(item.logical_path).name.casefold() in COMPOSE_NAMES
    ]
    has_compose = bool(compose_materials)
    if has_dockerfile and has_compose:
        build_form = "dockerfile_compose"
    elif has_dockerfile:
        build_form = "dockerfile"
    elif has_compose:
        build_form = "compose"
    else:
        build_form = "build_metadata"

    has_source_build = any(
        item.file_kind in {"source", "build_metadata"}
        or PurePosixPath(item.logical_path).suffix.casefold() in SOURCE_SUFFIXES
        or PurePosixPath(item.logical_path).name.casefold()
        in {"makefile", "cmakelists.txt", "build.sh"}
        for item in b_materials
    )
    primary_elfs: list[tuple[Material, dict[str, Any]]] = []
    for item in a_materials:
        basename = PurePosixPath(item.logical_path).name.casefold()
        if (
            basename.startswith("libc")
            or basename.startswith("ld-")
            or basename.startswith("ld-linux")
            or ".so" in basename
        ):
            continue
        metadata = elf_metadata(item.source_path)
        if metadata:
            primary_elfs.append((item, metadata))
    has_prebuilt = bool(primary_elfs)
    if has_source_build and has_prebuilt:
        build_mode = "hybrid"
    elif has_source_build:
        build_mode = "source_build"
    elif has_prebuilt:
        build_mode = "prebuilt_rehost"
    else:
        build_mode = "nonstandard"

    has_libc = any(
        re.search(r"(?:^|/)(?:libc(?:[-_.][^/]*)?\.so(?:\.\d+)?)$", path)
        for path in paths
    )
    has_loader = any(
        re.search(
            r"(?:^|/)(?:ld-linux[^/]*\.so(?:\.\d+)?|ld-[0-9.]+\.so)$",
            path,
        )
        for path in paths
    )
    interpreters = sorted(
        {
            str(metadata["interpreter"])
            for _, metadata in primary_elfs
            if metadata.get("interpreter")
        }
    )
    has_musl = any("musl" in path for path in paths + interpreters)
    has_static = any(metadata.get("static") for _, metadata in primary_elfs)
    if has_musl:
        runtime_form = "musl"
    elif has_libc and has_loader:
        runtime_form = "bundled_libc_loader"
    elif has_libc:
        runtime_form = "bundled_libc_only"
    elif has_loader:
        runtime_form = "bundled_loader_only"
    elif has_static:
        runtime_form = "static"
    elif interpreters:
        runtime_form = "system_libc"
    else:
        runtime_form = "unknown_or_non_elf"

    exploit_text = text_sample(p_materials)
    path_and_title = " ".join(
        (candidate.title.casefold(), " ".join(paths))
    )
    signal_text = " ".join(
        (
            path_and_title,
            exploit_text,
        )
    )
    exploit_classes: set[str] = set()
    exploit_class_evidence: dict[str, list[str]] = {}

    kernel_evidence: list[str] = []
    if re.search(r"(?:^|[/_.-])(?:bzimage|vmlinux)(?:$|[/_.-])", path_and_title):
        kernel_evidence.append("bzImage/vmlinux material")
    if re.search(r"(?:^|/)[^/]+\.ko(?:$|/)", path_and_title):
        kernel_evidence.append("kernel module material")
    if "kernel" in candidate.title.casefold():
        kernel_evidence.append("kernel in canonical title")
    if re.search(r"\b(?:commit_creds|prepare_kernel_cred|modprobe_path)\b", exploit_text):
        kernel_evidence.append("kernel privilege primitive in exploit")
    if re.search(r"/dev/[a-z0-9_.-]+", exploit_text) and re.search(
        r"\bioctl\s*\(", exploit_text
    ):
        kernel_evidence.append("device ioctl exploit")
    if kernel_evidence:
        exploit_classes.add("kernel")
        exploit_class_evidence["kernel"] = kernel_evidence

    heap_evidence: list[str] = []
    for pattern, label in (
        (r"\bheap\b", "heap marker"),
        (r"\btcache\b", "tcache primitive"),
        (r"\bfastbin\b", "fastbin primitive"),
        (r"\bunsortedbin\b", "unsorted-bin primitive"),
        (r"(?:malloc_hook|free_hook)", "allocator hook"),
        (r"\bhouse[ _.-]of\b", "House-of technique"),
    ):
        if re.search(pattern, signal_text):
            heap_evidence.append(label)
    if heap_evidence:
        exploit_classes.add("heap")
        exploit_class_evidence["heap"] = sorted(set(heap_evidence))

    format_evidence: list[str] = []
    for pattern, label in (
        (r"fmtstr_payload", "pwntools fmtstr_payload"),
        (r"format[._ -]string", "format-string marker"),
        (r"%[0-9$.*]*n\b", "%n write"),
        (r"(?:printf@got|printf_got)", "printf GOT target"),
    ):
        if re.search(pattern, signal_text):
            format_evidence.append(label)
    if format_evidence:
        exploit_classes.add("format_string")
        exploit_class_evidence["format_string"] = sorted(set(format_evidence))

    shellcode_evidence: list[str] = []
    for pattern, label in (
        (r"\bshellcraft\b", "pwntools shellcraft"),
        (r"\bseccomp\b", "seccomp constraint"),
        (r"(?:sigreturn|\bsrop\b)", "sigreturn/SROP"),
        (r"\basm\s*\(", "assembled payload"),
        (r"\bshellcode\b", "shellcode marker"),
        (r"\borw\b", "open-read-write chain"),
        (r"\bopenat\b", "openat syscall"),
    ):
        if re.search(pattern, signal_text):
            shellcode_evidence.append(label)
    if shellcode_evidence:
        exploit_classes.add("shellcode_seccomp")
        exploit_class_evidence["shellcode_seccomp"] = sorted(
            set(shellcode_evidence)
        )

    stack_evidence: list[str] = []
    for pattern, label in (
        (r"\brop\s*\(", "pwntools ROP"),
        (r"\brop\.", "ROP object"),
        (r"\bret2[a-z0-9_]*\b", "ret2 technique"),
        (r"pop[_ -]rdi", "pop-rdi gadget"),
        (r"\bcyclic(?:_find)?\b", "cyclic offset"),
        (r"stack[._ -]pivot", "stack pivot"),
        (r"buffer[._ -]overflow", "buffer overflow"),
        (r"\bropchain\b", "ROP chain"),
    ):
        if re.search(pattern, signal_text):
            stack_evidence.append(label)
    if stack_evidence:
        exploit_classes.add("stack_rop")
        exploit_class_evidence["stack_rop"] = sorted(set(stack_evidence))

    vm_evidence: list[str] = []
    for pattern, label in (
        (r"\bqemu\b", "QEMU marker"),
        (r"\bwasm\b", "WASM marker"),
        (r"\bv8\b", "V8 marker"),
        (r"\bjavascriptcore\b", "JavaScriptCore marker"),
        (r"\bbytecode\b", "bytecode marker"),
        (r"virtual[._ -]machine", "virtual-machine marker"),
    ):
        if re.search(pattern, signal_text):
            vm_evidence.append(label)
    if vm_evidence:
        exploit_classes.add("vm_emulator")
        exploit_class_evidence["vm_emulator"] = sorted(set(vm_evidence))
    if not exploit_classes:
        exploit_classes.add("other")
        exploit_class_evidence["other"] = ["no strong taxonomy signal"]

    service_counts = [
        compose_service_count(item.source_path) for item in compose_materials
    ]
    max_services = max(service_counts, default=1)
    topology = "multi_service" if max_services >= 2 else "single_service"

    if candidate.total_bytes < 1024 * 1024 and candidate.material_count < 32:
        complexity = "small"
    elif candidate.total_bytes >= 16 * 1024 * 1024 or candidate.material_count >= 96:
        complexity = "large"
    else:
        complexity = "medium"

    bucket = year_bucket(candidate.year)
    source_kinds = sorted({item.source_kind for item in candidate.materials})
    candidate.tags = {
        f"runtime:{runtime_form}",
        f"build_form:{build_form}",
        f"build_mode:{build_mode}",
        f"topology:{topology}",
        f"complexity:{complexity}",
        f"year_bucket:{bucket}",
        *(f"exploit:{value}" for value in exploit_classes),
        *(f"source_kind:{value}" for value in source_kinds),
    }
    candidate.feature_details = {
        "build_form": build_form,
        "build_mode": build_mode,
        "runtime_form": runtime_form,
        "runtime_interpreters": interpreters,
        "exploit_classes": sorted(exploit_classes),
        "exploit_class_evidence": exploit_class_evidence,
        "topology": topology,
        "compose_service_count": max_services if has_compose else 0,
        "complexity": complexity,
        "year_bucket": bucket,
        "source_kinds": source_kinds,
        "primary_elf_paths": [
            item.logical_path for item, _ in primary_elfs
        ],
        "has_bundled_libc": has_libc,
        "has_bundled_loader": has_loader,
    }


def tag_weight(tag: str) -> int:
    if tag.startswith("runtime:") or tag.startswith("exploit:"):
        return 40
    if tag.startswith("build_") or tag.startswith("topology:"):
        return 25
    if tag.startswith("year_bucket:"):
        return 15
    if tag.startswith("complexity:"):
        return 12
    if tag.startswith("source_kind:"):
        return 5
    return 1


def choose_subset(
    candidates: Sequence[Candidate],
    *,
    seed: str,
    excluded_ids: set[str] | None = None,
) -> list[Candidate]:
    excluded_ids = excluded_ids or set()
    pool = [
        candidate
        for candidate in candidates
        if candidate.challenge_id not in excluded_ids
    ]
    by_profile: dict[str, list[Candidate]] = defaultdict(list)
    for candidate in pool:
        by_profile[candidate.profile].append(candidate)
    for profile, quota in PROFILE_QUOTAS.items():
        if len(by_profile[profile]) < quota:
            raise SubsetError(
                f"only {len(by_profile[profile])} eligible {profile} tasks for quota {quota}"
            )

    selected: list[Candidate] = []
    selected_ids: set[str] = set()
    selected_fingerprints: set[str] = set()
    used_events: Counter[str] = Counter()
    used_years: Counter[str] = Counter()
    used_sources: Counter[str] = Counter()
    coverage: Counter[str] = Counter()
    profile_schedule = [
        profile
        for _ in range(max(PROFILE_QUOTAS.values()))
        for profile in ("AWPB", "APB")
        if _ < PROFILE_QUOTAS[profile]
    ]

    for profile in profile_schedule:
        available = [
            candidate
            for candidate in by_profile[profile]
            if candidate.challenge_id not in selected_ids
            and candidate.material_fingerprint not in selected_fingerprints
        ]
        unique_event = [
            candidate for candidate in available if not used_events[candidate.event.casefold()]
        ]
        if unique_event:
            available = unique_event
        if not available:
            raise SubsetError(f"no selectable candidate remains for {profile}")

        def score(candidate: Candidate) -> tuple[int, int]:
            marginal = 0
            for tag in candidate.tags:
                target = COVERAGE_TARGETS.get(tag, 0)
                if coverage[tag] < target:
                    marginal += tag_weight(tag) * (target - coverage[tag])
                elif tag.startswith("source_kind:") and coverage[tag] == 0:
                    marginal += tag_weight(tag)
            if not used_events[candidate.event.casefold()]:
                marginal += 250
            if not used_years[candidate.year]:
                marginal += 30
            if not used_sources[candidate.source_label.casefold()]:
                marginal += 100
            # Prefer the less represented exact value even after its global
            # minimum has been met, without making size an "easy task" proxy.
            for prefix in (
                "runtime:",
                "exploit:",
                "build_form:",
                "build_mode:",
                "topology:",
                "complexity:",
            ):
                values = [tag for tag in candidate.tags if tag.startswith(prefix)]
                marginal += sum(max(0, 10 - coverage[tag]) for tag in values)
            return (
                marginal,
                stable_hash(seed, profile, candidate.challenge_id),
            )

        chosen = max(available, key=score)
        reason_tags = [
            tag
            for tag in sorted(chosen.tags)
            if COVERAGE_TARGETS.get(tag, 0) > coverage[tag]
        ]
        reasons = [f"fills {tag}" for tag in reason_tags]
        if not used_events[chosen.event.casefold()]:
            reasons.append(f"adds event {chosen.event}")
        if not used_years[chosen.year]:
            reasons.append(f"adds year {chosen.year or 'unknown'}")
        if not used_sources[chosen.source_label.casefold()]:
            reasons.append(f"adds source {chosen.source_label}")
        chosen.selection_reason = reasons or [
            "deterministic tie-break after diversity targets"
        ]
        selected.append(chosen)
        selected_ids.add(chosen.challenge_id)
        selected_fingerprints.add(chosen.material_fingerprint)
        used_events[chosen.event.casefold()] += 1
        used_years[chosen.year] += 1
        used_sources[chosen.source_label.casefold()] += 1
        coverage.update(chosen.tags)

    validate_selection_shape(selected)
    return selected


def validate_selection_shape(selected: Sequence[Candidate]) -> None:
    expected_count = expected_task_count()
    if len(selected) != expected_count:
        raise SubsetError(
            f"selection has {len(selected)} tasks, expected {expected_count}"
        )
    profile_counts = Counter(candidate.profile for candidate in selected)
    if dict(profile_counts) != PROFILE_QUOTAS:
        raise SubsetError(
            f"selection profile quotas differ: {dict(profile_counts)} != {PROFILE_QUOTAS}"
        )
    ids = [candidate.challenge_id for candidate in selected]
    if len(ids) != len(set(ids)):
        raise SubsetError("selection contains duplicate challenge IDs")
    fingerprints = [candidate.material_fingerprint for candidate in selected]
    if len(fingerprints) != len(set(fingerprints)):
        raise SubsetError("selection contains duplicate material fingerprints")
    for candidate in selected:
        if candidate.route != PROFILE_ROUTES[candidate.profile]:
            raise SubsetError(
                f"selected profile/route mismatch: {candidate.challenge_id}"
            )

    selected_tags = set().union(*(candidate.tags for candidate in selected))
    missing = [
        label
        for label, options in REQUIRED_TAG_GROUPS.items()
        if not (selected_tags & options)
    ]
    if missing:
        raise SubsetError(
            "selection misses required diversity groups: " + ", ".join(missing)
        )


def archive_kind(path: Path) -> str | None:
    lower = path.name.casefold()
    for suffix in ARCHIVE_SUFFIXES:
        if lower.endswith(suffix):
            return suffix
    return None


def validate_archive(path: Path) -> str | None:
    kind = archive_kind(path)
    if kind is None:
        return None
    try:
        if kind in {".zip", ".jar", ".war", ".apk"}:
            with zipfile.ZipFile(path) as archive:
                bad = archive.testzip()
                if bad is not None:
                    return f"zip member failed CRC: {bad}"
            return None
        if kind in {".tar", ".tar.gz", ".tar.bz2", ".tar.xz", ".tgz", ".tbz2", ".txz"}:
            with tarfile.open(path, mode="r:*") as archive:
                for member in archive:
                    if member.isfile():
                        handle = archive.extractfile(member)
                        if handle is not None:
                            while handle.read(8 * 1024 * 1024):
                                pass
            return None
        if kind == ".gz":
            with gzip.open(path, "rb") as handle:
                while handle.read(8 * 1024 * 1024):
                    pass
            return None
        if kind == ".bz2":
            with bz2.open(path, "rb") as handle:
                while handle.read(8 * 1024 * 1024):
                    pass
            return None
        if kind == ".xz":
            with lzma.open(path, "rb") as handle:
                while handle.read(8 * 1024 * 1024):
                    pass
            return None
        if kind in {".7z", ".rar"}:
            seven_zip = shutil.which("7z") or shutil.which("7zz")
            if seven_zip is None:
                return f"cannot validate {kind}: 7z/7zz is unavailable"
            result = subprocess.run(
                [seven_zip, "t", "-bd", "-y", str(path)],
                capture_output=True,
                text=True,
            )
            if result.returncode:
                return f"7z test failed with rc={result.returncode}"
            return None
    except (OSError, EOFError, tarfile.TarError, zipfile.BadZipFile, lzma.LZMAError) as exc:
        return f"{type(exc).__name__}: {exc}"
    return f"unsupported archive validator for {kind}"


def deep_validate(candidate: Candidate) -> list[str]:
    failures: list[str] = []
    for material in candidate.materials:
        actual_sha = sha256_file(material.source_path)
        if actual_sha != material.artifact_sha256:
            failures.append(
                f"{material.logical_path}: sha256 {actual_sha} != "
                f"{material.artifact_sha256}"
            )
        archive_failure = validate_archive(material.source_path)
        if archive_failure:
            failures.append(f"{material.logical_path}: {archive_failure}")
    return failures


def select_with_integrity(
    candidates: Sequence[Candidate],
    *,
    seed: str,
) -> tuple[list[Candidate], dict[str, list[str]]]:
    integrity_failures: dict[str, list[str]] = {}
    excluded_ids: set[str] = set()
    while True:
        selected = choose_subset(
            candidates,
            seed=seed,
            excluded_ids=excluded_ids,
        )
        newly_failed: dict[str, list[str]] = {}
        for candidate in selected:
            failures = deep_validate(candidate)
            if failures:
                newly_failed[candidate.challenge_id] = failures
        if not newly_failed:
            return selected, integrity_failures
        integrity_failures.update(newly_failed)
        excluded_ids.update(newly_failed)


def selection_sha256(selected: Sequence[Candidate]) -> str:
    digest = hashlib.sha256()
    for position, candidate in enumerate(selected, 1):
        digest.update(
            json_dumps(
                {
                    "position": position,
                    "challenge_id": candidate.challenge_id,
                    "profile": candidate.profile,
                    "route": candidate.route,
                    "material_fingerprint": candidate.material_fingerprint,
                },
                pretty=False,
            ).encode()
        )
        digest.update(b"\n")
    return digest.hexdigest()


def candidate_manifest_record(
    candidate: Candidate,
    *,
    position: int,
) -> dict[str, Any]:
    materials_by_role = {
        role: [
            material.manifest_record()
            for material in candidate.materials
            if material.role == role
        ]
        for role in ("A", "W", "P", "B")
    }
    return {
        "position": position,
        "challenge_id": candidate.challenge_id,
        "challenge_source": {
            "dataset_abbr": candidate.dataset_abbr,
            "repository": candidate.source_repo,
            "reference": candidate.source_reference,
            "path": candidate.source_path,
            "origin_repository": candidate.origin_repo_hint,
            "selection_label": candidate.source_label,
        },
        "event": candidate.event,
        "year": candidate.year,
        "title": candidate.title,
        "material_profile": candidate.profile,
        "pipeline_route": candidate.route,
        "image_name": image_name_for(candidate),
        "role_states": candidate.role_states,
        "material_count": candidate.material_count,
        "material_bytes": candidate.total_bytes,
        "material_fingerprint": candidate.material_fingerprint,
        "features": candidate.feature_details,
        "selection_reason": candidate.selection_reason,
        "materials": materials_by_role,
    }


def make_manifest(
    selected: Sequence[Candidate],
    *,
    source: dict[str, Any],
    seed: str,
    rejected: Counter[str],
    integrity_failures: dict[str, list[str]],
) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "source": source,
        "selection": {
            "seed": seed,
            "algorithm": "alternating-profile deterministic greedy marginal coverage v1",
            "count": len(selected),
            "profile_quotas": PROFILE_QUOTAS,
            "selection_sha256": selection_sha256(selected),
            "candidate_limits": {
                "max_material_files": MAX_MATERIAL_FILES,
                "max_material_bytes": MAX_MATERIAL_BYTES,
                "max_single_file_bytes": MAX_SINGLE_FILE_BYTES,
            },
            "coverage_targets": COVERAGE_TARGETS,
            "eligibility_rejections": dict(sorted(rejected.items())),
            "integrity_rejections": integrity_failures,
        },
        "tier_claims": {
            "static_material_profile_is_not_execution_evidence": True,
            "rehost_tier": None,
            "exploit_tier": None,
        },
        "tasks": [
            candidate_manifest_record(candidate, position=position)
            for position, candidate in enumerate(selected, 1)
        ],
    }


def task_json(candidate: Candidate, selection_digest: str) -> dict[str, Any]:
    role_counts = Counter(material.role for material in candidate.materials)
    task_materials = {
        "deployment": ["materials/deployment"] if role_counts["B"] else [],
        "source": [],
        "exploit": ["materials/exploit"] if role_counts["P"] else [],
        "attachments": ["materials/attachments"] if role_counts["A"] else [],
        "writeups": ["materials/writeups"] if role_counts["W"] else [],
    }
    return {
        "schema_version": "cage-build-task-v1",
        "id": candidate.challenge_id,
        "name": candidate.title,
        "category": "pwn",
        "event": candidate.event,
        "year": candidate.year,
        "source_reference": candidate.source_reference,
        "description": (
            f"{candidate.event} {candidate.year} Pwn challenge "
            f"{candidate.title}. Reconstruct the target from formal local "
            f"{candidate.profile} material."
        ).strip(),
        "material_profile": candidate.profile,
        "pipeline_route": candidate.route,
        "image_name": image_name_for(candidate),
        "materials": task_materials,
        "material_states": {
            "attachment": {
                "state": "confirmed_local",
                "count": role_counts["A"],
            },
            "writeup": {
                "state": candidate.role_states["writeup"],
                "count": role_counts["W"],
            },
            "exp": {
                "state": "confirmed_local",
                "count": role_counts["P"],
            },
            "deploy": {
                "state": "confirmed_local",
                "count": role_counts["B"],
            },
        },
        "service_contract": {"protocol": "tcp"},
        "flag_format": "flag{...}",
        "flag_contract": {"evidence_state": "not_searched"},
        "build_environment": {"network": "restricted"},
        "static_evidence": {
            "profile_rule": PROFILE_RULE,
            "profile_plan_sha256": PLAN_SHA256,
            "profile_source_run_id": PROFILE_RUN_ID,
            "entity_rule": ENTITY_RULE,
            "entity_source_run_id": ENTITY_RUN_ID,
            "selection_sha256": selection_digest,
            "execution_tier_claimed": False,
        },
    }


def image_name_for(candidate: Candidate) -> str:
    component = re.sub(
        r"[^a-z0-9._-]+",
        "-",
        candidate.challenge_id.casefold(),
    ).strip("._-")
    if not component:
        raise SubsetError(
            f"challenge ID cannot form an image name: {candidate.challenge_id}"
        )
    tag = f"pwn-{component}"
    if len(tag) > 128:
        raise SubsetError(
            f"challenge ID produces an overlong Docker tag: {candidate.challenge_id}"
        )
    return f"ctf-env:{tag}"


def ensure_new_file(path: Path) -> None:
    if path.exists():
        raise FileExistsError(f"refusing to overwrite existing artifact: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)


def materialize_dataset(
    selected: Sequence[Candidate],
    dataset_root: Path,
    manifest: dict[str, Any],
) -> None:
    if dataset_root.exists():
        raise FileExistsError(f"refusing to overwrite dataset: {dataset_root}")
    dataset_root.parent.mkdir(parents=True, exist_ok=True)
    temporary = dataset_root.with_name(f".{dataset_root.name}.tmp-{os.getpid()}")
    if temporary.exists():
        raise FileExistsError(f"temporary dataset path already exists: {temporary}")
    temporary.mkdir(parents=True)
    try:
        digest = str(manifest["selection"]["selection_sha256"])
        for candidate in selected:
            task_root = temporary / candidate.challenge_id
            task_root.mkdir()
            for material in candidate.materials:
                destination = task_root / safe_relative_path(material.dataset_path)
                destination.parent.mkdir(parents=True, exist_ok=True)
                try:
                    os.link(material.source_path, destination)
                except OSError as exc:
                    if exc.errno != errno.EXDEV:
                        raise
                    shutil.copy2(material.source_path, destination)
            (task_root / "task.json").write_text(
                json_dumps(task_json(candidate, digest)),
                encoding="utf-8",
            )
        (temporary / "SELECTION.json").write_text(
            json_dumps(manifest),
            encoding="utf-8",
        )
        rows = [
            "position\tchallenge_id\tprofile\troute\tevent\tyear\tfiles\tbytes\n"
        ]
        for position, candidate in enumerate(selected, 1):
            rows.append(
                "\t".join(
                    (
                        str(position),
                        candidate.challenge_id,
                        candidate.profile,
                        candidate.route,
                        candidate.event.replace("\t", " "),
                        candidate.year,
                        str(candidate.material_count),
                        str(candidate.total_bytes),
                    )
                )
                + "\n"
            )
        (temporary / "TASKS.tsv").write_text("".join(rows), encoding="utf-8")
        temporary.rename(dataset_root)
    except BaseException:
        shutil.rmtree(temporary, ignore_errors=True)
        raise


def format_bytes(value: int) -> str:
    units = ("B", "KiB", "MiB", "GiB")
    number = float(value)
    for unit in units:
        if number < 1024 or unit == units[-1]:
            return f"{number:.1f} {unit}"
        number /= 1024
    return f"{value} B"


def coverage_summary(tasks: Sequence[dict[str, Any]], field: str) -> Counter[str]:
    values: Counter[str] = Counter()
    for task in tasks:
        value = task["features"].get(field)
        if isinstance(value, list):
            values.update(str(item) for item in value)
        else:
            values[str(value)] += 1
    return values


def markdown_counter(counter: Counter[str]) -> str:
    return ", ".join(f"`{key}` {count}" for key, count in sorted(counter.items()))


def render_report(manifest: dict[str, Any], generation_command: str) -> str:
    tasks = list(manifest["tasks"])
    source = manifest["source"]
    selection = manifest["selection"]
    profile_counts = Counter(task["material_profile"] for task in tasks)
    events = Counter(task["event"] for task in tasks)
    years = Counter(task["year"] or "unknown" for task in tasks)
    sources = Counter(
        task["challenge_source"]["selection_label"] for task in tasks
    )
    lines = [
        f"# P1 AWPB/APB {expected_task_count()}-task control subset",
        "",
        "This is a static-material observation subset. It makes **no R/X claim** "
        "and was selected without running an agent or model.",
        "",
        "## Frozen provenance",
        "",
        f"- Profile rule: `{source['profile_rule']}`",
        f"- Profile plan SHA-256: `{source['profile_plan_sha256']}`",
        f"- Profile run: `{source['profile_run_id']}`",
        f"- Entity rule/run: `{source['entity_rule']}` / `{source['entity_run_id']}`",
        f"- Entity selection SHA-256: `{source['entity_selection_sha256']}`",
        f"- Source repository commit: `{source['repository_commit']}`",
        f"- Catalog schema version: `{source['database_schema_version']}`",
        f"- Selection seed: `{selection['seed']}`",
        f"- Selection SHA-256: `{selection['selection_sha256']}`",
        "",
        "Generation command:",
        "",
        "```bash",
        generation_command,
        "```",
        "",
        "## Distribution",
        "",
        f"- Profiles: {markdown_counter(profile_counts)}",
        f"- Unique events: {len(events)}",
        f"- Unique source repositories: {len(sources)}",
        f"- Years: {markdown_counter(years)}",
        f"- Build forms: {markdown_counter(coverage_summary(tasks, 'build_form'))}",
        f"- Build modes: {markdown_counter(coverage_summary(tasks, 'build_mode'))}",
        f"- Runtime forms: {markdown_counter(coverage_summary(tasks, 'runtime_form'))}",
        f"- Exploit classes: {markdown_counter(coverage_summary(tasks, 'exploit_classes'))}",
        f"- Topology: {markdown_counter(coverage_summary(tasks, 'topology'))}",
        f"- Complexity: {markdown_counter(coverage_summary(tasks, 'complexity'))}",
        "",
        "## Selected tasks",
        "",
        "| # | challenge_id | profile / route | source / event / year | "
        "build | runtime | exploit | topology | material |",
        "|---:|---|---|---|---|---|---|---|---:|",
    ]
    for task in tasks:
        features = task["features"]
        lines.append(
            "| {position} | `{challenge_id}` | `{profile}` / `{route}` | "
            "`{source}` / {event} / {year} | `{build_form}`, `{build_mode}` | `{runtime}` | "
            "{exploit} | `{topology}` | {files} / {size} |".format(
                position=task["position"],
                challenge_id=task["challenge_id"],
                profile=task["material_profile"],
                route=task["pipeline_route"],
                source=str(
                    task["challenge_source"]["selection_label"]
                ).replace("|", "\\|"),
                event=str(task["event"]).replace("|", "\\|"),
                year=task["year"] or "unknown",
                build_form=features["build_form"],
                build_mode=features["build_mode"],
                runtime=features["runtime_form"],
                exploit=", ".join(features["exploit_classes"]),
                topology=features["topology"],
                files=task["material_count"],
                size=format_bytes(int(task["material_bytes"])),
            )
        )

    lines.extend(["", "## Per-task material audit", ""])
    for task in tasks:
        features = task["features"]
        lines.extend(
            [
                f"### {task['position']}. `{task['challenge_id']}` — {task['title']}",
                "",
                f"- Identity: {task['event']} / {task['year'] or 'unknown'} / Pwn",
                f"- Source: `{task['challenge_source']['selection_label']}`; "
                f"`{task['challenge_source']['reference']}`",
                f"- Formal route: `{task['material_profile']}` → `{task['pipeline_route']}`",
                f"- Build/runtime/EXP: `{features['build_form']}`; "
                f"`{features['build_mode']}`; `{features['runtime_form']}`; "
                + ", ".join(f"`{item}`" for item in features["exploit_classes"]),
                f"- Selection reason: {'; '.join(task['selection_reason'])}",
                f"- Material fingerprint: `{task['material_fingerprint']}`",
                "- Material paths:",
            ]
        )
        for role in ("A", "W", "P", "B"):
            records = task["materials"][role]
            if not records:
                lines.append(f"  - {role}: absent")
                continue
            lines.append(f"  - {role} ({len(records)}):")
            for record in records:
                lines.append(
                    f"    - `{record['dataset_path']}` ← "
                    f"`{record['source_relative_path']}` "
                    f"(`{record['sha256']}`, {record['size']} bytes)"
                )
        lines.append("")

    lines.extend(
        [
            "## Automated verification",
            "",
            "The verifier recomputes the deterministic selection from the formal "
            "database, checks the balanced profile quotas, canonical identities, "
            "role states, unique IDs/material fingerprints, every source and "
            "dataset path, byte size, SHA-256, archive integrity, task contracts, "
            "and report coverage.",
            "",
            "```bash",
            (
                "python examples/build_target/scripts/materialize_p1_control_subset.py "
                "verify"
            ),
            "```",
            "",
            "Static A/W/P/B evidence is inventory only; none of these tasks is "
            "reported as R3, R4, R5, or any X tier.",
            "",
        ]
    )
    return "\n".join(lines)


def generate(args: argparse.Namespace) -> int:
    source_root = args.source_root.resolve()
    database = source_root / "catalog/ctf_index.sqlite3"
    connection = connect_readonly(database)
    try:
        source = source_metadata(connection, source_root)
        candidates, rejected = load_candidates(connection, source_root)
    finally:
        connection.close()
    selected, integrity_failures = select_with_integrity(
        candidates,
        seed=args.seed,
    )
    manifest = make_manifest(
        selected,
        source=source,
        seed=args.seed,
        rejected=rejected,
        integrity_failures=integrity_failures,
    )

    ensure_new_file(args.manifest)
    ensure_new_file(args.report)
    materialize_dataset(selected, args.dataset, manifest)
    generation_command = (
        "python examples/build_target/scripts/materialize_p1_control_subset.py "
        "generate "
        f"--source-root {args.source_root} "
        f"--dataset {args.dataset} "
        f"--manifest {args.manifest} "
        f"--report {args.report} "
        f"--count {expected_task_count()} "
        f"--seed {args.seed}"
    )
    args.manifest.write_text(json_dumps(manifest), encoding="utf-8")
    args.report.write_text(
        render_report(manifest, generation_command),
        encoding="utf-8",
    )
    print(
        json_dumps(
            {
                "generated": True,
                "count": len(selected),
                "profiles": dict(
                    Counter(candidate.profile for candidate in selected)
                ),
                "selection_sha256": manifest["selection"]["selection_sha256"],
                "dataset": str(args.dataset),
                "manifest": str(args.manifest),
                "report": str(args.report),
            }
        ),
        end="",
    )
    return 0


def manifest_task_map(manifest: dict[str, Any]) -> dict[str, dict[str, Any]]:
    tasks = manifest.get("tasks")
    if not isinstance(tasks, list):
        raise SubsetError("manifest tasks must be a list")
    indexed = {
        str(task.get("challenge_id")): task
        for task in tasks
        if isinstance(task, dict)
    }
    if len(indexed) != len(tasks):
        raise SubsetError("manifest has duplicate or malformed task records")
    return indexed


def verify_manifest_shape(manifest: dict[str, Any]) -> None:
    if manifest.get("schema_version") != SCHEMA_VERSION:
        raise SubsetError("manifest schema version mismatch")
    tasks = list(manifest_task_map(manifest).values())
    expected_count = expected_task_count()
    if len(tasks) != expected_count:
        raise SubsetError(
            f"manifest task count is {len(tasks)}, expected {expected_count}"
        )
    profiles = Counter(str(task.get("material_profile")) for task in tasks)
    if dict(profiles) != PROFILE_QUOTAS:
        raise SubsetError(f"manifest profile quotas mismatch: {dict(profiles)}")
    fingerprints = [str(task.get("material_fingerprint")) for task in tasks]
    if len(fingerprints) != len(set(fingerprints)):
        raise SubsetError("manifest contains duplicate material fingerprints")
    for task in tasks:
        profile = str(task.get("material_profile"))
        if task.get("pipeline_route") != PROFILE_ROUTES.get(profile):
            raise SubsetError(
                f"manifest route mismatch for {task.get('challenge_id')}"
            )
        expected_roles = EXPECTED_EXPORT_ROLES[profile]
        actual_roles = {
            role
            for role, records in (task.get("materials") or {}).items()
            if records
        }
        if actual_roles != expected_roles:
            raise SubsetError(
                f"manifest material roles mismatch for {task.get('challenge_id')}"
            )
    digest_rows = [
        Candidate(
            challenge_id=str(task["challenge_id"]),
            dataset_abbr=str(task["challenge_source"]["dataset_abbr"]),
            event=str(task["event"]),
            year=str(task["year"]),
            title=str(task["title"]),
            source_repo=str(task["challenge_source"]["repository"]),
            source_reference=str(task["challenge_source"]["reference"]),
            source_path=str(task["challenge_source"]["path"]),
            origin_repo_hint=str(
                task["challenge_source"]["origin_repository"]
            ),
            profile=str(task["material_profile"]),
            route=str(task["pipeline_route"]),
            status_source_run_id=PROFILE_RUN_ID,
            profile_evidence={},
            role_states=dict(task["role_states"]),
            material_fingerprint=str(task["material_fingerprint"]),
        )
        for task in sorted(tasks, key=lambda item: int(item["position"]))
    ]
    actual_digest = selection_sha256(digest_rows)
    expected_digest = str(manifest["selection"]["selection_sha256"])
    if actual_digest != expected_digest:
        raise SubsetError(
            f"selection SHA mismatch: {actual_digest} != {expected_digest}"
        )
    tier_claims = manifest.get("tier_claims") or {}
    if (
        tier_claims.get("static_material_profile_is_not_execution_evidence")
        is not True
        or tier_claims.get("rehost_tier") is not None
        or tier_claims.get("exploit_tier") is not None
    ):
        raise SubsetError("manifest makes or permits an R/X tier claim")


def verify_dataset_task(
    task: dict[str, Any],
    dataset_root: Path,
    selection_digest: str,
) -> None:
    challenge_id = str(task["challenge_id"])
    task_root = dataset_root / challenge_id
    task_path = task_root / "task.json"
    if not task_path.is_file():
        raise SubsetError(f"dataset task.json missing: {challenge_id}")
    task_json_data = json.loads(task_path.read_text(encoding="utf-8"))
    if task_json_data.get("id") != challenge_id:
        raise SubsetError(f"task ID mismatch: {challenge_id}")
    if task_json_data.get("material_profile") != task["material_profile"]:
        raise SubsetError(f"task profile mismatch: {challenge_id}")
    if task_json_data.get("pipeline_route") != task["pipeline_route"]:
        raise SubsetError(f"task route mismatch: {challenge_id}")
    if task_json_data.get("image_name") != task["image_name"]:
        raise SubsetError(f"task image name mismatch: {challenge_id}")
    if str(task_json_data["image_name"]).endswith(":latest"):
        raise SubsetError(f"task image name uses latest: {challenge_id}")
    role_counts = {
        role: len(records) for role, records in task["materials"].items()
    }
    expected_task_materials = {
        "deployment": ["materials/deployment"] if role_counts["B"] else [],
        "source": [],
        "exploit": ["materials/exploit"] if role_counts["P"] else [],
        "attachments": ["materials/attachments"] if role_counts["A"] else [],
        "writeups": ["materials/writeups"] if role_counts["W"] else [],
    }
    if task_json_data.get("materials") != expected_task_materials:
        raise SubsetError(f"task role paths mismatch: {challenge_id}")
    if "target_maturity" in task_json_data:
        raise SubsetError(f"task improperly declares target maturity: {challenge_id}")
    evidence = task_json_data.get("static_evidence") or {}
    if evidence.get("execution_tier_claimed") is not False:
        raise SubsetError(f"task does not disclaim execution tier: {challenge_id}")
    if evidence.get("selection_sha256") != selection_digest:
        raise SubsetError(f"task selection digest mismatch: {challenge_id}")

    expected_materials: dict[str, dict[str, Any]] = {}
    for records in task["materials"].values():
        for record in records:
            expected_materials[str(record["dataset_path"])] = record
    actual_materials = {
        path.relative_to(task_root).as_posix(): path
        for path in task_root.glob("materials/**/*")
        if path.is_file()
    }
    if set(actual_materials) != set(expected_materials):
        missing = sorted(set(expected_materials) - set(actual_materials))
        extra = sorted(set(actual_materials) - set(expected_materials))
        raise SubsetError(
            f"dataset material set mismatch for {challenge_id}: "
            f"missing={missing} extra={extra}"
        )
    for relative_path, path in actual_materials.items():
        record = expected_materials[relative_path]
        if path.stat().st_size != int(record["size"]):
            raise SubsetError(
                f"dataset size mismatch: {challenge_id}/{relative_path}"
            )
        if sha256_file(path) != record["sha256"]:
            raise SubsetError(
                f"dataset SHA mismatch: {challenge_id}/{relative_path}"
            )
        archive_failure = validate_archive(path)
        if archive_failure:
            raise SubsetError(
                f"dataset archive failed: {challenge_id}/{relative_path}: "
                f"{archive_failure}"
            )


def verify(args: argparse.Namespace) -> int:
    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    verify_manifest_shape(manifest)
    if not args.dataset.is_dir():
        raise FileNotFoundError(f"materialized dataset is missing: {args.dataset}")
    if not args.report.is_file():
        raise FileNotFoundError(f"audit report is missing: {args.report}")

    source_root = args.source_root.resolve()
    connection = connect_readonly(source_root / "catalog/ctf_index.sqlite3")
    try:
        current_source = source_metadata(connection, source_root)
        candidates, rejected = load_candidates(connection, source_root)
    finally:
        connection.close()
    if current_source != manifest["source"]:
        raise SubsetError("manifest source provenance differs from current catalog")
    integrity_rejections = manifest["selection"].get("integrity_rejections") or {}
    regenerated = choose_subset(
        candidates,
        seed=str(manifest["selection"]["seed"]),
        excluded_ids=set(integrity_rejections),
    )
    regenerated_ids = [candidate.challenge_id for candidate in regenerated]
    manifest_tasks = sorted(manifest["tasks"], key=lambda task: int(task["position"]))
    manifest_ids = [str(task["challenge_id"]) for task in manifest_tasks]
    if regenerated_ids != manifest_ids:
        raise SubsetError(
            "deterministic reselection differs from manifest: "
            f"regenerated={regenerated_ids} manifest={manifest_ids}"
        )
    if dict(sorted(rejected.items())) != manifest["selection"]["eligibility_rejections"]:
        raise SubsetError("eligibility rejection summary differs from manifest")

    selection_digest = str(manifest["selection"]["selection_sha256"])
    manifest_index = manifest_task_map(manifest)
    candidate_index = {candidate.challenge_id: candidate for candidate in candidates}
    for challenge_id in manifest_ids:
        candidate = candidate_index.get(challenge_id)
        if candidate is None:
            raise SubsetError(f"selected task left formal eligible pool: {challenge_id}")
        task = manifest_index[challenge_id]
        if candidate.profile != task["material_profile"]:
            raise SubsetError(f"current profile drifted: {challenge_id}")
        if candidate.route != task["pipeline_route"]:
            raise SubsetError(f"current route drifted: {challenge_id}")
        current_record = candidate_manifest_record(
            candidate,
            position=int(task["position"]),
        )
        if current_record != task:
            raise SubsetError(
                f"manifest task record differs from canonical source: {challenge_id}"
            )
        failures = deep_validate(candidate)
        if failures:
            raise SubsetError(
                f"source integrity failed for {challenge_id}: {failures}"
            )
        verify_dataset_task(task, args.dataset, selection_digest)

    dataset_selection = json.loads(
        (args.dataset / "SELECTION.json").read_text(encoding="utf-8")
    )
    if dataset_selection != manifest:
        raise SubsetError("dataset SELECTION.json differs from tracked manifest")
    report_text = args.report.read_text(encoding="utf-8")
    for challenge_id in manifest_ids:
        if challenge_id not in report_text:
            raise SubsetError(f"audit report omits challenge {challenge_id}")
        for records in manifest_index[challenge_id]["materials"].values():
            for record in records:
                if record["dataset_path"] not in report_text:
                    raise SubsetError(
                        f"audit report omits dataset material path: "
                        f"{challenge_id}/{record['dataset_path']}"
                    )
                if record["source_relative_path"] not in report_text:
                    raise SubsetError(
                        f"audit report omits source material path: "
                        f"{challenge_id}/{record['source_relative_path']}"
                    )
    if "no R/X claim" not in report_text:
        raise SubsetError("audit report does not explicitly disclaim R/X")

    print(
        json_dumps(
            {
                "verified": True,
                "count": len(manifest_ids),
                "profiles": dict(
                    Counter(task["material_profile"] for task in manifest_tasks)
                ),
                "unique_events": len({task["event"] for task in manifest_tasks}),
                "selection_sha256": selection_digest,
                "source_paths_verified": sum(
                    len(records)
                    for task in manifest_tasks
                    for records in task["materials"].values()
                ),
                "dataset": str(args.dataset),
            }
        ),
        end="",
    )
    return 0


def analyze(args: argparse.Namespace) -> int:
    source_root = args.source_root.resolve()
    connection = connect_readonly(source_root / "catalog/ctf_index.sqlite3")
    try:
        source = source_metadata(connection, source_root)
        candidates, rejected = load_candidates(connection, source_root)
    finally:
        connection.close()
    selected = choose_subset(candidates, seed=args.seed)
    feature_counts: Counter[str] = Counter()
    for candidate in selected:
        feature_counts.update(candidate.tags)
    print(
        json_dumps(
            {
                "source": source,
                "eligible_counts": dict(
                    Counter(candidate.profile for candidate in candidates)
                ),
                "eligibility_rejections": dict(sorted(rejected.items())),
                "proposed_ids": [
                    candidate.challenge_id for candidate in selected
                ],
                "proposed_profile_counts": dict(
                    Counter(candidate.profile for candidate in selected)
                ),
                "proposed_unique_events": len(
                    {candidate.event.casefold() for candidate in selected}
                ),
                "proposed_unique_sources": len(
                    {candidate.source_label.casefold() for candidate in selected}
                ),
                "proposed_feature_counts": dict(sorted(feature_counts.items())),
            }
        ),
        end="",
    )
    return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    for command in ("generate", "verify", "analyze"):
        subparser = subparsers.add_parser(command)
        subparser.add_argument(
            "--source-root",
            type=Path,
            default=DEFAULT_SOURCE_ROOT,
        )
        subparser.add_argument(
            "--dataset",
            type=Path,
            default=DEFAULT_DATASET,
        )
        subparser.add_argument(
            "--manifest",
            type=Path,
            default=DEFAULT_MANIFEST,
        )
        subparser.add_argument(
            "--report",
            type=Path,
            default=DEFAULT_REPORT,
        )
        subparser.add_argument(
            "--count",
            type=int,
            default=expected_task_count(),
            help="positive even subset size, split equally between AWPB and APB",
        )
        subparser.add_argument("--seed", default=SELECTION_SEED)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    global PROFILE_QUOTAS
    PROFILE_QUOTAS = profile_quotas_for_count(args.count)
    if args.command == "generate":
        return generate(args)
    if args.command == "verify":
        return verify(args)
    return analyze(args)


if __name__ == "__main__":
    raise SystemExit(main())
