"""``probe_inner_service`` must never gate a UDP service on a TCP connect.

Regression for pb-postexp-range-8: under ``--public-host`` the SNMP entry
(161/udp) is host-published, and the readiness probe used to TCP-probe the
published port — a connect that can never succeed against a UDP-only service, so
the whole instance false-timed-out at launch and was torn down. ``cage run``
(network-only) was unaffected because it verifies UDP over the docker-exec path.

The invariant these tests pin: a UDP service is verified over its inner address
(best-effort, connectionless), NEVER via ``is_port_open`` (TCP-only) — whether or
not the service was host-published. Docker-free: the exec path is forced
unavailable so the tests exercise pure branch selection.
"""

from __future__ import annotations

from cage.target.server import health_probes as hp
from cage.target.server import server_state as ss
from cage.target.server.schemas import ServiceInfo


def _service(**over):
    base = dict(
        service_name="svc", alias="svc", ip="1.2.3.4", inner_ip="172.30.0.5",
        inner_host="svc", inner_port=80, internal_port=80,
        external_port=32101, external_host="0.0.0.0",
        host="0.0.0.0", port=32101, protocol="tcp",
    )
    base.update(over)
    return ServiceInfo(**base)


def _patch(monkeypatch):
    """Record TCP probes; force the docker-exec branch to be unavailable."""
    tcp_calls: list[tuple[str, int]] = []
    monkeypatch.setattr(
        hp, "is_port_open",
        lambda host, port, timeout=1.0: (tcp_calls.append((host, port)) or True),
    )

    def _no_docker():
        raise RuntimeError("no docker in unit test")

    monkeypatch.setattr(hp, "get_docker_client", _no_docker)
    return tcp_calls


def test_published_udp_entry_not_tcp_probed(monkeypatch):
    """The range-8 case: a published UDP entry is ready, not TCP-probed."""
    tcp_calls = _patch(monkeypatch)
    udp_pub = _service(protocol="udp", inner_port=161, internal_port=161,
                       external_port=32161, port=32161)
    assert hp.probe_inner_service(network_name="net", service=udp_pub) is True
    assert tcp_calls == []


def test_network_only_udp_not_tcp_probed(monkeypatch):
    """The cage-run path: a network-only UDP service is ready, not TCP-probed."""
    tcp_calls = _patch(monkeypatch)
    udp_net = _service(protocol="udp", inner_port=161, internal_port=161,
                       external_port=None, port=None)
    assert hp.probe_inner_service(network_name="net", service=udp_net) is True
    assert tcp_calls == []


def test_published_tcp_entry_still_tcp_probes_host_port(monkeypatch):
    """TCP behaviour is unchanged: a published TCP entry TCP-probes its host port."""
    tcp_calls = _patch(monkeypatch)
    tcp_pub = _service(protocol="tcp", external_port=32101, port=32101)
    assert hp.probe_inner_service(network_name="net", service=tcp_pub) is True
    assert tcp_calls == [("127.0.0.1", 32101)]


def test_published_tcp_entry_probes_configured_bind_ip(monkeypatch):
    tcp_calls = _patch(monkeypatch)
    monkeypatch.setattr(ss, "PUBLIC_BIND_IP", "10.221.20.11", raising=False)
    tcp_pub = _service(protocol="tcp", external_port=32101, port=32101)
    assert hp.probe_inner_service(network_name="net", service=tcp_pub) is True
    assert tcp_calls == [("10.221.20.11", 32101)]


def test_network_only_tcp_falls_back_to_inner_tcp(monkeypatch):
    """Network-only TCP with no exec path falls back to an inner-address TCP probe."""
    tcp_calls = _patch(monkeypatch)
    tcp_net = _service(protocol="tcp", inner_ip="172.30.0.9", inner_port=8080,
                       internal_port=8080, external_port=None, port=None)
    assert hp.probe_inner_service(network_name="net", service=tcp_net) is True
    assert tcp_calls == [("172.30.0.9", 8080)]
