# Background Research

Research, best practices, and technical background that informed ragged's design and technology choices.

## Contents

### [RAG Research](./rag.md)
Comprehensive research on state-of-the-art RAG systems for Mac M4.

- Performance expectations and model selection
- Vector database comparison and hybrid retrieval
- Document processing and chunking strategies
- Framework selection and modular architecture
- Monitoring, evaluation, and production deployment
- Memory optimisation for M4 Max
- Emerging patterns and future directions

This document captures the research foundation for ragged's architecture.

### [Technology Comparisons](./technology-comparisons.md)
Detailed comparisons of technology choices.

- **Vector Databases**: ChromaDB vs Qdrant vs FAISS
- **Embedding Models**: Qwen3 vs BGE vs Sentence-BERT
- **LLM Backends**: Ollama vs MLX vs llama.cpp
- **Model Selection**: 7B vs 24B vs 70B parameter models
- **Document Processing**: PyMuPDF vs Docling vs Unstructured
- **Frameworks**: LlamaIndex vs LangChain vs direct implementation
- **Chunking**: Semantic vs Recursive vs Fixed-size
- **Platform**: M4 Max vs NVIDIA RTX 4090

Each comparison explains the trade-offs and why ragged chose specific technologies.

### [Best Practices](./best-practices.md)
Industry best practices for RAG systems.

- **Document Processing**: Chunking, tables, metadata extraction
- **Retrieval Strategies**: Hybrid search, parameters, context assembly
- **Generation**: Prompt engineering, response quality
- **Configuration**: Modular design, progressive enhancement
- **Evaluation**: Metrics, frameworks, continuous monitoring
- **Memory & Performance**: M4 Max optimisation, scalability
- **Production**: Architecture patterns, API design, observability
- **Advanced Patterns**: Multi-modal RAG, graph integration, agentic RAG

Proven patterns extracted from research and real-world implementations.

### [Resources](./resources.md)
Curated collection of papers, tools, and communities.

- **Foundational Papers**: RAG core concepts, context, advanced techniques
- **Embedding Models**: Popular models and MTEB leaderboard
- **Vector Databases**: Embedded, local, and production-grade options
- **LLM Backends**: Ollama, LM Studio, llama.cpp, model sources
- **Document Processing**: Python libraries for PDF, DOCX, HTML
- **RAG Frameworks**: LangChain, LlamaIndex, Haystack
- **Evaluation**: RAGAS, TruLens, BEIR, KILT
- **Communities**: Discord, Reddit, forums

Links to papers, tools, and resources for deeper learning.

## How to Use This Documentation

### Understanding Design Choices

1. Read [RAG Research](./rag.md) for the research landscape
2. Check [Technology Comparisons](./technology-comparisons.md) for specific choices
3. Review [Best Practices](./best-practices.md) for implementation patterns
4. Explore [Resources](./resources.md) for deeper dive

### Evaluating Alternatives

Wondering why ragged chose ChromaDB over Qdrant? Or Ollama over MLX?

→ See [Technology Comparisons](./technology-comparisons.md)

### Learning RAG Best Practices

Want to understand chunking strategies, hybrid search, or evaluation metrics?

→ See [Best Practices](./best-practices.md)

### Further Research

Looking for papers, tools, or communities?

→ See [Resources](./resources.md)

## Key Insights

### Technology Stack Rationale

**Current Stack** (v0.1.0):
- ChromaDB (simple, Python-native, good for development)
- all-MiniLM-L6-v2 (proven, widely used)
- Ollama (easiest setup, good ecosystem)
- PyMuPDF (available, simple integration)
- Recursive chunking (20-30% less computation, often better quality)
- Direct implementation (no framework lock-in)

**Production Path** (future):
- Qdrant (when scaling >1M vectors)
- Qwen3-4B-4bit via MLX (5-8x faster embeddings)
- MLX (20-30% faster LLM inference)
- PyMuPDF4llm or Unstructured (better structure preservation)
- Hybrid search (12-30% accuracy improvement)

### M4 Max Advantages

The M4 Max with 128GB unified memory provides:
- No CPU-GPU transfer bottlenecks
- Multiple models in memory simultaneously
- 5-15x better performance than multi-GPU setups for large models
- 150W vs 600-700W power consumption
- Practical for 24/7 operation

This informed ragged's architecture and model choices.

### Best Practice Highlights

- **Start simple**: Linear pipeline, proven components, measure first
- **Modular design**: Independent component evolution and A/B testing
- **Configuration-driven**: Experiments without code changes
- **Progressive enhancement**: Add complexity only where justified by metrics
- **Monitor both**: Technical metrics AND quality metrics

## Related Documentation

- **[Architecture](../architecture/)** - How these research insights informed the design
- **[Decisions](../decisions/)** - ADRs explaining specific choices
- **[Terminology](../terminology/)** - Key concepts and glossary
- **[User Guide: Document Processing](../../user-guides/features/document-processing.md)** - Using these technologies

---

**Purpose**: Research foundation for ragged's design
**Audience**: Developers, researchers, and those evaluating alternatives
