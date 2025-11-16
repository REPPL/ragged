# Implementation Documentation

**Purpose:** Document what was actually built (vs. what was planned)

**Last Updated:** 2025-11-15

---

## Overview

This directory tracks the **actual implementation** of ragged features, organised by version. It documents what was built, how it differs from the plan, lessons learned, and implementation outcomes.

**Distinction:**
- **planning/** = What we **planned** to build (design phase)
- **implementations/** = What we **actually built** (retrospective)
- **process/devlogs/** = **How** we built it (narrative)

---

## Structure

```
implementations/
├── README.md           ← This file
└── versions/           ← Version-specific implementation records
    ├── v0.1/          ← MVP implementation (complete)
    └── v0.2/          ← Enhanced retrieval (in progress)
```

---

## Version Implementation Records

### [versions/v0.1/](./version/v0.1/) - MVP Implementation

**Status:** Complete (November 2025)

**What was built:**
- Local-only RAG system with CLI
- PDF ingestion and processing
- Dual embedding support (sentence-transformers + Ollama)
- ChromaDB vector storage
- Ollama LLM generation with citations
- Basic CLI interface

**Key documents:**
- [Summary](./version/v0.1/summary.md) - Results and retrospective
- [Implementation Notes](./version/v0.1/implementation-notes.md) - Technical details
- [Testing Results](./version/v0.1/testing.md) - Test coverage and quality
- [Lineage](./version/v0.1/lineage.md) - Complete traceability from planning to implementation

### [versions/v0.2/](./version/v0.2/) - Enhanced Retrieval

**Status:** In progress

**What's being built:**
- Advanced retrieval strategies
- Query understanding improvements
- Enhanced chunking methods
- Multi-query retrieval

**Key documents:**
- [Implementation Plan](./version/v0.2/implementation-plan.md) - Development guide
- [v0.2.1 Release Notes](./version/v0.2/v0.2.1-release-notes.md) - Chunking enhancements
- [v0.2.2 Release Notes](./version/v0.2/v0.2.2-release-notes.md) - Retrieval enhancements
- [Lineage](./version/v0.2/lineage.md) - Traceability from planning to implementation (partial)

---

## How to Use This Documentation

### Understanding What Was Built

1. Navigate to the version directory (e.g., `versions/v0.1/`)
2. Read the summary for high-level outcomes
3. Review implementation notes for technical details
4. Compare with original plans in `planning/version/`

### Planning Future Versions

1. Review lessons learned from completed versions
2. Identify patterns in deviations from plan
3. Apply learnings to future planning
4. Document decision rationale in ADRs

### Contributing

When completing a version:
1. Create version directory under `versions/`
2. Document what was actually built
3. Note deviations from the plan
4. Record lessons learned
5. Include metrics and outcomes

---

## Relationship to Other Documentation

**Planning documentation:**
- [planning/version/](../planning/version/) - Original design plans
- [planning/architecture/](../planning/architecture/) - System architecture

**Decision documentation:**
- [decisions/adrs/](../decisions/adrs/) - Architecture decisions made

**Process documentation:**
- [process/devlogs/version/](../process/devlogs/version/) - Development narratives
- [process/time-logs/version/](../process/time-logs/version/) - Time tracking

**Roadmap documentation:**
- [roadmaps/version/](../roadmaps/version/) - Feature roadmaps

---

## Navigation

- **[← Development Documentation](../README.md)** - Back to development docs
- **[Planning Documentation →](../planning/)** - Original design plans
- **[Process Documentation →](../process/)** - Development narratives

---

**Maintained By:** ragged development team

**License:** GPL-3.0
