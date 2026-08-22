# Spreading Load Across Keys and Endpoints

A long run makes thousands of LLM calls. One API key, or one self-hosted
endpoint, is often not enough — you hit a rate limit, burn a daily quota, or
saturate a single vLLM box while other boxes sit idle.

CAGE solves this by **rotating**: it hands each trial a different credential or
a different endpoint, cycling through whatever you gave it. There are two
rotation axes, and they compose:

| Axis | What rotates | Where you configure it |
|---|---|---|
| **Key pool** | several API keys against **one** endpoint | `api_keys` in `config/models.yml` |
| **Source pool** | several **whole endpoints** (different URL, key, upstream model name) | `sources` in your experiment YAML, or `--model-source` |

Use a key pool when you have multiple accounts on the same provider. Use a
source pool when you have several machines serving an interchangeable model.

A source pool also carries **per-endpoint concurrency**: each box declares how
many trials it can take at once, and a box that is bigger takes proportionally
more work. You can change those numbers — or add a box — **while the run is
executing**, with [`cage tune`](#retuning-a-running-run).

## Rotation is per-trial, not per-request

This is the single most important thing to understand, because it determines
whether rotation helps you at all.

CAGE picks the credential **once, when a trial starts**, and that trial keeps it
for its entire conversation — every LLM call the agent makes, start to finish.
It does not rotate between individual requests.

That is deliberate. Provider prompt caches are keyed per credential, so a
conversation that hopped keys mid-flight would miss the cache on every call and
cost you both money and latency. Pinning per trial keeps each conversation warm
while still spreading load across the run as a whole.

The consequence: **rotation spreads load, it does not rescue a failing trial.**
If a key hits its rate limit halfway through a trial, that trial fails with
`MODEL_RATE_LIMITED` or `MODEL_QUOTA_EXHAUSTED` — CAGE does not retry it on a
different key. Size your pool so no single key gets pushed to its limit, rather
than expecting failover to catch you.

## Key pool: several accounts, one endpoint

In `config/models.yml`, use **`api_keys`** (plural) instead of `api_key`:

```yaml
models:
  gpt-5.5-pool:
    provider: openai
    model: gpt-5.5
    base_url: https://api.openai.com/v1
    api_keys:
      - ${OPENAI_API_KEY}
      - ${OPENAI_API_KEY_2}
      - ${OPENAI_API_KEY_3}
```

Then use `gpt-5.5-pool` as a normal model id — nothing else in your experiment
YAML changes. Trial 0 gets the first key, trial 1 the second, trial 2 the third,
trial 3 wraps back to the first.

Notes:

- **`api_keys` overrides `api_key`.** If both are present, the pool wins. Pick
  one; don't set both.
- **`${ENV_VAR}` is expanded when the registry loads**, so keep the secrets in
  your environment rather than in the file. Be careful: an **undefined variable
  expands to an empty string silently** — no error. If one key in a pool is
  quietly empty, every trial assigned to that slot fails to authenticate while
  the others succeed, which looks like flaky infrastructure. Verify with
  `env | grep OPENAI_API_KEY` before a long run.
- **`cage model set` only writes the scalar `api_key`.** Key pools have to be
  hand-edited into `config/models.yml`.
- **Preflight only validates the first key.** A dead key in slot 2 is not
  caught before the run starts; it surfaces as failed trials.

## Source pool: several endpoints behind one name

A source pool puts several *registered* model entries behind one logical name.
Each source is a full endpoint, so they may differ in `base_url`, `api_key`,
upstream model name, and their own `api_keys` pool.

Register each endpoint normally:

```yaml
# config/models.yml
models:
  glm-5.2-box1:
    provider: openai
    model: glm-5.2
    base_url: http://192.0.2.11:8000/v1
    api_key: ${VLLM_KEY}

  glm-5.2-box2:
    provider: openai
    model: glm-5.2
    base_url: http://192.0.2.12:8000/v1
    api_key: ${VLLM_KEY}
```

Then declare the pool on the agent in your experiment YAML:

```yaml
agents:
  - kind: claude_code
    models:
      - id: glm-5.2                 # logical key — REQUIRED with `sources`
        sources: [glm-5.2-box1, glm-5.2-box2]
```

Or, without touching YAML, from the CLI:

```bash
cage run mybench \
  --model glm-5.2 \
  --model-source glm-5.2-box1 \
  --model-source glm-5.2-box2
```

Three rules the loader enforces:

- **An entry with `sources` must set an explicit `id`.** That id is a *logical
  key*: it names the run (run directory, labels, scores) and does **not** itself
  need to be a registered model. This is what keeps a two-endpoint run grouped as
  one result set instead of splitting into two.
- **All sources must share one wire protocol.** You cannot mix an `anthropic`
  endpoint with an `openai` one in a single pool — the run translates uniformly,
  so a mid-run protocol switch is rejected at load time rather than failing
  halfway through.
- **All sources must serve the same upstream model.** Which box a trial lands on
  depends on which one has free capacity at that moment, not on a reproducible
  index — so a pool holding two different models would make your results depend
  on scheduling timing, and you could never reproduce them. To compare two
  models, run two runs.

## Per-endpoint concurrency

Boxes are rarely the same size. Give each one a capacity and CAGE will respect
it — `id:N` in the source list, or the longhand `{id, concurrency}`:

```yaml
      - id: glm-5.2
        sources:
          - glm-5.2-box1:16       # a big machine
          - glm-5.2-box2:4        # a small one
          - glm-5.2-box3          # no number ⇒ uncapped
```

```bash
cage run mybench --model glm-5.2 \
  --model-source glm-5.2-box1:16 \
  --model-source glm-5.2-box2:4
```

**Taking a slot is what chooses the endpoint.** A trial waits for *some* box to
have room, and whichever has room is the one it uses. Three things follow, and
they are the whole reason the feature is shaped this way:

- **Capacity decides share.** With 16 and 4 slots, the big box gets four times
  the trials. A positional round-robin would have split them evenly and thrashed
  the small one.
- **A slow box de-weights itself.** Its slots stay occupied, so it stops being
  handed work until it catches up. Nothing needs to detect that it is slow.
- **`0` drains.** A box set to zero receives no new trials while the ones
  already on it run to completion. That is how you retire a machine without
  interrupting anything.

A source with no number is **uncapped**: it never blocks on its own, and is
bounded only by the agent's `max_concurrent` and the run's `max_trials_global`.
CAGE does not invent a number for a box whose size it cannot know.

The banner prints the pool and says which cap is actually binding:

```
         endpoints: glm-box1 x16  glm-box2 x4  glm-box3 x32   (3 sources, 52 slots total)
       concurrency: 40 trials in flight — bounded by max_concurrent (endpoint slots=52, …)
```

and the progress line carries the live occupancy, so a saturated run and an idle
one no longer look alike:

```
progress [########--] 34% 960/2820 done, running=47/52, failed=12, …
```

## Retuning a running run

A long run's right answer changes while it is running: a box gets scaled up, a
new one comes online, one starts misbehaving. Restarting to act on that costs
every in-flight trial — which on a benchmark whose trials run for hours is the
expensive part.

`cage tune` is its own command, the way `docker update` is to `docker run` —
it starts nothing, it adjusts something already running:

```bash
# 1. a new machine is up — register it (it need not have existed at launch)
cage model set glm-box3 --base-url http://192.0.2.13:8000/v1 --model glm-5.2

# 2. scale box1 up, bring box3 online, retire box2 — the run never stops
cage tune mybench --run-id R1 \
  --model-source glm-box1:32 \
  --model-source glm-box3:16 \
  --model-source glm-box2:0
```

```
Tuning run R1  [claude_code:glm-5.2:stateless]
  .cage_runs/claude_code:glm-5.2:stateless/R1

  glm-box1             16 -> 32
  glm-box2             4 -> drained (0)   drains; in-flight trials finish
  glm-box3             unset -> 16

Written to .cage_runs/claude_code:glm-5.2:stateless/R1/endpoint_concurrency.json
Applies to the next trial that starts; in-flight trials are unaffected.
```

Add `--dry-run` to see that table without writing anything.

To undo everything and go back to the concurrency the run launched with:

```bash
cage tune mybench --run-id R1 --clear
```

```
  glm-box1     32 -> 16   (launch value)
  glm-box2     drained (0) -> 4   (launch value)
```

The run records its launch pool itself, so this always has somewhere to return
to — and it is why the state file below is the complete picture rather than a
list of edits.

### Where the state lives

`cage tune` does not reach into the running process; it writes a file the run
re-reads, because the two are separate processes:

```
.cage_runs/<agent>/<run-id>/
├── runtime_status.json        # the run reporting outward: alive, pid, heartbeat
└── endpoint_concurrency.json  # the world instructing the run: these capacities
```

```json
{
  "agents": { "claude_code:glm-5.2:stateless": { "sources": { "glm-box1": 32, "glm-box2": 0 } } },
  "launch": { "claude_code:glm-5.2:stateless": { "glm-box1": 16, "glm-box2": 4 } }
}
```

`agents` is live state — what the run acts on and what a tune edits. `launch` is
written once at startup and never modified; `cage tune --clear` restores from it.
`cat` the file to see exactly what a run is doing right now.

Do not hand-edit it: writes must be atomic (the CLI does tmp + rename), and a
worker reading a half-saved file is precisely the failure this avoids.

What to expect:

- **Only the flags you type are applied.** A tune never re-reads the project
  YAML, so values still sitting in that file cannot quietly revert an earlier
  tune.
- **It takes effect at the next trial start**, which is the one moment where the
  change is unambiguous. Trials already running keep the endpoint they hold.
- **Capacity is required.** `--model-source box3:16` is accepted; a bare
  `--model-source box3` is refused. At launch a bare id means "uncapped", but in
  a tune it is almost always a dropped number, and silently doing nothing would
  be the worst answer.
- **The run must be alive.** Tuning a stopped run tells you to use `--resume`
  instead of writing a file nobody will read.
- **`--clear` reverts everything**, back to the launch configuration. Use
  it on its own — it cannot be combined with
  `--model-source` because restoring and changing in one command has no
  sensible reading.
- **Only the box's size is tunable, not what the run is.** `--model`, the sample
  set, `--difficulty`, `--max-rounds` and friends are refused rather than
  ignored — changing them mid-flight would produce results that no longer match
  the run's own plan.
- **A machine that came online after launch can be added.** Register it in
  `config/models.yml`, then name it in a tune — CAGE re-reads the registry, so
  the endpoint does not have to have existed when the run started. It must pass
  the same interchangeability checks as the rest of the pool (one protocol, one
  upstream model); a mismatch is refused, not silently accepted. An id the
  registry does not know is refused by the CLI before anything is written.



## Composing both axes

When a source in the pool itself declares `api_keys`, both axes are in play at
once, but they are chosen differently — and the difference matters when you are
reasoning about a run after the fact:

```
endpoint = whichever source has a free slot   (capacity, decided at runtime)
key      = pool[i % n_keys]                   (trial index, deterministic)
```

The key still advances by trial index, so a long run spreads evenly across
accounts. The endpoint does not, because capacity is the thing you actually want
it to track. One consequence is worth stating plainly: **which box a given trial
ran on is not predictable in advance, and is not reproducible across re-runs.**
It is recorded per trial (see below), so you can always find out after the fact —
and the same-upstream-model rule above is what keeps that from affecting your
results.

## Confirming it's working

When a pool has more than one entry, each trial logs the slot it was pinned to:

```
Trial <id> on source glm-5.2-box2 of 3 (glm-5.2 -> glm-5.2-box2)
Trial <id> pinned to api_key pool slot 0/3
```

A tune that lands is logged too, so the run's own log shows when capacity
changed and why the distribution shifted:

```
run control: claude_code:glm-5.2:stateless glm-box1: 16 -> 32
run control: claude_code:glm-5.2:stateless glm-box2: 4 -> drained
```

No such line means the pool has one entry or none — usually a typo in
`api_keys`, or an `${ENV_VAR}` that expanded to empty and got dropped.

The rotated credential reaches the endpoint via the **in-container proxy**, not
via the agent's own environment. The proxy holds the key and attaches it to
every upstream request, so rotation works uniformly no matter which agent CLI
is running and whether or not that CLI has its own key handling.

## Current limits

Worth knowing before you plan around them:

- **No failover.** A rate-limited or quota-exhausted trial terminates; it is not
  retried on another key or source.
- **No per-key health tracking.** An exhausted key stays in the rotation and
  keeps getting assigned trials for the rest of the run.
- **No automatic health-based eviction.** A box that has gone slow de-weights
  itself (its slots stay busy), but a box that is *failing fast* keeps accepting
  trials. Drain it yourself with `--model-source <id>:0`.
- **Capacity is per run, not per machine.** Two runs that each give `box1` 16
  slots will together push 32 at it. Nothing coordinates across runs.
- **Adoption is per-run, not global.** A tune adds the endpoint to the run you
  named; other runs in flight are untouched and need their own tune.

## Related

- [Models](/models) — the registry, entry shape, and full field table.
- [Experiment YAML Reference](/reference/project-yml) — `agents[].models` in full.
- [The CLI](/cli-design) — `cage model`, `cage run`.
