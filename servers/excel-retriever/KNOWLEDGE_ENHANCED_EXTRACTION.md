# Knowledge-Enhanced Excel Extraction for LLMs

## Overview

The intelligent Excel retriever now includes **Knowledge-Enhanced Extraction** — features specifically designed to help LLMs understand and reason about Excel data more accurately.

## Why JSON Alone Isn't Enough

When you extract Excel data to JSON, you get the raw data, but you lose critical context:

- **Relationships**: Which tables connect to each other? Which columns are foreign keys?
- **Semantics**: What do the columns mean? What units are they in?
- **Structure**: How is the workbook organized? What's the purpose of each sheet?
- **Instructions**: What business rules or data entry guidelines apply?

Without this context, LLMs struggle with:
- Joining data across tables
- Understanding data types and units
- Following business logic embedded in instruction blocks
- Answering questions that require cross-table analysis

## Knowledge-Enhanced Features

### 1. Automatic Relationship Detection

The extractor scans all tables and identifies **common columns** that can be used to join data.

**Example Output:**
```json
{
  "relationships": [
    {
      "source_table": "Projects.Active Projects",
      "target_table": "Projects.Upcoming Milestones",
      "common_columns": ["project id"],
      "relationship_type": "overlap",
      "description": "Tables 'Projects.Active Projects' and 'Projects.Upcoming Milestones' share columns: project id."
    }
  ]
}
```

**How it works:**
- Compares headers across all detected tables (case-insensitive)
- Filters out generic auto-generated column names
- Identifies exact matches (identical schemas) vs. overlaps (some common columns)

**Use case:** An LLM can now automatically join project details with milestone data using the `project id` column.

---

### 2. LLM Schema Description

A **natural language summary** of the workbook structure, optimized for LLM context windows.

**Example Output:**
```
Workbook: complex_sample.xlsx
=============================

This workbook contains 5 sheets and a total of 11 tables.

### Sheet: Projects
- **Active Projects**: 8 rows x 8 columns.
  Columns: Project ID, Name, Client, Start Date, End Date, Budget (K), Status, Risk Level
- **Upcoming Milestones**: 5 rows x 5 columns.
  Columns: Project ID, Milestone, Due Date, Owner, Complete
- Contains 1 instruction/note blocks.

### Key Relationships (Joins)
- Tables 'Projects.Active Projects' and 'Projects.Upcoming Milestones' share columns: project id.

### AI Analysis Strategy
1. Use common columns identified above to join data across tables.
2. Pay attention to instruction blocks for data entry rules and business logic.
3. References to 'ID' or 'Code' columns are likely primary/foreign keys.
```

**How it works:**
- Generates a Markdown-formatted summary of the entire workbook
- Lists all tables with their schemas
- Highlights relationships and named ranges
- Provides AI analysis hints

**Use case:** Prepend this to your LLM prompt to give it a "map" of the workbook before asking questions.

---

### 3. Text Classification

Standalone text blocks are classified into:
- **title**: Section headers
- **instruction**: Business rules, data entry guidelines, warnings
- **note**: General annotations
- **label**: Short descriptive text

**Example Output:**
```json
{
  "text_blocks": [
    {
      "row": 3,
      "col": 1,
      "text": "Note: All figures are in thousands (USD). Updated quarterly.",
      "classification": "instruction",
      "is_bold": false
    }
  ]
}
```

**Use case:** LLMs can understand that revenue values are in thousands, not raw dollars.

---

## When to Use a Graph Database

### ✅ Use Graph DB When:
- **Multi-file knowledge base**: You're indexing hundreds of Excel files and need to query relationships across them
- **Complex ontologies**: You have hierarchical taxonomies or multi-hop relationships (e.g., "Find all projects in regions with high risk")
- **Real-time graph queries**: You need to traverse relationships dynamically (e.g., "Show me all dependencies of Project X")

### ❌ JSON is Sufficient When:
- **Single-file analysis**: Users drop one Excel file at a time
- **Simple joins**: Relationships are 1-2 hops (e.g., join projects with milestones)
- **LLM-driven queries**: The LLM can reason about relationships from the schema description

