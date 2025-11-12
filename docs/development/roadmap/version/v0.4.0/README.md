# Ragged v0.4.0 Roadmap - Personal Memory & Knowledge Graphs

**Status:** Planned

**Total Hours:** 160-200 hours (AI implementation)

**Focus:** Personal memory system, knowledge graphs, personalisation

**Breaking Changes:** None - All features are additive and optional

**Implementation Note:** Due to size (160-200 hours), implement in 5-7 focused sessions of 25-35 hours each

## Overview

Version 0.4.0 introduces a **Personal Memory System** that transforms ragged from a document retrieval tool into an intelligent personal knowledge assistant. This release implements cutting-edge personalization techniques while maintaining ragged's privacy-first philosophy.

**Vision**: Ragged remembers what you care about, learns from your interactions, and provides increasingly personalized responses over time—all locally, with zero cloud dependencies.

**Key Capabilities**:
- **Persona Management**: Switch between work, research, personal contexts
- **Behavior Learning**: Automatically learn interests from query patterns
- **Temporal Memory**: Track what you worked on when
- **Personalized Ranking**: Boost relevant documents based on your interests
- **Knowledge Graphs**: Connect topics, documents, and concepts over time

**Research Foundation**: Based on state-of-the-art memory systems (Zep/Graphiti, Mem0, Letta) adapted for fully local operation.

---

## Part 1: Architecture Overview

### 1.1 Memory System Layers

```
┌──────────────────────────────────────────────────────────┐
│                   User Query                              │
└─────────────────────┬────────────────────────────────────┘
                      │
         ┌────────────▼──────────────┐
         │   Persona Context Layer   │
         │   - Active: researcher    │
         │   - Focus: ML, Privacy    │
         │   - Projects: RAG system  │
         └────────────┬──────────────┘
                      │
         ┌────────────▼──────────────┐
         │   Memory Enhancement      │
         │   - Recent topics         │
         │   - Related documents     │
         │   - Temporal context      │
         └────────────┬──────────────┘
                      │
         ┌────────────▼──────────────┐
         │   Hybrid Retrieval        │
         │   - Vector (semantic)     │
         │   - BM25 (keyword)        │
         │   - Memory (personalized) │
         └────────────┬──────────────┘
                      │
         ┌────────────▼──────────────┐
         │   Personalized Ranking    │
         │   - Interest boost        │
         │   - Recency boost         │
         │   - Project relevance     │
         └────────────┬──────────────┘
                      │
         ┌────────────▼──────────────┐
         │   Memory Update           │
         │   - Record interaction    │
         │   - Update knowledge graph│
         │   - Learn patterns        │
         └───────────────────────────┘
```

### 1.2 Storage Architecture

```
~/.ragged/
├── knowledge/                  # Document storage (existing)
│   ├── documents/
│   ├── embeddings/             # ChromaDB
│   └── bm25_index/
│
├── memory/                     # Personal memory (NEW)
│   ├── profiles/
│   │   ├── personas.yaml       # Persona definitions
│   │   ├── preferences.db      # SQLite: user preferences
│   │   └── user_profile.yaml   # Editable user information
│   │
│   ├── interactions/
│   │   ├── queries.db          # SQLite: query history
│   │   └── feedback.db         # User feedback signals
│   │
│   ├── semantic/
│   │   └── memory_vectors/     # ChromaDB: query embeddings
│   │
│   └── graph/                  # Temporal knowledge graph
│       └── kuzu_db/            # Kuzu embedded database
│
└── config/
    └── config.yml
```

### 1.3 Technology Stack

**New Dependencies**:
- **Kuzu** (v0.6+): Embedded graph database for personal memory
- **pydantic** (v2.0+): Already used, extended for memory schemas
- **python-dateutil** (v2.8+): Temporal operations
- **cryptography** (v41.0+): Optional encryption at rest

**Why Kuzu?**
- Embeddable (no separate service)
- Columnar storage (fast analytics)
- In-process (no network latency)
- Works in browser via WASM (future-proof)
- 1st-class Python integration
- Optimized for RAG use cases

**No external services**: All components run locally, privacy-guaranteed.

