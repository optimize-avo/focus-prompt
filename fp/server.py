"""MCP Server — Focus Prompt Research Tool for OpenCode.

⚠️  DEPRECATED — Web app only mode
====================================
This MCP server is DEPRECATED as of 2026-07-22. focus-prompt is now a web app only.

SKIP THIS FILE during development. Do NOT add new features here.
All new development goes to fp/web/ and the FastAPI app.

The entry point `fp-mcp` has been removed from pyproject.toml.
This file is kept for reference but is not installed.

To restore (not recommended): re-add `fp-mcp = "fp.server:main"` to [project.scripts]
in pyproject.toml and reinstall with `pip install -e .`.

See: docs/CLI_MCP_DEPRECATED.md
"""
from __future__ import annotations

import json
from pathlib import Path

from mcp.server.fastmcp import FastMCP

from fp.generate.focuses import generate_focuses
from fp.generate.prompts import generate_all_prompts
from fp.research.web import research_queries
from fp.enrichment.problems import discover_problems, discover_problems_enriched
from fp.models import (
    Brand,
    ProjectConfig,
    ProjectState,
    PromptMode,
)
from fp.scoring.scorer import score_all
from fp.output.export import export_json, export_csv, export_csv_content, export_table_content

mcp = FastMCP("Focus Prompt")
PROJECT_FILE = "fp-project.json"


def _load_state() -> ProjectState | None:
    if not Path(PROJECT_FILE).exists():
        return None
    return ProjectState.load(PROJECT_FILE)


def _save_state(state: ProjectState):
    state.save(PROJECT_FILE)


# ─── Tools ───────────────────────────────────────────────────────────────────


@mcp.tool()
async def fp_init(
    name: str,
    description: str = "",
    website: str = "",
    services: str = "",
    competitors: str = "",
    mode: str = "unbranded",
    language: str = "id",
) -> str:
    """Initialize a new brand project for AI visibility research.

    Args:
        name: Brand name (e.g. 'Sribu')
        description: What the brand does (e.g. 'Marketplace freelance Indonesia')
        website: Brand website URL (e.g. 'https://sribu.com')
        services: Comma-separated service categories (e.g. 'desain, programming, copywriting, videografi')
        competitors: Comma-separated competitor names (e.g. 'Fastwork, Projects.co.id, Fiverr')
        mode: Prompt mode — 'unbranded', 'branded', or 'both'
        language: Primary language code (e.g. 'id', 'en')
    """
    cats = [s.strip() for s in services.split(",") if s.strip()]
    comps = [c.strip() for c in competitors.split(",") if c.strip()]

    brand = Brand(
        name=name,
        description=description,
        website=website,
        service_categories=cats,
        competitors=comps,
    )

    config = ProjectConfig(
        brand=brand,
        prompt_mode=PromptMode(mode),
        language=language,
    )

    state = ProjectState(config=config)
    _save_state(state)

    return json.dumps({
        "status": "ok",
        "brand": name,
        "focuses": 0,
        "prompts": 0,
        "mode": mode,
        "services": cats,
        "competitors": comps,
    }, indent=2, ensure_ascii=False)


@mcp.tool()
async def fp_research(
    extra: str = "",
    include_autocomplete: bool = True,
) -> str:
    """Fetch real user queries from Google Autocomplete.

    Run this BEFORE fp_discover for grounded, data-backed problem discovery.
    Without this, fp_discover uses LLM-only guessing.

    Args:
        extra: Optional extra seed queries, comma-separated
        include_autocomplete: Whether to fetch Google Autocomplete (default: true)
    """
    state = _load_state()
    if not state:
        return json.dumps({"error": "No project found. Run fp_init first."})

    brand = state.config.brand
    extra_queries = [q.strip() for q in extra.split(",") if q.strip()] if extra else None

    try:
        web_data = await research_queries(
            brand,
            extra_queries=extra_queries,
            include_autocomplete=include_autocomplete,
        )
    except Exception as e:
        return json.dumps({"error": f"Web research failed: {str(e)}"})

    state.web_data = web_data
    _save_state(state)

    stats = web_data["stats"]
    sample_autocomplete = web_data["autocomplete"][:5]

    return json.dumps({
        "status": "ok",
        "stats": stats,
        "sample_autocomplete": sample_autocomplete,
        "message": "Run fp_discover next — it will use this real data as ground truth.",
    }, indent=2, ensure_ascii=False)


