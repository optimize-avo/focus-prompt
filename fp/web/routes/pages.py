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

    context = {"state": state}
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
