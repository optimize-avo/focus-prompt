# Design: SQLite Database + CRUD for Focus Prompt

## Problem

Current state persistence uses a single `fp-project.json` file — only one project at a time, no CRUD for focuses/prompts, no way to switch between projects.

## Goal

Add SQLite database for multi-project support with full CRUD (add/edit/delete) for focuses and prompts, all managed via Web UI.

## Decisions

- **Database:** SQLite via Python stdlib `sqlite3` (zero new dependencies)
- **Interface:** Web UI only (HTMX + FastAPI), CLI deprecated
- **Migration:** Auto-import existing `fp-project.json` on first run
- **Database location:** `~/.config/fp/focus_prompt.db`

---

## Database Schema

### `settings` table
```sql
CREATE TABLE settings (
    key   TEXT PRIMARY KEY,
    value TEXT NOT NULL
);
```
Stores `active_project_id` as a setting.

### `projects` table
```sql
CREATE TABLE projects (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT NOT NULL,
    description TEXT DEFAULT '',
    website     TEXT DEFAULT '',
    services    TEXT DEFAULT '[]',    -- JSON array
    competitors TEXT DEFAULT '[]',    -- JSON array
    prompt_mode TEXT DEFAULT 'unbranded',
    language    TEXT DEFAULT 'id',
    created_at  TEXT NOT NULL,
    updated_at  TEXT NOT NULL
);
```

### `focuses` table
```sql
CREATE TABLE focuses (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id          INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    name                TEXT NOT NULL,
    description         TEXT DEFAULT '',
    lens                TEXT DEFAULT 'problem',
    priority            TEXT DEFAULT 'medium',
    signals             TEXT DEFAULT '[]',    -- JSON array
    signal_count        INTEGER DEFAULT 0,
    service_match_score REAL DEFAULT 0.0
);
CREATE INDEX idx_focuses_project ON focuses(project_id);
```

### `prompts` table
```sql
CREATE TABLE prompts (
    id                 INTEGER PRIMARY KEY AUTOINCREMENT,
    focus_id           INTEGER NOT NULL REFERENCES focuses(id) ON DELETE CASCADE,
    text               TEXT NOT NULL,
    intent             TEXT DEFAULT 'info',
    mode               TEXT DEFAULT 'unbranded',
    language           TEXT DEFAULT 'id',
    service_match      REAL DEFAULT 0.0,
    mention_likelihood REAL DEFAULT 0.0,
    overall_score      REAL DEFAULT 0.0,
    needs_review       INTEGER DEFAULT 0
);
CREATE INDEX idx_prompts_focus ON prompts(focus_id);
```

### `step_selections` table
```sql
CREATE TABLE step_selections (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    step       TEXT NOT NULL,
    selections TEXT NOT NULL DEFAULT '[]',  -- JSON array of IDs
    UNIQUE(project_id, step)
);
```

### `web_data` table
```sql
CREATE TABLE web_data (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL UNIQUE REFERENCES projects(id) ON DELETE CASCADE,
    data       TEXT NOT NULL,    -- JSON blob
    updated_at TEXT NOT NULL
);
```

### Relationships
```
projects 1:N focuses 1:N prompts
projects 1:1 web_data
```

---

## API Routes

All routes under `/api/` prefix.

### Projects
| Method | Route | Action |
|--------|-------|--------|
| `GET` | `/projects` | List all projects |
| `POST` | `/projects` | Create new project |
| `GET` | `/projects/{id}` | Get project detail + focuses |
| `PUT` | `/projects/{id}` | Update project config |
| `DELETE` | `/projects/{id}` | Delete project (cascade) |
| `POST` | `/projects/{id}/activate` | Set as active project |

### Focuses
| Method | Route | Action |
|--------|-------|--------|
| `POST` | `/projects/{id}/focuses` | Add focus |
| `PUT` | `/projects/{id}/focuses/{fid}` | Edit focus |
| `DELETE` | `/projects/{id}/focuses/{fid}` | Delete focus (cascade) |

### Prompts
| Method | Route | Action |
|--------|-------|--------|
| `POST` | `/projects/{id}/focuses/{fid}/prompts` | Add prompt |
| `PUT` | `/projects/{id}/focuses/{fid}/prompts/{pid}` | Edit prompt |
| `DELETE` | `/projects/{id}/focuses/{fid}/prompts/{pid}` | Delete prompt |

### Key Behaviors
- Only 1 active project at a time (stored in `settings` table)
- Delete project → cascade deletes focuses, prompts, web_data
- Delete focus → cascade deletes prompts
- JSON array fields (services, competitors, signals) stored as JSON strings, parsed in Python

---

## Web UI Pages

