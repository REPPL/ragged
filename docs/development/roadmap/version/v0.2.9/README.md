# v0.2.9 Roadmap: Stability and Performance Enhancements

**Status**: Planning
**Estimated Effort**: 42-53 hours
**Timeline**: 3-4 weeks
**Dependencies**: v0.2.8 (recommended)

---

## Vision

Make ragged rock-solid and fast. Focus on production readiness through comprehensive error handling, performance optimisation, and operational excellence.

**Guiding Principle**: Users should trust ragged with their important data and demanding workloads.

---

## Success Criteria

### Performance Targets

| Metric | Current | Target | Improvement |
|--------|---------|--------|-------------|
| Embedder init (cold) | ~2-3s | <0.5s | 4-6x faster |
| Embedder init (warm) | ~2-3s | <0.1s | 20-30x faster |
| Batch embedding (100) | Sequential | Batched | 3-5x faster |
| Repeat query | Same as first | <200ms | 10-20x faster |
| Large directory scan | Blocking | Async | 2-3x faster |
| Memory usage | Uncontrolled | Capped | Predictable |

### Stability Targets

- ✅ Error recovery success rate: >95%
- ✅ No OOM crashes on large batches
- ✅ Graceful handling of network failures
- ✅ Comprehensive logging for debugging
- ✅ Proactive health checks
- ✅ Test coverage: >80%

---

## Phases

### Phase 1: Critical Performance (MUST-HAVE) - 30-38 hours

Core performance optimisations that deliver measurable improvements:

1. **Embedder Caching** (6-8h)
   - Singleton pattern for model reuse
   - 4-6x faster cold start, 20-30x faster warm start
   - Memory-mapped model files

2. **Batch Embedding Optimisation** (5-6h)
   - Dynamic batch sizing
   - 3-5x faster than sequential
   - Memory-aware processing

3. **Query Result Caching** (5-6h)
   - LRU cache for query embeddings
   - TTL cache for results
   - 10-20x faster repeat queries

4. **Error Recovery & Resilience** (6-8h)
   - Retry with exponential backoff
   - Circuit breaker for services
   - Graceful error handling

5. **Memory Management & Limits** (4-5h)
   - Dynamic memory monitoring
   - OOM prevention
   - Automatic batch adjustment

6. **Comprehensive Logging & Monitoring** (4-5h)
   - Structured logging (JSON option)
   - Performance metrics
   - Operation audit trail

**Deliverable**: Fast, reliable ragged suitable for production

**Priority**: MUST-HAVE (core v0.2.9 scope)

---

### Phase 2: High Priority (RECOMMENDED) - 12-15 hours

Production-quality features:

7. **Enhanced Health Checks** (3-4h)
   - Deep diagnostics
   - Performance health checks
   - Proactive issue detection

8. **Async Operations Optimisation** (5-6h)
   - Concurrent document loading
   - Async embedding generation
   - Better resource utilisation

9. **Index Optimisation** (4-5h)
   - Pre-build and cache BM25 index
   - Optimise ChromaDB settings
   - Faster retrieval

**Deliverable**: Professional operational excellence

**Priority**: HIGH (implement if schedule allows)

---

### Phase 3: Nice-to-Have - 13-17 hours

**Only if time permits**:

10. **Test Coverage Improvements** (6-8h) - reach 80%+
11. **Performance Profiling Tools** (4-5h) - built-in profiling
12. **Graceful Degradation** (3-4h) - fallback paths

**Priority**: NICE-TO-HAVE (defer if schedule pressure)

---

## Detailed Feature Specifications

See individual feature documents:
- [Embedder Caching](./features/embedder-caching.md)
- [Batch Embedding Optimisation](./features/batch-embedding.md)
- [Query Result Caching](./features/query-caching.md)
- [Error Recovery](./features/error-recovery.md)
- [Memory Management](./features/memory-management.md)
- [Comprehensive Logging](./features/logging.md)
- [Enhanced Health Checks](./features/health-checks.md)
- [Async Operations](./features/async-operations.md)
- [Index Optimisation](./features/index-optimisation.md)

---

## Breaking Changes

**None**. All optimisations are internal implementation improvements.

---

## Performance Benchmarking

### Benchmark Suite

```bash
# Embedder performance
ragged benchmark embedding-init --runs 10

# Batch embedding
ragged benchmark batch-embed --size 100 --runs 5

# Query performance
ragged benchmark query --queries test-set.txt --runs 20

# Memory profiling
ragged profile-memory add /large-dataset
```

### Success Metrics

**Before/After Comparison Required**:
- Embedder init time (cold/warm)
- Batch embedding throughput
- Query latency (first/repeat)
- Memory usage under load
- Error recovery success rate

---

## Testing Strategy

### Performance Testing
- Benchmark before/after for all optimisations
- Memory profiling under various loads
- Concurrent operation stress tests
- Long-running stability tests

### Stability Testing
- Error injection testing
- Network failure simulation
- Resource exhaustion tests
- Race condition testing
- Regression testing

### Coverage Testing
- Target: 80%+ overall
- Target: 90%+ for critical paths
- Property-based testing for edge cases

---

## Risk Assessment

**Medium Risk** - Performance optimisations can introduce bugs

### Identified Risks:

1. **Cache Invalidation Bugs**
   - Risk: Stale data, incorrect results
   - Mitigation: Comprehensive cache tests, TTL policies

2. **Memory Leaks**
   - Risk: OOM in long-running processes
   - Mitigation: Memory profiling, leak detection tests

3. **Race Conditions**
   - Risk: Data corruption in concurrent ops
   - Mitigation: Thorough concurrent testing, proper locking

4. **Performance Regressions**
   - Risk: Optimisations make things slower
   - Mitigation: Before/after benchmarks, feature flags

### Mitigation Strategy:

- Feature flags for all major changes
- Phased rollout (opt-in → default)
- Comprehensive test suite
- Performance regression tests in CI

---

## Timeline

**Week 1**: Caching (embedder, query results) - 11-14h
**Week 2**: Error handling + memory management - 10-13h
**Week 3**: Logging + high priority features - 12-15h
**Week 4**: Testing, benchmarking, validation - 9-11h

---

## Related Documentation

- [v0.2.8 Roadmap](../v0.2.8/README.md) - Previous version
- [v0.2.7 Implementation](../../implementation/version/v0.2/README.md) - Current baseline
- [Performance Planning](../../../planning/technologies/README.md) - Technical context

---

**Last Updated**: 2025-11-17
**Status**: Planning → Awaiting v0.2.8 Completion
