# Reranking

**Status**: 🚧 Coming Soon
**Last Updated**: 2025-11-09

## Overview

This document covers reranking strategies to improve retrieval quality by refining initial search results in ragged's RAG pipeline.

---

## Coming Soon

This document will cover:

### Why Reranking?

#### The Two-Stage Retrieval Problem
**Stage 1: Candidate Retrieval**
- Fast vector similarity search
- Retrieve top-k candidates (k=50-100)
- May include some irrelevant results
- Recall-focused

**Stage 2: Reranking**
- Slower, more accurate scoring
- Rerank top-k to get best top-n (n=5-10)
- Higher precision
- Quality-focused

#### Benefits
- **Better Precision**: More relevant results
- **Answer Quality**: Better context for LLM
- **User Experience**: More accurate citations
- **Efficiency**: Only rerank promising candidates

### Reranking Strategies

#### 1. Cross-Encoder Reranking (v0.3+)
**Method**: Use a cross-encoder model to score query-document pairs

**How it Works**:
```
Input: [query, document_chunk] → Cross-Encoder → Relevance Score
```

**Models**:
- **ms-marco-MiniLM-L-6-v2**: Fast, good quality
- **ms-marco-MiniLM-L-12-v2**: Better quality, slower
- **cross-encoder/ms-marco-electra-base**: Highest quality

**Pros**:
- ✅ More accurate than bi-encoders
- ✅ Considers query-document interaction
- ✅ Proven effectiveness

**Cons**:
- ⚠️ Slower than vector similarity
- ⚠️ Must run for each query-chunk pair
- ⚠️ Not suitable for initial retrieval

**Implementation**:
```python
from sentence_transformers import CrossEncoder

model = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')

# Get initial candidates
candidates = vector_store.search(query, k=50)

# Rerank
pairs = [[query, chunk.text] for chunk in candidates]
scores = model.predict(pairs)

# Sort by reranked scores
reranked = sorted(
    zip(candidates, scores),
    key=lambda x: x[1],
    reverse=True
)

# Return top-n
top_results = reranked[:10]
```

#### 2. BM25 + Vector Hybrid (v0.2+)
**Method**: Combine keyword search (BM25) with semantic search

**Score Fusion**:
- **Linear**: `score = α * vector_score + (1-α) * bm25_score`
- **Reciprocal Rank Fusion**: Combine rankings not scores
- **Weighted**: Different weights per retrieval method

**Pros**:
- ✅ Best of keyword and semantic search
- ✅ Handles both conceptual and exact matches
- ✅ Mitigates semantic search weaknesses

**Cons**:
- ⚠️ Requires BM25 index
- ⚠️ Score normalisation needed
- ⚠️ Weight tuning required

**Implementation**:
```python
def hybrid_search(query, k=10, alpha=0.5):
    # Vector search
    vector_results = vector_store.search(query, k=50)

    # BM25 search
    bm25_results = bm25_index.search(query, k=50)

    # Reciprocal Rank Fusion
    scores = defaultdict(float)
    for rank, doc in enumerate(vector_results):
        scores[doc.id] += 1.0 / (rank + 60)
    for rank, doc in enumerate(bm25_results):
        scores[doc.id] += 1.0 / (rank + 60)

    # Sort and return top-k
    reranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    return [doc_store[doc_id] for doc_id, _ in reranked[:k]]
```

#### 3. LLM-based Reranking (v0.4+)
**Method**: Use LLM to judge relevance

**Prompt**:
```
Given a query and a document chunk, rate the relevance from 0-10.

Query: {query}
Chunk: {chunk}

Relevance Score (0-10):
```

**Pros**:
- ✅ Most accurate
- ✅ Can consider nuanced relevance
- ✅ Adapts to query complexity

**Cons**:
- ❌ Very slow
- ❌ Expensive (LLM calls)
- ❌ Overkill for most use cases

**Use Case**: Premium quality mode, small result sets

#### 4. Metadata-Based Reranking
**Method**: Boost/demote based on metadata

**Factors**:
- **Recency**: Prefer recent documents
- **Source**: Boost authoritative sources
- **Section**: Boost relevant sections (e.g., "Methods" for methodology questions)
- **User Preferences**: Personal ranking preferences

**Implementation**:
```python
def metadata_rerank(results, query_metadata):
    for result in results:
        # Base score from retrieval
        score = result.score

        # Recency boost
        if result.date > recent_threshold:
            score *= 1.2

        # Section relevance
        if query_metadata.get('section') == result.section:
            score *= 1.3

        # Source authority
        if result.source in trusted_sources:
            score *= 1.1

        result.reranked_score = score

    return sorted(results, key=lambda x: x.reranked_score, reverse=True)
```

### Reranking Pipeline

#### v0.2: Hybrid Retrieval
```python
def retrieve_with_reranking(query, k=10):
    # Stage 1: Initial retrieval
    candidates = vector_store.search(query, k=50)

    # Stage 2: BM25 fusion
    reranked = hybrid_rerank(query, candidates)

    return reranked[:k]
```

#### v0.3: Cross-Encoder
```python
def retrieve_with_cross_encoder(query, k=10):
    # Stage 1: Fast vector retrieval
    candidates = vector_store.search(query, k=100)

    # Stage 2: Cross-encoder reranking
    reranked = cross_encoder_rerank(query, candidates)

    # Stage 3: Metadata boosting
    final = metadata_boost(reranked)

    return final[:k]
```

#### v0.4: Adaptive Reranking
```python
def adaptive_reranking(query, k=10):
    # Analyse query complexity
    complexity = analyse_query(query)

    # Choose strategy
    if complexity == 'simple':
        return vector_search(query, k)
    elif complexity == 'medium':
        return hybrid_search(query, k)
    else:  # complex
        return full_reranking_pipeline(query, k)
```

### Optimisation

#### Performance
- **Batch Processing**: Rerank in batches
- **Caching**: Cache reranking results
- **Early Stopping**: Stop if confidence high enough
- **Parallel Processing**: Rerank chunks in parallel

#### Quality
- **Model Selection**: Balance speed vs accuracy
- **Parameter Tuning**: Optimise k, fusion weights
- **Evaluation**: A/B test reranking strategies

### Evaluation

#### Metrics
- **Precision@k**: Relevant docs in top-k
- **NDCG**: Ranking quality
- **MRR**: First relevant result position
- **Latency**: Added reranking time

#### Baselines
- **No Reranking**: Vector search only
- **BM25 Only**: Keyword search only
- **Hybrid**: Combined approach
- **Cross-Encoder**: Deep reranking

### Version Roadmap

#### v0.1: Vector Search Only
- No reranking
- Baseline performance
- Simple and fast

#### v0.2: Hybrid Retrieval
- BM25 + Vector fusion
- Reciprocal rank fusion
- Configurable weights

#### v0.3: Cross-Encoder
- Cross-encoder reranking
- Metadata boosting
- Quality improvements

#### v0.4: Adaptive Strategy
- Query complexity analysis
- Strategy selection
- LLM-based reranking (optional)

#### v1.0: Optimised Defaults
- Benchmarked strategies
- Automatic tuning
- Performance optimised

---

## Related Documentation

- **[RAG Fundamentals](../core-concepts/rag-fundamentals.md)** - RAG technical background
- **[Embeddings](embeddings.md)** - Embedding models
- **[Vector Stores](vector-stores.md)** - Vector search
- **[Evaluation](../core-concepts/evaluation.md)** - Evaluation metrics

---

*This document will be expanded with benchmarks and specific reranking model comparisons*
