#!/bin/bash

# Test Alerts Script
# Task: T171 - Trigger test alerts via Alertmanager API and verify delivery to all channels
# Usage: ./test-alerts.sh [alertmanager-url]

set -e

# Configuration
ALERTMANAGER_URL="${1:-http://localhost:9093}"
PROMETHEUS_URL="${2:-http://localhost:9090}"

echo "========================================="
echo "Alert Testing Script"
echo "========================================="
echo "Alertmanager URL: $ALERTMANAGER_URL"
echo "Prometheus URL: $PROMETHEUS_URL"
echo "========================================="
echo ""

# Function to check Alertmanager health
check_alertmanager_health() {
    echo "[1/6] Checking Alertmanager health..."
    if curl -sf "${ALERTMANAGER_URL}/-/healthy" > /dev/null; then
        echo "✓ Alertmanager is healthy"
    else
        echo "✗ Alertmanager is not responding at ${ALERTMANAGER_URL}"
        exit 1
    fi
    echo ""
}

# Function to send test alert via Alertmanager API
send_test_alert() {
    local alertname=$1
    local severity=$2
    local service=$3
    local summary=$4
    local description=$5

    echo "Sending test alert: ${alertname} (${severity})..."

    local alert_json=$(cat <<EOF
[
  {
    "labels": {
      "alertname": "${alertname}",
      "severity": "${severity}",
      "service": "${service}",
      "cluster": "test-cluster",
      "environment": "test"
    },
    "annotations": {
      "summary": "${summary}",
      "description": "${description}"
    },
    "startsAt": "$(date -u +%Y-%m-%dT%H:%M:%S.000Z)",
    "endsAt": "$(date -u -d '+5 minutes' +%Y-%m-%dT%H:%M:%S.000Z)"
  }
]
EOF
)

    local response=$(curl -s -X POST "${ALERTMANAGER_URL}/api/v2/alerts" \
        -H "Content-Type: application/json" \
        -d "$alert_json")

    if [ -z "$response" ]; then
        echo "  ✓ Alert sent successfully"
        return 0
    else
        echo "  ✗ Failed to send alert: $response"
        return 1
    fi
}

# Function to test critical alert → PagerDuty
test_critical_alert() {
    echo "[2/6] Testing CRITICAL alert → PagerDuty..."

    send_test_alert \
        "TestCriticalAlert" \
        "critical" \
        "test-service" \
        "Test critical alert for PagerDuty integration" \
        "This is a test alert to verify PagerDuty integration is working correctly. Expected: PagerDuty incident created."

    echo ""
    echo "Expected behavior:"
    echo "  - PagerDuty incident should be created"
    echo "  - On-call engineer should receive notification"
    echo "  - Incident should appear in PagerDuty dashboard"
    echo ""
    echo "Verification steps:"
    echo "  1. Check PagerDuty incidents: https://[YOUR-DOMAIN].pagerduty.com/incidents"
    echo "  2. Verify incident details match alert summary"
    echo "  3. Acknowledge incident in PagerDuty to stop escalation"
    echo ""
    read -p "Press Enter to continue after verifying PagerDuty..."
    echo ""
}

# Function to test warning alert → Slack
test_warning_alert() {
    echo "[3/6] Testing WARNING alert → Slack..."

    send_test_alert \
        "TestWarningAlert" \
        "warning" \
        "test-service" \
        "Test warning alert for Slack integration" \
        "This is a test alert to verify Slack integration is working correctly. Expected: Message in #todo-alerts-warnings channel."

    echo ""
    echo "Expected behavior:"
    echo "  - Slack message should appear in #todo-alerts-warnings channel"
    echo "  - Message should have warning color (yellow/orange)"
    echo "  - Summary and description should be included"
    echo ""
    echo "Verification steps:"
    echo "  1. Check Slack channel: #todo-alerts-warnings"
    echo "  2. Verify message contains alert summary"
    echo "  3. Verify message color is warning"
    echo ""
    read -p "Press Enter to continue after verifying Slack..."
    echo ""
}

# Function to test info alert → Email
test_info_alert() {
    echo "[4/6] Testing INFO alert → Email..."

    send_test_alert \
        "TestInfoAlert" \
        "info" \
        "test-service" \
        "Test info alert for Email integration" \
        "This is a test alert to verify Email integration is working correctly. Expected: Email to ops-team@example.com."

    echo ""
    echo "Expected behavior:"
    echo "  - Email should be sent to ops-team@example.com"
    echo "  - Subject should be: [TODO-INFO] TestInfoAlert"
    echo "  - Email should contain alert summary and description"
    echo ""
    echo "Verification steps:"
    echo "  1. Check email inbox for ops-team@example.com"
    echo "  2. Verify email subject and content"
    echo "  3. Check spam folder if not in inbox"
    echo ""
    read -p "Press Enter to continue after verifying Email..."
    echo ""
}

