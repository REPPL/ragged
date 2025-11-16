# Version 0.1: Foundation & Basic RAG

**Status:** ✅ Implemented (v0.1.0 released)
**Implemented:** November 2025
**Last Updated**: 2025-11-16

## Overview

Version 0.1 establishes the foundation of ragged with basic RAG functionality via a command-line interface.

**Goal**: Prove the concept and create a working RAG system that can ingest documents and answer questions locally.

**For implementation details, see:**
- [Implementation Records](../../../implementation/version/v0.1/) - What was actually built

---

## Core Features

### Document Ingestion
- **Formats Supported**: PDF, TXT, Markdown, HTML
- **Processing**: Basic text extraction and chunking
- **Storage**: Local filesystem + vector database

### Query & Retrieval
- **Interface**: Command-line (CLI)
- **Search**: Semantic similarity using embeddings
- **Results**: Top-k relevant chunks

### Answer Generation
- **LLM**: Ollama integration (local models)
- **Responses**: Basic answer generation
- **Citations**: Show source documents and chunks

### Configuration
- **Settings**: Simple YAML configuration
- **Models**: Configurable embedding and LLM models
- **Storage**: Configurable data directory

---

## Technical Stack

### Core Components
- **Python 3.10+**
- **LLM Backend**: Ollama
- **Vector Database**: ChromaDB or Qdrant (TBD)
- **Embeddings**: sentence-transformers
- **Document Processing**: PyPDF2, python-docx, beautifulsoup4

### Architecture
- Modular design with clear component separation
- SQLite for metadata storage
- Local vector storage
- Configurable via YAML

---

## Success Criteria

✅ **Functional Requirements**:
1. Can ingest PDF, TXT, MD files successfully
2. Can embed documents and store in vector DB
3. Can retrieve relevant chunks for queries
4. Can generate answers with citations
5. CLI works end-to-end

✅ **Quality Requirements**:
1. Retrieval relevance > 70% (manual evaluation)
2. Answer faithfulness > 80% (based on sources)
3. End-to-end query time < 5 seconds (simple docs)

✅ **Documentation**:
1. Basic installation instructions
2. CLI usage documentation
3. Configuration guide

---

## Out of Scope

❌ **Not in v0.1**:
- Web interface (v0.2)
- Advanced retrieval strategies (v0.3)
- Knowledge graphs (v0.4)
- Self-improvement (v0.4)
- Multi-document reasoning (v0.5)
- Production optimisation (v1.0)

---

## Coming Soon

Detailed specifications will include:
- Component architecture diagrams
- API design
- Database schema
- CLI command structure
- Configuration format
- Testing strategy
- Evaluation approach

---

## Related Documentation

- **[Implementation Plan](../../README.md)** - Overall roadmap
- **[Architecture](../../architecture/README.md)** - System architecture
- **[v0.2 Plan](../v0.2/)** - Next version

---

*This version specification will be expanded before implementation begins*
