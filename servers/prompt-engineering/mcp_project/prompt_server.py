"""
MCP Server for PDF Report Generation - Prompt Engineering Demo

This server demonstrates how MCP servers can encapsulate prompt engineering patterns.
It extracts content from PDFs and generates executive summaries/introductions
following a structured prompt format:
- Instruction
- Additional Context  
- Constraints

Perfect for teaching prompt engineering.
"""

import json
import os
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
from mcp.server.fastmcp import FastMCP

# PDF processing imports
try:
    from docling.document_converter import DocumentConverter
    from docling.datamodel.base_models import InputFormat
    DOCLING_AVAILABLE = True
except ImportError:
    DOCLING_AVAILABLE = False

try:
    import PyPDF2
    PYPDF2_AVAILABLE = True
except ImportError:
    PYPDF2_AVAILABLE = False

# Default directory for PDF files
PDF_DIR = os.environ.get("PDF_DIR", "../pdf_files")

# Prompt library directory
PROMPT_LIBRARY_DIR = os.environ.get("PROMPT_LIBRARY_DIR", "../prompt_library")

# Initialize FastMCP server
mcp = FastMCP("prompt-mcp-demo")

# Initialize docling converter
_converter: Optional[DocumentConverter] = None

def get_converter() -> DocumentConverter:
    """Get or create the DocumentConverter instance."""
    global _converter
    if _converter is None:
        _converter = DocumentConverter()
    return _converter


# Prompt Templates
PROMPT_TEMPLATES = {
    "executive_summary": {
        "instruction": """You are a technical engineer. Write an executive summary for the following report.
The executive summary should capture the key findings, recommendations, and business impact.""",
        "additional_context": """This executive summary follows industry guidelines for technical reports.
It should be concise, professional, and actionable for decision-makers.
The summary should highlight critical insights that require management attention.""",
        "constraints": """Format your response with:
- 5 bullet points maximum
- Maximum 300 words
- Tone: professional and authoritative
- Audience: managers and executives at energy companies
- Focus on business impact and actionable recommendations"""
    },
    "introduction": {
        "instruction": """You are a technical engineer. Write an introduction section for the following proposal/report.
The introduction should set the context and outline the purpose of the document.""",
        "additional_context": """This introduction follows standard proposal structure.
It should establish credibility, define the scope, and preview the document structure.
The introduction prepares the reader for the detailed technical content that follows.""",
        "constraints": """Format your response with:
- 3-4 paragraphs
- Maximum 250 words
- Tone: professional and informative
- Audience: technical managers and stakeholders
- Include: background, scope, and document overview"""
    },
    "technical_summary": {
        "instruction": """You are a technical engineer. Write a technical summary of the following document.
Focus on the engineering analysis, methodologies, and technical findings.""",
        "additional_context": """This technical summary is for engineering peers and technical reviewers.
It should explain the technical approach, key findings, and engineering implications.
The summary bridges detailed analysis with practical application.""",
        "constraints": """Format your response with:
- 4-6 bullet points
- Maximum 400 words
- Tone: technical but accessible
- Audience: engineering managers and technical specialists
- Include: methodology overview, key technical findings, and recommendations"""
    }
}


