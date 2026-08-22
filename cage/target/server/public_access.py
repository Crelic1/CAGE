"""External-access mode: serving targets to an agent that is NOT on this host.

The default deployment keeps every launched service **network-only**: no host
port at all, reachable only at its ``container_addr`` on the instance's isolated
docker bridge. That is the cheat-resistant shape — an agent joins the instance
network as a container and attacks the target as a network peer, so it cannot
discover targets (its own or another team's) by scanning localhost.

A genuinely remote agent cannot join a docker network: docker networks are
host-local. Serving it means publishing the target's entry point on the host,
and that trade is what this module models. It is **off unless the operator turns
it on** (``cage benchmark serve --public-host``), because publishing a port to
``0.0.0.0`` changes the host's listening surface and must never be a
side effect of an incoming HTTP request.

Three consequences of that trade are implemented here:

1. **Only declared entries are published.** In external-access mode a launch
   publishes exactly the services the challenge names as entry points
   (``application_service_keys`` / ``entry_services``) — the same ones the agent
   prompt names — and nothing else. Scoring sidecars and a range's inner pivot
   hosts stay off the host entirely.
2. **The advertised address is derived, not configured.** The address an agent
   should dial is whatever address it just used to reach this API, so the
   ``Host`` header is the strongest evidence available and beats any static
   guess (a cloud box cannot see its own elastic IP). ``--public-host <addr>``
   overrides for the cases derivation cannot cover — a reverse proxy or a NAT
   that forwards the API and the target ports from different addresses.
3. **The host's public address is a shared namespace.** Once entries are on
   ``0.0.0.0``, one ``nmap`` of the host lists every published instance, and
   nothing binds a published port to the agent that launched it. So concurrent
   public instances can find and interfere with each other, and the number of
   them allowed at once is capped (``--max-public-instances``, default 1).
"""
from __future__ import annotations

import re
import socket
import time
from typing import Any, Iterable, Optional

import cage.target.server.server_state as _server_state

# ``--public-host`` with no value: derive the address per request instead of
# pinning one. Stored as this literal so "mode on" and "address pinned" stay
# distinguishable in a single env var.
PUBLIC_HOST_AUTO = "auto"

# Where a rendered entry-url host came from. Returned to callers so a wrong
# address is diagnosable instead of silently wrong.
SOURCE_FLAG = "flag"
SOURCE_HOST_IP_ENV = "host_ip_env"
SOURCE_HOST_HEADER = "host_header"
SOURCE_ROUTE = "route"
SOURCE_FALLBACK = "fallback"


def external_access_enabled() -> bool:
    """True when the operator started serve with ``--public-host``."""
    return bool(str(_server_state.PUBLIC_HOST or "").strip())


def configured_public_host() -> str:
    """The pinned advertise address, or ``""`` when off or set to ``auto``."""
    value = str(_server_state.PUBLIC_HOST or "").strip()
    if not value or value.lower() == PUBLIC_HOST_AUTO:
        return ""
    return value


def max_public_instances() -> int:
    """How many host-published instances may exist at once (0 = unlimited)."""
    return max(0, int(_server_state.MAX_PUBLIC_INSTANCES or 0))


"""Addresses that mean "the same host as the serve process"."""
LOOPBACK_HOSTS = frozenset({"127.0.0.1", "::1", "localhost", ""})


def default_network_only() -> bool:
    """The ``network_only`` default for a launch that didn't specify one.

    Publishing is a property of the SERVER, not of who is calling. A
    ``--public-host`` server exists to serve agents that are off-host, so every
    launch publishes its declared entry by default — loopback callers included.
    That is safe because ``--public-host`` is only ever a *dedicated* public
    server: ``cage run`` reaches its target over the isolated docker network and
    its embedded target-server never sets ``--public-host``, so
    ``external_access_enabled()`` is False there and cage-run trials stay
    network-only. A single launch can still opt back out with
    ``?network_only=true`` (e.g. an operator smoke-testing without exposing a
    port). Neither the bearer token nor the caller's address enters into it —
    the token only gates who may call the API.
    """
    return not external_access_enabled()


def host_from_header(host_header: str) -> str:
    """Extract the hostname from a ``Host`` header value (drops the port).

    The API port is not the target port, so the port must go. IPv6 literals
    arrive bracketed (``[::1]:8000``) — return them bracketed so the result can
    be pasted straight into a URL.
    """
    value = str(host_header or "").strip()
    if not value:
        return ""
    if value.startswith("["):
        end = value.find("]")
        return value[: end + 1] if end != -1 else ""
    return value.split(":", 1)[0].strip()


def _route_source_ip() -> str:
    """The local address the kernel would use to reach off-box, or ``""``.

    UDP ``connect`` only fixes the socket's route; no packet is sent, and the
    peer (TEST-NET-1, reserved for documentation) does not need to exist.
    """
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.settimeout(0.2)
            sock.connect(("192.0.2.1", 9))
            return str(sock.getsockname()[0] or "")
    except OSError:
        return ""