**Recommendation for your use case:** Start with **Knowledge-Enhanced JSON**. Only move to a Graph DB if you're building a multi-file knowledge base or need sub-second graph traversal queries.

---

## Best Practices for LLM Accuracy

### 1. Always Include the Schema Description
```python
# Extract with knowledge enhancement
analysis = extractor.analyze()

# Send to LLM
prompt = f"""
{analysis.llm_schema_description}

User Question: {user_question}

Data: {json.dumps(analysis_to_dict(analysis))}
"""
```

### 2. Use Relationships for Joins
```python
# Let the LLM know which columns to join on
for rel in analysis.relationships:
    print(f"Join hint: {rel.description}")
```

### 3. Separate Instructions from Data
```python
# Extract instruction blocks separately
instructions = [t for sheet in analysis.sheets 
                for t in sheet.text_blocks 
                if t.classification == "instruction"]

# Include them in the prompt
prompt += "\n\nBusiness Rules:\n"
for instr in instructions:
    prompt += f"- {instr.text}\n"
```

### 4. Export to Multiple Formats
- **JSON**: For structured LLM consumption
- **Markdown**: For human-readable summaries
- **CSV**: For data analysis tools
- **Parquet**: For large-scale data pipelines

---

## Example Workflow

```python
from smart_extractor import SmartExcelExtractor, analysis_to_dict

# 1. Analyze the Excel file
extractor = SmartExcelExtractor("user_upload.xlsx")
analysis = extractor.analyze()
extractor.close()

# 2. Get the LLM-ready schema
schema = analysis.llm_schema_description

# 3. Get relationships
relationships = [rel.description for rel in analysis.relationships]

# 4. Extract specific tables
tables = []
for sheet in analysis.sheets:
    for table in sheet.tables:
        tables.append({
            "name": f"{sheet.sheet_name}.{table.name}",
            "headers": table.headers,
            "data": table.data
        })

# 5. Send to LLM
prompt = f"""
You are analyzing an Excel workbook. Here's the structure:

{schema}

User Question: "Which projects are behind schedule and have high risk?"

Available Data:
{json.dumps(tables, indent=2)}
"""

# LLM can now:
# - Understand the workbook structure
# - Join Active Projects with Milestones using "project id"
# - Filter by Status and Risk Level columns
# - Provide accurate answers
```

---

## Comparison: JSON vs. Graph DB

| Feature | Knowledge-Enhanced JSON | Graph Database |
|---------|------------------------|----------------|
| **Setup Complexity** | Low (just use the extractor) | High (Neo4j, schema design, ETL) |
| **Query Speed** | Fast for single-file analysis | Very fast for multi-hop queries |
| **LLM Integration** | Direct (JSON in prompt) | Requires Cypher → JSON translation |
| **Multi-file Support** | Manual (concatenate JSON) | Native (graph traversal) |
| **Relationship Discovery** | Automatic (column matching) | Manual (define schema) |
| **Best For** | Single Excel file per request | Enterprise knowledge base |

---

## Advanced: Adding Custom Metadata

You can extend the extractor to add domain-specific metadata:

```python
# Example: Add unit inference
def infer_units(table):
    units = {}
    for col in table.headers:
        if "budget" in col.lower() or "revenue" in col.lower():
            units[col] = "USD (thousands)"
        elif "date" in col.lower():
            units[col] = "YYYY-MM-DD"
    return units

# Use in your workflow
for table in analysis.sheets[0].tables:
    table.units = infer_units(table)
```

---

## Summary

**For best LLM understanding:**
1. ✅ Use `smart_analyze_excel` to get relationships and schema
2. ✅ Include `llm_schema_description` in your LLM prompt
3. ✅ Separate instructions from data using text classification
4. ✅ Export to JSON for structured data + Markdown for readability
5. ❌ Don't use a Graph DB unless you have multi-file or complex graph queries

**The result:** LLMs can now accurately join tables, understand units, follow business rules, and answer complex questions about your Excel data.
