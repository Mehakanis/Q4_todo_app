"""
Event Schema Models - Phase V

Pydantic models for all Kafka event types published by the Task Service.
These schemas match the contracts defined in specs/007-phase5-cloud-deployment/contracts/event-schemas.yaml
"""

from typing import Optional, Dict, Any
from pydantic import BaseModel, Field, field_validator
from datetime import datetime
import uuid


class EventSchema(BaseModel):
    """
    Base event schema - all events extend this.

    Common fields across all event types:
    - event_id: Unique identifier for idempotency
    - event_type: Discriminator for event type
    - event_version: Schema version for evolution
    - timestamp: Event creation time (UTC)
    - user_id: User context for isolation and partitioning
    - task_id: Task database primary key
    - payload: Event-specific data
    """

    event_id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        description="Unique event identifier (UUID v4) for idempotency"
    )
    event_type: str = Field(
        ...,
        description="Event type discriminator (task.completed, reminder.scheduled, task.updated)"
    )
    event_version: str = Field(
        default="1.0",
        pattern=r"^\d+\.\d+$",
        description="Schema version (major.minor format)"
    )
    timestamp: str = Field(
        default_factory=lambda: datetime.utcnow().isoformat() + "Z",
        description="Event creation time in UTC (ISO 8601 format with 'Z' suffix)"
    )
    user_id: str = Field(
        ...,
        description="User ID for event isolation and Kafka partitioning"
    )
    task_id: int = Field(
        ...,
        gt=0,
        description="Task database primary key"
    )
    payload: Dict[str, Any] = Field(
        ...,
        description="Event-specific payload (schema varies by event_type)"
    )

    @field_validator('timestamp')
    @classmethod
    def validate_timestamp_utc(cls, v: str) -> str:
        """Ensure timestamp is ISO 8601 UTC format with 'Z' suffix."""
        if not v.endswith('Z'):
            raise ValueError("Timestamp must be in UTC with 'Z' suffix")
        try:
            datetime.fromisoformat(v.replace('Z', '+00:00'))
        except ValueError:
            raise ValueError("Timestamp must be valid ISO 8601 format")
        return v

    @field_validator('user_id')
    @classmethod
    def validate_user_id_not_empty(cls, v: str) -> str:
        """Ensure user_id is not empty (required for partitioning)."""
        if not v or not v.strip():
            raise ValueError("user_id must not be empty")
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "event_id": "550e8400-e29b-41d4-a716-446655440000",
                "event_type": "task.completed",
                "event_version": "1.0",
                "timestamp": "2025-12-29T12:00:00Z",
                "user_id": "user-123",
                "task_id": 456,
                "payload": {}
            }
        }


class TaskCompletedEventPayload(BaseModel):
    """
    Payload for task.completed event.

    Published when: Recurring task is marked complete
    Topic: task-events
    Consumer: Recurring Task Service
    """

    task_title: str = Field(
        ...,
        description="Task title for logging/debugging"
    )
    completed_at: str = Field(
        ...,
        description="When task was marked complete (UTC ISO 8601)"
    )
    recurring_pattern: Optional[str] = Field(
        None,
        description="RRULE string for recurring tasks (NULL for non-recurring)"
    )
    recurring_end_date: Optional[str] = Field(
        None,
        description="When recurring should stop (NULL for infinite recurrence)"
    )
    next_occurrence_due: Optional[str] = Field(
        None,
        description="Calculated next occurrence timestamp (UTC ISO 8601)"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "task_title": "Daily standup",
                "completed_at": "2025-12-29T12:00:00Z",
                "recurring_pattern": "FREQ=DAILY;INTERVAL=1",
                "recurring_end_date": None,
                "next_occurrence_due": "2025-12-30T09:00:00Z"
            }
        }


class TaskCompletedEvent(EventSchema):
    """
    Task Completion Event (v1.0)

    Published when recurring task is completed.
    Consumed by Recurring Task Service to create next occurrence.
    """

    event_type: str = Field(
        default="task.completed",
        description="Fixed event type"
    )
    payload: TaskCompletedEventPayload

    class Config:
        json_schema_extra = {
            "example": {
                "event_id": "550e8400-e29b-41d4-a716-446655440000",
                "event_type": "task.completed",
                "event_version": "1.0",
                "timestamp": "2025-12-29T12:00:00Z",
                "user_id": "user-123",
                "task_id": 456,
                "payload": {
                    "task_title": "Daily standup",
                    "completed_at": "2025-12-29T12:00:00Z",
                    "recurring_pattern": "FREQ=DAILY;INTERVAL=1",
                    "recurring_end_date": None,
                    "next_occurrence_due": "2025-12-30T09:00:00Z"
                }
            }
        }