@mcp.tool()
async def fp_discover(model: str = "") -> str:
    """Discover user problems and generate focus clusters.
    Requires fp_init to have been run first.
    Model configured via FP_MODEL env var or --model flag.
    """
    state = _load_state()
    if not state:
        return json.dumps({"error": "No project found. Run fp_init first."})

    brand = state.config.brand

    try:
        web_data = getattr(state, 'web_data', None)
        if web_data and web_data.get("stats", {}).get("total_queries", 0) > 0:
            problems = await discover_problems_enriched(brand, web_data, model=model, language=state.config.language)
        else:
            problems = discover_problems(brand, model=model, language=state.config.language)
    except Exception as e:
        return json.dumps({"error": f"Problem discovery failed: {str(e)}"})

    if not problems:
        return json.dumps({"error": "No problems discovered. Check brand input."})

    try:
        focuses = generate_focuses(brand, problems, model=model, language=state.config.language)
    except Exception as e:
        return json.dumps({"error": f"Focus generation failed: {str(e)}"})

    state.focuses = focuses
    _save_state(state)

    summary = [
        {
            "name": f.name,
            "description": f.description,
            "signal_count": f.signal_count,
        }
        for f in focuses
    ]

    return json.dumps({
        "status": "ok",
        "focus_count": len(focuses),
        "focuses": summary,
    }, indent=2, ensure_ascii=False)


@mcp.tool()
async def fp_generate_prompts(
    focus_name: str = "",
    mode: str = "",
    model: str = "",
    sanitize: bool = True,
) -> str:
    """Generate prompt variants for each focus.
    Requires fp_discover to have been run first.

    Args:
        focus_name: Optional — generate only for this focus (substring match)
        mode: Override prompt mode — 'unbranded', 'branded', 'both'
    """
    state = _load_state()
    if not state:
        return json.dumps({"error": "No project found. Run fp_init first."})

    if not state.focuses:
        return json.dumps({"error": "No focuses. Run fp_discover first."})

    brand = state.config.brand
    prompt_mode = PromptMode(mode) if mode else state.config.prompt_mode

    targets = state.focuses
    if focus_name:
        targets = [f for f in targets if focus_name.lower() in f.name.lower()]
        if not targets:
            return json.dumps({"error": f"No focus matching '{focus_name}'"})

    try:
        updated = generate_all_prompts(brand, targets, prompt_mode, model=model, language=state.config.language, sanitize=sanitize)
    except Exception as e:
        return json.dumps({"error": f"Prompt generation failed: {str(e)}"})

    if focus_name:
        for i, f in enumerate(state.focuses):
            if focus_name.lower() in f.name.lower():
                state.focuses[i] = updated[0]
                break
    else:
        state.focuses = updated

    _save_state(state)

    results = []
    for f in (updated if focus_name else state.focuses):
        unbranded = [p.text for p in f.prompts if p.mode.value == "unbranded"]
        branded = [p.text for p in f.prompts if p.mode.value == "branded"]
        results.append({
            "focus": f.name,
            "unbranded_count": len(unbranded),
            "branded_count": len(branded),
            "total": len(f.prompts),
            "unbranded": unbranded,
            "branded": branded,
        })

    return json.dumps({
        "status": "ok",
        "total_prompts": sum(r["total"] for r in results),
        "focuses": results,
    }, indent=2, ensure_ascii=False)


@mcp.tool()
async def fp_score(focus_name: str = "", model: str = "") -> str:
    """Score all prompts for brand relevance and mention likelihood.
    Requires fp_generate_prompts to have been run first.

    Args:
        focus_name: Optional — score only prompts in this focus
    """
    state = _load_state()
    if not state:
        return json.dumps({"error": "No project found. Run fp_init first."})

    total_prompts = sum(len(f.prompts) for f in state.focuses)
    if total_prompts == 0:
        return json.dumps({"error": "No prompts to score. Run fp_generate_prompts first."})

    brand = state.config.brand

    targets = state.focuses
    if focus_name:
        targets = [f for f in targets if focus_name.lower() in f.name.lower()]
        if not targets:
            return json.dumps({"error": f"No focus matching '{focus_name}'"})

    try:
        scored = score_all(targets, brand, model=model)
    except Exception as e:
        return json.dumps({"error": f"Scoring failed: {str(e)}"})

    if focus_name:
        for i, f in enumerate(state.focuses):
            if focus_name.lower() in f.name.lower():
                state.focuses[i] = scored[0]
                break
    else:
        state.focuses = scored

    _save_state(state)

    results = []
    for f in state.focuses:
        avg_service = f.service_match_score
        total = len(f.prompts)
        needs_review = sum(1 for p in f.prompts if p.needs_review)
        results.append({
            "focus": f.name,
            "priority": f.priority,
            "service_match": avg_service,
            "total_prompts": total,
            "needs_review": needs_review,
        })

    total_review = sum(r["needs_review"] for r in results)

    return json.dumps({
        "status": "ok",
        "total_focuses": len(results),
        "total_prompts": sum(r["total_prompts"] for r in results),
        "needs_review": total_review,
        "focuses": results,
    }, indent=2, ensure_ascii=False)


