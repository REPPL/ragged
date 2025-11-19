# RAGAS Evaluation & Quality Framework

Comprehensive quality measurement framework using RAGAS metrics to enable data-driven RAG pipeline optimisation with objective evaluation scores.

## Feature Overview

The RAGAS Evaluation & Quality Framework transforms ragged from a "build and hope" RAG system into a data-driven platform where every improvement can be objectively measured and validated. By integrating the RAGAS (Retrieval-Augmented Generation Assessment) framework, ragged gains industry-standard metrics for retrieval quality (Context Precision, Context Recall), generation quality (Faithfulness, Answer Relevancy), and overall RAG performance.

This feature is implemented FIRST in v0.3 (before any retrieval or generation improvements) to establish baseline metrics. Without objective measurement, there's no way to validate that v0.3.x improvements (reranking, semantic chunking, multi-modal support) actually improve quality. The framework enables A/B testing of different strategies, regression testing to prevent quality degradation, and data-driven decisions replacing guesswork.

Beyond RAGAS, the framework includes answer confidence scoring (helping users understand reliability), retrieval metrics (MRR, NDCG for ranking quality), and observability tools (trace retrieval and generation steps). The goal is achieving RAGAS scores >0.80 (vs ~0.70 in v0.2) and MRR@10 >0.75 (vs ~0.60 in v0.2), demonstrating measurable quality improvements.

## Design Goals

1. **Objective Quality Measurement**: Replace subjective assessment with quantitative metrics
   - RAGAS score >0.80 (overall RAG quality)
   - Context Precision >0.85 (relevant chunks retrieved)
   - Context Recall >0.80 (all relevant chunks retrieved)
   - Faithfulness >0.90 (answers match context)
   - Answer Relevancy >0.85 (answers address questions)

2. **Baseline Establishment**: Document v0.2.X performance before v0.3 improvements
   - Baseline RAGAS scores for current system
   - Baseline retrieval metrics (MRR, NDCG, Recall@k)
   - Reference dataset for regression testing
   - Performance tracking over versions

3. **Data-Driven Development**: Enable A/B testing and quantitative comparison
   - Compare fixed vs semantic chunking (quantify improvement)
   - Measure reranking impact on retrieval quality
   - Validate multi-modal processing benefit
   - Regression test to prevent quality degradation

4. **User Confidence**: Provide confidence scores so users understand answer reliability
   - High confidence (>0.9): Strong retrieval + citations
   - Medium confidence (0.6-0.9): Moderate quality
   - Low confidence (<0.6): Warn user about uncertainty

5. **Developer Observability**: Trace and debug RAG pipeline components
   - View retrieved chunks for each query
   - See LLM generation steps
   - Identify failure points
   - Monitor performance trends

## Technical Architecture

### Module Structure

```
src/
└── ragged/
    └── evaluation/
        ├── __init__.py
        ├── ragas_evaluator.py          # RAGAS framework integration (250 lines)
        │   └── class RAGASEvaluator
        ├── confidence_scorer.py        # Answer confidence scoring (200 lines)
        │   └── class ConfidenceCalculator
        ├── retrieval_metrics.py        # MRR, NDCG, Recall@k (180 lines)
        │   └── class RetrievalMetricsCalculator
        ├── test_set_manager.py         # Test set management (150 lines)
        │   └── class TestSetManager
        └── observability.py            # Tracing and logging (120 lines)
            └── class RAGTracer

src/ragged/cli/commands/
└── evaluate.py                         # CLI evaluation commands (250 lines)

tests/evaluation/
├── test_ragas_evaluator.py             # Unit tests (150 lines)
├── test_confidence_scorer.py           # Unit tests (120 lines)
├── test_retrieval_metrics.py           # Unit tests (130 lines)
└── test_integration.py                 # E2E tests (200 lines)

data/
└── test_sets/
    ├── baseline_v0.2.json              # Baseline test questions
    ├── retrieval_test_v0.3.json        # Retrieval-focused tests
    └── generation_test_v0.3.json       # Generation-focused tests
```

### Data Flow

