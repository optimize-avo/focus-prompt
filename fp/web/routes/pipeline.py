"""HTMX partial routes for pipeline steps."""
from __future__ import annotations

import json
from typing import AsyncGenerator

from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse, StreamingResponse

from fp.web.deps import get_state, save_state
from fp.research.web import research_queries
from fp.enrichment.problems import discover_problems, discover_problems_enriched
from fp.generate.focuses import generate_focuses
from fp.generate.prompts import generate_all_prompts
from fp.scoring.scorer import score_all
from fp.output.export import export_json, export_csv
from fp.models import ProjectState

router = APIRouter()


# ─── Helpers ──────────────────────────────────────────────────────────────────


def _phase_status(state: ProjectState | None) -> dict:
    """Return completion status for each pipeline phase.

    Returns dict with the shape specified by the frontend:
    {
      "research": {"completed": bool, "count": int, "total": int},
      "discover":  {"completed": bool, "count": int, "total": int},
      "generate":  {"completed": bool, "count": int, "total": int},
      "score":     {"completed": bool, "count": int, "total": int},
    }
    """
    if not state:
        return {
            "research": {"completed": False, "count": 0, "total": 0},
            "discover": {"completed": False, "count": 0, "total": 0},
            "generate": {"completed": False, "count": 0, "total": 0},
            "score": {"completed": False, "count": 0, "total": 0},
        }

    # Research: completed if web_data has queries
    has_research = (
        state.web_data is not None
        and state.web_data.get("stats", {}).get("total_queries", 0) > 0
    )
    research_count = (
        state.web_data.get("stats", {}).get("total_queries", 0)
        if state.web_data
        else 0
    )

    # Discover: completed if focuses exist with signals
    has_focuses = len(state.focuses) > 0
    total_focuses = len(state.focuses)

    # Generate: completed if focuses have prompts
    total_prompts = sum(len(f.prompts) for f in state.focuses)
    has_prompts = total_prompts > 0

    # Score: completed if prompts have scores
    scored_count = sum(
        1 for f in state.focuses for p in f.prompts if p.overall_score > 0
    )
    has_scores = scored_count > 0 and scored_count == total_prompts

    return {
        "research": {
            "completed": has_research,
            "count": research_count,
            "total": research_count,
        },
        "discover": {
            "completed": has_focuses,
            "count": total_focuses,
            "total": total_focuses,
        },
        "generate": {
            "completed": has_prompts,
            "count": total_prompts,
            "total": total_prompts,
        },
        "score": {
            "completed": has_scores,
            "count": scored_count,
            "total": total_prompts,
        },
    }


def _sse(event: str, data: str) -> str:
    """Format a single SSE message."""
    return f"event: {event}\ndata: {data}\n\n"


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


# ─── API Routes (JSON) ────────────────────────────────────────────────────────


@router.get("/pipeline/status")
async def pipeline_status(request: Request):
    """Return completion status for each pipeline phase."""
    state = get_state()
    return _phase_status(state)


@router.get("/pipeline/scores")
async def pipeline_scores(request: Request):
    """Return all scored prompts sorted by score ascending (worst first)."""
    state = get_state()
    if not state:
        return []

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
                    "method": "llm",
                    "explanation": f"service_match={prompt.service_match:.0f} mention={prompt.mention_likelihood:.0f}",
                })

    scored.sort(key=lambda x: x["score"])
    return scored


