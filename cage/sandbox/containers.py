"""Container runtime — persistent Docker container for an experiment.

Lifecycle: one container per (agent_instance, experiment_run).
The container stays alive across all trials. State isolation is
handled by snapshot/restore at trial boundaries.

Merged following capabilities:
- PersistentShell support (open_persistent_shell)
- Workspace helpers (symlink_dir_content, hardlink_dir_content, exists, mkdir)
- Static IP support on connect_network (ipv4_address param)
"""

from __future__ import annotations

import atexit
import logging
import shlex
import shutil
import socket
import subprocess
import threading
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from urllib.parse import urlparse

from cage.contracts.exceptions import ContainerError
from cage.contracts.execution import CONTAINER_PROXY_SCRIPT_NAME
from cage.sandbox.exec import ExecResult
from cage.sandbox.shell import PersistentShell

logger = logging.getLogger(__name__)

# Shared Docker hosts can serialize container creation behind long-running image
# save/build operations.  Allow ten minutes for ``docker run`` to return before
# treating startup as failed; the trial runtime timeout is configured separately.
DEFAULT_CONTAINER_START_TIMEOUT = 600.0

# Global registry of active container names that need cleanup on process exit.
# Container is a dataclass without __hash__, so we track by name (str).
_ACTIVE_CONTAINER_NAMES: set[str] = set()
_REGISTRY_LOCK = threading.Lock()

# Config spellings that mean "no ceiling". Mirrors the vocabulary
# ``contracts.execution`` uses for an unlimited round budget, so a user who
# writes ``unlimited`` in one place is not surprised by the other. Shared by
# the memory and CPU ceilings so both spell "off" the same way.
_UNLIMITED_LIMIT_TOKENS = frozenset({"", "0", "unlimited", "none", "null", "off", "-1"})


def memory_limit_is_unbounded(value: str | None) -> bool:
    """Whether a configured memory ceiling means "do not cap"."""
    return str(value or "").strip().lower() in _UNLIMITED_LIMIT_TOKENS


def cpu_limit_is_unbounded(value: str | None) -> bool:
    """Whether a configured CPU ceiling means "do not cap"."""
    return str(value or "").strip().lower() in _UNLIMITED_LIMIT_TOKENS


def _cleanup_all_containers() -> None:
    """atexit handler: force-remove any containers still alive."""
    with _REGISTRY_LOCK:
        leaked = list(_ACTIVE_CONTAINER_NAMES)
    for name in leaked:
        try:
            logger.warning("atexit cleanup: removing leaked container %s", name)
            subprocess.run(
                ["docker", "rm", "-f", name],
                capture_output=True, timeout=15,
            )
        except Exception:
            pass


atexit.register(_cleanup_all_containers)

READONLY_VOLUME_OPTIONS = {"ro", "readonly"}


def _subprocess_text(value: str | bytes | None) -> str:
    """Normalize subprocess output at the runtime boundary.

    ``TimeoutExpired.stdout``/``stderr`` may be bytes even when the original
    ``subprocess.run`` requested text mode.  Letting those bytes escape through
    ``ExecResult`` makes ordinary string checks fail with a TypeError during
    transient Docker daemon latency.
    """

    if value is None:
        return ""
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return str(value)


def _docker_bind_mount_spec(host_path: str, container_path_spec: str) -> str:
    """Build a Docker --mount bind spec.

    Unlike ``-v host:container``, ``--mount`` safely handles host paths that
    contain colons, which can happen because run directories include agent
    labels like ``agent:model:mode``.
    """
    container_path, _, options_raw = container_path_spec.partition(":")
    options = {
        option.strip().lower()
        for option in options_raw.split(",")
        if option.strip()
    }
    parts = [
        "type=bind",
        f"source={host_path}",
        f"target={container_path}",
    ]
    if options & READONLY_VOLUME_OPTIONS:
        parts.append("readonly")
    return ",".join(parts)


# ---------------------------------------------------------------------------
# URL → extra-hosts helper
# ---------------------------------------------------------------------------

