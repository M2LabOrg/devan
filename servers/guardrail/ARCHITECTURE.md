# Guardrail MCP - AI-Assisted SDLC Protection System

**Purpose**: Protect developers and the organization by enforcing guardrails during AI-assisted software development.

**Scope**: Real-time code scanning, policy enforcement, and security validation integrated into the development workflow.

---

## What Are Guardrail MCPs?

Guardrail MCPs act as **automated safety supervisors** that:

1. **Scan code** before it's accepted (security vulnerabilities, anti-patterns)
2. **Enforce policies (coding standards, compliance requirements)
3. **Detect secrets** (API keys, passwords, tokens accidentally leaked)
4. **Validate AI suggestions** (check if AI-generated code is safe to use)
5. **Block harmful actions** (prevent destructive operations)
6. **Log decisions** (audit trail for compliance)

---

## Architecture Overview

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│   Programmer    │────▶│     VS Code      │────▶│   AI Assistant  │
│   (writes code) │     │   (with MCPs)    │     │   (suggests)    │
└─────────────────┘     └──────────────────┘     └─────────────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │    Guardrail MCP     │
                    │  (The Safety Layer)  │
                    └──────────────────────┘
                               │
              ┌────────────────┼────────────────┐
              ▼                ▼                ▼
     ┌──────────────┐ ┌──────────────┐ ┌──────────────┐
     │ Code Scanner │ │Policy Checker│ │ Secret Guard │
     └──────────────┘ └──────────────┘ └──────────────┘
```

---

## Core Guardrail Components

### 1. **Security Scanner**
Detects:
- SQL injection vulnerabilities
- XSS (Cross-Site Scripting) risks
- Insecure crypto usage (DES, 3DES, RC4, ECB mode)
- Hardcoded credentials
- Unsafe deserialization (pickle, yaml.load)
- Path traversal vulnerabilities
- Command injection
- SSRF (Server-Side Request Forgery)
- XXE (XML External Entity)
- Disabled SSL verification
- Information disclosure in logs

### 2. **Policy Enforcer**
Validates:
- coding standards compliance
- License compatibility (MIT, Apache, BSD approved)
- Data handling regulations (GDPR, etc.)
- API usage restrictions
- Code complexity limits
- Test coverage requirements
- Human approval for high-risk operations

### 3. **Secret Detector**
Prevents:
- API keys in code (AWS, Azure, Google, GitHub, Slack)
- Database passwords
- Private tokens (RSA, DSA, EC, OpenSSH)
- Certificate files
- Connection strings
- JWT tokens (eyJ...)
- Basic Auth credentials
- Bearer tokens
- Environment variable leaks

### 4. **AI Output Validator**
Checks AI-generated code for:
- Hallucinated imports (non-existent libraries)
- Deprecated APIs
- Breaking changes
- Performance anti-patterns
- License violations

### 5. **Human-in-the-Loop Checker**
Ensures human approval for high-risk operations:
- Database migrations
- Production deployments
- Security policy changes
- Privileged access grants
- Data exports

### 6. **Security-by-Design Validator**
Validates security principles are followed:
- Least privilege
- Defense in depth
- Secure defaults
- Fail securely
- Input validation
- Separation of concerns

### 7. **Commercial SAST Integration**
Integrates with approved scanning tools:
- Veracode scanning status checks
- CI/CD pipeline configuration
- Scan reminders and compliance tracking
- Workflow generation for multiple platforms

---

## How It Works in Practice

### Scenario 1: AI Suggests Vulnerable Code

```
Programmer: "Generate a function to query user data"

AI suggests:
    def get_user(user_id):
        query = f"SELECT * FROM users WHERE id = {user_id}"
        return db.execute(query)

Guardrail MCP intercepts:
    ⚠️ SECURITY VIOLATION DETECTED
    
    Issue: SQL Injection vulnerability
    Location: Line 2
    Risk: HIGH
    
    Fix: Use parameterized queries
    
    def get_user(user_id):
        query = "SELECT * FROM users WHERE id = ?"
        return db.execute(query, (user_id,))
    
Action: Blocked until fixed or explicit override
```

### Scenario 2: Accidental Secret Commit

```
Programmer pastes:
    API_KEY = "sk-1234567890abcdef"

Guardrail MCP intercepts:
    🔒 SECRET DETECTED
    
    Type: API Key
    Pattern: sk-...
    File: config.py
    
    Options:
    1. Move to environment variable
    2. Add to .env file (gitignored)
    3. Use M2Lab secret manager
    4. Mark as false positive
    
Action: Commit blocked, guidance provided
```

### Scenario 3: Policy Violation

```
Programmer imports:
    import numpy as np  # GPL-licensed in this version

Guardrail MCP checks:
    📋 POLICY VIOLATION
    
    Issue: License incompatibility
    Package: numpy 1.x (GPL)
    M2Lab Policy: Apache/MIT/BSD only
    
    Suggestion: Use numpy 2.x (BSD license)
    
Action: Warning issued, alternative suggested
```

---

## Implementation Approach

### Phase 1: Pre-Commit Guardrails
- Run on every save
- Check current file
- Fast feedback (< 1 second)

### Phase 2: Pre-Push Guardrails
- Run before git push
- Check entire commit
- Comprehensive scan

### Phase 3: CI/CD Integration
- Run in pipeline
- Block merges on violations
- Generate compliance reports

---

## Benefits

| Benefit | Description |
|---------|-------------|
| **Risk Reduction** | Catch security issues before production |
| **Compliance** | Automated enforcement of project policies |
| **Developer Education** | Teach secure coding in real-time |
| **Audit Trail** | Log all guardrail decisions |
| **Consistency** | Same rules across all teams |
| **Speed** | Faster than manual code review for common issues |

---

## Next Steps

1. Review this architecture document
2. See example implementations in `/examples/`
3. Review VS Code integration guide
4. Pilot with one team
5. Gather feedback and iterate

---

**Document Version**: 1.1  
**Last Updated**: March 2025  
**Author**: AI-Assisted SDLC Guardrails Team  
**Tools**: 13 MCP tools | 40+ security patterns | 10+ secret patterns
