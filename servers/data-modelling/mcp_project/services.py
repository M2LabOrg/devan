"""Core business logic for the data-modelling MCP server.

Responsibilities
----------------
* Session lifecycle (create / get / list / delete)
* Data ingestion from files — see SUPPORTED_EXTENSIONS for the full list —
  and from inline text (auto-detected format) or Python dicts/lists
* Schema inference: column types, PK candidates, uniqueness, nullability
* Relationship detection: name heuristics + value-set overlap + cardinality
* Model manipulation: rename, retype, manual FK wiring
* Export: SQLite3, Arrow (.arrow), Feather (.feather), JSON
"""

from __future__ import annotations

import json
import re
import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd

from extractors import normalize_to_frames
from models import ColumnModel, DataModelSession, Relationship, TableModel

# Keep the old name available for internal callers
_normalize_json_to_frames = normalize_to_frames

# ---------------------------------------------------------------------------
# In-memory stores
# ---------------------------------------------------------------------------

_sessions: Dict[str, DataModelSession] = {}
_dataframes: Dict[str, Dict[str, pd.DataFrame]] = {}

# ---------------------------------------------------------------------------
# Supported extensions (for documentation / error messages)
# ---------------------------------------------------------------------------

SUPPORTED_EXTENSIONS = (
    # Tabular
    ".csv", ".tsv", ".txt",
    # Spreadsheet
    ".xls", ".xlsx", ".xlsm", ".xlsb", ".ods",
    # Semi-structured
    ".json", ".jsonl",
    ".yaml", ".yml",
    ".toml",
    ".xml",
    ".html", ".htm",
    # Document
    ".docx",
    ".pptx", ".ppt",
    # Markdown
    ".md", ".markdown",
    # Columnar
    ".parquet", ".feather", ".arrow",
)

# ---------------------------------------------------------------------------
# Schema inference helpers
# ---------------------------------------------------------------------------

_PANDAS_TO_SQLITE: Dict[str, str] = {
    "object": "text",
    "string": "text",
    "int8": "integer",  "int16": "integer",  "int32": "integer",  "int64": "integer",
    "uint8": "integer", "uint16": "integer", "uint32": "integer", "uint64": "integer",
    "float16": "real",  "float32": "real",   "float64": "real",
    "bool": "boolean",  "boolean": "boolean",
    "datetime64[ns]": "datetime", "datetime64[us]": "datetime",
    "date": "date",
    "timedelta64[ns]": "text",
    "category": "text",
}


def _pandas_dtype_to_sqlite(dtype) -> str:
    s = str(dtype)
    if s in _PANDAS_TO_SQLITE:
        return _PANDAS_TO_SQLITE[s]
    if s.startswith("datetime"):
        return "datetime"
    if s.startswith("int") or s.startswith("uint"):
        return "integer"
    if s.startswith("float"):
        return "real"
    return "text"


def _infer_schema(
    df: pd.DataFrame,
    table_name: str,
    source_file: Optional[str] = None,
    source_sheet: Optional[str] = None,
) -> TableModel:
    table = TableModel(
        name=table_name,
        row_count=len(df),
        source_file=source_file,
        source_sheet=source_sheet,
    )
    for col_name in df.columns:
        series = df[col_name]
        dtype = _pandas_dtype_to_sqlite(series.dtype)
        null_count = int(series.isna().sum())
        non_null = series.dropna()
        cardinality = int(non_null.nunique())
        is_unique = cardinality == len(non_null) and len(non_null) > 0
        samples = non_null.drop_duplicates().head(5).tolist() if len(non_null) > 0 else []

        col = ColumnModel(
            name=str(col_name),
            dtype=dtype,
            nullable=null_count > 0,
            unique=is_unique,
            null_count=null_count,
            cardinality=cardinality,
            sample_values=samples,
        )
        table.columns[str(col_name)] = col

    _assign_primary_key(df, table)
    return table


