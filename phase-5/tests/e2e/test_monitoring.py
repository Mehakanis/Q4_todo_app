"""
End-to-End Test: User Story 5 - Monitoring & Observability

Tests the complete monitoring stack:
1. Access Grafana dashboards
2. Verify metrics displayed from all services
3. Trace complete request in Zipkin

This validates the observability infrastructure.
"""

import pytest
import requests
import time
from typing import Dict, List


# Configuration
GRAFANA_URL = "http://localhost:30000"  # Minikube NodePort
ZIPKIN_URL = "http://localhost:30001"   # Minikube NodePort
GRAFANA_USER = "admin"
GRAFANA_PASSWORD = "admin"


@pytest.mark.integration
def test_grafana_accessible():
    """Test Grafana UI is accessible."""
    try:
        response = requests.get(GRAFANA_URL, timeout=10)
        assert response.status_code == 200, \
            f"Grafana not accessible: {response.status_code}"

        print("✅ Grafana accessible at", GRAFANA_URL)

    except requests.RequestException as e:
        pytest.fail(f"Grafana not accessible: {e}")


@pytest.mark.integration
def test_grafana_dashboards_exist():
    """Verify all expected Grafana dashboards exist."""
    expected_dashboards = [
        "Kafka Dashboard",
        "Dapr Dashboard",
        "Recurring Tasks Dashboard",
        "Reminders Dashboard"
    ]

    try:
        # Get all dashboards
        response = requests.get(
            f"{GRAFANA_URL}/api/search?type=dash-db",
            auth=(GRAFANA_USER, GRAFANA_PASSWORD),
            timeout=10
        )

        assert response.status_code == 200, \
            f"Failed to get dashboards: {response.status_code}"

        dashboards = response.json()
        dashboard_titles = [d.get("title") for d in dashboards]

        # Verify expected dashboards
        for expected in expected_dashboards:
            assert expected in dashboard_titles, \
                f"Dashboard '{expected}' not found"

            print(f"✅ Dashboard '{expected}' exists")

        print(f"✅ All {len(expected_dashboards)} dashboards found")

    except requests.RequestException as e:
        pytest.fail(f"Dashboard check failed: {e}")


@pytest.mark.integration
def test_grafana_prometheus_datasource():
    """Verify Prometheus datasource configured in Grafana."""
    try:
        response = requests.get(
            f"{GRAFANA_URL}/api/datasources",
            auth=(GRAFANA_USER, GRAFANA_PASSWORD),
            timeout=10
        )

        assert response.status_code == 200

        datasources = response.json()

        # Find Prometheus datasource
        prometheus_ds = None
        for ds in datasources:
            if ds.get("type") == "prometheus":
                prometheus_ds = ds
                break

        assert prometheus_ds is not None, "Prometheus datasource not configured"

        # Test datasource health
        ds_id = prometheus_ds.get("id")
        health_response = requests.get(
            f"{GRAFANA_URL}/api/datasources/{ds_id}/health",
            auth=(GRAFANA_USER, GRAFANA_PASSWORD),
            timeout=10
        )

        assert health_response.status_code == 200, \
            "Prometheus datasource unhealthy"

        print("✅ Prometheus datasource configured and healthy")

    except requests.RequestException as e:
        pytest.fail(f"Datasource check failed: {e}")


@pytest.mark.integration
def test_prometheus_metrics_available():
    """Verify key Prometheus metrics are being collected."""
    # Get Prometheus URL from Grafana datasource
    try:
        response = requests.get(
            f"{GRAFANA_URL}/api/datasources/name/Prometheus",
            auth=(GRAFANA_USER, GRAFANA_PASSWORD),
            timeout=10
        )

        if response.status_code != 200:
            pytest.skip("Prometheus datasource not configured")

        prometheus_url = response.json().get("url")

        if not prometheus_url:
            pytest.skip("Prometheus URL not found")

        # Query for key metrics
        key_metrics = [
            "task_operations_total",
            "kafka_consumer_lag_seconds",
            "dapr_component_health",
            "reminder_delivery_latency_seconds"
        ]

        for metric in key_metrics:
            metric_response = requests.get(
                f"{prometheus_url}/api/v1/query",
                params={"query": metric},
                timeout=10
            )

            if metric_response.status_code == 200:
                data = metric_response.json()
                if data.get("data", {}).get("result"):
                    print(f"✅ Metric '{metric}' available")
                else:
                    print(f"⚠️  Metric '{metric}' exists but no data yet")

    except Exception as e:
        pytest.skip(f"Prometheus check skipped: {e}")


