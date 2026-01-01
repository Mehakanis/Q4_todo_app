"""
End-to-End Test: User Story 3 - Minikube Deployment

Tests the complete local deployment:
1. Run deploy-minikube.sh script
2. Verify all pods reach Running state
3. Access frontend via port-forward
4. Verify Dapr components deployed

This validates the one-command deployment experience for developers.
"""

import pytest
import subprocess
import time
from typing import List, Dict


# Configuration
DEPLOYMENT_SCRIPT = "./scripts/deploy-minikube.sh"
MAX_WAIT_MINUTES = 15
EXPECTED_PODS = [
    "backend",
    "frontend",
    "recurring-task-service",
    "notification-service",
    "kafka",
    "postgresql",
    "prometheus",
    "grafana",
    "zipkin"
]
EXPECTED_DAPR_COMPONENTS = [
    "pubsub-kafka",
    "statestore-postgresql",
    "secretstore-kubernetes",
    "jobs-scheduler"
]


def run_command(cmd: str) -> tuple[int, str, str]:
    """
    Run shell command and return exit code, stdout, stderr.

    Args:
        cmd: Command to execute

    Returns:
        Tuple of (exit_code, stdout, stderr)
    """
    result = subprocess.run(
        cmd,
        shell=True,
        capture_output=True,
        text=True,
        timeout=900  # 15 minutes max
    )
    return result.returncode, result.stdout, result.stderr


def get_pod_status() -> List[Dict[str, str]]:
    """Get status of all pods in default namespace."""
    exit_code, stdout, stderr = run_command("kubectl get pods -o json")

    if exit_code != 0:
        print(f"❌ Failed to get pod status: {stderr}")
        return []

    import json
    data = json.loads(stdout)

    pods = []
    for item in data.get("items", []):
        pods.append({
            "name": item["metadata"]["name"],
            "status": item["status"]["phase"],
            "ready": all(
                c["ready"] for c in item["status"].get("containerStatuses", [])
            )
        })

    return pods


def wait_for_pods_running(timeout_minutes: int = 15) -> bool:
    """
    Wait for all expected pods to reach Running state.

    Args:
        timeout_minutes: Max minutes to wait

    Returns:
        True if all pods running, False otherwise
    """
    start_time = time.time()
    timeout_seconds = timeout_minutes * 60

    while time.time() - start_time < timeout_seconds:
        pods = get_pod_status()

        if not pods:
            print("⏳ Waiting for pods to be created...")
            time.sleep(10)
            continue

        # Check if all expected pods are running
        running_pods = [
            p for p in pods
            if p["status"] == "Running" and p["ready"]
        ]

        missing_pods = []
        for expected in EXPECTED_PODS:
            if not any(expected in p["name"] for p in running_pods):
                missing_pods.append(expected)

        if not missing_pods:
            print("✅ All expected pods are running")
            return True

        elapsed = (time.time() - start_time) / 60
        print(f"⏳ Waiting for pods ({elapsed:.1f}/{timeout_minutes} min): {', '.join(missing_pods)}")
        time.sleep(30)

    return False


def get_dapr_components() -> List[str]:
    """Get list of deployed Dapr components."""
    exit_code, stdout, stderr = run_command("kubectl get components -o json")

    if exit_code != 0:
        print(f"❌ Failed to get Dapr components: {stderr}")
        return []

    import json
    data = json.loads(stdout)

    return [
        item["metadata"]["name"]
        for item in data.get("items", [])
    ]


def test_frontend_accessible() -> bool:
    """
    Test frontend is accessible via port-forward.

    Returns:
        True if frontend returns 200, False otherwise
    """
    import requests

    # Start port-forward in background
    port_forward_proc = subprocess.Popen(
        ["kubectl", "port-forward", "svc/frontend", "3000:3000"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )

    try:
        # Wait for port-forward to establish
        time.sleep(5)

        # Test frontend access
        response = requests.get("http://localhost:3000", timeout=10)

        if response.status_code == 200:
            print("✅ Frontend accessible at http://localhost:3000")
            return True
        else:
            print(f"❌ Frontend returned status {response.status_code}")
            return False

    except Exception as e:
        print(f"❌ Frontend not accessible: {e}")
        return False

    finally:
        # Stop port-forward
        port_forward_proc.terminate()
        port_forward_proc.wait()


@pytest.mark.integration
@pytest.mark.slow
def test_minikube_deployment():
    """
    Test User Story 3: Minikube Deployment

    Steps:
    1. Run deploy-minikube.sh script
    2. Verify all pods reach Running state within 15 minutes
    3. Verify Dapr components deployed
    4. Access frontend via port-forward

    Note: This test takes 10-15 minutes to complete.
    """
    print("🚀 Starting Minikube deployment test...")

    # Step 1: Run deployment script
    print(f"📜 Running deployment script: {DEPLOYMENT_SCRIPT}")

    exit_code, stdout, stderr = run_command(DEPLOYMENT_SCRIPT)

    if exit_code != 0:
        print(f"❌ Deployment script failed with exit code {exit_code}")
        print(f"STDOUT:\n{stdout}")
        print(f"STDERR:\n{stderr}")
        pytest.fail("Deployment script failed")

    print("✅ Deployment script completed successfully")

    # Step 2: Wait for pods to be Running
    print(f"⏳ Waiting up to {MAX_WAIT_MINUTES} minutes for all pods to be Running...")

    all_running = wait_for_pods_running(timeout_minutes=MAX_WAIT_MINUTES)

    assert all_running, f"Not all pods reached Running state within {MAX_WAIT_MINUTES} minutes"

    print("✅ All pods are Running")

    # Step 3: Verify Dapr components
    print("🔍 Verifying Dapr components deployed...")

    components = get_dapr_components()

    missing_components = [
        c for c in EXPECTED_DAPR_COMPONENTS
        if c not in components
    ]

    assert not missing_components, \
        f"Missing Dapr components: {', '.join(missing_components)}"

    print(f"✅ All Dapr components deployed: {', '.join(components)}")

    # Step 4: Test frontend access
    print("🌐 Testing frontend accessibility...")

    frontend_accessible = test_frontend_accessible()

    assert frontend_accessible, "Frontend not accessible via port-forward"

    print("✅ Frontend accessible")

    print("✅ Test passed: Minikube deployment complete and functional")


@pytest.mark.integration
def test_dapr_health():
    """Verify Dapr runtime is healthy."""
    exit_code, stdout, stderr = run_command("dapr status -k")

    assert exit_code == 0, f"Dapr status check failed: {stderr}"

    # Check for required Dapr services
    required_services = ["dapr-operator", "dapr-sidecar-injector", "dapr-sentry"]

    for service in required_services:
        assert service in stdout, f"Dapr service {service} not found"

    print("✅ Dapr runtime healthy")


@pytest.mark.integration
def test_kafka_topics_created():
    """Verify Kafka topics are created."""
    expected_topics = ["task-events", "reminders", "task-updates"]

    # Get Kafka pod name
    exit_code, stdout, stderr = run_command(
        "kubectl get pods -l app.kubernetes.io/name=kafka -o jsonpath='{.items[0].metadata.name}'"
    )

    kafka_pod = stdout.strip()

    if not kafka_pod:
        pytest.skip("Kafka pod not found")

    # List topics
    exit_code, stdout, stderr = run_command(
        f"kubectl exec {kafka_pod} -- kafka-topics.sh "
        f"--bootstrap-server localhost:9092 --list"
    )

    for topic in expected_topics:
        assert topic in stdout, f"Kafka topic {topic} not created"

    print(f"✅ All Kafka topics created: {', '.join(expected_topics)}")


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v", "-s"])
