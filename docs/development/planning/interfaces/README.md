# User Interface Design Documentation

**Status:** Active

**Last Updated:** 2025-11-14

**Purpose:** Central hub for all user interface design documentation (both CLI and web UI)

---

## Overview

This directory contains comprehensive design documentation for all ragged user interfaces:

- **CLI (Command-Line Interface)** - Terminal-based interaction
- **Web UI** - Browser-based graphical interface

Both interfaces share the same underlying ragged system but are optimised for different user workflows and preferences.

---

## Directory Structure

```
UI/
├── cli/               → CLI design and enhancements
│   └── enhancements.md   → Complete CLI feature catalogue (23 enhancements)
└── web/               → Web UI version designs
    ├── v0.2-basic.md        → Basic Gradio interface
    ├── v0.3-enhanced.md     → Multi-modal support
    ├── v0.4-technical.md    → Advanced features
    ├── v0.5-rebuild.md      → Modern frontend rebuild
    └── v1.0-production.md   → Production-ready system
```

---

## CLI Design

### [CLI Enhancements Catalogue](./cli/enhancements.md)

**Purpose:** Comprehensive specification of 23 CLI enhancements distributed across v0.2.7, v0.3.0, and v0.4.0

**Total Scope:** 120-158 hours of development

**Coverage:**
- **v0.2.7** (11 enhancements, 48-62 hours) - Foundation capabilities
- **v0.3.0** (11 enhancements, 52-71 hours) - Advanced interactive features
- **v0.4.0** (1 enhancement, 20-25 hours) - Plugin architecture

**Categories:**
- Document Management (3 enhancements, 12-15 hours)
- Query & Retrieval (3 enhancements, 12-15 hours)
- User Experience (4 enhancements, 18-23 hours)
- Configuration & Setup (3 enhancements, 9-12 hours)
- Performance & Debugging (4 enhancements, 18-23 hours)
- Advanced Features (5 enhancements, 37-48 hours)
- Developer Tools (2 enhancements, 11-14 hours)

**Key Features:**
- Advanced search and filtering
- Interactive REPL mode
- Query templates and history
- Performance profiling and quality metrics
- Shell completion for bash/zsh/fish
- Plugin system for unlimited extensibility

**Implementation Tracking:**
- See [v0.2.7 Roadmap](../process/roadmap/version/v0.2.7/README.md) for CLI foundation
- See [v0.3.0 Roadmap](../process/roadmap/version/v0.3.0/README.md) for advanced CLI
- See [v0.4.0 Roadmap](../process/roadmap/version/v0.4.0/README.md) for plugin system

---

## Web UI Design

ragged's web UI evolves through five major versions, progressing from basic Gradio interface to production-ready modern frontend.

### Version Progression

| Version | Document | Focus | Status |
|---------|----------|-------|--------|
| v0.2 | [v0.2-basic.md](./web/v0.2-basic.md) | Basic Gradio interface | Implemented |
| v0.3 | [v0.3-enhanced.md](./web/v0.3-enhanced.md) | Multi-modal support | Planned |
| v0.4 | [v0.4-technical.md](./web/v0.4-technical.md) | Advanced features | Planned |
| v0.5 | [v0.5-rebuild.md](./web/v0.5-rebuild.md) | Modern frontend rebuild | Planned |
| v1.0 | [v1.0-production.md](./web/v1.0-production.md) | Production-ready system | Vision |

### [v0.2 - Basic Web UI](./web/v0.2-basic.md)

**Current Status:** Implemented (with known issues)

**Technology:** Gradio 5.5.0

**Capabilities:**
- Document upload and ingestion
- Text query interface
- Source citation display
- Collection management
- Configuration interface

**Known Issues:**
- API endpoints non-functional (BUG-001)
- Requires fixing before further development

### [v0.3 - Enhanced Web UI](./web/v0.3-enhanced.md)

**Focus:** Multi-modal support and improved UX

**New Capabilities:**
- Image and table processing
- Enhanced source preview with syntax highlighting
- Conversation history
- Export functionality (PDF, Markdown)
- Advanced filtering and search

**Prerequisites:** v0.2.5 bug fixes completed

### [v0.4 - Technical Web UI](./web/v0.4-technical.md)

**Focus:** Advanced RAG features and developer tools

**New Capabilities:**
- Query decomposition interface
- HyDE retrieval toggle
- Cross-encoder reranking controls
- RAGAS evaluation dashboard
- Chunking strategy selection
- Performance profiling