# Function to test SLO breach alert → Slack + PagerDuty
test_slo_breach_alert() {
    echo "[5/6] Testing SLO BREACH alert → Slack + PagerDuty..."

    # Send alert with slo label
    local alert_json=$(cat <<EOF
[
  {
    "labels": {
      "alertname": "TestSLOBreachAlert",
      "severity": "critical",
      "service": "test-service",
      "slo": "availability",
      "cluster": "test-cluster"
    },
    "annotations": {
      "summary": "Test SLO breach alert",
      "description": "This is a test SLO breach alert. Expected: Slack message in #todo-slo-alerts AND PagerDuty incident."
    },
    "startsAt": "$(date -u +%Y-%m-%dT%H:%M:%S.000Z)",
    "endsAt": "$(date -u -d '+5 minutes' +%Y-%m-%dT%H:%M:%S.000Z)"
  }
]
EOF
)

    curl -s -X POST "${ALERTMANAGER_URL}/api/v2/alerts" \
        -H "Content-Type: application/json" \
        -d "$alert_json" > /dev/null

    echo "  ✓ SLO breach alert sent"
    echo ""
    echo "Expected behavior:"
    echo "  - Slack message in #todo-slo-alerts channel"
    echo "  - PagerDuty incident created (SLO-specific service key)"
    echo "  - Both channels should receive notification"
    echo ""
    echo "Verification steps:"
    echo "  1. Check Slack channel: #todo-slo-alerts"
    echo "  2. Check PagerDuty for SLO-specific incident"
    echo "  3. Verify both notifications received"
    echo ""
    read -p "Press Enter to continue after verifying Slack + PagerDuty..."
    echo ""
}

# Function to verify Alertmanager routing
verify_routing() {
    echo "[6/6] Verifying Alertmanager routing configuration..."

    # Get Alertmanager status
    local status=$(curl -sf "${ALERTMANAGER_URL}/api/v2/status")

    if [ -n "$status" ]; then
        echo "✓ Alertmanager API is responding"

        # Extract cluster name
        local cluster=$(echo "$status" | jq -r '.cluster.name // "unknown"')
        echo "  Cluster: ${cluster}"

        # Extract configured receivers
        local config=$(curl -sf "${ALERTMANAGER_URL}/api/v2/status" | jq -r '.config')

        if [ -n "$config" ]; then
            echo "  ✓ Configuration loaded"

            # List receivers
            echo ""
            echo "Configured receivers:"
            echo "$config" | jq -r '.receivers[]?.name' | while read -r receiver; do
                echo "  - ${receiver}"
            done
        fi
    else
        echo "✗ Failed to get Alertmanager status"
    fi

    echo ""
}

# Function to send resolve notification
send_resolve_notification() {
    echo "Sending resolve notifications for test alerts..."

    # Resolve all test alerts
    for alertname in "TestCriticalAlert" "TestWarningAlert" "TestInfoAlert" "TestSLOBreachAlert"; do
        local resolve_json=$(cat <<EOF
[
  {
    "labels": {
      "alertname": "${alertname}"
    },
    "endsAt": "$(date -u +%Y-%m-%dT%H:%M:%S.000Z)"
  }
]
EOF
)

        curl -s -X POST "${ALERTMANAGER_URL}/api/v2/alerts" \
            -H "Content-Type: application/json" \
            -d "$resolve_json" > /dev/null
    done

    echo "✓ Resolve notifications sent"
    echo ""
    echo "Expected behavior:"
    echo "  - Slack channels should show resolved status"
    echo "  - PagerDuty incidents should auto-resolve"
    echo "  - Email notifications for resolution (if configured)"
    echo ""
}

# Main execution
main() {
    check_alertmanager_health
    test_critical_alert
    test_warning_alert
    test_info_alert
    test_slo_breach_alert
    verify_routing

    echo "========================================="
    echo "Alert Testing Summary"
    echo "========================================="
    echo ""
    echo "Tests completed. Please verify:"
    echo ""
    echo "✓ PagerDuty:"
    echo "    - Check https://[YOUR-DOMAIN].pagerduty.com/incidents"
    echo "    - Verify incident created for critical alert"
    echo "    - Acknowledge and resolve test incidents"
    echo ""
    echo "✓ Slack:"
    echo "    - Check #todo-alerts-warnings for warning alert"
    echo "    - Check #todo-slo-alerts for SLO breach alert"
    echo "    - Verify message formatting and colors"
    echo ""
    echo "✓ Email:"
    echo "    - Check ops-team@example.com inbox"
    echo "    - Verify email subject: [TODO-INFO] TestInfoAlert"
    echo "    - Check spam folder if not in inbox"
    echo ""
    echo "Next steps:"
    echo "  - Resolve test alerts to verify auto-resolution"
    echo "  - Configure alert silences for maintenance windows"
    echo "  - Review and adjust alert routing as needed"
    echo ""

    # Offer to send resolve notifications
    read -p "Send resolve notifications for test alerts? (y/n): " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        send_resolve_notification
    fi

    echo "Testing complete!"
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
