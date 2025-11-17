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
│       ├── planning/       → Future design (what to build)
│       │   ├── vision/         → Long-term product strategy
│       │   ├── requirements/   → User stories and needs
│       │   ├── architecture/   → System architecture
│       │   ├── core-concepts/  → Foundational concepts
│       │   ├── technologies/   → Technology choices
│       │   ├── interfaces/     → User interface design (CLI & web)
│       │   ├── version/       → Version-specific designs
│       │   └── references/     → Research papers and resources
│       ├── decisions/      → Rationale (why we chose)
│       │   ├── adrs/           → Architecture Decision Records
│       │   └── rfcs/           → Request for Comments proposals
│       ├── roadmap/       → Timelines (when to build)
│       │   ├── features/       → Feature roadmaps
│       │   └── version/        → Version roadmaps
│       ├── implementation/ → Past reality (what was built)
│       │   └── version/       → Implementation by version
│       └── process/        → Methodology (how we built)
│           ├── methodology/    → Development methods
│           ├── devlogs/        → Development narratives
│           ├── time-logs/      → Time tracking
│           ├── testing/        → Testing documentation
│           └── templates/      → Document templates
│
├── 🔬 Research & Community
│   └── research/        → Academic materials
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
- [User Personas](./explanation/personas-explained.md) - Who ragged serves
- [Versioning Strategy](./explanation/versioning-strategy.md) - Version philosophy
- [Progressive Disclosure](./explanation/progressive-disclosure-explained.md) - UX approach

---

## For Developers

All developer-facing documentation is now organised under [development/](./development/).

**Navigation:** See [Development Documentation README](./development/README.md) for complete navigation guide

### [Development Overview](./development/) - Complete Developer Documentation

**Purpose:** Central hub for all development-related documentation

**Structure:**
- **planning/** - Future design documentation (what to build)
  - vision/, requirements/, architecture/, core-concepts/, technologies/, interfaces/, version/, references/
- **decisions/** - Decision rationale (why we chose)
  - adrs/ (Architecture Decision Records), rfcs/ (Request for Comments)
- **roadmap/** - Development timelines (when to build)
  - features/, version/ (with current symlink → v0.3.0)
- **implementation/** - Implementation records (what was built)
  - version/ (v0.1/, v0.2/)
- **process/** - Development methodology (how we built)
  - methodology/, devlogs/, time-logs/, testing/, templates/

**Quick Links:**
- [Product Vision](./development/planning/vision/product-vision.md) - Goals and principles
- [Architecture Overview](./development/planning/architecture/README.md) - System architecture
- [Roadmaps](./development/roadmap/README.md) - Version roadmaps and timelines
- [Current Roadmap](./development/roadmap/version/current/) - Active development plan (v0.3.0)
- [CLI Enhancements Catalogue](./development/planning/interfaces/cli/enhancements.md) - Complete CLI feature catalogue
- [Web UI Design](./development/planning/interfaces/web/) - Web interface evolution
- [ADRs](./development/decisions/adrs/) - Key architectural decisions

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

### [Contributing](../CONTRIBUTING.md) - Contribution Guidelines

**Purpose:** Help contributors participate in ragged development

**Content:**
- [Contributing Guide](../CONTRIBUTING.md)
- Development setup
- Code standards
- Review process
- AI assistance disclosure

**Status:** Contributions welcomed (v0.2.2)

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
→ Read [Explanation](./explanation/) and [Core Concepts](./development/planning/core-concepts/)

**Understand the architecture**
→ Read [Architecture Overview](./explanation/architecture-overview.md) (user-facing)
→ Then [Architecture Documentation](./development/planning/architecture/) (technical details)

**Understand a specific decision**
→ Check [ADRs](./development/decisions/adrs/) for numbered architectural decisions
→ Or [Version Devlogs](./development/process/devlogs/version/) for narrative context

**See what's planned next**
→ Check [Roadmaps](./development/roadmap/) for version plans and timelines
→ Or [Current Roadmap](./development/roadmap/version/current/) for active development (v0.3.0)
→ Or [Version Design Plans](./development/planning/version/) for detailed feature specifications

**Contribute code or documentation**
→ See [Contributing Guide](../CONTRIBUTING.md)

**Study the development process**
→ Explore [Process Documentation](./development/process/)
→ Read [Time Logs](./development/process/time-logs/) for empirical data
→ Check [Development Logs](./development/process/devlogs/) for narratives

**Research AI-assisted development**
→ Review [AI Assistance Guidelines](./development/process/methodology/ai-assistance.md)
→ Compare [Design Plans](./development/planning/version/) vs. [Actual Implementation](./development/implementation/)
→ Study [Time Logs](./development/process/time-logs/) for AI effectiveness data

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

### Status Indicators

All documentation uses consistent status indicators to show implementation state:

- ✅ **Implemented** - Feature is complete and available in current version
- 🚧 **In Progress** - Feature is being actively developed in current version
- 📋 **Planned** - Feature is designed and scheduled for a future version
- 🔬 **Research** - Feature is in exploratory/experimental phase
- ⚠️ **Deprecated** - Feature is legacy and will be removed in future version
- 🔄 **Current Focus** - Highlighted area of active development

**Usage Examples:**
```markdown
## Features

- ✅ Basic RAG pipeline (v0.1)
- ✅ Web UI with Gradio (v0.2)
- 🚧 Document normalisation (v0.2 - in progress)
- 📋 Personal memory system (v0.3 - planned)
- 🔬 Self-RAG evaluation (v0.4 - research)
```

When documenting planned features, always indicate which version they target.

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
- Compare plans ([planning/version/](./development/planning/version/)) against actuals ([implementation/](./development/implementation/))

### AI Transparency

ragged development uses AI tools (Claude Code) transparently:
- AI usage disclosed in commits and documentation
- Time tracking distinguishes AI-assisted vs. manual work
- All AI-generated code reviewed and understood by humans
- See [AI Assistance Guidelines](./development/process/methodology/ai-assistance.md)

---

## Project Principles

### 1. Privacy-First

All processing 100% local by default. No external APIs unless explicitly configured.

**See:** [ADR-0001: Local-Only Processing](./development/decisions/adrs/0001-local-only-processing.md)

### 2. Learning-Focused

Documentation prioritises educational value. Explain "why", not just "what".

### 3. State-of-the-Art

Incorporate latest 2025 RAG research and best practices.

### 4. Modular Architecture

Pluggable components with clear interfaces. Easy to experiment and extend.

**See:** [Modularity](./development/planning/core-concepts/modularity.md)

### 5. Progressive Enhancement

Build incrementally. Each version adds capabilities without breaking previous work.

### 6. Transparent Development

Document the actual development process, including AI assistance, for reproducibility.

**See:** [Process Documentation](./development/process/)

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
1. Review [Contributing Guide](../CONTRIBUTING.md)
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
- **Contributing:** See [Contributing Guide](../CONTRIBUTING.md)

---

## License

All documentation is licensed under **GPL-3.0**, same as the ragged project.

See [`../LICENSE`](../LICENSE) for full text.

---

**Next Steps:**

1. **New users:** Wait for v0.1 release, then start with [Tutorials](./tutorials/)
2. **Contributors:** Review [Architecture](./development/planning/architecture/) and [Contributing Guide](../CONTRIBUTING.md)
3. **Developers:** Explore [Process](./development/process/) and [Version Plans](./development/planning/version/)
4. **Researchers:** Check [Research](./research/) and [Time Tracking](./development/process/methodology/time-tracking.md)
