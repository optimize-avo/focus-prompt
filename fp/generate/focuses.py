"""Generate focus clusters from discovered problems."""
from __future__ import annotations

import json

from fp.llm import completion_json
from fp.models import Brand, Focus


FOCUS_GENERATION_PROMPT = """You are a topic clustering analyst. Given a brand and a list of real user problems/queries, cluster them into meaningful "focuses" — topic areas that represent what people are actually asking about or searching for.

For each focus, provide:
1. name — short, descriptive name (e.g., "Freelance platform dengan biaya rendah")
2. description — 1 sentence explaining this focus
3. queries — list of the user queries that belong to this cluster

OUTPUT FORMAT — Return JSON:
{{
  "focuses": [
    {{
      "name": "Focus name",
      "description": "Brief description",
      "queries": ["query1", "query2", ...]
    }}
  ]
}}

Rules:
- Name in Indonesian (mix of English/ID is ok, as real users mix them)
- 4-8 focuses total
- Each focus must have at least 3 queries
- Focuses must be mutually exclusive
- Prioritize focuses where this brand's services are a natural fit
- Name must be problem-oriented, not brand-oriented
"""


def generate_focuses(brand: Brand, problems: list[dict], model: str = "") -> list[Focus]:
    """Generate focus clusters from discovered problems using LLM."""
    data = completion_json(
        model=model,
        messages=[
            {"role": "system", "content": FOCUS_GENERATION_PROMPT},
            {"role": "user", "content": json.dumps({
                "brand": brand.name,
                "description": brand.description,
                "service_categories": brand.service_categories,
                "problems": problems,
            }, indent=2)},
        ],
        temperature=0.6,
    )

    focuses = []
    for f in data.get("focuses", []):
        focus = Focus(
            name=f.get("name", "Unnamed Focus"),
            description=f.get("description", ""),
            lens="problem",
            signals=f.get("queries", []),
            signal_count=len(f.get("queries", [])),
        )
        focuses.append(focus)

    return focuses
