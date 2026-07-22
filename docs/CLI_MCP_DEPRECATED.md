# CLI & MCP Deprecated — Web App Only Mode

**Date:** 2026-07-22
**Status:** DEPRECATED (disabled, not deleted)
**Reason:** focus-prompt is now a **web application only**. CLI and MCP server surfaces have been removed.

---

## What Changed

| Component | Before | After |
|-----------|--------|-------|
| `fp` CLI command | Installed via `pip install -e .` | **Removed** (entry point deleted) |
| `fp-mcp` MCP server | Installed via `pip install -e .` | **Removed** (entry point deleted) |
| `fp/cli.py` | Active code | **DEPRECATED** header, kept for reference |
| `fp/server.py` | Active code | **DEPRECATED** header, kept for reference |
| Web UI (`fp/web/`) | Active | **Primary development target** |

---

## Files to Skip During Development

When working on focus-prompt, **only edit files under these paths:**

- `fp/web/` — FastAPI app, routes, templates (PRIMARY)
- `fp/enrichment/`, `fp/generate/`, `fp/scoring/`, `fp/output/`, `fp/research/`, `fp/llm.py`, `fp/models.py` — Shared core
- `fp/cli.py` — **DEPRECATED**, do not add features
- `fp/server.py` — **DEPRECATED**, do not add features

If you need to change something that touches CLI/MCP behavior, **add it to the web UI instead**.

---

## Why Not Delete?

- Some users may have scripts that call `fp` CLI
- Some IDE integrations may reference `fp-mcp`
- Keeping the code as reference for understanding the original API surface
- Low cost — these files are not imported by `fp/web/`

---

## How to Restore (Not Recommended)

If you need to re-enable CLI or MCP temporarily:

### Restore CLI + MCP

1. Edit `pyproject.toml` — uncomment the `[project.scripts]` block:

```toml
[project.scripts]
fp = "fp.cli:app"
fp-mcp = "fp.server:main"
```

2. Reinstall:

```bash
pip install -e .
```

3. Verify:
   - `fp --help` should work
   - `fp-mcp` should be available in your MCP client config

---

## Development Workflow

```bash
# 1. Make changes only to fp/web/ or core modules
# 2. Test web UI locally
.venv/bin/python -c "from fp.web.app import create_app; import uvicorn; uvicorn.run(create_app(), host='0.0.0.0', port=8000)"

# 3. Run tests
.venv/bin/pytest tests/ -v

# 4. Commit
git add fp/web/ fp/[core modules]
git commit -m "..."
```

**Never commit changes to `fp/cli.py` or `fp/server.py`** unless explicitly restoring them.

---

## Questions?

If you're unsure whether a change belongs in CLI/MCP or web:
- **Default: web UI** (`fp/web/`)
- Only restore CLI/MCP if there's a hard requirement (e.g., automation script that can't use HTTP)
