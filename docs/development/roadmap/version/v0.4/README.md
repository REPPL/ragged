# Ragged v0.4.x Roadmap Overview - Personal Memory & Knowledge Graphs

**Version Series:** v0.4.0 - v0.4.13

**Status:** Planned

**Total Hours:** 272-330 hours (across 14 incremental releases)

**Focus:** Foundation-first architecture with plugin system, personal memory, knowledge graphs, and mandatory LEANN backend integration

**Breaking Changes:** None - All features are additive and optional

**Dependencies:** v0.3.x complete (advanced retrieval, evaluation framework, VectorStore abstraction awareness)

---

## Vision

Version 0.4.x transforms ragged from a document retrieval tool into an intelligent personal knowledge assistant through **14 incremental releases** that prioritise architectural excellence, comprehensive testing, and production-ready stability.

**Core Principle**: Foundation first, features second - establish rock-solid architecture, testing infrastructure (80%+ coverage), and code quality before introducing complex memory and personalisation features.

**Key Capabilities** (by end of v0.4.13):
- **Plugin Architecture**: Extensible system with security sandboxing for custom embedders, retrievers, processors, and commands
- **VectorStore Abstraction**: Support for multiple backends with seamless migration
- **Personal Memory System**: Persona management, behaviour learning, temporal memory
- **Knowledge Graphs**: Connect topics, documents, and concepts over time
- **Personalised Ranking**: Boost relevant documents based on learned interests
- **LEANN Backend**: 97% storage savings through graph-based retrieval (mandatory, platform-aware)
- **Production-Ready**: Comprehensive testing, performance optimisation, security hardening, backend migration tools

---

## Prerequisites & Security

### Hard Prerequisites (Must Complete Before Starting v0.4)

**CRITICAL**: v0.4.x **CANNOT** begin until all prerequisites are met.

#### 1. Complete v0.2.10 & v0.2.11 (Security & Privacy Foundation)
- **Status**: ✅ Completed (Nov 2025)
- **Why Critical**: v0.4 stores highly sensitive user data (behaviour patterns, interests, temporal history)
- **Components Required**:
  - Session isolation (CRITICAL-003 resolved)
  - JSON serialisation (CRITICAL-001 resolved)
  - Encryption at rest (FEAT-PRIV-001)
  - PII detection and redaction (FEAT-PRIV-002)
  - Data lifecycle management (FEAT-PRIV-003)
  - GDPR compliance toolkit (FEAT-PRIV-004)

#### 2. Complete v0.3.x Series (All 13 Releases)
- **Status**: ⏳ In Progress (Target: Q2-Q3 2026)
- **Why Critical**: v0.4 builds directly on v0.3 architecture
- **Key Dependencies**:
  - v0.3.1: Evaluation framework (enables v0.4 validation)
  - v0.3.3: Advanced query processing (enables v0.4.0 personalisation)
  - v0.3.7: VectorStore abstraction (enables v0.4.0 & v0.4.0)
  - v0.3.13: REST API (coexists with v0.4.0 plugin system)

#### 3. Security Audit for Memory System (BEFORE v0.4.0)
- **Status**: ⏳ Planned (Complete during/after v0.4.0)
- **Why Critical**: Memory system stores personal behaviour data
- **Scope**: Memory system design, knowledge graph storage, behaviour tracking
- **Timeline**: 2-3 weeks, must pass before v0.4.0 implementation begins
- **Deliverable**: Security audit report with pass/fail status
- **See**: [v0.4.5/security-audit.md](v0.4.5/security-audit.md) for full requirements

### Target Timeline

**Earliest Start**: Q3 2026 (assuming v0.3.x complete by Q2-Q3 2026)
**Estimated Duration**: 11-12 months (45-48 weeks, 272-330 hours)
**Target Completion**: Q2 2027 (May-June)

**Critical Path**:
```
v0.2.10/v0.2.11 (Complete) →
v0.3.x (13 releases, Q2-Q3 2026) →
Security Audit (2-3 weeks, during v0.4.2) →
v0.4.0-v0.4.4 Foundation & Security →
v0.4.5-v0.4.8 Memory System Core →
v0.4.9-v0.4.10 Advanced Features →
v0.4.11-v0.4.13 Stabilisation & Production →
v0.4.13 Production Release (Q2 2027)
```

