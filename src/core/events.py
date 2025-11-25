"""Event bus for component communication.

Phase 0 Infrastructure: Simple pub/sub event system enabling:
- Real-time UI updates (WebSocket notifications)
- Agent task coordination (multi-step workflow events)
- Audit logging (compliance and debugging)
- Graceful degradation (error propagation)

Design Principles:
- Async-first with synchronous convenience wrapper
- Typed events via dataclasses for compile-time safety
- Decoupled publishers and subscribers
- Thread-safe for concurrent access

Usage:
    >>> from ragged.core.events import event_bus, QueryEvent
    >>>
    >>> # Subscribe to events
    >>> @event_bus.subscribe("query.completed")
    ... async def on_query_completed(event: QueryEvent):
    ...     print(f"Query completed: {event.query_text}")
    >>>
    >>> # Publish events
    >>> await event_bus.publish(QueryEvent(
    ...     event_type="query.completed",
    ...     query_text="What is RAG?",
    ...     latency_ms=150
    ... ))
"""

import asyncio
import logging
import threading
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Coroutine, TypeVar

logger = logging.getLogger(__name__)


# Type variable for event types
E = TypeVar("E", bound="Event")


class EventPriority(Enum):
    """Event processing priority levels."""

    LOW = 0
    NORMAL = 1
    HIGH = 2
    CRITICAL = 3


