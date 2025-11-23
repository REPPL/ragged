# Behaviour Learning System

**Guide: Technical details of ragged's behaviour learning system**

**Audience:** Developers, power users, contributors
**Version:** 0.4.7+
**Status:** Phase 1 (Keyword-based extraction)

---

## Overview

The behaviour learning system automatically builds user interest profiles from query patterns and document retrieval, enabling future personalised experiences while maintaining strict privacy guarantees.

### Design Goals

1. **Privacy-First**: All learning happens locally, zero external API calls
2. **Automatic**: No manual tagging or configuration required
3. **Transparent**: Users can view, export, and delete all learned data
4. **Accurate**: Confidence scores reflect actual user interest
5. **Extensible**: Designed for future NLP/LLM enhancement

### Phase 1 Scope (v0.4.7)

**Current Implementation:**
- Keyword-based topic extraction
- Frequency and recency tracking
- Confidence scoring algorithm
- CLI integration
- GDPR compliance

**Future Phases (v0.5.x):**
- NLP-based extraction (spaCy, transformers)
- LLM-enhanced topic identification
- Semantic clustering
- Personalised retrieval ranking

---

## System Architecture

### Component Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    User Query                              │
└───────────────────┬─────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────────────────┐
│            InteractionTracker                               │
│  - Records query, response, doc_ids                        │
│  - Passes to BehaviourLearner (if configured)             │
└───────────────────┬─────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────────────────┐
│            BehaviourLearner                                 │
│  - Orchestrates learning pipeline                          │
│  - Coordinates components                                  │
└───────────────────┬─────────────────────────────────────────┘
                    │
        ┌───────────┴───────────┐
        ▼                       ▼
┌──────────────────┐    ┌──────────────────┐
│ TopicExtractor   │    │ ProfileManager   │
│ - Query parsing  │    │ - Profile CRUD   │
│ - Document       │    │ - Persistence    │
│   analysis       │    │ - JSON export    │
└────────┬─────────┘    └────────┬─────────┘
         │                       │
         ▼                       ▼
┌──────────────────┐    ┌──────────────────┐
│ Topic            │    │ InterestProfile  │
│ - Name           │    │ - Topics dict    │
│ - Confidence     │    │ - Metadata       │
│ - Raw text       │    │ - Time decay     │
└──────────────────┘    └────────┬─────────┘
                                 │
                                 ▼
                        ┌──────────────────┐
                        │ TopicInterest    │
                        │ - Frequency      │
                        │ - Recency        │
                        │ - Confidence     │
                        │ - Documents      │
                        │ - Co-occurrence  │
                        └──────────────────┘
```

### Data Flow

1. **User queries** → InteractionTracker records
2. **Interaction** → BehaviourLearner.process_interaction()
3. **TopicExtractor** extracts topics from query + documents
4. **ProfileManager** loads existing profile
5. **InterestProfile** updates topic interests
6. **ConfidenceCalculator** recomputes confidence scores
7. **ProfileManager** saves updated profile
8. **(Optional)** KnowledgeGraph updated with relationships

---

## Topic Extraction

### TopicExtractor Algorithm

**3-Phase Extraction Pipeline:**

```python
def extract_topics(query: str) -> List[Topic]:
    topics = []

    # Phase 1: Capitalised terms (acronyms, proper nouns)
    topics.extend(_extract_capitalised_terms(query))

    # Phase 2: Multi-word phrases (2-3 words)
    topics.extend(_extract_phrases(query))

    # Phase 3: Individual keywords
    topics.extend(_extract_keywords(query))

    # Deduplicate, sort, filter by confidence
    return _process_topics(topics)
```

### Phase 1: Capitalised Terms

**Goal:** Extract acronyms and proper nouns (e.g., "RAG", "ChromaDB", "GPT")

**Pattern:** `\b[A-Z]{2,}\b` (2+ consecutive capitals)

**Confidence:** 0.9-0.95 (very high, as acronyms are usually specific)

**Example:**
```python
query = "What are the latest RAG techniques with ChromaDB?"
# Extracts: ["RAG", "ChromaDB"]
# Confidence: 0.90, 0.90
```

### Phase 2: Multi-Word Phrases

**Goal:** Extract meaningful phrases (e.g., "vector databases", "machine learning")

**Approach:**
1. Normalise text (lowercase, remove punctuation)
2. Split into words
3. Extract 2-word phrases (skip if either word is stop word)
4. Extract 3-word phrases (skip if any word is stop word)

**Confidence:**
- 2-word phrases: 0.7-0.85
- 3-word phrases: 0.8-0.9 (higher specificity)

**Formula:**
```python
# 2-word phrases
confidence = min(0.7 + (len(phrase) / 100), 0.85)

