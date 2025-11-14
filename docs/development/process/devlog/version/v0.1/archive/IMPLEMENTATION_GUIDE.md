# ragged v0.1 Implementation Guide

## Overview

This guide provides implementation skeletons for Phases 3-14 of ragged v0.1. Each phase includes:
- Complete file structures with function/class signatures
- Detailed docstrings explaining what to implement
- Test skeletons showing what to test
- Integration points and dependencies
- Implementation notes and best practices

**Completed:** Phases 1-2 (Foundation, Models, Security)
**Remaining:** Phases 3-14 (see below)

---

## Phase 3: Chunking System (Days 7-10)

### Files to Create

#### `src/chunking/token_counter.py`
Token counting with tiktoken for accurate measurements.

#### `src/chunking/splitters.py`
RecursiveCharacterTextSplitter implementation with smart boundary detection.

#### `tests/chunking/test_token_counter.py`
Token counting tests (accuracy, edge cases, caching).

#### `tests/chunking/test_splitters.py`
Chunking tests (size limits, overlap, boundaries, edge cases).

### Key Implementation Notes
- Use tiktoken for token counting
- Implement recursive splitting: `\n\n` → `\n` → `. ` → ` ` → chars
- Respect chunk_size and chunk_overlap from config
- Preserve semantic boundaries where possible
- Add chunk metadata (position, overlaps)

---

## Phase 4: Embeddings System (Days 11-14)

### Files to Create

#### `src/embeddings/base.py`
Abstract base class for all embedders.

#### `src/embeddings/sentence_transformer.py`
SentenceTransformer implementation (all-MiniLM-L6-v2).

#### `src/embeddings/ollama_embedder.py`
Ollama embedder implementation (nomic-embed-text).

#### `src/embeddings/factory.py`
Factory for creating embedders based on config.

#### `tests/embeddings/test_*.py`
Tests for each embedder + factory.

### Key Implementation Notes
- Abstract interface ensures swappable embedders
- Batch processing for efficiency
- Device detection (CPU/CUDA/MPS)
- Retry logic for Ollama API calls
- Model caching to avoid reloading

---

## Phase 5: Vector Storage (Days 15-17)

### Files to Create

#### `src/storage/vector_store.py`
ChromaDB client wrapper with connection management.

#### `tests/storage/test_vector_store.py`
Vector operations tests.

#### `tests/storage/test_persistence.py`
Persistence and recovery tests (marked as integration).

### Key Implementation Notes
- Wrap ChromaDB client with auto-reconnection
- Single collection for v0.1: "ragged_documents"
- Store full chunk text + metadata
- Batch upsert for efficiency
- Health checks before operations

---

## Phase 6: Retrieval System (Days 18-20)

### Files to Create

#### `src/retrieval/retriever.py`
Query processing and top-k retrieval.

#### `tests/retrieval/test_retriever.py`
Retrieval logic tests.

#### `tests/retrieval/test_evaluation.py`
Manual evaluation with test questions.

### Key Implementation Notes
- Embed query using configured embedder
- Retrieve top-k chunks from vector store
- Deduplicate if needed
- Format results with metadata
- Include relevance scores

---

## Phase 7: Generation System (Days 21-23)

### Files to Create

#### `src/generation/ollama_client.py`
Ollama API client for LLM generation.

#### `src/generation/prompts.py`
RAG prompt templates with citation instructions.

#### `src/generation/response_parser.py`
Parse LLM responses and extract citations.

#### `tests/generation/test_*.py`
Tests for each component.

### Key Implementation Notes
- Use ollama Python library
- RAG prompt: context + question + citation instructions
- Streaming support (for future CLI improvements)
- Timeout handling (30s default)
- Extract citations from response

---

## Phase 8: CLI Interface (Days 24-26)

### Files to Create

#### `src/main.py`
Click-based CLI with all commands.

