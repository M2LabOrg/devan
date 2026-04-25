"""
PDF Extractor MCP Server — Production-Grade PDF Processing for LLM & RAG Pipelines

Uses Docling (IBM, MIT licence) as the sole extraction engine. No AGPL dependencies.

Designed for:
- Hundreds of PDFs with hundreds of pages each
- Complex layouts with tables, figures, multi-column text
- Output ready for LLM context windows or RAG vector databases
- Configurable chunking strategies for embedding pipelines
"""

import base64
import hashlib
import io
import json
import os
import re
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

from mcp.server.fastmcp import FastMCP, Context
from mcp.types import ImageContent as MCPImageContent, SamplingMessage

# ─── Optional imports ─────────────────────────────────────────────────────────

try:
    from docling.datamodel.base_models import InputFormat
    from docling.datamodel.pipeline_options import PdfPipelineOptions
    from docling.document_converter import DocumentConverter, PdfFormatOption
    DOCLING_AVAILABLE = True
except ImportError:
    DOCLING_AVAILABLE = False

try:
    from pypdf import PdfReader
    PYPDF_AVAILABLE = True
except ImportError:
    PYPDF_AVAILABLE = False

try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False

# ─── Configuration ────────────────────────────────────────────────────────────

PDF_DIR = os.environ.get("PDF_DIR", "../pdf_files")
OUTPUT_DIR = os.environ.get("PDF_OUTPUT_DIR", "../output")

# ─── Initialize MCP Server ───────────────────────────────────────────────────

mcp = FastMCP("pdf-extractor-mcp")


# ─── Security: Path Validation ───────────────────────────────────────────────

_ALLOWED_DIRS: list[str] = [PDF_DIR, OUTPUT_DIR]


def _validate_path(path: str) -> str:
    """Resolve and verify a file path is within the server's allowed directories."""
    resolved = os.path.realpath(os.path.abspath(path))
    for allowed in _ALLOWED_DIRS:
        allowed_resolved = os.path.realpath(os.path.abspath(allowed))
        if resolved.startswith(allowed_resolved + os.sep) or resolved == allowed_resolved:
            return resolved
    raise ValueError(
        f"Access denied: path is outside allowed directories.\n"
        f"  Requested: {resolved}\n"
        f"  Allowed:   {_ALLOWED_DIRS}\n"
        f"Tip: set PDF_DIR / PDF_OUTPUT_DIR env vars to include your target files."
    )


# ─── Data Models ──────────────────────────────────────────────────────────────

@dataclass
class ExtractionResult:
    file_path: str
    file_name: str
    engine: str
    total_pages: int
    total_words: int
    total_tables: int
    total_figures: int
    extraction_time_seconds: float
    content_markdown: str
    pages: List[Dict[str, Any]]
    metadata: Dict[str, Any]


# ─── Engine Singletons ───────────────────────────────────────────────────────

_converter: Optional["DocumentConverter"] = None
_figure_converter: Optional["DocumentConverter"] = None


def _get_converter(with_images: bool = False) -> "DocumentConverter":
    global _converter, _figure_converter
    if with_images:
        if _figure_converter is None:
            opts = PdfPipelineOptions()
            opts.generate_picture_images = True
            _figure_converter = DocumentConverter(
                format_options={InputFormat.PDF: PdfFormatOption(pipeline_options=opts)}
            )
        return _figure_converter
    if _converter is None:
        _converter = DocumentConverter()
    return _converter


# ─── Core Extraction ─────────────────────────────────────────────────────────

def _parse_page_range(page_range: str) -> set:
    """Parse '1-5,8,10-12' into a set of 1-indexed page numbers."""
    pages: set = set()
    for part in page_range.split(","):
        part = part.strip()
        if "-" in part:
            a, b = part.split("-", 1)
            pages.update(range(int(a), int(b) + 1))
        else:
            pages.add(int(part))
    return pages


