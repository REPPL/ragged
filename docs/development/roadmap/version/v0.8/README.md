# Ragged v0.8 Series - Installation & Deployment Excellence

**Status:** Planned

**Total Hours:** 178-268 hours across 8 minor versions (5-7 months)

**Focus:** Make ragged trivially easy to install, configure, and deploy for users of all technical levels

**Breaking Changes:** None (installation improvements only)

**Dependencies:** Requires v0.7.x completion (production-ready WebUI)

**Purpose:** Transform ragged from "complex setup" to "one-command installation" with comprehensive error recovery, security, and documentation

---

## Series Overview

The v0.8 series focuses exclusively on **installation and deployment excellence**, making ragged accessible to non-technical users while maintaining power-user flexibility. After v0.7 delivered a production-ready WebUI, v0.8 ensures anyone can install and run ragged without technical expertise.

### Problem Statement

**Current Installation Challenges:**
- Manual dependency installation (Docker, Ollama, ChromaDB)
- Complex configuration files
- Platform-specific issues (Windows paths, macOS permissions, Linux variations)
- Cryptic error messages
- No automated recovery from failures
- Security misconfigurations
- Incomplete documentation
- No uninstall process
- Dependency version conflicts
- No embedded mode (Docker-free option)

### Target Outcomes

**After v0.8 Implementation:**
- ✅ One-command installation: `curl -sSL https://install.ragged.ai | sh`
- ✅ Interactive wizard for guided setup
- ✅ Automated prerequisite detection and installation
- ✅ Platform-specific installers (Windows .exe, macOS .pkg, Linux .deb/.rpm)
- ✅ Embedded mode option (no Docker required)
- ✅ Comprehensive error recovery and diagnostics
- ✅ Security hardening by default
- ✅ Complete installation documentation
- ✅ Automated testing across platforms
- ✅ One-command uninstall

---

## Version Breakdown

### Core Installation Series (Required)

**v0.8.0: Installation Foundation & Prerequisites System** (30-40 hours)
- Prerequisite detection (Docker, Python, Ollama, ChromaDB)
- Automated dependency installation
- Environment validation
- Configuration management
- Installation scaffolding

**v0.8.1: Interactive Installation Wizard & Automation** (35-45 hours)
- CLI wizard with prompts
- One-command installer script
- Progress tracking and status updates
- Configuration file generation
- Post-install verification

**v0.8.2: Post-Launch Refinements & Error Recovery** (15-25 hours)
- Error diagnostic system
- Automated recovery strategies
- Health check improvements
- Upgrade/migration paths
- Uninstall capability

### Extended Installation Features (Conditional)

**v0.8.3: Platform-Specific Installers** (20-30 hours, conditional)
- Windows installer (.exe with Inno Setup)
- macOS package (.pkg with Homebrew support)
- Linux packages (.deb, .rpm, AppImage)
- System integration (start menu, desktop shortcuts)

**v0.8.4: Embedded ChromaDB Option** (18-28 hours, conditional)
- Embedded ChromaDB (no Docker)
- Standalone deployment mode
- Resource usage optimisation
- Migration between Docker/embedded modes

### Quality & Security Series (Required)

**v0.8.5: Installation Security Hardening** (25-35 hours)
- Dependency verification (checksums, signatures)
- Secure defaults (permissions, configurations)
- Secrets management during installation
- Security audit automation
- Vulnerability scanning

**v0.8.6: Installation Testing & QA** (15-20 hours)
- Cross-platform automated tests
- Installation scenario testing
- Error recovery validation
- Performance benchmarking
- Regression testing

**v0.8.7: Installation Documentation Excellence** (20-30 hours)
- Comprehensive installation guides
- Troubleshooting knowledge base
- Video tutorials
- Quick start guides
- FAQ and common issues

---

## Decision Framework: When to Implement Extended Features

### v0.8.3: Platform-Specific Installers (Conditional)

**Implement if:**
- ✓ User feedback requests platform installers (>20 requests)
- ✓ Windows user adoption significant (>30% of users)
- ✓ Enterprise adoption requires MSI/pkg installers
- ✓ Core installation (v0.8.0-v0.8.2) proves insufficient

**Skip if:**
- ✗ Shell script installer satisfies most users (<10 installer requests)
- ✗ Resource constraints (focus on other priorities)
- ✗ Technical users dominate (comfortable with shell scripts)

**Decision Point:** After v0.8.2 release and 2-3 weeks of user feedback

---

### v0.8.4: Embedded ChromaDB Option (Conditional)

**Implement if:**
- ✓ Docker-free deployment requested (>15 requests)
- ✓ Resource-constrained environments (Raspberry Pi, low-memory VPS)
- ✓ Corporate firewalls block Docker Hub
- ✓ Simplified deployment desired (fewer moving parts)

**Skip if:**
- ✗ Docker adoption universal (<5 Docker-free requests)
- ✗ Embedded mode complexity outweighs benefits
- ✗ Performance/scalability trade-offs unacceptable

**Decision Point:** After v0.8.2 release and user feedback on deployment preferences

---

## Success Criteria by Category

### Core Installation (v0.8.0-v0.8.2)

**Installation Experience:**
- [ ] One-command installation completes in <10 minutes (average)
- [ ] Prerequisite detection 100% accurate
- [ ] Automated dependency installation succeeds >95%
- [ ] Error messages actionable (specific fix suggestions)
- [ ] Installation wizard intuitive (user testing validates)

