"""
Event Bus for Module Communication

Provides a lightweight, asynchronous pub‑sub mechanism so that
plugins and core components can communicate without tight coupling.
Supports synchronous and asynchronous subscribers, wildcard events,
and priority ordering.

Usage:
    bus = EventBus()
    bus.subscribe("scan:completed", my_handler)
    await bus.emit("scan:completed", scan_id=123)
"""

import asyncio
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set, Union
import structlog

logger = structlog.get_logger(__name__)


class EventType(str, Enum):
    """Common event types used across the framework."""
    # Scan lifecycle
    SCAN_STARTED = "scan:started"
    SCAN_COMPLETED = "scan:completed"
    SCAN_FAILED = "scan:failed"
    SCAN_CANCELLED = "scan:cancelled"

    # Module/Plugin events
    MODULE_STARTED = "module:started"
    MODULE_COMPLETED = "module:completed"
    MODULE_FAILED = "module:failed"

    # Target events
    TARGET_RESOLVED = "target:resolved"
    TARGET_INVALID = "target:invalid"

    # Data events
    ASSET_DISCOVERED = "asset:discovered"
    DATA_UPDATED = "data:updated"


@dataclass
class Event:
    """
    Represents an event with type, payload, and optional source.
    
    Attributes:
        type: Event type string (e.g., 'scan:completed').
        data: Arbitrary payload data (keyword arguments stored as dict).
        source: Optional identifier of the emitter (plugin name, 'core', etc.).
    """
    type: str
    data: Dict[str, Any] = field(default_factory=dict)
    source: str = "unknown"


# Type alias for subscriber callbacks
Subscriber = Callable[[Event], Union[None, "asyncio.Coroutine"]]


class EventBus:
    """
    Asynchronous event bus with wildcard and priority support.

    Subscribers can register for specific event types or use '*' to
    listen to all events. Handlers may be synchronous or async.
    Emitted events are delivered to all matching subscribers in order
    of priority (lower number = higher priority).
    """

    def __init__(self):
        # Mapping: event_type -> list of (priority, subscriber_id, callback)
        self._subscribers: Dict[str, List[tuple]] = {}
        self._counter = 0  # for generating unique subscriber IDs

    def subscribe(
        self,
        event_type: str,
        callback: Subscriber,
        priority: int = 100,
    ) -> Callable[[], None]:
        """
        Register a callback for an event type.

        Args:
            event_type: The event to listen for (e.g., 'scan:completed' or '*').
            callback: Function or coroutine to call. If async, it will be awaited.
            priority: Lower numbers are called first.

        Returns:
            An unsubscribe function that removes the subscription.
        """
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []

        sub_id = self._counter
        self._counter += 1
        entry = (priority, sub_id, callback)
        self._subscribers[event_type].append(entry)
        # Keep sorted by priority then insertion order (counter preserves FIFO for same priority)
        self._subscribers[event_type].sort(key=lambda x: (x[0], x[1]))

        def unsubscribe():
            try:
                self._subscribers[event_type].remove(entry)
                if not self._subscribers[event_type]:
                    del self._subscribers[event_type]
            except (ValueError, KeyError):
                pass

        return unsubscribe

    async def emit(self, event_type: str, source: str = "core", **data) -> None:
        """
        Emit an event to all matching subscribers.

        Subscribers listening on the exact event type and those on '*'
        are called. Each callback may be synchronous or async; async ones
        are awaited.

        Args:
            event_type: The event type string.
            source: Identifier of the emitter.
            **data: Keyword arguments passed as event payload.
        """
        event = Event(type=event_type, data=data, source=source)
        matching_types = [event_type, "*"]

        tasks = []
        for etype in matching_types:
            if etype in self._subscribers:
                for _, _, callback in self._subscribers[etype]:
                    try:
                        if asyncio.iscoroutinefunction(callback):
                            tasks.append(asyncio.create_task(callback(event)))
                        else:
                            callback(event)
                    except Exception:
                        logger.exception("Event handler error", event_type=event_type)

        if tasks:
            # Wait for async handlers to complete, but don't let one failure kill the bus
            results = await asyncio.gather(*tasks, return_exceptions=True)
            for i, res in enumerate(results):
                if isinstance(res, Exception):
                    logger.error("Async event handler raised exception", exc_info=res)

    def subscriber_count(self, event_type: Optional[str] = None) -> int:
        """Return number of subscribers for a given event type or total if None."""
        if event_type:
            return len(self._subscribers.get(event_type, []))
        return sum(len(v) for v in self._subscribers.values())

    def clear(self):
        """Remove all subscriptions."""
        self._subscribers.clear()