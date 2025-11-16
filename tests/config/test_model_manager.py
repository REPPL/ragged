"""Tests for model manager."""

import pytest
from unittest.mock import Mock, MagicMock, patch
from src.config.model_manager import ModelManager, ModelInfo


@pytest.fixture
def mock_ollama_client():
    """Create a mock Ollama client."""
    with patch('src.config.model_manager.ollama.Client') as MockClient:
        mock_client = MagicMock()
        MockClient.return_value = mock_client
        yield mock_client


@pytest.fixture
def sample_models():
    """Create sample model data."""
    return [
        MagicMock(
            model="llama3.1:latest",
            size=5000000000,  # 5GB
            modified_at="2024-01-01"
        ),
        MagicMock(
            model="mistral:7b-instruct",
            size=4000000000,  # 4GB
            modified_at="2024-01-02"
        ),
        MagicMock(
            model="qwen2.5:3b",
            size=2000000000,  # 2GB
            modified_at="2024-01-03"
        ),
    ]


class TestModelManagerInit:
    """Tests for ModelManager initialization."""

    def test_default_initialization(self, mock_ollama_client):
        """Test manager with default Ollama URL."""
        manager = ModelManager()
        assert manager.client is not None

    def test_custom_ollama_url(self, mock_ollama_client):
        """Test manager with custom Ollama URL."""
        custom_url = "http://custom:11434"
        manager = ModelManager(ollama_url=custom_url)

        assert manager.client is not None


class TestListAvailableModels:
    """Tests for listing available models."""

    @pytest.mark.requires_ollama
    def test_list_models_success(self, mock_ollama_client, sample_models):
        """Test successful model listing."""
        # Mock the response
        mock_response = MagicMock()
        mock_response.models = sample_models
        mock_ollama_client.list.return_value = mock_response

        manager = ModelManager()
        models = manager.list_available_models()

        assert len(models) == 3
        assert all(isinstance(m, ModelInfo) for m in models)
        # Should be sorted by suitability (descending)
        assert models[0].suitability_score >= models[1].suitability_score

    @pytest.mark.requires_ollama
    def test_list_models_empty(self, mock_ollama_client):
        """Test listing when no models are available."""
        mock_response = MagicMock()
        mock_response.models = []
        mock_ollama_client.list.return_value = mock_response

        manager = ModelManager()
        models = manager.list_available_models()

        assert models == []

    @pytest.mark.requires_ollama
    def test_list_models_error_handling(self, mock_ollama_client):
        """Test handling of Ollama connection errors."""
        mock_ollama_client.list.side_effect = Exception("Connection failed")

        manager = ModelManager()
        models = manager.list_available_models()

        # Should return empty list on error
        assert models == []

    @pytest.mark.requires_ollama
    def test_list_models_sorted_by_suitability(self, mock_ollama_client):
        """Test that models are sorted by suitability score."""
        # Create models with known suitability scores
        models_data = [
            MagicMock(model="qwen2.5:3b", size=2000000000, modified_at="2024-01-01"),  # Low score (3b)
            MagicMock(model="llama3.1:latest", size=5000000000, modified_at="2024-01-02"),  # High score (llama3 + large context)
            MagicMock(model="mistral:7b", size=4000000000, modified_at="2024-01-03"),  # Medium score
        ]

        mock_response = MagicMock()
        mock_response.models = models_data
        mock_ollama_client.list.return_value = mock_response

        manager = ModelManager()
        models = manager.list_available_models()

        # Verify sorting
        for i in range(len(models) - 1):
            assert models[i].suitability_score >= models[i + 1].suitability_score


class TestGetRecommendedModel:
    """Tests for getting recommended model."""

    @pytest.mark.requires_ollama
    def test_get_recommended_model_success(self, mock_ollama_client, sample_models):
        """Test getting recommended model when models are available."""
        mock_response = MagicMock()
        mock_response.models = sample_models
        mock_ollama_client.list.return_value = mock_response

        manager = ModelManager()
        recommended = manager.get_recommended_model()

        assert recommended is not None
        assert isinstance(recommended, str)

    @pytest.mark.requires_ollama
    def test_get_recommended_model_no_models(self, mock_ollama_client):
        """Test getting recommended model when no models are available."""
        mock_response = MagicMock()
        mock_response.models = []
        mock_ollama_client.list.return_value = mock_response

        manager = ModelManager()
        recommended = manager.get_recommended_model()

        assert recommended is None

    @pytest.mark.requires_ollama
    def test_get_recommended_model_error(self, mock_ollama_client):
        """Test recommended model when listing fails."""
        mock_ollama_client.list.side_effect = Exception("Connection error")

        manager = ModelManager()
        recommended = manager.get_recommended_model()

        assert recommended is None


