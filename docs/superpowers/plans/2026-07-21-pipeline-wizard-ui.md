# Pipeline Wizard UI Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Redesign the pipeline page from a tab-based interface to a unified vertical wizard flow with keep/discard/regenerate functionality.

**Architecture:** Server-side rendering with FastAPI + Jinja2 + HTMX. Each step becomes a vertical card. Status indicators use Tailwind CSS classes from existing design system. Keep/discard via checkbox + JS state management.

**Tech Stack:** Python 3.11+, FastAPI, Jinja2, HTMX 2.0, Tailwind CSS (via CDN), Vanilla JavaScript

## Global Constraints

- Dark slate theme (slate-900 base, slate-800 cards, slate-700 inputs) - do not change
- Use existing Tailwind classes from DESIGN.md color tokens
- All routes prefixed with `/api` (as per app.py:30)
- Templates in `fp/web/templates/`, partials in `fp/web/templates/partials/`
- HTMX partials return HTML, not JSON
- Keep dependencies minimal - no new libraries

---

## File Structure

**Modified Files:**
- `fp/web/templates/pipeline.html` - Complete rewrite to wizard layout
- `fp/web/templates/partials/research.html` - Enhanced with step card structure
- `fp/web/templates/partials/discover.html` - Enhanced with step card structure
- `fp/web/templates/partials/generate.html` - Enhanced with step card structure
- `fp/web/templates/partials/score.html` - Enhanced with step card structure
- `fp/web/templates/partials/export.html` - Enhanced with step card structure
- `fp/web/routes/pipeline.py` - Add keep/discard/regenerate endpoints

**New Files:**
- `fp/web/templates/partials/wizard-step.html` - Reusable step component template
- `fp/web/templates/partials/step-items.html` - Checkbox list component
- `fp/web/static/js/wizard.js` - Checkbox state management + scroll navigation

---

## Task 1: Create wizard-step.html partial template

**Files:**
- Create: `fp/web/templates/partials/wizard-step.html`

**Interfaces:**
- Consumes: `step_name` (str), `status` (str: locked/ready/loading/complete/failed), `summary` (str), `items` (list), `show_checkboxes` (bool)
- Produces: HTML for a step card with status badge, summary, and optional checkbox list

- [ ] **Step 1: Create the wizard-step.html template**

```html
<!-- Reusable step card component -->
<!-- Expects: step_name, status (locked|ready|loading|complete|failed), summary, items (list), show_checkboxes (bool), step_id -->
<div id="step-{{ step_id }}" class="bg-slate-800 rounded-xl border border-slate-700/50 p-6 mb-4" data-step="{{ step_id }}" data-status="{{ status }}">
    <!-- Header -->
    <div class="flex items-center justify-between mb-4">
        <h3 class="text-lg font-semibold text-white">{{ step_name }}</h3>
        <span class="step-badge
            {% if status == 'complete' %}bg-emerald-500/20 text-emerald-400
            {% elif status == 'loading' %}bg-blue-500 text-white status-pulse
            {% elif status == 'failed' %}bg-red-500/20 text-red-400
            {% elif status == 'ready' %}bg-blue-500/20 text-blue-400
            {% else %}bg-slate-700 text-slate-400{% endif %}
            px-3 py-1 rounded-full text-xs font-medium">
            {% if status == 'locked' %}🔒 Locked
            {% elif status == 'ready' %}○ Ready
            {% elif status == 'loading' %}⏳ Loading...
            {% elif status == 'complete' %}✓ Complete
            {% elif status == 'failed' %}✗ Failed{% endif %}
        </span>
    </div>

    <!-- Summary -->
    {% if summary %}
    <p class="text-sm text-slate-400 mb-4">{{ summary }}</p>
    {% endif %}

    <!-- Item List (when complete) -->
    {% if show_checkboxes and items %}
    <div class="space-y-2 mb-4">
        {% for item in items %}
        <label class="flex items-center gap-3 p-3 rounded-lg hover:bg-slate-700/30 transition-colors cursor-pointer">
            <input type="checkbox" 
                   class="step-item-checkbox rounded border-slate-600 bg-slate-700 text-blue-600 focus:ring-blue-500" 
                   data-item-id="{{ item.id }}" 
                   {% if item.checked %}checked{% endif %}>
            <span class="text-slate-200 text-sm">{{ item.text }}</span>
            {% if item.meta %}<span class="text-slate-500 text-xs ml-auto">{{ item.meta }}</span>{% endif %}
        </label>
        {% endfor %}
    </div>
    {% endif %}

    <!-- Actions Slot -->
    <div class="step-actions flex gap-3 mt-4">
        {{ actions|safe }}
    </div>
</div>
```

