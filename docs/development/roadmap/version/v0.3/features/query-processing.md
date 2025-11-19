# Advanced Query Processing & Retrieval

State-of-the-art retrieval techniques including query decomposition, HyDE, reranking, and contextual compression for 20-30% quality improvement (MRR@10 >0.75).

## Feature Overview

Advanced Query Processing transforms ragged's retrieval pipeline from basic similarity search into a sophisticated multi-stage system that rivals commercial RAG platforms. By implementing four complementary techniques - query decomposition (splitting complex queries), HyDE (hypothetical document embeddings), cross-encoder reranking, and contextual compression - ragged achieves 20-30% improvement in retrieval quality as measured by MRR@10 (Mean Reciprocal Rank).

The challenge with basic retrieval is that user queries are often poor semantic matches for document chunks. A query like "How do the proposed methods compare to prior work?" requires retrieving multiple pieces of information and synthesising them. Query decomposition breaks this into sub-queries, retrieves for each, and merges results. HyDE generates a hypothetical answer to the query and uses that for retrieval (answers are semantically closer to documents than questions). Reranking uses cross-encoders to re-score initial results with more sophisticated models. Contextual compression extracts only relevant sentences from chunks, reducing noise.

Each technique is independently valuable (5-15% improvement) and they compose multiplicatively. The features are controlled by configuration personas: "accuracy" enables all techniques for maximum quality, "speed" disables them for fast responses, and "balanced" enables reranking only. All improvements are validated against the RAGAS baseline established in v0.3.0, enabling data-driven development.

## Design Goals

1. **Retrieval Quality**: Achieve MRR@10 >0.75 (from baseline ~0.60, representing 25% improvement)
   - Query decomposition: +10-15% on multi-part queries
   - HyDE: +5-10% on semantic queries
   - Reranking: +10-15% (most consistent)
   - Contextual compression: +5-10% (reduces noise)

2. **Measurable Improvement Per Technique**: Each technique independently validated with RAGAS
   - Baseline scores (v0.3.0): Context Precision ~0.70, Context Recall ~0.65
   - Target after v0.3.0: Context Precision >0.80, Context Recall >0.75

3. **Configuration Flexibility**: User control via personas
   - "accuracy" persona: All techniques enabled (maximum quality, ~15s latency)
   - "speed" persona: All disabled (fast, ~2s latency)
   - "balanced" persona: Reranking only (good quality, ~4s latency)
   - "custom" persona: User-defined technique combination

4. **Performance Acceptable**: Latency remains reasonable even with all techniques
   - Query decomposition: <2s
   - HyDE: <1.5s
   - Reranking: <2s
   - Contextual compression: <1s
   - Total pipeline (accuracy): <15s

5. **Robustness**: Graceful fallback when techniques fail
   - Query decomposition fails → use original query
   - HyDE generation low confidence → use original query
   - Reranking errors → use initial retrieval scores
   - Compression over-aggressive → use full chunks

## Technical Architecture

### Module Structure

```
src/
└── ragged/
    └── retrieval/
        ├── __init__.py
        ├── retriever.py                    # Pipeline orchestration (modified - 350 lines)
        │   └── class Retriever
        ├── query_decomposition.py          # Query splitting (250 lines)
        │   └── class QueryDecomposer
        ├── hyde.py                          # Hypothetical docs (200 lines)
        │   └── class HyDEGenerator
        ├── reranker.py                      # Cross-encoder reranking (250 lines)
        │   └── class Reranker
        └── compression.py                   # Context compression (280 lines)
            └── class ContextualCompressor

tests/retrieval/
├── test_query_decomposition.py             # Unit tests (200 lines)
├── test_hyde.py                             # Unit tests (180 lines)
├── test_reranker.py                         # Unit tests (200 lines)
├── test_compression.py                      # Unit tests (220 lines)
└── test_integration_pipeline.py            # E2E tests (250 lines)
```

### Data Flow

