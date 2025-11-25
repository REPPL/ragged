# Ragged v0.7.0 Roadmap - CLI User Experience & WebUI Integration

**Status:** Planned

**Total Hours:** 35-45 hours (AI implementation)

**Focus:** Seamless CLI user experience and WebUI integration

**Breaking Changes:** None

**Dependencies:** Requires v0.6.10 completion (Svelte PWA & polish)

**Purpose:** Create unified user experience across CLI and WebUI interfaces

---

## Overview

Version 0.7.0 bridges the gap between ragged's command-line interface and the Svelte WebUI delivered in v0.6.7-v0.6.10. This release focuses on making the CLI more user-friendly and ensuring seamless integration between CLI and WebUI modes, allowing users to work effectively in either environment or transition smoothly between them.

### Problem Statement

**Current CLI/WebUI Friction:**
- CLI has 30+ commands with no categorisation in help output
- Error messages show technical stack traces (not user-friendly)
- Health dashboard is CLI-only, doesn't show WebUI status
- No CLI command to launch or interact with WebUI
- Model management requires manual configuration file editing
- Configuration complexity (100+ options) with no presets
- Documentation focuses on CLI, minimal WebUI coverage
- Users unaware of WebUI capabilities after v0.6 installation

### Target Outcomes

**After v0.7.0 Implementation:**
- ✅ Organised CLI help with categorised, searchable commands
- ✅ User-friendly error messages (no stack traces unless --debug)
- ✅ Health dashboard shows both CLI and WebUI service status
- ✅ CLI commands to launch, check, and manage WebUI
- ✅ Model management integrated into CLI with user-friendly commands
- ✅ Configuration presets for common use cases (single-user, team, researcher)
- ✅ Documentation covers both CLI and WebUI equally
- ✅ Smooth onboarding explaining both interface options

---

## UI-001: CLI Command Categorisation & Improved Help (5-7 hours)

**Problem:** 30+ uncategorised CLI commands make `ragged --help` overwhelming; users can't find what they need.

**Implementation:**

1. **Design command categorisation structure** [1-1.5 hours]
   - Define categories:
     - **Document Management:** ingest, delete, list, update
     - **Query & Search:** query, search, find-similar
     - **Configuration:** config, init, reset
     - **System & Services:** health, start, stop, restart, logs
     - **WebUI:** webui, launch-webui, webui-status
     - **Models:** model-list, model-download, model-remove, model-info
     - **Maintenance:** cache-clear, optimize, backup, restore
   - Create command groups in CLI framework
   - Add category metadata to each command

2. **Implement categorised help output** [2-3 hours]
   - Modify `ragged --help` to show categories:
     ```
     ragged - Privacy-first RAG system

     Document Management:
       ingest      Add documents to knowledge base
       delete      Remove documents
       list        List all documents
       update      Update document metadata

     Query & Search:
       query       Ask questions about your documents
       search      Full-text search across knowledge base
       find-similar Find documents similar to query

     WebUI:
       webui       Launch web interface
       webui-status Check if WebUI is running

     System & Services:
       health      Check system health (CLI + WebUI)
       start       Start all services
       stop        Stop all services

     Configuration:
       config      Manage configuration
       init        Initialize new configuration

     Models:
       model-list  List available LLM models
       model-download Download new model

     Use 'ragged <command> --help' for more information.
     ```
   - Add `ragged help <category>` to show category-specific commands
   - Add `ragged search-commands <keyword>` for searchable help

3. **Add rich help formatting** [1-1.5 hours]
   - Use Rich library for coloured, formatted output
   - Category headers in bold
   - Command descriptions with examples
   - Common flags highlighted (--help, --verbose, --json)
   - Add emoji indicators for command types (📄 documents, 🔍 search, ⚙️ config, 🌐 webui)

4. **Create interactive command discovery** [0.5-1 hour]
   - `ragged commands` shows all commands with brief descriptions
   - `ragged commands --interactive` launches fuzzy finder (fzf-style)
   - Filter commands by category, keyword
   - Show usage examples inline

**Files:**
- `src/cli/__init__.py` (modify - add command categories)
- `src/cli/help.py` (new - rich help formatting)
- `src/commands/commands.py` (new - command discovery)
- `pyproject.toml` (add Rich dependency)

