"""
Query optimisation module (v0.6.1+ OPTIMISE-001, OPTIMISE-002, OPTIMISE-003).

This module provides query classification, automatic model routing, and
domain adaptation for intelligent model selection and performance improvements.

v0.6.1 OPTIMISE-001: Query classification foundation
v0.6.2 OPTIMISE-002: Automatic model routing and lifecycle management
v0.6.2 OPTIMISE-002: Integrated routing service
v0.6.3 OPTIMISE-003: Domain adaptation for specialized content
"""

from ragged.optimisation.domain_adapter import Domain, DomainDetectionResult, DomainDetector
from ragged.optimisation.domain_retrieval import (
    DomainAwareRetriever,
    DomainRetrievalConfig,
    DomainRetrievalResult,
    get_domain_aware_retriever,
)
from ragged.optimisation.model_manager import ModelInfo, ModelManager
from ragged.optimisation.model_router import ModelRouter, ModelSelection
from ragged.optimisation.query_classifier import (
    QueryClassification,
    QueryClassifier,
    QueryIntent,
    QueryType,
)
from ragged.optimisation.routing_metadata import RoutingMetadata
from ragged.optimisation.routing_service import RoutingDecision, RoutingService
from ragged.optimisation.terminology import TerminologyManager, get_terminology_manager

__all__ = [
    # Query Classification (v0.6.1)
    "QueryClassifier",
    "QueryClassification",
    "QueryType",
    "QueryIntent",
    "RoutingMetadata",
    # Model Routing (v0.6.2)
    "ModelRouter",
    "ModelSelection",
    "ModelManager",
    "ModelInfo",
    "RoutingService",
    "RoutingDecision",
    # Domain Adaptation (v0.6.3)
    "Domain",
    "DomainDetector",
    "DomainDetectionResult",
    "TerminologyManager",
    "get_terminology_manager",
    "DomainAwareRetriever",
    "DomainRetrievalConfig",
    "DomainRetrievalResult",
    "get_domain_aware_retriever",
]
