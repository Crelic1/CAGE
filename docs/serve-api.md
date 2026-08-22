# Serve API Reference

Field-by-field reference for the `cage benchmark serve` HTTP API — what every
request parameter and response field *means*, and the behaviour no schema can
express.

Three companion documents:

| | |
|---|---|
| [`serve-external-audience.md`](serve-external-audience.md) | The narrative contract: deployment model, isolation, anti-cheat, worked `curl` and SDK examples. **Read that first** if you are integrating for the first time. |
| [`openapi.json`](openapi.json) | The machine-readable schema, for generating clients. Also served live at `GET /openapi.json`, with browsable UIs at `/docs` and `/redoc`. |
| This page | Every field, what it is for, and the traps. |

**API version `1`** (`info.version` in the schema). It describes the HTTP
contract, not the Python package, and is bumped only on a breaking change.

---

## Before anything else

**Auth.** Loopback callers are `internal` and need nothing. Any non-loopback
caller needs `Authorization: Bearer <token>` when the server was started with
`--external-token`; without it every request is **401**. A bearer sent to a
server that has no token configured is also 401 — the server never silently
accepts an unverifiable credential.

**The audience is not a permission level, it is an address book.** `internal`
callers are told docker-internal addresses; `external` callers are told
host-published ones. Both can call the same endpoints. What changes is which
address you are handed.

**The loop.** List → launch → read the briefing → attack → submit → close.

```
GET  /challenges                 # what can I run, and what am I scored out of
POST /launches                   # start one; poll GET /launches/{id} until ready
GET  /prompt/{run_id}            # the agent-facing briefing (launch already returns it)
POST /submit/{run_id}            # score my work
DELETE /launch/{chal_id}?run_id= # tear it down  (or submit with ?close=true)
```

`POST /rescores` is an operator action outside that loop: it re-scores a
submission that has already been scored.

**Two id's, do not mix them up.**

| id | Who makes it | What it identifies |
|---|---|---|
| `cage_run_id` | **You** | Your launch *operation*. Idempotency key for `POST /launches`. |
| `run_id` | **The server** | The launched *instance*. Everything after launch takes this: `/prompt`, `/submit`, `DELETE`, `/rescores`. |

---

## `GET /challenges`

What is available to run. Public-safe: flags, verifier scripts, `agent_input`
and raw `source_fields` are all excluded, so this is safe to expose to the same
audience that drives the targets.

**Query parameters**

| Param | Meaning |
|---|---|
| `benchmark` | Exact-match filter on benchmark name. Omit for all. |
| `category` | Exact-match filter on category. Omit for all. |

**Response** — `ChallengeSummary[]`

| Field | Type | Meaning |
|---|---|---|
| `id` | string | The handle. Pass to `POST /launches` (`challenge_id`) or `GET /launch/{chal_id}`. |
| `name` | string | Human-facing name. Display only — never key on it. |
| `benchmark` | string | Owning benchmark. `""` when unknown. |
| `category` | string | Grouping label, e.g. `real-world-web`, `post-exploitation`. Falls back to the literal `"unknown"` — **not** `""`, unlike `benchmark`. |
| `description` | string | One-line summary of the task. |
| `task_profile` | string | `single_target` (one web app) or `multi_target` (multi-host range). This is the discriminator: it tells you which shape of challenge you are holding. |
| `entry_service_count` | int | How many user-facing entry services get published. **Not a score denominator** — see the warning below. |
| `objective_count` | int | **What a result is scored out of**, known before you launch anything. Equals the `objective_total` the scorer later reports. |
| `objective_kind` | string | What one objective *is*: `vulnerability` for a single-target app, `marker` for a range. `""` if the challenge declares none. |

> ⚠️ **`entry_service_count` is not the denominator.** For `pb-postexp-range-4`
> it is `8`, while the range is scored out of `12` markers spread across `6`
> hosts. All three numbers differ. Use `objective_count`; it is the only field
> that means "out of how many".