def _extract_with_docling(file_path: str) -> ExtractionResult:
    conv = _get_converter()
    start = time.time()
    result = conv.convert(file_path)
    doc = result.document

    markdown = doc.export_to_markdown()
    text = doc.export_to_text()

    # Per-page content from markdown page-break markers
    splits = re.split(r"\n---\n|\f", markdown)
    splits = [s.strip() for s in splits if s.strip()]
    pages = []
    for i, txt in enumerate(splits):
        pages.append({
            "page_number": i + 1,
            "content": txt,
            "character_count": len(txt),
            "word_count": len(txt.split()),
        })
    if not pages and markdown.strip():
        pages.append({
            "page_number": 1,
            "content": markdown.strip(),
            "character_count": len(markdown),
            "word_count": len(markdown.split()),
        })

    # Tables with page provenance
    tables = []
    for i, tbl in enumerate(doc.tables):
        entry: Dict[str, Any] = {"index": i}
        try:
            entry["markdown"] = tbl.export_to_markdown()
        except Exception:
            entry["markdown"] = ""
        if tbl.prov:
            entry["page"] = tbl.prov[0].page_no
        if hasattr(tbl, "num_rows"):
            entry["rows"] = tbl.num_rows
        if hasattr(tbl, "num_cols"):
            entry["cols"] = tbl.num_cols
        tables.append(entry)

    # Figures with page provenance
    figures = []
    for i, pic in enumerate(doc.pictures):
        entry = {"index": i}
        if pic.prov:
            entry["page"] = pic.prov[0].page_no
        if hasattr(pic, "caption") and pic.caption:
            entry["caption"] = str(pic.caption)
        figures.append(entry)

    page_count = len(result.pages) if hasattr(result, "pages") else len(pages)
    elapsed = time.time() - start

    return ExtractionResult(
        file_path=file_path,
        file_name=os.path.basename(file_path),
        engine="docling",
        total_pages=page_count,
        total_words=len(text.split()),
        total_tables=len(tables),
        total_figures=len(figures),
        extraction_time_seconds=round(elapsed, 2),
        content_markdown=markdown,
        pages=pages,
        metadata={"tables": tables, "figures": figures},
    )


# ─── Chunking Strategies ─────────────────────────────────────────────────────

def _chunk_by_pages(markdown: str, pages_per_chunk: int = 5) -> List[Dict[str, Any]]:
    splits = re.split(r"\n---\n|\f", markdown)
    splits = [s.strip() for s in splits if s.strip()]
    chunks = []
    for i in range(0, len(splits), pages_per_chunk):
        group = splits[i:i + pages_per_chunk]
        txt = "\n\n".join(group)
        chunks.append({
            "chunk_index": len(chunks),
            "page_start": i + 1,
            "page_end": min(i + pages_per_chunk, len(splits)),
            "text": txt,
            "word_count": len(txt.split()),
            "char_count": len(txt),
        })
    return chunks


def _chunk_by_tokens(text: str, chunk_size: int = 512, overlap: int = 50) -> List[Dict[str, Any]]:
    words = text.split()
    chunks = []
    start = 0
    while start < len(words):
        end = min(start + chunk_size, len(words))
        txt = " ".join(words[start:end])
        chunks.append({
            "chunk_index": len(chunks),
            "word_start": start,
            "word_end": end,
            "text": txt,
            "word_count": end - start,
            "char_count": len(txt),
        })
        start += chunk_size - overlap
    return chunks


def _chunk_by_sections(markdown: str) -> List[Dict[str, Any]]:
    sections = re.split(r"\n(?=#{1,3}\s)", markdown)
    sections = [s.strip() for s in sections if s.strip()]
    chunks = []
    for section in sections:
        lines = section.split("\n")
        heading = lines[0].strip().lstrip("#").strip() if lines else "Untitled"
        chunks.append({
            "chunk_index": len(chunks),
            "heading": heading,
            "text": section,
            "word_count": len(section.split()),
            "char_count": len(section),
        })
    return chunks


def _file_hash(file_path: str) -> str:
    h = hashlib.sha256()
    with open(file_path, "rb") as f:
        for block in iter(lambda: f.read(8192), b""):
            h.update(block)
    return h.hexdigest()[:12]


# ─── MCP Tools ────────────────────────────────────────────────────────────────