### Privacy & Security Commitment

**Local-First Guarantee**: All user data remains on device
**Zero Telemetry**: No usage tracking, no cloud dependencies
**Privacy Controls**: Export, delete, disable tracking at any time
**Security Gates**: Formal audit before memory system implementation
**GDPR Compliance**: Built on v0.2.11 FEAT-PRIV-004 foundation

---

## Release Strategy

### Phase 1: Foundation & Security (v0.4.0 - v0.4.4)
**Focus**: Security baseline, plugin system, multi-backend support, code quality
**Hours**: 98-119
**Releases**: 5
**Goal**: Establish rock-solid architecture with security hardening, extensibility, and quality infrastructure

### Phase 2: Memory System Core (v0.4.5 - v0.4.8)
**Focus**: Personas, interaction tracking, behaviour learning, personalisation
**Hours**: 85-98
**Releases**: 4
**Goal**: Deliver complete personal memory system with user behaviour learning

### Phase 3: Advanced Features (v0.4.9 - v0.4.11)
**Focus**: Production readiness, mid-series security review, temporal memory (split into 2 parts)
**Hours**: 57-71
**Releases**: 3
**Goal**: Security-hardened codebase, complete temporal memory system with advanced reasoning

### Phase 4: Stabilisation & Production (v0.4.12 - v0.4.13)
**Focus**: Backend optimisation & migration (merged), production deployment with observability
**Hours**: 43-52
**Releases**: 2
**Goal**: Consolidated backend infrastructure, production-ready deployment with operational excellence

---

## Incremental Releases

### [v0.4.0 - Plugin Architecture & Testing Foundation](v0.4.0.md) (25-30h)

**Status**: Planned | **Priority**: P0 - Foundation

**Focus**: Extensibility architecture and quality infrastructure

**Deliverables**:
- ✅ Complete plugin system (embedders, retrievers, processors, commands)
- ✅ Plugin discovery via entry points
- ✅ Plugin management CLI commands
- ✅ Test infrastructure upgrades (80%+ coverage requirement)
- ✅ CI/CD quality gates (type checking, linting, security)
- ✅ Sample plugins and comprehensive documentation

**Success Criteria**:
- Plugin system fully functional
- 80%+ test coverage achieved and enforced
- Quality gates preventing regressions
- Zero breaking changes

---

### [v0.4.1 - VectorStore Abstraction & Refactoring](v0.4.1.md) (18-22h)

**Status**: Planned | **Priority**: P0 - Foundation

**Focus**: Backend abstraction and codebase preparation

**Deliverables**:
- ✅ VectorStore abstract interface
- ✅ ChromaDB refactored into clean implementation
- ✅ Codebase structure prepared for memory system
- ✅ Technical debt reduction
- ✅ Type safety improvements (mypy strict mode)
- ✅ Contract tests for VectorStore implementations

**Success Criteria**:
- All existing tests pass (no regressions)
- Performance maintained (<5% overhead)
- Codebase ready for memory integration
- Backend selection infrastructure ready

---

### [v0.4.2 - Code Quality & Stability Release](v0.4.2.md) (12-15h)

**Status**: Planned | **Priority**: P1 - Quality

**Focus**: Dedicated code quality and stability improvements

**Deliverables**:
- ✅ Code quality improvements across codebase
- ✅ Performance profiling and optimisation
- ✅ Documentation standardisation
- ✅ Security audit and hardening
- ✅ Error handling enhancements
- ✅ Logging and observability improvements

**Success Criteria**:
- Linting: 0 errors, <5 warnings
- Security: No high/critical vulnerabilities
- Performance: Baseline benchmarks established
- Documentation: All modules documented

---

### [v0.4.3 - Memory Foundation: Personas & Tracking](v0.4.3.md) (35-40h)

**Status**: Planned | **Priority**: P0 - Core Feature

**Focus**: Personal memory system foundation

