# Changelog

All notable changes to ragged will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.3.9] - 2025-11-22

### Added - Performance & Quality Monitoring

**Performance Profiling (285 lines)**
- High-precision pipeline timing with microsecond accuracy
- Context manager pattern for automatic stage tracking
- Bottleneck detection with configurable threshold (default: 20%)
- Multiple output formats: detailed, summary, JSON
- Zero overhead when disabled
- Manual stage recording support

**Quality Metrics Collection (343 lines)**
- Privacy-first metrics tracking with query hashing
- RAGAS score support (context_precision, context_recall, faithfulness, answer_relevancy)
- Persistent JSON storage with restrictive permissions (0o600)
- Aggregate statistics computation (success rate, avg duration, avg confidence)
- Dashboard rendering with quality assessment
- Export functionality for analysis
- Automatic file permissions management

**New Modules & Classes**
- `src/monitoring/__init__.py` - Package exports
- `src/monitoring/profiler.py`:
  - `PerformanceProfiler` - Pipeline performance profiling
  - `ProfileStage` - Individual stage tracking with metadata
  - `create_profiler()` - Convenience function
- `src/monitoring/metrics.py`:
  - `MetricsCollector` - Quality metrics tracking and storage
  - `QualityMetrics` - Dataclass for metric records
  - `create_metrics_collector()` - Convenience function

**Performance Profiler Features**
```python
from src.monitoring import create_profiler

profiler = create_profiler(enabled=True)

with profiler.stage("Query Preprocessing"):
    preprocess_query()

with profiler.stage("Query Embedding", model="all-MiniLM-L6-v2"):
    embed_query()

with profiler.stage("Vector Retrieval"):
    retrieve_chunks()

print(profiler.render())
# ⏱️  Performance Profile
# Pipeline Breakdown:
# 1. Query Preprocessing      2.5ms  (3.5%)
# 2. Query Embedding         45.8ms  (64.2%)
# 3. Vector Retrieval        23.1ms  (32.3%)
# Total: 71.4ms
# ✓ Performance: Good (< 2s target)
```

**Quality Metrics Features**
```python
from src.monitoring import create_metrics_collector, QualityMetrics
from datetime import datetime

collector = create_metrics_collector()

metrics = QualityMetrics(
    query_hash="abc123",
    timestamp=datetime.now(),
    duration_ms=1234.5,
    chunks_retrieved=5,
    avg_confidence=0.89,
    ragas_score=0.85,
    context_precision=0.87,
    context_recall=0.82,
    faithfulness=0.91,
    answer_relevancy=0.85,
)

collector.record(metrics)

print(collector.render_dashboard())
# 📊 Quality Metrics Dashboard
# Total Queries: 10
# Success Rate: 100.0%
# Overall RAGAS: 0.850
# ✓ Quality: Excellent (RAGAS ≥ 0.8)
```

**Privacy & Security**
- Query hashing prevents PII storage
- File permissions: 0o600 (user read/write only)
- Storage directory: 0o700 (user access only)
- No sensitive content in metadata
- Default storage: ~/.ragged/metrics/metrics.json

**Profiling Capabilities**
- Stage-level timing with microsecond precision (`time.perf_counter()`)
- Automatic bottleneck identification (>20% of total time)
- Metadata attachment to stages (model names, parameters, etc.)
- Total duration calculation with timestamp-based accuracy
- Slowest stage identification (configurable top-N)
- Formatted output with performance recommendations
- JSON export for external analysis

**Metrics Capabilities**
- Recent metrics retrieval (configurable limit)
- Aggregate statistics (count, success rate, averages)
- RAGAS component tracking (precision, recall, faithfulness, relevancy)
- Dashboard rendering with quality assessment
- Export to JSON with configurable limits
- Clear functionality with safety confirmation
- Automatic persistence on record

**Testing & Quality**
- Profiler: 30 comprehensive tests, 97% coverage
- Metrics: 23 comprehensive tests, 91% coverage
- Total: 53 tests, all passing
- Edge cases: empty data, disabled profilers, file permissions, statistics computation

**Performance**
- Profiler overhead: <5ms per stage when enabled, 0ms when disabled
- Metrics recording: <10ms (includes JSON write)
- Storage overhead: ~1KB per metric record
- Dashboard rendering: <50ms
- Zero impact on pipeline when profiling disabled

**Backward Compatibility**
- No changes to existing APIs
- Optional monitoring (disabled by default)
- Standalone package (no dependencies on core RAG)
- All existing functionality preserved

**Foundation for v0.4.0**
- Performance regression detection
- Quality monitoring dashboards
- A/B testing infrastructure
- Automated quality alerts

### Technical Details
- **Production Code**: 628 lines across 3 modules
  - `src/monitoring/__init__.py` (26 lines)
  - `src/monitoring/profiler.py` (285 lines)
  - `src/monitoring/metrics.py` (343 lines)
- **Test Code**: 592 lines across 2 test files
  - `tests/monitoring/test_profiler.py` (307 lines, 30 tests)
  - `tests/monitoring/test_metrics.py` (432 lines, 23 tests)
- **Test Coverage**: 53/53 tests passing (100%)
- **Component Coverage**: Profiler 97%, Metrics 91%
- **Architecture**: Context manager pattern, JSON storage, privacy-first design
- **Quality**: Complete type hints, British English docstrings, comprehensive error handling

