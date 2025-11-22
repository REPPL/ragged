## Part 7: Advanced CLI Features (52-71 hours)

This part adds 11 advanced CLI capabilities that transform ragged into an interactive, automation-ready, and developer-friendly tool. These enhancements focus on interactive workflows, automation, performance analysis, and developer productivity.

**Related Documentation:** [CLI Enhancements Catalogue](../../../../../planning/interfaces/cli/enhancements.md)

---

### CLI-012: Interactive Mode

**Priority**: High

**Estimated Time**: 8-10 hours

**Impact**: High - REPL-style interface for exploratory workflows

**Description:**
REPL-style interactive mode for exploratory workflows and iterative querying. Provides command history, tab completion, and session persistence.

**Command Syntax:**
```bash
# Start interactive mode
ragged interactive

# Interactive commands
> query machine learning
> refine --top-k 5
> show metadata doc_id_123
> help
> exit
```

**Implementation:**
- **Files to Create**:
  - `ragged/cli/commands/interactive.py` - New REPL command
  - `ragged/cli/repl.py` - REPL implementation
  - `ragged/cli/completers.py` - Interactive completion
  - `tests/cli/test_interactive.py` - Test suite

- **Dependencies**: Prompt Toolkit for REPL, Rich for formatted output, command history, tab completion

**Acceptance Criteria:**
- ✅ REPL starts and accepts commands
- ✅ Tab completion works
- ✅ Command history persists
- ✅ All ragged commands available interactively

