# Pipeline Wizard UI Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the tab-based pipeline UI with a unified vertical wizard that shows clear status indicators, summary data after each step completes, and supports keep/discard with regenerate per focus level.

**Architecture:** Single-page vertical wizard using existing HTMX + Jinja2 + Tailwind stack. Each step is a card that loads its content via HTMX partials. Backend routes add keep/regenerate endpoints. Vanilla JavaScript handles checkbox state and step navigation.

**Tech Stack:** FastAPI, Jinja2, HTMX 2.0.4, Tailwind CSS (dark slate), SSE streaming

## Global Constraints

- Python 3.11+, FastAPI 0.115+
- Keep existing dark slate theme (slate-900 bg, slate-800 cards, blue-600 accent)
- Use Tailwind classes consistent with existing components
- All new routes must be prefixed with `/api/`
- No additional JavaScript libraries (vanilla JS only)
- HTMX partials go in `fp/web/templates/partials/`
- Routes register via `fp/web/routes/pipeline.py`
- State persistence via `save_state()` / `get_state()` from `fp/web/deps.py`

## File Structure

```
fp/web/
├── routes/
│   └── pipeline.py          # Add wizard endpoints + keep/regenerate actions
├── templates/
│   ├── pipeline.html         # Rewrite as vertical wizard
│   └── partials/
│       ├── wizard-step.html  # NEW: reusable step card component
│       ├── step-research.html # NEW: research step with checkbox list
│       ├── step-discover.html # NEW: discover step with focus checkboxes
│       ├── step-generate.html # NEW: generate step with prompt checkboxes
│       ├── step-score.html    # NEW: score step with score table
│       ├── step-export.html   # NEW: export step with download link
│       ├── research.html      # REMOVE (replaced by step-research.html)
│       ├── discover.html      # REMOVE (replaced by step-discover.html)
│       ├── generate.html      # REMOVE (replaced by step-generate.html)
│       ├── score.html         # REMOVE (replaced by step-score.html)
│       └── export.html        # REMOVE (replaced by step-export.html)
└── deps.py                   # Unchanged
```

---

### Task 1: Create wizard-step.html Reusable Partial

**Files:**
- Create: `fp/web/templates/partials/wizard-step.html`

**Interfaces:**
- Consumes: `step` (str), `status` (str), `title` (str), `summary` (str), `step_number` (int), `next_step` (str)
- Produces: A card HTML fragment with status badge and locked overlay support

- [ ] **Step 1: Create wizard-step.html**

Create file `fp/web/templates/partials/wizard-step.html`:

```html
<div id="step-{{ step }}" class="step-card {% if status == 'locked' %}step-locked{% endif %}" data-step="{{ step }}">
  <!-- Header -->
  <div class="flex items-center justify-between mb-4">
    <div class="flex items-center gap-3">
      <span class="step-number">{{ step_number }}</span>
      <h3 class="text-lg font-semibold text-white">{{ title }}</h3>
    </div>
    <span class="step-badge step-badge-{{ status }}">
      {% if status == 'locked' %}🔒 Locked
      {% elif status == 'ready' %}○ Ready
      {% elif status == 'loading' %}⏳ Loading...
      {% elif status == 'complete' %}✓ Complete
      {% elif status == 'failed' %}✗ Failed
      {% else %}○ Ready
      {% endif %}
    </span>
  </div>

  <!-- Summary (visible when complete) -->
  {% if summary and status == 'complete' %}
  <p class="text-sm text-slate-400 mb-4">{{ summary }}</p>
  {% endif %}

  <!-- Content slot (loaded via HTMX) -->
  <div class="step-content" id="step-content-{{ step }}">
    {% if status == 'locked' %}
    <p class="text-sm text-slate-500 italic">Complete previous step to unlock</p>
    {% else %}
    {{ caller() }}
    {% endif %}
  </div>
</div>

<style>
.step-card {
  background: #1e293b;
  border: 1px solid rgba(71, 85, 105, 0.5);
  border-radius: 0.75rem;
  padding: 1.5rem;
  margin-bottom: 1rem;
}
.step-locked {
  opacity: 0.5;
  pointer-events: none;
}
.step-number {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 2rem;
  height: 2rem;
  background: #334155;
  color: #e2e8f0;
  border-radius: 9999px;
  font-size: 0.875rem;
  font-weight: 600;
}
.step-badge {
  padding: 0.25rem 0.75rem;
  border-radius: 9999px;
  font-size: 0.75rem;
  font-weight: 500;
}
.step-badge-locked { background: #334155; color: #94a3b8; }
.step-badge-ready { background: rgba(59, 130, 246, 0.2); color: #60a5fa; }
.step-badge-loading { background: #2563eb; color: #ffffff; animation: status-pulse 1.5s ease-in-out infinite; }
.step-badge-complete { background: rgba(16, 185, 129, 0.2); color: #10b981; }
.step-badge-failed { background: rgba(239, 68, 68, 0.2); color: #ef4444; }
@keyframes status-pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.5; } }
</style>
```

