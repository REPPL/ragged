# ragged v0.2.x Roadmap

**Version Series:** v0.2 - Enhanced RAG with Multi-Modal Support

**Status:** Completed (v0.2.1 through v0.2.9), Foundation Extended (v0.2.10-v0.2.11)

**Last Updated:** 2025-11-19

---

## Overview

The v0.2 series enhanced ragged with multi-modal document processing, performance optimisations, and comprehensive UX improvements. The series concluded with critical security and privacy infrastructure (v0.2.10-v0.2.11) that establishes the foundation for all future versions.

**Total Series Effort:** 245-291 hours across 11 releases

**Timeline:** Completed over multiple months (v0.2.1-v0.2.9), with security foundation added (v0.2.10-v0.2.11)

---

## Version Overview

### Core Feature Releases (v0.2.1 - v0.2.9)

| Version | Focus Area | Status | Key Features |
|---------|-----------|--------|--------------|
| [v0.2.3](./v0.2.3.md) | Foundation | ✅ Completed | Core enhancements |
| [v0.2.4](./v0.2.4.md) | Stability | ✅ Completed | Bug fixes, stability |
| [v0.2.5](./v0.2.5.md) | Performance | ✅ Completed | Performance optimisations |
| [v0.2.6](./v0.2.6/) | Refactoring | ✅ Completed | File structure refactoring |
| [v0.2.7](./v0.2.7/) | CLI Enhancements | ✅ Completed | Configuration, UX improvements |
| [v0.2.8](./v0.2.8.md) | Stability | ✅ Completed | Bug fixes, release prep |
| [v0.2.9](./v0.2.9/) | Production Ready | ✅ Completed | Multi-modal, quality, performance |

### Security & Privacy Foundation (v0.2.10 - v0.2.11)

**⚠️ CRITICAL:** These versions establish the security and privacy infrastructure required for ALL future versions (v0.3.x+).

| Version | Focus Area | Status | Time Estimate | Priority |
|---------|-----------|--------|---------------|----------|
| [v0.2.10](./v0.2.10/) | Security Hardening | 📋 Planned | 15-21 hours | **CRITICAL** |
| [v0.2.11](./v0.2.11/) | Privacy Infrastructure | 📋 Planned | 20-26 hours | **CRITICAL** |

**Why Critical:**

v0.2.10 and v0.2.11 must be completed BEFORE implementing v0.3.x features because:
- v0.3.9 (REPL) stores command history (PII risk)
- v0.3.10 (Metrics DB) stores query logs (privacy risk)
- v0.3.13 (REST API) handles multi-user sessions (cross-user leakage risk)

Without this foundation:
- ❌ Pickle arbitrary code execution vulnerability
- ❌ Cross-user data leakage (global caches)
- ❌ PII stored in plaintext
- ❌ GDPR non-compliance

---

## v0.2.10: Security Hardening

**Estimated Time:** 15-21 hours

**Purpose:** Eliminate critical security vulnerabilities before implementing data-handling features.

### Key Features

**FEAT-SEC-001: Replace Pickle with JSON (4-6h)**
- Eliminate arbitrary code execution vulnerability
- Migrate BM25 checkpoints to JSON serialisation
- Zero breaking changes (transparent migration)

**FEAT-SEC-002: Session Isolation (3-4h)**
- UUID-based session IDs
- Session-scoped caching (prevents cross-user leakage)
- SessionManager and Session classes

**FEAT-SEC-003: Security Testing Framework (3-4h)**
- Pre-commit hooks (detect-secrets, bandit, safety)
- Security test suite
- Automated vulnerability scanning

**FEAT-SEC-004: Security Audit & Documentation (2-3h)**
- Security policy documentation
- Secure coding standards
- Incident response procedures

### Success Criteria

- [ ] Zero Pickle usage in codebase
- [ ] All caches session-scoped
- [ ] Pre-commit hooks functional
- [ ] Security tests passing
- [ ] Documentation complete

**[→ Full v0.2.10 Roadmap](./v0.2.10/)**

---

## v0.2.11: Privacy Infrastructure

**Estimated Time:** 20-26 hours

**Purpose:** Establish privacy-by-design infrastructure for GDPR compliance and user data protection.

### Key Features

**FEAT-PRIV-001: Encryption at Rest (4-5h)**
- Fernet (AES-128) encryption for sensitive data
- Secure key management
- File permissions enforcement (0o600)

