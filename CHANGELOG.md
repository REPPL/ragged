# Changelog

All notable changes to ragged will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.2.5] - 2025-11-17

### Improved
- **QUALITY-001: Settings Side Effects**: Refactored `get_settings()` to eliminate global state mutation
  - Removed side effects preventing test fixture isolation
  - Fixed `get_logger()` to not depend on settings globally
  - Added `reset_settings()` utility for test isolation
  - Test suite isolation improved, no more test pollution
- **QUALITY-002: Bare Exception Handler**: Fixed bare `except:` clause catching BaseException
  - Changed to `except Exception:` in `logging.py:43`
  - Ensures keyboard interrupts and system exits work correctly
- **QUALITY-004: Exception Handler Improvements**: Improved 26 exception handlers across 7 files
  - Changed from `logger.error()` to `logger.exception()` for automatic traceback logging
  - Files: chunking (4), embeddings (3), ingestion (3), retrieval (1)
  - Debugging significantly easier with complete traceback information
- **QUALITY-005: Magic Numbers Extraction**: Extracted 13 hardcoded values to constants
  - New `constants.py` module with chunking, embedding, retrieval, generation, BM25, caching, security constants
  - Single source of truth for configuration values
  - Easier system tuning and parameter adjustment
- **QUALITY-006: Comprehensive Type Hints**: Complete type safety with mypy strict mode
  - Added strict mypy configuration with `--strict` flag
  - Fixed 21 generic type parameter errors (`dict`, `list`, `Callable`)
  - **Zero mypy errors across all 46 source files**
  - Better IDE autocomplete and type-related bug prevention
- **QUALITY-007: Exception Handler Standardisation**: Standardised 13 more exception handlers
  - Consistent exception handling in web/API layer (5 files)
  - All handlers preserve stack traces with `logger.exception()`
  - Improved error debugging throughout application
- **QUALITY-010: Exception Chaining**: Added exception chaining to preserve complete stack traces
  - Added `from e` to 2 exception re-raise locations (`security.py`, `path_utils.py`)
  - Follows PEP 3134 exception chaining best practices
  - Complete stack traces now preserved during exception re-raising
- **QUALITY-011: Contextual Overlap Calculation**: Accurate overlap metadata for chunk relationships
  - Implemented `_calculate_overlap()` method in ContextualChunker
  - Finds longest suffix/prefix match between consecutive chunks
  - 4 comprehensive tests verifying overlap accuracy
  - Enables better quality assessment of chunking strategies

### Added
- **QUALITY-003: Chunking Tests**: Comprehensive test coverage for chunking module
  - New `test_splitters.py` with 19 tests
  - Coverage: 0% → 85% for `chunking/splitters.py` (166 statements)
  - Tests for recursive, token-based, and sentence splitters
  - Fixed `chunk_document()` metadata bug (missing `chunk_index`)
- **QUALITY-008: Citation Parser Tests**: Complete test coverage for IEEE citation formatting
  - New `test_citation_formatter.py` with 28 tests
  - Coverage: 0% → 100% for `citation_formatter.py` (39 statements)
  - Tests for `extract_citation_numbers()`, `format_ieee_reference()`, `format_reference_list()`, `format_inline_citation()`
- **QUALITY-009: TODO Cleanup**: Documented future enhancements as GitHub issues
  - Created `todo-github-issues.md` documenting 2 future enhancements
  - Contextual overlap calculation (line 146)
  - Token-based context truncation (line 267)
  - Zero obsolete TODOs remaining in codebase
- **QUALITY-012: Integration Test Coverage**: Fixed and enabled multi-format integration tests
  - Created `sample_pdf` fixture using pymupdf/fitz for dynamic PDF generation
  - Fixed all 9 integration tests to use correct API (module-level `chunk_document()`, proper attribute names)
  - Full pipeline integration verified across TXT, MD, HTML, PDF formats
  - All tests passing with proper fixture isolation

