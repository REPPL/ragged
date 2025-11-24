"""Tests for temporal reasoner."""

import pytest
from datetime import datetime, timedelta, timezone

from ragged.memory.temporal_reasoner import TemporalReasoner, TimeRange


class TestTimeExpressionParsing:
    """Test time expression parsing."""

    def test_parse_yesterday(self):
        """Test parsing 'yesterday'."""
        reasoner = TemporalReasoner()
        result = reasoner.parse_time_expression("yesterday")

        assert isinstance(result, TimeRange)
        # Yesterday should be 1 day ago
        now = datetime.now(timezone.utc)
        expected_start = now.replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=1)
        assert result.start.date() == expected_start.date()

    def test_parse_last_week(self):
        """Test parsing 'last week'."""
        reasoner = TemporalReasoner()
        result = reasoner.parse_time_expression("last week")

        assert isinstance(result, TimeRange)
        assert result.duration_days() >= 6  # At least 6 days

    def test_parse_n_days_ago(self):
        """Test parsing 'N days ago'."""
        reasoner = TemporalReasoner()
        result = reasoner.parse_time_expression("3 days ago")

        now = datetime.now(timezone.utc)
        expected = now - timedelta(days=3)
        assert result.start.date() == expected.date()

    def test_parse_quarter(self):
        """Test parsing 'Q1 2024'."""
        reasoner = TemporalReasoner()
        result = reasoner.parse_time_expression("Q1 2024")

        assert result.start == datetime(2024, 1, 1, tzinfo=timezone.utc)
        # Q1 ends on March 31
        assert result.end.month == 3
        assert result.end.year == 2024

    def test_parse_month_year(self):
        """Test parsing 'January 2024'."""
        reasoner = TemporalReasoner()
        result = reasoner.parse_time_expression("January 2024")

        assert result.start == datetime(2024, 1, 1, tzinfo=timezone.utc)
        assert result.end.month == 1
        assert result.end.year == 2024


class TestRecencyScoring:
    """Test recency scoring."""

    def test_exponential_decay(self):
        """Test exponential decay scoring."""
        reasoner = TemporalReasoner()
        now = datetime.now(timezone.utc)

        # Recent document (1 day ago)
        recent = now - timedelta(days=1)
        score_recent = reasoner.calculate_recency_score(recent, now, "exponential")

        # Old document (100 days ago)
        old = now - timedelta(days=100)
        score_old = reasoner.calculate_recency_score(old, now, "exponential")

        # Recent should score higher
        assert score_recent > score_old
        assert 0.0 <= score_old <= 1.0
        assert 0.0 <= score_recent <= 1.0

    def test_linear_decay(self):
        """Test linear decay scoring."""
        reasoner = TemporalReasoner()
        now = datetime.now(timezone.utc)

        # Document from 180 days ago (halfway through 365-day window)
        mid = now - timedelta(days=182)
        score = reasoner.calculate_recency_score(mid, now, "linear")

        # Should be approximately 0.5
        assert 0.4 < score < 0.6


class TestTimeRangeInclusion:
    """Test TimeRange inclusion checks."""

    def test_includes_time(self):
        """Test time inclusion check."""
        start = datetime(2024, 1, 1, tzinfo=timezone.utc)
        end = datetime(2024, 1, 31, tzinfo=timezone.utc)
        range = TimeRange(start, end)

        # Should include middle of January
        mid = datetime(2024, 1, 15, tzinfo=timezone.utc)
        assert range.includes_time(mid)

        # Should not include February
        feb = datetime(2024, 2, 1, tzinfo=timezone.utc)
        assert not range.includes_time(feb)
