"""
Model routing for intelligent model selection (v0.6.2 OPTIMISE-002).

Automatically selects optimal models based on query classification:
- Simple queries → fast models (llama3.2:3b)
- Medium queries → balanced models (llama3.2:8b)
- Complex queries → quality models (llama3.2:70b)
- Vision queries → multi-modal models (llava)

Performance targets:
- Routing decision latency: <20ms (p95)
- Routing accuracy: >90%
- 30-50% latency reduction for simple queries
"""

import logging
from dataclasses import dataclass
from typing import Any

from ragged.optimisation.query_classifier import QueryClassification

logger = logging.getLogger(__name__)


@dataclass
class ModelSelection:
    """
    Routing decision for a query.

    Contains the selected model and metadata about the routing decision.

    v0.6.2 OPTIMISE-002: Model routing foundation
    """

    name: str  # Model name (e.g. "llama3.2:3b")
    tier: str  # "fast", "balanced", "quality", "vision"
    estimated_latency_ms: int  # Expected latency
    rationale: str  # Why this model was selected
    confidence: float  # Routing confidence (0.0-1.0)
    alternatives: list[str]  # Alternative models considered
    complexity_score: int  # Query complexity (from classification)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialisation."""
        return {
            "name": self.name,
            "tier": self.tier,
            "estimated_latency_ms": self.estimated_latency_ms,
            "rationale": self.rationale,
            "confidence": self.confidence,
            "alternatives": self.alternatives,
            "complexity_score": self.complexity_score,
        }


