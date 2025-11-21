# v0.3.3 Planning: Intelligent Chunking

**WHAT to Build**: Semantic and hierarchical chunking strategies
**WHY**: Improve RAG retrieval precision and answer completeness

---

## Vision

Transform ragged's chunking from fixed-size boundaries to intelligent, semantic-aware strategies that respect document structure and meaning.

**Current State (v0.2.x):**
- Fixed-size chunking breaks semantic boundaries
- Topic changes mid-chunk reduce retrieval precision
- No hierarchical context for answer generation
- Simple split-by-character approach

**Desired State (v0.3.3):**
- Semantic boundaries based on topic coherence
- Hierarchical parent-child relationships for context
- Improved retrieval precision (5-10% target)
- Better answer completeness (10-15% target)

---

## Goals & Objectives

### Primary Goals

1. **Semantic Chunking**
   - **WHAT**: Split text based on semantic similarity between sentences
   - **WHY**: Respect topic boundaries for better retrieval precision
   - **TARGET**: 5-10% improvement in retrieval precision (MRR@10)

2. **Hierarchical Chunking**
   - **WHAT**: Create parent-child chunk relationships
   - **WHY**: Provide broader context during answer generation
   - **TARGET**: 10-15% improvement in answer completeness

3. **Maintain Performance**
   - **WHAT**: Keep chunking overhead minimal
   - **WHY**: Don't sacrifice speed for small quality gains
   - **TARGET**: <45s additional per document

---

## Problem Statement

### Current Problems

**Problem 1: Semantic Boundary Violations**
- Fixed-size chunks (e.g., 500 chars) often split mid-topic
- When retriever finds "half a topic," answers incomplete or inaccurate
- Example: Legal document with clause split across chunks → misinterpretation

**Problem 2: Missing Context**
- Retrieved chunks lack broader document context
- Surrounding paragraphs/sections not available to LLM
- Example: Retrieving conclusion without access to supporting arguments

**Problem 3: Inconsistent Chunk Quality**
- Some chunks = complete ideas (high quality)
- Other chunks = sentence fragments (low quality)
- Retrieval quality varies unpredictably

### Why Now?

- **Foundation Ready**: v0.1-v0.2.x established working RAG system
- **Quality Metrics**: v0.3.0 added RAGAS evaluation to measure improvements
- **User Feedback**: Current chunking cited as retrieval quality bottleneck
- **Technology Available**: Sentence-transformers models mature and efficient

---

## Success Criteria

### Functional Requirements

**Must Have:**
1. ✅ Semantic chunking using sentence embeddings
2. ✅ Hierarchical chunking with parent-child relationships
3. ✅ Configurable similarity thresholds
4. ✅ Fallback to simple splitting on errors
5. ✅ Complete type hints and British English docstrings

**Should Have:**
1. ✅ Lazy model loading for performance
2. ✅ Cache-friendly design
3. ✅ Thread-safe implementation
4. ⏳ CLI options for strategy selection (deferred to v0.3.4+)

**Could Have (Deferred):**
1. ⏳ Multi-language support
2. ⏳ Custom embedding models
3. ⏳ Overlap strategies for hierarchical chunks

### Quality Metrics

**Retrieval Precision:**
- Baseline (fixed-size): MRR@10 ≈ 0.60
- Target (semantic): MRR@10 ≥ 0.65 (5-10% improvement)
- Measurement: RAGAS evaluation framework (v0.3.0)

**Answer Completeness:**
- Baseline: Completeness score ≈ 0.65
- Target (hierarchical): Completeness ≥ 0.75 (10-15% improvement)
- Measurement: RAGAS faithfulness and answer relevancy

**Performance:**
- Additional chunking time: <45s per document
- Memory overhead: Acceptable for 100-500MB model
- Startup time: <2s (lazy loading)

---

## Design Philosophy

### Core Principles

1. **Semantic Coherence Over Fixed Boundaries**
   - Chunks should represent complete thoughts
   - Topic transitions = natural chunk boundaries
   - Use embedding similarity to detect transitions

2. **Hierarchical Context Preservation**
   - Large parents (1500-3000 chars) for context
   - Small children (300-800 chars) for precision
   - Retrieve children, generate with parents

3. **Graceful Degradation**
   - If model loading fails → fallback to simple split
   - If embedding fails → fallback to sentence-based split
   - No total failures, always produce chunks

4. **Performance Through Laziness**
   - Load models only when needed
   - Cache embeddings when beneficial
   - Singleton pattern for model instances

---

## Strategic Fit

### Alignment with v0.3.x Vision

**v0.3 Series Goal:** Transform ragged from functional to intelligent

**v0.3.3 Contribution:**
- **Intelligence**: Semantic understanding of document structure
- **Quality**: Improved retrieval precision through better chunking
- **Context**: Hierarchical relationships provide richer information

