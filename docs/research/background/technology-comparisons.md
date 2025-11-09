# Technology Comparisons

This document compares key technology choices for RAG systems, based on research and benchmarks.

## Vector Databases

### ChromaDB vs Qdrant vs FAISS

| Feature | ChromaDB | Qdrant | FAISS |
|---------|----------|---------|-------|
| **Implementation** | Pure Python | Rust | C++ |
| **Performance** | Good for <1M vectors | 4x higher QPS | Industry standard |
| **Setup** | Zero compilation | Docker native on Apple Silicon | CPU version only on M4 |
| **Storage** | DuckDB+Parquet backend | SQLite option available | In-memory primarily |
| **Best For** | Rapid prototyping, development | Production, scalability | Research, algorithmic flexibility |
| **Latency** | Moderate | Sub-30ms p95 for 1M+ vectors | Very fast |
| **Special Features** | Embedded mode | Payload filtering, scalar quantization, disk offloading | Multiple index types (IVFFlat, HNSW, PQ) |

**Our Choice**: **ChromaDB** for development and small-scale deployments
- Zero compilation required
- Pure Python simplicity
- Excellent for <1M vectors
- Easy embedded mode

**Migration Path**: Qdrant for production when scaling beyond 1M vectors or requiring advanced features.

## Embedding Models

### Qwen3 vs BGE vs Sentence-BERT

| Model | Tokens/sec (M4 Max est.) | Dimensions | Size | Best For |
|-------|-------------------------|------------|------|----------|
| **Qwen3-0.6B** | 44,000+ | 512 | 900MB | Speed-critical |
| **Qwen3-4B-4bit** | 20,000-26,000 | 2560 | 2.5GB | Balanced (our choice) |
| **Qwen3-8B** | 11,000+ | 4096 | 4.5GB | Maximum quality |
| **BGE-base** | 3,000-5,000 | 768 | 1GB | Good quality, moderate speed |
| **Sentence-BERT** | 2,000-4,000 | 768 | 1.2GB | Older standard |

**Our Choice**: **all-MiniLM-L6-v2** (via Sentence Transformers) for initial implementation
- Widely used and tested
- Good balance of speed and quality
- 384 dimensions (efficient storage)
- Simple integration

**Future Upgrade**: Qwen3-4B-4bit when MLX integration is implemented for 5-8x performance improvement.

## LLM Backends

### Ollama vs MLX vs llama.cpp

| Backend | Setup Difficulty | Performance (M4) | Ecosystem | Best For |
|---------|-----------------|------------------|-----------|----------|
| **Ollama** | Very Easy ⭐⭐⭐⭐⭐ | Good | Growing rapidly | Development, ease of use |
| **MLX** | Moderate ⭐⭐⭐ | Excellent (20-30% faster) | 1,000+ models | Maximum performance |
| **llama.cpp** | Moderate ⭐⭐⭐ | Very Good | Largest ecosystem | Flexibility |
| **LM Studio** | Very Easy ⭐⭐⭐⭐⭐ | Good | GUI-focused | Non-technical users |

**Our Choice**: **Ollama**
- Easiest setup
- Growing model library
- Good performance
- Active community
- Clear upgrade path to MLX for production

**Benchmark Context** (M4 Max 128GB):
- Ollama serves Llama 3.3 70B at 8-10 tokens/sec
- MLX achieves 20-30% faster inference
- Unified memory eliminates GPU transfer bottlenecks

## Model Selection

### LLM Models for RAG

| Model | Size (quantized) | Speed (tokens/sec) | Quality | RAM Required | Use Case |
|-------|-----------------|-------------------|---------|--------------|----------|
| **Qwen 2.5 7B** | 4GB | 60-70+ | Good | 8GB total | Speed-focused |
| **Mistral Small 24B** | 13GB | 30-40 | Excellent | 21GB total | Balanced (recommended) |
| **Llama 3.3 70B** | 40GB | 8-10 | Best | 55GB total | Quality-focused |

**Our Initial Choice**: **Llama 3.2 3B** or **Mistral 7B**
- Fits comfortably on modest hardware
- Fast response times
- Sufficient quality for development

