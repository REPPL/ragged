# Behaviour Learning API Reference

**Complete API documentation for ragged's behaviour learning system**

**Version:** 0.4.7+
**Module:** `ragged.memory`

---

## Quick Reference

| Class | Purpose | Location |
|-------|---------|----------|
| `BehaviourLearner` | Main orchestrator for behaviour learning | `ragged.memory.behaviour` |
| `TopicExtractor` | Extract topics from text | `ragged.memory.topics` |
| `TopicExtractionConfig` | Configure topic extraction | `ragged.memory.topic_config` |
| `ConfidenceCalculator` | Calculate topic confidence scores | `ragged.memory.confidence` |
| `InterestProfile` | User interest profile | `ragged.memory.profile` |
| `ProfileManager` | CRUD operations for profiles | `ragged.memory.profile` |
| `TopicInterest` | Individual topic interest data | `ragged.memory.profile` |
| `Interaction` | User interaction record | `ragged.memory.interactions` |
| `InteractionTracker` | Track and store interactions | `ragged.memory.interactions` |

---

## ragged.memory.behaviour

### BehaviourLearner

**Main orchestrator for behaviour learning.**

```python
class BehaviourLearner:
    def __init__(
        self,
        profile_manager: ProfileManager,
        topic_config: Optional[TopicExtractionConfig] = None,
        confidence_calculator: Optional[ConfidenceCalculator] = None,
        knowledge_graph: Optional[KnowledgeGraph] = None,
        enable_graph_updates: bool = False
    )
```

**Parameters:**
- `profile_manager` (ProfileManager): ProfileManager instance for storing profiles
- `topic_config` (Optional[TopicExtractionConfig]): Topic extraction configuration (default: None, uses defaults)
- `confidence_calculator` (Optional[ConfidenceCalculator]): Confidence calculator (default: None, uses defaults)
- `knowledge_graph` (Optional[KnowledgeGraph]): Knowledge graph for relationship tracking (default: None)
- `enable_graph_updates` (bool): Enable automatic graph updates (default: False)

**Attributes:**
- `profile_manager` (ProfileManager): Profile manager instance
- `extractor` (TopicExtractor): Topic extractor instance
- `confidence_calculator` (ConfidenceCalculator): Confidence calculator instance
- `knowledge_graph` (Optional[KnowledgeGraph]): Knowledge graph instance
- `enable_graph_updates` (bool): Graph update status

#### process_interaction()

**Process user interaction and update interest profile.**

```python
def process_interaction(self, interaction: Interaction) -> InterestProfile
```

**Parameters:**
- `interaction` (Interaction): User interaction to process

**Returns:**
- `InterestProfile`: Updated interest profile

