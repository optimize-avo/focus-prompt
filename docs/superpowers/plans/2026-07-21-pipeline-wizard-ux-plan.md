# Pipeline Wizard UX Redesign Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Redesign the pipeline flow to be a step-by-step wizard with review modals at each step, making it understandable for non-technical digital marketers.

**Architecture:** Refactor `pipeline.html` into a wizard layout with separate views per step. Add API endpoints for item selection/review. Add modal components for reviewing all items at each step. Fix HTMX responses to auto-show results without refresh.

**Tech Stack:** Python (FastAPI/HTMX), Jinja2 templates, vanilla JavaScript, Tailwind CSS

## Global Constraints

- Python 3.11+
- FastAPI + HTMX for server-rendered UI
- Tailwind CSS for styling
- No external JS frameworks (vanilla JS only)
- Indonesian language for UI labels
- All API responses must be JSON
- HTMX responses must trigger UI updates without page refresh

---

## File Structure

| File | Responsibility |
|------|----------------|
| `fp/web/templates/pipeline.html` | Main wizard layout with step indicator and navigation |
| `fp/web/templates/partials/research.html` | Research step content (pre/post run) |
| `fp/web/templates/partials/discover.html` | Discover step content |
| `fp/web/templates/partials/generate.html` | Generate step content |
| `fp/web/templates/partials/score.html` | Score step content |
| `fp/web/templates/partials/export.html` | Export step content |
| `fp/web/templates/partials/modal.html` | Reusable modal component |
| `fp/web/routes/pipeline.py` | API endpoints for selection/review |
| `fp/web/static/js/wizard.js` | Wizard navigation + modal logic |
| `fp/web/static/js/modal.js` | Modal component logic |
| `fp/web/static/css/custom.css` | Modal + wizard styles |

---

## Task 1: Create Reusable Modal Component

**Files:**
- Create: `fp/web/templates/partials/modal.html`
- Create: `fp/web/static/js/modal.js`
- Create: `fp/web/static/css/custom.css`

**Interfaces:**
- Consumes: None (first task)
- Produces: `openModal(config)`, `closeModal()`, `getSelectedItems()` functions

- [ ] **Step 1: Create modal HTML template**

```html
<!-- fp/web/templates/partials/modal.html -->
<div id="review-modal" class="fixed inset-0 z-50 hidden" role="dialog" aria-modal="true">
  <div class="fixed inset-0 bg-black/60 backdrop-blur-sm" onclick="Modal.close()"></div>
  <div class="fixed inset-4 md:inset-12 lg:inset-24 bg-slate-800 rounded-2xl shadow-2xl flex flex-col overflow-hidden">
    <!-- Header -->
    <div class="flex items-center justify-between px-6 py-4 border-b border-slate-700">
      <h3 id="modal-title" class="text-lg font-semibold text-white">Review Items</h3>
      <button onclick="Modal.close()" class="text-slate-400 hover:text-white transition-colors">
        <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
        </svg>
      </button>
    </div>
    
    <!-- Search + Controls -->
    <div class="px-6 py-3 border-b border-slate-700 flex items-center gap-4">
      <input type="text" id="modal-search" placeholder="Search..." 
             class="flex-1 bg-slate-700 border border-slate-600 rounded-lg px-4 py-2 text-sm text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500"
             oninput="Modal.filterItems(this.value)">
      <button id="modal-select-all" onclick="Modal.toggleSelectAll()" 
              class="px-3 py-2 bg-slate-600 hover:bg-slate-500 text-white rounded-lg text-sm font-medium transition-colors">
        Select All
      </button>
    </div>
    
    <!-- Items List -->
    <div id="modal-items" class="flex-1 overflow-y-auto px-6 py-4 space-y-2">
      <!-- Items rendered here by JS -->
    </div>
    
    <!-- Footer -->
    <div class="px-6 py-4 border-t border-slate-700 flex items-center justify-between">
      <span id="modal-count" class="text-sm text-slate-400">Selected: 0 / 0</span>
      <div class="flex gap-3">
        <button onclick="Modal.close()" class="px-4 py-2 bg-slate-600 hover:bg-slate-500 text-white rounded-lg text-sm font-medium transition-colors">
          Batal
        </button>
        <button onclick="Modal.save()" class="px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-lg text-sm font-medium transition-colors">
          Simpan Pilihan
        </button>
      </div>
    </div>
  </div>
</div>
```

- [ ] **Step 2: Create modal JavaScript**

