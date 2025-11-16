# Decisions Documentation

**Purpose:** All architectural and technical decisions for ragged

**Last Updated:** 2025-11-15

---

## Overview

This directory contains all decision documentation for the ragged project, including Architecture Decision Records (ADRs) and Request for Comments (RFCs).

---

## Structure

### [adrs/](./adrs/)

**Architecture Decision Records**

Formal documentation of architectural decisions with context, rationale, and consequences.

**Format:** Numbered ADRs (0001-title.md)

**Current Count:** 14 ADRs

**Coverage:**
- Core architecture (local-only, factory patterns)
- Technology choices (Pydantic, ChromaDB, Ollama)
- Implementation strategies (chunking, embeddings, citations)
- Process decisions (14-phase approach)

### [rfcs/](./rfcs/)

**Request for Comments**

Proposals for significant changes before design phase.

**Status:** Empty (template ready)

**Format:** Numbered RFCs (0001-title.md)

**Process:**
1. Draft RFC with problem + proposed solution
2. Community discussion
3. Accept/reject decision
4. If accepted → Create design docs → Create ADR after implementation

---

## Decision Lifecycle

```
RFC (Proposal)
    ↓ (if accepted)
Design Documents (planning/)
    ↓
Implementation
    ↓
ADR (Record of decision)
```

---

## For Contributors

**To propose a major change:**
1. Create RFC in `rfcs/`
2. Submit for discussion
3. After approval, create design docs in `planning/`

**To understand past decisions:**
1. Browse `adrs/` by number or topic
2. Check ADR's "Related" section for connected decisions

---

## Related Documentation

- [ADRs Directory](./adrs/) - All architecture decisions
- [RFCs Directory](./rfcs/) - All proposals
- [Planning](../planning/) - Future designs
- [Implementations](../implementation/) - Past implementations

---

**Maintained By:** ragged development team

**License:** GPL-3.0
