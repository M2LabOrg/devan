# Dependency License Audit

> Last updated: 2026-04-19. Re-run before each public release.
>
> Purpose: verify every dependency is compatible with the project's Apache 2.0 licence before publishing to `m2laborg/devan`.

---

## Summary

| Status | Count |
|---|---|
| ✅ Compatible (MIT / BSD / Apache 2.0) | 19 |
| ⚠️ Weak copyleft — review required (LGPL) | 1 |
| ✅ Previously AGPL — now resolved | 2 |

**All blockers resolved.** `pymupdf`/`pymupdf4llm` (AGPL 3.0) replaced with `docling` (MIT) + `pypdf` (MIT) in `pdf-extractor` and `document` servers. See §Blockers for migration record.

---

## MCP Servers

### data-modelling

| Package | Version spec | License | Compatible? |
|---|---|---|---|
| mcp | ≥1.26.0 | MIT | ✅ |
| pandas | ≥2.0.0 | BSD-3-Clause | ✅ |
| pyarrow | ≥14.0.0 | Apache 2.0 | ✅ |
| openpyxl | ≥3.1.0 | MIT | ✅ |
| python-docx | ≥1.1.0 | MIT | ✅ |
| python-pptx | ≥1.0.0 | MIT | ✅ |
| pyyaml | ≥6.0 | MIT | ✅ |
| lxml | ≥5.0 | BSD-3-Clause + LGPL 2.0 (libxml2/libxslt bindings) | ⚠️ LGPL — dynamically linked, distribution is fine; verify no static linking |

### document

| Package | Version spec | License | Compatible? |
|---|---|---|---|
| mcp | ≥1.26.0 | MIT | ✅ |
| docling | ≥2.0.0 | MIT (IBM) | ✅ |
| pandas | ≥2.0.0 | BSD-3-Clause | ✅ |
| openpyxl | ≥3.1.0 | MIT | ✅ |
| pypdf | ≥4.0.0 | MIT | ✅ |
| python-docx | ≥1.1.0 | MIT | ✅ |
| anthropic | ≥0.40.0 | MIT | ✅ |

### excel-pipeline

| Package | Version spec | License | Compatible? |
|---|---|---|---|
| mcp | ≥1.26.0 | MIT | ✅ |
| openpyxl | ≥3.1.0 | MIT | ✅ |
| pandas | ≥2.0.0 | BSD-3-Clause | ✅ |

### excel-retriever

| Package | Version spec | License | Compatible? |
|---|---|---|---|
| mcp | ≥1.26.0 | MIT | ✅ |
| docling | ≥2.0.0 | MIT (IBM) | ✅ |
| pandas | ≥2.0.0 | BSD-3-Clause | ✅ |
| openpyxl | ≥3.1.0 | MIT | ✅ |
| opensearch-py | ≥3.1.0 | Apache 2.0 | ✅ |

### guardrail

| Package | Version spec | License | Compatible? |
|---|---|---|---|
| mcp | ≥1.0.0 | MIT | ✅ |

### pdf-extractor

| Package | Version spec | License | Compatible? |
|---|---|---|---|
| mcp | ≥1.26.0 | MIT | ✅ |
| docling | ≥2.0.0 | MIT (IBM) | ✅ |
| pypdf | ≥4.0.0 | MIT | ✅ |
| anthropic | ≥0.40.0 | MIT | ✅ |

### prompt-engineering

| Package | Version spec | License | Compatible? |
|---|---|---|---|
| mcp | ≥1.26.0 | MIT | ✅ |
| docling | ≥2.0.0 | MIT (IBM) | ✅ |

### webdesign

| Package | Version spec | License | Compatible? |
|---|---|---|---|
| mcp | ≥1.26.0 | MIT | ✅ |

### webscraper

| Package | Version spec | License | Compatible? |
|---|---|---|---|
| mcp | ≥1.26.0 | MIT | ✅ |
| httpx | ≥0.27.0 | BSD-3-Clause | ✅ |
| beautifulsoup4 | ≥4.12 | MIT | ✅ |
| lxml | ≥5.0 | BSD-3-Clause + LGPL 2.0 | ⚠️ LGPL — see note above |
| firecrawl-py | ≥1.0.0 | MIT | ✅ |
| openpyxl | ≥3.1.0 | MIT | ✅ |

---

## Client UI (`client/`)

| Package | Version spec | License | Compatible? |
|---|---|---|---|
| flask | ≥3.0.0 | BSD-3-Clause | ✅ |
| flask-socketio | ≥5.3.5 | MIT | ✅ |
| python-socketio | ≥5.10.0 | MIT | ✅ |
| requests | ≥2.32.3 | Apache 2.0 | ✅ |
| mcp | ≥1.0.0 | MIT | ✅ |
| python-dotenv | ≥1.0.0 | BSD-3-Clause | ✅ |
| httpx | ≥0.27.0 | BSD-3-Clause | ✅ |
| python-docx | ≥1.1.0 | MIT | ✅ |

---

## Blockers and Resolutions

### ✅ PyMuPDF / pymupdf4llm — RESOLVED (was AGPL 3.0)

**Affected servers:** `pdf-extractor`, `document`

**Resolution (2026-04-19):** Replaced `pymupdf` and `pymupdf4llm` with `docling` (MIT, IBM) for full extraction and `pypdf` (MIT) for lightweight page-count metadata. Both servers are now Apache 2.0 compatible.

- `pdf-extractor/mcp_project/pdf_extractor_server.py` — rewritten; docling is the sole engine.
- `document/mcp_project/document_server.py` — targeted edits; all pymupdf call sites replaced.
- Both `pyproject.toml` files updated accordingly.

**Trade-offs accepted:**
- `analyze_pdf_structure` now performs full docling conversion instead of a lightweight page scan (slower but correct).
- `page_range` parameter in `extract_pdf` is kept for API compatibility but docling always converts the full document; table/figure filtering by page still works via provenance.
- `describe_figures` now uses docling's `generate_picture_images=True` to extract embedded images instead of rendering pages with PyMuPDF.

### ⚠️ lxml (LGPL 2.0+)

**Affected servers:** `data-modelling`, `webscraper`

**Assessment:** Not a blocker. lxml is dynamically linked as a Python extension module. LGPL permits use in Apache 2.0 projects as long as the library is not statically linked into a larger binary. Standard Python packaging satisfies this requirement. No action needed unless we ship a bundled binary (e.g., PyInstaller single-file exe).

---

## Re-audit Checklist

Run this before each public release:

```bash
# Install pip-licenses in each venv, then:
pip-licenses --format=markdown --with-urls
```

Or use `uv run pip-licenses` within each `mcp_project/` environment.
