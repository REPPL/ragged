# Ragged v0.4.x Roadmap Overview - Personal Memory & Knowledge Graphs

**Version Series:** v0.4.0 - v0.4.10

**Status:** Planned

**Total Hours:** 195-242 hours (across 10 incremental releases)

**Focus:** Foundation-first architecture with plugin system, personal memory, knowledge graphs, and LEANN backend

**Breaking Changes:** None - All features are additive and optional

**Dependencies:** v0.3.x complete (advanced retrieval, evaluation framework, VectorStore abstraction awareness)

---

## Vision

Version 0.4.x transforms ragged from a document retrieval tool into an intelligent personal knowledge assistant through **10 incremental releases** that prioritise architectural excellence, comprehensive testing, and production-ready stability.

**Core Principle**: Foundation first, features second - establish rock-solid architecture, testing infrastructure (80%+ coverage), and code quality before introducing complex memory and personalisation features.

**Key Capabilities** (by end of v0.4.10):
- **Plugin Architecture**: Extensible system for custom embedders, retrievers, processors, and commands
- **VectorStore Abstraction**: Support for multiple backends (ChromaDB, LEANN)
- **Personal Memory System**: Persona management, behaviour learning, temporal memory
- **Knowledge Graphs**: Connect topics, documents, and concepts over time
- **Personalised Ranking**: Boost relevant documents based on learned interests
- **LEANN Backend**: 97% storage savings through graph-based retrieval
- **Production-Ready**: Comprehensive testing, performance optimisation, security hardening

---

## Release Strategy

### Foundation Phase (v0.4.1 - v0.4.3)
**Focus**: Architecture, testing infrastructure, code quality
**Hours**: 55-67
**Goal**: Establish foundation that enables safe, rapid feature development

### Core Features Phase (v0.4.4 - v0.4.6)
**Focus**: Memory system implementation with stability
**Hours**: 85-98
**Goal**: Deliver persona management, behaviour learning, and personalisation

### Advanced Features Phase (v0.4.7 - v0.4.9)
**Focus**: Refactoring, temporal memory, LEANN backend
**Hours**: 90-107
**Goal**: Complete memory system and alternative storage backend

### Stabilisation Phase (v0.4.10)
**Focus**: Production readiness, comprehensive testing, performance
**Hours**: 15-20
**Goal**: Release-ready v0.4 with all features polished and tested

---

## Incremental Releases

### [v0.4.1 - Plugin Architecture & Testing Foundation](v0.4.1.md) (25-30h)

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

### [v0.4.2 - VectorStore Abstraction & Refactoring](v0.4.2.md) (18-22h)

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

### [v0.4.3 - Code Quality & Stability Release](v0.4.3.md) (12-15h)

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

### [v0.4.4 - Memory Foundation: Personas & Tracking](v0.4.4.md) (35-40h)

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

### [v0.4.5 - Stability & Performance Enhancement](v0.4.5.md) (15-18h)

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

### [v0.4.6 - Behaviour Learning & Personalisation](v0.4.6.md) (35-40h)

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

### [v0.4.7 - Refactoring & Architecture Improvements](v0.4.7.md) (10-12h)

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

### [v0.4.8 - Temporal Memory System](v0.4.8.md) (40-45h)

**Status**: Planned | **Priority**: P0 - Advanced Feature

**Focus**: Time-aware memory and queries

**Deliverables**:
- ✅ Temporal fact storage
- ✅ Timeline query engine
- ✅ Temporal reasoning capabilities
- ✅ Time-based memory retrieval
- ✅ CLI temporal commands
- ✅ Comprehensive testing (4-7h)

**Success Criteria**:
- Temporal queries work correctly
- Time-aware fact handling
- Historical activity tracking
- Timeline visualisation functional

---

### [v0.4.9 - LEANN Backend Integration](v0.4.9.md) (35-42h)

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

### [v0.4.10 - Production Readiness & Final Stabilisation](v0.4.10.md) (15-20h)

**Status**: Planned | **Priority**: P0 - Release

**Focus**: Final polish and production readiness

**Deliverables**:
- ✅ Comprehensive end-to-end testing
- ✅ Performance benchmarking suite
- ✅ Security hardening review
- ✅ Documentation polish and completion
- ✅ Release preparation and packaging
- ✅ Migration guides and upgrade paths

**Success Criteria**:
- All features tested end-to-end
- Performance benchmarks met
- Security audit passed
- Documentation complete
- Ready for production use

---

## Total Effort Summary

| Phase | Releases | Hours | Focus |
|-------|----------|-------|-------|
| Foundation | v0.4.1 - v0.4.3 | 55-67 | Architecture, testing, quality |
| Core Features | v0.4.4 - v0.4.6 | 85-98 | Memory system, personalisation |
| Advanced | v0.4.7 - v0.4.9 | 90-107 | Refactoring, temporal, LEANN |
| Stabilisation | v0.4.10 | 15-20 | Production readiness |
| **Total** | **10 releases** | **195-242** | **Complete v0.4** |

