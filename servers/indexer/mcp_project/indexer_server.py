"""
Indexer MCP Server

SQLite-backed chunk store with citation-aware Q&A.
Stores extracted chunks from any file type and answers grounded questions
with citations to the source file and page/sheet.

Run:
    cd servers/indexer/mcp_project
    uv sync
    uv run indexer_server.py

Environment variables:
    INDEXER_DB        Path to SQLite database (default: indexer.db)
    SYNTHESIS_MODEL   Claude model for answer synthesis (default: claude-sonnet-4-6)
    INDEXER_TOP_K     Default chunks to retrieve per query (default: 8)
    ANTHROPIC_API_KEY Required for answer synthesis (optional — raw chunks returned otherwise)
"""

from __future__ import annotations

import json
import os
import re
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from mcp.server.fastmcp import FastMCP, Context

# ---------------------------------------------------------------------------
# Optional: Anthropic for answer synthesis
# ---------------------------------------------------------------------------

try:
    import anthropic as _anthropic_module

    _anthropic_client = _anthropic_module.Anthropic()
    ANTHROPIC_AVAILABLE = True
except Exception:
    _anthropic_client = None
    ANTHROPIC_AVAILABLE = False

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

DB_PATH = os.environ.get("INDEXER_DB", "indexer.db")
SYNTHESIS_MODEL = os.environ.get("SYNTHESIS_MODEL", "claude-sonnet-4-6")
TOP_K_DEFAULT = int(os.environ.get("INDEXER_TOP_K", "8"))

mcp = FastMCP("indexer")

# ---------------------------------------------------------------------------
# Database initialisation
# ---------------------------------------------------------------------------

_EXT_MAP = {
    "xlsx": "excel", "xls": "excel", "xlsm": "excel",
    "pdf": "pdf",
    "docx": "word", "doc": "word",
    "csv": "csv",
    "txt": "text", "md": "text",
}


