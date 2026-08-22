#!/bin/sh
# cage network proxy — the only way out for agent and range containers.
#
# Topology it assumes (created by scripts/agent_netproxy.py and by cage when it
# launches a range):
#
#     docker network create --subnet 10.90.1.0/24 --gateway 10.90.1.1 \
#         -o com.docker.network.bridge.inhibit_ipv4=true <net>
#
# ``inhibit_ipv4`` means the host does NOT get an address on that bridge, so the
# host is not on the network at all — but docker still hands every container
# ``default via 10.90.1.1``. This container takes that gateway address, so the
# containers' egress lands here with zero changes on their side: no NET_ADMIN,
# no proxy environment variables (which would break docker alias resolution like
# ``http://web``), no route commands, no image changes.
#
# Three rules this file exists to enforce. Each one was learned by getting it
# wrong first:
#
#   1. DENY BELONGS IN iptables, NEVER IN THE PROXY'S RULES. A transparent proxy
#      accepts the TCP connection before it consults any policy, so a "reject"
#      expressed in mihomo still completes the handshake — every scanned port
#      comes back open and the agent's recon is all false positives. Anything
#      that must not go through is dropped here, before the redirect.
#
#   2. THE DESTINATION MUST STAY A REAL IP. No fake-ip, no sniffer in the mihomo
#      config. With fake-ip the proxy forwards a *hostname* upstream, and a
#      request for ``<host-ip>.nip.io`` makes the upstream resolve it and
#      connect to the host on the agent's behalf. Keeping real IPs means the
#      iptables rules below see the true destination and are the single point
#      where "may this leave" is decided.
#
#   3. PACKETS ADDRESSED TO US ARE NOT REDIRECTED (``--dst-type LOCAL``).
#      Without that RETURN, the blanket REDIRECT swallows traffic aimed at the
#      gateway itself and every one of its 65535 ports answers — the loudest
#      possible thing to put in front of a scanning agent.
#
#   4. DNS IS A LEG OF ITS OWN AND HAS TO BE CAUGHT SEPARATELY. The redirect
#      above is ``-p tcp``, so UDP/53 used to fall straight through to
#      MASQUERADE: a name resolved as plain UDP out the raw egress while the
#      traffic that followed went through the upstream proxy. Port 53 is now
#      caught and answered by a caching resolver here (dnsmasq), forwarding
#      real answers — no fake-ip, no rewriting — so rule 2 still holds.
#
#      What this does and does not cover, measured rather than assumed: it
#      catches queries a container sends to a resolver ADDRESS (a target with
#      8.8.8.8 in its resolv.conf, a tool with a nameserver compiled in). It
#      does NOT catch the default path, because docker puts 127.0.0.11 in
#      resolv.conf and its embedded resolver forwards from the daemon's own
#      namespace, not through this gateway — verified by zeroing the counter
#      on the rule below and watching it stay at zero. Do not "fix" that by
#      pointing containers here with --dns: the host holds no address on these
#      networks (inhibit_ipv4), so the daemon could not reach us, and the
#      embedded resolver is also what makes ``http://web`` resolve to a range
#      service. The per-call query storm on that path is solved where it is
#      generated instead — see the DNS cache in cage/proxy/sidecar.py.
#
# Everything is reconciled in a loop rather than configured once: networks are
# attached over the container's lifetime (cage connects it to each range network
# at launch), and a container restart wipes both the addresses and the rules.
set -eu

REDIR_PORT="${REDIR_PORT:-7892}"
# Short on purpose. cage attaches this container to a range's networks right
# after ``compose up``, and until the gateway address is claimed the range's own
# services stall on ARP for anything they try to reach. The loop is a handful of
# ip/iptables calls and the policy is only re-applied when it actually changed.
RECONCILE_INTERVAL="${RECONCILE_INTERVAL:-2}"
MIHOMO_CONFIG="${MIHOMO_CONFIG:-/etc/mihomo/config.yaml}"

