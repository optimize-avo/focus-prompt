"""Tests for fp.web.app — FastAPI app factory."""
from __future__ import annotations

from unittest.mock import patch

from fastapi.testclient import TestClient


def test_create_app_returns_fastapi_instance():
    """create_app() should return a FastAPI instance with correct title."""
    from fp.web.app import create_app

    app = create_app()
    assert app.title == "Focus Prompt"


def test_create_app_disables_docs():
    """Docs and ReDoc should be disabled in production."""
    from fp.web.app import create_app

    app = create_app()
    assert app.docs_url is None
    assert app.redoc_url is None


def test_create_app_has_templates():
    """App state should have a Jinja2Templates instance."""
    from fp.web.app import create_app

    app = create_app()
    assert hasattr(app.state, "templates")


def test_create_app_registers_page_router():
    """Pages router should be registered (no /api prefix)."""
    from fp.web.app import create_app

    app = create_app()
    client = TestClient(app)
    # Pages router is registered — hitting a nonexistent page should
    # return 404 (not 405 Method Not Allowed), proving the router is active.
    response = client.get("/nonexistent-page")
    assert response.status_code == 404


def test_create_app_registers_pipeline_router_with_prefix():
    """Pipeline routes should be under /api prefix."""
    from fp.web.app import create_app

    app = create_app()
    client = TestClient(app)
    # Pipeline router is registered — GET /api/nonexistent should be 404 not 405
    response = client.get("/api/nonexistent-pipeline")
    assert response.status_code == 404


def test_create_app_registers_settings_router_with_prefix():
    """Settings routes should be under /api prefix."""
    from fp.web.app import create_app

    app = create_app()
    client = TestClient(app)
    # Settings router is registered — GET /api/nonexistent should be 404 not 405
    response = client.get("/api/nonexistent-settings")
    assert response.status_code == 404


def test_create_app_loads_user_config():
    """create_app() should call load_user_config() on startup."""
    from fp.web.app import create_app

    with patch("fp.web.app.load_user_config") as mock_load:
        create_app()
        mock_load.assert_called_once()


def test_templates_dir_exists():
    """The TEMPLATES_DIR should point to an existing directory."""
    from fp.web.app import TEMPLATES_DIR

    assert TEMPLATES_DIR.is_dir()
