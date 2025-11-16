# RAG Fundamentals

**Status:** 🚧 Coming Soon
**Last Updated**: 2025-11-09

## Overview

This document covers the technical fundamentals of RAG (Retrieval-Augmented Generation) systems as implemented in ragged.

---

## Coming Soon

This document will cover:

### RAG Architecture
- **Retrieval Pipeline**: Document processing, embedding, indexing
- **Augmentation Layer**: Context assembly, prompt construction
- **Generation Component**: LLM integration, response formatting

### Document Processing
- **Ingestion**: File parsing and text extraction
- **Normalisation**: Structure preservation, cleaning
- **Chunking Strategies**:
  - Fixed-size chunking
  - Semantic chunking
  - Document structure-aware chunking
  - Overlap and context windows

### Embeddings
- **Embedding Models**: Selection criteria and trade-offs
- **Embedding Generation**: Batch processing, caching
- **Vector Representation**: Dimensionality and performance

### Vector Storage
- **Database Options**: ChromaDB vs Qdrant
- **Indexing Strategies**: HNSW, IVF
- **Similarity Search**: Metrics (cosine, dot product, Euclidean)
- **Performance Optimisation**: Index tuning, query optimisation

### Retrieval Strategies
- **Semantic Search**: Dense vector retrieval
- **Keyword Search**: BM25, TF-IDF
- **Hybrid Retrieval**: Combining semantic and keyword approaches
- **Reranking**: Cross-encoder models, score fusion

### Context Assembly
- **Chunk Selection**: Top-k selection, threshold filtering
- **Context Ordering**: Relevance vs document order
- **Metadata Integration**: Using document/chunk metadata
- **Context Window Management**: Fitting within LLM limits

### Generation
- **LLM Integration**: Ollama, OpenAI-compatible APIs
- **Prompt Engineering**: RAG-specific prompts
- **Citation Generation**: Source attribution
- **Response Streaming**: Real-time output

### Advanced Techniques
- **Self-RAG**: Self-reflective retrieval and generation
- **GraphRAG**: Knowledge graph integration
- **Adaptive RAG**: Dynamic strategy selection
- **Multi-hop Reasoning**: Query decomposition and chaining

### Evaluation
- **Retrieval Metrics**:
  - Precision, Recall, F1
  - MRR (Mean Reciprocal Rank)
  - NDCG (Normalised Discounted Cumulative Gain)
- **Generation Metrics**:
  - Faithfulness (answer grounded in context)
  - Relevance (answer addresses question)
  - Citation accuracy
- **End-to-end Evaluation**: User satisfaction, task completion

---

## Related Documentation

- **[Architecture](../architecture/README.md)** - System architecture
- **[Technologies](../technologies/README.md)** - Technology stack
- **[Model Selection](model-selection.md)** - Model selection criteria

---

*This document will be expanded during v0.1 implementation with specific technical details and code examples*
