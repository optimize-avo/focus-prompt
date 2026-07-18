# Focus Prompt Web UI Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a local web UI to focus-prompt using FastAPI + htmx, accessible via `fp web` command.

**Architecture:** Thin FastAPI wrapper around existing `fp/` logic. HTMX for dynamic partials. Tailwind CSS via CDN. All state in `fp-project.json`.

**Tech Stack:** FastAPI, Jinja2, htmx, Tailwind CSS (CDN), uvicorn

## Global Constraints

- Python 3.11+
- Reuse ALL existing logic from `fp/` — no business logic duplication
- HTMX pattern: hx-get/hx-post for step loading, hx-target for content replacement
- Tailwind CSS via CDN (no build step)
- Local only: localhost:8000
- `.env` file for config (already exists at project root)

## File Structure

```
fp/web/
├── __init__.py              # Empty
├── app.py                   # FastAPI app factory, startup
├── deps.py                  # get_state(), get_config()
├── routes/
│   ├── __init__.py          # Empty
│   ├── pages.py             # HTML page routes
│   ├── pipeline.py          # HTMX partial routes
│   └── settings.py          # Settings API
└── templates/
    ├── base.html            # Layout
    ├── index.html           # Dashboard
    ├── init.html            # Brand setup form
    ├── pipeline.html        # Pipeline view
    └── settings.html        # API config
```

---

### Task 1: Add Dependencies + Project Config

**Files:**
- Modify: `pyproject.toml:6-17` (dependencies)
- Modify: `pyproject.toml:19-21` (scripts)

**Interfaces:**
- Consumes: None
- Produces: None

- [ ] **Step 1: Add FastAPI dependencies**

Edit `pyproject.toml` dependencies section:

```toml
dependencies = [
    "typer>=0.12.0",
    "pydantic>=2.0.0",
    "rich>=13.0.0",
    "httpx>=0.27.0",
    "litellm>=1.50.0",
    "python-dotenv>=1.0.0",
    "click>=8.0.0",
    "pyyaml>=6.0",
    "beautifulsoup4>=4.12.0",
    "mcp>=1.0.0",
    "fastapi>=0.115.0",
    "uvicorn[standard]>=0.30.0",
    "jinja2>=3.1.0",
    "python-multipart>=0.0.9",
]
```

- [ ] **Step 2: Commit**

```bash
git add pyproject.toml
git commit -m "deps: add fastapi, uvicorn, jinja2 for web ui"
```

---

### Task 2: Create Web Module Structure

**Files:**
- Create: `fp/web/__init__.py`
- Create: `fp/web/routes/__init__.py`

**Interfaces:**
- Consumes: None
- Produces: None

- [ ] **Step 1: Create directories and init files**

```bash
mkdir -p fp/web/routes fp/web/templates
touch fp/web/__init__.py fp/web/routes/__init__.py
```

- [ ] **Step 2: Commit**

```bash
git add fp/web/
git commit -m "feat(web): scaffold web module structure"
```

---

### Task 3: Create Shared Dependencies (deps.py)

**Files:**
- Create: `fp/web/deps.py`

**Interfaces:**
- Consumes: `fp.models.ProjectState`, `fp.config.load_user_config`, `fp.config.get_current_config`
- Produces: `get_state() -> ProjectState | None`, `get_config() -> dict[str, str]`

- [ ] **Step 1: Write deps.py**

```python
"""Shared dependencies for web routes."""
from __future__ import annotations

import os
from pathlib import Path

from fp.models import ProjectState
from fp.config import load_user_config, get_current_config

PROJECT_FILE = "fp-project.json"


def get_state() -> ProjectState | None:
    """Load project state from fp-project.json, or None if not found."""
    if not Path(PROJECT_FILE).exists():
        return None
    return ProjectState.load(PROJECT_FILE)


def save_state(state: ProjectState) -> None:
    """Save project state to fp-project.json."""
    state.save(PROJECT_FILE)


def get_config() -> dict[str, str]:
    """Get current config values (loads user config first)."""
    load_user_config()
    return get_current_config()
```

