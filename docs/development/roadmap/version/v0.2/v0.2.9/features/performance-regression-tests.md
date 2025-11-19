# Performance Regression Test Suite

**Feature**: Automated Performance Regression Detection
**Phase**: 0 (Foundation)
**Estimated Effort**: 4-5 hours
**Priority**: MUST-HAVE
**Dependencies**: Benchmarking framework (`src/utils/benchmarks.py` exists ✅)

---

## Overview

**Purpose**: Prevent performance regressions by automatically benchmarking critical operations in CI and failing builds if performance degrades >5%.

**Success Criteria**:
- All critical paths have automated benchmarks
- CI runs benchmarks on every PR/push
- Build fails if >5% slower than baseline
- Historical performance tracking
- Before/after comparison reports

---

## Technical Design

### Architecture

Three-layer system:
1. **Benchmark definitions** - Python functions using existing framework
2. **CI integration** - GitHub Actions workflow
3. **Performance database** - JSON file tracking historical results

### Benchmark Suite Structure

```python
# tests/performance/test_regression.py

import pytest
from src.utils.benchmarks import Benchmark, BenchmarkSuite
from src.embeddings.factory import get_embedder, create_embedder
from src.retrieval.hybrid import HybridRetriever

class RegressionBenchmarks:
    """Critical path benchmarks for regression detection."""

    @pytest.mark.performance
    def test_embedder_init_cold(self):
        """Benchmark embedder cold start."""
        benchmark = Benchmark(
            name="embedder-init-cold",
            warmup_iterations=0,  # No warmup for cold start
            test_iterations=10
        )
        result = benchmark.run(create_embedder)

        # Load baseline
        baseline = load_baseline("embedder-init-cold")

        # Assert not >5% slower
        assert result.mean <= baseline.mean * 1.05, \
            f"Regression: {result.mean}s vs baseline {baseline.mean}s"

    @pytest.mark.performance
    def test_batch_embedding_100(self):
        """Benchmark batch embedding (100 docs)."""
        embedder = get_embedder()
        texts = ["Sample document " * 50] * 100  # 100 docs

        benchmark = Benchmark("batch-embed-100", warmup_iterations=2, test_iterations=5)
        result = benchmark.run(lambda: embedder.embed_batch(texts))

        baseline = load_baseline("batch-embed-100")
        assert result.mean <= baseline.mean * 1.05

    @pytest.mark.performance
    def test_query_latency(self):
        """Benchmark query end-to-end latency."""
        # ... similar pattern
```

### CI Integration

```yaml
# .github/workflows/performance.yml

name: Performance Regression Tests

on: [push, pull_request]

jobs:
  performance:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.12'

      - name: Install dependencies
        run: |
          pip install -e .
          pip install pytest pytest-benchmark

      - name: Download baseline
        run: |
          # Download from artifacts or S3
          wget https://storage/baselines/v0.2.8-baseline.json -O baseline.json

      - name: Run performance tests
        run: |
          pytest tests/performance/ -v -m performance

      - name: Upload results
        if: always()
        uses: actions/upload-artifact@v3
        with:
          name: performance-results
          path: performance-results.json

      - name: Comment PR
        if: github.event_name == 'pull_request'
        run: |
          # Post results as PR comment
```

### Performance Database Schema

```json
// baseline.json
{
  "version": "0.2.8",
  "timestamp": "2025-11-18T10:00:00Z",
  "benchmarks": {
    "embedder-init-cold": {
      "mean": 2.5,
      "median": 2.4,
      "std_dev": 0.2,
      "min": 2.2,
      "max": 2.9,
      "iterations": 10
    },
    "batch-embed-100": {
      "mean": 5.2,
      "median": 5.1,
      "std_dev": 0.3,
      "min": 4.9,
      "max": 5.7,
      "iterations": 5
    }
  }
}
```

---

## Implementation Details

### Core Components

1. **Regression Test Suite** (`tests/performance/test_regression.py`)
   - One test per critical operation
   - Uses existing `Benchmark` class
   - Loads baseline, asserts <5% slower
   - Pytest markers: `@pytest.mark.performance`

2. **Baseline Management** (`tests/performance/baseline.py`)
   - Load baseline from JSON
   - Compare results
   - Update baseline (manual process)
   - Validate baseline schema

3. **CI Workflow** (`.github/workflows/performance.yml`)
   - Run on push/PR
   - Download baseline artifacts
   - Run performance tests
   - Fail if regressions detected
   - Upload results
   - Comment on PR with comparison

4. **Reporting** (`tests/performance/report.py`)
   - Generate comparison reports
   - Markdown table for PR comments
   - HTML report for artifacts
   - Performance trends visualization

### Critical Paths to Benchmark

**Must benchmark**:
1. Embedder init (cold)
2. Embedder init (warm) - after caching implemented
3. Batch embedding (10, 100, 1000 docs)
4. Query latency (first query)
5. Query latency (repeat query) - cache hit
6. Large directory scan (100+ files)
7. Index update (100, 1000, 10000 docs)

