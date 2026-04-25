# Indexer MCP Server

SQLite-backed unified session index for DEVAN. Stores extracted chunks from any file type and answers grounded Q&A questions with citations to the source file and page/sheet.

## What it does

- **Ingests chunks** from any file type (PDF, Excel, Word, CSV, plain text) extracted by the document server
- **Full-text search** across all indexed files in a session (SQLite FTS5 with Porter stemmer)
- **Grounded Q&A** — answers questions using only indexed content, with `[N]` citations to source file + page/sheet
- **Session isolation** — each session is an independent namespace; supports multiple parallel sessions
- **Export** — dump all chunks as JSON or CSV for downstream use

## Tools

| Tool | Description |
|------|-------------|
| `create_session` | Create (or reset) a named session |
| `index_chunks` | Store extracted chunks from a file |
| `query` | Full-text search + optional synthesized answer with citations |
| `list_indexed_files` | List files in a session with chunk counts |
| `get_chunk` | Retrieve a specific chunk by ID |
| `clear_session` | Delete all chunks and remove the session |
| `export_chunks` | Export chunks as JSON or CSV |
| `list_sessions` | List all active sessions |

## Typical workflow

```
1. create_session(session_id="q2-review")
2. [Extract file with document server]
3. index_chunks(session_id="q2-review", file_path="report.pdf", chunks=[...])
4. index_chunks(session_id="q2-review", file_path="kpis.xlsx", chunks=[...])
5. query(session_id="q2-review", question="What is the total revenue for Q2?")
   → { answer: "Based on [1] report.pdf page 3 and [2] kpis.xlsx Sheet: Summary...",
       citations: [...] }
```

## Setup

```bash
cd servers/indexer/mcp_project
uv sync
uv run indexer_server.py
```

With answer synthesis (requires `ANTHROPIC_API_KEY`):

```bash
uv sync --extra synthesis
export ANTHROPIC_API_KEY=sk-ant-...
uv run indexer_server.py
```

## Environment variables

| Variable | Default | Description |
|----------|---------|-------------|
| `INDEXER_DB` | `indexer.db` | SQLite database path |
| `SYNTHESIS_MODEL` | `claude-sonnet-4-6` | Model for answer synthesis |
| `INDEXER_TOP_K` | `8` | Default chunks per query |
| `ANTHROPIC_API_KEY` | — | Required for synthesis |

## Chunk format

When calling `index_chunks`, each chunk in the list should follow:

```json
{
  "content": "The installed capacity is 147.3 MW...",
  "source_ref": "page 3",
  "chunk_id": "optional-custom-id",
  "metadata": {"table_name": "Technical Data", "row_range": "2-15"}
}
```

`source_ref` is what appears in citations. Use:
- `"page N"` for PDFs
- `"Sheet: SheetName"` or `"Sheet: SheetName, rows 2-15"` for Excel
- `"rows N-M"` for CSV
