"""
Example 2: Secret Detection Guardrail

This example shows how a guardrail MCP can detect secrets and
credentials accidentally committed to code.
"""

# Example code with various secrets:
CODE_WITH_SECRETS = """
# AWS Configuration
aws_access_key_id = "AKIAIOSFODNN7EXAMPLE"
aws_secret_access_key = "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"

# GitHub Token
GITHUB_TOKEN = "ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"

# Slack Token
slack_token = "xoxb-EXAMPLE-SLACK-BOT-TOKEN-REPLACE-ME"

# Database connection
DATABASE_URL = "postgresql://user:password123@localhost:5432/mydb"

# Private key (PEM format)
private_key = '''-----BEGIN RSA PRIVATE KEY-----
MIIEpAIBAAKCAQEAxgNSPM+TDyx1Yw4BxhfLb0w+QoXn8...
-----END RSA PRIVATE KEY-----'''

# API key
API_KEY = "sk_live_51Hx9...xyz789"

# Function using secrets
def connect_to_services():
    s3 = boto3.client(
        's3',
        aws_access_key_id=aws_access_key_id,
        aws_secret_access_key=aws_secret_access_key
    )
    
    headers = {"Authorization": f"Bearer {GITHUB_TOKEN}"}
    response = requests.get("https://api.github.com/user", headers=headers)
    
    return s3, response
"""

# What guardrail detects:
DETECTION_RESULTS = """
🔴 [CRITICAL] SECRET
   Type: aws_access_key
   Pattern: AKIA[0-9A-Z]{16}
   File: config.py:3
   Issue: AWS Access Key ID detected
   Fix: Move to ~/.aws/credentials or use IAM roles

🔴 [CRITICAL] SECRET
   Type: aws_secret_key
   File: config.py:4
   Issue: AWS Secret Access Key detected
   Fix: Never commit secret keys - use AWS credential chain

🔴 [CRITICAL] SECRET
   Type: github_token
   Pattern: ghp_[a-zA-Z0-9]{36}
   File: config.py:7
   Issue: GitHub Personal Access Token detected
   Fix: Use GitHub CLI or environment variable: export GITHUB_TOKEN=...

🔴 [CRITICAL] SECRET
   Type: slack_token
   Pattern: xox[baprs]-...
   File: config.py:10
   Issue: Slack token detected
   Fix: Use Slack SDK with environment variables

🟠 [HIGH] SECRET
   Type: database_password
   File: config.py:13
   Issue: Database password in connection string
   Fix: Use DATABASE_URL from environment or secret manager

🔴 [CRITICAL] SECRET
   Type: private_key
   Pattern: -----BEGIN.*PRIVATE KEY-----
   File: config.py:16
   Issue: Private key detected
   Fix: Store in secure vault (AWS Secrets Manager, Azure Key Vault, etc.)

🔴 [CRITICAL] SECRET
   Type: api_key
   File: config.py:21
   Issue: API key detected
   Fix: Use environment variable: os.environ.get('API_KEY')
"""

# Safe alternative using environment variables:
SAFE_CODE = """
import os

# SECURE: Load from environment
aws_access_key_id = os.environ.get('AWS_ACCESS_KEY_ID')
aws_secret_access_key = os.environ.get('AWS_SECRET_ACCESS_KEY')

# SECURE: GitHub token from env
GITHUB_TOKEN = os.environ.get('GITHUB_TOKEN')

# SECURE: Slack token from env
slack_token = os.environ.get('SLACK_BOT_TOKEN')

# SECURE: Database URL from env
DATABASE_URL = os.environ.get('DATABASE_URL')

# SECURE: Private key from file (not committed)
private_key_path = os.environ.get('PRIVATE_KEY_PATH', '/secure/keys/private.pem')
with open(private_key_path, 'r') as f:
    private_key = f.read()

# SECURE: API key from env
API_KEY = os.environ.get('API_KEY')

# Function using secrets safely
def connect_to_services():
    # AWS - uses credential chain, no hardcoded values
    s3 = boto3.client('s3')
    
    # GitHub
    headers = {"Authorization": f"Bearer {GITHUB_TOKEN}"}
    response = requests.get("https://api.github.com/user", headers=headers)
    
    return s3, response


# .env file (add to .gitignore!)
# AWS_ACCESS_KEY_ID=your_key_here
# AWS_SECRET_ACCESS_KEY=your_secret_here
# GITHUB_TOKEN=your_token_here
# SLACK_BOT_TOKEN=your_token_here
# DATABASE_URL=postgresql://user:pass@host/db
# API_KEY=your_api_key_here
"""

print("=" * 70)
print("EXAMPLE 2: Secret Detection Guardrail")
print("=" * 70)
print("\nThis example shows how guardrails prevent secret leaks:\n")
print("VULNERABLE CODE (with secrets):")
print("-" * 40)
print(CODE_WITH_SECRETS)
print("\n" + "=" * 70)
print("GUARDRAIL DETECTION:")
print("-" * 40)
print(DETECTION_RESULTS)
print("\n" + "=" * 70)
print("SAFE ALTERNATIVE (using environment variables):")
print("-" * 40)
print(SAFE_CODE)
print("\n" + "=" * 70)
print("\nAdditional Recommendations:")
print("• Use .env files for local development (add to .gitignore!)")
print("• Use secret managers in production (AWS Secrets Manager, Vault, etc.)")
print("• Rotate secrets immediately if accidentally committed")
print("• Use pre-commit hooks to block secrets before they reach git")
print("=" * 70)
