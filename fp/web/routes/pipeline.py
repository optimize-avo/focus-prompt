"""HTMX partial routes for pipeline steps."""
from __future__ import annotations

import json
import asyncio
from typing import Any

from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse, JSONResponse
from sse_starlette.sse import EventSourceResponse

from fp.web.deps import get_state, save_state
from fp.research.web import research_queries
from fp.enrichment.problems import discover_problems, discover_problems_enriched
from fp.generate.focuses import generate_focuses
from fp.generate.prompts import generate_all_prompts
from fp.scoring.scorer import score_all
from fp.output.export import export_json, export_csv

router = APIRouter()

# Track pipeline run state
_pipeline_running = False
_current_phase = None


# ─── Helper Functions ────────────────────────────────────────────────────────


def _phase_status(state: Any) -> dict[str, str]:
    """Determine the status of each pipeline phase."""
    status = {
        "research": "not_started",
        "discover": "not_started",
        "generate": "not_started",
        "score": "not_started",
        "export": "not_started",
    }
    
    if not state:
        return status
    
    # Research is complete if we have web data
    if state.web_data and state.web_data.get("stats", {}).get("total_queries", 0) > 0:
        status["research"] = "completed"
    
    # Discover is complete if we have focuses with descriptions
    if state.focuses and len(state.focuses) > 0:
        # Check if focuses have signals (from discover phase)
        has_signals = any(f.signal_count > 0 for f in state.focuses)
        if has_signals:
            status["discover"] = "completed"
        else:
            status["discover"] = "partial"
    
    # Generate is complete if focuses have prompts
    if state.focuses:
        total_prompts = sum(len(f.prompts) for f in state.focuses)
        if total_prompts > 0:
            status["generate"] = "completed"
            # Check if prompts have scores
            scored_count = sum(1 for f in state.focuses for p in f.prompts if p.overall_score > 0)
            if scored_count > 0:
                status["score"] = "completed"
            elif scored_count > 0:
                status["score"] = "partial"
    
    return status


def _calculate_progress(status: dict[str, str]) -> dict[str, Any]:
    """Calculate overall progress percentage."""
    phases = ["research", "discover", "generate", "score", "export"]
    completed = sum(1 for p in phases if status.get(p) == "completed")
    partial = sum(0.5 for p in phases if status.get(p) == "partial")
    total = len(phases)
    
    percent = ((completed + partial) / total) * 100
    
    return {
        "completed": completed,
        "partial": partial,
        "total": total,
        "total_percent": percent,
    }


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


# ─── Status Routes (GET) ─────────────────────────────────────────────────────


@router.get("/pipeline/status", response_class=JSONResponse)
async def pipeline_status():
    """Get pipeline phase status."""
    global _pipeline_running, _current_phase
    
    state = get_state()
    status = _phase_status(state)
    
    # Add running state if applicable
    if _pipeline_running and _current_phase:
        status[_current_phase] = "running"
    
    progress = _calculate_progress(status)
    
    return JSONResponse({
        "status": status,
        "progress": progress,
        "running": _pipeline_running,
        "current_phase": _current_phase,
    })


@router.get("/pipeline/scores", response_class=JSONResponse)
async def pipeline_scores():
    """Get score results for all prompts."""
    state = get_state()
    
    if not state or not state.focuses:
        return JSONResponse({
            "scores": [],
            "average": 0,
            "count": 0,
            "needs_review": 0,
        })
    
    scores = []
    for focus in state.focuses:
        for prompt in focus.prompts:
            if prompt.overall_score > 0:
                scores.append({
                    "prompt": prompt.text[:80] + ("..." if len(prompt.text) > 80 else ""),
                    "score": prompt.overall_score,
                    "intent": prompt.intent.value if hasattr(prompt.intent, 'value') else str(prompt.intent),
                    "focus": focus.name,
                    "needs_review": prompt.needs_review,
                })
    
    # Sort by score ascending (worst first)
    scores.sort(key=lambda x: x["score"])
    
    # Calculate average
    avg_score = sum(s["score"] for s in scores) / len(scores) if scores else 0
    needs_review = sum(1 for s in scores if s["needs_review"])
    
    return JSONResponse({
        "scores": scores,
        "average": avg_score,
        "count": len(scores),
        "needs_review": needs_review,
    })


