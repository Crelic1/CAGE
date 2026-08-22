"""NYU CTF benchmark adapter for CAGE.

A member of the CTF benchmark family (see ``examples/base/ctf.py``): the shared
:class:`CtfBenchmark` provides discovery, the prompt, flag scoring and the
in-container ``submit``/``check`` services. NYU CTF's own bits are its per-sample
metadata mapping and the ``{box}``/``{port}`` placeholder substitution in the
challenge description.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

if __package__ in {None, ""}:
    repo_root = Path(__file__).resolve().parents[2]
    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))

from examples.base.ctf import CtfBenchmark


def _as_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "y", "on"}
    return bool(value)


class NYUCTF(CtfBenchmark):
    """NYU CTF benchmark adapter (CTF family)."""

    name = "nyu_ctf"
    package_dir = Path(__file__).resolve().parent
    index_filename = "nyu_ctf.json"
    env_root_var = "EVOLVE_CTF_BENCHMARK_ROOT"
    default_flag_format = "flag{...}"

    needs_check_service: bool = True
    needs_submit_service: bool = True

    def transform_description(self, description: str, source_fields: dict[str, Any]) -> str:
        internal_port = source_fields.get("internal_port")
        description = str(description).replace("{box}", "<service-host>")
        if internal_port is not None:
            description = description.replace("{port}", str(internal_port))
        return description

    def build_metadata(self, challenge, source_fields, challenge_dir):
        return {
            "year": source_fields.get("year"),
            "event": source_fields.get("event"),
            "challenge": source_fields.get("challenge"),
            "compose": _as_bool(source_fields.get("compose")),
            "box": source_fields.get("box"),
            "internal_port": source_fields.get("internal_port"),
            "reference": source_fields.get("reference"),
            "raw_index": {
                key: source_fields.get(key)
                for key in ("year", "event", "challenge", "category", "path")
                if key in source_fields
            },
        }


if __name__ == "__main__":
    bench = NYUCTF()
    bench.setup()
    assert bench.challenge_client is not None
    print(json.dumps({"count": len(bench.challenge_client.challenges)}))
