# Domain Auto-Detect Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add "Auto-detect from domain" to the init page — user enters a domain, EXA + LLM research fills brand details, user reviews and edits before submitting.

**Architecture:** Synchronous EXA + LLM research returns pre-filled brand data. HTMX swaps the init form with a review form. No model changes — Brand model already has all needed fields.

**Tech Stack:** Python 3.11+, FastAPI, HTMX, Jinja2, httpx (EXA), LiteLLM (LLM inference)

## Global Constraints

- Python 3.11+
- Pydantic v2 models
- HTMX 2.0.4 (CDN)
- Tailwind CSS (CDN)
- EXA_API_KEY required for auto-detect, graceful fallback if missing
- LLM calls via `fp.llm.completion_json()` with auto-resolved model

---

## File Structure

| File | Action | Responsibility |
|------|--------|---------------|
| `fp/research/autodetect.py` | Create | Core research logic: EXA + LLM → brand data dict |
| `fp/web/templates/init_review.html` | Create | Pre-filled editable review form template |
| `fp/web/templates/init.html` | Modify | Add auto-detect input section above existing form |
| `fp/web/routes/pages.py` | Modify | Add `POST /init/research` endpoint |
| `tests/research/test_autodetect.py` | Create | Unit tests for autodetect module |
| `tests/web/test_pages.py` | Modify | Add test for new `/init/research` route |

---

### Task 1: Create `fp/research/autodetect.py` — Core Research Logic

**Files:**
- Create: `fp/research/autodetect.py`
- Test: `tests/research/test_autodetect.py`

**Interfaces:**
- Consumes: `fp.research.exa.fetch_exa_batch()` (existing), `fp.llm.completion_json()` (existing)
- Produces: `research_brand(domain: str, model: str = "") -> dict` — returns `{name, description, website, service_categories, competitors, confidence}`

- [ ] **Step 1: Write the failing test**

```python
"""Tests for fp.research.autodetect — domain auto-detection."""
from __future__ import annotations

from unittest.mock import patch, AsyncMock
import pytest


@pytest.mark.asyncio
@patch("fp.research.autodetect.fetch_exa_batch")
@patch("fp.research.autodetect.completion_json")
async def test_research_brand_returns_structured_data(mock_llm, mock_exa):
    """research_brand should return dict with all Brand fields."""
    from fp.research.autodetect import research_brand

    mock_exa.return_value = [
        {
            "query": "acme.com",
            "results": [
                {"title": "ACME Corp - Enterprise Software", "url": "https://acme.com", "snippet": "ACME provides SaaS analytics"}
            ]
        }
    ]
    mock_llm.return_value = {
        "name": "ACME Corp",
        "description": "Enterprise software solutions",
        "service_categories": ["SaaS", "Analytics"],
        "competitors": ["Zoom", "Slack"],
        "confidence": 0.85
    }

    result = await research_brand("acme.com")

    assert result["name"] == "ACME Corp"
    assert result["description"] == "Enterprise software solutions"
    assert result["website"] == "https://acme.com"
    assert result["service_categories"] == ["SaaS", "Analytics"]
    assert result["competitors"] == ["Zoom", "Slack"]
    assert result["confidence"] == 0.85


@pytest.mark.asyncio
@patch("fp.research.autodetect.fetch_exa_batch")
@patch("fp.research.autodetect.completion_json")
async def test_research_brand_website_always_https(mock_llm, mock_exa):
    """website field should always start with https://."""
    from fp.research.autodetect import research_brand

    mock_exa.return_value = []
    mock_llm.return_value = {
        "name": "Test Co",
        "description": "Test",
        "service_categories": [],
        "competitors": [],
        "confidence": 0.3
    }

    result = await research_brand("test.com")
    assert result["website"] == "https://test.com"


@pytest.mark.asyncio
@patch("fp.research.autodetect.fetch_exa_batch")
@patch("fp.research.autodetect.completion_json")
async def test_research_brand_low_confidence_when_no_exa(mock_llm, mock_exa):
    """Confidence should be LOW when EXA returns no results."""
    from fp.research.autodetect import research_brand

    mock_exa.return_value = []
    mock_llm.return_value = {
        "name": "Unknown Co",
        "description": "Unknown",
        "service_categories": [],
        "competitors": [],
        "confidence": 0.2
    }

    result = await research_brand("unknown.com")
    assert result["confidence"] < 0.4
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /Users/admin/Documents/GitHub/focus-prompt && python -m pytest tests/research/test_autodetect.py -v`
Expected: FAIL — module `fp.research.autodetect` does not exist

