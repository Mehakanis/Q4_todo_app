"""
End-to-End Test: User Story 1 - Recurring Task Flow

Tests the complete flow:
1. Create recurring task with DAILY pattern
2. Mark task as complete
3. Verify next occurrence created with correct due date

This validates the event-driven architecture:
- Backend publishes task.completed event to Kafka
- Recurring Task Service consumes event
- RRULE parser calculates next occurrence
- Service creates next task via Dapr Service Invocation
"""

import pytest
import httpx
import asyncio
from datetime import datetime, timedelta, timezone
from typing import Dict, Any


# Configuration
API_BASE_URL = "http://localhost:8000"
TEST_USER_EMAIL = "test-recurring@example.com"
TEST_USER_PASSWORD = "test-password-123"


@pytest.fixture
async def auth_token() -> str:
    """Authenticate and return JWT token."""
    async with httpx.AsyncClient() as client:
        # Sign up user (or use existing)
        response = await client.post(
            f"{API_BASE_URL}/api/auth/signup",
            json={
                "email": TEST_USER_EMAIL,
                "password": TEST_USER_PASSWORD,
                "name": "Test User Recurring"
            }
        )

        # Sign in to get token
        response = await client.post(
            f"{API_BASE_URL}/api/auth/signin",
            json={
                "email": TEST_USER_EMAIL,
                "password": TEST_USER_PASSWORD
            }
        )

        assert response.status_code == 200
        data = response.json()
        return data["token"]


@pytest.fixture
async def user_id(auth_token: str) -> str:
    """Get authenticated user's ID from token."""
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{API_BASE_URL}/api/me",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        return data["id"]


@pytest.mark.asyncio
async def test_recurring_task_complete_creates_next_occurrence(
    auth_token: str,
    user_id: str
):
    """
    Test User Story 1: Recurring Task Flow

    Steps:
    1. Create recurring task with DAILY pattern
    2. Mark task complete
    3. Verify next occurrence created automatically
    4. Verify next occurrence has correct due date (tomorrow)
    """
    async with httpx.AsyncClient() as client:
        headers = {"Authorization": f"Bearer {auth_token}"}

        # Step 1: Create recurring task
        tomorrow = (datetime.now(timezone.utc) + timedelta(days=1)).replace(
            hour=9, minute=0, second=0, microsecond=0
        )

        create_response = await client.post(
            f"{API_BASE_URL}/api/{user_id}/tasks",
            headers=headers,
            json={
                "title": "Daily Standup Meeting",
                "description": "Team standup at 9 AM",
                "recurring_pattern": "DAILY",  # Simplified RRULE pattern
                "next_occurrence": tomorrow.isoformat()
            }
        )

        assert create_response.status_code == 201, \
            f"Failed to create task: {create_response.text}"

        task_data = create_response.json()
        original_task_id = task_data["id"]

        assert task_data["recurring_pattern"] == "DAILY"
        assert task_data["next_occurrence"] is not None

        print(f"✅ Created recurring task ID {original_task_id}")

        # Step 2: Mark task complete
        complete_response = await client.patch(
            f"{API_BASE_URL}/api/{user_id}/tasks/{original_task_id}",
            headers=headers,
            json={"completed": True}
        )

        assert complete_response.status_code == 200, \
            f"Failed to complete task: {complete_response.text}"

        print(f"✅ Marked task {original_task_id} as complete")

        # Step 3: Wait for event processing (Kafka → Recurring Task Service)
        # In production, this should be near-instant, but allow up to 5 seconds
        await asyncio.sleep(5)

        # Step 4: Verify next occurrence created
        list_response = await client.get(
            f"{API_BASE_URL}/api/{user_id}/tasks",
            headers=headers,
            params={"completed": False}  # Get pending tasks only
        )

        assert list_response.status_code == 200
        tasks = list_response.json()

        # Find the new occurrence
        new_occurrence = None
        for task in tasks:
            if (task["title"] == "Daily Standup Meeting"
                and task["id"] != original_task_id
                and not task["completed"]):
                new_occurrence = task
                break

        assert new_occurrence is not None, \
            "Next occurrence not created after task completion"

        print(f"✅ Next occurrence created: ID {new_occurrence['id']}")

        # Step 5: Verify next occurrence date is correct (tomorrow)
        next_occurrence_date = datetime.fromisoformat(
            new_occurrence["next_occurrence"].replace("Z", "+00:00")
        )

        day_after_tomorrow = tomorrow + timedelta(days=1)

        # Allow 1 hour tolerance for timing differences
        time_diff = abs(next_occurrence_date - day_after_tomorrow)
        assert time_diff < timedelta(hours=1), \
            f"Next occurrence date incorrect: {next_occurrence_date} vs expected {day_after_tomorrow}"

        print(f"✅ Next occurrence date correct: {next_occurrence_date}")

        # Cleanup: Delete tasks
        await client.delete(
            f"{API_BASE_URL}/api/{user_id}/tasks/{original_task_id}",
            headers=headers
        )
        await client.delete(
            f"{API_BASE_URL}/api/{user_id}/tasks/{new_occurrence['id']}",
            headers=headers
        )

        print("✅ Test passed: Recurring task flow works end-to-end")


@pytest.mark.asyncio
async def test_recurring_task_with_end_date(auth_token: str, user_id: str):
    """
    Test recurring task stops creating occurrences after end date.

    Steps:
    1. Create recurring task with end date 2 days from now
    2. Complete task twice
    3. Verify no occurrence created after end date
    """
    async with httpx.AsyncClient() as client:
        headers = {"Authorization": f"Bearer {auth_token}"}

        tomorrow = (datetime.now(timezone.utc) + timedelta(days=1)).replace(
            hour=9, minute=0, second=0, microsecond=0
        )
        end_date = tomorrow + timedelta(days=1)  # End after 2 days

        # Create recurring task with end date
        create_response = await client.post(
            f"{API_BASE_URL}/api/{user_id}/tasks",
            headers=headers,
            json={
                "title": "Limited Recurring Task",
                "recurring_pattern": "DAILY",
                "next_occurrence": tomorrow.isoformat(),
                "recurring_end_date": end_date.isoformat()
            }
        )

        assert create_response.status_code == 201
        task_id = create_response.json()["id"]

        # Complete task twice
        for i in range(2):
            await client.patch(
                f"{API_BASE_URL}/api/{user_id}/tasks/{task_id}",
                headers=headers,
                json={"completed": True}
            )
            await asyncio.sleep(5)  # Wait for event processing

            # Get pending tasks
            list_response = await client.get(
                f"{API_BASE_URL}/api/{user_id}/tasks",
                headers=headers,
                params={"completed": False}
            )
            tasks = list_response.json()

            if i == 0:
                # First completion: Next occurrence should exist
                assert any(
                    t["title"] == "Limited Recurring Task" for t in tasks
                ), f"Iteration {i+1}: Next occurrence not created"
            else:
                # Second completion: Past end date, no occurrence
                assert not any(
                    t["title"] == "Limited Recurring Task" for t in tasks
                ), f"Iteration {i+1}: Occurrence created after end date"

        print("✅ Test passed: Recurring end date respected")


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v", "-s"])
