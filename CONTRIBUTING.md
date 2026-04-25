# Contributing to DEVAN

Thank you for your interest in contributing to DEVAN. This document outlines the process for reporting issues and submitting improvements.

## Getting Started

1. Fork the repository and clone it locally.
2. Follow the quickstart in the README to get the client UI and at least one MCP server running.
3. Create a branch for your change: `git checkout -b feature/your-change`.

## Project Structure

```
servers/           MCP servers (each with an mcp_project/ subdirectory)
client/            DEVAN Agent web UI (Flask + Socket.IO)
hermes/            Hermes persistent-learning agent
src-tauri/         Desktop app wrapper (Tauri)
docs/              Architecture and integration guides
```

Each MCP server is independently runnable. You only need to set up the server(s) relevant to your change.

## Running a Server

```bash
cd servers/<name>/mcp_project
uv sync
uv run <server_name>.py
```

## Running the Client UI

```bash
cd client
cp config.example.json config.json
# Edit config.json: set "path" fields to your local clone, set "enabled": true
./start.sh
# Opens at http://localhost:5001
```

## Making Changes

- **Bug fixes and small improvements** — open a PR directly.
- **New MCP servers or significant features** — open an issue first to discuss the design.
- **Breaking changes** — please flag these clearly in the PR description.

## Code Style

- Python: follow PEP 8; use `uv` for dependency management.
- MCP servers: use [FastMCP](https://github.com/jlowin/fastmcp) (`mcp >= 1.26.0`).
- Commit messages: short imperative summary (`add`, `fix`, `update`), not past tense.

## Licence

By submitting a pull request you agree that your contribution will be licensed under the [Apache 2.0 licence](LICENSE).

## Questions

Open a GitHub Discussion or file an issue — we are happy to help.
