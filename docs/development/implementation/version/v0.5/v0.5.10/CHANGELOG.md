# v0.5.10 Changelog

**Release Date:** 2025-11-23
**Theme:** Documentation & Operational Excellence

---

## Overview

v0.5.10 is the final minor release in the v0.5.x series, focusing on documentation quality, operational guides, and developer experience improvements. This release prepares ragged for production deployments with comprehensive guides, automated tooling, and streamlined installation.

---

## New Features

### Developer Experience

**direnv Support**
- Automatic virtual environment activation when entering project directory
- Development environment variables pre-configured
- Works on macOS, Linux, and Windows WSL
- **File:** `.envrc`

**just Task Runner**
- 30+ common development commands
- Docker management (up, down, logs, rebuild)
- Testing workflows (test, coverage, watch)
- Documentation serving (docs-serve)
- Setup automation (install, setup)
- **File:** `justfile` (216 lines)

**Enhanced Installation Scripts**
- One-command installation for Linux, macOS, and Windows
- Automatic Python 3.12 detection
- Virtual environment setup
- Development mode installation
- direnv integration (if installed)
- **Files:** `scripts/install-local.sh`, `scripts/install-local.ps1`

### Documentation

**Security Guides**
- Security best practices (`docs/guides/security-guidelines.md`, 7.8K)
- Operational security monitoring (`docs/guides/security-monitoring.md`, 6.4K)
- Production hardening guidelines

**Deployment Guides**
- Docker setup and deployment (`docs/guides/docker-setup.md`, 9.1K)
- Comprehensive installation guide (`docs/tutorials/installation.md`, 19K)
- Three installation methods (Docker, Local, Development)

**Performance & GPU**
- GPU configuration and optimisation (`docs/guides/gpu-configuration-optimisation.md`, 10K)
- GPU device management (`docs/guides/gpu-management.md`, 9.8K)
- Performance tuning guide (`docs/guides/performance-tuning.md`, 13K)

**Operational Guides**
- General troubleshooting (`docs/guides/troubleshooting.md`, 11K)
- GPU troubleshooting (`docs/guides/troubleshooting/gpu-issues.md`, 12K)
- Comprehensive FAQ (`docs/guides/faq.md`, 16K)

**Tutorials**
- Complete beginner's guide (`docs/tutorials/complete-beginners-guide.md`, 18K)
- Multi-modal RAG workflow (`docs/tutorials/multimodal-workflow.md`, 12.7K)
- Scan processing tutorial (`docs/tutorials/your-first-scan.md`, 12.3K)
- Behaviour learning tutorial (`docs/tutorials/understanding-your-interest-profile.md`, 14.4K)

**API Documentation**
- Complete Sphinx-generated API reference (`docs/api/`)
- Coverage of all public APIs
- Usage examples

**Examples**
- Jupyter notebooks (`examples/notebooks/`)
- Basic usage examples (`examples/basic/`)
- Configuration examples (`examples/configs/`)
- Sample documents for testing (`examples/sample_documents/`)

---

## Improvements

### Installation Experience

**Before v0.5.10:**
```bash
git clone https://github.com/REPPL/ragged.git
cd ragged
python3.12 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

**After v0.5.10:**
```bash
# Option 1: One-command installation
curl -sSf https://raw.githubusercontent.com/REPPL/ragged/main/scripts/install-local.sh | bash

