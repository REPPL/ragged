# Testing Documentation

**Purpose:** Testing strategies and test plans

**Last Updated:** 2025-11-17

---

## Overview

This directory contains testing strategies, test plans, and testing-related documentation for ragged features.

---

## Contents

- [model-selection-testing.md](./model-selection-testing.md) - Dynamic model selection testing strategy

---

## Current Test Coverage

**As of v0.2.9-P1 (2025-11-17):**
- **Total Tests:** 667 passing unit tests
- **Code Coverage:** 58% overall
- **Test Files:** 24+ test modules

**Feature Coverage:**
- Hybrid retrieval: 100% tested
- BM25 search: 100% tested
- Citation extraction: 100% tested
- Document deduplication: 100% tested
- CLI commands: Comprehensive test suite (113 tests)
- Response parsing: Full coverage
- Batch ingestion: Complete test coverage
- Document loaders: All formats tested

---

## Testing Approach

ragged uses a hybrid testing approach:
- **Unit Tests:** Core logic and algorithms (667 tests)
- **Integration Tests:** Component interactions and workflows
- **Evaluation Tests:** RAG quality metrics (retrieval, generation)

---

## For Contributors

When adding new features:
1. Create unit tests for core logic
2. Add integration tests for component interactions
3. Define evaluation metrics for quality assessment
4. Document testing strategy in this directory

---

## Related Documentation

- [Testing Results](../../implementation/version/) - Per-version test results
- [Evaluation Framework](../../planning/core-concepts/evaluation.md) - Quality metrics

---


**License:** GPL-3.0