@mcp.tool()
def list_pdf_files(directory: Optional[str] = None) -> str:
    """
    List all PDF files in the specified directory.
    
    Args:
        directory: Path to directory containing PDF files.
                    Defaults to PDF_DIR environment variable or '../pdf_files'.
        
    Returns:
        JSON string with list of PDF files and their metadata.
    """
    search_dir = directory or PDF_DIR
    
    if not os.path.exists(search_dir):
        return json.dumps({
            "error": f"Directory not found: {search_dir}",
            "hint": "Create the directory or set PDF_DIR environment variable"
        }, indent=2)
    
    files = []
    for item in os.listdir(search_dir):
        if item.lower().endswith('.pdf'):
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
def extract_pdf_content(file_path: str) -> str:
    """
    Extract text content from a PDF file.
    
    Uses docling if available, falls back to PyPDF2.
    
    Args:
        file_path: Path to the PDF file
        
    Returns:
        JSON string with extracted text content.
    """
    if not os.path.exists(file_path):
        return json.dumps({
            "error": f"File not found: {file_path}"
        }, indent=2)
    
    try:
        # Try docling first
        if DOCLING_AVAILABLE:
            converter = get_converter()
            result = converter.convert(file_path)
            
            extracted_data = {
                "file_path": file_path,
                "file_name": os.path.basename(file_path),
                "extraction_method": "docling",
                "pages": len(result.pages) if hasattr(result, 'pages') else 0,
                "content": result.document.export_to_text(),
                "markdown": result.document.export_to_markdown()
            }
            return json.dumps(extracted_data, indent=2)
        
        # Fallback to PyPDF2
        elif PYPDF2_AVAILABLE:
            with open(file_path, 'rb') as f:
                reader = PyPDF2.PdfReader(f)
                text = ""
                for page in reader.pages:
                    text += page.extract_text() + "\n\n"
                
                extracted_data = {
                    "file_path": file_path,
                    "file_name": os.path.basename(file_path),
                    "extraction_method": "PyPDF2",
                    "pages": len(reader.pages),
                    "content": text
                }
                return json.dumps(extracted_data, indent=2)
        
        else:
            return json.dumps({
                "error": "No PDF extraction library installed",
                "setup_instructions": [
                    "Install docling: uv add docling",
                    "Or install PyPDF2: uv add PyPDF2"
                ]
            }, indent=2)
    
    except Exception as e:
        return json.dumps({
            "error": f"Failed to extract content: {str(e)}",
            "file_path": file_path
        }, indent=2)


# ─── MCP Prompt Templates ───────────────────────────────────────────────────
# Using @mcp.prompt() decorator for proper MCP prompt template exposure

@mcp.prompt()
def generate_executive_summary(pdf_content: str) -> str:
    """
    Generate an executive summary for a technical report.
    
    This prompt follows the structured prompt format:
    - Instruction: Role and task definition
    - Additional Context: Guidelines and standards
    - Constraints: Format and style requirements
    
    Args:
        pdf_content: The extracted content from the PDF report
        
    Returns:
        A structured prompt ready for LLM processing
    """
    template = PROMPT_TEMPLATES["executive_summary"]
    
    return f"""INSTRUCTION:
{template['instruction']}

ADDITIONAL CONTEXT:
{template['additional_context']}

DOCUMENT CONTENT:
{pdf_content[:8000]}

CONSTRAINTS:
{template['constraints']}

Please generate the executive summary based on the above document content."""


@mcp.prompt()
def generate_introduction(pdf_content: str) -> str:
    """
    Generate an introduction section for a proposal or report.
    
    This prompt follows the structured prompt format for introductions.
    
    Args:
        pdf_content: The extracted content from the PDF document
        
    Returns:
        A structured prompt ready for LLM processing
    """
    template = PROMPT_TEMPLATES["introduction"]
    
    return f"""INSTRUCTION:
{template['instruction']}

ADDITIONAL CONTEXT:
{template['additional_context']}

DOCUMENT CONTENT:
{pdf_content[:8000]}

CONSTRAINTS:
{template['constraints']}

Please generate the introduction based on the above document content."""


@mcp.prompt()
def generate_technical_summary(pdf_content: str) -> str:
    """
    Generate a technical summary for an engineering document.
    
    This prompt focuses on technical analysis and engineering findings.
    
    Args:
        pdf_content: The extracted content from the PDF document
        
    Returns:
        A structured prompt ready for LLM processing
    """
    template = PROMPT_TEMPLATES["technical_summary"]
    
    return f"""INSTRUCTION:
{template['instruction']}

ADDITIONAL CONTEXT:
{template['additional_context']}

DOCUMENT CONTENT:
{pdf_content[:8000]}

CONSTRAINTS:
{template['constraints']}

Please generate the technical summary based on the above document content."""


