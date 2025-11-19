# CLI Enhancements (v0.2.7)

This document details the 11 CLI enhancements planned for v0.2.7, transforming ragged into a comprehensive, production-ready tool.

**Total Estimated Time**: 48-62 hours
**Priority Distribution**: 6 high, 5 medium

**Related Documentation:** [CLI Enhancements Catalogue](../../../../planning/interfaces/cli/enhancements.md)

---

## CLI-001: Advanced Search & Filtering

**Priority**: High
**Estimated Time**: 3-4 hours
**Impact**: High - Essential for finding documents in large knowledge bases

### Description
Enhanced search capabilities for finding documents using multiple filter criteria (metadata, content type, date ranges, similarity thresholds).

### Command Syntax
```bash
# Search by metadata
ragged search --tag python --author "John Doe" --after 2025-01-01

# Search by content type
ragged search --type pdf --min-size 1MB --max-size 10MB

# Search by embedding similarity
ragged search "machine learning" --similarity 0.8

# Combined filters
ragged search --tag research --type pdf --after 2025-01-01 \
  --sort-by date --limit 10
```

### Implementation
- **Files to Create**:
  - `ragged/cli/commands/search.py` - Enhanced search command
  - `tests/cli/test_search.py` - Comprehensive test suite

- **Files to Modify**:
  - `ragged/core/storage.py` - Add filter query methods
  - `ragged/core/models.py` - Add filter data models

- **Dependencies**: ChromaDB metadata filtering, Click argument parsing, date utilities

### Testing Requirements
- Unit tests for each filter type
- Integration tests for combined filters
- Edge cases: empty results, invalid dates, missing metadata
- Performance tests with large knowledge bases

### Acceptance Criteria
- ✅ All filter types work correctly
- ✅ Filters can be combined
- ✅ Results sorted and limited appropriately
- ✅ Clear error messages for invalid filters

---

## CLI-002: Metadata Management

**Priority**: High
**Estimated Time**: 4-5 hours
**Impact**: High - Manage metadata without re-ingesting documents

### Description
Commands for viewing, updating, and managing document metadata without re-ingesting documents. Supports individual and batch operations.

### Command Syntax
```bash
# View metadata
ragged metadata show doc_id_123

# Update metadata
ragged metadata update doc_id_123 \
  --tag "machine-learning" \
  --author "Jane Smith" \
  --custom-field value

# Batch update
ragged metadata update --tag old_tag --replace-tag new_tag

# Delete metadata fields
ragged metadata delete doc_id_123 --field custom_field
```

### Implementation
- **Files to Create**:
  - `ragged/cli/commands/metadata.py` - New command group
  - `tests/cli/test_metadata.py` - Test suite

- **Files to Modify**:
  - `ragged/core/storage.py` - Metadata CRUD operations
  - `ragged/core/models.py` - Metadata validation models

- **Dependencies**: ChromaDB metadata API, Pydantic validation, Click command groups

### Testing Requirements
- Unit tests for metadata operations
- Integration tests for batch updates
- Validation tests for metadata schemas
- Rollback tests for failed updates

### Acceptance Criteria
- ✅ Can view and update individual metadata
- ✅ Batch operations work correctly
- ✅ Validation prevents invalid metadata
- ✅ Changes persist across restarts

---

## CLI-003: Bulk Operations

**Priority**: Medium
**Estimated Time**: 5-6 hours
**Impact**: Medium-High - Essential for large-scale document management

### Description
Efficient batch operations for ingesting, updating, or deleting multiple documents with parallel processing and progress tracking.

### Command Syntax
```bash
# Bulk ingest from directory
ragged ingest /path/to/docs --recursive --workers 4

# Bulk delete by filter
ragged delete --tag deprecated --dry-run
ragged delete --tag deprecated --confirm

# Bulk re-embed
ragged re-embed --collection research --model new-model
```

### Implementation
- **Files to Create**:
  - `ragged/core/processing.py` - Worker pool implementation
  - `tests/core/test_bulk_operations.py` - Test suite