- [ ] **Step 2: Commit**

```bash
git add fp/web/deps.py
git commit -m "feat(web): add shared deps (get_state, get_config)"
```

---

### Task 4: Create FastAPI App Factory

**Files:**
- Create: `fp/web/app.py`

**Interfaces:**
- Consumes: `fp.web.routes.pages`, `fp.web.routes.pipeline`, `fp.web.routes.settings`
- Produces: `create_app() -> FastAPI`, `main()`

- [ ] **Step 1: Write app.py**

```python
"""FastAPI app factory for focus-prompt web UI."""
from __future__ import annotations

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pathlib import Path

from fp.config import load_user_config

TEMPLATES_DIR = Path(__file__).parent / "templates"


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    # Load user config into env on startup
    load_user_config()

    app = FastAPI(title="Focus Prompt", docs_url=None, redoc_url=None)

    # Mount templates
    app.state.templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

    # Register routes
    from fp.web.routes.pages import router as pages_router
    from fp.web.routes.pipeline import router as pipeline_router
    from fp.web.routes.settings import router as settings_router

    app.include_router(pages_router)
    app.include_router(pipeline_router, prefix="/api")
    app.include_router(settings_router, prefix="/api")

    return app


def main():
    """Entry point for fp-web command."""
    import uvicorn
    uvicorn.run(create_app(), host="127.0.0.1", port=8000)
```

- [ ] **Step 2: Commit**

```bash
git add fp/web/app.py
git commit -m "feat(web): add FastAPI app factory"
```

---

### Task 5: Create Base Template

**Files:**
- Create: `fp/web/templates/base.html`

**Interfaces:**
- Consumes: None
- Produces: Base layout for all pages

- [ ] **Step 1: Write base.html**

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}Focus Prompt{% endblock %}</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://unpkg.com/htmx.org@2.0.4"></script>
    <style>
        .htmx-indicator { display: none; }
        .htmx-request .htmx-indicator { display: inline-block; }
        .htmx-request.htmx-indicator { display: inline-block; }
    </style>
</head>
<body class="bg-gray-50 text-gray-900 min-h-screen">
    <!-- Nav -->
    <nav class="bg-white border-b border-gray-200 px-4 py-3">
        <div class="max-w-5xl mx-auto flex items-center justify-between">
            <a href="/" class="text-lg font-semibold text-gray-800">Focus Prompt</a>
            <div class="flex gap-4 text-sm">
                <a href="/" class="text-gray-600 hover:text-gray-900">Dashboard</a>
                <a href="/init" class="text-gray-600 hover:text-gray-900">New Project</a>
                <a href="/pipeline" class="text-gray-600 hover:text-gray-900">Pipeline</a>
                <a href="/settings" class="text-gray-600 hover:text-gray-900">Settings</a>
            </div>
        </div>
    </nav>

    <!-- Content -->
    <main class="max-w-5xl mx-auto px-4 py-6">
        {% block content %}{% endblock %}
    </main>