```
Test Set (JSON)
    ├─ questions
    ├─ ground_truths (optional)
    └─ contexts (optional)
    ↓
┌────────────────────────────────┐
│  Evaluation Pipeline           │
│                                │
│  For each question:            │
│    1. Retrieve chunks          │
│    2. Generate answer          │
│    3. Calculate metrics        │
└────────┬───────────────────────┘
         ↓
┌────────────────────────────────┐
│  RAGAS Evaluation              │
│  - Context Precision           │
│  - Context Recall              │
│  - Faithfulness                │
│  - Answer Relevancy            │
└────────┬───────────────────────┘
         ↓
┌────────────────────────────────┐
│  Retrieval Metrics             │
│  - MRR (Mean Reciprocal Rank)  │
│  - NDCG (Normalised DCG)       │
│  - Recall@k                    │
└────────┬───────────────────────┘
         ↓
┌────────────────────────────────┐
│  Confidence Scoring            │
│  - Retrieval score             │
│  - Generation quality          │
│  - Citation coverage           │
└────────┬───────────────────────┘
         ↓
┌────────────────────────────────┐
│  Results Output                │
│  - JSON (for automation)       │
│  - Table (for humans)          │
│  - Visualisations (future)     │
└────────────────────────────────┘
```

### API Interfaces