class TestVerifyModel:
    """Tests for model verification."""

    @pytest.mark.requires_ollama
    def test_verify_existing_model(self, mock_ollama_client, sample_models):
        """Test verifying a model that exists."""
        mock_response = MagicMock()
        mock_response.models = sample_models
        mock_ollama_client.list.return_value = mock_response

        manager = ModelManager()
        exists = manager.verify_model("llama3.1:latest")

        assert exists is True

    @pytest.mark.requires_ollama
    def test_verify_nonexistent_model(self, mock_ollama_client, sample_models):
        """Test verifying a model that doesn't exist."""
        mock_response = MagicMock()
        mock_response.models = sample_models
        mock_ollama_client.list.return_value = mock_response

        manager = ModelManager()
        exists = manager.verify_model("nonexistent:latest")

        assert exists is False

    @pytest.mark.requires_ollama
    def test_verify_model_empty_list(self, mock_ollama_client):
        """Test verifying model when no models are available."""
        mock_response = MagicMock()
        mock_response.models = []
        mock_ollama_client.list.return_value = mock_response

        manager = ModelManager()
        exists = manager.verify_model("any:model")

        assert exists is False


class TestContextLengthEstimation:
    """Tests for context length estimation."""

    def test_estimate_llama31_context(self, mock_ollama_client):
        """Test context estimation for llama3.1."""
        manager = ModelManager()
        context = manager._estimate_context_length("llama3.1:latest")

        assert context == 128000

    def test_estimate_llama32_context(self, mock_ollama_client):
        """Test context estimation for llama3.2."""
        manager = ModelManager()
        context = manager._estimate_context_length("llama3.2:3b")

        assert context == 8192

    def test_estimate_llama33_context(self, mock_ollama_client):
        """Test context estimation for llama3.3."""
        manager = ModelManager()
        context = manager._estimate_context_length("llama3.3:70b")

        assert context == 128000

    def test_estimate_qwen_context(self, mock_ollama_client):
        """Test context estimation for qwen models."""
        manager = ModelManager()
        context = manager._estimate_context_length("qwen2.5:7b")

        assert context == 32768

    def test_estimate_mistral_context(self, mock_ollama_client):
        """Test context estimation for mistral."""
        manager = ModelManager()
        context = manager._estimate_context_length("mistral:7b-instruct")

        assert context == 8192

    def test_estimate_mixtral_context(self, mock_ollama_client):
        """Test context estimation for mixtral."""
        manager = ModelManager()
        context = manager._estimate_context_length("mixtral:8x7b")

        assert context == 32768

    def test_estimate_unknown_model_context(self, mock_ollama_client):
        """Test context estimation for unknown model."""
        manager = ModelManager()
        context = manager._estimate_context_length("unknown:model")

        assert context == 4096  # Conservative default

    def test_estimate_case_insensitive(self, mock_ollama_client):
        """Test that context estimation is case-insensitive."""
        manager = ModelManager()
        context1 = manager._estimate_context_length("LLAMA3.1:latest")
        context2 = manager._estimate_context_length("llama3.1:latest")

        assert context1 == context2 == 128000


class TestModelFamilyDetection:
    """Tests for model family detection."""

    def test_detect_llama_family(self, mock_ollama_client):
        """Test detection of llama family."""
        manager = ModelManager()
        family = manager._get_model_family("llama3.1:latest")

        assert family == "llama"

    def test_detect_mistral_family(self, mock_ollama_client):
        """Test detection of mistral family."""
        manager = ModelManager()
        family = manager._get_model_family("mistral:7b-instruct")

        assert family == "mistral"

    def test_detect_mixtral_family(self, mock_ollama_client):
        """Test detection of mixtral family."""
        manager = ModelManager()
        family = manager._get_model_family("mixtral:8x7b")

        assert family == "mistral"

    def test_detect_qwen_family(self, mock_ollama_client):
        """Test detection of qwen family."""
        manager = ModelManager()
        family = manager._get_model_family("qwen2.5:7b")

        assert family == "qwen"

    def test_detect_phi_family(self, mock_ollama_client):
        """Test detection of phi family."""
        manager = ModelManager()
        family = manager._get_model_family("phi3:medium")

        assert family == "phi"

    def test_detect_gemma_family(self, mock_ollama_client):
        """Test detection of gemma family."""
        manager = ModelManager()
        family = manager._get_model_family("gemma:7b")

        assert family == "gemma"

    def test_detect_unknown_family(self, mock_ollama_client):
        """Test detection of unknown family."""
        manager = ModelManager()
        family = manager._get_model_family("unknown:model")

        assert family == "unknown"

    def test_family_detection_case_insensitive(self, mock_ollama_client):
        """Test that family detection is case-insensitive."""
        manager = ModelManager()
        family1 = manager._get_model_family("LLAMA3.1:latest")
        family2 = manager._get_model_family("llama3.1:latest")

        assert family1 == family2 == "llama"