# Destinations that must never be reachable from behind this proxy. The host
# owns an address in several of these (bridge gateways, LAN, tailscale), and
# enumerating the host's addresses would be a list to keep in sync — denying
# private space wholesale is the version that cannot drift. 169.254/16 covers
# cloud metadata services.
PRIVATE_NETS="${PRIVATE_NETS:-10.0.0.0/8 172.16.0.0/12 192.168.0.0/16 100.64.0.0/10 169.254.0.0/16}"

# Carve-outs from PRIVATE_NETS: model endpoints on the internal network, an
# internal DNS resolver, anything else the trial legitimately needs.
#
# Read from a FILE on every cycle, not fixed at startup. This proxy is shared by
# every run on the machine, and each run has its own model endpoints — a run
# that starts later must be able to add its own without restarting the proxy and
# cutting the network out from under the runs already going. The env var seeds
# the file on first boot.
ALLOW_NETS_FILE="${ALLOW_NETS_FILE:-/etc/cage-netproxy/allow_nets}"
ALLOW_NETS_SEED="${ALLOW_NETS:-}"

read_allow_nets() {
    _acc="$ALLOW_NETS_SEED"
    if [ -f "$ALLOW_NETS_FILE" ]; then
        _acc="$_acc $(grep -vE '^\s*(#|$)' "$ALLOW_NETS_FILE" | tr '\n' ' ')"
    fi
    echo "$_acc" | tr ' ' '\n' | grep -v '^$' | sort -u | tr '\n' ' '
}

# The caching resolver (rule 4). cage fills DNS_UPSTREAM in with the docker
# host's real nameservers; the point is the cache and the single choke point,
# not a different provider. Falling back to this container's own resolv.conf is
# the last resort and often does not work: docker writes 127.0.0.11 there and
# the resolver behind it is not running in a container created on the default
# bridge — which is why the probe below exists.
#
# Carried in a FILE for the same reason the allow-list is: one proxy serves
# every run on the machine, so a run starting later must be able to change this
# without a restart that would cut the network out from under runs in flight.
# The env var only seeds first boot.
DNS_CACHE="${DNS_CACHE:-1}"
DNS_UPSTREAM_FILE="${DNS_UPSTREAM_FILE:-/etc/cage-netproxy/dns_upstream}"
DNS_UPSTREAM_SEED="${DNS_UPSTREAM:-}"
DNS_CACHE_SIZE="${DNS_CACHE_SIZE:-10000}"

# Normalised through awk so the seed and the file compare equal when they say
# the same thing: the restart below triggers on any difference, and a stray
# trailing space is not a difference worth restarting a live resolver for.
read_dns_upstream() {
    if [ -f "$DNS_UPSTREAM_FILE" ]; then
        _raw="$(grep -vE '^\s*(#|$)' "$DNS_UPSTREAM_FILE" | tr '\n' ' ')"
    else
        _raw="$DNS_UPSTREAM_SEED"
    fi
    echo "$_raw" | awk '{$1=$1; print}'
}
# A resolver that accepts queries and cannot answer them is worse than no
# resolver: the redirect sends every lookup into a hole. So it has to prove it
# resolves before the rules point at it, and keep proving it — measured against
# a name, because the failure mode we hit was a live dnsmasq with a dead
# forwarder. Failing the probe stops the process, which drops the redirect and
# puts DNS back on the path it took before.
DNS_PROBE_NAME="${DNS_PROBE_NAME:-example.com}"
DNS_PROBE_EVERY="${DNS_PROBE_EVERY:-30}"
# CDN endpoints hand out 5-30s TTLs. Honouring them literally is what turned
# name resolution into per-call traffic; a floor costs nothing here because a
# trial runs for minutes against one endpoint.
DNS_MIN_TTL="${DNS_MIN_TTL:-120}"

