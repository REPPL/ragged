# Personal Memory and Persona System

**Version**: 2.0
**Last Updated**: 2025-11-09
**Status**: Design Complete
**Implementation Target**: v0.3+

---

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Persona System](#persona-system)
4. [Memory Types](#memory-types)
5. [Storage Architecture](#storage-architecture)
6. [Privacy and Security](#privacy-and-security)
7. [Implementation Roadmap](#implementation-roadmap)
8. [Integration with RAG](#integration-with-rag)

---

## Overview

### Purpose

ragged's personal memory and persona system transforms it from a simple RAG tool into a personalised research assistant that:

- **Remembers** user preferences, behaviours, and interaction history
- **Adapts** to individual working styles and research areas
- **Switches contexts** via configurable personas (researcher, developer, casual user, etc.)
- **Extends automatically** based on usage patterns
- **Respects privacy** with local-only storage and explicit user control

### Key Features

1. **Multi-Persona Support**: Switch between different working contexts (researcher, developer, student)
2. **Automatic Enrichment**: Learn from user behaviour without manual configuration
3. **Explicit Preferences**: User-configurable settings that override defaults
4. **Temporal Context**: Remember what you were working on last week/month
5. **Cross-Document Insights**: Track connections between topics across your research
6. **Privacy-First**: All memory stored locally, exportable, deletable

### Design Principles

- **Transparency**: User always knows what's being remembered
- **Control**: User can view, edit, and delete any memory
- **Privacy**: No cloud synchronization by default, all local
- **Gradual Enhancement**: Start simple, add capabilities over time
- **Persona Isolation**: Memories can be persona-specific or shared

---

## Architecture

### High-Level Components

```
┌─────────────────────────────────────────────────────────────────┐
│                         User Interaction                         │
└──────────────────┬──────────────────────────────────────────────┘
                   │
                   ▼
    ┌──────────────────────────────┐
    │    Persona Manager           │
    │  - Active persona            │
    │  - Persona switching         │
    │  - Context selection         │
    └─────────┬────────────────────┘
              │
              ▼
    ┌──────────────────────────────┐
    │   Memory Coordinator         │
    │  - Query memory              │
    │  - Update memory             │
    │  - Context injection         │
    └─────────┬────────────────────┘
              │
              ├─────────────┬──────────────┬─────────────┐
              │             │              │             │
              ▼             ▼              ▼             ▼
     ┌──────────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────┐
     │  Interaction │ │ Semantic │ │ Temporal │ │  Preferences │
     │    Memory    │ │  Memory  │ │  Graph   │ │    Store     │
     │   (SQLite)   │ │ (Vector) │ │  (Kuzu)  │ │   (SQLite)   │
     └──────────────┘ └──────────┘ └──────────┘ └──────────────┘
              │             │              │             │
              └─────────────┴──────────────┴─────────────┘
                                  │
                                  ▼
                     ┌──────────────────────────┐
                     │  Integration with RAG    │
                     │  - Query rewriting       │
                     │  - Context filtering     │
                     │  - Personalised ranking  │
                     └──────────────────────────┘
```

### Component Descriptions

**Persona Manager**
- Manages active persona and switching
- Determines which memories are accessible
- Provides persona-specific context to queries

**Memory Coordinator**
- Central interface for all memory operations
- Routes memory queries to appropriate stores
- Manages memory lifecycle (create, update, delete)
- Handles memory prioritization and context injection

**Interaction Memory (SQLite)**
- Stores interaction history (queries, responses, timestamps)
- Tracks reading history and document access
- Records user feedback and corrections

**Semantic Memory (Vector Store)**
- Embeddings of past queries and interests
- Topic clusters and research areas
- Enables similarity-based memory retrieval

**Temporal Graph (Kuzu)**
- Tracks temporal relationships between entities
- "What was I working on last week?"
- Project evolution over time
- Fact verification with timestamps

**Preferences Store (SQLite)**
- Explicit user preferences (language, formality, model preferences)
- Persona configurations
- Feature toggles and settings

---

## Persona System

### What is a Persona?

A **persona** is a configurable context that tailors ragged's behaviour to specific use cases:

```python
@dataclass
class Persona:
    """Persona configuration"""
    name: str                          # "researcher", "developer", "casual"
    description: str                   # Human-readable description

    # Behavioural settings
    response_style: str                # "academic", "technical", "conversational"
    detail_level: str                  # "concise", "balanced", "comprehensive"
    citation_style: str                # "apa", "mla", "chicago", "inline"

    # Model preferences
    preferred_model_tier: str          # "fast", "balanced", "quality"
    task_model_overrides: dict         # {"code_generation": "codellama:34b"}

    # Memory settings
    memory_scope: str                  # "persona_only", "shared", "custom"
    auto_enrich: bool = True          # Auto-learn from interactions

    # Active context
    active_projects: list[str] = []    # Current research projects
    focus_areas: list[str] = []        # Topic areas of interest

    # Metadata
    created_at: datetime
    last_used: datetime
    usage_count: int = 0
```

### Built-In Personas

**Researcher Persona**
```yaml
name: researcher
description: Academic research assistant
response_style: academic
detail_level: comprehensive
citation_style: apa
preferred_model_tier: quality
task_model_overrides:
  reasoning: llama3.3:70b
  summarization: qwen2.5:32b
memory_scope: persona_only
auto_enrich: true
focus_areas:
  - research_methodology
  - academic_writing
  - literature_review
```

**Developer Persona**
```yaml
name: developer
description: Programming and software development assistant
response_style: technical
detail_level: balanced
citation_style: inline
preferred_model_tier: quality
task_model_overrides:
  code_generation: codellama:34b
  code_review: deepseek-coder:33b
memory_scope: persona_only
auto_enrich: true
focus_areas:
  - software_engineering
  - code_patterns
  - debugging
```

**Casual User Persona**
```yaml
name: casual
description: General-purpose assistant
response_style: conversational
detail_level: concise
citation_style: inline
preferred_model_tier: fast
memory_scope: shared
auto_enrich: true
```

### Persona Switching

**Explicit Switching**:
```bash
# CLI
ragged --persona researcher "Summarize the latest papers on RAG evaluation"

# Interactive
> /persona researcher
Switched to persona: researcher (Academic research assistant)

> What are the current state-of-the-art RAG metrics?
[Response uses academic style, comprehensive detail, APA citations...]

> /persona developer
Switched to persona: developer (Programming assistant)

> How do I implement RAG evaluation in Python?
[Response uses technical style, code examples, inline citations...]
```

**Context-Aware Auto-Switching** (Future Enhancement):
```python
# Detect coding question → suggest developer persona
query = "Write a function to parse JSON"
suggested_persona = persona_detector.suggest(query)  # → "developer"
```

### Persona Memory Isolation

Each persona can have:
- **Isolated memories**: Only accessible when that persona is active
- **Shared memories**: Accessible across all personas (e.g., general preferences)
- **Custom sharing**: Specific memories shared between select personas

```
Researcher Persona Memory:
  - Papers read in this persona
  - Research projects
  - Academic vocabulary preferences
  - Shared: General language preference, timezone

Developer Persona Memory:
  - Code repositories accessed
  - Programming languages used
  - Code style preferences
  - Shared: General language preference, timezone

Shared Memory Pool:
  - Language preference (Spanish/English)
  - Timezone
  - Privacy settings
  - General topics of interest
```

---

## Memory Types

### 1. Interaction Memory

**What It Stores**:
- Every query and response
- Document access history
- User feedback (thumbs up/down, corrections)
- Session metadata

**Schema**:
```sql
CREATE TABLE interactions (
    id TEXT PRIMARY KEY,
    persona TEXT NOT NULL,
    timestamp DATETIME NOT NULL,
    query TEXT NOT NULL,
    response TEXT,
    retrieved_doc_ids TEXT,  -- JSON array
    model_used TEXT,
    latency_ms REAL,
    user_feedback TEXT,      -- 'positive', 'negative', 'corrected'
    correction TEXT,         -- User's correction if provided
    session_id TEXT,
    metadata TEXT            -- JSON for extensibility
);

CREATE INDEX idx_interactions_persona ON interactions(persona);
CREATE INDEX idx_interactions_timestamp ON interactions(timestamp);
CREATE INDEX idx_interactions_session ON interactions(session_id);
```

**Use Cases**:
- "What was I asking about last Tuesday?"
- Detect topic shifts and project changes
- Learn from user corrections
- Improve responses based on feedback history

**Implementation**:
```python
class InteractionMemory:
    """Track all user interactions"""

    def record_interaction(
        self,
        persona: str,
        query: str,
        response: str,
        retrieved_docs: list,
        model: str,
        latency: float
    ):
        """Record new interaction"""
        interaction = {
            "id": generate_id(),
            "persona": persona,
            "timestamp": datetime.now(),
            "query": query,
            "response": response,
            "retrieved_doc_ids": json.dumps([d.id for d in retrieved_docs]),
            "model_used": model,
            "latency_ms": latency * 1000,
            "session_id": current_session_id(),
        }

        self.db.insert("interactions", interaction)

        # Also store in semantic memory for similarity search
        query_embedding = self.embedder.embed(query)
        self.semantic_memory.add(
            id=interaction["id"],
            embedding=query_embedding,
            metadata=interaction
        )

    def get_recent_by_persona(self, persona: str, limit: int = 10):
        """Get recent interactions for persona"""
        return self.db.query("""
            SELECT * FROM interactions
            WHERE persona = ?
            ORDER BY timestamp DESC
            LIMIT ?
        """, (persona, limit))

    def get_similar_past_queries(self, query: str, limit: int = 5):
        """Find similar past queries"""
        query_embedding = self.embedder.embed(query)
        similar = self.semantic_memory.query(
            query_embedding=query_embedding,
            n_results=limit
        )
        return similar
```

### 2. Semantic Memory

**What It Stores**:
- Topic clusters (automatically identified)
- Research areas and interests
- Concept relationships
- Query embeddings for similarity search

**Implementation**:
```python
class SemanticMemory:
    """Vector-based semantic memory"""

    def __init__(self, collection_name="semantic_memory"):
        self.chroma = chromadb.PersistentClient(path="./memory_db")
        self.collection = self.chroma.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"}
        )

    def add(self, id: str, embedding: list[float], metadata: dict):
        """Add to semantic memory"""
        self.collection.add(
            ids=[id],
            embeddings=[embedding],
            metadatas=[metadata]
        )

    def find_similar(self, embedding: list[float], n_results: int = 10):
        """Find semantically similar memories"""
        return self.collection.query(
            query_embeddings=[embedding],
            n_results=n_results
        )

    def cluster_topics(self) -> dict:
        """Identify topic clusters from interaction history"""
        # Get all interaction embeddings
        all_memories = self.collection.get()

        if len(all_memories['ids']) < 10:
            return {}  # Not enough data

        # Cluster using HDBSCAN or K-means
        from sklearn.cluster import HDBSCAN

        embeddings = np.array(all_memories['embeddings'])
        clusterer = HDBSCAN(min_cluster_size=3)
        labels = clusterer.fit_predict(embeddings)

        # Extract representative queries for each cluster
        clusters = {}
        for cluster_id in set(labels):
            if cluster_id == -1:  # Noise
                continue

            cluster_indices = np.where(labels == cluster_id)[0]
            cluster_queries = [
                all_memories['metadatas'][i]['query']
                for i in cluster_indices
            ]

            # Get cluster centroid and closest query
            centroid = embeddings[cluster_indices].mean(axis=0)
            closest_idx = cluster_indices[
                np.argmin(np.linalg.norm(embeddings[cluster_indices] - centroid, axis=1))
            ]
            representative = all_memories['metadatas'][closest_idx]['query']

            clusters[f"topic_{cluster_id}"] = {
                "representative_query": representative,
                "query_count": len(cluster_queries),
                "queries": cluster_queries[:10],  # Sample
            }

        return clusters
```

**Use Cases**:
- "Show me topics I've been researching"
- Detect topic drift and new interests
- Surface related past queries
- Personalise retrieval based on topic preferences

### 3. Temporal Graph

**What It Stores**:
- Time-aware relationships between concepts
- Project timelines
- Evolution of topics over time
- Fact verification with timestamps

**Why Temporal Graph?**

Research shows temporal knowledge graphs significantly outperform traditional semantic memory for time-aware queries:
- **Zep (2025)**: 94.8% DMR (Dialog Memory Recall), 18.5% improvement
- **Mem0 (2024)**: Graph-based memory improves entity tracking
- **Key benefit**: "What was I working on last week?" queries

**Implementation (Kuzu Embedded Graph DB)**:
```python
import kuzu

class TemporalMemory:
    """Temporal knowledge graph for time-aware memory"""

    def __init__(self, db_path="./memory_graph"):
        self.db = kuzu.Database(db_path)
        self.conn = kuzu.Connection(self.db)
        self._create_schema()

    def _create_schema(self):
        """Create graph schema"""
        # Nodes
        self.conn.execute("""
            CREATE NODE TABLE IF NOT EXISTS Entity(
                name STRING,
                type STRING,
                first_seen TIMESTAMP,
                last_seen TIMESTAMP,
                PRIMARY KEY(name)
            )
        """)

        self.conn.execute("""
            CREATE NODE TABLE IF NOT EXISTS Topic(
                name STRING,
                category STRING,
                interest_level FLOAT,
                PRIMARY KEY(name)
            )
        """)

        self.conn.execute("""
            CREATE NODE TABLE IF NOT EXISTS Document(
                doc_id STRING,
                title STRING,
                accessed_at TIMESTAMP,
                PRIMARY KEY(doc_id)
            )
        """)

        # Relationships
        self.conn.execute("""
            CREATE REL TABLE IF NOT EXISTS WORKED_ON(
                FROM Entity TO Topic,
                start_time TIMESTAMP,
                end_time TIMESTAMP,
                intensity FLOAT
            )
        """)

        self.conn.execute("""
            CREATE REL TABLE IF NOT EXISTS RELATED_TO(
                FROM Topic TO Topic,
                strength FLOAT,
                first_connected TIMESTAMP
            )
        """)

        self.conn.execute("""
            CREATE REL TABLE IF NOT EXISTS ACCESSED(
                FROM Entity TO Document,
                timestamp TIMESTAMP,
                purpose STRING
            )
        """)

    def record_topic_activity(
        self,
        user: str,
        topic: str,
        intensity: float = 1.0
    ):
        """Record user working on a topic"""
        now = datetime.now()

        # Ensure entities exist
        self.conn.execute("""
            MERGE (u:Entity {name: $user})
            ON CREATE SET u.type = 'User', u.first_seen = $now
            ON MATCH SET u.last_seen = $now
        """, {"user": user, "now": now})

        self.conn.execute("""
            MERGE (t:Topic {name: $topic})
            ON CREATE SET t.interest_level = $intensity
            ON MATCH SET t.interest_level = t.interest_level * 0.9 + $intensity * 0.1
        """, {"topic": topic, "intensity": intensity})

        # Create/update relationship
        self.conn.execute("""
            MATCH (u:Entity {name: $user})
            MATCH (t:Topic {name: $topic})
            MERGE (u)-[w:WORKED_ON]->(t)
            ON CREATE SET w.start_time = $now, w.intensity = $intensity
            ON MATCH SET w.end_time = $now, w.intensity = w.intensity * 0.9 + $intensity * 0.1
        """, {"user": user, "topic": topic, "now": now, "intensity": intensity})

    def get_recent_topics(self, user: str, since: datetime) -> list[str]:
        """Get topics user worked on since date"""
        result = self.conn.execute("""
            MATCH (u:Entity {name: $user})-[w:WORKED_ON]->(t:Topic)
            WHERE w.end_time >= $since
            RETURN t.name, w.intensity, w.end_time
            ORDER BY w.end_time DESC
        """, {"user": user, "since": since})

        return [row[0] for row in result.get_all()]

    def get_topic_evolution(self, topic: str) -> dict:
        """Get timeline of topic activity"""
        result = self.conn.execute("""
            MATCH (u:Entity)-[w:WORKED_ON]->(t:Topic {name: $topic})
            RETURN w.start_time, w.end_time, w.intensity
            ORDER BY w.start_time
        """, {"topic": topic})

        timeline = []
        for row in result.get_all():
            timeline.append({
                "start": row[0],
                "end": row[1],
                "intensity": row[2]
            })

        return {"topic": topic, "timeline": timeline}

    def find_topic_connections(self, topic: str, max_distance: int = 2) -> list:
        """Find related topics within graph distance"""
        result = self.conn.execute("""
            MATCH path = (t1:Topic {name: $topic})-[*1..$max_dist]-(t2:Topic)
            WHERE t1 <> t2
            RETURN DISTINCT t2.name, length(path) as distance
            ORDER BY distance, t2.interest_level DESC
            LIMIT 10
        """, {"topic": topic, "max_dist": max_distance})

        return [{"topic": row[0], "distance": row[1]} for row in result.get_all()]
```

**Use Cases**:
- "What was I working on last week?"
- Track project evolution over time
- Detect topic shifts and new research directions
- Verify facts with temporal context ("When did I learn about X?")

### 4. Preferences Store

**What It Stores**:
- Explicit user preferences (language, citation style, formality)
- Persona configurations
- Model preferences per task
- Feature toggles

**Schema**:
```sql
CREATE TABLE preferences (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,        -- JSON-encoded value
    persona TEXT,               -- NULL for global, persona name for specific
    category TEXT NOT NULL,     -- 'language', 'model', 'ui', 'privacy'
    updated_at DATETIME NOT NULL
);

CREATE TABLE persona_configs (
    name TEXT PRIMARY KEY,
    config TEXT NOT NULL,       -- JSON-encoded Persona object
    created_at DATETIME NOT NULL,
    last_used DATETIME,
    usage_count INTEGER DEFAULT 0
);

CREATE INDEX idx_preferences_persona ON preferences(persona);
CREATE INDEX idx_preferences_category ON preferences(category);
```

**Implementation**:
```python
class PreferencesStore:
    """User preferences and persona configurations"""

    def get_preference(self, key: str, persona: str = None, default=None):
        """Get preference value (persona-specific or global)"""
        # Try persona-specific first
        if persona:
            value = self.db.query(
                "SELECT value FROM preferences WHERE key = ? AND persona = ?",
                (key, persona)
            )
            if value:
                return json.loads(value[0]['value'])

        # Fall back to global
        value = self.db.query(
            "SELECT value FROM preferences WHERE key = ? AND persona IS NULL",
            (key,)
        )

        return json.loads(value[0]['value']) if value else default

    def set_preference(self, key: str, value: any, persona: str = None, category: str = "general"):
        """Set preference"""
        self.db.execute("""
            INSERT OR REPLACE INTO preferences (key, value, persona, category, updated_at)
            VALUES (?, ?, ?, ?, ?)
        """, (key, json.dumps(value), persona, category, datetime.now()))

    def get_persona(self, name: str) -> Persona:
        """Get persona configuration"""
        result = self.db.query(
            "SELECT config FROM persona_configs WHERE name = ?",
            (name,)
        )

        if not result:
            return None

        config = json.loads(result[0]['config'])
        return Persona(**config)

    def save_persona(self, persona: Persona):
        """Save persona configuration"""
        self.db.execute("""
            INSERT OR REPLACE INTO persona_configs (name, config, created_at, last_used, usage_count)
            VALUES (?, ?, ?, ?, ?)
        """, (
            persona.name,
            json.dumps(asdict(persona)),
            persona.created_at,
            persona.last_used,
            persona.usage_count
        ))
```

---

## Storage Architecture

### File System Layout

```
~/.ragged/
├── memory/
│   ├── interactions.db         # SQLite: interaction history
│   ├── preferences.db          # SQLite: preferences and personas
│   ├── semantic/               # ChromaDB: semantic memory
│   │   ├── chroma.sqlite3
│   │   └── ...
│   └── temporal/               # Kuzu: temporal graph
│       ├── catalog.db
│       └── ...
│
├── personas/
│   ├── researcher.yaml         # Persona config (human-editable)
│   ├── developer.yaml
│   └── custom_personas/
│       └── user_defined.yaml
│
└── exports/                    # User exports for backup
    ├── memory_export_2025-11-09.json
    └── ...
```

### Database Sizes (Estimated)

For **100,000 interactions** over 1 year:

```
Component               Size        Growth Rate
-------------------------------------------------
Interactions DB         50 MB       ~150 KB/day
Semantic Memory         200 MB      ~600 KB/day (embeddings)
Temporal Graph          100 MB      ~300 KB/day
Preferences DB          < 1 MB      Minimal
-------------------------------------------------
Total                   ~350 MB     ~1 MB/day

After 5 years:          ~1.8 GB
```

**Management**:
- Automatic archival of old interactions (> 2 years)
- On-demand cleanup of semantic memory clusters
- Temporal graph pruning (keep recent + important)

### Privacy-Preserving Design

**Encryption at Rest** (Optional):
```python
from cryptography.fernet import Fernet

class EncryptedMemory:
    """Encrypted memory storage"""

    def __init__(self, key_path="~/.ragged/memory.key"):
        self.key_path = Path(key_path).expanduser()
        self.key = self._load_or_create_key()
        self.cipher = Fernet(self.key)

    def _load_or_create_key(self):
        """Load encryption key or create new one"""
        if self.key_path.exists():
            return self.key_path.read_bytes()
        else:
            key = Fernet.generate_key()
            self.key_path.write_bytes(key)
            self.key_path.chmod(0o600)  # Owner read/write only
            return key

    def encrypt(self, data: str) -> bytes:
        """Encrypt data"""
        return self.cipher.encrypt(data.encode())

    def decrypt(self, encrypted: bytes) -> str:
        """Decrypt data"""
        return self.cipher.decrypt(encrypted).decode()
```

**Export/Delete**:
```python
class MemoryManager:
    """Manage memory lifecycle"""

    def export_memory(self, output_path: Path, persona: str = None):
        """Export all memory to JSON (GDPR compliance)"""
        export = {
            "exported_at": datetime.now().isoformat(),
            "persona": persona,
            "interactions": self.interaction_memory.export(persona),
            "preferences": self.preferences.export(persona),
            "semantic_clusters": self.semantic_memory.cluster_topics(),
            "temporal_activity": self.temporal_memory.export_timeline(persona),
        }

        output_path.write_text(json.dumps(export, indent=2))

        return export

    def delete_persona_memory(self, persona: str, confirm: bool = False):
        """Delete all memory for a persona"""
        if not confirm:
            raise ValueError("Must explicitly confirm deletion")

        # Delete from all stores
        self.interaction_memory.delete_persona(persona)
        self.preferences.delete_persona(persona)
        self.semantic_memory.delete_persona(persona)
        self.temporal_memory.delete_persona(persona)

        logger.info(f"Deleted all memory for persona: {persona}")
```

---

## Privacy and Security

### Privacy Guarantees

1. **Local-Only Storage**: All memory stored in `~/.ragged/memory/`
2. **No Cloud Sync**: Memory never leaves local machine (unless explicitly exported)
3. **User Control**: View, edit, delete any memory at any time
4. **Transparent Collection**: Clear documentation of what's stored and why
5. **Persona Isolation**: Memories can be isolated per persona

### User Controls

**View Memory**:
```bash
# View recent interactions
ragged memory list --limit 10

# View by persona
ragged memory list --persona researcher --limit 20

# Search memory
ragged memory search "machine learning" --timeframe "last week"

# View topic clusters
ragged memory topics
```

**Edit Memory**:
```bash
# Correct a stored interaction
ragged memory edit <interaction_id> --correction "Corrected response text"

# Update preference
ragged memory set language spanish --persona researcher

# Delete specific memory
ragged memory delete <interaction_id>
```

**Export/Backup**:
```bash
# Export all memory
ragged memory export ~/backup/memory_2025-11-09.json

# Export specific persona
ragged memory export ~/backup/researcher_memory.json --persona researcher

# Import memory
ragged memory import ~/backup/memory_2025-11-09.json
```

**Clear Memory**:
```bash
# Clear all memory (requires confirmation)
ragged memory clear --confirm

# Clear persona memory
ragged memory clear --persona researcher --confirm

# Clear old interactions (> 2 years)
ragged memory archive --older-than "2 years"
```

### Security Considerations

**Prompt Injection Resistance**:
- Memory contents treated as data, not instructions
- System prompts isolated from user memory
- No direct execution of memory-stored code

**PII Handling**:
- Optional PII detection and redaction
- Sensitive data flagging
- Configurable PII storage policies

```python
class PIIHandler:
    """Handle PII in memory"""

    def __init__(self, policy: str = "store"):
        """
        policy: 'store' (default), 'redact', 'flag', 'reject'
        """
        self.policy = policy
        self.detector = PIIDetector()  # Using Presidio or similar

    def process_before_storage(self, text: str) -> str:
        """Process text before storing in memory"""
        pii_detected = self.detector.detect(text)

        if not pii_detected:
            return text

        if self.policy == "store":
            return text  # Store as-is
        elif self.policy == "redact":
            return self.detector.redact(text)
        elif self.policy == "flag":
            # Store but mark as containing PII
            return text
        elif self.policy == "reject":
            raise ValueError("PII detected, storage rejected per policy")
```

---

## Implementation Roadmap

### Phase 1: Basic Memory (v0.3)

**Goal**: Simple interaction tracking and preferences

**Features**:
- Interaction history (query/response pairs)
- Basic preferences store (language, model preference)
- Single global "persona" (no switching yet)
- SQLite-based storage

**Effort**: 15-20 hours

**Dependencies**:
- SQLite
- Basic embedding model for semantic search

### Phase 2: Persona System (v0.4)

**Goal**: Multi-persona support and automatic enrichment

**Features**:
- Persona definitions and switching
- Persona-specific memory isolation
- Automatic topic detection
- Reading history tracking

**Effort**: 20-25 hours

**Dependencies**:
- ChromaDB for semantic memory
- Clustering algorithms (scikit-learn)

### Phase 3: Temporal Graph (v0.5)

**Goal**: Time-aware memory and project tracking

**Features**:
- Temporal knowledge graph (Kuzu)
- "What was I working on..." queries
- Project timeline visualization
- Topic evolution tracking

**Effort**: 25-30 hours

**Dependencies**:
- Kuzu embedded graph database
- Graph visualization (optional)

### Phase 4: Advanced Features (v1.0)

**Goal**: Production-ready personal memory

**Features**:
- Memory export/import (GDPR compliance)
- Encryption at rest
- PII detection and handling
- Memory analytics and insights
- Automatic memory optimisation

**Effort**: 20-25 hours

---

## Integration with RAG

### Query Rewriting with Personal Context

**Basic Query**:
```
User: "What are the latest papers on this topic?"
```

**Enhanced with Memory**:
```python
def enhance_query_with_memory(query: str, persona: str) -> str:
    """Add personal context to query"""

    # Get recent topics for persona
    recent_topics = memory.temporal.get_recent_topics(
        user=persona,
        since=datetime.now() - timedelta(weeks=1)
    )

    # Get similar past queries
    similar = memory.semantic.find_similar(
        embedding=embedder.embed(query),
        n_results=3
    )

    # Enhance query
    enhanced = f"""
    Query: {query}

    Context from user's recent work:
    - Recent topics: {', '.join(recent_topics[:3])}
    - Similar past queries: {', '.join([q['query'] for q in similar[:2]])}

    Focus on topics related to user's current research areas: {recent_topics[0]}
    """

    return enhanced
```

**Result**:
```
User: "What are the latest papers on this topic?"

Enhanced Query (internal):
"""
Query: What are the latest papers on this topic?

Context from user's recent work:
- Recent topics: RAG evaluation metrics, prompt engineering, LangChain
- Similar past queries:
  - "What are the best RAG evaluation frameworks?"
  - "How do I measure retrieval quality?"

Focus on topics related to user's current research areas: RAG evaluation metrics
"""

Response: "Based on your recent focus on RAG evaluation metrics, here are the latest papers..."
```

### Personalised Retrieval

**Filter by Relevance to User's Interests**:
```python
def personalized_retrieval(query: str, persona: str, k: int = 5) -> list:
    """Retrieve documents with personalisation"""

    # Standard retrieval
    candidates = standard_retriever.retrieve(query, k=k*3)  # Get 3x candidates

    # Get user's topic preferences
    topic_preferences = memory.semantic.cluster_topics()

    # Re-rank based on topic alignment
    scored_candidates = []
    for doc in candidates:
        base_score = doc.similarity_score

        # Boost if doc's topics align with user's interests
        topic_boost = calculate_topic_alignment(
            doc.topics,
            topic_preferences
        )

        # Boost if user has accessed this doc before
        access_history = memory.interaction.get_document_access(doc.id, persona)
        recency_boost = 0.1 if access_history else 0

        final_score = base_score * (1 + topic_boost + recency_boost)
        scored_candidates.append((doc, final_score))

    # Return top k after re-ranking
    scored_candidates.sort(key=lambda x: x[1], reverse=True)
    return [doc for doc, score in scored_candidates[:k]]
```

### Response Adaptation

**Adapt Response Style to Persona**:
```python
def generate_personalized_response(
    query: str,
    context: list,
    persona: Persona
) -> str:
    """Generate response tailored to persona preferences"""

    # Build system prompt from persona
    system_prompt = f"""
    You are a {persona.description}.

    Response style: {persona.response_style}
    Detail level: {persona.detail_level}
    Citation style: {persona.citation_style}

    The user is currently working on: {', '.join(persona.active_projects)}
    Focus areas: {', '.join(persona.focus_areas)}

    Adapt your response accordingly.
    """

    # Generate with persona context
    response = llm.generate(
        system=system_prompt,
        query=query,
        context=context
    )

    return response
```

**Example Difference**:

**Researcher Persona**:
```
Query: "What are the benefits of RAG?"

Response:
Retrieval-Augmented Generation (RAG) offers several key advantages for
question-answering systems:

1. **Improved Factual Accuracy**: By grounding responses in retrieved documents,
   RAG significantly reduces hallucinations compared to pure generative approaches
   (Lewis et al., 2020).

2. **Dynamic Knowledge Updates**: Unlike models with static knowledge cutoffs,
   RAG can access up-to-date information from external knowledge bases
   (Guu et al., 2020).

3. **Transparency and Provenance**: Retrieved documents provide explicit sources
   for generated answers, enabling verification (Thorne et al., 2018).

References:
Lewis, P., et al. (2020). Retrieval-Augmented Generation for Knowledge-Intensive
NLP Tasks. NeurIPS 2020.
...
```

**Casual Persona**:
```
Query: "What are the benefits of RAG?"

Response:
RAG (Retrieval-Augmented Generation) is pretty cool! Here's why:

• More accurate answers - it looks up real info instead of making things up
• Always up-to-date - pulls from current documents, not old training data
• Shows sources - you can check where the answer came from

Think of it like a smart assistant that actually reads your documents before
answering, instead of just guessing.
```

---

## Example Use Cases

### Use Case 1: Research Project Tracking

**Scenario**: User is researching RAG evaluation metrics over several weeks

**Week 1**:
```bash
> What are the best metrics for evaluating RAG systems?

[Response about RAGAS, faithfulness, relevance...]

Memory records:
- Topic: "RAG evaluation metrics"
- Documents accessed: ragas_paper.pdf, rag_survey.pdf
- Interaction stored with embeddings
```

**Week 2**:
```bash
> How do I implement faithfulness scoring?

[Memory enriches query with context:]
- User recently asked about RAG evaluation metrics
- Focusing on faithfulness specifically
- Retrieved documents: ragas_paper.pdf (high relevance - user accessed before)

[Personalised response with code examples, references to papers user already read]

Memory records:
- Topic: "RAG evaluation metrics" (reinforced)
- Sub-topic: "faithfulness scoring" (new)
- Temporal link: Week 1 topic → Week 2 subtopic
```

**Week 3**:
```bash
> What was I researching last week?

[Temporal graph query:]
MATCH (u:User)-[w:WORKED_ON]->(t:Topic)
WHERE w.end_time >= date('2025-11-02') AND w.end_time <= date('2025-11-09')
RETURN t.name, w.intensity
ORDER BY w.intensity DESC

Response:
"Last week you were focused on:
1. RAG evaluation metrics (high intensity)
   - Specifically: faithfulness scoring, RAGAS framework
   - Documents: ragas_paper.pdf, rag_survey.pdf, implementation_guide.md
2. Prompt engineering (medium intensity)

Your research seems to be evolving from general RAG evaluation toward
implementation-specific details."
```

### Use Case 2: Multi-Persona Workflow

**Developer Persona**:
```bash
> /persona developer

> How do I implement vector search in Python?

[Response: Technical, code-focused, inline citations]

Memory records (developer persona):
- Topic: "vector search implementation"
- Code examples stored for reference
```

**Researcher Persona**:
```bash
> /persona researcher

> What are the theoretical foundations of vector search?

[Response: Academic, comprehensive, APA citations]

Memory records (researcher persona):
- Topic: "vector search theory"
- Papers: [academic references]

Note: "vector search implementation" from developer persona
       is NOT visible to researcher persona (persona isolation)
```

**Shared Context**:
```bash
> /preference language Spanish --global

[Sets global preference, applies to all personas]

> /persona developer
> Cómo implemento búsqueda vectorial?

[Response in Spanish, technical style]
```

### Use Case 3: Automatic Topic Detection and Adaptation

**Session 1**: User asks about machine learning
**Session 2**: User asks about deep learning
**Session 3**: User asks about transformers

**Semantic Memory** detects topic cluster:
```python
{
    "topic_0": {
        "representative_query": "What are transformers?",
        "query_count": 15,
        "cluster_label": "Deep Learning & Transformers",
        "interest_level": 0.85
    }
}
```

**Future Query**:
```bash
> Tell me about attention mechanisms

[Memory recognizes this aligns with "Deep Learning & Transformers" cluster]
[Retrieval boosted for documents in this topic area]
[Response style: Assumes user has background knowledge based on query history]

Response: "Building on your recent exploration of transformers, attention
mechanisms are the core innovation that... [assumes familiarity with basics,
focuses on advanced concepts]"
```

---

## API Reference

### Memory Coordinator

```python
class MemoryCoordinator:
    """Central interface for all memory operations"""

    def __init__(self, memory_path: Path = Path("~/.ragged/memory")):
        self.interaction = InteractionMemory(memory_path / "interactions.db")
        self.semantic = SemanticMemory("semantic_memory")
        self.temporal = TemporalMemory(memory_path / "temporal")
        self.preferences = PreferencesStore(memory_path / "preferences.db")
        self.active_persona = "default"

    def record_interaction(
        self,
        query: str,
        response: str,
        retrieved_docs: list,
        model: str,
        latency: float
    ):
        """Record new interaction"""
        # Store in interaction memory
        self.interaction.record_interaction(
            persona=self.active_persona,
            query=query,
            response=response,
            retrieved_docs=retrieved_docs,
            model=model,
            latency=latency
        )

        # Extract topics and update temporal graph
        topics = self._extract_topics(query, response)
        for topic in topics:
            self.temporal.record_topic_activity(
                user=self.active_persona,
                topic=topic,
                intensity=1.0
            )

    def enhance_query(self, query: str) -> dict:
        """Enhance query with personal context"""
        # Get recent topics
        recent_topics = self.temporal.get_recent_topics(
            user=self.active_persona,
            since=datetime.now() - timedelta(weeks=1)
        )

        # Get similar past queries
        query_embedding = self.semantic.embedder.embed(query)
        similar = self.semantic.find_similar(query_embedding, n_results=3)

        # Get persona preferences
        persona = self.preferences.get_persona(self.active_persona)

        return {
            "original_query": query,
            "recent_topics": recent_topics,
            "similar_queries": similar,
            "persona": persona,
            "focus_areas": persona.focus_areas if persona else [],
        }

    def switch_persona(self, persona_name: str):
        """Switch active persona"""
        persona = self.preferences.get_persona(persona_name)
        if not persona:
            raise ValueError(f"Persona not found: {persona_name}")

        self.active_persona = persona_name

        # Update usage stats
        persona.last_used = datetime.now()
        persona.usage_count += 1
        self.preferences.save_persona(persona)

        return persona
```

---

## Configuration Reference

### Persona Configuration (YAML)

```yaml
# ~/.ragged/personas/researcher.yaml
name: researcher
description: Academic research assistant for literature review and analysis

# Response customization
response_style: academic       # academic, technical, conversational, concise
detail_level: comprehensive    # concise, balanced, comprehensive
citation_style: apa           # apa, mla, chicago, inline, none

# Model preferences
preferred_model_tier: quality  # fast, balanced, quality
task_model_overrides:
  reasoning: llama3.3:70b
  summarization: qwen2.5:32b
  code_generation: codellama:13b

# Memory configuration
memory_scope: persona_only     # persona_only, shared, custom
auto_enrich: true             # Automatically learn from interactions
track_reading_history: true
track_topics: true

# Active context
active_projects:
  - "RAG Evaluation Research"
  - "Personal Knowledge Management"

focus_areas:
  - research_methodology
  - academic_writing
  - machine_learning
  - rag_systems

# UI preferences
show_sources: true
show_confidence: true
show_reasoning: false

# Privacy
store_pii: redact            # store, redact, flag, reject
encrypt_memory: false
auto_archive_after_days: 730  # 2 years
```

### Global Preferences

```yaml
# ~/.ragged/config/preferences.yaml
language: en                   # Language for responses
timezone: America/New_York
date_format: "%Y-%m-%d"
time_format: "%H:%M:%S"

# Memory defaults
default_persona: researcher
memory_retention_days: 730     # Auto-archive after 2 years
enable_semantic_memory: true
enable_temporal_graph: true

# Privacy
pii_handling: redact          # Global PII policy
encrypt_at_rest: false
allow_memory_export: true

# Performance
embedding_batch_size: 100
semantic_index_rebuild_interval: 86400  # 24 hours
```

---

## Conclusion

The personal memory and persona system transforms ragged from a simple RAG tool into a true personal research assistant that:

- **Remembers** your work and preferences
- **Adapts** to your research style and needs
- **Switches contexts** seamlessly between different roles
- **Learns** from your interactions automatically
- **Respects privacy** with local-only, user-controlled memory

**Implementation Priority**: v0.3+ (after core RAG features are solid)

**Key Benefits**:
- More relevant responses (personalised retrieval)
- Better UX (remembers context across sessions)
- Increased productivity (no need to repeat context)
- Privacy-preserving (all local, no cloud)

**Next Steps**:
1. Implement basic interaction memory (v0.3)
2. Add persona system (v0.4)
3. Integrate temporal graph (v0.5)
4. Production-ready features (v1.0)

---

**Related Documentation**:
- [Document Normalisation](./document-normalisation.md)
- [Metadata Schema](./metadata-schema.md)
- [Privacy Architecture](./privacy-architecture.md)
- [Model Selection System](./model-selection.md)
