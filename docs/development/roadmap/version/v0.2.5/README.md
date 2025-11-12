# Ragged v0.2.5 Roadmap - Bug Fixes & Improvements

**Status**: Planned
**Timeline**: 1-2 weeks
**Estimated Hours**: 40-50 hours (with AI assistance)
**Focus**: Stability, quality, technical debt reduction
**Breaking Changes**: None

## Overview

Version 0.2.5 focuses exclusively on bug fixes, stability improvements, and technical debt reduction. This is a **critical release** that addresses several blocking issues, particularly the non-functional API endpoints that currently prevent the Web UI from working.

**Key Principles**:
- ✅ Fix bugs, don't add features
- ✅ Increase test coverage
- ✅ Improve error handling
- ✅ Integrate existing features
- ❌ No new functionality

---

## P0 - Critical Issues (12-15 hours)

These issues are blocking or severely impact functionality. **Start here.**

### BUG-001: API Endpoints Non-Functional ⚠️ CRITICAL

**Status**: 🔴 Critical - Blocks Web UI
**Priority**: P0
**Estimated Time**: 3-4 hours
**Complexity**: Medium

#### Problem
All FastAPI endpoints in `src/web/api.py` return placeholder data. The API doesn't perform actual retrieval or ingestion operations, making the Web UI completely non-functional for real use.

**Evidence**:
```python
# Line 98-101 in src/web/api.py
@app.post("/api/upload", response_model=UploadResponse)
async def upload_document(file: UploadFile = File(...)):
    # TODO: Implement actual document upload
    return UploadResponse(...)  # Placeholder!

# Line 120-123 in src/web/api.py
@app.post("/api/query", response_model=QueryResponse)
async def query_documents(request: QueryRequest):
    # TODO: Implement actual query processing
    return QueryResponse(...)  # Placeholder!
```

#### Solution

**Step 1**: Initialize services in startup event
```python
# src/web/api.py - startup_event()

# Add these imports
from src.config.settings import Settings
from src.retrieval.hybrid import HybridRetriever
from src.generation.ollama_client import OllamaClient
from src.vectorstore.chroma_store import ChromaStore
from src.embeddings.sentence_transformer import SentenceTransformerEmbedder
from src.retrieval.bm25 import BM25Retriever

# Global services
hybrid_retriever: Optional[HybridRetriever] = None
ollama_client: Optional[OllamaClient] = None
settings: Optional[Settings] = None

@app.on_event("startup")
async def startup_event():
    global hybrid_retriever, ollama_client, settings

    # Load settings
    settings = Settings()

    # Initialize vector store
    vector_store = ChromaStore(
        host=settings.chroma_host,
        port=settings.chroma_port,
        collection_name=settings.collection_name
    )

    # Initialize embedder
    embedder = SentenceTransformerEmbedder(
        model_name=settings.embedding_model
    )

    # Initialize retrievers
    vector_retriever = VectorRetriever(vector_store, embedder)
    bm25_retriever = BM25Retriever(vector_store)

    # Initialize hybrid retriever
    hybrid_retriever = HybridRetriever(
        vector_retriever=vector_retriever,
        bm25_retriever=bm25_retriever
    )

    # Initialize Ollama client
    ollama_client = OllamaClient(
        base_url=settings.ollama_base_url,
        model=settings.model
    )

    logger.info("API services initialized successfully")
```

**Step 2**: Implement actual query endpoint
```python
@app.post("/api/query", response_model=QueryResponse)
async def query_documents(request: QueryRequest):
    try:
        # Retrieve relevant chunks
        results = hybrid_retriever.retrieve(
            query=request.query,
            k=request.top_k or 5
        )

        # Build context from results
        context = "\n\n".join([
            f"[Source: {r.metadata['source']}, Page: {r.metadata.get('page', 'N/A')}]\n{r.text}"
            for r in results
        ])

        # Generate answer
        answer = ollama_client.generate(
            query=request.query,
            context=context
        )

        # Format sources
        sources = [
            Source(
                filename=r.metadata['source'],
                page=r.metadata.get('page'),
                content=r.text[:200] + "..." if len(r.text) > 200 else r.text,
                score=r.score
            )
            for r in results
        ]

        return QueryResponse(
            answer=answer,
            sources=sources,
            processing_time=0.0  # TODO: Add actual timing
        )

    except Exception as e:
        logger.error(f"Query failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
```

**Step 3**: Implement actual upload endpoint
```python
from src.ingestion.loaders import load_document
from src.chunking.splitters import RecursiveChunker

@app.post("/api/upload", response_model=UploadResponse)
async def upload_document(file: UploadFile = File(...)):
    try:
        # Save uploaded file temporarily
        temp_path = Path(f"/tmp/{file.filename}")
        with open(temp_path, "wb") as f:
            content = await file.read()
            f.write(content)

        # Load document
        document = load_document(temp_path)

        # Chunk document
        chunker = RecursiveChunker(
            chunk_size=settings.chunk_size,
            chunk_overlap=settings.chunk_overlap
        )
        chunks = chunker.chunk(document)

        # Embed chunks
        embedder = SentenceTransformerEmbedder(
            model_name=settings.embedding_model
        )
        texts = [chunk.text for chunk in chunks]
        embeddings = embedder.embed_batch(texts)

        # Store in vector database
        vector_store = ChromaStore(
            host=settings.chroma_host,
            port=settings.chroma_port,
            collection_name=settings.collection_name
        )

        metadatas = [chunk.metadata for chunk in chunks]
        vector_store.add(texts, embeddings, metadatas)

        # Clean up temp file
        temp_path.unlink()

        return UploadResponse(
            filename=file.filename,
            chunks=len(chunks),
            status="success"
        )

    except Exception as e:
        logger.error(f"Upload failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
```