# Conntrack. A scanning agent opens thousands of flows that never complete, each
# holding a table entry in SYN_SENT for two minutes by default. A full table
# means dropped packets, and UDP dies first because nothing retransmits it.
# We cannot raise the ceiling from in here — docker mounts /proc/sys read-only
# and the per-netns conntrack knobs do not exist yet at container init, so
# --sysctl is refused too. So we watch it and say so, with the command that
# fixes it on the host. Silence would just look like a flaky endpoint.
CONNTRACK_WARN_PCT="${CONNTRACK_WARN_PCT:-70}"

# Fail closed. When an upstream proxy is configured, egress that does NOT go
# through it is not "degraded", it is wrong: the destination is unreachable
# without the proxy, so the connection hangs and dies mid-TLS instead of failing
# honestly.
#
# DERIVED, never configured. mihomo's own config already says whether traffic is
# supposed to go through an upstream, so asking it is always current. A startup
# env var would go stale the moment a second run shares this proxy — the same
# startup-only-channel mistake the allow-list above had to be rescued from.
require_proxy() {
    [ -f "$MIHOMO_CONFIG" ] && grep -q 'MATCH,upstream' "$MIHOMO_CONFIG" 2>/dev/null
}

log() { echo "[cage-netproxy] $*"; }

# The interface with the default route is the way out; everything else is a
# network we are the gateway for. Deriving it beats naming interfaces, which
# depend on the order docker attached them.
outer_iface() { ip route show default 2>/dev/null | awk '{print $5; exit}'; }

inner_ifaces() {
    _out="$(outer_iface)"
    ip -4 -o addr show scope global 2>/dev/null | awk '{print $2}' | sort -u | while read -r i; do
        [ "$i" = "$_out" ] || [ "$i" = "lo" ] || echo "$i"
    done
}

# The gateway address of an interface's subnet: the first usable address.
# cage and the range compose files both declare ``.1``; a network that pins a
# different gateway can override it by writing "<iface> <addr>" lines into
# /etc/cage-netproxy/gateways (survives restarts, read every reconcile).
gateway_for() {
    _if="$1"; _cidr="$2"
    if [ -f /etc/cage-netproxy/gateways ]; then
        _pin="$(awk -v i="$_if" '$1 == i {print $2; exit}' /etc/cage-netproxy/gateways)"
        [ -n "$_pin" ] && { echo "$_pin"; return; }
    fi
    echo "$_cidr" | awk -F'[./]' '{print $1"."$2"."$3".1"}'
}

claim_gateway_addresses() {
    for IF in $(inner_ifaces); do
        CIDR="$(ip -4 -o addr show dev "$IF" scope global | awk '{print $4}' | head -1)"
        [ -n "$CIDR" ] || continue
        PREFIX="${CIDR#*/}"
        GW="$(gateway_for "$IF" "$CIDR")"
        if ! ip -4 -o addr show dev "$IF" | grep -q " ${GW}/"; then
            ip addr add "${GW}/${PREFIX}" dev "$IF" 2>/dev/null \
                && log "claimed gateway ${GW}/${PREFIX} on ${IF}"
        fi
    done
}

# Rendered wholesale and applied with iptables-restore so the policy switches
# atomically. Rebuilding a chain in place would leave a window with no rules,
# and a window with no rules is a window where the host is reachable.
# Redirecting to a port nothing listens on turns every outbound connection into
# "connection refused" — worse than having no proxy at all. So the redirect
# rules are emitted only while mihomo is actually up; without it the container
# still NATs straight out, which is right for destinations reachable directly.
redirect_available() {
    [ -f "$MIHOMO_CONFIG" ] && command -v mihomo >/dev/null 2>&1 && pgrep mihomo >/dev/null 2>&1
}

# Same reasoning for DNS: a redirect to a dead resolver is worse than no
# redirect, because every lookup then fails instantly with "connection refused"
# instead of going where it used to go.
dns_available() {
    [ "$DNS_CACHE" = "1" ] && command -v dnsmasq >/dev/null 2>&1 \
        && pgrep dnsmasq >/dev/null 2>&1
}

