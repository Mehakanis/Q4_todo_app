"""
Integration tests for task management endpoints.

This module tests all task CRUD operations with user isolation.
"""

import pytest
from datetime import datetime, timedelta
from httpx import AsyncClient
from sqlmodel import Session

from models import Task, User


class TestTaskCreation:
    """Tests for task creation endpoint (POST /api/{user_id}/tasks)."""

    @pytest.mark.asyncio
    async def test_create_task_success(
        self, async_client: AsyncClient, auth_headers: dict, test_user: User
    ):
        """Test successful task creation."""
        task_data = {
            "title": "Test Task",
            "description": "Test task description",
            "priority": "high",
            "tags": ["work", "urgent"],
        }

        response = await async_client.post(
            f"/api/{test_user.id}/tasks", json=task_data, headers=auth_headers
        )

        assert response.status_code == 201
        data = response.json()
        assert data["success"] is True
        assert data["data"]["title"] == "Test Task"
        assert data["data"]["description"] == "Test task description"
        assert data["data"]["priority"] == "high"
        assert data["data"]["tags"] == ["work", "urgent"]
        assert data["data"]["completed"] is False
        assert data["data"]["user_id"] == str(test_user.id)

    @pytest.mark.asyncio
    async def test_create_task_minimal_fields(
        self, async_client: AsyncClient, auth_headers: dict, test_user: User
    ):
        """Test task creation with only required fields."""
        task_data = {"title": "Minimal Task"}

        response = await async_client.post(
            f"/api/{test_user.id}/tasks", json=task_data, headers=auth_headers
        )

        assert response.status_code == 201
        data = response.json()
        assert data["success"] is True
        assert data["data"]["title"] == "Minimal Task"
        assert data["data"]["priority"] == "medium"  # default
        assert data["data"]["completed"] is False

    @pytest.mark.asyncio
    async def test_create_task_with_due_date(
        self, async_client: AsyncClient, auth_headers: dict, test_user: User
    ):
        """Test task creation with due date."""
        due_date = (datetime.utcnow() + timedelta(days=7)).isoformat()
        task_data = {"title": "Task with due date", "due_date": due_date}

        response = await async_client.post(
            f"/api/{test_user.id}/tasks", json=task_data, headers=auth_headers
        )

        assert response.status_code == 201
        data = response.json()
        assert data["success"] is True
        assert data["data"]["due_date"] is not None

    @pytest.mark.asyncio
    async def test_create_task_empty_title(
        self, async_client: AsyncClient, auth_headers: dict, test_user: User
    ):
        """Test task creation with empty title."""
        task_data = {"title": "   "}

        response = await async_client.post(
            f"/api/{test_user.id}/tasks", json=task_data, headers=auth_headers
        )

        assert response.status_code == 422  # Validation error

    @pytest.mark.asyncio
    async def test_create_task_invalid_priority(
        self, async_client: AsyncClient, auth_headers: dict, test_user: User
    ):
        """Test task creation with invalid priority."""
        task_data = {"title": "Test Task", "priority": "invalid"}

        response = await async_client.post(
            f"/api/{test_user.id}/tasks", json=task_data, headers=auth_headers
        )

        assert response.status_code == 422  # Validation error

    @pytest.mark.asyncio
    async def test_create_task_unauthorized(
        self, async_client: AsyncClient, test_user: User
    ):
        """Test task creation without authentication."""
        task_data = {"title": "Test Task"}

        response = await async_client.post(
            f"/api/{test_user.id}/tasks", json=task_data
        )

        assert response.status_code == 403  # No auth header

    @pytest.mark.asyncio
    async def test_create_task_user_mismatch(
        self, async_client: AsyncClient, auth_headers: dict, test_user: User, db: Session
    ):
        """Test task creation with mismatched user_id."""
        # Create another user
        other_user = User(email="other@example.com", password_hash="hash", name="Other User")
        db.add(other_user)
        db.commit()

        task_data = {"title": "Test Task"}

        # Try to create task for other user
        response = await async_client.post(
            f"/api/{other_user.id}/tasks", json=task_data, headers=auth_headers
        )

        assert response.status_code == 403  # Forbidden


