# SQLite Database + CRUD Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add SQLite database for multi-project support with full CRUD (add/edit/delete) for focuses and prompts via Web UI.

**Architecture:** New `fp/db.py` module with raw `sqlite3` handles all database operations. New routes in `fp/web/routes/projects.py` and `fp/web/routes/manage.py` expose CRUD API. New HTML templates for project list and manage pages. Existing `deps.py` updated to read/write from SQLite instead of JSON.

**Tech Stack:** Python 3.11+, sqlite3 (stdlib), FastAPI, HTMX, Jinja2, Pydantic v2

## Global Constraints

- Python >=3.11, sqlite3 from stdlib (zero new dependencies)
- Pydantic v2 models for data validation
- HTMX for UI interactions (no JS framework)
- Tailwind CSS for styling (already in use)
- JSON arrays stored as TEXT in SQLite, parsed in Python
- Cascade deletes: project → focuses → prompts, project → web_data
- Only 1 active project at a time (stored in `settings` table)

---

## File Map

| File | Action | Responsibility |
|------|--------|---------------|
| `fp/db.py` | CREATE | Database layer — init, CRUD helpers, conversion functions |
| `fp/web/routes/projects.py` | CREATE | Project CRUD API routes |
| `fp/web/routes/manage.py` | CREATE | Focus/prompt CRUD API routes |
| `fp/web/templates/projects.html` | CREATE | Project list page |
| `fp/web/templates/manage.html` | CREATE | Project detail/manage page |
| `fp/web/deps.py` | MODIFY | Switch from JSON to SQLite reads/writes |
| `fp/web/routes/pages.py` | MODIFY | Dashboard shows project list, import migration |
| `fp/web/routes/pipeline.py` | MODIFY | Read active project from SQLite |
| `fp/web/templates/base.html` | MODIFY | Update navigation |
| `tests/test_db.py` | CREATE | Unit tests for database layer |
| `tests/web/test_projects.py` | CREATE | Integration tests for project routes |
| `tests/web/test_manage.py` | CREATE | Integration tests for focus/prompt routes |

---

### Task 1: Database Layer — Schema & Init

**Files:**
- Create: `fp/db.py`
- Test: `tests/test_db.py`

**Interfaces:**
- Produces: `init_db()`, `get_db()`, `DB_PATH`

- [ ] **Step 1: Write failing test for init_db**

```python
# tests/test_db.py
import sqlite3
import tempfile
from pathlib import Path
from fp.db import init_db, get_db, DB_PATH


def test_init_db_creates_file(tmp_path, monkeypatch):
    """init_db creates database file and tables."""
    db_path = tmp_path / "test.db"
    monkeypatch.setattr("fp.db.DB_PATH", db_path)

    init_db()

    assert db_path.exists()
    conn = sqlite3.connect(str(db_path))
    cursor = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
    )
    tables = [row[0] for row in cursor.fetchall()]
    conn.close()

    assert "projects" in tables
    assert "focuses" in tables
    assert "prompts" in tables
    assert "web_data" in tables
    assert "step_selections" in tables
    assert "settings" in tables


def test_init_db_idempotent(tmp_path, monkeypatch):
    """init_db can be called multiple times without error."""
    db_path = tmp_path / "test.db"
    monkeypatch.setattr("fp.db.DB_PATH", db_path)

    init_db()
    init_db()  # second call should not fail


def test_get_db_returns_connection(tmp_path, monkeypatch):
    """get_db returns a working sqlite3 connection."""
    db_path = tmp_path / "test.db"
    monkeypatch.setattr("fp.db.DB_PATH", db_path)
    init_db()

    conn = get_db()
    assert isinstance(conn, sqlite3.Connection)
    conn.close()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_db.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'fp.db'`

- [ ] **Step 3: Implement db.py with init_db and get_db**

```python
# fp/db.py
"""SQLite database layer for focus-prompt."""
from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

DB_PATH = Path.home() / ".config" / "fp" / "focus_prompt.db"

_SCHEMA = """
CREATE TABLE IF NOT EXISTS settings (
    key   TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS projects (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT NOT NULL,
    description TEXT DEFAULT '',
    website     TEXT DEFAULT '',
    services    TEXT DEFAULT '[]',
    competitors TEXT DEFAULT '[]',
    prompt_mode TEXT DEFAULT 'unbranded',
    language    TEXT DEFAULT 'id',
    created_at  TEXT NOT NULL,
    updated_at  TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS focuses (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id          INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    name                TEXT NOT NULL,
    description         TEXT DEFAULT '',
    lens                TEXT DEFAULT 'problem',
    priority            TEXT DEFAULT 'medium',
    signals             TEXT DEFAULT '[]',
    signal_count        INTEGER DEFAULT 0,
    service_match_score REAL DEFAULT 0.0
);
CREATE INDEX IF NOT EXISTS idx_focuses_project ON focuses(project_id);

CREATE TABLE IF NOT EXISTS prompts (
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
CREATE INDEX IF NOT EXISTS idx_prompts_focus ON prompts(focus_id);

CREATE TABLE IF NOT EXISTS web_data (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL UNIQUE REFERENCES projects(id) ON DELETE CASCADE,
    data       TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS step_selections (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    step       TEXT NOT NULL,
    selections TEXT NOT NULL DEFAULT '[]',
    UNIQUE(project_id, step)
);
"""


def init_db(db_path: Path | None = None) -> None:
    """Create database and tables if they don't exist."""
    path = db_path or DB_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path))
    conn.execute("PRAGMA foreign_keys = ON")
    conn.executescript(_SCHEMA)
    conn.close()


def get_db(db_path: Path | None = None) -> sqlite3.Connection:
    """Get a database connection with row_factory enabled."""
    path = db_path or DB_PATH
    conn = sqlite3.connect(str(path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_db.py -v`
Expected: All 3 tests PASS

- [ ] **Step 5: Commit**

```bash
git add fp/db.py tests/test_db.py
git commit -m "feat(db): add SQLite database layer with schema and init"
```

---

### Task 2: Database Layer — Project CRUD

**Files:**
- Modify: `fp/db.py`
- Modify: `tests/test_db.py`

**Interfaces:**
- Consumes: `init_db()`, `get_db()` from Task 1
- Produces: `create_project()`, `get_project()`, `list_projects()`, `update_project()`, `delete_project()`, `set_active_project()`, `get_active_project_id()`

- [ ] **Step 1: Write failing tests for project CRUD**

```python
# append to tests/test_db.py

from fp.db import (
    create_project,
    get_project,
    list_projects,
    update_project,
    delete_project,
    set_active_project,
    get_active_project_id,
)


def _setup_db(tmp_path, monkeypatch):
    db_path = tmp_path / "test.db"
    monkeypatch.setattr("fp.db.DB_PATH", db_path)
    init_db(db_path)
    return db_path


def test_create_project(tmp_path, monkeypatch):
    _setup_db(tmp_path, monkeypatch)

    pid = create_project(
        name="Test Brand",
        description="A test",
        website="https://example.com",
        services='["design"]',
        competitors='["comp1"]',
        prompt_mode="unbranded",
        language="id",
    )

    assert pid > 0
    project = get_project(pid)
    assert project["name"] == "Test Brand"
    assert project["description"] == "A test"
    assert project["website"] == "https://example.com"


def test_list_projects(tmp_path, monkeypatch):
    _setup_db(tmp_path, monkeypatch)

    create_project(name="Brand A")
    create_project(name="Brand B")

    projects = list_projects()
    assert len(projects) == 2
    assert projects[0]["name"] == "Brand A"
    assert projects[1]["name"] == "Brand B"


def test_update_project(tmp_path, monkeypatch):
    _setup_db(tmp_path, monkeypatch)

    pid = create_project(name="Old Name")
    update_project(pid, name="New Name", description="Updated")

    project = get_project(pid)
    assert project["name"] == "New Name"
    assert project["description"] == "Updated"


def test_delete_project(tmp_path, monkeypatch):
    _setup_db(tmp_path, monkeypatch)

    pid = create_project(name="To Delete")
    delete_project(pid)

    assert get_project(pid) is None
    assert len(list_projects()) == 0


def test_active_project(tmp_path, monkeypatch):
    _setup_db(tmp_path, monkeypatch)

    pid1 = create_project(name="First")
    pid2 = create_project(name="Second")

    set_active_project(pid1)
    assert get_active_project_id() == pid1

    set_active_project(pid2)
    assert get_active_project_id() == pid2
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_db.py -v -k "project"`
Expected: FAIL with `ImportError: cannot import name 'create_project'`

