# ragged Implementation Plan (2025 Edition)

**Status**: Planning - No code implemented yet
**Last Updated**: 2025-11-08
**Architecture Version**: 2025 State-of-the-Art

---

## Table of Contents

- [Overview](#overview)
- [Purpose](#purpose)
- [Structure](#structure)
- [Key Documents](#key-documents)
- [Implementation Roadmap](#implementation-roadmap)
  - [Version 0.1: MVP - Foundation](#version-01-mvp---foundation-2-3-weeks)
  - [Version 0.2: Document Normalisation + Enhanced Retrieval + Web UI](#version-02-document-normalisation--enhanced-retrieval--web-ui-6-7-weeks)
  - [Version 0.3: Advanced Chunking + Enhanced UI](#version-03-advanced-chunking--enhanced-ui-3-4-weeks)
  - [Version 0.4: Adaptive Systems + Developer Mode](#version-04-adaptive-systems--developer-mode-4-5-weeks)
  - [Version 0.5: Knowledge Graphs + Svelte Rebuild](#version-05-knowledge-graphs--svelte-rebuild-5-6-weeks)
  - [Version 1.0: Production Ready + Stable API](#version-10-production-ready--stable-api-4-6-weeks)
- [Development Workflow](#development-workflow)
- [Principles](#principles)
- [Technology Standards](#technology-standards)
- [Using This Plan](#using-this-plan)
- [Version Control](#version-control)
- [Contributing](#contributing)
- [License](#license)
- [Acknowledgements](#acknowledgements)

---

## Overview

This directory contains the complete implementation plan for **ragged**, a privacy-first local RAG system designed for learning, experimentation, and eventually production use. The plan incorporates state-of-the-art RAG techniques from 2025 research while maintaining the core principles of privacy, modularity, and local processing.

## Purpose

This implementation plan serves multiple purposes:

1. **Development Blueprint**: Step-by-step guide for building ragged
2. **Academic Reference**: Transparent documentation of AI-assisted development process
3. **Learning Resource**: Educational material for understanding modern RAG systems
4. **Design Documentation**: Architecture decisions and trade-offs

## Structure

```
docs/implementation/plan/
├── README.md                      # This file - overview and navigation
├── architecture/                  # State-of-the-art RAG architecture
│   └── README.md                  # Main architecture document
├── PROJECT-VISION.md              # Goals, principles, and success criteria
├── DEVELOPMENT-GUIDE.md           # How to use this plan for development
│
├── versions/                      # Version-specific implementation plans
│   ├── v0.1/                      # MVP - Basic RAG
│   │   ├── README.md              # Version overview
│   │   ├── features.md            # Feature specifications
│   │   ├── architecture.md        # Technical architecture
│   │   ├── implementation.md      # Build instructions
│   │   └── testing.md             # Test strategy
│   ├── v0.2/                      # Enhanced Retrieval
│   ├── v0.3/                      # Advanced Chunking
│   ├── v0.4/                      # Adaptive Systems
│   ├── v0.5/                      # Knowledge Graphs
│   └── v1.0/                      # Production Ready
│
├── core-concepts/                 # Foundational documentation
│   ├── rag-fundamentals.md        # RAG principles and research
│   ├── privacy-architecture.md    # Privacy-first design
│   ├── modularity.md              # Plugin architecture
│   ├── evaluation.md              # Quality metrics and testing
│   ├── progressive-disclosure.md  # UI complexity management
│   └── versioning-philosophy.md   # Breaking changes policy (pre/post v1.0)
│
├── technology-stack/              # Technology decisions
│   ├── embeddings.md              # Embedding model choices
│   ├── vector-stores.md           # Vector database options
│   ├── llm-backends.md            # LLM integration
│   ├── chunking-strategies.md     # Document chunking approaches
│   ├── reranking.md               # Reranking techniques
│   ├── web-frameworks.md          # FastAPI, Gradio, Svelte comparison
│   ├── streaming.md               # SSE vs WebSockets for token streaming
│   └── offline-capability.md      # PWA, privacy-first web design
│
├── advanced-features/             # Future enhancements
│   ├── graph-rag.md               # GraphRAG implementation
│   ├── self-rag.md                # Self-reflective RAG
│   ├── adaptive-retrieval.md      # Dynamic strategy selection
│   ├── hybrid-search.md           # Vector + keyword fusion
│   └── multi-modal.md             # Image, audio, video support
│
└── references/                    # External resources
    ├── research-papers.md         # Academic papers (2024-2025)
    ├── best-practices.md          # Industry standards
    ├── tools-and-libraries.md     # Ecosystem overview
    └── benchmarks.md              # Performance comparisons
```

## Key Documents

### Essential Reading (Start Here)

1. **[PROJECT-VISION.md](./PROJECT-VISION.md)** - Why ragged exists, goals, non-goals
2. **[Architecture](./architecture/README.md)** - Complete system architecture
3. **[DEVELOPMENT-GUIDE.md](./DEVELOPMENT-GUIDE.md)** - How to use this plan

### Version Documentation

Each version (v0.1 through v1.0) contains:
- **README.md**: Version overview and objectives
- **features.md**: Feature specifications and requirements
- **architecture.md**: Technical architecture for that version
- **implementation.md**: Step-by-step build instructions
- **testing.md**: Test strategy and success criteria

### Core Concepts

- **[rag-fundamentals.md](./core-concepts/rag-fundamentals.md)**: RAG theory and research basis
- **[privacy-architecture.md](./core-concepts/privacy-architecture.md)**: How we maintain 100% local processing
- **[modularity.md](./core-concepts/modularity.md)**: Plugin system and extensibility
- **[evaluation.md](./core-concepts/evaluation.md)**: Quality metrics (RAGAS, etc.)

### Technology Stack

- **[embeddings.md](./technology-stack/embeddings.md)**: Sentence Transformers, Qwen3, comparison
- **[vector-stores.md](./technology-stack/vector-stores.md)**: ChromaDB, Qdrant, migration path
- **[llm-backends.md](./technology-stack/llm-backends.md)**: Ollama, MLX, integration patterns
- **[chunking-strategies.md](./technology-stack/chunking-strategies.md)**: Recursive, semantic, late chunking
- **[reranking.md](./technology-stack/reranking.md)**: Cross-encoder, MMR, LLM-based
- **[web-frameworks.md](./technology-stack/web-frameworks.md)**: FastAPI, Gradio, Svelte comparison
- **[streaming.md](./technology-stack/streaming.md)**: SSE vs WebSockets
- **[offline-capability.md](./technology-stack/offline-capability.md)**: PWA, privacy-first web

## Implementation Roadmap

### Version 0.1: MVP - Foundation (2-3 weeks)
**Status**: Not started
**Goal**: Basic functional RAG system

Core features:
- Basic RAG pipeline with recursive chunking
- ChromaDB vector storage
- Ollama integration
- Simple CLI
- PDF, TXT, MD support

→ **See [versions/v0.1/](./versions/v0.1/)**

### Version 0.2: Document Normalisation + Enhanced Retrieval + Web UI (6-7 weeks)
**Status**: Not started
**Goal**: ⭐ **Production-quality document processing** + improved retrieval + basic web interface

Core features:
- **🔑 Document Normalisation Pipeline** (+2 weeks - KEY FEATURE):
  - All formats → Markdown (PDF, HTML, DOCX, scanned images)
  - Format-specific processors: Docling (PDF), Trafilatura (HTML), PaddleOCR (scanned)
  - Metadata extraction: GROBID (academic papers), Trafilatura (web articles)
  - Duplicate detection: SHA256 (exact) + MinHash+LSH (near-duplicates)
  - SQLite metadata database
- **Enhanced Retrieval**:
  - Hybrid search (BM25 + vector)
  - Cross-encoder reranking
  - Query expansion
  - Metadata filtering
  - Caching layer
- **Basic Gradio Web UI**:
  - Simple chat interface with streaming (SSE)
  - Document upload interface
  - Basic citations with page numbers
  - FastAPI backend

→ **See [versions/v0.2/](./versions/v0.2/)** | **[Web UI Specs](./versions/v0.2/web-ui-basic.md)** | **[Doc Processing](./core-concepts/document-normalisation.md)**

### Version 0.3: Advanced Chunking + Enhanced UI (3-4 weeks)
**Status**: Not started
**Goal**: Optimise chunking + progressive disclosure

Core features:
- Semantic chunking
- Late chunking
- Structure-aware splitting
- Table/code preservation
- **Enhanced Gradio UI**:
  - Progressive disclosure (advanced settings)
  - Conversation history
  - Enhanced citations (confidence, pages)
  - Collection management UI

→ **See [versions/v0.3/](./versions/v0.3/)** | **[Web UI Specs](./versions/v0.3/web-ui-enhanced.md)**

### Version 0.4: Adaptive Systems + Developer Mode (4-5 weeks)
**Status**: Not started
**Goal**: Self-improving retrieval + technical visibility

Core features:
- Self-RAG with confidence scoring
- Adaptive retrieval strategies
- Query complexity analysis
- Hallucination detection
- **Developer Mode UI**:
  - Query inspector (rewrites, decomposition)
  - Retrieval details view (scores, timing)
  - Performance dashboard
  - Self-RAG visualization

→ **See [versions/v0.4/](./versions/v0.4/)** | **[Web UI Specs](./versions/v0.4/web-ui-technical.md)**

### Version 0.5: Knowledge Graphs + Svelte Rebuild (5-6 weeks)
**Status**: Not started
**Goal**: Relationship-aware retrieval

Core features:
- GraphRAG implementation
- Entity extraction
- Relationship mapping
- Multi-hop reasoning
- **🚨 Svelte/SvelteKit UI Rebuild** (breaking change):
  - Clean rebuild (not migration)
  - Graph visualization
  - Document preview with highlights
  - Split-view interface
  - Production design system

→ **See [versions/v0.5/](./versions/v0.5/)** | **[Web UI Specs](./versions/v0.5/web-ui-rebuild.md)**

### Version 1.0: Production Ready + Stable API (4-6 weeks)
**Status**: Not started
**Goal**: Production deployment + API stability commitment

Core features:
- Plugin architecture
- Monitoring and logging
- Performance optimisation
- Deployment automation
- Comprehensive documentation
- **Production Web UI**:
  - PWA with offline support
  - API documentation UI (Swagger)
  - Admin panel
  - Monitoring dashboard
  - **🎯 API freeze** (semver begins)

→ **See [versions/v1.0/](./versions/v1.0/)** | **[Web UI Specs](./versions/v1.0/web-ui-production.md)**

## Development Workflow

### Phase 1: Planning (Current)
- Review all documentation
- Understand architecture
- Set up development environment
- Create project structure

### Phase 2: Implementation (Per Version)
1. Read version README and feature specs
2. Follow implementation guide step-by-step
3. Implement features with tests
4. Validate against success criteria
5. Document what was actually built

### Phase 3: Validation
- Run test suite
- Evaluate with RAGAS metrics
- Performance benchmarking
- Documentation review

### Phase 4: Iteration
- Collect feedback
- Identify improvements
- Update plan for next version
- Archive completed version docs

## Principles

### 1. Privacy First
All processing must remain 100% local by default. External APIs only with explicit user configuration and consent.

### 2. Incremental Development
Each version builds on the previous. No big-bang rewrites. Progressive enhancement.

### 3. Test-Driven
Write tests alongside code. Maintain >80% coverage. Use RAGAS for quality evaluation.

### 4. Documentation-Driven
Document design before implementation. Update docs as you build. British English throughout.

### 5. Learning-Focused
Code should be readable and educational. Prioritize clarity over cleverness. Comment complex logic.

## Technology Standards

### Code Style
- **Language**: Python 3.10+
- **Formatter**: black (--skip-string-normalisation)
- **Linter**: ruff
- **Type Checker**: mypy
- **Quotes**: Single quotes for strings, double for docstrings

### Documentation Style
- **Language**: British English (organise, colour, behaviour)
- **Format**: Markdown (GitHub-flavored)
- **Commit Messages**: Conventional Commits
- **Docstrings**: Google style

### Testing Standards
- **Framework**: pytest
- **Coverage**: Minimum 80%
- **Quality**: RAGAS evaluation framework
- **Mocking**: Use unittest.mock for external services

## Using This Plan

### For Development
1. Start with v0.1 README
2. Follow implementation guide
3. Run tests continuously
4. Document deviations from plan

### For Learning
1. Read architecture/README.md first
2. Study core concepts
3. Review technology choices
4. Understand trade-offs

### For Academic Research
1. This entire plan is version-controlled
2. Compare plan vs actual implementation
3. Study AI-assisted development process
4. Cite using git commit hash

## Version Control

This plan is:
- **Version controlled** in git
- **Tagged** at major milestones
- **Archived** when implementation complete
- **Compared** against actual implementation

Tag format: `v0.0-plan-v0.X` for each version's plan completion

## Contributing

This is a personal learning project during initial development. Contributions will be welcomed after v0.1 is complete.

For questions or suggestions:
- GitHub Issues: https://github.com/REPPL/ragged/issues
- GitHub Discussions: https://github.com/REPPL/ragged/discussions

## License

This implementation plan, like the ragged project itself, is licensed under GPL-3.0.

## Acknowledgements

### Research Basis
- 2025 RAG research papers (see references/research-papers.md)
- Industry best practices from leading organizations
- Open source RAG implementations (LangChain, LlamaIndex, etc.)

### AI Assistance
This implementation plan was created with assistance from:
- **Claude Code** (Anthropic): Architecture design and planning
- **Model**: claude-sonnet-4-5-20250929
- **Date**: 2025-11-08

### Community
- Ollama project for local LLM inference
- ChromaDB and Qdrant teams for vector storage
- Sentence Transformers community
- Open source RAG community

---

**Next Steps**: Read [PROJECT-VISION.md](./PROJECT-VISION.md) to understand the goals, then dive into [architecture/README.md](./architecture/README.md) for the technical design.

**Current Status**: Planning phase - no code implemented yet. Ready to begin v0.1 development.
