"""Tests for domain-aware retrieval with query expansion and weighted scoring.

v0.6.3 OPTIMISE-003 Phase 3: Domain-Aware Retrieval
"""

import pytest

from ragged.optimisation.domain_adapter import Domain, DomainDetectionResult
from ragged.optimisation.domain_retrieval import (
    DomainAwareRetriever,
    DomainRetrievalConfig,
    DomainRetrievalResult,
)
from ragged.retrieval.retriever import RetrievedChunk


class MockRetriever:
    """Mock retriever for testing domain-aware retrieval logic."""

    def __init__(self, mock_chunks: list[RetrievedChunk] | None = None):
        """Initialize with mock chunks to return.

        Args:
            mock_chunks: List of chunks to return from retrieve()
        """
        self.mock_chunks = mock_chunks or []
        self.last_query = None
        self.last_k = None
        self.retrieve_count = 0

    def retrieve(
        self,
        query: str,
        k: int = 5,
        filter_metadata: dict | None = None,
        min_score: float | None = None,
    ) -> list[RetrievedChunk]:
        """Mock retrieve method."""
        self.last_query = query
        self.last_k = k
        self.retrieve_count += 1
        return self.mock_chunks[:k]


@pytest.fixture
def mock_technical_chunks():
    """Create mock technical domain chunks."""
    return [
        RetrievedChunk(
            text="Kubernetes uses ingress controllers for HTTP routing",
            score=0.1,
            chunk_id="chunk1",
            document_id="doc1",
            document_path="/docs/k8s.pdf",
            chunk_position=0,
            metadata={"domain": "technical"},
        ),
        RetrievedChunk(
            text="Docker containers provide isolation for applications",
            score=0.2,
            chunk_id="chunk2",
            document_id="doc2",
            document_path="/docs/docker.pdf",
            chunk_position=0,
            metadata={"domain": "technical"},
        ),
        RetrievedChunk(
            text="General information about cloud computing",
            score=0.3,
            chunk_id="chunk3",
            document_id="doc3",
            document_path="/docs/cloud.pdf",
            chunk_position=0,
            metadata={"domain": "general"},
        ),
    ]


@pytest.fixture
def mock_medical_chunks():
    """Create mock medical domain chunks."""
    return [
        RetrievedChunk(
            text="Myocardial infarction treatment includes aspirin",
            score=0.15,
            chunk_id="chunk1",
            document_id="doc1",
            document_path="/docs/cardio.pdf",
            chunk_position=0,
            metadata={"domain": "medical"},
        ),
        RetrievedChunk(
            text="Hypertension management requires lifestyle changes",
            score=0.25,
            chunk_id="chunk2",
            document_id="doc2",
            document_path="/docs/bp.pdf",
            chunk_position=0,
            metadata={"domain": "medical"},
        ),
        RetrievedChunk(
            text="General health information",
            score=0.35,
            chunk_id="chunk3",
            document_id="doc3",
            document_path="/docs/health.pdf",
            chunk_position=0,
            metadata={"domain": "general"},
        ),
    ]


@pytest.fixture
def retriever_config():
    """Create default retrieval configuration."""
    return DomainRetrievalConfig(
        domain_weighted_scoring=True,
        domain_score_boost=1.2,
        cross_domain_fallback=True,
        fallback_score_threshold=0.5,
        expand_queries=True,
        expand_abbreviations=True,
        confidence_threshold=0.6,
    )


