# fp/output/ — Export & Display

## Responsibility
Handles project data serialization (JSON/CSV export) and CLI table rendering via Rich.

## Design Patterns
- **Flat CSV Serialization**: Flattens nested Focus→Prompt hierarchy into single-row-per-prompt CSV
- **Rich Table Rendering**: Uses Rich library for formatted CLI output with color coding and alignment
- **Dual Export Formats**: JSON preserves full structure, CSV is flat for spreadsheet analysis

## Data & Control Flow
1. `export_json(state, path)` → `state.model_dump()` → pretty-printed JSON file
2. `export_csv(state, path)` → iterates focuses × prompts → `csv.DictWriter` → flat CSV with columns: focus, prompt, mode, intent, scores
3. `render_focus_table(focuses)` → builds Rich Table with columns: #, Focus, Priority, Unbranded, Branded, Service Match, Signals
4. `render_prompt_table(focus, mode_filter)` → builds Rich Table with columns: #, Mode, Prompt, Intent, Service, Mention, Score

## Integration Points
- **Called by**: `cli.py:export()`, `cli.py:focus_list()`, `cli.py:prompt_list()`, `cli.py:discover()`, `cli.py:prompt_generate()`, `cli.py:score()`
- **Depends on**: `fp.models.{Focus, ProjectState, PromptMode}`, Rich library

## Files
| File | Purpose |
|------|---------|
| `__init__.py` | Empty package marker |
| `export.py` | `export_json()`, `export_csv()` — file serialization |
| `table.py` | `render_focus_table()`, `render_prompt_table()` — Rich CLI tables |
