"""Tests for feature flag management.

v0.2.9: Comprehensive tests for runtime feature toggles.
"""

import pytest
from pydantic import ValidationError

from src.config.feature_flags import FeatureFlags


class TestFeatureFlagsInitialization:
    """Tests for FeatureFlags initialization."""

    def test_default_initialization(self):
        """Test default initialization with all flags."""
        flags = FeatureFlags()
        assert isinstance(flags, FeatureFlags)

    def test_most_flags_default_to_false(self):
        """Test that most flags default to False for safe rollout."""
        flags = FeatureFlags()
        all_flags = flags.get_all_flags()

        # Count False flags
        false_count = sum(1 for v in all_flags.values() if not v)
        total_count = len(all_flags)

        # Most should be False (only query_caching is True by default)
        assert false_count >= total_count - 1

    def test_query_caching_defaults_to_true(self):
        """Test that query_caching is enabled by default (exists in v0.2.8)."""
        flags = FeatureFlags()
        assert flags.enable_query_caching is True

    def test_custom_initialization(self):
        """Test initialization with custom values."""
        flags = FeatureFlags(
            enable_embedder_caching=True,
            enable_batch_auto_tuning=True
        )
        assert flags.enable_embedder_caching is True
        assert flags.enable_batch_auto_tuning is True

    def test_invalid_field_rejected(self):
        """Test that invalid fields are rejected."""
        with pytest.raises(ValidationError):
            FeatureFlags(invalid_field=True)


class TestPhase1Flags:
    """Tests for Phase 1 feature flags."""

    def test_embedder_caching_flag(self):
        """Test embedder caching flag."""
        flags = FeatureFlags()
        assert flags.enable_embedder_caching is False

        flags_enabled = FeatureFlags(enable_embedder_caching=True)
        assert flags_enabled.enable_embedder_caching is True

    def test_batch_auto_tuning_flag(self):
        """Test batch auto-tuning flag."""
        flags = FeatureFlags()
        assert flags.enable_batch_auto_tuning is False

    def test_advanced_error_recovery_flag(self):
        """Test advanced error recovery flag."""
        flags = FeatureFlags()
        assert flags.enable_advanced_error_recovery is False

    def test_resource_governance_flag(self):
        """Test resource governance flag."""
        flags = FeatureFlags()
        assert flags.enable_resource_governance is False

    def test_performance_aware_logging_flag(self):
        """Test performance-aware logging flag."""
        flags = FeatureFlags()
        assert flags.enable_performance_aware_logging is False


class TestPhase2Flags:
    """Tests for Phase 2 feature flags."""

    def test_enhanced_health_checks_flag(self):
        """Test enhanced health checks flag."""
        flags = FeatureFlags()
        assert flags.enable_enhanced_health_checks is False

    def test_async_backpressure_flag(self):
        """Test async backpressure flag."""
        flags = FeatureFlags()
        assert flags.enable_async_backpressure is False

    def test_incremental_indexing_flag(self):
        """Test incremental indexing flag."""
        flags = FeatureFlags()
        assert flags.enable_incremental_indexing is False

    def test_observability_dashboard_flag(self):
        """Test observability dashboard flag."""
        flags = FeatureFlags()
        assert flags.enable_observability_dashboard is False

    def test_cold_start_optimisation_flag(self):
        """Test cold start optimisation flag."""
        flags = FeatureFlags()
        assert flags.enable_cold_start_optimisation is False


class TestPhase3Flags:
    """Tests for Phase 3 feature flags."""

    def test_graceful_degradation_flag(self):
        """Test graceful degradation flag."""
        flags = FeatureFlags()
        assert flags.enable_graceful_degradation is False

    def test_multi_tier_caching_flag(self):
        """Test multi-tier caching flag."""
        flags = FeatureFlags()
        assert flags.enable_multi_tier_caching is False

    def test_adaptive_tuning_flag(self):
        """Test adaptive tuning flag."""
        flags = FeatureFlags()
        assert flags.enable_adaptive_tuning is False


