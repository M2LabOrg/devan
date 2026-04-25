# Guardrail MCP - Meeting Presentation Summary

**Meeting**: AI-Assisted SDLC Guardrails Review  
**Date**: March 2025  
**Audience: Engineering Leadership & Development Teams Development Teams  

---

## Executive Summary

We propose using **MCP (Model Context Protocol) based Guardrails** to protect developers and the organization during AI-assisted software development. This system provides real-time scanning, policy enforcement, and security validation directly in the development workflow.

---

## The Problem

### Current Risks with AI-Assisted Development

1. **AI Generates Vulnerable Code**
   - SQL injection vulnerabilities
   - Insecure authentication patterns
   - Hardcoded secrets in examples

2. **Accidental Secret Exposure**
   - API keys committed to repositories
   - Database passwords in config files
   - Private keys in source code

3. **Policy Violations**
   - Incompatible open-source licenses
   - Missing copyright headers
   - Non-compliant data handling

4. **Developer Education Gap**
   - Junior developers may not recognize risks
   - AI-generated code looks correct but isn't
   - No real-time feedback during coding

---

## The Solution: Guardrail MCPs

### What is MCP?

MCP (Model Context Protocol) is a standard way for AI assistants to interact with tools and data sources. Think of it as a "USB-C port" for AI capabilities.

### What are Guardrail MCPs?

Specialized MCP servers that act as **automated safety supervisors**:

```
┌─────────────────────────────────────────────────────────────┐
│                    Developer Workflow                       │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│   Developer → Writes Code → AI Suggests → Guardrail Check   │
│                                  ↓                          │
│                            Safe? → Accept                   │
│                            Unsafe? → Block + Guide          │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Three Lines of Defense

### 1. Pre-Save Guardrails (Real-Time)
**When**: Every file save  
**What**: Quick security scan of current file  
**Speed**: < 1 second  
**Blocks**: Critical security issues

### 2. Pre-Commit Guardrails (Comprehensive)
**When**: Before git commit  
**What**: Full scan of staged changes  
**Scope**: All staged files  
**Blocks**: Secrets, policy violations

### 3. CI/CD Guardrails (Enforcement)
**When**: Pull request / Merge  
**What**: Complete codebase scan  
**Blocks**: Merge if violations found  
**Reports**: Compliance documentation

---

## Live Demonstration Scenarios

### Scenario 1: AI Suggests SQL Injection

```python
# AI suggests vulnerable code:
def get_user(user_id):
    query = f"SELECT * FROM users WHERE id = {user_id}"
    return db.execute(query)

# Guardrail response:
🔴 CRITICAL: SQL Injection vulnerability detected
   File: app.py:2
   Fix: Use parameterized queries
   
   cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
```

**Value**: Prevents entire class of security vulnerabilities

---

### Scenario 2: Accidental Secret Commit

```python
# Developer accidentally includes:
API_KEY = "sk-1234567890abcdef"

# Guardrail response:
🔴 CRITICAL: API key detected
   File: config.py:1
   Fix: Move to environment variable
   
   API_KEY = os.environ.get('API_KEY')
```

**Value**: Prevents costly secret rotation and potential breaches

---

### Scenario 3: Policy Violation

```python
# AI suggests deprecated package:
import md5_hashlib  # Actually hallucinated module

# Guardrail response:
🟡 WARNING: Potentially hallucinated import
   Module 'md5_hashlib' may not exist
   
⚠️  WARNING: MD5 is deprecated
   Use SHA-256 for non-password hashing
   Use bcrypt for password hashing
