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
├── planning/         → All design and planning documents
│   ├── vision/       → Long-term product strategy
│   ├── requirements/ → User needs and user stories
│   ├── architecture/ → System architecture design
│   ├── core-concepts/→ Foundational technical concepts
│   ├── interfaces/   → User interface design (CLI & web)
│   ├── version/      → Version-specific design plans
│   ├── technologies/ → Technology evaluations
│   └── references/   → Research papers and resources
├── decisions/        → Decision records (grouped)
│   ├── adrs/        → Architecture Decision Records
│   └── rfcs/        → Request for Comments
├── roadmap/          → Development timelines and feature plans
├── implementation/   → What was actually built
└── process/          → How it was built (transparency)
```

---

## Single Source of Truth Principles

**Core Rule:** Each piece of information exists in exactly one canonical location.

### Directory Purposes

| Directory | Purpose | Timeline | Audience | Examples |
|-----------|---------|----------|----------|----------|
| **planning/** | What to build & why | Future | Designers, architects | Design goals, architecture, requirements |
| **roadmap/** | How & when to build | Future | Developers, managers | Feature specs, effort estimates, dependencies |
| **implementation/** | What was built | Past | All stakeholders | Technical records, test results, release notes |
| **process/** | How it was built | Past | Researchers, learners | Development narratives, time logs, methodology |

### Decision Tree: Where Does This Documentation Belong?

```
Is this about a completed version?
├─ YES: Is it technical implementation details?
│  ├─ YES → implementation/version/vX.X/
│  └─ NO: Is it development narrative/story?
│     └─ YES → process/devlogs/version/vX.X/
│
└─ NO: Is this about a future version?
   ├─ Is it high-level design goals (1-2 pages)?
   │  └─ YES → planning/version/vX.X/
   │
   └─ Is it detailed implementation plans (multi-page)?
      └─ YES → roadmap/version/vX.X.X/
