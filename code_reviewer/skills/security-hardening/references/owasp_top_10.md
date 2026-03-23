# 🛡️ OWASP Secure Coding for AI Agents

Guidance for mitigating the most critical security risks in Python-based AI applications.

## 1. Secret Management (A01:2021-Broken Access Control)
**Risk:** Hardcoded API keys, database credentials, or tokens.
**Mitigation:** Use environment variables or a secure secret manager (e.g., Google Secret Manager).

```python
# Before
API_KEY = "sk-..." 

# After
import os
from google.cloud import secretmanager

def get_secret(name):
    client = secretmanager.SecretManagerServiceClient()
    return client.access_secret_version(request={"name": name}).payload.data.decode("UTF-8")
```

## 2. Input Validation (A03:2021-Injection)
**Risk:** Prompt injection or SQL injection via user-provided strings.
**Mitigation:** Always sanitize inputs and use parameterized queries. Use specific validation schemas (e.g., Pydantic).

## 3. Tool Execution Safety (AI-Specific)
**Risk:** AI agents executing arbitrary shell commands or code without constraints.
**Mitigation:** Use sandboxed environments (e.g., gVisor, Restricted Python) and whitelist allowed commands/modules.

## 4. Insecure Output Handling
**Risk:** AI-generated content leading to XSS or downstream injection.
**Mitigation:** Treat all model outputs as untrusted. Sanitize before rendering in HTML.

## 5. Dependency Security
**Risk:** Vulnerable third-party libraries.
**Mitigation:** Pin versions in `requirements.txt` or `pyproject.toml` and use `pip-audit` or `Snyk`.
