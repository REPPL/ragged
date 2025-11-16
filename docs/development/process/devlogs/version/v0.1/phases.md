# v0.1 Phase-by-Phase Implementation Plan

This document provides detailed breakdowns of all 14 phases in the v0.1 implementation, including goals, deliverables, dependencies, and current status.

## Overview

ragged v0.1 is implemented in 14 incremental phases, organised into three groups:

1. **Foundation** (Phase 1): Core infrastructure
2. **Core Features** (Phases 2-8): RAG pipeline implementation
3. **Quality & Release** (Phases 9-14): Integration, testing, documentation, release

---

## Phase 1: Foundation & Development Environment ✅

**Status:** Complete
**Duration**: ~12 hours
**Completion Date**: 2025-11-09

### Goals
- Establish project structure and development environment
- Implement configuration and logging systems
- Create base document models
- Set up testing infrastructure

### Deliverables
- [x] Package structure with `src/` and `tests/`
- [x] `pyproject.toml` with all metadata and dependencies
- [x] Configuration system using Pydantic (`src/config/settings.py`)
- [x] Privacy-safe logging system (`src/utils/logging.py`)
- [x] Security utilities (`src/utils/security.py`)
- [x] Document models (`src/ingestion/models.py`)
- [x] Pre-commit hooks (`.pre-commit-config.yaml`)
- [x] Test infrastructure (`tests/conftest.py`)

### Test Coverage
- 44 tests passing
- 96% overall coverage
- 100% coverage on logging module
- 97% coverage on document models
- 92% coverage on settings

### Key Files Created
```
src/
├── config/settings.py (148 lines)
├── utils/logging.py (166 lines)
├── utils/security.py (215 lines)
└── ingestion/models.py (167 lines)

tests/
├── config/test_settings.py (16 tests)
├── utils/test_logging.py (12 tests)
└── ingestion/test_models.py (16 tests)
```

### Challenges & Solutions
- **Challenge**: Pydantic v2 deprecation warnings
  - **Solution**: Migrated from `class Config` to `model_config = ConfigDict()`
- **Challenge**: Test environment pollution
  - **Solution**: Created `clean_env` fixture with `autouse=True`

### Lessons Learned
- Pydantic validation catches configuration errors early
- Privacy filtering in logs is essential for sensitive data
- Comprehensive fixtures improve test reliability
- Type hints + Pydantic = excellent IDE support

---

## Phase 2: Document Ingestion Pipeline ✅

**Status:** Complete
**Duration**: ~10 hours
**Completion Date**: 2025-11-09

### Goals
- Implement loaders for PDF, TXT, Markdown, HTML
- Add security validation for all file operations
- Support automatic format detection

### Deliverables
- [x] PDF loader using PyMuPDF4LLM (`load_pdf`)
- [x] TXT loader with encoding detection (`load_txt`)
- [x] Markdown loader with title extraction (`load_markdown`)
- [x] HTML loader using Trafilatura (`load_html`)
- [x] Main loader with auto-detection (`load_document`)
- [x] Security validation (path traversal, file size, MIME types)

### Key Files Created
```
src/ingestion/loaders.py (283 lines)
├── load_document() - Main entry point with auto-detection
├── load_pdf() - PyMuPDF4LLM integration
├── load_txt() - Chardet for encoding
├── load_markdown() - Title extraction
├── load_html() - Trafilatura extraction
└── _detect_format() - MIME-based detection
```

### Dependencies Installed
```bash
pip install pymupdf4llm trafilatura chardet
```

### Challenges & Solutions
- **Challenge**: PyMuPDF4LLM returns markdown, not plain text
  - **Solution**: Embraced it - better structure preservation
- **Challenge**: Encoding detection for TXT files
  - **Solution**: Chardet fallback when UTF-8 fails
- **Challenge**: HTML extraction quality
  - **Solution**: Trafilatura provides clean, content-focused extraction

### Lessons Learned
- PyMuPDF4LLM's markdown output is superior to raw text extraction
- Trafilatura is excellent for web content extraction
- Security validation must happen before any file operations
- MIME type detection is more reliable than extension checking

---

## Phase 3: Chunking System ✅

**Status:** Complete
**Duration**: ~8 hours
**Completion Date**: 2025-11-09