**⚠️ MANUAL TEST:** Run `ragged --help`, `ragged help query`, `ragged commands` and verify output is clear and organised

**Success Criteria:**
- CLI help output is categorised and easy to scan
- Users can find commands quickly (<30 seconds)
- Common tasks discoverable without reading full documentation
- Searchable command help available

---

## UI-002: User-Friendly Error Messages (5-7 hours)

**Problem:** Technical stack traces confuse non-expert users; unclear what action to take when errors occur.

**Implementation:**

1. **Design error message structure** [1-1.5 hours]
   - Define error message format:
     ```
     ❌ Error: Document not found

     What happened:
     The document 'research-notes.pdf' does not exist in your knowledge base.

     Possible causes:
     - Document was never ingested
     - Document was deleted
     - Incorrect file path specified

     What to do next:
     1. List all documents: ragged list
     2. Ingest the document: ragged ingest path/to/research-notes.pdf
     3. Check for typos in the filename

     Need more details? Run with: ragged query --debug
     ```
   - No raw stack traces in user-facing errors
   - Actionable next steps always provided
   - Debug mode (`--debug`) shows full technical details

2. **Implement error handler middleware** [2-3 hours]
   - Create `src/errors/formatter.py`:
     - `format_error_for_user(exception, context)` - User-friendly formatting
     - `format_error_for_debug(exception)` - Full stack trace with context
     - Error code mapping (ERR-001: Document not found, etc.)
   - Wrap all CLI commands with error handler
   - Detect debug flag (`--debug`) and adjust formatting
   - Log full errors to `~/.ragged/logs/errors.log` (even in non-debug mode)

3. **Create error message database** [1.5-2 hours]
   - Map common exceptions to user-friendly messages:
     - `FileNotFoundError` → Document/file not found guidance
     - `ConnectionError` → Service not running (Ollama/ChromaDB)
     - `PermissionError` → File permission issues
     - `ValueError` → Invalid input format
     - `TimeoutError` → Service timeout, suggest checking health
   - Include platform-specific guidance (Windows vs macOS vs Linux)
   - Add error recovery suggestions

4. **Add error reporting telemetry** [0.5-1 hour]
   - Track error frequency (if user opts in to telemetry in v0.8.2)
   - Generate error report: `ragged report-error <error-id>`
   - Include sanitised error context for GitHub issues

**Files:**
- `src/errors/formatter.py` (new - error formatting)
- `src/errors/messages.py` (new - error message database)
- `src/cli/middleware.py` (new - error handler wrapper)
- `src/commands/*.py` (modify - wrap with error handler)

**⚠️ MANUAL TEST:** Trigger common errors (missing file, service down, invalid input) and verify user-friendly messages

**Success Criteria:**
- Zero raw stack traces shown to users in normal mode
- All errors include actionable next steps
- Users can self-resolve 80%+ of common errors
- Debug mode provides full technical details

---

## UI-003: Enhanced Health Dashboard with WebUI Status (6-8 hours)

**Problem:** `ragged health` only shows CLI service status; users don't know if WebUI is running or how to access it.

**Implementation:**

1. **Expand health check system** [2-3 hours]
   - Add WebUI health checks to existing `ragged health`:
     - FastAPI backend: Check http://localhost:8000/health
     - SvelteKit frontend: Check http://localhost:5173 (dev) or 3000 (prod)
     - WebSocket server: Check WS connection
     - Frontend build status
   - Add performance metrics:
     - Response time for each service (ms)
     - Memory usage (WebUI frontend + backend)
     - Active WebSocket connections
   - Existing checks (Ollama, ChromaDB, disk space) remain unchanged