</body>
</html>
```

- [ ] **Step 2: Commit**

```bash
git add fp/web/templates/base.html
git commit -m "feat(web): add base template with nav, tailwind, htmx"
```

---

### Task 6: Create Page Routes

**Files:**
- Create: `fp/web/routes/pages.py`

**Interfaces:**
- Consumes: `fp.web.deps.get_state`, `fp.web.deps.get_config`
- Produces: GET `/`, GET `/init`, GET `/pipeline`, GET `/settings`

- [ ] **Step 1: Write pages.py**

```python
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
```

- [ ] **Step 2: Commit**

```bash
git add fp/web/routes/pages.py
git commit -m "feat(web): add page routes (/, /init, /pipeline, /settings)"
```

---

### Task 7: Create Dashboard Template

**Files:**
- Create: `fp/web/templates/index.html`

**Interfaces:**
- Consumes: `state` (ProjectState | None) from page route
- Produces: Dashboard HTML

- [ ] **Step 1: Write index.html**

```html
{% extends "base.html" %}
{% block title %}Dashboard — Focus Prompt{% endblock %}
{% block content %}
<div class="space-y-6">
    <h1 class="text-2xl font-bold">Dashboard</h1>

    {% if state %}
    <!-- Project loaded -->
    <div class="bg-white rounded-lg border border-gray-200 p-6">
        <h2 class="text-lg font-semibold mb-4">{{ state.config.brand.name }}</h2>
        <div class="grid grid-cols-3 gap-4 text-sm">
            <div>
                <span class="text-gray-500">Description</span>
                <p class="font-medium">{{ state.config.brand.description or "—" }}</p>
            </div>
            <div>
                <span class="text-gray-500">Website</span>
                <p class="font-medium">{{ state.config.brand.website or "—" }}</p>
            </div>
            <div>
                <span class="text-gray-500">Mode</span>
                <p class="font-medium">{{ state.config.prompt_mode.value }}</p>
            </div>
        </div>

        <div class="mt-4 grid grid-cols-3 gap-4 text-sm">
            <div class="bg-gray-50 rounded p-3 text-center">
                <div class="text-2xl font-bold">{{ state.focuses | length }}</div>
                <div class="text-gray-500">Focuses</div>
            </div>
            <div class="bg-gray-50 rounded p-3 text-center">
                <div class="text-2xl font-bold">{{ state.focuses | map(attribute='prompts') | map('length') | sum }}</div>
                <div class="text-gray-500">Prompts</div>
            </div>
            <div class="bg-gray-50 rounded p-3 text-center">
                {% set review_count = [] %}
                {% for f in state.focuses %}
                    {% for p in f.prompts %}
                        {% if p.needs_review %}
                            {% if review_count.append(1) %}{% endif %}
                        {% endif %}
                    {% endfor %}
                {% endfor %}
                <div class="text-2xl font-bold">{{ review_count | length }}</div>
                <div class="text-gray-500">Needs Review</div>
            </div>
        </div>

        <div class="mt-4 flex gap-3">
            <a href="/pipeline" class="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 text-sm">Continue Pipeline</a>
        </div>
    </div>

    {% if state.focuses %}
    <!-- Focus list -->
    <div class="bg-white rounded-lg border border-gray-200 p-6">
        <h3 class="font-semibold mb-3">Focuses</h3>
        <div class="space-y-2">
            {% for focus in state.focuses %}
            <div class="flex items-center justify-between text-sm py-2 border-b border-gray-100 last:border-0">
                <div>
                    <span class="font-medium">{{ focus.name }}</span>
                    <span class="text-gray-400 ml-2">{{ focus.priority }}</span>
                </div>
                <div class="text-gray-500">
                    {{ focus.prompts | length }} prompts
                </div>
            </div>
            {% endfor %}
        </div>
    </div>
    {% endif %}

    {% else %}
    <!-- No project -->
    <div class="bg-white rounded-lg border border-gray-200 p-6 text-center">
        <p class="text-gray-500 mb-4">No project found. Create one to get started.</p>
        <a href="/init" class="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 text-sm">New Project</a>
    </div>
    {% endif %}
