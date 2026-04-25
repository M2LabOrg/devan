"""
MCP Server for Intelligent Excel Data Extraction

This server provides tools to extract and query data from Excel files.
It handles complex real-world spreadsheets with:
- Multiple tables per sheet (auto-detected)
- Merged cells
- Instruction text / notes mixed with data
- Figures and charts (metadata extraction)
- Named ranges
- Export to CSV, JSON, Markdown, and Parquet

Uses both a custom smart extractor (openpyxl) and docling for robust extraction.
"""

import json
import os
import csv
import io
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
from mcp.server.fastmcp import FastMCP

# Smart extractor for intelligent table detection
from smart_extractor import (
    SmartExcelExtractor,
    analysis_to_dict,
    table_to_csv_string,
    table_to_markdown,
    table_to_records,
)

# Docling imports for Excel processing
try:
    from docling.document_converter import DocumentConverter
    from docling.datamodel.base_models import InputFormat
    from docling.datamodel.document import ConversionResult
    DOCLING_AVAILABLE = True
except ImportError:
    DOCLING_AVAILABLE = False
    print("Warning: docling not installed. Excel extraction will be limited.")


# Default directory for Excel files
EXCEL_DIR = os.environ.get("EXCEL_DIR", "excel_files")

# Initialize FastMCP server
mcp = FastMCP("excel-retriever")

# Initialize docling converter
_converter: Optional[DocumentConverter] = None

def get_converter() -> DocumentConverter:
    """Get or create the DocumentConverter instance."""
    global _converter
    if _converter is None:
        _converter = DocumentConverter()
    return _converter


@mcp.tool()
def list_excel_files(directory: Optional[str] = None) -> str:
    """
    List all Excel files (.xlsx, .xls) in the specified directory.
    
    Args:
        directory: Path to directory containing Excel files. 
                    Defaults to EXCEL_DIR environment variable or 'excel_files'.
        
    Returns:
        JSON string with list of Excel files and their metadata.
    """
    search_dir = directory or EXCEL_DIR
    
    if not os.path.exists(search_dir):
        return json.dumps({
            "error": f"Directory not found: {search_dir}",
            "hint": "Create the directory or set EXCEL_DIR environment variable"
        }, indent=2)
    
    excel_extensions = ['.xlsx', '.xls', '.xlsm', '.xlsb']
    files = []
    
    for item in os.listdir(search_dir):
        if any(item.lower().endswith(ext) for ext in excel_extensions):
            file_path = os.path.join(search_dir, item)
            try:
                stat = os.stat(file_path)
                files.append({
                    "filename": item,
                    "path": file_path,
                    "size_bytes": stat.st_size,
                    "modified": str(stat.st_mtime)
                })
            except OSError as e:
                files.append({
                    "filename": item,
                    "path": file_path,
                    "error": str(e)
                })
    
    return json.dumps({
        "directory": search_dir,
        "file_count": len(files),
        "files": files
    }, indent=2)


@mcp.tool()
def extract_excel_content(file_path: str, sheet_name: Optional[str] = None) -> str:
    """
    Extract content from an Excel file using docling.
    
    Args:
        file_path: Path to the Excel file
        sheet_name: Optional specific sheet to extract. If not provided,
                   extracts all sheets.
        
    Returns:
        JSON string with extracted content structured as tables and text.
    """
    if not DOCLING_AVAILABLE:
        return json.dumps({
            "error": "docling is not installed. Install with: uv add docling"
        }, indent=2)
    
    if not os.path.exists(file_path):
        return json.dumps({
            "error": f"File not found: {file_path}"
        }, indent=2)
    
    try:
        converter = get_converter()
        result = converter.convert(file_path)
        
        # Extract structured content
        extracted_data = {
            "file_path": file_path,
            "file_name": os.path.basename(file_path),
            "document_type": "excel",
            "pages": []
        }
        
        # Process each page (sheet in Excel context)
        for page in result.pages:
            page_data = {
                "page_number": page.page_no,
                "tables": [],
                "text_content": ""
            }
            
            # Extract tables
            for table in page.tables:
                table_data = {
                    "headers": table.header if hasattr(table, 'header') else [],
                    "rows": []
                }
                
                # Process table rows
                for row in table.data:
                    row_data = []
                    for cell in row:
                        cell_text = str(cell) if cell else ""
                        row_data.append(cell_text)
                    table_data["rows"].append(row_data)
                
                page_data["tables"].append(table_data)
            
            # Extract text content
            for item in page.items:
                if hasattr(item, 'text'):
                    page_data["text_content"] += item.text + "\n"
            
            extracted_data["pages"].append(page_data)
        
        # Also get the full text export
        extracted_data["full_text"] = result.document.export_to_text()
        extracted_data["markdown"] = result.document.export_to_markdown()
        
        return json.dumps(extracted_data, indent=2, default=str)
        
    except Exception as e:
        return json.dumps({
            "error": f"Failed to extract content: {str(e)}",
            "file_path": file_path
        }, indent=2)


