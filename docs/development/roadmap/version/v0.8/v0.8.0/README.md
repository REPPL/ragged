# Ragged v0.8.0 Roadmap - Installation Foundation & Prerequisites System

**Status:** Planned

**Total Hours:** 30-40 hours (AI implementation)

**Focus:** Robust prerequisite detection, automated dependency installation, and installation scaffolding

**Breaking Changes:** None

**Dependencies:** Requires v0.7.x completion (production-ready application to install)

**Purpose:** Build the foundation for effortless ragged installation by detecting, installing, and configuring all prerequisites automatically

---

## Overview

Version 0.8.0 establishes the foundation for ragged's installation system, transforming manual dependency management into automated prerequisite detection and installation. This version focuses on **robustly detecting** what's installed, **automatically installing** missing dependencies, and **validating** the environment is ready for ragged.

### Problem Statement

**Current Installation Process (Manual):**
```bash
# User must manually:
1. Install Docker Desktop (or Docker Engine + Docker Compose)
2. Install Python 3.10+ with pip
3. Install Ollama
4. Pull Ollama models
5. Start ChromaDB in Docker
6. Create configuration files
7. Set up directory structure
8. Install ragged with pip
9. Verify everything works
```

**Issues with Current Process:**
- 9+ manual steps with platform-specific variations
- Cryptic error messages if steps missed or incorrect
- No verification until running ragged
- Dependency version conflicts not detected
- Port conflicts discovered at runtime
- File permission issues surface later
- No uninstall process

### Target Outcomes

**After v0.8.0 Implementation:**
- ✅ Prerequisite detection: Automatically detect installed dependencies (Docker, Python, Ollama)
- ✅ Automated installation: Install missing prerequisites with user consent
- ✅ Environment validation: Verify versions, ports, permissions before installation
- ✅ Configuration management: Generate config files from templates
- ✅ Installation scaffolding: Create directory structure, set permissions
- ✅ Health verification: Post-install checks ensure everything works
- ✅ Clear error messages: Actionable diagnostics with fix suggestions

---

## PREREQ-001: Prerequisite Detection System (6-8 hours)

**Problem:** No automated way to detect what's installed; users must manually verify dependencies.

**Implementation:**

1. **Design detection architecture** [1.5-2 hours]
   - Pluggable detector system:
     - Each dependency has dedicated detector class
     - Detectors return: installed (bool), version (str), path (str), issues (list)
   - Platform-specific detection (Windows, macOS, Linux)
   - Caching to avoid repeated checks
   - Schema for detector results

2. **Implement Docker detection** [1.5-2 hours]
   - Check for Docker binary:
     - macOS: `/usr/local/bin/docker`, `/Applications/Docker.app`
     - Linux: `/usr/bin/docker`, `which docker`
     - Windows: `C:\Program Files\Docker\Docker\Docker Desktop.exe`
   - Verify Docker daemon running: `docker info`
   - Check Docker Compose: `docker-compose --version` or `docker compose version`
   - Detect version: `docker --version`
   - Validate minimum version (Docker 20.10+, Compose 2.0+)
   - Identify installation method (Docker Desktop, Docker Engine)

3. **Implement Python detection** [1-1.5 hours]
   - Check Python binaries: `python3`, `python`
   - Verify version ≥3.10: `python3 --version`
   - Check pip installed: `python3 -m pip --version`
   - Validate venv capability: `python3 -m venv --help`
   - Detect virtual environment: Check `VIRTUAL_ENV` environment variable
   - Check Python installation path (system vs user)

4. **Implement Ollama detection** [1-1.5 hours]
   - Check Ollama binary:
     - macOS: `/usr/local/bin/ollama`
     - Linux: `/usr/local/bin/ollama`, `~/.ollama/bin/ollama`
     - Windows: `C:\Users\<user>\AppData\Local\Programs\Ollama\ollama.exe`
   - Verify Ollama service running: `ollama list` or check port 11434
   - Detect installed models: `ollama list`
   - Check storage location: `~/.ollama/models` size
   - Validate version: `ollama --version`

