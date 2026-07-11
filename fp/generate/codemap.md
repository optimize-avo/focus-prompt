# fp/generate/ — Focus & Prompt Generation

## Responsibility
Generates focus clusters from discovered problems, then produces unbranded and/or branded prompt variants for each focus.

## Design Patterns
- **Two-Phase Generation**: First clusters problems into focuses (topic grouping), then generates prompts per focus
- **Mode-Aware Prompting**: `PromptMode.UNBRANDED` / `BRANDED` / `BOTH` controls which LLM templates are invoked
- **Deep Copy Isolation**: `generate_all_prompts()` and `generate_focuses()` deep-copy inputs before mutation
- **Template Interpolation**: System prompts use `{brand_name}` format strings for brand-specific context

## Data & Control Flow
1. `generate_focuses(brand, problems, client)` → sends problems + brand context to GPT-4o-mini → returns `list[Focus]` with names, descriptions, and signal queries
2. `generate_all_prompts(brand, focuses, client, mode)` → iterates focuses → calls `generate_prompts_for_focus()` per focus
3. `generate_prompts_for_focus()` → conditionally calls unbranded and/or branded LLM templates → returns `list[ScoredPrompt]`
4. Each prompt gets: text, intent (from 8 IntentTypes), mode, focus_name, language

## Integration Points
- **Called by**: `cli.py:discover()`, `cli.py:prompt_generate()`, `server.py:fp_discover()`, `server.py:fp_generate_prompts()`
- **Depends on**: `fp.models.{Brand, Focus, Prompt, PromptIntent, PromptMode, ScoredPrompt}`, OpenAI client
- **Feeds into**: `fp.scoring.scorer.score_all()` — generated prompts are scored for relevance

## Files
| File | Purpose |
|------|---------|
| `__init__.py` | Empty package marker |
| `focuses.py` | `generate_focuses()` — LLM-based topic clustering from problems |
| `prompts.py` | `generate_prompts_for_focus()`, `generate_all_prompts()` — LLM prompt variant generation |
