# ragged v0.3 Design Overview


**Status:** 📋 Planned (Q2-Q3 2026)

---

## Overview

Version 0.3 transforms ragged from a functional RAG system into a production-ready, state-of-the-art document intelligence platform. The focus is on quality, evaluation, and advanced retrieval techniques.

**Goal**: Achieve production-ready quality with comprehensive evaluation, advanced retrieval, and multi-modal support.

**For detailed implementation plans, see:**
- [Roadmap: v0.3.0](../../../roadmap/version/v0.3.0/) - Detailed feature specifications (234-260 hours)

---

## Design Goals

### 1. Quality Through Measurement
**Problem**: No objective way to measure retrieval and generation quality.

**Solution**:
- Comprehensive evaluation framework with standard metrics
- Retrieval metrics: MRR, NDCG, Recall@k
- Generation metrics: BLEU, ROUGE, RAGAS
- Benchmarking suite for regression testing
- Observability and tracing

**Expected Impact**: Data-driven optimisation replacing guesswork

### 2. State-of-the-Art Retrieval
**Problem**: Current retrieval misses nuanced queries and context.

**Solution**:
- Reranking with cross-encoders for precision
- Query expansion and rewrites
- Multi-query retrieval for complex questions
- Parent-child document retrieval for context
- Hybrid search optimisations

**Expected Impact**: MRR@10 > 0.75 (vs 0.60 in v0.2)

### 3. Intelligent Chunking
**Problem**: Fixed-size chunks break semantic boundaries.

**Solution**:
- Semantic chunking (boundaries at topic shifts)
- Agentic chunking (LLM-proposed boundaries)
- Proposition-based chunking (atomic facts)
- Dynamic chunk sizing based on content

**Expected Impact**: Better retrieval precision with smaller chunks

### 4. Multi-Modal Intelligence
**Problem**: Can only process text, missing images and tables.

**Solution**:
- OCR for scanned documents
- Table extraction and understanding
- Image captioning and embedding
- Chart interpretation
- Layout-aware PDF processing

**Expected Impact**: Handle 95% of real-world PDFs successfully

### 5. Production Data Management
**Problem**: No versioning, limited metadata, poor discoverability.

**Solution**:
- Document version tracking
- Metadata filtering and faceted search
- Auto-tagging and classification
- Advanced search operators
- Collection organisation

**Expected Impact**: Manage large document collections professionally

### 6. Enhanced Generation Quality
**Problem**: Citations lack precision, responses lack reasoning transparency.

**Solution**:
- Chain-of-thought reasoning in responses
- Precise chunk-level citations
- Confidence scoring
- Multi-step reasoning for complex queries

**Expected Impact**: RAGAS score > 0.80 (vs 0.70 in v0.2)

### 7. Developer Experience
**Problem**: CLI lacks automation and advanced workflows.

**Solution**:
- Interactive mode for exploration
- Automation hooks for CI/CD
- Configuration management
- Batch operations improvements
- Developer tools (inspect, debug)

**Expected Impact**: Seamless integration into workflows

---

## Key Themes

1. **Advanced Retrieval** - Hybrid search, reranking, query expansion
2. **Intelligent Chunking** - Semantic, agentic, and proposition-based strategies
3. **Multi-Modal** - Images, tables, PDFs with complex layouts
4. **Quality & Evaluation** - Metrics, benchmarking, observability
5. **Data Management** - Versioning, metadata, auto-tagging
6. **Enhanced Generation** - Chain-of-thought, better citations
7. **CLI Enhancements** - Interactive mode, automation, developer tools

---

## Feature Areas (7 Parts)

### Part 1: Advanced Query Processing & Retrieval
**Effort:** 41 hours

**Features:**
- FEAT-001: Hybrid Search (BM25 + Dense)
- FEAT-002: Reranking (Cross-Encoder)
- FEAT-003: Query Expansion & Rewrites
- FEAT-004: Multi-Query Retrieval
- FEAT-005: Parent-Child Document Retrieval

### Part 2: Advanced Chunking Strategies
**Effort:** 28 hours

**Features:**
- FEAT-006: Semantic Chunking
- FEAT-007: Agentic Chunking
- FEAT-008: Proposition-Based Chunking
- FEAT-009: Dynamic Chunk Sizing

### Part 3: Multi-Modal Support
**Effort:** 35 hours

**Features:**
- FEAT-010: Advanced Multi-Modal (Images, Tables, Charts)

### Part 4: Evaluation & Quality
**Effort:** 24 hours

**Features:**
- Comprehensive evaluation framework
- Retrieval metrics (MRR, NDCG, Recall@k)
- Generation metrics (BLEU, ROUGE, RAGAS)
- Benchmarking suite
- Observability and tracing

### Part 5-6: Data Management & Generation
**Effort:** 54 hours combined

**Data Management Features:**
- FEAT-011: Document Version Tracking
- FEAT-012: Metadata Filtering & Faceted Search
- FEAT-013: Auto-Tagging & Classification

**Generation Features:**
- FEAT-014: Chain-of-Thought Reasoning
- FEAT-015: Enhanced Citations

### Part 7: Advanced CLI Features
**Effort:** 52-71 hours