---

## Part 2: Implementation Milestones

### Milestone 1: Personal Memory Foundation (Weeks 1-2, 40 hours)

**Goal**: Basic persona system and interaction tracking

#### FEAT-101: Persona Manager

**Priority**: P0 - Foundation
**Time**: 8 hours

**Functionality**:
```python
# Users can define and switch between personas
ragged persona create researcher \
    --description "Academic researcher in ML" \
    --focus "machine learning, privacy, RAG" \
    --style "technical, detailed"

ragged persona create developer \
    --description "Software developer" \
    --focus "Python, systems design, APIs" \
    --style "practical, code-focused"

# Switch active persona
ragged persona switch researcher

# Query with specific persona
ragged query "What is retrieval-augmented generation?" --persona researcher
```

**Implementation**:
```python
# src/memory/persona.py (NEW FILE)
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class Persona(BaseModel):
    """User persona definition"""
    name: str
    description: str
    focus_areas: List[str]
    active_projects: List[str] = []
    response_style: str = "balanced"  # technical, balanced, simple
    detail_level: str = "balanced"    # brief, balanced, detailed
    citation_style: str = "inline"    # inline, footnote, none
    created_at: datetime
    last_used: Optional[datetime] = None
    usage_count: int = 0

class PersonaManager:
    """Manage user personas and context switching"""

    def __init__(self, profiles_path: Path):
        self.profiles_path = profiles_path
        self.profiles_path.mkdir(parents=True, exist_ok=True)
        self.active_persona = "default"
        self.personas = self._load_personas()

    def create_persona(
        self,
        name: str,
        description: str,
        focus_areas: List[str],
        **kwargs
    ) -> Persona:
        """Create new persona"""
        persona = Persona(
            name=name,
            description=description,
            focus_areas=focus_areas,
            created_at=datetime.now(),
            **kwargs
        )

        self.personas[name] = persona
        self._save_persona(persona)

        logger.info(f"Created persona: {name}")
        return persona

    def switch_persona(self, name: str) -> Persona:
        """Switch active persona"""
        if name not in self.personas:
            raise ValueError(f"Persona '{name}' not found")

        self.active_persona = name
        persona = self.personas[name]

        # Update usage statistics
        persona.last_used = datetime.now()
        persona.usage_count += 1
        self._save_persona(persona)

        logger.info(f"Switched to persona: {name}")
        return persona

    def get_context(self) -> dict:
        """Get current persona context for query enhancement"""
        persona = self.personas[self.active_persona]

        return {
            "name": persona.name,
            "description": persona.description,
            "focus_areas": persona.focus_areas,
            "active_projects": persona.active_projects,
            "response_style": persona.response_style,
            "detail_level": persona.detail_level
        }

    def _load_personas(self) -> dict:
        """Load all personas from disk"""
        personas = {}

        # Load default persona
        personas["default"] = Persona(
            name="default",
            description="General purpose assistant",
            focus_areas=[],
            created_at=datetime.now()
        )

        # Load custom personas
        for persona_file in self.profiles_path.glob("*.yaml"):
            with open(persona_file) as f:
                data = yaml.safe_load(f)
                persona = Persona(**data)
                personas[persona.name] = persona

        return personas

    def _save_persona(self, persona: Persona):
        """Save persona to disk"""
        persona_file = self.profiles_path / f"{persona.name}.yaml"
        with open(persona_file, 'w') as f:
            yaml.dump(persona.dict(), f)
```

**Testing**:
- [ ] Create persona with all fields
- [ ] Switch between personas
- [ ] Verify persona isolation
- [ ] Test persona persistence across restarts

**Files to Create**:
- `src/memory/persona.py` (~250 lines)
- `tests/memory/test_persona.py` (~150 lines)

---

#### FEAT-102: Interaction Tracking (SQLite)

**Priority**: P0 - Foundation
**Time**: 6 hours

