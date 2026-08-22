"""Cybench benchmark adapter for CAGE.

A member of the CTF benchmark family (see ``examples/base/ctf.py``): the shared
:class:`CtfBenchmark` provides discovery, the prompt, flag scoring and the
in-container ``submit``/``check`` services. Cybench's own bits are three:

* **Two prompt tiers.** Upstream ships every task with a ``hard_prompt`` and an
  ``easy_prompt`` (its ``--easy_prompt`` flag). Both are carried on the
  challenge; ``--prompt-tier`` picks one per run, and the choice shows up as a
  variant axis on the run summary.
* **A handout staged by upstream's own script.** ``generate_dataset.py`` runs
  each task's ``init_script.sh`` and keeps the result under ``public/``, so
  ``prepare_trial`` reproduces upstream's working directory exactly rather than
  copying a file list someone transcribed by hand.
* **An answer format.** Upstream tells the agent the shape of the flag
  (``HTB{********}``); the prompt template renders it.

Only the unguided mode is implemented — one prompt, the flag is the win
condition. Upstream's guided mode (answer N subtasks in sequence, each revealed
after the previous one) is a different interaction protocol; the subtask data is
carried through on ``challenge.json`` so it can be added without regenerating
the dataset.
"""

from __future__ import annotations

import json
import re
import shlex
import sys
from pathlib import Path
from typing import TYPE_CHECKING, Any

if __package__ in {None, ""}:
    repo_root = Path(__file__).resolve().parents[2]
    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))

from cage.benchmarks import BenchmarkOption
from examples.base.ctf import CtfBenchmark

if TYPE_CHECKING:
    from cage.sandbox.containers import Container

# The four competitions Cybench draws from use four flag wrappers; ``flag{...}``
# is kept as a catch-all for a candidate an agent reports in the generic form.
CYBENCH_FLAG_RE = re.compile(
    r"(?:SEKAI|HTB|gctf|hkcert22|flag)\{[^}\r\n]{1,256}\}", re.IGNORECASE
)

PROMPT_TIERS = ("hard", "easy")

# Upstream's difficulty field is 0-5; these are its own names for the levels.
DIFFICULTY_NAMES = {
    "0": "easy",
    "1": "beginner",
    "2": "intermediate",
    "3": "advanced",
    "4": "expert",
    "5": "master",
}

# Where ``generate_dataset.py`` puts the agent-visible handout inside a
# challenge directory. Everything else there (Dockerfiles, compose, upstream
# metadata) stays on the host.
HANDOUT_DIR = "public"

# The workspace the CTF family renders prompts against (``CtfBenchmark.build_prompt``).
WORKSPACE_DIR = "/home/agent/workspace"


def _normalize_prompt_tier(value: Any) -> str:
    tier = str(value or "").strip().lower()
    return tier if tier in PROMPT_TIERS else PROMPT_TIERS[0]


