"""XBOW Validation Benchmarks adapter for CAGE."""

from __future__ import annotations

import hashlib
import json
import os
import re
import sys
from pathlib import Path
from typing import Any

import yaml

if __package__ in {None, ""}:
    repo_root = Path(__file__).resolve().parents[2]
    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))

from examples.base.ctf import CtfBenchmark


def _description(metadata: dict[str, Any]) -> str:
    parts = []
    for item in metadata.get("content", []) or []:
        if not isinstance(item, dict):
            continue
        text = str(item.get("content") or "").strip()
        if text:
            parts.append(text)
    return "\n\n".join(parts)


def _flag(challenge_id: str) -> str:
    digest = hashlib.sha256(challenge_id.upper().encode()).hexdigest()
    return f"FLAG{{{digest}}}"


def _image_tag(challenge_id: str, service: str) -> str:
    suffix = re.sub(r"[^a-z0-9_.-]+", "-", service.lower()).strip("-.")
    return f"cage/xbow:{challenge_id.lower()}-{suffix}"


def _write_if_changed(path: Path, content: str) -> None:
    if path.is_file() and path.read_text(encoding="utf-8") == content:
        return
    path.write_text(content, encoding="utf-8")


def materialize_cage_metadata(root: Path) -> None:
    index: dict[str, dict[str, Any]] = {}
    for challenge_dir in sorted(root.glob("XBEN-*-*")):
        metadata_path = challenge_dir / "benchmark.yaml"
        compose_path = challenge_dir / "docker-compose.yml"
        if not metadata_path.is_file() or not compose_path.is_file():
            continue

        challenge_id = challenge_dir.name
        metadata = yaml.safe_load(metadata_path.read_text(encoding="utf-8")) or {}
        compose = yaml.safe_load(compose_path.read_text(encoding="utf-8")) or {}
        services = compose.get("services") or {}
        target_services = [
            name
            for name, config in services.items()
            if isinstance(config, dict) and config.get("ports")
        ]
        override_services = {
            name: {"image": _image_tag(challenge_id, name)}
            for name, config in services.items()
            if isinstance(config, dict) and "build" in config
        }
        override = {"services": override_services}
        override_text = yaml.safe_dump(override, sort_keys=False)
        _write_if_changed(challenge_dir / "docker-compose.cage.yml", override_text)

        level = metadata.get("level")
        challenge = {
            "id": challenge_id,
            "benchmark": "xbow",
            "benchmark_family": "xbow",
            "benchmark_id": "xbow",
            "name": str(metadata.get("name") or challenge_id),
            "category": "web",
            "description": _description(metadata),
            "flag": _flag(challenge_id),
            "task_profile": "single_target",
            "compose_files": ["docker-compose.yml", "docker-compose.cage.yml"],
            "compose_env": {"FLAG": _flag(challenge_id)},
            "compose_target_services": target_services,
            "application_service_keys": target_services,
            "exposure_mode": "internal",
            "level": level,
            "tags": list(metadata.get("tags") or []),
            "files": [],
        }
        challenge_text = json.dumps(challenge, indent=2, sort_keys=True) + "\n"
        _write_if_changed(challenge_dir / "challenge.json", challenge_text)
        index[challenge_id] = {
            "path": challenge_id,
            "challenge": challenge_id,
            "category": "web",
            "level": level,
        }

    index_text = json.dumps(index, indent=2, sort_keys=True) + "\n"
    _write_if_changed(root / "xbow.json", index_text)


class XBOW(CtfBenchmark):
    name = "xbow"
    package_dir = Path(__file__).resolve().parent
    index_filename = "xbow.json"
    env_root_var = "XBOW_BENCHMARK_ROOT"
    default_category = "web"
    default_flag_format = "FLAG{...}"

    needs_check_service: bool = True
    needs_submit_service: bool = True

    @property
    def prompts_dir(self) -> Path:
        return self.package_dir.parent / "nyuctfbench" / "prompts"

    def _default_root(self) -> Path:
        return self.package_dir / "datasets" / "benchmarks"

    def _materialization_root(self) -> Path:
        if self.benchmark_root is not None:
            root = Path(self.benchmark_root).expanduser()
            if not root.is_absolute():
                root = self.package_dir / root
        elif self.env_root_var and os.getenv(self.env_root_var):
            root = Path(os.environ[self.env_root_var]).expanduser()
        else:
            root = self._default_root()
        return root.resolve()

    def setup(self) -> None:
        root = self._materialization_root()
        materialize_cage_metadata(root)
        self.benchmark_root = root
        super().setup()

    def build_metadata(self, challenge, source_fields, challenge_dir):
        return {
            "level": source_fields.get("level"),
            "tags": list(source_fields.get("tags") or []),
            "benchmark_family": "xbow",
        }

    def extra_sample_fields(self, challenge, source_fields, challenge_dir):
        return {
            "level": source_fields.get("level"),
            "tags": list(source_fields.get("tags") or []),
        }


if __name__ == "__main__":
    bench = XBOW()
    bench.setup()
    assert bench.challenge_client is not None
    print(json.dumps({"count": len(bench.challenge_client.challenges)}))
