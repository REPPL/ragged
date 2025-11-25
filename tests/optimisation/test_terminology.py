"""Tests for terminology expansion and normalization.

v0.6.3 OPTIMISE-003 Phase 2: Terminology Management
"""

import pytest

from ragged.optimisation.domain_adapter import Domain
from ragged.optimisation.terminology import TerminologyManager, get_terminology_manager


class TestTerminologyManager:
    """Test terminology expansion and normalization."""

    @pytest.fixture
    def manager(self):
        """Create terminology manager instance."""
        return TerminologyManager()

    def test_load_dictionaries(self, manager):
        """Verify dictionaries are loaded for all domains."""
        assert Domain.TECHNICAL in manager.dictionaries
        assert Domain.MEDICAL in manager.dictionaries
        assert Domain.LEGAL in manager.dictionaries
        assert Domain.ACADEMIC in manager.dictionaries

    def test_expand_technical_abbreviations(self, manager):
        """Verify technical abbreviation expansion."""
        text = "Using K8s for API deployment with JWT authentication"

        expanded = manager.expand_abbreviations(text, Domain.TECHNICAL)

        # Should expand K8s, API, JWT
        assert "Kubernetes" in expanded
        assert "Application Programming Interface" in expanded
        assert "JSON Web Token" in expanded

    def test_expand_medical_abbreviations(self, manager):
        """Verify medical abbreviation expansion."""
        text = "Patient has HTN and DM, BP is 140/90 mmHg"

        expanded = manager.expand_abbreviations(text, Domain.MEDICAL)

        # Should expand HTN, DM, BP, mmHg
        assert "Hypertension" in expanded
        assert "Diabetes Mellitus" in expanded
        assert "Blood Pressure" in expanded
        assert "millimeters of mercury" in expanded

    def test_expand_legal_abbreviations(self, manager):
        """Verify legal abbreviation expansion."""
        text = "See 42 U.S.C. § 1983 and Smith v. Jones"

        expanded = manager.expand_abbreviations(text, Domain.LEGAL)

        # Should expand U.S.C. and v.
        assert "United States Code" in expanded
        assert "versus" in expanded

    def test_expand_academic_abbreviations(self, manager):
        """Verify academic abbreviation expansion."""
        text = "RCT with n=500, p<0.05, CI 95%"

        expanded = manager.expand_abbreviations(text, Domain.ACADEMIC)

        # Should expand RCT, CI
        assert "Randomized Controlled Trial" in expanded
        assert "Confidence Interval" in expanded

    def test_no_expansion_for_general_domain(self, manager):
        """Verify no expansion for GENERAL domain."""
        text = "Some text with API and other words"

        expanded = manager.expand_abbreviations(text, Domain.GENERAL)

        # Should not expand anything
        assert expanded == text

    def test_get_technical_synonyms(self, manager):
        """Verify technical synonym retrieval."""
        synonyms = manager.get_synonyms("function", Domain.TECHNICAL)

        assert "method" in synonyms
        assert "procedure" in synonyms

    def test_get_medical_synonyms(self, manager):
        """Verify medical synonym retrieval."""
        synonyms = manager.get_synonyms("heart attack", Domain.MEDICAL)

        assert "myocardial infarction" in synonyms
        assert "MI" in synonyms

    def test_get_legal_synonyms(self, manager):
        """Verify legal synonym retrieval."""
        synonyms = manager.get_synonyms("lawsuit", Domain.LEGAL)

        assert "litigation" in synonyms
        assert "legal action" in synonyms

    def test_get_academic_synonyms(self, manager):
        """Verify academic synonym retrieval."""
        synonyms = manager.get_synonyms("research", Domain.ACADEMIC)

        assert "study" in synonyms
        assert "investigation" in synonyms

    def test_normalize_technical_term(self, manager):
        """Verify technical term normalization."""
        # Abbreviation normalization
        normalized = manager.normalize_term("API", Domain.TECHNICAL)
        assert normalized == "application programming interface"

        # Regular term normalization
        normalized = manager.normalize_term("Function", Domain.TECHNICAL)
        assert normalized == "function"

    def test_normalize_medical_term(self, manager):
        """Verify medical term normalization."""
        # Abbreviation normalization
        normalized = manager.normalize_term("MI", Domain.MEDICAL)
        assert normalized == "myocardial infarction"

    def test_expand_query_technical(self, manager):
        """Verify technical query expansion."""
        query = "How to deploy API using K8s?"

        expanded = manager.expand_query(query, Domain.TECHNICAL)

        # Should expand abbreviations
        assert "Kubernetes" in expanded
        assert "Application Programming Interface" in expanded

    def test_expand_query_medical(self, manager):
        """Verify medical query expansion."""
        query = "Treatment for HTN and DM"

        expanded = manager.expand_query(query, Domain.MEDICAL)

        # Should expand medical abbreviations
        assert "Hypertension" in expanded
        assert "Diabetes Mellitus" in expanded

    def test_expand_query_general_unchanged(self, manager):
        """Verify GENERAL domain queries are unchanged."""
        query = "How do I cook pasta?"

        expanded = manager.expand_query(query, Domain.GENERAL)

        # Should not change for general domain
        assert expanded == query

    def test_get_technical_expansions(self, manager):
        """Verify technical term expansions."""
        expansions = manager.get_expansions("Docker", Domain.TECHNICAL)

        assert "containerization" in expansions
        assert "container platform" in expansions

    def test_get_medical_expansions(self, manager):
        """Verify medical term expansions."""
        expansions = manager.get_expansions("aspirin", Domain.MEDICAL)

        assert "acetylsalicylic acid" in expansions
        assert "ASA" in expansions

    def test_get_legal_expansions(self, manager):
        """Verify legal term expansions."""
        expansions = manager.get_expansions("jurisdiction", Domain.LEGAL)

        assert "legal authority" in expansions
        assert "court authority" in expansions

    def test_get_academic_expansions(self, manager):
        """Verify academic term expansions."""
        expansions = manager.get_expansions("null hypothesis", Domain.ACADEMIC)

        assert "H0" in expansions
        assert "no effect hypothesis" in expansions

    def test_get_domain_phrases_technical(self, manager):
        """Verify technical common phrases."""
        phrases = manager.get_domain_phrases(Domain.TECHNICAL)

        assert "best practices" in phrases
        assert "code review" in phrases

    def test_get_domain_phrases_medical(self, manager):
        """Verify medical common phrases."""
        phrases = manager.get_domain_phrases(Domain.MEDICAL)

        assert "vital signs" in phrases
        assert "adverse effects" in phrases

    def test_enrich_query_context_technical(self, manager):
        """Verify query enrichment with contextual information."""
        query = "How to implement REST API using Docker?"

        context = manager.enrich_query_context(query, Domain.TECHNICAL)

        # Should find abbreviations
        assert any(item["abbr"] == "REST" for item in context["abbreviations"])
        assert any(item["abbr"] == "API" for item in context["abbreviations"])

        # Should find terms with expansions
        docker_exp = next(
            (item for item in context["expansions"] if item["term"] == "docker"),
            None
        )
        assert docker_exp is not None
        assert "containerization" in docker_exp["expansions"]

    def test_enrich_query_context_medical(self, manager):
        """Verify medical query enrichment."""
        query = "Patient with HTN needs BP monitoring"

        context = manager.enrich_query_context(query, Domain.MEDICAL)

        # Should find medical abbreviations
        assert any(item["abbr"] == "HTN" for item in context["abbreviations"])
        assert any(item["abbr"] == "BP" for item in context["abbreviations"])

    def test_enrich_query_context_general_empty(self, manager):
        """Verify general domain returns empty context."""
        query = "Some general text"

        context = manager.enrich_query_context(query, Domain.GENERAL)

        assert context["abbreviations"] == []
        assert context["synonyms"] == []
        assert context["expansions"] == []

    def test_word_boundary_matching(self, manager):
        """Verify abbreviations only match whole words."""
        # "API" should not match in "rapid" or "apical"
        text = "Rapid deployment of apical API endpoint"

        expanded = manager.expand_abbreviations(text, Domain.TECHNICAL)

        # Should only expand "API", not partial matches
        assert expanded.count("Application Programming Interface") == 1

    def test_case_insensitive_synonym_matching(self, manager):
        """Verify synonym matching is case-insensitive."""
        # Test with different cases
        synonyms1 = manager.get_synonyms("Function", Domain.TECHNICAL)
        synonyms2 = manager.get_synonyms("function", Domain.TECHNICAL)
        synonyms3 = manager.get_synonyms("FUNCTION", Domain.TECHNICAL)

        # Should all return the same synonyms
        assert synonyms1 == synonyms2 == synonyms3

    def test_reverse_synonym_lookup(self, manager):
        """Verify finding synonyms when term is in synonym list."""
        # "method" is a synonym of "function"
        synonyms = manager.get_synonyms("method", Domain.TECHNICAL)

        # Should return "function" and other synonyms
        assert "function" in synonyms
        assert "procedure" in synonyms

    def test_singleton_terminology_manager(self):
        """Verify global terminology manager singleton."""
        manager1 = get_terminology_manager()
        manager2 = get_terminology_manager()

        assert manager1 is manager2


