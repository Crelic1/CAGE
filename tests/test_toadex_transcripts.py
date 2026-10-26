from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

MODULE_PATH = (
    Path(__file__).parents[1] / "examples" / "agent_pentest_bench" / "toadex_transcripts.py"
)


def _module():
    spec = importlib.util.spec_from_file_location("toadex_transcripts", MODULE_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _write_jsonl(path: Path, entries: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(entry) + "\n" for entry in entries),
        encoding="utf-8",
    )


def test_export_preserves_raw_records_and_groups_model_turns(tmp_path: Path) -> None:
    source = tmp_path / "workspace-a" / "capture.jsonl"
    request = {
        "time": "2026-10-27T01:00:00Z",
        "thread": "thread/one",
        "event": "request",
        "data": {"input": [{"role": "user", "content": "inspect target"}]},
    }
    reasoning = {
        "time": "2026-10-27T01:00:01Z",
        "thread": "thread/one",
        "event": "stream",
        "data": {"type": "response.reasoning_summary_text.delta", "delta": "checking"},
    }
    assistant = {
        "time": "2026-10-27T01:00:02Z",
        "thread": "thread/one",
        "event": "stream",
        "data": {"type": "response.output_text.delta", "delta": "Found a lead"},
    }
    _write_jsonl(source, [request, reasoning, assistant])
    output = tmp_path / "export"

    manifest = _module().export_transcripts({"a": source.parent}, output)

    assert manifest["records"] == 3
    assert manifest["model_turns"] == 1
    exported = [
        json.loads(line)
        for line in (output / "events.jsonl").read_text(encoding="utf-8").splitlines()
    ]
    assert [event["category"] for event in exported] == [
        "request",
        "reasoning",
        "assistant_output",
    ]
    assert all(event["model_turn"] == 1 for event in exported)
    assert [event["raw"] for event in exported] == [request, reasoning, assistant]
    grouped = output / "turns" / "a" / "thread-one" / "turn-000001.jsonl"
    assert grouped.is_file()
    assert [json.loads(line)["raw"] for line in grouped.read_text().splitlines()] == [
        request,
        reasoning,
        assistant,
    ]
    assert (output / "raw" / "a" / "capture.jsonl").read_bytes() == source.read_bytes()


def test_export_reports_a_partially_written_raw_record(tmp_path: Path) -> None:
    source = tmp_path / "capture.jsonl"
    source.write_text(
        json.dumps(
            {
                "time": "2026-10-27T01:00:00Z",
                "thread": "thread-one",
                "event": "request",
                "data": {},
            }
        )
        + "\n"
        + '{"time":"2026-10-27T01:00:01Z","event":"stream"',
        encoding="utf-8",
    )

    manifest = _module().export_transcripts({"a": source}, tmp_path / "export")

    assert manifest["records"] == 1
    assert manifest["malformed_records"] == 1
    errors = [
        json.loads(line) for line in (tmp_path / "export" / "errors.jsonl").read_text().splitlines()
    ]
    assert errors == [
        {
            "schema_version": 1,
            "workspace": "a",
            "source_file": "capture.jsonl",
            "error": "malformed JSONL record",
        }
    ]


def test_export_keeps_threads_distinct_when_safe_names_collide(tmp_path: Path) -> None:
    source = tmp_path / "capture.jsonl"
    _write_jsonl(
        source,
        [
            {"thread": "thread/one", "event": "request", "data": {"input": "one"}},
            {"thread": "thread-one", "event": "request", "data": {"input": "two"}},
        ],
    )

    _module().export_transcripts({"a": source}, tmp_path / "export")

    turn_files = sorted((tmp_path / "export" / "turns" / "a").glob("*/turn-*.jsonl"))
    assert len(turn_files) == 2
    assert {json.loads(path.read_text().strip())["thread_id"] for path in turn_files} == {
        "thread/one",
        "thread-one",
    }


def test_manifest_summarizes_threads_and_event_categories(tmp_path: Path) -> None:
    source = tmp_path / "capture.jsonl"
    _write_jsonl(
        source,
        [
            {"thread": "one", "event": "request", "data": {}},
            {
                "thread": "one",
                "event": "stream",
                "data": {"type": "response.output_text.delta", "delta": "hello"},
            },
            {"thread": "two", "event": "request", "data": {}},
        ],
    )

    manifest = _module().export_transcripts({"a": source}, tmp_path / "export")

    assert manifest["threads"] == 2
    assert manifest["categories"] == {"assistant_output": 1, "request": 2}
