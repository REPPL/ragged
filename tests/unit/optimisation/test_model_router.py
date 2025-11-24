"""
Tests for model routing (v0.6.2 OPTIMISE-002).

Success criteria:
- Routing accuracy >90% (correct model for query type)
- Routing decision latency <20ms (p95)
- 30-50% latency improvement for simple queries
- No quality regression for complex queries
"""

import time

import pytest

from ragged.optimisation import (
    ModelRouter,
    ModelSelection,
    QueryClassifier,
    QueryIntent,
    QueryType,
)


class TestModelSelection:
    """Test ModelSelection dataclass."""

    def test_model_selection_creation(self) -> None:
        """Test ModelSelection instantiation."""
        selection = ModelSelection(
            name="llama3.2:3b",
            tier="fast",
            estimated_latency_ms=300,
            rationale="Simple query",
            confidence=0.95,
            alternatives=["llama3.2:8b"],
            complexity_score=2,
        )

        assert selection.name == "llama3.2:3b"
        assert selection.tier == "fast"
        assert selection.estimated_latency_ms == 300
        assert selection.confidence == 0.95
        assert selection.complexity_score == 2

    def test_model_selection_to_dict(self) -> None:
        """Test ModelSelection serialisation."""
        selection = ModelSelection(
            name="llama3.2:8b",
            tier="balanced",
            estimated_latency_ms=800,
            rationale="Medium complexity query",
            confidence=0.88,
            alternatives=["llama3.2:3b", "llama3.2:70b"],
            complexity_score=4,
        )

        selection_dict = selection.to_dict()

        assert "name" in selection_dict
        assert "tier" in selection_dict
        assert "estimated_latency_ms" in selection_dict
        assert "rationale" in selection_dict
        assert "confidence" in selection_dict
        assert "alternatives" in selection_dict
        assert "complexity_score" in selection_dict

        assert selection_dict["name"] == "llama3.2:8b"
        assert selection_dict["tier"] == "balanced"
        assert isinstance(selection_dict["alternatives"], list)


class TestModelRouterInitialization:
    """Test ModelRouter initialization."""

    def test_default_initialization(self) -> None:
        """Test ModelRouter with default models."""
        router = ModelRouter()

        assert router.fast_model == "llama3.2:3b"
        assert router.balanced_model == "llama3.2:8b"
        assert router.quality_model == "llama3.2:70b"
        assert router.vision_model == "llava"
        assert router.default_model == "llama3.2:8b"

    def test_custom_initialization(self) -> None:
        """Test ModelRouter with custom models."""
        router = ModelRouter(
            fast_model="mistral:7b",
            balanced_model="llama3:8b",
            quality_model="llama3:90b",
            vision_model="llava:13b",
            default_model="mistral:7b",
        )

        assert router.fast_model == "mistral:7b"
        assert router.balanced_model == "llama3:8b"
        assert router.quality_model == "llama3:90b"
        assert router.vision_model == "llava:13b"
        assert router.default_model == "mistral:7b"


class TestComplexityBasedRouting:
    """Test routing based on query complexity."""

    @pytest.fixture
    def router(self) -> ModelRouter:
        """Create router instance."""
        return ModelRouter()

    @pytest.fixture
    def classifier(self) -> QueryClassifier:
        """Create classifier instance."""
        return QueryClassifier()

    def test_simple_query_routes_to_fast_model(
        self, router: ModelRouter, classifier: QueryClassifier
    ) -> None:
        """Test that simple queries route to fast model (3b)."""
        simple_queries = [
            "What is RAG?",
            "Define embedding",
            "List all models",
            "Who invented transformers?",
        ]

        for query in simple_queries:
            classification = classifier.classify(query)
            selection = router.select_model(classification)

            assert (
                selection.name == "llama3.2:3b"
            ), f"Failed for query: {query} (complexity: {classification.complexity})"
            assert selection.tier == "fast"
            assert selection.estimated_latency_ms == 300
            assert classification.complexity <= 2

    def test_medium_query_routes_to_balanced_model(
        self, router: ModelRouter, classifier: QueryClassifier
    ) -> None:
        """Test that medium queries route to balanced model (8b)."""
        medium_queries = [
            "How does RAG work and what are its main benefits for document retrieval?",
            "Explain the difference between BM25 and semantic search",
            "What are the benefits of using embeddings and how do they improve search?",
            "Why use vector databases for retrieval and what advantages do they offer?",
        ]

        for query in medium_queries:
            classification = classifier.classify(query)
            selection = router.select_model(classification)

            assert (
                selection.name == "llama3.2:8b"
            ), f"Failed for query: {query} (complexity: {classification.complexity})"
            assert selection.tier == "balanced"
            assert selection.estimated_latency_ms == 800
            assert 3 <= classification.complexity <= 5

    def test_complex_query_routes_to_quality_model(
        self, router: ModelRouter, classifier: QueryClassifier
    ) -> None:
        """Test that complex queries route to quality model (70b)."""
        complex_queries = [
            "Compare RAG with fine-tuning, consider all trade-offs, and recommend the best approach for my use case",
            "Analyze the trade-offs between BM25 and semantic search for different document types, considering both precision and recall metrics",
            "How does ColPali compare to traditional OCR for document understanding, and what are the architectural differences?",
        ]

        for query in complex_queries:
            classification = classifier.classify(query)
            selection = router.select_model(classification)

            # Skip vision queries (they route to vision model instead)
            if "vision" in classification.domain_hints:
                continue

            assert (
                selection.name == "llama3.2:70b"
            ), f"Failed for query: {query} (complexity: {classification.complexity})"
            assert selection.tier == "quality"
            assert selection.estimated_latency_ms == 2500
            assert classification.complexity >= 6


