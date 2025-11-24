"""
Query classification for intelligent routing (v0.6.1 OPTIMISE-001).

Classifies queries by type, complexity, and intent to enable smart model
selection and optimisation in subsequent versions.
"""

import re
from dataclasses import dataclass
from enum import Enum


class QueryType(str, Enum):
    """Type of query based on information need."""

    FACTUAL = "factual"  # Lookup queries: "What is RAG?"
    CONCEPTUAL = "conceptual"  # Explanation queries: "How does RAG work?"
    EXPLORATORY = "exploratory"  # Discovery queries: "Find examples of..."
    MULTI_HOP = "multi_hop"  # Complex reasoning: "Compare X and Y, then..."


class QueryIntent(str, Enum):
    """Intent behind the query."""

    LOOKUP = "lookup"  # Finding specific information
    ANALYSIS = "analysis"  # Understanding relationships or patterns
    COMPARISON = "comparison"  # Evaluating alternatives or similarities
    SYNTHESIS = "synthesis"  # Creating new insights from multiple sources


@dataclass
class QueryClassification:
    """Classification results for a query."""

    query: str
    query_type: QueryType
    complexity: int  # 1-10 scale
    intent: QueryIntent
    is_multi_hop: bool
    domain_hints: list[str]  # Detected domain keywords

    def to_dict(self) -> dict:
        """Convert to dictionary for serialisation."""
        return {
            "query": self.query,
            "query_type": self.query_type.value,
            "complexity": self.complexity,
            "intent": self.intent.value,
            "is_multi_hop": self.is_multi_hop,
            "domain_hints": self.domain_hints,
        }


