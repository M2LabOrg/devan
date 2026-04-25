#!/bin/bash
# Interactive first-time setup for MCP Design & Deploy (Docker)

set -e

echo ""
echo "╔══════════════════════════════════════════════════╗"
echo "║       MCP Design & Deploy — Docker Setup         ║"
echo "╚══════════════════════════════════════════════════╝"
echo ""

# ── Check Docker is running ──────────────────────────────────────────────────
if ! docker info > /dev/null 2>&1; then
    echo "ERROR: Docker is not running. Please start Docker Desktop and try again."
    exit 1
fi

# ── Model selection ──────────────────────────────────────────────────────────
echo "Select an Ollama model (runs locally on CPU):"
echo ""
echo "  1) llama3.2:3b   — Recommended (~2 GB, Meta, strong instruction-following)"
echo "  2) llama3.2:1b   — Lightweight  (~1.3 GB, faster on slower machines)"
echo "  3) phi3.5        — Microsoft    (~2.2 GB, great at reasoning & code)"
echo "  4) qwen2.5:3b    — Alibaba      (~2 GB, multilingual, very capable)"
echo "  5) Custom        — Enter any model name from ollama.com/library"
echo ""
read -p "Choice [1]: " choice

case "$choice" in
    2) MODEL="llama3.2:1b" ;;
    3) MODEL="phi3.5" ;;
    4) MODEL="qwen2.5:3b" ;;
    5)
        read -p "Model name (e.g. mistral:7b): " MODEL
        if [ -z "$MODEL" ]; then
            MODEL="llama3.2:3b"
        fi
        ;;
    *) MODEL="llama3.2:3b" ;;
esac

echo ""
echo "Selected model: $MODEL"
echo "OLLAMA_MODEL=$MODEL" > .env
echo ""

# ── Build ────────────────────────────────────────────────────────────────────
echo "Building Docker image (first run: ~5–10 min while packages download)..."
echo ""
docker compose build

echo ""
echo "Starting Ollama and pulling $MODEL (~2 GB download on first run)..."
echo "This is cached in a Docker volume — subsequent starts are instant."
echo ""
docker compose up -d ollama
docker compose run --rm ollama-init

echo ""
echo "╔══════════════════════════════════════════════════╗"
echo "║             Setup complete!                      ║"
echo "║                                                  ║"
echo "║  Run:  make start                                ║"
echo "║  Open: http://localhost:5001                     ║"
echo "╚══════════════════════════════════════════════════╝"
echo ""
