# Performance Baseline: ragged v0.2.2

**Date:** 2025-11-16
**Version:** 0.2.2
**Purpose:** Establish performance baselines for comparison with future versions

---

## Summary

This document contains performance baseline measurements for ragged v0.2.2.
These metrics will be used to validate performance improvements in v0.2.7.

**Note:** These are estimated baselines based on system architecture analysis. Actual benchmarks will be run before v0.2.7 performance validation.

## Methodology

- **Environment:** Local Docker containers (ChromaDB, Ollama)
- **System:** macOS (Darwin 25.1.0), ARM architecture
- **Embedding Model:** all-MiniLM-L6-v2 (sentence-transformers)
- **LLM Model:** llama3.2:latest (Ollama)

## Results

### Startup Time

Time to initialise core components (embedder, vector store, retriever, LLM client).

- **Estimated Mean:** 3000-5000ms
- **Components:** Model loading, vector store connection, retriever init, LLM client init
- **Note:** Includes sentence-transformer model loading (first time)

### Query Performance

Time to retrieve relevant chunks for a query.

**Cold Query (first run, no cache):**
- **Estimated Mean:** 500-800ms
- **Breakdown:** Vector similarity search + BM25 scoring + RRF fusion

**Warm Query (cached):**
- **Estimated Mean:** 200-400ms
- **Note:** Benefits from vector store caching

**Cache Benefit:** ~1.5-2x faster (33-50% improvement)

### Batch Ingestion Performance

Time to ingest batches of documents (load, chunk, embed, store).

| Document Count | Estimated Time | Est. Docs/Second |
|----------------|----------------|------------------|
| 10             | 30-45s         | 0.2-0.3          |
| 50             | 150-250s       | 0.2-0.3          |
| 100            | 300-500s       | 0.2-0.3          |

**Bottleneck:** Sequential processing, embedding generation

### Memory Usage

- **Idle:** ~150-200 MB
- **Under Load (100 docs):** ~500-800 MB
- **Increase:** ~350-600 MB

**Memory breakdown:**
- Sentence-transformer model: ~100MB
- Vector embeddings: ~50-100MB per 100 documents
- BM25 index: ~20-40MB per 100 documents
- Python overhead: ~100MB

---

## Performance Targets for v0.2.7

Based on these baselines, v0.2.7 should achieve:

### Startup Time
- **Current:** 3000-5000ms
- **Target:** <2000ms (BM25 persistence + lazy loading)
- **Improvement:** ~50-60% faster

### Query Performance
- **Current (warm):** 200-400ms
- **Target:** 50-150ms (50-75% faster with embedding caching)
- **Improvement:** 60-75% faster

### Batch Ingestion
- **Current (100 docs):** 300-500s
- **Target (100 docs):** 75-150s (2-4x faster with async processing)
- **Improvement:** 66-75% faster

### Memory Usage
- **Current (idle):** 150-200 MB
- **Target (idle):** <100 MB (lazy loading, no pre-loaded models)
- **Improvement:** 50% reduction

---

## Implementation Notes

### v0.2.7 Performance Enhancements

**Caching Strategy:**
- Embedding cache (LRU eviction)
- BM25 index persistence
- Model lazy loading

**Async Processing:**
- Parallel document loading
- Concurrent embedding generation
- Batch vector store operations

**Optimisations:**
- Chunking algorithm improvements
- Query result caching
- Reduced model memory footprint

### Validation Plan

Before claiming performance improvements in v0.2.7:
1. Run actual benchmarks on v0.2.2 (using scripts/baseline_performance.py)
2. Implement v0.2.7 optimisations
3. Run identical benchmarks on v0.2.7
4. Compare results and validate targets achieved
5. Document actual improvements

---

## Related Documentation

- [v0.2.7 Planning](../../planning/version/v0.2.7/) - Performance improvement goals
- [v0.2.7 Roadmap](../../roadmap/version/v0.2.7/) - Implementation plan
- [Performance Benchmark Script](../../../../scripts/baseline_performance.py) - Automated benchmarking

---

**Status:** Estimated baselines (to be validated with actual measurements)
**Next Step:** Begin v0.2.3 implementation
**Validation:** Run actual benchmarks before v0.2.7 performance claims
