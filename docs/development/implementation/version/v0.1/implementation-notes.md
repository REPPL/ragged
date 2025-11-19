# v0.1 Implementation Notes

**Purpose**: Technical implementation details, patterns, and solutions

This document captures the technical details of how v0.1 was implemented, including patterns used, challenges solved, and technical decisions at the code level.

## Table of Contents
1. [Core Patterns](#core-patterns)
2. [Module Implementations](#module-implementations)
3. [Integration Points](#integration-points)
4. [Technical Challenges & Solutions](#technical-challenges--solutions)
5. [Performance Optimizations](#performance-optimisations)
6. [Security Implementations](#security-implementations)

---

## Core Patterns

### Factory Pattern (Embeddings)
**Location**: `src/embeddings/factory.py`

Used for creating embedder instances based on configuration:

```python
def create_embedder(model_type: EmbeddingModel = None, model_name: str = None) -> BaseEmbedder:
    settings = get_settings()
    model_type = model_type or settings.embedding_model
    model_name = model_name or settings.embedding_model_name

    if model_type == EmbeddingModel.SENTENCE_TRANSFORMERS:
        return SentenceTransformerEmbedder(model_name=model_name)
    elif model_type == EmbeddingModel.OLLAMA:
        return OllamaEmbedder(model_name=model_name)
```

**Benefits**: Runtime model selection, easy testing, extensible

### Abstract Base Classes
**Location**: `src/embeddings/base.py`

All embedders implement `BaseEmbedder`:

```python
class BaseEmbedder(ABC):
    @abstractmethod
    def embed_text(self, text: str) -> np.ndarray:
        pass

    @abstractmethod
    def embed_batch(self, texts: List[str]) -> np.ndarray:
        pass

    @property
    @abstractmethod
    def dimensions(self) -> int:
        pass
```

**Benefits**: Type safety, contract enforcement, swap-ability

### Pydantic Models
**Location**: `src/config/settings.py`, `src/ingestion/models.py`

Used for all data structures requiring validation:

```python
class DocumentMetadata(BaseModel):
    source_path: str
    file_size: int
    created_at: datetime = Field(default_factory=datetime.now)
    format: str
    sha256_hash: str
```

**Benefits**: Runtime validation, type safety, automatic parsing

### Recursive Strategy
**Location**: `src/chunking/splitters.py`

Recursive text splitting with fallback separators:

```python
def _split_recursive(self, text: str, separators: List[str]) -> List[str]:
    if not separators:
        return self._split_by_characters(text)

    separator = separators[0]
    splits = text.split(separator)

    # Try to fit in chunks, recurse if too large
    for split in splits:
        if count_tokens(split) > self.chunk_size:
            # Recurse with next separator
            sub_chunks = self._split_recursive(split, separators[1:])
```

**Benefits**: Preserves semantic boundaries while respecting size limits

---

## Module Implementations

### Configuration System
**File**: `src/config/settings.py` (148 lines)

Key features:
- Pydantic `BaseSettings` for automatic env var parsing
- Field validators for cross-field validation
- Sensible defaults with type safety
- Singleton pattern via `@lru_cache`

**Example**:
```python
@field_validator("embedding_model_name", mode="before")
@classmethod
def set_embedding_model_name(cls, v: str, info) -> str:
    if v:
        return v
    # Auto-select based on embedding_model
    embedding_model = info.data.get("embedding_model")
    if embedding_model == EmbeddingModel.SENTENCE_TRANSFORMERS:
        return "all-MiniLM-L6-v2"
    elif embedding_model == EmbeddingModel.OLLAMA:
        return "nomic-embed-text"
```

### Privacy-Safe Logging
**File**: `src/utils/logging.py` (166 lines)

Key features:
- Automatic PII filtering via `PrivacyFilter`
- Structured logging with consistent format
- JSON output option for log aggregation
- Sensitive key detection

**Filter Implementation**:
```python
class PrivacyFilter(logging.Filter):
    SENSITIVE_KEYS = {"password", "token", "api_key", "secret",
                      "auth", "credential", "content", "text"}

    def filter(self, record: logging.LogRecord) -> bool:
        msg_lower = str(record.msg).lower()
        for key in self.SENSITIVE_KEYS:
            if key in msg_lower:
                record.msg = f"[REDACTED: potentially sensitive - {key}]"
        return True
```

### Document Models
**File**: `src/ingestion/models.py` (167 lines)

Key features:
- Pydantic models for Document, Chunk, ChunkMetadata
- `from_file()` factory method with hash generation
- Automatic ID generation using `uuid4()`
- Rich metadata with file stats

**Example**:
```python
@classmethod
def from_file(cls, file_path: Path, content: str, format: str, ...) -> "Document":
    file_stats = file_path.stat()
    content_hash = hashlib.sha256(content.encode()).hexdigest()

    metadata = DocumentMetadata(
        source_path=str(file_path),
        file_size=file_stats.st_size,
        format=format,
        sha256_hash=content_hash,
        ...
    )

    return cls(content=content, metadata=metadata)
```

### Document Loaders
**File**: `src/ingestion/loaders.py` (283 lines)

Key features:
- Format auto-detection via MIME types
- Security validation before all operations
- Encoding detection for TXT files
- Structure preservation via markdown

**PDF Loader**:
```python
def load_pdf(file_path: Path) -> Document:
    md_text = pymupdf4llm.to_markdown(str(file_path))

    doc = fitz.open(file_path)
    metadata = doc.metadata or {}

    return Document.from_file(
        file_path, md_text, "pdf",
        title=metadata.get("title"),
        author=metadata.get("author"),
        page_count=len(doc)
    )
```

### Token Counter
**File**: `src/chunking/token_counter.py` (76 lines)

Key features:
- LRU cache on tokenizer for performance
- Accurate counting via tiktoken
- Estimation function for quick checks
- Token-to-char conversion utilities

**Caching**:
```python
@lru_cache(maxsize=1)
def get_tokenizer(model: str = "cl100k_base"):
    return tiktoken.get_encoding(model)
```

### Embedders
**Files**: `src/embeddings/sentence_transformer.py`, `src/embeddings/ollama_embedder.py`

**SentenceTransformers**:
- Device auto-detection (CUDA → MPS → CPU)
- Batch processing with progress bars
- `convert_to_numpy=True` for consistency

**Ollama**:
- Retry logic with exponential backoff
- Model availability verification
- Dimension auto-detection via test embedding

**Retry Implementation**:
```python
for attempt in range(self._max_retries):
    try:
        response = self.client.embeddings(model=self._model_name, prompt=text)
        return np.array(response['embedding'], dtype=np.float32)
    except Exception as e:
        if attempt == self._max_retries - 1:
            raise
        wait_time = 2 ** attempt
        time.sleep(wait_time)
```

### Vector Store
**File**: `src/storage/vector_store.py` (194 lines)

Key features:
- ChromaDB HttpClient integration
- URL parsing for host/port extraction
- Full CRUD operations
- Health checking via heartbeat

**Query Implementation**:
```python
def query(self, query_embedding: np.ndarray, k: int = 5, ...) -> Dict[str, Any]:
    query_list = query_embedding.tolist() if isinstance(query_embedding, np.ndarray) else [query_embedding.tolist()]

    results = self.collection.query(
        query_embeddings=query_list,
        n_results=k,
        where=where,
    )
    return results
```

### CLI
**File**: `src/main.py` (323 lines)

Key features:
- Click command groups
- Rich progress bars
- Error handling with user-friendly messages
- Conditional import of optional dependencies

**Progress Bar Example**:
```python
with Progress() as progress:
    task = progress.add_task("Processing...", total=100)

    # Load
    progress.update(task, description="Loading...", advance=20)
    document = load_document(file_path)

    # Chunk
    progress.update(task, description="Chunking...", advance=20)
    chunks = chunk_document(document)
```

---

## Integration Points

### Configuration → All Modules
- All modules use `get_settings()` for configuration
- Type-safe access via Pydantic
- Environment variables override defaults

### Loaders → Models
- All loaders return `Document` instances
- Consistent interface regardless of format
- Metadata populated automatically

### Chunks → Embeddings
- Chunks converted to text for embedding
- Batch processing for efficiency
- Metadata preserved through pipeline

### Embeddings → Vector Store
- Embeddings as numpy arrays
- Conversion to lists for ChromaDB
- Metadata stored alongside vectors

### Vector Store → Retrieval
- Retriever wraps vector store + embedder
- Query embedding → similarity search
- Results parsed into `RetrievedChunk` objects

### Retrieval → Generation
- Chunks formatted into RAG prompt
- System prompt sets citation format
- Response parsed for citations

### All → CLI
- CLI orchestrates entire pipeline
- Progress feedback at each stage
- Error handling at boundaries

---

## Technical Challenges & Solutions

### Challenge: Python 3.14 ChromaDB Compatibility
**Problem**: chromadb dependencies (onnxruntime, pulsar-client) lack Python 3.14 wheels

**Solution**:
1. Create virtual environment with minimal dependencies first
2. Install core packages separately (pydantic, pytest)
3. Accept warning about dependency conflicts
4. Works for development, may need Python 3.11 for production

**Status:** Deferred to Phase 10, may downgrade Python version

### Challenge: Test Environment Pollution
**Problem**: Environment variables from one test affecting others

**Solution**: Created `clean_env` fixture with `autouse=True`

```python
@pytest.fixture(autouse=True)
def clean_env():
    # Clear before
    for key in list(os.environ.keys()):
        if key.startswith("RAGGED_"):
            del os.environ[key]
    get_settings.cache_clear()

    yield

    # Clear after
    for key in list(os.environ.keys()):
        if key.startswith("RAGGED_"):
            del os.environ[key]
    get_settings.cache_clear()
```

### Challenge: ChromaDB Nested Result Format
**Problem**: ChromaDB returns `results["ids"][0]` not `results["ids"]`

**Solution**: Check if first element is a list and unpack:

```python
ids = results["ids"][0] if isinstance(results["ids"][0], list) else results["ids"]
```

### Challenge: Encoding Detection for Text Files
**Problem**: Not all text files are UTF-8

**Solution**: Try UTF-8 first, fall back to chardet:

```python
try:
    content = file_path.read_text(encoding="utf-8")
except UnicodeDecodeError:
    raw = file_path.read_bytes()
    encoding = chardet.detect(raw).get("encoding", "utf-8")
    content = raw.decode(encoding)
```

### Challenge: Token Counts vs Character Counts
**Problem**: Can't use character-based chunking with token limits

**Solution**: Always use tiktoken for accurate token counting, never estimate from characters

### Challenge: Device Detection for PyTorch
**Problem**: Need to auto-select best device (CUDA/MPS/CPU)

**Solution**: Check in order of preference:

```python
if torch.cuda.is_available():
    device = "cuda"
elif hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
    device = "mps"
else:
    device = "cpu"
```

---

## Performance Optimizations

### LRU Cache on Tokenizer
**Impact**: ~10x faster repeated token counting

```python
@lru_cache(maxsize=1)
def get_tokenizer(model: str = "cl100k_base"):
    return tiktoken.get_encoding(model)
```

### Batch Embedding
**Impact**: ~5x faster than individual embeddings

```python
def embed_batch(self, texts: List[str]) -> np.ndarray:
    return self.model.encode(
        texts,
        batch_size=self._batch_size,
        convert_to_numpy=True,
        show_progress_bar=len(texts) > 100
    )
```

### Singleton Settings
**Impact**: Avoids re-parsing env vars

```python
@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
```

### ChromaDB HTTP Client
**Trade-off**: HTTP overhead, but enables remote ChromaDB if needed

Could use in-process client for better performance:
```python
# Future optimisation
client = chromadb.Client()  # In-process, faster
```

---

## Security Implementations

### Path Traversal Prevention
**File**: `src/utils/security.py`

```python
def validate_file_path(file_path: Path, allowed_base: Path = None) -> Path:
    file_path = file_path.resolve()

    if allowed_base:
        try:
            file_path.relative_to(allowed_base.resolve())
        except ValueError:
            raise SecurityError(f"Path outside allowed directory")

    if ".." in file_path.parts:
        raise SecurityError("Path traversal detected")

    return file_path
```

### File Size Limits
```python
def validate_file_size(file_path: Path, max_size: int = 100 * 1024 * 1024):
    size = file_path.stat().st_size
    if size > max_size:
        raise ValueError(f"File too large: {size} bytes")
```

### MIME Type Validation
```python
def validate_mime_type(file_path: Path, allowed: List[str]):
    mime_type, _ = mimetypes.guess_type(str(file_path))
    if mime_type not in allowed:
        raise ValueError(f"Invalid file type: {mime_type}")
```

### PII Filtering in Logs
Automatic redaction of sensitive keywords in all log messages (see Logging section)

### No Credential Storage
- No hardcoded API keys
- No credential files
- All authentication via environment variables
- Sensitive data never logged

---

## Code Quality

### Type Hints Throughout
Every function has complete type hints:

```python
def chunk_document(
    document: Document,
    chunk_size: int = None,
    chunk_overlap: int = None
) -> List[Chunk]:
```

### Comprehensive Docstrings
All public functions documented:

```python
def load_document(file_path: Path, format: Optional[str] = None) -> Document:
    """
    Load a document from file with automatic format detection.

    Args:
        file_path: Path to the document file
        format: Optional format override (pdf, txt, md, html)

    Returns:
        Document instance with metadata

    Raises:
        ValueError: If file doesn't exist or format unsupported
        SecurityError: If path validation fails
    """
```

### Error Handling
Specific exceptions with clear messages:

```python
try:
    document = load_document(file_path)
except SecurityError as e:
    console.print(f"[red]Security error:[/red] {e}")
    sys.exit(1)
except ValueError as e:
    console.print(f"[yellow]Invalid file:[/yellow] {e}")
    sys.exit(1)
```

---

## Testing Approach

### Fixtures
Centralized in `tests/conftest.py`:

```python
@pytest.fixture
def sample_document():
    return Document(
        content="Test content",
        metadata=DocumentMetadata(...)
    )
```

### Test Organisation
Mirror source structure:
```
tests/
├── config/test_settings.py
├── utils/test_logging.py
├── ingestion/test_models.py
└── conftest.py
```

### Coverage Targets
- Overall: 60-70% (v0.1)
- Core modules: 90%+
- Utilities: 100% (logging)

---

## Lessons Learned

### What Worked Well
1. **Pydantic**: Caught many configuration errors early
2. **Factory Pattern**: Made swapping embedders trivial
3. **Markdown**: Excellent intermediate format for LLMs
4. **tiktoken**: Accurate token counting is critical
5. **Click + Rich**: Dramatically improves UX

### What Could Improve
1. **Test Coverage**: Should write tests alongside implementation
2. **Documentation**: Should document as you go, not at end
3. **Error Messages**: Could be more specific and actionable
4. **Performance Testing**: Should benchmark early to avoid surprises

### For v0.2
1. **Dependency Injection**: Consider for better testability
2. **Async/Await**: For concurrent operations
3. **Caching Layer**: For repeated queries
4. **Metrics Collection**: For performance monitoring
5. **Configuration Validation**: More comprehensive at startup

---

**Total Lines of Code**: ~3,000+
**Test Coverage**: 96% (Phase 1 modules)
**Next**: Expand test coverage to all modules