**Performance Budgets**:
- Embedder cold start: <0.5s (v0.2.9 target)
- Batch embed 100: <10s
- Query latency: <200ms (repeat)
- No operation >5% slower than baseline

---

## Edge Cases & Error Handling

### Edge Cases

1. **No baseline exists**
   - Scenario: First run, or baseline lost
   - Handling: Skip regression check, save current as baseline

2. **Baseline from different hardware**
   - Scenario: CI runs on different machine
   - Handling: Normalise by CPU/memory specs, or use percentage-based comparison

3. **Flaky benchmarks**
   - Scenario: High variance in results
   - Handling: Increase iterations, use median instead of mean

### Error Conditions

| Error Type | Trigger | Response | Recovery |
|------------|---------|----------|----------|
| `BaselineNotFoundError` | Missing baseline.json | Warning, create new baseline | User provides baseline |
| `RegressionError` | >5% slower | Fail build, show comparison | Developer investigates |
| `BenchmarkTimeoutError` | Test hangs | Kill after 5min, fail | Fix hanging code |

---

## Testing Requirements

### Unit Tests

- [ ] Test baseline loading
- [ ] Test comparison logic
- [ ] Test report generation
- [ ] Test >5% detection
- [ ] Test baseline validation

### Integration Tests

- [ ] Test full benchmark suite
- [ ] Test CI workflow (mocked)
- [ ] Test PR comment generation
- [ ] Test artifact upload

### Test Coverage Target

- **Overall**: 90%
- **Critical**: 100% (comparison logic, CI integration)

---

## Dependencies

### Internal Dependencies

- `src/utils/benchmarks.py` - Benchmark framework (exists ✅)
- `pytest>=7.0` - Test framework (installed ✅)

### External Dependencies

- `pytest-benchmark>=4.0.0` - pytest plugin for benchmarking
- GitHub Actions - CI platform (free for public repos)

---

## Success Metrics

### Functionality Metrics

| Metric | Target |
|--------|--------|
| Critical paths benchmarked | 7+ operations |
| CI integration | Works on every push/PR |
| Regression detection | Fails build if >5% slower |
| False positive rate | <5% (due to variance) |
| Historical tracking | JSON database maintained |

### Performance Metrics

- Benchmark suite runtime: <5 minutes
- CI overhead: <10 minutes total

---

## Timeline

**Estimated**: 4-5 hours

**Breakdown**:
- Regression test suite: 2h
- CI workflow setup: 1h
- Baseline management: 1h
- Reporting: 1h
- Testing & validation: 1h

---

## Related Documentation

- [v0.2.9 Roadmap](../README.md)
- [Benchmarking Framework](../../../../reference/benchmarks.md)
- [CI/CD Documentation](../../../../development/process/ci-cd.md)

---

**Status**: ✅ IMPLEMENTED (commit pending)

**Implementation Details**:

**Components Created**:
1. **BaselineManager** - Baseline management system
   - Load baselines from JSON
   - Compare current vs baseline (5% threshold)
   - Save new baselines
   - Validation and error handling
   - Automatic detection of improvements vs regressions

2. **Regression Test Suite** - Critical path benchmarks
   - embedder-init-cold: <0.5s target (was ~2-3s)
   - embedder-init-warm: <0.1s target (with caching)
   - batch-embed-10/100: Batch embedding performance
   - single-embed: Single document embedding
   - query-embed: Query embedding (shorter text)
   - hash-content: Content hashing performance
   - All tests compare against baseline with 5% threshold

3. **Baseline Database** - JSON-based performance tracking
   - Stores mean, median, std_dev, min, max, iterations
   - Version tracking
   - Timestamp metadata
   - 7 critical benchmarks defined

**Files Created**:
- `tests/performance/baseline.py` (160 lines)
- `tests/performance/test_baseline.py` (240 lines, 20+ tests)
- `tests/performance/test_regression.py` (180 lines, 7 benchmarks)
- `tests/performance/baseline.json` (baseline data)
- `tests/performance/README.md` (documentation)

**Features**:
- Automated regression detection (>5% slower = fail)
- Improvement detection (logs when faster)
- Graceful handling of missing baselines
- Pytest markers: @pytest.mark.performance, @pytest.mark.slow
- Integration with existing Benchmark framework
- Easy baseline updates after validation

**Usage**:
```bash
# Run all performance tests
pytest tests/performance/ -v -m performance

# Run only fast tests
pytest tests/performance/ -v -m "performance and not slow"

# Update baseline after improvements
python -c "from tests.performance.baseline import BaselineManager; ..."
```

**Next Steps** (CI integration pending):
- Create `.github/workflows/performance.yml`
- Configure artifact storage for baselines
- PR comment generation with results
- Automatic baseline validation
