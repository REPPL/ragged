"""
Query optimisation module (v0.6.1+).

This module provides query classification and routing optimisation for
intelligent model selection and performance improvements.
"""

from ragged.optimisation.query_classifier import (
    QueryClassification,
    QueryClassifier,
    QueryIntent,
    QueryType,
)
from ragged.optimisation.routing_metadata import RoutingMetadata

__all__ = [
    "QueryClassifier",
    "QueryClassification",
    "QueryType",
    "QueryIntent",
    "RoutingMetadata",
]
