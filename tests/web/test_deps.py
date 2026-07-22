"""Tests for fp.web.deps — SQLite-backed state management."""
from __future__ import annotations

import json
import pytest
from pathlib import Path

from fp.models import (
    Brand,
    Focus,
    ProjectConfig,
    ProjectState,
    PromptIntent,
    PromptMode,
    ScoredPrompt,
)
from fp import db
from fp.web import deps


@pytest.fixture(autouse=True)
def _use_test_db(tmp_path, monkeypatch):
    """Point all DB operations to a temporary test database."""
    db_path = tmp_path / "test.db"
    monkeypatch.setattr(db, "DB_PATH", db_path)
    monkeypatch.setattr(deps, "get_db_path", lambda: db_path)
    db.init_db(db_path)
    yield


def _make_state(
    name: str = "TestBrand",
    focuses=None,
    web_data=None,
    step_selections=None,
) -> ProjectState:
    """Build a minimal ProjectState for testing."""
    brand = Brand(
        name=name,
        description="A test brand",
        website="https://example.com",
        service_categories=["design", "development"],
        competitors=["comp1", "comp2"],
    )
    config = ProjectConfig(
        brand=brand,
        prompt_mode=PromptMode.UNBRANDED,
        language="id",
    )
    return ProjectState(
        config=config,
        focuses=focuses or [],
        web_data=web_data,
        step_selections=step_selections or {},
    )


# ── get_state() tests ──────────────────────────────────────────────────────


def test_get_state_returns_none_when_no_project():
    """get_state() returns None when there is no active project."""
    result = deps.get_state()
    assert result is None


def test_get_state_returns_project_state_after_save():
    """get_state() returns the saved ProjectState after save_state()."""
    state = _make_state(name="MyBrand")
    deps.save_state(state)

    loaded = deps.get_state()
    assert loaded is not None
    assert loaded.config.brand.name == "MyBrand"
    assert loaded.config.brand.description == "A test brand"


def test_get_state_returns_none_when_active_project_deleted():
    """get_state() returns None after the active project is deleted."""
    deps.save_state(_make_state())
    pid = db.get_active_project_id()
    assert pid is not None
    db.delete_project(pid)

    result = deps.get_state()
    assert result is None


# ── save_state() — new project ─────────────────────────────────────────────


def test_save_state_creates_project():
    """save_state() creates a new project in DB when none is active."""
    state = _make_state(name="NewBrand")
    deps.save_state(state)

    pid = db.get_active_project_id()
    assert pid is not None
    project = db.get_project(pid)
    assert project["name"] == "NewBrand"
    assert project["description"] == "A test brand"
    assert project["website"] == "https://example.com"


def test_save_state_serializes_services_and_competitors():
    """save_state() stores services and competitors as JSON strings."""
    state = _make_state()
    deps.save_state(state)

    pid = db.get_active_project_id()
    project = db.get_project(pid)
    assert json.loads(project["services"]) == ["design", "development"]
    assert json.loads(project["competitors"]) == ["comp1", "comp2"]


def test_save_state_stores_prompt_mode_and_language():
    """save_state() stores prompt_mode and language correctly."""
    state = _make_state()
    deps.save_state(state)

    pid = db.get_active_project_id()
    project = db.get_project(pid)
    assert project["prompt_mode"] == "unbranded"
    assert project["language"] == "id"


# ── save_state() — with focuses ────────────────────────────────────────────


def test_save_state_with_focuses():
    """save_state() persists focuses and their prompts."""
    focus = Focus(
        name="UX Design",
        description="User experience",
        lens="problem",
        priority="high",
        signals=["signal1", "signal2"],
        service_match_score=0.85,
        prompts=[
            ScoredPrompt(
                text="How to improve UX?",
                intent=PromptIntent.INFO,
                mode=PromptMode.UNBRANDED,
                focus_name="UX Design",
                language="id",
                service_match=0.9,
                mention_likelihood=0.7,
                overall_score=0.8,
                needs_review=False,
            )
        ],
    )
    state = _make_state(focuses=[focus])
    deps.save_state(state)

    loaded = deps.get_state()
    assert loaded is not None
    assert len(loaded.focuses) == 1
    f = loaded.focuses[0]
    assert f.name == "UX Design"
    assert f.signals == ["signal1", "signal2"]
    assert f.service_match_score == 0.85
    assert len(f.prompts) == 1
    p = f.prompts[0]
    assert p.text == "How to improve UX?"
    assert p.service_match == 0.9
    assert p.overall_score == 0.8
    assert p.needs_review is False


# ── save_state() — update existing project ─────────────────────────────────


def test_save_state_updates_existing_project():
    """save_state() updates the active project in place rather than creating a new one."""
    state1 = _make_state(name="Original")
    deps.save_state(state1)
    pid1 = db.get_active_project_id()

    state2 = _make_state(name="Updated")
    deps.save_state(state2)
    pid2 = db.get_active_project_id()

    # Should be the same project ID
    assert pid1 == pid2
    project = db.get_project(pid2)
    assert project["name"] == "Updated"


def test_save_state_updates_focuses_on_existing_project():
    """save_state() replaces focuses when updating an existing project."""
    focus_a = Focus(
        name="Focus A",
        description="First",
        prompts=[],
    )
    state1 = _make_state(focuses=[focus_a])
    deps.save_state(state1)

    focus_b = Focus(
        name="Focus B",
        description="Second",
        prompts=[],
    )
    state2 = _make_state(focuses=[focus_b])
    deps.save_state(state2)

    loaded = deps.get_state()
    assert loaded is not None
    assert len(loaded.focuses) == 1
    assert loaded.focuses[0].name == "Focus B"


def test_save_state_updates_web_data():
    """save_state() persists web_data."""
    web_data = {
        "stats": {"total_queries": 5},
        "autocomplete": ["q1", "q2"],
    }
    state = _make_state(web_data=web_data)
    deps.save_state(state)

    loaded = deps.get_state()
    assert loaded is not None
    assert loaded.web_data == web_data


def test_save_state_updates_step_selections():
    """save_state() persists step_selections."""
    selections = {"research": ["q1"], "discover": ["Focus A"]}
    state = _make_state(step_selections=selections)
    deps.save_state(state)

    loaded = deps.get_state()
    assert loaded is not None
    assert loaded.step_selections == selections


# ── save_state() — update existing project with web_data ───────────────────


def test_save_state_updates_web_data_on_existing_project():
    """save_state() updates web_data on an existing project."""
    state1 = _make_state()
    deps.save_state(state1)

    web_data = {"stats": {"total_queries": 3}}
    state2 = _make_state(web_data=web_data)
    deps.save_state(state2)

    loaded = deps.get_state()
    assert loaded is not None
    assert loaded.web_data == web_data
