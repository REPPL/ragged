"""Topic extraction for behaviour learning (v0.4.7).

Extracts topics from user queries and documents for interest profiling.

Phase 1: Keyword-based extraction with frequency analysis
Future: NLP/LLM-based extraction (v0.5.x)

Privacy: All extraction performed locally, no external API calls.
"""

import re
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Set

from ragged.utils.logging import get_logger

logger = get_logger(__name__)


@dataclass
class Topic:
    """Extracted topic with confidence score.

    Attributes:
        name: Topic name (normalized)
        confidence: Confidence score (0.0-1.0)
        raw_text: Original text before normalisation
        extracted_at: Extraction timestamp
    """

    name: str
    confidence: float
    raw_text: str = ""
    extracted_at: datetime = field(default_factory=datetime.now)

    def __post_init__(self):
        """Validate topic data."""
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError(f"Confidence must be 0.0-1.0, got {self.confidence}")
        if not self.name:
            raise ValueError("Topic name cannot be empty")
        if not self.raw_text:
            self.raw_text = self.name


# Default stop words (common English words to filter out)
DEFAULT_STOP_WORDS = {
    # Articles, determiners
    "a", "an", "the",
    # Pronouns
    "i", "you", "he", "she", "it", "we", "they", "me", "him", "her", "us", "them",
    "my", "your", "his", "her", "its", "our", "their",
    # Prepositions
    "in", "on", "at", "to", "for", "of", "with", "from", "by", "about",
    "as", "into", "through", "during", "before", "after", "above", "below",
    # Conjunctions
    "and", "but", "or", "nor", "so", "yet",
    # Auxiliary verbs
    "is", "are", "was", "were", "am", "be", "been", "being",
    "have", "has", "had", "do", "does", "did",
    "will", "would", "should", "could", "may", "might", "can",
    # Question words
    "what", "when", "where", "why", "how", "which", "who", "whom", "whose",
    # Common verbs (low semantic value)
    "get", "got", "make", "made", "take", "give", "go", "come",
    # Other common words
    "this", "that", "these", "those", "there", "here",
    "then", "than", "very", "just", "also", "only", "even",
    "some", "any", "all", "each", "every", "both", "few", "more", "most",
    "other", "such", "no", "not", "too", "so",
}