2. **Create rich dashboard UI** [2-3 hours]
   - Use Rich library for terminal dashboard:
     ```
     ╭─ Ragged Health Dashboard ─────────────────────────────────╮
     │                                                            │
     │ CLI Services:                                              │
     │   ✓ Ollama           Running    (11434)   Response: 45ms  │
     │   ✓ ChromaDB         Running    (8001)    Response: 23ms  │
     │   ✓ GPU Acceleration Available  (CUDA 12.1)               │
     │                                                            │
     │ WebUI Services:                                            │
     │   ✓ FastAPI Backend  Running    (8000)    Response: 12ms  │
     │   ✓ SvelteKit UI     Running    (5173)    Response: 8ms   │
     │   ✓ WebSocket Server Connected  (3 active)                │
     │   🌐 Access WebUI: http://localhost:5173                  │
     │                                                            │
     │ System Resources:                                          │
     │   💾 Disk Space:     45.2 GB free (68% available)         │
     │   🧠 Memory:         8.1 GB / 16 GB (51% used)            │
     │   📊 Knowledge Base: 1,247 documents indexed              │
     │                                                            │
     │ Overall Status: ✓ All systems operational                 │
     ╰────────────────────────────────────────────────────────────╯

     Commands:
       ragged webui        Launch WebUI in browser
       ragged start        Start all services
       ragged health --watch   Live monitoring (updates every 5s)
     ```
   - Colour-coded status (green ✓, red ✗, yellow ⚠)
   - Human-readable resource usage

3. **Add auto-repair suggestions** [1-1.5 hours]
   - If service down, show repair command:
     - Ollama not running: `Run: ragged start-ollama` or `brew services start ollama`
     - ChromaDB not running: `Run: ragged start-chromadb` or `docker-compose up -d chromadb`
     - WebUI not running: `Run: ragged webui --start`
   - Add `ragged health --fix` to attempt automatic repairs

4. **Add live monitoring mode** [0.5-1 hour]
   - `ragged health --watch` updates dashboard every 5 seconds
   - Show real-time metrics (queries/sec, active connections)
   - Highlight changes (service started, stopped)

**Files:**
- `src/commands/health.py` (modify - add WebUI checks, rich formatting)
- `src/health/webui_checker.py` (new - WebUI health checks)
- `src/health/dashboard.py` (new - rich dashboard rendering)

**⚠️ MANUAL TEST:** Run `ragged health` with various services up/down, verify accurate status and WebUI integration

**Success Criteria:**
- Health dashboard shows all services (CLI + WebUI)
- Users can access WebUI directly from health output (URL provided)
- Auto-repair suggestions reduce time-to-fix for common issues
- Live monitoring provides real-time visibility

---

## UI-004: WebUI Launch Commands (3-4 hours)

**Problem:** Users don't know how to access the WebUI delivered in v0.6; no CLI integration.

**Implementation:**

1. **Create WebUI launch command** [1.5-2 hours]
   - Implement `ragged webui` command:
     - Detect if WebUI is running
     - If not running: Start FastAPI backend + SvelteKit dev server
     - If running: Open browser to http://localhost:5173
     - Show startup logs in real-time
   - Add flags:
     - `--start`: Force start services even if running
     - `--stop`: Stop WebUI services
     - `--port <port>`: Use custom port
     - `--prod`: Run production build (port 3000)

2. **Implement WebUI status commands** [1-1.5 hours]
   - `ragged webui-status`: Check if WebUI is accessible
     - Output: "WebUI running at http://localhost:5173" or "WebUI not running"
     - Show which services are up (FastAPI, SvelteKit, WebSocket)
   - `ragged webui-logs`: Tail WebUI logs (backend + frontend)
   - `ragged webui-restart`: Restart WebUI services

3. **Add browser integration** [0.5-1 hour]
   - Auto-open browser when launching WebUI
   - Use Python `webbrowser` module
   - Add `--no-browser` flag to disable auto-open
   - Handle different browsers (default, Chrome, Firefox)

**Files:**
- `src/commands/webui.py` (new - WebUI management commands)
- `src/webui/launcher.py` (new - WebUI startup logic)

**⚠️ MANUAL TEST:** Run `ragged webui`, verify browser opens to WebUI, test --start/--stop/--port flags

**Success Criteria:**
- Single command launches WebUI (`ragged webui`)
- Browser automatically opens to WebUI
- Users can check WebUI status from CLI
- WebUI services manageable via CLI

---

## UI-005: Model Management CLI (5-7 hours)

**Problem:** Managing LLM models requires manual editing of configuration files; no visibility into available models.

**Implementation:**

