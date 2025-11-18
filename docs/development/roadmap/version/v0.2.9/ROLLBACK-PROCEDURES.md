# v0.2.9 Rollback Procedures

**Purpose**: Step-by-step procedures for safely rolling back v0.2.9 features if critical issues are discovered.

**Philosophy**: Every optimisation can be disabled. No feature is worth production instability.

---

## Rollback Decision Framework

### When to Rollback

**Immediate rollback required** if:
- Data corruption detected
- Critical security vulnerability discovered
- Error rate >10% (10x normal)
- Performance degradation >50%
- Complete service outage

**Consider rollback** if:
- Error rate >5% (sustained for >1 hour)
- Performance degradation >25%
- Memory leaks causing OOM crashes
- Multiple critical bugs discovered
- User reports indicate widespread issues

**Monitor but don't rollback** if:
- Minor bugs affecting edge cases
- Performance improvement less than expected but no regression
- Non-critical features not working perfectly
- Issues fixed by configuration changes

---

## Rollback Types

### Type 1: Feature Flag Rollback (Fastest)

**Duration**: Minutes
**Risk**: Minimal
**Scope**: Individual features

Disable specific features via configuration without code changes.

### Type 2: Configuration Rollback (Fast)

**Duration**: Minutes to hours
**Risk**: Low
**Scope**: Behaviour changes

Revert configuration to safe defaults.

### Type 3: Version Rollback (Full)

**Duration**: Hours
**Risk**: Medium (requires redeployment)
**Scope**: Complete rollback to v0.2.8

Revert entire deployment to previous stable version.

### Type 4: Data Rollback (Complex)

**Duration**: Hours to days
**Risk**: High (potential data loss)
**Scope**: Restore from backups

Only if data corruption detected. Last resort.

---

## Feature-by-Feature Rollback Procedures

### Phase 0: Foundation Features

#### Feature Flag Framework

**Rollback Strategy**: N/A (framework itself is the rollback mechanism)

**If framework has issues**:
1. Remove feature flag checks (revert to default behaviour)
2. Deploy emergency patch
3. Investigate framework issues offline

---

#### Performance Regression Tests

**Rollback Strategy**: N/A (testing infrastructure)

**If tests are flaky**:
1. Disable failing tests temporarily
2. Continue manual performance validation
3. Fix tests offline

---

### Phase 1: Core Performance Features

#### 1. Embedder Caching with Progressive Warm-Up

**Feature Flag**: `enable_embedder_caching` (default: true)

**Rollback Procedure**:
```bash
# 1. Disable via feature flag
ragged config set feature_flags.enable_embedder_caching false

# 2. Verify rollback
ragged health-check --verbose

# 3. Clear any cached models (if corruption suspected)
rm -rf ~/.cache/ragged/models/

# 4. Restart ragged (if daemon mode)
ragged daemon restart
```

**Validation**:
- Embedder init time returns to baseline (~2-3s)
- No more caching-related errors
- Memory usage stable

**When to rollback**:
- Memory leaks from cached models
- Model corruption in cache
- Cache invalidation bugs causing wrong embeddings

---

#### 2. Intelligent Batch Auto-Tuning

**Feature Flag**: `enable_batch_auto_tuning` (default: true)

**Rollback Procedure**:
```bash
# 1. Disable auto-tuning
ragged config set feature_flags.enable_batch_auto_tuning false

# 2. Set static batch size (safe default)
ragged config set embedding.batch_size 32

# 3. Verify behaviour
ragged add test_document.txt --verbose
```

**Validation**:
- Batch size fixed at configured value
- No OOM crashes
- Predictable memory usage

**When to rollback**:
- Auto-tuning causes OOM crashes
- Performance worse than static batching
- Unpredictable resource usage

---

#### 3. Query Result Caching (Already Implemented)

**Feature Flag**: `enable_query_caching` (default: true)

**Rollback Procedure**:
```bash
# 1. Disable query caching
ragged config set feature_flags.enable_query_caching false

# 2. Clear cache
ragged cache clear --query-cache

# 3. Verify queries still work
ragged query "test query"
```

**Validation**:
- Queries slower but correct
- No cache-related errors

**When to rollback**:
- Stale cache causing incorrect results
- Cache invalidation bugs

---

#### 4. Advanced Error Recovery

**Feature Flag**: `enable_advanced_error_recovery` (default: true)

**Rollback Procedure**:
```bash
# 1. Disable advanced recovery
ragged config set feature_flags.enable_advanced_error_recovery false

# 2. Revert to simple error handling (fail-fast)
ragged config set error_handling.mode "simple"

# 3. Test error scenarios
# (Manually test expected errors)
```

