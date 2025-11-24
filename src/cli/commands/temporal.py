"""CLI commands for temporal memory features.

Commands:
- ragged temporal fact add: Add temporal fact
- ragged temporal fact list: List facts
- ragged temporal timeline: Show activity timeline
- ragged temporal trending: Show trending topics

Part of v0.4.10 Advanced Temporal Features implementation.
"""

import click
from datetime import datetime, timedelta, timezone
from pathlib import Path
import sys

from ragged.memory.temporal_facts import TemporalFact, TemporalFactStore
from ragged.memory.temporal_query import TemporalQueryEngine
from ragged.memory.profile import ProfileManager
from ragged.memory.interactions import InteractionTracker


@click.group(name="temporal")
def temporal_cli():
    """Temporal memory commands."""
    pass


@temporal_cli.group(name="fact")
def fact_group():
    """Temporal fact management."""
    pass


@fact_group.command(name="add")
@click.option("--persona", required=True, help="Persona name")
@click.option("--type", "fact_type", required=True, help="Fact type (employment, learning, etc.)")
@click.option("--content", required=True, help="Fact content")
@click.option("--from", "valid_from", required=True, help="Valid from date (YYYY-MM-DD)")
@click.option("--to", "valid_to", default=None, help="Valid to date (YYYY-MM-DD), omit for current")
@click.option("--confidence", default=1.0, type=float, help="Confidence score (0.0-1.0)")
@click.option("--source", default="manual", help="Fact source")
def add_fact(persona, fact_type, content, valid_from, valid_to, confidence, source):
    """Add new temporal fact."""
    import uuid

    # Parse dates
    try:
        from_date = datetime.fromisoformat(valid_from).replace(tzinfo=timezone.utc)
        to_date = datetime.fromisoformat(valid_to).replace(tzinfo=timezone.utc) if valid_to else None
    except ValueError as e:
        click.echo(f"Error: Invalid date format. Use YYYY-MM-DD. {e}", err=True)
        sys.exit(1)

    # Create fact
    fact = TemporalFact(
        id=str(uuid.uuid4()),
        persona=persona,
        fact_type=fact_type,
        content=content,
        valid_from=from_date,
        valid_to=to_date,
        confidence=confidence,
        source=source
    )

    # Get storage path
    storage_path = Path.home() / ".ragged" / "memory" / "temporal_facts.db"
    storage_path.parent.mkdir(parents=True, exist_ok=True)

    # Save fact
    store = TemporalFactStore(db_path=str(storage_path))
    store.add_fact(fact)

    click.echo(f"✓ Added temporal fact: {fact.id}")
    click.echo(f"  Type: {fact_type}")
    click.echo(f"  Content: {content}")
    click.echo(f"  Valid: {valid_from} → {valid_to or 'present'}")


@fact_group.command(name="list")
@click.option("--persona", required=True, help="Persona name")
@click.option("--type", "fact_type", default=None, help="Filter by fact type")
@click.option("--current-only", is_flag=True, help="Show only currently valid facts")
def list_facts(persona, fact_type, current_only):
    """List temporal facts."""
    storage_path = Path.home() / ".ragged" / "memory" / "temporal_facts.db"

    if not storage_path.exists():
        click.echo("No temporal facts found.", err=True)
        sys.exit(1)

    store = TemporalFactStore(db_path=str(storage_path))

    if current_only:
        facts = store.get_current_facts(persona, fact_type)
    else:
        # Get all facts for persona
        facts = store.get_facts_at(persona, datetime.now(timezone.utc), fact_type)

    if not facts:
        click.echo(f"No facts found for persona '{persona}'")
        return

    click.echo(f"\nTemporal Facts for {persona}:")
    click.echo("=" * 80)

    for fact in facts:
        status = "CURRENT" if fact.is_current() else "HISTORICAL"
        click.echo(f"\n[{status}] {fact.fact_type.upper()}")
        click.echo(f"  Content: {fact.content}")
        click.echo(f"  Valid: {fact.valid_from.date()} → {fact.valid_to.date() if fact.valid_to else 'present'}")
        click.echo(f"  Confidence: {fact.confidence:.2f}")
        click.echo(f"  Source: {fact.source}")


