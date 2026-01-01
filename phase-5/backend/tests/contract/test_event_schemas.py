"""
Event Schema Contract Tests - Phase V

Validates that event schemas match the contracts defined in:
specs/007-phase5-cloud-deployment/contracts/event-schemas.yaml

These tests ensure backward compatibility and schema evolution compliance.
"""

import pytest
from pydantic import ValidationError
from phase_5.backend.src.events.schemas import (
    EventSchema,
    TaskCompletedEvent,
    TaskCompletedEventPayload,
    ReminderScheduledEvent,
    ReminderScheduledEventPayload,
    TaskUpdatedEvent,
    TaskUpdatedEventPayload
)


class TestBaseEventSchema:
    """Test base EventSchema validations."""

    def test_event_schema_requires_all_fields(self):
        """Base schema requires event_type, user_id, task_id, and payload."""
        with pytest.raises(ValidationError) as exc_info:
            EventSchema(
                event_type="task.completed",
                # Missing user_id, task_id, payload
            )

        errors = exc_info.value.errors()
        error_fields = [e['loc'][0] for e in errors]
        assert 'user_id' in error_fields
        assert 'task_id' in error_fields
        assert 'payload' in error_fields

    def test_event_schema_generates_defaults(self):
        """Base schema generates event_id, event_version, and timestamp by default."""
        event = EventSchema(
            event_type="task.completed",
            user_id="user-123",
            task_id=456,
            payload={}
        )

        assert event.event_id is not None  # UUID generated
        assert event.event_version == "1.0"
        assert event.timestamp.endswith('Z')  # UTC timestamp

    def test_event_schema_validates_timestamp_utc(self):
        """Timestamp must be UTC with 'Z' suffix."""
        with pytest.raises(ValidationError) as exc_info:
            EventSchema(
                event_type="task.completed",
                user_id="user-123",
                task_id=456,
                payload={},
                timestamp="2025-12-29T12:00:00"  # Missing 'Z'
            )

        assert "Timestamp must be in UTC with 'Z' suffix" in str(exc_info.value)

    def test_event_schema_validates_user_id_not_empty(self):
        """user_id must not be empty string."""
        with pytest.raises(ValidationError) as exc_info:
            EventSchema(
                event_type="task.completed",
                user_id="",  # Empty string
                task_id=456,
                payload={}
            )

        assert "user_id must not be empty" in str(exc_info.value)

    def test_event_schema_validates_task_id_positive(self):
        """task_id must be positive integer."""
        with pytest.raises(ValidationError) as exc_info:
            EventSchema(
                event_type="task.completed",
                user_id="user-123",
                task_id=0,  # Invalid: must be > 0
                payload={}
            )

        assert "greater than 0" in str(exc_info.value)


class TestTaskCompletedEvent:
    """Test TaskCompletedEvent schema contract."""

    def test_task_completed_event_valid(self):
        """Valid task.completed event passes validation."""
        event = TaskCompletedEvent(
            user_id="user-123",
            task_id=456,
            payload=TaskCompletedEventPayload(
                task_title="Daily standup",
                completed_at="2025-12-29T12:00:00Z",
                recurring_pattern="FREQ=DAILY;INTERVAL=1",
                recurring_end_date=None,
                next_occurrence_due="2025-12-30T09:00:00Z"
            )
        )

        assert event.event_type == "task.completed"
        assert event.event_version == "1.0"
        assert event.user_id == "user-123"
        assert event.task_id == 456
        assert event.payload.task_title == "Daily standup"

    def test_task_completed_event_matches_yaml_example(self):
        """Event matches the example from event-schemas.yaml."""
        # Example from specs/007-phase5-cloud-deployment/contracts/event-schemas.yaml line 129
        event = TaskCompletedEvent(
            event_id="550e8400-e29b-41d4-a716-446655440000",
            event_type="task.completed",
            event_version="1.0",
            timestamp="2025-12-29T12:00:00Z",
            user_id="user-123",
            task_id=456,
            payload=TaskCompletedEventPayload(
                task_title="Daily standup",
                completed_at="2025-12-29T12:00:00Z",
                recurring_pattern="FREQ=DAILY;INTERVAL=1",
                recurring_end_date=None,
                next_occurrence_due="2025-12-30T09:00:00Z"
            )
        )

        # Validate all fields match contract
        assert event.event_id == "550e8400-e29b-41d4-a716-446655440000"
        assert event.event_type == "task.completed"
        assert event.event_version == "1.0"
        assert event.timestamp == "2025-12-29T12:00:00Z"
        assert event.user_id == "user-123"
        assert event.task_id == 456
        assert event.payload.task_title == "Daily standup"
        assert event.payload.completed_at == "2025-12-29T12:00:00Z"
        assert event.payload.recurring_pattern == "FREQ=DAILY;INTERVAL=1"
        assert event.payload.recurring_end_date is None
        assert event.payload.next_occurrence_due == "2025-12-30T09:00:00Z"

    def test_task_completed_event_non_recurring(self):
        """Non-recurring task has NULL recurring fields."""
        event = TaskCompletedEvent(
            user_id="user-123",
            task_id=789,
            payload=TaskCompletedEventPayload(
                task_title="One-time task",
                completed_at="2025-12-29T12:00:00Z",
                recurring_pattern=None,  # NULL for non-recurring
                recurring_end_date=None,
                next_occurrence_due=None
            )
        )

        assert event.payload.recurring_pattern is None
        assert event.payload.next_occurrence_due is None


