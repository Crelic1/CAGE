"""Model-registry Cage CLI commands."""

from __future__ import annotations

from pathlib import Path

import click

from cage.cli.paths import display_path


def _model_registry_path(models_file: str | None = None) -> Path:
    """Resolve the model registry path using repo-level Cage config."""

    from cage.config import resolve_models_file

    return resolve_models_file(models_file, repo_root=Path.cwd())


def _load_model_registry_yaml(path: Path) -> tuple[dict, dict]:
    """Load ``config/models.yml`` while accepting the legacy flat mapping shape."""

    import yaml

    if path.exists():
        raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    else:
        raw = {}
    if not isinstance(raw, dict):
        raise click.ClickException(f"{path} must contain a YAML mapping")

    if "models" not in raw:
        if raw:
            raw = {"models": raw}
        else:
            raw["models"] = {}
    models = raw.get("models")
    if not isinstance(models, dict):
        raise click.ClickException(f"{path}: models must be a mapping")
    return raw, models


def _write_model_registry_yaml(path: Path, raw: dict) -> None:
    """Persist the model registry with stable YAML ordering for human edits."""

    import yaml

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        yaml.safe_dump(raw, sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )


def _masked_secret(value: object) -> str:
    """Mask API-key-like values for default terminal output."""

    text = str(value or "")
    if not text:
        return ""
    if len(text) <= 8:
        return "<set>"
    return f"{text[:3]}...{text[-4:]}"


def _entry_context_window(entry: dict) -> int | None:
    """The declared context window, accepting the ``context_window_size`` alias."""

    raw = entry.get("max_context_size", entry.get("context_window_size"))
    try:
        value = int(raw)
    except (TypeError, ValueError):
        return None
    return value if value > 0 else None


def _model_entry_key(entry: dict, *, show_secret: bool) -> str:
    """Return the visible key column for one model registry entry."""

    key = entry.get("api_key") or ""
    if not key and isinstance(entry.get("api_keys"), list) and entry["api_keys"]:
        key = entry["api_keys"][0]
    return str(key or "") if show_secret else _masked_secret(key)


def _ensure_model_entry_shape(entry: dict, model_id: str) -> None:
    """Fill all editable model fields before applying CLI overrides."""

    entry.setdefault("provider", "openai")
    entry.setdefault("model", model_id)
    entry.setdefault("agent_model_names", {})
    entry.setdefault("base_url", "")
    entry.setdefault("api_key", "")
    entry.setdefault("auth_source", "")
    entry.setdefault("api_keys", [])
    entry.setdefault("input_cost_per_1m", 0.0)
    entry.setdefault("output_cost_per_1m", 0.0)
    entry.setdefault("timeout", 360)
    entry.setdefault("max_retries", 2)
    entry.setdefault("extra_headers", {})


@click.group(name="model")
def model_group() -> None:
    """List and edit the repo model registry."""


@model_group.command("list")
@click.option(
    "--models",
    "models_file",
    type=click.Path(),
    default=None,
    hidden=True,
    help="Override the repo default model registry.",
)
@click.option("--show-secret", is_flag=True, help="Show API keys instead of masking them.")
def model_list(models_file: str | None, show_secret: bool) -> None:
    """List models from config/models.yml by default."""

    path = _model_registry_path(models_file)
    _raw, models = _load_model_registry_yaml(path)
    click.echo(f"Models: {display_path(path)}")
    click.echo(
        "ID                            Provider   Model                         "
        "Endpoint                         Context   Key"
    )
    click.echo(
        "----------------------------  ---------  ----------------------------  "
        "-------------------------------  --------  --------"
    )
    missing: list[str] = []
    for model_id, entry in sorted(models.items()):
        if not isinstance(entry, dict):
            continue
        endpoint = str(entry.get("base_url") or "")
        window = _entry_context_window(entry)
        if window is None:
            missing.append(str(model_id))
        click.echo(
            f"{str(model_id)[:28]:28s}  "
            f"{str(entry.get('provider') or '')[:9]:9s}  "
            f"{str(entry.get('model') or '')[:28]:28s}  "
            f"{endpoint[:31]:31s}  "
            f"{(f'{window:,}' if window else 'MISSING'):>8s}  "
            f"{_model_entry_key(entry, show_secret=show_secret)}"
        )
    if missing:
        # Surfaced here rather than in a separate check command: an entry
        # without a window will not load, so the list that shows what is
        # registered is also the list that should say what is unusable.
        click.echo()
        click.echo(
            f"{len(missing)} entr{'y' if len(missing) == 1 else 'ies'} cannot be "
            f"loaded until `max_context_size` is set: {', '.join(missing[:8])}"
            f"{' …' if len(missing) > 8 else ''}"
        )
        click.echo(
            "  Find the value: cage model ask <id> --prompt-tokens 500000"
        )
        click.echo(
            "  Then record it: cage model set <id> --max-context-size N"
        )


