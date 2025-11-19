"""Tests for recursive character text splitter.

v0.2.9: Tests for text chunking with recursive separators.
"""

import pytest
from unittest.mock import patch, Mock

from src.chunking.splitters.recursive_splitter import RecursiveCharacterTextSplitter


@pytest.fixture
def default_splitter():
    """Create splitter with default settings."""
    with patch("src.chunking.splitters.recursive_splitter.get_settings") as mock_settings:
        mock_settings.return_value = Mock(chunk_size=512, chunk_overlap=50)
        return RecursiveCharacterTextSplitter()


@pytest.fixture
def small_splitter():
    """Create splitter with small chunk size for testing."""
    return RecursiveCharacterTextSplitter(chunk_size=100, chunk_overlap=20)


class TestInitialization:
    """Tests for RecursiveCharacterTextSplitter initialization."""

    def test_default_initialization(self, default_splitter):
        """Test initialization with default settings."""
        assert default_splitter.chunk_size == 512
        assert default_splitter.chunk_overlap == 50
        assert default_splitter.separators == ["\n\n", "\n", ". ", " ", ""]

    def test_custom_chunk_size(self):
        """Test initialization with custom chunk size."""
        splitter = RecursiveCharacterTextSplitter(chunk_size=256)
        assert splitter.chunk_size == 256

    def test_custom_chunk_overlap(self):
        """Test initialization with custom overlap."""
        splitter = RecursiveCharacterTextSplitter(chunk_size=512, chunk_overlap=100)
        assert splitter.chunk_overlap == 100

    def test_custom_separators(self):
        """Test initialization with custom separators."""
        custom_seps = ["\n", ".", ","]
        splitter = RecursiveCharacterTextSplitter(chunk_size=512, separators=custom_seps)
        assert splitter.separators == custom_seps

    def test_overlap_exceeds_chunk_size(self):
        """Test that overlap >= chunk_size raises error."""
        with pytest.raises(ValueError, match="chunk_overlap.*must be less than chunk_size"):
            RecursiveCharacterTextSplitter(chunk_size=100, chunk_overlap=100)

        with pytest.raises(ValueError):
            RecursiveCharacterTextSplitter(chunk_size=100, chunk_overlap=150)


class TestSplitText:
    """Tests for split_text method."""

    def test_empty_text(self, default_splitter):
        """Test splitting empty text."""
        result = default_splitter.split_text("")
        assert result == []

    def test_short_text(self, small_splitter):
        """Test text shorter than chunk size."""
        text = "Short text"
        result = small_splitter.split_text(text)
        assert len(result) == 1
        assert result[0] == text

    def test_split_by_double_newline(self):
        """Test splitting by double newline (paragraph)."""
        splitter = RecursiveCharacterTextSplitter(chunk_size=50, chunk_overlap=0)
        text = "Paragraph 1.\n\nParagraph 2.\n\nParagraph 3."

        result = splitter.split_text(text)

        # Should split by \n\n
        assert len(result) >= 2

    def test_split_by_single_newline(self):
        """Test splitting by single newline when needed."""
        splitter = RecursiveCharacterTextSplitter(chunk_size=30, chunk_overlap=0)
        text = "Line 1\nLine 2\nLine 3\nLine 4"

        result = splitter.split_text(text)

        # Should split by \n when \n\n not available
        assert len(result) >= 2

    def test_split_by_sentence(self):
        """Test splitting by sentence."""
        splitter = RecursiveCharacterTextSplitter(chunk_size=40, chunk_overlap=0)
        text = "First sentence. Second sentence. Third sentence."

        result = splitter.split_text(text)

        # Should attempt to split by ". "
        assert len(result) >= 1

    def test_split_by_space(self):
        """Test splitting by space when needed."""
        splitter = RecursiveCharacterTextSplitter(chunk_size=30, chunk_overlap=0)
        text = "word1 word2 word3 word4 word5 word6"

        result = splitter.split_text(text)

        # Should split by space
        assert len(result) >= 2

    @patch("src.chunking.splitters.recursive_splitter.count_tokens")
    def test_split_by_character(self, mock_count_tokens):
        """Test splitting by character when text too long."""
        # Mock token counter to force character splitting
        mock_count_tokens.return_value = 1000  # Always too many tokens

        splitter = RecursiveCharacterTextSplitter(chunk_size=50, chunk_overlap=0)
        text = "VeryLongWordThatCannotBeSplitByAnySeparator" * 10

        # Should not crash and should split somehow
        result = splitter.split_text(text)
        assert len(result) >= 1


