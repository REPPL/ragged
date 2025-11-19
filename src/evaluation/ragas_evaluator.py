"""
RAGAS-based RAG evaluation implementation.

This module integrates the RAGAS (RAG Assessment) framework for objective,
automated quality evaluation of retrieval-augmented generation systems.

RAGAS provides four key metrics:
- Context Precision: How relevant are retrieved chunks?
- Context Recall: How complete is retrieval coverage?
- Faithfulness: Is the answer grounded in context?
- Answer Relevancy: Does answer address the question?
"""

from dataclasses import dataclass
from typing import List, Optional

from datasets import Dataset
from ragas import evaluate
from ragas.metrics import (
    answer_relevancy,
    context_precision,
    context_recall,
    faithfulness,
)


@dataclass
class EvaluationResult:
    """
    Results from RAGAS evaluation.

    Scores range from 0.0 to 1.0, where higher is better.
    Target scores for production quality: >0.80 for all metrics.
    """

    context_precision: float
    context_recall: float
    faithfulness: float
    answer_relevancy: float
    overall_score: float

    def to_dict(self) -> dict:
        """
        Convert result to dictionary.

        Returns:
            Dictionary with all metric scores
        """
        return {
            "context_precision": self.context_precision,
            "context_recall": self.context_recall,
            "faithfulness": self.faithfulness,
            "answer_relevancy": self.answer_relevancy,
            "overall_score": self.overall_score,
        }

    def __str__(self) -> str:
        """Human-readable result summary."""
        return (
            f"RAGAS Evaluation Results:\n"
            f"  Context Precision: {self.context_precision:.3f}\n"
            f"  Context Recall:    {self.context_recall:.3f}\n"
            f"  Faithfulness:      {self.faithfulness:.3f}\n"
            f"  Answer Relevancy:  {self.answer_relevancy:.3f}\n"
            f"  Overall Score:     {self.overall_score:.3f}"
        )


class RAGASEvaluator:
    """
    Evaluate RAG pipeline quality using RAGAS framework.

    RAGAS provides automated, objective quality metrics that correlate
    well with human judgement. Used for baseline establishment and
    tracking improvements across versions.

    Example:
        >>> evaluator = RAGASEvaluator()
        >>> result = evaluator.evaluate_single(
        ...     question="What is RAG?",
        ...     answer="RAG combines retrieval and generation...",
        ...     contexts=["RAG is a technique that...", "..."],
        ...     ground_truth="RAG is retrieval-augmented generation"
        ... )
        >>> print(f"Overall score: {result.overall_score:.2f}")
    """

    def __init__(self) -> None:
        """
        Initialise evaluator with default RAGAS metrics.

        Metrics:
        - context_precision: Relevance of retrieved chunks
        - context_recall: Completeness of retrieval
        - faithfulness: Grounding in provided context
        - answer_relevancy: Alignment with question
        """
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
    ) -> EvaluationResult:
        """
        Evaluate multiple question-answer pairs.

        Args:
            questions: List of questions
            answers: List of generated answers
            contexts: List of context lists (retrieved chunks for each question)
            ground_truths: Optional list of reference answers

        Returns:
            EvaluationResult with aggregated scores

        Raises:
            ValueError: If input lists have different lengths
        """
        # Validate input lengths
        if not (len(questions) == len(answers) == len(contexts)):
            raise ValueError(
                f"Input length mismatch: {len(questions)} questions, "
                f"{len(answers)} answers, {len(contexts)} contexts"
            )

        if ground_truths is not None and len(ground_truths) != len(questions):
            raise ValueError(
                f"Ground truth length mismatch: {len(ground_truths)} provided, "
                f"expected {len(questions)}"
            )

        # Prepare dataset for RAGAS
        data = {
            "question": questions,
            "answer": answers,
            "contexts": contexts,
        }

        if ground_truths is not None:
            data["ground_truth"] = ground_truths

        dataset = Dataset.from_dict(data)

        # Run RAGAS evaluation
        result = evaluate(
            dataset,
            metrics=self.metrics,
        )

        # Extract scores
        return EvaluationResult(
            context_precision=result["context_precision"],
            context_recall=result["context_recall"],
            faithfulness=result["faithfulness"],
            answer_relevancy=result["answer_relevancy"],
            overall_score=self._calculate_overall(result),
        )

    def evaluate_single(
        self,
        question: str,
        answer: str,
        contexts: List[str],
        ground_truth: Optional[str] = None,
    ) -> EvaluationResult:
        """
        Evaluate a single question-answer pair.

        Convenience method for evaluating individual queries.

        Args:
            question: The question
            answer: Generated answer
            contexts: Retrieved context chunks
            ground_truth: Optional reference answer

        Returns:
            EvaluationResult for this query
        """
        # Convert to lists for batch evaluation
        questions = [question]
        answers = [answer]
        contexts_list = [contexts]
        ground_truths = [ground_truth] if ground_truth is not None else None

        return self.evaluate(
            questions=questions,
            answers=answers,
            contexts=contexts_list,
            ground_truths=ground_truths,
        )

    def _calculate_overall(self, result: dict) -> float:
        """
        Calculate overall score from individual metrics.

        Simple average of all four metrics. More sophisticated
        weighting could be added in future versions.

        Args:
            result: Raw RAGAS evaluation result

        Returns:
            Overall score (0.0-1.0)
        """
        scores = [
            result.get("context_precision", 0.0),
            result.get("context_recall", 0.0),
            result.get("faithfulness", 0.0),
            result.get("answer_relevancy", 0.0),
        ]

        # Filter out None values (in case some metrics failed)
        valid_scores = [s for s in scores if s is not None]

        if not valid_scores:
            return 0.0

        return sum(valid_scores) / len(valid_scores)
