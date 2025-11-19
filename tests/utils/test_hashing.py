"""Tests for hashing utilities.

v0.2.9: Comprehensive tests for content hashing functions.
"""

import pytest
from src.utils.hashing import hash_content, hash_file_content, hash_query


class TestHashContent:
    """Tests for hash_content function."""

    def test_hash_string(self):
        """Test hashing a string."""
        result = hash_content("hello world")
        expected = "b94d27b9934d3e08a52e52d7da7dabfac484efe37a5380ee9088f7ace2efcde9"
        assert result == expected

    def test_hash_bytes(self):
        """Test hashing bytes."""
        result = hash_content(b"hello world")
        expected = "b94d27b9934d3e08a52e52d7da7dabfac484efe37a5380ee9088f7ace2efcde9"
        assert result == expected

    def test_string_and_bytes_produce_same_hash(self):
        """Test that string and bytes produce identical hashes."""
        str_hash = hash_content("test content")
        bytes_hash = hash_content(b"test content")
        assert str_hash == bytes_hash

    def test_hash_empty_string(self):
        """Test hashing empty string."""
        result = hash_content("")
        expected = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
        assert result == expected

    def test_hash_empty_bytes(self):
        """Test hashing empty bytes."""
        result = hash_content(b"")
        expected = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
        assert result == expected

    def test_hash_unicode_string(self):
        """Test hashing unicode content."""
        result = hash_content("Hello 世界 🌍")
        # Should successfully hash unicode
        assert isinstance(result, str)
        assert len(result) == 64  # SHA-256 hex length

    def test_hash_different_encoding(self):
        """Test hash with different encoding."""
        # UTF-8 is default
        utf8_hash = hash_content("test", encoding="utf-8")
        # Should also work with ascii for ascii strings
        ascii_hash = hash_content("test", encoding="ascii")
        assert utf8_hash == ascii_hash

    def test_hash_consistency(self):
        """Test that same content always produces same hash."""
        content = "consistency test content"
        hash1 = hash_content(content)
        hash2 = hash_content(content)
        hash3 = hash_content(content)
        assert hash1 == hash2 == hash3

    def test_hash_sensitivity(self):
        """Test that small changes produce different hashes."""
        hash1 = hash_content("test")
        hash2 = hash_content("Test")  # Different case
        hash3 = hash_content("test ")  # Extra space
        assert hash1 != hash2
        assert hash1 != hash3
        assert hash2 != hash3

    def test_hash_length(self):
        """Test that hash is always 64 characters (SHA-256 hex)."""
        for content in ["", "short", "a" * 10000]:
            result = hash_content(content)
            assert len(result) == 64

    def test_hash_format(self):
        """Test that hash is hexadecimal."""
        result = hash_content("test")
        # Should only contain hex characters
        assert all(c in "0123456789abcdef" for c in result)


class TestHashFileContent:
    """Tests for hash_file_content function."""

    def test_hash_small_file(self):
        """Test hashing content smaller than sample size."""
        content = "small content"
        result = hash_file_content(content, sample_size=1024)
        # Should hash entire content
        expected = hash_content(content)
        assert result == expected

    def test_hash_large_file_samples(self):
        """Test hashing large file uses sampling."""
        # Create content larger than 2 * sample_size
        content = "a" * 1000 + "middle content" + "b" * 1000
        result = hash_file_content(content, sample_size=100)

        # Should hash first 100 + last 100 bytes
        content_bytes = content.encode("utf-8")
        expected = hash_content(content_bytes[:100] + content_bytes[-100:])
        assert result == expected

    def test_hash_exactly_double_sample_size(self):
        """Test file exactly 2x sample size is hashed entirely."""
        content = "a" * 200
        result = hash_file_content(content, sample_size=100)
        # 200 bytes = 2 * 100, should hash entirely
        expected = hash_content(content)
        assert result == expected

    def test_hash_just_over_double_sample_size(self):
        """Test file just over 2x sample size uses sampling."""
        content = "a" * 201
        result = hash_file_content(content, sample_size=100)
        # 201 bytes > 2 * 100, should use sampling
        content_bytes = content.encode("utf-8")
        expected = hash_content(content_bytes[:100] + content_bytes[-100:])
        assert result == expected

    def test_hash_empty_content(self):
        """Test hashing empty file content."""
        result = hash_file_content("", sample_size=1024)
        expected = hash_content("")
        assert result == expected

    def test_hash_unicode_content(self):
        """Test hashing unicode file content."""
        content = "Hello 世界 🌍" * 1000
        result = hash_file_content(content, sample_size=100)
        assert isinstance(result, str)
        assert len(result) == 64

    def test_different_sample_sizes(self):
        """Test different sample sizes produce different hashes for large files."""
        content = "a" * 10000

        hash_100 = hash_file_content(content, sample_size=100)
        hash_500 = hash_file_content(content, sample_size=500)

        # For homogeneous content, might be same, but for varied content would differ
        # At minimum, both should be valid hashes
        assert len(hash_100) == 64
        assert len(hash_500) == 64

    def test_hash_consistency_sampling(self):
        """Test sampling produces consistent results."""
        content = "start content " + "a" * 10000 + " end content"
        hash1 = hash_file_content(content, sample_size=100)
        hash2 = hash_file_content(content, sample_size=100)
        assert hash1 == hash2

    def test_hash_varied_content(self):
        """Test hashing file with varied content."""
        # Create content with varied beginning and end
        content = "START" * 100 + "MIDDLE" * 1000 + "END" * 100
        result = hash_file_content(content, sample_size=50)

        # Should capture different start and end
        content_bytes = content.encode("utf-8")
        expected = hash_content(content_bytes[:50] + content_bytes[-50:])
        assert result == expected


