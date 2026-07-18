"""Settings API route."""
from __future__ import annotations

import os
from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse

from fp.config import save_user_config, load_user_config

router = APIRouter()

PROVIDER_MAP = {
    "openai": {"model": "gpt-4o-mini", "env_key": "OPENAI_API_KEY"},
    "minimax": {"model": "minimax/MiniMax-M2.7", "env_key": "MINIMAX_API_KEY", "base": "https://api.minimax.io/v1"},
    "deepseek": {"model": "deepseek/deepseek-chat", "env_key": "DEEPSEEK_API_KEY"},
    "dashscope": {"model": "dashscope/qwen-max", "env_key": "DASHSCOPE_API_KEY"},
    "xiaomi_mimo": {"model": "xiaomi_mimo/MiMo-7B-RL", "env_key": "XIAOMI_MIMO_API_KEY", "base": "https://api.xiaomi.com/v1"},
    "zai": {"model": "zai/glm-4.7", "env_key": "ZAI_API_KEY"},
    "moonshot": {"model": "moonshot/moonshot-v1-8k", "env_key": "MOONSHOT_API_KEY"},
    "volcengine": {"model": "volcengine/doubao-seed-1.6", "env_key": "VOLCENGINE_API_KEY"},
    "tencent": {"model": "tencent/deepseek-v4-pro", "env_key": "TENCENT_API_KEY"},
}


@router.post("/settings", response_class=HTMLResponse)
async def save_settings(
    provider: str = Form(""),
    model: str = Form(""),
    api_key: str = Form(""),
    api_base: str = Form(""),
    exa_key: str = Form(""),
):
    """Save settings to .env file."""
    settings = {}

    if model:
        settings["FP_MODEL"] = model

    if provider and provider in PROVIDER_MAP:
        info = PROVIDER_MAP[provider]
        if api_key:
            settings[info["env_key"]] = api_key
        if not model:
            settings["FP_MODEL"] = info["model"]
        if api_base:
            base_key = info["env_key"].replace("_API_KEY", "_API_BASE")
            settings[base_key] = api_base
        elif "base" in info and not api_base:
            base_key = info["env_key"].replace("_API_KEY", "_API_BASE")
            settings[base_key] = info["base"]
    elif api_key:
        settings["OPENAI_API_KEY"] = api_key

    if exa_key:
        settings["EXA_API_KEY"] = exa_key

    if settings:
        save_user_config(settings)
        # Reload into current env
        for k, v in settings.items():
            os.environ[k] = v

    return HTMLResponse(f'''
        <div class="p-3 bg-green-50 border border-green-200 rounded text-green-700 text-sm">
            ✓ Settings saved. Model: {settings.get("FP_MODEL", "unchanged")}
        </div>
    ''')