render_rules() {
    OUT="$(outer_iface)"
    INNERS="$(inner_ifaces)"
    # Networks we are the gateway for: containers behind us must keep reaching
    # each other (agent → target is the actual benchmark). Derived from our own
    # interfaces, so a newly attached range network is covered automatically.
    MYNETS="$(ip -4 -o addr show scope global | awk '{print $4}' \
        | sed 's|\.[0-9]*/|.0/|' | sort -u | grep -v '^172\.17\.' || true)"

    echo "*nat"
    echo ":PREROUTING ACCEPT [0:0]"
    echo ":INPUT ACCEPT [0:0]"
    echo ":OUTPUT ACCEPT [0:0]"
    echo ":POSTROUTING ACCEPT [0:0]"
    for IN in $INNERS; do
        # (3) traffic aimed at us is never redirected — it falls through to the
        #     INPUT drop below and the gateway reads as "no open ports".
        echo "-A PREROUTING -i $IN -m addrtype --dst-type LOCAL -j RETURN"
        # (4) DNS in transit is answered here instead. Deliberately AFTER the
        #     LOCAL RETURN so the gateway itself still reads as closed to a
        #     scan: what gets caught is a query a container addresses to a
        #     resolver out there, not the docker-embedded path (see rule 4 in
        #     the header for why that one does not come past us at all).
        if dns_available; then
            echo "-A PREROUTING -i $IN -p udp --dport 53 -j REDIRECT --to-ports 53"
            echo "-A PREROUTING -i $IN -p tcp --dport 53 -j REDIRECT --to-ports 53"
        fi
        if redirect_available; then
            # Allowed internal destinations go through the proxy like anything else.
            for N in $ALLOW_NETS; do
                echo "-A PREROUTING -i $IN -d $N -p tcp -j REDIRECT --to-ports $REDIR_PORT"
            done
            # (1) the rest of private space is not redirected, so it hits the
            #     FORWARD drop and fails at the handshake, the way a filtered
            #     destination should.
            for N in $PRIVATE_NETS; do
                echo "-A PREROUTING -i $IN -d $N -j RETURN"
            done
            echo "-A PREROUTING -i $IN -p tcp -j REDIRECT --to-ports $REDIR_PORT"
        fi
    done
    [ -n "$OUT" ] && echo "-A POSTROUTING -o $OUT -j MASQUERADE"
    echo "COMMIT"

    echo "*filter"
    echo ":INPUT ACCEPT [0:0]"
    echo ":FORWARD ACCEPT [0:0]"
    echo ":OUTPUT ACCEPT [0:0]"
    for IN in $INNERS; do
        for N in $MYNETS;      do echo "-A FORWARD -i $IN -d $N -j ACCEPT"; done
        for N in $ALLOW_NETS;  do echo "-A FORWARD -i $IN -d $N -j ACCEPT"; done
        for N in $PRIVATE_NETS; do echo "-A FORWARD -i $IN -d $N -j DROP"; done
        # Fail closed: with an upstream configured but no proxy to reach it
        # through, anything still being forwarded is leaving by the wrong door.
        # Dropping it is loud; letting it out is a connection that hangs and
        # dies mid-stream, which reads as a flaky endpoint. Range traffic was
        # accepted above, so the benchmark itself is unaffected, and DNS is
        # redirected to us rather than forwarded so lookups keep working.
        [ "${FAIL_CLOSED:-0}" = "1" ] && echo "-A FORWARD -i $IN -j DROP"
        # Only connections we redirected (DNAT) or already established may be
        # delivered locally. A scan, a ping, a direct dial of the redirect port:
        # all dropped.
        echo "-A INPUT -i $IN -m conntrack --ctstate DNAT,ESTABLISHED,RELATED -j ACCEPT"
        echo "-A INPUT -i $IN -j DROP"
    done
    echo "COMMIT"
}