**FEAT-PRIV-002: PII Detection & Redaction (3-4h)**
- Regex-based PII detection (email, phone, SSN, etc.)
- Query hashing (SHA-256) for logs/metrics
- PII warnings to users

**FEAT-PRIV-003: Data Lifecycle Management (4-5h)**
- TTL-based automatic cleanup
- CleanupScheduler for expired data
- Configurable retention periods

**FEAT-PRIV-004: GDPR Compliance Foundations (3-4h)**
- Right to access (data export)
- Right to erasure (complete deletion)
- Right to portability (JSON export)
- Privacy status commands

**FEAT-PRIV-005: Privacy Configuration (2-3h)**
- User-configurable privacy settings
- Privacy profiles (maximum, balanced, minimal)
- Transparency and control

### Success Criteria

- [ ] All sensitive data encrypted at rest
- [ ] PII detection functional (100+ test cases)
- [ ] TTL cleanup operational
- [ ] GDPR deletion complete (all data removed)
- [ ] GDPR export complete (all data returned)
- [ ] Privacy configuration working

**[→ Full v0.2.11 Roadmap](./v0.2.11/)**

---

## Combined Impact

### Security & Privacy Foundation

**Total Time:** 35-47 hours (one-time investment)

**Protects:** All v0.3.x+ features that handle user data

**Compliance:** GDPR, OWASP Top 10, CWE Top 25

### Integration with v0.3.x

All v0.3.x features integrate with this foundation:

| v0.3 Feature | v0.2.10 Usage | v0.2.11 Usage |
|--------------|---------------|---------------|
| **v0.3.9 REPL** | Session isolation | Encrypted sessions, PII warnings |
| **v0.3.10 Metrics** | Session-scoped DB | Query hashing, TTL cleanup |
| **v0.3.13 REST API** | Per-client sessions | Session isolation, audit logs |

**Privacy Risk Scores:**
- v0.3.9 (REPL): 90/100
- v0.3.10 (Metrics): 95/100
- v0.3.13 (REST API): 92/100

---

## Implementation Order

**Strict Sequential Order Required:**

```
v0.2.10 (Security) → v0.2.11 (Privacy) → v0.3.1 (First v0.3 Feature)
```

**Why Sequential:**
- v0.2.11 depends on v0.2.10 (uses Session class)
- v0.3.x depends on both v0.2.10 and v0.2.11
- Breaking this order creates security vulnerabilities

---

## Quality Gates

### For v0.2.10 (Security)
- [ ] No Pickle usage anywhere in codebase
- [ ] All caches session-scoped
- [ ] Security tests passing (100% coverage for security controls)
- [ ] Pre-commit hooks functional
- [ ] Security documentation complete
- [ ] British English compliance

### For v0.2.11 (Privacy)
- [ ] All sensitive data encrypted
- [ ] PII detection tested (100+ test cases)
- [ ] TTL cleanup functional (automated tests)
- [ ] GDPR deletion tested (all data removed)
- [ ] GDPR export tested (complete data returned)
- [ ] Privacy documentation complete
- [ ] British English compliance

---

## Documentation

### Security & Privacy Documentation

**Core Documents:**
- [Security Policy](../../../security/policy.md) - Comprehensive security policy
- [Privacy Architecture](../../../security/privacy-architecture.md) - Technical privacy documentation
- [Security README](../../../security/README.md) - Security documentation hub

**Roadmap Documents:**
- [v0.2.10 Roadmap](./v0.2.10/) - Security Hardening implementation plan
- [v0.2.11 Roadmap](./v0.2.11/) - Privacy Infrastructure implementation plan

### Implementation Records

After completing each version, document in:
- `docs/development/implementation/version/v0.2/v0.2.10/` or `v0.2.10.md`
- `docs/development/implementation/version/v0.2/v0.2.11/` or `v0.2.11.md`

---

## Related Documentation

### Security & Privacy
- [Security Policy](../../../security/policy.md)
- [Privacy Architecture](../../../security/privacy-architecture.md)
- [Security README](../../../security/README.md)

### Planning Documentation
- [v0.2 Planning](../../../planning/version/v0.2/) - Design goals and requirements

### Next Version
- [v0.3 Roadmap](../v0.3/README.md) - Production-Ready RAG (depends on v0.2.10/v0.2.11)

### Implementation Records
- [v0.2 Implementation](../../../implementation/version/v0.2/) - Completed work

---
