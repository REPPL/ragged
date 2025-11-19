# v0.2.9 Manual Tests

**Status:** ✅ COMPLETE
**Features:** Performance optimisation, cold start improvements, test coverage expansion, chunking enhancements
**Date Created:** 2025-11-19

---

## Overview

This directory contains manual tests for ragged v0.2.9, focusing on performance improvements and stability enhancements introduced in this release.

---

## Features Tested

- **Performance Optimisation** - Batch tuning, cold start improvements
- **Chunking Enhancements** - Token counter, recursive splitter improvements
- **Test Coverage** - Expansion to 70%+ coverage
- **Operational Excellence** - Logging, monitoring, error handling
- **Production Hardening** - Stability and reliability improvements

---

## Test Files

- `smoke_test.py` - Quick sanity check (5-10 minutes)
- `performance_optimisation_test.py` - Batch tuning, cold start tests
- `chunking_test.py` - Token counter and splitter tests
- `test_coverage_validation.py` - Coverage verification tests

---

## Running Tests

### Run all tests for this version

```bash
pytest scripts/manual_tests/version/v0.2.9/
```

### Run smoke test only

```bash
pytest scripts/manual_tests/version/v0.2.9/smoke_test.py
```

### Run specific feature tests

```bash
# Performance tests
pytest scripts/manual_tests/version/v0.2.9/ -m 'feature("performance")'

# Chunking tests
pytest scripts/manual_tests/version/v0.2.9/ -m 'feature("chunking")'

# Coverage tests
pytest scripts/manual_tests/version/v0.2.9/ -m 'feature("test_coverage")'
```

---

## pytest Markers

All tests in this directory use these markers:

- `@pytest.mark.smoke` - Quick sanity checks
- `@pytest.mark.version("v0.2.9")` - Version-specific marker
- `@pytest.mark.feature("performance")` - Performance optimisation tests
- `@pytest.mark.feature("chunking")` - Chunking enhancement tests
- `@pytest.mark.feature("test_coverage")` - Coverage validation tests
- `@pytest.mark.feature("cold_start")` - Cold start optimisation tests

---

## Feature Details

### 1. Performance Optimisation

**Phase 1: Core Performance (35-43h)**
- Batch embedding tuning with dynamic sizing
- Cold start optimisation (lazy loading)
- Query caching improvements
- Memory usage optimisation

**Key Improvements:**
- ~10% faster ingestion through batch tuning
- ~40-50% faster first query through cold start optimisation
- Reduced memory footprint

**Tests:**
- `test_batch_tuning()` - Verify dynamic batch sizing
- `test_cold_start_optimisation()` - Measure first query latency
- `test_query_caching()` - Validate cache effectiveness

### 2. Chunking Enhancements

**Improvements:**
- Token-aware chunking with accurate token counting
- Improved recursive splitter with better boundary handling
- Page tracking for PDF documents
- Overlap optimisation

**Tests:**
- `test_token_counter()` - Verify token counting accuracy
- `test_recursive_splitter()` - Test splitting logic
- `test_page_tracking()` - Validate PDF page metadata

### 3. Test Coverage Expansion

**Target:** 70%+ overall coverage (80%+ for core modules)

**Coverage Areas:**
- Chunking module: 80%+
- Embeddings module: 75%+
- Ingestion module: 80%+
- Retrieval module: 75%+
- Utilities module: 70%+

**Tests:**
- `test_coverage_metrics()` - Verify coverage thresholds met
- `test_critical_path_coverage()` - Ensure critical paths tested

### 4. Operational Excellence

**Improvements:**
- Enhanced logging (structured JSON logs)
- Better error messages
- Improved monitoring
- Resource governance

**Tests:**
- `test_logging_format()` - Validate log structure
- `test_error_messages()` - Check error clarity
- `test_resource_limits()` - Verify governance

---

## Known Issues

- None currently documented

---

## Performance Baseline

Expected performance for v0.2.9:

| Metric | Target | Notes |
|--------|--------|-------|
| Ingestion (100 docs) | < 50s | Mixed formats (PDF, MD, HTML, TXT) |
| First query latency | < 3.5s | Cold start optimisation |
| Subsequent query p95 | < 350ms | With caching |
| Memory (baseline) | < 200MB | Without documents |
| Memory (100 docs) | < 600MB | After ingestion |

---

## Related Documentation

- **Roadmap:** [v0.2.9 Roadmap](../../../docs/development/roadmap/version/v0.2/v0.2.9/README.md)
- **Implementation:** [v0.2.9 Implementation](../../../docs/development/implementation/version/v0.2/v0.2.9.md)
- **Manual Test Plan:** [v0.2.9 Manual Tests](../../../docs/development/process/testing/manual/v0.2/v0.2.9-manual-tests.md)
- **Features:**
  - [Performance Optimisation](../../../docs/development/roadmap/version/v0.2/v0.2.9/features/performance-optimisation.md)
  - [Test Coverage](../../../docs/development/roadmap/version/v0.2/v0.2.9/features/test-coverage.md)
  - [Chunking Strategies](../../../docs/development/roadmap/version/v0.2/v0.2.9/features/chunking-strategies.md)

---

**Maintained By:** ragged development team