@mcp.tool()
def list_pdf_files(directory: Optional[str] = None) -> str:
    """
    List all PDF files in the specified directory with metadata.

    Args:
        directory: Path to directory. Defaults to PDF_DIR env var or '../pdf_files'.

    Returns:
        JSON with file list including size and page count.
    """
    search_dir = directory or PDF_DIR
    if not os.path.exists(search_dir):
        return json.dumps({
            "error": f"Directory not found: {search_dir}",
            "hint": "Create the directory or set PDF_DIR environment variable",
        }, indent=2)

    files = []
    for root, dirs, filenames in os.walk(search_dir):
        dirs.sort()
        for item in sorted(filenames):
            if not item.lower().endswith(".pdf"):
                continue
            fp = os.path.join(root, item)
            rel = os.path.relpath(fp, search_dir)
            try:
                stat = os.stat(fp)
                size_mb = round(stat.st_size / (1024 * 1024), 2)
                page_count = None
                if PYPDF_AVAILABLE:
                    try:
                        page_count = len(PdfReader(fp).pages)
                    except Exception:
                        pass
                files.append({
                    "filename": item,
                    "relative_path": rel,
                    "path": fp,
                    "size_mb": size_mb,
                    "pages": page_count,
                    "hash": _file_hash(fp),
                })
            except OSError as e:
                files.append({"filename": item, "relative_path": rel, "error": str(e)})

    return json.dumps({
        "directory": os.path.abspath(search_dir),
        "file_count": len(files),
        "total_size_mb": round(sum(f.get("size_mb", 0) for f in files), 2),
        "total_pages": sum(f.get("pages", 0) or 0 for f in files),
        "engine": "docling",
        "files": files,
    }, indent=2)


@mcp.tool()
def extract_pdf(
    file_path: str,
    engine: str = "auto",
    page_range: Optional[str] = None,
    use_ai_ocr: bool = False,
) -> str:
    """
    Extract content from a PDF file as clean Markdown with per-page metadata.

    Uses Docling (IBM, MIT licence) for deep layout analysis including tables,
    figures, and complex multi-column layouts. Built-in OCR via Docling.

    Args:
        file_path: Path to the PDF file.
        engine: Kept for API compatibility; Docling is always used.
        page_range: Kept for API compatibility; full document is extracted.
        use_ai_ocr: Kept for API compatibility; Docling handles OCR natively.

    Returns:
        JSON with extracted Markdown, per-page content/metadata, tables, and figures.
    """
    try:
        file_path = _validate_path(file_path)
    except ValueError as e:
        return json.dumps({"error": str(e)}, indent=2)
    if not os.path.exists(file_path):
        return json.dumps({"error": f"File not found: {file_path}"}, indent=2)
    if not DOCLING_AVAILABLE:
        return json.dumps({"error": "Docling not installed. Run: uv add docling"}, indent=2)
    try:
        result = _extract_with_docling(file_path)
        return json.dumps(asdict(result), indent=2)
    except Exception as e:
        return json.dumps({"error": f"Extraction failed: {str(e)}", "file_path": file_path}, indent=2)


@mcp.tool()
def extract_tables(file_path: str, page_range: Optional[str] = None) -> str:
    """
    Extract only tables from a PDF file as Markdown tables.

    Args:
        file_path: Path to the PDF file.
        page_range: Optional page range like '1-5' to filter tables by page.

    Returns:
        JSON with list of tables as Markdown, including page numbers and dimensions.
    """
    try:
        file_path = _validate_path(file_path)
    except ValueError as e:
        return json.dumps({"error": str(e)}, indent=2)
    if not os.path.exists(file_path):
        return json.dumps({"error": f"File not found: {file_path}"}, indent=2)
    if not DOCLING_AVAILABLE:
        return json.dumps({"error": "Docling not installed. Run: uv add docling"}, indent=2)
    try:
        pages_filter = _parse_page_range(page_range) if page_range else None
        conv = _get_converter()
        result = conv.convert(file_path)
        doc = result.document
        page_count = len(result.pages) if hasattr(result, "pages") else 0

        tables = []
        for i, tbl in enumerate(doc.tables):
            page_no = tbl.prov[0].page_no if tbl.prov else None
            if pages_filter and page_no not in pages_filter:
                continue
            entry: Dict[str, Any] = {"table_index": i}
            if page_no is not None:
                entry["page"] = page_no
            try:
                entry["markdown"] = tbl.export_to_markdown()
            except Exception:
                entry["markdown"] = ""
            if hasattr(tbl, "num_rows"):
                entry["rows"] = tbl.num_rows
            if hasattr(tbl, "num_cols"):
                entry["cols"] = tbl.num_cols
            tables.append(entry)

        return json.dumps({
            "file_path": file_path,
            "file_name": os.path.basename(file_path),
            "total_pages": page_count,
            "pages_filter": page_range,
            "tables_found": len(tables),
            "tables": tables,
        }, indent=2)
    except Exception as e:
        return json.dumps({"error": f"Table extraction failed: {str(e)}"}, indent=2)


