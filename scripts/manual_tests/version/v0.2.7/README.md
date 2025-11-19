# v0.2.7 Manual Tests

**Status:** ✅ COMPLETE
**Features:** CLI refactoring, folder ingestion, enhanced HTML processing
**Date Created:** 2025-11-19

---

## Overview

Manual tests for ragged v0.2.7, focusing on CLI architecture improvements and folder ingestion capability.

---

## Features Tested

- **Modular CLI** - 14 command modules with improved testability
- **Folder Ingestion** - Recursive directory scanning with duplicate detection
- **HTML Processing** - Enhanced parsing with Trafilatura + BeautifulSoup
- **CLI Refactoring** - Separation of concerns, better error handling

---

## Test Files

- `smoke_test.py` - Quick sanity check
- `folder_ingestion_test.py` - Recursive scanning, duplicate detection tests
- `html_processing_test.py` - HTML parsing validation
- `modular_cli_test.py` - CLI architecture tests

---

## Running Tests

```bash
pytest scripts/manual_tests/version/v0.2.7/
```

---

## pytest Markers

- `@pytest.mark.feature("folder_ingestion")` - Folder scanning tests
- `@pytest.mark.feature("html_processing")` - HTML parsing tests
- `@pytest.mark.feature("modular_cli")` - CLI architecture tests

---

## Related Documentation

- [v0.2.7 Roadmap](../../../docs/development/roadmap/version/v0.2/v0.2.7/)
- [v0.2 Implementation](../../../docs/development/implementation/version/v0.2/README.md)

---

**Maintained By:** ragged development team
