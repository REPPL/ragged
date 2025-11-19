# Manual Testing Infrastructure

**Purpose:** Comprehensive manual testing framework for ragged, covering version-specific features, cross-version regression testing, end-to-end workflows, and performance validation.

**Location:** `scripts/manual_tests/` (executable tests) + `docs/development/process/testing/manual/` (test documentation)

---

## Quick Start

### Run Tests

```bash
# Run all smoke tests
pytest scripts/manual_tests/ -m smoke

# Run tests for specific version
pytest scripts/manual_tests/version/v0.2.9/

# Run tests for specific feature across all versions
pytest scripts/manual_tests/ -m 'feature("cli")'

# Run regression tests (critical paths)
pytest scripts/manual_tests/regression/

# Run performance benchmarks
pytest scripts/manual_tests/performance/benchmarks/

# Run everything except performance tests
pytest scripts/manual_tests/ -m 'not performance'

# Use the test runner for filtered execution
python scripts/manual_tests/run_tests.py --version v0.2.9 --type smoke
```

### pytest Markers

- `@pytest.mark.smoke` - Quick sanity checks (5-10 min)
- `@pytest.mark.feature("name")` - Tests for specific feature (cli, formatting, ingestion, etc.)
- `@pytest.mark.version("v")` - Tests for specific version
- `@pytest.mark.regression` - Cross-version critical paths
- `@pytest.mark.workflow` - End-to-end user workflows
- `@pytest.mark.performance` - Performance benchmarks
- `@pytest.mark.interactive` - Manual checklists (not automated)

---

## Directory Structure

```
scripts/manual_tests/
├── version/              # Version-specific tests (new features per version)
├── regression/           # Cross-version critical path tests
├── workflows/            # End-to-end user workflow tests
├── performance/          # Performance benchmarks + baselines
├── interactive/          # Manual checklists (UI, error scenarios)
├── test_data/            # Shared test data (documents, fixtures)
├── templates/            # Templates for creating new version tests
├── utils/                # Test utilities (helpers, validators, reporters)
└── reports/              # Generated test execution reports
```

---

## Test Types

### 1. Version-Specific Tests (`version/`)

Tests for **new features** introduced in each version.

**Structure:**
```
version/v0.2.9/
├── README.md                          # What's tested in v0.2.9
├── smoke_test.py                      # Quick validation (5-10 min)
├── performance_optimisation_test.py   # Feature-specific tests
└── test_data/                         # Version-specific test data
```

**Versions covered:**
- v0.2.4 - Base version
- v0.2.5 - Quality improvements
- v0.2.7 - CLI refactoring, folder ingestion
- v0.2.8 - CLI enhancements, output formatters
- v0.2.9 - Performance optimisation, cold start
- v0.2.10 - Security foundation (placeholder)
- v0.2.11 - Privacy infrastructure (placeholder)

**See:** [Version Test Directory](./version/README.md)

### 2. Regression Tests (`regression/`)

Tests for **critical paths** that must work across all versions.

**Coverage:**
- Document ingestion (PDF, MD, HTML, TXT)
- Retrieval quality (vector + BM25 + hybrid)
- Core CLI commands (add, query, list, clear)
- Web API endpoints (/upload, /query, /health)

**See:** [Regression Test Directory](./regression/README.md)

### 3. Workflow Tests (`workflows/`)

Tests for **end-to-end user scenarios** from start to finish.

**Coverage:**
- New user onboarding (first-time setup → add docs → query)
- Document lifecycle (add → metadata → search → delete)
- Query workflows (simple → filters → history replay)
- Backup/restore (export → clear → import → verify)

**See:** [Workflow Test Directory](./workflows/README.md)

### 4. Performance Tests (`performance/`)

**Benchmarks** for measuring system performance and detecting regressions.

**Coverage:**
- Ingestion speed (time to process 100 documents)
- Query latency (p50/p95/p99)
- Cold start time (first query latency)
- Memory usage profiling

**Baselines:** Historical performance data for v0.2.4-v0.2.9

**See:** [Performance Test Directory](./performance/README.md)

### 5. Interactive Checklists (`interactive/`)

**Manual validation checklists** for UI, error scenarios, and cross-platform testing.

**Coverage:**
- Gradio UI validation (step-by-step)
- CLI feature verification
- Error handling scenarios
- Cross-platform testing (macOS/Linux/Windows)

**See:** [Interactive Test Directory](./interactive/README.md)

---

## Creating Tests for New Versions

### Automated Creation

```bash
# Create tests for new version v0.2.12
./scripts/manual_tests/templates/create_version_tests.sh v0.2.12 "feature1,feature2,feature3"
```

This creates:
- `scripts/manual_tests/version/v0.2.12/` (from template)
- `docs/development/process/testing/manual/v0.2/v0.2.12-manual-tests.md`
- Updates `run_tests.py` with new version

### Manual Creation

1. Copy template: `cp -r templates/version_test_template/ version/v0.2.X/`
2. Rename files: `mv smoke_test.template.py smoke_test.py`
3. Replace placeholders: `{VERSION}`, `{FEATURES}`, `{DATE}`
4. Add feature-specific tests
5. Update README.md
6. Create documentation in `docs/development/process/testing/manual/v0.2/`

**See:** [Template Directory](./templates/README.md)

---

## Integration with Documentation

### Roadmap Integration

Each version roadmap links to manual test plan:
```markdown
## Testing
**Manual Test Plan:** [v0.2.9 Manual Tests](../../../process/testing/manual/v0.2/v0.2.9-manual-tests.md)
**Executable Tests:** `scripts/manual_tests/version/v0.2.9/`
```

### Implementation Integration

Each version implementation links to test results:
```markdown
## Manual Test Results
**Status:** ✅ COMPLETE
**Test Plan:** [v0.2.9 Manual Tests](../../process/testing/manual/v0.2/v0.2.9-manual-tests.md)
**Reports:** `scripts/manual_tests/reports/2025-11-19_v0.2.9_*.html`
```

### Documentation Location

**Test Plans:** `docs/development/process/testing/manual/v0.2/vX.X-manual-tests.md`
**Executable Tests:** `scripts/manual_tests/version/vX.X/`

---

## Test Execution Reports

Reports are generated in `reports/` directory:

```
reports/
├── 2025-11-19_smoke_v0.2.9.html
├── 2025-11-19_regression_all.html
└── 2025-11-19_performance_comparison.html
```

### Generate Reports

```bash
# Run tests and generate HTML report
pytest scripts/manual_tests/ --html=scripts/manual_tests/reports/$(date +%Y-%m-%d)_test_report.html

# Generate performance comparison report
python scripts/manual_tests/performance/compare_versions.py --output reports/
```

---

## Maintenance

### Quarterly Tasks

- Review and update test data (ensure relevance)
- Check for test rot (outdated scenarios)
- Update performance baselines
- Verify all documentation links

### When Releasing New Version

1. Create version test directory from template
2. Add version-specific smoke test
3. Update regression tests if critical paths changed
4. Add version-specific test scenarios for new features
5. Update performance baseline
6. Run full test suite before release
7. Document test results in implementation docs

---

## Related Documentation

- [Manual Testing Documentation](../../docs/development/process/testing/manual/README.md) - Test plans and scenarios
- [Testing Strategy](../../docs/development/process/testing/README.md) - Overall testing approach
- [Roadmap](../../docs/development/roadmap/README.md) - Feature planning and versioning
- [Implementation](../../docs/development/implementation/README.md) - Completed version documentation

---

**Maintained By:** ragged development team