@model_group.command("show")
@click.argument("model_id")
@click.option(
    "--models",
    "models_file",
    type=click.Path(),
    default=None,
    hidden=True,
    help="Override the repo default model registry.",
)
@click.option("--show-secret", is_flag=True, help="Show API keys instead of masking them.")
def model_show(model_id: str, models_file: str | None, show_secret: bool) -> None:
    """Show one model entry."""

    import yaml

    path = _model_registry_path(models_file)
    _raw, models = _load_model_registry_yaml(path)
    entry = models.get(model_id)
    if not isinstance(entry, dict):
        raise click.ClickException(f"Model {model_id!r} not found in {display_path(path)}")
    visible = dict(entry)
    if not show_secret:
        if "api_key" in visible:
            visible["api_key"] = _masked_secret(visible["api_key"])
        if isinstance(visible.get("api_keys"), list):
            visible["api_keys"] = [_masked_secret(value) for value in visible["api_keys"]]
    click.echo(yaml.safe_dump({model_id: visible}, sort_keys=False, allow_unicode=True))


@model_group.command("set")
@click.argument("model_id")
@click.option(
    "--models",
    "models_file",
    type=click.Path(),
    default=None,
    hidden=True,
    help="Override the repo default model registry.",
)
@click.option(
    "--provider",
    type=click.Choice(["openai", "anthropic", "vllm"]),
    default=None,
    help="Provider/protocol family.",
)
@click.option("--model", "model_name", default="", help="Model name sent to the upstream endpoint.")
@click.option(
    "--agent-model-name",
    "agent_model_names",
    multiple=True,
    metavar="AGENT=MODEL",
    help="Agent-specific CLI model name, e.g. claude_code=deepseek-v4-pro[1m].",
)
@click.option(
    "--endpoint",
    "--base-url",
    "base_url",
    default="",
    help="OpenAI/Anthropic-compatible API base URL.",
)
@click.option("--api-key", default="", help="API key value or environment placeholder.")
@click.option(
    "--auth-source",
    default="",
    help="Host credential directory for supported subscription auth.",
)
@click.option(
    "--input-cost-per-1m",
    type=float,
    default=None,
    help="Input token cost per 1M tokens.",
)
@click.option(
    "--output-cost-per-1m",
    type=float,
    default=None,
    help="Output token cost per 1M tokens.",
)
@click.option("--timeout", type=int, default=None, help="Model request timeout in seconds.")
@click.option("--max-retries", type=int, default=None, help="Upstream retry count.")
@click.option(
    "--max-context-size",
    type=int,
    default=None,
    help=(
        "REQUIRED for every model. The endpoint's context window in tokens — "
        "agents use it to decide when to compact, and CAGE refuses to load a "
        "registry entry without it. This belongs to the deployment, not the "
        "model: read it out of an oversized request's rejection rather than "
        "off the model card, since a server's advertised limit is not always "
        "the one it enforces. Guess low if you must — too small only compacts "
        "early, too large means the agent never compacts at all."
    ),
)
@click.option(
    "--reserved-context-size",
    type=int,
    default=None,
    help=(
        "Optional. How much of the window to hold back for the reply, for CLIs "
        "that want it stated separately instead of deriving it."
    ),
)
@click.option(
    "--rl-reward-sink",
    default=None,
    help=(
        "Enable RL mode: URL the trainer's reward sink listens on. When set, "
        "LLM calls carry an X-Trial-Id header and each trial's reward is POSTed "
        "here. Pass an empty string to disable RL mode again."
    ),
)
def model_set(
    model_id: str,
    models_file: str | None,
    provider: str | None,
    model_name: str,
    agent_model_names: tuple[str, ...],
    base_url: str,
    api_key: str,
    auth_source: str,
    input_cost_per_1m: float | None,
    output_cost_per_1m: float | None,
    timeout: int | None,
    max_retries: int | None,
    max_context_size: int | None,
    reserved_context_size: int | None,
    rl_reward_sink: str | None,
) -> None:
    """Create or update one model entry."""

    path = _model_registry_path(models_file)
    raw, models = _load_model_registry_yaml(path)
    entry = models.get(model_id)
    if entry is None:
        entry = {}
        models[model_id] = entry
    if not isinstance(entry, dict):
        raise click.ClickException(f"{path}: models.{model_id} must be a mapping")
    _ensure_model_entry_shape(entry, model_id)

    if provider is not None:
        entry["provider"] = provider
    if model_name:
        entry["model"] = model_name
    for item in agent_model_names:
        if "=" not in item:
            raise click.ClickException(f"--agent-model-name must use AGENT=MODEL, got {item!r}")
        agent_name, agent_model_name = item.split("=", 1)
        agent_name = agent_name.strip()
        agent_model_name = agent_model_name.strip()
        if not agent_name or not agent_model_name:
            raise click.ClickException(
                f"--agent-model-name must use non-empty AGENT=MODEL, got {item!r}"
            )
        aliases = entry.setdefault("agent_model_names", {})
        if not isinstance(aliases, dict):
            raise click.ClickException(
                f"{path}: models.{model_id}.agent_model_names must be a mapping"
            )
        aliases[agent_name] = agent_model_name
    if base_url:
        entry["base_url"] = base_url
    if api_key:
        entry["api_key"] = api_key
    if auth_source:
        entry["auth_source"] = auth_source
    if input_cost_per_1m is not None:
        entry["input_cost_per_1m"] = input_cost_per_1m
    if output_cost_per_1m is not None:
        entry["output_cost_per_1m"] = output_cost_per_1m
    if timeout is not None:
        entry["timeout"] = timeout
    if max_retries is not None:
        entry["max_retries"] = max_retries
    if max_context_size is not None:
        entry["max_context_size"] = max_context_size
    if reserved_context_size is not None:
        entry["reserved_context_size"] = reserved_context_size
    if rl_reward_sink is not None:
        # ``--rl-reward-sink ""`` clears the key (back to a normal model);
        # any non-empty value turns RL mode on.
        if rl_reward_sink:
            entry["rl_reward_sink"] = rl_reward_sink
        else:
            entry.pop("rl_reward_sink", None)

    if not entry.get("max_context_size") and not entry.get("context_window_size"):
        raise click.ClickException(
            f"Model {model_id!r} needs --max-context-size (the endpoint's context\n"
            f"window, in tokens). Agents use it to decide when to compact, and a\n"
            f"registry entry without it will not load. It is a property of the\n"
            f"deployment rather than the model, so read it off the endpoint: send\n"
            f"an oversized request and take the limit from the rejection. Guess low\n"
            f"if you must — too small only compacts early, too large means the\n"
            f"agent never compacts at all."
        )
    _write_model_registry_yaml(path, raw)
    click.echo(f"Model {model_id!r} written to {display_path(path)}")


