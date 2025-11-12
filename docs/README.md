# ragged Documentation

**Status**: Planning Phase - Comprehensive architecture and implementation plan complete
**Version**: v0.0 (pre-implementation)
**Last Updated**: 2025-11-09

---

## Welcome

This is the complete documentation for **ragged**, a privacy-first local RAG (Retrieval-Augmented Generation) system. The documentation serves multiple audiences and purposes:

- **End Users**: Learn to use ragged for document question-answering
- **Contributors**: Understand how to contribute code and documentation
- **Developers**: See how ragged is designed and built
- **Researchers**: Study AI-assisted development and RAG architecture

---

## Documentation Organization

ragged uses the **Diataxis framework** for user-facing documentation, plus additional sections for contributors, developers, and researchers.

### 📖 For Users (Diataxis Framework)

These sections help you **learn and use** ragged:

#### [**Tutorials**](./tutorials/) - Learning by Doing
*Learning-oriented - Build skills through hands-on exercises*

- For beginners with no RAG experience
- Step-by-step practical lessons
- Safe-to-fail learning environment

**Status**: Coming with v0.1 release

---

#### [**Guides**](./guides/) - Solving Problems
*Task-oriented - How to accomplish specific goals*

- For users with basic familiarity
- Solve real-world problems
- Step-by-step instructions for common tasks

**Status**: Coming with v0.1 release

---

#### [**Reference**](./reference/) - Looking Up Details
*Information-oriented - Technical specifications*

- API documentation
- Configuration options
- Terminology and definitions

**Status**: Reference materials will be auto-generated from code (v0.1+)

**Available Now**:
- [Terminology](./reference/terminology/) - RAG and ragged-specific terms

---

#### [**Explanation**](./explanation/) - Understanding Concepts
*Understanding-oriented - Deepen your knowledge*

- Why ragged works the way it does
- RAG concepts and theory
- Design philosophy and trade-offs

**Available Now**:
- [Architecture](./implementation/plan/architecture/) - System design principles
- [Design Principles](./explanation/design-principles/) - Core philosophy

**Also see**: Many explanatory documents in [Implementation Plan](./implementation/plan/core-concepts/)

---

### 🤝 For Contributors

#### [**Contributing Guide**](./contributing/)

- How to contribute to ragged (post-v0.1)
- Development setup instructions
- Code standards and review process
- AI assistance disclosure guidelines

**Status**: Pre-v0.1 - Contributions welcomed after v0.1 release

---

### 🔬 For Developers & Researchers

#### [**Development Process**](./development/) ⭐ NEW

*Transparency in AI-assisted software development*

**Purpose**: Document **how ragged is being built**, not just what it does.

**Contents**:
- **Daily Development Logs** (`devlog/`) - Chronicle of actual development
- **Architecture Decision Records** (`decisions/`) - Why we made specific choices
- **Time Tracking** (`time-logs/`) - Actual hours spent (not vague "weeks")
- **AI Assistance Documentation** - How AI tools are used transparently

**Why**: Supports reproducibility, transparency, research, and accountability.

**See**: [Development Documentation Index](./development/README.md)

---

#### [**Research Materials**](./research/)

*Academic and research-oriented documentation*

- Research methodology
- Background materials (RAG landscape, comparisons)
- Experimental results and benchmarks (coming in v0.2+)
- Citations and bibliography

**Purpose**: Support academic reproducibility and evidence-based design.

**See**: [Research Documentation Index](./research/README.md)

---

#### [**Implementation Plan**](./implementation/plan/) ⭐ COMPREHENSIVE

*Detailed version-by-version implementation roadmap*

The **complete technical plan** for building ragged from v0.1 (MVP) to v1.0 (production-ready).

**Key Documents**:
- [Implementation Plan Overview](./implementation/plan/README.md)
- [State-of-the-Art Architecture 2025](./implementation/plan/architecture/README.md)
- [Project Vision & Goals](./implementation/plan/PROJECT-VISION.md)
- [Development Guide](./implementation/plan/DEVELOPMENT-GUIDE.md)

