"""
API tests for task endpoints.

This module tests all task-related API endpoints through HTTP requests,
validating status codes, response structure, and data integrity.
"""

from datetime import timedelta
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from models import Task, User
from utils.auth import generate_jwt_token


@pytest.fixture
def auth_user(session):
    """Create and return an authenticated user with token."""
    from utils.password import hash_password

    user = User(
        email="testuser@example.com",
        password_hash=hash_password("testpassword123"),
        name="Test User",
    )
    session.add(user)
    session.commit()
    session.refresh(user)

    token = generate_jwt_token(str(user.id), user.email)

    return {"user": user, "token": token, "headers": {"Authorization": f"Bearer {token}"}}


@pytest.fixture
def other_user(session):
    """Create and return another user for testing user isolation."""
    from utils.password import hash_password

    user = User(
        email="otheruser@example.com",
        password_hash=hash_password("otherpassword123"),
        name="Other User",
    )
    session.add(user)
    session.commit()
    session.refresh(user)

    token = generate_jwt_token(str(user.id), user.email)

    return {"user": user, "token": token, "headers": {"Authorization": f"Bearer {token}"}}


class TestCreateTaskAPI:
    """Tests for POST /api/{user_id}/tasks endpoint."""

    def test_create_task_success_returns_201_with_task(self, client: TestClient, auth_user):
        """Test creating valid task returns 201 with task data."""
        # Arrange
        user_id = str(auth_user["user"].id)
        task_data = {
            "title": "New API Task",
            "description": "Created via API",
            "priority": "high",
            "tags": ["api", "test"],
        }

        # Act
        response = client.post(
            f"/api/{user_id}/tasks", json=task_data, headers=auth_user["headers"]
        )

        # Assert
        assert response.status_code == 201
        data = response.json()
        assert data["success"] is True
        assert data["data"]["title"] == "New API Task"
        assert data["data"]["priority"] == "high"
        assert data["data"]["completed"] is False
        assert "id" in data["data"]

    def test_create_task_minimal_data_uses_defaults(self, client: TestClient, auth_user):
        """Test creating task with minimal data uses default values."""
        # Arrange
        user_id = str(auth_user["user"].id)
        task_data = {"title": "Minimal Task"}

        # Act
        response = client.post(
            f"/api/{user_id}/tasks", json=task_data, headers=auth_user["headers"]
        )

        # Assert
        assert response.status_code == 201
        data = response.json()
        assert data["data"]["priority"] == "medium"  # default
        assert data["data"]["completed"] is False

    def test_create_task_without_auth_returns_401(self, client: TestClient):
        """Test creating task without authentication returns 401."""
        # Arrange
        user_id = str(uuid4())
        task_data = {"title": "Unauthorized Task"}

        # Act
        response = client.post(f"/api/{user_id}/tasks", json=task_data)

        # Assert
        assert response.status_code == 401

    def test_create_task_wrong_user_id_returns_403(self, client: TestClient, auth_user, other_user):
        """Test creating task for different user returns 403."""
        # Arrange
        other_user_id = str(other_user["user"].id)
        task_data = {"title": "Forbidden Task"}

        # Act - Use auth_user's token but other_user's ID
        response = client.post(
            f"/api/{other_user_id}/tasks", json=task_data, headers=auth_user["headers"]
        )

        # Assert
        assert response.status_code == 403

    def test_create_task_missing_title_returns_422(self, client: TestClient, auth_user):
        """Test creating task without title returns 422 validation error."""
        # Arrange
        user_id = str(auth_user["user"].id)
        task_data = {"description": "No title"}

        # Act
        response = client.post(
            f"/api/{user_id}/tasks", json=task_data, headers=auth_user["headers"]
        )

        # Assert
        assert response.status_code == 422

    def test_create_task_invalid_priority_returns_422(self, client: TestClient, auth_user):
        """Test creating task with invalid priority returns 422."""
        # Arrange
        user_id = str(auth_user["user"].id)
        task_data = {"title": "Task", "priority": "invalid"}

        # Act
        response = client.post(
            f"/api/{user_id}/tasks", json=task_data, headers=auth_user["headers"]
        )

        # Assert
        assert response.status_code == 422


