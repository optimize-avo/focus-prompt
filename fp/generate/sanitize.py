"""Post-generation sanitizer — detect and fix non-Latin characters via LLM."""
from __future__ import annotations

import re
import json
from fp.llm import completion_json
from fp.models import ScoredPrompt, Focus


# Characters that are NOT Latin script, Arabic numerals, or common punctuation
_NON_LATIN_RE = re.compile(r'[^\x00-\x7F\u00A0-\u00FF\u2000-\u206F\u2010-\u2027]')

# More targeted: CJK, Cyrillic, Thai, Devanagari, etc.
_CJK_RE = re.compile(r'[\u4e00-\u9fff\u3400-\u4dbf\uf900-\ufaff]')
_CYRILLIC_RE = re.compile(r'[\u0400-\u04ff]')
_OTHER_NON_LATIN_RE = re.compile(r'[\u0e00-\u0e7f\u0900-\u097f\u0600-\u06ff\u0590-\u05ff]')


def has_non_latin(text: str) -> bool:
    """Check if text contains non-Latin characters (CJK, Cyrillic, etc.)."""
    return bool(_CJK_RE.search(text) or _CYRILLIC_RE.search(text) or _OTHER_NON_LATIN_RE.search(text))


def _find_dirty_prompts(focuses: list[Focus]) -> list[tuple[int, int, ScoredPrompt]]:
    """Find all prompts with non-Latin chars. Returns (focus_idx, prompt_idx, prompt)."""
    dirty = []
    for fi, focus in enumerate(focuses):
        for pi, prompt in enumerate(focus.prompts):
            if has_non_latin(prompt.text):
                dirty.append((fi, pi, prompt))
    return dirty


SANITIZE_BATCH_PROMPT = """You are a text sanitizer for Indonesian/English AI prompts. Some prompts contain non-Latin characters (Chinese汉字, Cyrillic, Thai, etc.) that need to be replaced with correct Indonesian or English equivalents.

You will receive a numbered list of prompts that contain non-Latin characters. For each prompt:
1. Identify the non-Latin characters
2. Replace them with the correct Indonesian or English word/phrase that matches the intended meaning
3. Keep the rest of the prompt unchanged

Return JSON:
{{
  "fixed": [
    {{"id": 1, "text": "corrected prompt text with only Latin characters"}},
    ...
  ]
}}

Rules:
- Output ONLY Latin characters (a-z, A-Z), Arabic numerals, and common punctuation
- Preserve the original intent and meaning of each prompt
- Keep the language consistent (if prompt is in Indonesian, fix with Indonesian; if English, fix with English)
- Common fixes: 推荐→rekomendasi, 靠谱→terpercaya, 你们→kamu/anda, 找→cari, 切换→beralih
- NEVER introduce new non-Latin characters"""


def _sanitize_batch(prompts: list[ScoredPrompt], model: str = "") -> list[str]:
    """Send a batch of dirty prompts to LLM for fixing. Returns list of fixed texts."""
    if not prompts:
        return []

    numbered = "\n".join(f"{i+1}. {p.text}" for i, p in enumerate(prompts))

    data = completion_json(
        model=model,
        messages=[
            {"role": "system", "content": SANITIZE_BATCH_PROMPT},
            {"role": "user", "content": f"Fix these {len(prompts)} prompts:\n\n{numbered}"},
        ],
        temperature=0.3,
    )

    fixed_items = data.get("fixed", []) if isinstance(data, dict) else []

    results = []
    for i, p in enumerate(prompts):
        if i < len(fixed_items) and isinstance(fixed_items[i], dict):
            text = fixed_items[i].get("text", p.text)
            # Verify fix worked
            if not has_non_latin(text):
                results.append(text)
            else:
                results.append(p.text)  # fallback to original
        else:
            results.append(p.text)  # fallback to original

    return results


def sanitize_focuses(focuses: list[Focus], model: str = "", batch_size: int = 20) -> list[Focus]:
    """Sanitize all prompts across all focuses. Modifies in-place, returns focuses."""
    import sys

    dirty = _find_dirty_prompts(focuses)
    if not dirty:
        print("  ✓ All prompts clean — no non-Latin characters found", file=sys.stderr)
        return focuses

    print(f"  🔧 Found {len(dirty)} prompts with non-Latin characters — sanitizing...", file=sys.stderr)

    # Group by focus for efficient batch processing
    for batch_start in range(0, len(dirty), batch_size):
        batch = dirty[batch_start:batch_start + batch_size]
        batch_prompts = [item[2] for item in batch]

        try:
            fixed_texts = _sanitize_batch(batch_prompts, model=model)
            for (fi, pi, _), fixed_text in zip(batch, fixed_texts):
                focuses[fi].prompts[pi].text = fixed_text
        except Exception as e:
            print(f"  ⚠ Sanitize batch failed: {e} — keeping original", file=sys.stderr)

    # Verify
    remaining = _find_dirty_prompts(focuses)
    if remaining:
        print(f"  ⚠ {len(remaining)} prompts still have non-Latin chars after sanitization", file=sys.stderr)
    else:
        print(f"  ✓ All {len(dirty)} prompts sanitized successfully", file=sys.stderr)

    return focuses
