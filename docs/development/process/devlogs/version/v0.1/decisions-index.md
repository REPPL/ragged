# v0.1 Decisions Index

**Purpose:** Index of all architectural decisions made during v0.1 development

**Last Updated:** 2025-11-15

---

## Overview

This document provides a chronological index of all architectural decisions made during v0.1 implementation. Each decision has been extracted into a formal Architecture Decision Record (ADR) following the standard format.

All ADRs are located in: `docs/development/decisions/adrs/`

---

## ADR Index

### Core Architecture

**[ADR-0001: Local-Only Processing](../../../decisions/adrs/0001-local-only-processing.md)**
- **Date:** 2025-11-09
- **Area:** Architecture, Privacy
- **Summary:** All processing 100% local, no external APIs
- **Impact:** Fundamental principle shaping all technology choices

**[ADR-0004: Factory Pattern for Embedders](../../../decisions/adrs/0004-factory-pattern-for-embedders.md)**
- **Date:** 2025-11-09
- **Area:** Architecture, Embeddings
- **Summary:** Use factory pattern with BaseEmbedder interface
- **Impact:** Enables swappable embedding backends

### Configuration & Data

**[ADR-0002: Pydantic for Configuration](../../../decisions/adrs/0002-pydantic-for-configuration.md)**
- **Date:** 2025-11-09
- **Area:** Configuration
- **Summary:** Use Pydantic v2 for type-safe configuration
- **Impact:** Type safety, validation, clear error messages

**[ADR-0003: ChromaDB for Vector Storage](../../../decisions/adrs/0003-chromadb-for-vector-storage.md)**
- **Date:** 2025-11-09
- **Area:** Storage
- **Summary:** ChromaDB as vector database
- **Impact:** Persistent storage, efficient similarity search

### Embeddings

**[ADR-0006: Dual Embedding Model Support](../../../decisions/adrs/0006-dual-embedding-model-support.md)**
- **Date:** 2025-11-09
- **Area:** Embeddings
- **Summary:** Support sentence-transformers and Ollama embeddings
- **Impact:** User choice based on hardware and preferences

### Document Processing

**[ADR-0007: PyMuPDF4LLM for PDF Processing](../../../decisions/adrs/0007-pymupdf4llm-for-pdf-processing.md)**
- **Date:** 2025-11-09
- **Area:** Document Ingestion
- **Summary:** Use PyMuPDF4LLM for PDF to Markdown conversion
- **Impact:** Structure-preserving PDF extraction

**[ADR-0014: Markdown as Intermediate Format](../../../decisions/adrs/0014-markdown-as-intermediate-format.md)**
- **Date:** 2025-11-09
- **Area:** Document Processing
- **Summary:** Markdown as common intermediate format for all documents
- **Impact:** Consistent processing, better LLM understanding

### Chunking

**[ADR-0008: tiktoken for Token Counting](../../../decisions/adrs/0008-tiktoken-for-token-counting.md)**
- **Date:** 2025-11-09
- **Area:** Chunking
- **Summary:** Use tiktoken with cl100k_base encoding
- **Impact:** Accurate token counting for chunk sizing

**[ADR-0009: Recursive Character Text Splitter](../../../decisions/adrs/0009-recursive-character-text-splitter.md)**
- **Date:** 2025-11-09
- **Area:** Chunking
- **Summary:** Recursive splitting strategy with semantic boundaries
- **Impact:** Better semantic chunk boundaries

### LLM Generation

**[ADR-0012: Ollama for LLM Generation](../../../decisions/adrs/0012-ollama-for-llm-generation.md)**
- **Date:** 2025-11-09
- **Area:** LLM, Generation
- **Summary:** Ollama with llama3.2 as default model
- **Impact:** Local LLM generation with model flexibility

**[ADR-0013: Citation Format [Source: filename]](../../../decisions/adrs/0013-citation-format.md)**
- **Date:** 2025-11-09
- **Area:** Generation, UX
- **Summary:** Standardised citation format for generated answers
- **Impact:** Trust, verifiability, clear source attribution