**Deliverables**:
- ✅ Persona management system
- ✅ Interaction tracking (SQLite)
- ✅ Knowledge graph foundation (Kuzu)
- ✅ Memory management CLI commands
- ✅ Comprehensive testing (7-9h dedicated)
- ✅ Privacy guarantees validated

**Success Criteria**:
- Persona system works seamlessly
- All interactions tracked locally
- Knowledge graph initialized
- 80%+ test coverage maintained
- Zero data leaves local machine

---

### [v0.4.4 - Stability & Performance Enhancement](v0.4.4.md) (15-18h)

**Status**: Planned | **Priority**: P1 - Quality

**Focus**: Memory system stability and performance

**Deliverables**:
- ✅ Memory system performance optimisation
- ✅ Integration testing suite for memory features
- ✅ Error handling and edge case coverage
- ✅ Memory leak detection and fixes
- ✅ Database query optimisation
- ✅ Concurrent access handling

**Success Criteria**:
- Memory operations <100ms
- Graph queries <300ms
- No memory leaks
- Graceful error handling

---

### [v0.4.5 - Behaviour Learning & Personalisation](v0.4.5/README.md) (35-40h)

**Status**: Planned | **Priority**: P0 - Core Feature

**Focus**: Intelligent personalization

**Deliverables**:
- ✅ Topic extraction from queries
- ✅ Behaviour learning system
- ✅ Personalised ranking algorithm
- ✅ RAG pipeline integration
- ✅ Interest profile analytics
- ✅ Testing and validation (6-8h)

**Success Criteria**:
- Personalisation improves relevance by >15%
- Topic extraction 80%+ accuracy
- Interest profiles validated by users
- Performance <2s end-to-end

---

### [v0.4.6 - Refactoring & Architecture Improvements](v0.4.6.md) (10-12h)

**Status**: Planned | **Priority**: P2 - Quality

**Focus**: Dedicated refactoring release

**Deliverables**:
- ✅ Code consolidation and cleanup
- ✅ Architecture pattern enforcement
- ✅ Dependency optimisation
- ✅ Technical debt reduction
- ✅ Module boundary improvements
- ✅ Code complexity reduction

**Success Criteria**:
- Cyclomatic complexity reduced
- Code duplication eliminated
- Clear module boundaries
- Improved maintainability metrics

---

### [v0.4.7 - Behaviour Learning & Personalisation](v0.4.7.md) (35-40h)

**Status**: Planned | **Priority**: P0 - Core Feature

**Focus**: Intelligent personalisation and behaviour learning

**Deliverables**:
- ✅ Topic extraction from queries
- ✅ Behaviour learning system (interest profiling, temporal decay)
- ✅ Personalised ranking algorithm
- ✅ RAG pipeline integration
- ✅ Interest profile analytics
- ✅ Testing and validation (6-8h)

**Success Criteria**:
- Personalisation improves relevance by >15%
- Topic extraction 80%+ accuracy
- Interest profiles validated by users
- Performance <2s end-to-end

**Note**: Original v0.4.7 temporal memory content split into v0.4.10 & v0.4.11 (see restructuring below)

---

### [v0.4.8 - LEANN Backend Integration](v0.4.8.md) (35-42h)

**Status**: Planned | **Priority**: P1 - Alternative Backend

**Focus**: Graph-based vector storage

**Deliverables**:
- ✅ LEANN backend implementation
- ✅ Backend selection and configuration
- ✅ Migration tools (ChromaDB ↔ LEANN)
- ✅ Comprehensive documentation
- ✅ Performance comparison benchmarks
- ✅ Platform-specific builds

**Success Criteria**:
- LEANN achieves 97% storage savings
- 90% top-3 recall maintained
- Migration tools work correctly
- Users can choose backend easily

---

### [v0.4.9 - Production Readiness & Mid-Series Security Review](v0.4.9.md) (20-25h)

**Status**: Planned | **Priority**: P0 - Release & Security

**Focus**: Code consolidation, architecture enforcement, and comprehensive mid-series security audit

**Deliverables**:
- ✅ Mid-series security review (5-7h) - NEW strategic checkpoint
  - Comprehensive vulnerability scan (bandit, safety, pip-audit)
  - Path traversal, command injection, SQL injection fixes
  - Security audit report
