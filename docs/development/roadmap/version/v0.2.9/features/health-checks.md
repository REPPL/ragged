# Enhanced Health Checks with Deep Diagnostics

**Phase**: 2 | **Effort**: 3-4h | **Priority**: MUST-HAVE

**Current**: Basic health check exists (`src/cli/commands/health.py` - 52 lines)

**Enhancement**: Add deep diagnostics, performance validation, proactive issue detection

**Implementation**:
```python
@click.command()
@click.option("--deep", is_flag=True, help="Run deep diagnostics")
def health(deep: bool):
    checks = [
        check_ollama(),
        check_chromadb(),
        check_embedder(),          # NEW: embedder init time
        check_disk_space(),         # NEW: storage capacity
        check_memory_available(),   # NEW: RAM check
        check_cache_status(),       # NEW: cache health
    ]

    if deep:
        checks.extend([
            check_query_performance(),  # NEW: run test query
            check_index_integrity(),    # NEW: validate indices
            check_network_latency(),    # NEW: service latency
        ])
```

**Success**: All services validated, performance baselines checked, issues detected proactively

**Timeline**: 3-4h