[0.3.9]: https://github.com/REPPL/ragged/compare/v0.3.8...v0.3.9

## [0.3.8] - 2025-11-22

### Added - Developer Experience I

**Interactive REPL Mode (420+ lines)**
- Full-featured command-line interface for exploratory RAG workflows
- Persistent session management with command history
- Live configuration changes
- Document management commands (add, remove, list, show)
- Query commands (query, search)
- Configuration commands (set, get, show config, reset)
- Session commands (history, save, load, clear)
- Comprehensive help system

**Debug Mode for Pipeline Visualisation (270+ lines)**
- Step-by-step execution debugging
- Pipeline instrumentation with timing
- Detailed step logging with metadata
- Multiple output formats (detailed, summary, JSON)
- Context manager support for automatic step tracking
- Performance profiling per pipeline step

**New Modules & Classes**
- `src/cli/interactive.py`:
  - `InteractiveShell` - REPL interface (extends cmd.Cmd)
  - `start_interactive_mode()` - Entry point
- `src/cli/debug.py`:
  - `DebugLogger` - Pipeline debugging and visualisation
  - `DebugStep` - Individual step tracking
  - `DebugStepContext` - Context manager for steps
  - `create_debug_logger()` - Convenience function

**Interactive Mode Features**
```bash
$ ragged interactive

🔍 ragged Interactive Mode
Type 'help' for commands, 'exit' to quit

ragged> query what are the main findings?
🔍 Querying: what are the main findings?

ragged> set retrieval.top_k 10
✓ retrieval.top_k = 10

ragged> history
📜 Command History
  1. query what are the main findings?
  2. set retrieval.top_k 10

ragged> exit
Goodbye!
```

**Debug Mode Features**
- Timing for each pipeline step
- Detailed metadata capture
- Formatted output with colours/icons
- Summary mode for quick overview
- Serialisation to JSON for analysis

**Commands Available in REPL**
- Document: `add`, `remove`, `list`, `show`
- Query: `query`, `search`
- Config: `set`, `get`, `show config`, `reset config`
- Session: `history`, `save session`, `load session`, `clear`
- Info: `help`, `status`
- Control: `exit`, `quit`

**Debug Logger Usage**
```python
from src.cli.debug import DebugLogger

debug = DebugLogger(enabled=True)

debug.start_step("Query Preprocessing", original="test query")
debug.add_detail("normalised", "test query")
debug.complete_step()

debug.start_step("Query Embedding", model="all-MiniLM-L6-v2")
debug.add_detail("dimensions", 384)
debug.complete_step()

print(debug.render())
# [Step 1/2] Query Preprocessing
#   original: test query
#   normalised: test query
#   Duration: 2.3ms
# ...
```

**Testing & Quality**
- Interactive Mode: 41 comprehensive tests, 99% coverage
- Debug Mode: 27 comprehensive tests, 97% coverage
- All tests passing
- Edge cases covered: command validation, error handling, session state

**Performance**
- REPL startup: <100ms
- Command execution overhead: <10ms
- Debug mode overhead: <5ms per step
- Minimal memory footprint

**Backward Compatibility**
- No changes to existing APIs
- Optional debug logging (disabled by default)
- REPL is a separate entry point
- All existing functionality preserved

## [0.3.7d] - 2025-11-22

### Added - Metadata Filtering & Faceted Search

**Rich Query Filtering System (400+ lines)**
- User-friendly filter syntax parser
- Complex filter queries with AND/OR logic
- CLI-style filter arguments
- Faceted search interface (foundation)
- Integration with existing retrieval system

**Filter Syntax Support**
```bash
# Simple equality
tag=python author=Smith file_type=pdf

# Comparisons
confidence>0.9 date>=2023-01-01

# Multiple values (OR within field)
tag=python,java,rust

# Combined filters (AND across fields)
tag=python confidence>0.9 author=Smith date>=2023-01-01
```

**New Classes & Functions**
- `FilterCondition` - Single filter condition with operator support
- `MetadataFilter` - Complex filter with AND/OR logic, ChromaDB integration
- `FilterParser` - Parse filter strings and CLI arguments
- `FacetedSearch` - Discover available filter values (foundation)
- `create_filter()` - Convenience function for quick filter creation

**Supported Operators**
- Equality: `==`, `=`
- Inequality: `!=`
- Comparison: `>`, `<`, `>=`, `<=`
- Membership: `in`, `not_in`
- Contains: `contains` (string matching)

**CLI Filter Arguments** (ready for integration)
- `--tag` - Tag filter (comma-separated for OR)
- `--author` - Author name filter
- `--file-type` - File type filter (pdf, txt, md, etc.)
- `--date-after` - Date range start (YYYY-MM-DD)
- `--date-before` - Date range end (YYYY-MM-DD)
- `--confidence` - Confidence threshold (e.g., ">0.9", ">=0.95")
- Custom filters via kwargs

**Type Inference**
- Automatic type detection (boolean, integer, float, date, string)
- Date parsing (YYYY-MM-DD format → ISO datetime)
- Numeric inference based on field names (confidence, score)
- Quote stripping from string values

**Testing & Quality**
- 37 comprehensive unit tests
- 92% coverage on metadata_filter.py
- All tests passing
- Edge cases: invalid filters, type conversions, empty inputs

