# ragged v0.3.0 Implementation Roadmap

**Version:** v0.3.0 - Production-Ready RAG System

**Status:** Ready for Implementation

---

## Executive Summary

This roadmap breaks v0.3.0 (437-501 hours total) into **13 minor releases** delivered over 6-8 months. Each release focuses on specific categories (Core Functionality, Document Intelligence, Configuration, CLI Enhancements) and delivers shippable value.

**Key Innovations:**
- **Modern OCR Stack:** Docling + PaddleOCR (replacing Tesseract) - 30× faster
- **Automated Messy PDF Handling:** Zero user intervention for document correction
- **Configuration Personas:** User-friendly "accuracy", "speed", "balanced" profiles
- **Transparent Processing:** Users always know what ragged is doing
- **Production-Ready:** REST API, monitoring, automation, accessibility
- **Proper Agent Usage:** Documentation quality maintained throughout

---

## Security & Privacy Foundation (REQUIRED)

**⚠️ CRITICAL PREREQUISITE:** All v0.3.x versions depend on the security and privacy infrastructure established in v0.2.10 and v0.2.11. These versions **MUST be completed before implementing any v0.3.x features**.

### Why Required

v0.3.x introduces features that store and process user data:
- **v0.3.0 (REPL):** Command history and session files
- **v0.3.0 (Metrics DB):** Query logs and performance data
- **v0.3.0 (REST API):** Multi-user sessions and API requests

Without v0.2.10 and v0.2.11, these features would:
- ❌ Use insecure Pickle serialisation (arbitrary code execution vulnerability)
- ❌ Store queries in plaintext (PII exposure)
- ❌ Allow cross-user data leakage (global caches)
- ❌ Keep user data indefinitely (privacy violation)

### Security Foundation (v0.2.10)

**Status:** Must be completed before v0.3.1

**Estimated Time:** 15-21 hours

**Provides:**
- JSON serialisation (eliminates Pickle vulnerability)
- Session isolation (UUID-based session IDs)
- Session-scoped caching (prevents cross-user leakage)
- Security testing framework
- Pre-commit security validation

**[→ v0.2.10 Roadmap](../../v0.2/v0.2.10/)**

### Privacy Infrastructure (v0.2.11)

**Status:** Must be completed before v0.3.1

**Estimated Time:** 20-26 hours

**Provides:**
- Encryption at rest (Fernet/AES-128)
- PII detection and redaction
- Query hashing (SHA-256 for logs/metrics)
- TTL-based data lifecycle management
- GDPR compliance foundations (deletion, export, access rights)
- Privacy configuration system

**[→ v0.2.11 Roadmap](../../v0.2/v0.2.11/)**

### How v0.3.x Uses the Foundation

All v0.3.x features integrate with v0.2.10/v0.2.11:

| v0.3 Feature | Security Integration | Privacy Integration |
|--------------|---------------------|---------------------|
| **v0.3.0 REPL** | Session isolation | Encrypted session files, PII warnings, TTL cleanup |
| **v0.3.0 Metrics** | Session-scoped DB | Query hashing (NOT plaintext), TTL cleanup, GDPR export |
| **v0.3.0 REST API** | Per-client sessions | Session-scoped caching, query hashing, audit logs |

**Privacy Risk Scores:**
- v0.3.0 (REPL): 90/100
- v0.3.0 (Metrics): 95/100
- v0.3.0 (REST API): 92/100

See detailed privacy implementation sections in each version's roadmap file.

### Total Time Investment

**Security & Privacy Foundation:** 35-47 hours (BEFORE v0.3.x)

**v0.3.x Implementation:** 437-501 hours

**Combined Total:** 472-548 hours

This foundation is a **one-time investment** that protects ragged users and ensures compliance with privacy regulations from the start.

---

## Feature Specifications

For detailed technical specifications organised by feature area, see the **[features/](./features/)** directory. These documents provide comprehensive implementation details, code examples, and integration guidance for each major feature area.

| Feature | Description | Versions | Effort | Privacy Risk |
|---------|-------------|----------|--------|--------------|
| [Query Processing](./features/query-processing.md) | Query decomposition, HyDE, reranking, contextual compression | v0.3.0, v0.3.0, v0.3.0 | 50-63h | 88/100 |
| [Chunking Strategies](./features/chunking-strategies.md) | Semantic and hierarchical chunking with parent-child relationships | v0.3.0 | 38-46h | 90/100 |
| [Multi-Modal Support](./features/multi-modal-support.md) | Docling + PaddleOCR integration for OCR, tables, images, charts | v0.3.0 | 57-71h | 75/100 |
| [RAGAS Evaluation](./features/evaluation-quality.md) | RAGAS framework integration, MRR, NDCG metrics (target >0.80) | v0.3.0, v0.3.0, v0.3.0, v0.3.0 | 32-38h | 85/100 |
| [Data Generation](./features/data-generation.md) | Chain-of-thought reasoning, enhanced citations, metadata filtering, auto-tagging | v0.3.0 | 68-74h | 85/100 |
| [CLI Features](./features/cli-features.md) | Interactive REPL, debug mode, session management | v0.3.0 | 20-26h | 90/100 |

### High-Risk Features (Privacy/Security Attention Required)

These features require careful attention to privacy and security implementation:

- **CLI REPL** (v0.3.0) - Privacy Risk: 90/100
  - **Risks:** Session history contains sensitive user queries, persistent session state
  - **Mitigations:** Session isolation (v0.2.10), encrypted session files (v0.2.11), PII warnings, TTL cleanup
  - **Integration:** SessionManager, EncryptionManager, contains_pii(), hash_query()

- **Multi-Modal Processing** (v0.3.0) - Privacy Risk: 75/100
  - **Risks:** File uploads from external sources, temporary file handling, OCR of sensitive documents
  - **Mitigations:** Temporary file cleanup, session-scoped processing, no external API calls (local-only)
  - **Integration:** Session isolation for temporary files

- **Evaluation & Metrics** (v0.3.0, v0.3.0) - Privacy Risk: 85/100
  - **Risks:** Query logging for metrics, performance data storage
  - **Mitigations:** Query hashing (NOT plaintext), TTL-based cleanup, GDPR export/deletion
  - **Integration:** hash_query(), CleanupScheduler, GDPR compliance APIs

