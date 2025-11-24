"""
Routing metadata preparation for intelligent model selection (v0.6.1 OPTIMISE-001).

Prepares metadata from query classification for model routing decisions
in v0.6.2 (Automatic Model Routing).
"""

from dataclasses import dataclass

from ragged.optimisation.query_classifier import QueryClassification, QueryIntent, QueryType


@dataclass
class RoutingMetadata:
    """
    Metadata for routing decisions.

    Prepared from QueryClassification to guide model selection, caching,
    and optimisation strategies in subsequent versions.

    v0.6.1: Foundation for v0.6.2 (Automatic Model Routing)
    """

    recommended_model: str  # Model name for this query
    estimated_latency_ms: int  # Expected latency
    requires_vision: bool  # Needs multi-modal model
    cache_priority: str  # "high", "medium", "low"
    complexity_tier: str  # "simple", "medium", "complex"

    @classmethod
    def from_classification(cls, classification: QueryClassification) -> "RoutingMetadata":
        """
        Create routing metadata from query classification.

        Args:
            classification: QueryClassification result

        Returns:
            RoutingMetadata with routing recommendations

        Example:
            >>> from ragged.optimisation import QueryClassifier, RoutingMetadata
            >>> classifier = QueryClassifier()
            >>> classification = classifier.classify("How does RAG work?")
            >>> metadata = RoutingMetadata.from_classification(classification)
            >>> metadata.recommended_model
            'llama3.2:8b'
        """
        # Determine complexity tier
        if classification.complexity <= 2:
            complexity_tier = "simple"
        elif classification.complexity <= 5:
            complexity_tier = "medium"
        else:
            complexity_tier = "complex"

        # Recommend model based on complexity and type
        recommended_model = cls._recommend_model(classification, complexity_tier)

        # Estimate latency based on model
        estimated_latency_ms = cls._estimate_latency(recommended_model)

        # Check if vision model needed
        requires_vision = "vision" in classification.domain_hints

        # Determine cache priority
        cache_priority = cls._determine_cache_priority(classification)

        return cls(
            recommended_model=recommended_model,
            estimated_latency_ms=estimated_latency_ms,
            requires_vision=requires_vision,
            cache_priority=cache_priority,
            complexity_tier=complexity_tier,
        )

    @staticmethod
    def _recommend_model(classification: QueryClassification, complexity_tier: str) -> str:
        """
        Recommend model based on query characteristics.

        Model selection strategy (v0.6.2 will actually use these):
        - Simple queries (1-2) → llama3.2:3b (fast, 200-400ms)
        - Medium queries (3-5) → llama3.2:8b (balanced, 600-1000ms)
        - Complex queries (6-10) → llama3.2:70b (quality, 2000-3000ms)
        - Vision queries → llava or llama3.2-vision:90b
        """
        # Check for vision requirement first
        if "vision" in classification.domain_hints:
            return "llava"

        # Select based on complexity tier
        if complexity_tier == "simple":
            return "llama3.2:3b"
        elif complexity_tier == "medium":
            return "llama3.2:8b"
        else:  # complex
            return "llama3.2:70b"

    @staticmethod
    def _estimate_latency(model_name: str) -> int:
        """
        Estimate query latency based on model.

        These are approximations based on model size and typical performance.
        Actual latency depends on hardware, context length, etc.
        """
        latency_estimates = {
            "llama3.2:3b": 300,  # Fast model
            "llama3.2:8b": 800,  # Balanced model
            "llama3.2:70b": 2500,  # Quality model
            "llava": 1200,  # Vision model
            "llama3.2-vision:90b": 3000,  # Large vision model
        }
        return latency_estimates.get(model_name, 1000)  # Default 1s

    @staticmethod
    def _determine_cache_priority(classification: QueryClassification) -> str:
        """
        Determine caching priority based on query characteristics.

        Factual lookups cache well, while complex analysis may not.
        """
        # Factual queries are highly cacheable
        if classification.query_type == QueryType.FACTUAL:
            return "high"

        # Multi-hop and synthesis queries are less cacheable
        if classification.query_type == QueryType.MULTI_HOP or classification.intent == QueryIntent.SYNTHESIS:
            return "low"

        # Everything else is medium priority
        return "medium"

    def to_dict(self) -> dict:
        """Convert to dictionary for serialisation."""
        return {
            "recommended_model": self.recommended_model,
            "estimated_latency_ms": self.estimated_latency_ms,
            "requires_vision": self.requires_vision,
            "cache_priority": self.cache_priority,
            "complexity_tier": self.complexity_tier,
        }
