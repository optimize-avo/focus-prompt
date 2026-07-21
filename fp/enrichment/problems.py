"""Problem discovery — find real user problems/intents around a brand's service categories."""
from __future__ import annotations

import json
import os
from typing import Optional

import httpx

from fp.llm import completion_json
from fp.models import Brand

LANGUAGE_INSTRUCTION = {
    "id": "Queries MUST be in Indonesian (Bahasa Indonesia).",
    "en": "Queries MUST be in English.",
    "mix": "Queries should be in a mix of Indonesian and English (as real users do).",
}

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
      "category": "{{service_category_name}}",
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
- {language_instruction}
- Queries must NOT contain the brand name
- Queries must reflect real search/ask patterns — what a user would actually type
- Focus on problem-to-solution queries, not brand-specific queries
- Be specific, not generic — "where to hire video editor for wedding" not "find freelancer"
- Include variety: questions, statements, comparisons
"""


def discover_problems(brand: Brand, model: str = "", language: str = "id") -> list[dict]:
    """Use LLM to discover real user problems around brand's service categories."""
    categories_str = ", ".join(brand.service_categories) if brand.service_categories else brand.description

    lang_instruction = LANGUAGE_INSTRUCTION.get(language, LANGUAGE_INSTRUCTION["id"])
    system_prompt = PROBLEM_DISCOVERY_PROMPT.format(language_instruction=lang_instruction)
    data = completion_json(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": json.dumps({
                "brand": brand.name,
                "description": brand.description,
                "service_categories": brand.service_categories,
                "competitors": brand.competitors,
            }, indent=2)},
        ],
        temperature=0.7,
    )
    return data.get("problems", [])


def discover_problems_web(brand: Brand) -> list[str]:
    """Optional: fetch real user queries from web sources.
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


ENRICHED_DISCOVERY_PROMPT = """You are a user research analyst. I'm providing you with REAL search data collected from Google Autocomplete and EXA semantic search. This is ground truth — real things people actually search for.

Use this real data as your PRIMARY source. Supplement with your knowledge only where the data has gaps.

For each service category, analyze the real queries and identify:
1. What problems do users have that lead them to need this service?
2. What specific needs (hire, compare, learn, find) do they express?
3. What pain points (cheap, trusted, fast, quality) do they mention?
4. How do they phrase their search — casual, formal, in Indonesian, in English?

OUTPUT FORMAT — Return a JSON object:
{{
  "problems": [
    {{
      "category": "service category name",
      "problems": [
        {{
          "pain_point": "high cost / not trusted / hard to find",
          "raw_queries": [
            "real user query 1",
            "real user query 2"
          ],
          "source": "autocomplete|synthesized"
        }}
      ]
    }}
  ]
}}

Rules:
- {language_instruction}
- PRIORITIZE queries from the real data provided
- Mark each problem's source: autocomplete or synthesized
- Queries must reflect the real search patterns provided
- Be specific, not generic
"""


async def discover_problems_enriched(
    brand: Brand,
    web_data: dict,
    model: str = "",
    language: str = "id",
) -> list[dict]:
    """Discover problems using real web research data as ground truth.

    Args:
        brand: Brand info
        web_data: Output from fp.research.web.research_queries()
        model: LLM model identifier

    Returns:
        List of problem dicts with category, problems, pain_point, raw_queries, source
    """
    # Build context from real data
    autocomplete_sample = web_data.get("autocomplete", [])[:30]
    exa_sample = web_data.get("exa_results", [])[:10]
    all_queries = web_data.get("all_queries", [])[:50]

    real_data_context = {
        "brand": brand.name,
        "description": brand.description,
        "service_categories": brand.service_categories,
        "competitors": brand.competitors,
        "real_data": {
            "autocomplete_suggestions": autocomplete_sample,
            "exa_search_results": exa_sample,
            "merged_queries": all_queries,
            "stats": web_data.get("stats", {}),
        },
    }

    lang_instruction = LANGUAGE_INSTRUCTION.get(language, LANGUAGE_INSTRUCTION["id"])
    system_prompt = ENRICHED_DISCOVERY_PROMPT.format(language_instruction=lang_instruction)
    data = completion_json(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": json.dumps(real_data_context, indent=2, ensure_ascii=False)},
        ],
        temperature=0.5,
    )
    return data.get("problems", [])