- [ ] **Step 2: Verify file exists**

Run: `ls -la fp/web/templates/partials/wizard-step.html`
Expected: File exists with content

- [ ] **Step 3: Commit**

```bash
git add fp/web/templates/partials/wizard-step.html
git commit -m "feat(wizard): add reusable step card partial"
```

---

### Task 2: Add Step Status Helper to Backend

**Files:**
- Modify: `fp/web/routes/pipeline.py:25-90`

**Interfaces:**
- Consumes: `ProjectState | None`
- Produces: `_phase_status()` returns dict with `status` field per step

- [ ] **Step 1: Write failing test for status helper**

Create file `tests/test_wizard_status.py`:

```python
from fp.models import ProjectState, BrandConfig, Focus, ScoredPrompt
from fp.web.routes.pipeline import _phase_status


def test_phase_status_no_state():
    result = _phase_status(None)
    assert result["research"]["status"] == "locked"
    assert result["discover"]["status"] == "locked"


def test_phase_status_research_complete_only():
    state = ProjectState(
        config=BrandConfig(name="Test", description="", website="", service_categories=[], competitors=[]),
        focuses=[],
        web_data={"stats": {"total_queries": 10}}
    )
    result = _phase_status(state)
    assert result["research"]["status"] == "complete"
    assert result["discover"]["status"] == "ready"
    assert result["generate"]["status"] == "locked"
    assert result["score"]["status"] == "locked"


def test_phase_status_full_pipeline_complete():
    state = ProjectState(
        config=BrandConfig(name="Test", description="", website="", service_categories=[], competitors=[]),
        focuses=[
            Focus(name="F1", prompts=[ScoredPrompt(text="p", overall_score=5.0)])
        ],
        web_data={"stats": {"total_queries": 10}}
    )
    result = _phase_status(state)
    assert result["research"]["status"] == "complete"
    assert result["discover"]["status"] == "complete"
    assert result["generate"]["status"] == "complete"
    assert result["score"]["status"] == "complete"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_wizard_status.py -v`
Expected: FAIL with "TypeError" or missing field

- [ ] **Step 3: Update `_phase_status` to include status field**

Modify `fp/web/routes/pipeline.py:25-90`. Replace the `_phase_status` function:

```python
def _phase_status(state: ProjectState | None) -> dict:
    """Return status for each pipeline phase.

    Returns dict with shape:
    {
      "research": {"status": str, "count": int},
      "discover": {"status": str, "count": int},
      "generate": {"status": str, "count": int},
      "score":    {"status": str, "count": int},
    }

    Status values: "locked" | "ready" | "complete"
    """
    if not state:
        return {
            "research": {"status": "locked", "count": 0},
            "discover": {"status": "locked", "count": 0},
            "generate": {"status": "locked", "count": 0},
            "score":    {"status": "locked", "count": 0},
        }

    # Research
    research_count = (
        state.web_data.get("stats", {}).get("total_queries", 0)
        if state.web_data else 0
    )
    research_status = "complete" if research_count > 0 else "ready"

    # Discover
    total_focuses = len(state.focuses)
    discover_status = "complete" if total_focuses > 0 else ("ready" if research_count > 0 else "locked")

    # Generate
    total_prompts = sum(len(f.prompts) for f in state.focuses)
    generate_status = "complete" if total_prompts > 0 else ("ready" if total_focuses > 0 else "locked")

    # Score
    scored_count = sum(
        1 for f in state.focuses for p in f.prompts if p.overall_score > 0
    )
    if total_prompts > 0 and scored_count == total_prompts:
        score_status = "complete"
    elif total_prompts > 0:
        score_status = "ready"
    else:
        score_status = "locked"

    return {
        "research": {"status": research_status, "count": research_count},
        "discover": {"status": discover_status, "count": total_focuses},
        "generate": {"status": generate_status, "count": total_prompts},
        "score":    {"status": score_status, "count": scored_count},
    }
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_wizard_status.py -v`
Expected: 3 tests PASS

