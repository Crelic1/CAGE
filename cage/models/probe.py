"""Send one request to a model endpoint and report exactly what came back.

There is no interpretation here on purpose. The question this usually answers —
"how large a prompt does this endpoint accept?" — is tempting to automate, and
the automation is where it goes wrong: servers word their limits differently,
some apply more than one length check and answer with whichever one your probe
happened to trip, and a number read out of the wrong check can be several times
too large. Writing that number into the registry would cause the exact failure
a declared window exists to prevent, quietly.

So this reports and stops. Ask with a prompt too large to fit, read the limit
out of the reply yourself, and record it with ``cage model set``.
"""
from __future__ import annotations

from dataclasses import dataclass

import httpx

from cage.models.endpoint import ModelConfig


@dataclass(frozen=True)
class EndpointReply:
    """One round-trip to a model endpoint, unedited."""

    model_id: str
    #: HTTP status, or ``None`` when the request never got an answer.
    status: int | None
    #: Response body as received, or the transport error when there is none.
    body: str
    #: How many tokens of filler the request carried.
    prompt_tokens: int

    @property
    def reached(self) -> bool:
        return self.status is not None


def _speaks_anthropic(model: ModelConfig) -> bool:
    base = (model.base_url or "").lower()
    return "/anthropic" in base or "api.anthropic.com" in base


def _upstream_model_name(model: ModelConfig) -> str:
    """The name to send upstream, minus any ``[1m]``-style context suffix.

    Those suffixes are a hint to certain agent CLIs, not part of the name the
    endpoint knows, and sending one can be refused for the wrong reason.
    """
    import re

    return re.sub(r"\[[^\]]*\]$", "", model.model or model.id).strip()


def default_timeout_for(prompt_tokens: int) -> float:
    """A timeout that survives the upload it is being asked to wait for.

    The main reason to send a huge prompt is to have it refused, but the
    refusal still arrives only after the whole thing has been uploaded and
    tokenised. A fixed timeout therefore fails precisely on the request you
    most wanted to see, so it grows with the payload.
    """
    return 120.0 + 60.0 * (max(0, prompt_tokens) / 100_000)


def ask_endpoint(
    model: ModelConfig,
    *,
    prompt_tokens: int = 0,
    max_tokens: int = 16,
    timeout: float | None = None,
) -> EndpointReply:
    """Send one request and hand back the raw reply.

    ``prompt_tokens`` is roughly how much filler to put in the prompt; pass a
    number larger than the window you are checking and the endpoint will refuse
    the request during validation, before generating anything. ``timeout``
    defaults to something proportional to that size.
    """
    if timeout is None:
        timeout = default_timeout_for(prompt_tokens)
    if not (model.base_url or "").strip():
        return EndpointReply(model.id, None, "no base_url (subscription/OAuth entry)", 0)
    if not (model.api_key or "").strip():
        return EndpointReply(model.id, None, "no API key resolved for this entry", 0)

    content = "word " * prompt_tokens if prompt_tokens > 0 else "hi"
    anthropic = _speaks_anthropic(model)
    url = (model.base_url or "").rstrip("/") + (
        "/v1/messages" if anthropic else "/chat/completions"
    )
    headers = {"Content-Type": "application/json"}
    if anthropic:
        headers["x-api-key"] = model.api_key
        headers["anthropic-version"] = "2023-06-01"
    else:
        headers["Authorization"] = f"Bearer {model.api_key}"
    headers.update(model.extra_headers or {})

    payload = {
        "model": _upstream_model_name(model),
        "max_tokens": max_tokens,
        "messages": [{"role": "user", "content": content}],
    }
    try:
        with httpx.Client(timeout=timeout, trust_env=False) as client:
            response = client.post(url, headers=headers, json=payload)
        return EndpointReply(model.id, response.status_code, response.text, prompt_tokens)
    except Exception as exc:  # noqa: BLE001
        return EndpointReply(model.id, None, f"{type(exc).__name__}: {exc}", prompt_tokens)


__all__ = ["EndpointReply", "ask_endpoint"]
