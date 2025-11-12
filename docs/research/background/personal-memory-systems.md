# State-of-the-Art Personal Memory and Context Systems for AI Applications (2025)

**Research Report**
**Date:** November 2025
**Focus:** Personal Memory Frameworks, User Profiling, Context Management, and Privacy-First Local Deployment

---

## Executive Summary

The field of personal memory and context management for AI applications has matured significantly in 2025, with three major architectural paradigms emerging:

1. **Virtual Context Management (MemGPT/Letta)**: Inspired by operating system memory hierarchies, treating context windows like limited RAM and using external storage
2. **Graph-Based Memory (Mem0, Zep)**: Leveraging knowledge graphs to capture relationships and temporal evolution of facts
3. **Hybrid RAG + Memory**: Combining document retrieval with personalised user context

### Key State-of-the-Art Findings

- **Zep** currently leads in benchmark performance (94.8% on DMR, 18.5% improvement on LongMemEval with 90% latency reduction)
- **Mem0** offers the best balance of performance and ease-of-use (26% accuracy boost over OpenAI, 91% faster, 90% token reduction)
- **Letta** provides the most sophisticated self-editing memory architecture with strong theoretical foundations
- **LangGraph** has become the standard for production memory persistence in 2025

### Benchmark Landscape

- **LoCoMo**: 300-turn conversations averaging 9K tokens across 35 sessions - tests very long-term memory
- **DMR (Deep Memory Retrieval)**: Primary MemGPT/Letta benchmark, but limited by short conversations (60 messages)
- **LongMemEval**: Most challenging benchmark with 500 questions across 115k-1.5M tokens, testing 5 core abilities

### Critical Insight for Privacy-First Systems

All leading systems can run locally with open-source components, making them viable for privacy-first deployments:
- SQLite + vector extensions (sqlite-vec, SQLite-Vector)
- Local embedding models (Ollama, sentence-transformers)
- Local LLMs (Ollama, llama.cpp)
- Self-hosted graph databases (Neo4j, FalkorDB, Kuzu)

---

## 1. Personal Memory Frameworks

### 1.1 MemGPT/Letta - Virtual Context Management

**Overview:**
Letta (formerly MemGPT) implements an "LLM Operating System" approach inspired by hierarchical memory systems in traditional operating systems. The core innovation is treating the LLM's limited context window like RAM, with explicit paging between in-context and out-of-context memory.

**Technical Architecture:**

```
┌─────────────────────────────────────┐
│        LLM Context Window           │
│  ┌──────────────────────────────┐  │
│  │   In-Context Memory Blocks   │  │
│  │   - persona (editable)       │  │
│  │   - human (editable)         │  │
│  │   - additional custom blocks │  │
│  └──────────────────────────────┘  │
│              ↕                      │
│    Memory Management Tools          │
│  - memory_replace()                 │
│  - memory_insert()                  │
│  - memory_rethink()                 │
└─────────────────────────────────────┘
              ↕
┌─────────────────────────────────────┐
│    Out-of-Context Memory            │
│  ┌──────────────────────────────┐  │
│  │   Archival Memory (Vector)   │  │
│  │   - Long-term facts          │  │
│  │   - External data            │  │
│  └──────────────────────────────┘  │
│  ┌──────────────────────────────┐  │
│  │   Recall Memory (History)    │  │
│  │   - Conversation history     │  │
│  │   - Timestamped events       │  │
│  └──────────────────────────────┘  │
└─────────────────────────────────────┘
```

**Key Features:**

1. **Memory Blocks**: Persistent, labeled containers for knowledge
   - In-context blocks are part of every LLM call
   - Self-editable via dedicated tools
   - Shared across agents via block IDs

2. **Three-Tier Memory Hierarchy**:
   - Core Memory (in-context, always available)
   - Archival Memory (vector store, searchable)
   - Recall Memory (conversation history)

3. **Sleep-Time Agents**: Background agents handle memory editing separately from main reasoning loop

**Code Example (Python):**

```python
from letta import Letta

client = Letta(token="LETTA_API_KEY")

# Create agent with custom memory blocks
agent_state = client.agents.create(
    model="openai/gpt-4-turbo",
    embedding="openai/text-embedding-3-small",
    memory_blocks=[
        {
            "label": "human",
            "value": "User is a researcher working on privacy-first AI. "
                    "Interested in local deployment, SQLite, and RAG systems. "
                    "Prefers Python and TypeScript."
        },
        {
            "label": "persona",
            "value": "I am a technical assistant specialising in AI architecture. "
                    "I provide detailed, code-focused responses with security considerations."
        },
        {
            "label": "project_context",
            "value": "Working on 'ragged' - a privacy-first local RAG system. "
                    "Current focus: implementing personal memory layer."
        }
    ],
    tools=["web_search", "run_code"]
)

# Send message - agent can edit its own memory
response = client.agents.send_message(
    agent_id=agent_state.id,
    message="What database should I use for the memory layer?"
)

# Agent might use memory_replace to update project_context
# based on conversation
```

**TypeScript Example:**

```typescript
import { LettaClient } from '@letta-ai/letta-client'

const client = new LettaClient({ token: process.env.LETTA_API_KEY });

const agentState = await client.agents.create({
    model: "openai/gpt-4-turbo",
    embedding: "openai/text-embedding-3-small",
    memoryBlocks: [
        {
            label: "human",
            value: "User preferences and context..."
        },
        {
            label: "persona",
            value: "AI assistant personality..."
        }
    ],
    tools: ["web_search"]
});
```

**Performance:**
- DMR Benchmark: 93.4% accuracy (gpt-4-turbo)
- LoCoMo Benchmark: 74.0% with gpt-4o-mini

**Strengths:**
- Strong theoretical foundation (published paper)
- Self-editing memory provides autonomy
- Multi-agent shared memory enables organizational knowledge
- Agent File (.af) format for full state export/import
- Active development with DeepLearning.AI course support

**Weaknesses:**
- More complex to implement than simple RAG
- Requires careful prompt engineering for memory tools
- Limited relationship modeling (compared to graph approaches)
- DMR benchmark shows it's not SOTA anymore

**Privacy Considerations for Ragged:**
- Fully self-hostable with local LLMs (Ollama)
- Vector store can be local (ChromaDB, SQLite)
- No cloud dependencies required
- Agent state is exportable/importable
- Complete audit trail of memory edits

---

### 1.2 Mem0 - Personalised AI Memory Layer

**Overview:**
Mem0 (pronounced "mem-zero") provides a universal memory layer that sits between your application and LLM, automatically extracting and managing personalised context across conversations. The enhanced version uses graph memory to capture complex relationships.

**Technical Architecture:**

```
User Input → Mem0 → [Search Memory] → Augmented Context → LLM → Response
                           ↓
                    [Extract & Update]
                           ↓
                  ┌─────────────────┐
                  │  Hybrid Storage │
                  ├─────────────────┤
                  │ Vector Store    │ ← Semantic similarity
                  │ Graph Store     │ ← Relationships
                  │ Key-Value Store │ ← Metadata
                  └─────────────────┘
```

**Two-Phase Pipeline:**

1. **Extraction Phase**: Process new messages + historical context → Create new memories
2. **Update Phase**: Evaluate extracted memories vs. existing → Apply operations (add/update/delete)

**Graph Memory Enhancement:**
- Entities as nodes (people, places, projects, concepts)
- Relationships as edges (KNOWS, WORKS_ON, PREFERS, etc.)
- Temporal tracking of relationship changes
- 2% improvement over base configuration

**Code Example (Python):**

```python
from mem0 import Memory

# Initialize with configuration
config = {
    "vector_store": {
        "provider": "qdrant",
        "config": {
            "url": "http://localhost:6333",  # Local Qdrant
            "collection_name": "ragged_memory"
        }
    },
    "llm": {
        "provider": "ollama",
        "config": {
            "model": "llama3.1:8b",
            "base_url": "http://localhost:11434"
        }
    },
    "embedder": {
        "provider": "ollama",
        "config": {
            "model": "nomic-embed-text"
        }
    }
}

memory = Memory.from_config(config)

# Basic usage pattern
def chat_with_memory(message: str, user_id: str):
    # 1. Search for relevant memories
    relevant_memories = memory.search(
        query=message,
        user_id=user_id,
        limit=3
    )

    # 2. Augment LLM context
    context = "\n".join([m["memory"] for m in relevant_memories])
    messages = [
        {"role": "system", "content": f"Relevant context: {context}"},
        {"role": "user", "content": message}
    ]

    # 3. Generate response
    response = llm_client.create(messages=messages)

    # 4. Store interaction for learning
    memory.add(
        messages=[
            {"role": "user", "content": message},
            {"role": "assistant", "content": response}
        ],
        user_id=user_id
    )

    return response

# Advanced: Graph memory configuration
graph_config = {
    "graph_store": {
        "provider": "neo4j",
        "config": {
            "url": "bolt://localhost:7687",
            "username": "neo4j",
            "password": "password"
        }
    },
    "version": "v1.1"  # Enable graph memory
}
```

**Installation:**
```bash
# Base installation
pip install mem0ai

# With graph support
pip install "mem0ai[graph]"
```

**Supported Graph Stores:**
- Neo4j
- Memgraph
- AWS Neptune Analytics
- AWS Neptune DB Cluster
- Kuzu

**Performance Metrics (2025):**
- 26% relative accuracy improvement over OpenAI memory
- 91% lower p95 latency vs. full-context approaches
- 90% token cost reduction
- LoCoMo benchmark: 66.9% vs OpenAI's 52.9%

**API Growth:**
- Q1 2025: 35 million API calls
- Q3 2025: 186 million API calls (30% monthly growth)

**Strengths:**
- Easiest to integrate - minimal code changes
- Best performance/cost trade-off
- Automatic memory extraction (no manual tools)
- Multi-level memory (user/session/agent)
- Strong TypeScript/JavaScript support
- Graph memory for relationship modeling
- $24M Series A funding indicates strong support

**Weaknesses:**
- Less transparent than Letta's explicit memory tools
- Graph memory is newer, less proven
- Primarily designed for cloud (but supports local)
- Less control over memory structure

**Privacy Considerations for Ragged:**
- Can run fully locally with Ollama + local vector DB
- Graph store can be self-hosted (Neo4j, Kuzu)
- No cloud API calls required with proper config
- Memory data is in standard databases (exportable)
- May need custom extraction prompts for privacy-sensitive data

---

### 1.3 Zep - Temporal Knowledge Graph Memory

**Overview:**
Zep is the current state-of-the-art in agent memory (as of January 2025), using temporal knowledge graphs powered by its core component "Graphiti". Unlike other systems, Zep maintains explicit temporal understanding of how information evolves over time.

**Technical Architecture:**

