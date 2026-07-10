"""Problem discovery — find real user problems/intents around a brand's service categories."""
from __future__ import annotations

import json
from typing import Optional

import httpx
from openai import OpenAI

from fp.models import Brand


PROBLEM_DISCOVERY_PROMPT = """You are a user research analyst. Given a brand and its service categories, identify what real users search for or ask about when they need these services.

For each service category, think about:
1. What problems do users have that lead them to need this service?
2. What specific needs (hire, compare, learn, find) do they express?
3. What pain points (cheap, trusted, fast, quality) do they mention?
4. How do they phrase their search — casual, formal, in Indonesian, in English?

OUTPUT FORMAT — Return a JSON object with this exact structure:
{{
  "problems": [
    {{
      "category": "{service_category_name}",
      "problems": [
        {{
          "pain_point": "high cost / not trusted / hard to find",
          "raw_queries": [
            "real user query 1",
            "real user query 2"
          ]
        }}
      ]
    }}
  ]
}}

Rules:
- Queries must be in mix of Indonesian and English (as real users do)
- Queries must NOT contain the brand name
- Queries must reflect real search/ask patterns — what a user would actually type
- Focus on problem-to-solution queries, not brand-specific queries
- Be specific, not generic — "where to hire video editor for wedding" not "find freelancer"
- Include variety: questions, statements, comparisons
"""


def discover_problems(brand: Brand, client: OpenAI) -> list[dict]:
    """Use LLM to discover real user problems around brand's service categories."""
    categories_str = ", ".join(brand.service_categories) if brand.service_categories else brand.description

    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": PROBLEM_DISCOVERY_PROMPT},
            {"role": "user", "content": json.dumps({
                "brand": brand.name,
                "description": brand.description,
                "service_categories": brand.service_categories,
                "competitors": brand.competitors,
            }, indent=2)},
        ],
        response_format={"type": "json_object"},
        temperature=0.7,
    )

    raw = resp.choices[0].message.content
    data = json.loads(raw)
    return data.get("problems", [])


def discover_problems_web(brand: Brand) -> list[str]:
    """Optional: fetch real user queries from web sources (Reddit, Google PAA, etc.).
    For MVP, this is a placeholder — returns empty list.
    """
    queries = []

    try:
        resp = httpx.get(
            f"https://www.google.com/complete/search",
            params={"q": brand.service_categories[0] if brand.service_categories else brand.name, "hl": "id", "client": "hp"},
            headers={"User-Agent": "Mozilla/5.0"},
            timeout=10,
        )
    except Exception:
        pass

    return queries