- ✅ Code consolidation and refactoring (3h)
- ✅ Architecture pattern enforcement (3h)
- ✅ Dependency optimisation (2h)
- ✅ Module boundary improvements (2-3h)
- ✅ Code complexity reduction (1-2h)

**Success Criteria**:
- Zero HIGH/CRITICAL security vulnerabilities
- Security audit report complete
- Code duplication <3%
- Cyclomatic complexity reduced 20%+
- All tests passing

**Rationale**: Security checkpoint before complex temporal memory features (v0.4.10-v0.4.11)

---

### [v0.4.10 - Temporal Memory: Facts & Timeline Basics (Part 1)](v0.4.10/README.md) (20-25h)

**Status**: Planned | **Priority**: P0 - Core Feature

**Focus**: Foundation of temporal memory system

**Deliverables**:
- ✅ Temporal fact storage (8-10h) - Time-stamped facts with SQLite indexing
- ✅ Basic timeline query engine (6-8h) - Core queries only ("What happened on X?")
- ✅ CLI temporal commands (4-6h) - Essential commands (`ragged timeline query`)
- ✅ Basic testing (2h) - Core functionality validation

**Success Criteria**:
- Temporal facts stored and retrieved correctly
- Basic timeline queries functional
- CLI commands working
- Foundation ready for Part 2

**Deferred to v0.4.11 (Part 2)**: Advanced reasoning, visualisations, comprehensive testing

---

### [v0.4.11 - Temporal Memory: Advanced Features (Part 2)](v0.4.11.md) (17-21h)

**Status**: Planned | **Priority**: P0 - Advanced Feature

**Focus**: Advanced temporal reasoning and comprehensive testing

**Deliverables**:
- ✅ Temporal reasoning & time expression parsing (10-12h)
  - Natural language time parsing (dateparser library)
  - Support "last week", "Q4 2025", "yesterday at 3pm"
- ✅ Advanced visualisations (3-5h) - 4 chart types, heatmaps, activity graphs
- ✅ Comprehensive testing & property-based tests (4h)
  - Hypothesis framework integration
  - DST transitions, leap years, timezone edge cases
  - 90%+ test coverage for temporal modules

**Dependencies Added**:
- `dateparser>=1.2.0` - Natural language date/time parsing
- `hypothesis>=6.98.0` - Property-based testing

**Success Criteria**:
- Natural language time expressions work
- Property-based tests pass (100+ generated cases)
- DST/leap year edge cases handled
- 90%+ test coverage achieved

**Rationale**: Split from v0.4.10 to reduce implementation risk and improve testing depth

---

### [v0.4.12 - Backend Optimisation & Migration](v0.4.12.md) (25-30h)

**Status**: Planned | **Priority**: P1 - Infrastructure

**Focus**: Consolidated backend infrastructure (migration + optimisation merged)

**Part A: Backend Migration & Selection** (12-15h):
- ✅ Migration engine with dry-run mode, checkpointing, regression detection
- ✅ CLI migration commands with progress tracking
- ✅ Backend comparison and selection tools
- ✅ Automated verification post-migration

**Part B: Performance Optimisation** (13-15h):
- ✅ LEANN query optimisation with query plan caching
- ✅ Memory system performance tuning
- ✅ Multi-backend benchmarking with load testing (5+ minutes sustained)
- ✅ Profiling and monitoring tools

**Success Criteria**:
- Dry-run estimates accurate
- Migration checkpointing prevents data loss
- Automated regression detection (<20% latency degradation, >95% recall similarity)
- Load testing shows <10% performance degradation
- Query plan caching reduces overhead

**Rationale**: Merged old v0.4.11 + v0.4.12 for logical cohesion (benchmark → estimate → migrate → validate → load test)

---

### [v0.4.13 - Production Deployment & Observability](v0.4.13.md) (18-22h)

**Status**: Planned | **Priority**: P0 - Production

**Focus**: Production deployment with operational excellence

**Deliverables**:
- ✅ Observability & monitoring infrastructure (3-4h) - NEW
  - Structured logging (JSON format)
  - Prometheus-compatible metrics
  - Health monitoring dashboard
