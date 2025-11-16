# Technology Stack

This folder documents the technology choices and implementation approaches for key system capabilities in Ragged. Each document explores options, trade-offs, and recommendations for specific technical domains.

## Overview

The technology stack is designed to support Ragged's core requirements:
- **Privacy-first**: Local execution, no cloud dependencies
- **Offline-capable**: Complete functionality without internet connectivity
- **Resource-efficient**: Optimised for consumer hardware
- **Extensible**: Modular architecture supporting future enhancements

---

## Technology Documentation

### [Document Processing](./document-processing.md)
Document ingestion, parsing, and extraction capabilities.

**Topics covered:**
- Multi-format document parsing (PDF, DOCX, Markdown, HTML, etc.)
- Text extraction and preprocessing
- Metadata extraction
- Content structure preservation
- Library recommendations and comparisons

**Key technologies:** PyMuPDF, python-docx, BeautifulSoup4, readability-lxml

---

### [Offline Capability](./offline-capability.md)
Ensuring complete system functionality without internet connectivity.

**Topics covered:**
- Local LLM inference with Ollama
- Offline embedding models
- Local vector database storage
- Dependency management for offline operation
- Network isolation strategies

**Key technologies:** Ollama, ChromaDB, nomic-embed-text, Kuzu

---

### [Streaming](./streaming.md)
Real-time response streaming for improved user experience.

**Topics covered:**
- LLM response streaming approaches
- Incremental UI updates
- Streaming protocols (SSE, WebSockets)
- Backpressure handling
- Error recovery in streaming contexts

**Key technologies:** FastAPI StreamingResponse, Server-Sent Events (SSE)

---

### [Web Frameworks](./web-frameworks.md)
Web UI framework selection and implementation approach.

**Topics covered:**
- Frontend framework comparison (Svelte, React, Vue)
- Backend framework selection (FastAPI)
- Progressive enhancement strategy
- Desktop integration considerations (Tauri)
- Versioned UI rollout (v0.2 CLI → v0.5 Web → v1.0+ Desktop)

**Key technologies:** Svelte, FastAPI, Tauri (future)

---

## Selection Criteria

Technology choices are evaluated based on:

1. **Privacy & Security**: No telemetry, local-only operation
2. **Resource Efficiency**: Low memory/CPU footprint
3. **Developer Experience**: Good documentation, active community
4. **Reliability**: Mature, well-tested libraries
5. **Licensing**: Open source, permissive licenses
6. **Maintenance**: Active development, security updates

---

## Cross-References

- **Core Concepts**: [../core-concepts/](../core-concepts/)
- **Architecture**: [../architecture/](../architecture/)
- **Hardware Optimisation**: [../core-concepts/hardware-optimisation.md](../core-concepts/hardware-optimisation.md)
- **Model Selection**: [../core-concepts/model-selection.md](../core-concepts/model-selection.md)

---

## Implementation Status

| Technology Area | Status | First Version |
|----------------|--------|---------------|
| Document Processing | 🟡 Planned | v0.1 |
| Offline Capability | 🟡 Planned | v0.1 |
| Streaming | 🟡 Planned | v0.2 |
| Web Frameworks | 🟡 Planned | v0.5 |

Legend: 🟢 Implemented | 🟡 Planned | 🔴 Deferred

---

**Last Updated**: 2025-11-09
**Status:** Planning phase
