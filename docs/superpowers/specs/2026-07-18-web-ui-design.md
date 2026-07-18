# Focus Prompt Web UI — Design Spec

**Date:** 2026-07-18
**Status:** Approved
**Scope:** Full pipeline web interface (init → research → discover → generate → score → export)

## Overview

Convert the focus-prompt CLI into a local web UI using FastAPI + htmx. The backend reuses all existing logic from `fp/` — no duplication. Users access the interface at `localhost:8000` via `fp web` command.

## Tech Stack

- **Backend:** FastAPI (async, Jinja2 templates)
- **Frontend:** htmx + Tailwind CSS (CDN)
- **State:** Existing `fp-project.json`
- **Config:** `.env` file + Settings page in UI
- **Entry:** `fp web` CLI command → uvicorn

## Architecture

```
fp/web/
├── __init__.py
├── app.py              # FastAPI app factory, startup/shutdown
├── deps.py             # Shared: get_state(), get_config()
├── routes/
│   ├── __init__.py
│   ├── pages.py        # HTML page routes (GET /, /init, /pipeline, /settings)
│   ├── pipeline.py     # HTMX partial routes (POST /api/research, /api/discover, etc.)
│   └── settings.py     # Settings API (GET/POST /api/settings)
└── templates/
    ├── base.html       # Layout: nav, Tailwind CDN, htmx script
    ├── index.html      # Dashboard
    ├── init.html       # Brand setup form
    ├── pipeline.html   # Pipeline view (tabs + content area)
    └── settings.html   # API config
```

## Pages

### `/` — Dashboard
- Project status (loaded/not loaded)
- Focus count, prompt count
- Quick actions: "New Project" → `/init`, "Continue Pipeline" → `/pipeline`
- Link to Settings

### `/init` — Brand Setup
- Form fields: name, description, website, service_categories (comma-separated), competitors (comma-separated), prompt_mode (branded/unbranded), language (id/en/mix)
- POST → calls `fp_init()` from `fp/server.py` → saves to `fp-project.json` → redirect to `/pipeline`

### `/pipeline` — Main Pipeline
- Tab bar: Research → Discover → Generate → Score → Export
- Each tab loads content via htmx `hx-get`
- Steps run sequentially but tabs are clickable
- Each step shows status (pending/running/done/error)

**Tab content (HTMX partials):**
- **Research:** POST `/api/research` → calls `fp_research()` → shows autocomplete results + query count
- **Discover:** POST `/api/discover` → calls `fp_discover()` → shows discovered focuses with scores
- **Generate:** POST `/api/generate` → calls `fp_generate_prompts()` → shows generated prompts
- **Score:** POST `/api/score` → calls `fp_score()` → shows scored prompts with rankings
- **Export:** POST `/api/export` → calls `fp_export()` → download links (JSON, CSV)

### `/settings` — Configuration
- Provider dropdown (OpenAI, MiniMax, DeepSeek, Qwen, etc.)
- Model input (with presets)
- API key input (masked)
- Custom endpoint input (optional)
- Save → writes to `.env` file
- Load current values from env on page load

## HTMX Pattern

```html
<!-- Example: Research tab -->
<button hx-post="/api/research" hx-target="#research-content" hx-indicator="#research-spinner">
  Run Research
</button>
<div id="research-content"></div>
<div id="research-spinner" class="htmx-indicator">Loading...</div>
```

## Backend Integration

All routes call existing functions from `fp/`:
- `fp/server.py` — `fp_init()`, `fp_research()`, `fp_discover()`, `fp_generate_prompts()`, `fp_score()`, `fp_export()`, `fp_status()`
- `fp/config.py` — `load_user_config()`, `save_user_config()`, `get_current_config()`
- `fp/models.py` — `ProjectState`, `Brand`, `Focus`, `ScoredPrompt`

No business logic duplication. Web routes are thin wrappers.

## CLI Command

Add to `fp/cli.py`:
```python
@app.command()
def web(host: str = "127.0.0.1", port: int = 8000):
    """Start the web UI."""
    import uvicorn
    from fp.web.app import create_app
    uvicorn.run(create_app(), host=host, port=port)
```

## Dependencies

Add to `pyproject.toml`:
```
fastapi>=0.115.0
uvicorn[standard]>=0.30.0
jinja2>=3.1.0
python-multipart>=0.0.9
```

## Error Handling

- API errors return 200 with error message in HTML partial (htmx pattern)
- Validation errors shown inline on forms
- Missing project state → redirect to `/init`

## Non-Goals

- No authentication (local only)
- No WebSocket/real-time updates (htmx polling acceptable)
- No database (file-based state)
- No mobile responsiveness (desktop-first)
