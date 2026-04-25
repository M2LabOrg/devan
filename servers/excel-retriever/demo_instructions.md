# Excel Retriever MCP Server - Demo

This notebook demonstrates how to use the **Excel Retriever MCP Server** - a tool that extracts and queries data from Excel files using the docling library. This solves the problem of Copilot and other LLMs struggling to properly extract structured data from Excel files.

## How This Works (No Jupyter Required)

If you're reading this Markdown file (not the Jupyter notebook), the server files need to be created manually. Follow the steps below to set up the project.

**Note:** If you have the Jupyter notebook (`demo_notebook.ipynb`), it can create these files automatically using `%%writefile` magic functions.

## Folder Structure After Setup

```
excel_retriever/
├── mcp_project/          # MCP server code (created manually or by notebook)
│   ├── excel_server.py   # Main MCP server
│   └── pyproject.toml    # Project dependencies
├── excel_files/          # Your Excel files go here
├── create_sample_data.py # Sample data generator (at root level)
├── demo_notebook.ipynb   # Jupyter notebook with full tutorial + file generation
├── demo_instructions.md  # This file
└── README.md            # Quick reference
```

## What is MCP?

Model Context Protocol (MCP) is a standard for connecting AI assistants to external tools and data sources. This server exposes tools that can:
- **list_excel_files** - List all Excel files in a directory
- **extract_excel_content** - Extract full content from an Excel file
- **query_excel_data** - Query specific information from Excel
- **get_excel_summary** - Get file structure summary
- **convert_excel_to_csv** - Convert Excel sheets to CSV
- **convert_excel_to_json** - Convert Excel sheets to JSON

## OpenSearch Integration (Optional - For Large Files)

For very large Excel files (100k+ rows), the server now supports **OpenSearch integration**:

- **index_excel_in_opensearch** - Index Excel data for fast searching
- **search_excel_opensearch** - Search indexed data with hybrid (keyword + text) search
- **list_opensearch_indices** - List all indexed Excel files

**Why OpenSearch?**
- Handles massive Excel files that won't fit in memory
- Fast hybrid search (combines keyword and semantic matching)
- Relevance scoring with highlights

**When to use:**
- Small files (< 10k rows): Use `query_excel_data` directly
- Large files (10k-100k rows): Use server-side filtering
- Very large files (100k+ rows): Use OpenSearch indexing

## Prerequisites

You need either **uv** (recommended) or **pip** installed to run this server.

---

## Step 1: Install uv (Recommended)

**uv** is a fast Python package manager and environment manager. It's the recommended way to run MCP servers.

### Option A: Install uv (if not already installed)

**macOS/Linux:**
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

**Windows:**
```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

After installation, restart your terminal or run:
```bash
source ~/.zshrc  # macOS/Linux
```

### Option B: Use pip instead

If you prefer not to use uv, ensure you have Python 3.10+ and pip installed:
```bash
python3 --version  # Should be 3.10 or higher
pip --version
```

Install pip if needed:
- **macOS**: `python3 -m ensurepip --upgrade`
- **Ubuntu/Debian**: `sudo apt install python3-pip`
- **Windows**: pip comes with Python installer

---

## Step 2: Create the MCP Project Folder and Files

Since you're using the Markdown version (not Jupyter), you need to create the files manually:

### 2a. Create the mcp_project folder

```bash
mkdir -p mcp_project
```

### 2b. Create `mcp_project/excel_server.py`

Copy the server code from the `excel_server.py` file in the root folder, or create a new file with the MCP server code. The server code is also available in the GitHub repository.

**Key things to note for the server file:**
- It should use `EXCEL_DIR = os.environ.get("EXCEL_DIR", "../excel_files")` to look for Excel files in the parent directory
- It needs the 6 tool functions: `list_excel_files`, `extract_excel_content`, `query_excel_data`, `get_excel_summary`, `convert_excel_to_csv`, `convert_excel_to_json`
- **Optional:** 3 OpenSearch tools: `index_excel_in_opensearch`, `search_excel_opensearch`, `list_opensearch_indices`
- It uses FastMCP from the `mcp` package

### 2c. Create `mcp_project/pyproject.toml`

```toml
[project]
name = "excel-retriever-mcp"
version = "0.1.0"
description = "MCP Server for Excel data extraction using docling"
readme = "README.md"
requires-python = ">=3.10"
dependencies = [
    "mcp>=1.26.0",
    "docling>=2.0.0",
    "pandas>=2.0.0",
    "openpyxl>=3.1.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.0",
    "black>=23.0",
    "ruff>=0.1.0",
]
opensearch = [
    "opensearch-py>=2.4.0",
]

