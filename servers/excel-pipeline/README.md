# Excel Pipeline MCP Server

Robust Excel data extraction, processing, modelling, and validation exposed as stable MCP tools.

## Overview

This server provides a **standardised agent interface** to a deterministic Excel processing backend. It enables model-driven workflows to safely perform workbook triage, table detection, canonical modelling, validation, figure preparation, and export of ready-to-use JSON outputs.

## Architecture

```
excel_pipeline_server.py   ← MCP entry point (thin FastMCP wrapper)
tools.py                   ← MCP tool wrappers (input validation + error envelope)
services.py                ← Deterministic backend services (all business logic)
models.py                  ← Stable data model (dataclasses + enums)
```

**Design principle:** The MCP layer is a thin, structured, stable interface over the trusted backend. No business logic is duplicated in the tool wrappers.

## MCP Tools

| Tool | Purpose |
|------|---------|
| `triage_workbook` | Assess workbook support level (supported / warnings / review / unsupported) |
| `inspect_workbook_structure` | Return physical workbook model and sheet inventory |
| `detect_candidate_tables` | Detect tabular regions with confidence and parser agreement |
| `build_canonical_model` | Map detected content into a controlled business schema |
| `validate_canonical_model` | Run validation, reconciliation, and confidence checks |
| `get_lineage` | Return provenance for any model entity |
| `export_ready_json` | Export validated model as downstream-ready JSON |
| `prepare_figure_specs` | Generate structured chart specifications |
| `create_report_bundle` | Package all outputs for report production |
| `grounded_query_validated_data` | Answer natural-language queries over validated data |
| `process_workbook_end_to_end` | Run the full pipeline in one call |

## Pipeline Workflow

```
1. triage_workbook          → Is this workbook processable?
2. inspect_workbook_structure → What sheets/tables does it contain?
3. detect_candidate_tables   → Where are the data tables?
4. build_canonical_model     → Map to business entities (assets, KPIs, measurements)
5. validate_canonical_model  → Check consistency, units, completeness
6. export_ready_json         → Produce downstream-ready JSON package
7. prepare_figure_specs      → (optional) Chart specifications
8. create_report_bundle      → (optional) Full report package
9. grounded_query_validated_data → (optional) Query the validated data
```

## Quick Start

```bash
cd servers/excel-pipeline/mcp_project
uv sync
uv run excel_pipeline_server.py
```

## Output Contracts

The server produces these JSON artifacts:

- **`report_ready.json`** — Main downstream-ready package with assets, KPIs, measurements, lineage
- **`validation_report.json`** — Machine-readable validation results and issues
- **`figure_specs.json`** — Ready-to-render chart specifications
- **`summary_payload.json`** — Clean payload for grounded LLM summarisation

## Key Data Entities

`Asset`, `Scenario`, `KPI`, `Measurement`, `TimeSeriesPoint`, `Assumption`, `ValidationIssue`, `FigureSpec`, `SourceLineage`, `ReportBundle`

## Dependencies

- `mcp >= 1.26.0` — MCP Framework (FastMCP)
- `openpyxl >= 3.1.0` — Native Excel reading
- `pandas >= 2.0.0` — Tabular data processing
- `docling >= 2.0.0` — (optional) IBM document extraction
