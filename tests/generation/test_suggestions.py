"""Tests for smart query suggestions.

v0.3.12: Test query refinement and suggestions.
"""

import pytest

from src.generation.suggestions import (
    QuerySuggester,
    QuerySuggestions,
    create_query_suggester,
)


class TestQuerySuggester:
    """Test QuerySuggester class."""

    @pytest.fixture
    def suggester(self):
        """Create query suggester."""
        return create_query_suggester()

    def test_init(self, suggester):
        """Test suggester initialisation."""
        assert isinstance(suggester, QuerySuggester)
        assert suggester.llm_client is None

    def test_suggest_returns_suggestions(self, suggester):
        """Test suggest returns QuerySuggestions."""
        suggestions = suggester.suggest("what is machine learning")
        assert isinstance(suggestions, QuerySuggestions)
        assert suggestions.original == "what is machine learning"
        assert isinstance(suggestions.corrections, list)
        assert isinstance(suggestions.refinements, list)
        assert isinstance(suggestions.related, list)
        assert isinstance(suggestions.quality_score, float)

    def test_spelling_correction(self, suggester):
        """Test spelling correction."""
        # Test common misspelling
        suggestions = suggester.suggest("wat is machien learnign")
        assert len(suggestions.corrections) > 0
        assert "what is machine learning" in suggestions.corrections[0]

    def test_no_spelling_corrections_for_correct_query(self, suggester):
        """Test no corrections for correctly spelled query."""
        suggestions = suggester.suggest("what is machine learning")
        assert len(suggestions.corrections) == 0

    def test_vague_query_detection(self, suggester):
        """Test vague query detection."""
        assert suggester._is_vague("ml")  # Too short
        assert suggester._is_vague("machine learning")  # No question word
        assert not suggester._is_vague("what is machine learning")

    def test_query_refinement(self, suggester):
        """Test query refinement for vague queries."""
        suggestions = suggester.suggest("machine learning")
        assert len(suggestions.refinements) > 0
        # Should suggest question formats
        assert any("what" in r.lower() for r in suggestions.refinements)

    def test_no_refinement_for_good_query(self, suggester):
        """Test no refinement for well-formed query."""
        suggestions = suggester.suggest("what are the main concepts in machine learning?")
        assert len(suggestions.refinements) == 0

    def test_related_queries_generated(self, suggester):
        """Test related queries generation."""
        suggestions = suggester.suggest("what is deep learning")
        assert len(suggestions.related) > 0
        assert len(suggestions.related) <= 4  # Max 4

    def test_related_queries_contain_topic(self, suggester):
        """Test related queries reference the topic."""
        suggestions = suggester.suggest("what is neural networks")
        # Should contain variations on the topic
        assert any("neural networks" in r.lower() for r in suggestions.related)

    def test_quality_score_range(self, suggester):
        """Test quality score is between 0 and 1."""
        suggestions = suggester.suggest("test query")
        assert 0.0 <= suggestions.quality_score <= 1.0

    def test_quality_score_good_query(self, suggester):
        """Test quality score for well-formed query."""
        suggestions = suggester.suggest("what are the key concepts in machine learning?")
        assert suggestions.quality_score > 0.5  # Should score well

    def test_quality_score_poor_query(self, suggester):
        """Test quality score for poor query."""
        suggestions = suggester.suggest("ml")
        assert suggestions.quality_score < 0.5  # Should score poorly

    def test_quality_score_question_word_bonus(self, suggester):
        """Test quality score gives bonus for question words."""
        score_with_question = suggester._score_query("what is this")
        score_without_question = suggester._score_query("this thing")
        assert score_with_question > score_without_question

    def test_quality_score_length_bonus(self, suggester):
        """Test quality score gives bonus for sufficient length."""
        score_long = suggester._score_query("what are the main concepts in machine learning")
        score_short = suggester._score_query("what ml")
        assert score_long > score_short

    def test_multiple_corrections(self, suggester):
        """Test multiple spelling corrections."""
        suggestions = suggester.suggest("wat r the main findings")
        assert len(suggestions.corrections) > 0
        corrected = suggestions.corrections[0]
        assert "what" in corrected.lower()
        assert "are" in corrected.lower()

    def test_refinement_patterns(self, suggester):
        """Test different refinement patterns."""
        # Keywords only -> suggest questions
        refinements = suggester._refine_query("machine learning")
        assert any("what is" in r.lower() for r in refinements)
        assert any("how does" in r.lower() for r in refinements)

    def test_related_query_fallback(self, suggester):
        """Test related queries fallback for simple queries."""
        suggestions = suggester.suggest("test")
        # Should generate generic related queries
        assert len(suggestions.related) > 0

    def test_empty_query_handling(self, suggester):
        """Test handling of empty query."""
        suggestions = suggester.suggest("")
        assert suggestions.original == ""
        assert suggestions.quality_score < 0.3  # Low score for empty

    def test_create_query_suggester_factory(self):
        """Test factory function."""
        suggester = create_query_suggester()
        assert isinstance(suggester, QuerySuggester)
        assert suggester.llm_client is None

    def test_create_query_suggester_with_llm(self):
        """Test factory function with LLM client."""
        mock_llm = object()
        suggester = create_query_suggester(llm_client=mock_llm)
        assert suggester.llm_client is mock_llm