@dataclass
class Event(ABC):
    """Base class for all events.

    All events must inherit from this class and define an event_type.
    Events are immutable after creation for thread safety.

    Attributes:
        event_type: Dot-separated event type (e.g., "query.completed")
        event_id: Unique event identifier (auto-generated)
        timestamp: Event creation timestamp (auto-generated)
        priority: Processing priority (default: NORMAL)
        metadata: Optional event metadata
    """

    event_type: str
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = field(default_factory=datetime.now)
    priority: EventPriority = EventPriority.NORMAL
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert event to dictionary for serialisation.

        Returns:
            Dictionary representation of the event
        """
        return {
            "event_type": self.event_type,
            "event_id": self.event_id,
            "timestamp": self.timestamp.isoformat(),
            "priority": self.priority.name,
            "metadata": self.metadata,
        }


# === Domain Events ===


@dataclass
class QueryEvent(Event):
    """Event for query lifecycle.

    Published when queries are submitted, processed, or completed.

    Attributes:
        query_text: The query text
        session_id: Session that initiated the query
        latency_ms: Query processing latency (if completed)
        result_count: Number of results returned (if completed)
        error: Error message (if failed)
    """

    query_text: str = ""
    session_id: str = ""
    latency_ms: int = 0
    result_count: int = 0
    error: str | None = None


@dataclass
class DocumentEvent(Event):
    """Event for document lifecycle.

    Published when documents are ingested, updated, or deleted.

    Attributes:
        document_id: Document identifier
        document_path: File path (for ingestion events)
        action: Action performed (ingest, update, delete)
        chunk_count: Number of chunks created (for ingestion)
    """

    document_id: str = ""
    document_path: str = ""
    action: str = ""  # "ingest", "update", "delete"
    chunk_count: int = 0


@dataclass
class AgentEvent(Event):
    """Event for agent task lifecycle.

    Published when agents start, progress, or complete tasks.

    Attributes:
        agent_id: Agent identifier
        task_id: Task identifier
        step: Current step number
        total_steps: Total steps in task
        status: Task status (started, progress, completed, failed)
        output: Step output (for progress/completion)
    """

    agent_id: str = ""
    task_id: str = ""
    step: int = 0
    total_steps: int = 0
    status: str = ""  # "started", "progress", "completed", "failed"
    output: Any = None


@dataclass
class SystemEvent(Event):
    """Event for system-level notifications.

    Published for health changes, configuration updates, and errors.

    Attributes:
        component: System component name
        status: Component status
        message: Human-readable message
        severity: Event severity (info, warning, error, critical)
    """

    component: str = ""
    status: str = ""
    message: str = ""
    severity: str = "info"  # "info", "warning", "error", "critical"


@dataclass
class AuditEvent(Event):
    """Event for audit logging (compliance).

    Published for security-relevant actions.

    Attributes:
        user_id: User who performed the action
        action: Action performed
        resource: Resource affected
        outcome: Action outcome (success, denied, failed)
        ip_address: Client IP address (if available)
    """

    user_id: str = ""
    action: str = ""
    resource: str = ""
    outcome: str = ""  # "success", "denied", "failed"
    ip_address: str = ""


# === Event Handler Types ===


# Async handler type
AsyncEventHandler = Callable[[Event], Coroutine[Any, Any, None]]

# Sync handler type
SyncEventHandler = Callable[[Event], None]

# Combined handler type
EventHandler = AsyncEventHandler | SyncEventHandler


@dataclass
class Subscription:
    """Represents an event subscription.

    Attributes:
        subscription_id: Unique subscription identifier
        event_pattern: Event type pattern (supports wildcards: "query.*")
        handler: Event handler function
        is_async: Whether handler is async
        priority: Handler priority (higher = called first)
    """

    subscription_id: str
    event_pattern: str
    handler: EventHandler
    is_async: bool
    priority: int = 0


class EventBus:
    """Central event dispatcher for ragged components.

    Provides pub/sub messaging between components with:
    - Pattern matching for event types (e.g., "query.*")
    - Async and sync handler support
    - Thread-safe subscription management
    - Priority-based handler ordering

    Thread Safety:
        All public methods are thread-safe. The event bus uses a lock
        for subscription management and asyncio for event dispatch.

    Example:
        >>> bus = EventBus()
        >>>
        >>> # Subscribe with decorator
        >>> @bus.subscribe("query.*")
        ... async def handle_query(event: QueryEvent):
        ...     print(f"Query event: {event.event_type}")
        >>>
        >>> # Publish event
        >>> await bus.publish(QueryEvent(
        ...     event_type="query.completed",
        ...     query_text="test"
        ... ))
    """

    def __init__(self):
        """Initialise event bus."""
        self._subscriptions: dict[str, list[Subscription]] = {}
        self._lock = threading.RLock()
        self._event_history: list[Event] = []
        self._max_history = 1000

        logger.debug("EventBus initialised")

    def subscribe(
        self,
        event_pattern: str,
        priority: int = 0,
    ) -> Callable[[EventHandler], EventHandler]:
        """Decorator to subscribe a handler to events.

        Args:
            event_pattern: Event type pattern (e.g., "query.*", "document.ingest")
            priority: Handler priority (higher = called first)

        Returns:
            Decorator function

        Example:
            >>> @event_bus.subscribe("query.completed")
            ... async def on_query(event: QueryEvent):
            ...     print(event.query_text)
        """
        def decorator(handler: EventHandler) -> EventHandler:
            self.add_subscriber(event_pattern, handler, priority)
            return handler
        return decorator

    def add_subscriber(
        self,
        event_pattern: str,
        handler: EventHandler,
        priority: int = 0,
    ) -> str:
        """Add a subscriber to the event bus.

        Args:
            event_pattern: Event type pattern
            handler: Event handler function
            priority: Handler priority

        Returns:
            Subscription ID for later removal
        """
        subscription_id = str(uuid.uuid4())
        is_async = asyncio.iscoroutinefunction(handler)

        subscription = Subscription(
            subscription_id=subscription_id,
            event_pattern=event_pattern,
            handler=handler,
            is_async=is_async,
            priority=priority,
        )

        with self._lock:
            if event_pattern not in self._subscriptions:
                self._subscriptions[event_pattern] = []
            self._subscriptions[event_pattern].append(subscription)
            # Sort by priority (descending)
            self._subscriptions[event_pattern].sort(
                key=lambda s: s.priority,
                reverse=True
            )

        logger.debug(
            f"Added subscription {subscription_id} for pattern '{event_pattern}' "
            f"(async={is_async}, priority={priority})"
        )

        return subscription_id

    def remove_subscriber(self, subscription_id: str) -> bool:
        """Remove a subscriber by ID.

        Args:
            subscription_id: Subscription ID returned from add_subscriber

        Returns:
            True if subscription was found and removed
        """
        with self._lock:
            for pattern, subs in self._subscriptions.items():
                for sub in subs:
                    if sub.subscription_id == subscription_id:
                        subs.remove(sub)
                        logger.debug(f"Removed subscription {subscription_id}")
                        return True

        logger.warning(f"Subscription {subscription_id} not found")
        return False

    async def publish(self, event: Event) -> int:
        """Publish an event to all matching subscribers.

        Args:
            event: Event to publish

        Returns:
            Number of handlers that processed the event
        """
        # Record in history
        self._record_event(event)

        # Find matching subscriptions
        handlers = self._get_matching_handlers(event.event_type)

        if not handlers:
            logger.debug(f"No handlers for event type '{event.event_type}'")
            return 0

        # Execute handlers
        handler_count = 0
        for subscription in handlers:
            try:
                if subscription.is_async:
                    await subscription.handler(event)
                else:
                    subscription.handler(event)
                handler_count += 1
            except Exception as e:
                logger.error(
                    f"Error in event handler for '{event.event_type}': {e}",
                    exc_info=True
                )

        logger.debug(
            f"Published event '{event.event_type}' to {handler_count} handlers"
        )

        return handler_count

    def publish_sync(self, event: Event) -> int:
        """Synchronous wrapper for publish.

        Use this when calling from synchronous code.
        Creates a new event loop if none exists.

        Args:
            event: Event to publish

        Returns:
            Number of handlers that processed the event
        """
        try:
            loop = asyncio.get_running_loop()
            # If we're in an async context, schedule the coroutine
            future = asyncio.ensure_future(self.publish(event))
            # Note: We can't wait for it here without blocking
            return 0
        except RuntimeError:
            # No running loop - create one
            return asyncio.run(self.publish(event))

    def _get_matching_handlers(self, event_type: str) -> list[Subscription]:
        """Get all handlers matching an event type.

        Supports wildcard patterns:
        - "query.*" matches "query.started", "query.completed"
        - "*" matches all events

        Args:
            event_type: Event type to match

        Returns:
            List of matching subscriptions, sorted by priority
        """
        handlers: list[Subscription] = []

        with self._lock:
            for pattern, subs in self._subscriptions.items():
                if self._pattern_matches(pattern, event_type):
                    handlers.extend(subs)

        # Sort by priority (descending)
        handlers.sort(key=lambda s: s.priority, reverse=True)
        return handlers

    @staticmethod
    def _pattern_matches(pattern: str, event_type: str) -> bool:
        """Check if a pattern matches an event type.

        Args:
            pattern: Event pattern (e.g., "query.*", "document.ingest")
            event_type: Actual event type

        Returns:
            True if pattern matches event type
        """
        if pattern == "*":
            return True

        if pattern == event_type:
            return True

        # Wildcard matching
        if pattern.endswith(".*"):
            prefix = pattern[:-2]
            return event_type.startswith(prefix + ".")

        return False

    def _record_event(self, event: Event) -> None:
        """Record event in history for debugging.

        Args:
            event: Event to record
        """
        with self._lock:
            self._event_history.append(event)
            # Trim history if too long
            if len(self._event_history) > self._max_history:
                self._event_history = self._event_history[-self._max_history:]

    def get_history(
        self,
        event_type: str | None = None,
        limit: int = 100
    ) -> list[Event]:
        """Get recent event history.

        Args:
            event_type: Filter by event type (optional)
            limit: Maximum events to return

        Returns:
            List of recent events (newest first)
        """
        with self._lock:
            history = list(reversed(self._event_history))

            if event_type:
                history = [e for e in history if e.event_type == event_type]

            return history[:limit]

    def clear_history(self) -> None:
        """Clear event history."""
        with self._lock:
            self._event_history.clear()
        logger.debug("Event history cleared")

    def get_subscription_count(self) -> int:
        """Get total number of subscriptions.

        Returns:
            Total subscription count
        """
        with self._lock:
            return sum(len(subs) for subs in self._subscriptions.values())


# === Global Event Bus Instance ===


# Singleton event bus for application-wide use
_event_bus: EventBus | None = None
_event_bus_lock = threading.Lock()


def get_event_bus() -> EventBus:
    """Get the global event bus instance.

    Returns the same EventBus instance on subsequent calls.
    Thread-safe singleton pattern.

    Returns:
        EventBus: The global event bus instance

    Example:
        >>> from ragged.core.events import get_event_bus
        >>> bus = get_event_bus()
        >>> await bus.publish(QueryEvent(event_type="query.started"))
    """
    global _event_bus

    if _event_bus is None:
        with _event_bus_lock:
            if _event_bus is None:
                _event_bus = EventBus()
                logger.info("Global EventBus created")

    return _event_bus


def reset_event_bus() -> None:
    """Reset the global event bus (for testing).

    Creates a new EventBus instance, discarding all subscriptions.
    """
    global _event_bus

    with _event_bus_lock:
        _event_bus = EventBus()
        logger.info("Global EventBus reset")


# Convenience alias
event_bus = get_event_bus()