class TestReminderScheduledEvent:
    """Test ReminderScheduledEvent schema contract."""

    def test_reminder_scheduled_event_valid(self):
        """Valid reminder.scheduled event passes validation."""
        event = ReminderScheduledEvent(
            user_id="user-123",
            task_id=789,
            payload=ReminderScheduledEventPayload(
                task_title="Submit Q4 report",
                task_description="Include revenue, expenses, and forecasts",
                reminder_at="2025-12-31T16:00:00Z",
                notification_type="email",
                user_email="user@example.com",
                due_date="2025-12-31T17:00:00Z"
            )
        )

        assert event.event_type == "reminder.scheduled"
        assert event.event_version == "1.0"
        assert event.payload.notification_type == "email"

    def test_reminder_scheduled_event_matches_yaml_example(self):
        """Event matches the example from event-schemas.yaml."""
        # Example from specs/007-phase5-cloud-deployment/contracts/event-schemas.yaml line 241
        event = ReminderScheduledEvent(
            event_id="660e8400-e29b-41d4-a716-446655440001",
            event_type="reminder.scheduled",
            event_version="1.0",
            timestamp="2025-12-29T12:00:00Z",
            user_id="user-123",
            task_id=789,
            payload=ReminderScheduledEventPayload(
                task_title="Submit Q4 report",
                task_description="Include revenue, expenses, and forecasts",
                reminder_at="2025-12-31T16:00:00Z",
                notification_type="email",
                user_email="user@example.com",
                due_date="2025-12-31T17:00:00Z"
            )
        )

        # Validate all fields match contract
        assert event.event_id == "660e8400-e29b-41d4-a716-446655440001"
        assert event.event_type == "reminder.scheduled"
        assert event.payload.task_title == "Submit Q4 report"
        assert event.payload.reminder_at == "2025-12-31T16:00:00Z"
        assert event.payload.user_email == "user@example.com"

    def test_reminder_scheduled_event_validates_notification_type(self):
        """notification_type must be 'email' or 'push'."""
        with pytest.raises(ValidationError) as exc_info:
            ReminderScheduledEvent(
                user_id="user-123",
                task_id=789,
                payload=ReminderScheduledEventPayload(
                    task_title="Submit Q4 report",
                    reminder_at="2025-12-31T16:00:00Z",
                    notification_type="sms",  # Invalid type
                    user_email="user@example.com",
                    due_date="2025-12-31T17:00:00Z"
                )
            )

        assert "notification_type must be 'email' or 'push'" in str(exc_info.value)


