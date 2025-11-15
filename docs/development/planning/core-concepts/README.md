# Core Concepts

This folder contains the foundational concepts and design principles that guide the Ragged implementation. These documents explain the "why" and "how" behind key architectural decisions.

## Overview

The core concepts define how Ragged achieves its goals of being a privacy-first, locally-run RAG system optimised for personal knowledge management and research assistance. Each concept addresses a specific aspect of the system's design.

---

## Concepts by Category

### User Experience & Personalisation

**[Personal Memory & Personas](./personal-memory-personas.md)**
- Multi-persona system (Researcher, Developer, Casual)
- Persona-specific memory scopes and preferences
- Temporal memory with Kuzu graph database
- Privacy and security considerations

**[Progressive Disclosure](./progressive-disclosure.md)**
- Incremental feature rollout across versions
- Version-based capability management
- User experience evolution from v0.1 to v1.0

**[Versioning Philosophy](./versioning-philosophy.md)**
- Semantic versioning approach
- Feature delivery roadmap
- Backwards compatibility strategy

---

### Data Processing & Management

**[Document Normalisation](./document-normalisation.md)**
- Unified document representation
- Format-agnostic processing pipeline
- Content extraction and standardization

**[Duplicate Detection](./duplicate-detection.md)**
- Cross-format duplicate identification
- Content fingerprinting strategies
- Deduplication approaches

**[Metadata Schema](./metadata-schema.md)**
- Document metadata structure
- Versioned metadata evolution
- Extensibility design

---

### System Intelligence

**[Model Selection](./model-selection.md)**
- Task-based routing strategies
- Performance tier system (Fast/Balanced/Quality)
- Model recommendations by use case
- Dynamic model selection based on query complexity

**[Hardware Optimisation](./hardware-optimisation.md)**
- Resource-aware model selection
- Performance vs. quality trade-offs
- Hardware requirement tiers
- Memory and compute optimisation

---

### Quality & Reliability

**[Testing Strategy](./testing-strategy.md)**
- Multi-level testing approach (unit, integration, E2E)
- RAG-specific evaluation metrics
- Golden dataset testing
- Performance benchmarking
- Safety and security testing

---

## Implementation Notes

These core concepts are referenced throughout the implementation plan and inform:
- Architecture decisions (see [architecture/](../architecture/))
- Technology selection (see [technologies/](../technologies/))
- Version-specific features (see [versions/](../versions/))
- User story requirements (see [../../requirements/user-stories/](../../requirements/user-stories/))

---

## Cross-References

- **Architecture**: [architecture/README.md](../architecture/README.md)
- **Technology Stack**: [technologies/](../technologies/)
- **Version Roadmap**: [versions/](../versions/)
- **User Stories**: [../../requirements/user-stories/](../../requirements/user-stories/)

---

**Last Updated**: 2025-11-09
**Status**: Active development
