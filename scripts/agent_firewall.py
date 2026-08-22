#!/usr/bin/env python3
"""Stand up an allowlist firewall for agent containers (host-side ops tool).

Why
---
An agent evaluated on a vulnerability-reproduction benchmark must not be able to
look the answer up. Denying the CLI's web tools (``--disallowedTools
WebFetch,WebSearch``) is a *cooperative* control: it stops the agent's own web
tools, not ``curl`` in a Bash call. Network-level enforcement is the real one.

This mirrors the upstream CyberGym firewall (``cybergym.firewall``, added in
sunblaze-ucb/cybergym 475470f "feat: add firewall through proxy"): agent
containers sit on an **internal** Docker network with no route to the internet,
so every outbound connection must go through a Squid forward proxy that only
allows an explicit allowlist — a program that ignores ``HTTP_PROXY`` does not get
out, it simply fails to connect.

    agent ──(cage-internal · no internet)──▶ squid ──(bridge)──▶ allowed dests

By default this does NOT block the Docker host itself. Containers reach the host
at the internal network's gateway, which is exactly how a benchmark's grading
service is reached. Those are host-side services under our control, not the open
internet.

Sealed mode (``--no-host-gateway``) closes that door as well: the network is
created with ``com.docker.network.bridge.inhibit_ipv4``, so the host has no
address on it and the agent's netns has no route to the host at all — not a
filter rule, a missing route ("Network unreachable" from the kernel). It also
closes the host's DNAT'd published ports, i.e. every OTHER run's target ports,
which an ``INPUT`` firewall rule would not. Squid is unaffected: it is a
container on the same L2, reached by name through docker's in-netns DNS.

    agent ──(cage-sealed · no host, no internet)──▶ squid ──(bridge)──▶ allowed

Use it for benchmarks where the agent has no business talking to the host —
AgentPentestBench, where the agent is *trying* to break out of a range. It rules
out gateway-based grading, so pair it with a benchmark that submits through the
workspace, and seal the per-trial target bridge too::

    target:
      agent_network_isolation: per_trial_bridge_sealed

Sealed mode needs Docker 26+ (the driver option) and an allowlist that covers
the model endpoint, or ``--allow-all`` when only host containment is wanted.

Sealed mode vs. ``scripts/agent_netproxy.py``: this script's sealed network has
NO gateway at all, so a container on it can reach only what squid's allowlist
permits over HTTP(S) — nothing else has a route out. ``agent_netproxy.py``
instead declares a gateway that a proxy container claims, which keeps the host
equally unreachable while giving containers ordinary all-protocol egress, and it
covers a range's own compose networks (where a compromised target would
otherwise reach the host). Prefer ``agent_netproxy.py`` for pentest ranges; this
one is the stricter option when nothing needs to leave except model calls.

``examples/cybergym/default_arvo.yml`` ships wired to it, so bring it up once per
machine before running that benchmark (the command is idempotent)::

    python3 scripts/agent_firewall.py start          # network + squid + allowlist
    python3 scripts/agent_firewall.py status         # network, gateway, squid
    python3 scripts/agent_firewall.py test github.com    # probe the policy
    python3 scripts/agent_firewall.py stop           # remove squid, keep network
    python3 scripts/agent_firewall.py stop --all     # and remove the network

Sealed mode is the same commands under a different network/container name, so
both can coexist on one machine (a cybergym run keeps its gateway-based grading
while a pentest run gets no host at all)::

    python3 scripts/agent_firewall.py --network cage-sealed \
        --container cage-sealed-proxy start --no-host-gateway \
        --subnet 172.29.0.0/16 --from-models config/models.yml
    python3 scripts/agent_firewall.py --network cage-sealed \
        --container cage-sealed-proxy test         # must say SEALED

The YAML side is three pinned values (``status`` prints them verbatim)::

    runtime:
      agent_network_mode: cage-internal              # no route to the internet
    proxy:
      upstream_http_proxy: http://cage-firewall-proxy:3128   # sidecar's egress
    eval:
      benchmark:
        grading:
          host: 172.30.0.1                           # NOT the bridge's 172.17.0.1

Only cage's sidecar is pointed at the proxy; the agent's own shell gets no proxy
environment at all, so its ``curl`` has nowhere to go.

Allowlists are plain files (one entry per line, ``#`` comments) in Squid
``dstdomain`` format — a leading dot matches the domain and all its subdomains:

* ``agent_firewall_allowlist.txt`` — committed, generic (apt, pip, public LLM
  APIs), taken from upstream CyberGym.
* ``agent_firewall_allowlist.local.txt`` / ``agent_firewall_ips.local.txt`` —
  gitignored, merged on top when present. Private model endpoints belong here;
  generate the domain half with ``--from-models config/models.yml``.
* ``--allow`` / ``--allow-ip`` — one-off additions. Endpoints reached by bare IP
  must use the IP form: ``dstdomain`` never matches an address literal.
"""

