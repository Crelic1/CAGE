"""Trial phase vocabulary — "where inside its lifecycle is this trial right now?"

``contracts.trial_status`` answers *how a trial ended* (the coarse terminal
bucket: completed / failed / interrupted / running). It deliberately has no
opinion about what is happening *during* the run: every in-flight trial is just
``running``, from the moment its container is created to the moment its score is
written.

That single ``running`` value is not enough for two questions the framework has
to answer constantly:

1. **"Is this run alive?"** — with no phase, the only remaining signal is
   "did some file change recently?", which is a one-way approximation
   (a fresh file proves life; a stale file proves nothing).
2. **"Why did this trial fail?"** — an exception carries a message but not the
   *stage* it escaped from. A ``docker`` error raised while launching the target
   and one raised while snapshotting post-state read identically once flattened
   to ``str(exc)``, even though they mean completely different things.

``TrialPhase`` fixes one vocabulary for both. It is a **separate axis** from
``TrialRecord.status`` — status stays the coarse lifecycle bucket that resume,
trial counts, and the scoring pipeline key off, while phase is the fine-grained
position within it. Overloading ``status`` with phase values would silently
change what "terminal" means for every one of those consumers.

Lives in ``contracts`` (Layer 0) because it is universal vocabulary: every
benchmark's trial passes through these stages, and the runtime, the artifact
writer, the liveness probe, and the web inspector all need to name them the
same way. It imports nothing from the rest of ``cage``.
"""

from __future__ import annotations

from enum import Enum


class TrialPhase(str, Enum):
    """Stage of the trial lifecycle a trial currently occupies.

    Ordered as the runtime traverses them. ``PLANNED`` and ``FINISHED`` are the
    two non-active bookends; everything between them means work is in flight.
    """

    # Bookend — the record exists but the runtime has not picked it up. Also
    # covers a trial waiting on the admission gate or the concurrency
    # semaphore: it holds no resources and has no run dir of its own yet, so
    # there is nothing more specific to say and nowhere to write it.
    PLANNED = "planned"

    # Docker resources for the agent container.
    STARTING_CONTAINER = "starting_container"
    SETTING_UP_CONTAINER = "setting_up_container"

    # Preparing the agent *inside* a container that is already healthy:
    # installing its CLI, seeding credentials, installing plugins. Split from
    # the container phase because the two fail for unrelated reasons and have
    # unrelated fixes — a saturated Docker daemon versus an expired OAuth
    # credential — and collapsing them attributed every agent-setup failure to
    # the container.
    SETTING_UP_AGENT = "setting_up_agent"

    # Target stack (benchmark-provided challenge services) launch + network attach.
    LAUNCHING_TARGET = "launching_target"

    # Per-trial workspace preparation.
    SNAPSHOTTING_PRE = "snapshotting_pre"
    PREPARING_WORKSPACE = "preparing_workspace"
    BUILDING_PROMPT = "building_prompt"

    # In-container LLM proxy.
    STARTING_PROXY = "starting_proxy"

    # The agent CLI itself. Normally the longest phase by far, and the only one
    # during which ``proxy/progress.json`` ticks.
    RUNNING_AGENT = "running_agent"

    # Post-agent evidence gathering: on_agent_finish, final check-done capture,
    # declared artifact files, trajectory generation.
    COLLECTING_ARTIFACTS = "collecting_artifacts"
    SNAPSHOTTING_POST = "snapshotting_post"
    SCORING = "scoring"
    TEARING_DOWN = "tearing_down"

    # Bookend — the trial reached a terminal status.
    FINISHED = "finished"


#: Phases that mean the runtime is actively working on this trial. A trial
#: record sitting in one of these with a stale heartbeat is a *stalled* trial —
#: which is exactly what the liveness probe must be able to distinguish from a
#: healthy long-running one.
ACTIVE_PHASES: frozenset[str] = frozenset(
    phase.value
    for phase in TrialPhase
    if phase not in {TrialPhase.PLANNED, TrialPhase.FINISHED}
)

#: Human-facing labels. The inspector renders these next to the "Running" chip
#: so a trial that has been quiet for ten minutes still says *what* it is doing.
PHASE_LABELS: dict[str, str] = {
    TrialPhase.PLANNED.value: "Planned",
    TrialPhase.STARTING_CONTAINER.value: "Starting container",
    TrialPhase.SETTING_UP_CONTAINER.value: "Setting up container",
    TrialPhase.SETTING_UP_AGENT.value: "Setting up agent",
    TrialPhase.LAUNCHING_TARGET.value: "Launching target",
    TrialPhase.SNAPSHOTTING_PRE.value: "Snapshotting pre-state",
    TrialPhase.PREPARING_WORKSPACE.value: "Preparing workspace",
    TrialPhase.BUILDING_PROMPT.value: "Building prompt",
    TrialPhase.STARTING_PROXY.value: "Starting proxy",
    TrialPhase.RUNNING_AGENT.value: "Running agent",
    TrialPhase.COLLECTING_ARTIFACTS.value: "Collecting artifacts",
    TrialPhase.SNAPSHOTTING_POST.value: "Snapshotting post-state",
    TrialPhase.SCORING.value: "Scoring",
    TrialPhase.TEARING_DOWN.value: "Tearing down",
    TrialPhase.FINISHED.value: "Finished",
}


def is_active_phase(phase: object) -> bool:
    """True when ``phase`` names a stage with work in flight."""

    return _normalize(phase) in ACTIVE_PHASES


def phase_label(phase: object) -> str:
    """Human label for ``phase``; unknown values are humanized, not dropped.

    An unrecognized phase is far more useful rendered as "Some New Stage" than
    swallowed into a blank chip — a forward-compatibility rule the rest of the
    status presentation layer already follows.
    """

    normalized = _normalize(phase)
    if not normalized:
        return ""
    label = PHASE_LABELS.get(normalized)
    if label is not None:
        return label
    return normalized.replace("_", " ").capitalize()


def _normalize(value: object) -> str:
    """Lower-cased, stripped string form of ``value`` (``None`` → "").

    Enum members are unwrapped via ``.value`` rather than ``str()``: since
    Python 3.11 a ``str``-mixin Enum stringifies as ``TrialPhase.RUNNING_AGENT``,
    not ``running_agent``, so ``str()`` here would silently fail to match any
    known phase and every lookup would fall through.
    """

    if value is None:
        return ""
    if isinstance(value, TrialPhase):
        return value.value
    return str(value).strip().lower()


__all__ = [
    "ACTIVE_PHASES",
    "PHASE_LABELS",
    "TrialPhase",
    "is_active_phase",
    "phase_label",
]