#### `tests/cli/test_commands.py`
CLI command tests (use Click's CliRunner).

### Commands to Implement
```bash
ragged add <file>           # Ingest document
ragged query "<question>"   # Ask question
ragged list                 # List documents
ragged clear                # Clear database
ragged config [set]         # Show/update config
ragged health               # Check services
```

### Key Implementation Notes
- Use Click for command parsing
- Use Rich for beautiful output (progress bars, tables)
- Comprehensive error handling with helpful messages
- Progress indicators for long operations

---

## Phase 9: End-to-End Integration (Days 27-29)

### Files to Create

#### `tests/integration/test_end_to_end.py`
Full pipeline tests (ingest → query → generate).

#### `tests/integration/test_quality.py`
Quality metrics (relevance, faithfulness).

#### `tests/performance/test_benchmarks.py`
Performance tests (latency, memory).

### Test Scenarios
- Single document ingestion and query
- Multiple documents with cross-document queries
- Cross-format tests (PDF + TXT + MD + HTML)
- Error recovery (service restart)

### Quality Metrics
- Retrieval relevance: >70%
- Answer faithfulness: >80%
- Query latency: <5s

---

## Phase 10: Docker Integration (Days 30-32)

### Files to Update

#### `Dockerfile`
Fix PYTHONPATH and dependencies.

#### `docker-compose.yml`
Proper health checks and volume mounts.

#### `tests/integration/test_docker.py`
Containerized testing.

### Key Fixes Needed
- Install all dependencies in container
- Set PYTHONPATH correctly for src/ imports
- Volume mount for development
- Health checks that actually work
- Non-root user for security

---

## Phase 11: Documentation (Days 33-35)

### Files to Create/Update

#### `README.md`
Project overview, features, quick start.

#### `docs/user-guide/installation.md`
Detailed installation instructions.

#### `docs/user-guide/quick-start.md`
Tutorial with examples.

#### `docs/user-guide/cli-reference.md`
Complete CLI documentation.

#### `docs/user-guide/configuration.md`
All configuration options.

#### `docs/user-guide/troubleshooting.md`
Common issues and solutions.

#### `docs/developer/architecture.md`
System architecture overview.

#### `docs/developer/contributing.md`
How to contribute.

#### `docs/developer/testing.md`
Running and writing tests.

#### `CHANGELOG.md`
Version history.

---

## Phase 12: Security Audit (Days 36-37)

### Tasks

1. **Run Security Tools**
   - `bandit -r src/`
   - `pip-audit`
   - `safety check`

2. **Use Agent**
   - Run `codebase-security-auditor` agent
   - Review all findings
   - Fix high/critical issues
   - Document medium/low for future

3. **Manual Review**
   - Check all user inputs are validated
   - Verify no secrets in code
   - Review authentication (if added)
   - Check error messages don't leak info

---

## Phase 13: Testing & Coverage (Days 38-40)

### Tasks

1. **Run Full Test Suite**
   ```bash
   pytest --cov=src --cov-report=html
   ```

2. **Coverage Analysis**
   - Identify gaps
   - Write tests for critical uncovered paths
   - Target: 60-70% overall, 90%+ core logic

3. **Manual Testing**
   - Test on macOS (primary platform)
   - Test in Docker
   - Real-world documents
   - Usability testing

---

## Phase 14: Git Commit & Release (Day 41)

### Tasks

1. **Pre-Commit Checklist**
   - All tests pass
   - Coverage targets met
   - Security audit passed
   - Documentation complete
   - British English verified
   - No debug code

2. **Use Agent**
   - Run `git-documentation-committer` agent
   - Agent will create comprehensive commit
   - Review and adjust if needed

3. **Tag Release**
   ```bash
   git tag -a v0.1.0 -m "ragged version 0.1.0"
   ```

4. **Validation**
   - Fresh clone test
   - Install and run tests
   - Docker build and run
   - CLI smoke tests

---

## Implementation Order

Recommended order for implementing remaining phases:

1. **Phase 3** (Chunking) - Core functionality
2. **Phase 4** (Embeddings) - Core functionality
3. **Phase 5** (Storage) - Core functionality
4. **Phase 6** (Retrieval) - Core functionality
5. **Phase 7** (Generation) - Core functionality
6. **Phase 8** (CLI) - User interface
7. **Phase 9** (Integration) - Validation
8. **Phase 10** (Docker) - Deployment
9. **Phase 11** (Docs) - User-facing
10. **Phases 12-14** - Polish & release

---

## Testing Strategy

For each phase:

1. **Write tests first** (TDD for core logic)
2. **Run tests frequently** (`pytest -v`)
3. **Check coverage** (`pytest --cov=src`)
4. **Fix failures immediately**
5. **Refactor with confidence**

Test markers to use:
- `@pytest.mark.unit` - Fast, isolated
- `@pytest.mark.integration` - Multiple components
- `@pytest.mark.e2e` - Full system
- `@pytest.mark.slow` - Long-running

---

## Dependencies to Install

As you progress through phases, install these:

**Phase 3:**
```bash
pip install tiktoken
```

**Phase 4:**
```bash
pip install sentence-transformers torch ollama
```

**Phase 5:**
```bash
pip install chromadb-client  # Lighter than full chromadb
```

**Phase 7:**
```bash
pip install ollama  # If not already installed
```

**Phase 8:**
```bash
pip install click rich
```

**Phase 11:**
```bash
pip install mkdocs mkdocs-material  # Optional for docs
```

---

## Common Patterns Established

### 1. Error Handling
```python
try:
    result = operation()
except SpecificError as e:
    logger.error(f"Operation failed: {e}")
    raise CustomError(f"User-friendly message: {e}")
```

### 2. Configuration Access
```python
from src.config.settings import get_settings

settings = get_settings()
value = settings.some_config_value
```

### 3. Logging
```python
from src.utils.logging import get_logger

logger = get_logger(__name__)
logger.info("Operation completed", extra={"key": "value"})
```

### 4. Validation
```python
from src.utils.security import validate_file_path, validate_file_size

path = validate_file_path(input_path)
size = validate_file_size(path)
```

### 5. Pydantic Models
```python
from pydantic import BaseModel, Field, field_validator

class MyModel(BaseModel):
    field: str = Field(description="...")

    @field_validator("field")
    @classmethod
    def validate_field(cls, v: str) -> str:
        # validation logic
        return v
```

---

## Quality Standards

Maintain these standards throughout:

- ✅ **Type hints** on all functions
- ✅ **Docstrings** (Google style)
- ✅ **Tests** before or after implementation
- ✅ **Security** validation on all inputs
- ✅ **Error handling** with helpful messages
- ✅ **Logging** at appropriate levels
- ✅ **British English** in user-facing text
- ✅ **No hardcoded values** (use config)

---

## Getting Unstuck

If you encounter issues:

1. **Check logs** - Enable DEBUG level
2. **Run single test** - `pytest path/to/test.py::TestClass::test_method -v`
3. **Check dependencies** - Ensure all installed
4. **Review examples** - Phases 1-2 show patterns
5. **Read docs** - See docs/development/plans/v0.1-implementation-plan.md

---

## Success Criteria Reminder

Don't forget these targets:

- ✅ All 4 document formats working
- ✅ Both embedding models functional
- ✅ 60-70% test coverage overall
- ✅ 90%+ coverage on core logic
- ✅ Query latency <5s
- ✅ All security checks pass
- ✅ Documentation complete

---

**Next:** See individual phase skeleton files for detailed implementation guidance.
