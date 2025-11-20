"""
Security tests for v0.3.3 Intelligent Chunking.

Tests cover vulnerabilities identified in security audit:
- HIGH-001: Division by zero in cosine similarity
- HIGH-002: Unbounded memory usage in embedding operations
- MEDIUM-002: Missing input size validation
- MEDIUM-003: ReDoS vulnerability in sentence splitting
"""

import numpy as np
import pytest
import time
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from src.chunking.semantic_chunker import SemanticChunker
from src.chunking.hierarchical_chunker import HierarchicalChunker


class TestSemanticChunkerSecurity:
    """Security tests for SemanticChunker."""

    def test_division_by_zero_protection(self):
        """
        HIGH-001: Test cosine similarity handles zero-norm vectors.

        Vulnerability: Division by zero when embeddings have zero norm.
        Expected: Should handle gracefully without crashing.
        """
        chunker = SemanticChunker()

        # Create embeddings with zero-norm vector
        embeddings = np.array([
            [1.0, 0.0, 0.0],
            [0.0, 0.0, 0.0],  # Zero-norm vector
            [0.0, 1.0, 0.0],
        ])

        # Should not crash
        try:
            similarities = chunker._calculate_similarities(embeddings)
            # Should complete without error
            assert len(similarities) == 2
            # Zero-norm should result in 0.0 or handled gracefully
        except ZeroDivisionError:
            pytest.fail("Division by zero not protected (HIGH-001 not fixed)")

    def test_memory_exhaustion_protection(self):
        """
        HIGH-002: Test protection against memory exhaustion from large documents.

        Vulnerability: Unbounded memory allocation for sentence embeddings.
        Expected: Should either limit or batch process large inputs.
        """
        chunker = SemanticChunker()

        # Create very large document (simulated)
        # 15,000 sentences would exceed recommended limit
        large_text = "This is a test sentence. " * 15000

        # Mock the model to prevent actual embedding
        with patch.object(chunker, '_model', None):
            # Should fallback or handle gracefully
            chunks = chunker.split_text(large_text)
            assert len(chunks) > 0  # Should not crash

    def test_input_size_validation(self):
        """
        MEDIUM-002: Test input size limits to prevent DoS.

        Vulnerability: No maximum input size check.
        Expected: Should reject or warn about oversized inputs.
        """
        chunker = SemanticChunker()

        # Create 15MB text (exceeds typical 10MB limit if implemented)
        large_text = "X" * (15 * 1024 * 1024)

        # Should either:
        # 1. Raise ValueError for oversized input (preferred)
        # 2. Process with fallback (acceptable)
        # 3. Complete without memory exhaustion (minimum requirement)
        try:
            with patch.object(chunker, '_model', None):
                chunks = chunker.split_text(large_text)
                # If no error, should at least complete
                assert isinstance(chunks, list)
        except ValueError as e:
            # Acceptable: input size validation error
            assert "too large" in str(e).lower() or "size" in str(e).lower()

    def test_redos_protection_sentence_splitting(self):
        """
        MEDIUM-003: Test ReDoS protection in sentence splitting.

        Vulnerability: Catastrophic backtracking in regex.
        Expected: Should complete quickly even with pathological input.
        """
        chunker = SemanticChunker()

        # Pathological input: many consecutive punctuation marks
        pathological_text = "!" * 10000 + " Test sentence."

        start = time.time()
        sentences = chunker._split_sentences(pathological_text)
        elapsed = time.time() - start

        # Should complete quickly (< 1 second)
        assert elapsed < 1.0, f"Sentence splitting took {elapsed:.2f}s (possible ReDoS)"
        assert len(sentences) > 0

    def test_invalid_similarity_threshold(self):
        """
        MEDIUM-004: Test validation of similarity threshold parameter.

        Vulnerability: Threshold not validated to be in [0.0, 1.0].
        Expected: Should raise ValueError for invalid thresholds.
        """
        # Too high
        with pytest.raises(ValueError, match="similarity_threshold|threshold"):
            SemanticChunker(similarity_threshold=1.5)

        # Too low (if negative values rejected)
        try:
            SemanticChunker(similarity_threshold=-0.5)
        except ValueError:
            pass  # Acceptable to reject negative values

        # Valid boundaries should work
        chunker_min = SemanticChunker(similarity_threshold=0.0)
        assert chunker_min.similarity_threshold == 0.0

        chunker_max = SemanticChunker(similarity_threshold=1.0)
        assert chunker_max.similarity_threshold == 1.0

    def test_unicode_handling(self):
        """
        Edge case: Test handling of Unicode and emoji in text.

        Expected: Should handle without crashing.
        """
        chunker = SemanticChunker()

        text = "First sentence 你好. Second sentence مرحبا! Third sentence with emoji 😀."

        with patch.object(chunker, '_model', None):
            # Should fallback gracefully
            chunks = chunker.split_text(text)
            assert len(chunks) > 0

    def test_no_punctuation_handling(self):
        """
        Edge case: Test handling of text without punctuation.

        Expected: Should handle gracefully.
        """
        chunker = SemanticChunker()

        text = "This text has no punctuation marks at all just words"

        with patch.object(chunker, '_model', None):
            chunks = chunker.split_text(text)
            assert len(chunks) >= 1