@mcp.tool()
def extract_figures(file_path: str, page_range: Optional[str] = None) -> str:
    """
    Extract figure/image metadata from a PDF file.

    Args:
        file_path: Path to the PDF file.
        page_range: Optional page range like '1-5' to filter figures by page.

    Returns:
        JSON with list of figures and their metadata (page, caption if available).
    """
    try:
        file_path = _validate_path(file_path)
    except ValueError as e:
        return json.dumps({"error": str(e)}, indent=2)
    if not os.path.exists(file_path):
        return json.dumps({"error": f"File not found: {file_path}"}, indent=2)
    if not DOCLING_AVAILABLE:
        return json.dumps({"error": "Docling not installed. Run: uv add docling"}, indent=2)
    try:
        pages_filter = _parse_page_range(page_range) if page_range else None
        conv = _get_converter()
        result = conv.convert(file_path)
        doc = result.document
        page_count = len(result.pages) if hasattr(result, "pages") else 0

        figures = []
        for i, pic in enumerate(doc.pictures):
            page_no = pic.prov[0].page_no if pic.prov else None
            if pages_filter and page_no not in pages_filter:
                continue
            entry: Dict[str, Any] = {"figure_index": i}
            if page_no is not None:
                entry["page"] = page_no
            if hasattr(pic, "caption") and pic.caption:
                entry["caption"] = str(pic.caption)
            if hasattr(pic, "image") and pic.image and hasattr(pic.image, "size"):
                w, h = pic.image.size
                entry["width_px"] = w
                entry["height_px"] = h
            figures.append(entry)

        return json.dumps({
            "file_path": file_path,
            "file_name": os.path.basename(file_path),
            "total_pages": page_count,
            "pages_filter": page_range,
            "figures_found": len(figures),
            "figures": figures,
        }, indent=2)
    except Exception as e:
        return json.dumps({"error": f"Figure extraction failed: {str(e)}"}, indent=2)


