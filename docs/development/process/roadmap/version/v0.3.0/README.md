# ragged v0.3.0 Roadmap

**Version:** v0.3.0

**Status:** Planned

**Target:** Q2-Q3 2026

**Last Updated:** 2025-11-15

---

## Overview

Version 0.3.0 represents a major evolution of ragged, focusing on **advanced retrieval techniques**, **multi-modal support**, and **quality evaluation**. This version transforms ragged from a functional RAG system into a **production-ready, state-of-the-art** document intelligence platform.

### Key Themes

1. **Advanced Retrieval** - Hybrid search, reranking, query expansion
2. **Intelligent Chunking** - Semantic, agentic, and proposition-based strategies  
3. **Multi-Modal** - Images, tables, PDFs with complex layouts
4. **Quality & Evaluation** - Metrics, benchmarking, observability
5. **Data Management** - Versioning, metadata, auto-tagging
6. **Enhanced Generation** - Chain-of-thought, better citations
7. **CLI Enhancements** - Interactive mode, automation, developer tools

### Total Effort Estimate

**234-260 hours** across 7 feature areas

**Timeline:** ~6-8 months with single developer

---

## Feature Areas

### [Part 1: Advanced Query Processing & Retrieval](./features/query-processing.md)

**Effort:** 41 hours

**Features:**
- FEAT-001: Hybrid Search (BM25 + Dense)
- FEAT-002: Reranking (Cross-Encoder)
- FEAT-003: Query Expansion & Rewrites
- FEAT-004: Multi-Query Retrieval
- FEAT-005: Parent-Child Document Retrieval

### [Part 2: Advanced Chunking Strategies](./features/chunking-strategies.md)

**Effort:** 28 hours

**Features:**
- FEAT-006: Semantic Chunking
- FEAT-007: Agentic Chunking
- FEAT-008: Proposition-Based Chunking
- FEAT-009: Dynamic Chunk Sizing

### [Part 3: Multi-Modal Support](./features/multi-modal-support.md)

**Effort:** 35 hours

**Features:**
- FEAT-010: Advanced Multi-Modal (Images, Tables, Charts)

### [Part 4: Evaluation & Quality](./features/evaluation-quality.md)

**Effort:** 24 hours

**Features:**
- Comprehensive evaluation framework
- Retrieval metrics (MRR, NDCG, Recall@k)
- Generation metrics (BLEU, ROUGE, RAGAS)
- Benchmarking suite
- Observability and tracing

### [Part 5-6: Data Management & Generation](./features/data-generation.md)

**Effort:** 54 hours combined

**Data Management Features:**
- FEAT-011: Document Version Tracking
- FEAT-012: Metadata Filtering & Faceted Search
- FEAT-013: Auto-Tagging & Classification

**Generation Features:**
- FEAT-014: Chain-of-Thought Reasoning
- FEAT-015: Enhanced Citations

### [Part 7: Advanced CLI Features](./features/cli-features.md)

**Effort:** 52-71 hours

**Features:** 11 advanced CLI capabilities

**Related:** [CLI Enhancements Catalogue](../../../UI/cli/enhancements.md)

---

## Implementation Recommendations

### Recommended Order

**Phase 1 (Foundation):** Evaluation & Quality
- Build metrics and benchmarking first
- Enables data-driven decisions for all other features
- **Effort:** 24 hours

**Phase 2 (Core Retrieval):** Advanced Query Processing
- Hybrid search and reranking provide biggest quality wins
- Foundation for other retrieval techniques
- **Effort:** 41 hours

**Phase 3 (Intelligence):** Advanced Chunking
- Semantic and agentic chunking improve retrieval quality
- Benefits all downstream features
- **Effort:** 28 hours

**Phase 4 (Capabilities):** Multi-Modal Support
- Unlocks new document types
- High user value
- **Effort:** 35 hours

**Phase 5 (Production):** Data Management & Generation
- Production-readiness features
- Enhanced citations and metadata
- **Effort:** 54 hours

**Phase 6 (UX):** CLI Enhancements
- Developer productivity and automation
- Can be implemented in parallel
- **Effort:** 52-71 hours

### Parallelisation Opportunities

These feature sets can be developed in parallel by different developers:
- **Track A:** Evaluation → Retrieval → Chunking
- **Track B:** Multi-Modal → Data Management  
- **Track C:** CLI Enhancements (independent)

### Dependencies

```
Evaluation & Quality (no dependencies)
    ↓
Advanced Retrieval ← Advanced Chunking
    ↓
Multi-Modal Support
    ↓
Data Management & Generation
    ↓
CLI Enhancements (can run in parallel)
```

---

## Version Comparison

| Feature Area | v0.1 | v0.2 | v0.3 |
|--------------|------|------|------|
| **Retrieval** | Basic dense | Dense + normalisation | Hybrid + reranking |
| **Chunking** | Recursive splitter | + Overlap optimization | + Semantic/agentic |
| **Documents** | PDF, TXT, MD | + Metadata extraction | + Multi-modal (images) |
| **Evaluation** | Manual testing | Basic metrics | Comprehensive suite |
| **CLI** | Basic commands | Enhanced output | Interactive + automation |
| **Generation** | Basic citations | - | Chain-of-thought |

---

## Success Criteria

### Performance Targets

- **Retrieval Quality:** MRR@10 > 0.75 (vs 0.60 in v0.2)
- **Answer Quality:** RAGAS score > 0.80 (vs 0.70 in v0.2)
- **Multi-Modal:** Successfully extract text + images from 95% of PDFs
- **Throughput:** Process 1000 pages/minute on Mac Studio M4 Max

### User Experience

- Interactive mode enables exploratory workflows
- Evaluation results provide actionable insights
- Multi-modal support handles real-world documents
- CLI automation enables CI/CD integration

---

## Risk Assessment

### High Risk

- **Multi-modal complexity:** OCR quality varies significantly across documents
- **Semantic chunking performance:** May be slow on large corpora
- **Reranker latency:** Cross-encoders are slower than dense retrieval

### Medium Risk

- **Evaluation dataset quality:** Good benchmarks require manual curation
- **CLI backwards compatibility:** New features must not break existing workflows

### Low Risk

- **Hybrid search:** Well-established technique with proven libraries
- **Query expansion:** Mature NLP techniques available

---

## Post-v0.3.0

Features deferred to v0.4.0 and beyond:

**v0.4.0 - Knowledge Graphs:**
- Graph-based retrieval
- Entity extraction and linking
- Relationship mapping

**v0.5.0 - Advanced Memory:**
- Personal memory and context
- User personas
- Conversation history

**v1.0.0 - Production Release:**
- Web UI
- Multi-user support
- API server
- Performance monitoring

---

## Related Documentation

- [v0.1 Roadmap](../v0.1/) - MVP implementation  
- [v0.2 Roadmap](../v0.2/) - Enhanced retrieval
- [CLI Enhancements Catalogue](../../../UI/cli/enhancements.md) - Detailed CLI specs
- [Architecture](../../../architecture/) - System architecture

---

**Maintained By:** ragged development team

**License:** GPL-3.0
