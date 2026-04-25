# CI/CD Integration Guide - Guardrail MCP

This guide explains how to integrate Guardrail MCPs with CI/CD pipelines using DevOps platforms like GitHub Actions, Azure DevOps, GitLab CI, and Jenkins.

---

## Overview

**Purpose**: Enforce guardrails at every stage of the deployment pipeline  
**When**: On every PR, merge, and deployment  
**Blocks**: Code with critical violations from reaching production  

---

## Three Lines of Defense in CI/CD

```
┌─────────────────────────────────────────────────────────────────────┐
│                     CI/CD PIPELINE                                  │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  1. PRE-COMMIT    →  2. PR CHECKS    →  3. PRE-DEPLOY              │
│  (Developer)         (CI Pipeline)       (Staging/Prod)              │
│                                                                     │
│  • Block commits    • PR comments    • Final approval               │
│  • Fast scan        • Full scan      • Compliance report            │
│  • Local feedback   • Block merge    • Audit trail                  │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## GitHub Actions Integration

### Option 1: GitHub Actions Workflow

Create `.github/workflows/guardrails.yml`:

```yaml
name: M2Lab Guardrails

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main, develop]

jobs:
  guardrail-scan:
    name: Guardrail Security Scan
    runs-on: ubuntu-latest
    
    steps:
      - name: Checkout code
        uses: actions/checkout@v4
        with:
          fetch-depth: 0  # Full history for better scanning

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install MCP SDK
        run: pip install mcp

      - name: Run Guardrail Repository Scan
        id: scan
        run: |
          python << 'EOF'
          import asyncio
          import sys
          import json
          sys.path.insert(0, 'guardrail_mcp/mcp_project')
          from guardrail_server import scan_repository
          
          async def main():
              result = await scan_repository({
                  "repo_path": ".",
                  "file_extensions": [".py", ".js", ".ts"],
                  "include_secrets": True
              })
              print(result[0].text)
              
              # Exit with error if critical issues found
              if "🔴 Critical" in result[0].text:
                  sys.exit(1)
          
          asyncio.run(main())
          EOF
        continue-on-error: false

      - name: Check Dependencies
        run: |
          python << 'EOF'
          import asyncio
          import sys
          sys.path.insert(0, 'guardrail_mcp/mcp_project')
          from guardrail_server import check_dependencies
          
          async def main():
              result = await check_dependencies({
                  "requirements_file": "requirements.txt" if __import__('os').path.exists("requirements.txt") else None,
                  "package_json": "package.json" if __import__('os').path.exists("package.json") else None,
                  "check_licenses": True
              })
              print(result[0].text)
          
          asyncio.run(main())
          EOF

      - name: Generate Compliance Report
        if: always()
        run: |
          python << 'EOF'
          import asyncio
          import sys
          sys.path.insert(0, 'guardrail_mcp/mcp_project')
          from guardrail_server import generate_compliance_report
          
          async def main():
              result = await generate_compliance_report({
                  "repo_path": ".",
                  "report_format": "sarif",
                  "include_severity": ["critical", "high", "medium"]
              })
              
              # Save SARIF report for GitHub Advanced Security
              with open("guardrail-results.sarif", "w") as f:
                  f.write(result[0].text)
          
          asyncio.run(main())
          EOF

      - name: Upload SARIF to GitHub Security Tab
        if: always()
        uses: github/codeql-action/upload-sarif@v3
        with:
          sarif_file: guardrail-results.sarif
          category: guardrail-mcp

      - name: Comment PR with Results
        if: github.event_name == 'pull_request' && failure()
        uses: actions/github-script@v7
        with:
          script: |
            github.rest.issues.createComment({
              issue_number: context.issue.number,
              owner: context.repo.owner,
              repo: context.repo.repo,
              body: '🚫 **Guardrail Check Failed**\n\nThis PR contains security violations or policy breaches. Please review the scan results in the Actions tab.'
            })
```

### Option 2: Reusable Workflow (org standard)

Create `.github/workflows/guardrails-reusable.yml`:

```yaml
name: M2Lab Guardrails Reusable

on:
  workflow_call:
    inputs:
      severity-threshold:
        description: 'Minimum severity to block (critical/high/medium/low)'
        default: 'critical'
        type: string
      scan-path:
        description: 'Path to scan'
        default: '.'
        type: string
      file-extensions:
        description: 'File extensions to scan'
        default: '[".py", ".js", ".ts", ".java"]'
        type: string

