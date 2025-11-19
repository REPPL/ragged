# ragged Security Policy

**Project:** ragged - Privacy-first Retrieval-Augmented Generation system

**License:** GPL-3.0

---

## Executive Summary

This document defines the security policy for ragged, a privacy-first RAG system. Security and privacy are foundational principles, not afterthoughts. All contributors must follow these policies to protect user data and maintain trust.

**Key Principles:**
- **Privacy-by-Design:** Security and privacy built into features from the start
- **Transparency:** All AI assistance disclosed, security practices documented
- **Defence-in-Depth:** Multiple layers of security controls
- **Responsible Disclosure:** Clear process for reporting vulnerabilities
- **Continuous Improvement:** Regular security audits and updates

---

## Security Principles

### 1. Privacy-First Architecture

ragged is designed with privacy as the default:

**Data Minimisation:**
- Only collect and store data necessary for functionality
- Use query hashing (SHA-256) instead of plaintext storage
- No telemetry or usage tracking
- No data sent to external services without explicit user consent

**User Control:**
- Users own their data
- Full GDPR compliance (deletion, export, access rights)
- Transparent privacy settings
- Clear communication when PII detected

**Local-Only by Default:**
- All processing happens locally
- No cloud dependencies required
- User data never leaves device unless explicitly configured

### 2. Secure-by-Default

**Session Isolation:**
- UUID-based session IDs (v0.2.10)
- Session-scoped caching prevents cross-user leakage
- No global state for user data

**Encryption at Rest:**
- Fernet (AES-128) encryption for sensitive data (v0.2.11)
- File permissions: 0o600 (user read/write only)
- Encryption keys stored securely (never in version control)

**Input Validation:**
- All user input sanitised
- Path traversal prevention
- SQL injection prevention (parameterised queries)
- Command injection prevention

**Dependency Security:**
- All dependencies GPL-3.0 compatible (MIT, Apache 2.0, BSD)
- Regular CVE scanning
- Minimal dependency footprint
- Pin specific versions (not `latest`)

### 3. Defence-in-Depth

Multiple security layers protect against vulnerabilities:

1. **Application Layer:**
   - Input validation
   - Output encoding
   - Session management
   - Authentication (API keys for v0.3.13 REST API)

2. **Data Layer:**
   - Encryption at rest
   - Query hashing
   - PII detection and redaction
   - TTL-based cleanup

3. **System Layer:**
   - File permissions (0o600 for sensitive files)
   - Process isolation
   - Sandboxing (experimental Docker environment)

4. **Development Layer:**
   - Pre-commit security hooks
   - Security testing framework
   - Code review requirements
   - Dependency scanning

---

## Vulnerability Disclosure Policy

### Reporting Security Issues

**DO NOT** open public GitHub issues for security vulnerabilities.

**Instead:**

1. **Email:** security@ragged.dev (if available) OR create a private security advisory on GitHub
2. **Include:**
   - Description of the vulnerability
   - Steps to reproduce
   - Affected versions
   - Potential impact
   - Suggested fix (if available)

3. **Response Time:**
   - Acknowledgement: Within 48 hours
   - Initial assessment: Within 7 days
   - Fix timeline: Depends on severity (see below)

### Severity Levels

| Severity | Definition | Response Time | Examples |
|----------|-----------|---------------|----------|
| **CRITICAL** | Arbitrary code execution, data breach affecting multiple users | 24-48 hours | Pickle vulnerability (CVE-style), SQL injection |
| **HIGH** | Single user data exposure, authentication bypass | 7 days | PII leakage, session hijacking |
| **MEDIUM** | Denial of service, information disclosure (non-PII) | 30 days | Resource exhaustion, verbose error messages |
| **LOW** | Minor information disclosure, configuration issues | 90 days | Version disclosure, timing attacks |

### Security Updates

**Critical/High severity:**
- Immediate patch release (v0.X.Y+1)
- Security advisory published
- Users notified via GitHub releases
- CVE requested (if applicable)

**Medium/Low severity:**
- Fixed in next minor release
- Documented in CHANGELOG.md
- Security advisory (if warranted)

---

## Secure Coding Standards

### General Guidelines

1. **Never Trust User Input:**
   - Validate all input
   - Sanitise before processing
   - Use parameterised queries (SQL)
   - Escape output appropriately

