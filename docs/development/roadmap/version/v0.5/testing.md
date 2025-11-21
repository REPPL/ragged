# v0.5.0 Testing Specification

**Version:** v0.5.0 - Multi-Modal Vision RAG
**Status:** Planned
**Estimated Effort:** 30-40 hours

---

## Overview

Comprehensive testing strategy for v0.5's multi-modal vision capabilities. This document consolidates test requirements from all VISION features and defines quality gates for production readiness.

**Testing Objectives:**
1. **Functional Correctness:** All features work as specified
2. **Cross-Device Compatibility:** Works on CUDA, MPS, and CPU
3. **Performance Targets:** Meet latency and throughput requirements
4. **Failure Recovery:** Graceful handling of OOM, GPU unavailable, invalid inputs
5. **Integration Stability:** Components work together seamlessly

---

## Test Structure

```
tests/
├── unit/                          # Fast, isolated tests
│   ├── embeddings/
│   │   ├── test_colpali.py       # ColPali embedder (VISION-001)
│   │   └── test_batch_processing.py
│   ├── storage/
│   │   ├── test_dual_store.py    # Dual embedding storage (VISION-002)
│   │   ├── test_schema.py
│   │   └── test_migration.py
│   ├── retrieval/
│   │   ├── test_query_processor.py   # Multi-modal queries (VISION-003)
│   │   ├── test_vision_retriever.py
│   │   └── test_reranker.py
│   ├── gpu/
│   │   ├── test_device_manager.py    # GPU management (VISION-004)
│   │   ├── test_memory_monitor.py
│   │   └── test_oom_handler.py
│   └── cli/
│       ├── test_ingest_commands.py   # CLI (VISION-005)
│       └── test_query_commands.py
│
├── integration/                   # Component interaction tests
│   ├── test_dual_ingestion.py    # Text + vision ingestion
│   ├── test_hybrid_retrieval.py  # Multi-modal queries
│   ├── test_gpu_fallback.py      # Device fallback scenarios
│   └── test_cli_workflow.py      # End-to-end CLI usage
│
├── e2e/                          # End-to-end workflows
│   ├── test_document_lifecycle.py # Upload → query → delete
│   ├── test_multi_modal_search.py # Full search scenarios
│   └── test_web_ui.py            # Web UI workflows (VISION-006)
│
├── performance/                   # Performance benchmarks
│   ├── test_embedding_speed.py
│   ├── test_query_latency.py
│   └── test_memory_usage.py
│
└── compatibility/                 # Cross-platform tests
    ├── test_cuda_devices.py
    ├── test_mps_devices.py
    └── test_cpu_fallback.py
```

---

## Test Coverage by Feature

### VISION-001: ColPali Integration (10-12 hours)

**Unit Tests (6-7h):**

```python
# tests/unit/embeddings/test_colpali.py

class TestColPaliEmbedder:
    """Test ColPali vision embedder."""

    def test_model_initialization_cpu(self):
        """Test model loads successfully on CPU."""
        embedder = ColPaliEmbedder(device="cpu")
        assert embedder.device_info.device_type == DeviceType.CPU

    @pytest.mark.skipif(not torch.cuda.is_available(), reason="Requires CUDA")
    def test_model_initialization_cuda(self):
        """Test model loads on CUDA device."""
        embedder = ColPaliEmbedder(device="cuda")
        assert embedder.device_info.device_type == DeviceType.CUDA

    def test_single_page_embedding(self):
        """Test embedding generation for single page."""
        embedder = ColPaliEmbedder(device="cpu")
        test_image = Image.new("RGB", (800, 1200), color=(255, 255, 255))

        embedding = embedder.embed_page(test_image)

        assert embedding.shape == (768,)
        assert embedding.dtype == np.float32

    def test_batch_embedding(self):
        """Test batch embedding generation."""
        embedder = ColPaliEmbedder(device="cpu", batch_size=4)
        test_images = [
            Image.new("RGB", (800, 1200), color=(i * 50, i * 50, i * 50))
            for i in range(10)
        ]

        embeddings = embedder.embed_batch(test_images)

        assert embeddings.shape == (10, 768)

    def test_pdf_document_embedding(self, sample_pdf):
        """Test full PDF document embedding."""
        embedder = ColPaliEmbedder(device="cpu")

        embeddings, page_numbers = embedder.embed_document(sample_pdf)

        assert len(embeddings) == len(page_numbers)
        assert embeddings.shape[1] == 768
        assert all(isinstance(p, int) for p in page_numbers)

    def test_invalid_device_handling(self):
        """Test error handling for invalid device."""
        with pytest.raises(RuntimeError):
            ColPaliEmbedder(device="cuda:99")  # Non-existent GPU

    def test_memory_cleanup(self):
        """Test model is properly unloaded."""
        embedder = ColPaliEmbedder(device="cpu")
        embedder.unload_model()

        assert embedder.model is None
```

