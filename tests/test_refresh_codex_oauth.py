"""Unit coverage for the Codex OAuth cache refresher (no network calls)."""

from __future__ import annotations

import base64
import json
import stat
from pathlib import Path

from scripts.refresh_codex_oauth import _jwt_exp, _write_inplace


def test_write_inplace_preserves_inode_and_permission_mode(tmp_path: Path) -> None:
    auth_path = tmp_path / "auth.json"
    auth_path.write_text('{"old": true}\n', encoding="utf-8")
    auth_path.chmod(0o640)
    inode = auth_path.stat().st_ino

    _write_inplace(auth_path, {"tokens": {"access_token": "replacement"}})

    assert auth_path.stat().st_ino == inode
    assert stat.S_IMODE(auth_path.stat().st_mode) == 0o640
    assert json.loads(auth_path.read_text(encoding="utf-8")) == {
        "tokens": {"access_token": "replacement"},
    }


def test_jwt_exp_reads_unpadded_urlsafe_payload() -> None:
    payload = base64.urlsafe_b64encode(json.dumps({"exp": 12345}).encode())
    token = "header." + payload.decode().rstrip("=") + ".signature"

    assert _jwt_exp(token) == 12345.0
    assert _jwt_exp("not-a-jwt") is None
