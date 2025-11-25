"""Temporal reasoning for natural language time expressions.

Provides time expression parsing, temporal query enhancement, and
recency scoring for documents.

Part of v0.4.11 Advanced Temporal Features.
"""
from __future__ import annotations


from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import List, Optional, Dict, Any
import re
import math
import logging

logger = logging.getLogger(__name__)


@dataclass
class TimeRange:
    """Time range with start and end."""

    start: datetime
    end: datetime

    def includes_time(self, timestamp: datetime) -> bool:
        """Check if timestamp falls within this range."""
        return self.start <= timestamp <= self.end

    def duration_days(self) -> float:
        """Get duration in days."""
        return (self.end - self.start).total_seconds() / 86400


@dataclass
class EnhancedQuery:
    """Query enhanced with temporal context."""

    original_query: str
    time_contexts: List[TimeRange]
    temporal_facts: List[Any]
    focus_period: Optional[TimeRange] = None


class TemporalReasoner:
    """Apply temporal reasoning to queries.

    Supports natural language time expressions without external dependencies:
    - Relative: "yesterday", "last week", "3 days ago"
    - Named periods: "Q1 2024", "January", "this month"
    - ISO dates: "2024-01-15"
    """

    QUARTERS = {
        'q1': (1, 3), 'q2': (4, 6),
        'q3': (7, 9), 'q4': (10, 12)
    }

    MONTHS = {
        'january': 1, 'jan': 1,
        'february': 2, 'feb': 2,
        'march': 3, 'mar': 3,
        'april': 4, 'apr': 4,
        'may': 5,
        'june': 6, 'jun': 6,
        'july': 7, 'jul': 7,
        'august': 8, 'aug': 8,
        'september': 9, 'sep': 9, 'sept': 9,
        'october': 10, 'oct': 10,
        'november': 11, 'nov': 11,
        'december': 12, 'dec': 12
    }

    def parse_time_expression(
        self,
        expression: str,
        reference_time: Optional[datetime] = None
    ) -> TimeRange:
        """Parse natural language time expression.

        Examples:
            "yesterday" → yesterday 00:00 to 23:59:59
            "last week" → last Monday to Sunday
            "January 2024" → 2024-01-01 to 2024-01-31
            "Q4 2023" → 2023-10-01 to 2023-12-31
            "3 days ago" → 3 days ago to 3 days ago

        Args:
            expression: Time expression to parse
            reference_time: Base time (default: now)

        Returns:
            TimeRange representing the expression

        Raises:
            ValueError: If expression cannot be parsed
        """
        ref = reference_time or datetime.now(timezone.utc)
        expr = expression.lower().strip()

        # Try ISO date first
        try:
            dt = datetime.fromisoformat(expr).replace(tzinfo=timezone.utc)
            return TimeRange(dt, dt)
        except ValueError:
            pass

        # Relative expressions
        if expr == "yesterday":
            start = ref.replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=1)
            end = start + timedelta(days=1) - timedelta(microseconds=1)
            return TimeRange(start, end)

        if expr == "today":
            start = ref.replace(hour=0, minute=0, second=0, microsecond=0)
            end = start + timedelta(days=1) - timedelta(microseconds=1)
            return TimeRange(start, end)

        if expr == "tomorrow":
            start = ref.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
            end = start + timedelta(days=1) - timedelta(microseconds=1)
            return TimeRange(start, end)

        # "N days/weeks/months ago"
        match = re.match(r'(\d+)\s+(day|week|month|year)s?\s+ago', expr)
        if match:
            n, unit = int(match.group(1)), match.group(2)
            if unit == 'day':
                delta = timedelta(days=n)
            elif unit == 'week':
                delta = timedelta(weeks=n)
            elif unit == 'month':
                delta = timedelta(days=n * 30)  # Approximate
            else:  # year
                delta = timedelta(days=n * 365)

            target = ref - delta
            start = target.replace(hour=0, minute=0, second=0, microsecond=0)
            end = start + timedelta(days=1) - timedelta(microseconds=1)
            return TimeRange(start, end)

        # "last week/month/year"
        if expr.startswith("last "):
            period = expr[5:]  # Remove "last "
            if period == "week":
                # Last Monday to Sunday
                days_since_monday = ref.weekday()
                last_monday = ref - timedelta(days=days_since_monday + 7)
                start = last_monday.replace(hour=0, minute=0, second=0, microsecond=0)
                end = start + timedelta(days=7) - timedelta(microseconds=1)
                return TimeRange(start, end)

            if period == "month":
                # Previous month
                if ref.month == 1:
                    prev_month = 12
                    year = ref.year - 1
                else:
                    prev_month = ref.month - 1
                    year = ref.year

                start = datetime(year, prev_month, 1, tzinfo=timezone.utc)
                # Last day of previous month
                if prev_month == 12:
                    end = datetime(year + 1, 1, 1, tzinfo=timezone.utc) - timedelta(microseconds=1)
                else:
                    end = datetime(year, prev_month + 1, 1, tzinfo=timezone.utc) - timedelta(microseconds=1)

                return TimeRange(start, end)

        # "this week/month/year"
        if expr.startswith("this "):
            period = expr[5:]
            if period == "week":
                days_since_monday = ref.weekday()
                this_monday = ref - timedelta(days=days_since_monday)
                start = this_monday.replace(hour=0, minute=0, second=0, microsecond=0)
                end = ref
                return TimeRange(start, end)

            if period == "month":
                start = ref.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
                return TimeRange(start, ref)

            if period == "year":
                start = ref.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
                return TimeRange(start, ref)

        # "Quarter YYYY" e.g., "Q1 2024"
        match = re.match(r'q([1-4])\s+(\d{4})', expr)
        if match:
            quarter, year = int(match.group(1)), int(match.group(2))
            start_month, end_month = self.QUARTERS[f'q{quarter}']
            start = datetime(year, start_month, 1, tzinfo=timezone.utc)
            # Last day of quarter
            if end_month == 12:
                end = datetime(year + 1, 1, 1, tzinfo=timezone.utc) - timedelta(microseconds=1)
            else:
                end = datetime(year, end_month + 1, 1, tzinfo=timezone.utc) - timedelta(microseconds=1)

            return TimeRange(start, end)

        # "Month YYYY" e.g., "January 2024"
        for month_name, month_num in self.MONTHS.items():
            if month_name in expr:
                # Extract year
                year_match = re.search(r'\d{4}', expr)
                if year_match:
                    year = int(year_match.group(0))
                    start = datetime(year, month_num, 1, tzinfo=timezone.utc)
                    # Last day of month
                    if month_num == 12:
                        end = datetime(year + 1, 1, 1, tzinfo=timezone.utc) - timedelta(microseconds=1)
                    else:
                        end = datetime(year, month_num + 1, 1, tzinfo=timezone.utc) - timedelta(microseconds=1)

                    return TimeRange(start, end)

        raise ValueError(f"Could not parse time expression: {expression}")

    def calculate_recency_score(
        self,
        document_time: datetime,
        query_time: Optional[datetime] = None,
        decay_function: str = "exponential",
        half_life_days: float = 30.0
    ) -> float:
        """Calculate recency relevance score.

        Args:
            document_time: When document was created/modified
            query_time: Time of query (default: now)
            decay_function: "exponential", "linear", or "logarithmic"
            half_life_days: Days for exponential decay (default: 30)

        Returns:
            Recency score [0.0, 1.0]
        """
        ref = query_time or datetime.now(timezone.utc)
        age_days = (ref - document_time).total_seconds() / 86400

        if age_days < 0:
            # Future document? Return 0
            return 0.0

        if decay_function == "exponential":
            # Exponential decay: score = e^(-age / half_life)
            return math.exp(-age_days / half_life_days)

        elif decay_function == "linear":
            # Linear decay over 365 days
            return max(0.0, 1.0 - (age_days / 365))

        elif decay_function == "logarithmic":
            # Logarithmic decay (slower for old content)
            return 1.0 / (1.0 + math.log1p(age_days / half_life_days))

        else:
            raise ValueError(f"Unknown decay function: {decay_function}")

    def extract_time_expressions(self, text: str) -> List[str]:
        """Extract potential time expressions from text.

        Uses pattern matching to find common time expressions.

        Args:
            text: Text to extract from

        Returns:
            List of potential time expressions
        """
        patterns = [
            r'\b(last|this|next)\s+(week|month|year|quarter)\b',
            r'\b\d+\s+(days?|weeks?|months?|years?)\s+ago\b',
            r'\b(yesterday|today|tomorrow)\b',
            r'\b(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\s+\d{4}\b',
            r'\bQ[1-4]\s+\d{4}\b',
            r'\d{4}-\d{2}-\d{2}\b',
        ]

        expressions = []
        for pattern in patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            expressions.extend([m.group(0) for m in matches])

        return expressions
