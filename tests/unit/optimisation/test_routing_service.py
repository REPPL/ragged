"""
Tests for integrated routing service (v0.6.2 OPTIMISE-002 Phase 3).

Success criteria:
- End-to-end routing workflow functional
- Fallback logic activates when needed
- Routing latency <20ms (p95)
- Integration between all components successful
"""

import time

import pytest

from ragged.optimisation import (
    ModelInfo,
    ModelManager,
    ModelRouter,
    QueryClassifier,
    RoutingDecision,
    RoutingService,
)


class TestRoutingDecision:
    """Test RoutingDecision dataclass."""

    def test_routing_decision_to_dict(self) -> None:
        """Test RoutingDecision serialisation."""
        service = RoutingService()
        decision = service.route("What is RAG?")

        decision_dict = decision.to_dict()

        assert "query" in decision_dict
        assert "classification" in decision_dict
        assert "selection" in decision_dict
        assert "model_loaded" in decision_dict
        assert "fallback_used" in decision_dict
        assert "routing_latency_ms" in decision_dict
        assert "error" in decision_dict


class TestRoutingServiceInitialization:
    """Test RoutingService initialization."""

    def test_default_initialization(self) -> None:
        """Test RoutingService with default components."""
        service = RoutingService()

        assert service.classifier is not None
        assert service.router is not None
        assert service.manager is not None
        assert service.enable_fallback is True
        assert service.enable_auto_load is True

    def test_custom_components_initialization(self) -> None:
        """Test RoutingService with custom components."""
        classifier = QueryClassifier()
        router = ModelRouter(fast_model="mistral:7b")
        manager = ModelManager(max_loaded_models=5)

        service = RoutingService(
            classifier=classifier, router=router, manager=manager
        )

        assert service.classifier is classifier
        assert service.router is router
        assert service.manager is manager

    def test_custom_settings_initialization(self) -> None:
        """Test RoutingService with custom settings."""
        service = RoutingService(enable_fallback=False, enable_auto_load=False)

        assert service.enable_fallback is False
        assert service.enable_auto_load is False


class TestEndToEndRouting:
    """Test complete routing workflow."""

    @pytest.fixture
    def service(self) -> RoutingService:
        """Create routing service instance."""
        return RoutingService()

    def test_simple_query_routing(self, service: RoutingService) -> None:
        """Test routing for simple query."""
        decision = service.route("What is RAG?")

        assert decision.query == "What is RAG?"
        assert decision.classification.complexity <= 2
        assert decision.selection.name == "llama3.2:3b"
        assert decision.selection.tier == "fast"
        assert decision.fallback_used is False
        assert decision.error is None

    def test_medium_query_routing(self, service: RoutingService) -> None:
        """Test routing for medium complexity query."""
        decision = service.route(
            "How does RAG work and what are its benefits for document retrieval?"
        )

        assert decision.classification.complexity >= 3
        assert decision.classification.complexity <= 5
        assert decision.selection.name == "llama3.2:8b"
        assert decision.selection.tier == "balanced"

    def test_complex_query_routing(self, service: RoutingService) -> None:
        """Test routing for complex query."""
        decision = service.route(
            "Compare RAG with fine-tuning, consider all trade-offs, and recommend the best approach"
        )

        assert decision.classification.complexity >= 6
        assert decision.selection.name == "llama3.2:70b"
        assert decision.selection.tier == "quality"

    def test_vision_query_routing(self, service: RoutingService) -> None:
        """Test routing for vision query."""
        decision = service.route("How does ColPali process images?")

        assert "vision" in decision.classification.domain_hints
        assert decision.selection.name == "llava"
        assert decision.selection.tier == "vision"

    def test_model_loaded_after_routing(self, service: RoutingService) -> None:
        """Test that model is loaded after routing."""
        decision = service.route("What is RAG?")

        # With auto_load enabled, model should be loaded
        assert decision.model_loaded is True
        assert decision.selection.name in service.manager.get_loaded_models()


class TestFallbackBehavior:
    """Test fallback model selection."""

    def test_no_fallback_when_disabled(self) -> None:
        """Test no fallback when disabled."""
        manager = ModelManager(ollama_available=False)
        service = RoutingService(
            manager=manager, enable_fallback=False, enable_auto_load=True
        )

        decision = service.route("What is RAG?")

        assert decision.fallback_used is False
        assert decision.error is not None
        assert "unavailable" in decision.error.lower()


