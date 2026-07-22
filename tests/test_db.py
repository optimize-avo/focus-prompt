import sqlite3
from pathlib import Path

import pytest

from fp.db import init_db, get_db, DB_PATH
from fp.db import (
    create_project,
    get_project,
    list_projects,
    update_project,
    delete_project,
    set_active_project,
    get_active_project_id,
)


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


# --- Focus CRUD tests (Task 3) ---

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


# --- Prompt CRUD + web_data + step_selections tests (Task 4) ---

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


# --- Conversion helper tests (Task 5) ---

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