```javascript
// fp/web/static/js/modal.js
const Modal = {
    items: [],
    config: null,
    
    open(config) {
        this.config = config;
        this.items = config.items.map(item => ({...item}));
        document.getElementById('modal-title').textContent = config.title;
        this.render();
        document.getElementById('review-modal').classList.remove('hidden');
        document.body.style.overflow = 'hidden';
    },
    
    close() {
        document.getElementById('review-modal').classList.add('hidden');
        document.body.style.overflow = '';
    },
    
    render() {
        const container = document.getElementById('modal-items');
        const search = document.getElementById('modal-search').value.toLowerCase();
        
        const filtered = this.items.filter(item => 
            item.text.toLowerCase().includes(search)
        );
        
        container.innerHTML = filtered.map(item => `
            <label class="flex items-center gap-3 p-3 rounded-lg hover:bg-slate-700/30 transition-colors cursor-pointer border border-transparent hover:border-slate-700/50">
                <input type="checkbox" 
                       ${item.selected ? 'checked' : ''} 
                       onchange="Modal.toggleItem('${item.id}')"
                       class="rounded border-slate-600 bg-slate-700 text-blue-600 focus:ring-blue-500">
                <span class="text-slate-200 text-sm flex-1">${item.text}</span>
                ${item.relevant !== undefined ? `
                    <button onclick="Modal.toggleRelevant('${item.id}')" 
                            class="px-2 py-1 text-xs rounded ${item.relevant ? 'bg-emerald-500/20 text-emerald-400' : 'bg-slate-600 text-slate-400'}">
                        ${item.relevant ? 'Relevant' : 'Mark'}
                    </button>
                ` : ''}
            </label>
        `).join('');
        
        this.updateCount();
    },
    
    filterItems(query) {
        this.render();
    },
    
    toggleItem(id) {
        const item = this.items.find(i => i.id === id);
        if (item) item.selected = !item.selected;
        this.updateCount();
    },
    
    toggleRelevant(id) {
        const item = this.items.find(i => i.id === id);
        if (item) item.relevant = !item.relevant;
        this.render();
    },
    
    toggleSelectAll() {
        const allSelected = this.items.every(i => i.selected);
        this.items.forEach(i => i.selected = !allSelected);
        this.render();
    },
    
    updateCount() {
        const selected = this.items.filter(i => i.selected).length;
        document.getElementById('modal-count').textContent = `Selected: ${selected} / ${this.items.length}`;
    },
    
    getSelected() {
        return this.items.filter(i => i.selected);
    },
    
    async save() {
        const selected = this.getSelected();
        if (this.config.onSave) {
            await this.config.onSave(selected);
        }
        this.close();
    }
};

window.Modal = Modal;
```

- [ ] **Step 3: Create modal CSS**

```css
/* fp/web/static/css/custom.css */
#review-modal {
    z-index: 50;
}

#review-modal .fixed.inset-0 {
    z-index: 51;
}

#review-modal > div:last-child {
    z-index: 52;
}

/* Wizard step indicator */
.step-indicator {
    transition: all 0.3s ease;
}

.step-indicator.active {
    transform: scale(1.1);
}

/* Status pulse animation */
@keyframes status-pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.5; }
}

.status-pulse {
    animation: status-pulse 2s ease-in-out infinite;
}

/* Smooth transitions for step content */
.step-content {
    transition: opacity 0.3s ease, transform 0.3s ease;
}

.step-content.entering {
    opacity: 0;
    transform: translateX(20px);
}

.step-content.active {
    opacity: 1;
    transform: translateX(0);
}
```

- [ ] **Step 4: Test modal opens and closes**

Run: Open browser, click any "Review" button, verify modal appears, click close, verify modal disappears.

- [ ] **Step 5: Commit**

```bash
git add fp/web/templates/partials/modal.html fp/web/static/js/modal.js fp/web/static/css/custom.css
git commit -m "feat: add reusable modal component for item review"
```

---

## Task 2: Add Selection API Endpoints

**Files:**
- Modify: `fp/web/routes/pipeline.py`

**Interfaces:**
- Consumes: `ProjectState` from `fp.web.deps`
- Produces: `POST /api/pipeline/step/{step}/selection`, `GET /api/pipeline/step/{step}/items`

- [ ] **Step 1: Add selection storage to ProjectState**

```python
# In fp/models.py, add to ProjectState class:
step_selections: dict[str, list[str]] = {}
```

- [ ] **Step 2: Add GET /api/pipeline/step/{step}/items endpoint**

```python
# fp/web/routes/pipeline.py

@router.get("/api/pipeline/step/{step}/items")
async def get_step_items(request: Request, step: str):
    """Get all items for review modal."""
    state = get_state()
    if not state:
        return {"error": "No project found"}
    
    items = []
    
    if step == "research":
        if state.web_data:
            queries = state.web_data.get("autocomplete", [])
            selected = state.step_selections.get("research", queries)
            items = [
                {"id": q, "text": q, "selected": q in selected}
                for q in queries
            ]
    
    elif step == "discover":
        if state.focuses:
            selected = state.step_selections.get("discover", [f.name for f in state.focuses])
            items = [
                {"id": f.name, "text": f.name, "selected": f.name in selected}
                for f in state.focuses
            ]
    
    elif step == "generate":
        if state.focuses:
            selected = state.step_selections.get("generate", [])
            for focus in state.focuses:
                for prompt in focus.prompts:
                    pid = f"{focus.name}-{prompt.text[:30]}"
                    items.append({
                        "id": pid,
                        "text": prompt.text,
                        "selected": pid in selected if selected else True,
                        "group": focus.name
                    })
    
    elif step == "score":
        if state.focuses:
            for focus in state.focuses:
                for prompt in focus.prompts:
                    if prompt.overall_score > 0:
                        items.append({
                            "id": f"{focus.name}-{prompt.text[:30]}",
                            "text": prompt.text,
                            "score": prompt.overall_score,
                            "selected": True
                        })
    
    return {
        "step": step,
        "items": items,
        "total": len(items),
        "selected_count": sum(1 for i in items if i["selected"])
    }
```