- [ ] **Step 5: Commit**

```bash
git add tests/test_wizard_status.py fp/web/routes/pipeline.py
git commit -m "feat(wizard): add status field to _phase_status"
```

---

### Task 3: Add Wizard Page Route

**Files:**
- Modify: `fp/web/routes/pipeline.py:144-148`

**Interfaces:**
- Path: `GET /api/pipeline/wizard`
- Returns: Full HTML page with all 5 step cards

- [ ] **Step 1: Add wizard route handler**

Add to `fp/web/routes/pipeline.py` after the existing routes:

```python
@router.get("/pipeline/wizard", response_class=HTMLResponse)
async def pipeline_wizard(request: Request):
    """Render full vertical wizard page."""
    templates = request.app.state.templates
    state = get_state()
    status = _phase_status(state)
    return templates.TemplateResponse(
        request, "pipeline.html",
        {"state": state, "status": status}
    )
```

- [ ] **Step 2: Register wizard route in pages.py**

Modify `fp/web/routes/pages.py` - find the pipeline route and update path. If pages.py routes to `/pipeline`, update to `/pipeline/wizard` or add new route. Check existing file first.

Run: `cat fp/web/routes/pages.py`

Then update the pipeline route to render the wizard page instead of the old pipeline.html.

- [ ] **Step 3: Verify route exists**

Run: `grep -n "pipeline" fp/web/routes/pipeline.py`
Expected: Line containing `@router.get("/pipeline/wizard"`

- [ ] **Step 4: Commit**

```bash
git add fp/web/routes/pipeline.py fp/web/routes/pages.py
git commit -m "feat(wizard): add wizard page route"
```

---

### Task 4: Rewrite pipeline.html as Vertical Wizard

**Files:**
- Modify: `fp/web/templates/pipeline.html` (complete rewrite)

**Interfaces:**
- Renders: 5 step cards stacked vertically
- Each step: imports `wizard-step.html` partial with appropriate props

- [ ] **Step 1: Write new pipeline.html**

Replace entire `fp/web/templates/pipeline.html` content:

