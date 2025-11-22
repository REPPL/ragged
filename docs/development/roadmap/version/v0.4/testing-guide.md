# v0.4.x Testing Guide & Success Criteria

**Purpose**: Comprehensive testing standards, checklists, and acceptance criteria for v0.4.x series

**Audience**: Developers, QA, autonomous implementation agents

---

## Testing Philosophy

**Core Principle**: **Every release must pass ALL quality gates before tagging**

### Testing Pyramid for v0.4.x

```
           E2E Tests (10%)
         ─────────────────
        Integration Tests (30%)
      ───────────────────────────
     Unit Tests (60%)
   ─────────────────────────────────
```

**Coverage Targets**:
- Unit tests: 80%+ coverage (core functionality 90%+)
- Integration tests: All major workflows covered
- E2E tests: Critical user journeys validated
- Privacy tests: 100% of privacy-sensitive operations

---

## Quality Gates (Apply to Every Release)

**MANDATORY**: All gates must pass before `git tag vX.X.X`

### Gate 1: Test Coverage

```bash
# Run full test suite with coverage
pytest --cov=src --cov-report=term-missing --cov-report=html

# Requirements:
# - Overall coverage: ≥80%
# - Core modules coverage: ≥90%
# - New code coverage: ≥85%
# - No untested critical paths
```

**Pass Criteria**:
- ✅ Overall coverage ≥80%
- ✅ Core modules (memory/, storage/, retrieval/) ≥90%
- ✅ All new code in this release ≥85%
- ✅ No critical security functions untested

**Failure Actions**:
- Identify uncovered code
- Add tests for critical paths first
- Document any intentionally untested code (with justification)
- Re-run until passing

---

### Gate 2: Type Safety

```bash
# Run mypy strict type checking
mypy src/ --strict --show-error-codes

# Requirements:
# - Zero type errors
# - All function signatures typed
# - All return types explicit
# - No `Any` types unless justified
```

**Pass Criteria**:
- ✅ Zero mypy errors
- ✅ All public APIs fully typed
- ✅ No use of `# type: ignore` without justification comment

**Failure Actions**:
- Fix type errors immediately
- Add missing type annotations
- Document justified uses of `Any` or `# type: ignore`

---

### Gate 3: Code Quality

```bash
# Run ruff linter
ruff check src/ --select=ALL

# Requirements:
# - Zero errors
# - <10 warnings (document each)
# - Complexity: McCabe <10 per function
```

**Pass Criteria**:
- ✅ Zero ruff errors
- ✅ <10 warnings total
- ✅ All warnings documented with rationale
- ✅ Function complexity <10

**Failure Actions**:
- Fix all errors
- Reduce complexity for functions >10
- Document acceptable warnings

---

### Gate 4: Security Scan

```bash
# Run bandit security scanner
bandit -r src/ -ll

# Run dependency audit
pip-audit

# Run safety check
safety check --json
```

**Pass Criteria**:
- ✅ Zero high/critical findings in bandit
- ✅ Zero known CVEs in dependencies
- ✅ All medium findings documented with mitigation

**Failure Actions**:
- Fix all high/critical security issues immediately
- Update vulnerable dependencies
- Document accepted risks for medium findings

---

### Gate 5: Performance Regression

```bash
# Run benchmarks
python scripts/benchmark.py --compare-to v0.4.X-baseline.json

# Requirements:
# - No regression >5% on any benchmark
# - New features meet performance targets
```

**Pass Criteria**:
- ✅ No regression >5% from baseline
- ✅ All new features meet documented targets
- ✅ Memory usage stable or improved

**Failure Actions**:
- Profile performance bottlenecks
- Optimise slow operations
- Update baseline if intentional change (document reason)

---

### Gate 6: Privacy Validation (v0.4.3+)

```bash
# Run privacy test suite
pytest tests/privacy/ -v

# Requirements:
# - Zero network calls during memory operations
# - All data in ~/.ragged/memory/
# - Persona isolation verified
# - Encryption validated
```

**Pass Criteria** (see [v0.4.5/testing-scenarios.md](v0.4.5/testing-scenarios.md)):
- ✅ No external network calls (monitored)
- ✅ All data stored in expected location
- ✅ Personas completely isolated
- ✅ Encryption at rest working
- ✅ User controls functional (view, delete, export)
- ✅ PII detection working