def _assign_primary_key(df: pd.DataFrame, table: TableModel) -> None:
    lower_map = {c.lower(): c for c in table.columns}

    # 1. Column literally named "id"
    if "id" in lower_map and table.columns[lower_map["id"]].unique:
        table.columns[lower_map["id"]].primary_key = True
        return

    # 2. "<table>_id" or "<table>id"
    for suffix in (f"{table.name.lower()}_id", f"{table.name.lower()}id"):
        if suffix in lower_map and table.columns[lower_map[suffix]].unique:
            table.columns[lower_map[suffix]].primary_key = True
            return

    # 3. Any unique, non-null integer column
    for col in table.columns.values():
        if col.unique and not col.nullable and col.dtype == "integer":
            col.primary_key = True
            return

    # 4. Any unique, non-null column
    for col in table.columns.values():
        if col.unique and not col.nullable:
            col.primary_key = True
            return


# ---------------------------------------------------------------------------
# Session-level frame helper
# ---------------------------------------------------------------------------

def _add_frames_to_session(
    session: DataModelSession,
    session_id: str,
    frames: Dict[str, pd.DataFrame],
    source_file: Optional[str] = None,
    source_sheet: Optional[str] = None,
) -> List[TableModel]:
    """Register a dict of DataFrames into a session. Returns added TableModels."""
    added: List[TableModel] = []
    for key, df in frames.items():
        if df is None or df.empty:
            continue
        df = df.reset_index(drop=True).copy()
        df.columns = [str(c).strip() for c in df.columns]
        tname = _unique_table_name(session, key)
        _dataframes[session_id][tname] = df
        model = _infer_schema(df, tname, source_file, source_sheet)
        session.tables[tname] = model
        added.append(model)
    return added


def _unique_table_name(session: DataModelSession, desired: str) -> str:
    name = re.sub(r"[^A-Za-z0-9_]", "_", desired).strip("_") or "table"
    if name not in session.tables:
        return name
    i = 2
    while f"{name}_{i}" in session.tables:
        i += 1
    return f"{name}_{i}"


# ---------------------------------------------------------------------------
# Session management
# ---------------------------------------------------------------------------

def create_session(name: str) -> DataModelSession:
    session = DataModelSession.create(name)
    _sessions[session.session_id] = session
    _dataframes[session.session_id] = {}
    return session


def get_session(session_id: str) -> DataModelSession:
    if session_id not in _sessions:
        raise KeyError(f"Session not found: {session_id!r}")
    return _sessions[session_id]


def list_sessions() -> List[DataModelSession]:
    return list(_sessions.values())


def delete_session(session_id: str) -> None:
    if session_id not in _sessions:
        raise KeyError(f"Session not found: {session_id!r}")
    del _sessions[session_id]
    _dataframes.pop(session_id, None)


# ---------------------------------------------------------------------------
# Data ingestion — files
# ---------------------------------------------------------------------------

