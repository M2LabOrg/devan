# MCP Design & Deploy

A comprehensive repository for **designing, developing, and deploying Model Context Protocol (MCP) servers**.

This repository serves as both a **learning resource** (with demo MCP servers) and a **production toolkit** (with deployment-ready servers and guides).

---

## What is MCP?

The [Model Context Protocol (MCP)](https://modelcontextprotocol.io/) is an open protocol that enables AI assistants to securely connect with external tools and data sources. Think of it as a "USB-C port for AI applications" - standardized, extensible, and universal.

---

## Repository Structure

This repository contains **8 MCP server implementations**:

| Server | Purpose | Transport |
|--------|---------|-----------|
| **excel-retriever** | Full Excel + OpenSearch integration | stdio |
| **excel-pipeline** | Robust Excel extraction, modelling & validation | stdio |
| **pdf-extractor** | PDF extraction with layout analysis and OCR | stdio |
| **prompt-engineering** | Structured prompt templates and PDF summarisation | stdio |
| **guardrail** | LLM output safety, secret scanning, compliance | stdio |
| **webdesign** | AI-powered React website generation | stdio |
| **webscraper** | Web scraping with job management | stdio |
| **document** | Unified Excel + PDF + Word + Parquet server | stdio |

---

## Quick Start

### 🐳 Docker (Recommended — works on Windows, Mac & Linux)

No Python setup needed. Everything — the client UI, all MCP servers, and a
local Ollama LLM — runs inside containers.

**Prerequisites**: [Docker Desktop](https://www.docker.com/products/docker-desktop/)

```bash
git clone https://github.com/M2LabOrg/mcp-design-deploy.git
cd mcp-design-deploy

./setup.sh        # choose model, build image, pull LLM (~10 min first time)
make start        # → open http://localhost:5001
```

> **First run** downloads the Docker image layers and your chosen Ollama model
> (~2 GB). Subsequent starts are instant — the model is cached in a Docker volume.

Other useful commands:

```bash
make stop         # stop all containers
make restart      # restart app container only (after code changes)
make logs         # follow live app logs
make build        # rebuild image after dependency changes
make shell        # open a shell inside the running container
```

To switch models later, edit `.env` (created by `setup.sh`) and run `make build`.

---

### Manual Setup (without Docker)

#### Running the Client UI

```bash
cd client
./start.sh
```

The UI will be available at **http://localhost:5001**.

> Requires Python 3.10+, `uv`, and [Ollama](https://ollama.ai) running locally.

#### For Learning (MCP Inspector)

```bash
# Choose a demo server
cd excel_retriever_demo    # or prompt_mcp_demo
cd mcp_project

# Setup
uv init
uv venv
source .venv/bin/activate
uv add mcp [other-deps]

# Run with Inspector
npx @modelcontextprotocol/inspector uv run server.py
```

### For Production (Deployment)

```bash
# Choose a production server
cd webdesign_mcp  # or excel_retriever
cd mcp_project

# Local development
uv init && uv venv && source .venv/bin/activate
uv add mcp
python server.py

# Deploy to Azure (see deployment guides)
# Deploy to Docker (Mac Mini, cloud VMs)
```

---

### Hermes Agent (Learning-Capable Alternative)

[Hermes Agent](https://github.com/NousResearch/hermes-agent) by Nous Research is an open-source agent that **builds skills from experience** — it learns your workflows across sessions and gets faster over time. It natively supports MCP, so all servers in this repo plug straight in.

```bash
# Install Hermes (once)
curl -fsSL https://raw.githubusercontent.com/NousResearch/hermes-agent/main/scripts/install.sh | bash

# Register all MCP servers with Hermes
./hermes/install.sh

# Start
hermes
```

Hermes is complementary to the DEVAN web client: use DEVAN for the polished UI, use Hermes when you want the agent to remember and improve across sessions.

See [`hermes/README.md`](hermes/README.md) and [`docs/hermes-integration.md`](docs/hermes-integration.md) for details.

---

## Server Details

### 1. Excel Retriever Demo
**Purpose**: Simplified MCP server for teaching fundamentals  
**Features**:
- List, extract, and query Excel files
- Row-range selection for large files
- Docling chunking for LLM processing
- CSV/JSON conversion
- **No OpenSearch** (simpler setup)

**Tech Stack**: Python, docling, pandas, MCP

**Folder**: `excel_retriever_demo/`

---

### 2. Prompt MCP Demo
**Purpose**: Structured prompt engineering demonstration  
**Features**:
- PDF content extraction (docling/PyPDF2)
- Structured prompt templates (Instruction + Context + Constraints)
- Executive summary generation
- Introduction generation
- Custom prompt construction

**Tech Stack**: Python, docling, MCP

**Folder**: `prompt_mcp_demo/`

---

### 3. Excel Retriever (Full)
**Purpose**: Production Excel processing with search  
**Features**:
- All demo features plus:
- OpenSearch integration for large datasets
- Indexing and search capabilities
- Production-grade error handling

**Tech Stack**: Python, docling, pandas, OpenSearch, MCP

**Folder**: `excel_retriever/`

---

### 4. Excel Pipeline (Robust)
**Purpose**: Structured Excel data extraction, canonical modelling, validation, and export  
**Features**:
- Workbook triage (supported / warnings / review / unsupported)
- Multi-parser table detection with confidence scoring
- Canonical data model (assets, KPIs, measurements, scenarios)
- Validation with reconciliation and readiness checks
- Full lineage/provenance tracking for every data point
- Downstream-ready JSON export (report_ready, validation_report, figure_specs)
- Grounded natural-language queries over validated data
- End-to-end orchestration in a single tool call

**Tech Stack**: Python, openpyxl, pandas, MCP (FastMCP)

**Folder**: `servers/excel-pipeline/`

---

### 5. WebDesign MCP ⭐
**Purpose**: AI-powered React website generation  
**Features**:
- **Analyze use cases** and auto-generate design specs
- **Recommend templates** (landing, corporate, portfolio, dashboard, ecommerce, docs)
- **Color palettes** (corporate, energy, dark_modern, minimal)
- **Generate complete projects** (scaffold with all files)
- **Component templates** (Hero, Card, Button, Navigation, Testimonial, Pricing, ContactForm, etc.)
- **Design tokens** (CSS variables, Tailwind config)

**Tech Stack**: Python, MCP, React, TypeScript, Tailwind CSS

**Folder**: `webdesign_mcp/`

**Deployment Guides**:
- `DEPLOY_AZURE.md` - Enterprise Azure deployment with Private Endpoints
- `DEPLOY_MAC_DOCKER.md` - Docker deployment on Mac Mini
- `ROADMAP.md` - Future improvements and gamification plans

---

## Deployment Options

### Local Development
- **MCP Inspector**: `npx @modelcontextprotocol/inspector`
- **Windsurf IDE**: Add to `mcp_config.json`
- **Direct execution**: `uv run server.py`

### Production Deployment

| Platform | Method | Security | Cost |
|----------|--------|----------|------|
| **Azure** | Container Apps + Private Endpoint | Enterprise (Private networking, Managed Identity) | ~€40-50/month |
| **Mac Mini** | Docker (Docker Compose) | Containerized isolation | Free (hardware) |
| **VPS/Cloud** | Docker/Docker Compose | Standard container security | Varies |

**Deployment Guides**:
- See `webdesign_mcp/DEPLOY_AZURE.md` for enterprise Azure setup
- See `webdesign_mcp/DEPLOY_MAC_DOCKER.md` for Mac Mini setup

---

## Common MCP Tools by Server

### Excel Servers (excel_retriever*)
- `list_excel_files` - Discover files
- `extract_excel_content` - Full extraction
- `extract_excel_rows` - Row-range selection
- `chunk_excel_content` - Docling chunking
- `query_excel_data` - SQL-like queries
- `convert_excel_to_csv` - CSV export
- `convert_excel_to_json` - JSON export
- `index_excel_in_opensearch` - Search indexing (full version only)

### Excel Pipeline Server (excel-pipeline)
- `triage_workbook` - Assess workbook support level
- `inspect_workbook_structure` - Sheet inventory and metadata
- `detect_candidate_tables` - Find tabular regions with confidence
- `build_canonical_model` - Map to business entities (assets, KPIs, measurements)
- `validate_canonical_model` - Consistency, unit, and completeness checks
- `get_lineage` - Provenance for any data point
- `export_ready_json` - Downstream-ready JSON package
- `prepare_figure_specs` - Chart specifications for rendering
- `create_report_bundle` - Full report package export
- `grounded_query_validated_data` - Query validated data in natural language
- `process_workbook_end_to_end` - Full pipeline in one call

### Prompt Server (prompt_mcp_demo)
- `list_pdf_files` - Discover PDFs
- `extract_pdf_content` - Text extraction
- `get_prompt_template` - Get prompt templates
- `generate_executive_summary` - Auto-generate prompts
- `create_custom_prompt` - Build custom prompts

### WebDesign Server (webdesign_mcp)
- `analyze_use_case` - AI-powered design spec generation
- `list_design_templates` - Website templates
- `list_color_palettes` - Design system colors
- `generate_project_scaffold` - Complete React project
- `get_component_template` - React components
- `list_available_components` - Component library
- `get_design_tokens` - CSS/Tailwind tokens

---

## Security

MCP defines four mechanisms that servers can use to improve security posture.
Below is an honest assessment of each and what is implemented here.

---

### Authentication

**Applies to: HTTP/SSE transport only.**

All servers in this repo use `stdio` transport (spawned as subprocesses). In stdio mode the
operating system's process-isolation boundary is the security perimeter — no bearer tokens or
OAuth flows are needed. If you switch to HTTP transport for remote access, the MCP spec requires
OAuth 2.0 with PKCE:

```python
# Example: enable HTTP transport with built-in OAuth (mcp >= 1.x)
mcp.run(transport="streamable-http", host="0.0.0.0", port=8080)
# Add OAuth middleware per your identity provider
```

For external service credentials (OpenSearch, Anthropic, Veracode, Firecrawl), all servers
already follow the env-var pattern — no secrets are hard-coded.

---

### Roots (Path Validation) ✅ Implemented

MCP Roots is a client capability: the client tells the server which directories it is authorised
to access. Servers should reject file paths that fall outside those roots.

All file-accessing servers (`excel-retriever`, `pdf-extractor`, `document`) now enforce a
`_validate_path()` guard on every tool that accepts a `file_path` argument:

```python
def _validate_path(path: str) -> str:
    """Reject paths outside the server's configured directories."""
    resolved = os.path.realpath(os.path.abspath(path))
    for allowed in _ALLOWED_DIRS:
        allowed_resolved = os.path.realpath(os.path.abspath(allowed))
        if resolved.startswith(allowed_resolved + os.sep) or resolved == allowed_resolved:
            return resolved
    raise ValueError(f"Access denied: {resolved} is outside allowed dirs: {_ALLOWED_DIRS}")
```

`_ALLOWED_DIRS` is populated from the server's env-var configuration (e.g. `EXCEL_DIR`,
`PDF_DIR`, `WORD_DIR`). This prevents path-traversal attacks (`../../etc/passwd`) and symlink
escapes regardless of what the LLM client sends.

**Full MCP roots** (client-declared, async): when your client supports the `roots` capability
you can upgrade to dynamic roots by replacing the env-var lookup with:

```python
roots = await ctx.session.list_roots()
allowed = [r.uri.replace("file://", "") for r in roots.roots]
```

---

### Sampling ✅ Implemented (`pdf-extractor`)

MCP Sampling lets a server delegate LLM calls back to the *connected client* instead of holding
its own API key. The `describe_figures` tool in `pdf-extractor` now prefers sampling:

```python
@mcp.tool()
async def describe_figures(file_path, ..., ctx: Context = None):
    sampling_available = (
        ctx is not None
        and getattr(ctx.session.client_params.capabilities, "sampling", None) is not None
    )
    if sampling_available:
        result = await ctx.session.create_message(     # ← no API key on server
            messages=[SamplingMessage(role="user", content=MCPImageContent(...))],
            max_tokens=300,
            system_prompt="Describe this PDF figure concisely...",
        )
    else:
        result = anthropic_client.messages.create(...)  # ← API key fallback
```

Security benefits:
- Server no longer needs `ANTHROPIC_API_KEY` when the client supports sampling
- LLM calls are billed to the client operator, not the server owner
- The human-in-the-loop approval flow (if configured by the client) applies to all LLM requests

**To add sampling to other servers** (e.g. `document`'s `describe_pdf_figures`), follow the same
pattern: make the tool `async def`, add `ctx: Context = None`, and check
`ctx.session.client_params.capabilities.sampling`.

---

### Composability

MCP composability means one server acting as an MCP *client* to another server, enabling
tool-chaining pipelines (e.g. `guardrail` calling `document` to scan extracted text).

This repo is not yet wired for server-to-server MCP calls, but the pattern is straightforward:

```python
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

params = StdioServerParameters(command="uv", args=["run", "document_server.py"])
async with stdio_client(params) as (read, write):
    async with ClientSession(read, write) as session:
        await session.initialize()
        result = await session.call_tool("extract_pdf", {"file_path": "..."})
```

Current architecture keeps servers independent since the `document` server already bundles Excel
+ PDF + Word capabilities. Composability is most valuable when you want `guardrail` or another
meta-server to orchestrate multiple specialist servers.

---

## Design Philosophy

### For Demos
- **Simplified**: Remove complexity (e.g., no OpenSearch in demo)
- **Educational**: Clear comments, step-by-step guides
- **Interactive**: Jupyter notebooks with `%%writefile` magic
- **Self-contained**: Everything in one folder

### For Production
- **Complete**: Full feature sets
- **Scalable**: Cloud-ready architectures
- **Secure**: Private networking, managed identities
- **Documented**: Deployment guides, troubleshooting

---

## Tech Stack Overview

### Core Technologies
- **MCP SDK**: `mcp>=1.26.0` (FastMCP)
- **Python**: 3.10+
- **Package Manager**: `uv` (modern Python packaging)

### Server-Specific
- **Excel**: docling, pandas, openpyxl, OpenSearch (optional)
- **PDF**: docling, PyPDF2, reportlab
- **WebDesign**: Pure Python (generates React/TS code)

### Frontend (Generated by WebDesign MCP)
- **React**: 18.x
- **TypeScript**: 5.x
- **Build Tool**: Vite
- **Styling**: Tailwind CSS
- **UI Library**: shadcn/ui patterns
- **Icons**: Lucide React
- **Animation**: Framer Motion

---

## Repository Rename Suggestion

**Current**: `mcp-excel-retriever`  
**Suggested**: `mcp-design-deploy` or `mcp-servers`

### Why Rename?

The current name `mcp-excel-retriever` no longer reflects the repository's scope:

- Originally: Just Excel processing
- Now: Excel + PDF + WebDesign demos and production servers
- Future: More MCP servers, deployment guides, patterns

### Proposed Names

1. **`mcp-design-deploy`** ⭐ Recommended
   - Clear: Design MCP servers + Deploy them
   - Professional: Good for enterprise context
   - Extensible: Covers future servers

2. **`mcp-servers`**
   - Simple and direct
   - Clear purpose
   - Generic enough for expansion

3. **`mcp-toolkit`**
   - Implies comprehensive resource
   - Good for library/tool collection

4. **`ai-mcp-servers`**
   - Explicit AI connection
   - SEO-friendly

### How to Rename

```bash
# On GitHub website:
# 1. Go to repository Settings
# 2. Under "Repository name", click Rename
# 3. Enter new name: mcp-design-deploy
# 4. Click Rename

# Update local clone:
git remote set-url origin https://github.com/M2LabOrg/mcp-design-deploy.git

# Verify
git remote -v
```

**Note**: GitHub automatically redirects old URLs to new ones.

---

### Tauri Desktop App: Changes to templates not appearing

**Symptom**: You updated `client/templates/setup.html` (or `index.html`), rebuilt the Tauri app, but the old version still appears.

**Root Cause**: The Rust backend caches client files in the app's data directory (`~/Library/Application Support/io.m2lab.devan/` on macOS) and only re-syncs when the app version changes (see `sync_client_to_runtime()` in `src-tauri/src/main.rs`).

**How Template Syncing Works**:

1. **Build time**: `sync_templates.sh` (run via `beforeBuildCommand`) copies `client/templates/` → `src-tauri/ui/`
2. **Bundle time**: Tauri bundles `src-tauri/ui/` into the app binary
3. **Runtime**: On first launch, Rust copies bundled files to the writable app data directory
4. **Version gating**: The runtime only re-syncs when `tauri.conf.json` version differs from the cached version stamp

**Fix**: Bump the version in both:
- `src-tauri/tauri.conf.json` → `"version": "X.Y.Z"`
- `src-tauri/Cargo.toml` → `version = "X.Y.Z"`

Then rebuild:
```bash
npm run tauri build
```

**Quick Checklist for Template Changes**:

```bash
# 1. Edit the source file
vi client/templates/setup.html

# 2. Sync to src-tauri/ui/ (optional - build does this automatically)
bash sync_templates.sh

# 3. Bump version in BOTH files
#    - src-tauri/tauri.conf.json
#    - src-tauri/Cargo.toml

# 4. Build
npm run tauri build

# 5. The new app will sync fresh templates on first launch
```

**Testing without rebuilding**: Delete the runtime cache to force a fresh sync:
```bash
# macOS
rm -rf ~/Library/Application\ Support/io.m2lab.devan/

# Then run the app again
npm run tauri dev
```

---

## Troubleshooting

### Tauri/Rust build fails with `SIGKILL` (out of memory)

**Symptom**: `cargo build` or `npm run dev` exits with `signal: 9, SIGKILL: kill` during Rust compilation.

**Cause**: The Rust compiler runs out of RAM. On a 16GB Mac mini with active workloads, free memory can drop below 100MB — not enough to compile Tauri dependencies.

**Fix** (already applied in `src-tauri/.cargo/config.toml`):

1. Reduce debug info and limit parallel jobs:
   ```toml
   # src-tauri/.cargo/config.toml
   [build]
   jobs = 1

   [profile.dev]
   debug = 0
   split-debuginfo = "unpacked"
   ```

2. Free inactive memory before building:
   ```bash
   sudo purge
   ```

3. Then build:
   ```bash
   cd src-tauri
   cargo build --no-default-features
   # or from project root:
   npm run dev
   ```

Close browsers and other memory-heavy apps before building if the issue persists.

---

## Getting Started

### Prerequisites

- **macOS/Linux/Windows** with WSL
- **Python 3.10+**
- **uv**: `curl -LsSf https://astral.sh/uv/install.sh | sh`
- **Node.js**: For MCP Inspector (`npm install -g @modelcontextprotocol/inspector`)

### Choose Your Path

**Path 1: I want to learn MCP**
→ Start with `excel_retriever_demo/` or `prompt_mcp_demo/`

**Path 2: I need to deploy to Azure**
→ Go to `webdesign_mcp/` → Read `DEPLOY_AZURE.md`

**Path 3: I want to run on my Mac Mini**
→ Go to `webdesign_mcp/` → Read `DEPLOY_MAC_DOCKER.md`

**Path 4: I need Excel processing**
→ Use `excel_retriever/` (full version with OpenSearch)

**Path 5: I want an agent that learns my workflows**
→ Run `./hermes/install.sh` then `hermes` — see [`docs/hermes-integration.md`](docs/hermes-integration.md)

---

## Documentation Index

| Document | Location | Purpose |
|----------|----------|---------|
| **Main README** | `README.md` | This file - overview |
| **Demo Instructions** | `*/demo_instructions.md` | Step-by-step setup |
| **API Reference** | `*/README.md` | Tool documentation |
| **Azure Deployment** | `webdesign_mcp/DEPLOY_AZURE.md` | Enterprise Azure |
| **Docker/Mac Deployment** | `webdesign_mcp/DEPLOY_MAC_DOCKER.md` | Mac Mini setup |
| **Roadmap** | `webdesign_mcp/ROADMAP.md` | Future improvements |
| **Jupyter Tutorial** | `*/demo_notebook.ipynb` | Interactive learning |
| **Hermes Integration** | `docs/hermes-integration.md` | Learning agent setup |

---

## Contributing

This is an M2Lab.io project repository. To add a new MCP server:

1. Create folder: `new_mcp_demo/` or `new_mcp_service/`
2. Add structure:
   ```
   new_mcp/
   ├── mcp_project/
   │   ├── server.py
   │   └── pyproject.toml
   ├── README.md
   └── demo_instructions.md
   ```
3. Follow patterns from existing servers
4. Update this README

---

## Future Plans

See `webdesign_mcp/ROADMAP.md` for detailed roadmap:

- [ ] Gamification components (progress bars, badges, quizzes)
- [ ] More design system templates
- [ ] Industry-specific templates (SaaS, healthcare, finance)
- [ ] CI/CD pipelines for Azure
- [ ] Additional MCP servers (data analysis, document processing)

---

## License

MIT — for personal and commercial use.

---

## Contact

- **Organization**: M2Lab.io (M2LabOrg on GitHub)
- **Website**: https://m2lab.io
- **Purpose**: Tool development and knowledge sharing

---

**Repository**: https://github.com/M2LabOrg/mcp-design-deploy

---

*Last Updated: April 2026*
