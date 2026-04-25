"""
MCP Tool Wrappers for the Excel Pipeline.

Each tool validates input, calls the backend service, and returns structured JSON.
No business logic is duplicated here.
"""

from __future__ import annotations

import json
from typing import Any, Dict, List, Optional


import services


# ---------------------------------------------------------------------------
# Standard error envelope
# ---------------------------------------------------------------------------

def _error_response(tool_name: str, code: str, message: str, severity: str = "ERROR", details: Optional[Dict] = None) -> str:
    return json.dumps({
        "tool_name": tool_name,
        "status": "error",
        "error": {
            "code": code,
            "message": message,
            "severity": severity,
            "details": details or {},
        },
    }, indent=2)


def _success_response(tool_name: str, payload: Dict[str, Any]) -> str:
    return json.dumps({"tool_name": tool_name, "status": "success", **payload}, indent=2, default=str)


# ===================================================================
# Tool: triage_workbook
# ===================================================================

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
    try:
        result = services.triage_workbook(
            workbook_uri=workbook_uri,
            processing_profile=processing_profile,
            include_sheet_inventory=include_sheet_inventory,
            include_risk_signals=include_risk_signals,
        )
        return _success_response("triage_workbook", result)
    except FileNotFoundError as e:
        return _error_response("triage_workbook", "FILE_NOT_FOUND", str(e))
    except ValueError as e:
        return _error_response("triage_workbook", "UNSUPPORTED_FILE_TYPE", str(e))
    except Exception as e:
        return _error_response("triage_workbook", "INTERNAL_SERVICE_ERROR", str(e))


# ===================================================================
# Tool: inspect_workbook_structure
# ===================================================================

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
    try:
        result = services.inspect_workbook_structure(
            workbook_uri=workbook_uri,
            include_ranges=include_ranges,
            include_named_tables=include_named_tables,
            include_hidden_items=include_hidden_items,
        )
        return _success_response("inspect_workbook_structure", result)
    except FileNotFoundError as e:
        return _error_response("inspect_workbook_structure", "FILE_NOT_FOUND", str(e))
    except ValueError as e:
        return _error_response("inspect_workbook_structure", "UNSUPPORTED_FILE_TYPE", str(e))
    except Exception as e:
        return _error_response("inspect_workbook_structure", "INTERNAL_SERVICE_ERROR", str(e))


# ===================================================================
# Tool: detect_candidate_tables
# ===================================================================

def detect_candidate_tables(
    workbook_uri: str,
    sheet_names: Optional[List[str]] = None,
    detection_profile: str = "default",
    include_parser_comparison: bool = True,
) -> str:
    """Detect candidate tabular regions and return logical table metadata with confidence.

    Args:
        workbook_uri: Path to the Excel workbook file.
        sheet_names: Optional list of specific sheet names to scan.
        detection_profile: Detection profile to use.
        include_parser_comparison: Compare results from multiple parsers.

    Returns:
        JSON with detected tables and summary.
    """
    try:
        result = services.detect_candidate_tables(
            workbook_uri=workbook_uri,
            sheet_names=sheet_names,
            detection_profile=detection_profile,
            include_parser_comparison=include_parser_comparison,
        )
        return _success_response("detect_candidate_tables", result)
    except FileNotFoundError as e:
        return _error_response("detect_candidate_tables", "FILE_NOT_FOUND", str(e))
    except ValueError as e:
        return _error_response("detect_candidate_tables", "UNSUPPORTED_FILE_TYPE", str(e))
    except Exception as e:
        return _error_response("detect_candidate_tables", "INTERNAL_SERVICE_ERROR", str(e))


# ===================================================================
# Tool: build_canonical_model
# ===================================================================