**Failure Actions**:
- Investigate any network calls immediately
- Fix data locality issues
- Strengthen persona isolation
- Verify encryption implementation

---

## Release-Specific Testing Checklists

### v0.4.0 - Plugin Architecture

**Feature Tests**:
- [ ] Plugin discovery works (entry points)
- [ ] Plugin loading successful (4 plugin types)
- [ ] Plugin registry manages plugins correctly
- [ ] CLI commands work (`list`, `install`, `remove`)
- [ ] Sample plugins load and function

**Integration Tests**:
- [ ] Plugin system integrates with existing ragged functionality
- [ ] Plugins can extend embedders, retrievers, processors, commands
- [ ] No conflicts between multiple plugins
- [ ] Plugin uninstall cleans up properly

**Performance Tests**:
- [ ] Plugin loading <100ms per plugin
- [ ] Plugin discovery <50ms
- [ ] No memory leaks when loading/unloading plugins

**Acceptance Criteria**:
1. ✅ `ragged plugin list` displays installed plugins
2. ✅ `ragged plugin install <name>` installs successfully
3. ✅ Sample plugin executes without errors
4. ✅ Plugin system doesn't break existing functionality
5. ✅ Documentation clearly explains plugin development

---

### v0.4.1 - VectorStore Abstraction

**Feature Tests**:
- [ ] VectorStore interface implemented
- [ ] ChromaDBStore refactored correctly
- [ ] Factory pattern creates correct backend
- [ ] All existing functionality preserved

**Contract Tests**:
- [ ] ChromaDBStore implements all VectorStore methods
- [ ] Interface contract tests pass
- [ ] Type signatures match interface

**Integration Tests**:
- [ ] Existing code uses abstraction correctly
- [ ] Backend switching works (if multiple backends)
- [ ] Migration from old code successful

**Performance Tests**:
- [ ] Abstraction overhead <5%
- [ ] No performance regressions in queries
- [ ] Memory usage unchanged

**Acceptance Criteria**:
1. ✅ All existing tests pass unchanged
2. ✅ VectorStore interface fully documented
3. ✅ ChromaDBStore passes contract tests
4. ✅ Performance maintained (<5% overhead)
5. ✅ Backend selection mechanism works

---

### v0.4.2 - Code Quality & Security Baseline

**Code Quality Tests**:
- [ ] All linters pass (ruff, mypy)
- [ ] Type hints complete (100% public APIs)
- [ ] Complexity reduced (<10 per function)
- [ ] No code duplication detected

**Performance Baseline Tests**:
- [ ] Benchmarks created for representative workloads
- [ ] Baseline recorded in `benchmarks/v0.4.2-baseline.json`
- [ ] CI regression detection configured
- [ ] Benchmarks reproducible

**Security Tests**:
- [ ] Bandit scan: zero high/critical findings
- [ ] Safety check: zero known CVEs
- [ ] Pip-audit: all dependencies secure
- [ ] Security documentation complete

**Acceptance Criteria**:
1. ✅ All quality gates pass
2. ✅ Performance baseline established and documented
3. ✅ Security scans clean
4. ✅ Memory system architecture documented (for audit)
5. ✅ Privacy threat model created
6. ✅ Security audit initiated

---

### v0.4.3 - Memory Foundation 🔒

**🔒 PRE-IMPLEMENTATION GATE**:
- [ ] Security audit PASSED
- [ ] Privacy framework approved
- [ ] Testing scenarios prepared

**Feature Tests**:
- [ ] Persona creation/switching/deletion works
- [ ] Interaction recording accurate
- [ ] Knowledge graph initialised correctly
- [ ] Memory CLI commands functional
- [ ] Privacy controls work (view, delete, export)

**Privacy Tests** (see [v0.4.5/testing-scenarios.md](v0.4.5/testing-scenarios.md)):
- [ ] **Network Isolation**: Zero external calls during memory ops
- [ ] **Data Locality**: All data in `~/.ragged/memory/`
- [ ] **Persona Isolation**: No cross-persona data leakage
- [ ] **Encryption**: Data encrypted at rest
- [ ] **User Controls**: View, delete, export all functional
- [ ] **PII Detection**: Automatic redaction working
- [ ] **Deletion Permanence**: Deleted data unrecoverable

