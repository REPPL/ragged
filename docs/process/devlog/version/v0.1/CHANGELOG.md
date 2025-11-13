# Changelog - v0.1

All notable changes to ragged v0.1 documented here, following [Keep a Changelog](https://keepachangelog.com/en/1.0.0/) format.

## [Unreleased]

### To Do
- Complete integration tests (Phase 9)
- Fix Docker compatibility (Phase 10)
- Expand test coverage to 80%+ (Phase 13)
- Security audit (Phase 12)
- User documentation (Phase 11)

## [0.1.0] - 2025-11-09

### Added

#### Foundation (Phase 1)
- Pydantic-based configuration system with environment variable support
- Privacy-safe logging with automatic PII filtering
- Security utilities (path validation, file size limits, MIME checking)
- Document models (Document, Chunk, DocumentMetadata, ChunkMetadata)
- Test infrastructure with pytest and coverage
- Pre-commit hooks (black, ruff, mypy)

#### Document Ingestion (Phase 2)
- PDF loader using PyMuPDF4LLM with markdown conversion
- TXT loader with automatic encoding detection (chardet)
- Markdown loader with title extraction
- HTML loader using Trafilatura for clean extraction
- Automatic format detection via MIME types
- Security validation on all file operations

#### Chunking System (Phase 3)
- Token counter using tiktoken (cl100k_base encoding)
- RecursiveCharacterTextSplitter for semantic-aware chunking
- Configurable chunk size (default: 500 tokens) and overlap (default: 100)
- Metadata preservation through chunking pipeline
- LRU cache optimisation for tokenizer access

#### Embeddings (Phase 4)
- BaseEmbedder abstract interface
- SentenceTransformers embedder with device detection (CPU/CUDA/MPS)
- Ollama embedder with retry logic and exponential backoff
- Factory pattern for runtime model selection
- Support for all-MiniLM-L6-v2 (384 dims) and nomic-embed-text (768 dims)

#### Vector Storage (Phase 5)
- ChromaDB HTTP client integration
- Full CRUD operations (add, query, delete, count, clear)
- Health checking via heartbeat
- Metadata filtering support
- Collection management utilities

#### Retrieval (Phase 6)
- Semantic similarity search with top-k retrieval
- RetrievedChunk dataclass for structured results
- Score-based filtering
- Deduplication support
- Metadata query filtering

#### Generation (Phase 7)
- Ollama LLM client with model verification
- RAG-specific system prompts
- Prompt construction from retrieved chunks
- Citation extraction with regex (`[Source: filename]` format)
- Streaming support (for future use)
- CLI-friendly response formatting

#### CLI (Phase 8)
- Click-based command-line interface
- Rich terminal formatting (tables, progress bars, colors)
- `ragged add` command with progress tracking
- `ragged query` command with citation display
- `ragged list` command for collection statistics
- `ragged clear` command with confirmation
- `ragged config show` command
- `ragged health` command for service checks
- User-friendly error handling

#### Documentation
- README.md updates with current status
- Development log structure (Planning/Implementation/Retrospective)
- Comprehensive devlog with 12 organised files
- Implementation plans and checklists
- Architecture decision records (14 decisions)
- Technical implementation notes

### Changed
- Migrated from Pydantic v1 `class Config` to v2 `model_config = ConfigDict()`
- Improved test isolation with `clean_env` fixture
- Enhanced error messages throughout codebase

### Fixed
- Test environment pollution between tests
- Pydantic v2 deprecation warnings
- ChromaDB result parsing for nested lists
- File encoding issues with non-UTF-8 text files
- Path traversal vulnerabilities

### Security
- Implemented path traversal prevention
- Added file size validation (100MB limit)
- Added MIME type validation
- Implemented PII filtering in logs
- Ensured no hardcoded credentials
- Local-only processing (no external API calls)

## Version History

### v0.1.0 (2025-11-09)
- **Status**: Core implementation complete (Phases 1-8)
- **Features**: Full RAG pipeline with CLI
- **Coverage**: 96% (Phase 1 modules)
- **Lines of Code**: ~3,000+
- **Tests**: 44 passing
- **Time**: ~70 hours

### Next Version (v0.2)
- Web UI (FastAPI + React)
- Enhanced retrieval with context windows
- Few-shot prompting
- Document-level metadata tracking
- Improved Docker support

---

**Note**: This changelog covers development of v0.1. For changes after release, see the main CHANGELOG.md in the project root.

**Format**: Based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/)
**Versioning**: Follows [Semantic Versioning](https://semver.org/spec/v2.0.0.html)
