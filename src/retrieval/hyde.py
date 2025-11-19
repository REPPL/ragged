"""
HyDE (Hypothetical Document Embeddings) for enhanced retrieval.

Generates a hypothetical answer to the query, embeds it, and uses it for retrieval.
Rationale: Answers are semantically closer to document chunks than questions.
"""

import hashlib
from dataclasses import dataclass
from typing import Any, List, Optional

from src.config.settings import get_settings
from src.generation.ollama_client import OllamaClient
from src.utils.logging import get_logger

logger = get_logger(__name__)


HYDE_PROMPT = """Generate a concise, factual answer to the following question. Write as if you are answering from an authoritative source document.

Do not include:
- Phrases like "I don't know" or "I cannot answer"
- Meta-commentary about the question
- Questions back to the user

Write 2-3 sentences that directly answer the question in a factual, document-like style.

Question: {query}

Answer:"""


SYSTEM_PROMPT = "You are an expert that generates concise, factual answers in a document style."


@dataclass
class HypotheticalDocument:
    """Generated hypothetical document for a query."""

    query: str
    hypothetical_text: str
    confidence: float  # Estimated quality (0-1)
    used_for_retrieval: bool  # Whether this was actually used

    def __repr__(self) -> str:
        """String representation."""
        preview = self.hypothetical_text[:50] + "..." if len(self.hypothetical_text) > 50 else self.hypothetical_text
        return f"HypotheticalDocument(confidence={self.confidence:.2f}, text='{preview}')"


class HyDEGenerator:
    """
    Generates hypothetical documents for queries using HyDE technique.

    HyDE improves retrieval by generating a hypothetical answer and using its
    embedding for search, as answers are semantically closer to document chunks
    than questions.
    """

    def __init__(
        self,
        ollama_client: Optional[OllamaClient] = None,
        enable_caching: bool = True,
        confidence_threshold: float = 0.5,
    ):
        """
        Initialise HyDE generator.

        Args:
            ollama_client: Ollama client for LLM calls (creates default if None)
            enable_caching: Whether to cache generated hypothetical documents
            confidence_threshold: Minimum confidence to use hypothetical document (0-1)
        """
        self.ollama_client = ollama_client or OllamaClient()
        self.enable_caching = enable_caching
        self.confidence_threshold = confidence_threshold
        self._cache: dict = {}  # Simple in-memory cache

        settings = get_settings()

        logger.info(
            "HyDEGenerator initialised with caching=%s, confidence_threshold=%.2f",
            enable_caching,
            confidence_threshold
        )

    def generate(self, query: str) -> HypotheticalDocument:
        """
        Generate a hypothetical document for a query.

        Args:
            query: Query string

        Returns:
            HypotheticalDocument with generated text and metadata

        Example:
            >>> hyde = HyDEGenerator()
            >>> doc = hyde.generate("What is machine learning?")
            >>> print(doc.hypothetical_text)
            'Machine learning is a subset of artificial intelligence...'
        """
        query = query.strip()

        # Check cache
        if self.enable_caching:
            cache_key = self._get_cache_key(query)
            if cache_key in self._cache:
                logger.debug("Cache hit for HyDE generation")
                return self._cache[cache_key]

        try:
            # Generate hypothetical document
            hypothetical_text = self._generate_with_llm(query)

            # Validate and score confidence
            confidence = self._estimate_confidence(query, hypothetical_text)

            result = HypotheticalDocument(
                query=query,
                hypothetical_text=hypothetical_text,
                confidence=confidence,
                used_for_retrieval=(confidence >= self.confidence_threshold),
            )

            # Cache result
            if self.enable_caching:
                self._cache[cache_key] = result

            if result.used_for_retrieval:
                logger.info("Generated HyDE document (confidence=%.2f)", confidence)
            else:
                logger.warning(
                    "HyDE document confidence too low (%.2f < %.2f), will use original query",
                    confidence,
                    self.confidence_threshold
                )

            return result

        except Exception as e:
            logger.error(f"HyDE generation failed: {e}", exc_info=True)
            # Return low-confidence result to trigger fallback
            return HypotheticalDocument(
                query=query,
                hypothetical_text="",
                confidence=0.0,
                used_for_retrieval=False,
            )

    def _generate_with_llm(self, query: str) -> str:
        """
        Generate hypothetical document using LLM.

        Args:
            query: Query to generate document for

        Returns:
            Generated hypothetical document text
        """
        prompt = HYDE_PROMPT.format(query=query)

        response = self.ollama_client.generate(
            prompt=prompt,
            system=SYSTEM_PROMPT,
            temperature=0.5,  # Moderate temperature for varied but relevant answers
            max_tokens=150,  # Keep hypothetical docs concise
        )

        return response.strip()

    def _estimate_confidence(self, query: str, hypothetical_text: str) -> float:
        """
        Estimate confidence in the generated hypothetical document.

        Uses heuristics to detect low-quality generations (hallucinations, etc.)

        Args:
            query: Original query
            hypothetical_text: Generated hypothetical document

        Returns:
            Confidence score (0-1)
        """
        if not hypothetical_text:
            return 0.0

        # Heuristics for detecting low-quality generations
        text_lower = hypothetical_text.lower()

        # Red flags (hallucination indicators)
        red_flags = [
            "i don't know",
            "i cannot",
            "i'm not sure",
            "there is no information",
            "unable to answer",
            "i apologize",
            "as an ai",
        ]

        if any(flag in text_lower for flag in red_flags):
            logger.debug("HyDE generation contains red flags")
            return 0.3  # Low confidence

        # Check minimum length (too short is suspicious)
        if len(hypothetical_text.split()) < 10:
            logger.debug("HyDE generation too short")
            return 0.5

        # Check maximum length (too long might be rambling)
        if len(hypothetical_text.split()) > 200:
            logger.debug("HyDE generation too long")
            return 0.6

        # Check for question marks (shouldn't be asking questions back)
        if "?" in hypothetical_text:
            logger.debug("HyDE generation contains questions")
            return 0.7

        # Default: reasonable confidence
        return 0.85

    def _get_cache_key(self, query: str) -> str:
        """
        Generate cache key for query.

        Args:
            query: Query string

        Returns:
            Cache key (hash)
        """
        return hashlib.md5(query.lower().encode()).hexdigest()

    def clear_cache(self) -> None:
        """Clear the HyDE cache."""
        self._cache.clear()
        logger.debug("HyDE cache cleared")

    def should_use_hyde(self, query: str, hypothetical_doc: HypotheticalDocument) -> bool:
        """
        Determine if HyDE document should be used for retrieval.

        Args:
            query: Original query
            hypothetical_doc: Generated hypothetical document

        Returns:
            True if HyDE document should be used, False to fallback to original query
        """
        return hypothetical_doc.used_for_retrieval and hypothetical_doc.confidence >= self.confidence_threshold
