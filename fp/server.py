"""MCP Server — Focus Prompt Research Tool for OpenCode."""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Optional

from mcp.server.fastmcp import FastMCP
from openai import OpenAI

from fp.generate.focuses import generate_focuses
from fp.generate.prompts import generate_all_prompts
from fp.enrichment.problems import discover_problems
from fp.models import (
    Brand,
    Focus,
    ProjectConfig,
    ProjectState,
    PromptMode,
)
from fp.scoring.scorer import score_all
from fp.output.export import export_json, export_csv

mcp = FastMCP("Focus Prompt")
PROJECT_FILE = "fp-project.json"


def _get_client() -> OpenAI | None:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return None
    return OpenAI(api_key=api_key)


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
async def fp_discover() -> str:
    """Discover user problems and generate focus clusters.
    Requires fp_init to have been run first.
    Requires OPENAI_API_KEY environment variable.
    """
    state = _load_state()
    if not state:
        return json.dumps({"error": "No project found. Run fp_init first."})

    client = _get_client()
    if not client:
        return json.dumps({"error": "OPENAI_API_KEY not set"})

    brand = state.config.brand

    try:
        problems = discover_problems(brand, client)
    except Exception as e:
        return json.dumps({"error": f"Problem discovery failed: {str(e)}"})

    if not problems:
        return json.dumps({"error": "No problems discovered. Check brand input."})

    try:
        focuses = generate_focuses(brand, problems, client)
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

    client = _get_client()
    if not client:
        return json.dumps({"error": "OPENAI_API_KEY not set"})

    brand = state.config.brand
    prompt_mode = PromptMode(mode) if mode else state.config.prompt_mode

    targets = state.focuses
    if focus_name:
        targets = [f for f in targets if focus_name.lower() in f.name.lower()]
        if not targets:
            return json.dumps({"error": f"No focus matching '{focus_name}'"})

    try:
        updated = generate_all_prompts(brand, targets, client, prompt_mode)
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
async def fp_score(focus_name: str = "") -> str:
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

    client = _get_client()
    if not client:
        return json.dumps({"error": "OPENAI_API_KEY not set"})

    brand = state.config.brand

    targets = state.focuses
    if focus_name:
        targets = [f for f in targets if focus_name.lower() in f.name.lower()]
        if not targets:
            return json.dumps({"error": f"No focus matching '{focus_name}'"})

    try:
        scored = score_all(targets, brand, client)
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
async def fp_export(fmt: str = "json") -> str:
    """Export project data.

    Args:
        fmt: Export format — 'json' or 'csv'
    """
    state = _load_state()
    if not state:
        return json.dumps({"error": "No project found. Run fp_init first."})

    output_path = f"fp-export.{fmt}"

    if fmt == "json":
        export_json(state, output_path)
    elif fmt == "csv":
        export_csv(state, output_path)
    else:
        return json.dumps({"error": f"Unsupported format: {fmt}. Use json or csv."})

    return json.dumps({
        "status": "ok",
        "format": fmt,
        "path": output_path,
        "focuses": len(state.focuses),
        "prompts": sum(len(f.prompts) for f in state.focuses),
    }, indent=2, ensure_ascii=False)


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
