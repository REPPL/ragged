"""Tests for topic extraction (v0.4.7)."""

import pytest
from datetime import datetime
from pathlib import Path

from ragged.memory.topics import Topic, TopicExtractor, DEFAULT_STOP_WORDS
from ragged.memory.topic_config import TopicExtractionConfig, create_default_config


class TestTopic:
    """Tests for Topic dataclass."""

    def test_topic_creation(self):
        """Test creating a topic with valid data."""
        topic = Topic(name="machine learning", confidence=0.8)

        assert topic.name == "machine learning"
        assert topic.confidence == 0.8
        assert topic.raw_text == "machine learning"  # Auto-filled
        assert isinstance(topic.extracted_at, datetime)

    def test_topic_with_raw_text(self):
        """Test creating topic with explicit raw_text."""
        topic = Topic(name="ml", confidence=0.9, raw_text="Machine Learning")

        assert topic.name == "ml"
        assert topic.raw_text == "Machine Learning"

    def test_topic_confidence_validation(self):
        """Test topic confidence must be 0.0-1.0."""
        # Valid confidences
        Topic(name="test", confidence=0.0)
        Topic(name="test", confidence=0.5)
        Topic(name="test", confidence=1.0)

        # Invalid confidences
        with pytest.raises(ValueError, match="Confidence must be 0.0-1.0"):
            Topic(name="test", confidence=-0.1)

        with pytest.raises(ValueError, match="Confidence must be 0.0-1.0"):
            Topic(name="test", confidence=1.1)

    def test_topic_name_validation(self):
        """Test topic name cannot be empty."""
        with pytest.raises(ValueError, match="Topic name cannot be empty"):
            Topic(name="", confidence=0.5)


class TestTopicExtractor:
    """Tests for TopicExtractor class."""

    def test_extractor_initialization(self):
        """Test extractor initializes with default params."""
        extractor = TopicExtractor()

        assert extractor.min_topic_length == 3
        assert extractor.max_topics_per_query == 10
        assert extractor.min_confidence == 0.3
        assert extractor.stop_words == DEFAULT_STOP_WORDS
        assert extractor.enable_phrases is True

    def test_extractor_custom_params(self):
        """Test extractor with custom parameters."""
        custom_stop_words = {"foo", "bar"}
        extractor = TopicExtractor(
            min_topic_length=5,
            max_topics_per_query=5,
            min_confidence=0.5,
            stop_words=custom_stop_words,
            enable_phrases=False,
        )

        assert extractor.min_topic_length == 5
        assert extractor.max_topics_per_query == 5
        assert extractor.min_confidence == 0.5
        assert extractor.stop_words == custom_stop_words
        assert extractor.enable_phrases is False

    def test_extract_capitalised_terms(self):
        """Test extraction of capitalised terms (acronyms)."""
        extractor = TopicExtractor()

        topics = extractor.extract_topics("What are the latest RAG techniques for LLM applications?")

        topic_names = [t.name for t in topics]
        assert "RAG" in topic_names
        assert "LLM" in topic_names

        # RAG and LLM should have high confidence (0.9+)
        rag_topic = next(t for t in topics if t.name == "RAG")
        assert rag_topic.confidence >= 0.9

    def test_extract_phrases(self):
        """Test extraction of multi-word phrases."""
        extractor = TopicExtractor(enable_phrases=True)

        topics = extractor.extract_topics("retrieval augmented generation techniques")

        topic_names = [t.name for t in topics]

        # Should extract 2-word and 3-word phrases
        assert "retrieval augmented" in topic_names or "augmented generation" in topic_names
        assert any("retrieval" in name for name in topic_names)

    def test_extract_keywords(self):
        """Test extraction of individual keywords."""
        extractor = TopicExtractor(enable_phrases=False)

        topics = extractor.extract_topics("machine learning algorithms")

        topic_names = [t.name for t in topics]

        # With phrases disabled, should extract individual keywords
        assert "machine" in topic_names
        assert "learning" in topic_names
        assert "algorithms" in topic_names

    def test_stop_words_filtering(self):
        """Test that stop words are filtered out."""
        extractor = TopicExtractor()

        topics = extractor.extract_topics("what is the best way to learn python")

        topic_names = [t.name for t in topics]

        # Stop words should be filtered
        assert "what" not in topic_names
        assert "the" not in topic_names
        assert "is" not in topic_names

        # "learn" is in DEFAULT_STOP_WORDS (as part of common verbs)
        # "python" should be extracted
        assert "python" in topic_names

    def test_confidence_threshold_filtering(self):
        """Test filtering by minimum confidence."""
        extractor = TopicExtractor(min_confidence=0.7)

        topics = extractor.extract_topics("RAG techniques for machine learning")

        # All topics should have confidence >= 0.7
        assert all(t.confidence >= 0.7 for t in topics)

        # RAG (capitalised) should be included (confidence ~0.9)
        assert any(t.name == "RAG" for t in topics)

    def test_max_topics_limit(self):
        """Test limiting number of extracted topics."""
        extractor = TopicExtractor(max_topics_per_query=3, min_confidence=0.3)

        query = "machine learning deep learning neural networks transformers attention mechanisms RAG LLM"
        topics = extractor.extract_topics(query)

        assert len(topics) <= 3

    def test_deduplication(self):
        """Test deduplication keeps highest confidence."""
        extractor = TopicExtractor()

        # "RAG" appears twice (once as acronym, once potentially as keyword)
        topics = extractor.extract_topics("RAG is great, I love rag techniques")

        # Should only have one "RAG" or "rag" topic
        rag_topics = [t for t in topics if t.name.lower() == "rag"]
        assert len(rag_topics) == 1

    def test_empty_query(self):
        """Test extraction from empty query."""
        extractor = TopicExtractor()

        topics = extractor.extract_topics("")
        assert topics == []

        topics = extractor.extract_topics("   ")
        assert topics == []

    def test_min_topic_length(self):
        """Test filtering by minimum topic length."""
        extractor = TopicExtractor(min_topic_length=5)

        topics = extractor.extract_topics("AI ML NLP machine learning")

        topic_names = [t.name for t in topics]

        # "AI", "ML", "NLP" are < 5 chars, should be filtered
        assert "AI" not in topic_names
        assert "ML" not in topic_names
        assert "NLP" not in topic_names

        # "machine" is >= 5 chars
        # Note: might be in phrases depending on extraction order

    def test_extract_from_documents(self):
        """Test extraction from document IDs."""
        extractor = TopicExtractor()

        doc_ids = [
            "RAG_paper_2023.pdf",
            "machine_learning_intro.md",
            "neural-networks-tutorial.docx",
        ]

        topics = extractor.extract_from_documents(doc_ids)

        topic_names = [t.name for t in topics]

        # Should extract topics from filenames
        assert "RAG" in topic_names or "rag" in topic_names
        assert any("machine" in name for name in topic_names)
        assert any("neural" in name or "networks" in name for name in topic_names)

        # Document-derived topics should have reduced confidence
        assert all(t.confidence < 1.0 for t in topics)

    def test_extract_from_empty_documents(self):
        """Test extraction from empty document list."""
        extractor = TopicExtractor()

        topics = extractor.extract_from_documents([])
        assert topics == []

    def test_sorting_by_confidence(self):
        """Test topics are sorted by confidence (highest first)."""
        extractor = TopicExtractor()

        topics = extractor.extract_topics("RAG techniques for machine learning optimization")

        # Topics should be sorted by confidence descending
        confidences = [t.confidence for t in topics]
        assert confidences == sorted(confidences, reverse=True)


