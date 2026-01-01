"""
Event Publisher - Phase V

Publishes events to Kafka topics via Dapr Pub/Sub.
Implements user_id partitioning and event_id generation for idempotency.

Based on: .claude/skills/kafka-event-driven
"""

import logging
from typing import Optional
from src.integrations.dapr_client import get_dapr_client
from src.events.schemas import (
    TaskCompletedEvent,
    ReminderScheduledEvent,
    TaskUpdatedEvent
)

logger = logging.getLogger(__name__)


class EventPublisher:
    """
    Event publisher for Kafka topics via Dapr Pub/Sub.

    Topics:
    - task-events: Task completion events (consumed by Recurring Task Service)
    - reminders: Reminder scheduling events (consumed by Notification Service)
    - task-updates: Task update events (consumed by Audit Service - optional)
    """

    def __init__(self):
        self.dapr = get_dapr_client()

    async def publish_task_completed(
        self,
        event: TaskCompletedEvent
    ) -> None:
        """
        Publish task.completed event to task-events topic.

        Args:
            event: TaskCompletedEvent with user_id, task_id, and payload

        Raises:
            httpx.HTTPStatusError: If publish fails
        """
        await self.dapr.publish_event(
            topic="task-events",
            event_data=event.model_dump(),
            user_id=event.user_id  # Partition by user_id
        )
        logger.info(f"Published task.completed event: task_id={event.task_id}, user_id={event.user_id}")

    async def publish_reminder_scheduled(
        self,
        event: ReminderScheduledEvent
    ) -> None:
        """
        Publish reminder.scheduled event to reminders topic.

        Args:
            event: ReminderScheduledEvent with user_id, task_id, and payload

        Raises:
            httpx.HTTPStatusError: If publish fails
        """
        await self.dapr.publish_event(
            topic="reminders",
            event_data=event.model_dump(),
            user_id=event.user_id  # Partition by user_id
        )
        logger.info(f"Published reminder.scheduled event: task_id={event.task_id}, reminder_at={event.payload.reminder_at}")

    async def publish_task_updated(
        self,
        event: TaskUpdatedEvent
    ) -> None:
        """
        Publish task.updated event to task-updates topic.

        Args:
            event: TaskUpdatedEvent with user_id, task_id, and payload

        Raises:
            httpx.HTTPStatusError: If publish fails
        """
        await self.dapr.publish_event(
            topic="task-updates",
            event_data=event.model_dump(),
            user_id=event.user_id  # Partition by user_id
        )
        logger.info(f"Published task.updated event: task_id={event.task_id}, user_id={event.user_id}")


# Singleton instance
_event_publisher: Optional[EventPublisher] = None


def get_event_publisher() -> EventPublisher:
    """Get singleton EventPublisher instance."""
    global _event_publisher
    if _event_publisher is None:
        _event_publisher = EventPublisher()
    return _event_publisher