@mcp.tool()
def chunk_pdf_for_rag(
    file_path: str,
    strategy: str = "tokens",
    chunk_size: int = 512,
    overlap: int = 50,
    engine: str = "auto",
    page_range: Optional[str] = None,
) -> str:
    """
    Extract and chunk a PDF into pieces ready for a RAG vector database.

    Args:
        file_path: Path to the PDF file.
        strategy: 'tokens' (word-based), 'pages', or 'sections' (by headings).
        chunk_size: Words per chunk for 'tokens' (default 512). Pages per chunk for 'pages'.
        overlap: Word overlap between chunks for 'tokens' strategy (default 50).
        engine: Kept for API compatibility; Docling is always used.
        page_range: Kept for API compatibility.

    Returns:
        JSON with chunks array, each containing text, metadata, and position info.
    """
    try:
        file_path = _validate_path(file_path)
    except ValueError as e:
        return json.dumps({"error": str(e)}, indent=2)
    if not os.path.exists(file_path):
        return json.dumps({"error": f"File not found: {file_path}"}, indent=2)

    extraction_json = extract_pdf(file_path)
    extraction = json.loads(extraction_json)
    if "error" in extraction:
        return extraction_json

    markdown = extraction.get("content_markdown", "")
    if not markdown:
        return json.dumps({"error": "No content extracted from PDF"}, indent=2)

    if strategy == "tokens":
        chunks = _chunk_by_tokens(markdown, chunk_size=chunk_size, overlap=overlap)
    elif strategy == "pages":
        chunks = _chunk_by_pages(markdown, pages_per_chunk=chunk_size if chunk_size < 50 else 5)
    elif strategy == "sections":
        chunks = _chunk_by_sections(markdown)
    else:
        return json.dumps({
            "error": f"Unknown strategy: {strategy}. Use 'tokens', 'pages', or 'sections'."
        }, indent=2)

    doc_id = _file_hash(file_path)
    for chunk in chunks:
        chunk["doc_id"] = doc_id
        chunk["doc_name"] = os.path.basename(file_path)
        chunk["source"] = file_path

    return json.dumps({
        "file_path": file_path,
        "file_name": os.path.basename(file_path),
        "doc_id": doc_id,
        "engine": extraction.get("engine"),
        "strategy": strategy,
        "total_pages": extraction.get("total_pages"),
        "total_words": extraction.get("total_words"),
        "total_tables": extraction.get("total_tables"),
        "total_figures": extraction.get("total_figures"),
        "chunk_count": len(chunks),
        "chunks": chunks,
    }, indent=2)


@mcp.tool()
def batch_extract(
    directory: Optional[str] = None,
    engine: str = "auto",
    output_format: str = "markdown",
) -> str:
    """
    Batch extract all PDFs in a directory.

    Args:
        directory: Directory containing PDFs. Defaults to PDF_DIR.
        engine: Kept for API compatibility; Docling is always used.
        output_format: 'markdown' or 'json'.

    Returns:
        JSON summary with extraction results per file.
    """
    search_dir = directory or PDF_DIR
    if not os.path.exists(search_dir):
        return json.dumps({"error": f"Directory not found: {search_dir}"}, indent=2)

    pdf_files = []
    for root, dirs, filenames in os.walk(search_dir):
        dirs.sort()
        for f in sorted(filenames):
            if f.lower().endswith(".pdf"):
                pdf_files.append(os.path.join(root, f))
    if not pdf_files:
        return json.dumps({"error": "No PDF files found", "directory": search_dir}, indent=2)

    out_dir = OUTPUT_DIR
    os.makedirs(out_dir, exist_ok=True)
    results = []
    total_start = time.time()

    for fp in pdf_files:
        try:
            extraction_json = extract_pdf(fp)
            extraction = json.loads(extraction_json)
            if "error" in extraction:
                results.append({"file": os.path.basename(fp), "status": "error",
                                 "error": extraction["error"]})
                continue
            base_name = Path(fp).stem
            if output_format == "markdown":
                out_path = os.path.join(out_dir, f"{base_name}.md")
                with open(out_path, "w", encoding="utf-8") as fh:
                    fh.write(extraction.get("content_markdown", ""))
            else:
                out_path = os.path.join(out_dir, f"{base_name}.json")
                with open(out_path, "w", encoding="utf-8") as fh:
                    json.dump(extraction, fh, indent=2)
            results.append({
                "file": os.path.basename(fp),
                "status": "success",
                "engine": extraction.get("engine"),
                "pages": extraction.get("total_pages"),
                "words": extraction.get("total_words"),
                "tables": extraction.get("total_tables"),
                "figures": extraction.get("total_figures"),
                "time_seconds": extraction.get("extraction_time_seconds"),
                "output": out_path,
            })
        except Exception as e:
            results.append({"file": os.path.basename(fp), "status": "error", "error": str(e)})

    total_elapsed = round(time.time() - total_start, 2)
    succeeded = [r for r in results if r["status"] == "success"]
    failed = [r for r in results if r["status"] == "error"]

    return json.dumps({
        "directory": os.path.abspath(search_dir),
        "output_directory": os.path.abspath(out_dir),
        "total_files": len(pdf_files),
        "succeeded": len(succeeded),
        "failed": len(failed),
        "total_pages": sum(r.get("pages", 0) or 0 for r in succeeded),
        "total_words": sum(r.get("words", 0) or 0 for r in succeeded),
        "total_time_seconds": total_elapsed,
        "results": results,
    }, indent=2)


