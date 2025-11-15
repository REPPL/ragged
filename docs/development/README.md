# Development Documentation

**Purpose:** All documentation for developers working on ragged

**Last Updated:** 2025-11-14

---

## Table of Contents

- [Structure Overview](#structure-overview)
- [Navigation Guide](#navigation-guide)
- [Document Lifecycle](#document-lifecycle)
- [For Contributors](#for-contributors)

---

## Structure Overview

This directory contains all development-related documentation, organised by purpose:

```
development/
├── vision/           → Long-term product strategy
├── requirements/     → User needs and user stories
├── architecture/     → System architecture design
├── core-concepts/    → Foundational technical concepts
├── technology-stack/ → Technology evaluations
├── UI/               → User interface design (CLI & web)
├── versions/         → Version-specific design plans
├── references/       → Research papers and resources
├── rfcs/             → Proposals for significant changes
├── adr/              → Architecture Decision Records
├── implementation/   → What was actually built
└── process/          → How it was built (transparency)
```

---

## Planning & Design Documentation

### [vision/](./vision/) - Product Strategy

**Purpose:** Long-term product goals and principles

**Key documents:**
- [Product Vision](./vision/product-vision.md) - Goals, principles, success criteria

### [requirements/](./requirements/) - User Needs

**Purpose:** User stories and functional requirements

**Contains:**
- User stories organised by feature area
- Persona definitions

### [architecture/](./architecture/) - System Design

**Purpose:** State-of-the-art RAG architecture and system design

**Key documents:**
- [Architecture README](./architecture/README.md) - Complete architecture overview
- [Storage Model](./architecture/storage-model.md)
- [Configuration System](./architecture/configuration-system.md)

### [core-concepts/](./core-concepts/) - Foundational Concepts

**Purpose:** Core technical concepts and patterns

**Key documents:**
- [RAG Fundamentals](./core-concepts/rag-fundamentals.md) - Core RAG concepts
- [Privacy Architecture](./core-concepts/privacy-architecture.md) - Privacy-first design
- [Modularity](./core-concepts/modularity.md) - Plugin architecture

### [technology-stack/](./technology-stack/) - Technology Choices

**Purpose:** Technology evaluations and selections

**Contains:**
- Embedding models comparison
- Vector store evaluations
- LLM backend options
- Chunking strategies

### [UI/](./UI/) - User Interface Design

**Purpose:** Design documentation for all user interfaces

**Contains:**
- **[cli/](./UI/cli/)** - CLI enhancements catalogue (23 features across v0.2.7-v0.4.0)
- **[web/](./UI/web/)** - Web UI evolution (v0.2-v1.0 designs)

**Key documents:**
- [CLI Enhancements](./UI/cli/enhancements.md) - Complete CLI feature specifications
- [UI README](./UI/README.md) - Navigation and overview

### [versions/](./versions/) - Version Plans

**Purpose:** Version-specific high-level design plans

**Contains:**
- v0.1-v1.0 version overviews
- Feature roadmaps per version
- Long-term vision

### [references/](./references/) - Research Materials

**Purpose:** Academic papers, research, and external resources

**Contains:**
- Research papers on RAG, retrieval, and LLMs
- Web UI research and best practices
- Curated reference materials

---

## [rfcs/](./rfcs/) - Request for Comments

**Purpose:** Propose and discuss significant changes **before** design phase

**Status:** Empty (template ready)

**Process:**
1. Draft RFC with problem statement and proposed solution
2. Submit for community discussion
3. Iterate based on feedback
4. Accept/reject decision
5. If accepted → Create design docs
6. After implementation → Create ADR

**When to use:**
- Proposing breaking changes
- Major architectural shifts
- Controversial features
- Community input needed

**Format:** Numbered RFCs (0001-title.md, 0002-title.md)

---

## [adr/](./adr/) - Architecture Decision Records

**Purpose:** Document **why** specific architectural choices were made

**Status:** Active (4 ADRs documented)

**Contains:**
- [ADR-0001: Local-Only Processing](./adr/0001-local-only-processing.md)
- [ADR-0002: Pydantic for Configuration](./adr/0002-pydantic-for-configuration.md)
- [ADR-0003: ChromaDB for Vector Storage](./adr/0003-chromadb-for-vector-storage.md)
- [ADR-0004: Factory Pattern for Embedders](./adr/0004-factory-pattern-for-embedders.md)

**When to use:**
- Understanding why a decision was made
- Evaluating whether to change a decision
- Learning from past trade-offs
- Onboarding new contributors

**Format:** Numbered ADRs with standard structure (Status, Context, Decision, Consequences)

**Standard:** [Michael Nygard's ADR format](https://cognitect.com/blog/2011/11/15/documenting-architecture-decisions)

---

## [implementation/](./implementation/) - What Was Actually Built

**Purpose:** Document **actual** implementation vs. design plans

**Status:** Active (v0.1 complete, v0.2 in progress)

**Contains:**
- **[v0.1/](./implementation/v0.1/)** - MVP implementation records
- **[v0.2/](./implementation/v0.2/)** - Enhanced retrieval implementation

**When to use:**
- Understanding what was actually built (vs. what was planned)
- Identifying deviations from design
- Reviewing implementation outcomes
- Planning future versions based on learnings

**Key documents:**
- [v0.1 Summary](./implementation/v0.1/summary.md) - Results and retrospective
- [v0.1 Implementation Notes](./implementation/v0.1/implementation-notes.md) - Technical details
- [v0.1 Testing Results](./implementation/v0.1/testing.md) - Test coverage and quality

**Distinction:**
- **vision/architecture/versions/** = What we **planned** to build
- **implementation/** = What we **actually built**
- **process/** = **How** we built it (narrative)

---

## [process/](./process/) - How It Was Built

**Purpose:** Development transparency layer (unique to ragged)

**Status:** Active and evolving

**Contains:**
- **[methodology/](./process/methodology/)** - How we develop (AI assistance, time tracking)
- **[roadmap/](./process/roadmap/)** - Near-term detailed plans (next 2-3 versions)
- **[devlog/](./process/devlog/)** - Daily and version-based development narratives
- **[time-logs/](./process/time-logs/)** - Actual hours spent (empirical data)
- **[templates/](./process/templates/)** - Templates for various document types

**When to use:**
- Studying AI-assisted development
- Understanding the development journey
- Tracking time estimates vs. actuals
- Learning from development process
- Contributing to ragged

**Why this exists:**
- **Transparency:** Full disclosure of AI-assisted development
- **Research:** Support academic reproducibility
- **Learning:** Help others understand the journey
- **Accountability:** Track estimates vs. actuals

**Key documents:**
- [AI Assistance Guidelines](./process/methodology/ai-assistance.md)
- [Time Tracking Methodology](./process/methodology/time-tracking.md)
- [Roadmap Overview](./process/roadmap/README.md)
- [v0.1 Time Log](./process/time-logs/version/v0.1/v0.1.0-time-log.md)

---

## Navigation Guide

### I Want To...

**Plan a new feature**
1. Start with [vision/](./vision/) to ensure alignment
2. Create RFC in [rfcs/](./rfcs/) if significant
3. Design in [versions/](./versions/) or [architecture/](./architecture/)
4. Document decision in [adr/](./adr/)

**Understand a past decision**
1. Check [adr/](./adr/) for architectural decisions
2. Or [process/devlog/version/](./process/devlog/version/) for narrative context
3. Or [architecture/](./architecture/) for original planning

**See what's planned next**
1. Check [process/roadmap/](./process/roadmap/) for near-term plans
2. Or [versions/](./versions/) for long-term vision

**Study how ragged is built**
1. Read [process/README.md](./process/README.md) for overview
2. Explore [process/devlog/](./process/devlog/) for narratives
3. Study [process/time-logs/](./process/time-logs/) for empirical data

**Implement a feature**
1. Follow design in [versions/](./versions/) or [architecture/](./architecture/)
2. Track work in [process/devlog/](./process/devlog/)
3. Document actual in [implementation/](./implementation/)
4. Create ADR in [adr/](./adr/) for key decisions

**Research AI-assisted development**
1. Read [process/methodology/](./process/methodology/)
2. Compare [versions/](./versions/) vs. [implementation/](./implementation/)
3. Study [process/time-logs/](./process/time-logs/) for AI effectiveness

---

## Document Lifecycle

### 1. Proposal Phase
**Location:** [rfcs/](./rfcs/)
**Purpose:** Discuss significant changes
**Outcome:** Accept or reject

### 2. Planning Phase
**Location:** [vision/](./vision/), [architecture/](./architecture/), [versions/](./versions/)
**Purpose:** Detail what to build
**Output:** Architecture, specs, plans

### 3. Decision Phase
**Location:** [adr/](./adr/)
**Purpose:** Document why choices made
**Output:** Numbered ADRs

### 4. Implementation Phase
**Location:** [process/devlog/](./process/devlog/)
**Purpose:** Chronicle the build
**Output:** Daily logs, narratives, time tracking

### 5. Retrospective Phase
**Location:** [implementation/](./implementation/)
**Purpose:** Document what was built
**Output:** Summaries, comparisons to design

---

## For Contributors

### Getting Started

1. **Read** [vision/product-vision.md](./vision/product-vision.md) - Understand goals
2. **Review** [process/roadmap/](./process/roadmap/) - See what's planned
3. **Study** [adr/](./adr/) - Understand key decisions
4. **Follow** [versions/](./versions/) or [UI/](./UI/) - Implementation guides
5. **Document** [process/devlog/](./process/devlog/) - Share your journey

### Contributing

**For code:**
- Follow design in [architecture/](./architecture/) and [versions/](./versions/)
- Document decisions in [adr/](./adr/)
- Track time in [process/time-logs/](./process/time-logs/)
- Write devlog in [process/devlog/](./process/devlog/)

**For documentation:**
- See [../contributing/README.md](../contributing/README.md)
- Use templates in [process/templates/](./process/templates/)
- Maintain British English
- Cross-reference appropriately

### Standards

**Language:** British English (organise, colour, behaviour)

**Formatting:**
- Metadata on separate lines with line breaks
- Lowercase file names with hyphens
- README.md exception (standard convention)

**Version Control:**
- All docs version-controlled
- Git history preserved
- Meaningful commit messages

**AI Transparency:**
- Disclose AI assistance
- Document in methodology
- Track in time logs

---

## Questions?

- **General questions:** [GitHub Discussions](https://github.com/REPPL/ragged/discussions)
- **Documentation issues:** [GitHub Issues](https://github.com/REPPL/ragged/issues)
- **Contributing:** See [../contributing/README.md](../contributing/README.md)

---

**Last Updated:** 2025-11-14
**Maintained By:** ragged development team
**License:** GPL-3.0 (same as project)
