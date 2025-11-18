# Feature Flag Framework

**Feature**: Runtime Feature Toggles
**Phase**: 0 (Foundation)
**Estimated Effort**: 2-3 hours
**Priority**: MUST-HAVE
**Dependencies**: None (foundational)

---

## Overview

**Purpose**: Provide runtime feature toggles to enable safe, gradual rollout of v0.2.9 features with easy rollback capability.

**Success Criteria**:
- All v0.2.9 features can be toggled on/off via configuration
- Feature flags can be set globally or per-collection
- CLI command to view/modify feature flags
- Zero performance overhead when features enabled
- Default to safe values (new features OFF in alpha, ON in final)

---

## Technical Design

### Architecture

Feature flags implemented as part of settings system with three layers:
1. **Global defaults** - hardcoded safe defaults
2. **Config file** - user overrides in `~/.ragged/config.yml`
3. **Runtime API** - programmatic feature control

### Configuration Schema

```yaml
# ~/.ragged/config.yml
feature_flags:
  # Phase 1: Core Performance
  enable_embedder_caching: false          # v0.2.9-alpha: false, final: true
  enable_batch_auto_tuning: false
  enable_query_caching: true              # Already exists, default true
  enable_advanced_error_recovery: false
  enable_resource_governance: false
  enable_performance_aware_logging: false

  # Phase 2: Operational Excellence
  enable_enhanced_health_checks: false
  enable_async_backpressure: false
  enable_incremental_indexing: false
  enable_observability_dashboard: false
  enable_cold_start_optimisation: false

  # Phase 3: Production Hardening
  enable_graceful_degradation: false
  enable_multi_tier_caching: false
  enable_adaptive_tuning: false
```

### API Interface

```python
# src/config/feature_flags.py

from typing import Dict, Optional
from pydantic import BaseModel, Field

class FeatureFlags(BaseModel):
    """Runtime feature toggles for v0.2.9."""

    # Phase 1
    enable_embedder_caching: bool = Field(default=False)
    enable_batch_auto_tuning: bool = Field(default=False)
    enable_query_caching: bool = Field(default=True)
    enable_advanced_error_recovery: bool = Field(default=False)
    enable_resource_governance: bool = Field(default=False)
    enable_performance_aware_logging: bool = Field(default=False)

    # Phase 2
    enable_enhanced_health_checks: bool = Field(default=False)
    enable_async_backpressure: bool = Field(default=False)
    enable_incremental_indexing: bool = Field(default=False)
    enable_observability_dashboard: bool = Field(default=False)
    enable_cold_start_optimisation: bool = Field(default=False)

    # Phase 3
    enable_graceful_degradation: bool = Field(default=False)
    enable_multi_tier_caching: bool = Field(default=False)
    enable_adaptive_tuning: bool = Field(default=False)

    def is_enabled(self, feature: str) -> bool:
        """Check if feature is enabled."""
        return getattr(self, f"enable_{feature}", False)

    def enable(self, feature: str) -> None:
        """Enable a feature."""
        setattr(self, f"enable_{feature}", True)

    def disable(self, feature: str) -> None:
        """Disable a feature."""
        setattr(self, f"enable_{feature}", False)

# Integrate into Settings
class Settings(BaseSettings):
    # ... existing settings ...
    feature_flags: FeatureFlags = Field(default_factory=FeatureFlags)
```

### CLI Command

```python
# src/cli/commands/feature_flags.py

@click.group()
def feature_flags():
    """Manage feature flags."""
    pass

@feature_flags.command("list")
def list_flags():
    """List all feature flags and their status."""
    settings = get_settings()
    # Display table using Rich

@feature_flags.command("enable")
@click.argument("feature")
def enable_flag(feature: str):
    """Enable a feature flag."""
    # Update config file

@feature_flags.command("disable")
@click.argument("feature")
def disable_flag(feature: str):
    """Disable a feature flag."""
    # Update config file
```

---

## Implementation Details

### Core Components