2. **Principle of Least Privilege:**
   - Minimal file permissions
   - Minimal process privileges
   - Minimal API access

3. **Fail Securely:**
   - Default to deny
   - Graceful error handling
   - No sensitive information in error messages
   - Log security events

4. **Keep Secrets Secret:**
   - Never commit secrets to git
   - Use environment variables or secure key stores
   - Encrypt secrets at rest
   - Rotate keys periodically

### Python-Specific Standards

**Avoid Dangerous Functions:**
```python
# ❌ NEVER USE
import pickle  # Arbitrary code execution
eval()         # Code injection
exec()         # Code injection
os.system()    # Command injection

# ✅ SAFE ALTERNATIVES
import json    # Safe serialisation
ast.literal_eval()  # Safe evaluation (literals only)
subprocess.run(["cmd", "arg"], shell=False)  # Safe command execution
```

**Secure File Operations:**
```python
# ✅ GOOD: Explicit file permissions
from pathlib import Path
file_path = Path("sensitive.dat")
file_path.touch(mode=0o600)  # User read/write only

# ✅ GOOD: Path traversal prevention
from pathlib import Path
base_dir = Path("/safe/directory")
user_path = Path(user_input).resolve()
if not user_path.is_relative_to(base_dir):
    raise ValueError("Path traversal attempt detected")
```

**Secure Database Operations:**
```python
# ✅ GOOD: Parameterised queries
cursor.execute("SELECT * FROM queries WHERE session_id = ?", (session_id,))

# ❌ BAD: String interpolation (SQL injection)
cursor.execute(f"SELECT * FROM queries WHERE session_id = '{session_id}'")
```

**PII Handling:**
```python
# ✅ GOOD: Hash before logging/storing
from ragged.privacy import hash_query

query_hash = hash_query(user_question)  # One-way hash
logger.info(f"Query processed: {query_hash}")

# ❌ BAD: Plaintext PII in logs
logger.info(f"Query: {user_question}")  # May contain email, names, etc.
```

### OWASP Top 10 Mitigation

ragged follows OWASP Top 10 guidelines:

1. **Broken Access Control:** Session isolation, API authentication
2. **Cryptographic Failures:** Fernet encryption, secure key management
3. **Injection:** Parameterised queries, input validation
4. **Insecure Design:** Privacy-by-design, threat modelling
5. **Security Misconfiguration:** Secure defaults, minimal permissions
6. **Vulnerable Components:** CVE scanning, dependency audits
7. **Authentication Failures:** API keys (v0.3.13), rate limiting
8. **Data Integrity Failures:** Checksums, signature verification
9. **Logging Failures:** Query hashing, no PII in logs
10. **Server-Side Request Forgery:** URL validation, allowlists

---

## Security Testing Requirements

### Pre-Commit Requirements

All commits must pass security validation:

```bash
# Pre-commit hooks (v0.2.10)
- Secrets scanning (detect-secrets)
- Dependency CVE check (safety)
- Static analysis (bandit)
- Linting (ruff with security rules)
```

**Mandatory checks:**
- [ ] No secrets in code (API keys, passwords, tokens)
- [ ] No dangerous functions (pickle, eval, exec)
- [ ] No SQL string interpolation
- [ ] File permissions secure (0o600 for sensitive files)
- [ ] Input validation present
- [ ] British English compliance

### Security Testing by Version

**All v0.2.x and v0.3.x versions:**
- Unit tests for security controls
- Integration tests for session isolation
- Fuzzing for input validation
- Static analysis (bandit)

**Data-handling features (v0.3.9, v0.3.10, v0.3.13):**
- [ ] Session isolation verified (no cross-user leakage)
- [ ] PII detection tested (100+ test cases)
- [ ] Query hashing validated (no plaintext storage)
- [ ] Encryption verified (decryption round-trip)
- [ ] TTL cleanup functional (automated tests)
- [ ] GDPR deletion tested (all data removed)
- [ ] GDPR export tested (complete data returned)

### Security Agent Workflow

Use the `codebase-security-auditor` agent:

**When to invoke:**
1. After implementing each feature
2. Before committing code
3. Before each release
4. After dependency updates
5. Quarterly security audits

