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

### Future Minor Versions (Post-v0.7.0)

**Potential v0.7.1+ enhancements based on user feedback:**
- Installation analytics (opt-in, privacy-preserving)
- Embedded ChromaDB mode (no Docker requirement)
- Installation video/screencasts
- Automated dependency installation (with permission)
- Additional configuration presets for niche use cases

**Note:** Minor versions determined by user feedback after v0.7.0 release.

---

## Success Criteria for v0.7.x Series

**Measurable Goals:**
- Time-to-first-query: <15 minutes (target: <10 minutes)
- Installation success rate: >95% on clean systems
- User satisfaction: "Installation was easy" >4/5 rating
- Support reduction: 50% fewer installation-related requests
- Documentation: README <100 lines, getting-started <10 minutes

**Qualitative Goals:**
- Non-technical users can install without help
- Error messages are actionable (user knows what to do)
- First-run experience is confidence-building
- Documentation structure is discoverable
- CLI is approachable for beginners

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

- [v0.7.0 Detailed Roadmap](./v0.7.0/README.md) - Installation & onboarding features
- [v0.6.0 Roadmap](../v0.6/README.md) - Intelligent optimisation (prerequisite)
- [Current Installation Guide](../../../../tutorials/installation.md) - Existing documentation
- [Troubleshooting Guide](../../../../guides/troubleshooting.md) - Current troubleshooting
- [Version Overview](../README.md) - Complete version comparison

---
