# Testing Documentation

**Purpose:** Comprehensive testing documentation for ragged

---

## Overview

This directory contains all testing documentation for ragged, including manual test procedures, automated test guides, and testing standards. Testing ensures ragged's privacy-first RAG capabilities work reliably across platforms and configurations.

---

## Directory Structure

```
testing/
├── README.md           # This file
└── manual-tests/       # Manual test procedures and execution results
```

---

## Testing Approach

ragged uses a **dual testing strategy**:

### 1. Automated Tests

**Location:** `tests/` (project root)

**Purpose:** Fast, repeatable unit and integration tests

**Coverage:**
- Unit tests for individual components
- Integration tests for component interactions
- End-to-end workflow tests

**Execution:**
```bash
pytest                    # Run all tests
pytest --cov=src         # With coverage report
pytest -v tests/unit/    # Specific test suite
```

**Standards:**
- Minimum 70% overall coverage
- 80%+ for core functionality
- 100% for critical paths

### 2. Manual Tests

**Location:** `manual-tests/`

**Purpose:** Real-world workflow validation, visual inspection, cross-platform testing

**Categories:**
- Visual content ingestion (ColPali embeddings)
- Multi-modal query validation
- GPU detection and optimisation
- Cross-platform compatibility

**When to Use:**
- Before releases (full test pass)
- After significant refactoring
- When adding new features
- After fixing critical bugs

---

## What Belongs Here

**✅ Include:**
- Manual test procedures and templates
- Test execution results and evidence
- Testing standards and guidelines
- Cross-reference to automated tests

**❌ Don't Include:**
- Automated test code (goes in `tests/`)
- Sample data (goes in `examples/`)
- Performance benchmarks (goes in `docs/development/`)

---

## Quick Start

### Running Manual Tests

1. **Review available tests:**
   ```bash
   ls manual-tests/*/
   ```

2. **Select a test** from the appropriate category

3. **Follow test procedure** in the test document

4. **Document results** directly in the test file

See [Manual Tests README](./manual-tests/README.md) for detailed instructions.

### Running Automated Tests

1. **Install test dependencies:**
   ```bash
   pip install -e ".[dev]"
   ```

2. **Start required services:**
   ```bash
   docker-compose up -d chromadb
   ```

3. **Run tests:**
   ```bash
   pytest
   ```

See project `tests/README.md` for comprehensive test suite documentation.

---

## Testing Standards

### Manual Test Requirements

- **Documentation:** Clear prerequisites, exact commands, complete results
- **Evidence:** Output captures, screenshots, performance metrics
- **British English:** All test documentation uses British spelling
- **Status Indicators:** ✅ Pass, ❌ Fail, ⚠️ Partial

### Automated Test Requirements

- **Coverage:** Minimum 70% overall, 80%+ for core features
- **Speed:** Unit tests <1s each, integration tests <10s
- **Isolation:** No external dependencies (mock APIs, use fixtures)
- **Clarity:** Descriptive test names, clear assertions

---

## Test Maintenance

### Before Releases

- [ ] Run full automated test suite (pytest)
- [ ] Execute relevant manual tests
- [ ] Verify coverage meets standards
- [ ] Update test documentation

### After Bug Fixes

- [ ] Add regression test (automated)
- [ ] Re-run affected manual tests
- [ ] Update test status

### After New Features

- [ ] Create unit tests for components
- [ ] Create integration tests for workflows
- [ ] Create manual test if UI/UX involved
- [ ] Document in test README

---

## Related Documentation

- [Manual Test Procedures](./manual-tests/README.md) - Detailed manual testing guide
- [Automated Test Suite](../../tests/README.md) - Pytest test documentation
- [Contributing Guide](../../CONTRIBUTING.md) - How to contribute tests
- [Multi-Modal Tutorial](../tutorials/multimodal-workflow.md) - Testing multi-modal features

---

**Status**: Active
