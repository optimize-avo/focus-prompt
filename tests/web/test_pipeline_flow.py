"""Task 7: Full pipeline flow and edge-case tests for the wizard."""
from __future__ import annotations

import json
from unittest.mock import MagicMock, patch, AsyncMock

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.testclient import TestClient
from starlette.requests import Request


def _make_app():
    """Create a minimal FastAPI app with mocked templates and pipeline router."""
    app = FastAPI()

    mock_templates = MagicMock()
    mock_templates.TemplateResponse.return_value = HTMLResponse("<html>ok</html>")
    app.state.templates = mock_templates

    from fp.web.routes.pipeline import router
    app.include_router(router)

    return app, mock_templates


def _mock_state():
    """Build a MagicMock that behaves like a fully-populated ProjectState."""
    state = MagicMock()

    # brand config
    state.config.brand = "TestBrand"
    state.config.prompt_mode.value = "unbranded"
    state.config.language = "id"

    # research data
    state.web_data = {
        "autocomplete": [
            "jasa desain murah",
            "platform desain terbaik",
            "tool desain grafis",
            "software desain gratis",
            "aplikasi desain profesional",
        ],
        "all_queries": [
            "jasa desain murah",
            "platform desain terbaik",
            "tool desain grafis",
            "software desain gratis",
            "aplikasi desain profesional",
        ],
        "stats": {"autocomplete_count": 5, "total_queries": 5},
    }

    # focuses with prompts
    focus1 = MagicMock()
    focus1.name = "Desain Grafis"
    focus1.signal_count = 5
    prompt1 = MagicMock()
    prompt1.text = "jasa desain grafis murah untuk UMKM"
    prompt1.overall_score = 0.85
    prompt1.service_match = 0.9
    prompt1.mention_likelihood = 0.8
    prompt1.needs_review = False
    prompt2 = MagicMock()
    prompt2.text = "platform desain gratis untuk pemula"
    prompt2.overall_score = 0.72
    prompt2.service_match = 0.7
    prompt2.mention_likelihood = 0.74
    prompt2.needs_review = False
    focus1.prompts = [prompt1, prompt2]

    focus2 = MagicMock()
    focus2.name = "Branding Bisnis"
    focus2.signal_count = 3
    prompt3 = MagicMock()
    prompt3.text = "jasa branding murah untuk startup"
    prompt3.overall_score = 0.65
    prompt3.service_match = 0.6
    prompt3.mention_likelihood = 0.7
    prompt3.needs_review = True
    focus2.prompts = [prompt3]

    state.focuses = [focus1, focus2]
    state.step_selections = {}

    return state


# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 1: Full Pipeline Flow Integration Tests
# ═══════════════════════════════════════════════════════════════════════════════


