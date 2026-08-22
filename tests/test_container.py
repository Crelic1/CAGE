"""Tests for cage.sandbox.containers."""

from __future__ import annotations

import socket
import subprocess
from pathlib import Path

from cage.sandbox import containers as container_module
from cage.sandbox.containers import Container, resolve_extra_hosts_for_url
from cage.sandbox.exec import ExecResult
from cage.sandbox.state import (
    STATE_TRANSFER_TIMEOUT_SECONDS,
    StateSnapshot,
    restore_state,
)


class TestContainer:
    def test_run_local_timeout_decodes_partial_byte_output(self, monkeypatch) -> None:
        container = Container(name="cage-test-timeout", image="image")
        container._started = True

        def fake_run(cmd, **kwargs):
            raise subprocess.TimeoutExpired(
                cmd,
                timeout=kwargs.get("timeout"),
                output=b"000",
                stderr=b"docker daemon busy\xff",
            )

        monkeypatch.setattr(container_module.subprocess, "run", fake_run)

        result = container.exec("true", timeout=3.0)

        assert result.exit_code == -1
        assert result.stdout == "000"
        assert isinstance(result.stdout, str)
        assert "docker daemon busy" in result.stderr
        assert "Timed out after 3.0s" in result.stderr
        assert isinstance(result.stderr, str)

    def test_resolve_extra_hosts_for_url_uses_host_dns(self, monkeypatch) -> None:
        monkeypatch.setattr(
            socket,
            "getaddrinfo",
            lambda *args, **kwargs: [
                (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("10.10.10.8", 0)),
            ],
        )

        assert resolve_extra_hosts_for_url("https://internal-model.example.com/v1") == {
            "internal-model.example.com": "10.10.10.8",
        }

    def test_resolve_extra_hosts_for_url_skips_ip_literal(self) -> None:
        assert resolve_extra_hosts_for_url("http://10.1.2.3:8000/v1") == {}

    def test_start_uses_configured_network_mode(self) -> None:
        container = Container(
            name="cage-test-network",
            image="cage/claude-code:pentestenv",
            network_mode="host",
        )

        recorded: list[list[str]] = []

        def fake_run_local(cmd: list[str], *, timeout: float | None = None) -> ExecResult:
            recorded.append(cmd)
            return ExecResult(
                command=" ".join(cmd),
                stdout="container-id\n",
                stderr="",
                exit_code=0,
                duration_ms=1,
            )

        container._run_local = fake_run_local  # type: ignore[method-assign]

        container.start()

        assert recorded == [[
            "docker",
            "run",
            "-d",
            "--init",
            "--name",
            "cage-test-network",
            "--network",
            "host",
            "-e",
            "HTTP_PROXY=",
            "-e",
            "HTTPS_PROXY=",
            "-e",
            "ALL_PROXY=",
            "-e",
            "http_proxy=",
            "-e",
            "https_proxy=",
            "-e",
            "all_proxy=",
            "--add-host",
            "host.docker.internal:host-gateway",
            "cage/claude-code:pentestenv",
            "sleep",
            "infinity",
        ]]
        assert container.is_running is True
        container_module._ACTIVE_CONTAINER_NAMES.discard(container.name)
        container._started = False

    def test_start_mounts_colon_host_paths_with_mount_flag(self) -> None:
        container = Container(
            name="cage-test-volume-colon",
            image="cage/claude-code:pentestenv",
            volumes={
                "/var/cage_runs/agent:model:stateless/run-fixed/trials/trial-one/proxy": (
                    "/var/lib/cage/proxy"
                ),
            },
        )

        recorded: list[list[str]] = []

        def fake_run_local(cmd: list[str], *, timeout: float | None = None) -> ExecResult:
            recorded.append(cmd)
            return ExecResult(
                command=" ".join(cmd),
                stdout="container-id\n",
                stderr="",
                exit_code=0,
                duration_ms=1,
            )

        container._run_local = fake_run_local  # type: ignore[method-assign]
        container._wait_for_container_ready = lambda: None  # type: ignore[method-assign]

        container.start()

        run_cmd = recorded[0]
        assert "-v" not in run_cmd
        mount_index = run_cmd.index("--mount")
        assert run_cmd[mount_index + 1] == (
            "type=bind,"
            "source=/var/cage_runs/agent:model:stateless/run-fixed/trials/trial-one/proxy,"
            "target=/var/lib/cage/proxy"
        )
        container_module._ACTIVE_CONTAINER_NAMES.discard(container.name)
        container._started = False

    def test_start_preserves_readonly_volume_mode_with_mount_flag(self) -> None:
        container = Container(
            name="cage-test-volume-readonly",
            image="cage/claude-code:pentestenv",
            volumes={"/tmp/plugin-marketplace": "/opt/cage-plugins/plugin-marketplace:ro"},
        )

        recorded: list[list[str]] = []

        def fake_run_local(cmd: list[str], *, timeout: float | None = None) -> ExecResult:
            recorded.append(cmd)
            return ExecResult(
                command=" ".join(cmd),
                stdout="container-id\n",
                stderr="",
                exit_code=0,
                duration_ms=1,
            )

        container._run_local = fake_run_local  # type: ignore[method-assign]
        container._wait_for_container_ready = lambda: None  # type: ignore[method-assign]

        container.start()

        run_cmd = recorded[0]
        mount_index = run_cmd.index("--mount")
        assert run_cmd[mount_index + 1] == (
            "type=bind,"
            "source=/tmp/plugin-marketplace,"
            "target=/opt/cage-plugins/plugin-marketplace,"
            "readonly"
        )
        container_module._ACTIVE_CONTAINER_NAMES.discard(container.name)
        container._started = False

    def test_start_passes_supplemental_groups(self) -> None:
        container = Container(
            name="cage-test-group-add",
            image="cage/claude-code:pentestenv",
            group_add=["1002"],
        )

        recorded: list[list[str]] = []

        def fake_run_local(cmd: list[str], *, timeout: float | None = None) -> ExecResult:
            recorded.append(cmd)
            return ExecResult(
                command=" ".join(cmd),
                stdout="container-id\n",
                stderr="",
                exit_code=0,
                duration_ms=1,
            )

        container._run_local = fake_run_local  # type: ignore[method-assign]
        container._wait_for_container_ready = lambda: None  # type: ignore[method-assign]

        container.start()

        run_cmd = recorded[0]
        assert "--group-add" in run_cmd
        group_index = run_cmd.index("--group-add")
        assert run_cmd[group_index + 1] == "1002"
        container_module._ACTIVE_CONTAINER_NAMES.discard(container.name)
        container._started = False

    def test_sync_runtime_network_connects_and_switches_networks(self) -> None:
        container = Container(
            name="cage-test-network-sync",
            image="cage/claude-code:pentestenv",
            network_mode=None,
        )
        container._started = True

        recorded: list[list[str]] = []

        def fake_run_local(cmd: list[str], *, timeout: float | None = None) -> ExecResult:
            recorded.append(cmd)
            return ExecResult(
                command=" ".join(cmd),
                stdout="",
                stderr="",
                exit_code=0,
                duration_ms=1,
            )

        container._run_local = fake_run_local  # type: ignore[method-assign]

        container.sync_runtime_network("runtime-net-a")
        container.sync_runtime_network("runtime-net-b")
        container.sync_runtime_network(None)

        assert recorded == [
            ["docker", "network", "connect", "runtime-net-a", "cage-test-network-sync"],
            ["docker", "network", "disconnect", "-f", "runtime-net-a", "cage-test-network-sync"],
            ["docker", "network", "connect", "runtime-net-b", "cage-test-network-sync"],
            ["docker", "network", "disconnect", "-f", "runtime-net-b", "cage-test-network-sync"],
        ]

    def test_copy_to_accepts_custom_timeout(self) -> None:
        container = Container(
            name="cage-test-copy-to",
            image="cage/claude-code:pentestenv",
        )

        recorded: list[tuple[list[str], float | None]] = []

        def fake_run_local(cmd: list[str], *, timeout: float | None = None) -> ExecResult:
            recorded.append((cmd, timeout))
            return ExecResult(
                command=" ".join(cmd),
                stdout="",
                stderr="",
                exit_code=0,
                duration_ms=1,
            )

        container._run_local = fake_run_local  # type: ignore[method-assign]

        container.copy_to("/tmp/state", "/home/agent/.claude", timeout=120.0)

        assert recorded == [
            (
                ["docker", "cp", "/tmp/state", "cage-test-copy-to:/home/agent/.claude"],
                120.0,
            )
        ]


