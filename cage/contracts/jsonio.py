"""How cage reads and writes JSON and JSONL files. One seam, both directions.

Everything on disk in a run is one of two shapes:

* a **JSON document** — ``meta.json``, ``dashboard.json``, ``progress.json``;
* a **JSONL log** — ``proxy.jsonl``, ``events.jsonl``, ``resources.jsonl``,
  ``check_done_polls.jsonl``: one JSON object per ``\\n``-terminated line,
  append-only.

The reason both live in one module is that the JSONL pair has an invariant a
lone reader or a lone writer cannot hold:

    the writer emits ``json.dumps(..., ensure_ascii=False) + "\\n"``,
    so the reader must split on ``\\n`` — and on nothing else.

JSON escapes every character below ``0x20``, but ``ensure_ascii=False`` leaves
U+0085 (NEL), U+2028 and U+2029 in the payload verbatim, and Python's
``str.splitlines()`` treats all three as line terminators. A reader built on
``read_text().splitlines()`` therefore cuts such a record in half; both halves
fail ``json.loads`` and vanish, usually through an
``except JSONDecodeError: continue`` that doesn't even count them. One
mojibake'd web page in an agent's context (UTF-8 bytes decoded as Latin-1 turn
``0xC2 0x85`` into a raw NEL) is enough to delete every later call in that
conversation from token totals, scorer input and derived projections —
silently, while a neighbouring reader that iterates the file object still sees
them all. Observed in the wild: 500 recorded calls read as 433.

So: read JSONL through :func:`iter_jsonl_entries`, write it through
:func:`append_jsonl_record`, and never reach for ``splitlines()``.

The one writer that cannot import this module is the in-container proxy
(``cage/proxy/sidecar.py``, httpx-only by invariant). It hand-rolls the same
``json.dumps(..., ensure_ascii=False) + "\\n"`` line — which is exactly the
contract the readers here are built to survive.

This module sits at the dependency-free floor because every layer touches run
artifacts: the host-side proxy, the artifact writer, the scoring runtime and
the web inspector all read the same files and must read them the same way.
"""

from __future__ import annotations

import json
from collections.abc import Callable, Iterator, Mapping
from pathlib import Path
from typing import Any

__all__ = [
    "append_jsonl_record",
    "count_jsonl_lines",
    "dump_jsonl_record",
    "iter_jsonl_entries",
    "iter_jsonl_lines",
    "load_json_file",
    "read_jsonl_entries",
    "write_json_file",
]


# --- JSON documents --------------------------------------------------------

def load_json_file(path: str | Path) -> Any:
    """Read a JSON document, returning ``{}`` for anything unreadable.

    Deliberately total: callers are recovery paths (resume, dashboards, live
    views) that must keep going when a file is missing or half-written.
    """
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except Exception:
        return {}


def write_json_file(path: str | Path, payload: Mapping[str, Any]) -> None:
    """Write a pretty UTF-8 JSON document, creating parent directories."""
    file_path = Path(path)
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )


# --- JSONL logs ------------------------------------------------------------

def dump_jsonl_record(payload: Mapping[str, Any]) -> str:
    """Serialize one record as a JSONL line, terminator included."""
    return json.dumps(payload, ensure_ascii=False) + "\n"


def append_jsonl_record(path: str | Path, record: Mapping[str, Any] | str) -> None:
    """Append one record to a JSONL log, creating parent directories.

    Accepts a mapping, or a line a caller already serialized (some records have
    their own canonical form — sorted keys, schema version). Either way exactly
    one ``\\n`` terminates the line, which is what makes the readers below the
    exact inverse of this function.
    """
    file_path = Path(path)
    file_path.parent.mkdir(parents=True, exist_ok=True)
    line = record if isinstance(record, str) else dump_jsonl_record(record)
    if not line.endswith("\n"):
        line += "\n"
    with file_path.open("a", encoding="utf-8") as handle:
        handle.write(line)


def iter_jsonl_lines(path: str | Path) -> Iterator[str]:
    """Yield the non-empty, stripped lines of a JSONL log.

    Streams the file: one ``proxy.jsonl`` line can be tens of megabytes (agents
    resend the whole conversation on every call), so nothing here holds the
    file in memory. ``errors="replace"`` keeps a partially-flushed multi-byte
    character at the tail of a live log from raising — that line fails to parse
    and is reported as malformed instead of taking down the caller.
    """
    file_path = Path(path)
    if not file_path.is_file():
        return
    with file_path.open("r", encoding="utf-8", errors="replace") as handle:
        for raw in handle:
            line = raw.strip()
            if line:
                yield line


def iter_jsonl_entries(
    path: str | Path,
    *,
    on_malformed: Callable[[str], None] | None = None,
) -> Iterator[dict[str, Any]]:
    """Yield each record of a JSONL log, decoded as a JSON object.

    Lines that don't parse, or decode to something other than an object, are
    skipped — and handed to ``on_malformed`` when given, so a caller can
    surface the loss instead of silently under-reporting.
    """
    for line in iter_jsonl_lines(path):
        try:
            entry = json.loads(line)
        except json.JSONDecodeError:
            if on_malformed is not None:
                on_malformed(line)
            continue
        if not isinstance(entry, dict):
            if on_malformed is not None:
                on_malformed(line)
            continue
        yield entry


def read_jsonl_entries(
    path: str | Path,
    *,
    on_malformed: Callable[[str], None] | None = None,
) -> list[dict[str, Any]]:
    """Eager :func:`iter_jsonl_entries`, for callers that need the whole list."""
    return list(iter_jsonl_entries(path, on_malformed=on_malformed))


def count_jsonl_lines(path: str | Path) -> int:
    """Count the records in a JSONL log — the basis for monotonic record ids."""
    return sum(1 for _ in iter_jsonl_lines(path))