### Technical Details
- **Test Coverage**: +70 new tests added (66 unit + 4 contextual overlap)
- **Type Safety**: 100% strict mypy compliance (0 errors in 46 files)
- **Code Quality**: 26 exception handlers improved, 13 constants extracted, 2 exception chains added
- **Breaking Changes**: None (full backward compatibility maintained)
- **Completion**: All 12 planned quality improvements successfully implemented (QUALITY-001 through QUALITY-012)

### Quality Metrics
- Type Coverage: 100% (zero mypy --strict errors)
- Exception Handling: 26 handlers using `logger.exception()`, 2 exception chains added
- Magic Numbers: 13 values extracted to constants
- TODO Cleanup: 0 obsolete TODOs
- Integration Tests: 9 tests covering TXT, MD, HTML, PDF formats
- Development Time: ~15 hours (vs. 13-20h estimated)

## [0.2.4] - 2025-11-17

### Added
- **BUG-004: Custom Exception System**: Hierarchical exception structure with context-aware error messages
  - New `exceptions.py` module with base `RaggedError` and specialised exceptions
  - Organised by component: Ingestion, Storage, Retrieval, Generation, Configuration, Validation, Resource, API
  - Context-aware exceptions (e.g., `UnsupportedFormatError` lists supported formats)
  - Helper function `wrap_exception()` for third-party exception handling
  - 41 tests, 100% coverage
- **BUG-005: Secure Path Utilities**: Comprehensive path handling with security protections
  - New `path_utils.py` module with secure path operations
  - `safe_join()` prevents directory traversal attacks
  - Path normalisation, validation, and sanitisation functions
  - Utilities: directory creation, size calculation, hidden path detection
  - Handles symlinks, relative paths, special characters, spaces consistently
  - 51 tests, 100% coverage
- **BUG-007: ChromaDB Metadata Serialisation**: Complex metadata type support for ChromaDB
  - New `metadata_serialiser.py` module with automatic type conversion
  - Path objects → str, datetime → ISO format, lists/dicts → JSON
  - None values removed during serialisation (ChromaDB compatibility)
  - Transparent deserialisation on retrieval restores original types
  - Integrated into VectorStore methods: `add()`, `query()`, `get_documents_by_metadata()`
  - 30 tests, 95% coverage

### Fixed
- **BUG-006: Memory Leaks in Batch Processing**: Stable memory usage during large batch operations
  - Memory monitoring using psutil to track process usage
  - Configurable memory limits (default: 80% of available RAM)
  - Automatic garbage collection after each document
  - Explicit deletion of large objects (embeddings, chunk_texts, metadatas)
  - `MemoryLimitExceededError` exception for graceful memory limit handling
  - Tested stable with 50+ document batches
  - 23 batch tests, 95% coverage
- **BUG-008: Hybrid Retrieval Integration**: Complete system-wide hybrid retrieval
  - Added `retrieval_method` setting to config (default: "hybrid")
  - CLI query command now uses `HybridRetriever` instead of vector-only
  - Fixed parameter name consistency: `k=` instead of `top_k=` throughout codebase
  - Fixed `RetrievedChunk` attribute names in all tests
  - Configurable retrieval strategy: "hybrid", "vector", or "bm25"
  - 86 retrieval tests passing, 100% hybrid coverage
- **BUG-009: Dynamic Few-Shot Selection**: Embedding-based semantic example selection
  - Added `embedder` parameter to `FewShotExampleStore`
  - Cosine similarity search for dynamic example selection
  - Automatic fallback to keyword matching if embedder unavailable/fails
  - Examples recomputed on store load for consistency
  - Most relevant examples selected per query (improves answer quality)
  - 21 tests (3 new embedding tests), 92% coverage
- **BUG-010: Content-Based Duplicate Detection**: Efficient partial content hashing
  - Added `content_hash` field to `DocumentMetadata` and `ChunkMetadata`
  - Partial hashing: small files (≤2KB) use full hash, large files use first 1KB + last 1KB
  - Maintained `file_hash` for full content integrity checking
  - Batch duplicate detection updated to use `content_hash`
  - Detects renamed files, copied files, same content from different sources
  - 39 ingestion tests updated and passing
