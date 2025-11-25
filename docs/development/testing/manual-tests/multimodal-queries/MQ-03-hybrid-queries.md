# Test: Hybrid Text+Vision Queries

**Test ID:** MQ-03 | **Category:** multimodal-queries | **Status:** Pending

---

## Objective

Validate combined text and vision search with balanced ranking.

## Prerequisites

- Documents ingested WITH vision embeddings
- Both text and vision collections populated
- Hybrid query mode available

## Test Commands

```bash
# Query 1: Combined semantic + visual
ragged query hybrid "machine learning with diagrams" --limit 5

# Query 2: Text concept + visual context
ragged query hybrid "neural networks architecture visualization" --limit 5

# Query 3: Data analysis + charts
ragged query hybrid "statistical analysis with graphs" --limit 5
```

## Expected Results

- Results combine text relevance + visual similarity
- Pages with both text AND visual matches ranked highest
- Balanced scoring (not dominated by one modality)
- Diverse result set

## Verification

- [ ] Top results have both text and visual relevance
- [ ] Text-only and vision-only pages ranked lower
- [ ] Score distribution makes sense
- [ ] No single modality dominates

## Notes

Hybrid queries should leverage strengths of both text and vision embeddings.