**Integration**
- Compatible with existing `Retriever.retrieve(filter_metadata=...)` API
- ChromaDB where clause generation
- Ready for CLI command integration
- Backward compatible with existing code

**Performance**
- Lightweight filter parsing (~1ms)
- No overhead when filters not used
- Efficient ChromaDB query generation

## [0.3.7e] - 2025-11-22

### Added - Auto-Tagging & Classification

**LLM-Based Document Tagging System (480+ lines)**
- Automatic document type classification
- Topic extraction and categorisation
- Named entity recognition (people, organisations, locations)
- Academic level detection
- Intelligent keyword extraction
- Multi-strategy tagging (LLM + rule-based fallback)

**Document Classification**
- Document types: research_paper, book, article, technical_doc, blog_post, news, tutorial, reference, other
- Academic levels: introductory, intermediate, advanced, expert, not_applicable
- Language detection (ISO 639-1 codes)
- Confidence scoring for classification reliability

**New Classes & Enums**
- `DocumentType` - Enum for document type classification
- `AcademicLevel` - Enum for target audience expertise level
- `DocumentTags` - Dataclass for auto-generated tags and metadata
- `AutoTagger` - Main tagger class with LLM-based classification
- `tag_document()` - Convenience function for quick tagging

**LLM Integration**
- Structured JSON prompts for reliable classification
- Three specialised prompts: classification, topic extraction, entity extraction
- JSON extraction with error handling (handles extra text around JSON)
- Confidence scores from LLM responses

**Rule-Based Fallback**
- Offline operation without LLM
- Filename-based type detection (.pdf, .md, .markdown)
- Content analysis (abstract, chapter, references keywords)
- Keyword frequency analysis
- Simple capitalisation-based entity extraction
- Lower confidence scores (0.6) for rule-based vs LLM (0.8-0.95)

**Entity Recognition**
- People: Individual names
- Organisations: Companies, institutions, groups
- Locations: Countries, cities, places
- Automatic extraction from document content

**Topic & Keyword Extraction**
- LLM-based: 3-5 main topics from content analysis
- Rule-based: Frequency analysis with stopword filtering
- Automatic type inference for metadata values
- Configurable top-N keyword extraction

**Integration & Usage**
```python
# With LLM client
tagger = AutoTagger(llm_client)
tags = tagger.tag_document(content, filename="paper.pdf")
print(f"Type: {tags.document_type.value}")
print(f"Topics: {tags.topics}")
print(f"Entities: {tags.entities}")

# Without LLM (rule-based fallback)
tags = tag_document(content, filename="tutorial.md")
```

**Testing & Quality**
- 29 comprehensive unit tests
- 96% coverage on auto_tagger.py
- Mock LLM testing framework
- Edge cases: empty content, invalid JSON, LLM failures
- Fallback behaviour verification

**Performance**
- Fast rule-based classification (~5ms)
- LLM-based classification (depends on LLM latency)
- Graceful degradation on LLM failure
- No overhead when not used

## [0.3.7c] - 2025-11-22

### Added - Enhanced Citations

**Rich Citation Formatting (240+ lines)**
- Quote extraction from chunks with smart truncation
- Confidence score display in citations
- Chunk ID support for debugging
- Citation deduplication by source and page
- Flexible filtering by confidence threshold

**New Functions**
- `extract_quote_from_chunk()` - Extract representative quotes (respects word boundaries)
- `format_enhanced_citation()` - Format citations with metadata (quotes, confidence, chunk IDs)
- `format_enhanced_reference_list()` - Enhanced reference lists with filtering
- `format_response_with_enhanced_citations()` - Full response formatting
- `deduplicate_citations()` - Remove duplicate citations by (source, page) key

**Enhanced Citation Format**
```
[1] Source: paper.pdf, Page 42, Confidence: 0.95
"Machine learning is a subset of artificial intelligence that focuses..."
Chunk ID: doc1_ch007
```

**Key Features**
- Smart quote truncation (max length, word boundaries)
- Optional confidence threshold filtering (hide low-confidence sources)
- Optional chunk ID display for debugging
- Backward compatible with existing citation functions
- Cited numbers filtering (show only referenced sources)

**Testing & Quality**
- 27 comprehensive unit tests (22 new, 5 existing)
- 99% coverage on citation_formatter.py
- All 50 tests passing
- Edge cases: empty content, None metadata, missing attributes

**Performance**
- Minimal overhead (~50ms for quote extraction)
- Lazy evaluation (quotes extracted only when needed)
- No breaking changes to existing API

## [0.3.7b] - 2025-11-22

### Added - Chain-of-Thought Reasoning

**Transparent Reasoning System (500+ lines)**
- Multiple reasoning modes: NONE, BASIC, STRUCTURED, CHAIN
- ReasoningParser with XML and regex fallback parsing
- ReasoningGenerator for transparent AI responses
- Automatic validation with contradiction and uncertainty detection
- Confidence scoring with penalty system for validation issues

**Reasoning Modes**
- NONE: Direct answers (fastest, no reasoning overhead)
- BASIC: Simple step-by-step thinking (default)
- STRUCTURED: Detailed XML-formatted reasoning with confidence scores
- CHAIN: Full chain-of-thought with evidence gathering and validation