class TestVisionQueryRouting:
    """Test routing for vision/multi-modal queries."""

    @pytest.fixture
    def router(self) -> ModelRouter:
        """Create router instance."""
        return ModelRouter()

    @pytest.fixture
    def classifier(self) -> QueryClassifier:
        """Create classifier instance."""
        return QueryClassifier()

    def test_vision_query_routes_to_vision_model(
        self, router: ModelRouter, classifier: QueryClassifier
    ) -> None:
        """Test that vision queries route to vision model."""
        vision_queries = [
            "How does ColPali process images?",
            "Extract text from this photo using OCR",
            "Analyze this visual diagram",
            "What's in this picture?",
        ]

        for query in vision_queries:
            classification = classifier.classify(query)
            selection = router.select_model(classification)

            assert (
                selection.name == "llava"
            ), f"Failed for query: {query} (domain hints: {classification.domain_hints})"
            assert selection.tier == "vision"
            assert selection.estimated_latency_ms == 3000
            assert "vision" in classification.domain_hints


class TestRoutingConfidence:
    """Test routing confidence scoring."""

    @pytest.fixture
    def router(self) -> ModelRouter:
        """Create router instance."""
        return ModelRouter()

    @pytest.fixture
    def classifier(self) -> QueryClassifier:
        """Create classifier instance."""
        return QueryClassifier()

    def test_confidence_high_for_clear_simple_queries(
        self, router: ModelRouter, classifier: QueryClassifier
    ) -> None:
        """Test that clearly simple queries have high confidence."""
        query = "What is RAG?"
        classification = classifier.classify(query)
        selection = router.select_model(classification)

        assert selection.confidence >= 0.9, "Simple query should have high confidence"

    def test_confidence_moderate_for_borderline_queries(
        self, router: ModelRouter, classifier: QueryClassifier
    ) -> None:
        """Test that borderline queries have moderate confidence."""
        # Complexity ~3 (borderline between fast and balanced)
        query = "How does semantic search work with embeddings?"
        classification = classifier.classify(query)
        selection = router.select_model(classification)

        assert (
            0.7 <= selection.confidence <= 0.95
        ), "Borderline query should have moderate confidence"

    def test_confidence_high_for_multi_hop_quality_routing(
        self, router: ModelRouter, classifier: QueryClassifier
    ) -> None:
        """Test that multi-hop queries routed to quality have high confidence."""
        query = (
            "Compare RAG and fine-tuning, then recommend the best approach"
        )
        classification = classifier.classify(query)
        selection = router.select_model(classification)

        assert classification.is_multi_hop
        assert selection.tier == "quality"
        assert selection.confidence >= 0.85