- [ ] **Step 3: Write the implementation**

```python
"""Domain auto-detect — research brand info from domain via EXA + LLM."""
from __future__ import annotations

from fp.research.exa import fetch_exa_batch
from fp.llm import completion_json


SYSTEM_PROMPT = """You are a brand analyst. Given web research data about a domain, extract structured brand information.

Return a JSON object with exactly these keys:
- name: string — the brand/company name
- description: string — one-sentence description of what the brand does
- service_categories: list of strings — the main service/product categories
- competitors: list of strings — 2-5 direct competitor brand names
- confidence: float 0.0-1.0 — how confident you are in this extraction

Rules:
- Be specific about service categories (e.g. "SaaS" not "software")
- Competitors should be real, well-known brands in the same space
- If data is ambiguous, make your best guess and set confidence lower
- confidence HIGH (0.8-1.0): clear brand data from web results
- confidence MEDIUM (0.4-0.79): partial data, some guessing
- confidence LOW (0.0-0.39): minimal data, mostly guessing"""


def _format_exa_results(exa_data: list[dict]) -> str:
    """Format EXA search results into context string for LLM."""
    lines = []
    for batch in exa_data:
        for result in batch.get("results", []):
            title = result.get("title", "")
            snippet = result.get("snippet", "")
            url = result.get("url", "")
            if title or snippet:
                lines.append(f"- {title}: {snippet} [{url}]")
    return "\n".join(lines) if lines else "No web research data available."


async def research_brand(domain: str, model: str = "") -> dict:
    """Research a brand from its domain using EXA + LLM.

    Args:
        domain: The brand's domain (e.g. "acme.com")
        model: LLM model override (default: env FP_MODEL or gpt-4o-mini)

    Returns:
        Dict with keys: name, description, website, service_categories,
        competitors, confidence
    """
    # Step 1: EXA search for brand signals
    queries = [domain, f"{domain} services", f"{domain} competitors"]
    try:
        exa_data = await fetch_exa_batch(queries, limit_per_query=3)
    except Exception:
        exa_data = []

    # Step 2: Format context for LLM
    exa_context = _format_exa_results(exa_data)

    user_prompt = f"""Domain: {domain}

Web research results:
{exa_context}

Extract the brand information for this domain."""

    # Step 3: LLM inference
    try:
        result = completion_json(
            model=model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.3,
        )
    except Exception:
        # LLM failed — return minimal defaults
        return {
            "name": domain.split(".")[0].title(),
            "description": "",
            "website": f"https://{domain}",
            "service_categories": [],
            "competitors": [],
            "confidence": 0.0,
        }

    # Step 4: Normalize and return
    return {
        "name": result.get("name", domain.split(".")[0].title()),
        "description": result.get("description", ""),
        "website": f"https://{domain}",
        "service_categories": result.get("service_categories", []),
        "competitors": result.get("competitors", []),
        "confidence": max(0.0, min(1.0, result.get("confidence", 0.5))),
    }
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd /Users/admin/Documents/GitHub/focus-prompt && python -m pytest tests/research/test_autodetect.py -v`
Expected: All 3 tests PASS

- [ ] **Step 5: Commit**

```bash
git add fp/research/autodetect.py tests/research/test_autodetect.py
git commit -m "feat(research): add domain auto-detect module with EXA + LLM"
```

---

### Task 2: Create `fp/web/templates/init_review.html` — Review Form

**Files:**
- Create: `fp/web/templates/init_review.html`

**Interfaces:**
- Consumes: `brand` dict from `autodetect.research_brand()` (name, description, website, service_categories, competitors, confidence)
- Produces: HTML form that POSTs to `/api/init` (same endpoint as existing init)

- [ ] **Step 1: Create the template**

