# LEANN Integration Analysis - Decision Record

**Date:** 2025-11-16
**Status:** Research Complete, Pending v0.4 Implementation
**Decision Type:** Strategic Architecture

---

## Context

LEANN (Lightweight Embedding-Aware Neural Network) is a vector database that achieves 97% storage savings through graph-based selective recomputation instead of storing all embeddings permanently. This analysis evaluates the feasibility and strategic fit of integrating LEANN into ragged as an alternative vector storage backend.

### LEANN Overview

- **Repository:** https://github.com/yichuan-w/LEANN
- **Paper:** https://arxiv.org/abs/2506.08276
- **License:** MIT (compatible with ragged's GPL-3.0)
- **Core Innovation:** On-demand embedding computation using graph-based indexing
- **Storage Efficiency:** 97% reduction (5% of raw data, 50× smaller than traditional indexes)
- **Performance Trade-off:** 90% top-3 recall with <2s latency

---

## Strategic Alignment

### Strong Alignments ✅

1. **Privacy-First Philosophy**
   - Both projects: 100% local processing, no cloud dependencies
   - Perfect alignment with ragged's core principles

2. **Storage Efficiency**
   - LEANN addresses ragged's future scaling pain point
   - 97% reduction critical for large document collections

3. **Target Use Case**
   - LEANN: "RAG on Everything" for personal AI
   - ragged: Personal knowledge assistant
   - Nearly identical target users and use cases

4. **Hardware Constraints**
   - Both designed for personal devices with limited resources
   - Optimised for Mac Studio, laptop, desktop use

5. **License Compatibility**
   - MIT → GPL-3.0 is legally compatible
   - No licensing barriers to integration

### Trade-offs ⚠️

1. **Accuracy vs Storage**
   - LEANN: 90% top-3 recall
   - ChromaDB: ~100% recall
   - Users must choose based on priorities

2. **Build Complexity**
   - LEANN requires C++ compilation (CMake, Boost, Protobuf)
   - ragged currently pure Python
   - Increases deployment friction

3. **Dual Backend Maintenance**
   - Supporting both ChromaDB and LEANN doubles testing surface
   - Requires abstraction layer (VectorStore interface)

---

## Technical Feasibility

### Dependencies Analysis

| Component | LEANN | ragged | Compatibility |
|-----------|-------|--------|---------------|
| Python | 3.9-3.13 | 3.12 (strict) | ✅ Compatible |
| sentence-transformers | >3.0.0 | >=2.2.2 | ⚠️ Version upgrade needed |
| torch | Required | Transitive | ✅ Compatible |
| ollama | Optional | >=0.1.0 | ✅ Compatible |
| chromadb | N/A | >=0.4.18 | Coexist |
| Build tools | C++, CMake | Python only | Significant increase |

### Integration Approaches

**Evaluated Options:**

1. **Inspiration-Only** (Low Effort: 40-60 hours)
   - Learn from LEANN, implement natively
   - Full control, GPL-3.0 clean
   - Miss optimised implementation

2. **Library Dependency** (Medium Effort: 38-54 hours) ⭐ **RECOMMENDED**
   - Add LEANN as optional backend alongside ChromaDB
   - Leverage proven implementation
   - Optional - doesn't break existing users
   - Future-proof for large collections

3. **Full Replacement** (High Effort: 60-80 hours)
   - Replace ChromaDB entirely
   - Breaking change, no fallback
   - ❌ Not recommended - too risky

4. **Fork and Adapt** (Highest Effort: 100+ hours)
   - Fork LEANN, integrate directly
   - Maintenance burden, duplicate effort
   - ❌ Not recommended - unnecessary

---

## Decision: Optional Backend in v0.4

### Recommendation

**Integrate LEANN as an optional backend in v0.4 (Plugin Architecture)**

### Rationale

1. **Strategic Timing**
   - v0.4 introduces plugin architecture - perfect foundation
   - v0.4 roadmap explicitly mentions "pluggable vector stores"
   - v0.3 evaluation framework provides benchmarking capability
   - Timeline (Q4 2026) allows v0.2 and v0.3 completion first

2. **Risk Mitigation**
   - Optional dependency via pip extras: `pip install ragged[leann]`
   - Existing ChromaDB users unaffected
   - Users choose based on storage vs accuracy needs

3. **Effort Justification**
   - 38-54 hours for production-ready backend
   - 17-30% increase to v0.4's 180-225 hour budget
   - Manageable within version scope

4. **Value Proposition**
   - 97% storage savings increasingly valuable as collections grow
   - LEANN's graph structure complements v0.4's knowledge graphs
   - Future-proof architecture for scaling

### Prerequisites

**Must complete before v0.4:**
- [ ] VectorStore abstraction layer (ADR-0004)
- [ ] Refactor ChromaDB to use abstraction
- [ ] v0.3 evaluation framework operational
- [ ] Benchmark LEANN vs ChromaDB performance

---

## Implementation Roadmap

### Pre-Work in v0.3 (Q2-Q3 2026)

**Effort: 8-12 hours within v0.3**

1. Design VectorStore abstraction interface (4-6 hours)
2. Refactor ChromaDB to use abstraction (4-6 hours)
3. Evaluate LEANN performance (parallel to v0.3 evaluation work)

### v0.4 Implementation (Q4 2026 - Q1 2027)

**Effort: 38-54 hours**

**Phase 1: Foundation** (8-10 hours)
- Install LEANN locally, test compatibility
- Resolve dependency conflicts
- Test platform-specific builds (macOS, Linux)

**Phase 2: Adapter** (12-16 hours)
- Implement LeannVectorStore class
- Handle embedding format conversions
- Metadata mapping and storage
- Unit tests for adapter

**Phase 3: Integration** (8-12 hours)
- Add LEANN as optional dependency: `[leann]` extras
- CLI backend selection: `--backend chromadb|leann`
- Configuration file support
- Migration command: `ragged migrate chromadb-to-leann`

**Phase 4: Deployment** (6-8 hours)
- Multi-stage Dockerfile with LEANN build
- Platform-specific build scripts
- Docker Compose profiles for backends
- CI/CD updates for LEANN testing

**Phase 5: Documentation** (4-8 hours)
- Platform-specific installation guides
- Migration documentation
- Performance comparison docs
- Integration tests

---

## Risk Assessment

### Challenge 1: Build Complexity
**Risk:** C++ compilation, multiple system dependencies
**Mitigation:**
- Make LEANN optional via pip extras
- Provide pre-built wheels for major platforms
- Multi-stage Docker builds with layer caching
- Progressive disclosure: simple (ChromaDB) vs advanced (LEANN)

### Challenge 2: Platform-Specific Issues
**Risk:** Different dependencies on macOS vs Linux
**Mitigation:**
- CI/CD testing on multiple platforms
- Platform-specific installation guides
- Docker as recommended deployment for LEANN users

### Challenge 3: Dependency Conflicts
**Risk:** sentence-transformers version mismatch
**Mitigation:**
- Upgrade ragged to sentence-transformers >=3.0.0 in v0.3/v0.4
- Test backwards compatibility
- Provide migration path for existing collections

### Challenge 4: Performance Trade-offs
**Risk:** LEANN's on-demand computation slower than full storage
**Mitigation:**
- v0.3 evaluation framework provides benchmarks
- Let users choose based on priorities
- Document trade-offs clearly
- Configurable graph_degree and search_complexity

### Challenge 5: Migration Path
**Risk:** Existing ChromaDB users can't easily switch
**Mitigation:**
- Build migration tool: ChromaDB → LEANN converter
- Support running both backends simultaneously
- Per-collection backend selection
- Clear migration documentation

### Challenge 6: Maintenance Burden
**Risk:** Two backends doubles testing surface
**Mitigation:**
- VectorStore abstraction enables shared tests
- Parameterised tests run against both backends
- CI/CD matrix testing
- Community involvement for LEANN-specific issues

---

## Success Criteria

**Definition of Done for v0.4:**

- [x] Research complete and decision documented
- [ ] VectorStore abstraction layer implemented
- [ ] LeannVectorStore adapter functional
- [ ] Both backends passing integration tests
- [ ] Migration tool ChromaDB → LEANN working
- [ ] Platform-specific builds successful (macOS, Linux)
- [ ] Documentation complete and verified
- [ ] Performance benchmarks published
- [ ] <5% increase in overall maintenance burden

---

## Related Documentation

- [ADR-0004: VectorStore Abstraction Architecture](./adrs/0004-vectorstore-abstraction.md)
- [v0.3 Planning: Evaluation Framework](../planning/version/v0.3/README.md)
- [v0.4 Roadmap: Plugin Architecture](../roadmap/version/v0.4.0/README.md)
- [LEANN GitHub Repository](https://github.com/yichuan-w/LEANN)
- [LEANN Academic Paper](https://arxiv.org/abs/2506.08276)

---

**Maintained By:** ragged development team
**Last Updated:** 2025-11-16
**Next Review:** v0.3 completion (Q3 2026)
