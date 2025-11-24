# Ragged v0.7.0 Roadmap - State-of-the-Art Installation & User Onboarding

**Status:** Planned

**Total Hours:** 58-82 hours (AI implementation)

**Focus:** Best-in-class installation experience for non-expert CLI users

**Breaking Changes:** None

**Dependencies:** Requires v0.6.0 completion (intelligent optimisation)

**Purpose:** Transform ragged from "developer-friendly" to "everyone-friendly" installation

---

## Overview

Version 0.7.0 transforms ragged's installation and onboarding experience based on comprehensive analysis of current friction points. This release implements 13 focused improvements that reduce time-to-first-query from 20-30 minutes to under 10 minutes, making ragged accessible to non-technical users whilst maintaining power-user capabilities.

### Problem Statement

**Current Installation Friction:**
- Installation requires 15-30 minutes with multiple manual steps
- Python 3.12 strict requirement causes confusion
- Multiple external dependencies (Ollama, ChromaDB, Docker, Poppler) require separate installation
- Configuration has 100+ options (overwhelming for beginners)
- Error messages show technical stack traces
- No guided first-run experience
- 30+ CLI commands with no categorisation in help output
- Unclear service status and troubleshooting

### Target Outcomes

**After v0.7.0 Implementation:**
- ✅ Installation completes in <10 minutes on fresh system
- ✅ Interactive wizard asks ≤3 questions, generates optimal configuration
- ✅ Clear prerequisite validation with actionable error messages
- ✅ Guided first-run experience with working demo
- ✅ User-friendly error messages (no raw stack traces unless --debug)
- ✅ Visual service health dashboard with auto-repair capability
- ✅ Organised CLI help with categorised commands
- ✅ Comprehensive quick-start documentation (<100 lines in README)
- ✅ Model management integrated into CLI
- ✅ Configuration presets for common use cases
- ✅ Self-service troubleshooting with structured matrix

---

## INSTALL-001: Prerequisites Validation System (4-6 hours)

**Problem:** Users encounter cryptic errors when prerequisites are missing; unclear what to install or how.

**Implementation:**

1. **Create validation script** [1.5-2 hours]
   - Create `scripts/check-system.sh` with comprehensive checks:
     - Python 3.12 installed and accessible
     - Docker Desktop running (if needed for installation type)
     - Ollama installed and running
     - Required ports available (8000, 7860, 8001, 11434)
   - Output format: ✓ Ready | ✗ Missing | ⚠ Warning
   - Exit codes: 0 (all pass), 1 (critical missing), 2 (warnings only)

2. **Add platform-specific installation guidance** [0.5-1 hour]
   - macOS: Provide Homebrew commands
   - Linux: Provide apt/yum commands with distribution detection
   - Windows WSL: Provide Chocolatey/manual links
   - Direct links to official installation pages

3. **Integrate into existing installation scripts** [1-1.5 hours]
   - Auto-run at start of `setup.sh` and `install-local.sh`
   - Exit early with actionable messages if critical prerequisites missing
   - Show warnings but continue for non-critical issues
   - Add `--skip-checks` flag for advanced users

4. **Create CLI command for manual checks** [1-1.5 hours]
   - Implement `ragged check-prerequisites` command
   - Usable anytime to verify system readiness
   - Output detailed report with specific next steps
   - Add `--fix-hints` flag for automated fix suggestions

**Files:**
- `scripts/check-system.sh` (new)
- `scripts/setup.sh` (modify - add check invocation)
- `scripts/install-local.sh` (modify - add check invocation)
- `src/commands/check_prerequisites.py` (new)
- `docs/tutorials/installation.md` (add prerequisites section)

**⚠️ MANUAL TEST:** Test on fresh systems (macOS, Ubuntu, Windows WSL) with missing prerequisites

**Success Criteria:**
- Clear prerequisite validation before installation
- Users know exactly what to install and how
- Installation scripts fail fast with actionable messages
- Reduced support requests about "command not found" errors

---

## INSTALL-002: CLI Command Categorisation (2-3 hours)

**Problem:** 30+ commands are overwhelming; no logical grouping in `--help` output makes discovery difficult.

**Implementation:**

1. **Modify CLI help system** [1.5-2 hours]
   - Update `src/main.py` to group commands by category
   - Categories:
     - 🚀 **Getting Started:** ingest, query, list, health (5 essential commands)
     - 📁 **Organisation:** metadata, search, history, clear (document management)
     - ⚙️ **System:** config, cache, export, validate, env-info (maintenance)
     - 🎯 **Advanced:** gpu, scan, persona, memory, benchmark (power users)
   - Add "Quick Start" example to main help:
     ```
     Quick Start:
       ragged ingest pdf document.pdf
       ragged query "What is the main topic?"
     ```
   - Preserve existing command structure (no breaking changes)
   - Add `--show-all` flag to display uncategorised commands

2. **Update CLI documentation** [0.5-1 hour]
   - Synchronise `docs/reference/cli/command-reference.md` with new categorisation
   - Update CLI guides to reference categories
   - Add category navigation to documentation

**Files:**
- `src/main.py` (modify - implement command grouping)
- `docs/reference/cli/command-reference.md` (update with categories)
- `docs/guides/cli/cli-features.md` (reference categorisation)

**⚠️ MANUAL TEST:** Run `ragged --help` and verify categorisation is clear and intuitive

**Success Criteria:**
- CLI help output is organised and scannable
- Users can discover commands by purpose/category
- Essential commands prominently featured
- Advanced features discoverable but not overwhelming

---

## INSTALL-003: Quick Start Documentation (3-4 hours)

**Problem:** Main README is 328 lines, overwhelming for new users seeking quick orientation.

**Implementation:**

1. **Create QUICKSTART.md in project root** [1.5-2 hours]
   - Single-page reference with 5 essential commands
   - Structure:
     ```markdown
     # Ragged Quick Start

     ## 1. Check System Health
     ragged health
     → Verify services running

     ## 2. Ingest Document
     ragged ingest pdf document.pdf
     → Expected output: [example]

     ## 3. Query
     ragged query "What is the main topic?"
     → Expected output: [example]

     ## 4. List Documents
     ragged list
     → Shows ingested documents

     ## 5. Get Help
     ragged --help
     → Explore all commands

     ## Common Workflows
     - Research papers: [workflow]
     - Personal notes: [workflow]
     - Code documentation: [workflow]

     ## Next Steps
     - [Complete Guide](docs/tutorials/complete-beginners-guide.md)
     - [CLI Features](docs/guides/cli/cli-features.md)
     - [Troubleshooting](docs/guides/troubleshooting.md)
     ```
   - Include expected outputs for each command
   - Link to comprehensive guides

