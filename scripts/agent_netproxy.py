#!/usr/bin/env python3
"""Operate the egress proxy that keeps the docker host off agent networks.

``cage run`` manages this by itself when the experiment sets::

    runtime:
      network_containment: true

so this script is for the manual side of it: inspecting what is running,
probing the policy from outside a run, and tearing it down. The logic lives in
``cage.sandbox.netproxy`` — this is a CLI over it, not a second implementation.

    python3 scripts/agent_netproxy.py up          # same thing cage run does
    python3 scripts/agent_netproxy.py status      # state + bypass probes
    python3 scripts/agent_netproxy.py attach NET  # put it on another network
    python3 scripts/agent_netproxy.py down

Why any of this exists: a docker bridge makes the host the gateway of every
network, and the host listens on 0.0.0.0 — so a trial can dial its sshd, its
inspector, and every other run's published ports. Networks created here declare
a gateway the host does not occupy (``inhibit_ipv4``); this proxy claims that
address and is the only way out. Containers need no changes at all.
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from cage.sandbox import netproxy  # noqa: E402

PROBE_IMAGE = "curlimages/curl:latest"
_IPV4 = re.compile(r"\b\d{1,3}(?:\.\d{1,3}){3}\b")


def _probe(network: str, script: str) -> str:
    result = subprocess.run(
        ["docker", "run", "--rm", "--network", network, PROBE_IMAGE, "sh", "-c", script],
        capture_output=True, text=True, stdin=subprocess.DEVNULL, timeout=120.0,
    )
    return (result.stdout + result.stderr).strip()


def _has_upstream() -> bool:
    """Whether the running proxy was given an upstream to forward through."""
    result = subprocess.run(
        ["docker", "exec", netproxy.CONTAINER, "sh", "-c",
         "grep -q 'MATCH,upstream' /etc/mihomo/config.yaml 2>/dev/null && echo yes"],
        capture_output=True, text=True, timeout=30.0,
    )
    return "yes" in result.stdout


def cmd_up(args: argparse.Namespace) -> None:
    netproxy.ensure_running(
        upstream=args.upstream,
        mihomo=args.mihomo,
        allow_nets=args.allow_net,
        network=args.network,
    )
    cmd_status(args)


def cmd_attach(args: argparse.Namespace) -> None:
    for network in args.network_name:
        print(f"{network}: {'attached' if netproxy.attach(network) else 'FAILED'}")


def cmd_down(args: argparse.Namespace) -> None:
    subprocess.run(["docker", "rm", "-f", netproxy.CONTAINER], capture_output=True)
    if args.all:
        subprocess.run(["docker", "network", "rm", args.network], capture_output=True)
    print("down")


def cmd_status(args: argparse.Namespace) -> None:
    host_on = netproxy.host_holds_address_on(args.network)
    if host_on is None:
        print(f"network        {args.network}: ABSENT (run `up`)")
        return
    print(f"network        {args.network}")
    print(f"host on it     {'YES — NOT ISOLATED' if host_on else 'no (inhibit_ipv4)'}")
    if not netproxy.is_serving(network=args.network):
        print(f"proxy          {netproxy.CONTAINER}: NOT RUNNING (run `up`)")
        return
    nets = subprocess.run(
        ["docker", "inspect", "-f",
         "{{range $k, $v := .NetworkSettings.Networks}}{{$k}} {{end}}", netproxy.CONTAINER],
        capture_output=True, text=True,
    ).stdout.strip()
    print(f"proxy          {netproxy.CONTAINER} on {nets}")

    if args.no_probe:
        return
    gateway = subprocess.run(
        ["docker", "network", "inspect", args.network,
         "--format", "{{range .IPAM.Config}}{{.Gateway}}{{end}}"],
        capture_output=True, text=True,
    ).stdout.strip()
    print("\nself-check (from a throwaway container on the network):")
    checks = [
        ("egress: cn", "curl -sS -m 15 -o /dev/null -w '%{http_code}' https://www.baidu.com",
         lambda o: o.endswith(("200", "302")), "reachable"),
        # Only meaningful when an upstream proxy was configured: without one the
        # proxy egresses directly, and a blocked destination failing is correct.
        *([("egress: intl", "curl -sS -m 20 -o /dev/null -w '%{http_code}' https://www.google.com",
            lambda o: o.endswith(("200", "302")), "reachable via upstream")]
          if _has_upstream() else []),
        # ``getent`` and not ``nslookup``: nslookup prints an empty second
        # answer section for the AAAA lookup, so the last two lines carry no
        # address and this reported a failure while resolution was fine. It
        # also echoes the resolver's own address, which a laxer match would
        # have accepted as proof of an answer that never came.
        ("dns", "getent hosts github.com", lambda o: bool(_IPV4.search(o)), "resolves"),
        ("host: gateway", "nc -zv -w 3 172.17.0.1 22 2>&1 | tail -1",
         lambda o: "open" not in o.lower(), "blocked"),
        ("proxy: ping", f"ping -c1 -W2 {gateway} 2>&1 | tail -1",
         lambda o: "0 packets received" in o or "100% packet loss" in o, "silent"),
        ("proxy: ports", f"nc -zv -w 2 {gateway} {netproxy.REDIR_PORT} 2>&1 | tail -1",
         lambda o: "open" not in o.lower(), "filtered"),
        # The SSRF that a fake-ip / sniffer configuration would open: the
        # upstream resolving a hostname that points back at the host.
        ("ssrf: nip.io", "nc -zv -w 4 172.17.0.1.nip.io 22 2>&1 | tail -1",
         lambda o: "open" not in o.lower(), "blocked"),
    ]
    failures = 0
    for name, script, ok, expect in checks:
        out = _probe(args.network, script)
        passed = ok(out)
        failures += 0 if passed else 1
        tail = out.splitlines()[-1][:66] if out else "(empty)"
        print(f"  [{'PASS' if passed else 'FAIL'}] {name:<15} expect {expect:<28} got: {tail}")
    if failures:
        raise SystemExit(f"{failures} check(s) failed")


def main() -> None:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--network", default=netproxy.NETWORK)
    sub = parser.add_subparsers(dest="command", required=True)

    up = sub.add_parser("up", help="build the image if needed, create the network, start the proxy")
    up.add_argument("--upstream", default="", help="upstream HTTP proxy host:port")
    up.add_argument("--mihomo", default="", help="mihomo binary to copy in (default: search PATH)")
    up.add_argument("--allow-net", action="append", default=[], metavar="CIDR",
                    help="private destination to permit (model endpoints, internal DNS)")
    up.add_argument("--no-probe", action="store_true")
    up.set_defaults(func=cmd_up)

    attach = sub.add_parser("attach", help="put the proxy on another network")
    attach.add_argument("network_name", nargs="+")
    attach.set_defaults(func=cmd_attach)

    status = sub.add_parser("status", help="state + self-check probes")
    status.add_argument("--no-probe", action="store_true")
    status.set_defaults(func=cmd_status)

    down = sub.add_parser("down", help="remove the proxy container")
    down.add_argument("--all", action="store_true", help="also remove the network")
    down.add_argument("--no-probe", action="store_true")
    down.set_defaults(func=cmd_down)

    args = parser.parse_args()
    if not hasattr(args, "no_probe"):
        args.no_probe = True
    try:
        args.func(args)
    except netproxy.NetproxyError as exc:
        raise SystemExit(f"netproxy: {exc}")


if __name__ == "__main__":
    main()