</div>
{% endblock %}
```

- [ ] **Step 2: Commit**

```bash
git add fp/web/templates/index.html
git commit -m "feat(web): add dashboard template"
```

---

### Task 8: Create Init Form Template

**Files:**
- Create: `fp/web/templates/init.html`

**Interfaces:**
- Consumes: None
- Produces: Brand setup form, POSTs to `/api/init`

- [ ] **Step 1: Write init.html**

```html
{% extends "base.html" %}
{% block title %}New Project — Focus Prompt{% endblock %}
{% block content %}
<div class="max-w-xl">
    <h1 class="text-2xl font-bold mb-6">New Project</h1>

    <form hx-post="/api/init" hx-target="#init-result" hx-indicator="#init-spinner" class="space-y-4 bg-white rounded-lg border border-gray-200 p-6">
        <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Brand Name *</label>
            <input type="text" name="name" required class="w-full border border-gray-300 rounded px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500">
        </div>

        <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Description</label>
            <textarea name="description" rows="2" class="w-full border border-gray-300 rounded px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"></textarea>
        </div>

        <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Website</label>
            <input type="url" name="website" placeholder="https://example.com" class="w-full border border-gray-300 rounded px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500">
        </div>

        <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Service Categories (comma-separated)</label>
            <input type="text" name="services" placeholder="desain, programming, copywriting" class="w-full border border-gray-300 rounded px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500">
        </div>

        <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Competitors (comma-separated)</label>
            <input type="text" name="competitors" placeholder="Fastwork, Fiverr" class="w-full border border-gray-300 rounded px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500">
        </div>

        <div class="grid grid-cols-2 gap-4">
            <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">Prompt Mode</label>
                <select name="mode" class="w-full border border-gray-300 rounded px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500">
                    <option value="unbranded">Unbranded</option>
                    <option value="branded">Branded</option>
                    <option value="both">Both</option>
                </select>
            </div>
            <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">Language</label>
                <select name="language" class="w-full border border-gray-300 rounded px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500">
                    <option value="id">Indonesian</option>
                    <option value="en">English</option>
                    <option value="mix">Mixed</option>
                </select>
            </div>
        </div>

        <div class="flex items-center gap-3 pt-2">
            <button type="submit" class="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 text-sm">Create Project</button>
            <span id="init-spinner" class="htmx-indicator text-sm text-gray-500">Creating...</span>
        </div>
    </form>

    <div id="init-result" class="mt-4"></div>
</div>
{% endblock %}
```

- [ ] **Step 2: Commit**

```bash
git add fp/web/templates/init.html
git commit -m "feat(web): add brand setup form template"
```

---

### Task 9: Create Pipeline Template

**Files:**
- Create: `fp/web/templates/pipeline.html`

**Interfaces:**
- Consumes: `state` (ProjectState) from page route
- Produces: Tabbed pipeline view with HTMX partial loading

- [ ] **Step 1: Write pipeline.html**

```html
{% extends "base.html" %}
{% block title %}Pipeline — Focus Prompt{% endblock %}
{% block content %}
<div class="space-y-6">
    <h1 class="text-2xl font-bold">Pipeline</h1>

    <!-- Tab bar -->
    <div class="flex border-b border-gray-200">
        <button class="px-4 py-2 text-sm font-medium border-b-2 border-blue-600 text-blue-600" hx-get="/api/pipeline/research" hx-target="#pipeline-content" hx-indicator="#pipeline-spinner">Research</button>
        <button class="px-4 py-2 text-sm font-medium border-b-2 border-transparent text-gray-500 hover:text-gray-700" hx-get="/api/pipeline/discover" hx-target="#pipeline-content" hx-indicator="#pipeline-spinner">Discover</button>
        <button class="px-4 py-2 text-sm font-medium border-b-2 border-transparent text-gray-500 hover:text-gray-700" hx-get="/api/pipeline/generate" hx-target="#pipeline-content" hx-indicator="#pipeline-spinner">Generate</button>
        <button class="px-4 py-2 text-sm font-medium border-b-2 border-transparent text-gray-500 hover:text-gray-700" hx-get="/api/pipeline/score" hx-target="#pipeline-content" hx-indicator="#pipeline-spinner">Score</button>
        <button class="px-4 py-2 text-sm font-medium border-b-2 border-transparent text-gray-500 hover:text-gray-700" hx-get="/api/pipeline/export" hx-target="#pipeline-content" hx-indicator="#pipeline-spinner">Export</button>
    </div>

    <!-- Content area -->
    <div id="pipeline-content" class="bg-white rounded-lg border border-gray-200 p-6">
        <span id="pipeline-spinner" class="htmx-indicator text-sm text-gray-500">Loading...</span>
        <p class="text-gray-500 text-sm">Select a step above to begin.</p>
    </div>
