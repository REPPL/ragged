# Test: Batch PDF Ingestion with Vision Embeddings

**Category:** visual-content
**Test ID:** VC-02
**Date Executed:** 2025-11-23
**Tester:** Claude Code
**Environment:** macOS 14.x (Apple Silicon)

---

## Objective

Validate batch ingestion of multiple PDFs with vision embeddings in a single command.

---

## Prerequisites

- [ ] Sample data available: `examples/sample_documents/` (3 PDFs)
- [ ] ChromaDB running via docker-compose
- [ ] ColPali model already downloaded (from VC-01)
- [ ] Database cleared before test

---

## Test Procedure

### Step 1: Clear existing data

**Command:**
```bash
ragged clear --force
```

**Expected Result:**
- Database cleared successfully

**Actual Result:**
[To be filled]

**Status:** ⏳ Pending

---

### Step 2: Ingest all PDFs in batch

**Command:**
```bash
ragged ingest pdf examples/sample_documents/*.pdf --vision
```

**Expected Result:**
- All 3 PDFs ingested successfully
- Vision embeddings generated for each
- Progress shown for each document
- Total processing time displayed

**Actual Result:**
[To be filled]

**Status:** ⏳ Pending

---

### Step 3: Verify all documents ingested

**Command:**
```bash
ragged list
```

**Expected Result:**
- Three documents listed
- All show correct metadata

**Actual Result:**
[To be filled]

**Status:** ⏳ Pending

---

### Step 4: Check storage statistics

**Command:**
```bash
ragged storage info
```

**Expected Result:**
- Text embeddings count > 0 for all docs
- Vision embeddings count > 0 for all docs
- Total counts reflect all 3 documents

**Actual Result:**
[To be filled]

**Status:** ⏳ Pending

---

## Verification

### Visual Inspection
- [ ] All PDFs processed without errors
- [ ] Progress indicators for each document
- [ ] Success confirmation for batch

### Quantitative Checks
- [ ] Document count = 3
- [ ] Processing efficient (parallel if possible)
- [ ] No duplicate embeddings

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

- [Multi-Modal Workflow Tutorial](../../../tutorials/multimodal-workflow.md)
- [Batch Processing Guide](../../../guides/batch-processing.md)

---

## Metadata

- **Test Duration:** [X minutes]
- **Sample Data Used:** 3 PDFs (total ~1.8MB, 20 pages)
- **Models Used:** ColPali, nomic-embed-text
- **Hardware:** Apple Silicon (MPS backend)
