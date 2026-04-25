"""
Example 4: Extended Security Patterns from OWASP Top 10 and Industry Best Practices

This example demonstrates the additional security patterns added based on research
of OWASP Top 10, Bandit security linter, Semgrep rules, and GitHub secret scanning.
"""

# Extended Secret Detection Examples
EXTENDED_SECRET_EXAMPLES = """
# Azure Storage Account Key
AZURE_STORAGE_CONNECTION = "DefaultEndpointsProtocol=https;AccountName=myaccount;AccountKey=abc123...;EndpointSuffix=core.windows.net"

# Google API Key
GOOGLE_MAPS_API_KEY = "AIzaSyDdI0hCZtE6vySjMm-WEfRq3CPzqKqqsHI"

# JWT Token (commonly hardcoded in examples)
AUTH_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.dozjgNryP4J3jVmNHl0w5N_XgL0n3a9wZ7R3G8mY"

# Basic Auth in code
auth_header = "Basic dXNlcjpwYXNzd29yZA=="

# Bearer token
headers = {"Authorization": "Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."}

# Docker registry auth
DOCKER_CONFIG = '{"auths": {"https://index.docker.io/v1/": {"auth": "dXNlcjpwYXNz"}}}'

# .netrc credentials
machine github.com login user password secret123
"""

# OWASP Top 10 Security Vulnerability Examples
OWASP_VULNERABILITY_EXAMPLES = """
# A01:2021 - Broken Access Control
# Flask debug mode (exposes Werkzeug debugger with PIN)
app.run(debug=True)

# Django debug mode
DEBUG = True

# Insecure CORS - allows any origin
CORS(app, origins="*")

# ALLOWED_HOSTS accepting all
ALLOWED_HOSTS = ['*']

# A02:2021 - Cryptographic Failures
# Weak ciphers
from Crypto.Cipher import DES
cipher = DES.new(key, DES.MODE_ECB)

# ECB mode (insecure)
from Crypto.Cipher import AES
cipher = AES.new(key, AES.MODE_ECB)

# Static Fernet key
from cryptography.fernet import Fernet
key = Fernet.generate_key()
cipher_suite = Fernet("hardcoded-key-here")

# A01:2021 - Path Traversal
# Unsafe file path construction
filename = request.GET.get('file')
with open(f"../{filename}") as f:  # Path traversal!
    data = f.read()

# User input in path construction
file_path = os.path.join(BASE_DIR, request.POST.get('filename'))

# A05:2021 - Security Misconfiguration / XXE
# Vulnerable XML parsing
import xml.etree.ElementTree as ET
tree = ET.parse(user_input_xml)  # XXE vulnerability

# A10:2021 - Server-Side Request Forgery (SSRF)
# Request to internal addresses
import requests
url = request.GET.get('url')
response = requests.get(url)  # Could be http://localhost:8080/admin

# A03:2021 - Injection / XSS
# mark_safe with user input (Django)
from django.utils.safestring import mark_safe
output = mark_safe(request.POST.get('content'))  # XSS!

# A03:2021 - Command Injection
# os.system with user input
import os
command = request.GET.get('cmd')
os.system(f"ls -la {command}")  # Command injection!

# subprocess with shell=True and user input
import subprocess
cmd = request.POST.get('command')
subprocess.run(cmd, shell=True)  # Dangerous!

# A08:2021 - Software and Data Integrity Failures
# Unsafe deserialization
import pickle
data = pickle.loads(user_input)  # Arbitrary code execution!

# Unsafe yaml.load
import yaml
config = yaml.load(user_input)  # Can execute code!

# Unsafe marshal
import marshal
data = marshal.loads(user_input_bytes)  # Arbitrary code execution!

# Security Misconfiguration
# Disabling SSL verification
import requests
response = requests.get(url, verify=False)  # MITM risk!

# Insecure protocols
ftp_url = "ftp://user:pass@server.com/file.txt"
telnet_url = "telnet://server.com:23"

# A09:2021 - Security Logging and Monitoring Failures
# Logging sensitive data
import logging
logger.info(f"User login with password: {password}")  # Credential leak!
logger.debug(f"Credit card: {user.credit_card_number}")  # PCI violation!

# Debug printing credentials
print(f"API Key: {api_key}")  # Secret exposure!
print(f"User password: {user.password}")  # Password leak!
"""

