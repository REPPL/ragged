"""Smart query suggestions and refinement.

v0.3.12: Intelligent query refinement to improve retrieval quality.
"""

import re
from dataclasses import dataclass
from typing import List, Optional

from src.utils.logging import get_logger

logger = get_logger(__name__)


@dataclass
class QuerySuggestions:
    """Query suggestions and refinements."""

    original: str
    corrections: List[str]
    refinements: List[str]
    related: List[str]
    quality_score: float


class QuerySuggester:
    """Intelligent query refinement and suggestions."""

    # Common spelling mistakes in tech/research queries
    COMMON_CORRECTIONS = {
        "wat": "what",
        "wut": "what",
        "wats": "what's",
        "whats": "what's",
        "hows": "how's",
        "r": "are",
        "u": "you",
        "ur": "your",
        "thier": "their",
        "recieve": "receive",
        "occured": "occurred",
        "seperate": "separate",
        "definately": "definitely",
        "algoritm": "algorithm",
        "machien": "machine",
        "learnign": "learning",
        "retreive": "retrieve",
        "retreival": "retrieval",
    }

    # Question words for query quality
    QUESTION_WORDS = [
        "what",
        "how",
        "why",
        "when",
        "where",
        "who",
        "which",
        "can",
        "could",
        "would",
        "should",
        "does",
        "is",
        "are",
    ]

    def __init__(self, llm_client: Optional[object] = None):
        """Initialise query suggester.

        Args:
            llm_client: Optional LLM client for advanced suggestions
        """
        self.llm_client = llm_client

    def suggest(self, query: str) -> QuerySuggestions:
        """Generate query suggestions.

        Args:
            query: Original query

        Returns:
            QuerySuggestions with corrections, refinements, and related queries
        """
        suggestions = QuerySuggestions(
            original=query,
            corrections=[],
            refinements=[],
            related=[],
            quality_score=0.0,
        )

        # 1. Spelling correction
        corrections = self._check_spelling(query)
        if corrections:
            suggestions.corrections = corrections[:3]  # Top 3

        # 2. Query refinement (if vague)
        if self._is_vague(query):
            refined = self._refine_query(query)
            suggestions.refinements = refined[:3]  # Top 3

        # 3. Related queries
        related = self._generate_related(query)
        suggestions.related = related[:4]  # Top 4

        # 4. Quality score
        suggestions.quality_score = self._score_query(query)

        return suggestions

    def _check_spelling(self, query: str) -> List[str]:
        """Check and correct spelling.

        Args:
            query: Query to check

        Returns:
            List of spelling corrections
        """
        corrections = []
        words = query.lower().split()

        # Check for common corrections
        corrected_query = query
        for word in words:
            if word in self.COMMON_CORRECTIONS:
                corrected = self.COMMON_CORRECTIONS[word]
                corrected_query = corrected_query.replace(word, corrected)

        # Only add if different
        if corrected_query.lower() != query.lower():
            corrections.append(corrected_query)

        return corrections

    def _is_vague(self, query: str) -> bool:
        """Detect vague queries.

        Args:
            query: Query to check

        Returns:
            True if query appears vague
        """
        # Heuristics for vagueness
        word_count = len(query.split())
        has_question_word = any(
            q in query.lower() for q in self.QUESTION_WORDS
        )

        # Vague if too short or no question structure
        return word_count < 3 or not has_question_word

    def _refine_query(self, query: str) -> List[str]:
        """Refine vague query into specific questions.

        Args:
            query: Vague query to refine

        Returns:
            List of refined queries
        """
        refinements = []

        # If just keywords, suggest question formats
        if not any(q in query.lower() for q in self.QUESTION_WORDS):
            # Common refinement patterns
            refinements.append(f"What is {query}?")
            refinements.append(f"How does {query} work?")
            refinements.append(f"What are the main concepts in {query}?")

        # If has question word but too short, suggest expansions
        elif len(query.split()) < 5:
            refinements.append(f"{query} in detail?")
            refinements.append(f"{query} with examples?")

        return refinements

    def _generate_related(self, query: str) -> List[str]:
        """Generate related queries.

        Args:
            query: Original query

        Returns:
            List of related queries
        """
        related = []

        # Extract topic from query
        topic_match = re.search(r"(?:what|how|why|when|where|who)\s+(?:is|are|does|do)\s+(.+)", query, re.IGNORECASE)

        if topic_match:
            topic = topic_match.group(1).strip("?")

            # Generate related questions
            related.append(f"What are the benefits of {topic}?")
            related.append(f"What are the challenges with {topic}?")
            related.append(f"How is {topic} used in practice?")
            related.append(f"What are alternatives to {topic}?")
        else:
            # Generic related queries
            related.append("What are the key concepts?")
            related.append("What are common use cases?")
            related.append("What are best practices?")
            related.append("What are the limitations?")

        return related

    def _score_query(self, query: str) -> float:
        """Score query quality (0-1).

        Args:
            query: Query to score

        Returns:
            Quality score between 0.0 and 1.0
        """
        score = 0.0

        # Has question word (+0.3)
        if any(q in query.lower() for q in self.QUESTION_WORDS):
            score += 0.3

        # Sufficient length (+0.3)
        if len(query.split()) >= 5:
            score += 0.3
        elif len(query.split()) >= 3:
            score += 0.15

        # No obvious spelling errors (+0.2)
        if not self._check_spelling(query):
            score += 0.2

        # Specific/structured (+0.2)
        if "?" in query:
            score += 0.1
        if any(word.istitle() or word.isupper() for word in query.split()):
            score += 0.1

        return min(score, 1.0)


def create_query_suggester(llm_client: Optional[object] = None) -> QuerySuggester:
    """Create query suggester instance.

    Args:
        llm_client: Optional LLM client for advanced suggestions

    Returns:
        QuerySuggester instance
    """
    return QuerySuggester(llm_client=llm_client)


# Export
__all__ = ["QuerySuggester", "QuerySuggestions", "create_query_suggester"]
