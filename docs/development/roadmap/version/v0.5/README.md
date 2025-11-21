# Ragged v0.5.x Roadmap - ColPali Vision Integration

**Status:** Planned (restructured into 7-8 minor versions)

**Total Hours:** 191-257 hours across 7-8 minor versions

**Focus:** Multi-modal document understanding with vision-based retrieval

**Breaking Changes:** None

---

## Overview

Version 0.5.x introduces ColPali vision integration for multi-modal document understanding through a series of **7-8 balanced minor releases**. Each minor version delivers working functionality with clear dependencies and autonomous implementation capability.

**Key Deliverables (Across v0.5.x):**
- Vision embeddings for PDF pages (768-dimensional ColPali embeddings)
- Dual text+vision storage in ChromaDB
- Multi-modal queries (text, image, hybrid)
- Intelligent GPU resource management
- Comprehensive CLI for all vision features
- Demo web UI (Gradio) for stakeholder demonstrations
- Integration testing and quality assurance
- User documentation and tutorials
- Security hardening and production readiness

**Dependencies:** Requires v0.4.0 completion (knowledge graphs and personal memory)

**GPU Requirements:**
- Recommended: CUDA-compatible GPU (8GB+ VRAM) or Apple Silicon (MPS)
- Fallback: CPU-only mode supported (slower)

---

## Strategic Decisions

### Web UI Strategy

**v0.5.4:** Gradio demo UI (24-32 hours)
- Quick demonstration interface for stakeholders
- Proof-of-concept for vision features
- Auto-generated REST API for UI-backend communication
- **Purpose:** Early feedback, not production-quality

**v0.6.1:** Svelte/SvelteKit state-of-the-art UI (70-100 hours)
- Production-quality modern interface
- Split-screen document preview with highlighting
- Interactive knowledge graph visualization
- Token streaming, mobile-responsive, PWA-capable
- **Purpose:** End-user production interface

**Rationale:** Build quick demo in v0.5.4, invest in production UI once features stabilize in v0.6.x

**Alternative:** CLI-only for v0.5.x (skip Gradio), build Svelte directly in v0.6.x (cleaner architecture)

### API Strategy

**v0.6.0:** FastAPI layer (30-40 hours)
- RESTful API with automatic OpenAPI documentation
- Type-safe with Pydantic v2
- Document management, query operations, monitoring endpoints
- **Purpose:** Foundation for v0.6.1 Svelte UI and external developers

**v0.6.2:** Public API launch (10-15 hours)
- API versioning (/v1/...)
- Rate limiting and authentication
- Client SDKs (Python, JavaScript)
- External developer documentation

**Rationale:** Wait for v0.5 vision features to stabilize before committing to public API contract

**Alternative:** Include FastAPI in v0.5.5-v0.5.6 if external development needed earlier

---

## Minor Version Progression

### Version Overview Table

| Version | Focus | Features | Hours | Cumulative | Dependencies |
|---------|-------|----------|-------|------------|--------------|
| **v0.5.0** | Foundation | ColPali + Dual Storage | 55-75 | 55-75 | v0.4.0 |
| **v0.5.1** | Infrastructure | GPU Management | 18-24 | 73-99 | v0.5.0 |
| **v0.5.2** | Retrieval | Vision Queries | 28-38 | 101-137 | v0.5.0 |
| **v0.5.3** | CLI | Command Interface | 16-22 | 117-159 | v0.5.0-v0.5.2 |
| **v0.5.4** | Demo UI | Gradio Web Interface | 24-32 | 141-191 | v0.5.0-v0.5.3 |
| **v0.5.5** | Testing | Integration & E2E | 12-16 | 153-207 | v0.5.0-v0.5.4 |
| **v0.5.6** | Documentation | Tutorials & Guides | 20-26 | 173-233 | v0.5.0-v0.5.5 |
| **v0.5.7** | Security | Hardening & Reliability | 18-24 | 191-257 | v0.5.0-v0.5.6 |

**Average per version:** 24-32 hours (matches v0.3.x pattern)
**Timeline estimate:** 13-17 weeks @ 15 hours/week

---

## Minor Version Detailed Roadmaps

Each minor version below includes implementation checklist, success criteria, and hour breakdown. Click through to see detailed execution plans.

