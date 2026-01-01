"""
Integration tests for Intermediate Level features (Phase II) with Phase V features.

This module tests that Phase II Intermediate features (priorities, tags, search, filter, sort)
work correctly with Phase V features (recurring tasks, reminders).

Tests:
- T172: Task filtering by priority works with recurring tasks
- T173: Task filtering by tags works with recurring task instances
- T174: Task search includes recurring_pattern in searchable fields
- T175: Task sorting includes next_occurrence field for recurring tasks
- T176: Task filtering by due_date includes next_occurrence for recurring tasks
- T177: End-to-end verification of all Intermediate features with Phase V
"""

import pytest
from datetime import datetime, timedelta
from httpx import AsyncClient
from sqlmodel import Session

from main import app
from db import get_session
from models import Task
from tests.conftest import authenticated_client


class TestPriorityFilteringWithRecurringTasks:
    """Test priority filtering with recurring tasks (T172)."""

    @pytest.mark.asyncio
    async def test_filter_high_priority_recurring_tasks(
        self, authenticated_client: AsyncClient, db_session: Session
    ):
        """Test filtering high priority recurring tasks."""
        user_id = "test-user-123"

        # Create high priority recurring task
        high_recurring = Task(
            title="Daily standup",
            user_id=user_id,
            priority="high",
            recurring_pattern="DAILY",
            next_occurrence=datetime.utcnow() + timedelta(days=1),
        )

        # Create high priority non-recurring task
        high_normal = Task(
            title="Urgent fix",
            user_id=user_id,
            priority="high",
        )

        # Create low priority recurring task
        low_recurring = Task(
            title="Weekly cleanup",
            user_id=user_id,
            priority="low",
            recurring_pattern="WEEKLY",
            next_occurrence=datetime.utcnow() + timedelta(days=7),
        )

        db_session.add_all([high_recurring, high_normal, low_recurring])
        db_session.commit()

        # Filter by high priority
        response = await authenticated_client.get(
            f"/api/{user_id}/tasks",
            params={"priority": "high"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        items = data["data"]["items"]

        # Should return 2 high priority tasks (1 recurring, 1 normal)
        assert len(items) == 2
        assert all(task["priority"] == "high" for task in items)

        # Verify recurring task is included
        recurring_titles = [task["title"] for task in items if task.get("recurring_pattern")]
        assert "Daily standup" in recurring_titles

    @pytest.mark.asyncio
    async def test_filter_multiple_priorities_with_recurring(
        self, authenticated_client: AsyncClient, db_session: Session
    ):
        """Test filtering multiple priorities with recurring tasks."""
        user_id = "test-user-456"

        # Create tasks with different priorities
        tasks = [
            Task(title="High recurring", user_id=user_id, priority="high", recurring_pattern="DAILY"),
            Task(title="Medium recurring", user_id=user_id, priority="medium", recurring_pattern="WEEKLY"),
            Task(title="Low recurring", user_id=user_id, priority="low", recurring_pattern="MONTHLY"),
        ]

        db_session.add_all(tasks)
        db_session.commit()

        # Filter by medium and low priority
        response = await authenticated_client.get(
            f"/api/{user_id}/tasks",
            params={"priority": "medium,low"}
        )

        assert response.status_code == 200
        data = response.json()
        items = data["data"]["items"]

        assert len(items) == 2
        priorities = {task["priority"] for task in items}
        assert priorities == {"medium", "low"}


class TestTagFilteringWithRecurringTasks:
    """Test tag filtering with recurring task instances (T173)."""

    @pytest.mark.asyncio
    async def test_filter_tags_with_recurring_instances(
        self, authenticated_client: AsyncClient, db_session: Session
    ):
        """Test tag filtering includes recurring task instances."""
        user_id = "test-user-789"

        # Create recurring task with tags
        recurring_task = Task(
            title="Daily review",
            user_id=user_id,
            tags=["work", "review"],
            recurring_pattern="DAILY",
            next_occurrence=datetime.utcnow() + timedelta(days=1),
        )

        # Create non-recurring task with same tags
        normal_task = Task(
            title="One-time review",
            user_id=user_id,
            tags=["work", "review"],
        )

        # Create recurring task with different tags
        other_recurring = Task(
            title="Weekly planning",
            user_id=user_id,
            tags=["planning"],
            recurring_pattern="WEEKLY",
        )

        db_session.add_all([recurring_task, normal_task, other_recurring])
        db_session.commit()

        # Filter by "work" tag
        response = await authenticated_client.get(
            f"/api/{user_id}/tasks",
            params={"tags": "work"}
        )

        assert response.status_code == 200
        data = response.json()
        items = data["data"]["items"]

        # Should return 2 tasks with "work" tag (1 recurring, 1 normal)
        assert len(items) == 2
        assert all("work" in task["tags"] for task in items)

    @pytest.mark.asyncio
    async def test_filter_multiple_tags_recurring_tasks(
        self, authenticated_client: AsyncClient, db_session: Session
    ):
        """Test filtering multiple tags with recurring tasks."""
        user_id = "test-user-101"

        tasks = [
            Task(title="Task 1", user_id=user_id, tags=["work", "urgent"], recurring_pattern="DAILY"),
            Task(title="Task 2", user_id=user_id, tags=["personal"], recurring_pattern="WEEKLY"),
            Task(title="Task 3", user_id=user_id, tags=["work", "planning"]),
        ]

        db_session.add_all(tasks)
        db_session.commit()

        # Filter by "work" AND "urgent" tags
        response = await authenticated_client.get(
            f"/api/{user_id}/tasks",
            params={"tags": "work,urgent"}
        )

        assert response.status_code == 200
        data = response.json()
        items = data["data"]["items"]

        # Should return only Task 1
        assert len(items) == 1
        assert items[0]["title"] == "Task 1"
        assert "work" in items[0]["tags"]
        assert "urgent" in items[0]["tags"]


class TestSearchWithRecurringPattern:
    """Test search includes recurring_pattern in searchable fields (T174)."""

    @pytest.mark.asyncio
    async def test_search_daily_recurring_tasks(
        self, authenticated_client: AsyncClient, db_session: Session
    ):
        """Test search for 'daily recurring tasks'."""
        user_id = "test-user-202"

        # Create recurring tasks with different patterns
        daily_task = Task(
            title="Daily standup",
            user_id=user_id,
            recurring_pattern="DAILY",
        )

        weekly_task = Task(
            title="Weekly review",
            user_id=user_id,
            recurring_pattern="WEEKLY",
        )

        normal_task = Task(
            title="Daily normal task",  # Has "daily" in title but not recurring
            user_id=user_id,
        )

        db_session.add_all([daily_task, weekly_task, normal_task])
        db_session.commit()

        # Search for "daily"
        response = await authenticated_client.get(
            f"/api/{user_id}/tasks",
            params={"search": "daily"}
        )

        assert response.status_code == 200
        data = response.json()
        items = data["data"]["items"]

        # Should return both tasks with "daily" in title or pattern
        assert len(items) == 2
        titles = {task["title"] for task in items}
        assert "Daily standup" in titles
        assert "Daily normal task" in titles

    @pytest.mark.asyncio
    async def test_search_recurring_pattern_keyword(
        self, authenticated_client: AsyncClient, db_session: Session
    ):
        """Test search specifically for recurring pattern keyword."""
        user_id = "test-user-303"

        tasks = [
            Task(title="Task 1", user_id=user_id, recurring_pattern="DAILY"),
            Task(title="Task 2", user_id=user_id, recurring_pattern="WEEKLY"),
            Task(title="Task 3", user_id=user_id, recurring_pattern="MONTHLY"),
            Task(title="Recurring task", user_id=user_id),  # Not actually recurring
        ]

        db_session.add_all(tasks)
        db_session.commit()

        # Search for "weekly"
        response = await authenticated_client.get(
            f"/api/{user_id}/tasks",
            params={"search": "weekly"}
        )

        assert response.status_code == 200
        data = response.json()
        items = data["data"]["items"]

        # Should return only Task 2 with WEEKLY pattern
        assert len(items) == 1
        assert items[0]["title"] == "Task 2"
        assert items[0]["recurring_pattern"] == "WEEKLY"


class TestSortingWithNextOccurrence:
    """Test sorting includes next_occurrence field for recurring tasks (T175)."""

    @pytest.mark.asyncio
    async def test_sort_by_next_occurrence_ascending(
        self, authenticated_client: AsyncClient, db_session: Session
    ):
        """Test sorting by next occurrence date (ascending)."""
        user_id = "test-user-404"

        now = datetime.utcnow()

        # Create recurring tasks with different next occurrences
        task1 = Task(
            title="Task 1",
            user_id=user_id,
            recurring_pattern="DAILY",
            next_occurrence=now + timedelta(days=3),
        )

        task2 = Task(
            title="Task 2",
            user_id=user_id,
            recurring_pattern="WEEKLY",
            next_occurrence=now + timedelta(days=1),  # Earliest
        )

        task3 = Task(
            title="Task 3",
            user_id=user_id,
            recurring_pattern="MONTHLY",
            next_occurrence=now + timedelta(days=7),
        )

        db_session.add_all([task1, task2, task3])
        db_session.commit()

        # Sort by next_occurrence ascending
        response = await authenticated_client.get(
            f"/api/{user_id}/tasks",
            params={"sort": "next_occurrence:asc"}
        )

        assert response.status_code == 200
        data = response.json()
        items = data["data"]["items"]

        # Should return tasks ordered by next_occurrence
        assert len(items) == 3
        assert items[0]["title"] == "Task 2"  # +1 day
        assert items[1]["title"] == "Task 1"  # +3 days
        assert items[2]["title"] == "Task 3"  # +7 days

    @pytest.mark.asyncio
    async def test_sort_by_next_occurrence_descending(
        self, authenticated_client: AsyncClient, db_session: Session
    ):
        """Test sorting by next occurrence date (descending)."""
        user_id = "test-user-505"

        now = datetime.utcnow()

        tasks = [
            Task(title="Task 1", user_id=user_id, recurring_pattern="DAILY", next_occurrence=now + timedelta(days=1)),
            Task(title="Task 2", user_id=user_id, recurring_pattern="WEEKLY", next_occurrence=now + timedelta(days=7)),
            Task(title="Task 3", user_id=user_id, recurring_pattern="MONTHLY", next_occurrence=now + timedelta(days=30)),
        ]

        db_session.add_all(tasks)
        db_session.commit()

        # Sort by next_occurrence descending
        response = await authenticated_client.get(
            f"/api/{user_id}/tasks",
            params={"sort": "next_occurrence:desc"}
        )

        assert response.status_code == 200
        data = response.json()
        items = data["data"]["items"]

        assert len(items) == 3
        assert items[0]["title"] == "Task 3"  # +30 days (latest)
        assert items[1]["title"] == "Task 2"  # +7 days
        assert items[2]["title"] == "Task 1"  # +1 day (earliest)


class TestDueDateFilteringWithNextOccurrence:
    """Test due_date filtering includes next_occurrence for recurring tasks (T176)."""

    @pytest.mark.asyncio
    async def test_filter_due_date_includes_next_occurrence(
        self, authenticated_client: AsyncClient, db_session: Session
    ):
        """Test filtering by due_date includes next_occurrence."""
        user_id = "test-user-606"

        now = datetime.utcnow()
        tomorrow = now + timedelta(days=1)
        next_week = now + timedelta(days=7)

        # Create recurring task with next_occurrence tomorrow
        recurring_task = Task(
            title="Daily task",
            user_id=user_id,
            recurring_pattern="DAILY",
            next_occurrence=tomorrow,
        )

        # Create normal task with due_date tomorrow
        normal_task = Task(
            title="Normal task",
            user_id=user_id,
            due_date=tomorrow,
        )

        # Create recurring task with next_occurrence next week
        future_task = Task(
            title="Weekly task",
            user_id=user_id,
            recurring_pattern="WEEKLY",
            next_occurrence=next_week,
        )

        db_session.add_all([recurring_task, normal_task, future_task])
        db_session.commit()

        # Filter tasks due from now to tomorrow
        response = await authenticated_client.get(
            f"/api/{user_id}/tasks",
            params={
                "due_date_from": now.isoformat(),
                "due_date_to": (tomorrow + timedelta(hours=1)).isoformat(),
            }
        )

        assert response.status_code == 200
        data = response.json()
        items = data["data"]["items"]

        # Should return 2 tasks (both due tomorrow)
        assert len(items) == 2
        titles = {task["title"] for task in items}
        assert "Daily task" in titles
        assert "Normal task" in titles

    @pytest.mark.asyncio
    async def test_filter_by_due_date_range_recurring_only(
        self, authenticated_client: AsyncClient, db_session: Session
    ):
        """Test filtering recurring tasks by date range."""
        user_id = "test-user-707"

        now = datetime.utcnow()

        tasks = [
            Task(title="Task 1", user_id=user_id, recurring_pattern="DAILY", next_occurrence=now + timedelta(days=1)),
            Task(title="Task 2", user_id=user_id, recurring_pattern="WEEKLY", next_occurrence=now + timedelta(days=7)),
            Task(title="Task 3", user_id=user_id, recurring_pattern="MONTHLY", next_occurrence=now + timedelta(days=30)),
        ]

        db_session.add_all(tasks)
        db_session.commit()

        # Filter for tasks due in next 10 days
        response = await authenticated_client.get(
            f"/api/{user_id}/tasks",
            params={
                "due_date_from": now.isoformat(),
                "due_date_to": (now + timedelta(days=10)).isoformat(),
            }
        )

        assert response.status_code == 200
        data = response.json()
        items = data["data"]["items"]

        # Should return 2 tasks (Task 1 and Task 2, not Task 3)
        assert len(items) == 2
        titles = {task["title"] for task in items}
        assert "Task 1" in titles
        assert "Task 2" in titles
        assert "Task 3" not in titles


class TestEndToEndIntermediateFeaturesPhase5:
    """End-to-end tests for all Intermediate features with Phase V (T177)."""

    @pytest.mark.asyncio
    async def test_combined_filters_sort_search_recurring(
        self, authenticated_client: AsyncClient, db_session: Session
    ):
        """Test combined filtering, sorting, and search with recurring tasks."""
        user_id = "test-user-808"

        now = datetime.utcnow()

        # Create complex task set
        tasks = [
            # High priority daily recurring with tags
            Task(
                title="Daily standup",
                user_id=user_id,
                priority="high",
                tags=["work", "meeting"],
                recurring_pattern="DAILY",
                next_occurrence=now + timedelta(days=1),
            ),
            # High priority weekly recurring with tags
            Task(
                title="Weekly review",
                user_id=user_id,
                priority="high",
                tags=["work", "review"],
                recurring_pattern="WEEKLY",
                next_occurrence=now + timedelta(days=7),
            ),
            # Medium priority normal task
            Task(
                title="One-time task",
                user_id=user_id,
                priority="medium",
                tags=["work"],
            ),
            # Low priority monthly recurring
            Task(
                title="Monthly cleanup",
                user_id=user_id,
                priority="low",
                tags=["cleanup"],
                recurring_pattern="MONTHLY",
                next_occurrence=now + timedelta(days=30),
            ),
        ]

        db_session.add_all(tasks)
        db_session.commit()

        # Filter: high priority + "work" tag + sort by next_occurrence + search "review"
        response = await authenticated_client.get(
            f"/api/{user_id}/tasks",
            params={
                "priority": "high",
                "tags": "work",
                "sort": "next_occurrence:asc",
                "search": "review",
            }
        )

        assert response.status_code == 200
        data = response.json()
        items = data["data"]["items"]

        # Should return only "Weekly review" (high priority, has "work" tag, matches "review" search)
        assert len(items) == 1
        assert items[0]["title"] == "Weekly review"
        assert items[0]["priority"] == "high"
        assert "work" in items[0]["tags"]
        assert items[0]["recurring_pattern"] == "WEEKLY"

    @pytest.mark.asyncio
    async def test_pagination_with_recurring_filters(
        self, authenticated_client: AsyncClient, db_session: Session
    ):
        """Test pagination with recurring task filters."""
        user_id = "test-user-909"

        # Create 15 recurring tasks
        tasks = [
            Task(
                title=f"Task {i}",
                user_id=user_id,
                priority="high" if i % 2 == 0 else "low",
                recurring_pattern="DAILY",
                next_occurrence=datetime.utcnow() + timedelta(days=i),
            )
            for i in range(1, 16)
        ]

        db_session.add_all(tasks)
        db_session.commit()

        # Get page 1 (limit 5) with high priority filter
        response = await authenticated_client.get(
            f"/api/{user_id}/tasks",
            params={
                "priority": "high",
                "sort": "next_occurrence:asc",
                "page": 1,
                "limit": 5,
            }
        )

        assert response.status_code == 200
        data = response.json()

        # Should return 5 tasks
        assert len(data["data"]["items"]) == 5
        assert data["data"]["total"] == 7  # 7 high priority tasks total
        assert data["data"]["totalPages"] == 2  # 7 tasks / 5 per page = 2 pages

        # All should be high priority
        assert all(task["priority"] == "high" for task in data["data"]["items"])
