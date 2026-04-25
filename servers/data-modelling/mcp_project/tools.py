"""MCP tool wrappers for the data-modelling server.

Each public function corresponds to one @mcp.tool().
Validates inputs, delegates to services, and returns a JSON-serialisable
string using the project's standard envelope:

  {"status": "success", "tool": "<name>", ...payload}
  {"status": "error",   "tool": "<name>", "error": {"code": ..., "message": ...}}
"""

from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

import services


# ---------------------------------------------------------------------------
# Response helpers
# ---------------------------------------------------------------------------


def _ok(tool: str, **payload) -> str:
    return json.dumps({"status": "success", "tool": tool, **payload}, default=str)


def _err(tool: str, code: str, message: str) -> str:
    return json.dumps(
        {"status": "error", "tool": tool, "error": {"code": code, "message": message}},
        default=str,
    )


# ---------------------------------------------------------------------------
# Session management
# ---------------------------------------------------------------------------


def create_session(name: str) -> str:
    try:
        session = services.create_session(name)
        return _ok("create_session", session=session.to_dict())
    except Exception as exc:
        return _err("create_session", "CREATE_FAILED", str(exc))


def list_sessions() -> str:
    try:
        sessions = services.list_sessions()
        return _ok(
            "list_sessions",
            count=len(sessions),
            sessions=[
                {
                    "session_id": s.session_id,
                    "name": s.name,
                    "tables": list(s.tables.keys()),
                    "relationship_count": len(s.relationships),
                    "created_at": s.created_at,
                    "updated_at": s.updated_at,
                }
                for s in sessions
            ],
        )
    except Exception as exc:
        return _err("list_sessions", "LIST_FAILED", str(exc))


def inspect_session(session_id: str) -> str:
    try:
        session = services.get_session(session_id)
        return _ok("inspect_session", session=session.to_dict())
    except KeyError as exc:
        return _err("inspect_session", "NOT_FOUND", str(exc))
    except Exception as exc:
        return _err("inspect_session", "INSPECT_FAILED", str(exc))


def delete_session(session_id: str) -> str:
    try:
        services.delete_session(session_id)
        return _ok("delete_session", session_id=session_id)
    except KeyError as exc:
        return _err("delete_session", "NOT_FOUND", str(exc))
    except Exception as exc:
        return _err("delete_session", "DELETE_FAILED", str(exc))


# ---------------------------------------------------------------------------
# Data ingestion
# ---------------------------------------------------------------------------


def ingest_file(
    session_id: str,
    file_path: str,
    table_name: Optional[str] = None,
) -> str:
    try:
        added = services.ingest_file(session_id, file_path, table_name)
        return _ok(
            "ingest_file",
            file_path=file_path,
            tables_added=[t.to_dict() for t in added],
            count=len(added),
        )
    except FileNotFoundError as exc:
        return _err("ingest_file", "FILE_NOT_FOUND", str(exc))
    except KeyError as exc:
        return _err("ingest_file", "NOT_FOUND", str(exc))
    except Exception as exc:
        return _err("ingest_file", "INGEST_FAILED", str(exc))


def ingest_text(
    session_id: str,
    text: str,
    table_name: str = "data",
    hint: str = "auto",
) -> str:
    try:
        added, detected = services.ingest_text(session_id, text, table_name, hint)
        return _ok(
            "ingest_text",
            detected_format=detected,
            tables_added=[t.to_dict() for t in added],
            count=len(added),
        )
    except KeyError as exc:
        return _err("ingest_text", "NOT_FOUND", str(exc))
    except Exception as exc:
        return _err("ingest_text", "INGEST_FAILED", str(exc))


def ingest_json_data(
    session_id: str,
    data: Any,
    table_name: str = "data",
) -> str:
    try:
        added = services.ingest_json_data(session_id, data, table_name)
        return _ok(
            "ingest_json_data",
            tables_added=[t.to_dict() for t in added],
            count=len(added),
        )
    except KeyError as exc:
        return _err("ingest_json_data", "NOT_FOUND", str(exc))
    except Exception as exc:
        return _err("ingest_json_data", "INGEST_FAILED", str(exc))


# ---------------------------------------------------------------------------
# Relationship detection & management
# ---------------------------------------------------------------------------


def detect_relationships(session_id: str) -> str:
    try:
        found = services.detect_relationships(session_id)
        return _ok(
            "detect_relationships",
            detected=len(found),
            relationships=[r.to_dict() for r in found],
        )
    except KeyError as exc:
        return _err("detect_relationships", "NOT_FOUND", str(exc))
    except Exception as exc:
        return _err("detect_relationships", "DETECT_FAILED", str(exc))


