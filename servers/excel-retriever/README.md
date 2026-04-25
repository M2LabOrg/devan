# Excel Retriever MCP Server

An intelligent Model Context Protocol (MCP) server that extracts and queries data from complex Excel files. Drop in any Excel file — multiple tabs, multiple tables per tab, charts, instructions, merged cells — and get clean, structured data out in CSV, JSON, Markdown, or Parquet.

Designed as a reusable product: plug it into any application where users upload Excel files and need the data extracted for LLM analysis, dashboards, or data pipelines.

## Key Capabilities

- **Intelligent table detection** — automatically finds multiple tables per sheet, even with gaps, instructions, and charts between them
- **Text classification** — separates instructions, notes, titles, and labels from actual data
- **Chart/figure awareness** — detects and reports embedded charts and images
- **Merged cell handling** — correctly reads merged cell regions
- **Named range extraction** — reads workbook-level named ranges
- **Multi-format export** — CSV, JSON, Markdown, Parquet per table
- **Knowledge-enhanced extraction** — automatic relationship detection and LLM-ready schema descriptions
- **Large file support** — OpenSearch integration for 100k+ row files

## Quick Start

```bash
cd excel_retriever

# Set up environment
uv venv
source .venv/bin/activate  # macOS/Linux

# Install dependencies
uv pip install mcp openpyxl pandas

# Create sample complex Excel file
python create_complex_sample.py

# Run the Inspector
npx @modelcontextprotocol/inspector python3 excel_server.py
```

Then call `smart_analyze_excel` with the path to any Excel file.

## Folder Structure

```
excel_retriever/
├── excel_server.py          # MCP server (18 tools)
├── smart_extractor.py       # Intelligent extraction engine
├── excel_files/             # Your Excel files go here
├── create_sample_data.py    # Basic sample data generator
├── create_complex_sample.py # Complex sample (multi-table, charts, etc.)
├── pyproject.toml           # Project dependencies
├── demo_notebook.ipynb      # Jupyter notebook tutorial
├── demo_instructions.md     # Markdown tutorial
└── README.md                # This file
```

## Tools Overview

### Intelligent Extraction (New — Recommended)

| Tool | Description |
|------|-------------|
| `smart_analyze_excel` | Full workbook analysis: tables, text, figures, merged cells, named ranges |
| `smart_extract_tables` | Extract tables with auto-detection, output as JSON/CSV/Markdown/records |
| `smart_extract_text` | Extract standalone text (instructions, notes, titles) separate from data |
| `smart_export_all` | Batch export all tables to CSV, JSON, Markdown, and/or Parquet files |
| `smart_get_sheet_overview` | Spatial layout of all content on a specific sheet |
| `smart_table_to_format` | Convert a specific detected table to any format inline |

### Core Tools
- **list_excel_files** — Discover Excel files in a directory
- **extract_excel_content** — Extract content using docling
- **query_excel_data** — Query specific information from spreadsheets
- **get_excel_summary** — Get file structure and metadata
- **convert_excel_to_csv** — Convert sheets to CSV (pandas-based, one table per sheet)
- **convert_excel_to_json** — Convert sheets to JSON
- **extract_excel_rows** — Extract specific row ranges from large files
- **chunk_excel_content** — Chunk content for LLM context windows

### OpenSearch Tools (Optional — For Large Files)
- **index_excel_in_opensearch** — Index Excel data for fast searching (100k+ rows)
- **search_excel_opensearch** — Search indexed data with hybrid search
- **list_opensearch_indices** — List all indexed Excel files

**When to use OpenSearch:**
- Small files (< 10k rows): Use smart extraction tools directly
- Large files (10k-100k rows): Use core tools with pagination
- Very large files (100k+ rows): Use OpenSearch indexing

## Knowledge-Enhanced Extraction for LLMs

The `smart_analyze_excel` tool now includes **automatic relationship detection** and **LLM-ready schema descriptions** to help LLMs understand Excel data more accurately.

### What You Get

1. **Automatic Relationship Detection** — Finds common columns across tables (e.g., "Project ID" linking two tables)
2. **LLM Schema Description** — Natural language summary of the workbook structure, optimized for LLM prompts
3. **Text Classification** — Separates instructions/notes from data so LLMs understand business rules

### Example Output

