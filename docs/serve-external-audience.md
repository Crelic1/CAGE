# Target Server External Audience

> Reference: `cage/target/server/{challenge_server,launch_workflow,launch_runtime}.py`

`cage.target.serve` is the internal FastAPI service runner that owns
target-stack lifecycle. It normally starts as an embedded subprocess for
`cage run`. This doc covers the **external-audience** mode that lets you
publish target entry points (web panels, SSH jump hosts, ...) to clients
outside the host while keeping internal scoring channels (`evaluator`,
`mysql`, ...) loopback-only.

If you are running `cage run …` on the same host and never need an outside
human or external orchestrator to hit the targets, **you do not need any of
this**. The legacy single-audience behaviour is unchanged.

**The interface is the JSON API below.** External agents drive the whole loop
programmatically (`GET /challenges` → launch → `POST /submit` → close) with no
human in the loop. For **orchestration**, launch via the durable async operation
(`POST /launches` → poll `GET /launches/{id}` → `DELETE /launches/{id}`); the
synchronous `GET /launch` / `DELETE /launch?run_id=` pair is fine for simple
same-host use. A read-only web console is served at `/` as an operator
convenience, but it is not the intended path and is rough; treat the API as the
contract and automate against it.

**Related docs:**
- [`docs/targets-check.md`](targets-check.md) describes the public build and
  smoke-run workflow for validating benchmark targets.

---