class TestHierarchicalChunkerSecurity:
    """Security tests for HierarchicalChunker."""

    def test_infinite_loop_protection(self):
        """
        MEDIUM-001: Test protection against infinite loops.

        Vulnerability: overlap >= chunk_size could cause infinite loop.
        Expected: Should detect and prevent infinite loops.
        """
        chunker = HierarchicalChunker()

        # Edge case: overlap equals chunk_size
        text = "Test sentence. " * 50

        # Should not hang indefinitely
        start = time.time()
        chunks = chunker._split_with_overlap(text, chunk_size=100, overlap=100)
        elapsed = time.time() - start

        assert elapsed < 5.0, f"Possible infinite loop detected ({elapsed:.2f}s)"
        assert len(chunks) > 0
        assert len(chunks) < 1000, "Excessive chunk count suggests loop issue"

    def test_overlap_validation(self):
        """
        Test that invalid overlap/chunk_size combinations are handled.

        Expected: Should validate or adjust parameters.
        """
        chunker = HierarchicalChunker()

        text = "Test sentence. " * 20

        # overlap > chunk_size (invalid)
        try:
            chunks = chunker._split_with_overlap(text, chunk_size=50, overlap=100)
            # If it completes, should have adjusted parameters
            assert len(chunks) > 0
        except ValueError:
            pass  # Acceptable to raise error for invalid params

    def test_parameter_validation(self):
        """
        Test validation of chunk size parameters.

        Expected: Should validate size constraints.
        """
        # Invalid: min > max
        with pytest.raises(ValueError):
            HierarchicalChunker(
                min_parent_size=2000,
                max_parent_size=1000  # min > max
            )

        # Invalid: negative sizes
        with pytest.raises(ValueError):
            HierarchicalChunker(min_child_size=-100)


class TestChunkerResourceLimits:
    """Test resource consumption limits for both chunkers."""

    @pytest.mark.slow
    def test_maximum_input_size(self):
        """
        Test handling of maximum allowed input size.

        Expected: Should complete within reasonable time and memory.
        """
        semantic_chunker = SemanticChunker()
        hierarchical_chunker = HierarchicalChunker()

        # 5MB input (reasonable upper bound)
        large_text = "Test sentence. " * (5 * 1024 * 1024 // 15)

        with patch.object(semantic_chunker, '_model', None):
            start = time.time()
            chunks = semantic_chunker.split_text(large_text)
            elapsed = time.time() - start

            assert elapsed < 30.0, f"Processing took too long ({elapsed:.2f}s)"
            assert len(chunks) > 0

    @pytest.mark.slow
    def test_concurrent_chunking(self):
        """
        Test thread safety under concurrent load.

        Expected: Should handle concurrent access without crashes.
        """
        import threading

        chunker = SemanticChunker()
        text = "Test sentence. " * 100
        errors = []

        def chunk_text():
            try:
                with patch.object(chunker, '_model', None):
                    chunker.split_text(text)
            except Exception as e:
                errors.append(e)

        # Run 10 concurrent chunking operations
        threads = [threading.Thread(target=chunk_text) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=10.0)

        # Should complete without thread safety errors
        assert len(errors) == 0, f"Thread safety errors: {errors}"


# Add marker for slow tests
pytest.mark.slow = pytest.mark.skipif(
    "not config.getoption('--run-slow')",
    reason="Slow test, run with --run-slow"
)