apply_rules() {
    # Read once per cycle HERE, in the parent shell. render_rules runs inside a
    # command substitution — a subshell — so anything it assigns is lost the
    # moment it returns, and `set -u` then kills the container when the log line
    # below reads it. Assigning in the parent means both see the same value.
    ALLOW_NETS="$(read_allow_nets)"
    # Computed here, not inside render_rules: that function's stdout IS the
    # ruleset, so anything it logs would be fed to iptables-restore.
    if require_proxy && ! redirect_available; then
        FAIL_CLOSED=1
    else
        FAIL_CLOSED=0
    fi
    _new="$(render_rules)"
    _sig="$(echo "$_new" | md5sum | awk '{print $1}')"
    if [ "${_sig}" != "${LAST_SIG:-}" ]; then
        echo "$_new" | iptables-restore
        LAST_SIG="$_sig"
        log "policy applied (inner=$(inner_ifaces | tr '\n' ' ')allow='${ALLOW_NETS}' dns=$(dns_available && echo cached || echo passthrough))"
        # An `[ … ] && log` here would make this function return non-zero on the
        # common path, and `set -e` would take the whole container down with it.
        if [ "$FAIL_CLOSED" = "1" ]; then
            log "FAIL CLOSED: an upstream proxy is required but mihomo is not running — external egress is DROPPED until it comes back"
        fi
    fi
}

start_mihomo_if_configured() {
    # Without mihomo the proxy still works, it just NATs straight out: fine for
    # destinations reachable directly, no use for ones that need the upstream.
    # The redirect port having no listener is what breaks in that case, so the
    # redirect rules are only meaningful while this is running — hence the
    # restart-on-exit.
    [ -f "$MIHOMO_CONFIG" ] || return 0
    command -v mihomo >/dev/null 2>&1 || return 0
    pgrep mihomo >/dev/null 2>&1 && return 0
    mihomo -d "$(dirname "$MIHOMO_CONFIG")" -f "$MIHOMO_CONFIG" >/var/log/mihomo.log 2>&1 &
    log "started mihomo"
}

start_dnsmasq_if_enabled() {
    # Restarted from the loop for the same reason as mihomo: the DNS redirect
    # rules are only emitted while this is up, so a crash degrades to the old
    # pass-through behaviour instead of black-holing every lookup.
    [ "$DNS_CACHE" = "1" ] || return 0
    command -v dnsmasq >/dev/null 2>&1 || return 0
    pgrep dnsmasq >/dev/null 2>&1 && return 0

    # --bind-dynamic picks up range networks as they are attached, and
    # --except-interface=lo keeps us off 127.0.0.11, where docker's own
    # embedded resolver listens — binding that would fail to start AND take
    # away the resolver we forward to.
    _upstream="$(read_dns_upstream)"
    set -- --keep-in-foreground --bind-dynamic --except-interface=lo \
        --cache-size="$DNS_CACHE_SIZE" --min-cache-ttl="$DNS_MIN_TTL" \
        --neg-ttl=5 --dns-forward-max=1000 --no-hosts --log-facility=/var/log/dnsmasq.log
    if [ -n "$_upstream" ]; then
        set -- "$@" --no-resolv
        for S in $_upstream; do set -- "$@" --server="$S"; done
    fi
    dnsmasq "$@" >>/var/log/dnsmasq.log 2>&1 &
    # Give it a moment to bind before probing it.
    sleep 1
    if ! pgrep dnsmasq >/dev/null 2>&1; then
        log "dnsmasq failed to start — DNS stays on the raw pass-through path (see /var/log/dnsmasq.log)"
        return 0
    fi
    if dns_answers; then
        DNS_UPSTREAM_APPLIED="$_upstream"
        log "started dnsmasq (cache=${DNS_CACHE_SIZE} min-ttl=${DNS_MIN_TTL}s upstream=${_upstream:-resolv.conf})"
    else
        pkill dnsmasq 2>/dev/null || true
        log "dnsmasq started but could not resolve ${DNS_PROBE_NAME} via '${_upstream:-resolv.conf}' — stopped it rather than redirect DNS into a hole; lookups keep taking the path they took before"
    fi
}