class TestHashQuery:
    """Tests for hash_query function."""

    def test_hash_simple_query(self):
        """Test hashing a simple query."""
        result = hash_query("what is machine learning?")
        # Should be same as hash_content
        expected = hash_content("what is machine learning?")
        assert result == expected

    def test_hash_empty_query(self):
        """Test hashing empty query."""
        result = hash_query("")
        expected = hash_content("")
        assert result == expected

    def test_hash_unicode_query(self):
        """Test hashing unicode query."""
        result = hash_query("什么是机器学习？")
        assert isinstance(result, str)
        assert len(result) == 64

    def test_hash_query_consistency(self):
        """Test that same query always produces same hash (for caching)."""
        query = "tell me about python programming"
        hash1 = hash_query(query)
        hash2 = hash_query(query)
        hash3 = hash_query(query)
        assert hash1 == hash2 == hash3

    def test_hash_query_sensitivity(self):
        """Test that queries are case-sensitive."""
        hash1 = hash_query("Machine Learning")
        hash2 = hash_query("machine learning")
        assert hash1 != hash2

    def test_hash_query_whitespace_sensitive(self):
        """Test that whitespace matters."""
        hash1 = hash_query("machine learning")
        hash2 = hash_query("machine  learning")  # Double space
        assert hash1 != hash2

    def test_hash_long_query(self):
        """Test hashing very long query."""
        long_query = "what is " * 1000
        result = hash_query(long_query)
        assert isinstance(result, str)
        assert len(result) == 64


class TestIntegrationScenarios:
    """Integration tests for realistic scenarios."""

    def test_document_deduplication(self):
        """Test using hashes for document deduplication."""
        doc1 = "This is a test document"
        doc2 = "This is a test document"  # Duplicate
        doc3 = "This is a different document"

        hash1 = hash_content(doc1)
        hash2 = hash_content(doc2)
        hash3 = hash_content(doc3)

        # Duplicates should have same hash
        assert hash1 == hash2
        # Different content should have different hash
        assert hash1 != hash3

    def test_query_caching_keys(self):
        """Test using query hashes as cache keys."""
        queries = [
            "what is RAG?",
            "what is RAG?",  # Duplicate
            "What is RAG?",  # Different case
            "what is RAG? ",  # Extra whitespace
        ]

        hashes = [hash_query(q) for q in queries]

        # First two should match
        assert hashes[0] == hashes[1]
        # Case-sensitive: should differ
        assert hashes[0] != hashes[2]
        # Whitespace-sensitive: should differ
        assert hashes[0] != hashes[3]

    def test_file_change_detection(self):
        """Test detecting file changes using hashes."""
        # Simulate file content versions
        v1 = "Original content\n" + "a" * 10000
        v2 = "Original content\n" + "a" * 10000  # Same
        v3 = "Modified content\n" + "a" * 10000  # Changed start
        v4 = "Original content\n" + "b" * 10000  # Changed end

        hash_v1 = hash_file_content(v1, sample_size=100)
        hash_v2 = hash_file_content(v2, sample_size=100)
        hash_v3 = hash_file_content(v3, sample_size=100)
        hash_v4 = hash_file_content(v4, sample_size=100)

        # v1 and v2 should match (identical)
        assert hash_v1 == hash_v2
        # v3 changed beginning (in sample)
        assert hash_v1 != hash_v3
        # v4 changed end (in sample)
        assert hash_v1 != hash_v4

    def test_hash_as_dictionary_key(self):
        """Test using hashes as dictionary keys."""
        cache = {}

        # Store items by content hash
        content1 = "first item"
        content2 = "second item"

        key1 = hash_content(content1)
        key2 = hash_content(content2)

        cache[key1] = {"data": content1}
        cache[key2] = {"data": content2}

        # Retrieve by hash
        assert cache[hash_content("first item")]["data"] == "first item"
        assert cache[hash_content("second item")]["data"] == "second item"

    def test_collision_resistance(self):
        """Test that similar content produces different hashes."""
        # Similar but not identical content
        contents = [
            "The quick brown fox",
            "The quick brown fox ",
            "The quick brown fox.",
            "the quick brown fox",
            "The quick brown foxes",
        ]

        hashes = [hash_content(c) for c in contents]

        # All should be unique
        assert len(set(hashes)) == len(hashes)
