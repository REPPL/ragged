# RAG Latency Optimisation Research Notes

**Status**: Reference material for future development
**Created**: 2025-11-18
**Purpose**: Track research on RAG system latency reduction techniques

---

## Overview

Collection of research and articles exploring latency optimisation in RAG systems. These sources inform ragged's optimisation strategy but don't necessarily warrant formal acknowledgement (either because techniques are well-established, already independently planned, or not yet implemented).

---

## 1. Semantic Chunking for Attention Optimisation

**Source**: "RAG Too Slow? How to Cut Latency by 97%" by Florian June
**Publication**: AI Exploration Journey (Medium), November 2025
**URL**: https://aiexpjourney.substack.com/p/rag-too-slow-how-to-cut-latency-by
**Accessed**: 2025-11-18

### Key Concepts

**Problem Identified:**
- Traditional RAG pipelines retrieve chunks without considering semantic relationships
- LLMs waste compute calculating attention scores across semantically disconnected text
- Near-zero cross-chunk attention scores represent massive computational inefficiency

**Proposed Solution:**
- Organise chunks by semantic coherence to reduce unnecessary attention computation
- Eliminate computational overhead from evaluating irrelevant cross-chunk relationships

**Claimed Impact:** 97% latency reduction (unverified; article behind paywall)

### Relevance to ragged

**Status**: Concept already independently planned

- **v0.3.5 (FEAT-005)**: Semantic chunking implementation (10 hours)
  - Creates coherent chunks that naturally reduce attention overhead
  - Uses local embedding models for chunk boundary detection
  - Hierarchical structure for multi-level semantic organisation

- **v0.6.0 (OPTIMISE-001)**: Context scope management (15-20 hours)
  - Dynamic context adaptation based on query complexity
  - Limits context to semantically relevant documents
  - Further reduces unnecessary attention computation

### Assessment

**Novel Contribution:** Unclear (paywall prevents full verification)
**Acknowledgement Needed:** No - semantic chunking is well-established RAG best practice
**Implementation Status:** Already planned in v0.3.5 (before encountering article)
**Action:** Continue with planned semantic chunking; no changes needed

---

## 2. REFRAG: Dynamic Retrieval During Decoding

**Source**: "REFRAG: Rethinking RAG based Decoding"
**Authors**: Xiaoqiang Lin, Aritra Ghosh, Bryan Kian Hsiang Low, Anshumali Shrivastava, Vijai Mohan
**Publication**: arXiv:2509.01092v1, September 3, 2025
**URL**: https://arxiv.org/abs/2509.01092
**Accessed**: 2025-11-18

### Key Concepts

**Innovation**: Dynamic document retrieval throughout generation process (not just upfront)

**How It Works:**
- Conventional RAG: Retrieve documents once → Generate full response
- REFRAG: Retrieve dynamically during decoding as generation progresses
- Enables efficient document selection throughout generation
- Reduces computational overhead by retrieving only as needed

**Benefits for Local Systems:**
- Reduces number of documents retrieved (memory savings)
- Optimises when retrieval occurs (compute efficiency)
- Makes deployment on edge devices more feasible

### Relevance to ragged

**Status**: Interesting for future research, not currently planned

**Current ragged Approach:**
- Upfront retrieval + streaming generation (v0.6.0)
- Parallel retrieval to reduce latency (v0.6.0)
- Static retrieval with dynamic context scoping (v0.6.0)

**Potential Future Application (v0.7+):**
- Could enhance multi-hop reasoning (v1.x multi-agent features)
- May reduce memory footprint for long-context queries
- Requires significant architecture changes (retrieval-generation interleaving)

### Assessment

**Novel Contribution:** Yes - academic research with novel technique
**Acknowledgement Needed:** Only if ragged implements dynamic retrieval in future
**Implementation Status:** Not planned in current roadmap (v0.2-v0.7)
**Action:** Defer consideration to v0.8+ or v1.x; revisit when exploring advanced retrieval strategies

---

## 3. Speculative RAG (Google Research)

**Source**: "Enhancing Retrieval Augmented Generation through Drafting"
**Authors**: Google Research Team
**Publication**: arXiv:2407.08223, 2024
**Accessed**: 2025-11-18 (during latency optimisation research)

### Key Concepts

**Innovation**: Draft-verify approach using dual models

**How It Works:**
1. Small specialist model drafts response (fast)
2. Large generalist model verifies and corrects if needed
3. Accept draft if quality sufficient; otherwise revise or regenerate

**Measured Performance:**
- **Latency Reduction:** 51% (verified in academic study)
- **Accuracy Improvement:** Up to 12.97%
- **Draft Acceptance Rate:** ~60-70% for well-tuned systems

