# Changelog

All notable changes to ragged will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Fixed
- **BUG-006: Memory Leaks in Batch Processing**: Fixed memory accumulation during large batch document processing
  - Added memory monitoring using psutil to track process memory usage
  - Implemented configurable memory limits (default: 80% of available RAM)
  - Added automatic garbage collection after each document to free memory promptly
  - Added explicit deletion of large objects (embeddings, chunk_texts, metadatas) to accelerate memory release
  - Integrated MemoryLimitExceededError exception for graceful memory limit handling
  - Memory usage now remains stable during large batch operations (50+ documents)
  - All 23 batch processing tests pass with 95% coverage

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