@mcp.prompt()
def custom_prompt(
    instruction: str,
    additional_context: str,
    constraints: str = "",
    document_content: str = "",
    input_format: str = "",
    output_format: str = ""
) -> str:
    """
    Create a custom custom structured prompt with your own components.
    
    This allows you to build custom prompts following the structured prompt format:
    INSTRUCTION → ADDITIONAL CONTEXT → INPUT → DOCUMENT CONTENT → OUTPUT → CONSTRAINTS
    
    Args:
        instruction: The main instruction (e.g., "You are a technical engineer...")
        additional_context: Context about the task and guidelines
        constraints: Optional format and style constraints
        document_content: Optional document content to include
        input_format: Optional INPUT section describing expected input format
        output_format: Optional OUTPUT section describing expected output format
        
    Returns:
        A structured custom prompt ready for LLM processing
    """
    prompt_parts = ["INSTRUCTION:", instruction, "\nADDITIONAL CONTEXT:", additional_context]
    
    if input_format:
        prompt_parts.extend(["\nINPUT:", input_format])
    
    if document_content:
        prompt_parts.extend(["\nDOCUMENT CONTENT:", document_content[:8000]])
    
    if output_format:
        prompt_parts.extend(["\nOUTPUT:", output_format])
    
    if constraints:
        prompt_parts.extend(["\nCONSTRAINTS:", constraints])
    
    return "\n".join(prompt_parts)


# ─── MCP Resources ──────────────────────────────────────────────────────────
# Resources provide read-only access to data (like GET endpoints in REST API)

@mcp.resource("pdf://files")
def get_available_pdfs() -> str:
    """
    List all available PDF files in the PDF directory.
    
    This resource provides a browsable list of all PDFs that can be processed.
    """
    if not os.path.exists(PDF_DIR):
        return "# No PDF Directory\n\nThe PDF directory does not exist. Please create it or set PDF_DIR environment variable."
    
    pdf_files = []
    for item in os.listdir(PDF_DIR):
        if item.lower().endswith('.pdf'):
            file_path = os.path.join(PDF_DIR, item)
            try:
                stat = os.stat(file_path)
                size_mb = stat.st_size / (1024 * 1024)
                pdf_files.append({
                    "name": item,
                    "size_mb": round(size_mb, 2),
                    "path": file_path
                })
            except OSError:
                pass
    
    # Create markdown content
    content = "# Available PDF Files\n\n"
    if pdf_files:
        content += f"Total PDFs: {len(pdf_files)}\n\n"
        for pdf in pdf_files:
            content += f"- **{pdf['name']}** ({pdf['size_mb']} MB)\n"
            content += f"  - Path: `{pdf['path']}`\n"
        content += f"\n💡 Use `get_pdf_content_for_prompt(file_path)` to extract content from any PDF.\n"
    else:
        content += "No PDF files found.\n"
    
    return content


@mcp.resource("prompts://library")
def get_prompt_library_resource() -> str:
    """
    Browse all prompts in the prompt library.
    
    This resource provides a formatted view of all saved prompts with their metadata.
    """
    if not os.path.exists(PROMPT_LIBRARY_DIR):
        return "# Prompt Library Empty\n\nNo prompts have been saved yet. Use `save_prompt_to_library()` to add prompts."
    
    prompts = []
    for filename in os.listdir(PROMPT_LIBRARY_DIR):
        if filename.endswith('.json'):
            file_path = os.path.join(PROMPT_LIBRARY_DIR, filename)
            try:
                with open(file_path, 'r') as f:
                    prompt_data = json.load(f)
                    prompts.append(prompt_data)
            except Exception:
                pass
    
    # Create markdown content
    content = "# Prompt Library\n\n"
    if prompts:
        content += f"Total prompts: {len(prompts)}\n\n"
        for prompt in prompts:
            content += f"## {prompt.get('name', 'Unnamed')}\n"
            content += f"- **Description**: {prompt.get('description', 'N/A')}\n"
            content += f"- **Use Case**: {prompt.get('use_case', 'N/A')}\n"
            content += f"- **Author**: {prompt.get('author', 'N/A')}\n"
            content += f"- **Created**: {prompt.get('created_at', 'N/A')}\n"
            
            prompt_format_data = prompt.get('prompt_format', {})
            content += f"\n**Sections included:**\n"
            if prompt_format_data.get('instruction'):
                content += f"  - ✓ INSTRUCTION\n"
            if prompt_format_data.get('additional_context'):
                content += f"  - ✓ ADDITIONAL CONTEXT\n"
            if prompt_format_data.get('input'):
                content += f"  - ✓ INPUT\n"
            if prompt_format_data.get('output'):
                content += f"  - ✓ OUTPUT\n"
            if prompt_format_data.get('constraints'):
                content += f"  - ✓ CONSTRAINTS\n"
            
            content += f"\n💡 Use `load_prompt_from_library('{prompt.get('name')}')` to load this prompt.\n\n"
            content += "---\n\n"
    else:
        content += "No prompts found.\n"
    
    return content


