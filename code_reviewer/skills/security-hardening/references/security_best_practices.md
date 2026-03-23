# 🔐 Security Best Practices Reference

This document provides standardized mitigation patterns for common security vulnerabilities.

## 1. Parameterized Queries
- **Problem:** SQL Injection via direct string concatenation in queries.
- **Fix:** Use placeholder symbols (`?`, `%s`) and pass variables as a separate argument to the execute method.
- **Benefit:** Prevents attackers from executing arbitrary SQL commands.

## 2. Environment Variables for Secrets
- **Problem:** Hardcoded API keys or tokens in source code.
- **Fix:** Load sensitive data from environment variables using `os.environ` or a `.env` file.
- **Benefit:** Prevents credential leakage during code commits or logging.

## 3. Least Privilege
- **Problem:** Using administrative or broad permissions for limited tasks.
- **Fix:** Restrict service accounts and API tokens to the bare minimum scope required.
- **Benefit:** Minimizes the blast radius of a potential compromise.