- [ ] **Step 2: Verify template file created**

Run: `ls -la fp/web/templates/partials/wizard-step.html`
Expected: File exists with no errors

- [ ] **Step 3: Commit**

```bash
git add fp/web/templates/partials/wizard-step.html
git commit -m "feat(pipeline): add reusable wizard step partial template"
```

---

## Task 2: Create step-items.html partial for checkbox list

**Files:**
- Create: `fp/web/templates/partials/step-items.html`

**Interfaces:**
- Consumes: `items` (list of dicts with id, text, meta, checked)
- Produces: HTML with checkboxes for keep/discard UI

- [ ] **Step 1: Create step-items.html partial**

```html
<!-- Checkbox list for keep/discard -->
<!-- Expects: items (list), step_id (str) -->
<div class="step-items space-y-2">
    {% for item in items %}
    <label class="flex items-center gap-3 p-3 rounded-lg hover:bg-slate-700/30 transition-colors cursor-pointer border border-transparent hover:border-slate-700/50">
        <input type="checkbox" 
               class="step-item-checkbox rounded border-slate-600 bg-slate-700 text-blue-600 focus:ring-blue-500 focus:ring-offset-0" 
               value="{{ item.id }}"
               data-item-id="{{ item.id }}"
               data-step="{{ step_id }}"
               {% if item.get('checked', True) %}checked{% endif %}>
        <span class="text-slate-200 text-sm flex-1">{{ item.text }}</span>
        {% if item.get('meta') %}
        <span class="text-slate-500 text-xs">{{ item.meta }}</span>
        {% endif %}
    </label>
    {% endfor %}
</div>
```

- [ ] **Step 2: Verify file created**

Run: `ls -la fp/web/templates/partials/step-items.html`
Expected: File exists

- [ ] **Step 3: Commit**

```bash
git add fp/web/templates/partials/step-items.html
git commit -m "feat(pipeline): add checkbox list partial for keep/discard"
```

---

## Task 3: Create wizard.js for client-side interactions

**Files:**
- Create: `fp/web/static/js/wizard.js`

**Interfaces:**
- Consumes: DOM events from checkbox changes, Continue buttons
- Produces: Updated Continue button state, scroll-to-next-step behavior, fetch() calls to keep/regenerate endpoints

- [ ] **Step 1: Create static/js directory and wizard.js**

First create the directory:
```bash
mkdir -p fp/web/static/js
```

Then create `fp/web/static/js/wizard.js`:

```javascript
// Wizard state management
const Wizard = {
    updateContinueButton(stepId) {
        const step = document.getElementById(`step-${stepId}`);
        if (!step) return;
        const checkboxes = step.querySelectorAll('.step-item-checkbox');
        const checked = step.querySelectorAll('.step-item-checkbox:checked').length;
        const continueBtn = step.querySelector('.continue-btn');
        if (continueBtn) {
            continueBtn.disabled = checked === 0;
            continueBtn.classList.toggle('opacity-50', checked === 0);
            continueBtn.classList.toggle('cursor-not-allowed', checked === 0);
        }
    },

    initStep(stepId) {
        const step = document.getElementById(`step-${stepId}`);
        if (!step) return;
        const checkboxes = step.querySelectorAll('.step-item-checkbox');
        checkboxes.forEach(cb => {
            cb.addEventListener('change', () => this.updateContinueButton(stepId));
        });
        this.updateContinueButton(stepId);
    },

    async saveKeep(stepId, itemIds) {
        try {
            const response = await fetch(`/api/pipeline/step/${stepId}/keep`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ keep_ids: itemIds })
            });
            return response.ok;
        } catch (e) {
            console.error('Failed to save keep:', e);
            return false;
        }
    },

    async regenerate(stepId, itemIds) {
        try {
            const response = await fetch(`/api/pipeline/step/${stepId}/regenerate`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ regenerate_ids: itemIds })
            });
            if (response.ok) {
                location.reload(); // Reload to show new data
            }
        } catch (e) {
            console.error('Failed to regenerate:', e);
        }
    },

    continueToNext(currentStepId) {
        // Save keep state
        const step = document.getElementById(`step-${currentStepId}`);
        if (!step) return;
        const checkedIds = Array.from(step.querySelectorAll('.step-item-checkbox:checked'))
            .map(cb => cb.dataset.itemId);
        
        this.saveKeep(currentStepId, checkedIds).then(success => {
            if (success) {
                const nextStepId = this.getNextStep(currentStepId);
                if (nextStepId) {
                    const nextStep = document.getElementById(`step-${nextStepId}`);
                    if (nextStep) {
                        nextStep.scrollIntoView({ behavior: 'smooth', block: 'start' });
                    }
                }
            }
        });
    },

    getNextStep(currentStepId) {
        const order = ['research', 'discover', 'generate', 'score', 'export'];
        const idx = order.indexOf(currentStepId);
        return idx >= 0 && idx < order.length - 1 ? order[idx + 1] : null;
    }
};

// Initialize all steps on page load
document.addEventListener('DOMContentLoaded', () => {
    ['research', 'discover', 'generate', 'score', 'export'].forEach(stepId => {
        Wizard.initStep(stepId);
    });
});

// Expose to global scope for onclick handlers
window.Wizard = Wizard;
```

