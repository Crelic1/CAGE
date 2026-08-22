"""Corpus export: layering, segmentation, and the redaction that once broke SFT."""

from __future__ import annotations

import json
import time
from pathlib import Path

import pytest

from cage.corpus.build import BuildOptions, build_segments
from cage.corpus.records import TrainingAdmission
from cage.corpus.redact import (
    Redactor,
    primary_workdir,
    system_prompt,
    redaction_rewrites_workdir,
)
from cage.corpus.render import repair_think_tags, tool_call_xml

REPO_ROOT = Path(__file__).resolve().parents[1]

SYSTEM = (
    "x-anthropic-billing-header: cc_version=1; cch=abc;\n"
    "You are an interactive agent that helps users with software engineering tasks.\n"
    " - Primary working directory: /home/agent/workspace\n"
    " - You are powered by the model teacher-model-9.\n"
)


def _entry(messages, blocks, *, status="success", reasoning=""):
    upstream = {}
    if reasoning:
        upstream = {"choices": [{"message": {"reasoning_content": reasoning}}]}
    return {
        "status": status,
        "anthropic_request": {"system": SYSTEM, "messages": messages},
        "anthropic_response": {"content": blocks},
        "upstream_response": upstream,
        "openai_request": {"tools": [{"name": "Bash"}]},
    }


def _text(value):
    return {"type": "text", "text": value}


def _write_log(tmp_path: Path, entries) -> Path:
    path = tmp_path / "proxy.jsonl"
    path.write_text("\n".join(json.dumps(e) for e in entries), encoding="utf-8")
    return path


# --------------------------------------------------------------------------- #
# Layering
# --------------------------------------------------------------------------- #


def test_corpus_layer_names_no_benchmark() -> None:
    """Layer 1 must not learn any domain's vocabulary.

    A benchmark's gates reach the exporter as opaque codes precisely so the
    framework never needs a branch on one. A benchmark name appearing here means
    that contract was bypassed.
    """

    sources = sorted((REPO_ROOT / "cage" / "corpus").rglob("*.py"))
    sources.append(REPO_ROOT / "cage" / "cli" / "commands" / "corpus.py")
    forbidden = ("cybergym", "nyuctf", "cvebench", "agent_pentest_bench", "arvo", "gendesc")
    offenders = []
    for path in sources:
        lowered = path.read_text(encoding="utf-8").lower()
        for token in forbidden:
            if token in lowered:
                offenders.append(f"{path.relative_to(REPO_ROOT)}: {token}")
    assert not offenders, "benchmark vocabulary leaked into Layer 1: " + "; ".join(offenders)


def test_default_admission_is_permissive() -> None:
    """A benchmark that says nothing must not silently lose its trajectories."""

    admission = TrainingAdmission.ok(passed=True)
    assert admission.admitted
    assert admission.reasons == ()
    blocked = admission.rejected("some_gate", "because")
    assert not blocked.admitted
    assert blocked.reasons == ("some_gate",)
    assert blocked.detail["some_gate"] == "because"
    assert blocked.provenance == admission.provenance


# --------------------------------------------------------------------------- #
# Redaction
# --------------------------------------------------------------------------- #


def test_host_paths_are_redacted_and_container_paths_are_not() -> None:
    """The container path is what the system prompt declares and must survive.

    Rewriting it produced a corpus whose system prompt and actions disagreed,
    and models trained on it addressed a directory that does not exist.
    """

    redact = Redactor()
    text = "cd /data/team/workspace/alice/run7 && cat /home/agent/workspace/poc.bin"
    out = redact(text)
    assert "/data/team" not in out
    assert "/home/agent/workspace/poc.bin" in out


def test_system_prompt_is_verbatim_by_default() -> None:
    """Export reproduces what the agent sent; it does not tidy it up.

    The teacher's identity line and the per-call billing header were both really
    in that prompt. Whether they belong in a training set is a decision the
    consumer can still make on a faithful corpus, and cannot unmake on an
    edited one.
    """

    out = system_prompt(SYSTEM)
    assert "x-anthropic-billing-header" in out
    assert "teacher-model-9" in out
    assert "Primary working directory: /home/agent/workspace" in out

    trimmed = system_prompt(SYSTEM, strip_billing_header=True)
    assert "x-anthropic-billing-header" not in trimmed
    assert "teacher-model-9" in trimmed


def test_primary_workdir_is_read_from_the_prompt() -> None:
    assert primary_workdir(SYSTEM) == "/home/agent/workspace"
    assert primary_workdir("no environment block here") == ""


