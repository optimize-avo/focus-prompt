# fp/ — Root Package

## Responsibility
CLI entry point and MCP server for the Focus Prompt AI Brand Visibility Research Tool. Orchestrates the full pipeline: brand init → problem discovery → focus generation → prompt generation → scoring → export.

## Design Patterns
- **CLI/MCP Dual Interface**: `cli.py` (Typer CLI) and `server.py` (FastMCP server) expose identical functionality through different protocols
- **Pipeline Architecture**: Linear stages (init → discover → generate → score → export) with state persisted to `fp-project.json`
- **Pydantic Models**: All data structures in `models.py` with JSON serialization/deserialization via `model_dump()`/`model_validate()`
- **LiteLLM Abstraction**: Model-agnostic LLM calls via `llm.py` — supports 100+ providers with automatic env-var API key resolution

## Data & Control Flow
1. User runs `fp init <brand>` → creates `ProjectState` with `Brand` config → saves to `fp-project.json`
2. `fp focus discover` → calls `discover_problems()` (LLM) → `generate_focuses()` (LLM) → updates state
3. `fp prompt generate` → calls `generate_all_prompts()` (LLM per focus) → updates state
4. `fp score` → calls `score_all()` (LLM per prompt) → updates state with scores + priorities
5. `fp export json|csv` → writes flattened output

## Integration Points
- **MCP Server** (`server.py`): Exposes `fp://project`, `fp://focuses`, `fp://focus/{name}/prompts` resources + `fp_init`, `fp_discover`, `fp_generate_prompts`, `fp_score`, `fp_export`, `fp_status` tools
- **CLI** (`cli.py`): Commands: `init`, `discover`, `prompt_generate`, `score`, `focus_list`, `prompt_list`, `export`, `status`
- **Entry points** (from pyproject.toml): `fp` → `fp.cli:app`, `fp-mcp` → `fp.server:main`

## Files
| File | Purpose |
|------|---------|
| `__init__.py` | Empty package marker |
| `cli.py` | Typer CLI — all user-facing commands |
| `llm.py` | LiteLLM abstraction — model-agnostic completions with regional endpoint overrides |
| `models.py` | Pydantic models: Brand, Focus, Prompt, ScoredPrompt, ProjectConfig, ProjectState |
| `server.py` | FastMCP server — tools + resources for OpenCode integration |