@mcp.resource("prompts://{prompt_name}")
def get_prompt_details(prompt_name: str) -> str:
    """
    Get detailed information about a specific prompt from the library.
    
    Args:
        prompt_name: The name of the prompt to retrieve details for
    """
    safe_name = "".join(c if c.isalnum() or c in ('_', '-') else '_' for c in prompt_name.lower())
    file_path = os.path.join(PROMPT_LIBRARY_DIR, f"{safe_name}.json")
    
    if not os.path.exists(file_path):
        return f"# Prompt Not Found: {prompt_name}\n\nThis prompt does not exist in the library. Use @prompts://library to see available prompts."
    
    try:
        with open(file_path, 'r') as f:
            prompt_data = json.load(f)
        
        prompt_format_data = prompt_data.get('prompt_format', {})
        
        # Create detailed markdown content
        content = f"# {prompt_data.get('name', 'Unnamed Prompt')}\n\n"
        content += f"**Description**: {prompt_data.get('description', 'N/A')}\n\n"
        content += f"**Use Case**: {prompt_data.get('use_case', 'N/A')}\n\n"
        content += f"**Author**: {prompt_data.get('author', 'N/A')}\n\n"
        content += f"**Created**: {prompt_data.get('created_at', 'N/A')}\n\n"
        
        content += "## Prompt Format Structure\n\n"
        
        if prompt_format_data.get('instruction'):
            content += "### INSTRUCTION\n"
            content += f"```\n{prompt_format_data['instruction']}\n```\n\n"
        
        if prompt_format_data.get('additional_context'):
            content += "### ADDITIONAL CONTEXT\n"
            content += f"```\n{prompt_format_data['additional_context']}\n```\n\n"
        
        if prompt_format_data.get('input'):
            content += "### INPUT\n"
            content += f"```\n{prompt_format_data['input']}\n```\n\n"
        
        if prompt_format_data.get('output'):
            content += "### OUTPUT\n"
            content += f"```\n{prompt_format_data['output']}\n```\n\n"
        
        if prompt_format_data.get('constraints'):
            content += "### CONSTRAINTS\n"
            content += f"```\n{prompt_format_data['constraints']}\n```\n\n"
        
        return content
    
    except Exception as e:
        return f"# Error Loading Prompt\n\nFailed to load prompt '{prompt_name}': {str(e)}"


# ─── Helper Tools for PDF Processing ────────────────────────────────────────
# These tools help extract content that can be passed to the prompt templates

@mcp.tool()
def get_pdf_content_for_prompt(file_path: str) -> str:
    """
    Extract PDF content formatted for use with prompt templates.
    
    Use this tool to get PDF content, then pass it to one of the prompt templates:
    - generate_executive_summary
    - generate_introduction
    - generate_technical_summary
    - custom_prompt
    
    Args:
        file_path: Path to the PDF file
        
    Returns:
        JSON string with extracted content ready for prompt templates
    """
    if not os.path.exists(file_path):
        return json.dumps({
            "error": f"File not found: {file_path}"
        }, indent=2)
    
    extraction_result = extract_pdf_content(file_path)
    extraction_data = json.loads(extraction_result)
    
    if "error" in extraction_data:
        return extraction_result
    
    content = extraction_data.get("content", "")
    
    return json.dumps({
        "file_path": file_path,
        "file_name": os.path.basename(file_path),
        "content": content,
        "content_length": len(content),
        "usage": "Pass the 'content' field to a prompt template like generate_executive_summary(pdf_content=content)"
    }, indent=2)