[tool.uv]
python-downloads = "manual"
```

---

## Step 3: Set Up the Project Environment

**Important:** All commands below should be run from the `mcp_project` folder.

### Using uv (Recommended)

```bash
# Navigate to mcp_project folder
cd mcp_project

# Initialize the project
uv init

# Create virtual environment
uv venv

# Activate virtual environment
source .venv/bin/activate  # macOS/Linux
# .venv\Scripts\activate  # Windows

# Install dependencies
uv add mcp docling pandas

# Optional: Install OpenSearch support
uv add opensearch-py
```

### Using pip

```bash
# Navigate to mcp_project folder
cd mcp_project

# Create virtual environment
python3 -m venv .venv

# Activate virtual environment
source .venv/bin/activate  # macOS/Linux
# .venv\Scripts\activate  # Windows

# Install dependencies
pip install mcp docling pandas

# Optional: Install OpenSearch support
pip install opensearch-py
```

---

## Step 4: Prepare Sample Excel Files

The server looks for Excel files in the `excel_files` directory (at the project root level, next to this notebook). Create this directory and add your Excel files:

```bash
# From the excel_retriever root folder (where this notebook is)
mkdir -p excel_files
```

You can also set a custom directory using the `EXCEL_DIR` environment variable:

```bash
export EXCEL_DIR="/path/to/your/excel/files"
```

### Create Sample Data

Run the provided script from the root folder:

```bash
python create_sample_data.py
```

Or manually create sample data with Python:

```python
import pandas as pd
import os

# Create excel_files directory
os.makedirs('excel_files', exist_ok=True)

# Sample data
project_data = {
    'Project_ID': ['PRJ-001', 'PRJ-002', 'PRJ-003', 'PRJ-004', 'PRJ-005'],
    'Project_Name': ['Offshore Platform A', 'Wind Farm B', 'Pipeline C', 'Refinery D', 'Subsea E'],
    'Region': ['North Sea', 'Baltic Sea', 'Gulf of Mexico', 'Middle East', 'Norwegian Sea'],
    'Budget_MUSD': [450.5, 280.3, 125.8, 890.2, 340.7],
    'Actual_Cost_MUSD': [445.2, 295.1, 118.5, 920.5, 338.9],
    'Status': ['Complete', 'In Progress', 'Complete', 'In Progress', 'Planning'],
    'Risk_Level': ['Low', 'Medium', 'Low', 'High', 'Medium']
}

# Create Excel file
with pd.ExcelWriter('excel_files/sample_projects.xlsx') as writer:
    pd.DataFrame(project_data).to_excel(writer, sheet_name='Projects', index=False)

