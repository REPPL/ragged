# Graceful Degradation Specifications

**Phase**: 3 | **Effort**: 2-3h | **Priority**: MUST-HAVE

**Fallback Paths**:

1. **BM25 unavailable** → Dense-only search
2. **Embedder unavailable** → Skip re-embedding, use cached
3. **Memory pressure** → Reduce batch sizes
4. **Vector store down** → Cache-only mode
5. **Model unavailable** → Fallback to simpler model

**Implementation**:
```python
def retrieve_with_fallback(query, method="hybrid"):
    try:
        return hybrid_retrieve(query)
    except BM25Error:
        logger.warning("BM25 unavailable, using dense-only")
        return dense_retrieve(query)
    except VectorStoreError:
        if cache.has(query):
            return cache.get(query)
        raise ServiceUnavailableError("All retrieval methods unavailable")
```

**Success**: >99% availability despite failures

**Timeline**: 2-3h
