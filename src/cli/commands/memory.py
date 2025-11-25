"""Memory/interaction management commands for ragged CLI.

v0.4.5: Interaction history tracking and management.
v0.4.7: Interest profile and behaviour learning commands.
"""
from __future__ import annotations


import json
import sys
from pathlib import Path

import click

from ragged.cli.common import console
from ragged.cli.formatters import FORMAT_CHOICES, print_formatted
from ragged.config.settings import get_settings
from ragged.memory.behaviour import create_behaviour_learner
from ragged.memory.interactions import InteractionTracker
from ragged.memory.persona import PersonaManager
from ragged.utils.logging import get_logger
from ragged.validation.path_validator import PathTraversalError, PathValidator

logger = get_logger(__name__)


def _get_active_persona() -> str | None:
    """Get active persona or None."""
    try:
        manager = PersonaManager()
        active = manager.get_active()
        return active.name if active else None
    except Exception:
        return None


@click.group()
def memory() -> None:
    """Manage interaction history and memory.

    View, export, and manage your interaction history with full privacy.
    All data is stored locally and never leaves your device.
    """
    pass


@memory.command("list")
@click.option(
    "--persona",
    "-p",
    help="Filter by persona (uses active persona if not specified)",
)
@click.option(
    "--limit",
    "-l",
    type=int,
    default=10,
    help="Maximum number of interactions to show (default: 10)",
)
@click.option(
    "--offset",
    "-o",
    type=int,
    default=0,
    help="Number of interactions to skip (default: 0)",
)
@click.option(
    "--session",
    "-s",
    help="Filter by session ID",
)
@click.option(
    "--format",
    "-f",
    "output_format",
    type=click.Choice(FORMAT_CHOICES + ["text"], case_sensitive=False),
    default="text",
    help="Output format",
)
def list_interactions(
    persona: str | None,
    limit: int,
    offset: int,
    session: str | None,
    output_format: str,
) -> None:
    """List interaction history.

    \b
    Examples:
        ragged memory list
        ragged memory list --limit 20
        ragged memory list --persona researcher
        ragged memory list --session session-123 --format json
    """
    try:
        # Use active persona if not specified
        persona = persona or _get_active_persona()

        tracker = InteractionTracker()
        interactions = tracker.list_interactions(
            persona=persona,
            limit=limit,
            offset=offset,
            session_id=session,
        )

        if not interactions:
            console.print("\n[yellow]No interactions found.[/yellow]")
            if not persona:
                console.print(
                    "[dim]No active persona set. Use 'ragged persona switch <name>'[/dim]"
                )
            console.print()
            return

        # Format data
        interactions_data = []
        for i in interactions:
            interactions_data.append(
                {
                    "id": i.id[:8] + "...",  # Shortened ID for display
                    "timestamp": i.timestamp.strftime("%Y-%m-%d %H:%M"),
                    "persona": i.persona,
                    "query": (i.query[:60] + "...") if len(i.query) > 60 else i.query,
                    "model": i.model_used or "-",
                    "latency_ms": i.latency_ms if i.latency_ms else "-",
                    "feedback": i.feedback or "-",
                }
            )

        if output_format == "text":
            console.print(
                f"\n[bold]Interaction History[/bold] (showing {len(interactions)} of {limit})\n"
            )
            if persona:
                console.print(f"Persona: [bold]{persona}[/bold]\n")

            for idx, data in enumerate(interactions_data, start=offset + 1):
                console.print(f"[dim]{idx}.[/dim] {data['timestamp']} - {data['query']}")
                console.print(f"   ID: {data['id']} | Model: {data['model']}")
                if data["feedback"] != "-":
                    console.print(f"   Feedback: {data['feedback']}")
                console.print()
        else:
            print_formatted(
                interactions_data,
                format_type=output_format,  # type: ignore
                title="Interaction History",
                console=console,
            )

    except Exception as e:
        console.print(f"[bold red]✗[/bold red] Failed to list interactions: {e}")
        logger.error(f"List interactions failed: {e}", exc_info=True)
        sys.exit(1)


