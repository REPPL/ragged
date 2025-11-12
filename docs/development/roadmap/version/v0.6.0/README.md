# Ragged v0.6.0 Roadmap - Intelligent Optimisation

**Status:** Planned

**Total Hours:** 120-150 hours (AI implementation)

**Focus:** Automatic query routing, domain adaptation, and advanced analytics

**Breaking Changes:** None

---

## Overview

Version 0.6.0 introduces intelligent optimisation that automatically routes queries to optimal models, adapts to domain-specific terminology, and provides advanced analytics for system performance.

**Dependencies:** Requires v0.5.0 completion (vision integration)

---

## OPTIMISE-001: Query Classification (25-30 hours)

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

## OPTIMISE-002: Automatic Model Routing (30-40 hours)

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

## OPTIMISE-003: Domain Adaptation (25-35 hours)

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

## OPTIMISE-004: Performance Analytics (20-25 hours)

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

## OPTIMISE-005: Smart Caching Strategy (20-25 hours)

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

## OPTIMISE-006: CLI Analytics Commands (15-20 hours)

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

**Files:** src/main.py, src/analytics/reporter.py (new)

**⚠️ MANUAL TEST:** Use CLI analytics commands, verify data accurate and useful

**Success:** Analytics accessible via CLI, reports comprehensive and actionable

---

## Success Criteria (Test Checkpoints)

**Automated:**
- [ ] Query classification accuracy >85%
- [ ] Model routing selects appropriate models
- [ ] Domain adaptation improves domain-specific retrieval
- [ ] Analytics metrics collected correctly
- [ ] Smart caching improves hit rate
- [ ] All existing tests pass

**Manual Testing:**
- [ ] ⚠️ MANUAL: Model routing reduces latency for simple queries
- [ ] ⚠️ MANUAL: Domain adaptation improves domain-specific results
- [ ] ⚠️ MANUAL: Analytics provide actionable insights
- [ ] ⚠️ MANUAL: Cache warming improves performance
- [ ] ⚠️ MANUAL: Routing decisions sensible for query types

**Quality Gates:**
- [ ] 30-50% latency reduction for simple queries (model routing)
- [ ] 20-30% cache hit rate improvement (smart caching)
- [ ] Domain-specific retrieval quality improvement measurable
- [ ] Analytics overhead <5% of query time
- [ ] No regression in accuracy for any query type

---

## Known Risks

- Query classification may require tuning for accuracy
- Model routing logic may need domain-specific adjustments
- Domain adaptation effectiveness varies by domain
- Analytics collection may impact performance
- Smart caching prediction accuracy uncertain

---

## Next Version

After v0.6.0 completion:
- **v0.7.0:** Production readiness (scalability, enterprise features, stable API)
- See: `roadmap/version/v0.7.0/README.md`

---

**Last Updated:** 2025-11-12

**Status:** Requires v0.5.0 completion first