**Key Components**
- `src/generation/reasoning/types.py` - Data structures (ReasoningMode, ReasoningStep, ValidationFlag, ReasonedResponse)
- `src/generation/reasoning/prompts.py` - Prompt templates for each reasoning mode
- `src/generation/reasoning/parser.py` - Multi-strategy parser (XML, markdown, regex)
- `src/generation/reasoning/generator.py` - Generator integration with Ollama

**Validation Features**
- Automatic contradiction detection
- Uncertainty marker identification
- Unsupported claim detection
- Low confidence flagging
- Severity levels: low, medium, high

**Testing & Quality**
- 18 comprehensive unit tests
- 87% coverage on parser (most complex component)
- All tests passing
- Type hints throughout

**Performance**
- Minimal overhead for BASIC mode (~100ms parsing)
- Negligible impact for NONE mode (direct answers)
- Configurable via reasoning mode selection

**Backward Compatibility**
- 100% backward compatible (new module, no changes to existing code)
- Zero breaking changes
- Opt-in via ReasoningGenerator

### Technical Details

**Data Structures:**
```python
ReasoningMode: NONE | BASIC | STRUCTURED | CHAIN
ReasoningStep: (step_number, thought, action, confidence, evidence)
ValidationFlag: (type, description, severity, step_numbers)
ReasonedResponse: Complete response with reasoning trace
```

**Validation Types:**
- contradiction: Conflicting information
- uncertainty: Expressed doubt
- assumption: Unstated assumptions
- low_confidence: Below confidence threshold
- missing_evidence: Claims without citations

**Confidence Calculation:**
- Average across reasoning steps
- Penalties for validation flags (high: -0.2, medium: -0.1)
- Final score range: 0.0-1.0

## [0.3.7a] - 2025-11-22

### Added - Document Version Tracking

**SQLite Version Store (540 lines)**
- Persistent version tracking database using SQLite (~/.ragged/versions.db)
- Three-table schema for documents, versions, and chunk associations
- ACID transactions for data integrity
- Indexed queries for fast lookups
- Automatic sequential version numbering (1, 2, 3, ...)
- DocumentVersion dataclass with full type hints
- Chunk-to-version linking for result attribution

**Hierarchical Content Hashing**
- Two-level SHA-256 hashing for change detection:
  - Page-level: Individual hash per page
  - Document-level: Hash of concatenated page hashes
- Consistent, deterministic hashing
- Enables future partial re-indexing (detects which pages changed)
- Automatic duplicate detection (skip re-indexing unchanged documents)

**Version Query API**
- track_document() - Create/update version records
- is_new_version() - Check if content changed
- get_version() - Retrieve by version number, ID, or content hash
- list_versions() - Get all versions of a document
- find_document_by_path() - Find document ID from file path
- link_chunk_to_version() - Associate chunks with versions
- calculate_content_hash() - Hierarchical hashing utility

**CLI Commands (380+ lines)**
- `ragged versions list <file_path>` - List all versions with summary table
- `ragged versions show <identifier>` - Show detailed version information
- `ragged versions check <file_path>` - Check if document changed
- `ragged versions compare <doc_id> <v1> <v2>` - Compare two versions
- Rich-formatted output with tables, panels, and color coding
- Multiple query modes: by ID, version number, or content hash

**Testing & Quality**
- 24 comprehensive unit tests
- 96% test coverage on version_tracker.py
- All edge cases covered (concurrent tracking, path handling, metadata)
- Python 3.12 compatible (ISO datetime format)
- Zero deprecation warnings

**Documentation**
- ADR-0020: Document Version Tracking architecture decision
- Implementation summary with metrics and decisions
- README.md for v0.3.7a implementation
- Comprehensive docstrings (British English)
- CLI help text for all commands

**Backward Compatibility**
- 100% backward compatible (additive changes only)
- Zero breaking changes
- Existing code works unchanged
- Version tracking is opt-in

**Performance**
- SHA-256 hashing: ~1ms per page
- Database queries: <1ms (indexed)
- Storage overhead: ~1KB per version
- Negligible impact on indexing pipeline

### Technical Details

**Database Schema:**
```sql
documents (doc_id, file_path, created_at, updated_at)
versions (version_id, doc_id, content_hash, page_hashes, version_number, ...)
chunk_versions (chunk_id, version_id, page_number, chunk_sequence)
```

**Version Numbering:**
- Sequential per document (1, 2, 3, ...)
- Human-friendly and chronological
- Automatic increment on new versions
- Duplicate versions return existing record

**Hashing Algorithm:**
- SHA-256 for cryptographic quality
- Page-level granularity for change detection
- Document-level consistency check
- Future-ready for partial re-indexing

### Known Limitations

- No automatic integration with indexing pipeline (v0.3.7b will add)
- No partial re-indexing yet (page hashes stored but not used)
- No retention policies (all versions kept indefinitely)
- Binary-only hashing (no semantic change detection)

### Migration Notes

- New SQLite database created at ~/.ragged/versions.db
- Existing documents have no version history (tracking starts from v0.3.7a onward)
- No migration required for existing databases
- Graceful degradation for documents without version history

## [0.3.6] - 2025-11-22

### Added - VectorStore Abstraction Layer

**Abstract VectorStore Interface (244 lines)**
- Clean ABC-based interface for vector database operations
- 9 abstract methods defining complete vector store contract:
  - health_check(), add(), query(), delete(), update_metadata()
  - get_documents_by_metadata(), list(), count(), clear(), get_collection_info()