```python
"""Evaluation and quality measurement framework."""

from typing import List, Dict, Optional
from dataclasses import dataclass
from enum import Enum


class ConfidenceLevel(Enum):
    """Confidence level classifications."""

    VERY_HIGH = "very_high"  # >0.9
    HIGH = "high"  # 0.75-0.9
    MEDIUM = "medium"  # 0.6-0.75
    LOW = "low"  # 0.4-0.6
    VERY_LOW = "very_low"  # <0.4


@dataclass
class RAGASResult:
    """Results from RAGAS evaluation."""

    context_precision: float  # 0-1: Are retrieved chunks relevant?
    context_recall: float  # 0-1: Did we retrieve all relevant chunks?
    faithfulness: float  # 0-1: Does answer match context?
    answer_relevancy: float  # 0-1: Does answer address question?
    overall_score: float  # 0-1: Average of all metrics

    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON export."""
        return {
            "context_precision": self.context_precision,
            "context_recall": self.context_recall,
            "faithfulness": self.faithfulness,
            "answer_relevancy": self.answer_relevancy,
            "overall_score": self.overall_score,
        }


@dataclass
class ConfidenceScore:
    """Answer confidence breakdown."""

    retrieval_score: float  # 0-1: How relevant are chunks?
    generation_score: float  # 0-1: LLM confidence
    citation_coverage: float  # 0-1: Citation percentage
    overall_confidence: float  # 0-1: Weighted average
    level: ConfidenceLevel  # Human-readable level

    def to_str(self) -> str:
        """Human-readable confidence description."""
        return self.level.value.replace("_", " ").title()


@dataclass
class RetrievalMetrics:
    """Retrieval quality metrics."""

    mrr: float  # Mean Reciprocal Rank (0-1)
    ndcg_at_5: float  # NDCG@5 (0-1)
    ndcg_at_10: float  # NDCG@10 (0-1)
    recall_at_5: float  # Recall@5 (0-1)
    recall_at_10: float  # Recall@10 (0-1)


class RAGASEvaluator:
    """Evaluate RAG pipeline using RAGAS framework."""

    def __init__(self):
        """Initialise RAGAS evaluator with default metrics."""
        from ragas.metrics import (
            context_precision,
            context_recall,
            faithfulness,
            answer_relevancy,
        )

        self.metrics = [
            context_precision,
            context_recall,
            faithfulness,
            answer_relevancy,
        ]

    def evaluate(
        self,
        questions: List[str],
        answers: List[str],
        contexts: List[List[str]],
        ground_truths: Optional[List[str]] = None,
    ) -> RAGASResult:
        """
        Evaluate RAG pipeline performance.

        Args:
            questions: User queries
            answers: Generated answers
            contexts: Retrieved chunks for each query
            ground_truths: Optional reference answers for comparison

        Returns:
            RAGASResult with metric scores

        Raises:
            ValueError: If input lists have different lengths
        """
        pass

    def evaluate_single(
        self,
        question: str,
        answer: str,
        contexts: List[str],
        ground_truth: Optional[str] = None,
    ) -> RAGASResult:
        """
        Evaluate a single query-answer pair.

        Args:
            question: User query
            answer: Generated answer
            contexts: Retrieved chunks
            ground_truth: Optional reference answer

        Returns:
            RAGASResult for this single query
        """
        pass


class ConfidenceCalculator:
    """Calculate answer confidence scores."""

    def __init__(
        self,
        retrieval_weight: float = 0.4,
        generation_weight: float = 0.3,
        citation_weight: float = 0.3,
    ):
        """
        Initialise confidence calculator.

        Args:
            retrieval_weight: Weight for retrieval quality (0-1)
            generation_weight: Weight for generation quality (0-1)
            citation_weight: Weight for citation coverage (0-1)
        """
        self.retrieval_weight = retrieval_weight
        self.generation_weight = generation_weight
        self.citation_weight = citation_weight

    def calculate(
        self,
        retrieved_chunks: List,
        answer: str,
        citations: List[str],
    ) -> ConfidenceScore:
        """
        Calculate confidence for an answer.

        Args:
            retrieved_chunks: Retrieved chunks with similarity scores
            answer: Generated answer text
            citations: Extracted citations from answer

        Returns:
            ConfidenceScore with breakdown and overall confidence
        """
        pass


class RetrievalMetricsCalculator:
    """Calculate retrieval-specific metrics (MRR, NDCG, Recall@k)."""

    def calculate_mrr(
        self,
        retrieved_docs: List[List[str]],
        relevant_docs: List[List[str]],
    ) -> float:
        """
        Calculate Mean Reciprocal Rank.

        MRR measures where the first relevant document appears in rankings.
        Higher is better (1.0 = relevant doc is first).

        Args:
            retrieved_docs: List of retrieved doc lists for each query
            relevant_docs: List of relevant doc lists for each query

        Returns:
            MRR score (0-1)
        """
        pass

    def calculate_ndcg(
        self,
        retrieved_docs: List[List[str]],
        relevant_docs: List[List[str]],
        k: int = 10,
    ) -> float:
        """
        Calculate Normalised Discounted Cumulative Gain at k.

        NDCG measures ranking quality with position discount.
        Higher is better (1.0 = perfect ranking).

        Args:
            retrieved_docs: List of retrieved doc lists
            relevant_docs: List of relevant doc lists
            k: Number of top results to consider

        Returns:
            NDCG@k score (0-1)
        """
        pass

    def calculate_recall_at_k(
        self,
        retrieved_docs: List[List[str]],
        relevant_docs: List[List[str]],
        k: int = 10,
    ) -> float:
        """
        Calculate Recall@k.

        Recall@k measures what fraction of relevant docs appear in top-k.

        Args:
            retrieved_docs: List of retrieved doc lists
            relevant_docs: List of relevant doc lists
            k: Number of top results to consider

        Returns:
            Recall@k score (0-1)
        """
        pass


class TestSetManager:
    """Manage test sets for evaluation."""

    def load_test_set(self, path: str) -> Dict:
        """
        Load test set from JSON file.

        Expected format:
        [
            {
                "question": "What is RAG?",
                "ground_truth": "Retrieval-Augmented Generation...",
                "context": ["Optional pre-defined context..."]
            }
        ]

        Args:
            path: Path to JSON test set file

        Returns:
            Loaded test set dictionary
        """
        pass

    def create_baseline(self, output_path: str):
        """
        Create baseline test set for v0.2 performance tracking.

        Generates diverse questions covering:
        - Simple factual queries
        - Complex multi-hop reasoning
        - Queries requiring synthesis
        - Edge cases (no context, ambiguous)

        Args:
            output_path: Where to save baseline test set
        """
        pass
```

### Integration Points

