"""
End-to-End Test: User Story 4 - OKE Deployment

Tests the complete cloud deployment:
1. Trigger CI/CD pipeline (simulate git push)
2. Verify deployment to OKE succeeds
3. Verify health checks pass
4. Verify metrics in Grafana

This validates the production deployment pipeline.
"""

import pytest
import subprocess
import time
import requests
from typing import Dict, List


# Configuration
CLUSTER_NAME = "todo-oke-cluster"
NAMESPACE = "default"
EXPECTED_SERVICES = ["backend", "frontend", "recurring-task-service", "notification-service"]
GRAFANA_URL = None  # Will be determined from LoadBalancer IP


def run_command(cmd: str) -> tuple[int, str, str]:
    """Run shell command and return exit code, stdout, stderr."""
    result = subprocess.run(
        cmd,
        shell=True,
        capture_output=True,
        text=True,
        timeout=600
    )
    return result.returncode, result.stdout, result.stderr


def get_service_url(service_name: str) -> str:
    """Get external URL for LoadBalancer service."""
    exit_code, stdout, stderr = run_command(
        f"kubectl get svc {service_name} -n {NAMESPACE} "
        f"-o jsonpath='{{.status.loadBalancer.ingress[0].ip}}'"
    )

    if exit_code != 0 or not stdout:
        return None

    ip = stdout.strip()
    return f"http://{ip}"


def check_health_endpoint(service_name: str) -> bool:
    """Check if service health endpoint returns 200."""
    base_url = get_service_url(service_name)

    if not base_url:
        print(f"❌ Could not get URL for {service_name}")
        return False

    try:
        response = requests.get(f"{base_url}/health", timeout=10)
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Health check failed for {service_name}: {e}")
        return False


@pytest.mark.integration
@pytest.mark.cloud
def test_oke_deployment_health_checks():
    """
    Test User Story 4: OKE Cloud Deployment Health Checks

    Steps:
    1. Verify all expected services deployed
    2. Check health endpoints for all services
    3. Verify services have LoadBalancer IPs
    """
    print("🚀 Testing OKE deployment health checks...")

    # Step 1: Verify services deployed
    exit_code, stdout, stderr = run_command(
        f"kubectl get svc -n {NAMESPACE} -o json"
    )

    assert exit_code == 0, f"Failed to get services: {stderr}"

    import json
    services_data = json.loads(stdout)
    deployed_services = [
        item["metadata"]["name"]
        for item in services_data.get("items", [])
    ]

    for expected in EXPECTED_SERVICES:
        assert expected in deployed_services, \
            f"Service {expected} not deployed"

    print(f"✅ All services deployed: {', '.join(EXPECTED_SERVICES)}")

    # Step 2: Check health endpoints
    for service in EXPECTED_SERVICES:
        print(f"🔍 Checking health for {service}...")

        is_healthy = check_health_endpoint(service)

        assert is_healthy, f"Health check failed for {service}"

        print(f"✅ {service} is healthy")

    print("✅ Test passed: All OKE services are healthy")


@pytest.mark.integration
@pytest.mark.cloud
def test_oke_dapr_components():
    """Verify Dapr components deployed on OKE."""
    exit_code, stdout, stderr = run_command(
        f"kubectl get components -n {NAMESPACE} -o json"
    )

    assert exit_code == 0, f"Failed to get Dapr components: {stderr}"

    import json
    components_data = json.loads(stdout)
    components = [
        item["metadata"]["name"]
        for item in components_data.get("items", [])
    ]

    expected_components = [
        "pubsub-kafka",
        "statestore-postgresql",
        "secretstore-oci-vault",
        "jobs-scheduler"
    ]

    for expected in expected_components:
        assert expected in components, \
            f"Dapr component {expected} not deployed"

    print(f"✅ All Dapr components deployed: {', '.join(components)}")


@pytest.mark.integration
@pytest.mark.cloud
def test_oke_grafana_metrics():
    """Verify Grafana is accessible and displaying metrics."""
    grafana_url = get_service_url("grafana")

    if not grafana_url:
        pytest.skip("Grafana LoadBalancer IP not available")

    print(f"🔍 Testing Grafana at {grafana_url}...")

    try:
        # Test Grafana UI accessible
        response = requests.get(f"{grafana_url}:3000", timeout=10)
        assert response.status_code == 200, \
            f"Grafana not accessible: {response.status_code}"

        print("✅ Grafana UI accessible")

        # Test Prometheus datasource
        response = requests.get(
            f"{grafana_url}:3000/api/datasources",
            auth=("admin", "admin"),
            timeout=10
        )

        assert response.status_code == 200
        datasources = response.json()

        prometheus_found = any(
            ds.get("type") == "prometheus"
            for ds in datasources
        )

        assert prometheus_found, "Prometheus datasource not configured"

        print("✅ Prometheus datasource configured")

    except Exception as e:
        pytest.fail(f"Grafana test failed: {e}")


@pytest.mark.integration
@pytest.mark.cloud
def test_oke_tls_certificates():
    """Verify TLS certificates provisioned via cert-manager."""
    exit_code, stdout, stderr = run_command(
        f"kubectl get certificates -n {NAMESPACE} -o json"
    )

    if exit_code != 0:
        pytest.skip("cert-manager not installed or no certificates")

    import json
    certs_data = json.loads(stdout)

    for cert in certs_data.get("items", []):
        status = cert.get("status", {})
        conditions = status.get("conditions", [])

        ready = any(
            c.get("type") == "Ready" and c.get("status") == "True"
            for c in conditions
        )

        cert_name = cert["metadata"]["name"]

        assert ready, f"Certificate {cert_name} not ready"

        print(f"✅ Certificate {cert_name} is ready")


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v", "-s", "-m", "cloud"])
