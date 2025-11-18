# Ragged v0.2.3 Roadmap - Critical Bug Fixes

**Status:** ⊗ SKIPPED - Resolved in subsequent versions (v0.2.4, v0.2.5)

**Total Hours:** N/A (not implemented as planned)

**Focus:** P0 critical bugs that block core functionality

**Breaking Changes:** None

---

## Overview

Version 0.2.3 was originally planned to address three critical P0 bugs. However, this version was **skipped** in favour of addressing issues incrementally across v0.2.4 and v0.2.5.

**Originally Planned:**
1. BUG-001: API endpoints non-functional (blocks Web UI)
2. BUG-002: Logger undefined (runtime crash)
3. BUG-003: Zero test coverage for 606 lines of code

**Actual Resolution:**
- BUG-001: Fixed during API refactoring in v0.2.4
- BUG-002: Resolved by settings refactoring in v0.2.5 (QUALITY-001)
- BUG-003: Addressed by comprehensive test additions in v0.2.4 and v0.2.5

**See:** [v0.2.3 Implementation Record (Skipped)](../../implementation/version/v0.2/v0.2.3-skipped.md)

---

## BUG-001: API Endpoints Non-Functional (4 hours)

**Problem:** All FastAPI endpoints return placeholder data. Web UI completely non-functional.

**Implementation:**

1. Initialise services in startup event (src/web/api.py:50-105) [1.5 hours]
   - Add HybridRetriever, OllamaClient, Settings globals
   - Initialise in @app.on_event("startup")
   - Load vector store, embedder, retrievers

2. Implement /api/query endpoint (src/web/api.py:110-150) [1.5 hours]
   - Retrieve with hybrid_retriever
   - Build context from results
   - Generate answer with ollama_client
   - Format sources

3. Implement /api/upload endpoint (src/web/api.py:155-206) [1 hour]
   - Save temp file
   - Load, chunk, embed document
   - Store in vector database
   - Clean up temp file

**Files:** src/web/api.py

**⚠️ MANUAL TEST REQUIRED:**
- Upload document via Web UI, verify stored in database
- Query via Web UI, verify real answer returned (not placeholder)
- Test error handling with invalid file upload
- Test concurrent requests don't crash

**Success Criteria:**
- [ ] Web UI can upload documents successfully
- [ ] Web UI queries return real answers with citations
- [ ] ⚠️ MANUAL: User confirms Web UI functional end-to-end

---

## BUG-002: Logger Undefined (30 minutes)

**Problem:** `logger.info()` and `logger.warning()` called but logger never imported in src/config/settings.py:149, 159. Causes `NameError`.

**Implementation:**

Add import at top of file (src/config/settings.py:1-10) [30 minutes]

```python
from src.utils.logging import get_logger

logger = get_logger(__name__)
```

**Files:** src/config/settings.py

**⚠️ MANUAL TEST REQUIRED:**
- Load config with .env file present, verify log message
- Load config with .env missing, verify warning

**Success Criteria:**
- [ ] No NameError when loading config
- [ ] ⚠️ MANUAL: User confirms log messages appear correctly

---

## BUG-003: Zero Test Coverage for New Modules (8 hours)

**Problem:** Three modules have 0% test coverage (606 lines):
- src/ingestion/scanner.py (243 lines)
- src/ingestion/batch.py (205 lines)
- src/config/model_manager.py (158 lines)

**Implementation:**

1. Create tests/ingestion/test_scanner.py [3 hours]
   - Test directory scanning (all formats)
   - Test recursive flag
   - Test empty directory handling
   - Test symlink handling
   - Test hidden file filtering

2. Create tests/ingestion/test_batch.py [3 hours]
   - Test batch ingestion multiple documents
   - Test progress tracking
   - Test error handling (continue on failure)
   - Test duplicate detection
   - Test memory usage

3. Create tests/config/test_model_manager.py [2 hours]
   - Test model availability checking
   - Test model downloading with user consent
   - Test model caching
   - Test offline mode

**Files:**
- tests/ingestion/test_scanner.py (new)
- tests/ingestion/test_batch.py (new)
- tests/config/test_model_manager.py (new)

**⚠️ MANUAL TEST REQUIRED:**
- Run pytest, verify all tests pass
- Check coverage report shows >80% for these modules

**Success Criteria:**
- [ ] test_scanner.py: ≥80% coverage of scanner.py
- [ ] test_batch.py: ≥80% coverage of batch.py
- [ ] test_model_manager.py: ≥80% coverage of model_manager.py
- [ ] ⚠️ MANUAL: User verifies pytest passes, coverage reports acceptable

---

## Success Criteria (Test Checkpoints)

**Automated:**
- [ ] All new tests pass (BUG-003)
- [ ] No NameError in settings (BUG-002)
- [ ] API endpoints return real data (BUG-001)

**Manual Testing:**
- [ ] ⚠️ MANUAL: Web UI functional end-to-end (upload + query)
- [ ] ⚠️ MANUAL: Log messages appear correctly
- [ ] ⚠️ MANUAL: Test coverage ≥80% for new modules

**Quality Gates:**
- [ ] All existing tests still pass
- [ ] No new warnings in logs
- [ ] Web UI works in production mode

---

## Known Risks

**BUG-001 Risks:**
- May discover additional missing integrations
- Error handling might need iteration
- Performance testing needed for concurrent requests

**BUG-002 Risks:**
- Minimal risk (trivial fix)

**BUG-003 Risks:**
- Tests might reveal hidden bugs in modules
- Coverage might identify edge cases not yet handled
- Test writing might take longer than estimated (complex logic)

---

## Related Documentation

- [Next Version](../v0.2.4/README.md) - High priority bugs (P1)
- [Planning](../../planning/version/v0.2/) - Design goals for v0.2 series
- [Version Overview](../README.md) - Complete version comparison

---

## Next Version

After v0.2.3 completion:
- **v0.2.4:** High priority bugs (P1)
- See: `roadmap/version/v0.2.4/README.md`
