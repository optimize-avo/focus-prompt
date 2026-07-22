"""Tests for fp.web.routes.pages — HTML page routes."""
from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.testclient import TestClient
from starlette.requests import Request


def _make_app():
    """Create a minimal FastAPI app with mocked templates and page router."""
    app = FastAPI()

    # Mock templates — return a real HTMLResponse so Starlette can serialize it
    mock_templates = MagicMock()
    mock_templates.TemplateResponse.return_value = HTMLResponse("<html>ok</html>")
    app.state.templates = mock_templates

    from fp.web.routes.pages import router
    app.include_router(router)

    return app, mock_templates


# ── GET / ──────────────────────────────────────────────────────────────

@patch("fp.web.routes.pages.get_state")
def test_index_returns_html_response(mock_get_state):
    """GET / should return an HTML response using index.html template."""
    mock_get_state.return_value = {"brand": "test"}
    app, mock_templates = _make_app()
    client = TestClient(app)

    response = client.get("/")

    assert response.status_code == 200
    mock_templates.TemplateResponse.assert_called_once()
    call_args = mock_templates.TemplateResponse.call_args
    # Starlette 1.3+ API: TemplateResponse(request, name, context)
    assert isinstance(call_args[0][0], Request)  # request object
    assert call_args[0][1] == "index.html"


@patch("fp.web.routes.pages.get_state")
def test_index_passes_state_in_context(mock_get_state):
    """GET / should pass state from get_state() in the template context."""
    state_value = {"brand": "Acme Corp"}
    mock_get_state.return_value = state_value
    app, mock_templates = _make_app()
    client = TestClient(app)

    client.get("/")

    call_args = mock_templates.TemplateResponse.call_args
    # Starlette 1.3+ API: TemplateResponse(request, name, context)
    assert isinstance(call_args[0][0], Request)  # request object
    assert call_args[0][1] == "index.html"
    context = call_args[0][2]
    assert context["state"] == state_value


@patch("fp.web.routes.pages.get_state")
def test_index_passes_none_state_when_no_project(mock_get_state):
    """GET / should pass None state when no project file exists."""
    mock_get_state.return_value = None
    app, mock_templates = _make_app()
    client = TestClient(app)

    client.get("/")

    call_args = mock_templates.TemplateResponse.call_args
    # Starlette 1.3+ API: TemplateResponse(request, name, context)
    context = call_args[0][2]
    assert context["state"] is None


# ── GET /init ─────────────────────────────────────────────────────────

def test_init_page_returns_html_response():
    """GET /init should return an HTML response using init.html template."""
    app, mock_templates = _make_app()
    client = TestClient(app)

    response = client.get("/init")

    assert response.status_code == 200
    mock_templates.TemplateResponse.assert_called_once()
    call_args = mock_templates.TemplateResponse.call_args
    # Starlette 1.3+ API: TemplateResponse(request, name, context)
    assert isinstance(call_args[0][0], Request)  # request object
    assert call_args[0][1] == "init.html"


def test_init_page_passes_request_in_context():
    """GET /init should pass request in the template context."""
    app, mock_templates = _make_app()
    client = TestClient(app)

    client.get("/init")

    call_args = mock_templates.TemplateResponse.call_args
    # Starlette 1.3+ API: request is first arg, not in context
    assert isinstance(call_args[0][0], Request)  # request object


def test_init_page_no_state_or_config():
    """GET /init should not pass state or config in context."""
    app, mock_templates = _make_app()
    client = TestClient(app)

    client.get("/init")

    call_args = mock_templates.TemplateResponse.call_args
    # Starlette 1.3+ API: TemplateResponse(request, name, context)
    # No context arg passed (defaults to None)
    assert len(call_args[0]) == 2  # only request and name, no context


# ── GET /pipeline ──────────────────────────────────────────────────────

@patch("fp.web.routes.pages.get_state")
def test_pipeline_redirects_to_init_when_no_state(mock_get_state):
    """GET /pipeline should redirect to /init when no project state exists."""
    mock_get_state.return_value = None
    app, mock_templates = _make_app()
    client = TestClient(app)

    response = client.get("/pipeline", follow_redirects=False)

    assert response.status_code == 302
    assert response.headers["location"] == "/init"
    mock_templates.TemplateResponse.assert_not_called()


@patch("fp.web.routes.pages.get_state")
def test_pipeline_returns_html_when_state_exists(mock_get_state):
    """GET /pipeline should render pipeline.html when project state exists."""
    mock_get_state.return_value = SimpleNamespace(brand="test", web_data=None, focuses=[])
    app, mock_templates = _make_app()
    client = TestClient(app)

    response = client.get("/pipeline")

    assert response.status_code == 200
    mock_templates.TemplateResponse.assert_called_once()
    call_args = mock_templates.TemplateResponse.call_args
    # Starlette 1.3+ API: TemplateResponse(request, name, context)
    assert isinstance(call_args[0][0], Request)  # request object
    assert call_args[0][1] == "pipeline.html"


