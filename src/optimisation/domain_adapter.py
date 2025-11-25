"""Domain adaptation for specialized content retrieval.

Detects document domains (technical, medical, legal, academic) and adapts
retrieval strategies to improve accuracy with domain-specific terminology.

v0.6.3 OPTIMISE-003: Domain Adaptation
"""

import logging
import re
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

logger = logging.getLogger(__name__)


class Domain(Enum):
    """Supported content domains."""

    TECHNICAL = "technical"  # Programming, DevOps, cloud, APIs
    MEDICAL = "medical"  # Healthcare, pharmaceuticals, anatomy
    LEGAL = "legal"  # Law, regulations, contracts
    ACADEMIC = "academic"  # Research, scientific papers
    GENERAL = "general"  # Default for mixed or unrecognized content


@dataclass
class DomainDetectionResult:
    """Result of domain detection analysis."""

    primary_domain: Domain
    confidence: float  # 0.0-1.0
    domain_scores: dict[Domain, float]  # Scores for each domain
    indicators: list[str]  # Domain-specific keywords found


class DomainDetector:
    """Detects content domain based on terminology and patterns."""

    def __init__(self):
        """Initialize domain detector with keyword patterns."""
        # Domain-specific keyword patterns (regex patterns for flexibility)
        self.domain_patterns = {
            Domain.TECHNICAL: [
                # Programming & Software
                r"\b(function|class|method|variable|API|endpoint|REST|GraphQL)\b",
                r"\b(Python|JavaScript|Java|C\+\+|Rust|TypeScript|Golang)\b",
                r"\bGo\s+(language|programming|code|developer)\b",  # Go language with context
                r"\b(framework|library|package|dependency|npm|pip|cargo)\b",
                r"\b(Git|GitHub|Docker|Kubernetes|CI/CD|DevOps)\b",
                r"\b(database|SQL|NoSQL|MongoDB|PostgreSQL|Redis)\b",
                r"\b(cloud|AWS|Azure|GCP|serverless|microservices)\b",
                r"\b(algorithm|data structure|complexity|Big-O)\b",
                r"\b(authentication|authorization|OAuth|JWT|session)\b",
                # Code patterns
                r"[a-z]+\(\)|[A-Z][a-zA-Z]*\(\)",  # Function calls
                r"\{[^}]*\}|\[[^\]]*\]",  # Code blocks
            ],
            Domain.MEDICAL: [
                # Medical terminology
                r"\b(diagnosis|treatment|patient|symptoms?|disease)\b",
                r"\b(medication|prescription|dosage|mg|ml|tablet)\b",
                r"\b(surgery|procedure|operation|therapy)\b",
                r"\b(doctor|physician|nurse|hospital|clinic)\b",
                r"\b(cardiovascular|respiratory|neurological|gastrointestinal)\b",
                r"\b(hypertension|diabetes|cancer|infection|inflammation)\b",
                r"\b(acetaminophen|ibuprofen|antibiotic|insulin)\b",
                # Medical abbreviations
                r"\b(BP|HR|ECG|MRI|CT|X-ray)\b",
                r"\b(mg/dl|mmHg|bpm)\b",
            ],
            Domain.LEGAL: [
                # Legal terminology
                r"\b(statute|regulation|law|ordinance|code)\b",
                r"\b(court|judge|attorney|lawyer|counsel)\b",
                r"\b(plaintiff|defendant|petitioner|respondent)\b",
                r"\b(contract|agreement|clause|provision|amendment)\b",
                r"\b(liability|negligence|damages|tort|breach)\b",
                r"\b(jurisdiction|venue|standing|precedent)\b",
                r"\b(affidavit|deposition|subpoena|warrant|injunction)\b",
                # Legal citations
                r"\d+\s+U\.S\.C\.\s+§\s*\d+",  # U.S. Code
                r"\d+\s+F\.\s*\d+d?\s+\d+",  # Federal Reporter
                r"v\.|vs\.",  # versus in case names
            ],
            Domain.ACADEMIC: [
                # Academic/Research terminology
                r"\b(study|research|analysis|experiment|methodology)\b",
                r"\b(hypothesis|theory|model|framework)\b",
                r"\b(data|dataset|sample|population|cohort)\b",
                r"\b(statistical|significance|p-value|correlation)\b",
                r"\b(abstract|introduction|methods?|results?|discussion|conclusion)\b",
                r"\b(citation|reference|bibliography|et al\.)\b",
                r"\b(journal|paper|article|publication|conference)\b",
                r"\b(peer.review|manuscript|submission)\b",
                # Academic formatting
                r"\[\d+\]|\(\d{4}\)",  # Citations [1] or (2023)
                r"[A-Z][a-z]+\s+et\s+al\.",  # Author citations
            ],
        }

        # Compile patterns for efficiency
        self.compiled_patterns = {
            domain: [re.compile(pattern, re.IGNORECASE) for pattern in patterns]
            for domain, patterns in self.domain_patterns.items()
        }

    def detect_domain(self, text: str) -> DomainDetectionResult:
        """Detect the primary domain of the given text.

        Args:
            text: Text content to analyze

        Returns:
            DomainDetectionResult with primary domain and confidence
        """
        if not text or not text.strip():
            return DomainDetectionResult(
                primary_domain=Domain.GENERAL,
                confidence=1.0,
                domain_scores={Domain.GENERAL: 1.0},
                indicators=[],
            )

        # Calculate scores for each domain
        domain_scores = {}
        domain_indicators = {}

        for domain, patterns in self.compiled_patterns.items():
            matches = 0
            indicators = []

            for pattern in patterns:
                found = pattern.findall(text)
                if found:
                    matches += len(found)
                    indicators.extend(found[:3])  # Keep first 3 matches per pattern

            # Normalize score by text length (matches per 1000 characters)
            text_length = len(text)
            normalized_score = (matches / max(text_length / 1000, 1)) if text_length > 0 else 0

            domain_scores[domain] = min(normalized_score, 1.0)  # Cap at 1.0
            domain_indicators[domain] = indicators[:10]  # Keep top 10 indicators

        # Determine primary domain
        if not domain_scores or max(domain_scores.values()) < 0.1:
            # No strong domain signals - default to GENERAL
            return DomainDetectionResult(
                primary_domain=Domain.GENERAL,
                confidence=1.0,
                domain_scores={Domain.GENERAL: 1.0},
                indicators=[],
            )

        # Find domain with highest score
        primary_domain = max(domain_scores, key=domain_scores.get)
        primary_score = domain_scores[primary_domain]

        # Calculate confidence based on score separation
        sorted_scores = sorted(domain_scores.values(), reverse=True)
        if len(sorted_scores) > 1:
            # Confidence is higher when primary score is significantly higher than second
            score_gap = sorted_scores[0] - sorted_scores[1]
            confidence = min(primary_score + (score_gap * 0.5), 1.0)
        else:
            confidence = primary_score

        return DomainDetectionResult(
            primary_domain=primary_domain,
            confidence=confidence,
            domain_scores=domain_scores,
            indicators=domain_indicators[primary_domain],
        )

    def detect_domains_batch(self, texts: list[str]) -> list[DomainDetectionResult]:
        """Detect domains for multiple texts efficiently.

        Args:
            texts: List of text content to analyze

        Returns:
            List of DomainDetectionResult, one per input text
        """
        return [self.detect_domain(text) for text in texts]


