# Ragged v0.2.5 Roadmap - Code Quality & Bug Fixes

**Status**: ✅ COMPLETE (Released 2025-11-17)
**Total Hours**: ~15 hours actual (36-48h estimated implementation, significantly optimised)
**Focus**: Eliminate technical debt, fix remaining bugs, improve code quality
**Breaking Changes**: None

---

## Overview

Version 0.2.5 was a comprehensive code quality release that addressed critical technical debt. Successfully completed with all 12 planned quality improvements implemented.

**Achievements:**
- Zero mypy --strict errors across 46 files
- +70 new tests added
- 100% test coverage for citation formatter
- 26 exception handlers improved
- 13 magic numbers extracted to constants

**See:** [v0.2.5 Implementation Record](../../implementation/version/v0.2/v0.2.5.md) | [CHANGELOG](../../../../CHANGELOG.md#025---2025-11-17)

---

## PART 1: CRITICAL BUG FIXES (12-16 hours)

### QUALITY-001: Fix Settings Side Effects (2 hours)

**Problem**: Settings class creates directories during initialization (`model_post_init`), causing:
- Test pollution and failures
- Permission errors in Docker
- Side effects during object construction (anti-pattern)

**Files**:
- `src/config/settings.py` (modify)
- All modules using `get_settings()` (update call sites)
- `tests/config/test_settings.py` (add new tests)

**Implementation**:
1. Add `ensure_data_dir() -> Path` method for lazy directory creation
2. Remove `self.data_dir.mkdir()` from `model_post_init`
3. Update ~15 call sites to use `ensure_data_dir()` when needed
4. Add environment variable support (already exists via Pydantic)
5. Add tests verifying no side effects during instantiation

**Success Criteria**:
- ✅ `Settings()` instantiation has zero side effects
- ✅ All tests pass without filesystem permissions
- ✅ Directory created only when explicitly needed
- ✅ Works in all environments (Docker, CI/CD, local)

---

### QUALITY-002: Fix Bare Exception Handler (15 minutes)

**Problem**: Bare `except:` at `src/ingestion/loaders.py:280` catches system exits and keyboard interrupts

**Security Risk**: HIGH - Can mask critical errors, prevent graceful shutdown

**File**: `src/ingestion/loaders.py:280`

**Current Code**:
```python
try:
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(html, "html.parser")
    if soup.title and soup.title.string:
        title = soup.title.string.strip()
except:  # ❌ BARE EXCEPT
    pass
```

**Fix**:
```python
except (ImportError, AttributeError) as e:
    logger.debug(f"Could not extract title from HTML: {e}")
```

**Success Criteria**:
- ✅ Zero bare `except:` handlers in codebase
- ✅ Specific exception types identified
- ✅ Error logged with context

---

### QUALITY-003: Implement 13 Skipped Chunking Tests (6-8 hours)

**Problem**: 13 tests in `tests/chunking/test_splitters.py` marked as `TODO: Implement`
- Current coverage: 0%
- Target coverage: >80%

**File**: `tests/chunking/test_splitters.py`

**Tests to Implement**:
1. `test_split_text_basic` (line 16) - Basic splitting functionality
2. `test_split_text_empty` (line 24) - Empty string handling
3. `test_split_text_small` (line 32) - Text smaller than chunk size
4. `test_chunk_overlap` (line 41) - Overlap verification
5. `test_separators_hierarchy` (line 50) - Separator precedence
6. `test_long_chunk_handling` (line 60) - Chunks exceeding size
7. `test_unicode_handling` (line 69) - Special characters
8. `test_page_tracking_pdf` (line 77) - PDF page numbers
9. `test_page_tracking_text` (line 92) - Non-PDF documents (TXT/MD/HTML)
10. `test_page_range_spanning` (line 101) - Multi-page chunks
11. `test_chunk_metadata` (line 112) - Metadata correctness
12. `test_document_with_no_pages` (line 126) - TXT/MD handling
13. `test_chunk_position_tracking` (line 140) - Position accuracy

**Implementation Plan**:
- Part 1 (3-4h): Tests 1-7 (basic functionality)
- Part 2 (3-4h): Tests 8-13 (page tracking, metadata)

**Success Criteria**:
- ✅ All 13 tests implemented and passing
- ✅ >80% coverage on `src/chunking/splitters.py`
- ✅ Edge cases documented in test names

---

### QUALITY-004: Fix Top 10 Generic Exception Handlers (4 hours)

**Problem**: 38 instances of generic `except Exception` should be specific types

**Priority**: Fix top 10 by impact (Part 1 of 2)

**Affected Files** (top 10):
1. `src/generation/ollama_client.py:102` - API calls
2. `src/generation/ollama_client.py:142` - Stream handling
3. `src/web/api.py:93` - Query endpoint
4. `src/web/api.py:195` - Upload endpoint
5. `src/main.py:223` - CLI add command
6. `src/main.py:297` - CLI query command
7. `src/ingestion/loaders.py:107` - PDF loading
8. `src/ingestion/loaders.py:150` - TXT loading
9. `src/embeddings/ollama_embedder.py:73` - Embedding generation
10. `src/retrieval/retriever.py:90` - Vector retrieval

**Fix Pattern**:
```python
# Before:
try:
    result = risky_operation()
except Exception as e:
    logger.error(f"Failed: {e}")

# After:
try:
    result = risky_operation()
except (SpecificError1, SpecificError2) as e:
    raise CustomError(f"Operation failed: {e}") from e
except Exception as e:
    logger.error(f"Unexpected error: {e}")
    raise  # Re-raise unexpected errors
```

**Success Criteria**:
- ✅ Top 10 handlers use specific exception types
- ✅ All errors logged with context
- ✅ Exception chaining preserved (`from e`)

---

## PART 2: HIGH PRIORITY QUALITY IMPROVEMENTS (18-24 hours)

### QUALITY-005: Extract Magic Numbers to Constants (2-3 hours)

**Problem**: 50+ hardcoded numeric literals without named constants

**Create**: `src/config/constants.py`

**Constants to Extract**:
```python
# Service Defaults
OLLAMA_DEFAULT_PORT = 11434
CHROMA_DEFAULT_PORT = 8001
GRADIO_DEFAULT_PORT = 7860

# Chunking
DEFAULT_CHUNK_SIZE_TOKENS = 500
DEFAULT_CHUNK_OVERLAP_TOKENS = 100
CHARS_PER_TOKEN_ESTIMATE = 4
MAX_CONTEXT_TOKENS = 2000

# Embeddings
MINILM_EMBEDDING_DIM = 384
MPNET_EMBEDDING_DIM = 768
NOMIC_EMBEDDING_DIM = 768

# Model Context Windows
LLAMA3_1_CONTEXT_WINDOW = 128000
LLAMA3_2_CONTEXT_WINDOW = 8192
QWEN_CONTEXT_WINDOW = 32768
MIXTRAL_CONTEXT_WINDOW = 4096

# Retrieval
DEFAULT_RETRIEVAL_K = 5
MAX_RETRIEVAL_K = 50

# Memory Management
DEFAULT_MEMORY_LIMIT_PERCENTAGE = 0.8

# Display
PROGRESS_BAR_WIDTH = 100
MAX_DISPLAY_ITEMS = 1000
```

**Files to Update** (10+):
- `src/config/settings.py` (10+ magic numbers)
- `src/chunking/splitters.py` (4 chars per token)
- `src/generation/prompts.py` (2000 max tokens)
- `src/config/model_manager.py` (context windows)
- `src/main.py` (display limits)
- `src/generation/few_shot.py` (embedding dims)
- Others as identified

**Success Criteria**:
- ✅ All magic numbers in critical paths replaced
- ✅ Constants module with clear categories
- ✅ All tests still pass

---

### QUALITY-006: Add Missing Type Hints (6-8 hours)

**Problem**: ~78 functions missing return type hints
- Current: ~85% type hint coverage
- Target: 100% coverage, `mypy --strict` passes

**Approach**:
1. **Part 1 - Setup** (2h):
   - Run `mypy --strict src/` to baseline errors
   - Add `from __future__ import annotations` to all modules
   - Document current error count

2. **Part 2 - Core Modules** (2-3h):
   - `src/config/` (Settings, model_manager, constants)
   - `src/exceptions.py` (all exception classes)
   - `src/ingestion/models.py` (Document, Chunk, Metadata)

3. **Part 3 - Remaining** (2-3h):
   - ~50 remaining functions across all modules
   - Focus: public APIs, complex functions
   - Add type stubs for third-party libs if needed

**Type Hint Guidelines**:
- All `__init__` methods → `-> None`
- All public functions → explicit return types
- Optional parameters → `| None`
- Complex data → `TypedDict` or `dataclass`

**Success Criteria**:
- ✅ `mypy --strict src/` passes with 0 errors
- ✅ 100% type hint coverage
- ✅ IDE autocomplete fully functional

---

### QUALITY-007: Fix Remaining Exception Handlers (4-6 hours)

**Problem**: 28 remaining generic `except Exception` handlers (after QUALITY-004)

**Priority**: Fix all remaining handlers (Part 2 of 2)

**Affected Modules**:
- `src/web/` (4 handlers) - User-facing endpoints
- `src/generation/` (5 handlers) - Core generation logic
- `src/main.py` (6 handlers) - CLI commands
- `src/retrieval/` (3 handlers) - Query-critical paths
- `src/ingestion/` (5 handlers) - Data processing
- Others (5 handlers)

**Implementation Plan**:
- Part 1 (2-3h): web/ + generation/ (9 handlers)
- Part 2 (2-3h): main.py + retrieval/ + ingestion/ + others (19 handlers)

**Success Criteria**:
- ✅ <10 generic `except Exception` remaining (down from 38)
- ✅ All user-facing code has specific error handling
- ✅ Error messages actionable and contextual

---

### QUALITY-008: Implement 5 Citation Parser Tests (2-3 hours)

**Problem**: 5 tests in `tests/generation/test_response_parser.py` marked as TODO
- Current coverage: 0% (citation extraction not tested)
- Target coverage: >70%

**File**: `tests/generation/test_response_parser.py`

**Tests to Implement**:
1. `test_extract_ieee_citations` (line 13) - IEEE format [1], [2] parsing
2. `test_extract_inline_citations` (line 23) - Inline citation detection
3. `test_format_citation_list` (line 33) - Reference list formatting
4. `test_citation_deduplication` (line 43) - Duplicate handling
5. `test_malformed_citations` (line 53) - Error handling for bad citations

**Success Criteria**:
- ✅ All 5 tests implemented and passing
- ✅ >70% coverage on `src/generation/response_parser.py`
- ✅ Citation edge cases documented

---

### QUALITY-009: Clean Up TODO Comments (2-4 hours)

**Problem**: 11 TODO comments in codebase
- 8 obsolete (already implemented)
- 1 quick win (can implement now)
- 2 deferred (create GitHub issues)

**Part 1 - Remove Obsolete** (1h):
- `src/embeddings/base.py:33,48,62,77,91` - "Implement in subclasses" (done)
- `src/embeddings/factory.py:34,72` - "Implement factory logic" (done)
- `src/embeddings/ollama_embedder.py:48` - "Implement initialisation" (done)

**Part 2 - Quick Win** (1h):
- `src/chunking/contextual.py:140` - "Calculate actual overlap"
  - Implement text overlap calculation between adjacent chunks
  - ~1 hour effort

**Part 3 - Create GitHub Issues** (30min):
- `src/retrieval/retriever.py:151` - "Implement context retrieval (v0.2 feature)"
  - Create issue: "Feature: Context-aware retrieval" (v0.3)
- `src/chunking/contextual.py:261` - "Implement token-based truncation"
  - Create issue: "Feature: Token-based context truncation" (v0.3)
- Update TODOs with issue references

**Success Criteria**:
- ✅ 0 obsolete TODO comments
- ✅ 1 TODO implemented (contextual overlap)
- ✅ 2 TODOs linked to GitHub issues

---

## PART 3: OPTIONAL IMPROVEMENTS (4-6 hours)

### QUALITY-010: Add Exception Chaining (2 hours)

**Problem**: Missing `from e` in re-raised exceptions loses context

**Pattern**:
```python
# Before:
except OriginalError as e:
    raise CustomError("Failed")  # Lost context

# After:
except OriginalError as e:
    raise CustomError("Failed") from e  # Preserved
```

**Scope**: All exception re-raising throughout codebase

**Success Criteria**:
- ✅ All re-raised exceptions use `from e`
- ✅ Full stack traces in error logs

---

### QUALITY-011: Implement Contextual Chunker Overlap (1 hour)

**Problem**: `src/chunking/contextual.py:140` - Overlap hardcoded to 0

**Implementation**: Calculate actual text overlap between adjacent chunks

**Success Criteria**:
- ✅ Overlap calculation implemented
- ✅ Tests verify overlap accuracy

---

### QUALITY-012: Add Missing Integration Test (30 minutes)

**Problem**: `tests/integration/test_multiformat.py:155` - PDF fixture missing

**Implementation**: Add PDF fixture, enable skipped test

**Success Criteria**:
- ✅ 0 skipped integration tests

---

## Testing Strategy

### Unit Tests
- Minimum coverage: 80% on modified modules
- Run: `pytest tests/ --cov=src --cov-report=html`
- Focus: New code, modified logic, edge cases

### Integration Tests
- Verify Settings changes work end-to-end
- Test exception handling across modules
- Run: `pytest tests/integration/ -v`

### Type Checking
- Must pass: `mypy --strict src/`
- Zero `type: ignore` without justification
- Run: `mypy --strict src/ --show-error-codes`

### Manual Testing Checklist
- [ ] CLI commands functional (add, query, config)
- [ ] Web UI functional (upload, query)
- [ ] Docker build successful
- [ ] All README examples work

---

## Success Criteria

### Code Quality Metrics (Quantified)

| Metric | Before | After | Improvement |
|--------|--------|-------|-------------|
| Bare `except:` | 1 | 0 | ✅ 100% |
| Generic `except Exception` | 38 | <10 | ✅ 74% reduction |
| Obsolete TODOs | 8 | 0 | ✅ 100% |
| Magic numbers (critical) | 50+ | 0 | ✅ 100% |
| Type hints coverage | ~85% | 100% | ✅ 15% increase |
| Test coverage (avg) | ~60% | >80% | ✅ 20% increase |

### Test Metrics

| Test Category | Before | After | Added |
|---------------|--------|-------|-------|
| Chunking tests | 0 | 13 | +13 |
| Citation parser tests | 0 | 5 | +5 |
| Integration tests | 39 | 40 | +1 |
| **Total new tests** | - | - | **18** |
| Skipped tests (critical) | 19 | 0 | -19 |

### Documentation Metrics
- ✅ Planning docs complete
- ✅ Roadmap docs complete
- ✅ Implementation docs with lineage
- ✅ CHANGELOG updated
- ✅ Release notes published

---

## Files Modified

### New Files (1)
- `src/config/constants.py` - Centralised constants module

### Modified Files (20-30 estimated)

**Core**:
- `src/config/settings.py` - Lazy directory creation
- `src/ingestion/loaders.py` - Fixed bare except
- `src/chunking/splitters.py` - Magic numbers
- `src/chunking/contextual.py` - Overlap calculation

**Exception Handling** (10+ files):
- `src/generation/ollama_client.py`
- `src/web/api.py`
- `src/main.py`
- `src/ingestion/loaders.py`
- `src/embeddings/ollama_embedder.py`
- `src/retrieval/retriever.py`
- Others

**Type Hints** (all source files):
- All 45 Python files updated

**Tests**:
- `tests/chunking/test_splitters.py` - 13 tests implemented
- `tests/generation/test_response_parser.py` - 5 tests implemented
- `tests/integration/test_multiformat.py` - 1 test enabled

---

## Implementation Sequence

### Phase 1: Planning (3-4h)
→ Create planning/roadmap docs
→ Run documentation audit
→ Commit planning

### Phase 2: Critical Fixes (12-16h)
→ Settings side effects
→ Bare except handler
→ 13 chunking tests
→ Top 10 exception handlers

### Phase 3: High Priority Part 1 (10-12h)
→ Magic numbers extraction
→ Type hints setup + core modules

### Phase 4: High Priority Part 2 (8-12h)
→ Type hints completion
→ Remaining exception handlers
→ Citation parser tests
→ TODO cleanup

### Phase 5: Optional (4-6h)
→ Exception chaining
→ Contextual overlap
→ Integration test

### Phase 6: Validation (2-3h)
→ Full test suite
→ Type checking
→ Manual testing
→ Performance comparison

### Phase 7: Documentation (6-8h)
→ Devlog, time log
→ Release notes, lineage
→ CHANGELOG update
→ Documentation audit

### Phase 8: Release (2-3h)
→ Version bump
→ GitHub release
→ README updates

---

## Known Risks

1. **Type Hint Migration**: Some third-party libraries may need stubs
2. **Exception Specificity**: Identifying correct exception types may require testing
3. **Test Implementation**: Chunking tests may reveal edge cases
4. **Magic Numbers**: Some constants may need configuration hierarchy

---

## Dependencies

**Requires**:
- ✅ v0.2.4 complete (all 8 bugs fixed)

**Blocks**:
- v0.2.6 (structural improvements)
- v0.2.7 (new features)

**External**:
- Python 3.12.x
- All existing dependencies (no additions)

---

## Next Version

After v0.2.5 completion:
- **v0.2.6**: Documentation & structural improvements (24-35h)
- See: [v0.2.6 Roadmap](../v0.2.6/README.md)

---

## Related Documentation

- [v0.2.5 Design Goals](../../planning/version/v0.2/v0.2.5-design.md) - Vision and decisions
- [v0.2.5 Implementation](../../implementation/version/v0.2/v0.2.5.md) - What was built
- [v0.2.5 Time Log](../../process/time-logs/version/v0.2/v0.2.5-time-log.md) - Development timeline
- [v0.2.4 Roadmap](../v0.2.4/README.md) - Previous version
- [v0.2.6 Roadmap](../v0.2.6/README.md) - Next version

