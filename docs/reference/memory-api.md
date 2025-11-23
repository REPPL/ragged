# Memory API Reference

## Module: `ragged.memory`

The memory module provides three main components for personalised context management.

### Imports

```python
from ragged.memory import (
    Persona,
    PersonaManager,
    Interaction,
    InteractionTracker,
    KnowledgeGraph,
)
```

---

## PersonaManager

Manages user personas for context switching.

### Class: `PersonaManager`

```python
class PersonaManager:
    def __init__(self, storage_dir: Path | None = None) -> None
```

**Parameters:**
- `storage_dir` (Path | None): Custom storage directory. Default: `~/.ragged/memory/profiles`

**Attributes:**
- `storage_dir` (Path): Directory for persona storage
- `personas` (dict[str, Persona]): Loaded personas
- `active_persona` (str | None): Currently active persona name

### Methods

#### `create()`

```python
def create(
    self,
    name: str,
    description: str = "",
    focus: list[str] | None = None,
    preferences: dict[str, Any] | None = None,
    active_projects: list[str] | None = None,
) -> Persona
```

Create a new persona.

**Parameters:**
- `name` (str): Persona name (alphanumeric, hyphens, underscores)
- `description` (str): Human-readable description
- `focus` (list[str]): Focus areas/topics
- `preferences` (dict): User preferences
- `active_projects` (list[str]): Active project names

**Returns:**
- `Persona`: Created persona object

**Raises:**
- `ValueError`: If persona already exists or name is invalid

**Example:**
```python
manager = PersonaManager()
persona = manager.create(
    "researcher",
    description="ML researcher",
    focus=["RAG", "NLP"],
    preferences={"model": "llama3.2:3b"},
    active_projects=["thesis"]
)
```

#### `get()`

```python
def get(self, name: str) -> Persona
```

Get persona by name.

**Parameters:**
- `name` (str): Persona name

**Returns:**
- `Persona`: Persona object

**Raises:**
- `KeyError`: If persona not found

#### `switch()`

```python
def switch(self, name: str) -> Persona
```

Switch to a persona (sets as active).

**Parameters:**
- `name` (str): Persona name

**Returns:**
- `Persona`: Activated persona

**Raises:**
- `KeyError`: If persona not found

#### `list()`

```python
def list(self) -> list[str]
```

List all persona names.

**Returns:**
- `list[str]`: Sorted list of persona names

#### `delete()`

```python
def delete(self, name: str, confirm: bool = False) -> None
```

Delete a persona.

**Parameters:**
- `name` (str): Persona name to delete
- `confirm` (bool): Confirmation flag (required for safety)

**Raises:**
- `ValueError`: If confirmation not provided
- `KeyError`: If persona not found

**Example:**
```python
manager.delete("researcher", confirm=True)
```

#### `get_active()`

```python
def get_active(self) -> Persona | None
```

Get currently active persona.

**Returns:**
- `Persona | None`: Active persona or None

#### `export_persona()`

```python
def export_persona(self, name: str, output_path: Path | None = None) -> Path
```

Export persona data to JSON (GDPR Article 20).

**Parameters:**
- `name` (str): Persona name to export
- `output_path` (Path | None): Optional custom output path

**Returns:**
- `Path`: Path to exported JSON file

**Raises:**
- `ValueError`: If persona not found

**Example:**
```python
export_path = manager.export_persona("researcher")
print(f"Exported to: {export_path}")
```

---

## Persona

Data class representing a user persona.

### Class: `Persona`

```python
@dataclass
class Persona:
    name: str
    description: str = ""
    focus_areas: list[str] = field(default_factory=list)
    preferences: dict[str, Any] = field(default_factory=dict)
    active_projects: list[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    last_used: datetime = field(default_factory=datetime.now)
    usage_count: int = 0
```

**Attributes:**
- `name`: Unique identifier
- `description`: Human-readable description
- `focus_areas`: List of topics/areas of focus
- `preferences`: User preferences dictionary
- `active_projects`: Current projects
- `created_at`: Creation timestamp
- `last_used`: Last usage timestamp
- `usage_count`: Number of times used

### Methods

#### `to_dict()`

```python
def to_dict(self) -> dict[str, Any]
```

Serialise persona to dictionary.

#### `from_dict()`

```python
@classmethod
def from_dict(cls, data: dict[str, Any]) -> Persona
```

Deserialise persona from dictionary.

#### `mark_used()`

