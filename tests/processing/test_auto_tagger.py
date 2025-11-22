"""Tests for automatic document tagging and classification.

v0.3.7e: Test LLM-based classification and rule-based fallback.
"""

import json
from unittest.mock import Mock

import pytest

from src.processing.auto_tagger import (
    AcademicLevel,
    AutoTagger,
    DocumentTags,
    DocumentType,
    tag_document,
)


class TestDocumentType:
    """Test DocumentType enum."""

    def test_document_types(self):
        """Test all document type values."""
        assert DocumentType.RESEARCH_PAPER.value == "research_paper"
        assert DocumentType.BOOK.value == "book"
        assert DocumentType.ARTICLE.value == "article"
        assert DocumentType.TECHNICAL_DOC.value == "technical_doc"
        assert DocumentType.BLOG_POST.value == "blog_post"
        assert DocumentType.NEWS.value == "news"
        assert DocumentType.TUTORIAL.value == "tutorial"
        assert DocumentType.REFERENCE.value == "reference"
        assert DocumentType.OTHER.value == "other"


class TestAcademicLevel:
    """Test AcademicLevel enum."""

    def test_academic_levels(self):
        """Test all academic level values."""
        assert AcademicLevel.INTRODUCTORY.value == "introductory"
        assert AcademicLevel.INTERMEDIATE.value == "intermediate"
        assert AcademicLevel.ADVANCED.value == "advanced"
        assert AcademicLevel.EXPERT.value == "expert"
        assert AcademicLevel.NOT_APPLICABLE.value == "not_applicable"


class TestDocumentTags:
    """Test DocumentTags dataclass."""

    def test_default_tags(self):
        """Test default tag values."""
        tags = DocumentTags()

        assert tags.document_type == DocumentType.OTHER
        assert tags.topics == []
        assert tags.language == "en"
        assert tags.academic_level == AcademicLevel.NOT_APPLICABLE
        assert tags.entities == {}
        assert tags.keywords == []
        assert tags.confidence == 0.0

    def test_custom_tags(self):
        """Test custom tag values."""
        tags = DocumentTags(
            document_type=DocumentType.RESEARCH_PAPER,
            topics=["machine learning", "neural networks"],
            language="en",
            academic_level=AcademicLevel.ADVANCED,
            entities={"people": ["Geoffrey Hinton"]},
            keywords=["deep", "learning", "neural"],
            confidence=0.95,
        )

        assert tags.document_type == DocumentType.RESEARCH_PAPER
        assert len(tags.topics) == 2
        assert tags.academic_level == AcademicLevel.ADVANCED
        assert tags.confidence == 0.95

    def test_to_dict(self):
        """Test converting tags to dictionary."""
        tags = DocumentTags(
            document_type=DocumentType.ARTICLE,
            topics=["python", "programming"],
            confidence=0.9,
        )

        tag_dict = tags.to_dict()

        assert tag_dict["document_type"] == "article"
        assert tag_dict["topics"] == ["python", "programming"]
        assert tag_dict["auto_tag_confidence"] == 0.9
        assert tag_dict["language"] == "en"

    def test_from_dict(self):
        """Test creating tags from dictionary."""
        data = {
            "document_type": "research_paper",
            "topics": ["AI", "ML"],
            "language": "en",
            "academic_level": "expert",
            "entities": {"people": ["Hinton"]},
            "keywords": ["deep", "learning"],
            "auto_tag_confidence": 0.95,
        }

        tags = DocumentTags.from_dict(data)

        assert tags.document_type == DocumentType.RESEARCH_PAPER
        assert tags.topics == ["AI", "ML"]
        assert tags.academic_level == AcademicLevel.EXPERT
        assert tags.confidence == 0.95


