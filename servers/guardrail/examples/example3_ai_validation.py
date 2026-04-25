"""
Example 3: AI Output Validation Guardrail

This example shows how guardrails validate AI-generated code
before it's accepted, catching hallucinations and unsafe patterns.
"""

# Example AI-generated code with issues:
AI_GENERATED_CODE = """
# AI-generated authentication module
# Note: Some imports may need verification

import hashlib
import crypto_utils  # Potentially hallucinated module
from secure_hash import advanced_hash  # Potentially hallucinated module

def authenticate_user(username, password):
    # Check against database
    query = f"SELECT * FROM users WHERE username = '{username}' AND password = '{password}'"
    user = db.execute(query)
    
    if user:
        # Generate session token
        token = hashlib.md5(password.encode()).hexdigest()
        return {"success": True, "token": token}
    
    return {"success": False}

def hash_password(password):
    # Using SHA1 for password hashing
    return hashlib.sha1(password.encode()).hexdigest()

def send_reset_email(email):
    # TODO: Implement email sending
    pass

def process_payment(card_number, cvv, expiry):
    # Validate card
    if len(card_number) == 16:
        API_KEY = "pk_live_1234567890abcdef"
        result = payment_gateway.charge(API_KEY, card_number, cvv, expiry)
        return result
    return None

class AuthHelper:
    # FIXME: This class needs review
    pass
"""

# Guardrail validation results:
VALIDATION_REPORT = """
🛡️ AI OUTPUT VALIDATION REPORT
==================================================

🔴 CRITICAL (1): Must fix before accepting
🟠 HIGH (2): Should fix
🟡 MEDIUM (1): Consider fixing

🔴 [CRITICAL] SECURITY
   Rule: sql_injection
   File: auth.py:9
   Issue: Potential SQL injection vulnerability
   Fix: Use parameterized queries

🔴 [CRITICAL] SECURITY
   Rule: md5_hashing
   File: auth.py:14
   Issue: MD5 is cryptographically broken and unsuitable for password hashing
   Fix: Use bcrypt, argon2, or scrypt for password hashing

🔴 [CRITICAL] SECRET
   Type: api_key
   File: auth.py:24
   Issue: Hardcoded payment API key detected
   Fix: Move to environment variable

🟠 [HIGH] SECURITY
   Rule: sha1_hashing
   File: auth.py:18
   Issue: SHA-1 is deprecated for security use
   Fix: Use SHA-256 or stronger for non-password hashing

⚠️ WARNINGS:
  • Potentially hallucinated import: 'crypto_utils' - verify this module exists
  • Potentially hallucinated import: 'secure_hash' - verify this module exists
  • Code contains TODO/FIXME comments - review for completeness
  • Plaintext password comparison detected - use proper password verification

RECOMMENDATION: ⚠️ Do not accept this code without fixes

ACCEPT / MODIFY / REJECT ?
"""

# Improved version after guardrail feedback:
IMPROVED_CODE = """
# Safe authentication module
# Reviewed and fixed based on guardrail feedback

import bcrypt
import re
from typing import Optional, Dict
import os

# Load API key from environment
PAYMENT_API_KEY = os.environ.get('PAYMENT_API_KEY')
if not PAYMENT_API_KEY:
    raise ValueError("PAYMENT_API_KEY environment variable not set")

def authenticate_user(username: str, password: str, db) -> Dict:
    # SECURE: Parameterized query prevents SQL injection
    query = "SELECT id, password_hash FROM users WHERE username = ?"
    user = db.execute(query, (username,)).fetchone()
    
    if user and bcrypt.checkpw(password.encode(), user['password_hash']):
        # SECURE: Use cryptographically secure token generation
        import secrets
        token = secrets.token_urlsafe(32)
        return {"success": True, "token": token}
    
    return {"success": False}

def hash_password(password: str) -> str:
    # SECURE: Use bcrypt for password hashing
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(password.encode(), salt)

def validate_card_number(card_number: str) -> bool:
    # Basic Luhn algorithm validation
    if not re.match(r'^\\d{16}$', card_number):
        return False
    
    digits = [int(d) for d in card_number]
    odd_sum = sum(digits[-1::-2])
    even_sum = sum([sum(divmod(2 * d, 10)) for d in digits[-2::-2]])
    return (odd_sum + even_sum) % 10 == 0

def process_payment(card_number: str, amount_cents: int) -> Dict:
    # SECURE: Validate card before processing
    if not validate_card_number(card_number):
        return {"success": False, "error": "Invalid card number"}
    
    # SECURE: API key from environment, not hardcoded
    result = payment_gateway.charge(
        api_key=PAYMENT_API_KEY,
        card_number=card_number,
        amount_cents=amount_cents
    )
    return result
"""

print("=" * 70)
print("EXAMPLE 3: AI Output Validation Guardrail")
print("=" * 70)
print("\nThis example shows how guardrails validate AI-generated code:\n")
print("AI-GENERATED CODE (with issues):")
print("-" * 40)
print(AI_GENERATED_CODE)
print("\n" + "=" * 70)
print("GUARDRAIL VALIDATION:")
print("-" * 40)
print(VALIDATION_REPORT)
print("\n" + "=" * 70)
print("IMPROVED CODE (after guardrail fixes):")
print("-" * 40)
print(IMPROVED_CODE)
print("\n" + "=" * 70)
print("\nKey Guardrail Benefits:")
print("• Catches AI hallucinations (non-existent imports)")
print("• Prevents acceptance of vulnerable code")
print("• Provides specific fixes for each issue")
print("• Blocks secrets that AI might include in examples")
print("• Enforces project coding standards")
print("=" * 70)
