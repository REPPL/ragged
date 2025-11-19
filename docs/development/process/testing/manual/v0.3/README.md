# v0.3 Series Manual Test Plans

**Purpose:** Manual test documentation for ragged v0.3 series (planned).

**Status:** 📅 PLANNED - v0.3 series not yet implemented

---

## Overview

This directory will contain detailed test plans, verification checklists, and test scenarios for each minor release in the v0.3 series once implementation begins.

---

## Planned v0.3 Releases

Based on current roadmap:

| Version | Status | Planned Features | Hours Estimate |
|---------|--------|------------------|----------------|
| v0.3.1 | 📅 PLANNED | Contextual chunking, session context, advanced retrieval | 35-41h |
| v0.3.2 | 📅 PLANNED | RAGAS evaluation framework | 30-36h |
| v0.3.3 | 📅 PLANNED | Gradio UI enhancements | 25-30h |
| v0.3.4 | 📅 PLANNED | Ollama model manager | 20-25h |
| v0.3.5 | 📅 PLANNED | Advanced CLI features | 25-30h |
| v0.3.6 | 📅 PLANNED | ColPali multimodal prep | 20-25h |
| v0.3.7 | 📅 PLANNED | Synthetic data generation | 30-36h |
| v0.3.8 | 📅 PLANNED | Performance profiling | 25-30h |
| v0.3.9 | 📅 PLANNED | Documentation & tutorials | 30-36h |
| v0.3.10 | 📅 PLANNED | Automated testing expansion | 35-41h |
| v0.3.11 | 📅 PLANNED | Cross-platform validation | 30-36h |
| v0.3.12 | 📅 PLANNED | Integration testing | 35-41h |
| v0.3.13 | 📅 PLANNED | Production readiness review | 37-44h |

**Total v0.3 Series:** 437-501 hours

---

## Prerequisite Versions

Before v0.3.1 can begin, these versions must be complete:
- ✅ v0.2.9 - Performance optimisation
- 📅 v0.2.10 - Security foundation
- 📅 v0.2.11 - Privacy infrastructure

---

## When v0.3 Implementation Begins

### 1. Create Test Plans

For each v0.3.X version:
```bash
cp ../templates/version-manual-test-template.md ./v0.3.X-manual-tests.md
```

### 2. Create Test Scripts

```bash
./scripts/manual_tests/templates/create_version_tests.sh v0.3.X "feature1,feature2"
```

### 3. Update This README

- Add version to detailed table
- Document test execution results
- Link to test plans and scripts

---

## Related Documentation

- [Manual Testing README](../README.md) - Manual testing overview
- [v0.3 Roadmap](../../../../roadmap/version/v0.3/README.md) - v0.3 series planning
- [Executable Tests](../../../../../../scripts/manual_tests/version/README.md) - Version test scripts

---

