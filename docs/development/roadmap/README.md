# Ragged Version Roadmaps

This directory contains detailed roadmaps for all ragged versions from v0.2.3 through v0.7.0.

## Quick Overview

**Current Version:** v0.2.2

**Next 3 Versions:**
- **[v0.2.3](version/v0.2.3/README.md)** - Critical bugs (12-15h) - START HERE
- **[v0.2.4](version/v0.2.4/README.md)** - High priority bugs (20-25h)
- **[v0.2.6](version/v0.2.6/README.md)** - Code quality (12-19h)

**For complete version details**, see **[Version Overview](version/README.md)** which provides:
- All planned versions (v0.2.3 through v0.7.0)
- Comprehensive feature comparison matrix
- Hour estimates and timelines
- Success criteria and manual testing requirements
- Development workflow and principles

---

## CLI Enhancements Matrix

ragged's CLI receives comprehensive enhancements across versions v0.2.7-v0.4.0, adding 23 new capabilities distributed strategically by version.

**Related Documentation:** [CLI Enhancements Catalogue](../planning/interfaces/cli/enhancements.md)

### Enhancement Distribution by Version

| Version | Enhancements | Hours | Focus Area |
|---------|--------------|-------|------------|
| v0.2.7 | 11 | 48-62 | Foundation (document management, UX basics) |
| v0.3.0 | 11 | 52-71 | Advanced (interactive, automation, developer tools) |
| v0.4.0 | 1 | 20-25 | Extensibility (plugin system) |
| **Total** | **23** | **120-158** | **Comprehensive CLI** |

**Detailed Enhancement Specifications:**

All 23 CLI enhancements are fully documented in the [CLI Enhancements Catalogue](../planning/interfaces/cli/enhancements.md), including:
- Complete technical specifications for each enhancement
- Implementation guidance and code examples
- Testing requirements and acceptance criteria
- Cross-version dependencies and migration paths
- Category organisation and progressive enhancement strategy

**Why This Separation?**

The catalogue is the **Single Source of Truth** for CLI enhancement specifications. This roadmap provides the high-level distribution and timeline planning, while the catalogue maintains all technical details. This separation ensures consistency and prevents duplication.

---

## Development Principles

**Priority Order:**
1. **Stability First** - Fix critical bugs before adding features (v0.2.3-v0.2.6)
2. **User Value** - UX and performance improvements (v0.2.7)
3. **Advanced Features** - State-of-the-art RAG capabilities (v0.3+)

**Quality Standards:**
- Test-first approach for bug fixes
- Measurable benchmarks for performance claims
- Research-backed implementations for advanced features
- Comprehensive documentation for all changes

**See [Version Overview](version/README.md)** for:
- Detailed development workflow
- Priority rankings (P0, P1, P2, P3)
- Testing requirements
- Manual testing guidance

---

## Related Documentation

- **[Version Overview](version/README.md)** - Complete version comparison and detailed roadmaps
- [Planning Documentation](../planning/) - High-level design goals and architecture
- [Planning: Version Designs](../planning/version/) - What each version aims to achieve
- [Implementations](../implementation/) - What was actually built vs planned
- [Process: Development Logs](../process/devlogs/version/) - Development narratives
- [CLI Enhancements Catalogue](../planning/interfaces/cli/enhancements.md) - Complete CLI specifications

---

**Analysis Date**: 2025-11-11
**Current Version**: v0.2.2
**Analysed By**: Claude Code (Sonnet 4.5)
**Total Lines Analysed**: ~15,000 lines across src/, tests/, docs/
