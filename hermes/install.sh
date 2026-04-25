#!/usr/bin/env bash
# hermes/install.sh — Wire this project's MCP servers into Hermes Agent
#
# What it does:
#   1. Checks that Hermes CLI is installed (prints install instructions if not).
#   2. Resolves the absolute path of this repository.
#   3. Renders config.yaml.template → a real config.yaml by substituting PROJECT_ROOT.
#   4. Merges the rendered config into ~/.hermes/config.yaml (non-destructively).
#
# Usage:
#   chmod +x hermes/install.sh && ./hermes/install.sh

set -euo pipefail

# ── Helpers ──────────────────────────────────────────────────────────────────
BOLD='\033[1m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

info()    { echo -e "${GREEN}[hermes]${NC} $*"; }
warn()    { echo -e "${YELLOW}[hermes]${NC} $*"; }
error()   { echo -e "${RED}[hermes]${NC} $*" >&2; }
header()  { echo -e "\n${BOLD}$*${NC}"; }

# ── Resolve project root ──────────────────────────────────────────────────────
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
TEMPLATE="${SCRIPT_DIR}/config.yaml.template"
RENDERED="${SCRIPT_DIR}/config.yaml"
HERMES_CONFIG="${HOME}/.hermes/config.yaml"

header "Hermes ↔ mcp-design-deploy integration setup"
info "Project root : ${PROJECT_ROOT}"
info "Hermes config: ${HERMES_CONFIG}"

# ── Check Hermes is installed ─────────────────────────────────────────────────
if ! command -v hermes &>/dev/null; then
  warn "Hermes CLI not found."
  echo
  echo "  Install with:"
  echo "    curl -fsSL https://raw.githubusercontent.com/NousResearch/hermes-agent/main/scripts/install.sh | bash"
  echo
  echo "  Then re-run this script."
  echo
  echo "  Alternatively, continue anyway to generate the config file — you can"
  echo "  merge it manually later."
  read -rp "Continue anyway? [y/N] " ans
  [[ "${ans,,}" == "y" ]] || exit 0
fi

# ── Render template ───────────────────────────────────────────────────────────
info "Rendering config template..."
sed "s|\${PROJECT_ROOT}|${PROJECT_ROOT}|g" "${TEMPLATE}" > "${RENDERED}"
info "Written: ${RENDERED}"

# ── Merge into ~/.hermes/config.yaml ─────────────────────────────────────────
mkdir -p "${HOME}/.hermes"

if [[ ! -f "${HERMES_CONFIG}" ]]; then
  # No existing config — just copy ours in
  cp "${RENDERED}" "${HERMES_CONFIG}"
  info "Created ${HERMES_CONFIG}"
else
  # Config exists — check if mcp_servers key is already present
  if grep -q "^mcp_servers:" "${HERMES_CONFIG}"; then
    warn "~/.hermes/config.yaml already has an 'mcp_servers:' section."
    warn "Skipping automatic merge to avoid overwriting existing entries."
    echo
    echo "  Manually add the servers from ${RENDERED} into ${HERMES_CONFIG}"
    echo "  under the existing 'mcp_servers:' key."
    echo
    echo "  Or back up your config and re-run:"
    echo "    cp ~/.hermes/config.yaml ~/.hermes/config.yaml.bak"
    echo "    cat ${RENDERED} >> ~/.hermes/config.yaml"
  else
    # Safe to append the mcp_servers block
    echo "" >> "${HERMES_CONFIG}"
    cat "${RENDERED}" >> "${HERMES_CONFIG}"
    info "Appended MCP server config to ${HERMES_CONFIG}"
  fi
fi

# ── Verify uv is available (required to start each server) ───────────────────
if ! command -v uv &>/dev/null; then
  warn "'uv' not found — required to start MCP servers."
  echo "  Install with: curl -LsSf https://astral.sh/uv/install.sh | sh"
fi

# ── Summary ───────────────────────────────────────────────────────────────────
header "Done"
echo
echo "  Servers registered with Hermes:"
echo "    • document          — unified Excel / PDF / Word / Parquet"
echo "    • data-modelling    — schema inference, SQLite / Arrow export"
echo "    • excel-pipeline    — extraction, validation, lineage"
echo "    • excel-retriever   — Excel + OpenSearch integration"
echo "    • guardrail         — PII detection, secret scanning"
echo "    • pdf-extractor     — layout analysis, OCR, tables"
echo "    • prompt-engineering— templates and PDF summarisation"
echo "    • webdesign         — React component / page generation"
echo "    • webscraper        — Firecrawl / BeautifulSoup scraping"
echo
echo "  Start Hermes and use any of these tools by name:"
echo "    hermes"
echo
echo "  Hermes will build skills from your usage and remember them across sessions."
echo "  See hermes/README.md for tips on getting the most out of the learning loop."
echo
