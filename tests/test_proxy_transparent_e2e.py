"""End-to-end characterisation of the sidecar's transparent forward path.

These lock the wire behaviour that must survive changing HOW the sidecar talks
to upstream. Every assertion here is about what the agent sees and what lands in
``proxy.jsonl`` -- never about which HTTP library did the talking. That is the
point: they were written against the hand-rolled ``http.client`` implementation
and must pass unchanged against the httpx one.

A real upstream server and a real sidecar, over real sockets. Mocking the
transport would test the mock.
"""

from __future__ import annotations

import gzip
import json
import socket
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.request import Request, urlopen

import pytest

from cage.proxy import sidecar as container_proxy


class _Upstream(BaseHTTPRequestHandler):
    """Scripted model endpoint. ``/case/<name>`` picks the response shape."""

    # HTTP/1.0 (the default) closes after every response, which would make
    # "did the proxy reuse the connection" unanswerable.
    protocol_version = "HTTP/1.1"

    seen: list[dict] = []
    connections: set = set()

    def log_message(self, *args):  # noqa: A002
        pass

    def do_POST(self):  # noqa: N802
        # A fresh TCP connection gets a fresh source port, so this counts them.
        type(self).connections.add(self.client_address[1])
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length)
        type(self).seen.append({
            "path": self.path,
            "headers": {k.lower(): v for k, v in self.headers.items()},
            "body": body,
        })
        case = self.path.rsplit("/", 1)[-1]
        getattr(self, f"_case_{case}", self._case_plain)()

    # --- response shapes ---------------------------------------------------

    def _case_plain(self):
        payload = json.dumps({
            "id": "cmpl-1", "object": "chat.completion",
            "choices": [{"index": 0, "message": {"role": "assistant", "content": "hi"},
                         "finish_reason": "stop"}],
            "usage": {"prompt_tokens": 3, "completion_tokens": 2},
        }).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.send_header("X-Weird-Upstream-Header", "kept")
        self.end_headers()
        self.wfile.write(payload)

    def _case_gzip(self):
        raw = json.dumps({
            "id": "cmpl-gz", "object": "chat.completion",
            "choices": [{"index": 0, "message": {"role": "assistant", "content": "gz"},
                         "finish_reason": "stop"}],
            "usage": {"prompt_tokens": 1, "completion_tokens": 1},
        }).encode()
        payload = gzip.compress(raw)
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Encoding", "gzip")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def _case_error(self):
        payload = json.dumps({"error": {"message": "rate limited", "type": "rate_limit"}}).encode()
        self.send_response(429)
        self.send_header("Content-Type", "application/json")
        self.send_header("Retry-After", "7")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def _case_sse(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Cache-Control", "no-cache")
        # No Content-Length is possible for a stream; under HTTP/1.1 the close
        # is what marks its end.
        self.send_header("Connection", "close")
        self.end_headers()
        def _chunk(payload):
            return f'data: {{"id":"c1","object":"chat.completion.chunk",{payload}}}\n\n'

        chunks = [
            _chunk('"choices":[{"index":0,"delta":{"role":"assistant"}}]'),
            _chunk('"choices":[{"index":0,"delta":{"content":"he"}}]'),
            _chunk('"choices":[{"index":0,"delta":{"content":"llo"}}],'
                   '"usage":{"prompt_tokens":4,"completion_tokens":2}'),
            _chunk('"choices":[{"index":0,"delta":{},"finish_reason":"stop"}]'),
            "data: [DONE]\n\n",
        ]
        for chunk in chunks:
            self.wfile.write(chunk.encode())
            self.wfile.flush()
            time.sleep(0.05)


def _await_records(path, count, timeout=10.0):
    deadline = time.monotonic() + timeout
    while True:
        lines = path.read_text().splitlines() if path.exists() else []
        records = [json.loads(line) for line in lines if line.strip()]
        if len(records) >= count or time.monotonic() > deadline:
            return records
        time.sleep(0.02)


@pytest.fixture
def rig(tmp_path):
    """A real upstream and a real sidecar, wired together."""
    _Upstream.seen = []
    _Upstream.connections = set()
    upstream = ThreadingHTTPServer(("127.0.0.1", 0), _Upstream)
    upstream.daemon_threads = True
    threading.Thread(target=upstream.serve_forever, daemon=True).start()

    recorder = container_proxy.ProxyRecorder(tmp_path, "e2e-trial")
    proxy = container_proxy._ProxyServer(("127.0.0.1", 0), container_proxy._ProxyHandler)
    proxy.extra_headers = {}
    proxy.http_proxy = ""
    proxy.max_cost = None
    proxy.max_input_tokens = None
    proxy.max_output_tokens = None
    proxy.max_output_tokens_cap = None
    proxy.max_requests = -1  # -1 == no limit, matching run_proxy's default
    proxy.wrapup_at = None
    proxy.wrapup_message = ""
    proxy.needs_translation = False
    proxy.recorder = recorder
    proxy.request_timeout = 30.0
    proxy.system_template = ""
    proxy.trial_id = "e2e-trial"
    proxy.upstream_api_key = ""
    proxy.upstream_base_url = f"http://127.0.0.1:{upstream.server_address[1]}"
    proxy.upstream_extra_body = {}
    threading.Thread(target=proxy.serve_forever, daemon=True).start()

    yield {
        "url": f"http://127.0.0.1:{proxy.server_address[1]}",
        "upstream": _Upstream,
        # The record is written AFTER the response reaches the client, so a
        # bare read races the handler. Wait for the count instead of sleeping.
        "records": lambda n=1: _await_records(tmp_path / "proxy.jsonl", n),
    }
    proxy.shutdown()
    upstream.shutdown()


def _post(url, path, body, headers=None):
    req = Request(url + path, data=body, method="POST",
                  headers={"Content-Type": "application/json", **(headers or {})})
    resp = urlopen(req, timeout=30)
    return resp, resp.read()


def _post_exact(url, path, body, headers):
    """POST with EXACTLY these headers, so "what did the proxy add" is answerable.

    urllib and httpx both add Accept-Encoding/User-Agent of their own, which
    makes them useless for measuring what the proxy invents.
    """
    host, port = url.removeprefix("http://").split(":")
    sock = socket.create_connection((host, int(port)), timeout=30)
    lines = "".join(f"{k}: {v}\r\n" for k, v in headers.items())
    sock.sendall(
        f"POST {path} HTTP/1.1\r\nHost: {host}\r\n{lines}"
        f"Content-Length: {len(body)}\r\nConnection: close\r\n\r\n".encode() + body
    )
    out = b""
    while True:
        chunk = sock.recv(65536)
        if not chunk:
            break
        out += chunk
    sock.close()
    return out


def _post_raw_stream(url, path, body):
    """Read the response off a bare socket, timestamping each arrival.

    urllib buffers, so it cannot tell "streamed" from "sent in one lump" --
    which is the only thing this is here to measure.
    """
    host, port = url.removeprefix("http://").split(":")
    sock = socket.create_connection((host, int(port)), timeout=30)
    sock.sendall(
        f"POST {path} HTTP/1.1\r\nHost: {host}\r\n"
        f"Content-Type: application/json\r\nContent-Length: {len(body)}\r\n"
        f"Connection: close\r\n\r\n".encode() + body
    )
    arrivals = []
    while True:
        chunk = sock.recv(65536)
        if not chunk:
            break
        arrivals.append((time.monotonic(), chunk))
    sock.close()
    head, _, rest = b"".join(c for _, c in arrivals).partition(b"\r\n\r\n")
    return head.decode("latin-1"), rest, arrivals


class TestTransparentForwardWire:
    def test_plain_200_body_and_headers_pass_through_verbatim(self, rig):
        resp, body = _post(rig["url"], "/v1/case/plain", b'{"model":"m","messages":[]}')
        assert resp.status == 200
        assert json.loads(body)["id"] == "cmpl-1"
        # An upstream header the proxy knows nothing about still reaches the agent.
        assert resp.headers.get("X-Weird-Upstream-Header") == "kept"

    def test_non_200_is_forwarded_with_its_status_headers_and_body(self, rig):
        with pytest.raises(Exception) as excinfo:
            _post(rig["url"], "/v1/case/error", b'{"model":"m","messages":[]}')
        err = excinfo.value
        assert getattr(err, "code", None) == 429, "upstream status must not be rewritten"
        assert err.headers.get("Retry-After") == "7", "upstream headers must survive"
        assert json.loads(err.read())["error"]["type"] == "rate_limit"
        record = rig["records"]()[-1]
        assert record["status"] == "error"
        assert "429" in record["error"]

    def test_gzip_body_is_forwarded_compressed_and_logged_decoded(self, rig):
        resp, body = _post(rig["url"], "/v1/case/gzip", b'{"model":"m","messages":[]}')
        assert resp.headers.get("Content-Encoding") == "gzip"
        assert gzip.decompress(body)  # still gzip on the wire
        record = rig["records"]()[-1]
        # …but the recorder saw through it.
        assert record["upstream_response"]["choices"][0]["message"]["content"] == "gz"

    def test_request_headers_reach_upstream_verbatim(self, rig):
        _post(rig["url"], "/v1/case/plain", b'{"model":"m","messages":[]}',
              headers={"X-Custom-Agent-Header": "abc", "Authorization": "Bearer tok"})
        seen = rig["upstream"].seen[-1]["headers"]
        assert seen["x-custom-agent-header"] == "abc"
        assert seen["authorization"] == "Bearer tok"
        assert seen["content-length"] == str(len(b'{"model":"m","messages":[]}'))

    def test_no_headers_are_invented_on_the_agent_s_behalf(self, rig):
        """Verbatim means verbatim in both directions.

        An HTTP library left to its own devices adds Accept-Encoding, Accept,
        User-Agent and Connection. Any of those changes what the upstream sends
        back — Accept-Encoding especially, which decides whether the response
        is compressed at all. The agent's request must go out as the agent
        wrote it.
        """
        _post_exact(rig["url"], "/v1/case/plain", b'{"model":"m","messages":[]}',
                    {"Content-Type": "application/json", "X-Only-Mine": "1"})
        seen = set(rig["upstream"].seen[-1]["headers"])
        # host/content-length are structural; connection is hop-by-hop.
        invented = seen - {"host", "content-type", "content-length", "x-only-mine",
                           "connection", "accept-encoding"}
        assert not invented, f"proxy invented headers the agent never sent: {sorted(invented)}"
        assert "user-agent" not in seen, "proxy must not stamp its own User-Agent"

    def test_hop_by_hop_request_headers_are_not_relayed(self, rig):
        """They describe the agent↔proxy hop, not the proxy↔model one.

        Relaying ``Connection: close`` in particular makes the endpoint hang up
        after every call, which quietly undoes the connection pool.
        """
        _post_exact(rig["url"], "/v1/case/plain", b'{"model":"m","messages":[]}',
                    {"Content-Type": "application/json", "Keep-Alive": "timeout=5",
                     "TE": "trailers"})
        seen = rig["upstream"].seen[-1]["headers"]
        for hop in ("connection", "keep-alive", "te"):
            assert hop not in seen, f"{hop} describes our hop and must stop here"

    def test_internal_span_headers_are_recorded_but_never_forwarded(self, rig):
        _post(rig["url"], "/v1/case/plain", b'{"model":"m","messages":[]}',
              headers={"X-Cage-Node": "planner", "X-Cage-Run-Id": "r1"})
        seen = rig["upstream"].seen[-1]["headers"]
        assert "x-cage-node" not in seen
        assert rig["records"]()[-1]["cage_span"]["node"] == "planner"

    def test_sse_streams_incrementally_and_is_captured_whole(self, rig):
        head, payload, arrivals = _post_raw_stream(
            rig["url"], "/v1/case/sse", b'{"model":"m","messages":[],"stream":true}')
        assert "text/event-stream" in head
        assert payload.count(b"data:") == 5
        assert payload.rstrip().endswith(b"data: [DONE]")

        # Streaming, not buffered-then-dumped: the upstream spaces chunks 50ms
        # apart, so a pass-through delivers them over a comparable span.
        stamps = [t for t, _ in arrivals]
        assert len(arrivals) >= 2, "everything arrived in one lump — not streamed"
        assert stamps[-1] - stamps[0] > 0.05

        record = rig["records"]()[-1]
        assert record["upstream_response"]["choices"][0]["message"]["content"] == "hello"
        assert record["upstream_response"]["usage"]["prompt_tokens"] == 4

    def test_repeat_calls_reuse_one_connection(self, rig):
        """The defect this path was rebuilt to remove.

        Every model call used to open its own connection — so every call paid a
        fresh name resolution and a fresh TLS handshake, and a few seconds of
        resolver trouble became a burst of failed requests rather than a pause.
        """
        for _ in range(6):
            _post(rig["url"], "/v1/case/plain", b'{"model":"m","messages":[]}')
        rig["records"](6)
        assert len(rig["upstream"].connections) == 1, (
            f"expected keepalive to carry all 6 calls, upstream saw "
            f"{len(rig['upstream'].connections)} connections"
        )

    def test_one_record_per_call(self, rig):
        for _ in range(3):
            _post(rig["url"], "/v1/case/plain", b'{"model":"m","messages":[]}')
        assert len(rig["records"](3)) == 3
