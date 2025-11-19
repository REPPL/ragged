# Version-Specific Tests

**Purpose:** Test **new features** introduced in each version of ragged.

**Pattern:** Each version has its own directory containing smoke tests and feature-specific tests.

---

## Directory Structure

```
version/
├── v0.2.4/
│   ├── README.md
│   └── smoke_test.py
├── v0.2.5/
│   ├── README.md
│   ├── smoke_test.py
│   └── quality_improvements_test.py
├── v0.2.7/
│   ├── README.md
│   ├── smoke_test.py
│   ├── folder_ingestion_test.py
│   └── test_data/
├── v0.2.8/
│   ├── README.md
│   ├── smoke_test.py
│   ├── cli_commands_test.py
│   ├── formatters_test.py
│   └── completion_test.py
├── v0.2.9/
│   ├── README.md
│   ├── smoke_test.py
│   ├── performance_optimisation_test.py
│   └── cold_start_test.py
├── v0.2.10/      # Placeholder for security foundation
│   └── README.md
└── v0.2.11/      # Placeholder for privacy infrastructure
    └── README.md
```

---

## What Belongs Here

✅ **Smoke tests** - Quick validation that version is functional (5-10 min)
✅ **Feature-specific tests** - Tests for NEW features in this version
✅ **Migration tests** - Upgrade paths from previous version
✅ **Version-specific test data** - Sample data needed for this version's features

❌ **Cross-version tests** - Use `regression/` directory
❌ **User workflows** - Use `workflows/` directory
❌ **Performance benchmarks** - Use `performance/` directory

---

## pytest Markers

All version-specific tests should use these markers:

```python
import pytest

@pytest.mark.smoke
@pytest.mark.version("v0.2.9")
def test_basic_functionality():
    """Quick smoke test for v0.2.9"""
    pass

@pytest.mark.feature("performance")
@pytest.mark.version("v0.2.9")
def test_cold_start_optimisation():
    """Test cold start optimisation feature"""
    pass
```

---

## Running Tests

### Run all tests for specific version

```bash
pytest scripts/manual_tests/version/v0.2.9/
```

### Run smoke tests for all versions

```bash
pytest scripts/manual_tests/version/ -m smoke
```

### Run specific feature across all versions

```bash
pytest scripts/manual_tests/version/ -m 'feature("cli")'
```

### Run tests for multiple versions

```bash
pytest scripts/manual_tests/version/ -m 'version("v0.2.8") or version("v0.2.9")'
```

---

## Feature Tags by Version

### v0.2.9 (Performance & Stability)
- `@pytest.mark.feature("performance")` - Batch tuning, cold start optimisation
- `@pytest.mark.feature("chunking")` - Token counter, recursive splitter improvements
- `@pytest.mark.feature("test_coverage")` - 70%+ coverage validation

### v0.2.8 (CLI Enhancements)
- `@pytest.mark.feature("cli")` - 10 new CLI commands
- `@pytest.mark.feature("formatting")` - JSON/table/CSV/YAML output formatters
- `@pytest.mark.feature("completion")` - Shell completion (bash/zsh/fish)
- `@pytest.mark.feature("validation")` - Configuration validation
- `@pytest.mark.feature("monitoring")` - Environment diagnostics

### v0.2.7 (CLI Refactoring)
- `@pytest.mark.feature("folder_ingestion")` - Recursive folder scanning
- `@pytest.mark.feature("html_processing")` - Trafilatura + BeautifulSoup
- `@pytest.mark.feature("modular_cli")` - 14 command modules

### v0.2.5 (Quality Improvements)
- `@pytest.mark.feature("settings_refactor")` - No global state mutation
- `@pytest.mark.feature("error_handling")` - Improved exception handling
- `@pytest.mark.feature("type_safety")` - mypy --strict compliance

### v0.2.4 (Base Version)
- Basic functionality validation

---

## Creating Tests for New Version

### 1. Use Template

```bash
./scripts/manual_tests/templates/create_version_tests.sh v0.2.12 "feature1,feature2"
```

### 2. Implement Tests

- Add smoke_test.py (required)
- Add feature-specific tests
- Add test data if needed
- Update README.md with feature tags

### 3. Document

Create test plan in `docs/development/process/testing/manual/v0.2/v0.2.12-manual-tests.md`

---

## Version Status

| Version | Status | Key Features | Tests |
|---------|--------|--------------|-------|
| v0.2.4 | ✅ COMPLETE | Base functionality | smoke_test.py |
| v0.2.5 | ✅ COMPLETE | Quality improvements | smoke_test.py, quality_improvements_test.py |
| v0.2.7 | ✅ COMPLETE | CLI refactoring, folder ingestion | smoke_test.py, folder_ingestion_test.py, html_processing_test.py |
| v0.2.8 | ✅ COMPLETE | CLI enhancements, formatters | smoke_test.py, cli_commands_test.py, formatters_test.py, completion_test.py |
| v0.2.9 | ✅ COMPLETE | Performance optimisation | smoke_test.py, performance_optimisation_test.py, cold_start_test.py |
| v0.2.10 | 📅 PLANNED | Security foundation | README.md (placeholder) |
| v0.2.11 | 📅 PLANNED | Privacy infrastructure | README.md (placeholder) |

---

## Related Documentation

- [Version Test Plans](../../../docs/development/process/testing/manual/v0.2/) - Detailed test scenarios
- [Roadmap](../../../docs/development/roadmap/version/v0.2/) - Feature planning
- [Implementation](../../../docs/development/implementation/version/v0.2/) - What was built
- [Regression Tests](../regression/README.md) - Cross-version testing
- [Templates](../templates/README.md) - Creating new version tests

---

**Maintained By:** ragged development team
