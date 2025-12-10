# Security Review Checklist

This document provides a comprehensive security checklist for the Todo Backend application. Use this before deploying to production and as part of regular security audits.

## Table of Contents

- [Pre-Deployment Security Tests](#pre-deployment-security-tests)
- [Penetration Testing Checklist](#penetration-testing-checklist)
- [OWASP Top 10 Validation](#owasp-top-10-validation)
- [JWT Security Review](#jwt-security-review)
- [Input Validation Review](#input-validation-review)
- [Database Security](#database-security)
- [Infrastructure Security](#infrastructure-security)
- [Compliance and Best Practices](#compliance-and-best-practices)

---

## Pre-Deployment Security Tests

### Automated Security Scans

- [ ] **Dependency Vulnerability Scan**: Run `pip-audit` or `safety check`
  ```bash
  uv run pip-audit
  # or
  uv run safety check
  ```

- [ ] **Static Code Analysis**: Run Bandit for security issues
  ```bash
  uv run bandit -r . -f json -o bandit-report.json
  ```

- [ ] **Container Security Scan**: Scan Docker image with Trivy
  ```bash
  docker build -t todo-backend:latest .
  trivy image todo-backend:latest
  ```

- [ ] **Secret Detection**: Check for exposed secrets
  ```bash
  # Using truffleHog or git-secrets
  trufflehog filesystem .
  ```

- [ ] **SAST Tools**: Run Semgrep or similar tools
  ```bash
  semgrep --config auto .
  ```

### Manual Security Checks

- [ ] **Environment Variables**: No secrets in code, .env not committed
- [ ] **API Keys**: All API keys rotated and stored securely
- [ ] **Debug Mode**: Debug mode disabled in production
- [ ] **Error Messages**: No sensitive data in error messages
- [ ] **Logging**: No passwords or tokens in logs

---

## Penetration Testing Checklist

### Authentication & Authorization

- [ ] **Brute Force Protection**: Rate limiting on auth endpoints
  ```bash
  # Test with curl/httpie
  for i in {1..100}; do
    curl -X POST http://localhost:8000/api/auth/signin \
      -H "Content-Type: application/json" \
      -d '{"email":"test@test.com","password":"wrong"}'
  done
  # Should get rate limited after threshold
  ```

- [ ] **SQL Injection**: Test with malicious input
  ```bash
  # Test email field
  curl -X POST http://localhost:8000/api/auth/signin \
    -H "Content-Type: application/json" \
    -d '{"email":"admin'\'' OR 1=1--","password":"test"}'
  # Should reject invalid email format
  ```

- [ ] **JWT Token Manipulation**: Try modifying token
  ```bash
  # Decode JWT and modify payload
  # Try using modified token - should fail
  ```

- [ ] **Session Hijacking**: Test token reuse after logout
  ```bash
  # Get token, logout, try using old token
  # Should return 401 Unauthorized
  ```

- [ ] **Password Policy**: Test weak passwords
  ```bash
  curl -X POST http://localhost:8000/api/auth/signup \
    -H "Content-Type: application/json" \
    -d '{"email":"test@test.com","password":"123","name":"Test"}'
  # Should reject (min 8 characters)
  ```

### API Endpoint Security

- [ ] **User Isolation**: Try accessing other users' data
  ```bash
  # User A tries to access User B's tasks
  # Should return 403 Forbidden
  ```

- [ ] **IDOR (Insecure Direct Object Reference)**: Test with sequential IDs
  ```bash
  # Try accessing tasks with different IDs
  curl -X GET http://localhost:8000/api/{user_a_id}/tasks/{user_b_task_id} \
    -H "Authorization: Bearer {user_a_token}"
  # Should return 404 or 403
  ```

- [ ] **Mass Assignment**: Try setting unexpected fields
  ```bash
  curl -X POST http://localhost:8000/api/{user_id}/tasks \
    -H "Authorization: Bearer {token}" \
    -H "Content-Type: application/json" \
    -d '{"title":"Test","user_id":"different-user-id"}'
  # Should ignore user_id field
  ```

- [ ] **HTTP Method Tampering**: Try unauthorized methods
  ```bash
  # Try DELETE on read-only endpoint
  curl -X DELETE http://localhost:8000/health
  # Should return 405 Method Not Allowed
  ```

### Input Validation

- [ ] **XSS in JSON**: Test script injection
  ```bash
  curl -X POST http://localhost:8000/api/{user_id}/tasks \
    -H "Authorization: Bearer {token}" \
    -H "Content-Type: application/json" \
    -d '{"title":"<script>alert(1)</script>","description":"test"}'
  # Should sanitize or reject
  ```

- [ ] **Large Payload**: Test with huge requests
  ```bash
  # Create 10MB request body
  # Should reject or handle gracefully
  ```

- [ ] **Unicode/Special Characters**: Test encoding issues
  ```bash
  curl -X POST http://localhost:8000/api/{user_id}/tasks \
    -H "Authorization: Bearer {token}" \
    -H "Content-Type: application/json" \
    -d '{"title":"Test \u0000 null byte","description":"test"}'
  # Should handle safely
  ```

- [ ] **File Upload Security**: Test import endpoint
  ```bash
  # Upload malicious CSV/JSON
  # Upload extremely large file
  # Upload file with null bytes
  # Should validate and reject
  ```

### API Rate Limiting

- [ ] **Rate Limit Bypass**: Test different techniques
  ```bash
  # Try with different IPs
  # Try with different User-Agents
  # Try concurrent requests
  # All should be rate limited
  ```

- [ ] **Rate Limit Headers**: Check response headers
  ```bash
  curl -I http://localhost:8000/api/{user_id}/tasks
  # Should include X-RateLimit-* headers
  ```

---

## OWASP Top 10 Validation

### A01:2021 – Broken Access Control

- [ ] User cannot access other users' tasks
- [ ] User cannot modify other users' data
- [ ] Admin endpoints (if any) properly protected
- [ ] Path traversal attacks prevented
- [ ] User ID from JWT matches URL user ID

**Test Commands**:
```bash
# Test cross-user access
USER_A_TOKEN="..." USER_B_ID="..."
curl -H "Authorization: Bearer $USER_A_TOKEN" \
  http://localhost:8000/api/$USER_B_ID/tasks
# Expected: 403 Forbidden
```

### A02:2021 – Cryptographic Failures

- [ ] Passwords hashed with bcrypt (not MD5/SHA1)
- [ ] JWT tokens signed with strong secret (64+ characters)
- [ ] Database connections use SSL/TLS
- [ ] No sensitive data in logs or error messages
- [ ] HTTPS enforced in production

**Verification**:
```bash
# Check password hash in database
# Should see bcrypt hash starting with $2b$
```

### A03:2021 – Injection

- [ ] SQLModel ORM prevents SQL injection
- [ ] Parameterized queries everywhere
- [ ] Input validation on all fields
- [ ] No eval() or exec() usage
- [ ] Command injection prevented

**Test Commands**:
```bash
# SQL injection attempts
curl -X POST http://localhost:8000/api/auth/signin \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@example.com OR 1=1","password":"test"}'
# Expected: 400 Bad Request (invalid email)
```

### A04:2021 – Insecure Design

- [ ] User isolation enforced at multiple layers
- [ ] Rate limiting implemented
- [ ] Token expiration configured (7 days)
- [ ] No admin endpoints without proper auth
- [ ] Secure defaults everywhere

### A05:2021 – Security Misconfiguration

- [ ] Debug mode disabled in production
- [ ] CORS properly configured (not wildcard *)
- [ ] Security headers present
- [ ] Directory listing disabled
- [ ] Error messages don't expose internals

**Check Headers**:
```bash
curl -I http://localhost:8000/api/{user_id}/tasks
# Should include security headers:
# X-Content-Type-Options: nosniff
# X-Frame-Options: SAMEORIGIN
# X-XSS-Protection: 1; mode=block
```

### A06:2021 – Vulnerable and Outdated Components

- [ ] Python 3.13+ used
- [ ] All dependencies up to date
- [ ] No known vulnerabilities in dependencies
- [ ] Regular dependency updates scheduled

**Check**:
```bash
uv run pip-audit
# Should show no vulnerabilities
```

### A07:2021 – Identification and Authentication Failures

- [ ] Strong password policy (8+ characters)
- [ ] JWT tokens properly validated
- [ ] Token expiration enforced
- [ ] No default credentials
- [ ] Rate limiting on auth endpoints

### A08:2021 – Software and Data Integrity Failures

- [ ] Dependencies pinned in pyproject.toml
- [ ] Docker image uses specific versions
- [ ] Database migrations tracked
- [ ] No unsigned code execution
- [ ] CI/CD pipeline validates builds

### A09:2021 – Security Logging and Monitoring Failures

- [ ] Authentication failures logged
- [ ] Unauthorized access attempts logged
- [ ] Security events monitored
- [ ] Alerts configured for anomalies
- [ ] Log rotation configured

**Check Logs**:
```bash
# Failed login should be logged
grep "authentication failed" logs/app.log
```

### A10:2021 – Server-Side Request Forgery (SSRF)

- [ ] No endpoints accepting arbitrary URLs
- [ ] Import endpoints validate file types
- [ ] No proxy/redirect functionality
- [ ] Network egress controlled

---

## JWT Security Review

### Token Generation

- [ ] **Strong Secret**: BETTER_AUTH_SECRET is 64+ characters
  ```bash
  echo $BETTER_AUTH_SECRET | wc -c
  # Should be >= 64
  ```

- [ ] **Algorithm**: Uses HS256 (not none or RS256 without verification)
- [ ] **Claims**: Includes user_id and email
- [ ] **Expiration**: Set to 7 days (604800 seconds)
- [ ] **Issuer**: Set to application identifier

### Token Validation

- [ ] **Signature Verification**: Every request validates signature
- [ ] **Expiration Check**: Expired tokens rejected
- [ ] **Algorithm Check**: Only HS256 accepted
- [ ] **Claim Validation**: Required claims present
- [ ] **Token Revocation**: Logout invalidates token (client-side)

### Token Storage & Transmission

- [ ] **HTTPS Only**: Tokens only transmitted over HTTPS in prod
- [ ] **HTTP-Only Cookies**: Consider using HTTP-only cookies
- [ ] **Authorization Header**: Bearer token in header (not URL)
- [ ] **No Token in Logs**: Tokens filtered from logs

**Test**:
```bash
# Try expired token
# Try tampered token
# Try token with wrong signature
# All should return 401
```

---

## Input Validation Review

### Email Validation

- [ ] Email format validated (Pydantic EmailStr)
- [ ] Maximum length enforced (255 characters)
- [ ] No special characters that could cause issues
- [ ] Case normalization applied

### Password Validation

- [ ] Minimum length 8 characters
- [ ] No maximum length (allow passphrases)
- [ ] Stored as bcrypt hash
- [ ] Never logged or returned in responses

### Task Title Validation

- [ ] Maximum 200 characters
- [ ] Not empty after stripping whitespace
- [ ] Special characters allowed but sanitized
- [ ] Unicode handled properly

### Task Description Validation

- [ ] Maximum 1000 characters
- [ ] Optional field
- [ ] Null/empty handled correctly

### Priority Validation

- [ ] Only allowed values: low, medium, high
- [ ] Case-insensitive
- [ ] Default value: medium
- [ ] Invalid values rejected with 400

### Tags Validation

- [ ] Array of strings
- [ ] Empty strings filtered out
- [ ] Duplicates allowed/removed (decide which)
- [ ] Maximum tag count (consider limit)
- [ ] Maximum tag length (consider limit)

### Due Date Validation

- [ ] ISO 8601 format required
- [ ] Future dates allowed
- [ ] Past dates allowed (for completed tasks)
- [ ] Timezone handling correct

### Bulk Operations Validation

- [ ] task_ids array not empty
- [ ] task_ids are integers
- [ ] operation type validated
- [ ] User owns all task_ids

---

## Database Security

### Connection Security

- [ ] **SSL/TLS**: Database connection uses SSL (`sslmode=require`)
  ```bash
  echo $DATABASE_URL | grep sslmode=require
  ```

- [ ] **Credentials**: Strong password, not default
- [ ] **Connection Pooling**: Limits prevent exhaustion
- [ ] **Timeout**: Connection timeout configured

### Query Security

- [ ] **Parameterized Queries**: SQLModel ORM used (prevents SQL injection)
- [ ] **User Isolation**: All queries filter by user_id
- [ ] **No Raw SQL**: Avoid raw queries where possible
- [ ] **Transaction Management**: Proper commit/rollback

### Database Access

- [ ] **Least Privilege**: Database user has minimum permissions
- [ ] **No Admin Access**: Application doesn't use DBA account
- [ ] **Audit Logging**: Database audit log enabled
- [ ] **Backup Strategy**: Regular backups configured

### Indexes

- [ ] **Performance**: Indexes on user_id, email, completed, priority
- [ ] **Security**: Indexes don't expose sensitive data

---

## Infrastructure Security

### Docker Security

- [ ] **Non-Root User**: Container runs as user 'todoapp' (UID 1001)
- [ ] **Minimal Base Image**: Uses python:3.13-slim
- [ ] **No Secrets in Image**: Secrets passed as environment variables
- [ ] **Multi-Stage Build**: Smaller final image, less attack surface
- [ ] **Health Checks**: Container health monitored

**Verify**:
```bash
docker run --rm todo-backend:latest whoami
# Should output: todoapp (not root)
```

### Network Security

- [ ] **HTTPS**: SSL/TLS enforced in production
- [ ] **Firewall**: Only necessary ports open (80, 443, 8000)
- [ ] **Internal Network**: Backend not directly accessible
- [ ] **Reverse Proxy**: Nginx/Traefik in front of backend

### Environment Variables

- [ ] **Secrets Manager**: Production uses AWS Secrets Manager / Vault
- [ ] **No .env in Repo**: .env file in .gitignore
- [ ] **Secret Rotation**: Regular rotation schedule
- [ ] **Access Control**: Limited who can view secrets

### Server Hardening

- [ ] **OS Updates**: Server OS regularly updated
- [ ] **Unnecessary Services**: Disabled unnecessary services
- [ ] **SSH**: Key-based auth only, no root login
- [ ] **Monitoring**: Intrusion detection enabled

---

## Compliance and Best Practices

### GDPR Compliance (if applicable)

- [ ] **Data Minimization**: Only collect necessary data
- [ ] **Right to Deletion**: User can delete account and all data
- [ ] **Data Export**: User can export their data (CSV/JSON)
- [ ] **Consent**: Clear privacy policy and ToS
- [ ] **Data Encryption**: Data encrypted at rest and in transit

### Security Headers

```bash
# Check response headers
curl -I http://localhost:8000/api/health

# Should include:
# X-Content-Type-Options: nosniff
# X-Frame-Options: SAMEORIGIN
# X-XSS-Protection: 1; mode=block
# Content-Security-Policy: default-src 'self'
# Strict-Transport-Security: max-age=31536000; includeSubDomains
```

### Logging Best Practices

- [ ] **No Sensitive Data**: No passwords, tokens in logs
- [ ] **Security Events**: Failed logins, unauthorized access logged
- [ ] **Log Rotation**: Logs rotated and archived
- [ ] **Centralized Logging**: Logs sent to centralized system
- [ ] **Retention Policy**: Log retention period defined

### Incident Response

- [ ] **Incident Plan**: Security incident response plan documented
- [ ] **Contact List**: Security team contact information up to date
- [ ] **Runbooks**: Security runbooks for common scenarios
- [ ] **Backup/Restore**: Tested backup and restore procedures

---

## Security Testing Tools

### Recommended Tools

1. **SAST (Static Application Security Testing)**:
   - Bandit (Python security linter)
   - Semgrep (multi-language static analysis)
   - SonarQube (code quality and security)

2. **DAST (Dynamic Application Security Testing)**:
   - OWASP ZAP (penetration testing)
   - Burp Suite (web vulnerability scanner)
   - Nikto (web server scanner)

3. **Dependency Scanning**:
   - pip-audit (Python package vulnerabilities)
   - Safety (Python dependency checker)
   - Snyk (multi-language dependency scanner)

4. **Container Scanning**:
   - Trivy (container vulnerability scanner)
   - Clair (container vulnerability analyzer)
   - Docker Scout (Docker's security scanner)

5. **Secret Detection**:
   - truffleHog (find secrets in git repos)
   - git-secrets (prevent committing secrets)
   - detect-secrets (find secrets in code)

### Running Security Scans

```bash
# Full security scan workflow
cd phase-2/backend

# 1. SAST
uv run bandit -r . -ll -o bandit-report.json -f json

# 2. Dependency scan
uv run pip-audit

# 3. Container scan
docker build -t todo-backend:latest .
trivy image todo-backend:latest

# 4. Secret detection
trufflehog filesystem . --only-verified

# 5. DAST (requires running server)
uv run uvicorn main:app &
zap-cli quick-scan http://localhost:8000

# Review all reports before deployment
```

---

## Post-Deployment Security

### Continuous Monitoring

- [ ] **Prometheus Alerts**: Security alerts configured
- [ ] **Log Monitoring**: Centralized log analysis
- [ ] **Intrusion Detection**: IDS/IPS configured
- [ ] **Vulnerability Scanning**: Regular automated scans

### Regular Audits

- [ ] **Monthly**: Dependency vulnerability scan
- [ ] **Quarterly**: Full security audit
- [ ] **Annually**: Penetration testing by third party
- [ ] **Continuously**: Automated security scanning in CI/CD

### Security Updates

- [ ] **Patch Management**: Security patches applied within 48 hours
- [ ] **Dependency Updates**: Regular dependency updates (weekly)
- [ ] **Security Advisories**: Subscribed to security mailing lists
- [ ] **Incident Response**: 24/7 security incident response

---

## Sign-Off Checklist

Before deploying to production, ensure:

- [ ] All security tests passed
- [ ] Penetration testing completed
- [ ] OWASP Top 10 validated
- [ ] Security scan reports reviewed
- [ ] No high/critical vulnerabilities
- [ ] Secrets properly managed
- [ ] Monitoring and alerting configured
- [ ] Incident response plan in place
- [ ] Security team approval obtained
- [ ] Documentation up to date

**Deployment Approval**:

- Security Lead: _________________ Date: _______
- Technical Lead: ________________ Date: _______
- Product Owner: _________________ Date: _______

---

## Resources

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [OWASP Testing Guide](https://owasp.org/www-project-web-security-testing-guide/)
- [FastAPI Security](https://fastapi.tiangolo.com/tutorial/security/)
- [SQLModel Security](https://sqlmodel.tiangolo.com/)
- [Docker Security Best Practices](https://docs.docker.com/develop/security-best-practices/)
- [PostgreSQL Security](https://www.postgresql.org/docs/current/security.html)