@temporal_cli.command(name="timeline")
@click.option("--persona", required=True, help="Persona name")
@click.option("--period", default="this-week", help="Period (today, this-week, this-month, etc.)")
@click.option("--since", default=None, help="Start date (YYYY-MM-DD)")
@click.option("--until", default=None, help="End date (YYYY-MM-DD)")
def show_timeline(persona, period, since, until):
    """Show activity timeline."""
    # Parse dates if provided
    if since and until:
        try:
            since_date = datetime.fromisoformat(since).replace(tzinfo=timezone.utc)
            until_date = datetime.fromisoformat(until).replace(tzinfo=timezone.utc)
        except ValueError as e:
            click.echo(f"Error: Invalid date format. Use YYYY-MM-DD. {e}", err=True)
            sys.exit(1)
    else:
        # Use period
        engine = TemporalQueryEngine()
        since_date, until_date = engine._parse_period(period)

    # Get profile manager and interaction tracker
    storage_path = Path.home() / ".ragged" / "memory"
    storage_path.mkdir(parents=True, exist_ok=True)

    profile_db = storage_path / "profiles.db"
    interaction_db = storage_path / "interactions.db"

    profile_manager = ProfileManager(db_path=str(profile_db))
    interaction_tracker = InteractionTracker(db_path=str(interaction_db))

    # Create engine and get timeline
    engine = TemporalQueryEngine(
        profile_manager=profile_manager,
        interaction_tracker=interaction_tracker
    )

    timeline = engine.get_timeline(persona, since_date, until_date)

    # Display timeline
    click.echo(f"\nActivity Timeline for {persona}")
    click.echo(f"Period: {since_date.date()} to {until_date.date()}")
    click.echo("=" * 80)

    if not timeline.entries:
        click.echo("\nNo activity found for this period.")
        return

    # Group by day
    from collections import defaultdict
    by_day = defaultdict(list)

    for entry in timeline.entries:
        day = entry.timestamp.date()
        by_day[day].append(entry)

    # Display by day
    for day in sorted(by_day.keys()):
        entries = by_day[day]
        click.echo(f"\n{day} ({len(entries)} activities)")
        click.echo("-" * 80)

        for entry in entries[:5]:  # Show first 5 per day
            time = entry.timestamp.strftime("%H:%M")
            click.echo(f"  {time} | {entry.activity_type}: {entry.content[:60]}")

        if len(entries) > 5:
            click.echo(f"  ... and {len(entries) - 5} more activities")

    # Display summary
    click.echo(f"\n{'=' * 80}")
    click.echo("Summary:")
    click.echo(f"  Total activities: {timeline.summary.get('total_entries', 0)}")
    click.echo(f"  Days active: {timeline.summary.get('days_active', 0)}")
    click.echo(f"  Average per day: {timeline.summary.get('average_per_day', 0):.1f}")


@temporal_cli.command(name="trending")
@click.option("--persona", required=True, help="Persona name")
@click.option("--window", default="30d", help="Time window (7d, 30d, 90d)")
@click.option("--limit", default=10, type=int, help="Number of topics to show")
def show_trending(persona, window, limit):
    """Show trending topics."""
    storage_path = Path.home() / ".ragged" / "memory"
    profile_db = storage_path / "profiles.db"

    if not profile_db.exists():
        click.echo(f"No profile found for persona '{persona}'", err=True)
        sys.exit(1)

    profile_manager = ProfileManager(db_path=str(profile_db))
    engine = TemporalQueryEngine(profile_manager=profile_manager)

    trending = engine.get_trending_topics(persona, window)

    if not trending:
        click.echo(f"\nNo trending topics for {persona} in last {window}")
        return

    click.echo(f"\nTrending Topics for {persona} (last {window})")
    click.echo("=" * 80)

    for i, topic in enumerate(trending[:limit], 1):
        change_indicator = "↗" if topic.change > 0 else "↘" if topic.change < 0 else "→"
        click.echo(f"{i:2d}. {topic.topic:30s} | Score: {topic.score:6.2f} | Freq: {topic.frequency:3d} {change_indicator}")