```python
def mark_used(self) -> None
```

Update usage statistics.

---

## InteractionTracker

Tracks query/response interactions with SQLite storage.

### Class: `InteractionTracker`

```python
class InteractionTracker:
    def __init__(self, persona: str | None = None, storage_dir: Path | None = None) -> None
```

**Parameters:**
- `persona` (str | None): Default persona for operations
- `storage_dir` (Path | None): Custom storage directory. Default: `~/.ragged/memory`

**Attributes:**
- `persona` (str | None): Default persona
- `storage_dir` (Path): Storage directory
- `db_path` (Path): SQLite database path

### Methods

#### `record_interaction()`

```python
def record_interaction(
    self,
    query: str,
    response: str | None = None,
    persona: str | None = None,
    retrieved_doc_ids: list[str] | None = None,
    model_used: str | None = None,
    latency_ms: float | None = None,
    session_id: str | None = None,
) -> Interaction
```

Record a query/response interaction.

**Parameters:**
- `query` (str): User query
- `response` (str | None): System response
- `persona` (str | None): Persona name (uses default if not provided)
- `retrieved_doc_ids` (list[str] | None): Retrieved document IDs
- `model_used` (str | None): Model identifier
- `latency_ms` (float | None): Response latency in milliseconds
- `session_id` (str | None): Session identifier

**Returns:**
- `Interaction`: Created interaction object

**Raises:**
- `ValueError`: If persona not provided

**Example:**
```python
tracker = InteractionTracker(persona="researcher")
interaction = tracker.record_interaction(
    query="What is RAG?",
    response="Retrieval-Augmented Generation...",
    retrieved_doc_ids=["doc1", "doc2"],
    model_used="llama3.2:3b",
    latency_ms=150.5
)
```

#### `get_interaction()`

```python
def get_interaction(self, interaction_id: str) -> Interaction
```

Get interaction by ID.

**Parameters:**
- `interaction_id` (str): Interaction ID

**Returns:**
- `Interaction`: Interaction object

**Raises:**
- `ValueError`: If interaction not found

#### `list_interactions()`

```python
def list_interactions(
    self,
    persona: str | None = None,
    limit: int = 10,
    offset: int = 0,
) -> list[Interaction]
```

List interactions for a persona.

**Parameters:**
- `persona` (str | None): Persona name (uses default if not provided)
- `limit` (int): Maximum results. Default: 10
- `offset` (int): Results to skip. Default: 0

**Returns:**
- `list[Interaction]`: List of interactions (newest first)

**Example:**
```python
# Get last 20 interactions
history = tracker.list_interactions(limit=20)
for interaction in history:
    print(f"{interaction.timestamp}: {interaction.query}")
```

#### `delete_interaction()`

```python
def delete_interaction(self, interaction_id: str, confirm: bool = False) -> None
```

Delete a specific interaction.

**Parameters:**
- `interaction_id` (str): Interaction ID to delete
- `confirm` (bool): Confirmation flag (required for safety)

**Raises:**
- `ValueError`: If confirmation not provided or interaction not found

#### `clear_interactions()`

```python
def clear_interactions(self, persona: str | None = None, confirm: bool = False) -> int
```

Clear all interactions for a persona.

**Parameters:**
- `persona` (str | None): Persona name (uses default if not provided)
- `confirm` (bool): Confirmation flag (required for safety)

**Returns:**
- `int`: Number of interactions deleted

**Raises:**
- `ValueError`: If confirmation not provided or persona not provided

#### `export_interactions()`

```python
def export_interactions(
    self,
    persona: str | None = None,
    output_path: Path | None = None,
) -> dict[str, Any]
```

Export interactions to JSON format.

**Parameters:**
- `persona` (str | None): Persona name (uses default if not provided)
- `output_path` (Path | None): Optional file path to write JSON

**Returns:**
- `dict[str, Any]`: Export data dictionary

**Example:**
```python
# Export to dict
data = tracker.export_interactions()

# Export to file
tracker.export_interactions(output_path=Path("export.json"))
```

#### `add_feedback()`

```python
def add_feedback(self, interaction_id: str, feedback: str) -> None
```

Add feedback to an existing interaction.

**Parameters:**
- `interaction_id` (str): Interaction ID
- `feedback` (str): Feedback value ("positive", "negative", or "neutral")

**Raises:**
- `ValueError`: If invalid feedback value or interaction not found

---

## Interaction