def build_canonical_model(
    workbook_uri: str,
    processing_profile: str = "default",
    mapping_profile: str = "default",
    selected_table_ids: Optional[List[str]] = None,
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
    try:
        result = services.build_canonical_model(
            workbook_uri=workbook_uri,
            processing_profile=processing_profile,
            mapping_profile=mapping_profile,
            selected_table_ids=selected_table_ids,
            allow_llm_disambiguation=allow_llm_disambiguation,
        )
        return _success_response("build_canonical_model", result)
    except FileNotFoundError as e:
        return _error_response("build_canonical_model", "FILE_NOT_FOUND", str(e))
    except ValueError as e:
        return _error_response("build_canonical_model", "LOW_CONFIDENCE_MAPPING", str(e))
    except Exception as e:
        return _error_response("build_canonical_model", "INTERNAL_SERVICE_ERROR", str(e))


# ===================================================================
# Tool: validate_canonical_model
# ===================================================================

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
    try:
        result = services.validate_canonical_model(
            model_id=model_id,
            validation_profile=validation_profile,
            include_reconciliation=include_reconciliation,
        )
        return _success_response("validate_canonical_model", result)
    except ValueError as e:
        return _error_response("validate_canonical_model", "VALIDATION_BLOCKER", str(e))
    except Exception as e:
        return _error_response("validate_canonical_model", "INTERNAL_SERVICE_ERROR", str(e))


# ===================================================================
# Tool: get_lineage
# ===================================================================

def get_lineage(
    entity_type: str,
    entity_id: str,
) -> str:
    """Return provenance for a model entity, table, or figure input.

    Args:
        entity_type: The type of entity (e.g. Measurement, Asset, KPI).
        entity_id: The unique ID of the entity.

    Returns:
        JSON with lineage/provenance details.
    """
    try:
        result = services.get_lineage(entity_type=entity_type, entity_id=entity_id)
        return _success_response("get_lineage", result)
    except ValueError as e:
        return _error_response("get_lineage", "LINEAGE_NOT_FOUND", str(e))
    except Exception as e:
        return _error_response("get_lineage", "INTERNAL_SERVICE_ERROR", str(e))


# ===================================================================
# Tool: export_ready_json
# ===================================================================

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
    try:
        result = services.export_ready_json(
            model_id=model_id,
            export_profile=export_profile,
            include_lineage=include_lineage,
            include_validation=include_validation,
            include_null_fields=include_null_fields,
        )
        return _success_response("export_ready_json", result)
    except ValueError as e:
        return _error_response("export_ready_json", "EXPORT_BLOCKED", str(e))
    except Exception as e:
        return _error_response("export_ready_json", "INTERNAL_SERVICE_ERROR", str(e))


# ===================================================================
# Tool: prepare_figure_specs
# ===================================================================

def prepare_figure_specs(
    model_id: str,
    figure_profile: str = "default",
    requested_outputs: Optional[List[str]] = None,
) -> str:
    """Generate structured figure specifications from validated data.

    Args:
        model_id: The ID of the canonical model.
        figure_profile: Figure profile to apply.
        requested_outputs: List of figure types to generate (e.g. asset_comparison, time_series_trend, kpi_cards).

    Returns:
        JSON with figure specifications ready for a rendering engine.
    """
    try:
        result = services.prepare_figure_specs(
            model_id=model_id,
            figure_profile=figure_profile,
            requested_outputs=requested_outputs,
        )
        return _success_response("prepare_figure_specs", result)
    except ValueError as e:
        return _error_response("prepare_figure_specs", "MODEL_NOT_FOUND", str(e))
    except Exception as e:
        return _error_response("prepare_figure_specs", "INTERNAL_SERVICE_ERROR", str(e))


# ===================================================================
# Tool: create_report_bundle
# ===================================================================

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
        include_json: Include the main report_ready.json.
        include_validation_report: Include validation_report.json.
        include_figure_specs: Include figure_specs.json.
        include_summary_payload: Include summary_payload.json.

    Returns:
        JSON with bundle metadata and contents list.
    """
    try:
        result = services.create_report_bundle(
            model_id=model_id,
            bundle_profile=bundle_profile,
            include_json=include_json,
            include_validation_report=include_validation_report,
            include_figure_specs=include_figure_specs,
            include_summary_payload=include_summary_payload,
        )
        return _success_response("create_report_bundle", result)
    except ValueError as e:
        return _error_response("create_report_bundle", "EXPORT_BLOCKED", str(e))
    except Exception as e:
        return _error_response("create_report_bundle", "INTERNAL_SERVICE_ERROR", str(e))


# ===================================================================
# Tool: grounded_query_validated_data
# ===================================================================

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
    try:
        result = services.grounded_query_validated_data(
            model_id=model_id,
            question=question,
            response_mode=response_mode,
            include_lineage=include_lineage,
        )
        return _success_response("grounded_query_validated_data", result)
    except ValueError as e:
        return _error_response("grounded_query_validated_data", "MODEL_NOT_FOUND", str(e))
    except Exception as e:
        return _error_response("grounded_query_validated_data", "INTERNAL_SERVICE_ERROR", str(e))


# ===================================================================
# Tool: process_workbook_end_to_end
# ===================================================================

def process_workbook_end_to_end(
    workbook_uri: str,
    processing_profile: str = "default",
    bundle_profile: str = "report_bundle_v1",
    allow_llm_disambiguation: bool = False,
) -> str:
    """Run the supported end-to-end flow and return ready outputs.

    This orchestration tool calls all pipeline stages (triage, detection, modelling,
    validation, figure preparation, and bundle export) in sequence.

    Args:
        workbook_uri: Path to the Excel workbook file.
        processing_profile: Processing profile (default or energy_systems).
        bundle_profile: Bundle profile for the final export package.
        allow_llm_disambiguation: Allow LLM-assisted disambiguation.

    Returns:
        JSON with triage result, validation result, model_id, bundle URI, and any warnings.
    """
    try:
        result = services.process_workbook_end_to_end(
            workbook_uri=workbook_uri,
            processing_profile=processing_profile,
            bundle_profile=bundle_profile,
            allow_llm_disambiguation=allow_llm_disambiguation,
        )
        return _success_response("process_workbook_end_to_end", result)
    except FileNotFoundError as e:
        return _error_response("process_workbook_end_to_end", "FILE_NOT_FOUND", str(e))
    except ValueError as e:
        return _error_response("process_workbook_end_to_end", "UNSUPPORTED_FILE_TYPE", str(e))
    except Exception as e:
        return _error_response("process_workbook_end_to_end", "INTERNAL_SERVICE_ERROR", str(e))