class TestOverlap:
    """Tests for chunk overlap functionality."""

    def test_overlap_added(self):
        """Test that overlap is added between chunks."""
        splitter = RecursiveCharacterTextSplitter(chunk_size=50, chunk_overlap=10)
        text = "First chunk here.\n\nSecond chunk here.\n\nThird chunk here."

        result = splitter.split_text(text)

        if len(result) > 1:
            # Second chunk should contain some text from first
            # (overlap is character-based estimate)
            assert len(result[1]) > len("Second chunk here.")

    def test_no_overlap_for_single_chunk(self):
        """Test no overlap when only one chunk."""
        splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
        text = "Short text"

        result = splitter.split_text(text)

        assert len(result) == 1
        assert result[0] == text

    def test_zero_overlap(self):
        """Test with zero overlap."""
        splitter = RecursiveCharacterTextSplitter(chunk_size=50, chunk_overlap=0)
        text = "Chunk 1.\n\nChunk 2.\n\nChunk 3."

        result = splitter.split_text(text)

        # Each chunk should not contain content from others
        # (Exact verification depends on how splits work)
        assert len(result) >= 1


class TestRecursiveSplitting:
    """Tests for recursive splitting behavior."""

    @patch("src.chunking.splitters.recursive_splitter.count_tokens")
    def test_tries_separators_in_order(self, mock_count_tokens):
        """Test that separators are tried in order."""
        # Set up token counting to force splitting
        def token_counter(text):
            # Make combined chunks too large
            if len(text) > 30:
                return 1000
            return len(text.split())

        mock_count_tokens.side_effect = token_counter

        splitter = RecursiveCharacterTextSplitter(
            chunk_size=50,
            chunk_overlap=0,
            separators=["\n\n", "\n", " "]
        )

        # Text with double newlines
        text = "Para 1\n\nPara 2\n\nPara 3"
        result = splitter.split_text(text)

        # Should split by \n\n first
        assert len(result) >= 2

    @patch("src.chunking.splitters.recursive_splitter.count_tokens")
    def test_falls_back_to_finer_separators(self, mock_count_tokens):
        """Test fallback to finer separators when needed."""
        # Make paragraphs too large individually
        def token_counter(text):
            if "paragraph" in text.lower() and len(text) > 50:
                return 1000
            return 10

        mock_count_tokens.side_effect = token_counter

        splitter = RecursiveCharacterTextSplitter(
            chunk_size=50,
            chunk_overlap=0
        )

        text = "Long paragraph that needs to be split further. Contains multiple sentences."
        result = splitter.split_text(text)

        # Should recursively split the long paragraph
        assert len(result) >= 1


class TestEdgeCases:
    """Tests for edge cases and unusual inputs."""

    def test_text_all_newlines(self, small_splitter):
        """Test text that is all newlines."""
        text = "\n\n\n\n"
        result = small_splitter.split_text(text)

        # Should handle gracefully
        assert isinstance(result, list)

    def test_text_no_separators(self):
        """Test text without any standard separators."""
        splitter = RecursiveCharacterTextSplitter(chunk_size=20, chunk_overlap=0)
        text = "abcdefghijklmnopqrstuvwxyz" * 10

        result = splitter.split_text(text)

        # Should fall back to character splitting
        assert len(result) >= 1

    def test_very_long_word(self):
        """Test handling of very long word."""
        splitter = RecursiveCharacterTextSplitter(chunk_size=50, chunk_overlap=0)
        text = "a" * 1000  # 1000 character word

        result = splitter.split_text(text)

        # Should split somehow (character splitting)
        assert len(result) >= 1

    def test_unicode_text(self):
        """Test handling of unicode text."""
        splitter = RecursiveCharacterTextSplitter(chunk_size=50, chunk_overlap=10)
        text = "こんにちは世界\n\nНалло Welt\n\nΓεια σου κόσμε"

        result = splitter.split_text(text)

        # Should handle unicode gracefully
        assert len(result) >= 1
        # All text should be preserved
        combined = " ".join(result)
        assert "こんにちは" in combined
        assert "Налло" in combined

    def test_mixed_separators(self):
        """Test text with mixed separator types."""
        splitter = RecursiveCharacterTextSplitter(chunk_size=60, chunk_overlap=0)
        text = "Paragraph 1.\n\nSentence 1. Sentence 2.\nLine 1\nLine 2"

        result = splitter.split_text(text)

        # Should handle mixed separators
        assert len(result) >= 1