**Production Recommendation**: **Mistral Small 24B** (13GB quantized)
- Near-GPT-4 quality
- 35+ tokens/sec throughput
- Leaves 100GB+ for context windows and databases

## Document Processing

### PyMuPDF4llm vs Docling vs Unstructured

| Tool | Speed | Structure Preservation | Complexity | Best For |
|------|-------|----------------------|------------|----------|
| **PyMuPDF4llm** | Fast (0.12s/page) | Good markdown output | Low | RAG applications (our choice) |
| **Docling** | Slow (2.5 min/doc first run) | Advanced layout analysis | High | Complex PDFs with tables/formulas |
| **Unstructured** | Moderate | Excellent semantic detection | Moderate | Production multi-format support |

**Our Choice**: **PyMuPDF** (standard, not 4llm variant initially)
- Available and well-tested
- Good PDF extraction
- Simple integration
- Upgrade path to PyMuPDF4llm for markdown preservation

## Framework Comparison

### LlamaIndex vs LangChain

| Aspect | LlamaIndex | LangChain |
|--------|-----------|-----------|
| **Focus** | Document-heavy RAG | Multi-agent workflows |
| **Retrieval Accuracy** | 35% better (2025 benchmarks) | Good |
| **Document Processing** | 40% faster | Moderate |
| **Learning Curve** | Gentler | Steeper |
| **Best For** | RAG applications (our choice) | Complex orchestration |

**Our Choice**: **Neither (direct implementation)**
- Full control over components
- No framework lock-in
- Simpler dependencies
- Easier to understand and debug

**When to Use Frameworks**:
- LlamaIndex: For rapid prototyping or document-heavy applications
- LangChain: For multi-agent systems or complex workflows

## Chunking Strategies

### Semantic vs Recursive vs Fixed-Size

| Strategy | Computation | Quality (2024 research) | Complexity | Best For |
|----------|-------------|------------------------|------------|----------|
| **Recursive Character** | Low | Often better than semantic | Low | Most use cases (recommended) |
| **Semantic** | High (requires embeddings) | Good for high topic diversity | High | Stitched multi-topic docs |
| **Fixed-Size** | Minimal | Poor (breaks boundaries) | Very Low | Not recommended |
| **Document-Aware** | Low | Excellent | Moderate | Structured documents |

**Our Choice**: **Recursive Character Splitting** with document awareness
- 20-30% less computation than semantic
- Often outperforms semantic on structured docs
- Respects natural boundaries ("\n\n", "\n", ". ")
- Simple to implement and tune

**Parameters**: 400-500 token chunks with 15-20% overlap (75-100 tokens)

## Platform Comparison

### M4 Max vs NVIDIA RTX 4090

| Aspect | M4 Max (128GB) | RTX 4090 (24GB) |
|--------|----------------|-----------------|
| **Large Models (32B+)** | 5-15x better | Requires model splitting |
| **Small Models (<24GB)** | Good | 2-3x faster |
| **Memory Bandwidth** | 546GB/s unified | 1008GB/s VRAM (but limited size) |
| **Power Consumption** | 150W | 600-700W (full system) |
| **24/7 Operation** | Practical | Requires cooling infrastructure |
| **Multi-Model Loading** | Excellent | Poor (limited VRAM) |

**Our Context**: M4 Max advantages
- Unified memory eliminates CPU-GPU transfers
- Can run multiple models simultaneously
- Practical for 24/7 operation
- No model splitting overhead for large models

## Summary Recommendations

**Current Stack** (v0.1.0):
- Vector DB: ChromaDB
- Embeddings: all-MiniLM-L6-v2 (Sentence Transformers)
- LLM Backend: Ollama
- Model: Llama 3.2 3B or Mistral 7B
- Document Parser: PyMuPDF
- Chunking: Recursive character splitting (500 tokens, 100 overlap)
- Framework: Direct implementation (no framework)

**Production Stack** (future):
- Vector DB: Qdrant (when scaling >1M vectors)
- Embeddings: Qwen3-4B-4bit via MLX (5-8x faster)
- LLM Backend: MLX (20-30% faster)
- Model: Mistral Small 24B
- Document Parser: PyMuPDF4llm or Unstructured
- Chunking: Document-aware recursive splitting
- Hybrid search: Add BM25 for keyword matching