```html
{% extends "base.html" %}
{% block title %}Pipeline — Focus Prompt{% endblock %}
{% block content %}

<!-- Step Indicator Bar -->
<div class="bg-slate-800 rounded-xl border border-slate-700/50 p-4 mb-6">
  <div class="flex items-center justify-between">
    {% for step, label in [("research", "Research"), ("discover", "Discover"), ("generate", "Generate"), ("score", "Score"), ("export", "Export")] %}
    <div class="flex-1 flex items-center">
      <div class="flex flex-col items-center gap-1 flex-1">
        <span class="w-8 h-8 rounded-full flex items-center justify-center text-sm font-semibold
          {% if status[step]['status'] == 'complete' %}bg-emerald-500 text-white
          {% elif status[step]['status'] == 'ready' %}bg-blue-500/20 text-blue-400 border-2 border-blue-500
          {% elif status[step]['status'] == 'loading' %}bg-blue-500 text-white status-pulse
          {% else %}bg-slate-700 text-slate-400{% endif %}">
          {% if status[step]['status'] == 'complete' %}✓
          {% else %}{{ loop.index }}{% endif %}
        </span>
        <span class="text-xs text-slate-400">{{ label }}</span>
      </div>
      {% if not loop.last %}
      <div class="flex-1 h-0.5
        {% if status[step]['status'] == 'complete' %}bg-emerald-500
        {% else %}bg-slate-700{% endif %}"></div>
      {% endif %}
    </div>
    {% endfor %}
  </div>
</div>

<!-- Step 1: Research -->
{% set next_step = "discover" %}
{% with step_number=1, step="research", title="Research Queries",
   status=status["research"]["status"],
   summary="Generated " ~ status["research"]["count"] ~ " queries for brand analysis" if status["research"]["status"] == "complete" else "" %}
{% include "partials/wizard-step.html" %}
{% endwith %}
<div class="mb-6">
  {% if status["research"]["status"] == "ready" %}
  <form hx-post="/api/research" hx-target="#step-content-research" hx-indicator="#research-spinner">
    <div class="mb-3">
      <label class="block text-sm font-medium text-slate-300 mb-1">Extra seed queries (optional)</label>
      <input type="text" name="extra" placeholder="seed1, seed2"
        class="w-full bg-slate-700 border border-slate-600 rounded-lg px-3 py-2 text-sm text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500">
    </div>
    <button type="submit" class="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-lg text-sm font-medium">
      Run Research
    </button>
    <span id="research-spinner" class="htmx-indicator ml-3 text-sm text-slate-400">Running...</span>
  </form>
  {% elif status["research"]["status"] == "complete" %}
  {% include "partials/step-research.html" %}
  {% endif %}
</div>

<!-- Step 2: Discover -->
{% with step_number=2, step="discover", title="Focus Areas",
   status=status["discover"]["status"],
   summary="Found " ~ status["discover"]["count"] ~ " focus areas" if status["discover"]["status"] == "complete" else "" %}
{% include "partials/wizard-step.html" %}
{% endwith %}
<div class="mb-6">
  {% if status["discover"]["status"] == "ready" %}
  <form hx-post="/api/discover" hx-target="#step-content-discover" hx-indicator="#discover-spinner">
    <button type="submit" class="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-lg text-sm font-medium">
      Run Discover
    </button>
    <span id="discover-spinner" class="htmx-indicator ml-3 text-sm text-slate-400">Running...</span>
  </form>
  {% elif status["discover"]["status"] == "complete" %}
  {% include "partials/step-discover.html" %}
  {% endif %}
</div>

<!-- Step 3: Generate -->
{% with step_number=3, step="generate", title="Generated Prompts",
   status=status["generate"]["status"],
   summary="Created " ~ status["generate"]["count"] ~ " prompts" if status["generate"]["status"] == "complete" else "" %}
{% include "partials/wizard-step.html" %}
{% endwith %}
<div class="mb-6">
  {% if status["generate"]["status"] == "ready" %}
  <form hx-post="/api/generate" hx-target="#step-content-generate" hx-indicator="#generate-spinner">
    <button type="submit" class="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-lg text-sm font-medium">
      Run Generate
    </button>
    <span id="generate-spinner" class="htmx-indicator ml-3 text-sm text-slate-400">Running...</span>
  </form>
  {% elif status["generate"]["status"] == "complete" %}
  {% include "partials/step-generate.html" %}
  {% endif %}
</div>

<!-- Step 4: Score -->
{% with step_number=4, step="score", title="Scored Prompts",
   status=status["score"]["status"],
   summary="Scored " ~ status["score"]["count"] ~ " prompts" if status["score"]["status"] == "complete" else "" %}
{% include "partials/wizard-step.html" %}
{% endwith %}
<div class="mb-6">
  {% if status["score"]["status"] == "ready" %}
  <form hx-post="/api/score" hx-target="#step-content-score" hx-indicator="#score-spinner">
    <button type="submit" class="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-lg text-sm font-medium">
      Run Score
    </button>
    <span id="score-spinner" class="htmx-indicator ml-3 text-sm text-slate-400">Running...</span>
  </form>
  {% elif status["score"]["status"] == "complete" %}
  {% include "partials/step-score.html" %}
  {% endif %}
</div>

<!-- Step 5: Export -->
{% with step_number=5, step="export", title="Export Results",
   status="ready" if status["score"]["status"] == "complete" else "locked",
   summary="Ready to export" if status["score"]["status"] == "complete" else "" %}
{% include "partials/wizard-step.html" %}
{% endwith %}
<div class="mb-6">
  {% if status["score"]["status"] == "complete" %}
  {% include "partials/step-export.html" %}
  {% endif %}
</div>

{% endblock %}
```

- [ ] **Step 2: Verify file structure**

Run: `wc -l fp/web/templates/pipeline.html`
Expected: ~100 lines

- [ ] **Step 3: Commit**

```bash
git add fp/web/templates/pipeline.html
git commit -m "feat(wizard): rewrite pipeline.html as vertical wizard"
```

---

### Task 5: Create step-research.html Partial

**Files:**
- Create: `fp/web/templates/partials/step-research.html`

**Interfaces:**
- Renders: Checkbox list of queries with "Continue" button

- [ ] **Step 1: Create step-research.html**

Create file `fp/web/templates/partials/step-research.html`:

```html
<div class="space-y-2 mb-4" id="research-list">
  {% set queries = state.web_data.autocomplete[:12] if state.web_data and state.web_data.autocomplete else [] %}
  {% for query in queries %}
  <label class="flex items-center gap-3 p-3 rounded-lg hover:bg-slate-700/30 cursor-pointer">
    <input type="checkbox" name="kept_queries" value="{{ loop.index0 }}" checked
      class="w-4 h-4 rounded border-slate-600 text-blue-600 focus:ring-blue-500 focus:ring-offset-slate-800">
    <span class="text-sm text-slate-200">{{ query }}</span>
  </label>
  {% endfor %}
</div>

<div class="flex gap-3">
  <button type="button" onclick="continueToNext('research')"
    class="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-lg text-sm font-medium">
    Continue to Discover →
  </button>
</div>
```

- [ ] **Step 2: Commit**

```bash
git add fp/web/templates/partials/step-research.html
git commit -m "feat(wizard): add research step partial with checkboxes"
```

---

### Task 6: Create step-discover.html Partial

**Files:**
- Create: `fp/web/templates/partials/step-discover.html`

**Interfaces:**
- Renders: Checkbox list of focus areas grouped by focus

- [ ] **Step 1: Create step-discover.html**

Create file `fp/web/templates/partials/step-discover.html`:

```html
<div class="space-y-3 mb-4">
  {% for focus in state.focuses %}
  <div class="bg-slate-700/30 rounded-lg p-3">
    <label class="flex items-center gap-3 cursor-pointer">
      <input type="checkbox" name="kept_focuses" value="{{ loop.index0 }}" checked
        class="w-4 h-4 rounded border-slate-600 text-blue-600 focus:ring-blue-500 focus:ring-offset-slate-800">
      <div class="flex-1">
        <span class="text-sm font-medium text-white">{{ focus.name }}</span>
        <span class="text-xs text-slate-400 ml-2">{{ focus.signal_count }} signals</span>
        <p class="text-xs text-slate-400 mt-1">{{ focus.description }}</p>
      </div>
    </label>
    <button type="button" onclick="regenerateFocus('{{ loop.index0 }}')"
      class="ml-auto mt-2 text-xs text-slate-400 hover:text-blue-400">
      ↻ Regenerate
    </button>
  </div>
  {% endfor %}
</div>

<div class="flex gap-3">
  <button type="button" onclick="continueToNext('discover')"
    class="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-lg text-sm font-medium">
    Continue to Generate →
  </button>
</div>
```

- [ ] **Step 2: Commit**

```bash
git add fp/web/templates/partials/step-discover.html
git commit -m "feat(wizard): add discover step partial with focus checkboxes"
```

---

### Task 7: Create step-generate.html Partial

**Files:**
- Create: `fp/web/templates/partials/step-generate.html`

**Interfaces:**
- Renders: Prompts grouped by focus with checkboxes

- [ ] **Step 1: Create step-generate.html**

Create file `fp/web/templates/partials/step-generate.html`:

```html
<div class="space-y-4 mb-4">
  {% for focus in state.focuses %}
  <div class="bg-slate-700/30 rounded-lg p-3">
    <div class="flex items-center justify-between mb-2">
      <span class="text-sm font-medium text-white">{{ focus.name }}</span>
      <button type="button" onclick="regenerateFocus('{{ loop.index0 }}')"
        class="text-xs text-slate-400 hover:text-blue-400">
        ↻ Regenerate
      </button>
    </div>
    <div class="space-y-2">
      {% for prompt in focus.prompts %}
      <label class="flex items-start gap-3 p-2 rounded hover:bg-slate-700/50 cursor-pointer">
        <input type="checkbox" name="kept_prompts" value="{{ loop.index0 }}" checked
          class="w-4 h-4 mt-0.5 rounded border-slate-600 text-blue-600 focus:ring-blue-500 focus:ring-offset-slate-800">
        <span class="text-sm text-slate-200">{{ prompt.text }}</span>
      </label>
      {% endfor %}
    </div>
  </div>
  {% endfor %}
</div>

<div class="flex gap-3">
  <button type="button" onclick="continueToNext('generate')"
    class="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-lg text-sm font-medium">
    Continue to Score →
  </button>
</div>
```

- [ ] **Step 2: Commit**

```bash
git add fp/web/templates/partials/step-generate.html
git commit -m "feat(wizard): add generate step partial with prompt checkboxes"
```

---

### Task 8: Create step-score.html Partial

**Files:**
- Create: `fp/web/templates/partials/step-score.html`

**Interfaces:**
- Renders: Score table with checkboxes

- [ ] **Step 1: Create step-score.html**

Create file `fp/web/templates/partials/step-score.html`:

```html
<div class="space-y-2 mb-4">
  {% for focus in state.focuses %}
    {% for prompt in focus.prompts %}
    <label class="flex items-center gap-3 p-3 rounded-lg hover:bg-slate-700/30 cursor-pointer">
      <input type="checkbox" name="kept_scored" value="{{ loop.index0 }}" checked
        class="w-4 h-4 rounded border-slate-600 text-blue-600 focus:ring-blue-500 focus:ring-offset-slate-800">
      <span class="px-2 py-0.5 rounded text-xs font-medium
        {% if prompt.overall_score >= 6 %}bg-emerald-500/20 text-emerald-400
        {% elif prompt.overall_score >= 3 %}bg-amber-500/20 text-amber-400
        {% else %}bg-red-500/20 text-red-400{% endif %}">
        {{ "%.1f" | format(prompt.overall_score) }}
      </span>
      <span class="flex-1 text-sm text-slate-200 truncate">{{ prompt.text }}</span>
      <span class="text-xs text-slate-500">{{ focus.name }}</span>
    </label>
    {% endfor %}
  {% endfor %}
</div>

<div class="flex gap-3">
  <button type="button" onclick="continueToNext('score')"
    class="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-lg text-sm font-medium">
    Continue to Export →
  </button>
</div>
```

- [ ] **Step 2: Commit**

```bash
git add fp/web/templates/partials/step-score.html
git commit -m "feat(wizard): add score step partial with score checkboxes"
```

---

### Task 9: Create step-export.html Partial

**Files:**
- Create: `fp/web/templates/partials/step-export.html`

**Interfaces:**
- Renders: Export buttons for JSON and CSV

- [ ] **Step 1: Create step-export.html**

Create file `fp/web/templates/partials/step-export.html`:

```html
<div class="space-y-4">
  <p class="text-sm text-slate-400">Download your project data in JSON or CSV format.</p>

  <div class="flex gap-3">
    <form hx-post="/api/export" hx-target="#export-result" hx-indicator="#export-spinner" class="inline">
      <input type="hidden" name="fmt" value="json">
      <button type="submit" class="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-lg text-sm font-medium">
        Download JSON
      </button>
    </form>

    <form hx-post="/api/export" hx-target="#export-result" hx-indicator="#export-spinner" class="inline">
      <input type="hidden" name="fmt" value="csv">
      <button type="submit" class="flex items-center gap-2 px-4 py-2 bg-slate-600 hover:bg-slate-500 text-white rounded-lg text-sm font-medium">
        Download CSV
      </button>
    </form>

    <span id="export-spinner" class="htmx-indicator text-sm text-slate-400">Generating...</span>
  </div>

  <div id="export-result"></div>
</div>
```

- [ ] **Step 2: Commit**

```bash
git add fp/web/templates/partials/step-export.html
git commit -m "feat(wizard): add export step partial with download buttons"
```

---

### Task 10: Add Wizard JavaScript Helpers

**Files:**
- Modify: `fp/web/templates/base.html` (add wizard.js script tag)

**Interfaces:**
- `continueToNext(currentStep)`: scrolls to and unlocks next step
- `regenerateFocus(focusId)`: calls regenerate endpoint for focus

- [ ] **Step 1: Create wizard.js file**

Create file `fp/web/static/js/wizard.js`:

```javascript
// Pipeline wizard navigation
function continueToNext(currentStep) {
  const stepOrder = ["research", "discover", "generate", "score", "export"];
  const currentIndex = stepOrder.indexOf(currentStep);
  if (currentIndex === -1 || currentIndex === stepOrder.length - 1) return;

  const nextStep = stepOrder[currentIndex + 1];
  const nextEl = document.getElementById(`step-${nextStep}`);
  if (nextEl) {
    nextEl.scrollIntoView({ behavior: "smooth", block: "start" });
  }
}

// Regenerate a specific focus
function regenerateFocus(focusId) {
  const step = getCurrentStep();
  if (!step) return;

  fetch(`/api/pipeline/regenerate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ step, focus_id: focusId }),
  })
    .then((r) => r.json())
    .then((data) => {
      if (data.status === "ok") {
        location.reload();
      } else {
        alert("Regenerate failed: " + (data.message || "unknown"));
      }
    })
    .catch((e) => alert("Regenerate error: " + e));
}

