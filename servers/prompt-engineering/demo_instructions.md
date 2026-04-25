# Prompt MCP Demo - Instructions

This guide walks you through setting up and using the **Prompt MCP Server** for teaching the prompt engineering patterns.

## What You'll Learn

- How MCP servers encapsulate prompt engineering expertise
- M2Lab's structured prompt format: Instruction + Context + Constraints
- Automating report generation from PDF documents
- Managing reusable prompt templates

## Prerequisites

You need either **uv** (recommended) or **pip** installed.

### Install uv (macOS/Linux)
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### Install uv (Windows)
```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

## Step 1: Create the MCP Project Folder

Create a folder to isolate the server code:

```bash
mkdir -p mcp_project
```

## Step 2: Create Server Files

### Create `mcp_project/prompt_server.py`

Copy the server code from the provided `prompt_server.py` file. Key components:
- FastMCP server setup
- PDF extraction using docling or PyPDF2
- M2Lab prompt templates (Instruction + Context + Constraints)
- Tools for generating prompts from PDFs

### Create `mcp_project/pyproject.toml`

```toml
[project]
name = "prompt-mcp-demo"
version = "0.1.0"
description = "MCP Server for PDF report generation using M2Lab prompt engineering"
requires-python = ">=3.10"
dependencies = [
    "mcp>=1.26.0",
    "docling>=2.0.0",
]
```

## Step 3: Set Up Environment

Navigate to the mcp_project folder and set up:

```bash
cd mcp_project

# Initialize project
uv init

# Create virtual environment
uv venv

# Activate environment
source .venv/bin/activate  # macOS/Linux
# .venv\Scripts\activate   # Windows

# Install dependencies
uv add mcp docling

# Optional: Install reportlab for creating sample PDFs
uv add reportlab
```

## Step 4: Create Sample PDFs

From the root folder (where create_sample_pdfs.py is):

```bash
python create_sample_pdfs.py
```

This creates:
- `pdf_files/offshore_wind_assessment.pdf` (multi-page technical report)
- `pdf_files/pipeline_safety_proposal.pdf` (business proposal)
- `pdf_files/fatigue_analysis_memo.pdf` (short technical memo)

## Step 5: Launch MCP Inspector

The Inspector is a UI tool for testing MCP servers. **Important:** Run from mcp_project folder.

```bash
cd mcp_project
npx @modelcontextprotocol/inspector uv run prompt_server.py
```

You'll see a URL like `http://localhost:5173`. Open it in your browser.

## Step 6: Test the Tools

### Tool 1: List Available Templates
- **Tool**: `list_prompt_templates`
- **Parameters**: (empty)
- **What you see**: Available templates (executive_summary, introduction, technical_summary)

### Tool 2: Get a Template
- **Tool**: `get_prompt_template`
- **Parameters**:
  - `template_name`: `executive_summary`
- **What you see**: Full prompt structure with Instruction, Additional Context, and Constraints

### Tool 3: Generate Executive Summary Prompt
- **Tool**: `generate_executive_summary`
- **Parameters**:
  - `file_path`: `../pdf_files/offshore_wind_assessment.pdf`
- **What you see**: Constructed prompt with extracted PDF content ready for LLM processing

### Tool 4: Analyze PDF Structure
- **Tool**: `analyze_pdf_structure`
- **Parameters**:
  - `file_path`: `../pdf_files/pipeline_safety_proposal.pdf`
- **What you see**: Page count, word count, detected sections, content preview

### Tool 5: Extract PDF Content
- **Tool**: `extract_pdf_content`
- **Parameters**:
  - `file_path`: `../pdf_files/fatigue_analysis_memo.pdf`
- **What you see**: Raw text content extracted from the PDF

### Tool 6: Generate Introduction
- **Tool**: `generate_introduction`
- **Parameters**:
  - `file_path`: `../pdf_files/pipeline_safety_proposal.pdf`
