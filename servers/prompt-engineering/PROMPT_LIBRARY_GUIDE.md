# Prompt Library System

## Overview

The Prompt MCP Server now includes a comprehensive **Prompt Library System** that allows users to:

1. ✅ Create custom prompts with the structured format
2. ✅ Normalize any freeform prompt to standard format
3. ✅ Save prompts to a shared library for reuse
4. ✅ Load and share prompts across teams
5. ✅ Support optional INPUT/OUTPUT sections

---

## Prompt Structure

M2Lab uses a structured prompt format with the following sections:

```
INSTRUCTION:
[Role and task definition]

ADDITIONAL CONTEXT:
[Guidelines, standards, and background]

INPUT: (optional)
[Expected input format]

DOCUMENT CONTENT: (optional)
[Actual content to process]

OUTPUT: (optional)
[Expected output format]

CONSTRAINTS:
[Format, style, and requirements]
```

### Core Sections (Always Present)
- **INSTRUCTION** — Defines the role and main task
- **ADDITIONAL CONTEXT** — Provides guidelines and standards
- **CONSTRAINTS** — Specifies format and style requirements

### Optional Sections
- **INPUT** — Describes expected input format (when needed)
- **OUTPUT** — Describes expected output format (when needed)
- **DOCUMENT CONTENT** — Actual content to process (for PDF extraction workflows)

---

## New Features

### 1. Enhanced Custom Prompt (`@mcp.prompt`)

The `custom_prompt` now supports INPUT and OUTPUT sections:

```python
custom_prompt(
    instruction="You are a safety engineer...",
    additional_context="This is for offshore wind assessments...",
    constraints="- 3 bullet points\n- Max 200 words",
    input_format="PDF report with safety data",
    output_format="JSON with risk scores",
    document_content="[PDF content here]"
)
```

**Output:**
```
INSTRUCTION:
You are a safety engineer...

ADDITIONAL CONTEXT:
This is for offshore wind assessments...

INPUT:
PDF report with safety data

DOCUMENT CONTENT:
[PDF content here]

OUTPUT:
JSON with risk scores

CONSTRAINTS:
- 3 bullet points
- Max 200 words
```

---

### 2. Prompt Normalization (`normalize_prompt_format`)

**Problem:** Users may write prompts in different formats (freeform, markdown, etc.)

**Solution:** Auto-detect sections and normalize to standard format

#### Example 1: Auto-Detection Enabled

**Input (freeform prompt):**
```
You are a technical engineer reviewing technical reports.

Context: This is for annual compliance reviews.

Output: Executive summary with key findings

Constraints:
- Maximum 5 bullet points
- Professional tone
```

**Output (normalized):**
```json
{
  "normalized_prompt": "INSTRUCTION:\nYou are a technical engineer reviewing technical reports.\n\nADDITIONAL CONTEXT:\nThis is for annual compliance reviews.\n\nOUTPUT:\nExecutive summary with key findings\n\nCONSTRAINTS:\n- Maximum 5 bullet points\n- Professional tone",
  "detected_sections": {
    "instruction": true,
    "additional_context": true,
    "input": false,
    "output": true,
    "constraints": true
  }
}
```

#### Example 2: Auto-Detection Disabled

**Input:**
```
Write a risk assessment for offshore platforms
```

**Output:**
```json
{
  "normalized_prompt": "INSTRUCTION:\nWrite a risk assessment for offshore platforms\n\nADDITIONAL CONTEXT:\n(To be filled in)\n\nCONSTRAINTS:\n(To be filled in)",
  "detected_sections": {"instruction": "Write a risk assessment..."},
  "note": "Auto-detection disabled. Entire text treated as INSTRUCTION."
}
```

---

### 3. Prompt Library Management

#### Save Prompt to Library

```python
save_prompt_to_library(
    prompt_name="risk_assessment_summary",
    instruction="You are a risk engineer...",
    additional_context="This follows industry RP guidelines...",
    constraints="- 4-6 bullet points\n- Technical tone",
    input_format="Risk assessment report (PDF)",
    output_format="Executive summary with risk matrix",
    description="Generate executive summary for risk assessments",
    use_case="Offshore wind, oil & gas risk reviews",
    author="Safety Team",
    normalize_first=False  # Set to True to auto-normalize
)
```

**Saved as:** `../prompt_library/risk_assessment_summary.json`

```json
{
  "name": "risk_assessment_summary",
  "description": "Generate executive summary for risk assessments",
  "use_case": "Offshore wind, oil & gas risk reviews",
  "author": "Safety Team",
  "created_at": "2024-03-30T12:30:00",
  "prompt_format": {
    "instruction": "You are a risk engineer...",
    "additional_context": "This follows industry RP guidelines...",
    "input": "Risk assessment report (PDF)",
    "output": "Executive summary with risk matrix",
    "constraints": "- 4-6 bullet points\n- Technical tone"
  }
}
```

