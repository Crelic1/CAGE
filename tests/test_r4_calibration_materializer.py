from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest


def _load_module():
    path = (
        Path(__file__).resolve().parents[1]
        / "examples"
        / "build_target"
        / "scripts"
        / "materialize_r4_calibration.py"
    )
    spec = importlib.util.spec_from_file_location("r4_calibration", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _record() -> dict:
    return {
        "env_id": "saj-2024-pwn-demo",
        "priority": {"id": "dockerfile_writeup_attachments"},
        "task": {
            "category": "pwn",
            "data_tier": "D4",
            "material_states": {
                "deploy": {"state": "confirmed"},
                "writeup": {"state": "confirmed"},
            },
            "docker_closure": {"missing_ref_count": 0},
            "static_evidence": {"prior_runtime_failures": []},
            "image_name": "ctfenv/pwn-demo-wave4:d4-r3-x0",
        },
    }


def test_promotes_only_the_rehost_maturity_component() -> None:
    module = _load_module()

    assert (
        module.promote_image_tag("ctfenv/pwn-demo-wave4:d4-r3-x0")
        == "ctfenv/pwn-demo-wave4:d4-r4-x0"
    )
    module.validate_record(_record(), manifested=set())


def test_rejects_previously_manifested_or_lower_confidence_candidate() -> None:
    module = _load_module()
    record = _record()

    with pytest.raises(ValueError, match="already has an image_manifest"):
        module.validate_record(record, manifested={record["env_id"]})

    record["priority"]["id"] = "dockerfile_attachments"
    with pytest.raises(ValueError, match="strongest Pwn material class"):
        module.validate_record(record, manifested=set())
