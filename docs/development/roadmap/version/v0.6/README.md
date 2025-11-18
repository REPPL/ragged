# Ragged v0.6.0 Roadmap - Intelligent Optimisation

**Status:** Planned

**Total Hours:** 162-225 hours (AI implementation)

**Focus:** Automatic query routing, domain adaptation, and advanced analytics

**Breaking Changes:** None

---

## Overview

Version 0.6.0 introduces intelligent optimisation that automatically routes queries to optimal models, adapts to domain-specific terminology, and provides advanced analytics for system performance.

**Dependencies:** Requires v0.5.0 completion (vision integration)

---

## OPTIMISE-001: Context Scope Management (15-20 hours)

**Problem:** All queries use full context regardless of complexity. Simple queries waste tokens on broad context; complex queries may need comprehensive knowledge graph traversal.

**Theoretical Foundation:** Implements [Context Engineering 2.0](../../acknowledgements/context-engineering-2.0.md) **dynamic context adaptation**—adjusting context scope based on query complexity and resource constraints.

**Implementation:**
1. Research context compression techniques [2-3 hours]
2. Create ContextScopeManager with query complexity analysis [5-6 hours]
3. Implement context selection strategies (narrow/medium/broad) [4-5 hours]
4. Add context compression for complex queries [3-4 hours]
5. Create scope recommendation system [1-2 hours]

**Context Scopes:**
- **Narrow** (simple factual): Recent documents only, no knowledge graph
- **Medium** (standard queries): Recent + related topics from knowledge graph
- **Broad** (complex analytical): Full knowledge graph + temporal memory + all relevant documents

**Scope Selection Rules:**
```python
def determine_scope(query):
    complexity = classify_complexity(query)
    if complexity == "simple":
        return ContextScope.NARROW  # Last 7 days, top 5 docs
    elif complexity == "medium":
        return ContextScope.MEDIUM  # Last 30 days, topic graph, top 15 docs
    else:
        return ContextScope.BROAD   # Full timeline, full graph, top 30 docs
```

**Compression Strategies:**
- Chain-of-context: Summarise intermediate documents
- Entity-focused: Extract only relevant entities from knowledge graph
- Time-windowed: Limit temporal memory to relevant periods

**Files:**
- `src/context/scope_manager.py` (new, ~250 lines)
- `src/context/compression.py` (new, ~200 lines)
- `tests/context/test_scope_manager.py` (~150 lines)

**⚠️ MANUAL TEST:** Test with simple vs complex queries, verify appropriate context scope selected, measure token usage reduction

**Success:** Context usage optimised per query type, 30-50% token reduction on simple queries, no accuracy loss

---

## OPTIMISE-002: Query Classification (25-30 hours)

**Problem:** All queries treated identically, but different query types need different processing strategies.

**Implementation:**
1. Research query classification approaches [3-4 hours]
2. Create QueryClassifier for query type detection [8-10 hours]
3. Implement query complexity scoring [6-8 hours]
4. Add query intent detection (factual, analytical, creative) [5-6 hours]
5. Create classification metadata storage [3-4 hours]

**Query types:**
- Factual: "What is X?"
- Analytical: "Compare X and Y"
- Creative: "Suggest improvements to X"
- Visual: "Show me documents with charts"

**Files:** src/classification/query_classifier.py (new), src/retrieval/hybrid.py

**⚠️ MANUAL TEST:** Test with various query types, verify correct classification

**Success:** Queries classified accurately, appropriate strategies selected per type

---

## OPTIMISE-003: Automatic Model Routing (30-40 hours)

**Problem:** Single model for all queries is suboptimal - complex queries need larger models, simple queries can use faster models.

**Implementation:**
1. Create ModelRouter with routing logic [10-12 hours]
2. Implement model capability assessment [8-10 hours]
3. Add query-to-model matching algorithm [6-8 hours]
4. Create model performance profiling [4-6 hours]
5. Add routing override options [2-3 hours]

**Routing strategy:**
- Simple factual → Small fast model (llama3.2:3b)
- Complex analytical → Large capable model (llama3.2:70b)
- Creative → Medium balanced model (mistral:latest)
- Vision → Multi-modal model (llava)

**Files:** src/routing/model_router.py (new), src/generation/ollama_client.py

**⚠️ MANUAL TEST:** Test routing with different query complexities, verify appropriate models selected