- [ ] **Step 2: Verify file created**

Run: `ls -la fp/web/static/js/wizard.js`
Expected: File exists

- [ ] **Step 3: Commit**

```bash
git add fp/web/static/js/wizard.js
git commit -m "feat(pipeline): add wizard.js for checkbox state and navigation"
```

---

## Task 4: Add keep endpoint to pipeline.py

**Files:**
- Modify: `fp/web/routes/pipeline.py` (add new endpoint after line 175)

**Interfaces:**
- Consumes: `step` (path param), `keep_ids` (JSON body, list of int)
- Produces: `{"status": "ok", "kept": int, "discarded": int}` JSON response

- [ ] **Step 1: Write the keep endpoint**

Add this code at the end of `fp/web/routes/pipeline.py` (after the existing routes, before the action routes OR at the very end):

```python
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
            kept = [q for q in all_queries if str(q.get("id", "")) in keep_ids or q.get("text", "") in keep_ids]
            discarded = len(all_queries) - len(kept)
            state.web_data["queries"] = kept
            state.web_data["stats"]["total_queries"] = len(kept)
            save_state(state)
            return {"status": "ok", "kept": len(kept), "discarded": discarded}

    elif step == "discover":
        # Keep only selected focuses
        all_focuses = state.focuses
        kept = [f for f in all_focuses if str(f.name) in keep_ids]
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
```

- [ ] **Step 2: Verify endpoint added**

Run: `grep -n "keep_items" fp/web/routes/pipeline.py`
Expected: Shows the function definition

- [ ] **Step 3: Commit**

```bash
git add fp/web/routes/pipeline.py
git commit -m "feat(pipeline): add keep endpoint for wizard keep/discard"
```

---

## Task 5: Add regenerate endpoint to pipeline.py

**Files:**
- Modify: `fp/web/routes/pipeline.py` (add after keep endpoint)

**Interfaces:**
- Consumes: `step` (path param), `regenerate_ids` (JSON body, list)
- Produces: `{"status": "ok", "regenerating": int}` JSON response

- [ ] **Step 1: Write the regenerate endpoint**

Add this after the keep_items endpoint:

```python
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
```

- [ ] **Step 2: Verify endpoint added**

Run: `grep -n "regenerate_items" fp/web/routes/pipeline.py`
Expected: Shows the function definition

- [ ] **Step 3: Commit**

```bash
git add fp/web/routes/pipeline.py
git commit -m "feat(pipeline): add regenerate endpoint for wizard"
```

---

## Task 6: Rewrite pipeline.html with wizard layout

**Files:**
- Modify: `fp/web/templates/pipeline.html` (complete rewrite)

**Interfaces:**
- Consumes: ProjectState from backend
- Produces: Vertical wizard page with 5 step cards, status indicators, and Continue buttons

- [ ] **Step 1: Write new pipeline.html with wizard layout**

Replace the entire content of `fp/web/templates/pipeline.html` with:

