# focus-prompt

AI Brand Visibility Research Tool — prediksi dan generate unbranded prompt yang bisa dipakai AI chatbot untuk menemukan dan mention brand kamu.

## Setup (CLI)

```bash
# 1. Install
pip install -e .

# 2. Configure LLM provider
cp .env.example .env
# Edit .env — set FP_MODEL dan API key

# 3. Init project
fp init "Brand Name" \
  --desc "Deskripsi brand" \
  --url "https://brand.com" \
  --services "service1, service2" \
  --competitors "Kompetitor1, Kompetitor2" \
  --mode unbranded \
  --lang id
```

`fp` otomatis load `.env` dari project root — tidak perlu `export`.

## Setup (MCP Server)

Tambahkan di `opencode.jsonc` (global atau project-level):

```jsonc
{
  "mcp": {
    "fp": {
      "type": "local",
      "command": ["fp-mcp"],
      "env": {
        "FP_MODEL": "gpt-4o-mini",
        "OPENAI_API_KEY": "sk-..."
      }
    }
  }
}
```

Atau untuk provider lain:
```jsonc
"env": {
  "FP_MODEL": "minimax/MiniMax-M2.1",
  "MINIMAX_API_KEY": "your-key"
}
```

## Pipeline

```
init → research → discover → prompt-generate → score → export
```

Setiap step menyimpan state ke `fp-project.json`. Bisa jalan di CLI atau MCP server.

## CLI Commands

### `fp init`
Init brand project baru.

```bash
fp init "Sribu" \
  --desc "Marketplace freelance Indonesia" \
  --url "https://sribu.com" \
  --services "desain, programming, copywriting" \
  --competitors "Fastwork, Projects.co.id, Fiverr" \
  --mode both \
  --lang id
```

**Options:**
| Flag | Short | Default | Description |
|------|-------|---------|-------------|
| `--desc` | `-d` | `""` | Brand description |
| `--url` | `-u` | `""` | Brand website |
| `--services` | `-s` | `""` | Comma-separated service categories |
| `--competitors` | `-c` | `""` | Comma-separated competitor names |
| `--mode` | `-m` | `unbranded` | `unbranded`, `branded`, `both` |
| `--lang` | `-l` | `id` | Language code |

### `fp research`
Fetch real user queries dari Google Autocomplete.

```bash
fp research
fp research --extra "tips bisnis online,cara jualan online"
fp research --no-autocomplete
```

**Options:**
| Flag | Short | Description |
|------|-------|-------------|
| `--extra` | `-e` | Extra seed queries, comma-separated |
| `--no-autocomplete` | | Skip Google Autocomplete |

### `fp discover`
Problem discovery + focus clustering pakai LLM. Kalau sudah jalan `research`, pakai data real. Kalau belum, pakai LLM-only guessing.

```bash
fp discover
fp discover --model gpt-4o
```

### `fp prompt-generate`
Generate prompt variants untuk setiap focus.

```bash
fp prompt-generate
fp prompt-generate --model gpt-4o
```

### `fp score`
Score semua prompt untuk brand relevance dan mention likelihood.

```bash
fp score
fp score --model gpt-4o
```

### `fp focus-list`
List semua focuses.

```bash
fp focus-list
```

### `fp prompt-list`
List prompts, bisa difilter.

```bash
fp prompt-list
fp prompt-list --focus "desain"
fp prompt-list --mode unbranded
fp prompt-list --review
```

### `fp export`
Export project data ke JSON atau CSV.

```bash
fp export json
fp export csv
fp export json -o my-export.json
```

### `fp status`
Tampilkan status project.

```bash
fp status
```

## MCP Server

Entry point: `fp-mcp` (stdio transport).

### MCP Tools

| Tool | Description | Args |
|------|-------------|------|
| `fp_init` | Init brand project | `name`, `description`, `website`, `services`, `competitors`, `mode`, `language` |
| `fp_research` | Fetch real queries dari Google Autocomplete | `extra`, `include_autocomplete` |
| `fp_discover` | Problem discovery + focus clustering | `model` |
| `fp_generate_prompts` | Generate prompt variants | `focus_name`, `mode`, `model` |
| `fp_score` | Score prompts | `focus_name`, `model` |
| `fp_export` | Export data | `fmt` (json/csv) |
| `fp_status` | Project status | — |

### MCP Resources

| URI | Description |
|-----|-------------|
| `fp://project` | Full project state (JSON) |
| `fp://focuses` | Focus list + summary metrics |
| `fp://focus/{name}/prompts` | Prompts untuk focus tertentu |

## Data Flow

```
Brand Config (init)
    ↓
Research (web) — real queries dari Google Suggest API
    ↓
Problem Discovery (LLM) — problems by category
    ↓ list[dict]
Focus Clustering (LLM) — 4-8 topic clusters
    ↓ list[Focus]
Prompt Generation (LLM) — unbranded/branded variants
    ↓ list[Focus] with ScoredPrompts
Relevance Scoring (LLM) — scores + priorities
    ↓
Export / Display
```

## Models

| Model | Fields |
|-------|--------|
| `Brand` | `name`, `description`, `website`, `service_categories`, `competitors` |
| `Focus` | `name`, `description`, `lens`, `priority`, `signals`, `signal_count`, `service_match_score`, `prompts` |
| `Prompt` → `ScoredPrompt` | `text`, `intent`, `mode`, `language`, `service_match`, `mention_likelihood`, `overall_score`, `needs_review` |
| `ProjectConfig` | `brand`, `prompt_mode`, `language`, `output_dir` |
| `ProjectState` | `config`, `focuses`, `web_data` |

**Prompt Intent Types:** `info`, `comparison`, `how-to`, `hire`, `review`, `troubleshoot`, `explore`, `verify`

**Prompt Modes:** `unbranded` (mention likelihood weighted higher), `branded` (service match weighted higher), `both`

## Requirements

- Python 3.11+
- LLM API key (OpenAI, DeepSeek, MiniMax, Qwen, dll)
- LiteLLM — supports 100+ providers via `FP_MODEL` env var
