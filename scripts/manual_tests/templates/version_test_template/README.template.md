# {VERSION} Manual Tests

**Status:** {STATUS}
**Features:** {FEATURES}
**Date Created:** {DATE}

---

## Overview

This directory contains manual tests for ragged {VERSION}, focusing on new features and improvements introduced in this release.

---

## Features Tested

{FEATURE_LIST}

---

## Test Files

- `smoke_test.py` - Quick sanity check (5-10 minutes)
{FEATURE_TEST_FILES}

---

## Running Tests

### Run all tests for this version

```bash
pytest scripts/manual_tests/version/{VERSION}/
```

### Run smoke test only

```bash
pytest scripts/manual_tests/version/{VERSION}/smoke_test.py
```

### Run specific feature tests

```bash
pytest scripts/manual_tests/version/{VERSION}/ -m 'feature("{FEATURE_TAG}")'
```

---

## pytest Markers

All tests in this directory use these markers:

- `@pytest.mark.smoke` - Quick sanity checks
- `@pytest.mark.version("{VERSION}")` - Version-specific marker
{FEATURE_MARKERS}

---

## Related Documentation

- **Roadmap:** {ROADMAP_LINK}
- **Implementation:** {IMPLEMENTATION_LINK}
- **Manual Test Plan:** {MANUAL_TEST_PLAN_LINK}

---

**Maintained By:** ragged development team
