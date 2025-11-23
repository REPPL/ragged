# Test: Vision-Only Queries

**Test ID:** MQ-02 | **Category:** multimodal-queries | **Status:** Pending

---

## Objective

Validate visual similarity search using ColPali embeddings.

## Prerequisites

- Documents ingested WITH vision embeddings
- ColPali model loaded
- Sample PDFs contain visual content

## Test Commands

```bash
# Query 1: Diagram search
ragged query vision "neural network architecture diagram" --limit 5

# Query 2: Chart search
ragged query vision "bar chart data visualization" --limit 5

# Query 3: Table search
ragged query vision "table with numerical data" --limit 5
```

## Expected Results

- Pages with matching visual content returned
- Visual similarity scores reasonable
- Correct page numbers identified
- No text-only matches (vision embeddings only)

## Verification

- [ ] Results contain relevant visual elements
- [ ] Non-visual pages ranked lower
- [ ] Page-level results (not chunk-level)
- [ ] Performance acceptable (< 5 seconds)

## Notes

Vision queries use page-level embeddings, not chunk-level.
