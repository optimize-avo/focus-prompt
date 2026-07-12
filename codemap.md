# Repository Atlas: focus-prompt

## Project Responsibility
AI Brand Visibility Research Tool — predicts and generates unbranded prompts that AI chatbots might use to discover and mention a brand. Provides a CLI (`fp`) and MCP server (`fp-mcp`) for the full pipeline: brand init → problem discovery → focus clustering → prompt generation → relevance scoring → export.

## System Entry Points
- `fp/cli.py`: Typer CLI — `fp init`, `fp focus discover`, `fp prompt generate`, `fp score`, `fp export`
- `fp/server.py`: FastMCP server — `fp_init`, `fp_discover`, `fp_generate_prompts`, `fp_score`, `fp_export`, `fp_status` tools + `fp://project`, `fp://focuses`, `fp://focus/{name}/prompts` resources
- `pyproject.toml`: Entry points `fp` → `fp.cli:app`, `fp-mcp` → `fp.server:main`
- `.env.example`: Requires `OPENAI_API_KEY`

## Tech Stack
- Python 3.11+, Typer (CLI), FastMCP (MCP server), Pydantic v2 (models), LiteLLM (model-agnostic LLM calls), Rich (table output), httpx (web), BeautifulSoup4 (future web enrichment)

## Directory Map

| Directory | Responsibility Summary | Detailed Map |
|-----------|----------------------|--------------|
| `fp/` | Root package — CLI, MCP server, Pydantic models, entry points | [View Map](fp/codemap.md) |
| `fp/enrichment/` | Problem discovery — LLM-based user problem/query analysis per service category | [View Map](fp/enrichment/codemap.md) |
| `fp/generate/` | Focus clustering + prompt variant generation (unbranded/branded) + LLM sanitization | [View Map](fp/generate/codemap.md) |
| `fp/output/` | JSON/CSV export + Rich CLI table rendering | [View Map](fp/output/codemap.md) |
| `fp/scoring/` | LLM-based relevance scoring with mode-weighted metrics + priority classification | [View Map](fp/scoring/codemap.md) |

## Data Flow

```
Brand Config (init)
    ↓
Problem Discovery (enrichment/problems.py)
    ↓ list[dict] — problems by category
Focus Clustering (generate/focuses.py)
    ↓ list[Focus] — 4-8 topic clusters
Prompt Generation (generate/prompts.py)
    ↓ list[Focus] with ScoredPrompts attached
Sanitization (generate/sanitize.py) — auto-fix non-Latin chars via LLM
    ↓ clean prompts (Latin only)
Relevance Scoring (scoring/scorer.py)
    ↓ list[Focus] with scores + priorities
Export (output/export.py) — JSON file or CSV (file + inline content for MCP)
Display (output/table.py) — Rich CLI tables
```

## Key Models (`fp/models.py`)
- `Brand` — name, description, website, service_categories, competitors
- `Focus` — name, description, lens, priority, signals, service_match_score, prompts
- `Prompt` → `ScoredPrompt` — text, intent (8 types), mode, scores, needs_review
- `ProjectConfig` / `ProjectState` — serialized to `fp-project.json`

## Design Patterns
- **Pipeline Architecture**: Linear stages with JSON state persistence
- **Dual Interface**: CLI (Typer) and MCP server expose identical functionality
- **LLM-as-Judge**: Model-agnostic via LiteLLM — supports OpenAI, DeepSeek, MiniMax, Qwen, MiMo, and 100+ providers
- **Mode-Aware Weighting**: Unbranded prompts weight mention likelihood higher; branded weight service match