jobs:
  guardrail-check:
    name: Guardrail Check
    runs-on: ubuntu-latest
    
    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: pip install mcp

      - name: Run Guardrail Block Commit Check
        run: |
          python << EOF
          import asyncio
          import sys
          import os
          import subprocess
          
          # Get list of changed files
          result = subprocess.run(
              ["git", "diff", "--name-only", "origin/main...HEAD"],
              capture_output=True, text=True
          )
          changed_files = [f.strip() for f in result.stdout.split('\n') if f.strip()]
          
          sys.path.insert(0, 'guardrail_mcp/mcp_project')
          from guardrail_server import block_commit
          
          async def main():
              result = await block_commit({
                  "files": changed_files,
                  "block_on_severity": "${{ inputs.severity-threshold }}"
              })
              print(result[0].text)
              
              if "🚫 COMMIT BLOCKED" in result[0].text:
                  sys.exit(1)
          
          asyncio.run(main())
          EOF
```

Then in each repo, create `.github/workflows/ci.yml`:

```yaml
name: CI

on:
  pull_request:
    branches: [main]

jobs:
  guardrails:
    uses: m2lab-org/github-workflows/.github/workflows/guardrails-reusable.yml@main
    with:
      severity-threshold: 'high'
      scan-path: '.'
```

---

## Azure DevOps Integration

### Azure Pipelines YAML

Create `azure-pipelines.yml`:

```yaml
trigger:
  branches:
    include:
      - main
      - develop

pr:
  branches:
    include:
      - main
      - develop

stages:
  - stage: GuardrailCheck
    displayName: '🔒 Guardrail Security Check'
    jobs:
      - job: SecurityScan
        displayName: 'Security Scan'
        pool:
          vmImage: 'ubuntu-latest'
        
        steps:
          - task: UsePythonVersion@0
            inputs:
              versionSpec: '3.11'
            displayName: 'Use Python 3.11'

          - script: |
              pip install mcp
            displayName: 'Install MCP SDK'

          - script: |
              python << 'EOF'
              import asyncio
              import sys
              sys.path.insert(0, 'guardrail_mcp/mcp_project')
              from guardrail_server import scan_repository, generate_compliance_report
              
              async def main():
                  # Run scan
                  scan_result = await scan_repository({
                      "repo_path": "$(Build.SourcesDirectory)",
                      "file_extensions": [".py", ".js"],
                      "include_secrets": True
                  })
                  print(scan_result[0].text)
                  
                  # Generate report
                  report = await generate_compliance_report({
                      "repo_path": "$(Build.SourcesDirectory)",
                      "report_format": "json"
                  })
                  
                  # Save for later stages
                  with open("$(Build.ArtifactStagingDirectory)/guardrail-report.json", "w") as f:
                      f.write(report[0].text)
                  
                  # Fail if critical issues
                  if "🔴 Critical" in scan_result[0].text:
                      sys.exit(1)
              
              asyncio.run(main())
              EOF
            displayName: 'Run Guardrail Scan'
            failOnStderr: true

          - task: PublishBuildArtifacts@1
            inputs:
              pathToPublish: '$(Build.ArtifactStagingDirectory)/guardrail-report.json'
              artifactName: 'guardrail-report'
            displayName: 'Publish Guardrail Report'
            condition: always()

          - task: AzureDevOpsGuardrails@0  # Custom extension (hypothetical)
            inputs:
              reportPath: '$(Build.ArtifactStagingDirectory)/guardrail-report.json'
              blockOnSeverity: 'critical'
            displayName: 'Enforce Guardrails'
```

---

## GitLab CI Integration

### `.gitlab-ci.yml`

```yaml
stages:
  - guardrails
  - test
  - deploy

guardrail_scan:
  stage: guardrails
  image: python:3.11
  script:
    - pip install mcp
    - |
      python << 'EOF'
      import asyncio
      import sys
      import json
      sys.path.insert(0, 'guardrail_mcp/mcp_project')
      from guardrail_server import scan_repository, block_commit
      
      async def main():
          # Get changed files
          import subprocess
          result = subprocess.run(
              ["git", "diff", "--name-only", "HEAD~1", "HEAD"],
              capture_output=True, text=True
          )
          changed_files = result.stdout.strip().split('\n')
          
          # Block commit check
          block_result = await block_commit({
              "files": changed_files,
              "block_on_severity": "critical"
          })
          print(block_result[0].text)
          
          if "🚫 COMMIT BLOCKED" in block_result[0].text:
              sys.exit(1)
          
          # Full repository scan
          scan_result = await scan_repository({
              "repo_path": ".",
              "file_extensions": [".py"],
              "include_secrets": True
          })
          print(scan_result[0].text)
      
      asyncio.run(main())
      EOF
  artifacts:
    reports:
      sast: guardrail-results.json
    paths:
      - guardrail-results.json
    expire_in: 1 week
  allow_failure: false
  rules:
    - if: $CI_PIPELINE_SOURCE == "merge_request_event"
    - if: $CI_COMMIT_BRANCH == $CI_DEFAULT_BRANCH

