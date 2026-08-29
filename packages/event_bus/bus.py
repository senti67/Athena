"""
ATHENA Event Bus Architecture
Provides an asynchronous in-memory event bus for high-speed local processing
and an abstraction layer for Apache Kafka production streaming.
"""

import asyncio
from typing import Callable, Coroutine, Dict, List, Optional
from packages.logging.logger import get_logger
from packages.schemas.events import Event, EventType

logger = get_logger("athena.event_bus")

EventHandler = Callable[[Event], Coroutine[None, None, None]]


class EventBus:
    """High-performance Async Event Bus with topic subscriptions."""

    def __init__(self):
        self._subscribers: Dict[EventType, List[EventHandler]] = {
            event_type: [] for event_type in EventType
        }
        self._global_subscribers: List[EventHandler] = []
        self._is_running = True

    def subscribe(self, event_type: EventType, handler: EventHandler):
        """Registers a listener for a specific event type."""
        if event_type in self._subscribers:
            self._subscribers[event_type].append(handler)
            logger.debug(f"Subscribed handler to {event_type.value}")

    def subscribe_all(self, handler: EventHandler):
        """Registers a global listener for all events (e.g. audit loggers, WebSockets)."""
        self._global_subscribers.append(handler)

    async def publish(self, event: Event):
        """Publishes an event asynchronously to all registered listeners."""
        if not self._is_running:
            return

        handlers = list(self._subscribers.get(event.event_type, [])) + list(
            self._global_subscribers
        )

        for handler in handlers:
            try:
                # Run each handler in an isolated async task to prevent blocking
                asyncio.create_task(self._safe_dispatch(handler, event))
            except Exception as e:
                logger.error(
                    f"Error dispatching event {event.event_type.value}: {str(e)}",
                    exc_info=True,
                )

    async def _safe_dispatch(self, handler: EventHandler, event: Event):
        try:
            await handler(event)
        except Exception as e:
            logger.error(
                f"Exception in event handler for {event.event_type.value}: {str(e)}",
                exc_info=True,
            )

    def close(self):
        self._is_running = False


# Global EventBus singleton
event_bus = EventBus()
