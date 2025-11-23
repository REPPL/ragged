# ADR-005: Dual Embedding Storage Architecture

**Status:** Accepted

---

## Context and Problem Statement

ragged v0.5.0 introduced vision embeddings (ColPali, 128-dim) alongside existing text embeddings (SentenceTransformers, 384-dim). These have incompatible dimensions and cannot coexist in the same ChromaDB collection.

How should ragged store and retrieve across both embedding types?

## Decision Drivers

1. **Dimensionality Incompatibility**: Cannot mix 384-dim and 128-dim in same collection
2. **Hybrid Retrieval**: Need to query both text and vision, combine results
3. **Backward Compatibility**: Existing v0.4.x text-only collections must still work
4. **Storage Efficiency**: Avoid unnecessary duplication
5. **Query Performance**: Fast retrieval from both embedding types

## Considered Options

### Option 1: Separate Collections with RRF Fusion (Chosen)

**Description**: Store text embeddings in `{collection}_text` and vision embeddings in `{collection}_vision`. Use Reciprocal Rank Fusion (RRF) to merge results.

**Pros**:
- Clean separation of concerns
- Backward compatible (text collections unchanged)
- RRF proven technique for hybrid search
- Each collection optimised for its dimensionality
- Can query text-only, vision-only, or hybrid

**Cons**:
- Two separate queries required for hybrid retrieval
- RRF adds minor latency
- Storage overhead (both embeddings stored)

### Option 2: Unified Storage with Padding

**Description**: Pad 128-dim vision embeddings to 384-dim with zeros, store in same collection.

**Pros**:
- Single collection simplifies architecture
- One query for retrieval

**Cons**:
- Wastes storage (256 dimensions of zeros per vision embedding)
- Cosine similarity metrics distorted by padding
- No performance benefit (still need to process both types)

### Option 3: Separate Databases

**Description**: Use different ChromaDB instances for text vs vision.

**Pros**:
- Complete isolation

**Cons**:
- High operational overhead (two database instances)
- Complex configuration
- No architectural benefit over separate collections

## Decision Outcome

**Chosen Option**: "Separate Collections with RRF Fusion"

**Justification**:

1. **Technical Correctness**: Different embedding dimensions require separate collections. Padding is wasteful and distorts similarity metrics.

2. **Backward Compatibility**: Text-only workflows (v0.4.x) continue working unchanged. Vision embeddings are purely additive.

3. **Hybrid Retrieval**: RRF (Reciprocal Rank Fusion) is established technique:
   ```python
   text_results = query_text_collection(query)
   vision_results = query_vision_collection(query_image)
   combined = rrf_merge(text_results, vision_results, k=60)
   ```

4. **Flexibility**: Users can choose:
   - Text-only: Fast, lightweight
   - Vision-only: Layout-aware, no text extraction needed
   - Hybrid: Best of both (default when `--vision` used)

**Consequences**:
- **Positive**:
  - Clean architecture with clear separation
  - Backward compatible with v0.4.x
  - Optimal storage for each embedding type
  - Flexible retrieval strategies
  - RRF proven in information retrieval research

- **Negative**:
  - Two queries for hybrid retrieval (adds ~50ms latency)
  - Storage overhead when both embeddings used (~2x storage)
  - Slightly more complex codebase (DualEmbeddingStore class)

## Implementation Notes

**When**: Implemented in v0.5.0

**Key Classes**:
- `DualEmbeddingStore` (`src/storage/dual_store.py`) - Manages both collections
- Collection naming: `{name}_text` and `{name}_vision`
- RRF implementation in `reciprocal_rank_fusion()`

**Storage Format**:
```
~/.ragged/storage/
  chromadb/
    {collection}_text/     # 384-dim text embeddings
    {collection}_vision/   # 128-dim vision embeddings
```

## References

- [Reciprocal Rank Fusion Paper](https://plg.uwaterloo.ca/~gvcormac/cormacksigir09-rrf.pdf)
- [DualEmbeddingStore Implementation](../../../src/storage/dual_store.py)
- [ADR-001: Vision Embeddings Opt-In](./ADR-001-vision-embeddings-opt-in-design.md)
- [ADR-002: ChromaDB Choice](./ADR-002-chromadb-as-vector-database.md)

---

**Supersedes**: N/A

**Superseded By**: N/A
