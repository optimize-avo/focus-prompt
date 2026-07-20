"""Settings API route."""
from __future__ import annotations

import csv
import io
import json
import os
from fastapi import APIRouter, Form
from fastapi.responses import HTMLResponse, StreamingResponse

from fp.config import save_user_config
from fp.web.deps import get_state

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
        elif "base" in info:
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


# ─── Scoring Export Endpoints ─────────────────────────────────────────────────


@router.get("/export/scores-csv")
async def export_scores_csv(request: Request):
    """Export scored prompts as CSV download."""
    state = get_state()
    if not state:
        return HTMLResponse('<p class="text-red-600">No project found.</p>')

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["id", "focus", "prompt", "brand_answer_snippet", "ai_answer_snippet", "score", "method", "explanation"])

    for focus in state.focuses:
        for prompt in focus.prompts:
            if prompt.overall_score > 0:
                writer.writerow([
                    f"{focus.name}-{prompt.text[:30]}",
                    focus.name,
                    prompt.text,
                    "",  # brand_answer_snippet (first 200 chars)
                    "",  # ai_answer_snippet (first 200 chars)
                    f"{prompt.overall_score:.2f}",
                    "llm",
                    f"service_match={prompt.service_match:.0f} mention={prompt.mention_likelihood:.0f}",
                ])

    content = output.getvalue()
    return StreamingResponse(
        iter([content]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=scores.csv"},
    )


@router.get("/export/scores-json")
async def export_scores_json(request: Request):
    """Export scored prompts as JSON download."""
    state = get_state()
    if not state:
        return HTMLResponse('<p class="text-red-600">No project found.</p>')

    scored = []
    for focus in state.focuses:
        for prompt in focus.prompts:
            if prompt.overall_score > 0:
                scored.append({
                    "id": f"{focus.name}-{prompt.text[:30]}",
                    "focus": focus.name,
                    "prompt": prompt.text,
                    "brand_answer": "",
                    "ai_answer": "",
                    "score": prompt.overall_score,
                    "service_match": prompt.service_match,
                    "mention_likelihood": prompt.mention_likelihood,
                    "mode": prompt.mode.value,
                    "intent": prompt.intent.value,
                    "needs_review": prompt.needs_review,
                    "method": "llm",
                    "explanation": f"service_match={prompt.service_match:.0f} mention={prompt.mention_likelihood:.0f}",
                })

    content = json.dumps(scored, indent=2, ensure_ascii=False)
    return StreamingResponse(
        iter([content]),
        media_type="application/json",
        headers={"Content-Disposition": "attachment; filename=scores.json"},
    )
