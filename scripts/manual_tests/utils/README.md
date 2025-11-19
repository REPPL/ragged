# Test Utilities

**Purpose:** Shared utilities for manual test execution, validation, and reporting.

**Pattern:** Reusable helper functions to reduce test duplication.

---

## Utility Modules

### 1. `helpers.py` - Test Helper Functions

**Purpose:** Common setup, teardown, and data generation functions.

**Functions:**
- `create_test_ragged_instance()` - Create fresh ragged instance with temp DB
- `generate_sample_documents()` - Generate test documents (PDF, MD, HTML, TXT)
- `add_documents_to_ragged()` - Add documents to test instance
- `execute_test_query()` - Execute query and return results
- `cleanup_test_instance()` - Clean up test data and temp files
- `wait_for_service()` - Wait for Ollama/ChromaDB availability
- `create_test_config()` - Generate test configuration

**Example Usage:**
```python
from scripts.manual_tests.utils.helpers import (
    create_test_ragged_instance,
    generate_sample_documents,
    cleanup_test_instance
)

def test_document_ingestion():
    # Setup
    ragged = create_test_ragged_instance()
    docs = generate_sample_documents(count=10)

    # Test
    ragged.add_documents(docs)

    # Cleanup
    cleanup_test_instance(ragged)
```

### 2. `validators.py` - Result Validation Functions

**Purpose:** Validate test results and assertions.

**Functions:**
- `validate_document_ingestion()` - Check document was ingested correctly
- `validate_query_results()` - Validate query response structure and content
- `validate_metadata()` - Check metadata correctness
- `validate_performance()` - Check performance against baseline
- `validate_error_message()` - Validate error message format and content
- `validate_api_response()` - Validate API response structure
- `compare_results()` - Compare actual vs expected results

**Example Usage:**
```python
from scripts.manual_tests.utils.validators import (
    validate_query_results,
    validate_performance
)

def test_query_quality():
    results = execute_query("test query")

    # Validate results
    is_valid, errors = validate_query_results(
        results,
        min_sources=3,
        required_fields=["answer", "sources", "metadata"]
    )

    assert is_valid, f"Validation errors: {errors}"

    # Validate performance
    assert validate_performance(
        metric="query_latency_ms",
        value=results["latency_ms"],
        baseline=200,
        tolerance=0.2  # 20% tolerance
    )
```

### 3. `reporters.py` - Test Report Generation

**Purpose:** Generate HTML and JSON test reports.

**Functions:**
- `generate_html_report()` - Create HTML test report
- `generate_json_report()` - Create JSON test report
- `generate_performance_report()` - Performance comparison report
- `generate_summary_report()` - Test execution summary
- `format_test_results()` - Format results for display
- `create_comparison_table()` - Compare multiple test runs

**Example Usage:**
```python
from scripts.manual_tests.utils.reporters import (
    generate_html_report,
    generate_summary_report
)

def generate_test_reports(test_results):
    # Generate HTML report
    generate_html_report(
        results=test_results,
        output_path="reports/test_run_2025-11-19.html",
        title="v0.2.9 Manual Test Results"
    )

    # Generate summary
    summary = generate_summary_report(test_results)
    print(summary)
```

---

## Shared Fixtures (`conftest.py`)

**Purpose:** pytest fixtures available to all manual tests.

**Fixtures:**
- `ragged_instance` - Fresh ragged instance for each test
- `sample_documents` - Pre-generated sample documents
- `test_config` - Test configuration
- `ollama_available` - Skip if Ollama unavailable
- `chromadb_available` - Skip if ChromaDB unavailable
- `performance_baseline` - Load baseline metrics
- `temp_directory` - Temporary directory for test files

**Example Usage:**
```python
def test_with_fixtures(ragged_instance, sample_documents):
    """Test using shared fixtures"""
    ragged_instance.add_documents(sample_documents)
    results = ragged_instance.query("test query")
    assert len(results["sources"]) > 0
```

---

## Data Generators

### Document Generators