- [ ] **Step 3: Implement project CRUD functions**

Append to `fp/db.py`:

```python
def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def create_project(
    name: str,
    description: str = "",
    website: str = "",
    services: str = "[]",
    competitors: str = "[]",
    prompt_mode: str = "unbranded",
    language: str = "id",
) -> int:
    """Create a new project and return its ID."""
    now = _now()
    conn = get_db()
    try:
        cursor = conn.execute(
            """INSERT INTO projects (name, description, website, services, competitors, prompt_mode, language, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (name, description, website, services, competitors, prompt_mode, language, now, now),
        )
        conn.commit()
        return cursor.lastrowid
    finally:
        conn.close()


def get_project(project_id: int) -> dict | None:
    """Get a project by ID, or None if not found."""
    conn = get_db()
    try:
        row = conn.execute("SELECT * FROM projects WHERE id = ?", (project_id,)).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def list_projects() -> list[dict]:
    """List all projects ordered by created_at desc."""
    conn = get_db()
    try:
        rows = conn.execute("SELECT * FROM projects ORDER BY created_at DESC").fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def update_project(project_id: int, **fields) -> None:
    """Update project fields. Only provided fields are updated."""
    if not fields:
        return
    fields["updated_at"] = _now()
    set_clause = ", ".join(f"{k} = ?" for k in fields)
    values = list(fields.values()) + [project_id]
    conn = get_db()
    try:
        conn.execute(f"UPDATE projects SET {set_clause} WHERE id = ?", values)
        conn.commit()
    finally:
        conn.close()


def delete_project(project_id: int) -> None:
    """Delete a project and all related data (cascade via FK)."""
    conn = get_db()
    try:
        conn.execute("DELETE FROM projects WHERE id = ?", (project_id,))
        conn.commit()
    finally:
        conn.close()


def set_active_project(project_id: int) -> None:
    """Set the active project."""
    conn = get_db()
    try:
        conn.execute(
            "INSERT OR REPLACE INTO settings (key, value) VALUES ('active_project_id', ?)",
            (str(project_id),),
        )
        conn.commit()
    finally:
        conn.close()


def get_active_project_id() -> int | None:
    """Get the active project ID, or None."""
    conn = get_db()
    try:
        row = conn.execute("SELECT value FROM settings WHERE key = 'active_project_id'").fetchone()
        return int(row["value"]) if row else None
    finally:
        conn.close()
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_db.py -v -k "project"`
Expected: All 5 project tests PASS

- [ ] **Step 5: Commit**

```bash
git add fp/db.py tests/test_db.py
git commit -m "feat(db): add project CRUD operations"
```

---

### Task 3: Database Layer — Focus CRUD

**Files:**
- Modify: `fp/db.py`
- Modify: `tests/test_db.py`

**Interfaces:**
- Consumes: `create_project()` from Task 2
- Produces: `create_focus()`, `get_focuses()`, `update_focus()`, `delete_focus()`

- [ ] **Step 1: Write failing tests for focus CRUD**

```python
# append to tests/test_db.py

from fp.db import create_focus, get_focuses, update_focus, delete_focus


def test_create_focus(tmp_path, monkeypatch):
    _setup_db(tmp_path, monkeypatch)
    pid = create_project(name="Test")

    fid = create_focus(
        project_id=pid,
        name="Focus A",
        description="Desc",
        lens="problem",
        priority="high",
        signals='["sig1"]',
        service_match_score=85.0,
    )

    assert fid > 0
    focuses = get_focuses(pid)
    assert len(focuses) == 1
    assert focuses[0]["name"] == "Focus A"
    assert focuses[0]["service_match_score"] == 85.0


def test_get_focuses_empty(tmp_path, monkeypatch):
    _setup_db(tmp_path, monkeypatch)
    pid = create_project(name="Empty")

    focuses = get_focuses(pid)
    assert focuses == []


def test_update_focus(tmp_path, monkeypatch):
    _setup_db(tmp_path, monkeypatch)
    pid = create_project(name="Test")
    fid = create_focus(project_id=pid, name="Old")

    update_focus(fid, name="New", priority="low")

    focuses = get_focuses(pid)
    assert focuses[0]["name"] == "New"
    assert focuses[0]["priority"] == "low"


def test_delete_focus(tmp_path, monkeypatch):
    _setup_db(tmp_path, monkeypatch)
    pid = create_project(name="Test")
    fid = create_focus(project_id=pid, name="ToDelete")

    delete_focus(fid)

    assert get_focuses(pid) == []


def test_delete_focus_cascades_to_prompts(tmp_path, monkeypatch):
    _setup_db(tmp_path, monkeypatch)
    from fp.db import create_prompt, get_prompts

    pid = create_project(name="Test")
    fid = create_focus(project_id=pid, name="Focus")
    create_prompt(focus_id=fid, text="prompt1")
    create_prompt(focus_id=fid, text="prompt2")

    delete_focus(fid)

    assert get_focuses(pid) == []
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_db.py -v -k "focus"`
Expected: FAIL with `ImportError: cannot import name 'create_focus'`

- [ ] **Step 3: Implement focus CRUD functions**

Append to `fp/db.py`:

```python
def create_focus(
    project_id: int,
    name: str,
    description: str = "",
    lens: str = "problem",
    priority: str = "medium",
    signals: str = "[]",
    service_match_score: float = 0.0,
) -> int:
    """Create a focus for a project and return its ID."""
    signal_count = len(json.loads(signals)) if signals else 0
    conn = get_db()
    try:
        cursor = conn.execute(
            """INSERT INTO focuses (project_id, name, description, lens, priority, signals, signal_count, service_match_score)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (project_id, name, description, lens, priority, signals, signal_count, service_match_score),
        )
        conn.commit()
        return cursor.lastrowid
    finally:
        conn.close()


def get_focuses(project_id: int) -> list[dict]:
    """Get all focuses for a project."""
    conn = get_db()
    try:
        rows = conn.execute(
            "SELECT * FROM focuses WHERE project_id = ? ORDER BY id", (project_id,)
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def update_focus(focus_id: int, **fields) -> None:
    """Update focus fields."""
    if not fields:
        return
    if "signals" in fields:
        signals = fields["signals"]
        fields["signal_count"] = len(json.loads(signals)) if isinstance(signals, str) else len(signals)
    set_clause = ", ".join(f"{k} = ?" for k in fields)
    values = list(fields.values()) + [focus_id]
    conn = get_db()
    try:
        conn.execute(f"UPDATE focuses SET {set_clause} WHERE id = ?", values)
        conn.commit()
    finally:
        conn.close()


def delete_focus(focus_id: int) -> None:
    """Delete a focus and all its prompts (cascade via FK)."""
    conn = get_db()
    try:
        conn.execute("DELETE FROM focuses WHERE id = ?", (focus_id,))
        conn.commit()
    finally:
        conn.close()
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_db.py -v -k "focus"`
Expected: All 5 focus tests PASS

