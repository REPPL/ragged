# Security & Privacy Documentation

**Purpose:** Comprehensive security and privacy documentation for ragged.

**Last Updated:** 2025-11-19

---

## Overview

ragged is a **privacy-first** RAG system. Security and privacy are not afterthoughts—they are foundational architectural principles implemented from v0.2.10 onwards.

This directory contains:
- Security policies and procedures
- Privacy architecture documentation
- Security testing guidelines
- Incident response procedures

---

## Documents in This Directory

### [Security Policy](./policy.md)

**Purpose:** Comprehensive security policy for ragged contributors and users.

**Contents:**
- Security principles (Privacy-by-Design, Secure-by-Default, Defence-in-Depth)
- Vulnerability disclosure policy
- Secure coding standards
- Security testing requirements
- OWASP Top 10 mitigation
- Dependency management
- Incident response procedures
- AI transparency policy
- GDPR compliance

**Audience:** All contributors, security researchers, users

**When to Read:**
- Before contributing to ragged
- When reporting security issues
- When conducting security audits
- For compliance verification

---

### [Privacy Architecture](./privacy-architecture.md)

**Purpose:** Technical documentation of ragged's privacy architecture.

**Contents:**
- Privacy principles and design
- Session isolation architecture
- Encryption at rest (Fernet/AES-128)
- PII detection and handling
- Data lifecycle management (TTL cleanup)
- GDPR compliance implementation
- Privacy configuration
- Usage examples for v0.3.x features
- Privacy risk assessment

**Audience:** Developers, architects, privacy officers

**When to Read:**
- Implementing features that handle user data
- Integrating with v0.2.10/v0.2.11 privacy infrastructure
- Conducting privacy impact assessments
- Designing new privacy features

---

## Security & Privacy Foundation

### v0.2.10: Security Hardening

**Established:** November 2025

**Estimated Time:** 15-21 hours

**Key Features:**
- ✅ Pickle vulnerability eliminated (replaced with JSON)
- ✅ Session isolation (UUID-based session IDs)
- ✅ Session-scoped caching (prevents cross-user leakage)
- ✅ Security testing framework
- ✅ Pre-commit security hooks

**[→ v0.2.10 Roadmap](../roadmap/version/v0.2/v0.2.10/)**

### v0.2.11: Privacy Infrastructure

**Established:** November 2025

**Estimated Time:** 20-26 hours

**Key Features:**
- ✅ Encryption at rest (Fernet/AES-128)
- ✅ PII detection and redaction
- ✅ Query hashing (SHA-256 for logs/metrics)
- ✅ TTL-based data lifecycle management
- ✅ GDPR compliance foundations
- ✅ Privacy configuration system

**[→ v0.2.11 Roadmap](../roadmap/version/v0.2/v0.2.11/)**

### Combined Impact

**Total Investment:** 35-47 hours (one-time, foundational)

**Protects:** All v0.3.x+ features that handle user data

**Compliance:** GDPR, OWASP Top 10, CWE Top 25

---

## Quick Reference

### For Contributors

**Before contributing:**
1. Read [Security Policy](./policy.md) (sections 1-3, 5)
2. Review secure coding standards
3. Understand privacy-by-design principles
4. Set up pre-commit hooks (v0.2.10)

**During development:**
- Use `codebase-security-auditor` agent before commits
- Run security tests: `pytest tests/security/`
- Check for secrets: `detect-secrets scan`
- Validate dependencies: `safety check`

**Before committing:**
- [ ] No secrets in code
- [ ] No dangerous functions (pickle, eval, exec)
- [ ] Input validation present
- [ ] PII hashing used (not plaintext logging)
- [ ] British English compliance

### For Security Researchers

**Reporting vulnerabilities:**
- DO NOT open public GitHub issues
- Create private security advisory on GitHub
- Or email: security@ragged.dev (if available)
- Include: description, reproduction steps, impact, suggested fix

**Response times:**
- CRITICAL: 24-48 hours
- HIGH: 7 days
- MEDIUM: 30 days
- LOW: 90 days