# 3-word phrases
confidence = min(0.8 + (len(phrase) / 100), 0.9)
```

**Example:**
```python
query = "How does retrieval augmented generation work?"
# Normalised: "how does retrieval augmented generation work"
# Stop words removed: "how", "does", "work"

# 2-word phrases:
# - "retrieval augmented" (conf: 0.72)
# - "augmented generation" (conf: 0.73)

# 3-word phrases:
# - "retrieval augmented generation" (conf: 0.83)
```

### Phase 3: Individual Keywords

**Goal:** Extract single-word topics after filtering stop words

**Confidence:** 0.5-0.7 (lower than phrases, as less specific)

**Formula:**
```python
confidence = 0.5 + min(len(word) / 20, 0.2)
```

**Example:**
```python
query = "What are the latest RAG techniques?"
# Filtered: ["latest", "RAG", "techniques"]

# Keywords:
# - "latest" (conf: 0.53)
# - "techniques" (conf: 0.55)
```

### Stop Words

**Default Set:** 85 common English words

**Categories:**
- Articles: "a", "an", "the"
- Pronouns: "I", "you", "he", "she", etc.
- Prepositions: "in", "on", "at", "to", etc.
- Conjunctions: "and", "but", "or", etc.
- Auxiliary verbs: "is", "are", "was", "were", etc.
- Question words: "what", "when", "where", etc.
- Low-value verbs: "get", "make", "take", etc.

**Customisation:**
```python
from ragged.memory.topic_config import TopicExtractionConfig

config = TopicExtractionConfig(
    stop_words={"custom", "stop", "words"}
)
```

### Document Topic Extraction

**Goal:** Extract topics from retrieved document filenames

**Approach:**
1. Remove file extensions (`.pdf`, `.md`, `.txt`, `.docx`)
2. Replace separators (`_`, `-`) with spaces
3. Apply same extraction pipeline as queries
4. Reduce confidence by 60% (less reliable than explicit queries)

**Example:**
```python
doc_ids = ["rag_paper_2023.pdf", "vector_db_guide.md"]

# Cleaned:
# - "rag paper 2023"
# - "vector db guide"

# Topics extracted:
# - "rag" (conf: 0.54)  # 0.9 * 0.6
# - "paper" (conf: 0.30)
# - "vector db" (conf: 0.46)  # 0.77 * 0.6
# - "guide" (conf: 0.30)
```

---

## Confidence Calculation

### ConfidenceCalculator Algorithm

**4-Factor Weighted Average:**

```python
confidence = (
    frequency_score * 0.35 +
    recency_score   * 0.30 +
    consistency_score * 0.20 +
    depth_score     * 0.15
)
```

**Weight Rationale:**
- **Frequency (35%)**: Most important - shows sustained interest
- **Recency (30%)**: Crucial for keeping profile current
- **Consistency (20%)**: Distinguishes genuine interest from one-off queries
- **Depth (15%)**: Validates interest through document engagement

### Frequency Score

**Goal:** Measure how often the topic is queried

**Formula:**
```python
def frequency_score(frequency: int) -> float:
    # Logarithmic scale to prevent dominance
    # Normalised to 0.0-1.0
    if frequency == 0:
        return 0.0

    # log₂(frequency + 1) / log₂(max_observed_frequency + 1)
    # Capped at 1.0
    return min(math.log2(frequency + 1) / 10, 1.0)
```

**Examples:**
```
frequency=1  → score=0.10  (queried once)
frequency=5  → score=0.26  (queried 5 times)
frequency=10 → score=0.34  (queried 10 times)
frequency=50 → score=0.58  (queried 50 times)
```

### Recency Score

**Goal:** Prioritise recently queried topics

**Formula:**
```python
def recency_score(last_seen: datetime) -> float:
    days_ago = (datetime.now() - last_seen).days

    # Exponential decay: e^(-0.1 * days)
    # Half-life ≈ 7 days
    return math.exp(-0.1 * days_ago)