### [v0.5.0: Foundation - ColPali + Dual Storage](./v0.5.0.md)

**Hours:** 55-75 | **Dependencies:** v0.4.0

**Features:**
- VISION-001: ColPali vision embedder (768-dim embeddings)
- VISION-002: Dual text+vision storage in ChromaDB
- Migration utilities (v0.4 → v0.5 schema)
- Basic GPU/MPS/CPU device detection

**Delivers:** Working vision embeddings, dual storage schema, migration path

---

### [v0.5.1: Infrastructure - GPU Management](./v0.5.1.md)

**Hours:** 18-24 | **Dependencies:** v0.5.0

**Features:**
- VISION-004: GPU resource management
- Device manager (CUDA > MPS > CPU priority)
- Memory monitoring and OOM prevention
- Adaptive batch sizing

**Delivers:** Robust GPU handling, prevents OOM crashes, auto-scales batch sizes

---

### [v0.5.2: Retrieval - Vision Queries](./v0.5.2.md)

**Hours:** 28-38 | **Dependencies:** v0.5.0

**Features:**
- VISION-003: Multi-modal query processing
- VisionRetriever (text/image/hybrid queries)
- Visual reranking and boosting
- RRF score fusion

**Delivers:** Full multi-modal retrieval capability, visual content-aware search

---

### [v0.5.3: CLI - Command Interface](./v0.5.3.md)

**Hours:** 16-22 | **Dependencies:** v0.5.0-v0.5.2

**Features:**
- VISION-005: CLI commands
- Ingestion: `pdf`, `batch`, `status`
- Queries: `text`, `image`, `hybrid`, `interactive`
- GPU/Storage: `list`, `info`, `stats`, `benchmark`, `migrate`

**Delivers:** Complete CLI for all vision features, power-user interface

---

### [v0.5.4: Demo UI - Gradio Web Interface](./v0.5.4.md)

**Hours:** 24-32 | **Dependencies:** v0.5.0-v0.5.3

**Features:**
- VISION-006: Gradio web application
- Document upload (single & batch)
- Multi-modal query interface
- GPU monitoring dashboard
- Results display with visual badges

**Delivers:** Demo web UI for stakeholder demonstrations, proof-of-concept

**Note:** Gradio is for MVP/demo purposes. State-of-the-art Svelte UI planned for v0.6.1.

---

### [v0.5.5: Testing - Integration & E2E](./v0.5.5.md)

**Hours:** 12-16 | **Dependencies:** v0.5.0-v0.5.4

**Features:**
- Integration test suite (all 6 features)
- E2E workflow tests (ingest → query → retrieve)
- Performance benchmarks
- Cross-platform validation (CUDA/MPS/CPU)

**Delivers:** Quality assurance, performance validation, platform compatibility verified

---

### [v0.5.6: Documentation - Tutorials & Guides](./v0.5.6.md)

**Hours:** 20-26 | **Dependencies:** v0.5.0-v0.5.5

**Features:**
- Manual testing procedures (all 15 manual tests)
- Tutorial: "Getting Started with Vision RAG"
- Tutorial: "Multi-Modal Query Strategies"
- Tutorial: "GPU Configuration & Optimization"
- Example notebooks with real PDFs
- API documentation complete

**Delivers:** User onboarding materials, manual testing documentation, examples

---

### [v0.5.7: Security - Hardening & Reliability](./v0.5.7.md)

**Hours:** 18-24 | **Dependencies:** v0.5.0-v0.5.6

**Features:**
- Security audit (codebase-security-auditor agent)
- Visual PII detection validation
- Error recovery testing (OOM, missing GPU, corrupted PDFs)
- Encryption verification for vision data
- GDPR compliance for visual content
- Production deployment guide

**Delivers:** Production-ready v0.5.x, security validated, deployment guide

---

## Success Criteria

Success criteria are detailed in each minor version document. High-level requirements across v0.5.x:

### Functional Requirements by Version

**v0.5.0 (Foundation):**
- [ ] ColPali model loads on CUDA, MPS, CPU
- [ ] Vision embeddings generated (768-dim)
- [ ] Dual storage schema working
- [ ] Migration from v0.4 successful