- **CLI**: `ragged evaluate ragas test_set.json` command for evaluation
- **CI/CD**: Automated regression testing (run on every PR)
- **Generation Pipeline**: Confidence scores returned with answers
- **Retrieval Pipeline**: MRR/NDCG metrics for ranking quality assessment
- **Metrics DB** (v0.3.0): Store evaluation results for trend analysis

## Security & Privacy

### Requirements

- **Query Hashing**: Test questions hashed before storage (no plaintext)
- **Test Set Privacy**: User-provided test sets treated as sensitive
- **No External Calls**: RAGAS runs locally (no cloud APIs)
- **Results Storage**: Evaluation results encrypted if stored (v0.2.11)

### Privacy Risk Score

**Score**: 85/100 (Excellent privacy, low risk)

**Justification**:

**Risk Factors**:
- Test questions may contain user data (low sensitivity)
- Evaluation results stored temporarily (hashed queries only)
- All processing happens locally (no network)

**Mitigation**:
- Query hashing before any storage (v0.2.11 `hash_query()`)
- Test sets stored with restrictive permissions (0o600)
- Results can be deleted (GDPR compliance)
- No external API calls (fully offline evaluation)

The high privacy score (85/100) reflects minimal data collection and full offline operation. The only risk is user-provided test sets potentially containing sensitive queries, mitigated by hashing and encryption.

### Integration with Security Foundation

**Requires**: v0.2.11 (Privacy Infrastructure - for query hashing)

**Key APIs Used**:

```python
from ragged.privacy import hash_query

# Hash test questions before storage
test_questions = ["What is RAG?", "How does chunking work?"]
hashed_questions = [hash_query(q) for q in test_questions]

# Store hashed queries (never plaintext)
results = {
    "query_hash": hashed_questions[0],
    "ragas_score": 0.85,
    "timestamp": "2025-11-19T10:30:00Z",
}

# User can delete evaluation history
# ragged privacy delete --confirm
```

### Detailed Policies

