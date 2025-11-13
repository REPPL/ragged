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
Current     v0.2.2 ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
                                                         │ Bug Fixes
Next        v0.2.3 ━━━ P0 Critical (12-15h)             │ (44-59h)
            v0.2.4 ━━━ P1 High Priority (20-25h)        │
            v0.2.6 ━━━ P2 Quality (12-19h)              ┛
            ═════════════════════════════════════════ STABILITY
            v0.2.7 ━━━━━━━━━━━━━ UX & Performance (80-100h)
            ═════════════════════════════════════════ FOUNDATION
            v0.3.0 ━━━━━━━━━━━━━ Advanced RAG (180-220h)
            ═════════════════════════════════════════ ADVANCED
            v0.4.0 ━━━━━━━━━━━━━ Personal Memory (160-200h)
            v0.5.0 ━━━━━━━━━━━━━ ColPali Vision (140-180h)
            v0.6.0 ━━━━━━━━━━━━━ Optimisation (120-150h)
            ═════════════════════════════════════════ PRODUCTION
Future      v0.7.0 ━━━━━━━━━━━━━ Production Ready (150-200h)
```

---

## Version Overview

### v0.2.3 - Critical Bugs (P0) (12-15 hours)

**Status:** Planned
**Priority:** P0 - Must complete first
**Focus:** Blocking issues that prevent core functionality

**Key Issues:**
- BUG-001: API endpoints non-functional (blocks Web UI)
- BUG-002: Logger undefined in settings.py
- BUG-003: Zero test coverage for new modules (606 lines)

**Success Criteria:**
- Web UI functional for uploads and queries
- No NameError in config loading
- Test coverage ≥80% for scanner, batch, model_manager

**See:** [v0.2.3/README.md](./v0.2.3/README.md)

---

### v0.2.4 - High Priority Bugs (P1) (20-25 hours)

**Status:** Planned
**Priority:** P1 - Complete after v0.2.3
**Focus:** Significant quality and functionality improvements

**Key Issues:**
- BUG-004: Inconsistent error handling
- BUG-005: Path handling edge cases
- BUG-006: Memory leaks in batch processing
- BUG-007: ChromaDB metadata type restrictions
- BUG-008: Incomplete hybrid retrieval integration
- BUG-009: Few-shot examples unused
- BUG-010: Duplicate detection incomplete
- BUG-011: Page tracking edge cases

**Success Criteria:**
- Error handling consistent across codebase
- Memory stable during large batches
- Hybrid retrieval works correctly
- All P1 bugs resolved

**See:** [v0.2.4/README.md](./v0.2.4/README.md)

---

### v0.2.5 - Bug Fixes Overview (Split)

**Status:** Split into v0.2.3, v0.2.4, v0.2.6
**Note:** This version was split into three priority-based versions for token-efficient implementation.

**See:** [v0.2.5/README.md](./v0.2.5/README.md) for split overview

---

### v0.2.6 - Quality Improvements (P2) (12-19 hours)

**Status:** Planned
**Priority:** P2 - Complete after v0.2.4
**Focus:** Code quality and maintainability

**Key Improvements:**
- QUALITY-001: Type hint coverage
- QUALITY-002: Docstring completeness
- QUALITY-003: TODO comments cleanup
- QUALITY-004: Code duplication removal
- QUALITY-005: Magic numbers replacement

**Success Criteria:**
- mypy --strict passes
- All public functions documented
- No TODO comments without issue references
- Code quality metrics improved

**See:** [v0.2.6/README.md](./v0.2.6/README.md)

---

### v0.2.7 - UX & Performance (80-100 hours)

**Status:** Planning
**Focus:** User experience and performance optimizations

**Key Features:**
- Seamless model switching with model pool
- Multi-collection document organisation
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

### v0.5.0 - ColPali Vision Integration (140-180 hours)

**Status:** Planned
**Focus:** Multi-modal document understanding with vision-based retrieval

**Key Features:**
- ColPali model integration for vision embeddings
- Dual embedding storage (text + vision)
- Vision-enhanced retrieval
- GPU memory management
- Web UI vision support

**Success Criteria:**
- Vision embeddings generated for PDF pages
- Hybrid text+vision retrieval works
- GPU memory managed efficiently
- CPU fallback functional

**See:** [v0.5.0/README.md](./v0.5.0/README.md)

---

### v0.6.0 - Intelligent Optimisation (120-150 hours)

**Status:** Planned
**Focus:** Automatic query routing, domain adaptation, advanced analytics

**Key Features:**
- Query classification and routing
- Automatic model routing (30-50% latency reduction)
- Domain adaptation for specialised terminology
- Performance analytics and monitoring
- Smart caching strategies

**Success Criteria:**
- Query routing reduces latency for simple queries
- Domain adaptation improves domain-specific retrieval
- Analytics provide actionable insights
- Cache hit rate improved 20-30%

**See:** [v0.6.0/README.md](./v0.6.0/README.md)

---

### v0.7.0 - Production Readiness (150-200 hours)

**Status:** Planned
**Focus:** Scalability, enterprise features, stable API guarantee

**Key Features:**
- API stability and versioning
- Horizontal scalability (load balancing)
- Enterprise authentication (JWT, RBAC)
- Monitoring and observability
- Data backup and recovery
- Rate limiting and quotas
- Security hardening
- Production deployment guides

**Success Criteria:**
- API stability guaranteed for v1.0
- System scales horizontally
- Enterprise-ready authentication
- Production monitoring comprehensive
- Security audit passed

**See:** [v0.7.0/README.md](./v0.7.0/README.md)

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

| Feature | v0.2.2 | v0.2.3-6 | v0.2.7 | v0.3.0 | v0.4.0 | v0.5.0 | v0.6.0 | v0.7.0 |
|---------|--------|----------|--------|--------|--------|--------|--------|--------|
| **Status** | Current | Planned | Planned | Planned | Planned | Planned | Planned | Planned |
| **Hours** | - | 44-59 | 80-100 | 180-220 | 160-200 | 140-180 | 120-150 | 150-200 |
| **Focus** | - | Bugs | UX/Perf | RAG | Memory | Vision | Optimise | Production |
| Web UI | ⚠️ Degraded | ✅ Fixed | ✅ Enhanced | ✅ | ✅ | ✅ Vision | ✅ | ✅ Enterprise |
| Model Switching | ❌ | ❌ | ✅ | ✅ | ✅ | ✅ | ✅ Auto | ✅ |
| Collections | ❌ | ❌ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Caching | ❌ | ❌ | ✅ | ✅ | ✅ | ✅ | ✅ Smart | ✅ |
| HyDE | ❌ | ❌ | ❌ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Reranking | ❌ | ❌ | ❌ | ✅ | ✅ | ✅ | ✅ | ✅ |
| RAGAS Eval | ❌ | ❌ | ❌ | ✅ | ✅ | ✅ | ✅ Analytics | ✅ |
| Knowledge Graph | ❌ | ❌ | ❌ | ❌ | ✅ | ✅ | ✅ | ✅ |
| Personal Memory | ❌ | ❌ | ❌ | ❌ | ✅ | ✅ | ✅ | ✅ |
| Vision Retrieval | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ | ✅ | ✅ |
| Query Routing | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ | ✅ |
| Domain Adaptation | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ | ✅ |
| API Versioning | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ |
| Enterprise Auth | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ |
| Horizontal Scale | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ |

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
