# Memory System User Guide

## Overview

The ragged memory system provides personalised, privacy-first context management through three interconnected components:

1. **Personas**: User profiles for context switching
2. **Interaction Tracking**: Query and response history with SQLite
3. **Knowledge Graph**: Topic-document relationships with Kuzu

All data is stored locally with full GDPR compliance.

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Memory System                         │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │   Personas   │  │ Interactions │  │    Graph     │  │
│  │   (YAML)     │  │   (SQLite)   │  │   (Kuzu)     │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
│         │                 │                  │          │
│         └─────────────────┴──────────────────┘          │
│                           │                             │
│                  ~/.ragged/memory/                      │
└─────────────────────────────────────────────────────────┘
```

## Storage Structure

```
~/.ragged/memory/
├── profiles/
│   ├── personas.yaml           # All persona configurations
│   ├── active_persona.txt      # Current active persona
│   └── exports/                # Persona exports
├── interactions.db             # SQLite database for history
└── graph/
    └── kuzu_db/                # Kuzu graph database
```

## Component Details

### 1. Personas

Personas provide user identity and context for all memory operations.

**Data Structure:**
```python
{
    "name": "researcher",
    "description": "ML researcher focused on RAG systems",
    "focus_areas": ["RAG", "NLP", "Privacy"],
    "preferences": {
        "default_model": "llama3.2:3b",
        "max_history": 100
    },
    "active_projects": ["thesis", "paper-review"],
    "created_at": "2025-11-23T10:30:00",
    "last_used": "2025-11-23T14:25:00",
    "usage_count": 42
}
```

**Operations:**
- `create`: Create new persona
- `switch`: Set active persona
- `get`: Retrieve persona details
- `list`: List all personas
- `delete`: Remove persona and all associated data
- `export`: Export persona configuration

### 2. Interaction Tracking

Records all queries and responses with metadata for searchability and analysis.

**Schema:**
```sql
CREATE TABLE interactions (
    id TEXT PRIMARY KEY,
    persona TEXT NOT NULL,
    query TEXT NOT NULL,
    response TEXT,
    timestamp TIMESTAMP NOT NULL,
    retrieved_doc_ids TEXT,      -- JSON array
    model_used TEXT,
    latency_ms REAL,
    feedback TEXT,               -- positive/negative/neutral
    session_id TEXT
);
```

**Operations:**
- `record_interaction`: Store query/response pair
- `get_interaction`: Retrieve by ID
- `list_interactions`: Get history with pagination
- `delete_interaction`: Remove single interaction
- `clear_interactions`: Delete all for persona
- `export_interactions`: Export to JSON
- `add_feedback`: Add user feedback to interaction

**Features:**
- Full-text search across queries
- Timestamp-based filtering
- Session grouping
- Feedback tracking
- Latency monitoring

### 3. Knowledge Graph

Tracks relationships between users, topics, and documents using Kuzu graph database.

**Graph Schema:**

```cypher
// Nodes
(User {name: STRING, created_at: TIMESTAMP})
(Topic {name: STRING, interest_level: DOUBLE, created_at: TIMESTAMP})
(Document {doc_id: STRING, title: STRING, created_at: TIMESTAMP})

// Relationships
(User)-[INTERESTED_IN {frequency: INT64, last_accessed: TIMESTAMP}]->(Topic)
(User)-[ACCESSED {access_count: INT64, last_accessed: TIMESTAMP, first_accessed: TIMESTAMP}]->(Document)
(Topic)-[RELATED_TO {relevance: DOUBLE}]->(Document)
```

**Operations:**
- `ensure_user_exists`: Create user node
- `add_topic_interest`: Track topic with interest level
- `record_document_access`: Log document access
- `link_topic_to_document`: Create topic-document relationship
- `get_user_interests`: Query user's topics
- `get_accessed_documents`: Recent document access
- `get_related_documents`: Documents for specific topic
- `delete_user_data`: Remove all user data
- `export_graph`: Export graph data
- `clear_graph`: Delete entire graph

**Features:**
- Temporal tracking (when interests/access occurred)
- Frequency counting (how often topics accessed)
- Relevance scoring (topic-document connections)
- Multi-persona isolation
- Graph traversal for recommendations

## Integration

The three components work together automatically:

```python
# When you query with active persona "researcher":
ragged query "What is RAG?"

# Behind the scenes:
1. Persona: Uses "researcher" context
2. Interaction: Records query, response, docs, timestamp
3. Graph:
   - Adds "RAG" to topics for researcher
   - Records document access
   - Links RAG topic to accessed documents
```

## CLI Commands

### Persona Commands

```bash
# Create persona
ragged persona create <name> [--description TEXT] [--focus AREA]... [--project NAME]...

# Switch active persona
ragged persona switch <name>

# List all personas
ragged persona list [--format json|table]

# Show persona details
ragged persona show <name> [--format json]

# Delete persona (confirmation required)
ragged persona delete <name> [--yes]

# Show active persona
ragged persona active
```

### Memory Commands

```bash
# View interaction history
ragged memory history [--persona NAME] [--limit N] [--format json]

# View topics of interest
ragged memory interests [--persona NAME] [--format json]

# View accessed documents
ragged memory documents [--persona NAME] [--limit N]

# Export all memory data
ragged memory export [--persona NAME] [--output PATH]

# Clear interaction history (confirmation required)
ragged memory clear [--persona NAME] [--yes]