class CyBench(CtfBenchmark):
    """Cybench benchmark adapter (CTF family), unguided mode."""

    name = "cybench"
    package_dir = Path(__file__).resolve().parent
    index_filename = "cybench.json"
    env_root_var = "CYBENCH_BENCHMARK_ROOT"
    default_category = "misc"
    default_flag_format = "flag{...}"
    flag_pattern = CYBENCH_FLAG_RE

    needs_check_service: bool = True
    needs_submit_service: bool = True

    def __init__(
        self,
        benchmark_root: str | None = None,
        *,
        server_url: str | None = None,
        prompt_tier: str = "hard",
    ) -> None:
        super().__init__(benchmark_root, server_url=server_url)
        self._prompt_tier = _normalize_prompt_tier(prompt_tier)

    # -- Layer-3 knobs --------------------------------------------------------

    def cli_options(self) -> list[BenchmarkOption]:
        return [
            BenchmarkOption(
                flag="--prompt-tier",
                config_path="eval.benchmark.prompt_tier",
                choices=PROMPT_TIERS,
                help=(
                    "Which upstream prompt tier to use — 'hard' (default, "
                    "upstream's hard_prompt) states the task only; 'easy' "
                    "(upstream's --easy_prompt) adds a hint about the approach."
                ),
            )
        ]

    def variant_display_axes(self) -> dict[str, tuple[str, ...]]:
        return {"prompt": (self._prompt_tier,)}

    # -- samples --------------------------------------------------------------

    def transform_description(self, description: str, source_fields: dict[str, Any]) -> str:
        """Pick the requested prompt tier and resolve upstream's ``$TMP_DIR``.

        Twelve of the metadata prompts were lifted out of ``init_script.sh`` with
        their shell variable intact ("provided with chall.py in the $TMP_DIR"),
        and upstream never expands it either. ``$TMP_DIR`` *is* the agent's
        working directory, so it is spelled out here rather than handed to the
        model as an unbound variable.
        """
        if self._prompt_tier == "easy":
            easy = str(source_fields.get("description_easy", "") or "").strip()
            if easy:
                description = easy
        return (
            str(description)
            .replace("${TMP_DIR}", WORKSPACE_DIR)
            .replace("$TMP_DIR", WORKSPACE_DIR)
        )

    def build_metadata(self, challenge, source_fields, challenge_dir):
        difficulty = str(source_fields.get("difficulty", "") or "")
        return {
            "event": source_fields.get("event"),
            "competition": source_fields.get("competition"),
            "upstream_path": source_fields.get("upstream_path"),
            "categories": list(source_fields.get("categories", []) or []),
            "difficulty": difficulty,
            "difficulty_name": DIFFICULTY_NAMES.get(difficulty, ""),
            "target_host": source_fields.get("target_host", ""),
            "prompt_tier": self._prompt_tier,
            # Upstream's own subtask ladder is carried on the challenge but not
            # scored here (unguided mode); the count is what a run summary can
            # honestly say about it.
            "subtask_count": len(source_fields.get("subtasks", []) or []),
            "stateful_shell": bool(source_fields.get("stateful_shell", False)),
            # The handout contains the flag by upstream's design (a rev task
            # that hides it among decoys). Flagged so an easy solve on those is
            # not read as the same signal as one on a task that hides it.
            "flag_in_handout": bool(source_fields.get("flag_in_handout", False)),
            "source_benchmark": "cybench",
        }

    def extra_sample_fields(self, challenge, source_fields, challenge_dir):
        return {
            # Upstream tells the agent the shape of the answer; the prompt
            # template renders it, and it must never carry the flag itself.
            "answer_format": str(source_fields.get("answer_format", "") or ""),
            "difficulty": str(source_fields.get("difficulty", "") or ""),
            "event": source_fields.get("event", ""),
        }

    # -- trial lifecycle ------------------------------------------------------

    def prepare_trial(
        self,
        container: "Container",
        sample: dict[str, Any],
        workspace_dir: str,
    ) -> None:
        """Stage the handout at the paths upstream's ``init_script.sh`` used.

        The family default copies ``<challenge_dir>/<rel>``; Cybench keeps the
        handout in its own ``public/`` subtree so that the rest of the task
        directory — Dockerfiles, upstream metadata, the flag — has no path into
        the workspace even if a ``files`` entry were wrong.
        """
        container.exec(f"mkdir -p {shlex.quote(workspace_dir)}")
        handout_root = Path(sample["challenge_dir"]) / HANDOUT_DIR
        for filename in sample.get("files") or []:
            rel = Path(filename)
            if rel.is_absolute() or ".." in rel.parts:
                continue
            source = handout_root / rel
            if not source.exists():
                continue
            dest_parent = f"{workspace_dir}/{rel.parent.as_posix()}"
            container.exec(f"mkdir -p {shlex.quote(dest_parent)}")
            container.copy_to(str(source), f"{workspace_dir}/{rel.as_posix()}")


if __name__ == "__main__":
    bench = CyBench()
    bench.setup()
    assert bench.challenge_client is not None
    first = next(bench.iter_samples(), None)
    print(
        json.dumps(
            {
                "count": len(bench.challenge_client.challenges),
                "first": first["id"] if first else None,
            }
        )
    )
