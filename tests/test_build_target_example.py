from __future__ import annotations

import copy
import importlib.util
import json
import subprocess
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]


def _load_module():
    module_path = REPO_ROOT / "examples" / "build_target" / "benchmark.py"
    spec = importlib.util.spec_from_file_location("build_target_benchmark", module_path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _load_bash_guard_module():
    module_path = (
        REPO_ROOT / "examples" / "build_target" / "serve" / "claude_bash_guard.py"
    )
    spec = importlib.util.spec_from_file_location("build_target_claude_bash_guard", module_path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _write_task(root: Path, task: dict, name: str = "sample") -> Path:
    sample_dir = root / name
    sample_dir.mkdir(parents=True)
    (sample_dir / "task.json").write_text(json.dumps(task), encoding="utf-8")
    return sample_dir


def _one_sample(module, root: Path) -> dict:
    return next(iter(module.BuildTarget(root).iter_samples()))


def _write_runtime_cache(module, root: Path) -> Path:
    cache = root / "runtime-cache"
    bundles = []
    catalog = json.loads(module.RUNTIME_CATALOG_PATH.read_text(encoding="utf-8"))
    for entry in catalog["bundles"]:
        bundle_dir = cache / entry["id"]
        bundle_dir.mkdir(parents=True)
        libc = bundle_dir / "libc.so.6"
        loader = bundle_dir / "ld-linux-x86-64.so.2"
        libc.write_bytes(f"libc {entry['glibc_series']}".encode())
        loader.write_bytes(f"loader {entry['glibc_series']}".encode())
        bundles.append(
            {
                **entry,
                "libc": {
                    "path": libc.relative_to(cache).as_posix(),
                    "sha256": "libc-digest",
                    "size": libc.stat().st_size,
                },
                "loader": {
                    "path": loader.relative_to(cache).as_posix(),
                    "sha256": "loader-digest",
                    "size": loader.stat().st_size,
                },
            }
        )
    (cache / "manifest.json").write_text(
        json.dumps({"schema_version": "cage-pwn-runtime-cache-v1", "bundles": bundles}),
        encoding="utf-8",
    )
    return cache


@pytest.mark.parametrize(
    ("tier", "materials", "expected"),
    [
        ("D0", {}, "Default action: triage and stop at R0"),
        ("D1", {"writeups": ["writeup.md"]}, "extract facts, then remain R0"),
        ("D2", {"attachments": ["chall"]}, "historical authenticity"),
        ("D3", {"source": ["chall.c"]}, "Derive the runtime contract from source"),
        ("D4", {"deployment": ["Dockerfile"]}, "official Dockerfile/Compose"),
        ("D5", {"deployment": ["Dockerfile"]}, "near-complete evidence package"),
    ],
)
def test_routes_each_data_tier_to_its_own_policy(
    tmp_path: Path, tier: str, materials: dict, expected: str
) -> None:
    module = _load_module()
    task = {
        "name": f"tier-{tier.lower()}",
        "category": "web",
        "data_tier": tier,
        "materials": materials,
    }
    if materials.get("deployment") or materials.get("source") or materials.get("attachments"):
        task["image_name"] = f"ctfenv/web-tier-{tier.lower()}:d{tier[1]}-r3-x0"
    _write_task(tmp_path, task)

    sample = _one_sample(module, tmp_path)
    prompt = module.BuildTarget(tmp_path).build_prompt(sample)

    assert sample["data_tier"] == tier
    assert expected in prompt
    assert "does not grant an R level" in prompt


def test_rejects_unknown_data_tier(tmp_path: Path) -> None:
    module = _load_module()
    _write_task(tmp_path, {"name": "bad-tier", "category": "web", "data_tier": "D6"})

    with pytest.raises(ValueError, match="data_tier must be one of"):
        list(module.BuildTarget(tmp_path).iter_samples())


def test_prompt_preserves_candidate_and_confirmed_static_evidence(
    tmp_path: Path,
) -> None:
    module = _load_module()
    sample_dir = _write_task(
        tmp_path,
        {
            "name": "evidence-status",
            "category": "web",
            "data_tier": "D5",
            "data_tier_evidence": {
                "selected_from": "candidate",
                "candidate": "D5",
                "confirmed": "D4",
            },
            "target_maturity": {
                "data": "D5",
                "rehost": "R3",
                "exploit": "X0",
            },
            "material_states": {
                "deploy": {
                    "state": "confirmed",
                    "search_status": "complete",
                    "count": 1,
                },
                "attachment": {
                    "state": "candidate",
                    "search_status": "partial",
                    "count": 1,
                },
            },
            "docker_closure": {
                "status": "review",
                "missing_ref_count": 0,
                "review_ref_count": 2,
            },
            "static_evidence": {
                "blocker_codes": ["COPY_SOURCE_REVIEW"],
                "review_flags": ["candidate_attachment"],
                "prior_runtime_failures": [
                    {
                        "batch_id": "wave3",
                        "reason": "runtime requires /dev/kvm",
                    }
                ],
            },
            "materials": {
                "deployment": ["Dockerfile"],
                "attachments": ["chall"],
            },
            "image_name": "ctfenv/web-evidence-status-wave4:d5-r3-x0",
        },
    )
    (sample_dir / "Dockerfile").write_text("FROM scratch\n", encoding="utf-8")
    (sample_dir / "chall").write_bytes(b"fixture")

    benchmark = module.BuildTarget(tmp_path)
    sample = next(iter(benchmark.iter_samples()))
    prompt = benchmark.build_prompt(sample)

    assert sample["data_tier_evidence"]["confirmed"] == "D4"
    assert "candidate " in prompt
    assert "confirmed " in prompt
    assert "Docker closure: status " in prompt
    assert "COPY_SOURCE_REVIEW" in prompt
    assert "candidate_attachment" in prompt
    assert "runtime requires /dev/kvm" in prompt


def test_pwn_queue_uses_declared_material_priority(tmp_path: Path) -> None:
    module = _load_module()
    tasks = [
        (
            "p4-attachments",
            {"attachments": ["chall"]},
        ),
        (
            "p3-source",
            {"source": ["chall.c"], "attachments": ["chall"]},
        ),
        (
            "p5-compose-only",
            {"deployment": ["docker-compose.yml"], "attachments": ["chall"]},
        ),
        (
            "p1-dockerfile",
            {"deployment": ["Dockerfile"], "attachments": ["chall"]},
        ),
        (
            "p2-writeup",
            {"writeups": ["writeup.md"], "attachments": ["chall"]},
        ),
        (
            "p0-complete",
            {
                "deployment": ["Dockerfile"],
                "writeups": ["writeup.md"],
                "attachments": ["chall"],
            },
        ),
    ]
    for index, (name, materials) in enumerate(tasks):
        _write_task(
            tmp_path,
            {
                "name": name,
                "category": "pwn",
                "materials": materials,
                "image_name": f"ctfenv/pwn-{name}:d4-r3-x0",
            },
            name=f"sample-{index}",
        )

    samples = list(module.BuildTarget(tmp_path).iter_samples())

    assert [sample["id"] for sample in samples] == [
        "p0-complete",
        "p1-dockerfile",
        "p2-writeup",
        "p3-source",
        "p4-attachments",
        "p5-compose-only",
    ]
    assert [sample["pwn_material_priority"]["rank"] for sample in samples] == [
        0,
        1,
        2,
        3,
        4,
        5,
    ]
    assert samples[0]["pwn_material_priority"]["has_dockerfile"] is True
    assert samples[-1]["pwn_material_priority"]["has_dockerfile"] is False


def test_generated_queue_sort_key_is_preserved(tmp_path: Path) -> None:
    module = _load_module()
    for name, closure_rank in (("review-first", 2), ("closed-first", 0)):
        sample_dir = _write_task(
            tmp_path,
            {
                "name": name,
                "category": "web",
                "data_tier": "D4",
                "queue_priority": {
                    "id": "web_data_tier",
                    "rank": 0,
                    "sort_key": [1, 0, -4, closure_rank, name],
                },
                "materials": {
                    "deployment": ["Dockerfile"],
                },
                "image_name": f"ctfenv/web-{name}-wave4:d4-r3-x0",
            },
            name=name,
        )
        (sample_dir / "Dockerfile").write_text("FROM scratch\n", encoding="utf-8")

    samples = list(module.BuildTarget(tmp_path).iter_samples())

    assert [sample["id"] for sample in samples] == [
        "closed-first",
        "review-first",
    ]


def test_pwn_prompt_exposes_local_pairs_for_writeup_inference(
    tmp_path: Path,
) -> None:
    module = _load_module()
    cache = _write_runtime_cache(module, tmp_path)
    _write_task(
        tmp_path,
        {
            "name": "heap-task",
            "category": "pwn",
            "data_tier": "D2",
            "materials": {
                "attachments": ["chall"],
                "writeups": ["writeup.md"],
            },
            "image_name": "ctfenv/pwn-heap-task:d2-r3-x0",
        },
        name="sample",
    )

    benchmark = module.BuildTarget(tmp_path, pwn_runtime_cache=cache)
    sample = next(iter(benchmark.iter_samples()))
    prompt = benchmark.build_prompt(sample)

    assert sample["pwn_runtime"]["status"] == "ready"
    assert sample["pwn_material_priority"]["id"] == "writeup_attachments"
    assert "16.04 → glibc 2.23" in prompt
    assert "/opt/cage/pwn-runtimes/ubuntu-22.04-glibc-2.35-amd64/libc.so.6" in prompt
    assert "Do **not** use `ldd --version`" in prompt
    assert "`evidence` **must be a JSON array**" in prompt
    assert '"path": "build/runtime/libc.so.6"' in prompt
    assert "Never report the read-only `/opt/cage/pwn-runtimes/...` source path" in prompt
    assert "As soon as `docker-compose.yml`, `build_report.json`, and `challenge.json` exist" in prompt
    assert "do not approximate it with `SYS_ADMIN`" in prompt
    assert "`apparmor:unconfined`" in prompt
    assert '"target_ports": {"challenge": 1337}' in prompt
    assert "Do not choose or reserve a host port" in prompt
    assert "`build.tags` is not a substitute for `image:`" in prompt
    assert "image: ctfenv/pwn-heap-task:d2-r3-x0" in prompt
    assert str(cache) not in prompt


def test_prepare_trial_copies_ready_runtime_cache_outside_workspace(tmp_path: Path) -> None:
    module = _load_module()
    cache = _write_runtime_cache(module, tmp_path)
    sample_dir = _write_task(
        tmp_path,
        {
            "name": "runtime-copy",
            "category": "pwn",
            "materials": {
                "attachments": ["chall"],
                "writeups": ["writeup.md"],
            },
            "image_name": "ctfenv/pwn-runtime-copy:d2-r3-x0",
        },
        name="sample",
    )
    (sample_dir / "chall").write_bytes(b"ELF")
    (sample_dir / "writeup.md").write_text("Ubuntu 22.04", encoding="utf-8")

    class FakeContainer:
        def __init__(self) -> None:
            self.exec_calls: list[str] = []
            self.copy_calls: list[tuple[str, str]] = []

        def exec(self, command: str):
            self.exec_calls.append(command)

        def copy_to(self, source: str, destination: str):
            self.copy_calls.append((source, destination))

    benchmark = module.BuildTarget(tmp_path, pwn_runtime_cache=cache)
    sample = next(iter(benchmark.iter_samples()))
    container = FakeContainer()
    benchmark.prepare_trial(container, sample, "/home/agent/workspace")

    assert (f"{cache}/.", "/opt/cage/pwn-runtimes") in container.copy_calls
    assert not any(
        destination.startswith("/home/agent/workspace/runtime")
        for _, destination in container.copy_calls
    )


def test_pipeline_prepare_trial_installs_read_only_progressive_guides(
    tmp_path: Path,
) -> None:
    module = _load_module()
    _write_task(
        tmp_path,
        {
            "name": "guide-copy",
            "category": "web",
            "materials": {},
        },
    )

    class FakeContainer:
        def __init__(self) -> None:
            self.exec_calls: list[str] = []
            self.copy_calls: list[tuple[str, str]] = []

        def exec(self, command: str):
            self.exec_calls.append(command)

        def copy_to(self, source: str, destination: str):
            self.copy_calls.append((source, destination))

    benchmark = module.BuildTarget(tmp_path, pipeline_prompts=True)
    sample = next(iter(benchmark.iter_samples()))
    container = FakeContainer()
    benchmark.prepare_trial(container, sample, "/home/agent/workspace")

    assert (
        f"{module.GUIDES_SOURCE_DIR}/.",
        module.GUIDES_AGENT_DIR,
    ) in container.copy_calls
    assert (
        str(module.CLAUDE_BASH_GUARD_PATH),
        module.CLAUDE_BASH_GUARD_AGENT_PATH,
    ) in container.copy_calls
    assert any(
        f"chmod -R a-w,a+rX {module.GUIDES_AGENT_DIR}" in command
        for command in container.exec_calls
    )
    assert any(
        "--install" in command
        and module.CLAUDE_SETTINGS_PATH in command
        and module.CLAUDE_BASH_GUARD_AGENT_PATH in command
        for command in container.exec_calls
    )
    assert (module.GUIDES_SOURCE_DIR / "INDEX.md").is_file()
    qemu_guide = module.GUIDES_SOURCE_DIR / "runtime" / "qemu.md"
    archive_guide = module.GUIDES_SOURCE_DIR / "artifacts" / "archive-images.md"
    assert qemu_guide.is_file()
    qemu_text = " ".join(qemu_guide.read_text(encoding="utf-8").split())
    archive_text = " ".join(archive_guide.read_text(encoding="utf-8").split())
    assert "replacing that flow with autologin is a semantic change" in qemu_text
    assert "Never preinstall that payload in the guest" in qemu_text
    assert "archive reconstructed from degraded metadata" in archive_text
    assert "unprivileged agent as inspection-only" in archive_text
    assert "outside any broad recursive `chown`/`chmod`" in archive_text


@pytest.mark.parametrize(
    "command",
    [
        'grep -rl "selected_bundle" / 2>/dev/null',
        'grep -rl "pwn_runtime" /opt /usr /etc /var 2>/dev/null',
        "find /home -name task.json",
        "rg material_priority /usr/local/lib /var/lib",
    ],
)
def test_claude_bash_guard_blocks_unbounded_searches(command: str) -> None:
    guard = _load_bash_guard_module()
    reason = guard.evaluate_command(command, "/home/agent/workspace")
    assert reason is not None
    assert "search" in reason.lower()


@pytest.mark.parametrize(
    "command",
    [
        'rg -n "selected_bundle" /home/agent/workspace/materials',
        "find /home/agent/workspace -maxdepth 3 -type f",
        'grep -R "qemu-system" /opt/cage/build-target-guides',
        "find /opt/cage/pwn-runtimes -maxdepth 2 -type f",
        "cage-check --json 2>&1 | tee result.json",
    ],
)
def test_claude_bash_guard_allows_bounded_inspection(command: str) -> None:
    guard = _load_bash_guard_module()
    assert guard.evaluate_command(command, "/home/agent/workspace") is None


@pytest.mark.parametrize(
    "command",
    [
        "qemu-system-x86_64 -kernel bzImage -initrd rootfs.cpio",
        "socat TCP-LISTEN:1337,reuseaddr,fork EXEC:./chall",
        "python3 -m http.server 8000",
        "python3 /tmp/localtest/relay.py",
        "nc -lvnp 1337",
        "nohup cage-check --json > result.json 2>&1 &",
        "timeout 580 cage-check --json 2>&1",
        "env CAGE_CHECK_TIMEOUT_SECONDS=900 cage-check --json",
        "pkill -f qemu-system",
    ],
)
def test_claude_bash_guard_blocks_local_substitute_targets(command: str) -> None:
    guard = _load_bash_guard_module()
    assert guard.evaluate_command(command, "/home/agent/workspace") is not None


def test_claude_bash_guard_blocks_direct_workspace_elf(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    guard = _load_bash_guard_module()
    challenge = tmp_path / "chall"
    challenge.write_bytes(b"\x7fELF" + b"\0" * 32)
    monkeypatch.setattr(guard, "WORKSPACE_ROOT", tmp_path)
    assert guard.evaluate_command("./chall", str(tmp_path)) is not None


def test_claude_bash_guard_merges_settings_and_emits_deny_json(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    guard = _load_bash_guard_module()
    settings_path = tmp_path / "settings.json"
    script_path = Path("/home/agent/.claude/cage-build-target-bash-guard.py")
    settings_path.write_text(
        json.dumps({"env": {"KEEP": "1"}, "hooks": {"PostToolUse": []}}),
        encoding="utf-8",
    )
    guard.install(settings_path, script_path)
    settings = json.loads(settings_path.read_text(encoding="utf-8"))
    assert settings["env"] == {"KEEP": "1"}
    assert settings["hooks"]["PostToolUse"] == []
    entry = settings["hooks"]["PreToolUse"][0]
    assert entry["matcher"] == "Bash"
    assert entry["hooks"][0]["args"] == [str(script_path)]

    payload = {
        "hook_event_name": "PreToolUse",
        "cwd": "/home/agent/workspace",
        "tool_input": {"command": 'grep -rl "selected_bundle" /'},
    }
    marker_path = tmp_path / "guard-active.json"
    monkeypatch.setattr(guard, "ACTIVATION_MARKER", marker_path)
    monkeypatch.setattr(sys, "stdin", __import__("io").StringIO(json.dumps(payload)))
    assert guard._main() == 0
    assert json.loads(marker_path.read_text(encoding="utf-8"))["schema_version"] == 1
    output = json.loads(capsys.readouterr().out)
    assert output["hookSpecificOutput"]["permissionDecision"] == "deny"


def test_routes_existing_web_deployment_to_official_profile(tmp_path: Path) -> None:
    module = _load_module()
    _write_task(
        tmp_path,
        {
            "name": "panel",
            "category": "web",
            "data_tier": "D4",
            "image_name": "ctfenv/web-panel-wave1:d4-r3-x0",
            "materials": {
                "deployment": ["deploy/docker-compose.yml", "deploy/app/Dockerfile"],
                "source": ["source/app"],
                "writeups": ["evidence/writeups/panel.md"],
            },
            "service_contract": {
                "protocol": "http",
                "internal_port": 31337,
                "readiness_path": "/login",
            },
            "flag_contract": {
                "injection": "environment",
                "env_var": "FLAG",
                "value": "must-not-reach-the-prompt",
            },
        },
    )

    benchmark = module.BuildTarget(tmp_path)
    sample = next(iter(benchmark.iter_samples()))
    prompt = benchmark.build_prompt(sample)

    assert sample["build_profile"] == "official_deployment"
    assert sample["category_profile"] == "web"
    assert sample["internal_port"] == 31337
    assert sample["flag_contract"] == {
        "injection": "environment",
        "env_var": "FLAG",
        "format": "flag{...}",
    }
    assert "minimal compatibility repair" in prompt
    assert "complete application topology" in prompt
    assert "deploy/docker-compose.yml" in prompt
    assert "must-not-reach-the-prompt" not in prompt
    assert "ELF interpreter" not in prompt


def test_routes_source_only_pwn_task_to_source_rebuild(tmp_path: Path) -> None:
    module = _load_module()
    _write_task(
        tmp_path,
        {
            "name": "tiny-pwn",
            "category": "binary exploitation",
            "image_name": "ctfenv/pwn-tiny-pwn-wave1:d3-r3-x0",
            "attachments": ["tiny", "tiny.c", "notes/writeup.md"],
        },
    )

    benchmark = module.BuildTarget(tmp_path)
    sample = next(iter(benchmark.iter_samples()))
    prompt = benchmark.build_prompt(sample)

    assert sample["build_profile"] == "source_rebuild"
    assert sample["category_profile"] == "pwn"
    assert sample["materials"] == {
        "deployment": [],
        "source": ["tiny.c"],
        "exploit": [],
        "attachments": ["tiny"],
        "writeups": ["notes/writeup.md"],
    }
    assert "real build command" in prompt
    assert "ELF interpreter" in prompt
    assert "complete application topology" not in prompt


def test_routes_binary_and_writeup_without_source_to_artifact_rehost(tmp_path: Path) -> None:
    module = _load_module()
    _write_task(
        tmp_path,
        {
            "name": "binary-only",
            "category": "pwn",
            "image_name": "ctfenv/pwn-binary-only-wave1:d2-r3-x0",
            "materials": {
                "attachments": ["public/chall", "public/libc.so.6"],
                "writeups": ["evidence/writeups/solve.md"],
            },
        },
    )

    sample = _one_sample(module, tmp_path)
    prompt = module.BuildTarget(tmp_path).build_prompt(sample)

    assert sample["build_profile"] == "artifact_rehost"
    assert "thin transport wrapper" in prompt
    assert "Do not reimplement the challenge from the Writeup" in prompt


def test_routes_missing_material_to_triage_without_fabrication(tmp_path: Path) -> None:
    module = _load_module()
    _write_task(tmp_path, {"name": "metadata-only", "category": "web"})

    sample = _one_sample(module, tmp_path)
    prompt = module.BuildTarget(tmp_path).build_prompt(sample)

    assert sample["build_profile"] == "triage"
    assert "status: blocked" in prompt
    assert "Do not manufacture a Docker service" in prompt


def test_explicit_build_profile_alias_is_supported(tmp_path: Path) -> None:
    module = _load_module()
    _write_task(
        tmp_path,
        {
            "name": "explicit",
            "category": "web",
            "build_strategy": "source-based",
            "image_name": "ctfenv/web-explicit-wave1:d3-r3-x0",
            "materials": {"attachments": ["bundle.tar.gz"]},
        },
    )

    assert _one_sample(module, tmp_path)["build_profile"] == "source_rebuild"


def test_rejects_material_path_traversal(tmp_path: Path) -> None:
    module = _load_module()
    _write_task(
        tmp_path,
        {"name": "escape", "category": "pwn", "attachments": ["../secret"]},
    )

    with pytest.raises(ValueError, match="must stay inside material_root"):
        list(module.BuildTarget(tmp_path).iter_samples())


def test_rejects_empty_material_path(tmp_path: Path) -> None:
    module = _load_module()
    _write_task(tmp_path, {"name": "empty", "category": "pwn", "attachments": [" "]})

    with pytest.raises(ValueError, match="must stay inside material_root"):
        list(module.BuildTarget(tmp_path).iter_samples())


def test_rejects_invalid_benchmark_root_instead_of_falling_back(tmp_path: Path) -> None:
    module = _load_module()

    with pytest.raises(FileNotFoundError, match="benchmark root"):
        module.BuildTarget(tmp_path / "missing")


def test_rejects_invalid_build_environment_shape(tmp_path: Path) -> None:
    module = _load_module()
    _write_task(
        tmp_path,
        {
            "name": "bad-env",
            "category": "pwn",
            "attachments": ["chall"],
            "image_name": "ctfenv/pwn-bad-env-wave1:d2-r3-x0",
            "build_environment": "offline",
        },
    )

    with pytest.raises(ValueError, match="build_environment must be an object"):
        list(module.BuildTarget(tmp_path).iter_samples())


def test_non_triage_task_requires_archival_image_name(tmp_path: Path) -> None:
    module = _load_module()
    _write_task(
        tmp_path,
        {"name": "no-image", "category": "pwn", "attachments": ["chall"]},
    )

    with pytest.raises(ValueError, match="must declare image_name"):
        list(module.BuildTarget(tmp_path).iter_samples())


def test_rejects_latest_image_tag(tmp_path: Path) -> None:
    module = _load_module()
    _write_task(
        tmp_path,
        {
            "name": "latest",
            "category": "pwn",
            "attachments": ["chall"],
            "image_name": "ctfenv/pwn-latest:latest",
        },
    )

    with pytest.raises(ValueError, match="non-latest tag"):
        list(module.BuildTarget(tmp_path).iter_samples())


def test_prepare_trial_copies_nested_files_and_directories(tmp_path: Path) -> None:
    module = _load_module()
    sample_dir = _write_task(
        tmp_path,
        {
            "name": "nested",
            "category": "web",
            "image_name": "ctfenv/web-nested-wave1:d3-r3-x0",
            "materials": {
                "source": ["source/app"],
                "writeups": ["evidence/writeups/solve.md"],
            },
        },
    )
    (sample_dir / "source" / "app").mkdir(parents=True)
    (sample_dir / "source" / "app" / "server.js").write_text("serve()", encoding="utf-8")
    (sample_dir / "evidence" / "writeups").mkdir(parents=True)
    (sample_dir / "evidence" / "writeups" / "solve.md").write_text("steps", encoding="utf-8")

    class FakeContainer:
        def __init__(self) -> None:
            self.exec_calls: list[str] = []
            self.copy_calls: list[tuple[str, str]] = []

        def exec(self, command: str):
            self.exec_calls.append(command)

        def copy_to(self, source: str, destination: str):
            self.copy_calls.append((source, destination))

    sample = _one_sample(module, tmp_path)
    container = FakeContainer()
    module.BuildTarget(tmp_path).prepare_trial(container, sample, "/home/agent/workspace")

    assert container.copy_calls == [
        (
            str(sample_dir / "source" / "app"),
            "/home/agent/workspace/source/app",
        ),
        (
            str(sample_dir / "evidence" / "writeups" / "solve.md"),
            "/home/agent/workspace/evidence/writeups/solve.md",
        ),
    ]
    assert any("chown -R agent:agent" in command for command in container.exec_calls)


def test_prepare_trial_fails_on_declared_missing_material(tmp_path: Path) -> None:
    module = _load_module()
    _write_task(
        tmp_path,
        {
            "name": "missing",
            "category": "web",
            "image_name": "ctfenv/web-missing-wave1:d3-r3-x0",
            "materials": {"source": ["source/not-there"]},
        },
    )

    class FakeContainer:
        def exec(self, command: str):
            return None

        def copy_to(self, source: str, destination: str):
            raise AssertionError("copy_to must not be called")

    sample = _one_sample(module, tmp_path)
    with pytest.raises(FileNotFoundError, match="declared material"):
        module.BuildTarget(tmp_path).prepare_trial(FakeContainer(), sample, "/home/agent/workspace")


def _completed(cmd: list[str], returncode: int = 0, stdout: str = "", stderr: str = ""):
    return subprocess.CompletedProcess(cmd, returncode, stdout, stderr)


def _all_targets_ready(targets: list[dict], **_kwargs) -> dict:
    """Readiness fixture for scorer tests whose Docker runtime is fully mocked."""

    return {
        "deadline_seconds": 0,
        "targets": [
            {
                "service": target.get("service_name"),
                "container_addr": target.get("container_addr"),
                "internal_port": target.get("internal_port"),
                "ready": True,
                "attempts": 1,
            }
            for target in targets
        ],
    }


def test_scorer_rejects_attachments_only_runtime_authenticity_overclaim(
    tmp_path: Path,
) -> None:
    module = _load_module()
    trial_dir = tmp_path / "trial"
    workspace = trial_dir / "workspace"
    workspace.mkdir(parents=True)
    report = {
        "status": "ready",
        "data_tier": "D2",
        "build_profile": "artifact_rehost",
        "category_profile": "pwn",
        "pwn_runtime": {
            "material_priority": "attachments_only",
            "selection_basis": "elf_guess",
            "evidence": [],
            "selected_bundle": None,
            "confidence": "low",
            "authenticity_status": "verified",
        },
    }
    (workspace / "build_report.json").write_text(json.dumps(report), encoding="utf-8")
    ctx = module.ScoringContext(
        trial_id="runtime-overclaim",
        trial_index=0,
        sample={
            "data_tier": "D2",
            "build_profile": "artifact_rehost",
            "category_profile": "pwn",
            "pwn_material_priority": {"id": "attachments_only"},
        },
        trial_dir=trial_dir,
        run_dir=trial_dir,
    )

    _, failure = module._BootCheckScorer()._validate_build_report(ctx, workspace)

    assert failure is not None
    score = failure["build_target"]
    assert score.metadata["failure_class"] == "pwn_authenticity_overclaim"


@pytest.mark.parametrize(
    "selected_bundle",
    ["ubuntu-22.04-glibc-2.35-amd64", "external_verified"],
)
def test_scorer_validates_selected_libc_loader_pair(
    tmp_path: Path,
    selected_bundle: str,
) -> None:
    module = _load_module()
    trial_dir = tmp_path / "trial"
    workspace = trial_dir / "workspace"
    runtime_dir = workspace / "runtime"
    runtime_dir.mkdir(parents=True)
    libc = runtime_dir / "libc.so.6"
    loader = runtime_dir / "ld-linux-x86-64.so.2"
    libc.write_bytes(b"chosen libc")
    loader.write_bytes(b"chosen loader")
    libc_sha = module._sha256_file(libc)
    loader_sha = module._sha256_file(loader)
    report = {
        "status": "ready",
        "data_tier": "D2",
        "build_profile": "artifact_rehost",
        "category_profile": "pwn",
        "pwn_runtime": {
            "material_priority": "writeup_attachments",
            "selection_basis": "writeup",
            "evidence": [{"path": "writeup.md", "clue": "Ubuntu 22.04"}],
            "selected_bundle": selected_bundle,
            "confidence": "medium",
            "authenticity_status": "inferred_from_writeup",
            "selected_files": {
                "libc": {"path": "runtime/libc.so.6", "sha256": libc_sha},
                "loader": {
                    "path": "runtime/ld-linux-x86-64.so.2",
                    "sha256": loader_sha,
                },
            },
        },
    }
    (workspace / "build_report.json").write_text(json.dumps(report), encoding="utf-8")
    ctx = module.ScoringContext(
        trial_id="runtime-pair",
        trial_index=0,
        sample={
            "data_tier": "D2",
            "build_profile": "artifact_rehost",
            "category_profile": "pwn",
            "pwn_material_priority": {"id": "writeup_attachments"},
            "pwn_runtime": {
                "bundles": [] if selected_bundle == "external_verified" else [
                    {
                        "id": "ubuntu-22.04-glibc-2.35-amd64",
                        "libc": {"sha256": libc_sha},
                        "loader": {"sha256": loader_sha},
                    }
                ]
            },
        },
        trial_dir=trial_dir,
        run_dir=trial_dir,
    )

    validated, failure = module._BootCheckScorer()._validate_build_report(ctx, workspace)

    assert failure is None
    assert validated is not None
    assert validated["pwn_runtime"]["validated_selected_files"] == {
        "libc": {"path": "runtime/libc.so.6", "sha256": libc_sha},
        "loader": {"path": "runtime/ld-linux-x86-64.so.2", "sha256": loader_sha},
    }


def test_scorer_requires_build_backed_tag_and_keeps_local_image(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    module = _load_module()
    trial_dir = tmp_path / "trial"
    workspace = trial_dir / "workspace"
    workspace.mkdir(parents=True)
    (workspace / "docker-compose.yml").write_text("services: {}\n", encoding="utf-8")
    (workspace / "build_report.json").write_text(json.dumps({"status": "ready"}), encoding="utf-8")
    (workspace / "challenge.json").write_text(
        json.dumps(
            {
                "compose_files": ["docker-compose.yml"],
                "compose_target_services": ["challenge"],
                "compose_dependency_services": [],
                "target_ports": {"challenge": 31337},
                "target_port_protocols": {"challenge": "tcp"},
            }
        ),
        encoding="utf-8",
    )
    image_name = "ctfenv/pwn-demo-wave1:d4-r3-x0"
    calls: list[list[str]] = []

    def fake_run(cmd: list[str], **_kwargs):
        calls.append(cmd)
        if "config" in cmd:
            return _completed(
                cmd,
                stdout=json.dumps(
                    {
                        "services": {
                            "challenge": {
                                "build": {"context": "."},
                                "image": image_name,
                            }
                        }
                    }
                ),
            )
        if cmd[:3] == ["docker", "image", "inspect"]:
            return _completed(
                cmd,
                stdout=json.dumps(
                    {
                        "Id": "sha256:built-image-id",
                        "RepoTags": [image_name],
                        "RepoDigests": [],
                        "Created": "2026-07-13T00:00:00Z",
                        "Size": 1234,
                    }
                ),
            )
        if cmd[:2] == ["docker", "inspect"]:
            return _completed(
                cmd,
                stdout=json.dumps(
                    {
                        "State": {"Status": "running"},
                        "NetworkSettings": {
                            "Networks": {"buildcheck_default": {"IPAddress": "172.18.0.2"}}
                        },
                    }
                ),
            )
        if "ps" in cmd:
            return _completed(cmd, stdout="container-id\n")
        if "logs" in cmd:
            return _completed(cmd, stdout="challenge ready\n")
        return _completed(cmd)

    monkeypatch.setattr(module, "_run", fake_run)
    monkeypatch.setattr(module.time, "sleep", lambda _seconds: None)
    monkeypatch.setattr(module, "_await_target_readiness", _all_targets_ready)
    ctx = module.ScoringContext(
        trial_id="trial-1",
        trial_index=0,
        sample={"image_name": image_name, "image_names": [image_name]},
        trial_dir=trial_dir,
        run_dir=trial_dir,
    )

    score = module._BootCheckScorer().score(ctx)["build_target"]

    assert score.value == 1.0
    assert score.metadata["passed"] is True
    assert score.metadata["retained_local_images"] == [
        {
            "name": image_name,
            "services": ["challenge"],
            "image_id": "sha256:built-image-id",
            "repo_tags": [image_name],
            "repo_digests": [],
            "created": "2026-07-13T00:00:00Z",
            "size": 1234,
        }
    ]
    manifest = json.loads((trial_dir / "image_manifest.json").read_text(encoding="utf-8"))
    assert manifest["retained_locally"] is True
    assert manifest["images"][0]["name"] == image_name
    down = next(cmd for cmd in calls if "down" in cmd)
    assert "--rmi" not in down


def test_scorer_rejects_forbidden_runtime_settings_before_boot(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    module = _load_module()
    trial_dir = tmp_path / "trial"
    workspace = trial_dir / "workspace"
    workspace.mkdir(parents=True)
    (workspace / "docker-compose.yml").write_text("services: {}\n", encoding="utf-8")
    (workspace / "build_report.json").write_text(json.dumps({"status": "ready"}), encoding="utf-8")
    (workspace / "challenge.json").write_text(
        json.dumps(
            {
                "compose_files": ["docker-compose.yml"],
                "compose_target_services": ["app"],
                "compose_dependency_services": [],
                "target_ports": {"app": 1024},
                "target_port_protocols": {"app": "tcp"},
            }
        ),
        encoding="utf-8",
    )
    image_name = "ctfenv/pwn-ret4win-wave1:d4-r3-x0"
    calls: list[list[str]] = []

    def fake_run(cmd: list[str], **_kwargs):
        calls.append(cmd)
        if "config" in cmd:
            return _completed(
                cmd,
                stdout=json.dumps(
                    {
                        "services": {
                            "app": {
                                "build": {"context": "."},
                                "image": image_name,
                                "privileged": True,
                            }
                        }
                    }
                ),
            )
        return _completed(cmd)

    monkeypatch.setattr(module, "_run", fake_run)
    ctx = module.ScoringContext(
        trial_id="unsafe-runtime",
        trial_index=0,
        sample={"image_name": image_name, "image_names": [image_name]},
        trial_dir=trial_dir,
        run_dir=trial_dir,
    )

    score = module._BootCheckScorer().score(ctx)["build_target"]

    assert score.value == 0.0
    assert score.metadata["failure_class"] == "compose_runtime_unsafe"
    assert score.metadata["evidence"]["violations"] == [
        {"service": "app", "field": "privileged", "value": True}
    ]
    assert "forbids `privileged`" in score.metadata["feedback"]
    assert not any("up" in cmd for cmd in calls)


def test_scorer_rejects_sys_admin_and_unconfined_security_profiles_before_boot(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    module = _load_module()
    trial_dir = tmp_path / "trial"
    workspace = trial_dir / "workspace"
    workspace.mkdir(parents=True)
    (workspace / "docker-compose.yml").write_text("services: {}\n", encoding="utf-8")
    (workspace / "build_report.json").write_text(json.dumps({"status": "ready"}), encoding="utf-8")
    (workspace / "challenge.json").write_text(
        json.dumps(
            {
                "compose_files": ["docker-compose.yml"],
                "compose_target_services": ["app"],
                "compose_dependency_services": [],
                "target_ports": {"app": 1024},
                "target_port_protocols": {"app": "tcp"},
            }
        ),
        encoding="utf-8",
    )
    image_name = "ctfenv/pwn-ret4win-wave1:d4-r3-x0"
    calls: list[list[str]] = []

    def fake_run(cmd: list[str], **_kwargs):
        calls.append(cmd)
        if "config" in cmd:
            return _completed(
                cmd,
                stdout=json.dumps(
                    {
                        "services": {
                            "app": {
                                "build": {"context": "."},
                                "image": image_name,
                                "cap_add": ["SYS_ADMIN"],
                                "security_opt": [
                                    "apparmor:unconfined",
                                    "seccomp:unconfined",
                                ],
                            }
                        }
                    }
                ),
            )
        return _completed(cmd)

    monkeypatch.setattr(module, "_run", fake_run)
    ctx = module.ScoringContext(
        trial_id="unsafe-sysadmin-runtime",
        trial_index=0,
        sample={"image_name": image_name, "image_names": [image_name]},
        trial_dir=trial_dir,
        run_dir=trial_dir,
    )

    score = module._BootCheckScorer().score(ctx)["build_target"]

    assert score.value == 0.0
    assert score.metadata["failure_class"] == "compose_runtime_unsafe"
    assert score.metadata["evidence"]["violations"] == [
        {"service": "app", "field": "cap_add", "value": ["SYS_ADMIN"]},
        {
            "service": "app",
            "field": "security_opt",
            "value": ["apparmor:unconfined", "seccomp:unconfined"],
        },
    ]
    assert "SYS_ADMIN" in score.metadata["feedback"]
    assert "apparmor:unconfined" in score.metadata["feedback"]
    assert not any("up" in cmd for cmd in calls)


def test_scorer_challenge_feedback_includes_literal_example(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    module = _load_module()
    trial_dir = tmp_path / "trial"
    workspace = trial_dir / "workspace"
    workspace.mkdir(parents=True)
    (workspace / "docker-compose.yml").write_text("services: {}\n", encoding="utf-8")
    (workspace / "build_report.json").write_text(json.dumps({"status": "ready"}), encoding="utf-8")
    (workspace / "challenge.json").write_text(
        json.dumps(
            {
                "compose_files": ["docker-compose.yml"],
                "compose_target_services": ["app"],
                "compose_dependency_services": [],
                "target_ports": 1024,
            }
        ),
        encoding="utf-8",
    )
    image_name = "ctfenv/pwn-ret4win-wave1:d4-r3-x0"

    def fake_run(cmd: list[str], **_kwargs):
        if "config" in cmd:
            return _completed(
                cmd,
                stdout=json.dumps(
                    {
                        "services": {
                            "app": {
                                "build": {"context": "."},
                                "image": image_name,
                            }
                        }
                    }
                ),
            )
        return _completed(cmd)

    monkeypatch.setattr(module, "_run", fake_run)
    ctx = module.ScoringContext(
        trial_id="challenge-feedback",
        trial_index=0,
        sample={
            "image_name": image_name,
            "image_names": [image_name],
            "internal_port": 1024,
        },
        trial_dir=trial_dir,
        run_dir=trial_dir,
    )

    score = module._BootCheckScorer().score(ctx)["build_target"]

    assert score.value == 0.0
    assert score.metadata["failure_class"] == "challenge_json_invalid"
    assert '"target_ports": {' in score.metadata["feedback"]
    assert '"app": 1024' in score.metadata["feedback"]
    assert '"target_port_protocols": {' in score.metadata["feedback"]


def test_r4_contract_requires_writeup_backed_semantic_probe(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    module = _load_module()
    material_root = tmp_path / "materials"
    material_root.mkdir()
    writeup = material_root / "solve.md"
    writeup.write_text("The service opens with Choice: before reading option 1.\n", encoding="utf-8")

    trial_dir = tmp_path / "trial"
    workspace = trial_dir / "workspace"
    workspace.mkdir(parents=True)
    image_name = "ctfenv/pwn-semantic-wave4:d4-r4-x0"
    (workspace / "docker-compose.yml").write_text("services: {}\n", encoding="utf-8")
    (workspace / "build_report.json").write_text(
        json.dumps({"status": "ready"}), encoding="utf-8"
    )
    (workspace / "challenge.json").write_text(
        json.dumps(
            {
                "compose_files": ["docker-compose.yml"],
                "compose_target_services": ["challenge"],
                "compose_dependency_services": [],
                "target_ports": {"challenge": 31337},
                "target_port_protocols": {"challenge": "tcp"},
                "runtime_probes": [
                    {
                        "id": "menu",
                        "type": "tcp",
                        "service": "challenge",
                        "steps": [{"expect_contains": "Choice: "}],
                        "evidence": [
                            {
                                "path": "solve.md",
                                "basis": "the supplied solve waits for this prompt",
                            }
                        ],
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    def fake_run(cmd: list[str], **_kwargs):
        if "config" in cmd:
            return _completed(
                cmd,
                stdout=json.dumps(
                    {
                        "services": {
                            "challenge": {
                                "build": {"context": "."},
                                "image": image_name,
                            }
                        }
                    }
                ),
            )
        return _completed(cmd)

    monkeypatch.setattr(module, "_run", fake_run)
    ctx = module.ScoringContext(
        trial_id="semantic-contract",
        trial_index=0,
        sample={
            "image_name": image_name,
            "image_names": [image_name],
            "target_maturity": {"rehost": "R4"},
            "challenge_path": str(material_root),
            "materials": {"writeups": ["solve.md"]},
        },
        trial_dir=trial_dir,
        run_dir=trial_dir,
    )

    contract, failure = module._BootCheckScorer()._load_workspace_contract(ctx)

    assert failure is None
    assert contract is not None
    assert contract["runtime_probes_required"] is True
    evidence = contract["runtime_probes"][0]["evidence"][0]
    assert evidence["role"] == "writeups"
    assert evidence["sha256"] == module._sha256_file(writeup)


def test_r4_contract_rejects_missing_semantic_probe(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    module = _load_module()
    material_root = tmp_path / "materials"
    material_root.mkdir()
    (material_root / "solve.md").write_text("Choice: ", encoding="utf-8")
    trial_dir = tmp_path / "trial"
    workspace = trial_dir / "workspace"
    workspace.mkdir(parents=True)
    image_name = "ctfenv/pwn-no-probe-wave4:d4-r4-x0"
    (workspace / "docker-compose.yml").write_text("services: {}\n", encoding="utf-8")
    (workspace / "build_report.json").write_text(
        json.dumps({"status": "ready"}), encoding="utf-8"
    )
    (workspace / "challenge.json").write_text(
        json.dumps(
            {
                "compose_files": ["docker-compose.yml"],
                "compose_target_services": ["challenge"],
                "target_ports": {"challenge": 31337},
            }
        ),
        encoding="utf-8",
    )

    def fake_run(cmd: list[str], **_kwargs):
        if "config" in cmd:
            return _completed(
                cmd,
                stdout=json.dumps(
                    {
                        "services": {
                            "challenge": {
                                "build": {"context": "."},
                                "image": image_name,
                            }
                        }
                    }
                ),
            )
        return _completed(cmd)

    monkeypatch.setattr(module, "_run", fake_run)
    ctx = module.ScoringContext(
        trial_id="missing-semantic-probe",
        trial_index=0,
        sample={
            "image_name": image_name,
            "image_names": [image_name],
            "target_maturity": {"rehost": "R4"},
            "challenge_path": str(material_root),
            "materials": {"writeups": ["solve.md"]},
        },
        trial_dir=trial_dir,
        run_dir=trial_dir,
    )

    _, failure = module._BootCheckScorer()._load_workspace_contract(ctx)

    assert failure is not None
    score = failure["build_target"]
    assert score.metadata["failure_class"] == "runtime_probe_contract_missing"
    assert "port liveness is only R3" in score.explanation


def test_scorer_rejects_expected_tag_on_pull_only_service(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    module = _load_module()
    trial_dir = tmp_path / "trial"
    workspace = trial_dir / "workspace"
    workspace.mkdir(parents=True)
    (workspace / "docker-compose.yml").write_text("services: {}\n", encoding="utf-8")
    (workspace / "build_report.json").write_text(json.dumps({"status": "ready"}), encoding="utf-8")
    (workspace / "challenge.json").write_text(
        json.dumps(
            {
                "compose_files": ["docker-compose.yml"],
                "compose_target_services": ["web"],
                "compose_dependency_services": [],
                "target_ports": {"web": 80},
                "target_port_protocols": {"web": "http"},
            }
        ),
        encoding="utf-8",
    )
    image_name = "ctfenv/web-demo-wave1:d4-r3-x0"
    calls: list[list[str]] = []

    def fake_run(cmd: list[str], **_kwargs):
        calls.append(cmd)
        return _completed(
            cmd,
            stdout=json.dumps({"services": {"web": {"image": image_name}}}),
        )

    monkeypatch.setattr(module, "_run", fake_run)
    ctx = module.ScoringContext(
        trial_id="trial-2",
        trial_index=0,
        sample={"image_name": image_name, "image_names": [image_name]},
        trial_dir=trial_dir,
        run_dir=trial_dir,
    )

    score = module._BootCheckScorer().score(ctx)["build_target"]

    assert score.value == 0.0
    assert score.metadata["failure_class"] == "image_contract_mismatch"
    assert not any("up" in cmd for cmd in calls)


def test_scorer_uses_managed_runtime_compose_for_ports_and_subnet(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    module = _load_module()
    trial_dir = tmp_path / "trial"
    workspace = trial_dir / "workspace"
    workspace.mkdir(parents=True)
    (workspace / "docker-compose.yml").write_text(
        "\n".join(
            [
                'version: "3"',
                "services:",
                "  challenge:",
                "    image: ctfenv/pwn-ret4win-wave1:d4-r3-x0",
                "    build:",
                "      context: .",
                "    pids_limit: 999999",
                "    ports:",
                '      - "31337:1024"',
                "  helper:",
                "    image: helper:latest",
                "    pids_limit: 128",
                "",
            ]
        ),
        encoding="utf-8",
    )
    (workspace / "build_report.json").write_text(
        json.dumps(
            {
                "status": "ready",
                "data_tier": "D4",
                "build_profile": "official_deployment",
                "category_profile": "pwn",
                "pwn_runtime": {
                    "material_priority": "dockerfile_writeup_attachments",
                    "selection_basis": "musl runtime in image",
                    "evidence": [],
                    "selected_bundle": None,
                    "confidence": "confirmed",
                    "authenticity_status": "confirmed_by_deployment",
                },
            }
        ),
        encoding="utf-8",
    )
    (workspace / "challenge.json").write_text(
        json.dumps(
            {
                "compose_files": ["docker-compose.yml"],
                "compose_target_services": ["challenge"],
                "compose_dependency_services": [],
                # Deliberately copy the published side. CAGE owns host-port
                # allocation and must resolve this to the internal target.
                "target_ports": {"challenge": 31337},
                "target_port_protocols": {"challenge": "tcp"},
            }
        ),
        encoding="utf-8",
    )
    image_name = "ctfenv/pwn-ret4win-wave1:d4-r3-x0"

    calls: list[list[str]] = []

    def fake_run(cmd: list[str], **_kwargs):
        calls.append(cmd)
        if "config" in cmd:
            return _completed(
                cmd,
                stdout=json.dumps(
                    {
                        "networks": {},
                        "services": {
                            "challenge": {
                                "build": {"context": "."},
                                "image": image_name,
                                "ports": [
                                    {
                                        "mode": "ingress",
                                        "target": 1024,
                                        "published": "31337",
                                        "protocol": "tcp",
                                    }
                                ],
                            }
                        }
                    }
                ),
            )
        if cmd[:4] == ["docker", "network", "ls", "--format"]:
            return _completed(cmd, stdout="")
        if cmd[:3] == ["docker", "network", "inspect"]:
            return _completed(cmd, stdout="[]")
        if cmd[:4] == ["ip", "-4", "route", "show"]:
            return _completed(cmd, stdout="default via 192.168.1.1 dev eth0\n192.168.1.0/24 dev eth0\n")
        if "up" in cmd:
            compose_path = Path(cmd[cmd.index("-f") + 1])
            rendered = compose_path.read_text(encoding="utf-8")
            managed = yaml.safe_load(rendered)
            assert compose_path.name == ".cage-validator.compose.yml"
            assert "ports:" not in rendered
            assert "subnet:" in rendered
            assert (
                managed["services"]["challenge"]["pids_limit"]
                == module.DEFAULT_VALIDATOR_PIDS_LIMIT
            )
            assert managed["services"]["helper"]["pids_limit"] == 128
            return _completed(cmd)
        if "ps" in cmd:
            return _completed(cmd, stdout="container-id\n")
        if cmd[:2] == ["docker", "inspect"]:
            return _completed(
                cmd,
                stdout=json.dumps(
                    {
                        "State": {"Status": "running"},
                        "NetworkSettings": {
                            "Networks": {"buildcheck_default": {"IPAddress": "10.240.0.2"}}
                        },
                    }
                ),
            )
        if "logs" in cmd:
            return _completed(cmd, stdout="challenge ready\n")
        if cmd[:3] == ["docker", "image", "inspect"]:
            return _completed(
                cmd,
                stdout=json.dumps(
                    {
                        "Id": "sha256:auto-managed-id",
                        "RepoTags": [image_name],
                        "RepoDigests": [],
                        "Created": "2026-07-14T00:00:00Z",
                        "Size": 2048,
                    }
                ),
            )
        return _completed(cmd)

    monkeypatch.setattr(module, "_run", fake_run)
    monkeypatch.setattr(module, "_await_target_readiness", _all_targets_ready)
    ctx = module.ScoringContext(
        trial_id="pool-exhaustion",
        trial_index=0,
        sample={
            "image_name": image_name,
            "image_names": [image_name],
            "pwn_material_priority": {"id": "dockerfile_writeup_attachments"},
        },
        trial_dir=trial_dir,
        run_dir=trial_dir,
    )

    score = module._BootCheckScorer().score(ctx)["build_target"]

    assert score.value == 1.0
    assert score.metadata["failure_class"] is None
    assert score.metadata["targets"][0]["internal_port"] == 1024
    up_calls = [cmd for cmd in calls if "up" in cmd]
    assert len(up_calls) == 1


def test_network_pool_retry_preserves_managed_flag_injection(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    module = _load_module()
    trial_dir = tmp_path / "trial"
    workspace = trial_dir / "workspace"
    workspace.mkdir(parents=True)
    compose_path = workspace / "docker-compose.yml"
    image_name = "ctf-env:pwn-network-retry"
    compose_path.write_text(
        "\n".join(
            [
                "services:",
                "  challenge:",
                f"    image: {image_name}",
                "    build:",
                "      context: .",
                "    ports:",
                '      - "31337:3000"',
                "",
            ]
        ),
        encoding="utf-8",
    )
    (workspace / "solve").mkdir()
    (workspace / "solve" / "solve.py").write_text("print('solve')\n", encoding="utf-8")

    config_data = {
        "networks": {},
        "services": {
            "challenge": {
                "build": {"context": "."},
                "image": image_name,
                "ports": [
                    {
                        "mode": "ingress",
                        "target": 3000,
                        "published": "31337",
                        "protocol": "tcp",
                    }
                ],
            }
        },
    }
    scorer = module._BootCheckScorer(exploit_gate=True)
    ctx = module.ScoringContext(
        trial_id="network-retry",
        trial_index=0,
        sample={},
        trial_dir=trial_dir,
        run_dir=trial_dir,
    )
    contract = {
        "workspace": workspace,
        "compose_path": compose_path,
        "build_report": {"status": "ready"},
        "expected_images": [image_name],
        "build_services_by_image": {image_name: ["challenge"]},
        "target_services": ["challenge"],
        "target_ports": {"challenge": 3000},
        "target_port_protocols": {"challenge": "tcp"},
        "config_data": config_data,
        "solve": {"entry": "python3 solve.py", "service": "challenge"},
        "exploit_required": True,
        "flag_contract": {
            "inject": "file",
            "service": "challenge",
            "path": "/app/flag.txt",
        },
        "runtime_probes": [],
        "runtime_probes_required": False,
        "agent_network_hint": None,
    }
    monkeypatch.setattr(scorer, "_load_workspace_contract", lambda _ctx: (contract, None))
    monkeypatch.setattr(
        scorer,
        "_run_exploit_validation",
        lambda **_kwargs: {
            "passed": True,
            "captured": True,
            "observation": "captured",
            "returncode": 0,
            "error": None,
            "evidence": None,
            "stdout_tail": "captured",
            "stderr_tail": "",
        },
    )

    calls: list[list[str]] = []
    up_attempts = 0

    def fake_run(cmd: list[str], **_kwargs):
        nonlocal up_attempts
        calls.append(cmd)
        if cmd[:4] == ["docker", "network", "ls", "--format"]:
            return _completed(cmd, stdout="")
        if cmd[:3] == ["docker", "network", "inspect"]:
            return _completed(cmd, stdout="[]")
        if cmd[:4] == ["ip", "-4", "route", "show"]:
            return _completed(cmd, stdout="default via 192.168.1.1 dev eth0\n")
        if "up" in cmd:
            up_attempts += 1
            compose_files = [
                Path(cmd[index + 1])
                for index, value in enumerate(cmd)
                if value == "-f"
            ]
            if up_attempts == 1:
                assert [path.name for path in compose_files] == [
                    ".cage-validator.compose.yml"
                ]
                return _completed(
                    cmd,
                    returncode=1,
                    stderr=(
                        "failed to create network: invalid pool request: "
                        "Pool overlaps with other one on this address space"
                    ),
                )

            assert [path.name for path in compose_files] == [
                ".cage-validator.compose.yml",
                next(path.name for path in compose_files if "managed-networks" in path.name),
            ]
            managed = yaml.safe_load(compose_files[0].read_text(encoding="utf-8"))
            volumes = managed["services"]["challenge"]["volumes"]
            injected = next(volume for volume in volumes if volume["target"] == "/app/flag.txt")
            assert injected["type"] == "bind"
            assert injected["read_only"] is True
            assert Path(injected["source"]).read_text(encoding="utf-8").startswith("FAKE{")
            return _completed(cmd)
        if "ps" in cmd:
            return _completed(cmd, stdout="container-id\n")
        if cmd[:2] == ["docker", "inspect"]:
            return _completed(
                cmd,
                stdout=json.dumps(
                    {
                        "State": {"Status": "running"},
                        "NetworkSettings": {
                            "Networks": {
                                "buildcheck_default": {"IPAddress": "10.240.1.2"}
                            }
                        },
                    }
                ),
            )
        if "logs" in cmd:
            return _completed(cmd, stdout="ready\n")
        if cmd[:3] == ["docker", "image", "inspect"]:
            return _completed(
                cmd,
                stdout=json.dumps(
                    {
                        "Id": "sha256:network-retry",
                        "RepoTags": [image_name],
                        "RepoDigests": [],
                        "Created": "2026-08-03T00:00:00Z",
                        "Size": 2048,
                    }
                ),
            )
        return _completed(cmd)

    monkeypatch.setattr(module, "_run", fake_run)
    monkeypatch.setattr(module, "_await_target_readiness", _all_targets_ready)
    scores, runtime = scorer._run_validation(ctx, keep_runtime=False)

    assert runtime is None
    assert scores["build_target"].value == 1.0
    assert scores["build_target"].metadata["managed_network_retries"] == 1
    assert scorer._payload_from_scores(scores)["managed_network_retries"] == 1
    assert up_attempts == 2
    second_up = [cmd for cmd in calls if "up" in cmd][1]
    assert ".cage-validator.compose.yml" in " ".join(second_up)


def test_validation_recreates_and_reflags_target_before_each_r5_attempt(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module = _load_module()
    trial_dir = tmp_path / "trial"
    workspace = trial_dir / "workspace"
    workspace.mkdir(parents=True)
    compose_path = workspace / "docker-compose.yml"
    compose_path.write_text(
        "services:\n"
        "  challenge:\n"
        "    image: ctf-env:pwn-fresh-r5\n"
        "    build: .\n",
        encoding="utf-8",
    )
    (workspace / "solve").mkdir()
    (workspace / "solve" / "solve.py").write_text(
        "print('solve')\n", encoding="utf-8"
    )

    scorer = module._BootCheckScorer(exploit_gate=True, exploit_attempts=3)
    ctx = module.ScoringContext(
        trial_id="fresh-r5",
        trial_index=0,
        sample={},
        trial_dir=trial_dir,
        run_dir=trial_dir,
    )
    contract = {
        "workspace": workspace,
        "compose_path": compose_path,
        "build_report": {"status": "ready"},
        "expected_images": ["ctf-env:pwn-fresh-r5"],
        "build_services_by_image": {"ctf-env:pwn-fresh-r5": ["challenge"]},
        "target_services": ["challenge"],
        "target_ports": {"challenge": 1337},
        "target_port_protocols": {"challenge": "tcp"},
        "config_data": {
            "networks": {},
            "services": {
                "challenge": {
                    "image": "ctf-env:pwn-fresh-r5",
                    "build": {"context": "."},
                }
            },
        },
        "solve": {"entry": "python3 solve.py", "service": "challenge"},
        "exploit_required": True,
        "flag_contract": {
            "inject": "file",
            "service": "challenge",
            "path": "/flag.txt",
            "format": "flag{...}",
        },
        "runtime_probes": [],
        "runtime_probes_required": False,
        "agent_network_hint": None,
    }
    monkeypatch.setattr(scorer, "_load_workspace_contract", lambda _ctx: (contract, None))
    monkeypatch.setattr(module.time, "sleep", lambda _seconds: None)

    minted = iter(["flag{initial}", "flag{attempt-one}", "flag{attempt-two}"])
    monkeypatch.setattr(module, "_mint_random_flag", lambda _format: next(minted))
    injected_flags: list[str | None] = []

    def fake_write_runtime_compose(**kwargs):
        injected_flags.append(kwargs.get("injected_flag"))
        return compose_path, []

    monkeypatch.setattr(
        scorer,
        "_write_managed_runtime_compose",
        fake_write_runtime_compose,
    )

    calls: list[list[str]] = []
    up_count = 0

    def fake_run(cmd: list[str], **_kwargs):
        nonlocal up_count
        calls.append(list(cmd))
        if "up" in cmd:
            up_count += 1
            if up_count == 1:
                assert "--build" in cmd
                assert "--no-build" not in cmd
            else:
                assert "--no-build" in cmd
                assert "--build" not in cmd
                assert "--force-recreate" in cmd
                assert "--renew-anon-volumes" in cmd
            return _completed(cmd)
        if "ps" in cmd:
            return _completed(cmd, stdout=f"container-{up_count}\n")
        if cmd[:2] == ["docker", "inspect"]:
            return _completed(
                cmd,
                stdout=json.dumps(
                    {
                        "State": {"Status": "running"},
                        "NetworkSettings": {
                            "Networks": {
                                "buildcheck_default": {
                                    "IPAddress": f"10.240.{up_count}.2"
                                }
                            }
                        },
                    }
                ),
            )
        if "logs" in cmd:
            return _completed(cmd, stdout=f"target boot {up_count}\n")
        if cmd[:3] == ["docker", "image", "inspect"]:
            return _completed(
                cmd,
                stdout=json.dumps(
                    {
                        "Id": "sha256:fresh-r5",
                        "RepoTags": ["ctf-env:pwn-fresh-r5"],
                        "RepoDigests": [],
                        "Created": "2026-08-04T00:00:00Z",
                        "Size": 4096,
                    }
                ),
            )
        return _completed(cmd)

    monkeypatch.setattr(module, "_run", fake_run)
    monkeypatch.setattr(module, "_await_target_readiness", _all_targets_ready)
    prepared: list[dict] = []

    def fake_exploit_validation(**kwargs):
        first = kwargs["prepare_attempt"](1)
        second = kwargs["prepare_attempt"](2)
        prepared.extend([first, second])
        return {
            "passed": True,
            "captured": True,
            "attempt_count": 2,
            "max_attempts": 3,
            "successful_attempt": 2,
            "attempts": [],
            "observation": "captured on a fresh target",
            "returncode": 0,
            "error": None,
            "evidence": None,
            "stdout_tail": "flag captured",
            "stderr_tail": "",
        }

    monkeypatch.setattr(scorer, "_run_exploit_validation", fake_exploit_validation)
    scores, runtime = scorer._run_validation(ctx, keep_runtime=False)

    assert runtime is None
    assert scores["build_target"].metadata["validated_rehost_tier"] == "R5"
    assert up_count == 3
    assert injected_flags == [
        "flag{initial}",
        "flag{attempt-one}",
        "flag{attempt-two}",
    ]
    assert [item["flag"] for item in prepared] == injected_flags[1:]
    assert [
        item["target_instance"]["container_ids"] for item in prepared
    ] == [["container-2"], ["container-3"]]
    down_calls = [cmd for cmd in calls if "down" in cmd]
    assert len(down_calls) == 3


def test_managed_subnet_allocations_are_distinct_under_validator_concurrency(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module = _load_module()
    scorer = module._BootCheckScorer()
    monkeypatch.setattr(scorer, "_list_reserved_ipv4_subnets", lambda: set())

    with ThreadPoolExecutor(max_workers=8) as pool:
        allocations = list(
            pool.map(
                lambda index: scorer._allocate_managed_subnets(
                    1, seed="same-concurrent-project"
                ),
                range(8),
            )
        )

    flattened = [subnets[0] for subnets in allocations]
    assert len(set(flattened)) == 8
    assert len(module._MANAGED_SUBNET_RESERVATIONS) == 8
    for subnets in allocations:
        scorer._release_managed_subnets(subnets)
    assert module._MANAGED_SUBNET_RESERVATIONS == set()


def test_persistent_network_overlap_is_host_retryable_after_bounded_reallocation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    module = _load_module()
    trial_dir = tmp_path / "trial"
    workspace = trial_dir / "workspace"
    workspace.mkdir(parents=True)
    compose_path = workspace / "docker-compose.yml"
    compose_path.write_text(
        "services:\n"
        "  challenge:\n"
        "    image: ctf-env:pwn-network-contention\n"
        "    build: .\n",
        encoding="utf-8",
    )
    config_data = {
        "networks": {},
        "services": {
            "challenge": {
                "build": {"context": "."},
                "image": "ctf-env:pwn-network-contention",
            }
        },
    }
    scorer = module._BootCheckScorer()
    ctx = module.ScoringContext(
        trial_id="network-contention",
        trial_index=0,
        sample={},
        trial_dir=trial_dir,
        run_dir=trial_dir,
    )
    contract = {
        "workspace": workspace,
        "compose_path": compose_path,
        "build_report": {"status": "ready"},
        "expected_images": ["ctf-env:pwn-network-contention"],
        "build_services_by_image": {
            "ctf-env:pwn-network-contention": ["challenge"]
        },
        "target_services": ["challenge"],
        "target_ports": {"challenge": 1337},
        "target_port_protocols": {"challenge": "tcp"},
        "config_data": config_data,
        "solve": {},
        "exploit_required": False,
        "runtime_probes": [],
        "runtime_probes_required": False,
        "agent_network_hint": None,
    }
    monkeypatch.setattr(scorer, "_load_workspace_contract", lambda _ctx: (contract, None))

    up_attempts = 0

    def fake_run(cmd: list[str], **_kwargs):
        nonlocal up_attempts
        if cmd[:4] == ["docker", "network", "ls", "--format"]:
            return _completed(cmd, stdout="")
        if cmd[:4] == ["ip", "-4", "route", "show"]:
            return _completed(cmd, stdout="default via 192.168.1.1 dev eth0\n")
        if "up" in cmd:
            up_attempts += 1
            return _completed(
                cmd,
                returncode=1,
                stderr=(
                    "failed to create network: invalid pool request: "
                    "Pool overlaps with other one on this address space"
                ),
            )
        return _completed(cmd)

    monkeypatch.setattr(module, "_run", fake_run)
    scores, runtime = scorer._run_validation(ctx, keep_runtime=False)
    metadata = scores["build_target"].metadata

    assert runtime is None
    assert up_attempts == 1 + module._MAX_MANAGED_NETWORK_RETRIES
    assert metadata["failure_class"] == "host_runtime_network_exhausted"
    assert metadata["retryable"] is True
    assert metadata["evidence"]["managed_network_retries"] == 3
    assert "not a defect in the candidate workspace" in metadata["feedback"]
    assert "retry the unchanged `cage-check --json`" in metadata["feedback"]
    assert module._MANAGED_SUBNET_RESERVATIONS == set()


def test_agent_declared_ipam_conflict_remains_a_candidate_build_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    module = _load_module()
    trial_dir = tmp_path / "trial"
    workspace = trial_dir / "workspace"
    workspace.mkdir(parents=True)
    compose_path = workspace / "docker-compose.yml"
    image_name = "ctf-env:pwn-authored-ipam"
    compose_path.write_text(
        "services:\n"
        "  challenge:\n"
        f"    image: {image_name}\n"
        "    build: .\n"
        "    networks: [challenge_net]\n"
        "networks:\n"
        "  challenge_net:\n"
        "    ipam:\n"
        "      config:\n"
        "        - subnet: 172.18.0.0/16\n",
        encoding="utf-8",
    )
    config_data = {
        "networks": {
            "challenge_net": {
                "name": "authored-ipam",
                "ipam": {"config": [{"subnet": "172.18.0.0/16"}]},
            }
        },
        "services": {
            "challenge": {
                "build": {"context": "."},
                "image": image_name,
                "networks": {"challenge_net": None},
            }
        },
    }
    scorer = module._BootCheckScorer()
    ctx = module.ScoringContext(
        trial_id="authored-ipam",
        trial_index=0,
        sample={},
        trial_dir=trial_dir,
        run_dir=trial_dir,
    )
    contract = {
        "workspace": workspace,
        "compose_path": compose_path,
        "build_report": {"status": "ready"},
        "expected_images": [image_name],
        "build_services_by_image": {image_name: ["challenge"]},
        "target_services": ["challenge"],
        "target_ports": {"challenge": 1337},
        "target_port_protocols": {"challenge": "tcp"},
        "config_data": config_data,
        "solve": {},
        "exploit_required": False,
        "runtime_probes": [],
        "runtime_probes_required": False,
        "agent_network_hint": None,
    }
    monkeypatch.setattr(scorer, "_load_workspace_contract", lambda _ctx: (contract, None))
    up_attempts = 0

    def fake_run(cmd: list[str], **_kwargs):
        nonlocal up_attempts
        if "up" in cmd:
            up_attempts += 1
            return _completed(
                cmd,
                returncode=1,
                stderr="invalid pool request: Pool overlaps with other one on this address space",
            )
        return _completed(cmd)

    monkeypatch.setattr(module, "_run", fake_run)
    scores, runtime = scorer._run_validation(ctx, keep_runtime=False)
    metadata = scores["build_target"].metadata

    assert runtime is None
    assert up_attempts == 1
    assert metadata["failure_class"] == "build_or_boot_failed"
    assert metadata["retryable"] is True
    assert metadata["evidence"]["auto_managed_network"] is False
    assert metadata["evidence"]["managed_network_retries"] == 0
    assert "change one causal build-closure dimension" in metadata["feedback"]



def test_prompt_requires_final_probe_excerpt_after_live_pass(tmp_path: Path) -> None:
    module = _load_module()
    sample_dir = _write_task(
        tmp_path,
        {
            "name": "probe-final-report",
            "category": "web",
            "data_tier": "D4",
            "target_maturity": {"data": "D4", "rehost": "R4", "exploit": "X0"},
            "materials": {
                "deployment": ["Dockerfile"],
                "writeups": ["writeup.md"],
            },
            "image_name": "ctfenv/web-probe-final-report-wave4:d4-r4-x0",
        },
    )
    (sample_dir / "Dockerfile").write_text("FROM scratch\n", encoding="utf-8")
    (sample_dir / "writeup.md").write_text("GET / shows Probe App", encoding="utf-8")

    sample = _one_sample(module, tmp_path)
    prompt = module.BuildTarget(tmp_path).build_prompt(sample)

    assert "`cage-check` itself is the independent validator" in prompt
    assert "challenge.json.runtime_probes` is mandatory" in prompt
    assert "quote or summarize the returned host-side probe excerpt" in prompt
    assert "port-open or process-liveness observation cannot promote" in prompt


@pytest.mark.parametrize(
    ("profile", "route", "with_writeup"),
    [
        ("AWPB", "fast_track_full", True),
        ("APB", "fast_track_no_writeup", False),
    ],
)
def test_full_joint_prompt_surfaces_formal_abp_material_and_joint_plan(
    tmp_path: Path,
    profile: str,
    route: str,
    with_writeup: bool,
) -> None:
    module = _load_module()
    materials = {
        "attachments": ["materials/attachments"],
        "deployment": ["materials/deployment"],
        "exploit": ["materials/exploit"],
        "source": [],
        "writeups": ["materials/writeups"] if with_writeup else [],
    }
    sample_dir = _write_task(
        tmp_path,
        {
            "name": f"joint-{profile.lower()}",
            "category": "pwn",
            "data_tier": "D4",
            "material_profile": profile,
            "pipeline_route": route,
            "materials": materials,
            "image_name": f"ctfenv/pwn-joint-{profile.lower()}:control",
        },
    )
    for role in ("attachments", "deployment", "exploit"):
        (sample_dir / "materials" / role).mkdir(parents=True)
    (sample_dir / "materials" / "attachments" / "chall").write_bytes(b"\x7fELF")
    (sample_dir / "materials" / "deployment" / "Dockerfile").write_text(
        "FROM scratch\nCOPY chall /chall\n",
        encoding="utf-8",
    )
    (sample_dir / "materials" / "exploit" / "solve.py").write_text(
        "print('solver')\n",
        encoding="utf-8",
    )
    if with_writeup:
        (sample_dir / "materials" / "writeups").mkdir(parents=True)
        (sample_dir / "materials" / "writeups" / "README.md").write_text(
            "intended primitive\n",
            encoding="utf-8",
        )

    benchmark = module.BuildTarget(
        tmp_path,
        pipeline_prompts=True,
        pipeline_stage="full",
        exploit_gate=True,
    )
    sample = next(benchmark.iter_samples())
    prompt = benchmark.build_prompt(sample)

    assert sample["material_profile"] == profile
    assert sample["pipeline_route"] == route
    assert sample["startup_reminder_at"] == 4
    assert sample["startup_reminder_until"] == 16
    assert "EARLY DELIVERY GATE" in sample["startup_reminder_message"]
    assert "act on the delivery gate **in this model turn**" in sample[
        "startup_reminder_message"
    ]
    assert "do not call WebSearch/WebFetch" in sample["startup_reminder_message"]
    assert "`cage-check` is the only authority for build, runtime, and" in sample[
        "startup_reminder_message"
    ]
    assert (
        f"- `ctfenv/pwn-joint-{profile.lower()}:control`"
        in sample["startup_reminder_message"]
    )
    assert sample["wrapup_before"] == 20
    assert "only twenty model rounds remain" in sample["wrapup_message"]
    assert "education.json" in sample["wrapup_message"]
    assert "run at most one final `cage-check --json`" in " ".join(
        sample["wrapup_message"].split()
    )
    assert "pwn_runtime" in sample["wrapup_message"]
    assert "selected_files.libc" in sample["wrapup_message"]
    assert "vulnerability-bearing served target" in sample["wrapup_message"]
    assert "a host-tooling copy" in sample["wrapup_message"]
    assert "browser/V8" in sample["wrapup_message"]
    assert "does not mean that the exploit or R5" in sample["wrapup_message"]
    assert "`cage-check` is the only authority for build," in sample["wrapup_message"]
    assert "Never reproduce the complete target in the" in sample["wrapup_message"]
    assert "never run cage-check" in sample["wrapup_message"]
    assert "stop every background relay" in sample["wrapup_message"]
    assert '"compose_files": ["docker-compose.yml"]' in sample["wrapup_message"]
    assert "remove host `ports:`" in sample["wrapup_message"]
    assert (
        f"- `ctfenv/pwn-joint-{profile.lower()}:control`"
        in sample["wrapup_message"]
    )
    assert "no title, event, challenge, category" in sample["wrapup_message"]
    assert "`custom-allocator`" in sample["wrapup_message"]
    assert f"- `material_profile`: `{profile}`" in sample["wrapup_message"]
    assert f"- `pipeline_route`: `{route}`" in sample["wrapup_message"]
    assert "- `build_source`: `use_build_material`" in sample["wrapup_message"]
    assert "- `exploit_source`: `adapt_existing`" in sample["wrapup_message"]
    assert "- `pwn_runtime.material_priority`:" in sample["wrapup_message"]
    from cage.contracts.execution import resolve_wrapup

    assert resolve_wrapup(
        200,
        None,
        None,
        sample["wrapup_before"],
        sample["wrapup_message"],
    ) == (180, sample["wrapup_message"])
    assert f"formal material profile: `{profile}`" in prompt
    assert f"formal pipeline route: `{route}`" in prompt
    assert "episode plan: `joint`" in prompt
    assert "## attachments" in prompt
    assert "## deployment" in prompt
    assert "## exploit" in prompt
    assert ("## writeups" in prompt) is with_writeup
    assert '"validated_rehost_tier": "R5"' in prompt
    assert "cage-exploit" not in prompt
    assert "mechanical endpoint/path adaptation" in prompt
    assert "identical\nnon-PIE binary" in prompt
    assert "leave `runtime_probes` empty" in prompt
    assert '"type": "tcp"' in prompt
    assert "Copy the complete supplied exploit entry" in prompt
    assert "preserve that complete\nbinary-plus-driver chain" in prompt
    assert "never preinstall it in the\ntarget unless the historical" in prompt
    assert "kernel-symbol extraction" in " ".join(prompt.split())
    assert "Before observed R5 it must remain `unresolved`" in prompt
    assert "`objdump -d`" in prompt
    assert "service-level `image:` next to" in prompt
    assert "build.tags" in prompt
    assert "files resolved by the actual Dockerfile" in prompt
    assert "inspect the relevant contents of the exact consumed" in prompt
    assert "last proven link and the first unproven link" in prompt
    assert "one falsifiable hypothesis" in prompt
    assert "Do not use `cage-check` as a syntax checker" in prompt
    assert "Static preflight only; do not reproduce the target locally" in prompt
    assert "# NON-NEGOTIABLE LOCAL EXECUTION BOUNDARY" in prompt
    assert "never execute any supplied" in prompt
    assert "Never recursively run `find`, `grep`, `rg`" in " ".join(prompt.split())
    assert "host-side `cage-check` environment is the only authority" in prompt
    assert "do not run the challenge through a host or substitute" in prompt
    assert "`ready` means \"submit this candidate to `cage-check`\"" in prompt
    assert "Do not invoke the target's build or installation path" in prompt
    assert "`cargo build`, `go build`, `forge build`" in prompt
    assert "Checkpoint promptly" in prompt
    assert "before optional framework archaeology" in prompt
    assert "dependency actually compiles" in prompt
    assert "A necessary background compile/download" not in prompt
    assert "three consecutive end-to-end successes" not in prompt
    assert "changed to `ready` after local preflight" not in prompt
    assert "# EARLY DELIVERY CHECKPOINT" in prompt
    assert "cross a hard ordering boundary" in prompt
    assert "do **not** call `WebSearch`/`WebFetch`, compile" in prompt
    assert "or run `cage-check`" in prompt
    assert "Write the small root\n  contracts before a large recursive copy" in prompt
    assert "Never run `cage-check` while\n  the build report is `blocked`" in prompt
    assert "`build_report.status: \"blocked\"`" in prompt
    assert "up to five times" in prompt
    assert "one exact capture is sufficient and 5/5 is not required" in " ".join(
        prompt.split()
    )
    assert "do not revoke an exact capture" in " ".join(prompt.split())
    assert "Each invocation has its own reported solver budget" in prompt
    normalized_prompt = " ".join(prompt.split())
    assert "Before every invocation it destroys the preceding target" in normalized_prompt
    assert "injects a different fresh flag" in normalized_prompt
    assert (
        "Never depend on heap/process/VM/session state carrying across validator attempts"
        in normalized_prompt
    )
    assert "pwntools `ELF.address` rebases `symbols`" in normalized_prompt
    assert "catch expected per-attempt failures inside the loop" in normalized_prompt
    assert "non-empty output, a shell prompt" in normalized_prompt
    assert (
        "Exercise this production loop, including its exception path"
        in normalized_prompt
    )
    assert "idle timeouts: continuous input can reset them forever" in normalized_prompt
    assert "combined stdout/stderr exceeds 8 MiB" in normalized_prompt
    assert "Measure solver behavior only against a target returned by `cage-check`" in prompt
    assert (
        "exact capture proves environment R5 even if later solver cleanup exits non-zero"
        in normalized_prompt
    )
    assert "`/solve` is deliberately read-only" in prompt
    assert "separate solver-hygiene defects" in normalized_prompt
    assert "Never use `pkill`," in prompt
    assert "`ps | grep | xargs kill`" in prompt
    assert "pattern killing can\nterminate the agent itself" in prompt
    assert "pollute\nthe measured trajectory length" in prompt
    assert "Buffered `read(N)` may wait" in prompt
    assert "A timeout, EOF, empty response, open port" in prompt
    assert "self-authored marker proves only that its print site was reached" in prompt
    assert "validator injection → service/container" in prompt
    assert "/opt/cage/build-target-guides/INDEX.md" in prompt
    assert "consumed cpio/initramfs/disk/squashfs" in prompt
    assert "executed `qemu-system-*`, kernel+initrd" in prompt
    assert "FIRST GATE: SELECT GUIDES BEFORE SPECIALIZED WORK" in prompt
    assert "sed -n '1,220p' /opt/cage/build-target-guides/INDEX.md" in prompt
    assert "Do not read every linked guide without a trigger" in prompt
    assert "Multiple real triggers may require multiple small guides" in " ".join(
        prompt.split()
    )
    assert "does not include\nre-analyzing the vulnerability" in prompt
    assert "Do not create or\nmaintain a second task list" in prompt
    assert "Select from observed files/commands/boundaries" in " ".join(prompt.split())
    assert "`GUIDES: guide <- observed trigger`" in prompt
    assert (
        "`P_CHAIN: driver -> exact local helpers/prebuilt payload -> remote"
        in " ".join(prompt.split())
    )
    assert "listing or extracting an archive for inspection" in prompt
    assert "first `solve/` version must contain that exact byte-identical file" in " ".join(
        prompt.split()
    )
    assert "Freeze the real boot tuple" not in prompt
    assert "cage-check --json" in prompt
    assert '"checks_remaining"' in prompt
    assert "freezes one immutable submission" in prompt
    assert "host-side validation queue" in prompt
    assert "Do not run the check in\nthe background" in prompt
    assert '"submission_digest"' in prompt
    assert "cage-check status --json" in prompt
    assert "same `runtime_id`/`runtime_generation`" in prompt
    assert "current status `targets` describe the retained live stack" in " ".join(
        prompt.split()
    )
    assert "`build_or_boot_failed` or `build_or_boot_timeout`" in prompt
    assert "identify the first fatal\n  command or missing path" in prompt
    assert "If only `solve/` changes, continue debugging it against the retained" in prompt
    assert "the retained target is stale" in " ".join(prompt.split())
    assert "A stage-specific error in returned output can satisfy the gate" in " ".join(
        prompt.split()
    )
    assert "explicit short per-stage deadlines and flushed marker" in " ".join(
        prompt.split()
    )
    assert "must be emitted unbuffered or explicitly flushed" in prompt
    assert "sum of stage deadlines\n  must fit inside" in prompt
    assert "Keep ready status exactly" in prompt
    assert "create `education.json` at\nworkspace root" in prompt
    assert "write it even when `solve_report.json.status` must remain `unresolved`" in " ".join(
        prompt.split()
    )
    assert "2 to 5 unique tags" in prompt
    assert "use `qemu` only when QEMU or its device model is the target" in " ".join(
        prompt.split()
    )
    assert "“Get the flag” alone is invalid" in " ".join(prompt.split())
    assert "Do not mention that a supplied exploit/solution exists" in " ".join(
        prompt.split()
    )
    assert "not imperative steps" in " ".join(prompt.split())
    assert "Public internet access is an ordinary tool" in prompt
    assert "neither forbidden nor a mandatory" in prompt
    assert "Do not assume that every Pwn target needs" in prompt
    assert "kernel/QEMU guest; browser/V8 build" in prompt
    assert "`external_verified`" in prompt
    assert "Do not fetch missing challenge artifacts" not in prompt


def test_build_target_default_uses_200_rounds() -> None:
    config_path = REPO_ROOT / "examples" / "build_target" / "default_build_target.yml"
    config = yaml.safe_load(config_path.read_text(encoding="utf-8"))

    assert config["runtime"]["max_rounds"] == 200
    assert config["eval"]["benchmark"]["validation_build_timeout"] == 1800


def test_rejects_disagreeing_formal_profile_and_route(tmp_path: Path) -> None:
    module = _load_module()
    _write_task(
        tmp_path,
        {
            "name": "bad-formal-route",
            "category": "pwn",
            "material_profile": "AWPB",
            "pipeline_route": "fast_track_no_writeup",
            "materials": {
                "attachments": ["chall"],
                "deployment": ["Dockerfile"],
                "exploit": ["solve.py"],
                "writeups": ["README.md"],
            },
            "image_name": "ctfenv/pwn-bad-formal-route:control",
        },
    )

    with pytest.raises(ValueError, match="declares material_profile"):
        list(module.BuildTarget(tmp_path).iter_samples())


def test_full_staged_prompt_does_not_claim_a_supplied_exploit(tmp_path: Path) -> None:
    module = _load_module()
    sample_dir = _write_task(
        tmp_path,
        {
            "name": "staged-awb",
            "category": "pwn",
            "data_tier": "D4",
            "material_profile": "AWB",
            "pipeline_route": "build_then_generate",
            "materials": {
                "attachments": ["materials/attachments"],
                "deployment": ["materials/deployment"],
                "exploit": [],
                "source": [],
                "writeups": ["materials/writeups"],
            },
            "image_name": "ctfenv/pwn-staged-awb:control",
        },
    )
    for role in ("attachments", "deployment", "writeups"):
        (sample_dir / "materials" / role).mkdir(parents=True)
    (sample_dir / "materials" / "attachments" / "chall").write_bytes(b"\x7fELF")
    (sample_dir / "materials" / "deployment" / "Dockerfile").write_text(
        "FROM scratch\nCOPY chall /chall\n",
        encoding="utf-8",
    )
    (sample_dir / "materials" / "writeups" / "README.md").write_text(
        "generate the intended solver\n",
        encoding="utf-8",
    )

    benchmark = module.BuildTarget(
        tmp_path,
        pipeline_prompts=True,
        pipeline_stage="full",
        exploit_gate=True,
    )
    sample = next(benchmark.iter_samples())
    prompt = benchmark.build_prompt(sample)

    assert "episode plan: `staged`" in prompt
    assert "This is a `staged` episode: no supplied exploit exists." in prompt
    assert "Do not deliberately submit an incomplete schema" in prompt
    assert "Create the exploit from the route evidence" in prompt
    assert "Treat deployment and exploit" not in prompt
    assert "Copy the complete supplied exploit entry" not in prompt


@pytest.mark.parametrize(
    ("tier", "captured", "expected_passed", "expected_status"),
    [
        ("R4", False, False, "FAIL"),
        ("R5", True, True, "PASS"),
    ],
)
def test_live_joint_check_requires_objective_r5_capture_without_leaking_flag(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    tier: str,
    captured: bool,
    expected_passed: bool,
    expected_status: str,
) -> None:
    module = _load_module()
    scorer = module._BootCheckScorer(exploit_gate=True)
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    runtime = module._LiveRuntime(
        project="joint-live",
        workspace=workspace,
        compose_path=workspace / "docker-compose.yml",
        agent_container="agent",
        network_name="joint-net",
        service_targets=[
            {
                "service_name": "challenge",
                "container_addr": "10.10.0.2",
                "internal_port": 1024,
                "protocol": "tcp",
            }
        ],
    )
    minted = "FAKE{must-not-leak}"
    score = module.Score(
        value=1.0,
        answer=f"validated through {tier}",
        metadata={
            "passed": True,
            "validated_rehost_tier": tier,
            "targets": runtime.service_targets,
            "exploit_captured": captured,
            "exploit_passed": captured,
            "exploit_result": {
                "passed": captured,
                "captured": captured,
                "observation": "captured" if captured else "solver returned without capture",
                "stdout_tail": minted if captured else "EOF before flag",
                "stderr_tail": minted if captured else "STAGE login_prompt",
            },
        },
    )
    monkeypatch.setattr(
        scorer,
        "_run_validation",
        lambda *_args, **_kwargs: ({"build_target": score}, runtime),
    )
    ctx = module._LiveTrialContext(
        trial_id="joint-live",
        trial_dir=tmp_path,
        workspace=workspace,
        sample={"material_profile": "AWPB", "pipeline_route": "fast_track_full"},
        agent_container="agent",
        token="token",
    )

    payload = scorer.validate_live(ctx, check_label="check-01")

    assert payload["passed"] is expected_passed
    assert payload["required_checkpoint"] == "R5"
    assert payload["checkpoint"] == "exploit_capture"
    assert payload["checkpoint_status"] == expected_status
    public_payload = {key: value for key, value in payload.items() if key != "_runtime"}
    assert minted not in json.dumps(public_payload)
    if captured:
        assert "PASS through R5" in payload["feedback"]
    else:
        assert payload["failure_class"] == "exploit_capture_not_passed"
        assert "EXPLOIT_CAPTURE CHECKPOINT FAIL" in payload["feedback"]
        assert "recovery evidence gate before another `cage-check`" in payload["feedback"]
        assert "10.10.0.2:1024" in payload["feedback"]
        assert "emit each reached marker unbuffered" in payload["feedback"]
        assert "up to 5 times" in payload["feedback"]
        assert "separate 180s budget for each invocation" in payload["feedback"]
        assert "destroys the preceding target and non-external volumes" in payload["feedback"]
        assert "injects a different fresh flag" in payload["feedback"]
        assert "never rely on process, heap, VM, volume" in payload["feedback"]
        assert "success in every attempt is not required" in payload["feedback"]
        assert "explicit stage-specific error" in payload["feedback"]
        assert "STAGE login_prompt" in payload["feedback"]


@pytest.mark.parametrize(
    ("checkpoint_required", "tier", "captured", "expected_value"),
    [
        (False, "R3", False, 1.0),
        (True, "R3", False, 0.0),
        (True, "R5", True, 1.0),
    ],
)
def test_final_score_enforces_r5_only_when_exploit_checkpoint_is_required(
    tmp_path: Path,
    checkpoint_required: bool,
    tier: str,
    captured: bool,
    expected_value: float,
) -> None:
    module = _load_module()
    trial_dir = tmp_path / "trial"
    trial_dir.mkdir()
    ctx = module.ScoringContext(
        trial_id="joint-final",
        trial_index=0,
        sample={},
        trial_dir=trial_dir,
        run_dir=trial_dir,
    )
    score = module._BootCheckScorer(exploit_gate=True)._pass(
        ctx=ctx,
        compose_path=trial_dir / "workspace" / "docker-compose.yml",
        container_state="challenge=running",
        container_addr="10.10.0.2",
        network_name="joint-net",
        targets=[],
        service_logs="ready",
        agent_service_output="",
        build_report={"status": "ready"},
        image_evidence=[],
        image_manifest=None,
        validated_rehost_tier=tier,
        runtime_probe_results=None,
        runtime_probe_evidence=None,
        review_files={},
        exploit_result={
            "passed": captured,
            "captured": captured,
            "observation": (
                "captured" if captured else "solver returned without capture"
            ),
        },
        exploit_checkpoint_required=checkpoint_required,
    )["build_target"]

    assert score.value == expected_value
    assert score.metadata["passed"] is (expected_value == 1.0)
    assert score.metadata["validated_rehost_tier"] == tier
    if checkpoint_required and not captured:
        assert score.metadata["failure_class"] == "exploit_capture_not_passed"
        assert score.metadata["evidence"]["validated_rehost_tier"] == "R3"


def test_flag_file_injection_uses_compose_long_syntax_for_colon_path(
    tmp_path: Path,
) -> None:
    module = _load_module()
    scorer = module._BootCheckScorer(exploit_gate=True)
    managed_dir = tmp_path / "agent:model:stateless" / "validator"
    managed_dir.mkdir(parents=True)
    services = {
        "challenge": {
            "volumes": [
                "old-source:/flag.txt:ro",
                {"type": "volume", "source": "keep", "target": "/data"},
            ]
        }
    }

    scorer._inject_flag_into_services(
        services=services,
        managed_dir=managed_dir,
        flag="FAKE{private}",
        flag_contract={
            "inject": "file",
            "service": "challenge",
            "path": "/flag.txt",
        },
    )

    volumes = services["challenge"]["volumes"]
    assert len(volumes) == 2
    assert volumes[0]["target"] == "/data"
    assert volumes[1] == {
        "type": "bind",
        "source": str((managed_dir / "cage-injected-flag").resolve()),
        "target": "/flag.txt",
        "read_only": True,
    }
    assert ":" in volumes[1]["source"]


def test_minted_flag_uses_declared_prefix_and_normalized_contract_keeps_format() -> None:
    module = _load_module()

    contract = module._normalize_flag_contract(
        {
            "inject": "env",
            "service": "challenge",
            "env": "FLAG",
            "format": "BHFlagY{challenge-specific-body}",
        },
        default_service="fallback",
    )
    minted = module._mint_random_flag(contract["format"])

    assert contract["format"] == "BHFlagY{challenge-specific-body}"
    assert minted.startswith("BHFlagY{")
    assert minted.endswith("}")
    assert "challenge-specific-body" not in minted
    assert module._mint_random_flag("24h{...}").startswith("24h{")
    assert module._mint_random_flag("0xfun{...}").startswith("0xfun{")
    assert module._mint_random_flag("not-a-braced-format").startswith("FAKE{")


def test_exploit_gate_accepts_one_exact_capture_out_of_five_with_dirty_exit(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module = _load_module()
    workspace = tmp_path / "workspace"
    solve_dir = workspace / "solve"
    review_dir = tmp_path / "review"
    solve_dir.mkdir(parents=True)
    review_dir.mkdir()
    (solve_dir / "solve.py").write_text("print('solve')\n", encoding="utf-8")
    minted = "flag{private}"
    outcomes = [
        (1, "connected but no flag"),
        (1, "still no flag"),
        (0, "clean exit but no flag"),
        (1, "no capture yet"),
        (1, minted),
    ]
    calls: list[list[str]] = []

    def fake_sidecar(cmd, *, container_name, timeout, success_marker):
        del container_name
        assert timeout == 180
        assert success_marker == minted.encode()
        calls.append(list(cmd))
        returncode, stdout = outcomes[len(calls) - 1]
        return subprocess.CompletedProcess(cmd, returncode, stdout=stdout, stderr=""), False

    monkeypatch.setattr(module, "_run_managed_solver_sidecar", fake_sidecar)
    result = module._BootCheckScorer(
        exploit_gate=True,
        exploit_attempts=5,
    )._run_exploit_validation(
        ws=workspace,
        network_name="target-net",
        targets=[
            {
                "service_name": "challenge",
                "container_addr": "10.10.0.2",
                "internal_port": 1024,
            }
        ],
        solve={"service": "challenge", "entry": "python3 solve.py"},
        flag=minted,
        review_dir=review_dir,
        check_label="score",
    )

    assert len(calls) == 5
    assert result["passed"] is True
    assert result["captured"] is True
    assert result["successful_attempt"] == 5
    assert result["attempt_count"] == 5
    assert result["outcome_class"] == "retry_rescued_pass"
    assert result["solve_exit_clean"] is False
    assert result["solver_outcome_class"] == "dirty_exit"
    assert [attempt["passed"] for attempt in result["attempts"]] == [
        False, False, False, False, True
    ]
    assert [attempt["captured"] for attempt in result["attempts"]] == [
        False, False, False, False, True
    ]
    assert "Attempt 5/5" in result["observation"]
    evidence = json.loads((review_dir / "exploit_evidence.json").read_text())
    assert evidence["passed"] is True
    assert evidence["successful_attempt"] == 5
    assert evidence["outcome_class"] == "retry_rescued_pass"
    assert evidence["solve_exit_clean"] is False


def test_exploit_gate_uses_fresh_target_and_flag_for_each_attempt(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module = _load_module()
    workspace = tmp_path / "workspace"
    solve_dir = workspace / "solve"
    review_dir = tmp_path / "review"
    solve_dir.mkdir(parents=True)
    review_dir.mkdir()
    (solve_dir / "solve.py").write_text("print('solve')\n", encoding="utf-8")

    flags = ["flag{attempt-one}", "flag{attempt-two}"]
    prepared: list[int] = []
    solver_calls: list[list[str]] = []

    def prepare_attempt(attempt: int):
        prepared.append(attempt)
        index = attempt - 1
        return {
            "ok": True,
            "fresh_target": True,
            "flag": flags[index],
            "network_name": f"target-net-{attempt}",
            "targets": [
                {
                    "service_name": "challenge",
                    "container_id": f"container-{attempt}",
                    "container_addr": f"10.10.{attempt}.2",
                    "internal_port": 1024,
                }
            ],
        }

    def fake_sidecar(cmd, *, container_name, timeout, success_marker):
        del container_name
        assert timeout == 180
        solver_calls.append(list(cmd))
        attempt = len(solver_calls)
        stdout = "no flag" if attempt == 1 else flags[1]
        assert success_marker == flags[attempt - 1].encode()
        return subprocess.CompletedProcess(
            cmd,
            1 if attempt == 1 else 0,
            stdout=stdout,
            stderr="",
        ), False

    monkeypatch.setattr(module, "_run_managed_solver_sidecar", fake_sidecar)
    result = module._BootCheckScorer(
        exploit_gate=True,
        exploit_attempts=3,
    )._run_exploit_validation(
        ws=workspace,
        network_name="discarded-initial-network",
        targets=[],
        solve={"service": "challenge", "entry": "python3 solve.py"},
        flag="flag{discarded-initial-flag}",
        review_dir=review_dir,
        check_label="score",
        prepare_attempt=prepare_attempt,
    )

    assert prepared == [1, 2]
    assert len(solver_calls) == 2
    assert solver_calls[0][solver_calls[0].index("--network") + 1] == "target-net-1"
    assert solver_calls[1][solver_calls[1].index("--network") + 1] == "target-net-2"
    assert "TARGET_HOST=10.10.1.2" in solver_calls[0]
    assert "TARGET_HOST=10.10.2.2" in solver_calls[1]
    assert result["passed"] is True
    assert result["successful_attempt"] == 2
    assert result["outcome_class"] == "retry_rescued_pass"
    assert result["fresh_target_per_attempt"] is True
    assert result["distinct_target_instances"] == 2
    assert result["distinct_flag_fingerprints"] == 2
    assert [
        attempt["target_instance"]["container_ids"]
        for attempt in result["attempts"]
    ] == [["container-1"], ["container-2"]]


def test_exploit_gate_accepts_dirty_exit_after_exact_flag_capture(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module = _load_module()
    workspace = tmp_path / "workspace"
    solve_dir = workspace / "solve"
    review_dir = tmp_path / "review"
    solve_dir.mkdir(parents=True)
    review_dir.mkdir()
    (solve_dir / "solve.py").write_text("print('solve')\n", encoding="utf-8")
    minted = "flag{private}"
    calls = 0

    def fake_sidecar(cmd, *, container_name, timeout, success_marker):
        nonlocal calls
        del container_name
        assert timeout == 180
        assert success_marker == minted.encode()
        calls += 1
        return subprocess.CompletedProcess(cmd, 1, stdout=minted, stderr="dirty exit"), False

    monkeypatch.setattr(module, "_run_managed_solver_sidecar", fake_sidecar)
    result = module._BootCheckScorer(
        exploit_gate=True,
        exploit_attempts=3,
    )._run_exploit_validation(
        ws=workspace,
        network_name="target-net",
        targets=[
            {
                "service_name": "challenge",
                "container_addr": "10.10.0.2",
                "internal_port": 1024,
            }
        ],
        solve={"service": "challenge", "entry": "python3 solve.py"},
        flag=minted,
        review_dir=review_dir,
        check_label="score",
    )

    assert calls == 1
    assert result["passed"] is True
    assert result["captured"] is True
    assert result["successful_attempt"] == 1
    assert result["attempt_count"] == 1
    assert result["outcome_class"] == "first_attempt_pass"
    assert result["solve_exit_clean"] is False
    assert result["solver_outcome_class"] == "dirty_exit"
    assert all(attempt["returncode"] == 1 for attempt in result["attempts"])
    assert "The environment is R5" in result["observation"]


def test_exploit_gate_accepts_flag_seen_before_output_limit(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module = _load_module()
    workspace = tmp_path / "workspace"
    solve_dir = workspace / "solve"
    review_dir = tmp_path / "review"
    solve_dir.mkdir(parents=True)
    review_dir.mkdir()
    (solve_dir / "solve.py").write_text("print('solve')\n", encoding="utf-8")
    minted = "flag{private}"

    def fake_sidecar(cmd, *, container_name, timeout, success_marker):
        del container_name, timeout
        assert success_marker == minted.encode()
        completed = subprocess.CompletedProcess(
            cmd,
            0,
            stdout=minted,
            stderr="continued flooding",
        )
        completed.output_limited = True
        completed.output_bytes = module._SOLVER_OUTPUT_LIMIT_BYTES + 1
        return completed, False

    monkeypatch.setattr(module, "_run_managed_solver_sidecar", fake_sidecar)
    result = module._BootCheckScorer(
        exploit_gate=True,
        exploit_attempts=3,
    )._run_exploit_validation(
        ws=workspace,
        network_name="target-net",
        targets=[
            {
                "service_name": "challenge",
                "container_addr": "10.10.0.2",
                "internal_port": 1024,
            }
        ],
        solve={"service": "challenge", "entry": "python3 solve.py"},
        flag=minted,
        review_dir=review_dir,
        check_label="score",
    )

    assert result["passed"] is True
    assert result["captured"] is True
    assert result["attempt_count"] == 1
    assert all(attempt["error"] == "output_limit" for attempt in result["attempts"])
    assert all(attempt["returncode"] is None for attempt in result["attempts"])
    assert result["solver_outcome_class"] == "output_limited_after_capture"
    assert "The environment is R5" in result["observation"]


def test_solver_sidecar_uses_long_mount_syntax_for_colon_path(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module = _load_module()
    workspace = tmp_path / "agent:model:stateless" / "workspace"
    solve_dir = workspace / "solve"
    review_dir = tmp_path / "review"
    solve_dir.mkdir(parents=True)
    review_dir.mkdir()
    (solve_dir / "solve.py").write_text("print('solve')\n", encoding="utf-8")
    minted = "FAKE{private}"
    calls: list[list[str]] = []
    sidecar_names: list[str] = []

    def fake_sidecar(cmd, *, container_name, timeout, success_marker):
        calls.append(list(cmd))
        sidecar_names.append(container_name)
        assert timeout == 180
        assert success_marker == minted.encode()
        return subprocess.CompletedProcess(cmd, 0, stdout=minted, stderr=""), False

    monkeypatch.setattr(module, "_run_managed_solver_sidecar", fake_sidecar)
    pinned_solver = "sha256:" + "a" * 64
    result = module._BootCheckScorer(
        exploit_gate=True,
        solver_image=pinned_solver,
    )._run_exploit_validation(
        ws=workspace,
        network_name="target-net",
        targets=[
            {
                "service_name": "challenge",
                "container_addr": "10.10.0.2",
                "internal_port": 1024,
            }
        ],
        solve={
            "service": "challenge",
            "entry": "python3 solve.py",
            "image": "buildtarget/solver:latest",
        },
        flag=minted,
        review_dir=review_dir,
        check_label="check-01",
    )

    assert result["passed"] is True
    assert result["captured"] is True
    assert result["attempt_count"] == 1
    assert result["max_attempts"] == 5
    assert result["successful_attempt"] == 1
    assert result["outcome_class"] == "first_attempt_pass"
    assert calls
    assert sidecar_names[0].startswith("cage-build-target-solver-")
    assert calls[0][calls[0].index("--name") + 1] == sidecar_names[0]
    assert pinned_solver in calls[0]
    assert "buildtarget/solver:latest" not in calls[0]
    assert "PYTHONUNBUFFERED=1" in calls[0]
    assert "-v" not in calls[0]
    mount = calls[0][calls[0].index("--mount") + 1]
    assert mount == f"type=bind,src={solve_dir.resolve()},dst=/solve,readonly"
    assert ":" in str(solve_dir.resolve())


def test_default_solver_image_pin_validates_contract_and_dependencies(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module = _load_module()
    image_id = "sha256:" + "b" * 64
    calls: list[list[str]] = []

    def fake_run(cmd: list[str], **_kwargs):
        calls.append(list(cmd))
        if cmd[:3] == ["docker", "image", "inspect"]:
            return _completed(
                cmd,
                stdout=json.dumps(
                    [
                        {
                            "Id": image_id,
                            "Config": {
                                "Labels": {
                                    module.DEFAULT_SOLVER_CONTRACT_LABEL:
                                        module.DEFAULT_SOLVER_CONTRACT_VALUE
                                }
                            },
                        }
                    ]
                ),
            )
        assert cmd[:5] == ["docker", "run", "--rm", "--network", "none"]
        assert image_id in cmd
        return _completed(cmd, stdout="solver-contract-ok 3.23.0 4.15.0 2.34.2\n")

    monkeypatch.setattr(module, "_run", fake_run)

    assert module._pin_default_solver_image(module.DEFAULT_SOLVER_IMAGE) == image_id
    assert len(calls) == 2


def test_default_solver_image_pin_rejects_overwritten_tag_before_smoke(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module = _load_module()
    image_id = "sha256:" + "c" * 64
    calls: list[list[str]] = []

    def fake_run(cmd: list[str], **_kwargs):
        calls.append(list(cmd))
        return _completed(
            cmd,
            stdout=json.dumps(
                [
                    {
                        "Id": image_id,
                        "Config": {
                            "Labels": {
                                "com.docker.compose.project": "challenge-owned"
                            }
                        },
                    }
                ]
            ),
        )

    monkeypatch.setattr(module, "_run", fake_run)

    with pytest.raises(RuntimeError, match="tag may have been overwritten"):
        module._pin_default_solver_image(module.DEFAULT_SOLVER_IMAGE)
    assert len(calls) == 1


def test_build_target_caches_one_solver_content_id_per_run(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module = _load_module()
    image_id = "sha256:" + "d" * 64
    calls: list[str] = []

    def fake_pin(image: str) -> str:
        calls.append(image)
        return image_id

    monkeypatch.setattr(module, "_pin_default_solver_image", fake_pin)
    benchmark = module.BuildTarget(tmp_path, exploit_gate=True)

    assert benchmark.scorer()._solver_image == image_id
    assert benchmark.scorer()._solver_image == image_id
    assert calls == [module.DEFAULT_SOLVER_IMAGE]


def test_compose_cannot_build_over_reserved_solver_alias() -> None:
    module = _load_module()
    scorer = module._BootCheckScorer()

    failure, violations = scorer._validate_compose_runtime_policy(
        {
            "solver": {
                "build": {"context": "."},
                "image": "buildtarget/solver:latest",
            }
        }
    )

    assert failure is not None
    score = failure["build_target"]
    assert score.metadata["failure_class"] == "compose_runtime_unsafe"
    assert violations == [
        {
            "service": "solver",
            "field": "protected_solver_image_build",
            "value": "buildtarget/solver:latest",
        }
    ]
    assert "reserved" in score.metadata["feedback"]


def test_timed_out_solver_sidecar_is_removed_and_preserves_partial_output(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import io

    module = _load_module()
    cleanup_calls: list[list[str]] = []

    class FakeProcess:
        returncode = None
        stdout = io.BytesIO(b"STAGE login_prompt\n")
        stderr = io.BytesIO(b"diagnostic warning\n")

        def __init__(self) -> None:
            self.killed = False

        def poll(self):
            return self.returncode

        def wait(self, timeout=None):
            if self.returncode is None:
                raise subprocess.TimeoutExpired(["docker", "run"], timeout)
            return self.returncode

        def kill(self) -> None:
            self.killed = True
            self.returncode = -9

    fake_process = FakeProcess()
    monkeypatch.setattr(
        module.subprocess,
        "Popen",
        lambda *_args, **_kwargs: fake_process,
    )

    def fake_run(cmd, **_kwargs):
        cleanup_calls.append(list(cmd))
        fake_process.returncode = 137
        return subprocess.CompletedProcess(cmd, 0, stdout="", stderr="")

    monkeypatch.setattr(module, "_run", fake_run)

    result, timed_out = module._run_managed_solver_sidecar(
        ["docker", "run", "--name", "solver-test"],
        container_name="solver-test",
        timeout=0.01,
    )

    assert timed_out is True
    assert result.returncode is None
    assert result.stdout == "STAGE login_prompt\n"
    assert result.stderr == "diagnostic warning\n"
    assert cleanup_calls == [["docker", "rm", "-f", "solver-test"]]


def test_solver_sidecar_stops_after_bounded_combined_output(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import io

    module = _load_module()
    cleanup_calls: list[list[str]] = []

    class FinishedFloodProcess:
        returncode = 0
        stdout = io.BytesIO(b"x" * 2048)
        stderr = io.BytesIO(b"")

        def poll(self):
            return self.returncode

        def wait(self, timeout=None):
            return self.returncode

        def kill(self) -> None:
            raise AssertionError("an exited process must not need a local kill")

    monkeypatch.setattr(module, "_SOLVER_OUTPUT_LIMIT_BYTES", 1024)
    monkeypatch.setattr(
        module.subprocess,
        "Popen",
        lambda *_args, **_kwargs: FinishedFloodProcess(),
    )

    def fake_run(cmd, **_kwargs):
        cleanup_calls.append(list(cmd))
        return subprocess.CompletedProcess(cmd, 0, stdout="", stderr="")

    monkeypatch.setattr(module, "_run", fake_run)
    result, timed_out = module._run_managed_solver_sidecar(
        ["docker", "run", "--name", "solver-flood"],
        container_name="solver-flood",
        timeout=3,
    )

    assert timed_out is False
    assert result.returncode is None
    assert result.output_limited is True
    assert result.output_bytes == 2048
    assert cleanup_calls == [["docker", "rm", "-f", "solver-flood"]]


def test_solver_sidecar_detects_streamed_flag_and_stops_hanging_process(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module = _load_module()
    minted = b"flag{streamed-private-value}"
    real_popen = subprocess.Popen
    process_holder: dict[str, subprocess.Popen] = {}

    def tracked_popen(*args, **kwargs):
        process = real_popen(*args, **kwargs)
        process_holder["process"] = process
        return process

    monkeypatch.setattr(module.subprocess, "Popen", tracked_popen)

    def fake_run(cmd, **_kwargs):
        assert cmd == ["docker", "rm", "-f", "solver-stream-capture"]
        process_holder["process"].kill()
        return subprocess.CompletedProcess(cmd, 0, stdout="", stderr="")

    monkeypatch.setattr(module, "_run", fake_run)
    started = time.monotonic()
    result, timed_out = module._run_managed_solver_sidecar(
        [
            sys.executable,
            "-c",
            (
                "import sys,time; "
                f"sys.stdout.buffer.write({minted!r}); "
                "sys.stdout.flush(); time.sleep(30)"
            ),
        ],
        container_name="solver-stream-capture",
        timeout=10,
        success_marker=minted,
    )

    assert time.monotonic() - started < 3
    assert timed_out is False
    assert result.marker_seen is True
    assert result.terminated_after_capture is True
    assert minted.decode() in result.stdout


def test_subprocess_helpers_replace_non_utf8_output() -> None:
    module = _load_module()
    emit_invalid_bytes = (
        "import os; "
        "os.write(1, b'prefix\\xffsuffix\\n'); "
        "os.write(2, b'warning\\xfddetail\\n')"
    )

    direct = module._run([sys.executable, "-c", emit_invalid_bytes], timeout=5)
    sidecar, timed_out = module._run_managed_solver_sidecar(
        [sys.executable, "-c", emit_invalid_bytes],
        container_name="never-created",
        timeout=5,
    )

    assert direct.returncode == 0
    assert direct.stdout == "prefix\ufffdsuffix\n"
    assert direct.stderr == "warning\ufffddetail\n"
    assert timed_out is False
    assert sidecar.returncode == 0
    assert sidecar.stdout == "prefix\ufffdsuffix\n"
    assert sidecar.stderr == "warning\ufffddetail\n"


def test_scorer_projects_host_command_timeout_as_retryable_failure(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module = _load_module()
    scorer = module._BootCheckScorer()
    command = ["docker", "compose", "ps", "-q", "challenge"]

    def raise_timeout(*_args, **_kwargs):
        raise subprocess.TimeoutExpired(command, 60)

    monkeypatch.setattr(scorer, "_run_validation", raise_timeout)
    live_ctx = module._LiveTrialContext(
        trial_id="host-timeout-live",
        trial_dir=tmp_path,
        workspace=tmp_path / "workspace",
        sample={"name": "demo"},
        agent_container="agent",
        token="token",
    )
    score_ctx = module.ScoringContext(
        trial_id="host-timeout-score",
        trial_index=0,
        sample={"name": "demo"},
        trial_dir=tmp_path,
        run_dir=tmp_path,
    )

    live_payload = scorer.validate_live(live_ctx, check_label="check-01")
    final_score = scorer.score(score_ctx)["build_target"]

    assert live_payload["failure_class"] == "host_runtime_docker_timeout"
    assert live_payload["retryable"] is True
    assert live_payload["evidence"] == {
        "command": command,
        "timeout_seconds": 60,
    }
    assert final_score.value == 0.0
    assert final_score.metadata["failure_class"] == "host_runtime_docker_timeout"
    assert final_score.metadata["retryable"] is True


def test_workspace_signature_survives_unreadable_agent_artifact(
    tmp_path: Path,
) -> None:
    module = _load_module()
    artifact = tmp_path / "private-runtime"
    artifact.write_bytes(b"runtime")
    artifact.chmod(0)
    try:
        signature = module._workspace_runtime_signature(tmp_path)
    finally:
        artifact.chmod(0o600)

    assert len(signature) == 64


def test_live_check_scores_immutable_snapshot_and_rejects_concurrent_edit(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    module = _load_module()
    benchmark = module.BuildTarget(tmp_path, agent_validation=True)
    trial_dir = tmp_path / "trial"
    workspace = trial_dir / "workspace"
    workspace.mkdir(parents=True)
    (workspace / "solve.py").write_text("version-one\n", encoding="utf-8")
    token = "snapshot-token"
    ctx = module._LiveTrialContext(
        trial_id="trial-snapshot",
        trial_dir=trial_dir,
        workspace=workspace,
        sample={"name": "demo"},
        agent_container="agent-container",
        token=token,
    )
    benchmark._live_trials[token] = ctx
    entered = threading.Event()
    release = threading.Event()
    observed: dict[str, object] = {}

    class FakeScorer:
        def __init__(self, **_kwargs) -> None:
            pass

        def validate_live(self, frozen_ctx, *, check_label: str):
            observed["check_label"] = check_label
            observed["workspace"] = frozen_ctx.workspace
            observed["content"] = (frozen_ctx.workspace / "solve.py").read_text(
                encoding="utf-8"
            )
            entered.set()
            assert release.wait(timeout=5)
            return {
                "passed": False,
                "failure_class": "exploit_capture_not_passed",
                "retryable": True,
                "feedback": "frozen result",
            }

    monkeypatch.setattr(module, "_BootCheckScorer", FakeScorer)
    with ThreadPoolExecutor(max_workers=1) as pool:
        future = pool.submit(benchmark._handle_live_check, token)
        assert entered.wait(timeout=5)
        (workspace / "solve.py").write_text("version-two\n", encoding="utf-8")
        release.set()
        payload = future.result(timeout=5)

    frozen_workspace = observed["workspace"]
    assert isinstance(frozen_workspace, Path)
    assert frozen_workspace != workspace
    assert not frozen_workspace.is_symlink()
    assert observed["content"] == "version-one\n"
    assert payload["failure_class"] == "workspace_changed_after_submission"
    assert payload["artifact_dirty"] is True
    assert payload["check_count"] == 0
    assert payload["evidence"]["attempt_consumed"] is False
    assert len(payload["submission_digest"]) == 64
    assert ctx.check_count == 0


@pytest.mark.parametrize("change_runtime", [False, True])
def test_live_r5_stop_seals_only_unchanged_runtime_artifacts(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    change_runtime: bool,
) -> None:
    module = _load_module()
    benchmark = module.BuildTarget(tmp_path, agent_validation=True)
    trial_dir = tmp_path / "trial"
    workspace = trial_dir / "workspace"
    workspace.mkdir(parents=True)
    (workspace / "solve.py").write_text("print('solve')\n", encoding="utf-8")
    (workspace / "solve_report.json").write_text(
        json.dumps({"status": "unresolved"}), encoding="utf-8"
    )
    token = "seal-token"
    ctx = module._LiveTrialContext(
        trial_id="trial-seal",
        trial_dir=trial_dir,
        workspace=workspace,
        sample={"name": "demo"},
        agent_container="agent-container",
        token=token,
    )
    runtime = module._LiveRuntime(
        project="project",
        workspace=workspace,
        compose_path=workspace / "docker-compose.yml",
        agent_container="agent-container",
        network_name="network",
        generation=1,
    )
    ctx.last_runtime = runtime
    ctx.last_runtime_signature = module._workspace_runtime_signature(workspace)
    ctx.last_submission_id = "check-01-deadbeef"
    ctx.last_submission_digest = "a" * 64
    ctx.last_pass_payload = {
        "passed": True,
        "validated_rehost_tier": "R5",
        "exploit_attempt_count": 2,
        "exploit_successful_attempt": 2,
    }
    benchmark._live_trials[token] = ctx

    class FakeScorer:
        def __init__(self, **_kwargs) -> None:
            pass

        def stop_live_runtime(self, stopped_runtime):
            assert stopped_runtime is runtime
            return {"stopped": True, "network_name": stopped_runtime.network_name}

    monkeypatch.setattr(module, "_BootCheckScorer", FakeScorer)
    (workspace / "solve_report.json").write_text(
        json.dumps({"status": "solved"}), encoding="utf-8"
    )
    if change_runtime:
        (workspace / "solve.py").write_text("print('changed')\n", encoding="utf-8")

    payload = benchmark._handle_live_stop(token)
    verdict_path = trial_dir / "runtime" / "live_success.json"
    assert payload["runtime_artifacts_unchanged"] is (not change_runtime)
    assert payload["live_success_recorded"] is (not change_runtime)
    assert verdict_path.is_file() is (not change_runtime)
    if change_runtime:
        assert payload["requires_revalidation"] is True
    else:
        verdict = json.loads(verdict_path.read_text(encoding="utf-8"))
        assert verdict["evidence"]["submission_id"] == "check-01-deadbeef"
        assert verdict["evidence"]["successful_attempt"] == 2


def test_live_status_returns_only_the_current_runtime_lease(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module = _load_module()
    benchmark = module.BuildTarget(tmp_path, agent_validation=True)
    trial_dir = tmp_path / "trial"
    workspace = trial_dir / "workspace"
    workspace.mkdir(parents=True)
    ctx = module._LiveTrialContext(
        trial_id="trial-status",
        trial_dir=trial_dir,
        workspace=workspace,
        sample={"name": "demo"},
        agent_container="agent-container",
        token="status-token",
    )
    runtime = module._LiveRuntime(
        project="project",
        workspace=workspace,
        compose_path=workspace / "docker-compose.yml",
        agent_container="agent-container",
        network_name="project_default",
        service_targets=[
            {
                "service_name": "challenge",
                "container_addr": "10.240.0.2",
                "internal_port": 31337,
                "protocol": "tcp",
            }
        ],
        runtime_id="runtime-one",
        generation=3,
    )
    ctx.last_runtime = runtime
    ctx.last_submission_id = "check-01-deadbeef"
    benchmark._live_trials[ctx.token] = ctx

    monkeypatch.setattr(
        module,
        "_run",
        lambda cmd, **_kwargs: _completed(
            cmd,
            stdout=json.dumps({"project_default": {"IPAddress": "10.240.0.3"}}),
        ),
    )

    present = benchmark._handle_live_status(ctx.token)
    assert present == {
        "runtime_present": True,
        "runtime_id": "runtime-one",
        "runtime_generation": 3,
        "network_name": "project_default",
        "targets": runtime.service_targets,
        "agent_attached": True,
        "inspect_error": None,
        "check_count": 0,
        "submission_id": "check-01-deadbeef",
    }

    ctx.last_invalidated_runtime_id = runtime.runtime_id
    ctx.last_runtime = None
    absent = benchmark._handle_live_status(ctx.token)
    assert absent["runtime_present"] is False
    assert absent["last_invalidated_runtime_id"] == "runtime-one"


def test_live_check_reuses_passing_runtime_until_build_inputs_change(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    module = _load_module()
    benchmark = module.BuildTarget(tmp_path, agent_validation=True)
    trial_dir = tmp_path / "trial"
    workspace = trial_dir / "workspace"
    workspace.mkdir(parents=True)
    token = "live-token"
    ctx = module._LiveTrialContext(
        trial_id="trial-live",
        trial_dir=trial_dir,
        workspace=workspace,
        sample={"name": "demo"},
        agent_container="agent-container",
        token=token,
    )
    benchmark._live_trials[token] = ctx

    validate_calls: list[str] = []
    stopped_networks: list[str | None] = []

    class FakeScorer:
        def __init__(self, **_kwargs) -> None:
            pass

        def validate_live(self, _ctx, *, check_label: str):
            validate_calls.append(check_label)
            call_index = len(validate_calls)
            addr = f"10.240.{call_index}.2"
            runtime = module._LiveRuntime(
                project=f"project-{call_index}",
                workspace=workspace,
                compose_path=workspace / "docker-compose.yml",
                compose_files=[workspace / "docker-compose.yml"],
                agent_container="agent-container",
                network_name=f"network-{call_index}",
                service_targets=[
                    {
                        "service_name": "app",
                        "container_addr": addr,
                        "internal_port": 8080,
                        "protocol": "http",
                    }
                ],
                image_manifest=f"manifest-{call_index}",
            )
            return {
                "passed": True,
                "value": 1.0,
                "failure_class": None,
                "feedback": "initial pass",
                "container_addr": addr,
                "network_name": runtime.network_name,
                "targets": copy.deepcopy(runtime.service_targets),
                "agent_self_check_present": False,
                "agent_service_output": "",
                "validated_rehost_tier": "R4",
                "runtime_probe_results": {
                    "passed": True,
                    "probe_count": 1,
                    "probes": [
                        {
                            "id": "home",
                            "service": "app",
                            "passed": True,
                            "attempts": [
                                {
                                    "passed": True,
                                    "response": {
                                        "status": 200,
                                        "body_excerpt": "Demo application",
                                    },
                                }
                            ],
                        }
                    ],
                },
                "runtime_probe_evidence": "validator/runtime-probe.json",
                "review_files": {},
                "_runtime": runtime,
            }

        def stop_live_runtime(self, runtime):
            stopped_networks.append(runtime.network_name)
            return {"stopped": True, "network_name": runtime.network_name}

    monkeypatch.setattr(module, "_BootCheckScorer", FakeScorer)

    first = benchmark._handle_live_check(token)

    assert validate_calls == ["check-01"]
    assert stopped_networks == []
    assert first["container_addr"] == "10.240.1.2"
    assert ctx.last_runtime is not None

    second = benchmark._handle_live_check(token)

    assert validate_calls == ["check-01"]
    assert stopped_networks == []
    assert second["runtime_reused"] is True
    assert second["probe_evidence_present"] is True
    assert "PASS through R4" in second["feedback"]
    assert "Demo application" in second["feedback"]
    assert "run `cage-check stop`, and finish" in second["feedback"]

    (workspace / "service_output.txt").write_text(
        "curl -i http://10.240.1.2:8080/\nHTTP/1.1 200 OK\n",
        encoding="utf-8",
    )

    third = benchmark._handle_live_check(token)

    assert validate_calls == ["check-01"]
    assert stopped_networks == []
    assert third["runtime_reused"] is True
    assert third["probe_evidence_present"] is True
    assert "CAGE independently executed" in third["feedback"]
    assert "HTTP/1.1 200 OK" in third["agent_service_output"]

    (workspace / "Dockerfile").write_text("FROM scratch\n", encoding="utf-8")

    fourth = benchmark._handle_live_check(token)

    assert validate_calls == ["check-01", "check-02"]
    assert stopped_networks == ["network-1"]
    assert fourth["container_addr"] == "10.240.2.2"
    assert ctx.last_runtime is not None
    assert ctx.last_runtime.network_name == "network-2"

    audit = [
        json.loads(line)
        for line in (trial_dir / "build_checks.jsonl").read_text(encoding="utf-8").splitlines()
    ]
    assert [entry["action"] for entry in audit] == [
        "check",
        "check_reused",
        "check_reused",
        "stop",
        "check",
    ]


def test_live_check_stops_rebuilding_after_attempt_budget(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    module = _load_module()
    benchmark = module.BuildTarget(
        tmp_path,
        agent_validation=True,
        validation_max_checks=2,
    )
    trial_dir = tmp_path / "trial"
    workspace = trial_dir / "workspace"
    workspace.mkdir(parents=True)
    token = "budget-token"
    benchmark._live_trials[token] = module._LiveTrialContext(
        trial_id="trial-budget",
        trial_dir=trial_dir,
        workspace=workspace,
        sample={"name": "demo"},
        agent_container="agent-container",
        token=token,
    )
    validate_calls: list[str] = []

    class FakeScorer:
        def __init__(self, **_kwargs) -> None:
            pass

        def validate_live(self, _ctx, *, check_label: str):
            validate_calls.append(check_label)
            return {
                "passed": False,
                "failure_class": "build_or_boot_failed",
                "retryable": True,
                "feedback": "upstream image tag not found",
            }

    monkeypatch.setattr(module, "_BootCheckScorer", FakeScorer)

    first = benchmark._handle_live_check(token)
    second = benchmark._handle_live_check(token)
    third = benchmark._handle_live_check(token)

    assert first["failure_class"] == "build_or_boot_failed"
    assert first["check_count"] == 1
    assert first["checks_remaining"] == 1
    assert second["failure_class"] == "validation_attempt_budget_exhausted"
    assert second["retryable"] is False
    assert second["check_count"] == 2
    assert second["checks_remaining"] == 0
    assert second["last_failure_class"] == "build_or_boot_failed"
    assert second["last_feedback"] == "upstream image tag not found"
    assert "upstream image tag not found" in second["feedback"]
    assert third == second
    assert validate_calls == ["check-01", "check-02"]
    audit = [
        json.loads(line)
        for line in (trial_dir / "build_checks.jsonl").read_text(encoding="utf-8").splitlines()
    ]
    assert [entry["action"] for entry in audit] == [
        "check",
        "check",
        "check_terminal_reused",
    ]


def test_live_blocked_report_does_not_permanently_seal_trial(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    module = _load_module()
    benchmark = module.BuildTarget(
        tmp_path,
        agent_validation=True,
        validation_max_checks=3,
    )
    trial_dir = tmp_path / "trial"
    workspace = trial_dir / "workspace"
    workspace.mkdir(parents=True)
    token = "working-blocker-token"
    ctx = module._LiveTrialContext(
        trial_id="trial-working-blocker",
        trial_dir=trial_dir,
        workspace=workspace,
        sample={"name": "demo"},
        agent_container="agent-container",
        token=token,
    )
    benchmark._live_trials[token] = ctx
    validate_calls: list[str] = []

    class FakeScorer:
        def __init__(self, **_kwargs) -> None:
            pass

        def validate_live(self, _ctx, *, check_label: str):
            validate_calls.append(check_label)
            if len(validate_calls) == 1:
                return {
                    "passed": False,
                    "failure_class": "agent_reported_blocker",
                    "retryable": False,
                    "feedback": "builder reported blocked",
                }
            return {
                "passed": False,
                "failure_class": "build_or_boot_failed",
                "retryable": True,
                "feedback": "candidate reached real validation",
            }

    monkeypatch.setattr(module, "_BootCheckScorer", FakeScorer)

    first = benchmark._handle_live_check(token)
    second = benchmark._handle_live_check(token)

    assert first["failure_class"] == "agent_reported_blocker"
    assert first["retryable"] is True
    assert "did not permanently seal the trial" in first["feedback"]
    assert second["failure_class"] == "build_or_boot_failed"
    assert validate_calls == ["check-01", "check-02"]
    assert ctx.terminal_payload is None


@pytest.mark.parametrize("busy_scope", ["same_trial", "global_docker_gate"])
def test_live_check_waits_for_existing_work_without_polling_or_resubmitting(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    busy_scope: str,
) -> None:
    module = _load_module()
    benchmark = module.BuildTarget(
        tmp_path,
        agent_validation=True,
        validation_max_checks=3,
    )
    trial_dir = tmp_path / "trial"
    workspace = trial_dir / "workspace"
    workspace.mkdir(parents=True)
    token = "busy-token"
    ctx = module._LiveTrialContext(
        trial_id="trial-busy",
        trial_dir=trial_dir,
        workspace=workspace,
        sample={"name": "demo"},
        agent_container="agent-container",
        token=token,
    )
    benchmark._live_trials[token] = ctx

    validate_calls: list[str] = []

    class FakeScorer:
        def __init__(self, **_kwargs) -> None:
            pass

        def validate_live(self, _ctx, *, check_label: str):
            validate_calls.append(check_label)
            return {
                "passed": False,
                "failure_class": "build_or_boot_failed",
                "retryable": True,
                "feedback": "candidate failure",
            }

    monkeypatch.setattr(module, "_BootCheckScorer", FakeScorer)

    held_lock = ctx.lock if busy_scope == "same_trial" else benchmark._docker_gate
    assert held_lock.acquire(blocking=False)
    with ThreadPoolExecutor(max_workers=1) as pool:
        future = pool.submit(benchmark._handle_live_check, token)
        try:
            with pytest.raises(TimeoutError):
                future.result(timeout=0.05)
        finally:
            held_lock.release()
        payload = future.result(timeout=5)

    assert payload["failure_class"] == "build_or_boot_failed"
    assert payload["retryable"] is True
    assert payload["check_count"] == 1
    assert payload["checks_remaining"] == 2
    assert ctx.check_count == 1
    assert validate_calls == ["check-01"]
    audit = [
        json.loads(line)
        for line in (trial_dir / "build_checks.jsonl").read_text(encoding="utf-8").splitlines()
    ]
    assert [entry["action"] for entry in audit] == ["check"]


def test_host_network_contention_does_not_consume_live_validation_attempt(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    module = _load_module()
    benchmark = module.BuildTarget(
        tmp_path,
        agent_validation=True,
        validation_max_checks=3,
    )
    trial_dir = tmp_path / "trial"
    workspace = trial_dir / "workspace"
    workspace.mkdir(parents=True)
    token = "network-contention-token"
    ctx = module._LiveTrialContext(
        trial_id="trial-network-contention",
        trial_dir=trial_dir,
        workspace=workspace,
        sample={"name": "demo"},
        agent_container="agent-container",
        token=token,
    )
    benchmark._live_trials[token] = ctx
    validate_calls: list[str] = []

    class FakeScorer:
        def __init__(self, **_kwargs) -> None:
            pass

        def validate_live(self, _ctx, *, check_label: str):
            validate_calls.append(check_label)
            return {
                "passed": False,
                "failure_class": "host_runtime_network_exhausted",
                "retryable": True,
                "feedback": "retry unchanged",
                "evidence": {"managed_network_retries": 3},
            }

    monkeypatch.setattr(module, "_BootCheckScorer", FakeScorer)

    first = benchmark._handle_live_check(token)
    second = benchmark._handle_live_check(token)

    assert validate_calls == ["check-01", "check-01"]
    assert first["check_count"] == 0
    assert first["checks_remaining"] == 3
    assert first["evidence"]["attempt_consumed"] is False
    assert second["check_count"] == 0
    assert ctx.check_count == 0
    assert ctx.terminal_payload is None


@pytest.mark.parametrize(
    "failure_class",
    ["host_runtime_docker_timeout", "validator_internal_error"],
)
def test_host_validator_failure_does_not_consume_live_validation_attempt(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    failure_class: str,
) -> None:
    module = _load_module()
    benchmark = module.BuildTarget(
        tmp_path,
        agent_validation=True,
        validation_max_checks=3,
    )
    trial_dir = tmp_path / "trial"
    workspace = trial_dir / "workspace"
    workspace.mkdir(parents=True)
    token = "host-transient-token"
    ctx = module._LiveTrialContext(
        trial_id="trial-host-transient",
        trial_dir=trial_dir,
        workspace=workspace,
        sample={"name": "demo"},
        agent_container="agent-container",
        token=token,
    )
    benchmark._live_trials[token] = ctx

    class FakeScorer:
        def __init__(self, **_kwargs) -> None:
            pass

        def validate_live(self, _ctx, *, check_label: str):
            return {
                "passed": False,
                "failure_class": failure_class,
                "retryable": True,
                "feedback": "retry unchanged",
            }

    monkeypatch.setattr(module, "_BootCheckScorer", FakeScorer)

    payload = benchmark._handle_live_check(token)

    assert payload["failure_class"] == failure_class
    assert payload["check_count"] == 0
    assert payload["checks_remaining"] == 3
    assert payload["evidence"]["attempt_consumed"] is False
    assert ctx.check_count == 0
    assert ctx.terminal_payload is None


def test_unhandled_live_validator_error_is_structured_and_does_not_consume_attempt(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module = _load_module()
    benchmark = module.BuildTarget(
        tmp_path,
        agent_validation=True,
        validation_max_checks=3,
    )
    trial_dir = tmp_path / "trial"
    workspace = trial_dir / "workspace"
    workspace.mkdir(parents=True)
    token = "internal-error-token"
    ctx = module._LiveTrialContext(
        trial_id="trial-internal-error",
        trial_dir=trial_dir,
        workspace=workspace,
        sample={"name": "demo"},
        agent_container="agent-container",
        token=token,
    )
    benchmark._live_trials[token] = ctx

    class ExplodingScorer:
        def __init__(self, **_kwargs) -> None:
            pass

        def validate_live(self, _ctx, *, check_label: str):
            raise RuntimeError("synthetic validator failure")

    monkeypatch.setattr(module, "_BootCheckScorer", ExplodingScorer)

    payload = benchmark._handle_live_check(token)

    assert payload["failure_class"] == "validator_internal_error"
    assert payload["retryable"] is True
    assert payload["check_count"] == 0
    assert payload["checks_remaining"] == 3
    assert payload["evidence"] == {
        "attempt_consumed": False,
        "exception_type": "RuntimeError",
    }
    assert ctx.check_count == 0
    assert ctx.terminal_payload is None


def test_cage_check_timeout_is_configurable_and_longer_than_build_timeout() -> None:
    client = (
        REPO_ROOT / "examples" / "build_target" / "serve" / "cage-check"
    ).read_text(encoding="utf-8")

    assert 'REQUEST_TIMEOUT="${CAGE_CHECK_TIMEOUT_SECONDS:-2580}"' in client
    assert '--max-time "$REQUEST_TIMEOUT"' in client
    assert 'BUSY_RETRY_SECONDS="${CAGE_CHECK_BUSY_RETRY_SECONDS:-30}"' in client
    assert 'BUSY_MAX_RETRIES="${CAGE_CHECK_BUSY_MAX_RETRIES:-70}"' in client
    for failure_class in (
        "validator_busy",
        "host_runtime_network_exhausted",
        "host_runtime_docker_timeout",
        "validator_internal_error",
    ):
        assert f'"{failure_class}"' in client


def _r4_probe_contract_ctx(
    module,
    tmp_path: Path,
    *,
    writeup_text: str,
    runtime_probes: list,
    target_protocols: dict,
    image_name: str = "ctfenv/pwn-anchor-wave4:d4-r4-x0",
):
    """Build a scoring context that reaches _validate_runtime_probe_evidence."""
    material_root = tmp_path / "materials"
    material_root.mkdir()
    (material_root / "solve.md").write_text(writeup_text, encoding="utf-8")

    trial_dir = tmp_path / "trial"
    workspace = trial_dir / "workspace"
    workspace.mkdir(parents=True)
    (workspace / "docker-compose.yml").write_text("services: {}\n", encoding="utf-8")
    (workspace / "build_report.json").write_text(
        json.dumps({"status": "ready"}), encoding="utf-8"
    )
    (workspace / "challenge.json").write_text(
        json.dumps(
            {
                "compose_files": ["docker-compose.yml"],
                "compose_target_services": ["challenge"],
                "compose_dependency_services": [],
                "target_ports": {"challenge": 31337},
                "target_port_protocols": target_protocols,
                "runtime_probes": runtime_probes,
            }
        ),
        encoding="utf-8",
    )
    ctx = module.ScoringContext(
        trial_id="anchor-contract",
        trial_index=0,
        sample={
            "image_name": image_name,
            "image_names": [image_name],
            "target_maturity": {"rehost": "R4"},
            "challenge_path": str(material_root),
            "materials": {"writeups": ["solve.md"]},
        },
        trial_dir=trial_dir,
        run_dir=trial_dir,
    )
    return ctx, image_name


def _fake_config_run(image_name: str):
    def fake_run(cmd: list[str], **_kwargs):
        if "config" in cmd:
            return _completed(
                cmd,
                stdout=json.dumps(
                    {
                        "services": {
                            "challenge": {
                                "build": {"context": "."},
                                "image": image_name,
                            }
                        }
                    }
                ),
            )
        return _completed(cmd)

    return fake_run


def test_r4_probe_marker_must_be_anchored_in_cited_material(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    module = _load_module()
    ctx, image_name = _r4_probe_contract_ctx(
        module,
        tmp_path,
        writeup_text="This hint mentions nothing the probe will assert.\n",
        target_protocols={"challenge": "tcp"},
        runtime_probes=[
            {
                "id": "menu",
                "type": "tcp",
                "service": "challenge",
                "steps": [{"expect_contains": "SuperSecretBanner"}],
                "evidence": [
                    {"path": "solve.md", "basis": "cites the writeup but invents the marker"}
                ],
            }
        ],
    )
    monkeypatch.setattr(module, "_run", _fake_config_run(image_name))

    _, failure = module._BootCheckScorer()._load_workspace_contract(ctx)

    assert failure is not None
    score = failure["build_target"]
    assert score.metadata["failure_class"] == "runtime_probe_marker_unanchored"
    assert score.metadata["evidence"]["expected_markers"] == ["SuperSecretBanner"]
    assert "lifted from real challenge material" in score.metadata["feedback"]


def test_r4_probe_records_content_anchor_for_http_marker(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    module = _load_module()
    ctx, image_name = _r4_probe_contract_ctx(
        module,
        tmp_path,
        writeup_text="Landing page renders the <title>Json Analyser</title> banner.\n",
        target_protocols={"challenge": "http"},
        runtime_probes=[
            {
                "id": "home",
                "type": "http",
                "service": "challenge",
                "path": "/",
                "expect_status": 200,
                "expect_body_contains": "Json Analyser",
                "evidence": [
                    {"path": "solve.md", "basis": "writeup names the page title"}
                ],
            }
        ],
    )
    monkeypatch.setattr(module, "_run", _fake_config_run(image_name))

    contract, failure = module._BootCheckScorer()._load_workspace_contract(ctx)

    assert failure is None
    assert contract is not None
    anchor = contract["runtime_probes"][0]["content_anchor"]
    assert anchor["marker"] == "Json Analyser"
    assert anchor["cited_paths"] == ["solve.md"]


def test_scorer_rejects_escape_grade_capabilities(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    module = _load_module()
    trial_dir = tmp_path / "trial"
    workspace = trial_dir / "workspace"
    workspace.mkdir(parents=True)
    (workspace / "docker-compose.yml").write_text("services: {}\n", encoding="utf-8")
    (workspace / "build_report.json").write_text(json.dumps({"status": "ready"}), encoding="utf-8")
    (workspace / "challenge.json").write_text(
        json.dumps(
            {
                "compose_files": ["docker-compose.yml"],
                "compose_target_services": ["app"],
                "compose_dependency_services": [],
                "target_ports": {"app": 1024},
                "target_port_protocols": {"app": "tcp"},
            }
        ),
        encoding="utf-8",
    )
    image_name = "ctfenv/pwn-escape-wave1:d4-r3-x0"
    calls: list[list[str]] = []

    def fake_run(cmd: list[str], **_kwargs):
        calls.append(cmd)
        if "config" in cmd:
            return _completed(
                cmd,
                stdout=json.dumps(
                    {
                        "services": {
                            "app": {
                                "build": {"context": "."},
                                "image": image_name,
                                "cap_add": ["SYS_MODULE"],
                            }
                        }
                    }
                ),
            )
        return _completed(cmd)

    monkeypatch.setattr(module, "_run", fake_run)
    ctx = module.ScoringContext(
        trial_id="escape-caps",
        trial_index=0,
        sample={"image_name": image_name, "image_names": [image_name]},
        trial_dir=trial_dir,
        run_dir=trial_dir,
    )

    score = module._BootCheckScorer().score(ctx)["build_target"]

    assert score.value == 0.0
    assert score.metadata["failure_class"] == "compose_runtime_unsafe"
    assert {"service": "app", "field": "cap_add", "value": ["SYS_MODULE"]} in score.metadata[
        "evidence"
    ]["violations"]
    assert not any("up" in cmd for cmd in calls)


def test_scorer_rejects_userns_host_and_namespace_sharing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    module = _load_module()
    trial_dir = tmp_path / "trial"
    workspace = trial_dir / "workspace"
    workspace.mkdir(parents=True)
    (workspace / "docker-compose.yml").write_text("services: {}\n", encoding="utf-8")
    (workspace / "build_report.json").write_text(json.dumps({"status": "ready"}), encoding="utf-8")
    (workspace / "challenge.json").write_text(
        json.dumps(
            {
                "compose_files": ["docker-compose.yml"],
                "compose_target_services": ["app"],
                "compose_dependency_services": [],
                "target_ports": {"app": 1024},
                "target_port_protocols": {"app": "tcp"},
            }
        ),
        encoding="utf-8",
    )
    image_name = "ctfenv/pwn-userns-wave1:d4-r3-x0"

    def fake_run(cmd: list[str], **_kwargs):
        if "config" in cmd:
            return _completed(
                cmd,
                stdout=json.dumps(
                    {
                        "services": {
                            "app": {
                                "build": {"context": "."},
                                "image": image_name,
                                "userns_mode": "host",
                                "pid": "container:sidecar",
                            }
                        }
                    }
                ),
            )
        return _completed(cmd)

    monkeypatch.setattr(module, "_run", fake_run)
    ctx = module.ScoringContext(
        trial_id="userns-host",
        trial_index=0,
        sample={"image_name": image_name, "image_names": [image_name]},
        trial_dir=trial_dir,
        run_dir=trial_dir,
    )

    score = module._BootCheckScorer().score(ctx)["build_target"]

    assert score.metadata["failure_class"] == "compose_runtime_unsafe"
    violations = score.metadata["evidence"]["violations"]
    assert {"service": "app", "field": "userns_mode", "value": "host"} in violations
    assert {"service": "app", "field": "pid", "value": "container:sidecar"} in violations


def test_scorer_rejects_label_disable_and_systempaths_unconfined(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    module = _load_module()
    trial_dir = tmp_path / "trial"
    workspace = trial_dir / "workspace"
    workspace.mkdir(parents=True)
    (workspace / "docker-compose.yml").write_text("services: {}\n", encoding="utf-8")
    (workspace / "build_report.json").write_text(json.dumps({"status": "ready"}), encoding="utf-8")
    (workspace / "challenge.json").write_text(
        json.dumps(
            {
                "compose_files": ["docker-compose.yml"],
                "compose_target_services": ["app"],
                "compose_dependency_services": [],
                "target_ports": {"app": 1024},
                "target_port_protocols": {"app": "tcp"},
            }
        ),
        encoding="utf-8",
    )
    image_name = "ctfenv/pwn-selinux-wave1:d4-r3-x0"

    def fake_run(cmd: list[str], **_kwargs):
        if "config" in cmd:
            return _completed(
                cmd,
                stdout=json.dumps(
                    {
                        "services": {
                            "app": {
                                "build": {"context": "."},
                                "image": image_name,
                                # `systempaths=unconfined` uses the key=value form to
                                # exercise separator normalization.
                                "security_opt": ["label:disable", "systempaths=unconfined"],
                            }
                        }
                    }
                ),
            )
        return _completed(cmd)

    monkeypatch.setattr(module, "_run", fake_run)
    ctx = module.ScoringContext(
        trial_id="selinux-off",
        trial_index=0,
        sample={"image_name": image_name, "image_names": [image_name]},
        trial_dir=trial_dir,
        run_dir=trial_dir,
    )

    score = module._BootCheckScorer().score(ctx)["build_target"]

    assert score.metadata["failure_class"] == "compose_runtime_unsafe"
    assert {
        "service": "app",
        "field": "security_opt",
        "value": ["label:disable", "systempaths:unconfined"],
    } in score.metadata["evidence"]["violations"]


def test_scorer_rejects_host_bind_named_volume(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    module = _load_module()
    trial_dir = tmp_path / "trial"
    workspace = trial_dir / "workspace"
    workspace.mkdir(parents=True)
    (workspace / "docker-compose.yml").write_text("services: {}\n", encoding="utf-8")
    (workspace / "build_report.json").write_text(json.dumps({"status": "ready"}), encoding="utf-8")
    (workspace / "challenge.json").write_text(
        json.dumps(
            {
                "compose_files": ["docker-compose.yml"],
                "compose_target_services": ["app"],
                "compose_dependency_services": [],
                "target_ports": {"app": 1024},
                "target_port_protocols": {"app": "tcp"},
            }
        ),
        encoding="utf-8",
    )
    image_name = "ctfenv/pwn-volbind-wave1:d4-r3-x0"
    calls: list[list[str]] = []

    def fake_run(cmd: list[str], **_kwargs):
        calls.append(cmd)
        if "config" in cmd:
            return _completed(
                cmd,
                stdout=json.dumps(
                    {
                        "services": {
                            "app": {"build": {"context": "."}, "image": image_name}
                        },
                        "volumes": {
                            "hostroot": {
                                "driver": "local",
                                "driver_opts": {"type": "none", "o": "bind", "device": "/etc"},
                            }
                        },
                    }
                ),
            )
        return _completed(cmd)

    monkeypatch.setattr(module, "_run", fake_run)
    ctx = module.ScoringContext(
        trial_id="volbind",
        trial_index=0,
        sample={"image_name": image_name, "image_names": [image_name]},
        trial_dir=trial_dir,
        run_dir=trial_dir,
    )

    score = module._BootCheckScorer().score(ctx)["build_target"]

    assert score.metadata["failure_class"] == "compose_runtime_unsafe"
    assert {
        "volume": "hostroot",
        "field": "host_bind_volume",
        "value": {"device": "/etc", "o": "bind"},
    } in score.metadata["evidence"]["violations"]
    assert not any("up" in cmd for cmd in calls)


def test_await_target_readiness_detects_listening_and_closed_ports() -> None:
    import socket as _socket

    module = _load_module()

    # A listening port becomes ready immediately.
    listener = _socket.socket(_socket.AF_INET, _socket.SOCK_STREAM)
    listener.bind(("127.0.0.1", 0))
    listener.listen(1)
    ready_port = listener.getsockname()[1]
    try:
        res = module._await_target_readiness(
            [
                {
                    "service_name": "app",
                    "container_addr": "127.0.0.1",
                    "internal_port": ready_port,
                }
            ]
        )
    finally:
        listener.close()
    assert res["targets"][0]["ready"] is True

    # A closed port stays not-ready and the wait is bounded (never hangs).
    probe = _socket.socket(_socket.AF_INET, _socket.SOCK_STREAM)
    probe.bind(("127.0.0.1", 0))
    closed_port = probe.getsockname()[1]
    probe.close()
    res2 = module._await_target_readiness(
        [
            {
                "service_name": "app",
                "container_addr": "127.0.0.1",
                "internal_port": closed_port,
            }
        ],
        deadline_seconds=1,
    )
    assert res2["targets"][0]["ready"] is False
    assert res2["targets"][0]["attempts"] >= 1


@pytest.mark.parametrize("protocol", ["tcp", "http", "https"])
def test_running_container_without_listening_port_never_receives_r3(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    protocol: str,
) -> None:
    module = _load_module()
    trial_dir = tmp_path / "trial"
    workspace = trial_dir / "workspace"
    workspace.mkdir(parents=True)
    compose_path = workspace / "docker-compose.yml"
    compose_path.write_text("services: {}\n", encoding="utf-8")
    scorer = module._BootCheckScorer()
    contract = {
        "workspace": workspace,
        "compose_path": compose_path,
        "build_report": {"status": "ready"},
        "expected_images": ["ctf-env:pwn-not-listening"],
        "build_services_by_image": {
            "ctf-env:pwn-not-listening": ["challenge"]
        },
        "target_services": ["challenge"],
        "target_ports": {"challenge": 31337},
        "target_port_protocols": {"challenge": protocol},
        "config_data": {"services": {"challenge": {}}},
        "solve": {},
        "exploit_required": False,
        "runtime_probes": [],
        "runtime_probes_required": False,
        "agent_network_hint": None,
    }
    ctx = module.ScoringContext(
        trial_id=f"not-listening-{protocol}",
        trial_index=0,
        sample={},
        trial_dir=trial_dir,
        run_dir=trial_dir,
    )
    monkeypatch.setattr(scorer, "_load_workspace_contract", lambda _ctx: (contract, None))
    monkeypatch.setattr(
        scorer,
        "_write_managed_runtime_compose",
        lambda **_kwargs: (compose_path, []),
    )
    monkeypatch.setattr(
        scorer,
        "_collect_image_evidence",
        lambda **_kwargs: ([], None),
    )
    monkeypatch.setattr(module.time, "sleep", lambda _seconds: None)
    monkeypatch.setattr(
        module,
        "_await_target_readiness",
        lambda _targets: {
            "deadline_seconds": 30,
            "targets": [
                {
                    "service": "challenge",
                    "container_addr": "10.240.0.2",
                    "internal_port": 31337,
                    "ready": False,
                    "attempts": 30,
                }
            ],
        },
    )

    def fake_run(cmd: list[str], **_kwargs):
        if "ps" in cmd:
            return _completed(cmd, stdout="container-id\n")
        if cmd[:2] == ["docker", "inspect"]:
            return _completed(
                cmd,
                stdout=json.dumps(
                    {
                        "State": {"Status": "running"},
                        "NetworkSettings": {
                            "Networks": {
                                "buildcheck_default": {"IPAddress": "10.240.0.2"}
                            }
                        },
                    }
                ),
            )
        return _completed(cmd)

    monkeypatch.setattr(module, "_run", fake_run)
    scores, runtime = scorer._run_validation(ctx, keep_runtime=False)

    assert runtime is None
    metadata = scores["build_target"].metadata
    assert metadata.get("validated_rehost_tier") is None
    assert metadata["failure_class"] == "target_port_not_ready"
    assert metadata["evidence"]["not_ready"][0]["ready"] is False


def test_r3_task_drops_malformed_optional_probe_instead_of_failing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    module = _load_module()
    material_root = tmp_path / "materials"
    material_root.mkdir()
    (material_root / "solve.md").write_text("challenge hint text", encoding="utf-8")
    trial_dir = tmp_path / "trial"
    workspace = trial_dir / "workspace"
    workspace.mkdir(parents=True)
    image_name = "ctfenv/pwn-r3-optprobe:d4-r3-x0"
    (workspace / "docker-compose.yml").write_text("services: {}\n", encoding="utf-8")
    (workspace / "build_report.json").write_text(
        json.dumps({"status": "ready"}), encoding="utf-8"
    )
    (workspace / "challenge.json").write_text(
        json.dumps(
            {
                "compose_files": ["docker-compose.yml"],
                "compose_target_services": ["challenge"],
                "target_ports": {"challenge": 31337},
                "target_port_protocols": {"challenge": "tcp"},
                # malformed optional probe: a step with neither send nor expect
                "runtime_probes": [
                    {
                        "id": "bad",
                        "type": "tcp",
                        "service": "challenge",
                        "steps": [{"note": "no send or expect"}],
                        "evidence": [{"path": "solve.md", "basis": "x"}],
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    def fake_run(cmd: list[str], **_kwargs):
        if "config" in cmd:
            return _completed(
                cmd,
                stdout=json.dumps(
                    {"services": {"challenge": {"build": {"context": "."}, "image": image_name}}}
                ),
            )
        return _completed(cmd)

    monkeypatch.setattr(module, "_run", fake_run)
    ctx = module.ScoringContext(
        trial_id="r3-optprobe",
        trial_index=0,
        sample={
            "image_name": image_name,
            "image_names": [image_name],
            "target_maturity": {"rehost": "R3"},
            "challenge_path": str(material_root),
            "materials": {"writeups": ["solve.md"]},
        },
        trial_dir=trial_dir,
        run_dir=trial_dir,
    )

    contract, failure = module._BootCheckScorer()._load_workspace_contract(ctx)

    assert failure is None
    assert contract is not None
    assert contract["runtime_probes_required"] is False
    # The malformed optional probe is dropped, not turned into a hard failure.
    assert contract["runtime_probes"] == []


def test_network_pool_contention_variants_are_detected() -> None:
    module = _load_module()
    scorer = module._BootCheckScorer()
    positives = [
        "all predefined address pools have been fully subnetted",
        "Error response from daemon: could not find an available, non-overlapping "
        "IPv4 address pool among the defaults to assign to the network",
        "failed to create network buildcheck_x_default: Error response from daemon: "
        "invalid pool request: Pool overlaps with other one on this address space",
    ]
    for msg in positives:
        assert scorer._is_address_pool_exhaustion(msg) is True, msg
    assert scorer._is_address_pool_exhaustion(
        "failed to solve: gcc: command not found"
    ) is False
    assert scorer._is_address_pool_exhaustion("") is False


def test_build_failure_feedback_keeps_repair_on_authoritative_cage_path() -> None:
    module = _load_module()
    feedback = module._BootCheckScorer()._build_failure_feedback(
        "failed to solve: COPY missing-runtime.so /opt/challenge/: not found"
    )

    assert "authoritative host-side `docker compose up --build` attempt" in feedback
    assert "Do not reproduce or replace the target in the agent container" in feedback
    assert "first fatal command or missing path" in feedback
    assert "change one causal build-closure dimension" in feedback
    assert "let the next `cage-check` rebuild it" in feedback
    assert "COPY missing-runtime.so" in feedback


def test_service_failure_feedback_keeps_lifecycle_repair_on_cage_target() -> None:
    module = _load_module()
    feedback = module._BootCheckScorer()._service_failure_feedback(
        service_name="challenge",
        status="exited",
        service_logs="exec ./chall: Permission denied",
    )

    assert "image built" in feedback
    assert "host-side container and its logs are authoritative" in feedback
    assert "do not replace them with a locally launched target" in feedback
    assert "executable mode" in feedback
    assert "first broken lifecycle link" in feedback
    assert "let the next `cage-check` rebuild it" in feedback
    assert "Permission denied" in feedback