- [ ] **Step 3: Add POST /api/pipeline/step/{step}/selection endpoint**

```python
# fp/web/routes/pipeline.py

@router.post("/api/pipeline/step/{step}/selection")
async def save_step_selection(request: Request, step: str):
    """Save user's selection for a step."""
    state = get_state()
    if not state:
        return {"status": "error", "message": "No project found"}
    
    try:
        body = await request.json()
        selected_ids = body.get("selected_ids", [])
    except Exception:
        selected_ids = []
    
    if not selected_ids:
        return {"status": "error", "message": "Must select at least one item"}
    
    # Store selections
    if not hasattr(state, 'step_selections'):
        state.step_selections = {}
    state.step_selections[step] = selected_ids
    save_state(state)
    
    # Apply selections to actual data
    if step == "research" and state.web_data:
        queries = state.web_data.get("autocomplete", [])
        state.web_data["autocomplete"] = [q for q in queries if q in selected_ids]
        state.web_data["stats"]["total_queries"] = len(state.web_data["autocomplete"])
    
    elif step == "discover":
        state.focuses = [f for f in state.focuses if f.name in selected_ids]
    
    elif step == "generate":
        for focus in state.focuses:
            focus.prompts = [
                p for p in focus.prompts
                if f"{focus.name}-{p.text[:30]}" in selected_ids
            ]
    
    save_state(state)
    
    return {
        "status": "ok",
        "selected": len(selected_ids),
        "total": len(selected_ids)
    }
```

- [ ] **Step 4: Test API endpoints**

Run: 
```bash
curl http://localhost:8000/api/pipeline/research/items
curl -X POST http://localhost:8000/api/pipeline/research/selection -H "Content-Type: application/json" -d '{"selected_ids": ["query1", "query2"]}'
```

- [ ] **Step 5: Commit**

```bash
git add fp/web/routes/pipeline.py fp/models.py
git commit -m "feat: add selection API endpoints for pipeline review"
```

---

## Task 3: Refactor Pipeline to Wizard Layout

**Files:**
- Modify: `fp/web/templates/pipeline.html`

**Interfaces:**
- Consumes: Modal component from Task 1
- Produces: Step-by-step wizard layout with progress indicator

- [ ] **Step 1: Rewrite pipeline.html with wizard structure**

```html
{% extends "base.html" %}
{% block title %}Pipeline — Focus Prompt{% endblock %}
{% block content %}
<div class="max-w-4xl mx-auto space-y-6">
    <!-- Progress Indicator -->
    <div class="bg-slate-800 rounded-xl border border-slate-700/50 p-4">
        <div class="flex items-center justify-between">
            {% set steps = [
                ('research', 'Research', '1'),
                ('discover', 'Discover', '2'),
                ('generate', 'Generate', '3'),
                ('score', 'Score', '4'),
                ('export', 'Export', '5')
            ] %}
            {% for step_id, step_name, step_num in steps %}
            <div class="flex items-center">
                <button onclick="Wizard.goToStep('{{ step_id }}')" 
                        class="step-btn flex flex-col items-center group cursor-pointer
                               {% if current_step == step_id %}opacity-100
                               {% elif step_statuses.get(step_id) == 'complete' %}opacity-75
                               {% else %}opacity-50{% endif %}">
                    <div class="w-10 h-10 rounded-full flex items-center justify-center text-sm font-semibold transition-all
                                {% if step_statuses.get(step_id) == 'complete' %}bg-emerald-500 text-white
                                {% elif current_step == step_id %}bg-blue-500 text-white ring-4 ring-blue-500/30
                                {% else %}bg-slate-700 text-slate-400 group-hover:bg-slate-600{% endif %}">
                        {% if step_statuses.get(step_id) == 'complete' %}✓
                        {% else %}{{ step_num }}{% endif %}
                    </div>
                    <span class="text-xs mt-1 {% if current_step == step_id %}text-white font-medium{% else %}text-slate-400{% endif %}">
                        {{ step_name }}
                    </span>
                </button>
                {% if not loop.last %}
                <div class="w-12 h-0.5 mx-2 
                    {% if step_statuses.get(step_id) == 'complete' %}bg-emerald-500
                    {% else %}bg-slate-700{% endif %}"></div>
                {% endif %}
            </div>
            {% endfor %}
        </div>
    </div>

    <!-- Step Content -->
    <div id="step-content" class="bg-slate-800 rounded-xl border border-slate-700/50 p-6 min-h-[400px]">
        {% include "partials/" ~ current_step ~ ".html" %}
    </div>

    <!-- Navigation -->
    <div class="flex items-center justify-between">
        <button onclick="Wizard.prevStep()" 
                {% if current_step == 'research' %}disabled{% endif %}
                class="flex items-center gap-2 px-4 py-2 bg-slate-600 hover:bg-slate-500 text-white rounded-lg text-sm font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed">
            ← Kembali
        </button>
        <button onclick="Wizard.nextStep()" 
                {% if not step_statuses.get(current_step) == 'complete' %}disabled{% endif %}
                class="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-lg text-sm font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed">
            {% if current_step == 'export' %}Selesai ✓{% else %}Lanjut →{% endif %}
        </button>
    </div>
</div>

<!-- Modal -->
{% include "partials/modal.html" %}

<script src="/static/js/modal.js"></script>
<script src="/static/js/wizard.js"></script>
{% endblock %}
```

