"""Cache key generation with consistent hashing.

Provides secure, deterministic key generation for caching with
collision resistance and privacy preservation.

v0.6.4 OPTIMISE-005 Phase 1: Caching Infrastructure
"""

from __future__ import annotations

import hashlib
import json
from typing import Any


class CacheKeyGenerator:
    """Generate cache keys with consistent hashing.

    Features:
    - Deterministic key generation
    - Collision resistance (SHA256)
    - Privacy-preserving (no PII in keys)
    - Support for complex objects
    """

    @staticmethod
    def generate_key(*args: Any, **kwargs: Any) -> str:
        """Generate cache key from arguments.

        Args:
            *args: Positional arguments to include in key
            **kwargs: Keyword arguments to include in key

        Returns:
            Hex-encoded SHA256 hash key
        """
        # Build deterministic string representation
        key_parts = []

        # Add positional arguments
        for arg in args:
            key_parts.append(CacheKeyGenerator._serialise_value(arg))

        # Add keyword arguments (sorted for consistency)
        for k in sorted(kwargs.keys()):
            v = kwargs[k]
            key_parts.append(f"{k}={CacheKeyGenerator._serialise_value(v)}")

        # Join and hash
        key_string = "::".join(key_parts)
        return hashlib.sha256(key_string.encode("utf-8")).hexdigest()

    @staticmethod
    def generate_query_key(query: str, **context: Any) -> str:
        """Generate cache key for a query.

        Args:
            query: Query text
            **context: Additional context (model, domain, etc.)

        Returns:
            Cache key
        """
        return CacheKeyGenerator.generate_key(query, **context)

    @staticmethod
    def generate_classification_key(query: str) -> str:
        """Generate cache key for query classification.

        Args:
            query: Query text

        Returns:
            Cache key
        """
        return CacheKeyGenerator.generate_key("classification", query)

    @staticmethod
    def generate_routing_key(query_type: str, complexity: int) -> str:
        """Generate cache key for model routing.

        Args:
            query_type: Classified query type
            complexity: Query complexity score

        Returns:
            Cache key
        """
        return CacheKeyGenerator.generate_key(
            "routing", query_type=query_type, complexity=complexity
        )

    @staticmethod
    def generate_domain_key(text: str) -> str:
        """Generate cache key for domain detection.

        Args:
            text: Text to detect domain from

        Returns:
            Cache key
        """
        return CacheKeyGenerator.generate_key("domain", text)

    @staticmethod
    def generate_retrieval_key(
        query: str, k: int, domain: str | None = None
    ) -> str:
        """Generate cache key for retrieval results.

        Args:
            query: Query text
            k: Number of results
            domain: Optional domain filter

        Returns:
            Cache key
        """
        return CacheKeyGenerator.generate_key(
            "retrieval", query=query, k=k, domain=domain or "none"
        )

    @staticmethod
    def generate_llm_key(query: str, model: str, context_hash: str) -> str:
        """Generate cache key for LLM responses.

        Args:
            query: Query text
            model: Model identifier
            context_hash: Hash of retrieval context

        Returns:
            Cache key
        """
        return CacheKeyGenerator.generate_key(
            "llm", query=query, model=model, context=context_hash
        )

    @staticmethod
    def _serialise_value(value: Any) -> str:
        """Serialise a value for key generation.

        Args:
            value: Value to serialise

        Returns:
            String representation
        """
        if value is None:
            return "null"
        elif isinstance(value, bool):
            return "true" if value else "false"
        elif isinstance(value, (int, float)):
            return str(value)
        elif isinstance(value, str):
            return value
        elif isinstance(value, (list, tuple)):
            # Serialise as JSON for determinism
            return json.dumps(value, sort_keys=True)
        elif isinstance(value, dict):
            # Serialise as JSON for determinism
            return json.dumps(value, sort_keys=True)
        else:
            # Fall back to string representation
            return str(value)