# ─── Action Routes (POST) ────────────────────────────────────────────────────


@router.post("/research", response_class=HTMLResponse)
async def run_research(request: Request, extra: str = Form("")):
    """Run research step."""
    state = get_state()
    if not state:
        return HTMLResponse('<p class="text-red-400">No project found. <a href="/init" class="underline text-blue-400 hover:text-blue-300">Create one</a>.</p>')

    extra_queries = [q.strip() for q in extra.split(",") if q.strip()] if extra else None
    try:
        web_data = await research_queries(state.config.brand, extra_queries=extra_queries)
        state.web_data = web_data
        save_state(state)
        stats = web_data["stats"]
        return HTMLResponse(f'''
            <div class="space-y-2">
                <p class="text-emerald-400 font-medium">✓ Research complete</p>
                <p class="text-sm text-slate-300">Autocomplete: {stats["autocomplete_count"]} suggestions</p>
                <p class="text-sm text-slate-300">Total queries: {stats["total_queries"]}</p>
                <p class="text-sm text-slate-400">Sample: {", ".join(web_data["autocomplete"][:5])}</p>
            </div>
        ''')
    except Exception as e:
        return HTMLResponse(f'<p class="text-red-400">Error: {e}</p>')


@router.post("/discover", response_class=HTMLResponse)
async def run_discover(request: Request):
    """Run discover step."""
    state = get_state()
    if not state:
        return HTMLResponse('<p class="text-red-400">No project found.</p>')

    brand = state.config.brand
    try:
        web_data = getattr(state, "web_data", None)
        if web_data and web_data.get("stats", {}).get("total_queries", 0) > 0:
            problems = await discover_problems_enriched(brand, web_data)
        else:
            problems = discover_problems(brand)
    except Exception as e:
        return HTMLResponse(f'<p class="text-red-400">Discovery failed: {e}</p>')

    if not problems:
        return HTMLResponse('<p class="text-amber-400">No problems discovered.</p>')

    try:
        focuses = generate_focuses(brand, problems)
        state.focuses = focuses
        save_state(state)
        items = "".join(
            f'<li class="text-sm text-slate-300"><strong class="text-white">{f.name}</strong> — {f.signal_count} signals</li>'
            for f in focuses
        )
        return HTMLResponse(f'''
            <div class="space-y-2">
                <p class="text-emerald-400 font-medium">✓ Discovered {len(focuses)} focuses</p>
                <ul class="list-disc list-inside text-sm text-slate-300">{items}</ul>
            </div>
        ''')
    except Exception as e:
        return HTMLResponse(f'<p class="text-red-400">Focus generation failed: {e}</p>')


@router.post("/generate", response_class=HTMLResponse)
async def run_generate(request: Request):
    """Run generate step."""
    state = get_state()
    if not state or not state.focuses:
        return HTMLResponse('<p class="text-red-400">No focuses. Run discover first.</p>')

    try:
        updated = generate_all_prompts(state.config.brand, state.focuses, state.config.prompt_mode)
        state.focuses = updated
        save_state(state)
        total = sum(len(f.prompts) for f in state.focuses)
        return HTMLResponse(f'''
            <div class="space-y-2">
                <p class="text-emerald-400 font-medium">✓ Generated {total} prompts</p>
                <p class="text-sm text-slate-400">Across {len(state.focuses)} focuses</p>
            </div>
        ''')
    except Exception as e:
        return HTMLResponse(f'<p class="text-red-400">Generation failed: {e}</p>')


