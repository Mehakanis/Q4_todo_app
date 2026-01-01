"""
Integration tests for Phase II backward compatibility with Phase V.

Tests verify that all Phase II features (task CRUD, filtering, sorting, searching,
export/import) work correctly with the Phase V database schema (recurring_pattern,
next_occurrence, reminder_at, reminder_sent fields).

This ensures no regressions when migrating from Phase II to Phase V.
"""

import pytest
from datetime import datetime, timezone
from sqlmodel import Session
from httpx import AsyncClient

from models import Task
from main import app


class TestPhase2TaskCRUD:
    """Test Phase II task CRUD operations work with Phase V schema."""

    @pytest.mark.asyncio
    async def test_create_task_without_phase5_fields(self, async_client: AsyncClient, test_user_id: str):
        """Verify creating tasks without Phase V fields works (backward compatibility)."""
        # Create task with only Phase II fields
        task_data = {
            "title": "Legacy task",
            "description": "Task created without Phase V fields",
            "priority": "medium",
            "tags": ["phase2", "legacy"],
            "completed": False
        }

        response = await async_client.post(
            f"/api/{test_user_id}/tasks",
            json=task_data
        )

        assert response.status_code == 201
        data = response.json()
        assert data["success"] is True
        assert data["data"]["title"] == "Legacy task"

        # Verify Phase V fields are NULL
        assert data["data"]["recurring_pattern"] is None
        assert data["data"]["recurring_end_date"] is None
        assert data["data"]["next_occurrence"] is None
        assert data["data"]["reminder_at"] is None
        assert data["data"]["reminder_sent"] is False

    @pytest.mark.asyncio
    async def test_read_task_legacy_format(self, async_client: AsyncClient, test_user_id: str, db_session: Session):
        """Verify reading legacy tasks returns proper format."""
        # Create legacy task directly in database
        task = Task(
            user_id=test_user_id,
            title="Direct DB task",
            description="Created directly in database",
            priority="high",
            tags=["test"],
            completed=False,
            # Phase V fields explicitly NULL
            recurring_pattern=None,
            recurring_end_date=None,
            next_occurrence=None,
            reminder_at=None,
            reminder_sent=False
        )
        db_session.add(task)
        db_session.commit()
        db_session.refresh(task)

        # Read task via API
        response = await async_client.get(f"/api/{test_user_id}/tasks/{task.id}")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["id"] == task.id
        assert data["data"]["recurring_pattern"] is None

    @pytest.mark.asyncio
    async def test_update_task_without_phase5_fields(self, async_client: AsyncClient, test_user_id: str, db_session: Session):
        """Verify updating tasks without touching Phase V fields works."""
        # Create task
        task = Task(
            user_id=test_user_id,
            title="Task to update",
            description="Original description",
            priority="low",
            completed=False
        )
        db_session.add(task)
        db_session.commit()
        db_session.refresh(task)

        # Update task (only Phase II fields)
        update_data = {
            "title": "Updated title",
            "description": "Updated description",
            "priority": "high",
            "tags": ["updated"]
        }

        response = await async_client.put(
            f"/api/{test_user_id}/tasks/{task.id}",
            json=update_data
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["title"] == "Updated title"
        assert data["data"]["priority"] == "high"

        # Verify Phase V fields unchanged
        assert data["data"]["recurring_pattern"] is None
        assert data["data"]["next_occurrence"] is None

    @pytest.mark.asyncio
    async def test_delete_task_legacy(self, async_client: AsyncClient, test_user_id: str, db_session: Session):
        """Verify deleting legacy tasks works."""
        # Create legacy task
        task = Task(
            user_id=test_user_id,
            title="Task to delete",
            completed=False
        )
        db_session.add(task)
        db_session.commit()
        task_id = task.id

        # Delete task
        response = await async_client.delete(f"/api/{test_user_id}/tasks/{task_id}")

        assert response.status_code == 204

        # Verify task deleted
        response = await async_client.get(f"/api/{test_user_id}/tasks/{task_id}")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_complete_task_legacy(self, async_client: AsyncClient, test_user_id: str, db_session: Session):
        """Verify marking legacy tasks complete works (no recurring creation)."""
        # Create non-recurring task
        task = Task(
            user_id=test_user_id,
            title="Task to complete",
            completed=False,
            recurring_pattern=None  # Explicitly not recurring
        )
        db_session.add(task)
        db_session.commit()
        task_id = task.id

        # Mark complete
        response = await async_client.patch(f"/api/{test_user_id}/tasks/{task_id}/complete")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["completed"] is True
        assert data["data"]["completed_at"] is not None

        # Verify NO next occurrence created (not a recurring task)
        all_tasks_response = await async_client.get(f"/api/{test_user_id}/tasks")
        all_tasks = all_tasks_response.json()["data"]
        assert len(all_tasks) == 1  # Only original task, no new occurrence


class TestPhase2Filtering:
    """Test Phase II filtering features work with Phase V schema."""

    @pytest.mark.asyncio
    async def test_filter_by_completed_legacy_tasks(self, async_client: AsyncClient, test_user_id: str, db_session: Session):
        """Verify filtering by completed status works with legacy tasks."""
        # Create mix of completed and pending tasks
        tasks = [
            Task(user_id=test_user_id, title="Task 1", completed=False),
            Task(user_id=test_user_id, title="Task 2", completed=True, completed_at=datetime.utcnow()),
            Task(user_id=test_user_id, title="Task 3", completed=False),
        ]
        for task in tasks:
            db_session.add(task)
        db_session.commit()

        # Filter completed tasks
        response = await async_client.get(f"/api/{test_user_id}/tasks?completed=true")

        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]) == 1
        assert data["data"][0]["title"] == "Task 2"

    @pytest.mark.asyncio
    async def test_filter_by_priority_legacy_tasks(self, async_client: AsyncClient, test_user_id: str, db_session: Session):
        """Verify filtering by priority works with legacy tasks."""
        # Create tasks with different priorities
        tasks = [
            Task(user_id=test_user_id, title="High priority", priority="high", completed=False),
            Task(user_id=test_user_id, title="Medium priority", priority="medium", completed=False),
            Task(user_id=test_user_id, title="Low priority", priority="low", completed=False),
        ]
        for task in tasks:
            db_session.add(task)
        db_session.commit()

        # Filter high priority tasks
        response = await async_client.get(f"/api/{test_user_id}/tasks?priority=high")

        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]) == 1
        assert data["data"][0]["priority"] == "high"

    @pytest.mark.asyncio
    async def test_filter_by_tags_legacy_tasks(self, async_client: AsyncClient, test_user_id: str, db_session: Session):
        """Verify filtering by tags works with legacy tasks."""
        # Create tasks with different tags
        tasks = [
            Task(user_id=test_user_id, title="Work task", tags=["work", "urgent"], completed=False),
            Task(user_id=test_user_id, title="Personal task", tags=["personal"], completed=False),
            Task(user_id=test_user_id, title="Shopping", tags=["personal", "shopping"], completed=False),
        ]
        for task in tasks:
            db_session.add(task)
        db_session.commit()

        # Filter tasks with "personal" tag
        response = await async_client.get(f"/api/{test_user_id}/tasks?tags=personal")

        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]) == 2