def _get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def _init_db() -> None:
    with _get_conn() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS sessions (
                session_id  TEXT PRIMARY KEY,
                created_at  TEXT NOT NULL,
                metadata    TEXT DEFAULT '{}'
            );

            CREATE TABLE IF NOT EXISTS chunks (
                chunk_id    TEXT PRIMARY KEY,
                session_id  TEXT NOT NULL,
                file_path   TEXT NOT NULL,
                file_name   TEXT NOT NULL,
                file_type   TEXT NOT NULL,
                source_ref  TEXT NOT NULL,
                content     TEXT NOT NULL,
                metadata    TEXT DEFAULT '{}',
                created_at  TEXT NOT NULL,
                FOREIGN KEY (session_id) REFERENCES sessions(session_id)
            );

            CREATE INDEX IF NOT EXISTS idx_chunks_session
                ON chunks(session_id);

            CREATE INDEX IF NOT EXISTS idx_chunks_file
                ON chunks(session_id, file_path);

            CREATE VIRTUAL TABLE IF NOT EXISTS chunks_fts USING fts5(
                chunk_id    UNINDEXED,
                session_id  UNINDEXED,
                content,
                tokenize    = 'porter unicode61'
            );
        """)


_init_db()

# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _ok(data: dict[str, Any]) -> str:
    return json.dumps({"status": "ok", **data}, indent=2, ensure_ascii=False)


def _err(msg: str) -> str:
    return json.dumps({"status": "error", "message": msg}, indent=2)


def _file_type(file_path: str) -> str:
    ext = Path(file_path).suffix.lower().lstrip(".")
    return _EXT_MAP.get(ext, ext or "unknown")


def _fts_query(question: str) -> str:
    """Convert a natural-language question to an FTS5-safe query string."""
    tokens = re.sub(r"[^\w\s]", " ", question).split()
    meaningful = [t for t in tokens if len(t) >= 3]
    if not meaningful:
        return re.sub(r"[^\w\s]", " ", question).strip() or "a"
    return " OR ".join(meaningful)


# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------


@mcp.tool()
def create_session(
    session_id: str = "",
    metadata: str = "{}",
) -> str:
    """Create a new indexer session (or reset an existing one).

    A session is a named workspace for a set of indexed files.
    All chunks and Q&A are scoped to a session.

    Args:
        session_id: Optional identifier. A UUID is auto-generated if omitted.
        metadata: Optional JSON object (e.g. {"project": "Q2 Review"}).

    Returns:
        JSON with session_id and created_at.
    """
    sid = session_id.strip() or str(uuid.uuid4())
    try:
        meta = json.loads(metadata)
    except json.JSONDecodeError:
        meta = {}

    with _get_conn() as conn:
        conn.execute(
            "INSERT OR REPLACE INTO sessions VALUES (?, ?, ?)",
            (sid, _now(), json.dumps(meta)),
        )

    return _ok({"session_id": sid})


@mcp.tool()
def index_chunks(
    session_id: str,
    file_path: str,
    chunks: list[dict],
) -> str:
    """Store extracted chunks from a document into the session index.

    Call this after extracting content from a file with the document server.
    Each chunk should contain the text and a source reference so that answers
    can be cited back to the exact page or sheet.

    Args:
        session_id: Target session (must exist — call create_session first).
        file_path: Path to the source file (used in citations).
        chunks: List of chunk dicts. Each must have:
            - content  (str): Extracted text.
            - source_ref (str): Location label, e.g. "page 3" or "Sheet: KPIs".
            Optional fields:
            - chunk_id (str): Custom ID; auto-generated UUID if omitted.
            - metadata (dict): Any extra key-value pairs to store.

    Returns:
        JSON with indexed chunk count and list of chunk_ids.
    """
    with _get_conn() as conn:
        row = conn.execute(
            "SELECT session_id FROM sessions WHERE session_id = ?", (session_id,)
        ).fetchone()
        if not row:
            return _err(
                f"Session '{session_id}' not found. Call create_session first."
            )

    file_name = Path(file_path).name
    ftype = _file_type(file_path)
    now = _now()
    ids: list[str] = []
    skipped = 0

    with _get_conn() as conn:
        for chunk in chunks:
            content = str(chunk.get("content", "")).strip()
            if not content:
                skipped += 1
                continue

            source_ref = str(chunk.get("source_ref", ""))
            cid = str(chunk.get("chunk_id", "")).strip() or str(uuid.uuid4())
            meta = chunk.get("metadata", {})
            if not isinstance(meta, dict):
                meta = {}

            conn.execute(
                """INSERT OR REPLACE INTO chunks
                   (chunk_id, session_id, file_path, file_name, file_type,
                    source_ref, content, metadata, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    cid, session_id, file_path, file_name, ftype,
                    source_ref, content, json.dumps(meta), now,
                ),
            )
            conn.execute(
                "INSERT INTO chunks_fts(chunk_id, session_id, content) VALUES (?, ?, ?)",
                (cid, session_id, content),
            )
            ids.append(cid)

    return _ok({
        "indexed": len(ids),
        "skipped_empty": skipped,
        "file_path": file_path,
        "file_name": file_name,
        "file_type": ftype,
        "chunk_ids": ids,
    })