**Version Plans**:
- [v0.1: MVP Foundation](./implementation/plan/versions/v0.1/)
- [v0.2: Document Normalization + Enhanced Retrieval](./implementation/plan/versions/v0.2/)
- [v0.3: Advanced Chunking](./implementation/plan/versions/v0.3/)
- [v0.4: Adaptive Systems](./implementation/plan/versions/v0.4/)
- [v0.5: Knowledge Graphs](./implementation/plan/versions/v0.5/)
- [v1.0: Production Ready](./implementation/plan/versions/v1.0/)

**Core Concepts**:
- [RAG Fundamentals](./implementation/plan/core-concepts/rag-fundamentals.md)
- [Document Normalization](./implementation/plan/core-concepts/document-normalization.md) ⭐ KEY FEATURE
- [Duplicate Detection](./implementation/plan/core-concepts/duplicate-detection.md)
- [Metadata Schema](./implementation/plan/core-concepts/metadata-schema.md)
- [Progressive Disclosure](./implementation/plan/core-concepts/progressive-disclosure.md)
- [Privacy Architecture](./implementation/plan/core-concepts/privacy-architecture.md)

**Technology Stack**:
- [Document Processing Tools](./implementation/plan/technology-stack/document-processing.md)
- [Web Frameworks](./implementation/plan/technology-stack/web-frameworks.md)
- [Embeddings](./implementation/plan/technology-stack/embeddings.md)
- [Vector Stores](./implementation/plan/technology-stack/vector-stores.md)
- [And more...](./implementation/plan/technology-stack/)

---

## Quick Navigation

### I Want to...

**Learn how to use ragged**
→ Start with [Tutorials](./tutorials/) (coming with v0.1)

**Solve a specific problem**
→ Check [Guides](./guides/) (coming with v0.1)

**Look up API details**
→ See [Reference](./reference/) (auto-generated from code)

**Understand RAG concepts**
→ Read [Explanation](./explanation/) and [Core Concepts](./implementation/plan/core-concepts/)

**Contribute to ragged**
→ See [Contributing Guide](./contributing/)

**Understand the development process**
→ Explore [Development Documentation](./development/)

**Review the technical architecture**
→ Read [Implementation Plan](./implementation/plan/README.md) and [Architecture 2025](./implementation/plan/architecture/README.md)

**Study AI-assisted development**
→ Check [Time Tracking](./development/methodology/time-tracking.md) and [Development Logs](./development/devlog/)

**See research materials**
→ Browse [Research Documentation](./research/)

---

## Current Project Status

**Phase**: Planning → Early Development

**What Exists**:
- ✅ Comprehensive implementation plan (v0.1 through v1.0)
- ✅ State-of-the-art RAG architecture design (2025)
- ✅ Technology stack evaluation and decisions
- ✅ Core concepts documentation
- ✅ Development process transparency framework

**What's Next**:
- 🔄 **v0.1 Implementation** (Starting soon - 2-3 weeks estimated)
  - Basic RAG pipeline
  - Simple CLI
  - ChromaDB + Ollama integration
  - PDF, TXT, MD, HTML support

**Timeline**:
- v0.1: 2-3 weeks (basic functionality)
- v0.2: 6-7 weeks (⭐ **document normalization** + enhanced retrieval + web UI)
- v0.3: 3-4 weeks (advanced chunking)
- v0.4: 4-5 weeks (adaptive systems)
- v0.5: 5-6 weeks (knowledge graphs)
- v1.0: 4-6 weeks (production ready)

**Note**: These are preliminary estimates. **Actual time tracking** will replace estimates with empirical data. See [Time Tracking Methodology](./development/methodology/time-tracking.md).

---

## Documentation Standards

### Language

**British English** throughout all documentation (organise, colour, behaviour).

### Formats

- **Markdown**: GitHub-flavored for all documents
- **Diagrams**: Mermaid for architecture, ASCII for simple flows
- **Code**: Python 3.10+ with type hints

### Version Control

- All documentation version-controlled in git
- Major milestones tagged (e.g., `v0.1-plan-complete`)
- Plans compared against actual implementation

