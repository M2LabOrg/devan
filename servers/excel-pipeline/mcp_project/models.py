"""
Core data models for the Excel Pipeline.

Stable entity classes used across all backend services and MCP tool outputs.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class TriageResult(str, Enum):
    SUPPORTED = "SUPPORTED"
    SUPPORTED_WITH_WARNINGS = "SUPPORTED_WITH_WARNINGS"
    REVIEW_REQUIRED = "REVIEW_REQUIRED"
    UNSUPPORTED = "UNSUPPORTED"


class Severity(str, Enum):
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    BLOCKER = "BLOCKER"


class ReadinessState(str, Enum):
    NOT_READY = "NOT_READY"
    READY_WITH_WARNINGS = "READY_WITH_WARNINGS"
    READY = "READY"
    BLOCKED = "BLOCKED"


class ValidationResult(str, Enum):
    PASSED = "PASSED"
    PASSED_WITH_WARNINGS = "PASSED_WITH_WARNINGS"
    FAILED = "FAILED"
    BLOCKED = "BLOCKED"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _uid(prefix: str = "") -> str:
    short = uuid.uuid4().hex[:8]
    return f"{prefix}_{short}" if prefix else short


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


# ---------------------------------------------------------------------------
# Core entities
# ---------------------------------------------------------------------------

@dataclass
class WorkbookRecord:
    workbook_id: str
    file_name: str
    file_path: str
    sheet_count: int = 0
    created_at: str = field(default_factory=_now_iso)

    @staticmethod
    def create(file_name: str, file_path: str, sheet_count: int = 0) -> "WorkbookRecord":
        return WorkbookRecord(
            workbook_id=_uid("wb"),
            file_name=file_name,
            file_path=file_path,
            sheet_count=sheet_count,
        )


@dataclass
class SheetRecord:
    sheet_id: str
    workbook_id: str
    sheet_name: str
    visible: bool = True
    row_count_estimate: int = 0
    column_count_estimate: int = 0
    named_tables: List[Dict[str, str]] = field(default_factory=list)
    merged_regions: List[str] = field(default_factory=list)

    @staticmethod
    def create(workbook_id: str, sheet_name: str, **kwargs) -> "SheetRecord":
        return SheetRecord(sheet_id=_uid("sh"), workbook_id=workbook_id, sheet_name=sheet_name, **kwargs)


@dataclass
class DetectedTable:
    detected_table_id: str
    workbook_id: str
    sheet_name: str
    range: str
    header_rows: List[int] = field(default_factory=list)
    unit_rows: List[int] = field(default_factory=list)
    data_start_row: int = 0
    data_end_row: int = 0
    index_columns: List[str] = field(default_factory=list)
    column_headers: List[str] = field(default_factory=list)
    detection_confidence: float = 0.0
    parser_agreement: Dict[str, bool] = field(default_factory=dict)
    notes_detected_nearby: bool = False
    provenance: Dict[str, Any] = field(default_factory=dict)

    @staticmethod
    def create(workbook_id: str, sheet_name: str, **kwargs) -> "DetectedTable":
        return DetectedTable(detected_table_id=_uid("dt"), workbook_id=workbook_id, sheet_name=sheet_name, **kwargs)


@dataclass
class SourceLineage:
    lineage_id: str
    entity_type: str
    entity_id: str
    source_workbook_id: str
    source_sheet_name: str = ""
    source_range: str = ""
    source_table_id: str = ""
    parser_source: List[str] = field(default_factory=list)
    mapping_rule: str = ""
    validation_state: str = ""

    @staticmethod
    def create(entity_type: str, entity_id: str, workbook_id: str, **kwargs) -> "SourceLineage":
        return SourceLineage(lineage_id=_uid("lin"), entity_type=entity_type, entity_id=entity_id, source_workbook_id=workbook_id, **kwargs)


@dataclass
class Asset:
    asset_id: str
    asset_name: str
    asset_type: str = ""

    @staticmethod
    def create(asset_name: str, asset_type: str = "") -> "Asset":
        return Asset(asset_id=_uid("asset"), asset_name=asset_name, asset_type=asset_type)


@dataclass
class Scenario:
    scenario_id: str
    scenario_name: str

    @staticmethod
    def create(scenario_name: str) -> "Scenario":
        return Scenario(scenario_id=_uid("scn"), scenario_name=scenario_name)


@dataclass
class KPI:
    kpi_id: str
    kpi_name: str
    default_unit: str = ""

    @staticmethod
    def create(kpi_name: str, default_unit: str = "") -> "KPI":
        return KPI(kpi_id=_uid("kpi"), kpi_name=kpi_name, default_unit=default_unit)


@dataclass
class Measurement:
    measurement_id: str
    asset_id: str
    scenario_id: str
    kpi_id: str
    value: float
    unit: str = ""
    lineage_ref: str = ""

    @staticmethod
    def create(asset_id: str, scenario_id: str, kpi_id: str, value: float, unit: str = "", lineage_ref: str = "") -> "Measurement":
        return Measurement(measurement_id=_uid("msr"), asset_id=asset_id, scenario_id=scenario_id, kpi_id=kpi_id, value=value, unit=unit, lineage_ref=lineage_ref)


@dataclass
class TimeSeriesPoint:
    point_id: str
    measurement_id: str
    timestamp: str
    value: float
    unit: str = ""

    @staticmethod
    def create(measurement_id: str, timestamp: str, value: float, unit: str = "") -> "TimeSeriesPoint":
        return TimeSeriesPoint(point_id=_uid("ts"), measurement_id=measurement_id, timestamp=timestamp, value=value, unit=unit)


@dataclass
class Assumption:
    assumption_id: str
    description: str
    value: Any = None
    unit: str = ""
    source_ref: str = ""

    @staticmethod
    def create(description: str, **kwargs) -> "Assumption":
        return Assumption(assumption_id=_uid("asm"), description=description, **kwargs)


@dataclass
class ValidationIssue:
    issue_id: str
    severity: str
    code: str
    message: str
    entity_ref: Optional[Dict[str, str]] = None

    @staticmethod
    def create(severity: str, code: str, message: str, entity_ref: Optional[Dict[str, str]] = None) -> "ValidationIssue":
        return ValidationIssue(issue_id=_uid("vi"), severity=severity, code=code, message=message, entity_ref=entity_ref)


@dataclass
class FigureSpec:
    figure_id: str
    chart_type: str
    title: str
    entity_refs: List[Dict[str, str]] = field(default_factory=list)
    filters: Dict[str, str] = field(default_factory=dict)
    x_field: str = ""
    y_field: str = ""
    unit: str = ""
    ready_to_render: bool = False

    @staticmethod
    def create(chart_type: str, title: str, **kwargs) -> "FigureSpec":
        return FigureSpec(figure_id=_uid("fig"), chart_type=chart_type, title=title, **kwargs)


@dataclass
class ReportBundle:
    bundle_id: str
    profile: str
    contents: List[str] = field(default_factory=list)
    uri: str = ""

    @staticmethod
    def create(profile: str, contents: List[str], uri: str = "") -> "ReportBundle":
        return ReportBundle(bundle_id=_uid("rb"), profile=profile, contents=contents, uri=uri)


@dataclass
class RiskSignal:
    code: str
    severity: str
    message: str


@dataclass
class ConfidenceSummary:
    overall_model_confidence: float = 0.0
    boundary_detection_confidence: float = 0.0
    schema_match_confidence: float = 0.0
    semantic_mapping_confidence: float = 0.0


@dataclass
class CanonicalModel:
    model_id: str
    workbook_id: str
    processing_profile: str = "default"
    assets: List[Asset] = field(default_factory=list)
    scenarios: List[Scenario] = field(default_factory=list)
    kpis: List[KPI] = field(default_factory=list)
    measurements: List[Measurement] = field(default_factory=list)
    time_series: List[TimeSeriesPoint] = field(default_factory=list)
    assumptions: List[Assumption] = field(default_factory=list)
    lineage: List[SourceLineage] = field(default_factory=list)
    figure_specs: List[FigureSpec] = field(default_factory=list)
    issues: List[ValidationIssue] = field(default_factory=list)
    confidence: ConfidenceSummary = field(default_factory=ConfidenceSummary)
    validation_result: Optional[str] = None
    ready_for_export: bool = False

    @staticmethod
    def create(workbook_id: str, processing_profile: str = "default") -> "CanonicalModel":
        return CanonicalModel(model_id=_uid("cm"), workbook_id=workbook_id, processing_profile=processing_profile)


# ---------------------------------------------------------------------------
# Serialisation helper
# ---------------------------------------------------------------------------

def to_dict(obj) -> Any:
    """Recursively convert dataclass instances to dicts."""
    if hasattr(obj, "__dataclass_fields__"):
        return {k: to_dict(v) for k, v in asdict(obj).items()}
    if isinstance(obj, list):
        return [to_dict(i) for i in obj]
    if isinstance(obj, dict):
        return {k: to_dict(v) for k, v in obj.items()}
    if isinstance(obj, Enum):
        return obj.value
    return obj