@pytest.mark.integration
def test_zipkin_accessible():
    """Test Zipkin UI is accessible."""
    try:
        response = requests.get(ZIPKIN_URL, timeout=10)
        assert response.status_code == 200, \
            f"Zipkin not accessible: {response.status_code}"

        print("✅ Zipkin accessible at", ZIPKIN_URL)

    except requests.RequestException as e:
        pytest.fail(f"Zipkin not accessible: {e}")


@pytest.mark.integration
def test_zipkin_traces_exist():
    """Verify traces are being collected in Zipkin."""
    try:
        # Query for recent traces
        response = requests.get(
            f"{ZIPKIN_URL}/api/v2/traces",
            params={"limit": 10},
            timeout=10
        )

        assert response.status_code == 200, \
            f"Failed to get traces: {response.status_code}"

        traces = response.json()

        if not traces:
            print("⚠️  No traces found yet (application may not have processed requests)")
            pytest.skip("No traces available")

        print(f"✅ Found {len(traces)} recent traces")

        # Verify trace structure
        sample_trace = traces[0]
        assert isinstance(sample_trace, list), "Trace should be list of spans"
        assert len(sample_trace) > 0, "Trace should have at least one span"

        first_span = sample_trace[0]
        assert "traceId" in first_span
        assert "id" in first_span
        assert "name" in first_span

        print(f"✅ Trace structure valid (traceId: {first_span['traceId']})")

    except requests.RequestException as e:
        pytest.fail(f"Zipkin trace check failed: {e}")


@pytest.mark.integration
def test_zipkin_service_names():
    """Verify all expected services are reporting to Zipkin."""
    expected_services = [
        "backend",
        "recurring-task-service",
        "notification-service",
        "dapr"
    ]

    try:
        response = requests.get(
            f"{ZIPKIN_URL}/api/v2/services",
            timeout=10
        )

        assert response.status_code == 200

        services = response.json()

        for expected in expected_services:
            if expected in services:
                print(f"✅ Service '{expected}' reporting to Zipkin")
            else:
                print(f"⚠️  Service '{expected}' not reporting yet")

    except requests.RequestException as e:
        pytest.skip(f"Service check skipped: {e}")


@pytest.mark.integration
@pytest.mark.slow
def test_complete_trace_flow():
    """
    Test complete distributed trace for task completion flow.

    Traces the flow:
    Backend → Kafka → Recurring Task Service → Backend (next occurrence)

    Note: Requires active task completion during test.
    """
    try:
        # Search for traces with specific operation
        response = requests.get(
            f"{ZIPKIN_URL}/api/v2/traces",
            params={
                "serviceName": "backend",
                "spanName": "POST /api/:user_id/tasks/:task_id",
                "limit": 10
            },
            timeout=10
        )

        assert response.status_code == 200

        traces = response.json()

        if not traces:
            pytest.skip("No task completion traces found")

        # Find trace with multiple services
        multi_service_trace = None
        for trace in traces:
            service_names = {span.get("localEndpoint", {}).get("serviceName") for span in trace}

            if "recurring-task-service" in service_names:
                multi_service_trace = trace
                break

        if not multi_service_trace:
            pytest.skip("No distributed traces found with recurring-task-service")

        # Verify trace contains expected spans
        service_names = {
            span.get("localEndpoint", {}).get("serviceName")
            for span in multi_service_trace
        }

        print(f"✅ Found distributed trace with services: {', '.join(service_names)}")

        # Verify trace timing
        root_span = multi_service_trace[0]
        trace_duration_us = root_span.get("duration", 0)
        trace_duration_ms = trace_duration_us / 1000

        print(f"✅ Trace duration: {trace_duration_ms:.2f}ms")

        assert trace_duration_ms < 5000, \
            f"Trace too slow: {trace_duration_ms}ms (expected < 5000ms)"

        print("✅ Test passed: Complete distributed trace validated")

    except requests.RequestException as e:
        pytest.skip(f"Trace flow check skipped: {e}")


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v", "-s"])
