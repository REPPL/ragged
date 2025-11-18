# Performance Baseline Measurements

**Feature**: Current Performance Baseline Documentation
**Phase**: 0 (Foundation)
**Estimated Effort**: 1 hour
**Priority**: MUST-HAVE
**Dependencies**: Benchmarking framework (exists ✅)

---

## Overview

**Purpose**: Document current v0.2.8 performance as baseline for v0.2.9 improvements.

**Success Criteria**:
- All critical operations benchmarked on v0.2.8
- Results saved as `baseline.json`
- Baseline includes system specs (CPU, RAM, Python version)
- Baseline used by performance regression tests

---

## Implementation

### Baseline Script

```python
# scripts/benchmark_baseline.py

from src.utils.benchmarks import Benchmark, BenchmarkSuite
import json, platform, psutil

def create_baseline():
    """Benchmark all critical operations and save baseline."""

    suite = BenchmarkSuite("v0.2.8-baseline")

    # Embedder benchmarks
    suite.add(Benchmark("embedder-init-cold", warmup=0, iterations=10))
    suite.add(Benchmark("batch-embed-10", warmup=2, iterations=10))
    suite.add(Benchmark("batch-embed-100", warmup=2, iterations=5))

    # Query benchmarks
    suite.add(Benchmark("query-first", warmup=0, iterations=10))
    suite.add(Benchmark("query-repeat", warmup=1, iterations=20))

    # Ingestion benchmarks
    suite.add(Benchmark("scan-directory-100", warmup=0, iterations=3))

    # Index benchmarks
    suite.add(Benchmark("index-rebuild-100", warmup=0, iterations=3))
    suite.add(Benchmark("index-rebuild-1000", warmup=0, iterations=2))

    results = suite.run_all()

    # Save with system info
    baseline = {
        "version": "0.2.8",
        "timestamp": datetime.now().isoformat(),
        "system": {
            "cpu": platform.processor(),
            "cpu_count": psutil.cpu_count(),
            "ram_gb": psutil.virtual_memory().total / (1024**3),
            "python": platform.python_version()
        },
        "benchmarks": {name: result.to_dict() for name, result in results.items()}
    }

    with open("baseline.json", "w") as f:
        json.dump(baseline, f, indent=2)

    print(f"Baseline saved: {len(results)} benchmarks")
    return baseline
```

### Usage

```bash
# Generate baseline
python scripts/benchmark_baseline.py

# View baseline
cat baseline.json | jq '.benchmarks'
```

---

## Success Metrics

| Metric | Target |
|--------|--------|
| Operations benchmarked | 7+ critical paths |
| System info captured | CPU, RAM, Python version |
| Baseline file created | baseline.json |
| Used by regression tests | ✅ Integrated |

**Timeline**: 1 hour (script + run + validate)

---

**Status**: Specification complete, ready for implementation