**Integration Tests (4-5h):**

```python
# tests/integration/test_colpali_integration.py

class TestColPaliIntegration:
    """Integration tests for ColPali with ingestion pipeline."""

    def test_integration_with_ingestion_pipeline(self, sample_pdf):
        """Test ColPali integrated with document ingestion."""
        embedder = ColPaliEmbedder(device="cpu")
        processor = DocumentProcessor(vision_embedder=embedder)

        doc_id = processor.process_document(sample_pdf, enable_vision=True)

        assert doc_id is not None

    @pytest.mark.skipif(not torch.cuda.is_available(), reason="Requires GPU")
    def test_gpu_memory_usage(self, sample_pdf):
        """Test GPU memory usage stays within bounds."""
        embedder = ColPaliEmbedder(device="cuda")

        # Monitor memory before and after
        memory_before = torch.cuda.memory_allocated()

        embeddings, _ = embedder.embed_document(sample_pdf)

        memory_after = torch.cuda.memory_allocated()
        memory_used_mb = (memory_after - memory_before) / (1024**2)

        assert memory_used_mb < 4000  # Should use less than 4GB
```

---

### VISION-002: Dual Storage (8-10 hours)

**Unit Tests (5-6h):**

```python
# tests/unit/storage/test_dual_store.py

class TestDualEmbeddingStore:
    """Test dual text+vision storage."""

    def test_add_text_embedding(self):
        """Test adding text embedding."""
        store = DualEmbeddingStore(collection_name="test")
        embedding = np.random.rand(384)

        embedding_id = store.add_text_embedding(
            document_id="doc1",
            chunk_id="chunk1",
            chunk_index=0,
            embedding=embedding,
            text_content="Test content"
        )

        assert embedding_id == "doc1_chunk_0_text"

    def test_add_vision_embedding(self):
        """Test adding vision embedding."""
        store = DualEmbeddingStore(collection_name="test")
        embedding = np.random.rand(768)

        embedding_id = store.add_vision_embedding(
            document_id="doc1",
            page_number=1,
            embedding=embedding,
            image_hash="abc123"
        )

        assert embedding_id == "doc1_page_1_vision"

    def test_query_text_only(self):
        """Test text-only query filters correctly."""
        store = DualEmbeddingStore(collection_name="test")

        # Add mixed embeddings
        store.add_text_embedding("doc1", "c1", 0, np.random.rand(384), "text")
        store.add_vision_embedding("doc1", 1, np.random.rand(768), "hash")

        # Query text
        results = store.query_text(np.random.rand(384), n_results=10)

        # Should only return text embeddings
        assert all(
            m["embedding_type"] == "text"
            for m in results["metadatas"][0]
        )

    def test_dimension_validation(self):
        """Test embedding dimension validation."""
        store = DualEmbeddingStore(collection_name="test")

        # Wrong dimension for text
        with pytest.raises(ValueError, match="384-dimensional"):
            store.add_text_embedding(
                "doc1", "c1", 0, np.random.rand(768), "text"
            )

        # Wrong dimension for vision
        with pytest.raises(ValueError, match="768-dimensional"):
            store.add_vision_embedding(
                "doc1", 1, np.random.rand(384), "hash"
            )

    def test_hybrid_query_fusion(self):
        """Test hybrid query merges text and vision results."""
        store = DualEmbeddingStore(collection_name="test")

        # Add embeddings
        for i in range(5):
            store.add_text_embedding(f"doc{i}", f"c{i}", i, np.random.rand(384), f"text {i}")
            store.add_vision_embedding(f"doc{i}", i + 1, np.random.rand(768), f"hash{i}")

        # Hybrid query
        results = store.query_hybrid(
            text_embedding=np.random.rand(384),
            vision_embedding=np.random.rand(768),
            n_results=5,
            text_weight=0.6,
            vision_weight=0.4
        )

        # Should have results from both types
        assert len(results["ids"][0]) <= 5
```

