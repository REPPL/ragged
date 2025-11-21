# Ragged v0.5.0 Roadmap - ColPali Vision Integration

**Status:** Planned

**Total Hours:** 171-231 hours (detailed breakdown below)

**Focus:** Multi-modal document understanding with vision-based retrieval

**Breaking Changes:** None

---

## Overview

Version 0.5.0 introduces ColPali vision integration for multi-modal document understanding. This enables vision-based retrieval that can understand document layouts, diagrams, tables, and images without relying solely on text extraction.

**Key Deliverables:**
- Vision embeddings for PDF pages (768-dimensional ColPali embeddings)
- Dual text+vision storage in ChromaDB
- Multi-modal queries (text, image, hybrid)
- Intelligent GPU resource management
- Comprehensive CLI and web UI for vision features

**Dependencies:** Requires v0.4.0 completion (knowledge graphs and personal memory)

**GPU Requirements:**
- Recommended: CUDA-compatible GPU (8GB+ VRAM) or Apple Silicon (MPS)
- Fallback: CPU-only mode supported (slower)

---

## Implementation Execution Checklist

Total: 88 checkboxes across 6 features + testing

### VISION-001: ColPali Integration (30-40 hours)

**[Detailed Implementation Plan](./features/VISION-001-colpali-integration.md)**

**Phase 1: Research & Dependencies (6h)**
- [ ] 1.1: Research ColPali architecture and VidOre model (4h)
  - [ ] Study ColPali paper and implementation
  - [ ] Review VidOre ColPali model requirements
  - [ ] Identify optimal model variant for ragged
  - [ ] Document embedding dimension (768) and architecture
- [ ] 1.2: Install dependencies and verify GPU access (2h)
  - [ ] Add torch, transformers, pillow to pyproject.toml
  - [ ] Test CUDA/MPS/CPU device detection
  - [ ] Verify model downloads successfully

**Phase 2: Core ColPali Embedder (14-18h)**
- [ ] 2.1: Create ColPaliEmbedder class skeleton (4h)
  - [ ] Implement BaseEmbedder interface
  - [ ] Add device detection logic (CUDA > MPS > CPU)
  - [ ] Implement model loading with caching
- [ ] 2.2: Implement PDF page processing (4h)
  - [ ] Convert PDF pages to PIL Images
  - [ ] Implement image preprocessing for ColPali
  - [ ] Handle multi-page PDFs efficiently
- [ ] 2.3: Add GPU memory monitoring (3-4h)
  - [ ] Track VRAM usage during embedding
  - [ ] Implement batch size recommendations
  - [ ] Add memory warnings for large batches
- [ ] 2.4: Error handling and fallbacks (3-4h)
  - [ ] GPU unavailable → CPU fallback
  - [ ] OOM errors → reduce batch size
  - [ ] Invalid PDF handling

**Phase 3: Integration & Configuration (6-8h)**
- [ ] 3.1: Update configuration system (3-4h)
  - [ ] Add ColPali settings to config
  - [ ] Add GPU device selection options
  - [ ] Add batch size configuration
- [ ] 3.2: CLI integration (3-4h)
  - [ ] Add --vision flag to ingest command
  - [ ] Add --device option for GPU selection
  - [ ] Update help text and examples

**Phase 4: Testing (4-6h)**
- [ ] 4.1: Unit tests (2-3h)
  - [ ] Test model initialization (CPU, CUDA, MPS)
  - [ ] Test single-page embedding generation
  - [ ] Test batch embedding processing
  - [ ] Test device fallback logic
- [ ] 4.2: Integration tests (2-3h)
  - [ ] Test full PDF document processing
  - [ ] Test GPU memory management
  - [ ] Test error recovery scenarios

---

### VISION-002: Dual Storage (25-35 hours)

**[Detailed Implementation Plan](./features/VISION-002-dual-storage.md)**

**Phase 1: Schema Extension (6-8h)**
- [ ] 1.1: ChromaDB collection schema design (3-4h)
  - [ ] Create embedding type enumeration (text/vision)
  - [ ] Design metadata schema for both types
  - [ ] Implement ID generation (doc_chunk_N_text, doc_page_N_vision)
- [ ] 1.2: Migration utilities (3-4h)
  - [ ] Create v0.4 → v0.5 migration script
  - [ ] Implement schema version detection
  - [ ] Add dry-run mode for safe migration

