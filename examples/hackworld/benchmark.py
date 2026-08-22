"""HackWorld benchmark adapter for CAGE.

A member of the CTF benchmark family (see ``examples/base/ctf.py``): the shared
:class:`CtfBenchmark` provides discovery, the prompt and flag scoring. HackWorld
keeps its own broader flag-candidate regex (its challenges use several flag
wrappers — ``flag{...}``, ``key{...}``, ``*CTF{...}``, …), its per-sample
metadata mapping, and a ``task``-first ``content`` field.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any

if __package__ in {None, ""}:
    repo_root = Path(__file__).resolve().parents[2]
    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))

from examples.base.ctf import CtfBenchmark, first_text

# HackWorld challenges use several flag wrappers; match them all when scavenging
# candidate flags from the agent output for reporting.
HACKWORLD_FLAG_RE = re.compile(
    r"[A-Za-z0-9_]*CTF\{[^}\s]{1,256}\}|[a-z0-9_]+\{[^}\s]{1,256}\}", re.IGNORECASE
)


def _int_or_none(value: Any) -> int | None:
    try:
        return int(value) if value is not None else None
    except (TypeError, ValueError):
        return None


class HackWorld(CtfBenchmark):
    """HackWorld web CTF benchmark adapter (CTF family)."""

    name = "hackworld"
    package_dir = Path(__file__).resolve().parent
    index_filename = "hackworld.json"
    env_root_var = "HACKWORLD_BENCHMARK_ROOT"
    required_subdirs = ("web",)
    default_category = "web"
    default_flag_format = "{...}"
    flag_pattern = HACKWORLD_FLAG_RE

    def build_metadata(self, challenge, source_fields, challenge_dir):
        return {
            "event": source_fields.get("event"),
            "year": source_fields.get("year"),
            "source_benchmark": source_fields.get("source_benchmark")
            or source_fields.get("benchmark"),
            "benchmark_family": challenge.get("benchmark_family"),
            "task_profile": challenge.get("task_profile"),
            "target_scope": source_fields.get("target_scope"),
            "network_mode": source_fields.get("network_mode"),
            "box": source_fields.get("box") or source_fields.get("target_host"),
            "internal_port": _int_or_none(
                source_fields.get("internal_port") or source_fields.get("port")
            ),
            "raw_index": {
                key: source_fields.get(key)
                for key in (
                    "event", "year", "challenge", "category",
                    "path", "benchmark", "source_benchmark",
                )
                if key in source_fields
            },
        }

    def extra_sample_fields(self, challenge, source_fields, challenge_dir):
        return {
            # HackWorld's content is the task text (task-first), matching upstream.
            "content": first_text(challenge, "task", "description"),
            "task": first_text(challenge, "task", "description"),
            "source_benchmark": source_fields.get("source_benchmark")
            or source_fields.get("benchmark", ""),
        }


if __name__ == "__main__":
    bench = HackWorld()
    bench.setup()
    assert bench.challenge_client is not None
    first = next(bench.iter_samples(), None)
    if first is not None:
        print(json.dumps({"count": len(bench.challenge_client.challenges), "first": first["id"]}))
