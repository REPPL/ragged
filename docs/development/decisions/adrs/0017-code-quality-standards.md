# ADR-0017: Code Quality Standards for v0.4.x

**Date:** 2025-11-22
**Status:** Accepted (enforced from v0.4.0 onwards)
**Deciders:** ragged development team
**Tags:** quality, testing, standards, ci-cd, v0.4

---

## Context

As ragged evolves from a prototype into a production-ready system through v0.4.x (14 releases, 272-330 hours), we need rigorous code quality standards to:

1. **Prevent regressions** - Catch bugs before they reach users
2. **Enable confident refactoring** - Rewrite code without breaking functionality
3. **Maintain velocity** - Clean code is faster to work with
4. **Support contributors** - Clear standards help community contributions
5. **Ensure privacy/security** - Critical for personal memory system

### Current State (v0.3.x)

**Good**:
- pytest testing framework in place
- Basic CI/CD with GitHub Actions
- Some linting with ruff
- Security scanning with bandit

**Needs Improvement**:
- Test coverage inconsistent (ranges 40-80%)
- No coverage enforcement
- Type hints incomplete
- No complexity limits
- Security scan not enforced
- Performance regression detection manual

### v0.4.x Requirements

Version 0.4.x introduces:
- Personal memory system (privacy-critical)
- Plugin architecture (security-critical)
- Multiple backends (compatibility-critical)
- 14 incremental releases (stability-critical)

**These features demand higher quality standards.**

---

## Decision

We will enforce **comprehensive quality gates** for every release in v0.4.x, with automated CI/CD enforcement and zero tolerance for regressions.

### Quality Standards

#### 1. Test Coverage

**Requirement**: ≥80% overall code coverage (MANDATORY)

**Rationale**: 80% is industry standard for production systems, provides high confidence without diminishing returns of higher targets.

**Module-Specific Targets** (aspirational, not blocking):
- Plugin system: 90%+
- VectorStore implementations: 90%+
- Memory system: 85%+
- Core features: 85%+
- CLI commands: 80%+

**Enforcement**:
```bash
pytest --cov=src --cov-report=term-missing --cov-fail-under=80
```

**CI/CD Integration**:
```yaml
# .github/workflows/quality-gates.yml
- name: Test with coverage
  run: |
    pytest --cov=src --cov-fail-under=80
    if [ $? -ne 0 ]; then
      echo "❌ Coverage below 80% - blocking release"
      exit 1
    fi
```

---

#### 2. Type Safety

**Requirement**: Zero mypy errors in strict mode (MANDATORY)

**Configuration** (`pyproject.toml`):
```toml
[tool.mypy]
python_version = "3.11"
strict = true
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
disallow_any_generics = true
check_untyped_defs = true
no_implicit_reexport = true
warn_redundant_casts = true
warn_unused_ignores = true
warn_no_return = true
```

**Enforcement**:
```bash
mypy src/ --strict
# Must exit with code 0
```

**Rationale**: Type hints prevent entire classes of bugs, enable better IDE support, and serve as documentation.

---

#### 3. Linting

**Requirement**: Zero errors, <10 warnings (MANDATORY)

**Tool**: ruff (fast, modern Python linter)

**Configuration** (`pyproject.toml`):
```toml
[tool.ruff]
target-version = "py311"
line-length = 100

select = [
    "E",   # pycodestyle errors
    "W",   # pycodestyle warnings
    "F",   # pyflakes
    "I",   # isort
    "N",   # pep8-naming
    "UP",  # pyupgrade
    "B",   # flake8-bugbear
    "C4",  # flake8-comprehensions
    "SIM", # flake8-simplify
]

ignore = [
    "E501",  # Line too long (handled by formatter)
]
```

**Enforcement**:
```bash
ruff check src/
# Errors: 0 (blocking)
# Warnings: <10 (blocking)
```

---

#### 4. Code Complexity

**Requirement**: Cyclomatic complexity <10 per function (ASPIRATIONAL)

**Tool**: radon (complexity analyser)

**Monitoring**:
```bash
radon cc src/ -a -nc
# Average complexity: Target <5
# Max complexity: Target <10
```

**Note**: Not blocking in CI/CD, but monitored and addressed in refactoring releases (v0.4.2, v0.4.6, v0.4.9).

**Rationale**: Complex functions are hard to test, understand, and maintain. Breaking them up improves quality.

---

#### 5. Security Scanning