Progress, for any challenge and without branching on its shape:

```
progress = result.objective_achieved / result.objective_total   # == objective_count
```

---

## Launching

Two ways in. Prefer the asynchronous one for anything automated.

| | `POST /launches` (async) | `GET /launch/{chal_id}` (sync) |
|---|---|---|
| Returns | `202` immediately, poll for the result | Blocks until the target is up |
| Retry-safe | **Yes** — repeating with the same `cage_run_id` returns the same operation | No — a lost response is indistinguishable from "never accepted" |
| Cancellable | Yes, `DELETE /launches/{id}` | No |
| Use for | Orchestration, fleets, anything with a timeout | Quick manual pokes |

A multi-host range takes **minutes** of `docker compose` work. That is longer
than most proxies tolerate, which is the whole reason the async form exists.

### `POST /launches`

**Body** — `LaunchOpRequest`

| Field | Type | Meaning |
|---|---|---|
| `cage_run_id` | string, **required** | Your stable id, and the operation's identity. Re-POSTing it returns the same operation and never builds a second container set. Reusing it with *different* params is a **409**. |
| `challenge_id` | string, **required** | From `GET /challenges`. |
| `target_scope` | string, null | `per_agent` (default) gives you your own isolated instance; `per_challenge` shares one instance across callers. Use `per_agent` unless you *want* to share. |
| `network_only` | bool, null | Keep the target off host ports, reachable only on its docker network. Defaults to the server's mode — **on** normally, **off** on a `--public-host` server. |
| `prompt_level` | string, null | Hint tier bound to this instance: `l0` (no hints), `l1`, `l2`. Chosen by the operator; an agent cannot escalate itself later. Defaults to the server's `--prompt-level`. |
| `ttl` | int, null | Lease in seconds. The instance is reaped automatically when it expires. Omit for no lease. |
| `parallel_mode` | string, null | `network` or `alias`. Isolation strategy for concurrent instances. Leave unset unless you know you need it. |
| `network_mode` | string, null | `compose_project_local` or `shared_external`. |
| `exposure_mode` | string, null | `host_ports` or `internal`. The challenge definition wins over this. |

**Response** — `LaunchOpStatus`, `202` while the work is pending.

### `GET /launches/{launch_id}` · `DELETE /launches/{launch_id}`

`GET` is the authoritative status. `DELETE` cancels and cleans up, and is
idempotent.

**`LaunchOpStatus`**

| Field | Type | Meaning |
|---|---|---|
| `launch_id` | string | Echo of your `cage_run_id`. |
| `cage_run_id` | string | Same value; kept for symmetry with the request. |
| `challenge_id` | string | What is being launched. |
| `status` | string | `queued` → `starting` → `ready` \| `failed`; and `… → closing → closed` on cancel. |
| `status_url` | string | Where to poll. Use it rather than rebuilding the path. |
| `retry_after` | int, null | Seconds to wait before polling again. Present **only** while pending. Honour it — a heavy range takes minutes and tight polling only adds load. |
| `result` | `LaunchOpResult`, null | Present only on `ready`. |
| `error` | `LaunchOpError`, null | Present only on `failed` / `closed`. |

> **`ready` means genuinely usable.** It is only reported after a non-empty
> `run_id`, a healthy instance, a reachable target address, *and* a non-empty
> `task_prompt` all exist. So you can treat `ready` as "go" with no second
> discovery step.

**`LaunchOpResult`**

| Field | Type | Meaning |
|---|---|---|
| `run_id` | string | **The instance handle.** Everything downstream takes this. |
| `chal_id` | string | Challenge that was launched. |
| `container_addr` | string[] | `ip:port` on the isolated docker network — how a *co-located* attacker container reaches the target. |
| `entry_urls` | `EntryUrl[]` | Host-reachable entries, for an off-host caller. `[]` is normal (see `EntryUrl`). |
| `network_name` | string, null | The isolated docker network. Join it to attack as a network peer. |
| `network_subnet` | string, null | Its CIDR. |
| `task_prompt` | string | The agent-facing briefing, target address already filled in. |
| `task_prompt_template` | string | The same briefing with the address replaced by placeholder tokens — for diffing or re-templating. |
| `prompt_level` | string | The hint tier actually bound to this instance. |

