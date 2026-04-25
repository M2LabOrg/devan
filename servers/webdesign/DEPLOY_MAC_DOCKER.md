# Docker Deployment Guide - Mac Mini

This guide covers deploying the WebDesign MCP server on your Mac Mini using Docker.

**Platform**: Apple Silicon Mac Mini (M1/M2/M3) or Intel
**Deployment Type**: Local Docker (best for personal/development use)
**Security Level**: Containerized (isolated from host system)

---

## Why Docker on Mac Mini?

| Benefit | Details |
|---------|---------|
| **Isolation** | Each MCP server runs in its own container |
| **Clean System** | No Python/dependency conflicts on your Mac |
| **Portability** | Move containers to any machine instantly |
| **Easy Cleanup** | Remove with `docker rm` - no residue |
| **Version Control** | Pin exact versions, reproduce anywhere |
| **Resource Control** | Limit CPU/memory per container |

---

## Prerequisites

### 1. Install Docker Desktop

```bash
# Download from https://www.docker.com/products/docker-desktop
# Or install via Homebrew:
brew install --cask docker

# Start Docker Desktop
open -a Docker
```

### 2. Verify Installation

```bash
docker --version
docker compose version

# Test
docker run hello-world
```

---

## Deployment Options

### Option A: Single Container (Quick Start)

Best for testing or running one MCP server.

#### Step 1: Create Dockerfile

```bash
cd /path/to/mcp-design-deploy/servers/webdesign/mcp_project

cat > Dockerfile << 'EOF'
FROM python:3.11-slim

# Security: Run as non-root user
RUN groupadd -r appgroup && useradd -r -g appgroup appuser

WORKDIR /app

# Install dependencies
RUN pip install --no-cache-dir mcp

# Copy server code
COPY mcp_project/webdesign_server.py .
COPY mcp_project/pyproject.toml .

# Create output directory
RUN mkdir -p /app/output && chown -R appuser:appgroup /app

# Switch to non-root
USER appuser

# Environment variables
ENV WEBDESIGN_OUTPUT_DIR=/app/output
ENV PYTHONUNBUFFERED=1

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD python -c "import sys; sys.exit(0)" || exit 1

# Run server
CMD ["python", "webdesign_server.py"]
EOF
```

#### Step 2: Build Image

```bash
# Build for Apple Silicon (M1/M2/M3)
docker build --platform linux/arm64 -t webdesign-mcp:latest .

# Or for Intel Mac
docker build --platform linux/amd64 -t webdesign-mcp:latest .

# Or let Docker auto-detect
docker build -t webdesign-mcp:latest .
```

#### Step 3: Run Container

```bash
# Create output directory on host
mkdir -p ~/webdesign-output

# Run container
docker run -d \
  --name webdesign-mcp \
  --restart unless-stopped \
  -v ~/webdesign-output:/app/output \
  -e WEBDESIGN_OUTPUT_DIR=/app/output \
  webdesign-mcp:latest

# Check status
docker ps
docker logs webdesign-mcp
```

#### Step 4: Test

```bash
# Execute a test command
docker exec webdesign-mcp python -c "
import sys
sys.path.insert(0, '/app')
from webdesign_server import list_design_templates
print(list_design_templates())
"
```

---

### Option B: Docker Compose (Recommended)

Best for running multiple MCP servers together.

#### Step 1: Create docker-compose.yml

```bash
cd /path/to/mcp-design-deploy

cat > docker-compose.yml << 'EOF'
version: '3.8'

services:
  webdesign-mcp:
    build:
      context: ./webdesign_mcp
      dockerfile: Dockerfile
    container_name: webdesign-mcp
    volumes:
      - ~/mcp-output/webdesign:/app/output
    environment:
      - WEBDESIGN_OUTPUT_DIR=/app/output
      - PYTHONUNBUFFERED=1
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "python", "-c", "import sys; sys.exit(0)"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 5s
    # Resource limits (adjust for your Mac Mini specs)
    deploy:
      resources:
        limits:
          cpus: '1.0'
          memory: 512M
        reservations:
          cpus: '0.5'
          memory: 256M

  # Add other MCP servers here
  # excel-mcp:
  #   build:
  #     context: ./excel_retriever_demo
  #     dockerfile: Dockerfile
  #   container_name: excel-mcp
  #   volumes:
  #     - ~/mcp-output/excel:/app/excel_files
  #   environment:
  #     - EXCEL_DIR=/app/excel_files
  #   restart: unless-stopped

volumes:
  webdesign-output:
    driver: local

networks:
  default:
    name: mcp-network
EOF
```

