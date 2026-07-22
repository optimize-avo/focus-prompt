import sqlite3
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
