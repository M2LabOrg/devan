# Next Session — DEVAN Continuation Prompt

## What was just shipped (this session)

- **`_validate_path` fix** (`document_server.py`) — added `/host/home` and `/host/volumes` as
  allowed Docker mount roots; was blocking all user files → 0 chunks in KB indexing
- **PermissionError fix** (`_index_folder_async` + `index_start` in `app.py`) — file scanner
  now skips macOS `._*` resource forks with try/except
- **License fix** — removed AGPL v3 `pymupdf` / `pymupdf4llm` from `client/requirements.txt`
  and rewrote `_extract_pdf()` + VS Code script template to use `pypdf` (BSD 3-Clause).
  `docling` (MIT) remains as optional OCR dep in the document MCP server.
- **`client/requirements.txt`** — added `pypdf>=4.0.0`, `openpyxl>=3.1.0`
- **KB modal UX** — spinner now stops (solid green) on completion; modal auto-closes after 1.5 s
- **Better error logging** — `process_chat_message` now unwraps Python 3.11 `ExceptionGroup`
  (TaskGroup errors from MCP) so the real inner exception is visible in `docker logs`
- **`NEXT_SESSION.md`** — documented KB vs Batch Processing distinction (they are different)

### ✅ Smoke test PASSED (Week 7–8 milestone)

End-to-end KB flow confirmed working:
- Indexed `/host/home/Documents/devan-test` → **10 files, 21 chunks**
- Asked "What does the contract summary say?" → model answered correctly from indexed docs
- Both Document MCP and Document Indexer MCP are active and healthy

### KB vs Batch Processing — they are DIFFERENT features

| Feature | Route | Purpose | Output |
|---------|-------|---------|--------|
| **Knowledge Base (KB)** | `/api/index/start` | Chunk docs → SQLite FTS5 RAG index for cited chat answers | In-memory index (queried at chat time) |
| **Batch Folder Processing** | `/api/batch_process` | Extract all docs to structured JSON (one JSON per file) | JSON files in `<source>_processed/` or project folder |

- KB indexing uses the MCP servers (`document_mcp` → `indexer_mcp`) via stdio subprocesses.
- Batch Processing calls `_extract_file()` directly in Flask using `pypdf` / `openpyxl`.
- KB is for RAG chat. Batch is for offline document extraction.

### Earlier sessions (commits 04a863e → bb5f9b5)

- **Benchmark corpus** — 120 synthetic files (T1/T2/T3) + 27 domain Q&A pairs
- **Knowledge Base indexing UI** — folder picker, progress bar, chip turns green
- **Indexing pipeline** — `/api/index/start`, `index_sessions`, system-prompt injection
- **`systems/devan/adapter.py`** — `DevanAdapter` (direct MCP stdio, no Flask)
- **Citation rendering** — `[N]` markers + Sources footer in chat
- **Settings modal** + **KB button** in top bar

---

## Important operational note

The app runs via Docker:

```bash
cd /Volumes/LaCie/CODE/devan
make build      # only needed after code changes
make start      # docker compose up -d → http://localhost:5001
```

**Code changes always require `make build && make stop && make start`** — the app code is
baked into the Docker image, not volume-mounted.

Host paths inside the container:
- `~/Documents/foo` → `/host/home/Documents/foo`
- `/Volumes/LaCie/foo` → `/host/volumes/LaCie/foo`

---

## What to tackle next

### 1. Verify citation markers appear (quick — 5 min)

The smoke test confirmed the model answers from indexed docs, but citation `[N]` markers
were not verified in the screenshot. Open http://localhost:5001, re-index
`/host/home/Documents/devan-test`, ask a question, and scroll to the bottom of the answer
to confirm a **Sources** footer with `[1] filename.pdf` etc. appears.

If citations are missing, check `_agentic_loop` in `client/app.py` around line 1390 —
the `query` MCP tool result must populate `kb_citations` and that list must be non-empty.

### 2. Run the paper benchmark

With `make start` running and the benchmark data in place:

```bash
# Generate data first (one-time, run from mcp-design-deploy repo):
bash /Volumes/LaCie/CODE/devan/benchmark/setup.sh

# Run benchmark (from devan repo root):
python run_benchmark.py \
  --folder benchmark/data \
  --questions benchmark/questions.jsonl \
  --out benchmark/results.json
```

Expected output: `benchmark/results.json` with `citation_present`, `has_answer`, `avg_latency_ms`.

### 3. Capture T1–T3 results for the paper (§4)

Once results.json exists, split by `tier` field and report:

| Tier | Questions | citation_present | has_answer | avg_latency_ms |
|------|-----------|-----------------|------------|----------------|
| T1   | 9         | ?               | ?          | ?              |
| T2   | 9         | ?               | ?          | ?              |
| T3   | 9         | ?               | ?          | ?              |

### 4. Implement baseline adapters (paper §4 comparison)

The paper benchmark harness (`mcp-design-deploy/paper/benchmark/`) needs:
- `systems/langchain/adapter.py` — currently raises NotImplementedError
- `systems/crewai/adapter.py` — currently raises NotImplementedError
- `systems/monolithic/adapter.py` — partially implemented

Each must expose `run(task_id, instance) → {output, latency_s, error}`.

### 5. Replace Docker file access with native Flask process (Option C)

**Problem:** The Docker home-directory mount (`~/:/host/home:ro`) is a workaround.
Real users can't translate paths or be limited to their home folder.
The Tauri shell (`src-tauri/`) was designed to spawn Flask natively on the host,
giving it direct access to any local path with no mounting needed.

**What to do:**
- Wire `src-tauri/` to spawn `python client/app.py` as a child process on app launch
- Remove Docker dependency for the Flask layer (keep Docker only for Ollama)
- Update `docker-compose.yml` to run Ollama only, not the `app` service
- Update `Makefile` with a `make dev` target that runs Flask natively

### 6. Session persistence (optional quality-of-life)

`index_sessions` is in-memory — lost on Flask restart.
Persist active `session_id` to `client/config.json` so the app reconnects to the last KB
without re-indexing after `make start`.

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
| `client/requirements.txt` | Flask dependencies (pypdf, openpyxl, mcp, etc.) |
| `servers/indexer/mcp_project/indexer_server.py` | SQLite FTS5 RAG index |
| `servers/document/mcp_project/document_server.py` | Document extraction + chunking |
| `servers/document/mcp_project/pyproject.toml` | docling is optional dep (avoids torch in Docker) |
| `systems/devan/adapter.py` | Programmatic RAG adapter (complete) |
| `benchmark/questions.jsonl` | 27 T1/T2/T3 domain Q&A pairs (full set) |
| `benchmark_sample.jsonl` | 17 T1/T2/T3 domain Q&A pairs (curated subset) |
| `benchmark/setup.sh` | Generate benchmark/data/ locally |
| `run_benchmark.py` | CLI benchmark runner |

## MVP timeline status (from `plan/mvp.md`)

| Week | Work | Status |
|------|------|--------|
| 1–2 | CSV + TXT support in `document` server | ✅ |
| 3–4 | Build `indexer` MCP server | ✅ |
| 5–6 | Wire `indexer` into UI; citation rendering | ✅ |
| 7–8 | Synthetic corpus + Q&A pairs; smoke test KB end-to-end | ✅ |
| 9–10 | Run benchmark; polish; CONTRIBUTING.md; install docs | ⬜ |
| 11–12 | Write paper; submit to arXiv | ⬜ |
