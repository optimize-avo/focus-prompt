"""Shared dependencies for web routes."""
from __future__ import annotations

from pathlib import Path

from fp.models import ProjectState
from fp.config import load_user_config, get_current_config

PROJECT_FILE = "fp-project.json"


def get_db_path() -> Path:
    """Return the database path (mirrors fp.db.DB_PATH)."""
    from fp.db import DB_PATH
    return DB_PATH


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
