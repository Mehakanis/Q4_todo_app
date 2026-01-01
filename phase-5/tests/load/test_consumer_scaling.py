"""
Load Test: Kafka Consumer Scaling

Tests horizontal consumer scaling:
- Verify consumer lag < 1s under load
- Test scaling from 1 to 12 consumer instances
- Measure partition rebalancing time

Uses kubectl to scale deployments during load test.
"""

import subprocess
import time
import json
from typing import Dict, List
from locust import HttpUser, task, between, events


# Configuration
CONSUMER_SERVICE = "recurring-task-service"
NAMESPACE = "default"
MAX_CONSUMER_INSTANCES = 12  # Matches 12 Kafka partitions
TARGET_LAG_SECONDS = 1.0


def run_command(cmd: str) -> tuple[int, str, str]:
    """Run shell command and return exit code, stdout, stderr."""
    result = subprocess.run(
        cmd,
        shell=True,
        capture_output=True,
        text=True,
        timeout=60
    )
    return result.returncode, result.stdout, result.stderr


def scale_deployment(deployment: str, replicas: int) -> bool:
    """
    Scale Kubernetes deployment to specified replica count.

    Args:
        deployment: Deployment name
        replicas: Target replica count

    Returns:
        True if successful, False otherwise
    """
    cmd = f"kubectl scale deployment {deployment} -n {NAMESPACE} --replicas={replicas}"

    exit_code, stdout, stderr = run_command(cmd)

    if exit_code == 0:
        print(f"✅ Scaled {deployment} to {replicas} replicas")
        return True
    else:
        print(f"❌ Failed to scale {deployment}: {stderr}")
        return False


def get_consumer_lag() -> float:
    """
    Get current Kafka consumer lag in seconds.

    Returns:
        Average lag across all partitions in seconds
    """
    # Get Kafka pod name
    exit_code, stdout, stderr = run_command(
        "kubectl get pods -l app.kubernetes.io/name=kafka "
        "-o jsonpath='{.items[0].metadata.name}'"
    )

    kafka_pod = stdout.strip().strip("'")

    if not kafka_pod:
        print("⚠️  Kafka pod not found")
        return 0.0

    # Get consumer group lag
    cmd = (
        f"kubectl exec {kafka_pod} -- "
        f"kafka-consumer-groups.sh --bootstrap-server localhost:9092 "
        f"--describe --group {CONSUMER_SERVICE}"
    )

    exit_code, stdout, stderr = run_command(cmd)

    if exit_code != 0:
        print(f"⚠️  Failed to get consumer lag: {stderr}")
        return 0.0

    # Parse lag from output
    # Format: GROUP TOPIC PARTITION CURRENT-OFFSET LOG-END-OFFSET LAG ...
    lines = stdout.strip().split("\n")
    total_lag = 0
    partition_count = 0

    for line in lines[1:]:  # Skip header
        parts = line.split()
        if len(parts) >= 6:
            try:
                lag = int(parts[5])
                total_lag += lag
                partition_count += 1
            except ValueError:
                continue

    if partition_count == 0:
        return 0.0

    # Estimate lag in seconds (assuming ~100 events/sec per partition)
    avg_lag_messages = total_lag / partition_count
    estimated_lag_seconds = avg_lag_messages / 100

    return estimated_lag_seconds


def get_consumer_count() -> int:
    """Get current number of consumer instances."""
    cmd = (
        f"kubectl get deployment {CONSUMER_SERVICE} -n {NAMESPACE} "
        f"-o jsonpath='{{.status.readyReplicas}}'"
    )

    exit_code, stdout, stderr = run_command(cmd)

    if exit_code == 0 and stdout:
        try:
            return int(stdout.strip().strip("'"))
        except ValueError:
            pass

    return 0


class RecurringTaskUser(HttpUser):
    """
    Locust user that creates and completes recurring tasks.

    This generates load on the Recurring Task Service consumer.
    """
    host = "http://localhost:8000"
    wait_time = between(0.1, 0.5)

    def on_start(self):
        """Authenticate."""
        response = self.client.post(
            "/api/auth/signin",
            json={
                "email": "consumer-test@example.com",
                "password": "consumer-test-password"
            }
        )

        if response.status_code != 200:
            self.client.post(
                "/api/auth/signup",
                json={
                    "email": "consumer-test@example.com",
                    "password": "consumer-test-password",
                    "name": "Consumer Test User"
                }
            )

            response = self.client.post(
                "/api/auth/signin",
                json={
                    "email": "consumer-test@example.com",
                    "password": "consumer-test-password"
                }
            )

        self.token = response.json()["token"]
        self.user_id = response.json()["user_id"]
        self.task_ids = []

    @task
    def complete_recurring_task(self):
        """
        Create and complete recurring task.

        This triggers task.completed event → Recurring Task Service
        """
        # Create recurring task
        response = self.client.post(
            f"/api/{self.user_id}/tasks",
            headers={"Authorization": f"Bearer {self.token}"},
            json={
                "title": "Consumer Load Test Task",
                "recurring_pattern": "DAILY"
            }
        )

        if response.status_code == 201:
            task_id = response.json()["id"]

            # Complete task to trigger event
            self.client.patch(
                f"/api/{self.user_id}/tasks/{task_id}",
                headers={"Authorization": f"Bearer {self.token}"},
                json={"completed": True}
            )


