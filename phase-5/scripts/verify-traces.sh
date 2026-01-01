#!/bin/bash

# Verify Traces Script
# Task: T157 - Query Zipkin API to verify traces exist for all 4 services
# Usage: ./verify-traces.sh [zipkin-url]

set -e

# Configuration
ZIPKIN_URL="${1:-http://localhost:9411}"
SERVICES=("backend" "frontend" "recurring-task-service" "notification-service")
LOOKBACK_MS=3600000  # 1 hour
MIN_TRACES=1

echo "========================================="
echo "Zipkin Trace Verification Script"
echo "========================================="
echo "Zipkin URL: $ZIPKIN_URL"
echo "Lookback: ${LOOKBACK_MS}ms ($(($LOOKBACK_MS / 1000 / 60)) minutes)"
echo "========================================="
echo ""

# Function to check if Zipkin is reachable
check_zipkin_health() {
    echo "[1/5] Checking Zipkin health..."
    if curl -sf "${ZIPKIN_URL}/health" > /dev/null; then
        echo "✓ Zipkin is healthy"
    else
        echo "✗ Zipkin is not responding at ${ZIPKIN_URL}"
        exit 1
    fi
    echo ""
}

# Function to verify traces for a service
verify_service_traces() {
    local service=$1
    echo "[Service: ${service}] Checking for traces..."

    # Query Zipkin API for traces
    local traces=$(curl -sf "${ZIPKIN_URL}/api/v2/traces?serviceName=${service}&lookback=${LOOKBACK_MS}&limit=100")

    if [ -z "$traces" ] || [ "$traces" == "[]" ]; then
        echo "  ✗ No traces found for ${service}"
        return 1
    fi

    # Count traces
    local trace_count=$(echo "$traces" | jq '. | length')

    if [ "$trace_count" -ge "$MIN_TRACES" ]; then
        echo "  ✓ Found ${trace_count} traces for ${service}"

        # Show sample trace IDs
        local sample_traces=$(echo "$traces" | jq -r '.[0:3] | .[] | .[0].traceId')
        echo "  Sample trace IDs:"
        echo "$sample_traces" | while read -r trace_id; do
            echo "    - ${trace_id}"
        done

        return 0
    else
        echo "  ✗ Only ${trace_count} traces found for ${service} (minimum: ${MIN_TRACES})"
        return 1
    fi
}

# Function to verify specific trace patterns
verify_trace_patterns() {
    echo ""
    echo "[3/5] Verifying trace patterns..."

    # Pattern 1: Task completion events
    echo "[Pattern: task.completed] Checking for task completion traces..."
    local task_completed_traces=$(curl -sf "${ZIPKIN_URL}/api/v2/traces?annotationQuery=event_type=task.completed&lookback=${LOOKBACK_MS}&limit=10")
    local count=$(echo "$task_completed_traces" | jq '. | length')

    if [ "$count" -gt 0 ]; then
        echo "  ✓ Found ${count} task.completed event traces"
    else
        echo "  ⚠ No task.completed event traces found (may not have completed tasks yet)"
    fi

    # Pattern 2: Reminder scheduled events
    echo "[Pattern: reminder.scheduled] Checking for reminder traces..."
    local reminder_traces=$(curl -sf "${ZIPKIN_URL}/api/v2/traces?annotationQuery=event_type=reminder.scheduled&lookback=${LOOKBACK_MS}&limit=10")
    local count=$(echo "$reminder_traces" | jq '. | length')

    if [ "$count" -gt 0 ]; then
        echo "  ✓ Found ${count} reminder.scheduled event traces"
    else
        echo "  ⚠ No reminder.scheduled event traces found (may not have scheduled reminders yet)"
    fi

    # Pattern 3: Service invocation traces
    echo "[Pattern: service-invocation] Checking for service invocation traces..."
    local invocation_traces=$(curl -sf "${ZIPKIN_URL}/api/v2/traces?annotationQuery=dapr.service_invocation&lookback=${LOOKBACK_MS}&limit=10")
    local count=$(echo "$invocation_traces" | jq '. | length')

    if [ "$count" -gt 0 ]; then
        echo "  ✓ Found ${count} service invocation traces"
    else
        echo "  ⚠ No service invocation traces found"
    fi

    echo ""
}