@memory.command("show")
@click.argument("interaction_id")
@click.option(
    "--format",
    "-f",
    "output_format",
    type=click.Choice(FORMAT_CHOICES + ["text"], case_sensitive=False),
    default="text",
    help="Output format",
)
def show_interaction(interaction_id: str, output_format: str) -> None:
    """Show detailed information about an interaction.

    \b
    Examples:
        ragged memory show abc123...
        ragged memory show abc123... --format json
    """
    try:
        tracker = InteractionTracker()
        interaction = tracker.get_interaction(interaction_id)

        data = {
            "id": interaction.id,
            "persona": interaction.persona,
            "timestamp": interaction.timestamp.isoformat(),
            "query": interaction.query,
            "response": interaction.response or "(no response)",
            "retrieved_docs": interaction.retrieved_doc_ids,
            "model_used": interaction.model_used or "-",
            "latency_ms": interaction.latency_ms if interaction.latency_ms else "-",
            "feedback": interaction.feedback or "-",
            "session_id": interaction.session_id or "-",
        }

        if output_format == "text":
            console.print(f"\n[bold]Interaction Details[/bold]\n")
            console.print(f"ID: {data['id']}")
            console.print(f"Persona: {data['persona']}")
            console.print(
                f"Timestamp: {interaction.timestamp.strftime('%Y-%m-%d %H:%M:%S')}"
            )
            console.print(f"\n[bold]Query:[/bold]\n{data['query']}")
            console.print(f"\n[bold]Response:[/bold]\n{data['response']}")

            if interaction.retrieved_doc_ids:
                console.print(
                    f"\n[bold]Retrieved Documents ({len(interaction.retrieved_doc_ids)}):[/bold]"
                )
                for doc_id in interaction.retrieved_doc_ids:
                    console.print(f"  • {doc_id}")

            console.print(f"\n[bold]Metadata:[/bold]")
            console.print(f"Model: {data['model_used']}")
            if data["latency_ms"] != "-":
                console.print(f"Latency: {data['latency_ms']}ms")
            if data["feedback"] != "-":
                console.print(f"Feedback: {data['feedback']}")
            if data["session_id"] != "-":
                console.print(f"Session: {data['session_id']}")
            console.print()
        else:
            print_formatted(
                [data],
                format_type=output_format,  # type: ignore
                title="Interaction Details",
                console=console,
            )

    except KeyError as e:
        console.print(f"[bold red]✗[/bold red] {e}")
        sys.exit(1)
    except Exception as e:
        console.print(f"[bold red]✗[/bold red] Failed to show interaction: {e}")
        logger.error(f"Show interaction failed: {e}", exc_info=True)
        sys.exit(1)


@memory.command("delete")
@click.argument("interaction_id")
@click.option(
    "--yes",
    "-y",
    is_flag=True,
    help="Skip confirmation prompt",
)
def delete_interaction(interaction_id: str, yes: bool) -> None:
    """Delete a specific interaction.

    \b
    Examples:
        ragged memory delete abc123...
        ragged memory delete abc123... --yes
    """
    try:
        tracker = InteractionTracker()

        # Get interaction details for confirmation
        interaction = tracker.get_interaction(interaction_id)

        # Confirm deletion
        if not yes:
            console.print(f"\n[yellow]About to delete interaction:[/yellow]")
            console.print(f"ID: {interaction.id}")
            console.print(f"Persona: {interaction.persona}")
            console.print(
                f"Timestamp: {interaction.timestamp.strftime('%Y-%m-%d %H:%M')}"
            )
            console.print(
                f"Query: {(interaction.query[:60] + '...') if len(interaction.query) > 60 else interaction.query}"
            )

            if not click.confirm("\nContinue?"):
                console.print("Cancelled.")
                return

        # Delete interaction
        tracker.delete_interaction(interaction_id, confirm=True)

        console.print(f"\n[green]✓[/green] Deleted interaction: {interaction_id[:16]}...\n")

    except KeyError as e:
        console.print(f"[bold red]✗[/bold red] {e}")
        sys.exit(1)
    except Exception as e:
        console.print(f"[bold red]✗[/bold red] Failed to delete interaction: {e}")
        logger.error(f"Delete interaction failed: {e}", exc_info=True)
        sys.exit(1)