#### Testing Requirements
- [ ] Integration test for `/api/query` with real documents
- [ ] Integration test for `/api/upload` with various file types
- [ ] Test error handling (invalid files, connection failures)
- [ ] Test concurrent requests
- [ ] Test with empty database

#### Files to Modify
- `src/web/api.py` (lines 50-150)

#### Acceptance Criteria
- ✅ Web UI can successfully upload documents
- ✅ Web UI can successfully query and get real answers
- ✅ All API endpoints return real data, not placeholders
- ✅ Errors are handled gracefully and logged properly

---

### BUG-002: Settings Undefined Logger Import

**Status**: 🔴 Critical - Runtime Error
**Priority**: P0
**Estimated Time**: 5 minutes
**Complexity**: Trivial

#### Problem
In `src/config/settings.py:149`, `logger.info()` and `logger.warning()` are called but logger is never imported or defined. This will cause `NameError` when those code paths are executed.

**Evidence**:
```python
# Line 149 in src/config/settings.py
logger.info(f"Loaded .env from: {env_file}")  # NameError: logger not defined!

# Line 159
logger.warning(f".env file not found at {env_file}")  # NameError!
```

#### Solution

Add import at top of file:
```python
# src/config/settings.py (add near top)
from src.utils.logging import get_logger

logger = get_logger(__name__)
```

#### Testing Requirements
- [ ] Test loading config with .env file present
- [ ] Test loading config with .env file missing
- [ ] Verify log messages appear correctly

#### Files to Modify
- `src/config/settings.py` (add 2 lines near top)

#### Acceptance Criteria
- ✅ No NameError when loading config
- ✅ Proper log messages for config loading

---

### BUG-003: Missing Test Coverage for New Modules

**Status**: 🔴 Critical - 0% Coverage
**Priority**: P0
**Estimated Time**: 6-8 hours
**Complexity**: High

#### Problem
Three modules added in v0.2.2 have **zero test coverage**:
- `src/ingestion/scanner.py` (243 lines)
- `src/ingestion/batch.py` (205 lines)
- `src/config/model_manager.py` (158 lines)

**Total untested code**: 606 lines (0% coverage)

This creates significant risk for bugs and makes refactoring dangerous.

#### Solution

Create comprehensive test files:

**1. Create `tests/ingestion/test_scanner.py`**
```python
"""Tests for document scanner."""
import pytest
from pathlib import Path
from src.ingestion.scanner import DocumentScanner

class TestDocumentScanner:
    def test_scan_directory_finds_all_supported_formats(self, tmp_path):
        """Should find PDF, TXT, MD, HTML files."""
        # Create test files
        (tmp_path / "doc.pdf").touch()
        (tmp_path / "note.txt").touch()
        (tmp_path / "readme.md").touch()
        (tmp_path / "page.html").touch()
        (tmp_path / "image.jpg").touch()  # Should ignore

        scanner = DocumentScanner()
        files = scanner.scan(tmp_path)

        assert len(files) == 4
        assert all(f.suffix in ['.pdf', '.txt', '.md', '.html'] for f in files)

    def test_scan_respects_recursive_flag(self, tmp_path):
        """Should control subdirectory scanning."""
        subdir = tmp_path / "subdir"
        subdir.mkdir()
        (tmp_path / "doc1.pdf").touch()
        (subdir / "doc2.pdf").touch()

        scanner = DocumentScanner()

        # Non-recursive
        files = scanner.scan(tmp_path, recursive=False)
        assert len(files) == 1

        # Recursive
        files = scanner.scan(tmp_path, recursive=True)
        assert len(files) == 2

    def test_scan_handles_empty_directory(self, tmp_path):
        """Should return empty list for empty directory."""
        scanner = DocumentScanner()
        files = scanner.scan(tmp_path)
        assert files == []

    def test_scan_handles_symlinks(self, tmp_path):
        """Should handle symbolic links appropriately."""
        # Test symlink handling
        # TODO: Define policy - follow or skip symlinks?
        pass

    def test_scan_filters_hidden_files(self, tmp_path):
        """Should skip hidden files (starting with .)."""
        (tmp_path / ".hidden.pdf").touch()
        (tmp_path / "visible.pdf").touch()

        scanner = DocumentScanner()
        files = scanner.scan(tmp_path)

        assert len(files) == 1
        assert files[0].name == "visible.pdf"
```

