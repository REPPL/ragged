# ragged Development Roadmap - All Versions

**Current Version:** v0.2.2

**Last Updated:** 2025-11-12

**Planning Horizon:** v0.7.0 (~850-1050 total hours)

---

## Overview

This document provides a unified view of all planned ragged versions. Each version has its own detailed roadmap in its subdirectory.

**Philosophy:**
- **Stability First:** Fix critical bugs before adding features
- **Privacy Always:** All processing remains local
- **AI-Focused Estimates:** Hours for autonomous AI coding assistant
- **Manual Testing:** Clear markers for user verification required
- **No Migrations:** Fresh clone testing between versions

---

## Timeline Summary

```
Current     v0.2.2 ━━━━━━━━━━━━━━━━━━━━┓
                                        │ Bug Fixes Phase
Next        v0.2.5 ━━━━━━━━━━━━━━━━━━━━┫ (40-50 hours)
            v0.2.7 ━━━━━━━━━━━━━━━━━━━━┛ (80-100 hours)
            ══════════════════════════════ STABILITY ═══════════
            v0.3.0 ━━━━━━━━━━━━━━━━━━━━┓ Multi-Embedding
                                        │ (180-220 hours)
            ══════════════════════════════ FOUNDATION ══════════
            v0.4.0 ━━━━━━━━━━━━━━━━━━━━┓ ColPali Vision
                                        │ (160-200 hours)
            ══════════════════════════════ MULTIMODAL ══════════
Future      v0.5.0+━━━━━━━━━━━━━━━━━━━━┛ Advanced Features
```

---

## Version Overview

### v0.2.5 - Bug Fixes & Quality (40-50 hours)

**Status:** Planning
**Focus:** Critical bugs, no new features

**Key Issues:**
- BUG-001: API endpoints non-functional (blocks Web UI)
- BUG-002: Logger undefined in settings.py
- BUG-003: Duplicate detection I/O blocking
- BUG-004-013: Error handling, validation, memory leaks

**Success Criteria:**
- Zero crashes on valid inputs
- Web UI functional for real use
- All documented bugs resolved
- Test coverage ≥80%

**See:** [v0.2.5/README.md](./v0.2.5/README.md)

---

### v0.2.7 - UX & Performance (80-100 hours)

**Status:** Planning
**Focus:** User experience and performance optimizations

**Key Features:**
- Seamless model switching with model pool
- Multi-collection document organization
- Query result caching (50-90% speedup)
- Async batch processing (2-4x faster)
- Enhanced CLI feedback

**Success Criteria:**
- Batch processing 2-4x faster
- Query latency reduced 50-90% (cached)
- Model switching <2 sec
- Positive user feedback

**See:** [v0.2.7/README.md](./v0.2.7/README.md)

---

### v0.3.0 - Advanced RAG Techniques (180-220 hours)

**Status:** Planning
**Focus:** State-of-the-art RAG capabilities

**Key Features:**
- Query decomposition (multi-query RAG)
- HyDE (Hypothetical Document Embeddings)
- Cross-encoder reranking (+10-20% quality)
- Contextual compression
- Self-querying retrieval
- RAGAS evaluation framework

**Quality Improvements:**
- HyDE: +5-15% on complex queries
- Reranking: +10-20% overall
- Contextual compression: +5-10% on long documents

**Success Criteria:**
- Measurable quality improvements for each technique
- Comprehensive evaluation framework
- Research-backed validation

**See:** [v0.3.0/README.md](./v0.3.0/README.md)

---

### v0.4.0 - Personal Memory & Knowledge Graphs (160-200 hours)

**Status:** Planning
**Focus:** Intelligent context and relationships

**Key Features:**
- Personal memory system (user preferences)
- Knowledge graph integration (Kuzu)
- Entity extraction and relationship mapping
- Multi-hop reasoning
- Graph-enhanced retrieval

**Success Criteria:**
- Personal memory improves UX
- Knowledge graph enhances multi-document queries
- Privacy guarantees maintained
- Performance overhead <10%

**See:** [v0.4.0/README.md](./v0.4.0/README.md)

---

