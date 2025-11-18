# LEANN - Graph-Based Vector Storage

**Source**: https://github.com/davidsandberg/leann
**Paper**: "LEANN: Approximate Nearest Neighbour Search with Limited Memory" (arXiv)
**Authors**: David Sandberg, et al.
**License**: MIT

---

## Overview

LEANN (Limited memory Exact Approximate Nearest Neighbour) achieves 97% storage savings compared to traditional vector databases through graph-based selective recomputation. Instead of storing all embeddings, LEANN stores a graph structure and recomputes embeddings on-demand during search.

**Key Innovation**: Trade storage for computation - 97% less disk space with 90% recall@3 (vs ~100% for traditional dense storage)

---

## What We Borrowed

### Graph-Based Vector Storage (v0.4.9)

**Original**: Approximate nearest neighbour search using graph navigation with selective embedding recomputation

**Adapted for ragged**: Optional LEANN backend alongside ChromaDB, allowing users to choose between accuracy (ChromaDB) and storage efficiency (LEANN)

**Integration**:
- VectorStore abstraction layer (v0.3.7, refined v0.4.2)
- LEANN as optional backend (v0.4.9)
- Migration tools for switching between backends
- User choice based on storage constraints

**Differences**: ragged implements LEANN as one of multiple pluggable backends, maintains ChromaDB as default for accuracy-critical use cases

---

## Trade-Offs

| Aspect | ChromaDB | LEANN |
|--------|----------|-------|
| Storage | Standard (100%) | 3% (97% savings) |
| Accuracy | ~100% recall | 90% recall@3 |
| Query Latency | <500ms | <2s |
| Best For | Accuracy-critical | Storage-constrained |

---

## Implementation Timeline

| Version | Features | Status |
|---------|----------|--------|
| v0.3.7 | VectorStore abstraction (foundation) | Planned Q2-Q3 2026 |
| v0.4.2 | VectorStore refinement | Planned |
| v0.4.9 | LEANN backend implementation | Planned |

---

## Related

- [VectorStore Abstraction ADR](../decisions/adrs/0015-vectorstore-abstraction.md)
- [v0.3.7 Roadmap](../roadmap/version/v0.3.0/v0.3.7.md)
- [v0.4.9 Roadmap](../roadmap/version/v0.4.0/v0.4.9.md)

---

## Attribution

This work integrates LEANN's innovative graph-based approach to vector storage, adapting it as an optional backend within ragged's VectorStore architecture.

We are grateful to David Sandberg and the LEANN team for their research and open-source implementation that makes storage-efficient vector search accessible.

**Original project**: https://github.com/davidsandberg/leann

---

## License Compatibility

**Source License**: MIT
**ragged License**: GPL-3.0
**Compatibility**: ✅ Compatible (MIT is permissive, compatible with GPL-3.0)