def test_redaction_must_not_rewrite_the_agents_own_workdir() -> None:
    """The invariant is about the rule, not about any trajectory's text.

    Scanning turns for the placeholder cannot work: a target application with
    its own ``/workspace`` directory, or source quoting ``D:/workspace/img``,
    looks identical to a genuine rewrite. Asking the redactor what it would do
    to the declared directory answers exactly the question, with no false
    positives from either.
    """

    safe = Redactor()
    assert redaction_rewrites_workdir(safe, "/home/agent/workspace") == ""
    assert redaction_rewrites_workdir(safe, "") == ""

    # The historical bug: a pattern broad enough to swallow the container home.
    unsafe = Redactor(host_path_patterns=(r"/home/agent/workspace",))
    assert redaction_rewrites_workdir(unsafe, "/home/agent/workspace")


def test_target_owned_workspace_paths_survive() -> None:
    """Real cases that the earlier output-scanning check wrongly condemned."""

    redact = Redactor()
    for text in (
        "the model lands in /workspace/models/checkpoints/upscale/",
        'String folder = "D:/workspace/img";',
    ):
        assert redact(text) == text


def test_think_tag_repair_only_when_unpaired() -> None:
    assert repair_think_tags("reasoning</think> answer")[1] is True
    assert repair_think_tags("<think>a</think> b")[1] is False
    assert repair_think_tags("no tags at all")[1] is False


def test_tool_call_xml_serialises_non_strings() -> None:
    out = tool_call_xml("Bash", {"command": "ls", "timeout": 5})
    assert "<function=Bash>" in out
    assert "<parameter=command>\nls\n</parameter>" in out
    assert "<parameter=timeout>\n5\n</parameter>" in out


# --------------------------------------------------------------------------- #
# Segmentation
# --------------------------------------------------------------------------- #


def test_single_conversation_yields_one_segment(tmp_path: Path) -> None:
    entries = [
        _entry([{"role": "user", "content": [_text("Build a PoC.")]}], [_text("step one")]),
        _entry(
            [
                {"role": "user", "content": [_text("Build a PoC.")]},
                {"role": "assistant", "content": [_text("step one")]},
                {"role": "user", "content": [_text("keep going")]},
            ],
            [_text("step two")],
            reasoning="thinking hard",
        ),
    ]
    segments, problems = build_segments(_write_log(tmp_path, entries))
    assert problems == []
    assert len(segments) == 1

    segment = segments[0]
    assert segment.n_segments == 1
    assert segment.real_task_present is True
    assert segment.opens_with_summary is False
    # The last turn already carries the whole conversation as its prefix.
    assert [m["role"] for m in segment.messages] == [
        "system", "user", "assistant", "user", "assistant",
    ]
    assert [m["loss"] for m in segment.messages] == [0, 0, 1, 0, 1]
    assert "<think>\nthinking hard\n</think>" in segment.messages[-1]["content"]
    assert segment.stats["n_supervised"] == 2


COMPACTION_INSTRUCTION = (
    "Your task is to create a detailed summary of the conversation. "
    "Do NOT call any tools. Wrap it in <summary> tags."
)
CONTINUATION = (
    "This session is being continued from a previous conversation that ran out "
    "of context. The summary below covers the earlier portion.\n\nSummary: ..."
)


def _compacted_log(tmp_path: Path) -> Path:
    # A realistic run before the boundary: the collapse splitter needs the
    # message count to actually fall, and a normal turn only ever grows it.
    history = [{"role": "user", "content": [_text("Build a PoC.")]}]
    entries = []
    for step in range(6):
        entries.append(_entry(list(history), [_text(f"step {step}")]))
        history.append({"role": "assistant", "content": [_text(f"step {step}")]})
        history.append({"role": "user", "content": [_text(f"result {step}")]})
    entries += [
        # The compaction CALL: instruction appended, response is the summary.
        _entry(history + [{"role": "user", "content": [_text(COMPACTION_INSTRUCTION)]}],
               [_text("<summary>what happened</summary>")]),
        # The continuation: history replaced by the summary.
        _entry([{"role": "user", "content": [_text(CONTINUATION)]}], [_text("after compaction")]),
    ]
    return _write_log(tmp_path, entries)