class ReminderScheduledEventPayload(BaseModel):
    """
    Payload for reminder.scheduled event.

    Published when: Task with due_date is created
    Topic: reminders
    Consumer: Notification Service
    """

    task_title: str = Field(
        ...,
        description="Task title to include in reminder notification"
    )
    task_description: Optional[str] = Field(
        None,
        description="Task description to include in reminder (optional)"
    )
    reminder_at: str = Field(
        ...,
        description="When reminder should be sent (UTC ISO 8601)"
    )
    notification_type: str = Field(
        default="email",
        description="Notification delivery method (email or push)"
    )
    user_email: str = Field(
        ...,
        description="User's email address for notification delivery"
    )
    due_date: str = Field(
        ...,
        description="Task due date for context (displayed in reminder)"
    )

    @field_validator('notification_type')
    @classmethod
    def validate_notification_type(cls, v: str) -> str:
        """Validate notification_type is one of: email, push."""
        if v not in ['email', 'push']:
            raise ValueError("notification_type must be 'email' or 'push'")
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "task_title": "Submit Q4 report",
                "task_description": "Include revenue, expenses, and forecasts",
                "reminder_at": "2025-12-31T16:00:00Z",
                "notification_type": "email",
                "user_email": "user@example.com",
                "due_date": "2025-12-31T17:00:00Z"
            }
        }


class ReminderScheduledEvent(EventSchema):
    """
    Reminder Scheduled Event (v1.0)

    Published when task with due_date is created.
    Consumed by Notification Service to schedule reminder delivery.
    """

    event_type: str = Field(
        default="reminder.scheduled",
        description="Fixed event type"
    )
    payload: ReminderScheduledEventPayload

    class Config:
        json_schema_extra = {
            "example": {
                "event_id": "660e8400-e29b-41d4-a716-446655440001",
                "event_type": "reminder.scheduled",
                "event_version": "1.0",
                "timestamp": "2025-12-29T12:00:00Z",
                "user_id": "user-123",
                "task_id": 789,
                "payload": {
                    "task_title": "Submit Q4 report",
                    "task_description": "Include revenue, expenses, and forecasts",
                    "reminder_at": "2025-12-31T16:00:00Z",
                    "notification_type": "email",
                    "user_email": "user@example.com",
                    "due_date": "2025-12-31T17:00:00Z"
                }
            }
        }


class TaskUpdatedEventPayload(BaseModel):
    """
    Payload for task.updated event.

    Published when: Task fields are modified
    Topic: task-updates
    Consumer: Audit Service (optional)
    """

    updated_fields: Dict[str, Any] = Field(
        ...,
        description="Fields that were modified (key-value pairs)"
    )
    previous_values: Dict[str, Any] = Field(
        ...,
        description="Previous values before update (for audit trail)"
    )
    updated_at: str = Field(
        ...,
        description="When task was updated (UTC ISO 8601)"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "updated_fields": {
                    "title": "Updated daily standup",
                    "description": "Changed meeting time"
                },
                "previous_values": {
                    "title": "Daily standup",
                    "description": "Original meeting"
                },
                "updated_at": "2025-12-29T12:30:00Z"
            }
        }


class TaskUpdatedEvent(EventSchema):
    """
    Task Updated Event (v1.0)

    Published when task fields are modified.
    Consumed by Audit Service (optional) to maintain audit trail.
    """

    event_type: str = Field(
        default="task.updated",
        description="Fixed event type"
    )
    payload: TaskUpdatedEventPayload

    class Config:
        json_schema_extra = {
            "example": {
                "event_id": "770e8400-e29b-41d4-a716-446655440002",
                "event_type": "task.updated",
                "event_version": "1.0",
                "timestamp": "2025-12-29T12:30:00Z",
                "user_id": "user-123",
                "task_id": 456,
                "payload": {
                    "updated_fields": {
                        "title": "Updated daily standup",
                        "description": "Changed meeting time"
                    },
                    "previous_values": {
                        "title": "Daily standup",
                        "description": "Original meeting"
                    },
                    "updated_at": "2025-12-29T12:30:00Z"
                }
            }
        }


# Type aliases for convenience
EventType = TaskCompletedEvent | ReminderScheduledEvent | TaskUpdatedEvent