```json
{
  "relationships": [
    {
      "source_table": "Projects.Active Projects",
      "target_table": "Projects.Upcoming Milestones",
      "common_columns": ["project id"],
      "description": "Tables can be joined using 'project id'"
    }
  ],
  "llm_schema_description": "Workbook: complex_sample.xlsx\n\nSheet: Projects\n- Active Projects: 8 rows x 8 columns\n  Columns: Project ID, Name, Client, Start Date...\n\nKey Relationships:\n- Join Active Projects with Milestones using 'project id'\n\nAI Analysis Strategy:\n1. Use common columns to join data\n2. Pay attention to instruction blocks..."
}
```

### Why This Matters

**Without knowledge enhancement:** LLMs see raw data but struggle to join tables or understand units/business rules.

**With knowledge enhancement:** LLMs get a "map" of the workbook with explicit join hints, making answers 10x more accurate.

### When to Use a Graph Database

- ✅ **Use JSON** (current approach): Single Excel file per request, simple joins, LLM-driven queries
- ⚠️ **Consider Graph DB**: Multi-file knowledge base (100+ Excel files), complex graph traversal queries, real-time relationship discovery

**See [KNOWLEDGE_ENHANCED_EXTRACTION.md](KNOWLEDGE_ENHANCED_EXTRACTION.md) for the complete guide.**

## Prerequisites

You need either **uv** (recommended) or **pip** with Python 3.10+.

**Install uv (macOS/Linux):**
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

**Install uv (Windows):**
```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

## Setup

### Step 1: Create the mcp_project folder and files

**If using Jupyter:** Run the cells in `demo_notebook.ipynb` to automatically create the files.

**If manual:**
```bash
mkdir -p mcp_project
# Copy excel_server.py and pyproject.toml into mcp_project/
```

### Step 2: Install dependencies (from mcp_project folder)

```bash
cd mcp_project

# Using uv
uv init
uv venv
source .venv/bin/activate
uv add mcp docling pandas

# Or using pip
python3 -m venv .venv
source .venv/bin/activate
pip install mcp docling pandas
```

### Step 3: Create sample data (from root folder)

```bash
# Create excel_files directory
mkdir -p excel_files

# Generate sample data
python create_sample_data.py
```

### Step 4: Run the Inspector (from mcp_project folder)

**Note:** The Inspector automatically starts the server - you don't need to run it separately!

```bash
cd mcp_project
npx @modelcontextprotocol/inspector uv run excel_server.py
```

Open the displayed URL (usually http://localhost:5173) in your browser.

## Tool Reference

### Intelligent Extraction Tools

#### smart_analyze_excel
**The recommended first call.** Analyzes the entire workbook: detects tables, text blocks, figures, merged cells, named ranges.

**Parameters:**
- `file_path`: Path to Excel file

#### smart_extract_tables
Extract auto-detected tables from one or all sheets. Supports multiple output formats.

**Parameters:**
- `file_path`: Path to Excel file
- `sheet_name` (optional): Specific sheet
- `table_index` (optional): Specific table (0-based)
- `output_format` (optional): `json` (default), `csv`, `markdown`, or `records`

#### smart_extract_text
Extract standalone text blocks (instructions, notes, titles) that are NOT part of data tables.

**Parameters:**
- `file_path`: Path to Excel file
- `sheet_name` (optional): Specific sheet

#### smart_export_all
Batch export all detected tables to files in multiple formats.

**Parameters:**
- `file_path`: Path to Excel file
- `output_dir` (optional): Output directory (default: `<filename>_export/`)
- `formats` (optional): Comma-separated list: `csv,json,markdown,parquet` (default: `csv,json`)

#### smart_get_sheet_overview
Spatial layout of all content on a specific sheet — tables, text, figures, merged regions with positions.

**Parameters:**
- `file_path`: Path to Excel file
- `sheet_name`: Sheet name to analyze

#### smart_table_to_format
Convert a specific detected table to any format inline (no file written).

**Parameters:**
- `file_path`: Path to Excel file
- `sheet_name`: Sheet containing the table
- `table_index`: Table index (0-based)
- `output_format` (optional): `csv` (default), `json`, `markdown`, or `records`

### Core Tools

#### list_excel_files
Lists all Excel files in a directory with metadata.

**Parameters:**
- `directory` (optional): Path to search for Excel files (default: `excel_files`)

#### extract_excel_content
Extracts full content from an Excel file using docling.

**Parameters:**
- `file_path`: Path to Excel file
- `sheet_name` (optional): Specific sheet to extract

#### query_excel_data
Queries specific information from an Excel file.

**Parameters:**
- `file_path`: Path to Excel file
- `query`: Description of data to find (e.g., "high risk projects")

#### get_excel_summary
Gets structural summary of an Excel file.

**Parameters:**
- `file_path`: Path to Excel file

#### convert_excel_to_csv
Converts Excel sheets to CSV files (pandas-based, assumes one table per sheet).

**Parameters:**
- `file_path`: Path to Excel file
- `output_dir` (optional): Directory for CSV output

#### convert_excel_to_json
Converts Excel sheets to JSON files (individual + combined).

**Parameters:**
- `file_path`: Path to Excel file
- `output_dir` (optional): Directory for JSON output
- `include_metadata` (optional): Include column types and sheet info (default: `true`)

## OpenSearch Integration (Optional)

For very large Excel files (100k+ rows), use OpenSearch for fast indexing and search.

### Setup

**1. Start OpenSearch (Docker - Security Disabled for Demo)**
```bash
docker run -d -p 9200:9200 -e discovery.type=single-node -e plugins.security.disabled=true opensearchproject/opensearch:latest
```

**Wait 30-60 seconds** for OpenSearch to fully start. Test with: `curl http://localhost:9200`

