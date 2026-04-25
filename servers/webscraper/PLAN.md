# Web Scraper MCP — Development Plan

## Overview

A production-grade MCP server for intelligent web scraping that integrates with the DEVAN Agent UI. Supports both premium (Firecrawl) and free (BeautifulSoup + httpx) scraping engines, with real-time streaming, job persistence, CRUD operations, and structured data export.

---

## Architecture

```
servers/webscraper/
├── PLAN.md                    # This file
├── README.md                  # User documentation
├── mcp_project/
│   ├── pyproject.toml         # Dependencies (uv)
│   ├── webscraper_server.py   # FastMCP server — tool definitions
│   ├── engines/
│   │   ├── __init__.py
│   │   ├── base.py            # Abstract scraping engine interface
│   │   ├── firecrawl_engine.py # Firecrawl API engine (premium)
│   │   └── bs4_engine.py      # BeautifulSoup + httpx engine (free)
│   ├── job_manager.py         # Job lifecycle, state persistence, resume
│   ├── extractors.py          # Structured data extraction (CSS/XPath selectors)
│   └── exporters.py           # Export to JSON, CSV, Excel, SQLite
```

---

## Core Features

### 1. Dual Scraping Engines

| Feature | Firecrawl (Premium) | BeautifulSoup (Free) |
|---------|---------------------|----------------------|
| JavaScript rendering | ✅ Full | ❌ Static HTML only |
| Anti-bot bypass | ✅ Built-in | ❌ None |
| Rate limiting | ✅ Managed | ⚠️ Manual (we add it) |
| Structured extraction | ✅ AI-powered | ✅ CSS/XPath selectors |
| Crawl depth | ✅ Multi-page | ✅ Multi-page |
| Cost | API token required | Free |

**Engine selection:** User chooses engine explicitly, or LLM recommends based on target site complexity. UI shows a clear warning when using free engine about limitations.

### 2. Firecrawl Token Management

- Users provide their own Firecrawl API key via:
  - Environment variable `FIRECRAWL_API_KEY`
  - Flask UI configuration panel (stored in config.json, encrypted at rest)
  - MCP tool parameter (per-call override)
- Key validation on entry with test request
- Usage tracking to help users monitor their quota

### 3. Intelligent Scraping Parameters

Users describe what they want in natural language. The LLM translates this into structured scraping parameters:

```
User: "Get all product names and prices from this e-commerce page"
→ LLM decides: CSS selectors for .product-name, .price
→ Engine: Firecrawl with extract schema, or BS4 with CSS selectors
```

**Configurable parameters:**
- Target URL(s) or search query (for discovery)
- Extraction schema (fields to capture)
- Crawl depth (single page / follow links / full site)
- Page limit (cost control)
- Include/exclude URL patterns
- Wait strategies (for JS-heavy pages)
- Output format preference

### 4. Search-Then-Scrape Workflow

When users don't have specific URLs:
1. User describes what they're looking for
2. System uses search (DuckDuckGo or Google Custom Search) to find relevant URLs
3. Results presented for user approval
4. Selected URLs queued for scraping

### 5. Progressive Results & User Control

**Stream-first approach:**
- Results stream to UI as each page/item is scraped
- User sees data flowing in real-time via Socket.IO
- After first batch (e.g., 5 results), user is prompted: "Continue? (N more pages remaining)"
- Cost estimate shown for Firecrawl before continuing

**Job controls:**
- ▶️ Start — Begin scraping
- ⏸️ Pause — Suspend at next safe point (between pages)
- ▶️ Resume — Continue from pause point
- ⏹️ Stop — End job, keep partial results
- 🔄 Restart — Resume from last checkpoint (crash recovery)

### 6. Job State & Persistence

Each scraping job is persisted to disk:

```json
{
  "job_id": "uuid",
  "status": "running|paused|completed|failed|stopped",
  "engine": "firecrawl|beautifulsoup",
  "created_at": "ISO8601",
  "updated_at": "ISO8601",
  "config": {
    "urls": ["..."],
    "schema": {...},
    "crawl_depth": 1,
    "page_limit": 50
  },
  "progress": {
    "total_urls": 50,
    "completed": 23,
    "failed": 1,
    "failed_urls": [{"url": "...", "error": "..."}]
  },
  "checkpoint": {
    "last_url_index": 22,
    "next_url": "...",
    "cursor": null
  }
}
```

**Crash recovery:** On restart, job manager reads checkpoint, skips already-scraped URLs.

### 7. CRUD Operations on Results

- **Create** — New scraping job
- **Read** — View results (paginated, filterable, searchable)
- **Update** — Edit individual scraped records, add notes/tags
- **Delete** — Remove individual records or entire job results

### 8. Export System

Export partial or full results to:
- **JSON** — Full structured data
- **CSV** — Flat tabular format
- **Excel** (.xlsx) — With formatting and metadata sheet
- **SQLite** — Portable database file
- **Markdown** — Tables for documentation

Download available at any time (partial during scraping, full after completion).

### 9. Project Integration

Scraping jobs live inside the `client/projects/` structure:

```
client/projects/<project_name>/
├── input/           # Source URLs list, search configs
├── output/          # Scraped data (JSON per job)
├── scripts/         # Generated batch_scrape.py for VS Code
├── scrape_jobs/     # Job state files
│   ├── <job_id>.json      # Job metadata + checkpoint
│   └── <job_id>_data.json # Scraped results
└── exports/         # Downloaded files (CSV, Excel, etc.)
```

Uses shared `.venv` at `client/projects/.venv` level.

