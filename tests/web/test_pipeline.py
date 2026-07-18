"""Tests for fp.web.routes.pipeline — HTMX partial routes for pipeline steps."""
from __future__ import annotations

from unittest.mock import MagicMock, patch, AsyncMock

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.testclient import TestClient
from starlette.requests import Request


def _make_app():
    """Create a minimal FastAPI app with mocked templates and pipeline router."""
    app = FastAPI()

    # Mock templates — return a real HTMLResponse so Starlette can serialize it
    mock_templates = MagicMock()
    mock_templates.TemplateResponse.return_value = HTMLResponse("<html>ok</html>")
    app.state.templates = mock_templates

    from fp.web.routes.pipeline import router
    app.include_router(router)

    return app, mock_templates


# ── GET tab routes ────────────────────────────────────────────────────────────


@patch("fp.web.routes.pipeline.get_state")
def test_research_tab_returns_html(mock_get_state):
    """GET /pipeline/research should return an HTML partial."""
    mock_get_state.return_value = {"brand": "test"}
    app, mock_templates = _make_app()
    client = TestClient(app)

    response = client.get("/pipeline/research")

    assert response.status_code == 200
    mock_templates.TemplateResponse.assert_called_once()
    call_args = mock_templates.TemplateResponse.call_args
    # Starlette 1.3+ API: TemplateResponse(request, name, context)
    assert isinstance(call_args[0][0], Request)  # request object
    assert call_args[0][1] == "partials/research.html"


@patch("fp.web.routes.pipeline.get_state")
def test_discover_tab_returns_html(mock_get_state):
    """GET /pipeline/discover should return an HTML partial."""
    mock_get_state.return_value = {"brand": "test"}
    app, mock_templates = _make_app()
    client = TestClient(app)

    response = client.get("/pipeline/discover")

    assert response.status_code == 200
    mock_templates.TemplateResponse.assert_called_once()
    call_args = mock_templates.TemplateResponse.call_args
    assert isinstance(call_args[0][0], Request)
    assert call_args[0][1] == "partials/discover.html"


@patch("fp.web.routes.pipeline.get_state")
def test_generate_tab_returns_html(mock_get_state):
    """GET /pipeline/generate should return an HTML partial."""
    mock_get_state.return_value = {"brand": "test"}
    app, mock_templates = _make_app()
    client = TestClient(app)

    response = client.get("/pipeline/generate")

    assert response.status_code == 200
    mock_templates.TemplateResponse.assert_called_once()
    call_args = mock_templates.TemplateResponse.call_args
    assert isinstance(call_args[0][0], Request)
    assert call_args[0][1] == "partials/generate.html"


@patch("fp.web.routes.pipeline.get_state")
def test_score_tab_returns_html(mock_get_state):
    """GET /pipeline/score should return an HTML partial."""
    mock_get_state.return_value = {"brand": "test"}
    app, mock_templates = _make_app()
    client = TestClient(app)

    response = client.get("/pipeline/score")

    assert response.status_code == 200
    mock_templates.TemplateResponse.assert_called_once()
    call_args = mock_templates.TemplateResponse.call_args
    assert isinstance(call_args[0][0], Request)
    assert call_args[0][1] == "partials/score.html"


@patch("fp.web.routes.pipeline.get_state")
def test_export_tab_returns_html(mock_get_state):
    """GET /pipeline/export should return an HTML partial."""
    mock_get_state.return_value = {"brand": "test"}
    app, mock_templates = _make_app()
    client = TestClient(app)

    response = client.get("/pipeline/export")

    assert response.status_code == 200
    mock_templates.TemplateResponse.assert_called_once()
    call_args = mock_templates.TemplateResponse.call_args
    assert isinstance(call_args[0][0], Request)
    assert call_args[0][1] == "partials/export.html"


@patch("fp.web.routes.pipeline.get_state")
def test_tab_routes_pass_state_in_context(mock_get_state):
    """All tab routes should pass state in the template context."""
    state_value = {"brand": "Acme Corp"}
    mock_get_state.return_value = state_value
    app, mock_templates = _make_app()
    client = TestClient(app)

    for step in ["research", "discover", "generate", "score", "export"]:
        mock_templates.reset_mock()
        response = client.get(f"/pipeline/{step}")
        assert response.status_code == 200
        call_args = mock_templates.TemplateResponse.call_args
        # Starlette 1.3+ API: TemplateResponse(request, name, context)
        context = call_args[0][2]
        assert context["state"] == state_value


# ── POST /research ────────────────────────────────────────────────────────────


@patch("fp.web.routes.pipeline.save_state")
@patch("fp.web.routes.pipeline.get_state")
@patch("fp.web.routes.pipeline.research_queries", new_callable=AsyncMock)
def test_run_research_success(mock_research, mock_get_state, mock_save):
    """POST /research should run research and return success HTML."""
    mock_state = MagicMock()
    mock_state.config.brand = "TestBrand"
    mock_get_state.return_value = mock_state

    mock_research.return_value = {
        "autocomplete": ["query1", "query2", "query3", "query4", "query5", "query6"],
        "all_queries": ["query1", "query2"],
        "stats": {"autocomplete_count": 6, "total_queries": 2},
    }

    app, _ = _make_app()
    client = TestClient(app)

    response = client.post("/research")

    assert response.status_code == 200
    assert "Research complete" in response.text
    assert "6 suggestions" in response.text
    mock_save.assert_called_once_with(mock_state)