```html
{% extends "base.html" %}
{% block title %}Pipeline — Focus Prompt{% endblock %}
{% block content %}
<div class="space-y-6">
    <!-- Header -->
    <h1 class="text-2xl font-bold text-white">Pipeline</h1>
    <p class="text-slate-400 text-sm">Run the research pipeline to discover and generate prompts for your brand.</p>

    <!-- Step Indicator Bar -->
    <div class="bg-slate-800 rounded-xl border border-slate-700/50 p-4 overflow-x-auto">
        <div class="flex items-center justify-between min-w-max">
            {% set steps = [
                ('research', 'Research'),
                ('discover', 'Discover'),
                ('generate', 'Generate'),
                ('score', 'Score'),
                ('export', 'Export')
            ] %}
            {% for step_id, step_name in steps %}
            <div class="flex items-center">
                <div class="flex flex-col items-center">
                    <div class="step-indicator 
                        {% if step_statuses.get(step_id, 'locked') == 'complete' %}bg-emerald-500 text-white
                        {% elif step_statuses.get(step_id, 'locked') == 'loading' %}bg-blue-500 text-white status-pulse
                        {% elif step_statuses.get(step_id, 'locked') == 'failed' %}bg-red-500 text-white
                        {% elif step_statuses.get(step_id, 'locked') == 'ready' %}bg-blue-500/30 text-blue-400 border-2 border-blue-500
                        {% else %}bg-slate-700 text-slate-400{% endif %}
                        w-10 h-10 rounded-full flex items-center justify-center text-sm font-semibold">
                        {% if step_statuses.get(step_id, 'locked') == 'complete' %}✓
                        {% elif step_statuses.get(step_id, 'locked') == 'loading' %}⏳
                        {% elif step_statuses.get(step_id, 'locked') == 'failed' %}✗
                        {% elif step_statuses.get(step_id, 'locked') == 'ready' %}{{ loop.index }}
                        {% else %}🔒{% endif %}
                    </div>
                    <span class="text-xs text-slate-400 mt-1">{{ step_name }}</span>
                </div>
                {% if not loop.last %}
                <div class="w-12 h-0.5 mx-2 
                    {% if step_statuses.get(step_id, 'locked') == 'complete' %}bg-emerald-500
                    {% else %}bg-slate-700{% endif %}"></div>
                {% endif %}
            </div>
            {% endfor %}
        </div>
    </div>

    <!-- Step 1: Research -->
    {% include "partials/wizard-step.html" with context %}
    <!-- We'll set context vars per step. Use individual partials below for now -->

    <!-- Step 1: Research -->
    <div id="step-research" class="bg-slate-800 rounded-xl border border-slate-700/50 p-6 mb-4" data-step="research" data-status="{{ step_statuses.get('research', 'locked') }}">
        <div class="flex items-center justify-between mb-4">
            <h3 class="text-lg font-semibold text-white">1. Research Queries</h3>
            <span class="px-3 py-1 rounded-full text-xs font-medium
                {% if step_statuses.get('research') == 'complete' %}bg-emerald-500/20 text-emerald-400
                {% elif step_statuses.get('research') == 'loading' %}bg-blue-500 text-white status-pulse
                {% elif step_statuses.get('research') == 'failed' %}bg-red-500/20 text-red-400
                {% elif step_statuses.get('research') == 'ready' %}bg-blue-500/20 text-blue-400
                {% else %}bg-slate-700 text-slate-400{% endif %}">
                {% if step_statuses.get('research') == 'complete' %}✓ Complete
                {% elif step_statuses.get('research') == 'loading' %}⏳ Loading...
                {% elif step_statuses.get('research') == 'failed' %}✗ Failed
                {% elif step_statuses.get('research') == 'ready' %}○ Ready
                {% else %}🔒 Locked{% endif %}
            </span>
        </div>
        {% if state and state.web_data and state.web_data.get('stats', {}).get('total_queries', 0) > 0 %}
        <p class="text-sm text-slate-400 mb-4">Generated {{ state.web_data['stats']['total_queries'] }} queries for brand analysis.</p>
        <div class="space-y-2 mb-4">
            {% for query in state.web_data.get('autocomplete', [])[:10] %}
            <label class="flex items-center gap-3 p-3 rounded-lg hover:bg-slate-700/30 transition-colors cursor-pointer border border-transparent hover:border-slate-700/50">
                <input type="checkbox" class="step-item-checkbox rounded border-slate-600 bg-slate-700 text-blue-600 focus:ring-blue-500" 
                       value="{{ loop.index }}" data-item-id="{{ loop.index }}" data-step="research" checked>
                <span class="text-slate-200 text-sm flex-1">{{ query }}</span>
            </label>
            {% endfor %}
        </div>
        {% else %}
        <p class="text-sm text-slate-400 mb-4">Fetch real user queries from Google Autocomplete to start.</p>
        <form hx-post="/api/research" hx-target="#research-result" hx-indicator="#research-spinner" hx-trigger="submit">
            <div class="mb-3">
                <label class="block text-sm font-medium text-slate-300 mb-1">Extra seed queries (optional)</label>
                <input type="text" name="extra" placeholder="seed1, seed2" class="w-full bg-slate-700 border border-slate-600 rounded-lg px-3 py-2 text-sm text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500">
            </div>
            <div class="flex items-center gap-3">
                <button type="submit" class="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-lg text-sm font-medium transition-colors">
                    🔍 Run Research
                </button>
                <span id="research-spinner" class="htmx-indicator text-sm text-slate-400">Running...</span>
            </div>
        </form>
        <div id="research-result"></div>
        {% endif %}
        <div class="step-actions flex gap-3 mt-4">
            {% if state and state.web_data and state.web_data.get('stats', {}).get('total_queries', 0) > 0 %}
            <button onclick="Wizard.regenerate('research', [])" class="flex items-center gap-2 px-4 py-2 bg-slate-600 hover:bg-slate-500 text-white rounded-lg text-sm font-medium transition-colors">
                🔄 Regenerate
            </button>
            <button onclick="Wizard.continueToNext('research')" class="continue-btn flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-lg text-sm font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed">
                Continue to Discover →
            </button>
            {% endif %}
        </div>
    </div>

    <!-- Step 2: Discover -->
    <div id="step-discover" class="bg-slate-800 rounded-xl border border-slate-700/50 p-6 mb-4" data-step="discover" data-status="{{ step_statuses.get('discover', 'locked') }}">
        <div class="flex items-center justify-between mb-4">
            <h3 class="text-lg font-semibold text-white">2. Discover Focus Areas</h3>
            <span class="px-3 py-1 rounded-full text-xs font-medium
                {% if step_statuses.get('discover') == 'complete' %}bg-emerald-500/20 text-emerald-400
                {% elif step_statuses.get('discover') == 'loading' %}bg-blue-500 text-white status-pulse
                {% elif step_statuses.get('discover') == 'failed' %}bg-red-500/20 text-red-400
                {% elif step_statuses.get('discover') == 'ready' %}bg-blue-500/20 text-blue-400
                {% else %}bg-slate-700 text-slate-400{% endif %}">
                {% if step_statuses.get('discover') == 'complete' %}✓ Complete
                {% elif step_statuses.get('discover') == 'loading' %}⏳ Loading...
                {% elif step_statuses.get('discover') == 'failed' %}✗ Failed
                {% elif step_statuses.get('discover') == 'ready' %}○ Ready
                {% else %}🔒 Locked{% endif %}
            </span>
        </div>
        {% if state and state.focuses %}
        <p class="text-sm text-slate-400 mb-4">Found {{ state.focuses|length }} focus areas for your brand.</p>
        <div class="space-y-2 mb-4">
            {% for focus in state.focuses %}
            <label class="flex items-center gap-3 p-3 rounded-lg hover:bg-slate-700/30 transition-colors cursor-pointer border border-transparent hover:border-slate-700/50">
                <input type="checkbox" class="step-item-checkbox rounded border-slate-600 bg-slate-700 text-blue-600 focus:ring-blue-500" 
                       value="{{ focus.name }}" data-item-id="{{ focus.name }}" data-step="discover" checked>
                <span class="text-slate-200 text-sm flex-1">{{ focus.name }}</span>
                <span class="text-slate-500 text-xs">{{ focus.signal_count or 0 }} signals</span>
            </label>
            {% endfor %}
        </div>
        {% elif state and state.web_data %}
        <p class="text-sm text-slate-400 mb-4">Discover focus areas from your research data.</p>
        <form hx-post="/api/discover" hx-target="#discover-result" hx-indicator="#discover-spinner" hx-trigger="submit">
            <div class="flex items-center gap-3">
                <button type="submit" class="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-lg text-sm font-medium transition-colors">
                    💡 Run Discovery
                </button>
                <span id="discover-spinner" class="htmx-indicator text-sm text-slate-400">Running...</span>
            </div>
        </form>
        <div id="discover-result"></div>
        {% else %}
        <p class="text-sm text-slate-500 italic">Complete the Research step first.</p>
        {% endif %}
        <div class="step-actions flex gap-3 mt-4">
            {% if state and state.focuses %}
            <button onclick="Wizard.regenerate('discover', [])" class="flex items-center gap-2 px-4 py-2 bg-slate-600 hover:bg-slate-500 text-white rounded-lg text-sm font-medium transition-colors">
                🔄 Regenerate
            </button>
            <button onclick="Wizard.continueToNext('discover')" class="continue-btn flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-lg text-sm font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed">
                Continue to Generate →
            </button>
            {% endif %}
        </div>
    </div>

    <!-- Step 3: Generate -->
    <div id="step-generate" class="bg-slate-800 rounded-xl border border-slate-700/50 p-6 mb-4" data-step="generate" data-status="{{ step_statuses.get('generate', 'locked') }}">
        <div class="flex items-center justify-between mb-4">
            <h3 class="text-lg font-semibold text-white">3. Generate Prompts</h3>
            <span class="px-3 py-1 rounded-full text-xs font-medium
                {% if step_statuses.get('generate') == 'complete' %}bg-emerald-500/20 text-emerald-400
                {% elif step_statuses.get('generate') == 'loading' %}bg-blue-500 text-white status-pulse
                {% elif step_statuses.get('generate') == 'failed' %}bg-red-500/20 text-red-400
                {% elif step_statuses.get('generate') == 'ready' %}bg-blue-500/20 text-blue-400
                {% else %}bg-slate-700 text-slate-400{% endif %}">
                {% if step_statuses.get('generate') == 'complete' %}✓ Complete
                {% elif step_statuses.get('generate') == 'loading' %}⏳ Loading...
                {% elif step_statuses.get('generate') == 'failed' %}✗ Failed
                {% elif step_statuses.get('generate') == 'ready' %}○ Ready
                {% else %}🔒 Locked{% endif %}
            </span>
        </div>
        {% set total_prompts = state.focuses|map(attribute='prompts')|map('length')|sum if state and state.focuses else 0 %}
        {% if total_prompts > 0 %}
        <p class="text-sm text-slate-400 mb-4">Generated {{ total_prompts }} prompts across {{ state.focuses|length }} focus areas.</p>
        <div class="space-y-4 mb-4">
            {% for focus in state.focuses %}
            {% if focus.prompts %}
            <div>
                <h4 class="text-sm font-medium text-slate-300 mb-2">{{ focus.name }}</h4>
                <div class="space-y-2">
                    {% for prompt in focus.prompts[:5] %}
                    <label class="flex items-center gap-3 p-3 rounded-lg hover:bg-slate-700/30 transition-colors cursor-pointer border border-transparent hover:border-slate-700/50">
                        <input type="checkbox" class="step-item-checkbox rounded border-slate-600 bg-slate-700 text-blue-600 focus:ring-blue-500" 
                               value="{{ focus.name }}-{{ prompt.text[:30] }}" data-item-id="{{ focus.name }}-{{ prompt.text[:30] }}" data-step="generate" checked>
                        <span class="text-slate-200 text-sm flex-1">{{ prompt.text }}</span>
                    </label>
                    {% endfor %}
                </div>
            </div>
            {% endif %}
            {% endfor %}
        </div>
        {% elif state and state.focuses %}
        <p class="text-sm text-slate-400 mb-4">Generate prompt variants for each focus area.</p>
        <form hx-post="/api/generate" hx-target="#generate-result" hx-indicator="#generate-spinner" hx-trigger="submit">
            <div class="flex items-center gap-3">
                <button type="submit" class="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-lg text-sm font-medium transition-colors">
                    ✨ Generate Prompts
                </button>
                <span id="generate-spinner" class="htmx-indicator text-sm text-slate-400">Running...</span>
            </div>
        </form>
        <div id="generate-result"></div>
        {% else %}
        <p class="text-sm text-slate-500 italic">Complete the Discover step first.</p>
        {% endif %}
        <div class="step-actions flex gap-3 mt-4">
            {% if total_prompts > 0 %}
            <button onclick="Wizard.regenerate('generate', [])" class="flex items-center gap-2 px-4 py-2 bg-slate-600 hover:bg-slate-500 text-white rounded-lg text-sm font-medium transition-colors">
                🔄 Regenerate All
            </button>
            <button onclick="Wizard.continueToNext('generate')" class="continue-btn flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-lg text-sm font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed">
                Continue to Score →
            </button>
            {% endif %}
        </div>
    </div>

    <!-- Step 4: Score -->
    <div id="step-score" class="bg-slate-800 rounded-xl border border-slate-700/50 p-6 mb-4" data-step="score" data-status="{{ step_statuses.get('score', 'locked') }}">
        <div class="flex items-center justify-between mb-4">
            <h3 class="text-lg font-semibold text-white">4. Score Prompts</h3>
            <span class="px-3 py-1 rounded-full text-xs font-medium
                {% if step_statuses.get('score') == 'complete' %}bg-emerald-500/20 text-emerald-400
                {% elif step_statuses.get('score') == 'loading' %}bg-blue-500 text-white status-pulse
                {% elif step_statuses.get('score') == 'failed' %}bg-red-500/20 text-red-400
                {% elif step_statuses.get('score') == 'ready' %}bg-blue-500/20 text-blue-400
                {% else %}bg-slate-700 text-slate-400{% endif %}">
                {% if step_statuses.get('score') == 'complete' %}✓ Complete
                {% elif step_statuses.get('score') == 'loading' %}⏳ Loading...
                {% elif step_statuses.get('score') == 'failed' %}✗ Failed
                {% elif step_statuses.get('score') == 'ready' %}○ Ready
                {% else %}🔒 Locked{% endif %}
            </span>
        </div>
        {% set scored_prompts = state.focuses|map(attribute='prompts')|map('selectattr', 'overall_score', 'gt', 0)|list|sum(start=[]) if state and state.focuses else [] %}
        {% if scored_prompts|length > 0 %}
        <p class="text-sm text-slate-400 mb-4">Scored {{ scored_prompts|length }} prompts. Average score: {{ "%.2f"|format(scored_prompts|map(attribute='overall_score')|sum / scored_prompts|length) }}.</p>
        <div class="space-y-2 mb-4 max-h-64 overflow-y-auto">
            {% for focus in state.focuses %}
            {% for prompt in focus.prompts %}
            {% if prompt.overall_score > 0 %}
            <label class="flex items-center gap-3 p-3 rounded-lg hover:bg-slate-700/30 transition-colors cursor-pointer border border-transparent hover:border-slate-700/50">
                <input type="checkbox" class="step-item-checkbox rounded border-slate-600 bg-slate-700 text-blue-600 focus:ring-blue-500" 
                       value="{{ focus.name }}-{{ prompt.text[:30] }}" data-item-id="{{ focus.name }}-{{ prompt.text[:30] }}" data-step="score" checked>
                <span class="px-2 py-0.5 rounded text-xs font-medium
                    {% if prompt.overall_score >= 0.6 %}bg-emerald-500/20 text-emerald-400
                    {% elif prompt.overall_score >= 0.3 %}bg-amber-500/20 text-amber-400
                    {% else %}bg-red-500/20 text-red-400{% endif %}">{{ "%.2f"|format(prompt.overall_score) }}</span>
                <span class="text-slate-200 text-sm flex-1 truncate">{{ prompt.text }}</span>
            </label>
            {% endif %}
            {% endfor %}
            {% endfor %}
        </div>
        {% elif state and state.focuses and state.focuses|map(attribute='prompts')|map('length')|sum > 0 %}
        <p class="text-sm text-slate-400 mb-4">Score all prompts for brand relevance and mention likelihood.</p>
        <form hx-post="/api/score" hx-target="#score-result" hx-indicator="#score-spinner" hx-trigger="submit">
            <div class="flex items-center gap-3">
                <button type="submit" class="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-lg text-sm font-medium transition-colors">
                    📊 Run Scoring
                </button>
                <span id="score-spinner" class="htmx-indicator text-sm text-slate-400">Running...</span>
            </div>
        </form>
        <div id="score-result"></div>
        {% else %}
        <p class="text-sm text-slate-500 italic">Complete the Generate step first.</p>
        {% endif %}
        <div class="step-actions flex gap-3 mt-4">
            {% if scored_prompts|length > 0 %}
            <button onclick="Wizard.regenerate('score', [])" class="flex items-center gap-2 px-4 py-2 bg-slate-600 hover:bg-slate-500 text-white rounded-lg text-sm font-medium transition-colors">
                🔄 Re-score
            </button>
            <button onclick="Wizard.continueToNext('score')" class="continue-btn flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-lg text-sm font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed">
                Continue to Export →
            </button>
            {% endif %}
        </div>
    </div>

    <!-- Step 5: Export -->
    <div id="step-export" class="bg-slate-800 rounded-xl border border-slate-700/50 p-6 mb-4" data-step="export" data-status="{{ step_statuses.get('export', 'locked') }}">
        <div class="flex items-center justify-between mb-4">
            <h3 class="text-lg font-semibold text-white">5. Export Results</h3>
            <span class="px-3 py-1 rounded-full text-xs font-medium
                {% if scored_prompts|length > 0 %}bg-emerald-500/20 text-emerald-400
                {% elif state and state.focuses %}bg-blue-500/20 text-blue-400
                {% else %}bg-slate-700 text-slate-400{% endif %}">
                {% if scored_prompts|length > 0 %}✓ Ready
                {% elif state and state.focuses %}○ Ready
                {% else %}🔒 Locked{% endif %}
            </span>
        </div>
        {% if state and state.focuses %}
        <p class="text-sm text-slate-400 mb-4">Download your project data as JSON or CSV.</p>
        <div class="flex items-center gap-3">
            <a href="/api/export/download/json" class="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-lg text-sm font-medium transition-colors">
                📥 Download JSON
            </a>
            <a href="/api/export/download/csv" class="flex items-center gap-2 px-4 py-2 bg-slate-600 hover:bg-slate-500 text-white rounded-lg text-sm font-medium transition-colors">
                📥 Download CSV
            </a>
        </div>
        {% else %}
        <p class="text-sm text-slate-500 italic">Complete previous steps to enable export.</p>
        {% endif %}
    </div>
</div>

<script src="/static/js/wizard.js"></script>
{% endblock %}
```