```

**Examples:**
```
today      → score=1.00  (just queried)
1 day ago  → score=0.90
7 days ago → score=0.50  (half-life)
30 days ago → score=0.05  (very old)
```

### Consistency Score

**Goal:** Detect regular vs. burst patterns

**Formula:**
```python
def consistency_score(timestamps: List[datetime]) -> float:
    if len(timestamps) < 2:
        return 0.5  # Neutral for single query

    # Calculate time gaps between queries
    gaps = [t2 - t1 for t1, t2 in zip(timestamps[:-1], timestamps[1:])]

    # Standard deviation of gaps (in days)
    std_dev = statistics.stdev([gap.days for gap in gaps])

    # Low std_dev (regular queries) → high score
    # High std_dev (irregular queries) → low score
    return math.exp(-std_dev / 30)  # Normalised to 0-1
```

**Examples:**
```
Queries every 3 days  → score=0.90  (very consistent)
Queries every 7 days  → score=0.78  (consistent)
Irregular (1, 5, 20 days) → score=0.45  (inconsistent)
Single burst (all same day) → score=0.30  (burst pattern)
```

### Depth Score

**Goal:** Validate interest through document engagement

**Formula:**
```python
def depth_score(related_documents: List[str]) -> float:
    doc_count = len(related_documents)

    # Logarithmic scale
    # More documents → higher score
    return min(math.log2(doc_count + 1) / 6, 1.0)
```

**Examples:**
```
1 document   → score=0.17
5 documents  → score=0.43
10 documents → score=0.57
50 documents → score=0.96
```

### Confidence Examples

**Example 1: High Confidence Topic**
```
Topic: "rag"
Frequency: 15 queries
Last seen: 2 hours ago
Consistency: Every 2-3 days
Related docs: 12

Calculation:
- Frequency score: 0.40 (log₂(16)/10)
- Recency score: 0.99 (exp(-0.1 * 0.08))
- Consistency score: 0.88 (regular pattern)
- Depth score: 0.59 (log₂(13)/6)

Confidence: 0.40*0.35 + 0.99*0.30 + 0.88*0.20 + 0.59*0.15
          = 0.14 + 0.30 + 0.18 + 0.09
          = 0.71 (High confidence)
```

**Example 2: Medium Confidence Topic**
```
Topic: "privacy"
Frequency: 4 queries
Last seen: 10 days ago
Consistency: Irregular (burst)
Related docs: 3

Calculation:
- Frequency score: 0.23
- Recency score: 0.37
- Consistency score: 0.40
- Depth score: 0.33

Confidence: 0.23*0.35 + 0.37*0.30 + 0.40*0.20 + 0.33*0.15
          = 0.08 + 0.11 + 0.08 + 0.05
          = 0.32 (Medium-low confidence)
```

---

## Interest Profile Management

### InterestProfile Structure

```python
@dataclass
class InterestProfile:
    persona: str                           # Persona identifier
    topics: Dict[str, TopicInterest]       # Topic name → interest
    created_at: datetime                   # Profile creation time
    updated_at: datetime                   # Last update time
```

### TopicInterest Structure

```python
@dataclass
class TopicInterest:
    topic: str                             # Normalised topic name
    frequency: int                         # Query count
    recency: float                         # Recency score (0-1)
    confidence: float                      # Overall confidence (0-1)
    first_seen: datetime                   # First query timestamp
    last_seen: datetime                    # Most recent query
    related_documents: List[str]           # Document IDs
    co_occurring_topics: Dict[str, int]    # Topic → co-occurrence count