```html
{% extends "base.html" %}
{% block title %}Review Brand — Focus Prompt{% endblock %}
{% block content %}
<div class="max-w-xl" id="init-container">
    <h1 class="text-2xl font-bold text-white mb-4">New Project</h1>

    {# Confidence badge #}
    {% if brand.confidence >= 0.8 %}
    <div class="bg-emerald-500/10 border border-emerald-500/30 rounded-lg p-3 mb-4">
        <span class="text-emerald-400 text-sm">High confidence — auto-detected brand data looks solid</span>
    </div>
    {% elif brand.confidence >= 0.4 %}
    <div class="bg-amber-500/10 border border-amber-500/30 rounded-lg p-3 mb-4">
        <span class="text-amber-400 text-sm">Medium confidence — please verify all fields below</span>
    </div>
    {% else %}
    <div class="bg-red-500/10 border border-red-500/30 rounded-lg p-3 mb-4">
        <span class="text-red-400 text-sm">Low confidence — research had limited data, please verify carefully</span>
    </div>
    {% endif %}

    <form hx-post="/api/init" hx-target="#init-result" hx-indicator="#init-spinner" class="space-y-4 bg-slate-800 rounded-xl border border-slate-700/50 p-6">
        <div>
            <label class="block text-sm font-medium text-slate-300 mb-1">Brand Name *</label>
            <input type="text" name="name" value="{{ brand.name }}" required class="w-full bg-slate-700 border border-slate-600 rounded-lg px-3 py-2 text-sm text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent">
        </div>

        <div>
            <label class="block text-sm font-medium text-slate-300 mb-1">Description</label>
            <textarea name="description" rows="2" class="w-full bg-slate-700 border border-slate-600 rounded-lg px-3 py-2 text-sm text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent">{{ brand.description }}</textarea>
        </div>

        <div>
            <label class="block text-sm font-medium text-slate-300 mb-1">Website</label>
            <input type="url" name="website" value="{{ brand.website }}" class="w-full bg-slate-700 border border-slate-600 rounded-lg px-3 py-2 text-sm text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent">
        </div>

        <div>
            <label class="block text-sm font-medium text-slate-300 mb-1">Service Categories (comma-separated)</label>
            <input type="text" name="services" value="{{ brand.service_categories | join(', ') }}" class="w-full bg-slate-700 border border-slate-600 rounded-lg px-3 py-2 text-sm text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent">
        </div>

        <div>
            <label class="block text-sm font-medium text-slate-300 mb-1">Competitors (comma-separated)</label>
            <input type="text" name="competitors" value="{{ brand.competitors | join(', ') }}" class="w-full bg-slate-700 border border-slate-600 rounded-lg px-3 py-2 text-sm text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent">
        </div>

        <div class="grid grid-cols-2 gap-4">
            <div>
                <label class="block text-sm font-medium text-slate-300 mb-1">Prompt Mode</label>
                <select name="mode" class="w-full bg-slate-700 border border-slate-600 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent">
                    <option value="unbranded">Unbranded</option>
                    <option value="branded">Branded</option>
                    <option value="both">Both</option>
                </select>
            </div>
            <div>
                <label class="block text-sm font-medium text-slate-300 mb-1">Language</label>
                <select name="language" class="w-full bg-slate-700 border border-slate-600 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent">
                    <option value="id">Indonesian</option>
                    <option value="en">English</option>
                    <option value="mix">Mixed</option>
                </select>
            </div>
        </div>

        <div class="flex items-center gap-3 pt-2">
            <a href="/init" class="px-4 py-2 bg-slate-700 hover:bg-slate-600 text-white text-sm font-medium rounded-lg transition-colors">
                ← Back
            </a>
            <button type="submit" class="flex items-center gap-2 px-5 py-2.5 bg-blue-600 hover:bg-blue-500 text-white font-medium rounded-lg transition-colors">
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"/>
                </svg>
                Create Project
            </button>
            <span id="init-spinner" class="htmx-indicator text-sm text-slate-400">
                <svg class="animate-spin h-4 w-4 inline mr-1" fill="none" viewBox="0 0 24 24">
                    <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                    <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                Creating...
            </span>
        </div>
    </form>

    <div id="init-result" class="mt-4"></div>
</div>
{% endblock %}
```