```
User Query: "How do the proposed methods compare to prior work?"
    ↓
┌───────────────────────────────────────────┐
│  [Optional] Query Decomposition           │
│  - Sub-query 1: "What methods proposed?"  │
│  - Sub-query 2: "What was prior work?"    │
│  - Sub-query 3: "How do they compare?"    │
└────────┬──────────────────────────────────┘
         ↓
   ┌─────────────┐
   │  Retrieve   │──→ For each sub-query
   │  Top-K      │    (parallel if possible)
   └──────┬──────┘
          ↓
   ┌────────────────┐
   │  Merge Results │──→ Deduplicate, weighted scoring
   └──────┬─────────┘
          ↓
┌───────────────────────────────────────────┐
│  [Optional] HyDE Enhancement              │
│  LLM generates hypothetical answer:       │
│  "The proposed methods include..."        │
│  → Embed hypothetical → Retrieve          │
└────────┬──────────────────────────────────┘
         ↓
┌───────────────────────────────────────────┐
│  Initial Retrieval (Hybrid Search)        │
│  BM25 + Dense → Top-50 chunks             │
└────────┬──────────────────────────────────┘
         ↓
┌───────────────────────────────────────────┐
│  Reranking (Cross-Encoder)                │
│  Re-score Top-50 → Top-10                 │
│  Model: ms-marco-MiniLM-L-6-v2            │
└────────┬──────────────────────────────────┘
         ↓
┌───────────────────────────────────────────┐
│  [Optional] Contextual Compression        │
│  Extract relevant sentences only          │
│  Compression ratio: 30-50%                │
└────────┬──────────────────────────────────┘
         ↓
Final Chunks (3-10) → LLM Generation
```

### API Interfaces