```

### Specific Guidelines

#### planning/version/ vs roadmap/version/

**Use planning/version/** when documenting:
- High-level design goals (1-2 pages)
- Problem statements
- Solution approaches
- Expected impacts
- Success criteria

**Use roadmap/version/** when documenting:
- Detailed feature specifications
- Effort estimates (hours)
- Dependencies and prerequisites
- Implementation order
- Technical implementation details

**Example:**
- `planning/version/v0.3/README.md` - "What is v0.3 trying to achieve?"
- `roadmap/version/v0.3.0/README.md` - "How will we build v0.3.0, step by step?"

#### implementation/ vs process/devlogs/

**Use implementation/version/** for:
- Technical implementation records (canonical)
- Release notes
- Test results
- API documentation
- Final summaries

**Use process/devlogs/version/** for:
- Development narratives
- Daily logs
- Decision timelines
- Lessons learned
- Process observations

**Example:**
- `implementation/version/v0.1/implementation-notes.md` - Technical specs of what was built
- `process/devlogs/version/v0.1/daily-log.md` - Story of how it was built

### Exceptions to Single Source of Truth

**Different audiences may require adapted content:**
- User documentation (docs/tutorials/) vs developer documentation (docs/development/)
- High-level overview (README.md) vs detailed specs (architecture/)
- Public changelog (CHANGELOG.md) vs implementation records (implementation/)

**Rule:** Adaptation for audience is acceptable; duplication of technical details is not.

---

## Planning & Design Documentation

All design and planning documents are now organised under `planning/` for clarity:

### [planning/vision/](./planning/vision/) - Product Strategy

**Purpose:** Long-term product goals and principles

**Key documents:**
- [Product Vision](./planning/vision/product-vision.md) - Goals, principles, success criteria

### [planning/requirements/](./planning/requirements/) - User Needs

**Purpose:** User stories and functional requirements

**Contains:**
- User stories organised by feature area
- Persona definitions

### [planning/architecture/](./planning/architecture/) - System Design

**Purpose:** State-of-the-art RAG architecture and system design

**Key documents:**
- [Architecture README](./planning/architecture/README.md) - Complete architecture overview
- [Storage Model](./planning/architecture/storage-model.md)
- [Configuration System](./planning/architecture/configuration-system.md)

### [planning/core-concepts/](./planning/core-concepts/) - Foundational Concepts

**Purpose:** Core technical concepts and patterns

**Key documents:**
- [RAG Fundamentals](./planning/core-concepts/rag-fundamentals.md) - Core RAG concepts
- [Privacy Architecture](./planning/core-concepts/privacy-architecture.md) - Privacy-first design
- [Modularity](./planning/core-concepts/modularity.md) - Plugin architecture

### [planning/technologies/](./planning/technologies/) - Technology Choices

**Purpose:** Technology evaluations and selections

**Contains:**
- Embedding models comparison
- Vector store evaluations
- LLM backend options
- Chunking strategies

### [planning/interfaces/](./planning/interfaces/) - User Interface Design

**Purpose:** Design documentation for all user interfaces

**Contains:**
- **[cli/](./planning/interfaces/cli/)** - CLI enhancements catalogue
- **[web/](./planning/interfaces/web/)** - Web UI evolution (v0.2-v1.0 designs)

**Key documents:**
- [CLI Enhancements](./planning/interfaces/cli/enhancements.md) - Complete CLI feature specifications
- [Interfaces README](./planning/interfaces/README.md) - Navigation and overview

### [planning/version/](./planning/version/) - Version Plans

**Purpose:** Version-specific high-level design plans

**Contains:**
- v0.1-v1.0 version overviews
- Feature roadmaps per version
- Long-term vision

### [planning/references/](./planning/references/) - Research Materials

**Purpose:** Academic papers, research, and external resources

**Contains:**
- Research papers on RAG, retrieval, and LLMs
- Web UI research and best practices
- Curated reference materials

---

## [decisions/](./decisions/) - Decision Records

All decision documentation is now grouped under `decisions/` for easier navigation.

### [decisions/rfcs/](./decisions/rfcs/) - Request for Comments

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

### [decisions/adrs/](./decisions/adrs/) - Architecture Decision Records

**Purpose:** Document **why** specific architectural choices were made

**Status:** Active (14+ ADRs documented)

**Contains:**
- [ADR-0001: Local-Only Processing](./decisions/adrs/0001-local-only-processing.md)
- [ADR-0002: Pydantic for Configuration](./decisions/adrs/0002-pydantic-for-configuration.md)
- [ADR-0003: ChromaDB for Vector Storage](./decisions/adrs/0003-chromadb-for-vector-storage.md)
- [ADR-0004: Factory Pattern for Embedders](./decisions/adrs/0004-factory-pattern-for-embedders.md)
- And more (see [ADRs README](./decisions/adrs/README.md))

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
- **[version/v0.1/](./implementation/version/v0.1/)** - MVP implementation records
- **[version/v0.2/](./implementation/version/v0.2/)** - Enhanced retrieval implementation

**When to use:**
- Understanding what was actually built (vs. what was planned)
- Identifying deviations from design
- Reviewing implementation outcomes
- Planning future versions based on learnings

**Key documents:**
- [v0.1 Summary](./implementation/version/v0.1/summary.md) - Results and retrospective
- [v0.1 Implementation Notes](./implementation/version/v0.1/implementation-notes.md) - Technical details
- [v0.1 Testing Results](./implementation/version/v0.1/testing.md) - Test coverage and quality

**Distinction:**
- **planning/** = What we **planned** to build
- **implementation/** = What we **actually built**
- **process/** = **How** we built it (narrative)

---

## [roadmap/](./roadmap/) - Development Timelines

**Purpose:** Version roadmaps and feature planning

**Status:** Active (v0.2-v0.7 planned)

**Contains:**
- **[version/](./roadmap/version/)** - Version-specific roadmaps (v0.2.3-v0.7.0)
- **[features/](./roadmap/features/)** - Cross-version feature roadmaps

**Key documents:**
- [Roadmap Overview](./roadmap/README.md)
- [All Versions Overview](./roadmap/version/README.md)

---

## [process/](./process/) - How It Was Built

**Purpose:** Development transparency layer (unique to ragged)

**Status:** Active and evolving

**Contains:**
- **[methodology/](./process/methodology/)** - How we develop (AI assistance, time tracking)
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
- [v0.1 Time Log](./process/time-logs/version/v0.1/v0.1.0-time-log.md)

---

## Navigation Guide

### I Want To...

**Plan a new feature**
1. Start with [planning/vision/](./planning/vision/) to ensure alignment
2. Create RFC in [decisions/rfcs/](./decisions/rfcs/) if significant
3. Design in [planning/version/](./planning/version/) or [planning/architecture/](./planning/architecture/)
4. Document decision in [decisions/adrs/](./decisions/adrs/)

**Understand a past decision**
1. Check [decisions/adrs/](./decisions/adrs/) for architectural decisions
2. Or [process/devlogs/version/](./process/devlogs/version/) for narrative context
3. Or [planning/architecture/](./planning/architecture/) for original planning

**See what's planned next**
1. Check [roadmap/](./roadmap/) for near-term plans
2. Or [planning/version/](./planning/version/) for long-term vision

**Study how ragged is built**
1. Read [process/README.md](./process/README.md) for overview
2. Explore [process/devlogs/](./process/devlogs/) for narratives
3. Study [process/time-logs/](./process/time-logs/) for empirical data

**Implement a feature**
1. Follow design in [planning/version/](./planning/version/) or [planning/architecture/](./planning/architecture/)
2. Track work in [process/devlogs/](./process/devlogs/)
3. Document actual in [implementation/](./implementation/)
4. Create ADR in [decisions/adrs/](./decisions/adrs/) for key decisions

**Research AI-assisted development**
1. Read [process/methodology/](./process/methodology/)
2. Compare [planning/version/](./planning/version/) vs. [implementation/](./implementation/)
3. Study [process/time-logs/](./process/time-logs/) for AI effectiveness

---

## Document Lifecycle

### 1. Proposal Phase
**Location:** [decisions/rfcs/](./decisions/rfcs/)
**Purpose:** Discuss significant changes
**Outcome:** Accept or reject

### 2. Planning Phase
**Location:** [planning/](./planning/) (vision, architecture, versions, etc.)
**Purpose:** Detail what to build
**Output:** Architecture, specs, plans

### 3. Decision Phase
**Location:** [decisions/adrs/](./decisions/adrs/)
**Purpose:** Document why choices made
**Output:** Numbered ADRs

### 4. Implementation Phase
**Location:** [process/devlogs/](./process/devlogs/)
**Purpose:** Chronicle the build
**Output:** Daily logs, narratives, time tracking

### 5. Retrospective Phase
**Location:** [implementation/](./implementation/)
**Purpose:** Document what was built
**Output:** Summaries, comparisons to design

---

## For Contributors

### Getting Started

1. **Read** [planning/vision/product-vision.md](./planning/vision/product-vision.md) - Understand goals
2. **Review** [roadmap/](./roadmap/) - See what's planned
3. **Study** [decisions/adrs/](./decisions/adrs/) - Understand key decisions
4. **Follow** [planning/version/](./planning/version/) or [planning/interfaces/](./planning/interfaces/) - Implementation guides
5. **Document** [process/devlogs/](./process/devlogs/) - Share your journey

### Contributing

**For code:**
- Follow design in [planning/architecture/](./planning/architecture/) and [planning/version/](./planning/version/)
- Document decisions in [decisions/adrs/](./decisions/adrs/)
- Track time in [process/time-logs/](./process/time-logs/)
- Write devlog in [process/devlogs/](./process/devlogs/)

**For documentation:**
- See [CONTRIBUTING.md](../../CONTRIBUTING.md)
- Use templates in [process/templates/](./process/templates/)
- Maintain British English
- Follow cross-reference standards (see below)

### Cross-Reference Standards

**All major documentation files should include a "Related Documentation" section at the end:**

**Example format:**
```markdown
---