**Validation**:
- Errors fail immediately (no retry)
- Simpler error behaviour

**When to rollback**:
- Retry loops causing system hangs
- Circuit breaker malfunctioning
- Recovery causing more problems than failures

---

#### 5. Resource Governance System

**Feature Flag**: `enable_resource_governance` (default: true)

**Rollback Procedure**:
```bash
# 1. Disable resource governance
ragged config set feature_flags.enable_resource_governance false

# 2. Remove resource limits
ragged config set resource_limits.mode "unlimited"

# 3. Monitor for OOM
# (Be prepared to manually kill runaway processes)
```

**Validation**:
- No resource limits enforced
- Operations complete without governance overhead

**When to rollback**:
- False OOM prevention (killing valid operations)
- Resource governance overhead too high
- Governance logic buggy

---

#### 6. Performance-Aware Logging

**Feature Flag**: `enable_performance_aware_logging` (default: true)

**Rollback Procedure**:
```bash
# 1. Disable performance-aware features
ragged config set feature_flags.enable_performance_aware_logging false

# 2. Revert to synchronous logging
ragged config set logging.async false

# 3. Set log level to WARNING (reduce volume)
ragged config set logging.level "WARNING"
```

**Validation**:
- All logs written synchronously
- No log sampling
- Logging is verbose but safe

**When to rollback**:
- Async logging dropping important logs
- Log sampling hiding critical errors
- Performance-aware logic causing issues

---

### Phase 2: Operational Excellence Features

#### 7. Enhanced Health Checks

**Feature Flag**: `enable_enhanced_health_checks` (default: true)

**Rollback Procedure**:
```bash
# 1. Disable enhanced checks
ragged config set feature_flags.enable_enhanced_health_checks false

# 2. Revert to basic health check
ragged health-check --basic-only
```

**When to rollback**:
- Health checks themselves causing performance issues
- False positives in diagnostics

---

#### 8. Async Operations with Backpressure

**Feature Flag**: `enable_async_operations` (default: true)

**Rollback Procedure**:
```bash
# 1. Disable async operations
ragged config set feature_flags.enable_async_operations false

# 2. Revert to synchronous processing
ragged config set processing.mode "synchronous"

# 3. Test ingestion
ragged add /test/directory --verbose
```

**Validation**:
- Operations run sequentially
- Slower but stable

**When to rollback**:
- Race conditions causing data corruption
- Deadlocks in async operations
- Backpressure logic malfunctioning

---

#### 9. Incremental Index Operations

**Feature Flag**: `enable_incremental_indexing` (default: true)

**Rollback Procedure**:
```bash
# 1. Disable incremental updates
ragged config set feature_flags.enable_incremental_indexing false

# 2. Force full index rebuild
ragged index rebuild --full

# 3. Verify index integrity
ragged index validate
```

**Validation**:
- All index updates do full rebuild
- Index integrity maintained

**When to rollback**:
- Index corruption from incremental updates
- Incremental updates slower than full rebuild
- Index inconsistencies

---

#### 10. Operational Observability Dashboard

**Feature Flag**: `enable_observability_dashboard` (default: true)

**Rollback Procedure**:
```bash
# 1. Disable dashboard
ragged config set feature_flags.enable_observability_dashboard false

# 2. Stop monitoring if running
ragged monitor stop
```

**When to rollback**:
- Dashboard causing performance overhead
- Metrics collection impacting operations

---

#### 11. Cold Start Holistic Optimisation

**Feature Flag**: `enable_cold_start_optimisation` (default: true)

**Rollback Procedure**:
```bash
# 1. Disable cold start optimisations
ragged config set feature_flags.enable_cold_start_optimisation false

# 2. Revert to sequential initialisation
ragged config set startup.mode "sequential"

# 3. Clear any cached startup state
rm -rf ~/.cache/ragged/startup/
```

**When to rollback**:
- Parallel initialisation causing startup crashes
- Connection pooling issues
- Lazy initialisation breaking functionality

---

### Phase 3: Production Hardening Features

#### 12-16. Testing, Profiling, Degradation, Caching, Tuning

**Most Phase 3 features** are infrastructure/tools with minimal runtime impact.

**Rollback**: Disable via feature flags if causing issues
**Validation**: Core functionality unaffected

---

## Complete Version Rollback: v0.2.9 → v0.2.8

**Only if feature-level rollbacks insufficient**