**Agent checks:**
- OWASP Top 10 vulnerabilities
- CWE (Common Weakness Enumeration) patterns
- Insecure dependencies
- Code quality issues
- Configuration vulnerabilities

---

## Dependency Management

### Dependency Selection Criteria

Before adding a dependency:

1. **License Compatibility:**
   - Must be GPL-3.0 compatible
   - Acceptable: MIT, Apache 2.0, BSD, LGPL
   - Forbidden: Proprietary, non-commercial licenses

2. **Security Track Record:**
   - Check CVE database
   - Review security advisories
   - Assess maintainer responsiveness
   - Prefer mature, well-maintained libraries

3. **Necessity:**
   - Is this dependency truly needed?
   - Can we implement internally?
   - What's the attack surface increase?

### Dependency Monitoring

**Continuous monitoring:**
```bash
# Check for CVEs
safety check

# Check for outdated packages
pip list --outdated

# Audit dependencies
pip-audit
```

**Update policy:**
- **Critical security updates:** Immediate (within 48h)
- **High security updates:** Within 7 days
- **Medium/Low security updates:** Next minor release
- **Feature updates:** Evaluated on case-by-case basis

### Pinned Versions

```toml
# ✅ GOOD: Specific versions
langchain = "^0.1.0"      # Pin major.minor, allow patch
chromadb = "^0.4.18"      # Specific version tested

# ❌ BAD: Unpinned versions
langchain = "*"           # Any version (dangerous)
chromadb = "latest"       # Moving target
```

---

## Incident Response

### Security Incident Classification

**Level 1 - Critical:**
- Active exploitation detected
- Data breach confirmed
- System compromise

**Level 2 - High:**
- Vulnerability disclosed publicly
- Suspected unauthorised access
- PII exposure

**Level 3 - Medium:**
- Vulnerability reported privately
- Suspicious activity detected
- Configuration issue

**Level 4 - Low:**
- Potential vulnerability (unconfirmed)
- Security best practice violation

### Incident Response Process

**1. Detection & Analysis (0-2 hours):**
- Confirm incident severity
- Identify affected systems/users
- Document initial findings
- Escalate if needed

**2. Containment (2-6 hours):**
- Isolate affected systems
- Revoke compromised credentials
- Block attack vectors
- Preserve evidence

**3. Eradication (6-24 hours):**
- Remove malicious code/access
- Patch vulnerabilities
- Validate fix effectiveness
- Test in isolated environment

**4. Recovery (24-48 hours):**
- Restore systems from clean backups
- Monitor for reinfection
- Verify normal operations
- Communicate with users

**5. Post-Incident Review (1 week):**
- Root cause analysis
- Document lessons learned
- Update security controls
- Revise policies if needed

### Communication Plan

**Internal:**
- Core team notified immediately (Level 1-2)
- Development team notified within 24h (all levels)
- Post-mortem shared with all contributors

**External:**
- **Critical incidents:** Public advisory within 48h
- **High incidents:** Advisory within 7 days
- **Medium/Low incidents:** Documented in CHANGELOG.md
- Affected users notified directly (if identifiable)

---

## AI Transparency & Security

### AI-Assisted Development Disclosure

ragged is developed with full AI transparency:

**Commit Messages:**
```
feat(privacy): Add PII detection to query handler

Implemented regex-based PII detection for email, phone, SSN patterns.
Integrated with encryption system from v0.2.11.

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
```

**Security Implications:**
- AI-generated code undergoes same security review as human code
- All code tested and validated
- Security agent reviews all changes
- Human approval required for commits

### AI Safety Considerations

**Prompt Injection:**
- User queries sanitised before LLM processing
- System prompts protected from user input
- Output validation (no code execution from LLM)

**Model Bias:**
- RAGAS evaluation detects quality issues
- Diverse test datasets
- Bias monitoring in metrics (v0.3.10)

**Data Privacy:**
- User queries NOT sent to OpenAI/Anthropic by default
- Local embedding models preferred
- Clear consent required for API-based models
- No query data in telemetry

---

## Compliance & Standards

### GDPR Compliance

ragged complies with GDPR requirements:

**Data Protection Principles (Article 5):**
- ✅ Lawfulness, fairness, transparency
- ✅ Purpose limitation
- ✅ Data minimisation
- ✅ Accuracy
- ✅ Storage limitation (TTL cleanup)
- ✅ Integrity and confidentiality (encryption)