@patch("fp.web.routes.pipeline.get_state")
def test_run_research_no_project(mock_get_state):
    """POST /research should return error when no project exists."""
    mock_get_state.return_value = None
    app, _ = _make_app()
    client = TestClient(app)

    response = client.post("/research")

    assert response.status_code == 200
    assert "No project found" in response.text


@patch("fp.web.routes.pipeline.save_state")
@patch("fp.web.routes.pipeline.get_state")
@patch("fp.web.routes.pipeline.research_queries", new_callable=AsyncMock)
def test_run_research_with_extra_queries(mock_research, mock_get_state, mock_save):
    """POST /research should parse comma-separated extra queries."""
    mock_state = MagicMock()
    mock_state.config.brand = "TestBrand"
    mock_get_state.return_value = mock_state

    mock_research.return_value = {
        "autocomplete": ["q1"],
        "all_queries": ["q1"],
        "stats": {"autocomplete_count": 1, "total_queries": 1},
    }

    app, _ = _make_app()
    client = TestClient(app)

    response = client.post("/research", data={"extra": "seed1, seed2"})

    assert response.status_code == 200
    call_kwargs = mock_research.call_args
    assert call_kwargs[1]["extra_queries"] == ["seed1", "seed2"]


@patch("fp.web.routes.pipeline.get_state")
@patch("fp.web.routes.pipeline.research_queries", new_callable=AsyncMock)
def test_run_research_error_handling(mock_research, mock_get_state):
    """POST /research should handle exceptions gracefully."""
    mock_state = MagicMock()
    mock_state.config.brand = "TestBrand"
    mock_get_state.return_value = mock_state

    mock_research.side_effect = RuntimeError("API error")

    app, _ = _make_app()
    client = TestClient(app)

    response = client.post("/research")

    assert response.status_code == 200
    assert "Error" in response.text
    assert "API error" in response.text


# ── POST /discover ────────────────────────────────────────────────────────────


@patch("fp.web.routes.pipeline.save_state")
@patch("fp.web.routes.pipeline.get_state")
@patch("fp.web.routes.pipeline.discover_problems_enriched", new_callable=AsyncMock)
@patch("fp.web.routes.pipeline.generate_focuses")
def test_run_discover_with_web_data(mock_gen_focuses, mock_enriched, mock_get_state, mock_save):
    """POST /discover should use enriched discovery when web data exists."""
    mock_state = MagicMock()
    mock_state.config.brand = "TestBrand"
    mock_state.web_data = {"stats": {"total_queries": 5}}
    mock_get_state.return_value = mock_state

    mock_focus = MagicMock()
    mock_focus.name = "Focus 1"
    mock_focus.signal_count = 3
    mock_gen_focuses.return_value = [mock_focus]
    mock_enriched.return_value = [{"category": "test", "problems": []}]

    app, _ = _make_app()
    client = TestClient(app)

    response = client.post("/discover")

    assert response.status_code == 200
    assert "Discovered 1 focuses" in response.text
    mock_save.assert_called_once_with(mock_state)


@patch("fp.web.routes.pipeline.get_state")
def test_run_discover_no_project(mock_get_state):
    """POST /discover should return error when no project exists."""
    mock_get_state.return_value = None
    app, _ = _make_app()
    client = TestClient(app)

    response = client.post("/discover")

    assert response.status_code == 200
    assert "No project found" in response.text


# ── POST /generate ────────────────────────────────────────────────────────────


@patch("fp.web.routes.pipeline.save_state")
@patch("fp.web.routes.pipeline.get_state")
@patch("fp.web.routes.pipeline.generate_all_prompts")
def test_run_generate_success(mock_gen_prompts, mock_get_state, mock_save):
    """POST /generate should generate prompts and return success HTML."""
    mock_state = MagicMock()
    mock_state.config.brand = "TestBrand"
    mock_state.config.prompt_mode = "unbranded"
    mock_focus = MagicMock()
    mock_focus.prompts = [MagicMock(), MagicMock()]
    mock_state.focuses = [mock_focus]
    mock_get_state.return_value = mock_state

    updated_focus = MagicMock()
    updated_focus.prompts = [MagicMock(), MagicMock(), MagicMock()]
    mock_gen_prompts.return_value = [updated_focus]

    app, _ = _make_app()
    client = TestClient(app)

    response = client.post("/generate")

    assert response.status_code == 200
    assert "Generated 3 prompts" in response.text
    mock_save.assert_called_once_with(mock_state)


@patch("fp.web.routes.pipeline.get_state")
def test_run_generate_no_focuses(mock_get_state):
    """POST /generate should return error when no focuses exist."""
    mock_state = MagicMock()
    mock_state.focuses = []
    mock_get_state.return_value = mock_state

    app, _ = _make_app()
    client = TestClient(app)

    response = client.post("/generate")

    assert response.status_code == 200
    assert "No focuses" in response.text


