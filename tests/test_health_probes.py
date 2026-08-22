from __future__ import annotations

from types import SimpleNamespace

from cage.target.server import health_probes as hp
from cage.target.server.schemas import ServiceInfo


def _service() -> ServiceInfo:
    return ServiceInfo(
        service_name="web",
        alias="web",
        ip="172.31.1.2",
        inner_ip="172.31.1.2",
        inner_port=80,
        internal_port=80,
        external_port=None,
    )


def test_inner_probe_tries_nc_after_bash_probe_failure(monkeypatch):
    calls = []

    class Container:
        labels = {"com.docker.compose.service": "web"}

        def exec_run(self, command, demux=False):
            calls.append(command)
            return (1, b"") if command[0] == "bash" else (0, b"")

    client = SimpleNamespace(
        containers=SimpleNamespace(list=lambda filters: [Container()])
    )
    monkeypatch.setattr(hp, "get_docker_client", lambda: client)

    assert hp.probe_inner_service(network_name="net", service=_service()) is True
    assert [command[0] for command in calls] == ["bash", "sh"]


def test_inner_probe_falls_back_to_host_tcp(monkeypatch):
    class Container:
        labels = {"com.docker.compose.service": "web"}

        def exec_run(self, command, demux=False):
            return 1, b""

    client = SimpleNamespace(
        containers=SimpleNamespace(list=lambda filters: [Container()])
    )
    monkeypatch.setattr(hp, "get_docker_client", lambda: client)
    monkeypatch.setattr(
        hp,
        "is_port_open",
        lambda host, port, timeout: host == "172.31.1.2" and port == 80,
    )

    assert hp.probe_inner_service(network_name="net", service=_service()) is True
