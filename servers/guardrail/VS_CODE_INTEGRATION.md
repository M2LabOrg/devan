# VS Code Guardrail MCP Integration Guide

This guide explains how to set up and use Guardrail MCPs in VS Code to protect your development workflow.

---

## Overview

**What it does**: Real-time code scanning and policy enforcement directly in VS Code
**When it runs**: On file save, before commit, or on demand
**Who it protects**: Both M2Lab (policy compliance) and developers (security education)

---

## Installation

### Step 1: Install MCP Extension for VS Code

Currently, VS Code doesn't have native MCP support. You can use:

**Option A: Custom VS Code Extension** (future)
- M2Lab can build a custom VS Code extension
- Integrates MCP servers directly
- Native guardrail notifications

**Option B: CLI Integration** (immediate)
```bash
# Add to VS Code tasks.json
{
    "version": "2.0.0",
    "tasks": [
        {
            "label": "Guardrail Scan",
            "type": "shell",
            "command": "python",
            "args": ["-m", "guardrail_mcp.scan", "${file}"],
            "group": "build",
            "presentation": {
                "reveal": "always",
                "panel": "new"
            }
        }
    ]
}
```

---

## Configuration

### Step 2: Configure MCP Server

Create `.vscode/mcp_config.json` in your project:

```json
{
  "mcpServers": {
    "guardrail-mcp": {
      "command": "python",
      "args": [
        "/path/to/mcp-design-deploy/servers/guardrail/mcp_project/guardrail_server.py"
      ],
      "env": {
        "POLICY_STRICT": "true",
        "GUARDRAIL_MODE": "blocking"
      }
    }
  }
}
```

### Step 3: Add Pre-Save Hook

Create `.vscode/settings.json`:

```json
{
  "editor.formatOnSave": true,
  "editor.codeActionsOnSave": {
    "source.fixAll": true
  },
  // Custom command to run guardrail on save
  "runOnSave.commands": [
    {
      "match": "\\.py$",
      "command": "guardrail.scan",
      "message": "Running guardrail scan..."
    }
  ]
}
```

---

## Usage Examples

### Example 1: Real-Time Code Scanning

When you save a file with potential issues:

```python
# Your code
password = "secret123"
db.execute(f"SELECT * FROM users WHERE id = {user_id}")
```

VS Code will show:

```
🔴 [CRITICAL] SECRET
   File: config.py:1
   Issue: Hardcoded password detected
   Fix: Store in environment variable

🟠 [HIGH] SECURITY
   File: app.py:2
   Issue: Potential SQL injection
   Fix: Use parameterized queries
```

### Example 2: AI Assistant Integration

When using GitHub Copilot or similar:

1. Copilot suggests code
2. Guardrail MCP automatically scans it
3. You see warnings before accepting

```
Copilot suggestion:
    eval(user_input)

⚠️ Guardrail Alert:
🔴 CRITICAL: Dangerous eval() usage detected
   This could allow arbitrary code execution
   
Options:
[Modify] [Reject] [Override with comment]
```

### Example 3: Pre-Commit Check

Add to `.git/hooks/pre-commit`:

```bash
#!/bin/bash
# Run guardrail on staged files
STAGED_FILES=$(git diff --cached --name-only --diff-filter=ACM | grep '\.py$')

for file in $STAGED_FILES; do
    result=$(python -m guardrail_mcp.scan "$file")
    if echo "$result" | grep -q "CRITICAL"; then
        echo "🚫 Commit blocked by guardrail:"
        echo "$result"
        exit 1
    fi
done
```

---

## VS Code Tasks Integration

### Task: Manual Guardrail Scan

```json
// .vscode/tasks.json
{
    "version": "2.0.0",
    "tasks": [
        {
            "label": "🔒 Guardrail: Scan Current File",
            "type": "shell",
            "command": "echo '${file}' | python /path/to/guardrail_mcp/mcp_project/guardrail_server.py",
            "problemMatcher": [],
            "presentation": {
                "echo": true,
                "reveal": "always",
                "focus": false,
                "panel": "shared"
            }
        },
        {
            "label": "🔒 Guardrail: Scan All Python Files",
            "type": "shell",
            "command": "find . -name '*.py' -type f | xargs -I {} python /path/to/guardrail_mcp/mcp_project/guardrail_server.py scan",
            "problemMatcher": [],
            "group": {
                "kind": "build",
                "isDefault": false
            }
        },
        {
            "label": "🔒 Guardrail: Check Secrets",
            "type": "shell",
            "command": "python /path/to/guardrail_mcp/mcp_project/guardrail_server.py check-secrets ${file}",
            "problemMatcher": []
        }
    ]
}
```