#### Step 2: Create Dockerfile for webdesign_mcp

```bash
cd /path/to/mcp-design-deploy/servers/webdesign/mcp_project

cat > Dockerfile << 'EOF'
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN groupadd -r appgroup && useradd -r -g appgroup appuser

WORKDIR /app

# Copy and install Python dependencies
COPY mcp_project/pyproject.toml .
RUN pip install --no-cache-dir mcp

# Copy application
COPY mcp_project/webdesign_server.py .

# Create output directory with proper permissions
RUN mkdir -p /app/output && chown -R appuser:appgroup /app

# Switch to non-root user
USER appuser

# Environment
ENV WEBDESIGN_OUTPUT_DIR=/app/output
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD python -c "import sys; sys.exit(0)" || exit 1

# Default command
CMD ["python", "webdesign_server.py"]
EOF
```

#### Step 3: Start Services

```bash
cd /path/to/mcp-design-deploy

# Create output directories
mkdir -p ~/mcp-output/webdesign

# Start all services
docker-compose up -d

# Check status
docker-compose ps
docker-compose logs -f webdesign-mcp
```

#### Step 4: Manage Services

```bash
# View all MCP containers
docker-compose ps

# View logs
docker-compose logs webdesign-mcp
docker-compose logs -f  # Follow all

# Restart a service
docker-compose restart webdesign-mcp

# Stop all
docker-compose down

# Stop and remove volumes (CAREFUL: deletes data)
docker-compose down -v

# Update after code changes
docker-compose build webdesign-mcp
docker-compose up -d
```

---

### Option C: Multi-MCP Setup (Advanced)

Run all your MCP servers in one compose file.

```bash
cd /path/to/mcp-design-deploy

cat > mcp-servers-compose.yml << 'EOF'
version: '3.8'

services:
  webdesign-mcp:
    build:
      context: ./webdesign_mcp
      dockerfile: Dockerfile
    container_name: webdesign-mcp
    volumes:
      - webdesign-data:/app/output
    environment:
      - WEBDESIGN_OUTPUT_DIR=/app/output
    restart: unless-stopped
    networks:
      - mcp-net
    deploy:
      resources:
        limits:
          cpus: '1.0'
          memory: 512M

  excel-mcp:
    build:
      context: ./excel_retriever_demo
      dockerfile: Dockerfile
    container_name: excel-mcp
    volumes:
      - excel-data:/app/excel_files
    environment:
      - EXCEL_DIR=/app/excel_files
    restart: unless-stopped
    networks:
      - mcp-net

  prompt-mcp:
    build:
      context: ./prompt_mcp_demo
      dockerfile: Dockerfile
    container_name: prompt-mcp
    volumes:
      - prompt-data:/app/pdf_files
    environment:
      - PDF_DIR=/app/pdf_files
    restart: unless-stopped
    networks:
      - mcp-net

volumes:
  webdesign-data:
    driver: local
  excel-data:
    driver: local
  prompt-data:
    driver: local

networks:
  mcp-net:
    driver: bridge
EOF

# Start everything
docker-compose -f mcp-servers-compose.yml up -d

# Check all
docker-compose -f mcp-servers-compose.yml ps
```

---

## Integration with Windsurf

### Option 1: Direct Docker Exec (Local)

Use `docker exec` to run MCP tools from Windsurf:

```json
// mcp_config.json
{
  "mcpServers": {
    "webdesign-mcp-local": {
      "command": "docker",
      "args": [
        "exec",
        "-i",
        "webdesign-mcp",
        "python",
        "-c",
        "from webdesign_server import *; import sys; exec(sys.stdin.read())"
      ]
    }
  }
}
```

**Note**: This is experimental and may have limitations.

### Option 2: Expose via HTTP Bridge (Recommended)

Create a simple HTTP bridge container:

```bash
# Create bridge service
cat > docker-compose-with-bridge.yml << 'EOF'
version: '3.8'

services:
  webdesign-mcp:
    build:
      context: ./webdesign_mcp
      dockerfile: Dockerfile
    container_name: webdesign-mcp
    volumes:
      - ~/mcp-output/webdesign:/app/output
    environment:
      - WEBDESIGN_OUTPUT_DIR=/app/output
    networks:
      - mcp-net
    # No ports exposed - internal only

  mcp-bridge:
    image: python:3.11-slim
    container_name: mcp-bridge
    ports:
      - "8000:8000"
    volumes:
      - ./bridge:/app
    working_dir: /app
    command: python bridge.py
    networks:
      - mcp-net
    depends_on:
      - webdesign-mcp

networks:
  mcp-net:
    driver: bridge
EOF
```

Create bridge script:
```bash
mkdir -p bridge
cat > bridge/bridge.py << 'EOF'
from fastapi import FastAPI, Request
import subprocess
import json

app = FastAPI()

@app.post("/mcp/{tool}")
async def call_tool(tool: str, request: Request):
    params = await request.json()
    
    # Call MCP server via docker exec
    result = subprocess.run(
        ["docker", "exec", "webdesign-mcp", "python", "-c",
         f"from webdesign_server import {tool}; print({tool}(**{params}))"],
        capture_output=True,
        text=True
    )
    
    return json.loads(result.stdout)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
EOF

cat > bridge/requirements.txt << 'EOF'
fastapi
uvicorn
EOF

# Build and start
docker-compose -f docker-compose-with-bridge.yml up -d
```

Then configure Windsurf:
```json
{
  "mcpServers": {
    "webdesign-mcp": {
      "command": "curl",
      "args": [
        "-X", "POST",
        "-H", "Content-Type: application/json",
        "-d", "@{input}",
        "http://localhost:8000/mcp/{tool}"
      ]
    }
  }
}
```

---

## Accessing MCP from Docker in Windsurf

When your MCP server runs in a Docker container and you need to access it from Windsurf (or another container), use these approaches:

### Option 1: Use `host.docker.internal` (Recommended for macOS)

Since MCP servers run on your host machine, connect to them using the special DNS name:

```json
{
  "mcpServers": {
    "my-server": {
      "command": "docker",
      "args": [
        "run",
        "--rm",
        "-e", "MCP_HOST=host.docker.internal",
        "your-image"
      ]
    }
  }
}
```

Then in your container code, connect to `host.docker.internal` instead of `localhost`.

### Option 2: Host Network Mode (Linux only)

```bash
docker run --rm --network host your-image
```

**Note**: This doesn't work on macOS Docker Desktop.

### Option 3: Explicit Port Mapping

If your MCP server exposes a port (e.g., 3000):

```bash
docker run --rm -p 3000:3000 your-image
```

Then your containerized app connects to `host.docker.internal:3000`.

### Windsurf-Specific Configuration

