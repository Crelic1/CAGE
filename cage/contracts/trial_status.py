"""Trial status vocabulary — the single source of truth for "how a trial ended".

Every layer that summarizes a batch of trials (the canonical run record, the
scoring summary, resume reconstruction, the web header, the CLI banner) needs to
answer the same question: of these trials, how many *completed*, *failed*, or
were *interrupted*? Historically each site re-rolled that classification with a
subtly different definition of "completed", so the numbers could disagree across
the very same run.

This module fixes one definition and one classifier. The buckets are:

* ``completed``  — finished and eligible for scoring.
* ``failed``     — a genuine error terminated the trial.
* ``interrupted``— cancelled or interrupted before a terminal verdict.
* ``running``    — none of the above could be established (still in flight, or
  an input that carries no terminal signal).

**Runtime status and scoring status are separate axes.** Whether a trial ran is
independent of whether it has been scored: a failed trial can carry scoring
evidence, and a completed one can stay unscored. Scoring lives in
``TrialRecord.scoring.status``. Older runs recorded it in the runtime status
instead, so the sets below split into a strict *write* vocabulary and a wider
*read* one — see ``LEGACY_SCORING_TRIAL_STATUSES``. Tolerance belongs on read;
allowing those values on write is what let the two axes blur in the first place.

It lives in ``contracts`` (Layer 0) because it is universal vocabulary: it
imports nothing from the rest of ``cage`` and every other package may import it.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from typing import Any

# ---------------------------------------------------------------------------
# The runtime axis — what a trial's ``status`` field may actually be set to.
# ---------------------------------------------------------------------------

COMPLETED_TRIAL_STATUSES = frozenset({"completed"})
FAILED_TRIAL_STATUSES = frozenset({"failed"})
INTERRUPTED_TRIAL_STATUSES = frozenset({"interrupted", "cancelled"})

#: Every status the runtime may write. This is the **validation** set: it
#: mirrors ``TrialStatus`` minus the two non-terminal values, and nothing
#: outside it should ever reach a trial's ``status``.
TERMINAL_TRIAL_STATUSES = (
    COMPLETED_TRIAL_STATUSES | FAILED_TRIAL_STATUSES | INTERRUPTED_TRIAL_STATUSES
)

# ---------------------------------------------------------------------------
# Legacy tolerance — read-side only.
# ---------------------------------------------------------------------------

#: Scoring states that older runs recorded in the *runtime* status field,
#: before ``TrialRecord.scoring.status`` existed to hold them. They are two
#: different axes: a trial can fail at runtime and still be scored, or complete
#: and stay unscored — which is why the current writer
#: (``mark_trial_scored``) touches only the scoring field and leaves runtime
#: status alone.
#:
#: Kept solely so historical ``.cage_runs`` still classify correctly. Never
#: write these: the validation set above deliberately excludes them, so a new
#: write of ``status="scored"`` now fails loudly instead of silently creating a
#: trial whose runtime status is a scoring state.
LEGACY_SCORING_TRIAL_STATUSES = frozenset({"scored", "not_scored"})

#: What a *reader* should accept as "this trial completed" — the runtime status
#: plus the legacy scoring values. Consumers that classify on-disk records use
#: this; the writer's validator uses the strict set above. Separating the two
#: is the whole point: tolerance belongs on read, never on write.
COMPLETED_TRIAL_STATUSES_ON_READ = (
    COMPLETED_TRIAL_STATUSES | LEGACY_SCORING_TRIAL_STATUSES
)

#: Terminal-on-read: the strict terminal set widened by the same tolerance.
TERMINAL_TRIAL_STATUSES_ON_READ = (
    TERMINAL_TRIAL_STATUSES | LEGACY_SCORING_TRIAL_STATUSES
)

COMPLETED = "completed"
FAILED = "failed"
INTERRUPTED = "interrupted"
RUNNING = "running"


def _normalize(value: Any) -> str:
    """Lower-cased, stripped string form of ``value`` (``None`` → "")."""

    if value is None:
        return ""
    return str(value).strip().lower()


def classify_trial_status(
    *,
    status: Any = None,
    error: Any = None,
    termination_reason: Any = None,
    default: str = RUNNING,
) -> str:
    """Map a trial's raw signals onto one canonical bucket.

    Priority, highest first:

    1. an explicit terminal ``status`` (the canonical record's field),
    2. a ``termination_reason`` that names a terminal outcome,
    3. a truthy ``error`` ⇒ ``failed``,
    4. otherwise ``default`` (no terminal signal could be established).

    ``default`` is ``running`` for live/disk callers, but a caller that only
    ever sees *finished* trials (e.g. the post-run scoring summary) can pass
    ``default="completed"`` so a result carrying no explicit status is still
    treated as a completion rather than as in-flight.

    Returns one of ``"completed" | "failed" | "interrupted" | "running"``.
    """

    # Read side: tolerate the legacy scoring values older runs stored here.
    status_norm = _normalize(status)
    if status_norm in COMPLETED_TRIAL_STATUSES_ON_READ:
        return COMPLETED
    if status_norm in FAILED_TRIAL_STATUSES:
        return FAILED
    if status_norm in INTERRUPTED_TRIAL_STATUSES:
        return INTERRUPTED

    reason_norm = _normalize(termination_reason)
    if reason_norm in COMPLETED_TRIAL_STATUSES_ON_READ:
        return COMPLETED
    if reason_norm in INTERRUPTED_TRIAL_STATUSES:
        return INTERRUPTED
    if reason_norm in FAILED_TRIAL_STATUSES:
        return FAILED

    if error:
        return FAILED
    return default


@dataclass(frozen=True)
class TrialCounts:
    """Tally of trials by canonical bucket. ``running`` doubles as pending."""

    total: int = 0
    completed: int = 0
    failed: int = 0
    interrupted: int = 0
    running: int = 0

    def pending(self) -> int:
        """Trials not yet in a terminal bucket (alias for ``running``)."""

        return self.running


def _read(item: Any, key: str) -> Any:
    """Read ``key`` from a mapping or an object, returning ``None`` if absent."""

    if isinstance(item, Mapping):
        return item.get(key)
    return getattr(item, key, None)


def count_trials(
    items: Iterable[Any],
    *,
    status_key: str = "status",
    error_key: str = "error",
    reason_key: str = "termination_reason",
) -> TrialCounts:
    """Classify every item in ``items`` and tally the buckets.

    Each item may be a mapping or an object; the status / error / reason fields
    are read by ``status_key`` / ``error_key`` / ``reason_key`` respectively.
    ``running`` is the remainder (``total`` minus the three terminal buckets).
    """

    total = completed = failed = interrupted = 0
    for item in items:
        total += 1
        bucket = classify_trial_status(
            status=_read(item, status_key),
            error=_read(item, error_key),
            termination_reason=_read(item, reason_key),
        )
        if bucket == COMPLETED:
            completed += 1
        elif bucket == FAILED:
            failed += 1
        elif bucket == INTERRUPTED:
            interrupted += 1

    running = max(0, total - completed - failed - interrupted)
    return TrialCounts(
        total=total,
        completed=completed,
        failed=failed,
        interrupted=interrupted,
        running=running,
    )