class TestStateRestore:
    def test_restore_state_uses_extended_copy_timeout(self, tmp_path: Path) -> None:
        snapshot_dir = tmp_path / "snapshot"
        snapshot_dir.mkdir()
        state_dir = snapshot_dir / ".claude"
        state_dir.mkdir()
        (state_dir / "MEMORY.md").write_text("hello", encoding="utf-8")

        snapshot = StateSnapshot(
            snapshot_dir=snapshot_dir,
            state_paths=(".claude",),
            timestamp_ms=0,
        )

        class _Container:
            def __init__(self) -> None:
                self.exec_calls: list[str] = []
                self.copy_calls: list[tuple[str, str, float | None]] = []

            def exec(self, command: str):
                self.exec_calls.append(command)
                return ExecResult(command=command, stdout="", stderr="", exit_code=0, duration_ms=1)

            def copy_to(self, host_path: str, container_path: str, timeout: float | None = None):
                self.copy_calls.append((host_path, container_path, timeout))
                return ExecResult(command="", stdout="", stderr="", exit_code=0, duration_ms=1)

        container = _Container()

        restore_state(
            container,  # type: ignore[arg-type]
            snapshot=snapshot,
            home_dir="/home/agent",
        )

        assert container.exec_calls == ["mkdir -p /home/agent"]
        assert container.copy_calls == [
            (str(state_dir), "/home/agent/.claude", STATE_TRANSFER_TIMEOUT_SECONDS)
        ]


