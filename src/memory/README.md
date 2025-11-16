# Memory System

📋 **Status: Planned for v0.3**

This directory will contain the personal memory system for ragged, enabling the system to remember user preferences, past interactions, and build long-term context.

## Planned Components

### Interaction Memory (`interaction.py`)
- Store conversation history
- Track user preferences
- SQLite-based storage
- Query interface for retrieving past interactions

### Semantic Memory (`semantic.py`)
- Long-term semantic knowledge from conversations
- ChromaDB integration
- Automatic extraction of key facts
- Context-aware retrieval

### Temporal Memory (`temporal.py`)
- Time-based memory indexing
- Recency weighting
- Memory decay over time
- Graph database integration (Kuzu)

### Memory Manager (`manager.py`)
- Orchestrates different memory types
- Unified query interface
- Memory consolidation
- Privacy-safe storage

## Architecture

```python
# Planned interface (subject to change)

class MemorySystem:
    def __init__(self, config: MemoryConfig):
        self.interaction_memory = InteractionMemory()
        self.semantic_memory = SemanticMemory()
        self.temporal_memory = TemporalMemory()

    def add(self, interaction: Interaction) -> None:
        """Store a new interaction across all memory types."""
        pass

    def retrieve(
        self,
        query: str,
        k: int = 5,
        memory_types: list[str] = None
    ) -> list[Memory]:
        """Retrieve relevant memories."""
        pass

    def consolidate(self) -> None:
        """Consolidate short-term memories into long-term."""
        pass
```

## Configuration

Memory system will be configurable via:

```yaml
# ~/.ragged/config.yml
memory:
  enabled: true
  interaction:
    max_history: 1000
    retention_days: 90
  semantic:
    enabled: true
    chunk_size: 300
  temporal:
    enabled: true
    decay_factor: 0.95
```

## Database Schema

### Interaction Memory (SQLite)

```sql
CREATE TABLE interactions (
    id INTEGER PRIMARY KEY,
    timestamp DATETIME,
    query TEXT,
    response TEXT,
    sources JSON,
    persona TEXT,
    metadata JSON
);
```

### Semantic Memory (ChromaDB)

- Separate collection from document embeddings
- Metadata includes source interaction, timestamp, confidence

### Temporal Memory (Kuzu Graph DB)

- Nodes: Interactions, Facts, Entities
- Edges: Temporal relationships, references

## Privacy Considerations

- All memory stored locally by default
- User control over memory retention
- Ability to delete specific memories
- Export memory data
- Privacy-safe logging

## Testing

Memory system will have comprehensive tests:
- Unit tests for each memory type
- Integration tests for memory manager
- Performance tests for large memory stores
- Privacy tests to ensure no leakage

## See Also

- [v0.3 Roadmap](../../docs/development/roadmaps/version/v0.3.0/)
- [Architecture Planning](../../docs/development/planning/architecture/)
- [ADR: Personal Memory System](../../docs/development/decisions/adrs/) (TBD)

---

**Note:** This is a planning directory. Implementation will begin in v0.3 development cycle.
