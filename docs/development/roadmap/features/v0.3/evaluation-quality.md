## Part 4: Evaluation & Quality (24 hours)

### FEAT-009: RAGAS Evaluation Framework

**Priority**: High
**Estimated Time**: 16 hours
**Impact**: Quantify system quality, track improvements
**Research**: "RAGAS: Automated Evaluation of RAG Systems" (arXiv:2309.15217)

#### What is RAGAS?

RAGAS (Retrieval-Augmented Generation Assessment) provides automated metrics for RAG quality:
- **Faithfulness**: Is the answer faithful to the retrieved context?
- **Answer Relevancy**: Is the answer relevant to the question?
- **Context Precision**: Are retrieved chunks relevant?
- **Context Recall**: Are all relevant chunks retrieved?

#### Implementation

```python
# src/evaluation/ragas_eval.py (NEW FILE)
"""RAGAS evaluation framework integration."""
from typing import List, Dict
from dataclasses import dataclass
import json
from pathlib import Path

@dataclass
class RAGASMetrics:
    """RAGAS evaluation metrics."""
    faithfulness: float
    answer_relevancy: float
    context_precision: float
    context_recall: float
    overall_score: float

class RAGASEvaluator:
    """
    Evaluate RAG system using RAGAS metrics.

    Requires:
    - Test dataset with questions, ground truth answers
    - RAG system to evaluate
    """

    def __init__(self, llm_for_evaluation):
        """
        Initialize RAGAS evaluator.

        Args:
            llm_for_evaluation: LLM to use for metric calculation
        """
        self.llm = llm_for_evaluation

    def evaluate(
        self,
        test_dataset: List[Dict],
        rag_system
    ) -> RAGASMetrics:
        """
        Evaluate RAG system on test dataset.

        Args:
            test_dataset: List of test cases with format:
                {
                    'question': str,
                    'ground_truth': str,  # Expected answer
                    'contexts': List[str]  # Ground truth contexts (optional)
                }
            rag_system: RAG system to evaluate (must have query method)

        Returns:
            RAGAS metrics
        """
        faithfulness_scores = []
        relevancy_scores = []
        precision_scores = []
        recall_scores = []

        for test_case in test_dataset:
            question = test_case['question']
            ground_truth = test_case['ground_truth']

            # Get RAG system's answer and retrieved contexts
            result = rag_system.query(question)
            answer = result['answer']
            retrieved_contexts = [chunk.text for chunk in result['chunks']]

            # Calculate metrics
            faithfulness = self._calculate_faithfulness(
                question, answer, retrieved_contexts
            )
            faithfulness_scores.append(faithfulness)

            relevancy = self._calculate_answer_relevancy(
                question, answer
            )
            relevancy_scores.append(relevancy)

            # If ground truth contexts provided, calculate precision/recall
            if 'contexts' in test_case:
                precision = self._calculate_context_precision(
                    retrieved_contexts,
                    test_case['contexts']
                )
                precision_scores.append(precision)

                recall = self._calculate_context_recall(
                    retrieved_contexts,
                    test_case['contexts']
                )
                recall_scores.append(recall)

        # Aggregate scores
        metrics = RAGASMetrics(
            faithfulness=sum(faithfulness_scores) / len(faithfulness_scores),
            answer_relevancy=sum(relevancy_scores) / len(relevancy_scores),
            context_precision=sum(precision_scores) / len(precision_scores) if precision_scores else 0.0,
            context_recall=sum(recall_scores) / len(recall_scores) if recall_scores else 0.0,
            overall_score=0.0  # Will calculate below
        )

        # Overall score is average of available metrics
        available_metrics = [
            metrics.faithfulness,
            metrics.answer_relevancy
        ]
        if precision_scores:
            available_metrics.append(metrics.context_precision)
        if recall_scores:
            available_metrics.append(metrics.context_recall)

        metrics.overall_score = sum(available_metrics) / len(available_metrics)

        return metrics

    def _calculate_faithfulness(
        self,
        question: str,
        answer: str,
        contexts: List[str]
    ) -> float:
        """
        Calculate faithfulness: Is answer supported by context?

        Uses LLM to check if each statement in the answer can be
        inferred from the context.
        """
        faithfulness_prompt = f"""
Given a question, answer, and context, determine if the answer is faithful to the context.

An answer is faithful if all statements in it can be inferred from the context.

Question: {question}

Context:
{chr(10).join(contexts)}

Answer: {answer}

For each statement in the answer, can it be inferred from the context?
Provide your analysis and a faithfulness score from 0.0 (not faithful) to 1.0 (completely faithful).

Faithfulness score:"""

        response = self.llm.generate(
            query=faithfulness_prompt,
            context="",
            temperature=0.1
        )

        # Parse score from response
        score = self._parse_score(response)
        return score

    def _calculate_answer_relevancy(
        self,
        question: str,
        answer: str
    ) -> float:
        """
        Calculate answer relevancy: Does answer address the question?
        """
        relevancy_prompt = f"""
Rate how well this answer addresses the question.

Question: {question}

Answer: {answer}

Provide a relevancy score from 0.0 (not relevant) to 1.0 (perfectly relevant).

Relevancy score:"""

        response = self.llm.generate(
            query=relevancy_prompt,
            context="",
            temperature=0.1
        )

        score = self._parse_score(response)
        return score

    def _calculate_context_precision(
        self,
        retrieved: List[str],
        ground_truth: List[str]
    ) -> float:
        """
        Context precision: What fraction of retrieved contexts are relevant?
        """
        if not retrieved:
            return 0.0

        # Count how many retrieved contexts are in ground truth
        relevant_count = sum(
            1 for r in retrieved
            if any(self._is_similar(r, gt) for gt in ground_truth)
        )

        return relevant_count / len(retrieved)

    def _calculate_context_recall(
        self,
        retrieved: List[str],
        ground_truth: List[str]
    ) -> float:
        """
        Context recall: What fraction of relevant contexts were retrieved?
        """
        if not ground_truth:
            return 1.0  # No ground truth to retrieve

        # Count how many ground truth contexts were retrieved
        retrieved_count = sum(
            1 for gt in ground_truth
            if any(self._is_similar(gt, r) for r in retrieved)
        )

        return retrieved_count / len(ground_truth)

    def _is_similar(self, text1: str, text2: str, threshold: float = 0.7) -> bool:
        """Check if two texts are similar (simple Jaccard similarity)."""
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())

        intersection = words1 & words2
        union = words1 | words2

        similarity = len(intersection) / len(union) if union else 0.0
        return similarity >= threshold

    def _parse_score(self, response: str) -> float:
        """Parse score from LLM response."""
        import re

        # Look for number between 0 and 1
        match = re.search(r'([0-1]\.?\d*)', response)
        if match:
            score = float(match.group(1))
            return max(0.0, min(1.0, score))  # Clamp to [0, 1]

        return 0.5  # Default if can't parse
```