@router.get("/pipeline/run-all")
async def run_all_phases(request: Request):
    """Run all pipeline phases sequentially via SSE stream, skipping completed phases."""
    state = get_state()
    if not state:
        async def _empty():
            yield _sse("error", json.dumps({"message": "No project found."}))
        return StreamingResponse(_empty(), media_type="text/event-stream")

    brand = state.config.brand

    async def generate() -> AsyncGenerator[str, None]:
        nonlocal state

        def _phase(event: str, **kwargs) -> str:
            return _sse("phase", json.dumps(kwargs | {"phase": event}))

        def _done(**kwargs) -> str:
            return _sse("done", json.dumps(kwargs))

        # ── Phase 1: Research ──────────────────────────────────────────
        status = _phase_status(state)
        if not status["research"]["completed"]:
            yield _phase("research", status="running")
            try:
                web_data = await research_queries(brand)
                state.web_data = web_data
                save_state(state)
                yield _phase("research", status="completed")
            except Exception as e:
                yield _phase("research", status="error", message=str(e))
                yield _done(status="error", phase="research")
                return
        else:
            yield _phase("research", status="skipped")

        # ── Phase 2: Discover ──────────────────────────────────────────
        state = get_state()  # reload after save
        assert state is not None
        status = _phase_status(state)
        if not status["discover"]["completed"]:
            yield _phase("discover", status="running")
            try:
                web_data = getattr(state, "web_data", None)
                if web_data and web_data.get("stats", {}).get("total_queries", 0) > 0:
                    problems = await discover_problems_enriched(brand, web_data, language=state.config.language)
                else:
                    problems = discover_problems(brand, language=state.config.language)

                if not problems:
                    yield _phase("discover", status="error", message="No problems discovered")
                    yield _done(status="error", phase="discover")
                    return

                focuses = generate_focuses(brand, problems, language=state.config.language)
                state.focuses = focuses
                save_state(state)
                yield _phase("discover", status="completed")
            except Exception as e:
                yield _phase("discover", status="error", message=str(e))
                yield _done(status="error", phase="discover")
                return
        else:
            yield _phase("discover", status="skipped")

        # ── Phase 3: Generate ──────────────────────────────────────────
        state = get_state()
        assert state is not None
        status = _phase_status(state)
        if not status["generate"]["completed"]:
            yield _phase("generate", status="running")
            try:
                if not state.focuses:
                    yield _phase("generate", status="error", message="No focuses found")
                    yield _done(status="error", phase="generate")
                    return

                updated = generate_all_prompts(brand, state.focuses, state.config.prompt_mode, language=state.config.language)
                state.focuses = updated
                save_state(state)
                yield _phase("generate", status="completed")
            except Exception as e:
                yield _phase("generate", status="error", message=str(e))
                yield _done(status="error", phase="generate")
                return
        else:
            yield _phase("generate", status="skipped")

        # ── Phase 4: Score ─────────────────────────────────────────────
        state = get_state()
        assert state is not None
        status = _phase_status(state)
        if not status["score"]["completed"]:
            yield _phase("score", status="running")
            try:
                if not state.focuses or not any(f.prompts for f in state.focuses):
                    yield _phase("score", status="error", message="No prompts to score")
                    yield _done(status="error", phase="score")
                    return

                scored = score_all(state.focuses, brand)
                state.focuses = scored
                save_state(state)
                yield _phase("score", status="completed")
            except Exception as e:
                yield _phase("score", status="error", message=str(e))
                yield _done(status="error", phase="score")
                return
        else:
            yield _phase("score", status="skipped")

        yield _done(status="completed")

    return StreamingResponse(generate(), media_type="text/event-stream")


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
        resp = HTMLResponse(f'''
            <div class="space-y-2">
                <p class="text-green-600 font-medium">✓ Research complete</p>
                <p class="text-sm">Autocomplete: {stats["autocomplete_count"]} suggestions</p>
                <p class="text-sm">Total queries: {stats["total_queries"]}</p>
                <p class="text-sm text-gray-500">Sample: {", ".join(web_data["autocomplete"][:5])}</p>
            </div>
        ''')
        resp.headers["HX-Trigger"] = json.dumps({"phaseComplete": {"phase": "research", "completed": True}})
        return resp
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
            problems = await discover_problems_enriched(brand, web_data, language=state.config.language)
        else:
            problems = discover_problems(brand, language=state.config.language)
    except Exception as e:
        return HTMLResponse(f'<p class="text-red-600">Discovery failed: {e}</p>')

    if not problems:
        return HTMLResponse('<p class="text-yellow-600">No problems discovered.</p>')

    try:
        focuses = generate_focuses(brand, problems, language=state.config.language)
        state.focuses = focuses
        save_state(state)
        items = "".join(
            f'<li class="text-sm"><strong>{f.name}</strong> — {f.signal_count} signals</li>'
            for f in focuses
        )
        resp = HTMLResponse(f'''
            <div class="space-y-2">
                <p class="text-green-600 font-medium">✓ Discovered {len(focuses)} focuses</p>
                <ul class="list-disc list-inside text-sm text-gray-700">{items}</ul>
            </div>
        ''')
        resp.headers["HX-Trigger"] = json.dumps({"phaseComplete": {"phase": "discover", "completed": True}})
        return resp
    except Exception as e:
        return HTMLResponse(f'<p class="text-red-600">Focus generation failed: {e}</p>')


@router.post("/generate", response_class=HTMLResponse)
async def run_generate(request: Request):
    """Run generate step."""
    state = get_state()
    if not state or not state.focuses:
        return HTMLResponse('<p class="text-red-600">No focuses. Run discover first.</p>')

    try:
        updated = generate_all_prompts(state.config.brand, state.focuses, state.config.prompt_mode, language=state.config.language)
        state.focuses = updated
        save_state(state)
        total = sum(len(f.prompts) for f in state.focuses)
        resp = HTMLResponse(f'''
            <div class="space-y-2">
                <p class="text-green-600 font-medium">✓ Generated {total} prompts</p>
                <p class="text-sm text-gray-500">Across {len(state.focuses)} focuses</p>
            </div>
        ''')
        resp.headers["HX-Trigger"] = json.dumps({"phaseComplete": {"phase": "generate", "completed": True}})
        return resp
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
        resp = HTMLResponse(f'''
            <div class="space-y-2">
                <p class="text-green-600 font-medium">✓ Scoring complete</p>
                <p class="text-sm text-gray-500">{total_prompts} prompts scored, {needs_review} need review</p>
            </div>
        ''')
        resp.headers["HX-Trigger"] = json.dumps({"phaseComplete": {"phase": "score", "completed": True}})
        return resp
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