- [ ] **Step 2: Add Wizard navigation logic**

```javascript
// fp/web/static/js/wizard.js
const Wizard = {
    currentStep: '{{ current_step }}',
    steps: ['research', 'discover', 'generate', 'score', 'export'],
    
    async goToStep(stepId) {
        const currentIdx = this.steps.indexOf(this.currentStep);
        const targetIdx = this.steps.indexOf(stepId);
        
        // Only allow going back or to completed steps
        if (targetIdx < currentIdx || this.isStepCompleted(stepId)) {
            window.location.href = `/pipeline/${stepId}`;
        }
    },
    
    isStepCompleted(stepId) {
        // Check from server-rendered status
        return document.querySelector(`[data-step="${stepId}"]`)?.dataset.status === 'complete';
    },
    
    prevStep() {
        const idx = this.steps.indexOf(this.currentStep);
        if (idx > 0) {
            window.location.href = `/pipeline/${this.steps[idx - 1]}`;
        }
    },
    
    nextStep() {
        const idx = this.steps.indexOf(this.currentStep);
        if (idx < this.steps.length - 1) {
            window.location.href = `/pipeline/${this.steps[idx + 1]}`;
        }
    }
};

window.Wizard = Wizard;
```

- [ ] **Step 3: Add route for step navigation**

```python
# fp/web/routes/pipeline.py

@router.get("/pipeline/{step}")
async def pipeline_step(request: Request, step: str):
    """Render specific pipeline step."""
    if step not in ['research', 'discover', 'generate', 'score', 'export']:
        return RedirectResponse(url="/pipeline/research")
    
    templates = request.app.state.templates
    state = get_state()
    step_statuses = _phase_status(state) if state else {}
    
    return templates.TemplateResponse(request, "pipeline.html", {
        "state": state,
        "current_step": step,
        "step_statuses": step_statuses
    })
```

- [ ] **Step 4: Test wizard navigation**

Run: Open `/pipeline/research`, click through steps, verify navigation works.

- [ ] **Step 5: Commit**

```bash
git add fp/web/templates/pipeline.html fp/web/static/js/wizard.js fp/web/routes/pipeline.py
git commit -m "refactor: convert pipeline to wizard step-by-step layout"
```

---

## Task 4: Update Research Step with Auto-Show Results

**Files:**
- Modify: `fp/web/templates/partials/research.html`
- Modify: `fp/web/routes/pipeline.py`

**Interfaces:**
- Consumes: Modal from Task 1, Selection API from Task 2
- Produces: Research step with pre-run queries, auto-show results, review modal trigger

- [ ] **Step 1: Rewrite research.html partial**

