"""Tests for RAGAS evaluation module."""

import pytest
from unittest.mock import Mock, patch

from src.evaluation.ragas_evaluator import EvaluationResult, RAGASEvaluator


class TestEvaluationResult:
    """Tests for EvaluationResult dataclass."""

    def test_to_dict(self) -> None:
        """Test converting result to dictionary."""
        result = EvaluationResult(
            context_precision=0.85,
            context_recall=0.75,
            faithfulness=0.90,
            answer_relevancy=0.80,
            overall_score=0.825,
        )

        result_dict = result.to_dict()

        assert result_dict["context_precision"] == 0.85
        assert result_dict["context_recall"] == 0.75
        assert result_dict["faithfulness"] == 0.90
        assert result_dict["answer_relevancy"] == 0.80
        assert result_dict["overall_score"] == 0.825

    def test_str_representation(self) -> None:
        """Test string representation of result."""
        result = EvaluationResult(
            context_precision=0.85,
            context_recall=0.75,
            faithfulness=0.90,
            answer_relevancy=0.80,
            overall_score=0.825,
        )

        result_str = str(result)

        assert "0.850" in result_str
        assert "0.750" in result_str
        assert "0.900" in result_str
        assert "0.800" in result_str
        assert "0.825" in result_str


class TestRAGASEvaluator:
    """Tests for RAGASEvaluator class."""

    def test_initialisation(self) -> None:
        """Test evaluator initialisation."""
        evaluator = RAGASEvaluator()

        # Verify all four metrics are initialised
        assert len(evaluator.metrics) == 4

    @patch("src.evaluation.ragas_evaluator.evaluate")
    def test_evaluate_batch(self, mock_evaluate: Mock) -> None:
        """Test batch evaluation."""
        # Mock RAGAS evaluate function
        mock_evaluate.return_value = {
            "context_precision": 0.85,
            "context_recall": 0.75,
            "faithfulness": 0.90,
            "answer_relevancy": 0.80,
        }

        evaluator = RAGASEvaluator()
        questions = ["What is RAG?", "How does it work?"]
        answers = ["RAG combines...", "It works by..."]
        contexts = [
            ["RAG is a technique...", "It combines retrieval..."],
            ["The system retrieves...", "Then generates..."],
        ]
        ground_truths = ["RAG is retrieval-augmented generation", "Retrieval then generation"]

        result = evaluator.evaluate(
            questions=questions,
            answers=answers,
            contexts=contexts,
            ground_truths=ground_truths,
        )

        # Verify result
        assert result.context_precision == 0.85
        assert result.context_recall == 0.75
        assert result.faithfulness == 0.90
        assert result.answer_relevancy == 0.80
        assert result.overall_score == 0.825  # Average of all metrics

        # Verify evaluate was called
        mock_evaluate.assert_called_once()

    @patch("src.evaluation.ragas_evaluator.evaluate")
    def test_evaluate_without_ground_truth(self, mock_evaluate: Mock) -> None:
        """Test evaluation without ground truth."""
        mock_evaluate.return_value = {
            "context_precision": 0.85,
            "context_recall": 0.75,
            "faithfulness": 0.90,
            "answer_relevancy": 0.80,
        }

        evaluator = RAGASEvaluator()
        questions = ["What is RAG?"]
        answers = ["RAG combines..."]
        contexts = [["RAG is a technique..."]]

        result = evaluator.evaluate(
            questions=questions,
            answers=answers,
            contexts=contexts,
            ground_truths=None,
        )

        assert result.overall_score == 0.825

    def test_evaluate_length_mismatch(self) -> None:
        """Test validation of input length mismatch."""
        evaluator = RAGASEvaluator()
        questions = ["What is RAG?", "How does it work?"]
        answers = ["RAG combines..."]  # Length mismatch
        contexts = [["RAG is a technique..."]]

        with pytest.raises(ValueError, match="Input length mismatch"):
            evaluator.evaluate(
                questions=questions,
                answers=answers,
                contexts=contexts,
            )

    def test_evaluate_ground_truth_length_mismatch(self) -> None:
        """Test validation of ground truth length mismatch."""
        evaluator = RAGASEvaluator()
        questions = ["What is RAG?", "How does it work?"]
        answers = ["RAG combines...", "It works by..."]
        contexts = [["Context 1"], ["Context 2"]]
        ground_truths = ["Only one ground truth"]  # Length mismatch

        with pytest.raises(ValueError, match="Ground truth length mismatch"):
            evaluator.evaluate(
                questions=questions,
                answers=answers,
                contexts=contexts,
                ground_truths=ground_truths,
            )

    @patch("src.evaluation.ragas_evaluator.evaluate")
    def test_evaluate_single(self, mock_evaluate: Mock) -> None:
        """Test single query evaluation."""
        mock_evaluate.return_value = {
            "context_precision": 0.85,
            "context_recall": 0.75,
            "faithfulness": 0.90,
            "answer_relevancy": 0.80,
        }

        evaluator = RAGASEvaluator()
        question = "What is RAG?"
        answer = "RAG combines retrieval and generation"
        contexts = ["RAG is a technique...", "It combines..."]
        ground_truth = "RAG is retrieval-augmented generation"

        result = evaluator.evaluate_single(
            question=question,
            answer=answer,
            contexts=contexts,
            ground_truth=ground_truth,
        )

        assert result.context_precision == 0.85
        assert result.overall_score == 0.825

    @patch("src.evaluation.ragas_evaluator.evaluate")
    def test_evaluate_single_without_ground_truth(self, mock_evaluate: Mock) -> None:
        """Test single query evaluation without ground truth."""
        mock_evaluate.return_value = {
            "context_precision": 0.85,
            "context_recall": 0.75,
            "faithfulness": 0.90,
            "answer_relevancy": 0.80,
        }

        evaluator = RAGASEvaluator()
        question = "What is RAG?"
        answer = "RAG combines retrieval and generation"
        contexts = ["RAG is a technique..."]

        result = evaluator.evaluate_single(
            question=question,
            answer=answer,
            contexts=contexts,
        )

        assert result.overall_score == 0.825

    def test_calculate_overall_score(self) -> None:
        """Test overall score calculation."""
        evaluator = RAGASEvaluator()

        # Test with all metrics
        result_dict = {
            "context_precision": 0.8,
            "context_recall": 0.7,
            "faithfulness": 0.9,
            "answer_relevancy": 0.6,
        }
        overall = evaluator._calculate_overall(result_dict)
        assert overall == 0.75  # (0.8 + 0.7 + 0.9 + 0.6) / 4

    def test_calculate_overall_with_none_values(self) -> None:
        """Test overall score calculation with None values."""
        evaluator = RAGASEvaluator()

        # Test with some None metrics
        result_dict = {
            "context_precision": 0.8,
            "context_recall": None,
            "faithfulness": 0.9,
            "answer_relevancy": 0.7,
        }
        overall = evaluator._calculate_overall(result_dict)
        assert overall == pytest.approx(0.8)  # (0.8 + 0.9 + 0.7) / 3

    def test_calculate_overall_all_none(self) -> None:
        """Test overall score calculation with all None values."""
        evaluator = RAGASEvaluator()

        result_dict = {
            "context_precision": None,
            "context_recall": None,
            "faithfulness": None,
            "answer_relevancy": None,
        }
        overall = evaluator._calculate_overall(result_dict)
        assert overall == 0.0
