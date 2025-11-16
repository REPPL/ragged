# ragged - Project Vision

## Project Overview

**ragged** is a privacy-first Retrieval-Augmented Generation (RAG) system designed for personal knowledge management, learning RAG internals, and experimentation with RAG architectures.

**Status:** Early experimental/learning phase
**License**: GPLv3
**Primary Language**: Python 3.9+
**Future**: Production version planned as "ragd" (RAG daemon)

## Why ragged?

### Problem Statement

Current challenges with existing RAG solutions:

1. **Privacy Concerns**: Most RAG systems require sending data to external APIs
2. **Cost**: Cloud-based solutions can be expensive for personal use
3. **Complexity**: Enterprise RAG tools are often overly complex for individual users
4. **Control**: Limited ability to customize and experiment with RAG components
5. **Vendor Lock-in**: Dependence on specific LLM providers or platforms

### Solution

ragged addresses these by providing:

- **100% Local Processing**: All data stays on your machine
- **Zero Cost**: No API fees, no cloud services
- **Simplicity**: Easy to set up and use
- **Flexibility**: Modular architecture for experimentation
- **Open Source**: Complete transparency and customization

## Project Goals

### Primary Goals

1. **Privacy-First Architecture**
   - All processing happens locally
   - No external API calls (unless explicitly configured)
   - Encrypted storage options

2. **Ease of Use**
   - Simple CLI interface
   - Clear documentation
   - Minimal configuration required

3. **Experimentation-Friendly**
   - Modular, pluggable components
   - Easy to swap embedding models, LLMs, chunking strategies
   - Clear abstractions for extending functionality

4. **Performance**
   - Fast document indexing
   - Sub-second query response times (where possible)
   - Efficient resource usage

### Secondary Goals

1. **Multi-Backend Support**
   - Ollama, LM Studio, llama.cpp
   - Multiple vector stores (ChromaDB, FAISS, Qdrant)
   - Various embedding models

2. **Advanced Features**
   - Semantic chunking
   - Conversation memory
   - Query history
   - Hybrid search (vector + keyword)

3. **Developer Experience**
   - Well-documented codebase
   - Comprehensive tests
   - Type hints throughout
   - Example scripts and tutorials

## Target Users

### Primary Audience

- **Privacy-conscious individuals** who want to query their personal documents
- **Developers/researchers** experimenting with RAG architectures
- **Students** learning about RAG and LLMs
- **Professionals** needing local document Q&A without cloud dependencies

### Use Cases

1. **Personal Knowledge Base**
   - Index research papers, notes, articles
   - Query across all personal documents
   - Build a "second brain" locally

2. **Research & Development**
   - Experiment with different RAG components
   - Test chunking strategies
   - Compare embedding models
   - Benchmark retrieval methods

3. **Document Analysis**
   - Legal document review
   - Technical documentation search
   - Code repository querying

4. **Learning & Education**
   - Understand RAG internals
   - Learn about vector databases
   - Explore LLM prompting techniques

## Success Criteria

### Minimum Viable Product (v0.1)

- [ ] Index local documents (PDF, TXT, MD)
- [ ] Store embeddings in ChromaDB
- [ ] Query documents via CLI
- [ ] Integration with at least one LLM backend (Ollama)
- [ ] Basic chunking strategy (recursive text splitting)
- [ ] Simple configuration via .env file

### v0.2 Milestones

- [ ] Multiple document formats (DOCX, HTML, etc.)
- [ ] Semantic chunking strategy
- [ ] LM Studio backend support
- [ ] Web UI (optional, basic)
- [ ] Query history
- [ ] Improved context assembly

### v0.3 Milestones

- [ ] Conversation memory
- [ ] Hybrid search (vector + keyword)
- [ ] Multiple vector store backends
- [ ] Citation/source tracking
- [ ] Performance benchmarks

### Long-Term Vision

- **Community**: Active contributors and users
- **Extensibility**: Plugin system for custom components
- **Multi-modal**: Support for images, tables, charts
- **Collaboration**: Share indices (optionally)
- **Mobile**: iOS/Android apps for querying

## Non-Goals

What ragged is **not** trying to be:

1. **Enterprise RAG Platform**: Not targeting large organizations
2. **Cloud Service**: No hosted/SaaS offering planned
3. **General-Purpose Chatbot**: Focused on document retrieval
4. **Production Database**: Not a replacement for production data systems
5. **Data Analytics Tool**: Not for BI or complex data analysis