@memory.command("export")
@click.argument("output_file", type=click.Path())
@click.option(
    "--persona",
    "-p",
    help="Filter by persona (uses active persona if not specified)",
)
def export_interactions(output_file: str, persona: str | None) -> None:
    """Export interactions to JSON file.

    \b
    Examples:
        ragged memory export interactions.json
        ragged memory export interactions.json --persona researcher
    """
    try:
        # v0.5.8 HIGH-5: Validate output path for security
        try:
            validator = PathValidator(
                allowed_base=None,  # Allow export anywhere
                allow_absolute=True,  # Users commonly use absolute paths
                allow_symlinks=False,  # Block symlinks for security
            )
            output_path = validator.validate(Path(output_file))
        except PathTraversalError as e:
            console.print(f"[bold red]✗ Security Error:[/bold red] {e}")
            logger.error(f"Path validation failed: {e}")
            sys.exit(1)

        # Use active persona if not specified
        persona = persona or _get_active_persona()

        tracker = InteractionTracker()

        export_data = tracker.export_interactions(
            persona=persona,
            output_path=output_path,
        )

        console.print(f"\n[green]✓[/green] Exported {export_data['interaction_count']} interactions")
        console.print(f"Output: {output_path.absolute()}")
        if persona:
            console.print(f"Persona: {persona}")
        console.print()

    except Exception as e:
        console.print(f"[bold red]✗[/bold red] Failed to export interactions: {e}")
        logger.error(f"Export interactions failed: {e}", exc_info=True)
        sys.exit(1)


@memory.command("clear")
@click.option(
    "--persona",
    "-p",
    help="Filter by persona (uses active persona if not specified)",
)
@click.option(
    "--yes",
    "-y",
    is_flag=True,
    help="Skip confirmation prompt",
)
def clear_interactions(persona: str | None, yes: bool) -> None:
    """Clear all interactions for a persona.

    \b
    Examples:
        ragged memory clear
        ragged memory clear --persona researcher
        ragged memory clear --persona researcher --yes
    """
    try:
        # Use active persona if not specified
        persona = persona or _get_active_persona()

        if not persona:
            console.print(
                "[bold red]✗[/bold red] No persona specified and no active persona set."
            )
            console.print("[dim]Use --persona or set an active persona first[/dim]")
            sys.exit(1)

        tracker = InteractionTracker()

        # Get count for confirmation
        interactions = tracker.list_interactions(persona=persona, limit=10000)
        count = len(interactions)

        if count == 0:
            console.print(f"\n[yellow]No interactions found for persona: {persona}[/yellow]\n")
            return

        # Confirm deletion
        if not yes:
            console.print(
                f"\n[yellow]About to delete ALL {count} interaction(s) for persona:[/yellow] [bold]{persona}[/bold]"
            )
            console.print(
                "\n[bold red]⚠ This action cannot be undone![/bold red]"
            )

            if not click.confirm("\nContinue?"):
                console.print("Cancelled.")
                return

        # Clear interactions
        deleted_count = tracker.clear_interactions(persona=persona, confirm=True)

        console.print(
            f"\n[green]✓[/green] Deleted {deleted_count} interaction(s) for persona: {persona}\n"
        )

    except ValueError as e:
        console.print(f"[bold red]✗[/bold red] {e}")
        sys.exit(1)
    except Exception as e:
        console.print(f"[bold red]✗[/bold red] Failed to clear interactions: {e}")
        logger.error(f"Clear interactions failed: {e}", exc_info=True)
        sys.exit(1)


@memory.command("feedback")
@click.argument("interaction_id")
@click.argument(
    "feedback_value",
    type=click.Choice(["positive", "negative", "neutral"], case_sensitive=False),
)
def add_feedback(interaction_id: str, feedback_value: str) -> None:
    """Add feedback to an interaction.

    \b
    Examples:
        ragged memory feedback abc123... positive
        ragged memory feedback abc123... negative
        ragged memory feedback abc123... neutral
    """
    try:
        tracker = InteractionTracker()

        # Verify interaction exists
        interaction = tracker.get_interaction(interaction_id)

        # Add feedback
        tracker.add_feedback(interaction_id, feedback_value.lower())

        console.print(
            f"\n[green]✓[/green] Added [bold]{feedback_value}[/bold] feedback to interaction\n"
        )

    except KeyError as e:
        console.print(f"[bold red]✗[/bold red] {e}")
        sys.exit(1)
    except ValueError as e:
        console.print(f"[bold red]✗[/bold red] {e}")
        sys.exit(1)
    except Exception as e:
        console.print(f"[bold red]✗[/bold red] Failed to add feedback: {e}")
        logger.error(f"Add feedback failed: {e}", exc_info=True)
        sys.exit(1)


