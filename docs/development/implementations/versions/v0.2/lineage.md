# v0.2 Implementation Lineage

**Version:** v0.2.x (In Progress)

**Status:** Partial Implementation

**Last Updated:** 2025-11-15

---

## Purpose

This document traces the lineage from planning through decisions to implementation for ragged v0.2, focusing on document normalization and enhanced retrieval.

---

## Planning → Decisions → Implementation

### 1. Planning Documents

**Version Design:**
- [v0.2 Version Overview](../../../planning/versions/v0.2/) - Enhanced retrieval goals

**Architecture Enhancements:**
- [Document Normalisation](../../../planning/architecture/document-normalisation.md) - Text cleaning
- [Enhanced Retrieval](../../../planning/architecture/enhanced-retrieval.md) - Better search

**Core Concepts:**
- [Chunking Strategy](../../../planning/core-concepts/chunking.md) - Overlap optimization
- [Metadata Extraction](../../../planning/core-concepts/metadata.md) - Document metadata

### 2. Architectural Decisions

*Note: v0.2 builds on v0.1 ADRs. New decisions for v0.2 features will be documented as ADR-0015+*

**Inherited from v0.1:**
- All ADRs 0001-0014 remain applicable
- ChromaDB, Pydantic, Ollama, privacy principles unchanged

**Planned v0.2 Decisions** (to be created):
- Document normalization approach (Unicode, whitespace, structure)
- Chunk overlap strategy (token-based vs character-based)
- Metadata extraction pipeline (author, date, source)
- Enhanced retrieval techniques (query expansion, filtering)

### 3. Implementation Records

**Current Status:**
- [v0.2 Summary](./summary.md) - Partial implementation status
- [v0.2 Implementation Notes](./implementation-notes.md) - Technical details (in progress)

**Development Narrative:**
- v0.2 Development Log (not yet created)
- v0.2 Time Log (not yet created)

---

## Traceability Matrix

| Planning | Decision | Implementation | Status |
|----------|----------|----------------|--------|
| Document normalization | TBD (ADR-0015) | Text cleaning pipeline | 🔄 In Progress |
| Chunk overlap optimization | TBD (ADR-0016) | Overlap calculator | ⏳ Planned |
| Metadata extraction | TBD (ADR-0017) | Metadata pipeline | ⏳ Planned |
| Enhanced retrieval | TBD (ADR-0018) | Query expansion | ⏳ Planned |

---

## Implementation Progress

### Completed Features

1. **Document Normalisation:**
   - Unicode normalization (NFC)
   - Whitespace cleaning
   - Special character handling
   - Status: ✅ Implemented

2. **Metadata Extraction:**
   - Author, date, source extraction
   - File type detection
   - Status: ✅ Implemented

### In Progress Features

1. **Chunk Overlap Optimization:**
   - Token-based overlap calculation
   - Semantic boundary preservation
   - Status: 🔄 50% complete

2. **Enhanced Retrieval:**
   - Query expansion
   - Metadata filtering
   - Status: 🔄 30% complete

### Planned Features

1. **Web UI (Basic):**
   - Gradio interface
   - Status: ⏳ Not started

2. **Performance Monitoring:**
   - Latency tracking
   - Status: ⏳ Not started

---

## Deviations from Plan

### Implementation Order Changes

1. **Web UI Deferred:**
   - **Planned:** v0.2
   - **Actual:** Partial implementation, full UI deferred to v0.3
   - **Reason:** Focus on core retrieval improvements first

2. **Performance Monitoring Added Early:**
   - **Planned:** v0.3
   - **Actual:** Basic monitoring added in v0.2
   - **Reason:** Needed for retrieval optimization

---

## Lessons for v0.3

### What's Working Well

1. **Incremental Approach:** Building on v0.1 foundation
2. **Metadata Pipeline:** Clean extraction architecture
3. **Testing:** Maintaining high test coverage

### What Needs Improvement

1. **ADR Discipline:** Create ADRs earlier in the process
2. **Documentation Sync:** Keep implementation notes current
3. **Performance Tracking:** Need better benchmarks

---

## Related Documentation

**Planning:**
- [v0.2 Version Overview](../../../planning/versions/v0.2/)
- [Architecture Enhancements](../../../planning/architecture/)

**Decisions:**
- [All v0.1 ADRs](../../../decisions/adrs/) (inherited)
- v0.2 ADRs (to be created)

**Implementation:**
- [v0.2 Summary](./summary.md)
- [Implementation Notes](./implementation-notes.md)

**Previous Version:**
- [v0.1 Lineage](../v0.1/lineage.md) - Foundation

---

**Maintained By:** ragged development team

**License:** GPL-3.0
