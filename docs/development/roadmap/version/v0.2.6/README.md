# Ragged v0.2.6 Roadmap - Quality & Code Improvements

**Status:** Planned

**Total Hours:** 12-19 hours (AI implementation)

**Focus:** Code quality, maintainability, and technical debt reduction

**Breaking Changes:** None

---

## Overview

Version 0.2.6 addresses code quality improvements that enhance maintainability and reduce technical debt. Must complete v0.2.4 first.

**Dependencies:** Requires v0.2.4 completion (high priority bugs fixed)

---

## QUALITY-001: Type Hint Coverage (4 hours)

**Problem:** Approximately 15% of functions lack proper type hints, reducing code clarity and preventing static type checking.

**Implementation:**
1. Run mypy --strict to identify missing type hints [1 hour]
2. Add type hints to all public functions [2 hours]
3. Add type hints to internal functions [1 hour]

**Files:** All modules in src/ lacking complete type hints

**⚠️ MANUAL TEST:** Run mypy --strict, verify no errors

**Success:** mypy passes with --strict mode, all public functions have complete type hints

---

## QUALITY-002: Docstring Completeness (3 hours)

**Problem:** Some functions lack docstrings or have minimal documentation.

**Implementation:**
1. Audit all functions for missing docstrings [30 minutes]
2. Add Google-style docstrings to all public functions [1.5 hours]
3. Add examples to complex functions [1 hour]

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

## QUALITY-003: TODO Comments Cleanup (2-8 hours)

**Problem:** 11 TODO comments found in code should either be implemented or converted to issues.

**Implementation:**
1. Audit all TODO comments in codebase [30 minutes]
2. Implement quick TODOs (<30 min each) [1-5 hours]
3. Create GitHub issues for complex TODOs [30 minutes]
4. Remove obsolete TODOs [30 minutes]

**Decision criteria:**
- If quick (<30 min) → implement now
- If complex → create GitHub issue and reference it
- If obsolete → remove

**Files:** All files containing TODO comments (11 found)

**⚠️ MANUAL TEST:** Search for remaining TODOs, verify all have issue references or are implemented

**Success:** No TODO comments without issue references, quick TODOs implemented

---

## QUALITY-004: Code Duplication (1-2 hours)

**Problem:** Some code duplication exists beyond BUG-007's metadata sanitisation (already addressed in v0.2.4).

**Implementation:**
1. Run ruff to find duplicate code blocks [30 minutes]
2. Extract common patterns to utilities [30 minutes-1 hour]
3. Update all call sites [30 minutes]

**Common patterns to extract:**
- Repeated validation logic
- Common data transformations
- Shared formatting code

**Files:** All modules with duplicated code patterns

**⚠️ MANUAL TEST:** Review extracted utilities, verify no functionality broken

**Success:** No significant code duplication, shared logic in utilities modules

---

## QUALITY-005: Magic Numbers (2 hours)

**Problem:** Hardcoded values (magic numbers) scattered throughout code without explanation.

**Implementation:**
1. Create src/config/constants.py [1 hour]
2. Extract all magic numbers to named constants [30 minutes]
3. Update all usages [30 minutes]

**Constants to define:**
```python
# src/config/constants.py (NEW FILE)
"""Named constants for ragged."""

# Chunking
DEFAULT_CHUNK_SIZE = 500  # Tokens
DEFAULT_CHUNK_OVERLAP = 50  # Tokens
MAX_CHUNK_SIZE = 2000  # Maximum tokens per chunk

# Retrieval
DEFAULT_TOP_K = 5  # Number of chunks to retrieve
MAX_TOP_K = 50  # Maximum retrievable chunks

# Token estimation
CHARS_PER_TOKEN_ESTIMATE = 4  # Average characters per token

# Batch processing
DEFAULT_BATCH_SIZE = 32  # Documents per batch
MAX_MEMORY_MB = 2000  # Maximum memory usage in MB
```

**Files:** src/config/constants.py (new), all files with magic numbers

**⚠️ MANUAL TEST:** Verify all constants used correctly, behaviour unchanged

**Success:** All magic numbers replaced with named, documented constants

---

## Success Criteria (Test Checkpoints)

**Automated:**
- [ ] mypy --strict passes (QUALITY-001)
- [ ] ruff check passes (QUALITY-004)
- [ ] No bare magic numbers (QUALITY-005)
- [ ] All tests still pass

**Manual Testing:**
- [ ] ⚠️ MANUAL: Documentation complete and clear
- [ ] ⚠️ MANUAL: No TODO comments without issues
- [ ] ⚠️ MANUAL: Code duplication eliminated

**Quality Gates:**
- [ ] All existing tests pass
- [ ] No new warnings in logs
- [ ] Code quality metrics improved
- [ ] mypy strict mode compliance

---

## Known Risks

- TODO cleanup might reveal additional work needed
- Type hint additions might expose design issues
- Constant extraction might require configuration changes
- Docstring writing might take longer than estimated

---

## Next Version

After v0.2.6 completion:
- **v0.2.5:** Remaining P2 bugs (if any)
- **v0.2.7:** UX & performance improvements
- See: `roadmap/version/v0.2.7/README.md`

---

**Last Updated:** 2025-11-12

**Status:** Ready for implementation after v0.2.4