class TestKillAgent:
    """The reaper must CONFIRM the agent died, not just fire and hope.

    ``_run_local`` reports a ``docker exec`` timeout as ``exit_code == -1``
    rather than raising, so an unchecked single call fails silently — and it
    fails exactly when it matters: a runaway agent child thrashing the host is
    what makes ``docker exec`` slow enough to time out in the first place.
    """

    @staticmethod
    def _container() -> Container:
        container = Container(name="cage-test-kill", image="img")
        container._started = True
        return container

    @staticmethod
    def _exec_script(cmd: list[str]) -> str:
        return cmd[-1] if cmd[:2] == ["docker", "exec"] else ""

    def test_spares_the_sidecar_under_its_deployed_name(self) -> None:
        # The Dockerfiles COPY sidecar.py to /opt/cage-proxy/container_proxy.py,
        # so matching on "sidecar.py" would never spare the running process.
        container = self._container()
        scripts: list[str] = []

        def fake_run_local(cmd: list[str], *, timeout: float | None = None) -> ExecResult:
            scripts.append(self._exec_script(cmd))
            return ExecResult(command="", stdout="", stderr="", exit_code=0, duration_ms=1)

        container._run_local = fake_run_local  # type: ignore[method-assign]
        assert container.kill_agent() is True
        assert scripts and all("container_proxy.py" in s for s in scripts)
        assert not any("sidecar.py" in s for s in scripts)

    def test_clean_reap_returns_true_without_escalating(self) -> None:
        container = self._container()
        cmds: list[list[str]] = []

        def fake_run_local(cmd: list[str], *, timeout: float | None = None) -> ExecResult:
            cmds.append(cmd)
            return ExecResult(command="", stdout="", stderr="", exit_code=0, duration_ms=1)

        container._run_local = fake_run_local  # type: ignore[method-assign]
        assert container.kill_agent() is True
        # one sweep + one probe, and no fallback
        assert len(cmds) == 2
        assert not any(c[:2] == ["docker", "kill"] for c in cmds)

    def test_survivors_trigger_a_second_pass_then_docker_kill(self) -> None:
        container = self._container()
        cmds: list[list[str]] = []

        def fake_run_local(cmd: list[str], *, timeout: float | None = None) -> ExecResult:
            cmds.append(cmd)
            if cmd[:2] == ["docker", "kill"]:
                return ExecResult(command="", stdout="", stderr="", exit_code=0, duration_ms=1)
            # the probe keeps reporting a survivor: SIGKILL is pending on a
            # process wedged in uninterruptible sleep
            stdout = "4242\n" if 'echo "$p"' in self._exec_script(cmd) else ""
            return ExecResult(command="", stdout=stdout, stderr="", exit_code=0, duration_ms=1)

        container._run_local = fake_run_local  # type: ignore[method-assign]
        assert container.kill_agent() is True
        assert cmds[-1] == ["docker", "kill", "cage-test-kill"]
        assert sum(1 for c in cmds if c[:2] == ["docker", "exec"]) == 4  # 2 sweeps + 2 probes

    def test_silent_exec_timeout_still_escalates(self) -> None:
        container = self._container()
        cmds: list[list[str]] = []

        def fake_run_local(cmd: list[str], *, timeout: float | None = None) -> ExecResult:
            cmds.append(cmd)
            if cmd[:2] == ["docker", "kill"]:
                return ExecResult(command="", stdout="", stderr="", exit_code=0, duration_ms=1)
            # exactly how _run_local reports a timeout: no exception, -1
            return ExecResult(
                command="", stdout="", stderr=f"Timed out after {timeout}s",
                exit_code=-1, duration_ms=1,
            )

        container._run_local = fake_run_local  # type: ignore[method-assign]
        assert container.kill_agent() is True
        assert cmds[-1] == ["docker", "kill", "cage-test-kill"]

    def test_escalate_false_reports_failure_instead_of_killing(self) -> None:
        container = self._container()
        cmds: list[list[str]] = []

        def fake_run_local(cmd: list[str], *, timeout: float | None = None) -> ExecResult:
            cmds.append(cmd)
            return ExecResult(command="", stdout="", stderr="timeout", exit_code=-1, duration_ms=1)

        container._run_local = fake_run_local  # type: ignore[method-assign]
        assert container.kill_agent(escalate=False) is False
        assert not any(c[:2] == ["docker", "kill"] for c in cmds)

    def test_container_that_died_on_its_own_counts_as_reaped(self) -> None:
        container = self._container()

        def fake_run_local(cmd: list[str], *, timeout: float | None = None) -> ExecResult:
            if cmd[:2] == ["docker", "kill"]:
                return ExecResult(
                    command="", stdout="",
                    stderr="Error response from daemon: container ... is not running",
                    exit_code=1, duration_ms=1,
                )
            return ExecResult(command="", stdout="", stderr="", exit_code=-1, duration_ms=1)

        container._run_local = fake_run_local  # type: ignore[method-assign]
        assert container.kill_agent() is True

    def test_never_touches_docker_when_the_container_never_started(self) -> None:
        container = Container(name="cage-test-kill-unstarted", image="img")
        calls: list[list[str]] = []
        container._run_local = lambda cmd, *, timeout=None: calls.append(cmd)  # type: ignore[method-assign,assignment]
        assert container.kill_agent() is True
        assert calls == []