1. **Create model listing command** [1.5-2 hours]
   - `ragged model-list`: Show all models:
     - Downloaded models (from Ollama)
     - Available models (from Ollama library)
     - Currently active model
     - Model size, parameters, capabilities
   - Rich table format:
     ```
     ╭─ LLM Models ─────────────────────────────────────────╮
     │ Name            Size    Parameters  Status           │
     ├──────────────────────────────────────────────────────┤
     │ ✓ llama2        3.8GB   7B          ● Active         │
     │ ✓ mistral       4.1GB   7B          Downloaded       │
     │   phi           1.6GB   2.7B        Available        │
     │   codellama     3.8GB   7B          Available        │
     ╰──────────────────────────────────────────────────────╯
     ```

2. **Implement model download/remove** [2-3 hours]
   - `ragged model-download <name>`: Download model from Ollama
     - Show progress bar with download speed
     - Verify model after download
     - Suggest using model: `ragged config set MODEL_NAME=<name>`
   - `ragged model-remove <name>`: Delete downloaded model
     - Confirm before deletion (unless `--force`)
     - Show disk space freed

3. **Add model switching** [1-1.5 hours]
   - `ragged model-use <name>`: Switch active model
     - Update `.env` file with new MODEL_NAME
     - Restart services if needed
     - Verify model works with test query
   - `ragged model-info <name>`: Show detailed model information
     - Architecture, context window, training data
     - Recommended use cases
     - Performance benchmarks

4. **Add model recommendation** [0.5-1 hour]
   - `ragged model-recommend`: Suggest models based on use case
     - Ask: "What will you use ragged for?" (research, coding, general)
     - Recommend appropriate model (llama2, codellama, etc.)
     - Estimate disk space required

**Files:**
- `src/commands/model.py` (new - model management commands)
- `src/models/manager.py` (new - Ollama integration)

**⚠️ MANUAL TEST:** Download a model, switch to it, verify it's used for queries

**Success Criteria:**
- Users can discover, download, and switch models via CLI
- No manual configuration file editing required
- Model recommendations help users choose appropriate models
- Progress feedback during downloads

---

## UI-006: Configuration Presets (4-6 hours)

**Problem:** Configuration has 100+ options; beginners overwhelmed, don't know optimal settings for their use case.

**Implementation:**

1. **Design configuration presets** [1-1.5 hours]
   - Define presets in `templates/`:
     - `config-quickstart.env`: Minimal, fastest setup
     - `config-researcher.env`: Academic use (quality over speed)
     - `config-developer.env`: Coding focus (code-optimised model)
     - `config-team.env`: Multi-user collaboration
     - `config-performance.env`: Maximum performance (GPU required)
     - `config-privacy.env`: Maximum privacy (local-only, no telemetry)
   - Document each preset's trade-offs

2. **Implement preset application** [1.5-2 hours]
   - `ragged config use-preset <name>`: Apply preset
     - Backup current `.env` to `.env.backup.<timestamp>`
     - Copy preset template to `.env`
     - Merge user customisations (preserve API keys, paths)
     - Restart services if needed
   - `ragged config list-presets`: Show all available presets
     - Display preset name, description, recommended use case

3. **Create interactive preset selector** [1-1.5 hours]
   - `ragged config wizard`: Interactive setup
     - Ask questions:
       1. "What will you use ragged for?" (research, coding, general, team)
       2. "Do you have a GPU?" (yes, no)
       3. "Privacy preference?" (local-only, standard)
     - Recommend preset based on answers
     - Apply preset and verify configuration

4. **Add preset comparison** [0.5-1 hour]
   - `ragged config compare-presets <preset1> <preset2>`: Show differences
     - Side-by-side comparison of key settings
     - Highlight trade-offs (speed vs quality, privacy vs features)

**Files:**
- `templates/config-quickstart.env` (new)
- `templates/config-researcher.env` (new)
- `templates/config-developer.env` (new)
- `templates/config-team.env` (new)
- `templates/config-performance.env` (new)
- `templates/config-privacy.env` (new)
- `src/commands/config.py` (modify - add preset commands)
- `src/config/presets.py` (new - preset management)