**Phase 2: DualEmbeddingStore Implementation (8-10h)**
- [ ] 2.1: Create DualEmbeddingStore class (4-5h)
  - [ ] Implement add_text_embedding()
  - [ ] Implement add_vision_embedding()
  - [ ] Implement add_batch() for bulk operations
  - [ ] Add embedding dimension validation
- [ ] 2.2: Query interface (4-5h)
  - [ ] Implement query_text() (text-only)
  - [ ] Implement query_vision() (vision-only)
  - [ ] Implement query_hybrid() with RRF fusion
  - [ ] Add metadata filtering support

**Phase 3: Integration with Ingestion (6-8h)**
- [ ] 3.1: Update DocumentProcessor (3-4h)
  - [ ] Integrate dual storage in ingestion pipeline
  - [ ] Add configurable vision embedding toggle
  - [ ] Implement batch processing for efficiency
- [ ] 3.2: CLI and configuration (3-4h)
  - [ ] Add dual storage configuration options
  - [ ] Update CLI commands for vision storage
  - [ ] Add collection management commands

**Phase 4: Testing (4-6h)**
- [ ] 4.1: Unit tests (2-3h)
  - [ ] Test text/vision embedding addition
  - [ ] Test query methods (text, vision, hybrid)
  - [ ] Test dimension validation
  - [ ] Test batch operations
- [ ] 4.2: Integration tests (2-3h)
  - [ ] Test end-to-end dual storage workflow
  - [ ] Test migration from v0.4 schema
  - [ ] Test hybrid retrieval accuracy

---

### VISION-003: Vision Retrieval (28-38 hours)

**[Detailed Implementation Plan](./features/VISION-003-vision-retrieval.md)**

**Phase 1: Multi-Modal Query Processing (8-10h)**
- [ ] 1.1: Query type detection (3-4h)
  - [ ] Create QueryType enum (text/image/hybrid)
  - [ ] Implement MultiModalQueryProcessor
  - [ ] Add query validation and type inference
- [ ] 1.2: Query expansion (5-6h)
  - [ ] Implement text query expansion (visual keywords)
  - [ ] Add image query augmentation (future enhancement)
  - [ ] Create VisualQueryExpander class

**Phase 2: VisionRetriever Implementation (10-14h)**
- [ ] 2.1: Create VisionRetriever class (6-8h)
  - [ ] Implement query() method (unified interface)
  - [ ] Add text-only query execution
  - [ ] Add image-only query execution
  - [ ] Add hybrid query with score fusion
- [ ] 2.2: Visual reranking (4-6h)
  - [ ] Implement VisualReranker class
  - [ ] Add diagram/table content boosting
  - [ ] Add layout complexity filtering
  - [ ] Implement cross-modal relevance scoring

**Phase 3: Integration & Configuration (6-8h)**
- [ ] 3.1: CLI integration (3-4h)
  - [ ] Add query text command
  - [ ] Add query image command
  - [ ] Add query hybrid command
  - [ ] Add interactive query mode (REPL)
- [ ] 3.2: Configuration updates (3-4h)
  - [ ] Add retrieval configuration options
  - [ ] Add weight configuration (text/vision)
  - [ ] Add boosting factor configuration

**Phase 4: Testing (4-6h)**
- [ ] 4.1: Unit tests (2-3h)
  - [ ] Test query type detection
  - [ ] Test text/image/hybrid query execution
  - [ ] Test visual boosting logic
  - [ ] Test reranking algorithms
- [ ] 4.2: Integration tests (2-3h)
  - [ ] Test end-to-end multi-modal retrieval
  - [ ] Test query expansion effectiveness
  - [ ] Test hybrid score fusion accuracy

---

### VISION-004: GPU Management (18-24 hours)

**[Detailed Implementation Plan](./features/VISION-004-gpu-management.md)**

**Phase 1: Device Detection & Selection (4-6h)**
- [ ] 1.1: Device manager implementation (4-6h)
  - [ ] Create DeviceManager class
  - [ ] Implement device detection (CUDA > MPS > CPU)
  - [ ] Add device capability queries
  - [ ] Implement cache clearing utilities

**Phase 2: Memory Monitoring & OOM Handling (6-8h)**
- [ ] 2.1: Memory monitor (3-4h)
  - [ ] Create MemoryMonitor class
  - [ ] Implement memory snapshot tracking
  - [ ] Add threshold-based callbacks
  - [ ] Calculate recommended batch sizes