- [ ] **Step 2: Verify template renders (manual)**

Start the web server: `cd /Users/admin/Documents/GitHub/focus-prompt && python -m fp.web.app`
This task has no automated test — template correctness verified in Task 4 integration test.

- [ ] **Step 3: Commit**

```bash
git add fp/web/templates/init_review.html
git commit -m "feat(web): add init review form template for auto-detect"
```

---

### Task 3: Modify `init.html` — Add Auto-Detect Section

**Files:**
- Modify: `fp/web/templates/init.html`

**Interfaces:**
- Consumes: nothing (standalone input)
- Produces: HTMX POST to `/init/research`, swaps `#init-container`

- [ ] **Step 1: Wrap existing form in `#init-container` and add auto-detect section**

Replace the entire content of `fp/web/templates/init.html`:

```html
{% extends "base.html" %}
{% block title %}New Project — Focus Prompt{% endblock %}
{% block content %}
<div class="max-w-xl" id="init-container">
    <h1 class="text-2xl font-bold text-white mb-6">New Project</h1>

    {# Auto-detect from domain #}
    <div class="bg-slate-800 rounded-xl border border-slate-700/50 p-6 mb-6">
        <h2 class="text-lg font-semibold text-white mb-1">Auto-detect from domain</h2>
        <p class="text-sm text-slate-400 mb-3">Enter a domain and AI will research the brand for you</p>
        <form hx-post="/init/research" hx-target="#init-container" hx-indicator="#autodetect-spinner">
            <div class="flex gap-2">
                <input type="text" name="domain" placeholder="acme.com" required
                       class="flex-1 bg-slate-700 border border-slate-600 rounded-lg px-3 py-2 text-sm text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent">
                <button type="submit" class="px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white text-sm font-medium rounded-lg transition-colors flex items-center gap-2">
                    Auto-detect
                    <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 7l5 5m0 0l-5 5m5-5H6"/>
                    </svg>
                </button>
            </div>
            <span id="autodetect-spinner" class="htmx-indicator text-sm text-slate-400 mt-2 inline-flex items-center gap-1">
                <svg class="animate-spin h-3 w-3" fill="none" viewBox="0 0 24 24">
                    <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                    <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                Researching brand...
            </span>
        </form>
    </div>

    {# Divider #}
    <div class="flex items-center gap-3 my-6">
        <div class="flex-1 border-t border-slate-700"></div>
        <span class="text-xs text-slate-500 uppercase tracking-wide">or fill manually</span>
        <div class="flex-1 border-t border-slate-700"></div>
    </div>

    {# Manual form (unchanged) #}
    <form hx-post="/api/init" hx-target="#init-result" hx-indicator="#init-spinner" class="space-y-4 bg-slate-800 rounded-xl border border-slate-700/50 p-6">
        <div>
            <label class="block text-sm font-medium text-slate-300 mb-1">Brand Name *</label>
            <input type="text" name="name" required class="w-full bg-slate-700 border border-slate-600 rounded-lg px-3 py-2 text-sm text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent">
        </div>

        <div>
            <label class="block text-sm font-medium text-slate-300 mb-1">Description</label>
            <textarea name="description" rows="2" class="w-full bg-slate-700 border border-slate-600 rounded-lg px-3 py-2 text-sm text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"></textarea>
        </div>

        <div>
            <label class="block text-sm font-medium text-slate-300 mb-1">Website</label>
            <input type="url" name="website" placeholder="https://example.com" class="w-full bg-slate-700 border border-slate-600 rounded-lg px-3 py-2 text-sm text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent">
        </div>

        <div>
            <label class="block text-sm font-medium text-slate-300 mb-1">Service Categories (comma-separated)</label>
            <input type="text" name="services" placeholder="desain, programming, copywriting" class="w-full bg-slate-700 border border-slate-600 rounded-lg px-3 py-2 text-sm text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent">
        </div>

        <div>
            <label class="block text-sm font-medium text-slate-300 mb-1">Competitors (comma-separated)</label>
            <input type="text" name="competitors" placeholder="Fastwork, Fiverr" class="w-full bg-slate-700 border border-slate-600 rounded-lg px-3 py-2 text-sm text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent">
        </div>

        <div class="grid grid-cols-2 gap-4">
            <div>
                <label class="block text-sm font-medium text-slate-300 mb-1">Prompt Mode</label>
                <select name="mode" class="w-full bg-slate-700 border border-slate-600 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent">
                    <option value="unbranded">Unbranded</option>
                    <option value="branded">Branded</option>
                    <option value="both">Both</option>
                </select>
            </div>
            <div>
                <label class="block text-sm font-medium text-slate-300 mb-1">Language</label>
                <select name="language" class="w-full bg-slate-700 border border-slate-600 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent">
                    <option value="id">Indonesian</option>
                    <option value="en">English</option>
                    <option value="mix">Mixed</option>
                </select>
            </div>
        </div>

        <div class="flex items-center gap-3 pt-2">
            <button type="submit" class="flex items-center gap-2 px-5 py-2.5 bg-blue-600 hover:bg-blue-500 text-white font-medium rounded-lg transition-colors">
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"/>
                </svg>
                Create Project
            </button>
            <span id="init-spinner" class="htmx-indicator text-sm text-slate-400">
                <svg class="animate-spin h-4 w-4 inline mr-1" fill="none" viewBox="0 0 24 24">
                    <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                    <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                Creating...
            </span>
        </div>
    </form>

    <div id="init-result" class="mt-4"></div>
</div>
{% endblock %}
```

