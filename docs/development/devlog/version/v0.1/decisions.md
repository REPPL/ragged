# v0.1 Architecture Decision Records

**Purpose**: Document key architectural and technical decisions made during v0.1 development

This file captures the important decisions, the context that led to them, alternatives considered, and their consequences. These records help future developers understand why the system is built the way it is.

## Decision Index

1. [14-Phase Implementation Approach](#decision-1-14-phase-implementation-approach)
2. [Pydantic v2 for Configuration and Models](#decision-2-pydantic-v2-for-configuration-and-models)
3. [ChromaDB for Vector Storage](#decision-3-chromadb-for-vector-storage)
4. [Dual Embedding Model Support](#decision-4-dual-embedding-model-support)
5. [PyMuPDF4LLM for PDF Processing](#decision-5-pymupdf4llm-for-pdf-processing)
6. [tiktoken for Token Counting](#decision-6-tiktoken-for-token-counting)
7. [Recursive Character Text Splitter](#decision-7-recursive-character-text-splitter)
8. [Click + Rich for CLI](#decision-8-click--rich-for-cli)
9. [Privacy-Safe Logging](#decision-9-privacy-safe-logging)
10. [Factory Pattern for Embedders](#decision-10-factory-pattern-for-embedders)
11. [Ollama for LLM Generation](#decision-11-ollama-for-llm-generation)
12. [Citation Format [Source: filename]](#decision-12-citation-format-source-filename)
13. [Local-Only Processing (No External APIs)](#decision-13-local-only-processing-no-external-apis)
14. [Markdown as Intermediate Format](#decision-14-markdown-as-intermediate-format)

---

## Decision 1: 14-Phase Implementation Approach

**Status**: Accepted
**Date**: 2025-11-09
**Area**: Development Process

### Context
Need

ed a structured approach to implement a complete RAG system from scratch with clear milestones and deliverables.

### Decision
Implement v0.1 in 14 distinct phases:
- **Foundation** (Phase 1): Core infrastructure
- **Core Features** (Phases 2-8): Document ingestion through CLI
- **Quality & Release** (Phases 9-14): Integration, testing, security, documentation, release

### Rationale
- **Incremental Progress**: Each phase delivers working functionality
- **Clear Dependencies**: Each phase builds on previous ones
- **Testability**: Discrete phases enable focused testing
- **Tracking**: Easy to measure progress and estimate remaining work
- **Risk Management**: Issues contained within phases
- **Parallelization**: Some phases (e.g., 10, 11) can proceed in parallel

### Alternatives Considered
1. **Monolithic Development**: Build everything, then test
   - Rejected: Too risky, hard to track progress
2. **Feature-Based Increments**: One complete feature at a time
   - Rejected: Doesn't match natural system architecture
3. **TDD Strict**: Test-first for everything
   - Partially adopted: Hybrid TDD approach chosen

### Consequences
**Positive**:
- Clear roadmap and progress tracking
- Easier to onboard collaborators (know which phase we're in)
- Manageable scope per phase
- Natural git commit points

**Negative**:
- Some artificial boundaries (e.g., Phase 5 vs 6)
- Overhead in phase documentation
- Temptation to skip phases or combine them

**Lessons for v0.2**: Consider fewer, larger phases (8-10 instead of 14) to reduce overhead while maintaining structure.

---

## Decision 2: Pydantic v2 for Configuration and Models

**Status**: Accepted
**Date**: 2025-11-09
**Area**: Data Validation, Configuration

### Context
Needed type-safe configuration management and data validation for documents, chunks, and metadata.

### Decision
Use Pydantic v2 for:
- Settings management (`src/config/settings.py`)
- Document models (`src/ingestion/models.py`)
- All data structures requiring validation

### Rationale
- **Type Safety**: Runtime validation prevents configuration errors
- **IDE Support**: Excellent autocomplete and type checking
- **Validation**: Automatic validation of environment variables
- **Documentation**: Self-documenting through type hints
- **Performance**: Pydantic v2 is fast (Rust core)
- **Ecosystem**: Wide adoption, good documentation

### Alternatives Considered
1. **dataclasses + manual validation**
   - Rejected: More boilerplate, less validation
2. **attrs**
   - Rejected: Less ecosystem support than Pydantic
3. **TypedDict**
   - Rejected: No runtime validation

### Consequences
**Positive**:
- Configuration errors caught early (startup)
- Excellent developer experience
- Automatic environment variable parsing
- Clear error messages for users
- Type safety throughout codebase

**Negative**:
- Dependency on external library
- Migration needed for Pydantic v1 → v2 patterns
- Some learning curve for contributors

**Migration Notes**: Changed `class Config` to `model_config = ConfigDict()` for v2 compatibility.

---

## Decision 3: ChromaDB for Vector Storage

**Status**: Accepted
**Date**: 2025-11-09
**Area**: Vector Database

### Context
Needed a vector database for storing and searching document embeddings with semantic similarity.

### Decision
Use ChromaDB as the vector store with HTTP client mode.

### Rationale
- **Simplicity**: Easy to set up and use
- **Local-First**: Supports fully local deployment
- **Python-Native**: Excellent Python integration
- **Features**: Metadata filtering, collections, CRUD operations
- **Performance**: Fast enough for v0.1 use cases (<10k chunks)
- **Documentation**: Clear, comprehensive documentation
- **Active Development**: Regular updates and improvements

### Alternatives Considered
1. **Qdrant**
   - **Pros**: More features, better performance at scale
   - **Cons**: More complex setup, heavier resource usage
   - **Decision**: Defer to v0.2+ when scale matters
2. **FAISS**
   - **Pros**: Facebook-backed, very fast
   - **Cons**: No metadata filtering, no persistence out-of-box
   - **Decision**: Too low-level for v0.1
3. **Milvus**
   - **Pros**: Production-grade, highly scalable
   - **Cons**: Overkill for v0.1, complex deployment
   - **Decision**: Defer to v1.0+
4. **Weaviate**
   - **Pros**: GraphQL API, built-in vectorization
   - **Cons**: More complex, heavier footprint
   - **Decision**: Too complex for v0.1

### Consequences
**Positive**:
- Simple HTTP client integration
- Low resource requirements
- Metadata filtering works well
- Collection management is straightforward
- Fast enough for local use

**Negative**:
- May need to migrate to Qdrant for v0.3+ (scale)
- Limited query optimization options
- HTTP overhead (vs in-process)

**Future Considerations**: Re-evaluate for v0.3 when performance becomes critical (10k+ chunks).

---

## Decision 4: Dual Embedding Model Support

**Status**: Accepted
**Date**: 2025-11-09
**Area**: Embeddings

### Context
Users may prefer different embedding models based on hardware, accuracy needs, and local vs API preferences.

### Decision
Support two embedding backends via factory pattern:
1. **sentence-transformers** (all-MiniLM-L6-v2, 384 dims)
2. **Ollama** (nomic-embed-text, 768 dims)

### Rationale
- **Flexibility**: Users choose based on needs
- **Offline Support**: sentence-transformers works fully offline
- **Accuracy**: nomic-embed-text provides higher dimensions
- **Hardware**: sentence-transformers supports GPU acceleration
- **Consistency**: Ollama users can keep same backend for embeddings + LLM
- **Future-Proof**: Easy to add more backends later

### Alternatives Considered
1. **sentence-transformers only**
   - **Pros**: Simpler, fewer dependencies
   - **Cons**: No choice for users, locks into one model
2. **Ollama only**
   - **Pros**: Single backend for embeddings + LLM
   - **Cons**: Requires Ollama service, no offline fallback
3. **OpenAI embeddings**
   - **Rejected**: Violates privacy-first principle (external API)

### Implementation
Factory pattern (`src/embeddings/factory.py`) with:
- `create_embedder()` - Creates embedder based on config
- `get_embedder()` - Singleton access
- Abstract `BaseEmbedder` for consistency

### Consequences
**Positive**:
- User choice and flexibility
- Can switch models without code changes
- Future backends easy to add
- Testing can use faster model

**Negative**:
- More code to maintain
- Dimension mismatch possible if user switches models
- Need to document trade-offs for users

**User Guidance**: Document in user guide:
- **sentence-transformers**: Faster, smaller, fully offline, good for most uses
- **Ollama**: Larger dimensions, requires Ollama, consistency with LLM

---

## Decision 5: PyMuPDF4LLM for PDF Processing

**Status**: Accepted
**Date**: 2025-11-09
**Area**: Document Ingestion

### Context
PDFs are a primary document format, need reliable extraction that preserves structure.

### Decision
Use PyMuPDF4LLM for PDF processing, which converts PDFs to markdown.

### Rationale
- **Structure Preservation**: Maintains headings, lists, tables
- **LLM-Optimized**: Output format designed for LLM processing
- **Quality**: Better than raw text extraction
- **Simple API**: Single function call
- **Active Development**: pymupdf ecosystem is well-maintained
- **Markdown Output**: Natural fit for downstream processing

### Alternatives Considered
1. **PyPDF2**
   - **Pros**: Lightweight, pure Python
   - **Cons**: Poor handling of complex PDFs, no structure
2. **pdfplumber**
   - **Pros**: Good table extraction
   - **Cons**: More complex API, overkill for text extraction
3. **Apache Tika**
   - **Pros**: Handles many formats
   - **Cons**: Java dependency, heavy, overkill
4. **PyMuPDF (raw)**
   - **Cons**: PyMuPDF4LLM is a better wrapper for LLM use

### Consequences
**Positive**:
- Excellent PDF extraction quality
- Markdown output is semantic and readable
- Headings and structure preserved
- Works well with chunking system

**Negative**:
- Larger dependency than PyPDF2
- C++ extension (install complexity on some platforms)
- Markdown conversion may not be perfect for all PDFs

**Lessons**: Markdown output is superior to plain text for RAG use cases.

---

## Decision 6: tiktoken for Token Counting

**Status**: Accepted
**Date**: 2025-11-09
**Area**: Chunking

### Context
Need accurate token counting to respect LLM context limits and create appropriately-sized chunks.

### Decision
Use tiktoken with cl100k_base encoding for all token counting operations.

### Rationale
- **Accuracy**: Same tokenizer used by GPT models
- **OpenAI Standard**: Industry standard for token counting
- **Fast**: Rust implementation
- **Reliable**: Battle-tested by OpenAI
- **Caching**: Supports encoding caching for performance

### Alternatives Considered
1. **Character-based estimation**
   - **Pros**: Fast, no dependencies
   - **Cons**: Inaccurate (can be off by 50%+)
2. **transformers tokenizer**
   - **Pros**: Model-specific
   - **Cons**: Slower, different for each model
3. **Simple word count * 1.3**
   - **Pros**: Very fast
   - **Cons**: Highly inaccurate

### Consequences
**Positive**:
- Accurate chunk sizing
- Respects token limits reliably
- Performance is good with caching
- Industry-standard approach

**Negative**:
- Additional dependency
- Rust compilation on install
- cl100k_base may not match all LLMs exactly

**Note**: LRU cache on tokenizer reduces overhead significantly.

---

## Decision 7: Recursive Character Text Splitter

**Status**: Accepted
**Date**: 2025-11-09
**Area**: Chunking

### Context
Need to split documents into chunks while preserving semantic boundaries and respecting token limits.

### Decision
Implement RecursiveCharacterTextSplitter that tries increasingly smaller separators:
1. Paragraphs (`\n\n`)
2. Lines (`\n`)
3. Sentences (`. `)
4. Words (` `)
5. Characters (``)

### Rationale
- **Semantic Preservation**: Tries to split at natural boundaries
- **Fallback Strategy**: Falls back to smaller units if needed
- **Token-Aware**: Uses tiktoken for accurate sizing
- **Overlap Support**: Maintains context across chunks
- **Proven Pattern**: Used by LangChain and other RAG systems

### Alternatives Considered
1. **Fixed-size splitting**
   - **Pros**: Simple, predictable
   - **Cons**: Breaks mid-sentence, poor semantic boundaries
2. **Sentence-only splitting**
   - **Pros**: Clean boundaries
   - **Cons**: Sentences vary widely in token count
3. **Sliding window**
   - **Pros**: Maximum context preservation
   - **Cons**: Redundancy, more chunks to process
4. **Semantic chunking (AI-based)**
   - **Pros**: Best semantic boundaries
   - **Cons**: Slow, expensive, requires LLM calls

### Consequences
**Positive**:
- Good balance of semantic preservation and practicality
- Handles edge cases (very long sentences)
- Overlap maintains context
- Fast and reliable

**Negative**:
- Not perfect semantic boundaries
- Paragraph detection can be ambiguous
- Overlap creates some redundancy

**Future**: Consider semantic chunking for v0.3+ when speed is less critical.

---

## Decision 8: Click + Rich for CLI

**Status**: Accepted
**Date**: 2025-11-09
**Area**: CLI Interface

### Context
Need a user-friendly, professional command-line interface with progress feedback and good error handling.

### Decision
Use Click for CLI framework and Rich for terminal formatting.

### Rationale
- **Click**: Industry-standard CLI framework, clean API, excellent documentation
- **Rich**: Beautiful terminal output, tables, progress bars, syntax highlighting
- **Combination**: Click handles commands/args, Rich handles presentation
- **User Experience**: Progress bars and colors improve usability
- **Professional**: Polished appearance builds trust

### Alternatives Considered
1. **argparse + print**
   - **Pros**: Standard library, no dependencies
   - **Cons**: Verbose, ugly output, more code
2. **typer**
   - **Pros**: Type hints for CLI, based on Click
   - **Cons**: Extra layer of abstraction, less mature
3. **docopt**
   - **Pros**: Declarative CLI from docstrings
   - **Cons**: Less flexible, harder to test
4. **Click alone (no Rich)**
   - **Cons**: Plain text output, no progress bars

### Consequences
**Positive**:
- Excellent developer experience
- Beautiful, professional output
- Progress bars for long operations
- Easy to test with CliRunner
- Good error messages

**Negative**:
- Two dependencies instead of stdlib
- Rich adds ~1MB to install size
- Some learning curve for contributors

**User Feedback**: Users appreciate progress bars and clean formatting.

---

## Decision 9: Privacy-Safe Logging

**Status**: Accepted
**Date**: 2025-11-09
**Area**: Logging, Security

### Context
Logs may inadvertently capture sensitive information (passwords, API keys, document content). Need to prevent PII leakage.

### Decision
Implement privacy-safe logging with automatic PII filtering:
- Filter sensitive keys (password, token, api_key, secret, etc.)
- Redact content in error messages
- Structured logging for better filtering

### Rationale
- **Privacy-First**: Core principle of ragged
- **Compliance**: Prevents accidental logging of sensitive data
- **Security**: Logs can be safely shared for debugging
- **Best Practice**: Industry standard for secure applications

### Implementation
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

### Alternatives Considered
1. **No filtering**
   - **Rejected**: Too risky for privacy-first system
2. **Manual redaction**
   - **Rejected**: Error-prone, easy to forget
3. **Disable logging entirely**
   - **Rejected**: Logs are valuable for debugging

### Consequences
**Positive**:
- Logs are safe to share
- Automatic protection (can't forget to redact)
- Maintains privacy-first principle
- Compliance-friendly

**Negative**:
- May redact too aggressively (false positives)
- Slightly slower logging
- Debugging harder if needed info is redacted

**Lessons**: Consider log levels - DEBUG could be less aggressive, WARN/ERROR more aggressive.

---

## Decision 10: Factory Pattern for Embedders

**Status**: Accepted
**Date**: 2025-11-09
**Area**: Architecture, Embeddings

### Context
Multiple embedding backends need to be swappable without changing calling code.

### Decision
Implement factory pattern:
- `BaseEmbedder` abstract class
- `create_embedder()` factory method
- `get_embedder()` singleton access
- Configuration-driven selection

### Rationale
- **Swappability**: Change models without code changes
- **Testability**: Easy to mock for tests
- **Extensibility**: New backends just implement interface
- **Configuration**: Runtime selection via config
- **Best Practice**: Standard design pattern for this use case

### Alternatives Considered
1. **Direct instantiation everywhere**
   - **Rejected**: Hard to change, not DRY
2. **Dependency injection**
   - **Deferred**: Overkill for v0.1, consider for v0.3+
3. **Strategy pattern**
   - **Similar**: Factory is simpler for this case

### Consequences
**Positive**:
- Easy to add new embedding backends
- Clean separation of concerns
- Configuration-driven behavior
- Testable without real embedders

**Negative**:
- Extra abstraction layer
- Slightly more code
- Need to update factory for each new backend

**Future**: Consider dependency injection for v0.3+ as system grows.

---

## Decision 11: Ollama for LLM Generation

**Status**: Accepted
**Date**: 2025-11-09
**Area**: LLM, Generation

### Context
Need local LLM for answer generation that respects privacy-first principle.

### Decision
Use Ollama as the LLM backend with llama3.2 as default model.

### Rationale
- **Local**: Fully local execution, no external APIs
- **Simple**: Clean API, easy integration
- **Model Choice**: Access to llama3.2, mistral, others
- **Active Development**: Regular updates, growing ecosystem
- **Performance**: Optimized for local inference
- **Streaming Support**: Can stream responses for better UX

### Alternatives Considered
1. **OpenAI API**
   - **Rejected**: Violates privacy-first (external API)
2. **llamacpp**
   - **Pros**: Direct integration, no service
   - **Cons**: More complex, harder to swap models
3. **LocalAI**
   - **Pros**: OpenAI-compatible API
   - **Cons**: Less mature than Ollama
4. **Hugging Face transformers**
   - **Pros**: Direct model access
   - **Cons**: More complex, memory-intensive, slower

### Consequences
**Positive**:
- Fully local processing
- Easy model switching (ollama pull <model>)
- Good performance on M-series Macs
- Clean API for generation

**Negative**:
- Requires Ollama service running
- Another dependency/service to manage
- Model quality depends on user's hardware

**Future**: May add support for other backends (LocalAI, llamacpp) in v0.2+.

---

## Decision 12: Citation Format [Source: filename]

**Status**: Accepted
**Date**: 2025-11-09
**Area**: Generation, UX

### Context
Need a clear, parseable citation format for LLM-generated answers.

### Decision
Use `[Source: filename]` format for citations:
- Clear and readable for users
- Easily extractable with regex
- Common in documentation/markdown
- LLMs understand and follow it reliably

### Rationale
- **Readability**: Users immediately understand it
- **Parseability**: Simple regex extraction
- **LLM-Friendly**: Common format in training data
- **Markdown-Compatible**: Renders well in markdown
- **Unambiguous**: Square brackets distinguish from parenthetical notes

### Alternatives Considered
1. **Footnote numbers [1], [2]**
   - **Pros**: Cleaner in text
   - **Cons**: Requires mapping, harder to parse, less clear
2. **Inline (filename)**
   - **Pros**: Simpler
   - **Cons**: Ambiguous with other parenthetical content
3. **HTML-style <cite>filename</cite>**
   - **Pros**: Structured
   - **Cons**: Ugly in plain text, LLMs less reliable
4. **No citations**
   - **Rejected**: Citations are core feature for trust

### Implementation
System prompt:
```
Include citations in your answer using [Source: filename] format.
```

Extraction:
```python
pattern = r'\[Source:\s*([^\]]+)\]'
citations = re.findall(pattern, response_text)
```

### Consequences
**Positive**:
- Users know where information came from
- Simple to implement and parse
- LLMs follow instructions well
- Clean presentation

**Negative**:
- Manual citation by LLM (not always perfect)
- Can't verify citation accuracy automatically
- Multiple citations can clutter text

**Future**: Consider automatic citation verification in v0.2+ (map citations to actual chunks).

---

## Decision 13: Local-Only Processing (No External APIs)

**Status**: Accepted
**Date**: 2025-11-09
**Area**: Architecture, Privacy

### Context
ragged's core principle is privacy-first local document processing.

### Decision
Absolutely no external API calls:
- No OpenAI API
- No Anthropic API
- No cloud services
- All processing on user's machine

### Rationale
- **Privacy**: User's documents never leave their machine
- **Trust**: No third-party data access
- **Compliance**: Easier for sensitive documents
- **Offline**: Works without internet
- **Cost**: No per-use API costs
- **Control**: User controls all models and data

### Alternatives Considered
1. **Hybrid (local + optional cloud)**
   - **Rejected**: Adds complexity, violates core principle
2. **Cloud-first with local fallback**
   - **Rejected**: Opposite of privacy-first philosophy

### Consequences
**Positive**:
- True privacy preservation
- No API costs
- Works offline
- User owns all data
- Compliance-friendly
- Trust-building

**Negative**:
- Quality limited by local models
- Requires local compute resources
- Setup more complex (Ollama, models)
- Slower than cloud APIs

**Non-Negotiable**: This is a core principle of ragged, not up for debate.

**Future**: Always maintain local-only option, even if cloud features added in pro version.

---

## Decision 14: Markdown as Intermediate Format

**Status**: Accepted
**Date**: 2025-11-09
**Area**: Document Processing

### Context
After loading documents from various formats, need a common intermediate representation.

### Decision
Use Markdown as the intermediate format for all documents:
- PyMuPDF4LLM converts PDF → Markdown
- TXT remains as plain text (compatible)
- Markdown files unchanged
- HTML converted to Markdown via Trafilatura

### Rationale
- **Structure Preservation**: Markdown preserves headings, lists, etc.
- **LLM-Friendly**: Markdown is common in LLM training data
- **Human-Readable**: Easy to debug and inspect
- **Consistent**: Single format for all downstream processing
- **Semantic**: More semantic than plain text
- **Tooling**: Rich ecosystem of markdown tools

### Alternatives Considered
1. **Plain text**
   - **Pros**: Simple, universal
   - **Cons**: Loses all structure
2. **HTML**
   - **Pros**: Rich structure
   - **Cons**: Noisy tags, harder for LLMs
3. **Custom structured format**
   - **Pros**: Optimized for RAG
   - **Cons**: More work, less compatible

### Consequences
**Positive**:
- Better retrieval (semantic structure helps)
- Better generation (LLMs understand markdown)
- Human-debuggable intermediate format
- Consistent processing pipeline

**Negative**:
- Conversion quality depends on source
- Some information loss (e.g., PDF formatting)
- Markdown parsing complexity

**Lessons**: Markdown is an excellent LLM-friendly intermediate representation.

---

## Summary of Key Decisions

### Architecture Patterns
- **Factory Pattern**: Embedders
- **Abstract Base Classes**: BaseEmbedder
- **Singleton Pattern**: Embedder caching
- **Strategy Pattern**: Multiple loaders

### Technology Choices
- **Pydantic v2**: Configuration + data validation
- **ChromaDB**: Vector storage
- **tiktoken**: Token counting
- **Click + Rich**: CLI
- **Ollama**: LLM backend
- **PyMuPDF4LLM**: PDF processing

### Core Principles
- **Privacy-First**: No external APIs, ever
- **Local-Only**: All processing on user's machine
- **Type-Safe**: Pydantic throughout
- **Modular**: Clear separation of concerns
- **Extensible**: Easy to add new backends

### Process Decisions
- **14 Phases**: Incremental development
- **Hybrid TDD**: Tests for core logic
- **Markdown**: Intermediate format
- **[Source: filename]**: Citation format

---

**Last Updated**: 2025-11-09
**Total Decisions**: 14
**Status**: All accepted and implemented in v0.1