**⚠️ MANUAL TEST:** Apply each preset, verify configuration is valid and services work

**Success Criteria:**
- Beginners can set up ragged with single command (`ragged config use-preset quickstart`)
- Presets cover common use cases (80%+ of users)
- Interactive wizard guides users to appropriate preset
- Users can switch presets easily

---

## UI-007: Documentation Updates for CLI & WebUI (3-4 hours)

**Problem:** Documentation focuses on CLI; WebUI (delivered in v0.6) is under-documented.

**Implementation:**

1. **Update quick-start documentation** [1-1.5 hours]
   - Modify `README.md`:
     - Add "Choose Your Interface" section
     - CLI quick start (3-4 commands)
     - WebUI quick start (`ragged webui`)
     - Side-by-side comparison table (CLI vs WebUI features)
   - Add getting-started tutorial covering both interfaces

2. **Create WebUI user guide** [1-1.5 hours]
   - Create `docs/guides/webui.md`:
     - Launching WebUI from CLI
     - WebUI feature tour (document management, queries, visualisations)
     - Keyboard shortcuts
     - Settings and preferences
     - Troubleshooting WebUI issues
   - Screenshots/GIFs of WebUI (using existing design wireframes)

3. **Update CLI reference** [0.5-1 hour]
   - Ensure `docs/reference/cli.md` includes:
     - All new commands (webui, model-*, config presets)
     - Categorised command list (matching UI-001)
     - Examples for common tasks

**Files:**
- `README.md` (modify - add WebUI quick start)
- `docs/guides/webui.md` (new - WebUI user guide)
- `docs/reference/cli.md` (modify - add new commands)
- `docs/tutorials/getting-started.md` (modify - cover both CLI and WebUI)

**⚠️ MANUAL TEST:** Follow documentation as new user, verify accuracy

**Success Criteria:**
- Documentation gives equal weight to CLI and WebUI
- New users can choose their preferred interface
- WebUI features are documented comprehensively
- Quick-start covers both interfaces

---

## Success Criteria (Test Checkpoints)

**Automated Tests:**
- [ ] CLI help output shows categorised commands
- [ ] Error formatter handles all common exception types
- [ ] Health dashboard checks all services (CLI + WebUI)
- [ ] WebUI launch command starts services correctly
- [ ] Model management commands integrate with Ollama
- [ ] Configuration presets apply successfully

**Manual Testing:**
- [ ] ⚠️ MANUAL: Run `ragged --help`, verify organised output
- [ ] ⚠️ MANUAL: Trigger errors, verify user-friendly messages
- [ ] ⚠️ MANUAL: Check `ragged health`, verify WebUI status shown
- [ ] ⚠️ MANUAL: Launch WebUI with `ragged webui`, verify browser opens
- [ ] ⚠️ MANUAL: Download model with `ragged model-download`, verify progress
- [ ] ⚠️ MANUAL: Apply preset with `ragged config use-preset`, verify settings
- [ ] ⚠️ MANUAL: Follow updated documentation, verify accuracy

**Quality Gates:**
- [ ] CLI help is categorised and searchable
- [ ] Zero raw stack traces in user-facing errors
- [ ] Health dashboard shows all services (CLI + WebUI)
- [ ] WebUI launchable with single command
- [ ] Model management requires no manual config editing
- [ ] Configuration presets cover 80%+ of use cases
- [ ] Documentation covers CLI and WebUI equally

---

## Known Risks

- **Terminal compatibility:** Rich library formatting may not work on all terminals (fallback: plain text)
- **Browser detection:** Auto-opening browser may fail on headless systems (mitigate: provide URL)
- **Model download failures:** Network issues during large downloads (mitigate: resume capability)
- **Configuration merging:** Preset application may conflict with user customisations (mitigate: backup before changes)

---

## Related Documentation

- [v0.7 Series Overview](../README.md) - User Interface Enhancement & Refinement series
- [v0.7.1 Roadmap](../v0.7.1.md) - WebUI feature completeness (next version)
- [v0.6.10 Roadmap](../../v0.6/v0.6.10.md) - Svelte PWA & polish (prerequisite)
- [v0.6.0 Roadmap](../../v0.6/README.md) - Intelligent optimisation series

---