@patch("fp.web.routes.pages.get_state")
def test_pipeline_passes_state_in_context(mock_get_state):
    """GET /pipeline should pass state in the template context."""
    state_value = SimpleNamespace(brand="Acme Corp", web_data=None, focuses=[])
    mock_get_state.return_value = state_value
    app, mock_templates = _make_app()
    client = TestClient(app)

    client.get("/pipeline")

    call_args = mock_templates.TemplateResponse.call_args
    # Starlette 1.3+ API: TemplateResponse(request, name, context)
    context = call_args[0][2]
    assert context["state"] == state_value


# ── GET /settings ──────────────────────────────────────────────────────

@patch("fp.web.routes.pages.get_config")
def test_settings_returns_html_response(mock_get_config):
    """GET /settings should return an HTML response using settings.html template."""
    mock_get_config.return_value = {"key": "value"}
    app, mock_templates = _make_app()
    client = TestClient(app)

    response = client.get("/settings")

    assert response.status_code == 200
    mock_templates.TemplateResponse.assert_called_once()
    call_args = mock_templates.TemplateResponse.call_args
    # Starlette 1.3+ API: TemplateResponse(request, name, context)
    assert isinstance(call_args[0][0], Request)  # request object
    assert call_args[0][1] == "settings.html"


@patch("fp.web.routes.pages.get_config")
def test_settings_passes_config_in_context(mock_get_config):
    """GET /settings should pass config from get_config() in the template context."""
    config_value = {"api_key": "sk-123"}
    mock_get_config.return_value = config_value
    app, mock_templates = _make_app()
    client = TestClient(app)

    client.get("/settings")

    call_args = mock_templates.TemplateResponse.call_args
    # Starlette 1.3+ API: TemplateResponse(request, name, context)
    context = call_args[0][2]
    assert context["config"] == config_value


# ── POST /init/research ──────────────────────────────────────────────

@patch("fp.web.routes.pages.research_brand")
def test_init_research_returns_html_response(mock_research):
    """POST /init/research should return an HTML response."""
    mock_research.return_value = {
        "name": "ACME Corp",
        "description": "Enterprise software",
        "website": "https://acme.com",
        "service_categories": ["SaaS"],
        "competitors": ["Zoom"],
        "confidence": 0.8,
    }
    app, mock_templates = _make_app()
    client = TestClient(app)

    response = client.post("/init/research", data={"domain": "acme.com"})

    assert response.status_code == 200
    mock_templates.TemplateResponse.assert_called_once()


@patch("fp.web.routes.pages.research_brand")
def test_init_research_passes_brand_in_context(mock_research):
    """POST /init/research should pass brand data in template context."""
    brand_data = {
        "name": "ACME Corp",
        "description": "Enterprise software",
        "website": "https://acme.com",
        "service_categories": ["SaaS"],
        "competitors": ["Zoom"],
        "confidence": 0.8,
    }
    mock_research.return_value = brand_data
    app, mock_templates = _make_app()
    client = TestClient(app)

    client.post("/init/research", data={"domain": "acme.com"})

    call_args = mock_templates.TemplateResponse.call_args
    context = call_args[0][2]
    assert context["brand"] == brand_data


@patch("fp.web.routes.pages.research_brand")
def test_init_research_handles_error_gracefully(mock_research):
    """POST /init/research should return error HTML when research fails."""
    mock_research.side_effect = Exception("EXA API down")
    app, mock_templates = _make_app()
    client = TestClient(app)

    response = client.post("/init/research", data={"domain": "acme.com"})

    assert response.status_code == 200
    assert "error" in response.text.lower() or "failed" in response.text.lower()


# ── Integration: auto-detect flow ─────────────────────────────────────

# ── GET /projects ────────────────────────────────────────────────────

@patch("fp.db.get_prompts")
@patch("fp.db.get_focuses")
@patch("fp.db.list_projects")
def test_projects_returns_html_response(mock_list, mock_focuses, mock_prompts):
    """GET /projects should return an HTML response using projects.html template."""
    mock_list.return_value = []
    app, mock_templates = _make_app()
    client = TestClient(app)

    response = client.get("/projects")

    assert response.status_code == 200
    mock_templates.TemplateResponse.assert_called_once()
    call_args = mock_templates.TemplateResponse.call_args
    assert isinstance(call_args[0][0], Request)
    assert call_args[0][1] == "projects.html"


