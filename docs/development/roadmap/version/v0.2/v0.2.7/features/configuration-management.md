# Configuration Management (v0.2.7)

This document details the configuration management improvements planned for v0.2.7.

**Total Estimated Time**: 10 hours

**Related Documentation:** [Main v0.2.7 Roadmap](../README.md)

---


## Part 3: Configuration Management (10 hours)

### CONFIG-001: Runtime Configuration Updates

**Priority**: Medium
**Estimated Time**: 4 hours

Allow config updates without file editing:
```python
ragged config set chunk_size 600  # Immediate effect
ragged config set retrieval_k 10  # Persists to file
ragged config reset chunk_size   # Back to default
ragged config validate           # Check all settings
```

### CONFIG-002: Configuration Profiles

**Priority**: Medium
**Estimated Time**: 6 hours

Create and switch between config profiles:
```python
ragged config profile create fast
ragged config profile use fast
ragged config set chunk_size 300 --profile fast

ragged query "..." --profile fast
```


---

## Related Documentation

- [Main v0.2.7 Roadmap](../README.md)
- [UX Improvements](./ux-improvements.md)
- [CLI Enhancements](./cli-enhancements.md)
- [Performance Optimisations](./performance-optimisations.md)

---
