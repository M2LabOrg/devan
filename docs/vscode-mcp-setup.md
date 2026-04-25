# VS Code MCP Setup Guide

Connect the project's MCP servers to GitHub Copilot in VS Code so you can call them directly from Copilot Chat in Agent mode — no separate client required.

---

## Prerequisites

| Requirement | Minimum version |
|---|---|
| VS Code | 1.99+ |
| GitHub Copilot extension | Latest (Agent mode must be enabled) |
| `uv` package manager | Any recent version |

**Check your VS Code version:** `Help → About`. Update if needed — MCP support was introduced in 1.99.

**Check `uv` is on your PATH:**

```bash
uv --version
```

If `uv` is not installed, follow the [official install instructions](https://docs.astral.sh/uv/getting-started/installation/).

---

## Quick Setup: Auto-generate via DEVAN Agent

The fastest way is to use the **VS Code** button in the DEVAN Agent UI:

1. Start the client app:
   ```bash
   cd /path/to/mcp-design-deploy/client
   ./start.sh
   ```
2. Open the app at `http://localhost:5001`.
3. Click the **VS Code** button in the top-right status bar.
4. The app writes `.vscode/mcp.json` to the project root with correct absolute paths for your machine.
5. Reopen VS Code in the project folder — Copilot will detect the config automatically.

---

## Manual Setup

If you prefer to configure things by hand, create `.vscode/mcp.json` in the project root. VS Code 1.99+ reads this file automatically when the workspace is open.

Create the file at:
```
mcp-design-deploy/.vscode/mcp.json
```

**Full configuration for all five servers:**

```json
{
  "servers": {
    "excel-retriever": {
      "type": "stdio",
      "command": "uv",
      "args": ["run", "excel_server.py"],
      "cwd": "${workspaceFolder}/servers/excel-retriever/mcp_project"
    },
    "pdf-extractor": {
      "type": "stdio",
      "command": "uv",
      "args": ["run", "pdf_extractor_server.py"],
      "cwd": "${workspaceFolder}/servers/pdf-extractor/mcp_project"
    },
    "prompt-engineering": {
      "type": "stdio",
      "command": "uv",
      "args": ["run", "prompt_server.py"],
      "cwd": "${workspaceFolder}/servers/prompt-engineering/mcp_project"
    },
    "guardrail": {
      "type": "stdio",
      "command": "uv",
      "args": ["run", "guardrail_server.py"],
      "cwd": "${workspaceFolder}/servers/guardrail/mcp_project"
    },
    "webdesign": {
      "type": "stdio",
      "command": "uv",
      "args": ["run", "webdesign_server.py"],
      "cwd": "${workspaceFolder}/servers/webdesign/mcp_project"
    }
  }
}
```

`${workspaceFolder}` is a VS Code built-in variable that resolves to the workspace root — no hardcoded paths needed.

**Note:** The first time each server runs, `uv` will create a virtual environment and install dependencies automatically (from the server's `pyproject.toml`). This takes a few seconds on first use only.

---

## Using MCP Tools in Copilot Chat

1. Open the Copilot Chat panel (`Ctrl+Alt+I` / `Cmd+Alt+I`, or via the sidebar icon).
2. Switch to **Agent mode** using the mode selector at the top of the chat panel.
3. The MCP tools appear automatically — no further action required. You can confirm they loaded by clicking the tools icon (the wrench/sparkle icon) in the chat input bar.

**Example prompts:**

```
Extract the text and tables from @pdf-extractor /path/to/report.pdf

Analyse the data in @excel-retriever /path/to/budget.xlsx and summarise the key trends

Check this response for safety issues using @guardrail: <paste LLM output here>

Generate a React landing page for a SaaS product using @webdesign

Apply the engineering report template from @prompt-engineering to this document
```

---

## Server Reference

| Server | Use it for |
|---|---|
| **pdf-extractor** | Extracting text, tables, and metadata from PDF files for analysis or RAG pipelines |
| **excel-retriever** | Analysing Excel workbooks — multi-sheet data, formulas, merged cells |
| **prompt-engineering** | Applying structured prompt templates; summarising PDFs with predefined formats |
| **guardrail** | Validating LLM output for safety, policy compliance, and secret leakage |
| **webdesign** | Generating React component code and website prototypes |

---

## Troubleshooting

### `uv` not found

VS Code launches the server using your system `PATH`. If `uv` was installed to a non-standard location (e.g., `~/.cargo/bin` or `~/.local/bin`), VS Code may not find it.

**Fix:** Add an explicit `env` block to the server config:

```json
"excel-retriever": {
  "type": "stdio",
  "command": "uv",
  "args": ["run", "excel_server.py"],
  "cwd": "${workspaceFolder}/servers/excel-retriever/mcp_project",
  "env": {
    "PATH": "/Users/yourname/.local/bin:/usr/local/bin:/usr/bin:/bin"
  }
}
```

Alternatively, use the full path to `uv`:

```json
"command": "/Users/yourname/.local/bin/uv"
```

Find the path with `which uv`.

---

### Server won't start / tools not showing

1. Open the **Output** panel in VS Code (`View → Output`) and select **GitHub Copilot MCP** from the dropdown. Error messages from server startup appear here.
2. Verify the server runs standalone before expecting Copilot to use it:
   ```bash
   cd servers/pdf-extractor/mcp_project
   uv run pdf_extractor_server.py
   ```
   It should print startup output and wait. Press `Ctrl+C` to stop.
3. Check that `pyproject.toml` exists in the `mcp_project/` directory — `uv run` requires it.

---

### Tools show but calls fail

- Make sure any file paths you pass to a tool are **absolute paths** — relative paths are resolved from the server's working directory, which may not be what you expect.
- Some servers (e.g., excel-retriever) require the target file to be accessible from the machine running VS Code. Network paths may cause issues.

---

## Data Privacy

The MCP servers run **entirely on your local machine** as child processes of VS Code. They do not make outbound network requests on their own.

The only point where data leaves your machine is when Copilot Chat sends your message (and any tool results) to GitHub's servers to generate a response — the same as any normal Copilot interaction. If you include sensitive file content in a prompt or a tool call returns sensitive data, that content is subject to standard GitHub Copilot privacy terms.

For fully air-gapped operation, use the DEVAN Agent client with a locally-hosted LLM instead.
