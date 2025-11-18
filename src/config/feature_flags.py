"""Feature flags for v0.2.9 runtime toggles.

This module provides feature flag management for safe, gradual rollout
of v0.2.9 features with easy rollback capability.
"""

from pydantic import BaseModel, Field
from typing import Dict, List


class FeatureFlags(BaseModel):
    """Runtime feature toggles for v0.2.9 features.

    All flags default to False (safe) for gradual rollout.
    Set to True to enable features after validation.
    """

    # Phase 1: Core Performance
    enable_embedder_caching: bool = Field(
        default=False,
        description="Enable embedder singleton pattern with progressive warm-up (4-30x faster)"
    )
    enable_batch_auto_tuning: bool = Field(
        default=False,
        description="Enable intelligent batch size auto-tuning based on doc size/memory"
    )
    enable_query_caching: bool = Field(
        default=True,  # Already exists and working
        description="Enable query result caching (LRU with TTL)"
    )
    enable_advanced_error_recovery: bool = Field(
        default=False,
        description="Enable retry with exponential backoff and circuit breaker"
    )
    enable_resource_governance: bool = Field(
        default=False,
        description="Enable unified resource budget management (CPU/memory/I/O)"
    )
    enable_performance_aware_logging: bool = Field(
        default=False,
        description="Enable async logging with sampling for high-frequency events"
    )

    # Phase 2: Operational Excellence
    enable_enhanced_health_checks: bool = Field(
        default=False,
        description="Enable deep diagnostics and performance validation in health checks"
    )
    enable_async_backpressure: bool = Field(
        default=False,
        description="Enable backpressure control in async operations (queue limits, dynamic workers)"
    )
    enable_incremental_indexing: bool = Field(
        default=False,
        description="Enable incremental BM25 index operations (10-100x faster for large collections)"
    )
    enable_observability_dashboard: bool = Field(
        default=False,
        description="Enable live performance dashboard (ragged monitor command)"
    )
    enable_cold_start_optimisation: bool = Field(
        default=False,
        description="Enable cold start optimisations (connection pooling, parallel init)"
    )

    # Phase 3: Production Hardening
    enable_graceful_degradation: bool = Field(
        default=False,
        description="Enable graceful degradation (fallback paths for service failures)"
    )
    enable_multi_tier_caching: bool = Field(
        default=False,
        description="Enable multi-tier caching strategy (L1/L2/L3 for 30-50x improvement)"
    )
    enable_adaptive_tuning: bool = Field(
        default=False,
        description="Enable adaptive performance tuning (self-optimisation based on workload)"
    )

    def is_enabled(self, feature: str) -> bool:
        """Check if a feature is enabled.

        Args:
            feature: Feature name without 'enable_' prefix
                    (e.g., 'embedder_caching' not 'enable_embedder_caching')

        Returns:
            True if feature is enabled, False otherwise

        Raises:
            AttributeError: If feature name is invalid

        Example:
            >>> flags = FeatureFlags()
            >>> flags.is_enabled('query_caching')
            True
            >>> flags.is_enabled('embedder_caching')
            False
        """
        attr_name = f"enable_{feature}" if not feature.startswith("enable_") else feature
        if not hasattr(self, attr_name):
            raise AttributeError(f"Unknown feature: {feature}")
        return getattr(self, attr_name)

    def enable(self, feature: str) -> None:
        """Enable a feature flag.

        Args:
            feature: Feature name without 'enable_' prefix

        Raises:
            AttributeError: If feature name is invalid

        Example:
            >>> flags = FeatureFlags()
            >>> flags.enable('embedder_caching')
            >>> flags.is_enabled('embedder_caching')
            True
        """
        attr_name = f"enable_{feature}" if not feature.startswith("enable_") else feature
        if not hasattr(self, attr_name):
            raise AttributeError(f"Unknown feature: {feature}")
        setattr(self, attr_name, True)

    def disable(self, feature: str) -> None:
        """Disable a feature flag.

        Args:
            feature: Feature name without 'enable_' prefix

        Raises:
            AttributeError: If feature name is invalid

        Example:
            >>> flags = FeatureFlags()
            >>> flags.enable('embedder_caching')
            >>> flags.disable('embedder_caching')
            >>> flags.is_enabled('embedder_caching')
            False
        """
        attr_name = f"enable_{feature}" if not feature.startswith("enable_") else feature
        if not hasattr(self, attr_name):
            raise AttributeError(f"Unknown feature: {feature}")
        setattr(self, attr_name, False)

    def get_all_flags(self) -> Dict[str, bool]:
        """Get all feature flags and their current status.

        Returns:
            Dictionary mapping feature names to their enabled status

        Example:
            >>> flags = FeatureFlags()
            >>> all_flags = flags.get_all_flags()
            >>> all_flags['enable_query_caching']
            True
        """
        return {
            field_name: getattr(self, field_name)
            for field_name in self.model_fields.keys()
        }

    def get_enabled_features(self) -> List[str]:
        """Get list of currently enabled features.

        Returns:
            List of feature names (without 'enable_' prefix) that are enabled

        Example:
            >>> flags = FeatureFlags()
            >>> flags.get_enabled_features()
            ['query_caching']
        """
        return [
            field_name.replace("enable_", "")
            for field_name, value in self.get_all_flags().items()
            if value
        ]

    def get_phase(self, feature: str) -> int:
        """Get the phase number for a feature.

        Args:
            feature: Feature name

        Returns:
            Phase number (1, 2, or 3)

        Raises:
            AttributeError: If feature name is invalid
        """
        phase_1_features = [
            "embedder_caching", "batch_auto_tuning", "query_caching",
            "advanced_error_recovery", "resource_governance", "performance_aware_logging"
        ]
        phase_2_features = [
            "enhanced_health_checks", "async_backpressure", "incremental_indexing",
            "observability_dashboard", "cold_start_optimisation"
        ]
        phase_3_features = [
            "graceful_degradation", "multi_tier_caching", "adaptive_tuning"
        ]

        feature = feature.replace("enable_", "")
        if feature in phase_1_features:
            return 1
        elif feature in phase_2_features:
            return 2
        elif feature in phase_3_features:
            return 3
        else:
            raise AttributeError(f"Unknown feature: {feature}")

    class Config:
        """Pydantic configuration."""
        validate_assignment = True
        extra = "forbid"  # Prevent unknown fields
