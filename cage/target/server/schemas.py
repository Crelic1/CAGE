"""Pydantic schemas for the challenge server's launch/stop API."""
from __future__ import annotations

import time
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

# The one timestamp format this server emits: RFC 3339 / ISO 8601, UTC, second
# precision (``2026-07-19T16:12:57Z``). Internally the instance registry tracks
# launch time as epoch seconds because that is what arithmetic (uptime) wants;
# every value that crosses a boundary — the wire, or an on-disk record — goes
# through here first. Keep it the single source of truth: a second formatter
# somewhere else is how a float leaks into a field readers parse as a date.
RFC3339_UTC = "%Y-%m-%dT%H:%M:%SZ"


def epoch_to_rfc3339(value: Any) -> Optional[str]:
    """Format epoch seconds as an RFC 3339 UTC string; ``None`` if not a number.

    Accepts the ``int``/``float`` the registry stores. A ``bool`` is an ``int``
    in Python but is never a timestamp, so it is rejected. A value that is
    already a string is passed through untouched — it came from a source that
    stores RFC 3339 directly.
    """
    if isinstance(value, str):
        return value or None
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    return time.strftime(RFC3339_UTC, time.gmtime(value))


class ServiceInfo(BaseModel):
    """One container in a launched instance.

    ``host``/``port`` are the address to use **for your audience**: an internal
    caller gets the docker alias, an external caller gets the published host
    address. The ``inner_*`` / ``internal_*`` / ``external_*`` fields expose both
    views explicitly when you need to disambiguate.
    """
    service_name: str = Field(description="Service key from the challenge definition.")
    alias: str = Field(description="Docker network alias of the container.")
    ip: str = Field(description="Container IPv4 on the isolated docker network.")
    host: Optional[str] = Field(
        default=None,
        description=(
            "Address for the caller's audience — docker alias (internal) or the "
            "published host IP (external). Null if unresolved."
        ),
    )
    port: Optional[int] = Field(
        default=None, description="Port matching `host`; mirrors `external_port`."
    )
    protocol: Optional[str] = Field(
        default=None,
        description=(
            "One of `tcp`, `udp`, `http`, or null. Null for dependency services "
            "that declare no protocol. Web-category targets are promoted to "
            "`http` after the health check, so this can differ from the value a "
            "challenge file declares."
        ),
    )
    inner_host: Optional[str] = Field(default=None, description="Docker-internal hostname.")
    inner_ip: Optional[str] = Field(
        default=None,
        description=(
            "Docker-internal IPv4, resolved AFTER the health check. Null while "
            "the instance is still starting, or if resolution failed."
        ),
    )
    inner_port: Optional[int] = Field(default=None, description="Docker-internal port.")
    internal_port: Optional[int] = Field(
        description="Port inside the container. Always present; null if undeclared."
    )
    external_host: Optional[str] = Field(
        default=None, description="Host-published address, external audience only."
    )
    external_port: Optional[int] = Field(
        description=(
            "Host-published port. Always present; null when nothing was published "
            "— which is the DEFAULT (`network_only=true`), not an error."
        )
    )


class EntryUrl(BaseModel):
    """A user-facing target entry point published to host network.

    Only returned for ``audience=external`` callers. ``role`` is the
    service name from the challenge's ``application_service_keys``
    (e.g. ``web``, ``entry_web``, ``ssh_jump``); ``url`` is the
    full address an external client should hit (``http://<host>:<port>``
    for HTTP, ``<host>:<port>`` otherwise).
    """
    name: str
    role: str
    url: str
    host: str
    port: int
    protocol: str = "tcp"