@mcp.tool()
def query_excel_data(file_path: str, query: str) -> str:
    """
    Query specific information from an Excel file.
    This extracts the content and returns structured data that can be
    further processed by the LLM.
    
    Args:
        file_path: Path to the Excel file
        query: Description of what data to look for (e.g., "sales figures", 
               "employee names", "Q1 revenue")
        
    Returns:
        JSON string with relevant extracted data based on the query context.
    """
    if not DOCLING_AVAILABLE:
        return json.dumps({
            "error": "docling is not installed. Install with: uv add docling"
        }, indent=2)
    
    if not os.path.exists(file_path):
        return json.dumps({
            "error": f"File not found: {file_path}"
        }, indent=2)
    
    try:
        # First extract all content
        converter = get_converter()
        result = converter.convert(file_path)
        
        # Get structured data
        structured_data = {
            "query": query,
            "file": os.path.basename(file_path),
            "sheets": [],
            "tables": [],
            "key_values": []
        }
        
        # Process all pages/sheets
        for page in result.pages:
            sheet_info = {
                "sheet_number": page.page_no,
                "tables_found": len(page.tables),
                "text_segments": []
            }
            
            # Extract text segments
            for item in page.items:
                if hasattr(item, 'text'):
                    sheet_info["text_segments"].append(item.text)
            
            structured_data["sheets"].append(sheet_info)
            
            # Extract all tables
            for table in page.tables:
                table_rows = []
                for row in table.data:
                    row_cells = [str(cell) if cell else "" for cell in row]
                    table_rows.append(row_cells)
                
                structured_data["tables"].append({
                    "sheet": page.page_no,
                    "row_count": len(table_rows),
                    "data": table_rows[:50]  # Limit to first 50 rows
                })
        
        # Get full markdown for context
        structured_data["full_content_preview"] = result.document.export_to_markdown()[:5000]
        
        return json.dumps(structured_data, indent=2, default=str)
        
    except Exception as e:
        return json.dumps({
            "error": f"Failed to query data: {str(e)}",
            "file_path": file_path,
            "query": query
        }, indent=2)


@mcp.tool()
def get_excel_summary(file_path: str) -> str:
    """
    Get a summary of an Excel file's structure and content.
    
    Args:
        file_path: Path to the Excel file
        
    Returns:
        JSON string with summary information about sheets, tables, and data.
    """
    if not DOCLING_AVAILABLE:
        return json.dumps({
            "error": "docling is not installed. Install with: uv add docling"
        }, indent=2)
    
    if not os.path.exists(file_path):
        return json.dumps({
            "error": f"File not found: {file_path}"
        }, indent=2)
    
    try:
        converter = get_converter()
        result = converter.convert(file_path)
        
        summary = {
            "file_name": os.path.basename(file_path),
            "file_path": file_path,
            "total_sheets": len(result.pages),
            "sheets": []
        }
        
        for page in result.pages:
            sheet_summary = {
                "sheet_number": page.page_no,
                "table_count": len(page.tables),
                "has_text": len(page.items) > 0,
                "tables": []
            }
            
            for i, table in enumerate(page.tables):
                row_count = len(table.data) if hasattr(table, 'data') else 0
                sheet_summary["tables"].append({
                    "table_index": i,
                    "row_count": row_count
                })
            
            summary["sheets"].append(sheet_summary)
        
        return json.dumps(summary, indent=2, default=str)
        
    except Exception as e:
        return json.dumps({
            "error": f"Failed to generate summary: {str(e)}",
            "file_path": file_path
        }, indent=2)


@mcp.tool()
def convert_excel_to_csv(file_path: str, output_dir: Optional[str] = None) -> str:
    """
    Convert Excel file sheets to CSV format.
    
    Args:
        file_path: Path to the Excel file
        output_dir: Optional directory to save CSV files. Defaults to same directory as Excel file.
        
    Returns:
        JSON string with paths to created CSV files.
    """
    if not DOCLING_AVAILABLE:
        return json.dumps({
            "error": "docling is not installed. Install with: uv add docling"
        }, indent=2)
    
    if not os.path.exists(file_path):
        return json.dumps({
            "error": f"File not found: {file_path}"
        }, indent=2)
    
    try:
        import pandas as pd
        
        # Determine output directory
        if output_dir is None:
            output_dir = os.path.dirname(file_path) or "."
        
        os.makedirs(output_dir, exist_ok=True)
        
        # Read all sheets
        excel_file = pd.ExcelFile(file_path)
        created_files = []
        
        base_name = Path(file_path).stem
        
        for sheet_name in excel_file.sheet_names:
            df = pd.read_excel(file_path, sheet_name=sheet_name)
            
            # Create safe filename
            safe_sheet = "".join(c if c.isalnum() else "_" for c in sheet_name)
            csv_filename = f"{base_name}_{safe_sheet}.csv"
            csv_path = os.path.join(output_dir, csv_filename)
            
            df.to_csv(csv_path, index=False)
            created_files.append({
                "sheet_name": sheet_name,
                "csv_path": csv_path,
                "rows": len(df),
                "columns": len(df.columns)
            })
        
        return json.dumps({
            "source_file": file_path,
            "output_directory": output_dir,
            "csv_files_created": len(created_files),
            "files": created_files
        }, indent=2)
        
    except ImportError:
        return json.dumps({
            "error": "pandas not installed. Install with: uv add pandas"
        }, indent=2)
    except Exception as e:
        return json.dumps({
            "error": f"Failed to convert to CSV: {str(e)}",
            "file_path": file_path
        }, indent=2)