**2. Create `tests/ingestion/test_batch.py`**
```python
"""Tests for batch ingestion."""
import pytest
from pathlib import Path
from src.ingestion.batch import BatchIngester
from src.config.settings import Settings

class TestBatchIngester:
    def test_batch_ingest_multiple_documents(self, tmp_path, mock_vector_store):
        """Should ingest multiple documents successfully."""
        # Create test files
        files = []
        for i in range(3):
            f = tmp_path / f"doc{i}.txt"
            f.write_text(f"Content of document {i}")
            files.append(f)

        settings = Settings()
        ingester = BatchIngester(settings)

        results = ingester.ingest_batch(files)

        assert len(results) == 3
        assert all(r.status == "success" for r in results)

    def test_batch_ingest_detects_duplicates(self, tmp_path, mock_vector_store):
        """Should skip duplicate documents."""
        # Create same file twice
        f1 = tmp_path / "doc1.txt"
        f2 = tmp_path / "doc2.txt"
        f1.write_text("Same content")
        f2.write_text("Same content")

        ingester = BatchIngester(Settings())
        results = ingester.ingest_batch([f1, f2])

        assert results[0].status == "success"
        assert results[1].status == "duplicate"

    def test_batch_ingest_handles_errors_gracefully(self, tmp_path):
        """Should continue on errors, not crash."""
        # Create corrupt and valid files
        corrupt = tmp_path / "corrupt.pdf"
        corrupt.write_bytes(b"Not a real PDF")

        valid = tmp_path / "valid.txt"
        valid.write_text("Valid content")

        ingester = BatchIngester(Settings())
        results = ingester.ingest_batch([corrupt, valid])

        assert results[0].status == "error"
        assert results[1].status == "success"

    def test_batch_ingest_progress_reporting(self, tmp_path):
        """Should report progress during batch ingestion."""
        # Create multiple files
        files = [tmp_path / f"doc{i}.txt" for i in range(10)]
        for f in files:
            f.write_text("Content")

        ingester = BatchIngester(Settings())

        progress_updates = []
        def on_progress(current, total):
            progress_updates.append((current, total))

        ingester.ingest_batch(files, progress_callback=on_progress)

        assert len(progress_updates) == 10
        assert progress_updates[-1] == (10, 10)
```

**3. Create `tests/config/test_model_manager.py`**
```python
"""Tests for model manager."""
import pytest
from src.config.model_manager import ModelManager
from src.config.settings import Settings

class TestModelManager:
    def test_get_rag_suitability_score(self):
        """Should score models appropriately for RAG."""
        manager = ModelManager(Settings())

        # Large models should score higher
        score_large = manager.get_rag_suitability_score("llama3.2:70b")
        score_small = manager.get_rag_suitability_score("llama3.2:3b")

        assert score_large > score_small

    def test_select_best_model_for_rag(self):
        """Should select most suitable available model."""
        manager = ModelManager(Settings())

        available_models = [
            "llama3.2:3b",
            "llama3.2:70b",
            "mistral:latest"
        ]

        best = manager.select_best_model(available_models)
        assert best == "llama3.2:70b"  # Largest model

    def test_interactive_model_selection(self, monkeypatch):
        """Should allow user to select model interactively."""
        # Mock user input
        monkeypatch.setattr('builtins.input', lambda _: "1")

        manager = ModelManager(Settings())
        selected = manager.interactive_select(["model1", "model2"])

        assert selected == "model1"
```

#### Testing Requirements
- [ ] Achieve 85%+ coverage for each new module
- [ ] Test happy paths
- [ ] Test error paths
- [ ] Test edge cases (empty inputs, large inputs, etc.)

#### Files to Create
- `tests/ingestion/test_scanner.py` (~200 lines)
- `tests/ingestion/test_batch.py` (~250 lines)
- `tests/config/test_model_manager.py` (~150 lines)

#### Acceptance Criteria
- ✅ All three modules have 85%+ test coverage
- ✅ All tests pass
- ✅ Edge cases covered

---

## P1 - High Priority (20-25 hours)

These issues significantly impact quality or functionality.

### BUG-004: Inconsistent Error Handling

**Status**: 🟡 High Priority
**Priority**: P1
**Estimated Time**: 4-5 hours
**Complexity**: Medium

#### Problem
Error handling is inconsistent across the codebase:
- Some functions swallow exceptions silently
- Others don't log enough context
- Bare `except:` blocks without proper error handling
- Error messages aren't always actionable

#### Solution

**Step 1**: Audit all try/except blocks
```bash
# Find all exception handling
grep -rn "except" src/ --include="*.py" | wc -l
# Found 47 exception handlers - review each
```

**Step 2**: Define custom exceptions
```python
# src/exceptions.py (NEW FILE)
"""Custom exceptions for ragged."""

class RaggedException(Exception):
    """Base exception for all ragged errors."""
    pass

class DocumentLoadError(RaggedException):
    """Failed to load document."""
    pass

class EmbeddingError(RaggedException):
    """Failed to generate embeddings."""
    pass

class RetrievalError(RaggedException):
    """Failed to retrieve documents."""
    pass

class GenerationError(RaggedException):
    """Failed to generate answer."""
    pass

class ConfigurationError(RaggedException):
    """Invalid configuration."""
    pass
```

**Step 3**: Improve error handling patterns
```python
# BEFORE (bad)
try:
    result = some_operation()
except:
    pass  # Silent failure!

# AFTER (good)
try:
    result = some_operation()
except SpecificError as e:
    logger.error(f"Operation failed: {e}", exc_info=True, extra={
        'operation': 'some_operation',
        'input': input_data
    })
    raise DocumentLoadError(f"Failed to process document: {e}") from e
```

