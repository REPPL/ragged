"""
Model lifecycle management for automatic routing (v0.6.2 OPTIMISE-002 Phase 2).

Manages model availability, loading, and resource allocation for intelligent routing.

Responsibilities:
- Detect available models via Ollama API
- Handle model loading and unloading
- Manage GPU memory allocation
- Provide fallback logic when models unavailable
"""
from __future__ import annotations


import logging
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class ModelInfo:
    """
    Information about an available model.

    Tracks model availability and resource requirements.
    """

    name: str  # Model name (e.g. "llama3.2:3b")
    size_gb: float  # Approximate size in GB
    loaded: bool  # Currently loaded in memory
    available: bool  # Available in Ollama
    tier: str  # "fast", "balanced", "quality", "vision"

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialisation."""
        return {
            "name": self.name,
            "size_gb": self.size_gb,
            "loaded": self.loaded,
            "available": self.available,
            "tier": self.tier,
        }


class ModelManager:
    """
    Manage model lifecycle for automatic routing.

    Handles:
    - Model availability detection
    - Model loading/unloading
    - Resource management
    - Fallback strategies

    v0.6.2 OPTIMISE-002 Phase 2: Model management

    Example:
        >>> manager = ModelManager()
        >>> available = manager.get_available_models()
        >>> if manager.is_model_available("llama3.2:3b"):
        ...     manager.ensure_model_loaded("llama3.2:3b")
    """

    # Approximate model sizes (GB) - used for memory management
    MODEL_SIZES = {
        "llama3.2:3b": 2.0,
        "llama3.2:8b": 5.0,
        "llama3.2:70b": 40.0,
        "llava": 5.0,
        "mistral:latest": 4.0,
    }

    def __init__(
        self,
        ollama_available: bool = True,
        max_loaded_models: int = 3,
        auto_unload: bool = True,
    ) -> None:
        """
        Initialise model manager.

        Args:
            ollama_available: Whether Ollama service is available (for testing)
            max_loaded_models: Maximum models to keep loaded simultaneously
            auto_unload: Automatically unload models when reaching limit

        Example:
            >>> # Production
            >>> manager = ModelManager(ollama_available=True)
            >>> # Testing (mock mode)
            >>> manager = ModelManager(ollama_available=False)
        """
        self.ollama_available = ollama_available
        self.max_loaded_models = max_loaded_models
        self.auto_unload = auto_unload

        # Track loaded models
        self._loaded_models: list[str] = []

        # Track available models (populated by check_availability)
        self._available_models: dict[str, ModelInfo] = {}

        logger.debug(
            f"ModelManager initialised: "
            f"ollama_available={ollama_available}, "
            f"max_loaded={max_loaded_models}"
        )

    def check_availability(self, models: list[str]) -> dict[str, bool]:
        """
        Check which models are available in Ollama.

        In production, this would query the Ollama API.
        For v0.6.2, we simulate with a mock response.

        Args:
            models: List of model names to check

        Returns:
            Dictionary mapping model name to availability

        Example:
            >>> manager = ModelManager()
            >>> availability = manager.check_availability([
            ...     "llama3.2:3b",
            ...     "llama3.2:8b",
            ...     "unknown:model"
            ... ])
            >>> availability["llama3.2:3b"]
            True
            >>> availability["unknown:model"]
            False
        """
        availability = {}

        for model in models:
            # Simulate Ollama API check
            # In production: Use ollama.list() or similar
            if self.ollama_available and model in self.MODEL_SIZES:
                available = True
                self._available_models[model] = ModelInfo(
                    name=model,
                    size_gb=self.MODEL_SIZES.get(model, 5.0),
                    loaded=model in self._loaded_models,
                    available=True,
                    tier=self._get_model_tier(model),
                )
            else:
                available = False

            availability[model] = available
            logger.debug(f"Model {model} availability: {available}")

        return availability

    def is_model_available(self, model_name: str) -> bool:
        """
        Check if a specific model is available.

        Args:
            model_name: Model to check

        Returns:
            True if model is available

        Example:
            >>> manager = ModelManager()
            >>> manager.is_model_available("llama3.2:3b")
            True
        """
        if model_name in self._available_models:
            return self._available_models[model_name].available

        # Check on-demand if not cached
        availability = self.check_availability([model_name])
        return availability.get(model_name, False)

    def is_model_loaded(self, model_name: str) -> bool:
        """
        Check if a model is currently loaded in memory.

        Args:
            model_name: Model to check

        Returns:
            True if model is loaded

        Example:
            >>> manager = ModelManager()
            >>> manager.ensure_model_loaded("llama3.2:3b")
            >>> manager.is_model_loaded("llama3.2:3b")
            True
        """
        return model_name in self._loaded_models

    def ensure_model_loaded(self, model_name: str) -> bool:
        """
        Ensure a model is loaded in memory.

        Handles:
        - Loading if not already loaded
        - Auto-unloading if at capacity
        - Fallback if model unavailable

        Args:
            model_name: Model to load

        Returns:
            True if model successfully loaded or already loaded

        Raises:
            ValueError: If model not available and no fallback

        Example:
            >>> manager = ModelManager()
            >>> success = manager.ensure_model_loaded("llama3.2:8b")
            >>> assert success
            >>> assert manager.is_model_loaded("llama3.2:8b")
        """
        # Already loaded
        if model_name in self._loaded_models:
            logger.debug(f"Model {model_name} already loaded")
            return True

        # Check availability
        if not self.is_model_available(model_name):
            logger.error(f"Model {model_name} not available")
            raise ValueError(f"Model {model_name} not available in Ollama")

        # Check if we need to unload models
        if len(self._loaded_models) >= self.max_loaded_models:
            if self.auto_unload:
                # Unload least recently used model
                oldest_model = self._loaded_models[0]
                self.unload_model(oldest_model)
                logger.info(
                    f"Auto-unloaded {oldest_model} to make room for {model_name}"
                )
            else:
                logger.warning(
                    f"Cannot load {model_name}: max loaded models ({self.max_loaded_models}) reached"
                )
                return False

        # Simulate model loading
        # In production: Call Ollama API to load model
        self._loaded_models.append(model_name)

        # Update model info
        if model_name in self._available_models:
            self._available_models[model_name].loaded = True

        logger.info(f"Model {model_name} loaded successfully")
        return True

    def unload_model(self, model_name: str) -> bool:
        """
        Unload a model from memory.

        Args:
            model_name: Model to unload

        Returns:
            True if model successfully unloaded

        Example:
            >>> manager = ModelManager()
            >>> manager.ensure_model_loaded("llama3.2:3b")
            >>> manager.unload_model("llama3.2:3b")
            True
            >>> manager.is_model_loaded("llama3.2:3b")
            False
        """
        if model_name not in self._loaded_models:
            logger.debug(f"Model {model_name} not loaded, nothing to unload")
            return True

        # Simulate unloading
        # In production: Call Ollama API to unload model
        self._loaded_models.remove(model_name)

        # Update model info
        if model_name in self._available_models:
            self._available_models[model_name].loaded = False

        logger.info(f"Model {model_name} unloaded successfully")
        return True

    def get_available_models(self) -> list[ModelInfo]:
        """
        Get list of all available models.

        Returns:
            List of ModelInfo for available models

        Example:
            >>> manager = ModelManager()
            >>> manager.check_availability(["llama3.2:3b", "llama3.2:8b"])
            >>> models = manager.get_available_models()
            >>> len(models)
            2
        """
        return list(self._available_models.values())

    def get_loaded_models(self) -> list[str]:
        """
        Get list of currently loaded models.

        Returns:
            List of model names

        Example:
            >>> manager = ModelManager()
            >>> manager.ensure_model_loaded("llama3.2:3b")
            >>> manager.ensure_model_loaded("llama3.2:8b")
            >>> loaded = manager.get_loaded_models()
            >>> "llama3.2:3b" in loaded
            True
        """
        return self._loaded_models.copy()

    def get_fallback_model(self, unavailable_model: str, tier: str) -> str | None:
        """
        Get fallback model when preferred model unavailable.

        Fallback strategy:
        - Fast tier: 3b → 8b → 70b
        - Balanced tier: 8b → 3b → 70b
        - Quality tier: 70b → 8b → 3b
        - Vision tier: llava → 70b

        Args:
            unavailable_model: Model that is not available
            tier: Model tier ("fast", "balanced", "quality", "vision")

        Returns:
            Fallback model name, or None if no fallback available

        Example:
            >>> manager = ModelManager()
            >>> manager.check_availability(["llama3.2:8b"])
            >>> fallback = manager.get_fallback_model("llama3.2:3b", "fast")
            >>> fallback
            'llama3.2:8b'
        """
        # Define fallback chains per tier
        fallback_chains = {
            "fast": ["llama3.2:3b", "llama3.2:8b", "llama3.2:70b"],
            "balanced": ["llama3.2:8b", "llama3.2:3b", "llama3.2:70b"],
            "quality": ["llama3.2:70b", "llama3.2:8b", "llama3.2:3b"],
            "vision": ["llava", "llama3.2:70b", "llama3.2:8b"],
        }

        chain = fallback_chains.get(tier, ["llama3.2:8b"])

        # Try each model in fallback chain
        for candidate in chain:
            if candidate == unavailable_model:
                continue  # Skip the unavailable model

            if self.is_model_available(candidate):
                logger.info(
                    f"Using fallback model {candidate} for {unavailable_model}"
                )
                return candidate

        logger.error(f"No fallback available for {unavailable_model} (tier: {tier})")
        return None

    def _get_model_tier(self, model_name: str) -> str:
        """
        Determine model tier from name.

        Args:
            model_name: Model name

        Returns:
            Tier ("fast", "balanced", "quality", "vision")
        """
        # Check vision first (llava, vision models)
        if "llava" in model_name or "vision" in model_name:
            return "vision"
        # Then check size markers
        elif "3b" in model_name:
            return "fast"
        elif "8b" in model_name:
            return "balanced"
        elif "70b" in model_name or "90b" in model_name:
            return "quality"
        else:
            return "balanced"  # Default

    def get_memory_usage_gb(self) -> float:
        """
        Estimate current GPU memory usage.

        Returns:
            Estimated memory usage in GB

        Example:
            >>> manager = ModelManager()
            >>> manager.ensure_model_loaded("llama3.2:3b")
            >>> manager.ensure_model_loaded("llama3.2:8b")
            >>> memory = manager.get_memory_usage_gb()
            >>> memory >= 7.0  # 2GB + 5GB
            True
        """
        total_memory = 0.0
        for model in self._loaded_models:
            total_memory += self.MODEL_SIZES.get(model, 5.0)
        return total_memory