- **BUG-011: Page Tracking Edge Cases**: Proper page handling for all document types
  - Fixed page estimation to only apply to PDF documents
  - TXT/MD/HTML files correctly maintain `page_number=None` (no page structure)
  - PDFs continue accurate page tracking with estimation fallback
  - No crashes or incorrect page assignments for non-PDF documents

### Changed
- **Dependency Added**: `psutil>=5.9.0` for memory monitoring (BUG-006)
- **Schema Changes** (backwards-compatible with migration):
  - `DocumentMetadata` and `ChunkMetadata` now require `content_hash` field
  - Existing documents need re-ingestion for content-based duplicate detection

### Technical Details
- **Test Coverage**: 201 v0.2.4-specific tests passing, 13 skipped (TODO)
- **Component Coverage**: Exceptions (100%), Path Utils (100%), Hybrid Retrieval (100%)
- **Quality Gates**: All automated tests pass, no regressions
- **Performance**: Memory improvements outweigh minor overhead from new features
- **Security**: Path traversal prevention, input validation, secure hashing

## [0.2.2] - 2025-11-10

### Fixed
- **CLI Duplicate Detection**: Fixed UnboundLocalError when detecting duplicate documents
  - Variables now initialized before Progress context block
  - Duplicate handling wrapped in conditional check to prevent crashes
- **Python 3.12 Compatibility**: Fixed Path.is_dir() incompatibility in directory scanner
  - Removed follow_symlinks parameter (only exists in Python 3.13+)
  - Implemented manual symlink checking using is_symlink() for Python 3.12
- **Web UI Error Display**: Fixed generic "Error" messages in chat window
  - Added comprehensive error handling in respond() wrapper function
  - Now displays actual error messages (API errors, connection failures, stream parsing errors)
- **Batch Duplicate Detection**: Fixed duplicate detection in batch/folder ingestion mode
  - Added file_hash field to ChunkMetadata model for proper duplicate tracking
  - Duplicate detection now works correctly when adding same folder multiple times
- **Web UI Upload Message**: Removed confusing "(placeholder)" text from upload success messages

### Added
- **Folder Ingestion**: Recursive directory scanning and batch document processing
  - New `scanner.py` module with configurable ignore patterns (.git, node_modules, etc.)
  - New `batch.py` module for efficient multi-document processing with progress reporting
  - CLI `add` command now accepts both files and directories
  - Options: --recursive/--no-recursive, --max-depth, --fail-fast
  - Batch summary statistics: successful/duplicates/failed/total chunks
  - Auto-skips duplicates in batch mode (no interactive prompts)
- **Interactive Model Selection**: Smart model discovery and recommendations
  - New `model_manager.py` with RAG suitability scoring algorithm (1-100)
  - CLI commands: `ragged config set-model` and `ragged config list-models`
  - User configuration file support: ~/.ragged/config.yml
  - Enhanced error messages with model recommendations when model not found
- **Duplicate Handling**: Interactive overwrite prompts for duplicate documents
  - Content-based duplicate detection using SHA256 file hashing
  - Shows document details before overwrite (ID, path, chunk count)
  - Preserves document_id for referential integrity on overwrite

### Changed
- CLI `add` command parameter renamed from `file_path` to `path` (accepts files or directories)
- Python version requirement strictly enforced: 3.12.x (no longer supports 3.13+)
- Batch ingestion uses shared VectorStore and embedder instances for efficiency

### Technical Details
- Supported file extensions: .pdf, .txt, .md, .markdown, .html, .htm
- Default ignore patterns: .*, __pycache__, node_modules, .git, .venv*
- Permission errors handled gracefully with logging
- All fixes verified with manual testing and compilation checks

## [0.2.1] - 2025-11-10

### Fixed
- **Ollama Model Verification**: Fixed Ollama Python library API compatibility (ListResponse object vs dictionary)
  - Updated `ollama_client.py` to use `.models` attribute and `.model` property
  - Updated `ollama_embedder.py` with same API fixes
