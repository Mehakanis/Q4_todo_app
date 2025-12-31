# Phase V: Advanced Cloud Deployment

**Status**: ✅ Complete
**Version**: 1.0.0
**Last Updated**: 2025-12-31

Advanced cloud deployment with event-driven microservices, recurring tasks, reminders, Dapr integration, and production-ready Kubernetes orchestration.

---

## Table of Contents

- [Features](#features)
- [Architecture](#architecture)
- [Quick Start](#quick-start)
- [User Stories](#user-stories)
- [Tech Stack](#tech-stack)
- [Documentation](#documentation)
- [Deployment Guides](#deployment-guides)
- [Monitoring & Observability](#monitoring--observability)
- [Development](#development)

---

## Features

### Core Functionality (Phase V)

✅ **Recurring Tasks** (User Story 1)
- Create tasks with daily, weekly, monthly, or yearly patterns
- Automatic next occurrence generation when tasks complete
- Support for recurring end dates
- RRULE pattern parsing (simplified and RFC 5545 full format)

✅ **Due Dates & Reminders** (User Story 2)
- Set task due dates and times
- Schedule reminders (1 hour, 1 day, 1 week before due)
- Email notifications via Notification Service
- Exact-time scheduling with Dapr Jobs API
- Automatic reminder cancellation on task completion

✅ **Event-Driven Architecture**
- Kafka event streaming for task operations
- Dapr Pub/Sub integration for microservices
- User-isolated event partitioning (12 partitions)
- Dead Letter Queue with event-type-specific retry strategies
- At-least-once delivery guarantees

✅ **Microservices**
- **Backend Service**: FastAPI with JWT authentication
- **Recurring Task Service**: Consumes task.completed events, creates next occurrences
- **Notification Service**: Consumes reminder events, sends email notifications
- All services communicate via Dapr Pub/Sub and Service Invocation

✅ **Local Deployment (Minikube)** (User Story 3)
- One-command deployment script
- Full stack: Frontend, Backend, Kafka, Dapr, PostgreSQL
- Development-ready environment with port-forwarding
- Monitoring stack: Prometheus, Grafana, Zipkin

✅ **Cloud Deployment (OKE/AKS/GKE)** (User Story 4)
- Primary: Oracle Kubernetes Engine (OKE) with always-free tier
- Secondary: Azure (AKS), Google Cloud (GKE)
- Terraform Infrastructure as Code
- Automated CI/CD with GitHub Actions
- TLS certificates via cert-manager
- Secrets management with cloud vaults

✅ **Monitoring & Observability** (User Story 5)
- Prometheus metrics collection
- Grafana dashboards (Kafka, Dapr, Recurring Tasks, Reminders)
- Distributed tracing with Zipkin
- Centralized logging (structured JSON)
- Health check endpoints for all services
- Alertmanager with multi-channel routing (Slack, Email, PagerDuty)

### Backward Compatibility

✅ **Phase II/III/IV Features Preserved**
- Multi-user authentication (Better Auth + JWT)
- Task CRUD with user isolation
- Advanced filtering, sorting, search
- Priorities, tags, export/import
- AI chatbot with natural language task management
- All existing features work with NULL Phase V fields

---

## Architecture

### System Overview

```
┌──────────────┐   HTTPS    ┌─────────────────┐   REST/SSE   ┌──────────────────┐
│   Browser    │ ←────────→  │  Next.js 16     │ ←──────────→ │  FastAPI         │
│  (Frontend)  │             │  Frontend       │              │  Backend         │
└──────────────┘             └─────────────────┘              └──────────────────┘
                                    │                                 │
                                    │ Better Auth JWT                 │ Dapr Pub/Sub
                                    ▼                                 ▼
                             ┌─────────────────┐              ┌──────────────────┐
                             │  Better Auth    │              │  Kafka (Dapr)    │
                             │  (Auth Server)  │              │  - task-events   │
                             └─────────────────┘              │  - reminders     │
                                    │                         │  - task-updates  │
                                    │                         └──────────────────┘
                                    ▼                                 │
                             ┌────────────────────────────────────────────────────┐
                             │           Neon Serverless PostgreSQL               │
                             │  - Users, Sessions (Better Auth)                   │
                             │  - Tasks, Conversations, Messages (Application)    │
                             └────────────────────────────────────────────────────┘
                                                                      ▲
                             ┌────────────────────────────────────────┴───────────┐
                             │                                                    │
                      ┌──────────────────┐                           ┌──────────────────┐
                      │  Recurring Task  │                           │  Notification    │
                      │  Service (Dapr)  │                           │  Service (Dapr)  │
                      │  - Next occur.   │                           │  - Email alerts  │
                      └──────────────────┘                           └──────────────────┘
```

### Event Flow: Recurring Task Completion

1. User marks recurring task complete → Backend publishes `task.completed` event to Kafka
2. Kafka partitions event by `user_id` → Routes to Recurring Task Service consumer
3. Recurring Task Service calculates next occurrence using RRULE parser
4. Service creates next task via Dapr Service Invocation → Backend API
5. Backend publishes `task.created` event → Completes cycle

### Event Flow: Reminder Notification

1. User creates task with due date + reminder offset → Backend publishes `reminder.scheduled` event
2. Notification Service schedules reminder via Dapr Jobs API
3. At reminder time, Dapr triggers job → Notification Service sends email via SMTP
4. Service updates `reminder_sent=true` via Dapr Service Invocation → Backend API

---

## Quick Start

### Prerequisites

- **Local**: Docker, Minikube (4 CPUs, 8GB RAM), kubectl, Helm, Dapr CLI
- **Cloud**: Terraform, Cloud CLI (OCI/Azure/Google), kubectl, Helm

### 1. Minikube Deployment (Local)

```bash
# Start Minikube and deploy everything
cd phase-5
./scripts/deploy-minikube.sh

# Access frontend
kubectl port-forward svc/frontend 3000:3000
# Open http://localhost:3000

# Access Grafana dashboards
kubectl port-forward svc/grafana 30000:3000
# Open http://localhost:30000 (admin/admin)

# Access Zipkin tracing
kubectl port-forward svc/zipkin 30001:9411
# Open http://localhost:30001
```

### 2. Cloud Deployment (OKE)

```bash
# Provision infrastructure with Terraform
cd phase-5/terraform/oke
terraform init
terraform apply -var-file="terraform.tfvars"

# Deploy application with Helm
cd ../../
helm install todo-app ./helm/todo-app -f helm/todo-app/values-oke.yaml

# Verify deployment
kubectl get pods
kubectl get daprcomponents
```

### 3. CI/CD Deployment (Automated)

```bash
# Push to main branch triggers production deployment
git checkout main
git merge develop
git push origin main
# GitHub Actions automatically builds, tests, and deploys to OKE
```

---

## User Stories

### User Story 1: Recurring Tasks (Priority P1)

**Goal**: Users can create tasks that repeat automatically on a schedule.

**Example**:
```
User: "Create a daily task: Team standup at 9 AM"
AI: ✅ Created recurring task "Team standup" (daily at 9 AM)

[User marks task complete]
AI: ✅ Task complete. Next occurrence created for tomorrow at 9 AM.
```

**Implementation**: RRULE parser, Kafka event (`task.completed`), Recurring Task Service, next occurrence calculation

### User Story 2: Due Dates & Reminders (Priority P1)

**Goal**: Users receive automatic reminder notifications before task deadlines.

**Example**:
```
User: "Remind me to submit report by Friday 5 PM, remind me 1 day before"
AI: ✅ Task created with due date Friday 5 PM, reminder scheduled for Thursday 5 PM

[Thursday 5 PM arrives]
Email: "Reminder: Submit report is due in 1 day (Friday 5 PM)"
```

**Implementation**: Dapr Jobs API, Kafka event (`reminder.scheduled`), Notification Service, SMTP integration

### User Story 3: Local Deployment (Priority P2)

**Goal**: Developers deploy entire stack to Minikube with one command.

**Validation**: Run `./scripts/deploy-minikube.sh` → All pods Running within 15 minutes → Frontend accessible via port-forward

### User Story 4: Cloud Deployment (Priority P2)

**Goal**: Operations teams deploy to OKE/AKS/GKE with CI/CD pipelines.

**Validation**: Push to `main` → GitHub Actions builds Docker images → Helm deploys to OKE → Health checks pass → Metrics in Grafana

### User Story 5: Monitoring & Observability (Priority P3)

**Goal**: Operations teams monitor production system health and performance.

**Validation**: Access Grafana → Verify metrics from all services → Trace complete request in Zipkin → Alerts delivered to Slack/Email

---

## Tech Stack

### Backend Services

- **Framework**: FastAPI (Python 3.13+)
- **ORM**: SQLModel with Alembic migrations
- **Database**: Neon Serverless PostgreSQL
- **Authentication**: JWT verification (shared secret with Better Auth)
- **Event Streaming**: Kafka via Dapr Pub/Sub
- **Scheduling**: Dapr Jobs API (exact-time reminders)
- **Service Communication**: Dapr Service Invocation with mTLS

### Frontend

- **Framework**: Next.js 16 (App Router)
- **Language**: TypeScript 5+ (strict mode)
- **Chat UI**: OpenAI ChatKit React
- **Authentication**: Better Auth with JWT plugin
- **Styling**: Tailwind CSS 4

### Infrastructure

- **Orchestration**: Kubernetes (Minikube local, OKE/AKS/GKE cloud)
- **Service Mesh**: Dapr (all 5 building blocks: Pub/Sub, State, Bindings, Secrets, Service Invocation)
- **Message Broker**: Kafka (Bitnami Helm chart local, Redpanda Cloud Serverless cloud)
- **IaC**: Terraform (OKE/AKS/GKE templates)
- **Package Management**: Helm 3

### Monitoring & Observability

- **Metrics**: Prometheus
- **Dashboards**: Grafana (4 custom dashboards: Kafka, Dapr, Recurring Tasks, Reminders)
- **Tracing**: Zipkin (distributed tracing with Dapr integration)
- **Logging**: Structured JSON logs → OCI Logging / Azure Log Analytics / Google Cloud Logging
- **Alerting**: Alertmanager (Slack, Email, PagerDuty)

### Microservices

1. **Backend Service**: Task CRUD, JWT auth, event publishing
2. **Recurring Task Service**: Consumes `task.completed` events, creates next occurrences via RRULE parser
3. **Notification Service**: Consumes `reminder.scheduled` events, sends email notifications

---

## Documentation

### Quick Links

- **[Deployment Guide](docs/DEPLOYMENT.md)** - Complete deployment instructions (Minikube, OKE, AKS, GKE)
- **[Operations Runbook](docs/RUNBOOK.md)** - Common issues, troubleshooting, rollback procedures
- **[Monitoring Guide](docs/MONITORING.md)** - Grafana dashboards, Zipkin queries, alert response
- **[Architecture Documentation](docs/ARCHITECTURE.md)** - System context, microservices architecture, event flows

### Specifications

All specifications are in `specs/007-phase5-cloud-deployment/`:

- **[spec.md](specs/007-phase5-cloud-deployment/spec.md)** - Feature requirements, user scenarios, clarifications
- **[plan.md](specs/007-phase5-cloud-deployment/plan.md)** - Architecture decisions, implementation strategy
- **[tasks.md](specs/007-phase5-cloud-deployment/tasks.md)** - Task breakdown with dependencies (201 tasks, 8 phases)
- **[data-model.md](specs/007-phase5-cloud-deployment/data-model.md)** - Database schema changes, event schemas
- **[contracts/](specs/007-phase5-cloud-deployment/contracts/)** - API contracts, event schemas, service interfaces

---

## Deployment Guides

### Minikube (Local Development)

**Prerequisites**:
- Docker, Minikube, kubectl, Helm, Dapr CLI
- 4 CPUs, 8GB RAM minimum

**Deploy**:
```bash
cd phase-5
./scripts/deploy-minikube.sh
```

**Access**:
```bash
# Frontend
kubectl port-forward svc/frontend 3000:3000

# Grafana
kubectl port-forward svc/grafana 30000:3000

# Zipkin
kubectl port-forward svc/zipkin 30001:9411
```

**Verify**:
```bash
kubectl get pods
kubectl get daprcomponents
kubectl logs -l app=backend -f
```

See [DEPLOYMENT.md](docs/DEPLOYMENT.md) for complete instructions.

### OKE (Oracle Cloud - Primary)

**Infrastructure Provisioning**:
```bash
cd phase-5/terraform/oke
terraform init
terraform apply -var-file="terraform.tfvars"
```

**Application Deployment**:
```bash
# Configure kubectl
export KUBECONFIG=$(terraform output -raw kubeconfig_path)

# Deploy with Helm
cd ../../
helm install todo-app ./helm/todo-app -f helm/todo-app/values-oke.yaml

# Verify
kubectl get pods
kubectl get svc
```

**Always-Free Tier**: 2 VMs, 4 ARM cores, 24GB RAM total

See [DEPLOYMENT.md](docs/DEPLOYMENT.md) for OKE-specific configuration.

### AKS (Azure) / GKE (Google Cloud) - Secondary

**AKS**:
```bash
cd phase-5/terraform/aks
terraform apply
helm install todo-app ../../helm/todo-app -f ../../helm/todo-app/values-aks.yaml
```

**GKE**:
```bash
cd phase-5/terraform/gke
terraform apply
helm install todo-app ../../helm/todo-app -f ../../helm/todo-app/values-gke.yaml
```

See [DEPLOYMENT.md](docs/DEPLOYMENT.md) for cloud-specific instructions.

---

## Monitoring & Observability

### Grafana Dashboards

Access: `http://<minikube-ip>:30000` (local) or LoadBalancer IP (cloud)

**Dashboards**:
1. **Kafka Dashboard**: Topic metrics, consumer lag, partition distribution
2. **Dapr Dashboard**: Component health, service invocation metrics, pub/sub success rate
3. **Recurring Tasks Dashboard**: Creation rate, next occurrence distribution, RRULE calculation duration
4. **Reminders Dashboard**: Reminders sent total, delivery latency, failed reminders count

### Zipkin Distributed Tracing

Access: `http://<minikube-ip>:30001` (local) or LoadBalancer IP (cloud)

**Example Traces**:
- Task completion → Kafka → Recurring Task Service → Next occurrence creation
- Reminder scheduled → Dapr Jobs API → Notification Service → Email sent

### Prometheus Metrics

**Key Metrics**:
- `task_operations_total{operation="create|complete|delete"}`
- `kafka_consumer_lag_seconds`
- `dapr_component_health{component="pubsub|statestore|jobs"}`
- `reminder_delivery_latency_seconds`
- `rrule_calculation_duration_seconds`

### Health Checks

All services expose health endpoints:

```bash
# Backend
curl http://backend:8000/health

# Recurring Task Service
curl http://recurring-task-service:8001/health

# Notification Service
curl http://notification-service:8002/health
```

See [MONITORING.md](docs/MONITORING.md) for complete monitoring guide.

---

## Development

### Local Development Setup

**Backend**:
```bash
cd phase-5/backend
uv sync --extra dev
uv run alembic upgrade head
uv run uvicorn main:app --reload --port 8000
```

**Frontend**:
```bash
cd phase-5/frontend
pnpm install
pnpm dev
```

**Microservices** (in separate terminals):
```bash
# Recurring Task Service
cd phase-5/services/recurring-task-service
uv sync
uv run uvicorn main:app --port 8001

# Notification Service
cd phase-5/services/notification-service
uv sync
uv run uvicorn main:app --port 8002
```

### Testing

**Backend Tests**:
```bash
cd backend
uv run pytest                           # All tests
uv run pytest tests/unit/              # Unit tests
uv run pytest tests/integration/       # Integration tests
uv run pytest tests/e2e/               # End-to-end tests
uv run pytest --cov=. --cov-report=html # Coverage
```

**Load Tests**:
```bash
cd phase-5/tests/load
uv run locust -f test_kafka_throughput.py
uv run locust -f test_consumer_scaling.py
```

### Environment Variables

**Backend (.env)**:
```bash
DATABASE_URL=postgresql://user:password@host:5432/dbname
BETTER_AUTH_SECRET=your-secret-key
DAPR_HTTP_PORT=3500
KAFKA_BROKERS=kafka:9092
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
```

**Frontend (.env.local)**:
```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
BETTER_AUTH_SECRET=your-secret-key
DATABASE_URL=postgresql://user:password@host:5432/dbname
```

### Database Migrations

**Apply migrations**:
```bash
cd backend
uv run alembic upgrade head
```

**Create new migration**:
```bash
uv run alembic revision --autogenerate -m "Description"
```

**Rollback**:
```bash
uv run alembic downgrade -1
```

### Dapr Local Development

**Run with Dapr sidecar**:
```bash
dapr run --app-id backend --app-port 8000 -- uv run uvicorn main:app
dapr run --app-id recurring-task-service --app-port 8001 -- uv run uvicorn main:app
dapr run --app-id notification-service --app-port 8002 -- uv run uvicorn main:app
```

---

## CI/CD Pipelines

### GitHub Actions Workflows

**Production Deployment** (`.github/workflows/deploy-production.yml`):
- Trigger: Push to `main` branch
- Steps: Build Docker images → Push to OCIR → Deploy to OKE via Helm → Run health checks
- Rollback: Automatic on health check failure

**Staging Deployment** (`.github/workflows/deploy-staging.yml`):
- Trigger: Push to `develop` branch
- Steps: Build → Deploy to staging environment → Run integration tests

### Secrets Configuration

Required GitHub Secrets:
- `OCI_TENANCY_OCID`, `OCI_USER_OCID`, `OCI_FINGERPRINT`, `OCI_PRIVATE_KEY`
- `DATABASE_URL`, `BETTER_AUTH_SECRET`
- `OPENAI_API_KEY`, `SMTP_PASSWORD`

---

## Performance & Scalability

### Performance Optimizations

✅ Database connection pooling (pool_size=10, max_overflow=20)
✅ Kafka consumer prefetch optimization (prefetch_count=10)
✅ RRULE calculation caching (functools.lru_cache for repeated patterns)
✅ Bulk inserts for multiple next occurrences

### Scalability Targets

- **Kafka Throughput**: 1000 events/sec sustained
- **Consumer Scaling**: Horizontal scaling up to 12 instances (matching 12 partitions)
- **Consumer Lag**: < 1 second under normal load
- **Reminder Delivery**: Exact-time scheduling (no polling delay)

### Resource Limits (OKE Always-Free)

**Per Pod**:
- Requests: 200m CPU, 512Mi memory
- Limits: 1000m CPU, 1Gi memory

**Total Cluster** (2 nodes × 2 OCPUs × 12GB RAM):
- 4 OCPUs, 24GB RAM
- ~12 pods (backend, frontend, 2× recurring-task, 2× notification, Kafka, monitoring)

---

## Security

### Authentication & Authorization

- **Frontend → Backend**: JWT tokens signed with Better Auth shared secret
- **Service → Service**: Dapr mTLS for service invocation
- **Event Authorization**: `user_id` propagation in all Kafka events
- **User Isolation**: All database queries filtered by `user_id`

### Security Hardening

✅ Input validation for `recurring_pattern` (RRULE injection prevention)
✅ Rate limiting: 100 requests/minute per user (slowapi)
✅ User filtering in all microservices (prevent cross-user data access)
✅ Dapr mTLS enabled in production
✅ TLS certificates via cert-manager (Let's Encrypt)

### Secrets Management

- **Local**: Kubernetes Secrets
- **Cloud**: OCI Vault / Azure Key Vault / Google Secret Manager
- **Dapr**: Secrets API for secure credential retrieval
- **No hardcoded secrets**: All credentials via environment variables or Dapr Secrets

---

## Backward Compatibility

### Phase II/III/IV Features

✅ All existing tasks work with NULL Phase V fields
✅ Task creation without `recurring_pattern` creates non-recurring tasks
✅ API backward compatible (optional `recurring_pattern`, `reminder_at` parameters)
✅ Database migration rollback script available (`006_rollback.sql`)

### Migration Validation

**Test existing functionality**:
```bash
# Create non-recurring task (Phase II functionality)
POST /api/tasks {"title": "Old task"}  # No recurring_pattern

# Verify filtering works
GET /api/tasks?priority=high&completed=false

# Verify search works
GET /api/tasks?search=report

# Verify export works
GET /api/tasks/export?format=json
```

---

## Troubleshooting

### Common Issues

**Consumer Lag**:
```bash
# Check Kafka consumer lag
kubectl exec kafka-0 -- kafka-consumer-groups.sh --bootstrap-server localhost:9092 --describe --group recurring-task-service
```

**Reminder Failures**:
```bash
# Check Notification Service logs
kubectl logs -l app=notification-service -f

# Check SMTP credentials
kubectl get secret smtp-credentials -o yaml
```

**Pod Restarts**:
```bash
# Check pod events
kubectl describe pod <pod-name>

# Check resource usage
kubectl top pods
```

**Dapr Sidecar Not Running**:
```bash
# Verify Dapr annotations
kubectl get pod <pod-name> -o yaml | grep dapr.io

# Check Dapr sidecar logs
kubectl logs <pod-name> -c daprd
```

See [RUNBOOK.md](docs/RUNBOOK.md) for comprehensive troubleshooting guide.

---

## Support & Contributing

### Documentation

- **[Deployment Guide](docs/DEPLOYMENT.md)** - Complete deployment instructions
- **[Operations Runbook](docs/RUNBOOK.md)** - Troubleshooting and rollback procedures
- **[Monitoring Guide](docs/MONITORING.md)** - Dashboards, metrics, alerts
- **[Architecture Documentation](docs/ARCHITECTURE.md)** - System design and event flows

### Contributing

1. Follow [Spec-Kit Plus workflow](../.specify/README.md)
2. Use skills in `.claude/skills/` for implementation patterns
3. Write tests for all new features
4. Update documentation
5. Create pull request with clear description

### Skills Reference

- `dapr-integration` - Dapr HTTP APIs, Pub/Sub, State Store, Jobs, Secrets, Service Invocation
- `kafka-event-driven` - Event schemas, publishing, consuming, partitioning, DLQ
- `microservices-patterns` - Service-to-service communication, user isolation, idempotency
- `kubernetes-helm-deployment` - Helm charts, deployments, services, health probes
- `terraform-infrastructure` - OKE/AKS/GKE provisioning, networking, security
- `rrule-recurring-tasks` - RRULE parsing, next occurrence calculation, timezone handling
- `better-auth-ts`, `better-auth-python` - JWT verification, Better Auth integration

---

## License

MIT License - See LICENSE file for details

---

**Built with ❤️ using FastAPI, Next.js, Dapr, Kafka, and Kubernetes**

**Phase V achieves production-ready cloud deployment with:**
- Event-driven microservices architecture
- Recurring tasks with automatic next occurrence generation
- Exact-time reminder notifications
- Full observability (metrics, logs, traces)
- Multi-cloud deployment (OKE/AKS/GKE)
- Always-free tier hosting on Oracle Cloud