@mcp.tool()
def analyze_pdf_structure(file_path: str) -> str:
    """
    Analyze a PDF's structure: page count, tables, figures, complexity.

    Note: Uses Docling for full conversion — not a lightweight scan.

    Args:
        file_path: Path to the PDF file.

    Returns:
        JSON with structural analysis (page count, table/figure counts, complexity rating).
    """
    try:
        file_path = _validate_path(file_path)
    except ValueError as e:
        return json.dumps({"error": str(e)}, indent=2)
    if not os.path.exists(file_path):
        return json.dumps({"error": f"File not found: {file_path}"}, indent=2)
    if not DOCLING_AVAILABLE:
        return json.dumps({"error": "Docling not installed. Run: uv add docling"}, indent=2)
    try:
        stat = os.stat(file_path)
        result = _extract_with_docling(file_path)
        complexity = (
            "high" if (result.total_tables > 10 or result.total_figures > 20)
            else "medium" if (result.total_tables > 3 or result.total_figures > 5)
            else "low"
        )
        return json.dumps({
            "file_path": file_path,
            "file_name": os.path.basename(file_path),
            "size_mb": round(stat.st_size / (1024 * 1024), 2),
            "total_pages": result.total_pages,
            "total_words": result.total_words,
            "total_tables": result.total_tables,
            "total_figures": result.total_figures,
            "complexity": complexity,
            "engine": "docling",
            "extraction_time_seconds": result.extraction_time_seconds,
        }, indent=2)
    except Exception as e:
        return json.dumps({"error": f"Analysis failed: {str(e)}"}, indent=2)


@mcp.tool()
def get_extraction_status() -> str:
    """
    Get the status of available extraction engines and configuration.

    Returns:
        JSON with engine availability, configuration, and tool list.
    """
    return json.dumps({
        "engine": {
            "docling": {
                "available": DOCLING_AVAILABLE,
                "license": "MIT (IBM)",
                "strengths": (
                    "Deep-learning layout analysis, table/figure extraction, "
                    "built-in OCR, handles complex multi-column layouts"
                ),
                "install": "uv add docling",
            }
        },
        "configuration": {
            "pdf_dir": os.path.abspath(PDF_DIR),
            "output_dir": os.path.abspath(OUTPUT_DIR),
        },
        "tools": [
            "list_pdf_files — Discover PDFs in a directory (recursive)",
            "extract_pdf — Full extraction to Markdown",
            "extract_tables — Extract only tables as Markdown, with optional page filter",
            "extract_figures — Catalogue figures, with optional page filter",
            "describe_figures — AI-powered figure descriptions using Claude vision",
            "chunk_pdf_for_rag — Extract and chunk for vector DB ingestion",
            "batch_extract — Process all PDFs in a directory",
            "analyze_pdf_structure — Page count, table/figure counts, complexity rating",
        ],
        "figure_description": {
            "available": ANTHROPIC_AVAILABLE,
            "model": "claude-haiku-4-5-20251001",
            "note": "Requires ANTHROPIC_API_KEY environment variable",
        },
        "chunking_strategies": [
            "tokens — Word-based chunks with configurable size and overlap (default for RAG)",
            "pages — Split by page boundaries",
            "sections — Split by markdown headings",
        ],
    }, indent=2)


