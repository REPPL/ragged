# Hardware Optimisation Implementation Roadmap

**Feature:** Hardware Optimisation

**Status:** Planned

**Versions:** v0.1 - v1.0

**Last Updated:** 2025-11-15

---

## Overview

This roadmap details the phased implementation of hardware optimisation features for ragged. The implementation spans from basic hardware detection in v0.1 through dynamic performance monitoring in v1.0.

**Related Design:** [Hardware Optimisation Strategy](../../planning/core-concepts/hardware-optimisation.md)

---

## Phase 1: Basic Detection (v0.1)

**Target Version:** v0.1

**Goal:** Detect hardware and display capabilities

**Effort:** 5-8 hours

### Features

- Detect CPU, RAM, GPU using `psutil` and `torch`
- Identify Apple Silicon vs. NVIDIA vs. CPU
- Display hardware summary on startup
- Basic Ollama integration

### Implementation

```python
# On startup
hardware = HardwareDetector.detect()
print(f"Detected: {hardware}")

# Use single recommended model
if hardware.accelerator == 'mps' and hardware.total_ram_gb >= 100:
    default_model = "llama3.3:70b-q4"
elif hardware.accelerator == 'cuda' and hardware.gpu_memory_gb >= 20:
    default_model = "qwen2.5:32b-q4"
else:
    default_model = "llama3.2:8b-q6"
```

### Deliverables

- `HardwareDetector` class
- `HardwareProfile` dataclass
- Startup hardware display
- Basic model selection logic

### Success Criteria

- Correctly identifies hardware type (Apple Silicon / NVIDIA / CPU)
- Displays total RAM and GPU memory
- Recommends appropriate default model

---

## Phase 2: Model Recommendations (v0.2)

**Target Version:** v0.2

**Goal:** Recommend optimal models for detected hardware

**Effort:** 8-12 hours

### Features

- Calculate effective memory
- Recommend Fast/Balanced/Quality tiers
- Display model recommendations with expected performance
- Warn if insufficient resources

### Implementation

```python
# Get recommendations
recommendations = ModelSelector.recommend_models(hardware)

# Display
print("\nRecommended models for your hardware:")
for tier, config in recommendations['recommendations'].items():
    print(f"  {tier.title()}: {config['model']} "
          f"(~{config['expected_tokens_per_sec']:.0f} t/s, "
          f"{config['memory_gb']}GB)")
```

### Deliverables

- `ModelSelector` class with model database
- Three-tier recommendation system (Fast/Balanced/Quality)
- Expected performance calculations
- Insufficient memory warnings

### Success Criteria

- Recommends models that fit in available memory
- Provides three tiers when hardware allows
- Accurate performance estimates
- Helpful warnings for insufficient hardware

---

## Phase 3: Automatic Configuration (v0.3)

**Target Version:** v0.3

**Goal:** Configure Ollama and ChromaDB automatically

**Effort:** 10-15 hours

### Features

- Generate Ollama environment variables
- Configure ChromaDB for hardware
- Adjust batch sizes for embedding generation
- Context window recommendations

### Implementation

```python
# Generate configuration
config = ConfigGenerator.generate(hardware, recommendations)

# Save to ~/.ragged/config.yaml
config_path = Path.home() / ".ragged" / "config.yaml"
config_path.write_text(yaml.dump(config))

# Apply to environment
for key, value in config['environment'].items():
    os.environ[key] = str(value)
```

### Deliverables

- `ConfigGenerator` class
- Hardware-specific Ollama configuration
- ChromaDB HNSW parameter tuning
- Automatic config file generation (`~/.ragged/config.yaml`)
- Environment variable application

### Success Criteria

- Ollama configured optimally for hardware type
- ChromaDB tuned for expected workload size
- Batch sizes appropriate for available memory
- Configuration persists across sessions

---

## Phase 4: Dynamic Optimisation (v1.0)

**Target Version:** v1.0

**Goal:** Monitor and optimise performance in production

**Effort:** 15-20 hours

### Features

- Memory usage monitoring
- Performance metrics (latency, throughput)
- Automatic model unloading under memory pressure
- Adaptive batch sizing
- Performance regression detection

### Implementation

```python
class PerformanceMonitor:
    """Monitor and optimise RAG performance"""

    def __init__(self):
        self.metrics = {
            'retrieval_latency': [],
            'generation_latency': [],
            'memory_usage': [],
            'throughput': [],
        }

    def record_query(self, latency: float, memory_used: float):
        """Record query metrics"""
        self.metrics['generation_latency'].append(latency)
        self.metrics['memory_usage'].append(memory_used)

        # Check for issues
        if latency > 10.0:
            logger.warning(f"High latency detected: {latency:.2f}s")

        if memory_used > 100:  # GB
            logger.warning("High memory usage, consider unloading models")

    def get_summary(self) -> dict:
        """Get performance summary"""
        return {
            'avg_latency': np.mean(self.metrics['generation_latency']),
            'p95_latency': np.percentile(self.metrics['generation_latency'], 95),
            'avg_memory': np.mean(self.metrics['memory_usage']),
        }
```

### Deliverables