5. **Implement environment detection** [0.5-1 hour]
   - Check available ports:
     - 8000 (FastAPI backend)
     - 5173 (SvelteKit dev server)
     - 8001 (ChromaDB)
     - 11434 (Ollama)
   - Verify disk space (minimum 10GB recommended)
   - Check filesystem permissions for ~/.ragged/
   - Detect OS and architecture: `uname -a` (Linux/macOS), `systeminfo` (Windows)
   - Identify shell: bash, zsh, fish, powershell

**Files:**
- `src/install/detection/base.py` (new - abstract detector, ~200 lines)
- `src/install/detection/docker.py` (new - Docker detection, ~250 lines)
- `src/install/detection/python_detector.py` (new - Python detection, ~150 lines)
- `src/install/detection/ollama.py` (new - Ollama detection, ~200 lines)
- `src/install/detection/environment.py` (new - environment checks, ~200 lines)
- `tests/install/detection/` (new - detection tests, ~400 lines total)

**Success Criteria:**
- All detectors return accurate results
- Platform-specific detection works (Windows, macOS, Linux)
- Detection completes in <5 seconds
- False positives/negatives <1%

---

## PREREQ-002: Automated Dependency Installation (8-10 hours)

**Problem:** Users must manually install missing dependencies; no automation exists.

**Implementation:**

1. **Design installation framework** [2-2.5 hours]
   - Pluggable installer system matching detectors
   - Installation strategies:
     - **Official installers:** Download and run vendor installers
     - **Package managers:** Use apt, brew, choco, etc.
     - **Manual guidance:** Provide step-by-step instructions if automation impossible
   - User consent required before installation
   - Progress tracking and status updates
   - Rollback on failure
   - Idempotent (safe to rerun)

2. **Implement Docker installation** [2.5-3 hours]
   - **macOS:**
     - Check for Homebrew: `brew --version`
     - If Homebrew: `brew install --cask docker`
     - Else: Download Docker Desktop .dmg from docker.com
     - Start Docker Desktop: `open -a Docker`
     - Wait for daemon: Poll `docker info` until success
   - **Linux:**
     - Detect distro: Ubuntu/Debian, Fedora/RHEL, Arch, etc.
     - Ubuntu/Debian: `curl -fsSL https://get.docker.com | sh`
     - Start service: `sudo systemctl start docker`
     - Add user to docker group: `sudo usermod -aG docker $USER`
   - **Windows:**
     - Download Docker Desktop installer (.exe)
     - Run installer with silent flags if possible
     - Prompt user to enable WSL 2 if needed
     - Start Docker Desktop
   - Verify installation: `docker run hello-world`

3. **Implement Python installation** [1.5-2 hours]
   - **macOS:**
     - Homebrew: `brew install python@3.11`
     - Else: Download from python.org
   - **Linux:**
     - Ubuntu/Debian: `sudo apt install python3.11 python3-pip python3-venv`
     - Fedora: `sudo dnf install python3.11`
   - **Windows:**
     - Download Python installer from python.org
     - Run with flags: `/quiet InstallAllUsers=1 PrependPath=1`
   - Verify: `python3 --version`, `python3 -m pip --version`

4. **Implement Ollama installation** [1.5-2 hours]
   - **macOS:**
     - Download Ollama installer: `curl -fsSL https://ollama.ai/install.sh | sh`
     - Or Homebrew: `brew install ollama`
   - **Linux:**
     - Run install script: `curl -fsSL https://ollama.ai/install.sh | sh`
     - Start service: `sudo systemctl start ollama`
   - **Windows:**
     - Download Ollama installer from ollama.ai
     - Run installer
   - Start Ollama service
   - Pull default model: `ollama pull llama3.2:3b` (or user-selected model)
   - Verify: `ollama list`