- ✅ Deployment health checks (2-3h) - NEW
  - Startup validation, liveness/readiness probes
  - Pre/post-deployment checks
  - Kubernetes/Docker health endpoints
- ✅ Chaos engineering tests (2-3h) - NEW
  - Backend failure, database corruption, disk full scenarios
  - Network partition resilience
  - Concurrent failure recovery
- ✅ Comprehensive end-to-end testing (5-6h) - Enhanced
- ✅ Security hardening & privacy verification (4-5h)
- ✅ Documentation & operational runbooks (3-4h) - Enhanced (~1,000 lines)
- ✅ Release preparation & packaging (2-3h)

**Success Criteria**:
- All chaos tests passed
- Health checks automated
- Observability fully configured
- Operational runbooks complete
- Production deployment validated

**Rationale**: Enhanced with observability, health checks, and chaos testing for production maturity

---

## Total Effort Summary

| Phase | Releases | Hours | Focus |
|-------|----------|-------|-------|
| Foundation & Security | v0.4.0 - v0.4.4 | 98-119 | Architecture, testing, quality |
| Memory System Core | v0.4.5 - v0.4.8 | 110-129 | Personas, behaviour learning, LEANN |
| Advanced Features | v0.4.9 - v0.4.11 | 57-71 | Security review, temporal memory (2 parts) |
| Stabilisation & Production | v0.4.12 - v0.4.13 | 43-52 | Backend optimisation, observability |
| **Total** | **14 releases** | **308-371** | **Complete v0.4** |

**Original v0.4.0 estimate**: 180-225 hours
**Pre-restructuring v0.4.x total**: 270-329 hours
**Restructured v0.4.x total**: 308-371 hours
**Difference from original**: +83-146 hours (+46-65%) for enhanced quality, security, and operational excellence

**Restructuring Changes** (Nov 2025):
- **v0.4.10 split** into v0.4.10 (Part 1, 20-25h) + v0.4.11 (Part 2, 17-21h) for risk reduction
- **v0.4.11 + v0.4.12 merged** into v0.4.12 (25-30h) for logical cohesion (backend infrastructure)
- **v0.4.9 enhanced** with mid-series security review (15-20h → 20-25h)
- **v0.4.13 enhanced** with observability, health checks, chaos tests (12-15h → 18-22h)
- **Net change**: +38-42 hours (+14%) for security, operational excellence, and resilience validation

**Justification**: Additional investment in security audits (mid-series + final), observability infrastructure, chaos engineering, and incremental delivery (temporal memory split) delivers ~300% ROI through reduced debugging, faster incident response, and production stability.

---

## Key Architectural Decisions

### 1. Foundation-First Approach

**Decision**: Prioritise architecture and testing infrastructure before features

**Rationale**:
- Complex memory system requires solid foundation
- 80%+ test coverage prevents regressions
- Plugin architecture enables community contributions
- Quality gates catch issues early

**Impact**: Slightly longer initial development, but faster and safer feature delivery

### 2. Incremental Release Strategy

**Decision**: Break v0.4.0 into 14 incremental releases instead of 1 large release

**Rationale**:
- Manage complexity and risk
- Deliver value progressively
- Get user feedback early
- Easier testing and debugging
- Clear rollback points

**Impact**: Better quality, more flexibility, easier project management

### 3. Dedicated Stability Releases

**Decision**: Include 4 stability-focused releases (v0.4.0, v0.4.0, v0.4.0, v0.4.0)

**Rationale**:
- Foundation-first principle requires quality gates
- Memory system complexity demands stability focus
- Technical debt reduction prevents accumulation
- Performance optimisation needs dedicated time

**Impact**: Higher quality, better performance, easier maintenance

### 4. Plugin Architecture First

**Decision**: Implement plugin system before memory features (v0.4.0)

**Rationale**:
- Enables extensibility from start
- Memory system can use plugin patterns
- Community can contribute early
- Demonstrates architectural commitment

**Impact**: Flexibility, extensibility, community engagement

### 5. VectorStore Abstraction Early