**Database Schema**:
```sql
-- Interaction history
CREATE TABLE interactions (
    id TEXT PRIMARY KEY,
    persona TEXT NOT NULL,
    query TEXT NOT NULL,
    response TEXT,
    timestamp TIMESTAMP NOT NULL,
    retrieved_doc_ids TEXT,      -- JSON array
    model_used TEXT,
    latency_ms REAL,
    feedback TEXT,               -- 'positive', 'negative', null
    correction TEXT,             -- User correction if provided
    session_id TEXT,
    metadata TEXT                -- JSON for extensibility
);

CREATE INDEX idx_interactions_persona ON interactions(persona);
CREATE INDEX idx_interactions_timestamp ON interactions(timestamp);
CREATE INDEX idx_interactions_session ON interactions(session_id);

-- Preferences store
CREATE TABLE preferences (
    key TEXT NOT NULL,
    value TEXT NOT NULL,         -- JSON-encoded
    persona TEXT,                -- NULL for global preferences
    category TEXT NOT NULL,      -- 'profile', 'ui', 'privacy'
    updated_at TIMESTAMP NOT NULL,
    PRIMARY KEY (key, persona)
);
```

**Implementation**:
```python
# src/memory/interactions.py (NEW FILE)
import sqlite3
import json
from datetime import datetime
from typing import List, Optional
from dataclasses import dataclass

@dataclass
class Interaction:
    """Single user interaction"""
    id: str
    persona: str
    query: str
    response: str
    timestamp: datetime
    retrieved_doc_ids: List[str]
    model_used: str
    latency_ms: float
    feedback: Optional[str] = None
    correction: Optional[str] = None

class InteractionStore:
    """Store and retrieve interaction history"""

    def __init__(self, db_path: Path):
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self):
        """Initialize database schema"""
        with sqlite3.connect(self.db_path) as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS interactions (
                    id TEXT PRIMARY KEY,
                    persona TEXT NOT NULL,
                    query TEXT NOT NULL,
                    response TEXT,
                    timestamp TIMESTAMP NOT NULL,
                    retrieved_doc_ids TEXT,
                    model_used TEXT,
                    latency_ms REAL,
                    feedback TEXT,
                    correction TEXT,
                    session_id TEXT,
                    metadata TEXT
                );

                CREATE INDEX IF NOT EXISTS idx_interactions_persona
                    ON interactions(persona);
                CREATE INDEX IF NOT EXISTS idx_interactions_timestamp
                    ON interactions(timestamp);
            """)

    def record_interaction(
        self,
        persona: str,
        query: str,
        response: str,
        retrieved_doc_ids: List[str],
        model_used: str,
        latency_ms: float,
        session_id: str
    ) -> str:
        """Record a new interaction"""
        interaction_id = str(uuid.uuid4())

        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO interactions
                (id, persona, query, response, timestamp,
                 retrieved_doc_ids, model_used, latency_ms, session_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                interaction_id,
                persona,
                query,
                response,
                datetime.now(),
                json.dumps(retrieved_doc_ids),
                model_used,
                latency_ms,
                session_id
            ))

        return interaction_id

    def get_recent_interactions(
        self,
        persona: Optional[str] = None,
        limit: int = 10
    ) -> List[Interaction]:
        """Get recent interactions"""
        with sqlite3.connect(self.db_path) as conn:
            if persona:
                cursor = conn.execute("""
                    SELECT * FROM interactions
                    WHERE persona = ?
                    ORDER BY timestamp DESC
                    LIMIT ?
                """, (persona, limit))
            else:
                cursor = conn.execute("""
                    SELECT * FROM interactions
                    ORDER BY timestamp DESC
                    LIMIT ?
                """, (limit,))

            rows = cursor.fetchall()

        return [self._row_to_interaction(row) for row in rows]

    def add_feedback(
        self,
        interaction_id: str,
        feedback: str,
        correction: Optional[str] = None
    ):
        """Add user feedback to interaction"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                UPDATE interactions
                SET feedback = ?, correction = ?
                WHERE id = ?
            """, (feedback, correction, interaction_id))

    def _row_to_interaction(self, row) -> Interaction:
        """Convert database row to Interaction object"""
        return Interaction(
            id=row[0],
            persona=row[1],
            query=row[2],
            response=row[3],
            timestamp=datetime.fromisoformat(row[4]),
            retrieved_doc_ids=json.loads(row[5]) if row[5] else [],
            model_used=row[6],
            latency_ms=row[7],
            feedback=row[8],
            correction=row[9]
        )
```

