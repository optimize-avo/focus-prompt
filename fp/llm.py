"""LLM abstraction layer — model-agnostic completions via LiteLLM.

Supports 100+ providers (OpenAI, DeepSeek, MiniMax, Qwen, MiMo, etc.)
with automatic env-var-based API key resolution.

Model selection priority:
  1. Explicit `model` argument (from --model flag or MCP param)
  2. FP_MODEL environment variable
  3. Default: gpt-4o-mini

Regional endpoint overrides (Singapore) for Chinese providers:
  - MiniMax: api.minimax.io (Singapore) instead of api.minimax.chat (China)
  - MiMo: api.xiaomi.com/v1 (Singapore)

Override any endpoint via provider-specific env vars:
  MINIMAX_API_BASE, XIAOMI_MIMO_API_BASE, etc.
"""
from __future__ import annotations

import os

import litellm

DEFAULT_MODEL = "gpt-4o-mini"

# Regional API base overrides — Singapore endpoints for Chinese providers.
# Override any via env var (e.g. MINIMAX_API_BASE=https://custom.endpoint/v1).
_REGIONAL_API_BASES: dict[str, str] = {
    "minimax": os.getenv(
        "MINIMAX_API_BASE",
        "https://api.minimax.io/v1",  # Singapore (international)
    ),
    "xiaomi_mimo": os.getenv(
        "XIAOMI_MIMO_API_BASE",
        "https://api.xiaomi.com/v1",  # Singapore
    ),
}


def resolve_model(model: str = "") -> str:
    """Resolve model name from explicit arg, env, or default."""
    return model or os.getenv("FP_MODEL", DEFAULT_MODEL)


def completion(
    model: str = "",
    messages: list[dict] | None = None,
    response_format: dict | None = None,
    temperature: float = 0.7,
    **kwargs,
):
    """Call LLM via LiteLLM with automatic provider detection.

    Args:
        model: Model identifier (e.g. "gpt-4o-mini", "minimax/MiniMax-M2.1").
               Resolved via resolve_model() if empty.
        messages: Chat messages list.
        response_format: JSON response format (default: {"type": "json_object"}).
        temperature: Sampling temperature.
        **kwargs: Forwarded to litellm.completion() (api_base, api_key, etc.).

    Returns:
        LiteLLM ModelResponse with .choices[0].message.content
    """
    resolved = resolve_model(model)

    if messages is None:
        messages = []

    if response_format is None:
        response_format = {"type": "json_object"}

    # Auto-detect regional endpoint for known providers
    for provider, base in _REGIONAL_API_BASES.items():
        if resolved.startswith(f"{provider}/"):
            kwargs.setdefault("api_base", base)
            break

    return litellm.completion(
        model=resolved,
        messages=messages,
        response_format=response_format,
        temperature=temperature,
        **kwargs,
    )
