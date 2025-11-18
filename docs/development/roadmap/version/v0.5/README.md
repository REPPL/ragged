# Ragged v0.5.0 Roadmap - ColPali Vision Integration

**Status:** Planned

**Total Hours:** 140-180 hours (AI implementation)

**Focus:** Multi-modal document understanding with vision-based retrieval

**Breaking Changes:** None

---

## Overview

Version 0.5.0 introduces ColPali vision integration for multi-modal document understanding. This enables vision-based retrieval that can understand document layouts, diagrams, tables, and images without relying solely on text extraction.

**Dependencies:** Requires v0.4.0 completion (knowledge graphs and personal memory)

**GPU Requirements:** CUDA-compatible GPU recommended (minimum 8GB VRAM)

---

## VISION-001: ColPali Model Integration (30-40 hours)

**Problem:** Text-only embeddings cannot capture visual layout, diagrams, tables, or images in PDFs.

**Implementation:**
1. Research ColPali architecture and requirements [4 hours]
2. Add ColPali model dependencies (torch, transformers) [2 hours]
3. Implement ColPaliEmbedder in src/embeddings/ [8-10 hours]
4. Add GPU detection and fallback to CPU [4-6 hours]
5. Implement vision patch extraction from PDFs [6-8 hours]
6. Create vision embedding pipeline [6-8 hours]

**Files:** src/embeddings/colpali_embedder.py (new), src/config/settings.py, pyproject.toml

**⚠️ MANUAL TEST:** Test with PDFs containing diagrams, tables, charts - verify embeddings capture visual content

**Success:** ColPali embeddings generated for PDF pages, GPU acceleration works, graceful CPU fallback

---

## VISION-002: Dual Embedding Storage (25-35 hours)

**Problem:** Need to store both text and vision embeddings for hybrid retrieval.

**Implementation:**
1. Extend ChromaDB schema for dual embeddings [6-8 hours]
2. Create VisionVectorStore wrapper [8-10 hours]
3. Implement dual-embedding batch storage [6-8 hours]
4. Add metadata to distinguish embedding types [3-4 hours]
5. Update storage utilities for vision support [2-3 hours]

**Files:** src/storage/vision_vector_store.py (new), src/storage/chroma_store.py

**⚠️ MANUAL TEST:** Store documents with both text and vision embeddings, query both embedding types

**Success:** Documents stored with dual embeddings, retrieval works for both types

---

## VISION-003: Vision-Enhanced Retrieval (30-40 hours)

**Problem:** Need to query using visual similarity in addition to text similarity.

**Implementation:**
1. Create VisionRetriever for image-based queries [8-10 hours]
2. Implement hybrid text+vision retrieval [10-12 hours]
3. Add query mode selection (text-only, vision-only, hybrid) [4-6 hours]
4. Create vision similarity scoring [4-6 hours]
5. Add fusion strategy for text+vision results [4-6 hours]

**Files:** src/retrieval/vision_retriever.py (new), src/retrieval/hybrid.py

**⚠️ MANUAL TEST:** Query with visual questions ("show me documents with charts"), verify vision retrieval works

**Success:** Vision-based queries return visually similar documents, hybrid mode combines text + vision effectively

---

## VISION-004: GPU Memory Management (20-25 hours)

**Problem:** Vision models are memory-intensive and may exhaust GPU memory on large batches.

**Implementation:**
1. Add GPU memory monitoring utilities [4-5 hours]
2. Implement dynamic batch sizing for GPU [6-8 hours]
3. Add GPU memory cache clearing [3-4 hours]
4. Create GPU/CPU offloading strategy [4-5 hours]
5. Add VRAM usage warnings and limits [3-4 hours]

**Files:** src/utils/gpu.py (new), src/embeddings/colpali_embedder.py

**⚠️ MANUAL TEST:** Process large batches on GPU, monitor memory usage stays within limits

**Success:** GPU memory managed efficiently, no OOM errors, automatic batch sizing works

---

## VISION-005: CLI Vision Commands (15-20 hours)

**Problem:** Need CLI interface for vision-based operations.

**Implementation:**
1. Add --vision flag to add command [3-4 hours]
2. Add --retrieval-mode option (text/vision/hybrid) to query [3-4 hours]
3. Create vision diagnostic command (GPU status) [4-5 hours]
4. Add vision-specific configuration options [3-4 hours]
5. Update help documentation [2-3 hours]

**Files:** src/main.py, src/config/settings.py

**⚠️ MANUAL TEST:** Use CLI vision commands, verify all modes work correctly

**Success:** CLI supports vision operations, intuitive flags, clear help text

---

## VISION-006: Web UI Vision Support (20-25 hours)

**Problem:** Web UI needs to support vision-based queries and show visual similarity results.

**Implementation:**
1. Add vision mode toggle to Web UI [4-5 hours]
2. Create visual similarity result cards [6-8 hours]
3. Add page thumbnail preview in results [4-6 hours]
4. Implement vision query examples [3-4 hours]
5. Add GPU status indicator [3-4 hours]

**Files:** src/web/static/, src/web/templates/, src/web/api.py

**⚠️ MANUAL TEST:** Use Web UI with vision mode, verify visual results displayed correctly

**Success:** Web UI supports vision queries, thumbnails displayed, intuitive interface

---

## Success Criteria (Test Checkpoints)

**Automated:**
- [ ] ColPali embeddings generated correctly
- [ ] Dual embeddings stored in vector DB
- [ ] Vision retrieval returns correct results
- [ ] GPU memory managed within limits
- [ ] All existing tests pass

**Manual Testing:**
- [ ] ⚠️ MANUAL: PDFs with diagrams embedded correctly
- [ ] ⚠️ MANUAL: Vision queries return visually similar docs
- [ ] ⚠️ MANUAL: Hybrid mode improves retrieval quality
- [ ] ⚠️ MANUAL: GPU acceleration provides speedup
- [ ] ⚠️ MANUAL: CPU fallback works without GPU

**Quality Gates:**
- [ ] GPU memory usage <8GB for standard workloads
- [ ] Vision embeddings generation time <5 sec/page
- [ ] Retrieval quality improved for visual documents
- [ ] No performance regression for text-only mode
- [ ] Comprehensive documentation for vision features

---

## Known Risks

- ColPali model large (requires significant VRAM)
- Vision embeddings much larger than text embeddings
- GPU availability may be limited for users
- Performance tuning may require experimentation
- Integration complexity higher than text-only

---

## Next Version

After v0.5.0 completion:
- **v0.6.0:** Intelligent optimisation (auto-routing, domain adaptation)
- See: `roadmap/version/v0.6/README.md`

---

**Last Updated:** 2025-11-12

**Status:** Requires v0.4.0 completion first

---

## Related Documentation

- [Previous Version](../v0.4/README.md) - Personal memory & knowledge graphs
- [Next Version](../v0.6/README.md) - Intelligent optimisation
- [Planning](../../planning/version/v0.5/) - Design goals for v0.5
- [Version Overview](../README.md) - Complete version comparison

---
