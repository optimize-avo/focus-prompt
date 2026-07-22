"""Post-generation naturalness pass — make prompts sound like real humans typed them."""
from __future__ import annotations

import json

from fp.llm import completion_json
from fp.models import Focus

NATURALNESS_PASS_PROMPT = """You are a prompt naturalizer. Your job is to take AI-generated prompts and make them sound like they were typed by real, imperfect humans.

RULES:
1. Add natural imperfections:
   - Some should have typos or informal spelling ("wanna", "gonna", "tbh", "idk")
   - Some should be fragments, not complete sentences
   - Some should have filler words ("basically", "honestly", "like")

2. Reduce template patterns:
   - Remove "How to [verb] [topic]" pattern from >30% of prompts
   - Vary sentence structures dramatically
   - Some should be statements, not questions
   - Some should end with "..." or have trailing thoughts

3. Add emotional texture:
   - Frustration: "I'm so tired of...", "Why does this keep..."
   - Urgency: "Need this ASAP", "Anyone know fast..."
   - Skepticism: "Is this even worth it?", "Does this actually work?"
   - Confusion: "I don't get why...", "Wait, so how does..."

4. Platform mention cleanup:
   - Remove any prompt that mentions 3+ platforms
   - Replace specific platform names with generic terms in 70% of prompts

5. Length variation:
   - Mix very short ("best AI tracker?") with very long detailed prompts
   - Some should be 5-8 words, others 25+ words

Keep these unchanged:
- intent field
- language field
- mode field
- focus_name field
- All score fields if present

INPUT: Array of prompts with all fields
OUTPUT: Same array with naturalized text (keep all other fields unchanged)
"""


def naturalize_focus_prompts(
    focus: Focus,
    model: str = "",
) -> Focus:
    """Apply naturalness pass to all prompts in a focus."""
    if not focus.prompts:
        return focus

    # Convert to dicts for LLM
    prompt_dicts = []
    for p in focus.prompts:
        prompt_dicts.append({
            "text": p.text,
            "intent": p.intent.value if hasattr(p.intent, "value") else p.intent,
            "language": p.language,
            "mode": p.mode.value if hasattr(p.mode, "value") else p.mode,
            "focus_name": p.focus_name,
        })

    data = completion_json(
        model=model,
        messages=[
            {"role": "system", "content": NATURALNESS_PASS_PROMPT},
            {"role": "user", "content": json.dumps(prompt_dicts, indent=2)},
        ],
        temperature=0.9,  # Higher temperature for more variation
    )

    naturalized = data if isinstance(data, list) else data.get("prompts", prompt_dicts)

    # Update prompt texts
    for i, p in enumerate(focus.prompts):
        if i < len(naturalized):
            p.text = naturalized[i].get("text", p.text)

    return focus


def naturalize_all_focuses(
    focuses: list[Focus],
    model: str = "",
) -> list[Focus]:
    """Apply naturalness pass to all focuses."""
    import copy
    updated = copy.deepcopy(focuses)
    for focus in updated:
        naturalize_focus_prompts(focus, model=model)
    return updated