</div>
{% endblock %}
```

- [ ] **Step 2: Commit**

```bash
git add fp/web/templates/pipeline.html
git commit -m "feat(web): add pipeline template with tab navigation"
```

---

### Task 10: Create Settings Template

**Files:**
- Create: `fp/web/templates/settings.html`

**Interfaces:**
- Consumes: `config` (dict) from page route
- Produces: Settings form, saves to `.env`

- [ ] **Step 1: Write settings.html**

```html
{% extends "base.html" %}
{% block title %}Settings — Focus Prompt{% endblock %}
{% block content %}
<div class="max-w-xl">
    <h1 class="text-2xl font-bold mb-6">Settings</h1>

    <form hx-post="/api/settings" hx-target="#settings-result" hx-indicator="#settings-spinner" class="space-y-4 bg-white rounded-lg border border-gray-200 p-6">
        <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Provider</label>
            <select name="provider" id="provider-select" class="w-full border border-gray-300 rounded px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" onchange="updateModelPlaceholder()">
                <option value="openai">OpenAI</option>
                <option value="minimax" {{ 'selected' if 'MINIMAX' in config else '' }}>MiniMax (Singapore)</option>
                <option value="deepseek">DeepSeek</option>
                <option value="dashscope">Qwen/Alibaba</option>
                <option value="xiaomi_mimo">MiMo (Singapore)</option>
                <option value="zai">Zhipu/GLM</option>
                <option value="moonshot">Moonshot/Kimi</option>
                <option value="volcengine">ByteDance/Doubao</option>
                <option value="tencent">Tencent/Hunyuan</option>
            </select>
        </div>

        <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Model</label>
            <input type="text" name="model" value="{{ config.get('FP_MODEL', '') }}" placeholder="e.g. minimax/MiniMax-M2.7" class="w-full border border-gray-300 rounded px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500">
        </div>

        <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">API Key</label>
            <input type="password" name="api_key" value="" placeholder="Enter API key" class="w-full border border-gray-300 rounded px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500">
            {% for key, val in config.items() %}
                {% if key.endswith('_API_KEY') and val %}
                <p class="text-xs text-green-600 mt-1">✓ {{ key }} is set</p>
                {% endif %}
            {% endfor %}
        </div>

        <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Custom Endpoint (optional)</label>
            <input type="url" name="api_base" value="" placeholder="https://api.example.com/v1" class="w-full border border-gray-300 rounded px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500">
        </div>

        <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">EXA API Key (for web search)</label>
            <input type="password" name="exa_key" value="" placeholder="Enter EXA API key" class="w-full border border-gray-300 rounded px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500">
            {% if config.get('EXA_API_KEY') %}
            <p class="text-xs text-green-600 mt-1">✓ EXA_API_KEY is set</p>
            {% endif %}
        </div>

        <div class="flex items-center gap-3 pt-2">
            <button type="submit" class="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 text-sm">Save Settings</button>
            <span id="settings-spinner" class="htmx-indicator text-sm text-gray-500">Saving...</span>
        </div>
    </form>

    <div id="settings-result" class="mt-4"></div>
</div>

<script>
function updateModelPlaceholder() {
    const models = {
        'openai': 'gpt-4o-mini',
        'minimax': 'minimax/MiniMax-M2.7',
        'deepseek': 'deepseek/deepseek-chat',
        'dashscope': 'dashscope/qwen-max',
        'xiaomi_mimo': 'xiaomi_mimo/MiMo-7B-RL',
        'zai': 'zai/glm-4.7',
        'moonshot': 'moonshot/moonshot-v1-8k',
        'volcengine': 'volcengine/doubao-seed-1.6',
        'tencent': 'tencent/deepseek-v4-pro'
    };
    const select = document.getElementById('provider-select');
    const input = document.querySelector('input[name="model"]');
    input.placeholder = models[select.value] || 'model-name';
}
</script>
{% endblock %}
```

- [ ] **Step 2: Commit**

```bash
git add fp/web/templates/settings.html
git commit -m "feat(web): add settings template"
```

---

### Task 11: Create Pipeline HTMX Routes

**Files:**
- Create: `fp/web/routes/pipeline.py`

**Interfaces:**
- Consumes: `fp.web.deps.get_state`, `fp.web.deps.save_state`, `fp.research.web.research_queries`, `fp.enrichment.problems.*`, `fp.generate.focuses.generate_focuses`, `fp.generate.prompts.generate_all_prompts`, `fp.scoring.scorer.score_all`, `fp.output.export.*`
- Produces: GET `/api/pipeline/{step}`, POST `/api/{action}`

- [ ] **Step 1: Write pipeline.py**

```python
"""HTMX partial routes for pipeline steps."""
from __future__ import annotations