Data class representing a query/response interaction.

### Class: `Interaction`

```python
@dataclass
class Interaction:
    id: str
    persona: str
    query: str
    response: str | None
    timestamp: datetime
    retrieved_doc_ids: list[str]
    model_used: str | None
    latency_ms: float | None
    feedback: str | None
    session_id: str | None
```

**Attributes:**
- `id`: Unique identifier (UUID)
- `persona`: Associated persona
- `query`: User query text
- `response`: System response text
- `timestamp`: When interaction occurred
- `retrieved_doc_ids`: Document IDs used in response
- `model_used`: LLM model identifier
- `latency_ms`: Response time in milliseconds
- `feedback`: User feedback (positive/negative/neutral)
- `session_id`: Session identifier

### Methods

#### `to_dict()`

```python
def to_dict(self) -> dict[str, Any]
```

Serialise interaction to dictionary.

#### `from_dict()`

```python
@classmethod
def from_dict(cls, data: dict[str, Any]) -> Interaction
```

Deserialise interaction from dictionary.

---

## KnowledgeGraph

Graph database for tracking user-topic-document relationships.

### Class: `KnowledgeGraph`

```python
class KnowledgeGraph:
    def __init__(self, persona: str | None = None, storage_dir: Path | None = None) -> None
```

**Parameters:**
- `persona` (str | None): Default persona for operations
- `storage_dir` (Path | None): Custom storage directory. Default: `~/.ragged/memory/graph`

**Attributes:**
- `persona` (str | None): Default persona
- `storage_dir` (Path): Storage directory
- `db_path` (Path): Kuzu database path
- `db`: Kuzu database instance
- `conn`: Kuzu connection

### Methods

#### `ensure_user_exists()`

```python
def ensure_user_exists(self, persona: str | None = None) -> None
```

Ensure user node exists for persona.

**Parameters:**
- `persona` (str | None): Persona name (uses default if not provided)

**Raises:**
- `ValueError`: If persona not provided

#### `add_topic_interest()`

```python
def add_topic_interest(
    self,
    topic: str,
    interest_level: float = 0.5,
    persona: str | None = None,
) -> None
```

Add or update topic interest for persona.

**Parameters:**
- `topic` (str): Topic name
- `interest_level` (float): Interest level (0.0-1.0). Default: 0.5
- `persona` (str | None): Persona name (uses default if not provided)

**Raises:**
- `ValueError`: If persona not provided

**Example:**
```python
graph = KnowledgeGraph(persona="researcher")
graph.add_topic_interest("RAG", interest_level=0.9)
graph.add_topic_interest("NLP", interest_level=0.7)
```

#### `record_document_access()`

```python
def record_document_access(
    self,
    doc_id: str,
    title: str = "",
    persona: str | None = None,
) -> None
```

Record document access for persona.

**Parameters:**
- `doc_id` (str): Document identifier
- `title` (str): Document title. Default: ""
- `persona` (str | None): Persona name (uses default if not provided)

**Raises:**
- `ValueError`: If persona not provided

#### `link_topic_to_document()`

```python
def link_topic_to_document(
    self,
    topic: str,
    doc_id: str,
    relevance: float = 0.5,
) -> None
```

Link a topic to a document.

**Parameters:**
- `topic` (str): Topic name
- `doc_id` (str): Document identifier
- `relevance` (float): Relevance score (0.0-1.0). Default: 0.5

#### `get_user_interests()`

```python
def get_user_interests(self, persona: str | None = None) -> list[dict[str, Any]]
```

Get topics of interest for persona.

**Parameters:**
- `persona` (str | None): Persona name (uses default if not provided)

**Returns:**
- `list[dict]`: List of topic dictionaries

**Example:**
```python
interests = graph.get_user_interests()
for topic in interests:
    print(f"{topic['topic']}: {topic['frequency']} queries, "
          f"interest {topic['interest_level']}")
```

**Return Format:**
```python
[
    {
        "topic": "RAG",
        "interest_level": 0.9,
        "frequency": 15,
        "last_accessed": datetime(2025, 11, 23, 14, 30)
    },
    ...
]
```

#### `get_accessed_documents()`

```python
def get_accessed_documents(
    self,
    persona: str | None = None,
    limit: int = 10,
) -> list[dict[str, Any]]
```

Get recently accessed documents for persona.

**Parameters:**
- `persona` (str | None): Persona name (uses default if not provided)
- `limit` (int): Maximum results. Default: 10