**Step 4**: Add context to errors
```python
# Wrap external library errors with context
try:
    pdf = pymupdf.open(file_path)
except Exception as e:
    raise DocumentLoadError(
        f"Failed to load PDF '{file_path}': {e}. "
        f"File may be corrupted or password-protected."
    ) from e
```

#### Testing Requirements
- [ ] Test that custom exceptions are raised appropriately
- [ ] Test error logging contains necessary context
- [ ] Test error messages are user-friendly

#### Files to Modify
- Create `src/exceptions.py`
- Update error handling in:
  - `src/ingestion/loaders.py`
  - `src/chunking/splitters.py`
  - `src/embeddings/` (all files)
  - `src/retrieval/` (all files)
  - `src/generation/ollama_client.py`
  - `src/main.py`

#### Acceptance Criteria
- ✅ Custom exceptions defined and used
- ✅ No bare `except:` blocks
- ✅ All errors logged with context
- ✅ Error messages are actionable

---

### BUG-005: Path Handling Edge Cases

**Status**: 🟡 High Priority
**Priority**: P1
**Estimated Time**: 3-4 hours
**Complexity**: Medium

#### Problem
Path handling has potential edge cases:
- Symlinks not handled consistently
- Relative vs absolute paths
- Special characters in filenames
- Spaces in paths
- Non-existent parent directories

#### Solution

**Create path handling utilities**:
```python
# src/utils/paths.py (NEW FILE)
"""Path handling utilities."""
from pathlib import Path
from typing import Union
import logging

logger = logging.get_logger(__name__)

def normalize_path(path: Union[str, Path], resolve_symlinks: bool = True) -> Path:
    """
    Normalize a path to absolute Path object.

    Args:
        path: Path to normalize
        resolve_symlinks: Whether to resolve symbolic links

    Returns:
        Normalized absolute Path

    Raises:
        ValueError: If path is invalid
    """
    try:
        p = Path(path)

        # Convert to absolute
        if not p.is_absolute():
            p = p.absolute()

        # Resolve symlinks if requested
        if resolve_symlinks:
            p = p.resolve()

        return p

    except Exception as e:
        raise ValueError(f"Invalid path '{path}': {e}") from e

def ensure_parent_exists(path: Path) -> None:
    """
    Ensure parent directory exists, create if necessary.

    Args:
        path: File path whose parent should exist
    """
    parent = path.parent
    if not parent.exists():
        logger.info(f"Creating directory: {parent}")
        parent.mkdir(parents=True, exist_ok=True)

def safe_filename(filename: str) -> str:
    """
    Sanitize filename to remove problematic characters.

    Args:
        filename: Original filename

    Returns:
        Safe filename
    """
    # Remove/replace problematic characters
    safe = filename.replace('/', '_').replace('\\', '_')
    safe = safe.replace('\0', '')
    return safe

def validate_file_path(
    path: Path,
    must_exist: bool = True,
    must_be_file: bool = True,
    allowed_suffixes: list[str] = None
) -> None:
    """
    Validate a file path meets requirements.

    Args:
        path: Path to validate
        must_exist: Whether file must exist
        must_be_file: Whether path must be a file (not directory)
        allowed_suffixes: List of allowed file extensions (e.g., ['.pdf', '.txt'])

    Raises:
        ValueError: If validation fails
    """
    if must_exist and not path.exists():
        raise ValueError(f"File does not exist: {path}")

    if must_be_file and path.exists() and not path.is_file():
        raise ValueError(f"Path is not a file: {path}")

    if allowed_suffixes and path.suffix.lower() not in allowed_suffixes:
        raise ValueError(
            f"File type '{path.suffix}' not allowed. "
            f"Allowed types: {allowed_suffixes}"
        )
```

**Update existing code to use utilities**:
```python
# In src/ingestion/loaders.py
from src.utils.paths import normalize_path, validate_file_path

def load_document(file_path: Union[str, Path]) -> Document:
    # Normalize and validate path
    file_path = normalize_path(file_path)
    validate_file_path(
        file_path,
        must_exist=True,
        must_be_file=True,
        allowed_suffixes=['.pdf', '.txt', '.md', '.html']
    )

    # Continue with loading...
```

#### Testing Requirements
- [ ] Test with symlinks (both resolved and unresolved)
- [ ] Test with relative paths
- [ ] Test with paths containing spaces
- [ ] Test with paths containing special characters
- [ ] Test with non-existent paths
- [ ] Test with directory paths (should fail if expecting file)

#### Files to Create
- `src/utils/paths.py` (~150 lines)
- `tests/utils/test_paths.py` (~200 lines)

#### Files to Modify
- `src/ingestion/loaders.py`
- `src/ingestion/scanner.py`
- `src/ingestion/batch.py`
- `src/main.py`

#### Acceptance Criteria
- ✅ Consistent path handling across codebase
- ✅ Symlinks handled with defined policy
- ✅ Special characters handled correctly
- ✅ Clear error messages for invalid paths

---

### BUG-006: Memory Leaks in Batch Processing

**Status**: 🟡 High Priority
**Priority**: P1
**Estimated Time**: 4-5 hours
**Complexity**: Medium

#### Problem
Batch processing of large document sets may exhaust memory:
- No limit on batch size for embedding generation
- Large documents loaded entirely into memory
- No streaming for very large files
- Embeddings accumulate in memory

#### Solution

