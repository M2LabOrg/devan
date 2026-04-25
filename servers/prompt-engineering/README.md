# Prompt MCP Demo - PDF Report Generation

A simplified **Model Context Protocol (MCP)** server demonstrating the prompt engineering patterns for generating executive summaries and introductions from PDF reports.

## What This Teaches

This demo illustrates how MCP servers can encapsulate **structured prompt engineering**:

- **Instruction**: Role definition and task specification
- **Additional Context**: Background information and guidelines
- **Constraints**: Format, tone, and delivery requirements

## The Use Case

**Input**: PDF file (reports, proposals, technical memos)

**Output**: Executive summary or introduction following industry guidelines

**Example Workflow**:
1. Upload a 50-page technical report PDF
2. Server extracts the content
3. Server constructs a M2Lab-formatted prompt
4. LLM generates executive summary with 5 bullets, max 300 words, professional tone

## Quick Start

1. **Open the Jupyter Notebook**:
   ```bash
   jupyter notebook demo_notebook.ipynb
   ```

2. **Or follow the Markdown instructions**:
   - Read `demo_instructions.md` for step-by-step setup

## Tools (7 Total)

### PDF Processing
- **list_pdf_files** - Discover PDF files in directory
- **extract_pdf_content** - Extract text using docling or PyPDF2
- **analyze_pdf_structure** - Analyze document pages, sections, word count

### Prompt Management
- **list_prompt_templates** - Show available M2Lab prompt templates
- **get_prompt_template** - Retrieve a specific template (instruction + context + constraints)

### Report Generation
- **generate_executive_summary** - Auto-generate prompt with PDF content for executive summary
- **generate_introduction** - Auto-generate prompt with PDF content for introduction
- **create_custom_prompt** - Build custom prompts with your own components

## Folder Structure

```
prompt_mcp_demo/
├── mcp_project/              # MCP server code
│   ├── prompt_server.py      # Main server (7 tools)
│   └── pyproject.toml        # Dependencies
├── pdf_files/                # Your PDF files go here
├── create_sample_pdfs.py     # Generate sample PDFs
├── demo_notebook.ipynb       # Interactive tutorial
├── demo_instructions.md      # Step-by-step guide
└── README.md                # This file
```

## Prerequisites

- **uv** or **pip** with Python 3.10+
- **Node.js** (for MCP Inspector)

## Setup in 3 Steps

```bash
# 1. Create mcp_project folder and files (via notebook or manual)

# 2. Install dependencies (from mcp_project folder)
cd mcp_project
uv init
uv venv
source .venv/bin/activate
uv add mcp docling

# 3. Create sample PDFs (from root folder)
cd ..
python create_sample_pdfs.py  # Requires: uv add reportlab
```

## Running the Server

```bash
cd mcp_project
npx @modelcontextprotocol/inspector uv run prompt_server.py
```

Open the displayed URL in your browser.

## Example Usage in Inspector

### List Available Templates
- **Tool**: `list_prompt_templates`
- **Parameters**: (empty)

### View a Template
- **Tool**: `get_prompt_template`
- **Parameters**:
  - `template_name`: `executive_summary`

### Generate Executive Summary
- **Tool**: `generate_executive_summary`
- **Parameters**:
  - `file_path`: `../pdf_files/offshore_wind_assessment.pdf`

### Extract PDF Content
- **Tool**: `extract_pdf_content`
- **Parameters**:
  - `file_path**: `../pdf_files/pipeline_safety_proposal.pdf`

## Prompt Structure

All templates follow this format:

```
Instruction:
You are a technical engineer. Write an executive summary for the following report...

Additional Context:
This executive summary follows industry guidelines for technical reports...

[Document Content Extracted from PDF]

Constraints:
- 5 bullet points maximum
- Maximum 300 words
- Tone: professional and authoritative
- Audience: managers and executives at energy companies
```

## Available Templates

| Template | Use Case | Format |
|----------|----------|--------|
| `executive_summary` | Final reports, management briefings | 5 bullets, 300 words max |
| `introduction` | Proposals, project kickoffs | 3-4 paragraphs, 250 words max |
| `technical_summary` | Engineering reviews, peer reviews | 4-6 bullets, 400 words max, technical |

## Sample PDFs Created

- `offshore_wind_assessment.pdf` - Multi-page technical report
- `pipeline_safety_proposal.pdf` - Business proposal
- `fatigue_analysis_memo.pdf` - Short technical memorandum

## Key Concepts for Learning

### Why Structured Prompts?

the prompt engineering separates concerns:
- **Instruction**: Defines WHO (M2Lab Engineer) and WHAT (write summary)
- **Context**: Provides WHY (guidelines) and HOW (approach)
- **Constraints**: Sets BOUNDARIES (format, length, tone)

This structure ensures consistent, high-quality outputs that align with standard formats.

### MCP Value

The server encapsulates:
1. PDF extraction (technical complexity hidden)
2. Prompt construction (M2Lab expertise encoded)
3. Template management (reusable patterns)

Users just provide a PDF and get a ready-to-use prompt.

## Documentation

- **Interactive Tutorial**: `demo_notebook.ipynb`
- **Step-by-Step Guide**: `demo_instructions.md`

## Troubleshooting

**"reportlab not installed"** (for creating sample PDFs)
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

## Next Steps

- Experiment with different templates
- Add your own PDF files to pdf_files/
- Modify the templates in prompt_server.py for your use cases
- Build custom prompts with `create_custom_prompt`

## Resources

- [MCP Documentation](https://modelcontextprotocol.io/)
- [ReportLab PDF Generation](https://www.reportlab.com/docs/reportlab-userguide.pdf)
- 
