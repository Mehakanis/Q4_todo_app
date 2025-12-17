"""
MCP Server for task management operations (Phase III).

This module implements a proper MCP server using the FastMCP SDK.
The server exposes task operations as MCP tools that can be called by AI agents.

MCP Tools provided:
- add_task: Create a new task for a user
- list_tasks: Retrieve tasks with optional filtering
- complete_task: Mark a task as complete
- delete_task: Remove a task from the database
- update_task: Modify task title or description

Architecture:
- MCP Server runs as a separate process (not inside agent)
- Agent connects via MCPServerStdio transport
- Tools use @mcp.tool() decorator (not @function_tool)
"""

from typing import Literal, Optional

from mcp.server.fastmcp import FastMCP
from sqlmodel import Session

from db import get_session
from services.task_service import TaskService
from schemas.requests import CreateTaskRequest

# Create MCP server instance
mcp = FastMCP("task-management-server")


@mcp.tool()
def add_task(
    user_id: str,
    title: str,
    description: Optional[str] = None,
) -> dict:
    """
    Create a new task for a user.

    MCP Tool Contract:
    - Purpose: Add a task to user's todo list
    - Stateless: All state persisted to database
    - User Isolation: Enforced via user_id parameter

    Args:
        user_id: User's unique identifier (string UUID from Better Auth)
        title: Task title (required, max 200 characters)
        description: Task description (optional, max 1000 characters)

    Returns:
        dict: Task creation result
            - task_id (int): Created task ID
            - status (str): "created"
            - title (str): Task title

    Example:
        >>> add_task(user_id="user-123", title="Buy groceries", description="Milk, eggs, bread")
        {"task_id": 42, "status": "created", "title": "Buy groceries"}
    """
    # Get database session
    session = next(get_session())

    try:
        # Create task using task_service
        task_data = CreateTaskRequest(
            title=title,
            description=description,
            priority="medium",  # Default priority
            due_date=None,
            tags=None,
        )

        created_task = TaskService.create_task(
            db=session,
            user_id=user_id,
            task_data=task_data
        )

        # Return MCP tool response
        return {
            "task_id": created_task.id,
            "status": "created",
            "title": created_task.title,
        }

    finally:
        session.close()


@mcp.tool()
def list_tasks(
    user_id: str,
    status: Literal["all", "pending", "completed"] = "all",
) -> dict:
    """
    Retrieve tasks from user's todo list.

    MCP Tool Contract:
    - Purpose: List tasks with optional status filtering
    - Stateless: Queries database on each invocation
    - User Isolation: Enforced via user_id parameter

    Args:
        user_id: User's unique identifier (string UUID from Better Auth)
        status: Filter by completion status (default: "all")
            - "all": All tasks
            - "pending": Incomplete tasks only
            - "completed": Completed tasks only

    Returns:
        dict: Task list result
            - tasks (list): Array of task objects
                - id (int): Task ID
                - title (str): Task title
                - description (str|None): Task description
                - completed (bool): Completion status
                - priority (str): Priority level
                - created_at (str): ISO 8601 timestamp
            - count (int): Total number of tasks returned

    Example:
        >>> list_tasks(user_id="user-123", status="pending")
        {
            "tasks": [
                {"id": 1, "title": "Buy groceries", "completed": False, ...},
                {"id": 2, "title": "Call dentist", "completed": False, ...}
            ],
            "count": 2
        }
    """
    # Get database session
    session = next(get_session())

    try:
        # Import query params for filtering
        from schemas.query_params import TaskQueryParams

        # Create query params for status filtering
        query_params = TaskQueryParams(
            status=status,
            page=1,
            limit=100,  # Reasonable limit for chat context
        )

        # Get tasks using task_service
        tasks, metadata = TaskService.get_tasks(
            db=session,
            user_id=user_id,
            query_params=query_params
        )

        # Convert tasks to dict format
        task_list = [
            {
                "id": task.id,
                "title": task.title,
                "description": task.description,
                "completed": task.completed,
                "priority": task.priority,
                "due_date": task.due_date.isoformat() if task.due_date else None,
                "created_at": task.created_at.isoformat(),
            }
            for task in tasks
        ]

        # Return MCP tool response
        return {
            "tasks": task_list,
            "count": len(task_list),
        }

    finally:
        session.close()


@mcp.tool()
def complete_task(
    user_id: str,
    task_id: int,
) -> dict:
    """
    Mark a task as complete.

    MCP Tool Contract:
    - Purpose: Toggle task completion status to completed
    - Stateless: Updates database and returns result
    - User Isolation: Enforced via user_id parameter

    Args:
        user_id: User's unique identifier (string UUID from Better Auth)
        task_id: Task ID to mark as complete

    Returns:
        dict: Task completion result
            - task_id (int): Updated task ID
            - status (str): "completed"
            - title (str): Task title

    Raises:
        HTTPException: 404 if task not found or user doesn't have access

    Example:
        >>> complete_task(user_id="user-123", task_id=3)
        {"task_id": 3, "status": "completed", "title": "Call dentist"}
    """
    # Get database session
    session = next(get_session())

    try:
        # Mark task as complete using task_service
        updated_task = TaskService.toggle_complete(
            db=session,
            user_id=user_id,
            task_id=task_id,
            completed=True
        )

        # Return MCP tool response
        return {
            "task_id": updated_task.id,
            "status": "completed",
            "title": updated_task.title,
        }

    finally:
        session.close()


