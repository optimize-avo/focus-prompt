"""Tests for auto-migration of fp-project.json to SQLite (Task 9)."""
from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import pytest

from fp.models import (
    Brand,
    Focus,
    PromptIntent,
    PromptMode,
    ProjectConfig,
    ProjectState,
    ScoredPrompt,
)


def _make_sample_state() -> ProjectState:
    """Build a minimal ProjectState for testing."""
    brand = Brand(
        name="Migration Test Brand",
        description="A test brand",
        website="https://example.com",
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
        description="A focus area",
        lens="problem",
        priority="high",
        signals=["sig1"],
        service_match_score=85.0,
        prompts=[
            ScoredPrompt(
                text="How to test migration?",
                intent=PromptIntent.HOWTO,
                mode=PromptMode.UNBRANDED,
                focus_name="Focus 1",
                service_match=90.0,
                mention_likelihood=70.0,
                overall_score=80.0,
            )
        ],
    )
    return ProjectState(config=config, focuses=[focus])


def test_migrate_json_creates_project(tmp_path, monkeypatch):
    """Migration loads fp-project.json, saves to DB, renames to .bak."""
    from fp import db

    db_path = tmp_path / "test.db"
    monkeypatch.setattr(db, "DB_PATH", db_path)
    db.init_db(db_path)

    # Create fp-project.json in tmp_path (CWD for this test)
    json_path = tmp_path / "fp-project.json"
    state = _make_sample_state()
    state.save(json_path)
    monkeypatch.chdir(tmp_path)

    from fp.web.routes.pages import _migrate_json_if_needed

    _migrate_json_if_needed()

    # Project was created
    project_id = db.get_active_project_id()
    assert project_id is not None

    project = db.get_project(project_id)
    assert project is not None
    assert project["name"] == "Migration Test Brand"
    assert project["website"] == "https://example.com"

    # Focus was created
    focuses = db.get_focuses(project_id)
    assert len(focuses) == 1
    assert focuses[0]["name"] == "Focus 1"

    # Prompt was created
    prompts = db.get_prompts(focuses[0]["id"])
    assert len(prompts) == 1
    assert prompts[0]["text"] == "How to test migration?"

    # JSON file was renamed to .bak
    assert not json_path.exists()
    assert (tmp_path / "fp-project.json.bak").exists()


def test_migrate_json_skips_when_already_migrated(tmp_path, monkeypatch):
    """Migration is skipped if there's already an active project."""
    from fp import db

    db_path = tmp_path / "test.db"
    monkeypatch.setattr(db, "DB_PATH", db_path)
    db.init_db(db_path)

    # Create an active project first
    pid = db.create_project(name="Existing Project")
    db.set_active_project(pid)

    # Create fp-project.json
    json_path = tmp_path / "fp-project.json"
    state = _make_sample_state()
    state.save(json_path)
    monkeypatch.chdir(tmp_path)

    from fp.web.routes.pages import _migrate_json_if_needed

    _migrate_json_if_needed()

    # The original project should still be active
    assert db.get_active_project_id() == pid

    # JSON file should NOT have been touched
    assert json_path.exists()
    assert not (tmp_path / "fp-project.json.bak").exists()


def test_migrate_json_skips_when_no_file(tmp_path, monkeypatch):
    """Migration does nothing if no fp-project.json exists."""
    from fp import db

    db_path = tmp_path / "test.db"
    monkeypatch.setattr(db, "DB_PATH", db_path)
    db.init_db(db_path)
    monkeypatch.chdir(tmp_path)

    from fp.web.routes.pages import _migrate_json_if_needed

    _migrate_json_if_needed()

    # No project should be created
    assert db.get_active_project_id() is None
    assert len(db.list_projects()) == 0


def test_migrate_json_handles_corrupt_json(tmp_path, monkeypatch):
    """Migration handles corrupt JSON gracefully without crashing."""
    from fp import db

    db_path = tmp_path / "test.db"
    monkeypatch.setattr(db, "DB_PATH", db_path)
    db.init_db(db_path)

    # Write corrupt JSON
    json_path = tmp_path / "fp-project.json"
    json_path.write_text("{invalid json content")
    monkeypatch.chdir(tmp_path)

    from fp.web.routes.pages import _migrate_json_if_needed

    # Should not raise
    _migrate_json_if_needed()

    # No project created
    assert db.get_active_project_id() is None