def resolve_public_host(host_header: str = "") -> tuple[str, str]:
    """Resolve the address to advertise in ``entry_urls``: ``(host, source)``.

    Precedence, most explicit first:

    1. ``--public-host <addr>`` — the operator overrode derivation.
    2. ``TARGET_SERVER_HOST_IP`` — the pre-``--public-host`` env knob, honoured
       so existing deployments keep working.
    3. The request's ``Host`` header — the caller demonstrably just reached the
       server at this address, which is stronger evidence than anything the
       server can learn about itself. A LAN caller and a WAN caller therefore
       get their own correct address from one server.
    4. The default route's source address — for callers that sent no ``Host``.
    5. ``127.0.0.1``.
    """
    pinned = configured_public_host()
    if pinned:
        return pinned, SOURCE_FLAG

    legacy = str(_server_state.HOST_IP or "").strip()
    if legacy and legacy != "127.0.0.1":
        return legacy, SOURCE_HOST_IP_ENV

    from_header = host_from_header(host_header)
    # A loopback Host header (``localhost`` / ``127.0.0.1`` — e.g. an operator
    # polling /prompt from the serve host itself) is useless as an advertised
    # address: an off-host agent can't dial it. Skip it and fall to the route
    # source IP, which is the server's real reachable address. A pinned
    # ``--public-host <addr>`` (checked first, above) is the way to be exact
    # behind a proxy/NAT.
    if from_header and from_header.strip("[]").lower() not in LOOPBACK_HOSTS:
        return from_header, SOURCE_HOST_HEADER

    routed = _route_source_ip()
    if routed:
        return routed, SOURCE_ROUTE

    return "127.0.0.1", SOURCE_FALLBACK


def _attr(obj: Any, name: str) -> Any:
    """Read ``name`` off a pydantic ``ServiceInfo`` or a plain dict."""
    if isinstance(obj, dict):
        return obj.get(name)
    return getattr(obj, name, None)


def public_target_rewrites(
    services: Iterable[Any],
    entry_service_keys: Iterable[str],
    public_host: str,
) -> list[tuple[str, str]]:
    """``[(inner_authority, public_authority)]`` for every published entry.

    An instance's agent-facing addresses exist in two forms that never appear in
    the same sentence: ``prestashop:80`` (docker alias, what a co-located agent
    dials) and ``<public_host>:32101`` (host-published, what a remote agent
    dials). A challenge's prompt is written in the first form, so serving it to
    a remote agent means swapping authorities. Every inner spelling of the same
    service — service key, network alias, inner hostname, inner IP — maps to the
    same published address.
    """
    keys = {str(k) for k in entry_service_keys if k}
    rewrites: list[tuple[str, str]] = []
    for svc in services:
        name = str(_attr(svc, "service_name") or "")
        external_port = _attr(svc, "external_port")
        if not name or not external_port:
            continue
        if keys and name not in keys:
            continue
        internal_port = _attr(svc, "inner_port") or _attr(svc, "internal_port")
        if not internal_port:
            continue
        target = f"{public_host}:{int(external_port)}"
        seen: set[str] = set()
        for alias in (
            name,
            _attr(svc, "alias"),
            _attr(svc, "inner_host"),
            _attr(svc, "inner_ip"),
        ):
            alias = str(alias or "").strip()
            if not alias or alias in seen:
                continue
            seen.add(alias)
            rewrites.append((f"{alias}:{int(internal_port)}", target))
    return rewrites


def rewrite_targets_for_public_host(
    text: str,
    *,
    services: Iterable[Any],
    entry_service_keys: Iterable[str],
    public_host: str,
) -> str:
    """Rewrite inner target authorities in ``text`` to host-published ones.

    Only ``host:port`` forms are rewritten. A bare hostname is left alone on
    purpose: service keys are ordinary words (``web``, ``nginx``, ``ui``) and
    rewriting them unanchored would corrupt prose. Matches are anchored on both
    sides so ``web:80`` cannot match inside ``myweb:80`` or ``web:8080``.
    """
    if not text or not public_host:
        return text
    result = text
    for needle, replacement in public_target_rewrites(
        services, entry_service_keys, public_host
    ):
        host, _, port = needle.rpartition(":")
        pattern = re.compile(
            r"(?<![\w.-])" + re.escape(host) + ":" + re.escape(port) + r"(?!\d)"
        )
        result = pattern.sub(replacement, result)
    return result


def instance_is_public(info: dict) -> bool:
    """True when this instance holds (or is about to hold) a host-published entry.

    Deliberately says nothing about the caller's audience: an instance is public
    because a port of it is on the host, which is a fact about the instance, not
    about how whoever launched it authenticated. A token-less server publishes
    exactly the same surface as a token-guarded one.

    ``public_intent`` is stamped when the launch starts, before any port is
    allocated, so two concurrent launches cannot both pass the instance cap by
    looking at a not-yet-populated ``external_ports``.
    """
    if not isinstance(info, dict):
        return False
    return bool(info.get("public_intent") or info.get("external_ports"))


def ttl_remaining_s(info: dict) -> Optional[float]:
    """Seconds left on this instance's lease, or ``None`` when it has no TTL."""
    if not isinstance(info, dict):
        return None
    ttl = info.get("ttl_s")
    created_at = info.get("created_at")
    if not isinstance(ttl, (int, float)) or ttl <= 0:
        return None
    if not isinstance(created_at, (int, float)):
        return None
    return round(max(0.0, (created_at + float(ttl)) - time.time()), 1)


def instance_expired(info: dict) -> bool:
    remaining = ttl_remaining_s(info)
    return remaining is not None and remaining <= 0
