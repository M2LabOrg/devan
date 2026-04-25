#!/bin/bash

# MCP Client UI Startup Script

echo "🚀 Starting MCP Client UI..."
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Install/update dependencies
echo "📥 Installing dependencies..."
pip install -q -r requirements.txt

# Check for Ollama
echo ""
echo "🔍 Checking for local LLM providers..."
if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
    echo "✅ Ollama detected and running"
    MODELS=$(curl -s http://localhost:11434/api/tags | python3 -c "import sys, json; data=json.load(sys.stdin); print(', '.join([m['name'] for m in data.get('models', [])[:3]]))")
    if [ ! -z "$MODELS" ]; then
        echo "   Available models: $MODELS"
    fi
else
    echo "⚠️  Ollama not detected. Install from https://ollama.ai"
fi

# Check for LM Studio
if curl -s http://localhost:1234/v1/models > /dev/null 2>&1; then
    echo "✅ LM Studio detected and running"
else
    echo "ℹ️  LM Studio not detected (optional)"
fi

echo ""
echo "🌐 Starting web server..."
echo "   Open http://localhost:5001 in your browser"
echo ""
echo "Press Ctrl+C to stop"
echo ""

# Start the application
PORT=${PORT:-5001} python app.py