- **Files to Modify**:
  - `ragged/cli/commands/ingest.py` - Add parallel processing
  - `ragged/cli/commands/delete.py` - Add bulk delete
  - `ragged/utils/progress.py` - Enhanced progress bars

- **Dependencies**: Python multiprocessing, Rich/tqdm progress bars, transaction handling

### Testing Requirements
- Unit tests for worker pool
- Integration tests for parallel ingestion
- Error handling tests (partial failures)
- Performance benchmarks

### Acceptance Criteria
- ✅ Parallel processing faster than sequential
- ✅ Progress tracking accurate
- ✅ Errors don't crash entire batch
- ✅ --dry-run shows what would happen

---

## CLI-004: Export/Import Utilities

**Priority**: Medium
**Estimated Time**: 6-8 hours
**Impact**: High - Critical for backup, migration, and sharing

### Description
Tools for exporting and importing knowledge bases in multiple formats (JSON, CSV, archive), supporting backup, migration, and sharing scenarios.

### Command Syntax
```bash
# Export entire knowledge base
ragged export backup.tar.gz --format archive

# Export specific collection
ragged export research.json --collection research --format json

# Import knowledge base
ragged import backup.tar.gz --merge
ragged import backup.tar.gz --replace --confirm

# Export metadata only
ragged export metadata.csv --metadata-only --format csv
```

### Implementation
- **Files to Create**:
  - `ragged/cli/commands/export.py` - Export command
  - `ragged/cli/commands/import.py` - Import command
  - `ragged/core/backup.py` - Backup/restore logic
  - `tests/cli/test_export_import.py` - Test suite

- **Files to Modify**:
  - `ragged/core/storage.py` - Add export methods
  - `ragged/core/models.py` - Serialisation models

- **Dependencies**: Archive handling (tarfile, zipfile), JSON/CSV libraries, ChromaDB backup

### Testing Requirements
- Round-trip tests (export → import)
- Format validation tests
- Merge vs. replace behaviour tests
- Large knowledge base tests

### Acceptance Criteria
- ✅ Can export and import without data loss
- ✅ Multiple formats supported (JSON, CSV, archive)
- ✅ Merge mode preserves existing data
- ✅ Replace mode with safety confirmation

---

## CLI-005: Output Format Options

**Priority**: High
**Estimated Time**: 3-4 hours
**Impact**: High - Makes query results usable in different contexts

### Description
Multiple output formats for query results (JSON, CSV, Markdown, plain text, custom templates), supporting different consumption patterns and integrations.

### Command Syntax
```bash
# JSON output
ragged query "machine learning" --format json

# CSV output
ragged query "machine learning" --format csv --fields id,title,score

# Markdown table
ragged query "machine learning" --format markdown

# Plain text (default)
ragged query "machine learning" --format text

# Custom template
ragged query "machine learning" --template custom.jinja2
```

### Implementation
- **Files to Create**:
  - `ragged/cli/formatters.py` - Formatting module
  - `ragged/cli/templates/` - Jinja2 templates directory
  - `tests/cli/test_formatters.py` - Test suite

- **Files to Modify**:
  - `ragged/cli/commands/query.py` - Add format options

- **Dependencies**: Jinja2 templating, CSV writer, Rich for formatted output

### Testing Requirements
- Unit tests for each formatter
- Template rendering tests
- Edge cases: empty results, special characters
- Output validation tests

### Acceptance Criteria
- ✅ JSON, CSV, Markdown, text formats work
- ✅ Custom templates render correctly
- ✅ Field selection in CSV works
- ✅ Special characters handled properly

---

## CLI-006: Query History & Replay

**Priority**: Medium
**Estimated Time**: 4-5 hours
**Impact**: Medium - Improves iterative query refinement workflow

### Description
Maintain history of queries for replay, analysis, and iteration. Supports searching history and clearing old queries.

### Command Syntax
```bash
# View query history
ragged history list

# Replay previous query
ragged history replay 5

# Search history
ragged history search --contains "machine learning"

# Clear history
ragged history clear --before 2025-01-01
```

### Implementation
- **Files to Create**:
  - `ragged/cli/commands/history.py` - New command group
  - `ragged/core/history.py` - History storage (SQLite)
  - `tests/cli/test_history.py` - Test suite

