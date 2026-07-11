"""Web research orchestrator — fetch real user queries from Google Autocomplete."""
from __future__ import annotations

from fp.models import Brand
from fp.research.autocomplete import fetch_autocomplete_batch


async def research_queries(
    brand: Brand,
    extra_queries: list[str] | None = None,
    include_autocomplete: bool = True,
) -> dict:
    """Research real user queries from Google Autocomplete.

    Args:
        brand: Brand info (name, services, competitors)
        extra_queries: Additional seed queries beyond auto-generated ones
        include_autocomplete: Whether to fetch Google Autocomplete

    Returns:
        Dict with keys:
            - autocomplete: list[str] — Google suggestions
            - all_queries: list[str] — merged, deduplicated query list
            - stats: dict — counts per source
    """
    # Build seed queries from brand info
    seed_queries = []

    # Service category queries
    for cat in brand.service_categories:
        seed_queries.append(cat)
        seed_queries.append(f"jasa {cat} murah")
        seed_queries.append(f"platform {cat} terbaik")
        seed_queries.append(f"cari {cat} terpercaya")

    # Competitor comparison queries
    for comp in brand.competitors[:3]:
        seed_queries.append(f"{comp} vs")
        seed_queries.append(f"review {comp}")
        seed_queries.append(f"alternatif {comp}")

    # Brand-specific seed
    seed_queries.append(f"{brand.name} review")
    seed_queries.append(f"alternatif {brand.name}")

    # Merge with extra queries
    if extra_queries:
        seed_queries.extend(extra_queries)

    # Cap total seed queries
    seed_queries = seed_queries[:20]

    autocomplete_results = []

    if include_autocomplete:
        autocomplete_results = await fetch_autocomplete_batch(seed_queries)

    all_queries = list(set(autocomplete_results))

    stats = {
        "autocomplete_count": len(autocomplete_results),
        "total_queries": len(all_queries),
        "seed_count": len(seed_queries),
    }

    return {
        "autocomplete": autocomplete_results,
        "all_queries": all_queries,
        "stats": stats,
    }
