# Ragged Public API Reference

**Version:** v0.6.11
**Status:** Stable

## Overview

This document describes the public API surface for ragged v0.6.x, focusing on the query optimisation features implemented in the v0.6 series.

## Core APIs

### Query Processing

```python
from ragged.optimisation import QueryClassifier, ModelRouter, DomainDetector

# Query classification (v0.6.1)
classifier = QueryClassifier()
classification = classifier.classify("What is machine learning?")

# Automatic model routing (v0.6.2)
router = ModelRouter()
selected_model = router.route(classification)

# Domain adaptation (v0.6.3)
detector = DomainDetector()
domain = detector.detect(query="Explain neural networks", context=docs)
```

### Caching (v0.6.4)

```python
from ragged.caching import CacheManager, SmartCache

# Cache manager with multi-layer caching
manager = CacheManager(enabled=True)

# Smart caching with frequency tracking
smart_cache = SmartCache()
smart_cache.record_access(key, query=query)
hot_keys = smart_cache.get_hot_keys(top_n=10)
```

### Streaming (v0.6.5)

```python
from ragged.generation.streaming import StreamGenerator
from ragged.cli.streaming_formatter import StreamingFormatter

# Core streaming
generator = StreamGenerator()
for token in generator.stream_tokens(tokens):
    print(token.token, end="")

# CLI streaming with Rich
formatter = StreamingFormatter()
response = formatter.stream_response_live(tokens, title="Response")
```

### Analytics (v0.6.6)

```python
from ragged.caching import get_cache_manager

# Get cache statistics
manager = get_cache_manager()
stats = manager.get_stats()

# Cache hit rate, entries, size per layer
for layer, metrics in stats.items():
    print(f"{layer}: {metrics['hit_rate']:.1%} hit rate")
```

## CLI Commands

```bash
# Query with optimisations
ragged query "What is RAG?" --stream

# View analytics
ragged analytics cache
ragged analytics cache --detailed
ragged analytics status

# Clear caches
ragged analytics clear-cache
```

## Configuration

```yaml
# config.yml
query_optimisation:
  classification_enabled: true
  routing_enabled: true
  domain_adaptation_enabled: true

caching:
  enabled: true
  smart_caching: true

streaming:
  enabled: true
  cli:
    progressive_output: true
```

## API Stability

**Stable APIs** (v0.6.x):
- `QueryClassifier.classify()`
- `ModelRouter.route()`
- `DomainDetector.detect()`
- `CacheManager` operations
- `StreamGenerator.stream_tokens()`

**Experimental** (may change):
- Smart caching internals
- Streaming metrics format
- Analytics command outputs

---

**v0.6.11: Public API Documentation Complete**
