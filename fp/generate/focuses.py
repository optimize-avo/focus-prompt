"""Generate focus clusters from discovered problems."""
from __future__ import annotations

import json

from fp.llm import completion_json
from fp.models import Brand, Focus

LANGUAGE_INSTRUCTION = {
    "id": "Name MUST be in Indonesian (Bahasa Indonesia).",
    "en": "Name MUST be in English.",
    "mix": "Name can be in Indonesian or English (mix is ok, as real users mix them).",
}

FOCUS_GENERATION_PROMPT = """You are a topic clustering analyst. Given a brand, real user problems, and EXA search patterns, cluster them into meaningful "focuses" — topic areas that represent what people are actually asking about.

For each focus, provide:
1. name — EVOCATIVE, specific name that captures the real user pain point
2. description — 1 sentence explaining this focus from user's perspective
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
- {language_instruction}
- 4-8 focuses total
- Each focus must have at least 3 queries
- Focuses must be mutually exclusive
- Prioritize focuses where this brand's services are a natural fit
- Name must be problem-oriented, not brand-oriented

NAME QUALITY RULES (CRITICAL — these determine whether prompts feel natural or templated):
- Use emotional or specific language: "frustrated", "confused", "looking for", "tired of"
- Include concrete details: competitor names, budget ranges, specific scenarios
- Sound like a real person's complaint or question, not a marketing category

EXAMPLES OF GREAT FOCUS NAMES:
✓ "My Competitors Are in ChatGPT — Why Aren't We?"
✓ "AI Visibility Tools Under $100/Month"
✓ "Why Does ChatGPT Recommend My Competitor Instead of Me?"
✓ "Tracking Brand Mentions Across Multiple AI Platforms"
✓ "Is AI Visibility Tracking Worth the Investment?"
✓ "Finding a Tool That Actually Works for Small Businesses"
✓ "Competitor Analysis for AI Search Results"

EXAMPLES OF BAD FOCUS NAMES (TOO GENERIC):
✗ "Setting Up AI Visibility Tracking"
✗ "Getting Actionable Optimization Steps"
✗ "Comparing AI Visibility Platforms and Tools"
✗ "Understanding AI Visibility Technology"
"""


def generate_focuses(brand: Brand, problems: list[dict], model: str = "", language: str = "id") -> list[Focus]:
    """Generate focus clusters from discovered problems using LLM."""
    lang_instruction = LANGUAGE_INSTRUCTION.get(language, LANGUAGE_INSTRUCTION["id"])
    system_prompt = FOCUS_GENERATION_PROMPT.format(language_instruction=lang_instruction)
    data = completion_json(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
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
