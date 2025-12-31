# Architecture Documentation - Phase V Todo Application

This document provides comprehensive architecture documentation for the Phase V Todo application, including system context, microservices architecture, event flows, and infrastructure design.

## Table of Contents

1. [System Context Diagram](#system-context-diagram)
2. [Microservices Architecture](#microservices-architecture)
3. [Event Flows](#event-flows)
4. [Infrastructure Architecture](#infrastructure-architecture)
5. [Database Schema](#database-schema)
6. [Security Architecture](#security-architecture)
7. [Scalability and Resilience](#scalability-and-resilience)

---

## System Context Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          External Systems                                │
│                                                                           │
│  ┌──────────────┐   ┌──────────────┐   ┌──────────────┐                │
│  │  End Users   │   │ Better Auth  │   │ Email (SMTP) │                │
│  │  (Browser)   │   │   Server     │   │   Server     │                │
│  └──────┬───────┘   └──────┬───────┘   └──────┬───────┘                │
│         │                   │                   │                        │
└─────────┼───────────────────┼───────────────────┼────────────────────────┘
          │                   │                   │
          │                   │                   │
┌─────────▼───────────────────▼───────────────────▼────────────────────────┐
│                      Todo Application (Phase V)                           │
│                                                                            │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │                         Frontend Layer                            │   │
│  │  ┌────────────────────────────────────────────────────────┐      │   │
│  │  │  Next.js 16 Application (Port 3000)                     │      │   │
│  │  │  - Server Components (SSR)                              │      │   │
│  │  │  - Client Components (Interactive UI)                   │      │   │
│  │  │  - Better Auth Integration (JWT)                        │      │   │
│  │  └────────────────────────────────────────────────────────┘      │   │
│  └──────────────────────────┬───────────────────────────────────────┘   │
│                              │ HTTPS/REST API                            │
│  ┌──────────────────────────▼───────────────────────────────────────┐   │
│  │                      Backend Layer (FastAPI)                      │   │
│  │  ┌─────────────────────────────────────────────────────────┐     │   │
│  │  │  Backend Service (Port 8000)                             │     │   │
│  │  │  - Task CRUD API                                         │     │   │
│  │  │  - JWT Verification                                      │     │   │
│  │  │  - User Isolation                                        │     │   │
│  │  │  - Event Publishing (Dapr Pub/Sub)                       │     │   │
│  │  └─────────────────────────────────────────────────────────┘     │   │
│  └──────────────────────────┬───────────────────────────────────────┘   │
│                              │ Dapr mTLS                                 │
│  ┌──────────────────────────▼───────────────────────────────────────┐   │
│  │                    Microservices Layer                            │   │
│  │  ┌───────────────────────┐    ┌────────────────────────────┐     │   │
│  │  │ Recurring Task        │    │ Notification Service       │     │   │
│  │  │ Service (Port 8001)   │    │ (Port 8002)                │     │   │
│  │  │ - Consume task.       │    │ - Consume reminder.        │     │   │
│  │  │   completed events    │    │   scheduled events         │     │   │
│  │  │ - Calculate next      │    │ - Schedule Dapr Jobs       │     │   │
│  │  │   occurrence (RRULE)  │    │ - Send email (SMTP)        │     │   │
│  │  │ - Invoke Backend to   │    │ - Retry failed reminders   │     │   │
│  │  │   create next task    │    │ - Update reminder_sent     │     │   │
│  │  └───────────────────────┘    └────────────────────────────┘     │   │
│  └──────────────────────────┬───────────────────────────────────────┘   │
│                              │ Dapr Pub/Sub                              │
│  ┌──────────────────────────▼───────────────────────────────────────┐   │
│  │                      Message Broker Layer                         │   │
│  │  ┌────────────────────────────────────────────────────────┐      │   │
│  │  │  Kafka / Redpanda Cloud Serverless                      │      │   │
│  │  │  Topics:                                                │      │   │
│  │  │  - task-events (12 partitions, user_id partitioning)    │      │   │
│  │  │  - reminders (12 partitions, user_id partitioning)      │      │   │
│  │  │  - task-updates (12 partitions, user_id partitioning)   │      │   │
│  │  │  - DLQ topics (for failed events)                       │      │   │
│  │  └────────────────────────────────────────────────────────┘      │   │
│  └──────────────────────────┬───────────────────────────────────────┘   │
│                              │                                           │
│  ┌──────────────────────────▼───────────────────────────────────────┐   │
│  │                      Data Layer                                   │   │
│  │  ┌────────────────────────┐    ┌────────────────────────────┐    │   │
│  │  │ Neon PostgreSQL        │    │ Dapr State Store           │    │   │
│  │  │ - Tasks table          │    │ (PostgreSQL)               │    │   │
│  │  │ - Users table          │    │ - Conversation history     │    │   │
│  │  │ - Messages table       │    │ - Idempotency tracking     │    │   │
│  │  │ - Conversations table  │    │                            │    │   │
│  │  └────────────────────────┘    └────────────────────────────┘    │   │
│  └────────────────────────────────────────────────────────────────────┘   │
│                                                                            │
│  ┌────────────────────────────────────────────────────────────────────┐   │
│  │                  Cross-Cutting Concerns                             │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐     │   │
│  │  │ Dapr Runtime │  │ Monitoring   │  │ Distributed Tracing  │     │   │
│  │  │ (Sidecar)    │  │ (Prometheus) │  │ (Zipkin)             │     │   │
│  │  │ - Pub/Sub    │  │ - Grafana    │  │ - Request flows      │     │   │
│  │  │ - State      │  │ - Metrics    │  │ - Service-to-service │     │   │
│  │  │ - Secrets    │  │ - Alerts     │  │ - Performance        │     │   │
│  │  │ - Jobs API   │  │              │  │   analysis           │     │   │
│  │  │ - mTLS       │  │              │  │                      │     │   │
│  │  └──────────────┘  └──────────────┘  └──────────────────────┘     │   │
│  └────────────────────────────────────────────────────────────────────┘   │
│                                                                            │
└────────────────────────────────────────────────────────────────────────────┘
```

---

## Microservices Architecture

### Service Inventory

| Service | Port | Responsibilities | Technology |
|---------|------|------------------|------------|
| **Frontend** | 3000 | User interface, Better Auth integration, API client | Next.js 16, TypeScript, Tailwind CSS |
| **Backend** | 8000 | Task CRUD, JWT verification, event publishing | FastAPI, SQLModel, Python 3.13+ |
| **Recurring Task Service** | 8001 | RRULE calculation, next occurrence creation | FastAPI, python-dateutil |
| **Notification Service** | 8002 | Reminder scheduling (Dapr Jobs), email sending | FastAPI, SMTP client |
| **Kafka** | 9092 | Message broker, event streaming | Bitnami Kafka / Redpanda Cloud |
| **PostgreSQL** | 5432 | Persistent storage | Neon Serverless PostgreSQL |
| **Dapr Sidecar** | 3500 | Service mesh, pub/sub, state, secrets, jobs | Dapr 1.12+ |
| **Prometheus** | 9090 | Metrics collection | Prometheus |
| **Grafana** | 3000 | Metrics visualization | Grafana |
| **Zipkin** | 9411 | Distributed tracing | Zipkin |

### Service Communication Patterns

#### 1. **Synchronous Communication** (HTTP/REST via Dapr Service Invocation)

```
Recurring Task Service → (Dapr mTLS) → Backend
  POST /v1.0/invoke/backend/method/api/tasks
  {
    "title": "Daily standup",
    "user_id": "user-456",
    "recurring_pattern": "DAILY"
  }
```

**Use Cases**:
- Recurring Task Service calling Backend to create next occurrence
- Service health checks
- Admin operations

**Characteristics**:
- Synchronous request-response
- mTLS encryption between services
- Built-in retries and circuit breaking
- Automatic service discovery

#### 2. **Asynchronous Communication** (Event-Driven via Dapr Pub/Sub)

```
Backend → (Dapr Pub/Sub) → Kafka → (Dapr Pub/Sub) → Recurring Task Service
  Topic: task-events
  Event: task.completed
  {
    "event_id": "uuid",
    "event_type": "task.completed",
    "user_id": "user-456",
    "task_id": 123,
    "recurring_pattern": "DAILY"
  }
```

**Use Cases**:
- Task completion triggering next occurrence creation
- Reminder scheduling when task created with due_date
- Task updates synchronization

**Characteristics**:
- Fire-and-forget (no blocking)
- Decoupled services
- Horizontal scalability (up to 12 consumer instances per service)
- Exactly-once delivery semantics with idempotency

#### 3. **State Management** (Dapr State Store)

```
Backend → (Dapr State API) → PostgreSQL
  POST /v1.0/state/statestore
  [
    {
      "key": "conversation-{conversation_id}",
      "value": {"messages": [...]}
    }
  ]
```

**Use Cases**:
- Conversation history persistence (Phase III chatbot)
- Idempotency tracking (prevent duplicate event processing)
- Distributed locks (for critical sections)

**Characteristics**:
- Key-value storage
- Transactional state updates
- Automatic expiration (TTL)

#### 4. **Scheduled Jobs** (Dapr Jobs API)

```
Notification Service → (Dapr Jobs API) → Job Scheduler
  POST /v1.0-alpha1/jobs/reminder-task-{task_id}
  {
    "dueTime": "2025-12-30T16:00:00Z",
    "data": {"task_id": 123, "user_id": "user-456"}
  }
```

**Use Cases**:
- Scheduling exact-time reminder notifications
- Delayed task execution
- Periodic cleanup jobs

**Characteristics**:
- Exact-time execution (not cron-based)
- One-time or recurring jobs
- Job cancellation support

### Service Dependencies

```
Frontend
  ↓
Backend ←─────────────────────┐
  ↓                            │
Dapr Sidecar                   │
  ↓                            │
Kafka (task-events topic)      │
  ↓                            │
Recurring Task Service         │
  ↓                            │
Dapr Sidecar ─────────────────┘
  (Service Invocation to Backend)


Backend
  ↓
Dapr Sidecar
  ↓
Kafka (reminders topic)
  ↓
Notification Service
  ↓
Dapr Jobs API
  ↓
(Scheduled callback to Notification Service)
  ↓
SMTP Server (email delivery)
```

---

## Event Flows

### Event Flow 1: Recurring Task Completion → Next Occurrence Creation

**Scenario**: User marks recurring task as complete → System automatically creates next occurrence

```
┌──────────┐     1. PATCH /api/{user_id}/tasks/{task_id}/complete     ┌─────────┐
│          │────────────────────────────────────────────────────────▶ │         │
│  User    │                   {completed: true}                       │ Backend │
│ (Browser)│                                                            │         │
└──────────┘     2. 200 OK {task: {..., completed: true}}             └────┬────┘
                 ◀────────────────────────────────────────────────────────┘
                                                                             │
                                                                             │ 3. Publish event
                                                                             │    task.completed
                                                                             ▼
                                                                      ┌──────────────┐
                                                                      │ Dapr Pub/Sub │
                                                                      │   Sidecar    │
                                                                      └──────┬───────┘
                                                                             │
                                                                             │ 4. Kafka topic
                                                                             │    task-events
                                                                             ▼
                                                                      ┌──────────────┐
                                                                      │    Kafka     │
                                                                      │ (partition   │
                                                                      │  by user_id) │
                                                                      └──────┬───────┘
                                                                             │
                                                                             │ 5. Consume event
                                                                             ▼
                                                                      ┌──────────────────┐
                                                                      │ Recurring Task   │
                                                                      │    Service       │
                                                                      │                  │
                                                                      │ 6. Calculate     │
                                                                      │    next_         │
                                                                      │    occurrence    │
                                                                      │    (RRULE)       │
                                                                      └──────┬───────────┘
                                                                             │
                                                                             │ 7. Dapr Service
                                                                             │    Invocation
                                                                             ▼
                                                                      ┌─────────────────┐
                                                                      │     Backend     │
                                                                      │                 │
                                                                      │ 8. Create next  │
                                                                      │    occurrence   │
                                                                      │    task         │
                                                                      └─────────────────┘
```

**Event Schema** (task.completed):
```json
{
  "event_id": "task.completed-123-1735497600000",
  "event_type": "task.completed",
  "event_version": "1.0",
  "task_id": 123,
  "user_id": "user-456",
  "timestamp": "2025-12-29T10:00:00Z",
  "payload": {
    "task_id": 123,
    "completed_at": "2025-12-29T10:00:00Z",
    "recurring_pattern": "DAILY",
    "recurring_end_date": null
  }
}
```

**Idempotency**: Event ID format `{event_type}-{task_id}-{timestamp_ms}` ensures duplicate events are ignored.

**User Isolation**: `user_id` field partitions Kafka topic, ensuring events for same user are processed in order.

### Event Flow 2: Task with Due Date → Reminder Scheduled → Email Sent

**Scenario**: User creates task with due date and reminder offset → Reminder sent at scheduled time

```
┌──────────┐     1. POST /api/{user_id}/tasks                         ┌─────────┐
│          │────────────────────────────────────────────────────────▶ │         │
│  User    │     {title, due_date, reminder_offset_hours: 1}          │ Backend │
│ (Browser)│                                                            │         │
└──────────┘     2. 201 Created {task: {..., reminder_at}}            └────┬────┘
                 ◀────────────────────────────────────────────────────────┘
                                                                             │
                                                                             │ 3. Publish event
                                                                             │    reminder.scheduled
                                                                             ▼
                                                                      ┌──────────────┐
                                                                      │ Dapr Pub/Sub │
                                                                      │   Sidecar    │
                                                                      └──────┬───────┘
                                                                             │
                                                                             │ 4. Kafka topic
                                                                             │    reminders
                                                                             ▼
                                                                      ┌──────────────┐
                                                                      │    Kafka     │
                                                                      └──────┬───────┘
                                                                             │
                                                                             │ 5. Consume event
                                                                             ▼
                                                                      ┌──────────────────┐
                                                                      │  Notification    │
                                                                      │    Service       │
                                                                      │                  │
                                                                      │ 6. Schedule Dapr │
                                                                      │    Job at        │
                                                                      │    reminder_at   │
                                                                      └──────┬───────────┘
                                                                             │
                                                                             │ 7. Dapr Jobs API
                                                                             ▼
                                                                      ┌──────────────────┐
                                                                      │ Dapr Job         │
                                                                      │ Scheduler        │
                                                                      └──────┬───────────┘
                                                                             │
                         ┌───────────────────────────────────────────────────┘
                         │ 8. Callback at scheduled time
                         │    POST /api/jobs/trigger
                         ▼
                  ┌──────────────────┐
                  │  Notification    │
                  │    Service       │
                  │                  │
                  │ 9. Send email    │
                  │    via SMTP      │
                  └──────┬───────────┘
                         │
                         │ 10. SMTP server
                         ▼
                  ┌──────────────────┐
                  │  Email Server    │
                  │  (Gmail, etc.)   │
                  └──────────────────┘
```

**Event Schema** (reminder.scheduled):
```json
{
  "event_id": "reminder.scheduled-123-1735497600000",
  "event_type": "reminder.scheduled",
  "event_version": "1.0",
  "task_id": 123,
  "user_id": "user-456",
  "timestamp": "2025-12-29T10:00:00Z",
  "payload": {
    "task_id": 123,
    "title": "Important meeting",
    "due_date": "2025-12-29T15:00:00Z",
    "reminder_at": "2025-12-29T14:00:00Z"
  }
}
```

**Retry Strategy**: If email fails, retry 10 times with exponential backoff (1s, 2s, 4s, ..., 512s ≈ 17 minutes total).

### Event Flow 3: Failed Event → Dead Letter Queue → Manual Retry

**Scenario**: Event processing fails after max retries → Moved to DLQ → Ops team manually retries

```
Kafka (task-events) → Consumer fails → Retry 3 times → DLQ (task-events-dlq)
                                                              │
                                                              │ Alert ops team
                                                              ▼
                                                        ┌────────────────┐
                                                        │  Ops Team      │
                                                        │  (Slack/Email) │
                                                        └────┬───────────┘
                                                             │
                                                             │ Investigate logs
                                                             │ Fix root cause
                                                             │ Manual retry
                                                             ▼
                                                        POST /api/admin/dlq/retry
                                                        {event_id: "..."}
                                                             │
                                                             ▼
                                                        Re-publish to
                                                        original topic
```

**DLQ Retention**:
- `task-events-dlq`: 30 days
- `reminders-dlq`: 7 days
- `task-updates-dlq`: 14 days

---

## Infrastructure Architecture

### Kubernetes Cluster Architecture (OKE)

```
┌──────────────────────────────────────────────────────────────────────────┐
│                    Oracle Kubernetes Engine (OKE)                         │
│                    Always-Free Tier (2 nodes, 2 OCPUs each)               │
│                                                                            │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │                       Load Balancer                               │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐   │   │
│  │  │   Ingress    │  │   TLS        │  │   cert-manager       │   │   │
│  │  │   Controller │  │   Termination│  │   (Let's Encrypt)    │   │   │
│  │  └──────┬───────┘  └──────────────┘  └──────────────────────┘   │   │
│  └─────────┼──────────────────────────────────────────────────────────┘   │
│            │                                                               │
│  ┌─────────▼────────────────────────────────────────────────────────┐   │
│  │                    Application Namespace                           │   │
│  │  ┌─────────────────┐  ┌─────────────────┐  ┌──────────────────┐  │   │
│  │  │    Frontend     │  │     Backend     │  │ Recurring Task   │  │   │
│  │  │   Deployment    │  │   Deployment    │  │   Service        │  │   │
│  │  │   (2 replicas)  │  │   (2 replicas)  │  │   (2 replicas)   │  │   │
│  │  │   + Dapr        │  │   + Dapr        │  │   + Dapr         │  │   │
│  │  └─────────────────┘  └─────────────────┘  └──────────────────┘  │   │
│  │                                                                     │   │
│  │  ┌─────────────────┐                                              │   │
│  │  │  Notification   │                                              │   │
│  │  │    Service      │                                              │   │
│  │  │   (2 replicas)  │                                              │   │
│  │  │   + Dapr        │                                              │   │
│  │  └─────────────────┘                                              │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                            │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │                     Data Plane Namespace                          │   │
│  │  ┌─────────────────┐  ┌─────────────────┐                        │   │
│  │  │     Kafka       │  │   PostgreSQL    │                        │   │
│  │  │  (Bitnami)      │  │   (External     │                        │   │
│  │  │  (1 replica)    │  │    Neon DB)     │                        │   │
│  │  │  (12 partitions)│  │                 │                        │   │
│  │  └─────────────────┘  └─────────────────┘                        │   │
│  └──────────────────────────────────────────────────────────────────┘   │
│                                                                            │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │                   Monitoring Namespace                            │   │
│  │  ┌─────────────────┐  ┌─────────────────┐  ┌──────────────────┐  │   │
│  │  │   Prometheus    │  │     Grafana     │  │     Zipkin       │  │   │
│  │  │   (1 replica)   │  │   (1 replica)   │  │   (1 replica)    │  │   │
│  │  └─────────────────┘  └─────────────────┘  └──────────────────┘  │   │
│  │                                                                     │   │
│  │  ┌─────────────────┐                                              │   │
│  │  │  Alertmanager   │                                              │   │
│  │  │   (1 replica)   │                                              │   │
│  │  └─────────────────┘                                              │   │
│  └──────────────────────────────────────────────────────────────────┘   │
│                                                                            │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │                      Dapr System Namespace                        │   │
│  │  ┌─────────────────┐  ┌─────────────────┐  ┌──────────────────┐  │   │
│  │  │  Dapr Operator  │  │ Dapr Sentry     │  │ Dapr Placement   │  │   │
│  │  │   (mTLS CA)     │  │ (Cert Manager)  │  │   (Actor Host)   │  │   │
│  │  └─────────────────┘  └─────────────────┘  └──────────────────┘  │   │
│  └──────────────────────────────────────────────────────────────────┘   │
│                                                                            │
└────────────────────────────────────────────────────────────────────────────┘
```

### Resource Allocation (Always-Free Tier)

| Service | CPU Request | CPU Limit | Memory Request | Memory Limit | Replicas |
|---------|-------------|-----------|----------------|--------------|----------|
| Frontend | 100m | 500m | 256Mi | 512Mi | 2 |
| Backend | 200m | 1000m | 512Mi | 1Gi | 2 |
| Recurring Task Service | 100m | 500m | 256Mi | 512Mi | 2 |
| Notification Service | 100m | 500m | 256Mi | 512Mi | 2 |
| Kafka | 500m | 1000m | 1Gi | 2Gi | 1 |
| Prometheus | 200m | 500m | 512Mi | 1Gi | 1 |
| Grafana | 100m | 300m | 256Mi | 512Mi | 1 |
| Zipkin | 100m | 300m | 256Mi | 512Mi | 1 |

**Total**: ~1.6 OCPUs, ~5.5Gi memory (fits in 2 nodes × 2 OCPUs × 12Gi)

---

## Database Schema

### Tasks Table

```sql
CREATE TABLE tasks (
    id SERIAL PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    user_id VARCHAR(255) NOT NULL,  -- Better Auth user ID
    completed BOOLEAN DEFAULT FALSE,
    priority VARCHAR(20) DEFAULT 'medium',  -- Phase II
    tags TEXT[],  -- Phase II
    due_date TIMESTAMP,  -- Phase II
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),

    -- Phase V: Recurring Tasks
    recurring_pattern VARCHAR(255),  -- RRULE pattern (e.g., "DAILY", "WEEKLY", "FREQ=DAILY;INTERVAL=2")
    recurring_end_date TIMESTAMP,  -- End date for recurring series
    next_occurrence TIMESTAMP,  -- Next scheduled occurrence
    parent_task_id INTEGER,  -- Reference to parent recurring task

    -- Phase V: Reminders
    reminder_at TIMESTAMP,  -- Exact time to send reminder
    reminder_sent BOOLEAN DEFAULT FALSE,  -- Flag to prevent duplicate reminders

    -- Indexes
    INDEX idx_user_id (user_id),
    INDEX idx_next_occurrence (next_occurrence) WHERE next_occurrence IS NOT NULL,
    INDEX idx_reminder_at (reminder_at, user_id) WHERE reminder_at IS NOT NULL AND reminder_sent = FALSE,
    INDEX idx_tags (tags) USING GIN,  -- For tag filtering
    INDEX idx_priority (priority)  -- For priority filtering
);
```

### Event Processing Idempotency Table (Dapr State Store)

```sql
CREATE TABLE dapr_state (
    key VARCHAR(255) PRIMARY KEY,  -- Format: "event-{event_id}"
    value JSONB,  -- {processed: true, processed_at: "2025-12-29T10:00:00Z"}
    created_at TIMESTAMP DEFAULT NOW(),
    ttl INTEGER DEFAULT 86400  -- 24 hour TTL
);
```

---

## Security Architecture

### Authentication Flow (Better Auth + JWT)

```
1. User signs in via Frontend (Better Auth)
   ↓
2. Better Auth generates JWT token (signed with BETTER_AUTH_SECRET)
   ↓
3. Frontend stores token in localStorage/httpOnly cookie
   ↓
4. Frontend sends token in Authorization header for all API requests
   ↓
5. Backend verifies JWT signature using shared BETTER_AUTH_SECRET
   ↓
6. Backend extracts user_id from JWT payload
   ↓
7. Backend filters all database queries by user_id (User Isolation)
```

### Service-to-Service Authentication (Dapr mTLS)

```
Recurring Task Service → Dapr Sidecar → mTLS → Backend Dapr Sidecar → Backend
                     (Certificate validation)
```

**Features**:
- Automatic certificate rotation
- Mutual authentication (both client and server verify certificates)
- Encrypted communication (TLS 1.3)

### Secret Management (Dapr Secrets API)

```
Application → Dapr Secrets API → OCI Vault (Cloud) / Kubernetes Secrets (Minikube)
```

**Secrets Stored**:
- `DATABASE_URL`: Neon PostgreSQL connection string
- `BETTER_AUTH_SECRET`: Shared secret for JWT verification
- `SMTP_PASSWORD`: Email server credentials
- `KAFKA_SASL_USERNAME` / `KAFKA_SASL_PASSWORD`: Kafka authentication (cloud)

---

## Scalability and Resilience

### Horizontal Scaling

**Auto-Scaling Rules** (Kubernetes HPA):
```yaml
Backend:
  minReplicas: 2
  maxReplicas: 10
  targetCPUUtilizationPercentage: 70

Recurring Task Service:
  minReplicas: 2
  maxReplicas: 12  # Match Kafka partition count
  targetCPUUtilizationPercentage: 70

Notification Service:
  minReplicas: 2
  maxReplicas: 12  # Match Kafka partition count
  targetCPUUtilizationPercentage: 70
```

**Kafka Partitioning**: 12 partitions per topic enables up to 12 parallel consumer instances.

### Resilience Patterns

#### 1. Circuit Breaker (Dapr)

```yaml
apiVersion: dapr.io/v1alpha1
kind: Configuration
metadata:
  name: dapr-config
spec:
  features:
    - name: Resiliency
      enabled: true
  resiliency:
    circuitBreakers:
      default:
        maxRequests: 3
        interval: 60s
        timeout: 5s
        trip: consecutiveFailures > 5
```

#### 2. Retry Policy (Event-Type Specific)

- **Task Completion Events**: 3 retries (30s, 5min, 30min)
- **Reminder Events**: 10 retries (1s, 2s, 4s, ..., 512s)
- **Task Update Events**: 5 retries (1s, 2s, 4s, 8s, 16s)

#### 3. Dead Letter Queue (DLQ)

Failed events after max retries are moved to DLQ topic with retention:
- `task-events-dlq`: 30 days
- `reminders-dlq`: 7 days
- `task-updates-dlq`: 14 days

#### 4. Health Checks

All services implement:
- **Liveness Probe**: `/health/live` (Is process running?)
- **Readiness Probe**: `/health/ready` (Can service handle traffic?)

```yaml
livenessProbe:
  httpGet:
    path: /health/live
    port: 8000
  initialDelaySeconds: 30
  periodSeconds: 10

readinessProbe:
  httpGet:
    path: /health/ready
    port: 8000
  initialDelaySeconds: 5
  periodSeconds: 5
```

---

## Appendix: Technology Stack Summary

| Layer | Technology | Version | Purpose |
|-------|------------|---------|---------|
| Frontend | Next.js | 16+ | UI framework |
| Backend | FastAPI | 0.115+ | API framework |
| Database | Neon PostgreSQL | 16+ | Persistent storage |
| Message Broker | Kafka / Redpanda | 3.6+ | Event streaming |
| Service Mesh | Dapr | 1.12+ | Microservices runtime |
| Orchestration | Kubernetes | 1.28+ | Container orchestration |
| Package Manager | Helm | 3.x | K8s package management |
| IaC | Terraform | 1.9+ | Infrastructure provisioning |
| Monitoring | Prometheus | 2.x | Metrics collection |
| Visualization | Grafana | 11.x | Metrics dashboards |
| Tracing | Zipkin | 3.x | Distributed tracing |
| Auth | Better Auth | 1.x | Authentication |
| Language (Backend) | Python | 3.13+ | Backend services |
| Language (Frontend) | TypeScript | 5+ | Frontend code |

---

For questions or clarifications, contact the development team at `dev@example.com` or Slack `#todo-app-dev`.
