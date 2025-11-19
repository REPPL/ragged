# Performance Regression Tests

**Purpose**: Automated benchmarking to detect performance regressions (>5% slower than baseline).

## Files

- `baseline.py` - Baseline management (load, compare, validate)
- `baseline.json` - Performance baselines for v0.2.9
- `test_baseline.py` - Tests for baseline management
- `test_regression.py` - Regression tests for critical paths

## Running Tests

```bash
# Run all performance tests
pytest tests/performance/ -v -m performance

# Run only fast performance tests (exclude slow)
pytest tests/performance/ -v -m "performance and not slow"

# Run with verbose benchmark output
pytest tests/performance/test_regression.py -v -s
```

## Benchmarks

| Benchmark | Target | Baseline |
|-----------|--------|----------|
| embedder-init-cold | <0.5s | 0.45s |
| embedder-init-warm | <0.1s | 0.08s |
| batch-embed-10 | <2s | 1.5s |
| batch-embed-100 | <10s | 9.5s |
| single-embed | <0.2s | 0.15s |
| query-embed | <0.1s | 0.08s |
| hash-content | <0.001s | 0.0008s |

## Updating Baselines

After confirming performance improvements:

```python
from tests.performance.baseline import BaselineManager, BenchmarkResult

manager = BaselineManager()

# Run benchmarks and collect results
benchmarks = {
    "embedder-init-cold": BenchmarkResult(0.45, 0.44, 0.05, 0.40, 0.55, 10),
    # ... other benchmarks
}

# Save new baseline
manager.save_baseline("0.2.9", benchmarks)
```

## CI Integration

Performance tests run automatically in CI on every push/PR. Build fails if any benchmark is >5% slower than baseline.

See `.github/workflows/performance.yml` for CI configuration.

## Threshold

**5% regression threshold**: Tests fail if current performance is >5% slower than baseline.

This allows for minor variance while catching significant regressions.