**Integration Tests**:
- [ ] Memory integrates with query pipeline
- [ ] Persona switching preserves context
- [ ] Multiple personas don't interfere
- [ ] Long-running stability (1000+ interactions)

**Performance Tests**:
- [ ] Persona switching <100ms
- [ ] Interaction recording <50ms (async)
- [ ] Graph query <300ms
- [ ] Memory retrieval <200ms

**Acceptance Criteria**:
1. ✅ Security audit passed (no critical findings)
2. ✅ Persona system seamless
3. ✅ Memory tracking transparent
4. ✅ All interactions stored locally (verified)
5. ✅ Users can view/edit/delete memory (all controls functional)
6. ✅ Knowledge graph initialised
7. ✅ Privacy guaranteed (100% local, rigorously tested)
8. ✅ 85%+ test coverage (including privacy tests)
9. ✅ Performance targets met
10. ✅ CLI commands functional
11. ✅ Documentation complete (including privacy docs)
12. ✅ GDPR compliance verified (Articles 15, 17, 20)

---

### v0.4.4 - Stability & Performance

**Optimisation Tests**:
- [ ] Database queries optimised (indexes, prepared statements)
- [ ] Caching improves performance
- [ ] Memory leaks fixed (verified over 1000+ ops)

**Stability Tests**:
- [ ] Multi-persona concurrent access works
- [ ] Long-running stability (24-hour test passes)
- [ ] No crashes under load
- [ ] Graceful error handling

**Performance Tests**:
- [ ] Memory operations <100ms
- [ ] Graph queries <300ms
- [ ] No memory leaks over 1000 operations
- [ ] Concurrent access scales well

**Acceptance Criteria**:
1. ✅ All optimisations applied and tested
2. ✅ 24-hour stability test passes
3. ✅ Performance targets met consistently
4. ✅ No memory leaks detected
5. ✅ Concurrent access robust

---

### v0.4.5 - Behaviour Learning

**Feature Tests**:
- [ ] Topic extraction accurate (80%+ accuracy)
- [ ] Behaviour learning adapts over time
- [ ] Personalised ranking improves relevance (>15%)
- [ ] RAG pipeline integration seamless
- [ ] Interest profile analytics informative

**Integration Tests**:
- [ ] Topic extraction from real queries works
- [ ] Behaviour learning updates correctly
- [ ] Personalised ranking integrates with retrieval
- [ ] End-to-end personalisation pipeline functional

**Performance Tests**:
- [ ] Topic extraction <50ms
- [ ] Behaviour learning updates <100ms
- [ ] Personalised ranking <500ms
- [ ] End-to-end query <2s

**LEANN Decision Tests**:
- [ ] Storage usage measured accurately
- [ ] Decision criteria evaluated
- [ ] Decision documented in ADR-0018
- [ ] Outcome clear (proceed OR defer)

**Acceptance Criteria**:
1. ✅ Topic extraction 80%+ accurate
2. ✅ Personalisation improves relevance >15% (measured)
3. ✅ End-to-end performance <2s
4. ✅ LEANN decision made and documented
5. ✅ All integration tests pass

---

### v0.4.6 - Refactoring

**Refactoring Tests**:
- [ ] Code consolidation complete
- [ ] Complexity reduced (all functions <10)
- [ ] Architecture patterns enforced
- [ ] Dependencies optimised

**Regression Tests**:
- [ ] **ALL existing tests still pass**
- [ ] No functionality changed
- [ ] Performance maintained or improved
- [ ] API unchanged (internal refactor only)

**Maintainability Tests**:
- [ ] Code complexity metrics improved
- [ ] Duplicate code eliminated
- [ ] Module coupling reduced
- [ ] Test coverage maintained

**Acceptance Criteria**:
1. ✅ All existing tests pass without changes
2. ✅ Code complexity reduced
3. ✅ Maintainability metrics improved
4. ✅ No functionality regressions
5. ✅ Documentation updated for refactored areas

---

### v0.4.7 - Temporal Memory

