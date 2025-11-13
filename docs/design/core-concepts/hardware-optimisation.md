# Hardware Optimisation Strategy

**Version**: 2.0
**Last Updated**: 2025-11-09
**Status**: Design Complete
**Implementation Target**: v0.2+

---

## Table of Contents

1. [Overview](#overview)
2. [Primary Platform: Mac Studio M4 Max](#primary-platform-mac-studio-m4-max)
3. [Cross-Platform Support](#cross-platform-support)
4. [Automatic Hardware Detection](#automatic-hardware-detection)
5. [Model Selection by Hardware](#model-selection-by-hardware)
6. [Memory Management](#memory-management)
7. [Performance Optimisation](#performance-optimisation)
8. [Implementation Roadmap](#implementation-roadmap)

---

## Overview

### Purpose

ragged's hardware optimisation strategy ensures optimal performance across diverse hardware configurations, from entry-level MacBooks to high-end Mac Studios and NVIDIA GPU systems. The design prioritises the **Mac Studio M4 Max (128GB unified memory)** as the primary development and testing platform whilst maintaining broad compatibility.

### Design Principles

1. **Automatic Adaptation**: Detect hardware capabilities and recommend optimal configurations
2. **Transparent Performance**: Users understand speed/quality trade-offs for their hardware
3. **Graceful Degradation**: System works on modest hardware, excels on premium hardware
4. **Privacy-First**: All processing local, no cloud dependencies required
5. **Cross-Platform**: Support macOS (Apple Silicon), Windows/Linux (NVIDIA, CPU)

### Key Features

- **Hardware Auto-Detection**: Identify CPU, RAM, GPU capabilities automatically
- **Model Recommendations**: Suggest optimal models for detected hardware
- **Performance Tiers**: Fast/Balanced/Quality tiers adapt to available resources
- **Memory-Aware Loading**: Prevent OOM errors through intelligent memory management
- **Quantisation Selection**: Automatic quantisation level based on available memory

---

## Primary Platform: Mac Studio M4 Max

### Hardware Specifications

```
Mac Studio M4 Max (128GB Configuration)
├── CPU: 16-core (12 performance + 4 efficiency)
├── GPU: 40-core with Metal acceleration
├── Neural Engine: 16-core ML inference
├── Unified Memory: 128GB @ 273GB/s bandwidth
├── Architecture: Unified memory (CPU/GPU shared)
└── TDP: ~100W typical, ~200W maximum
```

### Performance Characteristics

**Model Performance (Measured 2025)**:

| Model Size | Quantisation | Memory Usage | Tokens/Second | Context Window |
|------------|--------------|--------------|---------------|----------------|
| 70B        | Q4_K_M       | ~45 GB       | 10-12 t/s     | 32K safe       |
| 70B        | Q5_K_M       | ~50 GB       | 10-11 t/s     | 24K safe       |
| 34B        | Q5_K_M       | ~25 GB       | 22-25 t/s     | 64K possible   |
| 13B        | Q6_K         | ~10 GB       | 45-50 t/s     | 128K possible  |
| 8B         | Q6_K         | ~6 GB        | 65-70 t/s     | 32K safe       |
| 7B         | Q8_0         | ~7 GB        | 65-70 t/s     | 8K safe        |

**Embedding Performance**:
- nomic-embed-text (768 dim): ~50-60 docs/sec (batch 100)
- mxbai-embed-large (1024 dim): ~35-40 docs/sec (batch 100)

### Optimal Configuration

**Recommended Model Stack**:

```yaml
quality_tier:
  llm:
    general: "llama3.3:70b-instruct-q4_K_M"
    reasoning: "deepseek-r1:70b-q4_K_M"
    memory: 45 GB
    speed: 10-12 t/s
    context: 32768

balanced_tier:
  llm:
    general: "qwen2.5:32b-instruct-q5_K_M"
    coding: "qwen2.5-coder:32b-instruct-q5_K_M"
    memory: 25 GB
    speed: 22-25 t/s
    context: 32768

fast_tier:
  llm:
    general: "llama3.2:8b-instruct-q6_K"
    quick: "mistral:7b-instruct-q4_K_M"
    memory: 6 GB
    speed: 65-70 t/s
    context: 32768

embedding:
  model: "nomic-embed-text"
  dimensions: 768
  context_window: 8192
  memory: 0.8 GB
  speed: 50-60 docs/sec
```

### Memory Budget (128GB System)

**Typical RAG Workload**:

```
Component                     Memory Usage
─────────────────────────────────────────────
Primary LLM (70B Q4)          45 GB
LLM Context Cache (16K)       5 GB
Embedding Model               1 GB
ChromaDB Index (100K docs)    8 GB
ChromaDB Vectors              3 GB
Kuzu Graph Database           2 GB
Application + Python          5 GB
System + macOS                15 GB
─────────────────────────────────────────────
Total Used                    84 GB
Available Buffer              44 GB (34%)
─────────────────────────────────────────────
```

**Concurrent Model Loading** (Possible):
- Primary LLM (70B Q4): 45 GB
- Secondary LLM (13B Q6) for fast queries: 10 GB
- Embedding model: 1 GB
- Total: 56 GB (still 72 GB free)

### Advantages Over Alternatives

**vs. NVIDIA RTX 4090 (24GB VRAM)**:
- ✅ Can run larger models (70B vs. 34B maximum)
- ✅ Unified memory (no CPU↔GPU transfer overhead)
- ✅ Silent operation (vs. active cooling)
- ✅ Lower power consumption (100W vs. 450W)
- ❌ Slower per-token (10-12 vs. 30-40 t/s)
- ❌ Higher upfront cost (£4,000 vs. £1,600)

**vs. Mac mini M4 Pro (64GB)**:
- ✅ Larger models (70B Q4 vs. tight fit)
- ✅ More comfortable context windows (32K vs. 8K for 70B)
- ✅ Can load multiple models concurrently
- ❌ Higher cost (£4,000 vs. £2,200)

**Recommendation**: Mac Studio M4 Max 128GB is **optimal** for serious local RAG work, balancing capability, efficiency, and future-proofing.

---

## Cross-Platform Support

### Hardware Tier Matrix

| Tier | Hardware | RAM/VRAM | Max Model Size | Speed | Price |
|------|----------|----------|----------------|-------|-------|
| **Ultra Premium** | | | | | |
| Mac Studio M4 Max | 128GB unified | 70B Q4-Q6 | 10-14 t/s | £4,000 |
| Mac Studio M3 Ultra | 512GB unified | 671B (quantised) | Varies | £8,000+ |
| NVIDIA RTX 5090 | 32GB VRAM | 32B dense, 70B Q4 | 60-213 t/s | £2,000 |
| **Premium** | | | | | |
| Mac mini M4 Pro | 64GB unified | 70B Q4, 34B Q5 | 8-12 t/s | £2,200 |
| MacBook Pro M4 Max | 128GB unified | 70B Q4-Q6 | 10-14 t/s | £4,500 |
| NVIDIA RTX 4090 | 24GB VRAM | 34B, 70B Q4 | 45-82 t/s | £1,600 |
| **Mid-Range** | | | | | |
| MacBook Pro M4 Pro | 48GB unified | 34B Q4, 13B Q6 | 15-30 t/s | £3,000 |
| Mac mini M4 | 32GB unified | 13B Q5, 7B Q8 | 40-60 t/s | £1,200 |
| NVIDIA RTX 4070 Ti | 12GB VRAM | 13B Q4, 7B Q6 | 45-62 t/s | £800 |
| **Entry Level** | | | | | |
| MacBook Pro M4 | 16GB unified | 7B Q4-Q6 | 40-50 t/s | £1,600 |
| NVIDIA RTX 3060 | 12GB VRAM | 13B Q4, 7B Q6 | 30-40 t/s | £300 |
| CPU Only (Intel/AMD) | 16GB+ | 7B Q4 | 7-10 t/s | Varies |

### Platform-Specific Optimisations

**macOS (Apple Silicon)**:

```python
# Ollama configuration for Apple Silicon
os.environ['OLLAMA_METAL'] = '1'              # Enable Metal acceleration
os.environ['OLLAMA_MAX_LOADED_MODELS'] = '2'  # Allow embedding + LLM
os.environ['OLLAMA_NUM_THREADS'] = '16'       # Physical cores

# Memory management
EFFECTIVE_MEMORY_GB = total_ram_gb * 0.70     # Use 70% for models
SAFETY_MARGIN_GB = 10                         # Reserve for system
```

**Windows/Linux (NVIDIA CUDA)**:

```python
# Ollama configuration for NVIDIA GPUs
os.environ['OLLAMA_NUM_GPU'] = '999'          # Use all GPU layers
os.environ['OLLAMA_GPU_OVERHEAD'] = '2400'    # 10-15% VRAM overhead (MB)
os.environ['OLLAMA_MAX_LOADED_MODELS'] = '1'  # Single model for best performance

# Memory management
EFFECTIVE_MEMORY_GB = gpu_vram_gb             # Use GPU VRAM
SAFETY_MARGIN_GB = gpu_vram_gb * 0.10         # 10% safety margin
```

**CPU Only (Fallback)**:

```python
# Ollama configuration for CPU-only
os.environ['OLLAMA_NUM_GPU'] = '0'            # Disable GPU
os.environ['OLLAMA_NUM_THREADS'] = str(cpu_physical_cores)
os.environ['OLLAMA_MAX_LOADED_MODELS'] = '1'

# Memory management
EFFECTIVE_MEMORY_GB = total_ram_gb * 0.50     # Use 50% for models
SAFETY_MARGIN_GB = 5                          # Minimal safety margin
```

### Quantisation Trade-offs

**Quality vs. Size Comparison** (relative to FP16 baseline):

| Quantisation | Size | Quality Loss | Use Case | Perplexity Impact |
|--------------|------|--------------|----------|-------------------|
| Q8_0         | 50%  | <1%          | Maximum quality, plenty of memory | +0.01 ppl |
| Q6_K         | 40%  | ~1-2%        | High quality, large memory | +0.02 ppl |
| Q5_K_M       | 36%  | ~2-3%        | Balanced quality/size | +0.0353 ppl |
| **Q4_K_M**   | **30%** | **~3-5%** | **RECOMMENDED - Best balance** | +0.0535 ppl |
| Q4_K_S       | 28%  | ~5-7%        | Memory constrained | +0.06 ppl |
| Q3_K_M       | 25%  | ~8-10%       | Extreme memory limits | +0.08+ ppl |

**Recommendation**: Use **Q4_K_M** as default unless:
- Abundant memory (>100GB) → Q5_K_M or Q6_K for higher quality
- Limited memory (<32GB) → Q4_K_S for smaller models
- Maximum quality required → Q8_0 or Q6_K

---

## Automatic Hardware Detection

### Implementation

```python
import platform
import psutil
import torch
from dataclasses import dataclass
from typing import Optional

@dataclass
class HardwareProfile:
    """Hardware capabilities profile"""
    platform: str              # 'Darwin', 'Windows', 'Linux'
    cpu_physical_cores: int
    cpu_logical_cores: int
    total_ram_gb: float
    available_ram_gb: float
    gpu_type: Optional[str]
    gpu_memory_gb: float
    accelerator: str           # 'cuda', 'mps', 'cpu'
    gpu_count: int = 1

    def __str__(self):
        if self.accelerator == 'mps':
            return f"Apple Silicon ({self.total_ram_gb:.0f}GB unified memory)"
        elif self.accelerator == 'cuda':
            return f"{self.gpu_type} ({self.gpu_memory_gb:.0f}GB VRAM)"
        else:
            return f"CPU ({self.total_ram_gb:.0f}GB RAM)"


class HardwareDetector:
    """Detect and profile hardware capabilities"""

    @staticmethod
    def detect() -> HardwareProfile:
        """Detect current hardware configuration"""

        profile = HardwareProfile(
            platform=platform.system(),
            cpu_physical_cores=psutil.cpu_count(logical=False),
            cpu_logical_cores=psutil.cpu_count(logical=True),
            total_ram_gb=psutil.virtual_memory().total / (1024**3),
            available_ram_gb=psutil.virtual_memory().available / (1024**3),
            gpu_type=None,
            gpu_memory_gb=0,
            accelerator='cpu'
        )

        # Detect NVIDIA CUDA
        if torch.cuda.is_available():
            profile.accelerator = 'cuda'
            profile.gpu_count = torch.cuda.device_count()
            profile.gpu_type = torch.cuda.get_device_name(0)
            profile.gpu_memory_gb = (
                torch.cuda.get_device_properties(0).total_memory / (1024**3)
            )

        # Detect Apple Metal
        elif torch.backends.mps.is_available():
            profile.accelerator = 'mps'
            profile.gpu_type = 'Apple Silicon'
            # Use 75% of RAM as effective GPU memory
            profile.gpu_memory_gb = profile.total_ram_gb * 0.75

        return profile

    @staticmethod
    def detect_ollama_models() -> list[dict]:
        """Detect which models are available in Ollama"""
        import requests

        try:
            response = requests.get("http://localhost:11434/api/tags", timeout=5)
            response.raise_for_status()
            return response.json().get('models', [])
        except Exception as e:
            logger.warning(f"Could not connect to Ollama: {e}")
            return []

    @staticmethod
    def check_ollama_running() -> bool:
        """Check if Ollama is running"""
        import requests

        try:
            response = requests.get("http://localhost:11434/api/tags", timeout=2)
            return response.status_code == 200
        except:
            return False
```

### Hardware Detection Flow

```
User starts ragged
    │
    ├─> Detect hardware (CPU, RAM, GPU)
    │   ├─> Apple Silicon? → accelerator='mps'
    │   ├─> NVIDIA GPU?    → accelerator='cuda'
    │   └─> Neither        → accelerator='cpu'
    │
    ├─> Calculate effective memory
    │   ├─> Apple Silicon  → 70% of total RAM
    │   ├─> NVIDIA        → GPU VRAM
    │   └─> CPU only      → 50% of total RAM
    │
    ├─> Check Ollama status
    │   ├─> Running?      → Detect available models
    │   └─> Not running   → Prompt to start or install
    │
    ├─> Recommend optimal models
    │   ├─> Quality tier  → Best model that fits
    │   ├─> Balanced tier → Medium model
    │   └─> Fast tier     → Small model
    │
    └─> Display configuration summary
        "Detected: Apple Silicon (128GB)"
        "Recommended models:"
        "  Quality:  llama3.3:70b-q4 (10-12 t/s)"
        "  Balanced: qwen2.5:32b-q5 (22-25 t/s)"
        "  Fast:     llama3.2:8b-q6 (65-70 t/s)"
```

---

## Model Selection by Hardware

### Selection Algorithm

```python
class ModelSelector:
    """Select optimal models based on hardware"""

    # Model database (2025 recommendations)
    MODELS = {
        'llama3.3:70b-q4': {
            'size_class': '70B',
            'quantisation': 'Q4_K_M',
            'memory_gb': 45,
            'quality_score': 95,
            'use_case': 'general',
        },
        'deepseek-r1:70b-q4': {
            'size_class': '70B',
            'quantisation': 'Q4_K_M',
            'memory_gb': 45,
            'quality_score': 95,
            'use_case': 'reasoning',
        },
        'qwen2.5-coder:32b-q5': {
            'size_class': '32B',
            'quantisation': 'Q5_K_M',
            'memory_gb': 22,
            'quality_score': 90,
            'use_case': 'coding',
        },
        'qwen2.5:32b-q4': {
            'size_class': '32B',
            'quantisation': 'Q4_K_M',
            'memory_gb': 20,
            'quality_score': 88,
            'use_case': 'general',
        },
        'llama3.2:8b-q6': {
            'size_class': '8B',
            'quantisation': 'Q6_K',
            'memory_gb': 6,
            'quality_score': 75,
            'use_case': 'general',
        },
        'mistral:7b-q4': {
            'size_class': '7B',
            'quantisation': 'Q4_K_M',
            'memory_gb': 4,
            'quality_score': 72,
            'use_case': 'general',
        },
    }

    EMBEDDING_MODELS = {
        'nomic-embed-text': {
            'memory_gb': 0.8,
            'dimensions': 768,
            'context': 8192,
            'quality_score': 90,
            'recommended': True,
        },
        'mxbai-embed-large': {
            'memory_gb': 1.0,
            'dimensions': 1024,
            'context': 512,
            'quality_score': 95,
            'recommended': False,  # Slower but higher quality
        },
    }

    @staticmethod
    def get_effective_memory(hardware: HardwareProfile) -> float:
        """Calculate memory available for models"""
        if hardware.accelerator == 'mps':
            return hardware.total_ram_gb * 0.70
        elif hardware.accelerator == 'cuda':
            return hardware.gpu_memory_gb
        else:
            return hardware.total_ram_gb * 0.50

    @staticmethod
    def recommend_models(
        hardware: HardwareProfile,
        use_case: str = 'general'
    ) -> dict:
        """Recommend optimal models for hardware"""

        effective_memory = ModelSelector.get_effective_memory(hardware)

        # Reserve memory for embeddings and system
        embedding_memory = 1.0
        system_reserve = 5.0 if hardware.accelerator == 'cpu' else 10.0
        available_for_llm = effective_memory - embedding_memory - system_reserve

        if available_for_llm < 4:
            return {
                'error': 'Insufficient memory',
                'minimum_required': '16GB RAM',
                'recommendation': 'Upgrade hardware or use cloud-based RAG'
            }

        # Filter models that fit
        fitting_models = {
            name: specs for name, specs in ModelSelector.MODELS.items()
            if specs['memory_gb'] <= available_for_llm
        }

        if not fitting_models:
            return {
                'error': f'No models fit in {available_for_llm:.1f}GB',
                'recommendation': 'Use smallest available model with CPU-only mode'
            }

        # Select by tier
        recommendations = {
            'fast': None,
            'balanced': None,
            'quality': None,
        }

        # Quality: Highest quality that fits
        recommendations['quality'] = max(
            fitting_models.items(),
            key=lambda x: x[1]['quality_score']
        )[0]

        # Fast: Fastest (smallest) model
        small_models = {
            name: specs for name, specs in fitting_models.items()
            if specs['memory_gb'] <= 10
        }
        if small_models:
            recommendations['fast'] = max(
                small_models.items(),
                key=lambda x: x[1]['quality_score']
            )[0]
        else:
            recommendations['fast'] = recommendations['quality']

        # Balanced: Medium model
        medium_models = {
            name: specs for name, specs in fitting_models.items()
            if 15 <= specs['memory_gb'] <= 30
        }
        if medium_models:
            recommendations['balanced'] = max(
                medium_models.items(),
                key=lambda x: x[1]['quality_score']
            )[0]
        else:
            recommendations['balanced'] = recommendations['fast']

        # Adjust speeds based on hardware
        speed_multiplier = ModelSelector._get_speed_multiplier(hardware)

        return {
            'hardware': str(hardware),
            'effective_memory_gb': effective_memory,
            'available_for_llm_gb': available_for_llm,
            'recommendations': {
                tier: {
                    'model': model_name,
                    **ModelSelector.MODELS[model_name],
                    'expected_speed_multiplier': speed_multiplier,
                }
                for tier, model_name in recommendations.items()
                if model_name
            },
            'embedding_model': ModelSelector.EMBEDDING_MODELS['nomic-embed-text'],
        }

    @staticmethod
    def _get_speed_multiplier(hardware: HardwareProfile) -> float:
        """Adjust expected speed based on hardware type"""

        # Baseline: RTX 4090
        if hardware.accelerator == 'cuda':
            if 'RTX 5090' in hardware.gpu_type:
                return 2.5
            elif 'RTX 4090' in hardware.gpu_type:
                return 1.0
            elif 'RTX 4080' in hardware.gpu_type:
                return 0.8
            elif 'RTX 4070' in hardware.gpu_type:
                return 0.7
            elif 'RTX 3090' in hardware.gpu_type:
                return 0.8
            else:
                return 0.6

        elif hardware.accelerator == 'mps':
            # Apple Silicon is slower per-token than CUDA
            if hardware.total_ram_gb >= 128:
                return 0.15  # M4 Max 128GB
            elif hardware.total_ram_gb >= 64:
                return 0.15  # M4 Pro 64GB
            else:
                return 0.12

        else:
            return 0.05  # CPU-only is very slow
```

### Model Recommendation Examples

**Mac Studio M4 Max 128GB**:
```
Detected: Apple Silicon (128GB unified memory)
Effective memory: 89.6 GB (70% of 128GB)
Available for LLM: 78.6 GB

Recommended models:
  Quality:  llama3.3:70b-q4 (~10-12 t/s, 45GB)
  Balanced: qwen2.5:32b-q5 (~22-25 t/s, 22GB)
  Fast:     llama3.2:8b-q6 (~65-70 t/s, 6GB)

Embedding: nomic-embed-text (768 dim, 8K context)
```

**Mac mini M4 Pro 64GB**:
```
Detected: Apple Silicon (64GB unified memory)
Effective memory: 44.8 GB
Available for LLM: 33.8 GB

Recommended models:
  Quality:  qwen2.5:32b-q4 (~22-25 t/s, 20GB)
  Balanced: qwen2.5:32b-q4 (~22-25 t/s, 20GB)
  Fast:     llama3.2:8b-q6 (~65-70 t/s, 6GB)

Note: 70B models possible but tight fit (limited context)
```

**MacBook Pro M4 Pro 48GB**:
```
Detected: Apple Silicon (48GB unified memory)
Effective memory: 33.6 GB
Available for LLM: 22.6 GB

Recommended models:
  Quality:  qwen2.5:32b-q4 (~22-25 t/s, 20GB)
  Balanced: llama3.2:8b-q6 (~65-70 t/s, 6GB)
  Fast:     llama3.2:8b-q6 (~65-70 t/s, 6GB)
```

**NVIDIA RTX 4090 24GB**:
```
Detected: NVIDIA GeForce RTX 4090 (24GB VRAM)
Effective memory: 24 GB
Available for LLM: 13 GB

Recommended models:
  Quality:  qwen2.5:32b-q4 (~30-35 t/s, 20GB) [TIGHT FIT]
  Balanced: llama3.2:8b-q6 (~80+ t/s, 6GB)
  Fast:     llama3.2:8b-q6 (~80+ t/s, 6GB)

Note: Fast inference but VRAM-limited for largest models
```

---

## Memory Management

### Context Window vs. Memory Trade-offs

**Memory Impact by Context Size** (70B Q4 model):

```
Base model:        40 GB
+ 4K context:      41.2 GB  (+1.2 GB)
+ 8K context:      42.4 GB  (+2.4 GB)
+ 16K context:     44.8 GB  (+4.8 GB)
+ 32K context:     49.6 GB  (+9.6 GB)
+ 64K context:     59.2 GB  (+19.2 GB)
+ 128K context:    78.4 GB  (+38.4 GB)

Formula: context_memory_gb ≈ (context_tokens / 1000) * 0.3
```

**Safe Context Windows by Hardware**:

| Hardware | 70B Q4 | 34B Q5 | 13B Q6 | 8B Q6 |
|----------|--------|--------|--------|-------|
| Mac Studio M4 Max 128GB | 32K | 64K | 128K | 128K |
| Mac mini M4 Pro 64GB | 8K | 32K | 64K | 128K |
| MacBook Pro M4 Pro 48GB | N/A | 16K | 48K | 128K |
| RTX 4090 24GB | 8K | 32K | 64K | 128K |

### Concurrent Model Loading

**Strategy for Mac Studio M4 Max**:

```python
class ModelManager:
    """Manage concurrent model loading"""

    def __init__(self, max_memory_gb: float = 128):
        self.max_memory_gb = max_memory_gb
        self.loaded_models = {}
        self.memory_budget = max_memory_gb * 0.70  # 70% for models
        self.current_usage = 0

    def can_load(self, model_name: str, estimated_memory: float) -> bool:
        """Check if model can be loaded"""
        return (self.current_usage + estimated_memory) < self.memory_budget

    def load_model(self, model_name: str, estimated_memory: float):
        """Load model with memory tracking"""

        if not self.can_load(model_name, estimated_memory):
            # Unload least recently used model
            if self.loaded_models:
                lru_model = min(
                    self.loaded_models.items(),
                    key=lambda x: x[1]['last_used']
                )
                self.unload_model(lru_model[0])

        # Load via Ollama
        self.loaded_models[model_name] = {
            'memory_gb': estimated_memory,
            'last_used': time.time(),
            'loaded_at': time.time(),
        }
        self.current_usage += estimated_memory

        logger.info(
            f"Loaded {model_name} ({estimated_memory}GB). "
            f"Total usage: {self.current_usage:.1f}/{self.memory_budget:.1f}GB"
        )

    def unload_model(self, model_name: str):
        """Unload model to free memory"""
        if model_name in self.loaded_models:
            memory_freed = self.loaded_models[model_name]['memory_gb']
            del self.loaded_models[model_name]
            self.current_usage -= memory_freed

            logger.info(
                f"Unloaded {model_name} ({memory_freed}GB freed). "
                f"Usage: {self.current_usage:.1f}/{self.memory_budget:.1f}GB"
            )
```

**Concurrent Loading Example** (Mac Studio M4 Max):

```python
manager = ModelManager(max_memory_gb=128)

# Load primary LLM
manager.load_model("llama3.3:70b-q4", estimated_memory=45)

# Load embedding model (concurrent)
manager.load_model("nomic-embed-text", estimated_memory=1)

# Load fast model for quick queries (concurrent)
manager.load_model("llama3.2:8b-q6", estimated_memory=6)

# Total: 52GB used, 76GB free
# Can still load ChromaDB (11GB), Kuzu (2GB), with 63GB free
```

---

## Performance Optimisation

### Ollama Configuration

**macOS (Apple Silicon)**:

```bash
# ~/.config/ollama/environment
export OLLAMA_METAL=1                          # Enable Metal
export OLLAMA_MAX_LOADED_MODELS=2              # Allow 2 models
export OLLAMA_NUM_THREADS=16                   # Physical cores
export OLLAMA_NUM_PARALLEL=4                   # Concurrent requests
export OLLAMA_MAX_QUEUE=512                    # Request queue size
```

**Windows/Linux (NVIDIA)**:

```bash
# Ollama environment
export OLLAMA_NUM_GPU=999                      # Use all GPU layers
export OLLAMA_GPU_OVERHEAD=2400                # 10% VRAM overhead (MB)
export OLLAMA_MAX_LOADED_MODELS=1              # Single model optimal
export OLLAMA_NUM_PARALLEL=4
```

### ChromaDB Optimisation

```python
import chromadb
from chromadb.config import Settings

# Optimal ChromaDB configuration for Mac Studio
client = chromadb.PersistentClient(
    path="./chroma_db",
    settings=Settings(
        anonymised_telemetry=False,
        allow_reset=True,
    )
)

collection = client.get_or_create_collection(
    name="documents",
    metadata={
        "hnsw:space": "cosine",           # Distance metric
        "hnsw:construction_ef": 200,      # Build quality
        "hnsw:search_ef": 100,            # Search quality
        "hnsw:M": 16,                     # Graph connectivity
    }
)

# Batch processing for efficiency
def batch_add_documents(docs, batch_size=1000):
    """Add documents in batches for optimal performance"""
    for i in range(0, len(docs), batch_size):
        batch = docs[i:i + batch_size]
        collection.add(
            documents=[d.text for d in batch],
            metadatas=[d.metadata for d in batch],
            ids=[d.id for d in batch]
        )
```

### Embedding Generation Optimisation

```python
class EmbeddingOptimiser:
    """Optimise embedding generation"""

    def __init__(self, model="nomic-embed-text"):
        self.model = model
        self.cache = {}  # Semantic cache

    def embed_batch(self, texts: list[str], batch_size: int = 100) -> list:
        """Batch embed for 2x speedup"""

        embeddings = []
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]

            # Check cache first
            uncached = [t for t in batch if t not in self.cache]

            if uncached:
                # Generate embeddings for uncached texts
                batch_embeddings = ollama.embeddings(
                    model=self.model,
                    prompt=uncached
                )

                # Update cache
                for text, embedding in zip(uncached, batch_embeddings):
                    self.cache[text] = embedding

            # Retrieve from cache
            embeddings.extend([self.cache[t] for t in batch])

        return embeddings
```

**Performance Impact**:
- Batch processing: **2x faster** than individual (50 vs. 25 docs/sec)
- Semantic caching: **100x faster** for repeated texts (0.001s vs. 0.1s)
- Combined: Significant speedup for typical RAG workloads

---

## Implementation Roadmap

### Phase 1: Basic Detection (v0.1)

**Goal**: Detect hardware and display capabilities

**Features**:
- Detect CPU, RAM, GPU using `psutil` and `torch`
- Identify Apple Silicon vs. NVIDIA vs. CPU
- Display hardware summary on startup
- Basic Ollama integration

**Implementation**:
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

**Effort**: 5-8 hours

### Phase 2: Model Recommendations (v0.2)

**Goal**: Recommend optimal models for detected hardware

**Features**:
- Calculate effective memory
- Recommend Fast/Balanced/Quality tiers
- Display model recommendations with expected performance
- Warn if insufficient resources

**Implementation**:
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

**Effort**: 8-12 hours

### Phase 3: Automatic Configuration (v0.3)

**Goal**: Configure Ollama and ChromaDB automatically

**Features**:
- Generate Ollama environment variables
- Configure ChromaDB for hardware
- Adjust batch sizes for embedding generation
- Context window recommendations

**Implementation**:
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

**Effort**: 10-15 hours

### Phase 4: Dynamic Optimisation (v1.0)

**Goal**: Monitor and optimise performance in production

**Features**:
- Memory usage monitoring
- Performance metrics (latency, throughput)
- Automatic model unloading under memory pressure
- Adaptive batch sizing
- Performance regression detection

**Implementation**:
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

**Effort**: 15-20 hours

---

## Configuration File Format

### Hardware Configuration (Auto-Generated)

```yaml
# ~/.ragged/hardware.yaml
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

## Conclusion

ragged's hardware optimisation strategy ensures:

- **Optimal Performance**: Automatic configuration for Mac Studio M4 Max 128GB
- **Broad Compatibility**: Supports Mac mini, MacBook Pro, Windows/NVIDIA, CPU-only
- **Transparent Trade-offs**: Users understand speed vs. quality for their hardware
- **Future-Proof**: Architecture supports upcoming models and hardware

**Implementation Priority**: v0.2 (after basic RAG functionality in v0.1)

**Key Benefits**:
- Maximise performance on available hardware
- Prevent out-of-memory errors
- User doesn't need to understand technical details
- Graceful degradation on modest hardware

**Next Steps**:
1. Implement hardware detection (v0.1)
2. Add model recommendations (v0.2)
3. Automatic configuration (v0.3)
4. Performance monitoring (v1.0)

---

**Related Documentation**:
- [Dynamic Model Selection](./model-selection.md)
- [Personal Memory & Personas](./personal-memory-personas.md)
- [Privacy Architecture](./privacy-architecture.md)
