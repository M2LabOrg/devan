# PDF Extractor MCP Server

Production-grade PDF extraction server for LLM and RAG pipelines. Replaces Microsoft Document Intelligence with open-source tools.

## Engines

| Engine | Best For | Speed | Tables | Figures | Install |
|--------|----------|-------|--------|---------|---------|
| **Docling** (IBM) | Complex layouts, scanned docs | Medium | Excellent | Yes | `uv add docling` |
| **PyMuPDF4LLM** | High-volume, large docs | Very Fast | Good | Metadata | `uv add pymupdf pymupdf4llm` |

The server auto-selects the best engine per file, or you can specify one.

## Tools

| Tool | Purpose |
|------|---------|
| `list_pdf_files` | Discover PDFs with page counts and sizes |
| `extract_pdf` | Full extraction to Markdown (tables, figures, text) |
| `extract_tables` | Extract only tables as Markdown |
| `extract_figures` | Catalogue embedded images/figures |
| `chunk_pdf_for_rag` | Extract + chunk for vector DB ingestion |
| `batch_extract` | Process all PDFs in a directory |
| `analyze_pdf_structure` | Quick structural scan without full extraction |
| `get_extraction_status` | Check engine availability and config |

## Chunking Strategies (for RAG)

- **tokens** — Word-based chunks with configurable size and overlap (default 512 words, 50 word overlap)
- **pages** — Split by page boundaries
- **sections** — Split by markdown headings

## Quick Start

```bash
cd mcp_project
uv sync
uv run pdf_extractor_server.py
```

## Configuration

Environment variables:
- `PDF_DIR` — Directory containing PDF files (default: `../pdf_files`)
- `PDF_OUTPUT_DIR` — Output directory for batch extraction (default: `../output`)
- `PDF_MAX_PAGES_PER_CHUNK` — Max pages per chunk (default: 20)

## Example: RAG Pipeline

```
1. list_pdf_files()          → Discover all PDFs
2. analyze_pdf_structure()   → Assess complexity
3. chunk_pdf_for_rag()       → Get chunks ready for embedding
4. → Send chunks to your embedding model → Store in vector DB
```
