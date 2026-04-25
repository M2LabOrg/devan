"""
Excel Pipeline MCP Server

Robust Excel data extraction, processing, modelling, and validation.
Exposes stable, high-level, trusted tools to an LLM or agent client.

Run:
    cd servers/excel-pipeline/mcp_project
    uv sync
    uv run excel_pipeline_server.py
"""

from __future__ import annotations

from mcp.server.fastmcp import FastMCP

import tools

# ---------------------------------------------------------------------------
# Server instance
# ---------------------------------------------------------------------------

mcp = FastMCP("excel-pipeline")

# ---------------------------------------------------------------------------
# Register tools
# ---------------------------------------------------------------------------


@mcp.tool()
def triage_workbook(
    workbook_uri: str,
    processing_profile: str = "default",
    include_sheet_inventory: bool = True,
    include_risk_signals: bool = True,
) -> str:
    """Assess whether a workbook is supported, partially supported, review-required, or unsupported.

    Args:
        workbook_uri: Path to the Excel workbook file.
        processing_profile: Processing profile to apply (default or energy_systems).
        include_sheet_inventory: Include sheet inventory in the response.
        include_risk_signals: Include risk signals in the response.

    Returns:
        JSON with triage result, confidence, summary, risk signals, and lineage ref.
    """
    return tools.triage_workbook(workbook_uri, processing_profile, include_sheet_inventory, include_risk_signals)


@mcp.tool()
def inspect_workbook_structure(
    workbook_uri: str,
    include_ranges: bool = True,
    include_named_tables: bool = True,
    include_hidden_items: bool = True,
) -> str:
    """Return the physical workbook model and sheet inventory in a stable, structured form.

    Args:
        workbook_uri: Path to the Excel workbook file.
        include_ranges: Include cell range information.
        include_named_tables: Include named table definitions.
        include_hidden_items: Include hidden sheets and items.

    Returns:
        JSON with workbook metadata, sheet details, and lineage ref.
    """
    return tools.inspect_workbook_structure(workbook_uri, include_ranges, include_named_tables, include_hidden_items)


@mcp.tool()
def detect_candidate_tables(
    workbook_uri: str,
    sheet_names: list[str] | None = None,
    detection_profile: str = "default",
    include_parser_comparison: bool = True,
) -> str:
    """Detect candidate tabular regions and return logical table metadata with confidence and provenance.

    Args:
        workbook_uri: Path to the Excel workbook file.
        sheet_names: Optional list of specific sheet names to scan.
        detection_profile: Detection profile to use.
        include_parser_comparison: Compare results from multiple parsers (openpyxl, pandas, docling).

    Returns:
        JSON with detected tables array and summary.
    """
    return tools.detect_candidate_tables(workbook_uri, sheet_names, detection_profile, include_parser_comparison)


@mcp.tool()
def build_canonical_model(
    workbook_uri: str,
    processing_profile: str = "default",
    mapping_profile: str = "default",
    selected_table_ids: list[str] | None = None,
    allow_llm_disambiguation: bool = False,
) -> str:
    """Map detected workbook content into a controlled business schema (canonical model).

    Args:
        workbook_uri: Path to the Excel workbook file.
        processing_profile: Processing profile (default or energy_systems).
        mapping_profile: Mapping profile for semantic column mapping.
        selected_table_ids: Optional list of specific detected_table_ids to include.
        allow_llm_disambiguation: Allow LLM-assisted disambiguation for ambiguous headers.

    Returns:
        JSON with canonical model summary, mapping summary, unresolved items, and lineage ref.
    """
    return tools.build_canonical_model(workbook_uri, processing_profile, mapping_profile, selected_table_ids, allow_llm_disambiguation)


@mcp.tool()
def validate_canonical_model(
    model_id: str,
    validation_profile: str = "default",
    include_reconciliation: bool = True,
) -> str:
    """Run validation, reconciliation, and confidence checks over the canonical model.

    Args:
        model_id: The ID of the canonical model to validate.
        validation_profile: Validation profile to apply.
        include_reconciliation: Include reconciliation checks.

    Returns:
        JSON with validation result, issues, confidence summary, and export readiness.
    """
    return tools.validate_canonical_model(model_id, validation_profile, include_reconciliation)