# Safe Alternatives
SAFE_ALTERNATIVES = """
# ✅ Safe Flask configuration
app.run(debug=os.environ.get('FLASK_DEBUG') == 'true')

# ✅ Safe CORS configuration
CORS(app, origins=["https://trusted-site.com", "https://app.example.com"])

# ✅ Safe ALLOWED_HOSTS
ALLOWED_HOSTS = ['myapp.example.com', 'api.example.com']

# ✅ Strong encryption
from Crypto.Cipher import AES
cipher = AES.new(key, AES.MODE_GCM)

# ✅ Safe file handling
import os
from pathlib import Path
base_path = Path("/safe/upload/directory")
requested_path = base_path / filename
if requested_path.resolve().parent != base_path.resolve():
    raise ValueError("Path traversal attempt detected")

# ✅ Safe XML parsing
from defusedxml import ElementTree as ET
tree = ET.parse(user_input_xml)  # XXE protected

# ✅ Safe URL requests (SSRF protection)
import requests
from urllib.parse import urlparse
blocked_hosts = ['localhost', '127.0.0.1', '0.0.0.0', '::1']
allowed_schemes = ['https']

url = request.GET.get('url')
parsed = urlparse(url)
if parsed.hostname in blocked_hosts:
    raise ValueError("Access to internal addresses not allowed")
if parsed.scheme not in allowed_schemes:
    raise ValueError("Only HTTPS allowed")

response = requests.get(url, verify=True, timeout=5)

# ✅ Safe HTML rendering (Django)
from django.template import Template, Context
template = Template("{{ content }}")
context = Context({'content': user_content})  # Auto-escaped
output = template.render(context)

# ✅ Safe command execution
import subprocess
# Use array instead of string, no shell
subprocess.run(['ls', '-la', directory], shell=False)

# ✅ Safe serialization
import json
data = json.loads(user_input)  # Safe deserialization

# ✅ Safe YAML parsing
import yaml
config = yaml.safe_load(user_input)  # Safe loader

# ✅ Safe logging (structured with redaction)
import logging
import copy

def redact_sensitive(data):
    redacted = copy.deepcopy(data)
    sensitive_fields = ['password', 'credit_card', 'ssn', 'api_key']
    for field in sensitive_fields:
        if field in redacted:
            redacted[field] = '***REDACTED***'
    return redacted

logger.info("User login", extra={'user': user_id})  # No sensitive data
"""

print("=" * 80)
print("EXAMPLE 4: Extended Security Patterns from OWASP Top 10")
print("=" * 80)
print("\nBased on research of:")
print("  • OWASP Top 10 2021")
print("  • Bandit Python Security Linter")
print("  • Semgrep Security Rules")
print("  • GitHub Secret Scanning Patterns")
print("\n" + "=" * 80)

print("\nNEW SECRET PATTERNS ADDED:")
print("-" * 40)
print("• Azure Storage Account Keys")
print("• Google API Keys (AIza...)")
print("• JWT Tokens (eyJ...)")
print("• Basic Authentication (Basic ...)")
print("• Bearer Tokens (Bearer ...)")
print("• Docker Registry Auth")
print("• .netrc Credentials")

print("\n" + "=" * 80)
print("\nNEW SECURITY VULNERABILITY PATTERNS:")
print("-" * 40)
print("\n[OWASP A01:2021] Broken Access Control:")
print("  • Flask/Django debug mode")
print("  • Insecure CORS (origins='*')")
print("  • ALLOWED_HOSTS = ['*']")
print("  • Path traversal (../ in file paths)")

print("\n[OWASP A02:2021] Cryptographic Failures:")
print("  • Weak ciphers (DES, 3DES, RC4, RC2)")
print("  • ECB encryption mode")
print("  • Static Fernet keys")

print("\n[OWASP A03:2021] Injection:")
print("  • Command injection (os.system, subprocess.shell=True)")
print("  • XSS via mark_safe with user input")

print("\n[OWASP A05:2021] Security Misconfiguration / XXE:")
print("  • xml.etree.ElementTree.parse (XXE vulnerable)")
print("  • lxml.etree.parse without protection")

print("\n[OWASP A08:2021] Software Integrity:")
print("  • pickle.load/pickle.loads (arbitrary code)")
print("  • yaml.load without SafeLoader")
print("  • marshal.load/marshal.loads")

print("\n[OWASP A09:2021] Logging Failures:")
print("  • Credentials in print statements")
print("  • Sensitive data in logs")

print("\n[OWASP A10:2021] SSRF:")
print("  • requests to internal IPs (localhost, 127.0.0.1)")
print("  • urllib requests to internal addresses")

print("\n[Additional] Security Misconfiguration:")
print("  • SSL verify=False")
print("  • Insecure protocols (ftp://, telnet://)")

print("\n" + "=" * 80)
print("\nThese patterns are now integrated into the guardrail_server.py")
print("and will be detected by the scan_code, check_secrets, and")
print("validate_ai_output tools.")
print("=" * 80)