**Requirement**: No high/critical vulnerabilities (MANDATORY)

**Tools**:
- **bandit** - Security linter for Python code
- **safety** - Dependency vulnerability checker
- **pip-audit** - CVE scanner for dependencies

**Enforcement**:
```bash
# Code security
bandit -r src/ -ll  # Only high/critical findings
# Must have zero findings

# Dependency vulnerabilities
safety check --json
pip-audit --require-hashes --desc

# Both must pass (zero high/critical)
```

**CI/CD Integration**: Runs on every PR and before every release.

---

#### 6. Performance Regression Detection

**Requirement**: No regression >5% from baseline (MANDATORY)

**Approach**:
1. **Baseline Establishment** (v0.4.2):
   - Run benchmarks on representative workloads
   - Record metrics in `benchmarks/v0.4.2-baseline.json`
   - Commit baselines to git

2. **Regression Detection** (every release):
   ```bash
   python scripts/benchmark.py --compare benchmarks/v0.4.2-baseline.json
   # Fails if any metric regressed >5%
   ```

3. **Benchmark Suite**:
   - Document ingestion (PDF, HTML, TXT)
   - Query performance (1K, 10K, 100K docs)
   - Memory operations (persona load, interaction insert, graph query)
   - CLI responsiveness

**Rationale**: Prevent performance degradation as features are added.

---

#### 7. Code Formatting

**Requirement**: Consistent formatting (MANDATORY)

**Tool**: black (opinionated formatter)

**Configuration**:
```toml
[tool.black]
line-length = 100
target-version = ['py311']
```

**Enforcement**:
```bash
black --check src/ tests/
# Must pass (no changes needed)
```

**Rationale**: Eliminates formatting debates, ensures consistency, reduces diff noise.

---

### CI/CD Quality Pipeline

**Every PR**:
1. Run all tests with coverage (≥80%)
2. Type check (mypy strict, zero errors)
3. Lint (ruff, zero errors, <10 warnings)
4. Security scan (bandit, safety, pip-audit)
5. Format check (black)
6. Build documentation (Sphinx, zero warnings)

**Every Release**:
1. All PR checks +
2. Performance benchmarks (no regression >5%)
3. Integration tests (cross-platform)
4. Security audit validation (v0.4.4-onwards)
5. Documentation completeness check

**GitHub Actions Workflow**:
```yaml
name: Quality Gates

on: [push, pull_request]

jobs:
  quality:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install -e ".[dev]"

      - name: Test Coverage
        run: pytest --cov=src --cov-fail-under=80

      - name: Type Check
        run: mypy src/ --strict

      - name: Lint
        run: |
          ruff check src/
          if [ $? -eq 1 ]; then
            echo "❌ Linting failed"
            exit 1
          fi

      - name: Security Scan
        run: |
          bandit -r src/ -ll
          safety check

      - name: Format Check
        run: black --check src/ tests/

      - name: Build Docs
        run: sphinx-build -W docs/ docs/_build/
```

---

## Consequences

### Positive

1. **High Confidence**: 80%+ coverage catches most regressions
2. **Type Safety**: mypy prevents type-related bugs
3. **Consistent Code**: Formatting and linting ensure readability
4. **Security**: Automated scans catch vulnerabilities early
5. **Performance**: Benchmarks prevent silent degradation
6. **Reviewability**: Clean code easier to review
7. **Contributor-Friendly**: Clear standards help contributions

### Negative

1. **Initial Overhead**: Setting up standards takes time
2. **Friction**: Some legitimate PRs may fail gates initially
3. **False Positives**: Security scans occasionally flag non-issues
4. **Maintenance**: Baseline benchmarks need periodic updates

### Mitigations

**Initial Overhead**:
- One-time investment in v0.4.0 (included in 25-30h estimate)
- Templates and examples for contributors
- Comprehensive CI/CD documentation

**Friction**:
- Clear error messages in CI/CD
- Pre-commit hooks catch issues locally
- Documentation on resolving common failures

**False Positives**:
- Allowlist for known false positives
- Regular review of suppressed warnings
- Security team approval for exceptions

**Maintenance**:
- Update baselines during performance-focused releases (v0.4.2, v0.4.12)
- Quarterly dependency updates
- Annual standards review

---

## Exceptions & Waivers

**When quality gates can be bypassed** (requires approval):

1. **Hotfixes** - Critical security/bug fixes
   - Requires: 2 maintainer approvals
   - Must create follow-up issue to restore coverage

