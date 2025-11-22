# Performance Tuning Guide

**Purpose**: Configuration options, optimisation techniques, and benchmarking guide for ragged performance.

**Audience**: Developers, system administrators, power users

---

## Table of Contents

1. [Performance Targets](#performance-targets)
2. [Benchmarking](#benchmarking)
3. [Ingestion Optimisation](#ingestion-optimisation)
4. [Query Optimisation](#query-optimisation)
5. [Memory Optimisation](#memory-optimisation)
6. [Vector Store Selection](#vector-store-selection)
7. [Configuration Tuning](#configuration-tuning)
8. [Profiling](#profiling)

---

## Performance Targets

### v0.4.4 Baseline Targets

**Ingestion Performance**:
- Single document: <50ms (p95)
- Batch 100 docs: <5s (p95)
- Large corpus (10K docs): <10min (p95)

**Query Performance**:
- Simple query: <300ms (p50), <500ms (p95)
- Complex query with filters: <500ms (p50), <800ms (p95)
- Cold start (first query): <2s (p95)

**Memory Usage**:
- Resident memory: <500MB for 10K docs
- Memory leak test: 0 growth over 1000 ops
- Peak memory: <1GB under load

**Resource Usage**:
- CPU idle: <5%
- CPU under load: <80% (single core)
- Disk I/O: <100MB/s peak

---

## Benchmarking

### Running Benchmarks

Use the provided benchmark script to measure performance:

```bash
# Full benchmark suite
python scripts/benchmark.py

# Quick benchmark (small corpus only)
python scripts/benchmark.py --quick

# Save to specific location
python scripts/benchmark.py --save benchmarks/my-baseline.json

# Run without saving
python scripts/benchmark.py --no-save
```

### Benchmark Results

Benchmark results are saved as JSON:

```json
{
  "version": "0.4.4",
  "timestamp": "2025-11-22 10:30:00",
  "benchmarks": {
    "startup": {"time_sec": 1.2, "target_sec": 2.0, "passes": true},
    "memory": {"current_mb": 245.3, "peak_mb": 450.1},
    "ingestion": {...},
    "query": {...}
  }
}
```

### Regression Detection

Performance regressions are detected automatically in CI/CD:

- **Hard limits** (CI fails): +10% query latency, +15% memory, -10% throughput
- **Soft limits** (warning): +5-10% query latency, +10-15% memory, -5-10% throughput

---

## Ingestion Optimisation

### Batch Processing

Always use batch ingestion for multiple documents:

```python
# SLOW - One document at a time
for doc in documents:
    ragged_system.ingest_document(doc)

# FAST - Batch ingestion
ragged_system.ingest_documents(documents, batch_size=100)
```

### Chunking Configuration

Optimise chunk size for your use case:

```python
from src.config import get_settings

settings = get_settings()

# Smaller chunks = more precise, slower ingestion
settings.chunk_size = 256
settings.chunk_overlap = 32

# Larger chunks = faster ingestion, less precise
settings.chunk_size = 1024
settings.chunk_overlap = 128
```

**Recommendations**:
- **Academic papers**: 512 tokens, 64 overlap
- **Code documentation**: 256 tokens, 32 overlap
- **Books/long-form**: 1024 tokens, 128 overlap

### Embedding Optimisation

Choose appropriate embedding model for speed/quality trade-off:

```python
# Fast but less accurate
settings.embedding_model = "all-MiniLM-L6-v2"  # 384 dimensions, ~60ms/doc

# Balanced
settings.embedding_model = "all-mpnet-base-v2"  # 768 dimensions, ~120ms/doc

# Slower but most accurate
settings.embedding_model = "instructor-xl"  # 768 dimensions, ~250ms/doc
```

### Parallel Processing

Enable parallel processing for large batches:

```python
import multiprocessing

# Use all available cores
settings.num_workers = multiprocessing.cpu_count()

# Conservative (leave cores for other processes)
settings.num_workers = max(1, multiprocessing.cpu_count() - 2)
```

---

## Query Optimisation

### Result Limit (k)

Request only as many results as you need:

```python
# Default is often excessive
results = ragged.query("what is AI?", k=10)  # Returns 10 results

# Optimise for speed
results = ragged.query("what is AI?", k=5)  # 50% faster for large corpora
```

### Metadata Filtering

Pre-filter with metadata before vector search:

```python
# SLOW - Vector search all docs, then filter
results = ragged.query("machine learning", k=10)
filtered = [r for r in results if r.metadata['year'] > 2020]

# FAST - Filter first, then vector search
results = ragged.query(
    "machine learning",
    k=10,
    filter={"year": {"$gt": 2020}}
)
```

### Caching

Enable query caching for repeated queries:

```python
settings.enable_query_cache = True
settings.cache_size = 1000  # Number of queries to cache
settings.cache_ttl = 3600  # Time-to-live in seconds
```

### Hybrid Search

For best precision, use hybrid search (vector + keyword):

```python
# Default: Vector search only (fastest)
results = ragged.query("explain neural networks", method="vector")

# Hybrid: Vector + BM25 keyword (better quality, ~20% slower)
results = ragged.query("explain neural networks", method="hybrid")
```

---

## Memory Optimisation

### Memory Mapping

For large corpora, use memory mapping to reduce RAM usage:

```python
# Load entire vector index into RAM (fastest, high memory)
settings.mmap_vectors = False

# Memory-mapped vectors (slower, low memory)
settings.mmap_vectors = True
```

### Lazy Loading

Enable lazy loading for large collections:

```python
# Eager loading (default, fast queries)
settings.lazy_load_collections = False

# Lazy loading (slower first query, saves memory)
settings.lazy_load_collections = True
```

### Garbage Collection

Tune garbage collection for long-running processes:

```python
import gc

# More frequent GC (lower memory, slightly slower)
gc.set_threshold(700, 10, 10)

# Less frequent GC (higher memory, faster)
gc.set_threshold(2000, 25, 25)

# Manually trigger after large operations
gc.collect()
```

---

## Vector Store Selection

### ChromaDB vs LEANN

Choose the right vector store for your platform:

**ChromaDB** (default):
- Cross-platform compatibility
- Mature, stable
- Good for <100K documents
- ~200-300ms query latency (p50)

**LEANN** (optimised for Apple Silicon):
- 2-3x faster on M1/M2/M3 Macs
- Native ARM64 optimisation
- Best for >10K documents
- ~80-120ms query latency (p50) on Apple Silicon

```bash
# Set vector store backend
export RAGGED_VECTOR_STORE=leann  # or chromadb
```

### Configuration Comparison

| Feature | ChromaDB | LEANN |
|---------|----------|-------|
| Platforms | All | macOS (M1+), Linux (ARM64/x86_64) |
| Speed (Apple Silicon) | Baseline | 2-3x faster |
| Speed (x86_64) | Baseline | Similar |
| Memory Usage | Moderate | Lower |
| Index Build | Slower | Faster |

---

## Configuration Tuning

### High-Performance Profile

For maximum speed (at cost of memory):

```env
# .env configuration
RAGGED_VECTOR_STORE=leann
RAGGED_CHUNK_SIZE=1024
RAGGED_CHUNK_OVERLAP=128
RAGGED_MMAP_VECTORS=false
RAGGED_LAZY_LOAD=false
RAGGED_QUERY_CACHE=true
RAGGED_CACHE_SIZE=2000
RAGGED_NUM_WORKERS=8
```

### Low-Memory Profile

For constrained environments:

```env
# .env configuration
RAGGED_VECTOR_STORE=leann
RAGGED_CHUNK_SIZE=512
RAGGED_CHUNK_OVERLAP=64
RAGGED_MMAP_VECTORS=true
RAGGED_LAZY_LOAD=true
RAGGED_QUERY_CACHE=false
RAGGED_NUM_WORKERS=2
```

### Balanced Profile (Recommended)

Default balanced configuration:

```env
# .env configuration
RAGGED_VECTOR_STORE=chromadb
RAGGED_CHUNK_SIZE=512
RAGGED_CHUNK_OVERLAP=64
RAGGED_MMAP_VECTORS=false
RAGGED_LAZY_LOAD=false
RAGGED_QUERY_CACHE=true
RAGGED_CACHE_SIZE=1000
RAGGED_NUM_WORKERS=4
```

---

## Profiling

### CPU Profiling

Identify CPU bottlenecks with cProfile:

```bash
# Profile a query
python -m cProfile -o profile.stats -m ragged query "what is machine learning"

# Analyse results
python -m pstats profile.stats
> sort cumulative
> stats 20
```

### Memory Profiling

Track memory usage with memory_profiler:

```bash
# Install memory_profiler
pip install memory-profiler

# Profile memory usage
python -m memory_profiler scripts/benchmark.py
```

### Visual Profiling

Generate flame graphs with py-spy:

```bash
# Install py-spy
pip install py-spy

# Record profile
py-spy record --output profile.svg -- python -m ragged query "test"

# Open profile.svg in browser
```

### Continuous Profiling

Monitor performance over time:

```bash
# Run benchmarks regularly
python scripts/benchmark.py --save benchmarks/$(date +%Y%m%d).json

# Compare with baseline
python scripts/compare_benchmarks.py \
    benchmarks/v0.4.4-baseline.json \
    benchmarks/$(date +%Y%m%d).json
```

---

## Related Documentation

- [VectorStore Backend Comparison](../development/implementation/version/v0.4/v0.4.3/README.md) - LEANN vs ChromaDB details
- [Performance Baseline](../../benchmarks/v0.4.4-baseline.json) - v0.4.4 baseline metrics
- [Architecture Overview](../explanation/architecture-overview.md) - System architecture

---