class TestMemoryLimit:
    """The cgroup ceiling is the only guard that acts BEFORE a termination
    condition fires — ``kill_agent`` never runs for a trial that ends
    ``completed``, which is how a 95 GB runaway once went unnoticed for two
    hours."""

    @staticmethod
    def _run_args(**kwargs) -> list[str]:
        container = Container(name="cage-test-mem", image="img", **kwargs)
        recorded: list[list[str]] = []

        def fake_run_local(cmd: list[str], *, timeout: float | None = None) -> ExecResult:
            recorded.append(cmd)
            return ExecResult(command="", stdout="cid\n", stderr="", exit_code=0, duration_ms=1)

        container._run_local = fake_run_local  # type: ignore[method-assign]
        container._wait_for_container_ready = lambda: None  # type: ignore[method-assign]
        try:
            container.start()
        finally:
            container_module._ACTIVE_CONTAINER_NAMES.discard(container.name)
            container._started = False
        return recorded[0]

    def test_limit_pins_memory_and_swap_together(self) -> None:
        # --memory alone lets Docker grant 2x through swap; pinning both makes
        # the ceiling mean what it says on a host that has swap.
        args = self._run_args(memory_limit="16g")
        assert "--memory" in args
        assert args[args.index("--memory") + 1] == "16g"
        assert args[args.index("--memory-swap") + 1] == "16g"

    def test_uncapped_by_default_so_the_flag_is_opt_in_at_this_layer(self) -> None:
        assert "--memory" not in self._run_args()

    def test_unlimited_spellings_leave_the_container_uncapped(self) -> None:
        for spelling in ("", "0", "unlimited", "none", "off", "-1", "  Unlimited  "):
            assert "--memory" not in self._run_args(memory_limit=spelling), spelling

    def test_whitespace_is_stripped_before_docker_sees_it(self) -> None:
        args = self._run_args(memory_limit="  16g  ")
        assert args[args.index("--memory") + 1] == "16g"


