# User Stories Index

**Last Updated**: 2025-11-09
**Status:** Active
**Version**: 1.0

---

## Overview

This directory contains user stories that define the **functional requirements** and **user value** for ragged. Each user story follows the standard format:

```
As a [user type]
I want [capability]
So that [benefit]
```

User stories are organised by **persona** and linked to **implementation versions**, **acceptance criteria**, and **test cases**.

---

## User Story Catalogue

### Researcher Persona

| ID | Title | Status | Version | Priority |
|----|-------|--------|---------|----------|
| **US-001** | [Professional Research Assistant](./US-001-professional-research-assistant.md) | ✅ Active | v0.1-v1.0 | **Critical** |
| **US-002** | [Personal Knowledge Vault](./US-002-personal-knowledge-vault.md) | ✅ Active | v0.1-v1.0 | **Critical** |

### Developer Persona

| ID | Title | Status | Version | Priority |
|----|-------|--------|---------|----------|
| **US-003** | [Code Documentation RAG](./US-003-code-documentation-rag.md) | ✅ Active | v0.3-v1.0 | **High** |

### Casual Persona

| ID | Title | Status | Version | Priority |
|----|-------|--------|---------|----------|
| **US-004** | [Personal Knowledge Assistant](./US-004-personal-knowledge-assistant.md) | ✅ Active | v0.2-v1.0 | **Medium** |

---

## Feature Mapping

### By Version

#### v0.1 - MVP
**User Stories**: Partial US-001, US-002
- Basic document ingestion (PDF, TXT, MD)
- Simple semantic search
- Basic Q&A with RAG

#### v0.2 - Document Normalisation
**User Stories**: US-001 (60%), US-002 (50%), US-004 (partial)
- All document format support
- Metadata extraction
- Improved search quality

#### v0.3 - Personal Memory & Personas
**User Stories**: US-001 (70%), US-002 (80%), US-003 (40%)
- Persona system
- Memory tracking
- Citation basics (APA)
- Code documentation indexing

#### v0.4 - Advanced Features
**User Stories**: US-001 (85%), US-002 (90%), US-003 (70%)
- Multiple citation formats
- Temporal features
- Learning from usage patterns
- Code search and explanation

#### v1.0 - Production
**User Stories**: US-001 (100%), US-002 (100%), US-003 (100%), US-004 (100%)
- Complete citation network
- Full temporal analytics
- Advanced learning capabilities
- Production-ready features

---

## By Persona

### Researcher
**Primary Stories**: US-001, US-002
**Persona Definition**: [Personal Memory & Personas](../../core-concepts/personal-memory-personas.md#researcher-persona)

**Key Needs**:
- Academic paper management
- Citation generation
- Literature synthesis
- Personal research notes with privacy

**Success Metrics**:
- 30%+ time savings in literature search
- 99%+ citation accuracy
- 90%+ relevant document recall

### Developer
**Primary Stories**: US-003
**Persona Definition**: [Personal Memory & Personas](../../core-concepts/personal-memory-personas.md#developer-persona)

**Key Needs**:
- Code documentation search
- API reference lookup
- Example code retrieval
- Technical knowledge base

**Success Metrics**:
- 40%+ faster documentation lookup
- 95%+ code example relevance
- 85%+ accurate technical answers

### Casual
**Primary Stories**: US-004
**Persona Definition**: [Personal Memory & Personas](../../core-concepts/personal-memory-personas.md#casual-persona)

**Key Needs**:
- Personal note management
- Quick information retrieval
- Simple, fast interface
- Web article archiving

**Success Metrics**:
- < 2 second query response time
- 90%+ note retrieval accuracy
- Minimal configuration required

---

## Acceptance Criteria Tracking

Each user story includes **testable acceptance criteria** that drive:

1. **Feature Development**: What to build
2. **Test Creation**: What to test
3. **Quality Gates**: When to ship

**Example Mapping**:
```
US-001: Professional Research Assistant
  ├── AC-001: PDF ingestion
  │   ├── Feature: Document processor (v0.1)
  │   ├── Test: tests/e2e/test_pdf_ingestion.py
  │   └── Quality: 100% of PDFs parseable
  │
  ├── AC-002: Semantic search
  │   ├── Feature: ChromaDB retrieval (v0.1)
  │   ├── Test: tests/integration/test_semantic_search.py
  │   └── Quality: > 90% recall @ k=10
  │
  └── AC-003: Citation generation
      ├── Feature: Citation formatter (v0.3)
      ├── Test: tests/unit/test_citations.py
      └── Quality: 99%+ accuracy for APA/MLA
```

---

## Creating New User Stories

### Template

Use the [User Story Template](../../development/templates/user-story-template.md) for consistency.

### Naming Convention

```
US-XXX-brief-description.md

Where:
- XXX = Sequential number (001, 002, 003...)
- brief-description = Kebab-case summary
```

### Required Sections

1. **Overview** - As a/I want/So that format
2. **Acceptance Criteria** - Testable requirements
3. **Technical Constraints** - Limitations and considerations
4. **Success Metrics** - Measurable outcomes
5. **Feature Roadmap** - Version mapping
6. **Related Personas** - Which personas benefit
7. **Cross-References** - Links to architecture and implementation

---

## Version Status Legend

| Symbol | Meaning |
|--------|---------|
| ✅ | Active - Currently being implemented |
| 🚧 | In Progress - Partially implemented |
| ⏸️ | Deferred - Postponed to later version |
| ✔️ | Complete - Fully implemented and tested |
| ❌ | Rejected - Not being pursued |

---

## Priority Levels

| Priority | Definition | Implementation |
|----------|------------|----------------|
| **Critical** | Core value proposition, must have for v1.0 | Implement first |
| **High** | Significant value, should have for v1.0 | Implement early |
| **Medium** | Nice to have, could have for v1.0 | Implement if time permits |
| **Low** | Future enhancement, won't have in v1.0 | Defer to v1.1+ |

---

## Cross-References

### Implementation
- [Architecture Overview](../../architecture/README.md)
- [Personal Memory & Personas](../../core-concepts/personal-memory-personas.md)
- [Hardware Optimisation](../../core-concepts/hardware-optimisation.md)
- [Model Selection](../../core-concepts/model-selection.md)
- [Testing Strategy](../../core-concepts/testing-strategy.md)

### Development
- [Version Roadmap](../../versions/)
- [Roadmaps](../../../roadmaps/README.md)

### Testing
- [Testing Process](../../../process/testing/README.md)

---

## Change History

| Date | Version | Changes | Author |
|------|---------|---------|--------|
| 2025-11-09 | 1.0 | Initial organisation, enhanced US-001 and US-002, added US-003 and US-004 | Claude |
| 2025-11-09 | 0.1 | Original user stories created | User |

---

## Contributing

When adding new user stories:

1. **Follow template structure** - Maintain consistency
2. **Link to personas** - Connect to existing persona definitions
3. **Map to versions** - Specify when features will be implemented
4. **Define acceptance criteria** - Make requirements testable
5. **Cross-reference** - Link to architecture and implementation docs
6. **Update this index** - Keep the catalogue current
7. **Use British English** - Maintain documentation consistency

---

**Document Owner**: Product/Requirements
**Stakeholders**: All (engineering, design, users)
**Review Cycle**: Every version milestone
