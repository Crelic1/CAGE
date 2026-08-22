from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
import zipfile
from pathlib import Path

import pytest


def _load_module():
    path = (
        Path(__file__).resolve().parents[1]
        / "examples"
        / "build_target"
        / "scripts"
        / "materialize_p1_control_subset.py"
    )
    spec = importlib.util.spec_from_file_location("p1_control_subset", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _material(module, root: Path, challenge_id: str, role: str, name: str):
    path = root / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(f"{role}:{name}".encode())
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    return module.Material(
        challenge_id=challenge_id,
        role=role,
        logical_path=name,
        source_kind="repository_file",
        file_kind="fixture",
        size=path.stat().st_size,
        artifact_sha256=digest,
        storage_root_id="workspace",
        export_relative_path=(
            f"work/materials/pwn-v11/{challenge_id}/"
            f"{module.ROLE_DIRECTORIES[role]}/{name}"
        ),
        export_state="hardlinked",
        source_path=path,
        dataset_path=f"materials/{module.ROLE_DIRECTORIES[role]}/{name}",
    )


def _candidate(module, tmp_path: Path):
    challenge_id = "gh-fixture"
    candidate = module.Candidate(
        challenge_id=challenge_id,
        dataset_abbr="gh",
        event="FixtureCTF",
        year="2025",
        title="fixture",
        source_repo="example/fixture",
        source_reference="https://example.invalid/fixture",
        source_path="pwn/fixture",
        origin_repo_hint="",
        profile="AWPB",
        route="fast_track_full",
        status_source_run_id=module.PROFILE_RUN_ID,
        profile_evidence={},
        role_states={
            "attachment": "confirmed_local",
            "writeup": "confirmed_local",
            "exploit": "confirmed_local",
            "build": "confirmed_local",
        },
    )
    candidate.materials = [
        _material(module, tmp_path, challenge_id, role, f"{role}/file-{role}")
        for role in ("A", "W", "P", "B")
    ]
    return candidate


def test_maps_canonical_export_to_safe_role_directory() -> None:
    module = _load_module()

    assert module.dataset_path_for(
        "gh-demo",
        "P",
        "work/materials/pwn-v11/gh-demo/solve/src/solve.py",
    ) == "materials/exploit/src/solve.py"


def test_candidate_contract_preserves_static_only_semantics(tmp_path: Path) -> None:
    module = _load_module()
    candidate = _candidate(module, tmp_path)

    assert module.eligibility_failure(candidate) is None
    assert candidate.material_fingerprint
    task = module.task_json(candidate, "a" * 64)
    assert task["material_profile"] == "AWPB"
    assert task["pipeline_route"] == "fast_track_full"
    assert task["image_name"] == "ctf-env:pwn-gh-fixture"
    assert task["materials"] == {
        "deployment": ["materials/deployment"],
        "source": [],
        "exploit": ["materials/exploit"],
        "attachments": ["materials/attachments"],
        "writeups": ["materials/writeups"],
    }
    assert "target_maturity" not in task
    assert task["static_evidence"]["execution_tier_claimed"] is False


def test_deep_validation_checks_sha_and_archive_integrity(tmp_path: Path) -> None:
    module = _load_module()
    candidate = _candidate(module, tmp_path)
    archive = tmp_path / "A" / "bundle.zip"
    with zipfile.ZipFile(archive, "w") as handle:
        handle.writestr("chall", b"ELF fixture")
    archive_material = module.Material(
        challenge_id=candidate.challenge_id,
        role="A",
        logical_path="bundle.zip",
        source_kind="direct_artifact",
        file_kind="archive",
        size=archive.stat().st_size,
        artifact_sha256=hashlib.sha256(archive.read_bytes()).hexdigest(),
        storage_root_id="workspace",
        export_relative_path=(
            "work/materials/pwn-v11/gh-fixture/public/bundle.zip"
        ),
        export_state="hardlinked",
        source_path=archive,
        dataset_path="materials/attachments/bundle.zip",
    )
    candidate.materials.append(archive_material)

    assert module.deep_validate(candidate) == []
    archive.write_bytes(b"not a zip")
    failures = module.deep_validate(candidate)
    assert any("sha256" in failure for failure in failures)
    assert any("BadZipFile" in failure for failure in failures)


def test_year_buckets_are_stable() -> None:
    module = _load_module()

    assert module.year_bucket("2019") == "pre_2020"
    assert module.year_bucket("2021") == "2020_2021"
    assert module.year_bucket("2024") == "2024"
    assert module.year_bucket("2026") == "2025_plus"
    assert module.year_bucket("") == "unknown"


def test_profile_quotas_scale_to_balanced_larger_subsets() -> None:
    module = _load_module()

    assert module.profile_quotas_for_count(30) == {"AWPB": 15, "APB": 15}
    assert module.profile_quotas_for_count(100) == {"AWPB": 50, "APB": 50}
    with pytest.raises(module.SubsetError, match="positive even integer"):
        module.profile_quotas_for_count(99)


def test_frozen_manifest_has_exact_control_contract() -> None:
    module = _load_module()
    manifest_path = (
        Path(__file__).resolve().parents[1]
        / "examples"
        / "build_target"
        / "task_lists"
        / "p1_control_30"
        / "manifest.json"
    )
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    module.verify_manifest_shape(manifest)
    assert manifest["selection"]["count"] == 30
    assert manifest["selection"]["profile_quotas"] == {"AWPB": 15, "APB": 15}
    assert len({task["challenge_id"] for task in manifest["tasks"]}) == 30
    assert all(
        task["image_name"] == f"ctf-env:pwn-{task['challenge_id']}"
        for task in manifest["tasks"]
    )