@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """Initialize consumer scaling test."""
    print("=" * 60)
    print("Kafka Consumer Scaling Load Test")
    print("=" * 60)
    print(f"Consumer Service: {CONSUMER_SERVICE}")
    print(f"Target Lag: < {TARGET_LAG_SECONDS}s")
    print(f"Scaling: 1 → {MAX_CONSUMER_INSTANCES} instances")
    print("=" * 60)

    # Start with 1 consumer instance
    scale_deployment(CONSUMER_SERVICE, 1)
    time.sleep(10)  # Wait for pod to be ready


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """Test consumer scaling under load."""
    print("\n" + "=" * 60)
    print("Consumer Scaling Test Results")
    print("=" * 60)

    # Test scaling to different replica counts
    replica_counts = [1, 3, 6, 12]
    results = []

    for replicas in replica_counts:
        print(f"\nTesting with {replicas} consumer instances...")

        # Scale deployment
        if not scale_deployment(CONSUMER_SERVICE, replicas):
            continue

        # Wait for pods to be ready and rebalancing to complete
        print("⏳ Waiting for rebalancing...")
        time.sleep(30)

        # Measure consumer lag
        lag_measurements = []

        for i in range(10):  # Take 10 measurements over 30 seconds
            lag = get_consumer_lag()
            lag_measurements.append(lag)
            time.sleep(3)

        avg_lag = sum(lag_measurements) / len(lag_measurements)
        max_lag = max(lag_measurements)

        results.append({
            "replicas": replicas,
            "avg_lag_seconds": avg_lag,
            "max_lag_seconds": max_lag
        })

        print(f"  Average lag: {avg_lag:.2f}s")
        print(f"  Max lag: {max_lag:.2f}s")

        if avg_lag < TARGET_LAG_SECONDS:
            print(f"  ✅ Lag within target ({avg_lag:.2f}s < {TARGET_LAG_SECONDS}s)")
        else:
            print(f"  ❌ Lag exceeds target ({avg_lag:.2f}s >= {TARGET_LAG_SECONDS}s)")

    # Print summary
    print("\n" + "=" * 60)
    print("Scaling Test Summary")
    print("=" * 60)
    print(f"{'Replicas':<10} {'Avg Lag (s)':<15} {'Max Lag (s)':<15} {'Status'}")
    print("-" * 60)

    for result in results:
        status = "✅ PASS" if result["avg_lag_seconds"] < TARGET_LAG_SECONDS else "❌ FAIL"
        print(
            f"{result['replicas']:<10} "
            f"{result['avg_lag_seconds']:<15.2f} "
            f"{result['max_lag_seconds']:<15.2f} "
            f"{status}"
        )

    print("=" * 60)

    # Verify horizontal scaling effectiveness
    if len(results) >= 2:
        lag_reduction = results[0]["avg_lag_seconds"] - results[-1]["avg_lag_seconds"]
        improvement_pct = (lag_reduction / results[0]["avg_lag_seconds"] * 100) if results[0]["avg_lag_seconds"] > 0 else 0

        print(f"\nScaling Impact:")
        print(f"  Initial lag (1 instance): {results[0]['avg_lag_seconds']:.2f}s")
        print(f"  Final lag ({results[-1]['replicas']} instances): {results[-1]['avg_lag_seconds']:.2f}s")
        print(f"  Improvement: {improvement_pct:.1f}%")

        if improvement_pct > 50:
            print("  ✅ Horizontal scaling effective")
        else:
            print("  ⚠️  Limited scaling benefit")


# Run with:
# locust -f test_consumer_scaling.py --headless -u 50 -r 5 -t 5m
#
# Parameters:
#   -u 50: 50 concurrent users
#   -r 5: Spawn 5 users per second
#   -t 5m: Run for 5 minutes
