import pytest
from fastapi.testclient import TestClient
from fp.web.app import create_app
from fp.db import init_db, create_project, create_focus
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


@pytest.fixture
def project_id(client):
    resp = client.post("/api/projects", json={"name": "Test"})
    return resp.json()["id"]


# ── Focus Tests ──

def test_create_focus(client, project_id):
    resp = client.post(f"/api/projects/{project_id}/focuses", json={
        "name": "Focus A",
        "description": "Desc",
        "priority": "high",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["name"] == "Focus A"
    assert data["id"] > 0


def test_list_focuses(client, project_id):
    client.post(f"/api/projects/{project_id}/focuses", json={"name": "F1"})
    client.post(f"/api/projects/{project_id}/focuses", json={"name": "F2"})

    resp = client.get(f"/api/projects/{project_id}/focuses")
    assert resp.status_code == 200
    assert len(resp.json()) == 2


def test_update_focus(client, project_id):
    create_resp = client.post(f"/api/projects/{project_id}/focuses", json={"name": "Old"})
    fid = create_resp.json()["id"]

    resp = client.put(f"/api/projects/{project_id}/focuses/{fid}", json={"name": "New"})
    assert resp.status_code == 200
    assert resp.json()["name"] == "New"


def test_delete_focus(client, project_id):
    create_resp = client.post(f"/api/projects/{project_id}/focuses", json={"name": "Del"})
    fid = create_resp.json()["id"]

    resp = client.delete(f"/api/projects/{project_id}/focuses/{fid}")
    assert resp.status_code == 200

    list_resp = client.get(f"/api/projects/{project_id}/focuses")
    assert len(list_resp.json()) == 0


# ── Prompt Tests ──

def test_create_prompt(client, project_id):
    focus_resp = client.post(f"/api/projects/{project_id}/focuses", json={"name": "F"})
    fid = focus_resp.json()["id"]

    resp = client.post(f"/api/projects/{project_id}/focuses/{fid}/prompts", json={
        "text": "How to track?",
        "intent": "how-to",
        "mode": "unbranded",
    })
    assert resp.status_code == 200
    assert resp.json()["text"] == "How to track?"


def test_list_prompts(client, project_id):
    focus_resp = client.post(f"/api/projects/{project_id}/focuses", json={"name": "F"})
    fid = focus_resp.json()["id"]

    client.post(f"/api/projects/{project_id}/focuses/{fid}/prompts", json={"text": "P1"})
    client.post(f"/api/projects/{project_id}/focuses/{fid}/prompts", json={"text": "P2"})

    resp = client.get(f"/api/projects/{project_id}/focuses/{fid}/prompts")
    assert len(resp.json()) == 2


def test_update_prompt(client, project_id):
    focus_resp = client.post(f"/api/projects/{project_id}/focuses", json={"name": "F"})
    fid = focus_resp.json()["id"]
    prompt_resp = client.post(f"/api/projects/{project_id}/focuses/{fid}/prompts", json={"text": "Old"})
    pid = prompt_resp.json()["id"]

    resp = client.put(
        f"/api/projects/{project_id}/focuses/{fid}/prompts/{pid}",
        json={"text": "New", "overall_score": 95.0},
    )
    assert resp.status_code == 200
    assert resp.json()["text"] == "New"
    assert resp.json()["overall_score"] == 95.0


def test_delete_prompt(client, project_id):
    focus_resp = client.post(f"/api/projects/{project_id}/focuses", json={"name": "F"})
    fid = focus_resp.json()["id"]
    prompt_resp = client.post(f"/api/projects/{project_id}/focuses/{fid}/prompts", json={"text": "Del"})
    pid = prompt_resp.json()["id"]

    resp = client.delete(f"/api/projects/{project_id}/focuses/{fid}/prompts/{pid}")
    assert resp.status_code == 200

    list_resp = client.get(f"/api/projects/{project_id}/focuses/{fid}/prompts")
    assert len(list_resp.json()) == 0


def test_get_full_project(client, project_id):
    """GET /api/projects/{id} returns focuses with prompts nested."""
    focus_resp = client.post(f"/api/projects/{project_id}/focuses", json={"name": "F"})
    fid = focus_resp.json()["id"]
    client.post(f"/api/projects/{project_id}/focuses/{fid}/prompts", json={"text": "P1"})

    resp = client.get(f"/api/projects/{project_id}/full")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["focuses"]) == 1
    assert len(data["focuses"][0]["prompts"]) == 1