from __future__ import annotations

import argparse
import json
import re
import shlex
import subprocess
import socket
import sys
import textwrap
from pathlib import Path

NETWORK = "cage-internal"
CONTAINER = "cage-firewall-proxy"
IMAGE = "ubuntu/squid:latest"
PORT = 3128
# Pinned so the experiment YAML can hardcode the values instead of chasing
# whatever docker hands out: agents reach squid by container name (docker's
# built-in DNS on a user-defined network) and host-side services — cage's
# proxy, a benchmark's grading server — live at this gateway. Override with
# --subnet/--gateway if 172.30/16 collides on your host.
SUBNET = "172.30.0.0/16"
GATEWAY = "172.30.0.1"
CONF_PATH = "/etc/squid/squid.conf"
DOMAINS_PATH = "/etc/squid/allowed_domains.txt"
IPS_PATH = "/etc/squid/allowed_ips.txt"

# Upstream CyberGym's allowlist, kept in a file next to this script so it can be
# audited and edited without touching code.
DEFAULT_ALLOWLIST = Path(__file__).with_name("agent_firewall_allowlist.txt")
# Machine-local additions, merged on top of the default when present and
# gitignored — this is where a private model endpoint goes, so the committed
# allowlist stays generic and carries no internal hostnames. Generate the
# domain half from your model registry with `--from-models config/models.yml`.
LOCAL_ALLOWLIST = Path(__file__).with_name("agent_firewall_allowlist.local.txt")
LOCAL_IP_ALLOWLIST = Path(__file__).with_name("agent_firewall_ips.local.txt")

SQUID_CONF = """\
# --- cage agent firewall (generated by scripts/agent_firewall.py) ---
acl SSL_ports port 443
acl Safe_ports port 80 443
acl CONNECT method CONNECT

acl allowed_domains dstdomain "{domains}"
acl allowed_ips dst "{ips}"

http_access deny !Safe_ports
http_access deny CONNECT !SSL_ports
http_access allow CONNECT allowed_domains
http_access allow CONNECT allowed_ips
http_access allow allowed_domains
http_access allow allowed_ips
http_access deny all

http_port {port}
cache deny all
access_log /var/log/squid/access.log
cache_log /var/log/squid/cache.log
{parent}
"""

# --allow-all: keep the proxy as the ONLY way out (so the sealed network still
# has no host route and no direct egress) while letting any destination
# through. This is the "I only want host containment, not an answer-lookup
# block" setting, and the same shape upstream CyberGym uses for its install
# proxy.
SQUID_CONF_ALLOW_ALL = """\
# --- cage agent firewall: ALLOW-ALL (generated by scripts/agent_firewall.py) ---
acl SSL_ports port 443
acl Safe_ports port 80 443
acl CONNECT method CONNECT

http_access deny !Safe_ports
http_access deny CONNECT !SSL_ports
http_access allow all

http_port {port}
cache deny all
access_log /var/log/squid/access.log
cache_log /var/log/squid/cache.log
{parent}
"""