**See:** [CLI Enhancements Catalogue](../../../../../planning/interfaces/cli/enhancements.md#12-interactive-mode) for full specification

---

### CLI-013: Query Templates & Saved Queries

**Priority**: Medium

**Estimated Time**: 5-6 hours

**Impact**: Medium - Reusable query patterns with parameters

**Description:**
Save and reuse complex query patterns with parameter substitution. Supports templating with Jinja2 for dynamic queries.

**Command Syntax:**
```bash
# Save query as template
ragged query "research on {topic} after {date}" \
  --save-template research-query

# Use template
ragged template run research-query \
  --topic "machine learning" \
  --date 2025-01-01

# List templates
ragged template list

# Delete template
ragged template delete research-query
```

**Implementation:**
- **Files to Create**:
  - `ragged/cli/commands/template.py` - New command group
  - `ragged/core/templates.py` - Template management
  - `tests/cli/test_templates.py` - Test suite

- **Dependencies**: Jinja2 templating, parameter validation, template storage

**Acceptance Criteria:**
- ✅ Can save queries as templates
- ✅ Parameter substitution works
- ✅ Templates persist across sessions
- ✅ Validation prevents invalid parameters

**See:** [CLI Enhancements Catalogue](../../../../../planning/interfaces/cli/enhancements.md#13-query-templates--saved-queries) for full specification

---

### CLI-014: Performance Profiling

**Priority**: Medium

**Estimated Time**: 5-6 hours

**Impact**: Medium - Essential for optimisation and troubleshooting

**Description:**
Profile query and ingestion performance to identify bottlenecks. Generates detailed performance reports with flamegraphs.

**Command Syntax:**
```bash
# Profile query
ragged query "machine learning" --profile

# Profile ingestion
ragged ingest document.pdf --profile

# Generate profile report
ragged profile report --format html
```

**Implementation:**
- **Files to Create**:
  - `ragged/cli/profiling.py` - Profiling utilities
  - `ragged/core/metrics.py` - Metrics collection
  - `tests/cli/test_profiling.py` - Test suite

- **Dependencies**: Python cProfile, performance metrics, report generation (HTML/JSON)

**Acceptance Criteria:**
- ✅ Profiling data collected accurately
- ✅ Reports show bottlenecks clearly
- ✅ Minimal performance overhead
- ✅ HTML and JSON output supported

**See:** [CLI Enhancements Catalogue](../../../../../planning/interfaces/cli/enhancements.md#14-performance-profiling) for full specification

---

### CLI-015: Quality Metrics

**Priority**: Medium

**Estimated Time**: 6-8 hours

**Impact**: High - Measure and improve retrieval quality

**Description:**
Measure and report on retrieval quality metrics (precision, recall, MRR, nDCG). Integrates with RAGAS for automated evaluation.

**Command Syntax:**
```bash
# Evaluate retrieval quality
ragged evaluate --test-set queries.json

# Show quality metrics
ragged metrics show --collection research

# Generate quality report
ragged metrics report --format html
```

**Implementation:**
- **Files to Create**:
  - `ragged/cli/commands/evaluate.py` - New command group
  - `ragged/core/evaluation.py` - Metrics calculation
  - `ragged/core/metrics.py` - Metric definitions
  - `tests/cli/test_evaluation.py` - Test suite

- **Dependencies**: Evaluation frameworks (RAGAS), test set handling, statistical calculations

**Acceptance Criteria:**
- ✅ Standard metrics calculated correctly
- ✅ Test sets loaded and processed
- ✅ Reports generated in multiple formats
- ✅ Integration with RAGAS works

**See:** [CLI Enhancements Catalogue](../../../../../planning/interfaces/cli/enhancements.md#15-quality-metrics) for full specification

---

### CLI-016: Watch Mode

**Priority**: Low

**Estimated Time**: 4-5 hours

**Impact**: Medium - Automatic document ingestion

**Description:**
Automatically ingest new documents as they appear in watched directories. Supports file patterns and recursive watching.

**Command Syntax:**
```bash
# Watch directory
ragged watch /path/to/docs --recursive

# Watch with filters
ragged watch /path/to/docs --pattern "*.pdf"

# Stop watching
ragged watch stop
```

**Implementation:**
- **Files to Create**:
  - `ragged/cli/commands/watch.py` - New command
  - `ragged/core/watcher.py` - File system watching
  - `tests/cli/test_watch.py` - Test suite

- **Dependencies**: Watchdog library, background processing, event handling

**Acceptance Criteria:**
- ✅ New files auto-ingested
- ✅ File patterns filter correctly
- ✅ Can start/stop watching
- ✅ Handles file operations (move, delete) gracefully

**See:** [CLI Enhancements Catalogue](../../../../../planning/interfaces/cli/enhancements.md#16-watch-mode) for full specification

---

### CLI-017: Scheduled Operations

**Priority**: Low

**Estimated Time**: 5-6 hours

**Impact**: Medium - Automation for maintenance tasks

**Description:**
Schedule periodic operations like re-indexing, cache warming, or backups using cron syntax.

**Command Syntax:**
```bash
# Schedule operation
ragged schedule add \
  --operation re-index \
  --collection research \
  --cron "0 2 * * *"

# List scheduled operations
ragged schedule list

# Remove schedule
ragged schedule remove schedule_id
```

**Implementation:**
- **Files to Create**:
  - `ragged/cli/commands/schedule.py` - New command group
  - `ragged/core/scheduler.py` - Scheduling logic
  - `ragged/core/daemon.py` - Background daemon
  - `tests/cli/test_schedule.py` - Test suite

- **Dependencies**: APScheduler library, cron parsing, background processing

**Acceptance Criteria:**
- ✅ Schedules created with cron syntax
- ✅ Operations execute on schedule
- ✅ Can list and remove schedules
- ✅ Daemon runs reliably in background

**See:** [CLI Enhancements Catalogue](../../../../../planning/interfaces/cli/enhancements.md#17-scheduled-operations) for full specification

---

### CLI-018: Debug Mode

**Priority**: High

**Estimated Time**: 4-5 hours

**Impact**: High - Essential for troubleshooting

**Description:**
Enhanced debugging with step-by-step execution and state inspection. Shows detailed execution traces and intermediate results.

**Command Syntax:**
```bash
# Debug query
ragged --debug query "machine learning"

# Debug ingestion
ragged --debug ingest document.pdf

# Show debug logs
ragged debug logs --tail 100
```

**Implementation:**
- **Files to Create**:
  - `ragged/utils/debugging.py` - Debug utilities
  - `tests/cli/test_debug.py` - Test suite

- **Files to Modify**:
  - `ragged/cli/main.py` - Add debug flag
  - All commands - Add debug hooks

- **Dependencies**: Enhanced logging, state inspection, trace utilities

**Acceptance Criteria:**
- ✅ Debug output shows execution steps
- ✅ Intermediate results visible
- ✅ Logs captured and viewable
- ✅ Minimal performance impact when not debugging

**See:** [CLI Enhancements Catalogue](../../../../../planning/interfaces/cli/enhancements.md#18-debug-mode) for full specification

---

### CLI-019: Testing Utilities

**Priority**: Medium

**Estimated Time**: 6-8 hours

**Impact**: Medium - Support custom configurations and testing

**Description:**
Built-in utilities for testing custom embeddings, chunking strategies, and configurations before deployment.

**Command Syntax:**
```bash
# Test embedding model
ragged test embedding --model sentence-transformers/all-MiniLM-L6-v2

# Test chunking strategy
ragged test chunking --strategy recursive --chunk-size 500

# Test configuration
ragged test config config.yaml
```

**Implementation:**
- **Files to Create**:
  - `ragged/cli/commands/test.py` - New command group
  - `ragged/core/testing.py` - Testing utilities
  - `ragged/core/validators.py` - Validation logic
  - `tests/cli/test_testing.py` - Test suite

- **Dependencies**: Test fixtures, validation frameworks, metric calculation

**Acceptance Criteria:**
- ✅ Can test embedding models
- ✅ Can test chunking strategies
- ✅ Configuration validation works
- ✅ Clear feedback on test results

**See:** [CLI Enhancements Catalogue](../../../../../planning/interfaces/cli/enhancements.md#19-testing-utilities) for full specification

---

### CLI-020: API Server Mode

**Priority**: Low

**Estimated Time**: 8-10 hours

**Impact**: Medium - Enable programmatic access

**Description:**
Run ragged as a local API server for integration with other tools. RESTful API with OpenAPI documentation.

**Command Syntax:**
```bash
# Start API server
ragged serve --port 8000

# Start with specific collections
ragged serve --collection research --port 8000

# Show API documentation
ragged serve --docs
```

**Implementation:**
- **Files to Create**:
  - `ragged/cli/commands/serve.py` - New command
  - `ragged/api/` - New API module
  - `ragged/api/routes.py` - API endpoints
  - `ragged/api/models.py` - Request/response models
  - `tests/api/test_server.py` - Test suite

- **Dependencies**: FastAPI framework, Uvicorn server, API documentation (Swagger/ReDoc)

**Acceptance Criteria:**
- ✅ Server starts and accepts requests
- ✅ All core operations available via API
- ✅ API documentation accessible
- ✅ Only binds to localhost (security)

**See:** [CLI Enhancements Catalogue](../../../../../planning/interfaces/cli/enhancements.md#20-api-server-mode) for full specification

---

### CLI-021: Smart Suggestions

**Priority**: Low

**Estimated Time**: 5-6 hours

**Impact**: Low-Medium - Improve query quality

**Description:**
AI-powered suggestions for query refinement and command completion using local LLM.

**Command Syntax:**
```bash
# Get query suggestions
ragged query "machne lerning" --suggest

# Auto-correct
ragged query "machne lerning" --auto-correct
```

**Implementation:**
- **Files to Create**:
  - `ragged/cli/suggestions.py` - Suggestion engine
  - `ragged/core/nlp.py` - NLP utilities
  - `tests/cli/test_suggestions.py` - Test suite

- **Files to Modify**:
  - `ragged/cli/commands/query.py` - Integration

- **Dependencies**: Spell checking, query expansion, local LLM (optional)

**Acceptance Criteria:**
- ✅ Spelling corrections suggested
- ✅ Query refinements offered
- ✅ Suggestions improve query quality
- ✅ All processing stays local

**See:** [CLI Enhancements Catalogue](../../../../../planning/interfaces/cli/enhancements.md#21-smart-suggestions) for full specification

---

### CLI-022: Color Themes & Customisation

**Priority**: Low

**Estimated Time**: 3-4 hours

**Impact**: Low - Personalisation and accessibility

**Description:**
Customisable colour themes for terminal output. Includes accessibility themes (high contrast, colorblind-friendly).

**Command Syntax:**
```bash
# Set theme
ragged config theme set solarized-dark

# List themes
ragged config theme list

# Create custom theme
ragged config theme create my-theme --config theme.yaml
```

**Implementation:**
- **Files to Create**:
  - `ragged/cli/themes.py` - Theme management
  - `ragged/cli/colors.py` - Color definitions
  - `ragged/config/themes/` - Theme files
  - `tests/cli/test_themes.py` - Test suite

- **Dependencies**: Rich colour support, theme configuration, terminal detection

**Acceptance Criteria:**
- ✅ Built-in themes available
- ✅ Can create custom themes
- ✅ Themes persist across sessions
- ✅ Accessibility themes included

**See:** [CLI Enhancements Catalogue](../../../../../planning/interfaces/cli/enhancements.md#22-colour-themes--customisation) for full specification

---

### CLI Enhancements Summary

**Total Enhancements**: 11

**Total Estimated Time**: 52-71 hours

**Priority Distribution**:
- High: 2 enhancements (Interactive Mode, Debug Mode)
- Medium: 5 enhancements (Query Templates, Performance Profiling, Quality Metrics, Watch Mode, Testing Utilities)
- Low: 4 enhancements (Scheduled Ops, API Server, Smart Suggestions, Color Themes)

**Category Breakdown**:
- User Experience: 2 (Interactive Mode, Color Themes)
- Query & Retrieval: 1 (Query Templates)
- Performance & Debugging: 3 (Performance Profiling, Quality Metrics, Debug Mode)
- Advanced Features: 3 (Watch Mode, Scheduled Ops, API Server)
- Developer Tools: 2 (Testing Utilities, Smart Suggestions)

**Integration Points**:
- All enhancements build on v0.2.7 CLI foundation
- Interactive mode provides REPL for all commands
- API server enables programmatic access to all features
- Testing utilities support custom configuration validation
- Quality metrics integrate with RAGAS evaluation framework

---


---

## Related Documentation

- [CLI Enhancements Catalogue](../../../../planning/interfaces/cli/enhancements.md) - Complete CLI specifications
- [v0.3 Roadmap](../../version/v0.3/) - Overall v0.3 planning
- [v0.3.12 Implementation](../../../implementation/version/v0.3/v0.3.12/) - Themes and API server implementation
- [Testing Framework (v0.3.1)](../../version/v0.3/v0.3.1.md) - Testing utilities roadmap

---