**Prerequisites:** v0.3.0 advanced RAG implementation

### [v0.5 - Modern Frontend Rebuild](./web/v0.5-rebuild.md)

**Focus:** Complete rewrite with modern frontend framework

**Technology Migration:**
- **From:** Gradio (Python-based)
- **To:** React/Vue + FastAPI backend

**Benefits:**
- Better performance and responsiveness
- Custom components and interactions
- Professional polish
- Extensibility for future features

**Prerequisites:** Stable v0.4 API endpoints

### [v1.0 - Production Web UI](./web/v1.0-production.md)

**Focus:** Production-ready system with enterprise features

**New Capabilities:**
- Multi-user authentication
- Role-based access control
- Workspace management
- API key management
- Usage analytics
- Admin dashboard

**Prerequisites:** v0.5 modern frontend completed

---

## Design Philosophy

### CLI First

ragged is designed with CLI as the **primary interface**:
- Full functionality available via command line
- Web UI provides visual convenience, not exclusive features
- Power users can script and automate via CLI
- CI/CD integration requires no graphical interface

### Progressive Enhancement

Both interfaces follow progressive enhancement:
- Core functionality first (v0.1-v0.2)
- Enhanced user experience (v0.3)
- Advanced features (v0.4)
- Production polish (v0.5-v1.0)

### Shared Backend

CLI and web UI share the **same ragged core**:
- Consistent behaviour across interfaces
- Same configuration system
- Same document processing pipeline
- Same RAG capabilities

**Backend Location:** `src/ragged/` (Python package)

**Interface Layers:**
- **CLI:** `src/ragged/cli.py` (Click-based)
- **Web UI:** `src/ragged/web_ui.py` (Gradio/FastAPI)

---

## Implementation Tracking

### Current Status (v0.2.2)

**CLI:**
- ✅ Basic commands (init, ingest, query, list, status)
- ⏳ 23 enhancements planned for v0.2.7-v0.4.0

**Web UI:**
- ✅ Basic Gradio interface (v0.2)
- ❌ API endpoints broken (critical bug)
- ⏳ Enhancements planned for v0.3-v1.0

### Roadmap Integration

**CLI Enhancements:**
- **v0.2.7** (11 enhancements) - See [v0.2.7 Roadmap](../process/roadmap/version/v0.2.7/README.md)
- **v0.3.0** (11 enhancements) - See [v0.3.0 Roadmap](../process/roadmap/version/v0.3.0/README.md)
- **v0.4.0** (plugin system) - See [v0.4.0 Roadmap](../process/roadmap/version/v0.4.0/README.md)

**Web UI Enhancements:**
- **v0.2.5** (bug fixes) - See [v0.2.5 Roadmap](../process/roadmap/version/v0.2.5/README.md)
- **v0.3.0** (multi-modal) - See [v0.3.0 Roadmap](../process/roadmap/version/v0.3.0/README.md)
- **v0.4.0** (advanced features) - See [v0.4.0 Roadmap](../process/roadmap/version/v0.4.0/README.md)

---

## Related Documentation

### Architecture
- [Architecture Overview](../architecture/README.md) - System architecture
- [Core Concepts](../core-concepts/README.md) - Fundamental concepts

### Requirements
- [User Stories](../requirements/user-stories.md) - User needs and workflows
- [User Personas](../../explanation/user-personas.md) - Who ragged serves

### Process
- [Roadmap Overview](../process/roadmap/README.md) - Development timeline
- [Methodology](../process/methodology/README.md) - Development approach

---

## Contributing

Contributions to UI design and implementation are welcome!

**For CLI enhancements:**
1. Review [CLI Enhancements Catalogue](./cli/enhancements.md)
2. Check roadmap for current version
3. See [Contributing Guide](../../contributing/README.md)

**For Web UI improvements:**
1. Review version-specific design documents
2. Ensure prerequisites are met
3. Test against current codebase
4. Submit PR with screenshots/demos

---

**Next Steps:**

1. **Users:** Try both CLI and web UI to find preferred workflow
2. **Contributors:** Pick an enhancement from the catalogue or roadmap
3. **Designers:** Propose UX improvements for future versions
4. **Developers:** Review technical architecture before implementing

---

**Questions?**

- **General UI Questions:** [GitHub Discussions](https://github.com/REPPL/ragged/discussions)
- **Bug Reports:** [GitHub Issues](https://github.com/REPPL/ragged/issues)
- **Feature Requests:** See roadmaps first, then open issue