- [ ] **Step 2: Commit**

```bash
git add fp/web/templates/init.html
git commit -m "feat(web): add auto-detect domain input to init page"
```

---

### Task 4: Add `POST /init/research` Route

**Files:**
- Modify: `fp/web/routes/pages.py` — add import + new endpoint
- Modify: `tests/web/test_pages.py` — add tests for new route

**Interfaces:**
- Consumes: `autodetect.research_brand()` from Task 1
- Produces: HTMLResponse with `init_review.html` template rendered with brand data

- [ ] **Step 1: Write the failing test**

Add to `tests/web/test_pages.py`:

```python
# ── POST /init/research ──────────────────────────────────────────────

@patch("fp.web.routes.pages.research_brand")
def test_init_research_returns_html_response(mock_research):
    """POST /init/research should return an HTML response."""
    mock_research.return_value = {
        "name": "ACME Corp",
        "description": "Enterprise software",
        "website": "https://acme.com",
        "service_categories": ["SaaS"],
        "competitors": ["Zoom"],
        "confidence": 0.8,
    }
    app, mock_templates = _make_app()
    client = TestClient(app)

    response = client.post("/init/research", data={"domain": "acme.com"})

    assert response.status_code == 200
    mock_templates.TemplateResponse.assert_called_once()


@patch("fp.web.routes.pages.research_brand")
def test_init_research_passes_brand_in_context(mock_research):
    """POST /init/research should pass brand data in template context."""
    brand_data = {
        "name": "ACME Corp",
        "description": "Enterprise software",
        "website": "https://acme.com",
        "service_categories": ["SaaS"],
        "competitors": ["Zoom"],
        "confidence": 0.8,
    }
    mock_research.return_value = brand_data
    app, mock_templates = _make_app()
    client = TestClient(app)

    client.post("/init/research", data={"domain": "acme.com"})

    call_args = mock_templates.TemplateResponse.call_args
    context = call_args[0][2]
    assert context["brand"] == brand_data


@patch("fp.web.routes.pages.research_brand")
def test_init_research_handles_error_gracefully(mock_research):
    """POST /init/research should return error HTML when research fails."""
    mock_research.side_effect = Exception("EXA API down")
    app, mock_templates = _make_app()
    client = TestClient(app)

    response = client.post("/init/research", data={"domain": "acme.com"})

    assert response.status_code == 200
    assert "error" in response.text.lower() or "failed" in response.text.lower()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /Users/admin/Documents/GitHub/focus-prompt && python -m pytest tests/web/test_pages.py -v -k "init_research"`
