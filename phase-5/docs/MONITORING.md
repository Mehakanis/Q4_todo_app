# Monitoring Guide - Phase V Todo Application

This document provides comprehensive guidance for monitoring the Phase V Todo application in production using Grafana dashboards, Zipkin distributed tracing, and Prometheus alerts.

## Table of Contents

1. [Grafana Dashboard Overview](#grafana-dashboard-overview)
2. [Zipkin Query Examples](#zipkin-query-examples)
3. [Alert Response Procedures](#alert-response-procedures)
4. [Metrics Reference](#metrics-reference)
5. [Troubleshooting Common Issues](#troubleshooting-common-issues)

---

## Grafana Dashboard Overview

Grafana provides real-time visualization of all Phase V metrics across microservices, Kafka, and Dapr components.

### Access URLs

**Minikube**:
```bash
# Get Minikube IP
minikube ip

# Access Grafana
http://$(minikube ip):30000

# Default credentials
Username: admin
Password: admin
```

**OKE Cloud**:
```bash
# Get LoadBalancer IP
kubectl get svc grafana -n monitoring

# Access Grafana
http://<EXTERNAL-IP>:3000
```

### Dashboard Descriptions

#### 1. Kafka Dashboard (`kafka-dashboard.json`)

**Purpose**: Monitor Kafka topic health, consumer lag, and message throughput

**Key Panels**:

1. **Message Throughput**
   - Metric: `kafka_topic_messages_total`
   - Shows: Messages published per second across all topics
   - Alert: Throughput drops below 100 msg/sec during business hours

2. **Consumer Lag**
   - Metric: `kafka_consumer_lag_seconds`
   - Shows: Time delay between message publish and consumption
   - Alert: Lag exceeds 60 seconds
   - Target: < 1 second under normal load

3. **Partition Distribution**
   - Metric: `kafka_topic_partition_count`
   - Shows: Number of partitions per topic
   - Expected: 12 partitions for `task-events`, `reminders`, `task-updates`

4. **Broker Health**
   - Metric: `kafka_broker_up`
   - Shows: Kafka broker availability (1 = up, 0 = down)
   - Alert: Broker down for > 30 seconds

**Query Examples**:

```promql
# Consumer lag by topic
kafka_consumer_lag_seconds{topic="task-events"}

# Message rate by topic (5min rate)
rate(kafka_topic_messages_total{topic="reminders"}[5m])

# Partition replication factor
kafka_topic_replication_factor{topic="task-updates"}
```

#### 2. Dapr Dashboard (`dapr-dashboard.json`)

**Purpose**: Monitor Dapr component health, service invocation, and pub/sub metrics

**Key Panels**:

1. **Component Health**
   - Metric: `dapr_component_loaded`
   - Shows: Status of all 5 Dapr components (1 = loaded, 0 = failed)
   - Expected: All 5 components loaded (pubsub, statestore, secrets, jobs, service-invocation)

2. **Pub/Sub Success Rate**
   - Metric: `dapr_pubsub_publish_success_total / dapr_pubsub_publish_total`
   - Shows: Percentage of successful event publications
   - Target: > 99.9%
   - Alert: Success rate < 99%

3. **State Store Latency**
   - Metric: `dapr_state_operation_duration_seconds`
   - Shows: P50, P95, P99 latency for state operations
   - Target: P95 < 100ms, P99 < 500ms

4. **Service Invocation Latency**
   - Metric: `dapr_service_invocation_duration_seconds`
   - Shows: Latency of service-to-service calls via Dapr
   - Target: P95 < 200ms

**Query Examples**:

```promql
# Pub/Sub success rate (5min window)
sum(rate(dapr_pubsub_publish_success_total[5m])) / sum(rate(dapr_pubsub_publish_total[5m])) * 100

# State store P95 latency
histogram_quantile(0.95, dapr_state_operation_duration_seconds_bucket{operation="get"})

# Service invocation errors
rate(dapr_service_invocation_errors_total[5m])
```

#### 3. Recurring Tasks Dashboard (`recurring-tasks-dashboard.json`)

**Purpose**: Monitor recurring task creation, RRULE calculation, and next occurrence scheduling

**Key Panels**:

1. **Recurring Task Creation Rate**
   - Metric: `recurring_task_created_total`
   - Shows: Number of next occurrences created per minute
   - Trend: Should correlate with task completion events

2. **Next Occurrence Calculation Duration**
   - Metric: `rrule_calculation_duration_seconds`
   - Shows: Time taken to calculate next occurrence from RRULE pattern
   - Target: P95 < 50ms, P99 < 100ms

3. **Recurring Task Completion Rate**
   - Metric: `recurring_task_completed_total`
   - Shows: Tasks completed that triggered next occurrence creation
   - Compare with creation rate to verify 1:1 ratio

4. **Recurring End Date Reached**
   - Metric: `recurring_task_end_date_reached_total`
   - Shows: Count of recurring tasks that reached their end date and stopped
   - Use: Identify completed recurring series

**Query Examples**:

```promql
# Recurring task creation rate (1min rate)
rate(recurring_task_created_total[1m])

# RRULE calculation P99 latency
histogram_quantile(0.99, rrule_calculation_duration_seconds_bucket)

# End date reached count (last 24h)
increase(recurring_task_end_date_reached_total[24h])
```

#### 4. Reminders Dashboard (`reminders-dashboard.json`)

**Purpose**: Monitor reminder scheduling, delivery, and failure rates

**Key Panels**:

1. **Reminders Sent Total**
   - Metric: `reminders_sent_total`
   - Shows: Total reminders delivered successfully
   - Breakdown: By notification type (email, push)

2. **Reminder Delivery Latency**
   - Metric: `reminder_delivery_latency_seconds`
   - Shows: Time from scheduled reminder time to actual delivery
   - Target: P95 < 5 seconds, P99 < 30 seconds

3. **Failed Reminders Count**
   - Metric: `reminders_failed_total`
   - Shows: Reminders that failed after max retries
   - Alert: > 10 failures per hour
   - Requires: Manual investigation via DLQ

4. **Retry Attempts Distribution**
   - Metric: `reminder_retry_attempts`
   - Shows: Histogram of retry attempts before success
   - Expected: Most succeed on first attempt, few reach max retries

**Query Examples**:

```promql
# Reminder success rate (5min window)
sum(rate(reminders_sent_total[5m])) / (sum(rate(reminders_sent_total[5m])) + sum(rate(reminders_failed_total[5m]))) * 100

# Delivery latency P95
histogram_quantile(0.95, reminder_delivery_latency_seconds_bucket)

# Failed reminders (last 1h)
increase(reminders_failed_total[1h])
```

---

## Zipkin Query Examples

Zipkin provides distributed tracing for request flows across microservices.

### Access URLs

**Minikube**:
```bash
http://$(minikube ip):30001
```

**OKE Cloud**:
```bash
kubectl get svc zipkin -n monitoring
http://<EXTERNAL-IP>:9411
```

### Trace Examples

#### 1. Task Completion Event Flow

**Scenario**: User completes recurring task → Kafka event → Next occurrence created

**Query**:
```
Service: backend
Span: POST /api/{user_id}/tasks/{task_id}/complete
```

**Expected Trace**:
1. **Backend** - `toggle_complete` (50-200ms)
2. **Backend** - `publish_event` to Kafka (10-50ms)
3. **Kafka** - Event delivery (5-20ms)
4. **Recurring Task Service** - `consume_event` (20-100ms)
5. **Recurring Task Service** - `calculate_next_occurrence` (10-50ms)
6. **Recurring Task Service** - `invoke_backend` (50-200ms)
7. **Backend** - `create_task` (50-150ms)

**Total Duration**: ~195-770ms (P95 should be < 500ms)

**How to Query**:
1. Go to Zipkin UI
2. Select "backend" service
3. Filter by annotation: `http.method=PATCH`
4. Filter by tag: `http.path=/api/{user_id}/tasks/{task_id}/complete`
5. Set lookback: Last 15 minutes
6. Click "Run Query"

#### 2. Reminder Scheduled Event Flow

**Scenario**: User creates task with reminder → Dapr Jobs API schedules reminder → Email sent

**Query**:
```
Service: backend
Span: POST /api/{user_id}/tasks
Tag: reminder_at != null
```

**Expected Trace**:
1. **Backend** - `create_task` (50-150ms)
2. **Backend** - `publish_reminder_event` (10-50ms)
3. **Kafka** - Event delivery (5-20ms)
4. **Notification Service** - `consume_event` (20-100ms)
5. **Notification Service** - `schedule_dapr_job` (30-100ms)
6. **Dapr Jobs API** - Job scheduled (20-80ms)

**Total Duration**: ~135-500ms

**How to Query**:
1. Select "backend" service
2. Filter by tag: `reminder.scheduled=true`
3. Set min duration: 100ms (to filter quick operations)
4. Click "Run Query"

#### 3. Service-to-Service Call via Dapr

**Scenario**: Recurring Task Service invokes Backend to create next occurrence

**Query**:
```
Service: recurring-task-service
Span: dapr.invoke
```

**Expected Trace**:
1. **Recurring Task Service** - `invoke_service` (50-200ms)
2. **Dapr Sidecar** - `service_invocation` (10-50ms)
3. **Dapr mTLS** - Certificate validation (5-20ms)
4. **Backend Dapr Sidecar** - Receive invocation (10-30ms)
5. **Backend** - `create_task` (50-150ms)

**Total Duration**: ~125-450ms

**How to Query**:
1. Select "recurring-task-service"
2. Filter by span name: `dapr.invoke`
3. Filter by tag: `dapr.app_id=backend`
4. Click "Run Query"

### Analyzing Slow Traces

**Steps to identify bottlenecks**:

1. **Sort by duration** (longest first)
2. **Click on slow trace** to open detailed view
3. **Identify longest span** in the waterfall chart
4. **Check annotations** for error messages
5. **Compare with P95** baseline latency

**Common bottlenecks**:
- **Database queries**: Optimize with indexes, connection pooling
- **Kafka consumer lag**: Scale consumer instances horizontally
- **RRULE calculation**: Add caching for frequently used patterns
- **SMTP delivery**: Check network latency to email server

---

## Alert Response Procedures

Prometheus Alertmanager routes alerts to different channels based on severity.

### Alert Routing Configuration

**Critical Alerts** → PagerDuty (on-call engineer)
**Warning Alerts** → Slack (`#todo-app-alerts` channel)
**Info Alerts** → Email (`ops@example.com`)

### Critical Alerts

#### 1. Consumer Lag Exceeds 60 Seconds

**Alert**: `ConsumerLagHigh`

**Symptoms**:
- Kafka consumer lag > 60 seconds
- Events not processed in real-time
- Next occurrences delayed

**Immediate Actions**:
1. Check Kafka consumer health:
   ```bash
   kubectl get pods -l app=recurring-task-service
   kubectl logs -l app=recurring-task-service --tail=100
   ```

2. Check consumer lag metric:
   ```promql
   kafka_consumer_lag_seconds{topic="task-events"} > 60
   ```

3. Scale consumers horizontally:
   ```bash
   kubectl scale deployment recurring-task-service --replicas=6
   ```

4. Monitor lag decrease (target: < 1 second within 5 minutes)

**Root Cause Investigation**:
- Slow database queries (check query logs)
- High event volume (check topic throughput)
- Consumer pod restarts (check pod events)

**Resolution**:
- Scale to 12 consumer instances (max for 12 partitions)
- Optimize slow database queries
- Increase consumer prefetch count

#### 2. Reminder Delivery Failures > 10/hour

**Alert**: `ReminderFailuresHigh`

**Symptoms**:
- Reminders not sent to users
- DLQ has failed events
- SMTP errors in logs

**Immediate Actions**:
1. Check notification service logs:
   ```bash
   kubectl logs -l app=notification-service --tail=200 | grep ERROR
   ```

2. Check SMTP server connectivity:
   ```bash
   kubectl exec -it deployment/notification-service -- curl -v smtp.example.com:587
   ```

3. Check DLQ topic:
   ```bash
   kubectl exec -it kafka-0 -- kafka-console-consumer --bootstrap-server localhost:9092 --topic reminders-dlq --from-beginning
   ```

4. Manually retry failed reminders:
   ```bash
   curl -X POST http://<API_URL>/api/admin/dlq/retry -H "Authorization: Bearer <ADMIN_TOKEN>"
   ```

**Root Cause Investigation**:
- SMTP server down or rate limiting
- Invalid email addresses in tasks
- Network connectivity issues

**Resolution**:
- Update SMTP credentials if expired
- Implement email validation on task creation
- Configure SMTP rate limiting backoff

#### 3. Pod Restart Loop

**Alert**: `PodCrashLooping`

**Symptoms**:
- Service unavailable
- Frequent pod restarts (> 5/minute)
- CrashLoopBackOff state

**Immediate Actions**:
1. Check pod status:
   ```bash
   kubectl get pods -l app=backend
   kubectl describe pod <POD_NAME>
   ```

2. Check pod logs:
   ```bash
   kubectl logs <POD_NAME> --previous  # Last terminated container
   kubectl logs <POD_NAME> --tail=100  # Current container
   ```

3. Check resource limits:
   ```bash
   kubectl top pods -l app=backend
   ```

4. Rollback if recent deployment:
   ```bash
   kubectl rollout undo deployment backend
   ```

**Root Cause Investigation**:
- Out of memory (OOMKilled)
- Database connection failures
- Missing environment variables
- Code errors (check stack traces)

**Resolution**:
- Increase memory limits in Helm values
- Fix database connection string
- Add missing secrets to Kubernetes
- Deploy hotfix for code errors

### Warning Alerts

#### 4. Service Latency P95 > 500ms

**Alert**: `HighLatency`

**Symptoms**:
- Slow API responses
- Increased request timeouts
- Poor user experience

**Actions**:
1. Check Zipkin traces for slow requests
2. Identify bottleneck service/span
3. Check database query performance:
   ```sql
   SELECT * FROM pg_stat_statements ORDER BY mean_exec_time DESC LIMIT 10;
   ```

4. Scale affected service:
   ```bash
   kubectl scale deployment backend --replicas=4
   ```

**Resolution**:
- Add database indexes
- Enable connection pooling
- Cache frequently accessed data
- Optimize slow queries

#### 5. Error Rate > 1%

**Alert**: `HighErrorRate`

**Symptoms**:
- HTTP 500 errors
- Failed API requests
- User-reported issues

**Actions**:
1. Check error logs:
   ```bash
   kubectl logs -l app=backend --tail=500 | grep -E "ERROR|500"
   ```

2. Check error metrics:
   ```promql
   rate(http_requests_total{status=~"5.."}[5m]) / rate(http_requests_total[5m]) * 100
   ```

3. Identify error patterns (common endpoints, error messages)

4. Deploy hotfix if code issue identified

**Resolution**:
- Fix code bugs
- Add error handling
- Improve input validation
- Add circuit breakers

---

## Metrics Reference

### Application Metrics

| Metric | Type | Description |
|--------|------|-------------|
| `http_requests_total` | Counter | Total HTTP requests by status code, method, path |
| `http_request_duration_seconds` | Histogram | Request latency (P50, P95, P99) |
| `recurring_task_created_total` | Counter | Next occurrences created |
| `rrule_calculation_duration_seconds` | Histogram | RRULE calculation time |
| `reminders_sent_total` | Counter | Reminders delivered successfully |
| `reminders_failed_total` | Counter | Reminders failed after max retries |
| `reminder_delivery_latency_seconds` | Histogram | Time from schedule to delivery |

### Dapr Metrics

| Metric | Type | Description |
|--------|------|-------------|
| `dapr_component_loaded` | Gauge | Component load status (1=loaded, 0=failed) |
| `dapr_pubsub_publish_total` | Counter | Events published to Kafka |
| `dapr_pubsub_publish_success_total` | Counter | Events published successfully |
| `dapr_state_operation_duration_seconds` | Histogram | State store operation latency |
| `dapr_service_invocation_duration_seconds` | Histogram | Service invocation latency |

### Kafka Metrics

| Metric | Type | Description |
|--------|------|-------------|
| `kafka_topic_messages_total` | Counter | Messages published to topic |
| `kafka_consumer_lag_seconds` | Gauge | Consumer lag in seconds |
| `kafka_topic_partition_count` | Gauge | Number of partitions per topic |
| `kafka_broker_up` | Gauge | Broker availability (1=up, 0=down) |

---

## Troubleshooting Common Issues

### Issue 1: Grafana Dashboard Not Loading

**Symptoms**:
- 404 error accessing Grafana
- Empty dashboards
- No data displayed

**Solutions**:

1. Check Grafana pod status:
   ```bash
   kubectl get pods -l app=grafana -n monitoring
   ```

2. Check Prometheus data source:
   ```bash
   kubectl exec -it grafana-<POD> -n monitoring -- curl http://prometheus:9090/-/healthy
   ```

3. Re-import dashboards:
   ```bash
   kubectl apply -f phase-5/monitoring/grafana/dashboards/
   ```

### Issue 2: Zipkin Missing Traces

**Symptoms**:
- No traces displayed in Zipkin
- Missing service-to-service spans
- Incomplete trace waterfall

**Solutions**:

1. Check Dapr configuration sampling rate:
   ```bash
   kubectl get configuration dapr-config -o yaml | grep samplingRate
   ```

2. Verify Zipkin endpoint in Dapr config:
   ```yaml
   spec:
     tracing:
       samplingRate: "1.0"
       zipkin:
         endpointAddress: "http://zipkin:9411/api/v2/spans"
   ```

3. Check Zipkin pod logs:
   ```bash
   kubectl logs -l app=zipkin -n monitoring
   ```

### Issue 3: Alerts Not Firing

**Symptoms**:
- No Slack/PagerDuty notifications
- Alerts not visible in Alertmanager
- Prometheus rules not evaluating

**Solutions**:

1. Check Prometheus alert rules:
   ```bash
   kubectl get prometheusrules -n monitoring
   kubectl describe prometheusrule phase5-alerts
   ```

2. Check Alertmanager configuration:
   ```bash
   kubectl get configmap alertmanager-config -n monitoring -o yaml
   ```

3. Test alert routing:
   ```bash
   kubectl exec -it alertmanager-0 -n monitoring -- amtool config routes test
   ```

---

## Appendix: Quick Reference Commands

### Grafana
```bash
# Port-forward Grafana (Minikube)
kubectl port-forward svc/grafana 3000:3000 -n monitoring

# Get admin password
kubectl get secret grafana-admin -n monitoring -o jsonpath="{.data.password}" | base64 -d
```

### Zipkin
```bash
# Port-forward Zipkin (Minikube)
kubectl port-forward svc/zipkin 9411:9411 -n monitoring

# Query traces via API
curl "http://localhost:9411/api/v2/traces?serviceName=backend&limit=10"
```

### Prometheus
```bash
# Port-forward Prometheus (Minikube)
kubectl port-forward svc/prometheus 9090:9090 -n monitoring

# Query metrics via API
curl "http://localhost:9090/api/v1/query?query=up"
```

### Alertmanager
```bash
# Port-forward Alertmanager (Minikube)
kubectl port-forward svc/alertmanager 9093:9093 -n monitoring

# Silence alert
amtool silence add alertname=ConsumerLagHigh --duration=1h
```

---

For additional help, contact the operations team at `ops@example.com` or Slack `#todo-app-support`.