2. **Restructure main README.md** [1-2 hours]
   - Reduce from 328 lines to ~100 lines
   - New structure:
     ```markdown
     # ragged

     [2-3 sentence description]
     [Architecture diagram]

     ## Quick Start (5 minutes)
     1. Install: `curl -sSf https://... | bash`
     2. Ingest: `ragged ingest pdf doc.pdf`
     3. Query: `ragged query "your question"`
     → See [QUICKSTART.md](QUICKSTART.md)

     ## Key Features
     [Bullet list with links to explanation docs]

     ## Installation
     [Table: CLI / Docker / Development]
     → Details: [Installation Guide](docs/tutorials/installation.md)

     ## Documentation
     - [Quick Start](QUICKSTART.md) - 5 essential commands
     - [Complete Guide](docs/tutorials/complete-beginners-guide.md)
     - [Troubleshooting](docs/guides/troubleshooting.md)

     ## Installation Problems?
     - Run: `ragged health --fix`
     - See: [Troubleshooting Guide](docs/guides/troubleshooting.md)

     ## Project Status
     [Version, license, contributing links]
     ```
   - Move detailed content to appropriate docs (preserve, don't delete)
   - Focus on: What is ragged? → Quick install → First query → Learn more

3. **Update navigation links** [0.5-1 hour]
   - Link QUICKSTART.md from README (prominent position)
   - Update `docs/README.md` to reference QUICKSTART
   - Add to installation completion messages

**Files:**
- `QUICKSTART.md` (new - ~50-75 lines)
- `README.md` (restructure from 328 to ~100 lines)
- `docs/README.md` (update navigation links)
- `scripts/setup.sh`, `scripts/install-local.sh` (mention QUICKSTART in completion)

**⚠️ MANUAL TEST:** New user reads README, follows to QUICKSTART, completes first query

**Success Criteria:**
- README under 100 lines, scannable in <2 minutes
- QUICKSTART provides clear path to first success in <5 minutes
- Users know where to find deeper documentation
- Reduced "where do I start?" questions

---

## INSTALL-004: User-Friendly Error Messages (5-7 hours)

**Problem:** Technical Python stack traces confuse non-expert users; unclear what action to take next.

**Implementation:**

1. **Create error handling framework** [2-3 hours]
   - Implement `src/errors/handlers.py` with error wrapper system
   - Define `UserFriendlyError` exception class
   - Map common Python exceptions to user-friendly messages
   - Include "Try: ..." actionable suggestions in all errors
   - Add error context (command being executed, service involved)

2. **Implement common error catches** [2-3 hours]
   - Service connection errors:
     - Ollama: "Ollama is not running. Start with: ollama serve"
     - ChromaDB: "ChromaDB is not running. Start with: docker compose up chromadb -d"
     - API: "ragged API is not running. Start with: ragged serve"
   - Configuration errors:
     - Python version: "ragged requires Python 3.12. You have 3.11. Install Python 3.12: [link]"
     - Port conflicts: "Port 8000 in use by another application. Stop it or change RAGGED_API_PORT in .env"
     - Invalid paths: "Data directory not found: /path. Create with: mkdir -p /path"
   - Model errors:
     - Missing model: "Model 'llama3.2:3b' not found. Download with: ollama pull llama3.2:3b"
     - Model loading failed: "Failed to load model. Check VRAM (need 4GB+) or use CPU mode"
   - Document errors:
     - File not found: "Document 'file.pdf' not found. Check path and permissions"
     - Unsupported format: "Format '.xyz' not supported. Supported: PDF, TXT, MD"

3. **Add debug mode control** [0.5-1 hour]
   - Suppress stack traces by default (user-friendly mode)
   - Show full stack traces when `--debug` flag present
   - Always write full traces to log files (`~/.ragged/logs/`)
   - Add environment variable: `RAGGED_DEBUG_MODE=1` for persistent debug

4. **Update all error messages with help references** [0.5-1 hour]
   - End all errors with:
     ```
     For diagnosis: ragged health
     For help: docs/guides/troubleshooting.md
     Support: https://github.com/REPPL/ragged/issues
     ```
   - Coloured output: red for errors, yellow for warnings, green for success

**Files:**
- `src/errors/handlers.py` (new - error wrapper framework)
- `src/errors/__init__.py` (new - exports)
- `src/main.py` (modify - add global error handler wrapper)
- `src/commands/*.py` (modify - add specific error handling to each command)
- `src/services/*.py` (modify - raise UserFriendlyError instead of generic exceptions)

**⚠️ MANUAL TEST:**
- Stop Ollama, run query → verify friendly error
- Use wrong Python version → verify clear message
- Create port conflict → verify actionable suggestion

**Success Criteria:**
- No raw stack traces shown to users (unless --debug)
- Every error includes specific next action
- Error messages reference help resources
- Reduced support requests for common errors
- User satisfaction: "errors tell me what to do"

---

## INSTALL-005: Interactive Installation Wizard (8-12 hours)

**Problem:** Multiple installation paths and configuration complexity overwhelming for new users.

**Implementation:**

1. **Design wizard flow and questions** [1-2 hours]
   - Define 3 essential questions:
     1. **Primary use case:**
        - Research papers (PDF-heavy, vision features)
        - Personal notes (lightweight, fast startup)
        - Code documentation (text-focused)
        - General use (balanced configuration)
     2. **Installation type:**
        - CLI only (fastest, ~5 minutes)
        - Web UI + CLI (Docker, ~10 minutes)
        - Development setup (full tooling, ~15 minutes)
     3. **Install location:**
        - Default: `~/.ragged`
        - Custom: [user input]
   - Map answer combinations to optimal configurations
   - Design confirmation step: "I'll install with these settings: [summary]"

2. **Create interactive installation script** [4-6 hours]
   - Implement `scripts/install-interactive.sh`
   - Interactive UI:
     - Use `dialog`/`whiptail` if available (better UX)
     - Fallback to simple prompts for compatibility
     - Show progress indicators during long operations
     - Clear explanations for each question
   - Generate optimal `.env` based on answers:
     - Research use case → enable vision, larger models, more VRAM
     - Personal use case → lightweight models, faster startup
     - Code use case → text embeddings, no vision overhead
   - Pre-select Ollama model:
     - Research: `llama3.2:3b` + `colpali` for vision
     - Personal/Code: `llama3.2:1b` (faster, smaller, 700MB)
     - General: `llama3.2:3b` (balanced, 2GB)
   - Start services automatically:
     - Docker mode: `docker compose up -d`
     - CLI mode: start Ollama if not running
   - Run prerequisite checks (INSTALL-001)
   - Run verification: `ragged health`
   - Idempotent: safe to re-run

3. **Add model recommendations by use case** [1-2 hours]
   - Create model registry: `src/config/models.yaml`
   - Define model metadata:
     - Name, size, speed, quality, use cases
     - VRAM requirements, CPU fallback support
   - Implement model selection logic
   - Show download size estimate before pulling

4. **Create customised "Next Steps" output** [1-1.5 hours]
   - Display relevant commands for chosen use case:
     - Research: "Try: ragged ingest pdf paper.pdf --vision"
     - Personal: "Try: ragged ingest text notes.txt"
     - Code: "Try: ragged ingest directory src/ --recursive"
   - Link to appropriate guides:
     - Research → Vision features guide
     - Personal → Personal knowledge management guide
     - Code → Code documentation guide
   - Suggest first actions:
     - "Ingest sample document to test"
     - "Run ragged query 'test' to verify setup"

5. **Document wizard in installation guide** [0.5-1 hour]
   - Add "Interactive Installation" section to `docs/tutorials/installation.md`
   - Include screenshots/examples of wizard flow
   - Document what each use case configures

**Files:**
- `scripts/install-interactive.sh` (new - 200-300 lines)
- `src/config/models.yaml` (new - model registry)
- `templates/config-*.env` (modify - add comments for wizard selections)
- `docs/tutorials/installation.md` (add wizard section)

**⚠️ MANUAL TEST:**
- Run wizard, choose each use case
- Verify generated .env is optimal
- Verify services start correctly
- Verify first query works

**Success Criteria:**
- Users answer 3 questions, get working installation
- Configuration optimised for chosen use case
- Installation completes without manual intervention
- Next steps customised and actionable
- Wizard completable in <2 minutes (excluding downloads)

---

## INSTALL-006: Enhanced Health Dashboard (6-8 hours)

**Problem:** `ragged health` returns JSON; not user-friendly; unclear service status and next actions.

**Implementation:**

1. **Create visual health dashboard** [3-4 hours]
   - Replace JSON output with formatted Rich console table
   - Dashboard sections:
     ```
     ragged System Health Check
     ═══════════════════════════════════════════════════════

     Core Services:
     ✓ Ollama          http://localhost:11434       [Healthy]  2.3ms
     ✓ ChromaDB        http://localhost:8001        [Healthy]  1.8ms
     ✗ ragged API      http://localhost:8000        [Stopped]

     Configuration:
     ✓ Environment     ~/.ragged/.env               [Valid]    12 vars set
     ✓ Data directory  ~/.ragged/storage            [Ready]    8.4GB used
     ⚠ Cache           ~/.cache/huggingface         [Large]    15.2GB - consider cleaning

     Models:
     ✓ LLM             llama3.2:3b                  [Loaded]   2.0GB
     ✓ Embeddings      all-MiniLM-L6-v2             [Ready]    90MB
     ✗ Vision          colpali-v1.3                 [Missing]  Run: ragged models download colpali

     System:
     ✓ Python          3.12.0                       [Compatible]
     ✓ Docker          24.0.5                       [Running]
     ⚠ GPU             None detected                [CPU mode] Queries will be slower
     ✓ Ports           8000,7860,8001,11434         [Available]

     Overall Status: Degraded (1 service stopped, 1 model missing)
     Suggestion: Run 'ragged health --fix' to automatically repair issues
     ```
   - Colour-coded status: green (✓), red (✗), yellow (⚠)
   - Response time for services
   - Specific suggestions for each issue

2. **Implement auto-repair mode** [2-3 hours]
   - Add `ragged health --fix` functionality:
     - Auto-start stopped services (with confirmation)
     - Pull missing models (show size, confirm)
     - Create missing directories
     - Fix common config issues:
       - Port conflicts → suggest alternative ports
       - Invalid paths → create directories
       - Permission issues → suggest chmod commands
     - Report actions taken:
       ```
       Repairing ragged installation...

       ✓ Started Ollama service
       ✓ Started ChromaDB container
       ⚠ Cannot download colpali (15GB) - run manually: ragged models download colpali
       ✓ Created data directory: ~/.ragged/storage

       Repair complete. Re-run 'ragged health' to verify.
       ```
   - Add `--auto-approve` flag to skip confirmations (for automation)
   - Dry-run mode: `--fix --dry-run` shows what would be fixed

3. **Preserve JSON output option** [0.5-1 hour]
   - Add `--json` flag for programmatic use
   - Maintain backward compatibility with existing health check JSON format
   - Add `--format` option: `table` (default), `json`, `yaml`

4. **Update documentation** [0.5-1 hour]
   - Add visual examples to `docs/reference/cli/command-reference.md`
   - Document `--fix` mode usage and safety
   - Add to troubleshooting guide: "First step: run ragged health --fix"

**Files:**
- `src/commands/health.py` (major refactor - visual dashboard)
- `src/services/repair.py` (new - auto-repair logic)
- `docs/reference/cli/command-reference.md` (add health examples)
- `docs/guides/troubleshooting.md` (reference health --fix prominently)

**⚠️ MANUAL TEST:**
- Stop services, run `ragged health` → verify visual status
- Run `ragged health --fix` → verify auto-repair works
- Run `ragged health --json` → verify backward compatibility

**Success Criteria:**
- Visual, scannable service status
- Auto-repair fixes common issues without manual intervention
- Clear next actions for issues that can't be auto-fixed
- Backward compatible JSON output preserved
- Reduced "how do I check if it's working?" questions

---

## INSTALL-007: First-Run Welcome Experience (5-7 hours)

**Problem:** No guided first-run experience; users unsure what to do immediately after installation.

**Implementation:**

1. **Create welcome command** [2-3 hours]
   - Implement `src/commands/firstrun.py` with `ragged welcome`
   - Welcome flow:
     ```
     ╔══════════════════════════════════════════════════════════╗
     ║  Welcome to ragged - Privacy-First RAG System            ║
     ╚══════════════════════════════════════════════════════════╝

     ragged helps you query your documents using AI - completely locally.

     Let me verify your installation...
     ✓ All services running
     ✓ Models loaded
     ✓ Ready to process documents

     Would you like to try ragged with a sample document? [Y/n]

     → Ingesting sample document (ragged-quickstart.pdf)...
     ✓ Ingested 1 document (3 pages, 15 chunks)

     → Running sample query: "What is ragged?"...
     ✓ ragged is a privacy-first RAG system that runs entirely locally...

     ╔══════════════════════════════════════════════════════════╗
     ║  Quick Tips for Your Use Case: [Research/Personal/etc]   ║
     ╚══════════════════════════════════════════════════════════╝

     Essential Commands:
       ragged ingest pdf document.pdf      Ingest a document
       ragged query "your question"        Ask a question
       ragged list                         Show documents
       ragged --help                       See all commands

     Next Steps:
       • [Link to guide for your use case]
       • [Link to CLI features]
       • [Link to troubleshooting]

     Ready to start! See QUICKSTART.md for more examples.
     ```
   - Detect first run: check for `~/.ragged/first-run-complete` flag
   - Run automatic service checks
   - Offer to ingest sample document
   - Run sample query to demonstrate
   - Show tips relevant to installation choices (read from `~/.ragged/install-config.json`)
   - Create completion flag after success

2. **Integrate into CLI initialisation** [1-1.5 hours]
   - Auto-run welcome on first `ragged` command invocation
   - Detect first run in `src/main.py`
   - Add `--skip-welcome` flag for automation/CI
   - Add `ragged welcome --replay` to run again manually
   - Store welcome completion timestamp

3. **Create sample documents** [1-1.5 hours]
   - Add `examples/sample-documents/` directory
   - Include:
     - `ragged-quickstart.pdf` (2-3 pages, ragged overview)
     - `ragged-faq.txt` (common questions)
     - `sample-paper.pdf` (if research use case)
   - Pre-optimised for quick ingestion (<5 seconds)
   - Meaningful content that demonstrates ragged capabilities

4. **Update installation scripts** [0.5-1 hour]
   - Modify completion messages in `setup.sh`, `install-local.sh`
   - Mention welcome experience: "Run 'ragged' to start the welcome experience"
   - Store installation choices in `~/.ragged/install-config.json` for welcome personalisation

**Files:**
- `src/commands/firstrun.py` (new - welcome command)
- `src/main.py` (modify - first-run detection)
- `examples/sample-documents/` (new directory with sample files)
- `scripts/setup.sh`, `scripts/install-local.sh` (update completion messages)
- `~/.ragged/install-config.json` (generated - stores installation choices)

**⚠️ MANUAL TEST:**
- Fresh installation → run first command → verify welcome triggers
- Complete welcome flow → verify sample query works
- Run `ragged welcome --replay` → verify can re-run

**Success Criteria:**
- Users see working demo immediately after installation
- First query completes successfully
- Next steps customised to use case
- Confidence boost: "it works!"
- Reduced "what do I do now?" questions

---

## INSTALL-008: Smart Service Auto-Start (3-4 hours)

**Problem:** Cryptic errors when services aren't running; manual service management burdensome for new users.

**Implementation:**

1. **Add service detection to command initialisation** [1.5-2 hours]
   - Before commands that need services (`ingest`, `query`), check if running
   - Detection logic:
     - Ollama: HTTP GET to `http://localhost:11434/api/tags`
     - ChromaDB: HTTP GET to `http://localhost:8001/api/v1/heartbeat`
   - If service not running, prompt:
     ```
     ⚠ ChromaDB is not running but required for this command.

     Start ChromaDB now? [Y/n]

     This will run: docker compose up chromadb -d
     ```
   - Start service on confirmation
   - Add `--auto-start-services` flag to skip prompts (always start)
   - Add `--no-auto-start` flag to disable (for CI/automation)

2. **Create service management utilities** [1-1.5 hours]
   - Implement `src/services/manager.py`:
     - `check_service(name) -> bool` - Check if service running
     - `start_service(name) -> Result` - Start service
     - `stop_service(name) -> Result` - Stop service
   - Detect installation type:
     - Docker: use `docker compose` commands
     - Native: use system commands (`ollama serve &`)
   - Use appropriate start commands based on platform (macOS/Linux/Windows)
   - Return structured results (success, error message, next steps)

3. **Add configuration option** [0.5-1 hour]
   - Add to `.env.example` and config:
     ```bash
     # Auto-start services when needed (default: prompt)
     RAGGED_AUTO_START_SERVICES=prompt  # Options: prompt, always, never
     ```
   - Document in `docs/reference/configuration.md`
   - Honour user preference in all commands

**Files:**
- `src/services/manager.py` (new - service management utilities)
- `src/commands/ingest.py` (modify - add service check before ingestion)
- `src/commands/query.py` (modify - add service check before query)
- `.env.example` (add AUTO_START_SERVICES option)
- `docs/reference/configuration.md` (document auto-start options)

**⚠️ MANUAL TEST:**
- Stop ChromaDB, run ingest → verify prompt appears
- Confirm start → verify service starts and command continues
- Set AUTO_START_SERVICES=always → verify no prompt
- Set AUTO_START_SERVICES=never → verify fails with clear error

**Success Criteria:**
- Services start automatically when needed (with confirmation)
- No more "connection refused" errors for new users
- Power users can disable auto-start
- Service management transparent and non-intrusive
- Reduced frustration from manual service management

---

## INSTALL-009: Unified Installation Script (6-8 hours)

**Problem:** Multiple installation scripts (`setup.sh`, `install-local.sh`, `install-interactive.sh`) confusing; unclear which to use.

**Implementation:**

1. **Create master installation script** [3-4 hours]
   - Implement `scripts/install.sh` as unified entry point
   - Support installation modes via flags:
     ```bash
     ./scripts/install.sh [OPTIONS]

     Options:
       --cli           CLI-only installation (fastest)
       --docker        Full Docker stack (API + Web UI)
       --dev           Development setup (full tooling)
       --interactive   Interactive wizard (default)
       --non-interactive  Silent install with defaults
       --repair        Repair broken installation
     ```
   - Default behaviour: Run interactive wizard (INSTALL-005)
   - Intelligent detection:
     - Platform: macOS / Linux / Windows WSL
     - Existing installation: repair vs fresh install
     - Available package managers: brew / apt / yum
   - Installation flow:
     1. Run prerequisite checks (INSTALL-001)
     2. Report missing dependencies with platform-specific install commands
     3. Pause and ask user to install missing items (unless --auto-install)
     4. Verify again after user confirms ready
     5. Proceed with installation based on mode
     6. Configure based on mode/wizard choices
     7. Start services (if Docker/API mode)
     8. Pull models with progress indicators
     9. Run first-run experience (INSTALL-007) unless --skip-welcome
     10. Display success message with next steps
   - Progress indicators for long operations
   - Coloured output for better UX

2. **Make idempotent and resumable** [2-3 hours]
   - Detect partial installations:
     - Check for `~/.ragged/install-state.json`
     - Track completed steps: [prerequisites, clone, venv, install, config, services, models]
   - Resume from last successful step:
     ```
     Detected partial installation (stopped at: install dependencies)
     Resume installation? [Y/n]
     ```
   - Safe to re-run (doesn't break existing installation):
     - Skip steps if already completed
     - Update only what's needed
   - Add `--repair` flag for fixing broken installations:
     - Re-run all steps
     - Fix permissions, paths, configurations
     - Useful for corrupted installations
   - Add `--force-fresh` flag to ignore existing installation

3. **Update documentation** [1-1.5 hours]
   - Simplify `docs/tutorials/installation.md`:
     - Primary method: `curl -sSf https://raw.githubusercontent.com/.../install.sh | bash`
     - Alternative: Clone and run `./scripts/install.sh`
     - Advanced: Individual scripts for specific modes
   - Keep detailed docs for advanced users
   - Update README installation section
   - Add troubleshooting: "Installation failed? Run: ./scripts/install.sh --repair"

**Files:**
- `scripts/install.sh` (new master script - 400-500 lines)
- `scripts/setup.sh` (mark as advanced/deprecated)
- `scripts/install-local.sh` (mark as advanced/deprecated)
- `~/.ragged/install-state.json` (generated - tracks installation progress)
- `docs/tutorials/installation.md` (major simplification)
- `README.md` (update installation section)

**⚠️ MANUAL TEST:**
- Fresh installation on each platform
- Interrupt installation mid-way → verify resume works
- Run on existing installation → verify safe
- Run --repair on broken installation → verify fixes issues

**Success Criteria:**
- Single entry point for all installation methods
- Intelligent detection and adaptation
- Resumable installation (survives interruptions)
- Clear progress indicators throughout
- Installation can be repaired without full reinstall
- Documentation simplified: one primary installation method

---

## INSTALL-010: Model Management CLI (5-7 hours)

**Problem:** Model downloads manual (via Ollama CLI), unclear which models to use, no ragged integration.

**Implementation:**

1. **Design model command group** [1-1.5 hours]
   - Plan `ragged models` command structure:
     - `ragged models list` - Show available/recommended models
     - `ragged models download <name>` - Pull model via Ollama
     - `ragged models status` - Show installed models
     - `ragged models set-default <name>` - Configure default model
     - `ragged models remove <name>` - Remove model
     - `ragged models info <name>` - Show model details
   - Design model registry format (YAML with metadata)

2. **Implement model commands** [3-4 hours]
   - Create `src/commands/models.py`:
     - `list`: Display available models with metadata:
       ```
       ragged Model Registry
       ════════════════════════════════════════════════════════════════

       Recommended Models:

       LLM Models:
       ✓ llama3.2:3b         [Installed]  2.0GB   Balanced performance
       ✗ llama3.2:1b         [Available]  700MB   Fast, lightweight
       ✗ llama3.1:8b         [Available]  4.7GB   High quality

       Embedding Models:
       ✓ all-MiniLM-L6-v2    [Installed]  90MB    Fast text embeddings
       ✗ nomic-embed-text    [Available]  274MB   High-quality embeddings

       Vision Models:
       ✗ colpali-v1.3        [Available]  1.2GB   Multi-modal retrieval

       Use 'ragged models download <name>' to install
       ```
     - `download`: Pull model via Ollama API:
       - Show download size before starting
       - Confirm download (especially for large models)
       - Real-time progress bar using Rich
       - Verify after download
     - `status`: Show installed models with sizes and usage stats
     - `set-default`: Update `.env` with `RAGGED_DEFAULT_MODEL=<name>`
     - `remove`: Remove model with confirmation (warn about size freed)
     - `info`: Detailed metadata (size, requirements, use cases, benchmarks)
   - Integrate with Ollama API for all operations
   - Handle errors gracefully (Ollama not running, network issues)

3. **Create model recommendations database** [0.5-1 hour]
   - Implement `src/config/models.yaml`:
     ```yaml
     llm_models:
       - name: llama3.2:3b
         size: 2.0GB
         vram: 4GB
         speed: medium
         quality: high
         use_cases: [general, research, personal]
         description: "Balanced performance for most use cases"
         recommended: true

       - name: llama3.2:1b
         size: 700MB
         vram: 2GB
         speed: fast
         quality: medium
         use_cases: [personal, quick-queries]
         description: "Lightweight model for fast responses"

     embedding_models:
       - name: all-MiniLM-L6-v2
         size: 90MB
         dimensions: 384
         speed: fast
         quality: good
         default: true

     vision_models:
       - name: colpali-v1.3
         size: 1.2GB
         vram: 8GB
         speed: medium
         quality: high
         use_cases: [research, vision-rag]
     ```
   - Load and parse in models command
   - Allow filtering by use case: `ragged models list --use-case research`

4. **Integrate with wizard** [0.5-1 hour]
   - Use model registry in installation wizard (INSTALL-005)
   - Pre-select appropriate models based on use case
   - Show size estimates during wizard

5. **Add documentation** [0.5-1 hour]
   - Update `docs/reference/cli/command-reference.md` with models commands
   - Create `docs/guides/model-selection.md`:
     - How to choose models
     - Performance vs quality trade-offs
     - VRAM requirements
     - Use case recommendations

**Files:**
- `src/commands/models.py` (new - model management)
- `src/config/models.yaml` (new - model registry)
- `src/services/ollama.py` (modify - add model download/remove functions)
- `docs/reference/cli/command-reference.md` (add models section)
- `docs/guides/model-selection.md` (new guide)

**⚠️ MANUAL TEST:**
- `ragged models list` → verify shows installed/available
- `ragged models download llama3.2:1b` → verify downloads with progress
- `ragged models set-default llama3.2:1b` → verify updates config
- `ragged models remove llama3.2:1b` → verify removes model

**Success Criteria:**
- Model management integrated into ragged
- Clear recommendations for different use cases
- Easy switching between models
- Download progress visible
- Users understand model trade-offs (size vs quality)

---

## INSTALL-011: Configuration Presets (4-6 hours)

**Problem:** 100+ configuration options overwhelming; unclear what settings to use for different use cases.

**Implementation:**

1. **Create preset templates** [2-3 hours]
   - Create `templates/` directory with 4 preset configurations:

   **templates/config-lightweight.env:**
   ```bash
   # Lightweight Configuration - Fast Startup, Minimal Resources
   # Best for: Quick queries, personal notes, limited hardware

   # Model Selection (small, fast)
   RAGGED_DEFAULT_MODEL=llama3.2:1b
   RAGGED_EMBEDDING_MODEL=all-MiniLM-L6-v2

   # Performance (optimised for speed)
   RAGGED_CHUNK_SIZE=300
   RAGGED_CHUNK_OVERLAP=50
   RAGGED_TOP_K=3

   # Features (minimal)
   RAGGED_VISION_ENABLED=false
   RAGGED_SCAN_ENABLED=false

   # Memory (low usage)
   RAGGED_CACHE_SIZE=100MB
   ```

   **templates/config-balanced.env:**
   ```bash
   # Balanced Configuration - Recommended Defaults
   # Best for: General use, good performance/quality trade-off

   RAGGED_DEFAULT_MODEL=llama3.2:3b
   RAGGED_CHUNK_SIZE=500
   RAGGED_TOP_K=5
   ```

   **templates/config-researcher.env:**
   ```bash
   # Researcher Configuration - Maximum Capabilities
   # Best for: Academic papers, vision features, deep analysis

   RAGGED_DEFAULT_MODEL=llama3.1:8b
   RAGGED_VISION_ENABLED=true
   RAGGED_VISION_MODEL=colpali-v1.3
   RAGGED_CHUNK_SIZE=750
   RAGGED_TOP_K=10
   ```

   **templates/config-developer.env:**
   ```bash
   # Developer Configuration - Debugging & Development
   # Best for: Contributing to ragged, testing, debugging

   RAGGED_DEBUG_MODE=true
   RAGGED_LOG_LEVEL=DEBUG
   RAGGED_API_ENABLED=true
   RAGGED_API_PORT=8000
   RAGGED_HOT_RELOAD=true
   ```

   - Heavily commented explaining each setting
   - Include use case descriptions
   - Hardware requirements noted
   - Estimated resource usage

2. **Implement preset system** [1.5-2 hours]
   - Add `ragged config preset <name>` command:
     - List available presets: `ragged config preset list`
     - Show preset details: `ragged config preset show <name>`
     - Apply preset: `ragged config preset apply <name>`
   - Preset application logic:
     - Backup existing `.env` to `.env.backup-{timestamp}`
     - Copy template to `~/.ragged/.env`
     - Merge user customisations where possible (preserve user-set values)
     - Show diff of changes
     - Restart services if needed (with confirmation)
   - Validation: ensure applied preset is valid (all required vars present)

3. **Integrate with installation wizard** [0.5-1 hour]
   - Wizard selects appropriate preset (INSTALL-005):
     - Research → researcher preset
     - Personal → lightweight preset
     - Code → balanced preset
     - General → balanced preset
   - Copy preset during installation
   - Document preset choice in `~/.ragged/install-config.json`

4. **Add preset documentation** [0.5-1 hour]
   - Update `docs/reference/configuration.md`:
     - "Configuration Presets" section
     - When to use each preset
     - How to customise presets
     - How to create custom presets
   - Add to QUICKSTART: "Change configuration: ragged config preset <name>"

**Files:**
- `templates/config-lightweight.env` (new)
- `templates/config-balanced.env` (new)
- `templates/config-researcher.env` (new)
- `templates/config-developer.env` (new)
- `src/commands/config.py` (add preset subcommands)
- `docs/reference/configuration.md` (document presets)
- `QUICKSTART.md` (mention presets)

**⚠️ MANUAL TEST:**
- `ragged config preset list` → verify shows all presets
- `ragged config preset apply lightweight` → verify applies and backs up
- Switch between presets → verify settings change correctly
- Customise preset, apply again → verify preserves customisations

**Success Criteria:**
- Users can switch configurations with single command
- Presets optimised for common use cases
- Configuration understandable (heavily commented)
- Easy transition from one use case to another
- Reduced configuration errors from manual editing

---

## INSTALL-012: Installation Troubleshooting Matrix (3-4 hours)

**Problem:** Troubleshooting guide comprehensive but unstructured; difficult to quickly find solution to specific installation issue.

**Implementation:**

1. **Create structured troubleshooting matrix** [2-2.5 hours]
   - Add "Installation Issues" section to `docs/guides/troubleshooting.md`
   - Table format for quick scanning:

   | Problem | Symptoms | Quick Fix | Prevention |
   |---------|----------|-----------|------------|
   | **Python 3.12 not found** | `command not found: python3.12` or `Python 3.11 detected` | Install Python 3.12:<br>macOS: `brew install python@3.12`<br>Linux: `sudo apt install python3.12`<br>Windows: Download from python.org | Run `scripts/check-system.sh` before installation |
   | **Ollama connection refused** | `Error connecting to Ollama` or `Connection refused on port 11434` | Start Ollama: `ollama serve`<br>Or check if running: `ps aux \| grep ollama` | Add Ollama to system startup:<br>macOS: Create LaunchAgent<br>Linux: systemd service |
   | **ChromaDB connection failed** | `Could not connect to ChromaDB` or `Connection refused on port 8001` | Start ChromaDB: `docker compose up chromadb -d`<br>Check Docker running: `docker ps` | Set Docker to auto-start on boot |
   | **Port already in use** | `Address already in use` or `Port 8000 in use` | Find process: `lsof -i :8000`<br>Kill process or change port in `.env`:<br>`RAGGED_API_PORT=8080` | Check ports before install: `scripts/check-system.sh` |
   | **Docker not running** | `Cannot connect to Docker daemon` | Start Docker Desktop<br>macOS: Open Docker.app<br>Linux: `sudo systemctl start docker` | Configure Docker auto-start |
   | **Model download fails** | `Failed to pull model` or `Connection timeout` | Check internet connection<br>Retry: `ollama pull llama3.2:3b`<br>Or use alternative model | Ensure stable internet during installation<br>Consider pre-downloading large models |
   | **Permission denied** | `Permission denied` on files/directories | Fix permissions:<br>`chmod +x scripts/install.sh`<br>`sudo chown -R $USER ~/.ragged` | Install to user-writable location (default: ~/.ragged) |
   | **Out of memory** | `Killed` or `MemoryError` during ingestion/query | Use smaller model: `ragged models set-default llama3.2:1b`<br>Reduce chunk size in `.env`<br>Close other applications | Check system RAM:<br>8GB minimum, 16GB recommended |
   | **GPU not detected** | `GPU not found, using CPU` | Install GPU drivers:<br>CUDA: Check NVIDIA drivers<br>Apple Silicon: Update macOS | GPU optional - ragged works on CPU (slower) |
   | **Installation interrupted** | Partial installation, missing files | Resume: `./scripts/install.sh` (automatically resumes)<br>Or repair: `./scripts/install.sh --repair` | N/A - resume feature handles this |

   - Platform-specific sub-sections (macOS / Linux / Windows WSL)
   - Each issue links to detailed solution (if complex)

2. **Link from error messages** [0.5-1 hour]
   - Update error handlers (INSTALL-004) to reference specific troubleshooting sections:
     ```
     Error: Ollama connection refused

     Quick Fix: Start Ollama with: ollama serve
     More help: docs/guides/troubleshooting.md#ollama-connection-refused
     ```
   - Use anchor links to jump to specific problems

3. **Add diagnostic command aliases** [0.5-1 hour]
   - Create `ragged diagnose` command (alias for extended health check):
     ```bash
     ragged diagnose

     Running comprehensive system diagnostics...

     ✓ Python version: 3.12.0
     ✓ Docker: Running
     ✗ Ollama: Not running → Start with: ollama serve
     ✓ ChromaDB: Healthy
     ⚠ Disk space: 8% free → Consider cleaning cache

     Detected 1 issue. See details above.
     For troubleshooting: docs/guides/troubleshooting.md
     ```
   - Runs all checks from prerequisite validator and health dashboard
   - Suggests specific troubleshooting sections based on detected issues

**Files:**
- `docs/guides/troubleshooting.md` (add installation matrix section)
- `src/errors/handlers.py` (add troubleshooting links to errors)
- `src/commands/diagnose.py` (new - alias/extended health check)

**⚠️ MANUAL TEST:**
- Encounter each common error
- Verify troubleshooting matrix has solution
- Follow quick fix → verify resolves issue
- Run `ragged diagnose` → verify suggests correct troubleshooting section

**Success Criteria:**
- Users can find solution to common installation problems in <1 minute
- Every installation error links to troubleshooting
- Matrix covers 90% of support requests
- Self-service troubleshooting reduces support burden

---

## INSTALL-013: Getting Started Tutorial Completion (4-6 hours)

**Problem:** `docs/tutorials/getting-started.md` is placeholder with minimal content; no focused quick-start tutorial exists.

**Implementation:**

1. **Write comprehensive getting-started tutorial** [3-4 hours]
   - Replace placeholder with complete 5-10 minute tutorial
   - Target audience: Complete beginners (no RAG knowledge required)
   - Structure:
     ```markdown
     # Getting Started with ragged

     **Time Required:** 5-10 minutes
     **Prerequisites:** None (we'll check together)

     ## Step 1: Check Prerequisites (1 minute)

     Before installing ragged, let's verify your system is ready.

     Download and run the prerequisite checker:
     ```bash
     curl -sSf https://raw.githubusercontent.com/.../check-system.sh | bash
     ```

     **Expected Output:**
     ```
     ✓ Python 3.12: Found
     ✓ Docker: Running
     ✗ Ollama: Not found
     ```

     If you see ✗ for any item, follow the link provided to install it.

     [Platform-specific installation links]

     ## Step 2: Choose Installation Method (30 seconds)

     ragged offers three installation methods:

     | Method | Time | Best For |
     |--------|------|----------|
     | CLI Only | ~5 min | Command-line users |
     | Web UI + CLI | ~10 min | Prefer graphical interface |
     | Development | ~15 min | Contributing code |

     **Recommendation:** Start with CLI-only for fastest setup.

     [Decision tree diagram]

     ## Step 3: Run Installation (3-5 minutes)

     Install ragged with our automated installer:

     ```bash
     curl -sSf https://raw.githubusercontent.com/.../install.sh | bash
     ```

     Or clone and run:

     ```bash
     git clone https://github.com/REPPL/ragged.git
     cd ragged
     ./scripts/install.sh --interactive
     ```

     **During installation, you'll answer 3 questions:**

     1. **What will you primarily use ragged for?**
        - Choose based on your needs
        - This optimises configuration for you

     2. **How do you want to use ragged?**
        - Choose "CLI only" for this tutorial

     3. **Install location?**
        - Press Enter for default (`~/.ragged`)

     **Expected Output:**
     [Screenshot of installation progress]

     The installer will:
     - ✓ Check prerequisites
     - ✓ Download ragged
     - ✓ Create virtual environment
     - ✓ Install dependencies
     - ✓ Download AI models (~2GB)
     - ✓ Start services
     - ✓ Run verification

     **Troubleshooting:** If installation fails, see [Troubleshooting Guide](../guides/troubleshooting.md#installation-issues)

     ## Step 4: Verify Installation (30 seconds)

     Check that everything is working:

     ```bash
     ragged health
     ```

     **Expected Output:**
     ```
     ragged System Health Check
     ═══════════════════════════

     Core Services:
     ✓ Ollama          [Healthy]
     ✓ ChromaDB        [Healthy]

     Models:
     ✓ LLM             [Loaded]
     ✓ Embeddings      [Ready]

     Overall Status: Healthy
     ```

     **If you see ✗:** Run `ragged health --fix` to auto-repair.

     ## Step 5: Ingest Your First Document (1 minute)

     Let's add a document to ragged. You can use:
     - Any PDF file you have
     - The sample document (included in installation)
     - A text file

     **Using sample document:**
     ```bash
     ragged ingest pdf examples/sample-documents/ragged-quickstart.pdf
     ```

     **Using your own document:**
     ```bash
     ragged ingest pdf /path/to/your/document.pdf
     ```

     **Expected Output:**
     ```
     Ingesting document: ragged-quickstart.pdf
     ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 100%

     ✓ Ingested 1 document
     ✓ Processed 3 pages
     ✓ Created 15 chunks
     ✓ Generated embeddings
     ✓ Stored in ChromaDB

     Document ready for queries!
     ```

     ## Step 6: Run Your First Query (30 seconds)

     Now ask a question about your document:

     ```bash
     ragged query "What is the main topic of this document?"
     ```

     **Expected Output:**
     ```
     Querying...
     ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 100%

     Answer:
     The main topic of this document is ragged, a privacy-first
     Retrieval-Augmented Generation (RAG) system that runs entirely
     locally on your machine...

     Sources:
     - ragged-quickstart.pdf (page 1, confidence: 0.89)

     Query completed in 2.3s
     ```

     **🎉 Congratulations!** You've successfully:
     - ✓ Installed ragged
     - ✓ Ingested a document
     - ✓ Run a query

     ## Step 7: Explore Commands (1 minute)

     View all available commands:

     ```bash
     ragged --help
     ```

     Essential commands for everyday use:

     ```bash
     # List all documents
     ragged list

     # Search without AI generation (faster)
     ragged search "keyword"

     # View query history
     ragged history list

     # Check system status
     ragged health

     # Get help on any command
     ragged ingest --help
     ```

     ## Next Steps

     Now that you have ragged running, explore these guides:

     **For Your Use Case:**
     - [Research Papers](../guides/use-cases/research-papers.md)
     - [Personal Notes](../guides/use-cases/personal-notes.md)
     - [Code Documentation](../guides/use-cases/code-documentation.md)

     **Learn CLI Features:**
     - [CLI Essentials](../guides/cli/essentials.md) - 5 must-know commands
     - [CLI Intermediate](../guides/cli/intermediate.md) - Power user features
     - [Complete Beginner's Guide](./complete-beginners-guide.md) - In-depth tutorial

     **Customise ragged:**
     - [Configuration Guide](../../reference/configuration.md)
     - [Model Selection](../guides/model-selection.md)

     **Need Help?**
     - [Troubleshooting Guide](../guides/troubleshooting.md)
     - [FAQ](../guides/faq.md)
     - [GitHub Issues](https://github.com/REPPL/ragged/issues)

     ## Quick Reference

     Keep [QUICKSTART.md](../../../QUICKSTART.md) bookmarked for quick command reference.

     ---

     **Installation Problems?** Run: `ragged health --fix` or see [Troubleshooting](../guides/troubleshooting.md)
     ```
   - Include screenshots/terminal captures at key steps
   - Inline troubleshooting for common issues
   - Link to deeper guides for each topic
   - Use consistent formatting and clear headings

2. **Create tutorial validation script** [0.5-1 hour]
   - Implement `tests/docs/test_getting_started.sh`
   - Automated test that tutorial steps actually work:
     - Run prerequisite checks
     - Verify commands in tutorial execute successfully
     - Check expected outputs match
   - Run in CI to catch documentation drift
   - Fail if tutorial is outdated

3. **Link from all relevant places** [0.5-1 hour]
   - README.md: Prominent "Getting Started" link
   - Installation completion message: "Next: Follow Getting Started tutorial"
   - docs/README.md: Feature getting-started prominently
   - Welcome experience (INSTALL-007): Mention tutorial

**Files:**
- `docs/tutorials/getting-started.md` (complete rewrite - ~300-400 lines)
- `tests/docs/test_getting_started.sh` (new - tutorial validator)
- `.github/workflows/docs-validation.yml` (add tutorial test)
- `README.md` (add prominent getting-started link)
- `docs/README.md` (feature tutorial)

**⚠️ MANUAL TEST:**
- Fresh user follows tutorial from start to finish
- Verify all commands work as documented
- Time tutorial execution (should be 5-10 minutes)
- Non-technical user attempts tutorial without guidance

**Success Criteria:**
- Clear 5-10 minute path from zero to first query
- Tutorial validated automatically (no drift)
- All commands copy-paste-able
- Expected outputs shown for verification
- No placeholders or TODOs in tutorial
- Users complete successfully without external help

---

## Success Criteria (Test Checkpoints)

### Automated Tests

- [ ] Prerequisites checker detects missing components correctly
- [ ] CLI `--help` displays categorised commands
- [ ] Error messages are user-friendly (no raw stack traces unless --debug)
- [ ] Health command shows visual dashboard (not JSON by default)
- [ ] Health --fix repairs common issues
- [ ] First-run welcome executes successfully
- [ ] Model management commands work (list, download, status)
- [ ] Config presets can be applied successfully
- [ ] Service auto-start prompts and starts services
- [ ] Unified installer completes on all platforms
- [ ] Getting-started tutorial automated test passes
- [ ] All existing tests still pass (no regressions)

### Manual Testing Requirements

- [ ] ⚠️ MANUAL: Fresh system installation (macOS clean VM)
- [ ] ⚠️ MANUAL: Fresh system installation (Ubuntu clean VM)
- [ ] ⚠️ MANUAL: Fresh system installation (Windows WSL clean environment)
- [ ] ⚠️ MANUAL: Interactive wizard completes successfully (all use cases)
- [ ] ⚠️ MANUAL: Non-technical user can install without help (observe user)
- [ ] ⚠️ MANUAL: Error messages tested (disconnect services, verify messages actionable)
- [ ] ⚠️ MANUAL: Health --fix tested on systems with issues
- [ ] ⚠️ MANUAL: First-run experience smooth and informative (user feedback)
- [ ] ⚠️ MANUAL: Documentation accuracy (follow all tutorials, verify steps work)
- [ ] ⚠️ MANUAL: README under 100 lines (count and verify readability)
- [ ] ⚠️ MANUAL: QUICKSTART completable in <5 minutes (timed test)
- [ ] ⚠️ MANUAL: Getting-started tutorial completable in 5-10 minutes (timed test)

### Quality Gates

- [ ] **Time-to-first-query:** <15 minutes on fresh system (target: <10 minutes)
- [ ] **Installation success rate:** >95% on clean systems (all platforms)
- [ ] **README.md length:** <100 lines
- [ ] **QUICKSTART.md length:** <75 lines
- [ ] **Getting-started tutorial:** 5-10 minute read + execution
- [ ] **CLI help organisation:** 4 categories (Getting Started, Organisation, System, Advanced)
- [ ] **Error messages:** 100% actionable (include specific next steps)
- [ ] **Health dashboard:** 5 status sections (Services, Config, Models, System, Overall)
- [ ] **User satisfaction:** "Installation was easy" rating >4/5 (user survey)
- [ ] **Support reduction:** 50% fewer installation-related support requests

---

## Time Breakdown Summary

| Component | Feature | Hours |
|-----------|---------|-------|
| INSTALL-001 | Prerequisites validation system | 4-6 |
| INSTALL-002 | CLI command categorisation | 2-3 |
| INSTALL-003 | Quick start documentation | 3-4 |
| INSTALL-004 | User-friendly error messages | 5-7 |
| INSTALL-005 | Interactive installation wizard | 8-12 |
| INSTALL-006 | Enhanced health dashboard | 6-8 |
| INSTALL-007 | First-run welcome experience | 5-7 |
| INSTALL-008 | Smart service auto-start | 3-4 |
| INSTALL-009 | Unified installation script | 6-8 |
| INSTALL-010 | Model management CLI | 5-7 |
| INSTALL-011 | Configuration presets | 4-6 |
| INSTALL-012 | Installation troubleshooting matrix | 3-4 |
| INSTALL-013 | Getting-started tutorial completion | 4-6 |
| **TOTAL** | **All installation improvements** | **58-82 hours** |

**Estimate Confidence:** Medium-High
- Based on comprehensive installation/UX analysis
- Hour ranges account for implementation complexity and testing
- Integration work between components may create efficiencies

---

## Known Risks

- **Windows WSL support:** May need additional platform-specific adjustments and testing
- **Interactive wizard UX:** Critical to get right - bad UX worse than no wizard (requires user testing)
- **Service auto-start:** May not work in all environments (permissions, Docker configurations)
- **Model downloads:** Dependent on internet speed - slow connections = poor first experience
- **Configuration presets:** May not cover all edge cases - some users need custom configs
- **Documentation maintenance:** Keeping docs in sync with code requires discipline
- **Cross-platform testing:** Need access to clean VMs for all platforms (macOS, Linux, Windows)
- **User testing:** Essential for validation - need real non-technical users to test

---

## Implementation Notes

### Dependencies Between Components

**Can implement in parallel:**
- INSTALL-001 (Prerequisites) + INSTALL-002 (CLI categorisation) + INSTALL-003 (Docs)
- INSTALL-010 (Model management) + INSTALL-011 (Config presets) + INSTALL-012 (Troubleshooting)

**Sequential dependencies:**
- INSTALL-004 (Error messages) → Used by all other components
- INSTALL-001 (Prerequisites) → Used by INSTALL-009 (Unified installer)
- INSTALL-005 (Wizard) → Uses INSTALL-010 (Models) and INSTALL-011 (Presets)
- INSTALL-006 (Health dashboard) → Used by INSTALL-007 (Welcome) and INSTALL-008 (Auto-start)
- INSTALL-009 (Unified installer) → Integrates most other components

**Recommended implementation order:**
1. Phase 1: INSTALL-001, 002, 003, 004 (foundations)
2. Phase 2: INSTALL-006, 010, 011, 012 (utilities)
3. Phase 3: INSTALL-007, 008 (user experience)
4. Phase 4: INSTALL-005, 009, 013 (integration and polish)

---

## Next Version

After v0.7.0 completion and user feedback:

**Potential v0.7.1 enhancements:**
- Installation analytics (opt-in, privacy-preserving)
- Platform-specific installers (macOS DMG, Windows MSI, Linux DEB/RPM)
- Embedded ChromaDB mode (no Docker requirement)
- Installation video/screencasts
- Automated dependency installation (with permission)

**Future major versions:**
- v0.8.0: Advanced features based on user feedback
- v0.9.0: Production readiness (original v0.7.0 content - API stability, scalability, auth)
- v1.0.0: First stable release with full API guarantees

---

## Related Documentation

- [v0.7 Series Overview](../README.md) - Overview of v0.7.x series
- [v0.6.0 Roadmap](../../v0.6/README.md) - Intelligent optimisation (prerequisite)
- [Current Installation Guide](../../../../../tutorials/installation.md) - Current documentation
- [Troubleshooting Guide](../../../../../guides/troubleshooting.md) - Current troubleshooting
- [Version Overview](../../README.md) - Complete version comparison

---