**Testing**:
- [ ] Record interaction and retrieve
- [ ] Query by persona
- [ ] Add feedback to interaction
- [ ] Test concurrent access

**Files to Create**:
- `src/memory/interactions.py` (~200 lines)
- `tests/memory/test_interactions.py` (~150 lines)

---

#### FEAT-103: Knowledge Graph Foundation (Kuzu)

**Priority**: P0 - Foundation
**Time**: 6 hours

**Graph Schema**:
```cypher
// Node types
CREATE NODE TABLE User(
    name STRING,
    created_at TIMESTAMP,
    PRIMARY KEY(name)
);

CREATE NODE TABLE Topic(
    name STRING,
    category STRING,
    interest_level FLOAT,
    first_seen TIMESTAMP,
    last_seen TIMESTAMP,
    PRIMARY KEY(name)
);

CREATE NODE TABLE Document(
    doc_id STRING,
    title STRING,
    doc_type STRING,
    added_at TIMESTAMP,
    PRIMARY KEY(doc_id)
);

CREATE NODE TABLE Project(
    name STRING,
    description STRING,
    status STRING,
    started_at TIMESTAMP,
    PRIMARY KEY(name)
);

// Relationship types
CREATE REL TABLE INTERESTED_IN(
    FROM User TO Topic,
    frequency INT,
    last_query TIMESTAMP,
    confidence FLOAT
);

CREATE REL TABLE ACCESSED(
    FROM User TO Document,
    timestamp TIMESTAMP,
    duration_seconds INT,
    interaction_id STRING
);

CREATE REL TABLE WORKING_ON(
    FROM User TO Project,
    start_time TIMESTAMP,
    end_time TIMESTAMP,
    intensity FLOAT
);

CREATE REL TABLE RELATED_TO(
    FROM Topic TO Topic,
    strength FLOAT,
    co_occurrence_count INT,
    last_seen TIMESTAMP
);
```

**Implementation**:
```python
# src/memory/graph.py (NEW FILE)
import kuzu

class MemoryGraph:
    """Knowledge graph for personal memory"""

    def __init__(self, db_path: Path):
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        self.db = kuzu.Database(str(db_path))
        self.conn = kuzu.Connection(self.db)

        self._init_schema()

    def _init_schema(self):
        """Initialize graph schema"""
        # Check if schema exists
        result = self.conn.execute("CALL show_tables()").get_as_df()

        if result.empty:
            # Create schema
            self.conn.execute("""
                CREATE NODE TABLE User(
                    name STRING,
                    created_at TIMESTAMP,
                    PRIMARY KEY(name)
                )
            """)

            self.conn.execute("""
                CREATE NODE TABLE Topic(
                    name STRING,
                    category STRING,
                    interest_level FLOAT,
                    first_seen TIMESTAMP,
                    last_seen TIMESTAMP,
                    PRIMARY KEY(name)
                )
            """)

            self.conn.execute("""
                CREATE NODE TABLE Document(
                    doc_id STRING,
                    title STRING,
                    doc_type STRING,
                    added_at TIMESTAMP,
                    PRIMARY KEY(doc_id)
                )
            """)

            self.conn.execute("""
                CREATE REL TABLE INTERESTED_IN(
                    FROM User TO Topic,
                    frequency INT,
                    last_query TIMESTAMP,
                    confidence FLOAT
                )
            """)

            self.conn.execute("""
                CREATE REL TABLE ACCESSED(
                    FROM User TO Document,
                    timestamp TIMESTAMP,
                    duration_seconds INT,
                    interaction_id STRING
                )
            """)

            logger.info("Initialized memory graph schema")

    def record_query_topics(
        self,
        user: str,
        topics: List[str],
        timestamp: datetime
    ):
        """Record topics from a query"""
        # Ensure user exists
        self.conn.execute("""
            MERGE (u:User {name: $user})
            ON CREATE SET u.created_at = $now
        """, {"user": user, "now": timestamp})

        # Record each topic
        for topic in topics:
            self.conn.execute("""
                MERGE (t:Topic {name: $topic})
                ON CREATE SET
                    t.category = 'inferred',
                    t.interest_level = 0.5,
                    t.first_seen = $now,
                    t.last_seen = $now
                ON MATCH SET
                    t.last_seen = $now

                MATCH (u:User {name: $user})
                MERGE (u)-[i:INTERESTED_IN]->(t)
                ON CREATE SET
                    i.frequency = 1,
                    i.last_query = $now,
                    i.confidence = 0.5
                ON MATCH SET
                    i.frequency = i.frequency + 1,
                    i.last_query = $now,
                    i.confidence = least(1.0, i.confidence + 0.05)
            """, {
                "user": user,
                "topic": topic,
                "now": timestamp
            })

    def get_top_topics(
        self,
        user: str,
        limit: int = 10
    ) -> List[dict]:
        """Get user's top topics by interest"""
        result = self.conn.execute("""
            MATCH (u:User {name: $user})-[i:INTERESTED_IN]->(t:Topic)
            RETURN t.name, i.frequency, i.confidence, t.last_seen
            ORDER BY i.frequency DESC, i.confidence DESC
            LIMIT $limit
        """, {"user": user, "limit": limit})

        return [
            {
                "topic": row[0],
                "frequency": row[1],
                "confidence": row[2],
                "last_seen": row[3]
            }
            for row in result.get_as_df().itertuples(index=False)
        ]
```