@memory.command("stats")
@click.option(
    "--persona",
    "-p",
    help="Filter by persona (uses active persona if not specified)",
)
@click.option(
    "--format",
    "-f",
    "output_format",
    type=click.Choice(FORMAT_CHOICES + ["text"], case_sensitive=False),
    default="text",
    help="Output format",
)
def memory_stats(persona: str | None, output_format: str) -> None:
    """Show memory statistics.

    \b
    Examples:
        ragged memory stats
        ragged memory stats --persona researcher
        ragged memory stats --format json
    """
    try:
        # Use active persona if not specified
        persona = persona or _get_active_persona()

        tracker = InteractionTracker()
        interactions = tracker.list_interactions(persona=persona, limit=10000)

        # Calculate statistics
        total_count = len(interactions)
        if total_count == 0:
            console.print(f"\n[yellow]No interactions found for persona: {persona or 'all'}[/yellow]\n")
            return

        # Collect stats
        models_used = {}
        feedback_counts = {"positive": 0, "negative": 0, "neutral": 0}
        total_latency = 0
        latency_count = 0

        for i in interactions:
            if i.model_used:
                models_used[i.model_used] = models_used.get(i.model_used, 0) + 1
            if i.feedback:
                feedback_counts[i.feedback] = feedback_counts.get(i.feedback, 0) + 1
            if i.latency_ms:
                total_latency += i.latency_ms
                latency_count += 1

        avg_latency = total_latency / latency_count if latency_count > 0 else 0

        stats_data = {
            "persona": persona or "all",
            "total_interactions": total_count,
            "models_used": models_used,
            "feedback": feedback_counts,
            "average_latency_ms": round(avg_latency, 2) if avg_latency > 0 else None,
        }

        if output_format == "text":
            console.print(f"\n[bold]Memory Statistics[/bold]\n")
            if persona:
                console.print(f"Persona: [bold]{persona}[/bold]")
            console.print(f"Total Interactions: {total_count}")

            if models_used:
                console.print(f"\n[bold]Models Used:[/bold]")
                for model, count in sorted(
                    models_used.items(), key=lambda x: x[1], reverse=True
                ):
                    percentage = (count / total_count) * 100
                    console.print(f"  {model}: {count} ({percentage:.1f}%)")

            console.print(f"\n[bold]Feedback:[/bold]")
            for feedback_type, count in feedback_counts.items():
                if count > 0:
                    percentage = (count / total_count) * 100
                    console.print(f"  {feedback_type}: {count} ({percentage:.1f}%)")

            if avg_latency > 0:
                console.print(f"\n[bold]Performance:[/bold]")
                console.print(f"  Average Latency: {avg_latency:.2f}ms")

            console.print()
        else:
            print_formatted(
                [stats_data],
                format_type=output_format,  # type: ignore
                title="Memory Statistics",
                console=console,
            )

    except Exception as e:
        console.print(f"[bold red]✗[/bold red] Failed to get memory stats: {e}")
        logger.error(f"Memory stats failed: {e}", exc_info=True)
        sys.exit(1)


# ============================================================================
# v0.4.7: Interest Profile & Behaviour Learning Commands
# ============================================================================


@memory.command("profile")
@click.option(
    "--persona",
    "-p",
    help="Persona to view (uses active persona if not specified)",
)
@click.option(
    "--format",
    "-f",
    "output_format",
    type=click.Choice(FORMAT_CHOICES + ["text"], case_sensitive=False),
    default="text",
    help="Output format",
)
def show_profile(persona: str | None, output_format: str) -> None:
    """Show interest profile for persona.

    \b
    Examples:
        ragged memory profile
        ragged memory profile --persona researcher
        ragged memory profile --format json
    """
    try:
        # Use active persona if not specified
        persona = persona or _get_active_persona()

        if not persona:
            console.print(
                "[bold red]✗[/bold red] No persona specified and no active persona set."
            )
            console.print("[dim]Use --persona or set an active persona first[/dim]")
            sys.exit(1)

        # Get behaviour learner
        settings = get_settings()
        data_dir = Path(settings.data_dir)
        learner = create_behaviour_learner(data_dir / "memory")

        # Get insights
        insights = learner.get_persona_insights(persona)

        if output_format == "text":
            console.print(f"\n[bold]Interest Profile: {persona}[/bold]\n")

            if insights["profile_age_days"] == 0:
                console.print("Profile Age: Today")
            elif insights["profile_age_days"] == 1:
                console.print("Profile Age: 1 day")
            else:
                console.print(f"Profile Age: {insights['profile_age_days']} days")

            console.print(f"Total Topics: {insights['total_topics']}\n")

            if insights["top_topics"]:
                console.print("[bold]Top Topics (by confidence):[/bold]")
                from datetime import datetime

                for idx, topic in enumerate(insights["top_topics"], start=1):
                    last_seen = datetime.fromisoformat(topic["last_seen"])
                    time_ago = _format_time_ago(last_seen)

                    console.print(
                        f"{idx}. [bold]{topic['topic']}[/bold] "
                        f"(confidence: {topic['confidence']:.2f}, "
                        f"frequency: {topic['frequency']}, "
                        f"last seen: {time_ago})"
                    )
                console.print()
            else:
                console.print(
                    "[yellow]No topics tracked yet. Start querying to build your profile![/yellow]\n"
                )

        else:
            print_formatted(
                [insights],
                format_type=output_format,  # type: ignore
                title="Interest Profile",
                console=console,
            )

    except Exception as e:
        console.print(f"[bold red]✗[/bold red] Failed to show profile: {e}")
        logger.error(f"Show profile failed: {e}", exc_info=True)
        sys.exit(1)