class TopicExtractor:
    """Extract topics from text for behaviour learning.

    Uses keyword-based extraction with stop word filtering and
    multi-word phrase detection.

    Example:
        >>> extractor = TopicExtractor(min_confidence=0.3)
        >>> topics = extractor.extract_topics("What are the latest RAG techniques?")
        >>> topics
        [Topic(name="RAG techniques", confidence=0.95),
         Topic(name="RAG", confidence=0.90)]
    """

    def __init__(
        self,
        min_topic_length: int = 3,
        max_topics_per_query: int = 10,
        min_confidence: float = 0.3,
        stop_words: Set[str] | None = None,
        enable_phrases: bool = True,
    ):
        """Initialise topic extractor.

        Args:
            min_topic_length: Minimum characters for valid topic
            max_topics_per_query: Maximum topics to extract per query
            min_confidence: Minimum confidence threshold (0.0-1.0)
            stop_words: Custom stop words set (uses default if None)
            enable_phrases: Enable multi-word phrase detection
        """
        self.min_topic_length = min_topic_length
        self.max_topics_per_query = max_topics_per_query
        self.min_confidence = min_confidence
        self.stop_words = stop_words if stop_words is not None else DEFAULT_STOP_WORDS
        self.enable_phrases = enable_phrases

        logger.debug(
            f"TopicExtractor initialised: min_length={min_topic_length}, "
            f"max_topics={max_topics_per_query}, min_confidence={min_confidence}"
        )

    def extract_topics(self, query: str) -> List[Topic]:
        """Extract topics from query text.

        Extraction process:
        1. Extract capitalised terms (potential acronyms/proper nouns)
        2. Extract multi-word phrases if enabled
        3. Extract individual keywords
        4. Score and rank topics
        5. Filter by confidence threshold

        Args:
            query: User query text

        Returns:
            List of extracted topics sorted by confidence (highest first)

        Example:
            >>> extractor = TopicExtractor()
            >>> topics = extractor.extract_topics(
            ...     "What are the latest RAG techniques for improving retrieval accuracy?"
            ... )
            >>> [t.name for t in topics]
            ['RAG', 'retrieval accuracy', 'techniques']
        """
        if not query or not query.strip():
            return []

        topics = []

        # Phase 1: Extract capitalised terms (likely acronyms or proper nouns)
        capitalised_topics = self._extract_capitalised_terms(query)
        topics.extend(capitalised_topics)

        # Phase 2: Extract multi-word phrases
        if self.enable_phrases:
            phrase_topics = self._extract_phrases(query)
            topics.extend(phrase_topics)

        # Phase 3: Extract individual keywords
        keyword_topics = self._extract_keywords(query)
        topics.extend(keyword_topics)

        # Deduplicate and merge (keep highest confidence)
        topics = self._deduplicate_topics(topics)

        # Sort by confidence (highest first)
        topics.sort(key=lambda t: t.confidence, reverse=True)

        # Filter by minimum confidence
        topics = [t for t in topics if t.confidence >= self.min_confidence]

        # Limit to max topics
        topics = topics[: self.max_topics_per_query]

        logger.debug(f"Extracted {len(topics)} topics from query: {query[:50]}...")
        return topics

    def _extract_capitalised_terms(self, text: str) -> List[Topic]:
        """Extract capitalised terms (likely acronyms or proper nouns).

        Args:
            text: Input text

        Returns:
            List of topics from capitalised terms
        """
        # Find consecutive capitalised letters (2+ chars)
        pattern = r"\b[A-Z]{2,}\b"
        matches = re.findall(pattern, text)

        topics = []
        for match in matches:
            if len(match) >= self.min_topic_length:
                # Acronyms get high confidence (0.9-0.95 based on length)
                confidence = 0.9 + min(len(match) / 20, 0.05)
                topics.append(Topic(name=match, confidence=confidence, raw_text=match))

        return topics

    def _extract_phrases(self, text: str) -> List[Topic]:
        """Extract multi-word phrases (2-3 word combinations).

        Args:
            text: Input text

        Returns:
            List of topics from phrases
        """
        # Normalise text
        normalised = text.lower()
        normalised = re.sub(r"[^\w\s]", " ", normalised)  # Remove punctuation
        words = normalised.split()

        topics = []

        # Extract 2-word phrases
        for i in range(len(words) - 1):
            word1, word2 = words[i], words[i + 1]

            # Skip if either word is a stop word
            if word1 in self.stop_words or word2 in self.stop_words:
                continue

            phrase = f"{word1} {word2}"
            if len(phrase) >= self.min_topic_length:
                # 2-word phrases get medium-high confidence (0.7-0.85)
                confidence = min(0.7 + (len(phrase) / 100), 0.85)
                topics.append(Topic(name=phrase, confidence=confidence, raw_text=phrase))

        # Extract 3-word phrases (higher confidence for specificity)
        for i in range(len(words) - 2):
            word1, word2, word3 = words[i], words[i + 1], words[i + 2]

            # Skip if any word is a stop word
            if (
                word1 in self.stop_words
                or word2 in self.stop_words
                or word3 in self.stop_words
            ):
                continue

            phrase = f"{word1} {word2} {word3}"
            if len(phrase) >= self.min_topic_length:
                # 3-word phrases get high confidence (0.8-0.9)
                confidence = min(0.8 + (len(phrase) / 100), 0.9)
                topics.append(Topic(name=phrase, confidence=confidence, raw_text=phrase))

        return topics

    def _extract_keywords(self, text: str) -> List[Topic]:
        """Extract individual keywords.

        Args:
            text: Input text

        Returns:
            List of topics from keywords
        """
        # Normalise text
        normalised = text.lower()
        normalised = re.sub(r"[^\w\s]", " ", normalised)  # Remove punctuation
        words = normalised.split()

        topics = []

        for word in words:
            # Skip stop words and short words
            if word in self.stop_words or len(word) < self.min_topic_length:
                continue

            # Keywords get lower confidence than phrases (0.5-0.7)
            # Longer words tend to be more specific, so higher confidence
            confidence = 0.5 + min(len(word) / 20, 0.2)

            topics.append(Topic(name=word, confidence=confidence, raw_text=word))

        return topics

    def _deduplicate_topics(self, topics: List[Topic]) -> List[Topic]:
        """Deduplicate topics, keeping highest confidence for each unique name.

        Args:
            topics: List of topics (may contain duplicates)

        Returns:
            Deduplicated list of topics
        """
        topic_dict = {}

        for topic in topics:
            # Normalise topic name for comparison
            normalised_name = topic.name.lower().strip()

            if (
                normalised_name not in topic_dict
                or topic.confidence > topic_dict[normalised_name].confidence
            ):
                # Keep this topic (first occurrence or higher confidence)
                topic_dict[normalised_name] = topic

        return list(topic_dict.values())

    def extract_from_documents(
        self, doc_ids: List[str], doc_texts: List[str] | None = None
    ) -> List[Topic]:
        """Extract topics from retrieved documents.

        Note: In this implementation, we extract from document IDs only.
        Future versions may use document content if provided.

        Args:
            doc_ids: Document IDs that were retrieved
            doc_texts: Optional document text content (future use)

        Returns:
            List of topics extracted from documents

        Example:
            >>> extractor = TopicExtractor()
            >>> topics = extractor.extract_from_documents(
            ...     ["RAG_paper_2023.pdf", "retrieval_optimization.md"]
            ... )
            >>> [t.name for t in topics]
            ['RAG', 'retrieval', 'optimisation']
        """
        if not doc_ids:
            return []

        all_topics = []

        # Extract topics from document IDs (filenames often contain topic keywords)
        for doc_id in doc_ids:
            # Remove file extensions and common separators
            cleaned_id = re.sub(r"\.(pdf|md|txt|docx?)$", "", doc_id, flags=re.IGNORECASE)
            cleaned_id = re.sub(r"[_\-]", " ", cleaned_id)

            # Extract topics from cleaned ID
            topics = self.extract_topics(cleaned_id)

            # Lower confidence for topics from document IDs (0.4-0.6)
            for topic in topics:
                topic.confidence *= 0.6  # Reduce confidence

            all_topics.extend(topics)

        # Deduplicate and sort
        all_topics = self._deduplicate_topics(all_topics)
        all_topics.sort(key=lambda t: t.confidence, reverse=True)

        # Filter and limit
        all_topics = [t for t in all_topics if t.confidence >= self.min_confidence]
        all_topics = all_topics[: self.max_topics_per_query]

        logger.debug(f"Extracted {len(all_topics)} topics from {len(doc_ids)} documents")
        return all_topics