**Decision**: Implement abstraction layer before memory features (v0.4.0)

**Rationale**:
- LEANN integration easier later (v0.4.0)
- Clean architecture from start
- Prepared for v0.3's VectorStore work
- Multiple backends possible

**Impact**: Future-proof architecture, easier backend additions

---

## Testing Strategy

### Test Coverage Requirements

**Minimum Coverage**: 80% overall (enforced via CI/CD)

**Module-Specific**:
- Plugin system: 90%+
- VectorStore: 90%+
- Memory system: 85%+
- Core features: 85%+
- CLI commands: 80%+

### Test Types

1. **Unit Tests**: Fast, isolated, comprehensive
2. **Integration Tests**: Component interactions
3. **Contract Tests**: Interface compliance (VectorStore, Plugins)
4. **End-to-End Tests**: Complete workflows
5. **Performance Tests**: Benchmarks and regression detection
6. **Security Tests**: Vulnerability scanning, penetration testing

### Quality Gates

**CI/CD Enforcements**:
- ✅ Test coverage ≥80%
- ✅ Type checking (mypy strict mode)
- ✅ Linting (ruff) 0 errors, <10 warnings
- ✅ Security scanning (no high/critical)
- ✅ Performance benchmarks (no regression >5%)

---

## Migration & Compatibility

### Backward Compatibility

**Guarantee**: Zero breaking changes throughout v0.4.x series

**Strategy**:
- All new features optional
- Default behaviour unchanged
- Existing tests must pass
- Configuration backward compatible
- Data migrations automatic

### Configuration Evolution

**v0.4.0+**: Plugin configuration added
**v0.4.0+**: VectorStore backend selection
**v0.4.0+**: Memory system configuration
**v0.4.0+**: LEANN backend options

**Principle**: Old configurations continue working, new features opt-in

---

## Documentation Strategy

### User Documentation

**For each release**:
1. **Tutorial**: Getting started with new features
2. **Guide**: Detailed usage and workflows
3. **Reference**: Complete API documentation
4. **Examples**: Working code samples

### Developer Documentation

**For each release**:
1. **ADR**: Architecture decisions
2. **Implementation Notes**: Technical details
3. **Testing Guide**: How to test new features
4. **Migration Guide**: Upgrade instructions

### Comprehensive Docs

**By v0.4.0**:
- Complete plugin development guide
- VectorStore backend development guide
- Memory system architecture documentation
- Performance tuning guide
- Security best practices
- Production deployment guide

---

## Risk Management

### High-Risk Items

**Memory System Complexity** (v0.4.0-v0.4.0):
- **Mitigation**: Incremental delivery with dedicated stability releases
- **Fallback**: Each release stands alone, can pause if issues

**LEANN Platform Support** (v0.4.0):
- **Mitigation**: Optional dependency, extensive testing
- **Fallback**: ChromaDB remains default and fully supported

### Medium-Risk Items

**Performance Overhead** (all releases):
- **Mitigation**: Benchmarking in each release, <5% regression limit
- **Fallback**: Performance optimisation in stability releases

**Plugin Security** (v0.4.0):
- **Mitigation**: Validation, sandboxing design (full impl later)
- **Fallback**: Plugin system can be disabled

### Low-Risk Items

**Test Coverage** (all releases):
- Well-established patterns
- Enforced via CI/CD
- Incremental improvement

**Refactoring** (v0.4.0, v0.4.0):
- Comprehensive existing tests
- Incremental changes
- Easy rollback

---

## Success Criteria for v0.4 Series

Version 0.4.x is successful if:

1. ✅ **Foundation Established**: Plugin architecture and VectorStore abstraction working
2. ✅ **Quality Maintained**: 80%+ test coverage throughout all releases
3. ✅ **Memory System Complete**: Personas, behaviour learning, temporal memory functional
4. ✅ **Performance Targets Met**: <2s queries, <100ms memory ops, <300ms graph queries
5. ✅ **LEANN Integrated**: 97% storage savings option available
6. ✅ **Zero Breaking Changes**: Full backward compatibility maintained
7. ✅ **Privacy Guaranteed**: 100% local operation, no data leaves device
8. ✅ **Production Ready**: Security hardened, documented, performant
9. ✅ **User Validated**: Personalisation demonstrably improves relevance
10. ✅ **Community Ready**: Plugin ecosystem enables contributions

