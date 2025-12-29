"""
Event Consumers - Phase V

Base consumer class for Dapr Pub/Sub subscriptions.
Implements idempotency checks and user isolation validation.

Based on: .claude/skills/microservices-patterns
"""

import logging
from typing import Dict, Any, Optional, Set
from abc import ABC, abstractmethod
from datetime import datetime

logger = logging.getLogger(__name__)


class EventConsumer(ABC):
    """
    Base event consumer with idempotency and user isolation.

    Subclasses must implement:
    - process_event(): Business logic for event processing
    - get_topic(): Kafka topic to subscribe to
    """

    def __init__(self):
        # In-memory idempotency tracking (replace with Dapr State Store in production)
        self._processed_events: Set[str] = set()

    @abstractmethod
    async def process_event(self, event_data: Dict[str, Any]) -> None:
        """
        Process event - implement in subclass.

        Args:
            event_data: Event payload from Kafka

        Raises:
            Exception: If processing fails
        """
        pass

    @abstractmethod
    def get_topic(self) -> str:
        """
        Get Kafka topic name.

        Returns:
            Topic name (task-events, reminders, task-updates)
        """
        pass

    def check_idempotency(self, event_id: str) -> bool:
        """
        Check if event has already been processed.

        Args:
            event_id: Event UUID

        Returns:
            True if already processed, False otherwise
        """
        if event_id in self._processed_events:
            logger.warning(f"Duplicate event detected: event_id={event_id} (skipping)")
            return True

        self._processed_events.add(event_id)
        return False

    def validate_user_isolation(self, event_data: Dict[str, Any]) -> bool:
        """
        Validate event contains user_id for user isolation.

        Args:
            event_data: Event payload

        Returns:
            True if valid, False otherwise
        """
        user_id = event_data.get("user_id")
        if not user_id:
            logger.error(f"Event missing user_id (violates user isolation)")
            return False
        return True

    async def handle_event(self, event_data: Dict[str, Any]) -> None:
        """
        Handle incoming event with idempotency and validation.

        Args:
            event_data: Event payload from Kafka

        Raises:
            Exception: If processing fails (event will be retried)
        """
        event_id = event_data.get("event_id")
        event_type = event_data.get("event_type")

        logger.info(f"Received event: event_id={event_id}, event_type={event_type}")

        # Idempotency check
        if self.check_idempotency(event_id):
            return  # Skip duplicate

        # User isolation validation
        if not self.validate_user_isolation(event_data):
            raise ValueError("Event failed user isolation validation")

        # Process event
        try:
            await self.process_event(event_data)
            logger.info(f"Event processed successfully: event_id={event_id}")
        except Exception as e:
            logger.error(f"Event processing failed: event_id={event_id}, error={str(e)}")
            raise  # Re-raise for retry mechanism


# Example consumer implementations (to be implemented in future phases)

class RecurringTaskConsumer(EventConsumer):
    """
    Consumes task.completed events from task-events topic.
    Creates next occurrence for recurring tasks.
    """

    def get_topic(self) -> str:
        return "task-events"

    async def process_event(self, event_data: Dict[str, Any]) -> None:
        """
        Process task.completed event.

        Logic:
        1. Check if task has recurring_pattern
        2. Calculate next_occurrence_due
        3. Create next task occurrence in database
        4. Validate next_occurrence_due <= recurring_end_date
        """
        # TODO: Implement in Phase 3 (User Stories)
        logger.info(f"Processing task.completed event: {event_data}")


class NotificationConsumer(EventConsumer):
    """
    Consumes reminder.scheduled events from reminders topic.
    Schedules reminder delivery via Dapr Jobs API.
    """

    def get_topic(self) -> str:
        return "reminders"

    async def process_event(self, event_data: Dict[str, Any]) -> None:
        """
        Process reminder.scheduled event.

        Logic:
        1. Extract reminder_at timestamp
        2. Schedule job via Dapr Jobs API
        3. Job will trigger at reminder_at to send email
        """
        # TODO: Implement in Phase 3 (User Stories)
        logger.info(f"Processing reminder.scheduled event: {event_data}")
