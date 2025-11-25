"""Domain-aware retrieval with query expansion and weighted scoring.

Integrates domain detection, terminology expansion, and domain-weighted scoring
to improve retrieval quality for specialized content.

v0.6.3 OPTIMISE-003 Phase 3: Domain-Aware Retrieval
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Optional

from ragged.optimisation.domain_adapter import Domain, DomainDetectionResult, DomainDetector
from ragged.optimisation.terminology import TerminologyManager

if TYPE_CHECKING:
    from ragged.retrieval.retriever import RetrievedChunk, Retriever

logger = logging.getLogger(__name__)


@dataclass
class DomainRetrievalConfig:
    """Configuration for domain-aware retrieval.

    Attributes:
        domain_weighted_scoring: Enable domain-based score boosting
        domain_score_boost: Multiplier for same-domain matches (e.g. 1.2 = 20% boost)
        cross_domain_fallback: Enable fallback to general domain if poor results
        fallback_score_threshold: Min average score to avoid fallback (0.0-1.0)
        expand_queries: Enable domain-specific query expansion
        expand_abbreviations: Expand abbreviations in queries
        max_expansions_per_term: Maximum number of synonym expansions per term
        confidence_threshold: Minimum domain confidence to apply specialization (0.0-1.0)
    """

    domain_weighted_scoring: bool = True
    domain_score_boost: float = 1.2
    cross_domain_fallback: bool = True
    fallback_score_threshold: float = 0.3
    expand_queries: bool = True
    expand_abbreviations: bool = True
    max_expansions_per_term: int = 2
    confidence_threshold: float = 0.6


@dataclass
class DomainRetrievalResult:
    """Result of domain-aware retrieval.

    Attributes:
        chunks: Retrieved chunks with domain-aware scoring
        query_domain: Detected domain for the query
        expanded_query: Query after domain-specific expansion
        applied_boost: Whether domain boost was applied
        fallback_used: Whether cross-domain fallback was used
        original_query: Original query text before expansion
    """

    chunks: list[RetrievedChunk]
    query_domain: DomainDetectionResult
    expanded_query: str
    applied_boost: bool = False
    fallback_used: bool = False
    original_query: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


class DomainAwareRetriever:
    """Retriever with domain adaptation for improved specialized content retrieval.

    Integrates:
    - Domain detection for queries and documents
    - Domain-specific query expansion (abbreviations, synonyms)
    - Domain-weighted scoring (boost same-domain matches)
    - Cross-domain fallback strategies

    Example:
        >>> retriever = DomainAwareRetriever()
        >>> result = retriever.retrieve("K8s ingress config", k=5)
        >>> print(result.expanded_query)  # "Kubernetes ingress configuration..."
        >>> print(result.query_domain.primary_domain)  # Domain.TECHNICAL
        >>> for chunk in result.chunks:
        ...     print(f"{chunk.score:.3f}: {chunk.text[:50]}")
    """

    def __init__(
        self,
        retriever: Optional[Retriever] = None,
        domain_detector: Optional[DomainDetector] = None,
        terminology_manager: Optional[TerminologyManager] = None,
        config: Optional[DomainRetrievalConfig] = None,
    ):
        """Initialize domain-aware retriever.

        Args:
            retriever: Base retriever instance (creates default if None)
            domain_detector: Domain detector instance (creates default if None)
            terminology_manager: Terminology manager instance (creates default if None)
            config: Domain retrieval configuration (uses defaults if None)
        """
        if retriever is None:
            from ragged.retrieval.retriever import Retriever
            retriever = Retriever()

        self.retriever = retriever
        self.domain_detector = domain_detector or DomainDetector()
        self.terminology_manager = terminology_manager or TerminologyManager()
        self.config = config or DomainRetrievalConfig()

        logger.info(
            f"Initialized DomainAwareRetriever "
            f"(weighted_scoring={self.config.domain_weighted_scoring}, "
            f"cross_domain_fallback={self.config.cross_domain_fallback})"
        )

    def retrieve(
        self,
        query: str,
        k: int = 5,
        domain: Optional[Domain] = None,
        filter_metadata: Optional[dict[str, Any]] = None,
        min_score: Optional[float] = None,
    ) -> DomainRetrievalResult:
        """Retrieve chunks with domain-aware expansion and scoring.

        Args:
            query: Query string
            k: Number of chunks to retrieve
            domain: Optional domain override (auto-detects if None)
            filter_metadata: Optional metadata filter for retrieval
            min_score: Optional minimum similarity score threshold

        Returns:
            DomainRetrievalResult with chunks and domain metadata

        Example:
            >>> retriever = DomainAwareRetriever()
            >>> result = retriever.retrieve("MI treatment ASA", k=3, domain=Domain.MEDICAL)
            >>> print(result.expanded_query)
            "MI (Myocardial Infarction) treatment ASA (Acetylsalicylic Acid)"
        """
        original_query = query

        # Step 1: Detect domain (or use provided)
        if domain is None:
            query_domain = self.domain_detector.detect_domain(query)
            logger.debug(
                f"Detected query domain: {query_domain.primary_domain} "
                f"(confidence={query_domain.confidence:.2f})"
            )
        else:
            # Manual domain specification
            query_domain = DomainDetectionResult(
                primary_domain=domain,
                all_domains={domain: 1.0},
                confidence=1.0,
                keywords=[],
                patterns_matched=[],
            )
            logger.debug(f"Using manual domain: {domain}")

        # Step 2: Expand query with domain-specific terminology
        expanded_query = query
        if self.config.expand_queries and query_domain.confidence >= self.config.confidence_threshold:
            expanded_query = self._expand_query(query, query_domain.primary_domain)
            logger.debug(f"Expanded query: '{query}' -> '{expanded_query}'")

        # Step 3: Perform retrieval with expanded query
        chunks = self.retriever.retrieve(
            query=expanded_query,
            k=k,
            filter_metadata=filter_metadata,
            min_score=min_score,
        )

        # Step 4: Apply domain-weighted scoring if enabled
        applied_boost = False
        if self.config.domain_weighted_scoring and query_domain.confidence >= self.config.confidence_threshold:
            chunks = self._apply_domain_weighting(chunks, query_domain.primary_domain)
            applied_boost = True
            logger.debug(f"Applied domain boost ({self.config.domain_score_boost}x) to matching chunks")

        # Step 5: Check if cross-domain fallback needed
        fallback_used = False
        if self.config.cross_domain_fallback and self._should_fallback(chunks):
            logger.info(
                f"Cross-domain fallback triggered (avg_score={self._avg_score(chunks):.3f} "
                f"< threshold={self.config.fallback_score_threshold})"
            )
            chunks = self._fallback_retrieval(original_query, k, filter_metadata, min_score)
            fallback_used = True

        return DomainRetrievalResult(
            chunks=chunks,
            query_domain=query_domain,
            expanded_query=expanded_query,
            applied_boost=applied_boost,
            fallback_used=fallback_used,
            original_query=original_query,
            metadata={
                "domain_confidence": query_domain.confidence,
                "expansion_enabled": self.config.expand_queries,
                "avg_score": self._avg_score(chunks) if chunks else 0.0,
            },
        )

    def _expand_query(self, query: str, domain: Domain) -> str:
        """Expand query with domain-specific terminology.

        Args:
            query: Original query
            domain: Detected domain

        Returns:
            Expanded query with abbreviations and optionally synonyms
        """
        expanded = query

        # Expand abbreviations if enabled
        if self.config.expand_abbreviations:
            expanded = self.terminology_manager.expand_abbreviations(expanded, domain)

        # Could add synonym expansion here if needed (currently disabled for performance)
        # if self.config.expand_synonyms:
        #     expanded = self.terminology_manager.expand_query_with_synonyms(
        #         expanded, domain, max_synonyms=self.config.max_expansions_per_term
        #     )

        return expanded

    def _apply_domain_weighting(
        self, chunks: list[RetrievedChunk], query_domain: Domain
    ) -> list[RetrievedChunk]:
        """Apply domain-weighted scoring boost to matching chunks.

        Chunks with metadata['domain'] matching query_domain receive a score boost.
        Lower scores are better (distance), so we multiply by reciprocal of boost.

        Args:
            chunks: Retrieved chunks
            query_domain: Query domain for matching

        Returns:
            Chunks with adjusted scores (re-sorted)
        """
        boosted_chunks = []

        for chunk in chunks:
            # Check if chunk domain matches query domain
            chunk_domain_str = chunk.metadata.get("domain", "general")

            # Convert string to Domain enum
            try:
                chunk_domain = Domain(chunk_domain_str)
            except ValueError:
                chunk_domain = Domain.GENERAL

            # Apply boost if domains match
            if chunk_domain == query_domain:
                # Lower score is better (distance), so divide to boost
                boosted_score = chunk.score / self.config.domain_score_boost
                logger.debug(
                    f"Boosted chunk {chunk.chunk_id}: "
                    f"{chunk.score:.3f} -> {boosted_score:.3f} (domain match)"
                )
                chunk.score = boosted_score

            boosted_chunks.append(chunk)

        # Re-sort by new scores
        boosted_chunks.sort(key=lambda c: c.score)

        return boosted_chunks

    def _should_fallback(self, chunks: list[RetrievedChunk]) -> bool:
        """Determine if cross-domain fallback is needed.

        Fallback if average score is poor (indicating low quality matches).

        Args:
            chunks: Retrieved chunks

        Returns:
            True if fallback should be used
        """
        if not chunks:
            return True

        avg_score = self._avg_score(chunks)
        return avg_score > self.config.fallback_score_threshold

    def _avg_score(self, chunks: list[RetrievedChunk]) -> float:
        """Calculate average score of chunks.

        Args:
            chunks: Retrieved chunks

        Returns:
            Average score (0.0 if no chunks)
        """
        if not chunks:
            return 0.0
        return sum(c.score for c in chunks) / len(c)

    def _fallback_retrieval(
        self,
        query: str,
        k: int,
        filter_metadata: Optional[dict[str, Any]],
        min_score: Optional[float],
    ) -> list[RetrievedChunk]:
        """Perform fallback retrieval without domain specialization.

        Used when domain-specific retrieval returns poor results.

        Args:
            query: Original query (no expansion)
            k: Number of chunks
            filter_metadata: Metadata filter
            min_score: Score threshold

        Returns:
            Retrieved chunks without domain weighting
        """
        logger.debug("Performing fallback retrieval (no domain specialization)")

        # Retrieve with original query, no domain filtering
        chunks = self.retriever.retrieve(
            query=query,
            k=k * 2,  # Get more results for fallback
            filter_metadata=filter_metadata,
            min_score=min_score,
        )

        # Return top k
        return chunks[:k]

    def retrieve_with_reranking(
        self,
        query: str,
        k: int = 5,
        domain: Optional[Domain] = None,
        rerank_k: int = 20,
        filter_metadata: Optional[dict[str, Any]] = None,
    ) -> DomainRetrievalResult:
        """Retrieve with domain-aware initial retrieval and reranking.

        Retrieves more chunks initially (rerank_k), then reranks and returns top k.

        Args:
            query: Query string
            k: Final number of chunks to return
            domain: Optional domain override
            rerank_k: Number of chunks to retrieve before reranking
            filter_metadata: Optional metadata filter

        Returns:
            DomainRetrievalResult with top k reranked chunks
        """
        # Retrieve more chunks for reranking
        result = self.retrieve(
            query=query,
            k=rerank_k,
            domain=domain,
            filter_metadata=filter_metadata,
        )

        # Apply domain-aware reranking (prioritize domain match + score)
        reranked = self._rerank_by_domain(result.chunks, result.query_domain.primary_domain)

        # Return top k
        result.chunks = reranked[:k]
        result.metadata["reranking_applied"] = True
        result.metadata["rerank_pool_size"] = rerank_k

        return result

    def _rerank_by_domain(
        self, chunks: list[RetrievedChunk], query_domain: Domain
    ) -> list[RetrievedChunk]:
        """Rerank chunks prioritizing domain match and score.

        Sorting key: (domain_mismatch, score) - domain matches come first, then by score.

        Args:
            chunks: Chunks to rerank
            query_domain: Query domain for matching

        Returns:
            Reranked chunks
        """
        def rerank_key(chunk: RetrievedChunk) -> tuple[int, float]:
            chunk_domain_str = chunk.metadata.get("domain", "general")
            try:
                chunk_domain = Domain(chunk_domain_str)
            except ValueError:
                chunk_domain = Domain.GENERAL

            # Priority: domain match (0) vs mismatch (1), then score
            domain_mismatch = 0 if chunk_domain == query_domain else 1
            return (domain_mismatch, chunk.score)

        return sorted(chunks, key=rerank_key)


def get_domain_aware_retriever(
    retriever: Optional[Retriever] = None,
    config: Optional[DomainRetrievalConfig] = None,
) -> DomainAwareRetriever:
    """Get domain-aware retriever instance (convenience factory).

    Args:
        retriever: Optional base retriever instance
        config: Optional configuration

    Returns:
        Configured DomainAwareRetriever
    """
    return DomainAwareRetriever(retriever=retriever, config=config)
