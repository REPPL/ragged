# v0.1 Testing Strategy & Coverage

**Purpose**: Document testing approach, coverage, and quality metrics

## Test Strategy

### Approach
- **Hybrid TDD**: Tests for core logic, implementation-first for exploratory code
- **Phase-Based**: Tests written alongside each phase
- **Coverage Target**: 60-70% overall, 90%+ for core modules

### Test Types

1. **Unit Tests**: Individual functions and methods
2. **Integration Tests**: Multi-module interactions (Phase 9, pending)
3. **End-to-End Tests**: Full pipeline (Phase 9, pending)

## Current Coverage

### Phase 1 Modules (Complete)

| Module | Tests | Coverage | Status |
|--------|-------|----------|--------|
| config/settings.py | 16 | 92% | ✅ |
| utils/logging.py | 12 | 100% | ✅ |
| ingestion/models.py | 16 | 97% | ✅ |
| Total Phase 1 | 44 | 96% | ✅ |

### Phases 2-8 Modules (Pending Tests)

| Module | Status | Priority |
|--------|--------|----------|
| ingestion/loaders.py | No tests | High |
| chunking/token_counter.py | No tests | High |
| chunking/splitters.py | No tests | High |
| embeddings/* | No tests | Medium |
| storage/vector_store.py | No tests | High |
| retrieval/retriever.py | No tests | High |
| generation/* | No tests | Medium |
| main.py (CLI) | No tests | Medium |

**Overall Coverage**: 96% (Phase 1 only), ~15% estimated total

## Test Fixtures

### Shared Fixtures (conftest.py)

```python
@pytest.fixture(autouse=True)
def clean_env():
    """Clean environment variables before/after each test."""
    # Prevents test pollution

@pytest.fixture
def sample_document():
    """Sample document for testing."""
    return Document(content="Test", metadata=...)

@pytest.fixture
def temp_file(tmp_path):
    """Temporary file for testing."""
    file = tmp_path / "test.txt"
    file.write_text("Test content")
    return file
```

## Quality Metrics

### Code Quality
- **Black**: Code formatted ✅
- **Ruff**: Linting passing ✅
- **mypy**: Type checking enabled (not strict yet)
- **Pre-commit**: Hooks configured ✅

### Test Quality
- **Isolation**: Tests don't depend on each other ✅
- **Fixtures**: Shared setup via conftest.py ✅
- **Assertions**: Clear, specific assertions ✅
- **Coverage**: 96% on Phase 1 modules ✅

## Phase 13 Plan

### Coverage Expansion Goals
1. **Target**: 80%+ overall coverage
2. **Priority Modules**:
   - ingestion/loaders.py (20+ tests)
   - chunking/* (18+ tests)
   - storage/vector_store.py (12+ tests)
   - retrieval/retriever.py (10+ tests)

### Test Markers
```python
@pytest.mark.unit
@pytest.mark.integration
@pytest.mark.slow
@pytest.mark.requires_ollama
@pytest.mark.requires_chromadb
```

### CI/CD (Future)
- GitHub Actions for test runs
- Coverage reporting to Codecov
- Pre-merge coverage requirements

## Testing Best Practices

### Followed ✅
- Clean fixtures with proper setup/teardown
- Isolated tests (no shared state)
- Descriptive test names
- Fast unit tests (<1s each)

### To Improve
- More integration tests
- Mock external services
- Performance benchmarks
- Load testing

---

**Last Updated**: 2025-11-09
**Current Coverage**: 96% (Phase 1), ~15% total
**Next**: Phase 13 - Expand to 80%+ overall