@memory.command("topics")
@click.option(
    "--persona",
    "-p",
    help="Persona to view (uses active persona if not specified)",
)
@click.option(
    "--min-confidence",
    "-c",
    type=float,
    default=0.3,
    help="Minimum confidence threshold (default: 0.3)",
)
@click.option(
    "--limit",
    "-l",
    type=int,
    default=20,
    help="Maximum number of topics to show (default: 20)",
)
@click.option(
    "--format",
    "-f",
    "output_format",
    type=click.Choice(FORMAT_CHOICES + ["text"], case_sensitive=False),
    default="text",
    help="Output format",
)
def list_topics(
    persona: str | None,
    min_confidence: float,
    limit: int,
    output_format: str,
) -> None:
    """List topics from interest profile.

    \b
    Examples:
        ragged memory topics
        ragged memory topics --min-confidence 0.5
        ragged memory topics --persona researcher --limit 10
    """
    try:
        # Use active persona if not specified
        persona = persona or _get_active_persona()

        if not persona:
            console.print(
                "[bold red]✗[/bold red] No persona specified and no active persona set."
            )
            console.print("[dim]Use --persona or set an active persona first[/dim]")
            sys.exit(1)

        # Get behaviour learner
        settings = get_settings()
        data_dir = Path(settings.data_dir)
        learner = create_behaviour_learner(data_dir / "memory")

        profile = learner.profile_manager.get_profile(persona)
        topics = profile.get_top_topics(limit=limit, min_confidence=min_confidence)

        if not topics:
            console.print(
                f"\n[yellow]No topics found with confidence >= {min_confidence}[/yellow]\n"
            )
            return

        topics_data = []
        for topic in topics:
            topics_data.append(
                {
                    "topic": topic.topic,
                    "confidence": round(topic.confidence, 3),
                    "frequency": topic.frequency,
                    "recency": round(topic.recency, 3),
                    "related_docs": len(topic.related_documents),
                    "related_topics": len(topic.co_occurring_topics),
                }
            )

        if output_format == "text":
            console.print(f"\n[bold]Topics for {persona}[/bold] (showing {len(topics)})\n")

            for idx, data in enumerate(topics_data, start=1):
                console.print(
                    f"{idx}. [bold]{data['topic']}[/bold] (conf: {data['confidence']:.2f}, "
                    f"freq: {data['frequency']}, rec: {data['recency']:.2f})"
                )
                console.print(
                    f"   {data['related_docs']} docs, {data['related_topics']} related topics"
                )
            console.print()
        else:
            print_formatted(
                topics_data,
                format_type=output_format,  # type: ignore
                title="Topics",
                console=console,
            )

    except Exception as e:
        console.print(f"[bold red]✗[/bold red] Failed to list topics: {e}")
        logger.error(f"List topics failed: {e}", exc_info=True)
        sys.exit(1)


