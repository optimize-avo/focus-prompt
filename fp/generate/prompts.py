"""Generate prompt variants per focus — unbranded first, branded variant optional."""
from __future__ import annotations

import json

from fp.llm import completion_json
from fp.models import Brand, Focus, PromptMode, Prompt, PromptIntent, ScoredPrompt


UNBRANDED_PROMPT_PROMPT = """You are an expert at predicting what real users ask AI chatbots. Given a focus topic and a brand that offers relevant services, generate realistic user prompts that people would actually type into ChatGPT, Google Gemini, or similar AI tools.

The prompts must be UNBRANDED — they must NOT mention the brand name. The goal is to predict prompts where the AI's response could naturally mention {brand_name} as a solution.

For each prompt:
1. text — the exact prompt a user would type
2. intent — one of: info, comparison, how-to, hire, review, troubleshoot, explore, verify
3. language — "id" for Indonesian, "en" for English, "mix" for mixed

OUTPUT FORMAT — Return JSON array:
[
  {{
    "text": "real prompt text",
    "intent": "info|comparison|how-to|hire|review|troubleshoot|explore|verify",
    "language": "id|en|mix"
  }}
]

Rules:
- Each prompt must be realistic — something a real person would actually type
- NEVER include the brand name "{brand_name}" in any prompt
- Vary the phrasing: some casual, some formal, some detailed, some short
- Vary the intent across prompts for each focus
- 6-10 prompts per focus
- OUTPUT LANGUAGE: Write prompts ONLY in Bahasa Indonesia or English. NEVER use Chinese characters (汉字), Japanese, Korean, or any non-Latin script except Arabic numerals. If you are unsure about a word, use the Indonesian or English equivalent.
- Think about different user personas: pemula, expert, bisnis, individual
"""

BRANDED_PROMPT_PROMPT = """You are an expert at predicting what real users ask AI chatbots about specific brands. Given a focus topic and a brand, generate realistic user prompts that include the brand name.

For each prompt:
1. text — the exact prompt a user would type (MUST include {brand_name})
2. intent — one of: info, comparison, how-to, hire, review, troubleshoot, explore, verify
3. language — "id" for Indonesian, "en" for English, "mix" for mixed

OUTPUT FORMAT — Return JSON array:
[
  {{
    "text": "real prompt text with {brand_name}",
    "intent": "info|comparison|how-to|hire|review|troubleshoot|explore|verify",
    "language": "id|en|mix"
  }}
]

Rules:
- Each prompt MUST include the brand name "{brand_name}"
- 4-6 prompts per focus
- Varied intent and phrasing
- OUTPUT LANGUAGE: Write prompts ONLY in Bahasa Indonesia or English. NEVER use Chinese characters (汉字), Japanese, Korean, Cyrillic, Thai, or any non-Latin script except Arabic numerals. If you are unsure about a word, use the Indonesian or English equivalent.
"""


def _call_prompt_gen(
    brand: Brand,
    focus: Focus,
    prompt_template: str,
    model: str = "",
) -> list[dict]:
    """Call LLM to generate prompts for a focus."""
    focus_input = {
        "focus_name": focus.name,
        "focus_description": focus.description,
        "brand_name": brand.name,
        "brand_description": brand.description,
        "brand_services": brand.service_categories,
    }

    system_msg = prompt_template.format(brand_name=brand.name)

    data = completion_json(
        model=model,
        messages=[
            {"role": "system", "content": system_msg},
            {"role": "user", "content": json.dumps(focus_input, indent=2)},
        ],
        temperature=0.8,
    )
    if isinstance(data, dict):
        return data.get("prompts", [])
    return data


def generate_prompts_for_focus(
    brand: Brand,
    focus: Focus,
    mode: PromptMode = PromptMode.UNBRANDED,
    model: str = "",
) -> list[ScoredPrompt]:
    """Generate prompts for a single focus."""
    all_prompts = []

    if mode in (PromptMode.UNBRANDED, PromptMode.BOTH):
        unbranded = _call_prompt_gen(brand, focus, UNBRANDED_PROMPT_PROMPT, model=model)
        for p in unbranded:
            all_prompts.append(ScoredPrompt(
                text=p.get("text", ""),
                intent=PromptIntent(p.get("intent", "info")),
                mode=PromptMode.UNBRANDED,
                focus_name=focus.name,
                language=p.get("language", "id"),
            ))

    if mode in (PromptMode.BRANDED, PromptMode.BOTH):
        branded = _call_prompt_gen(brand, focus, BRANDED_PROMPT_PROMPT, model=model)
        for p in branded:
            all_prompts.append(ScoredPrompt(
                text=p.get("text", ""),
                intent=PromptIntent(p.get("intent", "info")),
                mode=PromptMode.BRANDED,
                focus_name=focus.name,
                language=p.get("language", "id"),
            ))

    return all_prompts


def generate_all_prompts(
    brand: Brand,
    focuses: list[Focus],
    mode: PromptMode = PromptMode.UNBRANDED,
    model: str = "",
    sanitize: bool = True,
) -> list[Focus]:
    """Generate prompts for all focuses in place, optionally sanitize."""
    import copy
    updated = copy.deepcopy(focuses)
    for focus in updated:
        focus.prompts = generate_prompts_for_focus(brand, focus, mode, model=model)

    if sanitize:
        from fp.generate.sanitize import sanitize_focuses
        updated = sanitize_focuses(updated, model=model)

    return updated