```html
<!-- fp/web/templates/partials/research.html -->
<div class="space-y-6">
    <!-- Header -->
    <div>
        <h2 class="text-xl font-bold text-white mb-2">Langkah 1: Riset Query Real</h2>
        <p class="text-slate-400">Kami akan mencari query real yang diketik orang di Google tentang layananmu.</p>
    </div>

    {% if state and state.web_data and state.web_data.get('stats', {}).get('total_queries', 0) > 0 %}
    <!-- Post-Run Results -->
    <div class="bg-emerald-500/10 border border-emerald-500/20 rounded-lg p-4">
        <p class="text-emerald-400 font-medium mb-2">✓ Riset selesai!</p>
        <p class="text-slate-300">📊 <strong>{{ state.web_data['stats']['total_queries'] }}</strong> queries ditemukan dari Google</p>
    </div>

    <!-- Preview -->
    <div>
        <p class="text-sm text-slate-400 mb-3">Sample queries yang ditemukan:</p>
        <div class="space-y-2">
            {% for query in state.web_data.get('autocomplete', [])[:5] %}
            <div class="flex items-center gap-2 text-sm text-slate-300">
                <span class="text-slate-500">•</span>
                {{ query }}
            </div>
            {% endfor %}
        </div>
    </div>

    <!-- Review Button -->
    <button onclick="openResearchModal()" 
            class="flex items-center gap-2 px-4 py-2 bg-slate-600 hover:bg-slate-500 text-white rounded-lg text-sm font-medium transition-colors">
        🔍 Review Semua Queries
    </button>

    {% else %}
    <!-- Pre-Run UI -->
    <div>
        <p class="text-sm text-slate-400 mb-3">Query yang akan dicari:</p>
        <div class="space-y-2 mb-4">
            {% for cat in state.config.brand.service_categories if state %}
            <div class="flex items-center gap-2 text-sm text-slate-300">
                <span class="text-slate-500">•</span>
                jasa {{ cat }} murah
            </div>
            <div class="flex items-center gap-2 text-sm text-slate-300">
                <span class="text-slate-500">•</span>
                platform {{ cat }} terbaik
            </div>
            {% endfor %}
            {% for comp in state.config.brand.competitors[:2] if state %}
            <div class="flex items-center gap-2 text-sm text-slate-300">
                <span class="text-slate-500">•</span>
                {{ comp }} review
            </div>
            {% endfor %}
        </div>

        <!-- Add Query -->
        <div id="add-query-form" class="hidden mb-4">
            <div class="flex gap-2">
                <input type="text" id="new-query" placeholder="Tambah query baru..." 
                       class="flex-1 bg-slate-700 border border-slate-600 rounded-lg px-3 py-2 text-sm text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500">
                <button onclick="addQuery()" class="px-3 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-lg text-sm">
                    + Tambah
                </button>
            </div>
        </div>
        <button onclick="document.getElementById('add-query-form').classList.toggle('hidden')" 
                class="text-sm text-blue-400 hover:text-blue-300 mb-4">
            + Tambah Query
        </button>
    </div>

    <!-- Run Button -->
    <form hx-post="/api/research" hx-target="#step-content" hx-swap="innerHTML">
        <button type="submit" class="flex items-center gap-2 px-6 py-3 bg-blue-600 hover:bg-blue-500 text-white rounded-lg font-medium transition-colors">
            🔍 Mulai Riset
        </button>
    </form>
    {% endif %}
</div>

<script>
function openResearchModal() {
    fetch('/api/pipeline/research/items')
        .then(r => r.json())
        .then(data => {
            Modal.open({
                title: `Review Queries (${data.total})`,
                items: data.items,
                onSave: async (selected) => {
                    await fetch('/api/pipeline/research/selection', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({selected_ids: selected.map(i => i.id)})
                    });
                    location.reload();
                }
            });
        });
}

function addQuery() {
    const input = document.getElementById('new-query');
    if (input.value.trim()) {
        // Add to list visually
        const list = document.querySelector('.space-y-2.mb-4');
        const div = document.createElement('div');
        div.className = 'flex items-center gap-2 text-sm text-slate-300';
        div.innerHTML = `<span class="text-slate-500">•</span> ${input.value}`;
        list.appendChild(div);
        input.value = '';
    }
}
</script>
```

- [ ] **Step 2: Fix HTMX response for research**

```python
# fp/web/routes/pipeline.py - update run_research

@router.post("/api/research", response_class=HTMLResponse)
async def run_research(request: Request, extra: str = Form("")):
    """Run research step."""
    state = get_state()
    if not state:
        return HTMLResponse('<p class="text-red-600">No project found.</p>')
    
    extra_queries = [q.strip() for q in extra.split(",") if q.strip()] if extra else None
    try:
        web_data = await research_queries(state.config.brand, extra_queries=extra_queries)
        state.web_data = web_data
        save_state(state)
        
        # Return updated step content
        templates = request.app.state.templates
        return templates.TemplateResponse(request, "partials/research.html", {"state": state})
    except Exception as e:
        return HTMLResponse(f'<p class="text-red-600">Error: {e}</p>')
```

- [ ] **Step 3: Test research step**

Run: Open `/pipeline/research`, run research, verify results auto-show without refresh.

- [ ] **Step 4: Commit**

```bash
git add fp/web/templates/partials/research.html fp/web/routes/pipeline.py
git commit -m "feat: research step with auto-show results and review modal"
```

---

## Task 5: Update Remaining Steps (Discover, Generate, Score, Export)

**Files:**
- Modify: `fp/web/templates/partials/discover.html`
- Modify: `fp/web/templates/partials/generate.html`
- Modify: `fp/web/templates/partials/score.html`
- Modify: `fp/web/templates/partials/export.html`

**Interfaces:**
- Consumes: Modal from Task 1, Selection API from Task 2
- Produces: Updated step partials with auto-show results and review modals

- [ ] **Step 1: Update discover.html**