class TestCpuLimit:
    """Same fuse as the memory ceiling, for the resource fuzzing actually
    exhausts: one trial fanning out with ``-jobs=$(nproc)`` held ~1970% CPU —
    20 cores — while 60+ sibling trials queued behind it."""

    @staticmethod
    def _run_args(**kwargs) -> list[str]:
        container = Container(name="cage-test-cpu", image="img", **kwargs)
        recorded: list[list[str]] = []

        def fake_run_local(cmd: list[str], *, timeout: float | None = None) -> ExecResult:
            recorded.append(cmd)
            return ExecResult(command="", stdout="cid\n", stderr="", exit_code=0, duration_ms=1)

        container._run_local = fake_run_local  # type: ignore[method-assign]
        container._wait_for_container_ready = lambda: None  # type: ignore[method-assign]
        try:
            container.start()
        finally:
            container_module._ACTIVE_CONTAINER_NAMES.discard(container.name)
            container._started = False
        return recorded[0]

    def test_limit_is_passed_as_a_cfs_quota(self) -> None:
        # --cpus, not --cpuset-cpus: the kernel keeps placing threads on
        # whatever cores are free, so no caller has to hand out core ranges.
        args = self._run_args(cpu_limit="8")
        assert "--cpuset-cpus" not in args
        assert args[args.index("--cpus") + 1] == "8"

    def test_fractional_cores_survive_intact(self) -> None:
        args = self._run_args(cpu_limit="4.5")
        assert args[args.index("--cpus") + 1] == "4.5"

    def test_uncapped_by_default_so_the_flag_is_opt_in_at_this_layer(self) -> None:
        assert "--cpus" not in self._run_args()

    def test_unlimited_spellings_leave_the_container_uncapped(self) -> None:
        for spelling in ("", "0", "unlimited", "none", "off", "-1", "  Unlimited  "):
            assert "--cpus" not in self._run_args(cpu_limit=spelling), spelling

    def test_whitespace_is_stripped_before_docker_sees_it(self) -> None:
        args = self._run_args(cpu_limit="  8  ")
        assert args[args.index("--cpus") + 1] == "8"


def test_execution_config_default_ceiling_is_16g() -> None:
    """ExecutionConfig is the ONE source of this default (the loader reads it)."""
    from cage.config.sections import ExecutionConfig

    assert ExecutionConfig().agent_memory_limit == "16g"


def test_execution_config_default_cpu_ceiling_is_8_cores() -> None:
    """ExecutionConfig is the ONE source of this default (the loader reads it)."""
    from cage.config.sections import ExecutionConfig

    assert ExecutionConfig().agent_cpu_limit == "8"


def test_agent_container_factory_passes_the_configured_ceiling(monkeypatch) -> None:
    """A ceiling nobody wires through is a ceiling that does not exist."""
    from types import SimpleNamespace

    from cage.experiment.engine import trial_runner

    captured: dict[str, object] = {}

    def fake_container(**kwargs):
        captured.update(kwargs)
        return "container"

    monkeypatch.setattr(trial_runner, "Container", fake_container)
    run = SimpleNamespace(
        execution=SimpleNamespace(
            agent_network_mode="bridge", agent_memory_limit="24g", agent_cpu_limit="6"
        ),
        proxy=SimpleNamespace(enabled=False),
        benchmark=None,
        hooks=[],
    )
    agent = SimpleNamespace(
        effective_image="img", extra_env={}, plugins=[], agent_type=None, model=None,
    )
    trial_runner._create_container(run, agent, "cage-test-ceiling")

    assert captured["memory_limit"] == "24g"
    assert captured["cpu_limit"] == "6"