2. **Dependencies** - Third-party security issues
   - Requires: Security audit confirming false positive
   - Must document in `SECURITY.md`

3. **Platform-Specific** - Features not testable in CI
   - Requires: Manual testing documentation
   - Must add platform-specific test suite

**Process**:
```bash
git commit -m "fix: critical security patch" --allow-empty
# Add override label: "quality-gate-override"
# Requires 2 maintainer approvals
```

---

## Tools Configuration

**Install Development Tools**:
```bash
pip install -e ".[dev]"

# Included in [dev]:
- pytest>=7.4
- pytest-cov>=4.1
- mypy>=1.7
- ruff>=0.1
- black>=23.11
- bandit>=1.7
- safety>=2.3
- radon>=6.0
```

**Pre-Commit Hooks** (`.pre-commit-config.yaml`):
```yaml
repos:
  - repo: https://github.com/psf/black
    rev: 23.11.0
    hooks:
      - id: black

  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.1.6
    hooks:
      - id: ruff

  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.7.0
    hooks:
      - id: mypy
        additional_dependencies: [types-all]

  - repo: https://github.com/PyCQA/bandit
    rev: 1.7.5
    hooks:
      - id: bandit
        args: ['-ll', '-r', 'src/']
```

**Install Hooks**:
```bash
pre-commit install
# Now runs on every commit
```

---

## Monitoring & Reporting

**Quality Metrics Dashboard** (optional, v0.5.x):
- Test coverage trends
- Type coverage percentage
- Complexity distribution
- Security scan history
- Performance benchmark trends

**Release Quality Report** (every release):
```bash
ragged dev quality-report --release v0.4.5

# Outputs:
# ✅ Coverage: 87.3% (+2.1% from v0.4.4)
# ✅ Type Errors: 0
# ✅ Lint Errors: 0, Warnings: 3 (-2 from v0.4.4)
# ✅ Security Issues: 0 high, 0 critical
# ✅ Avg Complexity: 4.2 (-0.3 from v0.4.4)
# ✅ Performance: No regressions
```

---

## Rollout Plan

### v0.4.0 (Foundation)
- Establish all quality gates in CI/CD
- Achieve 80%+ coverage baseline
- Zero mypy strict mode errors
- Documentation for contributors

### v0.4.2 (Quality Baseline)
- Establish performance baselines
- Complexity analysis and reduction
- Security audit preparation
- Enhanced CI/CD reporting

### v0.4.6, v0.4.9 (Refactoring Releases)
- Complexity reduction sprints
- Improve test coverage in weak areas
- Update baselines
- Code consolidation

### v0.4.13 (Production Release)
- Final quality validation
- Comprehensive quality report
- Production-ready standards documentation
- Handoff to v0.5.x

---

## Related Documentation

**ADRs**:
- [ADR-0011: Privacy-Safe Logging](./0011-privacy-safe-logging.md) - Related quality standard
- [ADR-0016: Memory System Architecture](./0016-memory-system-architecture.md) - Requires these standards

**Roadmap**:
- [v0.4.0 Roadmap](../../roadmap/version/v0.4/v0.4.0.md) - Quality gates establishment
- [v0.4.2 Roadmap](../../roadmap/version/v0.4/v0.4.2.md) - Performance baselines and security
- [v0.4 Testing Guide](../../roadmap/version/v0.4/testing-guide.md) - Comprehensive testing standards

**Guides**:
- [Contributing Guide](../../../CONTRIBUTING.md) - How to meet quality standards
- [Testing Guide](../../process/testing-guide.md) - Writing effective tests

---

## Decision Rationale

These standards were chosen because they:

1. **Balance Rigour and Pragmatism**: 80% coverage is achievable without diminishing returns
2. **Automate Enforcement**: CI/CD catches issues before human review
3. **Prevent Regressions**: High coverage enables confident refactoring
4. **Enable Velocity**: Clean code is faster to work with long-term
5. **Support Community**: Clear standards help contributors succeed
6. **Ensure Trust**: Privacy/security-critical systems demand high quality

The tiered approach (80% mandatory, higher targets aspirational) allows flexibility while maintaining minimum standards.

**Foundation-first philosophy**: Establish quality infrastructure in v0.4.0 before building complex features, ensuring quality is baked in rather than bolted on.

---

**Status**: Accepted (enforced from v0.4.0 onwards)
