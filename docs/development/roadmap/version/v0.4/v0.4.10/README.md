# v0.4.10 - Temporal Memory System

**Hours**: 37-45 | **Priority**: P0 - Advanced Feature | **Status**: Planned

**Dependencies**: v0.4.9 complete (Refactored codebase)

---

## Overview

Implement comprehensive time-aware memory system enabling temporal fact storage, timeline queries, historical activity tracking, and time-based reasoning.

**Vision**: Ragged understands that information changes over time and can answer "what was I working on last week?" or "when did I first learn about RAG?"

**Theoretical Foundation**: Extends [Context Engineering 2.0](../../../../acknowledgements/context-engineering-2.0.md) **structured context layering** with a temporal dimension. Temporal knowledge graphs make time-based relationships explicit (when facts were valid, when topics were accessed, activity timelines), further reducing uncertainty through time-aware context organisation.

**Multi-File Organisation**: Due to complexity and scope (37-45h), this release is organised across multiple supporting files for maintainability.

---

## Core Deliverables

### 1. Temporal Fact Storage (8-10h)

Support facts that change over time with versioning and validity periods.

**Examples**:
- "I work at Company X" (valid-from: 2026-01-01, valid-to: present)
- "I used to work at Company Y" (valid-from: 2024-06-01, valid-to: 2025-12-31)
- "I'm learning Rust" (valid-from: 2026-02-01, valid-to: present)

#### Temporal Fact Schema

```python
@dataclass
class TemporalFact:
    """Fact with temporal validity."""
    id: str
    persona: str
    fact_type: str  # e.g., "employment", "learning", "location"
    content: str
    valid_from: datetime
    valid_to: Optional[datetime]  # None = current
    confidence: float
    source: str  # How fact was learned
    metadata: Dict[str, Any]

@dataclass
class FactVersion:
    """Version of a fact (for tracking changes)."""
    fact_id: str
    version: int
    content: str
    valid_from: datetime
    valid_to: datetime
    updated_at: datetime
    update_reason: str
```

#### Features

**Validity Tracking**:
- Valid-from/valid-to timestamps
- Current facts (valid_to = None)
- Historical facts (valid_to set)
- Overlapping validity detection

**Fact Versioning**:
- Track fact changes over time
- Version history
- Rollback capability
- Update reasoning

**Temporal Queries**:
```python
# Get facts valid at specific time
facts = temporal_store.get_facts_at(persona, datetime(2025, 6, 1))

# Get current facts
current_facts = temporal_store.get_current_facts(persona)

# Get fact history
history = temporal_store.get_fact_history(fact_id)
```

**See**: [temporal-facts.md](./temporal-facts.md) for complete implementation details

**Files**:
- `ragged/memory/temporal_facts.py` (~350 lines)
- `ragged/memory/fact_versioning.py` (~200 lines)
- `tests/memory/test_temporal_facts.py` (~250 lines)

---

### 2. Timeline Query Engine (12-15h)

Support sophisticated time-based queries and activity tracking.

#### Query Types Supported

**Activity Timeline**:
```bash
# What was I working on last week?
ragged memory timeline --since "-7d" --until "now" --persona researcher

# Show my activity for January
ragged memory timeline --period "2026-01" --persona researcher
```

**Topic Evolution**:
```bash
# When did I first query about RAG?
ragged memory first-seen --topic "RAG" --persona researcher

# Show evolution of interest in "privacy"
ragged memory topic-evolution "privacy" --persona researcher
```

**Trending Topics**:
```bash
# What topics interested me in the last 30 days?
ragged memory trending --window "30d" --persona researcher

# Compare topic interest: this month vs last month
ragged memory trending-compare --period-a "this-month" --period-b "last-month"
```

#### Timeline Engine Implementation

