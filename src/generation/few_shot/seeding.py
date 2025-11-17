"""Seeding default few-shot examples."""

import logging

from src.generation.few_shot.store import FewShotExampleStore

logger = logging.getLogger(__name__)


def seed_default_examples(store: FewShotExampleStore) -> None:
    """Seed the store with default examples.

    Args:
        store: Example store to seed
    """
    # Example 1: Factual retrieval
    store.add_example(
        query="What is machine learning?",
        context="[Source 1: ml_intro.pdf]\nMachine learning is a subset of artificial intelligence that enables systems to learn and improve from experience without being explicitly programmed. It focuses on the development of computer programs that can access data and use it to learn for themselves.",
        answer="Machine learning is a subset of artificial intelligence that allows systems to automatically learn and improve from experience without explicit programming. It involves developing algorithms that can access data and learn patterns from it to make predictions or decisions.",
        category="definition",
        tags=["AI", "machine learning", "basics"]
    )

    # Example 2: Comparative question
    store.add_example(
        query="What's the difference between supervised and unsupervised learning?",
        context="[Source 1: ml_types.pdf]\nSupervised learning uses labeled data where the correct output is known. The algorithm learns to map inputs to outputs. Common examples include classification and regression.\n\n[Source 2: ml_types.pdf]\nUnsupervised learning works with unlabeled data. The algorithm must find patterns and structure in the data without guidance. Clustering is a common unsupervised learning task.",
        answer="The key difference is in the training data:\n\nSupervised learning uses labeled data where correct answers are provided. The algorithm learns to predict outputs from inputs (e.g., classification, regression).\n\nUnsupervised learning works with unlabeled data. The algorithm must discover patterns and structure independently (e.g., clustering, dimensionality reduction).",
        category="comparison",
        tags=["machine learning", "supervised", "unsupervised"]
    )

    # Example 3: Process/How-to
    store.add_example(
        query="How does gradient descent work?",
        context="[Source 1: optimization.pdf]\nGradient descent is an optimisation algorithm used to minimise a cost function. It works by iteratively moving in the direction of steepest descent, which is the negative gradient. The learning rate determines the step size of each iteration.",
        answer="Gradient descent minimises a cost function through iterative steps:\n\n1. Calculate the gradient (slope) of the cost function\n2. Move in the opposite direction (negative gradient)\n3. The learning rate controls step size\n4. Repeat until convergence\n\nThis finds the minimum by following the steepest downward slope at each step.",
        category="process",
        tags=["optimisation", "gradient descent", "algorithms"]
    )

    # Example 4: Technical concept
    store.add_example(
        query="What is overfitting in machine learning?",
        context="[Source 1: model_evaluation.pdf]\nOverfitting occurs when a model learns the training data too well, including noise and outliers. The model performs well on training data but poorly on new, unseen data. It essentially memorises rather than generalises.",
        answer="Overfitting happens when a model learns training data too well, including noise and random fluctuations. While it achieves high accuracy on training data, it fails to generalise to new data.\n\nThis is like memorising answers instead of understanding concepts - the model performs poorly on unseen examples.",
        category="concept",
        tags=["machine learning", "overfitting", "model evaluation"]
    )

    # Example 5: When to use
    store.add_example(
        query="When should I use a decision tree vs neural network?",
        context="[Source 1: model_selection.pdf]\nDecision trees are interpretable, work well with structured data, and require less data. Neural networks excel with large datasets, unstructured data like images and text, but are less interpretable and require more computational resources.",
        answer="Choose based on your requirements:\n\nDecision Trees when you need:\n- Interpretability and explainability\n- Smaller structured datasets\n- Fast training\n- Simple deployment\n\nNeural Networks when you have:\n- Large amounts of data\n- Unstructured data (images, text, audio)\n- Complex patterns to learn\n- Computational resources available",
        category="selection",
        tags=["models", "decision trees", "neural networks"]
    )

    logger.info("Seeded 5 default few-shot examples")