**Enables Future Versions:**
- v0.3.7: RAGAS evaluation can measure chunking quality
- v0.3.4+: Pipeline integration makes strategies usable
- v0.4.x: Advanced chunking (multi-doc, cross-references)

### Dependency Graph

**Prerequisites:**
- v0.3.1: Configuration system (for chunking strategy selection)
- v0.1-v0.2: Base ingestion and retrieval pipeline

**Enables:**
- v0.3.4+: Integration into pipeline
- v0.3.7: Quality measurement via RAGAS

---

## Risks & Mitigation

### Technical Risks

**Risk 1: Model Size (100-500MB)**
- **Impact**: Large download, high memory usage
- **Likelihood**: Certain
- **Mitigation**: Lazy loading, document model size requirements clearly

**Risk 2: Thread Safety**
- **Impact**: Race conditions in multi-threaded environments
- **Likelihood**: Medium
- **Mitigation**: Instance-based design, document thread safety characteristics

**Risk 3: Test Execution Time**
- **Impact**: Slow CI/CD if loading models in tests
- **Likelihood**: High
- **Mitigation**: Mock-based testing, separate integration tests

### Process Risks

**Risk 4: Integration Complexity**
- **Impact**: Difficult to integrate into existing pipeline
- **Likelihood**: Medium
- **Mitigation**: Design clean API, defer integration to v0.3.4+

**Risk 5: Quality Measurement Lag**
- **Impact**: Can't validate improvements until v0.3.7 (RAGAS)
- **Likelihood**: Certain
- **Mitigation**: Document assumptions, validate later, accept uncertainty

---

## Non-Goals (Out of Scope)

### Explicitly NOT Included

1. **Pipeline Integration** - Deferred to v0.3.4+
   - Building modules only, not integrating into CLI/config
   - Clean API for future integration

2. **Multi-Language Support** - Deferred to v0.4.x
   - English-only for v0.3.3
   - Architecture allows future extension

3. **Custom Embedding Models** - Deferred to v0.4.x
   - Use `all-MiniLM-L6-v2` only
   - Configuration for model selection later

4. **Performance Optimization** - Deferred to v0.3.9
   - No GPU acceleration
   - No distributed chunking
   - Simple, functional implementation first

---

## Alternative Approaches Considered

### Alternative 1: Rule-Based Chunking

**Approach**: Use regex patterns to detect section headers, paragraph breaks
**Pros**: No model dependency, fast, deterministic
**Cons**: Brittle, document-format dependent, no semantic understanding
**Decision**: REJECTED - Too brittle for diverse document formats

### Alternative 2: LLM-Based Chunking

**Approach**: Use LLM to identify semantic boundaries
**Pros**: Highly accurate, context-aware
**Cons**: Expensive (API costs), slow, requires external service
**Decision**: REJECTED - Violates local-only privacy principle

### Alternative 3: Recursive Hierarchical Chunking

**Approach**: Recursively split until chunks meet size criteria
**Pros**: Simple, no embeddings needed
**Cons**: No semantic awareness, arbitrary boundaries
**Decision**: PARTIAL ADOPTION - Use for hierarchical baseline, add semantic layer

### Selected Approach: Semantic + Hierarchical

**Rationale**:
- Semantic: Embedding-based boundary detection balances accuracy and cost
- Hierarchical: Parent-child provides context without LLM complexity
- Local-only: All processing on device, no external dependencies
- Proven: Sentence-transformers widely used, mature library

---

## Stakeholders

### Internal Stakeholders

**Development Team:**
- **Need**: Clear API for integration in v0.3.4+
- **Concern**: Complexity of integration, test execution time
- **Engagement**: Design review, API feedback

**QA/Testing:**
- **Need**: Fast test suite, comprehensive coverage
- **Concern**: Model loading in tests, test data requirements
- **Engagement**: Mock strategy, test plan review

### External Stakeholders

**End Users:**
- **Need**: Better retrieval quality, complete answers
- **Concern**: Performance (don't slow down ingestion too much)
- **Engagement**: Beta testing feedback, quality metrics

**Contributors:**
- **Need**: Clean, well-documented code for future enhancements
- **Concern**: Learning curve for semantic chunking concepts
- **Engagement**: Comprehensive docstrings, usage examples

---

## Related Documentation

- **Roadmap**: [v0.3.3 Roadmap](../../../roadmap/version/v0.3/v0.3.3.md) - Detailed HOW & WHEN
- **Implementation**: [v0.3.3 Summary](../../../implementation/version/v0.3/v0.3.3/summary.md) - WHAT was built
- **Lineage**: [v0.3.3 Lineage](../../../implementation/version/v0.3/v0.3.3/lineage.md) - Evolution trace
- **Parent Plan**: [v0.3 Planning](../README.md) - Overall v0.3 vision

---

**Planning Status**: Complete
**Next Step**: [v0.3.3 Roadmap](../../../roadmap/version/v0.3/v0.3.3.md)