**User Rights:**
- ✅ Right to access (Article 15)
- ✅ Right to erasure (Article 17)
- ✅ Right to data portability (Article 20)
- ✅ Right to be informed (Article 13)

**Implementation:**
```bash
# CLI commands (v0.3.9+)
ragged privacy status        # Show stored data
ragged privacy export        # Export user data
ragged privacy delete        # Delete all data
```

### Security Standards

ragged follows these security standards:

**CWE (Common Weakness Enumeration):**
- CWE-89: SQL Injection (prevented via parameterised queries)
- CWE-79: Cross-Site Scripting (output encoding)
- CWE-502: Deserialisation (no Pickle, JSON only)
- CWE-259: Hard-coded credentials (environment variables)
- CWE-22: Path traversal (path validation)

**NIST Cybersecurity Framework:**
- **Identify:** Threat modelling, asset inventory
- **Protect:** Encryption, access control, security training
- **Detect:** Logging, monitoring, security testing
- **Respond:** Incident response plan
- **Recover:** Backups, disaster recovery

---

## Security Roadmap

### Completed (v0.2.10 - v0.2.11)

- ✅ Pickle vulnerability eliminated
- ✅ Session isolation implemented
- ✅ Encryption at rest (Fernet)
- ✅ PII detection and redaction
- ✅ TTL-based data lifecycle
- ✅ GDPR compliance foundations
- ✅ Security testing framework

### Planned (v0.3.x)

**v0.3.9 (REPL):**
- Encrypted session files
- PII warnings on input
- Session cleanup

**v0.3.10 (Metrics DB):**
- Query hashing (NOT plaintext)
- Database encryption
- Privacy-safe metrics

**v0.3.13 (REST API):**
- API key authentication
- Rate limiting
- CORS security
- Session isolation per client

### Future (v0.4.x+)

**v0.4.x:**
- Multi-factor authentication
- OAuth2 integration
- Audit logging enhancements

**v0.5.x:**
- Differential privacy for metrics
- Homomorphic encryption (research)
- Zero-knowledge proofs (research)

**v1.0:**
- Third-party security audit
- Penetration testing
- Security certification
- Bug bounty programme

---

## Roles & Responsibilities

### Security Team

**Security Lead:**
- Overall security strategy
- Vulnerability assessment
- Incident response coordination
- Security policy updates

**Developers:**
- Secure coding practices
- Security testing
- Vulnerability remediation
- Code reviews (security focus)

**Contributors:**
- Follow security policy
- Report vulnerabilities responsibly
- Complete security training
- Sign contributor agreement

### Reporting Structure

```
Security Incident
    ↓
Security Lead (immediate notification)
    ↓
Core Development Team (within 24h)
    ↓
Community (public advisory if needed)
```

---

## Security Training

### Required Training for Contributors

**Before first contribution:**
- [ ] Read this security policy
- [ ] Complete OWASP Top 10 training
- [ ] Review secure coding standards
- [ ] Understand privacy-by-design principles

**Ongoing:**
- Quarterly security updates
- New vulnerability awareness
- Threat landscape changes
- Tool and process updates

### Resources

**Internal:**
- [Privacy Architecture](./privacy-architecture.md)
- [v0.2.10 Security Roadmap](../roadmap/version/v0.2/v0.2.10/)
- [v0.2.11 Privacy Roadmap](../roadmap/version/v0.2/v0.2.11/)

**External:**
- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [CWE Top 25](https://cwe.mitre.org/top25/)
- [Python Security Best Practices](https://python.readthedocs.io/en/stable/library/security_warnings.html)
- [GDPR Official Text](https://gdpr-info.eu/)

---

## Policy Updates

This security policy is a living document and will be updated regularly:

**Review Schedule:**
- After security incidents (immediate)
- Quarterly reviews (minimum)
- Before major releases (v0.X.0)
- When industry standards change

**Change Process:**
1. Propose changes (GitHub issue or PR)
2. Security team review
3. Community feedback (7 days)
4. Core team approval
5. Documentation update
6. Announcement (if significant)

---

## Contact

**Security Issues:** Create private security advisory on GitHub

**General Security Questions:** Open public GitHub issue (non-sensitive)

**Project Maintainers:** See MAINTAINERS.md

---