# View specific interaction
ragged memory show <interaction-id>

# Add feedback to interaction
ragged memory feedback <interaction-id> <positive|negative|neutral>
```

## Privacy & GDPR Compliance

The memory system implements full GDPR compliance:

### Article 15: Right of Access

Users can view all their data:

```bash
# View all interactions
ragged memory history --persona researcher

# View all topics
ragged memory interests --persona researcher

# View all documents
ragged memory documents --persona researcher

# Export everything
ragged memory export --persona researcher
```

### Article 17: Right to Erasure

Users can delete their data:

```bash
# Delete specific interaction
ragged memory delete <interaction-id>

# Clear all interactions
ragged memory clear --persona researcher

# Delete entire persona
ragged persona delete researcher
```

### Article 20: Right to Data Portability

Export data in machine-readable JSON:

```bash
ragged memory export --persona researcher
```

Output format:
```json
{
  "export_type": "memory",
  "export_timestamp": "2025-11-23T14:30:00",
  "persona": {...},
  "interactions": [...],
  "knowledge_graph": {
    "interests": [...],
    "documents": [...],
    "relationships": [...]
  }
}
```

## Advanced Usage

### Programmatic Access

```python
from ragged.memory import PersonaManager, InteractionTracker, KnowledgeGraph

# Persona management
manager = PersonaManager()
manager.create("researcher", focus=["RAG", "NLP"])
manager.switch("researcher")

# Track interactions
tracker = InteractionTracker(persona="researcher")
tracker.record_interaction(
    query="What is RAG?",
    response="Retrieval-Augmented Generation...",
    retrieved_doc_ids=["doc1", "doc2"],
    model_used="llama3.2:3b",
    latency_ms=150.5
)

# Query history
history = tracker.list_interactions(limit=10)
for interaction in history:
    print(f"{interaction.timestamp}: {interaction.query}")

# Knowledge graph
graph = KnowledgeGraph(persona="researcher")
graph.add_topic_interest("RAG", interest_level=0.9)
graph.record_document_access("doc1", title="RAG Paper")
graph.link_topic_to_document("RAG", "doc1", relevance=0.95)

interests = graph.get_user_interests()
for topic in interests:
    print(f"{topic['topic']}: {topic['frequency']} queries")

graph.close()
```

### Bulk Operations

```python
# Bulk import interactions
for query, response in historical_data:
    tracker.record_interaction(query=query, response=response)

# Bulk topic addition
topics = ["RAG", "NLP", "Transformers", "BERT"]
for topic in topics:
    graph.add_topic_interest(topic)
```

### Custom Exports

```python
# Export with custom processing
export_data = tracker.export_interactions()

# Filter by date
recent = [i for i in export_data["interactions"]
          if i["timestamp"] > "2025-11-01"]

# Save custom format
import json
with open("custom_export.json", "w") as f:
    json.dump(recent, f)
```

## Performance Considerations

### Database Optimisation

**SQLite (Interactions):**
- Indexed on: `persona`, `timestamp`, `session_id`
- Typical query time: <1ms for recent history
- Storage: ~1KB per interaction

**Kuzu (Knowledge Graph):**
- In-memory graph processing
- Typical query time: <5ms for user interests
- Storage: ~500 bytes per node, ~200 bytes per relationship

### Recommended Limits

- **Interactions per persona**: 10,000 (typical), 100,000 (maximum)
- **Topics per persona**: 100 (typical), 1,000 (maximum)
- **Documents per persona**: 1,000 (typical), 10,000 (maximum)

### Cleanup Strategies

```bash
# Keep only recent interactions
ragged memory history --persona researcher --limit 1000 > recent.json
ragged memory clear --persona researcher --yes
# Re-import recent from backup if needed

# Archive old personas
ragged memory export --persona old-project
ragged persona delete old-project --yes
```

## Troubleshooting

### Database Locked Errors

If you see "database is locked":

```bash
# Check for stale processes
ps aux | grep ragged

# Close all ragged instances
# Try operation again
```

### Knowledge Graph Corruption

```bash
# Export data first
ragged memory export --persona researcher

# Clear and rebuild
rm -rf ~/.ragged/memory/graph/kuzu_db
# Re-run queries to rebuild graph
```

### Performance Degradation

```bash
# Check database size
du -sh ~/.ragged/memory/

# If > 1GB, consider archiving old data
ragged memory export --all
ragged memory clear --persona <old-personas>
```

## Security Considerations

1. **Local Storage Only**: All data in `~/.ragged/memory/`
2. **No Network Calls**: Zero external connections
3. **File Permissions**: 600 (user read/write only)
4. **Encryption at Rest**: Planned for v0.5.x
5. **Audit Logging**: Available via interaction history

## Migration & Backup

### Backup Strategy

```bash
# Full backup
tar -czf ragged-memory-backup-$(date +%Y%m%d).tar.gz ~/.ragged/memory/

# Persona-specific backup
ragged memory export --persona researcher --output researcher-backup.json
```

### Restore

```bash
# Full restore
tar -xzf ragged-memory-backup-20251123.tar.gz -C ~/

# Import persona (manual process)
# 1. Create persona
# 2. Import interactions via API
```

## Related Documentation

- [Getting Started with Personas](../tutorials/personas-quickstart.md)
- [Memory API Reference](../reference/memory-api.md)
- [Privacy & Data Control](privacy.md)

---

**Status**: Production-ready (v0.4.5)
