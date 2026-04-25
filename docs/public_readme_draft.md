# DEVAN — Composable MCP Agent Framework

> **Build, compose, and deploy multi-agent document pipelines with MCP.**

<!-- PLACEHOLDER: 60-second demo GIF -->
<!-- ![DEVAN demo](docs/demo.gif) -->

DEVAN is an open-source framework for building multi-agent pipelines using the [Model Context Protocol (MCP)](https://modelcontextprotocol.io). Each capability — document extraction, data modelling, safety guardrails — is an independently deployable MCP server. Compose them in any order, swap them without changing orchestration code, and audit every tool call at the boundary.

**Built by [M2Lab.io](https://m2lab.io) · Apache 2.0**

---

## Why DEVAN?

| Problem | How DEVAN solves it |
|---|---|
| Monolithic agent frameworks couple tools to orchestration | Each capability is an isolated MCP server — swap, scale, or audit independently |
| Safety moderation baked into LLM prompts is unreliable | Dedicated `guardrail` MCP server intercepts every response before it reaches the user |
| Business documents (Excel/PDF) need bespoke pipelines | `excel-pipeline` and `pdf-extractor` servers handle the hard cases out of the box |
| Session memory is lost between agent runs | `hermes` agent provides persistent skill memory across sessions via MCP |

---

## 60-Second Quickstart

**Prerequisites:** Python 3.10+, [uv](https://docs.astral.sh/uv/)

```bash
# 1. Clone
git clone https://github.com/m2laborg/devan.git
cd devan

# 2. Start an MCP server (e.g. PDF extractor)
cd servers/pdf-extractor/mcp_project
uv sync
uv run pdf_extractor.py

# 3. In a new terminal, start the DEVAN client UI
cd client
./start.sh
# → Opens at http://localhost:5001
```

Point the client at any running MCP server via `client/config.json`. No code changes required to switch servers.

---

## Servers

| Server | What it does | Key dependency |
|---|---|---|
| `excel-retriever` | Intelligent Q&A over Excel workbooks | FastMCP, pandas |
| `excel-pipeline` | Extract → validate → export Excel to relational model | FastMCP, openpyxl |
| `pdf-extractor` | PDF extraction optimised for LLM/RAG pipelines | FastMCP, docling |
| `prompt-engineering` | Prompt templates + PDF summarisation | FastMCP |
| `guardrail` | LLM output safety validation (policy + PII) | FastMCP |
| `webdesign` | Generate React websites from descriptions | FastMCP |

Each server is self-contained: its own `pyproject.toml`, `uv.lock`, and no shared state.

---

## Architecture

```
┌─────────────────────────────────┐
│         DEVAN Client UI          │  Flask + Socket.IO
│  (browser ↔ agent loop)         │
└────────────┬────────────────────┘
             │ MCP tool calls (JSON-RPC)
   ┌─────────▼──────────┐   ┌─────────────────┐
   │   excel-pipeline    │   │    guardrail     │  ← every response
   │   pdf-extractor     │   │    MCP server    │    passes through
   │   prompt-eng        │   └─────────────────┘
   └─────────────────────┘
```

The client speaks MCP to all servers. Adding a new capability = writing a new MCP server. No client changes needed.

---

## Research

DEVAN is the artifact for the paper:

> *DEVAN: A Composable MCP-Orchestrated Multi-Agent Framework for Document Intelligence and Data Pipelines*
> M2Lab.io — arXiv cs.MA *(coming soon)*

The paper makes two empirical contributions:
1. **Composability benchmark** — MCP-composed pipelines vs. LangChain/CrewAI monoliths on document tasks.
2. **Guardrail-in-the-loop study** — dedicated guardrail MCP server vs. in-LLM prompt moderation.

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). All contributions require signing off with `git commit -s` (DCO). Apache 2.0 license applies to all contributions.

---

## License

Apache 2.0 — see [LICENSE](LICENSE).

---

## Links

- [M2Lab.io](https://m2lab.io)
- [MCP Specification](https://modelcontextprotocol.io)
- [Report a vulnerability](SECURITY.md)