---

## Evolution from v0.3.x

Version 0.4.x builds directly upon the foundation established by v0.3.x (13 releases, 437-501 hours, Q2-Q3 2026).

### Critical Dependencies from v0.3.x

**v0.3.7 - VectorStore Abstraction** (16-22 hours):
- Delivers the VectorStore abstract interface
- Refactors ChromaDB into clean implementation
- **Enables**: v0.4.0 refactoring and v0.4.0 LEANN integration
- **Status**: Foundation layer for multi-backend support

**v0.3.1 - Foundation & Metrics** (30 hours):
- Establishes evaluation framework (MRR, NDCG, Recall@k, RAGAS)
- **Enables**: v0.4.x quality validation and performance benchmarking
- **Status**: Measurement infrastructure for v0.4 features

**v0.3.3 - Advanced Query Processing** (53-55 hours):
- Implements reranking, query expansion, multi-query retrieval
- **Enables**: v0.4.0 personalized ranking builds on this
- **Status**: Advanced retrieval techniques foundation

**v0.3.13 - Polish & Integration** (26-32 hours):
- Delivers REST API with FastAPI
- **Coexists with**: v0.4.0 plugin architecture (independent extension mechanisms)
- **Status**: Production API ready for v0.4 memory features

### v0.3.x → v0.4.x Progression

| Aspect | v0.3.x Achievement | v0.4.x Addition |
|--------|-------------------|-----------------|
| **Retrieval** | State-of-the-art (reranking, multi-query) | +Personalized ranking |
| **Documents** | Multi-modal OCR (Docling, 97.9% accuracy) | +Temporal memory |
| **Architecture** | VectorStore abstraction | +Plugin system |
| **Backends** | ChromaDB (prepared for multi) | +LEANN (97% savings) |
| **Quality** | Metrics framework (MRR, RAGAS) | +Behaviour learning |
| **API** | REST API (FastAPI) | +Plugin extensions |
| **Testing** | 80%+ coverage standard | Maintained throughout |

### Timeline Integration

**v0.3.x**: Q2-Q3 2026 (6-8 months, 13 releases)
**v0.4.x**: Starts after v0.3.13 complete (10 releases)

**Clean Handoff**:
- v0.3.7 delivers VectorStore → v0.4.0 refines and uses it
- v0.3.1 establishes metrics → v0.4.x validates against them
- v0.3.13 delivers API → v0.4.0 adds plugin system (complementary)

### Scope Boundaries

**v0.3.x Focus**: Advanced retrieval, multi-modal documents, production data management
**v0.4.x Focus**: Personal memory, behaviour learning, temporal queries, alternative backends

**No Overlap**: Clear separation of concerns ensures no duplicate work or conflicts.

---

## Out of Scope (Deferred)

**Deferred to v0.5.x**:
- ❌ Web UI (basic or advanced modes)
- ❌ Vision-based retrieval
- ❌ Multi-modal embeddings
- ❌ Advanced temporal reasoning
- ❌ Memory analytics dashboard

**Deferred to v1.0**:
- ❌ Multi-user support
- ❌ API server
- ❌ Production web UI
- ❌ Cloud deployment
- ❌ Monitoring and dashboards

---

## Roadmap Restructuring Status

**Completed Phases** (Nov 2025):

### Phase 1: Critical Structural Fixes ✅
- Fixed version numbering across 8 release files
- Applied v0.2.10+ naming conventions (lowercase filenames)
- Audited and fixed all cross-references
- **Commit**: 07e5470 (14 files changed, 115 insertions, 115 deletions)

### Phase 4: Execution Framework ✅
- Created execution playbook (step-by-step implementation guide)
- Created progress tracker (real-time status monitoring)
- Created testing guide (comprehensive quality gates and testing standards)
- **Commit**: 764dd84 (4 files changed, 1,804 insertions)

