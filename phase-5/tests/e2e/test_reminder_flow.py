"""
End-to-End Test: User Story 2 - Reminder Flow

Tests the complete flow:
1. Create task with due date and reminder offset
2. Wait for reminder time
3. Verify email notification received

This validates the Dapr Jobs API and Notification Service integration.
"""

import pytest
import httpx
import asyncio
from datetime import datetime, timedelta, timezone
from email import message_from_bytes
import imaplib
import time


# Configuration
API_BASE_URL = "http://localhost:8000"
TEST_USER_EMAIL = "test-reminders@example.com"
TEST_USER_PASSWORD = "test-password-123"

# Email configuration for verification
IMAP_SERVER = "imap.gmail.com"
IMAP_PORT = 993
EMAIL_USER = "test-reminders@example.com"  # Must match task user email
EMAIL_PASSWORD = "your-app-password"  # Gmail app password


@pytest.fixture
async def auth_token() -> str:
    """Authenticate and return JWT token."""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{API_BASE_URL}/api/auth/signin",
            json={
                "email": TEST_USER_EMAIL,
                "password": TEST_USER_PASSWORD
            }
        )
        assert response.status_code == 200
        return response.json()["token"]


@pytest.fixture
async def user_id(auth_token: str) -> str:
    """Get authenticated user's ID."""
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{API_BASE_URL}/api/me",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        return response.json()["id"]


def check_email_received(subject_contains: str, timeout: int = 300) -> bool:
    """
    Check if email with subject containing text was received.

    Args:
        subject_contains: Text to search for in subject
        timeout: Max seconds to wait for email

    Returns:
        True if email found, False otherwise
    """
    try:
        # Connect to IMAP server
        mail = imaplib.IMAP4_SSL(IMAP_SERVER, IMAP_PORT)
        mail.login(EMAIL_USER, EMAIL_PASSWORD)
        mail.select("INBOX")

        start_time = time.time()

        while time.time() - start_time < timeout:
            # Search for unread emails
            status, messages = mail.search(None, "UNSEEN")

            if status == "OK":
                email_ids = messages[0].split()

                for email_id in email_ids:
                    # Fetch email
                    status, msg_data = mail.fetch(email_id, "(RFC822)")

                    if status == "OK":
                        email_body = msg_data[0][1]
                        email_message = message_from_bytes(email_body)

                        subject = email_message["Subject"]

                        if subject and subject_contains.lower() in subject.lower():
                            print(f"✅ Email found: {subject}")
                            mail.close()
                            mail.logout()
                            return True

            # Wait 5 seconds before checking again
            time.sleep(5)

        mail.close()
        mail.logout()
        return False

    except Exception as e:
        print(f"❌ Email check failed: {e}")
        return False


@pytest.mark.asyncio
@pytest.mark.slow  # Mark as slow test (requires waiting for reminder time)
async def test_reminder_notification_sent(auth_token: str, user_id: str):
    """
    Test User Story 2: Reminder Notification Flow

    Steps:
    1. Create task with due date 5 minutes from now
    2. Set reminder for 2 minutes from now
    3. Wait for reminder time
    4. Verify email notification received

    Note: This test takes 2-3 minutes to complete due to waiting for reminder time.
    """
    async with httpx.AsyncClient() as client:
        headers = {"Authorization": f"Bearer {auth_token}"}

        # Step 1: Create task with reminder
        now = datetime.now(timezone.utc)
        due_date = now + timedelta(minutes=5)
        reminder_offset_minutes = 2  # Remind 2 minutes from now

        create_response = await client.post(
            f"{API_BASE_URL}/api/{user_id}/tasks",
            headers=headers,
            json={
                "title": "E2E Test: Submit Report",
                "description": "Test reminder notification",
                "due_date": due_date.isoformat(),
                "reminder_offset_hours": reminder_offset_minutes / 60  # Convert to hours
            }
        )

        assert create_response.status_code == 201, \
            f"Failed to create task: {create_response.text}"

        task_data = create_response.json()
        task_id = task_data["id"]

        assert task_data["reminder_at"] is not None

        reminder_time = datetime.fromisoformat(
            task_data["reminder_at"].replace("Z", "+00:00")
        )

        print(f"✅ Created task with reminder at {reminder_time}")

        # Step 2: Wait for reminder time
        wait_seconds = (reminder_time - datetime.now(timezone.utc)).total_seconds()
        wait_seconds = max(0, wait_seconds) + 30  # Add 30s buffer for processing

        print(f"⏳ Waiting {wait_seconds:.0f} seconds for reminder time...")
        await asyncio.sleep(wait_seconds)

        # Step 3: Verify email received
        print("📧 Checking for reminder email...")

        email_found = check_email_received(
            subject_contains="Reminder: Submit Report",
            timeout=120  # Wait up to 2 minutes for email delivery
        )

        assert email_found, "Reminder email not received within timeout"

        print("✅ Reminder email received")

        # Step 4: Verify reminder_sent flag updated
        task_response = await client.get(
            f"{API_BASE_URL}/api/{user_id}/tasks/{task_id}",
            headers=headers
        )

        assert task_response.status_code == 200
        updated_task = task_response.json()

        assert updated_task["reminder_sent"] is True, \
            "reminder_sent flag not updated after notification sent"

        print("✅ reminder_sent flag updated in database")

        # Cleanup
        await client.delete(
            f"{API_BASE_URL}/api/{user_id}/tasks/{task_id}",
            headers=headers
        )

        print("✅ Test passed: Reminder notification flow works end-to-end")


@pytest.mark.asyncio
async def test_reminder_cancelled_on_task_completion(
    auth_token: str,
    user_id: str
):
    """
    Test reminder is cancelled when task completed before reminder time.

    Steps:
    1. Create task with reminder 5 minutes from now
    2. Complete task immediately
    3. Wait for reminder time
    4. Verify NO email sent
    """
    async with httpx.AsyncClient() as client:
        headers = {"Authorization": f"Bearer {auth_token}"}

        # Create task with reminder
        due_date = datetime.now(timezone.utc) + timedelta(minutes=10)

        create_response = await client.post(
            f"{API_BASE_URL}/api/{user_id}/tasks",
            headers=headers,
            json={
                "title": "E2E Test: Quick Task",
                "due_date": due_date.isoformat(),
                "reminder_offset_hours": 5 / 60  # 5 minutes before
            }
        )

        task_id = create_response.json()["id"]
        reminder_time = datetime.fromisoformat(
            create_response.json()["reminder_at"].replace("Z", "+00:00")
        )

        # Complete task immediately
        await client.patch(
            f"{API_BASE_URL}/api/{user_id}/tasks/{task_id}",
            headers=headers,
            json={"completed": True}
        )

        print(f"✅ Completed task before reminder time {reminder_time}")

        # Wait past reminder time
        wait_seconds = (reminder_time - datetime.now(timezone.utc)).total_seconds()
        if wait_seconds > 0:
            await asyncio.sleep(wait_seconds + 60)  # Wait 1 min past reminder

        # Verify NO email received
        print("📧 Verifying no email sent for completed task...")

        email_found = check_email_received(
            subject_contains="Quick Task",
            timeout=30  # Only wait 30 seconds
        )

        assert not email_found, \
            "Reminder email sent despite task being completed"

        print("✅ Test passed: Reminder cancelled on task completion")


if __name__ == "__main__":
    # Run tests (excluding slow tests by default)
    pytest.main([__file__, "-v", "-s", "-m", "not slow"])
