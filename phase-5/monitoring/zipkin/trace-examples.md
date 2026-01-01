# Zipkin Trace Examples

**Task**: T155 - Example traces with flow diagrams for debugging distributed operations

## Overview

This document provides example distributed traces captured by Zipkin for Phase V event-driven operations. Each trace shows the complete flow of a request through multiple services.

## Trace 1: Task Completion → Next Occurrence Creation

### Flow Diagram

```
User marks task complete
    │
    ▼
┌─────────────┐
│   Backend   │ POST /api/tasks/{id}/complete
│   Service   │ (user_id: user-456, task_id: 123)
└──────┬──────┘
       │
       │ 1. Update task.completed = true in PostgreSQL
       │
       │ 2. Publish task.completed event to Kafka
       ▼
┌─────────────────────┐
│  Dapr Pub/Sub       │ Topic: task-events
│  (Kafka backend)    │ Partition: hash(user_id) % 12
└──────────┬──────────┘
           │
           │ 3. Event consumed by Recurring Task Service
           ▼
┌──────────────────────────┐
│ Recurring Task Service   │ Consumer Group: recurring-task-service
│                          │ Offset: auto-commit
└───────────┬──────────────┘
            │
            │ 4. Calculate next occurrence
            │    (RRULE: FREQ=DAILY;INTERVAL=1)
            │    (completed_at: 2025-12-29T10:00:00Z)
            │    (next: 2025-12-30T10:00:00Z)
            │
            │ 5. Service Invocation: POST backend/api/tasks
            ▼
┌─────────────┐
│   Backend   │ Create next occurrence
│   Service   │ (title: "Daily standup", next_occurrence: 2025-12-30T10:00:00Z)
└──────┬──────┘
       │
       │ 6. Insert new task into PostgreSQL
       │    (parent_task_id: 123, recurring_pattern: DAILY)
       │
       │ 7. Publish task.created event
       ▼
    Done
```

### Expected Spans in Zipkin

When querying Zipkin for `task.completed` trace:

1. **backend.tasks.complete** (root span)
   - Service: backend
   - Duration: ~50ms
   - Tags: `http.method=POST`, `http.status_code=200`, `user_id=user-456`, `task_id=123`

2. **dapr.pubsub.publish** (child of span 1)
   - Service: backend-dapr-sidecar
   - Duration: ~10ms
   - Tags: `pubsub.name=kafka-pubsub`, `topic=task-events`, `partition=5`

3. **kafka.produce** (child of span 2)
   - Service: kafka
   - Duration: ~5ms
   - Tags: `kafka.topic=task-events`, `kafka.partition=5`, `kafka.offset=1234`

4. **dapr.pubsub.consume** (new trace, linked by trace context)
   - Service: recurring-task-service-dapr-sidecar
   - Duration: ~5ms
   - Tags: `pubsub.name=kafka-pubsub`, `topic=task-events`, `consumer_group=recurring-task-service`

5. **recurring-task-service.handle_task_completed** (child of span 4)
   - Service: recurring-task-service
   - Duration: ~100ms
   - Tags: `event_type=task.completed`, `user_id=user-456`, `task_id=123`

6. **rrule.calculate_next_occurrence** (child of span 5)
   - Service: recurring-task-service
   - Duration: ~20ms
   - Tags: `pattern=DAILY`, `current=2025-12-29T10:00:00Z`, `next=2025-12-30T10:00:00Z`

7. **dapr.service_invocation.invoke** (child of span 5)
   - Service: recurring-task-service-dapr-sidecar
   - Duration: ~50ms
   - Tags: `app_id=backend`, `method=api/tasks`, `http.method=POST`

8. **backend.tasks.create** (child of span 7)
   - Service: backend
   - Duration: ~40ms
   - Tags: `http.method=POST`, `http.status_code=201`, `user_id=user-456`, `parent_task_id=123`

### Zipkin Query

```bash
# Query by service name
curl "http://zipkin:9411/api/v2/traces?serviceName=backend&limit=10"

# Query by span name
curl "http://zipkin:9411/api/v2/traces?spanName=backend.tasks.complete&limit=10"

# Query by tag
curl "http://zipkin:9411/api/v2/traces?annotationQuery=user_id=user-456&limit=10"

# Query by time range (last 1 hour)
curl "http://zipkin:9411/api/v2/traces?lookback=3600000&limit=10"
```

## Trace 2: Reminder Scheduled → Email Delivered

### Flow Diagram

```
User creates task with due_date and reminder_offset
    │
    ▼
┌─────────────┐
│   Backend   │ POST /api/tasks
│   Service   │ (due_date: 2025-12-30T10:00:00Z, reminder_offset_hours: 1)
└──────┬──────┘
       │
       │ 1. Insert task into PostgreSQL
       │    (reminder_at: 2025-12-30T09:00:00Z, reminder_sent: false)
       │
       │ 2. Publish reminder.scheduled event to Kafka
       ▼
┌─────────────────────┐
│  Dapr Pub/Sub       │ Topic: reminders
│  (Kafka backend)    │ Partition: hash(user_id) % 12
└──────────┬──────────┘
           │
           │ 3. Event consumed by Notification Service
           ▼
┌──────────────────────────┐
│ Notification Service     │ Consumer Group: notification-service
│                          │
└───────────┬──────────────┘
            │
            │ 4. Schedule job via Dapr Jobs API
            │    (job_name: reminder-task-123)
            │    (due_time: 2025-12-30T09:00:00Z)
            │    (callback: POST /api/jobs/trigger)
            ▼
┌─────────────────┐
│  Dapr Jobs API  │ Store job in scheduler
│                 │
└─────────┬───────┘
          │
          │ (Wait until due_time...)
          │
          │ 5. Job fires at 2025-12-30T09:00:00Z
          ▼
┌──────────────────────────┐
│ Notification Service     │ POST /api/jobs/trigger
│                          │ (job_data: {task_id: 123, user_id: user-456})
└───────────┬──────────────┘
            │
            │ 6. Fetch user email from backend
            │    (Service Invocation: GET backend/api/users/{user_id})
            │
            │ 7. Send email via SMTP
            │    (to: user@example.com, subject: "Reminder: Daily standup")
            │
            │ 8. Update task.reminder_sent = true
            │    (Service Invocation: PUT backend/api/tasks/{task_id}/reminder-sent)
            ▼
         Done
```

