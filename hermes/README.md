# Hermes Agent — Integration with mcp-design-deploy

[Hermes Agent](https://github.com/NousResearch/hermes-agent) by Nous Research is an open-source agent that **learns from use**. Unlike a stateless agent loop, Hermes builds a persistent skill library from every session — recording what worked, improving those procedures over time, and retrieving relevant context when you need it again.

This directory wires all nine MCP servers in this repo into Hermes, giving it document analysis, data modelling, web scraping, guardrails, and more — all growing smarter with every use.

---

## Why Hermes here?

| DEVAN client (current) | Hermes Agent |
|------------------------|--------------|
| Beautiful Zen web UI   | Terminal / messaging gateway |
| Stateless per session  | **Persistent skill memory across sessions** |
| Manually select servers| Auto-discovers enabled MCP tools |
| Up to 8 tool-call iterations | Adaptive, self-improving loop |
| Local Ollama / Azure   | Ollama + 200+ models via OpenRouter / Anthropic / OpenAI |

Hermes complements DEVAN rather than replacing it:
- Use **DEVAN** for the polished web interface and compliance/sandbox mode.
- Use **Hermes** when you want the agent to learn your workflows and get faster over time.

---

## Quick Start

```bash
# 1. Install Hermes (first time only)
curl -fsSL https://raw.githubusercontent.com/NousResearch/hermes-agent/main/scripts/install.sh | bash

# 2. Wire up all MCP servers
./hermes/install.sh

# 3. (Optional) pick your LLM — Ollama works out of the box
hermes model

# 4. Start chatting
hermes
```

That's it. Hermes discovers all registered tools automatically on first use.

---

## What the install script does

`install.sh`:
1. Resolves the absolute path of this repo (works wherever you cloned it).
2. Renders `config.yaml.template` → `config.yaml` with the real path substituted.
3. Appends the rendered config to `~/.hermes/config.yaml` (or creates it if missing).
4. Skips the merge safely if you already have an `mcp_servers:` section, and shows manual instructions instead.

---

## Registered MCP Servers

| Hermes name         | Server directory          | What it does |
|---------------------|---------------------------|--------------|
| `document`          | `servers/document/`       | Unified Excel / PDF / Word / Parquet extraction |
| `data-modelling`    | `servers/data-modelling/` | Schema inference, relational modelling, SQLite / Arrow export |
| `excel-pipeline`    | `servers/excel-pipeline/` | Robust Excel extraction with validation and lineage tracking |
| `excel-retriever`   | `servers/excel-retriever/`| Excel + OpenSearch full-text integration |
| `guardrail`         | `servers/guardrail/`      | PII detection, secret scanning, LLM output safety |
| `pdf-extractor`     | `servers/pdf-extractor/`  | PDF layout analysis, OCR, table and figure extraction |
| `prompt-engineering`| `servers/prompt-engineering/` | Prompt templates and PDF summarisation |
| `webdesign`         | `servers/webdesign/`      | React component and page generation |
| `webscraper`        | `servers/webscraper/`     | Firecrawl / BeautifulSoup scraping with job management |

Each server runs via `uv run` inside its own `mcp_project/` virtualenv — no dependency conflicts.

---

## The Learning Loop — How It Works

Hermes maintains a **skill library**: after you complete a task it didn't know before, it writes a reusable procedure. The next time a similar task comes up, it retrieves that skill and completes the task faster — no prompt engineering needed.

Example progression with this project's servers:

| Session | What happens |
|---------|-------------|
| 1st use | You ask Hermes to extract tables from a PDF and model the data. It figures it out step by step using `pdf-extractor` → `data-modelling`. |
| 2nd use | Same request. Hermes finds the "PDF → relational model" skill, runs it in one shot, 40% faster. |
| Later   | You refine the workflow (different output format). Hermes updates the skill. |

Skills are stored in `~/.hermes/skills/` as plain text — fully auditable and editable.

---

## LLM Configuration

Hermes works with any OpenAI-compatible endpoint, including local Ollama:

```bash
# Use a local Ollama model (no API key needed)
hermes model
# → select "Ollama" → pick your model

# Or set via env var
export HERMES_MODEL="ollama/llama3.2"
hermes
```

For cloud providers, `hermes model` walks you through API key setup.

---

## Tips

- **Seed the skill library early**: the first time you run a multi-step workflow (e.g. scrape → extract → model → export), describe your intent clearly. Hermes will store that as a skill.
- **Review your skills**: `hermes skills list` shows everything it has learned. Edit or delete entries in `~/.hermes/skills/` if a skill needs updating.
- **Search past sessions**: `hermes memory search "<query>"` retrieves relevant context from previous conversations — useful when revisiting a project after a break.
- **Parallel workstreams**: Hermes can spawn isolated subagents for independent tasks. Ask it to "process these three files in parallel" and it will.

---

## Files

```
hermes/
  config.yaml.template   Source of truth for MCP server definitions (PROJECT_ROOT placeholder)
  config.yaml            Rendered config (generated by install.sh, gitignored)
  install.sh             Setup script
  README.md              This file
```

`config.yaml` (the rendered output) is gitignored because it contains your machine's absolute paths.