import asyncio
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


@router.get("/pipeline/research", response_class=HTMLResponse)
async def research_tab(request: Request):
    """Research tab partial."""
    templates = request.app.state.templates
    state = get_state()
    return templates.TemplateResponse("partials/research.html", {"request": request, "state": state})


@router.get("/pipeline/discover", response_class=HTMLResponse)
async def discover_tab(request: Request):
    """Discover tab partial."""
    templates = request.app.state.templates
    state = get_state()
    return templates.TemplateResponse("partials/discover.html", {"request": request, "state": state})


@router.get("/pipeline/generate", response_class=HTMLResponse)
async def generate_tab(request: Request):
    """Generate tab partial."""
    templates = request.app.state.templates
    state = get_state()
    return templates.TemplateResponse("partials/generate.html", {"request": request, "state": state})


@router.get("/pipeline/score", response_class=HTMLResponse)
async def score_tab(request: Request):
    """Score tab partial."""
    templates = request.app.state.templates
    state = get_state()
    return templates.TemplateResponse("partials/score.html", {"request": request, "state": state})


@router.get("/pipeline/export", response_class=HTMLResponse)
async def export_tab(request: Request):
    """Export tab partial."""
    templates = request.app.state.templates
    state = get_state()
    return templates.TemplateResponse("partials/export.html", {"request": request, "state": state})


# ─── Action Routes ────────────────────────────────────────────────────────────


@router.post("/research", response_class=HTMLResponse)
async def run_research(request: Request, extra: str = Form("")):
    """Run research step."""
    templates = request.app.state.templates
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
    templates = request.app.state.templates
    state = get_state()
    if not state:
        return HTMLResponse('<p class="text-red-600">No project found.</p>')

    brand = state.config.brand
    try:
        web_data = getattr(state, 'web_data', None)
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
        items = "".join(f'<li class="text-sm"><strong>{f.name}</strong> — {f.signal_count} signals</li>' for f in focuses)
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
    templates = request.app.state.templates
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
    templates = request.app.state.templates
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
    templates = request.app.state.templates
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
```

- [ ] **Step 2: Create partials directory and partial templates**

```bash
mkdir -p fp/web/templates/partials
```

Create `fp/web/templates/partials/research.html`:

```html
<div class="space-y-4">
    <h3 class="font-semibold">Research</h3>
    <p class="text-sm text-gray-500">Fetch real user queries from Google Autocomplete.</p>

    <form hx-post="/api/research" hx-target="#research-result" hx-indicator="#research-spinner">
        <div class="mb-3">
            <label class="block text-sm font-medium text-gray-700 mb-1">Extra seed queries (optional, comma-separated)</label>
            <input type="text" name="extra" placeholder="seed1, seed2" class="w-full border border-gray-300 rounded px-3 py-2 text-sm">
        </div>
        <div class="flex items-center gap-3">
            <button type="submit" class="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 text-sm">Run Research</button>
            <span id="research-spinner" class="htmx-indicator text-sm text-gray-500">Running...</span>
        </div>
    </form>

    <div id="research-result"></div>
