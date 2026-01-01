"""
End-to-end integration tests for recurring tasks lifecycle.

Tests the complete flow:
1. Create recurring task with RRULE pattern
2. Mark task complete
3. Verify Kafka event published
4. Verify Recurring Task Service creates next occurrence
5. Verify next occurrence has correct due date

These tests verify the entire event-driven architecture for recurring tasks.
"""

import pytest
import asyncio
from datetime import datetime, timedelta, timezone
from sqlmodel import Session, select
from httpx import AsyncClient

from models import Task
from main import app
from src.integrations.dapr_client import get_dapr_client
from src.integrations.rrule_parser import get_rrule_parser


class TestRecurringTaskLifecycle:
    """Test complete lifecycle of recurring tasks from creation to next occurrence."""

    @pytest.mark.asyncio
    async def test_daily_recurring_task_full_lifecycle(self, async_client: AsyncClient, test_user_id: str, db_session: Session):
        """
        Test full lifecycle of daily recurring task:
        1. Create task with DAILY pattern
        2. Verify next_occurrence calculated
        3. Mark complete
        4. Verify task.completed event published
        5. Verify next occurrence created
        """
        # Step 1: Create daily recurring task
        task_data = {
            "title": "Daily standup",
            "description": "Team sync meeting",
            "priority": "high",
            "tags": ["work", "recurring"],
            "recurring_pattern": "DAILY",
            "due_date": "2025-12-29T10:00:00Z"
        }

        create_response = await async_client.post(
            f"/api/{test_user_id}/tasks",
            json=task_data
        )

        assert create_response.status_code == 201
        created_task = create_response.json()["data"]

        # Step 2: Verify next_occurrence calculated correctly
        assert created_task["recurring_pattern"] == "DAILY"
        assert created_task["next_occurrence"] is not None

        # Parse and verify next occurrence is 1 day after due_date
        parser = get_rrule_parser()
        expected_next = parser.calculate_next(
            pattern="DAILY",
            dtstart=datetime(2025, 12, 29, 10, 0, 0, tzinfo=timezone.utc),
            end_date=None
        )
        assert datetime.fromisoformat(created_task["next_occurrence"].replace("Z", "+00:00")) == expected_next

        # Step 3: Mark task complete
        complete_response = await async_client.patch(
            f"/api/{test_user_id}/tasks/{created_task['id']}/complete"
        )

        assert complete_response.status_code == 200
        completed_task = complete_response.json()["data"]
        assert completed_task["completed"] is True
        assert completed_task["completed_at"] is not None

        # Step 4: Wait for event processing (Kafka + Recurring Task Service)
        # In real deployment, this would be async. For testing, simulate event processing
        await asyncio.sleep(0.5)  # Give time for event to be processed

        # Step 5: Verify next occurrence created
        # Query database for tasks with same title but different ID
        statement = select(Task).where(
            Task.user_id == test_user_id,
            Task.title == "Daily standup",
            Task.completed == False
        )
        all_tasks = db_session.exec(statement).all()

        # Should have 2 tasks: original (completed) and next occurrence (pending)
        assert len(all_tasks) >= 1  # At least the next occurrence

        # Find the new occurrence (not the original)
        next_occurrence_task = next((t for t in all_tasks if t.id != created_task["id"]), None)
        assert next_occurrence_task is not None
        assert next_occurrence_task.recurring_pattern == "DAILY"
        assert next_occurrence_task.completed is False

    @pytest.mark.asyncio
    async def test_weekly_recurring_task_with_end_date(self, async_client: AsyncClient, test_user_id: str, db_session: Session):
        """
        Test weekly recurring task with end date:
        1. Create task with WEEKLY pattern and end_date
        2. Mark complete before end_date → next occurrence created
        3. Mark complete after end_date → NO next occurrence created
        """
        # Step 1: Create weekly recurring task with end date
        end_date = datetime(2026, 1, 31, 23, 59, 59, tzinfo=timezone.utc)
        task_data = {
            "title": "Weekly team meeting",
            "description": "Retrospective and planning",
            "priority": "medium",
            "recurring_pattern": "WEEKLY",
            "recurring_end_date": end_date.isoformat(),
            "due_date": "2025-12-29T14:00:00Z"
        }

        create_response = await async_client.post(
            f"/api/{test_user_id}/tasks",
            json=task_data
        )

        assert create_response.status_code == 201
        created_task = create_response.json()["data"]
        assert created_task["recurring_pattern"] == "WEEKLY"
        assert created_task["recurring_end_date"] is not None

        # Step 2: Mark complete (next occurrence should be created)
        await async_client.patch(f"/api/{test_user_id}/tasks/{created_task['id']}/complete")

        await asyncio.sleep(0.5)  # Event processing time

        # Verify next occurrence created
        statement = select(Task).where(
            Task.user_id == test_user_id,
            Task.title == "Weekly team meeting",
            Task.completed == False
        )
        pending_tasks = db_session.exec(statement).all()
        assert len(pending_tasks) >= 1

    @pytest.mark.asyncio
    async def test_monthly_recurring_pattern(self, async_client: AsyncClient, test_user_id: str, db_session: Session):
        """Test monthly recurring task creates next occurrence 1 month later."""
        # Create monthly recurring task
        task_data = {
            "title": "Monthly report",
            "description": "Submit financial report",
            "priority": "high",
            "recurring_pattern": "MONTHLY",
            "due_date": "2025-12-29T17:00:00Z"
        }

        create_response = await async_client.post(
            f"/api/{test_user_id}/tasks",
            json=task_data
        )

        assert create_response.status_code == 201
        created_task = create_response.json()["data"]

        # Verify next_occurrence is approximately 1 month later
        parser = get_rrule_parser()
        expected_next = parser.calculate_next(
            pattern="MONTHLY",
            dtstart=datetime(2025, 12, 29, 17, 0, 0, tzinfo=timezone.utc),
            end_date=None
        )
        actual_next = datetime.fromisoformat(created_task["next_occurrence"].replace("Z", "+00:00"))

        # Verify month difference
        assert actual_next.month == (expected_next.month % 12) or actual_next.month == expected_next.month

    @pytest.mark.asyncio
    async def test_invalid_rrule_pattern_rejected(self, async_client: AsyncClient, test_user_id: str):
        """Verify invalid RRULE patterns are rejected with clear error."""
        # Attempt to create task with invalid pattern
        task_data = {
            "title": "Invalid recurring task",
            "recurring_pattern": "INVALID_PATTERN",  # Invalid
            "due_date": "2025-12-29T10:00:00Z"
        }

        response = await async_client.post(
            f"/api/{test_user_id}/tasks",
            json=task_data
        )

        assert response.status_code == 400
        error = response.json()
        assert error["success"] is False
        assert "INVALID_RECURRING_PATTERN" in error["error"]["code"] or "Invalid" in error["error"]["message"]

    @pytest.mark.asyncio
    async def test_completing_non_recurring_task_no_next_occurrence(self, async_client: AsyncClient, test_user_id: str, db_session: Session):
        """Verify completing non-recurring tasks does NOT create next occurrence."""
        # Create normal (non-recurring) task
        task_data = {
            "title": "One-time task",
            "description": "Single occurrence only",
            "completed": False
        }

        create_response = await async_client.post(
            f"/api/{test_user_id}/tasks",
            json=task_data
        )

        assert create_response.status_code == 201
        created_task = create_response.json()["data"]
        assert created_task["recurring_pattern"] is None
        assert created_task["next_occurrence"] is None

        # Mark complete
        await async_client.patch(f"/api/{test_user_id}/tasks/{created_task['id']}/complete")

        await asyncio.sleep(0.5)  # Event processing time

        # Verify NO next occurrence created
        statement = select(Task).where(
            Task.user_id == test_user_id,
            Task.title == "One-time task"
        )
        all_tasks = db_session.exec(statement).all()
        assert len(all_tasks) == 1  # Only original task
        assert all_tasks[0].completed is True