class TestRAGSuitabilityScoring:
    """Tests for RAG suitability scoring."""

    def test_score_llama31_high(self, mock_ollama_client):
        """Test that llama3.1 gets high score (large context + llama3 bonus)."""
        manager = ModelManager()
        score = manager._calculate_rag_suitability("llama3.1:latest")

        # llama3.1 has 128k context (30 points) + llama3 (15 points) + latest (5 points) = 50 + 50 = 100
        assert score >= 90

    def test_score_large_context_bonus(self, mock_ollama_client):
        """Test that large context models get bonus points."""
        manager = ModelManager()

        # Mock to ensure we're testing context bonus
        with patch.object(manager, '_estimate_context_length') as mock_context:
            mock_context.return_value = 128000
            score = manager._calculate_rag_suitability("test:model")

            assert score >= 80  # Base 50 + 30 for large context

    def test_score_small_model_penalty(self, mock_ollama_client):
        """Test that small models get penalized."""
        manager = ModelManager()
        score = manager._calculate_rag_suitability("qwen2.5:3b")

        # Should have penalty for 3b size
        assert score < 70

    def test_score_instruct_bonus(self, mock_ollama_client):
        """Test that instruct-tuned models get bonus."""
        manager = ModelManager()
        score_instruct = manager._calculate_rag_suitability("mistral:7b-instruct")
        score_base = manager._calculate_rag_suitability("mistral:7b")

        # Instruct variant should score higher
        assert score_instruct > score_base

    def test_score_latest_bonus(self, mock_ollama_client):
        """Test that latest tag gets bonus."""
        manager = ModelManager()
        score_latest = manager._calculate_rag_suitability("llama3.1:latest")
        score_specific = manager._calculate_rag_suitability("llama3.1:8b")

        # Latest should get +5 bonus
        assert score_latest >= score_specific

    def test_score_range_valid(self, mock_ollama_client):
        """Test that all scores are in valid range (1-100)."""
        manager = ModelManager()

        test_models = [
            "llama3.1:latest",
            "llama3.2:3b",
            "mistral:7b-instruct",
            "qwen2.5:1b",
            "phi3:mini",
            "gemma:2b",
            "unknown:model",
        ]

        for model in test_models:
            score = manager._calculate_rag_suitability(model)
            assert 1 <= score <= 100, f"Score for {model} out of range: {score}"

    def test_score_7b_penalty(self, mock_ollama_client):
        """Test that 7b models get minor penalty."""
        manager = ModelManager()
        score = manager._calculate_rag_suitability("mistral:7b")

        # 7b should have -5 penalty but still reasonable score
        assert 40 <= score <= 75

    def test_score_consistency(self, mock_ollama_client):
        """Test that same model gets same score."""
        manager = ModelManager()

        score1 = manager._calculate_rag_suitability("llama3.1:latest")
        score2 = manager._calculate_rag_suitability("llama3.1:latest")

        assert score1 == score2


class TestModelInfo:
    """Tests for ModelInfo dataclass."""

    def test_model_info_creation(self):
        """Test creating ModelInfo instance."""
        info = ModelInfo(
            name="llama3.1:latest",
            size=5000000000,
            context_length=128000,
            family="llama",
            modified_at="2024-01-01",
            suitability_score=95
        )

        assert info.name == "llama3.1:latest"
        assert info.size == 5000000000
        assert info.context_length == 128000
        assert info.family == "llama"
        assert info.modified_at == "2024-01-01"
        assert info.suitability_score == 95

    def test_model_info_fields(self):
        """Test that ModelInfo has all required fields."""
        info = ModelInfo(
            name="test",
            size=100,
            context_length=4096,
            family="test",
            modified_at="2024",
            suitability_score=50
        )

        assert hasattr(info, 'name')
        assert hasattr(info, 'size')
        assert hasattr(info, 'context_length')
        assert hasattr(info, 'family')
        assert hasattr(info, 'modified_at')
        assert hasattr(info, 'suitability_score')


@pytest.mark.requires_ollama
class TestIntegrationScenarios:
    """Integration tests for common scenarios."""

    def test_select_best_model_from_multiple(self, mock_ollama_client):
        """Test selecting best model from multiple options."""
        # Create models with varying suitability
        models_data = [
            MagicMock(model="qwen2.5:3b", size=2000000000, modified_at="2024-01-01"),
            MagicMock(model="llama3.1:latest", size=5000000000, modified_at="2024-01-02"),
            MagicMock(model="mistral:7b-instruct", size=4000000000, modified_at="2024-01-03"),
            MagicMock(model="phi3:mini", size=1000000000, modified_at="2024-01-04"),
        ]

        mock_response = MagicMock()
        mock_response.models = models_data
        mock_ollama_client.list.return_value = mock_response

        manager = ModelManager()
        recommended = manager.get_recommended_model()

        # llama3.1:latest should be recommended (large context + llama3 bonus + latest)
        assert "llama3.1" in recommended

    def test_graceful_degradation_on_error(self, mock_ollama_client):
        """Test that manager gracefully handles Ollama being unavailable."""
        mock_ollama_client.list.side_effect = Exception("Service unavailable")

        manager = ModelManager()

        # All operations should return safe defaults
        assert manager.list_available_models() == []
        assert manager.get_recommended_model() is None
        assert manager.verify_model("any:model") is False
