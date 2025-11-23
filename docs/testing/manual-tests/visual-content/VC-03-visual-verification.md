# Test: Visual Content Verification

**Category:** visual-content
**Test ID:** VC-03
**Date Executed:** [TBD]
**Tester:** Claude Code
**Environment:** macOS 14.x (Apple Silicon)

---

## Objective

Verify that vision embeddings accurately capture and represent visual content from PDFs (diagrams, charts, tables).

---

## Prerequisites

- [ ] Documents ingested with vision embeddings (from VC-01 or VC-02)
- [ ] Storage backend showing vision embeddings
- [ ] Sample PDFs contain diverse visual content

---

## Test Procedure

### Step 1: Query for diagram-based content

**Command:**
```bash
ragged query vision "neural network architecture diagram" --limit 5
```

**Expected Result:**
- Results include pages with neural network diagrams
- Similarity scores reasonable (>0.5)
- Correct page numbers returned

**Actual Result:**
[To be filled]

**Status:** ⏳ Pending

---

### Step 2: Query for chart/graph content

**Command:**
```bash
ragged query vision "bar chart showing data comparison" --limit 5
```

**Expected Result:**
- Results include pages with charts/graphs
- Visual similarity detected correctly
- Pages without charts ranked lower

**Actual Result:**
[To be filled]

**Status:** ⏳ Pending

---

### Step 3: Query for table content

**Command:**
```bash
ragged query vision "table with numerical data" --limit 5
```

**Expected Result:**
- Results include pages with tables
- Table structure recognized
- Relevant pages ranked higher

**Actual Result:**
[To be filled]

**Status:** ⏳ Pending

---

### Step 4: Verify storage contains vision embeddings

**Command:**
```bash
ragged storage info --format json
```

**Expected Result:**
- vision_embeddings_count > 0
- vision_embeddings_count ≈ total_pages (one per page)
- text_embeddings_count > vision_embeddings_count (multiple chunks per page)

**Actual Result:**
[To be filled]

**Status:** ⏳ Pending

---

## Verification

### Visual Inspection
- [ ] Query results relevant to visual content
- [ ] Ranking reflects visual similarity
- [ ] Page previews (if available) match queries

### Quantitative Checks
- [ ] Vision embeddings exist for all pages
- [ ] Similarity scores in valid range (0-1)
- [ ] No missing or corrupted embeddings

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

- [Multi-Modal Query Guide](../../../guides/multimodal-queries.md)
- [Vision Embedding Architecture](../../../reference/vision-embeddings.md)

---

## Metadata

- **Test Duration:** [X minutes]
- **Sample Data Used:** 3 PDFs with visual content
- **Models Used:** ColPali (cached)
- **Hardware:** Apple Silicon (MPS backend)
