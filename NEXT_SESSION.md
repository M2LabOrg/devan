# Next Session — DEVAN Continuation Prompt

## What was just shipped (commits 04a863e → 1927ee4)

- **Knowledge Base indexing UI** — folder picker, progress bar, chip turns green
- **Indexing pipeline** (`client/app.py`) — `/api/index/start`, `index_sessions`, system-prompt injection
- **`systems/devan/adapter.py`** — `DevanAdapter` (direct MCP stdio, no Flask)
- **`run_benchmark.py`** + **`benchmark_sample.jsonl`** — CLI benchmark runner
- **Citation rendering** (this session):
  - `_agentic_loop` extracts `citations[]` from `query` tool JSON and returns them
  - `chat_response` Socket.IO event now includes `citations`
  - `renderCitations()` in `index.html` replaces `[N]` markers with `<sup>` links and appends a **Sources** footer (file name, source ref, 160-char excerpt)
- **Indexer MCP `uv sync`** ran — venv populated at `servers/indexer/mcp_project/.venv`

## Important operational note

The app runs via Docker, **not** as a static file:

```bash
cd /path/to/devan
make start          # docker compose up -d → http://localhost:5001
```

Opening `client/templates/index.html` directly in a browser will not work — Flask is not running, `loadConfig()` fails, and all MCP toggles are empty.

## What to tackle next

### 1. Smoke-test the end-to-end KB flow (highest priority)

```bash
make start          # start Flask + Ollama
# open http://localhost:5001
```

- Enable **Document MCP** and **Document Indexer MCP** in Settings → MCP Servers
- Click **Knowledge Base** → pick a small folder (3–5 PDFs or CSVs)
- Confirm progress events fire and the chip turns green
- Ask a question — verify the `query` tool fires, `[N]` markers appear in the reply, and the Sources footer renders

### 2. Implement `systems/devan/adapter.py` fully (paper benchmark)

`adapter.py` exists as a stub/prototype. For the paper's T1–T3 benchmark it needs:
- `index_folder(folder_path)` — walk folder, chunk every file via `document_mcp`, index via `indexer_mcp`
- `query(question, session_id)` — call `query` tool, return `{answer, citations}`
- `list_files(session_id)` — call `list_files` tool
- Error handling and timeout guard

Reference: `systems/devan/adapter.py`, `run_benchmark.py`.
This unlocks running `python run_benchmark.py --folder <corpus> --questions <qna>.jsonl`.

### 3. Replace `benchmark_sample.jsonl` with domain Q&A pairs

Create 20–30 Q&A pairs grounded in a real document corpus for the paper's T1–T3 tiers:
- **T1** — single-file factual retrieval ("What is the net revenue in Q3 from file X?")
- **T2** — cross-file aggregation ("Sum revenue across all quarterly reports")
- **T3** — inference + citation ("Which region had the highest growth and why?")

Run: `python run_benchmark.py --folder <corpus> --questions <your_qna>.jsonl`

### 4. Implement baseline adapters (paper §4)

Per `paper-plan.md` steps 3–5, the paper needs comparison systems:

| Adapter | File | Status |
|---------|------|--------|
| LangChain | `systems/langchain/adapter.py` | stub |
| CrewAI | `systems/crewai/adapter.py` | stub |
| Monolithic | `systems/monolithic/adapter.py` | stub |

Each adapter must expose the same `index_folder` / `query` interface as the DEVAN adapter so `run_benchmark.py` can swap them in.

### 5. Session persistence (optional quality-of-life)

`index_sessions` is in-memory — lost on Flask restart.
Persist active `session_id` to `client/config.json` so the app reconnects to the last KB without re-indexing.

---

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
| `client/app.py` | Flask backend — routes, agentic loop, indexing pipeline, citation extraction |
| `client/templates/index.html` | Chat UI — citation rendering, Sources footer |
| `servers/indexer/mcp_project/indexer_server.py` | SQLite FTS5 RAG index |
| `servers/document/mcp_project/document_server.py` | Document extraction + chunking |
| `systems/devan/adapter.py` | Programmatic RAG adapter (needs full implementation) |
| `systems/langchain/adapter.py` | LangChain baseline (stub) |
| `systems/crewai/adapter.py` | CrewAI baseline (stub) |
| `systems/monolithic/adapter.py` | Monolithic baseline (stub) |
| `run_benchmark.py` | CLI benchmark runner |
| `benchmark_sample.jsonl` | Replace with domain T1–T3 Q&A pairs |

## MVP timeline status (from `plan/mvp.md`)

| Week | Work | Status |
|------|------|--------|
| 1–2 | CSV + TXT support in `document` server | ✅ |
| 3–4 | Build `indexer` MCP server | ✅ |
| 5–6 | Wire `indexer` into UI; citation rendering | ✅ |
| 7–8 | Benchmark with real corpus; T1–T3 results | ⬜ next |
| 9–10 | Polish, CONTRIBUTING.md, install docs | ⬜ |
| 11–12 | Write paper; submit to arXiv | ⬜ |
