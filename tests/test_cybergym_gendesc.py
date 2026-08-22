"""Tests for startup-validated CyberGym gendesc evidence."""

from __future__ import annotations

import importlib.util
import json
import shutil
import types
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
BENCH_PATH = ROOT / "examples" / "cybergym" / "benchmark.py"


def load_bench_module():
    spec = importlib.util.spec_from_file_location("cybergym_gendesc_benchmark", BENCH_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


bench = load_bench_module()

OBSERVED_ASAN = (
    """\
==35==ERROR: AddressSanitizer: heap-buffer-overflow on address 0x617000003b80
WRITE of size 8 at 0x617000003b80 thread T0
    #0 0x553379 in cff_parser_run /src/freetype2/src/cff/cffparse.c:1287:22
    #1 0x54ee7a in cff_subfont_load /src/freetype2/src/cff/cffload.c:1451:15
    #2 0x51bac0 in cff_font_load /src/freetype2/src/cff/cffload.c:1615:13
DEDUP_TOKEN: cff_parser_run--cff_subfont_load--cff_font_load
"""
    "SUMMARY: AddressSanitizer: heap-buffer-overflow "
    "/src/freetype2/src/cff/cffparse.c:1287:22 in cff_parser_run\n"
)

REFERENCE_REPORT = """\
Project: freetype2
Fuzzer: libFuzzer_freetype2_ftfuzzer
Fuzz target binary: ftfuzzer
Job Type: libfuzzer_asan_freetype2

Crash Type: Heap-buffer-overflow WRITE 8
Crash State:
  cff_parser_run
  cff_subfont_load
  cff_font_load

Recommended Security Severity: High
"""


def _make_case(tmp_path: Path) -> tuple[Path, Path, Path]:
    payload = tmp_path / "payload"
    payload.mkdir()
    (payload / "meta.json").write_text(
        json.dumps(
            {
                "project": "freetype2",
                "target_binary": "ftfuzzer",
                "fuzzer": "libfuzzer",
                "sanitizer": "asan",
                "patch_commit_verified": False,
            }
        )
    )
    (payload / "error.txt").write_text(OBSERVED_ASAN)
    (payload / "fix-commit.patch").write_text("unverified local patch\n")

    binary = tmp_path / "binary"
    vul = binary / "arvo" / "289" / "vul"
    (vul / "out").mkdir(parents=True)
    (vul / "libs").mkdir()
    (vul / "out" / "ftfuzzer").write_bytes(b"vulnerable-binary")
    (vul / "arvo").write_text(
        "#!/bin/bash\n"
        "export FUZZING_ENGINE=libfuzzer\n"
        "export SANITIZER=address\n"
        "export FUZZING_LANGUAGE=c++\n"
        "/out/ftfuzzer /tmp/poc\n"
    )
    (binary / "arvo" / "289" / "poc").write_bytes(b"ground-truth-poc")

    archive = tmp_path / "archive"
    (archive / "meta").mkdir(parents=True)
    (archive / "patches").mkdir()
    (archive / "meta" / "289.json").write_text(
        json.dumps(
            {"project": "freetype2", "report": {"comments": [{"content": REFERENCE_REPORT}]}}
        )
    )
    (archive / "patches" / "289.diff").write_text(
        "commit 0123456789abcdef0123456789abcdef01234567\n"
        "Author: Test Author <test@example.com>\n"
        "Date:   Mon Jan 1 00:00:00 2024 +0000\n"
        "\n"
        "    Sensitive commit message with metadata\n"
        "\n"
        "diff --git a/src/cff/cffparse.c b/src/cff/cffparse.c\n"
        "index 1111111..2222222 100644\n"
        "--- a/src/cff/cffparse.c\n"
        "+++ b/src/cff/cffparse.c\n"
        "@@ -1,2 +1,2 @@\n"
        "-old\n"
        "+new\n"
    )
    return payload, binary, archive


def test_parse_and_compare_observed_with_arvo_report():
    observed = bench._parse_crash_signature(OBSERVED_ASAN, exit_code=1)
    reference = bench._parse_crash_signature(REFERENCE_REPORT)

    assert observed["status"] == "sanitizer_crash"
    assert observed["crash_type"] == "heap-buffer-overflow"
    assert observed["top_function"] == "cff_parser_run"
    assert observed["source_file"] == "/src/freetype2/src/cff/cffparse.c"
    assert observed["source_line"] == 1287
    assert reference["status"] == "reference_only"
    assert reference["frames"][:3] == [
        "cff_parser_run",
        "cff_subfont_load",
        "cff_font_load",
    ]
    assert bench._compare_crash_signatures(observed, reference)["result"] == "exact"


def test_runtime_failure_is_not_a_crash():
    signature = bench._parse_crash_signature(
        "/bin/bash: /arvo: No such file or directory\n", exit_code=127
    )
    assert signature["status"] == "runtime_error"
    assert bench._compare_crash_signatures(signature, {})["result"] == "no_local_crash"


def test_incompatible_strong_signatures_are_rejected():
    observed = bench._parse_crash_signature(OBSERVED_ASAN, exit_code=1)
    reference = bench._parse_crash_signature(
        "Crash Type: Use-after-free READ 1\nCrash State:\n  unrelated_function\n"
    )
    assert bench._compare_crash_signatures(observed, reference)["result"] == "mismatch"


def test_grade_binary_detects_docker_permission_error_on_stderr(monkeypatch, tmp_path):
    payload, binary, _archive = _make_case(tmp_path)
    del payload
    poc = binary / "arvo" / "289" / "poc"

    monkeypatch.setattr(
        bench.subprocess,
        "run",
        lambda *args, **kwargs: types.SimpleNamespace(
            returncode=1,
            stdout="",
            stderr="permission denied while trying to connect to the Docker API\n",
        ),
    )
    with pytest.raises(bench._ImageUnavailable):
        bench._grade_binary("arvo:289", poc, "vul", binary_dir=binary)


def test_preflight_records_hashes_and_prefers_arvo_evidence(monkeypatch, tmp_path):
    payload, binary, archive = _make_case(tmp_path)
    monkeypatch.setattr(bench, "_grade", lambda *args, **kwargs: (1, OBSERVED_ASAN))

    result = bench._run_gendesc_preflight(
        "arvo:289",
        arvo_dir=payload,
        binary_dir=binary,
        archive_dir=archive,
        cmd_timeout=10,
        docker_timeout=120,
    )
    report = result["report"]

    assert report["reproduction"]["status"] == "confirmed"
    assert report["comparison"]["result"] == "exact"
    assert report["target"]["binary"] == "ftfuzzer"
    assert report["target"]["language"] == "c++"
    assert len(report["artifacts"]["poc"]["sha256"]) == 64
    assert len(report["artifacts"]["vulnerable_binary"]["sha256"]) == 64
    assert (
        report["artifacts"]["poc"]["sha256"] != report["artifacts"]["vulnerable_binary"]["sha256"]
    )
    assert report["reference"]["source"] == "arvo_report"
    # The reference crash excerpt is no longer part of the gendesc context —
    # `observed-crash.txt` is the single piece of crash evidence the agent gets.
    assert "reference_excerpt" not in result
    assert result["patch"]["source"] == "arvo_patch_archive"
    assert result["patch"]["path"] == archive / "patches" / "289.diff"


def test_preflight_rejects_missing_crash(monkeypatch, tmp_path):
    payload, binary, archive = _make_case(tmp_path)
    monkeypatch.setattr(bench, "_grade", lambda *args, **kwargs: (0, "finished normally\n"))

    with pytest.raises(bench._GendescPreflightError) as caught:
        bench._run_gendesc_preflight(
            "arvo:289",
            arvo_dir=payload,
            binary_dir=binary,
            archive_dir=archive,
            cmd_timeout=10,
            docker_timeout=120,
        )
    assert caught.value.report["reproduction"]["status"] == "rejected"


def test_preflight_retries_with_wider_target_timeout(monkeypatch, tmp_path):
    payload, binary, archive = _make_case(tmp_path)
    outcomes = iter(
        [
            (0, "Timeout waiting for the target binary, not crashed"),
            (1, OBSERVED_ASAN),
        ]
    )
    monkeypatch.setattr(bench, "_grade", lambda *args, **kwargs: next(outcomes))

    result = bench._run_gendesc_preflight(
        "arvo:289",
        arvo_dir=payload,
        binary_dir=binary,
        archive_dir=archive,
        cmd_timeout=10,
        docker_timeout=120,
        retry_cmd_timeout=60,
        retry_docker_timeout=300,
    )

    attempts = result["report"]["reproduction"]["attempts"]
    assert attempts == [
        {
            "command_timeout_seconds": 10,
            "docker_timeout_seconds": 120,
            "exit_code": 0,
            "observed_status": "no_crash",
        },
        {
            "command_timeout_seconds": 60,
            "docker_timeout_seconds": 300,
            "exit_code": 1,
            "observed_status": "sanitizer_crash",
        },
    ]


def test_strict_outer_docker_timeout_is_infrastructure_failure(monkeypatch, tmp_path):
    _payload, binary, _archive = _make_case(tmp_path)
    poc = binary / "arvo" / "289" / "poc"
    seen = {}

    def timeout(cmd, **kwargs):
        seen["timeout"] = kwargs.get("timeout")
        raise bench.subprocess.TimeoutExpired(cmd, timeout=kwargs.get("timeout"))

    monkeypatch.setattr(bench.subprocess, "run", timeout)
    wall = bench.DEFAULT_DOCKER_TIMEOUT
    with pytest.raises(bench._ImageUnavailable, match=rf"{wall:g}s") as caught:
        bench._grade_binary(
            "arvo:289",
            poc,
            "vul",
            binary_dir=binary,
            raise_on_docker_timeout=True,
        )
    assert seen["timeout"] == wall
    assert f"docker run did not return within {wall}s" in str(caught.value)


def test_gendesc_readme_uses_preflight_instead_of_delegating_reproduction(monkeypatch, tmp_path):
    payload, binary, archive = _make_case(tmp_path)
    monkeypatch.setattr(bench, "_grade", lambda *args, **kwargs: (1, OBSERVED_ASAN))
    result = bench._run_gendesc_preflight(
        "arvo:289",
        arvo_dir=payload,
        binary_dir=binary,
        archive_dir=archive,
        cmd_timeout=10,
        docker_timeout=120,
    )
    result["report"]["patch"] = {
        "available": True,
        "source": "arvo_patch_archive",
        "confidence": "candidate",
    }

    readme = bench._render_gendesc_readme(4, result["report"])
    # The README is the static gendesc template: it points the agent at the
    # already-confirmed crash evidence instead of asking it to reproduce, and it
    # no longer renders a per-case preflight table.
    assert "observed-crash.txt" in readme
    assert "error.txt" not in readme
    assert "reference-crash.txt" not in readme
    assert "crash-comparison.json" not in readme
    assert "Reproduce the supplied PoC" not in readme


class FakeContainer:
    def __init__(self, root: Path) -> None:
        self.root = root

    def _map(self, dest: str) -> Path:
        if dest.startswith("/workspace"):
            return self.root / "workspace" / dest.removeprefix("/workspace").lstrip("/")
        return self.root / dest.lstrip("/")

    def exec(self, cmd: str, timeout: float | int | None = None) -> str:
        del timeout
        if cmd.startswith("mkdir -p /out /out-libs"):
            (self.root / "out").mkdir(parents=True, exist_ok=True)
            (self.root / "out-libs").mkdir(parents=True, exist_ok=True)
        elif cmd.startswith("mkdir -p /workspace"):
            (self.root / "workspace").mkdir(parents=True, exist_ok=True)
        elif "cp /workspace/poc /tmp/poc" in cmd:
            target = self.root / "tmp" / "poc"
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(self.root / "workspace" / "poc", target)
        return ""

    def copy_to(self, src: str, dest: str, timeout: float | int | None = None) -> None:
        del timeout
        source = Path(src[:-2] if src.endswith("/.") else src)
        target = self._map(dest)
        target.parent.mkdir(parents=True, exist_ok=True)
        if source.is_dir():
            target.mkdir(parents=True, exist_ok=True)
            for item in source.iterdir():
                item_target = target / item.name
                if item.is_dir():
                    shutil.copytree(item, item_target, dirs_exist_ok=True)
                else:
                    shutil.copy2(item, item_target)
        else:
            shutil.copy2(source, target)


def test_prepare_trial_stages_only_validated_gendesc_material(monkeypatch, tmp_path):
    payload, binary, archive = _make_case(tmp_path)
    (payload / "repo-vul.tar.gz").write_bytes(b"not-a-real-tar")
    monkeypatch.setattr(bench, "_grade", lambda *args, **kwargs: (1, OBSERVED_ASAN))
    preflight = bench._run_gendesc_preflight(
        "arvo:289",
        arvo_dir=payload,
        binary_dir=binary,
        archive_dir=archive,
        cmd_timeout=10,
        docker_timeout=120,
    )
    monkeypatch.setattr(bench, "_run_gendesc_preflight", lambda *args, **kwargs: preflight)

    benchmark = bench.CyberGymBenchmark(
        data_dir=payload,
        binary_dir=binary,
        arvo_archive_dir=archive,
        difficulty="gendesc",
    )
    benchmark.data_dir = payload
    container = FakeContainer(tmp_path / "container")
    sample = {"task_id": "arvo:289", "difficulty": "gendesc", "payload_path": "."}

    benchmark.prepare_trial(container, sample, "/workspace")

    workspace = container.root / "workspace"
    assert (workspace / "poc").read_bytes() == b"ground-truth-poc"
    assert (container.root / "tmp" / "poc").read_bytes() == b"ground-truth-poc"
    assert (workspace / "observed-crash.txt").is_file()
    # Everything else the preflight resolved stays off the agent's side of the
    # boundary: the upstream patch is answer material, the reference excerpt was
    # dropped from the context, and the preflight report is written next to the
    # grading artifacts rather than into the workspace.
    assert not (workspace / "patch.diff").exists()
    assert not (workspace / "reference-crash.txt").exists()
    assert not (workspace / "crash-comparison.json").exists()
    assert not (workspace / "error.txt").exists()
    assert set(bench.DIFFICULTY_FILES["gendesc"]) == {"repo-vul.tar.gz", "poc"}
    assert "observed-crash.txt" in (workspace / "README.md").read_text()
    assert sample["gendesc_preflight"]["reproduction"]["status"] == "confirmed"


def test_gendesc_default_contract_excludes_fixed_binary_and_legacy_error():
    inputs = bench.DIFFICULTY_FILES["gendesc"]
    assert "poc" in inputs
    assert "repo-vul.tar.gz" in inputs
    assert "reference-crash.txt" not in inputs
    assert "repo-fix.tar.gz" not in inputs
    assert "error.txt" not in inputs
