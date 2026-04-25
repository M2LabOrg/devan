# MCP Design & Deploy

A framework for designing, developing, and deploying MCP (Model Context Protocol) servers with a web-based client UI.

## Project Structure

```
servers/           Production MCP servers (each with mcp_project/ subdirectory)
  excel-retriever/ Intelligent Excel file analysis (demo/standalone)
  excel-pipeline/  Robust Excel extraction, modelling, validation & export
  pdf-extractor/   PDF extraction for LLM/RAG pipelines
  prompt-engineering/ Prompt templates and PDF summarisation
  guardrail/       LLM output safety validation
  webdesign/       React website generation
client/            DEVAN Agent web UI (Flask + Socket.IO)
misc/              Demos, learning notebooks, scratch work
docs/              Project documentation
```

## Running MCP Servers

Each server lives in `servers/<name>/mcp_project/` and runs via:

```bash
cd servers/<name>/mcp_project
uv sync
uv run <server_name>.py
```

## Running the Client UI

```bash
cd client
./start.sh
# Opens at http://localhost:5001
```

## Conventions

- MCP servers use FastMCP (mcp >= 1.26.0)
- Python 3.10+ required
- Package manager: `uv`
- Each server has its own `pyproject.toml` and `uv.lock` in `mcp_project/`
- Design system: "Zen Design System" (Japanese minimalist)
- Server paths in `client/config.json` use absolute paths
