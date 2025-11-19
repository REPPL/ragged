# Embedding Models

**Status:** 🚧 Coming Soon

## Overview

This document covers the selection, evaluation, and implementation of embedding models for ragged's semantic search capabilities.

---

## Coming Soon

This document will cover:

### Embedding Fundamentals

#### What are Embeddings?
- Vector representations of text
- Semantic similarity in vector space
- Dimensionality and trade-offs
- Quality vs performance balance

#### Role in RAG
- Document chunk embedding
- Query embedding
- Semantic similarity search
- Retrieval quality impact

### Model Selection Criteria

#### Quality Metrics
- **MTEB Score**: Massive Text Embedding Benchmark
- **Domain Relevance**: General vs domain-specific
- **Language Support**: English, multilingual
- **Retrieval Performance**: Precision and recall

#### Practical Constraints
- **Model Size**: Disk space and memory requirements
- **Inference Speed**: Latency per embedding
- **Hardware Compatibility**: CPU vs GPU
- **Privacy**: Local vs cloud-based

### Candidate Models

#### sentence-transformers (Default - v0.1)
**Model**: `all-MiniLM-L6-v2`
- **Dimensions**: 384
- **Size**: ~80MB
- **Performance**: Fast, CPU-friendly
- **Quality**: Good for general retrieval
- **Privacy**: 100% local

**Model**: `all-mpnet-base-v2`
- **Dimensions**: 768
- **Size**: ~420MB
- **Performance**: Moderate speed
- **Quality**: Better than MiniLM
- **Privacy**: 100% local

#### Ollama Embeddings
**Model**: `nomic-embed-text`
- **Dimensions**: 768
- **Integration**: Native with Ollama
- **Performance**: Good
- **Privacy**: 100% local

#### OpenAI Embeddings (Optional)
**Model**: `text-embedding-3-small`
- **Dimensions**: 1536
- **Quality**: Excellent
- **Performance**: Cloud latency
- **Privacy**: ⚠️ Cloud-based (opt-in only)
- **Cost**: $0.02 per 1M tokens

### Implementation

#### Local Embeddings (v0.1)
```python
from sentence_transformers import SentenceTransformer

model = SentenceTransformer('all-MiniLM-L6-v2')
embeddings = model.encode(texts, show_progress_bar=True)
```

#### Ollama Integration
```python
import ollama

response = ollama.embeddings(
    model='nomic-embed-text',
    prompt=text
)
embedding = response['embedding']
```

#### Batch Processing
- Efficient batching for throughput
- GPU acceleration when available
- Progress tracking for large datasets
- Caching for repeated queries

### Optimisation Strategies

#### Model Quantisation
- INT8 quantisation for smaller size
- Performance vs quality trade-offs
- Hardware acceleration support

#### Caching
- Query embedding cache
- Document embedding persistence
- Cache invalidation strategy

#### Hardware Acceleration
- GPU inference when available
- ONNX runtime optimisation
- Apple Silicon optimisation (Metal)

### Evaluation

#### Quality Metrics
- Retrieval precision@k
- Mean reciprocal rank (MRR)
- NDCG score
- Domain-specific benchmarks

#### Performance Metrics
- Embeddings per second
- Memory usage
- Latency (p50, p95, p99)
- Throughput with batching

### Version Roadmap

#### v0.1: Basic Local Embeddings
- sentence-transformers default
- CPU-optimised
- Simple configuration

#### v0.2: Model Selection
- User-configurable models
- Ollama integration
- Performance comparison

#### v0.3: Advanced Optimisation
- GPU acceleration
- Model quantisation
- Caching strategies

#### v1.0: Production Ready
- Optimal defaults
- Automatic hardware detection
- Comprehensive benchmarks

---

## Related Documentation

- **[Model Selection](../core-concepts/model-selection.md)** - Selection criteria
- **[Technology Stack](README.md)** - Overall stack
- **[Vector Stores](vector-stores.md)** - Storage for embeddings
- **[Hardware Optimisation](../core-concepts/hardware-optimisation.md)** - Performance tuning

---

*This document will be expanded with specific model comparisons and benchmarks*