# dnsmasq reads its servers once, at exec time, so a changed upstream only takes
# effect on a restart. Stopping it is enough: the loop starts it again with the
# new list, and the redirect rules follow dns_available down and back up.
restart_dnsmasq_if_upstream_changed() {
    dns_available || return 0
    _want="$(read_dns_upstream)"
    [ "$_want" = "${DNS_UPSTREAM_APPLIED:-}" ] && return 0
    log "dns upstream changed ('${DNS_UPSTREAM_APPLIED:-}' -> '${_want}') — restarting dnsmasq"
    pkill dnsmasq 2>/dev/null || true
}

# Ask the resolver for a real name on one of our own addresses. Loopback is not
# usable for this: dnsmasq deliberately does not bind lo (docker's embedded
# resolver lives at 127.0.0.11), so the probe uses the first global address.
dns_answers() {
    _addr="$(ip -4 -o addr show scope global 2>/dev/null | awk '{print $4}' \
        | cut -d/ -f1 | head -1)"
    [ -n "$_addr" ] || return 1
    nslookup "$DNS_PROBE_NAME" "$_addr" >/dev/null 2>&1
}

# Re-probed on a slow cadence: an upstream that dies mid-run has to take the
# redirect down with it, and the counter keeps that off the 2-second path.
recheck_dns_health() {
    dns_available || return 0
    DNS_TICKS=$(( ${DNS_TICKS:-0} + 1 ))
    [ "$DNS_TICKS" -ge "$DNS_PROBE_EVERY" ] || return 0
    DNS_TICKS=0
    if ! dns_answers; then
        pkill dnsmasq 2>/dev/null || true
        log "dnsmasq stopped answering for ${DNS_PROBE_NAME} — stopping it so the DNS redirect comes down; it will be restarted and re-probed"
    fi
}

CT_COUNT=/proc/sys/net/netfilter/nf_conntrack_count
CT_MAX=/proc/sys/net/netfilter/nf_conntrack_max

# Logged only when the bucket changes, so a busy run does not print this every
# two seconds — and so crossing the threshold is a visible event, not a wall.
check_conntrack() {
    [ -r "$CT_COUNT" ] && [ -r "$CT_MAX" ] || return 0
    _c="$(cat "$CT_COUNT" 2>/dev/null || echo 0)"
    _m="$(cat "$CT_MAX" 2>/dev/null || echo 0)"
    [ "$_m" -gt 0 ] 2>/dev/null || return 0
    _pct=$(( _c * 100 / _m ))
    [ "$_pct" -ge "$CONNTRACK_WARN_PCT" ] || { CT_BUCKET=""; return 0; }
    _bucket=$(( _pct / 10 ))
    [ "$_bucket" = "${CT_BUCKET:-}" ] && return 0
    CT_BUCKET="$_bucket"
    log "conntrack ${_c}/${_m} (${_pct}%) in this namespace — at 100% the kernel drops packets and UDP goes first. On the DOCKER HOST: sysctl -w net.netfilter.nf_conntrack_max=$(( _m * 2 )) net.netfilter.nf_conntrack_tcp_timeout_syn_sent=20"
}

log "starting (redir=${REDIR_PORT} interval=${RECONCILE_INTERVAL}s)"
sysctl -w net.ipv4.ip_forward=1 >/dev/null 2>&1 || true
# IPv6 would bypass every v4 rule above. Refuse to forward it rather than
# maintaining a parallel ruleset.
sysctl -w net.ipv6.conf.all.forwarding=0 >/dev/null 2>&1 || true
ip6tables -P FORWARD DROP 2>/dev/null || true

while :; do
    claim_gateway_addresses
    start_mihomo_if_configured
    restart_dnsmasq_if_upstream_changed
    start_dnsmasq_if_enabled
    recheck_dns_health
    apply_rules
    check_conntrack
    sleep "$RECONCILE_INTERVAL"
done