**Step 1**: Add batch size limits for embeddings
```python
# src/embeddings/base.py
class BaseEmbedder:
    def __init__(self, max_batch_size: int = 32):
        self.max_batch_size = max_batch_size

    def embed_batch(self, texts: list[str]) -> np.ndarray:
        """Embed batch of texts with automatic chunking."""
        if len(texts) <= self.max_batch_size:
            return self._embed_batch_internal(texts)

        # Process in chunks to avoid memory issues
        all_embeddings = []
        for i in range(0, len(texts), self.max_batch_size):
            batch = texts[i:i + self.max_batch_size]
            embeddings = self._embed_batch_internal(batch)
            all_embeddings.append(embeddings)

            # Clear memory
            if i % 100 == 0:
                gc.collect()

        return np.vstack(all_embeddings)
```

**Step 2**: Add memory monitoring
```python
# src/utils/memory.py (NEW FILE)
"""Memory monitoring utilities."""
import psutil
import logging

logger = logging.get_logger(__name__)

def get_memory_usage_mb() -> float:
    """Get current process memory usage in MB."""
    process = psutil.Process()
    return process.memory_info().rss / 1024 / 1024

def check_memory_threshold(threshold_mb: float = 1000) -> bool:
    """
    Check if memory usage exceeds threshold.

    Args:
        threshold_mb: Memory threshold in MB

    Returns:
        True if over threshold
    """
    usage = get_memory_usage_mb()
    if usage > threshold_mb:
        logger.warning(f"High memory usage: {usage:.1f} MB")
        return True
    return False
```

**Step 3**: Stream large file processing
```python
# src/ingestion/loaders.py
def load_large_document(file_path: Path, chunk_size_mb: int = 10):
    """
    Load very large documents in chunks to avoid memory issues.

    Yields chunks of the document for processing.
    """
    file_size_mb = file_path.stat().st_size / 1024 / 1024

    if file_size_mb > chunk_size_mb:
        logger.info(f"Large file detected ({file_size_mb:.1f} MB), streaming...")
        # Implement streaming for large files
        # Process in chunks, yield each chunk
    else:
        # Load entire file (small enough)
        yield load_document(file_path)
```

#### Testing Requirements
- [ ] Test batch processing with 1000+ documents
- [ ] Test memory usage stays bounded
- [ ] Test very large individual files (>100MB)
- [ ] Monitor memory before/after batch operations

#### Files to Create
- `src/utils/memory.py`
- `tests/utils/test_memory.py`

#### Files to Modify
- `src/embeddings/base.py`
- `src/embeddings/sentence_transformer.py`
- `src/embeddings/ollama_embedder.py`
- `src/ingestion/batch.py`

#### Acceptance Criteria
- ✅ Memory usage stays below 2GB for batch processing
- ✅ Large batches (1000+ docs) complete successfully
- ✅ Memory monitoring logs warnings

---

### BUG-007: ChromaDB Metadata Type Restrictions

**Status**: 🟡 High Priority
**Priority**: P1
**Estimated Time**: 2 hours
**Complexity**: Low

#### Problem
ChromaDB has strict metadata type requirements (no None values, no Path objects), but metadata preparation is duplicated in multiple places with manual filtering. This violates DRY principle and is fragile.

**Evidence**:
```python
# src/main.py:206-209
metadata_to_store = {
    k: str(v) if isinstance(v, Path) else v
    for k, v in metadata.items()
    if v is not None  # ChromaDB doesn't accept None values
}

# src/ingestion/batch.py:193-203 - Same logic duplicated!
```

#### Solution

Create centralized metadata sanitization:
```python
# src/utils/metadata.py (NEW FILE)
"""Metadata handling utilities."""
from pathlib import Path
from typing import Any, Dict
import logging

logger = logging.get_logger(__name__)

def sanitize_metadata(metadata: Dict[str, Any]) -> Dict[str, Any]:
    """
    Sanitize metadata for ChromaDB storage.

    ChromaDB requirements:
    - No None values
    - No Path objects (must be strings)
    - Values must be str, int, float, or bool

    Args:
        metadata: Raw metadata dictionary

    Returns:
        Sanitized metadata safe for ChromaDB
    """
    sanitized = {}

    for key, value in metadata.items():
        # Skip None values
        if value is None:
            continue

        # Convert Path to string
        if isinstance(value, Path):
            value = str(value)

        # Convert to supported types
        if isinstance(value, (str, int, float, bool)):
            sanitized[key] = value
        elif isinstance(value, (list, tuple)):
            # Convert to string representation
            sanitized[key] = str(value)
        else:
            # Log unsupported types
            logger.warning(
                f"Unsupported metadata type for '{key}': {type(value)}. "
                f"Converting to string."
            )
            sanitized[key] = str(value)

    return sanitized
```

**Update all usages**:
```python
# In src/main.py
from src.utils.metadata import sanitize_metadata

metadata_to_store = sanitize_metadata(metadata)

# In src/ingestion/batch.py
from src.utils.metadata import sanitize_metadata

metadata_to_store = sanitize_metadata(chunk.metadata)
```

#### Testing Requirements
- [ ] Test with None values (should be removed)
- [ ] Test with Path objects (should be converted to strings)
- [ ] Test with complex types (should be handled gracefully)
- [ ] Test with valid types (should pass through)