```

**Value**: Prevents technical debt and security issues

---

## VS Code Integration

### How It Works in Practice

1. **Developer writes code** in VS Code
2. **Saves file** → Guardrail automatically scans
3. **See inline feedback** directly in editor
4. **Problems panel** shows all violations
5. **Quick fixes** available for common issues
6. **Pre-commit hook** blocks commits with violations

### Configuration Example

```json
// VS Code settings.json
{
  "guardrail.enabled": true,
  "guardrail.mode": "blocking",
  "guardrail.scanOnSave": true,
  "guardrail.policies": {
    "licenseCheck": true,
    "maxComplexity": 15
  }
}
```

---

## Benefits

| Benefit | Impact |
|---------|--------|
| **Risk Reduction** | Catch vulnerabilities before production |
| **Compliance** | Automated enforcement of coding standards |
| **Developer Education** | Teach secure coding in real-time |
| **Audit Trail** | Log all guardrail decisions |
| **Consistency** | Same rules across all teams |
| **Speed** | Faster than manual review for common issues |

---

## Benefits for Developers

| Benefit | Impact |
|---------|--------|
| **Immediate Feedback** | Know issues while context is fresh |
| **Specific Guidance** | Clear explanation and fix suggestions |
| **Learning** | Understand why something is risky |
| **Confidence** | Assurance that code meets standards |
| **Focus** | Less time worrying about compliance |

---

## Implementation Roadmap

### Phase 1: Pilot (4-6 weeks)
- Deploy to 2-3 volunteer teams
- Gather feedback
- Tune rule sensitivity

### Phase 2: Rollout (2-3 months)
- Deploy to all development teams
- Integrate with CI/CD pipelines
- Train team leads
- Set up compliance reporting

### Phase 3: Enhance (ongoing)
- Add org-specific policies
- Build analytics dashboard
- Integrate with AI assistants
- Extend to additional languages

---

## Discussion Points

### 1. Policy Definition
- Which policies should be automated?
- Who defines and maintains the policy database?
- How do we handle policy exceptions?

### 2. Developer Experience
- Should guardrails be blocking or advisory initially?
- How do we prevent "alert fatigue"?
- What's the override process for false positives?

### 3. Integration Strategy
- Start with VS Code or other IDEs?
- CI/CD integration priority?
- AI assistant integration (Copilot, Claude, etc.)?

### 4. Compliance & Audit
- What guardrail decisions need to be logged?
- How long should we retain audit trails?
- Who has access to violation reports?

---

## Next Steps

1. **Review this proposal** with stakeholders
2. **Select pilot teams** for initial deployment
3. **Define org-specific policies** to enforce
4. **Set up test environment** for guardrail server
5. **Schedule follow-up** to review pilot results

---

## Resources

All implementation details available in:

- `/guardrail_mcp/ARCHITECTURE.md` - Technical design
- `/guardrail_mcp/VS_CODE_INTEGRATION.md` - VS Code setup guide
- `/guardrail_mcp/CI_CD_INTEGRATION.md` - DevOps pipeline integration (GitHub, Azure, GitLab, Jenkins)
- `/guardrail_mcp/examples/` - Working demonstrations
  - `example1_code_scanner.py` - Security scanning
  - `example2_secret_detection.py` - Secret detection
  - `example3_ai_validation.py` - AI output validation
  - `example4_extended_patterns.py` - OWASP Top 10 patterns
- `/guardrail_mcp/mcp_project/` - Server implementation

## Testing with MCP Inspector

For interactive testing and debugging of the guardrail tools:

```bash
# Setup virtual environment
cd guardrail_mcp/mcp_project
uv venv
source .venv/bin/activate  # macOS/Linux

# Install MCP package
uv pip install mcp

# Run the inspector
npx @modelcontextprotocol/inspector python3 guardrail_server.py
```

This launches a web interface to browse all 13 guardrail tools, test them with custom inputs, and view schemas.

---

## Questions?

**Technical Questions**: Review the architecture document  
**Implementation Questions**: Check VS Code integration guide  
**Demo Scenarios**: Run the examples  

---

**Document Version**: 1.1  
**Last Updated**: March 2025  
**Prepared for**: M2Lab AI-Assisted SDLC Initiative  
**Patterns Coverage**: 40+ security patterns, 10+ secret patterns (OWASP Top 10 based)
