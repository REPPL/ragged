"""Tests for embedder factory."""

import pytest
import threading
import time
from unittest.mock import patch, Mock, MagicMock
from src.embeddings.factory import (
    create_embedder,
    get_embedder,
    clear_embedder_cache,
    get_cache_stats,
    warmup_embedder_cache,
)
from src.embeddings.base import BaseEmbedder
from src.config.settings import EmbeddingModel


class TestEmbedderFactory:
    """Tests for embedder factory functions."""

    def test_create_embedder_sentence_transformers(self):
        """Test creating sentence-transformers embedder."""
        with patch("src.embeddings.factory.SentenceTransformerEmbedder") as mock_st:
            mock_instance = Mock(spec=BaseEmbedder)
            mock_st.return_value = mock_instance

            embedder = create_embedder(
                model_type=EmbeddingModel.SENTENCE_TRANSFORMERS,
                model_name="all-MiniLM-L6-v2"
            )

            mock_st.assert_called_once_with(model_name="all-MiniLM-L6-v2")
            assert embedder == mock_instance

    def test_create_embedder_ollama(self):
        """Test creating Ollama embedder."""
        with patch("src.embeddings.factory.OllamaEmbedder") as mock_ollama:
            mock_instance = Mock(spec=BaseEmbedder)
            mock_ollama.return_value = mock_instance

            embedder = create_embedder(
                model_type=EmbeddingModel.OLLAMA,
                model_name="nomic-embed-text"
            )

            mock_ollama.assert_called_once_with(model_name="nomic-embed-text")
            assert embedder == mock_instance

    def test_create_embedder_invalid_type(self):
        """Test creating embedder with invalid type."""
        # Create a mock invalid enum value
        class InvalidModel:
            value = "invalid-type"

        with pytest.raises(ValueError, match="Unsupported embedding model type"):
            create_embedder(
                model_type=InvalidModel(),  # type: ignore[arg-type]
                model_name="some-model"
            )

    def test_create_embedder_default_model_name(self):
        """Test that default model names are used when not specified."""
        with patch("src.embeddings.factory.SentenceTransformerEmbedder") as mock_st:
            mock_instance = Mock(spec=BaseEmbedder)
            mock_st.return_value = mock_instance

            with patch("src.embeddings.factory.get_settings") as mock_settings:
                # Mock settings to return default model name
                mock_settings.return_value.embedding_model_name = "default-model"

                # Don't specify model_name
                embedder = create_embedder(model_type=EmbeddingModel.SENTENCE_TRANSFORMERS)

                # Should use default model from settings
                mock_st.assert_called_once_with(model_name="default-model")

    def test_get_embedder_returns_embedder(self):
        """Test that get_embedder returns an embedder instance."""
        with patch("src.embeddings.factory.create_embedder") as mock_create:
            mock_instance = Mock(spec=BaseEmbedder)
            mock_create.return_value = mock_instance

            embedder = get_embedder()

            # Should call create_embedder
            mock_create.assert_called_once()
            assert embedder == mock_instance

    def test_get_embedder_uses_config(self):
        """Test that get_embedder uses configuration."""
        with patch("src.embeddings.factory.create_embedder") as mock_create:
            mock_instance = Mock(spec=BaseEmbedder)
            mock_create.return_value = mock_instance

            # get_embedder() should call create_embedder with no args
            # which causes create_embedder to use settings
            embedder = get_embedder()

            # Should call create_embedder with no parameters
            mock_create.assert_called_once_with()
            assert embedder == mock_instance