**Feature Tests**:
- [ ] Temporal fact storage works
- [ ] Timeline query engine accurate
- [ ] Time-aware memory retrieval correct
- [ ] Date range filtering works
- [ ] Temporal relationships captured

**Integration Tests**:
- [ ] Temporal queries integrate with memory system
- [ ] Timeline visualisation works
- [ ] Historical context retrieval accurate
- [ ] Time-based analytics functional

**Performance Tests**:
- [ ] Temporal queries <500ms
- [ ] Timeline generation <1s
- [ ] Time-range filtering efficient
- [ ] No performance degradation with historical data

**Acceptance Criteria**:
1. ✅ Temporal fact storage working
2. ✅ Timeline queries accurate and fast
3. ✅ Time-aware retrieval improves context
4. ✅ Performance targets met
5. ✅ Documentation explains temporal features

---

### v0.4.8 - LEANN Backend ⚠️ CONDITIONAL

**⚠️ ONLY TEST IF v0.4.5 DECISION = "PROCEED"**

**Feature Tests**:
- [ ] LEANN backend implements VectorStore interface
- [ ] Migration tools work (ChromaDB → LEANN)
- [ ] Backend selection system functional
- [ ] Graph-aware queries leverage LEANN

**Contract Tests**:
- [ ] LEANN backend passes all VectorStore contract tests
- [ ] Interface compatibility verified
- [ ] Type signatures correct

**Migration Tests**:
- [ ] Migration tool preserves all data
- [ ] Embeddings transferred correctly
- [ ] No data loss during migration
- [ ] Rollback mechanism works

**Performance Tests**:
- [ ] LEANN performance ≥ChromaDB baseline
- [ ] Graph queries faster with LEANN
- [ ] Memory usage acceptable
- [ ] Scalability improved

**Acceptance Criteria** (if implemented):
1. ✅ LEANN backend fully functional
2. ✅ Migration from ChromaDB successful
3. ✅ Performance equal or better than ChromaDB
4. ✅ Backend selection works seamlessly
5. ✅ Documentation explains LEANN benefits and usage

**If Deferred**:
1. ✅ Deferral documented in ADR
2. ✅ Roadmap updated (moved to v0.5.x)
3. ✅ Proceed directly to v0.4.9

---

### v0.4.9 - Stabilisation & Release

**Integration Tests**:
- [ ] All v0.4.0-v0.4.8 features work together
- [ ] No conflicts between features
- [ ] End-to-end workflows complete successfully
- [ ] Privacy features work with all functionality

**Regression Tests**:
- [ ] Full regression test suite passes
- [ ] All v0.4.x tests passing
- [ ] Performance benchmarks validated
- [ ] No breaking changes introduced

**Documentation Tests**:
- [ ] All documentation accurate and complete
- [ ] Tutorials work as written
- [ ] API reference matches implementation
- [ ] Migration guides tested

**Release Checklist Tests**:
- [ ] CHANGELOG.md complete and accurate
- [ ] Version bumped correctly in all files
- [ ] All tests passing (unit, integration, e2e, privacy)
- [ ] Security audit recommendations implemented
- [ ] Performance validated against baseline

**Acceptance Criteria**:
1. ✅ All v0.4.0-v0.4.8 features merged and working
2. ✅ Zero regressions detected
3. ✅ Documentation complete and validated
4. ✅ Release artifacts prepared (PyPI package, GitHub release)
5. ✅ v0.4.x success criteria all met

---

## Privacy Testing Framework (v0.4.3+)

**Critical Requirement**: Privacy tests MUST pass for v0.4.3 and all subsequent releases

### Privacy Test Categories

#### 1. Network Isolation Tests

**Purpose**: Verify zero external network calls during memory operations

```python
def test_memory_no_network_calls():
    """Verify memory system makes zero network calls."""
    with NetworkMonitor() as monitor:
        # Create persona
        create_persona("researcher")

        # Record interactions
        record_interaction("test query", ["doc1", "doc2"])

        # Query memory
        get_memory_stats("researcher")

        # Export data
        export_memory("researcher", "output.json")

    assert monitor.external_calls == 0, \
        f"Memory operations made {monitor.external_calls} external calls"
```

**Pass Criteria**:
- ✅ Zero external network connections
- ✅ No DNS queries
- ✅ No HTTP/HTTPS requests
- ✅ Localhost connections only (if any)

