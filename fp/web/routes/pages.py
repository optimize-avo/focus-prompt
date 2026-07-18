"""HTML page routes."""
from __future__ import annotations

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, RedirectResponse

from fp.web.deps import get_state, get_config

router = APIRouter()


@router.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """Dashboard — project status, quick actions."""
    templates = request.app.state.templates
    state = get_state()

    context = {"request": request, "state": state}
    return templates.TemplateResponse("index.html", context)


@router.get("/init", response_class=HTMLResponse)
async def init_page(request: Request):
    """Brand setup form."""
    templates = request.app.state.templates
    return templates.TemplateResponse("init.html", {"request": request})


@router.get("/pipeline", response_class=HTMLResponse)
async def pipeline_page(request: Request):
    """Main pipeline view."""
    templates = request.app.state.templates
    state = get_state()

    if not state:
        return RedirectResponse(url="/init", status_code=302)

    context = {"request": request, "state": state}
    return templates.TemplateResponse("pipeline.html", context)


@router.get("/settings", response_class=HTMLResponse)
async def settings_page(request: Request):
    """Settings page."""
    templates = request.app.state.templates
    config = get_config()
    context = {"request": request, "config": config}
    return templates.TemplateResponse("settings.html", context)
