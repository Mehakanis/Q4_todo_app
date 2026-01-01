# Phase V - Operations Runbook

**Version**: 1.0.0
**Last Updated**: 2025-12-31
**On-Call**: ops@example.com
**Escalation**: engineering@example.com

This runbook provides step-by-step procedures for common operational tasks, incident response, and troubleshooting for the Phase V Todo Application.

## Table of Contents

1. [Common Operations](#common-operations)
2. [Scaling Services](#scaling-services)
3. [Managing Kafka Topics](#managing-kafka-topics)
4. [Rotating Secrets](#rotating-secrets)
5. [Viewing Logs](#viewing-logs)
6. [Debugging Dapr Issues](#debugging-dapr-issues)
7. [Incident Response](#incident-response)
8. [Emergency Procedures](#emergency-procedures)

---

## Common Operations

### Health Check

```bash
# Check all pods status
kubectl get pods --all-namespaces

# Check specific service health
kubectl exec deployment/backend -- curl -f http://localhost:8000/health

# Check Dapr health
dapr status -k

# Check Kafka health
kubectl exec kafka-0 -- kafka-broker-api-versions.sh --bootstrap-server localhost:9092
```

### Restart Services

```bash
# Restart backend service (rolling restart)
kubectl rollout restart deployment/backend

# Restart recurring task service
kubectl rollout restart deployment/recurring-task-service

# Restart notification service
kubectl rollout restart deployment/notification-service

# Restart all services
kubectl rollout restart deployment --all

# Wait for rollout to complete
kubectl rollout status deployment/backend --timeout=5m
```

### Update Configuration

```bash
# Update ConfigMap
kubectl edit configmap backend-config

# Restart pods to pick up new config
kubectl rollout restart deployment/backend

# Update Dapr component
kubectl edit component pubsub-kafka

# Restart affected pods
kubectl rollout restart deployment/backend deployment/recurring-task-service
```

---

## Scaling Services

### Manual Scaling

```bash
# Scale backend service to 3 replicas
kubectl scale deployment/backend --replicas=3

# Scale recurring task service
kubectl scale deployment/recurring-task-service --replicas=5

# Scale notification service
kubectl scale deployment/notification-service --replicas=2

# Verify scaling
kubectl get deployment
kubectl get pods -w
```

### Horizontal Pod Autoscaler (HPA)

```bash
# Create HPA for backend (CPU-based)
kubectl autoscale deployment/backend \
  --min=2 \
  --max=10 \
  --cpu-percent=70

# Create HPA for recurring task service (custom metric: consumer lag)
kubectl apply -f - <<EOF
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: recurring-task-service-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: recurring-task-service
  minReplicas: 2
  maxReplicas: 12  # Match Kafka partitions
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Pods
    pods:
      metric:
        name: kafka_consumer_lag
      target:
        type: AverageValue
        averageValue: "100"  # Scale if lag > 100 messages
EOF

# Check HPA status
kubectl get hpa
kubectl describe hpa recurring-task-service-hpa
```

### Kafka Consumer Scaling

**⚠️ IMPORTANT**: Recurring Task Service can scale up to **12 replicas** (number of Kafka partitions). Scaling beyond 12 provides no benefit due to partition limits.

```bash
# Check current consumer lag
kubectl exec kafka-0 -- kafka-consumer-groups.sh \
  --bootstrap-server localhost:9092 \
  --group recurring-task-service \
  --describe

# If lag is high (>1000 messages), scale up
kubectl scale deployment/recurring-task-service --replicas=6

# Wait for partition rebalancing (30-60s)
sleep 60

# Verify lag decreased
kubectl exec kafka-0 -- kafka-consumer-groups.sh \
  --bootstrap-server localhost:9092 \
  --group recurring-task-service \
  --describe
```

---

## Managing Kafka Topics

### List Topics

```bash
kubectl exec kafka-0 -- kafka-topics.sh \
  --list \
  --bootstrap-server localhost:9092
```

### Describe Topic

```bash
kubectl exec kafka-0 -- kafka-topics.sh \
  --describe \
  --topic task-events \
  --bootstrap-server localhost:9092
```

### Update Topic Configuration

```bash
# Increase retention to 30 days (production)
kubectl exec kafka-0 -- kafka-configs.sh \
  --alter \
  --entity-type topics \
  --entity-name task-events \
  --add-config retention.ms=2592000000 \
  --bootstrap-server localhost:9092

# Increase partitions (CANNOT DECREASE)
kubectl exec kafka-0 -- kafka-topics.sh \
  --alter \
  --topic task-events \
  --partitions 24 \
  --bootstrap-server localhost:9092
```

### Monitor Consumer Lag

```bash
# Check lag for all consumer groups
kubectl exec kafka-0 -- kafka-consumer-groups.sh \
  --all-groups \
  --describe \
  --bootstrap-server localhost:9092

# Alert if lag > 60 seconds
LAG=$(kubectl exec kafka-0 -- kafka-consumer-groups.sh \
  --group recurring-task-service \
  --describe \
  --bootstrap-server localhost:9092 | \
  awk '{print $5}' | tail -n +2 | sort -n | tail -1)

if [ "$LAG" -gt 60000 ]; then
  echo "CRITICAL: Consumer lag is $LAG messages" | mail -s "KAFKA LAG ALERT" ops@example.com
fi
```

### Reset Consumer Group Offset (Emergency)

**⚠️ CAUTION**: This will cause events to be reprocessed. Use only for disaster recovery.

```bash
# Reset to earliest offset (replay all events)
kubectl exec kafka-0 -- kafka-consumer-groups.sh \
  --reset-offsets \
  --to-earliest \
  --group recurring-task-service \
  --topic task-events \
  --execute \
  --bootstrap-server localhost:9092

# Reset to specific timestamp
kubectl exec kafka-0 -- kafka-consumer-groups.sh \
  --reset-offsets \
  --to-datetime 2025-12-31T10:00:00.000 \
  --group recurring-task-service \
  --topic task-events \
  --execute \
  --bootstrap-server localhost:9092
```

---

## Rotating Secrets

### Database Credentials

```bash
# 1. Create new secret with updated password
kubectl create secret generic database-secrets-new \
  --from-literal=url="postgresql://user:NEW_PASSWORD@host:5432/db"

# 2. Update deployment to use new secret
kubectl set env deployment/backend --from=secret/database-secrets-new

# 3. Wait for rolling update
kubectl rollout status deployment/backend

# 4. Verify connectivity
kubectl exec deployment/backend -- curl -f http://localhost:8000/health

# 5. Delete old secret
kubectl delete secret database-secrets
kubectl rename secret database-secrets-new database-secrets
```

### Dapr Secrets (OCI Vault)

```bash
# 1. Update secret in OCI Vault
oci vault secret update-base64 \
  --secret-id $SECRET_OCID \
  --secret-content-content "NEW_SECRET_VALUE"

# 2. Restart pods to pick up new secret
kubectl rollout restart deployment/backend

# 3. Verify secret rotation
kubectl logs deployment/backend | grep -i "secret loaded"
```

### Kubernetes Secrets

```bash
# 1. Generate new secret value
NEW_SECRET=$(openssl rand -base64 32)

# 2. Update secret
kubectl create secret generic app-secrets \
  --from-literal=api-key=$NEW_SECRET \
  --dry-run=client -o yaml | kubectl apply -f -

# 3. Restart affected pods
kubectl rollout restart deployment/backend deployment/frontend
```

---

## Viewing Logs

### Application Logs

```bash
# View backend logs
kubectl logs deployment/backend --tail=100

# Stream logs
kubectl logs deployment/backend -f

# View logs from all backend pods
kubectl logs -l app=backend --tail=50

# View logs from specific container (if multi-container pod)
kubectl logs backend-xxxxx -c backend

# View Dapr sidecar logs
kubectl logs backend-xxxxx -c daprd
```

### Structured Log Queries

```bash
# Filter logs by user_id
kubectl logs deployment/backend | jq 'select(.user_id == "user-123")'

# Filter logs by event_type
kubectl logs deployment/recurring-task-service | jq 'select(.event_type == "task.completed")'

# Filter ERROR logs
kubectl logs deployment/backend | jq 'select(.level == "ERROR")'

# Count errors in last 1000 lines
kubectl logs deployment/backend --tail=1000 | jq 'select(.level == "ERROR")' | wc -l
```

### Centralized Logging (Fluentd)

```bash
# Query OCI Logging service
oci logging search --log-group-id $LOG_GROUP_OCID \
  --query-string 'search "error" | fields timestamp, message, user_id' \
  --start-time 2025-12-31T00:00:00Z \
  --end-time 2025-12-31T23:59:59Z

# View Fluentd DaemonSet logs
kubectl logs daemonset/fluentd -n kube-system
```

---

## Debugging Dapr Issues

### Check Dapr Installation

```bash
# Check Dapr status
dapr status -k

# Expected output:
#   NAME                   NAMESPACE    HEALTHY  STATUS   REPLICAS  VERSION  AGE
#   dapr-sentry            dapr-system  True     Running  1         1.12.0   2d
#   dapr-operator          dapr-system  True     Running  1         1.12.0   2d
#   dapr-placement-server  dapr-system  True     Running  1         1.12.0   2d
#   dapr-sidecar-injector  dapr-system  True     Running  1         1.12.0   2d

# Check Dapr pods
kubectl get pods -n dapr-system
```

### Check Dapr Components

```bash
# List all Dapr components
kubectl get components

# Describe component
kubectl describe component pubsub-kafka

# Test component connectivity
kubectl exec deployment/backend -- curl -f http://localhost:3500/v1.0/healthz

# Check component logs
kubectl logs -l app=dapr-operator -n dapr-system
```

### Dapr Sidecar Not Injected

**Symptoms**: Application pod has only 1 container (no `daprd` sidecar)

**Diagnosis**:
```bash
kubectl get pod backend-xxxxx -o jsonpath='{.spec.containers[*].name}'
# Should output: backend daprd
```

**Solutions**:
1. Check deployment annotations:
   ```yaml
   annotations:
     dapr.io/enabled: "true"
     dapr.io/app-id: "backend"
     dapr.io/app-port: "8000"
   ```
2. Restart pod: `kubectl delete pod backend-xxxxx`
3. Check sidecar-injector: `kubectl logs -l app=dapr-sidecar-injector -n dapr-system`

### Dapr Pub/Sub Not Working

**Symptoms**: Events not published/consumed

**Diagnosis**:
```bash
# Check Pub/Sub component
kubectl get component pubsub-kafka -o yaml

# Test Pub/Sub endpoint
kubectl exec deployment/backend -- curl -X POST \
  http://localhost:3500/v1.0/publish/kafka-pubsub/task-events \
  -H "Content-Type: application/json" \
  -d '{"test": "event"}'

# Check Dapr sidecar logs
kubectl logs backend-xxxxx -c daprd | grep -i pubsub
```

**Solutions**:
1. Verify Kafka connection: `kubectl get component pubsub-kafka -o yaml | grep brokers`
2. Check Kafka topics exist: `kubectl exec kafka-0 -- kafka-topics.sh --list`
3. Restart Dapr components: `kubectl rollout restart deployment -n dapr-system`

---

## Incident Response

### High Consumer Lag (>60s)

**Severity**: P2 (Warning)

**Symptoms**:
- Prometheus alert: `KafkaConsumerLag > 60000`
- Delayed next occurrence creation
- Delayed reminder notifications

**Response**:
1. Check current lag:
   ```bash
   ./phase-5/scripts/verify-kafka-lag.sh
   ```
2. Scale recurring task service:
   ```bash
   kubectl scale deployment/recurring-task-service --replicas=8
   ```
3. Monitor lag decrease:
   ```bash
   watch -n 5 './phase-5/scripts/verify-kafka-lag.sh'
   ```
4. If lag persists >5 minutes, escalate to engineering

### Reminder Delivery Failures (>10%)

**Severity**: P1 (Critical)

**Symptoms**:
- Prometheus alert: `ReminderDeliveryFailureRate > 0.1`
- Users not receiving reminder emails
- High error rate in notification-service logs

**Response**:
1. Check notification service logs:
   ```bash
   kubectl logs deployment/notification-service --tail=100 | grep -i error
   ```
2. Check SMTP connectivity:
   ```bash
   kubectl exec deployment/notification-service -- curl -f smtp://smtp.example.com:587
   ```
3. Check dead letter queue:
   ```bash
   kubectl exec kafka-0 -- kafka-console-consumer.sh \
     --bootstrap-server localhost:9092 \
     --topic reminders-dlq \
     --from-beginning \
     --max-messages 10
   ```
4. Manual retry failed reminders:
   ```bash
   curl -X POST http://admin.example.com/api/admin/retry-dlq \
     -H "Authorization: Bearer $ADMIN_TOKEN" \
     -d '{"topic": "reminders-dlq", "max_count": 100}'
   ```

### Database Connection Pool Exhausted

**Severity**: P1 (Critical)

**Symptoms**:
- 500 errors on API requests
- Logs: "connection pool exhausted"
- Prometheus alert: `DatabaseConnectionPoolUsage > 0.9`

**Response**:
1. Check current connections:
   ```bash
   kubectl exec deployment/backend -- psql $DATABASE_URL -c "SELECT count(*) FROM pg_stat_activity;"
   ```
2. Increase pool size (emergency):
   ```bash
   kubectl set env deployment/backend DB_POOL_SIZE=30 DB_MAX_OVERFLOW=20
   ```
3. Restart backend:
   ```bash
   kubectl rollout restart deployment/backend
   ```
4. Investigate long-running queries:
   ```bash
   kubectl exec deployment/backend -- psql $DATABASE_URL -c "SELECT pid, now() - query_start as duration, query FROM pg_stat_activity WHERE state != 'idle' ORDER BY duration DESC LIMIT 10;"
   ```

---

## Emergency Procedures

### Complete Service Outage

1. **Acknowledge incident**: Post to #incidents Slack channel
2. **Check cluster health**:
   ```bash
   kubectl get nodes
   kubectl get pods --all-namespaces
   ```
3. **Restart all services**:
   ```bash
   kubectl rollout restart deployment --all
   ```
4. **Monitor recovery**:
   ```bash
   watch -n 2 'kubectl get pods'
   ```
5. **Verify functionality**:
   ```bash
   ./phase-5/scripts/validate-deployment.sh
   ```
6. **Postmortem**: Document root cause, timeline, resolution

### Data Corruption

1. **Stop writes immediately**:
   ```bash
   kubectl scale deployment/backend --replicas=0
   ```
2. **Backup database**:
   ```bash
   pg_dump $DATABASE_URL > backup-$(date +%Y%m%d_%H%M%S).sql
   ```
3. **Restore from latest backup**:
   ```bash
   psql $DATABASE_URL < backup-20251230_000000.sql
   ```
4. **Validate data integrity**:
   ```bash
   psql $DATABASE_URL -c "SELECT count(*) FROM tasks WHERE user_id IS NULL;"
   ```
5. **Resume operations**:
   ```bash
   kubectl scale deployment/backend --replicas=2
   ```

### Security Incident

1. **Isolate affected services**:
   ```bash
   kubectl delete networkpolicy allow-all
   kubectl apply -f phase-5/k8s/network-policy-deny-all.yaml
   ```
2. **Rotate all secrets**:
   ```bash
   ./phase-5/scripts/rotate-all-secrets.sh
   ```
3. **Audit access logs**:
   ```bash
   kubectl logs deployment/backend | jq 'select(.level == "WARN" or .level == "ERROR")'
   ```
4. **Contact security team**: security@example.com

---

## Contacts

**On-Call Engineer**: ops@example.com
**Escalation (Engineering)**: engineering@example.com
**Security Team**: security@example.com
**PagerDuty**: https://your-org.pagerduty.com

**Resources**:
- Grafana: https://grafana.example.com
- Zipkin: https://zipkin.example.com
- OCI Console: https://cloud.oracle.com
- Slack: #todo-app-ops

---

For deployment procedures, see [DEPLOYMENT.md](DEPLOYMENT.md).

For monitoring details, see [MONITORING.md](MONITORING.md).

For architecture overview, see [ARCHITECTURE.md](ARCHITECTURE.md).