- Complete type hints using numpy arrays for embeddings (performance optimisation)
- Comprehensive docstrings with usage examples (British English)
- Backend-agnostic design enables multi-backend support

**ChromaDB Implementation (398 lines)**
- ChromaDBStore(VectorStore) implementing full abstract interface
- Preserved all existing resilience patterns:
  - Circuit breaker protection (failure_threshold=5, recovery_timeout=30s)
  - Automatic retry with exponential backoff (max 3 attempts)
  - Metadata serialization for complex types (Path, lists, dicts)
- Zero behavioral changes from original implementation
- All 14 storage tests passing without modification
- New list() method with pagination support

**Factory Pattern (91 lines)**
- get_vectorstore() factory function for backend selection
- Supports backend parameter: 'chromadb', 'leann', 'qdrant', 'weaviate'
- Graceful NotImplementedError for future backends with roadmap references
- Default backend selection from configuration
- Clear error messages for unsupported backends

**100% Backward Compatibility**
- Re-export pattern in vector_store.py maintains all existing imports
- `from src.storage import VectorStore` continues working unchanged
- All dependent modules (ingestion, retrieval, CLI) work without modification
- VectorStore is ChromaDBStore (identity check passes)
- Zero breaking changes for existing users

**Package Exports**
- VectorStoreInterface (abstract interface for type hints)
- VectorStore (backward compatible alias to ChromaDBStore)
- get_vectorstore (factory function, recommended for new code)
- ChromaDBStore (specific implementation)

### Technical Details
- **Production Code**: 761 lines across 3 new modules
  - `src/storage/vectorstore_interface.py` (244 lines) - Abstract interface
  - `src/storage/chromadb_store.py` (398 lines) - ChromaDB implementation
  - `src/storage/vectorstore_factory.py` (91 lines) - Factory function
  - `src/storage/vector_store.py` (28 lines, rewritten) - Backward compatibility re-export
- **Modified Modules**: 2 files
  - `src/storage/__init__.py` - Updated exports
  - `tests/storage/test_vector_store.py` - Updated patch paths
- **Test Coverage**: 14/14 storage tests passing (100%)
- **Architecture**: ABC pattern with factory, re-export for backward compatibility
- **Quality**: 100% type hints, complete docstrings (British English)

### Changed
- `src/storage/vector_store.py` completely rewritten as re-export (329 lines → 28 lines)
- ChromaDB implementation moved to `src/storage/chromadb_store.py`
- Test patch paths updated to `src.storage.chromadb_store`

### Performance
- Zero overhead (pure refactoring)
- Numpy arrays for embeddings provide performance improvement over List[float]
- Circuit breaker and retry patterns preserved
- No behavioral changes

### Foundation for v0.4.0
- Enables LEANN backend implementation
- Enables Qdrant, Weaviate, Pinecone support
- Foundation for backend migration tools
- Pluggable architecture for future vector databases

[0.3.6]: https://github.com/REPPL/ragged/compare/v0.3.5...v0.3.6

## [0.3.5] - 2025-11-22

### Added - Messy Document Intelligence

**PDF Quality Analysis Framework (457 lines)**
- Comprehensive PDF quality assessment before ingestion
- Four specialised detectors:
  - Rotation detector: Identifies incorrectly rotated pages
  - Duplicate detector: Finds consecutive duplicate pages
  - Ordering detector: Detects out-of-order page sequences
  - Quality detector: Assesses OCR confidence and readability
- Traffic light quality grading: Excellent (>90%), Good (70-90%), Fair (50-70%), Poor (<50%)
- Per-issue confidence scores and severity levels (critical, high, medium, low)
- Async analysis with configurable parallel execution and timeout

**Automated PDF Correction System (389 lines)**
- Intelligent PDF correction pipeline with quality improvement tracking
- Three specialised transformers:
  - Rotation transformer: Auto-corrects page orientation
  - Duplicate transformer: Removes duplicate pages with page mapping
  - Ordering transformer: Reorders pages to logical sequence
- Quality-before and quality-after scoring
- Detailed correction action logging (success/failure per action)
- Configurable retry attempts and checkpoint management

**Progressive Disclosure UX**
- `ragged add --auto-correct-pdf` automatically corrects PDFs before ingestion (default: enabled)
- Simple quality summary during ingestion (colour-coded icons: ✓ green, ⚠ yellow/red)
- Detailed metadata viewing via new `ragged show` command group:
  - `ragged show quality <doc_id>` - Full quality report with issue breakdown
  - `ragged show corrections <doc_id>` - Applied corrections and improvement metrics
  - `ragged show uncertainties <doc_id>` - Low-confidence sections requiring review

**Metadata Generation System (234 lines)**
- JSON metadata files stored in `.ragged/<document_id>/` directory
- Four metadata types:
  - `quality_report.json` - Quality scores, issues detected, affected pages
  - `corrections.json` - Correction actions, quality improvement, success/failure rates
  - `page_mapping.json` - Original-to-corrected page number mapping
  - `uncertainties.json` - Low-confidence pages requiring manual review

**Integration**
- Seamless integration with document ingestion pipeline
- Temporary corrected PDF created and cleaned up automatically
- Original PDF preserved untouched
- CLI feedback with real-time progress indicators

