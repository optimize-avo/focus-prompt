"""Generate prompt variants per focus — unbranded first, branded variant optional."""
from __future__ import annotations

import json

from fp.llm import completion_json
from fp.models import Brand, Focus, PromptMode, PromptIntent, ScoredPrompt

LANGUAGE_INSTRUCTION = {
    "id": "OUTPUT LANGUAGE: Write ALL prompts in Bahasa Indonesia. NEVER use Chinese characters (汉字), Japanese, Korean, or any non-Latin script except Arabic numerals.",
    "en": "OUTPUT LANGUAGE: Write ALL prompts in English. NEVER use Chinese characters (汉字), Japanese, Korean, or any non-Latin script except Arabic numerals.",
    "mix": "OUTPUT LANGUAGE: Write prompts in a mix of Indonesian and English (as real users do). NEVER use Chinese characters (汉字), Japanese, Korean, or any non-Latin script except Arabic numerals.",
}

UNBRANDED_PROMPT_PROMPT = """You are an expert at predicting what real users ask AI chatbots. Given a focus topic and a brand that offers relevant services, generate realistic user prompts that people would actually type into AI chatbots.

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
- {language_instruction}
- Think about different user personas: pemula, expert, bisnis, individual

REALISM INJECTION — these rules are CRITICAL for natural-sounding prompts:

1. PLATFORM MENTION LIMITS:
   - Maximum 1 platform name per prompt in 70% of prompts
   - Remaining 30% can mention 2 platforms max
   - Use generic terms like "AI chatbots", "AI assistants", "AI tools" for most prompts
   - NEVER list 3+ platforms in a single prompt
   - Example: "best AI brand tracker?" (no platform) vs "ChatGPT brand monitoring" (1 platform)

2. INTENT DISTRIBUTION (approximate per batch):
   - info: 25% (most common — people asking what something is)
   - how-to: 20% (very common — people wanting to do something)
   - comparison: 15% (common — people evaluating options)
   - explore: 12% (moderate — people browsing/discovering)
   - troubleshoot: 10% (moderate — people with problems)
   - review: 8% (less common — people seeking social proof)
   - verify: 6% (less common — people checking claims)
   - hire: 4% (rare — people ready to buy)

3. SPECIFICITY INJECTION — include variety of real-world details:
   - Budget constraints: "under $100/month", "free alternatives", "won't cost $500+"
   - Competitor names: Reference real competitors when relevant (e.g., PEEC AI, The Prompting Company, Brandwatch, Semrush, Ahrefs)
   - Geographic context: "for businesses in [region]", "in Indonesia", "for US market"
   - Company size: "small business", "enterprise", "agency managing 10+ brands"
   - Specific scenarios: "when generating articles longer than 1000 words", "for multiple brands at once"
   - Error messages: "timeout error", "API key invalid", "rate limit exceeded"

4. NATURAL LANGUAGE VARIATION:
   - Include prompts with imperfect grammar or casual slang
   - Mix prompt lengths: some under 10 words, some over 20 words
   - At least 2 prompts should sound like the user already tried something and failed
   - Include filler words naturally: "basically", "honestly", "like"
   - Some prompts should be fragmented sentences, not complete questions
   - Some should end with "..." or have trailing thoughts
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
- {language_instruction}

REALISM INJECTION — these rules are CRITICAL for natural-sounding prompts:

1. PLATFORM MENTION LIMITS:
   - Maximum 1 platform name per prompt in 70% of prompts
   - Remaining 30% can mention 2 platforms max
   - Use generic terms like "AI chatbots", "AI assistants", "AI tools" for most prompts
   - NEVER list 3+ platforms in a single prompt

2. SPECIFICITY INJECTION — include variety of real-world details:
   - Budget constraints: "Is {brand_name} worth the cost?", "cheaper than alternatives"
   - Competitor comparisons: "{brand_name} vs [competitor]", "better than [competitor]?"
   - Specific scenarios: "for my agency managing 10+ brands", "for small business on budget"
   - Experience level: "as a beginner", "for enterprise use"
   - Pain points: "tired of", "frustrated with", "looking for something better"

3. NATURAL LANGUAGE VARIATION:
   - Mix formal and casual phrasing
   - Some prompts should sound frustrated or skeptical
   - Some should be very specific about use case
   - Some should be short and direct, others detailed
   - Include natural filler words: "honestly", "basically", "actually"
"""


def _call_prompt_gen(
    brand: Brand,
    focus: Focus,
    prompt_template: str,
    model: str = "",
    language: str = "id",
) -> list[dict]:
    """Call LLM to generate prompts for a focus."""
    focus_input = {
        "focus_name": focus.name,
        "focus_description": focus.description,
        "brand_name": brand.name,
        "brand_description": brand.description,
        "brand_services": brand.service_categories,
    }

    lang_instruction = LANGUAGE_INSTRUCTION.get(language, LANGUAGE_INSTRUCTION["id"])
    system_msg = prompt_template.format(brand_name=brand.name, language_instruction=lang_instruction)

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
    language: str = "id",
) -> list[ScoredPrompt]:
    """Generate prompts for a single focus."""
    all_prompts = []

    if mode in (PromptMode.UNBRANDED, PromptMode.BOTH):
        unbranded = _call_prompt_gen(brand, focus, UNBRANDED_PROMPT_PROMPT, model=model, language=language)
        for p in unbranded:
            all_prompts.append(ScoredPrompt(
                text=p.get("text", ""),
                intent=PromptIntent(p.get("intent", "info")),
                mode=PromptMode.UNBRANDED,
                focus_name=focus.name,
                language=p.get("language", "id"),
            ))

    if mode in (PromptMode.BRANDED, PromptMode.BOTH):
        branded = _call_prompt_gen(brand, focus, BRANDED_PROMPT_PROMPT, model=model, language=language)
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
    language: str = "id",
    sanitize: bool = True,
    naturalize: bool = False,
) -> list[Focus]:
    """Generate prompts for all focuses in place, optionally sanitize and naturalize."""
    import copy
    updated = copy.deepcopy(focuses)
    for focus in updated:
        focus.prompts = generate_prompts_for_focus(brand, focus, mode, model=model, language=language)

    if sanitize:
        from fp.generate.sanitize import sanitize_focuses
        updated = sanitize_focuses(updated, model=model)

    if naturalize:
        from fp.generate.naturalness import naturalize_all_focuses
        updated = naturalize_all_focuses(updated, model=model)

    return updated