PARENT_CONF = """\
# All allowed traffic is forwarded to an upstream parent proxy (the host's own
# egress) instead of leaving squid directly — for networks where only that proxy
# can reach the outside.
cache_peer {host} parent {port} 0 no-query default
never_direct allow all
"""


def docker(*args: str, check: bool = True, quiet: bool = False) -> subprocess.CompletedProcess:
    cmd = ["docker", *args]
    if not quiet:
        print(f"  $ {' '.join(shlex.quote(a) for a in cmd)}", file=sys.stderr)
    return subprocess.run(cmd, capture_output=True, text=True, check=check)


def _exists(kind: str, name: str) -> bool:
    result = docker(kind, "inspect", name, check=False, quiet=True)
    return result.returncode == 0


def _inspect(kind: str, name: str) -> dict:
    result = docker(kind, "inspect", name, quiet=True)
    return json.loads(result.stdout)[0]


def _write_into(container: str, path: str, content: str) -> None:
    """Write a file inside the container without needing a bind mount."""
    subprocess.run(
        ["docker", "exec", "-i", container, "sh", "-c", f"cat > {shlex.quote(path)}"],
        input=content, text=True, check=True, capture_output=True,
    )


# Squid refuses to start on an empty acl file, so an unused list gets one entry
# that can never match: a name that cannot resolve for dstdomain, and an
# RFC 5737 documentation address (never routed) for the dst/IP acl, which only
# accepts address literals.
EMPTY_DOMAIN_ACL = "invalid.invalid"
EMPTY_IP_ACL = "192.0.2.1/32"


def _model_endpoints(paths: list[Path]) -> tuple[list[str], list[str]]:
    """Split a model registry's ``base_url`` hosts into (domains, ip literals).

    cage's own model traffic has to survive the firewall, and the endpoints are
    already declared in the registry — reading them there beats hand-copying
    hostnames into an allowlist and getting one wrong.
    """
    domains: list[str] = []
    ips: list[str] = []
    for path in paths:
        for match in re.finditer(r"base_url:\s*[\"']?([^\"'\s]+)", path.read_text(encoding="utf-8")):
            host = match.group(1).split("//")[-1].split("/")[0].split(":")[0]
            if not host or host in {"localhost", "127.0.0.1", "0.0.0.0"}:
                continue  # in-container / host-local: no route needed
            (ips if re.fullmatch(r"[\d.]+", host) else domains).append(host)
    return sorted(set(domains)), sorted(set(ips))


def _read_allowlist(
    path: Path | None, extra: list[str], *, placeholder: str, local: Path | None = None
) -> str:
    lines: list[str] = []
    if path is not None:
        lines.extend(path.read_text(encoding="utf-8").splitlines())
    if local is not None and local.is_file():
        lines.extend(local.read_text(encoding="utf-8").splitlines())
    lines.extend(extra)
    cleaned = [
        line.strip() for line in lines
        if line.strip() and not line.strip().startswith("#")
    ]
    return "\n".join(cleaned or [placeholder]) + "\n"


def network_gateway(name: str = NETWORK, *, required: bool = True) -> str:
    """The host's address on ``name``, or ``""`` when the network is sealed."""
    configs = _inspect("network", name).get("IPAM", {}).get("Config") or []
    for config in configs:
        if config.get("Gateway"):
            return str(config["Gateway"])
    if required:
        raise SystemExit(f"network {name} has no gateway")
    return ""


def proxy_ip(network: str = NETWORK, container: str = CONTAINER) -> str:
    networks = _inspect("container", container)["NetworkSettings"]["Networks"]
    return str(networks[network]["IPAddress"])


