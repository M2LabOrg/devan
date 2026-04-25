"""Data Modelling MCP Server.

Transforms structured or semi-structured data (CSV, TSV, Excel, JSON, Parquet,
Feather) into a well-defined relational data model with proper tables, columns,
primary keys, and foreign-key relationships, then exports the result to SQLite3,
Arrow (.arrow), Feather (.feather), and/or JSON.

Typical workflow
----------------
1. create_session        — start a named modelling session
2. ingest_file           — load one or more source files (multiple calls OK)
3. detect_relationships  — auto-detect FK links between tables
4. inspect_session       — review the inferred schema
5. [optional] rename/retype/set_primary_key — refine the model
6. export_sqlite / export_arrow / export_feather / export_json — persist
"""

from mcp.server.fastmcp import FastMCP

import tools

mcp = FastMCP("data-modelling-mcp")


# ---------------------------------------------------------------------------
# Session management
# ---------------------------------------------------------------------------


@mcp.tool()
def create_session(name: str) -> str:
    """
    Create a new data-modelling session.

    Args:
        name: Human-readable label for the session (e.g. "sales_q1_2024").

    Returns:
        JSON with session_id and initial metadata.
    """
    return tools.create_session(name)


@mcp.tool()
def list_sessions() -> str:
    """
    List all active modelling sessions with their table names and status.

    Returns:
        JSON array of session summaries.
    """
    return tools.list_sessions()


@mcp.tool()
def inspect_session(session_id: str) -> str:
    """
    Return the full schema of a session: all tables, columns (with inferred
    types, nullability, uniqueness, PK/FK flags, sample values), and all
    detected or manually defined relationships.

    Args:
        session_id: ID returned by create_session.

    Returns:
        JSON with complete session schema.
    """
    return tools.inspect_session(session_id)


@mcp.tool()
def delete_session(session_id: str) -> str:
    """
    Delete a session and free its in-memory data.

    Args:
        session_id: ID of the session to remove.

    Returns:
        JSON confirmation.
    """
    return tools.delete_session(session_id)


# ---------------------------------------------------------------------------
# Data ingestion
# ---------------------------------------------------------------------------


@mcp.tool()
def ingest_file(
    session_id: str,
    file_path: str,
    table_name: str = "",
) -> str:
    """
    Load a data file into the session and infer its schema.

    Supported formats
    -----------------
    Tabular:      .csv  .tsv  .txt (delimiter auto-detected)
    Spreadsheet:  .xls  .xlsx  .xlsm  .xlsb  .ods
                  (each non-empty sheet becomes a separate table)
    Documents:    .docx — tables, key-value paragraphs, lists, content
                  .pptx — per-slide table with title/body/notes +
                          any embedded table shapes
    Markup:       .md / .markdown — pipe tables, YAML front-matter, sections
                  .html / .htm   — all <table> elements
                  .xml           — flat or nested, normalised into tables
    Data:         .json          — nested objects/arrays → separate tables
                  .jsonl         — newline-delimited JSON records
                  .yaml / .yml   — normalised like JSON
                  .toml          — normalised like JSON
    Columnar:     .parquet  .feather  .arrow

    Args:
        session_id: Target session ID.
        file_path:  Absolute path to the file.
        table_name: Override the auto-generated table name.
                    For multi-table formats (Excel, DOCX, etc.) this becomes
                    a prefix combined with the sheet/table name.

    Returns:
        JSON listing all tables added with their inferred schema.
    """
    return tools.ingest_file(session_id, file_path, table_name or None)


@mcp.tool()
def ingest_json_data(
    session_id: str,
    data: str,
    table_name: str = "data",
) -> str:
    """
    Ingest an inline JSON string into the session.

    Nested JSON is automatically normalised:
    * ``[{...}, ...]``          → one table named table_name
    * ``{"key": [{...}], ...}`` → one table per top-level key
    * ``{...}``                 → single-row table

    Args:
        session_id: Target session ID.
        data:       JSON string (object or array).
        table_name: Base name for generated tables.

    Returns:
        JSON listing tables added with their inferred schema.
    """
    import json as _json
    try:
        parsed = _json.loads(data)
    except Exception as exc:
        import json as j
        return j.dumps({"status": "error", "tool": "ingest_json_data",
                        "error": {"code": "INVALID_JSON", "message": str(exc)}})
    return tools.ingest_json_data(session_id, parsed, table_name)