class TestFullPipelineFlow:
    """Simulate running through every pipeline step end-to-end."""

    @patch("fp.web.routes.pipeline.save_state")
    @patch("fp.web.routes.pipeline.get_state")
    @patch("fp.web.routes.pipeline.research_queries", new_callable=AsyncMock)
    def test_research_step_returns_results(
        self, mock_research, mock_get_state, mock_save
    ):
        """Step 1: Research should return results with HX-Trigger."""
        mock_state = MagicMock()
        mock_state.config.brand = "TestBrand"
        mock_get_state.return_value = mock_state

        mock_research.return_value = {
            "autocomplete": ["jasa desain murah", "platform desain terbaik"],
            "all_queries": ["jasa desain murah"],
            "stats": {"autocomplete_count": 2, "total_queries": 2},
        }

        app, mock_templates = _make_app()
        client = TestClient(app)

        response = client.post("/research")

        assert response.status_code == 200
        mock_templates.TemplateResponse.assert_called_once()
        call_args = mock_templates.TemplateResponse.call_args
        assert call_args[0][1] == "partials/research.html"
        trigger = json.loads(response.headers["HX-Trigger"])
        assert trigger["phaseComplete"]["phase"] == "research"
        assert trigger["phaseComplete"]["completed"] is True
        mock_save.assert_called_once()

    @patch("fp.web.routes.pipeline.save_state")
    @patch("fp.web.routes.pipeline.get_state")
    @patch("fp.web.routes.pipeline.discover_problems_enriched", new_callable=AsyncMock)
    @patch("fp.web.routes.pipeline.generate_focuses")
    def test_discover_step_uses_enriched_data(
        self, mock_gen_focuses, mock_enriched, mock_get_state, mock_save
    ):
        """Step 2: Discover should use enriched discovery when web_data exists."""
        mock_state = _mock_state()
        mock_get_state.return_value = mock_state

        mock_focus = MagicMock()
        mock_focus.name = "Focus 1"
        mock_focus.signal_count = 3
        mock_gen_focuses.return_value = [mock_focus]
        mock_enriched.return_value = [{"category": "test", "problems": []}]

        app, mock_templates = _make_app()
        client = TestClient(app)

        response = client.post("/discover")

        assert response.status_code == 200
        mock_enriched.assert_called_once()
        mock_gen_focuses.assert_called_once()
        trigger = json.loads(response.headers["HX-Trigger"])
        assert trigger["phaseComplete"]["phase"] == "discover"

    @patch("fp.web.routes.pipeline.save_state")
    @patch("fp.web.routes.pipeline.get_state")
    @patch("fp.web.routes.pipeline.generate_all_prompts")
    def test_generate_step_produces_prompts(
        self, mock_gen_prompts, mock_get_state, mock_save
    ):
        """Step 3: Generate should produce prompts for each focus."""
        mock_state = _mock_state()
        mock_get_state.return_value = mock_state

        updated_focus = MagicMock()
        updated_focus.prompts = [MagicMock(), MagicMock(), MagicMock()]
        mock_gen_prompts.return_value = [updated_focus]

        app, mock_templates = _make_app()
        client = TestClient(app)

        response = client.post("/generate")

        assert response.status_code == 200
        mock_gen_prompts.assert_called_once()
        trigger = json.loads(response.headers["HX-Trigger"])
        assert trigger["phaseComplete"]["phase"] == "generate"

    @patch("fp.web.routes.pipeline.save_state")
    @patch("fp.web.routes.pipeline.get_state")
    @patch("fp.web.routes.pipeline.score_all")
    def test_score_step_scores_all_prompts(
        self, mock_score_all, mock_get_state, mock_save
    ):
        """Step 4: Score should score all prompts."""
        mock_state = _mock_state()
        mock_get_state.return_value = mock_state

        scored_focus = MagicMock()
        scored_focus.prompts = [MagicMock(needs_review=False)]
        mock_score_all.return_value = [scored_focus]

        app, mock_templates = _make_app()
        client = TestClient(app)

        response = client.post("/score")

        assert response.status_code == 200
        mock_score_all.assert_called_once()
        trigger = json.loads(response.headers["HX-Trigger"])
        assert trigger["phaseComplete"]["phase"] == "score"

    @patch("fp.web.routes.pipeline.export_json")
    @patch("fp.web.routes.pipeline.get_state")
    def test_export_step_json(self, mock_get_state, mock_export_json):
        """Step 5: Export should produce a JSON file."""
        mock_state = _mock_state()
        mock_get_state.return_value = mock_state
        mock_export_json.return_value = "fp-export.json"

        app, mock_templates = _make_app()
        client = TestClient(app)

        response = client.post("/export", data={"fmt": "json"})

        assert response.status_code == 200
        mock_export_json.assert_called_once()
        trigger = json.loads(response.headers["HX-Trigger"])
        assert trigger["phaseComplete"]["phase"] == "export"

    @patch("fp.web.routes.pipeline.export_csv")
    @patch("fp.web.routes.pipeline.get_state")
    def test_export_step_csv(self, mock_get_state, mock_export_csv):
        """Step 5: Export should produce a CSV file."""
        mock_state = _mock_state()
        mock_get_state.return_value = mock_state
        mock_export_csv.return_value = "fp-export.csv"

        app, mock_templates = _make_app()
        client = TestClient(app)

        response = client.post("/export", data={"fmt": "csv"})

        assert response.status_code == 200
        mock_export_csv.assert_called_once()
        trigger = json.loads(response.headers["HX-Trigger"])
        assert trigger["phaseComplete"]["phase"] == "export"

    @patch("fp.web.routes.pipeline.get_state")
    def test_full_pipeline_tab_navigation(self, mock_get_state):
        """All 5 tabs should be accessible via GET."""
        mock_get_state.return_value = _mock_state()
        app, _ = _make_app()
        client = TestClient(app)

        for step in ["research", "discover", "generate", "score", "export"]:
            response = client.get(f"/pipeline/{step}")
            assert response.status_code == 200, f"GET /pipeline/{step} failed"

    @patch("fp.web.routes.pipeline.get_state")
    def test_all_action_routes_registered(self, mock_get_state):
        """All 5 action POST routes should be registered."""
        mock_get_state.return_value = _mock_state()
        app, _ = _make_app()
        client = TestClient(app)

        for action in ["research", "discover", "generate", "score", "export"]:
            response = client.post(f"/{action}")
            assert response.status_code != 405, f"POST /{action} not registered"


# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 2: Edge Case Tests
# ═══════════════════════════════════════════════════════════════════════════════


class TestEdgeCases:
    """Edge-case and boundary-condition tests."""

    # ── Research edge cases ─────────────────────────────────────────────

    @patch("fp.web.routes.pipeline.save_state")
    @patch("fp.web.routes.pipeline.get_state")
    @patch("fp.web.routes.pipeline.research_queries", new_callable=AsyncMock)
    def test_research_with_no_extra_queries(
        self, mock_research, mock_get_state, mock_save
    ):
        """Research with empty extra queries should still work."""
        mock_state = MagicMock()
        mock_state.config.brand = "TestBrand"
        mock_get_state.return_value = mock_state

        mock_research.return_value = {
            "autocomplete": ["query1"],
            "all_queries": ["query1"],
            "stats": {"autocomplete_count": 1, "total_queries": 1},
        }

        app, _ = _make_app()
        client = TestClient(app)

        # POST with empty extra field
        response = client.post("/research", data={"extra": ""})

        assert response.status_code == 200
        mock_research.assert_called_once()
        call_kwargs = mock_research.call_args
        assert call_kwargs[1]["extra_queries"] is None

    @patch("fp.web.routes.pipeline.save_state")
    @patch("fp.web.routes.pipeline.get_state")
    @patch("fp.web.routes.pipeline.research_queries", new_callable=AsyncMock)
    def test_research_with_whitespace_extra_queries(
        self, mock_research, mock_get_state, mock_save
    ):
        """Research with only whitespace extra queries should pass None."""
        mock_state = MagicMock()
        mock_state.config.brand = "TestBrand"
        mock_get_state.return_value = mock_state

        mock_research.return_value = {
            "autocomplete": ["query1"],
            "all_queries": ["query1"],
            "stats": {"autocomplete_count": 1, "total_queries": 1},
        }

        app, _ = _make_app()
        client = TestClient(app)

        response = client.post("/research", data={"extra": "  ,  ,  "})

        assert response.status_code == 200
        call_kwargs = mock_research.call_args
        assert call_kwargs[1]["extra_queries"] is None

    # ── Discover edge cases ─────────────────────────────────────────────

    @patch("fp.web.routes.pipeline.save_state")
    @patch("fp.web.routes.pipeline.get_state")
    @patch("fp.web.routes.pipeline.discover_problems_enriched", new_callable=AsyncMock)
    @patch("fp.web.routes.pipeline.generate_focuses")
    def test_discover_without_web_data_falls_back(
        self, mock_gen_focuses, mock_enriched, mock_get_state, mock_save
    ):
        """Discover should fall back to non-enriched discovery when no web_data."""
        mock_state = MagicMock()
        mock_state.config.brand = "TestBrand"
        mock_state.web_data = None
        mock_get_state.return_value = mock_state

        from fp.enrichment.problems import discover_problems

        with patch(
            "fp.web.routes.pipeline.discover_problems", wraps=discover_problems
        ) as mock_basic:
            mock_basic.return_value = [{"category": "test"}]

            mock_focus = MagicMock()
            mock_focus.name = "Focus 1"
            mock_gen_focuses.return_value = [mock_focus]

            app, _ = _make_app()
            client = TestClient(app)

            response = client.post("/discover")

            assert response.status_code == 200
            mock_enriched.assert_not_called()

    @patch("fp.web.routes.pipeline.get_state")
    def test_discover_no_problems_found(self, mock_get_state):
        """Discover with no problems should return error message."""
        mock_state = MagicMock()
        mock_state.config.brand = "TestBrand"
        mock_state.web_data = {"stats": {"total_queries": 5}}
        mock_get_state.return_value = mock_state

        with patch("fp.web.routes.pipeline.discover_problems_enriched", new_callable=AsyncMock) as mock_enriched:
            mock_enriched.return_value = []

            app, _ = _make_app()
            client = TestClient(app)

            response = client.post("/discover")

            assert response.status_code == 200
            assert "No problems discovered" in response.text

    # ── Generate edge cases ─────────────────────────────────────────────

    @patch("fp.web.routes.pipeline.get_state")
    def test_generate_no_focuses(self, mock_get_state):
        """Generate with empty focuses should return error."""
        mock_state = MagicMock()
        mock_state.focuses = []
        mock_get_state.return_value = mock_state

        app, _ = _make_app()
        client = TestClient(app)

        response = client.post("/generate")

        assert response.status_code == 200
        assert "No focuses" in response.text

    # ── Score edge cases ────────────────────────────────────────────────

    @patch("fp.web.routes.pipeline.get_state")
    def test_score_no_focuses(self, mock_get_state):
        """Score with no focuses should return error."""
        mock_state = MagicMock()
        mock_state.focuses = []
        mock_get_state.return_value = mock_state

        app, _ = _make_app()
        client = TestClient(app)

        response = client.post("/score")

        assert response.status_code == 200
        assert "No focuses" in response.text

    @patch("fp.web.routes.pipeline.get_state")
    def test_score_no_prompts(self, mock_get_state):
        """Score with focuses but no prompts should return error."""
        mock_state = MagicMock()
        focus = MagicMock()
        focus.prompts = []
        mock_state.focuses = [focus]
        mock_get_state.return_value = mock_state

        app, _ = _make_app()
        client = TestClient(app)

        response = client.post("/score")

        assert response.status_code == 200
        assert "No prompts to score" in response.text

    # ── Export edge cases ───────────────────────────────────────────────

    @patch("fp.web.routes.pipeline.get_state")
    def test_export_no_project(self, mock_get_state):
        """Export with no project should return error."""
        mock_get_state.return_value = None

        app, _ = _make_app()
        client = TestClient(app)

        response = client.post("/export")

        assert response.status_code == 200
        assert "No project found" in response.text

    # ── No-project edge cases ───────────────────────────────────────────

    @patch("fp.web.routes.pipeline.get_state")
    def test_research_no_project(self, mock_get_state):
        """Research with no project should return error."""
        mock_get_state.return_value = None

        app, _ = _make_app()
        client = TestClient(app)

        response = client.post("/research")

        assert response.status_code == 200
        assert "No project found" in response.text

    @patch("fp.web.routes.pipeline.get_state")
    def test_discover_no_project(self, mock_get_state):
        """Discover with no project should return error."""
        mock_get_state.return_value = None

        app, _ = _make_app()
        client = TestClient(app)

        response = client.post("/discover")

        assert response.status_code == 200
        assert "No project found" in response.text

    @patch("fp.web.routes.pipeline.get_state")
    def test_generate_no_project(self, mock_get_state):
        """Generate with no project should return error."""
        mock_get_state.return_value = None

        app, _ = _make_app()
        client = TestClient(app)

        response = client.post("/generate")

        assert response.status_code == 200
        assert "No focuses" in response.text

    # ── Selection API edge cases ────────────────────────────────────────

    @patch("fp.web.routes.pipeline.get_state")
    def test_selection_api_no_project(self, mock_get_state):
        """Selection API with no project should return error."""
        mock_get_state.return_value = None

        app, _ = _make_app()
        client = TestClient(app)

        response = client.post(
            "/pipeline/step/research/selection",
            content=json.dumps({"selected_ids": ["q1"]}),
            headers={"Content-Type": "application/json"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "error"
        assert "No project found" in data["message"]

    @patch("fp.web.routes.pipeline.get_state")
    def test_selection_api_empty_ids(self, mock_get_state):
        """Selection API with empty selected_ids should return error."""
        mock_get_state.return_value = _mock_state()

        app, _ = _make_app()
        client = TestClient(app)

        response = client.post(
            "/pipeline/step/research/selection",
            content=json.dumps({"selected_ids": []}),
            headers={"Content-Type": "application/json"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "error"
        assert "Must select at least one" in data["message"]

    @patch("fp.web.routes.pipeline.save_state")
    @patch("fp.web.routes.pipeline.get_state")
    def test_selection_api_research_filters_queries(
        self, mock_get_state, mock_save
    ):
        """Selection API for research should filter autocomplete queries."""
        mock_state = _mock_state()
        mock_get_state.return_value = mock_state

        app, _ = _make_app()
        client = TestClient(app)

        # Keep only first 2 queries
        selected = ["jasa desain murah", "platform desain terbaik"]
        response = client.post(
            "/pipeline/step/research/selection",
            content=json.dumps({"selected_ids": selected}),
            headers={"Content-Type": "application/json"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        mock_save.assert_called_once()

    @patch("fp.web.routes.pipeline.save_state")
    @patch("fp.web.routes.pipeline.get_state")
    def test_selection_api_discover_filters_focuses(
        self, mock_get_state, mock_save
    ):
        """Selection API for discover should filter focuses."""
        mock_state = _mock_state()
        mock_get_state.return_value = mock_state

        app, _ = _make_app()
        client = TestClient(app)

        # Keep only first focus
        response = client.post(
            "/pipeline/step/discover/selection",
            content=json.dumps({"selected_ids": ["Desain Grafis"]}),
            headers={"Content-Type": "application/json"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        mock_save.assert_called_once()

    @patch("fp.web.routes.pipeline.save_state")
    @patch("fp.web.routes.pipeline.get_state")
    def test_selection_api_generate_filters_prompts(
        self, mock_get_state, mock_save
    ):
        """Selection API for generate should filter prompts within focuses."""
        mock_state = _mock_state()
        mock_get_state.return_value = mock_state

        app, _ = _make_app()
        client = TestClient(app)

        # Keep only first prompt of first focus
        selected = ["Desain Grafis-jasa desain grafis murah untuk"]
        response = client.post(
            "/pipeline/step/generate/selection",
            content=json.dumps({"selected_ids": selected}),
            headers={"Content-Type": "application/json"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        mock_save.assert_called_once()

    # ── Items API edge cases ────────────────────────────────────────────

    @patch("fp.web.routes.pipeline.get_state")
    def test_items_api_no_project(self, mock_get_state):
        """Items API with no project should return error."""
        mock_get_state.return_value = None

        app, _ = _make_app()
        client = TestClient(app)

        response = client.get("/pipeline/step/research/items")

        assert response.status_code == 200
        data = response.json()
        assert data["error"] == "No project found"

    @patch("fp.web.routes.pipeline.get_state")
    def test_items_api_research_returns_queries(self, mock_get_state):
        """Items API for research should return queries."""
        mock_state = _mock_state()
        mock_get_state.return_value = mock_state

        app, _ = _make_app()
        client = TestClient(app)

        response = client.get("/pipeline/step/research/items")

        assert response.status_code == 200
        data = response.json()
        assert data["step"] == "research"
        assert data["total"] == 5
        assert data["selected_count"] == 5  # all selected by default

    @patch("fp.web.routes.pipeline.get_state")
    def test_items_api_discover_returns_focuses(self, mock_get_state):
        """Items API for discover should return focus areas."""
        mock_state = _mock_state()
        mock_get_state.return_value = mock_state

        app, _ = _make_app()
        client = TestClient(app)

        response = client.get("/pipeline/step/discover/items")

        assert response.status_code == 200
        data = response.json()
        assert data["step"] == "discover"
        assert data["total"] == 2

    @patch("fp.web.routes.pipeline.get_state")
    def test_items_api_generate_returns_prompts_with_groups(
        self, mock_get_state
    ):
        """Items API for generate should return prompts with group field."""
        mock_state = _mock_state()
        mock_get_state.return_value = mock_state

        app, _ = _make_app()
        client = TestClient(app)

        response = client.get("/pipeline/step/generate/items")

        assert response.status_code == 200
        data = response.json()
        assert data["step"] == "generate"
        assert data["total"] == 3  # 2 + 1 prompts
        # Check that items have group field
        groups = {item["group"] for item in data["items"]}
        assert "Desain Grafis" in groups
        assert "Branding Bisnis" in groups

    @patch("fp.web.routes.pipeline.get_state")
    def test_items_api_score_returns_scored_prompts(self, mock_get_state):
        """Items API for score should return prompts with scores."""
        mock_state = _mock_state()
        mock_get_state.return_value = mock_state

        app, _ = _make_app()
        client = TestClient(app)

        response = client.get("/pipeline/step/score/items")

        assert response.status_code == 200
        data = response.json()
        assert data["step"] == "score"
        assert data["total"] == 3
        # All items should have a score field
        for item in data["items"]:
            assert "score" in item
            assert item["score"] > 0

    # ── Pipeline status API edge cases ──────────────────────────────────

    @patch("fp.web.routes.pipeline.get_state")
    def test_pipeline_status_no_project(self, mock_get_state):
        """Pipeline status with no project should return all false."""
        mock_get_state.return_value = None

        app, _ = _make_app()
        client = TestClient(app)

        response = client.get("/pipeline/status")

        assert response.status_code == 200
        data = response.json()
        for phase in ["research", "discover", "generate", "score"]:
            assert data[phase]["completed"] is False

    @patch("fp.web.routes.pipeline.get_state")
    def test_pipeline_status_all_phases_complete(self, mock_get_state):
        """Pipeline status should show all phases complete when fully done."""
        mock_state = _mock_state()
        mock_get_state.return_value = mock_state

        app, _ = _make_app()
        client = TestClient(app)

        response = client.get("/pipeline/status")

        assert response.status_code == 200
        data = response.json()
        assert data["research"]["completed"] is True
        assert data["discover"]["completed"] is True
        assert data["generate"]["completed"] is True
        assert data["score"]["completed"] is True

    # ── Scores API edge cases ───────────────────────────────────────────

    @patch("fp.web.routes.pipeline.get_state")
    def test_scores_api_empty_when_no_project(self, mock_get_state):
        """Scores API with no project should return empty list."""
        mock_get_state.return_value = None

        app, _ = _make_app()
        client = TestClient(app)

        response = client.get("/pipeline/scores")

        assert response.status_code == 200
        data = response.json()
        assert data == []

    @patch("fp.web.routes.pipeline.get_state")
    def test_scores_api_returns_sorted_scores(self, mock_get_state):
        """Scores API should return prompts sorted by score ascending."""
        mock_state = _mock_state()
        mock_get_state.return_value = mock_state

        app, _ = _make_app()
        client = TestClient(app)

        response = client.get("/pipeline/scores")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3
        # Should be sorted ascending (worst first)
        scores = [item["score"] for item in data]
        assert scores == sorted(scores)

    # ── Keep/Discard API edge cases ─────────────────────────────────────

    @patch("fp.web.routes.pipeline.get_state")
    def test_keep_api_no_project(self, mock_get_state):
        """Keep API with no project should return error."""
        mock_get_state.return_value = None

        app, _ = _make_app()
        client = TestClient(app)

        response = client.post(
            "/pipeline/step/research/keep",
            content=json.dumps({"keep_ids": []}),
            headers={"Content-Type": "application/json"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "error"

    @patch("fp.web.routes.pipeline.save_state")
    @patch("fp.web.routes.pipeline.get_state")
    def test_keep_api_research_empty_set(self, mock_get_state, mock_save):
        """Keep API for research with empty set should return error."""
        mock_state = _mock_state()
        mock_get_state.return_value = mock_state

        app, _ = _make_app()
        client = TestClient(app)

        response = client.post(
            "/pipeline/step/research/keep",
            content=json.dumps({"keep_ids": []}),
            headers={"Content-Type": "application/json"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "error"

    @patch("fp.web.routes.pipeline.save_state")
    @patch("fp.web.routes.pipeline.get_state")
    def test_keep_api_discover_filters_focuses(self, mock_get_state, mock_save):
        """Keep API for discover should keep only specified focuses."""
        mock_state = _mock_state()
        mock_get_state.return_value = mock_state

        app, _ = _make_app()
        client = TestClient(app)

        response = client.post(
            "/pipeline/step/discover/keep",
            content=json.dumps({"keep_ids": ["Desain Grafis"]}),
            headers={"Content-Type": "application/json"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["kept"] == 1
        assert data["discarded"] == 1

    # ── Regenerate API edge cases ───────────────────────────────────────

    @patch("fp.web.routes.pipeline.get_state")
    def test_regenerate_api_no_project(self, mock_get_state):
        """Regenerate API with no project should return error."""
        mock_get_state.return_value = None

        app, _ = _make_app()
        client = TestClient(app)

        response = client.post(
            "/pipeline/step/research/regenerate",
            content=json.dumps({"regenerate_ids": []}),
            headers={"Content-Type": "application/json"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "error"

    # ── SSE run-all edge cases ──────────────────────────────────────────

    @patch("fp.web.routes.pipeline.get_state")
    def test_run_all_no_project(self, mock_get_state):
        """Run-all with no project should emit error SSE event."""
        mock_get_state.return_value = None

        app, _ = _make_app()
        client = TestClient(app)

        response = client.get("/pipeline/run-all")

        assert response.status_code == 200
        assert "text/event-stream" in response.headers["content-type"]

    # ── Error handling edge cases ───────────────────────────────────────

    @patch("fp.web.routes.pipeline.get_state")
    @patch("fp.web.routes.pipeline.research_queries", new_callable=AsyncMock)
    def test_research_api_error_returns_html(self, mock_research, mock_get_state):
        """Research API error should return HTML error message."""
        mock_state = MagicMock()
        mock_state.config.brand = "TestBrand"
        mock_get_state.return_value = mock_state
        mock_research.side_effect = RuntimeError("API timeout")

        app, _ = _make_app()
        client = TestClient(app)

        response = client.post("/research")

        assert response.status_code == 200
        assert "Error" in response.text
        assert "API timeout" in response.text

    @patch("fp.web.routes.pipeline.get_state")
    @patch("fp.web.routes.pipeline.research_queries", new_callable=AsyncMock)
    def test_research_error_does_not_save(self, mock_research, mock_get_state):
        """Research error should not call save_state."""
        mock_state = MagicMock()
        mock_state.config.brand = "TestBrand"
        mock_get_state.return_value = mock_state
        mock_research.side_effect = RuntimeError("fail")

        app, _ = _make_app()
        client = TestClient(app)

        with patch("fp.web.routes.pipeline.save_state") as mock_save:
            client.post("/research")
            mock_save.assert_not_called()

    # ── Wizard step statuses ────────────────────────────────────────────

    @patch("fp.web.routes.pipeline.get_state")
    def test_phase_status_research_completed(self, mock_get_state):
        """Phase status should show research completed when web_data has queries."""
        from fp.web.routes.pipeline import _phase_status

        mock_state = MagicMock()
        mock_state.web_data = {"stats": {"total_queries": 5}}
        mock_state.focuses = []
        mock_get_state.return_value = mock_state

        status = _phase_status(mock_state)
        assert status["research"]["completed"] is True
        assert status["research"]["count"] == 5

    @patch("fp.web.routes.pipeline.get_state")
    def test_phase_status_research_not_completed(self, mock_get_state):
        """Phase status should show research not completed when no web_data."""
        from fp.web.routes.pipeline import _phase_status

        mock_state = MagicMock()
        mock_state.web_data = None
        mock_state.focuses = []

        status = _phase_status(mock_state)
        assert status["research"]["completed"] is False

    @patch("fp.web.routes.pipeline.get_state")
    def test_phase_status_score_not_fully_completed(self, mock_get_state):
        """Phase status should show score incomplete when not all prompts scored."""
        from fp.web.routes.pipeline import _phase_status

        mock_state = MagicMock()
        mock_state.web_data = {"stats": {"total_queries": 5}}
        mock_state.focuses = []
        # Focus with prompts - 1 scored, 1 unscored
        focus = MagicMock()
        prompt_scored = MagicMock()
        prompt_scored.overall_score = 0.8
        prompt_unscored = MagicMock()
        prompt_unscored.overall_score = 0.0
        focus.prompts = [prompt_scored, prompt_unscored]
        mock_state.focuses = [focus]

        status = _phase_status(mock_state)
        assert status["score"]["completed"] is False
        assert status["score"]["count"] == 1
        assert status["score"]["total"] == 2
