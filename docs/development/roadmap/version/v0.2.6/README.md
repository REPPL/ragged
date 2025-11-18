# Ragged v0.2.6 Roadmap - Documentation & Structural Improvements

**Status:** ⊗ SKIPPED/DEFERRED - Structural improvements moved to later versions

**Total Hours:** N/A (not implemented as planned)

**Focus:** Documentation completeness and structural refactoring

**Breaking Changes:** None

---

## Overview

Version 0.2.6 was originally planned for large-scale documentation and file refactoring. However, this version was **skipped/deferred** for the following reasons:

**Decision Rationale:**
1. **Avoid Churn**: Large-scale file refactoring would create merge conflicts and disrupt ongoing work
2. **Premature Optimisation**: File structure was adequate for current needs
3. **Higher Priorities**: User-facing features (CLI, folder upload, HTML) took precedence
4. **Incremental Approach**: Structural improvements better addressed incrementally in v0.2.7-v0.2.8

**Items Already Completed in v0.2.5:**
- ~~QUALITY-001: Type hints~~ → v0.2.5 QUALITY-006 ✅
- ~~QUALITY-003: TODO cleanup~~ → v0.2.5 QUALITY-009 ✅
- ~~QUALITY-005: Magic numbers~~ → v0.2.5 QUALITY-005 ✅

**Items Incorporated into v0.2.7-v0.2.8:**
- CLI modularisation (14 command modules created)
- File organisation improvements where beneficial
- Documentation updates alongside feature development

---

## QUALITY-002: Complete Google-Style Docstrings (8-10 hours)

**Problem:** Some functions lack docstrings or have minimal documentation.

**Implementation:**
1. Audit all functions for missing docstrings [1 hour]
2. Add Google-style docstrings to all public functions [4-5 hours]
3. Add docstrings to internal functions [2-3 hours]
4. Add examples to complex functions [1-2 hours]

**Format:**
```python
def example_function(param1: str, param2: int = 5) -> Dict[str, Any]:
    """
    Short one-line description.

    Longer description if needed, explaining what the function does,
    when to use it, and any important details.

    Args:
        param1: Description of param1
        param2: Description of param2 (default: 5)

    Returns:
        Dictionary containing results with keys:
            - 'result': The main result
            - 'metadata': Additional metadata

    Raises:
        ValueError: If param1 is empty
        DocumentLoadError: If document cannot be loaded

    Example:
        >>> result = example_function("test", 10)
        >>> print(result['result'])
        'test processed'
    """
```

**Files:** All modules in src/ with incomplete documentation

**⚠️ MANUAL TEST:** Review generated documentation, verify completeness and clarity

**Success:** All public functions have complete Google-style docstrings with examples for complex functions

---

## QUALITY-004: Eliminate Code Duplication (4-6 hours)

**Problem:** Some code duplication exists beyond what was addressed in v0.2.4/v0.2.5.

**Implementation:**
1. Run ruff to find duplicate code blocks [1 hour]
2. Identify patterns for extraction [1 hour]
3. Extract common patterns to utilities [1-2 hours]
4. Update all call sites [1-2 hours]

**Common patterns to extract:**
- Repeated validation logic
- Common data transformations
- Shared formatting code
- Error handling patterns

**Files:** All modules with duplicated code patterns

**⚠️ MANUAL TEST:** Review extracted utilities, verify no functionality broken

**Success:** No significant code duplication, shared logic in utilities modules

---

## QUALITY-006: File Length Refactoring (6-10 hours)

**Problem:** 9 files exceed 300 lines, making them harder to navigate and maintain.

**Files Exceeding 300 Lines:**
1. `src/main.py` (586 lines) - CLI commands
2. `src/web/gradio_ui.py` (497 lines) - UI components
3. `src/generation/few_shot.py` (424 lines) - Storage + matching
4. `src/chunking/splitters.py` (404 lines) - Recursive splitting
5. `src/utils/benchmarks.py` (400 lines) - Profiling + analysis
6. `src/ingestion/async_processor.py` (376 lines) - Batch + async
7. `src/web/api.py` (364 lines) - Endpoint handlers
8. `src/utils/path_utils.py` (341 lines) - Path utilities
9. `src/exceptions.py` (327 lines) - Already well-organised ✅