```python
"""Advanced query processing and retrieval."""

from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from enum import Enum


class RetrievalStrategy(Enum):
    """Retrieval strategy options."""

    HYBRID = "hybrid"  # BM25 + Dense (default)
    VECTOR_ONLY = "vector"  # Dense only
    BM25_ONLY = "bm25"  # Sparse only


@dataclass
class RetrievalConfig:
    """Configuration for retrieval pipeline."""

    # Core retrieval
    strategy: RetrievalStrategy = RetrievalStrategy.HYBRID
    top_k: int = 50
    final_k: int = 5

    # Query processing
    enable_decomposition: bool = False
    enable_hyde: bool = False
    enable_compression: bool = True

    # Reranking
    enable_reranking: bool = True
    rerank_model: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"
    rerank_to: int = 10

    # Weights (for hybrid)
    bm25_weight: float = 0.3
    vector_weight: float = 0.7


@dataclass
class SubQuery:
    """Decomposed sub-query."""

    text: str  # Sub-query text
    weight: float  # Importance weight (0-1)
    original_query: str  # Parent query


@dataclass
class RetrievedChunk:
    """Retrieved chunk with metadata."""

    content: str  # Chunk text
    score: float  # Relevance score (0-1)
    document_id: str  # Source document
    chunk_id: str  # Chunk identifier
    metadata: Dict  # Additional metadata


class QueryDecomposer:
    """Decompose complex queries into sub-queries."""

    def __init__(self, llm_client):
        """
        Initialise query decomposer.

        Args:
            llm_client: LLM client for decomposition
        """
        self.llm = llm_client
        self._cache = {}  # Cache decompositions

    def decompose(self, query: str, max_subqueries: int = 3) -> List[SubQuery]:
        """
        Decompose query into sub-queries.

        Args:
            query: User query to decompose
            max_subqueries: Maximum number of sub-queries

        Returns:
            List of sub-queries with weights

        Raises:
            DecompositionError: If decomposition fails
        """
        pass

    def should_decompose(self, query: str) -> bool:
        """
        Determine if query needs decomposition.

        Simple queries (single question) don't benefit.

        Args:
            query: User query

        Returns:
            True if decomposition recommended
        """
        pass


class HyDEGenerator:
    """Generate hypothetical documents for retrieval."""

    def __init__(self, llm_client):
        """
        Initialise HyDE generator.

        Args:
            llm_client: LLM client for generation
        """
        self.llm = llm_client

    def generate(self, query: str) -> Tuple[str, float]:
        """
        Generate hypothetical document.

        Args:
            query: User query

        Returns:
            (hypothetical_document, confidence_score)

        Raises:
            GenerationError: If generation fails
        """
        pass

    def should_use_hyde(self, query: str, confidence: float) -> bool:
        """
        Determine if HyDE result should be used.

        Low confidence generations may hurt quality.

        Args:
            query: Original query
            confidence: Generation confidence (0-1)

        Returns:
            True if HyDE should be used
        """
        pass


class Reranker:
    """Rerank chunks using cross-encoder models."""

    def __init__(
        self,
        model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2",
    ):
        """
        Initialise reranker.

        Args:
            model_name: HuggingFace cross-encoder model
        """
        self.model_name = model_name
        self._model = None  # Lazy loading

    def rerank(
        self,
        query: str,
        chunks: List[RetrievedChunk],
        top_k: int = 10,
    ) -> List[RetrievedChunk]:
        """
        Rerank chunks using cross-encoder.

        Args:
            query: User query
            chunks: Initially retrieved chunks
            top_k: Number of top results to return

        Returns:
            Reranked chunks (top-k)
        """
        pass

    def _load_model(self):
        """Lazy load cross-encoder model."""
        pass


class ContextualCompressor:
    """Extract relevant sentences from chunks."""

    def __init__(
        self,
        min_relevance: float = 0.5,
        compression_ratio: float = 0.5,
    ):
        """
        Initialise contextual compressor.

        Args:
            min_relevance: Minimum sentence relevance score
            compression_ratio: Target compression (0.5 = 50% reduction)
        """
        self.min_relevance = min_relevance
        self.compression_ratio = compression_ratio

    def compress(
        self,
        query: str,
        chunks: List[RetrievedChunk],
    ) -> List[RetrievedChunk]:
        """
        Compress chunks by extracting relevant sentences.

        Args:
            query: User query
            chunks: Retrieved chunks to compress

        Returns:
            Compressed chunks (same count, reduced content)
        """
        pass

    def _score_sentence(self, query: str, sentence: str) -> float:
        """
        Score sentence relevance to query.

        Args:
            query: User query
            sentence: Sentence to score

        Returns:
            Relevance score (0-1)
        """
        pass


class Retriever:
    """Orchestrate multi-stage retrieval pipeline."""

    def __init__(self, config: RetrievalConfig):
        """
        Initialise retriever with configuration.

        Args:
            config: Retrieval configuration
        """
        self.config = config
        self.decomposer = QueryDecomposer() if config.enable_decomposition else None
        self.hyde = HyDEGenerator() if config.enable_hyde else None
        self.reranker = Reranker() if config.enable_reranking else None
        self.compressor = ContextualCompressor() if config.enable_compression else None

    def retrieve(self, query: str) -> List[RetrievedChunk]:
        """
        Retrieve chunks using multi-stage pipeline.

        Stages (conditional on config):
        1. Query decomposition (if enabled)
        2. HyDE enhancement (if enabled)
        3. Initial retrieval (hybrid/vector/BM25)
        4. Reranking (if enabled)
        5. Contextual compression (if enabled)

        Args:
            query: User query

        Returns:
            Final retrieved chunks (config.final_k)
        """
        pass
```

### Integration Points

- **Configuration**: Controlled by `RetrievalConfig` from config personas
- **Embedding**: Uses existing embedding models for HyDE and retrieval
- **LLM**: Reuses Ollama client for decomposition and HyDE generation
- **Vector Store**: Integrates with existing ChromaDB retrieval
- **RAGAS**: Evaluated using v0.3.0 evaluation framework
- **Generation**: Final chunks passed to existing generation pipeline

## Security & Privacy

### Requirements

- **No External Calls**: All processing local (cross-encoder models, LLM local)
- **Query Caching**: Cache with session isolation (v0.2.10)
- **No Plaintext Logging**: Log query hashes only (v0.2.11)
- **Resource Limits**: Prevent DoS via query decomposition bombing