### Preparation (Do Before v0.2.9 Deployment)

```bash
# 1. Tag v0.2.8 (if not already)
git tag -a v0.2.8 -m "Last stable before v0.2.9"

# 2. Backup configuration
cp ~/.config/ragged/config.yaml ~/.config/ragged/config.v0.2.8.yaml

# 3. Backup data (if applicable)
ragged export --all --output ragged_backup_v0.2.8.json

# 4. Document deployment state
ragged health-check > health_v0.2.8.txt
```

### Rollback Procedure

```bash
# 1. Verify v0.2.8 availability
git checkout v0.2.8

# 2. Rebuild and install
pip uninstall ragged
pip install -e .

# 3. Restore configuration
cp ~/.config/ragged/config.v0.2.8.yaml ~/.config/ragged/config.yaml

# 4. Verify rollback
ragged --version  # Should show v0.2.8
ragged health-check --verbose

# 5. Test basic operations
ragged query "test query"
ragged add test_document.txt
```

### Validation

- [ ] Version confirms v0.2.8
- [ ] All basic commands working
- [ ] Configuration valid
- [ ] Data accessible
- [ ] No v0.2.9 errors

### Post-Rollback

1. **Communication**:
   - Notify users of rollback
   - Explain reason and timeline

2. **Investigation**:
   - Collect logs from v0.2.9
   - Identify root cause
   - Create bug reports

3. **Planning**:
   - Decide: fix and re-release or skip to v0.3.0?
   - Update roadmap
   - Communicate plan

---

## Data Rollback (Emergency Only)

**Only if data corruption detected and cannot be fixed forward**

### Procedure

```bash
# 1. STOP ALL OPERATIONS IMMEDIATELY
ragged daemon stop

# 2. Assess corruption extent
ragged validate --all --verbose > corruption_report.txt

# 3. Restore from most recent backup
ragged import ragged_backup_v0.2.8.json

# 4. Verify data integrity
ragged validate --all

# 5. Document what was lost
# (Any data added after backup is lost)
```

### Data Loss Assessment

- Identify time range of data loss
- Notify affected users
- Document recovery process

---

## Configuration Defaults for Safe Rollback

**Safe configuration** (all optimisations disabled):

```yaml
feature_flags:
  enable_embedder_caching: false
  enable_batch_auto_tuning: false
  enable_query_caching: false
  enable_advanced_error_recovery: false
  enable_resource_governance: false
  enable_performance_aware_logging: false
  enable_enhanced_health_checks: false
  enable_async_operations: false
  enable_incremental_indexing: false
  enable_observability_dashboard: false
  enable_cold_start_optimisation: false

embedding:
  batch_size: 32  # Safe static size

processing:
  mode: "synchronous"

logging:
  level: "WARNING"
  async: false

resource_limits:
  mode: "unlimited"

error_handling:
  mode: "simple"
```

**Save as**: `config.safe_mode.yaml`

**Activate safe mode**:
```bash
cp ~/.config/ragged/config.safe_mode.yaml ~/.config/ragged/config.yaml
ragged daemon restart
```

---

## Rollback Testing

**Before v0.2.9 release**, test all rollback procedures:

- [ ] Test each feature flag rollback
- [ ] Test configuration rollback
- [ ] Test complete version rollback
- [ ] Test safe mode activation
- [ ] Verify data integrity after rollback
- [ ] Document rollback timing (how long does each take?)

---

## Post-Rollback Checklist

After any rollback:

- [ ] Verify system stability
- [ ] Verify data integrity
- [ ] Collect logs and diagnostics
- [ ] Identify root cause
- [ ] Update risk playbook
- [ ] Communicate to stakeholders
- [ ] Plan fix or alternative approach
- [ ] Update documentation with lessons learned

---

## Emergency Contacts

**During rollback emergency**:

1. **Technical Lead**: [Name/Contact]
2. **On-Call Engineer**: [Name/Contact]
3. **Escalation**: [Name/Contact]

**Communication Channels**:
- GitHub Issues: [URL]
- Discord/Slack: [Channel]
- Email: [support email]

---

## Related Documentation

- [v0.2.9 Roadmap](./README.md) - Features being rolled back
- [Risk Mitigation Playbook](./RISK-MITIGATION.md) - Why rollback might be needed
- [Production Readiness Checklist](./PRODUCTION-READINESS.md) - Prevent need for rollback
- [Feature Specifications](./features/README.md) - Feature details

---

**Status**: Ready for validation (test procedures before release)

**Last Updated**: 2025-11-18