class TestAutoTagger:
    """Test AutoTagger class."""

    @pytest.fixture
    def tagger(self):
        """Create tagger without LLM (rule-based only)."""
        return AutoTagger()

    @pytest.fixture
    def mock_llm(self):
        """Create mock LLM client."""
        llm = Mock()
        llm.generate = Mock()
        return llm

    def test_tagger_init_without_llm(self):
        """Test tagger initialisation without LLM."""
        tagger = AutoTagger()
        assert tagger.llm_client is None

    def test_tagger_init_with_llm(self, mock_llm):
        """Test tagger initialisation with LLM."""
        tagger = AutoTagger(llm_client=mock_llm)
        assert tagger.llm_client == mock_llm

    def test_tag_empty_document(self, tagger):
        """Test tagging empty document."""
        tags = tagger.tag_document("")

        assert tags.confidence == 0.0
        assert tags.document_type == DocumentType.OTHER

    def test_tag_document_rule_based(self, tagger):
        """Test rule-based document tagging."""
        content = """
        Machine learning is a subset of artificial intelligence. Neural networks
        are a key component of deep learning systems. Convolutional neural networks
        excel at image recognition tasks.
        """

        tags = tagger.tag_document(content)

        # Rule-based should extract some keywords
        assert len(tags.keywords) > 0
        assert tags.confidence == 0.6  # Lower confidence for rule-based
        assert tags.language == "en"

    def test_tag_document_with_filename_pdf(self, tagger):
        """Test tagging with PDF filename."""
        content = """
        Abstract: This paper presents a novel approach to deep learning.
        Introduction: Neural networks have revolutionised machine learning.
        References: [1] Hinton et al. 2006. DOI: 10.1234/example
        """

        tags = tagger.tag_document(content, filename="paper.pdf")

        # Should detect research paper from abstract, references, DOI
        assert tags.document_type == DocumentType.RESEARCH_PAPER

    def test_tag_document_with_filename_book(self, tagger):
        """Test tagging with book indicators."""
        content = """
        Table of Contents
        Chapter 1: Introduction to Machine Learning
        Chapter 2: Neural Networks
        Preface: This book covers the fundamentals...
        """

        tags = tagger.tag_document(content, filename="book.pdf")

        # Should detect book from chapter, preface, table of contents
        assert tags.document_type == DocumentType.BOOK

    def test_tag_document_with_filename_markdown_tutorial(self, tagger):
        """Test tagging markdown tutorial."""
        content = "# Tutorial: Getting Started with Python\nLearn the basics..."

        tags = tagger.tag_document(content, filename="tutorial.md")

        assert tags.document_type == DocumentType.TUTORIAL

    def test_tag_document_with_llm(self, mock_llm):
        """Test document tagging with LLM."""
        tagger = AutoTagger(llm_client=mock_llm)

        # Mock LLM response with valid JSON
        llm_response = json.dumps(
            {
                "document_type": "research_paper",
                "topics": ["machine learning", "neural networks"],
                "language": "en",
                "academic_level": "advanced",
                "entities": {
                    "people": ["Geoffrey Hinton", "Yann LeCun"],
                    "organizations": ["Google", "Meta"],
                    "locations": ["Toronto"],
                },
                "keywords": ["deep", "learning", "neural"],
                "confidence": 0.95,
            }
        )
        mock_llm.generate.return_value = llm_response

        content = "Neural networks paper content..."
        tags = tagger.tag_document(content)

        # Verify LLM was called
        assert mock_llm.generate.called

        # Verify tags from LLM response
        assert tags.document_type == DocumentType.RESEARCH_PAPER
        assert "machine learning" in tags.topics
        assert tags.academic_level == AcademicLevel.ADVANCED
        assert tags.confidence == 0.95
        assert "Geoffrey Hinton" in tags.entities.get("people", [])

    def test_tag_document_llm_with_extra_text(self, mock_llm):
        """Test LLM response with extra text around JSON."""
        tagger = AutoTagger(llm_client=mock_llm)

        # LLM response with text before and after JSON
        llm_response = """Here's the classification:

{
    "document_type": "article",
    "topics": ["python", "programming"],
    "language": "en",
    "academic_level": "intermediate",
    "entities": {"people": [], "organizations": [], "locations": []},
    "keywords": ["python", "code", "programming"],
    "confidence": 0.85
}

That's my analysis."""
        mock_llm.generate.return_value = llm_response

        tags = tagger.tag_document("Python programming article...")

        # Should extract JSON despite extra text
        assert tags.document_type == DocumentType.ARTICLE
        assert "python" in tags.topics
        assert tags.confidence == 0.85

    def test_tag_document_llm_fallback_on_error(self, mock_llm):
        """Test fallback to rule-based when LLM fails."""
        tagger = AutoTagger(llm_client=mock_llm)

        # Make LLM raise exception
        mock_llm.generate.side_effect = Exception("LLM error")

        content = """
        Abstract: Machine learning research paper.
        Introduction: This paper presents...
        """

        tags = tagger.tag_document(content, filename="paper.pdf")

        # Should fallback to rule-based
        assert tags.confidence == 0.6  # Rule-based confidence
        assert tags.document_type == DocumentType.RESEARCH_PAPER  # From filename/content

    def test_extract_topics_with_llm(self, mock_llm):
        """Test topic extraction with LLM."""
        tagger = AutoTagger(llm_client=mock_llm)

        llm_response = json.dumps(
            {"topics": ["machine learning", "neural networks", "deep learning"], "confidence": 0.9}
        )
        mock_llm.generate.return_value = llm_response

        topics = tagger.extract_topics("Neural networks and deep learning...")

        assert len(topics) == 3
        assert "machine learning" in topics

    def test_extract_topics_fallback(self, tagger):
        """Test topic extraction fallback (keyword frequency)."""
        content = """
        Machine learning machine learning machine learning.
        Neural networks neural networks.
        Deep learning.
        """

        topics = tagger.extract_topics(content)

        # Should extract top keywords as topics
        assert len(topics) > 0
        # "machine" and "learning" should be high frequency
        assert any("machine" in t or "learning" in t for t in topics)

    def test_extract_entities_with_llm(self, mock_llm):
        """Test entity extraction with LLM."""
        tagger = AutoTagger(llm_client=mock_llm)

        llm_response = json.dumps(
            {
                "entities": {
                    "people": ["Geoffrey Hinton", "Yann LeCun"],
                    "organizations": ["Google", "Meta"],
                    "locations": ["Toronto", "New York"],
                },
                "confidence": 0.85,
            }
        )
        mock_llm.generate.return_value = llm_response

        entities = tagger.extract_entities("Geoffrey Hinton from Google...")

        assert "Geoffrey Hinton" in entities["people"]
        assert "Google" in entities["organizations"]

    def test_extract_entities_fallback(self, tagger):
        """Test entity extraction fallback (capitalisation)."""
        content = "Geoffrey Hinton from Google and Yann LeCun from Meta in New York."

        entities = tagger.extract_entities(content)

        # Simple capitalisation-based extraction
        assert "people" in entities
        assert "organizations" in entities
        assert "locations" in entities

    def test_extract_keywords(self, tagger):
        """Test keyword extraction."""
        content = """
        Machine learning is important. Machine learning algorithms learn from data.
        Neural networks are machine learning models. Deep learning uses neural networks.
        """

        keywords = tagger._extract_keywords(content, top_n=5)

        # "machine" and "learning" should be top keywords (high frequency)
        assert "machine" in keywords or "learning" in keywords
        # Should not include stopwords
        assert "is" not in keywords
        assert "from" not in keywords

    def test_extract_keywords_excludes_short_words(self, tagger):
        """Test keyword extraction excludes short words."""
        content = "AI ML is to be or not to be that is the question."

        keywords = tagger._extract_keywords(content)

        # Should only include words with 3+ characters
        assert "ai" not in keywords  # 2 chars
        assert "ml" not in keywords  # 2 chars
        assert "is" not in keywords  # Stopword
        assert "question" in keywords  # Valid keyword

    def test_simple_entity_extraction(self, tagger):
        """Test simple capitalisation-based entity extraction."""
        content = "John Smith from Acme Corporation visited New York City yesterday."

        entities = tagger._simple_entity_extraction(content)

        # Should find capitalised words
        all_entities = (
            entities.get("people", [])
            + entities.get("organizations", [])
            + entities.get("locations", [])
        )

        # Should contain some capitalised entities (exact distribution may vary)
        assert len(all_entities) > 0

    def test_extract_json_valid(self, tagger):
        """Test JSON extraction from valid JSON string."""
        json_str = '{"key": "value", "number": 42}'

        result = tagger._extract_json(json_str)

        assert result["key"] == "value"
        assert result["number"] == 42

    def test_extract_json_with_surrounding_text(self, tagger):
        """Test JSON extraction with surrounding text."""
        response = """Here's the result:
{"document_type": "article", "confidence": 0.9}
Hope this helps!"""

        result = tagger._extract_json(response)

        assert result["document_type"] == "article"
        assert result["confidence"] == 0.9

    def test_extract_json_invalid(self, tagger):
        """Test JSON extraction with invalid JSON."""
        invalid_json = "This is not JSON at all"

        with pytest.raises(ValueError, match="No JSON object found"):
            tagger._extract_json(invalid_json)

    def test_extract_json_malformed(self, tagger):
        """Test JSON extraction with malformed JSON."""
        malformed = '{"key": invalid}'

        with pytest.raises(ValueError, match="Invalid JSON"):
            tagger._extract_json(malformed)


class TestConvenienceFunction:
    """Test convenience function."""

    def test_tag_document_function(self):
        """Test tag_document convenience function."""
        content = """
        Abstract: This is a research paper about machine learning.
        References: Various citations.
        """

        tags = tag_document(content, filename="paper.pdf")

        assert isinstance(tags, DocumentTags)
        assert tags.document_type == DocumentType.RESEARCH_PAPER

    def test_tag_document_function_with_llm(self):
        """Test tag_document function with LLM client."""
        mock_llm = Mock()
        mock_llm.generate.return_value = json.dumps(
            {
                "document_type": "tutorial",
                "topics": ["python"],
                "language": "en",
                "academic_level": "introductory",
                "entities": {"people": [], "organizations": [], "locations": []},
                "keywords": ["python", "tutorial"],
                "confidence": 0.8,
            }
        )

        tags = tag_document("Python tutorial content...", llm_client=mock_llm)

        assert tags.document_type == DocumentType.TUTORIAL
        assert mock_llm.generate.called