def cmd_start(args: argparse.Namespace) -> None:
    model_domains, model_ips = _model_endpoints(args.from_models)
    domains = _read_allowlist(
        args.allowlist or DEFAULT_ALLOWLIST, args.allow + model_domains,
        placeholder=EMPTY_DOMAIN_ACL, local=LOCAL_ALLOWLIST,
    )
    ips = _read_allowlist(
        args.ip_allowlist, args.allow_ip + model_ips,
        placeholder=EMPTY_IP_ACL, local=LOCAL_IP_ALLOWLIST,
    )

    if not _exists("network", args.network):
        create_argv = ["network", "create", "--internal", "--subnet", args.subnet]
        if args.no_host_gateway:
            # No host-side IPv4 on the bridge: the agent's netns never learns a
            # route to the docker host, so host services AND the host's DNAT'd
            # published ports (other runs' targets) are unreachable. Needs
            # Docker 26+; older engines reject the driver option outright.
            create_argv += ["-o", "com.docker.network.bridge.inhibit_ipv4=true"]
        else:
            create_argv += ["--gateway", args.gateway]
        create = docker(*create_argv, args.network, check=False)
        if create.returncode != 0:
            hint = ""
            if "overlaps" in create.stderr:
                hint = " — pick a free --subnet (`docker network ls -q | xargs docker network inspect --format '{{.Name}} {{range .IPAM.Config}}{{.Subnet}} {{end}}'`)"
            elif "inhibit_ipv4" in create.stderr:
                hint = " — sealed mode needs Docker 26+ for that driver option"
            raise SystemExit(f"docker network create failed: {create.stderr.strip()}{hint}")
    else:
        existing = network_gateway(args.network, required=False)
        wanted = "" if args.no_host_gateway else args.gateway
        if existing != wanted:
            raise SystemExit(
                f"network {args.network} exists with gateway "
                f"{existing or '(none — sealed)'}, not {wanted or '(none — sealed)'} "
                f"— the YAML pins this, so recreate it: "
                f"`{Path(__file__).name} stop --all --network {args.network}` then `start`"
            )
        print(f"network {args.network} already exists", file=sys.stderr)

    if _exists("container", args.container):
        docker("rm", "-f", args.container)
    # Squid needs a foot in both worlds: the internal network (where the agents
    # are) and a network with an actual route out.
    #
    # It also needs to RESOLVE what it is allowed to reach. The platform hands
    # out temporary per-deployment subdomains that live only in the host's
    # /etc/hosts (they are not in public DNS), so squid — which uses Docker's
    # resolver — cannot look them up and denies the CONNECT even though the
    # domain is allowlisted. Allowlisting the IP does not help: squid has to
    # resolve the name before it can match the destination at all. So carry the
    # host's own mapping in for exactly those names.
    host_pins: list[str] = []
    for d in domains.splitlines():
        d = d.strip().lstrip(".")
        if not d or d.startswith("#"):
            continue
        try:
            ip = socket.gethostbyname(d)
        except OSError:
            continue
        if ip not in ("127.0.0.1", "::1"):
            host_pins += ["--add-host", f"{d}:{ip}"]
    if host_pins:
        print(f"pinning {len(host_pins)//2} host entries into the proxy "
              f"(subdomains that resolve only via the host's /etc/hosts)",
              file=sys.stderr)
    docker(
        "run", "-d", "--name", args.container, "--restart", "unless-stopped",
        "--network", "bridge", *host_pins, args.image,
    )
    docker("network", "connect", args.network, args.container)

    parent = ""
    if args.parent_proxy:
        host, _, port = args.parent_proxy.rpartition(":")
        host = host.split("//")[-1]
        if not host or not port.isdigit():
            raise SystemExit(f"--parent-proxy must be host:port (got {args.parent_proxy!r})")
        parent = PARENT_CONF.format(host=host, port=port)

    _write_into(args.container, DOMAINS_PATH, domains)
    _write_into(args.container, IPS_PATH, ips)
    if args.allow_all:
        conf = SQUID_CONF_ALLOW_ALL.format(port=args.port, parent=parent)
        print("squid policy: ALLOW-ALL (allowlist files written but unused)",
              file=sys.stderr)
    else:
        conf = SQUID_CONF.format(
            domains=DOMAINS_PATH, ips=IPS_PATH, port=args.port, parent=parent,
        )
    _write_into(args.container, CONF_PATH, conf)
    check = docker("exec", args.container, "squid", "-k", "parse", check=False)
    if check.returncode != 0:
        raise SystemExit(f"squid rejected the generated config:\n{check.stderr}")
    docker("restart", args.container)
    cmd_status(args)