def ingest_file(
    session_id: str,
    file_path: str,
    table_name: Optional[str] = None,
) -> List[TableModel]:
    """
    Load a file into the session.  The format is determined by the file
    extension.  Returns the list of TableModels that were added.

    See SUPPORTED_EXTENSIONS for all recognised formats.
    """
    session = get_session(session_id)
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path!r}")

    ext = path.suffix.lower()
    stem = path.stem
    frames: Dict[str, pd.DataFrame] = {}

    # ---- Spreadsheets (multi-sheet) ----
    if ext in (".xls", ".xlsx", ".xlsm", ".xlsb", ".ods"):
        xl = pd.ExcelFile(file_path)
        for sheet in xl.sheet_names:
            df = xl.parse(sheet)
            if not df.empty:
                key = f"{table_name or stem}_{sheet}"
                frames[key] = df

    # ---- JSON ----
    elif ext == ".json":
        with open(file_path, encoding="utf-8") as fh:
            raw = json.load(fh)
        frames = normalize_to_frames(raw)
        if table_name and len(frames) == 1:
            frames = {table_name: next(iter(frames.values()))}

    # ---- JSONL ----
    elif ext == ".jsonl":
        df = pd.read_json(file_path, lines=True)
        frames = {table_name or stem: df}

    # ---- CSV / TSV / auto-delimited text ----
    elif ext in (".csv", ".tsv", ".txt"):
        sep = "\t" if ext == ".tsv" else None
        kwargs: Dict[str, Any] = {"engine": "python"}
        if sep is not None:
            kwargs["sep"] = sep
        else:
            kwargs["sep"] = None
        df = pd.read_csv(file_path, **kwargs)
        frames = {table_name or stem: df}

    # ---- Columnar formats ----
    elif ext == ".parquet":
        frames = {table_name or stem: pd.read_parquet(file_path)}

    elif ext in (".feather", ".arrow"):
        frames = {table_name or stem: pd.read_feather(file_path)}

    # ---- Word ----
    elif ext == ".docx":
        from extractors import extract_docx
        frames = extract_docx(file_path)
        if table_name:
            frames = _prefix_keys(frames, table_name)

    # ---- PowerPoint ----
    elif ext in (".pptx", ".ppt"):
        from extractors import extract_pptx
        frames = extract_pptx(file_path)
        if table_name:
            frames = _prefix_keys(frames, table_name)

    # ---- Markdown ----
    elif ext in (".md", ".markdown"):
        from extractors import extract_markdown
        frames = extract_markdown(path.read_text(encoding="utf-8"))
        if table_name:
            frames = _prefix_keys(frames, table_name)

    # ---- YAML ----
    elif ext in (".yaml", ".yml"):
        from extractors import extract_yaml
        frames = extract_yaml(file_path)
        if table_name and len(frames) == 1:
            frames = {table_name: next(iter(frames.values()))}

    # ---- TOML ----
    elif ext == ".toml":
        from extractors import extract_toml
        frames = extract_toml(file_path)

    # ---- XML ----
    elif ext == ".xml":
        from extractors import extract_xml
        frames = extract_xml(file_path)

    # ---- HTML ----
    elif ext in (".html", ".htm"):
        from extractors import extract_html
        frames = extract_html(file_path)

    else:
        raise ValueError(
            f"Unsupported extension {ext!r}. "
            f"Supported: {' '.join(sorted(SUPPORTED_EXTENSIONS))}"
        )

    if not frames:
        raise ValueError(f"File loaded but produced no usable data: {file_path!r}")

    added = _add_frames_to_session(session, session_id, frames, str(path))

    if str(path) not in session.source_files:
        session.source_files.append(str(path))
    session.touch()
    return added


def _prefix_keys(
    frames: Dict[str, pd.DataFrame], prefix: str
) -> Dict[str, pd.DataFrame]:
    if len(frames) == 1:
        return {prefix: next(iter(frames.values()))}
    return {f"{prefix}_{k}": v for k, v in frames.items()}


# ---------------------------------------------------------------------------
# Data ingestion — inline data
# ---------------------------------------------------------------------------

def ingest_json_data(
    session_id: str,
    data: Any,
    table_name: str = "data",
) -> List[TableModel]:
    """
    Ingest an already-parsed Python object (dict / list) into the session.
    Nested structures are normalised into multiple tables automatically.
    """
    session = get_session(session_id)
    frames = normalize_to_frames(data)
    if len(frames) == 1:
        frames = {table_name: next(iter(frames.values()))}
    elif len(frames) > 1:
        frames = {f"{table_name}_{k}": v for k, v in frames.items()}

    added = _add_frames_to_session(session, session_id, frames)
    session.touch()
    return added


def ingest_text(
    session_id: str,
    text: str,
    table_name: str = "data",
    hint: str = "auto",
) -> Tuple[List[TableModel], str]:
    """
    Ingest raw pasted text into the session with automatic format detection.

    Returns (added_tables, detected_format).

    Supported auto-detected formats:
      JSON, YAML, HTML tables, Markdown tables, CSV, TSV, key-value blocks,
      plain lines.

    hint can force: auto | json | yaml | csv | tsv | delimited |
                    markdown | html | key-value | plain
    """
    from extractors import detect_and_extract_text

    session = get_session(session_id)
    frames, detected = detect_and_extract_text(text, hint=hint)

    if not frames:
        return [], detected

    # Apply the caller-supplied name as prefix/override
    if table_name != "data":
        frames = _prefix_keys(frames, table_name)

    added = _add_frames_to_session(session, session_id, frames)
    session.touch()
    return added, detected