**Trade-offs:**
- Requires loading multiple models (VRAM consideration)
- Quality highly dependent on draft acceptance criteria
- Complexity vs single-model simplicity

### Relevance to ragged

**Status**: Planned as experimental feature in v0.6.0

- **v0.6.0 (OPTIMISE-010)**: Speculative RAG (Experimental) (25-35 hours)
  - Draft model: `llama3.2:3b` (fast, ~500 tokens/sec)
  - Verify model: `llama3.2:70b` (quality, ~50 tokens/sec)
  - Target 30-50% average latency reduction
  - Mark as experimental; validate quality before production

### Assessment

**Novel Contribution:** Yes - well-researched academic technique
**Acknowledgement Needed:** Yes - if implemented; cite Google Research
**Implementation Status:** Planned v0.6.0 (experimental)
**Action:** Implement as planned; create acknowledgement file when feature implemented

---

## 4. Additional Proven Techniques (Various Sources)

### 4A. Streaming Response Generation
**Status**: Industry standard, no specific attribution needed
**Implementation**: v0.6.0 (OPTIMISE-008) - Ollama native support
**Impact**: 60-80% perceived latency reduction (time to first token)

### 4B. Parallel Retrieval Processing
**Status**: Well-established async pattern, no specific attribution needed
**Implementation**: v0.6.0 (OPTIMISE-009) - Standard concurrent processing
**Impact**: 40-60% retrieval latency reduction

### 4C. Context Compression
**Status**: Informed by Context Engineering 2.0 (already acknowledged)
**Implementation**: v0.6.0 (OPTIMISE-001) - Dynamic context scope
**Impact**: 30-50% token reduction for simple queries

### 4D. Smart Caching
**Status**: Standard caching optimisation patterns
**Implementation**: v0.6.0 (OPTIMISE-006) - Enhanced LRU cache
**Impact**: 20-30% cache hit rate improvement

---

## Summary: ragged's Latency Optimisation Strategy

### Implemented (v0.2.x)
- ✅ Basic LRU caching
- ✅ Async document processing
- ✅ Hybrid retrieval (vector + BM25)

### Planned (v0.3.x)
- 📋 Semantic chunking (FEAT-005)
- 📋 Hierarchical chunking (FEAT-006)

### Planned (v0.6.x)
- 📋 Context scope management (OPTIMISE-001)
- 📋 Query classification (OPTIMISE-002)
- 📋 Automatic model routing (OPTIMISE-003)
- 📋 Smart caching (OPTIMISE-006)
- 📋 Streaming response generation (OPTIMISE-008) ⭐ NEW
- 📋 Parallel retrieval pipeline (OPTIMISE-009) ⭐ NEW
- 📋 Speculative RAG - experimental (OPTIMISE-010) ⭐ NEW

### Expected Combined Impact (v0.6.0)
- **Perceived latency:** 60-80% reduction (streaming)
- **Retrieval latency:** 40-60% reduction (parallel processing)
- **Simple queries:** 30-50% reduction (routing + context scope)
- **Cache performance:** 20-30% hit rate improvement
- **Experimental:** 30-50% average reduction (speculative RAG)

### Future Considerations (v0.7+)
- 🔬 Dynamic retrieval during decoding (REFRAG approach)
- 🔬 Hardware acceleration beyond GPU (quantisation, ONNX)
- 🔬 Custom embedding fine-tuning for domain-specific latency improvements

---

## Research Methodology Notes

### How These Sources Were Evaluated

1. **Relevance Check**: Does it apply to privacy-first, local-only RAG?
2. **Novelty Assessment**: Original research or compilation of existing techniques?
3. **Implementation Status**: Already planned independently?
4. **Attribution Requirement**: Formal acknowledgement warranted?
5. **Roadmap Impact**: Does it change current plans?

### Attribution Criteria

**Formal acknowledgement warranted when:**
- ✅ Original academic research with novel contribution
- ✅ Specific technique implemented in ragged
- ✅ Significant influence on architectural decisions

**Research note sufficient when:**
- ✅ Well-established best practice (no specific source)
- ✅ Technique already independently planned
- ✅ Educational article compiling existing knowledge
- ✅ Future consideration (not yet implemented)

---

## Related Documentation

- [Context Engineering 2.0](../acknowledgements/context-engineering-2.0.md) - Formal acknowledgement (theoretical framework)
- [Autonomous Agentic RAG](../acknowledgements/autonomous-agentic-rag.md) - Formal acknowledgement (multi-agent inspiration)
- [v0.6.0 Roadmap](../../roadmap/version/v0.6/README.md) - Latency optimisation features
- [v0.3.x Roadmap](../../roadmap/version/v0.3/) - Semantic chunking

---

**Maintained By**: ragged development team
**License**: GPL-3.0
**Last Updated**: 2025-11-18