#### Files to Create
- `src/utils/metadata.py`
- `tests/utils/test_metadata.py`

#### Files to Modify
- `src/main.py` (line 206-209)
- `src/ingestion/batch.py` (line 193-203)

#### Acceptance Criteria
- ✅ Single source of truth for metadata sanitization
- ✅ All metadata preparation uses utility function
- ✅ No DRY violations

---

### BUG-008: Incomplete Hybrid Retrieval Integration

**Status**: 🟡 High Priority
**Priority**: P1
**Estimated Time**: 3 hours
**Complexity**: Medium

#### Problem
`HybridRetriever` exists and works, but the main CLI query command only uses vector retrieval. Users can't access the hybrid retrieval functionality.

#### Solution

Add retrieval method flag to CLI:
```python
# src/main.py - query command
@click.option(
    "--retrieval-method",
    type=click.Choice(["vector", "bm25", "hybrid"], case_sensitive=False),
    default="hybrid",
    help="Retrieval method to use (default: hybrid)"
)
def query(query_text: str, top_k: int, retrieval_method: str):
    """Query the document store."""

    # Initialize appropriate retriever
    if retrieval_method == "vector":
        retriever = VectorRetriever(vector_store, embedder)
    elif retrieval_method == "bm25":
        retriever = BM25Retriever(vector_store)
    else:  # hybrid
        vector_retriever = VectorRetriever(vector_store, embedder)
        bm25_retriever = BM25Retriever(vector_store)
        retriever = HybridRetriever(
            vector_retriever=vector_retriever,
            bm25_retriever=bm25_retriever,
            alpha=0.5  # Configurable weight
        )

    # Retrieve and display results
    results = retriever.retrieve(query_text, k=top_k)
    # ... rest of query logic
```

Add to config:
```python
# src/config/settings.py
class Settings:
    # Add retrieval settings
    retrieval_method: str = "hybrid"
    hybrid_alpha: float = 0.5  # Weight for hybrid retrieval (0.0 = pure BM25, 1.0 = pure vector)
```

#### Testing Requirements
- [ ] Test vector-only retrieval
- [ ] Test BM25-only retrieval
- [ ] Test hybrid retrieval
- [ ] Compare results across methods

#### Files to Modify
- `src/main.py` (query command)
- `src/config/settings.py`
- `src/web/api.py` (also use hybrid)

#### Acceptance Criteria
- ✅ CLI supports `--retrieval-method` flag
- ✅ Default is hybrid retrieval
- ✅ All three methods work correctly

---

### BUG-009: Few-Shot Examples Unused

**Status**: 🟡 High Priority
**Priority**: P1
**Estimated Time**: 4 hours
**Complexity**: Medium

#### Problem
`src/generation/few_shot.py` provides few-shot prompting infrastructure but it's never integrated into the main query flow. Users can't benefit from few-shot examples.

#### Solution

**Step 1**: Add CLI commands for example management
```python
# src/main.py - new command group
@main.group()
def examples():
    """Manage few-shot examples for better responses."""
    pass

@examples.command()
@click.option("--query", prompt=True, help="Example query")
@click.option("--answer", prompt=True, help="Example answer")
@click.option("--context", help="Example context (optional)")
def add(query: str, answer: str, context: str = None):
    """Add a few-shot example."""
    from src.generation.few_shot import FewShotManager

    manager = FewShotManager()
    manager.add_example(query, answer, context)

    console.print("[green]✓[/green] Example added")

@examples.command()
def list():
    """List all few-shot examples."""
    from src.generation.few_shot import FewShotManager

    manager = FewShotManager()
    examples = manager.get_examples()

    table = Table(title="Few-Shot Examples")
    table.add_column("Query", style="cyan")
    table.add_column("Answer", style="green")

    for ex in examples:
        table.add_row(ex.query, ex.answer[:100] + "...")

    console.print(table)

@examples.command()
@click.argument("index", type=int)
def remove(index: int):
    """Remove a few-shot example by index."""
    from src.generation.few_shot import FewShotManager

    manager = FewShotManager()
    manager.remove_example(index)

    console.print("[green]✓[/green] Example removed")
```

**Step 2**: Integrate into query flow
```python
# src/main.py - query command
@click.option(
    "--use-examples",
    is_flag=True,
    help="Use few-shot examples to improve answer quality"
)
def query(query_text: str, top_k: int, use_examples: bool):
    """Query the document store."""

    # ... retrieval logic ...

    # Generate answer
    if use_examples:
        from src.generation.few_shot import FewShotManager
        manager = FewShotManager()

        # Build prompt with examples
        prompt = manager.build_prompt_with_examples(
            query=query_text,
            context=context,
            max_examples=3
        )
        answer = ollama_client.generate(prompt)
    else:
        # Standard generation
        answer = ollama_client.generate(query=query_text, context=context)
```

#### Testing Requirements
- [ ] Test adding examples
- [ ] Test listing examples
- [ ] Test removing examples
- [ ] Test query with and without examples
- [ ] Verify examples improve answer quality

#### Files to Modify
- `src/main.py` (add examples command group)
- `src/generation/ollama_client.py` (support few-shot prompts)

#### Acceptance Criteria
- ✅ CLI commands for example management
- ✅ Query can use few-shot examples
- ✅ Examples improve answer quality (subjective but testable)

---