@mcp.tool()
def delete_task(
    user_id: str,
    task_id: int,
) -> dict:
    """
    Remove a task from the todo list.

    MCP Tool Contract:
    - Purpose: Permanently delete task from database
    - Stateless: Deletes from database and returns confirmation
    - User Isolation: Enforced via user_id parameter

    Args:
        user_id: User's unique identifier (string UUID from Better Auth)
        task_id: Task ID to delete

    Returns:
        dict: Task deletion result
            - task_id (int): Deleted task ID
            - status (str): "deleted"
            - title (str): Task title (from pre-deletion state)

    Raises:
        HTTPException: 404 if task not found or user doesn't have access

    Example:
        >>> delete_task(user_id="user-123", task_id=2)
        {"task_id": 2, "status": "deleted", "title": "Old reminder"}
    """
    # Get database session
    session = next(get_session())

    try:
        # Get task details before deletion (for response)
        task = TaskService.get_task_by_id(
            db=session,
            user_id=user_id,
            task_id=task_id
        )

        task_title = task.title

        # Delete task using task_service
        TaskService.delete_task(
            db=session,
            user_id=user_id,
            task_id=task_id
        )

        # Return MCP tool response
        return {
            "task_id": task_id,
            "status": "deleted",
            "title": task_title,
        }

    finally:
        session.close()


@mcp.tool()
def update_task(
    user_id: str,
    task_id: int,
    title: Optional[str] = None,
    description: Optional[str] = None,
) -> dict:
    """
    Modify task title or description.

    MCP Tool Contract:
    - Purpose: Update task details
    - Stateless: Updates database and returns result
    - User Isolation: Enforced via user_id parameter
    - Partial Updates: At least one of title or description must be provided

    Args:
        user_id: User's unique identifier (string UUID from Better Auth)
        task_id: Task ID to update
        title: New task title (optional, max 200 characters)
        description: New task description (optional, max 1000 characters)

    Returns:
        dict: Task update result
            - task_id (int): Updated task ID
            - status (str): "updated"
            - title (str): Updated task title

    Raises:
        HTTPException: 404 if task not found or user doesn't have access
        HTTPException: 400 if neither title nor description provided

    Example:
        >>> update_task(user_id="user-123", task_id=1, title="Buy groceries and fruits")
        {"task_id": 1, "status": "updated", "title": "Buy groceries and fruits"}
    """
    # Get database session
    session = next(get_session())

    try:
        # Validate: at least one field must be provided
        if title is None and description is None:
            from fastapi import HTTPException, status
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="At least one of 'title' or 'description' must be provided"
            )

        # Create update request
        from schemas.requests import UpdateTaskRequest
        update_data = UpdateTaskRequest(
            title=title,
            description=description,
        )

        # Update task using task_service
        updated_task = TaskService.update_task(
            db=session,
            user_id=user_id,
            task_id=task_id,
            task_data=update_data
        )

        # Return MCP tool response
        return {
            "task_id": updated_task.id,
            "status": "updated",
            "title": updated_task.title,
        }

    finally:
        session.close()


@mcp.tool()
def bulk_update_tasks(
    user_id: str,
    action: Literal["complete", "delete"] = "complete",
    filter_status: Literal["all", "pending", "completed"] = "pending",
) -> dict:
    """
    Perform bulk operations on multiple tasks at once.

    MCP Tool Contract:
    - Purpose: Update multiple tasks efficiently in a single operation
    - Stateless: All state persisted to database
    - User Isolation: Enforced via user_id parameter
    - Efficiency: Uses direct SQL UPDATE/DELETE for optimal performance

    Args:
        user_id: User's unique identifier (string UUID from Better Auth)
        action: Bulk operation to perform (default: "complete")
            - "complete": Mark all matching tasks as completed
            - "delete": Delete all matching tasks
        filter_status: Filter which tasks to update (default: "pending")
            - "pending": Only incomplete tasks
            - "completed": Only complete tasks
            - "all": All tasks

    Returns:
        dict: Bulk operation result
            - count (int): Number of tasks updated
            - action (str): Action performed

    Example:
        >>> bulk_update_tasks(user_id="user-123", action="complete", filter_status="pending")
        {"count": 5, "action": "completed"}
    """
    from sqlmodel import select, update, delete
    from models import Task

    # Get database session
    session = next(get_session())

    try:
        # First, get the count of affected tasks
        count_statement = select(Task).where(Task.user_id == user_id)

        if filter_status == "pending":
            count_statement = count_statement.where(Task.completed == False)
        elif filter_status == "completed":
            count_statement = count_statement.where(Task.completed == True)

        affected_tasks = session.exec(count_statement).all()
        count = len(affected_tasks)

        if count == 0:
            return {
                "count": 0,
                "action": action,
                "message": f"No {filter_status} tasks found to {action}",
            }

        # Perform bulk action using direct SQL for optimal performance
        if action == "complete":
            # Build UPDATE statement for completion
            update_statement = update(Task).where(Task.user_id == user_id)

            if filter_status == "pending":
                update_statement = update_statement.where(Task.completed == False)
            elif filter_status == "completed":
                update_statement = update_statement.where(Task.completed == True)

            # Set completed to True
            update_statement = update_statement.values(completed=True)

            # Execute the update
            session.execute(update_statement)
            session.commit()

            return {
                "count": count,
                "action": "completed",
                "message": f"Marked {count} task(s) as completed",
            }

        elif action == "delete":
            # Build DELETE statement for deletion
            delete_statement = delete(Task).where(Task.user_id == user_id)

            if filter_status == "pending":
                delete_statement = delete_statement.where(Task.completed == False)
            elif filter_status == "completed":
                delete_statement = delete_statement.where(Task.completed == True)

            # Execute the delete
            session.execute(delete_statement)
            session.commit()

            return {
                "count": count,
                "action": "deleted",
                "message": f"Deleted {count} task(s)",
            }

        else:
            raise ValueError(f"Unsupported bulk action: {action}")

    finally:
        session.close()