class TestGetTasksAPI:
    """Tests for GET /api/{user_id}/tasks endpoint."""

    def test_get_tasks_success_returns_200_with_tasks(self, client: TestClient, auth_user, session):
        """Test getting tasks returns 200 with task list."""
        # Arrange
        user_id = str(auth_user["user"].id)
        # Create some tasks
        for i in range(3):
            task = Task(user_id=auth_user["user"].id, title=f"Task {i}", completed=False)
            session.add(task)
        session.commit()

        # Act
        response = client.get(f"/api/{user_id}/tasks", headers=auth_user["headers"])

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert len(data["data"]) == 3
        assert "meta" in data
        assert data["meta"]["total"] == 3

    def test_get_tasks_with_status_filter_returns_filtered_results(
        self, client: TestClient, auth_user, session
    ):
        """Test getting tasks with status filter returns only matching tasks."""
        # Arrange
        user_id = str(auth_user["user"].id)
        session.add(Task(user_id=auth_user["user"].id, title="Completed", completed=True))
        session.add(Task(user_id=auth_user["user"].id, title="Pending", completed=False))
        session.commit()

        # Act
        response = client.get(
            f"/api/{user_id}/tasks?status=completed", headers=auth_user["headers"]
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]) == 1
        assert data["data"][0]["title"] == "Completed"

    def test_get_tasks_with_pagination_returns_correct_page(
        self, client: TestClient, auth_user, session
    ):
        """Test getting tasks with pagination returns correct page."""
        # Arrange
        user_id = str(auth_user["user"].id)
        for i in range(10):
            session.add(Task(user_id=auth_user["user"].id, title=f"Task {i}", completed=False))
        session.commit()

        # Act
        response = client.get(
            f"/api/{user_id}/tasks?page=2&limit=3", headers=auth_user["headers"]
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]) == 3
        assert data["meta"]["page"] == 2
        assert data["meta"]["total"] == 10

    def test_get_tasks_with_search_filters_results(self, client: TestClient, auth_user, session):
        """Test getting tasks with search query filters results."""
        # Arrange
        user_id = str(auth_user["user"].id)
        session.add(Task(user_id=auth_user["user"].id, title="Python Development", completed=False))
        session.add(Task(user_id=auth_user["user"].id, title="Java Development", completed=False))
        session.commit()

        # Act
        response = client.get(f"/api/{user_id}/tasks?search=python", headers=auth_user["headers"])

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]) == 1
        assert "Python" in data["data"][0]["title"]

    def test_get_tasks_without_auth_returns_401(self, client: TestClient):
        """Test getting tasks without authentication returns 401."""
        # Act
        response = client.get(f"/api/{uuid4()}/tasks")

        # Assert
        assert response.status_code == 401

    def test_get_tasks_user_isolation_enforced(
        self, client: TestClient, auth_user, other_user, session
    ):
        """Test user isolation - users only see their own tasks."""
        # Arrange
        user_id = str(auth_user["user"].id)

        # Create tasks for both users
        session.add(Task(user_id=auth_user["user"].id, title="My Task", completed=False))
        session.add(Task(user_id=other_user["user"].id, title="Other Task", completed=False))
        session.commit()

        # Act
        response = client.get(f"/api/{user_id}/tasks", headers=auth_user["headers"])

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]) == 1
        assert data["data"][0]["title"] == "My Task"