# ─── Keep/Discard/Regenerate Endpoints ──────────────────────────────────────


@router.post("/pipeline/step/{step}/keep")
async def keep_items(request: Request, step: str):
    """Save which items to keep; discard unchecked items."""
    state = get_state()
    if not state:
        return {"status": "error", "message": "No project found"}

    try:
        body = await request.json()
        keep_ids = body.get("keep_ids", [])
    except Exception:
        keep_ids = []

    if step == "research":
        # Research items are queries - mark which to keep in web_data
        if state.web_data and "queries" in state.web_data:
            all_queries = state.web_data.get("queries", [])
            keep_set = set(keep_ids)
            kept = [q for q in all_queries if str(q.get("id", "")) in keep_set or q.get("text", "") in keep_set]
            discarded = len(all_queries) - len(kept)
            state.web_data["queries"] = kept
            state.web_data["stats"]["total_queries"] = len(kept)
            save_state(state)
            return {"status": "ok", "kept": len(kept), "discarded": discarded}

    elif step == "discover":
        # Keep only selected focuses
        all_focuses = state.focuses
        keep_set = set(keep_ids)
        kept = [f for f in all_focuses if str(f.name) in keep_set]
        discarded = len(all_focuses) - len(kept)
        state.focuses = kept
        save_state(state)
        return {"status": "ok", "kept": len(kept), "discarded": discarded}

    elif step == "generate":
        # Keep only selected prompts per focus
        keep_set = set(keep_ids)
        total_kept = 0
        total_discarded = 0
        for focus in state.focuses:
            kept_prompts = []
            for p in focus.prompts:
                pid = f"{focus.name}-{p.text[:30]}"
                if pid in keep_set or p.text in keep_set:
                    kept_prompts.append(p)
                    total_kept += 1
                else:
                    total_discarded += 1
            focus.prompts = kept_prompts
        save_state(state)
        return {"status": "ok", "kept": total_kept, "discarded": total_discarded}

    elif step == "score":
        # Scores are derived from prompts - no separate keep needed
        return {"status": "ok", "kept": 0, "discarded": 0}

    return {"status": "ok", "kept": 0, "discarded": 0}


@router.post("/pipeline/step/{step}/regenerate")
async def regenerate_items(request: Request, step: str):
    """Regenerate items for specified focuses or items."""
    state = get_state()
    if not state:
        return {"status": "error", "message": "No project found"}

    try:
        body = await request.json()
        regenerate_ids = body.get("regenerate_ids", [])
    except Exception:
        regenerate_ids = []

    brand = state.config.brand
    language = state.config.language

    if step == "research":
        # Regenerate queries for research
        from fp.research.web import research_queries
        web_data = await research_queries(brand, extra_queries=regenerate_ids if regenerate_ids else None)
        state.web_data = web_data
        save_state(state)
        return {"status": "ok", "regenerating": 1}

    elif step == "discover":
        # Regenerate focuses
        from fp.enrichment.problems import discover_problems, discover_problems_enriched
        from fp.generate.focuses import generate_focuses
        web_data = getattr(state, "web_data", None)
        if web_data and web_data.get("stats", {}).get("total_queries", 0) > 0:
            problems = await discover_problems_enriched(brand, web_data, language=language)
        else:
            problems = discover_problems(brand, language=language)
        focuses = generate_focuses(brand, problems, language=language)
        state.focuses = focuses
        save_state(state)
        return {"status": "ok", "regenerating": len(focuses)}

    elif step == "generate":
        # Regenerate prompts for specified focuses
        from fp.generate.prompts import generate_all_prompts
        if regenerate_ids:
            # Only regenerate for specific focuses
            focuses_to_regen = [f for f in state.focuses if f.name in regenerate_ids]
            if focuses_to_regen:
                updated = generate_all_prompts(brand, focuses_to_regen, state.config.prompt_mode, language=language)
                # Merge back
                for i, f in enumerate(state.focuses):
                    if f.name in regenerate_ids:
                        state.focuses[i] = updated[[u.name for u in updated].index(f.name)]
        else:
            # Regenerate all
            updated = generate_all_prompts(brand, state.focuses, state.config.prompt_mode, language=language)
            state.focuses = updated
        save_state(state)
        return {"status": "ok", "regenerating": len(regenerate_ids) if regenerate_ids else len(state.focuses)}

    elif step == "score":
        # Re-score all prompts
        from fp.scoring.scorer import score_all
        scored = score_all(state.focuses, brand)
        state.focuses = scored
        save_state(state)
        return {"status": "ok", "regenerating": 1}

    return {"status": "ok", "regenerating": 0}
