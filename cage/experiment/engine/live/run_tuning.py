"""The file ``cage run --tune`` writes and a running run reads.

The mirror image of :mod:`run_heartbeat`: that one is the run telling the world
it is alive, this one is the world telling the run to change shape. Both are a
single JSON file in the run directory, because ``cage run --tune`` is a separate
process from the run it adjusts and two processes need somewhere to meet.

A long run's right answer changes while it is running — a box is scaled up, a
new one comes online, one starts misbehaving. Restarting to act on that costs
every in-flight trial, which on a benchmark whose trials run for hours is the
expensive part. So the run re-reads this file at exactly one point: just before
a trial takes an endpoint slot. That point is already a critical section (the
pool's lock), which is why applying config there adds no new synchronisation and
no new race.

Writes are atomic (tmp + ``os.replace``) and only ever come from the CLI, which
validates first. That combination is deliberate: a half-written file read by a
worker mid-parse is the classic failure of watch-a-file designs, and hand-editing
this file is not supported for exactly that reason.

The run writes its own launch configuration here at startup, so the file is
always the COMPLETE picture rather than a diff — you can read it to see what a
run is doing now, and ``--tune --clear`` has a baseline to restore.
"""

from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

TUNING_FILENAME = "endpoint_concurrency.json"
TUNING_SCHEMA = "endpoint_concurrency.v1"


def tuning_path(run_dir: Path | str) -> Path:
    return Path(run_dir) / TUNING_FILENAME


def read_tuning(run_dir: Path | str) -> dict[str, Any] | None:
    """Parse the tuning file; ``None`` when absent or unusable.

    Never raises: an unreadable tuning file must leave the run executing on the
    configuration it already has, not kill it.
    """
    path = tuning_path(run_dir)
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return None
    except (OSError, ValueError) as exc:
        logger.warning("tuning file %s is unreadable (%s); ignoring", path, exc)
        return None
    if not isinstance(data, dict):
        logger.warning("tuning file %s is not an object; ignoring", path)
        return None
    return data


def write_tuning(run_dir: Path | str, payload: dict[str, Any]) -> Path:
    """Atomically write the tuning file. Returns its path."""
    path = tuning_path(run_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    body = dict(payload)
    body.setdefault("schema_version", TUNING_SCHEMA)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(body, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(tmp, path)  # atomic: a reader sees the old file or the new one
    return path


def write_launch_baseline(
    run_dir: Path | str,
    pools_by_label: dict[str, dict[str, int | None]],
) -> None:
    """Record the pool each agent launched with, unless a tuning file exists.

    Writes the same mapping twice: under ``agents`` (live state, edited by
    tunes) and under ``launch`` (never modified, so ``--tune-clear`` has a
    destination). Endpoints with no declared capacity are omitted — there is no
    number to restore for them, and they were never capped to begin with.

    Without this the file would list only endpoints somebody happened to tune,
    so reading it would give a misleading partial picture and ``--clear`` would
    have no baseline to restore. An existing file is never overwritten — on
    ``--resume`` the operator's last tuning is the state worth keeping.
    """
    if read_tuning(run_dir) is not None:
        return
    declared = {
        label: {sid: cap for sid, cap in sources.items() if cap is not None}
        for label, sources in pools_by_label.items()
    }
    declared = {label: caps for label, caps in declared.items() if caps}
    if not declared:
        return
    write_tuning(run_dir, {
        # ``agents`` is what the run acts on and what a tune edits.
        "agents": {label: {"sources": dict(caps)} for label, caps in declared.items()},
        # ``launch`` is the immutable original, kept so --tune-clear knows where
        # "back" is. Nothing reads it at runtime.
        "launch": declared,
    })


def source_caps_for_agent(tuning: dict[str, Any], agent_label: str) -> dict[str, int] | None:
    """Endpoint caps this file declares for ``agent_label``.

    ``None`` means "says nothing about this agent" — different from an empty
    mapping ("this agent has no capped endpoints"), and it must leave the
    agent's current pool untouched.
    """
    agents = tuning.get("agents")
    if not isinstance(agents, dict):
        return None
    entry = agents.get(agent_label)
    if not isinstance(entry, dict):
        return None
    sources = entry.get("sources")
    if not isinstance(sources, dict):
        return None
    caps: dict[str, int] = {}
    for sid, cap in sources.items():
        try:
            caps[str(sid)] = max(0, int(cap))
        except (TypeError, ValueError):
            logger.warning(
                "tuning: ignoring non-integer capacity %r for source %s", cap, sid
            )
    return caps


@dataclass
class TuningWatcher:
    """Returns the tuning payload only when it differs from the last one seen.

    Compares CONTENT, not ``(mtime, size)``. Two successive tunes routinely
    produce files of identical length (``{"box1": 0}`` → ``{"box1": 6}``), and
    ``os.replace`` can land them within the same mtime tick — a stat-based
    signature then reports "unchanged" and silently drops the second tune. That
    was observed, not theorised. Parsing a few hundred bytes once per trial
    start is far cheaper than a tune that goes missing.
    """

    run_dir: Path
    _last: dict[str, Any] | None = None

    def poll(self) -> dict[str, Any] | None:
        """Return the tuning payload if it changed since the last poll."""
        payload = read_tuning(self.run_dir)
        if payload == self._last:
            return None
        self._last = payload
        return payload

    def prime(self) -> None:
        """Adopt the file's current contents as the baseline, reporting nothing.

        Used right after the run writes its own launch state, so that write does
        not come back as a "change" the scheduler would pointlessly re-apply.
        """
        self._last = read_tuning(self.run_dir)


__all__ = [
    "TUNING_FILENAME",
    "TUNING_SCHEMA",
    "TuningWatcher",
    "read_tuning",
    "source_caps_for_agent",
    "tuning_path",
    "write_launch_baseline",
    "write_tuning",
]
