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
