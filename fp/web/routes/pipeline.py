"""HTMX partial routes for pipeline steps."""
from __future__ import annotations

from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse

from fp.web.deps import get_state, save_state
from fp.research.web import research_queries
from fp.enrichment.problems import discover_problems, discover_problems_enriched
from fp.generate.focuses import generate_focuses
from fp.generate.prompts import generate_all_prompts
from fp.scoring.scorer import score_all
from fp.output.export import export_json, export_csv

router = APIRouter()


# ─── Tab Routes (GET) ────────────────────────────────────────────────────────


@router.get("/pipeline/research", response_class=HTMLResponse)
async def research_tab(request: Request):
    """Research tab partial."""
    templates = request.app.state.templates
    state = get_state()
    return templates.TemplateResponse(request, "partials/research.html", {"state": state})


@router.get("/pipeline/discover", response_class=HTMLResponse)
async def discover_tab(request: Request):
    """Discover tab partial."""
    templates = request.app.state.templates
    state = get_state()
    return templates.TemplateResponse(request, "partials/discover.html", {"state": state})


@router.get("/pipeline/generate", response_class=HTMLResponse)
async def generate_tab(request: Request):
    """Generate tab partial."""
    templates = request.app.state.templates
    state = get_state()
    return templates.TemplateResponse(request, "partials/generate.html", {"state": state})


@router.get("/pipeline/score", response_class=HTMLResponse)
async def score_tab(request: Request):
    """Score tab partial."""
    templates = request.app.state.templates
    state = get_state()
    return templates.TemplateResponse(request, "partials/score.html", {"state": state})


@router.get("/pipeline/export", response_class=HTMLResponse)
async def export_tab(request: Request):
    """Export tab partial."""
    templates = request.app.state.templates
    state = get_state()
    return templates.TemplateResponse(request, "partials/export.html", {"state": state})


# ─── Action Routes (POST) ────────────────────────────────────────────────────


@router.post("/research", response_class=HTMLResponse)
async def run_research(request: Request, extra: str = Form("")):
    """Run research step."""
    state = get_state()
    if not state:
        return HTMLResponse('<p class="text-red-600">No project found. <a href="/init" class="underline">Create one</a>.</p>')

    extra_queries = [q.strip() for q in extra.split(",") if q.strip()] if extra else None
    try:
        web_data = await research_queries(state.config.brand, extra_queries=extra_queries)
        state.web_data = web_data
        save_state(state)
        stats = web_data["stats"]
        return HTMLResponse(f'''
            <div class="space-y-2">
                <p class="text-green-600 font-medium">✓ Research complete</p>
                <p class="text-sm">Autocomplete: {stats["autocomplete_count"]} suggestions</p>
                <p class="text-sm">Total queries: {stats["total_queries"]}</p>
                <p class="text-sm text-gray-500">Sample: {", ".join(web_data["autocomplete"][:5])}</p>
            </div>
        ''')
    except Exception as e:
        return HTMLResponse(f'<p class="text-red-600">Error: {e}</p>')


@router.post("/discover", response_class=HTMLResponse)
async def run_discover(request: Request):
    """Run discover step."""
    state = get_state()
    if not state:
        return HTMLResponse('<p class="text-red-600">No project found.</p>')

    brand = state.config.brand
    try:
        web_data = getattr(state, "web_data", None)
        if web_data and web_data.get("stats", {}).get("total_queries", 0) > 0:
            problems = await discover_problems_enriched(brand, web_data)
        else:
            problems = discover_problems(brand)
    except Exception as e:
        return HTMLResponse(f'<p class="text-red-600">Discovery failed: {e}</p>')

    if not problems:
        return HTMLResponse('<p class="text-yellow-600">No problems discovered.</p>')

    try:
        focuses = generate_focuses(brand, problems)
        state.focuses = focuses
        save_state(state)
        items = "".join(
            f'<li class="text-sm"><strong>{f.name}</strong> — {f.signal_count} signals</li>'
            for f in focuses
        )
        return HTMLResponse(f'''
            <div class="space-y-2">
                <p class="text-green-600 font-medium">✓ Discovered {len(focuses)} focuses</p>
                <ul class="list-disc list-inside text-sm text-gray-700">{items}</ul>
            </div>
        ''')
    except Exception as e:
        return HTMLResponse(f'<p class="text-red-600">Focus generation failed: {e}</p>')


@router.post("/generate", response_class=HTMLResponse)
async def run_generate(request: Request):
    """Run generate step."""
    state = get_state()
    if not state or not state.focuses:
        return HTMLResponse('<p class="text-red-600">No focuses. Run discover first.</p>')

    try:
        updated = generate_all_prompts(state.config.brand, state.focuses, state.config.prompt_mode)
        state.focuses = updated
        save_state(state)
        total = sum(len(f.prompts) for f in state.focuses)
        return HTMLResponse(f'''
            <div class="space-y-2">
                <p class="text-green-600 font-medium">✓ Generated {total} prompts</p>
                <p class="text-sm text-gray-500">Across {len(state.focuses)} focuses</p>
            </div>
        ''')
    except Exception as e:
        return HTMLResponse(f'<p class="text-red-600">Generation failed: {e}</p>')


@router.post("/score", response_class=HTMLResponse)
async def run_score(request: Request):
    """Run score step."""
    state = get_state()
    if not state or not state.focuses:
        return HTMLResponse('<p class="text-red-600">No focuses.</p>')

    total_prompts = sum(len(f.prompts) for f in state.focuses)
    if total_prompts == 0:
        return HTMLResponse('<p class="text-red-600">No prompts to score.</p>')

    try:
        scored = score_all(state.focuses, state.config.brand)
        state.focuses = scored
        save_state(state)
        needs_review = sum(1 for f in state.focuses for p in f.prompts if p.needs_review)
        return HTMLResponse(f'''
            <div class="space-y-2">
                <p class="text-green-600 font-medium">✓ Scoring complete</p>
                <p class="text-sm text-gray-500">{total_prompts} prompts scored, {needs_review} need review</p>
            </div>
        ''')
    except Exception as e:
        return HTMLResponse(f'<p class="text-red-600">Scoring failed: {e}</p>')


@router.post("/export", response_class=HTMLResponse)
async def run_export(request: Request, fmt: str = Form("json")):
    """Run export step."""
    state = get_state()
    if not state:
        return HTMLResponse('<p class="text-red-600">No project found.</p>')

    try:
        if fmt == "csv":
            path = export_csv(state, "fp-export.csv")
        else:
            path = export_json(state, "fp-export.json")
        return HTMLResponse(f'''
            <div class="space-y-2">
                <p class="text-green-600 font-medium">✓ Exported to {path}</p>
                <p class="text-sm text-gray-500">{len(state.focuses)} focuses, {sum(len(f.prompts) for f in state.focuses)} prompts</p>
            </div>
        ''')
    except Exception as e:
        return HTMLResponse(f'<p class="text-red-600">Export failed: {e}</p>')
