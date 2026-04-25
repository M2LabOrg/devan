# DEVAN

> Composable MCP-orchestrated agent framework for document intelligence and data pipelines. By [M2Lab.io](https://github.com/M2LabOrg).

[![Apache 2.0](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](LICENSE)
[![MCP](https://img.shields.io/badge/protocol-MCP-purple)](https://modelcontextprotocol.io)

| | |
|---|---|
| **Product site** | [devan-agent.netlify.app](https://devan-agent.netlify.app) — commercial front door |
| **Developer docs** | [m2laborg.github.io/devan](https://m2laborg.github.io/devan/#top) — open-source landing page |

---

## What is DEVAN?

DEVAN is a collection of **MCP (Model Context Protocol) servers** that give AI assistants first-class document intelligence and data pipeline capabilities. Each server is an independently deployable Python package exposing typed MCP tools — chain them together or use them standalone.

## MCP Servers

| Server | Description | Key formats |
|--------|-------------|-------------|
| [`document`](servers/document/) | Extract and reason over documents; index with OpenSearch | PDF, Word, Excel, PowerPoint, HTML |
| [`data-modelling`](servers/data-modelling/) | Schema inference, transformation pipelines, typed structured output | Excel, CSV, XML |
| [`excel-pipeline`](servers/excel-pipeline/) | Robust Excel extraction, canonical modelling, validation, and export | Excel |
| [`excel-retriever`](servers/excel-retriever/) | Intelligent Excel analysis with table detection | Excel |
| [`pdf-extractor`](servers/pdf-extractor/) | PDF extraction optimised for LLM and RAG pipelines | PDF |
| [`prompt-engineering`](servers/prompt-engineering/) | Prompt library management and PDF processing | PDF |
| [`guardrail`](servers/guardrail/) | Content moderation and safety guardrails for LLM outputs | — |
| [`webdesign`](servers/webdesign/) | React component and page generation | — |
| [`webscraper`](servers/webscraper/) | Web scraping with Firecrawl and BeautifulSoup engines | HTML |

## Quick start

```bash
# Clone the repo
git clone https://github.com/M2LabOrg/devan.git
cd devan

# Install a server
cd servers/document
pip install -e .
```

Connect to Claude Desktop or any MCP-compatible host:

```json
{
  "mcpServers": {
    "devan-document": {
      "command": "python",
      "args": ["-m", "mcp_project.server"]
    }
  }
}
```

## Architecture

```
  MCP Host (Claude Desktop / Claude Code / custom agent)
       |  MCP tool calls
       v
  +-----------+        +-----------------+
  |  document |        | data-modelling  |  ... 7 more servers
  |  server   |        |    server       |
  +-----------+        +-----------------+
       |                        |
  PDF, Word,              Excel, CSV,
  Excel, PPTX,            schema inference,
  HTML, OpenSearch        typed pipelines
```

## Requirements

- Python ≥ 3.11
- [MCP SDK](https://github.com/modelcontextprotocol/python-sdk) ≥ 1.27

Each server lists its own dependencies in its `pyproject.toml`.

## Contributing

Contributions are welcome! Please open an issue first to discuss what you'd like to change. See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## Security

Please report vulnerabilities per the [Security Policy](SECURITY.md).

## License

[Apache License 2.0](LICENSE) — © M2Lab.io