**Priority Refactoring** (focus on top 4):

### 1. `src/main.py` (2-3 hours)
**Strategy:** Split CLI commands into separate modules
- Create `src/cli/` directory
- Move commands to: `add.py`, `query.py`, `config.py`, `web.py`
- Keep `main.py` as entry point with command registration

### 2. `src/web/gradio_ui.py` (2-3 hours)
**Strategy:** Extract API client and separate UI components
- Create `src/web/gradio_client.py` for API interactions
- Create `src/web/gradio_components.py` for reusable UI elements
- Keep `gradio_ui.py` for layout and configuration

### 3. `src/generation/few_shot.py` (1-2 hours)
**Strategy:** Split storage logic from example matching
- Keep `few_shot.py` for matching logic
- Move storage to `few_shot_store.py`
- Potential for future database-backed storage

### 4. `src/chunking/splitters.py` (1-2 hours)
**Strategy:** Extract recursive splitting logic
- Keep `splitters.py` for `RecursiveCharacterTextSplitter`
- Extract page tracking helpers to `page_tracking.py`
- Clearer separation of concerns

**Success Criteria:**
- ✅ No files >400 lines (except exceptions.py which is acceptable)
- ✅ Clear module responsibilities
- ✅ All imports updated
- ✅ All tests still pass

---

## QUALITY-007: Complex Function Extraction (4-6 hours)

**Problem:** Some functions have high cyclomatic complexity, making them hard to test and maintain.

**Target Functions:**

### 1. `src/chunking/splitters.py:_split_recursive` (2 hours)
**Lines:** 43-89
**Complexity:** High (recursive with multiple conditionals)
**Strategy:** Extract separator handling and overlap logic to helper methods

### 2. `src/main.py:add` command (2-3 hours)
**Lines:** 43-230 (~190 lines)
**Complexity:** Very high (handles files + directories + progress + errors)
**Strategy:** Extract directory scanning, progress reporting, error handling to separate functions

### 3. `src/web/api.py:query_endpoint` (1-2 hours)
**Lines:** ~150-250
**Complexity:** High (streaming + non-streaming modes)
**Strategy:** Extract stream handling to dedicated function

**Implementation Plan:**
1. Identify extraction boundaries [1 hour]
2. Extract first function (splitters) [1 hour]
3. Extract second function (main.py) [1-2 hours]
4. Extract third function (api.py) [1 hour]
5. Update tests [1 hour]

**Success Criteria:**
- ✅ No function >50 lines (excluding data structures)
- ✅ Each function has single responsibility
- ✅ Complexity reduced, tests easier to write

---

## QUALITY-008: Add Usage Examples to Docstrings (2-3 hours)

**Problem:** Complex functions lack practical usage examples.

**Target Modules:**

### 1. `src/chunking/contextual.py:ContextualChunker` (30min)
Add example showing:
- Initialisation
- Processing a document
- Accessing chunks with context

### 2. `src/retrieval/fusion.py:ReciprocalRankFusion` (30min)
Add example showing:
- Combining vector and BM25 results
- Fusion parameters
- Output format

### 3. `src/generation/few_shot.py:FewShotManager` (30min)
Add example showing:
- Adding examples
- Searching for similar examples
- Using in prompt generation

### 4. Core Data Models (30min)
Add examples to:
- `Document.from_file()`
- `chunk_document()`
- `Chunk` creation

### 5. Configuration (30min)
Add examples for:
- `Settings` usage
- Custom configuration
- Environment variables

