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

---

**Status**: ✅ IMPLEMENTED (commit 4d0bf20)

**Commands Added**:
- `ragged benchmark embedding-init` - Benchmark embedder initialization
- `ragged benchmark batch-embed` - Benchmark batch embedding throughput
- `ragged benchmark query` - Benchmark query performance
- `ragged benchmark memory` - Profile memory usage (add/query/embed)
- `ragged benchmark all` - Run comprehensive benchmark suite

**Implementation**:
- src/cli/commands/benchmark.py (430 lines)
- 5 benchmark subcommands with rich formatting
- Integration with existing src/utils/benchmarks.py framework
- Memory profiling via tracemalloc
- Statistical analysis and performance rating

**Features**:
- Configurable runs and warmup iterations
- Throughput calculations
- Memory allocation tracking
- Color-coded performance ratings
- Detailed profiling modes
