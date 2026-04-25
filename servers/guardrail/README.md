# Guardrail MCP - AI-Assisted SDLC Protection

Real-time code scanning, policy enforcement, and security validation for AI-assisted software development.

## Overview

Guardrail MCPs act as **automated safety supervisors** that protect developers and the organization by:

- **Scanning code** for security vulnerabilities
- **Enforcing project policies** and compliance requirements
- **Detecting secrets** (API keys, passwords, tokens)
- **Validating AI output** before acceptance
- **Blocking harmful actions** with clear guidance

## Quick Start

### Installation

```bash
cd guardrail_mcp/mcp_project
pip install -e .
```

### Run the Server

```bash
python guardrail_server.py
```

### Test with Examples

```bash
cd examples
python example1_code_scanner.py
python example2_secret_detection.py
python example3_ai_validation.py
python example4_extended_patterns.py
```

### Test with MCP Inspector

For interactive testing and debugging of the guardrail tools:

```bash
# Setup virtual environment
cd guardrail_mcp/mcp_project
uv venv
source .venv/bin/activate  # macOS/Linux
# .venv\Scripts\activate   # Windows

# Install MCP package
uv pip install mcp

# Run the inspector
npx @modelcontextprotocol/inspector python3 guardrail_server.py
```

The Inspector provides a web interface where you can:
- Browse all 13 available guardrail tools
- Test individual tools with custom inputs
- View tool schemas and descriptions
- Debug tool responses

**Note**: Requires Node.js and npm installed.

## Documentation

- **[ARCHITECTURE.md](ARCHITECTURE.md)** - System design and guardrail concepts
- **[VS_CODE_INTEGRATION.md](VS_CODE_INTEGRATION.md)** - Integration guide for VS Code
- **[CI_CD_INTEGRATION.md](CI_CD_INTEGRATION.md)** - DevOps pipeline integration
- **[examples/](examples/)** - Working examples of guardrail scenarios

## Key Features

### 1. Security Scanning
Detects:
- SQL injection vulnerabilities
- XSS risks (including `mark_safe` with user input)
- Insecure crypto usage (DES, 3DES, RC4, ECB mode)
- Hardcoded credentials
- Unsafe eval/exec usage
- **Path traversal** (`../` in file paths)
- **Command injection** (`os.system` with user input)
- **SSRF** (requests to internal addresses)
- **XXE** (XML external entity attacks)
- **Insecure deserialization** (pickle, yaml.load, marshal)
- **Disabled SSL verification** (`verify=False`)
- **Information disclosure** (credentials in logs/print)
- **Insecure protocols** (ftp://, telnet://)

### 2. Policy Enforcement
Validates:
- coding standards
- License compatibility
- Code complexity limits
- Required headers/copyright

### 3. Secret Detection
Prevents:
- API keys in code (AWS, Azure, Google, GitHub, Slack)
- Database passwords
- Private keys (RSA, DSA, EC, OpenSSH)
- Connection strings
- **JWT tokens** (eyJ...)
- **Basic Auth** (Basic base64...)
- **Bearer tokens** (Bearer ...)
- **Azure Storage Keys**
- **Google API Keys**

### 4. AI Output Validation
Checks for:
- Hallucinated imports
- Deprecated APIs
- Breaking changes
- Security anti-patterns

## MCP Tools

| `scan_code` | Scan code for security issues | Pre-save validation |
| `check_secrets` | Detect secrets in code | Pre-commit check |
| `validate_ai_output` | Validate AI-generated code | AI assistant integration |
| `scan_repository` | Full repository scan | CI/CD pipeline |
| `check_dependencies` | Check for vulnerable dependencies | Security audit |
| `check_code_complexity` | Analyze code complexity | Quality gate |
| `check_license_compliance` | License policy enforcement | Compliance check |
| `generate_compliance_report` | Generate audit reports | Documentation |
| `block_commit` | Pre-commit validation | Git hooks |
| `get_guardrail_config` | Get current configuration | Policy review |

## VS Code Integration

Guardrails can be integrated into VS Code through:

1. **Tasks** - Run scans on file save
2. **Pre-commit hooks** - Block commits with violations
3. **Extensions** - Real-time inline feedback (future)

See [VS_CODE_INTEGRATION.md](VS_CODE_INTEGRATION.md) for detailed setup.

## How It Protects

### Protecting M2Lab
- Enforces compliance policies
- Prevents security vulnerabilities
- Maintains audit trails
- Ensures license compliance

### Protecting Developers
- Educates on secure coding
- Catches mistakes early
- Provides specific fixes
- Reduces cognitive load

## Example Workflow

```
Developer writes code → Saves file
                              ↓
                    Guardrail MCP scans
                              ↓
                    Issues detected?
                         /        \
                       Yes          No
                       /             \
                Show warnings    ✅ Continue
                with fixes
                       \
                Developer fixes
                       |
                Repeat until clean
```

## Configuration

Guardrails can be configured via:

- Environment variables
- Configuration files
- VS Code settings
- policy database

## Roadmap

- [x] Core guardrail server
- [x] Security pattern detection (40+ patterns)
- [x] Secret detection (10+ patterns)
- [x] AI output validation
- [x] CI/CD integration (GitHub, Azure, GitLab, Jenkins)
- [x] Compliance reporting (JSON, SARIF, Markdown)
- [ ] policy database integration
- [ ] VS Code extension
- [ ] Team analytics dashboard

## Contributing

This is a M2Lab internal project. Contact the M2Lab SDLC team for contributions.

## License

MIT License - See LICENSE file

---

**For Development Teams**: Review the architecture document and examples before the next meeting. The VS Code integration guide shows how to deploy this to your development workflow.