**Testing**:
- [ ] Initialize database
- [ ] Record topics
- [ ] Query top topics
- [ ] Test concurrent access

**Files to Create**:
- `src/memory/graph.py` (~300 lines)
- `tests/memory/test_graph.py` (~200 lines)

---

#### FEAT-104: CLI Commands - Memory Management

**Priority**: P1 - User Interface
**Time**: 8 hours

**Commands**:
```bash
# Persona management
ragged persona list
ragged persona create <name> --description "..." --focus "topics"
ragged persona switch <name>
ragged persona delete <name> --confirm

# Memory viewing
ragged memory list --limit 10 --persona researcher
ragged memory topics --persona researcher
ragged memory timeline --since "-30d"
ragged memory show <interaction-id>

# Memory management
ragged memory delete <interaction-id> --confirm
ragged memory export <output-file> --persona researcher
ragged memory clear --persona researcher --confirm

# Preferences
ragged memory set <key> <value> --persona researcher
ragged memory get <key> --persona researcher
```

**Testing**:
- [ ] All CLI commands work
- [ ] Pretty table output
- [ ] Error handling
- [ ] Confirmation prompts

**Files to Create**:
- Update `src/main.py` with new command groups
- `tests/test_memory_cli.py` (~200 lines)

---

### Milestone 2: Behavior Learning (Weeks 3-4, 60 hours)

**Goal**: Automatic interest profiling and personalized ranking

#### FEAT-105: Topic Extraction

**Priority**: P0 - Core Feature
**Time**: 4 hours

**Approach**: Simple keyword extraction (Phase 1), later enhance with NLP

**Implementation**:
```python
# src/memory/topics.py (NEW FILE)
from collections import Counter
import re
from typing import List

class TopicExtractor:
    """Extract topics from queries"""

    def __init__(self):
        self.stopwords = {
            "the", "a", "an", "in", "on", "at", "for", "to",
            "of", "is", "are", "was", "were", "what", "how",
            "why", "when", "where", "which", "who"
        }

    def extract_topics(
        self,
        text: str,
        max_topics: int = 5
    ) -> List[str]:
        """
        Extract topics from text.

        Phase 1: Simple keyword extraction
        Future: Enhance with spaCy NER or local LLM
        """
        # Lowercase and tokenize
        words = re.findall(r'\b[a-z]{4,}\b', text.lower())

        # Remove stopwords
        keywords = [w for w in words if w not in self.stopwords]

        # Count frequency
        counter = Counter(keywords)

        # Return top keywords as topics
        return [word for word, count in counter.most_common(max_topics)]
```