@mcp.tool()
def query(
    session_id: str,
    question: str,
    top_k: int = TOP_K_DEFAULT,
    synthesize: bool = True,
) -> str:
    """Answer a question grounded in the indexed chunks, with citations.

    Searches the session index using full-text search (SQLite FTS5) and
    returns the relevant chunks. If ANTHROPIC_API_KEY is set and synthesize
    is True, a natural-language answer is generated with [N] citations.

    Args:
        session_id: The session to query.
        question: Natural-language question.
        top_k: Maximum number of chunks to retrieve (default 8).
        synthesize: Generate a synthesized answer via Claude (requires API key).

    Returns:
        JSON with:
          - answer      Synthesized text with [N] citations (or "" if synthesis off).
          - citations   List of {file_name, file_path, source_ref, excerpt}.
          - chunks_used Number of chunks fed to the synthesizer.
          - session_id  Echo of the queried session.
    """
    fts_q = _fts_query(question)

    with _get_conn() as conn:
        rows = conn.execute(
            """
            SELECT c.chunk_id, c.file_path, c.file_name, c.file_type,
                   c.source_ref, c.content, c.metadata, fts.rank
            FROM chunks_fts fts
            JOIN chunks c ON fts.chunk_id = c.chunk_id
            WHERE fts.session_id = ?
              AND chunks_fts MATCH ?
            ORDER BY fts.rank
            LIMIT ?
            """,
            (session_id, fts_q, top_k),
        ).fetchall()

    # Fallback: return most-recent chunks when FTS finds nothing
    if not rows:
        with _get_conn() as conn:
            rows = conn.execute(
                """SELECT chunk_id, file_path, file_name, file_type,
                          source_ref, content, metadata, 0 AS rank
                   FROM chunks WHERE session_id = ?
                   ORDER BY created_at DESC LIMIT ?""",
                (session_id, top_k),
            ).fetchall()

    chunks_data = [
        {
            "chunk_id": r["chunk_id"],
            "file_path": r["file_path"],
            "file_name": r["file_name"],
            "file_type": r["file_type"],
            "source_ref": r["source_ref"],
            "content": r["content"],
            "metadata": json.loads(r["metadata"] or "{}"),
        }
        for r in rows
    ]

    citations = [
        {
            "file_name": c["file_name"],
            "file_path": c["file_path"],
            "source_ref": c["source_ref"],
            "excerpt": c["content"][:400],
        }
        for c in chunks_data
    ]

    answer = ""
    if synthesize and ANTHROPIC_AVAILABLE and chunks_data:
        blocks = []
        for i, c in enumerate(chunks_data, 1):
            blocks.append(
                f"[{i}] {c['file_name']} — {c['source_ref']}\n{c['content']}"
            )
        context = "\n\n---\n\n".join(blocks)

        prompt = (
            "You are a precise document analyst. Answer the question below using ONLY "
            "the provided document excerpts. Cite sources using [N] notation matching "
            "the excerpt numbers. If the answer is not present in the excerpts, say so "
            "explicitly — do not hallucinate.\n\n"
            f"Question: {question}\n\n"
            f"Document excerpts:\n\n{context}"
        )

        try:
            resp = _anthropic_client.messages.create(
                model=SYNTHESIS_MODEL,
                max_tokens=1024,
                messages=[{"role": "user", "content": prompt}],
            )
            answer = resp.content[0].text
        except Exception as exc:
            answer = f"[Synthesis error: {exc}]"

    return _ok({
        "answer": answer,
        "citations": citations,
        "chunks_used": len(chunks_data),
        "session_id": session_id,
    })


@mcp.tool()
def list_indexed_files(session_id: str) -> str:
    """List all files indexed in a session with chunk counts.

    Args:
        session_id: The session to inspect.

    Returns:
        JSON with list of files, their chunk counts, and file types.
    """
    with _get_conn() as conn:
        rows = conn.execute(
            """SELECT file_path, file_name, file_type,
                      COUNT(*) AS chunk_count,
                      MIN(created_at) AS first_indexed
               FROM chunks
               WHERE session_id = ?
               GROUP BY file_path
               ORDER BY first_indexed""",
            (session_id,),
        ).fetchall()

    files = [
        {
            "file_path": r["file_path"],
            "file_name": r["file_name"],
            "file_type": r["file_type"],
            "chunk_count": r["chunk_count"],
            "first_indexed": r["first_indexed"],
        }
        for r in rows
    ]

    return _ok({
        "session_id": session_id,
        "files": files,
        "total_files": len(files),
        "total_chunks": sum(f["chunk_count"] for f in files),
    })