@model_group.command("ask")
@click.argument("model_id")
@click.option(
    "--models",
    "models_file",
    type=click.Path(),
    default=None,
    hidden=True,
    help="Override the repo default model registry.",
)
@click.option(
    "--prompt-tokens", type=int, default=0,
    help="Roughly how much filler to put in the prompt. Pass more than the "
         "window you are checking and the endpoint will refuse the request "
         "during validation, before generating anything.",
)
@click.option("--max-tokens", type=int, default=16, help="Reply reservation to request.")
@click.option(
    "--timeout", type=float, default=None,
    help="Request timeout in seconds. Defaults to a value that scales with "
         "--prompt-tokens, since a large prompt has to finish uploading "
         "before it can be refused.",
)
def model_ask(
    model_id: str,
    models_file: str | None,
    prompt_tokens: int,
    max_tokens: int,
    timeout: float | None,
) -> None:
    """Send one request to a model's endpoint and print what came back.

    Useful for checking that credentials and routing work at all, and for
    finding an endpoint's context window: ask with a prompt larger than the
    window and read the limit out of the refusal.

    Nothing here interprets the reply. Servers word their limits differently
    and some apply more than one length check, answering with whichever one
    your request happened to trip — a number picked out automatically can be
    several times too large, and writing that into the registry causes exactly
    the runaway context this field exists to prevent. Read it yourself, then
    record it with `cage model set <id> --max-context-size N`.
    """

    from cage.models.endpoint import ModelConfig
    from cage.models.probe import ask_endpoint

    path = _model_registry_path(models_file)
    _raw, models = _load_model_registry_yaml(path)
    entry = models.get(model_id)
    if not isinstance(entry, dict):
        raise click.ClickException(f"Model {model_id!r} not found in {display_path(path)}")

    # Built here rather than through the registry loader: an entry with no
    # window declared is precisely the one you want to ask about, and the
    # loader refuses to return it.
    model = ModelConfig(
        id=model_id,
        provider=str(entry.get("provider") or "openai"),
        model=str(entry.get("model") or model_id),
        base_url=str(entry.get("base_url") or ""),
        api_key=str(entry.get("api_key") or ""),
        extra_headers={
            str(k): str(v) for k, v in (entry.get("extra_headers") or {}).items()
        },
    )

    filler = f"{prompt_tokens:,} tokens of filler" if prompt_tokens else "a one-word prompt"
    click.echo(f"{model_id} -> {model.base_url}  ({filler}, max_tokens={max_tokens})")
    reply = ask_endpoint(
        model, prompt_tokens=prompt_tokens, max_tokens=max_tokens, timeout=timeout,
    )
    click.echo(f"HTTP {reply.status if reply.reached else '(no response)'}")
    click.echo(reply.body.strip()[:4000])