class LaunchResponse(BaseModel):
    """Result of ``GET /launch/{chal_id}``."""

    status: str = Field(
        description=(
            "One of `launched` (fresh), `recreated` (replaced a stale instance), "
            "`reused` (an existing healthy instance was returned — no new "
            "containers), or `static` (a pre-existing target, not managed here). "
            "`reused` means you may be sharing state with an earlier caller."
        )
    )
    chal_id: str = Field(description="Challenge id that was launched.")
    run_id: Optional[str] = Field(
        default=None, description="Instance handle for follow-up calls. See `InstanceSummary.run_id`."
    )
    project_name: Optional[str] = Field(
        default=None, description="Docker compose project. Null for `status=static`."
    )
    network_name: Optional[str] = Field(default=None, description="Null for `status=static`.")
    network_subnet: Optional[str] = Field(default=None, description="Null for `status=static`.")
    network_gateway: Optional[str] = Field(default=None, description="Null for `status=static`.")
    scoring: Dict[str, Any] = Field(
        default_factory=dict,
        description=(
            "FREE-FORM, passed through verbatim from the challenge definition. "
            "Its shape is owned by the benchmark, not by this server, and varies "
            "between benchmarks. Do not code-generate a type from one sample."
        ),
    )
    debug: Dict[str, Any] = Field(
        default_factory=dict,
        description=(
            "FREE-FORM network diagnostics, best-effort. Keys are OMITTED rather "
            "than nulled when a value could not be resolved, and the whole block "
            "is replaced by `{\"error\": \"...\"}` on failure. Read defensively; "
            "for human debugging only — never branch program logic on it."
        ),
    )
    services: List[ServiceInfo] = []
    entry_urls: List[EntryUrl] = Field(
        default_factory=list,
        description="See `InstanceSummary.entry_urls` — `[]` is normal, not an error.",
    )
    # Internal ``ip:port`` of the target services ON the isolated docker
    # network — the serve-only counterpart of the host-published ``entry_urls``.
    # Together with ``network_name``/``network_subnet`` this is the network an
    # external agent attaches to (however it chooses to; the server does not
    # dictate that) to reach the targets at their real internal addresses.
    container_addr: List[str] = Field(default_factory=list)
    # Where the host in ``entry_urls`` came from: ``host_header`` (derived from
    # the address this caller reached the API at — the default), ``flag``
    # (``--public-host``), ``host_ip_env``, ``route``, or ``fallback``. Empty
    # when there are no entry_urls. Present so an unreachable advertised
    # address is diagnosable instead of silently wrong.
    entry_url_source: str = ""
    # Lease this instance was launched with (``?ttl=<seconds>``), and what is
    # left of it. Both null when the launch requested no lease — the instance
    # then runs until someone DELETEs it.
    ttl_s: Optional[int] = None
    ttl_remaining_s: Optional[float] = None


class StopResponse(BaseModel):
    """Result of ``DELETE /launch/{chal_id}``."""

    status: str = Field(
        description=(
            "Always the literal `stopped` — INCLUDING the no-op case where no "
            "such instance existed. Not a success/failure discriminator; read "
            "`message` to tell the two apart."
        )
    )
    chal_id: str
    message: str = Field(description="Free prose, not machine-readable.")
    container_logs: List[Dict[str, Any]] = Field(
        default_factory=list,
        description=(
            "Container logs captured just before purge, for audit. Entries are "
            "NOT uniform: the normal shape is `{name, service, status, exit_code, "
            "error, logs}`, but an entry that failed to collect carries only "
            "`{name, error}` — no `logs`/`status`/`exit_code`. Access by `.get()`, "
            "not by index. Empty when the instance was already gone."
        ),
    )


