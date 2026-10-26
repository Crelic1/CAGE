from __future__ import annotations

import importlib.util
import json
import sys
import threading
from pathlib import Path
from types import SimpleNamespace

import pytest

MODULE_PATH = Path(__file__).parents[1] / "examples" / "agent_pentest_bench" / "toadex_campaign.py"
DATASET_ROOT = (
    Path(__file__).parents[1]
    / "examples"
    / "agent_pentest_bench"
    / "datasets"
    / "web_exploit_bench"
)


def _module():
    spec = importlib.util.spec_from_file_location("toadex_campaign", MODULE_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_load_campaign_reports_target_and_clean_counts(tmp_path: Path) -> None:
    manifest = tmp_path / "campaign.json"
    manifest.write_text(
        json.dumps(
            {
                "id": "discovery-4",
                "targets": [
                    {"challenge_id": "vulnerable", "expected_clean": False},
                    {"challenge_id": "clean-1", "expected_clean": True},
                    {"challenge_id": "clean-2", "expected_clean": True},
                    {"challenge_id": "clean-3", "expected_clean": True},
                ],
            }
        ),
        encoding="utf-8",
    )

    campaign = _module().load_campaign(manifest)

    assert campaign.id == "discovery-4"
    assert campaign.target_count == 4
    assert campaign.clean_count == 3
    assert campaign.clean_ratio == 0.75


def test_bundled_campaign_matches_dataset_ground_truth() -> None:
    campaign = _module().load_campaign(DATASET_ROOT / "campaigns" / "toadex-discovery-24.json")
    challenges = {}
    challenge_paths = {}
    for path in DATASET_ROOT.glob("*/challenge.json"):
        challenge = json.loads(path.read_text(encoding="utf-8"))
        challenges[challenge["id"]] = challenge
        challenge_paths[challenge["id"]] = path

    assert campaign.target_count == 24
    assert campaign.clean_count == 18
    assert campaign.cohort_counts == {
        "patched": 6,
        "reference": 6,
        "upstream": 6,
        "vulnerable": 6,
    }
    assert {target.challenge_id for target in campaign.targets} == set(challenges)
    for target in campaign.targets:
        challenge = challenges[target.challenge_id]
        vulnerabilities = challenge.get("vulnerabilities")
        assert isinstance(vulnerabilities, list)
        if target.expected_clean:
            assert challenge.get("expected_clean") is True
            assert vulnerabilities == []
            compose = (
                challenge_paths[target.challenge_id].parent / "docker-compose.cage.yml"
            ).read_text(encoding="utf-8")
            assert "evaluator:" not in compose
        else:
            assert challenge.get("expected_clean") is not True
            assert vulnerabilities

    image_locks = json.loads(
        (DATASET_ROOT / "campaigns" / "images.lock.json").read_text(encoding="utf-8")
    )["images"]
    compose_text = "\n".join(
        path.read_text(encoding="utf-8") for path in DATASET_ROOT.glob("*/docker-compose.cage.yml")
    )
    for image, digest in image_locks.items():
        assert f"{image}@{digest}" in compose_text


def test_load_campaign_rejects_duplicate_challenge_ids(tmp_path: Path) -> None:
    manifest = tmp_path / "campaign.json"
    manifest.write_text(
        json.dumps(
            {
                "id": "duplicate",
                "targets": [
                    {"challenge_id": "same", "expected_clean": False},
                    {"challenge_id": "same", "expected_clean": True},
                ],
            }
        ),
        encoding="utf-8",
    )

    campaign_module = _module()
    with pytest.raises(campaign_module.CampaignError, match="duplicate challenge_id"):
        campaign_module.load_campaign(manifest)


def test_load_campaign_rejects_declared_count_mismatch(tmp_path: Path) -> None:
    manifest = tmp_path / "campaign.json"
    manifest.write_text(
        json.dumps(
            {
                "id": "wrong-count",
                "target_count": 2,
                "expected_clean_count": 1,
                "targets": [
                    {
                        "challenge_id": "only-one",
                        "expected_clean": True,
                        "cohort": "reference",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    campaign_module = _module()
    with pytest.raises(campaign_module.CampaignError, match="target_count"):
        campaign_module.load_campaign(manifest)


def test_load_campaign_requires_explicit_boolean_expected_clean(tmp_path: Path) -> None:
    manifest = tmp_path / "campaign.json"
    manifest.write_text(
        json.dumps(
            {
                "id": "ambiguous-ground-truth",
                "targets": [
                    {
                        "challenge_id": "unknown",
                        "expected_clean": "yes",
                        "cohort": "reference",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    campaign_module = _module()
    with pytest.raises(campaign_module.CampaignError, match="expected_clean"):
        campaign_module.load_campaign(manifest)


def test_load_campaign_rejects_declared_cohort_mismatch(tmp_path: Path) -> None:
    manifest = tmp_path / "campaign.json"
    manifest.write_text(
        json.dumps(
            {
                "id": "wrong-cohorts",
                "cohort_counts": {"vulnerable": 1, "reference": 1},
                "targets": [
                    {
                        "challenge_id": "clean-one",
                        "expected_clean": True,
                        "cohort": "reference",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    campaign_module = _module()
    with pytest.raises(campaign_module.CampaignError, match="cohort_counts"):
        campaign_module.load_campaign(manifest)


def test_render_scope_pairs_access_with_urls_without_leaking_ground_truth(
    tmp_path: Path,
) -> None:
    manifest = tmp_path / "campaign.json"
    manifest.write_text(
        json.dumps(
            {
                "id": "blackbox",
                "scope_seed": "stable-order",
                "targets": [
                    {
                        "challenge_id": "pb-secret-vulnerable-id",
                        "expected_clean": False,
                        "cohort": "vulnerable",
                        "access": "alex / password-one",
                    },
                    {
                        "challenge_id": "pb-secret-clean-id",
                        "expected_clean": True,
                        "cohort": "reference",
                        "access": "blair / password-two",
                    },
                ],
            }
        ),
        encoding="utf-8",
    )
    campaign_module = _module()
    campaign = campaign_module.load_campaign(manifest)
    launches = [
        campaign_module.CampaignLaunch(
            challenge_id="pb-secret-vulnerable-id",
            run_id="internal-run-one",
            urls=("http://127.0.0.1:31001",),
        ),
        campaign_module.CampaignLaunch(
            challenge_id="pb-secret-clean-id",
            run_id="internal-run-two",
            urls=("http://127.0.0.1:31002", "http://127.0.0.1:31003"),
        ),
    ]

    scope = campaign_module.render_campaign_scope(campaign, launches)

    assert "Asset 01" in scope and "Asset 02" in scope
    assert "http://127.0.0.1:31001" in scope
    assert "http://127.0.0.1:31002" in scope
    assert "http://127.0.0.1:31003" in scope
    assert "alex / password-one" in scope
    assert "blair / password-two" in scope
    for hidden in (
        "pb-secret-vulnerable-id",
        "pb-secret-clean-id",
        "internal-run-one",
        "internal-run-two",
        "expected_clean",
        "vulnerable",
        "reference",
    ):
        assert hidden not in scope


def test_launch_campaign_starts_targets_concurrently(tmp_path: Path) -> None:
    manifest = tmp_path / "campaign.json"
    manifest.write_text(
        json.dumps(
            {
                "id": "concurrent",
                "targets": [
                    {
                        "challenge_id": f"target-{index}",
                        "expected_clean": index > 0,
                        "cohort": "reference" if index > 0 else "vulnerable",
                    }
                    for index in range(3)
                ],
            }
        ),
        encoding="utf-8",
    )
    barrier = threading.Barrier(3)

    class FakeClient:
        def launch(self, challenge_id: str, **kwargs):
            assert kwargs["network_only"] is False
            assert kwargs["prompt_level"] == "l0"
            barrier.wait(timeout=2)
            return SimpleNamespace(
                chal_id=challenge_id,
                run_id=f"run-{challenge_id}",
                entry_urls=[{"url": f"http://127.0.0.1/{challenge_id}"}],
            )

    campaign_module = _module()
    campaign = campaign_module.load_campaign(manifest)

    launches = campaign_module.launch_campaign(campaign, FakeClient(), max_workers=3, ttl=3600)

    assert {launch.challenge_id for launch in launches} == {
        "target-0",
        "target-1",
        "target-2",
    }


def test_launch_campaign_rolls_back_ready_targets_after_failure(tmp_path: Path) -> None:
    manifest = tmp_path / "campaign.json"
    manifest.write_text(
        json.dumps(
            {
                "id": "rollback",
                "targets": [
                    {
                        "challenge_id": "ready-target",
                        "expected_clean": True,
                        "cohort": "reference",
                    },
                    {
                        "challenge_id": "failed-target",
                        "expected_clean": False,
                        "cohort": "vulnerable",
                    },
                ],
            }
        ),
        encoding="utf-8",
    )

    class FakeClient:
        def __init__(self) -> None:
            self.closed = []

        def launch(self, challenge_id: str, **_kwargs):
            if challenge_id == "failed-target":
                raise RuntimeError("did not become healthy")
            return SimpleNamespace(
                run_id="run-ready",
                entry_urls=[{"url": "http://127.0.0.1:31999"}],
            )

        def close(self, challenge_id: str, run_id: str) -> None:
            self.closed.append((challenge_id, run_id))

    campaign_module = _module()
    campaign = campaign_module.load_campaign(manifest)
    client = FakeClient()

    with pytest.raises(campaign_module.CampaignError, match="rolled back"):
        campaign_module.launch_campaign(campaign, client, max_workers=2)

    assert client.closed == [("ready-target", "run-ready")]


def test_validate_campaign_targets_rejects_missing_server_challenge(tmp_path: Path) -> None:
    manifest = tmp_path / "campaign.json"
    manifest.write_text(
        json.dumps(
            {
                "id": "availability",
                "targets": [
                    {"challenge_id": "present", "expected_clean": True},
                    {"challenge_id": "missing", "expected_clean": False},
                ],
            }
        ),
        encoding="utf-8",
    )

    class FakeClient:
        def list_challenges(self, benchmark=None):
            assert benchmark == "agent_pentest_bench"
            return [{"id": "present"}]

    campaign_module = _module()
    with pytest.raises(campaign_module.CampaignError, match="missing"):
        campaign_module.validate_campaign_targets(
            campaign_module.load_campaign(manifest), FakeClient()
        )


def test_state_round_trip_is_atomic_and_refuses_overwrite(tmp_path: Path) -> None:
    campaign_module = _module()
    state = campaign_module.CampaignState(
        campaign_id="campaign-one",
        manifest_sha256="a" * 64,
        project="bench/run-one",
        launches=(
            campaign_module.CampaignLaunch(
                challenge_id="target-one",
                run_id="run-one",
                urls=("http://127.0.0.1:31001",),
            ),
        ),
    )
    path = tmp_path / "state.json"

    campaign_module.save_campaign_state(path, state)

    assert campaign_module.load_campaign_state(path) == state
    assert not list(tmp_path.glob(".state.json.*"))
    with pytest.raises(campaign_module.CampaignError, match="already exists"):
        campaign_module.save_campaign_state(path, state)


def test_route_findings_uses_exact_public_origin_and_rejects_ambiguous_host() -> None:
    campaign_module = _module()
    launches = (
        campaign_module.CampaignLaunch(
            challenge_id="first",
            run_id="run-first",
            urls=("http://127.0.0.1:31001",),
        ),
        campaign_module.CampaignLaunch(
            challenge_id="second",
            run_id="run-second",
            urls=("http://127.0.0.1:31002",),
        ),
    )

    routed = campaign_module.route_findings(
        [
            {
                "id": "finding-one",
                "endpoint": "http://127.0.0.1:31002/api/admin",
                "status": "valid",
            }
        ],
        launches,
    )

    assert list(routed) == ["second"]
    assert routed["second"][0]["id"] == "finding-one"
    with pytest.raises(campaign_module.CampaignError, match="unmatched or ambiguous"):
        campaign_module.route_findings(
            [{"id": "host-only", "host": "127.0.0.1", "status": "valid"}],
            launches,
        )


def test_build_scan_request_locks_baseline_model_agents_and_blackbox_scope(
    tmp_path: Path,
) -> None:
    manifest = tmp_path / "campaign.json"
    manifest.write_text(
        json.dumps(
            {
                "id": "blackbox",
                "targets": [
                    {
                        "challenge_id": "hidden-vulnerable-name",
                        "expected_clean": False,
                        "cohort": "vulnerable",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    campaign_module = _module()
    campaign = campaign_module.load_campaign(manifest)
    launch = campaign_module.CampaignLaunch(
        challenge_id="hidden-vulnerable-name",
        run_id="internal-run",
        urls=("http://bench.example:31001",),
    )

    request = campaign_module.build_toadex_scan_request(
        campaign,
        (launch,),
        project="bench/discovery-001",
    )

    assert request["assessment_mode"] == "bounty"
    assert request["project"] == "bench/discovery-001"
    assert request["max_concurrent"] == 1
    assert request["swarm_size"] == 2
    assert request["subagents_enabled"] is False
    assert request["model_provider"] == "openai"
    assert request["model"] == "gpt-5.6-sol"
    assert request["reasoning_effort"] == "xhigh"
    assert request["validation_model_provider"] == "openai"
    assert request["validation_model"] == "gpt-5.6-sol"
    assert request["validation_reasoning_effort"] == "xhigh"
    assert request["validate_only"] is False
    assert request["recon_only"] is False
    assert "http://bench.example:31001" in request["scope_material"]
    assert "hidden-vulnerable-name" not in request["scope_material"]
    assert "expected_clean" not in request["scope_material"]
    assert "goal_limit" not in request
    assert campaign_module.required_toadex_settings() == {
        "workers": 1,
        "auth_profile": "zeroday-cloud-codex",
        "codex": {
            "early_hangup": False,
            "always_daybreak": True,
            "fast_mode": False,
            "experimental_context": False,
            "http_response_dedup": False,
        },
    }


def test_aggregate_scores_reports_discovery_precision_and_clean_specificity() -> None:
    campaign_module = _module()
    campaign = campaign_module.Campaign(
        id="aggregate",
        targets=(
            campaign_module.CampaignTarget("vuln", False, "vulnerable"),
            campaign_module.CampaignTarget("patched", True, "patched"),
            campaign_module.CampaignTarget("reference", True, "reference"),
            campaign_module.CampaignTarget("upstream", True, "upstream"),
        ),
    )
    verdicts = {
        "vuln": {
            "scores": {
                "agent_pentest_bench": {
                    "value": 0.5,
                    "metadata": {
                        "objective_achieved": 1,
                        "objective_total": 2,
                        "submitted_findings": 2,
                        "true_positive_findings": 1,
                        "false_positive_findings": 1,
                    },
                }
            }
        },
        "patched": {
            "scores": {
                "agent_pentest_bench": {
                    "value": 1.0,
                    "metadata": {
                        "objective_achieved": 1,
                        "objective_total": 1,
                        "submitted_findings": 0,
                        "false_positive_findings": 0,
                    },
                }
            }
        },
        "reference": {
            "scores": {
                "agent_pentest_bench": {
                    "value": 0.0,
                    "metadata": {
                        "objective_achieved": 0,
                        "objective_total": 1,
                        "submitted_findings": 1,
                        "false_positive_findings": 1,
                    },
                }
            }
        },
        "upstream": {
            "scores": {
                "agent_pentest_bench": {
                    "value": 1.0,
                    "metadata": {
                        "objective_achieved": 1,
                        "objective_total": 1,
                        "submitted_findings": 0,
                        "false_positive_findings": 0,
                    },
                }
            }
        },
    }

    result = campaign_module.aggregate_scores(campaign, verdicts)

    assert result["findings"] == {
        "submitted": 3,
        "true_positive": 1,
        "false_positive": 2,
        "precision": pytest.approx(1 / 3),
    }
    assert result["vulnerability_recall"] == pytest.approx(0.5)
    assert result["clean_specificity"] == pytest.approx(2 / 3)
    assert result["discovery_f1"] == pytest.approx(0.4)
    assert result["cohorts"]["reference"]["objective_achieved"] == 0


def test_summarize_toadex_efficiency_joins_usage_with_discovery_results() -> None:
    campaign_module = _module()
    report = {
        "targets": 24,
        "findings": {"true_positive": 2},
        "per_target": {
            "vulnerable": {
                "expected_clean": False,
                "objective_achieved": 3,
            },
            "clean": {
                "expected_clean": True,
                "objective_achieved": 1,
            },
        },
    }
    job = {
        "id": "scan-123",
        "status": "succeeded",
        "started_at": "2026-10-26T01:00:00Z",
        "finished_at": "2026-10-26T02:30:00Z",
        "model_usage": {
            "response_count": 12,
            "input_tokens": 900_000,
            "cached_input_tokens": 500_000,
            "output_tokens": 100_000,
            "total_tokens": 1_000_000,
            "model_provider": "openai",
            "model": "gpt-6-sol",
            "cost_usd": 42.0,
            "cost_source": "standard_api_rate_estimate",
            "ignored_internal_field": "do not copy",
        },
    }

    result = campaign_module.summarize_toadex_efficiency(job, report)

    assert result["job_id"] == "scan-123"
    assert result["status"] == "succeeded"
    assert result["wall_seconds"] == 5400.0
    assert result["model_usage"]["total_tokens"] == 1_000_000
    assert "ignored_internal_field" not in result["model_usage"]
    assert result["tokens_per_target"] == pytest.approx(1_000_000 / 24)
    assert result["tokens_per_true_positive_finding"] == 500_000
    assert result["tokens_per_vulnerability_objective"] == pytest.approx(1_000_000 / 3)
    assert result["cost_per_true_positive_finding_usd"] == 21.0
    assert result["cost_per_vulnerability_objective_usd"] == 14.0


def test_summarize_toadex_efficiency_rejects_active_job() -> None:
    campaign_module = _module()
    with pytest.raises(campaign_module.CampaignError, match="not terminal"):
        campaign_module.summarize_toadex_efficiency(
            {"id": "scan-running", "status": "running"},
            {"targets": 24, "findings": {}, "per_target": {}},
        )


def test_validate_toadex_job_binding_rejects_wrong_project() -> None:
    campaign_module = _module()
    state = campaign_module.CampaignState(
        campaign_id="campaign",
        manifest_sha256="d" * 64,
        project="bench/correct",
        launches=(
            campaign_module.CampaignLaunch("target", "run-target", ("http://bench.test:31001",)),
        ),
    )
    good = {
        "id": "scan-good",
        "status": "succeeded",
        "options": {"project": "bench/correct"},
    }

    campaign_module.validate_toadex_job_binding(good, state)

    bad = dict(good, options={"project": "bench/wrong"})
    with pytest.raises(campaign_module.CampaignError, match="different project"):
        campaign_module.validate_toadex_job_binding(bad, state)


def test_close_campaign_is_idempotent_and_persists_closed_launches(tmp_path: Path) -> None:
    campaign_module = _module()
    state = campaign_module.CampaignState(
        campaign_id="close",
        manifest_sha256="b" * 64,
        project="bench/close",
        launches=(
            campaign_module.CampaignLaunch(
                challenge_id="already-closed",
                run_id="run-old",
                urls=("http://127.0.0.1:1",),
                closed=True,
            ),
            campaign_module.CampaignLaunch(
                challenge_id="open",
                run_id="run-open",
                urls=("http://127.0.0.1:2",),
            ),
        ),
    )

    class FakeClient:
        def __init__(self) -> None:
            self.closed = []

        def close(self, challenge_id, run_id):
            self.closed.append((challenge_id, run_id))
            return {"closed": True}

    client = FakeClient()
    closed = campaign_module.close_campaign(state, client)

    assert client.closed == [("open", "run-open")]
    assert all(launch.closed for launch in closed.launches)
    again = campaign_module.close_campaign(closed, client)
    assert again == closed
    assert client.closed == [("open", "run-open")]


def test_validate_toadex_config_rejects_noncomparable_settings() -> None:
    campaign_module = _module()
    good = {
        "values": {
            "codex": {
                "early_hangup": False,
                "always_daybreak": True,
                "fast_mode": False,
                "experimental_context": False,
                "http_response_dedup": False,
            }
        }
    }

    campaign_module.validate_toadex_config(good)

    bad = json.loads(json.dumps(good))
    bad["values"]["codex"]["fast_mode"] = True
    with pytest.raises(campaign_module.CampaignError, match="fast_mode"):
        campaign_module.validate_toadex_config(bad)


def test_select_toadex_auth_profile_accepts_only_exact_ready_profile() -> None:
    campaign_module = _module()

    class FakeToadex:
        def __init__(self) -> None:
            self.calls = []

        def json(self, method, path, *, payload=None):
            self.calls.append((method, path, payload))
            return {
                "profiles": [
                    {
                        "id": 17,
                        "name": "zeroday-cloud-codex",
                        "active": True,
                        "has_auth": True,
                        "auth_mode": "chatgpt",
                        "login_status": "complete",
                        "auth_check_status": "valid",
                    }
                ]
            }

    client = FakeToadex()

    assert campaign_module.select_toadex_auth_profile(client) == 17
    assert client.calls == [("GET", "/api/v1/account/auth-profiles", None)]


def test_select_toadex_auth_profile_activates_and_verifies_exact_profile() -> None:
    campaign_module = _module()
    ready = {
        "id": 17,
        "name": "zeroday-cloud-codex",
        "has_auth": True,
        "auth_mode": "chatgpt",
        "login_status": "complete",
        "auth_check_status": "valid",
    }

    class FakeToadex:
        def __init__(self) -> None:
            self.calls = []

        def json(self, method, path, *, payload=None):
            self.calls.append((method, path, payload))
            if method == "GET":
                return {"profiles": [{**ready, "active": False}]}
            return {"profiles": [{**ready, "active": True}]}

    client = FakeToadex()

    assert campaign_module.select_toadex_auth_profile(client) == 17
    assert client.calls == [
        ("GET", "/api/v1/account/auth-profiles", None),
        ("PATCH", "/api/v1/account/auth-profiles/17", {"active": True}),
    ]


def test_start_scan_pins_profile_and_verifies_persisted_job(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    campaign_module = _module()
    manifest = tmp_path / "campaign.json"
    manifest.write_text(
        json.dumps(
            {
                "id": "profile-pin",
                "targets": [{"challenge_id": "target", "expected_clean": True}],
            }
        ),
        encoding="utf-8",
    )
    state_path = tmp_path / "state.json"
    campaign_module.save_campaign_state(
        state_path,
        campaign_module.CampaignState(
            campaign_id="profile-pin",
            manifest_sha256=campaign_module.campaign_manifest_sha256(manifest),
            project="bench/profile-pin",
            launches=(
                campaign_module.CampaignLaunch(
                    challenge_id="target",
                    run_id="run-target",
                    urls=("http://bench.test:31001",),
                ),
            ),
        ),
    )
    job_path = tmp_path / "job.json"
    calls = []

    class FakeToadex:
        def json(self, method, path, *, payload=None):
            calls.append((method, path, payload))
            if path == "/api/v1/config":
                return {
                    "values": {
                        "codex": {
                            "early_hangup": False,
                            "always_daybreak": True,
                            "fast_mode": False,
                            "experimental_context": False,
                            "http_response_dedup": False,
                        }
                    }
                }
            return {
                "profiles": [
                    {
                        "id": 17,
                        "name": "zeroday-cloud-codex",
                        "active": True,
                        "has_auth": True,
                        "auth_mode": "chatgpt",
                        "login_status": "complete",
                        "auth_check_status": "valid",
                    }
                ]
            }

        def start_scan(self, payload):
            calls.append(("START", payload))
            return {"id": "scan-started", "status": "queued"}

        def scan_job(self, job_id):
            calls.append(("GET_JOB", job_id))
            return {
                "id": job_id,
                "status": "queued",
                "options": {
                    "project": "bench/profile-pin",
                    "codex_auth_profile_id": 17,
                    "model_provider": "openai",
                    "model": "gpt-5.6-sol",
                    "reasoning_effort": "xhigh",
                    "validation_model_provider": "openai",
                    "validation_model": "gpt-5.6-sol",
                    "validation_reasoning_effort": "xhigh",
                    "swarm_size": 2,
                    "subagents_enabled": False,
                },
                "worker_spec": {
                    "traffic_log": True,
                    "codex_fast_mode_enabled": False,
                    "codex_always_daybreak_enabled": True,
                    "codex_experimental_context_enabled": False,
                    "codex_early_hangup_enabled": False,
                    "codex_http_response_dedup_enabled": False,
                },
                "runtime": {"log_json": True},
            }

    monkeypatch.setattr(campaign_module, "_toadex_client", lambda _args: FakeToadex())

    result = campaign_module.main(
        [
            "--manifest",
            str(manifest),
            "start-scan",
            "--state",
            str(state_path),
            "--job",
            str(job_path),
        ]
    )

    assert result == 0
    assert calls[0][:2] == ("GET", "/api/v1/config")
    assert calls[1][:2] == ("GET", "/api/v1/account/auth-profiles")
    assert calls[-1] == ("GET_JOB", "scan-started")
    assert json.loads(job_path.read_text(encoding="utf-8"))["options"][
        "codex_auth_profile_id"
    ] == 17


def test_validate_started_job_rejects_disabled_monitoring() -> None:
    campaign_module = _module()
    state = campaign_module.CampaignState(
        campaign_id="monitoring",
        manifest_sha256="e" * 64,
        project="bench/monitoring",
        launches=(),
    )
    job = {
        "id": "scan-monitoring",
        "options": {
            "project": "bench/monitoring",
            "codex_auth_profile_id": 17,
            "model_provider": "openai",
            "model": "gpt-5.6-sol",
            "reasoning_effort": "xhigh",
            "validation_model_provider": "openai",
            "validation_model": "gpt-5.6-sol",
            "validation_reasoning_effort": "xhigh",
            "swarm_size": 2,
            "subagents_enabled": False,
        },
        "worker_spec": {
            "traffic_log": False,
            "codex_fast_mode_enabled": False,
            "codex_always_daybreak_enabled": True,
            "codex_experimental_context_enabled": False,
            "codex_early_hangup_enabled": False,
            "codex_http_response_dedup_enabled": False,
        },
        "runtime": {"log_json": True},
    }

    with pytest.raises(campaign_module.CampaignError, match="traffic_log"):
        campaign_module.validate_started_toadex_job(job, state, auth_profile_id=17)


def test_start_scan_refuses_existing_job_file_before_api_side_effect(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    campaign_module = _module()
    manifest = tmp_path / "campaign.json"
    manifest.write_text(
        json.dumps(
            {
                "id": "start-safely",
                "targets": [{"challenge_id": "target", "expected_clean": True}],
            }
        ),
        encoding="utf-8",
    )
    state_path = tmp_path / "state.json"
    campaign_module.save_campaign_state(
        state_path,
        campaign_module.CampaignState(
            campaign_id="start-safely",
            manifest_sha256=campaign_module.campaign_manifest_sha256(manifest),
            project="bench/start-safely",
            launches=(
                campaign_module.CampaignLaunch(
                    challenge_id="target",
                    run_id="run-target",
                    urls=("http://bench.test:31001",),
                ),
            ),
        ),
    )
    job_path = tmp_path / "job.json"
    job_path.write_text("do not overwrite", encoding="utf-8")
    calls = []

    class FakeToadex:
        def json(self, *_args):
            return {
                "values": {
                    "codex": {
                        "early_hangup": False,
                        "always_daybreak": True,
                        "fast_mode": False,
                        "experimental_context": False,
                        "http_response_dedup": False,
                    }
                }
            }

        def start_scan(self, payload):
            calls.append(payload)
            return {"id": "scan-started"}

    monkeypatch.setattr(campaign_module, "_toadex_client", lambda _args: FakeToadex())

    result = campaign_module.main(
        [
            "--manifest",
            str(manifest),
            "start-scan",
            "--state",
            str(state_path),
            "--job",
            str(job_path),
        ]
    )

    assert result == 2
    assert calls == []
    assert job_path.read_text(encoding="utf-8") == "do not overwrite"


def test_submit_campaign_routes_bundles_and_scores_empty_targets(tmp_path: Path) -> None:
    campaign_module = _module()
    campaign = campaign_module.Campaign(
        id="submit",
        targets=(
            campaign_module.CampaignTarget("clean", True, "reference"),
            campaign_module.CampaignTarget("vuln", False, "vulnerable"),
        ),
    )
    state = campaign_module.CampaignState(
        campaign_id="submit",
        manifest_sha256="c" * 64,
        project="bench/submit",
        launches=(
            campaign_module.CampaignLaunch("clean", "run-clean", ("http://bench.test:31001",)),
            campaign_module.CampaignLaunch("vuln", "run-vuln", ("http://bench.test:31002",)),
        ),
    )

    class FakeToadex:
        def list_customer_ready_findings(self, project):
            assert project == "bench/submit"
            return [
                {
                    "id": "finding-1",
                    "status": "valid",
                    "endpoint": "http://bench.test:31002/api/export",
                }
            ]

        def download_finding_bundle(self, project, finding_id):
            assert (project, finding_id) == ("bench/submit", "finding-1")
            return b"bundle"

    submitted = {}

    class FakeCage:
        def submit(self, run_id, *, final_answer_dir):
            files = sorted(path.name for path in Path(final_answer_dir).iterdir())
            submitted[run_id] = files
            clean = run_id == "run-clean"
            return {
                "scores": {
                    "agent_pentest_bench": {
                        "value": 1.0,
                        "metadata": {
                            "objective_achieved": 1,
                            "objective_total": 1,
                            "submitted_findings": 0 if clean else 1,
                            "true_positive_findings": 0 if clean else 1,
                            "false_positive_findings": 0,
                        },
                    }
                }
            }

    def fake_adapter(bundle_paths, output_dir, *, metadata_by_id):
        target = Path(output_dir)
        target.mkdir()
        if bundle_paths:
            assert metadata_by_id == {
                "finding-1": {
                    "id": "finding-1",
                    "status": "valid",
                    "endpoint": "http://bench.test:31002/api/export",
                }
            }
            (target / "001.json").write_text("{}", encoding="utf-8")
        return []

    report = campaign_module.submit_campaign(
        campaign,
        state,
        FakeCage(),
        FakeToadex(),
        tmp_path / "result",
        adapt_bundles_fn=fake_adapter,
        job_record={
            "id": "scan-submit",
            "status": "succeeded",
            "started_at": "2026-10-26T01:00:00Z",
            "finished_at": "2026-10-26T01:30:00Z",
            "options": {"project": "bench/submit"},
            "model_usage": {"total_tokens": 50_000, "cost_usd": 2.5},
        },
    )

    assert submitted == {"run-clean": [], "run-vuln": ["001.json"]}
    assert report["findings"]["submitted"] == 1
    assert report["findings"]["precision"] == 1.0
    assert report["vulnerability_recall"] == 1.0
    assert report["clean_specificity"] == 1.0
    assert report["efficiency"]["tokens_per_true_positive_finding"] == 50_000
    assert report["efficiency"]["cost_per_true_positive_finding_usd"] == 2.5
    assert (tmp_path / "result" / "report.json").is_file()
    assert (tmp_path / "result" / "verdicts" / "vuln.json").is_file()