# ---------------------------------------------------------------------------
# Relationship detection
# ---------------------------------------------------------------------------

def detect_relationships(session_id: str) -> List[Relationship]:
    """
    Auto-detect FK relationships using:
    1. Name heuristics  — columns named <X>_id matched against tables named <X>
    2. Value-set overlap — ≥60 % subset match against another table's PK values

    Previously auto-detected relationships (confidence < 1.0) are replaced.
    Manually added ones (confidence = 1.0) are preserved.
    """
    session = get_session(session_id)
    dfs = _dataframes.get(session_id, {})

    kept = [r for r in session.relationships if r.confidence == 1.0]
    found: List[Relationship] = []

    for tname, table in session.tables.items():
        df_from = dfs.get(tname)
        for col_name, col in table.columns.items():
            if col.primary_key:
                continue
            low = col_name.lower()
            if not (low.endswith("_id") or low.endswith("id")):
                continue

            # Strategy 1: name match
            cand = _name_candidate(col_name, list(session.tables), tname)
            if cand:
                to_col = _pk_column(session.tables[cand])
                if to_col and df_from is not None:
                    rel_type = _classify(df_from, col_name, dfs.get(cand), to_col)
                    found.append(
                        Relationship(
                            from_table=tname, from_column=col_name,
                            to_table=cand, to_column=to_col,
                            relationship_type=rel_type, confidence=0.85,
                        )
                    )
                    col.foreign_key = f"{cand}.{to_col}"
                    continue

            # Strategy 2: value-set overlap
            if df_from is None or col_name not in df_from.columns:
                continue
            from_vals = set(df_from[col_name].dropna().unique())
            if not from_vals:
                continue

            best_score = 0.0
            best_match: Optional[Tuple[str, str]] = None
            for other_name, other_table in session.tables.items():
                if other_name == tname:
                    continue
                other_pk = _pk_column(other_table)
                if not other_pk:
                    continue
                df_other = dfs.get(other_name)
                if df_other is None or other_pk not in df_other.columns:
                    continue
                other_vals = set(df_other[other_pk].dropna().unique())
                if not other_vals:
                    continue
                overlap = len(from_vals & other_vals) / len(from_vals)
                if overlap >= 0.6 and overlap > best_score:
                    best_score = overlap
                    best_match = (other_name, other_pk)

            if best_match:
                to_table, to_col = best_match
                rel_type = _classify(df_from, col_name, dfs.get(to_table), to_col)
                found.append(
                    Relationship(
                        from_table=tname, from_column=col_name,
                        to_table=to_table, to_column=to_col,
                        relationship_type=rel_type,
                        confidence=round(best_score * 0.75, 3),
                    )
                )
                col.foreign_key = f"{to_table}.{to_col}"

    session.relationships = kept + found
    session.touch()
    return found


def _name_candidate(col: str, table_names: List[str], exclude: str) -> Optional[str]:
    base = re.sub(r"[_\-]?id$", "", col, flags=re.IGNORECASE).lower().strip("_")
    if not base:
        return None
    for variant in (base, base + "s", base.rstrip("s"), base + "es"):
        for t in table_names:
            if t.lower() == variant and t != exclude:
                return t
    return None


def _pk_column(table: TableModel) -> Optional[str]:
    for col in table.columns.values():
        if col.primary_key:
            return col.name
    return None


def _classify(
    df_from: Optional[pd.DataFrame], from_col: str,
    df_to: Optional[pd.DataFrame], to_col: str,
) -> str:
    if df_from is None or df_to is None:
        return "many-to-one"
    from_u = df_from[from_col].nunique() == len(df_from[from_col].dropna())
    to_u = df_to[to_col].nunique() == len(df_to[to_col].dropna())
    if from_u and to_u:
        return "one-to-one"
    if from_u:
        return "one-to-many"
    return "many-to-one"


# ---------------------------------------------------------------------------
# Model manipulation
# ---------------------------------------------------------------------------

