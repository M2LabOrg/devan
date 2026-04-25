"""
Example 1: Code Scanner Guardrail

This example shows how a guardrail MCP can detect security issues
in Python code before it's committed or used.
"""

# Example vulnerable code that would be caught:
VULNERABLE_CODE_EXAMPLE = """
import random
import os

# CRITICAL: Hardcoded password
DB_PASSWORD = "SuperSecret123!"

# CRITICAL: SQL Injection vulnerability
def get_user(user_id):
    query = f"SELECT * FROM users WHERE id = {user_id}"
    return db.execute(query)

# HIGH: Dangerous eval() usage
def process_user_input(data):
    return eval(data)

# MEDIUM: Debug mode enabled
DEBUG = True

# MEDIUM: Insecure random for crypto
def generate_token():
    return random.randint(100000, 999999)
"""

# Example of how the guardrail would respond:
EXPECTED_GUARDRAIL_RESPONSE = """
🔴 [CRITICAL] SECURITY
   Rule: hardcoded_password
   File: example.py:4
   Issue: Hardcoded password detected
   Fix: Store in environment variable: os.environ.get('DB_PASSWORD')

🔴 [CRITICAL] SECURITY
   Rule: sql_injection
   File: example.py:8
   Issue: Potential SQL injection vulnerability
   Fix: Use parameterized queries: cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))

🟠 [HIGH] SECURITY
   Rule: eval_usage
   File: example.py:13
   Issue: Dangerous eval() usage detected
   Fix: Use ast.literal_eval() for safe evaluation or json.loads() for JSON

🟠 [HIGH] SECURITY
   Rule: debug_mode
   File: example.py:17
   Issue: Debug mode enabled - security risk in production
   Fix: Set debug=False in production environments

🟡 [MEDIUM] SECURITY
   Rule: insecure_random
   File: example.py:2, 20
   Issue: Insecure random number generator for cryptographic use
   Fix: Use secrets module: import secrets; secrets.token_hex(16)
"""

# Safe version of the code:
SAFE_CODE_EXAMPLE = """
import os
import secrets

# SECURE: Password from environment
DB_PASSWORD = os.environ.get('DB_PASSWORD')
if not DB_PASSWORD:
    raise ValueError("DB_PASSWORD environment variable not set")

# SECURE: Parameterized query
def get_user(user_id):
    query = "SELECT * FROM users WHERE id = ?"
    return db.execute(query, (user_id,))

# SECURE: Safe data processing
def process_user_input(data):
    import json
    return json.loads(data)

# SECURE: Debug disabled in production
DEBUG = os.environ.get('DEBUG', 'false').lower() == 'true'

# SECURE: Cryptographically secure token
def generate_token():
    return secrets.token_hex(16)
"""

print("=" * 70)
print("EXAMPLE 1: Code Scanner Guardrail")
print("=" * 70)
print("\nThis example demonstrates how guardrails catch security issues:\n")
print("VULNERABLE CODE:")
print("-" * 40)
print(VULNERABLE_CODE_EXAMPLE)
print("\n" + "=" * 70)
print("GUARDRAIL DETECTION:")
print("-" * 40)
print(EXPECTED_GUARDRAIL_RESPONSE)
print("\n" + "=" * 70)
print("SAFE ALTERNATIVE:")
print("-" * 40)
print(SAFE_CODE_EXAMPLE)
print("\n" + "=" * 70)
