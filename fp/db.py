"""SQLite database layer for focus-prompt."""
from __future__ import annotations

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
    """List all projects ordered by created_at asc."""
    conn = get_db()
    try:
        rows = conn.execute("SELECT * FROM projects ORDER BY created_at ASC").fetchall()
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