- **What you see**: Constructed prompt for writing an introduction section

### Tool 7: Create Custom Prompt
- **Tool**: `create_custom_prompt`
- **Parameters**:
  - `instruction`: `You are a safety engineer reviewing...`
  - `additional_context`: `This review is for a North Sea platform...`
  - `constraints`: `- 3 bullet points\n- Max 200 words\n- Tone: cautionary`
  - `file_path`: `../pdf_files/offshore_wind_assessment.pdf` (optional)
- **What you see**: Custom constructed prompt with your components

## Understanding Prompt Structure

### The Three Components

1. **Instruction** - WHO and WHAT
   - Defines the role ("You are a technical engineer")
   - States the task ("Write an executive summary")

2. **Additional Context** - WHY and HOW
   - Background information
   - Guidelines and standards
   - Expected approach

3. **Constraints** - BOUNDARIES
   - Format requirements
   - Length limits
   - Tone and audience

### Example Breakdown

```
Instruction:
You are a technical engineer. Write an executive summary for the following report.
The executive summary should capture the key findings, recommendations, 
and business impact.

Additional Context:
This executive summary follows industry guidelines for technical reports.
It should be concise, professional, and actionable for decision-makers.
The summary should highlight critical insights that require management attention.

[PDF Content Inserted Here]

Constraints:
- 5 bullet points maximum
- Maximum 300 words
- Tone: professional and authoritative
- Audience: managers and executives at energy companies
- Focus on business impact and actionable recommendations
```

## Why This Matters

### Consistency
All M2Lab reports follow the same high-quality standard, regardless of who writes them.

### Efficiency
Engineers don't need to remember prompt best practices - they're encoded in the server.

### Quality
Constraints ensure outputs meet professional standards.

### Reusability
Templates can be reused across projects and teams.

## Teaching Points

### For Students Learning MCP
- Servers encapsulate domain expertise
- Tools hide technical complexity (PDF extraction)
- Prompt engineering becomes reusable infrastructure

### For Prompt Engineering Training
- Structure matters: Instruction → Context → Constraints
- Each component serves a specific purpose
- Constraints are as important as instructions

### For M2Lab Workflows
- PDF reports → Structured prompts → LLM generation
- Quality control through encoded constraints
- Scalable across teams and projects

## Troubleshooting

**"reportlab not installed"** (for sample PDFs)
```bash
cd mcp_project
uv add reportlab
cd ..
python create_sample_pdfs.py
```

**"docling not installed"**
```bash
cd mcp_project
uv add docling
```

**Inspector won't connect**
- Ensure you're in the mcp_project folder
- Check Node.js: `node --version`
- Verify the server file exists

**PDF extraction fails**
- Check file path: use `../pdf_files/file.pdf` from mcp_project
- Ensure PDF exists: run `python create_sample_pdfs.py` first

## Quick Reference

| Task | Tool | Key Parameters |
|------|------|---------------|
| List templates | `list_prompt_templates` | (none) |
| Get template | `get_prompt_template` | `template_name` |
| Generate summary | `generate_executive_summary` | `file_path` |
| Generate intro | `generate_introduction` | `file_path` |
| Analyze PDF | `analyze_pdf_structure` | `file_path` |
| Extract content | `extract_pdf_content` | `file_path` |
| Custom prompt | `create_custom_prompt` | `instruction`, `additional_context`, `constraints` |

## Next Steps

1. **Experiment with different PDFs** - Add your own reports
2. **Modify templates** - Edit PROMPT_TEMPLATES in the server
3. **Add new templates** - Create templates for other use cases
4. **Integrate with LLMs** - Use the constructed prompts with GPT-4, Claude, etc.

## Resources

- [MCP Docs](https://modelcontextprotocol.io/)
- [Docling GitHub](https://github.com/DS4SD/docling)
- [ReportLab PDF Generation](https://www.reportlab.com/)
