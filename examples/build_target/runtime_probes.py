"""Host-side semantic runtime probes for the BuildTarget benchmark.

The probe contract is intentionally small and declarative.  Agents may derive
it from supplied challenge evidence, but they do not execute or grade it.  The
BuildTarget scorer resolves the target container address and runs these probes
from the host after an isolated Compose boot.
"""

from __future__ import annotations

import base64
import http.client
import socket
import ssl
import time
from typing import Any

RUNTIME_PROBE_SCHEMA_VERSION = "cage-build-target-runtime-probes-v1"
_MAX_PROBES = 8
_MAX_STEPS = 12
_MAX_RESPONSE_BYTES = 64 * 1024
_ALLOWED_HTTP_METHODS = {"GET", "HEAD", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"}


class ProbeContractError(ValueError):
    """A runtime probe is missing, ambiguous, or mechanically unsafe."""

    def __init__(self, message: str, *, evidence: dict[str, Any] | None = None) -> None:
        super().__init__(message)
        self.evidence = evidence or {}


def _bounded_int(
    value: Any,
    *,
    field: str,
    default: int,
    minimum: int,
    maximum: int,
) -> int:
    if value in (None, ""):
        return default
    try:
        normalized = int(value)
    except (TypeError, ValueError) as exc:
        raise ProbeContractError(f"{field} must be an integer") from exc
    if normalized < minimum or normalized > maximum:
        raise ProbeContractError(
            f"{field} must be between {minimum} and {maximum}"
        )
    return normalized


def _meaningful_expectation(value: Any, *, field: str) -> str:
    text = str(value or "")
    if len(text.strip()) < 3:
        raise ProbeContractError(
            f"{field} must contain at least three non-whitespace characters"
        )
    return text


def _normalize_evidence(value: Any, *, probe_id: str) -> list[dict[str, str]]:
    if not isinstance(value, list) or not value:
        raise ProbeContractError(
            f"runtime probe {probe_id!r} must cite at least one supplied evidence file"
        )
    normalized: list[dict[str, str]] = []
    for index, entry in enumerate(value):
        if not isinstance(entry, dict):
            raise ProbeContractError(
                f"runtime probe {probe_id!r} evidence[{index}] must be an object"
            )
        path = str(entry.get("path") or "").strip()
        basis = str(entry.get("basis") or "").strip()
        if not path or not basis:
            raise ProbeContractError(
                f"runtime probe {probe_id!r} evidence[{index}] needs path and basis"
            )
        normalized.append({"path": path, "basis": basis})
    return normalized


def _first_present(source: dict[str, Any], *keys: str) -> Any:
    """Return the first key whose value is not None, tolerating field aliases.

    Models reach for short, natural probe field names (``send``/``expect``) even
    when the canonical schema uses ``send_text``/``expect_contains``. Accepting
    the common aliases keeps an agent from burning its whole validation budget
    fighting field-name errors before the build is ever attempted.
    """

    for key in keys:
        if source.get(key) is not None:
            return source.get(key)
    return None


def _normalize_http_probe(raw: dict[str, Any], *, probe_id: str) -> dict[str, Any]:
    method = str(raw.get("method") or "GET").strip().upper()
    if method not in _ALLOWED_HTTP_METHODS:
        raise ProbeContractError(
            f"runtime probe {probe_id!r} uses unsupported HTTP method {method!r}"
        )
    path = str(raw.get("path") or "/").strip()
    if not path.startswith("/") or "\r" in path or "\n" in path:
        raise ProbeContractError(
            f"runtime probe {probe_id!r} HTTP path must start with '/'"
        )
    headers_raw = raw.get("headers") or {}
    if not isinstance(headers_raw, dict):
        raise ProbeContractError(
            f"runtime probe {probe_id!r} headers must be an object"
        )
    headers: dict[str, str] = {}
    for key, value in headers_raw.items():
        name = str(key).strip()
        rendered = str(value)
        if not name or "\r" in name or "\n" in name or "\r" in rendered or "\n" in rendered:
            raise ProbeContractError(
                f"runtime probe {probe_id!r} contains an invalid HTTP header"
            )
        headers[name] = rendered

    expect_value = _first_present(
        raw, "expect_body_contains", "body_contains", "expect", "contains"
    )
    if expect_value is None:
        raise ProbeContractError(
            f"runtime probe {probe_id!r} must set expect_body_contains — the "
            "response substring to assert (aliases body_contains/expect/contains "
            "are also accepted)"
        )
    expected = _meaningful_expectation(
        expect_value,
        field=f"runtime probe {probe_id!r} expect_body_contains",
    )
    expect_status = _bounded_int(
        raw.get("expect_status"),
        field=f"runtime probe {probe_id!r} expect_status",
        default=200,
        minimum=100,
        maximum=599,
    )
    return {
        "method": method,
        "path": path,
        "headers": headers,
        "body": str(raw.get("body") or ""),
        "expect_status": expect_status,
        "expect_body_contains": expected,
    }


def _normalize_tcp_probe(raw: dict[str, Any], *, probe_id: str) -> dict[str, Any]:
    steps_raw = raw.get("steps")
    if steps_raw is None:
        steps_raw = [
            {
                "send_text": _first_present(raw, "send_text", "send"),
                "send_base64": raw.get("send_base64"),
                "expect_contains": _first_present(
                    raw, "expect_contains", "expect", "contains"
                ),
            }
        ]
    if not isinstance(steps_raw, list) or not steps_raw or len(steps_raw) > _MAX_STEPS:
        raise ProbeContractError(
            f"runtime probe {probe_id!r} steps must contain 1-{_MAX_STEPS} entries"
        )

    normalized_steps: list[dict[str, Any]] = []
    expectation_count = 0
    for index, step in enumerate(steps_raw):
        if not isinstance(step, dict):
            raise ProbeContractError(
                f"runtime probe {probe_id!r} steps[{index}] must be an object"
            )
        send_text = _first_present(step, "send_text", "send")
        send_base64 = step.get("send_base64")
        if send_text is not None and send_base64 is not None:
            raise ProbeContractError(
                f"runtime probe {probe_id!r} steps[{index}] cannot set both send_text and send_base64"
            )
        encoded: bytes | None = None
        send_kind: str | None = None
        rendered_send: str | None = None
        if send_text is not None:
            rendered_send = str(send_text)
            encoded = rendered_send.encode("utf-8")
            send_kind = "text"
        elif send_base64 is not None:
            rendered_send = str(send_base64)
            try:
                encoded = base64.b64decode(rendered_send, validate=True)
            except (ValueError, TypeError) as exc:
                raise ProbeContractError(
                    f"runtime probe {probe_id!r} steps[{index}] send_base64 is invalid"
                ) from exc
            send_kind = "base64"

        expect_raw = _first_present(step, "expect_contains", "expect", "contains")
        expected = None
        if expect_raw is not None:
            expected = _meaningful_expectation(
                expect_raw,
                field=f"runtime probe {probe_id!r} steps[{index}] expect_contains",
            )
            expectation_count += 1
        if encoded is None and expected is None:
            raise ProbeContractError(
                f"runtime probe {probe_id!r} steps[{index}] needs at least one of "
                "send_text (alias send), send_base64, or expect_contains (alias "
                "expect/contains)"
            )
        normalized_steps.append(
            {
                "send_kind": send_kind,
                "send": rendered_send,
                "send_bytes": encoded,
                "expect_contains": expected,
            }
        )

    if expectation_count == 0:
        raise ProbeContractError(
            f"runtime probe {probe_id!r} must assert challenge-specific response content"
        )
    return {"steps": normalized_steps}


def normalize_runtime_probes(
    raw_probes: Any,
    *,
    target_services: list[str],
    target_ports: dict[str, int],
    target_protocols: dict[str, str],
    required: bool,
) -> list[dict[str, Any]]:
    """Validate and normalize the declarative probe contract."""

    if raw_probes in (None, []):
        if required:
            raise ProbeContractError(
                "R4 validation requires challenge.json.runtime_probes; port liveness is only R3"
            )
        return []
    if not isinstance(raw_probes, list) or not raw_probes or len(raw_probes) > _MAX_PROBES:
        raise ProbeContractError(
            f"challenge.json.runtime_probes must contain 1-{_MAX_PROBES} probe objects"
        )

    targets = set(target_services)
    normalized: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    covered_services: set[str] = set()
    for index, raw in enumerate(raw_probes):
        if not isinstance(raw, dict):
            raise ProbeContractError(f"runtime_probes[{index}] must be an object")
        probe_id = str(raw.get("id") or f"probe-{index + 1}").strip()
        if not probe_id or probe_id in seen_ids:
            raise ProbeContractError("runtime probe ids must be non-empty and unique")
        seen_ids.add(probe_id)
        service = str(raw.get("service") or "").strip()
        if service not in targets:
            raise ProbeContractError(
                f"runtime probe {probe_id!r} references unknown target service {service!r}"
            )
        if service not in target_ports:
            raise ProbeContractError(
                f"runtime probe {probe_id!r} target service {service!r} has no internal port"
            )
        probe_type = str(raw.get("type") or target_protocols.get(service) or "tcp").lower()
        if probe_type == "https":
            probe_type = "http"
        if probe_type not in {"http", "tcp"}:
            raise ProbeContractError(
                f"runtime probe {probe_id!r} type must be http or tcp"
            )
        declared_protocol = str(target_protocols.get(service) or "tcp").lower()
        if declared_protocol in {"http", "https"} and probe_type != "http":
            raise ProbeContractError(
                f"runtime probe {probe_id!r} must use an HTTP semantic probe for {declared_protocol} target"
            )

        probe = {
            "id": probe_id,
            "type": probe_type,
            "service": service,
            "timeout_seconds": _bounded_int(
                raw.get("timeout_seconds"),
                field=f"runtime probe {probe_id!r} timeout_seconds",
                default=8,
                minimum=1,
                maximum=30,
            ),
            "attempts": _bounded_int(
                raw.get("attempts"),
                field=f"runtime probe {probe_id!r} attempts",
                default=3,
                minimum=1,
                maximum=5,
            ),
            "evidence": _normalize_evidence(raw.get("evidence"), probe_id=probe_id),
        }
        if probe_type == "http":
            probe.update(_normalize_http_probe(raw, probe_id=probe_id))
            probe["tls"] = declared_protocol == "https" or bool(raw.get("tls"))
        else:
            probe.update(_normalize_tcp_probe(raw, probe_id=probe_id))
        normalized.append(probe)
        covered_services.add(service)

    if required:
        missing = sorted(targets - covered_services)
        if missing:
            raise ProbeContractError(
                "R4 validation requires at least one semantic probe for every target service",
                evidence={"missing_target_services": missing},
            )
    return normalized


def _excerpt(data: bytes, limit: int = 1200) -> str:
    rendered = data.decode("utf-8", errors="replace")
    if len(rendered) <= limit:
        return rendered
    return rendered[:limit] + "\n...[truncated]"


def _run_http_probe(probe: dict[str, Any], *, host: str, port: int) -> dict[str, Any]:
    timeout = int(probe["timeout_seconds"])
    connection_cls = http.client.HTTPSConnection if probe.get("tls") else http.client.HTTPConnection
    kwargs: dict[str, Any] = {"timeout": timeout}
    if probe.get("tls"):
        kwargs["context"] = ssl._create_unverified_context()  # noqa: SLF001 - isolated target
    connection = connection_cls(host, port, **kwargs)
    try:
        connection.request(
            probe["method"],
            probe["path"],
            body=probe.get("body") or None,
            headers=probe.get("headers") or {},
        )
        response = connection.getresponse()
        body = response.read(_MAX_RESPONSE_BYTES + 1)
        truncated = len(body) > _MAX_RESPONSE_BYTES
        if truncated:
            body = body[:_MAX_RESPONSE_BYTES]
        expected_status = int(probe["expect_status"])
        expected_body = str(probe["expect_body_contains"])
        decoded = body.decode("utf-8", errors="replace")
        assertions = {
            "status": {
                "expected": expected_status,
                "actual": response.status,
                "passed": response.status == expected_status,
            },
            "body_contains": {
                "expected": expected_body,
                "passed": expected_body in decoded,
            },
        }
        passed = all(item["passed"] for item in assertions.values())
        return {
            "passed": passed,
            "request": {
                "method": probe["method"],
                "path": probe["path"],
            },
            "response": {
                "status": response.status,
                "reason": response.reason,
                "body_excerpt": _excerpt(body),
                "truncated": truncated,
            },
            "assertions": assertions,
        }
    finally:
        connection.close()


def _run_tcp_probe(probe: dict[str, Any], *, host: str, port: int) -> dict[str, Any]:
    timeout = int(probe["timeout_seconds"])
    pending = b""
    step_results: list[dict[str, Any]] = []
    with socket.create_connection((host, port), timeout=timeout) as sock:
        sock.settimeout(min(1.0, timeout))
        for index, step in enumerate(probe["steps"]):
            sent = step.get("send_bytes")
            if sent is not None:
                sock.sendall(sent)
            expected_text = step.get("expect_contains")
            expected = expected_text.encode("utf-8") if expected_text is not None else None
            deadline = time.monotonic() + timeout
            matched = expected is None
            observed = b""
            if expected is not None:
                while expected not in pending and len(pending) < _MAX_RESPONSE_BYTES:
                    remaining = deadline - time.monotonic()
                    if remaining <= 0:
                        break
                    sock.settimeout(min(1.0, remaining))
                    try:
                        chunk = sock.recv(min(4096, _MAX_RESPONSE_BYTES - len(pending)))
                    except TimeoutError:
                        continue
                    if not chunk:
                        break
                    pending += chunk
                matched = expected in pending
                if matched:
                    end = pending.index(expected) + len(expected)
                    observed = pending[:end]
                    pending = pending[end:]
                else:
                    observed = pending
            step_results.append(
                {
                    "index": index,
                    "sent": (
                        {"kind": step.get("send_kind"), "value": step.get("send")}
                        if sent is not None
                        else None
                    ),
                    "expect_contains": expected_text,
                    "matched": matched,
                    "response_excerpt": _excerpt(observed),
                }
            )
            if not matched:
                return {"passed": False, "steps": step_results}
    return {"passed": True, "steps": step_results}


def execute_runtime_probes(
    probes: list[dict[str, Any]],
    *,
    targets: list[dict[str, Any]],
) -> dict[str, Any]:
    """Execute normalized probes against resolved target container addresses."""

    target_map = {str(target.get("service_name")): target for target in targets}
    results: list[dict[str, Any]] = []
    for probe in probes:
        target = target_map.get(probe["service"]) or {}
        host = str(target.get("container_addr") or "")
        port = target.get("internal_port")
        probe_result: dict[str, Any] = {
            "id": probe["id"],
            "type": probe["type"],
            "service": probe["service"],
            "target": {"container_addr": host or None, "internal_port": port},
            "source_evidence": probe.get("evidence") or [],
            "content_anchor": probe.get("content_anchor"),
            "attempts": [],
            "passed": False,
        }
        if not host or port is None:
            probe_result["error"] = "validator could not resolve the target address and port"
            results.append(probe_result)
            continue

        for attempt in range(1, int(probe["attempts"]) + 1):
            started = time.monotonic()
            try:
                if probe["type"] == "http":
                    detail = _run_http_probe(probe, host=host, port=int(port))
                else:
                    detail = _run_tcp_probe(probe, host=host, port=int(port))
            except (OSError, http.client.HTTPException) as exc:
                detail = {"passed": False, "error": f"{type(exc).__name__}: {exc}"}
            detail["attempt"] = attempt
            detail["duration_ms"] = round((time.monotonic() - started) * 1000, 1)
            probe_result["attempts"].append(detail)
            if detail.get("passed"):
                probe_result["passed"] = True
                probe_result["successful_attempt"] = attempt
                break
            if attempt < int(probe["attempts"]):
                time.sleep(1)
        results.append(probe_result)

    return {
        "schema_version": RUNTIME_PROBE_SCHEMA_VERSION,
        "passed": bool(results) and all(result.get("passed") for result in results),
        "probe_count": len(results),
        "probes": results,
    }