---

## MCP Tools (FastMCP)

### Discovery & Planning
| Tool | Description |
|------|-------------|
| `search_urls` | Search the web for URLs matching a query |
| `analyze_page` | Preview a page structure before scraping |
| `suggest_schema` | LLM suggests extraction fields for a given URL |

### Scraping
| Tool | Description |
|------|-------------|
| `scrape_url` | Scrape a single URL with given schema |
| `scrape_batch` | Start batch scraping of multiple URLs |
| `crawl_site` | Crawl a site following links with depth control |

### Job Management
| Tool | Description |
|------|-------------|
| `list_jobs` | List all scraping jobs (with status) |
| `get_job_status` | Get detailed status of a specific job |
| `pause_job` | Pause a running job |
| `resume_job` | Resume a paused/failed job |
| `cancel_job` | Cancel and stop a job |
| `delete_job` | Delete job and its data |

### Data Operations
| Tool | Description |
|------|-------------|
| `get_results` | Get scraped results (paginated, filterable) |
| `update_record` | Edit a specific scraped record |
| `delete_record` | Delete a specific record |
| `search_results` | Full-text search across scraped data |

### Export
| Tool | Description |
|------|-------------|
| `export_results` | Export results to CSV/JSON/Excel/SQLite/Markdown |
| `get_export_formats` | List available export formats |

### Configuration
| Tool | Description |
|------|-------------|
| `configure_engine` | Set scraping engine and API keys |
| `get_engine_status` | Check engine availability and quota |

---

## Flask Client Integration

### New API Routes

```
POST   /api/scrape/start          Start a scraping job
POST   /api/scrape/search         Search for URLs
GET    /api/scrape/jobs            List all jobs
GET    /api/scrape/jobs/<id>       Job details + progress
POST   /api/scrape/jobs/<id>/pause    Pause job
POST   /api/scrape/jobs/<id>/resume   Resume job
POST   /api/scrape/jobs/<id>/stop     Stop job
DELETE /api/scrape/jobs/<id>       Delete job
GET    /api/scrape/jobs/<id>/results  Get results (paginated)
PUT    /api/scrape/jobs/<id>/results/<rid>  Update record
DELETE /api/scrape/jobs/<id>/results/<rid>  Delete record
GET    /api/scrape/jobs/<id>/export   Export results
POST   /api/scrape/configure       Configure engine/keys
GET    /api/scrape/engine/status    Engine status
```

### Socket.IO Events

```
scrape_progress    Per-URL progress updates
scrape_result      Individual result streamed
scrape_paused      Job paused notification
scrape_resumed     Job resumed notification
scrape_complete    Job finished
scrape_error       Error notification
scrape_confirm     Ask user to continue (cost gate)
```

### UI Components (Zen Design System)

1. **Scraper Tab** in command bar — dedicated scraping panel
2. **URL Input** — Single URL, multiple URLs (textarea), or search query
3. **Engine Selector** — Toggle between Firecrawl/BeautifulSoup with info tooltips
4. **Schema Builder** — Visual field definition (name, selector, type)
5. **Live Results Table** — Streaming data grid with sort/filter/search
6. **Progress Bar** — Per-job with pause/resume/stop controls
7. **Cost Indicator** — Firecrawl usage estimate (shown before continue)
8. **Export Panel** — Format selector + download button
9. **Job History** — List of past jobs with status badges

---

## Best Practices Included

### Rate Limiting & Politeness
- Configurable delay between requests (default: 1s for BS4)
- Respect `robots.txt` (check before crawling)
- User-Agent rotation for BS4 engine
- Firecrawl handles this automatically

### Error Handling & Resilience
- Retry with exponential backoff (3 attempts)
- Per-URL error tracking (don't fail entire job)
- Timeout per request (30s default)
- Connection pooling with httpx

### Security
- API keys stored in config, never logged
- URL validation (no local/private IPs — SSRF prevention)
- Content-type validation before parsing
- Sanitize extracted data (prevent XSS in UI display)
- Rate limit API endpoints to prevent abuse

### Data Quality
- Deduplication by URL
- Timestamp all records
- Store raw HTML + extracted data separately
- Validate extracted data against schema

---

## Development Phases

### Phase 1 — Core MCP Server ✱ Current
- [ ] Project structure & pyproject.toml
- [ ] Base engine interface
- [ ] BeautifulSoup engine (free)
- [ ] Firecrawl engine (premium)
- [ ] Job manager with state persistence
- [ ] Export system (JSON, CSV, Excel)
- [ ] Core MCP tools

### Phase 2 — Flask Integration
- [ ] API routes in app.py
- [ ] Socket.IO streaming events
- [ ] Scraper UI panel in index.html
- [ ] Project folder integration

### Phase 3 — Polish (Future)
- [ ] Search-then-scrape workflow
- [ ] Schema builder UI
- [ ] SQLite export
- [ ] VS Code batch_scrape.py generation
- [ ] Cost estimation for Firecrawl
- [ ] robots.txt checking

---

## Dependencies

```toml
[project]
dependencies = [
    "mcp>=1.26.0",          # FastMCP framework
    "httpx>=0.27.0",        # Async HTTP client
    "beautifulsoup4>=4.12",  # HTML parsing (free engine)
    "lxml>=5.0",            # Fast HTML/XML parser
    "firecrawl-py>=1.0.0",  # Firecrawl SDK (premium engine)
    "openpyxl>=3.1.0",      # Excel export
    "pandas>=2.0.0",        # Data manipulation + CSV
]
```
