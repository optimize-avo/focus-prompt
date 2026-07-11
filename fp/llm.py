"""LLM abstraction layer — model-agnostic completions via LiteLLM.

Supports 100+ providers (OpenAI, DeepSeek, MiniMax, Qwen, MiMo, etc.)
with automatic env-var-based API key resolution.

Setup (one-time):
  1. cp .env.example .env
  2. Edit .env — set FP_MODEL and your provider's API key
  3. fp discover — done

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
from pathlib import Path

from dotenv import load_dotenv
import litellm

DEFAULT_MODEL = "gpt-4o-mini"

# Auto-load .env from project root (no-op if file doesn't exist)
_ENV_PATH = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(_ENV_PATH)

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


def validate_model(model: str) -> None:
    """Validate model string and print helpful error if misconfigured."""
    if not model or "/" not in model and model == DEFAULT_MODEL:
        return  # basic model like "gpt-4o-mini" — skip prefix check
    # Check if API key env var exists for the provider
    provider = model.split("/")[0] if "/" in model else ""
    key_map = {
        "minimax": "MINIMAX_API_KEY",
        "xiaomi_mimo": "XIAOMI_MIMO_API_KEY",
        "deepseek": "DEEPSEEK_API_KEY",
        "dashscope": "DASHSCOPE_API_KEY",
        "zai": "ZAI_API_KEY",
        "moonshot": "MOONSHOT_API_KEY",
        "volcengine": "VOLCENGINE_API_KEY",
        "tencent": "TENCENT_API_KEY",
        "openai": "OPENAI_API_KEY",
    }
    env_var = key_map.get(provider)
    if env_var and not os.getenv(env_var):
        import sys
        print(
            f"⚠  FP_MODEL={model!r} requires {env_var} to be set.\n"
            f"   Add {env_var}=your-key to .env or export it.",
            file=sys.stderr,
        )


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
    validate_model(resolved)

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
