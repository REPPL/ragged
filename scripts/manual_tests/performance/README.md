# Performance Tests

**Purpose:** Measure system performance and detect regressions across versions.

**Pattern:** Benchmarks with historical baselines for comparison.

---

## Directory Structure

```
performance/
├── benchmarks/          # Executable benchmark scripts
│   ├── ingestion.py
│   ├── retrieval.py
│   ├── cold_start.py
│   └── memory_usage.py
├── baselines/           # Historical performance data
│   ├── v0.2.4.json
│   ├── v0.2.5.json
│   ├── v0.2.7.json
│   ├── v0.2.8.json
│   └── v0.2.9.json
└── compare_versions.py  # Cross-version comparison
```

---

## What Belongs Here

✅ **Performance benchmarks** - Timing, throughput, latency measurements
✅ **Resource usage** - Memory, CPU profiling
✅ **Historical baselines** - Performance data for past versions
✅ **Regression detection** - Identifying performance degradation

❌ **Functional tests** - Use `regression/` directory
❌ **Feature validation** - Use `version/` directory
❌ **User workflows** - Use `workflows/` directory

---

## Benchmarks

### 1. Ingestion Performance (`benchmarks/ingestion.py`)

**Measures:**
- Time to ingest 100 documents (mixed formats)
- Documents per second throughput
- Memory usage during ingestion
- Chunking performance

**Test Data:**
- 50 PDFs (varying sizes: 1-10 pages)
- 25 Markdown files
- 15 HTML files
- 10 Plain text files

**Metrics:**
- Total ingestion time
- Average time per document
- Peak memory usage
- Documents/second throughput

### 2. Retrieval Performance (`benchmarks/retrieval.py`)

**Measures:**
- Query latency (p50, p95, p99)
- Concurrent query throughput
- Cache hit rate
- Result fusion time (hybrid retrieval)

**Test Queries:**
- 50 diverse queries (simple, complex, filtered)
- Sequential and concurrent execution
- Cache warm and cold scenarios

**Metrics:**
- p50/p95/p99 query latency
- Queries per second
- Cache effectiveness
- Fusion overhead

### 3. Cold Start Performance (`benchmarks/cold_start.py`)

**Measures:**
- First query latency (includes embedder initialization)
- Model loading time
- Index initialization time

**Introduced:** v0.2.9 (cold start optimisation feature)

**Metrics:**
- Time to first query response
- Embedder initialization time
- ChromaDB connection time

### 4. Memory Usage (`benchmarks/memory_usage.py`)

**Measures:**
- Baseline memory footprint
- Memory growth during ingestion
- Memory during query execution
- Memory leak detection

**Metrics:**
- Baseline memory (MB)
- Peak memory usage (MB)
- Memory per document (KB)
- Memory growth rate

---

## pytest Markers

All performance tests should use these markers:

```python
import pytest

@pytest.mark.performance
@pytest.mark.slow
@pytest.mark.requires_ollama
@pytest.mark.requires_chromadb
def test_ingestion_performance():
    """Benchmark document ingestion performance"""
    pass
```

---

## Running Benchmarks

### Run all performance benchmarks

```bash
pytest scripts/manual_tests/performance/benchmarks/ -m performance
```

### Run specific benchmark

```bash
pytest scripts/manual_tests/performance/benchmarks/ingestion.py
```

### Generate performance comparison report

```bash
python scripts/manual_tests/performance/compare_versions.py \
    --versions v0.2.7,v0.2.8,v0.2.9 \
    --output reports/performance_comparison.html
```

---

## Performance Baselines

Baseline files store historical performance data in JSON format:

```json
{
  "version": "v0.2.9",
  "date": "2025-11-19",
  "system": {
    "os": "macOS 14.1",
    "cpu": "Apple M2",
    "memory": "16GB"
  },
  "ingestion": {
    "total_time_seconds": 45.2,
    "documents_per_second": 2.21,
    "peak_memory_mb": 512
  },
  "retrieval": {
    "p50_latency_ms": 120,
    "p95_latency_ms": 350,
    "p99_latency_ms": 580,
    "queries_per_second": 8.3
  },
  "cold_start": {
    "first_query_seconds": 3.2,
    "embedder_init_seconds": 2.1
  },
  "memory": {
    "baseline_mb": 180,
    "peak_mb": 512,
    "per_document_kb": 3.2
  }
}
```

---

## Performance Regression Detection

### Thresholds

**Warning:** Performance degradation > 10%
**Failure:** Performance degradation > 20%

### Example

```
v0.2.8 ingestion: 50 seconds
v0.2.9 ingestion: 45 seconds
Change: -10% (✅ IMPROVEMENT)

v0.2.8 query p95: 300ms
v0.2.9 query p95: 350ms
Change: +17% (⚠️ WARNING - investigate)
```

---

## Maintenance

### When to Update Baselines

- ✅ **After each version release** - Capture new baseline
- ✅ **Significant performance improvements** - Document gains
- ✅ **System changes** - Hardware, dependencies updated

### How to Update Baselines

```bash
# Run benchmarks for new version
pytest scripts/manual_tests/performance/benchmarks/ -m performance --json-report

# Generate new baseline file
python scripts/manual_tests/performance/generate_baseline.py \
    --version v0.2.10 \
    --output baselines/v0.2.10.json
```

---

## System Information

Include system specs when generating baselines:

- Operating system (macOS/Linux/Windows)
- CPU architecture (x86_64/arm64)
- Memory (GB)
- Python version
- Key dependency versions (ChromaDB, Ollama, etc.)

---

## Related Documentation

- [Version Tests](../version/README.md) - Feature-specific tests
- [Regression Tests](../regression/README.md) - Functional validation
- [Performance Roadmap](../../../docs/development/roadmap/features/hardware-optimisation-roadmap.md) - Optimisation plans
- [v0.2.9 Performance Features](../../../docs/development/roadmap/version/v0.2/v0.2.9/features/performance-optimisation.md) - Performance improvements

---

**Maintained By:** ragged development team