## Related Documentation

- [v0.2.7 Planning](./planning/version/v0.2/README.md) - Design goals for this version
- [v0.2.7 Implementation](./implementation/version/v0.2/README.md) - What was actually built
- [CLI Enhancements](./planning/interfaces/cli/enhancements.md) - Complete CLI specifications

---
```

**Guidelines:**
- Place "Related Documentation" section at the end, before metadata footer
- Use relative paths from current file
- Include brief description for each link
- Group by relationship type (design → implementation → process)
- Ensure bidirectional links (if A links to B, B should link to A)

**Standard patterns:**

```markdown
## Version Planning → Roadmap
- planning/version/v0.X/README.md links to roadmap/version/v0.X.X/
- roadmap/version/v0.X.X/ links back to planning/version/v0.X/

## Planning → Implementation
- planning/version/v0.X/ links to implementation/version/v0.X/
- implementation/version/v0.X/ links back to planning/version/v0.X/

## Design → Decision Records
- planning/architecture/*.md links to relevant decisions/adrs/*.md
- decisions/adrs/*.md links back to planning/architecture/*.md

## Implementation → Process
- implementation/version/v0.X/ links to process/devlogs/version/v0.X/
- process/devlogs/version/v0.X/ links to implementation/version/v0.X/
```

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
- **Contributing:** See [CONTRIBUTING.md](../../CONTRIBUTING.md)

---

**Last Updated:** 2025-11-14
**Maintained By:** ragged development team
**License:** GPL-3.0 (same as project)
