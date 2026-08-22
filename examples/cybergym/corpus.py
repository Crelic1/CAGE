"""Which CyberGym trials are unfit to train on.

These are contamination gates, not preferences. Each one names a way the
trajectory misrepresents the task the model is supposed to learn — the agent
already held the answer, the task belongs to the held-out evaluation set, the
"evidence" it reasoned from was synthetic. A consumer assembling a training mix
cannot be expected to know any of that, which is why the exporter refuses these
by default and only releases them under an explicit ``--allow <code>``.

Selection preferences deliberately live elsewhere: whether a failed attempt is
useful, how much reasoning is enough, how many trajectories per task to keep are
all decisions for whoever builds the mix, and reach them as exporter filters.

Gate codes are stable identifiers. The framework matches them and prints them
but never interprets one, so adding a gate here needs no framework change.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import TYPE_CHECKING, Any

from cage.corpus import TrainingAdmission

if TYPE_CHECKING:
    from cage.corpus import TrialCorpusView

# The gendesc variant inverts the task: the agent is handed the known-good PoC
# and asked to *write the description*. Its trials pass by construction, and a
# model trained on them learns that the answer will be sitting in the workspace.
GATE_GENDESC = "gendesc"
# Tasks in the official catalog make up the held-out evaluation set. Training on
# them does not make the model better, it makes the number meaningless.
GATE_CATALOG_LEAK = "catalog_leak"
# Synthesised stand-ins for evidence the payload lacked. The benchmark itself
# treats a file carrying these markers as absent; a corpus must agree, or it
# teaches the model to reason from a reconstructed header as if it were a real
# sanitizer trace.
GATE_PLACEHOLDER = "placeholder_materials"
# Workspace gone and no materials overlay configured, so the above cannot be
# checked. Trials whose payload supplies its own description are exactly the
# ones that carried synthesised placeholders, so "cannot verify" has to mean
# "refuse" rather than "assume clean".
GATE_UNVERIFIABLE = "materials_unverifiable"
# A pass whose vulnerable-side exit code is SIGTERM: the target was killed by
# the timeout, which is not the crash the task asks for.
GATE_TIMEOUT_PASS = "timeout_pass"
# The agent fetched the upstream bug tracker or fix commit instead of deriving
# the crash. Every observed attempt came back empty — the modern trackers need
# JS and a login — so the pass rate is not polluted, but the *action sequence*
# is: learning it wastes turns in a firewalled evaluation.
GATE_ANSWER_LOOKUP = "answer_lookup"

# A network fetch AND an answer-source URL must both appear. Matching the
# project names alone floods with false positives: a task's own source tree
# contains project.yaml, clusterfuzz-* corpus files and commit messages that
# mention oss-fuzz, and listing or reading those is ordinary analysis.
_ANSWER_SOURCE = re.compile(
    r"""(?:curl|wget|git\s+clone|fetch)\b[^|;&]{0,200}?
        https?://[^\s"']*(?:ARVO-Meta|n132/ARVO|oss-?fuzz|
        bugs\.chromium\.org|clusterfuzz|testcase-?detail|
        api\.github\.com/search)""",
    re.I | re.X,
)

_SUBMIT_RECORD = "runtime/cybergym_submit.json"
_SIGTERM_EXIT = 143


def _run_description_tier(trial: "TrialCorpusView") -> str | None:
    """The materials tier this run configured, if any.

    Not recorded per trial, so it comes from the run config. Its presence is
    also what tells a cleaned workspace apart from an unverifiable one: a run
    with a materials overlay staged real evidence, a run without it used
    whatever the payload carried.
    """

    config = trial.run_config
    node: Any = config
    for key in ("eval", "benchmark", "description_tier"):
        if not isinstance(node, dict):
            return None
        node = node.get(key)
    return node or None if isinstance(node, str) else None


def _placeholder_hits(workspace: Path, markers: dict[str, tuple[str, ...]]) -> list[str]:
    hits: list[str] = []
    for name, needles in markers.items():
        path = workspace / name
        if not path.is_file():
            continue
        try:
            text = path.read_text(errors="replace")
        except OSError:
            continue
        if any(needle in text for needle in needles):
            hits.append(name)
    return hits


# The held-out set is the OFFICIAL catalog, whatever index a given run happened
# to draw from. An external-ARVO run indexes ``arvo.json`` and can still land on
# a task that is also in ``cybergym.json`` — checking the run's own index would
# wave exactly those through.
EVALUATION_CATALOG = "cybergym.json"


def evaluation_task_ids(benchmark_root: Path | None) -> set[str]:
    """Task ids that make up the held-out evaluation set."""

    return _catalog_task_ids(benchmark_root, EVALUATION_CATALOG)


def _catalog_task_ids(benchmark_root: Path | None, index_file: str) -> set[str]:
    if benchmark_root is None:
        return set()
    path = benchmark_root / index_file
    if not path.is_file():
        return set()
    try:
        data = json.loads(path.read_text(errors="replace"))
    except Exception:
        return set()
    if isinstance(data, dict):
        return set(data)
    if isinstance(data, list):
        return {
            (item.get("id") if isinstance(item, dict) else str(item))
            for item in data
            if item
        }
    return set()


def admit(
    trial: "TrialCorpusView",
    *,
    catalog_task_ids: set[str],
    placeholder_markers: dict[str, tuple[str, ...]],
    passed: bool | None,
) -> TrainingAdmission:
    """Run every gate, collecting all reasons rather than stopping at the first.

    Keeping every reason is what makes a rejection distribution readable — "500
    collected, 80 admitted" is only actionable when the other 420 say why.
    """

    task_id = trial.trial_id.replace("_", ":", 1)
    submit = trial.read_json(_SUBMIT_RECORD)
    difficulty = submit.get("difficulty")
    tier = _run_description_tier(trial)

    verdict = TrainingAdmission.ok(
        passed=passed,
        difficulty=difficulty,
        description_tier=tier,
        task=task_id,
    )

    # The recorded field beats the naming convention: a run name is a habit, the
    # field is what the trial actually ran.
    if difficulty == "gendesc" or "gendesc" in trial.run_id.lower():
        verdict = verdict.rejected(
            GATE_GENDESC,
            "gendesc variant: the agent holds the known-good PoC and is asked to "
            "write the description, so the task is not the one being trained for",
        )

    if task_id in catalog_task_ids:
        verdict = verdict.rejected(
            GATE_CATALOG_LEAK,
            "task is in the official CyberGym catalog, which is the evaluation set",
        )

    workspace = trial.workspace
    hits = _placeholder_hits(workspace, placeholder_markers)
    if hits:
        verdict = verdict.rejected(
            GATE_PLACEHOLDER,
            f"materials are synthesised stand-ins the benchmark treats as absent: {hits}",
        )
    elif not (workspace / "description.txt").is_file() and not tier:
        verdict = verdict.rejected(
            GATE_UNVERIFIABLE,
            "workspace was cleaned and the run configured no materials overlay, so "
            "a synthesised description cannot be ruled out",
        )

    vul_exit = None
    cybergym_score = trial.scores.get("cybergym")
    if isinstance(cybergym_score, dict):
        metadata = cybergym_score.get("metadata")
        if isinstance(metadata, dict):
            vul_exit = metadata.get("vul_exit_code")
    if passed and vul_exit == _SIGTERM_EXIT:
        verdict = verdict.rejected(
            GATE_TIMEOUT_PASS,
            f"scored pass but the vulnerable run exited {_SIGTERM_EXIT} (SIGTERM): "
            "a timeout is not a crash",
        )
    verdict = verdict.with_provenance(vul_exit_code=vul_exit)

    # Last, and only when nothing cheaper already refused: this is the one gate
    # that has to read the whole trajectory, and trajectories routinely pass
    # 100 MB. Every gate above answers from small files, so short-circuiting
    # here is what keeps a scan of a 2,500-trial run from taking an hour —
    # and the reasons already collected are the ones worth reporting anyway.
    if verdict.admitted:
        lookups = trial.scan_tool_commands(_ANSWER_SOURCE, limit=8)
        verdict = verdict.with_provenance(n_answer_lookup=len(lookups))
        if lookups:
            verdict = verdict.rejected(
                GATE_ANSWER_LOOKUP,
                f"fetched an upstream answer source {len(lookups)}+ time(s)",
            )

    return verdict