### BUG-010: Duplicate Detection Incomplete

**Status**: 🟡 High Priority
**Priority**: P1
**Estimated Time**: 2 hours
**Complexity**: Low

#### Problem
Duplicate detection works for single files but batch ingestion may miss duplicates within the current batch (only checks against database, not in-progress batch).

**Example**:
```bash
# If folder contains doc.pdf twice, both may be ingested
ragged add folder/
```

#### Solution

Track seen files during batch:
```python
# src/ingestion/batch.py
class BatchIngester:
    def ingest_batch(self, files: List[Path]) -> List[IngestionResult]:
        results = []
        seen_hashes = set()  # Track within this batch

        for file in files:
            # Compute file hash
            file_hash = compute_file_hash(file)

            # Check if already seen in this batch
            if file_hash in seen_hashes:
                logger.info(f"Skipping duplicate within batch: {file}")
                results.append(IngestionResult(
                    file=file,
                    status="duplicate_in_batch",
                    chunks=0
                ))
                continue

            # Check if exists in database
            if self._exists_in_database(file_hash):
                logger.info(f"Skipping duplicate in database: {file}")
                results.append(IngestionResult(
                    file=file,
                    status="duplicate_in_database",
                    chunks=0
                ))
                continue

            # Process file
            result = self._process_file(file)
            results.append(result)

            # Mark as seen
            if result.status == "success":
                seen_hashes.add(file_hash)

        return results
```

#### Testing Requirements
- [ ] Test folder with duplicate files (same content, different names)
- [ ] Test folder with same file twice
- [ ] Test batch with mix of new and duplicate files

#### Files to Modify
- `src/ingestion/batch.py`

#### Acceptance Criteria
- ✅ Duplicates within batch are detected
- ✅ Clear status message differentiates batch vs database duplicates

---

### BUG-011: Page Tracking Edge Cases

**Status**: 🟡 High Priority
**Priority**: P1
**Estimated Time**: 3 hours
**Complexity**: Medium

#### Problem
Page tracking in `src/chunking/splitters.py:_map_chunks_to_pages()` uses complex position mapping that may fail for edge cases like malformed PDFs, documents with missing page numbers, or empty pages.

#### Solution

Add robust fallback handling:
```python
# src/chunking/splitters.py
def _map_chunks_to_pages(
    self,
    chunks: List[str],
    pages: List[Dict]
) -> List[int]:
    """
    Map chunks to page numbers with robust error handling.

    Returns:
        List of page numbers, one per chunk. Returns None for chunks
        that can't be reliably mapped.
    """
    chunk_pages = []

    for chunk in chunks:
        try:
            page_num = self._find_page_for_chunk(chunk, pages)
            chunk_pages.append(page_num)
        except Exception as e:
            logger.warning(
                f"Failed to map chunk to page: {e}. "
                f"Chunk preview: {chunk[:50]}..."
            )
            chunk_pages.append(None)  # Mark as unknown

    return chunk_pages

def _find_page_for_chunk(self, chunk: str, pages: List[Dict]) -> Optional[int]:
    """Find page number for a chunk with fallbacks."""
    # Try position-based mapping first (current implementation)
    try:
        page_num = self._position_based_mapping(chunk, pages)
        if page_num is not None:
            return page_num
    except Exception:
        pass

    # Fallback: Content-based matching
    try:
        page_num = self._content_based_mapping(chunk, pages)
        if page_num is not None:
            return page_num
    except Exception:
        pass

    # Final fallback: Return None
    logger.debug(f"Could not reliably map chunk to page")
    return None
```

Handle None page numbers gracefully:
```python
# When displaying citations
if page_num is not None:
    citation = f"{source}, p. {page_num}"
else:
    citation = f"{source} (page number unavailable)"
```

#### Testing Requirements
- [ ] Test with malformed PDFs
- [ ] Test with empty pages
- [ ] Test with documents without page metadata
- [ ] Test with very large pages
- [ ] Test with very small chunks

#### Files to Modify
- `src/chunking/splitters.py`
- `src/generation/citation_formatter.py` (handle None pages)

#### Acceptance Criteria
- ✅ Page mapping doesn't crash on edge cases
- ✅ Fallback to None when mapping uncertain
- ✅ Citations handle None page numbers gracefully

---

## P2 - Medium Priority (14-18 hours)

Code quality improvements that enhance maintainability.

### QUALITY-001: Type Hint Coverage

**Priority**: P2
**Estimated Time**: 4 hours
**Complexity**: Low-Medium

#### Problem
Approximately 15% of functions lack proper type hints, reducing code clarity and preventing static type checking.

#### Solution

Add type hints throughout:
```python
# Run mypy to find missing type hints
mypy src/ --strict

# Add type hints systematically
from typing import List, Dict, Optional, Union

def process_document(
    file_path: Path,
    chunk_size: int = 500,
    options: Optional[Dict[str, Any]] = None
) -> List[Chunk]:
    """Process document with full type hints."""
    ...
```

#### Files to Modify
- Review all files in `src/`
- Focus on recently added modules

#### Acceptance Criteria
- ✅ mypy passes with --strict mode
- ✅ All public functions have type hints

---

### QUALITY-002: Docstring Completeness

**Priority**: P2
**Estimated Time**: 3 hours
**Complexity**: Low

