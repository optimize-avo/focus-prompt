"""Scoring engine — evaluate prompt relevance, service match, and brand mention likelihood."""
from __future__ import annotations

import json

from openai import OpenAI

from fp.models import Brand, Focus, PromptMode, ScoredPrompt


SCORE_PROMPT = """You are a brand relevance analyst. Given a brand and a user prompt, evaluate:

1. service_match (0-100): How well does this prompt match services the brand offers? If the user is looking for something the brand actually sells, score high.
2. mention_likelihood (0-100): If an AI answers this prompt, how likely is it to mention {brand_name} in the response? Consider: is the brand a relevant answer to this query?
3. needs_review (true/false): Is this too ambiguous to auto-score? Flag if service match < 40.

Return JSON:
{{
  "service_match": 85,
  "mention_likelihood": 72,
  "reasoning": "Brief explanation",
  "needs_review": false
}}

Rules:
- For UNBRANDED prompts, mention_likelihood is the key metric — will the AI even think of this brand?
- For BRANDED prompts, service_match is the key metric — does the question match what they offer?
- Be honest — if the brand doesn't fit, score low
"""


def score_prompt(prompt: ScoredPrompt, brand: Brand, client: OpenAI) -> ScoredPrompt:
    """Score a single prompt for relevance to the brand."""
    system_msg = SCORE_PROMPT.format(brand_name=brand.name)

    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_msg},
            {"role": "user", "content": json.dumps({
                "brand": brand.name,
                "brand_description": brand.description,
                "brand_services": brand.service_categories,
                "prompt_text": prompt.text,
                "prompt_intent": prompt.intent.value,
                "prompt_mode": prompt.mode.value,
            }, indent=2)},
        ],
        response_format={"type": "json_object"},
        temperature=0.3,
    )

    raw = resp.choices[0].message.content
    data = json.loads(raw)

    prompt.service_match = data.get("service_match", 50)
    prompt.mention_likelihood = data.get("mention_likelihood", 50)

    weights = {"service_match": 0.5, "mention_likelihood": 0.5}
    if prompt.mode == PromptMode.UNBRANDED:
        weights = {"service_match": 0.3, "mention_likelihood": 0.7}
    elif prompt.mode == PromptMode.BRANDED:
        weights = {"service_match": 0.7, "mention_likelihood": 0.3}

    prompt.overall_score = (
        prompt.service_match * weights["service_match"]
        + prompt.mention_likelihood * weights["mention_likelihood"]
    )
    prompt.needs_review = data.get("needs_review", False) or prompt.service_match < 40

    return prompt


def score_focus(focus: Focus, brand: Brand, client: OpenAI) -> Focus:
    """Score all prompts in a focus and derive focus-level metrics."""
    scored_prompts = []
    for p in focus.prompts:
        scored = score_prompt(p, brand, client)
        scored_prompts.append(scored)

    focus.prompts = scored_prompts

    if focus.prompts:
        avg_service = sum(p.service_match for p in focus.prompts) / len(focus.prompts)
        focus.service_match_score = round(avg_service, 1)
    else:
        focus.service_match_score = 0.0

    return focus


def score_all(focuses: list[Focus], brand: Brand, client: OpenAI) -> list[Focus]:
    """Score all focuses."""
    import copy
    updated = copy.deepcopy(focuses)
    for i, focus in enumerate(updated):
        updated[i] = score_focus(focus, brand, client)

    updated.sort(key=lambda f: f.service_match_score, reverse=True)

    for focus in updated:
        if focus.service_match_score >= 75:
            focus.priority = "high"
        elif focus.service_match_score >= 55:
            focus.priority = "medium"
        else:
            focus.priority = "low"

    return updated
