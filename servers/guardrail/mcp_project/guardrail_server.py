"""
Guardrail MCP Server - AI-Assisted SDLC Protection

This MCP server provides real-time guardrails for code safety,
policy enforcement, and security validation.
"""

import json
import re
import os
import sys
from typing import Any, Dict, List, Optional
from pathlib import Path
from dataclasses import dataclass
from enum import Enum

# MCP SDK
from mcp.server import Server
from mcp.types import TextContent, Tool, Resource


class Severity(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ViolationType(Enum):
    SECURITY = "security"
    POLICY = "policy"
    SECRET = "secret"
    STYLE = "style"
    PERFORMANCE = "performance"


@dataclass
class Violation:
    type: ViolationType
    severity: Severity
    message: str
    line: Optional[int]
    column: Optional[int]
    file: str
    fix: Optional[str]
    rule_id: str


# Security patterns to detect
SECURITY_PATTERNS = {
    "sql_injection": {
        "pattern": r'(?i)(execute|query|raw)\s*\(\s*["\'].*%s.*["\']|%\s*\w+.*execute',
        "message": "Potential SQL injection vulnerability",
        "severity": Severity.CRITICAL,
        "fix": "Use parameterized queries: cursor.execute('SELECT * FROM table WHERE id = ?', (id,))",
    },
    "hardcoded_password": {
        "pattern": r'(?i)(password|passwd|pwd)\s*=\s*["\'][^"\']+["\']',
        "message": "Hardcoded password detected",
        "severity": Severity.CRITICAL,
        "fix": "Store in environment variable: os.environ.get('DB_PASSWORD')",
    },
    "eval_usage": {
        "pattern": r'(?i)\beval\s*\(',
        "message": "Dangerous eval() usage detected",
        "severity": Severity.HIGH,
        "fix": "Use ast.literal_eval() for safe evaluation or json.loads() for JSON",
    },
    "exec_usage": {
        "pattern": r'(?i)\bexec\s*\(',
        "message": "Dangerous exec() usage detected",
        "severity": Severity.HIGH,
        "fix": "Avoid exec(). Consider alternative approaches like functions or configuration files",
    },
    "insecure_random": {
        "pattern": r'(?i)import\s+random\b(?!\s*as)',
        "message": "Insecure random number generator for cryptographic use",
        "severity": Severity.MEDIUM,
        "fix": "Use secrets module for cryptographic operations: import secrets; secrets.token_hex(16)",
    },
    "debug_mode": {
        "pattern": r'(?i)(debug\s*=\s*True|DEBUG\s*=\s*True)',
        "message": "Debug mode enabled - security risk in production",
        "severity": Severity.HIGH,
        "fix": "Set debug=False in production environments",
    },
}


# Secret patterns to detect
SECRET_PATTERNS = {
    "aws_access_key": {
        "pattern": r'AKIA[0-9A-Z]{16}',
        "message": "AWS Access Key ID detected",
        "severity": Severity.CRITICAL,
    },
    "api_key_generic": {
        "pattern": r'(?i)(api[_-]?key|apikey)\s*[=:]\s*["\']\w{20,}["\']',
        "message": "Potential API key detected",
        "severity": Severity.HIGH,
    },
    "private_key": {
        "pattern": r'-----BEGIN (RSA |DSA |EC |OPENSSH )?PRIVATE KEY-----',
        "message": "Private key detected",
        "severity": Severity.CRITICAL,
    },
    "github_token": {
        "pattern": r'ghp_[a-zA-Z0-9]{36}',
        "message": "GitHub Personal Access Token detected",
        "severity": Severity.CRITICAL,
    },
    "slack_token": {
        "pattern": r'xox[baprs]-[0-9]{10,13}-[0-9]{10,13}',
        "message": "Slack token detected",
        "severity": Severity.CRITICAL,
    },
}


# Additional patterns for new tools
LICENSE_PATTERNS = {
    "gpl_license": {
        "pattern": r'(?i)(gpl|gnu general public license)',
        "message": "GPL license detected - may conflict with project license policy",
        "severity": Severity.HIGH,
    },
    "mit_license": {
        "pattern": r'(?i)mit license',
        "message": "MIT license - approved for use",
        "severity": Severity.LOW,
    },
}

# Dependency vulnerability patterns (simplified)
VULNERABLE_PATTERNS = {
    "pickle_usage": {
        "pattern": r'(?i)pickle\.(load|loads)',
        "message": "pickle usage detected - potential arbitrary code execution",
        "severity": Severity.HIGH,
        "fix": "Use json.loads() for safe deserialization or implement proper input validation",
    },
    "yaml_load": {
        "pattern": r'(?i)yaml\.load\(',
        "message": "Unsafe yaml.load() - use yaml.safe_load() instead",
        "severity": Severity.HIGH,
        "fix": "Replace yaml.load() with yaml.safe_load()",
    },
    "subprocess_shell": {
        "pattern": r'(?i)subprocess\.(run|call|check_output).*shell\s*=\s*True',
        "message": "Subprocess with shell=True - command injection risk",
        "severity": Severity.HIGH,
        "fix": "Use shell=False and pass command as list: subprocess.run(['ls', '-la'])",
    },
}

# Extended security patterns based on OWASP Top 10 and industry best practices
EXTENDED_SECRET_PATTERNS = {
    "azure_storage_key": {
        "pattern": r'DefaultEndpointsProtocol=https;AccountName=[^;]+;AccountKey=[^;]+;',
        "message": "Azure Storage Account Key detected",
        "severity": Severity.CRITICAL,
    },
    "google_api_key": {
        "pattern": r'AIza[0-9A-Za-z_-]{35}',
        "message": "Google API Key detected",
        "severity": Severity.CRITICAL,
    },
    "jwt_token": {
        "pattern": r'eyJ[A-Za-z0-9_/+-]*={0,2}\.eyJ[A-Za-z0-9_/+-]*={0,2}\.[A-Za-z0-9._/+-]*={0,2}',
        "message": "Potential JWT token detected",
        "severity": Severity.HIGH,
    },
    "basic_auth": {
        "pattern": r'(?i)basic\s+[a-zA-Z0-9+/:]{20,}={0,2}',
        "message": "Basic authentication credentials detected",
        "severity": Severity.CRITICAL,
    },
    "bearer_token": {
        "pattern": r'(?i)bearer\s+[a-zA-Z0-9_\-\.=]{20,}',
        "message": "Bearer token detected in code",
        "severity": Severity.HIGH,
    },
}

EXTENDED_SECURITY_PATTERNS = {
    # Cryptographic Failures (OWASP A02:2021)
    "weak_cipher": {
        "pattern": r'(?i)DES\s*\.|3DES|RC4|RC2|Blowfish',
        "message": "Weak cryptographic cipher detected",
        "severity": Severity.HIGH,
        "fix": "Use AES-256-GCM or ChaCha20-Poly1305",
    },
    "ecb_mode": {
        "pattern": r'(?i)AES.*ECB|Cipher\.MODE_ECB',
        "message": "ECB mode detected - insecure encryption mode",
        "severity": Severity.HIGH,
        "fix": "Use CBC with proper IV or GCM mode instead of ECB",
    },
    "static_key": {
        "pattern": r'(?i)fernet.*key\s*=\s*["\']',
        "message": "Static Fernet encryption key detected",
        "severity": Severity.CRITICAL,
        "fix": "Generate Fernet keys at runtime and store securely",
    },
    # Path Traversal (OWASP A01:2021)
    "path_traversal_unsafe": {
        "pattern": r'open\s*\([^)]*(?:\.\./|\.\.\\\\)',
        "message": "Path traversal vulnerability - unsafe file path construction",
        "severity": Severity.CRITICAL,
        "fix": "Use os.path.abspath() and validate against allowed base directory",
    },
    "unsafe_file_join": {
        "pattern": r'os\.path\.join\s*\([^)]*request\.(?:GET|POST|args|form)',
        "message": "User input used directly in path construction",
        "severity": Severity.HIGH,
        "fix": "Sanitize and validate user input before path construction",
    },
    # XXE - XML External Entity (OWASP A05:2021)
    "xxe_vulnerable_xml": {
        "pattern": r'(?i)xml\.etree\.ElementTree\.parse|ET\.parse\s*\([^)]+\)',
        "message": "Potentially vulnerable XML parsing - may be susceptible to XXE",
        "severity": Severity.HIGH,
        "fix": "Use defusedxml library or disable external entity resolution",
    },
    # SSRF - Server-Side Request Forgery (OWASP A10:2021)
    "ssrf_request": {
        "pattern": r'requests\.(?:get|post)\s*\([^)]*(?:http://localhost|http://127\.0\.0\.1|http://0\.0\.0\.0|file://)',
        "message": "Potential SSRF - request to internal/local address",
        "severity": Severity.HIGH,
        "fix": "Validate URLs against allowlist, block internal IPs",
    },
    # XSS - Cross-Site Scripting (OWASP A03:2021)
    "xss_mark_safe": {
        "pattern": r'mark_safe\s*\([^)]*(?:request\.|user_)',
        "message": "mark_safe with user input - XSS vulnerability",
        "severity": Severity.CRITICAL,
        "fix": "Never use mark_safe with untrusted input",
    },
    # Deserialization (OWASP A08:2021)
    "unsafe_pickle_load": {
        "pattern": r'pickle\.(?:load|loads)\s*\(',
        "message": "Unsafe pickle deserialization - arbitrary code execution risk",
        "severity": Severity.CRITICAL,
        "fix": "Use json.loads() or implement signed/encrypted serialization",
    },
    "marshal_load": {
        "pattern": r'marshal\.(?:load|loads)\s*\(',
        "message": "Unsafe marshal deserialization - arbitrary code execution",
        "severity": Severity.CRITICAL,
        "fix": "Use json for data serialization instead of marshal",
    },
    # Command Injection (OWASP A03:2021)
    "os_system_user_input": {
        "pattern": r'os\.system\s*\([^)]*(?:request\.|input|user_|params)',
        "message": "Command injection - user input in os.system()",
        "severity": Severity.CRITICAL,
        "fix": "Never pass user input to shell commands. Use subprocess with array args",
    },
    # Security Misconfiguration
    "disable_certificate_verify": {
        "pattern": r'verify\s*=\s*False',
        "message": "SSL certificate verification disabled - man-in-the-middle risk",
        "severity": Severity.CRITICAL,
        "fix": "Always use verify=True with proper certificates",
    },
    "insecure_protocol": {
        "pattern": r'ftp://|telnet://',
        "message": "Insecure protocol detected - use SFTP/FTPS or SSH instead",
        "severity": Severity.HIGH,
        "fix": "Use encrypted protocols (HTTPS, SFTP, SSH)",
    },
    # Information Disclosure
    "debug_print_credentials": {
        "pattern": r'print\s*\([^)]*(?:password|secret|key|token|credential)',
        "message": "Potential credential logging to console/output",
        "severity": Severity.HIGH,
        "fix": "Never log credentials. Use structured logging with redaction",
    },
    "logging_sensitive_data": {
        "pattern": r'(?:logger|logging)\.[a-z]+\s*\([^)]*(?:password|ssn|credit|card|cvv|pin)',
        "message": "Sensitive data may be logged - compliance violation",
        "severity": Severity.HIGH,
        "fix": "Redact or mask sensitive data before logging",
    },
}

# Merge extended patterns
SECRET_PATTERNS.update(EXTENDED_SECRET_PATTERNS)
SECURITY_PATTERNS.update(EXTENDED_SECURITY_PATTERNS)


# PII (Personally Identifiable Information) patterns — for data protection in sandbox mode
PII_PATTERNS = {
    "email": {
        "pattern": r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b',
        "message": "Email address detected",
        "severity": Severity.HIGH,
        "category": "PII",
        "redact_with": "[REDACTED-EMAIL]",
    },
    "phone_us": {
        "pattern": r'\b(?:\+1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b',
        "message": "US phone number detected",
        "severity": Severity.HIGH,
        "category": "PII",
        "redact_with": "[REDACTED-PHONE]",
    },
    "phone_intl": {
        "pattern": r'\+(?:[0-9] ?){6,14}[0-9]',
        "message": "International phone number detected",
        "severity": Severity.HIGH,
        "category": "PII",
        "redact_with": "[REDACTED-PHONE]",
    },
    "ssn": {
        "pattern": r'\b\d{3}-\d{2}-\d{4}\b',
        "message": "Social Security Number (SSN) detected",
        "severity": Severity.CRITICAL,
        "category": "PII",
        "redact_with": "[REDACTED-SSN]",
    },
    "credit_card": {
        "pattern": r'\b(?:4[0-9]{12}(?:[0-9]{3})?|5[1-5][0-9]{14}|3[47][0-9]{13}|3(?:0[0-5]|[68][0-9])[0-9]{11}|6(?:011|5[0-9]{2})[0-9]{12}|(?:2131|1800|35\d{3})\d{11})\b',
        "message": "Credit/debit card number detected",
        "severity": Severity.CRITICAL,
        "category": "PII/PCI",
        "redact_with": "[REDACTED-CARD-NUMBER]",
    },
    "iban": {
        "pattern": r'\b[A-Z]{2}\d{2}[A-Z0-9]{4}\d{7}(?:[A-Z0-9]{0,16})?\b',
        "message": "IBAN (bank account number) detected",
        "severity": Severity.CRITICAL,
        "category": "PII/Financial",
        "redact_with": "[REDACTED-IBAN]",
    },
    "ip_address_private": {
        "pattern": r'\b(?:10\.\d{1,3}\.\d{1,3}\.\d{1,3}|172\.(?:1[6-9]|2\d|3[01])\.\d{1,3}\.\d{1,3}|192\.168\.\d{1,3}\.\d{1,3})\b',
        "message": "Private/internal IP address detected",
        "severity": Severity.MEDIUM,
        "category": "Infrastructure",
        "redact_with": "[REDACTED-INTERNAL-IP]",
    },
    "date_of_birth": {
        "pattern": r'(?i)(?:dob|date[\s_-]of[\s_-]birth|birth[\s_-]date)[\s:=]+\d{1,2}[/\-]\d{1,2}[/\-]\d{2,4}',
        "message": "Date of birth indicator detected",
        "severity": Severity.HIGH,
        "category": "PII",
        "redact_with": "[REDACTED-DOB]",
    },
    "national_id": {
        "pattern": r'(?i)(?:national[\s_-]id|id[\s_-]number|nin|nric|national[\s_-]insurance)[\s:=]+[A-Z0-9]{6,15}',
        "message": "National ID number detected",
        "severity": Severity.CRITICAL,
        "category": "PII",
        "redact_with": "[REDACTED-NATIONAL-ID]",
    },
    "medical_record": {
        "pattern": r'(?i)(?:mrn|patient[\s_-]id|medical[\s_-]record[\s_-](?:number|no)|health[\s_-]id)[\s:=]+[A-Z0-9]{5,15}',
        "message": "Medical record / Patient ID detected",
        "severity": Severity.CRITICAL,
        "category": "PII/PHI",
        "redact_with": "[REDACTED-MEDICAL-ID]",
    },
    "drivers_license": {
        "pattern": r'(?i)(?:driver[\s_-]?s?[\s_-]?license|dl[\s_-]?number|license[\s_-]number)[\s:=]+[A-Z0-9]{6,12}',
        "message": "Driver's license number detected",
        "severity": Severity.HIGH,
        "category": "PII",
        "redact_with": "[REDACTED-DRIVERS-LICENSE]",
    },
    "passport_number": {
        "pattern": r'(?i)(?:passport[\s_-](?:number|no))[\s:=]+[A-Z]{1,2}[0-9]{6,9}',
        "message": "Passport number detected",
        "severity": Severity.CRITICAL,
        "category": "PII",
        "redact_with": "[REDACTED-PASSPORT]",
    },
    "tax_id": {
        "pattern": r'(?i)(?:tax[\s_-]?(?:id|identification)|tin|ein|taxpayer[\s_-]id)[\s:=]+\d{2}-\d{7}',
        "message": "Tax ID / EIN detected",
        "severity": Severity.HIGH,
        "category": "PII/Financial",
        "redact_with": "[REDACTED-TAX-ID]",
    },
}

POLICIES = {
    "license_check": {
        "allowed": ["MIT", "Apache-2.0", "BSD-3-Clause", "BSD-2-Clause"],
        "blocked": ["GPL", "AGPL", "LGPL", "Proprietary"],
        "severity": Severity.HIGH,
    },
    "max_complexity": {
        "max_cyclomatic": 15,
        "max_lines_per_function": 100,
        "severity": Severity.MEDIUM,
    },
    "required_headers": {
        "copyright": "Copyright (c) M2Lab",
        "license": "SPDX-License-Identifier",
        "severity": Severity.LOW,
    },
}


# Create MCP server
app = Server("guardrail-mcp")


@app.list_tools()
async def list_tools() -> List[Tool]:
    return [
        Tool(
            name="scan_code",
            description="Scan code for security vulnerabilities and policy violations",
            inputSchema={
                "type": "object",
                "properties": {
                    "code": {
                        "type": "string",
                        "description": "Source code to scan",
                    },
                    "language": {
                        "type": "string",
                        "description": "Programming language (python, javascript, etc.)",
                        "default": "python",
                    },
                    "filename": {
                        "type": "string",
                        "description": "Name of the file",
                        "default": "unknown.py",
                    },
                },
                "required": ["code"],
            },
        ),
        Tool(
            name="check_secrets",
            description="Detect secrets, API keys, and credentials in code",
            inputSchema={
                "type": "object",
                "properties": {
                    "code": {
                        "type": "string",
                        "description": "Source code to check",
                    },
                    "filename": {
                        "type": "string",
                        "description": "Name of the file",
                        "default": "unknown.py",
                    },
                },
                "required": ["code"],
            },
        ),
        Tool(
            name="validate_ai_output",
            description="Validate AI-generated code for safety and policy compliance",
            inputSchema={
                "type": "object",
                "properties": {
                    "code": {
                        "type": "string",
                        "description": "AI-generated code to validate",
                    },
                    "intent": {
                        "type": "string",
                        "description": "What the code is supposed to do",
                    },
                    "filename": {
                        "type": "string",
                        "description": "Name of the file",
                        "default": "generated.py",
                    },
                },
                "required": ["code"],
            },
        ),
        Tool(
            name="scan_repository",
            description="Scan an entire repository for security issues and policy violations",
            inputSchema={
                "type": "object",
                "properties": {
                    "repo_path": {
                        "type": "string",
                        "description": "Path to the repository root",
                    },
                    "file_extensions": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "File extensions to scan (e.g., ['.py', '.js'])",
                        "default": [".py"],
                    },
                    "include_secrets": {
                        "type": "boolean",
                        "description": "Also check for secrets",
                        "default": True,
                    },
                },
                "required": ["repo_path"],
            },
        ),
        Tool(
            name="check_dependencies",
            description="Check dependencies for known vulnerabilities and license compliance",
            inputSchema={
                "type": "object",
                "properties": {
                    "requirements_file": {
                        "type": "string",
                        "description": "Path to requirements.txt or similar",
                    },
                    "package_json": {
                        "type": "string",
                        "description": "Path to package.json for Node.js projects",
                    },
                    "check_licenses": {
                        "type": "boolean",
                        "description": "Check license compliance",
                        "default": True,
                    },
                },
                "required": [],
            },
        ),
        Tool(
            name="check_code_complexity",
            description="Analyze code complexity and enforce complexity limits",
            inputSchema={
                "type": "object",
                "properties": {
                    "code": {
                        "type": "string",
                        "description": "Source code to analyze",
                    },
                    "filename": {
                        "type": "string",
                        "description": "Name of the file",
                        "default": "unknown.py",
                    },
                    "max_cyclomatic": {
                        "type": "integer",
                        "description": "Maximum cyclomatic complexity allowed",
                        "default": 15,
                    },
                },
                "required": ["code"],
            },
        ),
        Tool(
            name="check_license_compliance",
            description="Check if code and dependencies comply with license policy",
            inputSchema={
                "type": "object",
                "properties": {
                    "license_text": {
                        "type": "string",
                        "description": "License text to check",
                    },
                    "license_file_path": {
                        "type": "string",
                        "description": "Path to LICENSE file",
                    },
                },
                "required": [],
            },
        ),
        Tool(
            name="generate_compliance_report",
            description="Generate a comprehensive compliance report for auditing",
            inputSchema={
                "type": "object",
                "properties": {
                    "repo_path": {
                        "type": "string",
                        "description": "Path to repository",
                    },
                    "report_format": {
                        "type": "string",
                        "enum": ["json", "markdown", "sarif"],
                        "description": "Report output format",
                        "default": "markdown",
                    },
                    "include_severity": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Include violations of these severities",
                        "default": ["critical", "high", "medium"],
                    },
                },
                "required": ["repo_path"],
            },
        ),
        Tool(
            name="block_commit",
            description="Check if a commit should be blocked based on guardrail violations",
            inputSchema={
                "type": "object",
                "properties": {
                    "files": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of files to check (staged files)",
                    },
                    "block_on_severity": {
                        "type": "string",
                        "enum": ["critical", "high", "medium", "low"],
                        "description": "Minimum severity to block commit",
                        "default": "critical",
                    },
                },
                "required": ["files"],
            },
        ),
        Tool(
            name="get_guardrail_config",
            description="Get current guardrail configuration and enabled rules",
            inputSchema={
                "type": "object",
                "properties": {},
            },
        ),
        Tool(
            name="check_pii",
            description=(
                "Detect personally identifiable information (PII) and regulated data in text or code. "
                "Checks for emails, phone numbers, SSNs, credit card numbers, IBANs, medical record IDs, "
                "passport numbers, national IDs, tax IDs, and driver's license numbers. "
                "Use this before sending data to any LLM to ensure restricted data is not exposed."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "text": {
                        "type": "string",
                        "description": "Text or code to scan for PII",
                    },
                    "filename": {
                        "type": "string",
                        "description": "Source filename or label (optional)",
                        "default": "input",
                    },
                    "categories": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "PII categories to check (e.g. ['PII', 'PII/PHI', 'PII/PCI']). Leave empty for all.",
                        "default": [],
                    },
                },
                "required": ["text"],
            },
        ),
        Tool(
            name="redact_sensitive_data",
            description=(
                "Redact PII, secrets, and sensitive data from text by replacing detected values with "
                "[REDACTED-TYPE] placeholders. Safe to use before logging or sending data to an LLM. "
                "Returns both the redacted text and a summary of what was removed."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "text": {
                        "type": "string",
                        "description": "Text to redact sensitive data from",
                    },
                    "redact_pii": {
                        "type": "boolean",
                        "description": "Redact PII patterns (email, phone, SSN, etc.)",
                        "default": True,
                    },
                    "redact_secrets": {
                        "type": "boolean",
                        "description": "Redact secrets and API keys",
                        "default": True,
                    },
                },
                "required": ["text"],
            },
        ),
        Tool(
            name="check_human_in_the_loop",
            description="Check if human approval is required for high-risk operations",
            inputSchema={
                "type": "object",
                "properties": {
                    "operation_type": {
                        "type": "string",
                        "enum": ["database_migration", "production_deploy", "security_policy_change", "privileged_access", "data_export"],
                        "description": "Type of operation requiring approval",
                    },
                    "risk_level": {
                        "type": "string",
                        "enum": ["low", "medium", "high", "critical"],
                        "description": "Risk level of the operation",
                        "default": "medium",
                    },
                    "approvers": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of required approver roles",
                        "default": ["team_lead"],
                    },
                    "code_changes": {
                        "type": "string",
                        "description": "Description of code changes (optional)",
                    },
                },
                "required": ["operation_type"],
            },
        ),
        Tool(
            name="check_security_by_design",
            description="Validate security-by-design principles are followed",
            inputSchema={
                "type": "object",
                "properties": {
                    "code": {
                        "type": "string",
                        "description": "Source code to analyze",
                    },
                    "filename": {
                        "type": "string",
                        "description": "Name of the file",
                        "default": "unknown.py",
                    },
                    "check_principles": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Security principles to check",
                        "default": ["least_privilege", "defense_in_depth", "secure_defaults", "fail_securely"],
                    },
                },
                "required": ["code"],
            },
        ),
        Tool(
            name="check_veracode_scan",
            description="Check Veracode scanning status and provide setup guidance for commercial SAST integration",
            inputSchema={
                "type": "object",
                "properties": {
                    "app_id": {
                        "type": "string",
                        "description": "Veracode Application ID (optional - will try to detect)",
                    },
                    "repo_path": {
                        "type": "string",
                        "description": "Path to repository to scan",
                        "default": ".",
                    },
                    "check_ci_cd": {
                        "type": "boolean",
                        "description": "Check if Veracode is configured in CI/CD pipelines",
                        "default": True,
                    },
                    "api_id": {
                        "type": "string",
                        "description": "Veracode API ID (from environment or config)",
                    },
                    "api_key": {
                        "type": "string",
                        "description": "Veracode API Key (from environment or config)",
                    },
                    "action": {
                        "type": "string",
                        "enum": ["check_status", "setup_guidance", "remind_scan", "generate_workflow"],
                        "description": "Action to perform",
                        "default": "check_status",
                    },
                },
                "required": [],
            },
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
    if name == "scan_code":
        return await scan_code(arguments)
    elif name == "check_secrets":
        return await check_secrets(arguments)
    elif name == "validate_ai_output":
        return await validate_ai_output(arguments)
    elif name == "scan_repository":
        return await scan_repository(arguments)
    elif name == "check_dependencies":
        return await check_dependencies(arguments)
    elif name == "check_code_complexity":
        return await check_code_complexity(arguments)
    elif name == "check_license_compliance":
        return await check_license_compliance(arguments)
    elif name == "generate_compliance_report":
        return await generate_compliance_report(arguments)
    elif name == "block_commit":
        return await block_commit(arguments)
    elif name == "get_guardrail_config":
        return await get_guardrail_config(arguments)
    elif name == "check_human_in_the_loop":
        return await check_human_in_the_loop(arguments)
    elif name == "check_security_by_design":
        return await check_security_by_design(arguments)
    elif name == "check_veracode_scan":
        return await check_veracode_scan(arguments)
    elif name == "check_pii":
        return await check_pii(arguments)
    elif name == "redact_sensitive_data":
        return await redact_sensitive_data(arguments)
    else:
        raise ValueError(f"Unknown tool: {name}")


async def scan_code(args: Dict[str, Any]) -> List[TextContent]:
    code = args.get("code", "")
    language = args.get("language", "python")
    filename = args.get("filename", "unknown.py")
    
    violations = []
    
    # Security scan
    for rule_name, rule in SECURITY_PATTERNS.items():
        for match in re.finditer(rule["pattern"], code, re.MULTILINE):
            start_pos = match.start()
            line_num = code[:start_pos].count('\n') + 1
            
            violation = Violation(
                type=ViolationType.SECURITY,
                severity=rule["severity"],
                message=rule["message"],
                line=line_num,
                column=None,
                file=filename,
                fix=rule.get("fix"),
                rule_id=rule_name,
            )
            violations.append(violation)
    
    # Generate report
    if violations:
        report = format_violation_report(violations)
        return [TextContent(type="text", text=report)]
    else:
        return [TextContent(type="text", text="✅ No security violations detected in the scanned code.")]


async def check_secrets(args: Dict[str, Any]) -> List[TextContent]:
    code = args.get("code", "")
    filename = args.get("filename", "unknown.py")
    
    secrets_found = []
    
    for secret_type, pattern in SECRET_PATTERNS.items():
        for match in re.finditer(pattern["pattern"], code, re.MULTILINE):
            start_pos = match.start()
            line_num = code[:start_pos].count('\n') + 1
            
            violation = Violation(
                type=ViolationType.SECRET,
                severity=pattern["severity"],
                message=pattern["message"],
                line=line_num,
                column=None,
                file=filename,
                fix="Move to environment variable or secret manager",
                rule_id=secret_type,
            )
            secrets_found.append(violation)
    
    if secrets_found:
        report = format_violation_report(secrets_found)
        return [TextContent(type="text", text=report)]
    else:
        return [TextContent(type="text", text="✅ No secrets detected in the scanned code.")]


async def validate_ai_output(args: Dict[str, Any]) -> List[TextContent]:
    code = args.get("code", "")
    intent = args.get("intent", "")
    filename = args.get("filename", "generated.py")
    
    all_violations = []
    warnings = []
    
    # Run security scan
    for rule_name, rule in SECURITY_PATTERNS.items():
        for match in re.finditer(rule["pattern"], code, re.MULTILINE):
            start_pos = match.start()
            line_num = code[:start_pos].count('\n') + 1
            
            violation = Violation(
                type=ViolationType.SECURITY,
                severity=rule["severity"],
                message=rule["message"],
                line=line_num,
                column=None,
                file=filename,
                fix=rule.get("fix"),
                rule_id=rule_name,
            )
            all_violations.append(violation)
    
    # Check for secrets
    for secret_type, pattern in SECRET_PATTERNS.items():
        for match in re.finditer(pattern["pattern"], code, re.MULTILINE):
            start_pos = match.start()
            line_num = code[:start_pos].count('\n') + 1
            
            violation = Violation(
                type=ViolationType.SECRET,
                severity=pattern["severity"],
                message=pattern["message"],
                line=line_num,
                column=None,
                file=filename,
                fix="Remove or secure this secret",
                rule_id=secret_type,
            )
            all_violations.append(violation)
    
    # Check for common AI hallucinations
    hallucination_warnings = check_ai_hallucinations(code)
    warnings.extend(hallucination_warnings)
    
    # Build comprehensive report
    report_lines = ["🛡️ AI OUTPUT VALIDATION REPORT", "=" * 50, ""]
    
    if all_violations:
        critical = [v for v in all_violations if v.severity == Severity.CRITICAL]
        high = [v for v in all_violations if v.severity == Severity.HIGH]
        medium = [v for v in all_violations if v.severity == Severity.MEDIUM]
        low = [v for v in all_violations if v.severity == Severity.LOW]
        
        if critical:
            report_lines.append(f"🔴 CRITICAL ({len(critical)}): Must fix before accepting")
        if high:
            report_lines.append(f"🟠 HIGH ({len(high)}): Should fix")
        if medium:
            report_lines.append(f"🟡 MEDIUM ({len(medium)}): Consider fixing")
        if low:
            report_lines.append(f"🔵 LOW ({len(low)}): Minor issues")
        
        report_lines.append("")
        report_lines.append(format_violation_report(all_violations))
    else:
        report_lines.append("✅ No security violations detected")
    
    if warnings:
        report_lines.append("\n⚠️ WARNINGS:")
        for warning in warnings:
            report_lines.append(f"  • {warning}")
    
    if not all_violations and not warnings:
        report_lines.append("\n✅ AI-generated code passed all guardrail checks!")
    
    return [TextContent(type="text", text="\n".join(report_lines))]


def check_ai_hallucinations(code: str) -> List[str]:
    warnings = []
    
    # Check for imports that might not exist
    import_pattern = r'^import\s+(\w+)|^from\s+(\w+)\s+import'
    common_hallucinations = [
        "crypto_utils", "secure_hash", "auth_helper", 
        "db_manager", "api_client_v2", "utils2"
    ]
    
    for match in re.finditer(import_pattern, code, re.MULTILINE):
        module = match.group(1) or match.group(2)
        if module in common_hallucinations:
            warnings.append(f"Potentially hallucinated import: '{module}' - verify this module exists")
    
    # Check for deprecated patterns
    if "md5(" in code:
        warnings.append("MD5 is deprecated for security - use SHA-256 or stronger")
    
    if "sha1(" in code:
        warnings.append("SHA-1 is deprecated for security - use SHA-256 or stronger")
    
    # Check for TODO/FIXME that AI often leaves
    if re.search(r'#\s*(TODO|FIXME|XXX)', code, re.IGNORECASE):
        warnings.append("Code contains TODO/FIXME comments - review for completeness")
    
    return warnings


def format_violation_report(violations: List[Violation]) -> str:
    lines = []
    
    for v in violations:
        severity_emoji = {
            Severity.CRITICAL: "🔴",
            Severity.HIGH: "🟠",
            Severity.MEDIUM: "🟡",
            Severity.LOW: "🔵",
        }.get(v.severity, "⚪")
        
        lines.append(f"{severity_emoji} [{v.severity.value.upper()}] {v.type.value.upper()}")
        lines.append(f"   Rule: {v.rule_id}")
        lines.append(f"   File: {v.file}:{v.line or '?'}")
        lines.append(f"   Issue: {v.message}")
        if v.fix:
            lines.append(f"   Fix: {v.fix}")
        lines.append("")
    
    return "\n".join(lines)


async def get_guardrail_config(args: Dict[str, Any]) -> List[TextContent]:
    config = {
        "enabled_security_rules": list(SECURITY_PATTERNS.keys()),
        "enabled_secret_patterns": list(SECRET_PATTERNS.keys()),
        "policies": {
            "allowed_licenses": POLICIES["license_check"]["allowed"],
            "max_complexity": POLICIES["max_complexity"]["max_cyclomatic"],
        },
        "severity_levels": ["low", "medium", "high", "critical"],
        "version": "1.0.0",
    }
    
    return [TextContent(type="text", text=json.dumps(config, indent=2))]


async def scan_repository(args: Dict[str, Any]) -> List[TextContent]:
    """Scan entire repository for issues."""
    repo_path = args.get("repo_path", ".")
    file_extensions = args.get("file_extensions", [".py"])
    include_secrets = args.get("include_secrets", True)
    
    all_violations = []
    files_scanned = 0
    
    try:
        path = Path(repo_path)
        for ext in file_extensions:
            for file_path in path.rglob(f"*{ext}"):
                if ".git" in str(file_path):
                    continue
                try:
                    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                        code = f.read()
                    
                    # Check security patterns
                    for rule_name, rule in {**SECURITY_PATTERNS, **VULNERABLE_PATTERNS}.items():
                        for match in re.finditer(rule["pattern"], code, re.MULTILINE):
                            start_pos = match.start()
                            line_num = code[:start_pos].count("\n") + 1
                            
                            violation = Violation(
                                type=ViolationType.SECURITY,
                                severity=rule["severity"],
                                message=rule["message"],
                                line=line_num,
                                column=None,
                                file=str(file_path),
                                fix=rule.get("fix"),
                                rule_id=rule_name,
                            )
                            all_violations.append(violation)
                    
                    # Check secrets if enabled
                    if include_secrets:
                        for secret_type, pattern in SECRET_PATTERNS.items():
                            for match in re.finditer(pattern["pattern"], code, re.MULTILINE):
                                start_pos = match.start()
                                line_num = code[:start_pos].count("\n") + 1
                                
                                violation = Violation(
                                    type=ViolationType.SECRET,
                                    severity=pattern["severity"],
                                    message=pattern["message"],
                                    line=line_num,
                                    column=None,
                                    file=str(file_path),
                                    fix="Move to environment variable or secret manager",
                                    rule_id=secret_type,
                                )
                                all_violations.append(violation)
                    
                    files_scanned += 1
                except Exception:
                    continue
        
        # Generate summary report
        report_lines = [
            f"📊 REPOSITORY SCAN REPORT",
            f"=" * 50,
            f"",
            f"Repository: {repo_path}",
            f"Files scanned: {files_scanned}",
            f"Total violations: {len(all_violations)}",
            f"",
        ]
        
        if all_violations:
            critical = len([v for v in all_violations if v.severity == Severity.CRITICAL])
            high = len([v for v in all_violations if v.severity == Severity.HIGH])
            medium = len([v for v in all_violations if v.severity == Severity.MEDIUM])
            low = len([v for v in all_violations if v.severity == Severity.LOW])
            
            report_lines.extend([
                f"Severity breakdown:",
                f"  🔴 Critical: {critical}",
                f"  🟠 High: {high}",
                f"  🟡 Medium: {medium}",
                f"  🔵 Low: {low}",
                f"",
                f"Detailed findings:",
                f"-" * 30,
            ])
            report_lines.append(format_violation_report(all_violations))
        else:
            report_lines.append("✅ No violations detected in repository!")
        
        return [TextContent(type="text", text="\n".join(report_lines))]
        
    except Exception as e:
        return [TextContent(type="text", text=f"❌ Error scanning repository: {str(e)}")]


async def check_dependencies(args: Dict[str, Any]) -> List[TextContent]:
    """Check dependencies for vulnerabilities and license compliance."""
    requirements_file = args.get("requirements_file")
    package_json = args.get("package_json")
    check_licenses = args.get("check_licenses", True)
    
    report_lines = ["📦 DEPENDENCY CHECK REPORT", "=" * 50, ""]
    issues = []
    
    # Check Python requirements
    if requirements_file and os.path.exists(requirements_file):
        with open(requirements_file, "r") as f:
            deps = f.read()
        
        report_lines.append(f"Checked: {requirements_file}")
        
        # Check for known vulnerable patterns in dependencies
        vulnerable_packages = {
            "django<3.2": "CVE-2021-31542 - Upgrade to Django 3.2+",
            "flask<2.0": "CVE-2021-XXXX - Upgrade to Flask 2.0+",
            "requests<2.26": "CVE-2021-XXXX - Upgrade to requests 2.26+",
            "urllib3<1.26": "CVE-2021-XXXX - Upgrade to urllib3 1.26+",
        }
        
        for pkg, issue in vulnerable_packages.items():
            if pkg in deps.lower():
                issues.append(f"🟠 {pkg}: {issue}")
    
    # Check Node.js dependencies
    if package_json and os.path.exists(package_json):
        import json as json_lib
        with open(package_json, "r") as f:
            try:
                pkg_data = json_lib.load(f)
                report_lines.append(f"Checked: {package_json}")
                
                # Check for known vulnerable npm packages
                all_deps = {**pkg_data.get("dependencies", {}), **pkg_data.get("devDependencies", {})}
                
                vulnerable_npm = {
                    "lodash": "<4.17.21 has prototype pollution vulnerabilities",
                    "minimist": "<1.2.6 has prototype pollution",
                    "ansi-regex": "<5.0.1 has ReDoS vulnerability",
                }
                
                for pkg, version in all_deps.items():
                    if pkg in vulnerable_npm:
                        issues.append(f"🟠 npm/{pkg}@{version}: {vulnerable_npm[pkg]}")
            except json_lib.JSONDecodeError:
                issues.append("⚠️ Could not parse package.json")
    
    # License compliance check
    if check_licenses:
        report_lines.append("")
        report_lines.append("📋 License Compliance:")
        report_lines.append(f"  Allowed: {', '.join(POLICIES['license_check']['allowed'])}")
        report_lines.append(f"  Blocked: {', '.join(POLICIES['license_check']['blocked'])}")
    
    if issues:
        report_lines.extend(["", "Issues found:"])
        report_lines.extend(issues)
    else:
        report_lines.append("✅ No known vulnerable dependencies detected")
    
    return [TextContent(type="text", text="\n".join(report_lines))]


async def check_code_complexity(args: Dict[str, Any]) -> List[TextContent]:
    """Analyze code complexity and enforce complexity limits."""
    code = args.get("code", "")
    filename = args.get("filename", "unknown.py")
    max_cyclomatic = args.get("max_cyclomatic", 15)
    
    lines = code.split("\n")
    violations = []
    
    # Simple cyclomatic complexity estimation
    # Count decision points (if, for, while, except, and, or, etc.)
    decision_keywords = ["if ", "for ", "while ", "except", "and ", "or "]
    
    current_function = None
    function_start = 0
    function_complexity = 0
    
    for i, line in enumerate(lines, 1):
        stripped = line.strip()
        
        # Detect function/method start
        if re.match(r'^def\s+\w+\s*\(', stripped):
            if current_function and function_complexity > max_cyclomatic:
                violations.append(Violation(
                    type=ViolationType.STYLE,
                    severity=Severity.MEDIUM,
                    message=f"Function '{current_function}' has cyclomatic complexity of {function_complexity} (max: {max_cyclomatic})",
                    line=function_start,
                    column=None,
                    file=filename,
                    fix="Refactor into smaller functions",
                    rule_id="complexity_exceeded",
                ))
            
            match = re.match(r'^def\s+(\w+)', stripped)
            current_function = match.group(1) if match else "unknown"
            function_start = i
            function_complexity = 1  # Base complexity
        
        # Count decision points
        if current_function:
            for keyword in decision_keywords:
                if keyword in stripped:
                    function_complexity += 1
    
    # Check last function
    if current_function and function_complexity > max_cyclomatic:
        violations.append(Violation(
            type=ViolationType.STYLE,
            severity=Severity.MEDIUM,
            message=f"Function '{current_function}' has cyclomatic complexity of {function_complexity} (max: {max_cyclomatic})",
            line=function_start,
            column=None,
            file=filename,
            fix="Refactor into smaller functions",
            rule_id="complexity_exceeded",
        ))
    
    # Check function length
    max_lines = POLICIES["max_complexity"]["max_lines_per_function"]
    if len(lines) > max_lines:
        violations.append(Violation(
            type=ViolationType.STYLE,
            severity=Severity.LOW,
            message=f"File has {len(lines)} lines (max recommended: {max_lines})",
            line=1,
            column=None,
            file=filename,
            fix="Split into multiple modules",
            rule_id="file_too_long",
        ))
    
    if violations:
        report = format_violation_report(violations)
        header = f"📊 COMPLEXITY ANALYSIS\n{'='*50}\n\n"
        return [TextContent(type="text", text=header + report)]
    else:
        return [TextContent(type="text", text=f"✅ Code complexity within defined limits (max: {max_cyclomatic})")]


async def check_license_compliance(args: Dict[str, Any]) -> List[TextContent]:
    """Check license compliance with project policies."""
    license_text = args.get("license_text", "")
    license_file_path = args.get("license_file_path")
    
    if license_file_path and os.path.exists(license_file_path):
        with open(license_file_path, "r") as f:
            license_text = f.read()
    
    if not license_text:
        return [TextContent(type="text", text="⚠️ No license text provided or file not found")]
    
    report_lines = ["📋 LICENSE COMPLIANCE CHECK", "=" * 50, ""]
    
    # Check for blocked licenses
    blocked = POLICIES["license_check"]["blocked"]
    allowed = POLICIES["license_check"]["allowed"]
    
    license_upper = license_text.upper()
    
    found_blocked = [lic for lic in blocked if lic.upper() in license_upper]
    found_allowed = [lic for lic in allowed if lic.replace("-", "").upper() in license_upper.replace("-", "").upper()]
    
    if found_blocked:
        report_lines.append(f"🔴 BLOCKED LICENSE DETECTED: {', '.join(found_blocked)}")
        report_lines.append("This license conflicts with project license policy.")
        report_lines.append("")
    
    if found_allowed:
        report_lines.append(f"✅ APPROVED LICENSE: {', '.join(found_allowed)}")
        report_lines.append("This license is approved for use.")
        report_lines.append("")
    
    if not found_blocked and not found_allowed:
        report_lines.append("🟡 UNKNOWN LICENSE TYPE")
        report_lines.append("Please review manually against project policy.")
        report_lines.append("")
    
    report_lines.append("License Policy:")
    report_lines.append(f"  ✅ Allowed: {', '.join(allowed)}")
    report_lines.append(f"  ❌ Blocked: {', '.join(blocked)}")
    
    return [TextContent(type="text", text="\n".join(report_lines))]


async def generate_compliance_report(args: Dict[str, Any]) -> List[TextContent]:
    """Generate comprehensive compliance report for auditing."""
    repo_path = args.get("repo_path", ".")
    report_format = args.get("report_format", "markdown")
    include_severity = args.get("include_severity", ["critical", "high", "medium"])
    
    # Map severity strings to enum
    severity_filter = []
    for s in include_severity:
        try:
            severity_filter.append(Severity(s.lower()))
        except ValueError:
            continue
    
    # Run repository scan
    scan_result = await scan_repository({
        "repo_path": repo_path,
        "file_extensions": [".py"],
        "include_secrets": True,
    })
    
    timestamp = "2025-03-28T15:00:00Z"  # In real impl, use datetime.utcnow().isoformat()
    
    if report_format == "json":
        report = {
            "report_type": "Guardrail Compliance Report",
            "timestamp": timestamp,
            "repository": repo_path,
            "scan_summary": scan_result[0].text if scan_result else "No results",
            "compliance_status": "REVIEW_REQUIRED" if "violation" in scan_result[0].text.lower() else "PASS",
        }
        return [TextContent(type="text", text=json.dumps(report, indent=2))]
    
    elif report_format == "sarif":
        # SARIF format for GitHub/CodeQL integration
        sarif = {
            "$schema": "https://raw.githubusercontent.com/oasis-tcs/sarif-spec/master/Schemata/sarif-schema-2.1.0.json",
            "version": "2.1.0",
            "runs": [{
                "tool": {
                    "driver": {
                        "name": "Guardrail MCP",
                        "version": "1.0.0"
                    }
                },
                "results": []
            }]
        }
        return [TextContent(type="text", text=json.dumps(sarif, indent=2))]
    
    else:  # markdown
        md_report = f"""# Guardrail Compliance Report

**Repository:** {repo_path}  
**Generated:** {timestamp}  
**Tool:** Guardrail MCP v1.0.0

## Executive Summary

{scan_result[0].text if scan_result else "No scan results available"}

## Compliance Statement

This report was generated automatically by the Guardrail MCP system.
For questions or exceptions, contact the M2Lab AI-Assisted SDLC team.

---
*Report generated for auditing purposes*
"""
        return [TextContent(type="text", text=md_report)]


async def block_commit(args: Dict[str, Any]) -> List[TextContent]:
    """Determine if a commit should be blocked based on violations."""
    files = args.get("files", [])
    block_on_severity = args.get("block_on_severity", "critical")
    
    severity_threshold = {
        "critical": [Severity.CRITICAL],
        "high": [Severity.CRITICAL, Severity.HIGH],
        "medium": [Severity.CRITICAL, Severity.HIGH, Severity.MEDIUM],
        "low": [Severity.CRITICAL, Severity.HIGH, Severity.MEDIUM, Severity.LOW],
    }.get(block_on_severity, [Severity.CRITICAL])
    
    all_violations = []
    
    for filepath in files:
        if not os.path.exists(filepath):
            continue
        
        try:
            with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                code = f.read()
            
            # Scan for issues
            for rule_name, rule in {**SECURITY_PATTERNS, **VULNERABLE_PATTERNS}.items():
                for match in re.finditer(rule["pattern"], code, re.MULTILINE):
                    start_pos = match.start()
                    line_num = code[:start_pos].count("\n") + 1
                    
                    violation = Violation(
                        type=ViolationType.SECURITY,
                        severity=rule["severity"],
                        message=rule["message"],
                        line=line_num,
                        column=None,
                        file=filepath,
                        fix=rule.get("fix"),
                        rule_id=rule_name,
                    )
                    all_violations.append(violation)
            
            # Check secrets
            for secret_type, pattern in SECRET_PATTERNS.items():
                for match in re.finditer(pattern["pattern"], code, re.MULTILINE):
                    start_pos = match.start()
                    line_num = code[:start_pos].count("\n") + 1
                    
                    violation = Violation(
                        type=ViolationType.SECRET,
                        severity=pattern["severity"],
                        message=pattern["message"],
                        line=line_num,
                        column=None,
                        file=filepath,
                        fix="Remove secret",
                        rule_id=secret_type,
                    )
                    all_violations.append(violation)
                    
        except Exception:
            continue
    
    # Check if any violations meet blocking threshold
    blocking_violations = [v for v in all_violations if v.severity in severity_threshold]
    
    if blocking_violations:
        report_lines = [
            "🚫 COMMIT BLOCKED",
            "=" * 50,
            "",
            f"Blocking threshold: {block_on_severity.upper()}+",
            f"Files checked: {len(files)}",
            f"Blocking violations: {len(blocking_violations)}",
            "",
            "Violations that block this commit:",
            "-" * 40,
            format_violation_report(blocking_violations),
            "",
            "To bypass (requires admin approval), run:",
            "  git commit --no-verify",
        ]
        return [TextContent(type="text", text="\n".join(report_lines))]
    else:
        non_blocking = [v for v in all_violations if v.severity not in severity_threshold]
        msg = f"✅ Commit approved. No {block_on_severity}+ violations found."
        if non_blocking:
            msg += f"\n⚠️ {len(non_blocking)} lower-severity issues detected (non-blocking)."
        return [TextContent(type="text", text=msg)]


async def check_human_in_the_loop(args: Dict[str, Any]) -> List[TextContent]:
    """Check if human approval is required for high-risk operations."""
    operation_type = args.get("operation_type", "")
    risk_level = args.get("risk_level", "medium")
    approvers = args.get("approvers", ["team_lead"])
    code_changes = args.get("code_changes", "")
    
    # Human-in-the-Loop Policy
    HITL_REQUIREMENTS = {
        "database_migration": {
            "min_risk": "medium",
            "required_approvers": ["dba", "team_lead"],
            "description": "Database schema changes can cause data loss or corruption",
        },
        "production_deploy": {
            "min_risk": "high",
            "required_approvers": ["team_lead", "security_champion"],
            "description": "Production deployments impact live systems and users",
        },
        "security_policy_change": {
            "min_risk": "medium",
            "required_approvers": ["security_champion", "compliance_officer"],
            "description": "Security policy changes affect overall security posture",
        },
        "privileged_access": {
            "min_risk": "high",
            "required_approvers": ["security_champion", "manager"],
            "description": "Privileged access grants elevated permissions that could be abused",
        },
        "data_export": {
            "min_risk": "medium",
            "required_approvers": ["data_owner", "compliance_officer"],
            "description": "Data exports may contain sensitive or regulated information",
        },
    }
    
    risk_order = {"low": 1, "medium": 2, "high": 3, "critical": 4}
    
    report_lines = [
        "👤 HUMAN-IN-THE-LOOP CHECK",
        "=" * 50,
        "",
        f"Operation Type: {operation_type}",
        f"Risk Level: {risk_level.upper()}",
    ]
    
    if code_changes:
        report_lines.append(f"Code Changes: {code_changes}")
    
    report_lines.append("")
    
    # Check if operation requires HITL
    policy = HITL_REQUIREMENTS.get(operation_type)
    
    if not policy:
        report_lines.extend([
            "🟡 UNKNOWN OPERATION TYPE",
            "Please consult the policy manual for approval requirements.",
        ])
        return [TextContent(type="text", text="\n".join(report_lines))]
    
    # Check risk level threshold
    current_risk = risk_order.get(risk_level, 0)
    min_risk = risk_order.get(policy["min_risk"], 0)
    
    if current_risk >= min_risk:
        report_lines.extend([
            "🔴 HUMAN APPROVAL REQUIRED",
            "",
            f"This operation requires explicit human approval because:",
            f"  • Risk level ({risk_level}) meets or exceeds threshold ({policy['min_risk']})",
            f"  • Operation type: {policy['description']}",
            "",
            "Required Approvers:",
        ])
        
        for approver in policy["required_approvers"]:
            report_lines.append(f"  ✅ {approver.replace('_', ' ').title()}")
        
        report_lines.extend([
            "",
            "Action Required:",
            "  1. Document the business justification",
            "  2. Obtain approval from all required approvers",
            "  3. Log approval in compliance system",
            "  4. Proceed only after all approvals received",
            "",
            "⚠️  Proceeding without approval violates security policy",
        ])
        
        return [TextContent(type="text", text="\n".join(report_lines))]
    else:
        report_lines.extend([
            "✅ AUTOMATED APPROVAL GRANTED",
            "",
            f"Risk level ({risk_level}) is below threshold ({policy['min_risk']}).",
            "Standard automated checks are sufficient.",
            "",
            "Still recommended:",
            "  • Review changes in staging environment",
            "  • Monitor deployment metrics",
            "  • Have rollback plan ready",
        ])
        
        return [TextContent(type="text", text="\n".join(report_lines))]


async def check_security_by_design(args: Dict[str, Any]) -> List[TextContent]:
    """Validate security-by-design principles are followed."""
    code = args.get("code", "")
    filename = args.get("filename", "unknown.py")
    check_principles = args.get("check_principles", [
        "least_privilege", "defense_in_depth", "secure_defaults", "fail_securely"
    ])
    
    # Security by Design patterns
    SBD_PATTERNS = {
        "least_privilege": {
            "patterns": [
                (r'(?i)admin\s*=\s*True|is_admin\s*=\s*True', "Admin privileges assigned by default"),
                (r'(?i)root|sudo|admin.*password', "Hardcoded privileged credentials"),
                (r'(?i)chmod\s+777|chmod\s+a\+rwx', "Overly permissive file permissions"),
                (r'(?i)run_as_root|run_as_admin', "Running with elevated privileges unnecessarily"),
            ],
            "severity": Severity.HIGH,
            "fix": "Apply least privilege - grant minimum necessary permissions",
        },
        "defense_in_depth": {
            "patterns": [
                (r'(?i)if\s+authenticated.*:', "Single layer of authentication check"),
                (r'(?i)only.*check.*password|just.*verify', "Insufficient validation layers"),
                (r'(?i)bypass.*check|skip.*validation', "Intentionally bypassing security checks"),
            ],
            "severity": Severity.MEDIUM,
            "fix": "Implement multiple independent security controls (input validation + authentication + authorization)",
        },
        "secure_defaults": {
            "patterns": [
                (r'(?i)default.*password\s*=\s*["\'][^"\']+["\']', "Default password configured"),
                (r'(?i)auth.*=\s*False|authentication\s*=\s*False', "Authentication disabled by default"),
                (r'(?i)encryption\s*=\s*False|encrypt\s*=\s*False', "Encryption disabled by default"),
                (r'(?i)timeout\s*=\s*(None|0|99999)', "Excessive or no timeout configured"),
            ],
            "severity": Severity.HIGH,
            "fix": "Enable security features by default, require explicit opt-out",
        },
        "fail_securely": {
            "patterns": [
                (r'except.*:\s*\n\s*return\s+True|except.*:\s*\n\s*return\s+1', "Exception returns success/false positive"),
                (r'(?i)catch.*exception.*allow|catch.*error.*permit', "Errors allow operation to proceed"),
                (r'(?i)finally.*grant|finally.*allow', "Finally block grants access regardless of error"),
                (r'(?i)on_error.*open|on_error.*grant', "Error handling opens security hole"),
            ],
            "severity": Severity.CRITICAL,
            "fix": "Default to denial - fail closed, not open",
        },
        "input_validation": {
            "patterns": [
                (r'(?i)request\.(?:GET|POST|args|form)\[[^\]]+\]', "Direct user input access without validation"),
                (r'(?i)input\s*\([^)]*\)\s*(?:\+|%)', "Unvalidated input in string operations"),
                (r'(?i)user.*input.*directly|direct.*user.*input', "User input used without sanitization"),
            ],
            "severity": Severity.CRITICAL,
            "fix": "Validate all input at system boundaries - whitelist over blacklist",
        },
        "separation_of_concerns": {
            "patterns": [
                (r'(?i)class.*User.*def.*admin|class.*Admin.*def.*user', "Mixing user and admin logic"),
                (r'(?i)auth.*AND.*business|security.*AND.*logic', "Security logic mixed with business logic"),
            ],
            "severity": Severity.MEDIUM,
            "fix": "Separate security controls from business logic",
        },
    }
    
    violations = []
    principles_checked = []
    
    for principle in check_principles:
        if principle in SBD_PATTERNS:
            principles_checked.append(principle)
            config = SBD_PATTERNS[principle]
            
            for pattern, message in config["patterns"]:
                for match in re.finditer(pattern, code, re.MULTILINE):
                    start_pos = match.start()
                    line_num = code[:start_pos].count('\n') + 1
                    
                    violation = Violation(
                        type=ViolationType.POLICY,
                        severity=config["severity"],
                        message=f"[{principle.replace('_', ' ').title()}] {message}",
                        line=line_num,
                        column=None,
                        file=filename,
                        fix=config.get("fix"),
                        rule_id=f"sbd_{principle}",
                    )
                    violations.append(violation)
    
    # Build report
    report_lines = [
        "🏗️ SECURITY-BY-DESIGN CHECK",
        "=" * 50,
        "",
        f"File: {filename}",
        f"Principles Checked: {', '.join(principles_checked)}",
        "",
    ]
    
    if violations:
        report_lines.append(f"❌ SECURITY PRINCIPLES VIOLATED: {len(violations)}")
        report_lines.append("")
        
        # Group by principle
        by_principle = {}
        for v in violations:
            principle = v.rule_id.replace("sbd_", "")
            if principle not in by_principle:
                by_principle[principle] = []
            by_principle[principle].append(v)
        
        for principle, prin_violations in by_principle.items():
            report_lines.append(f"\n📌 {principle.replace('_', ' ').title()}")
            report_lines.append("-" * 40)
            
            for v in prin_violations:
                emoji = {"critical": "🔴", "high": "🟠", "medium": "🟡", "low": "🔵"}.get(
                    v.severity.value, "⚪"
                )
                report_lines.append(f"{emoji} Line {v.line}: {v.message}")
                if v.fix:
                    report_lines.append(f"   Fix: {v.fix}")
        
        report_lines.extend([
            "",
            "📚 Security-By-Design Principles:",
            "  • Least Privilege: Grant minimum necessary access",
            "  • Defense in Depth: Multiple independent controls",
            "  • Secure Defaults: Security enabled by default",
            "  • Fail Securely: Default to denial, fail closed",
            "  • Input Validation: Validate at system boundaries",
            "  • Separation of Concerns: Security separate from business logic",
        ])
    else:
        report_lines.extend([
            "✅ ALL SECURITY PRINCIPLES FOLLOWED",
            "",
            "The code demonstrates good security-by-design practices:",
        ])
        
        for principle in principles_checked:
            report_lines.append(f"  ✅ {principle.replace('_', ' ').title()}")
        return [TextContent(type="text", text="\n".join(report_lines))]


async def check_veracode_scan(args: Dict[str, Any]) -> List[TextContent]:
    """Check Veracode scanning status and provide setup guidance."""
    app_id = args.get("app_id", "")
    repo_path = args.get("repo_path", ".")
    check_ci_cd = args.get("check_ci_cd", True)
    api_id = args.get("api_id", "")
    api_key = args.get("api_key", "")
    action = args.get("action", "check_status")
    
    # Check for Veracode credentials in environment if not provided
    if not api_id:
        api_id = os.environ.get("VERACODE_API_ID", "")
    if not api_key:
        api_key = os.environ.get("VERACODE_API_KEY", "")
    
    has_credentials = bool(api_id and api_key)
    
    # Check for CI/CD configuration
    ci_cd_configs = {
        "github_actions": ".github/workflows/veracode.yml",
        "azure_devops": "azure-pipelines-veracode.yml",
        "gitlab_ci": ".gitlab-ci-veracode.yml",
        "jenkins": "Jenkinsfile-veracode",
    }
    
    detected_configs = []
    if check_ci_cd and os.path.exists(repo_path):
        for platform, config_file in ci_cd_configs.items():
            config_path = os.path.join(repo_path, config_file)
            if os.path.exists(config_path):
                detected_configs.append(platform)
    
    # Check for Veracode policy/scans directory
    veracode_dirs = [".veracode", "veracode-scans", "security/veracode"]
    has_veracode_setup = any(os.path.exists(os.path.join(repo_path, d)) for d in veracode_dirs)
    
    if action == "setup_guidance":
        return generate_veracode_setup_guidance(has_credentials, detected_configs, repo_path)
    elif action == "generate_workflow":
        return generate_veracode_workflow(repo_path)
    elif action == "remind_scan":
        return generate_veracode_reminder(has_credentials, detected_configs, has_veracode_setup)
    else:  # check_status - default
        return generate_veracode_status_report(has_credentials, detected_configs, has_veracode_setup, app_id, repo_path)


def generate_veracode_status_report(has_credentials, detected_configs, has_veracode_setup, app_id, repo_path):
    """Generate status report for Veracode integration."""
    report_lines = [
        "🔒 VERACODE SAST INTEGRATION STATUS",
        "=" * 60,
        "",
    ]
    
    if has_credentials:
        report_lines.extend([
            "✅ API Credentials: Configured",
            "   Veracode API ID and Key found",
        ])
    else:
        report_lines.extend([
            "❌ API Credentials: NOT FOUND",
            "",
            "To configure Veracode credentials:",
            "  1. Get API credentials from Veracode Platform",
            "  2. Set environment variables:",
            "     export VERACODE_API_ID='your-api-id'",
            "     export VERACODE_API_KEY='your-api-key'",
        ])
    
    report_lines.append("")
    
    if detected_configs:
        report_lines.extend([
            f"✅ CI/CD Integration: Configured ({', '.join(detected_configs)})",
        ])
    else:
        report_lines.extend([
            "❌ CI/CD Integration: NOT FOUND",
            "",
            "To add Veracode to your CI/CD pipeline:",
            "  • Run 'check_veracode_scan' with action='generate_workflow'",
        ])
    
    report_lines.append("")
    
    if has_veracode_setup:
        report_lines.append("✅ Local Veracode Setup: Detected")
    else:
        report_lines.append("🟡 Local Veracode Setup: Not detected (optional)")
    
    if app_id:
        report_lines.append(f"📱 Veracode Application ID: {app_id}")
    else:
        report_lines.append("🟡 Veracode Application ID: Not provided")
    
    report_lines.extend([
        "",
        "-" * 60,
        "",
    ])
    
    if has_credentials and detected_configs:
        report_lines.extend([
            "🎉 VERACODE IS FULLY CONFIGURED",
            "",
            "Scans will run automatically on code changes.",
        ])
    elif has_credentials:
        report_lines.extend([
            "⚠️  VERACODE PARTIALLY CONFIGURED",
            "",
            "You have API credentials but no CI/CD integration.",
            "Run 'check_veracode_scan' with action='generate_workflow'",
        ])
    else:
        report_lines.extend([
            "🔴 VERACODE NOT CONFIGURED",
            "",
            "Action needed:",
            "  1. Obtain Veracode API credentials",
            "  2. Set environment variables or CI/CD secrets",
            "  3. Add CI/CD pipeline integration",
        ])
    
    return [TextContent(type="text", text="\n".join(report_lines))]


def generate_veracode_setup_guidance(has_credentials, detected_configs, repo_path):
    """Generate detailed setup guidance for Veracode."""
    guidance = """# Veracode SAST Setup Guide

## Overview
Veracode is an approved commercial SAST tool.

## Step 1: Obtain Veracode Credentials

1. Log in to Veracode Platform
2. Navigate to: Settings → API Credentials
3. Generate new API credentials
4. **IMPORTANT**: Never commit credentials to code!

## Step 2: Configure Credentials

### Option A: Environment Variables (Local Development)
```bash
export VERACODE_API_ID='your-api-id-here'
export VERACODE_API_KEY='your-api-key-here'
```

### Option B: CI/CD Secrets (Recommended for Pipelines)

**GitHub Actions:**
Repository → Settings → Secrets → Actions
Add: VERACODE_API_ID, VERACODE_API_KEY

**Azure DevOps:**
Project Settings → Pipelines → Library
Add Variable Group: veracode-credentials

## Step 3: Create Veracode Application

1. In Veracode Platform: Applications → Create Application
2. Use your repository name
3. Select your business unit

## Step 4: Add CI/CD Pipeline Integration

Run: check_veracode_scan with action='generate_workflow'

## Policy Requirements

- All production applications MUST have Veracode scanning
- High/Critical vulnerabilities must be resolved before deployment
- Scan results must be reviewed by Security Champion

## Support

Contact the security team: security@example.com
"""
    return [TextContent(type="text", text=guidance)]


def generate_veracode_reminder(has_credentials, detected_configs, has_veracode_setup):
    """Generate a reminder about Veracode scanning requirements."""
    if has_credentials and detected_configs:
        return [TextContent(type="text", text="""✅ VERACODE SCANNING IS CONFIGURED

Your repository has Veracode SAST integration:
  • API credentials: ✅
  • CI/CD pipeline: ✅
  • Automatic scanning: ✅

Remember:
  • High/Critical findings must be resolved before deployment
  • Review scan results in Veracode Platform after each commit

No action needed - scans will run automatically!
""")]
    
    reminder = """🔔 VERACODE SCANNING REMINDER

⚠️  This repository requires Veracode SAST scanning per policy.

Security Policy Requirements:
  • All production code must pass Veracode scanning
  • High/Critical vulnerabilities must be fixed
  • Security Champion approval required for exceptions

🚨 Code cannot be deployed to production without Veracode scan.

Need help? Run: check_veracode_scan with action='setup_guidance'
"""
    return [TextContent(type="text", text=reminder)]


def generate_veracode_workflow(repo_path):
    """Generate CI/CD workflow files for Veracode integration."""
    
    github_workflow = '''name: Veracode Security Scan
on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  veracode-scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Package application
        run: zip -r veracode-scan-target.zip . -x '*.git*' -x 'node_modules/*'
      - name: Upload and Scan with Veracode
        uses: veracode/veracode-uploadandscan-action@0.2.6
        with:
          appname: '${{ github.event.repository.name }}'
          createprofile: true
          filepath: 'veracode-scan-target.zip'
          vid: '${{ secrets.VERACODE_API_ID }}'
          vkey: '${{ secrets.VERACODE_API_KEY }}'
'''

    azure_pipeline = '''trigger:
  branches:
    include: [main, develop]

stages:
  - stage: SecurityScan
    jobs:
      - job: VeracodeScan
        pool:
          vmImage: 'ubuntu-latest'
        steps:
          - task: ArchiveFiles@2
            inputs:
              rootFolderOrFile: '$(Build.SourcesDirectory)'
              archiveFile: '$(Build.ArtifactStagingDirectory)/veracode-scan.zip'
          - task: Veracode@3
            inputs:
              Connection: 'VeracodeServiceConnection'
              appname: '$(Build.Repository.Name)'
              filepath: '$(Build.ArtifactStagingDirectory)/veracode-scan.zip'
'''

    gitlab_ci = '''veracode-sast:
  stage: security-scan
  image: veracode/veracode-cli:latest
  script:
    - zip -r veracode-scan.zip . -x '*.git*' -x 'node_modules/*'
    - veracode upload --appid "$CI_PROJECT_NAME" --filepath veracode-scan.zip
  artifacts:
    paths: [veracode-scan.zip]
  only: [main, develop]
'''

    report_lines = [
        "🔧 VERACODE CI/CD WORKFLOW GENERATOR",
        "=" * 60,
        "",
        "## GitHub Actions",
        "File: .github/workflows/veracode.yml",
        "",
        "```yaml",
        github_workflow,
        "```",
        "",
        "## Azure DevOps",
        "File: azure-pipelines-veracode.yml",
        "",
        "```yaml",
        azure_pipeline,
        "```",
        "",
        "## GitLab CI",
        "File: .gitlab-ci-veracode.yml",
        "",
        "```yaml",
        gitlab_ci,
        "```",
        "",
        "## Next Steps",
        "1. Choose your CI/CD platform workflow above",
        "2. Create the workflow file in your repository",
        "3. Add Veracode API credentials to CI/CD secrets:",
        "   - VERACODE_API_ID",
        "   - VERACODE_API_KEY",
        "4. Create Veracode Application in the platform",
        "5. Commit and push the workflow file",
    ]
    
    return [TextContent(type="text", text="\n".join(report_lines))]


async def check_pii(args: Dict[str, Any]) -> List[TextContent]:
    """Detect PII in text. Supports category filtering."""
    text = args.get("text", "")
    filename = args.get("filename", "input")
    filter_categories = args.get("categories", [])

    findings = []

    for pii_type, cfg in PII_PATTERNS.items():
        # Apply category filter when specified
        if filter_categories and cfg.get("category", "") not in filter_categories:
            continue
        for match in re.finditer(cfg["pattern"], text, re.MULTILINE):
            start_pos = match.start()
            line_num = text[:start_pos].count("\n") + 1
            findings.append(Violation(
                type=ViolationType.POLICY,
                severity=cfg["severity"],
                message=cfg["message"],
                line=line_num,
                column=None,
                file=filename,
                fix=f"Remove or replace with {cfg['redact_with']} before sharing",
                rule_id=f"pii_{pii_type}",
            ))

    report_lines = [
        "🔍 PII DETECTION REPORT",
        "=" * 50,
        "",
        f"Source: {filename}",
        f"Patterns checked: {len(PII_PATTERNS)}",
        "",
    ]

    if findings:
        critical = [f for f in findings if f.severity == Severity.CRITICAL]
        high = [f for f in findings if f.severity == Severity.HIGH]
        medium = [f for f in findings if f.severity == Severity.MEDIUM]

        report_lines.extend([
            f"⚠️  PII DETECTED — {len(findings)} finding(s)",
            "",
        ])
        if critical:
            report_lines.append(f"  🔴 Critical (regulated): {len(critical)}")
        if high:
            report_lines.append(f"  🟠 High (sensitive PII): {len(high)}")
        if medium:
            report_lines.append(f"  🟡 Medium: {len(medium)}")

        report_lines.extend([
            "",
            "Findings:",
            "-" * 40,
            format_violation_report(findings),
            "",
            "Recommended actions:",
            "  1. Use 'redact_sensitive_data' to replace PII before sending to LLM",
            "  2. Store PII only in approved encrypted data stores",
            "  3. Apply data minimisation — only process what is strictly necessary",
            "  4. Log this incident in your data protection register if required by policy",
        ])
    else:
        report_lines.extend([
            "✅ No PII detected",
            "",
            "The text does not contain recognisable PII patterns.",
            "Note: This scan uses pattern matching and may not catch all PII.",
            "Always apply a human review for sensitive use cases.",
        ])

    return [TextContent(type="text", text="\n".join(report_lines))]


async def redact_sensitive_data(args: Dict[str, Any]) -> List[TextContent]:
    """Redact PII and secrets from text, returning safe version and redaction summary."""
    text = args.get("text", "")
    redact_pii = args.get("redact_pii", True)
    redact_secrets = args.get("redact_secrets", True)

    redacted = text
    redaction_log: List[Dict[str, Any]] = []

    if redact_pii:
        for pii_type, cfg in PII_PATTERNS.items():
            placeholder = cfg["redact_with"]
            new_text, count = re.subn(cfg["pattern"], placeholder, redacted, flags=re.MULTILINE)
            if count:
                redaction_log.append({
                    "type": pii_type,
                    "category": cfg.get("category", "PII"),
                    "count": count,
                    "replaced_with": placeholder,
                })
                redacted = new_text

    if redact_secrets:
        for secret_type, cfg in SECRET_PATTERNS.items():
            placeholder = f"[REDACTED-SECRET-{secret_type.upper()}]"
            new_text, count = re.subn(cfg["pattern"], placeholder, redacted, flags=re.MULTILINE)
            if count:
                redaction_log.append({
                    "type": secret_type,
                    "category": "SECRET",
                    "count": count,
                    "replaced_with": placeholder,
                })
                redacted = new_text

    report_lines = [
        "🛡️ DATA REDACTION REPORT",
        "=" * 50,
        "",
    ]

    if redaction_log:
        total_redactions = sum(r["count"] for r in redaction_log)
        report_lines.extend([
            f"✅ Redaction complete — {total_redactions} value(s) replaced across {len(redaction_log)} pattern(s)",
            "",
            "Redaction summary:",
        ])
        for entry in redaction_log:
            report_lines.append(
                f"  • {entry['type']} [{entry['category']}]: {entry['count']}x → {entry['replaced_with']}"
            )
        report_lines.extend([
            "",
            "─" * 50,
            "REDACTED TEXT:",
            "─" * 50,
            redacted,
        ])
    else:
        report_lines.extend([
            "ℹ️  No sensitive data found — text returned unchanged.",
            "",
            "─" * 50,
            "TEXT (unchanged):",
            "─" * 50,
            redacted,
        ])

    return [TextContent(type="text", text="\n".join(report_lines))]


# Entry point
if __name__ == "__main__":
    import asyncio
    from mcp.server.stdio import stdio_server
    
    async def main():
        async with stdio_server() as (read_stream, write_stream):
            await app.run(
                read_stream,
                write_stream,
                app.create_initialization_options(),
            )
    
    asyncio.run(main())