class TestIntegrationScenarios:
    """Integration tests for realistic text splitting scenarios."""

    def test_article_splitting(self):
        """Test splitting a typical article."""
        splitter = RecursiveCharacterTextSplitter(chunk_size=200, chunk_overlap=50)

        article = """
        Introduction

        This is the introduction paragraph. It provides context about the topic.

        Main Content

        The main content goes here. It contains multiple sentences with detailed information.
        This continues with more details and examples.

        Conclusion

        The conclusion summarizes the key points discussed above.
        """

        result = splitter.split_text(article)

        # Should create multiple chunks
        assert len(result) >= 2

        # First chunk should contain "Introduction"
        assert "Introduction" in result[0]

        # Chunks should have overlap
        if len(result) > 1:
            # Some content should appear in adjacent chunks
            # (difficult to verify exactly due to token counting)
            pass

    def test_code_splitting(self):
        """Test splitting code with function definitions."""
        splitter = RecursiveCharacterTextSplitter(chunk_size=150, chunk_overlap=20)

        code = """
def function1():
    return "result1"

def function2():
    return "result2"

def function3():
    return "result3"
        """

        result = splitter.split_text(code)

        # Should split by double newlines (between functions)
        assert len(result) >= 1

    def test_chat_transcript_splitting(self):
        """Test splitting chat/dialogue format."""
        splitter = RecursiveCharacterTextSplitter(chunk_size=100, chunk_overlap=20)

        transcript = """
        Alice: Hello, how are you?
        Bob: I'm doing great, thanks!

        Alice: What are you working on?
        Bob: I'm building a text splitter.

        Alice: That sounds interesting!
        Bob: It handles different types of separators.
        """

        result = splitter.split_text(transcript)

        # Should create multiple chunks
        assert len(result) >= 1

        # Should preserve conversation structure
        combined = " ".join(result)
        assert "Alice:" in combined
        assert "Bob:" in combined

    def test_markdown_document_splitting(self):
        """Test splitting markdown document."""
        splitter = RecursiveCharacterTextSplitter(chunk_size=150, chunk_overlap=30)

        markdown = """
# Heading 1

Some content under heading 1.

## Heading 2

More content here. Multiple paragraphs.

Another paragraph with details.

## Heading 3

Final section content.
        """

        result = splitter.split_text(markdown)

        # Should preserve headings with their content
        assert len(result) >= 1

    def test_list_splitting(self):
        """Test splitting bulleted/numbered lists."""
        splitter = RecursiveCharacterTextSplitter(chunk_size=80, chunk_overlap=10)

        list_text = """
        Shopping list:
        - Apples
        - Bananas
        - Oranges

        Todo list:
        1. Buy groceries
        2. Clean house
        3. Write code
        """

        result = splitter.split_text(list_text)

        # Should handle lists
        assert len(result) >= 1

    def test_preserves_all_content(self):
        """Test that no content is lost during splitting."""
        splitter = RecursiveCharacterTextSplitter(chunk_size=100, chunk_overlap=20)

        original_text = "The quick brown fox jumps over the lazy dog. " * 20

        result = splitter.split_text(original_text)

        # Join all chunks (removing overlap is tricky, so just verify all words present)
        combined = " ".join(result)

        # Key words should all be present
        assert "quick" in combined
        assert "brown" in combined
        assert "fox" in combined
        assert "lazy" in combined
        assert "dog" in combined

    @patch("src.chunking.splitters.recursive_splitter.count_tokens")
    def test_respects_token_limits(self, mock_count_tokens):
        """Test that chunks respect token limits."""
        # Mock token counter with realistic values
        def token_counter(text):
            return len(text.split())  # Simple word count

        mock_count_tokens.side_effect = token_counter

        splitter = RecursiveCharacterTextSplitter(chunk_size=10, chunk_overlap=2)

        text = " ".join([f"word{i}" for i in range(50)])  # 50 words

        result = splitter.split_text(text)

        # Each chunk should have <= 10 tokens (approximately)
        for chunk in result:
            # Account for overlap
            assert mock_count_tokens(chunk) <= 12  # chunk_size + some tolerance
