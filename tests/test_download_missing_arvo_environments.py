from __future__ import annotations

import hashlib
import io
import json
import re
import subprocess
import tarfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "examples/cybergym/scripts/download_missing_arvo_environments.sh"
INVENTORY_SHA256 = "b54089e3eda6571eb563be9e8217e330315bdce3d993a6366bd05501b4e48c16"


def _embedded_ids() -> list[str]:
    text = SCRIPT.read_text()
    match = re.search(
        r"^# BEGIN ARVO_IDS\n(?P<ids>(?:[0-9]+\n)+)# END ARVO_IDS$",
        text,
        re.MULTILINE,
    )
    assert match, "embedded ARVO ID block is missing or malformed"
    return match.group("ids").splitlines()


def test_embeds_the_exact_missing_inventory_shape() -> None:
    ids = _embedded_ids()

    assert len(ids) == 2_244
    assert len(set(ids)) == len(ids)
    assert sum(int(ident) < 40_000_000 for ident in ids) == 297
    assert sum(int(ident) >= 40_000_000 for ident in ids) == 1_947
    inventory = ("\n".join(ids) + "\n").encode()
    assert hashlib.sha256(inventory).hexdigest() == INVENTORY_SHA256


def test_print_ids_is_self_contained() -> None:
    completed = subprocess.run(
        ["bash", str(SCRIPT), "--print-ids"],
        check=True,
        text=True,
        capture_output=True,
    )

    assert completed.stderr == ""
    assert completed.stdout.splitlines() == _embedded_ids()


def test_help_documents_the_fixed_pull_concurrency() -> None:
    completed = subprocess.run(
        ["bash", str(SCRIPT), "--help"],
        check=True,
        text=True,
        capture_output=True,
    )

    assert "16 concurrent crane pulls" in completed.stdout


def _add_bytes(archive: tarfile.TarFile, name: str, data: bytes, mode: int = 0o644) -> None:
    member = tarfile.TarInfo(name)
    member.size = len(data)
    member.mode = mode
    archive.addfile(member, io.BytesIO(data))


def _write_fixture_image(path: Path) -> None:
    layer_bytes = io.BytesIO()
    with tarfile.open(fileobj=layer_bytes, mode="w") as layer:
        _add_bytes(layer, "bin/arvo", b"#!/bin/bash\n/out/fuzzer /tmp/poc\n", 0o755)
        _add_bytes(layer, "out/fuzzer", b"#!/bin/sh\nexit 0\n", 0o755)
        _add_bytes(layer, "tmp/poc", b"crash-input")

    with tarfile.open(path, mode="w") as image:
        _add_bytes(image, "manifest.json", json.dumps([{"Layers": ["layer.tar"]}]).encode())
        _add_bytes(image, "layer.tar", layer_bytes.getvalue())


def _write_fake_crane(path: Path, fixture: Path, state: Path) -> None:
    path.write_text(
        f"""#!/usr/bin/env python3
import fcntl
import json
import shutil
import sys
import time
from pathlib import Path

fixture = Path({str(fixture)!r})
state_path = Path({str(state)!r})

if len(sys.argv) != 4 or sys.argv[1] != "pull":
    raise SystemExit(2)

with state_path.open("a+", encoding="utf-8") as handle:
    fcntl.flock(handle, fcntl.LOCK_EX)
    handle.seek(0)
    raw = handle.read()
    status = json.loads(raw) if raw else {{"active": 0, "maximum": 0, "calls": 0}}
    status["active"] += 1
    status["maximum"] = max(status["maximum"], status["active"])
    status["calls"] += 1
    call_number = status["calls"]
    handle.seek(0)
    handle.truncate()
    json.dump(status, handle)
    handle.flush()
    fcntl.flock(handle, fcntl.LOCK_UN)

if call_number <= 16:
    deadline = time.monotonic() + 5
    while time.monotonic() < deadline:
        with state_path.open(encoding="utf-8") as handle:
            fcntl.flock(handle, fcntl.LOCK_SH)
            active = json.load(handle)["active"]
        if active >= 16:
            break
        time.sleep(0.01)

time.sleep(0.1)
shutil.copyfile(fixture, sys.argv[3])

with state_path.open("r+", encoding="utf-8") as handle:
    fcntl.flock(handle, fcntl.LOCK_EX)
    status = json.load(handle)
    status["active"] -= 1
    handle.seek(0)
    handle.truncate()
    json.dump(status, handle)
"""
    )
    path.chmod(0o755)


def test_downloads_sixteen_at_a_time_then_extracts_each_batch(tmp_path: Path) -> None:
    fixture = tmp_path / "image.tar"
    state = tmp_path / "fake-crane-state.json"
    crane = tmp_path / "crane"
    destination = tmp_path / "result"
    _write_fixture_image(fixture)
    _write_fake_crane(crane, fixture, state)

    command = [
        "bash",
        str(SCRIPT),
        "--limit",
        "17",
        "--out",
        str(destination),
        "--crane",
        str(crane),
        "--pull-timeout",
        "30",
        "--retries",
        "1",
    ]
    subprocess.run(
        command,
        check=True,
        text=True,
        capture_output=True,
        timeout=60,
    )

    status = json.loads(state.read_text())
    assert status == {"active": 0, "maximum": 16, "calls": 34}
    for ident in _embedded_ids()[:17]:
        task = destination / "arvo" / ident
        assert (task / "vul/arvo").is_file()
        assert (task / "fix/arvo").is_file()
        assert (task / "vul/libs").is_dir()
        assert (task / "fix/libs").is_dir()
        assert (task / "poc").read_bytes() == b"crash-input"
        assert (task / ".collector-ready").is_file()

    log = (destination / ".collector/download.log").read_text()
    first_extract_end = log.index("extract-end")
    second_batch_start = log.index("batch-start", log.index("batch-start") + 1)
    assert first_extract_end < second_batch_start

    assert not list((destination / ".image-cache/n132_arvo").glob("*.tar"))
    subprocess.run(command, check=True, text=True, capture_output=True, timeout=30)
    assert json.loads(state.read_text()) == status
    assert (destination / ".collector/incomplete_ids.txt").read_text() == ""