@mcp.tool()
def normalize_prompt_format(
    prompt_text: str,
    auto_detect: bool = True
) -> str:
    """
    Normalize any prompt to the structured prompt format.
    
    This tool uses meta-prompting to detect sections in freeform prompts
    and restructure them into the standard format:
    INSTRUCTION → ADDITIONAL CONTEXT → INPUT → OUTPUT → CONSTRAINTS
    
    Args:
        prompt_text: The prompt text to normalize (any format)
        auto_detect: If True, attempts to auto-detect sections. If False, treats entire text as INSTRUCTION.
        
    Returns:
        JSON with normalized prompt structure
    """
    if not auto_detect:
        return json.dumps({
            "normalized_prompt": f"""INSTRUCTION:
{prompt_text}

ADDITIONAL CONTEXT:
(To be filled in)

CONSTRAINTS:
(To be filled in)""",
            "detected_sections": {"instruction": prompt_text},
            "note": "Auto-detection disabled. Entire text treated as INSTRUCTION."
        }, indent=2)
    
    # Simple heuristic-based detection
    sections = {
        "instruction": "",
        "additional_context": "",
        "input": "",
        "output": "",
        "constraints": ""
    }
    
    lines = prompt_text.split('\n')
    current_section = "instruction"
    
    for line in lines:
        line_lower = line.lower().strip()
        
        # Detect section headers
        if line_lower.startswith(("instruction:", "# instruction", "## instruction")):
            current_section = "instruction"
            continue
        elif line_lower.startswith(("context:", "additional context:", "# context", "background:")):
            current_section = "additional_context"
            continue
        elif line_lower.startswith(("input:", "# input", "input format:")):
            current_section = "input"
            continue
        elif line_lower.startswith(("output:", "# output", "output format:", "expected output:")):
            current_section = "output"
            continue
        elif line_lower.startswith(("constraints:", "# constraints", "requirements:", "rules:")):
            current_section = "constraints"
            continue
        
        # Add line to current section
        if line.strip():
            sections[current_section] += line + "\n"
    
    # Build normalized prompt
    normalized_parts = []
    
    if sections["instruction"]:
        normalized_parts.extend(["INSTRUCTION:", sections["instruction"].strip()])
    
    if sections["additional_context"]:
        normalized_parts.extend(["\nADDITIONAL CONTEXT:", sections["additional_context"].strip()])
    
    if sections["input"]:
        normalized_parts.extend(["\nINPUT:", sections["input"].strip()])
    
    if sections["output"]:
        normalized_parts.extend(["\nOUTPUT:", sections["output"].strip()])
    
    if sections["constraints"]:
        normalized_parts.extend(["\nCONSTRAINTS:", sections["constraints"].strip()])
    
    normalized_prompt = "\n".join(normalized_parts)
    
    return json.dumps({
        "normalized_prompt": normalized_prompt,
        "detected_sections": {k: bool(v.strip()) for k, v in sections.items()},
        "note": "Prompt normalized to standard prompt format. Review and adjust as needed."
    }, indent=2)