def add_relationship(
    session_id: str,
    from_table: str, from_column: str,
    to_table: str, to_column: str,
    relationship_type: str = "many-to-one",
) -> Relationship:
    session = get_session(session_id)
    for t, c in [(from_table, from_column), (to_table, to_column)]:
        if t not in session.tables:
            raise KeyError(f"Table not found: {t!r}")
        if c not in session.tables[t].columns:
            raise KeyError(f"Column not found: {t!r}.{c!r}")

    rel = Relationship(
        from_table=from_table, from_column=from_column,
        to_table=to_table, to_column=to_column,
        relationship_type=relationship_type, confidence=1.0,
    )
    session.tables[from_table].columns[from_column].foreign_key = f"{to_table}.{to_column}"
    session.relationships.append(rel)
    session.touch()
    return rel


def remove_relationship(session_id: str, from_table: str, from_column: str) -> int:
    session = get_session(session_id)
    before = len(session.relationships)
    session.relationships = [
        r for r in session.relationships
        if not (r.from_table == from_table and r.from_column == from_column)
    ]
    removed = before - len(session.relationships)
    tbl = session.tables.get(from_table)
    if removed and tbl and from_column in tbl.columns:
        tbl.columns[from_column].foreign_key = None
    session.touch()
    return removed


def rename_table(session_id: str, old_name: str, new_name: str) -> None:
    session = get_session(session_id)
    if old_name not in session.tables:
        raise KeyError(f"Table not found: {old_name!r}")
    safe = re.sub(r"[^A-Za-z0-9_]", "_", new_name).strip("_")
    if safe in session.tables:
        raise ValueError(f"Table {safe!r} already exists.")

    session.tables[safe] = session.tables.pop(old_name)
    session.tables[safe].name = safe

    if old_name in _dataframes.get(session_id, {}):
        _dataframes[session_id][safe] = _dataframes[session_id].pop(old_name)

    for rel in session.relationships:
        if rel.from_table == old_name:
            rel.from_table = safe
        if rel.to_table == old_name:
            rel.to_table = safe

    for table in session.tables.values():
        for col in table.columns.values():
            if col.foreign_key and col.foreign_key.startswith(f"{old_name}."):
                col.foreign_key = col.foreign_key.replace(f"{old_name}.", f"{safe}.", 1)

    session.touch()


def rename_column(
    session_id: str, table_name: str, old_name: str, new_name: str
) -> None:
    session = get_session(session_id)
    if table_name not in session.tables:
        raise KeyError(f"Table not found: {table_name!r}")
    table = session.tables[table_name]
    if old_name not in table.columns:
        raise KeyError(f"Column not found: {table_name!r}.{old_name!r}")

    safe = re.sub(r"[^A-Za-z0-9_]", "_", new_name).strip("_")
    table.columns = {(safe if k == old_name else k): v for k, v in table.columns.items()}
    table.columns[safe].name = safe

    df = _dataframes.get(session_id, {}).get(table_name)
    if df is not None and old_name in df.columns:
        _dataframes[session_id][table_name] = df.rename(columns={old_name: safe})

    session.touch()


def set_primary_key(session_id: str, table_name: str, columns: List[str]) -> None:
    session = get_session(session_id)
    if table_name not in session.tables:
        raise KeyError(f"Table not found: {table_name!r}")
    table = session.tables[table_name]
    for c in columns:
        if c not in table.columns:
            raise KeyError(f"Column not found: {table_name!r}.{c!r}")
    for col in table.columns.values():
        col.primary_key = col.name in columns
    session.touch()


def set_column_type(
    session_id: str, table_name: str, column_name: str, dtype: str
) -> None:
    valid = {"text", "integer", "real", "boolean", "date", "datetime", "blob"}
    if dtype not in valid:
        raise ValueError(f"dtype must be one of {sorted(valid)}, got {dtype!r}")
    session = get_session(session_id)
    if table_name not in session.tables:
        raise KeyError(f"Table not found: {table_name!r}")
    if column_name not in session.tables[table_name].columns:
        raise KeyError(f"Column not found: {table_name!r}.{column_name!r}")
    session.tables[table_name].columns[column_name].dtype = dtype
    session.touch()


def set_notes(session_id: str, notes: str) -> None:
    session = get_session(session_id)
    session.notes = notes
    session.touch()