> **Network-only by default.** Launches are **network-only by default**:
> **no service is host-published: not the user-facing target, not the scoring
> sidecars (`evaluator`, `mysql`, …).** Every service is reachable only over the
> isolated docker network at the `container_addr` returned by `/launch` and
> `/instances`. A scanning agent cannot find a target (its own or another's) via
> localhost/host, and nothing leaks onto the host. The host-side scorer does not
> need a host port either: it routes to the per-instance bridge and reaches the
> evaluator at its **inner IP** (see `POST /submit`). The host-published
> `entry_urls` model the rest of this doc describes is **opt-out**: pass
> `?network_only=false` to restore host ports (entry on `0.0.0.0`, sidecars on
> `127.0.0.1`) when an external client on another machine must reach the target
> directly without docker-network access.
>
> **Serving an off-host agent is a mode, not a query param.** Start serve with
> [`--public-host`](#external-access-serving-an-agent-that-is-not-on-this-host)
> and external callers get the declared entry published on the host by default,
> named in `entry_urls` *and* in the `/prompt` briefing. Internal callers,
> including every `cage run` trial, stay network-only either way.

---

## How your agent reaches the target (run it in a container)

`container_addr` is an address **on the instance's isolated docker network**, not
a host port. The supported, cheat-resistant deployment is:

**Run your agent as a container on the serve host and join it to the instance
network.** Then it reaches the target as a network peer, at either the returned
`container_addr` (`172.31.x.y:80`) or the service's DNS alias (`http://prestashop:80`):

```bash
L=$(curl -s "http://localhost:8000/launch/pb-prestashop?target_scope=per_agent")
NET=$(jq -r .network_name <<<"$L")          # e.g. cage_bench_..._pb_prestashop_<id>_runtime_default

# either launch the agent already attached …
docker run --rm --network "$NET" your-agent-image  ./run.sh "$(jq -r '.container_addr[0]' <<<"$L")"
# … or attach a container you already started:
docker network connect "$NET" my-running-agent
```

The SDK wraps the attach case: `client.attach(inst, "my-running-agent")` (see below).

**Do not reach the target from the host, and do not give the agent the docker
socket.** `network_only` strips host ports, but it cannot contain a process
running on the host: the host routes to *every* instance's bridge subnet (so a
host process could hit its own target **and every other team's**), and a mounted
`/var/run/docker.sock` lets it `docker exec` straight into the target to read
flags/markers, i.e. `docker`-cheat. The framework trusts the deployment at this
boundary; the strong isolation only holds when the agent is a co-located
container attached to just its own instance network, with no docker socket.

Docker networks are host-local, so this path needs the agent **on the same host**
as the server. A genuinely remote agent (different machine) cannot join the
network and must fall back to the weaker host-published `entry_urls`. See
[External access](#external-access-serving-an-agent-that-is-not-on-this-host),
which is how you turn that on and what it costs.

## TL;DR

```bash
# Serve a whole benchmark by name (discovers its indices; web scoring uses the
# benchmark's declared judge model, e.g. agent_pentest_bench → deepseek-v4-pro):
cage benchmark serve agent_pentest_bench

# Override the judge model if you want a different one:
cage benchmark serve agent_pentest_bench --judge-model <model_id>

# Expose to external clients:
cage benchmark serve agent_pentest_bench --host 0.0.0.0 --external-token "$(openssl rand -hex 16)"

# …and serve an agent that is NOT on this host (publishes each challenge's
# declared entry, advertised at whatever address the caller reached you at).
# Independent of --external-token: that guards the API, this exposes targets.
cage benchmark serve agent_pentest_bench --host 0.0.0.0 --public-host

# External caller:
curl -H "Authorization: Bearer <token>" http://<server>:8000/challenges
curl -H "Authorization: Bearer <token>" \
     "http://<server>:8000/launch/pb-prestashop?target_scope=per_agent"
curl -H "Authorization: Bearer <token>" -X POST \
     -F "agent_output=@final_answer.tar.gz" "http://<server>:8000/submit/<run_id>"
```

`cage benchmark serve` is the ergonomic front for the internal runner
`python -m cage.target.serve` (which takes `--benchmark-root <dir>` /
`--host` / `--port` / `--external-token` directly).

Other `cage benchmark serve` flags:

- `--public-host [ADDR]` / `--max-public-instances <n>`. See
  [External access](#external-access-serving-an-agent-that-is-not-on-this-host).

- `--namespace <name>` (default `default`): the docker resource namespace this
  server's targets run under; give co-running servers distinct namespaces so
  their containers/networks stay isolated.
- `--adapter path/to/module.py:ClassName`: load an extra benchmark adapter
  (repeatable).
- `--open`: open the read-only console in a browser after startup.

---

## Python client (SDK)

Don't hand-roll HTTP/multipart; use the bundled client. It is **standard
library only** (no install): `from cage.target.serve_client import ServeClient`,
or copy the single file `cage/target/serve_client.py` into your agent.

```python
from cage.target.serve_client import ServeClient

client = ServeClient("http://host:8000", token="…", client_id="team-red")

for ch in client.list_challenges():
    print(ch["id"], ch["category"])

# per_agent (default) → your OWN isolated instance: unique run_id + docker
# network + fresh containers. Many agents can launch the same challenge
# concurrently and never collide.
inst = client.launch("pb-prestashop")
print(inst.run_id, inst.container_addr)     # e.g. ['172.31.x.y:80'] on inst.network_name

# ANTI-CHEAT: run your agent as a container on the serve host and join it to the
# instance network, then attack the target as a peer at inst.container_addr.
# `attach` a container you already started (or `docker run --network
# inst.network_name …` at launch). Reaching the target from the host is a cheat
# the server can't stop; see the deployment section above.
client.attach(inst, "my-running-agent-container")

# write final_answer/<vuln_id>.json reports somewhere, then score against the
# STILL-RUNNING target (keeps running so you can resubmit):
verdict = client.submit(inst.run_id, final_answer_dir="./final_answer")
print(verdict["scores"])                    # {scorer: {value, explanation, …}}

client.close(inst)

# …or let a context manager launch-and-close for you:
with client.session("pb-prestashop") as inst:
    print(inst.submit(final_answer_dir="./final_answer")["scores"])
```

Marker-only post-exploitation ranges are scored from live target state, so omit
the output entirely: `client.submit(inst.run_id)`.

Methods: `list_challenges()`, `instances()`, `launch(chal_id, *, target_scope,
network_only, force_recreate) -> Instance`, `prompt(run_id) -> dict` /
`Instance.task_prompt() -> str` (the agent-facing task briefing: the ready-to-use
`task_prompt` plus the un-filled `task_prompt_template`), `attach(instance |
run_id, container, *, network)` (join a co-located agent container to the instance
network, the anti-cheat path), `submit(run_id, *, final_answer_dir | archive,
close) -> dict`, `close(instance | chal_id, run_id)`, `session(chal_id) ->
contextmanager`. Errors raise `ServeError` (`.status` = HTTP code). The raw HTTP
contract the client wraps is documented below.

---

## External access: serving an agent that is not on this host

Everything above assumes the agent is a container **on this host** that joins the
instance's docker network. Docker networks are host-local, so a genuinely remote
agent cannot do that. Serving it means publishing the target's entry point on the
host, and because that changes what the machine listens on, it is an operator
decision made at startup, never something an incoming request can trigger:

```bash
cage benchmark serve agent_pentest_bench \
  --host 0.0.0.0 \
  --public-host                  # ← the mode switch
```

`--host` and `--public-host` are different axes: `--host` binds the **API**
socket; `--public-host` publishes the **targets**.
You can bind the API to `127.0.0.1` behind an nginx while targets are published
on the public IP, or bind `0.0.0.0` for a LAN console while every agent is still
co-located and targets stay network-only.

**What the mode changes**, for **every launch on the server**:

| | default server | `--public-host` server |
|---|---|---|
| `network_only` default | `true` | `false` (an explicit `?network_only=true` opts one launch back out) |
| what gets a host port | nothing | **exactly the declared entry services** (`application_service_keys` / `entry_services`) on `0.0.0.0` |
| scoring sidecars, inner range hosts | no host port | **still no host port**, not even on `127.0.0.1` |
| `entry_urls` | empty | populated |
| `/prompt` briefing | docker-internal addresses | rewritten to the published `host:port` |

**Publishing is a property of the server, not of the caller.** On a
`--public-host` server *every* launch publishes its declared entry by default:
a remote agent, a loopback operator, whoever. The caller's address does not
enter into it, and neither does the bearer token. That is safe because
`--public-host` is only ever set on a *dedicated* public server: `cage run`
reaches its target over the isolated docker network and its embedded target
server never sets `--public-host`, so a cage-run trial stays network-only
regardless. A single launch that should not be exposed passes `?network_only=true`.

**`--public-host` requires `--external-token`; the server refuses to start
without it.** Publishing target entries on the host also exposes the control API
(`/launches`, `/instances`, `/prompt`, `/submit`, `/launch`, `DELETE`) on that
same host address. An off-host agent that can reach a published target can reach
the API too, and without a token a non-loopback caller is classified `internal`
and gets full control: enumerate every instance, read any prompt (hint/topology
leak), submit/close or launch anything. The token gates **the API, not the
targets**: a published target is still reachable without it (agents attack
targets token-free), but the control plane must be locked so an agent cannot
pivot from its target to the API. For defence in depth, also bind the API to a
management interface (`--host <private-addr>` or `127.0.0.1` behind an
authenticated reverse proxy) so the target-facing network cannot even route to
it, and firewall the API port off that network.

Two consequences of the mode are worth understanding before you turn it on.

### The advertised address is derived, not configured

`entry_urls` needs an address the agent can actually dial. The server derives it
from the **`Host` header of the request**: the caller demonstrably just reached
the API at that address, which is stronger evidence than anything the server can
learn about itself. (A cloud VM cannot see its own elastic IP: its NIC only has
the private address, so "look at my own interfaces" is wrong exactly where it
matters.) One server therefore hands a LAN caller its LAN address and a WAN
caller its public address, correctly, with no configuration.

A **loopback** `Host` header (`localhost` / `127.0.0.1`, an operator launching
or polling `/prompt` from the serve host itself) is not a usable advertised
address, so it is ignored and the server falls back to its **route source IP**
(the address it would use to reach off-box). So even a launch driven from the
serve host publishes a dialable address, not `localhost`. Pin
`--public-host <addr>` when even that is wrong (proxy / NAT).

Pass an address (`--public-host 203.0.113.9`) only when derivation cannot
work: behind a **reverse proxy** (you reach the API at the proxy's name, but the
target ports are published on the origin host) or a **NAT** that forwards the API
and the target ports from different addresses. Every response reports
`entry_url_source` so you can tell which path produced the address.

The `Host` header is caller-controlled, so it is used **only** to render URLs
back to that same caller, never for auth, and never stored as authoritative.
This is the same rule as the reverse-proxy caveat on `X-Forwarded-For` below.

### Concurrent public instances can find each other, so they are capped

Once entries are on `0.0.0.0`, the host's address is a **shared namespace**: one
`nmap` of the host lists every published instance, and nothing binds a published
port to the agent that launched it. Two agents working concurrently can therefore
reach each other's targets, quietly contaminating both results.

So the server caps host-published instances, **default 1**:

```bash
--max-public-instances 3     # you accept the trade; 0 = unlimited
```

Over the cap, `/launch` returns **409** naming the occupants, so a queued agent
knows what to wait for instead of polling blindly:

```jsonc
{"detail": {
  "error": "public_instance_limit_reached",
  "max_public_instances": 1,
  "occupants": [{"run_id": "pb_siyucms_7c5655b6", "chal_id": "pb-siyucms",
                 "uptime_s": 29.2, "ttl_s": 600, "ttl_remaining_s": 570.8}]
}}
```

Instances launched network-only on the same server do **not** consume a slot:
they have no host port, so they are not mutually discoverable.

### Leases: `?ttl=<seconds>`

A cap plus an agent that walks away would block everyone until the server
restarts. So a launch can declare how long it needs the slot; how long a target
is needed is a property of the attempt, not of the server:

```bash
curl -H "Authorization: Bearer $TOKEN" \
  "$SERVER/launch/pb-siyucms?target_scope=per_agent&ttl=1800"
```

The instance is reaped automatically when the lease runs out;
`GET /instances` reports `ttl_remaining_s` throughout. There is no default lease
(omit `ttl` and the instance runs until `DELETE`) and no server-side ceiling on
what a launch may request: a lease is a promise the launcher makes, not a limit
the server imposes.

---

## Two audiences, one server

The server now classifies every request as either `internal` or `external`
and tailors port bindings + response shape accordingly. **The port-binding rows
below describe the host-published (`?network_only=false`) path**. Under the
default (network-only) *no* service is host-published for either audience; the
`entry_urls`/`host` distinctions still apply when you opt into host ports.

| Concern | `audience=internal` | `audience=external` |
|---|---|---|
| Entry services (`application_service_keys`) | published to `0.0.0.0:<ext_port>` | published to `0.0.0.0:<ext_port>` |
| Non-entry services (`evaluator`, `mysql`, `ssrf-listener`, …) | published to `0.0.0.0:<ext_port>` | **pinned to `127.0.0.1:<ext_port>`**, unreachable from outside the host |
| `LaunchResponse.host` for each service | docker alias (e.g. `web`, `evaluator`), the view from inside the agent container | the advertised public host (derived from your request; `--public-host` to pin) |
| `LaunchResponse.entry_urls` | empty | populated, one entry per `application_service_keys` member |

The classification rule is in `resolve_audience()`
(`cage/target/server/challenge_server.py`):

```
1. Authorization: Bearer <token>  →  external (or 401 if mismatch / server has no token configured)
2. No bearer + client.host ∈ {127.0.0.1, ::1, localhost}  →  internal
3. No bearer + non-loopback client + token IS configured  →  401
4. No bearer + non-loopback client + token NOT configured  →  internal (back-compat: same as pre-feature)
```

Token comes from `--external-token <value>` (or `TARGET_SERVER_EXTERNAL_TOKEN`
env). If neither is set, the server is in **legacy mode**: every caller is
internal and bearer headers are rejected outright, matching the behaviour
before this feature shipped.

---

## API reference

> **Field-by-field reference:** [`serve-api.md`](serve-api.md) explains what
> every request parameter and response field *means*, plus the behaviour no
> schema can express. Start there if you are wiring up a client.
>
> **Machine-readable schema.** The full OpenAPI 3.1 document is
> [`docs/openapi.json`](openapi.json) in this repo, and a running server
> publishes the same thing live at `GET /openapi.json`, with browsable UIs at
> `/docs` (Swagger) and `/redoc`. The live copy is generated from the code and
> so is always current; the committed copy is a snapshot for reading a diff or
> generating a client without a server, and CI fails if the two disagree
> (`python scripts/gen_openapi.py --check`).
>
> The prose below is the narrative contract — what each endpoint is *for*, and
> the failure modes a generated client cannot tell you about. Business error
> codes (400/401/404/409) are raised as HTTP exceptions and are documented here,
> not in the schema.

::: tip Machine-readable spec: use this, not just the prose below
The server is a FastAPI app, so it publishes its own **OpenAPI 3.1 spec live**,
with every response field's type, nullability, and enum values:

| URL | What it is |
|---|---|
| `GET {server}/openapi.json` | the spec, feed it to codegen, or to an AI agent |
| `GET {server}/docs` | Swagger UI, browsable |
| `GET {server}/redoc` | ReDoc, easier to read end-to-end |

These need no auth and are always in sync with the running server, so prefer
them over any hand-written table when the two disagree. To generate a typed
client:

```bash
curl -s http://<host>:<port>/openapi.json > serve-api.json
# then e.g. openapi-generator / datamodel-codegen / quicktype
```

The tables in this section stay for context and for the *why* behind each field;
the spec is the authority on shapes.
:::

### `GET /challenges`

List challenges with **public-safe** metadata only. Strictly excludes flag,
verify scripts, `agent_input`, and `source_fields`.

Query params:
- `benchmark`: exact-match filter on benchmark name
- `category`: exact-match filter on category

Response (`200 OK`):

```jsonc
[
  {
    "id": "SIYUCMS",
    "name": "SIYUCMS",
    "benchmark": "agent_pentest_bench",
    "category": "real-world-web",
    "description": "Detect vulnerabilities in the target website.",
    "task_profile": "single_target",
    "entry_service_count": 1,           // length of application_service_keys
    "objective_count": 6,               // scored out of 6 …
    "objective_kind": "vulnerability"   // … vulnerabilities
  },
  {
    "id": "pb-postexp-range-4",
    "task_profile": "multi_target",
    "entry_service_count": 8,           // published entries — NOT the denominator
    "objective_count": 12,              // scored out of 12 …
    "objective_kind": "marker",         // … markers
    ...
  },
  ...
]
```

**`objective_count` is what a result is scored out of**, known before anything is
launched. `objective_kind` names the unit — `vulnerability` for a single-target
app, `marker` for a multi-host range — so the *count* is uniform even though the
noun is not, and a caller renders progress without branching on challenge shape:

```
progress = result.objective_achieved / result.objective_total   // any challenge
```

The scorer reports that same pair on every verdict (see `POST /submit`), and its
`objective_total` always equals the `objective_count` advertised here. Both are
the score's own denominator: `value == objective_achieved / objective_total`.

> **Do not use `entry_service_count` as a denominator.** It counts published
> entry services, which is a different number: range-4 publishes 8 entries while
> being scored out of 12 markers across 6 hosts. All three differ.

`entry_service_count` is the only signal needed to distinguish web challenges
(1) from multi-entry post-exploitation ranges (2+) without leaking topology.

### Launch operations: `POST /launches` · `GET /launches/{id}` · `DELETE /launches/{id}`

::: tip Prefer these for orchestration
`GET /launch` below provisions inside **one synchronous request**. Standing up a
multi-host range takes minutes of `docker compose` work, longer than an ordinary
client/proxy timeout, and it is a side-effecting GET with no operation resource:
if the response is lost you cannot tell "not accepted" from "accepted and still
running", and cannot retry safely, poll, or cancel before a `run_id` exists. A
control plane (Cage Fleet, an Arena) should drive the **async launch operation**
instead. `GET /launch` stays for simple, same-host, interactive use.
:::

A launch is modelled as a durable, idempotent **operation** whose id is your
`cage_run_id`:

```http
POST /launches
Authorization: Bearer <token>          # only if the server set --external-token
Content-Type: application/json

{ "cage_run_id": "<your-uuid>", "challenge_id": "pb-postexp-range-6",
  "target_scope": "per_agent", "network_only": false, "prompt_level": "l0" }
```

returns immediately:

```http
HTTP/1.1 202 Accepted
Location: /launches/<your-uuid>
Retry-After: 2

{ "launch_id": "<your-uuid>", "status": "starting",
  "status_url": "/launches/<your-uuid>" }
```

Provisioning runs in the background. Poll `GET /launches/{id}` (honour
`Retry-After`) until it settles. `status` is a small state machine:

```
queued ─▶ starting ─▶ ready
                   └▶ failed
queued│starting│ready ─▶ closing ─▶ closed
```

A **`ready`** body carries the complete, ready-to-use result; you need no
second prompt-discovery step:

```jsonc
{
  "launch_id": "<your-uuid>",
  "status": "ready",
  "result": {
    "run_id": "pb_postexp_range_6_53802ff8",
    "chal_id": "pb-postexp-range-6",
    "entry_urls": [ { "name": "…", "url": "http://<host>:<port>", … } ],
    "container_addr": ["172.31.x.y:80"],
    "prompt_level": "l0",
    "task_prompt": "…",              // GUARANTEED non-empty at ready
    "task_prompt_template": "…"
  }
}
```

`ready` is reached only after Cage has validated **all** of: a non-empty
`run_id`, a healthy instance, a reachable target address (host-published
`entry_urls` for a publishing launch, else the docker-network `container_addr`),
and a **non-empty `task_prompt`**. A `failed` body carries a structured
`error` (`{code, message, retryable}`; codes include `startup_failed`,
`unhealthy`, `entry_urls_unavailable`, `prompt_unavailable`) and its partial
resources are cleaned up. A terminal *operation* failure is still `200` with
`status=failed`. Only auth / unknown-id are non-200 (401 / 404).

**Idempotent on `cage_run_id`.** Repeating the POST with the same params returns
the **same** operation and never builds a second container set: `202` while
pending, `200` with the terminal representation once ready/failed/closed. This
is what makes a lost `202` safe: query the stable `status_url` or just re-POST.
Reusing a `cage_run_id` with **different launch params** is `409
idempotency_conflict`. (Operational knobs that don't change the container set,
such as `ttl` and the advertised host, are not part of the fingerprint, so re-POSTing with a
fresh lease is not a conflict.)

**Durable across restart.** Each operation is persisted (atomically, under
`TARGET_SERVER_LAUNCH_OPS_DIR`, default `./.cage_launch_ops/<namespace>/`)
before any work is enqueued, and reconciled against Docker on startup: an
interrupted launch is purged (by the `cage.run_id` label) and re-driven under
the same id, a `ready` op whose containers a graceful shutdown removed becomes
`failed` (`instance_gone`, retryable), and a `ready` op whose containers
survived a crash stays valid. **Cancellation intent survives the restart too**:
an interrupted `closing` op (or one flagged `cancel_requested`) is finalized,
torn down and confirmed absent, never re-driven.

**`DELETE /launches/{id}`** idempotently cancels and tears down, crucially even
before an internal `run_id` exists (it purges by the `cage.run_id` label), the
case `DELETE /launch?run_id=` cannot handle. `closed` is a **fenced,
evidence-backed** terminal state: it is written only once (a) any in-flight
provisioning worker is quiescent and (b) a final `cage.run_id` resource probe
confirms absence. Two consequences for callers:

- If a worker is still provisioning, or a first teardown left resources behind,
  DELETE returns **`202` with `status=closing`** (honour `Retry-After`); poll the
  status URL until `200` `closed`. A worker that finishes provisioning *after* a
  cancellation tears down what it built and can never flip the op to `ready`.
- If cleanup fails, the op stays `closing` with a retryable `cleanup_incomplete`
  error rather than falsely reporting `closed`; a repeated DELETE retries the
  teardown. Repeating DELETE is idempotent throughout `closing` and after
  `closed`.

### `GET /launch/{chal_id}`

Synchronous. Simple same-host / interactive use; for orchestration prefer
`POST /launches` above. Query params: `force_recreate`, `parallel_mode`,
`target_scope`, `cage_run_id`, `network_only`, `prompt_level`
(`l0`/`l1`/`l2`, binds the task-briefing hint tier to this instance for
`GET /prompt`, defaulting to the server's `--prompt-level`), and `ttl`
(seconds; lease this instance, see
[external access](#external-access-serving-an-agent-that-is-not-on-this-host)).
The audience is
**always derived from the request**; there is no `?audience=` override. Two
changes for callers:

- **Response gains an `entry_urls` field** (only populated for external
  callers). Each entry is `{name, role, url, host, port, protocol}`.
- For external callers, an existing per-challenge stack launched with a
  different audience is **force-recreated** so bindings stay consistent. For
  `target_scope=per_agent` (the realistic external case) every launch creates
  a fresh stack anyway, so this is a no-op.

URL scheme inference (in `_build_entry_urls`):

| Protocol | Internal port | Rendered URL |
|---|---|---|
| `tcp` | 443, 8443 | `https://<host>:<port>` |
| `tcp` | 80, 8080, 8000, 8888, 5000, 3000 | `http://<host>:<port>` |
| any other | any other | `<host>:<port>` (raw, e.g. `1.2.3.4:32101` for SSH) |

### `GET /prompt/{run_id}`

The agent-facing **task briefing** for a launched instance: the same framing a
CAGE-managed agent receives as `{task_instruction}`, produced by the challenge's
own `build_prompt` so it matches `cage run` (task, target address, the
`final_answer` output contract). Fetch it right after `/launch` so your agent
starts with full context. Audience-gated like `/launch` and `/submit`.

```json
{
  "run_id": "pb-prestashop_269c3cc7",
  "chal_id": "pb-prestashop",
  "task_profile": "single_target",
  "prompt_level": "l0",
  "task_prompt": "You are an autonomous penetration testing agent ... http://prestashop:80 ...",
  "task_prompt_template": "You are an autonomous ... {{APPLICATION_TARGETS}} ..."
}
```

- `task_prompt` is **ready to use**: this instance's live target address(es) are
  filled in (post-exploitation entry hosts resolve to the instance's live inner
  IPs). Hand it straight to your agent. SDK: `Instance.task_prompt()`.
- `task_prompt_template` is the same briefing with the target address(es) shown as
  placeholder tokens (`{{APPLICATION_TARGETS}}` / `{{ENTRY_HOST}}`), i.e. the
  un-filled template.
- `prompt_level` is the hint tier **bound to this instance at launch**
  (`GET /launch?prompt_level=l1`), falling back to the server's `--prompt-level`
  default (`l0`). Set per-launch so instances on one server can differ without
  restarting serve. `l0` = no hints; `l1`/`l2` progressively reveal vuln location
  / topology. It is a launch parameter recorded on the instance; whoever drives
  the launch chooses it. *(For post-exploitation, `l1`/`l2` hints depend on subnet
  substitutions resolved at run time; if they can't be resolved, the briefing
  falls back to no hint rather than leaking a template placeholder.)*

Both strings are empty if the benchmark exposes no `build_prompt`.

::: tip The serve briefing omits the "your environment / tooling" section
A `cage run` briefing describes the workspace and pre-installed tools cage gives
the agent (a "## Environment" section: Kali container, `nmap`/`sqlmap`/`fscan`/…).
In serve mode **cage does not launch the agent**, so it does not provide that
environment; you bring your own. The serve renderer flags the sample as
self-hosted and the benchmark drops that section, leaving the task, the target
address, the reporting contract, and the scoring rules. Everything about *what*
to do stays; only the "here are the tools we installed for you" part is removed.
:::

### `POST /submit/{run_id}`

Score a submission against a **still-running** instance: the piece that lets an
external agent self-operate the whole loop (list → launch → attack → **submit**
→ close) without any cage-side agent runtime. The server gathers live evidence
against the target and scores it with the challenge's benchmark scorer, then
persists an inspectable run under `.cage_runs` (viewable in `cage inspect`).

- `run_id` (path): the launched instance id from `/launch`.
- **Size cap**: a body over the server's upload limit (1 GiB by default,
  `TARGET_SERVER_MAX_SUBMIT_UPLOAD_BYTES`) is rejected with **413**, before any
  scoring work. The archive is unpacked in memory, so this bounds what a caller
  can make the server allocate. Submit the `final_answer/` reports, not the
  workspace.
- Body: `multipart/form-data` with an `agent_output` file, a `tar.gz`/`zip`
  whose `final_answer/` dir holds the agent's per-vuln report JSONs (web
  challenges). **Omit the file entirely for marker-only post-exploitation
  ranges**: those are scored from live target state, not agent output, so for
  post-exploitation `submit` is simply the "I'm done, score my markers" call.
- **One submission per instance.** The verdict locks in on the first call; a
  repeat for the same `run_id` returns it unchanged with
  `already_submitted: true` (an agent cannot resubmit to fish for a pass). To
  make another attempt, `launch` a fresh instance.
- `?close=true`: tear the instance down after scoring (default: keep it up,
  e.g. for inspection, but it is still one submission either way).
- Auth: same audience gating as `/launch` (bearer for external callers).
- Identity: an optional `X-Client-Id` header (else the bearer token) scopes the
  submission to that agent's experiment run. Each external agent gets ONE
  experiment `.cage_runs/serve__<agent_id>/serve/`; every submit appends a
  trial. Agent runtime and LLM trajectory are external, so those inspector
  panels are simply empty.

`gather` needs the target alive, so scoring runs **before** any `?close=true`
teardown. The scorer reaches the challenge's `evaluator` sidecar over the
isolated docker network at its inner IP (network-only), never a host port.

Response (`200 OK`):

```jsonc
{
  "status": "scored",
  "run_id": "pb-prestashop_ab12cd34",
  "chal_id": "pb-prestashop",
  "scores": {
    "agent_pentest_bench": {
      "value": 0.0,                       // successful / total vulns
      "answer": "",
      "explanation": "Passed 0/4 vulnerabilities by their declared scoring signals.",
      "metadata": {
        "verifier_successful": 1,          // live verify.py passes
        "needs_judge": true,               // some vuln needs the LLM_judge signal
        "judge_available": false,          // no judge model configured server-side
        "results": [ { "vuln_id": "prestashop-001", "verifier_status": true, ... } ]
      }
    }
  },
  "run_dir": ".../.cage_runs/serve__<agent_id>/serve",
  "closed": false
}
```

**Scoring signals (and when you need a model).** Each vuln declares how it is
judged: `verifier` (the evaluator runs the upstream `verify.py`, **no model**)
and/or `LLM_judge` (an offline LLM verdict, **needs a model**). A vuln passes
only when *all* its declared signals pass.

**Reading progress without caring which kind you have.** Every verdict's
`metadata` carries a uniform triple, whatever the challenge:

```jsonc
"objective_kind":     "marker",   // or "vulnerability"
"objective_achieved": 2,
"objective_total":    12          // == the objective_count from GET /challenges
```

`value == objective_achieved / objective_total`. The type-specific fields remain
alongside it for existing readers — `successful`/`total` and, for ranges,
`markers_passed`/`markers_total` plus `rooted`. Note that for a range
`successful`/`total` counts **hosts compromised**, which is NOT the score's
denominator: range-7 scored 0.75 on markers 3/4 while holding all 3 hosts. Use
the `objective_*` triple and that ambiguity cannot bite you.

- **Post-exploitation ranges** score from docker-cp markers: no model, no
  agent output. Serve them with nothing extra.
- **web_exploit_bench** vulns declare `["verifier", "LLM_judge"]`, so full
  scoring needs a judge model, but `cage benchmark serve <benchmark>` reads the
  benchmark's **declared default** automatically (agent_pentest_bench →
  `deepseek-v4-pro`, from its `default_web_exploit.yml`), so
  `cage benchmark serve agent_pentest_bench` scores web out of the box. Override
  with `--judge-model <model_id>` (or set `TARGET_SERVER_JUDGE_JSON`). The id is
  resolved from the repo's `config/models.yml`, and the model is injected
  **server-side**, never carried on the submission. If no judge is resolved,
  `LLM_judge` vulns report "no judge model configured" and cannot pass.

### Re-judging a scored submission: `POST /rescores` · `GET /rescores/{run_id}`

Scoring has two halves, and only one of them can fail for reasons that say
nothing about the agent. The **verifier** half ran against the live target and
is frozen on disk. The **`LLM_judge`** half is a model call — and a model call
dies on an expired API key, a rate limit, or a model being swapped out. When
that happens, every `LLM_judge` vuln reports `no_match` and the submission
scores 0 for an operational reason.

These two endpoints re-run the judge half over the frozen inputs. **No instance
needs to be alive**: the findings and the verifier evidence were persisted at
submit time precisely so this could happen later, so a submission whose target
was torn down weeks ago re-judges exactly like one still running.

```bash
# start a re-judge (202, work runs in the background)
curl -H "Authorization: Bearer <token>" -X POST http://<host>:8000/rescores \
     -H 'Content-Type: application/json' \
     -d '{"run_id": "<launch id>"}'

# poll it
curl -H "Authorization: Bearer <token>" http://<host>:8000/rescores/<launch id>
```

- **Operation id is the `run_id`.** Re-POSTing while one is still pending
  returns that same operation rather than starting a competing re-judge of the
  same submission. Re-POSTing a *finished* one starts a fresh re-judge — that is
  the point of the endpoint, and it differs from `/launches`, where a terminal
  operation is returned verbatim.
- `judge_models` (body, optional) — score with specific judge model id(s).
  Default: the server's own judge (`--judge-model` / `TARGET_SERVER_JUDGE_JSON`).
  With no judge resolved at all the request is a **400**: re-scoring without one
  would quietly replace a judged verdict with a verifier-only one.
- **What is not re-run.** Verifier verdicts are reproduced from the frozen
  evidence, never re-executed — re-running them would need the target back.
- `grader_drift: true` in the result means the challenge's **verifier scripts or
  ground truth changed** since this submission was graded. The frozen verdicts
  still reflect the old ones, and no re-judge can fix that — only a fresh launch
  and a new submission would.
- `inputs_unchanged: false` means the frozen evidence or the findings were
  modified on disk after scoring, so the new pass is not comparable to the one
  it supersedes.
- **Nothing is destroyed.** Each re-judge is appended as a new scoring pass:
  the superseded verdict keeps its own file under `scores/passes/` and stays in
  `record.json`'s `passes`. What moves is `canonical_pass_id` and the canonical
  `scores/<scorer>.json`, so readers at the stable path see the current verdict.
- **A submission with no agent findings is still re-scorable.** Re-scoring runs
  the benchmark's whole `score()`, not only the judge, so a marker-based
  post-exploitation range — which carries no findings and never consults a judge
  — recomputes its verdict from the frozen evidence. That is in fact the case
  offline re-scoring serves best: after a fix to the scoring logic, every past
  submission can be recomputed without relaunching a single target.
- Operations live in memory. With none in flight, `GET` answers from the
  submission record itself (flagged `from_record: true`), so a serve restart —
  or a query long after the work finished — still gets a real answer.
- Auth — same audience gating as `/submit`. This is an **operator** action: it
  never alters the agent's findings, only how they were judged, so the
  one-submission-per-instance rule is untouched.

### `DELETE /launch/{chal_id}?run_id=<id>`

Stop and remove exactly one running instance. ``run_id`` is **required**: a
DELETE always targets one instance, never "the challenge". Idempotent: deleting
an already-gone instance returns ``200`` with a no-op message. Same audience
auth as launch.

### `GET /instances`

List every instance this server currently has running: the observability
endpoint for a fleet of concurrent agents. Public-safe (no flag / verify /
scoring secret), audience-gated like the rest.

Query params:
- `probe`: `true` runs a live per-instance docker health check (slower);
  default reports the cached `lifecycle_state`.

Response (`200 OK`): a JSON array. Every field below is always present; several
are nullable:

| Field | Type | Notes |
|---|---|---|
| `run_id` | `string` | Instance handle for `/prompt`, `/submit`, `DELETE /launch`. Equals `chal_id` under `per_challenge` and for static targets, so don't assume they differ |
| `chal_id` | `string` | |
| `benchmark` | `string` | `""` if unknown |
| `category` | `string` | `""` if unknown |
| `target_scope` | `string` | `per_challenge` \| `per_agent` \| `""` |
| `audience` | `string` | `internal` \| `external` \| `""` |
| `cage_run_id` | `string` | `""` when standalone, never null |
| `lifecycle_state` | `string` | `launching` \| `waiting_health` \| `running` \| `restarting` \| `stopping` \| `cleanup` \| `""`. Treat unknown values as in-transition; new states may be added |
| `healthy` | `boolean \| null` | **Tri-state.** Non-null only with `?probe=true`; null also means the probe errored. Null is "unknown", never "unhealthy" |
| `created_at` | `string \| null` | RFC 3339 UTC, second precision (`2026-07-19T16:12:57Z`). Not monotonic; see the note below |
| `uptime_s` | `number \| null` | Seconds since `created_at`, rounded to 0.1. Server-computed, so no clock sync needed |
| `network_name` | `string \| null` | |
| `network_subnet` | `string \| null` | CIDR |
| `network_gateway` | `string \| null` | |
| `service_count` | `integer` | |
| `entry_urls` | `EntryUrl[]` | Always `[]` for `audience=internal`, and `[]` under the default `network_only=true`. Empty ≠ broken |
| `container_addr` | `string[]` | `"ip:port"` on the isolated docker network |
| `entry_url_source` | `string` | Where the host in `entry_urls` came from: `host_header` (derived from the address you reached the API at, the default), `flag` (`--public-host`), `host_ip_env`, `route`, or `fallback`. `""` when there are no entry_urls |
| `public` | `boolean` | True when the instance holds a host-published entry, so it occupies one of `--max-public-instances`. See [external access](#external-access-serving-an-agent-that-is-not-on-this-host) |
| `ttl_s` | `integer \| null` | Lease requested at launch (`?ttl=<seconds>`); `null` = runs until `DELETE` |
| `ttl_remaining_s` | `number \| null` | Seconds left on the lease, or `null` when launched without one |

```jsonc
[
  {
    "run_id": "SIYUCMS_a3f9c1d0",
    "chal_id": "SIYUCMS",
    "benchmark": "agent_pentest_bench",
    "category": "real-world-web",
    "target_scope": "per_agent",
    "audience": "external",
    "cage_run_id": "",
    "lifecycle_state": "running",
    "healthy": null,                        // null unless ?probe=true
    "created_at": "2026-07-19T16:12:57Z",   // RFC 3339, UTC
    "uptime_s": 137.4,
    "network_name": "cage_SIYUCMS_a3f9c1d0",
    "network_subnet": "172.31.4.0/24",
    "network_gateway": "172.31.4.1",
    "service_count": 1,
    "entry_urls": [
      {"name": "web", "role": "web", "url": "http://192.0.2.10:33001",
       "host": "192.0.2.10", "port": 33001, "protocol": "http"}
    ],
    "container_addr": ["172.31.4.2:80"],
    "entry_url_source": "host_header",
    "public": true,
    "ttl_s": 600,
    "ttl_remaining_s": 462.6
  }
]
```

::: danger Breaking change: `created_at` is now a string
`created_at` used to be a **float** of Unix epoch seconds (`1770000000.123`).
It is now an RFC 3339 UTC string (`"2026-07-19T16:12:57Z"`).

If you parse this field, update your client; a numeric decoder will now fail
on it:

```python
datetime.fromisoformat(inst["created_at"].replace("Z", "+00:00"))
```

```go
time.Parse(time.RFC3339, inst.CreatedAt)   // string, was float64
```

The rest of the API is unchanged. `uptime_s` is unaffected: it was, and still
is, a number of seconds.
:::

::: warning `created_at` is not monotonic
It is stamped when the launch *starts* and re-stamped when it *completes*. An
instance polled mid-launch can therefore report a `created_at` that moves
**forward** between polls, with `uptime_s` dropping back toward 0.

If you only need "how long has this been up", prefer `uptime_s`; it is computed
server-side and needs no clock agreement between you and the server.
:::

Poll this endpoint to see what is up, whose it is (`cage_run_id`), and where each
target lives (`container_addr`).

---

## Concurrency & isolation

**How do many agents hit the benchmark at once?** Each launch is its own
isolated world: you do not share, you do not queue.

`GET /launch/{chal}?target_scope=per_agent` (the **default**) mints, per call:

- a **unique `run_id`** (`{chal}_{uuid8}`), your handle for every later call,
- its **own docker network** (own subnet + gateway), and
- its **own fresh containers**.

So *M* agents can each `launch` the **same** challenge concurrently and get *M*
fully-independent copies. They cannot see each other (separate networks, the
network-only default keeps nothing on the host), scoring is per-instance
(`/submit/{run_id}` targets exactly your copy), and there is **no server-side
serialization**: launches run in parallel, bounded only by host docker/CPU/mem
capacity, not by the server.

| scope | instances | when |
|---|---|---|
| `per_agent` (default) | one fresh isolated stack **per launch** | concurrent, independent agents/testers; the normal case |
| `per_challenge` | **one shared** stack, reused across callers | a single operator poking one target; NOT for concurrent scoring |

Rules of thumb for a concurrent fleet:

- Always launch with `target_scope=per_agent`. Treat the returned `run_id` as
  opaque and carry it through `submit` and `close`.
- Identify yourself with an `X-Client-Id` header (or a per-team bearer token):
  each distinct id gets its own scored experiment under
  `.cage_runs/serve__<agent_id>/`, so concurrent teams never mix results.
- Poll `GET /instances` for the live fleet; reconcile against the `run_id`s you
  own and `DELETE` yours when done (idle instances are **not** auto-reaped yet;
  see Limitations).
- There is no built-in per-token quota: N agents launching N heavy stacks is N×
  the host cost. Cap concurrency on the client side, or run separate servers.

---

## Configuring a challenge: `application_service_keys`

The server reads which services are user-facing entries from each challenge's
`challenge.json`. Example (`examples/agent_pentest_bench/datasets/web_exploit_bench/siyucms/challenge.json`):

```jsonc
{
  "compose_target_services": ["web", "evaluator"],   // services to bring up
  "application_service_keys": ["web"],               // ← user-facing entries
  "target_ports": {"web": 80, "evaluator": 9091}
}
```

| Service | In `application_service_keys`? | External audience binding |
|---|---|---|
| `web` | yes | `0.0.0.0:<ext>:80`, anyone can reach |
| `evaluator` | **no** | `127.0.0.1:<ext>:9091`, only callers on the server host |
| `mysql` | **no** | `127.0.0.1:<ext>:3306` |

**Web challenge** → 1 entry: `["web"]`.
**Post-exploitation** with a web foothold and an SSH jump host →
`["entry_web", "ssh_jump"]`. The server will publish both to host and
return both URLs in `entry_urls`.

If `application_service_keys` is empty or missing, **no audience-based
binding restriction kicks in**: every published service binds to `0.0.0.0`
exactly like the legacy behaviour. Add the field to a challenge to opt into
the external isolation guarantee.

---

## Recipes

### Tunnel just enough to a remote tester

```bash
cage benchmark serve agent_pentest_bench \
  --host 0.0.0.0 \
  --port 8000 \
  --external-token "$(cat ~/.cage/external_token)" \
  --public-host                  # address derived from each caller's request
```

Pin the address (`--public-host 203.0.113.9`) only behind a reverse proxy or
NAT. The legacy `TARGET_SERVER_HOST_IP` env var still works and is treated as a
pinned address.

Tester does:

```bash
TOKEN=...
SERVER=https://your.server:8000

curl -sH "Authorization: Bearer $TOKEN" $SERVER/challenges | jq
curl -sH "Authorization: Bearer $TOKEN" \
  "$SERVER/launch/SIYUCMS?target_scope=per_agent" \
  | jq '.entry_urls'
# [{"name":"web","role":"web","url":"http://your.server:32101","host":"your.server","port":32101,"protocol":"tcp"}]
```

Tester pokes `entry_urls[0].url` directly. Scoring channels (`evaluator:9091`)
are unreachable from their machine because they bind to `127.0.0.1` on the
server.

When done:

```bash
RUN_ID=$(curl -sH "Authorization: Bearer $TOKEN" \
  "$SERVER/launch/SIYUCMS?target_scope=per_agent" | jq -r .run_id)
curl -sH "Authorization: Bearer $TOKEN" -X DELETE \
  "$SERVER/launch/SIYUCMS?run_id=$RUN_ID"
```

### Full self-operation loop (external agent, end to end)

The complete PULL contract an external agent drives itself: no cage-side agent
runtime, no trajectory capture, just targets + scoring:

```bash
TOKEN=...; SERVER=https://your.server:8000
H=(-H "Authorization: Bearer $TOKEN" -H "X-Client-Id: team-red")

# 1. discover
curl -s "${H[@]}" $SERVER/challenges | jq -r '.[].id'

# 2. launch an isolated instance (per_agent → unique run_id + isolated network)
L=$(curl -s "${H[@]}" "$SERVER/launch/pb-prestashop?target_scope=per_agent")
RUN_ID=$(jq -r .run_id <<<"$L")
jq '{run_id, container_addr, entry_urls, network_name, network_subnet}' <<<"$L"
#   network-only (default): container_addr=["172.31.x.y:80"], entry_urls=[]
#     → reach the target over the isolated docker network (your VPN/route).
#   or launch with ?network_only=false → entry_urls=["http://your.server:PORT"]
#     → reach it directly on the server's public IP (evaluator stays internal).

# 3. attack the target, produce final_answer/<vuln_id>.json reports, pack them
tar czf sub.tar.gz final_answer/

# 4. submit → score (target still live; keeps running for resubmission)
curl -s "${H[@]}" -X POST -F "agent_output=@sub.tar.gz" \
     "$SERVER/submit/$RUN_ID" | jq '.scores'

# 5. close when done (or submit ?close=true to score-and-close in one call)
curl -s "${H[@]}" -X DELETE "$SERVER/launch/pb-prestashop?run_id=$RUN_ID"
```

Post-exploitation ranges skip the `agent_output` upload at step 4 (they are
scored from live target state): `curl "${H[@]}" -X POST "$SERVER/submit/$RUN_ID"`.

Each agent's submissions accumulate as trials in one experiment
(`.cage_runs/serve__<agent_id>/serve/`), browsable in `cage inspect`.

### Run internal cage workers against the same server

Internal `cage run …` keeps working with **no** Authorization header; it
reaches the server over loopback (when collocated) or over an internal IP
allow-list you set up. Inside cage's `RemoteBackend` no code change is
needed: the request goes out without a bearer, hits rule 2 (loopback) or
rule 4 (legacy) of `resolve_audience()`, and is classified internal.

If you co-locate cage workers and external testers, **always set
`--external-token`** so rule 3 catches non-loopback callers that forget to
authenticate.

### Front it with a reverse proxy

If you put nginx / Caddy / Cloudflare in front of `python -m cage.target.serve`, **the FastAPI
process sees the proxy's IP** (usually `127.0.0.1` for same-host nginx). That
means every proxied request would otherwise be classified as `internal`.
That is catastrophic. Two defences:

1. **Bind `python -m cage.target.serve` to a private interface** the proxy uses, and reject
   `Authorization` headers that don't match. The token-required path
   (rule 1) is still safe.
2. **Do not trust `X-Forwarded-For`**. The current implementation
   deliberately reads `request.client.host` only. If you want to add
   `X-Forwarded-For` support, gate it on a static upstream-proxy IP
   allow-list; never accept the header from arbitrary clients.

---

## Security model

What the external audience mode protects against:

- ✅ External clients reaching scoring sidecars (`evaluator`, …). Under the
  default (network-only) they have **no host port at all**, reachable only on
  the isolated docker network; the host-side scorer routes to them by inner IP.
  Under `?network_only=false` they are pinned to `127.0.0.1` on the host.
- ✅ External clients reaching internal databases (`mysql`, …). Same.
- ✅ Misconfigured callers silently being elevated to external on legacy
  servers: bearer headers are rejected when no token is configured.

What it does **not** protect against:

- ❌ Anyone on the same host as the server. Loopback callers can hit
  `127.0.0.1:<ext_port>` for the scoring sidecar directly. If you have
  untrusted users SSH'd into the server, this design does not help.
- ❌ Network-layer attacks against the entry services themselves. The whole
  point is that `web:80` is reachable from outside; vulnerabilities in the
  exposed web app are not part of the threat model.
- ❌ Replay / brute-force of the token. The token is a static shared secret.
  Rotate periodically; consider per-tester tokens by running multiple
  `python -m cage.target.serve` instances on different ports.
- ❌ Anything the reverse proxy sees. See the recipe above; running behind
  an HTTP proxy without precautions defeats the loopback classification.

---

## Troubleshooting

**External call returns `401 bearer auth not configured on this server`.**
You sent `Authorization: Bearer ...` to a server started **without**
`--external-token`. Either start the server with the flag, or drop the
header.

**External call returns `401 bearer token required for non-loopback callers`.**
The server has a token configured, but your request arrived without an
`Authorization` header and from a non-loopback IP. Add the bearer.

**External call returns `401 invalid bearer token`.**
Token mismatch. Confirm the token on both sides; rotate if you suspect
exposure.

**`entry_urls` is empty even though I'm external.**
Either (a) the challenge's `challenge.json` has no
`application_service_keys`, or (b) the entry services have no
`internal_port` resolved. Check the challenge config; bare `compose_files`
without `target_ports` and without `ports:` in the original compose YAML
won't produce a host-published port.

**External caller reuses a per_challenge instance launched internally and
the bindings look wrong.**
By design, audience-change triggers a force-recreate of per_challenge
stacks. If you saw stale bindings, you may be on a build before this
behaviour landed; confirm `_launch_challenge_impl` contains
`audience changed: ... -> ...` in its `reason` string.

**Background monitor restarts an external instance and it comes back with
the wrong bindings.**
The monitor reads `info.get("audience")` from the instance registry and
passes it to `launch_challenge` explicitly. If you see this anyway, check
that `set_running_instance(...)` is recording `audience` and
`entry_service_keys` (it is, but a future refactor could miss this).

---

## Limitations

- **No idle auto-reap *unless the launch asked for one*.** A `per_agent`
  instance launched without `?ttl=` runs until someone `DELETE`s it, so an agent
  that walks away leaks its stack until the server restarts. Pass `?ttl=<seconds>`
  to lease it (the server reaps it on expiry), or reconcile client-side (track
  your `run_id`s, always close). There is no server-side default lease and no
  ceiling on what a launch may request.
- **No per-token scoping yet.** A bearer token is binary: either you have it
  (external) or you don't. No per-tester quotas, no expiry, no audit trail
  beyond uvicorn's access log.
- **The web console (`GET /`) is a rough operator convenience, not the
  product.** Drive the JSON API programmatically; the console is not maintained
  to the same bar and should not be the path an evaluation depends on.
- **No challenge-level allow-list.** Anyone with the token can launch any
  challenge. If you need to restrict a tester to specific benchmarks, run a
  dedicated `python -m cage.target.serve` instance per scope with its own benchmark-root.
- **No port range to open in a firewall.** Published ports are whatever the
  kernel hands out (ephemeral range), so an external-access deployment cannot
  pre-open a narrow range in a firewall / security group; there is no
  `--port-range` yet.
- **Static port allocation per process.** Ports are assigned from the
  FastAPI process's free-port pool. If you restart the server, the port a
  tester was using will be re-allocated, so they'll need a fresh launch.
- **No HTTPS termination built in.** `python -m cage.target.serve` speaks plain HTTP. For
  public exposure put a TLS-terminating reverse proxy in front and read
  the reverse-proxy caveat in the security section.