generate_report:
  stage: guardrails
  image: python:3.11
  script:
    - pip install mcp
    - |
      python << 'EOF'
      import asyncio
      import sys
      sys.path.insert(0, 'guardrail_mcp/mcp_project')
      from guardrail_server import generate_compliance_report
      
      async def main():
          result = await generate_compliance_report({
              "repo_path": ".",
              "report_format": "json"
          })
          with open("guardrail-results.json", "w") as f:
              f.write(result[0].text)
      
      asyncio.run(main())
      EOF
  artifacts:
    paths:
      - guardrail-results.json
    expire_in: 30 days
  rules:
    - if: $CI_COMMIT_BRANCH == $CI_DEFAULT_BRANCH
```

---

## Jenkins Integration

### Jenkinsfile

```groovy
pipeline {
    agent any
    
    stages {
        stage('Guardrail Check') {
            steps {
                script {
                    def scanResult = sh(
                        script: '''
                            python3 << 'EOF'
                            import asyncio
                            import sys
                            sys.path.insert(0, 'guardrail_mcp/mcp_project')
                            from guardrail_server import scan_repository, block_commit
                            
                            async def main():
                                # Get changed files from PR
                                import subprocess
                                result = subprocess.run(
                                    ["git", "diff", "--name-only", "origin/main...HEAD"],
                                    capture_output=True, text=True
                                )
                                changed_files = [f.strip() for f in result.stdout.split('\\n') if f.strip()]
                                
                                # Block commit check
                                block_result = await block_commit({
                                    "files": changed_files,
                                    "block_on_severity": "critical"
                                })
                                print(block_result[0].text)
                                
                                # Return exit code
                                if "🚫 COMMIT BLOCKED" in block_result[0].text:
                                    return 1
                                return 0
                            
                            result = asyncio.run(main())
                            sys.exit(result)
                            EOF
                        ''',
                        returnStatus: true
                    )
                    
                    if (scanResult != 0) {
                        error("Guardrail check failed - critical violations found")
                    }
                }
            }
        }
        
        stage('Compliance Report') {
            steps {
                sh '''
                    python3 << 'EOF'
                    import asyncio
                    import sys
                    sys.path.insert(0, 'guardrail_mcp/mcp_project')
                    from guardrail_server import generate_compliance_report
                    
                    async def main():
                        result = await generate_compliance_report({
                            "repo_path": ".",
                            "report_format": "markdown"
                        })
                        with open("compliance-report.md", "w") as f:
                            f.write(result[0].text)
                    
                    asyncio.run(main())
                    EOF
                '''
                
                archiveArtifacts artifacts: 'compliance-report.md', fingerprint: true
            }
        }
    }
    
    post {
        always {
            publishHTML([
                allowMissing: false,
                alwaysLinkToLastBuild: true,
                keepAll: true,
                reportDir: '.',
                reportFiles: 'compliance-report.md',
                reportName: 'Guardrail Compliance Report'
            ])
        }
    }
}
```

---

## Pre-Commit Hook (Local Dev)

Create `.pre-commit-hooks/guardrail-check.sh`:

```bash
#!/bin/bash
# Guardrail pre-commit hook

STAGED_FILES=$(git diff --cached --name-only --diff-filter=ACM | grep -E '\.(py|js|ts|java)$' || true)

if [ -z "$STAGED_FILES" ]; then
    exit 0
fi

echo "🔒 Running Guardrail check on staged files..."

python3 << 'EOF'
import asyncio
import sys
import subprocess

# Get staged Python files
result = subprocess.run(
    ["git", "diff", "--cached", "--name-only", "--diff-filter=ACM"],
    capture_output=True, text=True
)
files = [f.strip() for f in result.stdout.split('\n') if f.strip().endswith(('.py', '.js', '.ts'))]

if not files:
    sys.exit(0)

sys.path.insert(0, 'guardrail_mcp/mcp_project')
from guardrail_server import block_commit

async def main():
    result = await block_commit({
        "files": files,
        "block_on_severity": "critical"
    })
    print(result[0].text)
    
    if "🚫 COMMIT BLOCKED" in result[0].text:
        sys.exit(1)
    sys.exit(0)

asyncio.run(main())
EOF

