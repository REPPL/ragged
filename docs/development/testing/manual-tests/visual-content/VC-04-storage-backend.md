# Test: Storage Backend Validation

**Category:** visual-content
**Test ID:** VC-04
**Date Executed:** [TBD]
**Tester:** Claude Code
**Environment:** macOS 14.x (Apple Silicon)

---

## Objective

Validate the dual storage architecture (DualEmbeddingStore) correctly manages separate text and vision embeddings.

---

## Prerequisites

- [ ] Documents ingested with vision embeddings
- [ ] Both text and vision embeddings present
- [ ] Storage commands available

---

## Test Procedure

### Step 1: View storage information

**Command:**
```bash
ragged storage info
```

**Expected Result:**
- Shows text collection statistics
- Shows vision collection statistics
- Displays total documents
- Shows embedding counts for both types

**Actual Result:**
[To be filled]

**Status:** ⏳ Pending

---

### Step 2: Verify separate collections

**Command:**
```bash
ragged storage info --format json | python3 -m json.tool
```

**Expected Result:**
- JSON shows `text_collection` object
- JSON shows `vision_collection` object
- Collections have different IDs/names
- Counts match between text and vision

**Actual Result:**
[To be filled]

**Status:** ⏳ Pending

---

### Step 3: Test storage vacuum operation

**Command:**
```bash
ragged storage vacuum
```

**Expected Result:**
- Cleans up unused embeddings
- Reports space reclaimed
- Both collections optimised
- No data loss

**Actual Result:**
[To be filled]

**Status:** ⏳ Pending

---

### Step 4: Verify data integrity after vacuum

**Command:**
```bash
ragged storage info
```

**Expected Result:**
- Embedding counts same or reduced (if orphans removed)
- Document count unchanged
- Storage healthy

**Actual Result:**
[To be filled]

**Status:** ⏳ Pending

---

## Verification

### Visual Inspection
- [ ] Separate collections clearly identified
- [ ] Statistics accurate and consistent
- [ ] Vacuum operation successful

### Quantitative Checks
- [ ] text_embeddings_count > 0
- [ ] vision_embeddings_count > 0
- [ ] document_count matches expected
- [ ] Collections independent (can query separately)

---

## Issues Encountered

| Issue | Severity | Description | Resolution |
|-------|----------|-------------|------------|
| - | - | - | - |

---

## Summary

**Overall Status:** ⏳ Not yet executed

**Key Findings:**
- [To be filled]

**Recommendations:**
- [To be filled]

---

## Related Documentation


---

## Metadata

- **Test Duration:** [X minutes]
- **Sample Data Used:** Documents from VC-01/VC-02
- **Models Used:** N/A (storage validation only)
- **Hardware:** Any