@mcp.tool()
def convert_excel_to_json(file_path: str, output_dir: Optional[str] = None, include_metadata: bool = True) -> str:
    """
    Convert Excel file sheets to JSON format.
    
    Args:
        file_path: Path to the Excel file
        output_dir: Optional directory to save JSON files. Defaults to same directory as Excel file.
        include_metadata: Whether to include sheet metadata (default: True)
        
    Returns:
        JSON string with paths to created JSON files and inline data preview.
    """
    if not os.path.exists(file_path):
        return json.dumps({
            "error": f"File not found: {file_path}"
        }, indent=2)
    
    try:
        import pandas as pd
        
        # Determine output directory
        if output_dir is None:
            output_dir = os.path.dirname(file_path) or "."
        
        os.makedirs(output_dir, exist_ok=True)
        
        # Read all sheets
        excel_file = pd.ExcelFile(file_path)
        created_files = []
        all_data = {}
        
        base_name = Path(file_path).stem
        
        for sheet_name in excel_file.sheet_names:
            df = pd.read_excel(file_path, sheet_name=sheet_name)
            
            # Convert to records (list of dicts)
            records = df.replace({pd.NaT: None, pd.NA: None}).to_dict(orient='records')
            
            # Clean NaN values for JSON serialization
            clean_records = []
            for record in records:
                clean_record = {}
                for key, value in record.items():
                    if pd.isna(value):
                        clean_record[key] = None
                    elif isinstance(value, (pd.Timestamp, datetime)):
                        clean_record[key] = value.isoformat()
                    else:
                        clean_record[key] = value
                clean_records.append(clean_record)
            
            # Create JSON data structure
            sheet_data = {
                "sheet_name": sheet_name,
                "row_count": len(df),
                "column_count": len(df.columns),
                "columns": list(df.columns),
                "data": clean_records
            }
            
            if include_metadata:
                sheet_data["metadata"] = {
                    "source_file": os.path.basename(file_path),
                    "sheet_index": excel_file.sheet_names.index(sheet_name),
                    "dtypes": {col: str(df[col].dtype) for col in df.columns}
                }
            
            all_data[sheet_name] = sheet_data
            
            # Create safe filename
            safe_sheet = "".join(c if c.isalnum() else "_" for c in sheet_name)
            json_filename = f"{base_name}_{safe_sheet}.json"
            json_path = os.path.join(output_dir, json_filename)
            
            # Write individual sheet JSON
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(sheet_data, f, indent=2, ensure_ascii=False, default=str)
            
            created_files.append({
                "sheet_name": sheet_name,
                "json_path": json_path,
                "rows": len(df),
                "columns": len(df.columns)
            })
        
        # Also create a combined JSON file with all sheets
        combined_filename = f"{base_name}_all_sheets.json"
        combined_path = os.path.join(output_dir, combined_filename)
        
        combined_data = {
            "source_file": os.path.basename(file_path),
            "file_path": file_path,
            "total_sheets": len(excel_file.sheet_names),
            "sheet_names": excel_file.sheet_names,
            "sheets": all_data
        }
        
        with open(combined_path, 'w', encoding='utf-8') as f:
            json.dump(combined_data, f, indent=2, ensure_ascii=False, default=str)
        
        return json.dumps({
            "source_file": file_path,
            "output_directory": output_dir,
            "json_files_created": len(created_files),
            "files": created_files,
            "combined_file": combined_path,
            "preview": {
                sheet: {
                    "columns": data["columns"],
                    "row_count": data["row_count"],
                    "sample_rows": data["data"][:3] if data["data"] else []
                }
                for sheet, data in all_data.items()
            }
        }, indent=2, default=str)
        
    except ImportError:
        return json.dumps({
            "error": "pandas not installed. Install with: uv add pandas"
        }, indent=2)
    except Exception as e:
        return json.dumps({
            "error": f"Failed to convert to JSON: {str(e)}",
            "file_path": file_path
        }, indent=2)


@mcp.tool()
def extract_excel_rows(
    file_path: str,
    sheet_name: Optional[str] = None,
    start_row: int = 0,
    end_row: Optional[int] = None,
    max_rows: int = 1000
) -> str:
    """
    Extract specific rows from an Excel file.
    
    This tool is useful for large files where you only need a subset of rows.
    
    Args:
        file_path: Path to the Excel file
        sheet_name: Optional specific sheet to extract (default: first sheet)
        start_row: Row number to start from (0-indexed, default: 0)
        end_row: Row number to end at (exclusive, default: start_row + max_rows)
        max_rows: Maximum number of rows to return (default: 1000)
        
    Returns:
        JSON string with selected rows and metadata.
        
    Example:
        extract_excel_rows(file_path="data.xlsx", start_row=100, end_row=200)
    """
    if not os.path.exists(file_path):
        return json.dumps({
            "error": f"File not found: {file_path}"
        }, indent=2)
    
    try:
        import pandas as pd
        
        # Read the Excel file
        excel_file = pd.ExcelFile(file_path)
        
        # Determine which sheet to use
        if sheet_name is None:
            sheet_name = excel_file.sheet_names[0]
        
        # Calculate end_row if not provided
        if end_row is None:
            end_row = start_row + max_rows
        
        # Read specific rows using skiprows and nrows
        skip_rows = list(range(1, start_row + 1)) if start_row > 0 else None
        n_rows = end_row - start_row
        
        # Read the sheet with row limits
        df = pd.read_excel(
            file_path,
            sheet_name=sheet_name,
            skiprows=skip_rows,
            nrows=n_rows
        )
        
        # Convert to records
        records = df.replace({pd.NaT: None, pd.NA: None}).to_dict(orient='records')
        
        # Clean NaN values
        clean_records = []
        for record in records:
            clean_record = {}
            for key, value in record.items():
                if pd.isna(value):
                    clean_record[key] = None
                elif isinstance(value, (pd.Timestamp, datetime)):
                    clean_record[key] = value.isoformat()
                else:
                    clean_record[key] = value
            clean_records.append(clean_record)
        
        return json.dumps({
            "file_path": file_path,
            "sheet_name": sheet_name,
            "start_row": start_row,
            "end_row": end_row,
            "rows_returned": len(clean_records),
            "columns": list(df.columns),
            "data": clean_records
        }, indent=2, default=str)
        
    except ImportError:
        return json.dumps({
            "error": "pandas not installed. Install with: uv add pandas"
        }, indent=2)
    except Exception as e:
        return json.dumps({
            "error": f"Failed to extract rows: {str(e)}",
            "file_path": file_path
        }, indent=2)


# Initialize docling chunker
try:
    from docling.chunking import HierarchicalChunker
    _chunker: Optional[HierarchicalChunker] = None
    
    def get_chunker() -> HierarchicalChunker:
        """Get or create the HierarchicalChunker instance."""
        global _chunker
        if _chunker is None:
            _chunker = HierarchicalChunker()
        return _chunker
    
    CHUNKER_AVAILABLE = True