**See:** [Vulnerability Disclosure Policy](./policy.md#vulnerability-disclosure-policy)

### For Users

**Privacy controls:**
```bash
# View privacy status
ragged privacy status

# Export your data (GDPR Article 15, 20)
ragged privacy export --format json --output my-data.json

# Delete all data (GDPR Article 17)
ragged privacy delete --confirm

# View privacy policy
ragged privacy policy

# Configure privacy settings
ragged config set privacy.ttl_sessions_days 14
ragged config set privacy.pii_detection_sensitivity strict
```

**Data stored by ragged:**
- ✅ Document embeddings (for RAG functionality)
- ✅ Session files (encrypted, TTL: 7 days)
- ✅ Performance metrics (query hashes only, TTL: 90 days)
- ✅ REPL history (encrypted, TTL: 7 days)
- ❌ Queries in plaintext (NEVER stored)
- ❌ Telemetry or usage tracking (NEVER enabled by default)

**See:** [Privacy Architecture](./privacy-architecture.md)

---

## Security Principles

### 1. Privacy-by-Design

Security and privacy are built into features from the start:
- v0.2.10/v0.2.11 completed BEFORE v0.3.x data-handling features
- All user input paths include PII detection
- Encryption transparent to application logic
- Session isolation at architecture level

### 2. Data Minimisation

Only collect and store necessary data:
- Query hashing (SHA-256) instead of plaintext storage
- No telemetry or usage tracking
- TTL-based automatic cleanup (7-90 days)
- User data never sent to external services without consent

### 3. User Control

Users own their data:
- Full GDPR compliance (access, erasure, portability)
- Transparent privacy settings
- Clear communication when PII detected
- No dark patterns

### 4. Defence-in-Depth

Multiple security layers:
- Application: Input validation, output encoding, authentication
- Data: Encryption, hashing, PII detection, TTL cleanup
- System: File permissions (0o600), process isolation
- Development: Pre-commit hooks, security testing, code review

---

## Privacy Risk Assessment

### High-Risk Features

Features that store/process user data have detailed privacy implementations:

| Feature | Version | Risk Score | Mitigation |
|---------|---------|-----------|-----------|
| **REPL** | v0.3.9 | 90/100 | Encrypted sessions, PII warnings, TTL cleanup |
| **Metrics DB** | v0.3.10 | 95/100 | Query hashing (NOT plaintext), DB encryption, TTL |
| **REST API** | v0.3.13 | 92/100 | Session isolation, authentication, rate limiting |

**Risk Score Interpretation:**
- 90-100: Excellent privacy protection
- 70-89: Good privacy, minor gaps
- 50-69: Moderate privacy, improvements needed
- <50: Poor privacy, urgent action required

**See:** [Privacy Risk Assessment](./privacy-architecture.md#privacy-risk-assessment)

---

## Compliance

### GDPR (General Data Protection Regulation)

ragged complies with GDPR requirements:

**Data Protection Principles (Article 5):**
- ✅ Lawfulness, fairness, transparency
- ✅ Purpose limitation
- ✅ Data minimisation
- ✅ Accuracy
- ✅ Storage limitation (TTL cleanup)
- ✅ Integrity and confidentiality (encryption)

**User Rights:**
- ✅ Right to access (Article 15): `ragged privacy status`
- ✅ Right to erasure (Article 17): `ragged privacy delete`
- ✅ Right to portability (Article 20): `ragged privacy export`

**See:** [GDPR Compliance](./privacy-architecture.md#gdpr-compliance)

### Security Standards

ragged follows these security standards:

**OWASP Top 10:**
- Broken Access Control: Session isolation, API authentication
- Cryptographic Failures: Fernet encryption, secure key management
- Injection: Parameterised queries, input validation
- Insecure Design: Privacy-by-design, threat modelling
- Security Misconfiguration: Secure defaults, minimal permissions
- Vulnerable Components: CVE scanning, dependency audits
- Authentication Failures: API keys, rate limiting
- Data Integrity Failures: Checksums, signature verification
- Logging Failures: Query hashing, no PII in logs
- SSRF: URL validation, allowlists

**CWE (Common Weakness Enumeration):**
- CWE-502: Deserialisation (no Pickle, JSON only)
- CWE-89: SQL Injection (parameterised queries)
- CWE-79: XSS (output encoding)
- CWE-259: Hard-coded credentials (environment variables)
- CWE-22: Path traversal (path validation)

**See:** [Security Standards](./policy.md#compliance--standards)

---

## Security Testing

### Pre-Commit Requirements

All commits must pass security validation:

```bash
# Secrets scanning
detect-secrets scan

# Dependency CVE check
safety check

# Static analysis
bandit -r src/

# Linting with security rules
ruff check --select S
```

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
- CWE patterns
- Insecure dependencies
- Code quality issues
- Configuration vulnerabilities

### Testing by Feature Type

**For ALL versions:**
- [ ] Unit tests for security controls
- [ ] Static analysis passing
- [ ] No secrets in code
- [ ] Dependencies CVE-free
- [ ] British English compliance

**For data-handling features (v0.3.9, v0.3.10, v0.3.13):**
- [ ] Session isolation verified
- [ ] PII detection tested (100+ test cases)
- [ ] Query hashing validated
- [ ] Encryption round-trip verified
- [ ] TTL cleanup functional
- [ ] GDPR deletion tested
- [ ] GDPR export tested

**See:** [Security Testing Requirements](./policy.md#security-testing-requirements)

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

### Response Process

**Detection → Containment → Eradication → Recovery → Post-Incident Review**

**Timelines:**
- Detection & Analysis: 0-2 hours
- Containment: 2-6 hours
- Eradication: 6-24 hours
- Recovery: 24-48 hours
- Post-Incident Review: 1 week

**See:** [Incident Response](./policy.md#incident-response)

---

## Architecture Integration

### How v0.3.x Uses Privacy Foundation

All v0.3.x features integrate with v0.2.10/v0.2.11 infrastructure:

**From v0.2.10 (Session Isolation):**
```python
from ragged.session import Session, SessionManager

# All features use session-scoped operations
session = SessionManager().get_or_create_session()
cache_key = make_cache_key(session.session_id, query, **kwargs)
```

**From v0.2.11 (Privacy Infrastructure):**
```python
from ragged.privacy import (
    EncryptionManager,
    hash_query,
    contains_pii,
    redact_pii,
    CleanupScheduler,
)

# Encrypt sensitive data
encryption = EncryptionManager()
encrypted_data = encryption.encrypt(sensitive_data.encode())

# Hash queries for logging/metrics (NOT plaintext)
query_hash = hash_query(user_question)

# Detect PII in user input
if contains_pii(user_input):
    warn_user("Input contains PII - will be encrypted")

# Schedule TTL cleanup
scheduler = CleanupScheduler()
scheduler.schedule_cleanup(data_path, ttl_days=90)
```

**See detailed integration examples:**
- [v0.3.9 Privacy Implementation](../roadmap/version/v0.3/v0.3.9.md#privacy--security-implementation)
- [v0.3.10 Privacy Implementation](../roadmap/version/v0.3/v0.3.10.md#privacy--security-implementation)
- [v0.3.13 Privacy Implementation](../roadmap/version/v0.3/v0.3.13.md#privacy--security-implementation)

---

## Future Roadmap

### v0.4.x: Advanced Privacy

- Differential privacy for metrics
- Homomorphic encryption (research)
- Zero-knowledge proofs (research)

### v0.5.x: Privacy Dashboard

- Web UI for privacy management
- Visual privacy status
- Interactive data export
- Privacy settings GUI

### v1.0: Security Audit

- Third-party professional audit
- Penetration testing
- Privacy impact assessment
- Security certification (ISO 27001, SOC 2)
- Bug bounty programme

**See:** [Future Enhancements](./privacy-architecture.md#future-enhancements)

---

## Related Documentation

### Security & Privacy
- [Security Policy](./policy.md) - Comprehensive security policy
- [Privacy Architecture](./privacy-architecture.md) - Technical privacy documentation

### Implementation Roadmaps
- [v0.2.10 Roadmap](../roadmap/version/v0.2/v0.2.10/) - Security Hardening
- [v0.2.11 Roadmap](../roadmap/version/v0.2/v0.2.11/) - Privacy Infrastructure
- [v0.3 README](../roadmap/version/v0.3/README.md) - How v0.3.x uses security foundation

### Development Documentation
- [Development README](../README.md) - Main development hub
- [Roadmap Documentation](../roadmap/) - Feature roadmaps
- [ADRs](../decisions/adrs/) - Architecture decision records

---

## Contributing

### Security Contributions Welcome

We welcome contributions to improve ragged's security and privacy:

**Areas for contribution:**
- Security testing and auditing
- Privacy feature enhancements
- Documentation improvements
- Vulnerability reports (responsible disclosure)

**Before contributing:**
1. Read [Security Policy](./policy.md)
2. Review secure coding standards
3. Set up security development environment
4. Understand privacy-by-design principles

**Submit contributions:**
- Security fixes: Private security advisory first
- Enhancements: Public GitHub issue → PR
- Documentation: Direct PR with clear rationale

---

## Contact

**Security Issues:** Create private security advisory on GitHub

**General Security Questions:** Open public GitHub issue (non-sensitive)

**Project Maintainers:** See MAINTAINERS.md (root directory)

---

**License:** GPL-3.0

**Last Updated:** 2025-11-19

**Maintained By:** ragged security team
