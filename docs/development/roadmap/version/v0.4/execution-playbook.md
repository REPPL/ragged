# v0.4.x Execution Playbook

**Purpose**: Step-by-step guide for autonomous implementation of v0.4.x roadmap

**Status**: Ready for execution after v0.3.x complete

**Total Effort**: 195-242 hours across 10 releases

---

## Prerequisites

### Hard Blockers (Must Complete Before Starting)

**CRITICAL**: v0.4.x implementation **CANNOT** begin until all prerequisites met.

#### 1. v0.3.x Series Complete
- **Status**: ⏳ In Progress (Target: Q2-Q3 2026)
- **Required**: All 13 releases (v0.3.0-v0.3.13) shipped
- **Verification**:
  ```bash
  git tag | grep "v0.3" | wc -l  # Should show 13 tags
  ```

#### 2. v0.3.7 VectorStore Abstraction Available
- **Status**: Foundation for v0.4.1 and v0.4.8
- **Verification**: Check `src/storage/vector_store.py` exists with abstract interface
- **Dependency Chain**: v0.3.7 → v0.4.1 → v0.4.8

#### 3. Development Environment Ready
- **Python**: 3.11+
- **Dependencies**: All v0.3.x dependencies installed
- **Tools**: pytest, mypy, ruff, bandit configured
- **CI/CD**: All quality gates passing

---

## Execution Sequence

### Foundation Phase: v0.4.0 - v0.4.2 (55-67 hours)

**Goal**: Establish architecture and quality baseline before memory features

#### v0.4.0 - Plugin Architecture (25-30 hours)

**When to Start**: Immediately after v0.3.13 ships

**Steps**:
1. **Read**: [v0.4.0.md](v0.4.0.md) - Complete specification
2. **Design Review**: Validate plugin architecture decisions
3. **Implementation**:
   - Create `src/plugins/` module structure
   - Implement 4 plugin interfaces (Embedder, Retriever, Processor, Command)
   - Add entry point discovery system
   - Build plugin registry and loader
   - Create CLI commands (`ragged plugin list/install/remove`)
4. **Testing** (6-8 hours):
   - Unit tests: Plugin interfaces, loader, registry
   - Integration tests: End-to-end plugin workflows
   - Sample plugins: 2-3 working examples
   - Target: 90%+ coverage for plugin system
5. **Documentation** (3-4 hours):
   - Plugin development guide
   - API reference
   - Example plugins with tutorials
6. **Quality Gates**:
   - All tests passing
   - Type checking: `mypy src/plugins/ --strict`
   - Linting: `ruff check src/plugins/`
   - Security: `bandit -r src/plugins/`
7. **Commit & Tag**:
   ```bash
   git add src/plugins/ tests/plugins/ docs/
   git commit -m "feat(plugins): implement plugin architecture (v0.4.0)"
   git tag v0.4.0
   ```
8. **Verification**:
   - CLI: `ragged plugin list` works
   - Sample plugin loads successfully
   - All existing tests still pass (no regressions)

**Rollback**: If plugin system breaks existing functionality, revert tag and fix before proceeding.

---

#### v0.4.1 - VectorStore Abstraction (18-22 hours)

**Dependencies**: v0.4.0 complete, v0.3.7 foundation available

**Steps**:
1. **Read**: [v0.4.1.md](v0.4.1.md) - Builds on v0.3.7
2. **Refactor**:
   - Review v0.3.7 VectorStore interface
   - Refactor `src/storage/chromadb.py` into `ChromaDBStore` class
   - Implement factory pattern for backend selection
   - Update all callers to use abstraction
3. **Testing** (4 hours):
   - Contract tests: VectorStore interface compliance
   - ChromaDB implementation tests
   - Integration tests: Verify no regressions
   - Performance tests: <5% overhead requirement
4. **Documentation** (1 hour):
   - Backend development guide
   - API reference
5. **Quality Gates**:
   - All existing tests pass
   - Performance maintained
   - Type safety: mypy strict mode
6. **Commit & Tag**:
   ```bash
   git add src/storage/ tests/storage/
   git commit -m "refactor(storage): implement VectorStore abstraction (v0.4.1)"
   git tag v0.4.1
   ```

**Rollback**: If abstraction introduces bugs, revert to v0.4.0 and refine design.

---

#### v0.4.2 - Code Quality & Security Baseline (12-15 hours)

**Dependencies**: v0.4.1 complete