# Option 2: Development with modern tools
brew install direnv just
git clone https://github.com/REPPL/ragged.git
cd ragged  # direnv auto-activates
just setup  # All dependencies installed
```

### Developer Workflow

**Before v0.5.10:**
```bash
source .venv/bin/activate
pytest
python -m ragged.main --help
docker compose up -d
docker compose logs -f
```

**After v0.5.10:**
```bash
# direnv handles activation automatically
just test
just ragged --help
just docker-up
just docker-logs
```

### Documentation Navigation

**Before v0.5.10:**
- Documentation scattered across multiple locations
- No clear entry point for different user personas
- Limited troubleshooting guidance

**After v0.5.10:**
- Clear documentation hub (`docs/README.md`)
- Persona-based quickstarts (`docs/tutorials/personas-quickstart.md`)
- Comprehensive troubleshooting guides
- Complete FAQ with 50+ questions

---

## Breaking Changes

**None.** v0.5.10 is fully backwards compatible with v0.5.9.

---

## Migration Guide

### For Existing Users

**No migration required.** v0.5.10 adds new tools and documentation but doesn't change existing functionality.

### For Contributors

**Optional: Adopt New Developer Tools**

1. **Install direnv** (automatic environment activation):
   ```bash
   # macOS
   brew install direnv
   echo 'eval "$(direnv hook bash)"' >> ~/.bashrc

   # Linux (Debian/Ubuntu)
   apt install direnv
   echo 'eval "$(direnv hook bash)"' >> ~/.bashrc
   ```

2. **Install just** (task runner):
   ```bash
   # macOS
   brew install just

   # Linux
   cargo install just
   ```

3. **Enable in project**:
   ```bash
   cd ragged
   direnv allow  # Activates .envrc
   just --list   # See available commands
   ```

### For New Users

**Use New Installation Methods**

**Linux/macOS:**
```bash
curl -sSf https://raw.githubusercontent.com/REPPL/ragged/main/scripts/install-local.sh | bash
```

**Windows PowerShell:**
```powershell
irm https://raw.githubusercontent.com/REPPL/ragged/main/scripts/install-local.ps1 | iex
```

---

## Known Limitations

### Documentation Gaps

1. **Production Deployment Guide**
   - **Gap:** No single consolidated production deployment guide
   - **Workaround:** Content distributed across:
     - `docs/guides/docker-setup.md` (deployment)
     - `docs/guides/security-monitoring.md` (monitoring)
     - `docs/guides/security-guidelines.md` (hardening)
   - **Planned:** Consolidate in v0.6.0

2. **REST API Documentation**
   - **Gap:** No dedicated endpoint-by-endpoint REST API guide
   - **Workaround:** API documentation exists in Sphinx `docs/api/`
   - **Planned:** Expand with OpenAPI spec in v0.6.0

### Platform Support

1. **Windows Native Installation**
   - **Limitation:** Install script requires PowerShell 5.1+
   - **Workaround:** Use WSL or manual installation
   - **Note:** Docker recommended for Windows production deployments

---

## Dependencies

### No New Runtime Dependencies

v0.5.10 adds no new runtime Python dependencies.

### New Optional Developer Tools

**For Enhanced Developer Experience (optional):**
- **direnv** (optional): Automatic environment activation
- **just** (optional): Task runner for common commands

**Installation:**
```bash
# macOS
brew install direnv just

# Linux (Rust required for just)
apt install direnv
cargo install just
```

---

## Next Steps

**For Users:**
- Explore new tutorials in `docs/tutorials/`
- Check FAQ for common questions (`docs/guides/faq.md`)
- Use installation scripts for easier setup

**For Contributors:**
- Adopt direnv for automatic environment activation
- Use just commands for common development tasks
- Review updated installation guide

**For Operations:**
- Review security monitoring guide (`docs/guides/security-monitoring.md`)
- Implement production deployment using Docker guide (`docs/guides/docker-setup.md`)
- Set up troubleshooting runbooks based on guides

---

## Acknowledgements

v0.5.10 represents the culmination of the v0.5.x series, building on the foundation of:
- v0.5.0-v0.5.2: Vision embeddings and multi-modal RAG
- v0.5.3-v0.5.5: CLI enhancements and UI improvements
- v0.5.6: Documentation and manual testing
- v0.5.7-v0.5.8: Security hardening
- v0.5.9: Installation improvements
- v0.5.10: Operational excellence

---

## Related Documentation

- [v0.5.10 Implementation README](./README.md)
- [v0.5.10 Deliverables Summary](./DELIVERABLES-SUMMARY.md)
- [v0.5.10 Roadmap](../../../roadmap/version/v0.5/v0.5.10.md)
- [Installation Guide](../../../../tutorials/installation.md)
- [Troubleshooting Guide](../../../../guides/troubleshooting.md)

---

**Status:** Released
