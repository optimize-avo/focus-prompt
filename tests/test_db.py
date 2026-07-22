import sqlite3
from pathlib import Path
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