class TestTaskListing:
    """Tests for task listing endpoint (GET /api/{user_id}/tasks)."""

    @pytest.mark.asyncio
    async def test_get_tasks_empty(
        self, async_client: AsyncClient, auth_headers: dict, test_user: User
    ):
        """Test getting tasks when user has no tasks."""
        response = await async_client.get(
            f"/api/{test_user.id}/tasks", headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"] == []

    @pytest.mark.asyncio
    async def test_get_tasks_multiple(
        self, async_client: AsyncClient, auth_headers: dict, test_user: User, db: Session
    ):
        """Test getting multiple tasks."""
        # Create tasks
        tasks = [
            Task(user_id=test_user.id, title=f"Task {i}", priority="medium")
            for i in range(3)
        ]
        for task in tasks:
            db.add(task)
        db.commit()

        response = await async_client.get(
            f"/api/{test_user.id}/tasks", headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert len(data["data"]) == 3

    @pytest.mark.asyncio
    async def test_get_tasks_user_isolation(
        self, async_client: AsyncClient, auth_headers: dict, test_user: User, db: Session
    ):
        """Test that users only see their own tasks."""
        # Create another user with tasks
        other_user = User(email="other@example.com", password_hash="hash", name="Other User")
        db.add(other_user)
        db.commit()

        # Create tasks for both users
        user_task = Task(user_id=test_user.id, title="User Task", priority="medium")
        other_task = Task(user_id=other_user.id, title="Other Task", priority="medium")
        db.add(user_task)
        db.add(other_task)
        db.commit()

        # Get tasks for test_user
        response = await async_client.get(
            f"/api/{test_user.id}/tasks", headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert len(data["data"]) == 1
        assert data["data"][0]["title"] == "User Task"


class TestTaskRetrieval:
    """Tests for task retrieval endpoint (GET /api/{user_id}/tasks/{task_id})."""

    @pytest.mark.asyncio
    async def test_get_task_by_id_success(
        self, async_client: AsyncClient, auth_headers: dict, test_user: User, db: Session
    ):
        """Test getting a specific task by ID."""
        task = Task(
            user_id=test_user.id,
            title="Test Task",
            description="Description",
            priority="high",
        )
        db.add(task)
        db.commit()
        db.refresh(task)

        response = await async_client.get(
            f"/api/{test_user.id}/tasks/{task.id}", headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["id"] == task.id
        assert data["data"]["title"] == "Test Task"

    @pytest.mark.asyncio
    async def test_get_task_not_found(
        self, async_client: AsyncClient, auth_headers: dict, test_user: User
    ):
        """Test getting a non-existent task."""
        response = await async_client.get(
            f"/api/{test_user.id}/tasks/99999", headers=auth_headers
        )

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_get_task_other_user(
        self, async_client: AsyncClient, auth_headers: dict, test_user: User, db: Session
    ):
        """Test getting a task that belongs to another user."""
        # Create another user with a task
        other_user = User(email="other@example.com", password_hash="hash", name="Other User")
        db.add(other_user)
        db.commit()

        other_task = Task(user_id=other_user.id, title="Other Task", priority="medium")
        db.add(other_task)
        db.commit()
        db.refresh(other_task)

        # Try to get other user's task
        response = await async_client.get(
            f"/api/{test_user.id}/tasks/{other_task.id}", headers=auth_headers
        )

        assert response.status_code == 404  # Not found (user isolation)


class TestTaskUpdate:
    """Tests for task update endpoint (PUT /api/{user_id}/tasks/{task_id})."""

    @pytest.mark.asyncio
    async def test_update_task_success(
        self, async_client: AsyncClient, auth_headers: dict, test_user: User, db: Session
    ):
        """Test successful task update."""
        task = Task(user_id=test_user.id, title="Original Title", priority="low")
        db.add(task)
        db.commit()
        db.refresh(task)

        update_data = {
            "title": "Updated Title",
            "description": "New description",
            "priority": "high",
        }

        response = await async_client.put(
            f"/api/{test_user.id}/tasks/{task.id}", json=update_data, headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["title"] == "Updated Title"
        assert data["data"]["description"] == "New description"
        assert data["data"]["priority"] == "high"

    @pytest.mark.asyncio
    async def test_update_task_partial(
        self, async_client: AsyncClient, auth_headers: dict, test_user: User, db: Session
    ):
        """Test partial task update (only some fields)."""
        task = Task(
            user_id=test_user.id,
            title="Original Title",
            description="Original Description",
            priority="low",
        )
        db.add(task)
        db.commit()
        db.refresh(task)

        update_data = {"priority": "high"}  # Only update priority

        response = await async_client.put(
            f"/api/{test_user.id}/tasks/{task.id}", json=update_data, headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["title"] == "Original Title"  # Unchanged
        assert data["data"]["description"] == "Original Description"  # Unchanged
        assert data["data"]["priority"] == "high"  # Changed

    @pytest.mark.asyncio
    async def test_update_task_not_found(
        self, async_client: AsyncClient, auth_headers: dict, test_user: User
    ):
        """Test updating a non-existent task."""
        update_data = {"title": "Updated Title"}

        response = await async_client.put(
            f"/api/{test_user.id}/tasks/99999", json=update_data, headers=auth_headers
        )

        assert response.status_code == 404


class TestTaskDeletion:
    """Tests for task deletion endpoint (DELETE /api/{user_id}/tasks/{task_id})."""

    @pytest.mark.asyncio
    async def test_delete_task_success(
        self, async_client: AsyncClient, auth_headers: dict, test_user: User, db: Session
    ):
        """Test successful task deletion."""
        task = Task(user_id=test_user.id, title="Task to delete", priority="medium")
        db.add(task)
        db.commit()
        db.refresh(task)

        response = await async_client.delete(
            f"/api/{test_user.id}/tasks/{task.id}", headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["message"] == "Task deleted successfully"

        # Verify task is deleted from database
        deleted_task = db.get(Task, task.id)
        assert deleted_task is None

    @pytest.mark.asyncio
    async def test_delete_task_not_found(
        self, async_client: AsyncClient, auth_headers: dict, test_user: User
    ):
        """Test deleting a non-existent task."""
        response = await async_client.delete(
            f"/api/{test_user.id}/tasks/99999", headers=auth_headers
        )

        assert response.status_code == 404


class TestTaskCompletion:
    """Tests for task completion toggle endpoint (PATCH /api/{user_id}/tasks/{task_id}/complete)."""

    @pytest.mark.asyncio
    async def test_toggle_complete_to_true(
        self, async_client: AsyncClient, auth_headers: dict, test_user: User, db: Session
    ):
        """Test marking task as complete."""
        task = Task(user_id=test_user.id, title="Test Task", priority="medium", completed=False)
        db.add(task)
        db.commit()
        db.refresh(task)

        response = await async_client.patch(
            f"/api/{test_user.id}/tasks/{task.id}/complete",
            json={"completed": True},
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["completed"] is True

    @pytest.mark.asyncio
    async def test_toggle_complete_to_false(
        self, async_client: AsyncClient, auth_headers: dict, test_user: User, db: Session
    ):
        """Test marking task as incomplete."""
        task = Task(user_id=test_user.id, title="Test Task", priority="medium", completed=True)
        db.add(task)
        db.commit()
        db.refresh(task)

        response = await async_client.patch(
            f"/api/{test_user.id}/tasks/{task.id}/complete",
            json={"completed": False},
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["completed"] is False

    @pytest.mark.asyncio
    async def test_toggle_complete_not_found(
        self, async_client: AsyncClient, auth_headers: dict, test_user: User
    ):
        """Test toggling completion on non-existent task."""
        response = await async_client.patch(
            f"/api/{test_user.id}/tasks/99999/complete",
            json={"completed": True},
            headers=auth_headers,
        )

        assert response.status_code == 404