```
┌──────────────────────────────────────────┐
│           Graphiti Engine                │
├──────────────────────────────────────────┤
│  Bi-Temporal Knowledge Graph             │
│  ┌────────────────────────────────────┐  │
│  │ Entity (Node)                      │  │
│  │ - valid_at: timestamp              │  │
│  │ - invalid_at: timestamp            │  │
│  │ - ingestion_time: timestamp        │  │
│  └────────────────────────────────────┘  │
│            ↓ (edges) ↓                   │
│  ┌────────────────────────────────────┐  │
│  │ Relationship (Edge)                │  │
│  │ - valid_at: timestamp              │  │
│  │ - invalid_at: timestamp            │  │
│  │ - fact: string                     │  │
│  └────────────────────────────────────┘  │
└──────────────────────────────────────────┘
              ↓
    Hybrid Retrieval Strategy
    ┌────────────────────────┐
    │ Semantic (Embeddings)  │
    │ Keyword (BM25)         │
    │ Graph Traversal        │
    └────────────────────────┘
         ↓ (sub-second)
    Retrieved Context
```

**Key Innovations:**

1. **Bi-Temporal Model**: Tracks both event time and ingestion time
   - Event time: When something actually happened
   - Ingestion time: When the system learned about it
   - Enables accurate point-in-time queries

2. **Temporal Edge Invalidation**:
   - Contradictions handled through time-based invalidation
   - No LLM summarization needed (unlike GraphRAG)
   - Preserves historical state

3. **Episodic Data Structure**:
   - Information flows as discrete "episodes"
   - Each episode timestamped
   - Enables incremental updates without full rebuilds

4. **Hybrid Retrieval**:
   - Semantic similarity (embeddings)
   - Keyword search (BM25)
   - Graph traversal
   - P95 latency: 300ms (no LLM calls during retrieval)

**Code Example (Python):**

```python
from graphiti_core import Graphiti
from graphiti_core.driver.neo4j_driver import Neo4jDriver

# Initialize with local Neo4j
driver = Neo4jDriver(
    uri="bolt://localhost:7687",
    user="neo4j",
    password="password",
    database="ragged_memory"
)

graphiti = Graphiti(graph_driver=driver)

# Add episodic information
await graphiti.add_episode(
    name="research_session_001",
    episode_body="""
    User is researching personal memory systems for AI.
    Particular interest in privacy-first, local-only deployment.
    Currently comparing Letta, Mem0, and Zep.
    Prefers SQLite and vector databases.
    Working on project called 'ragged'.
    """,
    reference_time=datetime.now()
)

# Query with temporal context
results = await graphiti.search(
    query="What database preferences does the user have?",
    num_results=5
)

# Point-in-time query
historical_results = await graphiti.search(
    query="What was the user working on?",
    reference_time=datetime(2025, 11, 1)  # Query as-of specific date
)

# Custom entity definition (domain-specific)
from pydantic import BaseModel

class TechnicalPreference(BaseModel):
    category: str  # "database", "language", "framework"
    name: str
    confidence: float
    last_mentioned: datetime

# Graphiti can extract and track these custom entities
```

**Supported Graph Backends:**
- Neo4j (recommended for production)
- FalkorDB
- Amazon Neptune
- Kuzu (embedded, good for local deployment)

**Performance Benchmarks (2025):**
- DMR: 94.8% vs Letta's 93.4%
- LongMemEval: Up to 18.5% accuracy improvement, 90% latency reduction
- P95 latency: 300ms (vs. seconds for LLM-based approaches)

**Strengths:**
- State-of-the-art benchmark performance
- Explicit temporal reasoning (crucial for long-term memory)
- Fast retrieval without LLM calls
- Handles contradictions elegantly
- Real-time incremental updates
- Custom entity definitions
- MCP server implementation available

**Weaknesses:**
- Most complex to implement
- Requires graph database expertise
- Newer (less community resources than Letta/Mem0)
- Defaults to OpenAI (but supports Anthropic, Groq)

**Privacy Considerations for Ragged:**
- Open source (github.com/getzep/graphiti)
- Can use local graph databases (Kuzu is embedded)
- Supports local LLMs (Anthropic, Groq, custom)
- Full control over data storage
- Temporal audit trail built-in
- No cloud dependencies required

**Installation:**
```bash
pip install graphiti-core

# With Docker for quick start
docker-compose up  # Starts Neo4j and related services
```

---

### 1.4 LangChain/LangGraph - Production Memory Persistence

**Overview:**
LangGraph has become the standard framework for production agent memory in 2025. The legacy LangChain memory modules (ConversationBufferMemory, etc.) have been deprecated in favor of LangGraph's checkpointing system, which provides superior persistence and multi-threading support.

**Technical Architecture:**

```
┌─────────────────────────────────────────┐
│         LangGraph Agent                 │
│  ┌───────────────────────────────────┐  │
│  │    Thread-Scoped State            │  │
│  │    (Short-term Memory)            │  │
│  └───────────────────────────────────┘  │
│               ↓                         │
│         Checkpointer                    │
│  - Saves state at every super-step     │
│  - Enables time travel                 │
│  - Fault tolerance                     │
└─────────────────────────────────────────┘
              ↓
┌─────────────────────────────────────────┐
│      Checkpoint Storage                 │
│  - InMemorySaver (development)         │
│  - SqliteSaver (local workflows)       │
│  - PostgresSaver (production)          │
│  - MongoDBSaver (cross-thread memory)  │
└─────────────────────────────────────────┘
```

**Memory Types:**

1. **Short-Term Memory (Thread-Scoped)**:
   - Persisted via checkpointers
   - Conversation state within a session
   - Automatically saved at each step

2. **Long-Term Memory (Cross-Thread)**:
   - MongoDB Store integration (new in 2025)
   - JSON document storage
   - Flexible namespacing for users/orgs
   - Cross-conversation persistence

**Code Example (Python):**

```python
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.checkpoint.mongodb import MongoDBSaver
from typing import TypedDict, Annotated
import operator

# Define state structure
class State(TypedDict):
    messages: Annotated[list, operator.add]
    user_preferences: dict
    session_context: dict

# Create graph
graph = StateGraph(State)

# Add nodes (agent logic)
graph.add_node("agent", agent_node)
graph.add_node("tools", tool_node)

# Add edges
graph.add_edge("agent", "tools")
graph.add_edge("tools", "agent")
graph.set_entry_point("agent")

# Local SQLite checkpointer for short-term memory
checkpointer = SqliteSaver.from_conn_string("./ragged_checkpoints.db")

# Compile with persistence
app = graph.compile(checkpointer=checkpointer)

# Run with thread ID (automatic checkpointing)
result = app.invoke(
    {"messages": [{"role": "user", "content": "Hello"}]},
    {"configurable": {"thread_id": "user_123_session_001"}}
)

# Resume from checkpoint (fault tolerance)
result = app.invoke(
    {"messages": [{"role": "user", "content": "Continue"}]},
    {"configurable": {"thread_id": "user_123_session_001"}}
)

# Time travel - replay from specific checkpoint
from langgraph.pregel import Pregel

history = app.get_state_history(
    {"configurable": {"thread_id": "user_123_session_001"}}
)

for state in history:
    print(f"Step: {state.step}, State: {state.values}")
```

**Long-Term Memory with MongoDB:**

```python
from langgraph.store.mongodb import MongoDBStore

# Cross-thread persistent memory
store = MongoDBStore(
    client=mongo_client,
    db_name="ragged_memory"
)

# Store user preferences (persists across sessions)
store.put(
    namespace=["users", "user_123", "preferences"],
    key="technical_interests",
    value={
        "languages": ["Python", "TypeScript"],
        "databases": ["SQLite", "PostgreSQL"],
        "focus_areas": ["privacy", "local-deployment", "RAG"],
        "last_updated": "2025-11-09"
    }
)

# Retrieve in any session
prefs = store.get(
    namespace=["users", "user_123", "preferences"],
    key="technical_interests"
)

# Search across memories
results = store.search(
    namespace=["users", "user_123"],
    query="What databases does this user prefer?"
)
```

**Available Checkpointers (2025):**

| Checkpointer | Use Case | Storage | Status |
|-------------|----------|---------|--------|
| InMemorySaver | Development/testing | RAM | Stable |
| SqliteSaver | Local workflows | SQLite file | Stable |
| PostgresSaver | Production | PostgreSQL | Stable |
| MongoDBSaver | Long-term memory | MongoDB | New 2025 |

**Key Features:**

1. **Time Travel**: Replay any previous state
2. **Fault Tolerance**: Resume from last successful step
3. **Multi-Threading**: Separate state per conversation
4. **State Forking**: Explore alternative paths
5. **Human-in-the-Loop**: Pause for human input

**Strengths:**
- Production-ready (used by LangSmith)
- Well-documented and supported
- Multiple storage backends
- Time travel debugging
- Fault tolerance built-in
- Active development (MongoDB integration is new)

**Weaknesses:**
- Less sophisticated memory than Letta/Zep
- Manual memory structure design
- No automatic fact extraction
- Requires careful state schema design

**Privacy Considerations for Ragged:**
- SQLite checkpointer perfect for local deployment
- MongoDB can be self-hosted
- Full state control
- No cloud dependencies
- GDPR-compliant deletion (drop thread/namespace)

---

## 2. User Profiling and Personas

### 2.1 User Profile Modeling

**State-of-the-Art Approach (2025):**

Modern systems combine **implicit** and **explicit** signals to build dynamic user profiles:

**Explicit Signals:**
- Demographic information (age, occupation, location)
- Stated preferences and settings
- Direct feedback on outputs
- User-provided context

**Implicit Signals:**
- Behavioural patterns (search history, interaction frequency)
- Writing style and tone preferences
- Tool usage patterns
- Time-of-day preferences
- Response quality indicators (accepted/rejected outputs)

**Architecture Pattern:**

```python
# Modern user profile structure
class UserProfile:
    # Explicit attributes
    demographics: dict[str, str]
    stated_preferences: dict[str, Any]

    # Implicit learned attributes
    behavior_patterns: dict[str, float]
    interests: list[tuple[str, float]]  # (topic, confidence)
    interaction_style: dict[str, Any]

    # Temporal tracking
    created_at: datetime
    last_updated: datetime
    profile_version: int

    # Privacy controls
    data_retention_days: int
    exportable: bool
    deletable: bool

# Automatic enrichment from interaction
def enrich_profile_from_interaction(
    profile: UserProfile,
    interaction: Interaction
) -> UserProfile:
    # Extract entities and topics
    entities = extract_entities(interaction.content)
    topics = classify_topics(interaction.content)

    # Update interests with decay
    for topic, relevance in topics:
        if topic in profile.interests:
            # Exponential moving average
            old_score = profile.interests[topic]
            profile.interests[topic] = 0.7 * old_score + 0.3 * relevance
        else:
            profile.interests[topic] = relevance

    # Track behavioural patterns
    profile.behavior_patterns["session_length"].append(
        interaction.duration
    )
    profile.behavior_patterns["avg_query_length"].append(
        len(interaction.query.split())
    )

    # Update timestamp
    profile.last_updated = datetime.now()
    profile.profile_version += 1

    return profile
```

**Research Findings (2025):**

From "Enabling Personalised Long-term Interactions in LLM-based Agents":
- User profiles should be **implicitly generated** and **continuously refined**
- Include: demographics, preferences, interests, personality traits
- Dynamic profiles outperform static personas by 30% engagement
- ML-powered personas show 25% better conversion rates