### Privacy Risk Score

**Score**: 88/100 (Excellent privacy, low risk)

**Justification**:

**Risk Factors**:
- Query decomposition creates multiple queries (more data processing)
- HyDE generates hypothetical content (could reveal query intent)
- Cached results may persist (temporary exposure)

**Mitigation**:
- All processing happens locally (no external APIs)
- Caching uses session isolation (v0.2.10)
- Query hashing for any logs (v0.2.11 `hash_query()`)
- Cache TTL cleanup (v0.2.11)
- No data transmitted externally

The high privacy score (88/100) reflects fully offline operation. The only minor risk is cached decompositions/HyDE results, mitigated by session isolation and TTL cleanup.

### Integration with Security Foundation

**Requires**: v0.2.10 (Session Isolation), v0.2.11 (Query Hashing)

**Key APIs Used**:

```python
from ragged.session import SessionManager
from ragged.privacy import hash_query

# Session-scoped caching
session = SessionManager().get_or_create_session()
cache_key = f"{session.session_id}:decomp:{hash_query(query)}"

# Query decomposition with caching
if cache_key in decomposition_cache:
    sub_queries = decomposition_cache[cache_key]
else:
    sub_queries = decomposer.decompose(query)
    decomposition_cache[cache_key] = sub_queries

# Log only hashed queries (never plaintext)
query_hash = hash_query(user_query)
logger.info(f"Processing query: {query_hash}, sub-queries: {len(sub_queries)}")
```

### Detailed Policies