---

#### 2. Data Locality Tests

**Purpose**: Verify all memory data stored in expected location

```python
def test_memory_data_locality():
    """Verify all memory data stored in ~/.ragged/memory/."""
    memory_dir = Path.home() / ".ragged" / "memory"

    # Create persona and record data
    create_persona("test_persona")
    record_interactions(count=10)

    # Find all files created
    all_files = list_all_ragged_files()

    # Verify all in memory directory
    for file in all_files:
        assert str(file).startswith(str(memory_dir)), \
            f"File outside memory dir: {file}"
```

**Pass Criteria**:
- ✅ All DB files in `~/.ragged/memory/`
- ✅ All YAML files in `~/.ragged/memory/`
- ✅ No temp files outside memory directory
- ✅ No data in system temp directories

---

#### 3. Persona Isolation Tests

**Purpose**: Verify personas completely isolated (no data leakage)

```python
def test_persona_isolation():
    """Verify personas don't see each other's data."""
    # Create two personas with distinct data
    persona_a = create_persona("researcher")
    persona_b = create_persona("developer")

    # Record distinct interactions
    with active_persona(persona_a):
        record_interaction("machine learning", ["ml_doc1"])

    with active_persona(persona_b):
        record_interaction("kubernetes", ["k8s_doc1"])

    # Verify isolation
    with active_persona(persona_a):
        topics = get_topics()
        assert "kubernetes" not in topics
        assert "machine learning" in topics

    with active_persona(persona_b):
        topics = get_topics()
        assert "machine learning" not in topics
        assert "kubernetes" in topics
```

**Pass Criteria**:
- ✅ No cross-persona data leakage
- ✅ Graph queries respect persona boundaries
- ✅ Interactions isolated per persona
- ✅ Topics isolated per persona

---

#### 4. Encryption Validation Tests

**Purpose**: Verify data encrypted at rest

```python
def test_encryption_at_rest():
    """Verify sensitive data encrypted at rest."""
    # Create persona with sensitive data
    create_persona("test_user")
    record_interaction("my secret query", ["doc1"])

    # Read raw database file
    db_path = Path.home() / ".ragged" / "memory" / "interactions" / "queries.db"
    with open(db_path, "rb") as f:
        raw_data = f.read()

    # Verify plaintext not in raw data
    assert b"my secret query" not in raw_data, \
        "Plaintext found in encrypted database"
```

**Pass Criteria**:
- ✅ SQLite databases encrypted
- ✅ Sensitive YAML fields encrypted
- ✅ No plaintext in raw files
- ✅ Encryption key stored securely (system keyring)

---

#### 5. User Control Tests

**Purpose**: Verify all GDPR rights functional (Articles 15, 17, 20)

```python
def test_user_right_to_access():
    """Test GDPR Article 15: Right to access."""
    persona = create_persona("test_user")
    interaction_id = record_interaction("test query", ["doc1"])

    # User can view their data
    data = show_interaction(interaction_id)
    assert data["query"] == "test query"
    assert data["retrieved_docs"] == ["doc1"]

def test_user_right_to_erasure():
    """Test GDPR Article 17: Right to erasure."""
    persona = create_persona("test_user")
    interaction_id = record_interaction("test query", ["doc1"])

    # User can delete their data
    delete_interaction(interaction_id)

    # Verify deletion is permanent
    assert not interaction_exists(interaction_id)
    assert not in_database(interaction_id)
    assert not in_graph(interaction_id)

def test_user_right_to_portability():
    """Test GDPR Article 20: Right to data portability."""
    persona = create_persona("test_user")
    record_interactions(count=10)

    # User can export their data
    export_path = export_memory("test_user", "export.json")

    # Verify export complete and valid
    with open(export_path) as f:
        data = json.load(f)

    assert len(data["interactions"]) == 10
    assert "persona" in data["metadata"]
    assert "topics" in data
```

**Pass Criteria**:
- ✅ View all data (Article 15) functional
- ✅ Delete data (Article 17) functional and permanent
- ✅ Export data (Article 20) complete and machine-readable
- ✅ Disable collection works
- ✅ PII detection functional

---

#### 6. PII Detection Tests

**Purpose**: Verify automatic PII detection and redaction