**Enhancement Path** (v0.5+):
- Use spaCy for NER (entities as topics)
- Use local LLM for semantic topic extraction
- User-defined topic taxonomies

---

#### FEAT-106: Behavior Learner

**Priority**: P0 - Core Feature
**Time**: 12 hours

**Functionality**:
- Track which topics user queries about
- Track which documents user accesses
- Build interest profile
- Detect co-occurring topics

**Implementation**:
```python
# src/memory/behavior.py (NEW FILE)
class BehaviorLearner:
    """Learn from user behavior patterns"""

    def __init__(
        self,
        graph: MemoryGraph,
        interactions: InteractionStore
    ):
        self.graph = graph
        self.interactions = interactions

    def record_interaction(
        self,
        user: str,
        query: str,
        retrieved_docs: List[str],
        time_spent: int,
        feedback: Optional[str] = None
    ) -> str:
        """Record complete interaction for learning"""

        # Extract topics
        topics = TopicExtractor().extract_topics(query)

        # Record in graph
        self.graph.record_query_topics(
            user=user,
            topics=topics,
            timestamp=datetime.now()
        )

        # Record document access
        for doc_id in retrieved_docs:
            self.graph.conn.execute("""
                MATCH (u:User {name: $user})
                MERGE (d:Document {doc_id: $doc_id})
                CREATE (u)-[:ACCESSED {
                    timestamp: $now,
                    duration_seconds: $duration,
                    interaction_id: $interaction_id
                }]->(d)
            """, {
                "user": user,
                "doc_id": doc_id,
                "now": datetime.now(),
                "duration": time_spent,
                "interaction_id": uuid.uuid4()
            })

        # Store in SQLite
        interaction_id = self.interactions.record_interaction(
            persona=user,
            query=query,
            response="",  # Filled separately
            retrieved_doc_ids=retrieved_docs,
            model_used="",
            latency_ms=time_spent,
            session_id=str(uuid.uuid4())
        )

        return interaction_id

    def build_interest_profile(
        self,
        user: str
    ) -> dict:
        """Build comprehensive interest profile"""

        # Get top topics
        topics = self.graph.get_top_topics(user, limit=20)

        # Get frequently accessed documents
        docs = self.graph.conn.execute("""
            MATCH (u:User {name: $user})-[a:ACCESSED]->(d:Document)
            RETURN d.doc_id, d.title, count(a) as access_count,
                   avg(a.duration_seconds) as avg_duration,
                   max(a.timestamp) as last_access
            ORDER BY access_count DESC
            LIMIT 20
        """, {"user": user}).get_as_df()

        # Detect topic co-occurrences
        # (Topics queried together frequently)

        return {
            "top_topics": topics,
            "frequent_documents": docs.to_dict('records'),
            "topic_clusters": []  # Future: detect clusters
        }
```

**Testing**:
- [ ] Record interaction
- [ ] Build interest profile
- [ ] Verify graph updates
- [ ] Test temporal aspects

**Files to Create**:
- `src/memory/behavior.py` (~350 lines)
- `tests/memory/test_behavior.py` (~200 lines)

---

#### FEAT-107: Personalized Ranking

**Priority**: P0 - Core Feature
**Time**: 10 hours

**Algorithm**:
1. Get user's interest profile
2. Boost documents related to user's focus topics
3. Boost documents user has accessed before (familiarity)
4. Apply time decay (recent interests weighted more)

