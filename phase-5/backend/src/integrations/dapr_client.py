"""
Dapr Client - Phase V

Complete Dapr integration with all 5 building blocks:
1. Pub/Sub (Kafka) - Event publishing and subscription
2. State Store (PostgreSQL) - Conversation history storage
3. Jobs API (Scheduler) - Reminder scheduling
4. Secrets Management - Kubernetes/Cloud vault integration
5. Service Invocation - Service-to-service communication with mTLS

Based on: .claude/skills/dapr-integration/templates/dapr_client.py
"""

import httpx
from typing import Dict, List, Optional, Any
from datetime import datetime
import uuid
import logging

logger = logging.getLogger(__name__)


class DaprClient:
    """
    Complete Dapr client with all 5 building blocks for Phase V.

    Usage:
        dapr = DaprClient()
        await dapr.publish_event("task-events", {"user_id": "123", "task_id": 456})
    """

    def __init__(
        self,
        dapr_port: int = 3500,
        pubsub_name: str = "kafka-pubsub",
        state_store_name: str = "statestore",
        secrets_store_name: str = "kubernetes-secrets"
    ):
        """
        Initialize Dapr client.

        Args:
            dapr_port: Dapr sidecar HTTP port (default: 3500)
            pubsub_name: Dapr Pub/Sub component name (default: kafka-pubsub)
            state_store_name: Dapr State Store component name (default: statestore)
            secrets_store_name: Dapr Secrets component name (default: kubernetes-secrets)
        """
        self.dapr_url = f"http://localhost:{dapr_port}"
        self.pubsub_name = pubsub_name
        self.state_store_name = state_store_name
        self.secrets_store_name = secrets_store_name

    # ==================== Pub/Sub (Building Block 1) ====================

    async def publish_event(
        self,
        topic: str,
        event_data: Dict[str, Any],
        user_id: Optional[str] = None
    ) -> None:
        """
        Publish event to Kafka topic via Dapr Pub/Sub.

        Args:
            topic: Kafka topic name (task-events, reminders, task-updates)
            event_data: Event payload (must include user_id for partitioning)
            user_id: User ID for partitioning (if not in event_data)

        Raises:
            httpx.HTTPStatusError: If publish fails
        """
        # Ensure user_id is in event (required for Kafka partitioning)
        if user_id and "user_id" not in event_data:
            event_data["user_id"] = user_id

        # Add event metadata if not present
        if "event_id" not in event_data:
            event_data["event_id"] = str(uuid.uuid4())

        if "timestamp" not in event_data:
            event_data["timestamp"] = datetime.utcnow().isoformat() + "Z"

        url = f"{self.dapr_url}/v1.0/publish/{self.pubsub_name}/{topic}"

        logger.info(f"Publishing event to topic '{topic}': event_id={event_data.get('event_id')}, user_id={event_data.get('user_id')}")

        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                url,
                json=event_data,
                headers={"Content-Type": "application/json"}
            )
            response.raise_for_status()

        logger.info(f"Event published successfully to topic '{topic}'")

    # ==================== State Store (Building Block 2) ====================

    async def save_state(
        self,
        key: str,
        value: Dict[str, Any]
    ) -> None:
        """
        Save state to Dapr State Store (PostgreSQL).

        Note: State Store is ONLY used for conversation history (per Clarification #4).
        Tasks are NOT cached in State Store - all task queries go to PostgreSQL.

        Args:
            key: State key (e.g., "conversation-{user_id}-{conversation_id}")
            value: State value (dict)

        Raises:
            httpx.HTTPStatusError: If save fails
        """
        url = f"{self.dapr_url}/v1.0/state/{self.state_store_name}"

        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.post(
                url,
                json=[{"key": key, "value": value}],
                headers={"Content-Type": "application/json"}
            )
            response.raise_for_status()

        logger.debug(f"State saved: key={key}")

    async def get_state(
        self,
        key: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get state from Dapr State Store.

        Args:
            key: State key

        Returns:
            State value or None if not found

        Raises:
            httpx.HTTPStatusError: If get fails (except 404)
        """
        url = f"{self.dapr_url}/v1.0/state/{self.state_store_name}/{key}"

        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(url)
            if response.status_code == 404:
                return None
            response.raise_for_status()
            return response.json()

    async def delete_state(self, key: str) -> None:
        """
        Delete state from Dapr State Store.

        Args:
            key: State key to delete

        Raises:
            httpx.HTTPStatusError: If delete fails
        """
        url = f"{self.dapr_url}/v1.0/state/{self.state_store_name}/{key}"

        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.delete(url)
            response.raise_for_status()

        logger.debug(f"State deleted: key={key}")

    # ==================== Jobs API (Building Block 3) ====================

    async def schedule_job(
        self,
        job_name: str,
        due_time: str | None = None,
        schedule: str | None = None,
        data: Dict[str, Any] | str | None = None,
        repeats: int | None = None,
        ttl: str | None = None
    ) -> None:
        """
        Schedule a job using Dapr Jobs API (exact-time scheduling for reminders).

        Args:
            job_name: Unique job identifier (e.g., "reminder-task-123")
            due_time: One-time execution time (ISO 8601/RFC3339 format)
            schedule: Recurring schedule (cron or "@every 1m" format)
            data: Job payload (dict will be JSON serialized, or pass string)
            repeats: Number of times to repeat
            ttl: Time to live for the job (RFC3339 or Go duration string)

        Raises:
            httpx.HTTPStatusError: If schedule fails
            ValueError: If neither due_time nor schedule provided

        Note: At least one of `due_time` or `schedule` must be provided.
        """
        if not due_time and not schedule:
            raise ValueError("At least one of 'due_time' or 'schedule' must be provided")

        url = f"{self.dapr_url}/v1.0-alpha1/jobs/{job_name}"

        # Prepare request body
        request_body: Dict[str, Any] = {}

        if due_time:
            request_body["dueTime"] = due_time
        if schedule:
            request_body["schedule"] = schedule
        if data:
            # If data is a dict, serialize it to JSON string (as per Dapr API)
            if isinstance(data, dict):
                import json
                request_body["data"] = json.dumps(data)
            else:
                request_body["data"] = data
        if repeats is not None:
            request_body["repeats"] = repeats
        if ttl:
            request_body["ttl"] = ttl

        logger.info(f"Scheduling job '{job_name}': due_time={due_time}, schedule={schedule}")

        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.post(
                url,
                json=request_body,
                headers={"Content-Type": "application/json"}
            )
            response.raise_for_status()

        logger.info(f"Job scheduled successfully: {job_name}")

    async def delete_job(self, job_name: str) -> None:
        """
        Delete a scheduled job.

        Args:
            job_name: Job identifier to delete

        Raises:
            httpx.HTTPStatusError: If delete fails
        """
        url = f"{self.dapr_url}/v1.0-alpha1/jobs/{job_name}"

        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.delete(url)
            response.raise_for_status()

        logger.info(f"Job deleted: {job_name}")

    # ==================== Secrets (Building Block 4) ====================

    async def get_secret(
        self,
        secret_name: str,
        key: Optional[str] = None
    ) -> str | Dict[str, Any]:
        """
        Get secret from Dapr Secrets API.

        Args:
            secret_name: Secret name in secret store
            key: Optional key within secret (if secret is a dict)

        Returns:
            Secret value (string if key provided, dict if not)

        Raises:
            httpx.HTTPStatusError: If get fails

        Note: Dapr Secrets API returns secrets directly as a dict (for Kubernetes)
        or as a single value (for Vault). The response format depends on the
        secret store type.
        """
        url = f"{self.dapr_url}/v1.0/secrets/{self.secrets_store_name}/{secret_name}"

        # Add key as query parameter if provided
        if key:
            url += f"?key={key}"

        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(url)
            response.raise_for_status()
            secrets = response.json()

            # For Kubernetes secrets, response is a dict like {"key1": "value1", "key2": "value2"}
            # For Vault, response is like {"secret-name": "value"}
            if key:
                # If key provided, return specific value
                return secrets.get(key) if isinstance(secrets, dict) else secrets
            return secrets

    # ==================== Service Invocation (Building Block 5) ====================

    async def invoke_service(
        self,
        app_id: str,
        method: str,
        data: Optional[Dict[str, Any]] = None,
        http_verb: str = "POST"
    ) -> Dict[str, Any]:
        """
        Invoke another service via Dapr Service Invocation (with mTLS).

        Args:
            app_id: Dapr app ID of target service
            method: API method path (e.g., "api/tasks")
            data: Optional request payload
            http_verb: HTTP method (POST, GET, PUT, DELETE)

        Returns:
            Service response (dict)

        Raises:
            httpx.HTTPStatusError: If invocation fails
        """
        url = f"{self.dapr_url}/v1.0/invoke/{app_id}/method/{method}"

        logger.info(f"Invoking service '{app_id}' method '{method}'")

        async with httpx.AsyncClient(timeout=30.0) as client:
            if http_verb == "POST":
                response = await client.post(url, json=data or {})
            elif http_verb == "GET":
                response = await client.get(url)
            elif http_verb == "PUT":
                response = await client.put(url, json=data or {})
            elif http_verb == "DELETE":
                response = await client.delete(url)
            else:
                raise ValueError(f"Unsupported HTTP verb: {http_verb}")

            response.raise_for_status()
            return response.json() if response.content else {}


# ==================== Singleton Instance ====================

# Global Dapr client instance (reused across requests)
_dapr_client: Optional[DaprClient] = None


def get_dapr_client() -> DaprClient:
    """
    Get singleton Dapr client instance.

    Returns:
        DaprClient instance

    Usage:
        from phase_5.backend.src.integrations.dapr_client import get_dapr_client

        dapr = get_dapr_client()
        await dapr.publish_event("task-events", {...})
    """
    global _dapr_client
    if _dapr_client is None:
        _dapr_client = DaprClient()
    return _dapr_client