class TestRoutingMetadata:
    """Test routing decision metadata."""

    @pytest.fixture
    def router(self) -> ModelRouter:
        """Create router instance."""
        return ModelRouter()

    @pytest.fixture
    def classifier(self) -> QueryClassifier:
        """Create classifier instance."""
        return QueryClassifier()

    def test_rationale_includes_query_type(
        self, router: ModelRouter, classifier: QueryClassifier
    ) -> None:
        """Test that rationale includes query type."""
        query = "What is RAG?"
        classification = classifier.classify(query)
        selection = router.select_model(classification)

        assert isinstance(selection.rationale, str)
        assert len(selection.rationale) > 0
        # Should mention factual query type
        assert "factual" in selection.rationale.lower()

    def test_rationale_includes_complexity(
        self, router: ModelRouter, classifier: QueryClassifier
    ) -> None:
        """Test that rationale includes complexity score."""
        query = "How does RAG work?"
        classification = classifier.classify(query)
        selection = router.select_model(classification)

        assert str(classification.complexity) in selection.rationale
        assert "/10" in selection.rationale  # Complexity out of 10

    def test_alternatives_provided(
        self, router: ModelRouter, classifier: QueryClassifier
    ) -> None:
        """Test that alternative models are provided."""
        query = "Explain embeddings"
        classification = classifier.classify(query)
        selection = router.select_model(classification)

        assert isinstance(selection.alternatives, list)
        assert len(selection.alternatives) > 0
        assert selection.name not in selection.alternatives

    def test_complexity_score_matches_classification(
        self, router: ModelRouter, classifier: QueryClassifier
    ) -> None:
        """Test that complexity score matches classification."""
        query = "Compare RAG and fine-tuning"
        classification = classifier.classify(query)
        selection = router.select_model(classification)

        assert selection.complexity_score == classification.complexity


class TestRoutingPerformance:
    """Test routing performance benchmarks."""

    @pytest.fixture
    def router(self) -> ModelRouter:
        """Create router instance."""
        return ModelRouter()

    @pytest.fixture
    def classifier(self) -> QueryClassifier:
        """Create classifier instance."""
        return QueryClassifier()

    def test_routing_latency(
        self, router: ModelRouter, classifier: QueryClassifier
    ) -> None:
        """Test that routing decision completes in <20ms (p95)."""
        test_queries = [
            "What is RAG?",
            "How does semantic search work?",
            "Compare RAG and fine-tuning",
            "Analyze this image using OCR",
        ]

        latencies = []
        for query in test_queries:
            classification = classifier.classify(query)

            start_time = time.perf_counter()
            _ = router.select_model(classification)
            end_time = time.perf_counter()

            latency_ms = (end_time - start_time) * 1000
            latencies.append(latency_ms)

        # Check p95 latency
        latencies_sorted = sorted(latencies)
        p95_index = int(len(latencies_sorted) * 0.95)
        p95_latency = latencies_sorted[p95_index]

        assert (
            p95_latency < 20
        ), f"p95 routing latency {p95_latency:.2f}ms exceeds 20ms threshold"

    def test_batch_routing_performance(
        self, router: ModelRouter, classifier: QueryClassifier
    ) -> None:
        """Test batch routing performance."""
        queries = [
            "What is RAG?",
            "How does it work?",
            "Compare X and Y",
        ] * 10  # 30 routing decisions

        classifications = [classifier.classify(q) for q in queries]

        start_time = time.perf_counter()
        for classification in classifications:
            _ = router.select_model(classification)
        end_time = time.perf_counter()

        total_time_ms = (end_time - start_time) * 1000
        avg_time_ms = total_time_ms / len(queries)

        assert (
            avg_time_ms < 20
        ), f"Average routing time {avg_time_ms:.2f}ms exceeds 20ms"


class TestEdgeCases:
    """Test edge cases and error handling."""

    @pytest.fixture
    def router(self) -> ModelRouter:
        """Create router instance."""
        return ModelRouter()

    @pytest.fixture
    def classifier(self) -> QueryClassifier:
        """Create classifier instance."""
        return QueryClassifier()

    def test_empty_query_routing(
        self, router: ModelRouter, classifier: QueryClassifier
    ) -> None:
        """Test routing for empty query."""
        query = ""
        classification = classifier.classify(query)
        selection = router.select_model(classification)

        # Should not crash, provides sensible default
        assert isinstance(selection, ModelSelection)
        assert selection.name in [
            router.fast_model,
            router.balanced_model,
            router.quality_model,
        ]

    def test_very_long_query_routing(
        self, router: ModelRouter, classifier: QueryClassifier
    ) -> None:
        """Test routing for very long query."""
        long_query = " ".join(["word"] * 200)  # 200-word query
        classification = classifier.classify(long_query)
        selection = router.select_model(classification)

        # Long complex query should route to quality model
        assert selection.tier in ["balanced", "quality"]

    def test_mixed_domain_hints(
        self, router: ModelRouter, classifier: QueryClassifier
    ) -> None:
        """Test routing with multiple domain hints."""
        # Query with both vision and technical domains
        query = "How does the OCR API process images using computer vision algorithms?"
        classification = classifier.classify(query)
        selection = router.select_model(classification)

        # Vision should take priority
        if "vision" in classification.domain_hints:
            assert selection.tier == "vision"