def cmd_status(args: argparse.Namespace) -> None:
    if not _exists("network", args.network):
        print(f"network {args.network}: ABSENT (run `start`)")
        return
    gateway = network_gateway(args.network, required=False)
    running = _exists("container", args.container) and (
        _inspect("container", args.container)["State"]["Running"]
    )
    print(f"network        {args.network} (internal, no route to the internet)")
    if gateway:
        print(f"host gateway   {gateway}   <- grading.host / host services live here")
    else:
        print("host gateway   NONE (sealed) <- the agent has no route to the "
              "docker host, its services, or its published ports")
    if not running:
        print(f"squid          {args.container}: NOT RUNNING (run `start`)")
        return
    ip = proxy_ip(args.network, args.container)
    print(f"squid          {args.container} at {ip}:{args.port} "
          f"(agents reach it by name: http://{args.container}:{args.port})")
    print()
    if gateway:
        print("the run YAML pins these (examples/cybergym/default_arvo.yml already does):")
        print(textwrap.indent(textwrap.dedent(f"""\
            runtime:
              agent_network_mode: {args.network}
            proxy:
              upstream_http_proxy: http://{args.container}:{args.port}
            eval:
              benchmark:
                grading:
                  host: {gateway}"""), "  "))
    else:
        print("the run YAML pins these (sealed: no grading.host — nothing on the "
              "host is reachable):")
        print(textwrap.indent(textwrap.dedent(f"""\
            runtime:
              agent_network_mode: {args.network}
            proxy:
              upstream_http_proxy: http://{args.container}:{args.port}
            target:
              agent_network_isolation: per_trial_bridge_sealed"""), "  "))
    counts = docker(
        "exec", args.container, "sh", "-c",
        f"wc -l < {DOMAINS_PATH}; wc -l < {IPS_PATH}", quiet=True,
    ).stdout.split()
    if len(counts) == 2:
        print(f"\nallowlist      {counts[0]} domains, {counts[1]} ip entries")


def _probe_host(network: str) -> None:
    """Report whether a container on ``network`` can reach the docker host.

    Probes every address the host could answer on: this network's own gateway
    (``docker network inspect``) and the default bridge's gateway, which is what
    ``--add-host host.docker.internal:host-gateway`` resolves to inside every
    cage agent container. ``nc`` is used rather than ``curl`` because only its
    error text separates the two outcomes that matter — "Network unreachable"
    (no route at all: sealed) from "refused"/"open" (the host answered).
    """
    addresses = []
    gateway = network_gateway(network, required=False)
    if gateway:
        addresses.append((gateway, f"{network} gateway"))
    default_gw = network_gateway("bridge", required=False)
    if default_gw and default_gw != gateway:
        addresses.append((default_gw, "host.docker.internal / default bridge"))
    if not addresses:
        print("docker host: no gateway on this network and no default bridge to probe")
        return

    script = "ip route | sed 's/^/route: /'; " + "; ".join(
        f"nc -zv -w 3 {ip} 22 2>&1 | tail -1" for ip, _ in addresses
    )
    probe = docker(
        "run", "--rm", "--network", network, "curlimages/curl:latest",
        "sh", "-c", script, check=False, quiet=True,
    )
    lines = [ln.strip() for ln in (probe.stdout + probe.stderr).splitlines() if ln.strip()]
    routes = [ln for ln in lines if ln.startswith("route: ")]
    print("docker host reachability (port 22 = sshd, the host's own service)")
    print(f"  default route  {'none — no way off this network' if not any('default' in r for r in routes) else next(r for r in routes if 'default' in r)[7:]}")
    for (ip, label), line in zip(addresses, [ln for ln in lines if not ln.startswith("route: ")]):
        lowered = line.lower()
        if "unreachable" in lowered:
            verdict = "SEALED — no route to the host"
        elif "open" in lowered or "refused" in lowered:
            verdict = "HOST REACHABLE"
        else:
            verdict = "inconclusive"
        print(f"  {ip:<15} {verdict}  ({label}: {line})")