@mcp.tool()
async def fp_export(fmt: str = "csv") -> str:
    """Export project data.

    Args:
        fmt: Export format — 'csv' (default), 'json', or 'table'

    Returns:
        - csv: CSV content directly (copy-paste ready), saved to fp-export.csv
        - json: JSON file path info
        - table: Markdown table display (best for reading in opencode)
    """
    state = _load_state()
    if not state:
        return json.dumps({"error": "No project found. Run fp_init first."})

    if fmt == "csv":
        csv_content = export_csv_content(state)
        # Save to file
        output_path = "fp-export.csv"
        export_csv(state, output_path)
        # Return CSV directly for easy copy/download
        return csv_content
    elif fmt == "json":
        output_path = "fp-export.json"
        export_json(state, output_path)
        return json.dumps({
            "status": "ok",
            "format": "json",
            "path": output_path,
            "focuses": len(state.focuses),
            "prompts": sum(len(f.prompts) for f in state.focuses),
        }, indent=2, ensure_ascii=False)
    elif fmt == "table":
        return export_table_content(state)
    else:
        return json.dumps({"error": f"Unsupported format: {fmt}. Use csv, json, or table."})


@mcp.tool()
async def fp_status() -> str:
    """Get current project status — brand info, focuses, prompt counts."""
    state = _load_state()
    if not state:
        return json.dumps({"error": "No project found. Run fp_init first."})

    brand = state.config.brand
    total_prompts = sum(len(f.prompts) for f in state.focuses)
    needs_review = sum(1 for f in state.focuses for p in f.prompts if p.needs_review)

    focuses_summary = [
        {
            "name": f.name,
            "priority": f.priority,
            "service_match": f.service_match_score,
            "unbranded_prompts": sum(1 for p in f.prompts if p.mode.value == "unbranded"),
            "branded_prompts": sum(1 for p in f.prompts if p.mode.value == "branded"),
            "total_prompts": len(f.prompts),
            "needs_review": sum(1 for p in f.prompts if p.needs_review),
        }
        for f in state.focuses
    ]

    return json.dumps({
        "brand": {
            "name": brand.name,
            "description": brand.description or "",
            "website": brand.website or "",
            "services": brand.service_categories,
            "competitors": brand.competitors,
        },
        "config": {
            "mode": state.config.prompt_mode.value,
            "language": state.config.language,
        },
        "focus_count": len(state.focuses),
        "prompt_count": total_prompts,
        "needs_review": needs_review,
        "focuses": focuses_summary,
    }, indent=2, ensure_ascii=False)


# ─── Resources ───────────────────────────────────────────────────────────────


@mcp.resource("fp://project")
async def project_resource() -> str:
    """Full project state as JSON."""
    state = _load_state()
    if not state:
        return json.dumps({"error": "No project found. Run fp_init first."})
    return json.dumps(state.model_dump(mode="json"), indent=2, ensure_ascii=False)


@mcp.resource("fp://focuses")
async def focuses_resource() -> str:
    """Focus list with summary metrics."""
    state = _load_state()
    if not state or not state.focuses:
        return json.dumps({"error": "No focuses yet."})

    result = [
        {
            "name": f.name,
            "description": f.description,
            "priority": f.priority,
            "service_match": f.service_match_score,
            "signals": f.signals,
            "signal_count": f.signal_count,
            "unbranded_prompts": sum(1 for p in f.prompts if p.mode.value == "unbranded"),
            "branded_prompts": sum(1 for p in f.prompts if p.mode.value == "branded"),
            "total_prompts": len(f.prompts),
            "needs_review": sum(1 for p in f.prompts if p.needs_review),
        }
        for f in state.focuses
    ]

    return json.dumps(result, indent=2, ensure_ascii=False)