class InstanceSummary(BaseModel):
    """A running target instance, projected for the management console.

    Returned by ``GET /instances``. Public-safe: carries only the operational
    facts a console needs (what is running, since when, is it healthy, where
    are its entry points) and never a flag, verify script, or scoring secret.
    ``entry_urls`` is populated for external callers exactly like
    :class:`LaunchResponse`; internal callers get the docker-internal view.
    """
    run_id: str = Field(
        description=(
            "Instance handle — pass this to `/prompt`, `/submit`, and `DELETE "
            "/launch`. Equal to `chal_id` under `target_scope=per_challenge` and "
            "for static targets; `<chal_id>_<8 hex>` under `per_agent`. Do not "
            "assume it differs from `chal_id`."
        )
    )
    chal_id: str = Field(description="Challenge id this instance was launched from.")
    benchmark: str = Field(default="", description="Owning benchmark; `\"\"` if unknown.")
    category: str = Field(default="", description="Challenge category; `\"\"` if unknown.")
    target_scope: str = Field(
        default="", description="One of `per_challenge`, `per_agent`, or `\"\"`."
    )
    audience: str = Field(
        default="",
        description=(
            "One of `internal`, `external`, or `\"\"`. Decides whether "
            "`entry_urls` is populated."
        ),
    )
    cage_run_id: str = Field(
        default="", description="Owning cage run, or `\"\"` when standalone. Never null."
    )
    lifecycle_state: str = Field(
        default="",
        description=(
            "One of `launching`, `waiting_health`, `running`, `restarting`, "
            "`stopping`, `cleanup`, or `\"\"`. Treat unknown values as "
            "in-transition rather than failing — new states may be added."
        ),
    )
    healthy: Optional[bool] = Field(
        default=None,
        description=(
            "TRI-STATE. `true`/`false` only when called with `?probe=true`; "
            "otherwise null. Null ALSO means the probe itself errored, so null is "
            "'unknown', never 'unhealthy'. Do not collapse null to false."
        ),
    )
    created_at: Optional[str] = Field(
        default=None,
        description=(
            "Launch time as an RFC 3339 / ISO 8601 UTC timestamp, second "
            "precision (`2026-07-19T16:12:57Z`). Null if the instance predates "
            "timestamp tracking. "
            "NOTE: the value is stamped when the launch STARTS and re-stamped "
            "when it completes, so for an instance observed mid-launch it can "
            "move forward (and `uptime_s` drop back toward 0) between polls — "
            "do not rely on it being monotonic."
        ),
        json_schema_extra={"format": "date-time", "example": "2026-07-19T16:12:57Z"},
    )
    uptime_s: Optional[float] = Field(
        default=None,
        description=(
            "Seconds since `created_at`, rounded to 0.1. Server-computed, so it "
            "needs no clock sync with the caller. Null when `created_at` is null."
        ),
        json_schema_extra={"example": 137.4, "x-unit": "seconds"},
    )
    network_name: Optional[str] = Field(default=None, description="Isolated docker network name.")
    network_subnet: Optional[str] = Field(default=None, description="CIDR, e.g. `172.31.4.0/24`.")
    network_gateway: Optional[str] = Field(default=None, description="Gateway IPv4 of the network.")
    service_count: int = Field(default=0, description="Containers in this instance.")
    entry_urls: List[EntryUrl] = Field(
        default_factory=list,
        description=(
            "Host-reachable entry points. ALWAYS `[]` for `audience=internal`, "
            "and `[]` under the default `network_only=true` because no host port "
            "is published. An empty list does NOT imply a broken instance — use "
            "`container_addr` for the on-network view."
        ),
    )
    # Internal ``ip:port`` of the targets on the isolated docker network (see
    # ``LaunchResponse.container_addr``). This is the network output a serve-only
    # consumer needs; how the external agent connects to it is not our concern.
    container_addr: List[str] = Field(default_factory=list)
    # See ``LaunchResponse.entry_url_source``.
    entry_url_source: str = ""
    # True when this instance holds one of the server's host-published slots
    # (``--max-public-instances``) — i.e. its entry is reachable from off-host.
    public: bool = False
    # Lease and remaining lease, in seconds. Null when the instance was
    # launched without ``?ttl=`` and so runs until deleted.
    ttl_s: Optional[int] = None
    ttl_remaining_s: Optional[float] = None


class ChallengeSummary(BaseModel):
    """Public-facing projection of a challenge, returned by ``GET /challenges``.

    Strictly excludes flag, verify scripts, ``agent_input``, and any
    ``source_fields`` content. The list endpoint is safe to expose to
    external callers carrying the bearer token.
    """
    id: str = Field(description="Pass to `GET /launch/{chal_id}`.")
    name: str
    benchmark: str = Field(description="`\"\"` when unknown.")
    category: str = Field(
        description=(
            "Falls back to the literal string `unknown` when unset — NOT `\"\"`, "
            "unlike the sibling `benchmark` field."
        )
    )
    description: str
    task_profile: str
    entry_service_count: int
    objective_count: int = Field(
        default=0,
        description=(
            "How many objectives this challenge is scored out of — the "
            "denominator a result's progress is measured against, known before "
            "the challenge is ever launched. `0` when the challenge declares "
            "none. Pairs with the `objective_achieved` / `objective_total` the "
            "scorer reports, so the same number is used end to end."
        ),
    )
    objective_kind: str = Field(
        default="",
        description=(
            "What one objective IS for this challenge — `vulnerability` for a "
            "single-target app, `host` for a multi-host range; `\"\"` when "
            "unknown. A range counts hosts it is possible to own, not marker "
            "stages: several stages can belong to one host, and a host offering "
            "only a file read can never be owned. The count above is uniform "
            "whatever the noun, so a caller reads a denominator without "
            "branching on the challenge's shape."
        ),
    )
    # Every field is a non-null string; unset values are `""` (except `category`,
    # see above). No nulls are ever emitted by this model.