@mcp.tool()
def get_chunk(session_id: str, chunk_id: str) -> str:
    """Retrieve a specific chunk by ID.

    Args:
        session_id: The session the chunk belongs to.
        chunk_id: The chunk identifier.

    Returns:
        JSON with full chunk content and metadata.
    """
    with _get_conn() as conn:
        row = conn.execute(
            "SELECT * FROM chunks WHERE chunk_id = ? AND session_id = ?",
            (chunk_id, session_id),
        ).fetchone()

    if not row:
        return _err(f"Chunk '{chunk_id}' not found in session '{session_id}'.")

    return _ok({
        "chunk_id": row["chunk_id"],
        "file_path": row["file_path"],
        "file_name": row["file_name"],
        "file_type": row["file_type"],
        "source_ref": row["source_ref"],
        "content": row["content"],
        "metadata": json.loads(row["metadata"] or "{}"),
        "created_at": row["created_at"],
    })


@mcp.tool()
def clear_session(session_id: str) -> str:
    """Delete all chunks for a session and remove the session record.

    Args:
        session_id: The session to clear.

    Returns:
        JSON with count of deleted chunks.
    """
    with _get_conn() as conn:
        result = conn.execute(
            "DELETE FROM chunks WHERE session_id = ?", (session_id,)
        )
        deleted = result.rowcount
        conn.execute(
            "DELETE FROM chunks_fts WHERE session_id = ?", (session_id,)
        )
        conn.execute(
            "DELETE FROM sessions WHERE session_id = ?", (session_id,)
        )

    return _ok({"deleted_chunks": deleted, "session_id": session_id})


@mcp.tool()
def export_chunks(
    session_id: str,
    format: str = "json",
    file_path_filter: str = "",
) -> str:
    """Export all indexed chunks for a session as JSON or CSV.

    Args:
        session_id: The session to export.
        format: Output format — "json" (default) or "csv".
        file_path_filter: Optional substring to filter by file path.

    Returns:
        JSON array or CSV string with all chunks (content + citations metadata).
    """
    with _get_conn() as conn:
        if file_path_filter:
            rows = conn.execute(
                """SELECT * FROM chunks
                   WHERE session_id = ? AND file_path LIKE ?
                   ORDER BY file_path, created_at""",
                (session_id, f"%{file_path_filter}%"),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM chunks WHERE session_id = ? ORDER BY file_path, created_at",
                (session_id,),
            ).fetchall()

    records = [
        {
            "chunk_id": r["chunk_id"],
            "file_path": r["file_path"],
            "file_name": r["file_name"],
            "file_type": r["file_type"],
            "source_ref": r["source_ref"],
            "content": r["content"],
            "metadata": r["metadata"],
            "created_at": r["created_at"],
        }
        for r in rows
    ]

    if format.lower() == "csv":
        import csv
        import io

        buf = io.StringIO()
        if records:
            writer = csv.DictWriter(buf, fieldnames=records[0].keys())
            writer.writeheader()
            writer.writerows(records)
        return buf.getvalue()

    return json.dumps(records, indent=2, ensure_ascii=False)


@mcp.tool()
def list_sessions() -> str:
    """List all active sessions with chunk counts.

    Returns:
        JSON with all sessions ordered by creation time (newest first).
    """
    with _get_conn() as conn:
        rows = conn.execute(
            """SELECT s.session_id, s.created_at, s.metadata,
                      COUNT(c.chunk_id) AS chunk_count
               FROM sessions s
               LEFT JOIN chunks c ON s.session_id = c.session_id
               GROUP BY s.session_id
               ORDER BY s.created_at DESC""",
        ).fetchall()

    sessions = [
        {
            "session_id": r["session_id"],
            "created_at": r["created_at"],
            "metadata": json.loads(r["metadata"] or "{}"),
            "chunk_count": r["chunk_count"],
        }
        for r in rows
    ]

    return _ok({"sessions": sessions, "total": len(sessions)})


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    mcp.run()