**`LaunchOpError`**

| Field | Type | Meaning |
|---|---|---|
| `code` | string | Machine-readable, e.g. `startup_failed`, `prompt_unavailable`, `cancelled`. Branch on this. |
| `message` | string | Human detail. Do not parse. |
| `retryable` | bool | Whether a *fresh* launch (new `cage_run_id`) might succeed. Retrying the same id will not. |

### `GET /launch/{chal_id}` (synchronous)

Same provisioning, one blocking request. Query parameters mirror
`LaunchOpRequest` (`target_scope`, `network_only`, `prompt_level`, `ttl`,
`parallel_mode`, `network_mode`, `exposure_mode`, `cage_run_id`) plus:

| Param | Meaning |
|---|---|
| `force_recreate` | Tear down any existing instance and build a fresh one. |

**Response** — `LaunchResponse`

| Field | Type | Meaning |
|---|---|---|
| `status` | string | `launched` (fresh), `recreated` (replaced a stale one), `reused` (an existing healthy one was handed back), `static` (no containers — an externally-managed target). |
| `run_id` | string, null | Instance handle. |
| `chal_id` | string | Challenge id. |
| `services` | `ServiceInfo[]` | Every container in the instance. |
| `container_addr` | string[] | Docker-network `ip:port` list. |
| `entry_urls` | `EntryUrl[]` | Host-published entries; `[]` is normal, not an error. |
| `entry_url_source` | string | How the advertised host was derived (e.g. the `Host` header vs a configured address). Diagnostic. |
| `network_name` / `network_subnet` / `network_gateway` | string, null | The isolated network. All null for `status=static`. |
| `project_name` | string, null | Docker compose project. Null for `status=static`. |
| `ttl_s` / `ttl_remaining_s` | int / number, null | The lease and what is left of it. Null when no lease was requested. |
| `scoring` | object | **Free-form**, passed through verbatim from the challenge definition. Its shape is the benchmark's, not the framework's — do not assume keys. |
| `debug` | object | **Free-form** network diagnostics, best-effort. Keys are *omitted* rather than nulled when a value could not be determined, so check presence. |

---

## `GET /prompt/{run_id}`

The agent-facing briefing for a launched instance. `POST /launches` already
returns it; this is for fetching it again, or after a synchronous launch.

| Field | Type | Meaning |
|---|---|---|
| `run_id` / `chal_id` | string | What this briefing is for. |
| `task_prompt` | string | The briefing, with this instance's live target address filled in. Hand this to your agent. |
| `task_prompt_template` | string | Same text with the address masked to placeholder tokens. |
| `task_profile` | string | `single_target` / `multi_target`. |
| `prompt_level` | string | The hint tier bound to this instance at launch. |

Both prompt strings are `""` if the benchmark exposes no prompt builder — treat
that as "no briefing available", not as an error.

---

## `POST /submit/{run_id}`

Score one submission **against a still-running instance**. Evidence is gathered
from the live target first, so this must happen before teardown.

| Param | Where | Meaning |
|---|---|---|
| `run_id` | path | The instance being scored. |
| `close` | query | Tear the instance down after scoring. Default `false` — it stays up for inspection. |
| `label` | query | Optional human name for the record, to make it findable later. Not an identity; may repeat or be empty. |

**Body** — `multipart/form-data`, field `agent_output`: a `tar.gz` / `zip` whose
`final_answer/` directory holds your per-vulnerability report JSONs. **Omit the
file entirely for marker-only post-exploitation ranges** — those are scored from
live target state, so for them `submit` is simply "I'm done, score my markers".