- [ ] **Step 5: Commit**

```bash
git add fp/db.py tests/test_db.py
git commit -m "feat(db): add focus CRUD operations"
```

---

### Task 4: Database Layer — Prompt CRUD + Web Data

**Files:**
- Modify: `fp/db.py`
- Modify: `tests/test_db.py`

**Interfaces:**
- Consumes: `create_focus()` from Task 3
- Produces: `create_prompt()`, `get_prompts()`, `update_prompt()`, `delete_prompt()`, `save_web_data()`, `get_web_data()`, `save_step_selections()`, `get_step_selections()`

- [ ] **Step 1: Write failing tests for prompt CRUD and web_data**

```python
# append to tests/test_db.py

from fp.db import (
    create_prompt,
    get_prompts,
    update_prompt,
    delete_prompt,
    save_web_data,
    get_web_data,
    save_step_selections,
    get_step_selections,
)


def test_create_prompt(tmp_path, monkeypatch):
    _setup_db(tmp_path, monkeypatch)
    pid = create_project(name="Test")
    fid = create_focus(project_id=pid, name="Focus")

    prid = create_prompt(
        focus_id=fid,
        text="How to track AI visibility?",
        intent="how-to",
        mode="unbranded",
        language="en",
        service_match=90.0,
        mention_likelihood=70.0,
        overall_score=80.0,
        needs_review=0,
    )

    assert prid > 0
    prompts = get_prompts(fid)
    assert len(prompts) == 1
    assert prompts[0]["text"] == "How to track AI visibility?"
    assert prompts[0]["service_match"] == 90.0


def test_update_prompt(tmp_path, monkeypatch):
    _setup_db(tmp_path, monkeypatch)
    pid = create_project(name="Test")
    fid = create_focus(project_id=pid, name="Focus")
    prid = create_prompt(focus_id=fid, text="Old text")

    update_prompt(prid, text="New text", overall_score=95.0)

    prompts = get_prompts(fid)
    assert prompts[0]["text"] == "New text"
    assert prompts[0]["overall_score"] == 95.0


def test_delete_prompt(tmp_path, monkeypatch):
    _setup_db(tmp_path, monkeypatch)
    pid = create_project(name="Test")
    fid = create_focus(project_id=pid, name="Focus")
    prid = create_prompt(focus_id=fid, text="ToDelete")

    delete_prompt(prid)

    assert get_prompts(fid) == []


def test_save_get_web_data(tmp_path, monkeypatch):
    _setup_db(tmp_path, monkeypatch)
    pid = create_project(name="Test")

    data = {"autocomplete": ["q1", "q2"], "stats": {"total_queries": 2}}
    save_web_data(pid, data)

    loaded = get_web_data(pid)
    assert loaded["autocomplete"] == ["q1", "q2"]
    assert loaded["stats"]["total_queries"] == 2


def test_step_selections(tmp_path, monkeypatch):
    _setup_db(tmp_path, monkeypatch)
    pid = create_project(name="Test")

    save_step_selections(pid, "research", ["q1", "q2"])
    save_step_selections(pid, "discover", ["f1"])

    assert get_step_selections(pid, "research") == ["q1", "q2"]
    assert get_step_selections(pid, "discover") == ["f1"]
    assert get_step_selections(pid, "missing") == []


def test_delete_project_cascades_everything(tmp_path, monkeypatch):
    _setup_db(tmp_path, monkeypatch)

    pid = create_project(name="Full")
    fid = create_focus(project_id=pid, name="Focus")
    create_prompt(focus_id=fid, text="Prompt")
    save_web_data(pid, {"data": 1})
    save_step_selections(pid, "research", ["q1"])

    delete_project(pid)

    assert get_project(pid) is None
    assert get_focuses(pid) == []
    assert get_web_data(pid) is None
    assert get_step_selections(pid, "research") == []
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_db.py -v -k "prompt or web_data or step_sel or cascade"`
Expected: FAIL with `ImportError`

- [ ] **Step 3: Implement prompt CRUD, web_data, and step_selections**

Append to `fp/db.py`:

```python
def create_prompt(
    focus_id: int,
    text: str,
    intent: str = "info",
    mode: str = "unbranded",
    language: str = "id",
    service_match: float = 0.0,
    mention_likelihood: float = 0.0,
    overall_score: float = 0.0,
    needs_review: int = 0,
) -> int:
    """Create a prompt for a focus and return its ID."""
    conn = get_db()
    try:
        cursor = conn.execute(
            """INSERT INTO prompts (focus_id, text, intent, mode, language, service_match, mention_likelihood, overall_score, needs_review)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (focus_id, text, intent, mode, language, service_match, mention_likelihood, overall_score, needs_review),
        )
        conn.commit()
        return cursor.lastrowid
    finally:
        conn.close()


def get_prompts(focus_id: int) -> list[dict]:
    """Get all prompts for a focus."""
    conn = get_db()
    try:
        rows = conn.execute(
            "SELECT * FROM prompts WHERE focus_id = ? ORDER BY id", (focus_id,)
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def update_prompt(prompt_id: int, **fields) -> None:
    """Update prompt fields."""
    if not fields:
        return
    set_clause = ", ".join(f"{k} = ?" for k in fields)
    values = list(fields.values()) + [prompt_id]
    conn = get_db()
    try:
        conn.execute(f"UPDATE prompts SET {set_clause} WHERE id = ?", values)
        conn.commit()
    finally:
        conn.close()


def delete_prompt(prompt_id: int) -> None:
    """Delete a prompt."""
    conn = get_db()
    try:
        conn.execute("DELETE FROM prompts WHERE id = ?", (prompt_id,))
        conn.commit()
    finally:
        conn.close()


def save_web_data(project_id: int, data: dict) -> None:
    """Save web data for a project (upsert)."""
    now = _now()
    conn = get_db()
    try:
        conn.execute(
            "DELETE FROM web_data WHERE project_id = ?", (project_id,)
        )
        conn.execute(
            "INSERT INTO web_data (project_id, data, updated_at) VALUES (?, ?, ?)",
            (project_id, json.dumps(data), now),
        )
        conn.commit()
    finally:
        conn.close()


def get_web_data(project_id: int) -> dict | None:
    """Get web data for a project, or None."""
    conn = get_db()
    try:
        row = conn.execute(
            "SELECT data FROM web_data WHERE project_id = ?", (project_id,)
        ).fetchone()
        return json.loads(row["data"]) if row else None
    finally:
        conn.close()


def save_step_selections(project_id: int, step: str, selections: list[str]) -> None:
    """Save step selections (upsert)."""
    conn = get_db()
    try:
        conn.execute(
            "DELETE FROM step_selections WHERE project_id = ? AND step = ?",
            (project_id, step),
        )
        conn.execute(
            "INSERT INTO step_selections (project_id, step, selections) VALUES (?, ?, ?)",
            (project_id, step, json.dumps(selections)),
        )
        conn.commit()
    finally:
        conn.close()


def get_step_selections(project_id: int, step: str) -> list[str]:
    """Get step selections, or empty list."""
    conn = get_db()
    try:
        row = conn.execute(
            "SELECT selections FROM step_selections WHERE project_id = ? AND step = ?",
            (project_id, step),
        ).fetchone()
        return json.loads(row["selections"]) if row else []
    finally:
        conn.close()
```

