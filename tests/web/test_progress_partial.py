"""Regression tests for the indeterminate progress widget rendered by pipeline partials."""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from fp.models import (
    Brand,
    Focus,
    ProjectConfig,
    ProjectState,
    PromptIntent,
    PromptMode,
    ScoredPrompt,
)
from fp.web.app import create_app
from fp.web.deps import save_state


def _make_state(phase: str) -> ProjectState:
    """Build a ProjectState that triggers the pre-run branch of the given partial."""
    if phase == "research":
        focuses = []
        web_data = None
    elif phase == "discover":
        focuses = []
        web_data = {
            "stats": {"total_queries": 1, "autocomplete_count": 1},
            "autocomplete": ["q1"],
            "all_queries": ["q1"],
        }
    elif phase == "generate":
        focuses = [Focus(name="f1", description="", priority="", prompts=[])]
        web_data = {
            "stats": {"total_queries": 1, "autocomplete_count": 1},
            "autocomplete": ["q1"],
            "all_queries": ["q1"],
        }
    elif phase == "score":
        focuses = [
            Focus(
                name="f1",
                description="",
                priority="",
                prompts=[
                    ScoredPrompt(
                        text="p1",
                        intent=PromptIntent.INFO,
                        mode=PromptMode.UNBRANDED,
                        focus_name="f1",
                    )
                ],
            )
        ]
        web_data = {
            "stats": {"total_queries": 1, "autocomplete_count": 1},
            "autocomplete": ["q1"],
            "all_queries": ["q1"],
        }
    else:
        raise ValueError(f"unknown phase: {phase}")

    return ProjectState(
        config=ProjectConfig(
            brand=Brand(
                name="t",
                description="t",
                service_categories=["x"],
                competitors=[],
            )
        ),
        focuses=focuses,
        web_data=web_data,
    )


@pytest.fixture
def app_factory():
    """Return a callable that builds a TestClient with the given phase state seeded."""
    def _factory(phase: str) -> TestClient:
        save_state(_make_state(phase))
        return TestClient(create_app())
    return _factory


def test_research_partial_contains_progress_widget(app_factory):
    """Research pre-run partial must include the progress widget."""
    c = app_factory("research")
    r = c.get("/pipeline/research")
    assert r.status_code == 200
    body = r.text
    assert 'id="research-progress"' in body
    assert 'data-phase="research"' in body
    assert "Researching queries" in body
    assert "run-progress-fill" in body
    assert "run-progress-elapsed" in body


@pytest.mark.parametrize(
    "phase,label",
    [
        ("discover", "Discovering problems"),
        ("generate", "Generating prompts"),
        ("score", "Scoring prompts"),
    ],
)
def test_pipeline_partials_contain_progress_widget(app_factory, phase, label):
    """Discover/Generate/Score partials each include the progress widget with their own phase id."""
    c = app_factory(phase)
    r = c.get(f"/pipeline/{phase}")
    assert r.status_code == 200
    body = r.text
    assert f'id="{phase}-progress"' in body
    assert f'data-phase="{phase}"' in body
    assert label in body
    assert "run-progress-fill" in body


def test_progress_widget_is_initially_hidden(app_factory):
    """The progress widget must start hidden so it doesn't appear before a request."""
    c = app_factory("research")
    r = c.get("/pipeline/research")
    assert r.status_code == 200
    assert 'class="run-progress hidden' in r.text
