"""
Automatic document tagging and classification.

v0.3.7e: LLM-based classification with rule-based fallback.
"""

import json
import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from src.utils.logging import get_logger

logger = get_logger(__name__)


class DocumentType(Enum):
    """Document type classification."""

    RESEARCH_PAPER = "research_paper"
    BOOK = "book"
    ARTICLE = "article"
    TECHNICAL_DOC = "technical_doc"
    BLOG_POST = "blog_post"
    NEWS = "news"
    TUTORIAL = "tutorial"
    REFERENCE = "reference"
    OTHER = "other"


class AcademicLevel(Enum):
    """Academic level classification."""

    INTRODUCTORY = "introductory"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"
    NOT_APPLICABLE = "not_applicable"


@dataclass
class DocumentTags:
    """Auto-generated document tags and metadata."""

    document_type: DocumentType = DocumentType.OTHER
    topics: list[str] = field(default_factory=list)
    language: str = "en"
    academic_level: AcademicLevel = AcademicLevel.NOT_APPLICABLE
    entities: dict[str, list[str]] = field(default_factory=dict)
    keywords: list[str] = field(default_factory=list)
    confidence: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        """
        Convert tags to dictionary for storage.

        Returns:
            Dictionary representation suitable for metadata storage
        """
        return {
            "document_type": self.document_type.value,
            "topics": self.topics,
            "language": self.language,
            "academic_level": self.academic_level.value,
            "entities": self.entities,
            "keywords": self.keywords,
            "auto_tag_confidence": self.confidence,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "DocumentTags":
        """
        Create DocumentTags from dictionary.

        Args:
            data: Dictionary with tag data

        Returns:
            DocumentTags instance
        """
        return cls(
            document_type=DocumentType(data.get("document_type", "other")),
            topics=data.get("topics", []),
            language=data.get("language", "en"),
            academic_level=AcademicLevel(
                data.get("academic_level", "not_applicable")
            ),
            entities=data.get("entities", {}),
            keywords=data.get("keywords", []),
            confidence=data.get("auto_tag_confidence", 0.0),
        )


class AutoTagger:
    """
    Automatic document tagger using LLM-based classification.

    Uses structured JSON prompts for reliable classification with
    rule-based fallback for offline operation.
    """

    # Classification prompt for LLM
    CLASSIFICATION_PROMPT = """Analyze this document excerpt and classify it. Respond with valid JSON only.

Document excerpt (first 1000 characters):
{excerpt}

Provide classification in this exact JSON format:
{{
    "document_type": "research_paper|book|article|technical_doc|blog_post|news|tutorial|reference|other",
    "topics": ["topic1", "topic2", "topic3"],
    "language": "en",
    "academic_level": "introductory|intermediate|advanced|expert|not_applicable",
    "entities": {{
        "people": ["Person 1", "Person 2"],
        "organizations": ["Org 1", "Org 2"],
        "locations": ["Location 1"]
    }},
    "keywords": ["keyword1", "keyword2", "keyword3"],
    "confidence": 0.95
}}

Rules:
- document_type: Choose the most specific type that matches
- topics: 3-5 main topics covered in the document
- language: ISO 639-1 language code (e.g., "en", "es", "fr")
- academic_level: Target audience expertise level
- entities: Named entities found in the text
- keywords: 3-5 most important keywords
- confidence: Your confidence in this classification (0.0-1.0)

Respond with ONLY the JSON object, no explanation."""

    # Topic extraction prompt
    TOPIC_EXTRACTION_PROMPT = """Extract the main topics from this document excerpt. Respond with valid JSON only.

Document excerpt:
{excerpt}

Provide topics in this exact JSON format:
{{
    "topics": ["topic1", "topic2", "topic3"],
    "confidence": 0.9
}}

Rules:
- Extract 3-5 main topics
- Use general topic names, not specific details
- confidence: Your confidence in topic extraction (0.0-1.0)

Respond with ONLY the JSON object, no explanation."""

    # Entity extraction prompt
    ENTITY_EXTRACTION_PROMPT = """Extract named entities from this document excerpt. Respond with valid JSON only.

Document excerpt:
{excerpt}

Provide entities in this exact JSON format:
{{
    "entities": {{
        "people": ["Person 1", "Person 2"],
        "organizations": ["Org 1", "Org 2"],
        "locations": ["Location 1"]
    }},
    "confidence": 0.85
}}

Rules:
- people: Names of individuals
- organizations: Companies, institutions, groups
- locations: Countries, cities, places
- confidence: Your confidence in entity extraction (0.0-1.0)

Respond with ONLY the JSON object, no explanation."""

    def __init__(self, llm_client: Any | None = None):
        """
        Initialise auto-tagger.

        Args:
            llm_client: Optional LLM client for classification.
                       If None, uses rule-based fallback.
        """
        self.llm_client = llm_client

    def tag_document(
        self,
        content: str,
        filename: str | None = None,
    ) -> DocumentTags:
        """
        Automatically tag and classify a document.

        Args:
            content: Document text content
            filename: Optional filename for additional hints

        Returns:
            DocumentTags with classification results

        Example:
            >>> tagger = AutoTagger(llm_client)
            >>> tags = tagger.tag_document(content, "paper.pdf")
            >>> print(f"Type: {tags.document_type.value}")
            >>> print(f"Topics: {tags.topics}")
        """
        # Extract excerpt for analysis
        excerpt = content[:1000].strip()

        if not excerpt:
            logger.warning("Empty content provided for tagging")
            return DocumentTags(confidence=0.0)

        # Try LLM-based classification first
        if self.llm_client:
            try:
                return self._llm_based_classification(excerpt)
            except Exception as e:
                logger.warning(f"LLM classification failed: {e}, falling back to rules")

        # Fallback to rule-based tagging
        return self._rule_based_tagging(content, filename)

    def _llm_based_classification(self, excerpt: str) -> DocumentTags:
        """
        Classify document using LLM.

        Args:
            excerpt: Document excerpt to classify

        Returns:
            DocumentTags from LLM classification

        Raises:
            Exception: If LLM call fails or returns invalid JSON
        """
        # Generate classification prompt
        prompt = self.CLASSIFICATION_PROMPT.format(excerpt=excerpt)

        # Call LLM
        response = self.llm_client.generate(prompt)

        # Extract JSON from response
        classification = self._extract_json(response)

        # Convert to DocumentTags
        return DocumentTags(
            document_type=DocumentType(classification.get("document_type", "other")),
            topics=classification.get("topics", []),
            language=classification.get("language", "en"),
            academic_level=AcademicLevel(
                classification.get("academic_level", "not_applicable")
            ),
            entities=classification.get("entities", {}),
            keywords=classification.get("keywords", []),
            confidence=classification.get("confidence", 0.0),
        )

    def extract_topics(self, content: str) -> list[str]:
        """
        Extract main topics from document.

        Args:
            content: Document text content

        Returns:
            List of topic strings

        Example:
            >>> tagger = AutoTagger(llm_client)
            >>> topics = tagger.extract_topics(content)
            >>> print(topics)  # ["machine learning", "neural networks"]
        """
        excerpt = content[:1000].strip()

        if self.llm_client:
            try:
                prompt = self.TOPIC_EXTRACTION_PROMPT.format(excerpt=excerpt)
                response = self.llm_client.generate(prompt)
                result = self._extract_json(response)
                return result.get("topics", [])
            except Exception as e:
                logger.warning(f"LLM topic extraction failed: {e}")

        # Fallback: simple keyword frequency
        return self._extract_keywords(content)[:5]

    def extract_entities(self, content: str) -> dict[str, list[str]]:
        """
        Extract named entities from document.

        Args:
            content: Document text content

        Returns:
            Dictionary with entity types and lists of entities

        Example:
            >>> tagger = AutoTagger(llm_client)
            >>> entities = tagger.extract_entities(content)
            >>> print(entities["people"])  # ["Geoffrey Hinton", "Yann LeCun"]
        """
        excerpt = content[:1000].strip()

        if self.llm_client:
            try:
                prompt = self.ENTITY_EXTRACTION_PROMPT.format(excerpt=excerpt)
                response = self.llm_client.generate(prompt)
                result = self._extract_json(response)
                return result.get("entities", {})
            except Exception as e:
                logger.warning(f"LLM entity extraction failed: {e}")

        # Fallback: simple capitalized word detection
        return self._simple_entity_extraction(content)

    def _rule_based_tagging(
        self,
        content: str,
        filename: str | None = None,
    ) -> DocumentTags:
        """
        Simple rule-based tagging fallback.

        Args:
            content: Document text content
            filename: Optional filename for hints

        Returns:
            DocumentTags from rule-based classification
        """
        tags = DocumentTags(confidence=0.6)  # Lower confidence for rule-based

        # Detect document type from filename
        if filename:
            filename_lower = filename.lower()

            if filename_lower.endswith(".pdf"):
                # Check for book indicators first (more specific)
                if any(
                    keyword in content.lower()
                    for keyword in ["chapter", "preface", "table of contents"]
                ):
                    tags.document_type = DocumentType.BOOK
                # Check for research paper indicators
                elif any(
                    keyword in content.lower()
                    for keyword in [
                        "abstract",
                        "introduction",
                        "references",
                        "doi:",
                        "arxiv",
                    ]
                ):
                    tags.document_type = DocumentType.RESEARCH_PAPER
            elif filename_lower.endswith((".md", ".markdown")):
                # Markdown files often tutorials or blogs
                if "tutorial" in filename_lower or "guide" in filename_lower:
                    tags.document_type = DocumentType.TUTORIAL
                else:
                    tags.document_type = DocumentType.ARTICLE

        # Extract keywords using frequency analysis
        tags.keywords = self._extract_keywords(content)[:5]
        tags.topics = tags.keywords[:3]  # Use top keywords as topics

        # Simple entity extraction
        tags.entities = self._simple_entity_extraction(content)

        # Detect language (simple check for now)
        tags.language = "en"  # Default to English

        return tags

    def _extract_json(self, response: str) -> dict[str, Any]:
        """
        Extract JSON object from LLM response.

        Handles cases where LLM adds extra text around the JSON.

        Args:
            response: LLM response text

        Returns:
            Parsed JSON dictionary

        Raises:
            ValueError: If no valid JSON found
        """
        # Try to parse entire response as JSON first
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            pass

        # Look for JSON object in response
        # Find content between first { and last }
        start = response.find("{")
        end = response.rfind("}") + 1

        if start == -1 or end == 0:
            raise ValueError("No JSON object found in response")

        json_str = response[start:end]

        try:
            return json.loads(json_str)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in response: {e}")

    def _extract_keywords(self, content: str, top_n: int = 10) -> list[str]:
        """
        Extract keywords using simple frequency analysis.

        Args:
            content: Document text
            top_n: Number of top keywords to return

        Returns:
            List of keyword strings
        """
        # Simple word frequency (exclude common words)
        stopwords = {
            "the",
            "be",
            "to",
            "of",
            "and",
            "a",
            "in",
            "that",
            "have",
            "i",
            "it",
            "for",
            "not",
            "on",
            "with",
            "he",
            "as",
            "you",
            "do",
            "at",
            "this",
            "but",
            "his",
            "by",
            "from",
            "they",
            "we",
            "say",
            "her",
            "she",
            "or",
            "an",
            "will",
            "my",
            "one",
            "all",
            "would",
            "there",
            "their",
        }

        # Extract words (alphanumeric, 3+ chars)
        words = re.findall(r"\b[a-z]{3,}\b", content.lower())

        # Count frequencies
        word_freq: dict[str, int] = {}
        for word in words:
            if word not in stopwords:
                word_freq[word] = word_freq.get(word, 0) + 1

        # Sort by frequency
        sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)

        return [word for word, _ in sorted_words[:top_n]]

    def _simple_entity_extraction(self, content: str) -> dict[str, list[str]]:
        """
        Simple entity extraction using capitalization patterns.

        Args:
            content: Document text

        Returns:
            Dictionary with entity types and lists
        """
        # Find capitalized words (potential entities)
        # This is a very simple heuristic
        capitalized = re.findall(r"\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b", content)

        # Remove duplicates, keep first 5
        unique_entities = list(dict.fromkeys(capitalized))[:5]

        return {
            "people": unique_entities[:2],
            "organizations": unique_entities[2:4],
            "locations": unique_entities[4:5],
        }


# Convenience function for quick tagging
def tag_document(
    content: str,
    filename: str | None = None,
    llm_client: Any | None = None,
) -> DocumentTags:
    """
    Quickly tag a document.

    Args:
        content: Document text content
        filename: Optional filename
        llm_client: Optional LLM client

    Returns:
        DocumentTags with classification results

    Example:
        >>> tags = tag_document(content, "paper.pdf", llm_client)
        >>> print(tags.document_type.value)
    """
    tagger = AutoTagger(llm_client)
    return tagger.tag_document(content, filename)