### Expected Spans in Zipkin

When querying Zipkin for `reminder.scheduled` trace:

1. **backend.tasks.create** (root span)
   - Service: backend
   - Duration: ~80ms
   - Tags: `http.method=POST`, `http.status_code=201`, `user_id=user-456`, `task_id=123`

2. **dapr.pubsub.publish** (child of span 1)
   - Service: backend-dapr-sidecar
   - Duration: ~10ms
   - Tags: `pubsub.name=kafka-pubsub`, `topic=reminders`, `partition=8`

3. **dapr.pubsub.consume** (new trace, linked by trace context)
   - Service: notification-service-dapr-sidecar
   - Duration: ~5ms
   - Tags: `pubsub.name=kafka-pubsub`, `topic=reminders`

4. **notification-service.handle_reminder_scheduled** (child of span 3)
   - Service: notification-service
   - Duration: ~50ms
   - Tags: `event_type=reminder.scheduled`, `task_id=123`, `reminder_at=2025-12-30T09:00:00Z`

5. **dapr.jobs.schedule** (child of span 4)
   - Service: notification-service-dapr-sidecar
   - Duration: ~30ms
   - Tags: `job_name=reminder-task-123`, `due_time=2025-12-30T09:00:00Z`

6. **notification-service.send_reminder** (new trace when job fires)
   - Service: notification-service
   - Duration: ~500ms
   - Tags: `task_id=123`, `user_id=user-456`, `email=user@example.com`

7. **smtp.send_email** (child of span 6)
   - Service: notification-service
   - Duration: ~400ms
   - Tags: `smtp.host=smtp.gmail.com`, `smtp.port=587`, `recipient=user@example.com`

8. **dapr.service_invocation.invoke** (child of span 6)
   - Service: notification-service-dapr-sidecar
   - Duration: ~50ms
   - Tags: `app_id=backend`, `method=api/tasks/123/reminder-sent`, `http.method=PUT`

### Zipkin Query

```bash
# Query reminder traces by topic
curl "http://zipkin:9411/api/v2/traces?annotationQuery=topic=reminders&limit=10"

# Query by job name
curl "http://zipkin:9411/api/v2/traces?annotationQuery=job_name=reminder-task-123&limit=1"

# Find slow email deliveries (> 1s)
curl "http://zipkin:9411/api/v2/traces?minDuration=1000000&serviceName=notification-service&limit=10"
```

## Debugging with Zipkin

### Common Debugging Scenarios

1. **Slow Next Occurrence Creation**
   - Query: `curl "http://zipkin:9411/api/v2/traces?serviceName=recurring-task-service&minDuration=500000"`
   - Look for spans: `rrule.calculate_next_occurrence` with high duration
   - Check: RRULE complexity, database query latency

2. **Failed Reminder Delivery**
   - Query: `curl "http://zipkin:9411/api/v2/traces?serviceName=notification-service&annotationQuery=error=true"`
   - Look for spans: `smtp.send_email` with error tags
   - Check: SMTP credentials, network connectivity, retry attempts

3. **Kafka Consumer Lag**
   - Query: `curl "http://zipkin:9411/api/v2/traces?annotationQuery=topic=task-events&lookback=3600000"`
   - Count traces: Compare publish rate vs. consume rate
   - Check: Consumer group health, rebalancing frequency

4. **Service Invocation Failures**
   - Query: `curl "http://zipkin:9411/api/v2/traces?annotationQuery=app_id=backend&annotationQuery=http.status_code=500"`
   - Look for spans: `dapr.service_invocation.invoke` with 5xx status codes
   - Check: Service health endpoints, network policies, Dapr mTLS

### Trace Context Propagation

All services MUST propagate trace context via HTTP headers:

- `traceparent`: W3C Trace Context (e.g., `00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01`)
- `tracestate`: Vendor-specific trace data (optional)

Dapr automatically propagates these headers between services when using:
- Pub/Sub (CloudEvents format)
- Service Invocation (HTTP headers)
- Jobs API (callback request headers)

### Sampling Strategy

- **Development (Minikube)**: 100% sampling (`samplingRate: "1"`)
  - Captures all traces for debugging
  - High storage usage, but acceptable for local development

- **Production (OKE/AKS/GKE)**: 10% sampling (`samplingRate: "0.1"`)
  - Balances visibility with performance
  - Captures 1 in 10 requests
  - Sufficient for identifying patterns and slow requests

## References

- [Zipkin API Documentation](https://zipkin.io/zipkin-api/)
- [Dapr Distributed Tracing](https://docs.dapr.io/operations/observability/tracing/)
- [W3C Trace Context](https://www.w3.org/TR/trace-context/)