- [ ] **Step 4: Run all tests to verify they pass**

Run: `pytest tests/test_db.py -v`
Expected: All tests PASS

- [ ] **Step 5: Commit**

```bash
git add fp/db.py tests/test_db.py
git commit -m "feat(db): add prompt CRUD, web_data, and step_selections"
```

---

### Task 5: Database Layer — Model Conversion Helpers

**Files:**
- Modify: `fp/db.py`
- Modify: `tests/test_db.py`

**Interfaces:**
- Consumes: All CRUD functions from Tasks 2-4
- Produces: `project_row_to_state()`, `state_to_db()`

- [ ] **Step 1: Write failing tests for conversion helpers**

```python
# append to tests/test_db.py

from fp.db import project_row_to_state, state_to_db
from fp.models import (
    Brand,
    Focus,
    PromptMode,
    ProjectConfig,
    ProjectState,
    ScoredPrompt,
    PromptIntent,
)


def test_project_row_to_state(tmp_path, monkeypatch):
    _setup_db(tmp_path, monkeypatch)

    pid = create_project(
        name="AVO",
        description="AI Visibility",
        website="https://getavo.ai",
        services='["design"]',
        competitors='["comp1"]',
        prompt_mode="both",
        language="en",
    )
    fid = create_focus(
        project_id=pid,
        name="Focus 1",
        description="Desc",
        signals='["sig1"]',
        service_match_score=90.0,
    )
    create_prompt(
        focus_id=fid,
        text="How to track?",
        intent="how-to",
        mode="unbranded",
        service_match=95.0,
        mention_likelihood=70.0,
        overall_score=80.0,
    )

    state = project_row_to_state(pid)

    assert isinstance(state, ProjectState)
    assert state.config.brand.name == "AVO"
    assert state.config.prompt_mode == PromptMode.BOTH
    assert len(state.focuses) == 1
    assert state.focuses[0].name == "Focus 1"
    assert len(state.focuses[0].prompts) == 1
    assert state.focuses[0].prompts[0].text == "How to track?"


def test_state_to_db(tmp_path, monkeypatch):
    _setup_db(tmp_path, monkeypatch)

    brand = Brand(
        name="Test Brand",
        description="Desc",
        website="https://test.com",
        service_categories=["design"],
        competitors=["comp1"],
    )
    config = ProjectConfig(
        brand=brand,
        prompt_mode=PromptMode.UNBRANDED,
        language="id",
    )
    focus = Focus(
        name="Focus 1",
        description="A focus",
        priority="high",
        signals=["sig1"],
        service_match_score=85.0,
        prompts=[
            ScoredPrompt(
                text="Test prompt?",
                intent=PromptIntent.HOWTO,
                mode=PromptMode.UNBRANDED,
                focus_name="Focus 1",
                service_match=90.0,
                mention_likelihood=70.0,
                overall_score=80.0,
            )
        ],
    )
    state = ProjectState(config=config, focuses=[focus])

    pid = state_to_db(state)

    loaded = project_row_to_state(pid)
    assert loaded.config.brand.name == "Test Brand"
    assert len(loaded.focuses) == 1
    assert loaded.focuses[0].prompts[0].text == "Test prompt?"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_db.py -v -k "convert or state_to_db"`
Expected: FAIL with `ImportError: cannot import name 'project_row_to_state'`

- [ ] **Step 3: Implement conversion helpers**

Append to `fp/db.py`:

```python
from fp.models import (
    Brand,
    Focus,
    Prompt,
    PromptIntent,
    PromptMode,
    ProjectConfig,
    ProjectState,
    ScoredPrompt,
)


def project_row_to_state(project_id: int) -> ProjectState:
    """Load a full ProjectState from the database."""
    project = get_project(project_id)
    if not project:
        raise ValueError(f"Project {project_id} not found")

    brand = Brand(
        name=project["name"],
        description=project["description"],
        website=project["website"],
        services=project["services"],
        competitors=project["competitors"],
    )
    config = ProjectConfig(
        brand=brand,
        prompt_mode=PromptMode(project["prompt_mode"]),
        language=project["language"],
    )

    db_focuses = get_focuses(project_id)
    focuses = []
    for f in db_focuses:
        db_prompts = get_prompts(f["id"])
        prompts = [
            ScoredPrompt(
                text=p["text"],
                intent=PromptIntent(p["intent"]),
                mode=PromptMode(p["mode"]),
                focus_name=f["name"],
                language=p["language"],
                service_match=p["service_match"],
                mention_likelihood=p["mention_likelihood"],
                overall_score=p["overall_score"],
                needs_review=bool(p["needs_review"]),
            )
            for p in db_prompts
        ]
        focuses.append(
            Focus(
                name=f["name"],
                description=f["description"],
                lens=f["lens"],
                priority=f["priority"],
                signals=json.loads(f["signals"]),
                signal_count=f["signal_count"],
                service_match_score=f["service_match_score"],
                prompts=prompts,
            )
        )

    web_data = get_web_data(project_id)
    step_selections = {}
    conn = get_db()
    try:
        rows = conn.execute(
            "SELECT step, selections FROM step_selections WHERE project_id = ?",
            (project_id,),
        ).fetchall()
        for r in rows:
            step_selections[r["step"]] = json.loads(r["selections"])
    finally:
        conn.close()

    return ProjectState(
        config=config,
        focuses=focuses,
        web_data=web_data,
        step_selections=step_selections,
    )


def state_to_db(state: ProjectState) -> int:
    """Save a full ProjectState to the database. Returns project ID."""
    brand = state.config.brand
    pid = create_project(
        name=brand.name,
        description=brand.description,
        website=brand.website,
        services=json.dumps(brand.service_categories),
        competitors=json.dumps(brand.competitors),
        prompt_mode=state.config.prompt_mode.value,
        language=state.config.language,
    )

    for focus in state.focuses:
        fid = create_focus(
            project_id=pid,
            name=focus.name,
            description=focus.description,
            lens=focus.lens,
            priority=focus.priority,
            signals=json.dumps(focus.signals),
            service_match_score=focus.service_match_score,
        )
        for prompt in focus.prompts:
            create_prompt(
                focus_id=fid,
                text=prompt.text,
                intent=prompt.intent.value,
                mode=prompt.mode.value,
                language=prompt.language,
                service_match=prompt.service_match,
                mention_likelihood=prompt.mention_likelihood,
                overall_score=prompt.overall_score,
                needs_review=int(prompt.needs_review),
            )

    if state.web_data:
        save_web_data(pid, state.web_data)

    for step, selections in state.step_selections.items():
        save_step_selections(pid, step, selections)

    return pid
```

- [ ] **Step 4: Run all tests to verify they pass**

Run: `pytest tests/test_db.py -v`
Expected: All tests PASS

- [ ] **Step 5: Commit**

```bash
git add fp/db.py tests/test_db.py
git commit -m "feat(db): add model conversion helpers (project_row_to_state, state_to_db)"
```

---

### Task 6: Project CRUD API Routes

**Files:**
- Create: `fp/web/routes/projects.py`
- Modify: `fp/web/app.py` (register router)
- Create: `tests/web/test_projects.py`

**Interfaces:**
- Consumes: All `fp.db` functions from Tasks 2-5
- Produces: `/api/projects`, `/api/projects/{id}`, `/api/projects/{id}/activate`