Check your `~/.codeium/windsurf/mcp_config.json` (or the project's `.windsurf/mcp_config.json`). When defining a Docker-based MCP server:

```json
{
  "mcpServers": {
    "filesystem": {
      "command": "docker",
      "args": [
        "run",
        "--rm",
        "-i",
        "--add-host=host.docker.internal:host-gateway",
        "mcp/filesystem",
        "/projects"
      ]
    }
  }
}
```

The `--add-host=host.docker.internal:host-gateway` helps with Linux compatibility.

### Resource Allocation

For a base Mac Mini (8GB RAM, 256GB SSD):

```yaml
# docker-compose.yml snippet
deploy:
  resources:
    limits:
      cpus: '0.5'        # Half CPU core
      memory: 256M       # Quarter GB RAM
    reservations:
      cpus: '0.25'
      memory: 128M
```

For a higher-end Mac Mini (16GB+ RAM):

```yaml
deploy:
  resources:
    limits:
      cpus: '1.0'
      memory: 512M
    reservations:
      cpus: '0.5'
      memory: 256M
```

### Auto-Start on Boot

```bash
# Create plist for LaunchDaemon
sudo tee /Library/LaunchDaemons/com.docker.mcp-servers.plist << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.docker.mcp-servers</string>
    <key>ProgramArguments</key>
    <array>
        <string>/usr/local/bin/docker-compose</string>
        <string>-f</string>
        <string>/path/to/mcp-design-deploy/docker-compose.yml</string>
        <string>up</string>
        <string>-d</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>StandardOutPath</key>
    <string>/tmp/mcp-servers.out</string>
    <key>StandardErrorPath</key>
    <string>/tmp/mcp-servers.err</string>
</dict>
</plist>
EOF

# Load and start
sudo launchctl load /Library/LaunchDaemons/com.docker.mcp-servers.plist
sudo launchctl start com.docker.mcp-servers

# Check status
sudo launchctl list | grep mcp
```

---

## Maintenance

### Update Containers

```bash
cd /path/to/mcp-design-deploy/servers/webdesign/mcp_project

# Pull latest code
git pull origin main

# Rebuild
docker-compose build webdesign-mcp

# Restart
docker-compose up -d

# Verify
docker-compose ps
```

### Backup Data

```bash
# Backup generated projects
tar -czf ~/backups/webdesign-$(date +%Y%m%d).tar.gz ~/mcp-output/webdesign

# Or use Docker volume backup
docker run --rm -v webdesign-data:/data -v ~/backups:/backup alpine \
  tar -czf /backup/webdesign-$(date +%Y%m%d).tar.gz -C /data .
```

### Clean Up

```bash
# Remove unused images
docker image prune -a

# Remove unused volumes
docker volume prune

# Full cleanup (CAREFUL)
docker system prune -a --volumes
```

---

## Troubleshooting

### Container won't start

```bash
# Check logs
docker logs webdesign-mcp

# Check for syntax errors
docker run --rm webdesign-mcp:latest python -m py_compile webdesign_server.py

# Interactive debugging
docker run -it --rm webdesign-mcp:latest /bin/bash
```

### Permission denied on volumes

```bash
# Fix permissions on Mac
sudo chown -R $(whoami) ~/mcp-output

# Or run container as your user
docker run -d \
  --user $(id -u):$(id -g) \
  -v ~/mcp-output:/app/output \
  webdesign-mcp:latest
```

### Apple Silicon issues

```bash
# Build with platform specification
docker build --platform linux/arm64 -t webdesign-mcp:latest .

# Or use buildx for multi-platform
docker buildx build --platform linux/arm64 -t webdesign-mcp:latest .
```

### High CPU/Memory usage

```bash
# Monitor resources
docker stats

# Limit resources
docker update --cpus 0.5 --memory 256m webdesign-mcp

# Check for memory leaks
docker exec webdesign-mcp ps aux --sort=-%mem | head
```

---

## Security Best Practices

### ✅ Do

- Run containers as non-root user (Dockerfile has `USER appuser`)
- Keep images updated: `docker pull python:3.11-slim` regularly
- Scan images for vulnerabilities: `docker scan webdesign-mcp`
- Use volume mounts for persistent data (not container storage)
- Enable Docker Content Trust: `export DOCKER_CONTENT_TRUST=1`
- Limit container resources (CPU/memory caps)

### ❌ Don't

- Don't use `--privileged` flag unless absolutely necessary
- Don't store secrets in environment variables (use Docker secrets or files)
- Don't expose ports unnecessarily (keep internal only)
- Don't run with root user inside container
- Don't use `latest` tag for production (pin to specific versions)

---

## Comparison: Docker vs Direct

| Aspect | Docker | Direct Install |
|--------|--------|----------------|
| Setup complexity | Medium (Dockerfile) | Low (pip install) |
| Isolation | Strong | None |
| Cleanup | Easy (`docker rm`) | Hard (pip uninstall) |
| Portability | Excellent | Poor |
| Resource control | Yes | No |
| Auto-restart | Yes (`restart: unless-stopped`) | Manual |
| Multi-tenant | Easy | Hard |
| Learning curve | Medium | Low |
| **Recommendation** | **✅ Use for production** | For quick testing only |

---

## Next Steps

1. [ ] Choose Option A, B, or C based on your needs
2. [ ] Deploy and verify MCP server works
3. [ ] Configure Windsurf to connect (via bridge if needed)
4. [ ] Set up auto-start on boot
5. [ ] Configure backup schedule
6. [ ] Document any customizations

---

**Last Updated**: March 2025
**Platform**: macOS (Apple Silicon & Intel)
**Docker Version**: 24.x+