except ImportError:
    CHUNKER_AVAILABLE = False


@mcp.tool()
def chunk_excel_content(file_path: str, chunk_size: int = 1000) -> str:
    """
    Chunk Excel content using docling's HierarchicalChunker.
    
    This is useful for processing large Excel files in manageable chunks
    for LLM context windows or for creating embeddings.
    
    Args:
        file_path: Path to the Excel file
        chunk_size: Approximate number of tokens per chunk (default: 1000)
        
    Returns:
        JSON string with chunks and metadata.
    """
    if not DOCLING_AVAILABLE:
        return json.dumps({
            "error": "docling is not installed. Install with: uv add docling"
        }, indent=2)
    
    if not CHUNKER_AVAILABLE:
        return json.dumps({
            "error": "docling chunking not available. Install with: uv add 'docling[chunking]'"
        }, indent=2)
    
    if not os.path.exists(file_path):
        return json.dumps({
            "error": f"File not found: {file_path}"
        }, indent=2)
    
    try:
        converter = get_converter()
        chunker = get_chunker()
        
        # Convert the document
        result = converter.convert(file_path)
        
        # Chunk the document
        chunks = list(chunker.chunk(result.document))
        
        # Format chunks for output
        chunk_data = []
        for i, chunk in enumerate(chunks):
            chunk_info = {
                "chunk_number": i + 1,
                "text": chunk.text,
                "metadata": {
                    "headings": chunk.meta.headings if hasattr(chunk.meta, 'headings') else [],
                    "page_number": chunk.meta.page_number if hasattr(chunk.meta, 'page_number') else None,
                    "doc_items": [str(ref) for ref in chunk.meta.doc_items] if hasattr(chunk.meta, 'doc_items') else []
                }
            }
            chunk_data.append(chunk_info)
        
        return json.dumps({
            "file_path": file_path,
            "file_name": os.path.basename(file_path),
            "total_chunks": len(chunk_data),
            "chunk_size_setting": chunk_size,
            "chunks": chunk_data
        }, indent=2, default=str)
        
    except Exception as e:
        return json.dumps({
            "error": f"Failed to chunk content: {str(e)}",
            "file_path": file_path
        }, indent=2)


# OpenSearch integration for large files
try:
    from opensearchpy import OpenSearch
    OPENSEARCH_AVAILABLE = True
except ImportError:
    OPENSEARCH_AVAILABLE = False

# OpenSearch client cache
_opensearch_client: Optional["OpenSearch"] = None

def get_opensearch_client() -> Optional["OpenSearch"]:
    """Get or create OpenSearch client."""
    global _opensearch_client
    if _opensearch_client is None and OPENSEARCH_AVAILABLE:
        host = os.environ.get("OPENSEARCH_HOST", "localhost")
        port = int(os.environ.get("OPENSEARCH_PORT", "9200"))
        
        # Check if security is enabled (default: false for demo setups)
        security_enabled = os.environ.get("OPENSEARCH_SECURITY_ENABLED", "false").lower() == "true"
        
        try:
            if security_enabled:
                # Secure mode with authentication
                auth = (
                    os.environ.get("OPENSEARCH_USER", "admin"),
                    os.environ.get("OPENSEARCH_PASSWORD", "admin")
                )
                _opensearch_client = OpenSearch(
                    hosts=[{"host": host, "port": port}],
                    http_auth=auth,
                    use_ssl=True,
                    verify_certs=False,
                    ssl_assert_hostname=False,
                    ssl_show_warn=False,
                )
            else:
                # Insecure mode (default for demos - security plugin disabled)
                _opensearch_client = OpenSearch(
                    hosts=[{"host": host, "port": port}],
                    http_compress=True,
                    use_ssl=False,
                    verify_certs=False,
                    ssl_assert_hostname=False,
                    ssl_show_warn=False,
                )
        except Exception:
            pass
    return _opensearch_client