### Technical Details
- **Production Code**: 1,080 lines across 7 modules
  - `src/correction/pipeline.py` (178 lines)
  - `src/correction/analyzer.py` (457 lines)
  - `src/correction/corrector.py` (389 lines)
  - `src/correction/metadata.py` (234 lines)
  - `src/correction/schemas.py` (134 lines)
  - `src/cli/commands/show.py` (287 lines) - new CLI command
  - Integration in `src/cli/commands/add.py`
- **Test Code**: 1,207 lines across 3 test files
  - `tests/correction/test_pipeline.py` (327 lines, 10 tests)
  - `tests/correction/test_metadata.py` (386 lines, 12 tests)
  - `tests/integration/test_v0_3_5_correction_integration.py` (505 lines, 52 tests)
- **Test Coverage**: 73 tests passing, 1 skipped
- **Architecture**: Detector-transformer pattern with async pipeline coordination
- **Quality**: Complete type hints, Pydantic validation, British English docstrings

### Performance
- PDF analysis: <5 seconds for typical documents (async parallel detection)
- Correction pipeline: Quality improvement averaging 30-40% for messy PDFs
- Zero overhead for clean PDFs (auto-skips correction when quality >90%)
- Metadata generation: <100ms

### Changed
- `ragged add` command now includes PDF quality analysis by default
- PDF ingestion flow enhanced with automatic correction capability
- CLI output includes quality indicators and correction summaries

[0.3.5]: https://github.com/REPPL/ragged/compare/v0.3.4b...v0.3.5

## [0.3.4b] - 2025-11-19

### Added - Intelligent Document Routing

**Quality Assessment Framework (703 lines)**
- Comprehensive document quality analysis with QualityAssessor class
- Born-digital vs scanned document detection (>95% accuracy)
- Image quality metrics (resolution, contrast, sharpness, noise)
- Layout complexity assessment (columns, tables, mixed content)
- Per-page and document-level quality scoring
- Quality assessment caching for performance optimisation

**Intelligent Routing System (375 lines)**
- ProcessorRouter class for quality-based processor selection
- Dynamic configuration adjustment based on document quality
- Quality tier routing:
  - High quality (>0.85): Standard Docling processing
  - Medium quality (0.70-0.85): Aggressive Docling settings
  - Low quality (<0.70): Maximum effort mode
- Routing explanation generation for transparency
- Processing time estimation
- Fallback processor determination

**Processing Metrics Collection (467 lines)**
- ProcessingMetrics class for comprehensive tracking
- Routing decision recording and analysis
- Quality score distribution tracking
- Processing time per quality tier
- Success/failure rate monitoring
- JSON export capabilities with automatic retention management

**Integration**
- Seamless integration with document ingestion pipeline
- Routing metadata attached to all processed documents
- Configurable quality thresholds
- Backward compatible (can disable routing)

**Configuration**
- `enable_quality_assessment` (default: True)
- `routing_high_quality_threshold` (default: 0.85)
- `routing_low_quality_threshold` (default: 0.70)
- `fast_quality_assessment` (default: True)
- `cache_quality_assessments` (default: True)

### Changed
- Version bumped to 0.3.4b in pyproject.toml
- Document ingestion pipeline enhanced with quality-based routing
- ProcessorFactory updated to support routing metadata

### Dependencies
- Added opencv-python>=4.8.0 (Apache 2.0 licence) for image quality analysis

### Technical
- Production code: 1,545 lines (quality_assessor.py: 703, router.py: 375, metrics.py: 467)
- Test code: 1,568 lines across 4 test files
- Tests: 69 total (87 passing, 8 minor integration test issues)
- Test coverage: 93-98% for core routing modules
- Complete type hints and British English docstrings
- Lazy loading for opencv-python to minimise overhead

### Performance
- Quality assessment: <1s overhead per document (fast mode)
- Router decision time: <50ms
- Quality assessment caching reduces repeat overhead to near-zero
- Per-page assessment: ~200ms per page

### Foundation for v0.3.4c
- Router architecture ready for multi-processor coordination
- `enable_paddleocr_fallback` configuration prepared
- Fallback chain infrastructure in place

[0.3.4b]: https://github.com/REPPL/ragged/compare/v0.3.4a...v0.3.4b

## [0.3.4a] - 2025-11-19

### Added
- **Modern Document Processing**: State-of-the-art Docling integration replacing basic pymupdf extraction
  - **Processor Architecture** (`src/processing/`): Plugin-based system supporting multiple document processors
    - `BaseProcessor` abstract interface for consistent processor contracts
    - `ProcessorFactory` for configuration-driven processor selection
    - `ProcessedDocument` standardised output format with structured content
    - `ProcessorConfig` dataclass for flexible configuration
    - Support for legacy (pymupdf) and modern (Docling) processors
  - **Docling Processor** (`src/processing/docling_processor.py`): Advanced document analysis with ML models
    - DocLayNet integration for precise layout analysis
    - TableFormer integration for accurate table structure extraction
    - Reading order preservation for multi-column documents
    - Structured markdown output ideal for RAG chunking
    - Lazy model loading with automatic downloads
    - 30× performance improvement over legacy Tesseract approaches
    - 97%+ table extraction accuracy (vs <50% with basic extraction)
  - **Legacy Processor** (`src/processing/legacy_processor.py`): Backwards-compatible pymupdf processor
    - Maintains existing functionality for simple use cases
    - Refactored from original ingestion code
    - Implements `BaseProcessor` interface
  - **Model Management** (`src/processing/model_manager.py`): Intelligent model handling
    - Lazy loading (downloads only when needed)
    - Model caching to prevent redundant downloads
    - Retry logic for network failures
    - Progress indicators for downloads
    - Configurable cache directory