**Implementation Example with Letta:**

```python
# Letta-based profile management
profile_memory_block = {
    "label": "user_profile",
    "value": """
    Demographics:
    - Occupation: Software Engineer
    - Location: San Francisco
    - Experience: 10 years in AI/ML

    Interests (confidence scores):
    - Privacy-preserving AI (0.95)
    - Local LLM deployment (0.90)
    - RAG systems (0.88)
    - Vector databases (0.85)

    Behavioural Patterns:
    - Prefers detailed technical explanations
    - Asks follow-up questions about implementation
    - Values code examples with comments
    - Active during 9am-5pm PST

    Current Focus:
    - Building privacy-first RAG system
    - Evaluating memory architectures
    - Researching local deployment options
    """
}
```

### 2.2 Persona Switching and Management

**The Persona Pattern (2025):**

Modern AI systems support multiple personas that can be switched dynamically or composed together for complex tasks.

**Approaches:**

1. **Predefined Personas** (Static):
   - Consistent behaviour across sessions
   - Suitable for recurring tasks
   - Example: "Technical Expert", "Creative Writer", "Code Reviewer"

2. **Dynamic Personas** (Runtime):
   - Created on-the-fly for unique tasks
   - Tailored to specific contexts
   - Example: Domain-specific expert for current query

3. **Multi-Persona Teams** (Agentic):
   - Multiple personas collaborate
   - Each has specialised role
   - Example: Product Manager + Architect + Implementer

**Implementation Pattern:**

```python
# Persona management system
class Persona:
    id: str
    name: str
    role: str
    expertise: list[str]
    communication_style: dict
    memory_namespace: str  # Separate memory per persona

class PersonaManager:
    def __init__(self, memory_store):
        self.personas: dict[str, Persona] = {}
        self.active_persona: str = None
        self.memory_store = memory_store

    def switch_persona(self, persona_id: str):
        """Switch to different persona"""
        if persona_id not in self.personas:
            raise ValueError(f"Unknown persona: {persona_id}")

        # Save current persona's context
        if self.active_persona:
            self.memory_store.save_context(
                namespace=["personas", self.active_persona],
                context=self.get_current_context()
            )

        # Load new persona's context
        self.active_persona = persona_id
        context = self.memory_store.load_context(
            namespace=["personas", persona_id]
        )
        return context

    def create_persona_team(self, task: str) -> list[Persona]:
        """Create multi-persona team for complex task"""
        # Analyse task requirements
        required_expertise = analyze_task_requirements(task)

        # Compose team
        team = []
        if "architecture" in required_expertise:
            team.append(self.personas["architect"])
        if "implementation" in required_expertise:
            team.append(self.personas["developer"])
        if "review" in required_expertise:
            team.append(self.personas["reviewer"])

        return team

# Usage example
manager = PersonaManager(memory_store)

# Define personas
manager.add_persona(Persona(
    id="privacy_expert",
    name="Privacy & Security Specialist",
    role="Advise on privacy-preserving implementations",
    expertise=["GDPR", "data minimization", "local-first"],
    communication_style={"formality": "high", "detail": "thorough"}
))

manager.add_persona(Persona(
    id="performance_optimizer",
    name="Performance Engineer",
    role="Optimise for speed and efficiency",
    expertise=["caching", "indexing", "profiling"],
    communication_style={"formality": "medium", "detail": "focused"}
))

# Switch based on query type
query = "How do I ensure user data is never sent to cloud?"
if "privacy" in query or "data" in query:
    manager.switch_persona("privacy_expert")
elif "performance" in query or "slow" in query:
    manager.switch_persona("performance_optimizer")
```

**Real-World Application:**

Legal AI startup **August** launched Personas in 2025:
- Remembers lawyer-specific formatting and style preferences
- Tracks recurring facts per lawyer
- 25% improvement in output accuracy
- 50% reduction in follow-up questions
- Memory layer purpose-built for legal work

**Multi-Agent Persona Example with LangGraph:**

```python
from langgraph.graph import StateGraph

class TeamState(TypedDict):
    task: str
    proposals: list[str]
    final_solution: str

# Product Manager persona
def pm_persona(state: TeamState):
    return {
        "proposals": state["proposals"] + [
            "From PM: Focus on user needs and UX"
        ]
    }

# Architect persona
def architect_persona(state: TeamState):
    return {
        "proposals": state["proposals"] + [
            "From Architect: Use microservices with event sourcing"
        ]
    }

# Build persona team
team = StateGraph(TeamState)
team.add_node("pm", pm_persona)
team.add_node("architect", architect_persona)
team.add_node("implementer", implementer_persona)

# Each persona contributes to solution
team.add_edge("pm", "architect")
team.add_edge("architect", "implementer")
```

### 2.3 Automatic Persona Enrichment

**Learning from Usage Patterns:**

Modern systems automatically enrich personas based on observed interactions:

```python
class PersonaEnrichment:
    def __init__(self, llm, vector_store):
        self.llm = llm
        self.vector_store = vector_store

    async def enrich_from_interactions(
        self,
        persona_id: str,
        interactions: list[Interaction]
    ):
        # Extract patterns
        patterns = await self.analyze_patterns(interactions)

        # Generate enrichment
        enrichment_prompt = f"""
        Based on these interaction patterns:
        {json.dumps(patterns, indent=2)}

        Update the persona profile to include:
        1. Discovered preferences
        2. Communication style patterns
        3. Subject matter expertise
        4. Common workflows
        """

        enrichments = await self.llm.generate(enrichment_prompt)

        # Store as structured data
        await self.vector_store.upsert(
            namespace=["personas", persona_id, "enrichments"],
            data=enrichments
        )

        return enrichments

    async def analyze_patterns(self, interactions):
        return {
            "query_complexity": self.measure_complexity(interactions),
            "topic_distribution": self.extract_topics(interactions),
            "response_preferences": self.analyze_feedback(interactions),
            "temporal_patterns": self.find_temporal_patterns(interactions)
        }
```

**Privacy-Preserving Enrichment:**

For local-only systems like ragged:

```python
# Differential privacy for pattern learning
from typing import List
import numpy as np

class PrivatePatternLearner:
    def __init__(self, epsilon: float = 1.0):
        self.epsilon = epsilon  # Privacy budget

    def learn_topic_distribution(
        self,
        interactions: List[Interaction],
        add_noise: bool = True
    ) -> dict[str, float]:
        # Count topic frequencies
        topic_counts = {}
        for interaction in interactions:
            for topic in interaction.topics:
                topic_counts[topic] = topic_counts.get(topic, 0) + 1

        if add_noise:
            # Add Laplace noise for differential privacy
            sensitivity = 1.0  # One interaction changes count by at most 1
            scale = sensitivity / self.epsilon

            for topic in topic_counts:
                noise = np.random.laplace(0, scale)
                topic_counts[topic] += noise

        # Normalise to probabilities
        total = sum(topic_counts.values())
        return {
            topic: count / total
            for topic, count in topic_counts.items()
        }
```

---

## 3. Context Management

### 3.1 Reading/Search History Tracking

**Modern Approach:**

Track what users read and search to provide better context:

```python
class HistoryTracker:
    def __init__(self, storage):
        self.storage = storage

    async def track_document_access(
        self,
        user_id: str,
        document_id: str,
        chunks_viewed: list[str],
        time_spent: float,
        interaction_type: str  # "read", "search", "reference"
    ):
        event = {
            "user_id": user_id,
            "document_id": document_id,
            "chunks_viewed": chunks_viewed,
            "time_spent": time_spent,
            "interaction_type": interaction_type,
            "timestamp": datetime.now().isoformat(),
            "context": self.get_session_context()
        }

        # Store in temporal database
        await self.storage.insert(
            collection="reading_history",
            document=event
        )

        # Update document importance score
        await self.update_document_relevance(
            user_id, document_id, time_spent
        )

    async def get_recent_context(
        self,
        user_id: str,
        hours: int = 24
    ) -> str:
        cutoff = datetime.now() - timedelta(hours=hours)

        history = await self.storage.query(
            collection="reading_history",
            filter={
                "user_id": user_id,
                "timestamp": {"$gte": cutoff.isoformat()}
            },
            sort=[("timestamp", -1)]
        )

        # Summarize recent activity
        summary = f"Recent activity ({hours}h):\n"
        for event in history:
            summary += f"- {event['interaction_type']} {event['document_id']} "
            summary += f"for {event['time_spent']:.1f}s\n"

        return summary
```

**Integration with RAG:**

```python
class ContextAwareRAG:
    def __init__(self, retriever, history_tracker):
        self.retriever = retriever
        self.history = history_tracker

    async def retrieve_with_history(
        self,
        query: str,
        user_id: str
    ):
        # Get user's reading history
        recent_docs = await self.history.get_recently_accessed(
            user_id, hours=24
        )

        # Boost relevance of recently-viewed documents
        results = await self.retriever.search(
            query=query,
            filters={
                "boost_docs": recent_docs,  # Increase ranking
                "user_id": user_id
            }
        )

        # Filter out just-read content (avoid repetition)
        very_recent = await self.history.get_recently_accessed(
            user_id, hours=1
        )
        results = [r for r in results if r.id not in very_recent]

        return results
```

### 3.2 Temporal Context ("What was I working on last week?")

**Temporal Knowledge Graph Approach (Zep/Graphiti):**

```python
# Query historical work context
async def get_weekly_context(
    graphiti: Graphiti,
    user_id: str,
    week_offset: int = 0  # 0=this week, 1=last week, etc.
):
    # Calculate time range
    today = datetime.now()
    week_start = today - timedelta(
        days=today.weekday() + (7 * week_offset)
    )
    week_end = week_start + timedelta(days=7)

    # Query with temporal filter
    context = await graphiti.search(
        query="What was the user working on?",
        filters={
            "user_id": user_id,
            "valid_at": {
                "$gte": week_start,
                "$lt": week_end
            }
        },
        reference_time=week_start  # Point-in-time query
    )

    # Group by project/topic
    projects = {}
    for item in context:
        project = item.get("project", "unspecified")
        if project not in projects:
            projects[project] = []
        projects[project].append(item)

    return {
        "week": week_start.strftime("%Y-W%W"),
        "projects": projects,
        "summary": generate_weekly_summary(projects)
    }
```

**LangGraph Checkpoint Approach:**

```python
# Time-travel through conversation history
from langgraph.checkpoint.sqlite import SqliteSaver

checkpointer = SqliteSaver.from_conn_string("./memory.db")

# Get state from last week
target_time = datetime.now() - timedelta(days=7)

history = app.get_state_history(
    config={"configurable": {"thread_id": "user_123"}}
)

# Find checkpoint closest to target time
for state in history:
    if state.timestamp <= target_time:
        print(f"Last week you were working on:")
        print(state.values.get("project_context"))
        break
```

### 3.3 Cross-Document Insight Tracking

**Contextual Memory Intelligence (CMI) Framework:**

Recent research (May 2025) introduced concepts for tracking insights across documents:

- **Contextual Entropy**: Measure of information disorder/uncertainty
- **Insight Drift**: How insights evolve over time
- **Resonance Intelligence**: Cross-modal alignment of insights
- **Memory Lineage**: Tracking provenance of insights

**Implementation Pattern:**

```python
class InsightTracker:
    def __init__(self, graph_store, vector_store):
        self.graph = graph_store
        self.vectors = vector_store

    async def track_insight(
        self,
        insight: str,
        source_docs: list[str],
        user_id: str,
        session_id: str
    ):
        # Generate embedding
        embedding = await self.get_embedding(insight)

        # Find related insights (cross-document)
        related = await self.vectors.search(
            vector=embedding,
            filter={"user_id": user_id},
            limit=5
        )

        # Create insight node in graph
        insight_id = await self.graph.create_node(
            type="insight",
            properties={
                "text": insight,
                "user_id": user_id,
                "session_id": session_id,
                "created_at": datetime.now(),
                "confidence": 0.8
            }
        )

        # Link to source documents
        for doc_id in source_docs:
            await self.graph.create_edge(
                from_node=insight_id,
                to_node=doc_id,
                type="DERIVED_FROM",
                properties={"timestamp": datetime.now()}
            )

        # Link to related insights
        for related_insight in related:
            similarity = related_insight.score
            if similarity > 0.7:
                await self.graph.create_edge(
                    from_node=insight_id,
                    to_node=related_insight.id,
                    type="RELATED_TO",
                    properties={"similarity": similarity}
                )

        return insight_id

    async def get_insight_lineage(self, insight_id: str):
        """Trace where an insight came from"""
        # Graph traversal
        query = """
        MATCH path = (i:Insight {id: $insight_id})-[:DERIVED_FROM*1..]->(doc:Document)
        RETURN path
        """
        return await self.graph.query(query, {"insight_id": insight_id})

    async def detect_insight_drift(
        self,
        topic: str,
        user_id: str,
        time_window_days: int = 30
    ):
        """Track how insights on a topic evolved"""
        cutoff = datetime.now() - timedelta(days=time_window_days)

        # Get insights chronologically
        insights = await self.graph.query("""
            MATCH (i:Insight)
            WHERE i.user_id = $user_id
              AND i.text CONTAINS $topic
              AND i.created_at >= $cutoff
            RETURN i
            ORDER BY i.created_at ASC
        """, {
            "user_id": user_id,
            "topic": topic,
            "cutoff": cutoff
        })

        # Measure drift (embedding distance over time)
        drifts = []
        for i in range(1, len(insights)):
            prev_emb = insights[i-1].embedding
            curr_emb = insights[i].embedding
            distance = cosine_distance(prev_emb, curr_emb)
            drifts.append({
                "time": insights[i].created_at,
                "drift": distance,
                "text": insights[i].text
            })

        return drifts
```

### 3.4 Project/Research Area Context

**Namespace-Based Organisation:**

```python
# Organise memory by project
class ProjectContextManager:
    def __init__(self, memory_store):
        self.store = memory_store

    async def create_project(self, user_id: str, project_name: str):
        namespace = ["users", user_id, "projects", project_name]

        # Initialize project metadata
        await self.store.put(
            namespace=namespace,
            key="metadata",
            value={
                "name": project_name,
                "created_at": datetime.now(),
                "status": "active",
                "tags": [],
                "related_projects": []
            }
        )

        return namespace

    async def add_to_project(
        self,
        namespace: list[str],
        item_type: str,  # "document", "insight", "query", etc.
        item: dict
    ):
        await self.store.put(
            namespace=namespace + [item_type + "s"],
            key=item["id"],
            value=item
        )

    async def get_project_context(self, namespace: list[str]) -> str:
        # Retrieve all project items
        documents = await self.store.search(
            namespace=namespace + ["documents"]
        )
        insights = await self.store.search(
            namespace=namespace + ["insights"]
        )
        queries = await self.store.search(
            namespace=namespace + ["queries"]
        )

        # Generate context summary
        return f"""
        Project Context:
        - {len(documents)} documents accessed
        - {len(insights)} insights generated
        - {len(queries)} queries made

        Recent activity:
        {self.summarize_recent(queries[-5:])}

        Key insights:
        {self.summarize_insights(insights)}
        """

    async def switch_project(
        self,
        user_id: str,
        from_project: str,
        to_project: str
    ):
        # Save current project state
        from_ns = ["users", user_id, "projects", from_project]
        await self.store.put(
            namespace=from_ns,
            key="last_active",
            value=datetime.now()
        )

        # Load new project context
        to_ns = ["users", user_id, "projects", to_project]
        context = await self.get_project_context(to_ns)

        return context
```

### 3.5 Interaction Pattern Learning

**Behavioural Pattern Extraction:**

```python
class InteractionPatternLearner:
    def __init__(self, storage):
        self.storage = storage

    async def learn_patterns(self, user_id: str):
        # Get interaction history
        interactions = await self.storage.get_user_interactions(
            user_id,
            limit=1000
        )

        patterns = {
            "temporal": self.analyze_temporal_patterns(interactions),
            "query_style": self.analyze_query_patterns(interactions),
            "response_preferences": self.analyze_response_patterns(interactions),
            "tool_usage": self.analyze_tool_patterns(interactions)
        }

        return patterns

    def analyze_temporal_patterns(self, interactions):
        # When is user most active?
        hours = [i.timestamp.hour for i in interactions]
        days = [i.timestamp.weekday() for i in interactions]

        return {
            "peak_hours": self.find_peaks(hours),
            "active_days": self.find_peaks(days),
            "session_length_avg": np.mean([i.duration for i in interactions])
        }

    def analyze_query_patterns(self, interactions):
        queries = [i.query for i in interactions]

        return {
            "avg_length": np.mean([len(q.split()) for q in queries]),
            "complexity": self.measure_query_complexity(queries),
            "common_topics": self.extract_common_topics(queries),
            "question_types": self.classify_question_types(queries)
        }

    def analyze_response_patterns(self, interactions):
        # What kind of responses does user prefer?
        feedback = [i.feedback for i in interactions if i.feedback]

        liked = [i for i in feedback if i.sentiment > 0.5]
        disliked = [i for i in feedback if i.sentiment < 0.5]

        return {
            "preferred_length": np.mean([len(i.response) for i in liked]),
            "preferred_style": self.extract_style_features(liked),
            "format_preferences": {
                "code_examples": sum(1 for i in liked if "```" in i.response) / len(liked),
                "bullet_points": sum(1 for i in liked if "\n- " in i.response) / len(liked),
                "detailed_explanations": sum(1 for i in liked if len(i.response) > 500) / len(liked)
            }
        }

# Use patterns to personalise responses
class PatternAwareResponseGenerator:
    def __init__(self, pattern_learner):
        self.patterns = pattern_learner

    async def generate(self, query: str, user_id: str):
        patterns = await self.patterns.learn_patterns(user_id)

        # Adapt system prompt based on patterns
        system_prompt = self.create_personalized_prompt(patterns)

        # Example adaptations:
        if patterns["response_preferences"]["format_preferences"]["code_examples"] > 0.7:
            system_prompt += "\nAlways include code examples when relevant."

        if patterns["query_style"]["complexity"] > 0.8:
            system_prompt += "\nProvide detailed technical explanations."

        return await llm.generate(
            system=system_prompt,
            user=query
        )
```

---

## 4. Storage Architecture

### 4.1 Separating Personal Memory from Documents

**Recommended Architecture for Ragged:**

```
┌─────────────────────────────────────────────────────┐
│                  Document Store                     │
│  (Primary knowledge base - immutable content)       │
│                                                      │
│  SQLite database: documents.db                      │
│  ┌─────────────┐  ┌──────────────┐                 │
│  │  Documents  │  │    Chunks     │                 │
│  │  - id       │  │    - id       │                 │
│  │  - path     │  │    - doc_id   │                 │
│  │  - content  │  │    - content  │                 │
│  │  - metadata │  │    - embedding│                 │
│  └─────────────┘  └──────────────┘                 │
└─────────────────────────────────────────────────────┘
                         ↕
          Retrieval queries (read-only)
                         ↕
┌─────────────────────────────────────────────────────┐
│               Personal Memory Store                 │
│  (User context - mutable, privacy-controlled)       │
│                                                      │
│  SQLite database: memory.db                         │
│  ┌──────────────────────────────────────────────┐  │
│  │  User Profiles                                │  │
│  │  - user_id, preferences, demographics         │  │
│  ├──────────────────────────────────────────────┤  │
│  │  Interaction History                          │  │
│  │  - query, response, timestamp, feedback       │  │
│  ├──────────────────────────────────────────────┤  │
│  │  Extracted Facts (Vector + Graph)            │  │
│  │  - fact, entities, relationships, confidence  │  │
│  ├──────────────────────────────────────────────┤  │
│  │  Reading History                              │  │
│  │  - doc_id, chunks_viewed, time_spent         │  │
│  ├──────────────────────────────────────────────┤  │
│  │  Project Contexts                             │  │
│  │  - project_id, metadata, active_status       │  │
│  ├──────────────────────────────────────────────┤  │
│  │  Insights                                     │  │
│  │  - insight, source_docs, lineage, timestamp  │  │
│  └──────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────┘
```

**Why Separate?**

1. **Privacy**: Personal data is isolated, easier to delete/export
2. **Lifecycle**: Documents are long-lived, memory evolves
3. **Performance**: Different access patterns and indexes
4. **Portability**: Memory can be moved between document collections

**Implementation:**

```python
# Separate storage managers
class DocumentStore:
    """Immutable knowledge base"""
    def __init__(self, db_path: str):
        self.db = sqlite3.connect(db_path)
        self.vector_index = self.load_vector_index()

    def search(self, query: str, top_k: int = 5):
        """Search documents only"""
        embedding = self.get_embedding(query)
        return self.vector_index.search(embedding, top_k)

    def get_document(self, doc_id: str):
        """Retrieve full document"""
        return self.db.execute(
            "SELECT * FROM documents WHERE id = ?",
            (doc_id,)
        ).fetchone()

class MemoryStore:
    """Mutable personal context"""
    def __init__(self, db_path: str):
        self.db = sqlite3.connect(db_path)
        self.graph = self.init_graph_store()

    def add_interaction(self, user_id: str, interaction: dict):
        """Record interaction"""
        self.db.execute("""
            INSERT INTO interactions
            (user_id, query, response, timestamp, feedback)
            VALUES (?, ?, ?, ?, ?)
        """, (
            user_id,
            interaction["query"],
            interaction["response"],
            datetime.now(),
            interaction.get("feedback")
        ))
        self.db.commit()

    def extract_facts(self, user_id: str, interaction: dict):
        """Extract personal facts from interaction"""
        facts = llm_extract_facts(interaction)
        for fact in facts:
            self.add_fact(user_id, fact)

    def get_user_context(self, user_id: str) -> str:
        """Retrieve personalised context"""
        profile = self.get_profile(user_id)
        recent = self.get_recent_interactions(user_id, limit=10)
        facts = self.get_relevant_facts(user_id)

        return f"""
        User Profile: {profile}
        Recent Activity: {recent}
        Known Facts: {facts}
        """