**Implementation**:
```python
# src/memory/personalization.py (NEW FILE)
class PersonalizedRanker:
    """Re-rank retrieval results using personal context"""

    def __init__(self, behavior_learner: BehaviorLearner):
        self.learner = behavior_learner

    def rerank(
        self,
        results: List[RetrievedChunk],
        user: str,
        weights: dict = None
    ) -> List[RetrievedChunk]:
        """
        Rerank results based on user interests.

        Args:
            results: Initial retrieval results
            user: User persona name
            weights: Boost weights (topic, familiarity, recency)

        Returns:
            Reranked results
        """
        if not results:
            return results

        # Default weights
        weights = weights or {
            "topic": 0.3,        # Topic interest boost
            "familiarity": 0.1,  # Document familiarity boost
            "recency": 0.1       # Recent topic boost
        }

        # Get user profile
        profile = self.learner.build_interest_profile(user)

        # Create topic interest map
        topic_scores = {
            t["topic"]: t["confidence"]
            for t in profile["top_topics"]
        }

        # Create document familiarity map
        doc_scores = {
            d["doc_id"]: d["access_count"]
            for d in profile["frequent_documents"]
        }
        max_accesses = max(doc_scores.values()) if doc_scores else 1

        # Rerank each result
        for result in results:
            base_score = result.score

            # Topic boost
            doc_topics = result.metadata.get("topics", [])
            topic_boost = sum(
                topic_scores.get(t, 0) * weights["topic"]
                for t in doc_topics
            )

            # Familiarity boost
            familiarity_boost = (
                doc_scores.get(result.document_id, 0) / max_accesses
                * weights["familiarity"]
            )

            # Apply boosts multiplicatively
            result.score = base_score * (1 + topic_boost + familiarity_boost)

        # Sort by new scores
        return sorted(results, key=lambda x: x.score, reverse=True)
```

**Testing**:
- [ ] Personalization improves relevance (manual verification)
- [ ] Boosts apply correctly
- [ ] Edge cases (no profile, empty results)

**Files to Create**:
- `src/memory/personalization.py` (~200 lines)
- `tests/memory/test_personalization.py` (~150 lines)

---

#### FEAT-108: Integration with RAG Pipeline

**Priority**: P0 - Core Integration
**Time**: 8 hours

**Enhanced Pipeline**:
```python
# src/rag_pipeline.py (MODIFY)
class EnhancedRAGPipeline:
    """RAG pipeline with personal memory"""

    def __init__(
        self,
        retriever: HybridRetriever,
        memory_system: PersonalMemorySystem,
        llm_client: OllamaClient
    ):
        self.retriever = retriever
        self.memory = memory_system
        self.llm = llm_client

    def query(
        self,
        query_text: str,
        persona: str = "default",
        k: int = 5,
        use_memory: bool = True
    ) -> dict:
        """Query with memory enhancement"""

        start = time.time()

        # 1. Switch persona
        self.memory.persona_mgr.switch_persona(persona)

        # 2. Enhance query with personal context
        if use_memory:
            context = self.memory.get_context()
            # Could augment query here if desired

        # 3. Retrieve (get more for reranking)
        raw_results = self.retriever.retrieve(
            query_text,
            top_k=k * 2
        )

        # 4. Personalized reranking
        if use_memory:
            ranked = self.memory.personalized_ranker.rerank(
                raw_results,
                user=persona
            )[:k]
        else:
            ranked = raw_results[:k]

        # 5. Generate response
        response = self._generate(query_text, ranked, context)

        # 6. Record interaction
        latency = time.time() - start

        self.memory.behavior_learner.record_interaction(
            user=persona,
            query=query_text,
            retrieved_docs=[r.document_id for r in ranked],
            time_spent=int(latency * 1000)
        )

        return {
            "query": query_text,
            "response": response,
            "sources": ranked,
            "persona": persona,
            "latency_ms": latency * 1000
        }
```

**Testing**:
- [ ] End-to-end query with memory
- [ ] Memory updates correctly
- [ ] Performance acceptable (<3s)

**Files to Modify**:
- `src/main.py` (integrate memory)
- `src/web/api.py` (add persona support)

---

### Milestone 3: Temporal Memory (Weeks 5-6, 60 hours)

**Goal**: Track information over time, support temporal queries

#### FEAT-109: Temporal Fact Storage

**Priority**: P1 - Advanced Feature
**Time**: 8 hours

Support facts that change over time:
- "I work at Company X" (current)
- "I used to work at Company Y" (historical)
- "I'm learning Rust" (current)
- "I learned Python in 2020" (historical)

**Implementation**: See comprehensive analysis section 2.5

---

#### FEAT-110: Timeline Queries

**Priority**: P1 - Advanced Feature
**Time**: 12 hours

