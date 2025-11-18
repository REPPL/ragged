# Performance Profiling Tools Integration

**Phase**: 3 | **Effort**: 4-5h | **Priority**: MUST-HAVE

**Current**: Benchmarking framework exists (`src/utils/benchmarks.py` - 401 lines)

**Integration**: Add CLI commands

**Implementation**:
```python
@click.group()
def benchmark():
    """Performance benchmarking commands."""
    pass

@benchmark.command("embedding-init")
@click.option("--runs", default=10)
def bench_embedding_init(runs):
    """Benchmark embedder initialisation."""
    bench = Benchmark("embedding-init", warmup=0, iterations=runs)
    result = bench.run(create_embedder)
    print(f"Mean: {result.mean:.3f}s")

@benchmark.command("profile-memory")
@click.argument("operation")
def profile_memory(operation):
    """Profile memory usage of operation."""
    # Use memory_profiler or tracemalloc
```

**Success**: `ragged benchmark` and `ragged profile-memory` working

**Timeline**: 4-5h
