FROM python:3.11-slim

# System dependencies for OpenCV (easyocr), PDF rendering, and build tools
RUN apt-get update && apt-get install -y \
    curl \
    git \
    build-essential \
    libgl1 \
    libglib2.0-0 \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Install uv (fast Python package manager used by MCP servers)
# Use pip install uv for reliable Docker builds (curl|sh exits 0 even on failure)
# uv is also available at /root/.local/bin when installed via the astral script on host
RUN pip install --no-cache-dir uv
ENV PATH="/root/.local/bin:/usr/local/bin:$PATH"

WORKDIR /app

# Copy dependency files first so Docker can cache the install layer.
# The expensive pip install and uv sync steps only re-run when these files change,
# not on every code edit.
COPY client/requirements.txt client/requirements.txt
RUN pip install --no-cache-dir -r client/requirements.txt

# Copy MCP server manifests for uv sync
COPY servers/ servers/
RUN for dir in servers/document servers/prompt-engineering servers/guardrail servers/webdesign servers/webscraper servers/excel-pipeline; do \
    [ -d "/app/$dir/mcp_project" ] || continue; \
    echo "==> Syncing $dir/mcp_project ..." && \
    cd /app/$dir/mcp_project && uv sync --no-dev 2>&1 && cd /app; \
    done

# Copy the rest of the project (code changes land here — no reinstall needed)
COPY . .

# Entrypoint
COPY docker/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

EXPOSE 5001

ENTRYPOINT ["/entrypoint.sh"]