## Guiding Principles

### 1. Privacy First
- Default to local-only processing
- No telemetry or data collection
- User owns all data

### 2. Simplicity Over Features
- Focus on doing one thing well (RAG)
- Avoid feature bloat
- Keep configuration minimal

### 3. Transparency
- Open source everything
- Clear documentation
- No black boxes

### 4. Experimentation-Friendly
- Easy to modify and extend
- Clear abstractions
- Pluggable architecture

### 5. Performance Matters
- Fast indexing and retrieval
- Efficient resource usage
- Scalable to thousands of documents

## Technical Philosophy

### Architecture Principles

1. **Modularity**: Each component (chunking, embedding, retrieval, generation) is independent
2. **Abstraction**: Base classes for all major components
3. **Configuration**: Declarative configuration via files
4. **Testing**: Comprehensive unit and integration tests
5. **Documentation**: Code is self-documenting with clear docstrings

### Technology Choices

- **Language**: Python (widespread, great ML ecosystem)
- **Vector Store**: ChromaDB (default, simple, embedded)
- **Embeddings**: Sentence Transformers (local, fast, quality)
- **LLM**: Ollama (default, easy setup, growing ecosystem)
- **Testing**: pytest
- **Formatting**: black, ruff
- **Type Checking**: mypy

## Risks & Challenges

### Technical Risks

1. **Performance**: Local LLMs may be slow on older hardware
   - *Mitigation*: Support for quantized models, GPU acceleration

2. **Memory Usage**: Large document sets require significant RAM
   - *Mitigation*: Streaming indexing, chunked processing

3. **Quality**: Local embeddings/LLMs may not match GPT-4 quality
   - *Mitigation*: Focus on "good enough" for personal use

### Product Risks

1. **Complexity**: RAG systems can get complex quickly
   - *Mitigation*: Maintain strict scope, resist feature creep

2. **Maintenance**: Dependencies may break or become outdated
   - *Mitigation*: Minimal dependencies, regular updates

3. **Competition**: Many RAG tools emerging
   - *Mitigation*: Focus on privacy + simplicity niche

## Roadmap

### Phase 1: Foundation (Current)
**Timeline**: Month 1-2
- [x] Project setup (repo, structure, tooling)
- [ ] Basic RAG pipeline
- [ ] Document ingestion (PDF, TXT, MD)
- [ ] ChromaDB integration
- [ ] Ollama integration
- [ ] CLI interface
- [ ] Basic tests

### Phase 2: Core Features
**Timeline**: Month 3-4
- [ ] Multiple document formats
- [ ] Semantic chunking
- [ ] Additional LLM backends
- [ ] Query refinement
- [ ] Basic web UI
- [ ] Comprehensive documentation

### Phase 3: Enhancement
**Timeline**: Month 5-6
- [ ] Conversation memory
- [ ] Hybrid search
- [ ] Citation tracking
- [ ] Performance optimisations
- [ ] Additional vector stores

### Phase 4: Polish
**Timeline**: Month 7+
- [ ] Extensive testing
- [ ] Performance benchmarks
- [ ] Community feedback integration
- [ ] v1.0 release preparation

## Measuring Success

### Metrics

1. **Functionality**: Does it retrieve relevant documents?
2. **Performance**: Query response time < 2s
3. **Usability**: Can someone set it up in < 15 minutes?
4. **Privacy**: Zero external API calls by default
5. **Reliability**: Tests pass, no critical bugs

### Feedback Loops

- Personal usage (dogfooding)
- GitHub issues and discussions
- Performance benchmarks
- Code quality metrics (coverage, linting)

## Resources & References

### Inspiration

- LangChain RAG patterns
- llama-index architecture
- PrivateGPT approach
- Quivr design

### Key Papers

- "Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks" (Lewis et al., 2020)
- "Lost in the Middle: How Language Models Use Long Contexts" (Liu et al., 2023)
- "Precise Zero-Shot Dense Retrieval without Relevance Labels" (Gao et al., 2022)

### Communities

- Ollama Discord
- r/LocalLLaMA
- Hugging Face forums

---

**Document Version**: 1.0
**Last Updated**: 2025-11-02
**Owner**: REPPL
**Status:** Living document (update as project evolves)