def add_relationship(
    session_id: str,
    from_table: str,
    from_column: str,
    to_table: str,
    to_column: str,
    relationship_type: str = "many-to-one",
) -> str:
    valid_types = {"one-to-one", "one-to-many", "many-to-one", "many-to-many"}
    if relationship_type not in valid_types:
        return _err(
            "add_relationship",
            "INVALID_TYPE",
            f"relationship_type must be one of {sorted(valid_types)}",
        )
    try:
        rel = services.add_relationship(
            session_id, from_table, from_column, to_table, to_column, relationship_type
        )
        return _ok("add_relationship", relationship=rel.to_dict())
    except KeyError as exc:
        return _err("add_relationship", "NOT_FOUND", str(exc))
    except Exception as exc:
        return _err("add_relationship", "ADD_FAILED", str(exc))


def remove_relationship(
    session_id: str,
    from_table: str,
    from_column: str,
) -> str:
    try:
        count = services.remove_relationship(session_id, from_table, from_column)
        return _ok("remove_relationship", removed=count)
    except KeyError as exc:
        return _err("remove_relationship", "NOT_FOUND", str(exc))
    except Exception as exc:
        return _err("remove_relationship", "REMOVE_FAILED", str(exc))


# ---------------------------------------------------------------------------
# Model manipulation
# ---------------------------------------------------------------------------


def rename_table(session_id: str, old_name: str, new_name: str) -> str:
    try:
        services.rename_table(session_id, old_name, new_name)
        return _ok("rename_table", old_name=old_name, new_name=new_name)
    except (KeyError, ValueError) as exc:
        return _err("rename_table", "RENAME_FAILED", str(exc))
    except Exception as exc:
        return _err("rename_table", "RENAME_FAILED", str(exc))


def rename_column(
    session_id: str, table_name: str, old_name: str, new_name: str
) -> str:
    try:
        services.rename_column(session_id, table_name, old_name, new_name)
        return _ok(
            "rename_column",
            table_name=table_name,
            old_name=old_name,
            new_name=new_name,
        )
    except KeyError as exc:
        return _err("rename_column", "NOT_FOUND", str(exc))
    except Exception as exc:
        return _err("rename_column", "RENAME_FAILED", str(exc))


def set_primary_key(
    session_id: str, table_name: str, columns: List[str]
) -> str:
    if not columns:
        return _err("set_primary_key", "INVALID_INPUT", "columns list must not be empty")
    try:
        services.set_primary_key(session_id, table_name, columns)
        return _ok("set_primary_key", table_name=table_name, primary_key=columns)
    except KeyError as exc:
        return _err("set_primary_key", "NOT_FOUND", str(exc))
    except Exception as exc:
        return _err("set_primary_key", "SET_FAILED", str(exc))


def set_column_type(
    session_id: str, table_name: str, column_name: str, dtype: str
) -> str:
    try:
        services.set_column_type(session_id, table_name, column_name, dtype)
        return _ok(
            "set_column_type",
            table_name=table_name,
            column_name=column_name,
            dtype=dtype,
        )
    except (KeyError, ValueError) as exc:
        return _err("set_column_type", "SET_FAILED", str(exc))
    except Exception as exc:
        return _err("set_column_type", "SET_FAILED", str(exc))


def set_notes(session_id: str, notes: str) -> str:
    try:
        services.set_notes(session_id, notes)
        return _ok("set_notes", session_id=session_id)
    except KeyError as exc:
        return _err("set_notes", "NOT_FOUND", str(exc))
    except Exception as exc:
        return _err("set_notes", "SET_FAILED", str(exc))


# ---------------------------------------------------------------------------
# Export
# ---------------------------------------------------------------------------


def export_sqlite(session_id: str, output_path: str) -> str:
    try:
        path = services.export_sqlite(session_id, output_path)
        session = services.get_session(session_id)
        return _ok(
            "export_sqlite",
            output_path=path,
            tables=list(session.tables.keys()),
            relationships=len(session.relationships),
        )
    except KeyError as exc:
        return _err("export_sqlite", "NOT_FOUND", str(exc))
    except Exception as exc:
        return _err("export_sqlite", "EXPORT_FAILED", str(exc))


def export_arrow(session_id: str, table_name: str, output_path: str) -> str:
    try:
        path = services.export_arrow(session_id, table_name, output_path)
        return _ok("export_arrow", table_name=table_name, output_path=path)
    except (KeyError, ValueError) as exc:
        return _err("export_arrow", "NOT_FOUND", str(exc))
    except Exception as exc:
        return _err("export_arrow", "EXPORT_FAILED", str(exc))


def export_feather(session_id: str, table_name: str, output_path: str) -> str:
    try:
        path = services.export_feather(session_id, table_name, output_path)
        return _ok("export_feather", table_name=table_name, output_path=path)
    except (KeyError, ValueError) as exc:
        return _err("export_feather", "NOT_FOUND", str(exc))
    except Exception as exc:
        return _err("export_feather", "EXPORT_FAILED", str(exc))


def export_json(
    session_id: str,
    output_path: str,
    include_data: bool = True,
) -> str:
    try:
        path = services.export_json(session_id, output_path, include_data=include_data)
        return _ok("export_json", output_path=path, include_data=include_data)
    except KeyError as exc:
        return _err("export_json", "NOT_FOUND", str(exc))
    except Exception as exc:
        return _err("export_json", "EXPORT_FAILED", str(exc))
