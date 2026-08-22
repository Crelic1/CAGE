# The network proxy that agent + range containers reach the outside through.
#
# It is NOT an agent image and no benchmark ships it — it is host-side
# infrastructure, brought up once per machine by scripts/agent_netproxy.py.
#
# Deliberately minimal: the agent can never open a connection TO this container
# (see the INPUT policy in the entrypoint), so its only attack surface is the
# traffic it forwards. Every package here widens that surface.
FROM alpine:3.20

# iproute2 for `ip addr/route`, iptables for the policy, conntrack for the
# ctstate matches, dnsmasq for the caching resolver (rule 4 in the entrypoint:
# DNS used to be the one leg that left here unproxied and uncached). No shell
# tooling beyond busybox.
RUN apk add --no-cache iptables ip6tables iproute2 conntrack-tools dnsmasq tini

COPY entrypoint.sh /usr/local/bin/cage-netproxy
RUN chmod +x /usr/local/bin/cage-netproxy

# tini reaps the mihomo child and forwards signals so `docker stop` is clean.
ENTRYPOINT ["/sbin/tini", "--", "/usr/local/bin/cage-netproxy"]
