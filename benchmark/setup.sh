#!/usr/bin/env bash
# Generate synthetic benchmark data for the DEVAN RAG evaluation.
#
# Requires: uv (https://docs.astral.sh/uv/)
# Output:   benchmark/data/  (gitignored — not committed)
#
# Usage:
#   cd <devan-root>
#   bash benchmark/setup.sh
#
# After running, execute the benchmark:
#   python run_benchmark.py \
#     --folder benchmark/data \
#     --questions benchmark/questions.jsonl \
#     --out benchmark/results.json

set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
GENERATOR="$ROOT_DIR/../mcp-design-deploy/paper/benchmark/generate_data.py"
OUTPUT="$SCRIPT_DIR/data"

if [ ! -f "$GENERATOR" ]; then
  echo "ERROR: generator not found at $GENERATOR"
  echo "Clone mcp-design-deploy alongside this repo and retry."
  exit 1
fi

if [ -d "$OUTPUT" ]; then
  echo "benchmark/data/ already exists — skipping generation."
  echo "Delete it to regenerate: rm -rf $OUTPUT"
  exit 0
fi

echo "Installing data-generation dependencies..."
cd "$(dirname "$GENERATOR")"
uv venv --python 3.12 2>/dev/null || true
uv pip install reportlab openpyxl 2>/dev/null

echo "Generating 120 synthetic benchmark documents (seed=42)..."
.venv/bin/python "$GENERATOR" --seed 42 --output "$OUTPUT" --n 20

echo ""
echo "Done. Run the benchmark with:"
echo "  python run_benchmark.py --folder benchmark/data --questions benchmark/questions.jsonl --out benchmark/results.json"
