# Dynamic Model Selection Testing Strategy

**Feature:** Dynamic Model Selection & Routing

**Status:** Planned

---

## Overview

This document outlines the comprehensive testing strategy for ragged's dynamic model selection and routing system.

**Related Documentation:**
- [Model Selection Design](../../core-concepts/model-selection.md)
- [Model Selection Roadmap](../roadmap/features/model-selection-roadmap.md)

---

## Testing Strategy

### Unit Tests

**Routing Components** (coverage target: 90%):
```python
# tests/routing/test_task_classifier.py
def test_classify_code_generation():
    classifier = TaskClassifier()
    assert classifier.classify("Write a Python function") == 'code_generation'
    assert classifier.classify("Debug this code") == 'code_generation'

def test_classify_reasoning():
    classifier = TaskClassifier()
    assert classifier.classify("Why does X happen?") == 'reasoning'
    assert classifier.classify("Compare A and B") == 'reasoning'

# tests/routing/test_complexity_analyser.py
def test_complexity_scoring():
    analyser = ComplexityAnalyserV2()

    # Simple query
    score = analyser.analyse("What is Paris?")
    assert score.total < 3.0
    assert score.tier == 'fast'

    # Complex query
    score = analyser.analyse("Analyse the architectural trade-offs between...")
    assert score.total > 7.0
    assert score.tier == 'quality'

# tests/routing/test_capability_matcher.py
def test_match_code_task():
    matcher = CapabilityMatcher(MODEL_REGISTRY)

    requirements = {
        'tier': 'balanced',
        'capabilities': {'code'},
        'specialisations': ['code_generation'],
    }

    model = matcher.find_best_match(
        requirements,
        available_models=['qwen2.5-coder:32b', 'llama3.2:8b'],
        hardware=mock_hardware_128gb
    )

    assert model == 'qwen2.5-coder:32b'
```

### Integration Tests

**End-to-End Routing** (coverage target: 80%):
```python
# tests/routing/test_integration.py
def test_routing_pipeline():
    router = UnifiedModelRouter(
        hardware=mock_hardware_128gb,
        model_registry=MODEL_REGISTRY
    )

    # Code generation routing
    request = RoutingRequest(
        query="Write a Python function to sort a list",
        available_models=['qwen2.5-coder:32b', 'llama3.2:8b']
    )
    decision = router.route(request)

    assert decision.task_type == 'code_generation'
    assert decision.model == 'qwen2.5-coder:32b'
    assert decision.tier == 'balanced'

def test_persona_routing():
    persona = Persona(
        name='researcher',
        preferred_model_tier='quality',
        task_model_overrides={}
    )

    request = RoutingRequest(
        query="Explain neural networks",
        persona=persona,
        available_models=['llama3.3:70b', 'llama3.2:8b']
    )

    decision = router.route(request)
    assert decision.tier == 'quality'
    assert decision.model == 'llama3.3:70b'
```

### Evaluation Tests

**Routing Quality Assessment**:
```python
# tests/routing/test_routing_quality.py
def test_routing_accuracy_on_golden_dataset():
    """Test routing decisions against golden dataset"""

    golden_dataset = load_golden_routing_examples()
    # Dataset contains: (query, expected_tier, expected_task_type)

    router = UnifiedModelRouter(...)
    correct = 0
    total = len(golden_dataset)

    for query, expected_tier, expected_task in golden_dataset:
        request = RoutingRequest(query=query)
        decision = router.route(request)

        if (decision.tier == expected_tier and
            decision.task_type == expected_task):
            correct += 1

    accuracy = correct / total
    assert accuracy >= 0.80, f"Routing accuracy {accuracy:.2%} below threshold"

def test_fallback_chain_quality():
    """Ensure fallback chains degrade gracefully"""

    generator = FallbackGenerator(MODEL_REGISTRY)

    # Quality tier primary
    fallbacks = generator.generate_fallbacks(
        primary_model='llama3.3:70b',
        requirements={'task_type': 'reasoning'},
        available_models=list(MODEL_REGISTRY.keys())
    )

    # Check fallbacks are progressively smaller
    primary_size = MODEL_REGISTRY['llama3.3:70b'].size_b
    for fallback in fallbacks:
        fallback_size = MODEL_REGISTRY[fallback].size_b
        assert fallback_size < primary_size
```

---

