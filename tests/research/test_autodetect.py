"""Tests for fp.research.autodetect — domain auto-detection."""
from __future__ import annotations

from unittest.mock import patch, AsyncMock
import pytest


@pytest.mark.asyncio
@patch("fp.research.autodetect.fetch_exa_batch")
@patch("fp.research.autodetect.completion_json")
async def test_research_brand_returns_structured_data(mock_llm, mock_exa):
    """research_brand should return dict with all Brand fields."""
    from fp.research.autodetect import research_brand

    mock_exa.return_value = [
        {
            "query": "acme.com",
            "results": [
                {"title": "ACME Corp - Enterprise Software", "url": "https://acme.com", "snippet": "ACME provides SaaS analytics"}
            ]
        }
    ]
    mock_llm.return_value = {
        "name": "ACME Corp",
        "description": "Enterprise software solutions",
        "service_categories": ["SaaS", "Analytics"],
        "competitors": ["Zoom", "Slack"],
        "confidence": 0.85
    }

    result = await research_brand("acme.com")

    assert result["name"] == "ACME Corp"
    assert result["description"] == "Enterprise software solutions"
    assert result["website"] == "https://acme.com"
    assert result["service_categories"] == ["SaaS", "Analytics"]
    assert result["competitors"] == ["Zoom", "Slack"]
    assert result["confidence"] == 0.85


@pytest.mark.asyncio
@patch("fp.research.autodetect.fetch_exa_batch")
@patch("fp.research.autodetect.completion_json")
async def test_research_brand_website_always_https(mock_llm, mock_exa):
    """website field should always start with https://."""
    from fp.research.autodetect import research_brand

    mock_exa.return_value = []
    mock_llm.return_value = {
        "name": "Test Co",
        "description": "Test",
        "service_categories": [],
        "competitors": [],
        "confidence": 0.3
    }

    result = await research_brand("test.com")
    assert result["website"] == "https://test.com"


@pytest.mark.asyncio
@patch("fp.research.autodetect.fetch_exa_batch")
@patch("fp.research.autodetect.completion_json")
async def test_research_brand_low_confidence_when_no_exa(mock_llm, mock_exa):
    """Confidence should be LOW when EXA returns no results."""
    from fp.research.autodetect import research_brand

    mock_exa.return_value = []
    mock_llm.return_value = {
        "name": "Unknown Co",
        "description": "Unknown",
        "service_categories": [],
        "competitors": [],
        "confidence": 0.2
    }

    result = await research_brand("unknown.com")
    assert result["confidence"] < 0.4