#### Load Prompt from Library

```python
load_prompt_from_library("risk_assessment_summary")
```

Returns the full prompt structure as JSON.

#### List All Prompts

```python
list_prompt_library()
```

**Output:**
```json
{
  "library_path": "../prompt_library",
  "total_prompts": 3,
  "prompts": [
    {
      "name": "risk_assessment_summary",
      "description": "Generate executive summary for risk assessments",
      "use_case": "Offshore wind, oil & gas risk reviews",
      "author": "Safety Team",
      "created_at": "2024-03-30T12:30:00"
    },
    {
      "name": "compliance_report",
      "description": "Annual compliance report generator",
      "use_case": "Regulatory compliance reviews",
      "author": "Compliance Team",
      "created_at": "2024-03-29T10:15:00"
    }
  ]
}
```

---

## Workflow Examples

### Workflow 1: Create and Save Custom Prompt

```bash
# Step 1: Create a custom prompt
custom_prompt(
    instruction="You are a structural engineer...",
    additional_context="This is for offshore platform inspections...",
    constraints="- 5 key findings\n- Technical language",
    input_format="Inspection report with photos",
    output_format="Structured JSON with severity scores"
)

# Step 2: Save to library
save_prompt_to_library(
    prompt_name="structural_inspection_summary",
    instruction="You are a structural engineer...",
    additional_context="This is for offshore platform inspections...",
    constraints="- 5 key findings\n- Technical language",
    input_format="Inspection report with photos",
    output_format="Structured JSON with severity scores",
    description="Summarize structural inspection findings",
    use_case="Offshore platform inspections",
    author="Structural Team"
)
```

### Workflow 2: Normalize and Save Freeform Prompt

```bash
# Step 1: User writes freeform prompt
freeform_prompt = """
You are a technical engineer analyzing vessel performance data.

Context: This is for annual fleet performance reviews.

Input: CSV files with fuel consumption and speed data

Output: Performance report with efficiency metrics

Requirements:
- Include year-over-year comparison
- Highlight top 3 performers and bottom 3
- Professional tone for management
"""

# Step 2: Normalize to standard format
normalize_prompt_format(freeform_prompt, auto_detect=True)

# Step 3: Review normalized output, then save
save_prompt_to_library(
    prompt_name="fleet_performance_analysis",
    instruction="You are a technical engineer analyzing vessel performance data.",
    additional_context="This is for annual fleet performance reviews.",
    constraints="- Include year-over-year comparison\n- Highlight top 3 performers and bottom 3\n- Professional tone for management",
    input_format="CSV files with fuel consumption and speed data",
    output_format="Performance report with efficiency metrics",
    description="Analyze fleet performance data",
    use_case="Annual fleet reviews",
    author="Maritime Team"
)
```

### Workflow 3: Use Prompt from Library with PDF

```bash
# Step 1: Load prompt from library
prompt_data = load_prompt_from_library("risk_assessment_summary")

# Step 2: Extract PDF content
pdf_content = get_pdf_content_for_prompt("reports/offshore_risk_2024.pdf")

# Step 3: Use the prompt (MCP client invokes the prompt)
# The prompt template automatically includes the PDF content
```

---

## Best Practices

### 1. Consistency Through Normalization

**✅ Recommended:** Always normalize prompts before saving to library

```python
save_prompt_to_library(
    ...,
    normalize_first=True  # Auto-normalize freeform text
)
```

**Why:** Ensures all prompts in the library follow the standard structure.

### 2. When to Use INPUT/OUTPUT Sections

**Use INPUT when:**
- The prompt expects specific data formats (CSV, JSON, PDF)
- You need to specify data structure or schema
- Input validation is important

**Use OUTPUT when:**
- You need structured output (JSON, tables, specific formats)
- Output format is critical for downstream processing
- You want to enforce consistency

**Skip INPUT/OUTPUT when:**
- Working with simple text-to-text transformations
- Format is obvious from context
- Maximum flexibility is desired

### 3. Library Organization

**Naming Convention:**
- Use descriptive names: `risk_assessment_summary`, not `prompt1`
- Use underscores: `fleet_performance_analysis`
- Be specific: `offshore_wind_safety_review` vs. `safety_review`

**Metadata:**
- Always fill in `description` and `use_case`
- Include `author` for team prompts
- Update prompts with new versions (delete old, save new)

### 4. Hybrid Approach: Accept Any Format, Normalize on Save

**Philosophy:** Be flexible with input, strict with storage

```python
# Accept freeform prompt from user
user_prompt = "Write a summary of this technical report..."

# Normalize before saving
normalize_prompt_format(user_prompt, auto_detect=True)

# Review and adjust, then save with M2Lab structure
save_prompt_to_library(...)
```