**Features:** 11 advanced CLI capabilities

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

## Implementation Approach

### Recommended Order

**Phase 1 (Foundation):** Evaluation & Quality (24 hours)
- Build metrics and benchmarking first
- Enables data-driven decisions for all other features

**Phase 2 (Core Retrieval):** Advanced Query Processing (41 hours)
- Hybrid search and reranking provide biggest quality wins
- Foundation for other retrieval techniques

**Phase 3 (Intelligence):** Advanced Chunking (28 hours)
- Semantic and agentic chunking improve retrieval quality
- Benefits all downstream features

**Phase 4 (Capabilities):** Multi-Modal Support (35 hours)
- Unlocks new document types
- High user value

**Phase 5 (Production):** Data Management & Generation (54 hours)
- Production-readiness features
- Enhanced citations and metadata

**Phase 6 (UX):** CLI Enhancements (52-71 hours)
- Developer productivity and automation
- Can be implemented in parallel

### Total Effort
**234-260 hours** across 7 feature areas
**Timeline:** ~6-8 months with single developer

---

## Architecture Changes

### New Components
- **Reranker**: Cross-encoder model for result reranking
- **Query Processor**: Expansion, rewrites, multi-query
- **Semantic Chunker**: LLM-based semantic boundary detection
- **Multi-Modal Processor**: Image, table, chart extraction
- **Evaluation Framework**: Metrics, benchmarks, tracing
- **Metadata Manager**: Tagging, classification, filtering

### Modified Components
- **Chunking Pipeline**: Multiple strategies, dynamic sizing
- **Retrieval Pipeline**: Parent-child, multi-query support
- **Generation Pipeline**: Chain-of-thought, enhanced citations
- **Vector Store**: Metadata filtering, version tracking
- **CLI**: Interactive mode, automation hooks

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

## Preparation for v0.4 Integration

While not part of v0.3's deliverables, this version includes preparatory work for v0.4's plugin architecture and LEANN backend integration.

### VectorStore Abstraction Layer
**Effort:** 8-12 hours (within v0.3 budget)

**Context:** v0.4 will introduce LEANN as an optional vector storage backend alongside ChromaDB. To enable this, v0.3 will lay the groundwork with abstraction layer design.

**Tasks:**
1. **Interface Design** (4-6 hours)
   - Define VectorStore abstract base class
   - Specify VectorStoreDocument and VectorStoreQueryResult datatypes
   - Document interface contracts and method signatures
   - See [ADR-0015: VectorStore Abstraction](../../../decisions/adrs/0015-vectorstore-abstraction.md)

2. **ChromaDB Refactor** (4-6 hours)
   - Extract ChromaDB logic into ChromaDBStore class
   - Update ragged core to use VectorStore interface
   - Ensure all existing tests pass
   - Prepare for multi-backend support

**Rationale:**
- Enables v0.4 LEANN integration without breaking changes
- Cleaner architecture with better separation of concerns
- Testing infrastructure for multiple backends
- Foundation for future vector store options

### LEANN Performance Evaluation
**Effort:** Parallel to Part 4 (Evaluation & Quality)

**Context:** LEANN offers 97% storage savings but with 90% top-3 recall vs ChromaDB's ~100%. v0.3's evaluation framework will benchmark both backends.

**Evaluation Criteria:**
1. **Storage Efficiency**
   - Measure actual storage reduction on test corpus
   - Compare ChromaDB vs LEANN disk usage
   - Track index build times

2. **Retrieval Quality**
   - MRR@10, NDCG@10, Recall@10 on benchmark dataset
   - Compare ChromaDB vs LEANN retrieval accuracy
   - Identify query types where LEANN underperforms

3. **Query Latency**
   - Measure average query response time
   - Compare cold vs warm cache performance
   - Assess impact on end-to-end RAG latency

4. **Scalability**
   - Test with 1K, 10K, 100K, 1M documents
   - Memory usage under different workloads
   - Insertion and update throughput

**Deliverables:**
- Performance comparison matrix (ChromaDB vs LEANN)
- Recommendation guide for when to use each backend
- Trade-off analysis (storage vs accuracy vs latency)
- Data to inform v0.4 integration decisions

**Integration:**
- Results feed into [LEANN Integration Analysis](../../../decisions/2025-11-16-leann-integration-analysis.md)
- Guides v0.4 implementation priorities
- Documents user-facing trade-offs

---

## Out of Scope (Deferred to v0.4+)

❌ **Not in v0.3**:
- Knowledge graphs (v0.4)
- Personal memory systems (v0.4)
- LEANN backend implementation (v0.4 - preparation only in v0.3)
- Web UI (v1.0)
- Multi-user support (v1.0)
- API server (v1.0)

---

## Related Documentation

- [v0.2 Planning](../v0.2/) - Current version design
- [v0.4 Planning](../v0.4/) - Knowledge graphs
- [v0.5 Planning](../v0.5/) - Advanced memory
- [Roadmap: v0.3.0](../../../roadmap/version/v0.3.0/) - Detailed implementation plan
- [Architecture](../../architecture/) - System architecture
- [CLI Enhancements Catalogue](../../interfaces/cli/enhancements.md) - Complete CLI specs

---
