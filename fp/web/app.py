"""FastAPI app factory for focus-prompt web UI."""
from __future__ import annotations

from fastapi import FastAPI
from fastapi.templating import Jinja2Templates
from pathlib import Path

from fp.config import load_user_config

TEMPLATES_DIR = Path(__file__).parent / "templates"


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    # Load user config into env on startup
    load_user_config()

    app = FastAPI(title="Focus Prompt", docs_url=None, redoc_url=None)

    # Mount templates
    app.state.templates = Jinja2Templates(directory=str(TEMPLATES_DIR))
    from fastapi.staticfiles import StaticFiles
    STATIC_DIR = Path(__file__).parent / "static"
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

    # Register routes
    from fp.web.routes.pages import router as pages_router
    from fp.web.routes.pipeline import router as pipeline_router
    from fp.web.routes.settings import router as settings_router
    from fp.web.routes.projects import router as projects_router

    app.include_router(pages_router)
    app.include_router(pipeline_router, prefix="/api")
    app.include_router(settings_router, prefix="/api")
    app.include_router(projects_router, prefix="/api")

    return app


def main():
    """Entry point for fp-web command."""
    import uvicorn

    uvicorn.run(create_app(), host="127.0.0.1", port=8000)
