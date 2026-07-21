"""EXA Search — fetch semantically related content for enrichment."""
from __future__ import annotations

import os
from dataclasses import dataclass

import httpx
from dotenv import load_dotenv

load_dotenv()


EXA_API_URL = "https://api.exa.ai/search"


@dataclass
class ExaResult:
    """Single EXA search result."""
    title: str
    url: str
    snippet: str
    score: float


async def fetch_exa(
    query: str,
    limit: int = 5,
) -> list[ExaResult]:
    """Fetch EXA search results for a query.

    Args:
        query: The search query
        limit: Max results per query

    Returns:
        List of ExaResult objects.
    """
    api_key = os.getenv("EXA_API_KEY")
    if not api_key:
        return []

    headers = {
        "x-api-key": api_key,
        "Content-Type": "application/json",
    }
    payload = {
        "query": query,
        "type": "auto",
        "numResults": limit,
        "contents": {
            "highlights": True,
        },
    }

    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.post(EXA_API_URL, json=payload, headers=headers)
            resp.raise_for_status()
            data = resp.json()

            results = []
            for item in data.get("results", []):
                highlights = item.get("highlights", [])
                snippet = highlights[0] if highlights else ""
                results.append(ExaResult(
                    title=item.get("title", ""),
                    url=item.get("url", ""),
                    snippet=snippet,
                    score=item.get("score", 0.0),
                ))
            return results
    except Exception:
        return []


async def fetch_exa_batch(
    queries: list[str],
    limit_per_query: int = 5,
) -> list[dict]:
    """Fetch EXA results for multiple queries.

    Args:
        queries: List of search queries
        limit_per_query: Max results per query

    Returns:
        List of dicts: [{"query": "...", "results": [ExaResult, ...]}]
    """
    all_results = []
    for query in queries:
        results = await fetch_exa(query, limit_per_query)
        all_results.append({
            "query": query,
            "results": [vars(r) for r in results],
        })
    return all_results