**Steps**:
1. **Read**: [v0.4.2.md](v0.4.2.md) - Quality and security focus
2. **Code Quality** (4-5 hours):
   - Run linters and fix all issues
   - Type hint completion
   - Complexity reduction (target: <10 per function)
   - Code deduplication
3. **Performance Baseline** (3-4 hours):
   - Create `scripts/benchmark.py`
   - Run benchmarks on representative workloads
   - Record baselines in `benchmarks/v0.4.2-baseline.json`
   - Configure CI regression detection
4. **Security Audit Preparation** (3-4 hours):
   - Run security scans: `bandit`, `safety`, `pip-audit`
   - Fix all high/critical findings
   - Document memory system architecture (for v0.4.3 audit)
   - Create privacy threat model
5. **Documentation** (1-2 hours):
   - Security guidelines
   - Performance tuning guide
6. **Commit & Tag**:
   ```bash
   git add src/ tests/ scripts/benchmark.py benchmarks/
   git commit -m "chore(quality): establish code quality and security baseline (v0.4.2)"
   git tag v0.4.2
   ```

**Security Gate**: Before proceeding to v0.4.3, initiate formal security audit (2-3 weeks concurrent with v0.4.3 development).

---

### Core Features Phase: v0.4.3 - v0.4.5 (85-98 hours)

**Goal**: Implement personal memory system with stability

#### v0.4.3 - Memory Foundation (35-40 hours)

**🔒 SECURITY GATE**: Implementation **BLOCKED** until security audit passes

**Dependencies**:
- v0.4.2 complete
- Security audit PASSED (see [v0.4.3/security-audit.md](v0.4.3/security-audit.md))

**Pre-Implementation Checklist**:
- [ ] Security audit complete
- [ ] Audit report: NO critical findings
- [ ] All high-priority recommendations addressed
- [ ] Privacy framework documented
- [ ] Testing scenarios prepared

**Steps**:
1. **Security Verification**: Confirm audit pass before ANY code changes
2. **Read**: [v0.4.3/README.md](v0.4.3/README.md) - Complete specification
3. **Implementation** (25-30 hours):
   - Persona management system (`src/memory/personas.py`)
   - Interaction tracking with SQLite (`src/memory/interactions.py`)
   - Knowledge graph foundation with Kuzu (`src/memory/graph.py`)
   - Memory CLI commands
   - Privacy controls and encryption
4. **Testing** (7-9 hours):
   - Unit tests: All memory components
   - Integration tests: End-to-end workflows
   - Privacy tests: Data isolation, encryption, user controls
   - Target: 85%+ coverage
5. **Documentation** (3-4 hours):
   - Memory system architecture
   - Privacy documentation
   - User guide for memory features
6. **Commit & Tag**:
   ```bash
   git add src/memory/ tests/memory/ docs/
   git commit -m "feat(memory): implement personal memory foundation (v0.4.3)"
   git tag v0.4.3
   ```

**If Audit Failed**: Do NOT proceed. Address findings first, re-audit, only implement when passed.

---

#### v0.4.4 - Stability & Performance (15-18 hours)

**Dependencies**: v0.4.3 complete

**Steps**:
1. **Read**: [v0.4.4.md](v0.4.4.md) - Stability focus
2. **Optimization** (6-7 hours):
   - Database query optimization (indexes, prepared statements)
   - Caching strategies
   - Memory leak detection and fixes
3. **Integration Testing** (4-5 hours):
   - Multi-persona scenarios
   - Concurrent access tests
   - Long-running stability tests (24-hour test)
4. **Performance Targets**:
   - Memory operations: <100ms
   - Graph queries: <300ms
   - No memory leaks over 1000 operations
5. **Commit & Tag**:
   ```bash
   git commit -m "perf(memory): optimize memory system performance (v0.4.4)"
   git tag v0.4.4
   ```

---

#### v0.4.5 - Behaviour Learning (35-40 hours)

**Dependencies**: v0.4.4 complete

**Steps**:
1. **Read**: [v0.4.5.md](v0.4.5.md) - Personalisation system
2. **Implementation** (26-30 hours):
   - Topic extraction from queries
   - Behaviour learning system
   - Personalised ranking algorithm
   - RAG pipeline integration
   - Interest profile analytics
3. **Testing** (6-8 hours):
   - Validate personalisation improves relevance >15%
   - Topic extraction accuracy: 80%+
   - End-to-end performance: <2s