@mcp.tool()
def ingest_text(
    session_id: str,
    text: str,
    table_name: str = "data",
    hint: str = "auto",
) -> str:
    """
    Ingest raw pasted or inline text into the session with automatic format
    detection.  This is the most flexible ingestion tool — it handles whatever
    the user pastes, copies from a spreadsheet, or dumps from a terminal.

    Auto-detected formats (in priority order)
    -----------------------------------------
    * JSON           — objects or arrays, including nested/API responses
    * YAML           — including front-matter blocks (---)
    * HTML           — extracts all <table> elements
    * Markdown       — pipe tables (|col|col|) and heading-structured sections
    * CSV / TSV      — comma, tab, semicolon delimiters
    * Key-Value      — "Key: Value" or "Key = Value" line patterns
    * Plain text     — stored as a two-column table (line_number, text)

    hint parameter
    --------------
    Set hint to override auto-detection:
    auto | json | yaml | csv | tsv | delimited | markdown | html | key-value | plain

    Args:
        session_id: Target session ID.
        text:       The raw text to ingest (any format).
        table_name: Base name for generated tables.
        hint:       Optional format hint to skip auto-detection.

    Returns:
        JSON with detected_format and list of tables added with their schema.
    """
    return tools.ingest_text(session_id, text, table_name, hint)


# ---------------------------------------------------------------------------
# Relationship detection & management
# ---------------------------------------------------------------------------


@mcp.tool()
def detect_relationships(session_id: str) -> str:
    """
    Auto-detect foreign-key relationships between tables using two strategies:

    1. **Name heuristics** — a column called ``customer_id`` is matched to a
       table called ``customer`` or ``customers`` that has a primary key.
    2. **Value-set overlap** — columns whose values are ≥ 60 % a subset of
       another table's primary-key values are linked automatically.

    Confidence scores are attached to each detected relationship.
    Previously auto-detected relationships are replaced; manually added ones
    (confidence = 1.0) are preserved.

    Args:
        session_id: Target session ID.

    Returns:
        JSON listing detected relationships with confidence scores.
    """
    return tools.detect_relationships(session_id)


@mcp.tool()
def add_relationship(
    session_id: str,
    from_table: str,
    from_column: str,
    to_table: str,
    to_column: str,
    relationship_type: str = "many-to-one",
) -> str:
    """
    Manually define a foreign-key relationship between two columns.

    Args:
        session_id:        Target session ID.
        from_table:        Table that holds the FK column.
        from_column:       FK column in from_table.
        to_table:          Referenced table.
        to_column:         Referenced column in to_table (usually the PK).
        relationship_type: one-to-one | one-to-many | many-to-one | many-to-many

    Returns:
        JSON with the added relationship definition.
    """
    return tools.add_relationship(
        session_id, from_table, from_column, to_table, to_column, relationship_type
    )


@mcp.tool()
def remove_relationship(
    session_id: str,
    from_table: str,
    from_column: str,
) -> str:
    """
    Remove all FK relationships originating from from_table.from_column.

    Args:
        session_id:  Target session ID.
        from_table:  Table whose FK you want to remove.
        from_column: Column whose FK annotation should be cleared.

    Returns:
        JSON with number of relationships removed.
    """
    return tools.remove_relationship(session_id, from_table, from_column)


# ---------------------------------------------------------------------------
# Model refinement
# ---------------------------------------------------------------------------


@mcp.tool()
def rename_table(session_id: str, old_name: str, new_name: str) -> str:
    """
    Rename a table within the session (updates relationship references too).

    Args:
        session_id: Target session ID.
        old_name:   Current table name.
        new_name:   Desired new name (non-alphanumeric characters are replaced
                    with underscores).

    Returns:
        JSON confirmation.
    """
    return tools.rename_table(session_id, old_name, new_name)


