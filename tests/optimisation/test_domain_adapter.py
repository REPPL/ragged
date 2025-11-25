"""Tests for domain adaptation and detection.

v0.6.3 OPTIMISE-003: Domain Adaptation
"""

import pytest

from ragged.optimisation.domain_adapter import (
    Domain,
    DomainAdapter,
    DomainDetector,
    get_domain_adapter,
)


class TestDomainDetector:
    """Test domain detection from text content."""

    @pytest.fixture
    def detector(self):
        """Create domain detector instance."""
        return DomainDetector()

    def test_technical_domain_detection(self, detector):
        """Verify technical domain detection from programming content."""
        text = """
        This function implements a REST API endpoint using FastAPI.
        The endpoint accepts JSON payloads and returns a response.
        We use async/await for better performance and Docker for deployment.
        The database connection uses PostgreSQL with SQLAlchemy ORM.
        """

        result = detector.detect_domain(text)

        assert result.primary_domain == Domain.TECHNICAL
        assert result.confidence > 0.5
        assert "function" in [ind.lower() for ind in result.indicators]
        assert Domain.TECHNICAL in result.domain_scores
        assert result.domain_scores[Domain.TECHNICAL] > 0

    def test_medical_domain_detection(self, detector):
        """Verify medical domain detection from healthcare content."""
        text = """
        Patient presents with hypertension and diabetes mellitus type 2.
        Prescribed medication includes metformin 500mg twice daily and
        lisinopril 10mg once daily. Blood pressure measured at 140/90 mmHg.
        Follow-up appointment scheduled in 3 months for monitoring.
        """

        result = detector.detect_domain(text)

        assert result.primary_domain == Domain.MEDICAL
        assert result.confidence > 0.5
        assert any("patient" in ind.lower() or "medication" in ind.lower()
                  for ind in result.indicators)

    def test_legal_domain_detection(self, detector):
        """Verify legal domain detection from legal content."""
        text = """
        Pursuant to 42 U.S.C. § 1983, the plaintiff alleges a violation
        of civil rights. The defendant failed to provide due process as
        required by the Fourteenth Amendment. The court has jurisdiction
        under federal question jurisdiction. Damages sought include
        compensatory and punitive damages for breach of contract.
        """

        result = detector.detect_domain(text)

        assert result.primary_domain == Domain.LEGAL
        assert result.confidence > 0.5
        assert any("plaintiff" in ind.lower() or "defendant" in ind.lower()
                  for ind in result.indicators)

    def test_academic_domain_detection(self, detector):
        """Verify academic domain detection from research content."""
        text = """
        This study examines the correlation between social media usage
        and mental health outcomes. The methodology employed a mixed-methods
        approach with n=500 participants. Results indicate a statistically
        significant relationship (p < 0.05). Smith et al. (2023) found similar
        patterns in their research. Further analysis is needed to establish
        causation versus correlation.
        """

        result = detector.detect_domain(text)

        assert result.primary_domain == Domain.ACADEMIC
        assert result.confidence > 0.5
        assert any("study" in ind.lower() or "research" in ind.lower()
                  for ind in result.indicators)

    def test_general_domain_for_mixed_content(self, detector):
        """Verify GENERAL domain for mixed or everyday content."""
        text = """
        Today I went to the grocery store and bought some fresh vegetables.
        The weather was nice, so I decided to go for a walk in the park.
        Later, I met my friend for coffee and we discussed our weekend plans.
        """

        result = detector.detect_domain(text)

        assert result.primary_domain == Domain.GENERAL
        assert result.confidence >= 0.5

    def test_empty_text_returns_general(self, detector):
        """Verify empty text returns GENERAL domain."""
        result = detector.detect_domain("")

        assert result.primary_domain == Domain.GENERAL
        assert result.confidence == 1.0
        assert result.indicators == []

    def test_domain_scores_normalized(self, detector):
        """Verify domain scores are properly normalized."""
        text = "Python function API REST database SQL"

        result = detector.detect_domain(text)

        # All scores should be between 0 and 1
        for score in result.domain_scores.values():
            assert 0 <= score <= 1.0

    def test_confidence_calculation(self, detector):
        """Verify confidence reflects score separation."""
        # Strong technical signal
        technical_text = """
        function async await Python JavaScript API REST endpoint
        Docker Kubernetes Git GitHub PostgreSQL MongoDB Redis
        """

        result = detector.detect_domain(technical_text)

        # High confidence when one domain dominates
        assert result.confidence > 0.6
        assert result.primary_domain == Domain.TECHNICAL

    def test_multi_domain_content_picks_strongest(self, detector):
        """Verify multi-domain content selects strongest domain."""
        # Mix of technical and medical, but more technical
        text = """
        The healthcare API provides endpoints for patient data management.
        We use Python and FastAPI to implement the REST API with JWT authentication.
        The database stores medical records using PostgreSQL with encrypted fields.
        Functions handle CRUD operations for patient records.
        """

        result = detector.detect_domain(text)

        # Should detect technical as primary (more technical terms)
        assert result.primary_domain == Domain.TECHNICAL
        # But medical should also have a score
        assert Domain.MEDICAL in result.domain_scores
        assert result.domain_scores[Domain.MEDICAL] > 0

    def test_batch_detection(self, detector):
        """Verify batch domain detection."""
        texts = [
            "Python function API endpoint",
            "Patient diagnosed with hypertension",
            "Plaintiff filed lawsuit under statute",
            "Research study with p-value analysis",
        ]

        results = detector.detect_domains_batch(texts)

        assert len(results) == 4
        assert results[0].primary_domain == Domain.TECHNICAL
        assert results[1].primary_domain == Domain.MEDICAL
        assert results[2].primary_domain == Domain.LEGAL
        assert results[3].primary_domain == Domain.ACADEMIC

    def test_indicators_limited_count(self, detector):
        """Verify indicator count is limited."""
        # Lots of technical keywords
        text = " ".join(["Python function API endpoint"] * 20)

        result = detector.detect_domain(text)

        # Should limit indicators even with many matches
        assert len(result.indicators) <= 10