Run with: `Cmd+Shift+P` → "Tasks: Run Task" → Select guardrail task

---

## Keybindings

Add to `.vscode/keybindings.json`:

```json
[
    {
        "key": "ctrl+shift+g",
        "command": "workbench.action.tasks.runTask",
        "args": "🔒 Guardrail: Scan Current File",
        "when": "editorTextFocus && editorLangId == python"
    },
    {
        "key": "ctrl+shift+alt+g",
        "command": "workbench.action.tasks.runTask",
        "args": "🔒 Guardrail: Check Secrets"
    }
]
```

---

## Status Bar Integration

Create a custom VS Code extension or use an existing one to show:

```
🔒 Guardrails: Active | Last scan: 2s ago | Issues: 0
```

Click to:
- Run quick scan
- View last report
- Toggle guardrail modes

---

## Problem Panel Integration

Guardrail violations appear in the Problems panel:

```
📁 Problems (2)

🔴 config.py  [1, 1]  Hardcoded password  guardrail(secrets)
🟠 app.py     [15, 5] SQL injection risk   guardrail(security)
```

Click to:
- Navigate to line
- See detailed message
- Apply suggested fix

---

## Settings

### User Settings (`settings.json`)

```json
{
    "guardrail.enabled": true,
    "guardrail.mode": "blocking",  // "blocking" | "warning" | "silent"
    "guardrail.scanOnSave": true,
    "guardrail.scanOnType": false,   // Real-time as you type (performance impact)
    "guardrail.severityFilter": "medium",  // Only show medium+
    "guardrail.autoFix": false,      // Automatically apply safe fixes
    "guardrail.excludedPaths": [
        "**/tests/**",
        "**/migrations/**"
    ],
    "guardrail.policies": {
        "licenseCheck": true,
        "complexityLimit": 15,
        "copyrightHeader": true
    }
}
```

---

## Workflows

### Daily Development Workflow

1. **Write code** in VS Code
2. **Save file** → Guardrail auto-scans
3. **See results** inline or Problems panel
4. **Fix issues** or mark as intentional
5. **Commit** → Pre-commit hook runs full scan

### Code Review Workflow

1. **Create PR** → CI runs guardrail
2. **Results posted** as PR comments
3. **Block merge** if critical issues found
4. **Approve** only when clean

### AI-Assisted Workflow

1. **Request help** from AI assistant (GitHub Copilot, etc.)
2. **AI generates** code suggestion
3. **Guardrail intercepts** and validates
4. **See warnings** before accepting
5. **Accept/Reject** with full context

---

## Troubleshooting

### Issue: Guardrail not running

```bash
# Check MCP server is running
curl -X POST http://localhost:8000/health

# Check VS Code can reach it
# View → Output → Select "MCP" from dropdown
```

### Issue: Too many false positives

```json
// Disable specific rules
{
    "guardrail.disabledRules": [
        "insecure_random",
        "style.import_order"
    ]
}
```

### Issue: Performance slow

```json
// Adjust settings
{
    "guardrail.scanOnType": false,
    "guardrail.maxFileSize": 100000,  // Skip large files
    "guardrail.timeout": 5000         // 5 second timeout
}
```

---

## Future Enhancements

1. **Native VS Code Extension**
   - Inline decorations
   - Quick fix actions
   - Guardrail explorer panel

2. **AI Assistant Integration**
   - Native Copilot integration
   - Pre-validation of suggestions
   - Learning from overrides

3. **Team Features**
   - Shared policy configurations
   - Team-wide statistics
   - Violation trends

---

## Getting Started Checklist

- [ ] Install guardrail MCP server
- [ ] Configure VS Code settings
- [ ] Add pre-commit hook
- [ ] Test with sample violations
- [ ] Train team on override process
- [ ] Set up CI/CD integration

---

**Document Version**: 1.0
**Last Updated**: March 2025
**Compatible**: VS Code 1.85+
