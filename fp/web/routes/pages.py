"""HTML page routes."""
from __future__ import annotations

from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse

from fp.models import Brand, ProjectConfig, ProjectState, PromptMode
from fp.web.deps import get_state, get_config, save_state

router = APIRouter()


@router.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """Dashboard — project status, quick actions."""
    templates = request.app.state.templates
    state = get_state()

    context = {"state": state}
    return templates.TemplateResponse(request, "index.html", context)


@router.get("/init", response_class=HTMLResponse)
async def init_page(request: Request):
    """Brand setup form."""
    templates = request.app.state.templates
    return templates.TemplateResponse(request, "init.html")


@router.get("/pipeline", response_class=HTMLResponse)
async def pipeline_page(request: Request):
    """Main pipeline view."""
    templates = request.app.state.templates
    state = get_state()

    if not state:
        return RedirectResponse(url="/init", status_code=302)

    # Compute step statuses for wizard UI
    step_statuses = {}
    if state:
        # Research
        step_statuses["research"] = "complete" if (state.web_data and state.web_data.get("stats", {}).get("total_queries", 0) > 0) else "ready"
        # Discover
        step_statuses["discover"] = "complete" if state.focuses else ("ready" if state.web_data else "locked")
        # Generate
        total_prompts = sum(len(f.prompts) for f in state.focuses)
        step_statuses["generate"] = "complete" if total_prompts > 0 else ("ready" if state.focuses else "locked")
        # Score
        scored = sum(1 for f in state.focuses for p in f.prompts if p.overall_score > 0)
        step_statuses["score"] = "complete" if (scored > 0 and scored == total_prompts) else ("ready" if total_prompts > 0 else "locked")
        # Export
        step_statuses["export"] = "ready" if scored > 0 else "locked"
    else:
        for s in ["research", "discover", "generate", "score", "export"]:
            step_statuses[s] = "locked"

    context = {"state": state, "step_statuses": step_statuses}
    return templates.TemplateResponse(request, "pipeline.html", context)


@router.get("/settings", response_class=HTMLResponse)
async def settings_page(request: Request):
    """Settings page."""
    templates = request.app.state.templates
    config = get_config()
    context = {"config": config}
    return templates.TemplateResponse(request, "settings.html", context)


@router.post("/api/init", response_class=HTMLResponse)
async def init_project(
    request: Request,
    name: str = Form(...),
    description: str = Form(""),
    website: str = Form(""),
    services: str = Form(""),
    competitors: str = Form(""),
    mode: str = Form("unbranded"),
    language: str = Form("id"),
):
    """Create a new project from the init form."""
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
    save_state(state)

    return HTMLResponse(f'''
        <div class="p-3 bg-emerald-500/10 border border-emerald-500/30 rounded-lg text-emerald-400 text-sm">
            ✓ Project created for <strong>{name}</strong>.
            <a href="/pipeline" class="underline ml-1">Go to Pipeline →</a>
        </div>
    ''')