```python
class TemporalQueryEngine:
    """Engine for time-based queries."""

    def get_timeline(
        self,
        persona: str,
        since: datetime,
        until: datetime,
        granularity: str = "day"
    ) -> Timeline:
        """Get activity timeline for period.

        Args:
            persona: Persona name
            since: Start time
            until: End time
            granularity: "hour", "day", "week", "month"

        Returns:
            Timeline with aggregated activity
        """
        pass

    def get_activity_summary(
        self,
        persona: str,
        period: str
    ) -> ActivitySummary:
        """Get activity summary for period.

        Args:
            persona: Persona name
            period: "today", "yesterday", "this-week", "last-month", etc.

        Returns:
            Summary of activity
        """
        pass

    def find_first_occurrence(
        self,
        persona: str,
        topic: str
    ) -> Optional[datetime]:
        """Find when topic was first seen.

        Args:
            persona: Persona name
            topic: Topic to find

        Returns:
            First occurrence timestamp or None
        """
        pass

    def get_trending_topics(
        self,
        persona: str,
        window: str = "30d"
    ) -> List[TrendingTopic]:
        """Get trending topics for window.

        Args:
            persona: Persona name
            window: Time window ("7d", "30d", "90d")

        Returns:
            Topics sorted by trend score
        """
        pass

    def compare_periods(
        self,
        persona: str,
        period_a: str,
        period_b: str
    ) -> PeriodComparison:
        """Compare activity between two periods.

        Args:
            persona: Persona name
            period_a: First period
            period_b: Second period

        Returns:
            Comparison with changes
        """
        pass
```

**See**: [timeline-engine.md](./timeline-engine.md) for complete implementation details

**Files**:
- `ragged/memory/temporal_query.py` (~500 lines)
- `ragged/memory/timeline.py` (~300 lines)
- `ragged/memory/trending.py` (~250 lines)
- `tests/memory/test_temporal_query.py` (~350 lines)

---

### 3. Temporal Reasoning (10-12h)

Understand temporal context in queries and apply time-aware logic.

#### Time Expression Parsing

**Natural Language Time Expressions**:
- "last week" → datetime range
- "-30d" → 30 days ago
- "January" → 2026-01-01 to 2026-01-31
- "Q4 2025" → 2025-10-01 to 2025-12-31
- "this morning" → today 00:00 to 12:00

**Relative Time**:
- "yesterday", "today", "tomorrow"
- "this week", "last month", "next year"
- "3 days ago", "2 weeks from now"

**Absolute Time**:
- "2026-01-15"
- "March 2025"
- "Q3 2024"

#### Temporal Context Enhancement

```python
class TemporalReasoner:
    """Apply temporal reasoning to queries."""

    def enhance_query_with_time(
        self,
        query: str,
        persona: str
    ) -> EnhancedQuery:
        """Add temporal context to query.

        Examples:
        - "my recent work" → Focus on last 30d
        - "when I was at Company X" → Filter by employment period
        - "my old notes on Python" → Emphasise older content
        """
        pass

    def apply_temporal_filter(
        self,
        results: List[Document],
        time_context: TimeContext
    ) -> List[Document]:
        """Filter results by temporal context."""
        pass

    def calculate_recency_score(
        self,
        document: Document,
        query_time: datetime
    ) -> float:
        """Calculate recency relevance score."""
        pass
```

#### Time-Aware Relevance Scoring

**Recency Weighting**:
- Recent documents boosted for current queries
- Historical documents boosted for historical queries
- Configurable decay curves

**Temporal Fact Validation**:
- Check fact validity at query time
- Don't use facts that were valid in past but not now
- Historical queries use facts valid at that time

**See**: [temporal-reasoning.md](./temporal-reasoning.md) for complete implementation details

**Files**:
- `ragged/memory/temporal_reasoning.py` (~400 lines)
- `ragged/memory/time_parser.py` (~250 lines)
- `tests/memory/test_temporal_reasoning.py` (~300 lines)

---

### 4. CLI Temporal Commands (6-8h)

Comprehensive command-line interface for temporal queries.