- [ ] **Step 1: Write failing integration tests**

```python
# tests/web/test_projects.py
import pytest
from fastapi.testclient import TestClient
from fp.web.app import create_app
from fp.db import init_db, list_projects
import tempfile
from pathlib import Path


@pytest.fixture
def client(tmp_path, monkeypatch):
    db_path = tmp_path / "test.db"
    monkeypatch.setattr("fp.db.DB_PATH", db_path)
    init_db(db_path)
    monkeypatch.setattr("fp.web.deps.get_db_path", lambda: db_path)
    app = create_app()
    return TestClient(app)


def test_list_projects_empty(client):
    resp = client.get("/api/projects")
    assert resp.status_code == 200
    data = resp.json()
    assert data == []


def test_create_project(client):
    resp = client.post("/api/projects", json={
        "name": "Test Brand",
        "description": "A test",
        "website": "https://test.com",
        "services": ["design"],
        "competitors": ["comp1"],
        "prompt_mode": "unbranded",
        "language": "id",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["name"] == "Test Brand"
    assert data["id"] > 0


def test_get_project(client):
    create_resp = client.post("/api/projects", json={"name": "AVO"})
    pid = create_resp.json()["id"]

    resp = client.get(f"/api/projects/{pid}")
    assert resp.status_code == 200
    assert resp.json()["name"] == "AVO"


def test_update_project(client):
    create_resp = client.post("/api/projects", json={"name": "Old"})
    pid = create_resp.json()["id"]

    resp = client.put(f"/api/projects/{pid}", json={"name": "New"})
    assert resp.status_code == 200

    get_resp = client.get(f"/api/projects/{pid}")
    assert get_resp.json()["name"] == "New"


def test_delete_project(client):
    create_resp = client.post("/api/projects", json={"name": "ToDelete"})
    pid = create_resp.json()["id"]

    resp = client.delete(f"/api/projects/{pid}")
    assert resp.status_code == 200

    get_resp = client.get(f"/api/projects/{pid}")
    assert get_resp.status_code == 404


def test_activate_project(client):
    r1 = client.post("/api/projects", json={"name": "First"})
    r2 = client.post("/api/projects", json={"name": "Second"})

    client.post(f"/api/projects/{r1.json()['id']}/activate")
    resp = client.get("/api/projects/active")
    assert resp.json()["name"] == "First"

    client.post(f"/api/projects/{r2.json()['id']}/activate")
    resp = client.get("/api/projects/active")
    assert resp.json()["name"] == "Second"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/web/test_projects.py -v`
Expected: FAIL (404 on `/api/projects`)

- [ ] **Step 3: Implement project routes**

```python
# fp/web/routes/projects.py
"""Project CRUD API routes."""
from __future__ import annotations

import json
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

from fp import db

router = APIRouter()


class ProjectCreate(BaseModel):
    name: str
    description: str = ""
    website: str = ""
    services: list[str] = []
    competitors: list[str] = []
    prompt_mode: str = "unbranded"
    language: str = "id"


class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    website: Optional[str] = None
    services: Optional[list[str]] = None
    competitors: Optional[list[str]] = None
    prompt_mode: Optional[str] = None
    language: Optional[str] = None


@router.get("/projects")
async def list_projects():
    """List all projects."""
    return db.list_projects()


@router.post("/projects")
async def create_project(body: ProjectCreate):
    """Create a new project."""
    pid = db.create_project(
        name=body.name,
        description=body.description,
        website=body.website,
        services=json.dumps(body.services),
        competitors=json.dumps(body.competitors),
        prompt_mode=body.prompt_mode,
        language=body.language,
    )
    return db.get_project(pid)


@router.get("/projects/active")
async def get_active_project():
    """Get the active project."""
    pid = db.get_active_project_id()
    if not pid:
        raise HTTPException(status_code=404, detail="No active project")
    project = db.get_project(pid)
    if not project:
        raise HTTPException(status_code=404, detail="Active project not found")
    return project


@router.get("/projects/{project_id}")
async def get_project(project_id: int):
    """Get a project by ID."""
    project = db.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


@router.put("/projects/{project_id}")
async def update_project(project_id: int, body: ProjectUpdate):
    """Update a project."""
    project = db.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    fields = body.model_dump(exclude_unset=True)
    if "services" in fields:
        fields["services"] = json.dumps(fields["services"])
    if "competitors" in fields:
        fields["competitors"] = json.dumps(fields["competitors"])
    db.update_project(project_id, **fields)
    return db.get_project(project_id)


@router.delete("/projects/{project_id}")
async def delete_project(project_id: int):
    """Delete a project and all related data."""
    project = db.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    db.delete_project(project_id)
    return {"status": "ok"}


@router.post("/projects/{project_id}/activate")
async def activate_project(project_id: int):
    """Set a project as active."""
    project = db.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    db.set_active_project(project_id)
    return {"status": "ok", "active_project_id": project_id}
```

- [ ] **Step 4: Register the router in app.py**

```python
# In fp/web/app.py, after existing router includes:
from fp.web.routes.projects import router as projects_router
app.include_router(projects_router, prefix="/api")
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `pytest tests/web/test_projects.py -v`
Expected: All 6 tests PASS

- [ ] **Step 6: Commit**

```bash
git add fp/web/routes/projects.py fp/web/app.py tests/web/test_projects.py
git commit -m "feat(api): add project CRUD routes"
```

---

### Task 7: Focus & Prompt CRUD API Routes

**Files:**
- Create: `fp/web/routes/manage.py`
- Modify: `fp/web/app.py` (register router)
- Create: `tests/web/test_manage.py`

**Interfaces:**
- Consumes: All `fp.db` functions from Tasks 2-5
- Produces: `/api/projects/{id}/focuses`, `/api/projects/{id}/focuses/{fid}`, `/api/projects/{id}/focuses/{fid}/prompts`, etc.

- [ ] **Step 1: Write failing integration tests**

```python
# tests/web/test_manage.py
import pytest
from fastapi.testclient import TestClient
from fp.web.app import create_app
from fp.db import init_db, create_project, create_focus
import tempfile
from pathlib import Path


@pytest.fixture
def client(tmp_path, monkeypatch):
    db_path = tmp_path / "test.db"
    monkeypatch.setattr("fp.db.DB_PATH", db_path)
    init_db(db_path)
    monkeypatch.setattr("fp.web.deps.get_db_path", lambda: db_path)
    app = create_app()
    return TestClient(app)


@pytest.fixture
def project_id(client):
    resp = client.post("/api/projects", json={"name": "Test"})
    return resp.json()["id"]


# ── Focus Tests ──

