# v0.2 Series Manual Test Plans

**Purpose:** Manual test documentation for ragged v0.2 series (v0.2.4 through v0.2.11).

---

## Overview

This directory contains detailed test plans, verification checklists, and test scenarios for each minor release in the v0.2 series.

---

## Test Plans

| Version | Status | Features | Test Plan |
|---------|--------|----------|-----------|
| v0.2.4 | ✅ COMPLETE | Base functionality | [v0.2.4 Manual Tests](./v0.2.4-manual-tests.md) |
| v0.2.5 | ✅ COMPLETE | Quality improvements | [v0.2.5 Manual Tests](./v0.2.5-manual-tests.md) |
| v0.2.7 | ✅ COMPLETE | CLI refactoring, folder ingestion | [v0.2.7 Manual Tests](./v0.2.7-manual-tests.md) |
| v0.2.8 | ✅ COMPLETE | CLI enhancements, formatters | [v0.2.8 Manual Tests](./v0.2.8-manual-tests.md) |
| v0.2.9 | ✅ COMPLETE | Performance optimisation | [v0.2.9 Manual Tests](./v0.2.9-manual-tests.md) |
| v0.2.10 | 📅 PLANNED | Security foundation | [v0.2.10 Manual Tests](./v0.2.10-manual-tests.md) |
| v0.2.11 | 📅 PLANNED | Privacy infrastructure | [v0.2.11 Manual Tests](./v0.2.11-manual-tests.md) |

---

## Version Highlights

### v0.2.4 - Base Version
- Core document ingestion
- Basic CLI commands
- Vector search
- Foundation for future features

### v0.2.5 - Quality Improvements
- Settings refactoring (no global state)
- Improved error handling
- Type safety (mypy --strict)
- Code quality enhancements

### v0.2.7 - CLI Refactoring
- Modular CLI architecture (14 commands)
- Folder ingestion (recursive scanning)
- Enhanced HTML processing
- Improved testability

### v0.2.8 - CLI Enhancements
- 10 new CLI commands
- Output formatters (JSON/table/CSV/YAML)
- Shell completion (bash/zsh/fish)
- Configuration validation
- Environment diagnostics

### v0.2.9 - Performance Optimisation
- Batch tuning optimisation
- Cold start optimisation
- Test coverage expansion (70%+)
- Chunking improvements
- Performance regression testing

### v0.2.10 - Security Foundation (Planned)
- JSON serialisation (eliminate Pickle)
- Session isolation (UUID-based)
- Session-scoped caching
- Security audit compliance

### v0.2.11 - Privacy Infrastructure (Planned)
- Encryption at rest (Fernet/AES-128)
- PII detection and redaction
- Query hashing (SHA-256)
- TTL-based data lifecycle
- GDPR compliance foundations

---

## How to Use Test Plans

### 1. Select Version

Choose the version you want to test and open its test plan markdown file.

### 2. Review Prerequisites

Each test plan specifies:
- Required services (Ollama, ChromaDB)
- Configuration requirements
- Test environment setup

### 3. Run Automated Tests

Before manual testing, run automated tests:
```bash
pytest scripts/manual_tests/version/vX.X.X/
```

### 4. Execute Manual Test Scenarios

Follow step-by-step test scenarios in the test plan:
- Read scenario description
- Execute steps
- Document actual results
- Compare with expected results

### 5. Complete Verification Checklist

Mark checklist items as you validate:
- [ ] Functional requirements
- [ ] Performance requirements
- [ ] Error handling
- [ ] Documentation accuracy

### 6. Document Results

Update test plan with:
- Actual results
- Issues found
- GitHub issue numbers
- Test completion date

---

## Creating New Test Plans

When a new v0.2.X version is ready:

1. **Copy template:**
   ```bash
   cp ../templates/version-manual-test-template.md ./v0.2.X-manual-tests.md
   ```

2. **Fill in placeholders:**
   - Version number
   - Features being tested
   - Feature matrix
   - Test scenarios

3. **Link to roadmap and implementation:**
   - Roadmap: `docs/development/roadmap/version/v0.2/v0.2.X/`
   - Implementation: `docs/development/implementation/version/v0.2/v0.2.X.md`
   - Test scripts: `scripts/manual_tests/version/v0.2.X/`

4. **Update this README:**
   - Add version to table
   - Add version highlights
   - Update status

---

## Test Execution Timeline

| Version | Planned Testing | Actual Testing | Duration | Issues Found |
|---------|----------------|----------------|----------|--------------|
| v0.2.4 | TBD | TBD | TBD | TBD |
| v0.2.5 | TBD | TBD | TBD | TBD |
| v0.2.7 | TBD | TBD | TBD | TBD |
| v0.2.8 | TBD | TBD | TBD | TBD |
| v0.2.9 | TBD | TBD | TBD | TBD |

---

## Related Documentation

- [Manual Testing README](../README.md) - Manual testing overview
- [Executable Tests](../../../../../../scripts/manual_tests/version/README.md) - Version test scripts
- [v0.2 Roadmap](../../../../roadmap/version/v0.2/README.md) - v0.2 series planning
- [v0.2 Implementation](../../../../implementation/version/v0.2/README.md) - What was built

---

