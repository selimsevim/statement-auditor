"""Anthropic client, on-disk response cache, and structured-output helper.

`cached_structured` is shared by both LLM passes. It:
  * keys an on-disk cache on (model, system, user, schema, max_tokens) so re-runs
    are free — the cache key uses the *original* prompt, so a run that needed a
    retry still produces a cache hit next time;
  * forces schema-valid JSON via `messages.parse()` (structured outputs), which
    Haiku 4.5 and Sonnet 5 both support;
  * on refusal / truncation / validation failure, retries once with the error
    appended, then raises LLMError so the caller can log-and-skip.

Haiku 4.5 does not support the `effort` parameter or adaptive thinking, so this
helper passes neither — just a plain structured call.
"""
from __future__ import annotations

import hashlib
from typing import Any, TypeVar

import anthropic
from pydantic import BaseModel

from .config import Config, require_api_key

T = TypeVar("T", bound=BaseModel)


class LLMError(RuntimeError):
    """Raised when a structured call fails after all retries."""


def _usage_record(model: str, schema: str, salt: str, *, cached: bool,
                  error: bool = False, usage: Any = None) -> dict[str, Any]:
    """One row for the optional usage_sink, so callers can tally calls/tokens.

    Cached hits and parse failures carry zero token counts (no API call was
    billed). Thinking tokens are not billed as a separate field by the API —
    on Claude they are part of output_tokens — so they are not recorded here.
    """
    return {
        "model": model, "schema": schema, "salt": salt,
        "cached": cached, "error": error,
        "input_tokens": int(getattr(usage, "input_tokens", 0) or 0),
        "output_tokens": int(getattr(usage, "output_tokens", 0) or 0),
        "cache_read_input_tokens": int(getattr(usage, "cache_read_input_tokens", 0) or 0),
        "cache_creation_input_tokens": int(getattr(usage, "cache_creation_input_tokens", 0) or 0),
    }


def get_client() -> anthropic.Anthropic:
    """Anthropic client. Reads ANTHROPIC_API_KEY from the environment (or .env)."""
    require_api_key()  # fail fast with clear guidance if unset
    return anthropic.Anthropic()


def _cache_key(model: str, system: str, user: str, schema: str, max_tokens: int, salt: str) -> str:
    h = hashlib.sha256()
    for part in (model, system, user, schema, str(max_tokens), salt):
        h.update(part.encode("utf-8"))
        h.update(b"\x00")
    return h.hexdigest()


def cached_structured(
    cfg: Config,
    *,
    model: str,
    system: str,
    user: str,
    response_model: type[T],
    max_tokens: int,
    client: anthropic.Anthropic | None = None,
    use_cache: bool = True,
    retries: int = 1,
    cache_salt: str = "",
    thinking: dict[str, Any] | None = None,
    usage_sink: list[dict[str, Any]] | None = None,
) -> T:
    """Return a validated `response_model` instance for one structured call.

    Caches successful results on (model, prompt hash, cache_salt). `cache_salt`
    is folded into the cache key but NOT sent to the API — so identical prompts
    can be sampled independently (e.g. median-of-3 scoring) with each sample
    cached separately, making re-runs deterministic. Raises LLMError after
    exhausting `retries`.

    `thinking` is passed through to the API only when non-None (e.g.
    `{"type": "disabled"}` for the combined scorer); it is deliberately NOT part
    of the cache key, so existing keys — and the committed cache — are unchanged.
    Each distinct request shape lives under its own `response_model` schema
    namespace, so there is no cross-contamination. `usage_sink`, when provided,
    receives one record per invocation (cache hit, live call, or failure) so
    callers can tally call counts and token usage.
    """
    schema_name = response_model.__name__
    key = _cache_key(model, system, user, schema_name, max_tokens, cache_salt)
    cache_file = cfg.path("cache_dir") / f"{schema_name}_{key}.json"

    if use_cache and cache_file.exists():
        if usage_sink is not None:
            usage_sink.append(_usage_record(model, schema_name, cache_salt, cached=True))
        return response_model.model_validate_json(cache_file.read_text(encoding="utf-8"))

    client = client or get_client()
    attempt_user = user
    last_err: Exception | None = None
    extra: dict[str, Any] = {"thinking": thinking} if thinking is not None else {}

    for _ in range(retries + 1):
        try:
            msg = client.messages.parse(
                model=model,
                max_tokens=max_tokens,
                system=system,
                messages=[{"role": "user", "content": attempt_user}],
                output_format=response_model,
                **extra,
            )
            if msg.stop_reason == "refusal":
                raise LLMError("model refused the request")
            obj = msg.parsed_output
            if obj is None:
                raise LLMError(f"no parsed output (stop_reason={msg.stop_reason})")
            if use_cache:
                cache_file.parent.mkdir(parents=True, exist_ok=True)
                cache_file.write_text(obj.model_dump_json(indent=2), encoding="utf-8")
            if usage_sink is not None:
                usage_sink.append(_usage_record(
                    model, schema_name, cache_salt, cached=False, usage=getattr(msg, "usage", None)))
            return obj
        except (anthropic.AuthenticationError, anthropic.PermissionDeniedError):
            raise  # credential problems are not retryable — surface immediately
        except Exception as exc:  # noqa: BLE001 — validation / truncation / transient
            last_err = exc
            attempt_user = (
                f"{user}\n\nYour previous response was invalid "
                f"({type(exc).__name__}: {exc}). Return corrected, schema-valid JSON."
            )

    if usage_sink is not None:
        usage_sink.append(_usage_record(model, schema_name, cache_salt, cached=False, error=True))
    raise LLMError(f"failed after {retries + 1} attempt(s): {last_err}")
