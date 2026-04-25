# Web Scraper MCP Server

Intelligent web scraping as an MCP server — extract structured data from any website using free or premium engines.

## Features

- **Dual Engine Architecture**
  - 🆓 **BeautifulSoup** — Free, static HTML, CSS selector extraction
  - ⭐ **Firecrawl** — Premium, JavaScript rendering, anti-bot bypass, AI-powered extraction
- **Smart Extraction** — Define CSS selector schemas to pull exactly the data you need
- **Search-Then-Scrape** — Search the web first, then scrape selected results
- **Job Management** — Start, pause, resume, stop, restart jobs with full state persistence
- **Crash Recovery** — Jobs checkpoint after every URL; resume from the last position
- **CRUD Operations** — View, edit, delete individual scraped records
- **Export** — JSON, CSV, Excel, SQLite, Markdown
- **Real-time Streaming** — Results flow to the UI as each page is scraped
- **Project Integration** — Works with the DEVAN Agent project folder structure

## Quick Start

### As MCP Server (VS Code / Copilot)

```bash
cd servers/webscraper/mcp_project
uv sync
uv run webscraper_server.py
```

### Via DEVAN Agent UI

1. Open http://localhost:5001
2. Enable "Web Scraper MCP" in the command bar
3. Click the "Web Scraper" action chip
4. Enter URLs or search for them
5. Start scraping!

## MCP Tools

| Tool | Description |
|------|-------------|
| `search_urls` | Search the web for URLs matching a query |
| `analyze_page` | Preview page structure before scraping |
| `suggest_schema` | Auto-suggest CSS selectors for a page |
| `scrape_url` | Scrape a single URL |
| `scrape_batch` | Start batch scraping multiple URLs |
| `crawl_site` | Crawl a site following links |
| `list_jobs` | List all scraping jobs |
| `get_job_status` | Get job progress details |
| `pause_job` / `resume_job` / `cancel_job` | Job lifecycle control |
| `get_results` | Paginated results with search |
| `update_record` / `delete_record` | CRUD on individual records |
| `export_job_results` | Export to JSON/CSV/Excel/SQLite/Markdown |
| `configure_engine` | Set Firecrawl API key |
| `get_engine_status` | Check engine availability |

## Extraction Schema

Define what data to extract using CSS selectors:

```json
{
  "title": "css:h1",
  "prices": "css:.product-price[]",
  "links": "css:a@href[]",
  "description": "css:meta[name='description']@content"
}
```

- `css:SELECTOR` — Extract text from first match
- `css:SELECTOR[]` — Extract list of all matches
- `css:SELECTOR@attr` — Extract attribute value

## Firecrawl Setup

1. Get a free API key at [firecrawl.dev](https://firecrawl.dev) (500 free credits/month)
2. Set via environment: `export FIRECRAWL_API_KEY=fc-...`
3. Or configure in the DEVAN UI: Web Scraper → ⚙️ Settings → Save API Key

## Engine Comparison

| Feature | BeautifulSoup | Firecrawl |
|---------|:---:|:---:|
| Static HTML | ✅ | ✅ |
| JavaScript pages | ❌ | ✅ |
| Anti-bot bypass | ❌ | ✅ |
| Rate limiting | Manual (1s delay) | Managed |
| AI extraction | ❌ | ✅ |
| Cost | Free | API key required |

## Dependencies

- `mcp>=1.26.0` — MCP framework
- `httpx` — Async HTTP client
- `beautifulsoup4` + `lxml` — HTML parsing
- `firecrawl-py` — Firecrawl SDK (optional)
- `openpyxl` — Excel export
- `pandas` — Data manipulation
