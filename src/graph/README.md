# Knowledge Graph (GraphRAG)

📋 **Status: Planned for v0.4-v0.5**

This directory will contain the knowledge graph system (GraphRAG), enabling entity-based retrieval and multi-hop reasoning over document collections.

## Planned Components

### Entity Extraction (`extraction.py`)
- Extract entities from documents (people, places, concepts)
- Named Entity Recognition (NER) using GLiNER or similar
- Relation extraction between entities
- Temporal entity tracking

### Graph Builder (`builder.py`)
- Construct knowledge graph from entities and relations
- Node types: Entities, Documents, Concepts
- Edge types: References, Related, Temporal
- Graph database integration (NetworkX → Neo4j/Kuzu)

### Graph Querier (`query.py`)
- Cypher query generation from natural language
- Subgraph extraction for relevant context
- Path finding between entities
- Community detection for document clustering

### Hybrid Retriever (`hybrid.py`)
- Combine vector search + graph traversal
- Multi-hop reasoning across documents
- Entity-based filtering and ranking
- Fusion of graph and vector results

## Architecture

```python
# Planned interface (subject to change)

class KnowledgeGraph:
    def __init__(self, graph_db: GraphDatabase):
        self.db = graph_db
        self.entity_extractor = EntityExtractor()

    def build_from_documents(
        self,
        documents: list[Document]
    ) -> None:
        """Extract entities and build knowledge graph."""
        pass

    def query(
        self,
        query: str,
        max_hops: int = 2,
        entity_types: list[str] = None
    ) -> GraphResult:
        """Query the knowledge graph."""
        pass

    def get_subgraph(
        self,
        entity: str,
        radius: int = 1
    ) -> Subgraph:
        """Extract subgraph around an entity."""
        pass
```

## Graph Schema

### Node Types

```python
# Entity Node
{
    "id": "entity_123",
    "type": "person",  # person, place, concept, organisation
    "name": "John Doe",
    "aliases": ["J. Doe", "Dr. Doe"],
    "mentions": 15,
    "first_seen": "2024-01-01",
    "properties": {...}
}

# Document Node
{
    "id": "doc_456",
    "title": "Research Paper",
    "source": "/path/to/doc.pdf",
    "embedding_id": "chroma_id_789",
    "metadata": {...}
}

# Concept Node
{
    "id": "concept_789",
    "name": "Machine Learning",
    "category": "technology",
    "related_concepts": [...]
}

# Organisation Node
{
    "id": "org_234",
    "type": "organisation",
    "name": "Example University",
    "category": "education"
}
```

### Edge Types

```python
# MENTIONS (Document -> Entity)
{
    "type": "MENTIONS",
    "count": 5,
    "context": ["sentence 1", "sentence 2"],
    "importance": 0.8
}

# RELATES_TO (Entity -> Entity)
{
    "type": "RELATES_TO",
    "relation": "works_with",  # works_with, located_in, part_of
    "confidence": 0.9,
    "source_doc": "doc_456"
}

# TEMPORAL (Entity -> Entity)
{
    "type": "TEMPORAL",
    "relation": "before",  # before, after, concurrent
    "timestamp": "2024-01-01"
}
```

## GraphRAG Query Flow

```
User Query: "What did John Doe publish about ML?"
    ↓
1. Entity Recognition in Query
    → Entities: ["John Doe", "ML"]
    ↓
2. Graph Traversal
    → Find John Doe node
    → Traverse MENTIONS edges to documents
    → Filter documents mentioning ML concept
    ↓
3. Vector Search
    → Use filtered documents as candidates
    → Semantic search within subgraph
    ↓
4. Context Building
    → Include entity relationships
    → Add temporal context
    → Graph-aware chunking
    ↓
5. Generation
    → Structured response with entity graph
    → Visualize entity relationships
    → Provide document citations
```

## Entity Extraction

Using GLiNER or similar models:

```python
# Extract entities
entities = entity_extractor.extract(text)

# Output
[
    {
        "text": "John Doe",
        "type": "person",
        "span": (0, 8),
        "confidence": 0.95
    },
    {
        "text": "Stanford University",
        "type": "organization",
        "span": (25, 44),
        "confidence": 0.92
    }
]
```

## Graph Databases

### Phase 1 (v0.4): NetworkX
- In-memory graph
- Lightweight, no external dependencies
- Good for prototyping
- Limited to single machine

### Phase 2 (v0.5): Neo4j or Kuzu
- Persistent graph storage
- Cypher query language
- Scalable to large graphs
- Advanced algorithms (PageRank, community detection)

**Kuzu advantages:**
- Embedded database (like SQLite for graphs)
- No server required
- Better privacy (all local)
- Fast analytical queries

## Community Detection

Group related documents by entity clusters:

```python
# Detect communities
communities = graph.detect_communities(algorithm="louvain")

# Get documents in community
docs = graph.get_community_documents(community_id=3)

# Community-based retrieval
results = retriever.retrieve_from_community(
    query="What is RAG?",
    community_id=3
)
```

## Multi-Hop Reasoning

```python
# Find path between entities
path = graph.find_path(
    start="John Doe",
    end="Neural Networks",
    max_hops=3
)

# Path: John Doe → Published → Paper X → Mentions → Neural Networks

# Use path for context
context = graph.extract_path_context(path)
```

## Visualization

Generate graph visualizations for users:

```python
# Export subgraph for visualization
subgraph = graph.get_subgraph(entity="Machine Learning", radius=2)
graph.visualize(subgraph, format="html")

# Interactive visualization in web UI
# Using vis.js, D3.js, or similar
```

## Configuration

```yaml
# ~/.ragged/config.yml
graph:
  enabled: true
  database: "kuzu"  # networkx, neo4j, kuzu
  entity_extraction:
    model: "gliner-large-v2"
    batch_size: 32
    min_confidence: 0.7
  graph_building:
    deduplicate_entities: true
    relation_threshold: 0.8
  retrieval:
    enable_graph_retrieval: true
    max_hops: 2
    graph_weight: 0.4  # vs vector weight 0.6
```

## Testing

- Unit tests for entity extraction
- Graph construction tests
- Query performance tests
- Multi-hop reasoning tests
- Community detection accuracy tests

## Performance Considerations

- Incremental graph building (don't rebuild entire graph)
- Entity caching
- Subgraph caching for common queries
- Lazy loading of graph neighborhoods

## See Also

- [v0.4 Roadmap](../../docs/development/roadmaps/version/v0.4.0/)
- [v0.5 Roadmap](../../docs/development/roadmaps/version/v0.5.0/)
- [Architecture Planning](../../docs/development/planning/architecture/)
- [GraphRAG Research](../../docs/research/background/)

---

**Note:** This is a planning directory. Implementation will begin in v0.4-v0.5 development cycles.