class TestEmbedderCaching:
    """Tests for v0.2.9 embedder caching functionality."""

    def setup_method(self):
        """Clear cache before each test."""
        clear_embedder_cache()
        # Reset warm-up flag
        import src.embeddings.factory as factory
        factory._warmup_started = False

    def test_caching_disabled_creates_new_instance_each_time(self):
        """Test that when caching is disabled, new instances are created."""
        with patch("src.embeddings.factory.get_settings") as mock_settings:
            # Disable caching
            mock_settings.return_value.feature_flags.enable_embedder_caching = False
            mock_settings.return_value.embedding_model = EmbeddingModel.SENTENCE_TRANSFORMERS
            mock_settings.return_value.embedding_model_name = "test-model"

            with patch("src.embeddings.factory.create_embedder") as mock_create:
                mock_create.side_effect = [Mock(spec=BaseEmbedder), Mock(spec=BaseEmbedder)]

                embedder1 = get_embedder()
                embedder2 = get_embedder()

                # Should create two different instances
                assert mock_create.call_count == 2
                assert embedder1 != embedder2

    def test_caching_enabled_returns_same_instance(self):
        """Test that when caching is enabled, the same instance is returned."""
        with patch("src.embeddings.factory.get_settings") as mock_settings:
            # Enable caching
            mock_settings.return_value.feature_flags.enable_embedder_caching = True
            mock_settings.return_value.embedding_model = EmbeddingModel.SENTENCE_TRANSFORMERS
            mock_settings.return_value.embedding_model_name = "test-model"

            with patch("src.embeddings.factory.create_embedder") as mock_create:
                mock_instance = Mock(spec=BaseEmbedder)
                mock_create.return_value = mock_instance

                embedder1 = get_embedder()
                embedder2 = get_embedder()

                # Should create only once and return same instance
                mock_create.assert_called_once()
                assert embedder1 is embedder2

    def test_lru_eviction_when_cache_full(self):
        """Test that LRU eviction occurs when cache is full."""
        with patch("src.embeddings.factory.get_settings") as mock_settings:
            mock_settings.return_value.feature_flags.enable_embedder_caching = True
            mock_settings.return_value.embedding_model = EmbeddingModel.SENTENCE_TRANSFORMERS

            with patch("src.embeddings.factory.create_embedder") as mock_create:
                # Create 4 different mock instances
                mocks = [Mock(spec=BaseEmbedder) for _ in range(4)]
                mock_create.side_effect = mocks

                # Add 3 models to fill the cache (max_cache_size = 3)
                mock_settings.return_value.embedding_model_name = "model1"
                embedder1 = get_embedder()

                mock_settings.return_value.embedding_model_name = "model2"
                embedder2 = get_embedder()

                mock_settings.return_value.embedding_model_name = "model3"
                embedder3 = get_embedder()

                # Cache should have 3 items
                stats = get_cache_stats()
                assert stats["size"] == 3

                # Add a 4th model - should evict model1 (LRU)
                mock_settings.return_value.embedding_model_name = "model4"
                embedder4 = get_embedder()

                # Cache should still have 3 items
                stats = get_cache_stats()
                assert stats["size"] == 3

                # model1 should have been evicted
                assert "sentence-transformers:model1" not in stats["models"]
                assert "sentence-transformers:model4" in stats["models"]

    def test_lru_moves_to_end_on_access(self):
        """Test that accessing a cached model moves it to the end (most recent)."""
        with patch("src.embeddings.factory.get_settings") as mock_settings:
            mock_settings.return_value.feature_flags.enable_embedder_caching = True
            mock_settings.return_value.embedding_model = EmbeddingModel.SENTENCE_TRANSFORMERS

            with patch("src.embeddings.factory.create_embedder") as mock_create:
                mocks = [Mock(spec=BaseEmbedder) for _ in range(4)]
                mock_create.side_effect = mocks

                # Add 3 models
                mock_settings.return_value.embedding_model_name = "model1"
                get_embedder()

                mock_settings.return_value.embedding_model_name = "model2"
                get_embedder()

                mock_settings.return_value.embedding_model_name = "model3"
                get_embedder()

                # Access model1 (should move to end)
                mock_settings.return_value.embedding_model_name = "model1"
                get_embedder()

                # Add model4 - should evict model2 (now LRU)
                mock_settings.return_value.embedding_model_name = "model4"
                get_embedder()

                stats = get_cache_stats()
                # model2 should be evicted, model1 should still be in cache
                assert "sentence-transformers:model2" not in stats["models"]
                assert "sentence-transformers:model1" in stats["models"]

    def test_clear_cache_removes_all_entries(self):
        """Test that clear_embedder_cache removes all cached embedders."""
        with patch("src.embeddings.factory.get_settings") as mock_settings:
            mock_settings.return_value.feature_flags.enable_embedder_caching = True
            mock_settings.return_value.embedding_model = EmbeddingModel.SENTENCE_TRANSFORMERS
            mock_settings.return_value.embedding_model_name = "test-model"

            with patch("src.embeddings.factory.create_embedder") as mock_create:
                mock_create.return_value = Mock(spec=BaseEmbedder)

                # Cache an embedder
                get_embedder()

                stats = get_cache_stats()
                assert stats["size"] == 1

                # Clear cache
                count = clear_embedder_cache()
                assert count == 1

                # Cache should be empty
                stats = get_cache_stats()
                assert stats["size"] == 0

    def test_get_cache_stats_returns_correct_info(self):
        """Test that get_cache_stats returns accurate cache information."""
        with patch("src.embeddings.factory.get_settings") as mock_settings:
            mock_settings.return_value.feature_flags.enable_embedder_caching = True
            mock_settings.return_value.embedding_model = EmbeddingModel.SENTENCE_TRANSFORMERS

            with patch("src.embeddings.factory.create_embedder") as mock_create:
                mock_create.return_value = Mock(spec=BaseEmbedder)

                # Empty cache
                stats = get_cache_stats()
                assert stats["size"] == 0
                assert stats["models"] == []
                assert stats["enabled"] is True

                # Add a model
                mock_settings.return_value.embedding_model_name = "test-model"
                get_embedder()

                stats = get_cache_stats()
                assert stats["size"] == 1
                assert "sentence-transformers:test-model" in stats["models"]

    def test_thread_safety_concurrent_access(self):
        """Test that concurrent access to cache is thread-safe."""
        with patch("src.embeddings.factory.get_settings") as mock_settings:
            mock_settings.return_value.feature_flags.enable_embedder_caching = True
            mock_settings.return_value.embedding_model = EmbeddingModel.SENTENCE_TRANSFORMERS
            mock_settings.return_value.embedding_model_name = "test-model"

            call_count = 0
            lock = threading.Lock()

            def mock_create(*args, **kwargs):
                nonlocal call_count
                with lock:
                    call_count += 1
                time.sleep(0.01)  # Simulate slow model loading
                return Mock(spec=BaseEmbedder)

            with patch("src.embeddings.factory.create_embedder", side_effect=mock_create):
                # Launch 10 threads trying to get the same embedder
                threads = []
                results = []

                def get_and_store():
                    embedder = get_embedder()
                    results.append(embedder)

                for _ in range(10):
                    t = threading.Thread(target=get_and_store)
                    threads.append(t)
                    t.start()

                for t in threads:
                    t.join()

                # Only one instance should have been created
                assert call_count == 1

                # All threads should get the same instance
                assert len(set(id(r) for r in results)) == 1

    def test_warmup_with_caching_enabled(self):
        """Test that warm-up preloads embedder when caching is enabled."""
        with patch("src.embeddings.factory.get_settings") as mock_settings:
            mock_settings.return_value.feature_flags.enable_embedder_caching = True
            mock_settings.return_value.embedding_model = EmbeddingModel.SENTENCE_TRANSFORMERS
            mock_settings.return_value.embedding_model_name = "test-model"

            with patch("src.embeddings.factory.create_embedder") as mock_create:
                mock_create.return_value = Mock(spec=BaseEmbedder)

                # Call warm-up
                warmup_embedder_cache()

                # Give background thread time to complete
                time.sleep(0.1)

                # Embedder should have been created
                mock_create.assert_called_once()

                # Cache should have the embedder
                stats = get_cache_stats()
                assert stats["size"] == 1

    def test_warmup_with_caching_disabled(self):
        """Test that warm-up does nothing when caching is disabled."""
        with patch("src.embeddings.factory.get_settings") as mock_settings:
            mock_settings.return_value.feature_flags.enable_embedder_caching = False

            with patch("src.embeddings.factory.create_embedder") as mock_create:
                # Call warm-up
                warmup_embedder_cache()

                # Give background thread time (if it started)
                time.sleep(0.1)

                # Embedder should NOT have been created
                mock_create.assert_not_called()

    def test_warmup_is_idempotent(self):
        """Test that calling warm-up multiple times doesn't create multiple threads."""
        with patch("src.embeddings.factory.get_settings") as mock_settings:
            mock_settings.return_value.feature_flags.enable_embedder_caching = True
            mock_settings.return_value.embedding_model = EmbeddingModel.SENTENCE_TRANSFORMERS
            mock_settings.return_value.embedding_model_name = "test-model"

            with patch("src.embeddings.factory.create_embedder") as mock_create:
                mock_create.return_value = Mock(spec=BaseEmbedder)

                # Call warm-up multiple times
                warmup_embedder_cache()
                warmup_embedder_cache()
                warmup_embedder_cache()

                # Give background thread time
                time.sleep(0.1)

                # Should only create once
                mock_create.assert_called_once()

    def test_warmup_handles_errors_gracefully(self):
        """Test that warm-up handles errors without crashing."""
        with patch("src.embeddings.factory.get_settings") as mock_settings:
            mock_settings.return_value.feature_flags.enable_embedder_caching = True
            mock_settings.return_value.embedding_model = EmbeddingModel.SENTENCE_TRANSFORMERS
            mock_settings.return_value.embedding_model_name = "test-model"

            with patch("src.embeddings.factory.create_embedder") as mock_create:
                mock_create.side_effect = Exception("Model loading failed")

                # Should not raise exception
                warmup_embedder_cache()

                # Give background thread time
                time.sleep(0.1)

                # Cache should be empty
                stats = get_cache_stats()
                assert stats["size"] == 0
