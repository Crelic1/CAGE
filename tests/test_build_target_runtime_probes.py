from __future__ import annotations

import json
import os
import socketserver
import subprocess
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import pytest

from examples.build_target.runtime_probes import (
    ProbeContractError,
    execute_runtime_probes,
    normalize_runtime_probes,
)


def test_http_probe_requires_and_checks_application_content() -> None:
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:  # noqa: N802
            body = b"<title>Json Analyser</title>"
            self.send_response(200)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, *_args) -> None:
            pass

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        probes = normalize_runtime_probes(
            [
                {
                    "id": "home-page",
                    "type": "http",
                    "service": "app",
                    "path": "/",
                    "expect_status": 200,
                    "expect_body_contains": "Json Analyser",
                    "attempts": 1,
                    "evidence": [
                        {"path": "writeup.md", "basis": "writeup names the page"}
                    ],
                }
            ],
            target_services=["app"],
            target_ports={"app": server.server_port},
            target_protocols={"app": "http"},
            required=True,
        )
        result = execute_runtime_probes(
            probes,
            targets=[
                {
                    "service_name": "app",
                    "container_addr": "127.0.0.1",
                    "internal_port": server.server_port,
                }
            ],
        )
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)

    assert result["passed"] is True
    attempt = result["probes"][0]["attempts"][0]
    assert attempt["assertions"]["status"]["passed"] is True
    assert attempt["assertions"]["body_contains"]["passed"] is True
    assert "Json Analyser" in attempt["response"]["body_excerpt"]


def test_tcp_probe_checks_real_prompt_and_benign_interaction() -> None:
    class Handler(socketserver.BaseRequestHandler):
        def handle(self) -> None:
            self.request.sendall(b"Choice: ")
            command = self.request.recv(64)
            if command == b"1\n":
                self.request.sendall(b"Name: ")

    server = socketserver.ThreadingTCPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        probes = normalize_runtime_probes(
            [
                {
                    "id": "menu",
                    "type": "tcp",
                    "service": "challenge",
                    "attempts": 1,
                    "steps": [
                        {"expect_contains": "Choice: "},
                        {"send_text": "1\n", "expect_contains": "Name: "},
                    ],
                    "evidence": [
                        {"path": "solve.py", "basis": "solve waits for both prompts"}
                    ],
                }
            ],
            target_services=["challenge"],
            target_ports={"challenge": server.server_address[1]},
            target_protocols={"challenge": "tcp"},
            required=True,
        )
        result = execute_runtime_probes(
            probes,
            targets=[
                {
                    "service_name": "challenge",
                    "container_addr": "127.0.0.1",
                    "internal_port": server.server_address[1],
                }
            ],
        )
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)

    assert result["passed"] is True
    steps = result["probes"][0]["attempts"][0]["steps"]
    assert [step["matched"] for step in steps] == [True, True]
    assert "Choice:" in steps[0]["response_excerpt"]
    assert "Name:" in steps[1]["response_excerpt"]


def test_r4_contract_rejects_port_only_or_uncited_probes() -> None:
    with pytest.raises(ProbeContractError, match="port liveness is only R3"):
        normalize_runtime_probes(
            None,
            target_services=["challenge"],
            target_ports={"challenge": 31337},
            target_protocols={"challenge": "tcp"},
            required=True,
        )

    with pytest.raises(ProbeContractError, match="must cite"):
        normalize_runtime_probes(
            [
                {
                    "id": "port-only",
                    "type": "tcp",
                    "service": "challenge",
                    "expect_contains": "Choice: ",
                }
            ],
            target_services=["challenge"],
            target_ports={"challenge": 31337},
            target_protocols={"challenge": "tcp"},
            required=True,
        )


def test_cage_check_cli_renders_addresses_and_host_probe_without_name_error(
    tmp_path: Path,
) -> None:
    payload = {
        "passed": True,
        "container_addr": "10.240.1.2",
        "validated_rehost_tier": "R4",
        "targets": [
            {
                "service_name": "app",
                "container_addr": "10.240.1.2",
                "internal_port": 8080,
                "protocol": "http",
            }
        ],
        "runtime_probe_results": {
            "passed": True,
            "probe_count": 1,
            "probes": [
                {
                    "id": "home",
                    "service": "app",
                    "attempts": [
                        {
                            "passed": True,
                            "response": {
                                "status": 200,
                                "body_excerpt": "Json Analyser",
                            },
                        }
                    ],
                }
            ],
        },
    }
    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    fake_curl = fake_bin / "curl"
    fake_curl.write_text(
        "#!/usr/bin/env python3\nprint(" + repr(json.dumps(payload)) + ")\n",
        encoding="utf-8",
    )
    fake_curl.chmod(0o755)
    script = (
        Path(__file__).resolve().parents[1]
        / "examples"
        / "build_target"
        / "serve"
        / "cage-check"
    )
    env = dict(os.environ)
    env["PATH"] = f"{fake_bin}:{env['PATH']}"

    result = subprocess.run(
        ["bash", str(script)],
        capture_output=True,
        text=True,
        env=env,
        timeout=10,
    )

    assert result.returncode == 0, result.stderr
    assert "container_addr: 10.240.1.2" in result.stdout
    assert "independent_runtime_probes: PASS (1)" in result.stdout
    assert "Json Analyser" in result.stdout
    assert "NameError" not in result.stderr


