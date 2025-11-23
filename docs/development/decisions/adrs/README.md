# Architecture Decision Records (ADRs)

**Status:** ✅ Active

## Overview

This directory contains Architecture Decision Records (ADRs) documenting significant architectural and technical decisions made during ragged's development.

---

## Purpose

ADRs provide:
- **Context**: Why a decision was needed
- **Options**: What alternatives were considered
- **Decision**: What was chosen and why
- **Consequences**: What effects this decision has

---

## ADR Format

Each ADR follows the template at [adr-template.md](../../process/templates/adr-template.md) and includes:

1. **Title**: Short, descriptive name
2. **Status**: Proposed, Accepted, Deprecated, Superseded
3. **Date**: When the decision was made
4. **Context**: The situation requiring a decision
5. **Decision**: What was decided
6. **Consequences**: Positive and negative effects

---

## Accepted ADRs

| ID | Title | Date | Status |
|----|-------|------|--------|
| [ADR-001](./ADR-001-vision-embeddings-opt-in-design.md) | Vision Embeddings Opt-In Design | 2025-11-23 | Accepted |

---

## Future Decisions

Decisions that may be documented as development progresses:
- Choice of vector database (ChromaDB vs Qdrant)
- Document chunking strategy
- Web framework selection
- Storage model design
- LLM provider integration approach

---

## Related Documentation

- **[ADR Template](../../process/templates/adr-template.md)** - Template for new ADRs
- **[Development Guide](../README.md)** - Development process
- **[Architecture](../../planning/architecture/README.md)** - Current architecture

---

*This directory will be populated as architectural decisions are made during development*
