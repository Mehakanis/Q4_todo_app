# Phase 7 Implementation Prompt for Claude Code

## Prompt

```text
@phase5-cloud-deployment-engineer

Implement Phase 7: User Story 5 - Monitoring & Observability (T146-T171) from specs/007-phase5-cloud-deployment/tasks.md.

**Goal**: Enable operations teams to monitor production system health, performance, and reliability

**Independent Test**: Access Grafana dashboards → verify metrics from all services, trace complete request in Zipkin

**Requirements:**
1. Use Context7 MCP server for Prometheus, Grafana, and Zipkin configuration patterns
2. Use skills:
   - kubernetes-helm-deployment (for ServiceMonitor CRDs and health check probes)
   - dapr-integration (for Dapr tracing configuration)
   - terraform-infrastructure (for OCI Logging configuration)
3. Reference files:
   - Constitution: .specify/memory/constitution.md
   - Spec: specs/007-phase5-cloud-deployment/spec.md
   - Plan: specs/007-phase5-cloud-deployment/plan.md

**Tasks to Complete:**

### Prometheus Configuration (T146-T149)
- T146: Update prometheus.yaml with scrape configs for Recurring Task Service and Notification Service metrics endpoints
- T147: Update alerts.yaml with alerts (consumer lag > 60s, reminder delivery failure > 5%, pod restart rate > 3/hour)
- T148: Create servicemonitor-recurring-task.yaml ServiceMonitor CRD
- T149: Create servicemonitor-notification.yaml ServiceMonitor CRD

### Grafana Dashboards (T150-T153)
- T150: Update kafka-dashboard.json with message throughput, partition lag, broker health panels
- T151: Update dapr-dashboard.json with pub/sub success rate, state store latency, service invocation latency panels
- T152: Update recurring-tasks-dashboard.json with next occurrence calculation duration, completion rate, end date reached panels
- T153: Create reminders-dashboard.json with reminders sent total, delivery latency, failed reminders count panels

### Distributed Tracing (T154-T157)
- T154: Update dapr/config/config.yaml with sampling rate (100% dev, 10% production)
- T155: Verify Zipkin traces for task.completed event flow
- T156: Verify Zipkin traces for reminder.scheduled event flow
- T157: Create zipkin-queries.md with example queries for debugging

### Centralized Logging (T158-T162)
- T158: Configure structured JSON logging in config.py (timestamp, level, service, user_id, event_id, message)
- T159: Add logging in recurring_task_service.py (next occurrence creation, RRULE errors)
- T160: Add logging in notification_service.py (reminder sending, SMTP failures, retries)
- T161: Create logging.tf in terraform/oke/ with log group and log stream
- T162: Test log aggregation (search by user_id in OCI Logging console)

### Health Checks (T163-T168)
- T163: Create health.py endpoint for backend (database connectivity, Dapr sidecar status)
- T164: Create health.py endpoint for Recurring Task Service (Kafka consumer status, database connectivity)
- T165: Create health.py endpoint for Notification Service (Kafka consumer status, SMTP connectivity)
- T166: Update backend-deployment.yaml liveness probes to use /health
- T167: Update recurring-task-service-deployment.yaml readiness probes to use /health
- T168: Update notification-service-deployment.yaml readiness probes to use /health

### Alerting (T169-T171)
- T169: Create alertmanager.yaml with email notification receiver for ops team
- T170: Test alert firing (simulate consumer lag > 60s by stopping Recurring Task Service pod)
- T171: Test alert firing (simulate reminder delivery failure with invalid SMTP credentials)

**Checkpoint**: Operations team has full visibility with dashboards, traces, logs, and alerts.
```

## Quick Copy-Paste Version

```text
@phase5-cloud-deployment-engineer

Implement Phase 7: User Story 5 - Monitoring & Observability (T146-T171) from specs/007-phase5-cloud-deployment/tasks.md.

Use Context7 MCP server for Prometheus, Grafana, Zipkin, and logging patterns.
Use skills: kubernetes-helm-deployment, dapr-integration, terraform-infrastructure.

References: constitution.md, spec.md, plan.md.

Tasks:
- Prometheus (T146-T149): Scrape configs, alert rules, ServiceMonitor CRDs
- Grafana (T150-T153): Update existing dashboards, create reminders dashboard
- Tracing (T154-T157): Dapr sampling config, Zipkin trace verification, query examples
- Logging (T158-T162): Structured JSON logging, service logging, OCI Logging config
- Health checks (T163-T168): Health endpoints for all services, Kubernetes probe updates
- Alerting (T169-T171): Alertmanager config, alert testing

Test: Access Grafana dashboards → verify metrics from all services → trace complete request in Zipkin.
```