- `PerformanceMonitor` class
- Real-time memory tracking
- Latency and throughput metrics
- Automatic model unloading (LRU strategy)
- Adaptive batch sizing based on load
- Performance dashboard/summary

### Success Criteria

- Memory usage stays within budget
- Models automatically unloaded when memory pressure detected
- Performance metrics collected and reported
- Batch sizes adapt to current memory availability
- Early warning for performance degradation

---

## Configuration File Format

### Hardware Configuration (Auto-Generated)

**Location:** `~/.ragged/hardware.yaml`

```yaml
hardware:
  platform: Darwin
  cpu_cores: 16
  total_ram_gb: 128.0
  accelerator: mps
  gpu_type: Apple Silicon
  effective_memory_gb: 89.6

models:
  quality:
    name: llama3.3:70b-instruct-q4_K_M
    memory_gb: 45
    expected_tokens_per_sec: 10-12
    context_window: 32768

  balanced:
    name: qwen2.5:32b-instruct-q5_K_M
    memory_gb: 22
    expected_tokens_per_sec: 22-25
    context_window: 32768

  fast:
    name: llama3.2:8b-instruct-q6_K
    memory_gb: 6
    expected_tokens_per_sec: 65-70
    context_window: 32768

embedding:
  name: nomic-embed-text
  dimensions: 768
  context_window: 8192
  batch_size: 100

ollama:
  environment:
    OLLAMA_METAL: "1"
    OLLAMA_MAX_LOADED_MODELS: "2"
    OLLAMA_NUM_THREADS: "16"
    OLLAMA_NUM_PARALLEL: "4"

chromadb:
  persist_directory: ~/.ragged/chroma_db
  hnsw_construction_ef: 200
  hnsw_search_ef: 100
  hnsw_M: 16

performance:
  embedding_batch_size: 100
  max_concurrent_models: 2
  memory_safety_margin_gb: 10
  context_window_limits:
    70b_q4: 32768
    34b_q5: 65536
    13b_q6: 131072
```

---

## Cumulative Effort Estimates

| Phase | Version | Features | Effort (hours) | Cumulative (hours) |
|-------|---------|----------|----------------|--------------------|
| 1 | v0.1 | Basic Detection | 5-8 | 5-8 |
| 2 | v0.2 | Model Recommendations | 8-12 | 13-20 |
| 3 | v0.3 | Automatic Configuration | 10-15 | 23-35 |
| 4 | v1.0 | Dynamic Optimisation | 15-20 | 38-55 |

**Total Implementation Effort:** 38-55 hours across 4 versions

---

## Dependencies

### Python Packages

- `psutil` - CPU/RAM detection
- `torch` - GPU detection (CUDA/MPS)
- `pyyaml` - Configuration file I/O
- `numpy` - Performance metrics (Phase 4)

### External Services

- Ollama - LLM serving
- ChromaDB - Vector storage

---

## Testing Requirements

### Phase 1 (v0.1)

- Unit tests for `HardwareDetector.detect()`
- Test on: Mac (Apple Silicon), Windows (NVIDIA), Linux (CPU-only)
- Verify correct accelerator detection

### Phase 2 (v0.2)

- Unit tests for `ModelSelector.recommend_models()`
- Test with various memory configurations (16GB, 32GB, 64GB, 128GB)
- Verify tier logic (Fast/Balanced/Quality)

### Phase 3 (v0.3)

- Integration tests for config generation
- Verify Ollama env vars are correctly set
- Test config persistence across restarts

### Phase 4 (v1.0)

- Performance monitoring tests
- Memory pressure simulation
- LRU eviction verification
- Metrics accuracy validation

---

## Success Metrics

### User Experience

- **v0.1:** User sees their hardware detected and displayed
- **v0.2:** User receives 3 model recommendations with performance estimates
- **v0.3:** User's Ollama/ChromaDB are configured automatically
- **v1.0:** User experiences consistent performance without manual intervention

### Technical

- **v0.1:** 100% hardware detection accuracy across platforms
- **v0.2:** Model recommendations fit in available memory 100% of time
- **v0.3:** Generated configuration achieves 90%+ of theoretical performance
- **v1.0:** Memory usage stays within budget 95%+ of time

---

## Future Enhancements (Post v1.0)

### Multi-GPU Support

- Distribute model layers across multiple GPUs
- Load balancing for concurrent requests

### Cloud GPU Integration

- Support for cloud-hosted GPUs (Vast.ai, RunPod)
- Automatic provisioning based on workload

### Model Benchmarking

- Automatic performance benchmarking on first run
- Update model database with actual measured performance

### Hardware Upgrade Recommendations

- Identify performance bottlenecks
- Suggest specific hardware upgrades
- Cost/benefit analysis for different upgrade paths

---

## Related Documentation

- [Hardware Optimisation Strategy](../../planning/core-concepts/hardware-optimisation.md) - Complete design specification
- [Model Selection](../../planning/core-concepts/model-selection.md) - Model selection strategies
- [Configuration System](../../planning/architecture/configuration-system.md) - Configuration architecture
- [v0.2 Roadmap](../version/v0.2/) - Overall v0.2 features

---


**License:** GPL-3.0
