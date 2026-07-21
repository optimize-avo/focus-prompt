"""Tests for fp.web.routes.pages — HTML page routes."""
from __future__ import annotations

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
    mock_get_state.return_value = {"brand": "test"}
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
    state_value = {"brand": "Acme Corp"}
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


# ── Router integration ─────────────────────────────────────────────────

@patch("fp.web.routes.pages.get_state")
@patch("fp.web.routes.pages.get_config")
def test_all_routes_registered(mock_get_config, mock_get_state):
    """All 4 page routes should be registered and accessible."""
    mock_get_state.return_value = None
    mock_get_config.return_value = {}
    app, mock_templates = _make_app()
    client = TestClient(app)

    # All 4 page routes should respond (not 405 Method Not Allowed)
    for path in ["/", "/init", "/pipeline", "/settings"]:
        response = client.get(path)
        assert response.status_code != 405, f"{path} should be registered"


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
