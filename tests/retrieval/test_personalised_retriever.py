"""Tests for PersonalisedRetriever (v0.4.8)."""

import pytest
from unittest.mock import Mock, patch

from ragged.memory.personalisation import PersonalisationConfig
from ragged.memory.profile import ProfileManager, InterestProfile
from ragged.memory.topics import TopicExtractor
from ragged.retrieval.personalised_retriever import PersonalisedRetriever
from ragged.retrieval.retriever import RetrievedChunk


@pytest.fixture
def mock_profile_manager():
    """Create mock profile manager."""
    manager = Mock(spec=ProfileManager)
    profile = InterestProfile(persona="test_user")
    manager.get_profile.return_value = profile
    return manager


@pytest.fixture
def mock_topic_extractor():
    """Create mock topic extractor."""
    return Mock(spec=TopicExtractor)


@pytest.fixture
def mock_base_retriever():
    """Create mock base retriever."""
    retriever = Mock()
    retriever.retrieve.return_value = [
        RetrievedChunk(
            text="test",
            score=0.1,
            chunk_id=f"chunk{i}",
            document_id=f"doc{i}",
            document_path=f"/docs/doc{i}.txt",
            chunk_position=0,
            metadata={},
        )
        for i in range(10)
    ]
    return retriever


@pytest.fixture
def personalised_retriever(mock_profile_manager, mock_topic_extractor, mock_base_retriever):
    """Create personalised retriever."""
    return PersonalisedRetriever(
        profile_manager=mock_profile_manager,
        topic_extractor=mock_topic_extractor,
        base_retriever=mock_base_retriever,
    )


class TestPersonalisedRetriever:
    """Tests for PersonalisedRetriever."""

    def test_initialization(self, personalised_retriever):
        """Test retriever initialisation."""
        assert personalised_retriever is not None
        assert personalised_retriever.base_retriever is not None
        assert personalised_retriever.ranker is not None

    def test_retrieve_without_personalisation(
        self, personalised_retriever, mock_base_retriever
    ):
        """Test retrieval without personalisation."""
        results = personalised_retriever.retrieve(
            query="test query",
            k=5,
            personalise=False,
        )

        # Should call base retriever with k (not k*multiplier)
        mock_base_retriever.retrieve.assert_called_once()
        call_args = mock_base_retriever.retrieve.call_args
        assert call_args[1]["k"] == 5

        assert len(results) == 5

    def test_retrieve_with_personalisation(
        self, personalised_retriever, mock_base_retriever
    ):
        """Test retrieval with personalisation."""
        results = personalised_retriever.retrieve(
            query="test query",
            k=5,
            persona="test_user",
            personalise=True,
        )

        # Should call base retriever with k*multiplier
        mock_base_retriever.retrieve.assert_called_once()
        call_args = mock_base_retriever.retrieve.call_args
        assert call_args[1]["k"] == 10  # k=5 * multiplier=2

        assert len(results) == 5

    def test_retrieve_disabled_in_config(
        self, personalised_retriever, mock_base_retriever
    ):
        """Test retrieval when personalisation disabled in config."""
        personalised_retriever.config.enabled = False

        results = personalised_retriever.retrieve(
            query="test query",
            k=5,
            personalise=True,  # Request personalisation
        )

        # Should still retrieve k (not k*multiplier) when disabled
        call_args = mock_base_retriever.retrieve.call_args
        assert call_args[1]["k"] == 5

    def test_retrieve_empty_results(
        self, personalised_retriever, mock_base_retriever
    ):
        """Test retrieval with no results."""
        mock_base_retriever.retrieve.return_value = []

        results = personalised_retriever.retrieve(
            query="test query",
            k=5,
            personalise=True,
        )

        assert results == []

    def test_record_interaction(self, personalised_retriever):
        """Test recording interaction."""
        chunks = [
            RetrievedChunk(
                text="test",
                score=0.1,
                chunk_id="chunk1",
                document_id="doc1",
                document_path="/docs/doc1.txt",
                chunk_position=0,
                metadata={},
            )
        ]

        personalised_retriever.record_interaction(
            query="test query",
            retrieved_docs=chunks,
            persona="test_user",
        )

        # Should record access in ranker
        assert "doc1" in personalised_retriever.ranker._access_history

    def test_get_config(self, personalised_retriever):
        """Test getting configuration."""
        config = personalised_retriever.get_config()
        assert isinstance(config, PersonalisationConfig)

    def test_update_config(self, personalised_retriever):
        """Test updating configuration."""
        personalised_retriever.update_config(alpha=0.5, retrieve_multiplier=3)

        assert personalised_retriever.config.alpha == 0.5
        assert personalised_retriever.config.retrieve_multiplier == 3

    def test_update_config_invalid_parameter(self, personalised_retriever):
        """Test updating with invalid parameter."""
        with pytest.raises(ValueError, match="Invalid configuration parameter"):
            personalised_retriever.update_config(invalid_param=123)

    def test_enable_personalisation(self, personalised_retriever):
        """Test enabling personalisation."""
        personalised_retriever.config.enabled = False
        personalised_retriever.enable_personalisation()
        assert personalised_retriever.config.enabled is True

    def test_disable_personalisation(self, personalised_retriever):
        """Test disabling personalisation."""
        personalised_retriever.config.enabled = True
        personalised_retriever.disable_personalisation()
        assert personalised_retriever.config.enabled is False

    def test_retrieve_with_filters(
        self, personalised_retriever, mock_base_retriever
    ):
        """Test retrieval with metadata filters."""
        personalised_retriever.retrieve(
            query="test query",
            k=5,
            filter_metadata={"category": "tech"},
            min_score=0.5,
        )

        # Should pass filters to base retriever
        call_args = mock_base_retriever.retrieve.call_args
        assert call_args[1]["filter_metadata"] == {"category": "tech"}
        assert call_args[1]["min_score"] == 0.5


class TestPersonalisedRetrieverIntegration:
    """Integration tests for PersonalisedRetriever."""

    def test_full_retrieval_workflow(self, mock_profile_manager, mock_topic_extractor):
        """Test complete retrieval workflow."""
        # Use real Retriever (mocked vector store)
        with patch("ragged.retrieval.personalised_retriever.Retriever") as MockRetriever:
            mock_retriever = Mock()
            mock_retriever.retrieve.return_value = [
                RetrievedChunk(
                    text=f"Document {i}",
                    score=i * 0.1,
                    chunk_id=f"chunk{i}",
                    document_id=f"doc{i}",
                    document_path=f"/docs/doc{i}.txt",
                    chunk_position=0,
                    metadata={},
                )
                for i in range(10)
            ]
            MockRetriever.return_value = mock_retriever

            retriever = PersonalisedRetriever(
                profile_manager=mock_profile_manager,
                topic_extractor=mock_topic_extractor,
            )

            # Retrieve
            results = retriever.retrieve(
                query="machine learning",
                k=5,
                persona="test_user",
                personalise=True,
            )

            assert len(results) == 5

            # Record interaction
            retriever.record_interaction(
                query="machine learning",
                retrieved_docs=results,
                persona="test_user",
            )

            # Retrieve again (should use history)
            results2 = retriever.retrieve(
                query="machine learning",
                k=5,
                persona="test_user",
                personalise=True,
            )

            assert len(results2) == 5
