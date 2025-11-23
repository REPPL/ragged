# ragged Development Roadmap - All Versions

**Planning Horizon:** v2.0.0 (~790-1035 total hours remaining)

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
Completed   v0.2.2 ━━━ Base System ✅
            v0.2.3 ━━━ SKIPPED (resolved in v0.2.4-v0.2.5)
            v0.2.4 ━━━ High Priority Bugs ✅ (2025-11-17)
            v0.2.5 ━━━ Code Quality ✅ (2025-11-17)
            v0.2.6 ━━━ SKIPPED/DEFERRED
Current     v0.2.7 ━━━ CLI Refactoring (in progress)
            v0.2.8 ━━━ CLI Enhancements (in progress)
            ═════════════════════════════════════════ STABILITY
Next        v0.2.9 ━━━ Performance & Stability (42-53h)
            ═════════════════════════════════════════ FOUNDATION
            v0.3.x ━━━━━━━━━━━━━ Advanced RAG (437-501h, 13 releases)
            ═════════════════════════════════════════ ADVANCED
            v0.4.x ━━━━━━━━━━━━━ Personal Memory (195-242h, 10 releases)
            v0.5.0 ━━━━━━━━━━━━━ ColPali Vision (140-180h)
            ═════════════════════════════════════════ DATA & UI
            v0.6.0 ━━━━━━━━━━━━━ Data Connectivity & UI Foundation (80-120h)
            v0.7.0 ━━━━━━━━━━━━━ Enterprise Foundation (150-200h)
            v0.8.0 ━━━━━━━━━━━━━ Agent Capabilities (60-80h)
            v0.9.0 ━━━━━━━━━━━━━ Web UI Completion (120-180h)
            ═════════════════════════════════════════ COLLABORATION
Future      v1.5.0 ━━━━━━━━━━━━━ Collaboration & Multi-User (100-150h)
            ═════════════════════════════════════════ ENTERPRISE
            v2.0.0 ━━━━━━━━━━━━━ Enterprise & Applications (150-200h)