**Error Recovery:**
- [ ] All common errors detected and diagnosed
- [ ] Automated recovery succeeds >80% of failures
- [ ] Manual recovery documented for remaining 20%
- [ ] Health check identifies all critical issues
- [ ] Uninstall removes all traces of ragged

**Quality:**
- [ ] Installation tested on 10+ platform/OS combinations
- [ ] Zero critical bugs in installation process
- [ ] Configuration generation correct 100% of time
- [ ] Post-install verification catches all issues

---

### Extended Features (v0.8.3-v0.8.4, Conditional)

**Platform Installers (v0.8.3):**
- [ ] Windows installer (silent install, uninstall, upgrades)
- [ ] macOS package (Homebrew cask, notarized)
- [ ] Linux packages (.deb for Ubuntu/Debian, .rpm for Fedora/RHEL)
- [ ] System integration complete (PATH, shortcuts, uninstall entries)

**Embedded ChromaDB (v0.8.4):**
- [ ] Embedded mode works without Docker
- [ ] Performance acceptable (<20% slower than Docker mode)
- [ ] Migration Docker ↔ embedded seamless
- [ ] Resource usage optimised (<500MB RAM)
- [ ] Feature parity with Docker mode (no missing features)

---

### Quality & Security (v0.8.5-v0.8.7)

**Security (v0.8.5):**
- [ ] All dependencies verified (checksums, signatures)
- [ ] Secure defaults enforced (file permissions, network binding)
- [ ] Secrets never logged or exposed
- [ ] Security audit automated (runs pre-install)
- [ ] Vulnerability scanning integrated (CI/CD and runtime)

**Testing (v0.8.6):**
- [ ] Cross-platform tests passing (Windows, macOS, Linux)
- [ ] Installation scenarios covered (clean install, upgrade, recovery)
- [ ] Error injection testing validates recovery
- [ ] Performance benchmarks established
- [ ] Regression testing prevents known issues

**Documentation (v0.8.7):**
- [ ] Installation guide covers all platforms
- [ ] Troubleshooting guide resolves 90% of issues
- [ ] Video tutorials for visual learners
- [ ] Quick start guide (<5 minutes to running)
- [ ] FAQ addresses common questions
- [ ] Searchable knowledge base

---

## Historical Context: Why v0.8 Focuses on Installation

### Evolution from v0.6 and v0.7

**v0.6.x (100-140h):** Delivered Svelte WebUI foundation
- FastAPI REST layer with authentication (v0.6.7)
- SvelteKit application and component library (v0.6.8)
- Interactive knowledge graphs and real-time features (v0.6.9)
- PWA capabilities and advanced features (v0.6.10)

**v0.7.x (165-245h):** Completed WebUI for production readiness
- CLI UX and WebUI integration (v0.7.0)
- Feature completeness (collections, history, preferences) (v0.7.1)
- Advanced visualisations (graphs, analytics) (v0.7.2)
- Collaboration features (conditional) (v0.7.3)
- Security hardening (v0.7.4)
- Testing and QA (v0.7.5)

**v0.8.x (178-268h):** Makes ragged accessible to everyone
- Problem: Powerful application, but installation complexity limits adoption
- Solution: Comprehensive installation experience from first-time user to enterprise deployment

---

## Known Risks

- **Platform diversity:** Testing across Windows/macOS/Linux variants expensive (mitigate: CI/CD matrix, community testing)
- **Dependency conflicts:** Third-party tools (Docker, Ollama) may have issues (mitigate: version pinning, compatibility testing)
- **False expectations:** One-command install may fail in edge cases (mitigate: clear prerequisites documentation)
- **Maintenance burden:** Installation code requires ongoing updates as dependencies evolve (mitigate: automated dependency updates, comprehensive tests)
- **Embedded mode trade-offs:** Performance/scalability may be worse than Docker mode (mitigate: clear documentation of limitations)

---

## Related Documentation

- [v0.7 Series Overview](../v0.7/README.md) - User Interface Enhancement & Refinement (prerequisite)
- [v0.7.0 Roadmap](../v0.7/v0.7.0/README.md) - CLI UX & WebUI integration (foundation)
- [v0.6 Series Overview](../v0.6/README.md) - Svelte UI foundation
- [v0.9 Series Overview](../v0.9/README.md) - Agent Capabilities & Automation (next series)

---

## Detailed Roadmaps by Minor Version

### Core Installation (Required)

- [v0.8.0: Installation Foundation & Prerequisites System](./v0.8.0/README.md) - 30-40h
- [v0.8.1: Interactive Installation Wizard & Automation](./v0.8.1.md) - 35-45h
- [v0.8.2: Post-Launch Refinements & Error Recovery](./v0.8.2.md) - 15-25h

### Extended Features (Conditional)

- [v0.8.3: Platform-Specific Installers](./v0.8.3.md) - 20-30h (conditional)
- [v0.8.4: Embedded ChromaDB Option](./v0.8.4.md) - 18-28h (conditional)

### Quality & Security (Required)

- [v0.8.5: Installation Security Hardening](./v0.8.5.md) - 25-35h
- [v0.8.6: Installation Testing & QA](./v0.8.6.md) - 15-20h
- [v0.8.7: Installation Documentation Excellence](./v0.8.7.md) - 20-30h

---