class SubmitResponse(BaseModel):
    """Verdict for a serve-only submission, returned by ``POST /submit/{run_id}``.

    The server gathered live evidence against the still-running instance and
    scored the submission with the challenge's benchmark scorer. ``scores`` maps
    each scorer name to ``{value, answer, explanation, metadata}``. ``run_dir``
    is the ``.cage_runs`` path the verdict was persisted to — the same tree the
    cage inspector renders, so a submission is inspectable exactly like a
    cage-run trial. ``closed`` reports whether the instance was torn down after
    scoring (``?close=true``).

    **One submission per instance.** The score is locked in on the first submit;
    a repeat call for the same ``run_id`` returns that recorded verdict unchanged
    with ``already_submitted=true`` (an agent cannot resubmit to fish for a
    pass). To make another attempt, launch a fresh instance.
    """
    status: str = Field(
        default="scored",
        description=(
            "Always the literal `scored`. Not a discriminator — a scored FAIL and "
            "a scored PASS both report `scored`. Read `scores[*].value` for the "
            "verdict."
        ),
    )
    run_id: str
    chal_id: str
    benchmark_module: str = Field(
        default="", description="Filesystem path of the scoring module, for audit."
    )
    scores: Dict[str, Any] = Field(
        default_factory=dict,
        description=(
            "Maps scorer name to `{value, answer, explanation, metadata}`. "
            "`value` is normally a float, but a scorer may return `bool`/`int`/"
            "null and nothing coerces it — compare numerically, do not assume "
            "float. `metadata` is free-form, and a custom scorer may add keys "
            "beyond the four listed."
        ),
    )
    run_dir: str = Field(default="", description="`.cage_runs` path the verdict persisted to.")
    closed: bool = Field(
        default=False,
        description=(
            "Whether the instance was torn down after scoring (`?close=true`). "
            "On the `already_submitted=true` replay path this is always `false` "
            "even if the FIRST submit did close the instance — check "
            "`GET /instances` if you need the real current state."
        ),
    )
    already_submitted: bool = Field(
        default=False,
        description="True when this is a replay of a previously locked-in verdict.",
    )


class PromptResponse(BaseModel):
    """Agent-facing task briefing for a launched instance (``GET /prompt/{run_id}``).

    Two forms of the benchmark's own ``build_prompt`` output — the SAME briefing a
    CAGE-managed agent receives as ``{task_instruction}``:

    - ``task_prompt`` — ready to hand to your agent as-is: the live target
      address(es) of THIS instance are filled in. This is the one you use.
    - ``task_prompt_template`` — the same briefing with the target address(es)
      shown as placeholder tokens (the un-filled template).

    ``prompt_level`` is the OPERATOR-selected hint tier
    (``cage benchmark serve --prompt-level``); an agent cannot raise it. Both
    strings are empty if the benchmark exposes no ``build_prompt``.
    """
    run_id: str
    chal_id: str
    task_profile: str = ""
    prompt_level: str = "l0"
    task_prompt: str = ""
    task_prompt_template: str = ""


class LaunchOpRequest(BaseModel):
    """Body of ``POST /launches`` — a durable, idempotent launch operation.

    ``cage_run_id`` is the caller's stable correlation id AND the operation id:
    repeating the POST with the same id + params returns the same operation and
    never builds a second container set; the same id with different params is a
    ``409``. Everything else mirrors ``GET /launch`` query params.
    """
    cage_run_id: str = Field(description="Stable caller-supplied id; the launch operation's identity. Required.")
    challenge_id: str = Field(description="Challenge to launch.")
    target_scope: Optional[str] = Field(default=None, description="per_agent | per_challenge.")
    network_only: Optional[bool] = Field(default=None, description="Keep the target on the docker network only. Default follows the server (off on a --public-host server).")
    prompt_level: Optional[str] = Field(default=None, description="Hint tier l0/l1/l2 bound to this instance. Default: the server's --prompt-level.")
    parallel_mode: Optional[str] = Field(default=None, description="network | alias.")
    network_mode: Optional[str] = Field(default=None, description="compose_project_local | shared_external.")
    exposure_mode: Optional[str] = Field(default=None, description="host_ports | internal.")
    ttl: Optional[int] = Field(default=None, description="Lease in seconds; the instance is reaped when it expires.")


class RescoreRequest(BaseModel):
    """Body of ``POST /rescores`` — re-judge one already-scored submission.

    Re-runs the OFFLINE half of scoring for the submission produced by
    ``run_id``: the ``LLM_judge`` signal is re-evaluated against the findings
    frozen at submit time, while the verifier verdicts — gathered back when the
    target was still running — are reproduced from the frozen evidence, not
    re-run. No instance needs to be alive.

    Use it when a verdict is wrong for reasons outside the agent's submission:
    an expired judge API key, a rate-limited judge, a judge model being
    replaced. It never alters the agent's findings, and every pass is kept.
    """
    run_id: str = Field(description="Launch id of the submission to re-judge; also the operation's identity.")
    judge_models: List[str] = Field(default_factory=list, description="Judge model id(s) to score with. Default: the server's own judge configuration.")