- **Files to Modify**:
  - `ragged/cli/commands/query.py` - Record queries to history
  - `ragged/config/settings.py` - History configuration

- **Dependencies**: SQLite for history storage, Click command groups, date/time handling

### Testing Requirements
- Unit tests for history operations
- Integration tests for replay
- Privacy tests (no sensitive data storage)
- Performance tests with large histories

### Acceptance Criteria
- ✅ Queries automatically saved to history
- ✅ Can replay previous queries
- ✅ Search works across history
- ✅ Clear removes old queries

---

## CLI-007: Verbose & Quiet Modes

**Priority**: High
**Estimated Time**: 2-3 hours
**Impact**: High - Essential for debugging and automation

### Description
Global flags for controlling output verbosity across all commands. Supports multiple verbosity levels for detailed debugging.

### Command Syntax
```bash
# Verbose mode (debug information)
ragged --verbose ingest document.pdf
ragged -v query "machine learning"

# Quiet mode (minimal output)
ragged --quiet ingest document.pdf
ragged -q query "machine learning"

# Very verbose (trace level)
ragged -vv ingest document.pdf
```

### Implementation
- **Files to Create**:
  - `ragged/utils/logging.py` - Enhanced logging configuration
  - `tests/cli/test_verbosity.py` - Test suite

- **Files to Modify**:
  - `ragged/cli/main.py` - Add global flags
  - All command files - Respect verbosity settings

- **Dependencies**: Python logging module, Click global options, Rich for formatted output

### Testing Requirements
- Unit tests for log level configuration
- Integration tests across all commands
- Output capture tests
- Performance impact tests

### Acceptance Criteria
- ✅ -v shows debug information
- ✅ -q suppresses non-essential output
- ✅ -vv shows trace-level logs
- ✅ Works consistently across all commands

---

## CLI-008: Configuration Validation

**Priority**: High
**Estimated Time**: 3-4 hours
**Impact**: High - Essential for troubleshooting setup issues

### Description
Command to validate ragged configuration and diagnose setup issues. Checks embedding models, storage connections, and all configuration values.

### Command Syntax
```bash
# Validate configuration
ragged config validate

# Check specific configuration
ragged config check --embedding
ragged config check --storage
ragged config check --all

# Show current configuration
ragged config show --format json
```

### Implementation
- **Files to Create**:
  - `ragged/cli/commands/config.py` - New command group
  - `ragged/config/validation.py` - Validation logic
  - `ragged/core/health.py` - Health check utilities
  - `tests/cli/test_config.py` - Test suite

- **Files to Modify**:
  - `ragged/config/settings.py` - Add validation methods

- **Dependencies**: Pydantic validation, service connectivity checks, configuration schema

### Testing Requirements
- Unit tests for validation rules
- Integration tests with invalid configs
- Diagnostic message tests
- Edge cases: missing files, invalid values

### Acceptance Criteria
- ✅ Detects invalid configuration values
- ✅ Checks service connectivity
- ✅ Provides helpful error messages
- ✅ Shows current config in readable format

---

## CLI-009: Environment Information

**Priority**: Medium
**Estimated Time**: 2-3 hours
**Impact**: Medium - Useful for debugging and support

### Description
Display system information useful for debugging and support requests. Shows Python version, installed packages, hardware info, and ragged configuration.

### Command Syntax
```bash
# Show all environment info
ragged info

# Show specific information
ragged info --python
ragged info --embeddings
ragged info --storage

# Export for bug reports
ragged info --format json > bug-report.json
```

### Implementation
- **Files to Create**:
  - `ragged/cli/commands/info.py` - New command
  - `ragged/utils/system.py` - System information gathering
  - `tests/cli/test_info.py` - Test suite

- **Files to Modify**:
  - `ragged/version.py` - Version information utilities

- **Dependencies**: Python sys/platform modules, package version detection, hardware detection

### Testing Requirements
- Unit tests for info gathering
- Cross-platform tests (Linux, macOS, Windows)
- Privacy tests (no sensitive data)
- Format validation tests

