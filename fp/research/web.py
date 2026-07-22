"""Web research orchestrator — fetch real user queries from Google Autocomplete and EXA."""
from __future__ import annotations

from fp.models import Brand
from fp.research.autocomplete import fetch_autocomplete_batch
from fp.research.exa import fetch_exa_batch


async def research_queries(
    brand: Brand,
    extra_queries: list[str] | None = None,
    include_autocomplete: bool = True,
    include_exa: bool = True,
    language: str = "id",
) -> dict:
    """Research real user queries from Google Autocomplete and EXA.

    Args:
        brand: Brand info (name, services, competitors)
        extra_queries: Additional seed queries beyond auto-generated ones
        include_autocomplete: Whether to fetch Google Autocomplete
        include_exa: Whether to fetch EXA search results
        language: Language code for seed query patterns ("id", "en", or "mix")

    Returns:
        Dict with keys:
            - autocomplete: list[str] — Google suggestions
            - exa_results: list[dict] — EXA search results per query
            - all_queries: list[str] — merged, deduplicated query list
            - stats: dict — counts per source
    """
    # Language-aware seed query templates
    _seed_templates: dict[str, dict[str, str]] = {
        "id": {
            "affordable_service": "jasa {cat} murah",
            "best_platform": "platform {cat} terbaik",
            "trusted_service": "cari {cat} terpercaya",
            "comp_alt": "alternatif {comp}",
            "brand_alt": "alternatif {brand}",
        },
        "en": {
            "affordable_service": "affordable {cat} service",
            "best_platform": "best {cat} platform",
            "trusted_service": "trusted {cat} service",
            "comp_alt": "alternative to {comp}",
            "brand_alt": "alternative to {brand}",
        },
        "mix": {
            "affordable_service": "affordable {cat} service",
            "best_platform": "platform {cat} terbaik",
            "trusted_service": "trusted {cat} service",
            "comp_alt": "alternatif {comp}",
            "brand_alt": "alternative to {brand}",
        },
    }
    templates = _seed_templates.get(language, _seed_templates["id"])

    # Build seed queries from brand info
    seed_queries = []

    # Service category queries
    for cat in brand.service_categories:
        seed_queries.append(cat)
        seed_queries.append(templates["affordable_service"].format(cat=cat))
        seed_queries.append(templates["best_platform"].format(cat=cat))
        seed_queries.append(templates["trusted_service"].format(cat=cat))

    # Competitor comparison queries
    for comp in brand.competitors[:3]:
        seed_queries.append(f"{comp} vs")
        seed_queries.append(f"review {comp}")
        seed_queries.append(templates["comp_alt"].format(comp=comp))

    # Brand-specific seed
    seed_queries.append(f"{brand.name} review")
    seed_queries.append(templates["brand_alt"].format(brand=brand.name))

    # Merge with extra queries
    if extra_queries:
        seed_queries.extend(extra_queries)

    # Cap total seed queries
    seed_queries = seed_queries[:20]

    autocomplete_results = []
    exa_results = []

    if include_autocomplete:
        autocomplete_results = await fetch_autocomplete_batch(seed_queries, lang=language)

    if include_exa:
        exa_results = await fetch_exa_batch(seed_queries[:10])

    # Merge autocomplete + EXA snippets into all_queries
    all_queries = set(autocomplete_results)
    for exa_item in exa_results:
        for result in exa_item.get("results", []):
            title = result.get("title", "")
            if title:
                all_queries.add(title)

    stats = {
        "autocomplete_count": len(autocomplete_results),
        "exa_count": sum(len(item.get("results", [])) for item in exa_results),
        "total_queries": len(all_queries),
        "seed_count": len(seed_queries),
    }

    return {
        "autocomplete": autocomplete_results,
        "exa_results": exa_results,
        "all_queries": list(all_queries),
        "stats": stats,
    }