### Goals
- Implement accurate token counting
- Create semantic-aware text splitter
- Support configurable chunk size and overlap

### Deliverables
- [x] Token counter with tiktoken integration (`src/chunking/token_counter.py`)
- [x] Recursive character text splitter (`src/chunking/splitters.py`)
- [x] Configuration support for chunk size and overlap
- [x] Metadata preservation in chunks

### Key Files Created
```
src/chunking/
├── token_counter.py (76 lines)
│   ├── get_tokenizer() - Cached tokenizer
│   ├── count_tokens() - Accurate counting
│   ├── estimate_tokens() - Quick estimation
│   ├── split_by_tokens() - Token-based splitting
│   └── tokens_to_chars() - Token-to-char conversion
└── splitters.py (201 lines)
    ├── RecursiveCharacterTextSplitter - Main class
    ├── chunk_document() - Document chunking
    └── create_chunk_metadata() - Metadata creation
```

### Implementation Details
- **Token Counting**: tiktoken with cl100k_base encoding
- **Splitting Strategy**: Recursive by separators (paragraphs → lines → sentences → words → chars)
- **Chunk Size**: Default 500 tokens
- **Overlap**: Default 100 tokens
- **Metadata**: Preserves document context, position, token counts

### Dependencies Installed
```bash
pip install tiktoken
```

### Challenges & Solutions
- **Challenge**: Token count vs character count mismatch
  - **Solution**: Always use token-based sizing with tiktoken
- **Challenge**: Preserving semantic boundaries
  - **Solution**: Recursive splitting tries larger separators first

### Lessons Learned
- Token-accurate chunking is critical for LLM context management
- Recursive splitting preserves semantic structure better than fixed-size
- LRU cache on tokenizer significantly improves performance
- Overlap helps maintain context across chunks

---

## Phase 4: Embeddings System ✅

**Status:** Complete
**Duration**: ~12 hours
**Completion Date**: 2025-11-09

### Goals
- Support multiple embedding backends
- Implement factory pattern for model selection
- Provide device detection for optimal performance

### Deliverables
- [x] Base embedder interface (`src/embeddings/base.py`)
- [x] SentenceTransformers implementation (`src/embeddings/sentence_transformer.py`)
- [x] Ollama embeddings implementation (`src/embeddings/ollama_embedder.py`)
- [x] Factory for model creation (`src/embeddings/factory.py`)

### Key Files Created
```
src/embeddings/
├── base.py (117 lines)
│   ├── BaseEmbedder - Abstract base class
│   └── similarity() - Cosine similarity calculation
├── sentence_transformer.py (82 lines)
│   ├── Device detection (CPU/CUDA/MPS)
│   ├── embed_text() - Single text embedding
│   └── embed_batch() - Batch processing
├── ollama_embedder.py (133 lines)
│   ├── Retry logic with exponential backoff
│   ├── Model availability verification
│   └── Dimension detection
└── factory.py (78 lines)
    ├── create_embedder() - Factory method
    └── get_embedder() - Singleton access
```

### Models Supported
- **sentence-transformers**: all-MiniLM-L6-v2 (384 dimensions, local)
- **Ollama**: nomic-embed-text (768 dimensions, local via API)

### Dependencies Installed
```bash
pip install sentence-transformers torch ollama
```

### Challenges & Solutions
- **Challenge**: Device detection for optimal performance
  - **Solution**: Auto-detect CUDA, MPS, fallback to CPU
- **Challenge**: Ollama API reliability
  - **Solution**: Retry logic with exponential backoff
- **Challenge**: Different embedding dimensions per model
  - **Solution**: Auto-detect dimensions on initialization

### Lessons Learned
- Factory pattern makes model switching trivial
- Device auto-detection improves user experience
- Retry logic essential for API-based embedders
- Dimension auto-detection prevents configuration errors

---

## Phase 5: Vector Storage ✅

**Status:** Complete
**Duration**: ~6 hours
**Completion Date**: 2025-11-09

### Goals
- Integrate ChromaDB for vector storage
- Implement full CRUD operations
- Support metadata filtering

### Deliverables
- [x] ChromaDB wrapper (`src/storage/vector_store.py`)
- [x] Connection management and health checking
- [x] Add, query, delete, count, clear operations
- [x] Collection metadata support

