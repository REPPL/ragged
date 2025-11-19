# v0.2.8 Manual Tests

**Status:** ✅ COMPLETE
**Features:** CLI enhancements, output formatters, shell completion
**Date Created:** 2025-11-19

---

## Overview

Manual tests for ragged v0.2.8, focusing on 10 new CLI commands and advanced output formatting.

---

## Features Tested

- **CLI Commands** - 10 new commands (metadata, search, history, cache, export, completion, validate, feature-flags, monitor)
- **Output Formatters** - JSON, table, CSV, YAML, markdown output formats
- **Shell Completion** - bash, zsh, fish completion scripts
- **Configuration Validation** - Config file validation and diagnostics
- **Environment Info** - System diagnostics and debugging

---

## Test Files

- `smoke_test.py` - Quick sanity check
- `cli_commands_test.py` - All 10 new CLI commands
- `formatters_test.py` - JSON/table/CSV/YAML/markdown output
- `completion_test.py` - Shell completion validation

---

## Running Tests

```bash
pytest scripts/manual_tests/version/v0.2.8/
```

---

## pytest Markers

- `@pytest.mark.feature("cli")` - CLI command tests
- `@pytest.mark.feature("formatting")` - Output formatter tests
- `@pytest.mark.feature("completion")` - Shell completion tests
- `@pytest.mark.feature("validation")` - Config validation tests
- `@pytest.mark.feature("monitoring")` - Environment diagnostics tests

---

## CLI Commands Added

1. `ragged metadata` - View/update document metadata
2. `ragged search` - Advanced search with filters
3. `ragged history` - Query history management
4. `ragged cache` - Cache operations
5. `ragged export/import` - Backup/restore
6. `ragged completion` - Shell completion installation
7. `ragged validate` - Config validation
8. `ragged feature-flags` - Feature toggle management
9. `ragged monitor` - System monitoring
10. Enhanced `ragged env-info` - Environment diagnostics

---

## Related Documentation

- [v0.2.8 Roadmap](../../../docs/development/roadmap/version/v0.2/v0.2.8/)
- [v0.2 Implementation](../../../docs/development/implementation/version/v0.2/README.md)
- [CLI Commands Reference](../../../docs/reference/cli-commands.md)

---

**Maintained By:** ragged development team