</div>
```

Create `fp/web/templates/partials/discover.html`:

```html
<div class="space-y-4">
    <h3 class="font-semibold">Discover</h3>
    <p class="text-sm text-gray-500">Discover problems and generate focus clusters from LLM + web signals.</p>

    <form hx-post="/api/discover" hx-target="#discover-result" hx-indicator="#discover-spinner">
        <div class="flex items-center gap-3">
            <button type="submit" class="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 text-sm">Run Discovery</button>
            <span id="discover-spinner" class="htmx-indicator text-sm text-gray-500">Running...</span>
        </div>
    </form>

    <div id="discover-result"></div>
</div>
```

Create `fp/web/templates/partials/generate.html`:

```html
<div class="space-y-4">
    <h3 class="font-semibold">Generate Prompts</h3>
    <p class="text-sm text-gray-500">Generate prompt variants for each focus (unbranded-first).</p>

    <form hx-post="/api/generate" hx-target="#generate-result" hx-indicator="#generate-spinner">
        <div class="flex items-center gap-3">
            <button type="submit" class="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 text-sm">Generate Prompts</button>
            <span id="generate-spinner" class="htmx-indicator text-sm text-gray-500">Running...</span>
        </div>
    </form>

    <div id="generate-result"></div>
</div>
```

Create `fp/web/templates/partials/score.html`:

```html
<div class="space-y-4">
    <h3 class="font-semibold">Score</h3>
    <p class="text-sm text-gray-500">Score all prompts for brand relevance and mention likelihood.</p>

    <form hx-post="/api/score" hx-target="#score-result" hx-indicator="#score-spinner">
        <div class="flex items-center gap-3">
            <button type="submit" class="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 text-sm">Run Scoring</button>
            <span id="score-spinner" class="htmx-indicator text-sm text-gray-500">Running...</span>
        </div>
    </form>

    <div id="score-result"></div>
</div>
```

Create `fp/web/templates/partials/export.html`:

```html
<div class="space-y-4">
    <h3 class="font-semibold">Export</h3>
    <p class="text-sm text-gray-500">Export your project data.</p>

    <form hx-post="/api/export" hx-target="#export-result" hx-indicator="#export-spinner">
        <div class="mb-3">
            <label class="block text-sm font-medium text-gray-700 mb-1">Format</label>
            <select name="fmt" class="border border-gray-300 rounded px-3 py-2 text-sm">
                <option value="json">JSON</option>
                <option value="csv">CSV</option>
            </select>
        </div>
        <div class="flex items-center gap-3">
            <button type="submit" class="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 text-sm">Export</button>
            <span id="export-spinner" class="htmx-indicator text-sm text-gray-500">Exporting...</span>
        </div>
    </form>

    <div id="export-result"></div>
</div>
```

- [ ] **Step 3: Commit**

```bash
git add fp/web/routes/pipeline.py fp/web/templates/partials/
git commit -m "feat(web): add pipeline routes and partial templates"
```

---

### Task 12: Create Settings Route

**Files:**
- Create: `fp/web/routes/settings.py`

**Interfaces:**
- Consumes: `fp.config.save_user_config`
- Produces: POST `/api/settings`

- [ ] **Step 1: Write settings.py**

```python
"""Settings API route."""
from __future__ import annotations

import os
from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse

from fp.config import save_user_config, load_user_config

router = APIRouter()

PROVIDER_MAP = {
    "openai": {"model": "gpt-4o-mini", "env_key": "OPENAI_API_KEY"},
    "minimax": {"model": "minimax/MiniMax-M2.7", "env_key": "MINIMAX_API_KEY", "base": "https://api.minimax.io/v1"},
    "deepseek": {"model": "deepseek/deepseek-chat", "env_key": "DEEPSEEK_API_KEY"},
    "dashscope": {"model": "dashscope/qwen-max", "env_key": "DASHSCOPE_API_KEY"},
    "xiaomi_mimo": {"model": "xiaomi_mimo/MiMo-7B-RL", "env_key": "XIAOMI_MIMO_API_KEY", "base": "https://api.xiaomi.com/v1"},
    "zai": {"model": "zai/glm-4.7", "env_key": "ZAI_API_KEY"},
    "moonshot": {"model": "moonshot/moonshot-v1-8k", "env_key": "MOONSHOT_API_KEY"},
    "volcengine": {"model": "volcengine/doubao-seed-1.6", "env_key": "VOLCENGINE_API_KEY"},
    "tencent": {"model": "tencent/deepseek-v4-pro", "env_key": "TENCENT_API_KEY"},
}