class TestGetTaskByIdAPI:
    """Tests for GET /api/{user_id}/tasks/{task_id} endpoint."""

    def test_get_task_by_id_success_returns_200_with_task(
        self, client: TestClient, auth_user, session
    ):
        """Test getting existing task by ID returns 200 with task data."""
        # Arrange
        user_id = str(auth_user["user"].id)
        task = Task(user_id=auth_user["user"].id, title="Specific Task", completed=False)
        session.add(task)
        session.commit()

        # Act
        response = client.get(
            f"/api/{user_id}/tasks/{task.id}", headers=auth_user["headers"]
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["id"] == task.id
        assert data["data"]["title"] == "Specific Task"

    def test_get_task_nonexistent_returns_404(self, client: TestClient, auth_user):
        """Test getting non-existent task returns 404."""
        # Arrange
        user_id = str(auth_user["user"].id)

        # Act
        response = client.get(f"/api/{user_id}/tasks/99999", headers=auth_user["headers"])

        # Assert
        assert response.status_code == 404

    def test_get_task_wrong_user_returns_404(
        self, client: TestClient, auth_user, other_user, session
    ):
        """Test getting another user's task returns 404."""
        # Arrange
        user_id = str(auth_user["user"].id)
        # Create task for other user
        task = Task(user_id=other_user["user"].id, title="Other User Task", completed=False)
        session.add(task)
        session.commit()

        # Act
        response = client.get(
            f"/api/{user_id}/tasks/{task.id}", headers=auth_user["headers"]
        )

        # Assert
        assert response.status_code == 404


class TestUpdateTaskAPI:
    """Tests for PUT /api/{user_id}/tasks/{task_id} endpoint."""

    def test_update_task_success_returns_200_with_updated_task(
        self, client: TestClient, auth_user, session
    ):
        """Test updating task returns 200 with updated data."""
        # Arrange
        user_id = str(auth_user["user"].id)
        task = Task(user_id=auth_user["user"].id, title="Original Title", completed=False)
        session.add(task)
        session.commit()

        update_data = {"title": "Updated Title", "priority": "high"}

        # Act
        response = client.put(
            f"/api/{user_id}/tasks/{task.id}", json=update_data, headers=auth_user["headers"]
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["title"] == "Updated Title"
        assert data["data"]["priority"] == "high"

    def test_update_task_partial_update_works(self, client: TestClient, auth_user, session):
        """Test partial task update only changes specified fields."""
        # Arrange
        user_id = str(auth_user["user"].id)
        task = Task(
            user_id=auth_user["user"].id,
            title="Original",
            description="Original Description",
            priority="low",
            completed=False,
        )
        session.add(task)
        session.commit()

        update_data = {"priority": "high"}  # Only update priority

        # Act
        response = client.put(
            f"/api/{user_id}/tasks/{task.id}", json=update_data, headers=auth_user["headers"]
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["priority"] == "high"
        assert data["data"]["title"] == "Original"  # Unchanged

    def test_update_task_wrong_user_returns_404(
        self, client: TestClient, auth_user, other_user, session
    ):
        """Test updating another user's task returns 404."""
        # Arrange
        user_id = str(auth_user["user"].id)
        task = Task(user_id=other_user["user"].id, title="Other Task", completed=False)
        session.add(task)
        session.commit()

        # Act
        response = client.put(
            f"/api/{user_id}/tasks/{task.id}",
            json={"title": "Hacked"},
            headers=auth_user["headers"],
        )

        # Assert
        assert response.status_code == 404


class TestDeleteTaskAPI:
    """Tests for DELETE /api/{user_id}/tasks/{task_id} endpoint."""

    def test_delete_task_success_returns_200(self, client: TestClient, auth_user, session):
        """Test deleting task returns 200 with success message."""
        # Arrange
        user_id = str(auth_user["user"].id)
        task = Task(user_id=auth_user["user"].id, title="To Delete", completed=False)
        session.add(task)
        session.commit()
        task_id = task.id

        # Act
        response = client.delete(
            f"/api/{user_id}/tasks/{task_id}", headers=auth_user["headers"]
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "deleted" in data["message"].lower()

    def test_delete_task_removes_from_database(self, client: TestClient, auth_user, session):
        """Test deleted task is actually removed from database."""
        # Arrange
        user_id = str(auth_user["user"].id)
        task = Task(user_id=auth_user["user"].id, title="To Delete", completed=False)
        session.add(task)
        session.commit()
        task_id = task.id

        # Act
        client.delete(f"/api/{user_id}/tasks/{task_id}", headers=auth_user["headers"])

        # Assert - Try to get deleted task
        response = client.get(f"/api/{user_id}/tasks/{task_id}", headers=auth_user["headers"])
        assert response.status_code == 404

    def test_delete_task_wrong_user_returns_404(
        self, client: TestClient, auth_user, other_user, session
    ):
        """Test deleting another user's task returns 404."""
        # Arrange
        user_id = str(auth_user["user"].id)
        task = Task(user_id=other_user["user"].id, title="Other Task", completed=False)
        session.add(task)
        session.commit()

        # Act
        response = client.delete(
            f"/api/{user_id}/tasks/{task.id}", headers=auth_user["headers"]
        )

        # Assert
        assert response.status_code == 404


class TestToggleCompleteAPI:
    """Tests for PATCH /api/{user_id}/tasks/{task_id}/complete endpoint."""

    def test_toggle_complete_to_true_returns_200(self, client: TestClient, auth_user, session):
        """Test toggling task to completed returns 200."""
        # Arrange
        user_id = str(auth_user["user"].id)
        task = Task(user_id=auth_user["user"].id, title="To Complete", completed=False)
        session.add(task)
        session.commit()

        # Act
        response = client.patch(
            f"/api/{user_id}/tasks/{task.id}/complete",
            json={"completed": True},
            headers=auth_user["headers"],
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["completed"] is True

    def test_toggle_complete_to_false_returns_200(self, client: TestClient, auth_user, session):
        """Test toggling task to incomplete returns 200."""
        # Arrange
        user_id = str(auth_user["user"].id)
        task = Task(user_id=auth_user["user"].id, title="To Uncomplete", completed=True)
        session.add(task)
        session.commit()

        # Act
        response = client.patch(
            f"/api/{user_id}/tasks/{task.id}/complete",
            json={"completed": False},
            headers=auth_user["headers"],
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["completed"] is False


class TestExportTasksAPI:
    """Tests for GET /api/{user_id}/tasks/export endpoint."""

    def test_export_csv_returns_csv_file(self, client: TestClient, auth_user, session):
        """Test exporting tasks as CSV returns CSV file."""
        # Arrange
        user_id = str(auth_user["user"].id)
        session.add(Task(user_id=auth_user["user"].id, title="Task 1", completed=False))
        session.add(Task(user_id=auth_user["user"].id, title="Task 2", completed=True))
        session.commit()

        # Act
        response = client.get(
            f"/api/{user_id}/tasks/export?format=csv", headers=auth_user["headers"]
        )

        # Assert
        assert response.status_code == 200
        assert response.headers["content-type"] == "text/csv; charset=utf-8"
        assert "attachment" in response.headers["content-disposition"]
        assert "Task 1" in response.text
        assert "Task 2" in response.text

    def test_export_json_returns_json_file(self, client: TestClient, auth_user, session):
        """Test exporting tasks as JSON returns JSON file."""
        # Arrange
        user_id = str(auth_user["user"].id)
        session.add(Task(user_id=auth_user["user"].id, title="JSON Task", completed=False))
        session.commit()

        # Act
        response = client.get(
            f"/api/{user_id}/tasks/export?format=json", headers=auth_user["headers"]
        )

        # Assert
        assert response.status_code == 200
        assert "application/json" in response.headers["content-type"]
        assert "JSON Task" in response.text


class TestImportTasksAPI:
    """Tests for POST /api/{user_id}/tasks/import endpoint."""

    def test_import_csv_valid_file_returns_200(self, client: TestClient, auth_user):
        """Test importing valid CSV file returns 200 with import results."""
        # Arrange
        user_id = str(auth_user["user"].id)
        csv_content = b"""title,description,priority
Import Task 1,Description 1,high
Import Task 2,Description 2,low"""

        # Act
        response = client.post(
            f"/api/{user_id}/tasks/import",
            files={"file": ("tasks.csv", csv_content, "text/csv")},
            headers=auth_user["headers"],
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["imported"] == 2

    def test_import_json_valid_file_returns_200(self, client: TestClient, auth_user):
        """Test importing valid JSON file returns 200 with import results."""
        # Arrange
        user_id = str(auth_user["user"].id)
        json_content = b'[{"title": "JSON Import", "priority": "medium"}]'

        # Act
        response = client.post(
            f"/api/{user_id}/tasks/import",
            files={"file": ("tasks.json", json_content, "application/json")},
            headers=auth_user["headers"],
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["imported"] == 1


class TestStatisticsAPI:
    """Tests for GET /api/{user_id}/tasks/statistics endpoint."""

    def test_get_statistics_returns_200_with_stats(self, client: TestClient, auth_user, session):
        """Test getting statistics returns 200 with task statistics."""
        # Arrange
        user_id = str(auth_user["user"].id)
        from datetime import date

        session.add(Task(user_id=auth_user["user"].id, title="Completed", completed=True, priority="high"))
        session.add(Task(user_id=auth_user["user"].id, title="Pending", completed=False, priority="medium"))
        session.add(
            Task(
                user_id=auth_user["user"].id,
                title="Overdue",
                completed=False,
                priority="low",
                due_date=date.today() - timedelta(days=1),
            )
        )
        session.commit()

        # Act
        response = client.get(f"/api/{user_id}/tasks/statistics", headers=auth_user["headers"])

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["total"] == 3
        assert data["data"]["completed"] == 1
        assert data["data"]["pending"] == 2
        assert data["data"]["overdue"] == 1


class TestBulkOperationsAPI:
    """Tests for POST /api/{user_id}/tasks/bulk endpoint."""

    def test_bulk_delete_returns_200_with_results(self, client: TestClient, auth_user, session):
        """Test bulk delete returns 200 with operation results."""
        # Arrange
        user_id = str(auth_user["user"].id)
        task1 = Task(user_id=auth_user["user"].id, title="Task 1", completed=False)
        task2 = Task(user_id=auth_user["user"].id, title="Task 2", completed=False)
        session.add_all([task1, task2])
        session.commit()

        # Act
        response = client.post(
            f"/api/{user_id}/tasks/bulk?operation=delete&task_ids={task1.id}&task_ids={task2.id}",
            headers=auth_user["headers"],
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["success"] == 2
        assert data["data"]["failed"] == 0

    def test_bulk_complete_returns_200(self, client: TestClient, auth_user, session):
        """Test bulk complete marks all tasks as completed."""
        # Arrange
        user_id = str(auth_user["user"].id)
        task1 = Task(user_id=auth_user["user"].id, title="Task 1", completed=False)
        task2 = Task(user_id=auth_user["user"].id, title="Task 2", completed=False)
        session.add_all([task1, task2])
        session.commit()

        # Act
        response = client.post(
            f"/api/{user_id}/tasks/bulk?operation=complete&task_ids={task1.id}&task_ids={task2.id}",
            headers=auth_user["headers"],
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["success"] == 2

    def test_bulk_operations_empty_task_ids_returns_400(self, client: TestClient, auth_user):
        """Test bulk operations with empty task_ids returns 400."""
        # Arrange
        user_id = str(auth_user["user"].id)

        # Act
        response = client.post(
            f"/api/{user_id}/tasks/bulk?operation=delete", headers=auth_user["headers"]
        )

        # Assert
        assert response.status_code == 400
