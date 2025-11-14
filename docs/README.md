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
│   ├── tutorials/     → Learning-oriented lessons
│   ├── guides/        → Task-oriented how-tos
│   ├── reference/     → Information-oriented specs
│   └── explanation/   → Understanding-oriented concepts
│
├── 🎯 Product & Planning
│   ├── vision/        → Long-term product strategy
│   └── requirements/  → User stories and needs
│
├── 🏗️ Technical Design
│   ├── design/        → Architecture and technical design
│   ├── adr/           → Architecture Decision Records
│   └── rfcs/          → Request for Comments proposals
│
├── ⚙️ Implementation Records
│   └── implementation/ → What was actually built
│
├── 📊 Development Process (Unique to ragged)
│   └── process/       → How ragged is being built
│
├── 🔬 Research & Community
│   ├── research/      → Academic materials
│   └── contributing/  → Contribution guidelines
│
└── 📋 This file         → Navigation and overview
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

## For Product & Planning

### [Vision](./vision/) - Long-Term Strategy

**Purpose:** Define what ragged will become

**Content:**
- [Product Vision](./vision/product-vision.md) - Goals, principles, success criteria

**Audience:** Product stakeholders, contributors, researchers

---

### [Requirements](./requirements/) - User Needs

**Purpose:** Define what users need from ragged

**Content:**
- [User Stories](./requirements/user-stories/) - Feature requirements by persona

**Audience:** Product and engineering teams

---

## For Technical Design

### [Design](./development/design/) - Technical Architecture

**Purpose:** Design decisions **before** implementation

**Content:**
- [Design Overview](./development/design/README.md) - Complete design documentation
- [Architecture](./development/design/architecture/) - System architecture design
- [Core Concepts](./development/design/core-concepts/) - Foundational technical concepts
- [Technology Stack](./development/design/technology-stack/) - Technology evaluations
- [Version Plans](./development/design/versions/) - Version-specific designs (v0.1-v1.0)
- [Development Guide](./development/design/DEVELOPMENT-GUIDE.md) - How to use the design docs

**Key Documents:**
- [Architecture README](./development/design/architecture/README.md) - State-of-the-art RAG architecture
- [RAG Fundamentals](./development/design/core-concepts/rag-fundamentals.md) - RAG theory
- [Privacy Architecture](./development/design/core-concepts/privacy-architecture.md) - Privacy-first design
- [Modularity](./development/design/core-concepts/modularity.md) - Plugin architecture

**Audience:** Engineering team, technical contributors

---

### [ADR](./adr/) - Architecture Decision Records

**Purpose:** Document **why** specific architectural choices were made

**Format:** Numbered ADRs (0001-decision-name.md)

**Available ADRs:**
- [ADR-0001: Local-Only Processing](./adr/0001-local-only-processing.md) - Privacy-first principle
- [ADR-0002: Pydantic for Configuration](./adr/0002-pydantic-for-configuration.md) - Data validation
- [ADR-0003: ChromaDB for Vector Storage](./adr/0003-chromadb-for-vector-storage.md) - Vector database choice
- [ADR-0004: Factory Pattern for Embedders](./adr/0004-factory-pattern-for-embedders.md) - Design pattern

**Audience:** Engineering team, technical contributors

**Standard:** Follows [Michael Nygard's ADR format](https://cognitect.com/blog/2011/11/15/documenting-architecture-decisions)

---

### [RFCs](./rfcs/) - Request for Comments

**Purpose:** Propose and discuss significant changes

**Content:**
- [RFC README](./rfcs/README.md) - RFC process and template

**Status:** Empty (placeholder for future proposals)

**Audience:** Engineering team, contributors

---

## For Implementation Records

### [Implementation](./implementation/) - What Was Actually Built

**Purpose:** Document **actual** implementation vs. design

**Content:**
- [v0.1 Implementation](./implementation/v0.1/) - What was actually built in v0.1
- [v0.2 Implementation](./implementation/v0.2/) - What was actually built in v0.2

**Key Documents:**
- [v0.1 Summary](./implementation/v0.1/summary.md) - Results and outcomes
- [v0.1 Implementation Notes](./implementation/v0.1/implementation-notes.md) - Technical details
- [v0.1 Testing Results](./implementation/v0.1/testing.md) - Test coverage and quality

**Distinction:**
- **design/** = What we **planned** to build
- **implementation/** = What we **actually built**
- **process/** = **How** we built it (narrative)

**Audience:** Engineering team, researchers, future maintainers

---

## For Development Process

### [Process](./process/) - Development Transparency

**Purpose:** Document **how ragged is being built** with full transparency

**Unique to ragged:** This structure is a novel contribution to open-source practices, supporting AI-assisted development transparency and research reproducibility.

**Content:**
- [Process Overview](./process/README.md) - Why this structure exists
- [Methodology](./process/methodology/) - How we develop (AI assistance, time tracking)
- [Roadmap](./process/roadmap/) - Near-term detailed plans (next 2-3 versions)
- [Development Logs](./process/devlog/) - Daily and version-based narratives
- [Time Logs](./process/time-logs/) - Actual hours spent (empirical data)
- [Templates](./process/templates/) - Templates for various documents

**Key Documents:**
- [AI Assistance Guidelines](./process/methodology/ai-assistance.md) - How we use AI transparently
- [Time Tracking Methodology](./process/methodology/time-tracking.md) - How we track time
- [Daily Devlogs](./process/devlog/daily/) - Day-by-day development chronicle
- [Version Devlogs](./process/devlog/version/) - Version-specific narratives

**Why this exists:**
- **Transparency:** Full disclosure of AI-assisted development
- **Research:** Support academic reproducibility
- **Learning:** Help others understand the development journey
- **Accountability:** Track estimates vs. actuals

**Audience:** Researchers, contributors, future developers

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