@router.post("/score", response_class=HTMLResponse)
async def run_score(request: Request):
    """Run score step."""
    state = get_state()
    if not state or not state.focuses:
        return HTMLResponse('<p class="text-red-400">No focuses.</p>')

    total_prompts = sum(len(f.prompts) for f in state.focuses)
    if total_prompts == 0:
        return HTMLResponse('<p class="text-red-400">No prompts to score.</p>')

    try:
        scored = score_all(state.focuses, state.config.brand)
        state.focuses = scored
        save_state(state)
        needs_review = sum(1 for f in state.focuses for p in f.prompts if p.needs_review)
        return HTMLResponse(f'''
            <div class="space-y-2">
                <p class="text-emerald-400 font-medium">✓ Scoring complete</p>
                <p class="text-sm text-slate-400">{total_prompts} prompts scored, {needs_review} need review</p>
            </div>
        ''')
    except Exception as e:
        return HTMLResponse(f'<p class="text-red-400">Scoring failed: {e}</p>')


@router.post("/export", response_class=HTMLResponse)
async def run_export(request: Request, fmt: str = Form("json")):
    """Run export step."""
    state = get_state()
    if not state:
        return HTMLResponse('<p class="text-red-400">No project found.</p>')

    try:
        if fmt == "csv":
            path = export_csv(state, "fp-export.csv")
        else:
            path = export_json(state, "fp-export.json")
        return HTMLResponse(f'''
            <div class="space-y-2">
                <p class="text-emerald-400 font-medium">✓ Exported to {path}</p>
                <p class="text-sm text-slate-400">{len(state.focuses)} focuses, {sum(len(f.prompts) for f in state.focuses)} prompts</p>
            </div>
        ''')
    except Exception as e:
        return HTMLResponse(f'<p class="text-red-400">Export failed: {e}</p>')


# ─── Run All Pipeline (POST + SSE) ──────────────────────────────────────────


@router.post("/pipeline/run-all")
async def run_all_phases(request: Request):
    """Run all pipeline phases sequentially via SSE."""
    global _pipeline_running, _current_phase
    
    if _pipeline_running:
        return JSONResponse({"error": "Pipeline already running"}, status_code=409)
    
    state = get_state()
    if not state:
        return JSONResponse({"error": "No project found"}, status_code=400)
    
    _pipeline_running = True
    
    async def event_generator():
        global _pipeline_running, _current_phase
        
        phases = ["research", "discover", "generate", "score"]
        
        try:
            for phase in phases:
                _current_phase = phase
                yield {
                    "event": "phase_start",
                    "data": json.dumps({"phase": phase})
                }
                
                try:
                    if phase == "research":
                        # Run research
                        web_data = await research_queries(state.config.brand)
                        state.web_data = web_data
                        save_state(state)
                        
                    elif phase == "discover":
                        # Run discover
                        web_data = getattr(state, "web_data", None)
                        if web_data and web_data.get("stats", {}).get("total_queries", 0) > 0:
                            problems = await discover_problems_enriched(state.config.brand, web_data)
                        else:
                            problems = discover_problems(state.config.brand)
                        
                        if problems:
                            focuses = generate_focuses(state.config.brand, problems)
                            state.focuses = focuses
                            save_state(state)
                        
                    elif phase == "generate":
                        # Run generate
                        if state.focuses:
                            updated = generate_all_prompts(state.config.brand, state.focuses, state.config.prompt_mode)
                            state.focuses = updated
                            save_state(state)
                        
                    elif phase == "score":
                        # Run score
                        if state.focuses and sum(len(f.prompts) for f in state.focuses) > 0:
                            scored = score_all(state.focuses, state.config.brand)
                            state.focuses = scored
                            save_state(state)
                    
                    yield {
                        "event": "phase_complete",
                        "data": json.dumps({"phase": phase, "success": True})
                    }
                    
                except Exception as e:
                    yield {
                        "event": "phase_error",
                        "data": json.dumps({"phase": phase, "error": str(e)})
                    }
                    # Continue to next phase even if one fails
                    continue
                
                # Small delay between phases for UI feedback
                await asyncio.sleep(0.1)
            
            # All phases complete
            yield {
                "event": "run_complete",
                "data": json.dumps({"success": True})
            }
            
        finally:
            _pipeline_running = False
            _current_phase = None
    
    return EventSourceResponse(event_generator())