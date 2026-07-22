"""SQLite database layer for focus-prompt."""
from __future__ import annotations

import sqlite3
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