@memory.command("topic-info")
@click.argument("topic_name")
@click.option(
    "--persona",
    "-p",
    help="Persona to query (uses active persona if not specified)",
)
@click.option(
    "--format",
    "-f",
    "output_format",
    type=click.Choice(FORMAT_CHOICES + ["text"], case_sensitive=False),
    default="text",
    help="Output format",
)
def show_topic_info(topic_name: str, persona: str | None, output_format: str) -> None:
    """Show detailed information about a topic.

    \b
    Examples:
        ragged memory topic-info "RAG"
        ragged memory topic-info "machine learning" --persona researcher
    """
    try:
        # Use active persona if not specified
        persona = persona or _get_active_persona()

        if not persona:
            console.print(
                "[bold red]✗[/bold red] No persona specified and no active persona set."
            )
            console.print("[dim]Use --persona or set an active persona first[/dim]")
            sys.exit(1)

        # Get behaviour learner
        settings = get_settings()
        data_dir = Path(settings.data_dir)
        learner = create_behaviour_learner(data_dir / "memory")

        profile = learner.profile_manager.get_profile(persona)
        topic = profile.get_topic(topic_name)

        if not topic:
            console.print(
                f"\n[yellow]Topic '{topic_name}' not found in profile for {persona}[/yellow]\n"
            )
            return

        topic_data = {
            "topic": topic.topic,
            "confidence": round(topic.confidence, 3),
            "frequency": topic.frequency,
            "recency": round(topic.recency, 3),
            "first_seen": topic.first_seen.isoformat(),
            "last_seen": topic.last_seen.isoformat(),
            "related_documents": topic.related_documents,
            "co_occurring_topics": topic.co_occurring_topics,
        }

        if output_format == "text":
            from datetime import datetime

            console.print(f"\n[bold]Topic: {topic.topic}[/bold]\n")
            console.print(f"Confidence: {topic.confidence:.3f}")
            console.print(f"Frequency: {topic.frequency}")
            console.print(f"Recency: {topic.recency:.3f}")
            console.print(
                f"First Seen: {topic.first_seen.strftime('%Y-%m-%d %H:%M')}"
            )
            console.print(
                f"Last Seen: {topic.last_seen.strftime('%Y-%m-%d %H:%M')} ({_format_time_ago(topic.last_seen)})"
            )

            if topic.related_documents:
                console.print(f"\n[bold]Related Documents ({len(topic.related_documents)}):[/bold]")
                for doc in topic.related_documents[:10]:  # Show first 10
                    console.print(f"  • {doc}")
                if len(topic.related_documents) > 10:
                    console.print(f"  ... and {len(topic.related_documents) - 10} more")

            if topic.co_occurring_topics:
                console.print(f"\n[bold]Co-occurring Topics ({len(topic.co_occurring_topics)}):[/bold]")
                sorted_topics = sorted(
                    topic.co_occurring_topics.items(),
                    key=lambda x: x[1],
                    reverse=True,
                )
                for related_topic, count in sorted_topics[:10]:  # Show top 10
                    console.print(f"  • {related_topic} ({count} times)")
                if len(topic.co_occurring_topics) > 10:
                    console.print(f"  ... and {len(topic.co_occurring_topics) - 10} more")

            console.print()
        else:
            print_formatted(
                [topic_data],
                format_type=output_format,  # type: ignore
                title="Topic Information",
                console=console,
            )

    except Exception as e:
        console.print(f"[bold red]✗[/bold red] Failed to show topic info: {e}")
        logger.error(f"Show topic info failed: {e}", exc_info=True)
        sys.exit(1)


