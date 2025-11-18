# Ragged v0.2.7 Roadmap - CLI Structure Refactoring

**Status:** 🔄 IN PROGRESS (Current Version)

**Total Hours:** TBD actual (originally estimated 137-151h for broader scope)

**Focus:** CLI architecture refactoring, folder ingestion, HTML processing

**Breaking Changes:** None (multi-collection deferred to later version)

**Implementation Note:** Scope significantly refined to focus on CLI foundation

## Overview

Version 0.2.7 refactored the CLI from a monolithic structure to a modular command-based architecture, establishing a foundation for future enhancements. Additionally implemented user-requested features: folder ingestion and HTML processing.

**Actual Focus (Refined from Original Plan):**
- ✅ CLI command modularisation (14 modules created)
- ✅ Folder ingestion with recursive scanning
- ✅ HTML processing support (Trafilatura + BeautifulSoup)
- ✅ Batch processing with progress bars
- 🔄 Additional CLI enhancements (transitioned to v0.2.8)
- 📅 Performance optimisations (deferred to v0.2.9)

**Key Achievement:** CLI entry point reduced from 586+ lines to 107 lines (82% reduction)

**See:** [v0.2.7 Implementation Record](../../implementation/version/v0.2/v0.2.7.md)

---

## Feature Areas

The v0.2.7 roadmap is organised into four main areas:

### 1. User Experience Improvements (42 hours)
Comprehensive UX enhancements including seamless model switching, multi-collection support, enhanced progress indicators, and smart query suggestions.

**Details:** [UX Improvements](./features/ux-improvements.md)

**Key Features:**
- UX-001: Seamless Model Switching (8h)
- UX-002: Multi-Collection Support (10h)
- UX-003: Enhanced Progress Indicators (4h)
- UX-004: Smart Query Suggestions (6h)
- UX-005-007: Additional improvements (14h)

---

### 2. Performance Optimisations (37 hours)
Performance improvements including embedding caching, async processing, lazy model loading, and various query optimisations.

**Details:** [Performance Optimisations](./features/performance-optimisations.md)

**Key Features:**
- PERF-001: Embedding Caching (5h)
- PERF-002: Async Document Processing (12h)
- PERF-003: Lazy Model Loading (6h)
- PERF-004: BM25 Index Persistence (3h)
- PERF-005: Chunking Optimisation (5h)
- PERF-006: Vector Store Query Optimisation (6h)

**Performance Targets:**
- Batch ingestion: 2-4x faster (async)
- Query time: 50-90% faster (caching)
- Startup time: <2 seconds (BM25 persistence)
- Memory usage: <100MB idle (lazy loading)
- Model switching: <2 seconds

---

### 3. Configuration Management (10 hours)
Runtime configuration updates and configuration profiles for flexible system behaviour.

**Details:** [Configuration Management](./features/configuration-management.md)

**Key Features:**
- CONFIG-001: Runtime Configuration Updates (4h)
- CONFIG-002: Configuration Profiles (6h)

---

### 4. CLI Enhancements (48-62 hours)
Eleven comprehensive CLI enhancements transforming ragged into a production-ready tool.

**Details:** [CLI Enhancements](./features/cli-enhancements.md)

**Key Features:**
- CLI-001: Advanced Search & Filtering (3-4h)
- CLI-002: Metadata Management (4-5h)
- CLI-003: Bulk Operations (5-6h)
- CLI-004: Export/Import Utilities (6-8h)
- CLI-005: Output Format Options (3-4h)
- CLI-006: Query History & Replay (4-5h)
- CLI-007: Verbose & Quiet Modes (2-3h)
- CLI-008: Configuration Validation (3-4h)
- CLI-009: Environment Information (2-3h)
- CLI-010: Cache Management (3-4h)
- CLI-011: Shell Completion (4-5h)

---


## Summary & Implementation Order

### Recommended Implementation Order

**Session 1: Core UX** (30 hours)
1. UX-001: Model switching (8h)
2. UX-002: Multi-collection support (10h)
3. UX-003: Enhanced progress (4h)
4. PERF-001: Embedding caching (5h)
5. Testing and bug fixes (3h)