class TestTaskUpdatedEvent:
    """Test TaskUpdatedEvent schema contract."""

    def test_task_updated_event_valid(self):
        """Valid task.updated event passes validation."""
        event = TaskUpdatedEvent(
            user_id="user-123",
            task_id=456,
            payload=TaskUpdatedEventPayload(
                updated_fields={"title": "Updated daily standup"},
                previous_values={"title": "Daily standup"},
                updated_at="2025-12-29T12:30:00Z"
            )
        )

        assert event.event_type == "task.updated"
        assert event.payload.updated_fields == {"title": "Updated daily standup"}

    def test_task_updated_event_matches_yaml_example(self):
        """Event matches the example from event-schemas.yaml."""
        # Example from specs/007-phase5-cloud-deployment/contracts/event-schemas.yaml line 356
        event = TaskUpdatedEvent(
            event_id="770e8400-e29b-41d4-a716-446655440002",
            event_type="task.updated",
            event_version="1.0",
            timestamp="2025-12-29T12:30:00Z",
            user_id="user-123",
            task_id=456,
            payload=TaskUpdatedEventPayload(
                updated_fields={
                    "title": "Updated daily standup",
                    "description": "Changed meeting time"
                },
                previous_values={
                    "title": "Daily standup",
                    "description": "Original meeting"
                },
                updated_at="2025-12-29T12:30:00Z"
            )
        )

        # Validate all fields match contract
        assert event.event_id == "770e8400-e29b-41d4-a716-446655440002"
        assert event.payload.updated_fields["title"] == "Updated daily standup"
        assert event.payload.previous_values["title"] == "Daily standup"


class TestSchemaEvolution:
    """Test schema evolution and backward compatibility."""

    def test_event_version_format(self):
        """event_version must match pattern: ^\d+\.\d+$"""
        # Valid versions
        EventSchema(
            event_type="task.completed",
            user_id="user-123",
            task_id=456,
            payload={},
            event_version="1.0"
        )
        EventSchema(
            event_type="task.completed",
            user_id="user-123",
            task_id=456,
            payload={},
            event_version="2.1"
        )

        # Invalid version (missing minor)
        with pytest.raises(ValidationError):
            EventSchema(
                event_type="task.completed",
                user_id="user-123",
                task_id=456,
                payload={},
                event_version="1"  # Invalid: must be "major.minor"
            )

    def test_optional_fields_support_evolution(self):
        """Optional fields allow backward-compatible schema evolution."""
        # v1.0: Only required fields
        event_v1 = TaskCompletedEvent(
            user_id="user-123",
            task_id=456,
            payload=TaskCompletedEventPayload(
                task_title="Daily standup",
                completed_at="2025-12-29T12:00:00Z"
                # Optional fields omitted
            )
        )
        assert event_v1.payload.recurring_pattern is None

        # v1.1: Add optional field (backward compatible)
        event_v1_1 = TaskCompletedEvent(
            event_version="1.1",
            user_id="user-123",
            task_id=456,
            payload=TaskCompletedEventPayload(
                task_title="Daily standup",
                completed_at="2025-12-29T12:00:00Z",
                recurring_pattern="FREQ=DAILY;INTERVAL=1"  # New optional field
            )
        )
        assert event_v1_1.payload.recurring_pattern == "FREQ=DAILY;INTERVAL=1"


class TestEventSerialization:
    """Test event serialization to JSON (for Kafka publishing)."""

    def test_event_serializes_to_json(self):
        """Events can be serialized to JSON for Kafka."""
        event = TaskCompletedEvent(
            user_id="user-123",
            task_id=456,
            payload=TaskCompletedEventPayload(
                task_title="Daily standup",
                completed_at="2025-12-29T12:00:00Z"
            )
        )

        # Serialize to JSON dict
        event_json = event.model_dump()

        assert event_json['event_type'] == "task.completed"
        assert event_json['user_id'] == "user-123"
        assert event_json['task_id'] == 456
        assert event_json['payload']['task_title'] == "Daily standup"

    def test_event_deserializes_from_json(self):
        """Events can be deserialized from JSON (consumed from Kafka)."""
        event_json = {
            "event_id": "550e8400-e29b-41d4-a716-446655440000",
            "event_type": "task.completed",
            "event_version": "1.0",
            "timestamp": "2025-12-29T12:00:00Z",
            "user_id": "user-123",
            "task_id": 456,
            "payload": {
                "task_title": "Daily standup",
                "completed_at": "2025-12-29T12:00:00Z",
                "recurring_pattern": None,
                "recurring_end_date": None,
                "next_occurrence_due": None
            }
        }

        # Deserialize from JSON
        event = TaskCompletedEvent(**event_json)

        assert event.event_id == "550e8400-e29b-41d4-a716-446655440000"
        assert event.user_id == "user-123"
        assert event.payload.task_title == "Daily standup"
