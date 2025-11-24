# Ragged v0.7.x Series Overview - Installation & User Experience Excellence

**Status:** Planned

**Focus:** Transform ragged from "developer-friendly" to "everyone-friendly" installation

**Dependencies:** Requires v0.6.0 completion (intelligent optimisation)

---

## Series Purpose

The v0.7.x series addresses the most immediate barrier to ragged adoption: installation complexity. Whilst ragged is powerful for users who successfully install it, the installation process currently requires 15-30 minutes with multiple manual steps, making it inaccessible to non-technical users.

This series prioritises **user experience** over **enterprise features**, recognising that widespread adoption requires an excellent first impression.

---

## Series Focus: Installation & Onboarding

**Problem Statement:**
- Current installation requires deep technical knowledge
- Python 3.12 strict requirement causes friction
- Multiple external dependencies (Ollama, ChromaDB, Docker, Poppler)
- Configuration has 100+ overwhelming options
- No guided first-run experience
- Error messages are technical (stack traces)
- CLI has 30+ uncategorised commands

**Target Outcomes:**
- Installation in <10 minutes on fresh system
- Interactive wizard with ≤3 questions
- Clear prerequisite validation with actionable errors
- Guided first-run experience with working demo
- User-friendly error messages
- Visual service health dashboard
- Organised CLI help

---

## Design Philosophy Change

### Previous Direction (Deferred)
The original v0.7.0 roadmap focused on **production readiness**:
- API stability & versioning
- Horizontal scalability
- Enterprise authentication
- Monitoring & observability
- Rate limiting & quotas

**Rationale for deferral:** These features are important for v1.0 but premature before ragged has broader adoption. Installation friction is the immediate blocker preventing users from experiencing ragged's capabilities.

### New Direction (v0.7.x)
Focus on **state-of-the-art installation experience**:
- Make installation trivial for all skill levels
- Excellent error messages and troubleshooting
- Smooth onboarding with guided first-run
- Clear, concise documentation
- Self-service problem resolution

**Rationale:** Better to have 1000 happy users with easy installation than 10 enterprise users with complex deployment. Production readiness will come after v1.0 when API is stable and user base is established.

---

## Minor Versions

### v0.7.0 - State-of-the-Art Installation & User Onboarding

**Total Hours:** 58-82 hours (AI implementation)

**Status:** Planned

**Features:** 13 focused installation improvements (INSTALL-001 through INSTALL-013)

**Highlights:**
- Prerequisites validation system
- CLI command categorisation
- Quick start documentation (README <100 lines)
- User-friendly error messages (no stack traces)
- Interactive installation wizard (3 questions)
- Enhanced health dashboard with auto-repair
- First-run welcome experience
- Smart service auto-start
- Unified installation script
- Model management CLI
- Configuration presets
- Installation troubleshooting matrix
- Getting-started tutorial completion

**See:** [v0.7.0 Detailed Roadmap](./v0.7.0/README.md)

### v0.7.1 - Post-Launch Refinements & User Feedback

**Total Hours:** 15-25 hours (AI implementation)

**Status:** Planned

**Features:** 4 refinement features (REFINE-001 through REFINE-004)

**Highlights:**
- Installation analytics (opt-in, privacy-preserving)
- Enhanced error recovery based on real user issues
- Installation resume/checkpoint system
- Configuration migration tools

**Delivers:** Refined installation based on real user experiences

**Dependencies:** Requires v0.7.0 completion and 2-4 weeks of user feedback

**See:** [v0.7.1 Roadmap](./v0.7.1.md)

### v0.7.2 - Platform-Specific Enhancements & Native Installers

**Total Hours:** 20-30 hours (AI implementation)

**Status:** Planned (conditional on user demand)

**Features:** 3 platform features (PLATFORM-001 through PLATFORM-003)

**Highlights:**
- macOS DMG installer (drag-and-drop, code signing, menu bar)
- Windows MSI installer (native, PATH, Start Menu)
- Linux DEB/RPM packages (apt/yum compatibility, systemd)

**Delivers:** Professional native installers for all major platforms

**Decision Criteria:** Implement if GitHub requests >10 OR enterprise adoption requires OR analytics show script friction >20%

**Dependencies:** Requires v0.7.1 completion

**See:** [v0.7.2 Roadmap](./v0.7.2.md)

### v0.7.3 - Embedded ChromaDB Option (Optional)

**Total Hours:** 18-28 hours (AI implementation)

**Status:** Conditional (implement only if Docker is major pain point)

**Features:** 2 embedded features (EMBED-001 through EMBED-002)

**Highlights:**
- Embedded ChromaDB mode (no Docker required)
- Performance optimisations for embedded mode
- Migration tools between Docker and embedded modes
- Backup and restore for embedded database

**Delivers:** Docker-free installation option

**Decision Criteria:** Implement if Docker causes >30% of failures OR strong user demand (>15 requests) OR embedded achieves 80%+ performance

**Dependencies:** Requires v0.7.1 completion and Docker pain point validation

**See:** [v0.7.3 Roadmap](./v0.7.3.md)

### v0.7.4 - Testing & Quality Assurance (Conditional)

**Total Hours:** 12-18 hours (AI implementation)

**Status:** Conditional (implement only if v0.7.3 is built)

**Features:** 3 QA features (QA-001 through QA-003)

**Highlights:**
- Automated installation testing (CI/CD matrix across platforms)
- Installation documentation polish (platform guides, videos)
- Performance benchmarking (Docker vs embedded comparison)

**Delivers:** Quality gate for complete v0.7.x series

**Decision Criteria:** Automatic - implement if v0.7.3 exists, skip otherwise