@mcp.tool()
async def describe_figures(
    file_path: str,
    page_range: Optional[str] = None,
    max_figures: int = 10,
    ctx: Context = None,
) -> str:
    """
    Extract figures from a PDF and describe their content using Claude vision AI.

    Prefers MCP sampling (no API key needed on the server) when the client supports it.
    Falls back to a direct Anthropic API call when ANTHROPIC_API_KEY is set.

    Args:
        file_path: Path to the PDF file.
        page_range: Optional page range like '1-5'. Processes all pages if omitted.
        max_figures: Maximum number of figures to describe (default 10, to control cost).

    Returns:
        JSON with list of figures, each with page number and AI description.
    """
    try:
        file_path = _validate_path(file_path)
    except ValueError as e:
        return json.dumps({"error": str(e)}, indent=2)
    if not os.path.exists(file_path):
        return json.dumps({"error": f"File not found: {file_path}"}, indent=2)
    if not DOCLING_AVAILABLE:
        return json.dumps({"error": "Docling not installed. Run: uv add docling"}, indent=2)

    sampling_available = (
        ctx is not None
        and hasattr(ctx, "session")
        and getattr(getattr(ctx.session, "client_params", None), "capabilities", None) is not None
        and getattr(ctx.session.client_params.capabilities, "sampling", None) is not None
    )
    api_key = os.environ.get("ANTHROPIC_API_KEY")

    if not sampling_available and not (ANTHROPIC_AVAILABLE and api_key):
        return json.dumps({
            "error": (
                "No LLM backend available for figure description. "
                "Either connect a client that supports MCP sampling, or set ANTHROPIC_API_KEY."
            ),
            "fallback": "Use extract_figures tool for metadata-only figure listing.",
        }, indent=2)

    describe_prompt = (
        "This image is a figure extracted from a PDF document. "
        "Describe what it shows concisely in 1-3 sentences. "
        "If it is a chart or graph, mention the type, subject, and key values or trends. "
        "If it is a diagram or photo, describe its content briefly."
    )

    try:
        pages_filter = _parse_page_range(page_range) if page_range else None
        conv = _get_converter(with_images=True)
        result = conv.convert(file_path)
        doc = result.document
        page_count = len(result.pages) if hasattr(result, "pages") else 0

        direct_client = (
            anthropic.Anthropic(api_key=api_key)
            if (ANTHROPIC_AVAILABLE and api_key and not sampling_available)
            else None
        )
        described = []
        count = 0
        llm_backend = "sampling" if sampling_available else "anthropic-api"

        for pic in doc.pictures:
            if count >= max_figures:
                break
            page_no = pic.prov[0].page_no if pic.prov else None
            if pages_filter and page_no not in pages_filter:
                continue

            pil_img = (
                pic.image.pil_image
                if hasattr(pic, "image") and pic.image and hasattr(pic.image, "pil_image")
                else None
            )
            if pil_img is None:
                described.append({"page": page_no, "description": "Image data not available."})
                continue

            w, h = pil_img.size
            if w < 50 or h < 50:
                continue

            buf = io.BytesIO()
            pil_img.save(buf, format="PNG")
            img_b64 = base64.standard_b64encode(buf.getvalue()).decode("utf-8")

            try:
                if sampling_available:
                    res = await ctx.session.create_message(
                        messages=[SamplingMessage(
                            role="user",
                            content=MCPImageContent(type="image", data=img_b64, mimeType="image/png"),
                        )],
                        max_tokens=300,
                        system_prompt=describe_prompt,
                        include_context="none",
                    )
                    description = (
                        res.content.text.strip()
                        if hasattr(res.content, "text")
                        else "No description available."
                    )
                else:
                    response = direct_client.messages.create(
                        model="claude-haiku-4-5-20251001",
                        max_tokens=300,
                        messages=[{"role": "user", "content": [
                            {"type": "image", "source": {
                                "type": "base64", "media_type": "image/png", "data": img_b64,
                            }},
                            {"type": "text", "text": describe_prompt},
                        ]}],
                    )
                    description = (
                        response.content[0].text.strip()
                        if response.content
                        else "No description available."
                    )
            except Exception as exc:
                description = f"Description failed: {exc}"

            described.append({"page": page_no, "width_px": w, "height_px": h, "description": description})
            count += 1

        return json.dumps({
            "file_path": file_path,
            "file_name": os.path.basename(file_path),
            "total_pages": page_count,
            "figures_described": len(described),
            "max_figures_limit": max_figures,
            "truncated": count >= max_figures,
            "llm_backend": llm_backend,
            "figures": described,
        }, indent=2)
    except Exception as e:
        return json.dumps({"error": f"Figure description failed: {str(e)}"}, indent=2)


# ─── Entry Point ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    mcp.run(transport="stdio")