print("Created: excel_files/sample_projects.xlsx")
```

---

## Step 5: Launch the MCP Inspector and Test the Server

The **MCP Inspector** is a UI tool for testing MCP servers interactively. You do NOT need to run the server separately first - the Inspector will start it for you!

### Prerequisites

You need **Node.js** installed to run the Inspector:

**Check if Node.js is installed:**
```bash
node --version
npx --version
```

**Install Node.js if needed:**
- **macOS**: `brew install node`
- **Ubuntu/Debian**: `sudo apt install nodejs npm`
- **Windows**: Download from [nodejs.org](https://nodejs.org)

### Start the Inspector

**Important:** Run this command from the `mcp_project` folder.

Open a terminal and run:

**Using uv:**
```bash
cd mcp_project
npx @modelcontextprotocol/inspector uv run excel_server.py
```

**Using Python:**
```bash
cd mcp_project
npx @modelcontextprotocol/inspector python excel_server.py
```

**What happens:**
1. The Inspector starts the MCP server automatically
2. The Inspector displays a URL (usually http://localhost:5173)
3. Open that URL in your browser
4. You can now test all the tools interactively!

### Inspector Configuration

In the Inspector UI, make sure these settings are correct:

| Setting | Value (uv) | Value (pip) |
|---------|------------|-------------|
| **Command** | `uv` | `python` |
| **Arguments** | `run excel_server.py` | `excel_server.py` |

Click **"Connect"** or **"Restart"** to connect to the server.

---

## Step 6: Test the Tools in the Inspector

Once connected in the Inspector, try these example queries:

### 1. List Excel Files
- **Tool**: `list_excel_files`
- **Parameters**: (leave empty to use default directory `../excel_files`)

### 2. Get Excel Summary
- **Tool**: `get_excel_summary`
- **Parameters**:
  - `file_path`: `../excel_files/sample_projects.xlsx`

### 3. Extract Content
- **Tool**: `extract_excel_content`
- **Parameters**:
  - `file_path`: `../excel_files/sample_projects.xlsx`

### 4. Query Specific Data
- **Tool**: `query_excel_data`
- **Parameters**:
  - `file_path`: `../excel_files/sample_projects.xlsx`
  - `query`: `projects with high risk`

### 5. Convert to CSV
- **Tool**: `convert_excel_to_csv`
- **Parameters**:
  - `file_path`: `../excel_files/sample_projects.xlsx`
  - `output_dir`: `../excel_files/csv_output`

### 6. Convert to JSON
- **Tool**: `convert_excel_to_json`
- **Parameters**:
  - `file_path`: `../excel_files/sample_projects.xlsx`
  - `output_dir`: `../excel_files/json_output` (optional)
  - `include_metadata`: `true` (optional, includes column types and sheet info)
- **Output**: Creates individual JSON files per sheet + a combined `*_all_sheets.json` file with preview data

---

## OpenSearch Setup (Optional)

For very large Excel files, use OpenSearch for fast indexing and search.

### Step A: Start OpenSearch (Docker - Security Disabled for Demo)

This is the simplest setup for demos. For production, see the Advanced section below.

```bash
docker run -d -p 9200:9200 -e discovery.type=single-node -e plugins.security.disabled=true opensearchproject/opensearch:latest
```

**Wait 30-60 seconds** for OpenSearch to fully start. Check with:
```bash
# Check if OpenSearch is ready
curl http://localhost:9200
```

You should see a JSON response with cluster information.

**Option 2: Local Installation**
Follow [OpenSearch installation guide](https://opensearch.org/downloads.html)

### Step B: Install OpenSearch Python Client

```bash
cd mcp_project
uv add opensearch-py
```

### Step C: Set Environment Variables (Optional)

For the simple demo setup (security disabled), no environment variables are needed:

```bash
# Optional - only if OpenSearch is not on localhost:9200
export OPENSEARCH_HOST=localhost
export OPENSEARCH_PORT=9200
```

**For Production (Security Enabled):**
```bash
export OPENSEARCH_HOST=localhost
export OPENSEARCH_PORT=9200
export OPENSEARCH_SECURITY_ENABLED=true
export OPENSEARCH_USER=admin
export OPENSEARCH_PASSWORD=your_strong_password
```

### Step D: Test OpenSearch Tools in Inspector

**Index an Excel file:**
- **Tool**: `index_excel_in_opensearch`
- **Parameters**:
  - `file_path`: `../excel_files/sample_projects.xlsx`
  - `index_name`: `sample_projects` (optional, auto-derived from filename)

**Search indexed data:**
- **Tool**: `search_excel_opensearch`
- **Parameters**:
  - `query`: `Gulf of Mexico`
  - `index_name`: `sample_projects`
  - `size`: `10` (optional, number of results)

**List all indices:**
- **Tool**: `list_opensearch_indices`
- **Parameters**: (none)

---

### Closing the Inspector

Once you're done testing, close the Inspector by typing **Ctrl+C** in the terminal where you started it.

---

## Troubleshooting

### Issue: "docling is not installed"
**Solution**: Install docling in your virtual environment:
```bash
cd mcp_project
uv add docling  # or: pip install docling
```

### Issue: "File not found" errors
**Solution**: Ensure you're using the correct relative path from the `mcp_project` folder:
- Use `../excel_files/filename.xlsx` instead of `excel_files/filename.xlsx`
- Or set the absolute path: `file_path`: `/full/path/to/excel_files/filename.xlsx`

### Issue: Python version error
**Solution**: MCP requires Python 3.10+. Check your version:
```bash
python3 --version
```
If needed, install Python 3.11:
```bash
# macOS
brew install python@3.11