class TestAutoLoad:
    """Test automatic model loading."""

    def test_auto_load_enabled(self) -> None:
        """Test models auto-load when enabled."""
        service = RoutingService(enable_auto_load=True)
        decision = service.route("What is RAG?")

        assert decision.model_loaded is True

    def test_auto_load_disabled(self) -> None:
        """Test models don't auto-load when disabled."""
        service = RoutingService(enable_auto_load=False)
        decision = service.route("What is RAG?")

        assert decision.model_loaded is False
        # But routing still succeeds
        assert decision.error is None


class TestPerformance:
    """Test routing performance."""

    @pytest.fixture
    def service(self) -> RoutingService:
        """Create routing service instance."""
        return RoutingService()

    def test_routing_latency(self, service: RoutingService) -> None:
        """Test routing latency <20ms (p95)."""
        test_queries = [
            "What is RAG?",
            "How does semantic search work?",
            "Compare RAG and fine-tuning",
            "Analyze this image",
        ]

        latencies = []
        for query in test_queries:
            decision = service.route(query)
            latencies.append(decision.routing_latency_ms)

        # Check p95 latency
        latencies_sorted = sorted(latencies)
        p95_index = int(len(latencies_sorted) * 0.95)
        p95_latency = latencies_sorted[p95_index]

        assert (
            p95_latency < 20
        ), f"p95 routing latency {p95_latency:.2f}ms exceeds 20ms threshold"

    def test_batch_routing_performance(self, service: RoutingService) -> None:
        """Test batch routing performance."""
        queries = ["What is RAG?", "How does it work?", "Compare X and Y"] * 10

        start_time = time.perf_counter()
        for query in queries:
            _ = service.route(query)
        end_time = time.perf_counter()

        total_time_ms = (end_time - start_time) * 1000
        avg_time_ms = total_time_ms / len(queries)

        assert (
            avg_time_ms < 20
        ), f"Average routing time {avg_time_ms:.2f}ms exceeds 20ms"


class TestWarmUp:
    """Test model warm-up functionality."""

    @pytest.fixture
    def service(self) -> RoutingService:
        """Create routing service instance."""
        return RoutingService()

    def test_warm_up_single_model(self, service: RoutingService) -> None:
        """Test warming up single model."""
        results = service.warm_up(["llama3.2:3b"])

        assert "llama3.2:3b" in results
        assert results["llama3.2:3b"] is True
        assert "llama3.2:3b" in service.manager.get_loaded_models()

    def test_warm_up_multiple_models(self, service: RoutingService) -> None:
        """Test warming up multiple models."""
        results = service.warm_up(["llama3.2:3b", "llama3.2:8b"])

        assert results["llama3.2:3b"] is True
        assert results["llama3.2:8b"] is True
        assert len(service.manager.get_loaded_models()) == 2

    def test_warm_up_unavailable_model(self, service: RoutingService) -> None:
        """Test warming up unavailable model."""
        results = service.warm_up(["unknown:model"])

        assert "unknown:model" in results
        assert results["unknown:model"] is False


class TestStatus:
    """Test service status reporting."""

    @pytest.fixture
    def service(self) -> RoutingService:
        """Create routing service instance."""
        return RoutingService()

    def test_get_status_initial(self, service: RoutingService) -> None:
        """Test status before any routing."""
        status = service.get_status()

        assert "loaded_models" in status
        assert "available_models" in status
        assert "memory_usage_gb" in status
        assert "enable_fallback" in status
        assert "enable_auto_load" in status

        assert isinstance(status["loaded_models"], list)
        assert len(status["loaded_models"]) == 0
        assert status["memory_usage_gb"] == 0.0

    def test_get_status_after_routing(self, service: RoutingService) -> None:
        """Test status after routing."""
        service.route("What is RAG?")
        status = service.get_status()

        assert len(status["loaded_models"]) >= 1
        assert status["memory_usage_gb"] > 0.0


class TestErrorHandling:
    """Test error handling in routing."""

    def test_empty_query(self) -> None:
        """Test routing with empty query."""
        service = RoutingService()
        decision = service.route("")

        # Should not crash
        assert decision.query == ""
        assert decision.error is None

    def test_very_long_query(self) -> None:
        """Test routing with very long query."""
        service = RoutingService()
        long_query = " ".join(["word"] * 200)
        decision = service.route(long_query)

        # Should handle gracefully
        assert decision.query == long_query
        assert decision.selection.name in [
            "llama3.2:8b",
            "llama3.2:70b",
        ]  # Medium or complex

    def test_routing_with_all_models_unavailable(self) -> None:
        """Test routing when all models unavailable."""
        manager = ModelManager(ollama_available=False)
        service = RoutingService(
            manager=manager, enable_fallback=True, enable_auto_load=True
        )

        decision = service.route("What is RAG?")

        # Should provide decision with error
        assert decision.error is not None
        assert decision.model_loaded is False
