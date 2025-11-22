"""
Query decomposition for complex multi-part queries.

Breaks complex queries into sub-queries, retrieves for each, then merges results.
"""

import hashlib
from dataclasses import dataclass

from src.config.settings import get_settings
from src.generation.ollama_client import OllamaClient
from src.utils.logging import get_logger

logger = get_logger(__name__)


DECOMPOSITION_PROMPT = """You are a query analysis expert. Your task is to break down complex queries into simpler sub-queries.

Given a complex query, identify if it contains multiple distinct questions or aspects. If so, split it into 2-4 focused sub-queries. If the query is already simple, return just the original query.

Rules:
1. Each sub-query should be self-contained and answerable independently
2. Sub-queries should cover all aspects of the original query
3. Keep sub-queries concise and focused
4. Return ONLY the sub-queries, one per line
5. If the query is simple (single question), return just the original query

Examples:

Query: "What methods did the authors use and how do they compare to prior work?"
Sub-queries:
What methods did the authors use?
What was the prior work in this area?
How do the authors' methods compare to prior work?

Query: "What is machine learning?"
Sub-queries:
What is machine learning?

Query: "Explain the dataset, model architecture, and evaluation metrics used in the paper."
Sub-queries:
What dataset was used in the paper?
What was the model architecture?
What evaluation metrics were used?

Now decompose this query:
{query}

Sub-queries:"""


SYSTEM_PROMPT = "You are a helpful assistant that decomposes complex queries into simpler sub-queries."


@dataclass
class DecomposedQuery:
    """Result of query decomposition."""

    original_query: str
    sub_queries: list[str]
    was_decomposed: bool  # False if query was simple and not split

    def __repr__(self) -> str:
        """String representation."""
        if self.was_decomposed:
            return f"DecomposedQuery(original='{self.original_query[:50]}...', sub_queries={len(self.sub_queries)})"
        else:
            return f"DecomposedQuery(simple_query='{self.original_query[:50]}...')"


class QueryDecomposer:
    """
    Decomposes complex queries into simpler sub-queries.

    Uses LLM to identify multiple aspects or questions within a complex query,
    enabling better retrieval through focused sub-query search.
    """

    def __init__(
        self,
        ollama_client: OllamaClient | None = None,
        enable_caching: bool = True,
    ):
        """
        Initialise query decomposer.

        Args:
            ollama_client: Ollama client for LLM calls (creates default if None)
            enable_caching: Whether to cache decomposition results
        """
        self.ollama_client = ollama_client or OllamaClient()
        self.enable_caching = enable_caching
        self._cache: dict = {}  # Simple in-memory cache

        settings = get_settings()
        self.max_sub_queries = 4  # Limit to prevent explosion
        self.min_query_length = 20  # Don't decompose very short queries

        logger.info("QueryDecomposer initialised with caching=%s", enable_caching)

    def decompose(self, query: str) -> DecomposedQuery:
        """
        Decompose a query into sub-queries.

        Args:
            query: Original query string

        Returns:
            DecomposedQuery with original and sub-queries

        Example:
            >>> decomposer = QueryDecomposer()
            >>> result = decomposer.decompose("What methods were used and how do they compare?")
            >>> print(result.sub_queries)
            ['What methods were used?', 'How do the methods compare?']
        """
        query = query.strip()

        # Check cache
        if self.enable_caching:
            cache_key = self._get_cache_key(query)
            if cache_key in self._cache:
                logger.debug("Cache hit for query decomposition")
                return self._cache[cache_key]

        # Simple queries don't need decomposition
        if len(query) < self.min_query_length or not self._is_complex_query(query):
            logger.debug("Query is simple, skipping decomposition")
            result = DecomposedQuery(
                original_query=query,
                sub_queries=[query],
                was_decomposed=False,
            )
            if self.enable_caching:
                self._cache[cache_key] = result
            return result

        # Decompose using LLM
        try:
            sub_queries = self._decompose_with_llm(query)

            # Validate results
            if not sub_queries or len(sub_queries) > self.max_sub_queries:
                logger.warning("Invalid decomposition result, falling back to original query")
                sub_queries = [query]
                was_decomposed = False
            else:
                was_decomposed = len(sub_queries) > 1

            result = DecomposedQuery(
                original_query=query,
                sub_queries=sub_queries,
                was_decomposed=was_decomposed,
            )

            # Cache result
            if self.enable_caching:
                self._cache[cache_key] = result

            logger.info("Decomposed query into %d sub-queries", len(sub_queries))
            return result

        except Exception as e:
            logger.error(f"Decomposition failed: {e}", exc_info=True)
            # Fallback to original query
            result = DecomposedQuery(
                original_query=query,
                sub_queries=[query],
                was_decomposed=False,
            )
            return result

    def _decompose_with_llm(self, query: str) -> list[str]:
        """
        Decompose query using LLM.

        Args:
            query: Query to decompose

        Returns:
            List of sub-queries
        """
        prompt = DECOMPOSITION_PROMPT.format(query=query)

        response = self.ollama_client.generate(
            prompt=prompt,
            system=SYSTEM_PROMPT,
            temperature=0.3,  # Lower temperature for more consistent decomposition
        )

        # Parse response (one sub-query per line)
        sub_queries = [
            line.strip()
            for line in response.strip().split("\n")
            if line.strip() and not line.strip().startswith("#")
        ]

        # Remove duplicates while preserving order
        seen = set()
        unique_sub_queries = []
        for sq in sub_queries:
            sq_lower = sq.lower()
            if sq_lower not in seen:
                seen.add(sq_lower)
                unique_sub_queries.append(sq)

        return unique_sub_queries[:self.max_sub_queries]

    def _is_complex_query(self, query: str) -> bool:
        """
        Heuristic to detect if query is complex.

        Args:
            query: Query string

        Returns:
            True if query appears complex
        """
        # Complex indicators
        complex_words = ["and", "compare", "difference", "versus", "vs", "between", "both"]
        query_lower = query.lower()

        # Check for multiple questions
        if query_lower.count("?") > 1:
            return True

        # Check for complex connecting words
        if any(word in query_lower for word in complex_words):
            return True

        # Check for multiple clauses (commas)
        if query.count(",") >= 2:
            return True

        return False

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
        """Clear the decomposition cache."""
        self._cache.clear()
        logger.debug("Decomposition cache cleared")
