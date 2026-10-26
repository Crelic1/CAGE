from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path


MODULE_PATH = (
    Path(__file__).parents[1]
    / "examples"
    / "agent_pentest_bench"
    / "toadex_watchdog.py"
)
SYSTEMD_ROOT = MODULE_PATH.parent / "systemd"


def _module():
    spec = importlib.util.spec_from_file_location("toadex_watchdog", MODULE_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _profile(*, daybreak: str = "daybreak_blue", fast_mode: bool = False):
    return {
        "models": [
            {
                "model": "gpt-5.6-sol",
                "effort": "xhigh",
                "daybreak": daybreak,
                "settings": json.dumps(
                    {
                        "fast_mode": fast_mode,
                        "always_daybreak": True,
                        "experimental_context": False,
                        "early_hangup": False,
                        "http_response_dedup": False,
                    }
                ),
            }
        ]
    }


def test_profile_contract_requires_daybreak_blue_and_exact_settings() -> None:
    watchdog = _module()

    assert watchdog.profile_contract_issues(_profile()) == []
    assert "daybreak" in " ".join(
        watchdog.profile_contract_issues(_profile(daybreak="not sent"))
    )
    assert "fast_mode" in " ".join(
        watchdog.profile_contract_issues(_profile(fast_mode=True))
    )


def test_profile_contract_ignores_inflight_rows_without_wire_metadata() -> None:
    watchdog = _module()
    report = _profile()
    report["models"].append(
        {
            "model": "gpt-5.6-sol",
            "effort": "",
            "daybreak": "unknown",
            "operations": 2,
            "timed": 0,
            "incomplete": 2,
            "usage_responses": 0,
            "settings": json.dumps(
                {
                    "fast_mode": False,
                    "always_daybreak": True,
                    "experimental_context": False,
                    "early_hangup": False,
                    "http_response_dedup": False,
                }
            ),
        }
    )

    assert watchdog.profile_contract_issues(report) == []
    assert watchdog.completed_profile_model_rows(report) == 1


def test_failed_scan_is_continued_up_to_four_times() -> None:
    watchdog = _module()

    assert watchdog.choose_action(
        status="failed",
        retry_count=3,
        contract_issues=[],
        progress=True,
        stale_checks=0,
    ).action == "continue"
    assert watchdog.choose_action(
        status="failed",
        retry_count=4,
        contract_issues=[],
        progress=True,
        stale_checks=0,
    ).action == "exhausted"


def test_running_scan_restarts_only_after_four_stagnant_checks() -> None:
    watchdog = _module()

    waiting = watchdog.choose_action(
        status="running",
        retry_count=0,
        contract_issues=[],
        progress=False,
        stale_checks=2,
    )
    restarting = watchdog.choose_action(
        status="running",
        retry_count=0,
        contract_issues=[],
        progress=False,
        stale_checks=3,
    )

    assert (waiting.action, waiting.stale_checks) == ("observe", 3)
    assert (restarting.action, restarting.stale_checks) == ("restart", 4)


def test_contract_mismatch_restarts_immediately() -> None:
    watchdog = _module()

    decision = watchdog.choose_action(
        status="running",
        retry_count=0,
        contract_issues=["daybreak is not blue"],
        progress=True,
        stale_checks=0,
    )

    assert decision.action == "restart"


def test_success_is_never_retried() -> None:
    watchdog = _module()

    decision = watchdog.choose_action(
        status="succeeded",
        retry_count=0,
        contract_issues=[],
        progress=False,
        stale_checks=3,
    )

    assert decision.action == "complete"


def test_systemd_timer_is_persistent_and_runs_every_fifteen_minutes() -> None:
    timer = (SYSTEMD_ROOT / "toadex-benchmark-watchdog@.timer").read_text(
        encoding="utf-8"
    )
    service = (SYSTEMD_ROOT / "toadex-benchmark-watchdog@.service").read_text(
        encoding="utf-8"
    )

    assert "OnCalendar=*:0/15" in timer
    assert "Persistent=true" in timer
    assert "--max-retries 4" in service
    assert "UnsetEnvironment=OPENAI_API_KEY" in service
    assert "toadex-vm-proxy.socket" in service
    assert "toadex-zdc.service" not in service


def test_workspace_mount_keeps_all_worker_binds_on_vm_local_storage() -> None:
    mount = (SYSTEMD_ROOT / "toadex-benchmark-workspace.mount.in").read_text(
        encoding="utf-8"
    )

    assert "What=/var/local/toadex/engagements/CAMPAIGN_ID" in mount
    assert "Where=/opt/toadex-data/CAMPAIGN_ID" in mount
    assert "Before=toadex-zdc.service" in mount


def test_vm_controller_uses_local_idmap_compatible_runtime_sources() -> None:
    override = (SYSTEMD_ROOT / "toadex-zdc-vm-local-runtime.conf.in").read_text(
        encoding="utf-8"
    )

    for source in (
        "/var/local/toadex/controller-usr-PROFILE_TAG",
        "/var/local/toadex/controller-venv-PROFILE_TAG",
        "/var/local/toadex/source-PROFILE_TAG",
        "/var/local/toadex/worker-runtime",
        "/var/local/toadex/scan-jobs",
    ):
        assert f"src={source}" in override
    assert "env -u OPENAI_API_KEY" in override
