"""
DevanAdapter — programmatic Python interface to the DEVAN RAG pipeline.

Connects directly to the document and indexer MCP servers over stdio,
bypassing the Flask chat layer. Use this for benchmarking, API wrappers,
or any programmatic access to the index-and-query flow.

Usage:
    adapter = DevanAdapter()
    result  = asyncio.run(adapter.index_folder("/path/to/docs"))
    answer  = asyncio.run(adapter.query("What are the key findings?", result.session_id))
    print(answer.answer, answer.citations)
"""

from __future__ import annotations

import asyncio
import json
import os
import re
import time
import uuid
from contextlib import AsyncExitStack
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

PROJECT_ROOT = Path(__file__).parent.parent.parent

SUPPORTED_EXTENSIONS = {
    ".pdf", ".xlsx", ".xls", ".xlsm",
    ".csv", ".txt", ".md",
    ".docx", ".doc",
    ".parquet",
}


# ---------------------------------------------------------------------------
# Result types
# ---------------------------------------------------------------------------

@dataclass
class ChunkResult:
    file_path: str
    chunks_indexed: int
    error: Optional[str] = None


@dataclass
class IndexResult:
    session_id: str
    files_indexed: int
    total_chunks: int
    index_time_ms: float
    errors: list[str] = field(default_factory=list)


@dataclass
class Citation:
    file_name: str
    file_path: str
    source_ref: str
    excerpt: str


@dataclass
class QueryResult:
    answer: str
    citations: list[Citation]
    chunks_used: int
    session_id: str
    latency_ms: float


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _uv_server_params(server_dir: Path, script: str, extra_env: dict) -> StdioServerParameters:
    env = {**os.environ, **extra_env}
    local_bin = os.path.expanduser("~/.local/bin")
    if local_bin not in env.get("PATH", ""):
        env["PATH"] = local_bin + ":" + env.get("PATH", "")
    return StdioServerParameters(
        command=env.get("UV_BIN", "uv"),
        args=["--directory", str(server_dir), "run", script],
        env=env,
    )


def _simple_word_chunks(text: str, chunk_size: int = 512, overlap: int = 50) -> list[dict]:
    words = text.split()
    chunks: list[dict] = []
    step = max(1, chunk_size - overlap)
    for start in range(0, max(1, len(words)), step):
        batch = words[start: start + chunk_size]
        if not batch:
            break
        chunks.append({
            "content": " ".join(batch),
            "source_ref": f"words {start + 1}–{start + len(batch)}",
        })
    return chunks


async def _call_tool(session: ClientSession, tool: str, args: dict) -> dict:
    result = await session.call_tool(tool, args)
    texts = [b.text for b in (result.content or []) if hasattr(b, "text")]
    if not texts:
        return {}
    try:
        return json.loads(texts[0])
    except Exception:
        return {}


async def _extract_chunks(file_path: Path, doc_session: ClientSession) -> list[dict]:
    """Route a file to the correct document-server chunk tool and normalise output."""
    ext = file_path.suffix.lower()
    fp = str(file_path)
    chunks: list[dict] = []

    if ext == ".pdf":
        data = await _call_tool(doc_session, "chunk_pdf_for_rag", {"file_path": fp})
        for c in data.get("chunks", []):
            text = c.get("text", "").strip()
            if text:
                ref = (
                    f"pages {c['page_start']}–{c['page_end']}"
                    if "page_start" in c
                    else f"chunk {c.get('chunk_index', 0) + 1}"
                )
                chunks.append({"content": text, "source_ref": ref})

    elif ext in {".xlsx", ".xls", ".xlsm"}:
        data = await _call_tool(doc_session, "chunk_excel_content", {"file_path": fp})
        for c in data.get("chunks", []):
            text = c.get("text", "").strip()
            if text:
                page = (c.get("metadata") or {}).get("page_number")
                ref = f"page {page}" if page else f"chunk {c.get('chunk_number', 1)}"
                chunks.append({"content": text, "source_ref": ref})

    elif ext == ".csv":
        data = await _call_tool(doc_session, "chunk_csv_for_rag", {"file_path": fp})
        for c in data.get("chunks", []):
            if c.get("content", "").strip():
                chunks.append({"content": c["content"], "source_ref": c.get("source_ref", "")})

    elif ext in {".txt", ".md"}:
        data = await _call_tool(doc_session, "chunk_text_for_rag", {"file_path": fp})
        for c in data.get("chunks", []):
            if c.get("content", "").strip():
                chunks.append({"content": c["content"], "source_ref": c.get("source_ref", "")})

    elif ext in {".docx", ".doc"}:
        data = await _call_tool(doc_session, "word_to_markdown", {"file_path": fp})
        md = data.get("markdown", "").strip()
        if md:
            chunks = _simple_word_chunks(md)

    elif ext == ".parquet":
        data = await _call_tool(doc_session, "read_parquet", {"file_path": fp, "row_limit": 2000})
        content = (data.get("content") or data.get("markdown") or str(data)).strip()
        if content:
            chunks = _simple_word_chunks(content)

    return chunks


# ---------------------------------------------------------------------------
# Public adapter
# ---------------------------------------------------------------------------

