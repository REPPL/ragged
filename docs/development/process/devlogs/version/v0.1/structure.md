# v0.1 Project Structure

**Purpose**: Explain project organisation, module layout, and file conventions

This document provides a comprehensive overview of ragged's project structure, explaining how code is organised and why.

## Table of Contents
1. [Directory Tree](#directory-tree)
2. [Module Purposes](#module-purposes)
3. [File Organisation Principles](#file-organisation-principles)
4. [Import Patterns](#import-patterns)
5. [Configuration Structure](#configuration-structure)
6. [Test Organisation](#test-organisation)

---

## Directory Tree

```
ragged/
├── src/                                # Source code
│   ├── __init__.py                     # Package init with version
│   ├── main.py                         # CLI entry point (323 lines)
│   │
│   ├── config/                         # Configuration management
│   │   ├── __init__.py                 # Exports get_settings
│   │   └── settings.py                 # Pydantic settings (148 lines)
│   │
│   ├── ingestion/                      # Document loading and models
│   │   ├── __init__.py                 # Exports models
│   │   ├── models.py                   # Document/Chunk/Metadata (167 lines)
│   │   └── loaders.py                  # PDF/TXT/MD/HTML loaders (283 lines)
│   │
│   ├── chunking/                       # Text chunking system
│   │   ├── __init__.py                 # Module init
│   │   ├── token_counter.py            # tiktoken integration (76 lines)
│   │   └── splitters.py                # Recursive splitter (201 lines)
│   │
│   ├── embeddings/                     # Embedding generation
│   │   ├── __init__.py                 # Module init
│   │   ├── base.py                     # BaseEmbedder ABC (117 lines)
│   │   ├── sentence_transformer.py     # ST embedder (82 lines)
│   │   ├── ollama_embedder.py          # Ollama embedder (133 lines)
│   │   └── factory.py                  # Factory pattern (78 lines)
│   │
│   ├── storage/                        # Vector storage
│   │   ├── __init__.py                 # Module init
│   │   └── vector_store.py             # ChromaDB wrapper (194 lines)
│   │
│   ├── retrieval/                      # Semantic search
│   │   ├── __init__.py                 # Exports Retriever
│   │   └── retriever.py                # Retriever class (181 lines)
│   │
│   ├── generation/                     # LLM generation
│   │   ├── __init__.py                 # Exports all generation classes
│   │   ├── ollama_client.py            # Ollama client (163 lines)
│   │   ├── prompts.py                  # RAG prompts (89 lines)
│   │   └── response_parser.py          # Citation parsing (91 lines)
│   │
│   └── utils/                          # Utilities
│       ├── __init__.py                 # Module init
│       ├── logging.py                  # Privacy-safe logging (166 lines)
│       └── security.py                 # Security validation (215 lines)
│
├── tests/                              # Test suite (mirrors src/)
│   ├── __init__.py                     # Test package init
│   ├── conftest.py                     # Shared fixtures (72 lines)
│   │
│   ├── config/
│   │   ├── __init__.py
│   │   └── test_settings.py            # 16 tests, 92% coverage
│   │
│   ├── ingestion/
│   │   ├── __init__.py
│   │   └── test_models.py              # 16 tests, 97% coverage
│   │
│   ├── chunking/
│   │   ├── test_token_counter.py       # Token counting tests
│   │   └── test_splitters.py           # Splitter tests
│   │
│   └── utils/
│       ├── __init__.py
│       └── test_logging.py             # 12 tests, 100% coverage
│
├── docs/                               # Documentation
│   ├── development/                    # Development docs
│   │   ├── devlog/                     # Development logs
│   │   │   └── v0.1/                   # v0.1 development log
│   │   │       ├── README.md           # Entry point
│   │   │       ├── archive/            # Original working docs
│   │   │       ├── timeline.md         # Timeline & estimates
│   │   │       ├── phases.md           # Phase breakdown
│   │   │       ├── checklist.md        # Implementation checklist
│   │   │       ├── decisions.md        # Architecture decisions
│   │   │       ├── implementation-notes.md  # Technical details
│   │   │       ├── structure.md        # This file
│   │   │       ├── lessons-learned.md  # Retrospective
│   │   │       ├── testing.md          # Test strategy
│   │   │       ├── CHANGELOG.md        # Version changelog
│   │   │       └── summary.md          # Executive summary
│   │   │
│   │   └── plans/                      # Implementation plans
│   │       └── v0.1-implementation-plan.md
│   │
│   ├── explanation/                    # Conceptual documentation
│   ├── implementation/                 # Implementation guides
│   ├── research/                       # Research and references
│   └── templates/                      # Document templates
│
├── .github/                            # GitHub configuration
│   └── workflows/                      # CI/CD (future)
│
├── .env.example                        # Example environment variables
├── .gitignore                          # Git ignore rules
├── .pre-commit-config.yaml             # Pre-commit hooks config
├── docker-compose.yml                  # Docker services (partial)
├── Dockerfile                          # ragged-app container (partial)
├── pyproject.toml                      # Project metadata & tools
├── README.md                           # Project README
└── setup.py                            # Package setup (if needed)
```

**Total Lines of Code**: ~3,000+ (excluding tests and docs)
**Total Test Lines**: ~1,000+
**Total Documentation**: ~30,000+ words

---

## Module Purposes

### `src/config/`
**Purpose**: Application configuration management

**Files**:
- `settings.py`: Pydantic-based settings with env var support

**Responsibilities**:
- Parse environment variables
- Validate configuration
- Provide sensible defaults
- Singleton settings access via `get_settings()`

**Key Classes**:
- `Settings`: Main settings class
- `Environment`: Enum for env types
- `EmbeddingModel`: Enum for embedding models

### `src/ingestion/`
**Purpose**: Document loading and data models

**Files**:
- `models.py`: Pydantic models for Document, Chunk, Metadata
- `loaders.py`: Format-specific loaders (PDF, TXT, MD, HTML)

**Responsibilities**:
- Load documents from various formats
- Convert to common intermediate format (markdown)
- Extract metadata (file size, hash, etc.)
- Security validation (path, size, MIME type)

**Key Classes**:
- `Document`: Main document model
- `Chunk`: Document chunk with metadata
- `DocumentMetadata`, `ChunkMetadata`: Metadata models

**Key Functions**:
- `load_document()`: Main loader with auto-detection
- `load_pdf()`, `load_txt()`, `load_markdown()`, `load_html()`: Format-specific loaders

### `src/chunking/`
**Purpose**: Text chunking with token awareness

**Files**:
- `token_counter.py`: tiktoken integration
- `splitters.py`: Text splitting strategies

**Responsibilities**:
- Count tokens accurately
- Split text at semantic boundaries
- Respect token limits
- Add overlap for context

**Key Classes**:
- `RecursiveCharacterTextSplitter`: Main splitter

**Key Functions**:
- `get_tokenizer()`: Cached tokenizer access
- `count_tokens()`: Accurate token counting
- `chunk_document()`: Document-to-chunks conversion

### `src/embeddings/`
**Purpose**: Embedding generation with multiple backends

**Files**:
- `base.py`: Abstract base class
- `sentence_transformer.py`: sentence-transformers implementation
- `ollama_embedder.py`: Ollama implementation
- `factory.py`: Factory pattern

**Responsibilities**:
- Generate embeddings for text
- Support multiple backends
- Batch processing
- Device detection (CPU/CUDA/MPS)

**Key Classes**:
- `BaseEmbedder`: Abstract interface
- `SentenceTransformerEmbedder`: Local embeddings
- `OllamaEmbedder`: Ollama embeddings

**Key Functions**:
- `create_embedder()`: Factory method
- `get_embedder()`: Singleton access

### `src/storage/`
**Purpose**: Vector database integration

**Files**:
- `vector_store.py`: ChromaDB wrapper

**Responsibilities**:
- Store embeddings in ChromaDB
- Semantic similarity search
- CRUD operations
- Collection management

**Key Classes**:
- `VectorStore`: Main storage class

**Key Methods**:
- `add()`: Store embeddings
- `query()`: Similarity search
- `delete()`: Remove entries
- `clear()`: Clear collection

### `src/retrieval/`
**Purpose**: Semantic search and result ranking

**Files**:
- `retriever.py`: Retriever class

**Responsibilities**:
- Query embedding
- Vector similarity search
- Result parsing and ranking
- Deduplication

**Key Classes**:
- `Retriever`: Main retrieval class
- `RetrievedChunk`: Result dataclass

**Key Methods**:
- `retrieve()`: Main retrieval method
- `deduplicate_chunks()`: Remove duplicates

### `src/generation/`
**Purpose**: LLM-based answer generation

**Files**:
- `ollama_client.py`: Ollama LLM client
- `prompts.py`: RAG prompt templates
- `response_parser.py`: Response parsing

**Responsibilities**:
- Generate answers using LLM
- Construct RAG prompts
- Parse citations
- Format responses

**Key Classes**:
- `OllamaClient`: LLM client
- `GeneratedResponse`: Response dataclass

**Key Functions**:
- `build_rag_prompt()`: Prompt construction
- `parse_response()`: Citation extraction
- `format_response_for_cli()`: CLI formatting

### `src/utils/`
**Purpose**: Shared utilities and helpers

**Files**:
- `logging.py`: Privacy-safe logging setup
- `security.py`: Security validation functions

**Responsibilities**:
- Logging configuration
- PII filtering
- Path validation
- File size checking
- MIME type validation

**Key Functions**:
- `setup_logging()`: Configure logging
- `get_logger()`: Get module logger
- `validate_file_path()`: Path validation
- `validate_file_size()`: Size validation

### `src/main.py`
**Purpose**: CLI entry point

**Responsibilities**:
- Command-line interface
- Orchestrate pipeline
- Progress feedback
- Error handling

**Commands**:
- `add`: Ingest documents
- `query`: Ask questions
- `list`: Show statistics
- `clear`: Clear database
- `config show`: Display configuration
- `health`: Check services

---

## File Organisation Principles

### 1. **Separation by Concern**
Each module handles one aspect of RAG:
- `config`: Settings
- `ingestion`: Loading
- `chunking`: Splitting
- `embeddings`: Vectorization
- `storage`: Persistence
- `retrieval`: Search
- `generation`: Answering
- `utils`: Cross-cutting concerns

### 2. **Single Responsibility**
Each file has a clear, single purpose:
- `settings.py`: Only configuration
- `loaders.py`: Only document loading
- `vector_store.py`: Only vector storage

### 3. **Dependency Flow**
```
config ← utils
   ↓
ingestion/models → chunking → embeddings → storage
                      ↓           ↓          ↓
                  retrieval ←──────────────┘
                      ↓
                  generation
                      ↓
                    main (CLI)
```

### 4. **Test Mirroring**
Test structure mirrors source:
```
src/config/settings.py → tests/config/test_settings.py
src/utils/logging.py → tests/utils/test_logging.py
```

### 5. **Module Exports**
Each `__init__.py` explicitly exports public API:

```python
# src/embeddings/__init__.py
from src.embeddings.base import BaseEmbedder
from src.embeddings.factory import create_embedder, get_embedder

__all__ = ["BaseEmbedder", "create_embedder", "get_embedder"]
```

---

## Import Patterns

### Absolute Imports
Always use absolute imports from `src`:

```python
# Good
from src.config.settings import get_settings
from src.ingestion.models import Document
from src.embeddings.factory import get_embedder

# Bad
from ..config import settings
from ...utils import logging
```

### Conditional Imports
For optional dependencies:

```python
try:
    import chromadb
except ImportError:
    chromadb = None

# Later:
if chromadb is None:
    raise ImportError("chromadb required: pip install chromadb")
```

### Type Hints with TYPE_CHECKING
For avoiding circular imports:

```python
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.storage.vector_store import VectorStore
```

### Lazy Imports in CLI
Import heavy dependencies only when needed:

```python
def add(file_path: Path):
    from src.ingestion.loaders import load_document  # Import here
    from src.embeddings.factory import get_embedder
    # ...
```

---

## Configuration Structure

### Environment Variables
All configuration via `RAGGED_*` env vars:

```bash
RAGGED_ENVIRONMENT=development
RAGGED_LOG_LEVEL=INFO
RAGGED_EMBEDDING_MODEL=sentence-transformers
RAGGED_EMBEDDING_MODEL_NAME=all-MiniLM-L6-v2
RAGGED_LLM_MODEL=llama3.2
RAGGED_CHUNK_SIZE=500
RAGGED_CHUNK_OVERLAP=100
RAGGED_CHROMA_URL=http://localhost:8001
RAGGED_OLLAMA_URL=http://localhost:11434
```

### .env File
Use `.env` for local development:

```bash
# .env
RAGGED_ENVIRONMENT=development
RAGGED_LOG_LEVEL=DEBUG
```

Loaded automatically by Pydantic's `BaseSettings`.

### Settings Access
Always via singleton:

```python
from src.config.settings import get_settings

settings = get_settings()
chunk_size = settings.chunk_size  # Type-safe access
```

---

## Test Organisation

### Structure Mirrors Source
```
src/
└── config/settings.py

tests/
└── config/test_settings.py
```

### Shared Fixtures
Common fixtures in `conftest.py`:

```python
# tests/conftest.py
@pytest.fixture
def sample_document():
    return Document(content="Test", metadata=...)

@pytest.fixture(autouse=True)
def clean_env():
    # Clear env vars before/after each test
```

### Test Files
One test file per source file:

```
src/utils/logging.py → tests/utils/test_logging.py
src/ingestion/models.py → tests/ingestion/test_models.py
```

### Test Naming
```python
class TestSettings:
    def test_default_values(self):
        ...

    def test_env_var_override(self):
        ...

def test_load_pdf_success():
    ...

def test_load_pdf_missing_file():
    ...
```

---

## File Naming Conventions

### Python Files
- Lowercase with underscores: `token_counter.py`, `ollama_client.py`
- Descriptive names: `settings.py`, not `config.py`

### Test Files
- Prefix with `test_`: `test_settings.py`, `test_logging.py`
- Mirror source file name: `loaders.py` → `test_loaders.py`

### Documentation
- Lowercase with hyphens: `implementation-notes.md`, `lessons-learned.md`
- All caps for special files: `README.md`, `CHANGELOG.md`, `summary.md`

### Directories
- Lowercase, no underscores: `config/`, `ingestion/`, `retrieval/`
- Plural for collections: `embeddings/`, `utils/`
- Singular for modules: `generation/`, `retrieval/`

---

## Module Dependencies

### Dependency Graph
```
utils ──┐
        ├→ config ──┐
        │           ├→ ingestion/models ──┐
        │           │                     ├→ ingestion/loaders ──┐
        │           │                     │                      │
        │           ├→ chunking ←─────────┘                      │
        │           │     ↓                                      │
        │           ├→ embeddings ←───────────────────────────────┘
        │           │     ↓
        │           ├→ storage ←─────────────────────────────────┘
        │           │     ↓
        │           ├→ retrieval ←────────┘
        │           │     ↓
        │           └→ generation ←───────┘
        │                 ↓
        └─────────────→ main (CLI)
```

### No Circular Dependencies
Strict hierarchy:
- Lower modules don't import from higher modules
- `utils` and `config` are foundational (no deps)
- `main` is top-level (imports everything)

---

## Code Statistics

### Source Code
- **Total Files**: 25+ implementation files
- **Total Lines**: ~3,000+
- **Average File Size**: ~120 lines

### Tests
- **Total Tests**: 44+ (Phase 1)
- **Coverage**: 96% (Phase 1 modules)
- **Test Files**: 8+ files

### Documentation
- **Devlog Files**: 12 files
- **Total Words**: ~30,000+
- **Archive Files**: 5 files

---

## Future Structure Considerations

### For v0.2
- Add `src/api/` for web API endpoints
- Add `src/web/` for web interface
- Add `src/evaluation/` for RAG metrics
- Consider `src/cache/` for query caching

### For v0.3
- Add `src/reranking/` for result reranking
- Add `src/graph/` for knowledge graph
- Add `src/multimodal/` for images/audio

### For v1.0
- Add `src/deploy/` for deployment utilities
- Add `src/monitoring/` for metrics
- Add `src/optimisation/` for performance tuning

---

**Last Updated**: 2025-11-09
**Version**: 0.1.0
**Status:** Core structure complete
