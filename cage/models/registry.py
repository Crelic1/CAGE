"""Model registry loading from Cage configuration files."""

from __future__ import annotations

from pathlib import Path

import yaml

from cage.contracts.coerce import optional_float
from cage.contracts.env import expand_env_refs
from cage.contracts.exceptions import ConfigError
from cage.models.endpoint import ModelConfig

_KNOWN_FIELDS = frozenset((
    "provider", "model", "base_url", "api_key", "api_keys", "auth_source",
    "timeout", "max_retries", "input_cost_per_1m", "output_cost_per_1m",
    "extra_headers", "agent_model_names",
    # Context-window capabilities, promoted out of ``extra`` to typed fields.
    # ``context_window_size`` is an accepted alias for ``max_context_size``.
    "max_context_size", "reserved_context_size", "context_window_size",
    # RL training integration: the reward sink URL (presence ⇒ RL mode on).
    "rl_reward_sink",
))


def _optional_int(value: object) -> int | None:
    """Coerce a declared token count to a positive int, or None if unset."""

    if value is None:
        return None
    n = int(value)
    if n <= 0:
        raise ValueError(f"context size must be a positive integer, got {value!r}")
    return n


def _missing_context_size_message(model_id: str) -> str:
    """Explain why Cage refuses to guess an endpoint's context window.

    Agents compact their conversation before it outgrows the window. Every CLI
    we drive takes that budget as an absolute token count, so somebody has to
    supply the number — and the only party who knows it is whoever stood the
    endpoint up. Cage used to let it stay unset and hope the agent's own
    default was close enough; when it wasn't, the agent never compacted and the
    trial died at the wall with no indication that a knob had been missed.
    """

    return (
        f"config/models.yml::{model_id} is missing ``max_context_size``.\n"
        f"\n"
        f"  Set it to the largest prompt this endpoint actually accepts, in tokens:\n"
        f"\n"
        f"    {model_id}:\n"
        f"      max_context_size: 262144\n"
        f"\n"
        f"  This is a property of the deployment, not of the model, which is why\n"
        f"  Cage will not guess it. The same weights served by two different hosts\n"
        f"  can enforce very different limits, and a server's advertised limit can\n"
        f"  be far larger than the one it enforces — so the model card, and even\n"
        f"  ``GET /models``, may both disagree with reality.\n"
        f"\n"
        f"  To find the real number, send a deliberately oversized request and read\n"
        f"  the limit back out of the rejection; most servers name it. Agents use\n"
        f"  this value to decide when to compact, so an over-estimate is the\n"
        f"  dangerous direction: the agent will never compact and will run the\n"
        f"  conversation straight into the wall.\n"
        f"\n"
        f"  Optionally set ``reserved_context_size`` to hold room back for the\n"
        f"  reply; unset means the headroom is derived from the request itself."
    )


def load_models(path: str | Path) -> dict[str, ModelConfig]:
    """Load model endpoint declarations from ``models.yml``.

    The loader accepts either a top-level ``models:`` mapping or a direct
    mapping of model ids to endpoint fields. Credential pools are normalized so
    older single-key consumers can keep reading ``api_key`` while trial-level
    scheduling can rotate over ``api_keys``.
    """

    models_path = Path(path)
    if not models_path.is_file():
        # The single most common first-run failure. Left as a bare
        # FileNotFoundError it reached the user as a raw traceback with no hint
        # that the file is meant to be created from the committed example.
        raise ConfigError(
            f"Model registry not found: {models_path}\n"
            f"  Create it from the committed example:\n"
            f"    cp {models_path.parent / 'models.example.yml'} {models_path}\n"
            f"  Then fill in the endpoints and keys you want to evaluate against."
        )
    raw = expand_env_refs(yaml.safe_load(models_path.read_text()))
    if not isinstance(raw, dict):
        raise ConfigError(
            f"Invalid models file: {models_path}\n"
            f"  Expected a YAML mapping, optionally under a top-level `models:` key."
        )

    models_section = raw.get("models", raw)
    result: dict[str, ModelConfig] = {}

    for model_id, cfg in models_section.items():
        if not isinstance(cfg, dict):
            continue
        key_pool = [
            str(k).strip()
            for k in (cfg.get("api_keys") or [])
            if str(k).strip()
        ]
        explicit_key = str(cfg.get("api_key", "") or "").strip()
        effective_key = explicit_key or (key_pool[0] if key_pool else "")
        if "max_concurrent" in cfg:
            raise ValueError(
                f"config/models.yml::{model_id} sets ``max_concurrent`` - this "
                "field has moved to ``agents.<i>.max_concurrent`` in "
                "project.yml. Each agent declares its own concurrency budget "
                "against the model it uses; concurrency is no longer a "
                "property of the model id."
            )
        agent_model_names = cfg.get("agent_model_names") or {}
        if not isinstance(agent_model_names, dict):
            raise ValueError(
                f"config/models.yml::{model_id}.agent_model_names must be a mapping"
            )
        max_context_size = _optional_int(
            cfg.get("max_context_size", cfg.get("context_window_size"))
        )
        if max_context_size is None or max_context_size <= 0:
            raise ConfigError(_missing_context_size_message(model_id))
        result[model_id] = ModelConfig(
            id=model_id,
            provider=cfg.get("provider", "anthropic"),
            model=cfg.get("model", model_id),
            agent_model_names={
                str(k): str(v)
                for k, v in agent_model_names.items()
                if str(k).strip() and str(v).strip()
            },
            base_url=cfg.get("base_url", ""),
            api_key=effective_key,
            api_keys=key_pool,
            auth_source=str(cfg.get("auth_source", "") or "").strip(),
            timeout=cfg.get("timeout", 360),
            max_retries=cfg.get("max_retries", 2),
            input_cost_per_1m=optional_float(cfg.get("input_cost_per_1m")),
            output_cost_per_1m=optional_float(cfg.get("output_cost_per_1m")),
            extra_headers={
                str(k): str(v)
                for k, v in (cfg.get("extra_headers") or {}).items()
            },
            max_context_size=max_context_size,
            reserved_context_size=_optional_int(cfg.get("reserved_context_size")),
            rl_reward_sink=str(cfg.get("rl_reward_sink", "") or "").strip(),
            extra={k: v for k, v in cfg.items() if k not in _KNOWN_FIELDS},
        )

    return result
