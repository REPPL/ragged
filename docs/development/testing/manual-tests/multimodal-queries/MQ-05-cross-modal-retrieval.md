# Test: Cross-Modal Retrieval

**Test ID:** MQ-05 | **Category:** multimodal-queries | **Status:** Pending

---

## Objective

Validate ability to find visual content using text queries and vice versa.

## Prerequisites

- Documents with both text and visual content
- Vision embeddings include semantic understanding
- Cross-modal search enabled

## Test Commands

```bash
# Test 1: Text query → Find diagrams
ragged query hybrid "show me architecture diagrams" --limit 5

# Test 2: Visual description → Find content
ragged query vision "flowchart or process diagram" --limit 5

# Test 3: Concept → Find visualizations
ragged query hybrid "how data flows through the system" --limit 5
```

## Expected Results

- Text queries can retrieve pages with relevant diagrams
- Visual descriptions match actual visual content
- ColPali's semantic understanding of images works
- Cross-modal matches score reasonably

## Verification

- [ ] Text queries find relevant visual pages
- [ ] Visual descriptions match diagrams/charts
- [ ] Results make semantic sense
- [ ] No over-reliance on exact text matching

## Notes

Cross-modal retrieval is a key advantage of vision embeddings. ColPali understands image semantics, not just visual similarity.