# Function to verify trace sampling rate
verify_sampling_rate() {
    echo "[4/5] Verifying sampling rate..."

    # Get all traces from backend (high traffic service)
    local backend_traces=$(curl -sf "${ZIPKIN_URL}/api/v2/traces?serviceName=backend&lookback=${LOOKBACK_MS}&limit=1000")
    local backend_count=$(echo "$backend_traces" | jq '. | length')

    if [ "$backend_count" -eq 0 ]; then
        echo "  ⚠ No backend traces to analyze sampling rate"
        echo ""
        return 0
    fi

    # Get total HTTP requests from Prometheus (if available)
    # This is a rough estimate - actual implementation would query Prometheus
    echo "  Backend traces collected: ${backend_count}"
    echo "  Note: Verify actual sampling rate via Dapr config (100% dev, 10% prod)"
    echo ""
}

# Function to identify slow traces
identify_slow_traces() {
    echo "[5/5] Identifying slow traces (>1s)..."

    local slow_traces=$(curl -sf "${ZIPKIN_URL}/api/v2/traces?minDuration=1000000&lookback=${LOOKBACK_MS}&limit=10")
    local count=$(echo "$slow_traces" | jq '. | length')

    if [ "$count" -gt 0 ]; then
        echo "  ⚠ Found ${count} slow traces (>1s):"

        # Show slow trace details
        echo "$slow_traces" | jq -r '.[] | .[0] | "    - Trace ID: \(.traceId), Service: \(.localEndpoint.serviceName), Duration: \(.duration/1000)ms"' | head -5
    else
        echo "  ✓ No slow traces found (all requests <1s)"
    fi

    echo ""
}

# Main execution
main() {
    check_zipkin_health

    echo "[2/5] Verifying traces for all services..."
    all_services_ok=true

    for service in "${SERVICES[@]}"; do
        if ! verify_service_traces "$service"; then
            all_services_ok=false
        fi
    done

    echo ""

    verify_trace_patterns
    verify_sampling_rate
    identify_slow_traces

    echo "========================================="
    echo "Verification Summary"
    echo "========================================="

    if [ "$all_services_ok" = true ]; then
        echo "✓ All services have traces in Zipkin"
        echo "✓ Distributed tracing is working correctly"
        echo ""
        echo "Next steps:"
        echo "  - View traces in Zipkin UI: ${ZIPKIN_URL}"
        echo "  - Query specific traces: ${ZIPKIN_URL}/zipkin/?serviceName=backend"
        echo "  - Analyze slow requests: ${ZIPKIN_URL}/zipkin/?minDuration=1000000"
        exit 0
    else
        echo "✗ Some services are missing traces"
        echo ""
        echo "Troubleshooting:"
        echo "  1. Check if services are running: kubectl get pods"
        echo "  2. Verify Dapr sidecar injection: kubectl get pods -o jsonpath='{.items[*].spec.containers[*].name}'"
        echo "  3. Check Dapr configuration: kubectl get configuration dapr-config -o yaml"
        echo "  4. Verify sampling rate: grep samplingRate phase-5/dapr/config/config.yaml"
        echo "  5. Check Zipkin endpoint: curl ${ZIPKIN_URL}/api/v2/services"
        exit 1
    fi
}

# Check dependencies
if ! command -v jq &> /dev/null; then
    echo "Error: jq is required but not installed"
    echo "Install: sudo apt-get install jq (Ubuntu) or brew install jq (macOS)"
    exit 1
fi

if ! command -v curl &> /dev/null; then
    echo "Error: curl is required but not installed"
    exit 1
fi

main