- [ ] 2.2: OOM recovery (3-4h)
  - [ ] Create OOMHandler class
  - [ ] Implement cache clearing strategy
  - [ ] Implement batch size reduction strategy
  - [ ] Implement CPU fallback strategy

**Phase 3: Adaptive Batch Sizing (4-6h)**
- [ ] 3.1: Batch size calculator (2-3h)
  - [ ] Create AdaptiveBatchSizer class
  - [ ] Implement memory-based calculation
  - [ ] Add adaptive adjustment based on usage
- [ ] 3.2: Integration with ColPali (2-3h)
  - [ ] Update ColPaliEmbedder with GPU management
  - [ ] Add adaptive batching to embed_batch()
  - [ ] Integrate OOM handling

**Phase 4: Testing & Documentation (4-6h)**
- [ ] 4.1: Unit tests (2-3h)
  - [ ] Test device detection on available hardware
  - [ ] Test memory monitoring accuracy
  - [ ] Test OOM recovery strategies
  - [ ] Test batch size calculations
- [ ] 4.2: Integration tests (2-3h)
  - [ ] Test GPU resource management in real workflows
  - [ ] Test OOM recovery with actual models
  - [ ] Test cross-platform compatibility

---

### VISION-005: CLI Commands (16-22 hours)

**[Detailed Implementation Plan](./features/VISION-005-cli-commands.md)**

**Phase 1: Ingestion Commands (5-7h)**
- [ ] 1.1: Enhanced PDF ingestion (3-4h)
  - [ ] Update ingest pdf command with --vision flag
  - [ ] Add --device option for GPU selection
  - [ ] Add --batch-size option
  - [ ] Implement progress indicators
- [ ] 1.2: Testing ingestion commands (2-3h)
  - [ ] Test PDF ingestion with/without vision
  - [ ] Test device selection and fallback
  - [ ] Test error handling

**Phase 2: Query Commands (4-6h)**
- [ ] 2.1: Multi-modal query commands (3-4h)
  - [ ] Implement query text command
  - [ ] Implement query image command
  - [ ] Implement query hybrid command
  - [ ] Add interactive query mode (REPL)
- [ ] 2.2: Testing query commands (1-2h)
  - [ ] Test all query command variants
  - [ ] Test result formatting
  - [ ] Test interactive mode

**Phase 3: GPU & Storage Management (4-6h)**
- [ ] 3.1: GPU management commands (2-3h)
  - [ ] Implement gpu list command
  - [ ] Implement gpu info command
  - [ ] Implement gpu stats command (real-time)
  - [ ] Implement gpu benchmark command
- [ ] 3.2: Storage commands (2-3h)
  - [ ] Implement storage info command
  - [ ] Implement storage migrate command
  - [ ] Add storage vacuum command (stub)

**Phase 4: Testing & Integration (3-4h)**
- [ ] 4.1: CLI integration tests (2-3h)
  - [ ] Test end-to-end CLI workflows
  - [ ] Test all command combinations
  - [ ] Test error messages and help text
- [ ] 4.2: Documentation (1h)
  - [ ] Update CLI help text
  - [ ] Add usage examples to docs

---

### VISION-006: Web UI (24-32 hours)

**[Detailed Implementation Plan](./features/VISION-006-web-ui.md)**

**Phase 1: Core UI Framework (6-8h)**
- [ ] 1.1: Gradio application structure (3-4h)
  - [ ] Create RaggedWebUI class
  - [ ] Build tab structure (Documents, Query, System)
  - [ ] Implement event handlers
- [ ] 1.2: Enhanced results display (3-4h)
  - [ ] Create ResultsRenderer class
  - [ ] Implement rich HTML formatting
  - [ ] Add visual content badges
  - [ ] Add thumbnail placeholders

**Phase 2: Advanced Features (8-10h)**
- [ ] 2.1: Real-time GPU monitoring (4-5h)
  - [ ] Create GPUMonitor class
  - [ ] Add live memory charts
  - [ ] Implement auto-refresh (every 2s)
  - [ ] Add utilisation statistics
- [ ] 2.2: Batch upload & progress tracking (4-5h)
  - [ ] Support multiple PDF uploads
  - [ ] Add progress bar integration
  - [ ] Implement per-file status reporting