# Combined RAG with personal memory
class PersonalizedRAG:
    def __init__(self, doc_store: DocumentStore, memory_store: MemoryStore):
        self.docs = doc_store
        self.memory = memory_store

    async def query(self, user_id: str, query: str):
        # 1. Get personal context
        user_context = self.memory.get_user_context(user_id)

        # 2. Enhance query with personal context
        enhanced_query = self.rewrite_query(query, user_context)

        # 3. Search documents
        doc_results = self.docs.search(enhanced_query)

        # 4. Filter/rank based on user history
        reading_history = self.memory.get_reading_history(user_id)
        ranked_results = self.personalize_ranking(
            doc_results,
            reading_history
        )

        # 5. Generate response
        response = await llm.generate(
            system=f"User context: {user_context}",
            context=ranked_results,
            query=query
        )

        # 6. Record interaction and learn
        interaction = {
            "query": query,
            "response": response,
            "docs_used": [r.id for r in ranked_results]
        }
        self.memory.add_interaction(user_id, interaction)
        self.memory.extract_facts(user_id, interaction)

        return response
```

### 4.2 Privacy Levels and Access Control

**Multi-Level Privacy Model:**

```python
from enum import Enum

class PrivacyLevel(Enum):
    PUBLIC = 0      # Shareable with anyone
    SHARED = 1      # Shareable within organisation
    PRIVATE = 2     # User-only
    SENSITIVE = 3   # Encrypted, minimal retention

class MemoryItem:
    id: str
    user_id: str
    content: str
    privacy_level: PrivacyLevel
    encrypted: bool
    retention_days: int | None  # None = keep forever
    created_at: datetime
    expires_at: datetime | None