**Success:** Queries routed to optimal models, 30-50% latency reduction on simple queries

---

## OPTIMISE-004: Domain Adaptation (25-35 hours)

**Problem:** General-purpose embeddings may not capture domain-specific terminology and concepts.

**Implementation:**
1. Research domain adaptation techniques [3-4 hours]
2. Implement domain vocabulary extraction [8-10 hours]
3. Create domain-specific query expansion [6-8 hours]
4. Add domain embedding fine-tuning (optional) [6-8 hours]
5. Implement domain-aware retrieval boosting [2-3 hours]

**Domains to support:**
- Technical/Engineering
- Medical/Healthcare
- Legal
- Academic/Research
- General

**Files:** src/adaptation/domain_adapter.py (new), src/retrieval/hybrid.py

**⚠️ MANUAL TEST:** Test with domain-specific documents, verify improved retrieval for domain terminology

**Success:** Domain-specific queries retrieve more relevant results, terminology recognised correctly

---

## OPTIMISE-005: Performance Analytics (20-25 hours)

**Problem:** No visibility into system performance, bottlenecks, or quality metrics over time.

**Implementation:**
1. Create AnalyticsCollector for metrics gathering [6-8 hours]
2. Implement query latency tracking and profiling [4-5 hours]
3. Add cache hit rate monitoring [3-4 hours]
4. Create model usage statistics [3-4 hours]
5. Implement quality metrics (RAGAS integration) [4-5 hours]

**Metrics to track:**
- Query latency (p50, p95, p99)
- Retrieval quality scores
- Model routing decisions
- Cache effectiveness
- GPU utilisation
- Memory usage patterns

**Files:** src/analytics/collector.py (new), src/analytics/metrics.py (new)

**⚠️ MANUAL TEST:** Run queries, verify metrics collected accurately

**Success:** Comprehensive metrics collected, analytics queryable, trends visible

---

## OPTIMISE-006: Smart Caching Strategy (20-25 hours)

**Problem:** Basic caching in v0.2.7 needs intelligence - predict what to cache, when to invalidate.

**Implementation:**
1. Implement intelligent cache warming [5-6 hours]
2. Add query pattern prediction [6-8 hours]
3. Create cache priority scoring [4-5 hours]
4. Implement adaptive cache sizing [3-4 hours]
5. Add cache analytics dashboard [2-3 hours]

**Caching strategies:**
- Frequency-based (cache common queries)
- Recency-based (cache recent queries)
- Predictive (cache likely next queries)
- Similarity-based (cache similar queries)

**Files:** src/caching/smart_cache.py (new), src/retrieval/hybrid.py

**⚠️ MANUAL TEST:** Monitor cache performance, verify hit rate improvement

**Success:** Cache hit rate improved by 20-30%, latency reduced further

---

## OPTIMISE-007: CLI Analytics Commands (15-20 hours)

**Problem:** Need CLI interface to view analytics and optimisation status.

**Implementation:**
1. Create analytics view command [4-5 hours]
2. Add routing statistics command [3-4 hours]
3. Implement performance report generation [4-5 hours]
4. Add optimisation suggestions [3-4 hours]
5. Create export options (JSON, CSV) [1-2 hours]

**Commands:**
- `ragged analytics` - View performance metrics
- `ragged analytics routing` - Model routing stats
- `ragged analytics cache` - Cache performance
- `ragged analytics domain` - Domain adaptation stats
- `ragged analytics context` - Context scope usage statistics

**Files:** src/main.py, src/analytics/reporter.py (new)

**⚠️ MANUAL TEST:** Use CLI analytics commands, verify data accurate and useful

**Success:** Analytics accessible via CLI, reports comprehensive and actionable

---

## OPTIMISE-008: Streaming Response Generation (12-15 hours)

**Problem:** Users wait for complete response generation before seeing any output, creating perception of slowness even when total latency is acceptable.

**Theoretical Foundation:** Reduces perceived latency by streaming tokens as they're generated, providing immediate feedback and progress indication.

**Implementation:**
1. Enable Ollama streaming mode in client [3-4 hours]
2. Implement streaming API endpoints [4-5 hours]
3. Add CLI progressive display with token streaming [3-4 hours]
4. Update Gradio UI for streaming responses [2-3 hours]