Support queries like:
- "What was I working on last week?"
- "When did I first query about RAG?"
- "Show my activity for January"

**Implementation**:
```python
# src/memory/temporal.py (NEW FILE)
class TemporalQueryEngine:
    """Handle time-based queries"""

    def get_timeline(
        self,
        user: str,
        since: str = "-30d",
        until: str = None
    ) -> dict:
        """Get activity timeline"""

        # Parse time expressions
        start_time = self._parse_time(since)
        end_time = self._parse_time(until) if until else datetime.now()

        # Query graph for activities in time range
        activities = self.graph.conn.execute("""
            MATCH (u:User {name: $user})-[i:INTERESTED_IN]->(t:Topic)
            WHERE i.last_query >= $start AND i.last_query <= $end
            RETURN t.name, i.last_query, i.frequency
            ORDER BY i.last_query DESC
        """, {
            "user": user,
            "start": start_time,
            "end": end_time
        })

        # Group by date
        timeline = {}
        for row in activities.get_as_df().itertuples():
            date_key = row.last_query.date()
            if date_key not in timeline:
                timeline[date_key] = []

            timeline[date_key].append({
                "type": "query",
                "topic": row.name,
                "frequency": row.frequency
            })

        return timeline
```

---

## Part 3: Success Criteria & Metrics

### 3.1 Quantitative Metrics

**Performance**:
- Query latency: <2s (including memory enhancement)
- Graph query: <300ms
- Memory update: <100ms (async)

**Quality**:
- Personalization improvement: +15% relevance (user feedback)
- Topic extraction accuracy: 80% (vs manual labeling)
- Interest profile accuracy: 85% (user confirms top interests)

### 3.2 Qualitative Metrics

**User Satisfaction**:
- "Memory helps find documents": 85% agree
- "Personas useful": 80% use at least 2 personas
- "Privacy confident": 100% (guaranteed local)

### 3.3 Acceptance Criteria

v0.4.0 is successful if:
1. ✅ Persona system works seamlessly
2. ✅ Memory tracking is transparent
3. ✅ Personalization improves relevance (measurable)
4. ✅ All interactions stored locally
5. ✅ Users can view/edit/delete memory
6. ✅ Performance targets met

---

## Part 4: Testing Strategy

### 4.1 Unit Tests

- Persona management (create, switch, delete)
- Interaction recording
- Graph operations (CRUD)
- Topic extraction
- Personalized ranking algorithm

### 4.2 Integration Tests

- Full query flow with memory
- Persona isolation (no leakage)
- Graph + SQLite consistency
- Timeline accuracy

### 4.3 Privacy Tests

- No network calls (monitor all connections)
- Data stays local (verify file locations)
- Persona isolation (attempt cross-persona access)

---

## Part 5: Migration & Compatibility

### 5.1 Backward Compatibility

**No breaking changes**:
- Memory features are optional
- Default persona works like v0.3
- Can disable memory: `ragged query "..." --no-memory`

### 5.2 Data Migration

**First run**:
- Auto-create default persona
- Initialize empty memory database
- Migrate existing preferences (if any)

---

## Part 6: Documentation

### 6.1 User Guide

**Topics**:
- Getting started with personas
- Understanding memory tracking
- Viewing your memory
- Privacy guarantees
- Advanced: Temporal queries

### 6.2 API Documentation

- Python API for memory system
- CLI command reference
- Graph query examples
- Integration guide

---

## Summary

v0.4.0 represents a major evolution for ragged:
- From **document retrieval** to **personal knowledge assistant**
- From **stateless** to **memory-aware**
- From **generic** to **personalized**

All while maintaining ragged's core values:
- **Privacy-first**: 100% local, zero cloud dependencies
- **Transparent**: Users see and control their memory
- **Open**: Extensible architecture, open source

**Total Implementation**: 160-200 hours over 6-8 weeks

**Next Version** (v0.5):
- Enhanced NLP for topic extraction
- Document-level knowledge graphs (optional)
- Advanced temporal reasoning
- Memory analytics dashboard

---

**Appendix**: See comprehensive analysis document for detailed technical specifications, research references, and implementation examples.