> **One submission per instance.** The verdict locks in on the first call. A
> repeat for the same `run_id` returns that recorded verdict unchanged with
> `already_submitted: true`. Launch a fresh instance to try again.

**Response** — `SubmitResponse`

| Field | Type | Meaning |
|---|---|---|
| `status` | string | Always the literal `"scored"`. **Not** a pass/fail discriminator — a scored zero also reports `scored`. Read `scores[*].value`. |
| `run_id` / `chal_id` | string | What was scored. |
| `scores` | object | `{scorer_name: {value, answer, explanation, metadata}}`. See below. |
| `run_dir` | string | Server-side path the verdict was persisted to. For audit; not fetchable over HTTP. |
| `benchmark_module` | string | Path of the scoring module that produced the verdict. For audit. |
| `closed` | bool | Whether the instance was torn down. On an `already_submitted` replay this is `false` even if the original call closed it — it describes *this* call. |
| `already_submitted` | bool | True when this is a replay of a locked-in verdict. |

**Reading `scores`.** `value` is normally a float, but a scorer may return
`bool` / `int` / `null` and nothing coerces it — compare numerically, do not
assume float. `metadata` is free-form and benchmark-owned; a scorer may add keys
beyond the ones below.

Every verdict carries a uniform progress triple, whatever the challenge:

| Metadata field | Meaning |
|---|---|
| `objective_kind` | `vulnerability` or `marker`. |
| `objective_achieved` | How many were achieved. |
| `objective_total` | Out of how many — equals the `objective_count` from `GET /challenges`. |

and `value == objective_achieved / objective_total`.

Type-specific fields remain alongside it:

| Metadata field | Applies to | Meaning |
|---|---|---|
| `successful` / `total` | both | Web: vulnerabilities passed / declared. Range: **hosts compromised / hosts total**. |
| `markers_passed` / `markers_total` | ranges | Markers captured / declared. |
| `rooted` | ranges | Hosts where a root marker was captured. |
| `verifier_successful` / `verifier_results` | web | Per-vulnerability verifier verdicts. |
| `judge_successful` / `judge_findings` | web | LLM-judge verdicts, one entry per submitted finding. |
| `results` | both | Per-objective detail rows. |
| `score_source` | both | Which signals produced the verdict, e.g. `verify.py`, `verify.py+llm_judge`, `missing`. |

> ⚠️ **For a range, `successful`/`total` is *not* the score's denominator.**
> It counts hosts, while the score divides by markers. `pb-postexp-range-7`
> scored `0.75` — markers 3/4 — while holding **all 3 of 3 hosts**. Use the
> `objective_*` triple and this cannot bite you.

> ⚠️ **`judge_findings` embeds the judge's reasoning about every official
> vulnerability**, including per-candidate explanations of why your finding did
> *not* match each one. That is enough to reconstruct the ground truth. Treat
> this response as privileged and do not hand it to the agent under test.

---

## `DELETE /launch/{chal_id}?run_id=<id>`

Stop and remove exactly one instance.

| Param | Where | Meaning |
|---|---|---|
| `chal_id` | path | The challenge. |
| `run_id` | query, **required** | The instance. A DELETE always targets one instance, never "the challenge". |

**Response** — `StopResponse`

| Field | Type | Meaning |
|---|---|---|
| `status` | string | Always the literal `"stopped"` — **including** the no-op case where no such instance existed. Not a success/failure signal; the operation is idempotent by design. |
| `chal_id` | string | Echo. |
| `message` | string | Free prose. Not machine-readable. |
| `container_logs` | object[] | Logs captured just before purge, for audit. **Entries are not uniform**: normally `{name, logs}`, but an entry may instead carry an error note when capture failed. Check keys before reading. |

---

## `GET /instances`

Everything currently running on this server.

| Param | Meaning |
|---|---|
| `probe` | Run a live docker health check per instance. **Slower.** Default reports the cached lifecycle state only. |

**Response** — `InstanceSummary[]`

