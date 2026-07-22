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


@pytest.mark.skip(reason="create_prompt/get_prompts not yet implemented (Task 4)")
def test_delete_focus_cascades_to_prompts(tmp_path, monkeypatch):
    _setup_db(tmp_path, monkeypatch)
    from fp.db import create_prompt, get_prompts

    pid = create_project(name="Test")
    fid = create_focus(project_id=pid, name="Focus")
    create_prompt(focus_id=fid, text="prompt1")
    create_prompt(focus_id=fid, text="prompt2")

    delete_focus(fid)

    assert get_focuses(pid) == []