### Key Files Created
```
src/storage/vector_store.py (194 lines)
├── __init__() - Connection setup
├── health_check() - Heartbeat verification
├── add() - Batch insertion
├── query() - Similarity search
├── delete() - Remove by ID or filter
├── count() - Get collection size
├── clear() - Remove all entries
└── get_collection_info() - Collection metadata
```

### Implementation Details
- **Client**: ChromaDB HttpClient
- **URL Parsing**: Extracts host/port from configured URL
- **Collections**: Auto-create with metadata
- **Operations**: Full CRUD with error handling

### Dependencies Installed
```bash
pip install chromadb
```

### Challenges & Solutions
- **Challenge**: ChromaDB nested list format in results
  - **Solution**: Proper unpacking of results[0] for ids, documents, etc.
- **Challenge**: Connection verification
  - **Solution**: Heartbeat check on initialization

### Lessons Learned
- ChromaDB API is straightforward and well-documented
- URL parsing from config prevents hardcoding
- Health checks catch connection issues early
- Metadata support enables powerful filtering

---

## Phase 6: Retrieval System ✅

**Status:** Complete
**Duration**: ~6 hours
**Completion Date**: 2025-11-09

### Goals
- Implement semantic similarity search
- Support top-k retrieval with filtering
- Provide structured result objects

### Deliverables
- [x] Retriever class (`src/retrieval/retriever.py`)
- [x] RetrievedChunk dataclass for results
- [x] Query embedding and similarity search
- [x] Deduplication support

### Key Files Created
```
src/retrieval/retriever.py (181 lines)
├── RetrievedChunk - Result dataclass
├── Retriever - Main retrieval class
│   ├── __init__() - Setup with vector store + embedder
│   ├── retrieve() - Semantic search
│   ├── retrieve_with_context() - Context windows (v0.2)
│   └── deduplicate_chunks() - Remove duplicates
```

### Implementation Details
- **Embedding**: Uses configured embedder
- **Search**: ChromaDB similarity search
- **Results**: Structured with score, metadata, position
- **Filtering**: Optional metadata filters
- **Scoring**: Distance-based (lower = better)

### Challenges & Solutions
- **Challenge**: ChromaDB returns nested lists
  - **Solution**: Proper unpacking logic
- **Challenge**: Score interpretation (distance vs similarity)
  - **Solution**: Document that lower distance = better match

### Lessons Learned
- Retrieval builds naturally on embeddings + storage
- Structured result objects improve usability
- Metadata filtering enables powerful queries
- Deduplication prevents redundant results

---

## Phase 7: Generation System ✅

**Status:** Complete
**Duration**: ~8 hours
**Completion Date**: 2025-11-09

### Goals
- Integrate Ollama for LLM generation
- Implement RAG-specific prompts
- Extract and parse citations

### Deliverables
- [x] Ollama client (`src/generation/ollama_client.py`)
- [x] RAG prompt templates (`src/generation/prompts.py`)
- [x] Response parser (`src/generation/response_parser.py`)

### Key Files Created
```
src/generation/
├── ollama_client.py (163 lines)
│   ├── __init__() - Client setup with model verification
│   ├── generate() - Text generation
│   ├── generate_stream() - Streaming responses
│   └── health_check() - Service verification
├── prompts.py (89 lines)
│   ├── RAG_SYSTEM_PROMPT - System instructions
│   ├── build_rag_prompt() - Prompt construction
│   └── build_few_shot_prompt() - Few-shot examples (v0.2)
└── response_parser.py (91 lines)
    ├── GeneratedResponse - Result dataclass
    ├── parse_response() - Citation extraction
    └── format_response_for_cli() - CLI formatting
```

### Implementation Details
- **LLM**: Ollama with llama3.2 default
- **Prompts**: RAG-specific with citation instructions
- **Citations**: Regex-based extraction `[Source: filename]`
- **Streaming**: Supported for future UI enhancements

### Dependencies Installed
```bash
pip install ollama
```

### Challenges & Solutions
- **Challenge**: Ensuring citation format consistency
  - **Solution**: Clear system prompt instructions
- **Challenge**: Model availability verification
  - **Solution**: Check models list on initialization

