"""Run one corpus export at a time, off the request that asked for it.

Streaming an export straight into the response looked simplest and did not
survive contact with a large run. What went wrong is worth stating, because the
fixes here are each aimed at one of it:

* **A browser disconnect threw the work away.** The generator ran inside the
  response, so a closed connection ended it — after ninety seconds of parsing.
  Seven attempts from a remote browser produced seven HTTP 200s and zero
  completions, while the identical request made locally finished fine.
* **Clicking again started a second full export.** Nothing tied the two
  requests together, so a run whose logs total 3.2 GiB got scanned twice at
  once, peaking near 4 GiB of memory for one user action.
* **A chunked response cannot resume.** No ``Content-Length``, no ranges: an
  interruption at 90% cost the whole thing.

So an export becomes a job. It runs in a daemon thread, writes to ``.partial``
and renames atomically on success, and reports progress that a page can poll.
A second request for the same thing joins the job in flight instead of starting
another. Once finished the artifact is an ordinary file, which the web layer can
serve with a length and honour ranges against.

The cache lives outside ``.cage_runs``: that tree is the immortal record of what
happened, and an export is a derived convenience.
"""

from __future__ import annotations

import hashlib
import json
import os
import threading
import time
from collections.abc import Callable, Iterator
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

# Where finished exports live. Outside the run tree by design; overridable
# because the default sits next to the inspect root, which is not always
# writable.
CACHE_DIR_ENV = "CAGE_CORPUS_CACHE"
CACHE_DIRNAME = ".cage_corpus"


def cache_dir(root: Path) -> Path:
    configured = os.getenv(CACHE_DIR_ENV, "").strip()
    return Path(configured) if configured else root / CACHE_DIRNAME


@dataclass
class ExportJob:
    """One export, its progress, and where its result landed."""

    key: str
    label: str
    path: Path
    state: str = "running"  # running | done | failed
    trials_seen: int = 0
    trials_total: int = 0
    rows: int = 0
    bytes_written: int = 0
    error: str = ""
    started_at: float = field(default_factory=time.time)
    finished_at: float = 0.0
    #: The live tally the export is filling in. Progress is read from here
    #: rather than counted as rows are produced: a run can scan for minutes
    #: without yielding a single row — every trial refused by a gate, say — and
    #: a progress display that only moves on output sits at 0 the whole time,
    #: which is indistinguishable from being stuck.
    tally: Any = None

    def as_dict(self) -> dict[str, Any]:
        elapsed = (self.finished_at or time.time()) - self.started_at
        seen = self.trials_seen
        refused: dict[str, int] = {}
        dropped: dict[str, int] = {}
        if self.tally is not None:
            seen = max(seen, self.tally.trials_seen)
            refused = dict(self.tally.gates.most_common())
            dropped = dict(self.tally.filters.most_common())
        return {
            "state": self.state,
            "label": self.label,
            "trials_seen": seen,
            "trials_total": self.trials_total,
            "rows": self.rows,
            "bytes": self.bytes_written,
            "elapsed_s": round(elapsed, 1),
            "error": self.error,
            "filename": self.path.name,
            # Why an export can finish with nothing in it. Without this a
            # legitimately empty result — every trial refused by a
            # contamination gate — looks exactly like a broken one.
            "refused_by_gate": refused,
            "dropped_by_filter": dropped,
        }


class ExportRegistry:
    """The one place that knows which exports are in flight.

    Keyed by what is being exported plus a fingerprint of the run's current
    contents, so a finished export is reused while the run is unchanged and
    regenerated once it grows — a run being written to would otherwise serve a
    stale corpus forever.
    """

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._jobs: dict[str, ExportJob] = {}

    def get(self, key: str) -> ExportJob | None:
        with self._lock:
            job = self._jobs.get(key)
        if job is None:
            return None
        # A finished job whose file has been removed is no longer finished.
        if job.state == "done" and not job.path.is_file():
            with self._lock:
                self._jobs.pop(key, None)
            return None
        return job

    def submit(
        self,
        key: str,
        label: str,
        path: Path,
        produce: Callable[[ExportJob], Iterator[dict[str, Any]]],
        total: int = 0,
        tally: Any = None,
    ) -> ExportJob:
        """Start the export, or return the one already doing this work.

        Returning the in-flight job is what stops a double click from doubling
        the load; it is also why the caller must not assume the job it gets back
        is the one it asked to create.
        """

        existing = self.get(key)
        if existing is not None and existing.state in ("running", "done"):
            return existing

        job = ExportJob(key=key, label=label, path=path, trials_total=total, tally=tally)
        with self._lock:
            racing = self._jobs.get(key)
            if racing is not None and racing.state in ("running", "done"):
                return racing
            self._jobs[key] = job

        thread = threading.Thread(
            target=self._run, args=(job, produce), name=f"corpus-export-{label}", daemon=True
        )
        thread.start()
        return job

    @staticmethod
    def _run(job: ExportJob, produce: Callable[[ExportJob], Iterator[dict[str, Any]]]) -> None:
        # Written beside the final name so the rename is atomic on the same
        # filesystem: a reader can never observe a half-written corpus, and a
        # crash leaves a .partial that is obviously not a result.
        partial = job.path.with_suffix(job.path.suffix + ".partial")
        try:
            job.path.parent.mkdir(parents=True, exist_ok=True)
            # A previous attempt killed with the process leaves its .partial
            # behind; nothing ever comes back for it, so it would accumulate.
            partial.unlink(missing_ok=True)
            with open(partial, "w") as handle:
                for row in produce(job):
                    line = json.dumps(row, ensure_ascii=False)
                    handle.write(line + "\n")
                    job.rows += 1
                    job.bytes_written += len(line) + 1
            partial.replace(job.path)
            # A sidecar so a cached result can still explain itself. An empty
            # corpus is often the correct answer — every trial refused by a
            # contamination gate — and on the second visit the tally that said
            # so is gone with the process. Without this the cache turns a
            # well-explained "nothing to export" into a bare empty file.
            try:
                job.path.with_suffix(job.path.suffix + ".meta.json").write_text(
                    json.dumps(job.as_dict(), ensure_ascii=False), encoding="utf-8"
                )
            except OSError:
                pass
            job.state = "done"
        except Exception as exc:  # noqa: BLE001
            job.state = "failed"
            job.error = f"{type(exc).__name__}: {exc}"
            partial.unlink(missing_ok=True)
        finally:
            job.finished_at = time.time()


#: Process-wide registry. One inspector process, one set of in-flight exports.
registry = ExportRegistry()


def run_fingerprint(run_dir: Path) -> str:
    """Cheap signature of a run's current contents.

    Trial count and the newest trial mtime. Enough to notice a run that has
    grown or been re-scored since an export was cached, without walking gigabytes
    to find out.
    """

    from cage.artifacts.run_storage import iter_live_trial_dirs

    newest = 0.0
    count = 0
    for trial_dir in iter_live_trial_dirs(run_dir):
        count += 1
        try:
            newest = max(newest, trial_dir.stat().st_mtime)
        except OSError:
            continue
    return f"{count}:{int(newest)}"


def cache_key(scope: str, run_dir: Path, fingerprint: str) -> str:
    digest = hashlib.sha1(f"{scope}|{run_dir}|{fingerprint}".encode()).hexdigest()[:16]
    return digest
