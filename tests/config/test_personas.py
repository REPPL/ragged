"""Tests for configuration personas system."""

import pytest

from src.config.config_manager import RaggedConfig
from src.config.personas import PersonaConfig, PersonaManager


class TestPersonaConfig:
    """Test PersonaConfig dataclass."""

    def test_persona_config_creation(self):
        """Test creating a PersonaConfig."""
        persona = PersonaConfig(
            name="test",
            description="Test persona",
            retrieval_method="hybrid",
            top_k=5,
            enable_reranking=True,
            rerank_to=3,
            enable_query_decomposition=False,
            enable_hyde=False,
            enable_compression=False,
            confidence_threshold=0.85,
        )

        assert persona.name == "test"
        assert persona.description == "Test persona"
        assert persona.retrieval_method == "hybrid"
        assert persona.top_k == 5
        assert persona.enable_reranking is True
        assert persona.rerank_to == 3
        assert persona.confidence_threshold == 0.85


class TestPersonaManager:
    """Test PersonaManager class."""

    def test_all_personas_exist(self):
        """Test that all expected personas are defined."""
        expected_personas = ["accuracy", "speed", "balanced", "research", "quick-answer"]

        for persona_name in expected_personas:
            assert (
                persona_name in PersonaManager.PERSONAS
            ), f"Persona {persona_name} should exist"

    def test_get_accuracy_persona(self):
        """Test getting accuracy persona."""
        persona = PersonaManager.get_persona("accuracy")

        assert persona.name == "accuracy"
        assert persona.description == "Maximum quality, slower responses"
        assert persona.retrieval_method == "hybrid"
        assert persona.top_k == 10
        assert persona.enable_reranking is True
        assert persona.rerank_to == 3
        assert persona.enable_query_decomposition is True
        assert persona.enable_hyde is False
        assert persona.enable_compression is True
        assert persona.confidence_threshold == 0.95

    def test_get_speed_persona(self):
        """Test getting speed persona."""
        persona = PersonaManager.get_persona("speed")

        assert persona.name == "speed"
        assert persona.description == "Fast answers, good quality"
        assert persona.retrieval_method == "vector"
        assert persona.top_k == 3
        assert persona.enable_reranking is False
        assert persona.rerank_to == 0
        assert persona.enable_query_decomposition is False
        assert persona.enable_hyde is False
        assert persona.enable_compression is False
        assert persona.confidence_threshold == 0.80

    def test_get_balanced_persona(self):
        """Test getting balanced persona (default)."""
        persona = PersonaManager.get_persona("balanced")

        assert persona.name == "balanced"
        assert persona.description == "Default - balanced quality and speed"
        assert persona.retrieval_method == "hybrid"
        assert persona.top_k == 5
        assert persona.enable_reranking is True
        assert persona.rerank_to == 5
        assert persona.enable_query_decomposition is False
        assert persona.enable_hyde is False
        assert persona.enable_compression is False
        assert persona.confidence_threshold == 0.85

    def test_get_research_persona(self):
        """Test getting research persona."""
        persona = PersonaManager.get_persona("research")

        assert persona.name == "research"
        assert persona.description == "Deep exploration, comprehensive results"
        assert persona.retrieval_method == "hybrid"
        assert persona.top_k == 30
        assert persona.enable_reranking is True
        assert persona.rerank_to == 10
        assert persona.enable_query_decomposition is True
        assert persona.enable_hyde is True
        assert persona.enable_compression is False
        assert persona.confidence_threshold == 0.90

    def test_get_quick_answer_persona(self):
        """Test getting quick-answer persona."""
        persona = PersonaManager.get_persona("quick-answer")

        assert persona.name == "quick-answer"
        assert persona.description == "Single best answer, fastest"
        assert persona.retrieval_method == "hybrid"
        assert persona.top_k == 1
        assert persona.enable_reranking is False
        assert persona.rerank_to == 0
        assert persona.enable_query_decomposition is False
        assert persona.enable_hyde is False
        assert persona.enable_compression is False
        assert persona.confidence_threshold == 0.75

    def test_get_unknown_persona_raises_error(self):
        """Test that getting unknown persona raises ValueError."""
        with pytest.raises(ValueError, match="Unknown persona"):
            PersonaManager.get_persona("nonexistent")

    def test_list_personas(self):
        """Test listing all personas."""
        personas = PersonaManager.list_personas()

        assert isinstance(personas, dict)
        assert len(personas) == 5

        # Check that all expected personas are present
        assert "accuracy" in personas
        assert "speed" in personas
        assert "balanced" in personas
        assert "research" in personas
        assert "quick-answer" in personas

        # Check descriptions
        assert personas["accuracy"] == "Maximum quality, slower responses"
        assert personas["speed"] == "Fast answers, good quality"
        assert personas["balanced"] == "Default - balanced quality and speed"
        assert personas["research"] == "Deep exploration, comprehensive results"
        assert personas["quick-answer"] == "Single best answer, fastest"

    def test_apply_persona_to_config(self):
        """Test applying persona settings to a config."""
        config = RaggedConfig()

        # Initial state (balanced default)
        assert config.persona == "balanced"
        assert config.top_k == 5

        # Apply speed persona
        PersonaManager.apply_persona(config, "speed")

        assert config.persona == "speed"
        assert config.retrieval_method == "vector"
        assert config.top_k == 3
        assert config.enable_reranking is False
        assert config.confidence_threshold == 0.80

    def test_apply_accuracy_persona_changes_all_settings(self):
        """Test that applying accuracy persona changes all relevant settings."""
        config = RaggedConfig()

        # Set to different values first
        config.retrieval_method = "vector"
        config.top_k = 3
        config.enable_reranking = False
        config.enable_query_decomposition = False
        config.enable_hyde = False
        config.enable_compression = False

        # Apply accuracy persona
        PersonaManager.apply_persona(config, "accuracy")

        # Verify all settings changed
        assert config.persona == "accuracy"
        assert config.retrieval_method == "hybrid"
        assert config.top_k == 10
        assert config.enable_reranking is True
        assert config.rerank_to == 3
        assert config.enable_query_decomposition is True
        assert config.enable_hyde is False
        assert config.enable_compression is True
        assert config.confidence_threshold == 0.95

    def test_apply_multiple_personas_sequentially(self):
        """Test applying multiple personas in sequence."""
        config = RaggedConfig()

        # Apply speed
        PersonaManager.apply_persona(config, "speed")
        assert config.persona == "speed"
        assert config.top_k == 3

        # Apply accuracy
        PersonaManager.apply_persona(config, "accuracy")
        assert config.persona == "accuracy"
        assert config.top_k == 10

        # Apply quick-answer
        PersonaManager.apply_persona(config, "quick-answer")
        assert config.persona == "quick-answer"
        assert config.top_k == 1

    def test_apply_unknown_persona_raises_error(self):
        """Test that applying unknown persona raises ValueError."""
        config = RaggedConfig()

        with pytest.raises(ValueError, match="Unknown persona"):
            PersonaManager.apply_persona(config, "nonexistent")

        # Config should remain unchanged
        assert config.persona == "balanced"

    def test_persona_consistency(self):
        """Test that persona settings are internally consistent."""
        for persona_name in PersonaManager.PERSONAS.keys():
            persona = PersonaManager.get_persona(persona_name)

            # Rerank_to should never exceed top_k
            if persona.enable_reranking:
                assert (
                    persona.rerank_to <= persona.top_k
                ), f"{persona_name}: rerank_to should not exceed top_k"

            # Confidence threshold should be reasonable
            assert (
                0 <= persona.confidence_threshold <= 1.0
            ), f"{persona_name}: confidence_threshold should be 0-1"

            # Top-K should be positive
            assert persona.top_k > 0, f"{persona_name}: top_k should be positive"

    def test_persona_speed_vs_accuracy_tradeoffs(self):
        """Test that personas make sensible speed/accuracy tradeoffs."""
        speed = PersonaManager.get_persona("speed")
        accuracy = PersonaManager.get_persona("accuracy")
        research = PersonaManager.get_persona("research")
        quick_answer = PersonaManager.get_persona("quick-answer")

        # Speed should retrieve fewer documents than accuracy
        assert speed.top_k < accuracy.top_k

        # Research should retrieve most documents
        assert research.top_k > accuracy.top_k
        assert research.top_k > speed.top_k

        # Quick answer should retrieve fewest
        assert quick_answer.top_k <= speed.top_k

        # Speed should have fewer advanced features
        assert not speed.enable_reranking
        assert not speed.enable_query_decomposition

        # Accuracy should have more advanced features
        assert accuracy.enable_reranking
        assert accuracy.enable_query_decomposition

        # Research should have most advanced features
        assert research.enable_reranking
        assert research.enable_query_decomposition
        assert research.enable_hyde

    def test_persona_confidence_thresholds(self):
        """Test that personas have appropriate confidence thresholds."""
        quick_answer = PersonaManager.get_persona("quick-answer")
        speed = PersonaManager.get_persona("speed")
        balanced = PersonaManager.get_persona("balanced")
        research = PersonaManager.get_persona("research")
        accuracy = PersonaManager.get_persona("accuracy")

        # Accuracy should have highest threshold
        assert accuracy.confidence_threshold >= research.confidence_threshold
        assert accuracy.confidence_threshold >= balanced.confidence_threshold

        # Quick answer should have lowest (accepts lower quality for speed)
        assert quick_answer.confidence_threshold <= speed.confidence_threshold
        assert quick_answer.confidence_threshold <= balanced.confidence_threshold

    def test_persona_retrieval_methods(self):
        """Test that personas use appropriate retrieval methods."""
        speed = PersonaManager.get_persona("speed")
        accuracy = PersonaManager.get_persona("accuracy")
        balanced = PersonaManager.get_persona("balanced")

        # Speed optimizes with vector-only for performance
        assert speed.retrieval_method == "vector"

        # Accuracy and balanced use hybrid for better quality
        assert accuracy.retrieval_method == "hybrid"
        assert balanced.retrieval_method == "hybrid"
