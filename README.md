# focus-prompt

AI Brand Visibility Research Tool — prediksi dan generate unbranded prompt yang bisa dipakai AI chatbot untuk menemukan dan mention brand kamu.

## Installation

### pipx (recommended for CLI + MCP)

[pipx](https://pypa.github.io/pipx/) installs Python CLI tools in isolated environments — like `npx` for Python.

```bash
# Install pipx (one-time)
brew install pipx
pipx ensurepath

# Install focus-prompt
pipx install focus-prompt
```

Provides global `fp` (CLI) and `fp-mcp` (MCP server) commands.

### From PyPI

```bash
pip install focus-prompt
```

### From source

```bash
git clone https://github.com/optimize-avo/focus-prompt.git
cd focus-prompt
pip install .
```

### Development mode

```bash
git clone https://github.com/optimize-avo/focus-prompt.git
cd focus-prompt
pip install -e .
```

## Update

```bash
# From PyPI
pip install --upgrade focus-prompt

# From source
git pull
pip install .
```

## Uninstall

```bash
pip uninstall focus-prompt
# .env, fp-project.json, dan export files tetap ada (data aman)
```

## Configuration

### 1. Buat file `.env`

```bash
cp .env.example .env
```

### 2. Pilih model dan set API key

Edit `.env`:

```bash
# Step 1: Pilih model (uncomment salah satu)
FP_MODEL=gpt-4o-mini
# FP_MODEL=minimax/MiniMax-M2.1
# FP_MODEL=deepseek/deepseek-chat
# FP_MODEL=dashscope/qwen-max
# FP_MODEL=xiaomi_mimo/MiMo-7B-RL

# Step 2: Set API key untuk provider yang dipilih
OPENAI_API_KEY=sk-your-key-here
# MINIMAX_API_KEY=your-key-here
# DEEPSEEK_API_KEY=sk-your-key-here
# DASHSCOPE_API_KEY=your-key-here
# XIAOMI_MIMO_API_KEY=your-key-here
```

### 3. Verifikasi

```bash
fp status
```

Kalau muncul warning `⚠ FP_MODEL='...' requires ..._API_KEY`, berarti API key belum diset.

> **Tip:** Kalau API key mengandung karakter spesial (`/`, newline, dll), jangan pakai `sed`. Pakai Python:
> ```bash
> python3 -c "
> path = '.env'
> with open(path) as f: c = f.read()
> key = input('Paste key: ').strip()
> with open(path, 'w') as f: f.write(c.replace('YOUR_KEY_HERE', key))
> "
> ```

### Supported Providers

| Provider | FP_MODEL value | API Key Env Var |
|----------|---------------|-----------------|
| OpenAI | `gpt-4o-mini` | `OPENAI_API_KEY` |
| DeepSeek | `deepseek/deepseek-chat` | `DEEPSEEK_API_KEY` |
| MiniMax (Singapore) | `minimax/MiniMax-M2.1` | `MINIMAX_API_KEY` |
| Qwen/Alibaba | `dashscope/qwen-max` | `DASHSCOPE_API_KEY` |
| Zhipu/GLM | `zai/glm-4.7` | `ZAI_API_KEY` |
| Moonshot/Kimi | `moonshot/kimi-k2-thinking` | `MOONSHOT_API_KEY` |
| ByteDance/Doubao | `volcengine/doubao-seed-1.6` | `VOLCENGINE_API_KEY` |
| Tencent/Hunyuan | `tencent/deepseek-v4-pro` | `TENCENT_API_KEY` |
| MiMo (Singapore) | `xiaomi_mimo/mimo-v2-pro` | `XIAOMI_MIMO_API_KEY` |

## Usage

### CLI

```bash
# 1. Init brand project
fp init "Brand Name" \
  --desc "Deskripsi brand" \
  --url "https://brand.com" \
  --services "service1, service2" \
  --competitors "Kompetitor1, Kompetitor2" \
  --mode unbranded \
  --lang id

# 2. Research — fetch real queries dari Google Autocomplete
fp research

# 3. Discover — problem discovery + focus clusters
fp discover

# 4. Generate prompts (auto-sanitizes non-Latin chars)
fp prompt-generate
# Or skip sanitization: fp prompt-generate --no-sanitize

# 5. Score
fp score

# 6. Export (JSON or CSV)
fp export json
fp export csv
```

### MCP Server

focus-prompt bisa dijalankan sebagai MCP server — terintegrasi langsung di AI editor seperti OpenCode, Claude Code, atau Cursor.

> **Set API key via terminal** (jangan pakai `sed` kalau key ada karakter spesial):
> ```bash
> python3 -c "
> import json, os
> path = os.path.expanduser('~/.config/opencode/opencode.jsonc')
> with open(path) as f: c = f.read()
> key = input('Paste MINIMAX_API_KEY: ').strip()
> with open(path, 'w') as f: f.write(c.replace('your-key-here', key))
> print('Done!')
> "
> ```

#### OpenCode

Tambahkan di `~/.config/opencode/opencode.jsonc`:

```jsonc
{
  "mcp": {
    "focus-prompt": {
      "type": "local",
      "command": ["fp-mcp"],
      "env": {
        "FP_MODEL": "minimax/MiniMax-M2.1",
        "MINIMAX_API_KEY": "your-key-here"
      }
    }
  }
}
```

#### Claude Code

Tambahkan di `.claude/settings.json` (project-level) atau `~/.claude.json` (global):

```json
{
  "mcpServers": {
    "focus-prompt": {
      "command": "fp-mcp",
      "env": {
        "FP_MODEL": "minimax/MiniMax-M2.1",
        "MINIMAX_API_KEY": "your-key-here"
      }
    }
  }
}
```

#### Cursor

Tambahkan di `.cursor/mcp.json`:

```json
{
  "mcpServers": {
    "focus-prompt": {
      "command": "fp-mcp",
      "env": {
        "FP_MODEL": "minimax/MiniMax-M2.1",
        "MINIMAX_API_KEY": "your-key-here"
      }
    }
  }
}
```

#### Ganti Provider

Ganti `FP_MODEL` dan API key di `env` block:

```jsonc
// OpenAI
"FP_MODEL": "gpt-4o-mini",
"OPENAI_API_KEY": "sk-..."

// DeepSeek
"FP_MODEL": "deepseek/deepseek-chat",
"DEEPSEEK_API_KEY": "sk-..."

// Qwen
"FP_MODEL": "dashscope/qwen-max",
"DASHSCOPE_API_KEY": "sk-..."
```

Restart editor setelah ganti config.

## CLI Commands

| Command | Description |
|---------|-------------|
| `fp init` | Init brand project baru |
| `fp research` | Fetch real queries dari Google Autocomplete |
| `fp discover` | Problem discovery + focus clustering (LLM) |
| `fp prompt-generate` | Generate prompt variants (auto-sanitize non-Latin chars; `--no-sanitize` to skip) |
| `fp score` | Score prompts untuk relevance |
| `fp export json\|csv` | Export hasil (JSON file or CSV file) |
| `fp status` | Status project |
| `fp focus-list` | List semua focuses |
| `fp prompt-list` | List prompts (filter: `--focus`, `--mode`, `--review`) |

### `fp init` Options

| Flag | Short | Default | Description |
|------|-------|---------|-------------|
| `--desc` | `-d` | `""` | Brand description |
| `--url` | `-u` | `""` | Brand website |
| `--services` | `-s` | `""` | Comma-separated service categories |
| `--competitors` | `-c` | `""` | Comma-separated competitor names |
| `--mode` | `-m` | `unbranded` | `unbranded`, `branded`, `both` |
| `--lang` | `-l` | `id` | Language code |

## Pipeline

```
init → research → discover → prompt-generate (auto-sanitize) → score → export (csv)
```

## MCP Tools

| Tool | Description |
|------|-------------|
| `fp_init` | Init brand project |
| `fp_research` | Fetch real queries dari Google Autocomplete |
| `fp_discover` | Problem discovery + focus clustering |
| `fp_generate_prompts` | Generate prompt variants (`sanitize`: auto-fix non-Latin chars) |
| `fp_score` | Score prompts |
| `fp_export` | Export data (`fmt`: json/csv — CSV returns inline content for download) |
| `fp_status` | Project status |

## Models

| Model | Fields |
|-------|--------|
| `Brand` | `name`, `description`, `website`, `service_categories`, `competitors` |
| `Focus` | `name`, `description`, `lens`, `priority`, `signals`, `signal_count`, `service_match_score`, `prompts` |
| `ScoredPrompt` | `text`, `intent`, `mode`, `language`, `service_match`, `mention_likelihood`, `overall_score`, `needs_review` |

## Requirements

- Python 3.11+
- LLM API key (OpenAI, DeepSeek, MiniMax, Qwen, dll)