def test_create_focus(client, project_id):
    resp = client.post(f"/api/projects/{project_id}/focuses", json={
        "name": "Focus A",
        "description": "Desc",
        "priority": "high",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["name"] == "Focus A"
    assert data["id"] > 0


def test_list_focuses(client, project_id):
    client.post(f"/api/projects/{project_id}/focuses", json={"name": "F1"})
    client.post(f"/api/projects/{project_id}/focuses", json={"name": "F2"})

    resp = client.get(f"/api/projects/{project_id}/focuses")
    assert resp.status_code == 200
    assert len(resp.json()) == 2


def test_update_focus(client, project_id):
    create_resp = client.post(f"/api/projects/{project_id}/focuses", json={"name": "Old"})
    fid = create_resp.json()["id"]

    resp = client.put(f"/api/projects/{project_id}/focuses/{fid}", json={"name": "New"})
    assert resp.status_code == 200
    assert resp.json()["name"] == "New"


def test_delete_focus(client, project_id):
    create_resp = client.post(f"/api/projects/{project_id}/focuses", json={"name": "Del"})
    fid = create_resp.json()["id"]

    resp = client.delete(f"/api/projects/{project_id}/focuses/{fid}")
    assert resp.status_code == 200

    list_resp = client.get(f"/api/projects/{project_id}/focuses")
    assert len(list_resp.json()) == 0


# ── Prompt Tests ──

def test_create_prompt(client, project_id):
    focus_resp = client.post(f"/api/projects/{project_id}/focuses", json={"name": "F"})
    fid = focus_resp.json()["id"]

    resp = client.post(f"/api/projects/{project_id}/focuses/{fid}/prompts", json={
        "text": "How to track?",
        "intent": "how-to",
        "mode": "unbranded",
    })
    assert resp.status_code == 200
    assert resp.json()["text"] == "How to track?"


def test_list_prompts(client, project_id):
    focus_resp = client.post(f"/api/projects/{project_id}/focuses", json={"name": "F"})
    fid = focus_resp.json()["id"]

    client.post(f"/api/projects/{project_id}/focuses/{fid}/prompts", json={"text": "P1"})
    client.post(f"/api/projects/{project_id}/focuses/{fid}/prompts", json={"text": "P2"})

    resp = client.get(f"/api/projects/{project_id}/focuses/{fid}/prompts")
    assert len(resp.json()) == 2


def test_update_prompt(client, project_id):
    focus_resp = client.post(f"/api/projects/{project_id}/focuses", json={"name": "F"})
    fid = focus_resp.json()["id"]
    prompt_resp = client.post(f"/api/projects/{project_id}/focuses/{fid}/prompts", json={"text": "Old"})
    pid = prompt_resp.json()["id"]

    resp = client.put(
        f"/api/projects/{project_id}/focuses/{fid}/prompts/{pid}",
        json={"text": "New", "overall_score": 95.0},
    )
    assert resp.status_code == 200
    assert resp.json()["text"] == "New"
    assert resp.json()["overall_score"] == 95.0


def test_delete_prompt(client, project_id):
    focus_resp = client.post(f"/api/projects/{project_id}/focuses", json={"name": "F"})
    fid = focus_resp.json()["id"]
    prompt_resp = client.post(f"/api/projects/{project_id}/focuses/{fid}/prompts", json={"text": "Del"})
    pid = prompt_resp.json()["id"]

    resp = client.delete(f"/api/projects/{project_id}/focuses/{fid}/prompts/{pid}")
    assert resp.status_code == 200

    list_resp = client.get(f"/api/projects/{project_id}/focuses/{fid}/prompts")
    assert len(list_resp.json()) == 0


def test_get_full_project(client, project_id):
    """GET /api/projects/{id} returns focuses with prompts nested."""
    focus_resp = client.post(f"/api/projects/{project_id}/focuses", json={"name": "F"})
    fid = focus_resp.json()["id"]
    client.post(f"/api/projects/{project_id}/focuses/{fid}/prompts", json={"text": "P1"})

    resp = client.get(f"/api/projects/{project_id}/full")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["focuses"]) == 1
    assert len(data["focuses"][0]["prompts"]) == 1
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/web/test_manage.py -v`
Expected: FAIL (404 on focus/prompt routes)

- [ ] **Step 3: Implement focus/prompt manage routes**

```python
# fp/web/routes/manage.py
"""Focus and Prompt CRUD API routes."""
from __future__ import annotations

import json
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

from fp import db

router = APIRouter()


# ── Focus ──

class FocusCreate(BaseModel):
    name: str
    description: str = ""
    lens: str = "problem"
    priority: str = "medium"
    signals: list[str] = []
    service_match_score: float = 0.0


class FocusUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    lens: Optional[str] = None
    priority: Optional[str] = None
    signals: Optional[list[str]] = None
    service_match_score: Optional[float] = None


@router.get("/projects/{project_id}/focuses")
async def list_focuses(project_id: int):
    """List all focuses for a project."""
    project = db.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return db.get_focuses(project_id)


@router.post("/projects/{project_id}/focuses")
async def create_focus(project_id: int, body: FocusCreate):
    """Create a focus for a project."""
    project = db.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    fid = db.create_focus(
        project_id=project_id,
        name=body.name,
        description=body.description,
        lens=body.lens,
        priority=body.priority,
        signals=json.dumps(body.signals),
        service_match_score=body.service_match_score,
    )
    focuses = db.get_focuses(project_id)
    return [f for f in focuses if f["id"] == fid][0]


@router.put("/projects/{project_id}/focuses/{focus_id}")
async def update_focus(project_id: int, focus_id: int, body: FocusUpdate):
    """Update a focus."""
    focuses = db.get_focuses(project_id)
    if not any(f["id"] == focus_id for f in focuses):
        raise HTTPException(status_code=404, detail="Focus not found")
    fields = body.model_dump(exclude_unset=True)
    if "signals" in fields:
        fields["signals"] = json.dumps(fields["signals"])
    db.update_focus(focus_id, **fields)
    focuses = db.get_focuses(project_id)
    return [f for f in focuses if f["id"] == focus_id][0]


@router.delete("/projects/{project_id}/focuses/{focus_id}")
async def delete_focus(project_id: int, focus_id: int):
    """Delete a focus and its prompts."""
    focuses = db.get_focuses(project_id)
    if not any(f["id"] == focus_id for f in focuses):
        raise HTTPException(status_code=404, detail="Focus not found")
    db.delete_focus(focus_id)
    return {"status": "ok"}


# ── Prompt ──

class PromptCreate(BaseModel):
    text: str
    intent: str = "info"
    mode: str = "unbranded"
    language: str = "id"
    service_match: float = 0.0
    mention_likelihood: float = 0.0
    overall_score: float = 0.0
    needs_review: bool = False


class PromptUpdate(BaseModel):
    text: Optional[str] = None
    intent: Optional[str] = None
    mode: Optional[str] = None
    language: Optional[str] = None
    service_match: Optional[float] = None
    mention_likelihood: Optional[float] = None
    overall_score: Optional[float] = None
    needs_review: Optional[bool] = None


@router.get("/projects/{project_id}/focuses/{focus_id}/prompts")
async def list_prompts(project_id: int, focus_id: int):
    """List all prompts for a focus."""
    focuses = db.get_focuses(project_id)
    if not any(f["id"] == focus_id for f in focuses):
        raise HTTPException(status_code=404, detail="Focus not found")
    return db.get_prompts(focus_id)


@router.post("/projects/{project_id}/focuses/{focus_id}/prompts")
async def create_prompt(project_id: int, focus_id: int, body: PromptCreate):
    """Create a prompt for a focus."""
    focuses = db.get_focuses(project_id)
    if not any(f["id"] == focus_id for f in focuses):
        raise HTTPException(status_code=404, detail="Focus not found")
    pid = db.create_prompt(
        focus_id=focus_id,
        text=body.text,
        intent=body.intent,
        mode=body.mode,
        language=body.language,
        service_match=body.service_match,
        mention_likelihood=body.mention_likelihood,
        overall_score=body.overall_score,
        needs_review=int(body.needs_review),
    )
    prompts = db.get_prompts(focus_id)
    return [p for p in prompts if p["id"] == pid][0]


@router.put("/projects/{project_id}/focuses/{focus_id}/prompts/{prompt_id}")
async def update_prompt(project_id: int, focus_id: int, prompt_id: int, body: PromptUpdate):
    """Update a prompt."""
    prompts = db.get_prompts(focus_id)
    if not any(p["id"] == prompt_id for p in prompts):
        raise HTTPException(status_code=404, detail="Prompt not found")
    fields = body.model_dump(exclude_unset=True)
    if "needs_review" in fields:
        fields["needs_review"] = int(fields["needs_review"])
    db.update_prompt(prompt_id, **fields)
    prompts = db.get_prompts(focus_id)
    return [p for p in prompts if p["id"] == prompt_id][0]


@router.delete("/projects/{project_id}/focuses/{focus_id}/prompts/{prompt_id}")
async def delete_prompt(project_id: int, focus_id: int, prompt_id: int):
    """Delete a prompt."""
    prompts = db.get_prompts(focus_id)
    if not any(p["id"] == prompt_id for p in prompts):
        raise HTTPException(status_code=404, detail="Prompt not found")
    db.delete_prompt(prompt_id)
    return {"status": "ok"}


@router.get("/projects/{project_id}/full")
async def get_full_project(project_id: int):
    """Get full project with focuses and prompts nested."""
    project = db.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    focuses = db.get_focuses(project_id)
    for f in focuses:
        f["prompts"] = db.get_prompts(f["id"])
    project["focuses"] = focuses
    return project
```

- [ ] **Step 4: Register the router in app.py**

```python
# In fp/web/app.py, add after projects_router:
from fp.web.routes.manage import router as manage_router
app.include_router(manage_router, prefix="/api")
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `pytest tests/web/test_manage.py -v`
Expected: All 10 tests PASS

- [ ] **Step 6: Commit**

```bash
git add fp/web/routes/manage.py fp/web/app.py tests/web/test_manage.py
git commit -m "feat(api): add focus and prompt CRUD routes"
```

---

### Task 8: Update deps.py — SQLite Reads/Writes

**Files:**
- Modify: `fp/web/deps.py`

**Interfaces:**
- Consumes: `fp.db` functions from Tasks 2-5
- Produces: Updated `get_state()`, `save_state()`

- [ ] **Step 1: Update deps.py**

```python
# fp/web/deps.py
"""Shared dependencies for web routes."""
from __future__ import annotations

from pathlib import Path

from fp import db
from fp.config import load_user_config, get_current_config


def get_db_path():
    """Return the database path (for monkeypatching in tests)."""
    return db.DB_PATH


def get_state():
    """Load active project state from SQLite, or None if no active project."""
    db.init_db()
    project_id = db.get_active_project_id()
    if not project_id:
        return None
    try:
        return db.project_row_to_state(project_id)
    except ValueError:
        return None


def save_state(state) -> None:
    """Save project state to SQLite (upsert active project)."""
    from fp.models import ProjectState
    db.init_db()
    project_id = db.get_active_project_id()
    if project_id:
        # Update existing project in place
        brand = state.config.brand
        db.update_project(
            project_id,
            name=brand.name,
            description=brand.description,
            website=brand.website,
            services=brand.service_categories,
            competitors=brand.competitors,
            prompt_mode=state.config.prompt_mode.value,
            language=state.config.language,
        )
        # Delete old focuses and re-create
        old_focuses = db.get_focuses(project_id)
        for f in old_focuses:
            db.delete_focus(f["id"])
        for focus in state.focuses:
            fid = db.create_focus(
                project_id=project_id,
                name=focus.name,
                description=focus.description,
                lens=focus.lens,
                priority=focus.priority,
                signals=focus.signals,
                service_match_score=focus.service_match_score,
            )
            for prompt in focus.prompts:
                db.create_prompt(
                    focus_id=fid,
                    text=prompt.text,
                    intent=prompt.intent.value,
                    mode=prompt.mode.value,
                    language=prompt.language,
                    service_match=prompt.service_match,
                    mention_likelihood=prompt.mention_likelihood,
                    overall_score=prompt.overall_score,
                    needs_review=int(prompt.needs_review),
                )
        if state.web_data:
            db.save_web_data(project_id, state.web_data)
        for step, selections in state.step_selections.items():
            db.save_step_selections(project_id, step, selections)
    else:
        # No active project — create new one
        new_id = db.state_to_db(state)
        db.set_active_project(new_id)


def get_config() -> dict[str, str]:
    """Get current config values."""
    load_user_config()
    return get_current_config()
```

- [ ] **Step 2: Run existing web tests to check for regressions**

Run: `pytest tests/web/ -v`
Expected: All existing tests PASS (some may need adjustment for new deps)

- [ ] **Step 3: Commit**

```bash
git add fp/web/deps.py
git commit -m "refactor(deps): switch from JSON to SQLite reads/writes"
```

---

### Task 9: Migration — Auto-Import Existing JSON

**Files:**
- Modify: `fp/web/routes/pages.py` (add migration logic)

**Interfaces:**
- Consumes: `fp.db.state_to_db()`, `fp.db.get_active_project_id()`

- [ ] **Step 1: Add migration to pages.py init route**

Add to `fp/web/routes/pages.py` at module level (runs once on import):

```python
# At the top of pages.py, after imports:
def _migrate_json_if_needed():
    """Auto-import fp-project.json to SQLite on first run."""
    from fp.db import init_db, get_active_project_id, state_to_db, set_active_project
    from fp.models import ProjectState

    init_db()

    if get_active_project_id() is not None:
        return  # Already migrated

    json_path = Path("fp-project.json")
    if not json_path.exists():
        return  # Nothing to migrate

    try:
        state = ProjectState.load(json_path)
        pid = state_to_db(state)
        set_active_project(pid)
        json_path.rename(json_path.with_suffix(".json.bak"))
    except Exception:
        pass  # If migration fails, user can create new project


# Call on module load
_migrate_json_if_needed()
```

- [ ] **Step 2: Commit**

```bash
git add fp/web/routes/pages.py
git commit -m "feat(migration): auto-import fp-project.json to SQLite"
```

---

### Task 10: Project List Page (HTML)

**Files:**
- Create: `fp/web/templates/projects.html`
- Modify: `fp/web/routes/pages.py` (add `/projects` route)

**Interfaces:**
- Consumes: `fp.db.list_projects()`, `fp.db.get_focuses()`, `fp.db.get_prompts()`

- [ ] **Step 1: Add project list route to pages.py**

```python
@router.get("/projects", response_class=HTMLResponse)
async def projects_page(request: Request):
    """Project list page."""
    from fp.db import list_projects, get_focuses, get_prompts

    templates = request.app.state.templates
    projects = list_projects()
    # Enrich with counts
    for p in projects:
        focuses = get_focuses(p["id"])
        p["focus_count"] = len(focuses)
        p["prompt_count"] = sum(len(get_prompts(f["id"])) for f in focuses)

    return templates.TemplateResponse(request, "projects.html", {"projects": projects})
```

- [ ] **Step 2: Create projects.html template**

```html
<!-- fp/web/templates/projects.html -->
{% extends "base.html" %}
{% block title %}Projects — Focus Prompt{% endblock %}
{% block content %}
<div class="space-y-6">
    <div class="flex items-center justify-between">
        <h1 class="text-2xl font-bold text-white">Projects</h1>
        <a href="/init" class="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white font-medium rounded-lg transition-colors text-sm">
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"/>
            </svg>
            New Project
        </a>
    </div>

    {% if projects %}
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {% for p in projects %}
        <div class="bg-slate-800 rounded-xl border border-slate-700/50 p-5 hover:border-slate-600 transition-colors cursor-pointer group"
             onclick="window.location='/pipeline'">
            <div class="flex items-start justify-between mb-3">
                <div class="flex items-center gap-3">
                    <div class="w-10 h-10 rounded-lg bg-blue-500/20 flex items-center justify-center text-blue-400 font-bold text-lg">
                        {{ p.name[0] | upper }}
                    </div>
                    <div>
                        <h3 class="font-semibold text-white group-hover:text-blue-400 transition-colors">{{ p.name }}</h3>
                        <p class="text-slate-500 text-xs">{{ p.prompt_mode | title }} · {{ p.language | upper }}</p>
                    </div>
                </div>
                <div class="flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                    <button onclick="event.stopPropagation(); activateProject({{ p.id }})"
                            class="p-1.5 rounded hover:bg-slate-700 text-slate-400 hover:text-white"
                            title="Set as active">
                        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/>
                        </svg>
                    </button>
                    <button onclick="event.stopPropagation(); deleteProject({{ p.id }}, '{{ p.name }}')"
                            class="p-1.5 rounded hover:bg-red-500/20 text-slate-400 hover:text-red-400"
                            title="Delete">
                        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"/>
                        </svg>
                    </button>
                </div>
            </div>

            {% if p.description %}
            <p class="text-slate-400 text-sm mb-3 line-clamp-2">{{ p.description }}</p>
            {% endif %}

            <div class="flex gap-4 text-xs text-slate-500">
                <span>{{ p.focus_count }} focuses</span>
                <span>{{ p.prompt_count }} prompts</span>
            </div>
        </div>
        {% endfor %}
    </div>
    {% else %}
    <div class="bg-slate-800 rounded-xl border border-slate-700/50 p-12 text-center">
        <svg class="w-16 h-16 mx-auto text-slate-600 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10"/>
        </svg>
        <p class="text-slate-400 mb-2">No projects yet</p>
        <a href="/init" class="inline-flex items-center gap-2 px-5 py-2.5 bg-blue-600 hover:bg-blue-500 text-white font-medium rounded-lg transition-colors">
            Create First Project
        </a>
    </div>
    {% endif %}
</div>

<script>
async function activateProject(id) {
    await fetch(`/api/projects/${id}/activate`, { method: 'POST' });
    window.location = '/pipeline';
}

async function deleteProject(id, name) {
    if (!confirm(`Delete "${name}" and all its focuses/prompts?`)) return;
    await fetch(`/api/projects/${id}`, { method: 'DELETE' });
    window.location.reload();
}
</script>
{% endblock %}
```

- [ ] **Step 3: Commit**

```bash
git add fp/web/templates/projects.html fp/web/routes/pages.py
git commit -m "feat(ui): add project list page"
```

---

### Task 11: Project Manage Page (HTML)

**Files:**
- Create: `fp/web/templates/manage.html`
- Modify: `fp/web/routes/pages.py` (add `/projects/{id}/manage` route)

**Interfaces:**
- Consumes: `fp.db.project_row_to_state()`, focus/prompt CRUD API routes

- [ ] **Step 1: Add manage page route**

```python
@router.get("/projects/{project_id}/manage", response_class=HTMLResponse)
async def manage_page(request: Request, project_id: int):
    """Project detail/manage page with focuses and prompts."""
    from fp.db import get_project, project_row_to_state, get_focuses, get_prompts

    templates = request.app.state.templates
    project = get_project(project_id)
    if not project:
        return RedirectResponse(url="/projects", status_code=302)

    focuses = get_focuses(project_id)
    for f in focuses:
        f["prompts"] = db.get_prompts(f["id"])

    context = {"project": project, "focuses": focuses}
    return templates.TemplateResponse(request, "manage.html", context)
```

- [ ] **Step 2: Create manage.html template**

This is a large template with inline editing. Key sections:
- Project header with editable name/description
- Focuses table with expand/collapse for prompts
- Add/edit/delete modals for both focuses and prompts
- All CRUD via HTMX to the API routes

Due to size, this template will be created in a dedicated step. The template uses:
- HTMX `hx-post`, `hx-put`, `hx-delete` for CRUD
- `hx-target` and `hx-swap` for partial page updates
- CSS for inline editing (click-to-edit pattern)
- Modal dialogs for add operations

- [ ] **Step 3: Commit**

```bash
git add fp/web/templates/manage.html fp/web/routes/pages.py
git commit -m "feat(ui): add project manage page with inline CRUD"
```

---

### Task 12: Update Navigation & Dashboard

**Files:**
- Modify: `fp/web/templates/base.html`
- Modify: `fp/web/routes/pages.py` (update index route)

**Interfaces:**
- Consumes: Updated navigation from Design Section 3

- [ ] **Step 1: Update nav in base.html**

Change the nav links:
```html
<a href="/projects" class="...">Projects</a>
<a href="/pipeline" class="...">Pipeline</a>
<a href="/settings" class="...">Settings</a>
```

- [ ] **Step 2: Update index route to redirect to /projects**

```python
@router.get("/", response_class=RedirectResponse)
async def index(request: Request):
    """Dashboard redirects to project list."""
    return RedirectResponse(url="/projects", status_code=302)
```

- [ ] **Step 3: Commit**

```bash
git add fp/web/templates/base.html fp/web/routes/pages.py
git commit -m "refactor(ui): update navigation and dashboard redirect"
```

---

### Task 13: Run Full Test Suite & Lint

**Files:** None (verification only)

- [ ] **Step 1: Run all tests**

Run: `pytest tests/ -v`
Expected: All tests PASS

- [ ] **Step 2: Run lint/typecheck if available**

Run: `ruff check fp/` or `mypy fp/` (if configured)
Expected: No errors

- [ ] **Step 3: Manual smoke test**

```bash
fp web
# Open http://127.0.0.1:8000/projects
# Verify: empty project list shows
# Click "New Project" → create project → verify redirect to pipeline
# Go back to /projects → verify project card appears
# Click project → manage page → add focus → add prompt → verify
# Delete prompt → delete focus → delete project → verify cascade
```

- [ ] **Step 4: Commit any fixes**

```bash
git add -A
git commit -m "fix: address lint and test issues"
```

---

## Summary

| Task | Description | New Files | Modified Files |
|------|-------------|-----------|----------------|
| 1 | DB schema & init | `fp/db.py`, `tests/test_db.py` | — |
| 2 | Project CRUD | — | `fp/db.py`, `tests/test_db.py` |
| 3 | Focus CRUD | — | `fp/db.py`, `tests/test_db.py` |
| 4 | Prompt CRUD + web_data | — | `fp/db.py`, `tests/test_db.py` |
| 5 | Model conversion helpers | — | `fp/db.py`, `tests/test_db.py` |
| 6 | Project API routes | `fp/web/routes/projects.py`, `tests/web/test_projects.py` | `fp/web/app.py` |
| 7 | Focus/Prompt API routes | `fp/web/routes/manage.py`, `tests/web/test_manage.py` | `fp/web/app.py` |
| 8 | deps.py SQLite migration | — | `fp/web/deps.py` |
| 9 | JSON auto-import migration | — | `fp/web/routes/pages.py` |
| 10 | Project list page | `fp/web/templates/projects.html` | `fp/web/routes/pages.py` |
| 11 | Project manage page | `fp/web/templates/manage.html` | `fp/web/routes/pages.py` |
| 12 | Navigation update | — | `fp/web/templates/base.html`, `fp/web/routes/pages.py` |
| 13 | Full test suite & lint | — | — |