@router.post("/settings", response_class=HTMLResponse)
async def save_settings(
    provider: str = Form(""),
    model: str = Form(""),
    api_key: str = Form(""),
    api_base: str = Form(""),
    exa_key: str = Form(""),
):
    """Save settings to .env file."""
    settings = {}

    if model:
        settings["FP_MODEL"] = model

    if provider and provider in PROVIDER_MAP:
        info = PROVIDER_MAP[provider]
        if api_key:
            settings[info["env_key"]] = api_key
        if not model:
            settings["FP_MODEL"] = info["model"]
        if api_base:
            base_key = info["env_key"].replace("_API_KEY", "_API_BASE")
            settings[base_key] = api_base
        elif "base" in info and not api_base:
            base_key = info["env_key"].replace("_API_KEY", "_API_BASE")
            settings[base_key] = info["base"]
    elif api_key:
        settings["OPENAI_API_KEY"] = api_key

    if exa_key:
        settings["EXA_API_KEY"] = exa_key

    if settings:
        save_user_config(settings)
        # Reload into current env
        for k, v in settings.items():
            os.environ[k] = v

    return HTMLResponse(f'''
        <div class="p-3 bg-green-50 border border-green-200 rounded text-green-700 text-sm">
            ✓ Settings saved. Model: {settings.get("FP_MODEL", "unchanged")}
        </div>
    ''')
```

- [ ] **Step 2: Commit**

```bash
git add fp/web/routes/settings.py
git commit -m "feat(web): add settings API route"
```

---

### Task 13: Add `fp web` CLI Command

**Files:**
- Modify: `fp/cli.py:476-477` (add web command before `if __name__`)

**Interfaces:**
- Consumes: `fp.web.app.create_app`
- Produces: `fp web` CLI command

- [ ] **Step 1: Add web command to cli.py**

Add before `if __name__ == "__main__":`:

```python
@app.command()
def web(
    host: str = typer.Option("127.0.0.1", "--host", "-h", help="Host to bind"),
    port: int = typer.Option(8000, "--port", "-p", help="Port to bind"),
):
    """Start the web UI."""
    import uvicorn
    from fp.web.app import create_app
    console.print(f"\n[bold green]✓[/] Starting web UI at [cyan]http://{host}:{port}[/]")
    console.print("  Press Ctrl+C to stop\n")
    uvicorn.run(create_app(), host=host, port=port)
```

- [ ] **Step 2: Commit**

```bash
git add fp/cli.py
git commit -m "feat(web): add fp web CLI command"
```

---

### Task 14: Install and Smoke Test

**Files:**
- None (verification only)

**Interfaces:**
- Consumes: All previous tasks
- Produces: Working web UI

- [ ] **Step 1: Install dependencies**

```bash
pip install -e .
```

- [ ] **Step 2: Start web server**

```bash
fp web &
```

- [ ] **Step 3: Test dashboard loads**

```bash
curl -s http://127.0.0.1:8000/ | head -5
```

Expected: HTML response with "Dashboard" title

- [ ] **Step 4: Test init page**

```bash
curl -s http://127.0.0.1:8000/init | head -5
```

Expected: HTML form with "Brand Name" field

- [ ] **Step 5: Test settings page**

```bash
curl -s http://127.0.0.1:8000/settings | head -5
```

Expected: HTML form with "Provider" dropdown

- [ ] **Step 6: Stop server and cleanup**

```bash
kill %1 2>/dev/null; true
```

- [ ] **Step 7: Final commit**

```bash
git add -A
git commit -m "feat(web): complete web UI — fp web command, FastAPI + htmx"
```
