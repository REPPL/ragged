# Audit Reports

This directory contains all audit reports for the ragged project, including security assessments, documentation quality audits, and planning/roadmap reviews.

## Directory Structure

```
audit/
├── security/          # Security audits and assessments
│   ├── baseline/      # Baseline security audits
│   └── implementation/ # Implementation verification audits
├── documentation/     # Documentation quality audits
└── roadmap/          # Planning and roadmap audits
```

## Audit Types

### Security Audits

Security audits assess vulnerabilities, security posture, and compliance with security best practices.

**Baseline Audits** (`security/baseline/`):
- Comprehensive security assessments establishing baseline security posture
- Vulnerability identification and risk assessment
- Examples: v0.5.7 baseline audit, pre-v0.2.10 baseline

**Implementation Audits** (`security/implementation/`):
- Verification that security fixes were properly implemented
- Post-implementation security validation
- Examples: v0.5.8 implementation verification

**Ongoing Audits** (`security/`):
- Regular security reviews and assessments
- Dated audit reports (YYYY-MM-DD-security-audit.md)

### Documentation Audits

Documentation audits assess documentation quality, coverage, accuracy, and adherence to standards.

**Types:**
- Quality audits (structure, completeness, accuracy)
- Metadata audits (cross-references, lineage tracking)
- Version-specific audits (pre-release documentation review)

### Roadmap Audits

Roadmap audits review planning documentation, task organisation, and version roadmaps for completeness and feasibility.

**Current Audits:**
- [Feature-Centric Restructuring Plan](./roadmap/2025-11-25-restructuring-plan.md) - Migration from version-centric to feature-centric roadmap structure

## Relationship to Other Documentation

- **User Guides** (`docs/guides/`): How to *use* security features
- **Audit Reports** (`docs/audit/`): Security *assessments* and quality reviews
- **Implementation** (`docs/development/implementation/`): What was *built*
- **Security Policies** (`docs/security/`): Security policies and architecture

## Conducting Audits

### Security Audits

For guidance on conducting security audits, see:
- [Security Monitoring Guide](../guides/security-monitoring.md) - Operational monitoring procedures
- [Security Policy](../security/policy.md) - Security policies and procedures
- [Baseline README](./security/baseline/README.md) - Baseline audit procedures
- [Implementation README](./security/implementation/README.md) - Implementation audit procedures

### Documentation Audits

Documentation audits use the `documentation-auditor` agent:
```bash
# Run comprehensive documentation audit
/verify-docs
```


### Roadmap Audits

Roadmap audits review:
- Feature completeness and feasibility
- Time estimates and dependencies
- Alignment with project goals
- Risks and mitigation strategies

---

## Navigation Guide

### Finding Specific Audits

**By Type:**
- Security baseline audits: [`security/baseline/`](./security/baseline/)
- Security implementation audits: [`security/implementation/`](./security/implementation/)
- Documentation audits: [`documentation/`](./documentation/)
- Roadmap audits: [`roadmap/`](./roadmap/)

**By Date:**
Most audit files are named with dates (YYYY-MM-DD format) for easy chronological navigation:
```bash
# Find all audits from November 2025
ls -l */2025-11-*.md

# Find security audits from a specific date
ls -l security/*/2025-11-23*.md
```

**By Version:**
Security baseline audits are organised by version milestone:
```bash
ls -l security/baseline/v*.md
```

---

## Audit File Naming Conventions

- **Security baseline:** `vX.X.X-security-audit.md` (e.g., `v0.5.7-security-audit.md`)
- **Security implementation:** `vX.X.X-security-audit.md` in `security/implementation/`
- **Documentation audits:** `YYYY-MM-DD-description.md` (e.g., `2025-11-23-quality-audit.md`)
- **Roadmap audits:** `YYYY-MM-DD-description.md` (e.g., `2025-11-22-v0.6-roadmap-audit.md`)

---

## Related Documentation

- [Implementation Documentation](../development/implementation/) - What was built
- [Roadmap Documentation](../development/roadmap/) - What will be built
- [Feature-Centric Roadmap Standard](../development/process/methodology/feature-centric-roadmaps.md) - Target methodology for roadmaps
- [Security Guides](../guides/) - How to use security features
- [Testing Documentation](../testing/) - Test procedures and manual tests