exit $?
```

Install the hook:

```bash
chmod +x .pre-commit-hooks/guardrail-check.sh
ln -s ../../.pre-commit-hooks/guardrail-check.sh .git/hooks/pre-commit
```

---

## DevOps Best Practices

### 1. Severity-Based Blocking

| Stage | Threshold | Action |
|-------|-----------|--------|
| Pre-commit | Critical | Block commit |
| PR Check | High | Block merge |
| Pre-deploy | Medium | Require approval |
| Production | Any | Full audit |

### 2. Gradual Rollout

```yaml
# Phase 1: Advisory only (monitoring mode)
guardrail_scan:
  script:
    - python guardrail_scan.py || true  # Don't fail pipeline

# Phase 2: Block critical only
guardrail_scan:
  script:
    - python guardrail_scan.py --block-on critical

# Phase 3: Full enforcement
guardrail_scan:
  script:
    - python guardrail_scan.py --block-on high
  allow_failure: false
```

### 3. Exception Process

Create `.guardrail-exceptions.yml`:

```yaml
# Guardrail Exceptions
# Requires: Manager approval + Security review

exceptions:
  - rule: sql_injection
    file: "legacy/migration_script.py"
    reason: "One-time migration, no user input"
    approved_by: "security-team@example.com"
    expires: "2025-06-01"
    
  - rule: hardcoded_password
    file: "tests/test_config.py"
    reason: "Test-only credentials in isolated test DB"
    approved_by: "dev-lead@example.com"
    expires: "2025-12-31"
```

### 4. Compliance Dashboard

Integrate with compliance systems:

```python
# Submit results to compliance API
import requests

compliance_data = {
    "repository": os.environ.get("GITHUB_REPOSITORY"),
    "commit": os.environ.get("GITHUB_SHA"),
    "scan_results": guardrail_results,
    "timestamp": datetime.utcnow().isoformat(),
    "pipeline_url": os.environ.get("GITHUB_SERVER_URL") + "/" + os.environ.get("GITHUB_RUN_ID")
}

requests.post(
    "https://compliance.example.com/api/v1/guardrail-reports",
    json=compliance_data,
    headers={"Authorization": "Bearer " + os.environ.get("COMPLIANCE_TOKEN")}
)
```

---

## Reporting & Notifications

### Slack Notifications

```yaml
- name: Notify Slack on Guardrail Failure
  if: failure()
  uses: 8398a7/action-slack@v3
  with:
    status: ${{ job.status }}
    text: |
      🚫 *Guardrail Check Failed*
      
      Repository: ${{ github.repository }}
      Commit: ${{ github.sha }}
      Author: ${{ github.actor }}
      
      Critical security violations detected.
      PR cannot be merged until resolved.
    webhook_url: ${{ secrets.SLACK_WEBHOOK_URL }}
```

### Email Notifications

```yaml
- name: Send Email Alert
  if: failure() && github.ref == 'refs/heads/main'
  uses: dawidd6/action-send-mail@v3
  with:
    server_address: smtp.example.com
    username: ${{ secrets.EMAIL_USERNAME }}
    password: ${{ secrets.EMAIL_PASSWORD }}
    subject: '🚨 Guardrail Alert: Critical violations in main branch'
    body: |
      Guardrail security scan detected critical violations
      in the main branch of ${{ github.repository }}.
      
      Immediate attention required.
    to: security-team@example.com,dev-leads@example.com
```

---

## Troubleshooting

### Issue: Pipeline fails but no violations in local scan

**Cause**: Different configurations between local and CI  
**Fix**: Ensure `.guardrail-config.yml` is committed and used in both

### Issue: SARIF upload fails

**Cause**: GitHub Advanced Security not enabled  
**Fix**: Enable in repo settings or use markdown reports instead

### Issue: Slow scan times

**Fix**: Add caching and parallelization:

```yaml
- name: Cache Guardrail Results
  uses: actions/cache@v3
  with:
    path: .guardrail-cache
    key: guardrail-${{ hashFiles('**/requirements.txt', '**/package.json') }}
```

### Issue: False positives blocking valid code

**Fix**: Use exception file or adjust rules:

```yaml
- name: Run Guardrails (with exceptions)
  run: |
    python guardrail_scan.py \
      --exceptions .guardrail-exceptions.yml \
      --block-on critical
```

---

## Quick Reference

### GitHub Actions
```yaml
uses: your-org/guardrail-action@v1
with:
  severity-threshold: 'high'
  report-format: 'sarif'
```

### Azure DevOps
```yaml
- task: Guardrails@1
  inputs:
    severityThreshold: 'high'
    generateReport: true
```

### GitLab CI
```yaml
include:
  - template: guardrails.gitlab-ci.yml
```

---

**Document Version**: 1.0  
**Last Updated**: March 2025  
**Compatible with**: GitHub, Azure DevOps, GitLab, Jenkins
