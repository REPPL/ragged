# Testing Documentation

This directory contains comprehensive test reports and testing-related documentation for the ragged project.

## Contents

### Test Reports

- **`v0.2.x-test-report.md`** - Comprehensive test report for v0.2.10 (Security Hardening) and v0.2.11 (Privacy Infrastructure)
  - 156 tests across 69 new + 87 existing tests
  - Bug fixes and final 98.7% pass rate
  - Code coverage analysis
  - Security and privacy feature verification

### Purpose

This directory serves as the central location for:

1. **Cross-version test reports** - Reports covering multiple versions (e.g., v0.2.10 + v0.2.11)
2. **Test strategy documentation** - Testing approaches and methodologies
3. **Test suite documentation** - Organisation and structure of test suites
4. **Quality assurance records** - Test results, coverage reports, bug findings

## What Belongs Here

✅ **Include:**
- Comprehensive test reports for released versions
- Cross-version testing documentation
- Test strategy and methodology documents
- Coverage analysis and quality metrics
- Bug discovery and resolution records

❌ **Exclude:**
- Individual test files (belong in `tests/` directory)
- Version-specific implementation details (belong in `docs/development/implementation/version/`)
- Planning documents (belong in `docs/development/planning/`)

## Related Documentation

- [Development Process](../process/) - Development methodology and devlogs
- [Implementation Records](../implementation/) - What was actually built per version
- [Roadmap](../roadmap/) - Planned features and implementation details

---

**Note:** Test reports in this directory focus on **testing activities and quality assurance**, not implementation details. For implementation documentation, see `docs/development/implementation/version/`.