**v0.5.1 (GPU Management):**
- [ ] Device detection: CUDA > MPS > CPU
- [ ] OOM recovery functional
- [ ] Adaptive batch sizing works
- [ ] Memory monitoring accurate

**v0.5.2 (Retrieval):**
- [ ] Text/image/hybrid queries work
- [ ] Visual boosting increases diagram scores
- [ ] RRF score fusion accurate
- [ ] Backward compatibility maintained

**v0.5.3 (CLI):**
- [ ] All CLI commands functional
- [ ] Help text comprehensive
- [ ] Error messages clear
- [ ] Progress indicators work

**v0.5.4 (Demo UI):**
- [ ] Gradio UI launches
- [ ] Document upload works
- [ ] Multi-modal queries via UI
- [ ] GPU dashboard functional

**v0.5.5 (Testing):**
- [ ] Integration tests pass
- [ ] E2E workflows validated
- [ ] Performance targets met
- [ ] Cross-platform verified

**v0.5.6 (Documentation):**
- [ ] Manual tests documented
- [ ] Tutorials complete
- [ ] Examples validated
- [ ] API docs comprehensive

**v0.5.7 (Security):**
- [ ] Security audit passed
- [ ] Visual PII detection works
- [ ] Error recovery validated
- [ ] Production guide complete

### Quality Gates (End of v0.5.7)

**Test Coverage:**
- [ ] Unit tests: 85%+ for vision modules
- [ ] Integration: All features tested
- [ ] E2E: Complete workflows pass
- [ ] Performance: All targets met

**Performance Targets:**
- [ ] Vision embedding: <5s/page (GPU), <15s (CPU)
- [ ] Text query: <200ms
- [ ] Image query: <500ms
- [ ] Hybrid query: <600ms
- [ ] GPU memory: <8GB standard workloads

**Code Quality:**
- [ ] Type hints: 100% public methods
- [ ] British English: All text
- [ ] Linters: No errors (ruff, mypy)
- [ ] Conventions: ragged standards followed

**Documentation:**
- [ ] Implementation docs: All 6 features
- [ ] CLI docs: Complete with examples
- [ ] Tutorials: 3+ validated
- [ ] Manual tests: 15 procedures documented

### Manual Testing (v0.5.6)

Detailed manual testing procedures documented in v0.5.6. Key categories:

- **Visual Content:** Diagrams, tables, charts, layout capture
- **Multi-Modal Queries:** Text+image, visual similarity, hybrid precision
- **Cross-Platform:** CUDA, MPS, CPU compatibility
- **GPU Management:** OOM recovery, batch adaptation, memory tracking

---

## Known Risks & Limitations

**Technical:**
- **GPU Requirements:** ColPali requires 4-8GB VRAM (may exclude CPU-only users)
- **Storage Overhead:** Vision embeddings approximately double storage needs
- **Model Size:** ColPali model is ~1.2GB (slow initial download, ~5-10 minutes)
- **Cross-Modal Gap:** Text and vision embeddings in different semantic spaces (no direct comparison)

**Implementation:**
- **Minor Version Dependencies:** Later versions depend on earlier (must implement in sequence)
- **Performance Tuning:** Optimal batch sizes vary by hardware (adaptive sizing helps but not perfect)
- **Gradio Limitations:** v0.5.4 UI is demo-quality, not production (replaced in v0.6.1)

**Dependencies:**
- **PyTorch Required:** Adds ~500MB to installation size
- **GPU Drivers:** Users need CUDA 11.8+/ROCm 5.4+ (NVIDIA/AMD) or macOS 12+ (Apple Silicon)

---

## Deferred to v0.6.x and Beyond

**Not Included in v0.5.x:**

1. **State-of-the-Art Web UI (v0.6.1):**
   - Production Svelte/SvelteKit interface (70-100h)
   - Split-screen document preview
   - Interactive graph visualisation
   - Mobile-responsive, PWA-capable

2. **FastAPI Layer (v0.6.0):**
   - RESTful API with OpenAPI docs (30-40h)
   - External developer integrations
   - Client SDKs (Python, JavaScript)

3. **Advanced Features (v0.6.x+):**
   - Page thumbnail rendering (requires PDF rendering integration)
   - Learned fusion weights (vs fixed text/vision weights)
   - Cross-modal alignment (shared embedding space)
   - Multi-GPU parallelism
   - Model quantization (INT8/FP16)