**For Production:** Use secure setup with authentication (see Advanced section in demo_instructions.md)

**2. Install OpenSearch Python Client**
```bash
cd mcp_project
uv add opensearch-py
```

**3. Set Environment Variables (Optional)**
```bash
# Only needed if OpenSearch is not on localhost:9200
export OPENSEARCH_HOST=localhost
export OPENSEARCH_PORT=9200

# For production (security enabled):
# export OPENSEARCH_SECURITY_ENABLED=true
# export OPENSEARCH_USER=admin
# export OPENSEARCH_PASSWORD=your_password
```

### OpenSearch Tools

#### index_excel_in_opensearch
Indexes an Excel file into OpenSearch for fast searching.

**Parameters:**
- `file_path`: Path to Excel file
- `index_name` (optional): Custom index name (default: derived from filename)
- `chunk_size` (optional): Rows per batch (default: 1000)

#### search_excel_opensearch
Searches indexed Excel data using hybrid (keyword + text) search.

**Parameters:**
- `query`: Search query (e.g., "Gulf of Mexico")
- `index_name` (optional): OpenSearch index to search
- `size` (optional): Max results (default: 10)
- `file_path` (optional): Used to determine index_name if not provided

#### list_opensearch_indices
Lists all OpenSearch indices created for Excel files.

**Parameters:** None

## Important Paths

Since the server runs from `mcp_project/`, use these relative paths:

| Location | Path from mcp_project |
|----------|----------------------|
| Excel files | `../excel_files/filename.xlsx` |
| CSV output | `../excel_files/csv_output/` |
| JSON output | `../excel_files/json_output/` |

Or use absolute paths.

## Files

- `excel_server.py` - MCP server with 18 tools (6 smart + 8 core + 1 chunker + 3 OpenSearch)
- `smart_extractor.py` - Intelligent extraction engine (table detection, text classification, figure/chart awareness)
- `pyproject.toml` - Project dependencies
- `create_sample_data.py` - Basic sample data generator
- `create_complex_sample.py` - Complex sample with multi-table sheets, charts, merged cells, instructions
- `demo_notebook.ipynb` - Full tutorial with automatic file generation
- `demo_instructions.md` - Markdown version (manual setup)

## Documentation

- **Full Instructions with Jupyter**: See `demo_notebook.ipynb`
- **Full Instructions without Jupyter**: See `demo_instructions.md`
- **Quick Commands**: See "Quick Reference" sections in the docs above

## Troubleshooting

**"docling is not installed"**
```bash
cd mcp_project
uv add docling
```

**"File not found" errors**
- Make sure you're using paths relative to `mcp_project/` folder
- Use `../excel_files/` instead of `excel_files/`

**Python version error**
MCP requires Python 3.10+. Check version:
```bash
python3 --version
```

If needed, recreate venv with Python 3.11:
```bash
cd mcp_project
rm -rf .venv
uv venv --python python3.11
source .venv/bin/activate
uv add mcp docling pandas
```

**Inspector won't connect**
1. Run Inspector from `mcp_project` folder
2. Check Node.js is installed: `node --version`
3. Verify command: `uv` with args `run excel_server.py`

**OpenSearch connection failed**
```bash
# Check if OpenSearch is running
curl http://localhost:9200

# Check Docker container
docker ps | grep opensearch

# Verify environment variables
echo $OPENSEARCH_HOST $OPENSEARCH_PORT
```

## License

MIT
