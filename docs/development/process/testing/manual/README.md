# Manual Testing Documentation

**Purpose:** Documentation for manual testing procedures, test plans, and verification checklists for ragged.

**Location:** `docs/development/process/testing/manual/` (documentation) + `scripts/manual_tests/` (executable tests)

---

## Overview

This directory contains **test plans and scenarios** for manual testing of ragged. The actual **executable test scripts** are located in `scripts/manual_tests/`.

---

## Directory Structure

```
manual/
├── README.md                       # This file
├── v0.2/                           # v0.2 series manual test plans
│   ├── README.md
│   ├── v0.2.4-manual-tests.md
│   ├── v0.2.5-manual-tests.md
│   ├── v0.2.7-manual-tests.md
│   ├── v0.2.8-manual-tests.md
│   ├── v0.2.9-manual-tests.md
│   ├── v0.2.10-manual-tests.md     # Planned
│   └── v0.2.11-manual-tests.md     # Planned
├── v0.3/                           # v0.3 series (future)
│   └── README.md
└── templates/
    └── version-manual-test-template.md
```

---

## What Belongs Here

✅ **Manual test plans** - Detailed test scenarios for each version
✅ **Verification checklists** - Step-by-step validation procedures
✅ **Feature matrices** - Features tested + pytest markers
✅ **Test scenarios** - Interactive test procedures
✅ **Known issues** - Documented limitations per version

❌ **Executable tests** - Use `scripts/manual_tests/` directory
❌ **Automated tests** - Use `tests/` directory
❌ **Performance benchmarks** - Use `scripts/manual_tests/performance/`

---

## Manual Test Plan Structure

Each version's manual test plan (`vX.X.X-manual-tests.md`) includes:

### 1. Test Plan Overview
- Version information
- Status (planned/in-progress/completed)
- Features being tested
- Estimated testing time
- Prerequisites

### 2. Feature Matrix
Table mapping features to pytest markers:
```markdown
| Feature | pytest Marker | Tests | Status |
|---------|--------------|-------|--------|
| CLI Enhancements | @pytest.mark.feature("cli") | 10 | ✅ COMPLETE |
```

### 3. Test Scenarios
Interactive step-by-step test procedures:
```markdown
### Scenario: Document Ingestion

**Steps:**
1. Start ragged
2. Add document: `ragged add sample.pdf`
3. Verify document appears: `ragged list`

**Expected Results:**
- Document added successfully
- Appears in document list
- No errors

**Actual Results:** [Fill in during testing]
```

### 4. Verification Checklist
Manual validation checklist:
```markdown
- [ ] All features work as expected
- [ ] Error messages are clear
- [ ] Performance is acceptable
- [ ] Documentation is accurate
```

### 5. Known Issues
Documented limitations and bugs:
```markdown
- Issue #123: Shell completion fails on zsh < 5.8
- Limitation: Folder ingestion doesn't support symlinks
```

### 6. Links
Cross-references to:
- Roadmap document (feature specifications)
- Implementation record (what was built)
- Executable tests (`scripts/manual_tests/version/vX.X/`)

---

## Integration with Executable Tests

### From Documentation → Scripts

Each manual test plan links to executable tests:
```markdown
## Executable Tests

Run automated tests for this version:
```bash
pytest scripts/manual_tests/version/v0.2.9/
```

See: [Executable Tests](../../../../../scripts/manual_tests/version/v0.2.9/)
```

### From Scripts → Documentation

Each version test directory links to test plan:
```markdown
## Test Plan

Detailed test scenarios and checklists:
- [v0.2.9 Manual Test Plan](../../../docs/development/process/testing/manual/v0.2/v0.2.9-manual-tests.md)
```

---

## Creating Manual Test Plans for New Versions

### 1. Use Template

```bash
cp docs/development/process/testing/manual/templates/version-manual-test-template.md \
   docs/development/process/testing/manual/v0.2/v0.2.12-manual-tests.md
```

### 2. Fill In Placeholders

Replace:
- `{VERSION}` → `v0.2.12`
- `{DATE}` → Current date
- `{FEATURES}` → List of features
- `{FEATURE_MATRIX}` → Feature table
- `{ROADMAP_LINK}` → Link to roadmap
- `{TEST_SCRIPTS_PATH}` → Link to test scripts

### 3. Add Test Scenarios

Write interactive test scenarios for each feature:
- Clear steps
- Expected results
- Space for actual results
- Success criteria

### 4. Create Verification Checklist

List all validation points:
- Functional requirements
- Non-functional requirements (performance, usability)
- Documentation accuracy
- Error handling

### 5. Link to Roadmap and Implementation

Add cross-references:
- Roadmap: Feature specifications
- Implementation: What was actually built
- Test scripts: Automated tests

---

## Test Execution Workflow

### 1. Pre-Testing

- [ ] Review roadmap for version
- [ ] Read implementation notes
- [ ] Set up test environment
- [ ] Ensure services available (Ollama, ChromaDB)

### 2. Automated Testing

```bash
# Run smoke tests
pytest scripts/manual_tests/version/v0.2.X/ -m smoke

# Run all automated tests for version
pytest scripts/manual_tests/version/v0.2.X/
```

### 3. Manual Testing

- Open manual test plan
- Follow test scenarios step-by-step
- Document actual results
- Mark checklist items
- Note any issues

### 4. Post-Testing

- [ ] Document results in test plan
- [ ] Create GitHub issues for failures
- [ ] Update implementation docs with test results
- [ ] Generate test report

---

## Version Status

| Version | Status | Manual Test Plan | Automated Tests | Last Updated |
|---------|--------|------------------|-----------------|--------------|
| v0.2.4 | ✅ COMPLETE | TBD | smoke_test.py | TBD |
| v0.2.5 | ✅ COMPLETE | TBD | smoke_test.py, quality_improvements_test.py | TBD |
| v0.2.7 | ✅ COMPLETE | TBD | smoke_test.py, folder_ingestion_test.py | TBD |
| v0.2.8 | ✅ COMPLETE | TBD | smoke_test.py, cli_commands_test.py, formatters_test.py | TBD |
| v0.2.9 | ✅ COMPLETE | TBD | smoke_test.py, performance_optimisation_test.py | TBD |
| v0.2.10 | 📅 PLANNED | TBD | README.md (placeholder) | TBD |
| v0.2.11 | 📅 PLANNED | TBD | README.md (placeholder) | TBD |

---

## Related Documentation

- [Test Scripts](../../../../../scripts/manual_tests/README.md) - Executable tests
- [Testing Strategy](../README.md) - Overall testing approach
- [Roadmap](../../../roadmap/README.md) - Feature planning
- [Implementation](../../../implementation/README.md) - What was built
- [Version Tests](../../../../../scripts/manual_tests/version/README.md) - Version-specific tests

---