### Lessons Learned
- Ollama API is clean and straightforward
- System prompts are critical for citation quality
- Streaming support enables better UX in future
- Citation extraction with regex is simple and effective

---

## Phase 8: CLI Interface ✅

**Status:** Complete
**Duration**: ~8 hours
**Completion Date**: 2025-11-09

### Goals
- Create user-friendly command-line interface
- Implement core commands (add, query, list, etc.)
- Provide progress feedback and error handling

### Deliverables
- [x] Click-based CLI (`src/main.py`)
- [x] Rich formatting for output
- [x] 6 core commands implemented
- [x] Progress bars and status indicators

### Key Files Created
```
src/main.py (323 lines)
├── cli() - Main Click group
├── add() - Document ingestion with progress
├── query() - Question answering with RAG
├── list() - Collection statistics
├── clear() - Database clearing with confirmation
├── config() - Configuration group
│   ├── show() - Display current config
│   └── set() - Modify config (v0.2)
└── health() - Service health checks
```

### Commands Implemented

1. **`ragged add <file>`**
   - Ingests document with progress tracking
   - Shows: loading → chunking → embedding → storing
   - Reports: document ID, chunk count, path

2. **`ragged query "<question>"`**
   - Retrieves relevant chunks
   - Generates answer with LLM
   - Shows citations and sources
   - Options: `--show-sources`, `-k <number>`

3. **`ragged list`**
   - Shows collection statistics
   - Displays: collection name, total chunks
   - Note about v0.2 document-level listing

4. **`ragged clear`**
   - Clears all documents
   - Confirmation prompt (unless `--force`)
   - Reports chunks removed

5. **`ragged config show`**
   - Displays all configuration settings
   - Table format with Rich
   - Shows: models, URLs, chunk settings

6. **`ragged health`**
   - Checks Ollama connectivity
   - Checks ChromaDB connectivity
   - Shows chunk count
   - Color-coded status indicators

### Dependencies Installed
```bash
pip install click rich
```

### Challenges & Solutions
- **Challenge**: Progress bar integration with long operations
  - **Solution**: Rich Progress with task updates
- **Challenge**: Error handling and user feedback
  - **Solution**: Try/except with console.print formatting

### Lessons Learned
- Click makes CLI development straightforward
- Rich dramatically improves terminal UX
- Progress feedback essential for long operations
- Clear error messages prevent user frustration

---

## Phase 9: End-to-End Integration ⏳

**Status:** Pending
**Estimated Duration**: 24-40 hours

### Goals
- Verify complete pipeline functionality
- Create integration test suite
- Test with real documents

### Planned Deliverables
- [ ] Integration test suite (`tests/integration/`)
- [ ] End-to-end workflow tests
- [ ] Sample document corpus for testing
- [ ] Performance benchmarks
- [ ] Edge case testing

### Test Scenarios
1. **Full Pipeline**: PDF ingestion → chunking → embedding → storage → retrieval → generation
2. **Multi-Format**: Test with PDF, TXT, MD, HTML
3. **Large Documents**: Test with 100+ page PDFs
4. **Multiple Documents**: Test with document corpus
5. **Query Quality**: Test retrieval relevance
6. **Citation Accuracy**: Verify correct source attribution

### Dependencies
- Phases 1-8 must be complete (✅)
- Test document corpus needed
- ChromaDB and Ollama services running

---

## Phase 10: Docker Integration ⏳

**Status:** Pending
**Estimated Duration**: 16-24 hours

### Goals
- Fix Docker Compose setup
- Resolve Python 3.14 compatibility issues
- Enable containerized development

### Planned Deliverables
- [ ] Working `docker-compose.yml`
- [ ] Dockerfile for ragged-app
- [ ] Python 3.14 dependency compatibility
- [ ] Volume mounts for development
- [ ] Service health checks

### Known Issues
- Python 3.14 with chromadb dependency conflicts
- onnxruntime and pulsar-client missing wheels
- PYTHONPATH configuration for imports

### Blockers
- ChromaDB Python 3.14 compatibility
- Consider downgrading to Python 3.11 or waiting for dependencies

---

## Phase 11: Documentation 🚧

**Status:** In Progress (~50% complete)
**Estimated Remaining**: 20-36 hours

