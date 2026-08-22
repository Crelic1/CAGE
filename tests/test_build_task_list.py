from __future__ import annotations

import importlib.util
import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]


def _load_module():
    module_path = REPO_ROOT / "examples" / "build_target" / "scripts" / "build_task_list.py"
    spec = importlib.util.spec_from_file_location("build_task_list", module_path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _material(
    state: str,
    *,
    paths: list[str] | None = None,
    evidence: list[dict] | None = None,
) -> dict:
    files = [
        {
            "path": path,
            "sha256": "0" * 64,
            "size": 1,
        }
        for path in paths or []
    ]
    return {
        "state": state,
        "search_status": "complete",
        "count": len(files) or len(evidence or []),
        "bytes": len(files),
        "files": files,
        "candidate_files": [],
        "evidence": evidence or [],
    }


def _row(
    env_id: str,
    *,
    category: str,
    tier: str,
    confirmed_tier: str,
    name: str,
    deploy: list[str] | None = None,
    attachments: list[str] | None = None,
    source: bool = False,
    writeup: str | None = None,
) -> dict:
    writeup_evidence = [{"local_path": writeup}] if writeup else []
    return {
        "challenge_id": env_id,
        "identity": {
            "category": category,
            "event": "ExampleCTF",
            "year": "2024",
            "name": name,
        },
        "data_tier": {
            "candidate": tier,
            "confirmed": confirmed_tier,
        },
        "materials": {
            "deploy": _material("confirmed" if deploy else "not_found", paths=deploy),
            "source": _material("confirmed" if source else "not_found"),
            "attachment": _material(
                "candidate" if attachments else "not_found",
                paths=attachments,
            ),
            "writeup": _material(
                "confirmed" if writeup else "not_found",
                evidence=writeup_evidence,
            ),
            "exp": _material("not_found"),
        },
        "docker_closure": {
            "status": "closed" if deploy else "no_deploy",
            "selection_status": "selected" if deploy else "none",
            "entries": [],
            "missing_refs": [],
            "review_refs": [],
            "blockers": [],
        },
        "flag_contract": {"state": "not_searched"},
        "blockers": [],
        "review_flags": [],
        "manifest_path": f"sources/{category}/challenges/{env_id}/source_manifest.json",
        "snapshot_as_of": "2026-07-13",
        "wave_id": "test-wave",
    }


def _make_challenge(
    root: Path,
    *,
    env_id: str,
    category: str,
    files: list[str],
) -> None:
    challenge = root / "sources" / category / "challenges" / env_id
    challenge.mkdir(parents=True)
    (challenge / "source_manifest.json").write_text("{}", encoding="utf-8")
    for relative in files:
        path = challenge / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("fixture", encoding="utf-8")


def test_builds_deterministic_policy_queue_and_removes_completed(tmp_path: Path) -> None:
    module = _load_module()
    source_repo = tmp_path / "source-repo"
    catalog = source_repo / "catalog"
    catalog.mkdir(parents=True)

    complete_id = "saj-2024-pwn-complete"
    docker_id = "saj-2024-pwn-docker"
    deferred_id = "saj-2024-web-deferred"
    dropped_id = "saj-2024-web-dropped"
    candidate_only_id = "saj-2024-web-candidate-only"
    completed_id = "saj-2024-web-built"
    rows = [
        _row(
            complete_id,
            category="pwn",
            tier="D5",
            confirmed_tier="D4",
            name="Complete",
            deploy=["deploy/Dockerfile"],
            attachments=["public/chall"],
            writeup=(f"sources/pwn/challenges/{complete_id}/evidence/writeups/community/wp.md"),
        ),
        _row(
            docker_id,
            category="pwn",
            tier="D4",
            confirmed_tier="D4",
            name="Docker",
            deploy=["deploy/Dockerfile"],
            attachments=["public/chall"],
        ),
        _row(
            deferred_id,
            category="web",
            tier="D2",
            confirmed_tier="D1",
            name="Deferred",
            attachments=["public/archive.zip"],
            source=True,
        ),
        _row(
            dropped_id,
            category="web",
            tier="D1",
            confirmed_tier="D1",
            name="Dropped",
            writeup=(f"sources/web/challenges/{dropped_id}/evidence/writeups/community/wp.md"),
        ),
        _row(
            candidate_only_id,
            category="web",
            tier="D4",
            confirmed_tier="D1",
            name="Candidate only",
            deploy=["deploy/Dockerfile"],
            attachments=["public/chall"],
        ),
        _row(
            completed_id,
            category="web",
            tier="D4",
            confirmed_tier="D4",
            name="Built",
            deploy=["deploy/Dockerfile"],
        ),
    ]
    for row in rows:
        env_id = row["challenge_id"]
        category = row["identity"]["category"]
        paths = [
            entry["path"] for material in row["materials"].values() for entry in material["files"]
        ]
        for evidence in row["materials"]["writeup"]["evidence"]:
            local = Path(evidence["local_path"])
            paths.append(
                local.relative_to(Path("sources") / category / "challenges" / env_id).as_posix()
            )
        if row["materials"]["source"]["state"] == "confirmed":
            paths.append("source/app.py")
        _make_challenge(
            source_repo,
            env_id=env_id,
            category=category,
            files=paths,
        )

    static_materials = catalog / "static_materials.jsonl"
    static_materials.write_text(
        "".join(json.dumps(row) + "\n" for row in rows),
        encoding="utf-8",
    )
    completed_manifest = source_repo / "completed.json"
    completed_manifest.write_text(
        json.dumps(
            {
                "batch_id": "test-success",
                "status": "build_and_cage_serve_verified",
                "runtime_replacements": [
                    {
                        "removed": docker_id,
                        "reason": "runtime requires /dev/kvm",
                        "added": completed_id,
                    }
                ],
                "environments": [
                    {
                        "env_id": completed_id,
                        "maturity": "D4-R3-X0",
                        "image": "ctfenv/web-built-wave3:d4-r3-x0",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    artifacts = module.build_artifacts(
        static_materials=static_materials,
        source_repo=source_repo,
        completion_manifests=[completed_manifest],
        wave="wave4",
    )

    assert artifacts["summary"]["counts"] == {
        "input": 6,
        "build": 2,
        "deferred_d2": 1,
        "completed": 1,
        "candidate_tier_not_confirmed": 1,
        "policy_dropped_d0_d1": 1,
        "confirmed_d0_d1_total": 2,
        "build_with_prior_runtime_blocker": 1,
        "excluded_total": 3,
    }
    assert [record["env_id"] for record in artifacts["build"]] == [
        complete_id,
        docker_id,
    ]
    assert [record["priority"]["id"] for record in artifacts["build"]] == [
        "dockerfile_writeup_attachments",
        "dockerfile_attachments",
    ]
    first_task = artifacts["build"][0]["task"]
    assert first_task["data_tier_evidence"] == {
        "selected_from": "confirmed",
        "candidate": "D5",
        "confirmed": "D4",
    }
    assert first_task["materials"] == {
        "deployment": ["deploy"],
        "source": [],
        "attachments": ["public"],
        "writeups": ["evidence/writeups/community/wp.md"],
    }
    assert first_task["image_name"] == "ctfenv/pwn-complete-wave4:d4-r3-x0"
    assert artifacts["build"][1]["priority"]["known_prior_runtime_blocker"] is True
    assert (
        artifacts["build"][1]["task"]["static_evidence"]["prior_runtime_failures"][0]["reason"]
        == "runtime requires /dev/kvm"
    )
    assert artifacts["deferred"][0]["env_id"] == deferred_id
    assert artifacts["completed"][0]["env_id"] == completed_id
    assert {record["reason"] for record in artifacts["excluded"]} == {
        "already_generated_r3",
        "candidate_tier_not_confirmed_for_build",
        "policy_drop_d0_d1",
    }
    assert [record["env_id"] for record in artifacts["candidate_only"]] == [candidate_only_id]

    output_dir = tmp_path / "output"
    module.write_artifacts(artifacts, output_dir)
    assert (output_dir / "build_task_ids.txt").read_text(encoding="utf-8").splitlines() == [
        complete_id,
        docker_id,
    ]
    tsv_lines = (output_dir / "build_tasks.tsv").read_text(encoding="utf-8").splitlines()
    assert len(tsv_lines) == 3
    assert tsv_lines[1].split("\t")[1] == complete_id
    assert tsv_lines[1].split("\t")[3:5] == ["D5", "D4"]


def test_disambiguates_image_names_without_using_latest(tmp_path: Path) -> None:
    module = _load_module()
    source_repo = tmp_path / "source-repo"
    catalog = source_repo / "catalog"
    catalog.mkdir(parents=True)
    rows = []
    for year, suffix in (("2023", "a"), ("2024", "b")):
        env_id = f"saj-{year}-pwn-echo-{suffix}"
        row = _row(
            env_id,
            category="pwn",
            tier="D4",
            confirmed_tier="D4",
            name="Echo",
            deploy=["deploy/Dockerfile"],
            attachments=["public/chall"],
        )
        row["identity"]["year"] = year
        rows.append(row)
        _make_challenge(
            source_repo,
            env_id=env_id,
            category="pwn",
            files=["deploy/Dockerfile", "public/chall"],
        )
    static_materials = catalog / "static_materials.jsonl"
    static_materials.write_text(
        "".join(json.dumps(row) + "\n" for row in rows),
        encoding="utf-8",
    )

    artifacts = module.build_artifacts(
        static_materials=static_materials,
        source_repo=source_repo,
        completion_manifests=[],
        wave="wave4",
    )
    image_names = {record["task"]["image_name"] for record in artifacts["build"]}

    assert image_names == {
        "ctfenv/pwn-echo-2023-wave4:d4-r3-x0",
        "ctfenv/pwn-echo-2024-wave4:d4-r3-x0",
    }
    assert all(not image.endswith(":latest") for image in image_names)
    assert artifacts["summary"]["image_name_collisions"]["affected_task_count"] == 2
