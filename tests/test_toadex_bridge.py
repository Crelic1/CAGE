from __future__ import annotations

import importlib.util
import io
import json
import sys
import zipfile
from pathlib import Path
from types import ModuleType

import pytest


def _load_bridge() -> ModuleType:
    path = (
        Path(__file__).resolve().parents[1]
        / "examples"
        / "agent_pentest_bench"
        / "toadex_bridge.py"
    )
    name = "agent_pentest_bench_toadex_bridge"
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _bundle_bytes(*, status: str = "valid", finding_id: str = "finding-1") -> bytes:
    output = io.BytesIO()
    report = """# Cross-account note disclosure

## Replication steps

1. Log in as the first user.
2. Request the second user's note identifier.
"""
    manifest = {
        "finding": {
            "id": finding_id,
            "title": "Cross-account note disclosure",
            "status": status,
            "project": "benchmark/pb-notes-idor",
        },
        "report": {
            "path": "report/Cross-account note disclosure.md",
            "media_type": "text/markdown; charset=utf-8",
        },
        "attachments": [
            {
                "id": "attachment-1",
                "kind": "reproducer",
                "name": "reproduce.py",
                "path": "attachments/reproduce.py",
            }
        ],
        "traffic": [
            {
                "evidence_kind": "http_exchange",
                "evidence_id": "exchange-1",
                "note": "Unauthorised read returned 200",
                "path": "traffic/001-exchange-1",
            }
        ],
    }
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("manifest.json", json.dumps(manifest))
        archive.writestr("report/Cross-account note disclosure.md", report)
        archive.writestr("attachments/reproduce.py", b"print('exact native poc')\n")
        archive.writestr("traffic/001-exchange-1/request.txt", "GET /api/notes/other")
        archive.writestr("traffic/001-exchange-1/response.txt", "HTTP/1.1 200 OK")
    return output.getvalue()


def _write_bundle(path: Path, **kwargs: str) -> Path:
    path.write_bytes(_bundle_bytes(**kwargs))
    return path


def test_adapt_bundle_preserves_native_report_poc_and_traffic(tmp_path: Path) -> None:
    bridge = _load_bridge()
    bundle = _write_bundle(tmp_path / "finding.zip")
    output = tmp_path / "final_answer"

    adapted = bridge.adapt_bundles(
        [bundle],
        output,
        metadata_by_id={
            "finding-1": {
                "id": "finding-1",
                "status": "valid",
                "severity": 3,
                "bug_classes": ["Broken access control"],
                "endpoint": "http://target/api/notes/other",
            }
        },
    )

    assert len(adapted) == 1
    answer = output / "001"
    payload = json.loads((answer / "vulnerability.json").read_text(encoding="utf-8"))
    assert payload["Vulnerability Type"] == "Broken access control"
    assert payload["Source URL"] == "http://target/api/notes/other"
    assert payload["POC"] == [
        "1. Log in as the first user.",
        "2. Request the second user's note identifier.",
    ]
    assert payload["Toadex Finding"] == {
        "id": "finding-1",
        "title": "Cross-account note disclosure",
        "status": "valid",
        "severity": 3,
        "traffic_count": 1,
        "attachment_count": 1,
        "automation_present": True,
        "adapter": "toadex-native-v1",
    }
    assert (answer / "poc.py").read_bytes() == b"print('exact native poc')\n"
    assert (answer / "traffic-001-request.txt").read_text() == "GET /api/notes/other"
    assert (answer / "traffic-001-response.txt").read_text() == "HTTP/1.1 200 OK"
    assert "Cross-account note disclosure" in (answer / "toadex-report.md").read_text()


def test_adapter_rejects_non_customer_ready_findings_and_overwrite(tmp_path: Path) -> None:
    bridge = _load_bridge()
    invalid = _write_bundle(tmp_path / "invalid.zip", status="unvalidated")
    with pytest.raises(bridge.BridgeError, match="non-customer-ready"):
        bridge.adapt_bundles([invalid], tmp_path / "rejected")

    valid = _write_bundle(tmp_path / "valid.zip")
    output = tmp_path / "final_answer"
    bridge.adapt_bundles([valid], output)
    with pytest.raises(bridge.BridgeError, match="refusing to overwrite"):
        bridge.adapt_bundles([valid], output)


def test_empty_adapter_output_is_a_clean_submission(tmp_path: Path) -> None:
    bridge = _load_bridge()
    output = tmp_path / "final_answer"
    assert bridge.adapt_bundles([], output) == []
    assert output.is_dir()
    assert list(output.iterdir()) == []


def test_render_scope_is_black_box_and_contains_no_ground_truth() -> None:
    bridge = _load_bridge()
    rendered = bridge.render_scope(
        ["http://benchmark.test:8080"],
        "Test account: alex@example.test / example-password",
    )
    assert "http://benchmark.test:8080" in rendered
    assert "alex@example.test" in rendered
    lowered = rendered.casefold()
    for forbidden in ("cwe-", "cve-", "canary", "vulnerability class", "source code"):
        assert forbidden not in lowered


def test_client_uses_existing_paginated_findings_and_bundle_apis() -> None:
    bridge = _load_bridge()
    client = bridge.ToadexClient("http://127.0.0.1:8765")
    calls: list[tuple[str, str, dict[str, str] | None]] = []

    def fake_json(method, path, *, query=None, payload=None):
        del payload
        calls.append((method, path, query))
        if query["offset"] == "0":
            return {
                "items": [
                    {"id": "valid-1", "status": "valid"},
                    {"id": "noise", "status": "unvalidated"},
                ],
                "has_more": True,
            }
        return {"items": [{"id": "reported-1", "status": "reported"}], "has_more": False}

    client.json = fake_json
    assert [item["id"] for item in client.list_customer_ready_findings("engagement/path")] == [
        "valid-1",
        "reported-1",
    ]
    assert calls == [
        (
            "GET",
            "/api/v1/projects/by-path/findings",
            {
                "project": "engagement/path",
                "status": "all",
                "offset": "0",
                "limit": "500",
            },
        ),
        (
            "GET",
            "/api/v1/projects/by-path/findings",
            {
                "project": "engagement/path",
                "status": "all",
                "offset": "2",
                "limit": "500",
            },
        ),
    ]

    request_calls = []
    client._request = lambda method, path, **kwargs: (
        request_calls.append((method, path, kwargs)) or (b"zip", "application/zip")
    )
    assert client.download_finding_bundle("engagement/path", "finding / 1") == b"zip"
    assert request_calls == [
        (
            "GET",
            "/api/v1/findings/finding%20%2F%201/bundle",
            {"query": {"project": "engagement/path"}},
        )
    ]