@mcp.tool()
def index_excel_in_opensearch(
    file_path: str,
    index_name: Optional[str] = None,
    chunk_size: int = 1000
) -> str:
    """
    Index an Excel file into OpenSearch for fast searching of large datasets.
    
    This converts Excel data to searchable documents and indexes them in OpenSearch,
    enabling hybrid (keyword + vector) search for large files.
    
    Args:
        file_path: Path to the Excel file
        index_name: Optional custom OpenSearch index name. Defaults to filename.
        chunk_size: Number of rows to process per batch (default: 1000)
        
    Returns:
        JSON string with indexing status and statistics.
        
    Environment Variables:
        OPENSEARCH_HOST: OpenSearch host (default: localhost)
        OPENSEARCH_PORT: OpenSearch port (default: 9200)
    """
    if not OPENSEARCH_AVAILABLE:
        return json.dumps({
            "error": "OpenSearch not installed. Install with: uv add opensearch-py",
            "setup_instructions": [
                "1. Install OpenSearch: docker run -d -p 9200:9200 -e discovery.type=single-node opensearchproject/opensearch:latest",
                "2. Install Python client: uv add 'excel-retriever-mcp[opensearch]'",
                "3. Set environment: export OPENSEARCH_HOST=localhost"
            ]
        }, indent=2)
    
    if not os.path.exists(file_path):
        return json.dumps({
            "error": f"File not found: {file_path}"
        }, indent=2)
    
    try:
        import pandas as pd
        
        client = get_opensearch_client()
        if client is None:
            return json.dumps({
                "error": "Could not connect to OpenSearch",
                "hint": "Ensure OpenSearch is running and OPENSEARCH_HOST/PORT are set correctly"
            }, indent=2)
        
        # Determine index name
        if index_name is None:
            index_name = Path(file_path).stem.lower().replace(" ", "_")
        
        # Create index if it doesn't exist
        if not client.indices.exists(index=index_name):
            client.indices.create(
                index=index_name,
                body={
                    "settings": {
                        "number_of_shards": 1,
                        "number_of_replicas": 0
                    },
                    "mappings": {
                        "properties": {
                            "sheet_name": {"type": "keyword"},
                            "row_number": {"type": "integer"},
                            "data": {"type": "object"},
                            "full_text": {"type": "text"},
                            "source_file": {"type": "keyword"}
                        }
                    }
                }
            )
        
        # Read and index each sheet
        excel_file = pd.ExcelFile(file_path)
        total_docs = 0
        sheet_stats = []
        
        for sheet_name in excel_file.sheet_names:
            df = pd.read_excel(file_path, sheet_name=sheet_name)
            
            # Convert to records and create bulk indexing payload
            records = df.replace({pd.NaT: None, pd.NA: None}).to_dict(orient='records')
            
            bulk_data = []
            for i, record in enumerate(records):
                # Clean the record for JSON serialization
                clean_record = {}
                full_text_parts = []
                
                for key, value in record.items():
                    if pd.isna(value):
                        clean_record[key] = None
                    elif isinstance(value, (pd.Timestamp, datetime)):
                        clean_record[key] = value.isoformat()
                        full_text_parts.append(str(value))
                    else:
                        clean_record[key] = value
                        full_text_parts.append(str(value))
                
                doc = {
                    "_index": index_name,
                    "_source": {
                        "sheet_name": sheet_name,
                        "row_number": i + 1,
                        "data": clean_record,
                        "full_text": " ".join(full_text_parts),
                        "source_file": os.path.basename(file_path)
                    }
                }
                bulk_data.append(doc)
            
            # Bulk index in chunks
            from opensearchpy.helpers import bulk
            indexed, errors = bulk(client, bulk_data, chunk_size=chunk_size, raise_on_error=False)
            
            sheet_stats.append({
                "sheet_name": sheet_name,
                "rows": len(records),
                "indexed": indexed,
                "errors": len(errors) if errors else 0
            })
            total_docs += indexed
        
        # Refresh index
        client.indices.refresh(index=index_name)
        
        return json.dumps({
            "status": "success",
            "index_name": index_name,
            "source_file": file_path,
            "total_documents_indexed": total_docs,
            "sheets": sheet_stats,
            "search_hint": f"Now use search_excel_opensearch with index_name='{index_name}'"
        }, indent=2)
        
    except ImportError:
        return json.dumps({
            "error": "pandas not installed. Install with: uv add pandas"
        }, indent=2)
    except Exception as e:
        return json.dumps({
            "error": f"Failed to index in OpenSearch: {str(e)}",
            "file_path": file_path
        }, indent=2)


@mcp.tool()
def search_excel_opensearch(
    query: str,
    index_name: Optional[str] = None,
    size: int = 10,
    file_path: Optional[str] = None
) -> str:
    """
    Search indexed Excel data in OpenSearch using hybrid (keyword + text) search.
    
    This enables fast searching of large Excel files that have been indexed.
    Supports full-text search across all columns and rows.
    
    Args:
        query: Search query (keywords to find in the data)
        index_name: OpenSearch index name to search. If not provided, will try to derive from file_path
        size: Maximum number of results to return (default: 10)
        file_path: Optional path to Excel file (used to determine index_name if not provided)
        
    Returns:
        JSON string with search results.
        
    Example:
        search_excel_opensearch(query="Gulf of Mexico", index_name="sample_projects")
    """
    if not OPENSEARCH_AVAILABLE:
        return json.dumps({
            "error": "OpenSearch not installed. Install with: uv add opensearch-py"
        }, indent=2)
    
    try:
        client = get_opensearch_client()
        if client is None:
            return json.dumps({
                "error": "Could not connect to OpenSearch",
                "hint": "Ensure OpenSearch is running and OPENSEARCH_HOST/PORT are set correctly"
            }, indent=2)
        
        # Determine index name
        if index_name is None:
            if file_path:
                index_name = Path(file_path).stem.lower().replace(" ", "_")
            else:
                return json.dumps({
                    "error": "Either index_name or file_path must be provided"
                }, indent=2)
        
        # Check if index exists
        if not client.indices.exists(index=index_name):
            return json.dumps({
                "error": f"Index '{index_name}' not found",
                "hint": f"Index the file first using index_excel_in_opensearch(file_path='...')"
            }, indent=2)
        
        # Build search query - multi-match across full_text and data fields
        search_body = {
            "size": size,
            "query": {
                "multi_match": {
                    "query": query,
                    "fields": ["full_text^2", "data.*"],
                    "type": "best_fields",
                    "fuzziness": "AUTO"
                }
            },
            "highlight": {
                "fields": {
                    "full_text": {}
                }
            }
        }
        
        response = client.search(index=index_name, body=search_body)
        
        hits = response["hits"]["hits"]
        results = []
        
        for hit in hits:
            source = hit["_source"]
            result = {
                "score": hit["_score"],
                "sheet_name": source.get("sheet_name"),
                "row_number": source.get("row_number"),
                "data": source.get("data"),
                "source_file": source.get("source_file")
            }
            if "highlight" in hit:
                result["highlights"] = hit["highlight"]
            results.append(result)
        
        return json.dumps({
            "query": query,
            "index_name": index_name,
            "total_hits": response["hits"]["total"]["value"],
            "returned": len(results),
            "results": results
        }, indent=2)
        
    except Exception as e:
        return json.dumps({
            "error": f"Search failed: {str(e)}",
            "query": query,
            "index_name": index_name
        }, indent=2)


