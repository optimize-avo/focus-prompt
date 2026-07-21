# Design: Domain Auto-Detect for Brand Init

**Date:** 2026-07-21
**Status:** Approved
**Scope:** Web UI only (CLI/MCP unchanged)

## Problem

The current `init` flow requires users to manually fill in brand name, description, service categories, and competitors. This is tedious and error-prone — users often don't know their competitors offhand or struggle to articulate service categories. The tool already has EXA search integration and LLM capabilities that could auto-detect this information from a domain.

## Solution

Add an "Auto-detect from domain" path to the init page alongside the existing manual form. User enters a domain, AI + EXA research fills in brand details, user reviews and edits before submitting.

## Design Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Init flow | Dual path (auto-detect + manual) | Preserves existing manual flow for power users |
| Research method | Synchronous EXA + LLM (single POST) | <10s latency, no need for SSE complexity |
| Low confidence | Always proceed, show badge | Degrades gracefully, never blocks user |
| Review UX | Full editable form pre-filled | Maximum flexibility for user corrections |
| CLI impact | None | CLI users typically know their brand info |

## Architecture

### New Files

- `fp/research/autodetect.py` — Core research logic
- `fp/web/templates/init_review.html` — Pre-filled review form template

### Modified Files

- `fp/web/templates/init.html` — Add auto-detect input section above existing form
- `fp/web/routes/pages.py` — Add `POST /init/research` endpoint

### Unchanged

- `fp/models.py` — Brand model has all needed fields already
- `fp/research/exa.py` — Existing EXA integration reused
- `fp/research/web.py` — Unchanged (runs later in pipeline)
- CLI, MCP server, all downstream pipeline steps

## Data Flow

```
User enters "acme.com" → clicks "Auto-detect"
    ↓
HTMX POST /init/research (HX-Trigger swaps init container)
    ↓
autodetect.research_brand(domain: str) → dict
  1. fetch_exa_batch([domain, "{domain} services", "{domain} competitors"])
  2. LLM prompt: extract brand info from EXA results
  3. Return {name, description, website, service_categories, competitors, confidence}
    ↓
Render init_review.html with pre-filled form (all editable)
    ↓
User edits → POST /api/init → saves brand (same endpoint as today)
```

## New Module: `fp/research/autodetect.py`

```python
async def research_brand(domain: str, model: str = "") -> dict:
    """Research a brand from its domain.

    Returns dict with keys:
    - name: str
    - description: str
    - website: str (always "https://{domain}")
    - service_categories: list[str]
    - competitors: list[str]
    - confidence: float (0.0-1.0)
    """
```

### Step 1: EXA Search

- Query the domain directly: `fetch_exa_batch([domain])`
- Also query: `"{domain} services"`, `"{domain} competitors"`
- Extract: page titles, snippets, URLs as context signals
- If EXA fails or returns nothing, skip — rely on LLM knowledge

### Step 2: LLM Inference

- System prompt: "You are a brand analyst. Given web research data about {domain}, extract structured brand information. Be specific about service categories and competitors. If data is ambiguous, make your best guess and note low confidence."
- Input: EXA results (title + snippet per result)
- Output: JSON matching Brand fields
- Fallback: if no EXA data, LLM uses its own knowledge about the brand

### Step 3: Confidence Scoring

- **HIGH** (0.8-1.0): EXA found clear brand pages + LLM extracted all fields
- **MEDIUM** (0.4-0.79): Partial EXA data or LLM filled some fields with uncertainty
- **LOW** (0.0-0.39): No EXA data, LLM guessing based on domain name only

Confidence does not block anything — it hints to the user in the review form.

## UI Changes

### Init Page (`init.html`)

Wrap the existing content in a `<div id="init-container">` so HTMX can swap the whole container. Add auto-detect section above the existing form inside this container:

```html
<div class="bg-slate-800 rounded-xl border border-slate-700/50 p-6 mb-6">
  <h2 class="text-lg font-semibold text-white mb-3">Auto-detect from domain</h2>
  <form hx-post="/init/research" hx-target="#init-container" hx-indicator="#autodetect-spinner">
    <div class="flex gap-2">
      <input type="text" name="domain" placeholder="acme.com" required
             class="flex-1 bg-slate-700 border border-slate-600 rounded-lg px-3 py-2 text-sm text-white">
      <button type="submit" class="px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white text-sm font-medium rounded-lg">
        Auto-detect →
      </button>
    </div>
    <span id="autodetect-spinner" class="htmx-indicator text-sm text-slate-400 mt-2">
      Researching brand...
    </span>
  </form>
</div>

<!-- Divider -->
<div class="flex items-center gap-3 my-6">
  <div class="flex-1 border-t border-slate-700"></div>
  <span class="text-xs text-slate-500 uppercase">or fill manually</span>
  <div class="flex-1 border-t border-slate-700"></div>
</div>

<!-- Existing form stays here unchanged -->
```

### Review Form (`init_review.html`)

After auto-detect completes, the entire `#init-container` swaps with the review form:

```html
<div id="init-container">
  <!-- Confidence badge -->
  <div class="bg-amber-500/10 border border-amber-500/30 rounded-lg p-3 mb-4">
    <span class="text-amber-400 text-sm">🟡 Medium Confidence — please verify all fields below</span>
  </div>

  <form hx-post="/api/init" hx-target="#init-result" class="space-y-4 bg-slate-800 rounded-xl border border-slate-700/50 p-6">
    <!-- All fields pre-filled, fully editable -->
    <div>
      <label class="block text-sm font-medium text-slate-300 mb-1">Brand Name *</label>
      <input type="text" name="name" value="ACME Corp" required class="...">
    </div>

    <div>
      <label class="block text-sm font-medium text-slate-300 mb-1">Description</label>
      <textarea name="description" rows="2" class="...">Enterprise software solutions...</textarea>
    </div>

    <div>
      <label class="block text-sm font-medium text-slate-300 mb-1">Website</label>
      <input type="url" name="website" value="https://acme.com" class="...">
    </div>

    <div>
      <label class="block text-sm font-medium text-slate-300 mb-1">Service Categories (comma-separated)</label>
      <input type="text" name="services" value="SaaS, Analytics, Cloud" class="...">
    </div>

    <div>
      <label class="block text-sm font-medium text-slate-300 mb-1">Competitors (comma-separated)</label>
      <input type="text" name="competitors" value="Zoom, Slack, Microsoft Teams" class="...">
    </div>

    <!-- Mode + Language dropdowns (same as manual) -->

    <div class="flex items-center gap-3 pt-2">
      <a href="/init" class="px-4 py-2 bg-slate-700 hover:bg-slate-600 text-white text-sm rounded-lg">← Back</a>
      <button type="submit" class="px-5 py-2.5 bg-blue-600 hover:bg-blue-500 text-white font-medium rounded-lg">Create Project</button>
    </div>
  </form>
</div>
```

### Backend Route (`pages.py`)

```python
@router.post("/init/research", response_class=HTMLResponse)
async def init_research(request: Request, domain: str = Form(...)):
    """Auto-detect brand info from domain."""
    try:
        brand_data = await research_brand(domain)
    except Exception as e:
        return HTMLResponse(f'<p class="text-red-500">Research failed: {e}</p>')

    templates = request.app.state.templates
    context = {
        "brand": brand_data,
        "domain": domain,
    }
    return templates.TemplateResponse(request, "init_review.html", context)
```

## Error Handling

| Failure | Behavior |
|---------|----------|
| EXA API fails | Skip EXA, LLM uses own knowledge |
| LLM fails | Show error toast, keep manual form visible |
| EXA + LLM both fail | Show "Research unavailable, please fill manually" |
| Domain doesn't resolve | Low confidence, LLM guesses from domain name |

Always degrade gracefully — never block the user from proceeding manually.

## Testing

- Unit test `autodetect.research_brand()` with mocked EXA responses
- Unit test `autodetect.research_brand()` with no EXA data (LLM-only fallback)
- Integration test: POST `/init/research` returns valid HTML with pre-filled fields
- Manual test: enter known domain (e.g., "stripe.com"), verify correct brand extraction
- Manual test: enter unknown domain, verify low confidence + still works