**Phase 3: Polish & Testing (8-12h)**
- [ ] 3.1: UI/UX improvements (4-6h)
  - [ ] Add custom CSS styling
  - [ ] Add loading spinners
  - [ ] Improve error message display
  - [ ] Add keyboard shortcuts
  - [ ] Ensure responsive layout
- [ ] 3.2: Testing & documentation (4-6h)
  - [ ] Test UI component rendering
  - [ ] Test event handler logic
  - [ ] Write user guide for web UI
  - [ ] Add screenshots and examples

**Phase 4: Deployment (2-4h)**
- [ ] 4.1: Production configuration (1-2h)
  - [ ] Create UIConfig dataclass
  - [ ] Add authentication support (optional)
  - [ ] Add resource limits
- [ ] 4.2: Docker & deployment guide (1-2h)
  - [ ] Create Dockerfile for web UI
  - [ ] Create docker-compose.yml
  - [ ] Write deployment documentation

---

### Testing (30-40 hours)

**[Detailed Testing Specification](./testing.md)**

- [ ] Create comprehensive test suite (30-40h)
  - [ ] Unit tests for all 6 features (18-24h)
  - [ ] Integration tests (6-8h)
  - [ ] E2E tests (4-6h)
  - [ ] Performance benchmarks (2-4h)

---

## Success Criteria

### Functional Requirements

**VISION-001: ColPali Integration**
- [ ] ColPali model loads successfully on CUDA, MPS, and CPU
- [ ] Vision embeddings generated for PDF pages (768-dim)
- [ ] Batch processing works with adaptive sizing
- [ ] GPU memory monitoring prevents OOM errors
- [ ] Graceful fallback to CPU when GPU unavailable

**VISION-002: Dual Storage**
- [ ] Text embeddings stored with `embedding_type: "text"`
- [ ] Vision embeddings stored with `embedding_type: "vision"`
- [ ] ID format: `{doc}_chunk_{n}_text` and `{doc}_page_{n}_vision`
- [ ] Query methods filter by embedding type correctly
- [ ] Hybrid queries merge results using RRF
- [ ] Migration from v0.4 to v0.5 schema works

**VISION-003: Vision Retrieval**
- [ ] Text-only queries work (existing functionality maintained)
- [ ] Image-only queries return visually similar pages
- [ ] Hybrid queries combine text + vision scores
- [ ] Visual boosting increases scores for diagram/table results
- [ ] Reranker adjusts scores based on visual metadata

**VISION-004: GPU Management**
- [ ] Device detection prioritises: CUDA > MPS > CPU
- [ ] Memory monitor tracks GPU usage accurately
- [ ] OOM handler recovers via: cache clear → batch reduce → CPU fallback
- [ ] Adaptive batch sizing adjusts based on available memory
- [ ] Multi-GPU systems can select specific device

**VISION-005: CLI Commands**
- [ ] `ingest pdf --vision` generates vision embeddings
- [ ] `query text/image/hybrid` commands work
- [ ] `gpu list/info/stats/benchmark` commands work
- [ ] `storage info/migrate` commands work
- [ ] All commands have helpful `--help` text

**VISION-006: Web UI**
- [ ] Document upload works (single and batch)
- [ ] Vision embedding toggle functions
- [ ] Text/image/hybrid queries execute via UI
- [ ] Results display with rich formatting
- [ ] GPU monitoring dashboard shows real-time stats

---

### Quality Requirements

**Test Coverage:**
- [ ] Unit tests: 85%+ coverage for new code
- [ ] Integration tests: All 6 features
- [ ] E2E tests: Complete workflows
- [ ] Performance benchmarks: Meet targets

**Performance Targets:**
- [ ] Vision embedding: <5s per page (GPU), <15s (CPU)
- [ ] Text query latency: <200ms
- [ ] Image query latency: <500ms (including embedding)
- [ ] Hybrid query latency: <600ms
- [ ] GPU memory usage: <8GB for standard documents

**Code Quality:**
- [ ] Type hints on all public methods
- [ ] British English docstrings throughout
- [ ] No linter errors (ruff, mypy --strict)
- [ ] All code follows ragged conventions

**Documentation:**
- [ ] All 6 features have detailed implementation docs
- [ ] CLI commands documented with examples
- [ ] Web UI user guide complete
- [ ] Testing specification comprehensive

---

### Manual Testing Checklist