class TestPhase2Sorting:
    """Test Phase II sorting features work with Phase V schema."""

    @pytest.mark.asyncio
    async def test_sort_by_created_at(self, async_client: AsyncClient, test_user_id: str, db_session: Session):
        """Verify sorting by created_at works."""
        # Create tasks with different timestamps
        import time
        tasks = []
        for i in range(3):
            task = Task(
                user_id=test_user_id,
                title=f"Task {i}",
                completed=False
            )
            db_session.add(task)
            db_session.commit()
            db_session.refresh(task)
            tasks.append(task)
            time.sleep(0.1)  # Ensure different timestamps

        # Sort by created_at descending
        response = await async_client.get(f"/api/{test_user_id}/tasks?sort=created_at&order=desc")

        assert response.status_code == 200
        data = response.json()
        titles = [task["title"] for task in data["data"]]
        assert titles == ["Task 2", "Task 1", "Task 0"]

    @pytest.mark.asyncio
    async def test_sort_by_priority(self, async_client: AsyncClient, test_user_id: str, db_session: Session):
        """Verify sorting by priority works."""
        # Create tasks with different priorities
        tasks = [
            Task(user_id=test_user_id, title="Low task", priority="low", completed=False),
            Task(user_id=test_user_id, title="High task", priority="high", completed=False),
            Task(user_id=test_user_id, title="Medium task", priority="medium", completed=False),
        ]
        for task in tasks:
            db_session.add(task)
        db_session.commit()

        # Sort by priority (high > medium > low)
        response = await async_client.get(f"/api/{test_user_id}/tasks?sort=priority&order=desc")

        assert response.status_code == 200
        data = response.json()
        priorities = [task["priority"] for task in data["data"]]
        # Depending on DB sort implementation, verify high comes before low
        assert priorities.index("high") < priorities.index("low")


class TestPhase2Search:
    """Test Phase II search features work with Phase V schema."""

    @pytest.mark.asyncio
    async def test_search_by_title(self, async_client: AsyncClient, test_user_id: str, db_session: Session):
        """Verify searching by title works."""
        # Create tasks with different titles
        tasks = [
            Task(user_id=test_user_id, title="Buy groceries", description="Milk and bread", completed=False),
            Task(user_id=test_user_id, title="Fix bug in code", description="Authentication issue", completed=False),
            Task(user_id=test_user_id, title="Call dentist", description="Schedule appointment", completed=False),
        ]
        for task in tasks:
            db_session.add(task)
        db_session.commit()

        # Search for "bug"
        response = await async_client.get(f"/api/{test_user_id}/tasks?search=bug")

        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]) == 1
        assert "bug" in data["data"][0]["title"].lower()

    @pytest.mark.asyncio
    async def test_search_by_description(self, async_client: AsyncClient, test_user_id: str, db_session: Session):
        """Verify searching by description works."""
        # Create tasks with different descriptions
        tasks = [
            Task(user_id=test_user_id, title="Task 1", description="Urgent meeting with client", completed=False),
            Task(user_id=test_user_id, title="Task 2", description="Prepare presentation slides", completed=False),
            Task(user_id=test_user_id, title="Task 3", description="Review code changes", completed=False),
        ]
        for task in tasks:
            db_session.add(task)
        db_session.commit()

        # Search for "meeting"
        response = await async_client.get(f"/api/{test_user_id}/tasks?search=meeting")

        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]) == 1
        assert "meeting" in data["data"][0]["description"].lower()