## Future Versions (Beyond v0.4.0)

**v0.5.0 - ColPali Vision Integration**
- Multi-modal document understanding
- Vision-based retrieval for PDFs
- GPU-accelerated processing

**v0.6.0 - Intelligent Optimization**
- Auto-routing queries to optimal models
- Domain adaptation
- Advanced analytics

**v0.7.0 - Production Ready**
- Scalability improvements
- Enterprise features
- Stable API guarantee

---

## Key Principles

### 1. No Breaking Changes Before v1.0

Every version maintains backward compatibility. Users can upgrade safely without data loss or workflow changes.

### 2. Privacy First

All processing remains local. No external APIs without explicit user consent. User control over all data.

### 3. Progressive Disclosure

Simple by default, advanced features opt-in. Sensible defaults that work for most users. Excellent documentation.

### 4. Quality Focused

Empirical validation required for quality claims. Comprehensive testing. Performance benchmarks.

### 5. AI-Assisted Development

Hour estimates reflect autonomous AI coding assistant capabilities. Clear markers for required manual testing. Transparent about AI usage.

---

## Version Comparison

| Feature | v0.2.2 | v0.2.5 | v0.2.7 | v0.3.0 | v0.4.0 |
|---------|--------|--------|--------|--------|--------|
| **Status** | Current | Planning | Planning | Planning | Planning |
| **Hours** | - | 40-50 | 80-100 | 180-220 | 160-200 |
| **Focus** | - | Bugs | UX/Perf | RAG | Memory |
| Web UI | ⚠️ Degraded | ✅ Fixed | ✅ Enhanced | ✅ | ✅ |
| Model Switching | ❌ | ❌ | ✅ | ✅ | ✅ |
| Collections | ❌ | ❌ | ✅ | ✅ | ✅ |
| Caching | ❌ | ❌ | ✅ | ✅ | ✅ |
| HyDE | ❌ | ❌ | ❌ | ✅ | ✅ |
| Reranking | ❌ | ❌ | ❌ | ✅ | ✅ |
| RAGAS Eval | ❌ | ❌ | ❌ | ✅ | ✅ |
| Knowledge Graph | ❌ | ❌ | ❌ | ❌ | ✅ |
| Personal Memory | ❌ | ❌ | ❌ | ❌ | ✅ |

---

## Development Workflow

### Phase 1: Planning
1. Create detailed roadmap in `roadmap/version/vX.X/README.md`
2. Document features, bugs, hour estimates
3. Mark manual testing points: ⚠️ MANUAL TEST REQUIRED
4. Review and approve

### Phase 2: Implementation
5. Begin development
6. Log daily progress in `devlog/daily/`
7. Track implementation in `devlog/version/vX.X/`
8. Make architectural decisions → Create ADRs

### Phase 3: Release
9. Complete implementation
10. Create release notes in `devlog/version/vX.X/`
11. Log actual time in `time-logs/version/vX.X/`
12. User testing and verification

### Phase 4: Next Version
13. Fresh clone for testing
14. Begin next version cycle

---

## Manual Testing Requirements

**⚠️ Indicates manual testing required throughout roadmaps:**

- Web UI functionality (uploads, queries, error handling)
- GPU features (ColPali, vision processing)
- End-to-end workflows (ingest → query → answer)
- Performance benchmarks (cache hit rates, speedups)
- User acceptance (UX improvements)

**Why manual testing:**
- UI/UX requires human evaluation
- Performance needs real-world validation
- GPU testing needs specific hardware
- Integration scenarios complex to automate
- User satisfaction subjective

---

## Questions?

- **For bug reports:** Open GitHub issue
- **For feature requests:** Create RFC in `rfcs/`
- **For roadmap feedback:** GitHub Discussions
- **For usage questions:** Check main README

---

## Document Metadata

- **Created:** 2025-11-12
- **Maintained By:** ragged development team
- **Location:** `docs/development/roadmap/version/README.md`
- **Purpose:** Unified overview of all planned versions

---

**This is a living roadmap.** Versions may shift based on feedback, priorities may change based on user needs, and timeline estimates may adjust based on complexity.
