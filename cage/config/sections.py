"""Parsed configuration sections for an experiment.

These are the cohesive value objects ``project.yml`` deserializes into — proxy,
target, execution, live-check, output, judge, and resume policy. They are plain
dataclasses with no engine dependencies, so both the loader
(:mod:`cage.config.experiment`) and the live run context
(:class:`cage.experiment.engine.run_context.ExperimentRun`) can hold them
without an import cycle.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from cage.contracts.execution import DEFAULT_UPSTREAM_REQUEST_TIMEOUT_S
from cage.models import ModelConfig


@dataclass
class JudgeConfig:
    """Judge model configuration for scoring."""

    model: ModelConfig
    temperature: float = 0.0
    max_tokens: int = 4096


@dataclass
class ProxyConfig:
    """Proxy configuration."""

    enabled: bool = True
    rewrite_system: str = ""  # template with {{ system_raw }}
    # upstream request timeout in seconds
    request_timeout: float = DEFAULT_UPSTREAM_REQUEST_TIMEOUT_S
    upstream_http_proxy: str = ""  # HTTP proxy used by the in-container upstream proxy


@dataclass
class TargetConfig:
    """Target / target_server server configuration.

    Drives the lifecycle of the target stack each trial talks to: how the
    agent attaches to the runtime network, SSH tunnelling, and per-experiment
    isolation knobs.

    Note: target_server is **always** spawned per-run by the orchestrator
    (``spawn_embedded_target_server``). Its URL is an internal runtime value
    and is not configurable from project.yml — it's set programmatically on
    the ChallengeClient after the embedded subprocess starts.
    """

    enabled: bool = True
    run_mode: str = "remote"  # 'local' | 'remote'
    # ``server_url`` is set at runtime by the orchestrator from the embedded
    # target_server's chosen port; do not write to it from yaml.
    server_url: str = ""
    use_ssh_tunnel: bool = False
    # SSH tunnelling defaults are empty — opt in via project.yml ``target.ssh:``.
    jump_host: str = ""
    jump_user: str = ""
    ssh_key_path: str = ""
    remote_bind_address: str = "127.0.0.1"
    remote_bind_port: int = 8000
    # Forbidden if set true (config resolution raises). Agents reach targets over
    # the isolated docker network, never host-published ports. Kept False-only so
    # the field still resolves for the client that reads it.
    use_external_access: bool = False
    # Empty default — set this explicitly when the agent must reach a specific
    # gateway IP instead of ``host.docker.internal``.
    host_ip_for_agent: str = ""
    network_name: str = "cage_net"
    # Embedded target_server launch limits. ``None`` means keep the server
    # default; project.yml can raise these for large compose stacks.
    startup_timeout: float | None = None
    compose_up_timeout: float | None = None
    # Per-experiment isolation policy. Passed through to target_server via the
    # ChallengeClient runtime args. Empty string = let the server pick the
    # default for the benchmark family.
    #   target_scope:  "per_agent" (default) | "per_challenge" | ""
    #   parallel_mode: ""           (default — server picks "network" for
    #                                compose-network benchmarks, "alias" otherwise)
    #                | "network"    (each agent gets its own L3 subnet)
    #                | "alias"      (agents share a network, route by alias)
    target_scope: str = "per_agent"
    parallel_mode: str = ""
    # Compose launch mode + service exposure, experiment-level defaults.
    # Empty = unset: a challenge.json that declares ``network_mode`` /
    # ``exposure_mode`` always wins (the topology may be intrinsic to whether
    # the challenge runs); only when the challenge is silent does this value
    # apply; otherwise the server picks its own default (``compose_project_local``
    # / ``host_ports``).
    #   network_mode:  "" | "compose_project_local" | "shared_external"
    #   exposure_mode: "" | "host_ports" | "internal"
    network_mode: str = ""
    exposure_mode: str = ""
    # Network-namespace isolation between the agent container and the
    # challenge's *internal* services (databases, secrets initialisers,
    # caches, …).
    #   "per_trial_bridge" (default): cage creates a per-trial bridge,
    #       connects only services flagged public by target_server
    #       (``external_port`` set), and attaches the agent only there.
    #       Internal services on the compose project's own networks stay
    #       unreachable regardless of how the adapter configured them.
    #   "per_trial_bridge_sealed": same bridge, created with ``--internal`` and
    #       ``com.docker.network.bridge.inhibit_ipv4`` so the host has NO
    #       address on it. A normal bridge makes the docker host the gateway,
    #       and an agent that dials it reaches every port the host has open
    #       (sshd, the inspector, other runs' published target ports). Sealed,
    #       the agent's netns simply has no route there. Needs Docker 26+, and
    #       it fails the trial rather than falling back to a host-reachable
    #       network. Seal the agent's BASE network too
    #       (``runtime.agent_network_mode``) or the gateway is back on that one
    #       — see scripts/agent_firewall.py --no-host-gateway.
    #   "trust_server": legacy behaviour — agent attaches to the network
    #       name returned by target_server as-is.
    agent_network_isolation: str = "per_trial_bridge"


@dataclass
class ReactiveLiveCheckConfig:
    """Configuration for agent-triggered live checks."""

    enabled: bool = True
    check_on_submit: bool = True
    check_on_9091_call: bool = True


@dataclass
class PollingLiveCheckConfig:
    """Configuration for orchestrator-driven live check polling."""

    enabled: bool = False
    interval_seconds: float = 5.0
    stop_on_success: bool = True
    # Require this many CONSECUTIVE successful polls before locking in
    # a live-success verdict. Defends against transient validator flips
    # (target slowdowns, restarts, network jitter) that briefly mark the
    # exploit as "successful" while the agent has done nothing.
    # 1 = legacy single-poll lock-in (back-compat). 2-3 is the audited
    # audited default for spurious-trigger resistance. Benchmarks can also override per-verdict
    # via :meth:`Benchmark.live_check_confirm_polls`.
    confirm_polls: int = 1


@dataclass
class LiveCheckConfig:
    """Configuration for in-container live answer checking."""

    enabled: bool = False
    max_calls: int = 3
    stop_on_success: bool = True
    reactive: ReactiveLiveCheckConfig = field(default_factory=ReactiveLiveCheckConfig)
    polling: PollingLiveCheckConfig = field(default_factory=PollingLiveCheckConfig)


@dataclass
class ExecutionConfig:
    """Execution parameters."""

    # Global cap on simultaneously in-flight trials across the whole run.
    # 0 = unlimited (no global cap); the per-agent ``max_concurrent`` still
    # applies and is the usual control.
    max_trials_global: int = 0
    # Max concurrent target stack launches/readiness waits. 1 serializes heavy
    # docker compose setup while still allowing already-ready agents to run.
    # 0 disables this separate setup cap.
    max_target_setups: int = 1
    timeout: float = 0.0  # per-trial timeout in seconds (0 = unlimited)
    on_failure: str = "continue"
    chunk_size: int | None = None
    agent_network_mode: str | None = "host"
    # One switch for "the docker host must not be reachable from this run".
    #
    # On a stock bridge the host IS the gateway of every network cage and the
    # benchmark create, and it listens on 0.0.0.0 — so a trial can dial its
    # sshd, its inspector, and the published ports of every other run. Closing
    # only the agent's own network is not enough either: an agent that takes a
    # range machine uses THAT machine's stack, which sits on the range's compose
    # networks where the host is the gateway again.
    #
    # With this on, ``cage run`` takes care of all three legs itself: it brings
    # up the egress proxy (building its image on first use), points the agent
    # containers at a network the host holds no address on, seals the per-trial
    # agent↔target bridge, and tells the target server to build the range's own
    # networks the same way. Containers are untouched — no NET_ADMIN, no proxy
    # environment variables (those would break ``http://web`` alias resolution),
    # no image changes — and egress stays ordinary all-protocol traffic.
    #
    # Needs Docker 26+. Does NOT cover a target that mounts docker.sock, runs
    # privileged, or uses network_mode: host: those bypass networking entirely.
    network_containment: bool = False
    # Path to a mihomo/clash binary handed to the egress proxy so it can reach
    # the model endpoints through ``proxy.upstream_http_proxy``. Empty ⇒ look on
    # PATH; nothing found ⇒ the proxy egresses directly, which is fine when no
    # upstream proxy is configured.
    netproxy_mihomo: str = ""
    # Servers the egress proxy's caching resolver forwards to, space separated
    # ("223.5.5.5 1.1.1.1", or "10.0.0.53#5353"). Empty ⇒ whatever the docker
    # host resolves with. This covers containers that query a resolver by
    # address; the default docker path (127.0.0.11) is served by the daemon and
    # never reaches the proxy, which is why the sidecar caches as well.
    netproxy_dns_upstream: str = ""
    # Hard memory ceiling for EACH agent container (Docker ``--memory``), as a
    # docker size string: "16g", "512m", or raw bytes. ``""`` / ``"0"`` /
    # ``"unlimited"`` removes the ceiling.
    #
    # This is a safety fuse, not a tuning knob. Without it one agent-authored
    # script can consume the whole host: an unbounded ``bytearray`` grew to
    # 70 GB and an ``np.zeros((65536, 65536))`` to 95 GB, and because neither
    # trial was over its timeout the orchestrator never looked at them — the
    # kernel OOM-killer did, after taking every other run on the box down with
    # it. cgroup enforcement is the only mechanism that acts BEFORE a
    # termination condition fires. 16g matches what the fuzzing fleet on the
    # same hosts already caps each task at, and leaves ~90x headroom over an
    # agent container's observed steady state (~170 MB).
    #
    # The cgroup kills the offending PROCESS, not the container. When that is a
    # script the agent spawned (both observed runaways were), the agent simply
    # sees exit 137 from its own Bash call and can correct course — the trial
    # runs on. Only when the agent process itself is the one reaped does the
    # trial end at 137, which ``classify_trial_termination`` already reports as
    # ``oom_killed``. Either way a too-low ceiling is visible in the run rather
    # than silently charged to the agent. This dataclass is the ONE source of
    # this default; the loader references it rather than restating a literal.
    agent_memory_limit: str = "16g"
    # Hard CPU ceiling for EACH agent container (Docker ``--cpus``), in
    # cores-worth of runtime: "8", "4.5". ``""`` / ``"0"`` / ``"unlimited"``
    # removes the ceiling.
    #
    # Same class of fuse as ``agent_memory_limit``, and needed for the same
    # reason: nothing else stops a runaway before a termination condition
    # fires. A fuzzing agent that fans out with ``-jobs=$(nproc)`` sees the
    # HOST's core count (a cgroup quota does not narrow sched_getaffinity) and
    # spawns that many spinning processes — one such trial was measured at
    # ~1970% CPU, starving the 60+ trials scheduled alongside it.
    #
    # 8 bounds any single trial to 1/8 of a 64-core host while still leaving
    # real fuzzing parallelism. Note this caps a trial's PEAK, not the fleet's
    # total: N concurrent trials can still oversubscribe the box, so the ceiling
    # is a fairness guarantee between trials rather than a substitute for
    # sizing ``max_concurrent`` to the host. This dataclass is the ONE source of
    # this default; the loader references it rather than restating a literal.
    agent_cpu_limit: str = "8"
    # Config space: "unlimited" (the default; no round cap) | -1 (use the
    # benchmark sample default) | 0 (no rounds) | N. Resolved by
    # resolve_max_rounds(); an unlimited budget needs another stop condition.
    max_rounds: int | str | None = "unlimited"
    # Graceful wrap-up before the hard round cap. ``wrapup_before`` = how many
    # rounds before ``max_rounds`` the in-container proxy starts injecting the
    # wrap-up reminder, so the agent finalizes its deliverable instead of being
    # hard-stopped (429) at the cap. Offset (not absolute) so it tracks whatever
    # ``max_rounds`` resolves to. None/<=0, or a message-less benchmark, disables
    # it. The reminder text usually comes from the benchmark sample; set
    # ``wrapup_message`` here only to override per-run. Resolved by
    # resolve_wrapup(); needs a finite ``max_rounds`` to have anything to offset.
    wrapup_before: int | None = None
    wrapup_message: str | None = None
    max_input_tokens: int | None = None
    max_output_tokens: int | None = None
    max_cost: float | None = None
    # Keep proxy.jsonl (the trial's full LLM-call log — the inspector/trajectory
    # views depend on it) after the trial ends. Default on. This dataclass is the
    # ONE source of this default; the loader references it rather than restating a
    # literal (see cage/config/experiment.py).
    store_proxy: bool = True
    # Poll self-hosted (vllm/sglang) model endpoints until they answer before
    # starting — for remotely-launched servers with unknown boot time. The CLI
    # ``--wait-for-model`` flag overrides this. ``wait_timeout`` of 0 waits
    # indefinitely.
    wait_for_model: bool = False
    wait_timeout: float = 0.0
    wait_interval: float = 10.0
    live_check: LiveCheckConfig = field(default_factory=LiveCheckConfig)
    # Number of independent attempts per sample. >1 turns the run into a
    # pass@k evaluation: the trial sequence is replayed k times in
    # ``[pass1 over all samples, pass2 over all samples, ...]`` order, so a
    # full pass completes before the next pass begins (even under
    # parallelism — passes are batched).
    passk: int = 1
    # Per-invocation execution cap: run only trials whose global index is
    # ``< max_trial`` this run, leaving the rest pending. Trials are ordered
    # pass-major (pass_1 over all samples, then pass_2, …), so e.g. with 24
    # samples ``max_trial=48`` runs pass_1+pass_2 and defers pass_3. Unlike
    # lowering ``passk``, this does NOT shrink the recorded trial plan, so
    # ``--resume`` stays plan-compatible and a later capless run finishes the
    # remainder. ``None`` = no cap. Also handy as a quota throttle.
    max_trial: int | None = None


@dataclass
class OutputConfig:
    """Controls what goes into dashboard.json and results.csv.

    All flags default to True (full output). Set to False in project.yml
    ``output:`` section to exclude heavy fields.

    Example project.yml::

        output:
          dashboard_prompt: false
          dashboard_output: false
          dashboard_reasoning: false
          csv_prompt: false
          csv_output: false
          csv_reasoning: false
    """

    dashboard_prompt: bool = True
    dashboard_output: bool = True
    dashboard_reasoning: bool = True
    csv_prompt: bool = True
    csv_output: bool = True
    csv_reasoning: bool = True


@dataclass
class ResumeKeepIf:
    """Veto thresholds for ``--resume``: a trial that is otherwise eligible to
    be re-run (failed with a retry reason / missing result) is instead KEPT
    (its prior result replays from disk) when **any** of these match its
    on-disk evidence. Empty = no veto (legacy behaviour).

    Configured under ``resume.keep_if`` in project.yml. The intent is
    "this attempt already did enough work — don't throw it away just because
    it ended on a retryable error":

        resume:
          keep_if:
            min_rounds: 100        # ran >= 100 agent rounds (progress.json)
            min_duration_s: 1800   # ran >= 30 min wall-clock (meta.timing)
            id_matches: "range-8"  # trial_id matches this regex
    """

    min_rounds: int | None = None
    min_duration_s: float | None = None
    id_matches: str | None = None

    def is_empty(self) -> bool:
        return (
            self.min_rounds is None
            and self.min_duration_s is None
            and not self.id_matches
        )
