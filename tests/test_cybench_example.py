from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest
import yaml

EXAMPLE_DIR = Path(__file__).resolve().parents[1] / "examples" / "cybench"
DATASET_DIR = EXAMPLE_DIR / "datasets"

pytestmark = pytest.mark.skipif(
    not (DATASET_DIR / "cybench.json").is_file(),
    reason="cybench dataset submodule is not initialized",
)


def _load_cybench_module():
    module_path = EXAMPLE_DIR / "benchmark.py"
    spec = importlib.util.spec_from_file_location("cybench_benchmark", module_path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class _RecordingContainer:
    def __init__(self) -> None:
        self.exec_commands: list[str] = []
        self.copies: list[tuple[str, str]] = []

    def exec(self, command: str):
        self.exec_commands.append(command)
        return {"exit_code": 0, "stdout": "", "stderr": ""}

    def copy_to(self, source: str, dest: str) -> None:
        self.copies.append((source, dest))


def _sample(benchmark, sample_id: str) -> dict:
    return next(s for s in benchmark.iter_samples() if s["id"] == sample_id)


def test_loads_every_upstream_task_with_a_flag():
    benchmark = _load_cybench_module().CyBench()
    benchmark.setup()
    samples = list(benchmark.iter_samples())

    assert len(samples) == 40, "Cybench is a 40-task benchmark"
    assert all(sample["flag"] for sample in samples), "every task must carry its flag"
    assert {sample["metadata"]["event"] for sample in samples} == {
        "HTB",
        "S22",
        "S23",
        "HKC",
        "GLA",
    }


def test_sample_carries_upstream_metadata():
    benchmark = _load_cybench_module().CyBench()
    benchmark.setup()
    sample = _sample(benchmark, "cb-s22-crypto-diffecient")

    assert sample["benchmark"] == "cybench"
    assert sample["category"] == "crypto"
    assert sample["name"] == "diffecient"
    assert sample["flag"].startswith("SEKAI{")
    assert sample["files"] == ["diffecient.py"]
    assert sample["answer_format"].endswith("}")
    assert sample["metadata"]["competition"] == "project-sekai-ctf/sekaictf-2022"
    assert sample["metadata"]["difficulty_name"] == "advanced"
    assert sample["metadata"]["subtask_count"] == 5


def test_prompt_tier_selects_the_upstream_tier_and_resolves_tmp_dir():
    module = _load_cybench_module()

    hard = _sample_after_setup(module.CyBench(prompt_tier="hard"), "cb-s22-crypto-diffecient")
    easy = _sample_after_setup(module.CyBench(prompt_tier="easy"), "cb-s22-crypto-diffecient")

    assert hard["description"] != easy["description"]
    assert "the system will reveal a flag" in easy["description"]
    # Upstream leaves its own shell variable in the prompt text; the agent must
    # not be handed an unbound "$TMP_DIR".
    assert "TMP_DIR" not in hard["description"]
    assert "/home/agent/workspace" in hard["description"]


def _sample_after_setup(benchmark, sample_id: str) -> dict:
    benchmark.setup()
    return _sample(benchmark, sample_id)


def test_prompt_never_contains_the_flag():
    benchmark = _load_cybench_module().CyBench()
    benchmark.setup()
    for sample in benchmark.iter_samples():
        prompt = benchmark.build_prompt(sample)
        assert sample["flag"] not in prompt, sample["id"]


def test_prepare_trial_stages_the_handout_at_upstream_paths():
    benchmark = _load_cybench_module().CyBench()
    benchmark.setup()
    sample = _sample(benchmark, "cb-s23-pwn-network_tools")
    container = _RecordingContainer()

    benchmark.prepare_trial(container, sample, "/home/agent/workspace")

    destinations = [dest for _, dest in container.copies]
    assert "/home/agent/workspace/main.rs" in destinations
    assert "/home/agent/workspace/nettools" in destinations
    # Sources come from the challenge's public/ subtree, never the task root:
    # the flag and the upstream solution live outside it.
    assert all("/public/" in source for source, _ in container.copies)


def test_generated_compose_is_launchable_concurrently():
    """No fixed container names, no external networks, explicit image tags."""
    composes = sorted(DATASET_DIR.glob("*/*/*/**/docker-compose.cage.yml"))
    assert composes, "networked tasks must ship a generated compose file"

    for compose_path in composes:
        config = yaml.safe_load(compose_path.read_text(encoding="utf-8")) or {}
        for service_name, service in (config.get("services") or {}).items():
            assert "container_name" not in service, f"{compose_path}: {service_name}"
            if "build" in service:
                assert service.get("image"), f"{compose_path}: {service_name} build without image"
        for network_name, network in (config.get("networks") or {}).items():
            assert not (network or {}).get("external"), f"{compose_path}: {network_name}"


def test_every_networked_task_has_a_compose_file():
    index = json.loads((DATASET_DIR / "cybench.json").read_text(encoding="utf-8"))
    for challenge_id, entry in index.items():
        if not entry.get("has_target"):
            continue
        challenge = json.loads(
            (DATASET_DIR / entry["path"] / "challenge.json").read_text(encoding="utf-8")
        )
        assert challenge.get("compose_files"), challenge_id
        for relative in challenge["compose_files"]:
            assert (DATASET_DIR / entry["path"] / relative).is_file(), challenge_id


def test_default_project_registers_the_benchmark():
    config = yaml.safe_load((EXAMPLE_DIR / "default_cybench.yml").read_text(encoding="utf-8"))
    assert config["registration"]["id"] == "cybench"
    assert config["eval"]["benchmark"]["class"] == "CyBench"
    assert config["eval"]["benchmark"]["prompt_tier"] in {"hard", "easy"}