```html
<!-- fp/web/templates/partials/discover.html -->
<div class="space-y-6">
    <div>
        <h2 class="text-xl font-bold text-white mb-2">Langkah 2: Temukan Focus Areas</h2>
        <p class="text-slate-400">Kami akan menganalisis query dan menemukan topik-topik utama yang relevan dengan bisnismu.</p>
    </div>

    {% if state and state.focuses %}
    <!-- Post-Run Results -->
    <div class="bg-emerald-500/10 border border-emerald-500/20 rounded-lg p-4">
        <p class="text-emerald-400 font-medium mb-2">✓ Focus areas ditemukan!</p>
        <p class="text-slate-300">📊 <strong>{{ state.focuses|length }}</strong> focus areas ditemukan</p>
    </div>

    <!-- Focus List -->
    <div class="space-y-2">
        {% for focus in state.focuses %}
        <div class="flex items-center justify-between p-3 bg-slate-700/30 rounded-lg">
            <span class="text-slate-200">{{ focus.name }}</span>
            <span class="text-slate-500 text-sm">{{ focus.signal_count or 0 }} signals</span>
        </div>
        {% endfor %}
    </div>

    <!-- Review Button -->
    <button onclick="openDiscoverModal()" 
            class="flex items-center gap-2 px-4 py-2 bg-slate-600 hover:bg-slate-500 text-white rounded-lg text-sm font-medium transition-colors">
        💡 Review Semua Focus
    </button>

    {% elif state and state.web_data %}
    <!-- Pre-Run UI -->
    <div class="bg-slate-700/30 rounded-lg p-4">
        <p class="text-slate-300">Menggunakan <strong>{{ state.web_data.get('stats', {}).get('total_queries', 0) }}</strong> queries dari langkah sebelumnya.</p>
    </div>

    <form hx-post="/api/discover" hx-target="#step-content" hx-swap="innerHTML">
        <button type="submit" class="flex items-center gap-2 px-6 py-3 bg-blue-600 hover:bg-blue-500 text-white rounded-lg font-medium transition-colors">
            💡 Temukan Focus Areas
        </button>
    </form>
    {% else %}
    <p class="text-slate-500 italic">Selesaikan langkah Research terlebih dahulu.</p>
    {% endif %}
</div>

<script>
function openDiscoverModal() {
    fetch('/api/pipeline/discover/items')
        .then(r => r.json())
        .then(data => {
            Modal.open({
                title: `Review Focus Areas (${data.total})`,
                items: data.items,
                onSave: async (selected) => {
                    await fetch('/api/pipeline/discover/selection', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({selected_ids: selected.map(i => i.id)})
                    });
                    location.reload();
                }
            });
        });
}
</script>
```

- [ ] **Step 2: Update generate.html**

```html
<!-- fp/web/templates/partials/generate.html -->
<div class="space-y-6">
    <div>
        <h2 class="text-xl font-bold text-white mb-2">Langkah 3: Generate Prompts</h2>
        <p class="text-slate-400">Kami akan membuat berbagai variasi prompt untuk setiap focus area.</p>
    </div>

    {% set total_prompts = state.focuses|map(attribute='prompts')|map('length')|sum if state and state.focuses else 0 %}
    {% if total_prompts > 0 %}
    <!-- Post-Run Results -->
    <div class="bg-emerald-500/10 border border-emerald-500/20 rounded-lg p-4">
        <p class="text-emerald-400 font-medium mb-2">✓ Prompts dihasilkan!</p>
        <p class="text-slate-300">📊 <strong>{{ total_prompts }}</strong> prompts dihasilkan di <strong>{{ state.focuses|length }}</strong> focus areas</p>
    </div>

    <!-- Prompts by Focus -->
    <div class="space-y-4">
        {% for focus in state.focuses %}
        <div>
            <h4 class="text-sm font-medium text-slate-300 mb-2">{{ focus.name }} ({{ focus.prompts|length }})</h4>
            <div class="space-y-1">
                {% for prompt in focus.prompts[:3] %}
                <p class="text-sm text-slate-400 truncate">• {{ prompt.text }}</p>
                {% endfor %}
                {% if focus.prompts|length > 3 %}
                <p class="text-xs text-slate-500">...dan {{ focus.prompts|length - 3 }} lainnya</p>
                {% endif %}
            </div>
        </div>
        {% endfor %}
    </div>

    <!-- Review Button -->
    <button onclick="openGenerateModal()" 
            class="flex items-center gap-2 px-4 py-2 bg-slate-600 hover:bg-slate-500 text-white rounded-lg text-sm font-medium transition-colors">
        ✨ Review Semua Prompts
    </button>

    {% elif state and state.focuses %}
    <!-- Pre-Run UI -->
    <div class="bg-slate-700/30 rounded-lg p-4">
        <p class="text-slate-300">Menggunakan <strong>{{ state.focuses|length }}</strong> focus areas dari langkah sebelumnya.</p>
        <p class="text-slate-400 text-sm mt-1">Mode: <strong>{{ state.config.prompt_mode.value }}</strong></p>
    </div>

    <form hx-post="/api/generate" hx-target="#step-content" hx-swap="innerHTML">
        <button type="submit" class="flex items-center gap-2 px-6 py-3 bg-blue-600 hover:bg-blue-500 text-white rounded-lg font-medium transition-colors">
            ✨ Generate Prompts
        </button>
    </form>
    {% else %}
    <p class="text-slate-500 italic">Selesaikan langkah Discover terlebih dahulu.</p>
    {% endif %}
</div>

<script>
function openGenerateModal() {
    fetch('/api/pipeline/generate/items')
        .then(r => r.json())
        .then(data => {
            // Group by focus
            const grouped = {};
            data.items.forEach(item => {
                if (!grouped[item.group]) grouped[item.group] = [];
                grouped[item.group].push(item);
            });
            
            Modal.open({
                title: `Review Prompts (${data.total})`,
                items: data.items,
                grouped: true,
                onSave: async (selected) => {
                    await fetch('/api/pipeline/generate/selection', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({selected_ids: selected.map(i => i.id)})
                    });
                    location.reload();
                }
            });
        });
}
</script>
```