@mcp.tool()
def list_opensearch_indices() -> str:
    """
    List all OpenSearch indices that have been created for Excel files.
    
    Returns:
        JSON string with list of indices and their stats.
    """
    if not OPENSEARCH_AVAILABLE:
        return json.dumps({
            "error": "OpenSearch not installed. Install with: uv add opensearch-py"
        }, indent=2)
    
    try:
        client = get_opensearch_client()
        if client is None:
            return json.dumps({
                "error": "Could not connect to OpenSearch"
            }, indent=2)
        
        indices = client.cat.indices(format="json")
        
        excel_indices = []
        for idx in indices:
            if not idx["index"].startswith("."):  # Skip system indices
                excel_indices.append({
                    "index_name": idx["index"],
                    "doc_count": idx.get("docs.count", "0"),
                    "size": idx.get("store.size", "0")
                })
        
        return json.dumps({
            "indices": excel_indices,
            "total": len(excel_indices)
        }, indent=2)
        
    except Exception as e:
        return json.dumps({
            "error": f"Failed to list indices: {str(e)}"
        }, indent=2)


# ─── Intelligent Extraction Tools ───────────────────────────────────────────────


@mcp.tool()
def smart_analyze_excel(file_path: str) -> str:
    """
    Intelligently analyze an Excel file, detecting all tables, text blocks,
    figures, merged cells, and named ranges across all sheets.

    This is the recommended first tool to call when a user drops in an Excel file.
    It handles complex real-world spreadsheets with multiple tables per sheet,
    instructions mixed with data, charts, and irregular layouts.

    Args:
        file_path: Path to the Excel file

    Returns:
        JSON string with complete workbook analysis including:
        - All detected tables with headers, data, and locations
        - Standalone text blocks (instructions, notes, titles)
        - Charts and figures metadata
        - Merged cell regions
        - Named ranges
    """
    if not os.path.exists(file_path):
        return json.dumps({
            "error": f"File not found: {file_path}"
        }, indent=2)

    try:
        extractor = SmartExcelExtractor(file_path)
        analysis = extractor.analyze()
        result = analysis_to_dict(analysis)
        extractor.close()
        return json.dumps(result, indent=2, default=str)
    except Exception as e:
        return json.dumps({
            "error": f"Failed to analyze file: {str(e)}",
            "file_path": file_path
        }, indent=2)


@mcp.tool()
def smart_extract_tables(
    file_path: str,
    sheet_name: Optional[str] = None,
    table_index: Optional[int] = None,
    output_format: str = "json"
) -> str:
    """
    Extract tables from an Excel file using intelligent table detection.

    Automatically finds multiple tables per sheet, even when they are separated
    by empty rows/columns, instruction text, or figures.

    Args:
        file_path: Path to the Excel file
        sheet_name: Optional sheet name to extract from. If not provided,
                   extracts from all sheets.
        table_index: Optional specific table index (0-based) within a sheet.
                    If not provided, extracts all tables.
        output_format: Output format - "json" (default), "csv", "markdown",
                      or "records" (list of dicts per table).

    Returns:
        JSON string with extracted tables in the requested format.
    """
    if not os.path.exists(file_path):
        return json.dumps({
            "error": f"File not found: {file_path}"
        }, indent=2)

    valid_formats = ["json", "csv", "markdown", "records"]
    if output_format not in valid_formats:
        return json.dumps({
            "error": f"Invalid output_format '{output_format}'. Must be one of: {valid_formats}"
        }, indent=2)

    try:
        extractor = SmartExcelExtractor(file_path)
        analysis = extractor.analyze()
        extractor.close()

        tables_output = []

        for sheet in analysis.sheets:
            if sheet_name and sheet.sheet_name != sheet_name:
                continue

            for table in sheet.tables:
                if table_index is not None and table.table_index != table_index:
                    continue

                table_out = {
                    "sheet_name": table.sheet_name,
                    "table_index": table.table_index,
                    "name": table.name,
                    "headers": table.headers,
                    "row_count": table.row_count,
                    "col_count": table.col_count,
                    "location": f"rows {table.start_row}-{table.end_row}, cols {table.start_col}-{table.end_col}",
                }

                if output_format == "csv":
                    table_out["data_csv"] = table_to_csv_string(table)
                elif output_format == "markdown":
                    table_out["data_markdown"] = table_to_markdown(table)
                elif output_format == "records":
                    table_out["data_records"] = table_to_records(table)
                else:
                    table_out["data"] = table.data

                tables_output.append(table_out)

        return json.dumps({
            "file_path": file_path,
            "output_format": output_format,
            "tables_found": len(tables_output),
            "tables": tables_output,
        }, indent=2, default=str)

    except Exception as e:
        return json.dumps({
            "error": f"Failed to extract tables: {str(e)}",
            "file_path": file_path
        }, indent=2)


@mcp.tool()
def smart_extract_text(file_path: str, sheet_name: Optional[str] = None) -> str:
    """
    Extract standalone text blocks from an Excel file (instructions, notes,
    titles, labels) that are NOT part of data tables.

    Useful for understanding the context and instructions that accompany
    the data in complex spreadsheets.

    Args:
        file_path: Path to the Excel file
        sheet_name: Optional sheet name. If not provided, extracts from all sheets.

    Returns:
        JSON string with classified text blocks:
        - "title": Bold or short text likely serving as a section header
        - "instruction": Long text or text starting with keywords like Note, Warning
        - "note": Other standalone text
        - "label": Short text near data
    """
    if not os.path.exists(file_path):
        return json.dumps({
            "error": f"File not found: {file_path}"
        }, indent=2)

    try:
        extractor = SmartExcelExtractor(file_path)
        analysis = extractor.analyze()
        extractor.close()

        text_output = []
        for sheet in analysis.sheets:
            if sheet_name and sheet.sheet_name != sheet_name:
                continue

            for text in sheet.text_blocks:
                text_output.append({
                    "sheet_name": text.sheet_name,
                    "row": text.row,
                    "col": text.col,
                    "text": text.text,
                    "classification": text.classification,
                    "is_bold": text.is_bold,
                })

        return json.dumps({
            "file_path": file_path,
            "text_blocks_found": len(text_output),
            "text_blocks": text_output,
        }, indent=2, default=str)

    except Exception as e:
        return json.dumps({
            "error": f"Failed to extract text: {str(e)}",
            "file_path": file_path
        }, indent=2)