- [Security Policy](../../../../security/policy.md#secure-coding-standards) - Input validation and query handling
- [Privacy Architecture](../../../../security/privacy-architecture.md#session-isolation) - Session-scoped caching

## Implementation Phases

### Phase 1: Design & Architecture (8-10h)

**Objective**: Design multi-stage retrieval pipeline and prompt engineering

**Steps**:
1. Use architecture-advisor agent for retrieval pipeline design
2. Design query decomposition prompts (how to split queries)
3. Design HyDE prompts (generate hypothetical answers)
4. Design compression algorithm (sentence extraction)
5. Plan integration with existing retrieval
6. Document architecture decisions

**Dependencies**: v0.3.0 complete (RAGAS baseline)

**Deliverables**:
- Architecture decision record
- Pipeline flow documented
- Prompt templates prepared

**Verification**:
- [ ] Architecture-advisor review complete
- [ ] Prompts validated with sample queries
- [ ] Integration plan clear

### Phase 2: Query Decomposition (12-15h)

**Objective**: Implement query splitting and result merging

**Steps**:
1. Create `src/retrieval/query_decomposition.py`
2. Implement `QueryDecomposer` class
3. Add LLM prompts for decomposition
4. Implement sub-query validation (detect failures)
5. Implement result merging with deduplication
6. Add caching mechanism
7. Create unit tests
8. Test with complex multi-part queries

**Dependencies**: Phase 1 complete

**Deliverables**:
- Query decomposition working
- Result merging functional
- Unit tests passing

**Verification**:
- [ ] Complex queries decomposed correctly
- [ ] Simple queries bypass decomposition
- [ ] Merging deduplicates results
- [ ] Caching reduces redundant calls
- [ ] Unit tests >80% coverage

### Phase 3: HyDE Implementation (6-8h)

**Objective**: Generate and use hypothetical documents

**Steps**:
1. Create `src/retrieval/hyde.py`
2. Implement `HyDEGenerator` class
3. Add prompts for hypothetical answer generation
4. Integrate with embedding pipeline
5. Add confidence scoring (detect low-quality generations)
6. Implement fallback to original query
7. Create unit tests

**Dependencies**: Phase 1 complete (parallel to Phase 2)

**Deliverables**:
- HyDE generation working
- Embedding integration functional
- Fallback handling robust

**Verification**:
- [ ] Hypothetical documents generated correctly
- [ ] Low confidence triggers fallback
- [ ] Embedding integration working
- [ ] Unit tests passing

### Phase 4: Reranking Enhancement (4-6h)

**Objective**: Enhance existing reranking with cross-encoder models

**Steps**:
1. Modify `src/retrieval/reranker.py`
2. Add cross-encoder model loading (`ms-marco-MiniLM-L-6-v2`)
3. Implement batch processing for efficiency
4. Add configurable rerank ratio (top_k → rerank_to)
5. Add model caching (lazy loading)
6. Create/update unit tests
7. Performance profiling

**Dependencies**: None (enhancing existing)

**Deliverables**:
- Cross-encoder reranking working
- Batch processing implemented
- Configuration integrated

**Verification**:
- [ ] Reranking improves top-k precision
- [ ] Batch processing efficient (<2s for 50→10)
- [ ] Model loads lazily
- [ ] Configuration works

### Phase 5: Contextual Compression (10-12h)

**Objective**: Extract relevant sentences from chunks

**Steps**:
1. Create `src/retrieval/compression.py`
2. Implement `ContextualCompressor` class
3. Add sentence extraction with relevance scoring
4. Implement coherence preservation (keep context)
5. Tune compression ratio (target 30-50%)
6. Add quality validation (prevent over-compression)
7. Create unit tests
8. Test with diverse chunks

**Dependencies**: Phase 1 complete (parallel to others)

**Deliverables**:
- Contextual compression working
- Compression ratio tunable
- Quality preserved

**Verification**:
- [ ] Relevant sentences extracted
- [ ] Coherence maintained
- [ ] Compression ratio configurable
- [ ] No over-compression (RAGAS faithfulness)
- [ ] Unit tests passing

### Phase 6: Integration & Testing (8-10h)

**Objective**: Integrate all techniques and validate with RAGAS

**Steps**:
1. Integrate all techniques into `Retriever` class
2. Add configuration switching (personas)
3. Create integration tests (full pipeline)
4. Run RAGAS evaluation with each technique enabled
5. Measure per-technique improvement
6. Performance profiling (latency per stage)
7. Tune thresholds and parameters
8. Document results

**Dependencies**: Phases 2-5 complete

**Deliverables**:
- Full pipeline working
- RAGAS improvements documented
- Performance benchmarks

**Verification**:
- [ ] All techniques integrate smoothly
- [ ] Configuration personas work
- [ ] MRR@10 >0.75 achieved
- [ ] Each technique shows 5-15% improvement
- [ ] Integration tests passing

### Phase 7: Documentation & Release (2-4h)

**Objective**: Complete documentation and release v0.3.3

**Steps**:
1. Use documentation-architect agent
2. Document all 4 techniques (user guide)
3. Document configuration options
4. Create examples for each technique
5. Use documentation-auditor agent
6. Use git-documentation-committer agent
7. Tag v0.3.0 release

**Dependencies**: Phase 6 complete

**Deliverables**:
- Complete API documentation
- User guide with examples
- Configuration guide
- Release tagged

**Verification**:
- [ ] Documentation complete
- [ ] Examples working
- [ ] `/verify-docs` passing
- [ ] Release tagged

## Code Examples

### Current Behaviour (v0.2.X - Basic Retrieval)

```python
# Simple retrieval with basic reranking
from ragged import Retriever

retriever = Retriever(top_k=5)
chunks = retriever.retrieve("How do the methods compare?")

# Issues:
# - Complex queries poorly handled (single query for multi-part question)
# - Query semantics not optimised (question != document semantics)
# - Basic reranking only
# - Full chunks used (lots of noise)

# MRR@10 ~0.60 (baseline)
```

### Enhanced Behaviour (v0.3.0 - Advanced Query Processing)

```python
# Multi-stage retrieval with all techniques
from ragged.retrieval import Retriever, RetrievalConfig, RetrievalStrategy

# "accuracy" persona configuration
config = RetrievalConfig(
    strategy=RetrievalStrategy.HYBRID,
    top_k=50,
    final_k=5,
    enable_decomposition=True,  # Split complex queries
    enable_hyde=False,  # Optional (adds latency)
    enable_reranking=True,  # Always beneficial
    enable_compression=True,  # Reduce noise
    rerank_to=10,
)

retriever = Retriever(config)
chunks = retriever.retrieve("How do the proposed methods compare to prior work?")

# Workflow:
# 1. Query decomposition:
#    - "What methods proposed?"
#    - "What was prior work?"
#    - "How do they compare?"
# 2. Retrieve for each sub-query (parallel)
# 3. Merge and deduplicate results
# 4. Initial retrieval: Top-50 chunks
# 5. Reranking: Top-50 → Top-10 (cross-encoder)
# 6. Compression: Extract relevant sentences only
# 7. Final: 5 high-quality, focused chunks

# MRR@10 ~0.78 (30% improvement!)
```

### Per-Technique Control

```python
# Enable only reranking (balanced persona)
config = RetrievalConfig(
    enable_decomposition=False,
    enable_hyde=False,
    enable_reranking=True,  # Most consistent improvement
    enable_compression=False,
)

# Speed persona (all techniques off)
config = RetrievalConfig(
    enable_decomposition=False,
    enable_hyde=False,
    enable_reranking=False,
    enable_compression=False,
)
# Latency: ~2s (vs ~15s for accuracy)

# Custom combination
config = RetrievalConfig(
    enable_decomposition=True,  # Handle complex queries
    enable_hyde=False,  # Skip (adds latency)
    enable_reranking=True,  # Always good
    enable_compression=True,  # Reduce noise
)
# Balanced quality and speed
```

**Why This Improvement Matters**

Basic retrieval treats all queries the same: embed query, find similar chunks, done. But queries vary dramatically: "What is RAG?" (simple factual) vs "How do transformer architectures compare to RNNs for sequence tasks and what are the trade-offs?" (complex multi-part). Advanced query processing adapts the retrieval strategy to query complexity, achieving 20-30% improvement in retrieval quality while remaining configurable for different use cases.

## Testing Requirements

### Unit Tests

- [ ] `QueryDecomposer` class (>80% coverage)
  - Decomposition for complex queries
  - Bypass for simple queries
  - Sub-query validation
  - Result merging and deduplication
  - Caching

- [ ] `HyDEGenerator` class (>80% coverage)
  - Hypothetical document generation
  - Confidence scoring
  - Fallback to original query
  - Error handling

- [ ] `Reranker` class (>80% coverage)
  - Cross-encoder reranking
  - Batch processing
  - Model loading and caching
  - Configuration options

- [ ] `ContextualCompressor` class (>80% coverage)
  - Sentence extraction
  - Relevance scoring
  - Coherence preservation
  - Compression ratio control

### Integration Tests

- [ ] Full pipeline with all techniques enabled
- [ ] Pipeline with selective techniques
- [ ] Configuration persona switching
- [ ] Error handling (technique failures)
- [ ] Performance profiling (latency per stage)

### End-to-End Tests

- [ ] Complex multi-part queries
- [ ] Simple factual queries
- [ ] RAGAS evaluation per technique
- [ ] A/B comparison (v0.2 baseline vs v0.3.0)
- [ ] Regression testing (no quality loss when disabled)

### Performance Benchmarks

| Stage | Target Latency | Measurement |
|-------|---------------|-------------|
| Query decomposition | <2s | Average over 100 queries |
| HyDE generation | <1.5s | Average over 100 queries |
| Reranking (50→10) | <2s | Average cross-encoder time |
| Contextual compression | <1s | Average sentence extraction |
| Full pipeline (accuracy) | <15s | End-to-end with all techniques |
| Speed persona | <3s | Baseline retrieval only |

## Acceptance Criteria

- [ ] All 7 implementation phases complete
- [ ] All unit tests passing (>80% coverage per module)
- [ ] All integration tests passing
- [ ] All e2e tests passing
- [ ] MRR@10 >0.75 achieved (from ~0.60 baseline)
- [ ] Each technique shows 5-15% independent improvement
- [ ] RAGAS Context Precision >0.80 (from ~0.70)
- [ ] RAGAS Context Recall >0.75 (from ~0.65)
- [ ] Configuration personas working (accuracy/speed/balanced)
- [ ] Performance targets met (latency per stage)
- [ ] Graceful fallback when techniques fail
- [ ] Documentation complete (API docs, user guide, examples)
- [ ] `/verify-docs` passing
- [ ] British English compliance
- [ ] v0.3.0 release tagged

## Related Versions

- **v0.3.0** - Complete advanced query processing implementation (53-55h total)
  - Design & architecture (8-10h)
  - Query decomposition (12-15h)
  - HyDE implementation (6-8h)
  - Reranking enhancement (4-6h)
  - Contextual compression (10-12h)
  - Integration & testing (8-10h)
  - Documentation (2-4h)

This feature is implemented entirely in v0.3.0. See [v0.3.0 roadmap](../v0.3.0.md) for detailed implementation plan.

## Dependencies

### From v0.2.10/v0.2.11 (Security Foundation)

- `SessionManager` - Session-scoped caching (v0.2.10)
- `hash_query()` - Query hashing for logs (v0.2.11)

### From v0.3.0 (Evaluation)

- `RAGASEvaluator` - Measure per-technique improvement
- Baseline scores - Comparison reference

### External Libraries

- **sentence-transformers** (>= 2.2.0) - Apache 2.0 license - Cross-encoder models
- **transformers** (>= 4.30.0) - Apache 2.0 license - HuggingFace models
- **torch** (>= 2.0.0) - BSD license - Model inference
- **nltk** (>= 3.8.0) - Apache 2.0 license - Sentence splitting
- **scipy** (>= 1.11.0) - BSD license - Similarity calculations

All dependencies are GPL-3.0 compatible.

### Hardware/System Requirements

**Minimum**:
- 8GB RAM (for cross-encoder models)
- 4 CPU cores
- 2GB disk space (models)

**Optimal**:
- 16GB+ RAM
- 8+ CPU cores
- GPU with 4GB+ VRAM (10× faster reranking)

**Note**: Cross-encoders work on CPU but GPU significantly improves performance.

## Risk Assessment

### Technical Risks

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Query decomposition quality varies | Medium | High | Validate sub-queries, fallback to original, test diverse queries |
| HyDE generates hallucinations | Medium | Medium | Confidence scoring, fallback to original query, quality checks |
| Performance overhead too high | High | Medium | Make techniques optional (personas), cache results, async processing |
| Compression loses context | Medium | Medium | Tune compression ratio, preserve surrounding sentences, RAGAS validation |

### Performance Risks

- **Cumulative latency**: All techniques together could be too slow
  - **Mitigation**: Personas allow selective enabling, async where possible, caching

- **Resource usage**: Multiple LLM calls consume CPU/memory
  - **Mitigation**: Batch processing, model caching, configurable limits

### Security/Privacy Risks

- **Query decomposition bombing**: Malicious queries decompose into many sub-queries (DoS)
  - **Mitigation**: Limit max sub-queries (3-5), timeouts, rate limiting

- **Cache poisoning**: Malicious cached results
  - **Mitigation**: Session isolation (v0.2.10), TTL cleanup (v0.2.11)

## Related Documentation

- [v0.3.0 Roadmap](../v0.3.0.md) - Detailed implementation plan for advanced query processing
- [v0.3.0 Roadmap](../v0.3.0.md) - RAGAS evaluation (baseline scores)
- [v0.3 Planning](../../../planning/version/v0.3/README.md) - High-level v0.3 design goals
- [v0.3 Master Roadmap](../README.md) - Complete v0.3 overview
- [Security Policy](../../../../security/policy.md#data-minimisation) - Query hashing
- [Privacy Architecture](../../../../security/privacy-architecture.md#session-isolation) - Session-scoped caching

---

**Total Feature Effort:** 50-63 hours (across all phases)