### Goals
- Complete user documentation
- Finish developer documentation
- Organise development logs

### Deliverables
- [x] README.md updates
- [x] Development log organisation
- [ ] User guide (`docs/user-guide.md`)
- [ ] Installation instructions
- [ ] Configuration guide
- [ ] CLI reference
- [ ] API documentation (docstrings)
- [ ] Architecture documentation
- [ ] Troubleshooting guide

### Current Progress
- ✅ README.md updated with v0.1 status
- ✅ Development log structure created
- ✅ Archive of working documents
- 🚧 README.md, timeline.md, phases.md created
- ⏳ User-facing documentation pending

---

## Phase 12: Security Audit & Code Review ⏳

**Status:** Pending
**Estimated Duration**: 16-24 hours

### Goals
- Comprehensive security review
- Code quality assessment
- Vulnerability scanning

### Planned Deliverables
- [ ] Security audit report
- [ ] Code review findings
- [ ] Vulnerability assessment
- [ ] Remediation plan
- [ ] Security best practices documentation

### Review Areas
1. **Input Validation**: File paths, sizes, MIME types
2. **Path Traversal**: Security utility effectiveness
3. **Injection Attacks**: Command injection, SQL injection (N/A)
4. **Secret Management**: No hardcoded credentials
5. **Dependency Vulnerabilities**: pip-audit scan
6. **Logging Security**: PII filtering effectiveness
7. **Error Handling**: No information leakage

### Tools to Use
- codebase-security-auditor agent
- pip-audit for dependency scanning
- bandit for Python security linting

---

## Phase 13: Testing & Coverage ⏳

**Status:** Pending
**Estimated Duration**: 24-40 hours

### Goals
- Expand test coverage to 80%+
- Add missing unit tests
- Create integration tests
- Establish quality metrics

### Planned Deliverables
- [ ] Expanded unit test suite
- [ ] Integration test suite
- [ ] Coverage report (target: 80%+)
- [ ] Test documentation
- [ ] CI/CD pipeline (optional)

### Current Coverage
- **Overall**: 96% (Phase 1 modules only)
- **Config**: 92%
- **Logging**: 100%
- **Models**: 97%

### Gaps to Fill
- Chunking module tests
- Embeddings module tests
- Storage module tests
- Retrieval module tests
- Generation module tests
- CLI module tests

---

## Phase 14: Git Commit & Release ⏳

**Status:** Pending (Core implementation committed)
**Estimated Duration**: 4-8 hours

### Goals
- Final code review
- Complete git commit
- Tag release
- Publish documentation

### Deliverables
- [ ] Final code review
- [ ] Clean commit history
- [ ] v0.1.0 git tag
- [ ] GitHub release notes
- [ ] Published documentation

### Completed
- ✅ Core implementation committed (commit 0c67784)
- ✅ Comprehensive commit message
- ✅ Development log structure

### Pending
- Code review for remaining phases
- Final integration commit
- Version tagging
- Release notes

---

## Summary

### Completed Phases (8/14)
✅ Phase 1: Foundation
✅ Phase 2: Document Ingestion
✅ Phase 3: Chunking
✅ Phase 4: Embeddings
✅ Phase 5: Vector Storage
✅ Phase 6: Retrieval
✅ Phase 7: Generation
✅ Phase 8: CLI

### In Progress (1/14)
🚧 Phase 11: Documentation (~50% complete)

### Pending (5/14)
⏳ Phase 9: End-to-End Integration
⏳ Phase 10: Docker Integration
⏳ Phase 12: Security Audit
⏳ Phase 13: Testing & Coverage
⏳ Phase 14: Git Commit & Release

### Overall Progress
- **Phases**: 8/14 complete (57%)
- **Core Features**: 100% complete
- **Quality Assurance**: 0% complete
- **Documentation**: 50% complete

### Next Priority
1. Complete Phase 11 (Documentation)
2. Execute Phase 9 (Integration Tests)
3. Execute Phase 12 (Security Audit)
4. Execute Phase 13 (Coverage Expansion)
5. Resolve Phase 10 (Docker) or defer to v0.2
6. Execute Phase 14 (Release)

---

**Last Updated**: 2025-11-09
**Status:** Core implementation complete, quality phases in progress