**Migration Tests (3-4h):**

```python
# tests/unit/storage/test_migration.py

class TestStorageMigration:
    """Test v0.4 to v0.5 schema migration."""

    def test_schema_version_detection(self):
        """Test detection of schema version."""
        migration = StorageMigration(chromadb.Client())

        # Create v0.4 collection (no embedding_type metadata)
        # ... setup code ...

        version = migration.detect_schema_version("test_collection")
        assert version == "v0.4"

    def test_migration_dry_run(self):
        """Test migration preview without applying changes."""
        migration = StorageMigration(chromadb.Client())

        # Create v0.4 collection
        # ... setup code ...

        stats = migration.migrate_collection(
            "test_collection",
            dry_run=True
        )

        assert stats["embeddings_migrated"] > 0
        assert stats["ids_renamed"] > 0

        # Verify no actual changes
        version = migration.detect_schema_version("test_collection")
        assert version == "v0.4"  # Still v0.4

    def test_migration_execution(self):
        """Test actual migration execution."""
        migration = StorageMigration(chromadb.Client())

        # Create v0.4 collection
        # ... setup code ...

        stats = migration.migrate_collection("test_collection", dry_run=False)

        # Verify migration
        version = migration.detect_schema_version("test_collection")
        assert version == "v0.5"

        # Check metadata updated
        # ... verification code ...
```

---

### VISION-003: Vision Retrieval (6-8 hours)

**Unit Tests (4-5h):**

```python
# tests/unit/retrieval/test_vision_retriever.py

class TestVisionRetriever:
    """Test multi-modal retrieval."""

    def test_text_query(self):
        """Test text-only query execution."""
        retriever = VisionRetriever()

        response = retriever.query(text="test query", n_results=5)

        assert response.query_type == QueryType.TEXT_ONLY
        assert len(response.results) <= 5

    @pytest.mark.skipif(not torch.cuda.is_available(), reason="Requires GPU")
    def test_image_query(self, sample_image):
        """Test image-only query execution."""
        retriever = VisionRetriever()

        response = retriever.query(image=sample_image, n_results=5)

        assert response.query_type == QueryType.IMAGE_ONLY
        assert all(r.embedding_type == "vision" for r in response.results)

    def test_hybrid_query(self, sample_image):
        """Test hybrid text+image query."""
        retriever = VisionRetriever()

        response = retriever.query(
            text="test query",
            image=sample_image,
            n_results=5,
            text_weight=0.6,
            vision_weight=0.4
        )

        assert response.query_type == QueryType.HYBRID

    def test_visual_boosting(self):
        """Test diagram/table boosting."""
        retriever = VisionRetriever()

        # Add documents with/without diagrams
        # ... setup code ...

        response_no_boost = retriever.query(
            text="architecture",
            n_results=10,
            boost_diagrams=False
        )

        response_with_boost = retriever.query(
            text="architecture",
            n_results=10,
            boost_diagrams=True
        )

        # Results with diagrams should rank higher when boosted
        # ... assertions ...
```