@mcp.tool()
def save_prompt_to_library(
    prompt_name: str,
    instruction: str,
    additional_context: str,
    constraints: str = "",
    input_format: str = "",
    output_format: str = "",
    description: str = "",
    use_case: str = "",
    author: str = "",
    normalize_first: bool = False
) -> str:
    """
    Save a prompt to the shared prompt library.
    
    This allows users to contribute reusable prompts that follow the standard format.
    All prompts are saved in the standardized structure.
    
    Args:
        prompt_name: Unique name for the prompt (e.g., "risk_assessment_summary")
        instruction: The main instruction
        additional_context: Context and guidelines
        constraints: Optional format and style constraints
        input_format: Optional INPUT section
        output_format: Optional OUTPUT section
        description: Brief description of what this prompt does
        use_case: When to use this prompt
        author: Author name or team
        normalize_first: If True, attempts to normalize freeform text in instruction field
        
    Returns:
        JSON with save status and file path
    """
    # Create library directory if it doesn't exist
    os.makedirs(PROMPT_LIBRARY_DIR, exist_ok=True)
    
    # Sanitize filename
    safe_name = "".join(c if c.isalnum() or c in ('_', '-') else '_' for c in prompt_name.lower())
    file_path = os.path.join(PROMPT_LIBRARY_DIR, f"{safe_name}.json")
    
    # Check if prompt already exists
    if os.path.exists(file_path):
        return json.dumps({
            "error": f"Prompt '{prompt_name}' already exists in library",
            "file_path": file_path,
            "hint": "Use a different name or delete the existing prompt first"
        }, indent=2)
    
    # Normalize if requested
    if normalize_first and instruction:
        norm_result = json.loads(normalize_prompt_format(instruction, auto_detect=True))
        detected = norm_result.get("detected_sections", {})
        
        # Override with detected sections if they were found
        if detected.get("instruction") and not additional_context:
            # Keep original instruction, user can review
            pass
    
    # Build prompt structure
    prompt_data = {
        "name": prompt_name,
        "description": description,
        "use_case": use_case,
        "author": author,
        "created_at": datetime.now().isoformat(),
        "prompt_format": {
            "instruction": instruction,
            "additional_context": additional_context,
            "input": input_format,
            "output": output_format,
            "constraints": constraints
        }
    }
    
    # Save to file
    try:
        with open(file_path, 'w') as f:
            json.dump(prompt_data, f, indent=2)
        
        return json.dumps({
            "success": True,
            "message": f"Prompt '{prompt_name}' saved to library",
            "file_path": file_path,
            "prompt_data": prompt_data
        }, indent=2)
    
    except Exception as e:
        return json.dumps({
            "error": f"Failed to save prompt: {str(e)}",
            "file_path": file_path
        }, indent=2)


@mcp.tool()
def load_prompt_from_library(prompt_name: str) -> str:
    """
    Load a prompt from the prompt library.
    
    Args:
        prompt_name: Name of the prompt to load
        
    Returns:
        JSON with the prompt structure
    """
    safe_name = "".join(c if c.isalnum() or c in ('_', '-') else '_' for c in prompt_name.lower())
    file_path = os.path.join(PROMPT_LIBRARY_DIR, f"{safe_name}.json")
    
    if not os.path.exists(file_path):
        return json.dumps({
            "error": f"Prompt '{prompt_name}' not found in library",
            "hint": "Use list_prompt_library() to see available prompts"
        }, indent=2)
    
    try:
        with open(file_path, 'r') as f:
            prompt_data = json.load(f)
        
        return json.dumps(prompt_data, indent=2)
    
    except Exception as e:
        return json.dumps({
            "error": f"Failed to load prompt: {str(e)}",
            "file_path": file_path
        }, indent=2)


@mcp.tool()
def list_prompt_library() -> str:
    """
    List all prompts in the prompt library.
    
    Returns:
        JSON with available prompts and their metadata
    """
    if not os.path.exists(PROMPT_LIBRARY_DIR):
        return json.dumps({
            "message": "Prompt library is empty",
            "library_path": PROMPT_LIBRARY_DIR,
            "hint": "Use save_prompt_to_library() to add prompts"
        }, indent=2)
    
    prompts = []
    for filename in os.listdir(PROMPT_LIBRARY_DIR):
        if filename.endswith('.json'):
            file_path = os.path.join(PROMPT_LIBRARY_DIR, filename)
            try:
                with open(file_path, 'r') as f:
                    prompt_data = json.load(f)
                    prompts.append({
                        "name": prompt_data.get("name", filename[:-5]),
                        "description": prompt_data.get("description", ""),
                        "use_case": prompt_data.get("use_case", ""),
                        "author": prompt_data.get("author", ""),
                        "created_at": prompt_data.get("created_at", "")
                    })
            except Exception as e:
                prompts.append({
                    "name": filename[:-5],
                    "error": f"Failed to load: {str(e)}"
                })
    
    return json.dumps({
        "library_path": PROMPT_LIBRARY_DIR,
        "total_prompts": len(prompts),
        "prompts": prompts
    }, indent=2)


