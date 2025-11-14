# ragged Documentation

**Status:** Early Development (v0.2.2)

**Last Updated:** 2025-11-13

**Documentation Version:** 3.0 (restructured for industry standards)

---

## Table of Contents

- [Welcome](#welcome)
- [Documentation Structure](#documentation-structure)
- [For Users: Diátaxis Framework](#for-users-diátaxis-framework)
  - [Tutorials - Learning by Doing](#tutorials---learning-by-doing)
  - [Guides - Solving Problems](#guides---solving-problems)
  - [Reference - Looking Up Details](#reference---looking-up-details)
  - [Explanation - Understanding Concepts](#explanation---understanding-concepts)
- [For Product & Planning](#for-product--planning)
  - [Vision - Long-Term Strategy](#vision---long-term-strategy)
  - [Requirements - User Needs](#requirements---user-needs)
- [For Technical Design](#for-technical-design)
  - [Design - Technical Architecture](#design---technical-architecture)
  - [ADR - Architecture Decision Records](#adr---architecture-decision-records)
  - [RFCs - Request for Comments](#rfcs---request-for-comments)
- [For Implementation Records](#for-implementation-records)
  - [Implementation - What Was Actually Built](#implementation---what-was-actually-built)
- [For Development Process](#for-development-process)
  - [Process - Development Transparency](#process---development-transparency)
- [For Research & Community](#for-research--community)
  - [Research - Academic Materials](#research---academic-materials)
  - [Contributing - Contribution Guidelines](#contributing---contribution-guidelines)
- [I Want To...](#i-want-to)
- [Current Project Status](#current-project-status)
- [Documentation Standards](#documentation-standards)
- [Project Principles](#project-principles)
- [Contributing to Documentation](#contributing-to-documentation)
- [External Resources](#external-resources)
- [Questions?](#questions)
- [License](#license)

---

## Welcome

This is the complete documentation for **ragged**, a privacy-first local RAG (Retrieval-Augmented Generation) system. The documentation serves multiple audiences:

- **End Users:** Learn to use ragged for document question-answering
- **Contributors:** Understand how to contribute code and documentation
- **Developers:** See how ragged is designed and built
- **Researchers:** Study AI-assisted development and RAG architecture

---

## Documentation Structure

ragged's documentation follows industry-standard patterns with some unique additions for development transparency and research.

### Quick Navigation Map

```
docs/
├── 📘 User Documentation (Diátaxis)
│   ├── tutorials/       → Learning-oriented lessons
│   ├── guides/          → Task-oriented how-tos
│   ├── reference/       → Information-oriented specs
│   └── explanation/     → Understanding-oriented concepts
│
├── 👨‍💻 Development Documentation
│   └── development/     → All developer-facing documentation
│       ├── design/      → Architecture and technical design
│       │   ├── vision/         → Long-term product strategy
│       │   ├── requirements/   → User stories and needs
│       │   ├── architecture/   → System architecture
│       │   ├── core-concepts/  → Foundational concepts
│       │   ├── technology-stack/ → Technology choices
│       │   └── versions/       → Version-specific designs
│       ├── rfcs/        → Request for Comments proposals
│       ├── adr/         → Architecture Decision Records
│       ├── implementation/ → What was actually built
│       └── process/     → How ragged is being built
│           ├── methodology/    → Development methods
│           ├── roadmap/        → Near-term plans
│           ├── devlog/         → Development narratives
│           ├── time-logs/      → Time tracking
│           └── templates/      → Document templates
│
├── 🔬 Research & Community
│   ├── research/        → Academic materials
│   └── contributing/    → Contribution guidelines
│
└── 📋 This file          → Navigation and overview
```

---

## For Users: [Diátaxis](https://diataxis.fr/) Framework

ragged uses the Diátaxis documentation system to help you learn and use the system effectively.

### [Tutorials](./tutorials/) - Learning by Doing

**Purpose:** Build skills through hands-on exercises

**Audience:** Beginners with no RAG experience

**Content:**
- Step-by-step practical lessons
- Safe-to-fail learning environment
- Conceptual explanations alongside practice

**Status:** Coming with v0.1 release

---

### [Guides](./guides/) - Solving Problems

**Purpose:** Accomplish specific goals

**Audience:** Users with basic familiarity

**Content:**
- Real-world problem solutions
- Step-by-step instructions
- Common tasks and workflows

**Status:** Coming with v0.1 release

**Available Now:**
- [Docker Setup Guide](./guides/docker-setup.md)

---

### [Reference](./reference/) - Looking Up Details

**Purpose:** Technical specifications and API documentation

**Audience:** Users needing precise information

**Content:**
- API documentation (auto-generated from code)
- Configuration options
- Terminology and definitions

**Status:** Reference materials will be auto-generated from code docstrings (v0.1+)

**Available Now:**
- [Terminology Glossary](./reference/terminology/)

---

### [Explanation](./explanation/) - Understanding Concepts

**Purpose:** Deepen your understanding of how and why ragged works

**Audience:** Users wanting conceptual knowledge

**Content:**
- RAG concepts and theory
- Design philosophy and trade-offs
- Why ragged works the way it does

**Available Now:**
- [Architecture Overview](./explanation/architecture-overview.md) - High-level system design
- [RAG Fundamentals](./explanation/rag-fundamentals.md) - Core RAG concepts
- [Privacy Design](./explanation/privacy-design.md) - Privacy-first architecture
- [Design Principles](./explanation/design-principles.md) - Core philosophy
- [User Personas](./explanation/user-personas.md) - Who ragged serves

---

## For Developers

All developer-facing documentation is now organised under [development/](./development/).

**Navigation:** See [Development Documentation README](./development/README.md) for complete navigation guide

### [Development Overview](./development/) - Complete Developer Documentation

**Purpose:** Central hub for all development-related documentation

**Structure:**
- **design/** - Architecture and planning (vision, requirements, technical design)
- **rfcs/** - Proposals for significant changes
- **adr/** - Architecture Decision Records
- **implementation/** - What was actually built
- **process/** - How it was built (methodology, roadmap, devlogs, time tracking)

**Quick Links:**
- [Product Vision](./development/design/vision/product-vision.md) - Goals and principles
- [Architecture Overview](./development/design/architecture/README.md) - System architecture
- [Roadmap](./development/process/roadmap/README.md) - Near-term plans and CLI enhancements
- [CLI Enhancements Catalogue](./development/design/core-concepts/cli-enhancements.md) - Complete CLI feature catalogue
- [ADRs](./development/adr/) - Key architectural decisions

**Audience:** Contributors, developers, technical stakeholders

---

## For Research & Community

### [Research](./research/) - Academic Materials

**Purpose:** Support academic reproducibility and evidence-based design

**Content:**
- [Research Overview](./research/README.md)
- [Background Materials](./research/background/) - RAG landscape, comparisons
- Methodology (coming)
- Experiments (coming)
- Benchmarks (coming)

**Audience:** Researchers, academics, evidence-based practitioners

---

### [Contributing](./contributing/) - Contribution Guidelines

**Purpose:** Help contributors participate in ragged development

**Content:**
- [Contributing Guide](./contributing/README.md)
- Development setup
- Code standards
- Review process
- AI assistance disclosure

**Status:** Contributions welcomed after v0.1 release

**Audience:** Contributors, developers

---

## I Want To...

**Learn how to use ragged**
→ Start with [Tutorials](./tutorials/) (coming with v0.1)
→ Or read [Architecture Overview](./explanation/architecture-overview.md) for concepts

**Solve a specific problem**
→ Check [Guides](./guides/) (coming with v0.1)

**Look up API or configuration details**
→ See [Reference](./reference/) (auto-generated from code with v0.1)

**Understand RAG concepts**
→ Read [Explanation](./explanation/) and [Core Concepts](./development/design/core-concepts/)

**Understand the architecture**
→ Read [Architecture Overview](./explanation/architecture-overview.md) (user-facing)
→ Then [Design Architecture](./development/design/architecture/) (technical details)

**Understand a specific decision**
→ Check [ADR](./adr/) for numbered architectural decisions
→ Or [Version Decisions](./process/devlog/version/) for narrative context

**See what's planned next**
→ Check [Process Roadmap](./process/roadmap/) for near-term plans
→ Or [Design Version Plans](./development/design/versions/) for long-term vision

**Contribute code or documentation**
→ See [Contributing Guide](./contributing/README.md)

**Study the development process**
→ Explore [Process Documentation](./process/)
→ Read [Time Logs](./process/time-logs/) for empirical data
→ Check [Development Logs](./process/devlog/) for narratives

**Research AI-assisted development**
→ Review [AI Assistance Guidelines](./process/methodology/ai-assistance.md)
→ Compare [Design Plans](./development/design/versions/) vs. [Actual Implementation](./implementation/)
→ Study [Time Logs](./process/time-logs/) for AI effectiveness data

**See research materials**
→ Browse [Research Documentation](./research/)

---

## Current Project Status

**Version:** v0.2.2 (Early Development)

**Date:** 2025-11-13

**What Exists:**
- ✅ Comprehensive technical design (v0.1 through v1.0)
- ✅ State-of-the-art RAG architecture (2025)
- ✅ Technology stack evaluations
- ✅ Core v0.1 implementation (basic RAG pipeline)
- ✅ Development process transparency framework
- ✅ Partial v0.2 implementation

**Current Focus:**
- 🔄 **v0.2 Development** - Document normalisation + enhanced retrieval + web UI

**Recent Updates:**
- Documentation restructured to industry standards (2025-11-13)
- ADR system implemented for architectural decisions
- Clear separation of design vs. implementation vs. process

---

## Documentation Standards

### Language

**British English** throughout all documentation:
- "organise" not "organize"
- "colour" not "color"
- "behaviour" not "behavior"

### Formatting

**Metadata formatting:**
```markdown
**Status:** Active

**Date:** 2025-11-13

**Owner:** Engineering
```

Each metadata field on its own line for readability.

**File naming:**
- Lowercase with hyphens: `architecture-overview.md`
- README.md exception: All caps (standard convention)
- Avoid capitals for normal files: `summary.md` not `summary.md`

### Version Control

- All documentation version-controlled in git
- Major milestones tagged (e.g., `v0.1-complete`)
- Compare plans ([design/](./development/design/)) against actuals ([implementation/](./implementation/))

### AI Transparency

ragged development uses AI tools (Claude Code) transparently:
- AI usage disclosed in commits and documentation
- Time tracking distinguishes AI-assisted vs. manual work
- All AI-generated code reviewed and understood by humans
- See [AI Assistance Guidelines](./process/methodology/ai-assistance.md)

---

## Project Principles

### 1. Privacy-First

All processing 100% local by default. No external APIs unless explicitly configured.

**See:** [ADR-0001: Local-Only Processing](./adr/0001-local-only-processing.md)

### 2. Learning-Focused

Documentation prioritises educational value. Explain "why", not just "what".

### 3. State-of-the-Art

Incorporate latest 2025 RAG research and best practices.

### 4. Modular Architecture

Pluggable components with clear interfaces. Easy to experiment and extend.

**See:** [Modularity](./development/design/core-concepts/modularity.md)

### 5. Progressive Enhancement

Build incrementally. Each version adds capabilities without breaking previous work.

### 6. Transparent Development

Document the actual development process, including AI assistance, for reproducibility.

**See:** [Process Documentation](./process/)

---

## Contributing to Documentation

Documentation contributions are welcome!

**Types of contributions:**
- Tutorials for new users
- How-to guides for specific tasks
- Explanations of RAG concepts
- Corrections and clarifications
- Examples and use cases

**Process:**
1. Review [Contributing Guide](./contributing/README.md)
2. Create an issue to discuss your contribution
3. Submit a pull request

**Note:** Documentation improvements welcome anytime! Code contributions welcome after v0.1.

---

## External Resources

### Community

- **GitHub Repository:** https://github.com/REPPL/ragged
- **Discussions:** https://github.com/REPPL/ragged/discussions
- **Issues:** https://github.com/REPPL/ragged/issues

### Related Documentation

- **Project README:** [`../README.md`](../README.md) - User-facing project introduction
- **Code Documentation:** Auto-generated from docstrings (coming with v0.1)

---

## Questions?

- **General Questions:** [GitHub Discussions](https://github.com/REPPL/ragged/discussions)
- **Documentation Issues:** [GitHub Issues](https://github.com/REPPL/ragged/issues)
- **Contributing:** See [Contributing Guide](./contributing/README.md)

---

## License

All documentation is licensed under **GPL-3.0**, same as the ragged project.

See [`../LICENSE`](../LICENSE) for full text.

---

**Next Steps:**

1. **New users:** Wait for v0.1 release, then start with [Tutorials](./tutorials/)
2. **Contributors:** Review [Design](./development/design/) and [Contributing Guide](./contributing/)
3. **Developers:** Explore [Process](./process/) and [Architecture](./development/design/architecture/)
4. **Researchers:** Check [Research](./research/) and [Time Tracking](./process/methodology/time-tracking.md)