**Integration Tests (2-3h):**

```python
# tests/integration/test_hybrid_retrieval.py

class TestHybridRetrievalIntegration:
    """Integration tests for multi-modal retrieval."""

    def test_end_to_end_hybrid_workflow(self, sample_pdfs):
        """Test complete hybrid retrieval workflow."""
        # Ingest documents with vision
        processor = DocumentProcessor(
            vision_embedder=ColPaliEmbedder(device="cpu")
        )

        for pdf in sample_pdfs:
            processor.process_document(pdf, enable_vision=True)

        # Query with text and image
        retriever = VisionRetriever()

        response = retriever.query(
            text="database architecture",
            image=create_test_diagram(),
            n_results=10
        )

        assert len(response.results) > 0
```

---

### VISION-004: GPU Management (6-8 hours)

**Unit Tests (4-5h):**

```python
# tests/unit/gpu/test_device_manager.py

class TestDeviceManager:
    """Test GPU device management."""

    def test_device_detection(self):
        """Test automatic device detection."""
        manager = DeviceManager()

        assert len(manager._available_devices) > 0

        # Should have at least CPU
        device_types = [d.device_type for d in manager._available_devices]
        assert DeviceType.CPU in device_types

    def test_optimal_device_selection(self):
        """Test optimal device selection logic."""
        manager = DeviceManager()

        # Auto-select
        device = manager.get_optimal_device()
        assert device is not None

        # Explicit CPU
        cpu_device = manager.get_optimal_device(device_hint="cpu")
        assert cpu_device.device_type == DeviceType.CPU

    @pytest.mark.skipif(not torch.cuda.is_available(), reason="Requires CUDA")
    def test_memory_query(self):
        """Test GPU memory information retrieval."""
        manager = DeviceManager()
        cuda_device = manager.get_optimal_device(device_hint="cuda")

        memory_info = manager.get_device_memory_info(cuda_device)

        assert memory_info["total"] > 0
        assert memory_info["free"] <= memory_info["total"]

    @pytest.mark.skipif(not torch.cuda.is_available(), reason="Requires CUDA")
    def test_cache_clearing(self):
        """Test GPU cache clearing."""
        manager = DeviceManager()
        device = manager.get_optimal_device(device_hint="cuda")

        # Allocate some memory
        dummy_tensor = torch.zeros((1000, 1000), device="cuda")

        # Clear cache
        manager.clear_cache(device)

        # Memory should be freed
        del dummy_tensor
        torch.cuda.empty_cache()
```

**OOM Handling Tests (2-3h):**

```python
# tests/unit/gpu/test_oom_handler.py

class TestOOMHandler:
    """Test out-of-memory error handling."""

    @pytest.mark.skipif(not torch.cuda.is_available(), reason="Requires GPU")
    def test_cache_clearing_strategy(self):
        """Test OOM recovery via cache clearing."""
        handler = OOMHandler(DeviceManager())

        # Simulate OOM condition
        # ... test code ...

    @pytest.mark.skipif(not torch.cuda.is_available(), reason="Requires GPU")
    def test_cpu_fallback_strategy(self):
        """Test fallback to CPU on persistent OOM."""
        handler = OOMHandler(DeviceManager(), enable_cpu_fallback=True)

        # Force OOM and verify CPU fallback
        # ... test code ...
```

---

### VISION-005: CLI Commands (5-7 hours)

**Unit Tests (3-4h):**

