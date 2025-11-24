"""Tests for temporal fact storage and management."""

import pytest
from datetime import datetime, timedelta, timezone
import tempfile
from pathlib import Path

from ragged.memory.temporal_facts import (
    TemporalFact,
    FactVersion,
    TemporalFactStore
)


@pytest.fixture
def temp_db():
    """Create temporary database for testing."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name
    yield db_path
    Path(db_path).unlink(missing_ok=True)


@pytest.fixture
def fact_store(temp_db):
    """Create fact store with temporary database."""
    return TemporalFactStore(db_path=temp_db)


@pytest.fixture
def sample_fact():
    """Create sample temporal fact."""
    return TemporalFact(
        id="fact_001",
        persona="researcher",
        fact_type="employment",
        content="Works at Company X",
        valid_from=datetime(2024, 1, 1, tzinfo=timezone.utc),
        valid_to=None,  # Current
        confidence=0.95,
        source="manual"
    )


class TestTemporalFact:
    """Tests for TemporalFact dataclass."""

    def test_is_valid_at_current(self, sample_fact):
        """Test validity check for current facts."""
        now = datetime.now(timezone.utc)
        assert sample_fact.is_valid_at(now)

    def test_is_valid_at_past(self, sample_fact):
        """Test validity check for past dates."""
        past = datetime(2023, 1, 1, tzinfo=timezone.utc)
        assert not sample_fact.is_valid_at(past)

    def test_is_valid_at_historical(self):
        """Test validity check for historical facts."""
        fact = TemporalFact(
            id="hist_001",
            persona="researcher",
            fact_type="employment",
            content="Worked at Company Y",
            valid_from=datetime(2022, 1, 1, tzinfo=timezone.utc),
            valid_to=datetime(2023, 12, 31, tzinfo=timezone.utc),
            confidence=1.0,
            source="manual"
        )

        # Should be valid during period
        during = datetime(2023, 6, 1, tzinfo=timezone.utc)
        assert fact.is_valid_at(during)

        # Should not be valid after period
        after = datetime(2024, 6, 1, tzinfo=timezone.utc)
        assert not fact.is_valid_at(after)

    def test_is_current(self, sample_fact):
        """Test current fact detection."""
        assert sample_fact.is_current()

        historical = TemporalFact(
            id="hist_001",
            persona="researcher",
            fact_type="employment",
            content="Worked at Company Y",
            valid_from=datetime(2022, 1, 1, tzinfo=timezone.utc),
            valid_to=datetime(2023, 12, 31, tzinfo=timezone.utc),
            confidence=1.0
        )
        assert not historical.is_current()

    def test_overlaps_with(self):
        """Test overlap detection."""
        fact1 = TemporalFact(
            id="f1",
            persona="researcher",
            fact_type="employment",
            content="Company A",
            valid_from=datetime(2022, 1, 1, tzinfo=timezone.utc),
            valid_to=datetime(2023, 12, 31, tzinfo=timezone.utc)
        )

        fact2 = TemporalFact(
            id="f2",
            persona="researcher",
            fact_type="employment",
            content="Company B",
            valid_from=datetime(2023, 6, 1, tzinfo=timezone.utc),
            valid_to=datetime(2024, 12, 31, tzinfo=timezone.utc)
        )

        assert fact1.overlaps_with(fact2)
        assert fact2.overlaps_with(fact1)

    def test_no_overlap(self):
        """Test non-overlapping facts."""
        fact1 = TemporalFact(
            id="f1",
            persona="researcher",
            fact_type="employment",
            content="Company A",
            valid_from=datetime(2022, 1, 1, tzinfo=timezone.utc),
            valid_to=datetime(2023, 12, 31, tzinfo=timezone.utc)
        )

        fact2 = TemporalFact(
            id="f2",
            persona="researcher",
            fact_type="employment",
            content="Company B",
            valid_from=datetime(2024, 1, 1, tzinfo=timezone.utc),
            valid_to=None
        )

        assert not fact1.overlaps_with(fact2)
        assert not fact2.overlaps_with(fact1)


class TestTemporalFactStore:
    """Tests for TemporalFactStore."""

    def test_initialization(self, fact_store):
        """Test store initialization."""
        assert fact_store is not None

    def test_add_fact(self, fact_store, sample_fact):
        """Test adding a fact."""
        fact_store.add_fact(sample_fact)

        retrieved = fact_store.get_fact(sample_fact.id)
        assert retrieved is not None
        assert retrieved.id == sample_fact.id
        assert retrieved.content == sample_fact.content

    def test_add_duplicate_fact_raises_error(self, fact_store, sample_fact):
        """Test adding duplicate fact raises error."""
        fact_store.add_fact(sample_fact)

        with pytest.raises(ValueError, match="already exists"):
            fact_store.add_fact(sample_fact)

    def test_get_nonexistent_fact(self, fact_store):
        """Test getting nonexistent fact returns None."""
        fact = fact_store.get_fact("nonexistent")
        assert fact is None

    def test_get_current_facts(self, fact_store):
        """Test getting current facts."""
        # Add current fact
        current = TemporalFact(
            id="current_001",
            persona="researcher",
            fact_type="employment",
            content="Current job",
            valid_from=datetime(2024, 1, 1, tzinfo=timezone.utc),
            valid_to=None
        )
        fact_store.add_fact(current)

        # Add historical fact
        historical = TemporalFact(
            id="hist_001",
            persona="researcher",
            fact_type="employment",
            content="Old job",
            valid_from=datetime(2022, 1, 1, tzinfo=timezone.utc),
            valid_to=datetime(2023, 12, 31, tzinfo=timezone.utc)
        )
        fact_store.add_fact(historical)

        # Get current facts
        current_facts = fact_store.get_current_facts("researcher")

        assert len(current_facts) == 1
        assert current_facts[0].id == "current_001"

    def test_get_facts_at_timestamp(self, fact_store):
        """Test getting facts valid at specific time."""
        # Add facts with different validity periods
        fact1 = TemporalFact(
            id="f1",
            persona="researcher",
            fact_type="employment",
            content="Job 1",
            valid_from=datetime(2022, 1, 1, tzinfo=timezone.utc),
            valid_to=datetime(2023, 6, 30, tzinfo=timezone.utc)
        )
        fact2 = TemporalFact(
            id="f2",
            persona="researcher",
            fact_type="employment",
            content="Job 2",
            valid_from=datetime(2023, 7, 1, tzinfo=timezone.utc),
            valid_to=None
        )

        fact_store.add_fact(fact1)
        fact_store.add_fact(fact2)

        # Query facts at different times
        at_2023_03 = fact_store.get_facts_at(
            "researcher",
            datetime(2023, 3, 1, tzinfo=timezone.utc)
        )
        assert len(at_2023_03) == 1
        assert at_2023_03[0].id == "f1"

        at_2024_01 = fact_store.get_facts_at(
            "researcher",
            datetime(2024, 1, 1, tzinfo=timezone.utc)
        )
        assert len(at_2024_01) == 1
        assert at_2024_01[0].id == "f2"

    def test_update_fact(self, fact_store, sample_fact):
        """Test updating a fact."""
        fact_store.add_fact(sample_fact)

        # Update fact
        updated = fact_store.update_fact(
            sample_fact.id,
            content="Works at Company Z now",
            confidence=0.9,
            update_reason="Job change"
        )

        assert updated.content == "Works at Company Z now"
        assert updated.confidence == 0.9

        # Verify version was created
        history = fact_store.get_fact_history(sample_fact.id)
        assert len(history) == 1
        assert history[0].content == sample_fact.content

    def test_update_nonexistent_fact_raises_error(self, fact_store):
        """Test updating nonexistent fact raises error."""
        with pytest.raises(ValueError, match="not found"):
            fact_store.update_fact("nonexistent", content="New content")

    def test_get_fact_history(self, fact_store, sample_fact):
        """Test getting fact version history."""
        fact_store.add_fact(sample_fact)

        # Update multiple times
        fact_store.update_fact(sample_fact.id, content="Update 1", update_reason="Reason 1")
        fact_store.update_fact(sample_fact.id, content="Update 2", update_reason="Reason 2")

        history = fact_store.get_fact_history(sample_fact.id)

        assert len(history) == 2
        assert history[0].version == 1
        assert history[1].version == 2
        assert history[0].content == sample_fact.content
        assert history[1].content == "Update 1"

    def test_delete_fact(self, fact_store, sample_fact):
        """Test deleting a fact."""
        fact_store.add_fact(sample_fact)

        # Update to create version
        fact_store.update_fact(sample_fact.id, content="Updated")

        # Delete fact
        fact_store.delete_fact(sample_fact.id)

        # Verify fact and versions deleted
        assert fact_store.get_fact(sample_fact.id) is None
        assert len(fact_store.get_fact_history(sample_fact.id)) == 0

    def test_filter_by_fact_type(self, fact_store):
        """Test filtering facts by type."""
        # Add facts of different types
        employment = TemporalFact(
            id="emp_001",
            persona="researcher",
            fact_type="employment",
            content="Job",
            valid_from=datetime(2024, 1, 1, tzinfo=timezone.utc)
        )
        learning = TemporalFact(
            id="learn_001",
            persona="researcher",
            fact_type="learning",
            content="Learning Rust",
            valid_from=datetime(2024, 1, 1, tzinfo=timezone.utc)
        )

        fact_store.add_fact(employment)
        fact_store.add_fact(learning)

        # Filter by type
        employment_facts = fact_store.get_current_facts("researcher", fact_type="employment")
        assert len(employment_facts) == 1
        assert employment_facts[0].id == "emp_001"

        learning_facts = fact_store.get_current_facts("researcher", fact_type="learning")
        assert len(learning_facts) == 1
        assert learning_facts[0].id == "learn_001"
