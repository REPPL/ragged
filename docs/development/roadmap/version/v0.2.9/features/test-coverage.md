# Test Coverage Improvements

**Phase**: 3 | **Effort**: 6-8h | **Priority**: MUST-HAVE

**Target**: 90%+ overall, 95%+ critical paths

**Tasks**:
1. Measure current coverage
2. Identify gaps
3. Write unit tests for uncovered code
4. Add property-based tests (hypothesis)
5. Add concurrent operation tests
6. Long-running stability tests

**Tools**:
- pytest-cov for coverage
- hypothesis for property testing
- pytest-xdist for parallel tests

**Success**: 90%+ coverage, all critical paths 95%+

**Timeline**: 6-8h

---

**Status**: ⚠️ PARTIAL (commits 898250c, c4be33c)

**Completed**:
- Measured current coverage: 69.2% test/source ratio
- Identified 16 critical files without tests
- Added 2,407 lines of comprehensive tests across 6 critical modules:
  - utils/hashing.py + security.py (620 lines, 120+ tests)
  - config/constants.py + feature_flags.py (620 lines, 120+ tests)
  - chunking/splitters/* (730 lines, 130+ tests)
- Achieved 2.85x test/source ratio for new modules (target: 1x)
- Reduced critical untested files from 16 to 10 (37.5% progress)

**Remaining**:
- 10 critical files still need tests (embeddings, generation, cli, main)
- Property-based tests (hypothesis) - not yet added
- Long-running stability tests - not yet added
- Overall coverage measurement (pytest-cov run) - pending

**Next Steps**: Add tests for embeddings and generation modules to reach 90%+ target.