@mcp.tool()
def get_lineage(
    entity_type: str,
    entity_id: str,
) -> str:
    """Return provenance for a model entity, table, or figure input.

    Args:
        entity_type: The type of entity (e.g. Measurement, Asset, KPI).
        entity_id: The unique ID of the entity.

    Returns:
        JSON with lineage/provenance details including source workbook, sheet, range, and parser.
    """
    return tools.get_lineage(entity_type, entity_id)


@mcp.tool()
def export_ready_json(
    model_id: str,
    export_profile: str = "report_ready_v1",
    include_lineage: bool = True,
    include_validation: bool = True,
    include_null_fields: bool = False,
) -> str:
    """Export a validated canonical model as a downstream-ready JSON package.

    Args:
        model_id: The ID of the canonical model to export.
        export_profile: Export profile version.
        include_lineage: Include lineage data in the export.
        include_validation: Include validation data in the export.
        include_null_fields: Include null/empty fields in the output.

    Returns:
        JSON with export metadata and payload preview.
    """
    return tools.export_ready_json(model_id, export_profile, include_lineage, include_validation, include_null_fields)


@mcp.tool()
def prepare_figure_specs(
    model_id: str,
    figure_profile: str = "default",
    requested_outputs: list[str] | None = None,
) -> str:
    """Generate structured figure specifications from validated data.

    Does not render the final chart image. Prepares a reproducible chart contract.

    Args:
        model_id: The ID of the canonical model.
        figure_profile: Figure profile to apply.
        requested_outputs: List of figure types (e.g. asset_comparison, time_series_trend, kpi_cards).

    Returns:
        JSON with figure specifications ready for a rendering engine.
    """
    return tools.prepare_figure_specs(model_id, figure_profile, requested_outputs)


@mcp.tool()
def create_report_bundle(
    model_id: str,
    bundle_profile: str = "report_bundle_v1",
    include_json: bool = True,
    include_validation_report: bool = True,
    include_figure_specs: bool = True,
    include_summary_payload: bool = True,
) -> str:
    """Package all validated outputs needed for report production.

    Args:
        model_id: The ID of the canonical model.
        bundle_profile: Bundle profile to apply.
        include_json: Include report_ready.json in the bundle.
        include_validation_report: Include validation_report.json.
        include_figure_specs: Include figure_specs.json.
        include_summary_payload: Include summary_payload.json.

    Returns:
        JSON with bundle metadata and contents list.
    """
    return tools.create_report_bundle(model_id, bundle_profile, include_json, include_validation_report, include_figure_specs, include_summary_payload)


@mcp.tool()
def grounded_query_validated_data(
    model_id: str,
    question: str,
    response_mode: str = "structured",
    include_lineage: bool = True,
) -> str:
    """Allow grounded natural-language querying only over validated data.

    Args:
        model_id: The ID of the canonical model.
        question: Natural-language question about the validated data.
        response_mode: Response mode (structured or text).
        include_lineage: Include lineage references in the answer.

    Returns:
        JSON with answer, confidence, supporting entities, and lineage refs.
    """
    return tools.grounded_query_validated_data(model_id, question, response_mode, include_lineage)


@mcp.tool()
def process_workbook_end_to_end(
    workbook_uri: str,
    processing_profile: str = "default",
    bundle_profile: str = "report_bundle_v1",
    allow_llm_disambiguation: bool = False,
) -> str:
    """Run the full end-to-end pipeline: triage, detection, modelling, validation, figures, and bundle export.

    Args:
        workbook_uri: Path to the Excel workbook file.
        processing_profile: Processing profile (default or energy_systems).
        bundle_profile: Bundle profile for the final export package.
        allow_llm_disambiguation: Allow LLM-assisted disambiguation.

    Returns:
        JSON with triage result, validation result, model_id, bundle URI, and any warnings.
    """
    return tools.process_workbook_end_to_end(workbook_uri, processing_profile, bundle_profile, allow_llm_disambiguation)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    mcp.run()