class DevanAdapter:
    """End-to-end DEVAN RAG adapter.

    Args:
        db_path: Path for the indexer's SQLite database.
                 Defaults to ``<project_root>/indexer.db``.
        anthropic_api_key: Override ANTHROPIC_API_KEY for answer synthesis.
                           Falls back to the environment variable.
    """

    def __init__(
        self,
        db_path: Optional[str] = None,
        anthropic_api_key: Optional[str] = None,
    ) -> None:
        self._extra_env: dict[str, str] = {}
        if db_path:
            self._extra_env["INDEXER_DB"] = db_path
        if anthropic_api_key:
            self._extra_env["ANTHROPIC_API_KEY"] = anthropic_api_key

    def _doc_params(self) -> StdioServerParameters:
        return _uv_server_params(
            PROJECT_ROOT / "servers" / "document" / "mcp_project",
            "document_server.py",
            self._extra_env,
        )

    def _idx_params(self) -> StdioServerParameters:
        return _uv_server_params(
            PROJECT_ROOT / "servers" / "indexer" / "mcp_project",
            "indexer_server.py",
            self._extra_env,
        )

    # ------------------------------------------------------------------
    # index_folder
    # ------------------------------------------------------------------

    async def index_folder(
        self,
        folder_path: str,
        session_id: Optional[str] = None,
        progress_cb=None,
    ) -> IndexResult:
        """Index all supported documents in *folder_path*.

        Args:
            folder_path: Directory to walk recursively.
            session_id: Optional fixed session ID; auto-generated if omitted.
            progress_cb: Optional async callable ``(file_name, done, total)``
                         called after each file is processed.

        Returns:
            :class:`IndexResult` with session_id and chunk counts.
        """
        sid = session_id or str(uuid.uuid4())
        folder = Path(folder_path).expanduser().resolve()
        files = sorted([
            f for f in folder.rglob("*")
            if f.is_file()
            and f.suffix.lower() in SUPPORTED_EXTENSIONS
            and not f.name.startswith(".")
            and ".venv" not in f.parts
            and "__pycache__" not in f.parts
        ])

        errors: list[str] = []
        total_chunks = 0
        t0 = time.perf_counter()

        async with AsyncExitStack() as stack:
            dr, dw = await stack.enter_async_context(stdio_client(self._doc_params()))
            doc = await stack.enter_async_context(ClientSession(dr, dw))
            await doc.initialize()

            ir, iw = await stack.enter_async_context(stdio_client(self._idx_params()))
            idx = await stack.enter_async_context(ClientSession(ir, iw))
            await idx.initialize()

            await idx.call_tool("create_session", {
                "session_id": sid,
                "metadata": json.dumps({"folder": str(folder)}),
            })

            for i, file_path in enumerate(files):
                try:
                    chunks = await _extract_chunks(file_path, doc)
                    if chunks:
                        result = await _call_tool(idx, "index_chunks", {
                            "session_id": sid,
                            "file_path": str(file_path),
                            "chunks": chunks,
                        })
                        total_chunks += result.get("indexed", 0)
                except Exception as exc:
                    errors.append(f"{file_path.name}: {exc}")

                if progress_cb:
                    await progress_cb(file_path.name, i + 1, len(files))

        elapsed_ms = (time.perf_counter() - t0) * 1000
        return IndexResult(
            session_id=sid,
            files_indexed=len(files) - len(errors),
            total_chunks=total_chunks,
            index_time_ms=round(elapsed_ms, 1),
            errors=errors,
        )

    # ------------------------------------------------------------------
    # query
    # ------------------------------------------------------------------

    async def query(
        self,
        question: str,
        session_id: str,
        top_k: int = 8,
        synthesize: bool = True,
    ) -> QueryResult:
        """Answer *question* from the indexed knowledge base.

        Args:
            question: Natural-language question.
            session_id: Indexer session to query (from :meth:`index_folder`).
            top_k: Maximum chunks to retrieve.
            synthesize: Generate a Claude-synthesised answer (requires
                        ``ANTHROPIC_API_KEY``). When False, returns raw
                        excerpts only.

        Returns:
            :class:`QueryResult` with answer text, citations, and latency.
        """
        t0 = time.perf_counter()

        async with AsyncExitStack() as stack:
            ir, iw = await stack.enter_async_context(stdio_client(self._idx_params()))
            idx = await stack.enter_async_context(ClientSession(ir, iw))
            await idx.initialize()

            data = await _call_tool(idx, "query", {
                "session_id": session_id,
                "question": question,
                "top_k": top_k,
                "synthesize": synthesize,
            })

        latency_ms = (time.perf_counter() - t0) * 1000
        citations = [
            Citation(
                file_name=c["file_name"],
                file_path=c["file_path"],
                source_ref=c["source_ref"],
                excerpt=c["excerpt"],
            )
            for c in data.get("citations", [])
        ]

        return QueryResult(
            answer=data.get("answer", ""),
            citations=citations,
            chunks_used=data.get("chunks_used", 0),
            session_id=session_id,
            latency_ms=round(latency_ms, 1),
        )

    # ------------------------------------------------------------------
    # list_files  (convenience)
    # ------------------------------------------------------------------

    async def list_files(self, session_id: str) -> list[dict]:
        """Return the list of files indexed under *session_id*."""
        async with AsyncExitStack() as stack:
            ir, iw = await stack.enter_async_context(stdio_client(self._idx_params()))
            idx = await stack.enter_async_context(ClientSession(ir, iw))
            await idx.initialize()
            data = await _call_tool(idx, "list_indexed_files", {"session_id": session_id})
        return data.get("files", [])