# From mcp_project folder, recreate venv with Python 3.11
rm -rf .venv
uv venv --python python3.11
```

### Issue: Inspector won't connect
**Solution**:
1. Make sure you're running the Inspector from the `mcp_project` folder
2. Check that Node.js is installed: `node --version`
3. Try specifying the full path to the server file
4. Verify the command and arguments in Inspector settings

### Issue: OpenSearch connection failed
**Solution**:
1. Check OpenSearch is running: `curl http://localhost:9200`
2. Verify environment variables: `echo $OPENSEARCH_HOST`
3. Check Docker container: `docker ps | grep opensearch`

---

## Quick Reference: All Commands

### Setup (one-time)
```bash
# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install Node.js (for Inspector)
brew install node
```

### Project Setup (run from mcp_project folder)
```bash
cd mcp_project
uv init
uv venv
source .venv/bin/activate
uv add mcp docling pandas
```

### Launch Inspector (run from mcp_project folder)
```bash
cd mcp_project
npx @modelcontextprotocol/inspector uv run excel_server.py
```

### Close Inspector
Press **Ctrl+C** in the terminal where the Inspector is running.

### OpenSearch Quick Start
```bash
# Start OpenSearch
docker run -d -p 9200:9200 -e discovery.type=single-node opensearchproject/opensearch:latest

# Install client
cd mcp_project
uv add opensearch-py

# Test connection
curl http://localhost:9200
```

---

## Demo Script for Colleagues

Here's a quick demo flow to show your colleagues:

1. **Create the mcp_project folder and files** manually or using the Jupyter notebook

2. **Show the Problem**: Open the sample Excel file and explain how Copilot struggles with complex Excel structures

3. **Create Sample Data**: Run `python create_sample_data.py` from the root folder

4. **Launch the Inspector**: From `mcp_project/` folder, run:
   ```bash
   npx @modelcontextprotocol/inspector uv run excel_server.py
   ```
   (The Inspector will automatically start the server for you!)

5. **Demo the Tools**:
   - List files: Show how it discovers Excel files
   - Get summary: Show the sheet structure
   - Query data: Ask for "projects with high risk" or "total budget"
   - Extract content: Show the full structured data
   - Convert to JSON: Show the structured JSON output

6. **Optional - Demo OpenSearch** (for large files):
   - Start OpenSearch with Docker
   - Index the Excel file
   - Search: "Gulf of Mexico"
   - Show relevance scoring and highlights

7. **Close the Inspector**: Press Ctrl+C in the terminal

8. **Highlight the Value**: The LLM now gets properly structured data from Excel, enabling accurate analysis and responses

---

## Resources

- [MCP Documentation](https://modelcontextprotocol.io/)
- [FastMCP GitHub](https://github.com/jlowin/fastmcp)
- [Docling Documentation](https://github.com/DS4SD/docling)
- [uv Documentation](https://docs.astral.sh/uv/)
- [MCP Inspector](https://github.com/modelcontextprotocol/inspector)
- [OpenSearch Documentation](https://opensearch.org/docs/)