**Visual Content Understanding:**
- [ ] ⚠️ MANUAL: Test with PDFs containing diagrams
- [ ] ⚠️ MANUAL: Test with PDFs containing tables
- [ ] ⚠️ MANUAL: Test with PDFs containing charts/graphs
- [ ] ⚠️ MANUAL: Verify vision embeddings capture layout

**Multi-Modal Queries:**
- [ ] ⚠️ MANUAL: Query "show documents with flowcharts"
- [ ] ⚠️ MANUAL: Upload diagram image, find similar pages
- [ ] ⚠️ MANUAL: Hybrid query improves precision vs text-only

**Cross-Platform:**
- [ ] ⚠️ MANUAL: Test on NVIDIA GPU (CUDA)
- [ ] ⚠️ MANUAL: Test on Apple Silicon (MPS)
- [ ] ⚠️ MANUAL: Test on CPU-only system

**GPU Resource Management:**
- [ ] ⚠️ MANUAL: Process large PDF batch, monitor GPU memory
- [ ] ⚠️ MANUAL: Trigger OOM intentionally, verify recovery
- [ ] ⚠️ MANUAL: Verify adaptive batch sizing works

---

## Known Risks & Limitations

**Technical:**
- **GPU Requirements:** ColPali model requires 4-8GB VRAM (may exclude some users)
- **Storage Overhead:** Vision embeddings double storage requirements
- **Model Size:** ColPali model is ~1.2GB (slow initial download)
- **Cross-Modal Gap:** Text and vision embeddings in different semantic spaces

**Implementation:**
- **Integration Complexity:** 6 interconnected features increase testing burden
- **Performance Tuning:** Optimal batch sizes may vary by hardware
- **Thumbnail Generation:** Requires PDF rendering (deferred to post-v0.5)

**Dependencies:**
- **PyTorch Required:** Adds ~500MB to installation
- **GPU Drivers:** Users may need to install CUDA/ROCm separately

---

## Deferred to Post-v0.5

**Features Not Included:**
1. **Page Thumbnail Rendering:** Placeholder images only (requires PDF rendering)
2. **Advanced Fusion Methods:** Using learned weights instead of fixed
3. **Cross-Modal Alignment:** Shared text-vision embedding space
4. **Multi-GPU Parallelism:** Single GPU per embedder instance
5. **Model Quantization:** INT8/FP16 for memory efficiency

**Rationale:** Focus on core vision capabilities first, optimise later

---

## Hour Breakdown Summary

| Feature | Hours | Checkboxes |
|---------|-------|------------|
| VISION-001: ColPali | 30-40 | 14 |
| VISION-002: Dual Storage | 25-35 | 16 |
| VISION-003: Vision Retrieval | 28-38 | 16 |
| VISION-004: GPU Management | 18-24 | 13 |
| VISION-005: CLI Commands | 16-22 | 16 |
| VISION-006: Web UI | 24-32 | 13 |
| Testing | 30-40 | 1 (comprehensive) |
| **Total** | **171-231** | **88** |

---

## Next Steps

**After v0.5.0 Completion:**
1. **v0.5.1:** Address deferred items (thumbnail rendering, optimisations)
2. **v0.6.0:** Intelligent optimisation (auto-routing, domain adaptation)

**Prerequisites:**
- v0.4.0 must be complete (knowledge graphs, personal memory)
- GPU testing infrastructure set up
- Test PDFs with rich visual content prepared

---

## Related Documentation

**Implementation Details:**
- [VISION-001: ColPali Integration](./features/VISION-001-colpali-integration.md)
- [VISION-002: Dual Storage](./features/VISION-002-dual-storage.md)
- [VISION-003: Vision Retrieval](./features/VISION-003-vision-retrieval.md)
- [VISION-004: GPU Management](./features/VISION-004-gpu-management.md)
- [VISION-005: CLI Commands](./features/VISION-005-cli-commands.md)
- [VISION-006: Web UI](./features/VISION-006-web-ui.md)
- [Testing Specification](./testing.md)

**Context:**
- [Previous Version](../v0.4/README.md) - Personal memory & knowledge graphs
- [Next Version](../v0.6/README.md) - Intelligent optimisation
- [Planning](../../planning/version/v0.5/) - Design goals for v0.5
- [Version Overview](../README.md) - Complete version comparison

---

**Status:** Planned - Implementation-Ready
