"""LLM abstraction layer — model-agnostic completions via LiteLLM.

Supports 100+ providers (OpenAI, DeepSeek, MiniMax, Qwen, MiMo, etc.)
with automatic env-var-based API key resolution.

Setup (one-time):
  1. cp .env.example .env
  2. Edit .env — set FP_MODEL and your provider's API key
  3. fp discover — done

.env is loaded from your current working directory automatically.
No export needed — just edit .env and run fp.

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

import json
import os

from dotenv import load_dotenv, find_dotenv
import litellm

DEFAULT_MODEL = "gpt-4o-mini"

# Auto-load .env from current working directory.
# python-dotenv's default find_dotenv() walks up from this module's __file__,
# which breaks when installed via pipx (module is in venv, not cwd).
# Fix: explicitly search from CWD using pathlib.
from pathlib import Path as _Path

_env_path = _Path.cwd() / ".env"
if _env_path.exists():
    load_dotenv(_env_path, override=True)
else:
    # Fallback: try default search (works for `pip install -e .` dev mode)
    load_dotenv()

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


def extract_json(text: str) -> str:
    """Strip markdown code fences from LLM responses and return raw JSON.

    Some providers (MiniMax, DeepSeek, etc.) wrap JSON in ```json ... ```
    even when response_format=json_object is requested.
    Also handles literal control characters (newlines, tabs) inside JSON strings.
    """
    import re
    # Try to extract content from markdown code fences
    match = re.search(r"```(?:json)?\s*\n?(.*?)\n?\s*```", text, re.DOTALL)
    if match:
        text = match.group(1).strip()
    else:
        text = text.strip()

    # Fix control characters: replace literal newlines/tabs inside JSON strings
    # with escaped versions. Walk through and track whether we're inside a string.
    result = []
    in_string = False
    i = 0
    while i < len(text):
        ch = text[i]
        if ch == '"' and (i == 0 or text[i - 1] != '\\'):
            in_string = not in_string
            result.append(ch)
        elif in_string and ch == '\n':
            result.append('\\n')
        elif in_string and ch == '\t':
            result.append('\\t')
        elif in_string and ch == '\r':
            result.append('\\r')
        else:
            result.append(ch)
        i += 1

    return ''.join(result)


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


def completion_json(
    model: str = "",
    messages: list[dict] | None = None,
    temperature: float = 0.7,
    retries: int = 3,
    **kwargs,
) -> dict:
    """Call LLM and return parsed JSON dict. Retries on parse failure.

    Some providers (MiniMax, DeepSeek) occasionally return malformed JSON
    even with response_format=json_object. This retries up to `retries` times.
    """
    import sys
    last_err = None
    for attempt in range(retries):
        try:
            resp = completion(
                model=model,
                messages=messages,
                response_format={"type": "json_object"},
                temperature=temperature,
                **kwargs,
            )
            raw = resp.choices[0].message.content
            return json.loads(extract_json(raw))
        except (json.JSONDecodeError, KeyError, IndexError) as e:
            last_err = e
            if attempt < retries - 1:
                print(f"  ⚠ JSON parse failed (attempt {attempt + 1}/{retries}): {e}", file=sys.stderr)
                continue
    raise last_err