def test_compaction_splits_and_drops_the_summary_turn(tmp_path: Path) -> None:
    """Two segments, and the summary is never a supervised target.

    Learning to write a conversation summary is not the task; the summary still
    appears in the corpus, on the input side of the next segment, because that
    is where the model really saw it.
    """

    segments, problems = build_segments(_compacted_log(tmp_path))
    assert problems == []
    assert len(segments) == 2
    assert [s.index for s in segments] == [0, 1]
    assert all(s.n_segments == 2 for s in segments)

    supervised = [
        m["content"] for s in segments for m in s.messages if m.get("loss") == 1
    ]
    assert not any("<summary>" in text for text in supervised)

    # The summary survives as context at the head of the second segment.
    second = segments[1]
    assert second.opens_with_summary is True
    assert second.real_task_present is False
    assert any(
        "being continued from a previous conversation" in (m["content"] or "")
        and m["loss"] == 0
        for m in second.messages
    )


def test_keeping_the_compaction_call_is_opt_in(tmp_path: Path) -> None:
    segments, _ = build_segments(
        _compacted_log(tmp_path), BuildOptions(drop_compaction_call=False)
    )
    supervised = [
        m["content"] for s in segments for m in s.messages if m.get("loss") == 1
    ]
    assert any("<summary>" in text for text in supervised)


def test_subagent_turns_are_excluded(tmp_path: Path) -> None:
    sub_system = (
        "You are an agent for Claude Code, Anthropic's official CLI for Claude. "
        "Given the user's message, you should use the tools available."
    )
    main = _entry([{"role": "user", "content": [_text("Build a PoC.")]}], [_text("main turn")])
    sub = _entry([{"role": "user", "content": [_text("go look")]}], [_text("sub turn")])
    sub["anthropic_request"]["system"] = sub_system

    segments, _ = build_segments(_write_log(tmp_path, [main, sub]))
    assert len(segments) == 1
    joined = " ".join(m["content"] or "" for m in segments[0].messages)
    assert "main turn" in joined
    assert "sub turn" not in joined


def test_missing_log_yields_nothing(tmp_path: Path) -> None:
    segments, problems = build_segments(tmp_path / "absent.jsonl")
    assert segments == []
    assert problems == []


@pytest.mark.parametrize("splitter", ["system_prompt", "forest"])
def test_both_splitters_find_the_same_boundary(tmp_path: Path, splitter: str) -> None:
    segments, _ = build_segments(_compacted_log(tmp_path), BuildOptions(splitter=splitter))
    assert len(segments) == 2


# --------------------------------------------------------------------------- #
# Export jobs
# --------------------------------------------------------------------------- #


def test_a_second_request_joins_the_export_already_running(tmp_path: Path) -> None:
    """Clicking twice must not scan the same gigabytes twice.

    This is the failure that made a large run unusable: nothing tied concurrent
    requests together, so one user's repeated clicks became several full
    exports at once.
    """

    import threading

    from cage.corpus.jobs import ExportRegistry

    registry = ExportRegistry()
    started = []
    release = threading.Event()

    def produce(job):
        started.append(1)
        release.wait(5)
        yield {"row": 1}

    first = registry.submit("k", "label", tmp_path / "out.jsonl", produce)
    second = registry.submit("k", "label", tmp_path / "out.jsonl", produce)
    assert first is second
    release.set()
    for _ in range(100):
        if first.state != "running":
            break
        time.sleep(0.05)
    assert first.state == "done", first.error
    assert started == [1], "the export ran more than once"
    assert first.rows == 1


def test_a_failed_export_leaves_no_half_written_file(tmp_path: Path) -> None:
    """A reader must never see a partial corpus as if it were a result."""

    from cage.corpus.jobs import ExportRegistry

    registry = ExportRegistry()
    out = tmp_path / "out.jsonl"

    def produce(job):
        yield {"row": 1}
        raise RuntimeError("upstream went away")

    job = registry.submit("k", "label", out, produce)
    for _ in range(100):
        if job.state != "running":
            break
        time.sleep(0.05)
    assert job.state == "failed"
    assert "upstream went away" in job.error
    assert not out.exists()
    assert not out.with_suffix(".jsonl.partial").exists()


def test_a_finished_export_is_reused_until_the_run_changes(tmp_path: Path) -> None:
    """The cache key must track the run's contents, not just its name."""

    from cage.corpus.jobs import cache_key

    a = cache_key("run", tmp_path, "9:1000")
    assert a == cache_key("run", tmp_path, "9:1000")
    assert a != cache_key("run", tmp_path, "10:1000"), "a new trial must invalidate"
    assert a != cache_key("run", tmp_path, "9:2000"), "a re-scored trial must invalidate"
    assert a != cache_key("trial", tmp_path, "9:1000"), "scopes must not collide"
