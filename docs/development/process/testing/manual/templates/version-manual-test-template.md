# {VERSION} Manual Test Plan

**Status:** {STATUS}
**Date Created:** {DATE}
**Features:** {FEATURES}
**Estimated Testing Time:** {ESTIMATED_TIME}

---

## Overview

Manual test plan for ragged {VERSION}, focusing on {FOCUS_AREAS}.

---

## Prerequisites

- [ ] ragged {VERSION} installed
- [ ] Ollama service running (http://localhost:11434)
- [ ] ChromaDB service running (http://localhost:8001)
- [ ] Test documents available
- [ ] Review roadmap: [{VERSION} Roadmap]({ROADMAP_LINK})
- [ ] Review implementation: [{VERSION} Implementation]({IMPLEMENTATION_LINK})

---

## Feature Matrix

| Feature | Description | pytest Marker | Test File | Status |
|---------|-------------|---------------|-----------|--------|
{FEATURE_MATRIX_ROWS}

**Legend:**
- ✅ COMPLETE - Feature tested and passing
- 🔄 IN PROGRESS - Testing underway
- 📅 PLANNED - Not yet tested
- ⏸️ BLOCKED - Blocked by dependencies

---

## Test Scenarios

### Scenario 1: {SCENARIO_NAME}

**Objective:** {SCENARIO_OBJECTIVE}

**Prerequisites:**
- {PREREQUISITE_1}
- {PREREQUISITE_2}

**Steps:**
1. {STEP_1}
2. {STEP_2}
3. {STEP_3}

**Expected Results:**
- {EXPECTED_RESULT_1}
- {EXPECTED_RESULT_2}

**Actual Results:** ____________________

**Status:** ☐ Pass ☐ Fail ☐ N/A

**Notes:** ____________________

---

### Scenario 2: {SCENARIO_NAME}

**Objective:** {SCENARIO_OBJECTIVE}

**Prerequisites:**
- {PREREQUISITE_1}

**Steps:**
1. {STEP_1}
2. {STEP_2}

**Expected Results:**
- {EXPECTED_RESULT_1}

**Actual Results:** ____________________

**Status:** ☐ Pass ☐ Fail ☐ N/A

**Notes:** ____________________

---

## Verification Checklist

### Functional Requirements

- [ ] All new features work as specified
- [ ] No regression in existing functionality
- [ ] Error handling is appropriate
- [ ] Edge cases handled correctly

### Non-Functional Requirements

- [ ] Performance meets requirements
- [ ] Memory usage is acceptable
- [ ] Response times are reasonable
- [ ] Resource cleanup works correctly

### User Experience

- [ ] CLI commands are intuitive
- [ ] Error messages are clear and actionable
- [ ] Help text is accurate
- [ ] Output formatting is readable

### Documentation

- [ ] README updated with new features
- [ ] CLI reference documentation accurate
- [ ] Examples work correctly
- [ ] Changelog entries complete

---

## Executable Tests

### Run Automated Tests

```bash
# Run all tests for this version
pytest {TEST_SCRIPTS_PATH}

# Run smoke tests only
pytest {TEST_SCRIPTS_PATH} -m smoke

# Run specific feature tests
pytest {TEST_SCRIPTS_PATH} -m 'feature("{FEATURE_TAG}")'
```

### Generate Test Report

```bash
pytest {TEST_SCRIPTS_PATH} \
  --html=scripts/manual_tests/reports/{VERSION}_test_report.html \
  --self-contained-html
```

---

## Performance Validation

### Expected Performance

| Metric | Target | Actual | Status |
|--------|--------|--------|--------|
| Ingestion (100 docs) | {TARGET_1} | ____ | ☐ Pass ☐ Fail |
| Query latency (p95) | {TARGET_2} | ____ | ☐ Pass ☐ Fail |
| First query (cold start) | {TARGET_3} | ____ | ☐ Pass ☐ Fail |
| Memory (baseline) | {TARGET_4} | ____ | ☐ Pass ☐ Fail |
| Memory (with 100 docs) | {TARGET_5} | ____ | ☐ Pass ☐ Fail |

### Performance Notes

____________________

---

## Known Issues

### Issue 1: {ISSUE_TITLE}

**Description:** {ISSUE_DESCRIPTION}

**Impact:** {IMPACT}

**Workaround:** {WORKAROUND}

**GitHub Issue:** #{ISSUE_NUMBER}

**Status:** ☐ Open ☐ In Progress ☐ Fixed

---

### Issue 2: {ISSUE_TITLE}

**Description:** {ISSUE_DESCRIPTION}

**Impact:** {IMPACT}

**Workaround:** {WORKAROUND}

**GitHub Issue:** #{ISSUE_NUMBER}

**Status:** ☐ Open ☐ In Progress ☐ Fixed

---

## Limitations

### Current Limitations

- {LIMITATION_1}
- {LIMITATION_2}

### Planned Improvements

- {PLANNED_IMPROVEMENT_1} (Target: v{FUTURE_VERSION})
- {PLANNED_IMPROVEMENT_2} (Target: v{FUTURE_VERSION})

---

## Test Execution Summary

**Test Execution Date:** ____________________

**Tester:** ____________________

**Environment:**
- OS: ____________________
- Python Version: ____________________
- ragged Version: ____________________

**Results:**
- Total Test Scenarios: ____
- Passed: ____
- Failed: ____
- Blocked: ____
- Pass Rate: ____%

**Overall Status:** ☐ PASS ☐ FAIL ☐ PARTIAL

---

## Issues Found During Testing

| Issue # | Description | Severity | Status | GitHub Issue |
|---------|-------------|----------|--------|--------------|
| 1 | | ☐ Critical ☐ High ☐ Medium ☐ Low | ☐ Open ☐ Fixed | # |
| 2 | | ☐ Critical ☐ High ☐ Medium ☐ Low | ☐ Open ☐ Fixed | # |
| 3 | | ☐ Critical ☐ High ☐ Medium ☐ Low | ☐ Open ☐ Fixed | # |

---

## Sign-Off

### Tester Approval

**Name:** ____________________
**Date:** ____________________
**Signature:** ____________________

**Recommendation:** ☐ Approve for release ☐ Approve with conditions ☐ Reject

**Conditions/Notes:** ____________________

---

## Related Documentation

- **Roadmap:** [{VERSION} Roadmap]({ROADMAP_LINK})
- **Implementation:** [{VERSION} Implementation]({IMPLEMENTATION_LINK})
- **Test Scripts:** [{VERSION} Test Scripts]({TEST_SCRIPTS_PATH})
- **Previous Version Tests:** [{PREVIOUS_VERSION} Manual Tests]({PREVIOUS_VERSION_LINK})

---

