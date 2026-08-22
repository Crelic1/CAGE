# Models

CAGE reads model endpoints from one repo-level registry. The registry is **not**
benchmark-local and **not** committed — it holds your keys and endpoints, so it
stays on your machine.

## Where the registry lives

`config/cage.yml` names the registry file; it defaults to `config/models.yml`:

```yaml
# config/cage.yml
models_file: config/models.yml
```

The file is git-ignored. Create it from the committed example, then edit it with
`cage model` (never hand-maintain benchmark-local `models.yml` files):

```bash
cp config/models.example.yml config/models.yml
```

## Editing with `cage model`

```bash
cage model list
cage model show gpt-5.5
cage model set gpt-5.5 \
  --provider openai \
  --model gpt-5.5 \
  --endpoint https://api.openai.com/v1 \
  --api-key '${OPENAI_API_KEY}'
```

`cage model` is the front end for the registry a run reads — see
[The CLI › cage model](/cli-design).

## The entry shape

`config/models.example.yml` documents the full shape; a minimal
OpenAI-compatible entry is:

```yaml
models:
  gpt-5.5:
    provider: openai
    model: gpt-5.5
    agent_model_names: {}
    base_url: https://api.openai.com/v1
    api_key: ${OPENAI_API_KEY}
    api_keys: []
    auth_source: ""
    input_cost_per_1m: 0.0
    output_cost_per_1m: 0.0
    timeout: 360      # default; omit to accept it
    max_retries: 2
    extra_headers: {}
```

| Field | Meaning |
|---|---|
| `provider` | `openai`, `vllm`, or `sglang` (OpenAI protocol); `anthropic` (Anthropic protocol); `gemini` / `google` (Google Generative Language API, for the `gemini_cli` agent). Selects the wire protocol. |
| `model` | model name sent upstream |
| `agent_model_names` | optional per-agent CLI model names, keyed by agent kind |
| `base_url` | API base URL |
| `api_key` / `api_keys` | a single key, or a pool CAGE pins per-trial round-robin — see [Key & Endpoint Rotation](/model-rotation) |
| `auth_source` | host credential directory for supported subscription auth |
| `input_cost_per_1m` / `output_cost_per_1m` | prices used to estimate `max_cost` when the provider reports no cost |
| `timeout` / `max_retries` | upstream request timeout (default `360`) and retry count |
| `extra_headers` | headers attached to every upstream model request |
| `max_context_size` (alias `context_window_size`) | **Required.** The endpoint's context window, in tokens. Agents compact their conversation before it outgrows the window, and every CLI CAGE drives takes that budget as an absolute token count — so CAGE passes this straight through (`claude_code`, `codex`, `kimi_code`, `qwen_code`). It is a property of the *deployment*, not the model: the same weights on two hosts can enforce very different limits, and a server's advertised limit is not always the one it enforces. CAGE will not guess — a missing value is a load-time error. See [Choosing the value](#choosing-max_context_size). |
| `reserved_context_size` | optional; how much of the window to hold back for the reply, for CLIs that want it spelled out separately rather than deriving it (`kimi_code`). Most CLIs pick their own reply ceiling and subtract it themselves, so leaving this unset is normal. |
| `rl_reward_sink` | RL-mode switch: URL an external trainer's reward sink listens on. Set it and every LLM call carries an `X-Trial-Id` header and each trial's reward is POSTed here; unset ⇒ an ordinary model. Also settable via `cage model set --rl-reward-sink`. |

### Choosing `max_context_size`

The number you want is the largest prompt the endpoint will actually accept —
which is often **not** the number on the model card.

Read it out of the endpoint rather than looking it up. Send a deliberately
oversized request; most servers name their limit in the rejection, and that
rejection costs nothing because it happens before any generation:

```
This model's maximum context length is 262144 tokens. However, you requested …
Input length (500013 tokens) exceeds the maximum allowed length (224314 tokens).
```

Do not trust a server's self-report. One endpoint in our own registry answers
`GET /models` with `max_model_len: 1048576` while refusing anything past
~224k — the model was built for a 1M window, the server was started with far
less. The advertised figure describes the weights; only the rejection
describes the deployment.

If you have to guess, **guess low**. Too small only makes the agent compact
sooner than it had to. Too large means it never compacts at all: the CLI keeps
appending until the endpoint refuses the request outright, and a long trial
dies at the wall with nothing to show for the hours it spent.

> `cage model set --provider` only accepts `openai` / `anthropic` / `vllm`. To
> register a `gemini` / `google` / `sglang` endpoint, hand-edit
> `config/models.yml` (or copy an example entry) — the loader accepts them even
> though the `set` CLI does not.

The complete field table is in the
[Experiment YAML Reference](/reference/project-yml).

## Things worth knowing

**Protocol follows `provider`.** `openai`, `vllm`, and `sglang` speak the OpenAI
protocol; `anthropic` speaks the Anthropic protocol; `gemini` / `google` speak
the Google Generative Language API (`generateContent`, for the `gemini_cli`
agent). The in-container proxy translates when an agent and its model disagree,
so a Claude Code agent can drive an OpenAI-protocol endpoint and vice versa.

**`${ENV_VAR}` is expanded at load time.** Keep secrets in the environment and
reference them, rather than pasting keys into the file:

```bash
export OPENAI_API_KEY=...
```

**Keep endpoint identity separate from agent launch strings.** A model's `model`
is the upstream name; some agents need a decorated variant. Express that with
`agent_model_names` instead of forking the endpoint:

```yaml
models:
  deepseek-v4-pro:
    provider: anthropic
    model: deepseek-v4-pro
    agent_model_names:
      claude_code: deepseek-v4-pro[1m]      # only Claude Code gets the suffix
    base_url: https://api.deepseek.com/anthropic
    api_key: ${DEEPSEEK_API_KEY}
```

**Endpoints on the Docker host must be container-reachable.** If a model endpoint
runs on the same host as CAGE, bind it to `0.0.0.0` or a Docker-reachable host
IP. Plain `host.docker.internal` is not portable on Linux unless the container
gets a host-gateway mapping. To egress through a host proxy, set
`proxy.upstream_http_proxy` (see [Configuring the proxy](/reference/project-yml#proxy)).

**Concurrency is not a model property.** Put `max_concurrent` on the agent
(`agents[].max_concurrent`), not in the model registry.

## Related

- [Quick Start](/getting-started/) — register one model and run a trial.
- [Key & Endpoint Rotation](/model-rotation) — spread a run's load over several
  API keys (`api_keys`) or several endpoints (`sources`).
- [The CLI › cage model](/cli-design).
- [Experiment YAML Reference](/reference/project-yml) — full field tables.