class DomainAdapter:
    """Adapts retrieval strategies based on detected domain."""

    def __init__(self, terminology_manager=None):
        """Initialize domain adapter.

        Args:
            terminology_manager: Optional TerminologyManager instance.
                                 If None, will be lazily initialized.
        """
        self.detector = DomainDetector()
        self._terminology_manager = terminology_manager

    def tag_document_domain(self, content: str) -> dict[str, str | float]:
        """Tag document with detected domain metadata.

        Args:
            content: Document content

        Returns:
            Dictionary with domain metadata (domain, confidence, indicators)
        """
        result = self.detector.detect_domain(content)

        return {
            "domain": result.primary_domain.value,
            "domain_confidence": result.confidence,
            "domain_indicators": ", ".join(result.indicators[:5]),  # Top 5
        }

    def adapt_query_for_domain(self, query: str, domain: Domain | None = None) -> str:
        """Adapt query based on domain characteristics.

        If domain is not provided, detects domain from query.

        Args:
            query: Original query text
            domain: Optional domain hint

        Returns:
            Adapted query with terminology expansion
        """
        if domain is None:
            result = self.detector.detect_domain(query)
            domain = result.primary_domain

        # Use terminology manager for expansion (lazy initialization)
        if self._terminology_manager is None:
            # Avoid circular import
            from ragged.optimisation.terminology import get_terminology_manager
            self._terminology_manager = get_terminology_manager()

        # Expand query with domain-specific terminology
        adapted = self._terminology_manager.expand_query(query, domain)
        logger.debug(f"Query adapted for {domain.value} domain")
        return adapted

    def get_domain_weight_multiplier(self, domain: Domain) -> float:
        """Get scoring weight multiplier for domain-specific results.

        Different domains may benefit from different scoring adjustments.

        Args:
            domain: Document domain

        Returns:
            Weight multiplier (1.0 = no adjustment)
        """
        # Technical content benefits from exact term matching
        if domain == Domain.TECHNICAL:
            return 1.2

        # Medical/legal benefit from terminology normalization
        if domain in (Domain.MEDICAL, Domain.LEGAL):
            return 1.1

        # Academic benefits from citation matching
        if domain == Domain.ACADEMIC:
            return 1.05

        # General domain uses default scoring
        return 1.0


# Global instance for convenience
_domain_adapter = None


def get_domain_adapter() -> DomainAdapter:
    """Get global DomainAdapter instance (singleton pattern)."""
    global _domain_adapter
    if _domain_adapter is None:
        _domain_adapter = DomainAdapter()
    return _domain_adapter