### Phase 5: Enhancement Opportunities ✅
- Documented security hardening enhancements (HSM, sandboxing, audit logging)
- Documented performance optimisation opportunities (caching, parallel processing)
- Documented plugin ecosystem expansion strategy (marketplace, community)
- **Commit**: 7983500 (3 files changed, 3,219 insertions)

**Deferred Phases** (to be addressed after v0.3.x complete):

### Phase 2: Content Consolidation (Deferred)
- **Original Goal**: Consolidate overlapping content, remove redundancies
- **Why Deferred**: Requires significant refactoring best done during v0.4.x implementation when all release specifications are finalised
- **When to Revisit**: After v0.4.3 (memory foundation) when core architecture is stable

### Phase 3: Decision Framework Documentation (Deferred)
- **Original Goal**: Document decision-making frameworks and trade-offs
- **Why Deferred**: LEANN decision framework already well-documented in v0.4.5 and related ADRs; additional decision documentation can be added as implementation progresses
- **When to Revisit**: During v0.4.x implementation as design decisions arise

### Phase 6: Final Review & Polish (Deferred)
- **Original Goal**: Comprehensive review of all v0.4.x documentation for clarity, consistency, completeness
- **Why Deferred**: Most valuable after v0.4.x implementation when all specifications have been tested and refined through actual development
- **When to Revisit**: After v0.4.9 (before declaring v0.4.x complete)

**Rationale for Deferral**:
These phases involve refinement and polish best done after the v0.4.x implementation cycle, when:
1. All specifications have been tested through actual development
2. Design decisions have been validated or revised based on implementation experience
3. Content consolidation opportunities are clearer (after seeing what content was actually used)
4. Final polish can address lessons learned from the full implementation cycle

The completed phases (1, 4, 5) establish the critical foundation needed for autonomous implementation to begin once v0.3.x is complete.

---

## Related Documentation

**Planning**:
- [v0.3 Planning](../../../planning/version/v0.3/) - Advanced retrieval foundation
- [v0.4 Planning](../../../planning/version/v0.4/) - Memory system design overview

**Implementation Roadmaps**:
- [v0.3 Roadmap](../../README.md) - Advanced retrieval & document intelligence (13 releases, Q2-Q3 2026)
  - See especially [v0.3.7](../v0.3/v0.3.7.md) - VectorStore abstraction foundation
- [v0.4 Detailed Spec](v0.4-detailed-spec.md) - Original comprehensive roadmap (kept for reference)
- Individual release roadmaps:
  - Foundation & Security: [v0.4.0](v0.4.0.md) - [v0.4.4](v0.4.4.md)
  - Memory System Core: [v0.4.5](v0.4.5/README.md) - [v0.4.8](v0.4.8.md)
  - Advanced Features: [v0.4.9](v0.4.9.md) - [v0.4.10](v0.4.10/README.md)
  - Stabilisation & Production: [v0.4.11](v0.4.11.md) - [v0.4.13](v0.4.13.md)

**Implementation Guides**:
- [Execution Playbook](execution-playbook.md) - Step-by-step implementation guide for autonomous execution
- Progress Tracker - Real-time status tracking across all 14 releases
- [Testing Guide](testing-guide.md) - Comprehensive testing standards, quality gates, and success criteria

**Enhancement Opportunities** (beyond baseline):
- [Security Enhancements](security-enhancements.md) - Optional security hardening (HSM, sandboxing, audit logging, supply chain)
- [Performance Enhancements](performance-enhancements.md) - Optional performance optimisations (caching, parallel processing, monitoring)
- [Plugin Ecosystem](plugin-ecosystem.md) - Plugin ecosystem expansion strategy (official plugins, marketplace, community)

**Architecture**:
- [Architecture Overview](../../../planning/architecture/README.md) - System architecture
- [ADR-0015: VectorStore Abstraction](../../../decisions/adrs/0015-vectorstore-abstraction.md)
- Additional ADRs created in each release

**Reference**:
- [CLI Enhancements Catalogue](../../../planning/interfaces/cli/enhancements.md)
- [LEANN Integration Analysis](../../../decisions/2025-11-16-leann-integration-analysis.md)

---