**Format:**
```python
"""
...

Example:
    Basic usage::

        >>> from src.chunking.contextual import ContextualChunker
        >>> chunker = ContextualChunker(chunk_size=500)
        >>> chunks = chunker.process_document(document)
        >>> for chunk in chunks:
        ...     print(chunk.text[:50])
        First chunk with context...
        Second chunk with context...

    Advanced usage with custom context::

        >>> chunker = ContextualChunker(
        ...     chunk_size=500,
        ...     context_size=100
        ... )
        >>> chunks = chunker.process_document(document)
"""
```

**Success Criteria:**
- ✅ All complex public APIs have examples
- ✅ Examples are tested (doctest or manual verification)
- ✅ Examples cover common use cases

---

## Success Criteria (Test Checkpoints)

**Automated:**
- [ ] All tests still pass after refactoring
- [ ] ruff check passes (QUALITY-004)
- [ ] No new warnings or errors
- [ ] Import structure validated

**Manual Testing:**
- [ ] ⚠️ MANUAL: Documentation complete and clear
- [ ] ⚠️ MANUAL: Examples tested and work correctly
- [ ] ⚠️ MANUAL: Code duplication eliminated
- [ ] ⚠️ MANUAL: File structure logical and navigable

**Quality Gates:**
- [ ] No files >400 lines (except exceptions.py)
- [ ] No functions >50 lines
- [ ] All public functions documented with examples
- [ ] Code quality metrics maintained or improved

**Documentation Metrics:**
- [ ] 100% public function docstring coverage
- [ ] 80%+ internal function docstring coverage
- [ ] All complex functions have usage examples
- [ ] API reference generated successfully

---

## Files Modified

### New Files (8-12 estimated)
**CLI Modules** (if main.py refactored):
- `src/cli/__init__.py`
- `src/cli/add.py`
- `src/cli/query.py`
- `src/cli/config.py`
- `src/cli/web.py`

**Web Modules** (if gradio_ui.py refactored):
- `src/web/gradio_client.py`
- `src/web/gradio_components.py`

**Generation Modules** (if few_shot.py refactored):
- `src/generation/few_shot_store.py`

**Chunking Modules** (if splitters.py refactored):
- `src/chunking/page_tracking.py`

### Modified Files (All source files)
**Docstrings Added:** All 45 Python source files updated

**Refactored:**
- `src/main.py`
- `src/web/gradio_ui.py`
- `src/generation/few_shot.py`
- `src/chunking/splitters.py`
- All files with code duplication

---

## Implementation Sequence

### Phase 1: Documentation (8-10 hours)
→ QUALITY-002: Add Google-style docstrings
→ QUALITY-008: Add usage examples

### Phase 2: Code Organisation (10-16 hours)
→ QUALITY-006: File length refactoring
→ QUALITY-007: Complex function extraction

### Phase 3: Quality Improvements (4-6 hours)
→ QUALITY-004: Eliminate code duplication

### Phase 4: Validation (2-3 hours)
→ Run full test suite
→ Manual testing
→ Documentation review

---

## Known Risks

1. **File Refactoring**: Import updates may break existing code if not careful
2. **Function Extraction**: May require updating many call sites
3. **Docstring Writing**: Estimating complexity/time difficult
4. **Code Duplication**: Some patterns may be intentionally duplicated for clarity

---

## Dependencies

**Requires:**
- ✅ v0.2.5 complete (code quality improvements, type hints, magic numbers)

**Blocks:**
- v0.2.7 (new features)

**External:**
- Python 3.12.x
- All existing dependencies (no additions)

---

## Next Version

After v0.2.6 completion:
- **v0.2.7:** Feature enhancements (UX & performance improvements)
- See: [v0.2.7 Roadmap](../v0.2.7/README.md)

---

## Related Documentation

- [v0.2.6 Design Goals](../../planning/version/v0.2/v0.2.6-design.md) - Vision and decisions
- [v0.2.5 Roadmap](../v0.2.5/README.md) - Previous version
- [v0.2.7 Roadmap](../v0.2.7/README.md) - Next version