class TestIsEnabled:
    """Tests for is_enabled method."""

    def test_is_enabled_with_prefix(self):
        """Test is_enabled with 'enable_' prefix."""
        flags = FeatureFlags(enable_embedder_caching=True)
        assert flags.is_enabled("enable_embedder_caching") is True

    def test_is_enabled_without_prefix(self):
        """Test is_enabled without 'enable_' prefix."""
        flags = FeatureFlags(enable_embedder_caching=True)
        assert flags.is_enabled("embedder_caching") is True

    def test_is_enabled_false_flag(self):
        """Test is_enabled for disabled flag."""
        flags = FeatureFlags()
        assert flags.is_enabled("embedder_caching") is False

    def test_is_enabled_invalid_feature(self):
        """Test is_enabled with invalid feature name."""
        flags = FeatureFlags()
        with pytest.raises(AttributeError, match="Unknown feature"):
            flags.is_enabled("nonexistent_feature")

    def test_is_enabled_query_caching_default(self):
        """Test is_enabled for query_caching (default enabled)."""
        flags = FeatureFlags()
        assert flags.is_enabled("query_caching") is True


class TestEnableMethod:
    """Tests for enable method."""

    def test_enable_feature(self):
        """Test enabling a feature."""
        flags = FeatureFlags()
        assert flags.enable_embedder_caching is False

        flags.enable("embedder_caching")
        assert flags.enable_embedder_caching is True

    def test_enable_with_prefix(self):
        """Test enabling with 'enable_' prefix."""
        flags = FeatureFlags()
        flags.enable("enable_batch_auto_tuning")
        assert flags.enable_batch_auto_tuning is True

    def test_enable_already_enabled(self):
        """Test enabling an already enabled feature."""
        flags = FeatureFlags(enable_embedder_caching=True)
        flags.enable("embedder_caching")
        assert flags.enable_embedder_caching is True  # Still True

    def test_enable_invalid_feature(self):
        """Test enabling invalid feature."""
        flags = FeatureFlags()
        with pytest.raises(AttributeError, match="Unknown feature"):
            flags.enable("nonexistent_feature")


class TestDisableMethod:
    """Tests for disable method."""

    def test_disable_feature(self):
        """Test disabling a feature."""
        flags = FeatureFlags(enable_embedder_caching=True)
        assert flags.enable_embedder_caching is True

        flags.disable("embedder_caching")
        assert flags.enable_embedder_caching is False

    def test_disable_with_prefix(self):
        """Test disabling with 'enable_' prefix."""
        flags = FeatureFlags(enable_batch_auto_tuning=True)
        flags.disable("enable_batch_auto_tuning")
        assert flags.enable_batch_auto_tuning is False

    def test_disable_already_disabled(self):
        """Test disabling an already disabled feature."""
        flags = FeatureFlags()
        flags.disable("embedder_caching")
        assert flags.enable_embedder_caching is False  # Still False

    def test_disable_invalid_feature(self):
        """Test disabling invalid feature."""
        flags = FeatureFlags()
        with pytest.raises(AttributeError, match="Unknown feature"):
            flags.disable("nonexistent_feature")

    def test_disable_query_caching(self):
        """Test disabling query_caching (default enabled)."""
        flags = FeatureFlags()
        assert flags.enable_query_caching is True

        flags.disable("query_caching")
        assert flags.enable_query_caching is False