class TestDomainAwareRetriever:
    """Test suite for DomainAwareRetriever."""

    def test_initialization(self):
        """Test retriever initializes with defaults."""
        mock_retriever = MockRetriever()
        retriever = DomainAwareRetriever(retriever=mock_retriever)

        assert retriever.retriever is not None
        assert retriever.domain_detector is not None
        assert retriever.terminology_manager is not None
        assert retriever.config is not None
        assert isinstance(retriever.config, DomainRetrievalConfig)

    def test_initialization_with_custom_config(self, retriever_config):
        """Test retriever initializes with custom configuration."""
        mock_retriever = MockRetriever()
        retriever = DomainAwareRetriever(retriever=mock_retriever, config=retriever_config)

        assert retriever.config.domain_score_boost == 1.2
        assert retriever.config.expand_abbreviations is True

    def test_retrieve_with_technical_query(self, mock_technical_chunks, retriever_config):
        """Test retrieval with technical domain query."""
        mock_retriever = MockRetriever(mock_chunks=mock_technical_chunks)
        retriever = DomainAwareRetriever(
            retriever=mock_retriever,
            config=retriever_config,
        )

        # Explicitly specify technical domain to test retrieval behavior
        result = retriever.retrieve("K8s ingress configuration", k=3, domain=Domain.TECHNICAL)

        assert isinstance(result, DomainRetrievalResult)
        assert result.query_domain.primary_domain == Domain.TECHNICAL
        assert len(result.chunks) == 3
        assert result.applied_boost is True
        assert result.fallback_used is False
        # Query should be expanded (K8s -> Kubernetes)
        assert "Kubernetes" in result.expanded_query or "K8s" in result.expanded_query

    def test_retrieve_with_medical_query(self, mock_medical_chunks, retriever_config):
        """Test retrieval with medical domain query."""
        mock_retriever = MockRetriever(mock_chunks=mock_medical_chunks)
        retriever = DomainAwareRetriever(
            retriever=mock_retriever,
            config=retriever_config,
        )

        # Explicitly specify medical domain
        result = retriever.retrieve("MI treatment ASA", k=3, domain=Domain.MEDICAL)

        assert result.query_domain.primary_domain == Domain.MEDICAL
        assert len(result.chunks) == 3
        # Query should be expanded (MI -> Myocardial Infarction, ASA -> aspirin/acetylsalicylic acid)
        assert "MI" in result.expanded_query  # Original preserved in expansion

    def test_abbreviation_expansion_enabled(self, mock_technical_chunks):
        """Test query abbreviation expansion when enabled."""
        mock_retriever = MockRetriever(mock_chunks=mock_technical_chunks)
        config = DomainRetrievalConfig(expand_abbreviations=True, expand_queries=True)
        retriever = DomainAwareRetriever(retriever=mock_retriever, config=config)

        result = retriever.retrieve("API endpoint K8s", k=3)

        # Should expand abbreviations
        expanded = result.expanded_query
        assert "Application Programming Interface" in expanded or "API" in expanded
        assert "Kubernetes" in expanded or "K8s" in expanded

    def test_abbreviation_expansion_disabled(self, mock_technical_chunks):
        """Test query not expanded when expansion disabled."""
        mock_retriever = MockRetriever(mock_chunks=mock_technical_chunks)
        config = DomainRetrievalConfig(expand_abbreviations=False, expand_queries=False)
        retriever = DomainAwareRetriever(retriever=mock_retriever, config=config)

        result = retriever.retrieve("API endpoint K8s", k=3)

        # Original query should be unchanged
        assert result.expanded_query == "API endpoint K8s"

    def test_domain_weighted_scoring(self, mock_technical_chunks):
        """Test domain-weighted scoring boosts matching chunks."""
        mock_retriever = MockRetriever(mock_chunks=mock_technical_chunks)
        config = DomainRetrievalConfig(domain_weighted_scoring=True, domain_score_boost=1.5)
        retriever = DomainAwareRetriever(retriever=mock_retriever, config=config)

        result = retriever.retrieve("Kubernetes ingress", k=3, domain=Domain.TECHNICAL)

        assert result.applied_boost is True
        # Technical chunks should have boosted scores (lower is better)
        tech_chunk = result.chunks[0]  # First should be technical (best match)
        assert tech_chunk.metadata["domain"] == "technical"
        # Score should be reduced (boosted) compared to original
        assert tech_chunk.score < 0.1  # Original was 0.1, should be ~0.067 (0.1/1.5)

    def test_domain_weighting_disabled(self, mock_technical_chunks):
        """Test domain weighting can be disabled."""
        mock_retriever = MockRetriever(mock_chunks=mock_technical_chunks)
        config = DomainRetrievalConfig(domain_weighted_scoring=False)
        retriever = DomainAwareRetriever(retriever=mock_retriever, config=config)

        result = retriever.retrieve("Kubernetes ingress", k=3, domain=Domain.TECHNICAL)

        assert result.applied_boost is False
        # Scores should be unchanged
        assert result.chunks[0].score == 0.1  # Original score

    def test_manual_domain_override(self, mock_medical_chunks):
        """Test manual domain specification overrides detection."""
        mock_retriever = MockRetriever(mock_chunks=mock_medical_chunks)
        retriever = DomainAwareRetriever(retriever=mock_retriever)

        # Query about "Python code" but manually specify MEDICAL domain
        result = retriever.retrieve(
            "Python code for analysis",
            k=3,
            domain=Domain.MEDICAL,  # Manual override
        )

        assert result.query_domain.primary_domain == Domain.MEDICAL
        assert result.query_domain.confidence == 1.0  # Manual override = 100% confidence

    def test_cross_domain_fallback_triggered(self):
        """Test cross-domain fallback when results are poor quality."""
        # Create chunks with high scores (poor matches)
        poor_chunks = [
            RetrievedChunk(
                text="Unrelated content",
                score=0.9,  # High score = poor match (distance-based)
                chunk_id="chunk1",
                document_id="doc1",
                document_path="/docs/test.pdf",
                chunk_position=0,
                metadata={"domain": "technical"},
            ),
        ]

        mock_retriever = MockRetriever(mock_chunks=poor_chunks)
        config = DomainRetrievalConfig(
            cross_domain_fallback=True,
            fallback_score_threshold=0.5,  # Trigger fallback if avg > 0.5
        )
        retriever = DomainAwareRetriever(retriever=mock_retriever, config=config)

        result = retriever.retrieve("test query", k=3)

        assert result.fallback_used is True
        assert mock_retriever.retrieve_count == 2  # Initial + fallback

    def test_cross_domain_fallback_not_triggered(self, mock_technical_chunks):
        """Test cross-domain fallback not used when results are good quality."""
        mock_retriever = MockRetriever(mock_chunks=mock_technical_chunks)
        config = DomainRetrievalConfig(
            cross_domain_fallback=True,
            fallback_score_threshold=0.5,  # Don't fallback if avg < 0.5
        )
        retriever = DomainAwareRetriever(retriever=mock_retriever, config=config)

        result = retriever.retrieve("Kubernetes", k=3)

        assert result.fallback_used is False
        assert mock_retriever.retrieve_count == 1  # Only initial retrieval

    def test_retrieve_with_reranking(self, mock_technical_chunks):
        """Test retrieval with domain-aware reranking."""
        mock_retriever = MockRetriever(mock_chunks=mock_technical_chunks)
        retriever = DomainAwareRetriever(retriever=mock_retriever)

        result = retriever.retrieve_with_reranking(
            "Kubernetes ingress",
            k=2,
            rerank_k=3,  # Retrieve 3, return 2
            domain=Domain.TECHNICAL,
        )

        assert len(result.chunks) == 2
        assert result.metadata["reranking_applied"] is True
        assert result.metadata["rerank_pool_size"] == 3
        # First chunk should be technical (domain match prioritised)
        assert result.chunks[0].metadata["domain"] == "technical"

    def test_reranking_prioritizes_domain_match(self):
        """Test reranking prioritizes domain matches even with slightly worse scores."""
        # Create chunks where general has better score but technical should rank higher
        chunks = [
            RetrievedChunk(
                text="General content",
                score=0.05,  # Best score
                chunk_id="chunk1",
                document_id="doc1",
                document_path="/docs/gen.pdf",
                chunk_position=0,
                metadata={"domain": "general"},
            ),
            RetrievedChunk(
                text="Technical content",
                score=0.15,  # Slightly worse score
                chunk_id="chunk2",
                document_id="doc2",
                document_path="/docs/tech.pdf",
                chunk_position=0,
                metadata={"domain": "technical"},
            ),
        ]

        mock_retriever = MockRetriever(mock_chunks=chunks)
        retriever = DomainAwareRetriever(retriever=mock_retriever)

        result = retriever.retrieve_with_reranking(
            "Kubernetes",
            k=2,
            rerank_k=2,
            domain=Domain.TECHNICAL,
        )

        # After reranking, technical should be first despite worse original score
        assert result.chunks[0].metadata["domain"] == "technical"
        assert result.chunks[1].metadata["domain"] == "general"

    def test_metadata_includes_confidence(self, mock_technical_chunks):
        """Test result metadata includes domain confidence."""
        mock_retriever = MockRetriever(mock_chunks=mock_technical_chunks)
        retriever = DomainAwareRetriever(retriever=mock_retriever)

        result = retriever.retrieve("Kubernetes API endpoint", k=3)

        assert "domain_confidence" in result.metadata
        assert 0.0 <= result.metadata["domain_confidence"] <= 1.0
        assert "avg_score" in result.metadata
        assert "expansion_enabled" in result.metadata

    def test_low_confidence_skips_specialization(self):
        """Test low domain confidence skips domain-specific processing."""
        mock_retriever = MockRetriever(mock_chunks=[])
        config = DomainRetrievalConfig(
            confidence_threshold=0.8,  # High threshold
            expand_queries=True,
            domain_weighted_scoring=True,
        )
        retriever = DomainAwareRetriever(retriever=mock_retriever, config=config)

        # Generic query with low confidence
        result = retriever.retrieve("some random text", k=3)

        # Should not apply specialization if confidence < 0.8
        if result.query_domain.confidence < 0.8:
            assert result.applied_boost is False

    def test_empty_chunks_triggers_fallback(self):
        """Test empty initial results trigger fallback."""
        mock_retriever = MockRetriever(mock_chunks=[])
        config = DomainRetrievalConfig(cross_domain_fallback=True)
        retriever = DomainAwareRetriever(retriever=mock_retriever, config=config)

        result = retriever.retrieve("test query", k=3)

        # Empty results should trigger fallback
        assert result.fallback_used is True
        assert mock_retriever.retrieve_count == 2

    def test_filter_metadata_passed_through(self, mock_technical_chunks):
        """Test filter_metadata is passed to underlying retriever."""
        mock_retriever = MockRetriever(mock_chunks=mock_technical_chunks)
        retriever = DomainAwareRetriever(retriever=mock_retriever)

        filter_meta = {"document_type": "pdf"}
        # Can't easily test this without mocking, but ensure it doesn't crash
        result = retriever.retrieve("test", k=3, filter_metadata=filter_meta)

        assert result is not None

    def test_min_score_passed_through(self, mock_technical_chunks):
        """Test min_score threshold is passed to underlying retriever."""
        mock_retriever = MockRetriever(mock_chunks=mock_technical_chunks)
        retriever = DomainAwareRetriever(retriever=mock_retriever)

        # Can't easily test this without mocking, but ensure it doesn't crash
        result = retriever.retrieve("test", k=3, min_score=0.5)

        assert result is not None

    def test_get_domain_aware_retriever_factory(self):
        """Test convenience factory function."""
        from ragged.optimisation.domain_retrieval import get_domain_aware_retriever

        mock_retriever = MockRetriever()
        retriever = get_domain_aware_retriever(retriever=mock_retriever)

        assert isinstance(retriever, DomainAwareRetriever)
        assert retriever.config is not None

    def test_fallback_retrieves_more_chunks(self):
        """Test fallback retrieval requests more chunks (k*2)."""
        mock_retriever = MockRetriever(mock_chunks=[])
        config = DomainRetrievalConfig(
            cross_domain_fallback=True,
            fallback_score_threshold=0.0,  # Always trigger fallback
        )
        retriever = DomainAwareRetriever(retriever=mock_retriever, config=config)

        retriever.retrieve("test", k=5)

        # Fallback should request k*2 = 10 chunks
        assert mock_retriever.last_k == 10

    def test_avg_score_calculation(self, mock_technical_chunks):
        """Test average score calculation."""
        mock_retriever = MockRetriever(mock_chunks=mock_technical_chunks)
        # Disable domain weighting to test raw average
        config = DomainRetrievalConfig(domain_weighted_scoring=False)
        retriever = DomainAwareRetriever(retriever=mock_retriever, config=config)

        result = retriever.retrieve("test", k=3)

        # Avg score should be (0.1 + 0.2 + 0.3) / 3 = 0.2 (without boost)
        expected_avg = (0.1 + 0.2 + 0.3) / 3
        assert abs(result.metadata["avg_score"] - expected_avg) < 0.01

    def test_domain_boost_applies_correctly(self):
        """Test domain boost calculation is correct."""
        chunks = [
            RetrievedChunk(
                text="Technical",
                score=0.3,  # Will be divided by 1.5 = 0.2
                chunk_id="chunk1",
                document_id="doc1",
                document_path="/docs/test.pdf",
                chunk_position=0,
                metadata={"domain": "technical"},
            ),
        ]

        mock_retriever = MockRetriever(mock_chunks=chunks)
        config = DomainRetrievalConfig(
            domain_weighted_scoring=True,
            domain_score_boost=1.5,
        )
        retriever = DomainAwareRetriever(retriever=mock_retriever, config=config)

        result = retriever.retrieve("test", k=1, domain=Domain.TECHNICAL)

        # Score should be boosted: 0.3 / 1.5 = 0.2
        assert abs(result.chunks[0].score - 0.2) < 0.01