```

---

## Version Overview

### v0.2.3 - Critical Bugs (P0) (12-15 hours)

**Status:** SKIPPED - Critical bugs resolved in subsequent versions (v0.2.4, v0.2.5)
**Priority:** P0 - Was planned first
**Focus:** Blocking issues that prevent core functionality

**Resolution:**
- Critical bugs were addressed incrementally in v0.2.4 and v0.2.5
- API endpoints fixed
- Logger issues resolved
- Test coverage improved across multiple releases

**See:** v0.2.3/README.md

---

### v0.2.4 - High Priority Bugs (P1) (20-25 hours)

**Status:** ✅ COMPLETE (Released 2025-11-17)
**Priority:** P1
**Focus:** Significant quality and functionality improvements

- BUG-004: Custom exception system with hierarchical structure
- BUG-005: Secure path utilities with directory traversal protection
- BUG-007: ChromaDB metadata serialisation for complex types
- BUG-008: Hybrid retrieval implementation (sparse + dense)
- BUG-010: Comprehensive duplicate detection (file hash, content hash, similarity)
- BUG-011: Page tracking with citation support

**Achievement:**
- 100% test coverage for exceptions and path utilities
- All P1 bugs resolved
- 92 new tests added

**See:** v0.2.4/README.md | CHANGELOG

---

### v0.2.5 - Code Quality Improvements (13-20 hours)

**Status:** ✅ COMPLETE (Released 2025-11-17)
**Focus:** Code quality, type safety, and test coverage

- QUALITY-001: Settings side effects eliminated
- QUALITY-002: Exception handling improvements (26 handlers)
- QUALITY-003: Chunking test coverage (0% → 85%)
- QUALITY-004: Magic numbers extracted to constants (13 values)
- QUALITY-005: Comprehensive type hints (100% strict mypy compliance)
- QUALITY-006-012: Citation tests, TODO cleanup, integration tests

**Achievement:**
- Zero mypy --strict errors across 46 files
- +70 new tests added
- 100% test coverage for citation formatter
- ~15 hours (vs 13-20h estimated)

**See:** v0.2.5/README.md | CHANGELOG

---

### v0.2.6 - File Refactoring & Structure (12-19 hours)

**Status:** SKIPPED/DEFERRED - Structural improvements moved to later versions
**Priority:** P2
**Focus:** File organisation and code structure

**Note:**
- Large-scale file refactoring deferred to avoid churn
- Some improvements incorporated into v0.2.7-v0.2.8 CLI work
- Remaining structural changes scheduled for v0.3+ as needed

**See:** [v0.2.6/README.md](./v0.2/v0.2.6/README.md)

---

### v0.2.7 - CLI Structure Refactoring (estimated 80-100h, actual TBD)

**Status:** 🔄 IN PROGRESS (Current Version)
**Focus:** CLI architecture and command organisation

- CLI command modularisation (14 command modules created)
- Main entry point refactored (586→107 lines, 82% reduction)
- Command structure: add, cache, completion, config, docs, envinfo, exportimport, health, history, metadata, query, search, validate
- Batch processing with progress bars
- Folder ingestion with recursive scanning
- HTML processing support (Trafilatura + BeautifulSoup)

**In Progress:**
- Performance optimisations
- Additional CLI enhancements

**See:** [v0.2.7/README.md](./v0.2/v0.2.7/README.md)

---

### v0.2.8 - CLI Enhancements (planned 40-60h, actual TBD)

**Status:** 🔄 IN PROGRESS
**Focus:** Advanced CLI features and utilities

- Shell completion (completion command)
- Output formats (JSON, table formatters)
- Config validation command
- Environment info command
- Metadata management
- Search & filtering
- Query history & replay
- Export/import utilities
- Cache management
- Verbose/quiet modes

**In Progress:**
- Testing and documentation
- Integration with v0.2.7 features

**See:** v0.2.8/README.md

---

### v0.2.9 - Stability & Performance (42-53 hours)

**Status:** 📅 PLANNED - Next target after v0.2.7-v0.2.8 complete
**Focus:** Performance optimisation and system stability

**Planned Features:**
- Embedder caching (singleton pattern, 4-6x faster cold start)
- Batch embedding optimisation (dynamic sizing, 3-5x throughput)
- Query result caching (LRU/TTL, 10-20x faster repeat queries)
- Error recovery & resilience (retry, circuit breaker, graceful degradation)
- Memory management (dynamic monitoring, OOM prevention)
- Comprehensive logging (structured JSON, metrics, audit trails)

**Success Criteria:**
- Embedder init: <0.5s cold, <0.1s warm
- Repeat queries: <200ms
- No OOM crashes
- >95% error recovery rate
- >80% test coverage maintained

**See:** [v0.2.9/README.md](./v0.2/v0.2.9/README.md)

---

### v0.3.x - Advanced RAG Techniques (437-501 hours, 13 releases)

**Status:** Planning
**Focus:** State-of-the-art RAG capabilities across 13 incremental releases

**Release Structure:**
- **v0.3.1** - Foundation & metrics (30h)
- **v0.3.2** - Configuration transparency (28-34h)
- **v0.3.3** - Advanced query processing (53-55h)
- **v0.3.4** - Chunking strategies (58-65h)
- **v0.3.5** - Modern OCR (Docling) (50-55h)
- **v0.3.6** - Messy document handling (23-25h)
- **v0.3.7** - VectorStore abstraction (35-40h)
- **v0.3.8** - Production data & generation (68-74h)
- **v0.3.9-v0.3.13** - Developer experience tools (92-120h)

**Key Features:**
- RAGAS evaluation framework
- Query decomposition, reranking, HyDE
- Semantic chunking, hierarchical strategies
- Modern OCR (30× performance improvement)
- Automated messy PDF handling
- Versioned documents, rich queries
- Interactive REPL, profiling, dashboards

**Success Criteria:**
- RAGAS scores >0.80
- Measurable quality improvements for each technique
- Production-ready tooling

**See:** [v0.3/README.md](./v0.3/README.md)

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

**See:** [v0.4/README.md](./v0.4/README.md)

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

**See:** [v0.5/README.md](./v0.5/README.md)

---

### v0.6.0 - Data Connectivity & UI Foundation (80-120 hours)

**Status:** Planned
**Focus:** Expand data sources and establish modern web UI

**Key Features:**
- Cloud connectors (Google Drive, Dropbox, Notion)
- Folder watch automation (PrivateGPT-inspired)
- Svelte/SvelteKit web UI foundation
- REST API stabilisation (OpenAPI spec)
- Document library and search interface

**Strategic Context:**
- Addresses ecosystem gap: automated ingestion and professional UI
- Brings ragged in line with PrivateGPT's folder watch
- Begins UI modernisation toward AnythingLLM-level polish

**Success Criteria:**
- Cloud connectors authenticate and sync correctly
- Folder watch auto-ingests within 30 seconds
- UI responsive on mobile and desktop
- API versioned and documented (OpenAPI)

**See:** [v0.6/README.md](./v0.6/README.md)

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

**See:** [v0.7/README.md](./v0.7/README.md)

---

### v0.8.0 - Agent Capabilities (60-80 hours)

**Status:** Planned
**Focus:** Intelligent agents for complex workflows and tool use

**Key Features:**
- Agent framework (planner, executor, tools)
- Tool library (RAG tools + external tools)
- Visual workflow builder backend (JSON workflows)
- Multi-agent orchestration (experimental)
- CLI agent commands and templates

**Strategic Context:**
- Addresses major ecosystem gap: agentic workflows
- Inspired by RAGFlow's multi-agent orchestration
- Brings no-code agent capabilities (AnythingLLM-inspired)
- Maintains privacy-first principles (local-only agents)

**Success Criteria:**
- Agents execute multi-step tasks successfully (>80% success rate)
- Tool library complete and safe
- Workflow backend functional (ready for v0.9 UI)
- CLI agent templates accelerate adoption

**See:** [v0.8/README.md](./v0.8/README.md)

---

### v0.9.0 - Web UI Completion (120-180 hours)

**Status:** Planned
**Focus:** Complete modern web interface with advanced features

**Key Features:**
- Block-based editor (TipTap, Notion-inspired)
- Command palette (Cmd+K, VS Code-inspired)
- Knowledge graph visualization (interactive D3.js/Cytoscape)
- Visual workflow editor (RAGFlow-inspired DAG editor)
- Dark mode & theming
- Progressive Web App (PWA, offline support)
- Advanced document library (faceted search, virtual scrolling)
- Mobile responsive design

**Strategic Context:**
- Achieves AnythingLLM-level UI polish
- Adds RAGFlow's visual workflow editor
- Completes transformation from Gradio to professional web app
- Enables daily-driver usage

**Success Criteria:**
- Block editor performance <100ms per keystroke
- Graph visualization handles 1,000+ nodes smoothly
- Workflow editor supports 50+ node workflows
- PWA scores 90+ on Lighthouse
- All features accessible on mobile

**See:** [v0.9/README.md](./v0.9/README.md)

---

### v1.5.0 - Collaboration & Multi-User (100-150 hours)

**Status:** Planned
**Focus:** Team collaboration and document sharing

**Key Features:**
- Multi-user foundation (workspaces, teams)
- Document sharing & granular permissions (RBAC + ACL)
- Real-time collaboration (Yjs CRDT)
- Team workflows (shared agents, templates)
- Conversation sharing and comments
- Notifications & activity feed
- Optional end-to-end encryption

**Strategic Context:**
- Transforms ragged from personal to team tool
- Inspired by Onyx/Danswer's permission mirroring
- Adds AnythingLLM's team capabilities
- Maintains privacy-first with optional E2EE

**Success Criteria:**
- Data isolation between workspaces enforced
- Real-time collaboration supports 10+ concurrent users
- Permission checks add <50ms query latency
- Migration preserves 100% of single-user data
- Zero permission bypass vulnerabilities

**Note:** Major pivot toward team collaboration—validate demand before implementation

**See:** [v1.5/README.md](./v1.5/README.md)

---

### v2.0.0 - Enterprise & Applications (150-200 hours)

**Status:** Planned
**Focus:** Enterprise compliance and native applications

**Key Features:**
- HIPAA compliance (encryption at rest, comprehensive audit logs)
- SOC2 Type II compliance (MFA, security controls, monitoring)
- Air-gapped deployment (offline installer, no internet dependency)
- Desktop applications (Electron: macOS/Windows/Linux)
- Browser extension (Chrome/Firefox web clipper)
- Embeddable widget (one-line integration)
- Advanced observability (Jaeger tracing, Grafana dashboards)

**Strategic Context:**
- Enterprise parity with Onyx/Danswer
- Desktop apps like AnythingLLM
- Air-gapped like LocalGPT for regulated industries
- Completes transformation to enterprise-ready platform

**Success Criteria:**
- HIPAA audit logs capture 100% of PHI access
- Air-gap deployment functional with zero internet requests
- Desktop apps <200MB (all platforms)
- Browser extension works in Chrome/Firefox/Edge/Safari
- Widget loads <2 seconds, works on mobile
- Zero compliance violations in testing

**Note:** Enterprise pivot—consider separate "Enterprise Edition" to fund development

**See:** [v2.0/README.md](./v2.0/README.md)

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

| Feature | v0.3.0 | v0.4.0 | v0.5.0 | v0.6.0 | v0.7.0 | v0.8.0 | v0.9.0 | v1.5 | v2.0 |
|---------|--------|--------|--------|--------|--------|--------|--------|------|------|
| **Status** | Planned | Planned | Planned | Planned | Planned | Planned | Planned | Planned | Planned |
| **Hours** | 180-220 | 160-200 | 140-180 | 80-120 | 150-200 | 60-80 | 120-180 | 100-150 | 150-200 |
| **Focus** | RAG | Memory | Vision | Data/UI | Enterprise | Agents | UI Polish | Collab | Enterprise Apps |
| Advanced RAG | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Knowledge Graph | ❌ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ KG Viz | ✅ | ✅ |
| Personal Memory | ❌ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Vision Retrieval | ❌ | ❌ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Cloud Connectors | ❌ | ❌ | ❌ | ✅ GDrive/Dropbox/Notion | ✅ | ✅ | ✅ | ✅ | ✅ |
| Folder Watch | ❌ | ❌ | ❌ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Svelte UI | ❌ | ❌ | ❌ | ✅ Foundation | ✅ | ✅ | ✅ Complete | ✅ | ✅ |
| API Versioning | ❌ | ❌ | ❌ | ✅ OpenAPI | ✅ | ✅ | ✅ | ✅ | ✅ |
| Enterprise Auth | ❌ | ❌ | ❌ | ❌ | ✅ JWT/RBAC | ✅ | ✅ | ✅ MFA | ✅ |
| Agents | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ | ✅ Visual | ✅ Team | ✅ |
| Block Editor | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ | ✅ Realtime | ✅ |
| Command Palette | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ | ✅ | ✅ |
| PWA | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ | ✅ | ✅ |
| Multi-User | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ | ✅ |
| Collaboration | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ CRDT | ✅ |
| HIPAA | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ |
| Desktop Apps | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ |
| Browser Ext | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ |
| Embeddable Widget | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ |

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

**This is a living roadmap.** Versions may shift based on feedback, priorities may change based on user needs, and timeline estimates may adjust based on complexity.