class RescoreOpResult(BaseModel):
    """What a finished re-judge produced."""
    run_id: str = ""
    chal_id: str = ""
    submission_id: str = ""
    submission_dir: str = Field(default="", description="Local path of the submission record this verdict was written to.")
    benchmark_module: str = ""
    pass_id: str = Field(default="", description="Id of the pass just written; now the canonical verdict.")
    previous_pass_id: str = Field(default="", description="The pass this one superseded as canonical.")
    pass_count: int = Field(default=0, description="Total scoring passes on this submission, the original included.")
    judge_models: List[str] = Field(default_factory=list)
    scores: dict = Field(default_factory=dict, description="The new verdict, per scorer: {value, answer, explanation, metadata}.")
    previous_scores: dict = Field(default_factory=dict, description="The superseded verdict, for comparison.")
    changed: bool = Field(default=False, description="Whether any scorer's numeric value moved.")
    inputs_digest: str = ""
    inputs_unchanged: bool = Field(default=True, description="False means the frozen evidence or findings changed on disk since the original scoring, so this pass is NOT comparable to it.")
    grader_drift: bool = Field(default=False, description="True means the verifier scripts / ground truth changed since this submission was graded. The frozen verifier verdicts still reflect the OLD ones — a re-judge cannot account for that, only a fresh launch can.")
    scored_at: float = Field(default=0.0, description="Unix time this pass was scored.")
    from_record: bool = Field(default=False, description="True when this verdict was read back from the submission record rather than produced by the polled operation (e.g. after a serve restart).")


class RescoreOpError(BaseModel):
    code: str = Field(description="Machine-readable failure code, e.g. RescoreError.")
    message: str = Field(description="Human-readable detail.")


class RescoreOpStatus(BaseModel):
    """One authoritative representation of a re-judge operation.

    Returned by ``POST /rescores`` (202 while pending) and
    ``GET /rescores/{run_id}``. ``status`` is a small state machine:
    ``queued`` → ``running`` → ``done`` | ``failed``. ``result`` is present for
    ``done``; ``error`` only for ``failed``.

    The operation id is the ``run_id``, so a re-POST while one is still pending
    returns that same operation rather than starting a competing re-judge of the
    same submission. Re-POSTing a finished one starts a fresh re-judge — that is
    the whole point of the endpoint.
    """
    run_id: str
    status: str
    status_url: str
    attempts: int = Field(default=0, description="How many re-judges have been started for this submission in this server's lifetime.")
    retry_after: Optional[int] = Field(default=None, description="Seconds to wait before re-polling (pending states only).")
    result: Optional[RescoreOpResult] = None
    error: Optional[RescoreOpError] = None


class LaunchOpError(BaseModel):
    code: str = Field(description="Machine-readable failure code, e.g. prompt_unavailable, startup_failed.")
    message: str = Field(description="Human-readable detail.")
    retryable: bool = Field(default=False, description="Whether a fresh launch (new cage_run_id) might succeed.")


class LaunchOpResult(BaseModel):
    """The complete, Fleet-consumable result of a ``ready`` launch operation."""
    run_id: str
    chal_id: str
    entry_urls: List[EntryUrl] = Field(default_factory=list)
    container_addr: List[str] = Field(default_factory=list)
    network_name: Optional[str] = None
    network_subnet: Optional[str] = None
    prompt_level: str = "l0"
    task_prompt: str = ""
    task_prompt_template: str = ""


class LaunchOpStatus(BaseModel):
    """One authoritative representation of a launch operation.

    Returned by ``POST /launches`` (202 while pending) and ``GET /launches/{id}``.
    ``status`` is a small state machine: ``queued`` → ``starting`` → ``ready`` |
    ``failed``; and ``... → closing → closed`` on cancel. ``result`` is present
    only for ``ready``; ``error`` only for ``failed``/``closed``. ``ready``
    guarantees a non-empty ``run_id``, a reachable target address, and a non-empty
    ``task_prompt`` — treat it as "go" with no second discovery step.
    """
    launch_id: str
    cage_run_id: str
    challenge_id: str
    status: str
    status_url: str
    retry_after: Optional[int] = Field(default=None, description="Seconds to wait before re-polling (pending states only).")
    result: Optional[LaunchOpResult] = None
    error: Optional[LaunchOpError] = None