**Benefits:**
- Users can write naturally
- Library maintains consistency
- Easy to share and reuse

---

## Configuration

### Environment Variables

```bash
# Set custom prompt library location
export PROMPT_LIBRARY_DIR="/shared/prompts"

# Set PDF directory
export PDF_DIR="/data/pdf_files"
```

### Default Locations

- Prompt Library: `../prompt_library/`
- PDF Files: `../pdf_files/`

---

## MCP Resources

Resources provide **read-only access** to data (similar to GET endpoints in REST APIs). They allow clients to browse and discover available content without executing tools.

### Available Resources

| Resource URI | Description | Usage |
|-------------|-------------|-------|
| `pdf://files` | List all PDF files in the PDF directory | `@pdf://files` |
| `prompts://library` | Browse all prompts in the library | `@prompts://library` |
| `prompts://{prompt_name}` | Get detailed info about a specific prompt | `@prompts://risk_assessment` |

### How to Use Resources

**In MCP Clients (like Claude Desktop):**
```
@pdf://files                    # List all available PDFs
@prompts://library              # Browse prompt library
@prompts://risk_assessment      # View specific prompt details
```

**What Resources Provide:**
- 📄 **PDF Files** — Browse available PDFs with sizes and paths
- 📚 **Prompt Library** — See all saved prompts with metadata
- 🔍 **Prompt Details** — View full structure of any saved prompt

**Benefits:**
- No tool execution needed
- Fast browsing and discovery
- Formatted markdown output
- Direct integration with MCP clients

---

## API Reference

### MCP Prompts

| Prompt | Parameters | Description |
|--------|-----------|-------------|
| `generate_executive_summary` | `pdf_content` | Executive summary for reports |
| `generate_introduction` | `pdf_content` | Introduction for proposals |
| `generate_technical_summary` | `pdf_content` | Technical summary for engineering docs |
| `custom_prompt` | `instruction`, `additional_context`, `constraints`, `input_format`, `output_format`, `document_content` | Custom prompt with full M2Lab structure |

### MCP Tools

| Tool | Parameters | Description |
|------|-----------|-------------|
| `normalize_prompt_format` | `prompt_text`, `auto_detect` | Normalize any prompt to standard format |
| `save_prompt_to_library` | `prompt_name`, `instruction`, `additional_context`, `constraints`, `input_format`, `output_format`, `description`, `use_case`, `author`, `normalize_first` | Save prompt to library |
| `load_prompt_from_library` | `prompt_name` | Load prompt from library |
| `list_prompt_library` | - | List all prompts in library |
| `get_pdf_content_for_prompt` | `file_path` | Extract PDF content for prompts |
| `list_available_prompts` | - | List built-in prompt templates |

---

## FAQ

**Q: Should we normalize all prompts before adding to the library?**

**A:** Yes, recommended. Use `normalize_first=True` or manually normalize with `normalize_prompt_format()` before saving. This ensures consistency.

**Q: What if a user doesn't use the expected syntax?**

**A:** The `normalize_prompt_format()` tool auto-detects sections and restructures the prompt. Review the output and adjust as needed before saving.

**Q: Can we use meta-prompting for different prompt styles?**

**A:** The current implementation uses heuristic-based detection (looking for keywords like "instruction:", "context:", etc.). For more advanced meta-prompting, you could:
1. Use an LLM to analyze and restructure prompts
2. Provide examples of standard format in the normalization prompt
3. Let users choose between strict normalization or flexible acceptance

**Q: Do we need INPUT/OUTPUT sections for all prompts?**

**A:** No, they're optional. Use them when:
- Input/output format is critical
- You need structured data
- Downstream processing requires specific formats

For simple text transformations, INSTRUCTION + CONTEXT + CONSTRAINTS is sufficient.

**Q: How do we share prompts across teams?**

**A:** Set `PROMPT_LIBRARY_DIR` to a shared network location:
```bash
export PROMPT_LIBRARY_DIR="/shared/prompts"
```

All teams can then save/load from the same library.

---

## Summary

The Prompt Library System provides:

✅ **Structured Format** — INSTRUCTION → CONTEXT → INPUT → OUTPUT → CONSTRAINTS  
✅ **Flexibility** — Accept any format, normalize to standard  
✅ **Reusability** — Save and share prompts across teams  
✅ **Consistency** — All library prompts follow standard format  
✅ **Optional Sections** — INPUT/OUTPUT when needed  

**Recommended Approach:** Hybrid model
- Accept freeform prompts from users
- Normalize to standard format with `normalize_prompt_format()`
- Review and save to library with `save_prompt_to_library()`
- Maintain consistency while allowing flexibility