```python
# tests/unit/cli/test_ingest_commands.py

class TestIngestCommands:
    """Test CLI ingestion commands."""

    def test_pdf_ingestion_text_only(self, cli_runner, sample_pdf):
        """Test PDF ingestion without vision."""
        result = cli_runner.invoke(
            ingest,
            ["pdf", str(sample_pdf)]
        )

        assert result.exit_code == 0
        assert "ingested" in result.output.lower()

    @pytest.mark.skipif(not torch.cuda.is_available(), reason="Requires GPU")
    def test_pdf_ingestion_with_vision(self, cli_runner, sample_pdf):
        """Test PDF ingestion with vision embeddings."""
        result = cli_runner.invoke(
            ingest,
            ["pdf", str(sample_pdf), "--vision", "--device", "cuda"]
        )

        assert result.exit_code == 0

    def test_batch_ingestion(self, cli_runner, pdf_directory):
        """Test batch PDF ingestion."""
        result = cli_runner.invoke(
            ingest,
            ["batch", str(pdf_directory), "--pattern", "*.pdf"]
        )

        assert result.exit_code == 0
```

**Integration Tests (2-3h):**

```python
# tests/integration/test_cli_workflow.py

class TestCLIWorkflow:
    """Integration tests for CLI workflows."""

    def test_complete_ingest_query_workflow(self, cli_runner, sample_pdf):
        """Test full ingest → query workflow via CLI."""
        # Ingest
        ingest_result = cli_runner.invoke(
            ingest,
            ["pdf", str(sample_pdf), "--vision"]
        )
        assert ingest_result.exit_code == 0

        # Query text
        query_result = cli_runner.invoke(
            query,
            ["text", "test query"]
        )
        assert query_result.exit_code == 0
        assert "results" in query_result.output.lower()
```

---

### VISION-006: Web UI (5-7 hours)

**UI Tests (3-4h):**

```python
# tests/e2e/test_web_ui.py

class TestWebUI:
    """End-to-end tests for web UI."""

    def test_ui_launches_successfully(self):
        """Test web UI launches without errors."""
        ui = RaggedWebUI(enable_vision=False)  # CPU mode for testing

        app = ui.build_interface()

        assert app is not None

    def test_document_upload_handler(self, sample_pdf):
        """Test document upload event handler."""
        ui = RaggedWebUI(enable_vision=False)

        status, doc_list = ui.handle_document_upload(
            pdf_path=str(sample_pdf),
            enable_vision=False
        )

        assert "ingested" in status.lower()
        assert len(doc_list) > 0

    def test_query_handler(self):
        """Test query event handler."""
        ui = RaggedWebUI(enable_vision=False)

        # Add some documents first
        # ... setup code ...

        html_results = ui.handle_query(
            text="test query",
            image_path=None,
            num_results=10,
            text_weight=0.5,
            vision_weight=0.5,
            boost_diagrams=False,
            boost_tables=False
        )

        assert isinstance(html_results, str)
        assert len(html_results) > 0
```

**Component Tests (2-3h):**

```python
# tests/unit/ui/test_results_renderer.py

class TestResultsRenderer:
    """Test results rendering."""

    def test_html_result_formatting(self):
        """Test HTML formatting of results."""
        renderer = ResultsRenderer()

        # Create mock results
        results = [
            RetrievalResult(
                document_id="doc1",
                embedding_id="doc1_chunk_0_text",
                score=0.95,
                embedding_type="text",
                metadata={"text_content": "Sample text"},
                rank=1
            )
        ]

        html = renderer.render_results_html(
            results=results,
            total_results=1,
            execution_time_ms=50.0
        )

        assert "doc1" in html
        assert "0.95" in html
        assert "Sample text" in html
```

---

## Performance Benchmarks

**Target Metrics:**

```python
# tests/performance/test_performance.py

class TestPerformance:
    """Performance benchmark tests."""

    @pytest.mark.benchmark
    @pytest.mark.skipif(not torch.cuda.is_available(), reason="GPU required")
    def test_vision_embedding_throughput(self, benchmark):
        """Benchmark vision embedding generation speed."""
        embedder = ColPaliEmbedder(device="cuda")
        test_images = [
            Image.new("RGB", (800, 1200), color=(i * 10, i * 10, i * 10))
            for i in range(20)
        ]

        result = benchmark(embedder.embed_batch, test_images)

        # Target: >10 images/second on modern GPU
        assert benchmark.stats["mean"] < 2.0  # <2s for 20 images

    @pytest.mark.benchmark
    def test_query_latency(self, benchmark):
        """Benchmark query execution latency."""
        retriever = VisionRetriever()

        result = benchmark(
            retriever.query,
            text="test query",
            n_results=10
        )

        # Target: <200ms for text query
        assert benchmark.stats["mean"] < 0.2
```

