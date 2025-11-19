# v0.2.10 Manual Tests

**Status:** 📅 PLANNED
**Features:** Security foundation (JSON serialisation, session isolation, session-scoped caching)
**Date Created:** 2025-11-19

---

## Overview

This directory will contain manual tests for ragged v0.2.10, focusing on security foundation improvements.

**Note:** v0.2.10 is currently in planning phase. Tests will be implemented once development begins.

---

## Planned Features

- **JSON Serialisation** - Replace Pickle with JSON (eliminate security vulnerability)
- **Session Isolation** - UUID-based session management
- **Session-Scoped Caching** - Isolated cache per session
- **Security Audit** - Comprehensive security review

**Hours Estimate:** 15-21h

---

## Prerequisites

v0.2.10 is a **prerequisite** for v0.3.1 and beyond. All security foundations must be in place before advancing to v0.3.

---

## Test Files (Planned)

- `smoke_test.py` - Quick security validation
- `json_serialisation_test.py` - Pickle elimination verification
- `session_isolation_test.py` - Session management tests
- `session_cache_test.py` - Scoped caching tests

---

## When Implementation Begins

1. Use automation script:
   ```bash
   ./scripts/manual_tests/templates/create_version_tests.sh v0.2.10 "security,serialisation,session_isolation"
   ```

2. Implement test files
3. Create manual test plan in `docs/development/process/testing/manual/v0.2/v0.2.10-manual-tests.md`
4. Update this README with actual features and test details

---

## Related Documentation

- [v0.2.10 Roadmap](../../../docs/development/roadmap/version/v0.2/v0.2.10/)
- [v0.2 Implementation](../../../docs/development/implementation/version/v0.2/README.md)

---

**Maintained By:** ragged development team
