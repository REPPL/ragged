"""Temporal query engine for time-based queries.

This module provides querying capabilities for temporal data:
- Activity timelines by period
- Topic evolution tracking
- Trending topic analysis
- Period comparisons

Part of v0.4.10 Advanced Temporal Features implementation.
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Optional, Tuple, Any
from collections import defaultdict
import logging

from ragged.memory.temporal_facts import TemporalFactStore
from ragged.memory.profile import ProfileManager, InterestProfile
from ragged.memory.interactions import InteractionTracker

logger = logging.getLogger(__name__)


@dataclass
class TimelineEntry:
    """Single entry in activity timeline.

    Attributes:
        timestamp: Entry timestamp
        activity_type: Type of activity ("query", "document_access", etc.)
        content: Activity content/description
        metadata: Additional metadata
    """

    timestamp: datetime
    activity_type: str
    content: str
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Timeline:
    """Activity timeline for a period.

    Attributes:
        persona: Associated persona
        since: Period start
        until: Period end
        entries: Timeline entries
        summary: Activity summary statistics
    """

    persona: str
    since: datetime
    until: datetime
    entries: List[TimelineEntry]
    summary: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TrendingTopic:
    """Trending topic with trend score.

    Attributes:
        topic: Topic name
        score: Trend score (higher = more trending)
        frequency: Query frequency
        recency: Recent activity indicator
        change: Change from previous period
    """

    topic: str
    score: float
    frequency: int
    recency: float
    change: float = 0.0


@dataclass
class PeriodComparison:
    """Comparison between two time periods.

    Attributes:
        persona: Associated persona
        period_a: First period
        period_b: Second period
        topics_gained: Topics that appeared in B but not A
        topics_lost: Topics that disappeared from B
        topics_increased: Topics with increased activity
        topics_decreased: Topics with decreased activity
        summary: Comparison summary statistics
    """

    persona: str
    period_a: Tuple[datetime, datetime]
    period_b: Tuple[datetime, datetime]
    topics_gained: List[str]
    topics_lost: List[str]
    topics_increased: List[Tuple[str, float]]
    topics_decreased: List[Tuple[str, float]]
    summary: Dict[str, Any] = field(default_factory=dict)


class TemporalQueryEngine:
    """Engine for time-based queries."""

    def __init__(
        self,
        fact_store: Optional[TemporalFactStore] = None,
        profile_manager: Optional[ProfileManager] = None,
        interaction_tracker: Optional[InteractionTracker] = None
    ):
        """Initialise temporal query engine.

        Args:
            fact_store: Temporal fact store
            profile_manager: Profile manager for interest data
            interaction_tracker: Interaction tracker for activity data
        """
        self.fact_store = fact_store
        self.profile_manager = profile_manager
        self.interaction_tracker = interaction_tracker

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
            since: Period start
            until: Period end
            granularity: "hour", "day", "week", "month"

        Returns:
            Timeline with aggregated activity
        """
        entries = []

        # Gather interactions if tracker available
        if self.interaction_tracker:
            interactions = self.interaction_tracker.get_interactions_in_range(
                persona, since, until
            )

            for interaction in interactions:
                entries.append(TimelineEntry(
                    timestamp=interaction.timestamp,
                    activity_type="query",
                    content=interaction.query,
                    metadata={
                        "documents_retrieved": len(interaction.documents_retrieved),
                        "topics": interaction.topics
                    }
                ))

        # Sort by timestamp
        entries.sort(key=lambda e: e.timestamp)

        # Calculate summary statistics
        summary = self._calculate_timeline_summary(entries, since, until, granularity)

        return Timeline(
            persona=persona,
            since=since,
            until=until,
            entries=entries,
            summary=summary
        )

    def get_activity_summary(
        self,
        persona: str,
        period: str
    ) -> Dict[str, Any]:
        """Get activity summary for period.

        Args:
            persona: Persona name
            period: "today", "yesterday", "this-week", "last-month", etc.

        Returns:
            Summary of activity with statistics
        """
        # Parse period to datetime range
        since, until = self._parse_period(period)

        # Get timeline
        timeline = self.get_timeline(persona, since, until)

        # Build summary
        summary = {
            "period": period,
            "since": since,
            "until": until,
            "total_queries": len([e for e in timeline.entries if e.activity_type == "query"]),
            "unique_topics": self._count_unique_topics(timeline.entries),
            "most_active_day": self._find_most_active_day(timeline.entries, since, until),
            "activity_by_type": self._count_by_type(timeline.entries)
        }

        return summary

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
            First occurrence timestamp or None if never seen
        """
        if not self.profile_manager:
            return None

        profile = self.profile_manager.get_profile(persona)
        if not profile:
            return None

        topic_interest = profile.topics.get(topic)
        if not topic_interest:
            return None

        return topic_interest.first_seen

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
            Topics sorted by trend score (descending)
        """
        if not self.profile_manager:
            return []

        # Parse window to datetime range
        days = int(window.rstrip('d'))
        until = datetime.now(timezone.utc)
        since = until - timedelta(days=days)

        # Get profile
        profile = self.profile_manager.get_profile(persona)
        if not profile:
            return []

        # Calculate trend scores for each topic
        trending = []

        for topic, interest in profile.topics.items():
            # Skip if not active in window
            if interest.last_seen < since:
                continue

            # Calculate trend score (frequency * recency * confidence)
            score = interest.frequency * interest.recency * interest.confidence

            # Calculate change (simplified - compare to previous window)
            change = self._calculate_topic_change(
                topic, profile, since, until, days
            )

            trending.append(TrendingTopic(
                topic=topic,
                score=score,
                frequency=interest.frequency,
                recency=interest.recency,
                change=change
            ))

        # Sort by score descending
        trending.sort(key=lambda t: t.score, reverse=True)

        return trending

    def compare_periods(
        self,
        persona: str,
        period_a: str,
        period_b: str
    ) -> PeriodComparison:
        """Compare activity between two periods.

        Args:
            persona: Persona name
            period_a: First period ("this-month", "last-month", etc.)
            period_b: Second period

        Returns:
            Comparison with changes
        """
        # Parse periods
        since_a, until_a = self._parse_period(period_a)
        since_b, until_b = self._parse_period(period_b)

        # Get activity for both periods
        timeline_a = self.get_timeline(persona, since_a, until_a)
        timeline_b = self.get_timeline(persona, since_b, until_b)

        # Extract topics from each period
        topics_a = self._extract_topics_from_timeline(timeline_a)
        topics_b = self._extract_topics_from_timeline(timeline_b)

        # Calculate changes
        topics_gained = list(set(topics_b.keys()) - set(topics_a.keys()))
        topics_lost = list(set(topics_a.keys()) - set(topics_b.keys()))

        topics_increased = []
        topics_decreased = []

        for topic in set(topics_a.keys()) & set(topics_b.keys()):
            change = topics_b[topic] - topics_a[topic]
            if change > 0:
                topics_increased.append((topic, change))
            elif change < 0:
                topics_decreased.append((topic, abs(change)))

        # Sort by magnitude
        topics_increased.sort(key=lambda x: x[1], reverse=True)
        topics_decreased.sort(key=lambda x: x[1], reverse=True)

        # Build summary
        summary = {
            "period_a_queries": len(timeline_a.entries),
            "period_b_queries": len(timeline_b.entries),
            "query_change": len(timeline_b.entries) - len(timeline_a.entries),
            "topics_gained_count": len(topics_gained),
            "topics_lost_count": len(topics_lost)
        }

        return PeriodComparison(
            persona=persona,
            period_a=(since_a, until_a),
            period_b=(since_b, until_b),
            topics_gained=topics_gained,
            topics_lost=topics_lost,
            topics_increased=topics_increased,
            topics_decreased=topics_decreased,
            summary=summary
        )

    def _parse_period(self, period: str) -> Tuple[datetime, datetime]:
        """Parse period string to datetime range.

        Args:
            period: Period string ("today", "yesterday", "this-week", etc.)

        Returns:
            Tuple of (since, until) datetimes
        """
        now = datetime.now(timezone.utc)
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

        if period == "today":
            return today_start, now
        elif period == "yesterday":
            yesterday_start = today_start - timedelta(days=1)
            return yesterday_start, today_start
        elif period == "this-week":
            # Start of week (Monday)
            week_start = today_start - timedelta(days=now.weekday())
            return week_start, now
        elif period == "last-week":
            week_start = today_start - timedelta(days=now.weekday())
            last_week_start = week_start - timedelta(days=7)
            return last_week_start, week_start
        elif period == "this-month":
            month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            return month_start, now
        elif period == "last-month":
            month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            last_month_end = month_start - timedelta(days=1)
            last_month_start = last_month_end.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            return last_month_start, last_month_end
        else:
            # Default to last 30 days
            return now - timedelta(days=30), now

    def _calculate_timeline_summary(
        self,
        entries: List[TimelineEntry],
        since: datetime,
        until: datetime,
        granularity: str
    ) -> Dict[str, Any]:
        """Calculate summary statistics for timeline."""
        # Count entries by day
        by_day = defaultdict(int)
        for entry in entries:
            day_key = entry.timestamp.date().isoformat()
            by_day[day_key] += 1

        # Most active day
        most_active_day = max(by_day.items(), key=lambda x: x[1]) if by_day else (None, 0)

        return {
            "total_entries": len(entries),
            "days_active": len(by_day),
            "most_active_day": most_active_day[0] if most_active_day[0] else None,
            "most_active_day_count": most_active_day[1],
            "average_per_day": len(entries) / max(1, len(by_day))
        }

    def _count_unique_topics(self, entries: List[TimelineEntry]) -> int:
        """Count unique topics across entries."""
        topics = set()
        for entry in entries:
            if "topics" in entry.metadata:
                topics.update(entry.metadata["topics"])
        return len(topics)

    def _find_most_active_day(
        self,
        entries: List[TimelineEntry],
        since: datetime,
        until: datetime
    ) -> Optional[str]:
        """Find most active day in period."""
        by_day = defaultdict(int)
        for entry in entries:
            day_key = entry.timestamp.date().isoformat()
            by_day[day_key] += 1

        if not by_day:
            return None

        return max(by_day.items(), key=lambda x: x[1])[0]

    def _count_by_type(self, entries: List[TimelineEntry]) -> Dict[str, int]:
        """Count entries by activity type."""
        by_type = defaultdict(int)
        for entry in entries:
            by_type[entry.activity_type] += 1
        return dict(by_type)

    def _extract_topics_from_timeline(
        self,
        timeline: Timeline
    ) -> Dict[str, int]:
        """Extract topic frequencies from timeline."""
        topics = defaultdict(int)
        for entry in timeline.entries:
            if "topics" in entry.metadata:
                for topic in entry.metadata["topics"]:
                    topics[topic] += 1
        return dict(topics)

    def _calculate_topic_change(
        self,
        topic: str,
        profile: InterestProfile,
        since: datetime,
        until: datetime,
        window_days: int
    ) -> float:
        """Calculate topic frequency change compared to previous window."""
        # This is a simplified implementation
        # In a full implementation, we'd query interaction history
        # and compare frequencies across time windows

        interest = profile.topics.get(topic)
        if not interest:
            return 0.0

        # Approximate change using recency as proxy
        # High recency = recent activity = positive change
        return interest.recency - 0.5  # Normalized around 0