@patch("fp.db.get_prompts")
@patch("fp.db.get_focuses")
@patch("fp.db.list_projects")
@patch("fp.db.get_active_project_id")
def test_projects_passes_empty_projects_in_context(mock_active, mock_list, mock_focuses, mock_prompts):
    """GET /projects should pass empty projects list when no projects exist."""
    mock_list.return_value = []
    mock_active.return_value = None
    app, mock_templates = _make_app()
    client = TestClient(app)

    client.get("/projects")

    call_args = mock_templates.TemplateResponse.call_args
    context = call_args[0][2]
    assert context["projects"] == []
    assert context["active_project_id"] is None


@patch("fp.db.get_prompts")
@patch("fp.db.get_focuses")
@patch("fp.db.list_projects")
def test_projects_enriches_with_focus_and_prompt_counts(mock_list, mock_focuses, mock_prompts):
    """GET /projects should enrich each project with focus_count and prompt_count."""
    mock_list.return_value = [
        {"id": 1, "name": "Brand A", "description": "Desc", "prompt_mode": "unbranded", "language": "en"},
        {"id": 2, "name": "Brand B", "description": "", "prompt_mode": "branded", "language": "id"},
    ]
    # Project 1 has 2 focuses with 3 prompts total
    mock_focuses.side_effect = lambda pid: (
        [{"id": 10, "name": "f1"}, {"id": 11, "name": "f2"}] if pid == 1
        else [{"id": 20, "name": "f3"}]
    )
    mock_prompts.side_effect = lambda fid: (
        [{"id": 100}, {"id": 101}] if fid == 10
        else [{"id": 102}] if fid == 11
        else [{"id": 200}, {"id": 201}, {"id": 202}]
    )

    app, mock_templates = _make_app()
    client = TestClient(app)

    client.get("/projects")

    call_args = mock_templates.TemplateResponse.call_args
    context = call_args[0][2]
    projects = context["projects"]

    assert len(projects) == 2
    assert projects[0]["focus_count"] == 2
    assert projects[0]["prompt_count"] == 3
    assert projects[1]["focus_count"] == 1
    assert projects[1]["prompt_count"] == 3


@patch("fp.db.get_prompts")
@patch("fp.db.get_focuses")
@patch("fp.db.list_projects")
def test_projects_passes_project_metadata(mock_list, mock_focuses, mock_prompts):
    """GET /projects should pass original project fields through."""
    mock_list.return_value = [
        {"id": 1, "name": "ACME", "description": "Enterprise", "prompt_mode": "both", "language": "id"},
    ]
    mock_focuses.return_value = []
    mock_prompts.return_value = []

    app, mock_templates = _make_app()
    client = TestClient(app)

    client.get("/projects")

    call_args = mock_templates.TemplateResponse.call_args
    context = call_args[0][2]
    p = context["projects"][0]
    assert p["name"] == "ACME"
    assert p["description"] == "Enterprise"
    assert p["prompt_mode"] == "both"
    assert p["language"] == "id"


@patch("fp.db.get_prompts")
@patch("fp.db.get_focuses")
@patch("fp.db.list_projects")
@patch("fp.db.get_active_project_id")
def test_projects_passes_active_project_id(mock_active, mock_list, mock_focuses, mock_prompts):
    """GET /projects should pass the active project id to the template."""
    mock_list.return_value = [
        {"id": 1, "name": "A", "description": "", "prompt_mode": "unbranded", "language": "en"},
        {"id": 2, "name": "B", "description": "", "prompt_mode": "unbranded", "language": "en"},
    ]
    mock_active.return_value = 2
    mock_focuses.return_value = []
    mock_prompts.return_value = []

    app, mock_templates = _make_app()
    client = TestClient(app)

    client.get("/projects")

    call_args = mock_templates.TemplateResponse.call_args
    context = call_args[0][2]
    assert context["active_project_id"] == 2


# ── Router integration ─────────────────────────────────────────────────

@patch("fp.db.get_prompts")
@patch("fp.db.get_focuses")
@patch("fp.db.list_projects")
@patch("fp.db.get_active_project_id")
@patch("fp.web.routes.pages.get_state")
@patch("fp.web.routes.pages.get_config")
def test_all_routes_registered(mock_get_config, mock_get_state, mock_active, mock_list, mock_focuses, mock_prompts):
    """All 5 page routes should be registered and accessible."""
    mock_get_state.return_value = None
    mock_get_config.return_value = {}
    mock_active.return_value = None
    mock_list.return_value = []
    app, mock_templates = _make_app()
    client = TestClient(app)

    # All 5 page routes should respond (not 405 Method Not Allowed)
    for path in ["/", "/init", "/pipeline", "/settings", "/projects"]:
        response = client.get(path)
        assert response.status_code != 405, f"{path} should be registered"


# ── POST /init/research ──────────────────────────────────────────────