- **Data Generation** (v0.3.0) - Privacy Risk: 85/100
  - **Risks:** Auto-tagging processes document content, metadata storage
  - **Mitigations:** Local LLM processing only, session-scoped metadata, no external APIs
  - **Integration:** Session isolation for metadata

See detailed privacy implementation sections in each feature specification and version roadmap.

---

## Quick Navigation

### By Implementation Sequence
1. [v0.3.0 - Foundation & Metrics](#v030---foundation--metrics-30-hours) (30h)
2. [v0.3.0 - Configuration Transparency](#v031---configuration-transparency-28-34-hours) (28-34h)
3. [v0.3.0 - Advanced Query Processing](#v032---advanced-query-processing-53-55-hours) (53-55h)
4. [v0.3.0 - Intelligent Chunking](#v033---intelligent-chunking-38-40-hours) (38-40h)
5. [v0.3.0 - Modern Document Processing](#v034---modern-document-processing-55-62-hours) (55-62h)
6. [v0.3.0 - Messy Document Intelligence](#v035---messy-document-intelligence-49-57-hours) (49-57h)
7. [v0.3.0 - VectorStore Abstraction](#v036---vectorstore-abstraction-16-22-hours) (16-22h)
8. [v0.3.0 - Production Data & Generation](#v037---production-data--generation-68-74-hours) (68-74h)
9. [v0.3.0 - Developer Experience I](#v038---developer-experience-i-20-24-hours) (20-24h)
10. [v0.3.0 - Performance & Quality Tools](#v039---performance--quality-tools-19-24-hours) (19-24h)
11. [v0.3.0 - Automation & Templates](#v0310---automation--templates-18-24-hours) (18-24h)
12. [v0.3.0 - Production Operations](#v0311---production-operations-17-23-hours) (17-23h)
13. [v0.3.0 - Polish & Integration](#v0312---polish--integration-26-32-hours) (26-32h)

### By Category
- **[Core Functionality](#category-core-functionality):** v0.3.0, v0.3.0 (91-95h)
- **[Document Intelligence](#category-document-intelligence):** v0.3.0, v0.3.0 (104-119h)
- **[Quality & Metrics](#category-quality--metrics):** v0.3.0, v0.3.0 (49-54h)
- **[Configuration & UX](#category-configuration--ux):** v0.3.0 (28-34h)
- **[Production Features](#category-production-features):** v0.3.0 (68-74h)
- **[Developer Experience](#category-developer-experience):** v0.3.0, v0.3.0, v0.3.0 (55-71h)
- **[API & Integration](#category-api--integration):** v0.3.0, v0.3.0 (42-54h)

---

## Execution Framework

### Recommended Implementation Sequence

The 13 versions are designed to be implemented **sequentially** with some flexibility for parallel work on independent features.

**⚠️ PREREQUISITE:** Complete v0.2.10 (Security Hardening) and v0.2.11 (Privacy Infrastructure) before starting v0.3.0. See [Security & Privacy Foundation](#security--privacy-foundation-required) above.

#### Phase 0: Security & Privacy Foundation (35-47h)
**Goal:** Establish security and privacy infrastructure

```
v0.2.10 (15-21h) → v0.2.11 (20-26h)
    ↓                   ↓
Security hardening   Privacy infrastructure
```

**Critical Path:** Must complete before ANY v0.3.x work
**Deliverable:** Session isolation, encryption, PII handling, GDPR compliance

#### Phase 1: Foundation (Weeks 1-7, 111-129h)
**Goal:** Establish quality metrics, configuration system, and core retrieval improvements

**Prerequisite:** v0.2.10 and v0.2.11 must be complete

```
v0.3.0 (30h) → v0.3.0 (28-34h) → v0.3.0 (53-55h)
   ↓              ↓                  ↓
RAGAS baseline  Personas         Advanced retrieval
```

**Critical Path:** Must complete in order
**Deliverable:** Measurable quality baseline + user-friendly configuration

---

#### Phase 2: Intelligence (Weeks 8-19, 142-159h)
**Goal:** Intelligent chunking and modern document processing

```
v0.3.0 (38-40h) ──→ v0.3.0 (55-62h) ──→ v0.3.0 (49-57h)
   ↓                   ↓                    ↓
Semantic chunking   Docling OCR         Auto-correction
```

**Dependencies:**
- v0.3.0 depends on v0.3.0 (chunking for processed documents)
- v0.3.0 depends on v0.3.0 (Docling integration for messy PDFs)

**Deliverable:** 30× faster OCR + automated messy PDF handling

---

#### Phase 3: Production Ready (Weeks 20-28, 100-118h)
**Goal:** Production features and API foundation

```
v0.3.0 (16-22h) ──→ v0.3.0 (68-74h)
   ↓                   ↓
VectorStore API     Production features
```

**Dependencies:**
- v0.3.0 depends on v0.3.0 (RAGAS metrics for chain-of-thought validation)

**Deliverable:** RAGAS > 0.80 + multi-backend support

---

#### Phase 4: Developer Experience (Weeks 29-37, 55-71h)
**Goal:** Developer tools, profiling, automation

```
       v0.3.0 (20-24h)
           ↓
   v0.3.0 (19-24h) ──→ v0.3.0 (18-24h) ──→ v0.3.0 (17-23h)
       ↓                    ↓                     ↓
   Profiling           Templates            Watch mode
```

**Dependencies:**
- v0.3.0 depends on v0.3.0 (metrics infrastructure)
- v0.3.0 depends on v0.3.0 (configuration validation)
- v0.3.0 depends on v0.3.0 (templates for scheduled operations)

**Deliverable:** Complete developer toolkit

---

#### Phase 5: Integration & Polish (Weeks 38-44, 26-32h)
**Goal:** REST API, accessibility, final documentation

```
v0.3.0 (26-32h)
    ↓
REST API + Accessibility + Complete docs
```

**Dependencies:** All v0.3.x features (integration testing)

**Deliverable:** Production-ready v0.3.0 release

---

### Dependency Graph

```
                    ┌─────────────────────────────────┐
                    │ SECURITY & PRIVACY FOUNDATION   │
                    │                                 │
                    │  v0.2.10 (Security Hardening)   │
                    │         +                       │
                    │  v0.2.11 (Privacy Infrastructure)│
                    └────────────┬────────────────────┘
                                 │
                                 │ (ALL v0.3.x depend on this)
                                 │
                    ┌────────────▼────────────────────┐
                    │      v0.3.x RELEASES            │
                    └─────────────────────────────────┘

v0.3.0 (Foundation & Metrics)
    ├─→ v0.3.0 (needs RAGAS)
    ├─→ v0.3.0 (session management)
    └─→ v0.3.0 (needs metrics infrastructure)

v0.3.0 (Configuration)
    ├─→ v0.3.0 (config for interactive mode)
    └─→ v0.3.0 (config validation)

v0.3.0 (Advanced Retrieval)
    └─→ v0.3.0 (query suggestions use decomposition)

v0.3.0 (Intelligent Chunking)
    └─→ v0.3.0 (chunking for processed docs)

v0.3.0 (Modern OCR)
    └─→ v0.3.0 (Docling for messy PDFs)

v0.3.0 (Interactive/Debug)
    └─→ v0.3.0 (debug mode for profiling)
    [Uses v0.2.10 Session, v0.2.11 encryption]

v0.3.0 (Performance Tools)
    [Uses v0.2.11 query hashing, TTL cleanup]
    [No v0.3.x dependents]

v0.3.0 (Templates)
    └─→ v0.3.0 (templates for scheduled operations)

v0.3.0, v0.3.0 → Independent

v0.3.0 (Final Integration)
    ↑
    All versions (integration testing)
    [Uses v0.2.10 session isolation, v0.2.11 privacy]
```

---

### Standard Implementation Workflow (Per Version)

Each version follows this standard workflow:

#### 1. Pre-Implementation (30min - 2h)
- [ ] Read version roadmap file (e.g., `v0.3.0.md`)
- [ ] Review dependencies (ensure prerequisites complete)
- [ ] Create feature branch: `git checkout -b feature/v0.3.X-name`
- [ ] Optional: Use architecture-advisor agent for complex design decisions
- [ ] Optional: Use ux-architect agent for user-facing features

#### 2. Implementation (varies by version)
- [ ] Follow execution checklist in version roadmap
- [ ] Write code following module structure
- [ ] Write unit tests as you go (target: 100% coverage for new code)
- [ ] Commit frequently with descriptive messages
- [ ] Run tests continuously

#### 3. Testing & Validation (10-20% of implementation time)
- [ ] Run full test suite
- [ ] Manual testing of new features
- [ ] Performance testing (where applicable)
- [ ] Check quality gates in version roadmap
- [ ] RAGAS evaluation (for retrieval/generation features)

#### 4. Documentation (Before Commit)
- [ ] Use documentation-architect agent (plan structure)
- [ ] Write/update user documentation
- [ ] Write/update API documentation
- [ ] Add usage examples
- [ ] Update CHANGELOG.md

#### 5. Quality Assurance (Before Commit)
- [ ] Use documentation-auditor agent (comprehensive review)
- [ ] Fix any issues found
- [ ] Verify all quality gates passed
- [ ] Verify British English compliance

#### 6. Commit & Release
- [ ] Use git-documentation-committer agent
- [ ] Or manually: `git add . && git commit` with AI attribution
- [ ] Tag release: `git tag v0.3.X`
- [ ] Push: `git push origin feature/v0.3.X-name`
- [ ] Update [Progress Tracking](#progress-tracking) section below

---

## Progress Tracking

### Version Completion Checklist

Track your progress through v0.3.x implementation:

- [ ] **v0.3.0** - Foundation & Metrics (30h)
  - [ ] RAGAS framework integrated
  - [ ] Baseline metrics established
  - [ ] Tests passing
  - [ ] Documentation complete

- [ ] **v0.3.0** - Configuration Transparency (28-34h)
  - [ ] Personas implemented
  - [ ] `ragged explain` command working
  - [ ] Presets functional
  - [ ] Tests passing
  - [ ] Documentation complete

- [ ] **v0.3.0** - Advanced Query Processing (53-55h)
  - [ ] Query decomposition working
  - [ ] HyDE implemented
  - [ ] Reranking functional
  - [ ] Contextual compression working
  - [ ] MRR@10 > 0.75 achieved
  - [ ] Tests passing
  - [ ] Documentation complete

- [ ] **v0.3.0** - Intelligent Chunking (38-40h)
  - [ ] Semantic chunking working
  - [ ] Hierarchical chunking functional
  - [ ] Parent-child retrieval working
  - [ ] Tests passing
  - [ ] Documentation complete

- [ ] **v0.3.0** - Modern Document Processing (55-62h)
  - [ ] Docling integrated
  - [ ] PaddleOCR fallback working
  - [ ] 30× performance improvement validated
  - [ ] Table extraction 97.9% accurate
  - [ ] Tests passing
  - [ ] Documentation complete

- [ ] **v0.3.0** - Messy Document Intelligence (49-57h)
  - [ ] PDF analysis working
  - [ ] Auto-correction functional
  - [ ] 98%+ OCR confidence achieved
  - [ ] Exceptional markdown generated
  - [ ] Tests passing
  - [ ] Documentation complete

- [ ] **v0.3.0** - VectorStore Abstraction (16-22h)
  - [ ] VectorStore interface complete
  - [ ] ChromaDB refactored
  - [ ] Zero breaking changes
  - [ ] Tests passing
  - [ ] Documentation complete

- [ ] **v0.3.0** - Production Data & Generation (68-74h)
  - [ ] Version tracking working
  - [ ] Metadata filtering functional
  - [ ] Auto-tagging working
  - [ ] Chain-of-thought reasoning functional
  - [ ] Enhanced citations working
  - [ ] RAGAS > 0.80 achieved
  - [ ] Tests passing
  - [ ] Documentation complete

- [ ] **v0.3.0** - Developer Experience I (20-24h)
  - [ ] Interactive REPL working
  - [ ] Debug mode functional
  - [ ] Session management working
  - [ ] Tests passing
  - [ ] Documentation complete

- [ ] **v0.3.0** - Performance & Quality Tools (19-24h)
  - [ ] Performance profiling working
  - [ ] Quality metrics dashboard functional
  - [ ] Historical tracking working
  - [ ] Tests passing
  - [ ] Documentation complete

- [ ] **v0.3.0** - Automation & Templates (18-24h)
  - [ ] Query templates working
  - [ ] Configuration validation functional
  - [ ] Benchmark testing working
  - [ ] Tests passing
  - [ ] Documentation complete

- [ ] **v0.3.0** - Production Operations (17-23h)
  - [ ] Watch mode working
  - [ ] Scheduled operations functional
  - [ ] Daemon mode stable
  - [ ] Tests passing
  - [ ] Documentation complete

- [ ] **v0.3.0** - Polish & Integration (26-32h)
  - [ ] REST API functional
  - [ ] Smart suggestions working
  - [ ] All 5 themes implemented
  - [ ] WCAG 2.1 AA compliance validated
  - [ ] Integration testing complete
  - [ ] Full documentation complete
  - [ ] v0.3.0 released

### Milestone Tracking

- [ ] **Milestone 1:** Foundation Complete (v0.3.0-v0.3.0)
  - Target: Weeks 1-7
  - Metrics baseline + User-friendly configuration

- [ ] **Milestone 2:** Core Retrieval Complete (v0.3.0-v0.3.0)
  - Target: Weeks 8-15
  - Advanced retrieval + Intelligent chunking

- [ ] **Milestone 3:** Modern OCR Complete (v0.3.0-v0.3.0)
  - Target: Weeks 16-25
  - 30× faster processing + Messy PDF handling

- [ ] **Milestone 4:** Production Ready (v0.3.0-v0.3.0)
  - Target: Weeks 26-32
  - Multi-backend + RAGAS > 0.80

- [ ] **Milestone 5:** Developer Tools Complete (v0.3.0-v0.3.0)
  - Target: Weeks 33-40
  - REPL + Profiling + Templates + Automation

- [ ] **Milestone 6:** v0.3.0 Released (v0.3.0)
  - Target: Weeks 41-44
  - REST API + Accessibility + Complete docs

---

## Total Effort Breakdown

### v0.3.x Only

| Category | Hours | Percentage |
|----------|-------|------------|
| Implementation | 334-390h | 68-78% |
| Documentation & Agents | 103-111h | 22-32% |
| **v0.3.x Total** | **437-501h** | **100%** |

### Including Security & Privacy Foundation

| Phase | Hours | Description |
|-------|-------|-------------|
| **v0.2.10 Security** | 15-21h | Pickle elimination, session isolation, security testing |
| **v0.2.11 Privacy** | 20-26h | Encryption, PII handling, TTL cleanup, GDPR compliance |
| **v0.3.x Implementation** | 437-501h | All 13 v0.3.x versions |
| **Combined Total** | **472-548h** | **Complete v0.3.0 with security foundation** |

**Timeline Estimates (Including v0.2.10 + v0.2.11):**
- At 10 hours/week: 47-55 weeks (11-13 months)
- At 15 hours/week: 31-37 weeks (7-9 months)
- At 20 hours/week: 24-28 weeks (6-7 months)

---

## Minor Version Releases

### v0.3.0 - Foundation & Metrics (30 hours)

**Category:** Quality & Evaluation Infrastructure

**Priority:** Critical (must complete first)

**Dependencies:** None

Establish metrics BEFORE any improvements to enable data-driven development.

**Key Features:**
- RAGAS framework integration (Context Precision, Recall, Faithfulness, Answer Relevancy)
- Baseline metrics establishment
- Citation tracking
- Evaluation utilities

**Deliverable:** Objective quality metrics, baseline scores for comparison

**[→ Detailed Roadmap](./v0.3.0.md)**

---

### v0.3.0 - Configuration Transparency (28-34 hours)

**Category:** User Experience & Configuration

**Priority:** High

**Dependencies:** None

Transparent, customisable configuration with personas.

**Key Features:**
- Configuration personas (accuracy, speed, balanced, research, quick-answer)
- Preset configurations
- `ragged explain` command
- Configuration validation

**Deliverable:** "accuracy", "speed", "balanced" profiles, transparent decision-making

**[→ Detailed Roadmap](./v0.3.0.md)**

---

### v0.3.0 - Advanced Query Processing (53-55 hours)

**Category:** Core Retrieval Functionality

**Priority:** Critical

**Dependencies:** v0.3.0 (RAGAS for evaluation)

State-of-the-art retrieval techniques.

**Key Features:**
- Query decomposition (complex → sub-queries)
- HyDE (Hypothetical Document Embeddings)
- Cross-encoder reranking
- Contextual compression

**Deliverable:** 10-20% quality improvement per technique, MRR@10 > 0.75

**[→ Detailed Roadmap](./v0.3.0.md)**

---

### v0.3.0 - Intelligent Chunking (38-40 hours)

**Category:** Core Chunking Intelligence

**Priority:** High

**Dependencies:** v0.3.0 (for testing with advanced retrieval)

Topic-coherent chunks with parent-child relationships.

**Key Features:**
- Semantic chunking (topic boundary detection)
- Hierarchical chunking (parent-child relationships)
- Dynamic chunk sizing
- Integration with existing pipeline

**Deliverable:** Semantic and hierarchical chunking strategies, 5-15% quality improvement

**[→ Detailed Roadmap](./v0.3.0.md)**

---

### v0.3.0 - Modern Document Processing (55-62 hours)

**Category:** State-of-the-Art OCR & Document Intelligence

**Priority:** Critical (architectural change)

**Dependencies:** v0.3.0 (chunking for processed documents)

Replace Tesseract + Camelot with Docling + PaddleOCR.

**Key Features:**
- Docling integration (primary processor)
- PaddleOCR fallback (messy documents)
- Quality-based routing
- 30× performance improvement
- 97.9% table extraction accuracy

**Deliverable:** Modern OCR stack, 30× faster processing, exceptional quality

**[→ Detailed Roadmap](./v0.3.0.md)**

---

### v0.3.0 - Messy Document Intelligence (49-57 hours)

**Category:** Automated Document Correction & Exceptional Markdown (KILLER FEATURE)

**Priority:** High

**Dependencies:** v0.3.0 (Docling integration)

Fully automated PDF correction with exceptional markdown conversion - completely hidden from users.

**Key Features:**
- PDF analysis (rotation, order, duplicates, missing pages)
- Automated correction (rotate, reorder, remove duplicates)
- Exceptional markdown (98%+ OCR confidence)
- Original files never modified

**Deliverable:** Zero user intervention for messy PDFs, 98% OCR confidence

**[→ Detailed Roadmap](./v0.3.0.md)**

---

### v0.3.0 - VectorStore Abstraction (16-22 hours)

**Category:** API Foundation for v0.4 LEANN

**Priority:** Medium

**Dependencies:** None

Clean abstraction for multi-backend support.

**Key Features:**
- VectorStore interface (abstract base class)
- ChromaDB refactor (implements interface)
- Factory pattern
- Zero breaking changes

**Deliverable:** Multi-database support foundation for v0.4 LEANN

**[→ Detailed Roadmap](./v0.3.0.md)**

---

### v0.3.0 - Production Data & Generation (68-74 hours)

**Category:** Production-Ready Features

**Priority:** Critical

**Dependencies:** v0.3.0 (RAGAS for chain-of-thought validation)

Versioned documents, rich queries, transparent reasoning.

**Key Features:**
- Document version tracking
- Metadata filtering & faceted search
- Auto-tagging & classification
- Chain-of-thought reasoning
- Enhanced citations (page numbers, quotes, confidence)

**Deliverable:** RAGAS > 0.80, transparent AI reasoning, production-quality generation

**[→ Detailed Roadmap](./v0.3.0.md)**

---

### v0.3.0 - Developer Experience I (20-24 hours)

**Category:** CLI - Interactive & Debug

**Priority:** Medium

**Dependencies:** v0.3.0 (configuration system)

Exploratory workflows and debugging tools.

**Key Features:**
- Interactive REPL mode (Python-like workflow)
- Debug mode (step-by-step pipeline visualisation)
- Session management
- Tab completion

**Deliverable:** Interactive exploration, transparent debugging

**[→ Detailed Roadmap](./v0.3.0.md)**

---

### v0.3.0 - Performance & Quality Tools (19-24 hours)

**Category:** CLI - Measurement & Optimisation

**Priority:** Medium

**Dependencies:** v0.3.0 (RAGAS metrics), v0.3.0 (debug mode integration)

Bottleneck identification and quality dashboards.

**Key Features:**
- Performance profiling (timing, memory, bottleneck detection)
- Quality metrics dashboard (RAGAS scores, trends)
- Historical tracking (SQLite-based)
- Configuration comparison (A/B testing)

**Deliverable:** Data-driven optimisation tools

**[→ Detailed Roadmap](./v0.3.0.md)**

---

### v0.3.0 - Automation & Templates (18-24 hours)

**Category:** CLI - Workflow Automation

**Priority:** Medium

**Dependencies:** v0.3.0 (configuration), v0.3.0 (metrics for testing)

Template-based queries and testing tools.

**Key Features:**
- Query templates (Jinja2-powered workflows)
- Configuration validation (syntax, semantic, security)
- Benchmark testing (quality assurance)
- Regression testing (detect quality drops)

**Deliverable:** Repeatable workflows, automated testing

**[→ Detailed Roadmap](./v0.3.0.md)**

---

### v0.3.0 - Production Operations (17-23 hours)

**Category:** CLI - Production Monitoring

**Priority:** Medium

**Dependencies:** v0.3.0 (templates for scheduled operations)

Production monitoring and automation.

**Key Features:**
- Watch mode (automatic directory monitoring)
- Scheduled operations (cron-like scheduling)
- Daemon support (background operation)
- Execution history tracking

**Deliverable:** Production-ready automation and monitoring

**[→ Detailed Roadmap](./v0.3.0.md)**

---

### v0.3.0 - Polish & Integration (26-32 hours)

**Category:** API, Web, Final UX

**Priority:** Critical (final release)

**Dependencies:** All v0.3.x features (integration testing)

REST API, refined UX, accessibility, complete documentation - v0.3 production-ready release.

**Key Features:**
- FastAPI REST server (full ragged functionality via HTTP)
- Smart query suggestions (spelling, refinement, related queries)
- Colour themes & accessibility (5 themes, WCAG 2.1 AA compliant)
- Complete documentation (user guides, API docs, deployment guides)

**Deliverable:** Production-ready v0.3.0 release with REST API and accessibility

**[→ Detailed Roadmap](./v0.3.0.md)**

---

## Category Distribution

| Category | Versions | Total Hours | Percentage |
|----------|----------|-------------|------------|
| **Core Functionality** | v0.3.0, v0.3.0 | 91-95h | 21% |
| **Document Intelligence** | v0.3.0, v0.3.0 | 104-119h | 24% |
| **Quality & Metrics** | v0.3.0, v0.3.0 | 49-54h | 11% |
| **Configuration & UX** | v0.3.0 | 28-34h | 6% |
| **Production Features** | v0.3.0 | 68-74h | 15% |
| **Developer Experience** | v0.3.0, v0.3.0, v0.3.0 | 55-71h | 14% |
| **API & Integration** | v0.3.0, v0.3.0 | 42-54h | 10% |

### Category: Core Functionality

**Focus:** Advanced retrieval and intelligent chunking

**Versions:** v0.3.0, v0.3.4

**Total:** 91-95h (21% of effort)

**Impact:** Foundation for all retrieval quality improvements

---

### Category: Document Intelligence

**Focus:** Modern OCR and automated PDF correction

**Versions:** v0.3.0, v0.3.6

**Total:** 104-119h (24% of effort - largest category)

**Impact:** 30× performance improvement, killer feature (messy PDF handling)

---

### Category: Quality & Metrics

**Focus:** RAGAS framework and performance profiling

**Versions:** v0.3.0, v0.3.10

**Total:** 49-54h (11% of effort)

**Impact:** Data-driven development, objective quality measurement

---

### Category: Configuration & UX

**Focus:** User-friendly configuration with personas

**Versions:** v0.3.2

**Total:** 28-34h (6% of effort)

**Impact:** Accessibility for non-technical users

---

### Category: Production Features

**Focus:** Production-ready generation and data management

**Versions:** v0.3.8

**Total:** 68-74h (15% of effort)

**Impact:** RAGAS > 0.80, transparent AI reasoning

---

### Category: Developer Experience

**Focus:** Interactive tools, profiling, templates, automation

**Versions:** v0.3.0, v0.3.0, v0.3.12

**Total:** 55-71h (14% of effort)

**Impact:** Developer productivity, testing, monitoring

---

### Category: API & Integration

**Focus:** VectorStore abstraction and REST API

**Versions:** v0.3.0, v0.3.12

**Total:** 42-54h (10% of effort)

**Impact:** Web integration, v0.4 LEANN foundation

---

## Success Metrics

### Performance Targets

| Metric | v0.2 | v0.3 Target | Achievement |
|--------|------|-------------|-------------|
| **Retrieval Quality** | MRR@10 ~0.60 | > 0.75 | [Track in v0.3.0] |
| **Answer Quality** | RAGAS ~0.70 | > 0.80 | [Track in v0.3.0] |
| **Multi-Modal Success** | - | 95%+ PDFs | [Track in v0.3.0] |
| **OCR Confidence** | - | 98%+ (good quality) | [Track in v0.3.0] |
| **Processing Speed** | 100 pages/min | 1000 pages/min | [Track in v0.3.0] |

### User Experience Goals

- ✓ Zero-configuration messy PDF handling
- ✓ Persona-based configuration
- ✓ Transparent decision-making
- ✓ Sub-second queries on cached results
- ✓ Interactive exploration workflows

### Developer Experience Goals

- ✓ 70%+ test coverage (from 58%)
- ✓ Interactive debugging tools
- ✓ Performance profiling
- ✓ Automated testing utilities

---

## Quality Gates (Cross-Version)

These quality gates apply across all v0.3.x versions:

### Code Quality Requirements (Every Version)
- [ ] 100% test coverage for new code
- [ ] All tests passing
- [ ] Type hints complete
- [ ] Docstrings complete (British English)
- [ ] No regressions in existing tests

### Documentation Requirements (Every Version)
- [ ] User documentation written
- [ ] API documentation updated (if applicable)
- [ ] Examples provided
- [ ] CHANGELOG.md updated
- [ ] British English compliance verified

### Performance Requirements (Where Applicable)
- [ ] No performance regressions
- [ ] Performance targets met (see version-specific goals)
- [ ] Memory usage acceptable
- [ ] Profiling data captured (v0.3.0+)

### Quality Requirements (Retrieval/Generation Features)
- [ ] RAGAS scores measured and documented
- [ ] Quality targets met (see version-specific goals)
- [ ] Edge cases tested
- [ ] User acceptance testing complete

---

## Timeline Estimates

### At 10 Hours/Week

| Version | Hours | Weeks | Cumulative Weeks |
|---------|-------|-------|------------------|
| **v0.2.10** | **15-21** | **2** | **2** |
| **v0.2.11** | **20-26** | **2-3** | **4-5** |
| v0.3.0 | 30 | 3 | 7-8 |
| v0.3.0 | 28-34 | 3-4 | 10-12 |
| v0.3.0 | 53-55 | 5-6 | 15-18 |
| v0.3.0 | 38-40 | 4 | 19-22 |
| v0.3.0 | 55-62 | 6 | 25-28 |
| v0.3.0 | 49-57 | 5-6 | 30-34 |
| v0.3.0 | 16-22 | 2 | 32-36 |
| v0.3.0 | 68-74 | 7 | 39-43 |
| v0.3.0 | 20-24 | 2-3 | 41-46 |
| v0.3.0 | 19-24 | 2-3 | 43-49 |
| v0.3.0 | 18-24 | 2-3 | 45-52 |
| v0.3.0 | 17-23 | 2-3 | 47-55 |
| v0.3.0 | 26-32 | 3 | 50-58 |
| **Total** | **472-548** | **47-55** | **47-55 weeks** |

**Note:** v0.2.10 and v0.2.11 are prerequisites that must be completed before v0.3.0.

### At 15 Hours/Week

Total: 31-37 weeks (7-9 months)

### At 20 Hours/Week

Total: 24-28 weeks (6-7 months)

---

## Agent Usage Patterns

### Standard Workflow Per Version

**1. Before Implementation (optional, 2-3h when needed):**
- **architecture-advisor:** Design review for complex decisions
- **ux-architect:** UX validation for user-facing features

**2. After Implementation (4-8h):**
- **documentation-architect:** Plan documentation structure (2-4h)
- Write documentation following plan

**3. Before Commit (4-8h):**
- **documentation-auditor:** Comprehensive review (2-4h)
- Fix any issues found
- **git-documentation-committer:** Commit with quality checks (2-4h)

### Agent Roles & When to Use

| Agent | Use Case | Typical Duration | Required? |
|-------|----------|------------------|-----------|
| **architecture-advisor** | Complex design decisions, technology choices, trade-off analysis | 2-3h per decision | Optional (as needed) |
| **ux-architect** | User-facing features, CLI design, persona/configuration UX | 2h per feature | Optional (as needed) |
| **documentation-architect** | Planning doc structure BEFORE writing, new feature docs | 2-4h per version | Recommended |
| **documentation-auditor** | Before EVERY commit, comprehensive quality check | 2-4h per version | **Required** |
| **git-documentation-committer** | For EVERY commit, ensures quality and consistency | 2-4h per version | **Required** |

### Agent Usage by Version

Specific agent recommendations are documented in each version's roadmap file. See the "Agent Workflow" section in each version.

---

## Dependency Changes

### Removed Dependencies (v0.3.0)
```toml
# REMOVED in v0.3.5
# pytesseract = "^0.3.10"      # Replaced by Docling/PaddleOCR
# camelot-py = "^0.11.0"       # Replaced by Docling TableFormer
```

### New Dependencies by Version

#### v0.3.0 - Intelligent Chunking
```toml
nltk = "^3.8.0"                 # Apache 2.0 - Sentence splitting
scipy = "^1.11.0"               # BSD - Similarity calculations
```

#### v0.3.0 - Modern Document Processing
```toml
docling = "^2.0.0"              # MIT - Modern document processing
paddleocr = "^2.8.0"            # Apache 2.0 - Fallback OCR
paddlepaddle = "^2.6.0"         # Apache 2.0 - PaddleOCR backend
opencv-python = "^4.8.0"        # BSD - Image preprocessing
```

#### v0.3.0 - Messy Document Intelligence
```toml
pypdf = "^3.17.0"               # BSD - PDF manipulation
img2pdf = "^0.5.1"              # LGPL - Image to PDF
scikit-image = "^0.22.0"        # BSD - Image quality assessment
Pillow = "^10.0.0"              # HPND - Image handling
```

#### v0.3.0 - Developer Experience I
```toml
prompt-toolkit = "^3.0.0"       # BSD - REPL interface
```

#### v0.3.0 - Performance & Quality Tools
```toml
memory-profiler = "^0.61.0"     # BSD - Memory tracking
rich = "^13.7.0"                # MIT - Beautiful tables
```

#### v0.3.0 - Automation & Templates
```toml
jinja2 = "^3.1.0"               # BSD - Template engine
```

#### v0.3.0 - Production Operations
```toml
watchdog = "^3.0.0"             # Apache 2.0 - File system monitoring
APScheduler = "^3.10.0"         # MIT - Job scheduling
croniter = "^2.0.0"             # MIT - Cron parsing
```

#### v0.3.0 - Polish & Integration
```toml
fastapi = "^0.104.0"            # MIT - REST API framework
uvicorn = "^0.24.0"             # BSD - ASGI server
python-multipart = "^0.0.6"     # Apache 2.0 - File uploads
pyspellchecker = "^0.7.0"       # MIT - Spelling correction
wcag-contrast-ratio = "^0.9"    # MIT - Accessibility validation
```

**All dependencies are GPL-3.0 compatible (MIT, Apache 2.0, BSD, HPND, LGPL)**

---

## Configuration Personas Design

### Built-in Personas

**"accuracy"** - Maximum quality, slower
- Query decomposition: Enabled
- Retrieval method: Hybrid
- Reranking: Enabled (top-10 → top-3)
- Contextual compression: Enabled
- Confidence threshold: 95%
- Use case: Research, critical decisions

**"speed"** - Fast answers
- Query decomposition: Disabled
- Retrieval method: Vector only
- Reranking: Disabled
- Contextual compression: Disabled
- Confidence threshold: 80%
- Use case: Quick lookups, exploration

**"balanced"** - Default
- Query decomposition: Auto (on complex queries)
- Retrieval method: Hybrid
- Reranking: Enabled (top-15 → top-5)
- Contextual compression: Auto
- Confidence threshold: 85%
- Use case: General usage

**"research"** - Deep exploration
- Query decomposition: Enabled
- Retrieval method: Hybrid
- Retrieve: Top-30 chunks
- Reranking: Enabled (top-30 → top-10)
- Multi-query: Enabled
- Use case: Academic research, comprehensive analysis

**"quick-answer"** - Single best answer
- Retrieval method: Hybrid
- Retrieve: Top-1
- Reranking: Disabled (too slow for single result)
- Format: Concise
- Use case: CLI automation, scripts

### User Custom Personas

Users can create custom personas in `~/.config/ragged/personas.yml`:

```yaml
personas:
  my-research:
    description: "Custom research profile"
    inherits: accuracy
    overrides:
      retrieval_method: hybrid
      top_k: 50
      rerank_to: 15
```

---

## Version Comparison Table

| Feature Area | v0.1 | v0.2 | v0.3 |
|--------------|------|------|------|
| **Retrieval** | Basic dense | Dense + BM25 hybrid | Hybrid + reranking + query expansion |
| **Chunking** | Recursive | + Overlap optimisation | + Semantic/hierarchical |
| **Documents** | PDF, TXT, MD | + Metadata extraction | + Multi-modal + auto-correction |
| **OCR** | None | Tesseract | Docling + PaddleOCR |
| **Evaluation** | Manual | Basic metrics | RAGAS framework |
| **CLI** | Basic | Enhanced output | Interactive + automation + personas |
| **Generation** | Basic | Few-shot | Chain-of-thought + confidence |
| **Configuration** | Static | File-based | Personas + transparency |
| **API** | None | None | FastAPI REST server |
| **Accessibility** | None | None | WCAG 2.1 AA compliant |
| **Test Coverage** | ~40% | ~58% | Target: 70-80% |

---

## Risk Mitigation

### High Risk Items

**1. Docling Performance on Very Messy Scans**
- **Risk:** Docling may struggle with worst-case documents
- **Mitigation:** PaddleOCR fallback, confidence tracking
- **Validation:** Test on representative sample before full implementation (v0.3.0)
- **Owner:** v0.3.0, v0.3.6

**2. Automated Correction Accuracy**
- **Risk:** Auto-correction may make wrong decisions
- **Mitigation:** Confidence tracking, metadata logging, user can review corrections
- **Validation:** Manual review of 50+ corrected documents (v0.3.0)
- **Owner:** v0.3.6

### Medium Risk Items

**3. Configuration Persona Design**
- **Risk:** Personas may not match user mental models
- **Mitigation:** User testing, iteration based on feedback
- **Validation:** Get feedback from 3-5 users before finalising (v0.3.0)
- **Owner:** v0.3.2

**4. Test Coverage Goals**
- **Risk:** May not reach 70% coverage
- **Mitigation:** Focus on core paths first, defer edge cases
- **Validation:** Track coverage per version, adjust if needed
- **Owner:** All versions

**5. RAGAS > 0.80 Target**
- **Risk:** May not achieve target with current techniques
- **Mitigation:** Combine multiple techniques, iterate on prompts
- **Validation:** Measure after each retrieval improvement (v0.3.0, v0.3.0, v0.3.0)
- **Owner:** v0.3.8

### Low Risk Items

- License compatibility (all verified GPL-3.0 compatible)
- OCR technology maturity (proven tools)
- Query processing techniques (well-established)
- REST API implementation (FastAPI is mature)

---

## Security & Privacy Considerations

### Privacy-by-Design Principles

All v0.3.x features follow privacy-by-design principles established in v0.2.10 and v0.2.11:

1. **Data Minimisation:** Only store necessary data (query hashes, NOT plaintext queries)
2. **Purpose Limitation:** User data only used for intended purpose (performance metrics, debugging)
3. **Storage Limitation:** TTL-based cleanup (7-90 days depending on feature)
4. **Confidentiality:** Encryption at rest (Fernet/AES-128)
5. **Transparency:** Users informed when PII detected
6. **User Control:** GDPR rights (deletion, export, access)

### Security Testing Requirements

Each v0.3.x version must pass security validation:

**For ALL versions:**
- [ ] Pre-commit security hooks pass (v0.2.10)
- [ ] No secrets in code or configuration
- [ ] Dependencies scanned for CVEs
- [ ] Input validation on user data
- [ ] British English compliance in error messages

**For data-handling features (v0.3.0, v0.3.0, v0.3.0):**
- [ ] Session isolation verified (no cross-user leakage)
- [ ] PII detection tested (email, phone, SSN patterns)
- [ ] Query hashing used (NOT plaintext storage)
- [ ] Encryption at rest verified (file permissions 0o600)
- [ ] TTL cleanup functional
- [ ] GDPR deletion/export tested

**Security Agent Workflow:**

Use `codebase-security-auditor` agent:
1. After implementing each feature
2. Before committing code
3. Before release

See detailed security testing checklists in v0.2.10 and v0.2.11 roadmaps.

### Privacy Risk Assessment

| v0.3 Feature | Privacy Risk | Mitigation | Risk Score |
|--------------|-------------|-----------|-----------|
| **v0.3.0 RAGAS** | Low | No user data stored | N/A |
| **v0.3.0 Config** | None | Configuration only | N/A |
| **v0.3.0 Retrieval** | Low | Session-scoped caching | N/A |
| **v0.3.0 Chunking** | None | Document processing only | N/A |
| **v0.3.0 OCR** | None | Document processing only | N/A |
| **v0.3.0 Auto-correct** | None | Document processing only | N/A |
| **v0.3.0 VectorStore** | Low | Session isolation | N/A |
| **v0.3.0 Metadata** | Medium | Query hashing, TTL | N/A |
| **v0.3.0 REPL** | **HIGH** | Encrypted sessions, PII warnings, TTL | **90/100** |
| **v0.3.0 Metrics** | **HIGH** | Query hashing, DB encryption, TTL | **95/100** |
| **v0.3.0 Templates** | Low | Template processing only | N/A |
| **v0.3.0 Watch** | Low | File monitoring only | N/A |
| **v0.3.0 REST API** | **HIGH** | Session isolation, auth, rate limiting | **92/100** |

**High-risk features (v0.3.0, v0.3.0, v0.3.0) have detailed privacy implementation sections in their roadmap files.**

### GDPR Compliance Summary

v0.3.x features support GDPR requirements through v0.2.11 infrastructure:

| GDPR Right | Implementation | v0.3 Features |
|-----------|---------------|---------------|
| **Right to Access (Art. 15)** | User can export all data | v0.3.0, v0.3.0, v0.3.0 |
| **Right to Erasure (Art. 17)** | User can delete all data | v0.3.0, v0.3.0, v0.3.0 |
| **Right to Portability (Art. 20)** | JSON export format | v0.3.0, v0.3.0, v0.3.0 |
| **Storage Limitation (Art. 5)** | TTL-based cleanup | v0.3.0, v0.3.0, v0.3.0 |
| **Data Minimisation (Art. 5)** | Query hashing (NOT plaintext) | v0.3.0, v0.3.0 |
| **Confidentiality (Art. 32)** | Encryption at rest | v0.3.0, v0.3.0, v0.3.0 |

**CLI Commands (implemented in v0.3.0+):**
```bash
ragged privacy export --format json --output my-data.json
ragged privacy delete --confirm
ragged privacy status  # Show what data is stored
```

### Security Foundation APIs Used by v0.3.x

**From v0.2.10 (Session Isolation):**
```python
from ragged.session import Session, SessionManager

# All features use session-scoped operations
session = SessionManager().get_or_create_session()
cache_key = make_cache_key(session.session_id, query, **kwargs)
```

**From v0.2.11 (Privacy Infrastructure):**
```python
from ragged.privacy import (
    EncryptionManager,
    hash_query,
    contains_pii,
    redact_pii,
    CleanupScheduler,
)

# Encrypt sensitive data
encryption = EncryptionManager()
encrypted_data = encryption.encrypt(sensitive_data.encode())

# Hash queries for logging/metrics (NOT plaintext)
query_hash = hash_query(user_question)

# Detect PII in user input
if contains_pii(user_input):
    warn_user("Input contains PII - will be encrypted")

# Schedule TTL cleanup
scheduler = CleanupScheduler()
scheduler.schedule_cleanup(data_path, ttl_days=90)
```

---

## Related Documentation

### Security & Privacy Prerequisites
- [v0.2.10 Roadmap](../v0.2/v0.2.10/) - Security Hardening (REQUIRED before v0.3.x)
- [v0.2.11 Roadmap](../v0.2/v0.2.11/) - Privacy Infrastructure (REQUIRED before v0.3.x)

### Planning Documentation
- [v0.3.0 Planning](../../planning/version/v0.3/) - Design goals and requirements

### Feature Specifications
- [Query Processing Features](./features/query-processing.md) - Detailed specs
- [Chunking Strategies](./features/chunking-strategies.md) - Detailed specs
- [Multi-Modal Support](./features/multi-modal-support.md) - Detailed specs
- [Evaluation & Quality](./features/evaluation-quality.md) - Detailed specs
- [Data & Generation](./features/data-generation.md) - Detailed specs
- [CLI Features](./features/cli-features.md) - Detailed specs

### Architecture Decisions
- [CLI Enhancements Catalogue](../../planning/interfaces/cli/enhancements.md) - Comprehensive CLI specs
- [Docling OCR Decision](../../../decisions/2025-11-17-docling-ocr-decision.md) - Architecture decision record

### Implementation Records
- After completing each version, create implementation record in `docs/development/implementation/version/v0.3/`

---

## Next Steps

### Getting Started

1. **Read this roadmap completely** to understand the full scope
2. **Review [v0.3.0](./v0.3.0.md)** - the first version to implement
3. **Set up your environment** with necessary dependencies
4. **Create feature branch** for v0.3.1
5. **Follow the execution checklist** in v0.3.0.md
6. **Track your progress** using the [Progress Tracking](#progress-tracking) section

### After v0.3.0 Completion

Once all 13 versions are complete:

**v0.4.0 - LEANN Integration**
- Integrate LEANN vector database
- Multi-backend support (ChromaDB, LEANN, Qdrant, Weaviate)
- Performance optimisation

**v0.5.0 - Multi-Modal RAG**
- Image understanding (llava integration)
- Audio transcription
- Video processing

**v1.0.0 - Stable Release**
- API stability guarantees
- LTS support
- Production hardening

---

**Status:** Ready for implementation