**Raises:**
- None (errors logged, doesn't fail)

**Example:**
```python
from ragged.memory.interactions import Interaction

interaction = Interaction(
    persona="researcher",
    query="What is RAG?",
    retrieved_doc_ids=["rag_paper.pdf"]
)

profile = learner.process_interaction(interaction)
print(f"Total topics: {len(profile.topics)}")
```

#### process_batch()

**Process multiple interactions in batch.**

```python
def process_batch(self, interactions: List[Interaction]) -> None
```

**Parameters:**
- `interactions` (List[Interaction]): List of interactions to process

**Returns:**
- None

**Example:**
```python
interactions = [
    Interaction(persona="user", query="What is RAG?"),
    Interaction(persona="user", query="Vector databases")
]

learner.process_batch(interactions)
```

#### get_persona_insights()

**Get insights about persona's interests.**

```python
def get_persona_insights(self, persona: str) -> dict
```

**Parameters:**
- `persona` (str): Persona name

**Returns:**
- `dict`: Insights dictionary containing:
  - `top_topics` (List[dict]): Top 10 topics by confidence
  - `total_topics` (int): Total topics tracked
  - `profile_age_days` (int): Days since profile creation
  - `most_related_topics` (List[dict]): Topics with most co-occurrences

**Example:**
```python
insights = learner.get_persona_insights("researcher")
print(f"Top topic: {insights['top_topics'][0]['topic']}")
print(f"Total topics: {insights['total_topics']}")
```

#### forget_topic()

**Remove topic from profile (GDPR right to erasure).**

```python
def forget_topic(self, persona: str, topic_name: str) -> bool
```

**Parameters:**
- `persona` (str): Persona name
- `topic_name` (str): Topic to remove (case-insensitive)

**Returns:**
- `bool`: True if topic was removed, False if not found

**Example:**
```python
removed = learner.forget_topic("researcher", "RAG")
if removed:
    print("Topic forgotten")
```

#### reset_profile()

**Reset entire profile (GDPR right to erasure).**

```python
def reset_profile(self, persona: str) -> bool
```

**Parameters:**
- `persona` (str): Persona name

**Returns:**
- `bool`: True if profile was reset

**Example:**
```python
learner.reset_profile("researcher")
```

#### export_profile()

**Export profile as JSON (GDPR data portability).**

```python
def export_profile(self, persona: str) -> str
```

**Parameters:**
- `persona` (str): Persona name

**Returns:**
- `str`: JSON string of profile

**Example:**
```python
json_data = learner.export_profile("researcher")
with open("profile.json", "w") as f:
    f.write(json_data)
```

### create_behaviour_learner()

**Helper function to create behaviour learner with defaults.**

```python
def create_behaviour_learner(
    storage_dir: Path,
    topic_config: Optional[TopicExtractionConfig] = None,
    enable_graph: bool = False
) -> BehaviourLearner
```

**Parameters:**
- `storage_dir` (Path): Directory for storing profiles and graph
- `topic_config` (Optional[TopicExtractionConfig]): Topic extraction configuration (default: None)
- `enable_graph` (bool): Enable knowledge graph integration (default: False)

**Returns:**
- `BehaviourLearner`: Configured behaviour learner instance

**Example:**
```python
from pathlib import Path
from ragged.memory.behaviour import create_behaviour_learner

learner = create_behaviour_learner(
    storage_dir=Path("~/.ragged/memory").expanduser(),
    enable_graph=False
)
```

---

## ragged.memory.topics

### Topic

**Extracted topic with confidence score.**

```python
@dataclass
class Topic:
    name: str                              # Topic name (normalised)
    confidence: float                      # Confidence score (0.0-1.0)
    raw_text: str = ""                     # Original text before normalisation
    extracted_at: datetime = field(default_factory=datetime.now)  # Extraction timestamp
```

**Validation:**
- `confidence` must be 0.0-1.0 (raises ValueError otherwise)
- `name` cannot be empty (raises ValueError otherwise)

### TopicExtractor

**Extract topics from text using keyword-based extraction.**

```python
class TopicExtractor:
    def __init__(
        self,
        min_topic_length: int = 3,
        max_topics_per_query: int = 10,
        min_confidence: float = 0.3,
        stop_words: Set[str] | None = None,
        enable_phrases: bool = True
    )
```

**Parameters:**
- `min_topic_length` (int): Minimum characters for valid topic (default: 3)
- `max_topics_per_query` (int): Maximum topics to extract (default: 10)
- `min_confidence` (float): Minimum confidence threshold 0.0-1.0 (default: 0.3)
- `stop_words` (Set[str] | None): Custom stop words set (default: None, uses DEFAULT_STOP_WORDS)
- `enable_phrases` (bool): Enable multi-word phrase detection (default: True)

#### extract_topics()

**Extract topics from query text.**

```python
def extract_topics(self, query: str) -> List[Topic]
```

**Parameters:**
- `query` (str): User query text

**Returns:**
- `List[Topic]`: Extracted topics sorted by confidence (highest first)

**Example:**
```python
extractor = TopicExtractor()
topics = extractor.extract_topics("What is RAG?")

for topic in topics:
    print(f"{topic.name}: {topic.confidence:.2f}")
# Output: rag: 0.90
```

#### extract_from_documents()

**Extract topics from retrieved documents.**

```python
def extract_from_documents(
    self,
    doc_ids: List[str],
    doc_texts: List[str] | None = None
) -> List[Topic]
```

**Parameters:**
- `doc_ids` (List[str]): Document IDs (filenames)
- `doc_texts` (List[str] | None): Optional document content (future use, default: None)

**Returns:**
- `List[Topic]`: Extracted topics from document IDs

**Example:**
```python
topics = extractor.extract_from_documents(
    ["rag_paper_2023.pdf", "vector_db_guide.md"]
)
```

---

## ragged.memory.topic_config

### TopicExtractionConfig

**Configuration for topic extraction.**

```python
@dataclass
class TopicExtractionConfig:
    min_topic_length: int = 3
    max_topics_per_query: int = 10
    confidence_threshold: float = 0.3
    stop_words: Set[str] = field(default_factory=lambda: DEFAULT_STOP_WORDS.copy())
    enable_phrases: bool = True
```

**Methods:**

#### from_yaml()

```python
@classmethod
def from_yaml(cls, yaml_path: Path) -> "TopicExtractionConfig"
```

Load configuration from YAML file.

#### from_dict()

```python
@classmethod
def from_dict(cls, config_dict: dict) -> "TopicExtractionConfig"
```

Load configuration from dictionary.

#### to_dict()

```python
def to_dict(self) -> dict
```

Convert to dictionary.

#### save_yaml()

```python
def save_yaml(self, yaml_path: Path) -> None
```

Save configuration to YAML file.

---

## ragged.memory.confidence

### ConfidenceCalculator

**Calculate confidence scores for topic interests.**

```python
class ConfidenceCalculator:
    def __init__(
        self,
        frequency_weight: float = 0.35,
        recency_weight: float = 0.30,
        consistency_weight: float = 0.20,
        depth_weight: float = 0.15
    )
```

**Parameters:**
- `frequency_weight` (float): Weight for frequency factor (default: 0.35)
- `recency_weight` (float): Weight for recency factor (default: 0.30)
- `consistency_weight` (float): Weight for consistency factor (default: 0.20)
- `depth_weight` (float): Weight for depth factor (default: 0.15)

**Note:** Weights must sum to 1.0 (raises ValueError otherwise)

#### calculate_confidence()

**Calculate overall confidence score.**

```python
def calculate_confidence(
    self,
    frequency: int,
    last_seen: datetime,
    first_seen: datetime,
    related_documents: List[str],
    timestamps: List[datetime] | None = None
) -> float
```

**Parameters:**
- `frequency` (int): Number of times topic queried
- `last_seen` (datetime): Most recent query timestamp
- `first_seen` (datetime): First query timestamp
- `related_documents` (List[str]): Related document IDs
- `timestamps` (List[datetime] | None): All query timestamps (default: None)

**Returns:**
- `float`: Confidence score 0.0-1.0

**Example:**
```python
from datetime import datetime, timedelta

calc = ConfidenceCalculator()

confidence = calc.calculate_confidence(
    frequency=10,
    last_seen=datetime.now(),
    first_seen=datetime.now() - timedelta(days=30),
    related_documents=["doc1", "doc2", "doc3"],
    timestamps=[datetime.now() - timedelta(days=i) for i in range(10)]
)

print(f"Confidence: {confidence:.2f}")
# Output: Confidence: 0.72
```

### update_topic_confidence()

**Helper function to update topic interest confidence.**

```python
def update_topic_confidence(
    interest: TopicInterest,
    calculator: ConfidenceCalculator
) -> None
```

**Parameters:**
- `interest` (TopicInterest): Topic interest to update
- `calculator` (ConfidenceCalculator): Confidence calculator instance

**Returns:**
- None (updates interest in-place)

---

## ragged.memory.profile

### InterestProfile

**User interest profile containing tracked topics.**

```python
@dataclass
class InterestProfile:
    persona: str
    topics: Dict[str, TopicInterest] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
```

#### update_topic_interest()

**Update or create topic interest.**

```python
def update_topic_interest(
    self,
    topic: Topic,
    doc_ids: Optional[List[str]] = None,
    related_topics: Optional[List[str]] = None
) -> None
```

**Parameters:**
- `topic` (Topic): Topic to update
- `doc_ids` (Optional[List[str]]): Related document IDs (default: None)
- `related_topics` (Optional[List[str]]): Co-occurring topic names (default: None)

#### get_topic()

**Get topic interest by name (case-insensitive).**

```python
def get_topic(self, topic_name: str) -> Optional[TopicInterest]
```

**Returns:**
- `Optional[TopicInterest]`: Topic interest or None if not found

#### get_top_topics()

**Get top topics by confidence.**

```python
def get_top_topics(
    self,
    limit: int = 10,
    min_confidence: float = 0.0
) -> List[TopicInterest]
```

**Parameters:**
- `limit` (int): Maximum topics to return (default: 10)
- `min_confidence` (float): Minimum confidence threshold (default: 0.0)

**Returns:**
- `List[TopicInterest]`: Top topics sorted by confidence

#### remove_topic()

**Remove topic from profile.**

```python
def remove_topic(self, topic_name: str) -> bool
```

**Returns:**
- `bool`: True if removed, False if not found

#### apply_time_decay()

**Apply exponential time decay to topic recency.**

```python
def apply_time_decay(
    self,
    decay_rate: float = 0.1,
    decay_days: int = 30
) -> None
```

**Parameters:**
- `decay_rate` (float): Decay rate (default: 0.1)
- `decay_days` (int): Days before decay starts (default: 30)

#### export_to_json()

**Export profile as JSON string.**

```python
def export_to_json(self) -> str
```

### TopicInterest

**Individual topic interest tracking.**

```python
@dataclass
class TopicInterest:
    topic: str
    frequency: int = 1
    recency: float = 1.0
    confidence: float = 0.5
    first_seen: datetime = field(default_factory=datetime.now)
    last_seen: datetime = field(default_factory=datetime.now)
    related_documents: List[str] = field(default_factory=list)
    co_occurring_topics: Dict[str, int] = field(default_factory=dict)
```

### ProfileManager

**Manage CRUD operations for interest profiles.**

```python
class ProfileManager:
    def __init__(self, db_path: Path)
```

**Parameters:**
- `db_path` (Path): Path to SQLite database file

#### get_profile()

**Get or create profile for persona.**

```python
def get_profile(self, persona: str) -> InterestProfile
```

**Parameters:**
- `persona` (str): Persona name

**Returns:**
- `InterestProfile`: Existing or new profile

#### save_profile()

**Save profile to database.**

```python
def save_profile(self, profile: InterestProfile) -> None
```

#### delete_profile()

**Delete profile from database.**

```python
def delete_profile(self, persona: str) -> bool
```

**Returns:**
- `bool`: True if deleted, False if not found

#### list_profiles()

**List all personas with profiles.**

```python
def list_profiles(self) -> List[str]
```

**Returns:**
- `List[str]`: List of persona names

---

## ragged.memory.interactions

### Interaction

**User interaction record.**

```python
@dataclass
class Interaction:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    persona: str = ""
    query: str = ""
    response: str | None = None
    timestamp: datetime = field(default_factory=datetime.now)
    retrieved_doc_ids: list[str] = field(default_factory=list)
    model_used: str | None = None
    latency_ms: float | None = None
    feedback: str | None = None
    session_id: str | None = None
```

### InteractionTracker

**Track user interactions with behaviour learning integration.**

```python
class InteractionTracker:
    def __init__(
        self,
        persona: str | None = None,
        storage_dir: Path | None = None,
        behaviour_learner: "BehaviourLearner | None" = None
    )
```

**Parameters:**
- `persona` (str | None): Default persona (default: None)
- `storage_dir` (Path | None): Storage directory (default: None, uses ~/.ragged/memory/interactions)
- `behaviour_learner` (BehaviourLearner | None): Behaviour learner for automatic profile updates (default: None)

#### record_interaction()

**Record new interaction and update profile (if learner configured).**

```python
def record_interaction(
    self,
    query: str,
    response: str | None = None,
    persona: str | None = None,
    retrieved_doc_ids: list[str] | None = None,
    model_used: str | None = None,
    latency_ms: float | None = None,
    feedback: str | None = None,
    session_id: str | None = None
) -> Interaction
```

**Parameters:**
- `query` (str): User query text
- `response` (str | None): System response (default: None)
- `persona` (str | None): Persona name (default: None, uses tracker default)
- `retrieved_doc_ids` (list[str] | None): Retrieved document IDs (default: None)
- `model_used` (str | None): LLM model identifier (default: None)
- `latency_ms` (float | None): Response latency (default: None)
- `feedback` (str | None): User feedback (positive/negative/neutral) (default: None)
- `session_id` (str | None): Session identifier (default: None)

**Returns:**
- `Interaction`: Created interaction object

**Example:**
```python
tracker = InteractionTracker(
    persona="researcher",
    behaviour_learner=learner  # Automatic profile updates
)

interaction = tracker.record_interaction(
    query="What is RAG?",
    response="Retrieval-Augmented Generation...",
    retrieved_doc_ids=["rag_paper.pdf"]
)
```

---

## CLI Commands

### ragged memory profile

**Show interest profile for persona.**

```bash
ragged memory profile [OPTIONS]
```

**Options:**
- `--persona, -p TEXT`: Persona to view (uses active if not specified)
- `--format, -f [text|json|yaml|table]`: Output format (default: text)

**Example:**
```bash
ragged memory profile --persona researcher
ragged memory profile --format json
```

### ragged memory topics

**List topics from interest profile.**

```bash
ragged memory topics [OPTIONS]
```

**Options:**
- `--persona, -p TEXT`: Persona to query
- `--min-confidence, -c FLOAT`: Minimum confidence threshold (default: 0.3)
- `--limit, -l INTEGER`: Maximum topics to show (default: 20)
- `--format, -f [text|json|yaml|table]`: Output format

**Example:**
```bash
ragged memory topics --min-confidence 0.5 --limit 10
```

### ragged memory topic-info

**Show detailed information about a topic.**

```bash
ragged memory topic-info TOPIC_NAME [OPTIONS]
```

**Arguments:**
- `TOPIC_NAME`: Topic name to query

**Options:**
- `--persona, -p TEXT`: Persona to query
- `--format, -f [text|json|yaml|table]`: Output format

**Example:**
```bash
ragged memory topic-info "rag" --persona researcher
```

### ragged memory related-topics

**Show topics that co-occur with specified topic.**

```bash
ragged memory related-topics TOPIC_NAME [OPTIONS]
```

**Arguments:**
- `TOPIC_NAME`: Topic name

**Options:**
- `--persona, -p TEXT`: Persona to query
- `--limit, -l INTEGER`: Maximum related topics (default: 10)

**Example:**
```bash
ragged memory related-topics "rag" --limit 5
```

### ragged memory forget-topic

**Remove topic from profile (GDPR right to erasure).**

```bash
ragged memory forget-topic TOPIC_NAME [OPTIONS]
```

**Arguments:**
- `TOPIC_NAME`: Topic name to remove

**Options:**
- `--persona, -p TEXT`: Persona to modify
- `--yes, -y`: Skip confirmation prompt

**Example:**
```bash
ragged memory forget-topic "sensitive-topic" --yes
```

---

## Related Documentation

- [Understanding Your Interest Profile Tutorial](../tutorials/understanding-your-interest-profile.md) - User-focused guide
- [Behaviour Learning System Guide](../guides/behaviour-learning.md) - Technical implementation details
- [Memory Management Guide](../guides/memory-management.md) - Interaction tracking

---
