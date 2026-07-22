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