@patch("fp.web.routes.pages.research_brand")
@patch("fp.web.routes.pages.save_state")
def test_init_research_then_submit_creates_project(mock_save, mock_research):
    """Full flow: auto-detect returns brand data, user submits form, project created."""
    brand_data = {
        "name": "ACME Corp",
        "description": "Enterprise software",
        "website": "https://acme.com",
        "service_categories": ["SaaS", "Analytics"],
        "competitors": ["Zoom", "Slack"],
        "confidence": 0.85,
    }
    mock_research.return_value = brand_data

    app, mock_templates = _make_app()
    # Register the pipeline router too so /api/init works
    from fp.web.routes.pipeline import router as pipeline_router
    app.include_router(pipeline_router, prefix="/api")
    client = TestClient(app)

    # Step 1: Auto-detect
    response = client.post("/init/research", data={"domain": "acme.com"})
    assert response.status_code == 200

    # Step 2: Submit the review form (simulating user clicking "Create Project")
    response = client.post("/api/init", data={
        "name": "ACME Corp",
        "description": "Enterprise software",
        "website": "https://acme.com",
        "services": "SaaS, Analytics",
        "competitors": "Zoom, Slack",
        "mode": "unbranded",
        "language": "id",
    })
    assert response.status_code == 200
    mock_save.assert_called_once()


# ── GET /projects/{id}/manage ────────────────────────────────────────

@patch("fp.db.get_prompts")
@patch("fp.db.get_focuses")
@patch("fp.db.get_project")
def test_manage_page_returns_html_response(mock_project, mock_focuses, mock_prompts):
    """GET /projects/1/manage should return an HTML response using manage.html template."""
    mock_project.return_value = {"id": 1, "name": "ACME"}
    mock_focuses.return_value = []
    app, mock_templates = _make_app()
    client = TestClient(app)

    response = client.get("/projects/1/manage")

    assert response.status_code == 200
    mock_templates.TemplateResponse.assert_called_once()
    call_args = mock_templates.TemplateResponse.call_args
    assert isinstance(call_args[0][0], Request)
    assert call_args[0][1] == "manage.html"


@patch("fp.db.get_prompts")
@patch("fp.db.get_focuses")
@patch("fp.db.get_project")
def test_manage_page_passes_project_in_context(mock_project, mock_focuses, mock_prompts):
    """GET /projects/1/manage should pass project and focuses in template context."""
    mock_project.return_value = {"id": 1, "name": "ACME", "description": "Enterprise"}
    mock_focuses.return_value = [{"id": 10, "name": "Focus A", "project_id": 1}]
    mock_prompts.return_value = [{"id": 100, "text": "Prompt 1", "focus_id": 10}]
    app, mock_templates = _make_app()
    client = TestClient(app)

    client.get("/projects/1/manage")

    call_args = mock_templates.TemplateResponse.call_args
    context = call_args[0][2]
    assert context["project"]["name"] == "ACME"
    assert len(context["focuses"]) == 1


@patch("fp.db.get_project")
def test_manage_page_redirects_when_project_not_found(mock_project):
    """GET /projects/999/manage should redirect to /projects when project doesn't exist."""
    mock_project.return_value = None
    app, mock_templates = _make_app()
    client = TestClient(app)

    response = client.get("/projects/999/manage", follow_redirects=False)

    assert response.status_code == 302
    assert response.headers["location"] == "/projects"
    mock_templates.TemplateResponse.assert_not_called()


@patch("fp.db.get_prompts")
@patch("fp.db.get_focuses")
@patch("fp.db.get_project")
def test_manage_page_enriches_focuses_with_prompts(mock_project, mock_focuses, mock_prompts):
    """GET /projects/1/manage should attach prompts to each focus."""
    mock_project.return_value = {"id": 1, "name": "ACME"}
    mock_focuses.return_value = [
        {"id": 10, "name": "Focus A"},
        {"id": 11, "name": "Focus B"},
    ]
    mock_prompts.side_effect = lambda fid: (
        [{"id": 100, "text": "P1"}, {"id": 101, "text": "P2"}] if fid == 10
        else [{"id": 200, "text": "P3"}]
    )
    app, mock_templates = _make_app()
    client = TestClient(app)

    client.get("/projects/1/manage")

    call_args = mock_templates.TemplateResponse.call_args
    context = call_args[0][2]
    focuses = context["focuses"]
    assert focuses[0]["prompts"][0]["text"] == "P1"
    assert focuses[0]["prompts"][1]["text"] == "P2"
    assert focuses[1]["prompts"][0]["text"] == "P3"


@patch("fp.db.get_prompts")
@patch("fp.db.get_focuses")
@patch("fp.db.get_project")
def test_manage_page_route_registered(mock_project, mock_focuses, mock_prompts):
    """GET /projects/1/manage should not return 405."""
    mock_project.return_value = {"id": 1, "name": "ACME"}
    mock_focuses.return_value = []
    app, mock_templates = _make_app()
    client = TestClient(app)

    response = client.get("/projects/1/manage")
    assert response.status_code != 405