- [ ] **Step 3: Update score.html**

```html
<!-- fp/web/templates/partials/score.html -->
<div class="space-y-6">
    <div>
        <h2 class="text-xl font-bold text-white mb-2">Langkah 4: Skor Relevansi</h2>
        <p class="text-slate-400">Kami akan menilai setiap prompt untuk relevansi dengan brand Anda.</p>
    </div>

    {% set scored_prompts = [] %}
    {% if state and state.focuses %}
        {% for focus in state.focuses %}
            {% for prompt in focus.prompts %}
                {% if prompt.overall_score is defined and prompt.overall_score > 0 %}
                    {% set _ = scored_prompts.append(prompt) %}
                {% endif %}
            {% endfor %}
        {% endfor %}
    {% endif %}

    {% if scored_prompts|length > 0 %}
    <!-- Post-Run Results -->
    <div class="bg-emerald-500/10 border border-emerald-500/20 rounded-lg p-4">
        <p class="text-emerald-400 font-medium mb-2">✓ Scoring selesai!</p>
        <p class="text-slate-300">
            📊 <strong>{{ scored_prompts|length }}</strong> prompts scored<br>
            📈 Average score: <strong>{{ "%.2f"|format(scored_prompts|map(attribute='overall_score')|sum / scored_prompts|length) }}</strong>
        </p>
    </div>

    <!-- Top Scores Preview -->
    <div class="space-y-2">
        {% for focus in state.focuses %}
            {% for prompt in focus.prompts %}
                {% if prompt.overall_score >= 0.7 %}
                <div class="flex items-center gap-3 p-2 bg-slate-700/30 rounded-lg">
                    <span class="px-2 py-0.5 rounded text-xs font-medium bg-emerald-500/20 text-emerald-400">
                        {{ "%.2f"|format(prompt.overall_score) }}
                    </span>
                    <span class="text-sm text-slate-300 truncate">{{ prompt.text }}</span>
                </div>
                {% endif %}
            {% endfor %}
        {% endfor %}
    </div>

    <!-- Review Button -->
    <button onclick="openScoreModal()" 
            class="flex items-center gap-2 px-4 py-2 bg-slate-600 hover:bg-slate-500 text-white rounded-lg text-sm font-medium transition-colors">
        📊 Review Hasil Skor
    </button>

    {% elif state and state.focuses and state.focuses|map(attribute='prompts')|map('length')|sum > 0 %}
    <!-- Pre-Run UI -->
    <div class="bg-slate-700/30 rounded-lg p-4">
        <p class="text-slate-300">Menggunakan <strong>{{ state.focuses|map(attribute='prompts')|map('length')|sum }}</strong> prompts dari langkah sebelumnya.</p>
    </div>

    <form hx-post="/api/score" hx-target="#step-content" hx-swap="innerHTML">
        <button type="submit" class="flex items-center gap-2 px-6 py-3 bg-blue-600 hover:bg-blue-500 text-white rounded-lg font-medium transition-colors">
            📊 Mulai Scoring
        </button>
    </form>
    {% else %}
    <p class="text-slate-500 italic">Selesaikan langkah Generate terlebih dahulu.</p>
    {% endif %}
</div>

<script>
function openScoreModal() {
    fetch('/api/pipeline/score/items')
        .then(r => r.json())
        .then(data => {
            Modal.open({
                title: `Review Scores (${data.total})`,
                items: data.items.map(i => ({...i, text: `${i.score.toFixed(2)} - ${i.text}`})),
                onSave: async () => { Modal.close(); }
            });
        });
}
</script>
```

- [ ] **Step 4: Update export.html**