#### Problem
Some functions lack docstrings or have minimal documentation.

#### Solution

Follow Google-style docstrings:
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
    ...
```

#### Files to Modify
- All files in `src/`
- Focus on public APIs

#### Acceptance Criteria
- ✅ All public functions have docstrings
- ✅ Docstrings follow Google style
- ✅ Include examples for complex functions

---

### QUALITY-003: TODO Comments Cleanup

**Priority**: P2
**Estimated Time**: 2-8 hours (varies)
**Complexity**: Varies

#### Problem
11 TODO comments found in code. These should either be implemented or converted to issues.

#### Solution

Audit all TODOs:
```bash
grep -rn "TODO" src/ --include="*.py"
```

For each TODO:
1. If quick (<30 min) - implement now
2. If complex - create GitHub issue and reference it
3. If obsolete - remove

Example:
```python
# BEFORE
# TODO: Add caching

# AFTER (if implementing)
@lru_cache(maxsize=1000)
def cached_function(...):
    ...

# AFTER (if deferring)
# See issue #42 for caching implementation
```

#### Files to Review
- All files containing TODO comments

#### Acceptance Criteria
- ✅ No TODO comments without issue references
- ✅ Quick TODOs implemented
- ✅ Complex TODOs tracked as issues

---

### QUALITY-004: Code Duplication

**Priority**: P2
**Estimated Time**: 1-2 hours
**Complexity**: Low

#### Problem
Metadata preparation logic is duplicated between `main.py` and `batch.py` (already addressed in BUG-007, but check for other duplications).

#### Solution

Use `ruff` to find duplications:
```bash
# Find duplicate code blocks
ruff check src/ --select=D

# Extract to shared utilities
```

Common patterns to extract:
- Repeated validation logic
- Common data transformations
- Shared formatting code

#### Files to Review
- All files in `src/`

#### Acceptance Criteria
- ✅ No significant code duplication
- ✅ Shared logic in utilities modules

---

### QUALITY-005: Magic Numbers

**Priority**: P2
**Estimated Time**: 2 hours
**Complexity**: Low

#### Problem
Hardcoded values (magic numbers) scattered throughout code without explanation.

**Examples**:
```python
chunk_size = chunk_size or len(text) * 4  # Why *4?
max_tokens = 500  # Why 500?
```

#### Solution

Extract to named constants with documentation:
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
CHARS_PER_TOKEN_ESTIMATE = 4  # Average characters per token for estimation

# Batch processing
DEFAULT_BATCH_SIZE = 32  # Documents per batch
MAX_MEMORY_MB = 2000  # Maximum memory usage in MB
```

Use constants:
```python
from src.config.constants import CHARS_PER_TOKEN_ESTIMATE

estimated_tokens = len(text) // CHARS_PER_TOKEN_ESTIMATE
```

#### Files to Create
- `src/config/constants.py`

#### Files to Modify
- Any file with magic numbers

#### Acceptance Criteria
- ✅ All magic numbers replaced with named constants
- ✅ Constants documented with rationale

---

## Summary & Checklist

### Completion Checklist

**P0 - Critical** (Must complete):
- [ ] BUG-001: Make API endpoints functional
- [ ] BUG-002: Fix logger import in settings.py
- [ ] BUG-003: Add tests for scanner, batch, model_manager

**P1 - High Priority** (Should complete):
- [ ] BUG-004: Improve error handling consistency
- [ ] BUG-005: Handle path edge cases
- [ ] BUG-006: Fix memory leaks in batch processing
- [ ] BUG-007: Centralize metadata sanitization
- [ ] BUG-008: Integrate hybrid retrieval in CLI
- [ ] BUG-009: Integrate few-shot examples
- [ ] BUG-010: Fix duplicate detection in batches
- [ ] BUG-011: Improve page tracking robustness

**P2 - Medium Priority** (Nice to have):
- [ ] QUALITY-001: Add type hints
- [ ] QUALITY-002: Complete docstrings
- [ ] QUALITY-003: Clean up TODOs
- [ ] QUALITY-004: Remove code duplication
- [ ] QUALITY-005: Replace magic numbers

### Time Estimate by Priority

| Priority | Issues | Hours |
|----------|--------|-------|
| P0 | 3 | 12-15 |
| P1 | 8 | 20-25 |
| P2 | 5 | 12-15 |
| **Total** | **16** | **44-55** |

### Testing Strategy

1. **Unit Tests First**: Write tests before fixing bugs (TDD)
2. **Integration Tests**: Add end-to-end tests for API endpoints
3. **Coverage Goal**: Increase from 68% to 75%
4. **Regression Tests**: Ensure fixes don't break existing functionality

### Validation

Before releasing v0.2.5:
- [ ] All tests pass (no failures)
- [ ] Coverage ≥ 75%
- [ ] No critical/high priority bugs remain
- [ ] API endpoints fully functional
- [ ] Documentation updated
- [ ] Changelog updated

### Success Criteria

v0.2.5 is successful if:
1. ✅ Web UI is fully functional
2. ✅ All new modules have test coverage
3. ✅ No critical bugs remain
4. ✅ Code quality improved
5. ✅ Foundation solid for v0.2.7 development

---

**Next Steps**: After completing v0.2.5, proceed to [v0.2.7 Roadmap](v0.2.7-roadmap.md) for UX and performance improvements.