### 1. Project List Page (`/`)
- Card grid of all projects
- Each card: brand name, focus count, prompt count, created date
- Click card → activate + redirect to `/pipeline`
- "New Project" button → `/init`
- Edit/delete icons per card (hover to reveal)

### 2. Project Manage Page (`/projects/{id}`)
- Header: brand name + config (editable inline)
- Main area: **Focuses table**
  - Columns: Name, Priority, Service Match, Prompts Count, Actions
  - Inline edit: click name → input field
  - Add focus button → form/modal
  - Delete button → confirmation dialog
  - Expand row → view/edit prompts sub-table

- **Prompts sub-table** (per focus):
  - Columns: Text (truncated), Intent, Mode, Scores, Actions
  - Inline edit: click text → textarea
  - Add prompt button → form/modal
  - Delete button → confirmation dialog

### 3. Init Page (`/init`)
- Same as current, but saves to SQLite instead of JSON

### 4. Pipeline Page (`/pipeline`)
- Same as current, but reads from SQLite (active project)

### 5. Navigation Update
```
Dashboard (project list) | Pipeline (active project) | Settings
```

---

## Data Layer (`fp/db.py`)

### Functions
```python
def init_db() -> None
    """Create tables if they don't exist."""

def get_db() -> sqlite3.Connection
    """Get database connection with row_factory."""

def create_project(name, description, website, services, competitors, mode, lang) -> int
def get_project(project_id) -> dict | None
def list_projects() -> list[dict]
def update_project(project_id, **fields) -> None
def delete_project(project_id) -> None
def set_active_project(project_id) -> None
def get_active_project_id() -> int | None

def create_focus(project_id, name, description, lens, priority, signals, service_match_score) -> int
def get_focuses(project_id) -> list[dict]
def update_focus(focus_id, **fields) -> None
def delete_focus(focus_id) -> None

def create_prompt(focus_id, text, intent, mode, language, service_match, mention_likelihood, overall_score, needs_review) -> int
def get_prompts(focus_id) -> list[dict]
def update_prompt(prompt_id, **fields) -> None
def delete_prompt(prompt_id) -> None

def save_web_data(project_id, data: dict) -> None
def get_web_data(project_id) -> dict | None
```

### Conversion Helpers
```python
def project_row_to_config(row) -> ProjectConfig
    """Convert DB row → Pydantic ProjectConfig."""

def project_row_to_state(row, focuses, web_data) -> ProjectState
    """Convert DB row + relations → full ProjectState."""
```

---

## Migration Strategy

### Auto-migration on first run
When `fp web` starts:
1. Call `init_db()` — create tables if needed
2. Check if `fp-project.json` exists in current directory
3. If exists:
   a. Parse JSON into `ProjectState`
   b. Insert into SQLite (project → focuses → prompts → web_data)
   c. Set as active project
   d. Rename `fp-project.json` → `fp-project.json.bak`
4. If no active project in DB, first project is auto-activated

### `deps.py` updates
```python
def get_state() -> ProjectState | None:
    """Load active project from SQLite."""
    project_id = get_active_project_id()
    if not project_id:
        return None
    # ... load from DB

def save_state(state: ProjectState) -> None:
    """Save to SQLite (update active project)."""
    # ... write to DB
```

---

## File Structure

```
fp/
├── db.py                    ← NEW: database layer
├── web/routes/
│   ├── projects.py          ← NEW: project CRUD routes
│   └── manage.py            ← NEW: focus/prompt CRUD routes
├── web/templates/
│   ├── projects.html        ← NEW: project list page
│   └── manage.html          ← NEW: project detail/manage page
├── web/deps.py              ← MODIFIED: read/write from SQLite
├── web/routes/pages.py      ← MODIFIED: dashboard shows project list
└── web/routes/pipeline.py   ← MODIFIED: reads active project from SQLite
```

---

## Backward Compatibility

- **CLI:** Remains functional with JSON files — no changes needed
- **MCP Server:** Remains functional with JSON — no changes needed
- **Web UI:** Fully migrated to SQLite
- **No breaking changes** for existing users

---

## Implementation Order

1. `fp/db.py` — database layer + init + CRUD helpers
2. Migration logic — auto-import from JSON
3. `fp/web/routes/projects.py` — project CRUD API routes
4. `fp/web/routes/manage.py` — focus/prompt CRUD API routes
5. `fp/web/templates/projects.html` — project list page
6. `fp/web/templates/manage.html` — project detail/manage page
7. Update `deps.py` — switch to SQLite reads/writes
8. Update `pages.py` — dashboard → project list
9. Update `base.html` — navigation
10. Update `pipeline.py` — read from SQLite
11. Tests — unit tests for db.py, integration tests for routes
