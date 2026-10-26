"""Network debug payload + entry-url construction for a launched challenge."""
from __future__ import annotations

import ipaddress
import re
import urllib.parse
from typing import Any, Dict, List

from cage.target.server.network_admin import list_project_containers
from cage.target.server.schemas import EntryUrl, ServiceInfo
from cage.target.server.server_state import get_docker_client


def entry_url_hints_from_challenge(meta: Dict[str, Any]) -> Dict[str, str]:
    """Return agent-facing HTTP URL templates keyed by compose service name."""
    source_fields = meta.get("source_fields", {}) or {}
    agent_input = source_fields.get("agent_input") or meta.get("agent_input") or {}
    if not isinstance(agent_input, dict):
        return {}

    targets = str(agent_input.get("application_targets") or "")
    hints: Dict[str, str] = {}
    for match in re.finditer(r"https?://[^\s,]+", targets):
        candidate = match.group(0).strip()
        parsed = urllib.parse.urlsplit(candidate)
        if parsed.hostname and parsed.scheme in {"http", "https"}:
            hints[parsed.hostname] = candidate
    return hints

def build_network_debug(project_name: str, network_name: str, parallel_mode: str) -> Dict[str, Any]:
    debug: Dict[str, Any] = {
        "parallel_mode": parallel_mode,
        "network": {
            "name": network_name,
        },
    }
    try:
        network = get_docker_client().networks.get(network_name)
        attrs = getattr(network, "attrs", {}) or {}
        network_block = debug["network"]
        network_block["driver"] = attrs.get("Driver")

        ipam_config = (((attrs.get("IPAM", {}) or {}).get("Config") or [{}])[0] or {})
        subnet = str(ipam_config.get("Subnet", "") or "").strip() or None
        gateway = str(ipam_config.get("Gateway", "") or "").strip() or None
        if subnet:
            network_block["subnet"] = subnet
        if gateway:
            network_block["gateway"] = gateway
        if subnet:
            parsed = ipaddress.ip_network(subnet, strict=False)
            network_block["total_addresses"] = parsed.num_addresses
            network_block["usable_addresses"] = max(parsed.num_addresses - 2, 0)

        status_subnets = ((((attrs.get("Status", {}) or {}).get("IPAM", {}) or {}).get("Subnets", {}) or {}))
        if subnet and subnet in status_subnets:
            subnet_status = status_subnets[subnet] or {}
            network_block["ips_in_use"] = subnet_status.get("IPsInUse")
            network_block["dynamic_ips_available"] = subnet_status.get("DynamicIPsAvailable")

        services: List[Dict[str, Any]] = []
        for container in list_project_containers(project_name):
            labels = getattr(container, "labels", {}) or {}
            service_name = labels.get("com.docker.compose.service")
            if not service_name:
                continue
            try:
                container.reload()
                networks = (((container.attrs or {}).get("NetworkSettings", {}) or {}).get("Networks", {}) or {})
                network_info = networks.get(network_name)
                if not network_info:
                    continue
                ipv4 = str(network_info.get("IPAddress", "") or "").strip() or None
                mac_address = str(network_info.get("MacAddress", "") or "").strip() or None
                services.append(
                    {
                        "service_name": service_name,
                        "container_name": getattr(container, "name", None),
                        "ipv4": ipv4,
                        "mac_address": mac_address,
                    }
                )
            except Exception as exc:
                services.append({"service_name": service_name, "error": str(exc)})

        services.sort(key=lambda item: item.get("service_name", ""))
        network_block["services"] = services
    except Exception as exc:
        debug["network"]["error"] = str(exc)
    return debug


def build_container_addrs(
    services: List[ServiceInfo],
    entry_service_keys: set[str],
) -> List[str]:
    """Internal ``ip:port`` of the target services ON the docker network.

    The serve-only counterpart of :func:`_build_entry_urls`: instead of a
    host-published port, each service's address as seen from INSIDE the isolated
    network (``inner_ip:internal_port``). An external agent that has attached to
    the docker network reaches the targets here. When entry services are declared
    — web via ``application_service_keys``, post-exploitation ranges via
    ``entry_services`` — only those are listed, the internal parallel of
    ``entry_urls``: it advertises exactly the entry points the agent prompt
    names and keeps scoring sidecars / non-entry hosts out. Only a range that
    declares no entries at all falls back to listing every internal address.
    """
    addrs: List[str] = []
    for svc in services:
        if entry_service_keys and svc.service_name not in entry_service_keys:
            continue
        ip = str(getattr(svc, "inner_ip", "") or "").strip()
        port = getattr(svc, "inner_port", None) or getattr(svc, "internal_port", None)
        if ip and port:
            addrs.append(f"{ip}:{int(port)}")
    return addrs


def _build_entry_urls(
    *,
    services: List[ServiceInfo],
    entry_service_keys: set[str],
    host_ip: str,
    url_hints: Dict[str, str] | None = None,
) -> List[EntryUrl]:
    """Render published entry-service ports into client-usable URLs.

    The benchmark's agent-facing target URL wins when supplied. Otherwise,
    HTTP scheme is inferred from common web ports (80/8080/8000/8888/5000/3000
    → http, 443/8443 → https). Anything else is returned as bare ``host:port``
    so SSH/RDP/raw TCP entries still get a usable string.
    """
    if not entry_service_keys:
        return []
    urls: List[EntryUrl] = []
    for svc in services:
        if svc.service_name not in entry_service_keys:
            continue
        if not svc.external_port:
            continue
        protocol = (svc.protocol or "tcp").lower()
        internal = svc.internal_port
        hint = (url_hints or {}).get(svc.service_name)
        parsed_hint = urllib.parse.urlsplit(hint) if hint else None
        if parsed_hint is not None and parsed_hint.scheme in {"http", "https"}:
            suffix = parsed_hint.path or ""
            if parsed_hint.query:
                suffix += f"?{parsed_hint.query}"
            if parsed_hint.fragment:
                suffix += f"#{parsed_hint.fragment}"
            protocol = parsed_hint.scheme
            url = f"{protocol}://{host_ip}:{svc.external_port}{suffix}"
        elif protocol in {"http", "https"}:
            url = f"{protocol}://{host_ip}:{svc.external_port}"
        elif protocol == "tcp" and internal in {443, 8443}:
            url = f"https://{host_ip}:{svc.external_port}"
        elif protocol == "tcp" and internal in {80, 8080, 8000, 8888, 5000, 3000}:
            url = f"http://{host_ip}:{svc.external_port}"
        else:
            url = f"{host_ip}:{svc.external_port}"
        urls.append(EntryUrl(
            name=svc.service_name,
            role=svc.service_name,
            url=url,
            host=host_ip,
            port=svc.external_port,
            protocol=protocol,
        ))
    return urls
