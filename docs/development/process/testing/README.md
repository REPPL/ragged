# Testing Documentation

**Purpose:** Testing strategies and test plans

**Last Updated:** 2025-11-15

---

## Overview

This directory contains testing strategies, test plans, and testing-related documentation for ragged features.

---

## Contents

- [model-selection-testing.md](./model-selection-testing.md) - Dynamic model selection testing strategy

---

## Testing Approach

ragged uses a hybrid testing approach:
- **Unit Tests:** Core logic and algorithms
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

- [Testing Results](../../implementations/version/) - Per-version test results
- [Evaluation Framework](../../planning/core-concepts/evaluation.md) - Quality metrics

---

**Maintained By:** ragged development team

**License:** GPL-3.0
