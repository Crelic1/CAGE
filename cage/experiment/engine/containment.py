"""Turn ``runtime.network_containment`` into the three things it actually means.

The user-facing knob is one boolean. Behind it sit three separate legs, each of
which is a different network the docker host would otherwise be the gateway of:

    1. the agent container's base network       → runtime.agent_network_mode
    2. the per-trial agent↔target bridge        → target.agent_network_isolation
    3. the range's own compose networks         → the target server's environment

Leaving any one of them open makes the other two decorative: an agent that
cannot dial the host directly simply takes a range machine and dials from there.
So this module sets all three from the single switch, after making sure the
egress proxy those networks route to is actually running.
"""

from __future__ import annotations

import ipaddress
import logging
import socket
from typing import Any
from urllib.parse import urlparse

from cage.sandbox import netproxy

logger = logging.getLogger("cage.experiment.containment")

# Passed to the embedded target server so it builds the range's own networks
# with the host off them and attaches the proxy after ``compose up``.
TARGET_SERVER_ENV = "TARGET_SERVER_HOST_OFF_NETWORKS"


def model_endpoint_cidrs(config: Any) -> list[str]:
    """Private addresses the trial must still reach: the model endpoints.

    The proxy denies private space wholesale — that is how "the host" is denied
    without enumerating the host's addresses — so endpoints on the internal
    network have to be carved out by address. Reading them off the resolved
    agents is more accurate than re-parsing the registry: it sees exactly the
    models this run will use.
    """
    hosts: set[str] = set()
    for agent in getattr(config, "agents", []) or []:
        sources = getattr(agent, "model_sources", None) or [getattr(agent, "model", None)]
        for model in sources:
            base_url = str(getattr(model, "base_url", "") or "")
            hostname = urlparse(base_url).hostname if base_url else None
            if hostname:
                hosts.add(hostname)

    cidrs: set[str] = set()
    for hostname in sorted(hosts):
        if hostname in {"localhost", "127.0.0.1", "0.0.0.0"}:
            continue  # in-container / host-local: no route needed
        try:
            address = socket.gethostbyname(hostname)
        except OSError:
            logger.warning(
                "containment: could not resolve model endpoint %s — if it is on "
                "the internal network the trial will not reach it", hostname,
            )
            continue
        if ipaddress.ip_address(address).is_private:
            cidrs.add(f"{address}/32")
    return sorted(cidrs)


def apply_network_containment(config: Any) -> dict[str, Any] | None:
    """Bring the proxy up and rewrite the three switches.

    Returns a summary of what was actually done (``None`` when the switch is
    off) so the CLI can print the specifics — which network, which proxy, which
    private destinations stayed reachable. "Containment is on" on its own is not
    checkable by the person reading it; the addresses are.

    Called before preflight so the checks see the same networking the trials
    will get. Raises :class:`~cage.sandbox.netproxy.NetproxyError` rather than
    quietly continuing — a run that believes it is contained and is not is worse
    than one that refuses to start.
    """
    if not getattr(config.execution, "network_containment", False):
        return None

    from cage.target.provisioning import SEALED_TRIAL_BRIDGE

    upstream = str(getattr(config.proxy, "upstream_http_proxy", "") or "")
    allow_nets = model_endpoint_cidrs(config)
    netproxy.ensure_running(
        upstream=upstream,
        mihomo=str(getattr(config.execution, "netproxy_mihomo", "") or ""),
        allow_nets=allow_nets,
        dns_upstream=str(getattr(config.execution, "netproxy_dns_upstream", "") or ""),
    )

    config.execution.agent_network_mode = netproxy.NETWORK
    if getattr(config, "target", None) is not None:
        config.target.agent_network_isolation = SEALED_TRIAL_BRIDGE

    if upstream:
        # The upstream proxy runs on the host, which the agent container can no
        # longer reach — and must not, or the containment is void. It is the
        # egress proxy's upstream now (set above), so the in-container sidecar
        # must stop pointing at it: its traffic leaves through the same gateway
        # as everything else.
        config.proxy.upstream_http_proxy = ""
        logger.info(
            "containment: %s is now the egress proxy's upstream; the sidecar "
            "egresses through the network gateway instead", upstream,
        )

    return {
        "network": netproxy.NETWORK,
        "proxy": netproxy.CONTAINER,
        "upstream": upstream,
        "allow_nets": allow_nets,
        "target_enabled": bool(getattr(getattr(config, "target", None), "enabled", False)),
        # A proxy left running from an earlier version serves that version's
        # policy. Reported rather than fixed: it is shared with runs in flight.
        "stale_proxy": netproxy.running_image() if netproxy.stale() else "",
        "image": netproxy.IMAGE,
    }


def target_server_env(config: Any) -> dict[str, str]:
    """Environment for the embedded target server (leg 3)."""
    if not getattr(config.execution, "network_containment", False):
        return {}
    return {TARGET_SERVER_ENV: "1"}