def resolve_extra_hosts_for_url(url: str) -> dict[str, str]:
    """Resolve a URL hostname to a static IPv4 host mapping for containers."""
    if not url:
        return {}

    hostname = urlparse(url).hostname
    if not hostname:
        return {}

    try:
        socket.inet_aton(hostname)
        return {}
    except OSError:
        pass

    try:
        infos = socket.getaddrinfo(hostname, None, family=socket.AF_INET, type=socket.SOCK_STREAM)
    except socket.gaierror:
        logger.warning("Failed to resolve hostname on host: %s", hostname)
        return {}

    for family, _, _, _, sockaddr in infos:
        if family == socket.AF_INET and sockaddr and sockaddr[0]:
            return {hostname: sockaddr[0]}

    logger.warning("Resolved hostname %s but found no IPv4 address", hostname)
    return {}


@dataclass
class Container:
    """Manages a single Docker container for an agent experiment."""

    name: str
    image: str
    env_vars: dict[str, str] = field(default_factory=dict)
    volumes: dict[str, str] = field(default_factory=dict)  # host_path -> container_path
    extra_hosts: dict[str, str] = field(default_factory=dict)
    network_mode: str | None = None
    security_opt: list[str] = field(default_factory=list)
    cap_add: list[str] = field(default_factory=list)
    group_add: list[str] = field(default_factory=list)
    privileged: bool = False
    # Docker ``--memory`` size string ("16g", "512m", raw bytes). Empty or any
    # of ``_UNLIMITED_LIMIT_TOKENS`` leaves the container uncapped, which is
    # Docker's own default. ``--memory-swap`` is pinned to the same value so the
    # ceiling cannot be escaped through swap on a host that has some.
    memory_limit: str = ""
    # Docker ``--cpus`` value — CPU-cores-worth of runtime ("8", "4.5"). Empty
    # or any of ``_UNLIMITED_LIMIT_TOKENS`` leaves the container uncapped.
    cpu_limit: str = ""
    start_timeout: float = DEFAULT_CONTAINER_START_TIMEOUT
    labels: dict[str, str] = field(default_factory=dict)
    _started: bool = False
    _runtime_network_name: str | None = None

    @property
    def is_running(self) -> bool:
        return self._started

    # ------------------------------------------------------------------ #
    # Lifecycle
    # ------------------------------------------------------------------ #

    def start(self) -> None:
        """Start the container: docker run -d --init ... sleep infinity."""
        cmd = ["docker", "run", "-d", "--init", "--name", self.name]

        for label_key, label_value in self.labels.items():
            cmd.extend(["--label", f"{label_key}={label_value}"])

        if self.network_mode:
            cmd.extend(["--network", self.network_mode])

        # A cgroup ceiling is the only thing that can stop a runaway
        # agent-authored script BEFORE some termination condition fires — the
        # reaper (``kill_agent``) only runs once the orchestrator has decided to
        # stop the trial, and a trial that ends ``completed`` never triggers it
        # at all. Pinning ``--memory-swap`` to the same value keeps the ceiling
        # meaningful on a host with swap (Docker otherwise allows 2x).
        if not memory_limit_is_unbounded(self.memory_limit):
            limit = self.memory_limit.strip()
            cmd.extend(["--memory", limit, "--memory-swap", limit])

        # The same fuse, for CPU. Uncapped, ONE trial can take the whole host:
        # a fuzzing agent that fans out with ``-jobs=$(nproc)`` was observed
        # holding 64 processes at ~1970% CPU — 20 cores — while 60+ sibling
        # trials queued behind it. ``--cpus`` is a CFS quota, so the kernel
        # keeps placing threads on whatever cores are free; unlike
        # ``--cpuset-cpus`` it needs no core-range bookkeeping from the caller.
        #
        # Note this bounds a container's SHARE, not its process count: ``nproc``
        # reads sched_getaffinity, which a quota does not narrow, so an agent
        # that fans out by core count still spawns host-core-count processes.
        # They now contend for the container's own slice instead of the host's,
        # which is the property that matters — the context-switch cost stays
        # charged to the trial that caused it.
        if not cpu_limit_is_unbounded(self.cpu_limit):
            cmd.extend(["--cpus", self.cpu_limit.strip()])

        # Docker injects HTTP(S)_PROXY/ALL_PROXY into every container from the
        # CLI's ~/.docker/config.json "proxies" block. For an agent container
        # that is actively harmful: the agent's own traffic to the benchmark
        # target (a docker-network host like ``frontend``) gets forced through
        # the host proxy and fails — agents have been observed wasting turns
        # diagnosing "the proxy is interfering" and retrying with --noproxy.
        # The agent reaches the model through the in-container sidecar
        # (ANTHROPIC_BASE_URL), never through these vars, so blank them by
        # default. A benchmark that genuinely needs an egress proxy can set one
        # via extra_env — those are applied below and override these empties.
        for _proxy_var in (
            "HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY",
            "http_proxy", "https_proxy", "all_proxy",
        ):
            cmd.extend(["-e", f"{_proxy_var}="])
        for k, v in self.env_vars.items():
            cmd.extend(["-e", f"{k}={v}"])

        for host_path, container_path in self.volumes.items():
            cmd.extend(["--mount", _docker_bind_mount_spec(host_path, container_path)])

        for opt in self.security_opt:
            cmd.extend(["--security-opt", opt])
        for cap in self.cap_add:
            cmd.extend(["--cap-add", cap])
        for group in self.group_add:
            cmd.extend(["--group-add", group])
        if self.privileged:
            cmd.append("--privileged")

        cmd.extend(["--add-host", "host.docker.internal:host-gateway"])
        for hostname, ip in self.extra_hosts.items():
            cmd.extend(["--add-host", f"{hostname}:{ip}"])

        # ``sleep infinity`` keeps the container alive but never reaps: every
        # process the agent orphans (a backgrounded bash, a curl whose shell
        # exited, a compiler killed by timeout) reparents to it and stays a
        # zombie for the whole trial. A long trial accumulated 1091 of them.
        # ``--init`` puts tini at PID 1 instead, which reaps orphans and
        # forwards signals, so ``docker stop`` also shuts down cleanly.
        cmd.extend([self.image, "sleep", "infinity"])

        result = self._run_local(cmd, timeout=self.start_timeout)
        if result.exit_code != 0:
            # Typed, so the CLI renders it as a message and the trial classifier
            # attributes it to the container rather than to nothing. The missing
            # image is by far the most common cause and has a one-line fix, so
            # say it rather than leaving a docker registry error to interpret.
            detail = (result.stderr or "").strip()
            if "Unable to find image" in detail or "manifest unknown" in detail:
                detail = (
                    f"image {self.image!r} is not available locally and could not "
                    f"be pulled.\n  Build it with: cage agent build\n  {detail[:400]}"
                )
            else:
                detail = f"docker run failed: {detail[:500]}"
            raise ContainerError(self.name, detail)
        self._started = True
        # Register for atexit cleanup (in case stop() is never called)
        with _REGISTRY_LOCK:
            _ACTIVE_CONTAINER_NAMES.add(self.name)
        self._wait_for_container_ready()
        logger.info("Container started: %s (image=%s)", self.name, self.image)

    def stop(self) -> None:
        """Stop and remove the container."""
        if not self._started:
            return
        self._run_local(["docker", "rm", "-f", self.name], timeout=30.0)
        self._started = False
        self._runtime_network_name = None
        with _REGISTRY_LOCK:
            _ACTIVE_CONTAINER_NAMES.discard(self.name)
        logger.info("Container stopped: %s", self.name)

    # ------------------------------------------------------------------ #
    # Command execution
    # ------------------------------------------------------------------ #

    def exec(
        self,
        command: str,
        *,
        timeout: float | None = None,
        interactive: bool = False,
        user: str | None = None,
        cwd: str = "",
    ) -> ExecResult:
        """Execute a command inside the container.

        Args:
            command: Shell command string.
            timeout: Max execution time in seconds.
            interactive: Use -i flag (needed for Claude Code).
            user: Run as specific user (e.g. "agent").
            cwd: Working directory inside the container.
        """
        if not self._started:
            raise RuntimeError(f"Container {self.name} is not running")

        cmd = ["docker", "exec"]
        if interactive:
            cmd.append("-i")
        if cwd:
            cmd.extend(["-w", cwd])

        if user:
            # ``--user`` inherits the container's env (HOME, etc.); ``su <u> -c``
            # would reset HOME and break tools that read ``~/.codex`` etc.
            cmd.extend(["--user", user, self.name, "bash", "-lc", command])
        else:
            cmd.extend([self.name, "bash", "-lc", command])

        logger.debug(
            "container_exec_start",
            extra={"command": command[:200], "timeout": timeout, "interactive": interactive},
        )

        return self._run_local(cmd, timeout=timeout)

    def copy_from(
        self,
        container_path: str,
        host_path: str,
        *,
        timeout: float | None = 300.0,
    ) -> ExecResult:
        """docker cp from container to host."""
        return self._run_local(
            ["docker", "cp", f"{self.name}:{container_path}", host_path],
            timeout=timeout,
        )

    def copy_to(
        self,
        host_path: str,
        container_path: str,
        *,
        timeout: float | None = 300.0,
    ) -> ExecResult:
        """docker cp from host to container."""
        return self._run_local(
            ["docker", "cp", host_path, f"{self.name}:{container_path}"],
            timeout=timeout,
        )

    def get_version(self, version_command: str) -> str:
        """Run a version command and return the output."""
        result = self.exec(version_command, timeout=10.0)
        return result.stdout.strip() if result.exit_code == 0 else "unknown"

    # ------------------------------------------------------------------ #
    # Workspace management
    # ------------------------------------------------------------------ #

    def setup_workspace(self, workspace_dir: str, *, owner: str = "agent") -> None:
        """Create workspace directory with proper ownership."""
        self.exec(f"mkdir -p {workspace_dir} && chown {owner}:{owner} {workspace_dir}")

    def write_file(self, path: str, content: str) -> None:
        """Write a file inside the container via heredoc."""
        self.exec(
            f"cat > {path} << 'CAGE_EOF'\n{content}\nCAGE_EOF"
        )

    def mkdir(self, path: str) -> None:
        """Create a directory inside the container."""
        self.exec(f"mkdir -p {path}")

    def exists(self, path: str) -> bool:
        """Check if a path exists inside the container."""
        result = self.exec(f"test -e {path}", timeout=5.0)
        return result.exit_code == 0

    def symlink_dir_content(self, src_dir: str, dst_dir: str) -> None:
        """Create symlinks from src_dir into dst_dir using cp -rs."""
        self.exec(f"mkdir -p {dst_dir}")
        self.exec(f"cp -rs {src_dir}/* {dst_dir}/")

    def hardlink_dir_content(self, src_dir: str, dst_dir: str) -> None:
        """Create hardlinks from src_dir into dst_dir using cp -rl."""
        result = self.exec(f"mkdir -p {dst_dir} && cp -rl {src_dir}/* {dst_dir}/ 2>/dev/null || true")
        logger.debug(
            "Hard-linked %s/* -> %s (exit_code=%d)",
            src_dir, dst_dir, result.exit_code,
        )

    def reset_directory(self, path: str) -> None:
        """Remove all contents of a directory."""
        self.exec(f"rm -rf {path}/* {path}/.[!.]* {path}/..?* 2>/dev/null || true")

    def prepare_challenge_files(self, challenge: dict) -> str:
        """Copy all challenge files into /challenge/{dir_name} in the container.

        Returns the container directory name (e.g. 'targetenv_{chal_id}_{uuid}').
        """
        challenge_id = challenge.get("id")
        file_paths = challenge.get("files", [])
        if not file_paths:
            logger.warning("No 'file' field in challenge %s", challenge_id)

        dir_name = f"targetenv_{challenge_id}_{uuid.uuid4().hex[:8]}"
        container_dir = f"/challenge/{dir_name}"
        host_tmp_dir = Path("/tmp") / dir_name

        try:
            host_tmp_dir.mkdir(parents=True, exist_ok=True)
            for rel_path in file_paths:
                src = Path(challenge["full_path"]) / rel_path
                if not src.exists():
                    logger.error("Challenge file missing: %s", src)
                    continue
                dst = host_tmp_dir / rel_path
                dst.parent.mkdir(parents=True, exist_ok=True)
                if src.is_file():
                    shutil.copy2(src, dst)
                else:
                    shutil.copytree(src, dst, dirs_exist_ok=True)

            self.mkdir(container_dir)
            self.copy_to(str(host_tmp_dir), "/challenge/")
            logger.info("Copied challenge files to container:%s", container_dir)
            return dir_name
        finally:
            if host_tmp_dir.exists():
                shutil.rmtree(host_tmp_dir, ignore_errors=True)

    # ------------------------------------------------------------------ #
    # Network management
    # ------------------------------------------------------------------ #

    def connect_network(self, network_name: str, *, ipv4_address: str | None = None) -> None:
        """Connect the running container to a Docker network.

        Args:
            network_name: Docker network to join.
            ipv4_address: Optional static IPv4 address to assign.
        """
        if not self._started or not network_name:
            return
        cmd = ["docker", "network", "connect"]
        if ipv4_address:
            cmd.extend(["--ip", ipv4_address])
        cmd.extend([network_name, self.name])

        self._run_local(cmd, timeout=30.0)
        self._runtime_network_name = network_name
        logger.info("Connected %s to network %s%s",
                     self.name, network_name,
                     f" (ip={ipv4_address})" if ipv4_address else "")

    def disconnect_network(self, network_name: str) -> None:
        """Disconnect the running container from a Docker network."""
        if not self._started or not network_name:
            return
        self._run_local(
            ["docker", "network", "disconnect", "-f", network_name, self.name],
            timeout=30.0,
        )
        self._runtime_network_name = None

    def sync_runtime_network(self, network_name: str | None) -> None:
        """Attach to the active runtime network and detach from the previous one."""
        if self.network_mode == "host":
            if network_name and network_name != self._runtime_network_name:
                raise RuntimeError(
                    f"Container {self.name} uses host networking and cannot join runtime network {network_name}"
                )
            return
        if network_name == self._runtime_network_name:
            return
        if self._runtime_network_name and self._runtime_network_name != network_name:
            self.disconnect_network(self._runtime_network_name)
            self._runtime_network_name = None
        if network_name:
            self.connect_network(network_name)
            self._runtime_network_name = network_name

    # ------------------------------------------------------------------ #
    # Background process management
    # ------------------------------------------------------------------ #

    def exec_background(self, command: str, *, user: str | None = None) -> str:
        """Start a command as a background process inside the container.

        Uses `docker exec -d` which detaches immediately.
        Returns the PID of the started process.
        """
        if not self._started:
            raise RuntimeError(f"Container {self.name} is not running")

        cmd = ["docker", "exec", "-d"]
        if user:
            cmd.extend(["-u", user])
        cmd.extend([self.name, "bash", "-c", command])

        logger.debug(
            "container_exec_background",
            extra={"command": command[:200], "user": user},
        )

        result = self._run_local(cmd, timeout=30.0)
        if result.exit_code != 0:
            raise RuntimeError(
                f"Failed to start background process: {result.stderr[:500]}"
            )
        # docker exec -d doesn't return PID directly; find it
        pid_result = self.exec("pgrep -n -f $(echo '$0' | head -c 50)", timeout=5.0)
        pid = pid_result.stdout.strip()
        if not pid or not pid.isdigit():
            return ""
        return pid

    def is_process_running(self, pid: str) -> bool:
        """Check if a process with the given PID is running in the container."""
        result = self.exec(f"kill -0 {pid} 2>/dev/null", timeout=5.0)
        return result.exit_code == 0

    def kill_process(self, pid: str, *, signal: str = "TERM") -> None:
        """Send a signal to a process in the container."""
        self.exec(f"kill -s {signal} {pid} 2>/dev/null || true", timeout=5.0)

    def kill_agent(
        self,
        *,
        user: str = "agent",
        spare_pattern: str = CONTAINER_PROXY_SCRIPT_NAME,
        escalate: bool = True,
    ) -> bool:
        """Force-kill the agent process tree inside the container.

        The agent is launched via :meth:`exec_async` as the unprivileged
        ``agent`` user. Killing the host-side ``docker exec`` *client* (the
        ``Popen`` returned by ``exec_async``) does **not** stop it: Docker does
        not forward the client's death into the container, so the agent keeps
        running — still issuing model calls — and the host-side
        ``proc.communicate()`` blocks on the exec stdout pipe the agent's
        children keep open. Every in-band termination (wall-clock timeout,
        ``max_rounds``/token/cost budget, live-check success) needs to actually
        reach into the container; this is that hammer.

        We SIGKILL every ``user`` process **except** the proxy sidecar (which
        runs as the same user and must outlive the agent to flush its request
        log — matched by ``spare_pattern`` in ``/proc/<pid>/cmdline``). This
        runs as the container's default (root) user so it can signal the
        unprivileged agent, targets the per-trial container's own PID namespace
        (each trial gets its own container, so this never touches another
        trial), and once the agent tree dies the exec pipe EOFs and the
        host-side drain returns promptly.

        The reap is VERIFIED, not fire-and-forget. ``_run_local`` reports a
        ``docker exec`` timeout as ``exit_code == -1`` instead of raising, so a
        single unchecked call fails silently — and it fails precisely when it
        matters most: an agent whose runaway child is thrashing the host is the
        case where ``docker exec`` needs longer than the first budget just to
        fork. We therefore re-probe for survivors, retry once with a much larger
        budget, and (when ``escalate``) fall back to ``docker kill``, which the
        daemon delivers to PID 1 without ever forking inside the starved
        container.

        Returns ``True`` once no agent process survives, ``False`` when that
        could not be established.
        """
        if not self._started:
            return True
        # POSIX sh loop: list the user's PIDs, skip the sidecar, act on the rest.
        loop = (
            f"for p in $(pgrep -u {shlex.quote(user)} 2>/dev/null); do "
            f"grep -qa {shlex.quote(spare_pattern)} \"/proc/$p/cmdline\" 2>/dev/null "
            f"|| %s; "
            f"done; true"
        )
        reap_script = loop % 'kill -KILL "$p" 2>/dev/null'
        probe_script = loop % 'echo "$p"'

        survivors: list[str] | None = None
        for timeout in (10.0, 60.0):
            self._reap_agent_once(reap_script, timeout=timeout)
            survivors = self._agent_survivors(probe_script, timeout=timeout)
            if survivors == []:
                return True

        detail = "unknown (container unreachable)" if survivors is None \
            else ",".join(survivors)
        logger.warning(
            "kill_agent: agent tree still alive in %s after two reap attempts "
            "(survivors=%s)%s",
            self.name,
            detail,
            "; escalating to `docker kill`" if escalate else "",
        )
        if not escalate:
            return False
        # Stops the whole container, so any post-trial snapshot will fail. That
        # is the accepted trade against leaving a runaway agent burning host
        # memory and model quota. ``_started`` stays True so ``stop()`` still
        # runs ``docker rm -f`` and the container is not leaked.
        result = self._run_local(["docker", "kill", self.name], timeout=30.0)
        stderr = (result.stderr or "").strip()
        if result.exit_code == 0:
            logger.warning("kill_agent: escalated to `docker kill %s`", self.name)
            return True
        if "is not running" in stderr:
            return True  # it died between the probe and the escalation
        logger.error(
            "kill_agent: `docker kill %s` failed (exit=%s): %s",
            self.name,
            result.exit_code,
            stderr[:200],
        )
        return False

    def _reap_agent_once(self, script: str, *, timeout: float) -> None:
        """One best-effort SIGKILL sweep; never raises."""
        try:
            self.exec(script, timeout=timeout)
        except Exception as exc:  # noqa: BLE001 - best-effort reaper; never raise
            logger.warning("kill_agent reap failed for %s: %s", self.name, exc)

    def _agent_survivors(self, script: str, *, timeout: float) -> list[str] | None:
        """PIDs still alive after a sweep, or None when the probe itself failed.

        None and ``[]`` mean different things: ``[]`` is a confirmed clean
        container, None is "we could not find out" — which must NOT be read as
        success, because a timed-out probe is the signature of the very
        situation the reaper exists for.
        """
        try:
            result = self.exec(script, timeout=timeout)
        except Exception as exc:  # noqa: BLE001 - probe is advisory; never raise
            logger.debug("kill_agent survivor probe failed for %s: %s", self.name, exc)
            return None
        if result.exit_code != 0:
            return None
        return [line.strip() for line in result.stdout.splitlines() if line.strip()]

    def exec_async(
        self,
        command: str,
        *,
        interactive: bool = False,
        user: str | None = None,
    ) -> subprocess.Popen:
        """Execute a command inside the container, returning a Popen for async control."""
        if not self._started:
            raise RuntimeError(f"Container {self.name} is not running")

        cmd = ["docker", "exec"]
        if interactive:
            cmd.append("-i")
        if user:
            # ``--user`` inherits the container's env (in particular
            # ``HOME``, set on ``docker run``). Going through ``su <u> -c``
            # would reset HOME to the target user's passwd home — codex /
            # claude-code then look in ``/root/.codex`` instead of the
            # ``/home/agent/.codex`` cage seeded, and silently fall back
            # to in-memory ``-c`` overrides (e.g. an incomplete
            # ``[model_providers.cage]`` block, missing ``name``).
            cmd.extend(["--user", user, self.name, "bash", "-lc", command])
        else:
            cmd.extend([self.name, "bash", "-lc", command])

        logger.debug(
            "container_exec_async",
            extra={"command": command[:200], "interactive": interactive},
        )
        return subprocess.Popen(
            cmd,
            text=True,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            # Run the agent's ``docker exec`` in its own session/process group.
            # Otherwise a terminal Ctrl+C (SIGINT to the whole foreground process
            # group) hits this child directly and kills the in-flight agent —
            # defeating the graceful "let the running trial finish" path, which
            # must be driven solely by cage's own SIGINT handler.
            start_new_session=True,
        )

    # ------------------------------------------------------------------ #
    # Persistent shell
    # ------------------------------------------------------------------ #

    def open_persistent_shell(
        self,
        *,
        cwd: str = "",
        timeout_start: float = 5.0,
    ) -> PersistentShell:
        """Open a long-lived bash session inside the container via a host PTY."""
        if not self._started:
            raise RuntimeError(f"Container {self.name} is not running")
        shell = PersistentShell(
            container_id=self.name,
            cwd=cwd,
            logger=logger,
        )
        shell.start(timeout=timeout_start)
        return shell

    # ------------------------------------------------------------------ #
    # Internal
    # ------------------------------------------------------------------ #

    def _wait_for_container_ready(self, timeout: float = 15.0, poll_interval: float = 0.5) -> None:
        """Wait until the container's writable layer is ready for cp/exec."""
        deadline = time.time() + timeout
        while time.time() < deadline:
            try:
                result = subprocess.run(
                    ["docker", "inspect", "--format", "{{.State.Running}}", self.name],
                    capture_output=True, text=True, timeout=5,
                )
                if result.returncode == 0 and "true" in result.stdout.lower():
                    return
            except subprocess.TimeoutExpired:
                pass
            time.sleep(poll_interval)
        logger.warning(
            "Container %s did not reach 'running' state within %.0fs",
            self.name, timeout,
        )

    def _run_local(
        self,
        cmd: list[str],
        *,
        timeout: float | None = None,
    ) -> ExecResult:
        started = int(time.time() * 1000)
        try:
            result = subprocess.run(
                cmd,
                text=True,
                stdin=subprocess.DEVNULL,
                capture_output=True,
                timeout=timeout,
            )
            stdout = _subprocess_text(result.stdout)
            stderr = _subprocess_text(result.stderr)
            exit_code = result.returncode
        except subprocess.TimeoutExpired as exc:
            stdout = _subprocess_text(exc.stdout)
            partial_stderr = _subprocess_text(exc.stderr).strip()
            timeout_message = f"Timed out after {timeout}s"
            stderr = (
                f"{partial_stderr}\n{timeout_message}"
                if partial_stderr
                else timeout_message
            )
            exit_code = -1
        except Exception as exc:
            stdout = ""
            stderr = str(exc)
            exit_code = -1

        ended = int(time.time() * 1000)
        duration_ms = max(0, ended - started)

        result = ExecResult(
            command=" ".join(cmd),
            stdout=stdout,
            stderr=stderr,
            exit_code=exit_code,
            duration_ms=duration_ms,
        )

        if exit_code == -1 and "Timed out" in stderr:
            logger.warning(
                "container_exec_timeout",
                extra={"command": " ".join(cmd)[:200], "timeout": timeout, "duration_ms": duration_ms},
            )
        elif exit_code != 0:
            logger.debug(
                "container_exec_failed",
                extra={
                    "command": " ".join(cmd)[:200],
                    "exit_code": exit_code,
                    "stderr": stderr[:500],
                    "duration_ms": duration_ms,
                },
            )
        else:
            logger.debug(
                "container_exec_completed",
                extra={"command": " ".join(cmd)[:200], "exit_code": 0, "duration_ms": duration_ms},
            )

        return result