# ---------------------------------------------------------------------------
# Export
# ---------------------------------------------------------------------------

_SQLITE_TYPE_MAP = {
    "text": "TEXT", "integer": "INTEGER", "real": "REAL",
    "boolean": "INTEGER", "date": "TEXT", "datetime": "TEXT", "blob": "BLOB",
}


def export_sqlite(session_id: str, output_path: str) -> str:
    session = get_session(session_id)
    dfs = _dataframes.get(session_id, {})

    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)

    con = sqlite3.connect(str(out))
    try:
        for tname, table in session.tables.items():
            df = dfs.get(tname)
            if df is None or df.empty:
                cols_ddl = ", ".join(_col_ddl(c) for c in table.columns.values())
                con.execute(f'CREATE TABLE IF NOT EXISTS "{tname}" ({cols_ddl})')
            else:
                df.to_sql(tname, con, if_exists="replace", index=False)

        if session.relationships:
            pd.DataFrame([r.to_dict() for r in session.relationships]).to_sql(
                "_schema_relationships", con, if_exists="replace", index=False
            )

        schema_rows = [
            {
                "table_name": tname, "column_name": col.name,
                "dtype": col.dtype, "nullable": col.nullable,
                "unique": col.unique, "primary_key": col.primary_key,
                "foreign_key": col.foreign_key or "",
            }
            for tname, table in session.tables.items()
            for col in table.columns.values()
        ]
        if schema_rows:
            pd.DataFrame(schema_rows).to_sql(
                "_schema_columns", con, if_exists="replace", index=False
            )

        con.commit()
    finally:
        con.close()

    return str(out.resolve())


def _col_ddl(col: ColumnModel) -> str:
    sql_type = _SQLITE_TYPE_MAP.get(col.dtype, "TEXT")
    parts = [f'"{col.name}" {sql_type}']
    if col.primary_key:
        parts.append("PRIMARY KEY")
    if not col.nullable:
        parts.append("NOT NULL")
    if col.unique and not col.primary_key:
        parts.append("UNIQUE")
    return " ".join(parts)


def export_arrow(session_id: str, table_name: str, output_path: str) -> str:
    import pyarrow as pa
    import pyarrow.ipc as ipc

    _check_table(session_id, table_name)
    df = _get_df(session_id, table_name)
    table = pa.Table.from_pandas(df, preserve_index=False)
    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    with ipc.new_file(str(out), table.schema) as w:
        w.write(table)
    return str(out.resolve())


def export_feather(session_id: str, table_name: str, output_path: str) -> str:
    import pyarrow.feather as feather

    _check_table(session_id, table_name)
    df = _get_df(session_id, table_name)
    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    feather.write_feather(df, str(out))
    return str(out.resolve())


def export_json(
    session_id: str,
    output_path: str,
    include_data: bool = True,
    indent: int = 2,
) -> str:
    session = get_session(session_id)
    dfs = _dataframes.get(session_id, {})

    payload: Dict[str, Any] = {
        "session": {
            "session_id": session.session_id, "name": session.name,
            "created_at": session.created_at, "updated_at": session.updated_at,
            "source_files": session.source_files, "notes": session.notes,
        },
        "relationships": [r.to_dict() for r in session.relationships],
        "tables": {},
    }

    for tname, table in session.tables.items():
        entry: Dict[str, Any] = {"schema": table.to_dict()}
        if include_data:
            df = dfs.get(tname)
            entry["data"] = (
                json.loads(df.to_json(orient="records", date_format="iso", default_handler=str))
                if df is not None and not df.empty
                else []
            )
        payload["tables"][tname] = entry

    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(str(out), "w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=indent, default=str)

    return str(out.resolve())


def _check_table(session_id: str, table_name: str) -> None:
    session = get_session(session_id)
    if table_name not in session.tables:
        raise KeyError(f"Table not found: {table_name!r}")


def _get_df(session_id: str, table_name: str) -> pd.DataFrame:
    df = _dataframes.get(session_id, {}).get(table_name)
    if df is None:
        raise ValueError(f"No data loaded for table {table_name!r}")
    return df