- [ ] **Step 2: Verify pipeline.html updated**

Run: `grep -c "step-research" fp/web/templates/pipeline.html`
Expected: 1 (or more) matches

- [ ] **Step 3: Commit**

```bash
git add fp/web/templates/pipeline.html
git commit -m "feat(pipeline): rewrite pipeline.html as vertical wizard"
```

---

## Task 7: Update pages.py route to pass step_statuses context

**Files:**
- Modify: `fp/web/routes/pages.py` (find the pipeline route)

**Interfaces:**
- Consumes: state from get_state()
- Produces: Template context with `step_statuses` dict

- [ ] **Step 1: Read pages.py to find pipeline route**

Run: `cat fp/web/routes/pages.py`
Expected: Shows the pipeline route definition

- [ ] **Step 2: Add step_statuses to pipeline route context**

In `fp/web/routes/pages.py`, find the pipeline route and modify it to include step_statuses. The existing route looks like:

```python
@router.get("/pipeline")
async def pipeline_page(request: Request):
    templates = request.app.state.templates
    state = get_state()
    return templates.TemplateResponse(request, "pipeline.html", {"state": state})
```

Modify it to:

```python
@router.get("/pipeline")
async def pipeline_page(request: Request):
    templates = request.app.state.templates
    state = get_state()
    
    # Compute step statuses for wizard UI
    step_statuses = {}
    if state:
        # Research
        step_statuses["research"] = "complete" if (state.web_data and state.web_data.get("stats", {}).get("total_queries", 0) > 0) else "ready"
        # Discover
        step_statuses["discover"] = "complete" if state.focuses else ("ready" if state.web_data else "locked")
        # Generate
        total_prompts = sum(len(f.prompts) for f in state.focuses)
        step_statuses["generate"] = "complete" if total_prompts > 0 else ("ready" if state.focuses else "locked")
        # Score
        scored = sum(1 for f in state.focuses for p in f.prompts if p.overall_score > 0)
        step_statuses["score"] = "complete" if (scored > 0 and scored == total_prompts) else ("ready" if total_prompts > 0 else "locked")
        # Export
        step_statuses["export"] = "ready" if scored > 0 else "locked"
    else:
        for s in ["research", "discover", "generate", "score", "export"]:
            step_statuses[s] = "locked"
    
    return templates.TemplateResponse(request, "pipeline.html", {
        "state": state,
        "step_statuses": step_statuses
    })
```