**Streaming Approach:**
```python
async def stream_query(query: str):
    # Retrieval phase (non-streaming)
    context = await retrieve(query)

    # Generation phase (streaming)
    async for token in ollama_client.generate_stream(query, context):
        yield token  # Stream to user immediately
```

**Benefits:**
- **Time to first token:** <1 second (vs 3-8 seconds for full response)
- **Perceived latency reduction:** 60-80%
- **User experience:** Immediate feedback, progress indication
- **No accuracy impact:** Same final response, different delivery

**Files:**
- `src/generation/ollama_client.py` (modify existing, add `generate_stream()`)
- `src/web/api.py` (add `/query/stream` endpoint)
- `src/cli/commands/query.py` (add progressive display)
- `src/web/app.py` (update Gradio interface)
- `tests/generation/test_streaming.py` (~100 lines)

**⚠️ MANUAL TEST:** Test streaming with various query types, verify smooth token delivery, no buffering delays

**Success:** Token streaming functional, time to first token <1s, CLI displays progressive output, Gradio shows real-time generation

---

## OPTIMISE-009: Parallel Retrieval Pipeline (15-20 hours)

**Problem:** Retrieval operations run sequentially (vector search → BM25 → reranking), wasting time when operations are independent.

**Theoretical Foundation:** Parallelise independent retrieval operations to reduce total latency through concurrent execution.

**Implementation:**
1. Refactor hybrid retrieval for async parallel execution [6-8 hours]
2. Implement parallel retrieval orchestrator [5-6 hours]
3. Add intelligent result merging and deduplication [3-4 hours]
4. Benchmark and tune concurrency parameters [1-2 hours]

**Parallel Retrieval Architecture:**
```python
async def parallel_hybrid_retrieve(query: str, k: int):
    # Run all retrievers concurrently
    vector_task = asyncio.create_task(vector_retrieve(query, k))
    bm25_task = asyncio.create_task(bm25_retrieve(query, k))

    # Wait for both to complete
    vector_results, bm25_results = await asyncio.gather(
        vector_task, bm25_task
    )

    # Merge results (fast, in-memory)
    merged = merge_and_rerank(vector_results, bm25_results, k)
    return merged
```

**Sequential vs Parallel:**
- **Sequential:** Vector (200ms) + BM25 (150ms) + Rerank (100ms) = 450ms
- **Parallel:** max(Vector, BM25) + Rerank = 200ms + 100ms = 300ms
- **Reduction:** 33% for this example, up to 60% for complex pipelines

**Files:**
- `src/retrieval/hybrid.py` (major refactor for async)
- `src/retrieval/parallel_retriever.py` (new, ~250 lines)
- `src/retrieval/result_merger.py` (new, ~150 lines)
- `tests/retrieval/test_parallel.py` (~200 lines)

**⚠️ MANUAL TEST:** Benchmark sequential vs parallel retrieval, verify result quality unchanged, measure latency reduction

**Success:** Retrieval latency reduced by 40-60%, no accuracy regression, concurrent operations properly synchronized

---

## OPTIMISE-010: Speculative RAG (Experimental) (25-35 hours)

**Problem:** Large models provide high-quality responses but are slow; small models are fast but may lack quality. Users face latency-quality trade-off.

**Theoretical Foundation:** Based on Google Research's Speculative RAG (arXiv:2407.08223) - smaller specialist model drafts response, larger generalist model verifies and corrects if needed.

**Status:** EXPERIMENTAL - Mark as optional, validate quality before production use

**Implementation:**
1. Research speculative RAG implementation patterns [4-5 hours]
2. Implement draft-verify orchestration [10-12 hours]
3. Add draft quality assessment and acceptance criteria [6-8 hours]
4. Create fallback mechanisms for draft rejection [3-4 hours]
5. Comprehensive benchmark: accuracy vs latency trade-offs [2-3 hours]

**Speculative RAG Workflow:**
```python
async def speculative_rag_query(query: str, context: str):
    # Step 1: Draft with fast small model
    draft = await small_model.generate(query, context)

    # Step 2: Assess draft quality
    quality_score = assess_draft_quality(draft, query)

    # Step 3: Decide verification strategy
    if quality_score > ACCEPTANCE_THRESHOLD:
        return draft  # High confidence, accept draft
    elif quality_score > REVISION_THRESHOLD:
        # Medium confidence, verify specific sections
        return await large_model.verify_and_correct(draft, query, context)
    else:
        # Low confidence, regenerate with large model
        return await large_model.generate(query, context)
```

