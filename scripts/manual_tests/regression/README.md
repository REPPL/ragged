# Regression Tests

**Purpose:** Test **critical paths** that must work consistently across all ragged versions.

**Pattern:** Cross-version tests that ensure core functionality doesn't break with new releases.

---

## What Belongs Here

✅ **Core document ingestion** - PDF, Markdown, HTML, TXT processing
✅ **Retrieval quality** - Vector search, BM25, hybrid retrieval
✅ **Essential CLI commands** - add, query, list, clear
✅ **Web API endpoints** - /upload, /query, /health
✅ **Critical error handling** - Graceful degradation, recovery

❌ **Version-specific features** - Use `version/` directory
❌ **User workflows** - Use `workflows/` directory
❌ **Performance benchmarks** - Use `performance/` directory

---

## Test Coverage

### 1. Document Ingestion Pipeline (`test_ingestion_pipeline.py`)

**Supported:** v0.1+

**Tests:**
- PDF processing (PyMuPDF, PyMuPDF4LLM)
- Markdown processing
- HTML processing (Trafilatura, BeautifulSoup)
- Plain text processing
- Folder ingestion (v0.2.7+)
- Duplicate detection
- Chunking strategies
- Metadata extraction

### 2. Retrieval Quality (`test_retrieval_quality.py`)

**Supported:** v0.2+ (hybrid retrieval introduced)

**Tests:**
- Vector search accuracy (semantic similarity)
- BM25 search accuracy (keyword matching)
- Hybrid retrieval fusion
- Result ranking quality
- Metadata filtering
- Query result caching

### 3. Core CLI Commands (`test_cli_core.py`)

**Supported:** v0.1+

**Tests:**
- `ragged add` - Document addition
- `ragged query` - Query execution
- `ragged list` - Document listing
- `ragged clear` - Document deletion
- `ragged health` - Service health checks
- Command-line argument parsing
- Error message clarity

### 4. Web API (`test_web_api.py`)

**Supported:** v0.2+ (FastAPI introduced)

**Tests:**
- POST /upload - Document upload endpoint
- POST /query - Query endpoint with streaming
- GET /health - Health check endpoint
- Response format validation (JSON)
- Error responses (4xx, 5xx)
- Concurrent request handling

---

## pytest Markers

All regression tests should use these markers:

```python
import pytest

@pytest.mark.regression
@pytest.mark.requires_ollama
@pytest.mark.requires_chromadb
def test_document_ingestion_pipeline():
    """Test complete document ingestion across versions"""
    pass
```

---

## Running Tests

### Run all regression tests

```bash
pytest scripts/manual_tests/regression/
```

### Run specific regression test

```bash
pytest scripts/manual_tests/regression/test_ingestion_pipeline.py
```

### Run regression tests requiring external services

```bash
pytest scripts/manual_tests/regression/ -m 'requires_ollama and requires_chromadb'
```

---

## Version Compatibility Matrix

| Test | v0.1 | v0.2.4 | v0.2.5 | v0.2.7 | v0.2.8 | v0.2.9 | v0.2.10 | v0.2.11 |
|------|------|--------|--------|--------|--------|--------|---------|---------|
| **Ingestion Pipeline** | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | TBD | TBD |
| **Retrieval Quality** | ⚠️ (vector only) | ✅ | ✅ | ✅ | ✅ | ✅ | TBD | TBD |
| **Core CLI** | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | TBD | TBD |
| **Web API** | ❌ | ✅ | ✅ | ✅ | ✅ | ✅ | TBD | TBD |

---

## Maintenance

### When to Update

- ✅ **Breaking changes** in core functionality
- ✅ **New critical paths** added to the system
- ✅ **API changes** in core commands or endpoints
- ✅ **Version incompatibilities** discovered

### How to Update

1. Add new test cases for new critical functionality
2. Update version compatibility matrix
3. Mark deprecated tests with `@pytest.mark.skip(reason="...")`
4. Document breaking changes in test docstrings

---

## Related Documentation

- [Version Tests](../version/README.md) - Version-specific feature tests
- [Workflow Tests](../workflows/README.md) - End-to-end user scenarios
- [Manual Test Plans](../../../docs/development/process/testing/manual/) - Test documentation
- [Implementation](../../../docs/development/implementation/) - What was built

---

**Maintained By:** ragged development team
