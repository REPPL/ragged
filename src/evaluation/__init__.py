"""
Evaluation module for RAG quality assessment.

This module provides tools for evaluating RAG pipeline quality using
industry-standard frameworks and custom metrics.
"""

from src.evaluation.ragas_evaluator import EvaluationResult, RAGASEvaluator

__all__ = ["RAGASEvaluator", "EvaluationResult"]