5. **Add error recovery and logging** [0.5-1 hour]
   - Log all installation attempts
   - Capture stderr/stdout from installers
   - Provide actionable error messages
   - Suggest manual steps if automation fails
   - Create installation report (summary of what was installed)

**Files:**
- `src/install/installers/base.py` (new - abstract installer, ~200 lines)
- `src/install/installers/docker.py` (new - Docker installation, ~400 lines)
- `src/install/installers/python_installer.py` (new - Python installation, ~250 lines)
- `src/install/installers/ollama.py` (new - Ollama installation, ~300 lines)
- `src/install/installers/utils.py` (new - download, run, progress, ~200 lines)
- `tests/install/installers/` (new - installer tests, ~400 lines)

**Success Criteria:**
- Automated installation succeeds >90% on supported platforms
- User consent required before any installation
- Clear progress indication during installation
- Installation failures provide actionable error messages
- Rollback works if installation fails midway

---

## PREREQ-003: Environment Validation (5-7 hours)

**Problem:** Environment issues (port conflicts, permissions, disk space) discovered at runtime, not install time.

**Implementation:**

1. **Implement port availability checker** [1.5-2 hours]
   - Check ports 8000, 5173, 8001, 11434 available
   - Identify processes using conflicting ports:
     - Linux/macOS: `lsof -i :<port>` or `netstat`
     - Windows: `netstat -ano | findstr :<port>`
   - Suggest killing conflicting processes or using alternative ports
   - Allow user to override default ports

2. **Implement filesystem validation** [1.5-2 hours]
   - Check ~/.ragged/ directory:
     - Create if doesn't exist
     - Verify write permissions
     - Check ownership (avoid root-owned directories)
   - Verify disk space:
     - Minimum 10GB recommended (5GB for models, 2GB for documents, 3GB for databases)
     - Warn if <10GB available
     - Block if <2GB available
   - Check filesystem type (avoid NFS, network drives for database storage)

3. **Implement dependency version validation** [1-1.5 hours]
   - Verify minimum versions:
     - Docker ≥20.10, Docker Compose ≥2.0
     - Python ≥3.10
     - Ollama ≥0.1.0 (latest recommended)
   - Check for known incompatible versions
   - Suggest upgrades if version too old
   - Warn if version too new (untested)

4. **Implement system requirements check** [0.5-1 hour]
   - Minimum RAM: 8GB (16GB recommended)
   - CPU: 2+ cores recommended
   - OS versions:
     - macOS: ≥11.0 (Big Sur)
     - Linux: Recent kernel (≥5.0)
     - Windows: ≥10
   - Warn if system below recommendations

5. **Create validation report** [0.5-1 hour]
   - Generate human-readable validation report:
     ```
     ✅ Docker 24.0.5 installed and running
     ✅ Python 3.11.4 installed
     ✅ Ollama 0.1.32 installed
     ✅ All required ports available
     ✅ 45GB disk space available
     ✅ Filesystem permissions correct
     ⚠️  RAM: 8GB (16GB recommended for large collections)
     ```
   - Categorise issues: CRITICAL (blocker), WARNING (proceed with caution), INFO
   - Provide fix suggestions for each issue

**Files:**
- `src/install/validation/ports.py` (new - port checking, ~200 lines)
- `src/install/validation/filesystem.py` (new - filesystem checks, ~250 lines)
- `src/install/validation/versions.py` (new - version validation, ~150 lines)
- `src/install/validation/system.py` (new - system requirements, ~200 lines)
- `src/install/validation/report.py` (new - validation report generation, ~150 lines)
- `tests/install/validation/` (new - validation tests, ~350 lines)

**Success Criteria:**
- All validation checks complete in <10 seconds
- Critical issues block installation
- Warnings allow user to proceed or abort
- Validation report clear and actionable
- Fix suggestions resolve 80%+ of issues

---

## PREREQ-004: Configuration Management (6-8 hours)

**Problem:** Manual configuration file creation; users don't know correct values or format.

**Implementation:**