class TestDomainAdapter:
    """Test domain adaptation and query handling."""

    @pytest.fixture
    def adapter(self):
        """Create domain adapter instance."""
        return DomainAdapter()

    def test_tag_document_domain(self, adapter):
        """Verify document domain tagging."""
        content = """
        This API endpoint handles user authentication using JWT tokens.
        The function validates credentials and returns a session token.
        """

        metadata = adapter.tag_document_domain(content)

        assert "domain" in metadata
        assert metadata["domain"] == Domain.TECHNICAL.value
        assert "domain_confidence" in metadata
        assert isinstance(metadata["domain_confidence"], float)
        assert "domain_indicators" in metadata
        assert isinstance(metadata["domain_indicators"], str)

    def test_adapt_query_detects_domain(self, adapter):
        """Verify query adaptation detects domain."""
        query = "How do I implement a REST API endpoint in Python?"

        adapted = adapter.adapt_query_for_domain(query)

        # For Phase 1, query is unchanged but domain is detected
        assert adapted == query

    def test_adapt_query_with_explicit_domain(self, adapter):
        """Verify query adaptation with explicit domain hint."""
        query = "What causes high blood pressure?"

        adapted = adapter.adapt_query_for_domain(query, domain=Domain.MEDICAL)

        # For Phase 1, query is unchanged
        assert adapted == query

    def test_domain_weight_multipliers(self, adapter):
        """Verify domain-specific weight multipliers."""
        # Technical domain gets higher weight for exact matching
        assert adapter.get_domain_weight_multiplier(Domain.TECHNICAL) == 1.2

        # Medical and legal get moderate boost
        assert adapter.get_domain_weight_multiplier(Domain.MEDICAL) == 1.1
        assert adapter.get_domain_weight_multiplier(Domain.LEGAL) == 1.1

        # Academic gets small boost
        assert adapter.get_domain_weight_multiplier(Domain.ACADEMIC) == 1.05

        # General uses default
        assert adapter.get_domain_weight_multiplier(Domain.GENERAL) == 1.0

    def test_singleton_adapter(self):
        """Verify global adapter singleton."""
        adapter1 = get_domain_adapter()
        adapter2 = get_domain_adapter()

        assert adapter1 is adapter2


class TestRealWorldScenarios:
    """Test domain detection with real-world content examples."""

    @pytest.fixture
    def detector(self):
        """Create domain detector instance."""
        return DomainDetector()

    def test_github_readme_technical(self, detector):
        """Verify GitHub README detected as technical."""
        readme = """
        # My Project

        A Python library for building REST APIs with FastAPI.

        ## Installation
        ```bash
        pip install myproject
        ```

        ## Usage
        ```python
        from myproject import create_app
        app = create_app()
        ```

        ## Features
        - JWT authentication
        - PostgreSQL database integration
        - Docker deployment support
        - Kubernetes configuration
        """

        result = detector.detect_domain(readme)
        assert result.primary_domain == Domain.TECHNICAL

    def test_medical_journal_abstract(self, detector):
        """Verify medical journal abstract detected as medical/academic."""
        abstract = """
        Background: Hypertension affects millions worldwide.
        Methods: A randomized controlled trial with 500 patients.
        Treatment group received antihypertensive medication (lisinopril 10mg).
        Results: Significant reduction in blood pressure (p<0.001).
        Conclusion: Early intervention improves patient outcomes.
        """

        result = detector.detect_domain(abstract)
        # Could be medical or academic, both are valid
        assert result.primary_domain in (Domain.MEDICAL, Domain.ACADEMIC)

    def test_legal_contract_clause(self, detector):
        """Verify legal contract detected as legal."""
        contract = """
        TERMS AND CONDITIONS

        1. The parties hereby agree to the following provisions:
        2. Liability is limited to direct damages only.
        3. In the event of breach, the non-breaching party may seek
           injunctive relief and damages.
        4. This agreement shall be governed by the laws of California.
        5. Disputes shall be resolved through binding arbitration.
        """

        result = detector.detect_domain(contract)
        assert result.primary_domain == Domain.LEGAL

    def test_research_paper_methods(self, detector):
        """Verify research paper detected as academic."""
        methods = """
        Participants: 300 university students (150 male, 150 female).
        Methodology: Cross-sectional survey with Likert scale responses.
        Analysis: Statistical analysis using SPSS. Pearson correlation
        coefficients calculated to examine relationships between variables.
        Hypothesis testing conducted with alpha = 0.05 significance level.
        Results validated against prior studies (Johnson et al., 2022).
        """

        result = detector.detect_domain(methods)
        assert result.primary_domain == Domain.ACADEMIC