| Field | Type | Meaning |
|---|---|---|
| `run_id` | string | Instance handle — pass to `/prompt`, `/submit`, `DELETE`, `/rescores`. Equals `chal_id` under `target_scope=per_challenge`. |
| `chal_id` | string | Challenge it was launched from. |
| `benchmark` / `category` | string | Owning benchmark and grouping. `""` if unknown. |
| `cage_run_id` | string | Owning launch operation, or `""` when standalone. Never null. |
| `target_scope` | string | `per_challenge`, `per_agent`, or `""`. |
| `lifecycle_state` | string | `launching`, `waiting_health`, `running`, `restarting`, `stopping`, `cleanup`, or `""`. Treat an unrecognised value as in-flight rather than failed. |
| `healthy` | bool, **null** | **Tri-state.** `true`/`false` only when called with `?probe=true`. Otherwise null — and null *also* means the probe itself errored. Null never means "unhealthy". |
| `service_count` | int | Containers in the instance. |
| `container_addr` | string[] | Docker-network `ip:port` list. |
| `entry_urls` | `EntryUrl[]` | Host-reachable entries. **Always `[]`** for `audience=internal`, and `[]` under the default `network_only=true`. |
| `entry_url_source` | string | How the advertised host was derived. Diagnostic. |
| `audience` | string | `internal`, `external`, or `""` — which address book you were served. |
| `public` | bool | Whether host ports are actually published for this instance. |
| `network_name` / `network_subnet` / `network_gateway` | string, null | The isolated docker network. |
| `created_at` | string, null | Launch time, RFC 3339 UTC at second precision (`2026-07-19T16:12:57Z`). Null for instances predating the field. |
| `uptime_s` | number, null | Seconds since `created_at`, to 0.1. **Server-computed**, so it needs no clock sync with you. Null when `created_at` is. |
| `ttl_s` / `ttl_remaining_s` | int / number, null | Lease and remainder. Null when no lease. |

---

## `POST /rescores` · `GET /rescores/{run_id}`

Re-score a submission that has already been scored — **offline, with no live
instance**. The findings and the verifier evidence were persisted at submit time
precisely so this could happen later.

Use it when a verdict is wrong for reasons that have nothing to do with the
agent: an expired judge API key, a rate-limited judge, a judge model swapped
out, or a fix to the scoring logic that should be applied to past results.

**Body** — `RescoreRequest`

| Field | Type | Meaning |
|---|---|---|
| `run_id` | string, **required** | The submission to re-score, identified by its launch id. Also the operation's identity. |
| `judge_models` | string[] | Score with specific judge model id(s). Omit to use the server's own judge configuration. |

**Response** — `RescoreOpStatus`, `202` while pending.

| Field | Type | Meaning |
|---|---|---|
| `run_id` | string | Echo. |
| `status` | string | `queued` → `running` → `done` \| `failed`. |
| `status_url` | string | Where to poll. |
| `attempts` | int | How many re-scores have been started for this submission in this server's lifetime. |
| `retry_after` | int, null | Poll interval hint; present only while pending. |
| `result` | `RescoreOpResult`, null | Present on `done`. |
| `error` | `RescoreOpError`, null | Present on `failed`. `code` is machine-readable, `message` is prose. |

> **Re-POSTing a *finished* operation starts a fresh one.** This differs from
> `/launches`, where a terminal operation is returned verbatim — repeating a
> launch would build containers, whereas re-scoring only ever appends a verdict.
> While one is still pending, a re-POST returns that same operation instead of
> racing it.

**`RescoreOpResult`**

