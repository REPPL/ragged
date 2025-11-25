"""
Integrated routing service (v0.6.2 OPTIMISE-002 Phase 3).

Unified interface for automatic model routing combining:
- Query classification (QueryClassifier)
- Model selection (ModelRouter)
- Model lifecycle management (ModelManager)

Provides single entry point for intelligent query routing.
"""

import logging
import time
from dataclasses import dataclass
from typing import Any

from ragged.optimisation.model_manager import ModelManager
from ragged.optimisation.model_router import ModelRouter, ModelSelection
from ragged.optimisation.query_classifier import QueryClassification, QueryClassifier

logger = logging.getLogger(__name__)


@dataclass
class RoutingDecision:
    """
    Complete routing decision for a query.

    Contains all metadata from classification, routing, and model management.

    v0.6.2 OPTIMISE-002: Integrated routing decision
    """

    query: str  # Original query
    classification: QueryClassification  # Query analysis
    selection: ModelSelection  # Model selection
    model_loaded: bool  # Whether model is loaded and ready
    fallback_used: bool  # Whether fallback model was used
    routing_latency_ms: float  # Time taken for routing decision
    error: str | None = None  # Error message if routing failed

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialisation."""
        return {
            "query": self.query,
            "classification": self.classification.to_dict(),
            "selection": self.selection.to_dict(),
            "model_loaded": self.model_loaded,
            "fallback_used": self.fallback_used,
            "routing_latency_ms": self.routing_latency_ms,
            "error": self.error,
        }


class RoutingService:
    """
    Unified routing service for automatic model selection.

    Integrates classification, routing, and model management into
    a single interface for intelligent query processing.

    v0.6.2 OPTIMISE-002 Phase 3: Service integration

    Example:
        >>> service = RoutingService()
        >>> decision = service.route("What is RAG?")
        >>> decision.selection.name
        'llama3.2:3b'
        >>> decision.model_loaded
        True
        >>> decision.routing_latency_ms < 20
        True
    """

    def __init__(
        self,
        classifier: QueryClassifier | None = None,
        router: ModelRouter | None = None,
        manager: ModelManager | None = None,
        enable_fallback: bool = True,
        enable_auto_load: bool = True,
    ) -> None:
        """
        Initialise routing service.

        Args:
            classifier: QueryClassifier instance (creates if None)
            router: ModelRouter instance (creates if None)
            manager: ModelManager instance (creates if None)
            enable_fallback: Use fallback models when primary unavailable
            enable_auto_load: Automatically load models

        Example:
            >>> # Use defaults
            >>> service = RoutingService()
            >>> # Custom components
            >>> classifier = QueryClassifier()
            >>> router = ModelRouter(fast_model="mistral:7b")
            >>> manager = ModelManager(max_loaded_models=5)
            >>> service = RoutingService(
            ...     classifier=classifier,
            ...     router=router,
            ...     manager=manager
            ... )
        """
        self.classifier = classifier or QueryClassifier()
        self.router = router or ModelRouter()
        self.manager = manager or ModelManager()
        self.enable_fallback = enable_fallback
        self.enable_auto_load = enable_auto_load

        logger.info(
            f"RoutingService initialised: "
            f"fallback={enable_fallback}, auto_load={enable_auto_load}"
        )

    def route(self, query: str) -> RoutingDecision:
        """
        Route a query to the optimal model.

        Complete workflow:
        1. Classify query (QueryClassifier)
        2. Select model (ModelRouter)
        3. Ensure model loaded (ModelManager)
        4. Handle fallback if needed
        5. Return routing decision

        Args:
            query: User query string

        Returns:
            RoutingDecision with complete metadata

        Example:
            >>> service = RoutingService()
            >>> decision = service.route("How does RAG work?")
            >>> print(decision.selection.name)  # "llama3.2:8b"
            >>> print(decision.classification.complexity)  # 4
            >>> print(decision.routing_latency_ms)  # ~15ms
        """
        start_time = time.perf_counter()
        fallback_used = False
        error = None

        try:
            # Step 1: Classify query
            classification = self.classifier.classify(query)
            logger.debug(
                f"Query classified: type={classification.query_type.value}, "
                f"complexity={classification.complexity}"
            )

            # Step 2: Select model
            selection = self.router.select_model(classification)
            logger.debug(
                f"Model selected: {selection.name} (tier={selection.tier}, "
                f"confidence={selection.confidence})"
            )

            # Step 3: Ensure model available and loaded
            model_loaded = False
            selected_model = selection.name

            if self.enable_auto_load:
                try:
                    # Check if model is available
                    if not self.manager.is_model_available(selected_model):
                        if self.enable_fallback:
                            # Try fallback model
                            fallback_model = self.manager.get_fallback_model(
                                selected_model, selection.tier
                            )
                            if fallback_model:
                                selected_model = fallback_model
                                fallback_used = True
                                logger.info(
                                    f"Using fallback model {fallback_model} for {selection.name}"
                                )

                                # Update selection to reflect fallback
                                selection = ModelSelection(
                                    name=fallback_model,
                                    tier=selection.tier,
                                    estimated_latency_ms=selection.estimated_latency_ms,
                                    rationale=f"Fallback for {selection.name}: {selection.rationale}",
                                    confidence=selection.confidence * 0.9,  # Slightly lower confidence
                                    alternatives=selection.alternatives,
                                    complexity_score=selection.complexity_score,
                                )
                            else:
                                error = f"Model {selected_model} unavailable and no fallback found"
                                logger.error(error)
                        else:
                            error = f"Model {selected_model} unavailable and fallback disabled"
                            logger.error(error)

                    # Load model if available
                    if error is None:
                        model_loaded = self.manager.ensure_model_loaded(selected_model)
                        if not model_loaded:
                            error = f"Failed to load model {selected_model}"
                            logger.error(error)

                except Exception as e:
                    error = f"Model management error: {str(e)}"
                    logger.error(error, exc_info=True)

            # Calculate routing latency
            end_time = time.perf_counter()
            routing_latency_ms = (end_time - start_time) * 1000

            return RoutingDecision(
                query=query,
                classification=classification,
                selection=selection,
                model_loaded=model_loaded,
                fallback_used=fallback_used,
                routing_latency_ms=routing_latency_ms,
                error=error,
            )

        except Exception as e:
            end_time = time.perf_counter()
            routing_latency_ms = (end_time - start_time) * 1000
            error = f"Routing failed: {str(e)}"
            logger.error(error, exc_info=True)

            # Return error decision with minimal info
            return RoutingDecision(
                query=query,
                classification=self.classifier.classify(""),  # Empty fallback
                selection=ModelSelection(
                    name="unknown",
                    tier="unknown",
                    estimated_latency_ms=0,
                    rationale=f"Error: {error}",
                    confidence=0.0,
                    alternatives=[],
                    complexity_score=0,
                ),
                model_loaded=False,
                fallback_used=False,
                routing_latency_ms=routing_latency_ms,
                error=error,
            )

    def warm_up(self, models: list[str]) -> dict[str, bool]:
        """
        Pre-load models for faster first query.

        Args:
            models: List of model names to warm up

        Returns:
            Dictionary mapping model name to load success

        Example:
            >>> service = RoutingService()
            >>> results = service.warm_up(["llama3.2:3b", "llama3.2:8b"])
            >>> results["llama3.2:3b"]
            True
        """
        results = {}
        for model in models:
            try:
                success = self.manager.ensure_model_loaded(model)
                results[model] = success
                if success:
                    logger.info(f"Warmed up model: {model}")
                else:
                    logger.warning(f"Failed to warm up model: {model}")
            except Exception as e:
                logger.error(f"Error warming up model {model}: {e}")
                results[model] = False

        return results

    def get_status(self) -> dict[str, Any]:
        """
        Get current status of routing service.

        Returns:
            Status dictionary with loaded models, memory usage, etc.

        Example:
            >>> service = RoutingService()
            >>> service.route("What is RAG?")
            >>> status = service.get_status()
            >>> status["loaded_models"]
            ['llama3.2:3b']
            >>> status["memory_usage_gb"]
            2.0
        """
        return {
            "loaded_models": self.manager.get_loaded_models(),
            "available_models": [
                info.to_dict() for info in self.manager.get_available_models()
            ],
            "memory_usage_gb": self.manager.get_memory_usage_gb(),
            "enable_fallback": self.enable_fallback,
            "enable_auto_load": self.enable_auto_load,
        }