---

## Test Execution Strategy

### Local Development

```bash
# Run all tests
pytest

# Run unit tests only (fast)
pytest tests/unit/

# Run with coverage
pytest --cov=ragged --cov-report=html

# Run specific feature tests
pytest tests/unit/embeddings/  # VISION-001
pytest tests/unit/storage/     # VISION-002

# Run GPU tests (requires GPU)
pytest -m gpu

# Run performance benchmarks
pytest -m benchmark
```

### CI/CD Pipeline

```yaml
# .github/workflows/test.yml

name: Test Suite

on: [push, pull_request]

jobs:
  test-cpu:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run CPU tests
        run: pytest tests/unit/ tests/integration/ -m "not gpu"

  test-cuda:
    runs-on: ubuntu-gpu  # Self-hosted GPU runner
    steps:
      - uses: actions/checkout@v3
      - name: Run GPU tests
        run: pytest -m gpu
```

---

## Quality Gates

**Pre-Merge Requirements:**
- [ ] All unit tests pass (100%)
- [ ] Integration tests pass (95%+)
- [ ] Test coverage ≥85% for new code
- [ ] No performance regressions >10%
- [ ] All linter checks pass (ruff, mypy)
- [ ] British English compliance (automated check)

**Pre-Release Requirements:**
- [ ] All E2E tests pass on: CUDA, MPS, CPU
- [ ] Performance benchmarks meet targets
- [ ] Manual testing on production-like data
- [ ] Security audit passed
- [ ] Documentation complete and verified

---

## Test Data Management

**Test Fixtures:**
```
tests/fixtures/
├── pdfs/
│   ├── sample_text_only.pdf       # Pure text PDF
│   ├── sample_with_diagrams.pdf   # Contains diagrams/charts
│   ├── sample_with_tables.pdf     # Contains tables
│   ├── sample_complex_layout.pdf  # Complex multi-column
│   └── sample_multilingual.pdf    # Mixed language content
│
└── images/
    ├── diagram_sketch.png         # Hand-drawn diagram
    ├── flowchart.png              # Software flowchart
    └── architecture_diagram.png   # System architecture
```

**Fixture Management:**
```python
# tests/conftest.py

@pytest.fixture
def sample_pdf():
    """Provide sample PDF for testing."""
    return Path(__file__).parent / "fixtures" / "pdfs" / "sample_text_only.pdf"

@pytest.fixture
def sample_image():
    """Provide sample image for testing."""
    return Path(__file__).parent / "fixtures" / "images" / "diagram_sketch.png"
```

---

## Known Testing Challenges

1. **GPU Availability:** Many tests require GPU, may skip in CI
2. **Model Download:** ColPali model is ~1.2GB, slow initial test run
3. **Determinism:** Vision embeddings may vary slightly between runs
4. **Test Data Size:** Full PDF fixtures can be large, use Git LFS

---

## Related Documentation

- [VISION-001: ColPali Integration](./features/VISION-001-colpali-integration.md)
- [VISION-002: Dual Storage](./features/VISION-002-dual-storage.md)
- [VISION-003: Vision Retrieval](./features/VISION-003-vision-retrieval.md)
- [VISION-004: GPU Management](./features/VISION-004-gpu-management.md)
- [VISION-005: CLI Commands](./features/VISION-005-cli-commands.md)
- [VISION-006: Web UI](./features/VISION-006-web-ui.md)

---

**Status:** Planned
**Estimated Total Effort:** 30-40 hours