```python
def test_pii_detection():
    """Verify PII automatically detected and redacted."""
    # Enable PII redaction
    enable_pii_redaction()

    # Record interaction with PII
    record_interaction(
        "My email is john.doe@example.com and phone is 555-1234",
        ["doc1"]
    )

    # Verify PII redacted in stored data
    interaction = get_latest_interaction()
    assert "john.doe@example.com" not in interaction["query"]
    assert "[EMAIL]" in interaction["query"]
    assert "555-1234" not in interaction["query"]
    assert "[PHONE]" in interaction["query"]
```

**Pass Criteria**:
- ✅ Email addresses redacted
- ✅ Phone numbers redacted
- ✅ Credit card numbers redacted
- ✅ SSNs redacted
- ✅ IP addresses redacted

---

## Automated Quality Gate Script

**Location**: `scripts/quality_gates.sh`

```bash
#!/bin/bash
# Quality Gates for v0.4.x Releases
# Usage: ./scripts/quality_gates.sh

set -e  # Exit on any error

echo "🔍 Running Quality Gates for v0.4.x..."
echo ""

# Gate 1: Test Coverage
echo "Gate 1: Test Coverage (≥80%)"
pytest --cov=src --cov-report=term-missing --cov-fail-under=80
echo "✅ Gate 1 PASSED"
echo ""

# Gate 2: Type Safety
echo "Gate 2: Type Safety (mypy strict)"
mypy src/ --strict --show-error-codes
echo "✅ Gate 2 PASSED"
echo ""

# Gate 3: Code Quality
echo "Gate 3: Code Quality (ruff)"
ruff check src/ --select=ALL
echo "✅ Gate 3 PASSED"
echo ""

# Gate 4: Security Scan
echo "Gate 4: Security Scan (bandit, pip-audit)"
bandit -r src/ -ll
pip-audit
echo "✅ Gate 4 PASSED"
echo ""

# Gate 5: Performance Regression
echo "Gate 5: Performance Regression (benchmarks)"
python scripts/benchmark.py --compare-to benchmarks/baseline.json --max-regression 5
echo "✅ Gate 5 PASSED"
echo ""

# Gate 6: Privacy Tests (if v0.4.3+)
if [ -d "tests/privacy" ]; then
    echo "Gate 6: Privacy Validation"
    pytest tests/privacy/ -v
    echo "✅ Gate 6 PASSED"
    echo ""
fi

echo "🎉 ALL QUALITY GATES PASSED!"
echo "✅ Ready to tag release"
```

---

## Success Criteria Matrix

**Use this matrix to verify overall v0.4.x success**

| Criterion | Target | Measurement | Status |
|-----------|--------|-------------|--------|
| **Plugin Architecture** | Functional | `ragged plugin list` works, sample plugin loads | ⏳ |
| **VectorStore Abstraction** | Functional | ChromaDBStore passes contract tests | ⏳ |
| **Test Coverage** | ≥80% overall | pytest --cov | ⏳ |
| **Memory System** | Complete | Personas, learning, temporal all working | ⏳ |
| **Performance - Queries** | <2s | Benchmark average | ⏳ |
| **Performance - Memory Ops** | <100ms | Benchmark average | ⏳ |
| **LEANN Integration** | Decided | Implemented OR deferred (documented) | ⏳ |
| **Breaking Changes** | Zero | API compatibility maintained | ⏳ |
| **Local Operation** | 100% | Privacy tests: zero network calls | ⏳ |
| **Security Audit** | Passed | No critical findings | ⏳ |
| **GDPR Compliance** | Complete | Articles 15, 17, 20 functional | ⏳ |
| **Documentation** | Complete | Tutorials, guides, reference all accurate | ⏳ |
| **Production Ready** | Yes | All quality gates pass consistently | ⏳ |

---

## Related Documentation

- [Execution Playbook](./execution-playbook.md) - Implementation guide
- [Progress Tracker](./progress-tracker.md) - Status tracking
- [v0.4.3 Privacy Testing](./v0.4.5/testing-scenarios.md) - Detailed privacy test scenarios
- [v0.4.3 Security Audit](./v0.4.5/security-audit.md) - Security requirements

---

**Status**: Ready for use during v0.4.x implementation