Expected: FAIL — route `/init/research` not found (405 Method Not Allowed)

- [ ] **Step 3: Add the route to `fp/web/routes/pages.py`**

Add import at top of `pages.py`:

```python
from fp.research.autodetect import research_brand
```

Add new endpoint after the existing `init_page` GET route:

```python
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
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd /Users/admin/Documents/GitHub/focus-prompt && python -m pytest tests/web/test_pages.py -v -k "init_research"`
Expected: All 3 tests PASS

- [ ] **Step 5: Run full test suite**

Run: `cd /Users/admin/Documents/GitHub/focus-prompt && python -m pytest tests/ -v`
Expected: All tests PASS (no regressions)

- [ ] **Step 6: Commit**

```bash
git add fp/web/routes/pages.py tests/web/test_pages.py
git commit -m "feat(web): add POST /init/research endpoint for auto-detect"
```

---

### Task 5: Integration Test — End-to-End Auto-Detect Flow

**Files:**
- Modify: `tests/web/test_pages.py` — add integration test

**Interfaces:**
- Tests the full flow: POST `/init/research` → template renders with brand data → form POSTs to `/api/init`

- [ ] **Step 1: Write the integration test**

Add to `tests/web/test_pages.py`:

```python
# ── Integration: auto-detect flow ─────────────────────────────────────

@patch("fp.web.routes.pages.research_brand")
@patch("fp.web.routes.pages.save_state")
def test_init_research_then_submit_creates_project(mock_save, mock_research):
    """Full flow: auto-detect returns brand data, user submits form, project created."""
    brand_data = {
        "name": "ACME Corp",
        "description": "Enterprise software",
        "website": "https://acme.com",
        "service_categories": ["SaaS", "Analytics"],
        "competitors": ["Zoom", "Slack"],
        "confidence": 0.85,
    }
    mock_research.return_value = brand_data

    app, mock_templates = _make_app()
    # Register the pipeline router too so /api/init works
    from fp.web.routes.pipeline import router as pipeline_router
    app.include_router(pipeline_router, prefix="/api")
    client = TestClient(app)

    # Step 1: Auto-detect
    response = client.post("/init/research", data={"domain": "acme.com"})
    assert response.status_code == 200

    # Step 2: Submit the review form (simulating user clicking "Create Project")
    response = client.post("/api/init", data={
        "name": "ACME Corp",
        "description": "Enterprise software",
        "website": "https://acme.com",
        "services": "SaaS, Analytics",
        "competitors": "Zoom, Slack",
        "mode": "unbranded",
        "language": "id",
    })
    assert response.status_code == 200
    mock_save.assert_called_once()
```

- [ ] **Step 2: Run the integration test**

Run: `cd /Users/admin/Documents/GitHub/focus-prompt && python -m pytest tests/web/test_pages.py -v -k "integration"`
Expected: PASS

- [ ] **Step 3: Run full test suite**

Run: `cd /Users/admin/Documents/GitHub/focus-prompt && python -m pytest tests/ -v`
Expected: All tests PASS

- [ ] **Step 4: Commit**

```bash
git add tests/web/test_pages.py
git commit -m "test(web): add integration test for auto-detect init flow"
```

---

### Task 6: Manual Verification

- [ ] **Step 1: Start web server**

```bash
cd /Users/admin/Documents/GitHub/focus-prompt && python -m fp.web.app
```

- [ ] **Step 2: Test auto-detect flow in browser**

1. Open `http://127.0.0.1:8000/init`
2. Verify: auto-detect section appears above manual form with divider
3. Enter a known domain (e.g., "stripe.com") in auto-detect input
4. Click "Auto-detect" — verify spinner appears
5. Verify: review form appears with pre-filled fields
6. Verify: confidence badge shows correct level
7. Edit a field (e.g., change description)
8. Click "Create Project" — verify redirect to pipeline

- [ ] **Step 3: Test manual path still works**

1. Go to `/init`
2. Fill manual form directly
3. Click "Create Project" — verify it works as before

- [ ] **Step 4: Test error handling**

1. Enter an invalid/garbage domain
2. Verify: graceful degradation (error message or low confidence)
3. Verify: "← Back to manual entry" link works
