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

| ID | Title | Status |
|----|-------|--------|
| [ADR-001](./ADR-001-vision-embeddings-opt-in-design.md) | Vision Embeddings Opt-In Design | Accepted |
| [ADR-002](./ADR-002-chromadb-as-vector-database.md) | ChromaDB as Vector Database | Accepted |
| [ADR-003](./ADR-003-privacy-first-local-only-design.md) | Privacy-First Local-Only Design Philosophy | Accepted |
| [ADR-004](./ADR-004-gpl-3-license-choice.md) | GPL-3.0 License Choice | Accepted |
| [ADR-005](./ADR-005-dual-embedding-storage-architecture.md) | Dual Embedding Storage Architecture | Accepted |
| [ADR-006](./ADR-006-ollama-for-llm-generation.md) | Ollama for LLM Generation | Accepted |
| [ADR-007](./ADR-007-gradio-for-web-ui.md) | Gradio for Web UI | Accepted |

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
