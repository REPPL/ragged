# File Length Refactoring Plan (v0.2.6-004)

**Status:** Deferred to v0.2.7
**Estimated Effort:** 8-12 hours
**Priority:** Medium

---

## Overview

Refactor files exceeding 400 lines to improve maintainability, readability, and testability.

---

## Files Requiring Refactoring

### 1. main.py (597 lines) - PRIORITY 1

**Current Structure:**
- CLI entry point with all commands inline
- Multiple large command functions (add: ~184 lines, config: ~171 lines)

**Proposed Structure:**
```
src/
├── main.py (~60 lines)           # CLI group setup + entry point
└── cli/
    ├── __init__.py
    └── commands/
        ├── __init__.py
        ├── add.py (~200 lines)    # Document adding
        ├── query.py (~90 lines)   # Query execution
        ├── docs.py (~70 lines)    # List/clear documents
        ├── config.py (~180 lines) # Configuration commands
        └── health.py (~50 lines)  # Health check
```

**Refactoring Steps:**
1. Create `src/cli/commands/` directory structure
2. Extract `add` command to `cli/commands/add.py`
3. Extract `query` command to `cli/commands/query.py`
4. Extract `list_docs` and `clear` to `cli/commands/docs.py`
5. Extract all `config` commands to `cli/commands/config.py`
6. Extract `health` command to `cli/commands/health.py`
7. Update `main.py` to import and register commands
8. Run full test suite to verify functionality
9. Update CLI documentation if needed

**Testing Requirements:**
- All CLI commands must work identically
- No import errors
- No circular dependencies
- Tests in `tests/cli/` must pass

---

### 2. gradio_ui.py (517 lines) - PRIORITY 2

**Current Structure:**
- Single file with all Gradio UI components
- Event handlers, layout, and business logic mixed

**Proposed Structure:**
```
src/web/
├── gradio_ui.py (~100 lines)  # Main app setup + launch
└── gradio/
    ├── __init__.py
    ├── components.py (~150 lines)  # UI component definitions
    ├── handlers.py (~200 lines)    # Event handler logic
    └── layouts.py (~100 lines)     # Tab layouts
```

**Refactoring Steps:**
1. Create `src/web/gradio/` directory
2. Extract component creation to `components.py`
3. Extract event handlers to `handlers.py`
4. Extract layout logic to `layouts.py`
5. Keep main app setup in `gradio_ui.py`
6. Test UI functionality end-to-end

---

### 3. few_shot.py (427 lines) - PRIORITY 3

**Current Structure:**
- Example storage, retrieval, and seeding in one file
- Mixed concerns: data models, storage, search, utilities

**Proposed Structure:**
```
src/generation/few_shot/
├── __init__.py
├── models.py (~80 lines)      # FewShotExample dataclass
├── store.py (~200 lines)      # FewShotExampleStore class
├── search.py (~100 lines)     # Search logic (embedding, keyword)
└── seeds.py (~80 lines)       # Default example seeding
```

**Refactoring Steps:**
1. Create `src/generation/few_shot/` directory
2. Extract `FewShotExample` to `models.py`
3. Move `FewShotExampleStore` to `store.py`
4. Extract search methods to `search.py`
5. Move `seed_default_examples` to `seeds.py`
6. Update imports throughout codebase

---

### 4. splitters.py (407 lines) - PRIORITY 4

**Current Structure:**
- Multiple splitter classes in one file
- Base class + 4 concrete implementations

**Proposed Structure:**
```
src/chunking/splitters/
├── __init__.py
├── base.py (~60 lines)                  # TextSplitter base
├── character.py (~80 lines)             # CharacterTextSplitter
├── recursive_character.py (~120 lines)  # RecursiveCharacterTextSplitter
├── sentence.py (~80 lines)              # SentenceTextSplitter
└── token.py (~100 lines)                # TokenTextSplitter
```

**Refactoring Steps:**
1. Create `src/chunking/splitters/` directory
2. Extract `TextSplitter` base to `base.py`
3. Each splitter type to its own file
4. Update imports in `__init__.py` for backwards compatibility
5. Run chunking tests

---

## Additional Candidates (Lower Priority)

### 5. benchmarks.py (400 lines)
- Not currently used in production code
- Can be split later if benchmarks become core feature

### 6. api.py (379 lines)
- Just under 400-line threshold
- Consider if grows further

### 7. async_processor.py (377 lines)
- Just under threshold
- Monitor for future refactoring

---

## Testing Strategy

For each refactored file:

1. **Unit Tests:** Ensure all tests pass before and after
2. **Integration Tests:** Verify end-to-end workflows
3. **Import Tests:** Check for circular dependencies
4. **Manual Testing:** Test CLI commands and UI manually

---

## Benefits

1. **Maintainability:** Smaller files easier to understand and modify
2. **Testability:** Isolated components easier to test
3. **Reusability:** Extracted modules can be reused
4. **Onboarding:** New developers can navigate codebase faster
5. **Git History:** Smaller diffs, clearer change tracking

---

## Risks and Mitigations

| Risk | Mitigation |
|------|------------|
| Breaking imports | Update all imports systematically, use IDE refactoring tools |
| Circular dependencies | Careful dependency planning, use dependency injection where needed |
| Test failures | Run full test suite after each file refactored |
| Lost functionality | Comprehensive manual testing of all features |
| Merge conflicts | Complete refactoring in dedicated branch, merge quickly |

---

## Timeline Estimate

| File | Estimated Hours | Priority |
|------|----------------|----------|
| main.py | 4-5h | P1 |
| gradio_ui.py | 2-3h | P2 |
| few_shot.py | 1-2h | P3 |
| splitters.py | 1-2h | P4 |
| **Total** | **8-12h** | |

---

## Implementation Notes

- Complete one file at a time with full testing
- Commit after each successful refactoring
- Maintain backwards compatibility where possible
- Update documentation after each change
- Use British English in all new docstrings

---

**Created:** 2025-11-17
**Status:** Planning complete, ready for implementation