```

### Profile Operations

#### Adding/Updating Topics

```python
def update_topic_interest(
    self,
    topic: Topic,
    doc_ids: Optional[List[str]] = None,
    related_topics: Optional[List[str]] = None
) -> None:
    """Update or create topic interest."""

    topic_name = topic.name.lower().strip()

    if topic_name in self.topics:
        # Update existing topic
        interest = self.topics[topic_name]
        interest.frequency += 1
        interest.last_seen = datetime.now()

        # Add documents
        if doc_ids:
            for doc_id in doc_ids:
                if doc_id not in interest.related_documents:
                    interest.related_documents.append(doc_id)

        # Update co-occurrence
        if related_topics:
            for related in related_topics:
                if related != topic_name:
                    interest.co_occurring_topics[related] = (
                        interest.co_occurring_topics.get(related, 0) + 1
                    )
    else:
        # Create new topic
        self.topics[topic_name] = TopicInterest(
            topic=topic_name,
            frequency=1,
            recency=1.0,
            confidence=topic.confidence,
            first_seen=datetime.now(),
            last_seen=datetime.now(),
            related_documents=doc_ids or [],
            co_occurring_topics={
                t: 1 for t in (related_topics or []) if t != topic_name
            }
        )
```

#### Time Decay

**Goal:** Gradually reduce recency scores for old topics

```python
def apply_time_decay(
    self,
    decay_rate: float = 0.1,
    decay_days: int = 30
) -> None:
    """Apply exponential decay to topic recency."""

    now = datetime.now()

    for interest in self.topics.values():
        days_ago = (now - interest.last_seen).days

        if days_ago > decay_days:
            # Apply decay for topics older than threshold
            periods = (days_ago - decay_days) / decay_days
            interest.recency *= math.exp(-decay_rate * periods)
```

**Effect:**
- Topics queried within 30 days: No decay
- Topics older than 30 days: Gradual decay
- Decay rate: 0.1 (configurable)

**Example:**
```
Topic last seen 60 days ago (1 period past threshold):
recency = 1.0 * exp(-0.1 * 1) = 0.90

Topic last seen 120 days ago (3 periods past threshold):
recency = 1.0 * exp(-0.1 * 3) = 0.74
```

---

## Integration Patterns

### Pattern 1: Automatic Integration with InteractionTracker

**Use Case:** Automatic profile building from query interactions

```python
from ragged.memory.behaviour import create_behaviour_learner
from ragged.memory.interactions import InteractionTracker

# Create behaviour learner
learner = create_behaviour_learner(
    storage_dir=Path("~/.ragged/memory"),
    enable_graph=False  # Optional knowledge graph
)

# Create tracker with learner
tracker = InteractionTracker(
    persona="researcher",
    behaviour_learner=learner  # Automatic processing
)

# Record interaction (profile automatically updated)
interaction = tracker.record_interaction(
    query="What is RAG?",
    response="Retrieval-Augmented Generation...",
    retrieved_doc_ids=["rag_paper.pdf"],
    model_used="llama3"
)
```

**How It Works:**
1. `record_interaction()` saves interaction to database
2. Calls `learner.process_interaction(interaction)` automatically
3. Profile updated in real-time
4. Failures don't prevent interaction recording (graceful degradation)

### Pattern 2: Manual Batch Processing

**Use Case:** Processing historical interactions or batch imports

```python
from ragged.memory.behaviour import BehaviourLearner
from ragged.memory.interactions import Interaction
from ragged.memory.profile import ProfileManager

# Setup
manager = ProfileManager(Path("profiles.db"))
learner = BehaviourLearner(manager)

# Load historical interactions
interactions = [
    Interaction(persona="researcher", query="What is RAG?"),
    Interaction(persona="researcher", query="Vector databases"),
    # ... more interactions
]

# Batch process
learner.process_batch(interactions)

# Get insights
insights = learner.get_persona_insights("researcher")
print(f"Processed {insights['total_topics']} topics")
```

### Pattern 3: Custom Topic Extraction

**Use Case:** Custom topic extraction logic or filters

```python
from ragged.memory.topics import TopicExtractor, Topic
from ragged.memory.topic_config import TopicExtractionConfig

# Custom configuration
config = TopicExtractionConfig(
    min_topic_length=4,           # Longer topics only
    max_topics_per_query=15,      # More topics
    confidence_threshold=0.4,     # Higher threshold
    stop_words=custom_stop_words,  # Domain-specific stop words
    enable_phrases=True            # Enable phrase extraction
)

# Create extractor
extractor = TopicExtractor(
    min_topic_length=config.min_topic_length,
    max_topics_per_query=config.max_topics_per_query,
    min_confidence=config.confidence_threshold,
    stop_words=config.stop_words,
    enable_phrases=config.enable_phrases
)

