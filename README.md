# DEVAN

> Composable MCP-orchestrated agent framework for document intelligence and data pipelines. By [M2Lab.io](https://github.com/M2LabOrg).

[![Apache 2.0](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](LICENSE)
[![GitHub Pages](https://img.shields.io/badge/docs-GitHub%20Pages-indigo)](https://m2laborg.github.io/devan/)
[![MCP](https://img.shields.io/badge/protocol-MCP-purple)](https://modelcontextprotocol.io)

**[Documentation & landing page →](https://m2laborg.github.io/devan/)**

---

## What is DEVAN?

DEVAN is a collection of **MCP (Model Context Protocol) servers** that give AI assistants first-class document intelligence and data pipeline capabilities. Each server is an independently deployable Python package exposing typed MCP tools — chain them together or use them standalone.

## MCP Servers

| Server | Description | Key formats |
|--------|-------------|-------------|
| [`document`](servers/document/) | Extract and reason over documents; index with OpenSearch | PDF, Word, Excel, PowerPoint, HTML |
| [`data-modelling`](servers/data-modelling/) | Schema inference, transformation pipelines, typed structured output | Excel, CSV, XML |

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
  |  document |        | data-modelling  |
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

Contributions are welcome! Please open an issue first to discuss what you'd like to change. See [CONTRIBUTING.md](CONTRIBUTING.md) *(coming soon)* for guidelines.

## Security

Please report vulnerabilities per the [Security Policy](SECURITY.md).

## License

[Apache License 2.0](LICENSE) — © M2Lab.io