class QueryClassifier:
    """
    Classify queries for intelligent routing.

    Uses rule-based classification with feature extraction for:
    - Query type detection (factual, conceptual, exploratory, multi-hop)
    - Complexity scoring (1-10 scale)
    - Intent classification (lookup, analysis, comparison, synthesis)
    - Domain hint detection

    v0.6.1 OPTIMISE-001: Foundation for automatic model routing (v0.6.2)
    """

    # Patterns for query type detection
    FACTUAL_PATTERNS = [
        r"\bwhat is\b",
        r"\bwho is\b",
        r"\bwhen was\b",
        r"\bwhere is\b",
        r"\bdefine\b",
        r"\blist\b",
    ]

    CONCEPTUAL_PATTERNS = [
        r"\bhow does\b",
        r"\bhow do\b",
        r"\bhow can\b",
        r"\bwhy\b",
        r"\bexplain\b",
        r"\bdescribe\b",
        r"\bwhat are the .* of\b",
    ]

    EXPLORATORY_PATTERNS = [
        r"\bfind\b",
        r"\bshow\b",
        r"\bdiscover\b",
        r"\bexplore\b",
        r"\bsearch for\b",
        r"\blook for\b",
    ]

    MULTI_HOP_INDICATORS = [
        r"\bcompare\b",
        r"\bcontrast\b",
        r"\band then\b",
        r"\bafter that\b",
        r"\bbased on\b",
        r"\bgiven that\b",
        r"\bif .* then\b",
    ]

    # Patterns for intent detection
    COMPARISON_PATTERNS = [
        r"\bcompare\b",
        r"\bcontrast\b",
        r"\bdifference between\b",
        r"\bsimilar to\b",
        r"\bvs\b",
        r"\bversus\b",
    ]

    ANALYSIS_PATTERNS = [
        r"\banalyse\b",
        r"\banalyze\b",
        r"\bwhy\b",
        r"\bhow\b",
        r"\brelationship\b",
        r"\bimpact\b",
        r"\beffect\b",
    ]

    SYNTHESIS_PATTERNS = [
        r"\bcombine\b",
        r"\bsynthesize\b",
        r"\bsummarise\b",
        r"\bsummarize\b",
        r"\bintegrate\b",
        r"\bmerge\b",
    ]

    # Domain keywords for hint detection
    DOMAIN_KEYWORDS = {
        "vision": ["image", "picture", "photo", "visual", "ocr", "colpali", "vision"],
        "embeddings": ["embedding", "vector", "semantic", "similarity"],
        "technical": ["code", "api", "function", "algorithm", "implementation"],
        "medical": ["medical", "diagnosis", "treatment", "patient", "clinical"],
        "legal": ["legal", "law", "contract", "statute", "regulation"],
        "academic": ["research", "study", "paper", "publication", "academic"],
    }

    def __init__(self) -> None:
        """Initialise query classifier with pattern matchers."""
        # Compile patterns for efficiency
        self.factual_re = [re.compile(p, re.IGNORECASE) for p in self.FACTUAL_PATTERNS]
        self.conceptual_re = [
            re.compile(p, re.IGNORECASE) for p in self.CONCEPTUAL_PATTERNS
        ]
        self.exploratory_re = [
            re.compile(p, re.IGNORECASE) for p in self.EXPLORATORY_PATTERNS
        ]
        self.multi_hop_re = [
            re.compile(p, re.IGNORECASE) for p in self.MULTI_HOP_INDICATORS
        ]
        self.comparison_re = [
            re.compile(p, re.IGNORECASE) for p in self.COMPARISON_PATTERNS
        ]
        self.analysis_re = [re.compile(p, re.IGNORECASE) for p in self.ANALYSIS_PATTERNS]
        self.synthesis_re = [
            re.compile(p, re.IGNORECASE) for p in self.SYNTHESIS_PATTERNS
        ]

    def classify(self, query: str) -> QueryClassification:
        """
        Classify a query for intelligent routing.

        Args:
            query: User query string

        Returns:
            QueryClassification with type, complexity, intent, and hints

        Example:
            >>> classifier = QueryClassifier()
            >>> result = classifier.classify("How does ColPali work?")
            >>> result.query_type
            <QueryType.CONCEPTUAL: 'conceptual'>
            >>> result.complexity
            5
        """
        # Sanitize query
        query_clean = query.strip()
        query_lower = query_clean.lower()

        # Detect query type
        query_type = self._detect_query_type(query_lower)

        # Check for multi-hop
        is_multi_hop = self._is_multi_hop(query_lower)
        if is_multi_hop:
            query_type = QueryType.MULTI_HOP

        # Calculate complexity
        complexity = self._calculate_complexity(query_clean, is_multi_hop)

        # Detect intent
        intent = self._detect_intent(query_lower, query_type)

        # Extract domain hints
        domain_hints = self._extract_domain_hints(query_lower)

        return QueryClassification(
            query=query_clean,
            query_type=query_type,
            complexity=complexity,
            intent=intent,
            is_multi_hop=is_multi_hop,
            domain_hints=domain_hints,
        )

    def _detect_query_type(self, query_lower: str) -> QueryType:
        """Detect query type from patterns."""
        # Check factual patterns
        if any(pattern.search(query_lower) for pattern in self.factual_re):
            return QueryType.FACTUAL

        # Check conceptual patterns
        if any(pattern.search(query_lower) for pattern in self.conceptual_re):
            return QueryType.CONCEPTUAL

        # Check exploratory patterns
        if any(pattern.search(query_lower) for pattern in self.exploratory_re):
            return QueryType.EXPLORATORY

        # Default to factual for simple queries
        return QueryType.FACTUAL

    def _is_multi_hop(self, query_lower: str) -> bool:
        """Check if query requires multi-hop reasoning."""
        return any(pattern.search(query_lower) for pattern in self.multi_hop_re)

    def _calculate_complexity(self, query: str, is_multi_hop: bool) -> int:
        """
        Calculate query complexity (1-10 scale).

        Factors:
        - Query length (longer = more complex)
        - Number of clauses (commas, conjunctions)
        - Multi-hop indicators
        - Technical terminology density
        """
        complexity = 1

        # Length factor (1-3 points)
        word_count = len(query.split())
        if word_count > 30:
            complexity += 3
        elif word_count > 15:
            complexity += 2
        elif word_count > 5:
            complexity += 1

        # Clause factor (1-3 points)
        clause_count = query.count(",") + query.count(" and ") + query.count(" or ")
        if clause_count >= 3:
            complexity += 3
        elif clause_count >= 2:
            complexity += 2
        elif clause_count >= 1:
            complexity += 1

        # Multi-hop bonus (2 points)
        if is_multi_hop:
            complexity += 2

        # Question complexity (1-2 points)
        if "?" in query:
            # Multiple questions = more complex
            question_count = query.count("?")
            complexity += min(question_count, 2)

        # Cap at 10
        return min(complexity, 10)

    def _detect_intent(self, query_lower: str, query_type: QueryType) -> QueryIntent:
        """Detect user intent from query."""
        # Check comparison patterns (highest priority)
        if any(pattern.search(query_lower) for pattern in self.comparison_re):
            return QueryIntent.COMPARISON

        # Check synthesis patterns
        if any(pattern.search(query_lower) for pattern in self.synthesis_re):
            return QueryIntent.SYNTHESIS

        # Check analysis patterns
        if any(pattern.search(query_lower) for pattern in self.analysis_re):
            return QueryIntent.ANALYSIS

        # Default based on query type
        if query_type in (QueryType.CONCEPTUAL, QueryType.MULTI_HOP):
            return QueryIntent.ANALYSIS
        else:
            return QueryIntent.LOOKUP

    def _extract_domain_hints(self, query_lower: str) -> list[str]:
        """Extract domain hints from query keywords."""
        hints = []
        for domain, keywords in self.DOMAIN_KEYWORDS.items():
            if any(keyword in query_lower for keyword in keywords):
                hints.append(domain)
        return hints
