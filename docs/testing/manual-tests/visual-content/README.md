# Visual Content Tests

**Purpose:** Validate PDF ingestion and vision embedding functionality

**Last Updated:** 2025-11-23

---

## Overview

These tests validate ragged's ability to ingest PDFs with visual content analysis using ColPali vision embeddings. Visual embeddings enable multi-modal retrieval where users can query based on diagrams, charts, tables, and other visual elements in documents.

---

## Test Scenarios

### VC-01: Basic PDF Ingestion
**File:** [VC-01-basic-pdf-ingestion.md](./VC-01-basic-pdf-ingestion.md)

**Purpose:** Validate single PDF ingestion with vision embeddings

**Key Validations:**
- ColPali model download (first-time setup)
- Vision embedding generation
- Dual storage (text + vision) verification
- Basic ingestion workflow

**Status:** In progress - ColPali model downloading

**Note:** Initial execution reveals ColPali model download can take 10-30 minutes depending on connection speed. This is a one-time setup cost.

---

### VC-02: Batch Ingestion
**File:** [VC-02-batch-ingestion.md](./VC-02-batch-ingestion.md)

**Purpose:** Validate multiple PDF ingestion in single command

**Key Validations:**
- Batch processing efficiency
- Consistent embedding quality across documents
- Progress reporting for multiple files

**Status:** Not yet executed (depends on VC-01)

---

### VC-03: Visual Content Verification
**File:** [VC-03-visual-verification.md](./VC-03-visual-verification.md)

**Purpose:** Verify vision embeddings capture visual content accurately

**Key Validations:**
- Embeddings reflect visual content (diagrams, charts)
- Storage separation between text and vision
- Embedding dimensions correct

**Status:** Planned

---

### VC-04: Storage Backend Validation
**File:** [VC-04-storage-backend.md](./VC-04-storage-backend.md)

**Purpose:** Validate dual storage architecture (text + vision)

**Key Validations:**
- Separate collections for text/vision
- Storage info command accuracy
- Migration and backup compatibility

**Status:** Planned

---

## Prerequisites

### System Requirements
- **Python:** 3.12
- **ChromaDB:** Running via Docker or local
- **Ollama:** Local with nomic-embed-text model
- **GPU/MPS:** Apple Silicon (MPS) or CUDA GPU recommended for vision embeddings
- **Disk Space:** ~5GB for ColPali model (first-time download)

### Sample Data
All tests use PDFs from `examples/sample_documents/`:
- `data_visualization.pdf` (220KB, 9 pages) - Charts and graphs
- `machine_learning_survey.pdf` (576KB, 6 pages) - Technical diagrams
- `neural_networks.pdf` (1.0MB, 5 pages) - Architecture diagrams

---

## Execution Order

Tests should be run in order:

1. **VC-01** - Establishes baseline, downloads ColPali model
2. **VC-02** - Validates batch processing (model already cached)
3. **VC-03** - Verifies embedding quality
4. **VC-04** - Validates storage architecture

---

## Common Issues

### Issue: ColPali Model Download Slow
**Symptom:** Ingestion hangs after "Quality: 95% (Excellent)"

**Cause:** First-time ColPali model download (vidore/colpali-v1.3-hf) from HuggingFace

**Solution:** Wait for download to complete (10-30 min). Model is cached for future use.

**Verification:**
```bash
ls ~/.cache/huggingface/hub/ | grep colpali
```

---

### Issue: Out of Memory on CPU
**Symptom:** Process killed during vision embedding

**Cause:** ColPali requires significant memory (~8GB recommended)

**Solution:**
- Use GPU/MPS if available
- Reduce batch size: `--vision-batch-size 1`
- Close other applications

---

### Issue: ChromaDB Connection Failed
**Symptom:** "Connection refused" error

**Cause:** ChromaDB not running

**Solution:**
```bash
docker-compose up -d chromadb
# Wait for healthy status
docker-compose ps chromadb
```

---

## Performance Expectations

### First Execution (with model download):
- **Setup Time:** 10-30 minutes (ColPali download)
- **Per-Page Processing:** 2-5 seconds (vision embeddings)
- **9-Page PDF:** ~1-2 minutes (after model downloaded)

### Subsequent Executions (model cached):
- **Setup Time:** None
- **Per-Page Processing:** 2-5 seconds
- **9-Page PDF:** ~1-2 minutes

### Batch Processing (3 PDFs, 20 pages total):
- **Expected Time:** 3-5 minutes (model cached)
- **Parallel Processing:** Not currently implemented
- **Sequential:** Each PDF processed individually

---

## Success Criteria

For visual content tests to pass:

- [ ] ColPali model downloads successfully
- [ ] Vision embeddings generated for all PDF pages
- [ ] Dual storage (text + vision) verified via `storage info`
- [ ] No errors during ingestion
- [ ] Reasonable processing time (<5 min per PDF excluding first-time setup)
- [ ] Storage counts match expectations (text + vision embeddings)

---

## Related Documentation

- [Multi-Modal Workflow Tutorial](../../../tutorials/multimodal-workflow.md)
- [Storage Management Guide](../../../guides/storage-management.md)
- [GPU Configuration Guide](../../../guides/gpu-configuration-optimisation.md)
- [Manual Testing README](../README.md)

---

## Test Execution Log

| Test | Date | Status | Duration | Notes |
|------|------|--------|----------|-------|
| VC-01 | 2025-11-23 | In Progress | ~5min+ | ColPali downloading |
| VC-02 | - | Pending | - | Awaits VC-01 |
| VC-03 | - | Pending | - | Awaits VC-01 |
| VC-04 | - | Pending | - | Awaits VC-01 |