@mcp.tool()
def list_available_prompts() -> str:
    """
    List all available prompt templates.
    
    These are exposed as MCP prompts (not tools) and can be used directly
    by MCP clients or invoked with the get_pdf_content_for_prompt tool.
    
    Returns:
        JSON string with available prompt templates and their descriptions.
    """
    prompts_info = {
        "generate_executive_summary": {
            "description": "Executive summary for reports - 5 bullets, 300 words max, professional tone",
            "use_case": "Final reports, assessment summaries, management briefings",
            "parameters": ["pdf_content: str"]
        },
        "generate_introduction": {
            "description": "Introduction for proposals/reports - 3-4 paragraphs, 250 words max",
            "use_case": "Proposals, technical reports, project kickoffs",
            "parameters": ["pdf_content: str"]
        },
        "generate_technical_summary": {
            "description": "Technical summary - 4-6 bullets, 400 words max, technical tone",
            "use_case": "Engineering reviews, technical documentation, peer reviews",
            "parameters": ["pdf_content: str"]
        },
        "custom_prompt": {
            "description": "Custom custom structured prompt with your own components",
            "use_case": "Any custom prompt following the structured prompt format",
            "parameters": ["instruction: str", "additional_context: str", "constraints: str", "document_content: str (optional)"]
        }
    }
    
    return json.dumps({
        "available_prompts": prompts_info,
        "total_prompts": len(prompts_info),
        "usage_hint": "These are MCP prompts. Use get_pdf_content_for_prompt() to extract PDF content, then invoke the prompt."
    }, indent=2)


@mcp.tool()
def analyze_pdf_structure(file_path: str) -> str:
    """
    Analyze the structure of a PDF document.
    
    Returns information about pages, sections, and content organization.
    Useful for understanding what type of document you're working with.
    
    Args:
        file_path: Path to the PDF file
        
    Returns:
        JSON string with document structure analysis.
    """
    if not os.path.exists(file_path):
        return json.dumps({
            "error": f"File not found: {file_path}"
        }, indent=2)
    
    try:
        # Extract content first
        extraction_result = extract_pdf_content(file_path)
        extraction_data = json.loads(extraction_result)
        
        if "error" in extraction_data:
            return extraction_result
        
        content = extraction_data.get("content", "")
        
        # Simple analysis
        lines = content.split('\n')
        paragraphs = [p.strip() for p in content.split('\n\n') if p.strip()]
        
        # Detect potential headers (short lines in caps or with numbers)
        potential_headers = []
        for line in lines[:50]:  # Check first 50 lines
            line = line.strip()
            if line and len(line) < 100:
                if line.isupper() or line.startswith(('1.', '2.', '3.', '4.', '5.', 'Executive', 'Introduction', 'Conclusion')):
                    potential_headers.append(line)
        
        return json.dumps({
            "file_path": file_path,
            "file_name": os.path.basename(file_path),
            "analysis": {
                "total_pages": extraction_data.get("pages", 0),
                "total_characters": len(content),
                "total_lines": len(lines),
                "total_paragraphs": len(paragraphs),
                "estimated_word_count": len(content.split()),
                "potential_sections": potential_headers[:10]  # First 10 potential headers
            },
            "content_preview": content[:500] + "..." if len(content) > 500 else content,
            "recommendations": {
                "suitable_for_summary": len(content) > 500,
                "suggested_template": "executive_summary" if len(content) > 2000 else "introduction",
                "complexity": "high" if len(content) > 10000 else "medium" if len(content) > 3000 else "low"
            }
        }, indent=2)
    
    except Exception as e:
        return json.dumps({
            "error": f"Failed to analyze PDF: {str(e)}",
            "file_path": file_path
        }, indent=2)


if __name__ == "__main__":
    # Initialize and run the server
    mcp.run(transport='stdio')