**Original v0.4.0 estimate**: 180-225 hours
**New v0.4.x total**: 195-242 hours
**Difference**: +15-17 hours (+8%) for dedicated quality/stability releases

**Justification**: Additional time investment in foundation, testing, and stability releases (v0.4.3, v0.4.5, v0.4.7, v0.4.10) pays dividends in reduced debugging, easier maintenance, and higher quality.

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

**Decision**: Break v0.4.0 into 10 incremental releases instead of 1 large release

**Rationale**:
- Manage complexity and risk
- Deliver value progressively
- Get user feedback early
- Easier testing and debugging
- Clear rollback points

**Impact**: Better quality, more flexibility, easier project management

### 3. Dedicated Stability Releases

**Decision**: Include 4 stability-focused releases (v0.4.3, v0.4.5, v0.4.7, v0.4.10)

**Rationale**:
- Foundation-first principle requires quality gates
- Memory system complexity demands stability focus
- Technical debt reduction prevents accumulation
- Performance optimisation needs dedicated time

**Impact**: Higher quality, better performance, easier maintenance

### 4. Plugin Architecture First

**Decision**: Implement plugin system before memory features (v0.4.1)

**Rationale**:
- Enables extensibility from start
- Memory system can use plugin patterns
- Community can contribute early
- Demonstrates architectural commitment

**Impact**: Flexibility, extensibility, community engagement

### 5. VectorStore Abstraction Early

**Decision**: Implement abstraction layer before memory features (v0.4.2)

**Rationale**:
- LEANN integration easier later (v0.4.9)
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

**v0.4.1+**: Plugin configuration added
**v0.4.2+**: VectorStore backend selection
**v0.4.4+**: Memory system configuration
**v0.4.9+**: LEANN backend options

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

**By v0.4.10**:
- Complete plugin development guide
- VectorStore backend development guide
- Memory system architecture documentation
- Performance tuning guide
- Security best practices
- Production deployment guide

---

## Risk Management

### High-Risk Items

**Memory System Complexity** (v0.4.4-v0.4.8):
- **Mitigation**: Incremental delivery with dedicated stability releases
- **Fallback**: Each release stands alone, can pause if issues

**LEANN Platform Support** (v0.4.9):
- **Mitigation**: Optional dependency, extensive testing
- **Fallback**: ChromaDB remains default and fully supported

### Medium-Risk Items

**Performance Overhead** (all releases):
- **Mitigation**: Benchmarking in each release, <5% regression limit
- **Fallback**: Performance optimisation in stability releases

**Plugin Security** (v0.4.1):
- **Mitigation**: Validation, sandboxing design (full impl later)
- **Fallback**: Plugin system can be disabled

### Low-Risk Items

**Test Coverage** (all releases):
- Well-established patterns
- Enforced via CI/CD
- Incremental improvement

**Refactoring** (v0.4.2, v0.4.7):
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
- **Enables**: v0.4.2 refactoring and v0.4.9 LEANN integration
- **Status**: Foundation layer for multi-backend support

**v0.3.1 - Foundation & Metrics** (30 hours):
- Establishes evaluation framework (MRR, NDCG, Recall@k, RAGAS)
- **Enables**: v0.4.x quality validation and performance benchmarking
- **Status**: Measurement infrastructure for v0.4 features

**v0.3.3 - Advanced Query Processing** (53-55 hours):
- Implements reranking, query expansion, multi-query retrieval
- **Enables**: v0.4.6 personalized ranking builds on this
- **Status**: Advanced retrieval techniques foundation

**v0.3.13 - Polish & Integration** (26-32 hours):
- Delivers REST API with FastAPI
- **Coexists with**: v0.4.1 plugin architecture (independent extension mechanisms)
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
- v0.3.7 delivers VectorStore → v0.4.2 refines and uses it
- v0.3.1 establishes metrics → v0.4.x validates against them
- v0.3.13 delivers API → v0.4.1 adds plugin system (complementary)

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

## Related Documentation

**Planning**:
- [v0.3 Planning](../../../planning/version/v0.3/) - Advanced retrieval foundation
- [v0.4 Planning](../../../planning/version/v0.4/) - Memory system design overview

**Implementation Roadmaps**:
- [v0.3.0 Roadmap](../../v0.3.0/README.md) - Advanced retrieval & document intelligence (13 releases, Q2-Q3 2026)
  - See especially [v0.3.7](../../v0.3.0/v0.3.7.md) - VectorStore abstraction foundation
- [v0.4.0 Detailed Spec](v0.4.0-DETAILED-SPEC.md) - Original comprehensive roadmap (kept for reference)
- Individual release roadmaps: [v0.4.1](v0.4.1.md) through [v0.4.10](v0.4.10.md)

**Architecture**:
- [Architecture Overview](../../../planning/architecture/README.md) - System architecture
- [ADR-0015: VectorStore Abstraction](../../../decisions/adrs/0015-vectorstore-abstraction.md)
- Additional ADRs created in each release

**Reference**:
- [CLI Enhancements Catalogue](../../../planning/interfaces/cli/enhancements.md)
- [LEANN Integration Analysis](../../../decisions/2025-11-16-leann-integration-analysis.md)

---