1. **Design configuration system** [1.5-2 hours]
   - Configuration schema using Pydantic:
     - Server settings (host, port, CORS)
     - Database settings (ChromaDB host, collection name)
     - LLM settings (Ollama host, default model)
     - Storage settings (documents path, cache path)
     - Security settings (JWT secret, authentication)
   - Template system for config generation
   - Environment variable override support
   - Validation on load
   - Migration for config schema changes

2. **Implement config file generation** [2-2.5 hours]
   - Templates for common scenarios:
     - **Default:** Local development, all services on localhost
     - **Production:** Secure defaults, authentication enabled
     - **Docker:** All services in containers
     - **Hybrid:** Some local, some Docker
   - Auto-detect best configuration:
     - Use detected dependency locations
     - Assign available ports
     - Set appropriate paths (~/.ragged/)
   - Interactive prompts for user preferences:
     - Default model (llama3.2, mistral, etc.)
     - Authentication on/off
     - WebUI enabled/disabled
   - Generate .env file (never commit secrets)

3. **Implement secrets management** [1.5-2 hours]
   - Generate secure JWT secret (256-bit random)
   - Store in .env file or system keyring
   - Never log or display secrets
   - Provide secret rotation capability
   - Warn if using insecure defaults

4. **Create configuration CLI** [0.5-1 hour]
   - Commands:
     - `ragged config init` - Interactive config generation
     - `ragged config validate` - Validate config file
     - `ragged config show` - Display current config (secrets redacted)
     - `ragged config set <key> <value>` - Update config value
   - Configuration file location: `~/.ragged/config.yaml`

5. **Add configuration documentation** [0.5-1 hour]
   - Inline comments in generated config
   - Reference documentation for all settings
   - Examples for common scenarios
   - Migration guides for config schema changes

**Files:**
- `src/config/schema.py` (modify - add validation, migration, ~300 lines)
- `src/config/templates/` (new - config templates, ~200 lines)
- `src/config/generator.py` (new - config generation, ~250 lines)
- `src/install/config_manager.py` (new - installation-time config setup, ~200 lines)
- `src/cli/commands/config.py` (new - config CLI commands, ~200 lines)
- `tests/config/test_generation.py` (new - config tests, ~250 lines)

**Success Criteria:**
- Generated config files work immediately
- All required settings populated
- Secrets generated securely
- Config validation catches errors before runtime
- Interactive prompts user-friendly

---

## PREREQ-005: Installation Scaffolding (5-7 hours)

**Problem:** Manual directory creation, permission setting, and initial setup required.

**Implementation:**

1. **Implement directory structure creation** [1.5-2 hours]
   - Create standard directory layout:
     ```
     ~/.ragged/
     ├── config.yaml          # Main configuration
     ├── .env                 # Secrets (not committed)
     ├── documents/           # Uploaded documents
     ├── chromadb/            # ChromaDB data (if embedded mode)
     ├── cache/               # Query cache, embeddings cache
     ├── logs/                # Application logs
     ├── models/              # Downloaded models (if local)
     └── backups/             # Database backups
     ```
   - Set correct permissions (700 for secrets, 755 for data)
   - Create .gitignore for sensitive directories
   - Add README explaining directory structure

2. **Implement Docker setup automation** [2-2.5 hours]
   - Generate docker-compose.yml:
     - ChromaDB service
     - FastAPI backend service
     - SvelteKit frontend service (if WebUI enabled)
   - Pull required Docker images:
     - `chromadb/chroma:latest`
     - Custom images if needed
   - Create Docker volumes for persistence
   - Set up Docker networks
   - Start services: `docker-compose up -d`
   - Wait for health checks to pass

3. **Implement initial data setup** [1-1.5 hours]
   - Create default ChromaDB collection
   - Seed database with initial data (if applicable)
   - Create default user (if authentication enabled)
   - Generate API keys
   - Set up example documents (optional, user consent)