class TestGetAllFlags:
    """Tests for get_all_flags method."""

    def test_get_all_flags_returns_dict(self):
        """Test get_all_flags returns a dictionary."""
        flags = FeatureFlags()
        all_flags = flags.get_all_flags()
        assert isinstance(all_flags, dict)

    def test_get_all_flags_count(self):
        """Test get_all_flags returns all flags."""
        flags = FeatureFlags()
        all_flags = flags.get_all_flags()

        # Should have flags from all 3 phases
        # Phase 1: 6 flags
        # Phase 2: 5 flags
        # Phase 3: 3 flags
        # Total: 14 flags
        assert len(all_flags) == 14

    def test_get_all_flags_keys(self):
        """Test get_all_flags has correct keys."""
        flags = FeatureFlags()
        all_flags = flags.get_all_flags()

        # All keys should start with 'enable_'
        for key in all_flags.keys():
            assert key.startswith("enable_")

    def test_get_all_flags_values_are_boolean(self):
        """Test all flag values are booleans."""
        flags = FeatureFlags()
        all_flags = flags.get_all_flags()

        for value in all_flags.values():
            assert isinstance(value, bool)

    def test_get_all_flags_reflects_changes(self):
        """Test get_all_flags reflects runtime changes."""
        flags = FeatureFlags()
        flags.enable("embedder_caching")

        all_flags = flags.get_all_flags()
        assert all_flags["enable_embedder_caching"] is True


class TestGetEnabledFeatures:
    """Tests for get_enabled_features method."""

    def test_get_enabled_features_returns_list(self):
        """Test get_enabled_features returns a list."""
        flags = FeatureFlags()
        enabled = flags.get_enabled_features()
        assert isinstance(enabled, list)

    def test_get_enabled_features_default(self):
        """Test get_enabled_features with defaults."""
        flags = FeatureFlags()
        enabled = flags.get_enabled_features()

        # Only query_caching is enabled by default
        assert "query_caching" in enabled
        assert len(enabled) == 1

    def test_get_enabled_features_after_enabling(self):
        """Test get_enabled_features after enabling features."""
        flags = FeatureFlags()
        flags.enable("embedder_caching")
        flags.enable("batch_auto_tuning")

        enabled = flags.get_enabled_features()
        assert "embedder_caching" in enabled
        assert "batch_auto_tuning" in enabled
        assert "query_caching" in enabled
        assert len(enabled) == 3

    def test_get_enabled_features_no_prefix(self):
        """Test get_enabled_features returns names without prefix."""
        flags = FeatureFlags(enable_embedder_caching=True)
        enabled = flags.get_enabled_features()

        # Should be 'embedder_caching', not 'enable_embedder_caching'
        assert "embedder_caching" in enabled
        assert "enable_embedder_caching" not in enabled

    def test_get_enabled_features_empty(self):
        """Test get_enabled_features when all disabled."""
        flags = FeatureFlags(enable_query_caching=False)
        enabled = flags.get_enabled_features()
        assert len(enabled) == 0


class TestGetPhase:
    """Tests for get_phase method."""

    def test_get_phase_phase1_features(self):
        """Test get_phase for Phase 1 features."""
        flags = FeatureFlags()
        phase_1_features = [
            "embedder_caching",
            "batch_auto_tuning",
            "query_caching",
            "advanced_error_recovery",
            "resource_governance",
            "performance_aware_logging",
        ]

        for feature in phase_1_features:
            assert flags.get_phase(feature) == 1

    def test_get_phase_phase2_features(self):
        """Test get_phase for Phase 2 features."""
        flags = FeatureFlags()
        phase_2_features = [
            "enhanced_health_checks",
            "async_backpressure",
            "incremental_indexing",
            "observability_dashboard",
            "cold_start_optimisation",
        ]

        for feature in phase_2_features:
            assert flags.get_phase(feature) == 2

    def test_get_phase_phase3_features(self):
        """Test get_phase for Phase 3 features."""
        flags = FeatureFlags()
        phase_3_features = [
            "graceful_degradation",
            "multi_tier_caching",
            "adaptive_tuning",
        ]

        for feature in phase_3_features:
            assert flags.get_phase(feature) == 3

    def test_get_phase_with_prefix(self):
        """Test get_phase handles 'enable_' prefix."""
        flags = FeatureFlags()
        assert flags.get_phase("enable_embedder_caching") == 1

    def test_get_phase_invalid_feature(self):
        """Test get_phase with invalid feature."""
        flags = FeatureFlags()
        with pytest.raises(AttributeError, match="Unknown feature"):
            flags.get_phase("nonexistent_feature")