### CLI & UX

**[ADR-0010: Click + Rich for CLI](../../../decisions/adrs/0010-click-rich-for-cli.md)**
- **Date:** 2025-11-09
- **Area:** CLI Interface
- **Summary:** Click for commands, Rich for beautiful output
- **Impact:** Professional CLI with progress bars and formatting

### Security & Privacy

**[ADR-0011: Privacy-Safe Logging](../../../decisions/adrs/0011-privacy-safe-logging.md)**
- **Date:** 2025-11-09
- **Area:** Logging, Security
- **Summary:** Automatic PII filtering in logs
- **Impact:** Safe log sharing, privacy compliance

### Development Process

**[ADR-0005: 14-Phase Implementation Approach](../../../decisions/adrs/0005-14-phase-implementation-approach.md)**
- **Date:** 2025-11-09
- **Area:** Development Process
- **Summary:** Structured 14-phase implementation for v0.1
- **Impact:** Clear milestones, incremental progress

---

## Decision Categories

### By Impact Level

**High Impact (Fundamental):**
- ADR-0001: Local-Only Processing
- ADR-0002: Pydantic for Configuration
- ADR-0003: ChromaDB for Vector Storage
- ADR-0006: Dual Embedding Model Support
- ADR-0012: Ollama for LLM Generation

**Medium Impact (Quality):**
- ADR-0007: PyMuPDF4LLM for PDF Processing
- ADR-0009: Recursive Character Text Splitter
- ADR-0014: Markdown as Intermediate Format

**Implementation Details:**
- ADR-0004: Factory Pattern for Embedders
- ADR-0005: 14-Phase Implementation Approach
- ADR-0008: tiktoken for Token Counting
- ADR-0010: Click + Rich for CLI
- ADR-0011: Privacy-Safe Logging
- ADR-0013: Citation Format

### By Technology Area

**Embeddings:**
- ADR-0004: Factory Pattern for Embedders
- ADR-0006: Dual Embedding Model Support

**Document Processing:**
- ADR-0007: PyMuPDF4LLM for PDF Processing
- ADR-0014: Markdown as Intermediate Format

**Chunking:**
- ADR-0008: tiktoken for Token Counting
- ADR-0009: Recursive Character Text Splitter

**Generation:**
- ADR-0012: Ollama for LLM Generation
- ADR-0013: Citation Format

**Infrastructure:**
- ADR-0001: Local-Only Processing
- ADR-0002: Pydantic for Configuration
- ADR-0003: ChromaDB for Vector Storage
- ADR-0010: Click + Rich for CLI
- ADR-0011: Privacy-Safe Logging

**Process:**
- ADR-0005: 14-Phase Implementation Approach

---

## Timeline

All decisions were made during the v0.1 planning and implementation phase (November 2025). The decisions were documented in narrative form in this file and subsequently extracted to individual ADR files following standard ADR format.

---

## Related Documentation

**Implementation:**
- [v0.1 Implementation Summary](../../../../implementations/version/v0.1/summary.md)
- [v0.1 Implementation Notes](../../../../implementations/version/v0.1/implementation-notes.md)

**Architecture:**
- [Architecture Overview](../../../../architecture/README.md)
- [Core Concepts](../../../../core-concepts/)

**Process:**
- [v0.1 Development Log](../README.md)
- [v0.1 Time Log](../../../time-logs/version/v0.1/v0.1.0-time-log.md)

---

## Using This Index

**To understand a specific decision:**
1. Find the ADR by area or technology
2. Click through to read full context, rationale, and consequences
3. Check "Related" section in each ADR for connected decisions

**To understand the architecture:**
1. Start with "High Impact" decisions (fundamental choices)
2. Read category groups (e.g., all Embeddings ADRs together)
3. Follow cross-references between related ADRs

**To contribute:**
1. Read relevant ADRs before proposing changes
2. New significant decisions should create new ADRs
3. Follow ADR template in `process/templates/adr-template.md`

---

**Maintained By:** ragged development team

**License:** GPL-3.0