def test_cage_check_cli_renders_failed_probe_attempt(tmp_path: Path) -> None:
    payload = {
        "passed": False,
        "failure_class": "runtime_probe_failed",
        "retryable": True,
        "feedback": "semantic probe did not match",
        "evidence": {
            "failed_probes": [
                {
                    "id": "menu-banner",
                    "service": "challenge",
                    "last_attempt": {
                        "passed": False,
                        "error": "[Errno 111] Connection refused",
                    },
                }
            ]
        },
    }
    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    fake_curl = fake_bin / "curl"
    fake_curl.write_text(
        "#!/usr/bin/env python3\nprint(" + repr(json.dumps(payload)) + ")\n",
        encoding="utf-8",
    )
    fake_curl.chmod(0o755)
    script = (
        Path(__file__).resolve().parents[1]
        / "examples"
        / "build_target"
        / "serve"
        / "cage-check"
    )
    env = dict(os.environ)
    env["PATH"] = f"{fake_bin}:{env['PATH']}"

    result = subprocess.run(
        ["bash", str(script)],
        capture_output=True,
        text=True,
        env=env,
        timeout=10,
    )

    assert result.returncode == 1
    assert "probe_failure: menu-banner service=challenge" in result.stdout
    assert "Connection refused" in result.stdout


@pytest.mark.parametrize(
    "transient_failure",
    ["validator_busy", "host_runtime_network_exhausted"],
)
def test_cage_check_cli_retries_transient_validator_failure_without_exposing_json(
    tmp_path: Path,
    transient_failure: str,
) -> None:
    busy_payload = {
        "passed": False,
        "failure_class": transient_failure,
        "retryable": True,
        "evidence": {"attempt_consumed": False},
    }
    final_payload = {
        "passed": True,
        "validated_rehost_tier": "R5",
        "check_count": 1,
    }
    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    state = tmp_path / "curl-count"
    fake_curl = fake_bin / "curl"
    fake_curl.write_text(
        "#!/usr/bin/env python3\n"
        "import json, os\n"
        "from pathlib import Path\n"
        "state = Path(os.environ['FAKE_CURL_STATE'])\n"
        "count = int(state.read_text() if state.exists() else '0') + 1\n"
        "state.write_text(str(count))\n"
        f"busy = {busy_payload!r}\n"
        f"final = {final_payload!r}\n"
        "print(json.dumps(busy if count <= 2 else final))\n",
        encoding="utf-8",
    )
    fake_curl.chmod(0o755)
    fake_sleep = fake_bin / "sleep"
    fake_sleep.write_text("#!/usr/bin/env bash\nexit 0\n", encoding="utf-8")
    fake_sleep.chmod(0o755)
    script = (
        Path(__file__).resolve().parents[1]
        / "examples"
        / "build_target"
        / "serve"
        / "cage-check"
    )
    env = dict(os.environ)
    env.update(
        {
            "PATH": f"{fake_bin}:{env['PATH']}",
            "FAKE_CURL_STATE": str(state),
            "CAGE_CHECK_BUSY_RETRY_SECONDS": "1",
            "CAGE_CHECK_BUSY_MAX_RETRIES": "3",
        }
    )

    result = subprocess.run(
        ["bash", str(script), "--json"],
        capture_output=True,
        text=True,
        env=env,
        timeout=10,
    )

    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout) == final_payload
    assert state.read_text(encoding="utf-8") == "3"
    assert result.stderr.count(f"validator transient {transient_failure}; retry") == 2


def test_probe_field_aliases_are_accepted() -> None:
    # TCP steps: `send`/`expect` are accepted as `send_text`/`expect_contains`.
    probes = normalize_runtime_probes(
        [
            {
                "id": "menu",
                "type": "tcp",
                "service": "challenge",
                "steps": [{"send": "1\n", "expect": "Choice"}],
                "evidence": [{"path": "solve.py", "basis": "solve waits for the prompt"}],
            }
        ],
        target_services=["challenge"],
        target_ports={"challenge": 1337},
        target_protocols={"challenge": "tcp"},
        required=True,
    )
    step = probes[0]["steps"][0]
    assert step["expect_contains"] == "Choice"
    assert step["send_bytes"] == b"1\n"

    # HTTP: `body_contains` is accepted as `expect_body_contains`.
    hprobes = normalize_runtime_probes(
        [
            {
                "id": "home",
                "type": "http",
                "service": "web",
                "path": "/",
                "body_contains": "Welcome",
                "evidence": [{"path": "wp.md", "basis": "writeup names the page"}],
            }
        ],
        target_services=["web"],
        target_ports={"web": 80},
        target_protocols={"web": "http"},
        required=True,
    )
    assert hprobes[0]["expect_body_contains"] == "Welcome"


def test_missing_tcp_step_content_names_accepted_fields() -> None:
    with pytest.raises(ProbeContractError, match="send_text.*send_base64.*expect_contains"):
        normalize_runtime_probes(
            [
                {
                    "id": "empty",
                    "type": "tcp",
                    "service": "challenge",
                    "steps": [{"note": "no send or expect here"}],
                    "evidence": [{"path": "solve.py", "basis": "x"}],
                }
            ],
            target_services=["challenge"],
            target_ports={"challenge": 1337},
            target_protocols={"challenge": "tcp"},
            required=True,
        )