@mcp.resource("fp://docs")
async def docs_resource() -> str:
    """Full usage documentation for focus-prompt MCP server and CLI."""
    return """# focus-prompt — Usage Docs

AI Brand Visibility Research Tool — prediksi dan generate unbranded prompt yang bisa dipakai AI chatbot untuk menemukan dan mention brand kamu.

## Pipeline
```
init → research → discover → prompt-generate (auto-sanitize) → score → export (csv default, copy-paste ready; table for markdown display)
```

## Model Configuration

Model-agnostic via LiteLLM — supports 100+ providers.

**Model selection priority:**
1. `model` parameter (from --model flag or MCP param)
2. `FP_MODEL` environment variable
3. Default: `gpt-4o-mini`

**Supported providers (examples):**
| Provider | FP_MODEL value | API Key Env Var |
|----------|---------------|-----------------|
| OpenAI | `gpt-4o-mini` | `OPENAI_API_KEY` |
| DeepSeek | `deepseek/deepseek-chat` | `DEEPSEEK_API_KEY` |
| MiniMax (Singapore) | `minimax/MiniMax-M2.1` | `MINIMAX_API_KEY` |
| Qwen/Alibaba | `dashscope/qwen-max` | `DASHSCOPE_API_KEY` |
| Zhipu/GLM | `zai/glm-4.7` | `ZAI_API_KEY` |
| Moonshot/Kimi | `moonshot/kimi-k2-thinking` | `MOONSHOT_API_KEY` |
| ByteDance/Doubao | `volcengine/doubao-seed-1.6` | `VOLCENGINE_API_KEY` |
| Tencent/Hunyuan | `tencent/deepseek-v4-pro` | `TENCENT_API_KEY` |
| MiMo (Singapore) | `xiaomi_mimo/mimo-v2-pro` | `XIAOMI_MIMO_API_KEY` |
| Any OpenAI-compatible | `openai/<model>` + `api_base` | Provider-specific |

## MCP Tools

| Tool | Description | Args |
|------|-------------|------|
| `fp_init` | Init brand project | `name`, `description`, `website`, `services` (comma-sep), `competitors` (comma-sep), `mode` (unbranded/branded/both), `language` |
| `fp_research` | Fetch real queries dari Google Autocomplete | `extra` (comma-seed queries), `include_autocomplete` |
| `fp_discover` | Problem discovery + focus clustering (LLM) | `model` |
| `fp_generate_prompts` | Generate prompt variants per focus | `focus_name` (optional filter), `mode`, `model`, `sanitize` (auto-fix non-Latin chars) |
| `fp_score` | Score prompts untuk brand relevance | `focus_name` (optional filter), `model` |
| `fp_export` | Export data — CSV (default), JSON, or Table | `fmt` (csv/json/table, default: csv) |
| `fp_status` | Project status | — |

## MCP Resources

| URI | Description |
|-----|-------------|
| `fp://project` | Full project state (JSON) |
| `fp://focuses` | Focus list + summary metrics |
| `fp://focus/{name}/prompts` | Prompts untuk focus tertentu |
| `fp://docs` | Dokumentasi ini |

## Quick Start (MCP)
```
1. fp_init — init brand (name, description, services, competitors)
2. fp_research — fetch real user queries dari Google Autocomplete (optional tapi better)
3. fp_discover — problem discovery + focus clusters
4. fp_generate_prompts — generate prompt variants
5. fp_score — score relevance
6. fp_export — export CSV (default, copy-paste ready), JSON, atau table (markdown display)
```

## CLI Commands
```
fp init "Brand" --desc "..." --services "s1,s2" --competitors "k1,k2"
fp research --extra "seed1,seed2"
fp discover
fp prompt-generate [--no-sanitize]
fp score
fp export json|csv
fp status
fp focus-list
fp prompt-list --focus "name" --mode unbranded --review
```

## Models
- **Brand**: name, description, website, service_categories, competitors
- **Focus**: name, description, lens, priority, signals, signal_count, service_match_score, prompts
- **ScoredPrompt**: text, intent, mode, language, service_match, mention_likelihood, overall_score, needs_review
- **PromptIntent**: info, comparison, how-to, hire, review, troubleshoot, explore, verify
- **PromptMode**: unbranded (mention likelihood weighted higher), branded (service match weighted higher), both

## Requirements
- Python 3.11+
- LLM API key (OPENAI_API_KEY, DEEPSEEK_API_KEY, MINIMAX_API_KEY, etc.)
- Set FP_MODEL env var to choose provider (default: gpt-4o-mini)
"""


@mcp.resource("fp://focus/{name}/prompts")
async def focus_prompts_resource(name: str) -> str:
    """Prompts for a specific focus."""
    state = _load_state()
    if not state or not state.focuses:
        return json.dumps({"error": "No focuses yet."})

    matches = [f for f in state.focuses if name.lower() in f.name.lower()]
    if not matches:
        return json.dumps({"error": f"No focus matching '{name}'"})

    focus = matches[0]
    result = {
        "focus": focus.name,
        "description": focus.description,
        "service_match": focus.service_match_score,
        "prompts": [
            {
                "text": p.text,
                "mode": p.mode.value,
                "intent": p.intent.value,
                "language": p.language,
                "service_match": p.service_match,
                "mention_likelihood": p.mention_likelihood,
                "overall_score": p.overall_score,
                "needs_review": p.needs_review,
            }
            for p in focus.prompts
        ],
    }

    return json.dumps(result, indent=2, ensure_ascii=False)


# ─── Main ────────────────────────────────────────────────────────────────────


def main():
    mcp.run()


if __name__ == "__main__":
    main()