1. **FeatureFlags Model** (`src/config/feature_flags.py`)
   - Pydantic model with all v0.2.9 flags
   - Validation and type safety
   - Helper methods: `is_enabled()`, `enable()`, `disable()`

2. **Settings Integration** (`src/config/settings.py`)
   - Add `feature_flags: FeatureFlags` field
   - Load from config file
   - Singleton pattern (already exists)

3. **CLI Commands** (`src/cli/commands/feature_flags.py`)
   - `ragged feature-flags list` - show all flags
   - `ragged feature-flags enable <name>` - enable flag
   - `ragged feature-flags disable <name>` - disable flag

4. **Usage Pattern** (throughout codebase)
   ```python
   from src.config import get_settings

   settings = get_settings()
   if settings.feature_flags.enable_embedder_caching:
       # Use cached embedder
   else:
       # Use traditional approach
   ```

### Performance Considerations

- **Target**: Zero overhead when features enabled
- **Approach**: Simple boolean checks (nanosecond cost)
- **Optimisation**: Settings singleton prevents repeated config loading

---

## Edge Cases & Error Handling

### Edge Cases

1. **Invalid feature name**
   - Scenario: User types `ragged feature-flags enable typo`
   - Handling: List valid feature names, suggest closest match

2. **Config file doesn't exist**
   - Scenario: First-time user
   - Handling: Create config file with defaults

3. **Partial config**
   - Scenario: Config file missing some flags
   - Handling: Use defaults for missing flags

### Error Conditions

| Error Type | Trigger | Response | Recovery |
|------------|---------|----------|----------|
| `InvalidFeatureError` | Unknown feature name | Show available features | User corrects |
| `ConfigWriteError` | Can't write config | Show error, suggest manual edit | Manual fix |
| `ValidationError` | Invalid flag value | Show validation error | User corrects |

---

## Testing Requirements

### Unit Tests

- [ ] Test FeatureFlags model creation
- [ ] Test is_enabled() method
- [ ] Test enable/disable methods
- [ ] Test Settings integration
- [ ] Test config file loading
- [ ] Test default values

### Integration Tests

- [ ] Test CLI list command
- [ ] Test CLI enable command
- [ ] Test CLI disable command
- [ ] Test config persistence
- [ ] Test feature usage pattern

### Test Coverage Target

- **Overall**: 95% (simple boolean logic)
- **Critical paths**: 100% (config loading, validation)

---

## Dependencies

### Internal Dependencies

- `src/config/settings.py` - Settings system (exists ✅)
- `src/cli/` - CLI framework (exists ✅)

### External Dependencies

- `pydantic>=2.5.0` - Already installed ✅
- `pyyaml>=6.0.0` - Already installed ✅

---

## Migration & Rollback

### Migration Path

1. Add FeatureFlags to Settings
2. Set all flags to False (safe defaults)
3. Update config schema documentation
4. Add CLI commands

### Rollback Procedure

If feature flags cause issues:
```python
# Disable all v0.2.9 features in config
feature_flags:
  enable_*: false  # All flags OFF
```

### Feature Flag

**This IS the feature flag system** - self-implementing.

---

## Success Metrics

### Functionality Metrics

| Metric | Target |
|--------|--------|
| All v0.2.9 features toggleable | 100% |
| Config file creation | Works |
| CLI commands functional | All 3 working |
| Performance overhead | <1 nanosecond |

### Usability Metrics

- Clear feature names (snake_case, descriptive)
- Intuitive CLI interface
- Good error messages

---

## Timeline

**Estimated**: 2-3 hours

**Breakdown**:
- FeatureFlags model: 30min
- Settings integration: 30min
- CLI commands: 1h
- Tests: 30-60min
- Documentation: 30min

---

## Related Documentation

- [v0.2.9 Roadmap](../README.md)
- [Settings Documentation](../../../../reference/configuration.md)
- [CLI Documentation](../../../../reference/cli.md)

---

**Status**: Specification complete, ready for implementation