class TestTopicExtractionConfig:
    """Tests for TopicExtractionConfig."""

    def test_default_config(self):
        """Test creating default configuration."""
        config = create_default_config()

        assert config.min_topic_length == 3
        assert config.max_topics_per_query == 10
        assert config.confidence_threshold == 0.3
        assert config.stop_words == DEFAULT_STOP_WORDS
        assert config.enable_phrases is True

    def test_config_validation(self):
        """Test configuration validation."""
        # Valid config
        TopicExtractionConfig(
            min_topic_length=1,
            max_topics_per_query=5,
            confidence_threshold=0.5,
        )

        # Invalid min_topic_length
        with pytest.raises(ValueError, match="min_topic_length must be >= 1"):
            TopicExtractionConfig(min_topic_length=0)

        # Invalid max_topics_per_query
        with pytest.raises(ValueError, match="max_topics_per_query must be >= 1"):
            TopicExtractionConfig(max_topics_per_query=0)

        # Invalid confidence_threshold
        with pytest.raises(ValueError, match="confidence_threshold must be 0.0-1.0"):
            TopicExtractionConfig(confidence_threshold=-0.1)

        with pytest.raises(ValueError, match="confidence_threshold must be 0.0-1.0"):
            TopicExtractionConfig(confidence_threshold=1.5)

    def test_from_dict(self):
        """Test loading config from dictionary."""
        config_dict = {
            "min_topic_length": 5,
            "max_topics_per_query": 20,
            "confidence_threshold": 0.5,
            "stop_words": ["foo", "bar", "baz"],
            "enable_phrases": False,
        }

        config = TopicExtractionConfig.from_dict(config_dict)

        assert config.min_topic_length == 5
        assert config.max_topics_per_query == 20
        assert config.confidence_threshold == 0.5
        assert config.stop_words == {"foo", "bar", "baz"}
        assert config.enable_phrases is False

    def test_from_dict_default_stop_words(self):
        """Test loading config with 'default' stop words."""
        config_dict = {
            "stop_words": "default",
        }

        config = TopicExtractionConfig.from_dict(config_dict)

        assert config.stop_words == DEFAULT_STOP_WORDS

    def test_to_dict(self):
        """Test converting config to dictionary."""
        config = TopicExtractionConfig(
            min_topic_length=5,
            max_topics_per_query=20,
            confidence_threshold=0.5,
            enable_phrases=False,
        )

        config_dict = config.to_dict()

        assert config_dict["min_topic_length"] == 5
        assert config_dict["max_topics_per_query"] == 20
        assert config_dict["confidence_threshold"] == 0.5
        assert config_dict["stop_words"] == "default"
        assert config_dict["enable_phrases"] is False

    def test_to_dict_custom_stop_words(self):
        """Test converting config with custom stop words to dict."""
        config = TopicExtractionConfig(stop_words={"foo", "bar"})

        config_dict = config.to_dict()

        assert set(config_dict["stop_words"]) == {"foo", "bar"}

    def test_yaml_roundtrip(self, tmp_path):
        """Test saving and loading config from YAML."""
        config = TopicExtractionConfig(
            min_topic_length=5,
            max_topics_per_query=15,
            confidence_threshold=0.6,
        )

        yaml_path = tmp_path / "config.yaml"
        config.to_yaml(yaml_path)

        loaded_config = TopicExtractionConfig.from_yaml(yaml_path)

        assert loaded_config.min_topic_length == 5
        assert loaded_config.max_topics_per_query == 15
        assert loaded_config.confidence_threshold == 0.6

    def test_from_yaml_missing_file(self, tmp_path):
        """Test loading from non-existent YAML file."""
        yaml_path = tmp_path / "missing.yaml"

        with pytest.raises(FileNotFoundError):
            TopicExtractionConfig.from_yaml(yaml_path)

    def test_load_custom_stop_words(self, tmp_path):
        """Test loading custom stop words from file."""
        config = TopicExtractionConfig()

        stop_words_file = tmp_path / "stop_words.txt"
        stop_words_file.write_text("foo\nbar\nbaz\n\n")

        config.load_custom_stop_words(stop_words_file)

        assert config.stop_words == {"foo", "bar", "baz"}

    def test_load_custom_stop_words_missing_file(self, tmp_path):
        """Test loading stop words from non-existent file."""
        config = TopicExtractionConfig()

        with pytest.raises(FileNotFoundError):
            config.load_custom_stop_words(tmp_path / "missing.txt")

    def test_add_stop_words(self):
        """Test adding stop words to configuration."""
        config = TopicExtractionConfig(stop_words=set())

        config.add_stop_words(["foo", "bar"])
        assert "foo" in config.stop_words
        assert "bar" in config.stop_words

        config.add_stop_words({"baz"})
        assert "baz" in config.stop_words

    def test_remove_stop_words(self):
        """Test removing stop words from configuration."""
        config = TopicExtractionConfig(stop_words={"foo", "bar", "baz"})

        config.remove_stop_words(["foo"])
        assert "foo" not in config.stop_words
        assert "bar" in config.stop_words

        config.remove_stop_words({"bar", "baz"})
        assert "bar" not in config.stop_words
        assert "baz" not in config.stop_words


class TestIntegration:
    """Integration tests for topic extraction with configuration."""

    def test_extractor_with_config(self):
        """Test using TopicExtractor with TopicExtractionConfig."""
        config = TopicExtractionConfig(
            min_topic_length=3,
            max_topics_per_query=5,
            confidence_threshold=0.5,
        )

        extractor = TopicExtractor(
            min_topic_length=config.min_topic_length,
            max_topics_per_query=config.max_topics_per_query,
            min_confidence=config.confidence_threshold,
            stop_words=config.stop_words,
            enable_phrases=config.enable_phrases,
        )

        topics = extractor.extract_topics("What are RAG techniques for LLM optimization?")

        assert len(topics) <= 5
        assert all(t.confidence >= 0.5 for t in topics)
        assert all(len(t.name) >= 3 for t in topics)

    def test_realistic_query_extraction(self):
        """Test extraction from realistic user query."""
        extractor = TopicExtractor()

        query = "What are the best practices for implementing RAG with vector databases like ChromaDB?"

        topics = extractor.extract_topics(query)

        topic_names = [t.name for t in topics]

        # Should extract key terms
        assert "RAG" in topic_names
        assert any("vector" in name or "database" in name for name in topic_names)
        assert any("chroma" in name.lower() for name in topic_names)