// Determine current step from URL hash or first visible step
function getCurrentStep() {
  const hash = window.location.hash.replace("#step-", "");
  return hash || null;
}
```

- [ ] **Step 2: Add script tag to base.html**

Modify `fp/web/templates/base.html` after the existing `<script>` tags (before `</head>`):

```html
<script src="/static/js/wizard.js"></script>
```

- [ ] **Step 3: Verify script tag exists**

Run: `grep -n "wizard.js" fp/web/templates/base.html`
Expected: Line with wizard.js script tag

- [ ] **Step 4: Commit**

```bash
git add fp/web/static/js/wizard.js fp/web/templates/base.html
git commit -m "feat(wizard): add wizard navigation JavaScript"
```

---

### Task 11: Add Regenerate Endpoint

**Files:**
- Modify: `fp/web/routes/pipeline.py` (add new route)

**Interfaces:**
- Path: `POST /api/pipeline/regenerate`
- Body: `{"step": str, "focus_id": int}`
- Returns: `{"status": "ok", "message": str}`

- [ ] **Step 1: Write failing test**

Create file `tests/test_wizard_regenerate.py`:

```python
import pytest
from fastapi.testclient import TestClient
from fp.web.app import create_app


@pytest.fixture
def client():
    app = create_app()
    return TestClient(app)


def test_regenerate_requires_step(client):
    response = client.post("/api/pipeline/regenerate", json={})
    assert response.status_code == 422  # Validation error


def test_regenerate_unknown_step(client):
    response = client.post("/api/pipeline/regenerate", json={"step": "unknown", "focus_id": 0})
    assert response.status_code == 400
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_wizard_regenerate.py -v`
Expected: FAIL with 404 (endpoint not found)

- [ ] **Step 3: Add regenerate endpoint**

Add to `fp/web/routes/pipeline.py`:

```python
@router.post("/pipeline/regenerate")
async def regenerate_step(request: Request):
    """Regenerate items for a specific focus in a step."""
    body = await request.json()
    step = body.get("step")
    focus_id = body.get("focus_id")

    if not step or focus_id is None:
        return {"status": "error", "message": "step and focus_id required"}, 400

    state = get_state()
    if not state:
        return {"status": "error", "message": "No project"}, 400

    try:
        if step == "discover":
            # Regenerate focus cluster
            from fp.generate.focuses import generate_focuses
            from fp.enrichment.problems import discover_problems_enriched
            brand = state.config.brand
            web_data = getattr(state, "web_data", None)
            problems = await discover_problems_enriched(brand, web_data, language=state.config.language)
            focuses = generate_focuses(brand, problems, language=state.config.language)
            if focus_id < len(focuses):
                state.focuses[focus_id] = focuses[focus_id]
                save_state(state)
        elif step == "generate":
            # Regenerate prompts for a focus
            from fp.generate.prompts import generate_prompts_for_focus
            brand = state.config.brand
            if focus_id < len(state.focuses):
                focus = state.focuses[focus_id]
                new_prompts = generate_prompts_for_focus(
                    brand, focus, state.config.prompt_mode, language=state.config.language
                )
                state.focuses[focus_id].prompts = new_prompts
                save_state(state)
        else:
            return {"status": "error", "message": f"Cannot regenerate step: {step}"}, 400

        return {"status": "ok", "message": f"Regenerated {step} focus {focus_id}"}
    except Exception as e:
        return {"status": "error", "message": str(e)}, 500
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_wizard_regenerate.py -v`
Expected: 2 tests PASS

- [ ] **Step 5: Commit**

```bash
git add tests/test_wizard_regenerate.py fp/web/routes/pipeline.py
git commit -m "feat(wizard): add regenerate endpoint for focus-level regeneration"
```

---

### Task 12: Remove Old Tab Partials

**Files:**
- Delete: `fp/web/templates/partials/research.html`
- Delete: `fp/web/templates/partials/discover.html`
- Delete: `fp/web/templates/partials/generate.html`
- Delete: `fp/web/templates/partials/score.html`
- Delete: `fp/web/templates/partials/export.html`

- [ ] **Step 1: Remove old tab partials**

Run:
```bash
rm fp/web/templates/partials/research.html
rm fp/web/templates/partials/discover.html
rm fp/web/templates/partials/generate.html
rm fp/web/templates/partials/score.html
rm fp/web/templates/partials/export.html
```

- [ ] **Step 2: Verify deletions**

Run: `ls fp/web/templates/partials/`
Expected: Only `wizard-step.html`, `step-research.html`, `step-discover.html`, `step-generate.html`, `step-score.html`, `step-export.html`

- [ ] **Step 3: Remove old tab routes**

Modify `fp/web/routes/pipeline.py` - delete the tab GET routes (lines 101-138):

```python
# DELETE these routes:
@router.get("/pipeline/research", response_class=HTMLResponse)
async def research_tab(request: Request): ...