class ModelRouter:
    """
    Intelligent model routing based on query classification.

    Routes queries to optimal models based on:
    - Query complexity (from QueryClassifier)
    - Domain requirements (vision, embeddings, etc.)
    - Performance targets (latency vs quality trade-off)

    v0.6.2 OPTIMISE-002: Automatic model routing

    Example:
        >>> from ragged.optimisation import QueryClassifier, ModelRouter
        >>> classifier = QueryClassifier()
        >>> router = ModelRouter()
        >>> query = "What is RAG?"
        >>> classification = classifier.classify(query)
        >>> selection = router.select_model(classification)
        >>> selection.name
        'llama3.2:3b'
        >>> selection.estimated_latency_ms
        300
    """

    # Model configurations (v0.6.2 defaults)
    FAST_MODEL = {
        "name": "llama3.2:3b",
        "tier": "fast",
        "max_complexity": 2,
        "latency_ms": 300,
    }

    BALANCED_MODEL = {
        "name": "llama3.2:8b",
        "tier": "balanced",
        "max_complexity": 5,
        "latency_ms": 800,
    }

    QUALITY_MODEL = {
        "name": "llama3.2:70b",
        "tier": "quality",
        "max_complexity": 10,
        "latency_ms": 2500,
    }

    VISION_MODEL = {
        "name": "llava",
        "tier": "vision",
        "max_complexity": 10,
        "latency_ms": 3000,
    }

    def __init__(
        self,
        fast_model: str = "llama3.2:3b",
        balanced_model: str = "llama3.2:8b",
        quality_model: str = "llama3.2:70b",
        vision_model: str = "llava",
        default_model: str = "llama3.2:8b",
    ) -> None:
        """
        Initialise model router with configurable models.

        Args:
            fast_model: Model for simple queries (complexity 1-2)
            balanced_model: Model for medium queries (complexity 3-5)
            quality_model: Model for complex queries (complexity 6-10)
            vision_model: Model for vision/multi-modal queries
            default_model: Fallback model if routing fails

        Example:
            >>> # Use defaults
            >>> router = ModelRouter()
            >>> # Custom models
            >>> router = ModelRouter(
            ...     fast_model="mistral:7b",
            ...     quality_model="llama3.2:90b"
            ... )
        """
        self.fast_model = fast_model
        self.balanced_model = balanced_model
        self.quality_model = quality_model
        self.vision_model = vision_model
        self.default_model = default_model

        logger.debug(
            f"ModelRouter initialised: "
            f"fast={fast_model}, balanced={balanced_model}, "
            f"quality={quality_model}, vision={vision_model}"
        )

    def select_model(self, classification: QueryClassification) -> ModelSelection:
        """
        Select optimal model based on query classification.

        Routing logic:
        1. Vision queries → vision model (highest priority)
        2. Complexity 1-2 → fast model (3b)
        3. Complexity 3-5 → balanced model (8b)
        4. Complexity 6-10 → quality model (70b)

        Args:
            classification: QueryClassification from QueryClassifier

        Returns:
            ModelSelection with routing decision

        Example:
            >>> classifier = QueryClassifier()
            >>> router = ModelRouter()
            >>> classification = classifier.classify("What is RAG?")
            >>> selection = router.select_model(classification)
            >>> print(selection.name)  # "llama3.2:3b"
            >>> print(selection.rationale)  # "Simple factual query..."
        """
        complexity = classification.complexity
        domain_hints = classification.domain_hints

        # Priority 1: Vision queries (require multi-modal model)
        if "vision" in domain_hints:
            return self._select_vision_model(classification)

        # Priority 2: Complexity-based routing
        if complexity <= 2:
            return self._select_fast_model(classification)
        elif complexity <= 5:
            return self._select_balanced_model(classification)
        else:
            return self._select_quality_model(classification)

    def _select_fast_model(self, classification: QueryClassification) -> ModelSelection:
        """Select fast model for simple queries (complexity 1-2)."""
        return ModelSelection(
            name=self.fast_model,
            tier="fast",
            estimated_latency_ms=self.FAST_MODEL["latency_ms"],
            rationale=(
                f"Simple {classification.query_type.value} query with low complexity "
                f"({classification.complexity}/10). Fast model optimises for latency."
            ),
            confidence=self._calculate_confidence(classification, "fast"),
            alternatives=[self.balanced_model, self.quality_model],
            complexity_score=classification.complexity,
        )

    def _select_balanced_model(
        self, classification: QueryClassification
    ) -> ModelSelection:
        """Select balanced model for medium queries (complexity 3-5)."""
        return ModelSelection(
            name=self.balanced_model,
            tier="balanced",
            estimated_latency_ms=self.BALANCED_MODEL["latency_ms"],
            rationale=(
                f"Medium complexity {classification.query_type.value} query "
                f"({classification.complexity}/10). Balanced model provides good "
                f"trade-off between latency and quality."
            ),
            confidence=self._calculate_confidence(classification, "balanced"),
            alternatives=[self.fast_model, self.quality_model],
            complexity_score=classification.complexity,
        )

    def _select_quality_model(
        self, classification: QueryClassification
    ) -> ModelSelection:
        """Select quality model for complex queries (complexity 6-10)."""
        return ModelSelection(
            name=self.quality_model,
            tier="quality",
            estimated_latency_ms=self.QUALITY_MODEL["latency_ms"],
            rationale=(
                f"Complex {classification.query_type.value} query "
                f"({classification.complexity}/10). Quality model ensures high "
                f"accuracy for demanding analysis."
            ),
            confidence=self._calculate_confidence(classification, "quality"),
            alternatives=[self.balanced_model],
            complexity_score=classification.complexity,
        )

    def _select_vision_model(
        self, classification: QueryClassification
    ) -> ModelSelection:
        """Select vision model for multi-modal queries."""
        return ModelSelection(
            name=self.vision_model,
            tier="vision",
            estimated_latency_ms=self.VISION_MODEL["latency_ms"],
            rationale=(
                f"Vision/multi-modal query detected (domain hints: {classification.domain_hints}). "
                f"Requires multi-modal model for image understanding."
            ),
            confidence=0.95,  # High confidence for vision queries
            alternatives=[self.quality_model],  # Fallback if vision unavailable
            complexity_score=classification.complexity,
        )

    def _calculate_confidence(
        self, classification: QueryClassification, tier: str
    ) -> float:
        """
        Calculate routing confidence based on query characteristics.

        Higher confidence when:
        - Complexity clearly in tier range
        - Single dominant query type
        - No conflicting domain hints

        Args:
            classification: Query classification
            tier: Selected tier ("fast", "balanced", "quality")

        Returns:
            Confidence score (0.0-1.0)
        """
        complexity = classification.complexity

        # Base confidence by tier fit
        if tier == "fast":
            # Complexity 1-2: High confidence at 1, decreasing toward 2
            base_confidence = 1.0 - (complexity - 1) * 0.1
        elif tier == "balanced":
            # Complexity 3-5: Highest at 4, decreasing toward edges
            distance_from_center = abs(4 - complexity)
            base_confidence = 1.0 - distance_from_center * 0.1
        else:  # quality
            # Complexity 6-10: Increasing confidence with complexity
            base_confidence = 0.8 + (complexity - 6) * 0.04

        # Adjust for multi-hop (increases confidence in quality tier)
        if classification.is_multi_hop and tier == "quality":
            base_confidence = min(base_confidence + 0.1, 1.0)

        # Adjust for domain hints (may suggest specific model needed)
        if classification.domain_hints and tier != "vision":
            # Reduce confidence slightly if domain hints present but not using vision
            base_confidence = max(base_confidence - 0.05, 0.7)

        return round(base_confidence, 2)