**Model Pairing (Ollama):**
- **Draft Model:** `llama3.2:3b` (fast, ~500 tokens/sec)
- **Verify Model:** `llama3.2:70b` (quality, ~50 tokens/sec)
- **Acceptance Rate:** Target 60-70% (Google reported 51% latency reduction at similar rates)

**Expected Performance:**
- **Simple queries:** Draft accepted → 80% latency reduction
- **Medium queries:** Partial verification → 40-60% reduction
- **Complex queries:** Full regeneration → No reduction (same as baseline)
- **Overall (mixed workload):** 30-50% average latency reduction

**Quality Safeguards:**
- Accuracy validation against baseline
- User feedback integration
- Configurable acceptance thresholds
- Automatic fallback to single-model mode if quality degrades

**Files:**
- `src/generation/speculative_rag.py` (new, ~350 lines)
- `src/generation/draft_assessor.py` (new, ~200 lines)
- `src/routing/model_router.py` (extend existing)
- `tests/generation/test_speculative.py` (~250 lines)

**⚠️ MANUAL TEST:** Extensive quality validation across query types, verify no accuracy regression, measure actual latency gains

**Success:** 30-50% latency reduction on average, no accuracy loss, draft acceptance rate 60-70%, graceful degradation

---

## Success Criteria (Test Checkpoints)

**Automated:**
- [ ] Context scope selection correct for query complexity
- [ ] Query classification accuracy >85%
- [ ] Model routing selects appropriate models
- [ ] Domain adaptation improves domain-specific retrieval
- [ ] Analytics metrics collected correctly
- [ ] Smart caching improves hit rate
- [ ] Streaming response tokens delivered correctly
- [ ] Parallel retrieval produces identical results to sequential
- [ ] Speculative RAG draft acceptance rate 60-70%
- [ ] All existing tests pass

**Manual Testing:**
- [ ] ⚠️ MANUAL: Context scope reduces token usage without accuracy loss
- [ ] ⚠️ MANUAL: Model routing reduces latency for simple queries
- [ ] ⚠️ MANUAL: Domain adaptation improves domain-specific results
- [ ] ⚠️ MANUAL: Analytics provide actionable insights
- [ ] ⚠️ MANUAL: Cache warming improves performance
- [ ] ⚠️ MANUAL: Routing decisions sensible for query types
- [ ] ⚠️ MANUAL: Streaming provides smooth user experience
- [ ] ⚠️ MANUAL: Parallel retrieval reduces latency measurably
- [ ] ⚠️ MANUAL: Speculative RAG maintains quality while reducing latency

**Quality Gates:**
- [ ] 30-50% token reduction for simple queries (context scope)
- [ ] 60-80% perceived latency reduction (streaming - time to first token)
- [ ] 40-60% retrieval latency reduction (parallel processing)
- [ ] 30-50% average latency reduction (speculative RAG, experimental)
- [ ] 30-50% latency reduction for simple queries (model routing)
- [ ] 20-30% cache hit rate improvement (smart caching)
- [ ] Domain-specific retrieval quality improvement measurable
- [ ] Analytics overhead <5% of query time
- [ ] No regression in accuracy for any query type

---

## Known Risks

- Context scope determination may need query-specific tuning
- Query classification may require tuning for accuracy
- Model routing logic may need domain-specific adjustments
- Domain adaptation effectiveness varies by domain
- Analytics collection may impact performance
- Smart caching prediction accuracy uncertain
- Streaming may buffer on slow systems (test on various hardware)
- Parallel retrieval requires careful concurrency management (deadlock risk)
- Speculative RAG quality highly dependent on draft acceptance criteria (experimental)

---

## Next Version

After v0.6.0 completion:
- **v0.7.0:** Production readiness (scalability, enterprise features, stable API)
- See: `roadmap/version/v0.7/README.md`

---

**Last Updated:** 2025-11-12

**Status:** Requires v0.5.0 completion first

---

## Related Documentation

- [Previous Version](../v0.5/README.md) - Multi-model intelligence
- [Next Version](../v0.7/README.md) - Enterprise & production
- [Planning](../../planning/version/v0.6/) - Design goals for v0.6
- [Version Overview](../README.md) - Complete version comparison

---
