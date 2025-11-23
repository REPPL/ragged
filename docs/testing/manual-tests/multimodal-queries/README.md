# Multi-Modal Query Tests

**Purpose:** Validate hybrid text+vision query functionality

---

## Overview

These tests validate ragged's multi-modal query capabilities, enabling users to search documents using:
- Text-only queries (semantic search)
- Vision-only queries (visual similarity)
- Hybrid queries (combined text + vision)

---

## Test Scenarios

| Test | Purpose | Key Validation |
|------|---------|----------------|
| **MQ-01** | Text-only queries | Semantic search accuracy |
| **MQ-02** | Image-based queries | Visual similarity matching |
| **MQ-03** | Hybrid queries | Combined text+vision ranking |
| **MQ-04** | Result ranking | Relevance scoring accuracy |
| **MQ-05** | Cross-modal retrieval | Find visual content via text queries |

---

## Prerequisites

- Documents ingested with vision embeddings
- ColPali model downloaded and cached
- Sample PDFs with diverse visual content
- ChromaDB running

---

## Execution Order

1. **MQ-01**: Baseline text search
2. **MQ-02**: Vision-only search
3. **MQ-03**: Hybrid search combining both
4. **MQ-04**: Verify ranking algorithms
5. **MQ-05**: Cross-modal capabilities

---

## Success Criteria

- [ ] Text queries return semantically relevant results
- [ ] Vision queries match visual content accurately
- [ ] Hybrid queries balance text and vision effectively
- [ ] Ranking reflects true relevance
- [ ] No crashes or errors during query execution

---

## Related Documentation

- [Multi-Modal Workflow Tutorial](../../../tutorials/multimodal-workflow.md)
- Query Command Reference
- [Manual Testing README](../README.md)