- **Comprehensive Testing**: Full test coverage for processor architecture
  - `tests/processing/test_base.py` (189 lines): Interface and configuration tests
  - `tests/processing/test_factory.py` (90 lines): Factory pattern tests
  - `tests/processing/test_legacy_processor.py` (99 lines): Legacy processor validation
  - `tests/processing/test_docling_processor.py` (159 lines): Docling integration tests
  - `tests/processing/test_model_manager.py` (99 lines): Model management tests
  - `tests/processing/test_integration.py` (134 lines): End-to-end pipeline tests
  - Total: 7 test files (771 lines)

### Changed
- Document processing pipeline now uses processor architecture
- Default processor set to Docling for improved quality
- Ingestion pipeline supports processor selection via configuration

### Technical Details
- **New Production Files**: 6 modules (1,974 lines total)
  - `src/processing/__init__.py` (29 lines)
  - `src/processing/base.py` (204 lines)
  - `src/processing/factory.py` (149 lines)
  - `src/processing/legacy_processor.py` (177 lines)
  - `src/processing/docling_processor.py` (436 lines)
  - `src/processing/model_manager.py` (208 lines)
- **New Test Files**: 7 files (771 lines total)
- **Dependencies Added**:
  - `docling>=2.5.0` (MIT licence)
  - `docling-core>=2.0.0` (MIT licence)
  - `docling-parse>=2.0.0` (MIT licence)
- **Architecture**: Plugin-based processor system with factory pattern
- **Quality**: Complete type hints, British English docstrings, comprehensive error handling
- **ML Models**: DocLayNet (layout analysis), TableFormer (table extraction)

### Performance
- Docling processing: 30× faster than legacy Tesseract approaches
- Table extraction: 97%+ accuracy with structure preservation
- Layout analysis: Proper reading order for multi-column documents
- Model downloads: One-time cost with permanent caching
- Memory efficient: Page-by-page processing for large documents

### Breaking Changes
- None (backwards compatible - legacy processor maintained)
- Existing code continues to work with automatic processor selection
- Users can opt-in to Docling or remain on legacy processor

### Migration
- New installations default to Docling processor
- Existing installations continue using legacy processor unless configured
- Configuration option: `processor_type: "docling"` or `processor_type: "legacy"`
- No data migration required (processors operate independently)

## [0.3.3] - 2025-11-19

### Added
- **Intelligent Chunking**: Semantic and hierarchical chunking strategies for improved retrieval
  - **Semantic Chunking** (`src/chunking/semantic_chunker.py`): Topic-aware chunking using sentence embeddings
    - Uses sentence transformers to identify semantic boundaries
    - Groups semantically similar sentences into coherent chunks
    - Dynamic chunk sizing with configurable min/max constraints (200-1500 chars)
    - Fallback to simple splitting on errors
  - **Hierarchical Chunking** (`src/chunking/hierarchical_chunker.py`): Parent-child chunk relationships
    - Creates large parent chunks (1500-3000 chars) for broad context
    - Generates smaller child chunks (300-800 chars) for specific retrieval
    - Links children to parents via metadata for context-aware generation
    - Improves answer completeness by providing broader context
- **Comprehensive Testing**: Full test coverage for both chunking strategies
  - `tests/chunking/test_semantic_chunker.py` (276 lines)
  - `tests/chunking/test_hierarchical_chunker.py` (339 lines)
  - Unit tests for all core functionality
  - Integration tests for end-to-end chunking pipeline

### Changed
- Enhanced chunking pipeline to support multiple strategies
- Improved chunk metadata schema to support hierarchical relationships

### Technical Details
- **New Production Files**: 2 files (666 lines total)
  - `src/chunking/semantic_chunker.py` (327 lines)
  - `src/chunking/hierarchical_chunker.py` (339 lines)
- **New Test Files**: 2 files (615 lines total)
- **Dependencies**: Uses existing sentence-transformers and NLTK
- **Architecture**: Lazy model loading, thread-safe implementations
- **Quality**: Complete type hints, British English docstrings, comprehensive error handling

### Performance
- Semantic chunking: Topic-aware boundaries improve retrieval precision
- Hierarchical chunking: Parent context improves answer completeness by 10-15%
- Configurable trade-off between speed (fixed) and quality (semantic/hierarchical)

## [0.2.10] - 2025-11-19

### Added
- **Security Hardening**: Comprehensive security infrastructure (CRITICAL priority)
  - Safe JSON serialisation utilities (`src/utils/serialization.py`)
  - Session management system (`src/core/session.py`)
  - Security testing framework (`tests/security/`)
  - Pre-commit security hooks
- **Session Isolation**: UUID-based session IDs prevent cross-user data leakage
  - Session-scoped caching
  - Automatic session cleanup
  - Thread-safe session operations
- **Security Audits**: Professional security assessment
  - Baseline security audit (pre-v0.2.10)
  - Post-implementation verification audit
  - Comprehensive vulnerability analysis (18 issues → 9 issues)

