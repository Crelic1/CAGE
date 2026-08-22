"""Regression: JSONL records must survive Unicode line separators in payloads.

``json.dumps(..., ensure_ascii=False)`` — what every cage writer uses — escapes
control characters but leaves U+0085 (NEL), U+2028 and U+2029 raw. Python's
``str.splitlines()`` treats all three as line breaks, so any reader built on
``read_text().splitlines()`` cuts such a record in two, fails to parse both
halves, and drops the record without a trace.

Seen in production: a mojibake'd page in an agent's context (UTF-8 bytes read as
Latin-1 turn 0xC2 0x85 into a raw NEL) put one NEL into the conversation
history, which then rode along in every later request — a 500-call trial was
reported as 433 calls and 36.4M input tokens instead of 44.9M, with "0.0%
errors", while the trial page (which iterates the file) showed all 500.

Every test here writes a record the same way the runtime does and asserts the
reader still sees one record.
"""

import json
from pathlib import Path

from cage.contracts.jsonio import (
    append_jsonl_record,
    count_jsonl_lines,
    iter_jsonl_entries,
    load_json_file,
    read_jsonl_entries,
    write_json_file,
)
from cage.proxy.monitor import _parse_proxy_stats
from cage.scoring.context import ScoringContext

# The separators splitlines() treats as line breaks. Written as escapes on
# purpose: a literal U+2028 in this file would itself be a line break to any
# tool that reads this source with splitlines().
SEPARATORS = [
    "\u0085",  # NEL — the one seen in production
    "\u2028",  # LINE SEPARATOR
    "\u2029",  # PARAGRAPH SEPARATOR
    "\x0b",    # VT / FF / file / group / record separators: json.dumps
    "\x0c",    # escapes these, so they reach a reader only through a
    "\x1c",    # hand-written or third-party log. Covered anyway — the
    "\x1d",    # cost of getting one wrong is a silently dropped record.
    "\x1e",
]


def _write_jsonl(path: Path, entries: list[dict]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(e, ensure_ascii=False) + "\n" for e in entries),
        encoding="utf-8",
    )
    return path


def _proxy_entry(text: str, *, tokens_in: int = 100, tokens_out: int = 10) -> dict:
    return {
        "request_id": "req-0001",
        "status": "success",
        "openai_request": {"messages": [{"role": "user", "content": text}]},
        "upstream_response": {
            "choices": [{"message": {"role": "assistant", "content": "ok"}}],
            "usage": {"prompt_tokens": tokens_in, "completion_tokens": tokens_out},
        },
    }


def test_separators_are_written_raw_and_would_split_a_naive_reader(tmp_path: Path):
    """Guard the premise: this is a real hazard, not a hypothetical one."""
    path = _write_jsonl(tmp_path / "p.jsonl", [_proxy_entry("mojibake \x85 tail")])
    raw = path.read_text(encoding="utf-8")

    assert "\x85" in raw, "ensure_ascii=False must leave NEL raw for this to matter"
    assert len(raw.splitlines()) == 2, "splitlines() splits the record — the bug"
    assert len(read_jsonl_entries(path)) == 1, "the line-safe reader keeps it whole"


def test_every_unicode_separator_survives_a_round_trip(tmp_path: Path):
    for i, sep in enumerate(SEPARATORS):
        path = _write_jsonl(
            tmp_path / f"sep-{i}.jsonl",
            [_proxy_entry(f"before{sep}after"), _proxy_entry("plain")],
        )
        entries = read_jsonl_entries(path)
        assert len(entries) == 2, f"record lost on {sep!r}"
        assert count_jsonl_lines(path) == 2, f"line count wrong on {sep!r}"


def test_malformed_records_are_reported_not_swallowed(tmp_path: Path):
    path = tmp_path / "p.jsonl"
    path.write_text('{"a": 1}\nnot json at all\n[1, 2]\n', encoding="utf-8")

    seen: list[str] = []
    entries = list(iter_jsonl_entries(path, on_malformed=seen.append))

    assert entries == [{"a": 1}]
    assert len(seen) == 2, "a bad line and a non-object line both count as malformed"


def test_proxy_stats_count_records_carrying_a_separator(tmp_path: Path):
    """The 500-vs-433 regression, in miniature."""
    entries = [_proxy_entry("clean")] * 3 + [_proxy_entry("poisoned \x85 context")] * 2
    proxy_log = _write_jsonl(tmp_path / "proxy.jsonl", entries)

    stats = _parse_proxy_stats(proxy_log)

    assert stats["num_requests"] == 5
    assert stats["total_requests"] == 5
    assert stats["input_tokens"] == 500
    assert stats["malformed"] == 0


def test_proxy_stats_report_undecodable_records(tmp_path: Path):
    proxy_log = tmp_path / "proxy.jsonl"
    proxy_log.write_text(
        json.dumps(_proxy_entry("clean")) + "\ntruncated {\n",
        encoding="utf-8",
    )

    stats = _parse_proxy_stats(proxy_log)

    assert stats["num_requests"] == 1
    assert stats["malformed"] == 1, "an undercount must announce itself"


def test_scoring_context_proxy_log_keeps_separator_records(tmp_path: Path):
    """A scorer judging a truncated trajectory is the worst version of this bug."""
    trial_dir = tmp_path / "trials" / "t1"
    trial_dir.mkdir(parents=True)
    (trial_dir / "task_output.json").write_text(
        json.dumps({"output": "done", "exit_code": 0, "sample": {}}),
        encoding="utf-8",
    )
    _write_jsonl(
        trial_dir / "proxy" / "proxy.jsonl",
        [_proxy_entry("clean"), _proxy_entry("poisoned \x85 context")],
    )

    ctx = ScoringContext.from_trial_dir(trial_dir)

    assert ctx is not None
    assert len(ctx.proxy_log) == 2


def test_appended_records_read_back_whole(tmp_path: Path):
    """The writer and the readers are one seam: what it writes, they must read.

    Written through the seam rather than by hand, so this breaks if either half
    drifts — a writer that stops escaping, or a reader that starts splitting on
    more than the terminator.
    """
    path = tmp_path / "events.jsonl"
    for sep in SEPARATORS:
        append_jsonl_record(path, _proxy_entry(f"payload{sep}tail"))
    append_jsonl_record(path, '{"pre": "serialized"}')  # already a line

    entries = read_jsonl_entries(path)

    assert len(entries) == len(SEPARATORS) + 1
    assert count_jsonl_lines(path) == len(SEPARATORS) + 1
    assert entries[-1] == {"pre": "serialized"}


def test_json_documents_round_trip_and_missing_files_degrade_quietly(tmp_path: Path):
    path = tmp_path / "nested" / "meta.json"
    payload = {"trial_id": "t1", "note": "sep \u2028 inside a value"}
    write_json_file(path, payload)

    assert load_json_file(path) == payload
    assert load_json_file(tmp_path / "missing.json") == {}, "readers are recovery paths"