**CLI Integration**:
```python
# src/main.py - new command
@main.command()
@click.argument("dataset", type=click.Path(exists=True))
@click.option("--output", help="Output file for results")
def evaluate(dataset: str, output: str):
    """Evaluate RAG system using RAGAS metrics."""
    from src.evaluation.ragas_eval import RAGASEvaluator

    # Load test dataset
    with open(dataset) as f:
        test_data = json.load(f)

    # Initialize evaluator
    evaluator = RAGASEvaluator(ollama_client)

    # Run evaluation
    console.print("[cyan]Running RAGAS evaluation...[/cyan]")
    metrics = evaluator.evaluate(test_data, rag_system)

    # Display results
    table = Table(title="RAGAS Evaluation Results")
    table.add_column("Metric")
    table.add_column("Score", justify="right")

    table.add_row("Faithfulness", f"{metrics.faithfulness:.3f}")
    table.add_row("Answer Relevancy", f"{metrics.answer_relevancy:.3f}")
    table.add_row("Context Precision", f"{metrics.context_precision:.3f}")
    table.add_row("Context Recall", f"{metrics.context_recall:.3f}")
    table.add_row("[bold]Overall Score[/bold]", f"[bold]{metrics.overall_score:.3f}[/bold]")

    console.print(table)

    # Save to file if requested
    if output:
        results = {
            'metrics': {
                'faithfulness': metrics.faithfulness,
                'answer_relevancy': metrics.answer_relevancy,
                'context_precision': metrics.context_precision,
                'context_recall': metrics.context_recall,
                'overall_score': metrics.overall_score
            },
            'timestamp': str(datetime.now())
        }

        with open(output, 'w') as f:
            json.dump(results, f, indent=2)

        console.print(f"\n[green]✓[/green] Results saved to {output}")
```

#### Testing Requirements
- [ ] Test metric calculation on sample data
- [ ] Create test dataset
- [ ] Validate scores are in [0, 1]
- [ ] Test evaluation CLI command
- [ ] Compare metrics before/after improvements

#### Files to Create
- `src/evaluation/ragas_eval.py` (~400 lines)
- `src/evaluation/test_dataset.json` (sample test data)
- `tests/evaluation/test_ragas.py` (~150 lines)

#### Acceptance Criteria
- ✅ RAGAS metrics implemented
- ✅ Can evaluate system on test dataset
- ✅ Metrics track quality improvements
- ✅ CLI command for evaluation

---

### FEAT-010: Answer Confidence Scores

**Priority**: Medium
**Estimated Time**: 8 hours
**Impact**: Users know when to verify answers

#### Implementation

