"""Data model definitions for the data-modelling MCP server."""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


def _uid(prefix: str = "dm") -> str:
    return f"{prefix}_{uuid.uuid4().hex[:8]}"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class ColumnModel:
    """Schema definition for a single column."""

    name: str
    # SQLite-style types: text | integer | real | boolean | date | datetime | blob
    dtype: str
    nullable: bool = True
    unique: bool = False
    primary_key: bool = False
    # "table_name.column_name" when this column is a FK
    foreign_key: Optional[str] = None
    sample_values: List[Any] = field(default_factory=list)
    null_count: int = 0
    cardinality: int = 0  # number of distinct non-null values

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "dtype": self.dtype,
            "nullable": self.nullable,
            "unique": self.unique,
            "primary_key": self.primary_key,
            "foreign_key": self.foreign_key,
            "sample_values": [str(v) for v in self.sample_values[:5]],
            "null_count": self.null_count,
            "cardinality": self.cardinality,
        }


@dataclass
class TableModel:
    """Schema definition for a single table."""

    name: str
    columns: Dict[str, ColumnModel] = field(default_factory=dict)
    row_count: int = 0
    source_file: Optional[str] = None
    source_sheet: Optional[str] = None  # populated for multi-sheet Excel files

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "columns": {k: v.to_dict() for k, v in self.columns.items()},
            "row_count": self.row_count,
            "source_file": self.source_file,
            "source_sheet": self.source_sheet,
            "primary_keys": [c.name for c in self.columns.values() if c.primary_key],
        }


@dataclass
class Relationship:
    """A foreign-key relationship between two tables."""

    from_table: str
    from_column: str
    to_table: str
    to_column: str
    # one-to-one | one-to-many | many-to-one | many-to-many
    relationship_type: str = "many-to-one"
    # 0–1; 1.0 for manually defined, <1.0 for auto-detected
    confidence: float = 1.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "from_table": self.from_table,
            "from_column": self.from_column,
            "to_table": self.to_table,
            "to_column": self.to_column,
            "relationship_type": self.relationship_type,
            "confidence": round(self.confidence, 3),
        }


@dataclass
class DataModelSession:
    """A complete data-modelling session: schema, relationships, and metadata."""

    session_id: str
    name: str
    tables: Dict[str, TableModel] = field(default_factory=dict)
    relationships: List[Relationship] = field(default_factory=list)
    source_files: List[str] = field(default_factory=list)
    created_at: str = field(default_factory=_now_iso)
    updated_at: str = field(default_factory=_now_iso)
    notes: str = ""

    @staticmethod
    def create(name: str) -> "DataModelSession":
        return DataModelSession(session_id=_uid("sess"), name=name)

    def touch(self) -> None:
        self.updated_at = _now_iso()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "session_id": self.session_id,
            "name": self.name,
            "tables": {k: v.to_dict() for k, v in self.tables.items()},
            "relationships": [r.to_dict() for r in self.relationships],
            "source_files": self.source_files,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "notes": self.notes,
        }