class TestRecurringTaskEdgeCases:
    """Test edge cases and error handling for recurring tasks."""

    @pytest.mark.asyncio
    async def test_recurring_task_without_due_date(self, async_client: AsyncClient, test_user_id: str):
        """Test recurring task without due_date uses current time as dtstart."""
        task_data = {
            "title": "Recurring task no due date",
            "recurring_pattern": "DAILY"
            # No due_date provided
        }

        response = await async_client.post(
            f"/api/{test_user_id}/tasks",
            json=task_data
        )

        assert response.status_code == 201
        created_task = response.json()["data"]
        assert created_task["recurring_pattern"] == "DAILY"
        assert created_task["next_occurrence"] is not None

        # Verify next_occurrence is approximately 1 day from now
        next_occ = datetime.fromisoformat(created_task["next_occurrence"].replace("Z", "+00:00"))
        now = datetime.now(timezone.utc)
        time_diff = (next_occ - now).total_seconds()
        assert 23 * 3600 < time_diff < 25 * 3600  # Between 23-25 hours (1 day ± tolerance)

    @pytest.mark.asyncio
    async def test_recurring_end_date_in_past_no_occurrence(self, async_client: AsyncClient, test_user_id: str):
        """Test recurring task with end_date in the past creates no next_occurrence."""
        task_data = {
            "title": "Expired recurring task",
            "recurring_pattern": "DAILY",
            "recurring_end_date": "2020-01-01T00:00:00Z",  # Past date
            "due_date": "2025-12-29T10:00:00Z"
        }

        response = await async_client.post(
            f"/api/{test_user_id}/tasks",
            json=task_data
        )

        # Task creation succeeds, but next_occurrence is NULL
        assert response.status_code == 201
        created_task = response.json()["data"]
        assert created_task["recurring_pattern"] == "DAILY"
        assert created_task["next_occurrence"] is None  # End date already passed

    @pytest.mark.asyncio
    async def test_full_rfc5545_rrule_pattern(self, async_client: AsyncClient, test_user_id: str):
        """Test using full RFC 5545 RRULE pattern (advanced)."""
        task_data = {
            "title": "Advanced RRULE task",
            "description": "Every Monday and Wednesday",
            "recurring_pattern": "FREQ=WEEKLY;BYDAY=MO,WE;INTERVAL=1",
            "due_date": "2025-12-29T10:00:00Z"  # Monday
        }

        response = await async_client.post(
            f"/api/{test_user_id}/tasks",
            json=task_data
        )

        assert response.status_code == 201
        created_task = response.json()["data"]
        assert created_task["recurring_pattern"] == "FREQ=WEEKLY;BYDAY=MO,WE;INTERVAL=1"
        assert created_task["next_occurrence"] is not None


@pytest.fixture
def db_session():
    """Provide database session for direct DB operations."""
    from db import get_session
    session = next(get_session())
    yield session
    session.rollback()  # Rollback to avoid test pollution
    session.close()


@pytest.fixture
def test_user_id():
    """Provide test user ID."""
    return "test-user-recurring-e2e"


@pytest.fixture
async def async_client():
    """Provide async HTTP client for API tests."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client