**Rationale:** Focus v0.5.x on core vision capabilities, build production interfaces once features stabilize

---

## Version Selection Guide

**Starting v0.5.x implementation? Recommended sequence:**

1. **Start with v0.5.0** (Foundation) - Largest version (55-75h) but unavoidable
2. **Proceed to v0.5.1** (GPU Management) - Critical before heavy processing in v0.5.2
3. **Consider parallel work:** v0.5.3 (CLI) and v0.5.4 (Web UI) can be developed in parallel after v0.5.2
4. **Don't skip v0.5.6** (Documentation) - Critical for user adoption
5. **v0.5.7 is mandatory** (Security) - Required before production deployment

**Each version is shippable** - delivers working functionality with value at every stage

---

## Hour Breakdown Summary

| Version | Category | Hours | Cumulative |
|---------|----------|-------|------------|
| v0.5.0 | Foundation | 55-75 | 55-75 |
| v0.5.1 | Infrastructure | 18-24 | 73-99 |
| v0.5.2 | Retrieval | 28-38 | 101-137 |
| v0.5.3 | CLI | 16-22 | 117-159 |
| v0.5.4 | Demo UI | 24-32 | 141-191 |
| v0.5.5 | Testing | 12-16 | 153-207 |
| v0.5.6 | Documentation | 20-26 | 173-233 |
| v0.5.7 | Security | 18-24 | 191-257 |
| **Total** | | **191-257h** | |

**Timeline:** 13-17 weeks @ 15 hours/week (single developer)

---

## Next Steps After v0.5.x

**v0.6.x: Modern Stack + Intelligent Optimisation (110-155h)**

- **v0.6.0:** FastAPI layer (30-40h)
- **v0.6.1:** Svelte/SvelteKit UI (70-100h)
- **v0.6.2:** Public API launch (10-15h)
- **v0.6.3+:** Query routing, domain adaptation, analytics

**v1.0: Production Stability (40-60h)**

- API stability guarantee (semantic versioning)
- Admin panel
- PWA enhancements
- Multi-user authentication

**Prerequisites for v0.5.0:**
- [ ] v0.4.0 complete (knowledge graphs, personal memory)
- [ ] GPU testing infrastructure set up
- [ ] Test PDFs with diagrams/tables/charts prepared
- [ ] Development environment: Python 3.10+, 16GB+ RAM

---

## Related Documentation

**Minor Version Roadmaps:**
- [v0.5.0: ColPali + Dual Storage](./v0.5.0.md)
- [v0.5.1: GPU Management](./v0.5.1.md)
- [v0.5.2: Vision Retrieval](./v0.5.2.md)
- [v0.5.3: CLI Integration](./v0.5.3.md)
- [v0.5.4: Gradio Web UI](./v0.5.4.md)
- [v0.5.5: Integration Testing](./v0.5.5.md)
- [v0.5.6: Documentation & Tutorials](./v0.5.6.md)
- [v0.5.7: Security & Reliability](./v0.5.7.md)

**Detailed Feature Implementation:**
- [VISION-001: ColPali Integration](./features/VISION-001-colpali-integration.md) (~450 lines, code examples)
- [VISION-002: Dual Storage](./features/VISION-002-dual-storage.md) (~700 lines, code examples)
- [VISION-003: Vision Retrieval](./features/VISION-003-vision-retrieval.md) (~850 lines, code examples)
- [VISION-004: GPU Management](./features/VISION-004-gpu-management.md) (~900 lines, code examples)
- [VISION-005: CLI Commands](./features/VISION-005-cli-commands.md) (~900 lines, code examples)
- [VISION-006: Web UI](./features/VISION-006-web-ui.md) (~1000 lines, code examples)
- [Testing Specification](./testing.md) (~600 lines, test examples)

**Context:**
- [Previous Version: v0.4.x](../v0.4/README.md) - Personal memory & knowledge graphs
- [Next Version: v0.6.x](../v0.6/README.md) - FastAPI + Svelte UI + intelligent optimisation
- [Planning: v0.5 Design Goals](../../planning/version/v0.5/) - What & why
- [Version Overview](../README.md) - Complete version comparison

---

**Status:** Planned - Implementation-Ready (7-8 balanced minor versions)