4. **LEANN Decision Point** (1-2 hours):
   - Measure actual storage usage with memory system
   - Evaluate against decision criteria (see README.md)
   - Document decision in ADR-0018
   - **Outcome**: Proceed with v0.4.8 OR defer to v0.5.x
5. **Commit & Tag**:
   ```bash
   git commit -m "feat(memory): implement behaviour learning and personalisation (v0.4.5)"
   git tag v0.4.5
   ```

---

### Advanced Features Phase: v0.4.6 - v0.4.8 (90-107 hours)

#### v0.4.6 - Refactoring (10-12 hours)

**Steps**: See [v0.4.6.md](v0.4.6.md)
- Code consolidation, complexity reduction
- Architecture pattern enforcement
- Dependency optimization

---

#### v0.4.7 - Temporal Memory (40-45 hours)

**Steps**: See [v0.4.7.md](v0.4.7.md)
- Temporal fact storage
- Timeline query engine
- Time-aware memory retrieval

---

#### v0.4.8 - LEANN Backend (35-42 hours) **CONDITIONAL**

**⚠️ ONLY IF**: v0.4.5 decision was "Proceed with LEANN"

**Steps**: See [v0.4.8.md](v0.4.8.md)
- LEANN backend implementation
- Migration tools
- Backend selection system

**If Deferred**: Skip v0.4.8, proceed directly to v0.4.9

---

### Stabilisation Phase: v0.4.9 (15-20 hours)

**Dependencies**: v0.4.7 complete, v0.4.8 complete OR skipped

**Steps**: See [v0.4.9.md](v0.4.9.md)

**Release Checklist**:
- [ ] All v0.4.0-v0.4.8 features merged
- [ ] All tests passing (including privacy suite)
- [ ] Performance benchmarks validated
- [ ] Security audit recommendations implemented
- [ ] Documentation complete and reviewed
- [ ] CHANGELOG.md updated
- [ ] Version bump to v0.4.9
- [ ] Git tag created
- [ ] GitHub release published
- [ ] PyPI package published

---

## Quality Gates (Enforce at Every Release)

**See**: [testing-guide.md](testing-guide.md#quality-gates-apply-to-every-release) for comprehensive specifications, pass criteria, and failure actions.

### Required Checks Before Tagging (Quick Reference)

```bash
# 1. All tests pass
pytest --cov=src --cov-report=term-missing
# Coverage must be ≥80% overall

# 2. Type checking
mypy src/ --strict
# Must pass with zero errors

# 3. Linting
ruff check src/
# Zero errors, <10 warnings

# 4. Security scan
bandit -r src/
# No high/critical findings

# 5. Performance regression check
python scripts/benchmark.py
# No regression >5% from baseline
```

---

## Rollback Procedures

### If Release Breaks Existing Functionality

```bash
# 1. Revert tag
git tag -d v0.4.X
git push origin :refs/tags/v0.4.X

# 2. Revert commits
git revert <commit-hash>

# 3. Fix issues

# 4. Re-tag when fixed
git tag v0.4.X
git push origin v0.4.X
```

### If Security Audit Fails (v0.4.3 gate)

1. **DO NOT** proceed with v0.4.3 implementation
2. Address all critical and high findings
3. Update design documentation
4. Re-submit for audit
5. Only proceed when audit passes

---

## Progress Tracking

See [progress-tracker.md](progress-tracker.md) for detailed status tracking.

**Quick Status Check**:
```bash
git tag | grep "v0.4" | wc -l  # Count completed releases
```

---

## Success Criteria for v0.4 Series

Version 0.4.x is successful if all criteria met:

1. ✅ Plugin architecture working (v0.4.0)
2. ✅ VectorStore abstraction functional (v0.4.1)
3. ✅ 80%+ test coverage maintained throughout
4. ✅ Memory system complete (personas, learning, temporal)
5. ✅ Performance targets met (<2s queries, <100ms memory ops)
6. ✅ LEANN integrated (if decision was "proceed") OR deferred (if "defer")
7. ✅ Zero breaking changes maintained
8. ✅ 100% local operation (no data leaks)
9. ✅ Security audit passed
10. ✅ Production-ready quality

---

## Related Documentation

- [v0.4 Overview](README.md) - Series overview and decision framework
- [Progress Tracker](progress-tracker.md) - Status tracking
- [v0.4.0](v0.4.0.md) through [v0.4.9](v0.4.9.md) - Individual release specs
- [v0.4.3 Security Audit](v0.4.3/security-audit.md) - **Critical gate requirements**

---

**Status**: Ready for autonomous execution

