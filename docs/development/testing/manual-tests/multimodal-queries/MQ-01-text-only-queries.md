# Test: Text-Only Queries

**Test ID:** MQ-01 | **Category:** multimodal-queries | **Status:** Pending

---

## Objective

Validate semantic text search functionality without vision components.

## Prerequisites

- Documents ingested (with or without vision)
- Text embeddings available
- nomic-embed-text model loaded

## Test Commands

```bash
# Query 1: Technical concept
ragged query text "machine learning algorithms" --limit 5

# Query 2: Specific topic
ragged query text "neural network architecture" --limit 5

# Query 3: Data analysis
ragged query text "data visualization techniques" --limit 5
```

## Expected Results

- Semantically relevant chunks returned
- Similarity scores > 0.5 for good matches
- Results ranked by relevance
- Response time < 2 seconds

## Verification

- [ ] Results match query intent
- [ ] Ranking appears correct
- [ ] No errors or crashes
- [ ] Performance acceptable

## Notes

Test baseline text search before adding vision complexity.
