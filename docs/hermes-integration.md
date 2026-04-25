# Hermes Agent Integration

## What is Hermes?

[Hermes Agent](https://github.com/NousResearch/hermes-agent) (by Nous Research, released February 2026) is an open-source autonomous agent with a built-in **learning loop**. It creates reusable skills from experience, improves them through use, and builds a persistent memory of your projects and preferences — all locally, with no telemetry.

It natively supports the **Model Context Protocol (MCP)**, making it a natural companion to this project's server collection.

> "The only agent with a built-in learning loop — it creates skills from experience, improves them during use, nudges itself to persist knowledge, searches its own past conversations, and builds a deepening model of who you are across sessions."
> — Nous Research

---

## Why Add It to This Project?

This project already provides nine high-quality MCP servers covering document extraction, data modelling, web scraping, guardrails, and more. The DEVAN client provides a clean web UI to use them.

What's currently missing is **continuity**: every DEVAN session starts fresh. Hermes fills that gap:

- It remembers how you used `pdf-extractor` → `data-modelling` last Tuesday.
- It builds a skill for that sequence and runs it faster next time.
- It tracks your project context across sessions so you don't have to re-explain it.

Hermes and DEVAN address different needs and coexist cleanly — they share the same MCP servers via stdio.

---

## Architecture

```
┌────────────────────────────────────────────┐
│  Hermes Agent CLI                          │
│  ~/.hermes/                                │
│    skills/        ← learned procedures     │
│    memory/        ← session summaries      │
│    config.yaml    ← MCP server registry    │
└──────────────────┬─────────────────────────┘
                   │  stdio (MCP protocol)
       ┌───────────┼────────────────────┐
       │           │                    │
  document    data-modelling      webscraper
  (uv run)    (uv run)            (uv run)
  ... and 6 more servers
```

Hermes spawns each server as a subprocess on demand, discovers its tools, and shuts it down when idle — identical to how the DEVAN client works.

---

## Setup

### 1. Install Hermes

```bash
curl -fsSL https://raw.githubusercontent.com/NousResearch/hermes-agent/main/scripts/install.sh | bash
```

Supported: Linux, macOS, WSL2, Termux.

### 2. Register the MCP Servers

From the repo root:

```bash
./hermes/install.sh
```

This renders `hermes/config.yaml.template` with your machine's absolute paths and merges the result into `~/.hermes/config.yaml`.

### 3. Choose an LLM

```bash
hermes model
```

Options include local **Ollama** (no API key, fully private), OpenRouter (200+ models), Anthropic Claude, OpenAI, Google Gemini, and any OpenAI-compatible endpoint.

### 4. Start

```bash
hermes
```

Hermes discovers all registered MCP tools automatically and is ready to use them.

---

## The Learning Loop in Practice

Hermes uses a three-layer memory system:

| Layer | Storage | Purpose |
|-------|---------|---------|
| **Skills** | `~/.hermes/skills/*.md` | Reusable procedures learned from tasks |
| **Session memory** | `~/.hermes/memory/` | FTS5-indexed summaries of past conversations |
| **User model** | `~/.hermes/profile.md` | Inferred preferences, project context, working style |

### Example: First use vs. learned use

**Session 1** — you ask:
> "Extract the tables from Q3-report.pdf, infer a relational schema, and export to SQLite."

Hermes reasons step-by-step: calls `pdf-extractor`, passes results to `data-modelling`, exports. At the end of the session it writes a skill:

```markdown
# Skill: PDF → Relational SQLite export
1. Call pdf-extractor.extract_tables(file) → structured data
2. Call data-modelling.infer_schema(data) → schema
3. Call data-modelling.export_sqlite(schema, output_path)
```

**Session 2** — same request, different file:
> "Do the same for Q4-report.pdf."

Hermes retrieves the skill, runs it in one pass. Nous Research benchmarks show ~40% faster completion versus a fresh instance.

---

## Recommended Workflows with This Server Set

| Goal | Servers involved | What Hermes learns |
|------|-----------------|-------------------|
| Document intelligence pipeline | `document` → `data-modelling` | Your preferred output format, column naming conventions |
| Compliance-aware extraction | `guardrail` → `pdf-extractor` | Which PII patterns matter for your domain |
| Research assistant | `webscraper` → `document` → `prompt-engineering` | Your summarisation style and report structure |
| Data product from Excel | `excel-pipeline` → `data-modelling` | Your canonical schema, validation rules |
| React UI from spec | `prompt-engineering` → `webdesign` | Your component library preferences |

---

## Differences vs. the DEVAN Client

| Feature | DEVAN Client | Hermes Agent |
|---------|-------------|-------------|
| Interface | Web UI (Zen design) | Terminal + Telegram/Discord/Slack/etc. |
| Session memory | None (stateless) | Persistent (FTS5, LLM summaries) |
| Skill learning | None | Built-in learning loop |
| Compliance mode | Yes (audit log, PII scan, guardrail) | Manual — use `guardrail` MCP server |
| Docker support | Yes (`make start`) | Not required (runs anywhere) |
| Best for | Demos, shared environments, web access | Personal productivity, long-running projects |

They use the same MCP servers and can run simultaneously without conflict.

---

## Files Added by This Integration

```
hermes/
  config.yaml.template   MCP server definitions (PROJECT_ROOT placeholder)
  config.yaml            Rendered config — gitignored, machine-specific
  install.sh             One-command setup
  .gitignore             Excludes rendered config
  README.md              Quick-start and tips
docs/
  hermes-integration.md  This file
```

---

## Troubleshooting

**Server fails to start**
- Run `uv sync` inside `servers/<name>/mcp_project/` to install its dependencies first.
- Check that `uv` is on your PATH: `which uv`.

**`hermes` command not found after install**
- Restart your shell or run `source ~/.bashrc` (or `~/.zshrc`).

**Config already has `mcp_servers:`**
- `install.sh` will skip the auto-merge and show you the manual steps.
- Back up and append: `cat hermes/config.yaml >> ~/.hermes/config.yaml`

**Skills seem wrong**
- Edit or delete entries in `~/.hermes/skills/` — they are plain Markdown files.
- Run `hermes skills list` to browse them.