```python
# Generate sample PDF
from utils.helpers import generate_pdf_document
pdf = generate_pdf_document(
    title="Test Document",
    content="Lorem ipsum...",
    pages=5
)

# Generate sample Markdown
from utils.helpers import generate_markdown_document
md = generate_markdown_document(
    title="Test Document",
    sections=["Introduction", "Methods", "Results"]
)

# Generate folder structure
from utils.helpers import generate_document_folder
folder = generate_document_folder(
    num_files=20,
    formats=["pdf", "md", "html", "txt"],
    nested=True
)
```

### Query Generators

```python
# Generate test queries
from utils.helpers import generate_test_queries
queries = generate_test_queries(
    categories=["simple", "complex", "filtered"],
    count_per_category=10
)
```

---

## Performance Utilities

### Timing Decorators

```python
from utils.helpers import measure_time

@measure_time
def test_slow_operation():
    # This function's execution time will be measured
    pass
```

### Memory Profiling

```python
from utils.helpers import memory_profile

with memory_profile("ingestion"):
    ragged.add_documents(docs)
# Prints: "ingestion: 245.6 MB peak memory"
```

### Benchmarking

```python
from utils.helpers import benchmark

results = benchmark(
    func=lambda: ragged.query("test"),
    iterations=100,
    warmup=10
)
# Returns: {"mean": 0.12, "p50": 0.11, "p95": 0.15, "p99": 0.18}
```

---

## Service Utilities

### Wait for Services

```python
from utils.helpers import wait_for_service

# Wait for Ollama to be available
wait_for_service("ollama", timeout=30)

# Wait for ChromaDB
wait_for_service("chromadb", timeout=30)
```

### Health Checks

```python
from utils.helpers import check_service_health

health = check_service_health("ollama")
assert health["status"] == "healthy"
```

---

## File Utilities

### Temporary Files

```python
from utils.helpers import create_temp_file, cleanup_temp_files

# Create temporary file
temp_pdf = create_temp_file(content=pdf_bytes, suffix=".pdf")

# Use file
ragged.add(temp_pdf)

# Cleanup
cleanup_temp_files()
```

### Test Data Management

```python
from utils.helpers import load_test_data, save_test_data

# Load test data
test_docs = load_test_data("sample_documents.json")

# Save results
save_test_data(results, "test_results.json")
```

---

## Validation Helpers

### Schema Validation

```python
from utils.validators import validate_schema

response = api.query("test")

# Validate against expected schema
is_valid, errors = validate_schema(
    data=response,
    schema={
        "answer": str,
        "sources": list,
        "metadata": dict
    }
)
```

### Regression Detection

```python
from utils.validators import detect_regression

current_performance = {"latency_ms": 250}
baseline_performance = {"latency_ms": 200}

regression = detect_regression(
    current=current_performance,
    baseline=baseline_performance,
    tolerance=0.1  # 10% tolerance
)

if regression:
    print(f"Performance regression detected: {regression}")
```

---

## Best Practices

### Using Utilities

1. ✅ **Import from utils/** - Don't duplicate logic
2. ✅ **Use fixtures** - Reduce setup/teardown code
3. ✅ **Validate consistently** - Use validators for all assertions
4. ✅ **Generate reports** - Document test results
5. ✅ **Profile performance** - Use timing and memory utilities

### Adding New Utilities

1. ✅ **Check for duplication** - Don't reinvent existing utilities
2. ✅ **Write docstrings** - Document parameters and return values
3. ✅ **Add type hints** - Use Python type annotations
4. ✅ **Write unit tests** - Test utilities themselves
5. ✅ **Update this README** - Document new utilities

---

## Maintenance

### When to Update

- ✅ **New test patterns** emerge
- ✅ **Common code** appears in multiple tests
- ✅ **Validation logic** changes
- ✅ **Reporting needs** expand

### How to Update

1. Identify repeated code in tests
2. Extract to utility function
3. Add to appropriate module (helpers/validators/reporters)
4. Update tests to use utility
5. Document in this README
6. Write tests for new utility

---

## Related Documentation

- [conftest.py](../conftest.py) - Shared pytest fixtures
- [Test Data](../test_data/README.md) - Sample test data
- [Version Tests](../version/README.md) - Using utilities in version tests
- [Performance Tests](../performance/README.md) - Performance utilities

---

**Maintained By:** ragged development team
