# Dynamic Model Selection Implementation Roadmap

**Feature:** Dynamic Model Selection & Routing

**Status:** Planned

**Versions:** v0.1 - v2.1+

**Last Updated:** 2025-11-15

---

## Overview

This roadmap details the phased implementation of dynamic model selection and intelligent routing for ragged. The implementation spans from single-model support in v0.1 through advanced learning-based routing and cloud integration in v2.0+.

**Related Design:** [Dynamic Model Selection Strategy](../../planning/core-concepts/model-selection.md)

---

## Implementation Timeline

### v0.1 - MVP (Single Model)
**Duration**: 2-3 weeks
**Status:** Foundation

- ✅ Single model support (manual selection)
- ✅ Basic Ollama integration
- ✅ No routing (use default model)

**Deliverables**:
- Basic model interface
- Ollama client wrapper
- Manual model configuration

---

### v0.2 - Basic Routing
**Duration**: 3-4 weeks
**Status:** Planned

**Features**:
- Task classification (basic patterns)
- Hardware detection
- Tier recommendations (fast/balanced/quality)
- Simple task-based routing

**Deliverables**:
- `TaskClassifier` with regex patterns
- `HardwareDetector` integration
- `ModelSelector` with tier logic
- Configuration file support

**Example**:
```python
# Auto-select based on task
answer = ragged.query("Write a Python function...")
# → Automatically routes to code-specialised model
```

---

### v0.3 - Complexity Analysis
**Duration**: 2-3 weeks
**Status:** Planned

**Features**:
- Complexity scoring algorithm
- Tier selection based on complexity
- Capability matching
- Model registry with capabilities

**Deliverables**:
- `ComplexityAnalyser` with multi-dimensional scoring
- Expanded `MODEL_REGISTRY` with capabilities
- `CapabilityMatcher` for requirement matching

**Example**:
```python
# Simple query → fast tier
ragged.query("What is Paris?")  # → mistral:7b

# Complex query → quality tier
ragged.query("Analyse the architectural trade-offs...")  # → llama3.3:70b
```

---

### v0.4 - Persona Integration
**Duration**: 3-4 weeks
**Status:** Planned

**Features**:
- Persona-aware routing
- Persona model preferences
- Task overrides per persona
- Tier adjustment rules

**Deliverables**:
- `PersonaAwareRouter`
- Persona configuration schema
- Integration with persona system

**Example**:
```python
# Researcher persona prefers quality tier
ragged.set_persona("researcher")
ragged.query("Explain neural networks")  # → llama3.3:70b

# Developer persona uses code-specialised models
ragged.set_persona("developer")
ragged.query("Write a sorting function")  # → deepseek-coder:33b
```

---

### v0.5 - Advanced Routing
**Duration**: 2-3 weeks
**Status:** Planned

**Features**:
- Fallback chain generation
- Error handling and recovery
- Routing analytics and logging
- Performance monitoring

**Deliverables**:
- `FallbackGenerator`
- `RouterWithFallback`
- Routing decision logging
- Performance metrics collection

**Example**:
```python
# Automatic fallback if primary unavailable
ragged.query("Complex query")
# → Try llama3.3:70b
# → Fallback to qwen2.5:32b if unavailable
# → Fallback to llama3.2:8b if needed
```

---

### v1.0 - Production Routing
**Duration**: 3-4 weeks
**Status:** Future

**Features**:
- Cost optimisation (for cloud deployments)
- Latency optimisation
- A/B testing framework
- Learning-based routing (optional)
- Advanced monitoring and dashboards

**Deliverables**:
- Production-grade router
- Monitoring dashboards
- Cost tracking
- Performance analytics
- Optional: RouteLLM integration

---


## Future Enhancements

### Phase 1: Learning-Based Routing (v1.1+)

**RouteLLM Integration**:
- Train lightweight router model on routing decisions
- 85% cost reduction while preserving 95% quality
- Requires dataset of (query, best_model, quality_score)

```python
# Future implementation
class LearnedRouter:
    """Router with learned preferences from usage data"""

    def train_from_history(self, routing_history: list[RoutingRecord]):
        """Train router from historical routing decisions and outcomes"""
        # RouteLLM or similar framework
        pass
```

### Phase 2: Multi-Model Ensemble (v1.2+)

**Use multiple models for single query**:
- Fast model for query rewriting
- Balanced model for initial answer
- Quality model for refinement/verification

```python
# Future implementation
class EnsembleRouter:
    """Route to multiple models in pipeline"""

    def route_ensemble(self, query: str) -> list[RoutingDecision]:
        return [
            RoutingDecision(model='mistral:7b', role='query_rewriter'),
            RoutingDecision(model='qwen2.5:32b', role='primary'),
            RoutingDecision(model='llama3.3:70b', role='verifier'),
        ]
```

### Phase 3: Cloud Integration (v2.0+)

**Hybrid local + cloud routing**:
- Use local models for fast/balanced tier
- Route complex queries to cloud (Claude, GPT-4)
- Cost-aware routing decisions

```python
# Future implementation
class HybridRouter:
    """Route between local and cloud models"""

    def route_hybrid(
        self,
        query: str,
        cost_limit: float,
        latency_limit: float
    ) -> RoutingDecision:
        # Balance cost, latency, quality
        pass
```

### Phase 4: Specialised Fine-Tuned Models (v2.1+)

**User-specific fine-tuning**:
- Fine-tune small models on user's documents
- Route domain-specific queries to fine-tuned models
- Continual learning from user feedback

---

## Summary

This document defines a comprehensive **dynamic model selection system** for ragged, enabling:

**Automatic Routing**: Intelligent model selection without user intervention
**Multi-Strategy**: Task-based, complexity-based, and persona-aware routing
**Hardware-Aware**: Respects memory and compute constraints
**Extensible**: Easy to add new models and routing strategies
**Production-Ready**: Robust fallback handling and error recovery

**Implementation spans v0.2-v1.0**, with progressive enhancement:
- v0.2: Basic task routing
- v0.3: Complexity analysis
- v0.4: Persona integration
- v0.5: Advanced fallbacks
- v1.0: Production monitoring

The system balances **performance, quality, and resource efficiency**, ensuring users get optimal results regardless of hardware tier or query complexity.

---

**Next Steps**:
1. Review and approve design
2. Create implementation tickets
3. Begin v0.2 development (basic routing)
4. Develop golden dataset for routing evaluation

---

**Document Status**: Design Complete
**Last Updated**: 2025-11-09
**Related Documents**:
- [Hardware Optimisation Strategy](./hardware-optimisation.md)
- [Personal Memory & Personas](./personal-memory-personas.md)
- [Testing Strategy](./testing-strategy.md) (pending)