**Returns:**
- `list[dict]`: List of document dictionaries (newest first)

**Return Format:**
```python
[
    {
        "doc_id": "doc123",
        "title": "RAG Paper",
        "access_count": 5,
        "last_accessed": datetime(2025, 11, 23, 14, 25)
    },
    ...
]
```

#### `get_related_documents()`

```python
def get_related_documents(self, topic: str, limit: int = 10) -> list[dict[str, Any]]
```

Get documents related to a topic.

**Parameters:**
- `topic` (str): Topic name
- `limit` (int): Maximum results. Default: 10

**Returns:**
- `list[dict]`: List of document dictionaries (highest relevance first)

**Return Format:**
```python
[
    {
        "doc_id": "doc123",
        "title": "RAG Paper",
        "relevance": 0.95
    },
    ...
]
```

#### `delete_user_data()`

```python
def delete_user_data(self, persona: str, confirm: bool = False) -> int
```

Delete all data for a persona (GDPR Article 17).

**Parameters:**
- `persona` (str): Persona name to delete
- `confirm` (bool): Confirmation flag (required for safety)

**Returns:**
- `int`: Number of nodes deleted

**Raises:**
- `ValueError`: If confirmation not provided

#### `export_graph()`

```python
def export_graph(self, persona: str | None = None) -> dict[str, Any]
```

Export graph data for a persona (GDPR Article 20).

**Parameters:**
- `persona` (str | None): Persona name (uses default if not provided)

**Returns:**
- `dict[str, Any]`: Export data dictionary

**Return Format:**
```python
{
    "persona": "researcher",
    "export_timestamp": "2025-11-23T14:30:00",
    "interests": [...],
    "documents": [...],
    "topic_document_links": [...]
}
```

#### `clear_graph()`

```python
def clear_graph(self, confirm: bool = False) -> int
```

Clear entire graph database.

**Warning:** Deletes ALL data for ALL personas.

**Parameters:**
- `confirm` (bool): Confirmation flag (required for safety)

**Returns:**
- `int`: Number of nodes deleted

**Raises:**
- `ValueError`: If confirmation not provided

#### `close()`

```python
def close(self) -> None
```

Close database connection.

**Example:**
```python
graph = KnowledgeGraph(persona="researcher")
# ... operations ...
graph.close()
```

**Context Manager:**
```python
with KnowledgeGraph(persona="researcher") as graph:
    graph.add_topic_interest("RAG")
    # Automatically closed on exit
```

---

## Complete Example

```python
from ragged.memory import PersonaManager, InteractionTracker, KnowledgeGraph

# Setup persona
manager = PersonaManager()
persona = manager.create(
    "researcher",
    description="ML researcher",
    focus=["RAG", "NLP"]
)
manager.switch("researcher")

# Track interaction
tracker = InteractionTracker(persona="researcher")
interaction = tracker.record_interaction(
    query="What is RAG?",
    response="Retrieval-Augmented Generation combines...",
    retrieved_doc_ids=["doc1", "doc2"],
    model_used="llama3.2:3b",
    latency_ms=245.8
)

# Build knowledge graph
with KnowledgeGraph(persona="researcher") as graph:
    # Add topic interest
    graph.add_topic_interest("RAG", interest_level=0.9)

    # Record document access
    graph.record_document_access("doc1", title="RAG: A Survey")
    graph.record_document_access("doc2", title="RAG Applications")

    # Link topics to documents
    graph.link_topic_to_document("RAG", "doc1", relevance=0.95)
    graph.link_topic_to_document("RAG", "doc2", relevance=0.85)

    # Query user interests
    interests = graph.get_user_interests()
    print(f"Found {len(interests)} topics")

    # Query related documents
    docs = graph.get_related_documents("RAG")
    print(f"Found {len(docs)} RAG-related documents")

# Export everything (GDPR compliance)
persona_export = manager.export_persona("researcher")
interaction_export = tracker.export_interactions()
graph_export = graph.export_graph()

print(f"Persona exported to: {persona_export}")
print(f"Interactions: {len(interaction_export['interactions'])}")
print(f"Topics: {len(graph_export['interests'])}")
```

---

## Related Documentation

- [Getting Started with Personas](../tutorials/personas-quickstart.md)
- [Memory System User Guide](../guides/memory-system.md)
- [Privacy & Data Control](../guides/privacy.md)

---

**Status**: Production-ready (v0.4.5)