class TestPhase2ExportImport:
    """Test Phase II export/import features work with Phase V schema."""

    @pytest.mark.asyncio
    async def test_export_csv_with_phase5_fields(self, async_client: AsyncClient, test_user_id: str, db_session: Session):
        """Verify CSV export includes Phase V fields (recurring_pattern, next_occurrence)."""
        # Create task with Phase V fields
        task = Task(
            user_id=test_user_id,
            title="Recurring task",
            description="Daily standup",
            priority="high",
            tags=["work"],
            completed=False,
            recurring_pattern="DAILY",
            next_occurrence=datetime(2025, 12, 30, 10, 0, 0, tzinfo=timezone.utc)
        )
        db_session.add(task)
        db_session.commit()

        # Export to CSV
        response = await async_client.get(f"/api/{test_user_id}/tasks/export?format=csv")

        assert response.status_code == 200
        assert response.headers["content-type"] == "text/csv; charset=utf-8"

        # Verify CSV includes Phase V fields
        csv_content = response.text
        assert "recurring_pattern" in csv_content
        assert "next_occurrence" in csv_content
        assert "DAILY" in csv_content

    @pytest.mark.asyncio
    async def test_export_json_with_phase5_fields(self, async_client: AsyncClient, test_user_id: str, db_session: Session):
        """Verify JSON export includes Phase V fields."""
        # Create task with reminders
        task = Task(
            user_id=test_user_id,
            title="Task with reminder",
            description="Important meeting",
            priority="high",
            due_date=datetime(2025, 12, 31, 14, 0, 0, tzinfo=timezone.utc),
            reminder_at=datetime(2025, 12, 31, 13, 0, 0, tzinfo=timezone.utc),
            reminder_sent=False,
            completed=False
        )
        db_session.add(task)
        db_session.commit()

        # Export to JSON
        response = await async_client.get(f"/api/{test_user_id}/tasks/export?format=json")

        assert response.status_code == 200
        assert response.headers["content-type"] == "application/json"

        # Verify JSON includes Phase V fields
        data = response.json()
        assert len(data) == 1
        assert data[0]["reminder_at"] is not None
        assert data[0]["reminder_sent"] is False

    @pytest.mark.asyncio
    async def test_import_csv_without_phase5_fields(self, async_client: AsyncClient, test_user_id: str):
        """Verify importing legacy CSV (without Phase V fields) works."""
        # Create legacy CSV (Phase II format only)
        csv_content = """id,title,description,priority,due_date,tags,completed,created_at,updated_at
1,Legacy task,From old export,medium,,work;personal,false,2025-12-29T10:00:00Z,2025-12-29T10:00:00Z
"""

        # Import CSV
        response = await async_client.post(
            f"/api/{test_user_id}/tasks/import",
            files={"file": ("tasks.csv", csv_content, "text/csv")}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["imported_count"] == 1

        # Verify task imported with NULL Phase V fields
        tasks_response = await async_client.get(f"/api/{test_user_id}/tasks")
        tasks = tasks_response.json()["data"]
        assert len(tasks) == 1
        assert tasks[0]["title"] == "Legacy task"
        assert tasks[0]["recurring_pattern"] is None

    @pytest.mark.asyncio
    async def test_import_json_with_phase5_fields(self, async_client: AsyncClient, test_user_id: str):
        """Verify importing JSON with Phase V fields works."""
        # Create JSON with Phase V fields
        json_content = [
            {
                "title": "Recurring import",
                "description": "Weekly meeting",
                "priority": "high",
                "tags": ["work", "recurring"],
                "completed": False,
                "recurring_pattern": "WEEKLY",
                "recurring_end_date": "2026-12-31T23:59:59Z",
                "next_occurrence": "2026-01-05T10:00:00Z"
            }
        ]

        # Import JSON
        import json
        response = await async_client.post(
            f"/api/{test_user_id}/tasks/import",
            files={"file": ("tasks.json", json.dumps(json_content), "application/json")}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["imported_count"] == 1

        # Verify task imported with Phase V fields
        tasks_response = await async_client.get(f"/api/{test_user_id}/tasks")
        tasks = tasks_response.json()["data"]
        assert len(tasks) == 1
        assert tasks[0]["recurring_pattern"] == "WEEKLY"
        assert tasks[0]["next_occurrence"] is not None


@pytest.fixture
def db_session():
    """Provide database session for direct DB operations."""
    from db import get_session
    session = next(get_session())
    yield session
    session.close()


@pytest.fixture
def test_user_id():
    """Provide test user ID."""
    return "test-user-12345"


@pytest.fixture
async def async_client():
    """Provide async HTTP client for API tests."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client