```bash
# ========================================
# Timeline Queries
# ========================================

# Activity timeline
ragged memory timeline --since "-30d" --until "now" --persona researcher
ragged memory timeline --period "2026-01" --granularity day
ragged memory timeline --period "last-week" --format json

# Activity summary
ragged memory activity --period "today" --persona researcher
ragged memory activity --period "last-week" --detailed
ragged memory activity --period "Q4-2025" --export summary.json

# ========================================
# Topic Queries
# ========================================

# Topic trends
ragged memory trending --window "30d" --persona researcher
ragged memory trending --window "90d" --min-queries 5

# Topic evolution
ragged memory topic-evolution "RAG" --persona researcher
ragged memory topic-evolution "privacy" --since "2025-01-01"

# First occurrence
ragged memory first-seen --topic "RAG" --persona researcher
ragged memory first-seen --topic "machine learning"

# ========================================
# Comparisons
# ========================================

# Compare periods
ragged memory compare-periods \
  --period-a "this-month" \
  --period-b "last-month" \
  --persona researcher

# Compare topic interest over time
ragged memory compare-topics \
  --topics "RAG,privacy,NLP" \
  --window "90d"

# ========================================
# Temporal Facts
# ========================================

# Add temporal fact
ragged memory add-fact \
  --type "employment" \
  --content "Working at Company X" \
  --since "2026-01-01" \
  --persona researcher

# Update fact (end validity)
ragged memory update-fact <fact-id> --until "2026-12-31"

# View facts at specific time
ragged memory facts --at "2025-06-01" --persona researcher

# View current facts
ragged memory facts --current --persona researcher

# View fact history
ragged memory fact-history <fact-id>
```

**Output Examples**: See [cli-examples.md](./cli-examples.md)

**Files**:
- `ragged/cli/commands/timeline.py` (~300 lines)
- `ragged/cli/commands/temporal.py` (~250 lines)
- `ragged/cli/formatters/timeline.py` (~150 lines)
- `tests/cli/test_temporal_commands.py` (~300 lines)

---

### 5. Visualisations (3-5h)

Visual representations of temporal data.

**Timeline Visualisation**:
```bash
$ ragged memory timeline --period "last-week" --visual

Activity Timeline: researcher (2026-03-08 to 2026-03-15)

Mon 03/08  ████████░░  8 queries   Topics: RAG, privacy
Tue 03/09  ██████████  12 queries  Topics: RAG, vector search, embeddings
Wed 03/10  ████░░░░░░  4 queries   Topics: privacy, security
Thu 03/11  ██████░░░░  6 queries   Topics: RAG, NLP
Fri 03/12  ████████░░  10 queries  Topics: machine learning, RAG
Sat 03/13  ██░░░░░░░░  2 queries   Topics: privacy
Sun 03/14  ░░░░░░░░░░  0 queries   -

Total: 42 queries | Avg: 6/day | Peak: Tue 12 queries
```

**Topic Trend Graph**:
```bash
$ ragged memory topic-evolution "RAG" --visual

Topic Evolution: RAG (last 90 days)

Queries per week:
Week 1   ██░░░░░░░░  2
Week 2   ████░░░░░░  4
Week 3   ████░░░░░░  4
Week 4   ██████░░░░  6
Week 5   ████████░░  8
Week 6   ██████████  10  ← Peak
Week 7   ████████░░  8
Week 8   ██████████  10
Week 9   ████████░░  9
Week 10  ██████████  11
Week 11  ██████████  12  ← Trending up
Week 12  ██████████  10
Week 13  ████████░░  8

Trend: ↑ Growing interest (confidence: 0.87)
First seen: 2025-12-15
Total queries: 102
```

**Files**:
- `ragged/cli/visualisations/timeline.py` (~200 lines)
- `ragged/cli/visualisations/trends.py` (~150 lines)

---

### 6. Testing & Validation (6-8h)

Comprehensive temporal logic testing.

**Test Coverage**:

1. **Temporal Fact Tests**:
   - ✅ Fact validity tracking
   - ✅ Fact versioning
   - ✅ Overlapping facts handled
   - ✅ Current vs historical facts

2. **Timeline Tests**:
   - ✅ Time range queries accurate
   - ✅ Activity aggregation correct
   - ✅ Granularity handling (hour/day/week/month)
   - ✅ Period comparisons accurate