class TestPydanticValidation:
    """Tests for Pydantic validation features."""

    def test_validate_assignment(self):
        """Test that assignments are validated."""
        flags = FeatureFlags()

        # Should allow boolean
        flags.enable_embedder_caching = True
        assert flags.enable_embedder_caching is True

        flags.enable_embedder_caching = False
        assert flags.enable_embedder_caching is False

    def test_extra_fields_forbidden(self):
        """Test that extra fields are forbidden."""
        with pytest.raises(ValidationError):
            FeatureFlags(unknown_flag=True)

    def test_field_descriptions_exist(self):
        """Test that all fields have descriptions."""
        flags = FeatureFlags()

        for field_name, field_info in flags.model_fields.items():
            assert field_info.description is not None
            assert len(field_info.description) > 0


class TestIntegrationScenarios:
    """Integration tests for realistic feature flag usage."""

    def test_phased_rollout_scenario(self):
        """Test phased rollout of features."""
        # Start with all disabled
        flags = FeatureFlags()

        # Phase 1 rollout
        flags.enable("embedder_caching")
        flags.enable("batch_auto_tuning")

        phase_1_enabled = ["embedder_caching", "batch_auto_tuning"]
        enabled = flags.get_enabled_features()

        for feature in phase_1_enabled:
            assert feature in enabled

        # Phase 2 rollout
        flags.enable("enhanced_health_checks")
        flags.enable("incremental_indexing")

        enabled = flags.get_enabled_features()
        assert len(enabled) >= 4  # Phase 1 + Phase 2 features

    def test_rollback_scenario(self):
        """Test rolling back a problematic feature."""
        flags = FeatureFlags()

        # Enable feature
        flags.enable("embedder_caching")
        assert flags.is_enabled("embedder_caching") is True

        # Discover issue, rollback
        flags.disable("embedder_caching")
        assert flags.is_enabled("embedder_caching") is False

        # Other features unaffected
        assert flags.is_enabled("query_caching") is True

    def test_selective_feature_enabling(self):
        """Test enabling only specific features."""
        flags = FeatureFlags(
            enable_embedder_caching=True,
            enable_incremental_indexing=True,
            enable_multi_tier_caching=True,
        )

        enabled = flags.get_enabled_features()

        # Should have query_caching (default) + 3 explicitly enabled
        assert len(enabled) == 4
        assert "embedder_caching" in enabled
        assert "incremental_indexing" in enabled
        assert "multi_tier_caching" in enabled

        # Other features should be disabled
        assert "batch_auto_tuning" not in enabled

    def test_check_before_using_feature(self):
        """Test checking flag before using feature."""
        flags = FeatureFlags(enable_embedder_caching=True)

        # Typical usage pattern
        if flags.is_enabled("embedder_caching"):
            # Use embedder caching
            result = "using cache"
        else:
            # Fallback path
            result = "no cache"

        assert result == "using cache"

    def test_get_phase_for_filtering(self):
        """Test using get_phase to filter features."""
        flags = FeatureFlags()

        # Enable all Phase 1 features
        all_flags = flags.get_all_flags()
        for flag_name in all_flags.keys():
            feature_name = flag_name.replace("enable_", "")
            if flags.get_phase(feature_name) == 1:
                flags.enable(feature_name)

        # Check that only Phase 1 features are enabled
        enabled = flags.get_enabled_features()
        for feature in enabled:
            if feature != "query_caching":  # Skip default
                phase = flags.get_phase(feature)
                assert phase == 1

    def test_feature_flag_state_persistence(self):
        """Test that feature flag state can be serialized."""
        flags = FeatureFlags(
            enable_embedder_caching=True,
            enable_batch_auto_tuning=True,
        )

        # Serialize
        state = flags.model_dump()

        # Create new instance from state
        restored_flags = FeatureFlags(**state)

        # State should match
        assert restored_flags.enable_embedder_caching is True
        assert restored_flags.enable_batch_auto_tuning is True
        assert restored_flags.enable_advanced_error_recovery is False