### Acceptance Criteria
- ✅ Shows Python and package versions
- ✅ Shows hardware information
- ✅ Shows ragged configuration
- ✅ Can export as JSON for bug reports

---

## CLI-010: Cache Management

**Priority**: Medium
**Estimated Time**: 3-4 hours
**Impact**: Medium - Essential for performance tuning and troubleshooting

### Description
Commands for managing embedding and processing caches. Show statistics, clear caches, and warm caches for better performance.

### Command Syntax
```bash
# Show cache statistics
ragged cache stats

# Clear all caches
ragged cache clear --all

# Clear specific caches
ragged cache clear --embeddings
ragged cache clear --processed-docs

# Warm cache
ragged cache warm --collection research
```

### Implementation
- **Files to Create**:
  - `ragged/cli/commands/cache.py` - New command group
  - `ragged/core/cache.py` - Enhanced cache management
  - `tests/cli/test_cache.py` - Test suite

- **Files to Modify**:
  - `ragged/embeddings/cache.py` - Add statistics methods
  - `ragged/config/settings.py` - Cache configuration

- **Dependencies**: File system operations, cache size calculation, ChromaDB cache handling

### Testing Requirements
- Unit tests for cache operations
- Integration tests for cache clearing
- Performance tests for cache warming
- Edge cases: missing cache directories

### Acceptance Criteria
- ✅ Shows cache size and hit rate
- ✅ Can clear all or specific caches
- ✅ Cache warming improves performance
- ✅ Statistics accurate and helpful

---

## CLI-011: Shell Completion

**Priority**: High
**Estimated Time**: 4-5 hours
**Impact**: High - Significantly improves CLI usability

### Description
Auto-completion support for bash, zsh, and fish shells. Provides command, option, and dynamic argument completion (e.g., collection names, document IDs).

### Command Syntax
```bash
# Generate completion script
ragged completion bash > ~/.ragged-completion.bash
ragged completion zsh > ~/.ragged-completion.zsh
ragged completion fish > ~/.config/fish/completions/ragged.fish

# Install completion
ragged completion install --shell bash
```

### Implementation
- **Files to Create**:
  - `ragged/cli/completion.py` - Completion generation
  - Shell-specific completion files (bash, zsh, fish)
  - `tests/cli/test_completion.py` - Test suite

- **Files to Modify**:
  - `ragged/cli/main.py` - Command registration for completion

- **Dependencies**: Click shell completion, shell detection, file system operations

### Testing Requirements
- Manual tests in each shell
- Completion generation tests
- Dynamic completion tests (e.g., document IDs)
- Cross-platform tests

### Acceptance Criteria
- ✅ Bash completion works
- ✅ Zsh completion works
- ✅ Fish completion works
- ✅ Dynamic completions (collections, etc.) work
- ✅ Easy installation process

---

## CLI Enhancements Summary

**Total Enhancements**: 11

**Total Estimated Time**: 48-62 hours

**Priority Distribution**:
- High: 6 enhancements (Search, Metadata, Output Formats, Verbose/Quiet, Config Validation, Shell Completion)
- Medium: 5 enhancements (Bulk Ops, Export/Import, Query History, Env Info, Cache Management)

**Category Breakdown**:
- Document Management: 3 (Search, Metadata, Bulk Ops)
- Query & Retrieval: 2 (Output Formats, Query History)
- User Experience: 2 (Verbose/Quiet, Shell Completion)
- Configuration & Setup: 2 (Config Validation, Env Info)
- Performance & Debugging: 1 (Cache Management)
- Advanced Features: 1 (Export/Import)

**Integration Points**:
- All enhancements integrate with existing command structure
- Consistent error handling and output formatting
- Respect global verbosity flags
- Support all collection operations
- Documented in CLI reference and guides

---

## Related Documentation

- [Main v0.2.7 Roadmap](../README.md)
- [CLI Enhancements Catalogue](../../../../planning/interfaces/cli/enhancements.md)
- [UX Improvements](./ux-improvements.md)
- [Performance Optimisations](./performance-optimisations.md)

---