3. **Temporal Reasoning Tests**:
   - ✅ Time expression parsing
   - ✅ Relative time calculation
   - ✅ Timezone handling
   - ✅ DST transitions handled
   - ✅ Edge cases (leap years, month boundaries)

4. **Integration Tests**:
   - ✅ End-to-end timeline queries
   - ✅ Temporal filtering in retrieval
   - ✅ Fact-based query enhancement
   - ✅ Multi-persona temporal isolation

**Test Files** (~1,200 lines):
- `tests/memory/test_temporal_facts.py` (~250 lines)
- `tests/memory/test_temporal_query.py` (~350 lines)
- `tests/memory/test_temporal_reasoning.py` (~300 lines)
- `tests/cli/test_temporal_commands.py` (~300 lines)

---

## Testing Requirements

**Coverage**: ≥85% for temporal modules

**Critical Test Scenarios**:

1. **Timezone Handling**:
   - ✅ All times stored in UTC
   - ✅ Display in user's timezone
   - ✅ DST transitions handled correctly
   - ✅ International date line handling

2. **Edge Cases**:
   - ✅ Leap years
   - ✅ Month/year boundaries
   - ✅ Empty time ranges
   - ✅ Future dates
   - ✅ Very old dates (>100 years ago)

3. **Performance**:
   - ✅ Large date ranges (<1s)
   - ✅ Many temporal facts (<500ms)
   - ✅ Complex timeline aggregations (<2s)

---

## Documentation

**Required** (~2,000 lines):

1. **Tutorial**: Time-Aware Memory (~500 lines)
   - Understanding temporal facts
   - Querying timelines
   - Topic evolution tracking
   - Practical examples

2. **Guide**: Temporal Memory System (~800 lines)
   - Architecture overview
   - Temporal fact storage
   - Timeline queries
   - Temporal reasoning
   - Time expression syntax
   - Timezone handling
   - Best practices

3. **Reference**: Temporal API Documentation (~500 lines)
   - TemporalFact schema
   - TemporalQueryEngine API
   - TemporalReasoner API
   - CLI command reference

4. **Examples**: Temporal Query Patterns (~200 lines)
   - Common timeline queries
   - Trend analysis examples
   - Temporal fact management
   - Activity tracking patterns

**See**: [documentation-plan.md](./documentation-plan.md) for complete documentation structure

---

## Success Criteria

Version 0.4.10 is successful if:

1. ✅ Temporal fact storage works correctly
2. ✅ Fact versioning tracks changes accurately
3. ✅ Timeline queries produce accurate results
4. ✅ Time expression parsing handles natural language
5. ✅ Temporal reasoning enhances query relevance
6. ✅ Timezone handling correct (including DST)
7. ✅ Activity summaries accurate and insightful
8. ✅ Trending topics detection meaningful
9. ✅ CLI commands intuitive and functional
10. ✅ Visualisations clear and helpful
11. ✅ Performance targets met (see below)
12. ✅ 85%+ test coverage
13. ✅ Documentation complete
14. ✅ No edge case bugs (leap years, DST, etc.)

---

## Performance Targets

- Timeline query (30d): <500ms
- Timeline query (1y): <2s
- Temporal fact lookup: <200ms
- Activity summary: <1s
- Trending topics (90d): <800ms
- First occurrence lookup: <300ms
- Time expression parsing: <10ms
- Fact versioning query: <200ms

---

## File Summary

**New Files** (~4,650 lines):
- Temporal core: ~1,950 lines
- CLI: ~700 lines
- Tests: ~1,200 lines
- Documentation: ~2,000 lines
- Visualisations: ~350 lines

**Supporting Documentation**:
- [temporal-facts.md](./temporal-facts.md) - Temporal fact storage details
- [timeline-engine.md](./timeline-engine.md) - Timeline query engine details
- [temporal-reasoning.md](./temporal-reasoning.md) - Temporal reasoning details
- [cli-examples.md](./cli-examples.md) - CLI command examples
- [documentation-plan.md](./documentation-plan.md) - Documentation structure

**Dependencies**:
- `python-dateutil>=2.8` - Temporal operations
- `pytz>=2023.3` - Timezone handling
- No other new dependencies

