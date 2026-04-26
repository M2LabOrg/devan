# Next Session — DEVAN Continuation Prompt

## What was just shipped (commit 04a863e)

- **Knowledge Base indexing UI** (`client/templates/index.html`):
  - "Knowledge Base" chip in Quick Actions opens a modal with folder picker + progress bar
  - Socket.IO events `index_progress` / `index_complete` drive the live progress
  - On completion, the chip turns green and `set_index_session` activates the KB for chat

- **Indexing pipeline** (`client/app.py`):
  - `indexer_mcp` registered in `MCP_SERVERS`
  - `/api/index/start` POST — walks folder, connects to `document_mcp` + `indexer_mcp`
    via the existing `_collect_mcp_tools` pattern, chunks each file type, indexes chunks
  - `index_sessions` dict (sid → session_id) + system-prompt injection so the LLM
    automatically uses the `query` tool with citations when a KB is active
  - Fixed pre-existing `SyntaxError` in `_generate_vscode_script` (Python 3.12+)

- **`systems/devan/adapter.py`** — `DevanAdapter(index_folder, query, list_files)`:
  connects directly to MCP servers over stdio, no Flask dependency

- **`run_benchmark.py`** + **`benchmark_sample.jsonl`** — CLI benchmark runner:
  ```
  python run_benchmark.py --folder /path/to/docs --questions benchmark_sample.jsonl
  ```
  Outputs `benchmark_results.json` with citation_present, has_answer, avg_latency_ms.

## What to tackle next

### 1. Smoke-test the end-to-end flow
- Enable the Document Indexer MCP in the UI settings (it may default to disabled)
- Pick a small folder (3–5 PDFs or CSVs), click Knowledge Base → Index Folder
- Confirm progress events fire and the chip goes green
- Ask a question in chat — verify the `query` tool is called and citations appear

### 2. Citation rendering in chat (UI polish)
The indexer's `query` tool returns `[N]` citation markers in the answer text.
The current chat renderer (Marked.js) renders them as plain text.
Add a post-processing step in the `chat_response` handler in `index.html`:
- Parse `[N]` markers and link them to a "Sources" footer below the message
- Show `file_name`, `source_ref`, and excerpt for each citation
- Look at `tools_used` in the `chat_response` event to detect when the indexer was called

### 3. Benchmark with a real corpus
- Replace `benchmark_sample.jsonl` with domain-specific Q&A pairs for the paper
- Run `python run_benchmark.py --folder <corpus> --questions <your_qna>.jsonl`
- The output JSON has per-question breakdown and aggregate metrics ready for tables

### 4. Indexer MCP `pyproject.toml` — check uv sync
`servers/indexer/mcp_project/pyproject.toml` exists but was not verified.
Run `cd servers/indexer/mcp_project && uv sync` before first use to ensure
the venv is populated (especially `anthropic` for synthesis).

### 5. Session persistence (optional, for monetisation)
Currently `index_sessions` is in-memory (lost on Flask restart).
Consider persisting active session_id to `client/config.json` so re-opening
the app reconnects to the last KB session without re-indexing.

## Architecture reminder

```
Tauri shell (Rust, src-tauri/)
  └─ spawns Flask (client/app.py, port 5001+)
       ├─ serves index.html (Jinja2 + Socket.IO)
       ├─ MCP servers via stdio (uv --directory <path> run <script>)
       │    ├─ document_mcp  → chunk_pdf_for_rag, chunk_csv_for_rag, ...
       │    ├─ indexer_mcp   → create_session, index_chunks, query
       │    └─ (others: prompt, guardrail, webdesign, webscraper, ...)
       └─ index_sessions: Dict[sid, session_id] → injected into LLM system prompt

systems/devan/adapter.py  → DevanAdapter (bypasses Flask, direct MCP stdio)
run_benchmark.py          → uses DevanAdapter for end-to-end eval
```

## Key file locations

| File | Role |
|------|------|
| `client/app.py` | Flask backend — all routes, agentic loop, indexing pipeline |
| `client/templates/index.html` | Chat UI — Zen design system, Socket.IO client |
| `servers/indexer/mcp_project/indexer_server.py` | SQLite FTS5 RAG index |
| `servers/document/mcp_project/document_server.py` | Document extraction + chunking |
| `systems/devan/adapter.py` | Programmatic RAG adapter |
| `run_benchmark.py` | CLI benchmark runner |
| `benchmark_sample.jsonl` | Replace with domain Q&A for paper |