```python
# src/generation/confidence.py (NEW FILE)
"""Confidence scoring for generated answers."""

class ConfidenceScorer:
    """
    Estimate confidence in generated answers.

    Uses multiple signals:
    - Retrieval scores (how good are the retrieved chunks?)
    - Answer-context alignment (does answer match context?)
    - Self-assessment (ask LLM for confidence)
    """

    def __init__(self, llm):
        self.llm = llm

    def calculate_confidence(
        self,
        query: str,
        answer: str,
        chunks: List[Chunk]
    ) -> Dict:
        """
        Calculate confidence score for an answer.

        Returns:
            Dictionary with:
                - score: Overall confidence (0.0-1.0)
                - signals: Individual confidence signals
                - reasoning: Explanation of score
        """
        signals = {}

        # Signal 1: Retrieval quality
        signals['retrieval'] = self._retrieval_quality(chunks)

        # Signal 2: Answer length (very short may indicate low confidence)
        signals['answer_length'] = self._answer_length_signal(answer)

        # Signal 3: LLM self-assessment
        signals['self_assessment'] = self._llm_self_assessment(
            query, answer, chunks
        )

        # Combine signals
        overall_score = (
            signals['retrieval'] * 0.3 +
            signals['answer_length'] * 0.1 +
            signals['self_assessment'] * 0.6
        )

        # Get reasoning
        reasoning = self._explain_confidence(signals, overall_score)

        return {
            'score': overall_score,
            'signals': signals,
            'reasoning': reasoning
        }

    def _retrieval_quality(self, chunks: List[Chunk]) -> float:
        """Score based on retrieval quality."""
        if not chunks:
            return 0.0

        # Average of top chunk scores
        scores = [c.score for c in chunks[:3]]
        return sum(scores) / len(scores)

    def _answer_length_signal(self, answer: str) -> float:
        """Score based on answer length."""
        words = len(answer.split())

        if words < 10:
            return 0.3  # Very short answers may be uncertain
        elif words < 50:
            return 1.0  # Normal length
        elif words < 200:
            return 0.9  # Longer is ok
        else:
            return 0.7  # Very long might be rambling

    def _llm_self_assessment(
        self,
        query: str,
        answer: str,
        chunks: List[Chunk]
    ) -> float:
        """Ask LLM to assess its own confidence."""
        context = "\n\n".join([c.text for c in chunks[:3]])

        prompt = f"""
You just answered a question. Rate your confidence in the answer.

Question: {query}

Context used:
{context}

Your answer: {answer}

On a scale of 0.0 (no confidence) to 1.0 (very confident), how confident are you that this answer is correct and complete?

Consider:
- Is the context sufficient to answer the question?
- Did you make any assumptions?
- Are there gaps in your knowledge?

Confidence score (0.0-1.0):"""

        response = self.llm.generate(
            query=prompt,
            context="",
            temperature=0.1
        )

        # Parse score
        import re
        match = re.search(r'([0-1]\.?\d*)', response)
        if match:
            return float(match.group(1))

        return 0.5  # Default

    def _explain_confidence(self, signals: Dict, score: float) -> str:
        """Generate human-readable explanation of confidence."""
        explanations = []

        if signals['retrieval'] < 0.5:
            explanations.append("Retrieved context had low relevance scores")

        if signals['answer_length'] < 0.5:
            explanations.append("Answer was unusually short")

        if signals['self_assessment'] < 0.5:
            explanations.append("Answer may contain uncertainties or assumptions")

        if score >= 0.8:
            level = "High confidence"
        elif score >= 0.6:
            level = "Moderate confidence"
        else:
            level = "Low confidence"

        if explanations:
            return f"{level}. {'; '.join(explanations)}."
        else:
            return f"{level}. Answer is well-supported by retrieved context."
```

**Display to User**:
```python
# src/main.py - query command
def query(query_text: str):
    # ... retrieval and generation ...

    # Calculate confidence
    confidence = ConfidenceScorer(ollama_client).calculate_confidence(
        query_text, answer, chunks
    )

    # Display answer
    console.print("\n[bold]Answer:[/bold]")
    console.print(answer)

    # Display confidence
    score = confidence['score']
    if score >= 0.8:
        color = "green"
        emoji = "✓"
    elif score >= 0.6:
        color = "yellow"
        emoji = "⚠"
    else:
        color = "red"
        emoji = "⚠"

    console.print(f"\n[{color}]{emoji} Confidence: {score:.1%}[/{color}]")
    console.print(f"[dim]{confidence['reasoning']}[/dim]")

    if score < 0.5:
        console.print("\n[red]Note: Low confidence. Please verify this answer.[/red]")
```

#### Testing Requirements
- [ ] Test confidence calculation on various queries
- [ ] Validate confidence correlates with quality
- [ ] Test low confidence detection
- [ ] Test confidence display in UI

#### Files to Create
- `src/generation/confidence.py` (~200 lines)
- `tests/generation/test_confidence.py` (~100 lines)

#### Acceptance Criteria
- ✅ Confidence scores calculated
- ✅ Low confidence warnings shown
- ✅ Scores correlate with answer quality

---


---

## Related Documentation

- [Evaluation Framework (v0.3.7)](../../version/v0.3/v0.3.7.md) - Implementation roadmap
- [Benchmarking Suite (v0.3.8)](../../version/v0.3/v0.3.8.md) - Performance benchmarks
- [Quality Measurement](../../../../planning/architecture/) - Architecture approach
- [v0.3 Planning](../../../../planning/version/v0.3/) - Design goals

---
