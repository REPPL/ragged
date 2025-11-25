"""
Query optimisation module (v0.6.1+ OPTIMISE-001, OPTIMISE-002).

This module provides query classification and automatic model routing for
intelligent model selection and performance improvements.

v0.6.1 OPTIMISE-001: Query classification foundation
v0.6.2 OPTIMISE-002: Automatic model routing and lifecycle management
"""

from ragged.optimisation.model_manager import ModelInfo, ModelManager
from ragged.optimisation.model_router import ModelRouter, ModelSelection
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
    "ModelRouter",
    "ModelSelection",
    "ModelManager",
    "ModelInfo",
]
