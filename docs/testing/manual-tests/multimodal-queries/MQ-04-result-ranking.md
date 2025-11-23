# Test: Result Ranking Validation

**Test ID:** MQ-04 | **Category:** multimodal-queries | **Status:** Pending

---

## Objective

Verify that result ranking accurately reflects relevance across query types.

## Prerequisites

- Multiple documents ingested with known content
- Variety of content types (text-heavy, visual-heavy, mixed)
- All query modes available

## Test Commands

```bash
# Test 1: Verify score ordering
ragged query text "machine learning" --limit 10 --show-scores

# Test 2: Check minimum score threshold
ragged query text "machine learning" --min-score 0.7 --limit 10

# Test 3: Compare across modalities
ragged query hybrid "data visualization" --limit 5 --show-scores
```

## Expected Results

- Scores in descending order (highest first)
- Min-score filter works correctly
- Scores in valid range (0.0-1.0)
- Higher scores correlate with better matches

## Verification

- [ ] Results sorted by score (descending)
- [ ] No scores outside 0.0-1.0 range
- [ ] Min-score threshold respected
- [ ] Qualitative relevance matches scores

## Notes

Ranking quality directly impacts user experience. Verify both quantitative (scores) and qualitative (actual relevance) aspects.
