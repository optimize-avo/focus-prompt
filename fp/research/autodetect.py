"""Domain auto-detect — research brand info from domain via EXA + LLM."""
from __future__ import annotations

from fp.research.exa import fetch_exa_batch
from fp.llm import completion_json


SYSTEM_PROMPT = """You are a brand analyst. Given web research data about a domain, extract structured brand information.

Return a JSON object with exactly these keys:
- name: string — the brand/company name
- description: string — one-sentence description of what the brand does
- service_categories: list of strings — the main service/product categories
- competitors: list of strings — 2-5 direct competitor brand names
- confidence: float 0.0-1.0 — how confident you are in this extraction

Rules:
- Be specific about service categories (e.g. "SaaS" not "software")
- Competitors should be real, well-known brands in the same space
- If data is ambiguous, make your best guess and set confidence lower
- confidence HIGH (0.8-1.0): clear brand data from web results
- confidence MEDIUM (0.4-0.79): partial data, some guessing
- confidence LOW (0.0-0.39): minimal data, mostly guessing"""


def _format_exa_results(exa_data: list[dict]) -> str:
    """Format EXA search results into context string for LLM."""
    lines = []
    for batch in exa_data:
        for result in batch.get("results", []):
            title = result.get("title", "")
            snippet = result.get("snippet", "")
            url = result.get("url", "")
            if title or snippet:
                lines.append(f"- {title}: {snippet} [{url}]")
    return "\n".join(lines) if lines else "No web research data available."


async def research_brand(domain: str, model: str = "") -> dict:
    """Research a brand from its domain using EXA + LLM.

    Args:
        domain: The brand's domain (e.g. "acme.com")
        model: LLM model override (default: env FP_MODEL or gpt-4o-mini)

    Returns:
        Dict with keys: name, description, website, service_categories,
        competitors, confidence
    """
    # Step 1: EXA search for brand signals
    queries = [domain, f"{domain} services", f"{domain} competitors"]
    try:
        exa_data = await fetch_exa_batch(queries, limit_per_query=3)
    except Exception:
        exa_data = []

    # Step 2: Format context for LLM
    exa_context = _format_exa_results(exa_data)

    user_prompt = f"""Domain: {domain}

Web research results:
{exa_context}

Extract the brand information for this domain."""

    # Step 3: LLM inference
    try:
        result = completion_json(
            model=model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.3,
        )
    except Exception:
        # LLM failed — return minimal defaults
        return {
            "name": domain.split(".")[0].title(),
            "description": "",
            "website": f"https://{domain}",
            "service_categories": [],
            "competitors": [],
            "confidence": 0.0,
        }

    # Step 4: Normalize and return
    return {
        "name": result.get("name", domain.split(".")[0].title()),
        "description": result.get("description", ""),
        "website": f"https://{domain}",
        "service_categories": result.get("service_categories", []),
        "competitors": result.get("competitors", []),
        "confidence": max(0.0, min(1.0, result.get("confidence", 0.5))),
    }
