# DEVAN Agent

A desktop application for managing local LLM providers and MCP servers with a Zen-inspired interface.

## Quick Start

### Option A: Desktop App (Recommended)

1. Download the latest release for your platform (`.dmg` for macOS, `.msi` for Windows, `.AppImage` for Linux)
2. Install and open the app
3. The **setup wizard** will guide you through:
   - Checking prerequisites (Python, uv, Git)
   - Cloning the MCP servers repository
   - Creating the Python virtual environment
   - Setting up Ollama and pulling a default LLM model

### Option B: Run from Source

```bash
cd client
./start.sh
# Opens at http://localhost:5001
```

### Option C: Tauri Development

```bash
npm run dev   # from the project root
```

## First-Run Setup Wizard

When you launch the app for the first time (or without a configured environment), the setup wizard checks and installs everything you need:

| Step | What it does | Required? |
|------|-------------|-----------|
| **Python 3.10+** | Checks for a system Python installation | Yes |
| **uv** | Package manager for MCP server dependencies | Yes |
| **Git** | Needed to clone the MCP servers repository | Yes |
| **MCP Servers** | Clones/detects the server repository and updates paths in `config.json` | Yes |
| **Client Environment** | Creates a Python venv and installs Flask + dependencies | Yes |
| **Ollama + Model** | Checks for Ollama, optionally pulls `llama3.2` | Optional |

After setup completes, click **"Launch DEVAN Agent"** to enter the main interface.

### Installing Prerequisites

If the wizard detects missing dependencies, it shows download links:

- **Python**: [python.org/downloads](https://www.python.org/downloads/) or `brew install python` (macOS)
- **uv**: [docs.astral.sh/uv](https://docs.astral.sh/uv/getting-started/installation/) or `curl -LsSf https://astral.sh/uv/install.sh | sh`
- **Git**: [git-scm.com/downloads](https://git-scm.com/downloads) or `xcode-select --install` (macOS)
- **Ollama**: [ollama.com/download](https://ollama.com/download)

## Features

- **Local LLM Support** — Ollama, LM Studio, Azure Foundry, GitHub Copilot
- **MCP Server Management** — Enable/disable servers, real-time tool discovery
- **Zen Chat Interface** — Japanese minimalist design, command-bar-centric (press `Cmd+K`)
- **Project Workspaces** — Isolated folders for batch processing tasks
- **Document Processing** — PDF, Excel, Word extraction with OCR support
- **Web Scraping** — BeautifulSoup and Firecrawl integration
- **VS Code Integration** — Export MCP config for use in VS Code

## Architecture

```
Desktop App (Tauri)
    └── Flask Backend (client/app.py)
            ├── Local LLM APIs (Ollama, etc.)
            └── MCP Servers (stdio, each with own venv via uv)
                ├── Document MCP — PDF/Excel/Word extraction
                ├── Prompt Engineering MCP — Prompt templates
                ├── Guardrail MCP — Content moderation
                └── Web Design MCP — HTML/CSS generation
```

The app is lightweight (~50 MB) because:
- Only the Flask client and templates are bundled
- MCP server dependencies are installed on-demand via `uv sync`
- Heavy packages (torch, docling, easyocr) are installed at runtime when needed
- The client venv is created on first launch, not shipped in the bundle

## Configuration

Stored in `client/config.json`:

```json
{
  "mcp_servers": [
    { "id": "document_mcp", "enabled": true, "path": "/path/to/servers/document/mcp_project", ... }
  ],
  "llm_providers": [...],
  "selected_llm": "ollama",
  "selected_model": "llama3.2:latest"
}
```

Server paths are auto-configured by the setup wizard. To add a new MCP server, edit the `MCP_SERVERS` list in `app.py`.

## Building the Desktop App

### Clean Build (when changes don't appear)

If `npm run tauri build` doesn't reflect recent changes, clean the build artifacts:

```bash
# From the project root
rm -rf src-tauri/target dist build
npm run tauri build
```

Or with cargo:
```bash
cd src-tauri && cargo clean && cd .. && npm run tauri build
```

### Standard Build

```bash
# From the project root
cd src-tauri
cargo tauri build
```

The `Cargo.toml` is configured for minimal binary size:

```toml
[profile.release]
strip = true
lto = true
codegen-units = 1
opt-level = "z"
panic = "abort"
```

### macOS DMG Compression

After building, optionally recompress the DMG with bzip2:

```bash
hdiutil convert target/release/bundle/dmg/DEVAN*.dmg -format UDRW -o /tmp/devan-rw.dmg
hdiutil convert /tmp/devan-rw.dmg -format UDBZ -o DEVAN-Agent-compressed.dmg
rm /tmp/devan-rw.dmg
```

## Security Notes

- Designed for **local development only** — do not expose to the internet without authentication
- Change `SECRET_KEY` in production
- Project files in `client/projects/` are excluded from Git via `.gitignore`

## License

Same as parent project