4. **Add post-install verification** [0.5-1 hour]
   - Health check all services:
     - Ollama: `curl http://localhost:11434`
     - ChromaDB: `curl http://localhost:8001/api/v1/heartbeat`
     - FastAPI: `curl http://localhost:8000/health`
     - SvelteKit: `curl http://localhost:5173` (if WebUI)
   - Run test query to verify end-to-end
   - Generate installation success report
   - Display next steps to user

5. **Create uninstall capability** [0.5-1 hour]
   - `ragged uninstall` command
   - Stop all services
   - Remove Docker containers and volumes
   - Option to keep or delete user data (~/.ragged/)
   - Remove ragged binary/package
   - Clean up PATH, shortcuts (if applicable)

**Files:**
- `src/install/scaffolding/directories.py` (new - directory creation, ~200 lines)
- `src/install/scaffolding/docker_setup.py` (new - Docker automation, ~300 lines)
- `src/install/scaffolding/initial_setup.py` (new - initial data, ~200 lines)
- `src/install/scaffolding/verification.py` (new - post-install checks, ~250 lines)
- `src/install/uninstall.py` (new - uninstall logic, ~200 lines)
- `tests/install/scaffolding/` (new - scaffolding tests, ~350 lines)

**Success Criteria:**
- Directory structure created correctly
- Permissions set appropriately
- Docker services start successfully
- Post-install verification passes
- Uninstall removes all traces (except user data if requested)

---

## Success Criteria (Test Checkpoints)

**Automated Tests:**
- [ ] All detectors return accurate results (validated against known environments)
- [ ] Installers handle errors gracefully (network failures, permission issues)
- [ ] Validation catches all critical issues (port conflicts, disk space, versions)
- [ ] Config generation produces valid, working configurations
- [ ] Directory scaffolding creates correct structure with proper permissions
- [ ] Docker setup starts all services successfully
- [ ] Post-install verification detects broken installations

**Manual Testing:**
- [ ] ⚠️ MANUAL: Run installation on fresh macOS (no dependencies)
- [ ] ⚠️ MANUAL: Run installation on fresh Ubuntu 22.04
- [ ] ⚠️ MANUAL: Run installation on Windows 11
- [ ] ⚠️ MANUAL: Test with Docker already installed (skip Docker installation)
- [ ] ⚠️ MANUAL: Test with conflicting ports (recovery works)
- [ ] ⚠️ MANUAL: Test with insufficient disk space (blocks installation)
- [ ] ⚠️ MANUAL: Verify uninstall removes everything correctly

**Quality Gates:**
- [ ] Detection completes in <5 seconds
- [ ] Installation succeeds >90% on supported platforms
- [ ] Validation catches 100% of critical issues before they cause runtime errors
- [ ] Generated configs work without manual edits
- [ ] Post-install verification confirms ragged fully operational
- [ ] Documentation complete for all features
- [ ] Error messages actionable (specific fix suggestions)

---

## Known Risks

- **Platform diversity:** Supporting Windows, macOS, and Linux variants is complex (mitigate: extensive testing, clear platform requirements)
- **Dependency conflicts:** Third-party installers may fail or conflict (mitigate: multiple installation strategies, fallback to manual)
- **User permissions:** Installation may require sudo/admin (mitigate: clearly communicate requirements, attempt non-privileged install first)
- **Network failures:** Download failures during installation (mitigate: retry logic, offline installer option in future)
- **Version drift:** Dependencies update frequently, breaking compatibility (mitigate: version pinning, automated compatibility testing)

---

## Related Documentation

- [v0.8 Series Overview](../README.md) - Installation & Deployment Excellence series
- [v0.8.1 Roadmap](../v0.8.1.md) - Interactive Installation Wizard & Automation (next version)
- [v0.7.0 Roadmap](../../v0.7/v0.7.0/README.md) - CLI UX & WebUI Integration (what we're installing)
- [v0.8.5 Roadmap](../v0.8.5.md) - Installation Security Hardening (security for installation)

---
