# Operational Observability Dashboard

**Phase**: 2 | **Effort**: 3-4h | **Priority**: MUST-HAVE

**New**: CLI command `ragged monitor` for live metrics

**Implementation**:
```python
@click.command()
def monitor():
    """Live performance dashboard."""
    with Live(refresh_per_second=1) as live:
        while True:
            metrics = collect_metrics()
            table = create_metrics_table(metrics)
            live.update(table)
            time.sleep(1)

def collect_metrics():
    return {
        "cache_hit_rate": get_cache_stats(),
        "embedder_latency": get_embedder_metrics(),
        "memory_usage": psutil.virtual_memory().percent,
        "active_operations": get_active_ops(),
    }
```

**Success**: Real-time visibility, Prometheus export support

**Timeline**: 3-4h

---

**Status**: ✅ IMPLEMENTED (commit 9d31e3f)