**Dependencies:** Only implement if v0.7.3 is built

**See:** [v0.7.4 Roadmap](./v0.7.4.md)

---

## Decision Framework for v0.7.x Minor Versions

### v0.7.0 (Foundation)
**Status:** ✓ Committed - detailed roadmap exists

**Decision:** No decision required - this is the foundation version

### v0.7.1 (Post-Launch Refinements)
**Status:** ✓ Recommended - essential for addressing real user feedback

**When to implement:** After v0.7.0 release and 2-4 weeks of user feedback

**Decision criteria:** Always implement (address real user pain points)

### v0.7.2 (Platform Installers)
**Status:** ⚠️ Conditional - implement if user demand justifies

**When to implement:** After v0.7.1 release and feedback analysis

**Decision criteria:**
- ✓ GitHub requests for native installers (>10 independent requests)
- ✓ Enterprise adoption feedback requires professional installers
- ✓ Analytics show script friction (>20% abandon installation)
- ✗ Skip if script-based installation proves sufficient (<5% abandonment)

**Decision point:** After v0.7.1 release and 2-3 weeks of feedback

### v0.7.3 (Embedded ChromaDB)
**Status:** ⚠️ Optional - implement only if Docker is major barrier

**When to implement:** After v0.7.1 analytics review, prototype validation

**Decision criteria:**
- ✓ Docker failures account for >30% of installation issues (from v0.7.1 analytics)
- ✓ Strong user demand (>15 independent GitHub issues/requests)
- ✓ Embedded mode achieves 80%+ of Docker performance (prototype validation)
- ✗ Skip if Docker installation proves unproblematic (<10% failures)
- ✗ Skip if performance gap too large (embedded >30% slower)

**Decision point:** After v0.7.1 analytics review, before v0.7.2 development

### v0.7.4 (Quality Gate)
**Status:** ⚠️ Automatic - implement if v0.7.3 built, skip otherwise

**When to implement:** Immediately after v0.7.3 completion (if v0.7.3 exists)

**Decision criteria:**
- ✓ Implement if v0.7.3 is built (provides quality gate for extended series)
- ✗ Skip if v0.7.3 not built (core series doesn't need separate QA version)

**Decision point:** Automatic based on v0.7.3 implementation status

---

## Success Criteria for v0.7.x Series

### Core Series (v0.7.0-v0.7.1)

**Measurable Goals:**
- Time-to-first-query: <10 minutes (from current 20-30 minutes)
- Installation success rate: >98% on clean systems (up from v0.7.0's 95% target)
- User satisfaction: "Installation was easy" >4/5 rating
- Support reduction: 50% fewer installation-related requests
- Documentation: README <100 lines, getting-started <10 minutes

**Qualitative Goals:**
- Non-technical users can install without help
- Error messages are actionable (user knows what to do)
- First-run experience is confidence-building
- Documentation structure is discoverable
- CLI is approachable for beginners

### Extended Series (if v0.7.2-v0.7.4 built)

**Additional Goals:**
- Native installer adoption: >40% of users choose DMG/MSI/DEB over script (v0.7.2)
- Embedded mode adoption: >20% of users where Docker is pain point (v0.7.3)
- Embedded mode performance: 80-90% of Docker performance (v0.7.3)
- Installation testing coverage: 100% of all paths (v0.7.4)
- Documentation accuracy: 100% match with implementation (v0.7.4)

---

## Impact on Roadmap

### What This Means for Production Readiness

The features originally planned for v0.7.0 (production readiness) are **deferred but not cancelled**:

**New timeline:**
- **v0.7.x:** Installation & user experience (current)
- **v0.8.x:** Advanced features based on user feedback
- **v0.9.x:** Production readiness (API stability, scalability, auth, monitoring)
- **v1.0.0:** First stable release with API guarantees

**Rationale:** This sequencing ensures:
1. Users can actually install ragged (v0.7.x)
2. Feature set is validated with broader user base (v0.8.x)
3. Production features built on stable foundation (v0.9.x)
4. v1.0 represents truly production-ready, widely-adopted system

---

## Known Risks

- **Windows WSL support:** May need additional platform-specific work
- **User testing dependency:** Need real non-technical users for validation
- **Documentation maintenance:** Keeping docs in sync requires discipline
- **Feature creep:** Must resist adding features over improving experience
- **Delayed production readiness:** Enterprise users may need to wait for v0.9

---

## Next Major Version

After v0.7.x series completion:
- **v0.8.0:** Advanced features (domain-specific enhancements, community requests)
- Continue iterating on user feedback from improved installation
- Prepare foundation for production readiness in v0.9

---

## Related Documentation

### v0.7.x Minor Versions
- [v0.7.0 Detailed Roadmap](./v0.7.0/README.md) - Installation & onboarding features (foundation)
- [v0.7.1 Roadmap](./v0.7.1.md) - Post-launch refinements & user feedback
- [v0.7.2 Roadmap](./v0.7.2.md) - Platform-specific installers (conditional)
- [v0.7.3 Roadmap](./v0.7.3.md) - Embedded ChromaDB option (optional)
- [v0.7.4 Roadmap](./v0.7.4.md) - Testing & quality assurance (conditional)

### Related Versions
- [v0.6.0 Roadmap](../v0.6/README.md) - Intelligent optimisation (prerequisite)
- [Version Overview](../README.md) - Complete version comparison

### Current Documentation
- [Installation Guide](../../../../tutorials/installation.md) - Existing documentation
- [Troubleshooting Guide](../../../../guides/troubleshooting.md) - Current troubleshooting

---