# Extract topics
topics = extractor.extract_topics("Your custom query here")

# Post-process (e.g., filter domain-specific topics)
filtered_topics = [
    t for t in topics
    if is_relevant_to_domain(t.name)
]
```

### Pattern 4: GDPR Compliance

**Use Case:** Implementing user data rights

```python
# Right to Access (Article 15)
profile_json = learner.export_profile("researcher")
send_to_user(profile_json)

# Right to Erasure (Article 17)
# Remove specific topic
learner.forget_topic("researcher", "sensitive-topic")

# Remove entire profile
learner.reset_profile("researcher")

# Right to Data Portability (Article 20)
profile_data = learner.export_profile("researcher")
save_portable_format(profile_data)
```

---

## Configuration

### TopicExtractionConfig

**File:** `~/.ragged/config/topic_extraction.yaml`

```yaml
# Topic extraction configuration
min_topic_length: 3           # Minimum characters for valid topic
max_topics_per_query: 10      # Maximum topics per query
confidence_threshold: 0.3     # Minimum confidence to track
enable_phrases: true          # Enable multi-word phrase extraction

# Custom stop words (extends default set)
stop_words:
  - "custom"
  - "domain"
  - "specific"
```

**Loading Configuration:**

```python
from ragged.memory.topic_config import TopicExtractionConfig

# From YAML
config = TopicExtractionConfig.from_yaml("config.yaml")

# From dict
config = TopicExtractionConfig.from_dict({
    "min_topic_length": 4,
    "confidence_threshold": 0.5
})

# Programmatic
config = TopicExtractionConfig(
    min_topic_length=3,
    max_topics_per_query=15,
    confidence_threshold=0.4
)
```

### ConfidenceCalculator Weights

**Customising Confidence Calculation:**

```python
from ragged.memory.confidence import ConfidenceCalculator

# Custom weights (must sum to 1.0)
calculator = ConfidenceCalculator(
    frequency_weight=0.40,   # Emphasise frequency
    recency_weight=0.35,     # Emphasise recency
    consistency_weight=0.15,  # De-emphasise consistency
    depth_weight=0.10        # De-emphasise depth
)

# Use in learner
learner = BehaviourLearner(
    profile_manager=manager,
    confidence_calculator=calculator
)
```

---

## Performance Considerations

### Extraction Performance

**Metrics (typical query, ~20 words):**
- Topic extraction: ~1-2ms
- Profile update: ~5-10ms
- Database save: ~10-20ms
- **Total overhead: ~15-30ms per interaction**

**Optimisations:**
- Regex compilation cached
- Stop word set lookups O(1)
- Database uses WAL mode (2-3x faster writes)
- Batch processing for imports

### Storage Efficiency

**Profile Storage:**
- SQLite database with JSON serialisation
- Typical profile (100 topics): ~50-100 KB
- Compression not needed (minimal overhead)

**Indexes:**
- Primary key: persona (unique)
- Secondary index: updated_at (for cleanup)

### Memory Usage

**Peak Memory (typical):**
- Topic extraction: ~1-5 MB
- Profile in memory: ~0.5-1 MB per persona
- Total overhead: < 10 MB for single-persona usage

### Scaling Considerations

**Current Limits:**
- Designed for single-user workloads
- Tested with up to 1000 topics per persona
- Up to 100 personas per installation

**For High-Volume Usage:**
- Consider periodic profile cleanup (remove low-confidence topics)
- Archive old interactions
- Use time decay to naturally reduce topic count

---

## Extension Points

### Custom Topic Extractors

**Interface:**

```python
class CustomTopicExtractor:
    """Custom topic extractor using NLP/LLM."""

    def extract_topics(self, query: str) -> List[Topic]:
        """Extract topics from query.

        Must return list of Topic objects with:
        - name: topic string
        - confidence: 0.0-1.0
        - raw_text: original text
        """
        # Your custom logic here
        pass

    def extract_from_documents(
        self,
        doc_ids: List[str],
        doc_texts: Optional[List[str]] = None
    ) -> List[Topic]:
        """Extract topics from documents."""
        # Your custom logic here
        pass
```

**Usage:**

```python
# Create custom extractor
custom_extractor = CustomTopicExtractor()