| Field | Type | Meaning |
|---|---|---|
| `run_id` / `chal_id` / `submission_id` | string | What was re-scored. |
| `scores` | object | The new verdict — same shape as `SubmitResponse.scores`. |
| `previous_scores` | object | The verdict this one superseded, for comparison. |
| `changed` | bool | Whether any scorer's numeric value actually moved. |
| `pass_id` | string | Id of the pass just written; now the canonical verdict. |
| `previous_pass_id` | string | The pass it superseded. |
| `pass_count` | int | Total passes on this submission, the original included. **Nothing is ever destroyed** — every earlier verdict is retained. |
| `judge_models` | string[] | Which judge model(s) produced this pass. |
| `inputs_digest` | string | Digest over the frozen evidence + findings this pass scored. |
| `inputs_unchanged` | bool | **`false` means the frozen evidence or findings changed on disk** since the original scoring, so this pass is not comparable to the one it replaced. |
| `grader_drift` | bool | **`true` means the verifier scripts / ground truth changed** since this submission was graded. The frozen verifier verdicts still reflect the *old* ones; no re-score can fix that — only a fresh launch and a new submission would. |
| `from_record` | bool | `true` when the verdict was read back from the stored record rather than produced by the operation you polled — e.g. after a server restart. Do not read it as "the re-score you asked for just finished". |
| `submission_dir` | string | Server-side path of the record. For audit. |
| `benchmark_module` | string | Scoring module used. For audit. |
| `scored_at` | number | Unix time this pass was scored. |

**What is and is not re-run.** The `LLM_judge` signal is re-evaluated against the
persisted findings. Verifier verdicts are **reproduced from the frozen
evidence**, not re-executed — re-running them would need the target back. A
submission with no findings at all (a marker-only range) still re-scores
normally: its whole verdict comes from that frozen evidence.

---

## Shared objects

**`ServiceInfo`** — one container in an instance.

| Field | Type | Meaning |
|---|---|---|
| `service_name` | string | Service key from the challenge definition. |
| `alias` | string | Docker network alias. |
| `ip` | string | Container IPv4 on the isolated network. |
| `internal_port` | int, null | Port inside the container. Always present; null if undeclared. |
| `inner_host` / `inner_ip` / `inner_port` | string / string / int, null | Docker-internal address. `inner_ip` resolves only **after** the health check — null while starting. |
| `external_host` / `external_port` | string / int, null | Host-published address. **Null is the default**, not a failure: nothing is published under `network_only=true`. |
| `host` / `port` | string / int, null | The address for *your* audience — docker alias if internal, published host if external. Use this pair unless you specifically need one of the others. |
| `protocol` | string, null | `tcp`, `udp`, `http`, or null for dependency services that declare none. |

**`EntryUrl`** — a user-facing entry point, host-reachable.

| Field | Type | Meaning |
|---|---|---|
| `name` | string | Service key. |
| `role` | string | What the entry is for. |
| `host` / `port` | string / int | Where to reach it. |
| `protocol` | string | Scheme, when known. |
| `url` | string | Ready-to-use URL. Prefer it over rebuilding from host/port. |

---

## Error codes

Business errors are raised as HTTP exceptions and are documented here rather
than in the schema — a generated client will not know about them.

| Code | When |
|---|---|
| `202` | Async operation accepted; poll `status_url`. |
| `400` | Missing or empty required value; or a re-score with no judge model available anywhere. |
| `401` | Bearer missing, wrong, or sent to a server with no token configured. |
| `404` | No such challenge, instance, or scored submission. |
| `409` | `cage_run_id` reused with different launch params; or the host-published instance cap is full (the body names the occupants). |
| `413` | Submission upload over the server's limit (1 GiB by default). Rejected before any scoring work. |
| `422` | Request body or parameters fail schema validation. |
| `500` | Challenge registry unavailable, or an unexpected server fault. |

---

## Regenerating the schema

`openapi.json` is generated from the code and enforced by CI:

```bash
python scripts/gen_openapi.py           # rewrite docs/openapi.json
python scripts/gen_openapi.py --check   # exit 1 if it is stale
```

A test fails the build when the committed schema and the code disagree, so
regenerating is part of changing the API. **This page is hand-written** — it is
not generated, and it must be updated by hand when the contract changes.