---

## Storage Schema Extensions

**SQLite Temporal Facts Table**:
```sql
CREATE TABLE temporal_facts (
    id TEXT PRIMARY KEY,
    persona TEXT NOT NULL,
    fact_type TEXT NOT NULL,
    content TEXT NOT NULL,
    valid_from TIMESTAMP NOT NULL,
    valid_to TIMESTAMP,
    confidence REAL,
    source TEXT,
    metadata TEXT,  -- JSON
    created_at TIMESTAMP,
    FOREIGN KEY (persona) REFERENCES personas(name)
);

CREATE INDEX idx_temporal_facts_validity
ON temporal_facts(persona, valid_from, valid_to);

CREATE TABLE fact_versions (
    fact_id TEXT NOT NULL,
    version INTEGER NOT NULL,
    content TEXT NOT NULL,
    valid_from TIMESTAMP NOT NULL,
    valid_to TIMESTAMP,
    updated_at TIMESTAMP,
    update_reason TEXT,
    PRIMARY KEY (fact_id, version),
    FOREIGN KEY (fact_id) REFERENCES temporal_facts(id)
);
```

**Kuzu Graph Extensions**:
```cypher
// Add temporal properties to relationships
ALTER REL TABLE INTERESTED_IN ADD first_seen TIMESTAMP;
ALTER REL TABLE INTERESTED_IN ADD last_seen TIMESTAMP;
ALTER REL TABLE ACCESSED ADD access_timestamps TIMESTAMP[];
```

---

## Risk Assessment

**Medium Risk**:
- Timezone handling complexity → Mitigation: Comprehensive testing, use established libraries
- Performance with large date ranges → Mitigation: Database indexing, query optimisation
- Time expression parsing ambiguity → Mitigation: Clear syntax, validation

**Low Risk**:
- SQLite temporal queries (well-established patterns)
- Fact versioning (simple table structure)
- Timeline aggregation (standard algorithms)

---

## Configuration

**Temporal System Config** (`~/.ragged/config/memory.yaml`):
```yaml
temporal_memory:
  enabled: true

  timezone:
    user_timezone: "auto"  # Auto-detect or specify (e.g., "Europe/London")
    storage_timezone: "UTC"  # Always UTC

  timeline:
    default_window: "30d"
    max_window: "5y"
    default_granularity: "day"

  facts:
    auto_expire_enabled: false
    default_confidence: 0.7

  trending:
    min_queries_for_trend: 3
    trend_calculation_method: "exponential_moving_average"

  performance:
    cache_timelines: true
    cache_ttl_minutes: 30
```

---

## Integration with Existing Features

**Memory Foundation** (v0.4.5):
- Temporal facts stored in same database
- Persona isolation maintained
- Privacy controls apply

**Behaviour Learning** (v0.4.7, v0.4.8):
- Timeline queries use interaction history
- Trending topics based on learned interests
- Temporal context enhances personalisation

**Knowledge Graph** (v0.4.5):
- Temporal relationships in graph
- Time-aware graph queries
- Historical graph snapshots

---

## Related Documentation

- [v0.4 Overview](../README.md) - Release series overview
- [v0.4 Detailed Spec](../v0.4-DETAILED-SPEC.md) - Part 2: Milestone 3
- [v0.4.9](../v0.4.9.md) - Refactoring (previous)
- [v0.4.11](../v0.4.11.md) - Backend migration tools (next)
- [v0.4.5 README](../v0.4.5/README.md) - Memory foundation

---

## Supporting Files

This release includes supporting documentation files in this directory:

1. **[temporal-facts.md](./temporal-facts.md)** - Temporal fact storage implementation details
2. **[timeline-engine.md](./timeline-engine.md)** - Timeline query engine implementation
3. **[temporal-reasoning.md](./temporal-reasoning.md)** - Temporal reasoning implementation
4. **[cli-examples.md](./cli-examples.md)** - Comprehensive CLI examples
5. **[documentation-plan.md](./documentation-plan.md)** - Documentation structure and plan

---