@mcp.tool()
def rename_column(
    session_id: str,
    table_name: str,
    old_name: str,
    new_name: str,
) -> str:
    """
    Rename a column within a table (updates the underlying DataFrame too).

    Args:
        session_id: Target session ID.
        table_name: Table containing the column.
        old_name:   Current column name.
        new_name:   Desired new name.

    Returns:
        JSON confirmation.
    """
    return tools.rename_column(session_id, table_name, old_name, new_name)


@mcp.tool()
def set_primary_key(session_id: str, table_name: str, columns: list) -> str:
    """
    Explicitly set the primary key column(s) for a table, overriding the
    auto-detected candidate.

    Args:
        session_id: Target session ID.
        table_name: Table to modify.
        columns:    List of column names that form the primary key.

    Returns:
        JSON confirmation.
    """
    return tools.set_primary_key(session_id, table_name, columns)


@mcp.tool()
def set_column_type(
    session_id: str,
    table_name: str,
    column_name: str,
    dtype: str,
) -> str:
    """
    Override the inferred data type for a column.

    Valid types: text | integer | real | boolean | date | datetime | blob

    Args:
        session_id:  Target session ID.
        table_name:  Table containing the column.
        column_name: Column to retype.
        dtype:       New type string.

    Returns:
        JSON confirmation.
    """
    return tools.set_column_type(session_id, table_name, column_name, dtype)


@mcp.tool()
def set_notes(session_id: str, notes: str) -> str:
    """
    Attach free-text notes / documentation to a session.

    Args:
        session_id: Target session ID.
        notes:      Markdown or plain text.

    Returns:
        JSON confirmation.
    """
    return tools.set_notes(session_id, notes)


# ---------------------------------------------------------------------------
# Export
# ---------------------------------------------------------------------------


@mcp.tool()
def export_sqlite(session_id: str, output_path: str) -> str:
    """
    Export the entire session to a SQLite3 database file.

    All tables are written as SQL tables.  Two extra metadata tables are
    included automatically:
    * ``_schema_columns``       — column-level schema info
    * ``_schema_relationships`` — FK relationship manifest

    Args:
        session_id:  Source session ID.
        output_path: Absolute path for the .sqlite / .db file.
                     Parent directories are created if necessary.

    Returns:
        JSON with the resolved output path and table list.
    """
    return tools.export_sqlite(session_id, output_path)


@mcp.tool()
def export_arrow(session_id: str, table_name: str, output_path: str) -> str:
    """
    Export a single table as an Arrow IPC file (.arrow).

    Arrow IPC is a column-oriented binary format ideal for high-performance
    data exchange with other Arrow-compatible tools (DuckDB, Polars, etc.).

    Args:
        session_id:  Source session ID.
        table_name:  Name of the table to export.
        output_path: Absolute path for the .arrow file.

    Returns:
        JSON with the resolved output path.
    """
    return tools.export_arrow(session_id, table_name, output_path)


@mcp.tool()
def export_feather(session_id: str, table_name: str, output_path: str) -> str:
    """
    Export a single table as a Feather v2 file (.feather).

    Feather is optimised for fast local read/write and is natively supported
    by pandas, Polars, and R's arrow package.

    Args:
        session_id:  Source session ID.
        table_name:  Name of the table to export.
        output_path: Absolute path for the .feather file.

    Returns:
        JSON with the resolved output path.
    """
    return tools.export_feather(session_id, table_name, output_path)


@mcp.tool()
def export_json(
    session_id: str,
    output_path: str,
    include_data: bool = True,
) -> str:
    """
    Export the session schema and (optionally) all table data as JSON.

    Output structure::

        {
          "session": { ...metadata... },
          "relationships": [ ...FK definitions... ],
          "tables": {
            "<table_name>": {
              "schema": { ...column definitions... },
              "data":   [ ...rows as objects... ]   // if include_data=true
            }
          }
        }

    Args:
        session_id:   Source session ID.
        output_path:  Absolute path for the .json file.
        include_data: Set to false to export schema only (no row data).

    Returns:
        JSON with the resolved output path.
    """
    return tools.export_json(session_id, output_path, include_data=include_data)


# ---------------------------------------------------------------------------
# Entrypoint
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    mcp.run()
