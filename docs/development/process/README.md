# Development Process Documentation

**Transparency in AI-Assisted Software Development**

---

## Table of Contents

- [Overview](#overview)
- [Why Document Development Process?](#why-document-development-process)
- [Directory Structure](#directory-structure)
- [Key Components](#key-components)
  - [Methodology](#1-methodology-methodology)
  - [Roadmap](#2-roadmap-roadmap)
  - [Development Logs](#3-development-logs-devlog)
  - [Time Logs](#4-time-logs-time-logs)
  - [Architecture Decision Records](#5-architecture-decision-records-decisions)
  - [Request for Comments](#6-request-for-comments-rfcs)
  - [Templates](#7-templates-templates)
- [Document Lifecycle](#document-lifecycle)
- [Using This Documentation](#using-this-documentation)
- [Transparency Principles](#transparency-principles)
- [Development Philosophy](#development-philosophy)
- [Example: Transparency in Action](#example-transparency-in-action)
- [Contributing](#contributing)
- [Questions?](#questions)

---

## Overview

This directory contains comprehensive documentation of ragged's development process. Unlike typical project documentation, we document **how the software is being built**, not just what it does.

## Why Document Development Process?

1. **Transparency**: Show how AI tools (Claude Code, etc.) are used in development
2. **Reproducibility**: Enable others to understand and replicate our approach
3. **Learning**: Share lessons learned from AI-assisted development
4. **Research**: Contribute data to understanding AI coding effectiveness
5. **Accountability**: Honest tracking of time, effort, and challenges

---

## Directory Structure

```
development/
├── README.md (this file)
│
├── methodology/                  # How we develop
│   ├── README.md
│   ├── ai-assistance.md
│   └── time-tracking.md
│
├── devlog/                       # What we're doing & did
│   ├── README.md
│   ├── daily/                   # Daily development logs
│   │   ├── 2025-11-09.md
│   │   ├── 2025-11-10.md
│   │   └── 2025-11-12.md
│   └── version/                 # Version-specific logs
│       ├── v0.1/
│       │   ├── README.md
│       │   ├── implementation-notes.md
│       │   ├── decisions.md
│       │   └── summary.md
│       └── v0.2/
│           ├── README.md
│           └── v0.2.x-release-notes.md
│
├── time-logs/                    # How long it took
│   ├── README.md
│   └── version/
│       ├── v0.1/
│       │   └── v0.1-time-log.md
│       └── v0.2/
│           └── v0.2.x-time-log.md
│
└── templates/                    # How to document
    ├── adr-template.md
    ├── devlog-template.md
    └── version-time-log-template.md
```

---

## Key Components

### 1. Methodology (`methodology/`)

Documents **how** we develop ragged with AI assistance and transparent time tracking.

**[methodology/README.md](./methodology/README.md)** - Development methodology overview

**[methodology/ai-assistance.md](./methodology/ai-assistance.md)** - AI tool usage:
- Which tools (Claude Code, etc.)
- For what tasks (scaffolding, documentation, debugging)
- Effectiveness ratings by task type
- Guidelines for contributors using AI

**[methodology/time-tracking.md](./methodology/time-tracking.md)** - Time tracking approach:
- Per-feature time logs with hour breakdowns
- AI vs. manual time comparison
- What worked, what didn't
- Realistic expectations for similar work

---

### 2. Development Logs (`devlog/`)

Documents **what we're doing and did** during development.

**Daily Logs** (`devlog/daily/`):
- What was accomplished each day
- Decisions made
- Blockers encountered
- AI tool effectiveness
- Energy and focus levels

**Version Logs** (`devlog/version/vX.X/`):
- **README.md**: Overview and navigation
- **implementation-notes.md**: Technical details during development
- **decisions.md**: Architecture decisions made
- **summary.md**: Retrospective after completion
- **testing.md, lessons-learned.md**: Quality and learning

**Purpose**: Chronicle the actual development journey, not just outcomes.

---

### 3. Time Logs (`time-logs/`)

Documents **how long development actually took** per version and feature.

**[time-logs/README.md](./time-logs/README.md)** - Time tracking overview

**Per-Version Time Logs** (`time-logs/version/vX.X/vX.X-time-log.md`):
- Total hours per category (implementation, testing, docs, debugging)
- AI-assisted vs. manual time breakdown
- AI effectiveness by task type
- Challenges and resolutions
- Learning and retrospective

**Purpose**: Provide empirical data for future estimates and research.

---

### 4. Templates (`templates/`)

Documents **how to create** consistent development documentation.

**Available Templates**:
- `adr-template.md` - Architecture Decision Records
- `devlog-template.md` - Daily development logs
- `version-time-log-template.md` - Version time logs
- `feature-time-log-template.md` - Feature-specific time logs

---

## Document Lifecycle

### Phase 1: Planning (../roadmap/)
1. Create roadmap: `../roadmap/version/vX.X/README.md`
2. Document features, bugs, hour estimates
3. Mark manual testing points (⚠️ MANUAL TEST REQUIRED)
4. Review and approve

### Phase 2: Development (devlog/)
5. Start work → Daily logs in `devlog/daily/`
6. Create version folder: `devlog/version/vX.X/`
7. Track implementation in `implementation-notes.md`
8. Document decisions in `../decisions/adrs/` (ADRs)

### Phase 3: Completion (time-logs/ + devlog/)
9. Complete → Create `summary.md` retrospective
10. Log actual time in `time-logs/version/vX.X/`
11. Capture lessons learned

### Phase 4: Next Version
12. Fresh clone for testing (no migrations)
13. Begin next version planning cycle

---

## Using This Documentation

### For Users

- **Curious about AI development?** Read [methodology/ai-assistance.md](./methodology/ai-assistance.md)
- **Want to understand decisions?** Check ADRs in [../decisions/adrs/](../decisions/adrs/)
- **See actual progress?** Read [devlog/daily/](./devlog/daily/)
- **View planned features?** Check [../roadmap/version/](../roadmap/version/)

### For Contributors

- **Using AI tools?** Follow guidelines in [methodology/ai-assistance.md](./methodology/ai-assistance.md)
- **Making architectural decisions?** Create ADR in [../decisions/adrs/](../decisions/adrs/)
- **Proposing major features?** Write RFC in [../decisions/rfcs/](../decisions/rfcs/)
- **Tracking your time?** Use templates in [templates/](./templates/)

### For Researchers

- **Studying AI coding?** Time logs provide quantitative data
- **Reproducibility?** Devlogs and ADRs show full process
- **Case study material?** Complete development history
- **Empirical estimates?** Compare roadmap estimates vs. actual time logs

### For Future You

- **"Why did we do X?"** → Check [../decisions/adrs/](../decisions/adrs/) (ADRs)
- **"How long did Y take?"** → Check [time-logs/version/](./time-logs/version/)
- **"What happened on date Z?"** → Check [devlog/daily/](./devlog/daily/)
- **"What's planned next?"** → Check [../roadmap/version/](../roadmap/version/)

---

## Transparency Principles

### We Document

✅ Actual time spent (hours for AI assistant, not calendar weeks)
✅ AI tool usage and effectiveness
✅ Decisions and trade-offs
✅ Blockers and how they were resolved
✅ What worked and what didn't
✅ Learning outcomes
✅ Manual testing requirements

### We Don't Hide

❌ Mistakes or failed approaches
❌ AI-generated code (disclosed openly)
❌ Time spent debugging
❌ Learning curves
❌ Challenges encountered
❌ Discrepancies between estimates and actuals

---

## Development Philosophy

### AI as Amplifier, Not Substitute

- AI tools amplify human expertise, don't replace it
- All AI-generated code is reviewed and understood
- Developers are accountable for all submitted code
- Critical code paths are written manually
- Hour estimates reflect AI coding assistant capabilities

### Empirical Over Aspirational

- Track actual time, not estimates (time logs vs roadmap)
- Document real decisions, not ideal ones
- Share failures alongside successes
- Learn from data, not assumptions
- Compare planned vs. actual hours

### Open Development

- Development process is public
- Decisions are documented
- Community can see how ragged is built
- Academic research can use our data
- Fresh clone testing (no migration complexity)

---

## Example: Transparency in Action

**Instead of saying**:
> "v0.2.5 will take 1-2 weeks and fix bugs"

**We document**:

**Roadmap** (`roadmap/version/v0.2.5/README.md`):
- 16 bugs categorized by priority
- Estimated: 40-50 hours (AI implementation)
- Manual testing: API endpoints, Web UI, error handling
- Success criteria: Zero crashes, Web UI functional, 80% test coverage

**Time Log** (`time-logs/version/v0.2/v0.2.5-time-log.md`):
- Actual: 47.5 hours
- AI-assisted: 62% (29.5h)
- Manual: 38% (18h)
- Challenges: ChromaDB connection handling (3.5h), Progress bar I/O (2h)
- Learning: AI excellent for error handling, manual testing critical

This gives:
- **Realistic expectations** for similar work (47.5h actual vs 40-50h estimated)
- **Insight into AI effectiveness** (62% AI-assisted, varies by task)
- **Honest accounting** of challenges (5.5h on 2 unexpected issues)
- **Reproducible data** for research (compare roadmap vs time log)

---

## Contributing

When contributing to ragged:

1. **Use AI tools?** Disclose in PR (see [methodology/ai-assistance.md](./methodology/ai-assistance.md))
2. **Making architectural decisions?** Create ADR in [../decisions/adrs/](../decisions/adrs/)
3. **Proposing major features?** Write RFC in [../decisions/rfcs/](../decisions/rfcs/)
4. **Significant time investment?** Create time log in [time-logs/](./time-logs/)
5. **Daily development?** Log in [devlog/daily/](./devlog/daily/)

See [Contributing Guide](../../../CONTRIBUTING.md) for details.

---

## Questions?

- **About development process**: [GitHub Discussions](https://github.com/REPPL/ragged/discussions)
- **About specific decisions**: Check [../decisions/adrs/](../decisions/adrs/)
- **About time tracking**: See [methodology/time-tracking.md](./methodology/time-tracking.md)
- **About roadmap**: See [../roadmap/version/README.md](../roadmap/version/README.md)

---

**This is a living process.** We'll refine our transparency practices as we learn what's most valuable for the community and research.

---

## Related Documentation

- [Planning Documentation](../planning/) - What we plan to build
- [Roadmaps](../roadmap/) - How and when we plan to build it
- [Implementations](../implementation/) - What we actually built
- [Decision Records (ADRs)](../decisions/adrs/) - Why we made specific choices
- [Development Documentation](../README.md) - Overall development documentation structure

---

**Last updated**: 2025-11-12
**Status:** Active - all ragged development tracked from v0.1 onwards
