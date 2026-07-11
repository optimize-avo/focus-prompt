"""Google Autocomplete — fetch real search suggestions people actually type."""
from __future__ import annotations

import json
import re

import httpx


async def fetch_autocomplete(
    query: str,
    lang: str = "id",
    limit: int = 10,
) -> list[str]:
    """Fetch Google Autocomplete suggestions for a query.

    Args:
        query: The seed query (e.g. "jasa desain logo murah")
        lang: Language code for suggestions (default: "id" for Indonesian)
        limit: Max suggestions per query

    Returns:
        List of suggestion strings people actually type into Google.
    """
    url = "https://suggestqueries.google.com/complete/search"
    params = {
        "q": query,
        "hl": lang,
        "client": "hp",
    }
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    }

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(url, params=params, headers=headers)
            resp.raise_for_status()
            text = resp.text

            # Google returns JSONP: window.google.ac.h(["query", [["suggestion", 0, [512,19]], ...]])
            # Extract the JSON array from inside the parentheses
            match = re.search(r'\((.+)\)', text)
            if match:
                data = json.loads(match.group(1))
                # Response format: [query, [[suggestion, score, flags], ...]]
                raw_suggestions = data[1] if len(data) > 1 else []
                # Each suggestion is a list: [text, score, flags]
                suggestions = []
                for item in raw_suggestions:
                    if isinstance(item, list) and len(item) > 0:
                        s = item[0] if isinstance(item[0], str) else str(item[0])
                        # Strip HTML bold tags
                        s = re.sub(r'<[^>]+>', '', s)
                        suggestions.append(s)
                    elif isinstance(item, str):
                        suggestions.append(re.sub(r'<[^>]+>', '', item))
                return suggestions[:limit]
            return []
    except Exception:
        return []


async def fetch_autocomplete_batch(
    queries: list[str],
    lang: str = "id",
    limit_per_query: int = 10,
) -> list[str]:
    """Fetch autocomplete suggestions for multiple queries.

    Args:
        queries: List of seed queries
        lang: Language code
        limit_per_query: Max suggestions per seed query

    Returns:
        Deduplicated list of all suggestions.
    """
    all_suggestions = set()
    for query in queries:
        suggestions = await fetch_autocomplete(query, lang, limit_per_query)
        all_suggestions.update(suggestions)
    return list(all_suggestions)