# Replace in behaviour learner
learner.extractor = custom_extractor

# Process as normal
learner.process_interaction(interaction)
```

### Custom Confidence Calculators

**Interface:**

```python
class CustomConfidenceCalculator:
    """Custom confidence calculation logic."""

    def calculate_confidence(
        self,
        frequency: int,
        last_seen: datetime,
        first_seen: datetime,
        related_documents: List[str],
        timestamps: Optional[List[datetime]] = None
    ) -> float:
        """Calculate confidence score (0.0-1.0)."""
        # Your custom logic here
        pass
```

### Knowledge Graph Integration

**Current Support:** Optional (v0.4.7)

**Future Enhancement:** v0.5.x will add:
- Topic clustering
- Semantic relationships
- Cross-persona insights
- Visual exploration

**Enable Graph:**

```python
learner = create_behaviour_learner(
    storage_dir=Path("~/.ragged/memory"),
    enable_graph=True  # Creates Kuzu graph database
)
```

---

## Testing & Debugging

### Unit Testing

**Test Topic Extraction:**

```python
from ragged.memory.topics import TopicExtractor

def test_extraction():
    extractor = TopicExtractor()
    topics = extractor.extract_topics("What is RAG?")

    assert "rag" in [t.name.lower() for t in topics]
    assert all(0.0 <= t.confidence <= 1.0 for t in topics)
```

**Test Confidence Calculation:**

```python
from ragged.memory.confidence import ConfidenceCalculator
from datetime import datetime, timedelta

def test_confidence():
    calc = ConfidenceCalculator()

    # High confidence scenario
    conf = calc.calculate_confidence(
        frequency=15,
        last_seen=datetime.now(),
        first_seen=datetime.now() - timedelta(days=30),
        related_documents=["doc1", "doc2", "doc3"],
        timestamps=[datetime.now() - timedelta(days=i) for i in range(15)]
    )

    assert conf > 0.7  # Should be high confidence
```

### Integration Testing

**Test Full Pipeline:**

```python
from ragged.memory.behaviour import create_behaviour_learner
from ragged.memory.interactions import Interaction

def test_full_pipeline(tmp_path):
    learner = create_behaviour_learner(tmp_path)

    # Process interaction
    interaction = Interaction(
        persona="test-user",
        query="What is RAG?",
        retrieved_doc_ids=["doc1.pdf"]
    )

    profile = learner.process_interaction(interaction)

    assert len(profile.topics) > 0
    assert "rag" in profile.topics
```

### Debugging Tips

**Enable Debug Logging:**

```python
import logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("ragged.memory")
logger.setLevel(logging.DEBUG)
```

**Inspect Extraction:**

```python
topics = extractor.extract_topics(query)
for topic in topics:
    print(f"{topic.name}: {topic.confidence:.3f}")
```

**Profile Inspection:**

```python
profile = manager.get_profile("persona")
for name, interest in profile.topics.items():
    print(f"{name}: freq={interest.frequency}, conf={interest.confidence:.3f}")
```

---

## Future Roadmap

### v0.5.x: NLP Enhancement

**Planned Features:**
- spaCy integration for named entity recognition (NER)
- Transformer-based topic modeling
- Semantic similarity clustering
- Multi-language support

**Benefits:**
- More accurate topic extraction
- Better handling of synonyms
- Domain-specific entity recognition

### v0.6.x: Personalised Retrieval

**Planned Features:**
- Profile-aware document ranking
- Query expansion based on interests
- Contextual query understanding
- Adaptive retrieval strategies

**Example:**
```python
# Query: "latest techniques"
# Without profile: Generic results
# With profile (RAG-focused): Latest RAG techniques prioritised
```

### v0.7.x: Collaborative Learning

**Planned Features:**
- Federated learning (privacy-preserving)
- Community topic trends
- Cross-persona insights (opt-in)

---

## Related Documentation

- [Understanding Your Interest Profile Tutorial](../tutorials/understanding-your-interest-profile.md) - User-focused guide
- [Behaviour Learning API Reference](../reference/behaviour-learning-api.md) - Complete API documentation
<!-- TODO v0.4.8+: Add Memory Management Guide -->
<!-- TODO v0.4.8+: Add Privacy Features Guide -->

---