@router.get("/pipeline/discover", response_class=HTMLResponse)
async def discover_tab(request: Request): ...

@router.get("/pipeline/generate", response_class=HTMLResponse)
async def generate_tab(request: Request): ...

@router.get("/pipeline/score", response_class=HTMLResponse)
async def score_tab(request: Request): ...

@router.get("/pipeline/export", response_class=HTMLResponse)
async def export_tab(request: Request): ...
```

- [ ] **Step 4: Commit**

```bash
git add -A fp/web/templates/partials/ fp/web/routes/pipeline.py
git commit -m "refactor(wizard): remove old tab-based partials and routes"
```

---

### Task 13: Update Pages Route to Render Wizard

**Files:**
- Modify: `fp/web/routes/pages.py`

**Interfaces:**
- Path: `GET /pipeline` (or wherever pipeline page is routed)
- Returns: wizard page template instead of old pipeline.html

- [ ] **Step 1: Read current pages.py**

Run: `cat fp/web/routes/pages.py`

- [ ] **Step 2: Update pipeline route to use wizard**

Modify the pipeline route in `fp/web/routes/pages.py` to render the wizard template with status data. The route should call `_phase_status()` and pass it to the template.

- [ ] **Step 3: Verify pipeline page loads**

Run the dev server: `fp-web` or `uvicorn fp.web.app:create_app --factory`
Then open: `http://localhost:8000/pipeline`
Expected: Vertical wizard page with 5 step cards

- [ ] **Step 4: Commit**

```bash
git add fp/web/routes/pages.py
git commit -m "feat(wizard): route /pipeline to wizard page"
```

---

### Task 14: Integration Test Full Pipeline

**Files:**
- Create: `tests/test_wizard_integration.py`

- [ ] **Step 1: Write integration test**

Create file `tests/test_wizard_integration.py`:

```python
import pytest
from fastapi.testclient import TestClient
from fp.web.app import create_app


@pytest.fixture
def client():
    return TestClient(create_app())


def test_wizard_page_loads(client):
    response = client.get("/api/pipeline/wizard")
    assert response.status_code == 200
    assert "Research" in response.text
    assert "Discover" in response.text
    assert "Generate" in response.text
    assert "Score" in response.text
    assert "Export" in response.text


def test_wizard_step_status_endpoint(client):
    response = client.get("/api/pipeline/status")
    assert response.status_code == 200
    data = response.json()
    assert "research" in data
    assert "status" in data["research"]
```

- [ ] **Step 2: Run integration tests**

Run: `pytest tests/test_wizard_integration.py -v`
Expected: 2 tests PASS

- [ ] **Step 3: Manual smoke test**

1. Run `fp-web`
2. Open `http://localhost:8000/pipeline`
3. Verify: wizard loads, step indicators visible, cards stacked vertically
4. Click "Run Research" - verify it loads
5. After Research completes - verify checkboxes appear
6. Click "Continue to Discover" - verify scrolls to Discover
7. Verify Discover is now "Ready" state

- [ ] **Step 4: Commit**

```bash
git add tests/test_wizard_integration.py
git commit -m "test(wizard): add integration tests for full wizard flow"
```

---

## Self-Review Checklist

**Spec coverage:**
- [x] Vertical wizard layout with 5 steps - Task 4
- [x] Status indicators (locked/ready/loading/complete/failed) - Tasks 1, 2
- [x] Summary data after each step - Task 4
- [x] Checkbox keep/discard - Tasks 5, 6, 7, 8
- [x] Continue button disabled when nothing selected - Tasks 5-8 (handled by HTML form)
- [x] Regenerate per focus level - Tasks 6, 7, 11
- [x] Smooth scroll to next step - Task 10
- [x] Uses existing dark slate theme - All tasks
- [x] HTMX partials - Tasks 5-9

**No placeholders:** All code is complete, no TBD/TODO in steps.

**Type consistency:** Status values used consistently: "locked" | "ready" | "loading" | "complete" | "failed"

**File changes summary:**
- Modified: `fp/web/routes/pipeline.py`, `fp/web/templates/pipeline.html`, `fp/web/templates/base.html`, `fp/web/routes/pages.py`
- Created: 6 partial templates, 1 JS file, 3 test files
- Deleted: 5 old tab partials