@memory.command("related-topics")
@click.argument("topic_name")
@click.option(
    "--persona",
    "-p",
    help="Persona to query (uses active persona if not specified)",
)
@click.option(
    "--limit",
    "-l",
    type=int,
    default=10,
    help="Maximum number of related topics to show (default: 10)",
)
def show_related_topics(topic_name: str, persona: str | None, limit: int) -> None:
    """Show topics that co-occur with the specified topic.

    \b
    Examples:
        ragged memory related-topics "RAG"
        ragged memory related-topics "machine learning" --limit 5
    """
    try:
        # Use active persona if not specified
        persona = persona or _get_active_persona()

        if not persona:
            console.print(
                "[bold red]✗[/bold red] No persona specified and no active persona set."
            )
            console.print("[dim]Use --persona or set an active persona first[/dim]")
            sys.exit(1)

        # Get behaviour learner
        settings = get_settings()
        data_dir = Path(settings.data_dir)
        learner = create_behaviour_learner(data_dir / "memory")

        profile = learner.profile_manager.get_profile(persona)
        topic = profile.get_topic(topic_name)

        if not topic:
            console.print(
                f"\n[yellow]Topic '{topic_name}' not found in profile for {persona}[/yellow]\n"
            )
            return

        if not topic.co_occurring_topics:
            console.print(
                f"\n[yellow]No related topics found for '{topic_name}'[/yellow]\n"
            )
            return

        # Sort by count (descending)
        sorted_topics = sorted(
            topic.co_occurring_topics.items(),
            key=lambda x: x[1],
            reverse=True,
        )[:limit]

        console.print(f"\n[bold]Topics related to '{topic.topic}':[/bold]\n")

        for idx, (related_topic, count) in enumerate(sorted_topics, start=1):
            # Get confidence for related topic if it exists
            related_info = profile.get_topic(related_topic)
            if related_info:
                console.print(
                    f"{idx}. {related_topic} "
                    f"(co-occurred {count} times, confidence: {related_info.confidence:.2f})"
                )
            else:
                console.print(f"{idx}. {related_topic} (co-occurred {count} times)")

        console.print()

    except Exception as e:
        console.print(f"[bold red]✗[/bold red] Failed to show related topics: {e}")
        logger.error(f"Show related topics failed: {e}", exc_info=True)
        sys.exit(1)


@memory.command("forget-topic")
@click.argument("topic_name")
@click.option(
    "--persona",
    "-p",
    help="Persona to modify (uses active persona if not specified)",
)
@click.option(
    "--yes",
    "-y",
    is_flag=True,
    help="Skip confirmation prompt",
)
def forget_topic(topic_name: str, persona: str | None, yes: bool) -> None:
    """Remove topic from interest profile (GDPR right to erasure).

    \b
    Examples:
        ragged memory forget-topic "RAG"
        ragged memory forget-topic "machine learning" --persona researcher --yes
    """
    try:
        # Use active persona if not specified
        persona = persona or _get_active_persona()

        if not persona:
            console.print(
                "[bold red]✗[/bold red] No persona specified and no active persona set."
            )
            console.print("[dim]Use --persona or set an active persona first[/dim]")
            sys.exit(1)

        # Get behaviour learner
        settings = get_settings()
        data_dir = Path(settings.data_dir)
        learner = create_behaviour_learner(data_dir / "memory")

        # Check if topic exists
        profile = learner.profile_manager.get_profile(persona)
        topic = profile.get_topic(topic_name)

        if not topic:
            console.print(
                f"\n[yellow]Topic '{topic_name}' not found in profile for {persona}[/yellow]\n"
            )
            return

        # Confirm deletion
        if not yes:
            console.print(f"\n[yellow]About to remove topic:[/yellow] [bold]{topic.topic}[/bold]")
            console.print(f"Persona: {persona}")
            console.print(f"Frequency: {topic.frequency}")
            console.print(f"Confidence: {topic.confidence:.3f}")
            console.print("\n[bold red]⚠ This action cannot be undone![/bold red]")

            if not click.confirm("\nContinue?"):
                console.print("Cancelled.")
                return

        # Remove topic
        removed = learner.forget_topic(persona, topic_name)

        if removed:
            console.print(
                f"\n[green]✓[/green] Removed topic '[bold]{topic_name}[/bold]' from {persona}\n"
            )
        else:
            console.print(
                f"\n[yellow]Topic '{topic_name}' not found (may have been already removed)[/yellow]\n"
            )

    except Exception as e:
        console.print(f"[bold red]✗[/bold red] Failed to forget topic: {e}")
        logger.error(f"Forget topic failed: {e}", exc_info=True)
        sys.exit(1)


def _format_time_ago(timestamp) -> str:
    """Format timestamp as human-readable 'time ago' string."""
    from datetime import datetime

    now = datetime.now()
    diff = now - timestamp

    if diff.days > 365:
        years = diff.days // 365
        return f"{years}y ago" if years > 1 else "1y ago"
    elif diff.days > 30:
        months = diff.days // 30
        return f"{months}mo ago" if months > 1 else "1mo ago"
    elif diff.days > 0:
        return f"{diff.days}d ago" if diff.days > 1 else "1d ago"
    elif diff.seconds > 3600:
        hours = diff.seconds // 3600
        return f"{hours}h ago" if hours > 1 else "1h ago"
    elif diff.seconds > 60:
        minutes = diff.seconds // 60
        return f"{minutes}m ago" if minutes > 1 else "1m ago"
    else:
        return "just now"