@mcp.tool()
def smart_export_all(
    file_path: str,
    output_dir: Optional[str] = None,
    formats: Optional[str] = None
) -> str:
    """
    Export all detected tables from an Excel file to multiple formats.

    Each table is exported as a separate file. Supports CSV, JSON, Markdown,
    and Parquet formats. Also generates a summary JSON with the full analysis.

    Args:
        file_path: Path to the Excel file
        output_dir: Directory to save exported files. Defaults to a subfolder
                   next to the Excel file named '<filename>_export/'.
        formats: Comma-separated list of formats to export.
                Supported: "csv", "json", "markdown", "parquet".
                Defaults to "csv,json".

    Returns:
        JSON string with paths to all created files and export summary.
    """
    if not os.path.exists(file_path):
        return json.dumps({
            "error": f"File not found: {file_path}"
        }, indent=2)

    # Parse formats
    if formats is None:
        format_list = ["csv", "json"]
    else:
        format_list = [f.strip().lower() for f in formats.split(",")]

    valid_formats = {"csv", "json", "markdown", "parquet"}
    invalid = set(format_list) - valid_formats
    if invalid:
        return json.dumps({
            "error": f"Invalid formats: {invalid}. Supported: {valid_formats}"
        }, indent=2)

    # Determine output directory
    if output_dir is None:
        base = Path(file_path).stem
        output_dir = os.path.join(os.path.dirname(file_path) or ".", f"{base}_export")

    os.makedirs(output_dir, exist_ok=True)

    try:
        extractor = SmartExcelExtractor(file_path)
        analysis = extractor.analyze()
        extractor.close()

        created_files = []
        base_name = Path(file_path).stem

        # Export analysis summary
        summary_path = os.path.join(output_dir, f"{base_name}_analysis.json")
        analysis_dict = analysis_to_dict(analysis)
        with open(summary_path, 'w', encoding='utf-8') as f:
            json.dump(analysis_dict, f, indent=2, ensure_ascii=False, default=str)
        created_files.append({
            "type": "analysis_summary",
            "path": summary_path,
        })

        # Export each table
        for sheet in analysis.sheets:
            safe_sheet = "".join(c if c.isalnum() else "_" for c in sheet.sheet_name)

            for table in sheet.tables:
                table_label = table.name or f"table_{table.table_index}"
                safe_label = "".join(c if c.isalnum() else "_" for c in table_label)
                file_prefix = f"{base_name}_{safe_sheet}_{safe_label}"

                if "csv" in format_list:
                    csv_path = os.path.join(output_dir, f"{file_prefix}.csv")
                    with open(csv_path, 'w', encoding='utf-8', newline='') as f:
                        writer = csv.writer(f)
                        if table.has_header:
                            writer.writerow(table.headers)
                        for row in table.data:
                            writer.writerow([str(v) if v is not None else "" for v in row])
                    created_files.append({
                        "type": "csv",
                        "sheet": sheet.sheet_name,
                        "table": table_label,
                        "path": csv_path,
                        "rows": table.row_count,
                    })

                if "json" in format_list:
                    json_path = os.path.join(output_dir, f"{file_prefix}.json")
                    records = table_to_records(table)
                    table_json = {
                        "sheet_name": table.sheet_name,
                        "table_name": table.name,
                        "headers": table.headers,
                        "row_count": table.row_count,
                        "data": records,
                    }
                    with open(json_path, 'w', encoding='utf-8') as f:
                        json.dump(table_json, f, indent=2, ensure_ascii=False, default=str)
                    created_files.append({
                        "type": "json",
                        "sheet": sheet.sheet_name,
                        "table": table_label,
                        "path": json_path,
                        "rows": table.row_count,
                    })

                if "markdown" in format_list:
                    md_path = os.path.join(output_dir, f"{file_prefix}.md")
                    md_content = table_to_markdown(table)
                    with open(md_path, 'w', encoding='utf-8') as f:
                        if table.name:
                            f.write(f"## {table.name}\n\n")
                        f.write(md_content)
                        f.write("\n")
                    created_files.append({
                        "type": "markdown",
                        "sheet": sheet.sheet_name,
                        "table": table_label,
                        "path": md_path,
                        "rows": table.row_count,
                    })

                if "parquet" in format_list:
                    try:
                        import pandas as pd
                        pq_path = os.path.join(output_dir, f"{file_prefix}.parquet")
                        records = table_to_records(table)
                        df = pd.DataFrame(records)
                        df.to_parquet(pq_path, index=False)
                        created_files.append({
                            "type": "parquet",
                            "sheet": sheet.sheet_name,
                            "table": table_label,
                            "path": pq_path,
                            "rows": table.row_count,
                        })
                    except ImportError:
                        created_files.append({
                            "type": "parquet",
                            "error": "pandas or pyarrow not installed for Parquet export",
                        })

        # Export text blocks as a separate file
        text_blocks = []
        for sheet in analysis.sheets:
            for text in sheet.text_blocks:
                text_blocks.append({
                    "sheet_name": text.sheet_name,
                    "row": text.row,
                    "col": text.col,
                    "text": text.text,
                    "classification": text.classification,
                })

        if text_blocks:
            text_path = os.path.join(output_dir, f"{base_name}_text_blocks.json")
            with open(text_path, 'w', encoding='utf-8') as f:
                json.dump(text_blocks, f, indent=2, ensure_ascii=False, default=str)
            created_files.append({
                "type": "text_blocks",
                "path": text_path,
                "count": len(text_blocks),
            })

        return json.dumps({
            "status": "success",
            "source_file": file_path,
            "output_directory": output_dir,
            "total_tables_exported": analysis.total_tables,
            "total_files_created": len(created_files),
            "formats": format_list,
            "files": created_files,
        }, indent=2, default=str)

    except Exception as e:
        return json.dumps({
            "error": f"Failed to export: {str(e)}",
            "file_path": file_path
        }, indent=2)


