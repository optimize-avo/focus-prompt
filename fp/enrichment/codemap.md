# fp/enrichment/ — Problem Discovery

## Responsibility
Discovers real user problems and search queries around a brand's service categories using LLM analysis.

## Design Patterns
- **Prompt-Engineered LLM Calls**: Structured system prompts with JSON output format enforcement (`response_format={"type": "json_object"}`)
- **Placeholder Web Enrichment**: `discover_problems_web()` is a stub for future web scraping

## Data & Control Flow
1. `discover_problems(brand, client)` → builds category string from brand → sends to GPT-4o-mini with structured system prompt
2. LLM returns JSON with problems grouped by service category, each containing pain points and raw queries
3. Returns `list[dict]` — list of `{category, problems: [{pain_point, raw_queries}]}` structures

## Integration Points
- **Called by**: `cli.py:discover()`, `server.py:fp_discover()`
- **Depends on**: `fp.models.Brand`, OpenAI client
- **Feeds into**: `fp.generate.focuses.generate_focuses()` — problems are input for focus clustering

## Files
| File | Purpose |
|------|---------|
| `__init__.py` | Empty package marker |
| `problems.py` | `discover_problems()` — LLM-based problem discovery; `discover_problems_web()` — web enrichment placeholder |
