"""
Tests for model lifecycle management (v0.6.2 OPTIMISE-002 Phase 2).

Success criteria:
- Model availability detection functional
- Model loading/unloading works correctly
- Fallback logic provides alternatives
- Memory management prevents overload
"""

import pytest

from ragged.optimisation import ModelInfo, ModelManager


class TestModelInfo:
    """Test ModelInfo dataclass."""

    def test_model_info_creation(self) -> None:
        """Test ModelInfo instantiation."""
        info = ModelInfo(
            name="llama3.2:3b",
            size_gb=2.0,
            loaded=True,
            available=True,
            tier="fast",
        )

        assert info.name == "llama3.2:3b"
        assert info.size_gb == 2.0
        assert info.loaded is True
        assert info.available is True
        assert info.tier == "fast"

    def test_model_info_to_dict(self) -> None:
        """Test ModelInfo serialisation."""
        info = ModelInfo(
            name="llama3.2:8b",
            size_gb=5.0,
            loaded=False,
            available=True,
            tier="balanced",
        )

        info_dict = info.to_dict()

        assert "name" in info_dict
        assert "size_gb" in info_dict
        assert "loaded" in info_dict
        assert "available" in info_dict
        assert "tier" in info_dict

        assert info_dict["name"] == "llama3.2:8b"
        assert info_dict["tier"] == "balanced"


class TestModelManagerInitialization:
    """Test ModelManager initialization."""

    def test_default_initialization(self) -> None:
        """Test ModelManager with default settings."""
        manager = ModelManager()

        assert manager.ollama_available is True
        assert manager.max_loaded_models == 3
        assert manager.auto_unload is True

    def test_custom_initialization(self) -> None:
        """Test ModelManager with custom settings."""
        manager = ModelManager(
            ollama_available=False, max_loaded_models=5, auto_unload=False
        )

        assert manager.ollama_available is False
        assert manager.max_loaded_models == 5
        assert manager.auto_unload is False


class TestModelAvailability:
    """Test model availability detection."""

    @pytest.fixture
    def manager(self) -> ModelManager:
        """Create manager instance with Ollama available."""
        return ModelManager(ollama_available=True)

    @pytest.fixture
    def manager_no_ollama(self) -> ModelManager:
        """Create manager instance without Ollama."""
        return ModelManager(ollama_available=False)

    def test_check_availability_known_models(self, manager: ModelManager) -> None:
        """Test availability check for known models."""
        models = ["llama3.2:3b", "llama3.2:8b", "llama3.2:70b"]
        availability = manager.check_availability(models)

        assert availability["llama3.2:3b"] is True
        assert availability["llama3.2:8b"] is True
        assert availability["llama3.2:70b"] is True

    def test_check_availability_unknown_model(self, manager: ModelManager) -> None:
        """Test availability check for unknown models."""
        availability = manager.check_availability(["unknown:model"])

        assert availability["unknown:model"] is False

    def test_check_availability_no_ollama(
        self, manager_no_ollama: ModelManager
    ) -> None:
        """Test availability check when Ollama unavailable."""
        availability = manager_no_ollama.check_availability(["llama3.2:3b"])

        assert availability["llama3.2:3b"] is False

    def test_is_model_available(self, manager: ModelManager) -> None:
        """Test is_model_available method."""
        manager.check_availability(["llama3.2:3b"])

        assert manager.is_model_available("llama3.2:3b") is True
        assert manager.is_model_available("unknown:model") is False

    def test_get_available_models(self, manager: ModelManager) -> None:
        """Test get_available_models returns ModelInfo list."""
        manager.check_availability(["llama3.2:3b", "llama3.2:8b"])

        available = manager.get_available_models()

        assert len(available) == 2
        assert all(isinstance(info, ModelInfo) for info in available)
        assert all(info.available for info in available)


class TestModelLoading:
    """Test model loading and unloading."""

    @pytest.fixture
    def manager(self) -> ModelManager:
        """Create manager instance."""
        return ModelManager(ollama_available=True)

    def test_ensure_model_loaded_success(self, manager: ModelManager) -> None:
        """Test successful model loading."""
        success = manager.ensure_model_loaded("llama3.2:3b")

        assert success is True
        assert manager.is_model_loaded("llama3.2:3b")

    def test_ensure_model_loaded_already_loaded(self, manager: ModelManager) -> None:
        """Test loading already-loaded model."""
        manager.ensure_model_loaded("llama3.2:3b")
        success = manager.ensure_model_loaded("llama3.2:3b")

        assert success is True
        assert manager.is_model_loaded("llama3.2:3b")

    def test_ensure_model_loaded_unavailable(self, manager: ModelManager) -> None:
        """Test loading unavailable model raises error."""
        with pytest.raises(ValueError, match="not available"):
            manager.ensure_model_loaded("unknown:model")

    def test_unload_model(self, manager: ModelManager) -> None:
        """Test model unloading."""
        manager.ensure_model_loaded("llama3.2:3b")
        assert manager.is_model_loaded("llama3.2:3b")

        success = manager.unload_model("llama3.2:3b")

        assert success is True
        assert not manager.is_model_loaded("llama3.2:3b")

    def test_unload_not_loaded_model(self, manager: ModelManager) -> None:
        """Test unloading model that isn't loaded."""
        success = manager.unload_model("llama3.2:3b")

        assert success is True  # No-op, but successful

    def test_get_loaded_models(self, manager: ModelManager) -> None:
        """Test get_loaded_models returns list."""
        manager.ensure_model_loaded("llama3.2:3b")
        manager.ensure_model_loaded("llama3.2:8b")

        loaded = manager.get_loaded_models()

        assert len(loaded) == 2
        assert "llama3.2:3b" in loaded
        assert "llama3.2:8b" in loaded


