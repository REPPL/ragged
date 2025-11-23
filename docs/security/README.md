# Security Documentation

Documentation for security audits, vulnerability assessments, and security best practices for the ragged project.

## Purpose

This directory contains security-related documentation including:
- Security audit reports
- Vulnerability assessments
- Dependency security scans
- Security best practices
- Incident response procedures (if applicable)

## What Belongs Here

- Security audit findings and reports
- Dependency vulnerability scans
- Security configuration guidelines
- Threat model documentation
- Security testing results
- Security-related ADRs (cross-reference from decisions/adrs/)

## What Doesn't Belong Here

- **Implementation details** → See `../development/implementation/`
- **Architecture decisions** → See `../development/decisions/adrs/` (primary location)
- **General development process** → See `../development/process/`
- **User-facing security guides** → See `../guides/security/` (if created)

## Security Standards

ragged follows these security principles:
1. **Privacy-first** - All processing local by default
2. **No telemetry** - No usage tracking or data collection
3. **Transparent dependencies** - Regular dependency audits
4. **Secure defaults** - Safe configuration out of the box
5. **GPL-3.0 compliance** - All dependencies compatible with license

## Related Documentation

- [Privacy Design](../explanation/privacy-design.md) - Privacy architecture
- [ADR-0001: Local-Only Processing](../development/decisions/adrs/0001-local-only-processing.md) - Privacy decision rationale
- [Contributing Security Issues](../../CONTRIBUTING.md#security-issues) - How to report vulnerabilities