### AI Transparency

ragged development uses AI tools (Claude Code, GitHub Copilot) transparently:
- AI usage disclosed in commits and documentation
- Time tracking distinguishes AI-assisted vs. manual work
- All AI-generated code reviewed and understood by humans

See [Development Process](./development/) for full transparency framework.

---

## Project Principles

### 1. Privacy-First
All processing 100% local by default. No external APIs unless explicitly configured.

### 2. Learning-Focused
Documentation prioritizes educational value. Explain "why", not just "what".

### 3. State-of-the-Art
Incorporate latest 2025 RAG research and best practices.

### 4. Modular Architecture
Pluggable components with clear interfaces. Easy to experiment and extend.

### 5. Progressive Enhancement
Build incrementally. Each version adds capabilities without breaking previous work.

### 6. Transparent Development
Document the actual development process, including AI assistance, for reproducibility.

---

## Contributing to Documentation

Documentation contributions are welcome!

**Types of contributions**:
- Tutorials for new users
- How-to guides for specific tasks
- Explanations of RAG concepts
- Corrections and clarifications
- Examples and use cases

**Process**:
1. Check [Contributing Guide](./contributing/README.md)
2. Create an issue to discuss your contribution
3. Submit a pull request

**Note**: Post-v0.1 for code contributions, but documentation improvements welcome anytime!

---

## External Resources

### Community

- **GitHub Repository**: https://github.com/REPPL/ragged
- **Discussions**: https://github.com/REPPL/ragged/discussions
- **Issues**: https://github.com/REPPL/ragged/issues

### Related Documentation

- **Project README**: [`../README.md`](../README.md) - User-facing project introduction
- **Code Documentation**: Auto-generated from docstrings (coming with v0.1)

---

## Documentation Roadmap

### v0.1 Release
- [ ] Tutorials for basic usage
- [ ] API reference (auto-generated)
- [ ] Installation and setup guide
- [ ] First time-tracked feature logs

### v0.2 Release
- [ ] Document normalization guides
- [ ] Web UI tutorials
- [ ] Advanced configuration reference
- [ ] Version time summary
- [ ] First benchmarks

### v0.3+ Releases
- [ ] Advanced chunking explanations
- [ ] Performance tuning guides
- [ ] Experimental results
- [ ] User studies (if conducted)

### v1.0 Release
- [ ] Complete user documentation
- [ ] Comprehensive API reference
- [ ] Production deployment guides
- [ ] Migration guides
- [ ] Full research documentation

---

## Migrated Content

**From `project-setup/` (reorganized 2025-11-09)**:

Content has been reorganized into the new Diataxis-based structure:

- `architecture/` → [`implementation/plan/architecture/`](./implementation/plan/architecture/)
- `background/` → [`research/background/`](./research/background/)
- `decisions/` → [`development/decisions/`](./development/decisions/)
- `design-principles/` → [`explanation/design-principles/`](./explanation/design-principles/)
- `terminology/` → [`reference/terminology/`](./reference/terminology/)

---

## Questions?

- **General Questions**: [GitHub Discussions](https://github.com/REPPL/ragged/discussions)
- **Documentation Issues**: [GitHub Issues](https://github.com/REPPL/ragged/issues)
- **Contributing**: See [Contributing Guide](./contributing/README.md)

---

## License

All documentation is licensed under **GPL-3.0**, same as the ragged project.

See [`../LICENSE`](../LICENSE) for full text.

---

**Next Steps**:
1. **New users**: Wait for v0.1 release, then start with [Tutorials](./tutorials/)
2. **Contributors**: Review [Implementation Plan](./implementation/plan/) and [Contributing Guide](./contributing/)
3. **Developers**: Explore [Development Process](./development/) and [Architecture](./implementation/plan/architecture/README.md)
4. **Researchers**: Check [Research Materials](./research/) and [Time Tracking](./development/methodology/time-tracking.md)

---

**Status**: Planning complete. Ready to begin v0.1 implementation.
**Last Updated**: 2025-11-09
**Documentation Version**: 2.0 (reorganized with Diataxis framework + transparency layers)