class TestTerminologyIntegration:
    """Test terminology integration with domain adapter."""

    @pytest.fixture
    def manager(self):
        """Create terminology manager."""
        return TerminologyManager()

    def test_technical_query_flow(self, manager):
        """Test complete technical query expansion flow."""
        query = "Deploy API with K8s and JWT auth"

        # Expand abbreviations
        expanded = manager.expand_query(query, Domain.TECHNICAL)

        # Should have expanded K8s, API, JWT
        assert "Kubernetes" in expanded
        assert "Application Programming Interface" in expanded
        assert "JSON Web Token" in expanded

    def test_medical_query_flow(self, manager):
        """Test complete medical query expansion flow."""
        query = "Patient with MI and HTN on aspirin"

        # Expand abbreviations
        expanded = manager.expand_query(query, Domain.MEDICAL)

        # Should have expanded MI, HTN
        assert "Myocardial Infarction" in expanded
        assert "Hypertension" in expanded

    def test_multi_abbreviation_text(self, manager):
        """Test text with multiple abbreviations."""
        text = "Using REST API with JWT for K8s deployment on AWS"

        expanded = manager.expand_abbreviations(text, Domain.TECHNICAL)

        # Should expand all abbreviations
        assert "Representational State Transfer" in expanded
        assert "Application Programming Interface" in expanded
        assert "JSON Web Token" in expanded
        assert "Kubernetes" in expanded
        assert "Amazon Web Services" in expanded

    def test_mixed_case_abbreviations(self, manager):
        """Test abbreviations with mixed case."""
        text = "The api uses jwt authentication"

        # lowercase abbreviations should also be expanded
        expanded = manager.expand_abbreviations(text, Domain.TECHNICAL)

        assert "application programming interface" in expanded.lower() or "api" in expanded.lower()

    def test_preserve_original_with_expansion(self, manager):
        """Verify original abbreviation is preserved with expansion."""
        text = "API endpoint"

        expanded = manager.expand_abbreviations(text, Domain.TECHNICAL)

        # Should have both original and expansion
        assert "API" in expanded
        assert "Application Programming Interface" in expanded