- **Document Ingestion**: Fixed chunk_document return value and Chunk model field name
  - `chunk_document()` now returns Document with chunks attached
  - Changed `chunk.content` to `chunk.text` throughout codebase
  - Added Path→string serialization for ChromaDB metadata compatibility
- **Default Model**: Updated default LLM model from `llama3.2:3b` to `llama3.2:latest`
- **Docker Health Check**: Corrected FastAPI health check endpoint from `/health` to `/api/health`
- **Metadata Field**: Fixed retriever to use `document_path` instead of `source_path`

### Added
- **IEEE Citation System**: Academic-quality numbered citations with formatted reference lists
  - New `citation_formatter.py` module with 4 citation formatting functions
  - Page tracking in PDF documents with `<!-- PAGE N -->` markers
  - Character-level position mapping for precise page number extraction
  - ChunkMetadata now includes `page_number` and `page_range` fields
  - 7 new page mapping helper functions in `splitters.py`
  - Updated RAG prompts to request numbered citations [1], [2], [3]
  - CLI query command now displays formatted references automatically
- **Enhanced Context**: Document chunking now preserves page information for citations

### Changed
- PDF loader now processes pages individually to enable precise citation tracking
- System prompts updated to guide LLM toward numbered citation format
- Response formatting now includes IEEE-style reference lists

### Testing
- 261 tests passing (v0.2 test suite maintained)
- All bug fixes verified on separate installation

## [0.2.0] - 2025-11-10

### Added
- **Web UI**: Gradio-based web interface with chat and document upload (port 7860)
- **FastAPI Backend**: RESTful API with SSE streaming support (port 8000)
- **Hybrid Retrieval**: BM25 keyword search + vector semantic search with Reciprocal Rank Fusion
- **Few-Shot Prompting**: Dynamic example storage and retrieval for improved answer quality
- **Contextual Chunking**: Document and section header context for better retrieval
- **Performance Caching**: LRU cache with TTL for query results (98% coverage)
- **Async Processing**: Concurrent document loading and processing with thread/process pools (91% coverage)
- **Benchmarking**: Comprehensive performance measurement utilities (99% coverage)
- **Docker Compose**: Updated with separate API and UI services, health checks for all containers

### Changed
- Python requirement upgraded from 3.10+ to 3.12+ for better library compatibility
- docker-compose.yml: Split ragged-app into ragged-api (FastAPI) and ragged-ui (Gradio)
- Documentation updated to reflect v0.2 architecture and features

### Testing
- 199 new tests for v0.2 features (100% passing)
- 262 total tests passing (199 v0.2 + 63 v0.1)
- 68% overall code coverage

### Development
- **Time**: 10 hours actual vs 61-80 hours estimated (82-86% faster with AI assistance)
- **Phases**: 8 phases completed (Environment, Backend, UI, Prompting, Performance, Docker, Testing, Release)
- **AI Assistance**: Claude Code used extensively with full transparency

## [0.1.0] - 2025-11-09

### Added
- Core RAG pipeline with ChromaDB vector storage
- Multi-format document support (PDF, TXT, Markdown, HTML)
- Dual embedding backends (sentence-transformers, Ollama)
- CLI interface with Click and Rich
- Privacy-first architecture (100% local by default)
- Recursive character text splitter with configurable chunk size/overlap
- Basic retrieval with cosine similarity
- Configuration system with environment variables
- Comprehensive logging with PII filtering
- Security features (path validation, file size limits, MIME type checking)
- Docker support with hybrid architecture (native Ollama + containerized app)

### Testing
- 63 unit and integration tests
- pytest with coverage reporting

### Documentation
- Complete implementation plan (v0.1 through v1.0)
- Architecture decision records (ADRs)
- Time-tracked development logs
- Docker setup guide for Apple Silicon
- Comprehensive README with usage examples

---

**Note**: Development of ragged uses AI-assisted coding tools transparently documented in `docs/development/`.

[0.2.0]: https://github.com/REPPL/ragged/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/REPPL/ragged/releases/tag/v0.1.0