**Session 2: Performance** (30 hours)
1. PERF-002: Async processing (12h)
2. PERF-003: Lazy model loading (6h)
3. PERF-004: BM25 persistence (3h)
4. UX-006: Better error messages (6h)
5. Testing and optimisation (3h)

**Session 3: Polish** (30 hours)
1. CONFIG-001: Runtime config (4h)
2. CONFIG-002: Config profiles (6h)
3. UX-004: Query suggestions (6h)
4. UX-005: Query refinement (8h)
5. UX-007: Document preview (4h)
6. Final testing and documentation (2h)

**Session 4: Optimisation & Testing** (20 hours)
1. PERF-005: Chunking optimisation (5h)
2. PERF-006: Query optimisation (6h)
3. Comprehensive testing (6h)
4. Documentation updates (3h)

**Session 5: CLI Foundation** (27 hours)
1. CLI-007: Verbose & quiet modes (3h)
2. CLI-008: Configuration validation (4h)
3. CLI-009: Environment information (3h)
4. CLI-005: Output format options (4h)
5. CLI-011: Shell completion (5h)
6. CLI-010: Cache management (4h)
7. Testing and integration (4h)

**Session 6: CLI Advanced Features** (30 hours)
1. CLI-001: Advanced search & filtering (4h)
2. CLI-002: Metadata management (5h)
3. CLI-003: Bulk operations (6h)
4. CLI-004: Export/import utilities (8h)
5. CLI-006: Query history & replay (5h)
6. Testing and documentation (2h)

### Performance Targets

By end of v0.2.7:
- [ ] Batch ingestion: 2-4x faster (async)
- [ ] Query time: 50-90% faster (caching)
- [ ] Startup time: <2 seconds (BM25 persistence)
- [ ] Memory usage: <100MB idle (lazy loading)
- [ ] Model switching: <2 seconds

### Breaking Changes

**Multi-Collection System**:
- Existing documents auto-migrate to "default" collection
- ChromaDB collection names may change
- Migration script runs on first v0.2.7 startup

**Migration Checklist**:
- [ ] Backup existing data before upgrade
- [ ] Run migration script
- [ ] Verify all documents accessible in "default" collection
- [ ] Test queries work correctly

### Acceptance Criteria

v0.2.7 is successful if:
1. ✅ Model switching works seamlessly
2. ✅ Multi-collection system stable
3. ✅ Performance targets met
4. ✅ User experience significantly improved
5. ✅ Migration from v0.2.5 works flawlessly
6. ✅ All 11 CLI enhancements functional and tested
7. ✅ CLI provides comprehensive document management capabilities
8. ✅ Shell completion works for bash, zsh, and fish
9. ✅ All tests pass with ≥75% coverage

---

## Related Documentation

- [Previous Version](../v0.2.6/README.md) - Documentation & structural improvements
- [Next Version](../v0.3/README.md) - Advanced RAG features
- [Planning](../../planning/version/v0.2/) - Design goals for v0.2 series
- [CLI Enhancements Catalogue](../../planning/interfaces/cli/enhancements.md) - Comprehensive CLI specifications
- [Version Overview](../README.md) - Complete version comparison

---

**Next Steps**: After completing v0.2.7, proceed to v0.3 for advanced RAG features.

---

## Related Documentation

- [Previous Version](../v0.2.6/README.md) - Documentation & structural improvements
- [Next Version](../v0.3/README.md) - Advanced RAG features
- [Planning](../../planning/version/v0.2/) - Design goals for v0.2 series
- [CLI Enhancements Catalogue](../../planning/interfaces/cli/enhancements.md) - Comprehensive CLI specifications
- [Version Overview](../README.md) - Complete version comparison
- [v0.2.7 Implementation Record (In Progress)](../../implementation/version/v0.2/v0.2.7.md)

---

**Next Steps**: After completing v0.2.7, proceed to v0.2.8 for additional CLI enhancements.

**License:** GPL-3.0