- [ ] **Step 3: Verify pages.py updated**

Run: `grep -n "step_statuses" fp/web/routes/pages.py`
Expected: Shows the variable assignment

- [ ] **Step 4: Commit**

```bash
git add fp/web/routes/pages.py
git commit -m "feat(pipeline): pass step_statuses to pipeline page template"
```

---

## Task 8: Test the wizard end-to-end

**Files:**
- Test: Run the web UI and verify the wizard works

- [ ] **Step 1: Start the web server**

Run: `cd /Users/admin/Documents/GitHub/focus-prompt && python -m fp.web.app`
Expected: Server starts on port 8000

- [ ] **Step 2: Open browser and verify wizard layout**

Open: `http://localhost:8000/pipeline`
Expected:
- Step indicator bar at top shows 5 steps
- Step cards stack vertically below
- Locked steps show 🔒 icon
- No tabs at top (replaced by wizard layout)

- [ ] **Step 3: Test checkbox state management**

In browser:
- Click a checkbox to uncheck it
- Verify the Continue button becomes disabled (opacity-50)
Expected: Continue button visually disables when no checkboxes are checked

- [ ] **Step 4: Test scroll navigation**

In browser:
- Check at least one checkbox in a step
- Click "Continue to Next Step →"
Expected: Page scrolls smoothly to the next step

- [ ] **Step 5: Test regenerate (if data exists)**

In browser:
- If data exists for a step, click "🔄 Regenerate"
Expected: Page reloads and step data refreshes

- [ ] **Step 6: Stop the server**

Press Ctrl+C in terminal to stop the server.

---

## Acceptance Criteria

- [ ] Vertical wizard layout with 5 sequential steps
- [ ] Step indicator bar at top showing progress
- [ ] Clear status indicators (🔒 locked, ○ ready, ⏳ loading, ✓ complete, ✗ failed)
- [ ] Summary data displayed after each step completes
- [ ] Checkbox-based keep/discard mechanism
- [ ] Continue button disabled when nothing selected
- [ ] Regenerate button per step
- [ ] Smooth scroll to next step on Continue
- [ ] Responsive design (mobile-friendly)
- [ ] Uses existing dark slate theme

## Implementation Order

1. wizard-step.html template (Task 1)
2. step-items.html partial (Task 2)
3. wizard.js (Task 3)
4. Backend: keep endpoint (Task 4)
5. Backend: regenerate endpoint (Task 5)
6. Rewritten pipeline.html (Task 6)
7. pages.py context update (Task 7)
8. End-to-end testing (Task 8)