@patch("fp.web.routes.pipeline.get_state")
def test_run_generate_no_project(mock_get_state):
    """POST /generate should return error when no project exists."""
    mock_get_state.return_value = None
    app, _ = _make_app()
    client = TestClient(app)

    response = client.post("/generate")

    assert response.status_code == 200
    assert "No focuses" in response.text


# ── POST /score ───────────────────────────────────────────────────────────────


@patch("fp.web.routes.pipeline.save_state")
@patch("fp.web.routes.pipeline.get_state")
@patch("fp.web.routes.pipeline.score_all")
def test_run_score_success(mock_score_all, mock_get_state, mock_save):
    """POST /score should score prompts and return success HTML."""
    mock_state = MagicMock()
    mock_state.config.brand = "TestBrand"
    mock_focus = MagicMock()
    mock_focus.prompts = [MagicMock(needs_review=False), MagicMock(needs_review=True)]
    mock_state.focuses = [mock_focus]
    mock_get_state.return_value = mock_state

    scored_focus = MagicMock()
    scored_focus.prompts = [MagicMock(needs_review=False), MagicMock(needs_review=True)]
    mock_score_all.return_value = [scored_focus]

    app, _ = _make_app()
    client = TestClient(app)

    response = client.post("/score")

    assert response.status_code == 200
    assert "Scoring complete" in response.text
    assert "2 prompts scored" in response.text
    mock_save.assert_called_once_with(mock_state)


@patch("fp.web.routes.pipeline.get_state")
def test_run_score_no_focuses(mock_get_state):
    """POST /score should return error when no focuses exist."""
    mock_state = MagicMock()
    mock_state.focuses = []
    mock_get_state.return_value = mock_state

    app, _ = _make_app()
    client = TestClient(app)

    response = client.post("/score")

    assert response.status_code == 200
    assert "No focuses" in response.text


@patch("fp.web.routes.pipeline.get_state")
def test_run_score_no_prompts(mock_get_state):
    """POST /score should return error when focuses have no prompts."""
    mock_state = MagicMock()
    mock_focus = MagicMock()
    mock_focus.prompts = []
    mock_state.focuses = [mock_focus]
    mock_get_state.return_value = mock_state

    app, _ = _make_app()
    client = TestClient(app)

    response = client.post("/score")

    assert response.status_code == 200
    assert "No prompts to score" in response.text


# ── POST /export ──────────────────────────────────────────────────────────────


@patch("fp.web.routes.pipeline.export_json")
@patch("fp.web.routes.pipeline.get_state")
def test_run_export_json(mock_get_state, mock_export_json):
    """POST /export should export JSON and return success HTML."""
    mock_state = MagicMock()
    mock_state.focuses = [MagicMock(prompts=[MagicMock()])]
    mock_get_state.return_value = mock_state
    mock_export_json.return_value = "fp-export.json"

    app, _ = _make_app()
    client = TestClient(app)

    response = client.post("/export", data={"fmt": "json"})

    assert response.status_code == 200
    assert "Exported to fp-export.json" in response.text


@patch("fp.web.routes.pipeline.export_csv")
@patch("fp.web.routes.pipeline.get_state")
def test_run_export_csv(mock_get_state, mock_export_csv):
    """POST /export should export CSV when fmt=csv."""
    mock_state = MagicMock()
    mock_state.focuses = [MagicMock(prompts=[MagicMock()])]
    mock_get_state.return_value = mock_state
    mock_export_csv.return_value = "fp-export.csv"

    app, _ = _make_app()
    client = TestClient(app)

    response = client.post("/export", data={"fmt": "csv"})

    assert response.status_code == 200
    assert "Exported to fp-export.csv" in response.text


@patch("fp.web.routes.pipeline.get_state")
def test_run_export_no_project(mock_get_state):
    """POST /export should return error when no project exists."""
    mock_get_state.return_value = None
    app, _ = _make_app()
    client = TestClient(app)

    response = client.post("/export")

    assert response.status_code == 200
    assert "No project found" in response.text


# ── Router integration ────────────────────────────────────────────────────────


@patch("fp.web.routes.pipeline.get_state")
def test_all_pipeline_routes_registered(mock_get_state):
    """All 5 tab routes should be registered and accessible via GET."""
    mock_get_state.return_value = {"brand": "test"}
    app, _ = _make_app()
    client = TestClient(app)

    for step in ["research", "discover", "generate", "score", "export"]:
        response = client.get(f"/pipeline/{step}")
        assert response.status_code != 405, f"/pipeline/{step} should be registered for GET"


@patch("fp.web.routes.pipeline.get_state")
def test_all_action_routes_registered(mock_get_state):
    """All 5 action routes should be registered and accessible via POST."""
    mock_state = MagicMock()
    mock_state.focuses = []
    mock_get_state.return_value = mock_state
    app, _ = _make_app()
    client = TestClient(app)

    for action in ["research", "discover", "generate", "score", "export"]:
        response = client.post(f"/{action}")
        assert response.status_code != 405, f"/{action} should be registered for POST"