class TestAutoUnload:
    """Test automatic model unloading."""

    @pytest.fixture
    def manager(self) -> ModelManager:
        """Create manager with max 2 models."""
        return ModelManager(ollama_available=True, max_loaded_models=2, auto_unload=True)

    def test_auto_unload_when_at_capacity(self, manager: ModelManager) -> None:
        """Test auto-unload of oldest model when at capacity."""
        # Load 2 models (at capacity)
        manager.ensure_model_loaded("llama3.2:3b")
        manager.ensure_model_loaded("llama3.2:8b")

        assert len(manager.get_loaded_models()) == 2

        # Load 3rd model - should auto-unload oldest (3b)
        manager.ensure_model_loaded("llama3.2:70b")

        loaded = manager.get_loaded_models()
        assert len(loaded) == 2
        assert "llama3.2:3b" not in loaded  # Oldest unloaded
        assert "llama3.2:8b" in loaded
        assert "llama3.2:70b" in loaded

    def test_no_auto_unload_when_disabled(self) -> None:
        """Test no auto-unload when disabled."""
        manager = ModelManager(
            ollama_available=True, max_loaded_models=2, auto_unload=False
        )

        manager.ensure_model_loaded("llama3.2:3b")
        manager.ensure_model_loaded("llama3.2:8b")

        # Attempt to load 3rd model - should fail
        success = manager.ensure_model_loaded("llama3.2:70b")

        assert success is False
        assert len(manager.get_loaded_models()) == 2


class TestFallbackLogic:
    """Test fallback model selection."""

    @pytest.fixture
    def manager(self) -> ModelManager:
        """Create manager with some models unavailable."""
        manager = ModelManager(ollama_available=True)
        # Check availability for subset of models
        manager.check_availability(["llama3.2:8b", "llama3.2:70b"])
        return manager

    def test_fallback_fast_tier(self, manager: ModelManager) -> None:
        """Test fallback for fast tier (3b → 8b → 70b)."""
        fallback = manager.get_fallback_model("llama3.2:3b", "fast")

        assert fallback == "llama3.2:8b"  # First available in chain

    def test_fallback_balanced_tier(self, manager: ModelManager) -> None:
        """Test fallback for balanced tier (8b → 3b → 70b)."""
        fallback = manager.get_fallback_model("unavailable:model", "balanced")

        assert fallback == "llama3.2:8b"  # First available

    def test_fallback_quality_tier(self, manager: ModelManager) -> None:
        """Test fallback for quality tier (70b → 8b → 3b)."""
        fallback = manager.get_fallback_model("llama3.2:90b", "quality")

        assert fallback == "llama3.2:70b"  # First available in chain

    def test_fallback_vision_tier(self, manager: ModelManager) -> None:
        """Test fallback for vision tier (llava → 70b → 8b)."""
        fallback = manager.get_fallback_model("llava", "vision")

        assert fallback == "llama3.2:70b"  # Next in chain

    def test_fallback_no_models_available(self) -> None:
        """Test fallback when no models available."""
        manager = ModelManager(ollama_available=False)

        fallback = manager.get_fallback_model("llama3.2:3b", "fast")

        assert fallback is None


class TestMemoryManagement:
    """Test GPU memory estimation."""

    @pytest.fixture
    def manager(self) -> ModelManager:
        """Create manager instance."""
        return ModelManager(ollama_available=True)

    def test_memory_usage_empty(self, manager: ModelManager) -> None:
        """Test memory usage with no models loaded."""
        memory = manager.get_memory_usage_gb()

        assert memory == 0.0

    def test_memory_usage_single_model(self, manager: ModelManager) -> None:
        """Test memory usage with single model."""
        manager.ensure_model_loaded("llama3.2:3b")

        memory = manager.get_memory_usage_gb()

        assert memory == 2.0  # 3b model size

    def test_memory_usage_multiple_models(self, manager: ModelManager) -> None:
        """Test memory usage with multiple models."""
        manager.ensure_model_loaded("llama3.2:3b")  # 2 GB
        manager.ensure_model_loaded("llama3.2:8b")  # 5 GB

        memory = manager.get_memory_usage_gb()

        assert memory == 7.0  # 2 + 5

    def test_memory_usage_large_model(self, manager: ModelManager) -> None:
        """Test memory usage with large model."""
        manager.ensure_model_loaded("llama3.2:70b")  # 40 GB

        memory = manager.get_memory_usage_gb()

        assert memory == 40.0


class TestModelTierDetection:
    """Test model tier detection from name."""

    @pytest.fixture
    def manager(self) -> ModelManager:
        """Create manager instance."""
        return ModelManager()

    def test_tier_detection_fast(self, manager: ModelManager) -> None:
        """Test fast tier detection."""
        tier = manager._get_model_tier("llama3.2:3b")
        assert tier == "fast"

    def test_tier_detection_balanced(self, manager: ModelManager) -> None:
        """Test balanced tier detection."""
        tier = manager._get_model_tier("llama3.2:8b")
        assert tier == "balanced"

    def test_tier_detection_quality(self, manager: ModelManager) -> None:
        """Test quality tier detection."""
        tier = manager._get_model_tier("llama3.2:70b")
        assert tier == "quality"

        tier = manager._get_model_tier("llama3.2:90b")
        assert tier == "quality"

    def test_tier_detection_vision(self, manager: ModelManager) -> None:
        """Test vision tier detection."""
        tier = manager._get_model_tier("llava")
        assert tier == "vision"

        tier = manager._get_model_tier("llama3.2-vision:90b")
        assert tier == "vision"

    def test_tier_detection_unknown(self, manager: ModelManager) -> None:
        """Test unknown model defaults to balanced."""
        tier = manager._get_model_tier("unknown:model")
        assert tier == "balanced"
