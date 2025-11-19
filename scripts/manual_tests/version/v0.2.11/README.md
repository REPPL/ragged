# v0.2.11 Manual Tests

**Status:** 📅 PLANNED
**Features:** Privacy infrastructure (encryption at rest, PII detection, query hashing, TTL lifecycle)
**Date Created:** 2025-11-19

---

## Overview

This directory will contain manual tests for ragged v0.2.11, focusing on privacy infrastructure and GDPR compliance foundations.

**Note:** v0.2.11 is currently in planning phase. Tests will be implemented once development begins.

---

## Planned Features

- **Encryption at Rest** - Fernet/AES-128 encryption for stored data
- **PII Detection & Redaction** - Automatic detection and redaction of personally identifiable information
- **Query Hashing** - SHA-256 hashing for query privacy
- **TTL-Based Lifecycle** - Time-to-live for automatic data expiry
- **GDPR Compliance** - Foundations for data privacy regulations

**Hours Estimate:** 20-26h

---

## Prerequisites

- v0.2.10 (Security Foundation) must be complete
- v0.2.11 is a **prerequisite** for v0.3.1 and beyond

---

## Test Files (Planned)

- `smoke_test.py` - Quick privacy validation
- `encryption_test.py` - Data encryption verification
- `pii_detection_test.py` - PII detection and redaction tests
- `query_hashing_test.py` - Query privacy tests
- `ttl_lifecycle_test.py` - Data expiry tests
- `gdpr_compliance_test.py` - GDPR compliance validation

---

## When Implementation Begins

1. Use automation script:
   ```bash
   ./scripts/manual_tests/templates/create_version_tests.sh v0.2.11 "privacy,encryption,pii_detection,gdpr"
   ```

2. Implement test files
3. Create manual test plan in `docs/development/process/testing/manual/v0.2/v0.2.11-manual-tests.md`
4. Update this README with actual features and test details

---

## Privacy Testing Considerations

- Test with realistic PII data (but use synthetic/test data only)
- Verify encryption keys are properly managed
- Validate secure deletion of expired data
- Test GDPR right-to-be-forgotten workflows
- Ensure no data leakage in logs or error messages

---

## Related Documentation

- [v0.2.11 Roadmap](../../../docs/development/roadmap/version/v0.2/v0.2.11/)
- [v0.2 Implementation](../../../docs/development/implementation/version/v0.2/README.md)

---

**Maintained By:** ragged development team
