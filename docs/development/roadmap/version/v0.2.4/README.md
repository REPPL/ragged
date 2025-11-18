# Ragged v0.2.4 Roadmap - High Priority Bugs

**Status:** Planned

**Total Hours:** 20-25 hours (AI implementation)

**Focus:** P1 high priority bugs affecting quality and functionality

**Breaking Changes:** None

---

## Overview

Version 0.2.4 addresses 8 high-priority bugs that significantly impact quality. Must complete v0.2.3 first.

**Dependencies:** Requires v0.2.3 completion (critical bugs fixed)

---

## BUG-004: Inconsistent Error Handling (4-5 hours)

**Problem:** Error handling inconsistent across codebase - silent failures, bare except blocks, unhelpful error messages.

**Implementation:**
1. Create src/exceptions.py with custom exceptions [1 hour]
2. Audit all 47 try/except blocks [1 hour]
3. Replace bare except blocks with specific exceptions [2 hours]
4. Add context to error logs [0.5-1 hour]

**Files:** src/exceptions.py (new), src/ingestion/loaders.py, src/embeddings/*, src/retrieval/*, src/generation/ollama_client.py, src/main.py

**⚠️ MANUAL TEST:** Trigger various error scenarios, verify error messages actionable and properly logged

**Success:** Custom exceptions used, no bare except blocks, errors logged with context

---

## BUG-005: Path Handling Edge Cases (3-4 hours)

**Problem:** Path handling doesn't handle symlinks, relative paths, special characters, spaces consistently.

**Implementation:**
1. Create src/utils/paths.py with normalisation utilities [2 hours]
2. Add path validation (exists, is_file, allowed suffixes) [1 hour]  
3. Update all modules to use new utilities [0.5-1 hour]

**Files:** src/utils/paths.py (new), src/ingestion/*, src/main.py

**⚠️ MANUAL TEST:** Test with symlinks, spaces in filenames, special characters, relative paths

**Success:** All paths normalised consistently, edge cases handled gracefully

---

## BUG-006: Memory Leaks in Batch Processing (3-4 hours)

**Problem:** Large batch processing shows increasing memory usage, potential OOM on large document sets.

**Implementation:**
1. Add memory profiling to identify leaks [1 hour]
2. Clear embedder cache after each document [1 hour]
3. Add explicit gc.collect() calls [30 minutes]
4. Add memory monitoring and warnings [0.5-1 hour]

**Files:** src/ingestion/batch.py, src/embeddings/*.py

**⚠️ MANUAL TEST:** Process 50+ documents, monitor memory usage stays stable

**Success:** Memory usage stable during large batches, no OOM errors

---

## BUG-007: ChromaDB Metadata Type Restrictions (2-3 hours)

**Problem:** ChromaDB only accepts str, int, float, bool for metadata. Lists/dicts cause errors.

**Implementation:**
1. Add metadata serialisation layer [1.5 hours]
2. Convert complex types to JSON strings [0.5 hour]
3. Update retrieval to deserialise [0.5-1 hour]

**Files:** src/storage/vector_store.py, src/retrieval/retriever.py

**⚠️ MANUAL TEST:** Ingest document with complex metadata (lists, dicts), verify retrieval works

**Success:** All metadata types supported, no type errors from ChromaDB

---

## BUG-008: Incomplete Hybrid Retrieval Integration (2-3 hours)

**Problem:** Hybrid retriever exists but isn't integrated everywhere - some code still uses only vector retrieval.

**Implementation:**
1. Audit all retrieval call sites [30 minutes]
2. Replace VectorRetriever with HybridRetriever [1 hour]
3. Update tests to use hybrid retrieval [0.5-1 hour]
4. Add configuration for retrieval strategy [0.5 hour]

**Files:** src/main.py, src/web/api.py, tests/integration/*

**⚠️ MANUAL TEST:** Query and verify results use both BM25 and vector retrieval

**Success:** All retrieval uses hybrid by default, configurable strategy

---

## BUG-009: Few-Shot Examples Unused (2 hours)

**Problem:** Few-shot prompting infrastructure exists but examples aren't selected dynamically - always uses same examples.

**Implementation:**
1. Implement dynamic example selection based on query similarity [1 hour]
2. Add fallback if no similar examples [30 minutes]
3. Update prompts to use selected examples [30 minutes]

**Files:** src/generation/prompts.py, src/generation/ollama_client.py

**⚠️ MANUAL TEST:** Query, verify different queries get different examples

**Success:** Examples selected dynamically, improve answer quality

---

## BUG-010: Duplicate Detection Incomplete (2-3 hours)

**Problem:** Duplicate detection by file hash works, but doesn't check for content-based duplicates (same content, different filename).

**Implementation:**
1. Add content hashing (first 1KB + last 1KB) [1 hour]
2. Check both file hash and content hash [0.5 hour]
3. Add user confirmation for content duplicates [0.5 hour]
4. Update batch processing to handle duplicates [0.5-1 hour]

**Files:** src/ingestion/loaders.py, src/ingestion/batch.py

**⚠️ MANUAL TEST:** Add same document twice with different filenames, verify detection

**Success:** Detects both file-based and content-based duplicates

---

## BUG-011: Page Tracking Edge Cases (2 hours)

**Problem:** Page tracking doesn't handle:
- Documents without pages (TXT, MD)
- Multi-page spans
- PDFs with non-standard page numbering

**Implementation:**
1. Add robust page metadata handling [1 hour]
2. Add page span support (pages 5-7) [30 minutes]
3. Handle documents without pages gracefully [30 minutes]

**Files:** src/ingestion/loaders.py, src/chunking/splitters.py

**⚠️ MANUAL TEST:** Test PDFs, TXT, MD - verify page tracking appropriate for each

**Success:** Page tracking works for all document types, no crashes

---

## Success Criteria (Test Checkpoints)

**Automated:**
- [ ] All new tests pass
- [ ] No bare except blocks (code review)
- [ ] All paths normalised consistently
- [ ] Hybrid retrieval used everywhere

**Manual Testing:**
- [ ] ⚠️ MANUAL: Error messages helpful and actionable
- [ ] ⚠️ MANUAL: Memory stable during large batches (50+ docs)
- [ ] ⚠️ MANUAL: Duplicate detection works (file + content)
- [ ] ⚠️ MANUAL: Few-shot examples vary by query

**Quality Gates:**
- [ ] All existing tests pass
- [ ] No new warnings
- [ ] No memory leaks in 100-document test

---

## Known Risks

- Error handling audit might find more issues than estimated
- Memory profiling could reveal complex leak sources
- Duplicate detection might need performance optimisation
- Few-shot example selection might require tuning

---

## Next Version

After v0.2.4 completion:
- **v0.2.5:** Medium priority bugs (P2)
- See: `roadmap/version/v0.2.5/README.md`

---

**Last Updated:** 2025-11-12

**Status:** Ready for implementation after v0.2.3

---

## Related Documentation

- [Previous Version](../v0.2.3/README.md) - Critical bug fixes (P0)
- [Next Version](../v0.2.5/README.md) - Code quality improvements
- [Planning](../../planning/version/v0.2/) - Design goals for v0.2 series
- [Version Overview](../README.md) - Complete version comparison

---