class PrivacyControlledMemory:
    def __init__(self, encryption_key: bytes):
        self.key = encryption_key

    def store(self, item: MemoryItem):
        # Encrypt if sensitive
        content = item.content
        if item.privacy_level == PrivacyLevel.SENSITIVE:
            content = self.encrypt(content, self.key)
            item.encrypted = True

        # Set expiration
        if item.retention_days:
            item.expires_at = (
                datetime.now() + timedelta(days=item.retention_days)
            )

        # Store with access controls
        self.db.execute("""
            INSERT INTO memory_items
            (id, user_id, content, privacy_level, encrypted, expires_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            item.id,
            item.user_id,
            content,
            item.privacy_level.value,
            item.encrypted,
            item.expires_at
        ))

    def retrieve(
        self,
        item_id: str,
        requesting_user_id: str,
        requester_role: str = "user"
    ) -> MemoryItem | None:
        item = self.db.execute(
            "SELECT * FROM memory_items WHERE id = ?",
            (item_id,)
        ).fetchone()

        if not item:
            return None

        # Check access permissions
        if item.privacy_level == PrivacyLevel.PRIVATE:
            if item.user_id != requesting_user_id:
                raise PermissionError("Access denied")

        # Decrypt if needed
        if item.encrypted:
            item.content = self.decrypt(item.content, self.key)

        return item

    def auto_expire(self):
        """Delete expired items"""
        self.db.execute("""
            DELETE FROM memory_items
            WHERE expires_at IS NOT NULL
              AND expires_at < ?
        """, (datetime.now(),))
        self.db.commit()
```

**Local Encryption for Sensitive Data:**

```python
from cryptography.fernet import Fernet

class LocalEncryption:
    def __init__(self, key_path: str = "~/.ragged/memory.key"):
        self.key_path = os.path.expanduser(key_path)
        self.key = self.load_or_create_key()
        self.fernet = Fernet(self.key)

    def load_or_create_key(self) -> bytes:
        if os.path.exists(self.key_path):
            with open(self.key_path, "rb") as f:
                return f.read()
        else:
            key = Fernet.generate_key()
            os.makedirs(os.path.dirname(self.key_path), exist_ok=True)
            with open(self.key_path, "wb") as f:
                f.write(key)
            os.chmod(self.key_path, 0o600)  # User-only permissions
            return key

    def encrypt(self, data: str) -> bytes:
        return self.fernet.encrypt(data.encode())

    def decrypt(self, encrypted: bytes) -> str:
        return self.fernet.decrypt(encrypted).decode()
```

### 4.3 Export/Delete Capabilities (GDPR Compliance)

**Full Export Functionality:**

```python
class MemoryExporter:
    def __init__(self, memory_store):
        self.store = memory_store

    def export_all(self, user_id: str, format: str = "json") -> bytes:
        """Export all user data"""
        data = {
            "export_date": datetime.now().isoformat(),
            "user_id": user_id,
            "profile": self.export_profile(user_id),
            "interactions": self.export_interactions(user_id),
            "facts": self.export_facts(user_id),
            "insights": self.export_insights(user_id),
            "reading_history": self.export_reading_history(user_id),
            "projects": self.export_projects(user_id)
        }

        if format == "json":
            return json.dumps(data, indent=2).encode()
        elif format == "jsonl":
            return "\n".join(
                json.dumps(item) for item in data.values()
            ).encode()
        else:
            raise ValueError(f"Unsupported format: {format}")

    def export_profile(self, user_id: str):
        return self.store.db.execute(
            "SELECT * FROM user_profiles WHERE user_id = ?",
            (user_id,)
        ).fetchone()

    def export_interactions(self, user_id: str):
        return self.store.db.execute(
            "SELECT * FROM interactions WHERE user_id = ? ORDER BY timestamp",
            (user_id,)
        ).fetchall()

    # ... similar methods for other data types

class MemoryDeleter:
    def __init__(self, memory_store):
        self.store = memory_store

    def delete_all(self, user_id: str, confirm: str):
        """Permanently delete all user data"""
        if confirm != f"DELETE {user_id}":
            raise ValueError("Confirmation string doesn't match")

        # Delete from all tables
        tables = [
            "user_profiles",
            "interactions",
            "facts",
            "insights",
            "reading_history",
            "projects",
            "memory_items"
        ]

        for table in tables:
            self.store.db.execute(
                f"DELETE FROM {table} WHERE user_id = ?",
                (user_id,)
            )

        # Delete from graph store
        self.store.graph.query(
            "MATCH (n {user_id: $user_id}) DETACH DELETE n",
            {"user_id": user_id}
        )

        # Delete from vector store
        self.store.vector_index.delete(
            filter={"user_id": user_id}
        )

        self.store.db.commit()

        # Audit log
        self.log_deletion(user_id)

    def delete_before_date(self, user_id: str, cutoff: datetime):
        """Delete data older than cutoff date"""
        self.store.db.execute("""
            DELETE FROM interactions
            WHERE user_id = ? AND timestamp < ?
        """, (user_id, cutoff))

        # Similar for other tables with timestamps
        self.store.db.commit()
```

**CLI for Data Rights:**

```bash
# Export user data
ragged memory export --user-id user_123 --format json > user_data.json

# Delete specific time range
ragged memory delete --user-id user_123 --before 2025-01-01

# Complete deletion
ragged memory delete --user-id user_123 --all --confirm "DELETE user_123"

# List what data exists
ragged memory list --user-id user_123
```

### 4.4 Efficient Retrieval of Personal Context

**Hybrid Indexing Strategy:**

```python
class EfficientMemoryRetrieval:
    def __init__(self):
        # Multiple indexes for different access patterns
        self.vector_index = VectorIndex()  # Semantic search
        self.time_index = BTreeIndex()     # Temporal queries
        self.graph_index = GraphIndex()    # Relationship traversal
        self.cache = LRUCache(maxsize=1000)  # Hot data

    async def get_relevant_context(
        self,
        user_id: str,
        query: str,
        max_tokens: int = 2000
    ) -> str:
        # Check cache first
        cache_key = f"{user_id}:{hash(query)}"
        if cache_key in self.cache:
            return self.cache[cache_key]

        # Parallel retrieval from multiple indexes
        results = await asyncio.gather(
            self.vector_index.search(query, user_id=user_id, limit=5),
            self.time_index.get_recent(user_id=user_id, hours=24),
            self.graph_index.get_related_facts(query, user_id=user_id)
        )

        vector_results, recent_context, graph_facts = results

        # Combine and rank
        combined = self.merge_and_rank(
            vector_results,
            recent_context,
            graph_facts
        )

        # Truncate to token limit
        context = self.truncate_to_tokens(combined, max_tokens)

        # Cache result
        self.cache[cache_key] = context

        return context

    def merge_and_rank(self, *result_sets):
        # Reciprocal Rank Fusion
        scores = {}
        for rank, results in enumerate(result_sets):
            for i, item in enumerate(results):
                if item.id not in scores:
                    scores[item.id] = 0
                scores[item.id] += 1 / (60 + i)  # RRF formula

        # Sort by combined score
        ranked = sorted(
            scores.items(),
            key=lambda x: x[1],
            reverse=True
        )

        return [item_id for item_id, score in ranked]
```

**Semantic Caching for Memory:**

```python
class MemoryCache:
    def __init__(self, vector_db, threshold: float = 0.95):
        self.vector_db = vector_db
        self.threshold = threshold  # Similarity threshold for cache hit

    async def get_or_compute(
        self,
        query: str,
        user_id: str,
        compute_fn: callable
    ):
        # Generate query embedding
        query_embedding = await self.get_embedding(query)

        # Search for similar cached queries
        similar = await self.vector_db.search(
            vector=query_embedding,
            filter={"user_id": user_id, "type": "cached_context"},
            limit=1
        )

        # Cache hit if similarity above threshold
        if similar and similar[0].score >= self.threshold:
            print(f"Cache hit (similarity: {similar[0].score:.3f})")
            return similar[0].metadata["context"]

        # Cache miss - compute fresh
        print("Cache miss - computing fresh context")
        context = await compute_fn()

        # Store in cache
        await self.vector_db.upsert(
            id=f"cache_{user_id}_{hash(query)}",
            vector=query_embedding,
            metadata={
                "type": "cached_context",
                "user_id": user_id,
                "query": query,
                "context": context,
                "timestamp": datetime.now()
            }
        )

        return context
```

---

## 5. Integration with RAG

### 5.1 Personal Memory Enhances Retrieval

**Query Rewriting with Personal Context:**

```python
class PersonalizedQueryRewriter:
    def __init__(self, memory_store, llm):
        self.memory = memory_store
        self.llm = llm

    async def rewrite_query(self, query: str, user_id: str) -> list[str]:
        # Get user context
        profile = await self.memory.get_profile(user_id)
        recent_topics = await self.memory.get_recent_topics(user_id, hours=24)
        current_project = await self.memory.get_active_project(user_id)

        # Generate query variants
        prompt = f"""
        User profile: {profile.expertise_areas}
        Recent topics: {recent_topics}
        Current project: {current_project.name}

        Original query: {query}

        Generate 3 query variants that:
        1. Incorporate user's expertise level
        2. Consider recent research context
        3. Align with current project needs
        """

        variants = await self.llm.generate(prompt)

        return [query] + variants  # Original + enhanced variants

# Example usage
async def personalized_retrieval(query: str, user_id: str):
    # Rewrite query with personal context
    query_variants = await rewriter.rewrite_query(query, user_id)

    # Search with all variants
    results = []
    for q in query_variants:
        results.extend(await document_store.search(q, top_k=3))

    # Deduplicate and rank
    unique_results = deduplicate_by_id(results)
    ranked = rank_by_relevance(unique_results, user_id)

    return ranked
```

**Filtering Based on User Preferences:**

```python
class PersonalizedFilter:
    def __init__(self, memory_store):
        self.memory = memory_store

    async def apply_user_filters(
        self,
        results: list[Document],
        user_id: str
    ) -> list[Document]:
        # Get user preferences
        prefs = await self.memory.get_preferences(user_id)

        filtered = results

        # Filter by complexity level
        if "complexity_level" in prefs:
            filtered = [
                r for r in filtered
                if r.complexity <= prefs["complexity_level"]
            ]

        # Boost preferred sources
        if "preferred_sources" in prefs:
            for r in filtered:
                if r.source in prefs["preferred_sources"]:
                    r.score *= 1.5

        # Filter out recently viewed (avoid repetition)
        recent_docs = await self.memory.get_recently_viewed(
            user_id,
            hours=24
        )
        filtered = [r for r in filtered if r.id not in recent_docs]

        # Re-rank
        filtered.sort(key=lambda r: r.score, reverse=True)

        return filtered
```

### 5.2 Personalising LLM Interactions

**Dynamic System Prompts:**

```python
class PersonalizedPromptBuilder:
    def __init__(self, memory_store):
        self.memory = memory_store

    async def build_system_prompt(self, user_id: str) -> str:
        profile = await self.memory.get_profile(user_id)
        patterns = await self.memory.get_interaction_patterns(user_id)

        prompt = "You are a helpful AI assistant."

        # Adapt to expertise level
        if profile.expertise_level == "expert":
            prompt += "\nThe user is a technical expert. "
            prompt += "Provide detailed, advanced explanations. "
            prompt += "Use technical terminology freely."
        elif profile.expertise_level == "beginner":
            prompt += "\nThe user is learning. "
            prompt += "Explain concepts clearly with examples. "
            prompt += "Avoid jargon unless necessary."

        # Adapt to communication style
        if patterns.prefers_concise:
            prompt += "\nBe concise and to-the-point."
        else:
            prompt += "\nProvide thorough explanations."

        if patterns.prefers_code_examples:
            prompt += "\nInclude code examples when relevant."

        # Include current project context
        project = await self.memory.get_active_project(user_id)
        if project:
            prompt += f"\n\nCurrent project: {project.name}"
            prompt += f"\nProject context: {project.description}"

        # Include recent topics
        recent = await self.memory.get_recent_topics(user_id, hours=24)
        if recent:
            prompt += f"\n\nRecent topics: {', '.join(recent)}"

        return prompt

# Usage
async def generate_response(query: str, user_id: str):
    system_prompt = await prompt_builder.build_system_prompt(user_id)

    response = await llm.generate(
        system=system_prompt,
        user=query
    )

    return response
```

### 5.3 Context Injection Strategies

**Hierarchical Context Window Management:**

```python
class ContextWindowManager:
    def __init__(self, max_tokens: int = 8000):
        self.max_tokens = max_tokens

    def build_context(
        self,
        query: str,
        user_id: str,
        documents: list[Document],
        memory_context: str
    ) -> str:
        # Token budget allocation
        budget = {
            "system_prompt": 500,
            "user_profile": 300,
            "recent_context": 500,
            "retrieved_docs": 5000,
            "query": 200,
            "buffer": 500  # Safety margin
        }

        # Build context layers
        context_layers = [
            ("system", self.get_system_prompt(), budget["system_prompt"]),
            ("profile", self.get_user_profile(user_id), budget["user_profile"]),
            ("recent", memory_context, budget["recent_context"]),
            ("docs", self.format_documents(documents), budget["retrieved_docs"]),
            ("query", query, budget["query"])
        ]

        # Truncate each layer to budget
        final_context = []
        for name, content, max_tokens in context_layers:
            truncated = self.truncate_to_tokens(content, max_tokens)
            final_context.append(f"## {name.upper()}\n{truncated}")

        return "\n\n".join(final_context)

    def truncate_to_tokens(self, text: str, max_tokens: int) -> str:
        tokens = self.tokenize(text)
        if len(tokens) <= max_tokens:
            return text

        # Truncate and add indicator
        truncated_tokens = tokens[:max_tokens-3]
        return self.detokenize(truncated_tokens) + "..."
```

**Selective Context Injection:**

```python
class SelectiveContextInjector:
    """Only inject context when it's relevant"""

    def __init__(self, memory_store, llm):
        self.memory = memory_store
        self.llm = llm

    async def should_inject_context(
        self,
        query: str,
        context_type: str
    ) -> bool:
        """Decide if context type is relevant to query"""
        prompt = f"""
        Query: {query}
        Context type: {context_type}

        Is this context type relevant to answering the query?
        Answer: yes/no
        """

        response = await self.llm.generate(prompt, max_tokens=5)
        return response.strip().lower() == "yes"

    async def inject_selective_context(
        self,
        query: str,
        user_id: str
    ) -> str:
        # Available context types
        context_types = {
            "user_profile": lambda: self.memory.get_profile(user_id),
            "recent_activity": lambda: self.memory.get_recent_context(user_id),
            "project_context": lambda: self.memory.get_active_project(user_id),
            "reading_history": lambda: self.memory.get_reading_history(user_id)
        }

        # Check relevance of each type
        relevant_context = {}
        for name, getter in context_types.items():
            if await self.should_inject_context(query, name):
                relevant_context[name] = await getter()

        # Build minimal context
        context_parts = [
            f"{name}: {content}"
            for name, content in relevant_context.items()
        ]

        return "\n".join(context_parts)
```

### 5.4 Balancing Document Knowledge vs. Personal Context

**Weighted Context Blending:**

```python
class ContextBlender:
    def __init__(self):
        self.weights = {
            "documents": 0.6,      # Primary source of facts
            "user_memory": 0.3,    # Personalisation layer
            "general_knowledge": 0.1  # LLM base knowledge
        }

    async def blend_contexts(
        self,
        query: str,
        user_id: str
    ) -> tuple[str, dict]:
        # Retrieve from each source
        doc_results = await self.search_documents(query)
        memory_context = await self.get_memory_context(user_id, query)

        # Determine query type
        query_type = self.classify_query(query)

        # Adjust weights based on query type
        if query_type == "factual":
            # Factual queries rely more on documents
            weights = {"documents": 0.8, "user_memory": 0.1, "general": 0.1}
        elif query_type == "personal":
            # Personal queries rely more on memory
            weights = {"documents": 0.2, "user_memory": 0.7, "general": 0.1}
        elif query_type == "contextual":
            # Contextual queries need both
            weights = {"documents": 0.5, "user_memory": 0.4, "general": 0.1}
        else:
            weights = self.weights  # Default

        # Build weighted context
        context = self.build_weighted_context(
            doc_results,
            memory_context,
            weights
        )

        return context, weights

    def build_weighted_context(
        self,
        doc_results: list,
        memory_context: str,
        weights: dict
    ) -> str:
        # Allocate token budget based on weights
        total_tokens = 4000
        doc_tokens = int(total_tokens * weights["documents"])
        memory_tokens = int(total_tokens * weights["user_memory"])

        # Truncate to budgets
        doc_context = self.truncate_to_tokens(
            self.format_docs(doc_results),
            doc_tokens
        )
        memory_context = self.truncate_to_tokens(
            memory_context,
            memory_tokens
        )

        return f"""
        DOCUMENT KNOWLEDGE:
        {doc_context}

        USER CONTEXT:
        {memory_context}
        """

    def classify_query(self, query: str) -> str:
        """Classify query to determine context weights"""
        personal_indicators = ["i", "my", "me", "prefer", "usually"]
        factual_indicators = ["what", "how", "when", "where", "who"]

        query_lower = query.lower()

        if any(ind in query_lower for ind in personal_indicators):
            return "personal"
        elif any(ind in query_lower for ind in factual_indicators):
            return "factual"
        else:
            return "contextual"
```

---

## 6. Recommendations for Ragged's Personal Memory Architecture

### 6.1 Recommended Architecture

Based on the research, here's the recommended architecture for ragged:

```
┌─────────────────────────────────────────────────────────────┐
│                    RAGGED ARCHITECTURE                       │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│  Layer 1: Document Store (Primary Knowledge Base)           │
│  - SQLite with sqlite-vec extension                         │
│  - Immutable, versioned documents                           │
│  - Fast vector search for retrieval                         │
└─────────────────────────────────────────────────────────────┘
                            ↕
┌─────────────────────────────────────────────────────────────┐
│  Layer 2: Personal Memory Store (Hybrid Approach)           │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  SQLite Database (Structured Memory)                 │  │
│  │  - User profiles                                     │  │
│  │  - Interaction history                               │  │
│  │  - Reading history                                   │  │
│  │  - Project contexts                                  │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Embedded Graph (Temporal Knowledge)                 │  │
│  │  - Kuzu (embedded graph database)                    │  │
│  │  - Facts as nodes, relationships as edges            │  │
│  │  - Temporal tracking (valid_at, invalid_at)          │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Vector Index (Semantic Memory)                      │  │
│  │  - SQLite-vec for fast retrieval                     │  │
│  │  - Cached embeddings                                 │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                            ↕
┌─────────────────────────────────────────────────────────────┐
│  Layer 3: Memory Management (Inspired by Letta + Zep)       │
│  - LangGraph for state persistence                          │
│  - Graphiti-inspired temporal graph logic                   │
│  - Mem0-style automatic fact extraction                     │
└─────────────────────────────────────────────────────────────┘
                            ↕
┌─────────────────────────────────────────────────────────────┐
│  Layer 4: Local LLM Stack                                   │
│  - Ollama for LLM inference                                 │
│  - sentence-transformers for embeddings                     │
│  - No external API calls                                    │
└─────────────────────────────────────────────────────────────┘
```

**Why This Architecture?**

1. **Privacy-First**: Everything runs locally, no cloud dependencies
2. **Performance**: SQLite is fast, lightweight, and battle-tested
3. **Simplicity**: Single-file databases, easy backup/export
4. **Hybrid Approach**: Combines best of Letta (self-editing), Mem0 (ease), and Zep (temporal graphs)
5. **Proven Tech**: All components have strong track records

### 6.2 Technology Stack Recommendations

**Core Components:**

| Component | Technology | Reasoning |
|-----------|-----------|-----------|
| Document DB | SQLite + sqlite-vec | Single file, embedded, fast vector search |
| Memory DB | SQLite | Same as above, separate concerns |
| Graph Store | Kuzu | Embedded graph DB, no server needed |
| LLM | Ollama (llama3.1, qwen2.5) | Local inference, privacy-preserving |
| Embeddings | sentence-transformers | Local embedding generation |
| State Management | LangGraph + SqliteSaver | Production-ready persistence |
| Orchestration | LangGraph | Standard for agents in 2025 |

**Why NOT the others?**

- **Neo4j**: Requires server, overkill for local-only
- **PostgreSQL**: Too heavy for local deployment
- **Qdrant/Milvus**: Excellent but require servers
- **OpenAI APIs**: Not privacy-first

### 6.3 Implementation Roadmap

**Phase 1: Basic Memory (Weeks 1-2)**

```python
# Simple memory store
class BasicMemory:
    """Minimal viable memory - start here"""
    def __init__(self, db_path: str):
        self.db = sqlite3.connect(db_path)
        self.init_tables()

    def init_tables(self):
        self.db.execute("""
            CREATE TABLE IF NOT EXISTS user_profiles (
                user_id TEXT PRIMARY KEY,
                preferences JSON,
                created_at TIMESTAMP
            )
        """)

        self.db.execute("""
            CREATE TABLE IF NOT EXISTS interactions (
                id TEXT PRIMARY KEY,
                user_id TEXT,
                query TEXT,
                response TEXT,
                timestamp TIMESTAMP,
                feedback INTEGER
            )
        """)

    def add_interaction(self, user_id: str, query: str, response: str):
        self.db.execute("""
            INSERT INTO interactions (id, user_id, query, response, timestamp)
            VALUES (?, ?, ?, ?, ?)
        """, (str(uuid.uuid4()), user_id, query, response, datetime.now()))
        self.db.commit()

    def get_recent_context(self, user_id: str, limit: int = 5) -> str:
        rows = self.db.execute("""
            SELECT query, response FROM interactions
            WHERE user_id = ?
            ORDER BY timestamp DESC
            LIMIT ?
        """, (user_id, limit)).fetchall()

        return "\n".join([f"Q: {q}\nA: {r}" for q, r in rows])
```

**Phase 2: Vector Memory (Weeks 3-4)**

```python
# Add vector search capability
import sqlite_vec

class VectorMemory(BasicMemory):
    def init_tables(self):
        super().init_tables()

        # Add vector extension
        self.db.enable_load_extension(True)
        sqlite_vec.load(self.db)

        self.db.execute("""
            CREATE VIRTUAL TABLE IF NOT EXISTS memory_vectors
            USING vec0(
                id TEXT PRIMARY KEY,
                embedding FLOAT[384],  -- sentence-transformers dimension
                content TEXT,
                user_id TEXT,
                timestamp TIMESTAMP
            )
        """)

    def add_memory(self, user_id: str, content: str):
        # Generate embedding locally
        embedding = self.get_embedding(content)

        self.db.execute("""
            INSERT INTO memory_vectors (id, embedding, content, user_id, timestamp)
            VALUES (?, ?, ?, ?, ?)
        """, (
            str(uuid.uuid4()),
            embedding,
            content,
            user_id,
            datetime.now()
        ))
        self.db.commit()

    def search_memory(self, query: str, user_id: str, limit: int = 3):
        query_embedding = self.get_embedding(query)

        results = self.db.execute("""
            SELECT content, vec_distance_cosine(embedding, ?) as distance
            FROM memory_vectors
            WHERE user_id = ?
            ORDER BY distance
            LIMIT ?
        """, (query_embedding, user_id, limit)).fetchall()

        return [r[0] for r in results]
```

**Phase 3: Temporal Graph (Weeks 5-6)**

```python
# Add temporal knowledge graph with Kuzu
import kuzu

class TemporalMemory(VectorMemory):
    def __init__(self, db_path: str, graph_path: str):
        super().__init__(db_path)
        self.graph = kuzu.Database(graph_path)
        self.conn = kuzu.Connection(self.graph)
        self.init_graph_schema()

    def init_graph_schema(self):
        # Create node table for entities
        self.conn.execute("""
            CREATE NODE TABLE IF NOT EXISTS Entity(
                name STRING,
                type STRING,
                user_id STRING,
                valid_at TIMESTAMP,
                invalid_at TIMESTAMP,
                PRIMARY KEY (name, user_id)
            )
        """)

        # Create edge table for relationships
        self.conn.execute("""
            CREATE REL TABLE IF NOT EXISTS Relationship(
                FROM Entity TO Entity,
                type STRING,
                fact STRING,
                valid_at TIMESTAMP,
                invalid_at TIMESTAMP
            )
        """)

    def add_fact(
        self,
        user_id: str,
        subject: str,
        relation: str,
        object: str,
        timestamp: datetime = None
    ):
        if timestamp is None:
            timestamp = datetime.now()

        # Create or update entities
        for entity in [subject, object]:
            self.conn.execute("""
                MERGE (e:Entity {name: $name, user_id: $user_id})
                ON CREATE SET e.valid_at = $timestamp
            """, {"name": entity, "user_id": user_id, "timestamp": timestamp})

        # Create relationship
        self.conn.execute("""
            MATCH (s:Entity {name: $subject, user_id: $user_id})
            MATCH (o:Entity {name: $object, user_id: $user_id})
            CREATE (s)-[r:Relationship {
                type: $relation,
                fact: $fact,
                valid_at: $timestamp
            }]->(o)
        """, {
            "subject": subject,
            "object": object,
            "user_id": user_id,
            "relation": relation,
            "fact": f"{subject} {relation} {object}",
            "timestamp": timestamp
        })
```

**Phase 4: Integration with RAG (Weeks 7-8)**

```python
class PersonalizedRAG:
    def __init__(
        self,
        doc_store: DocumentStore,
        memory: TemporalMemory,
        llm: OllamaLLM
    ):
        self.docs = doc_store
        self.memory = memory
        self.llm = llm

    async def query(self, user_id: str, query: str) -> str:
        # 1. Get personal context
        recent_context = self.memory.get_recent_context(user_id)
        memory_facts = self.memory.search_memory(query, user_id)
        graph_context = self.memory.query_graph(user_id, query)

        # 2. Enhance query
        enhanced_query = await self.enhance_query(
            query,
            memory_facts,
            graph_context
        )

        # 3. Retrieve documents
        doc_results = await self.docs.search(enhanced_query)

        # 4. Build context
        context = self.build_context(
            recent_context,
            memory_facts,
            doc_results
        )

        # 5. Generate response
        response = await self.llm.generate(
            system="You are a helpful assistant with memory.",
            context=context,
            query=query
        )

        # 6. Extract and store new facts
        facts = await self.extract_facts(query, response)
        for fact in facts:
            self.memory.add_fact(user_id, **fact)

        # 7. Record interaction
        self.memory.add_interaction(user_id, query, response)

        return response
```

### 6.4 Privacy Considerations

**Privacy-by-Design Principles:**

1. **Data Minimization**: Only store what's necessary
2. **Local Processing**: No data leaves the device
3. **User Control**: Easy export/delete
4. **Encryption**: Sensitive data encrypted at rest
5. **Transparency**: Clear audit logs

**Implementation Checklist:**

```python
class PrivacyCompliantMemory:
    """Memory system with privacy guarantees"""

    def __init__(self, config: PrivacyConfig):
        self.config = config
        self.encryption = LocalEncryption()
        self.audit_log = AuditLog()

    async def store_data(self, user_id: str, data: dict):
        # Check privacy level
        if data.get("privacy_level") == "sensitive":
            # Encrypt sensitive data
            data["content"] = self.encryption.encrypt(data["content"])
            data["encrypted"] = True

        # Set retention policy
        if self.config.max_retention_days:
            data["expires_at"] = (
                datetime.now() +
                timedelta(days=self.config.max_retention_days)
            )

        # Store with audit
        await self.db.insert(data)
        self.audit_log.record("store", user_id, data["id"])

    async def export_all(self, user_id: str) -> bytes:
        """GDPR Article 20: Right to data portability"""
        data = await self.collect_all_user_data(user_id)
        self.audit_log.record("export", user_id, len(data))
        return json.dumps(data, indent=2).encode()

    async def delete_all(self, user_id: str, confirmation: str):
        """GDPR Article 17: Right to erasure"""
        if confirmation != f"DELETE {user_id}":
            raise ValueError("Confirmation required")

        # Delete from all stores
        await self.db.delete_user(user_id)
        await self.vector_store.delete_user(user_id)
        await self.graph_store.delete_user(user_id)

        self.audit_log.record("delete", user_id, "all_data")

    async def auto_expire(self):
        """Automatically delete expired data"""
        expired = await self.db.query("""
            SELECT user_id, id FROM memory_items
            WHERE expires_at IS NOT NULL AND expires_at < ?
        """, (datetime.now(),))

        for user_id, item_id in expired:
            await self.db.delete(item_id)
            self.audit_log.record("auto_expire", user_id, item_id)
```

**Privacy Configuration:**

```yaml
# config/privacy.yaml
privacy:
  # Data retention
  max_retention_days: 90  # Auto-delete after 90 days

  # Encryption
  encrypt_sensitive: true
  key_path: ~/.ragged/memory.key

  # Privacy levels
  default_privacy_level: private

  # Consent
  require_explicit_consent: true

  # Export/Delete
  export_format: json
  enable_gdpr_endpoints: true

  # Audit
  audit_log_enabled: true
  audit_log_path: ~/.ragged/audit.log
```

### 6.5 Code Patterns and Examples

**Complete Example: Minimal Ragged Memory:**

```python
#!/usr/bin/env python3
"""
Minimal implementation of Ragged's personal memory system.
Privacy-first, local-only, SQLite-based.
"""

import sqlite3
import json
from datetime import datetime, timedelta
from typing import Optional
import numpy as np
from sentence_transformers import SentenceTransformer

class RaggedMemory:
    """Privacy-first personal memory for RAG applications"""

    def __init__(self, db_path: str = "~/.ragged/memory.db"):
        self.db_path = os.path.expanduser(db_path)
        self.db = sqlite3.connect(self.db_path)
        self.embedder = SentenceTransformer('all-MiniLM-L6-v2')
        self.init_database()

    def init_database(self):
        """Initialize database schema"""
        # User profiles
        self.db.execute("""
            CREATE TABLE IF NOT EXISTS user_profiles (
                user_id TEXT PRIMARY KEY,
                preferences JSON,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Interactions
        self.db.execute("""
            CREATE TABLE IF NOT EXISTS interactions (
                id TEXT PRIMARY KEY,
                user_id TEXT,
                query TEXT,
                response TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                feedback INTEGER,
                FOREIGN KEY (user_id) REFERENCES user_profiles(user_id)
            )
        """)

        # Facts (extracted knowledge)
        self.db.execute("""
            CREATE TABLE IF NOT EXISTS facts (
                id TEXT PRIMARY KEY,
                user_id TEXT,
                content TEXT,
                confidence REAL,
                source_interaction TEXT,
                valid_from TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                valid_to TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES user_profiles(user_id)
            )
        """)

        # Vector index (for semantic search)
        self.db.execute("""
            CREATE TABLE IF NOT EXISTS memory_vectors (
                id TEXT PRIMARY KEY,
                user_id TEXT,
                content TEXT,
                embedding BLOB,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES user_profiles(user_id)
            )
        """)

        self.db.commit()

    def add_interaction(
        self,
        user_id: str,
        query: str,
        response: str,
        feedback: Optional[int] = None
    ):
        """Record an interaction"""
        interaction_id = str(uuid.uuid4())

        self.db.execute("""
            INSERT INTO interactions (id, user_id, query, response, feedback)
            VALUES (?, ?, ?, ?, ?)
        """, (interaction_id, user_id, query, response, feedback))

        self.db.commit()
        return interaction_id

    def extract_and_store_facts(
        self,
        user_id: str,
        interaction_id: str,
        llm_extractor
    ):
        """Extract facts from interaction using LLM"""
        # Get interaction
        interaction = self.db.execute("""
            SELECT query, response FROM interactions WHERE id = ?
        """, (interaction_id,)).fetchone()

        if not interaction:
            return []

        query, response = interaction

        # Use LLM to extract facts
        extraction_prompt = f"""
        From this conversation, extract factual statements about the user.

        User: {query}
        Assistant: {response}

        Extract facts in JSON format:
        [
            {{"fact": "user prefers X", "confidence": 0.9}},
            ...
        ]
        """

        facts_json = llm_extractor.generate(extraction_prompt)
        facts = json.loads(facts_json)

        # Store facts
        for fact in facts:
            fact_id = str(uuid.uuid4())

            # Store in facts table
            self.db.execute("""
                INSERT INTO facts
                (id, user_id, content, confidence, source_interaction)
                VALUES (?, ?, ?, ?, ?)
            """, (
                fact_id,
                user_id,
                fact["fact"],
                fact["confidence"],
                interaction_id
            ))

            # Generate and store embedding
            embedding = self.embedder.encode(fact["fact"])

            self.db.execute("""
                INSERT INTO memory_vectors
                (id, user_id, content, embedding)
                VALUES (?, ?, ?, ?)
            """, (
                fact_id,
                user_id,
                fact["fact"],
                embedding.tobytes()
            ))

        self.db.commit()
        return facts

    def search_memory(
        self,
        user_id: str,
        query: str,
        top_k: int = 5
    ) -> list[str]:
        """Semantic search over user's memory"""
        # Generate query embedding
        query_embedding = self.embedder.encode(query)

        # Get all user's memories
        memories = self.db.execute("""
            SELECT id, content, embedding FROM memory_vectors
            WHERE user_id = ?
        """, (user_id,)).fetchall()

        if not memories:
            return []

        # Compute similarities
        scores = []
        for mem_id, content, emb_bytes in memories:
            mem_embedding = np.frombuffer(emb_bytes, dtype=np.float32)
            similarity = np.dot(query_embedding, mem_embedding) / (
                np.linalg.norm(query_embedding) * np.linalg.norm(mem_embedding)
            )
            scores.append((similarity, content))

        # Sort by similarity
        scores.sort(reverse=True)

        return [content for _, content in scores[:top_k]]

    def get_recent_context(
        self,
        user_id: str,
        hours: int = 24,
        limit: int = 5
    ) -> str:
        """Get recent conversation context"""
        cutoff = datetime.now() - timedelta(hours=hours)

        interactions = self.db.execute("""
            SELECT query, response, timestamp
            FROM interactions
            WHERE user_id = ? AND timestamp > ?
            ORDER BY timestamp DESC
            LIMIT ?
        """, (user_id, cutoff, limit)).fetchall()

        context = []
        for query, response, timestamp in interactions:
            context.append(f"[{timestamp}]\nUser: {query}\nAssistant: {response}")

        return "\n\n".join(context)

    def export_user_data(self, user_id: str) -> dict:
        """Export all user data (GDPR compliance)"""
        return {
            "user_id": user_id,
            "export_date": datetime.now().isoformat(),
            "profile": self.db.execute(
                "SELECT * FROM user_profiles WHERE user_id = ?",
                (user_id,)
            ).fetchone(),
            "interactions": self.db.execute(
                "SELECT * FROM interactions WHERE user_id = ? ORDER BY timestamp",
                (user_id,)
            ).fetchall(),
            "facts": self.db.execute(
                "SELECT * FROM facts WHERE user_id = ? ORDER BY valid_from",
                (user_id,)
            ).fetchall()
        }

    def delete_user_data(self, user_id: str, confirmation: str):
        """Delete all user data (GDPR right to erasure)"""
        if confirmation != f"DELETE {user_id}":
            raise ValueError("Confirmation string doesn't match")

        tables = ["memory_vectors", "facts", "interactions", "user_profiles"]
        for table in tables:
            self.db.execute(f"DELETE FROM {table} WHERE user_id = ?", (user_id,))

        self.db.commit()

# Usage example
if __name__ == "__main__":
    memory = RaggedMemory()

    # Add interaction
    user_id = "user_123"
    interaction_id = memory.add_interaction(
        user_id,
        "I prefer Python over JavaScript",
        "Noted! I'll keep that in mind when suggesting programming languages."
    )

    # Search memory
    results = memory.search_memory(user_id, "What programming language does the user like?")
    print("Memory search results:", results)

    # Export data
    user_data = memory.export_user_data(user_id)
    print("Exported data:", json.dumps(user_data, indent=2))
```

---

## 7. Additional Research Findings

### 7.1 Benchmark Summary

| Benchmark | What It Tests | Leading Systems |
|-----------|---------------|-----------------|
| LoCoMo | Very long-term conversations (300 turns, 9K tokens, 35 sessions) | Mem0: 66.9%, OpenAI: 52.9%, Letta: 74.0% |
| DMR (Deep Memory Retrieval) | Fact retrieval from 60-message conversations | Zep: 94.8%, Letta: 93.4% |
| LongMemEval | Complex memory tasks across 115k-1.5M tokens, 5 core abilities | Zep: +18.5% accuracy, -90% latency vs baseline |

**Key Takeaway**: DMR is becoming less relevant as LLMs can fit 60-message conversations in context. LongMemEval is the new gold standard.

### 7.2 Performance Metrics

**Mem0:**
- 26% accuracy improvement over OpenAI
- 91% lower p95 latency
- 90% token cost reduction
- 186M API calls in Q3 2025 (30% MoM growth)

**Zep:**
- 94.8% DMR accuracy (vs 93.4% for Letta)
- Up to 18.5% accuracy improvement on LongMemEval
- 90% latency reduction
- P95 latency: 300ms (no LLM calls during retrieval)

**Letta:**
- 74.0% on LoCoMo benchmark (gpt-4o-mini)
- Strong theoretical foundation
- Self-editing memory paradigm

### 7.3 Emerging Trends (2025)

1. **Graph Memory**: Moving from flat vector stores to graph-based representations
2. **Temporal Awareness**: Tracking how facts evolve over time
3. **Hybrid Approaches**: Combining vector + graph + structured storage
4. **Local-First**: Privacy concerns driving local deployment
5. **Production Ready**: LangGraph becoming standard for state management
6. **Automatic Extraction**: LLM-based fact extraction from conversations
7. **Persona-Based**: Multi-persona systems for specialised tasks
8. **Context Engineering**: The "#1 job of AI engineers"

### 7.4 Privacy Techniques

**Differential Privacy:**
- Local DP (client-side noise)
- Central DP (server-side aggregation)
- Adaptive privacy budgets
- Typical ε values: 0.1-1.0

**Federated Learning:**
- Collaborative model training without data sharing
- Communication-efficient algorithms (90% reduction)
- Healthcare and finance applications

**Encryption:**
- At-rest encryption (Fernet, AES)
- Searchable encryption research (single-digit ms overhead)
- Homomorphic encryption for computation on encrypted data

**Anonymization:**
- Entity perturbation
- k-anonymity
- Pseudonymization

### 7.5 Real-World Applications

**Legal (August):**
- Personas for lawyer-specific preferences
- 25% accuracy improvement
- 50% reduction in follow-up questions

**Healthcare:**
- Federated learning with differential privacy
- Patient data never leaves hospitals
- Collaborative model training

**Enterprise:**
- Knowledge management (McKinsey research)
- Agentic AI for deep research
- Cross-document synthesis

---

## 8. Conclusion

The state-of-the-art in personal memory and context systems for AI applications has matured significantly in 2025. Three major paradigms have emerged:

1. **Virtual Context Management (Letta)**: OS-inspired memory hierarchy with self-editing
2. **Graph-Based Memory (Mem0, Zep)**: Temporal knowledge graphs for relationship tracking
3. **Hybrid Production Systems (LangGraph)**: Practical state management for real applications

For **ragged**, a privacy-first local RAG system, the recommended approach is:

**Hybrid Architecture:**
- SQLite for structured data (profiles, interactions, history)
- sqlite-vec for semantic search
- Kuzu for temporal knowledge graph
- LangGraph for state management
- Ollama for local LLM inference

**Key Advantages:**
- ✅ Fully local (no cloud dependencies)
- ✅ Privacy-preserving (data never leaves device)
- ✅ GDPR-compliant (easy export/delete)
- ✅ Battle-tested components (SQLite, proven libraries)
- ✅ Single-file databases (easy backup)
- ✅ Production-ready (LangGraph is standard)

**Implementation Priority:**
1. Basic interaction history (Week 1-2)
2. Vector memory for semantic search (Week 3-4)
3. Temporal graph for fact tracking (Week 5-6)
4. Integration with RAG pipeline (Week 7-8)

The research shows that effective personal memory systems can provide 20-30% accuracy improvements while reducing costs by 80-90%. For a privacy-first system like ragged, the local-only approach is not just feasible but recommended, with all necessary components available as open-source, production-ready tools.

---

## References

### Research Papers
- "MemGPT: Towards LLMs as Operating Systems" (arXiv:2310.08560)
- "Mem0: Building Production-Ready AI Agents with Scalable Long-Term Memory" (arXiv:2504.19413)
- "Zep: A Temporal Knowledge Graph Architecture for Agent Memory" (arXiv:2501.13956)
- "LongMemEval: Benchmarking Chat Assistants on Long-Term Interactive Memory" (arXiv:2410.10813)
- "Evaluating Very Long-Term Conversational Memory of LLM Agents" (arXiv:2402.17753)
- "A Survey of Personalisation: From RAG to Agent" (arXiv:2504.10147)
- "Enabling Personalised Long-term Interactions in LLM-based Agents" (arXiv:2510.07925)

### Open Source Projects
- Letta: github.com/letta-ai/letta
- Mem0: github.com/mem0ai/mem0
- Graphiti: github.com/getzep/graphiti
- LangChain: github.com/langchain-ai/langchain
- LangGraph: github.com/langchain-ai/langgraph
- sqlite-vec: github.com/asg017/sqlite-vec
- Kuzu: github.com/kuzudb/kuzu

### Documentation
- Letta Docs: docs.letta.com
- Mem0 Docs: docs.mem0.ai
- Zep Docs: help.getzep.com
- LangGraph Docs: langchain-ai.github.io/langgraph

### Courses
- "LLMs as Operating Systems: Agent Memory" (DeepLearning.AI)

---

**Report compiled:** November 9, 2025
**Total sources reviewed:** 50+ research papers, documentation pages, and implementations
**Focus:** Privacy-first, local-only deployment for ragged