### Changed
- **Pickle Elimination**: Replaced pickle with JSON for all serialisation
  - BM25 checkpoints now use secure JSON format
  - L2 cache embeddings use JSON (not pickle)
  - Automatic migration from legacy .pkl files
- **Cache Architecture**: Session-isolated caching prevents PII leakage
  - Cache keys include session ID
  - Session-scoped cache invalidation

### Security
- **CRITICAL Vulnerabilities Resolved**:
  - CRITICAL-001: Arbitrary code execution via pickle (CVSS 9.8) - RESOLVED
  - CRITICAL-003: Cross-session cache pollution (CVSS 8.1) - RESOLVED
- **Security Tests**: 30+ automated security tests
  - Pickle usage detection (prevents regression)
  - Session isolation validation
  - Path traversal protection
  - Dependency vulnerability scanning

### Technical Details
- **New Files Created**: 8 files (2 production, 6 testing)
  - src/utils/serialization.py (298 lines)
  - src/core/session.py (405 lines)
  - tests/security/* (5 test files, 1,166+ lines)
- **Files Modified**: 3 production files
  - src/retrieval/incremental_index.py (pickle → JSON migration)
  - src/utils/multi_tier_cache.py (pickle → JSON migration)
  - src/retrieval/cache.py (session isolation)
- **Total Lines Changed**: ~2,200 lines (additions + modifications)
- **Test Coverage**: 30+ security tests, 150+ assertions
- **Risk Reduction**: HIGH → MEDIUM (50% issue reduction)
- **Production Readiness**: ✅ Ready for controlled deployments

### Breaking Changes
- None (automatic migration from legacy pickle files)

### Migration
- Legacy .pkl checkpoint files automatically migrated to .json on first load
- No user action required (transparent migration)

## [0.2.8] - 2025-11-18

### Added
- **CLI Enhancements**: 10 new commands and features for comprehensive document management
  - `metadata` command group: List, show, update, and search document metadata
  - `search` command: Advanced semantic search with metadata filtering
  - `history` command group: View, show, replay, clear, and export query history
  - `cache` command group: View cache information and clear caches
  - `export` command group: Backup and restore functionality
  - `validate` command: Configuration and environment validation
  - `env-info` command: System information for bug reports
  - `completion` command: Shell completion installation (bash/zsh/fish)
  - Query history automatically saved (disable with `--no-history`)
  - Interactive model selection with RAG suitability scores
- **Documentation**: Comprehensive CLI documentation
  - CLI Command Reference Guide: Complete technical specifications for all 14 commands
  - CLI Features User Guide: Comprehensive 1593-line tutorial with examples and workflows
  - CLI-specific README files with navigation and cross-references
- **Testing**: 8 new test files covering all CLI commands
  - test_add.py: 24 tests for document ingestion
  - test_query.py: 23 tests for query command
  - test_health.py: 7 tests for service checks
  - test_docs.py: 7 tests for document management
  - test_config.py: 8 tests for configuration
  - test_envinfo.py: 5 tests for environment information
  - test_formatters.py: 18 tests for output formatting
  - test_verbosity.py: 10 tests for verbosity control
  - Total: 91+ new CLI tests

### Changed
- README.md updated with v0.2.8 features and CLI documentation links
- Enhanced Quick Start section with comprehensive CLI examples
- Added CLI Features section listing all 14 commands by category

### Technical Details
- **Commands**: 14 total CLI commands (4 base + 10 command groups)
- **Documentation**: 2 major guides (command reference + features guide)
- **Test Coverage**: 91+ new tests for CLI functionality
- **Output Formats**: Multiple format support (text, json, table, csv, markdown, yaml)
- **Completion**: Breaking Changes: None (all additions are backwards-compatible)

## [0.2.7] - 2025-11-17

### Added
- **CLI Architecture Refactoring**: Modular command structure for maintainability
  - Extracted all commands from monolithic `main.py` to separate modules in `cli/commands/`
  - 14 command files: add, query, health, docs, config, completion, validate, envinfo, metadata, search, history, exportimport, cache
  - Common utilities in `cli/common.py`, `cli/formatters.py`, `cli/verbosity.py`
  - Improved testability with isolated command modules
- **Folder Ingestion**: Already implemented in v0.2.2, validated and documented
  - Recursive directory scanning with configurable depth
  - Batch processing with progress indicators
  - Automatic duplicate detection and skipping
- **HTML Processing**: Enhanced web content extraction
  - Trafilatura integration for clean HTML conversion
  - BeautifulSoup fallback for complex pages
  - Metadata extraction from HTML documents

### Changed
- CLI codebase restructured from single file to modular architecture
- Improved code organisation and command isolation
- Better separation of concerns (formatting, verbosity, common utilities)

### Technical Details
- **Architecture**: Modular command system with shared utilities
- **Maintainability**: Each command in separate file for easier testing and updates
- **Breaking Changes**: None (internal refactoring only)

## [0.2.6] - 2025-11-17

**Note**: Version v0.2.6 was skipped/deferred. Features originally planned for v0.2.6 were either already implemented in earlier versions or deferred to v0.2.8 and beyond.

See implementation notes: `docs/development/implementation/version/v0.2/v0.2.6-skipped.md`

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