@mcp.tool()
def smart_get_sheet_overview(file_path: str, sheet_name: str) -> str:
    """
    Get a detailed overview of a specific sheet, including all content regions
    laid out spatially so you can understand the sheet structure.

    Args:
        file_path: Path to the Excel file
        sheet_name: Name of the sheet to analyze

    Returns:
        JSON string with spatial layout of all content on the sheet:
        tables, text blocks, figures, and merged regions with their positions.
    """
    if not os.path.exists(file_path):
        return json.dumps({
            "error": f"File not found: {file_path}"
        }, indent=2)

    try:
        extractor = SmartExcelExtractor(file_path)
        analysis = extractor.analyze()
        extractor.close()

        target_sheet = None
        for sheet in analysis.sheets:
            if sheet.sheet_name == sheet_name:
                target_sheet = sheet
                break

        if target_sheet is None:
            return json.dumps({
                "error": f"Sheet '{sheet_name}' not found",
                "available_sheets": analysis.sheet_names,
            }, indent=2)

        # Build spatial overview
        content_map = []

        for table in target_sheet.tables:
            content_map.append({
                "type": "table",
                "name": table.name,
                "table_index": table.table_index,
                "location": {
                    "start_row": table.start_row,
                    "end_row": table.end_row,
                    "start_col": table.start_col,
                    "end_col": table.end_col,
                },
                "size": f"{table.row_count} rows x {table.col_count} cols",
                "headers": table.headers,
                "sample_data": table.data[:3] if table.data else [],
            })

        for text in target_sheet.text_blocks:
            content_map.append({
                "type": "text",
                "classification": text.classification,
                "location": {"row": text.row, "col": text.col},
                "text": text.text[:200] + ("..." if len(text.text) > 200 else ""),
                "is_bold": text.is_bold,
            })

        for fig in target_sheet.figures:
            content_map.append({
                "type": "figure",
                "chart_type": fig.chart_type,
                "title": fig.title,
                "series_count": fig.series_count,
            })

        for merged in target_sheet.merged_cells:
            content_map.append({
                "type": "merged_region",
                "range": merged["range"],
                "value": merged["value"],
            })

        # Sort by position
        def sort_key(item):
            loc = item.get("location", {})
            if isinstance(loc, dict):
                return (loc.get("start_row", loc.get("row", 999)), loc.get("start_col", loc.get("col", 999)))
            return (999, 999)

        content_map.sort(key=sort_key)

        return json.dumps({
            "file_path": file_path,
            "sheet_name": sheet_name,
            "dimensions": f"{target_sheet.total_rows} rows x {target_sheet.total_cols} cols",
            "summary": {
                "tables": len(target_sheet.tables),
                "text_blocks": len(target_sheet.text_blocks),
                "figures": len(target_sheet.figures),
                "merged_regions": len(target_sheet.merged_cells),
            },
            "content_map": content_map,
        }, indent=2, default=str)

    except Exception as e:
        return json.dumps({
            "error": f"Failed to get sheet overview: {str(e)}",
            "file_path": file_path
        }, indent=2)


@mcp.tool()
def smart_table_to_format(
    file_path: str,
    sheet_name: str,
    table_index: int,
    output_format: str = "csv"
) -> str:
    """
    Convert a specific detected table to a chosen format and return the content
    inline (no file written). Useful for quick data inspection or piping to LLMs.

    Args:
        file_path: Path to the Excel file
        sheet_name: Name of the sheet containing the table
        table_index: Index of the table within the sheet (0-based)
        output_format: "csv", "json", "markdown", or "records"

    Returns:
        The table content in the requested format as a string.
    """
    if not os.path.exists(file_path):
        return json.dumps({
            "error": f"File not found: {file_path}"
        }, indent=2)

    valid_formats = ["csv", "json", "markdown", "records"]
    if output_format not in valid_formats:
        return json.dumps({
            "error": f"Invalid format '{output_format}'. Use one of: {valid_formats}"
        }, indent=2)

    try:
        extractor = SmartExcelExtractor(file_path)
        analysis = extractor.analyze()
        extractor.close()

        # Find the target table
        target_table = None
        for sheet in analysis.sheets:
            if sheet.sheet_name == sheet_name:
                for table in sheet.tables:
                    if table.table_index == table_index:
                        target_table = table
                        break
                break

        if target_table is None:
            # Provide helpful info about what's available
            available = []
            for sheet in analysis.sheets:
                for table in sheet.tables:
                    available.append({
                        "sheet": sheet.sheet_name,
                        "table_index": table.table_index,
                        "name": table.name,
                        "rows": table.row_count,
                    })
            return json.dumps({
                "error": f"Table not found: sheet='{sheet_name}', table_index={table_index}",
                "available_tables": available,
            }, indent=2)

        if output_format == "csv":
            return table_to_csv_string(target_table)
        elif output_format == "markdown":
            return table_to_markdown(target_table)
        elif output_format == "records":
            return json.dumps(table_to_records(target_table), indent=2, default=str)
        else:
            return json.dumps({
                "headers": target_table.headers,
                "data": target_table.data,
                "row_count": target_table.row_count,
            }, indent=2, default=str)

    except Exception as e:
        return json.dumps({
            "error": f"Failed to convert table: {str(e)}",
            "file_path": file_path
        }, indent=2)


if __name__ == "__main__":
    # Initialize and run the server
    mcp.run(transport='stdio')
