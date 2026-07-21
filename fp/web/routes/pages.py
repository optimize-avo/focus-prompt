"""HTML page routes."""
from __future__ import annotations

from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse

from fp.models import Brand, ProjectConfig, ProjectState, PromptMode
from fp.research.autodetect import research_brand
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


@router.post("/init/research", response_class=HTMLResponse)
async def init_research(request: Request, domain: str = Form(...)):
    """Auto-detect brand info from domain via EXA + LLM."""
    templates = request.app.state.templates
    try:
        brand_data = await research_brand(domain)
    except Exception as e:
        return HTMLResponse(f'''
            <div id="init-container" class="max-w-xl">
                <div class="bg-red-500/10 border border-red-500/30 rounded-lg p-4 mb-4">
                    <p class="text-red-400 text-sm">Research failed: {e}</p>
                    <a href="/init" class="text-red-300 text-sm underline mt-2 inline-block">← Back to manual entry</a>
                </div>
            </div>
        ''')

    context = {"brand": brand_data, "domain": domain}
    return templates.TemplateResponse(request, "init_review.html", context)


VALID_STEPS = ["research", "discover", "generate", "score", "export"]


def _compute_step_statuses(state) -> dict:
    """Compute completion status for each pipeline step."""
    step_statuses = {}
    if state:
        step_statuses["research"] = {
            "completed": bool(state.web_data and state.web_data.get("stats", {}).get("total_queries", 0) > 0),
            "count": state.web_data.get("stats", {}).get("total_queries", 0) if state.web_data else 0,
            "total": state.web_data.get("stats", {}).get("total_queries", 0) if state.web_data else 0,
        }
        step_statuses["discover"] = {
            "completed": bool(state.focuses),
            "count": len(state.focuses),
            "total": len(state.focuses),
        }
        total_prompts = sum(len(f.prompts) for f in state.focuses)
        step_statuses["generate"] = {
            "completed": total_prompts > 0,
            "count": total_prompts,
            "total": total_prompts,
        }
        scored = sum(1 for f in state.focuses for p in f.prompts if p.overall_score > 0)
        step_statuses["score"] = {
            "completed": scored > 0 and scored == total_prompts,
            "count": scored,
            "total": total_prompts,
        }
        step_statuses["export"] = {
            "completed": scored > 0,
            "count": scored,
            "total": total_prompts,
        }
    else:
        for s in VALID_STEPS:
            step_statuses[s] = {"completed": False, "count": 0, "total": 0}
    return step_statuses


@router.get("/pipeline", response_class=HTMLResponse)
async def pipeline_page(request: Request):
    """Main pipeline view — defaults to research step."""
    templates = request.app.state.templates
    state = get_state()

    if not state:
        return RedirectResponse(url="/init", status_code=302)

    step_statuses = _compute_step_statuses(state)

    context = {
        "state": state,
        "current_step": "research",
        "step_statuses": step_statuses,
    }
    return templates.TemplateResponse(request, "pipeline.html", context)


@router.get("/pipeline/{step}", response_class=HTMLResponse)
async def pipeline_step(request: Request, step: str):
    """Render a specific pipeline step in the wizard."""
    if step not in VALID_STEPS:
        return RedirectResponse(url="/pipeline/research", status_code=302)

    templates = request.app.state.templates
    state = get_state()

    if not state:
        return RedirectResponse(url="/init", status_code=302)

    step_statuses = _compute_step_statuses(state)

    context = {
        "state": state,
        "current_step": step,
        "step_statuses": step_statuses,
    }
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