```html
<!-- fp/web/templates/partials/export.html -->
<div class="space-y-6">
    <div>
        <h2 class="text-xl font-bold text-white mb-2">Langkah 5: Export Hasil</h2>
        <p class="text-slate-400">Unduh hasil riset Anda dalam format yang diinginkan.</p>
    </div>

    {% if state and state.focuses %}
    <!-- Summary -->
    <div class="bg-slate-700/30 rounded-lg p-4">
        <p class="text-slate-300 mb-2"><strong>Ringkasan:</strong></p>
        <ul class="space-y-1 text-sm text-slate-400">
            <li>• {{ state.focuses|length }} focus areas</li>
            <li>• {{ state.focuses|map(attribute='prompts')|map('length')|sum }} prompts
                {% set needs_review = state.focuses|map(attribute='prompts')|map('selectattr', 'needs_review')|map('length')|sum %}
                {% if needs_review > 0 %}
                <span class="text-amber-400">({{ needs_review }} need review)</span>
                {% endif %}
            </li>
        </ul>
    </div>

    <!-- Download Buttons -->
    <div class="flex flex-wrap gap-3">
        <a href="/api/export/download/csv" class="flex items-center gap-2 px-6 py-3 bg-blue-600 hover:bg-blue-500 text-white rounded-lg font-medium transition-colors">
            📥 Download CSV
        </a>
        <a href="/api/export/download/json" class="flex items-center gap-2 px-6 py-3 bg-slate-600 hover:bg-slate-500 text-white rounded-lg font-medium transition-colors">
            📥 Download JSON
        </a>
    </div>

    {% else %}
    <p class="text-slate-500 italic">Selesaikan langkah sebelumnya untuk export.</p>
    {% endif %}
</div>
```

- [ ] **Step 5: Test all steps**

Run: Go through each step, verify auto-show results and review modals work.

- [ ] **Step 6: Commit**

```bash
git add fp/web/templates/partials/*.html
git commit -m "feat: update all pipeline steps with auto-show results and review modals"
```

---

## Task 6: Update HTMX Responses for All Steps

**Files:**
- Modify: `fp/web/routes/pipeline.py`

**Interfaces:**
- Consumes: Updated partials from Task 5
- Produces: HTMX responses that return updated step content

- [ ] **Step 1: Update all POST endpoints to return templates**

```python
# fp/web/routes/pipeline.py - update all POST endpoints

@router.post("/api/discover", response_class=HTMLResponse)
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
        
        templates = request.app.state.templates
        return templates.TemplateResponse(request, "partials/discover.html", {"state": state})
    except Exception as e:
        return HTMLResponse(f'<p class="text-red-600">Focus generation failed: {e}</p>')


@router.post("/api/generate", response_class=HTMLResponse)
async def run_generate(request: Request):
    """Run generate step."""
    state = get_state()
    if not state or not state.focuses:
        return HTMLResponse('<p class="text-red-600">No focuses.</p>')
    
    try:
        updated = generate_all_prompts(state.config.brand, state.focuses, state.config.prompt_mode, language=state.config.language)
        state.focuses = updated
        save_state(state)
        
        templates = request.app.state.templates
        return templates.TemplateResponse(request, "partials/generate.html", {"state": state})
    except Exception as e:
        return HTMLResponse(f'<p class="text-red-600">Generation failed: {e}</p>')


@router.post("/api/score", response_class=HTMLResponse)
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
        
        templates = request.app.state.templates
        return templates.TemplateResponse(request, "partials/score.html", {"state": state})
    except Exception as e:
        return HTMLResponse(f'<p class="text-red-600">Scoring failed: {e}</p>')
```

- [ ] **Step 2: Test HTMX responses**

Run: Click each "Run" button, verify content updates without page refresh.

- [ ] **Step 3: Commit**

```bash
git add fp/web/routes/pipeline.py
git commit -m "fix: update HTMX responses to return template partials"
```

---

## Task 7: Final Testing and Cleanup

**Files:**
- None (testing only)

**Interfaces:**
- Consumes: All previous tasks
- Produces: Verified working pipeline wizard

- [ ] **Step 1: Full flow test**

Run through entire pipeline:
1. `/pipeline/research` - Run research, review queries in modal
2. `/pipeline/discover` - Run discover, review focuses in modal
3. `/pipeline/generate` - Run generate, review prompts in modal
4. `/pipeline/score` - Run scoring, review scores
5. `/pipeline/export` - Download CSV/JSON

- [ ] **Step 2: Test edge cases**

- Run research with no extra queries
- Try to go to next step before completing current step
- Review modal with many items (scroll, search)
- Deselect all items in modal

- [ ] **Step 3: Clean up any debug code**

Remove any console.log or debug statements.

- [ ] **Step 4: Final commit**

```bash
git add -A
git commit -m "feat: complete pipeline wizard UX redesign"
```

---

## Summary

| Task | Description | Files |
|------|-------------|-------|
| 1 | Create reusable modal component | modal.html, modal.js, custom.css |
| 2 | Add selection API endpoints | pipeline.py, models.py |
| 3 | Refactor to wizard layout | pipeline.html, wizard.js, pipeline.py |
| 4 | Update research step | research.html, pipeline.py |
| 5 | Update remaining steps | discover.html, generate.html, score.html, export.html |
| 6 | Fix HTMX responses | pipeline.py |
| 7 | Final testing | (testing only) |

**Total estimated time:** 2-3 hours for experienced developer
