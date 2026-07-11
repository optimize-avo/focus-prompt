# fp/scoring/ — Relevance Scoring Engine

## Responsibility
Evaluates each prompt for brand relevance (service match) and AI mention likelihood using LLM analysis, then derives focus-level priority rankings.

## Design Patterns
- **Weighted Scoring**: Mode-dependent weights — unbranded prompts weight `mention_likelihood` higher (0.7), branded weight `service_match` higher (0.7)
- **Priority Classification**: Score-based thresholds — high (≥75%), medium (≥55%), low (<55%)
- **Review Flagging**: Auto-flags prompts with `service_match < 40` or LLM-flagged ambiguity
- **Deep Copy Isolation**: `score_all()` deep-copies focuses before mutation

## Data & Control Flow
1. `score_all(focuses, brand, client)` → deep-copies → iterates focuses → calls `score_focus()` per focus
2. `score_focus(focus, brand, client)` → iterates prompts → calls `score_prompt()` per prompt → computes `focus.service_match_score` as average
3. `score_prompt(prompt, brand, client)` → sends prompt + brand context to GPT-4o-mini → gets `service_match`, `mention_likelihood`, `needs_review` → computes `overall_score` with mode-specific weights
4. Post-scoring: focuses sorted by `service_match_score` descending, priority assigned by threshold

## Integration Points
- **Called by**: `cli.py:score()`, `server.py:fp_score()`
- **Depends on**: `fp.models.{Brand, Focus, PromptMode, ScoredPrompt}`, OpenAI client
- **Feeds into**: `fp.output.export` and `fp.output.table` — scored data is exported/displayed

## Files
| File | Purpose |
|------|---------|
| `__init__.py` | Empty package marker |
| `scorer.py` | `score_prompt()`, `score_focus()`, `score_all()` — LLM-based relevance scoring |