- [Security Policy](../../../../security/policy.md#gdpr-compliance) - Data minimisation principles
- [Privacy Architecture](../../../../security/privacy-architecture.md#privacy-principles) - Data minimisation and PII in test sets

## Implementation Phases

### Phase 1: RAGAS Integration (8-10h)

**Objective**: Integrate RAGAS framework and implement core evaluation

**Steps**:
1. Add RAGAS dependencies (`ragas>=0.1.0`, `datasets>=2.14.0`)
2. Create `src/evaluation/ragas_evaluator.py`
3. Implement `RAGASEvaluator` class
4. Support all 4 RAGAS metrics (context precision/recall, faithfulness, answer relevancy)
5. Implement batch evaluation (multiple questions)
6. Implement single query evaluation
7. Create unit tests
8. Test with sample queries

**Dependencies**: None

**Deliverables**:
- RAGAS framework integrated
- `RAGASEvaluator` class working
- Unit tests passing

**Verification**:
- [ ] RAGAS evaluates test queries correctly
- [ ] All 4 metrics calculated
- [ ] Batch and single evaluation working
- [ ] Unit tests >80% coverage

### Phase 2: CLI Evaluation Commands (6-8h)

**Objective**: Create user-friendly CLI for running evaluations

**Steps**:
1. Create `src/cli/commands/evaluate.py`
2. Implement `ragged evaluate ragas` command
3. Support JSON and table output formats
4. Integrate with existing retrieval and generation pipelines
5. Add progress indicators for long evaluations
6. Support ground truth (optional)
7. Create CLI tests

**Dependencies**: Phase 1 complete

**Deliverables**:
- CLI command working
- Both output formats supported
- Progress indicators functional

**Verification**:
- [ ] `ragged evaluate ragas test_set.json` works
- [ ] JSON output valid
- [ ] Table output readable
- [ ] Progress shown for long evaluations

### Phase 3: Answer Confidence Scoring (6-8h)

**Objective**: Provide confidence scores for generated answers

**Steps**:
1. Create `src/evaluation/confidence_scorer.py`
2. Implement `ConfidenceCalculator` class
3. Calculate retrieval score (chunk similarity average)
4. Estimate generation quality (heuristics initially, logprobs future)
5. Calculate citation coverage (percentage of answer cited)
6. Compute weighted overall confidence
7. Integrate with generation pipeline (return with answers)
8. Create unit tests

**Dependencies**: None (parallel to Phase 1-2)

**Deliverables**:
- Confidence scores working
- Integrated with generation
- Unit tests passing

**Verification**:
- [ ] Confidence calculated correctly
- [ ] Scores correlate with quality
- [ ] Integrated into answer responses
- [ ] Unit tests passing

### Phase 4: Retrieval Metrics (6-8h)

**Objective**: Implement MRR, NDCG, Recall@k for retrieval evaluation

**Steps**:
1. Create `src/evaluation/retrieval_metrics.py`
2. Implement `RetrievalMetricsCalculator` class
3. Implement MRR (Mean Reciprocal Rank) calculation
4. Implement NDCG@k (Normalised Discounted Cumulative Gain)
5. Implement Recall@k calculation
6. Support various k values (5, 10, 20)
7. Create unit tests with ground truth datasets

**Dependencies**: None (parallel)

**Deliverables**:
- All 3 metrics implemented
- Unit tests passing with known datasets

**Verification**:
- [ ] MRR calculated correctly
- [ ] NDCG@k matches reference implementations
- [ ] Recall@k accurate
- [ ] Tests with ground truth pass

### Phase 5: Baseline Establishment (4-6h)

**Objective**: Document v0.2.X baseline performance for comparison

**Steps**:
1. Create `src/evaluation/test_set_manager.py`
2. Implement test set loading/saving
3. Create comprehensive baseline test set (50-100 questions)
4. Run full evaluation on v0.2.X (current system)
5. Document baseline scores (RAGAS, MRR, NDCG)
6. Save results for v0.3.X comparison

**Dependencies**: Phases 1-4 complete

**Deliverables**:
- Baseline test set created
- v0.2.X scores documented
- Results saved for comparison

**Verification**:
- [ ] Test set covers diverse query types
- [ ] Baseline scores documented
- [ ] Results reproducible
- [ ] Saved in version control

### Phase 6: Documentation & Release (2-4h)

**Objective**: Complete documentation and release v0.3.1

**Steps**:
1. Use documentation-architect agent for evaluation docs
2. Document RAGAS metrics (what they measure)
3. Document CLI usage (examples, test set format)
4. Document confidence scores (interpretation)
5. Create tutorial for creating test sets
6. Use documentation-auditor agent
7. Use git-documentation-committer agent
8. Tag v0.3.0 release

**Dependencies**: Phase 5 complete

**Deliverables**:
- Complete API documentation
- User guide for evaluation
- Tutorial for test set creation
- Release tagged

**Verification**:
- [ ] Documentation complete
- [ ] Examples working
- [ ] Tutorial clear
- [ ] `/verify-docs` passing
- [ ] Release tagged

## Code Examples

### Current Behaviour (v0.2.X - No Evaluation)

```python
# No objective quality measurement in v0.2
# Quality assessment is purely subjective:
# "Does this answer look good? I think so..."

from ragged import query

answer = query("What is RAG?")
print(answer)
# Output: [some answer]

# Questions we can't answer:
# - Is this answer accurate?
# - Did we retrieve the right chunks?
# - Is this better than yesterday's version?
# - Did my changes improve quality?
```

### Enhanced Behaviour (v0.3.0 - RAGAS Evaluation)

```python
# Objective quality measurement with RAGAS
from ragged.evaluation import RAGASEvaluator, ConfidenceCalculator
from ragged import Retriever, Generator

# Initialize components
retriever = Retriever()
generator = Generator()
evaluator = RAGASEvaluator()
confidence_calc = ConfidenceCalculator()

# Single query evaluation
question = "What is RAG?"
chunks = retriever.retrieve(question, top_k=5)
answer = generator.generate(question, chunks)

# Calculate RAGAS metrics
result = evaluator.evaluate_single(
    question=question,
    answer=answer,
    contexts=[c.content for c in chunks],
    ground_truth="Retrieval-Augmented Generation combines...",  # Optional
)

print(f"Context Precision: {result.context_precision:.3f}")  # 0.850
print(f"Context Recall: {result.context_recall:.3f}")  # 0.800
print(f"Faithfulness: {result.faithfulness:.3f}")  # 0.920
print(f"Answer Relevancy: {result.answer_relevancy:.3f}")  # 0.880
print(f"Overall RAGAS Score: {result.overall_score:.3f}")  # 0.862

# Calculate confidence
confidence = confidence_calc.calculate(
    retrieved_chunks=chunks,
    answer=answer,
    citations=extract_citations(answer),
)

print(f"Confidence: {confidence.to_str()}")  # "High"
print(f"Confidence Score: {confidence.overall_confidence:.2%}")  # 85%
```

### Batch Evaluation from CLI

```bash
# Create test set (JSON file)
cat > test_set.json <<EOF
[
    {
        "question": "What is RAG?",
        "ground_truth": "Retrieval-Augmented Generation combines retrieval and generation..."
    },
    {
        "question": "How does semantic chunking work?",
        "ground_truth": "Semantic chunking splits documents based on topic boundaries..."
    }
]
EOF

# Run evaluation
ragged evaluate ragas test_set.json

# Output (table format):
# RAGAS Evaluation Results:
#   Context Precision: 0.850
#   Context Recall:    0.820
#   Faithfulness:      0.910
#   Answer Relevancy:  0.870
#   Overall Score:     0.862

# Or get JSON output for automation
ragged evaluate ragas test_set.json --format json > results.json
```

### Comparing Versions (v0.2 vs v0.3)

```python
# Run same test set on v0.2 and v0.3, compare scores

# v0.2 baseline (documented in Phase 5)
v0_2_scores = {
    "ragas_overall": 0.72,
    "mrr": 0.62,
    "ndcg@10": 0.68,
}

# v0.3.0 after semantic chunking
v0_3_6_scores = {
    "ragas_overall": 0.85,  # +18% improvement!
    "mrr": 0.76,  # +23% improvement!
    "ndcg@10": 0.82,  # +21% improvement!
}

# Data-driven validation: semantic chunking works!
```

**Why This Improvement Matters**

Without objective metrics, RAG development is guesswork. RAGAS evaluation enables data-driven decisions: "Semantic chunking improved RAGAS score from 0.72 to 0.85" is far more compelling than "I think semantic chunking works better." Confidence scores help users trust answers, retrieval metrics validate improvements, and baseline tracking prevents regressions.

## Testing Requirements

### Unit Tests

- [ ] `RAGASEvaluator` class (>80% coverage)
  - All 4 metrics calculated correctly
  - Batch evaluation
  - Single evaluation
  - Ground truth optional
  - Error handling

- [ ] `ConfidenceCalculator` class (>80% coverage)
  - Retrieval score calculation
  - Generation quality estimation
  - Citation coverage calculation
  - Weighted average correct
  - Confidence level mapping

- [ ] `RetrievalMetricsCalculator` class (>80% coverage)
  - MRR calculation
  - NDCG@k calculation
  - Recall@k calculation
  - Various k values
  - Edge cases (empty results)

- [ ] `TestSetManager` class (>80% coverage)
  - Load JSON test sets
  - Save test sets
  - Validation (required fields)
  - Error handling

### Integration Tests

- [ ] End-to-end evaluation pipeline
  - Load test set → retrieve → generate → evaluate
  - RAGAS scores calculated correctly
  - Results match expected format
  - Progress indicators work

- [ ] CLI integration
  - `ragged evaluate ragas` command works
  - JSON output valid
  - Table output formatted
  - Error handling (invalid test sets)

### End-to-End Tests

- [ ] Full evaluation with 50-question test set
- [ ] Baseline establishment workflow
- [ ] Confidence scores integrated into generation
- [ ] Retrieval metrics with ground truth
- [ ] Regression test (v0.2 vs v0.3 comparison)

### Performance Benchmarks

| Metric | Target | Measurement |
|--------|--------|-------------|
| RAGAS evaluation (50 questions) | <5 minutes | Wall clock time |
| Confidence calculation | <100ms per answer | Average latency |
| MRR/NDCG calculation | <1s for 100 queries | Computation time |
| Test set loading | <500ms | File I/O time |

## Acceptance Criteria

- [ ] All 6 implementation phases complete
- [ ] All unit tests passing (>80% coverage per module)
- [ ] All integration tests passing
- [ ] All e2e tests passing
- [ ] RAGAS framework integrated (all 4 metrics)
- [ ] CLI command working (`ragged evaluate ragas`)
- [ ] Confidence scoring integrated into generation
- [ ] Retrieval metrics implemented (MRR, NDCG, Recall@k)
- [ ] Baseline scores established for v0.2.X
- [ ] Baseline test set created and version controlled
- [ ] Documentation complete (API docs, user guide, tutorial)
- [ ] `/verify-docs` passing
- [ ] British English compliance
- [ ] v0.3.0 release tagged

## Related Versions

- **v0.3.0** - Complete RAGAS evaluation implementation (30h total)
  - RAGAS integration (8-10h)
  - CLI commands (6-8h)
  - Confidence scoring (6-8h)
  - Retrieval metrics (6-8h)
  - Baseline establishment (4-6h)
  - Documentation (2-4h)

This feature is implemented entirely in v0.3.0. See [v0.3.0 roadmap](../v0.3.0.md) for detailed implementation plan.

## Dependencies

### From v0.2.10/v0.2.11 (Security Foundation)

- `hash_query()` - Hash test questions before storage (v0.2.11)

### External Libraries

- **ragas** (>= 0.1.0) - Apache 2.0 license - RAGAS evaluation framework
- **datasets** (>= 2.14.0) - Apache 2.0 license - Required by RAGAS
- **nltk** (>= 3.8.0) - Apache 2.0 license - Text processing for metrics
- **scipy** (>= 1.11.0) - BSD license - Statistical calculations
- **numpy** (>= 1.24.0) - BSD license - Numerical operations

All dependencies are GPL-3.0 compatible.

### Hardware/System Requirements

**Minimum**:
- 4GB RAM
- 2 CPU cores
- Internet for initial RAGAS model download (~500MB)

**Optimal**:
- 8GB+ RAM (for large test sets)
- 4+ CPU cores (parallel evaluation)

**Note**: RAGAS uses small language models for metric calculation, running efficiently on CPU.

## Risk Assessment

### Technical Risks

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| RAGAS metric calculation slow | Medium | Medium | Batch processing, async evaluation, progress indicators |
| Test set creation difficulty | Medium | High | Provide templates, examples, automated test set generation (future) |
| Baseline scores hard to interpret | Low | Medium | Clear documentation, comparison examples, threshold guidance |
| Confidence scores inaccurate | Medium | Medium | Tune weights, validate against human judgment, improve with LLM logprobs |

### Performance Risks

- **RAGAS evaluation latency**: Each metric requires LLM calls, potentially slow for large test sets
  - **Mitigation**: Batch processing, parallel evaluation, caching, smaller LLM models

- **Storage overhead**: Test sets and results consume disk space
  - **Mitigation**: Compression, TTL-based cleanup, optional storage

### Security/Privacy Risks

- **Test sets contain sensitive queries**: User-provided test questions may have PII
  - **Mitigation**: Query hashing (v0.2.11), encryption, user warnings

- **Results leakage**: Evaluation results stored insecurely
  - **Mitigation**: Restrictive permissions (0o600), encryption at rest (v0.2.11)

## Related Documentation

- [v0.3.0 Roadmap](../v0.3.0.md) - Detailed implementation plan for RAGAS evaluation
- [v0.3 Planning](../../../planning/version/v0.3/README.md) - High-level v0.3 design goals
- [v0.3 Master Roadmap](../README.md) - Complete v0.3 overview
- [RAGAS Framework](https://github.com/explodinggradients/ragas) - Official RAGAS documentation
- [Privacy Architecture](../../../../security/privacy-architecture.md#data-minimisation) - Query hashing requirements

---

**Total Feature Effort:** 32-38 hours (across all phases)