def cmd_test(args: argparse.Namespace) -> None:
    """Probe the policy from a throwaway container on the internal network."""
    _probe_host(args.network)
    if not args.destination:
        return
    ip = proxy_ip(args.network, args.container)
    for destination in args.destination:
        url = destination if "://" in destination else f"https://{destination}"
        direct = docker(
            "run", "--rm", "--network", args.network, "curlimages/curl:latest",
            "-sS", "--max-time", "8", "-o", "/dev/null", "-w", "%{http_code}", url,
            check=False, quiet=True,
        )
        viaproxy = docker(
            "run", "--rm", "--network", args.network, "curlimages/curl:latest",
            "-sS", "--max-time", "15", "--proxy", f"http://{ip}:{args.port}",
            "-o", "/dev/null", "-w", "%{http_code}", url,
            check=False, quiet=True,
        )
        print(
            f"{url}\n"
            f"  direct     {'BLOCKED' if direct.returncode else 'REACHED ' + direct.stdout}"
            f"  (expected BLOCKED — the network has no route out)\n"
            f"  via squid  {'denied/failed' if viaproxy.returncode else 'allowed ' + viaproxy.stdout}"
        )


def cmd_stop(args: argparse.Namespace) -> None:
    if _exists("container", args.container):
        docker("rm", "-f", args.container)
    if args.all and _exists("network", args.network):
        docker("network", "rm", args.network)
    cmd_status(args)


def main() -> None:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--network", default=NETWORK)
    parser.add_argument("--container", default=CONTAINER)
    parser.add_argument("--image", default=IMAGE)
    parser.add_argument("--port", type=int, default=PORT)
    parser.add_argument("--subnet", default=SUBNET, help=f"pinned subnet (default {SUBNET})")
    parser.add_argument("--gateway", default=GATEWAY, help=f"pinned gateway = where host services live (default {GATEWAY})")
    sub = parser.add_subparsers(dest="command", required=True)

    start = sub.add_parser("start", help="create the internal network + squid")
    start.add_argument("--allowlist", type=Path, help=f"domain allowlist file (default {DEFAULT_ALLOWLIST.name})")
    start.add_argument("--allow", action="append", default=[], help="extra allowed domain (repeatable; '.x.com' = subdomains)")
    start.add_argument("--ip-allowlist", type=Path, help="ip/CIDR allowlist file")
    start.add_argument("--allow-ip", action="append", default=[], help="extra allowed ip/CIDR (repeatable) — for endpoints reached by address")
    start.add_argument("--from-models", action="append", default=[], type=Path, metavar="MODELS_YML",
                       help="allow every base_url host in a cage model registry (e.g. config/models.yml)")
    start.add_argument("--parent-proxy", help="forward allowed traffic to this host:port instead of going out directly")
    start.add_argument("--no-host-gateway", action="store_true",
                       help="sealed mode: create the network with no host address, so the agent "
                            "has no route to the docker host or its published ports (Docker 26+). "
                            "Rules out gateway-based grading; pair with "
                            "target.agent_network_isolation: per_trial_bridge_sealed")
    start.add_argument("--allow-all", action="store_true",
                       help="let squid forward to ANY destination (host containment only, no "
                            "answer-lookup block) — the allowlist files are ignored")
    start.set_defaults(func=cmd_start)

    status = sub.add_parser("status", help="show network, gateway, squid ip + the YAML to paste")
    status.set_defaults(func=cmd_status)

    test = sub.add_parser("test", help="probe: host must be unreachable in sealed mode, "
                                       "direct egress must fail, via-squid must match the policy")
    test.add_argument("destination", nargs="*")
    test.set_defaults(func=cmd_test)

    stop = sub.add_parser("stop", help="remove the squid container")
    stop.add_argument("--all", action="store_true", help="also remove the internal network")
    stop.set_defaults(func=cmd_stop)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
