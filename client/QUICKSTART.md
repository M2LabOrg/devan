# MCP Client UI - Quick Start Guide

Get up and running in 5 minutes!

## Step 1: Install Ollama (2 minutes)

```bash
# macOS/Linux
curl -fsSL https://ollama.ai/install.sh | sh

# Or download from https://ollama.ai

# Pull a model (choose one or more)
ollama pull llama3.2        # Fast, general purpose
ollama pull mistral         # Good for coding
ollama pull qwen2.5-coder   # Excellent for code
```

## Step 2: Start the UI (1 minute)

```bash
cd mcp_client_ui
./start.sh
```

That's it! Open **http://localhost:5001** in your browser.

## Step 3: Configure & Chat (2 minutes)

### In the Web UI:

1. **Focus the Command Bar**
   - Click the search bar or press **⌘K** to expand it.

2. **Select LLM Provider**
   - Click on an available provider chip (Ollama/LM Studio).
   - Select a model from the dropdown.

3. **Enable MCP Servers**
   - Toggle the chips for the servers you want to use.

4. **Start Chatting**
   - Click "Start Chat" in quick actions or just type your message and press Enter.

## Example Conversations

### With Excel Retriever
```
You: List available Excel files
Assistant: [Uses excel_retriever to list files]

You: Analyze sales_data.xlsx
Assistant: [Extracts and analyzes the data]
```

### With Prompt Engineering MCP
```
You: Show me available prompts
Assistant: [Lists prompts from library]

You: Create a technical summary prompt
Assistant: [Creates structured prompt]
```

### With Multiple Servers
```
You: Extract data from report.xlsx and create a professional summary
Assistant: [Uses excel_retriever + prompt_mcp together]
```

## Troubleshooting

### Ollama Not Detected?
```bash
# Check if running
ollama serve

# Test manually
curl http://localhost:11434/api/tags
```

### MCP Server Won't Connect?
```bash
# Test the server manually
cd ../excel_retriever/mcp_project
uv run excel_server.py
```

### Need Help?
- Check the full [README.md](README.md)
- Review MCP server documentation
- Check browser console (F12) for errors

## What's Next?

- Try different LLM models
- Enable multiple MCP servers
- Explore the prompt library
- Analyze your own Excel files
- Create custom prompts

## Tips

💡 **Best Models for Different Tasks:**
- **General chat**: llama3.2, mistral
- **Code generation**: qwen2.5-coder, deepseek-coder
- **Analysis**: llama3.2, mixtral

💡 **MCP Server Combinations:**
- Excel + Prompts = Professional reports from data
- Excel + Guardrails = Safe data analysis
- All servers = Maximum capabilities

💡 **Performance:**
- Smaller models (7B) = Faster responses
- Larger models (70B+) = Better quality
- Use quantized models for speed

Enjoy! 🚀
