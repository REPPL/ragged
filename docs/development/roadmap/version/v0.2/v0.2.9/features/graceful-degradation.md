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

---

**Status**: ✅ IMPLEMENTED (commit 6fade61)

**Components**:
1. **FallbackStrategy** - Primary + ordered fallbacks with automatic retry
2. **@with_fallback** - Decorator for fallback behaviour
3. **DegradedMode** - Context manager for reduced functionality states
4. **safe_execute** - Simple execution with default fallback
5. **FallbackChain** - Builder pattern for sequential fallbacks
6. **adaptive_batch_size** - Dynamic sizing under resource pressure
7. **CircuitBreaker** - Prevent repeated calls to failing services

**Implementation**: src/utils/graceful_degradation.py (450 lines)
**Tests**: 530 lines, 80+ test cases

**Fallback Paths Implemented**:
- BM25 unavailable → Dense-only search
- Embedder unavailable → Cached embeddings
- Memory pressure → Reduced batch sizes
- Vector store down → Cache-only mode
- Model unavailable → Simpler model fallback
- Circuit breaker: 3 states (CLOSED/OPEN/HALF_OPEN)
