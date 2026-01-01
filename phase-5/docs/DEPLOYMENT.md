# Phase V - Deployment Guide

**Version**: 1.0.0
**Last Updated**: 2025-12-31

This document provides comprehensive deployment instructions for the Phase V Todo Application across three environments: Local (Minikube), Cloud (OKE), and Secondary Clouds (AKS/GKE).

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Quick Start (Minikube)](#quick-start-minikube)
3. [Production Deployment (OKE)](#production-deployment-oke)
4. [Secondary Clouds (AKS/GKE)](#secondary-clouds-aksgke)
5. [Troubleshooting](#troubleshooting)
6. [Rollback Procedures](#rollback-procedures)

---

## Prerequisites

### Required Tools

**Local Development** (Minikube):
- Docker Desktop or Docker Engine (20.10+)
- Minikube (1.32+)
- kubectl (1.28+)
- Helm (3.12+)
- Dapr CLI (1.12+)

**Cloud Deployment** (OKE/AKS/GKE):
- Terraform (1.6+)
- kubectl (1.28+)
- Helm (3.12+)
- Cloud CLI:
  - OCI CLI (Oracle Cloud)
  - Azure CLI (Microsoft Azure)
  - gcloud CLI (Google Cloud)

### Installation Commands

```bash
# Install Minikube (macOS)
brew install minikube

# Install kubectl
brew install kubectl

# Install Helm
brew install helm

# Install Dapr CLI
curl -fsSL https://raw.githubusercontent.com/dapr/cli/master/install/install.sh | bash

# Verify installations
minikube version
kubectl version --client
helm version
dapr version
```

### Infrastructure Requirements

**Minikube (Local)**:
- 4 CPUs minimum
- 8GB RAM minimum
- 20GB disk space
- Docker driver

**OKE (Oracle Cloud Always-Free Tier)**:
- 2 VMs (VM.Standard.A1.Flex shape)
- 2 OCPUs per VM (4 total)
- 12GB RAM per VM (24GB total)
- Neon PostgreSQL (free tier: 0.5GB storage)
- Redpanda Cloud Serverless (free tier: 10GB storage, 10MB/s throughput)

**AKS (Azure) / GKE (Google Cloud)**:
- 2-3 nodes (Standard_B2s / e2-medium)
- 4GB RAM per node
- Managed Kubernetes service
- Managed PostgreSQL (Azure Database / Cloud SQL)
- Managed Kafka (Event Hubs / Pub/Sub)

---

## Quick Start (Minikube)

### 1. Start Minikube Cluster

```bash
# Start Minikube with appropriate resources
minikube start --cpus=4 --memory=8192 --driver=docker

# Verify cluster running
kubectl cluster-info
kubectl get nodes
```

### 2. Install Dapr Runtime

```bash
# Initialize Dapr on Kubernetes (development mode)
dapr init -k --runtime-version 1.12 --enable-ha=false

# Verify Dapr installation
kubectl get pods -n dapr-system

# Expected pods:
# - dapr-operator
# - dapr-placement-server
# - dapr-sentry
# - dapr-sidecar-injector
```

### 3. Deploy Kafka

```bash
# Add Bitnami Helm repository
helm repo add bitnami https://charts.bitnami.com/bitnami
helm repo update

# Install Kafka (single broker for local dev)
helm install kafka bitnami/kafka \
  -f phase-5/helm/kafka/values-minikube.yaml \
  --set persistence.size=10Gi \
  --set replicaCount=1

# Wait for Kafka ready
kubectl wait --for=condition=ready pod -l app.kubernetes.io/name=kafka --timeout=5m
```

### 4. Create Kafka Topics

```bash
# Create topics with 12 partitions (user_id partitioning)
./phase-5/scripts/create-kafka-topics.sh

# Topics created:
# - task-events (12 partitions, 7-day retention)
# - reminders (12 partitions, 7-day retention)
# - task-updates (12 partitions, 7-day retention)
```

### 5. Deploy Dapr Components

```bash
# Apply all Dapr components
kubectl apply -f phase-5/dapr/components/pubsub-kafka.yaml
kubectl apply -f phase-5/dapr/components/statestore-postgresql.yaml
kubectl apply -f phase-5/dapr/components/secretstore-kubernetes.yaml
kubectl apply -f phase-5/dapr/components/jobs-scheduler.yaml

# Verify components registered
kubectl get components
dapr components -k
```

### 6. Deploy Application

```bash
# Install Helm chart
helm install todo-app phase-5/helm/todo-app \
  -f phase-5/helm/todo-app/values-minikube.yaml \
  --set backend.image.tag=latest \
  --set frontend.image.tag=latest

# Wait for all pods ready
kubectl wait --for=condition=ready pod --all --timeout=10m
```

### 7. Deploy Monitoring Stack

```bash
# Install Prometheus
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm install prometheus prometheus-community/kube-prometheus-stack \
  -f phase-5/monitoring/prometheus/values-minikube.yaml

# Install Zipkin
kubectl apply -f phase-5/monitoring/zipkin/zipkin.yaml

# Verify monitoring pods
kubectl get pods -l app.kubernetes.io/name=prometheus
kubectl get pods -l app=zipkin
```

### 8. Access Application

```bash
# Port-forward frontend service
kubectl port-forward svc/frontend 3000:3000

# Port-forward Grafana
kubectl port-forward svc/prometheus-grafana 3001:80

# Port-forward Zipkin
kubectl port-forward svc/zipkin 9411:9411

# Access URLs:
# - Frontend: http://localhost:3000
# - Grafana: http://localhost:3001 (admin/prom-operator)
# - Zipkin: http://localhost:9411
```

### Automated Deployment

```bash
# One-command deployment (recommended)
./phase-5/scripts/deploy-minikube.sh

# This script handles:
# 1. Minikube start
# 2. Dapr installation
# 3. Kafka deployment
# 4. Topic creation
# 5. Dapr components
# 6. Application deployment
# 7. Monitoring stack
# 8. Verification checks
```

---

## Production Deployment (OKE)

### 1. Provision Infrastructure with Terraform

```bash
cd phase-5/terraform/oke

# Initialize Terraform
terraform init

# Create terraform.tfvars
cat > terraform.tfvars <<EOF
tenancy_ocid     = "ocid1.tenancy.oc1..."
user_ocid        = "ocid1.user.oc1..."
fingerprint      = "aa:bb:cc:..."
private_key_path = "~/.oci/oci_api_key.pem"
compartment_ocid = "ocid1.compartment.oc1..."
region           = "us-ashburn-1"
EOF

# Review plan
terraform plan

# Apply infrastructure (creates OKE cluster, node pool, VCN, subnets)
terraform apply

# Get kubeconfig
terraform output kubeconfig > ~/.kube/config-oke
export KUBECONFIG=~/.kube/config-oke

# Verify cluster access
kubectl get nodes
```

### 2. Initialize Dapr on OKE

```bash
# Install Dapr with mTLS enabled (production)
dapr init -k --runtime-version 1.12 --enable-mtls=true --wait

# Verify Dapr installation
kubectl get pods -n dapr-system
dapr status -k
```

### 3. Deploy Managed Kafka (Redpanda Cloud)

```bash
# Sign up for Redpanda Cloud Serverless (free tier)
# Create cluster via UI: https://cloud.redpanda.com

# Create Kafka topics via Redpanda Cloud UI or CLI:
rpk topic create task-events --partitions 12 --retention.ms 2592000000  # 30 days
rpk topic create reminders --partitions 12 --retention.ms 2592000000
rpk topic create task-updates --partitions 12 --retention.ms 2592000000

# Update Dapr Pub/Sub component with Redpanda credentials
kubectl apply -f phase-5/dapr/components/pubsub-redpanda.yaml
```

### 4. Configure Secrets (OCI Vault)

```bash
# Create secrets in OCI Vault (via OCI Console or CLI)
oci vault secret create-base64 \
  --compartment-id $COMPARTMENT_OCID \
  --vault-id $VAULT_OCID \
  --key-id $KEY_OCID \
  --secret-name DATABASE_URL \
  --secret-content-content "postgresql://user:pass@host:5432/db"

# Update Dapr Secrets component
kubectl apply -f phase-5/dapr/components/secretstore-oci-vault.yaml
```

### 5. Deploy Application via Helm

```bash
# Build and push Docker images to OCIR (Oracle Container Image Registry)
docker build -t ocir.io/tenancy/todo-backend:${GIT_SHA} phase-5/backend
docker build -t ocir.io/tenancy/todo-frontend:${GIT_SHA} phase-5/frontend
docker build -t ocir.io/tenancy/recurring-task-service:${GIT_SHA} phase-5/services/recurring-task-service
docker build -t ocir.io/tenancy/notification-service:${GIT_SHA} phase-5/services/notification-service

docker login ocir.io/tenancy -u 'tenancy/username' -p 'auth_token'
docker push ocir.io/tenancy/todo-backend:${GIT_SHA}
docker push ocir.io/tenancy/todo-frontend:${GIT_SHA}
docker push ocir.io/tenancy/recurring-task-service:${GIT_SHA}
docker push ocir.io/tenancy/notification-service:${GIT_SHA}

# Deploy with Helm (OKE values)
helm upgrade --install todo-app phase-5/helm/todo-app \
  -f phase-5/helm/todo-app/values-oke.yaml \
  --set backend.image.tag=${GIT_SHA} \
  --set frontend.image.tag=${GIT_SHA} \
  --set recurringTaskService.image.tag=${GIT_SHA} \
  --set notificationService.image.tag=${GIT_SHA}

# Wait for rollout
kubectl rollout status deployment/backend
kubectl rollout status deployment/frontend
kubectl rollout status deployment/recurring-task-service
kubectl rollout status deployment/notification-service
```

### 6. Configure TLS/HTTPS with cert-manager

```bash
# Install cert-manager
kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.13.0/cert-manager.yaml

# Create ClusterIssuer for Let's Encrypt
kubectl apply -f phase-5/k8s/cert-manager.yaml

# Create Ingress with TLS
kubectl apply -f phase-5/k8s/ingress.yaml

# Verify certificate issued
kubectl get certificate
```

### 7. Deploy Monitoring & Observability

```bash
# Install Prometheus with OKE-specific config
helm install prometheus prometheus-community/kube-prometheus-stack \
  -f phase-5/monitoring/prometheus/values-oke.yaml

# Install Zipkin
kubectl apply -f phase-5/monitoring/zipkin/zipkin-production.yaml

# Install Fluentd for centralized logging
kubectl apply -f phase-5/k8s/fluentd-daemonset.yaml

# Verify monitoring stack
kubectl get pods -l app.kubernetes.io/name=prometheus
kubectl get pods -l app=zipkin
kubectl get daemonset fluentd
```

### 8. CI/CD Deployment (Automated)

```bash
# GitHub Actions workflow (.github/workflows/deploy-production.yml)
# Triggered on: push to main branch

# Workflow steps:
# 1. Build Docker images
# 2. Push to OCIR
# 3. Update Helm chart
# 4. Deploy to OKE
# 5. Run integration tests
# 6. Verify health checks
# 7. Rollback on failure

# Manual trigger:
git push origin main

# Monitor deployment:
kubectl get pods -w
kubectl logs -f deployment/backend
```

---

## Secondary Clouds (AKS/GKE)

### Azure Kubernetes Service (AKS)

```bash
cd phase-5/terraform/aks

# Initialize Terraform
terraform init

# Create terraform.tfvars
cat > terraform.tfvars <<EOF
subscription_id = "..."
location        = "eastus"
resource_group  = "todo-app-rg"
EOF

# Apply infrastructure
terraform apply

# Get kubeconfig
az aks get-credentials --resource-group todo-app-rg --name todo-aks-cluster

# Deploy application (same Helm chart, different values)
helm install todo-app phase-5/helm/todo-app \
  -f phase-5/helm/todo-app/values-aks.yaml
```

### Google Kubernetes Engine (GKE)

```bash
cd phase-5/terraform/gke

# Initialize Terraform
terraform init

# Create terraform.tfvars
cat > terraform.tfvars <<EOF
project_id = "..."
region     = "us-central1"
EOF

# Apply infrastructure
terraform apply

# Get kubeconfig
gcloud container clusters get-credentials todo-gke-cluster --region us-central1

# Deploy application (same Helm chart, different values)
helm install todo-app phase-5/helm/todo-app \
  -f phase-5/helm/todo-app/values-gke.yaml
```

---

## Troubleshooting

### Common Issues

#### 1. Pods Not Starting

**Symptoms**: Pods stuck in Pending/CrashLoopBackOff state

**Diagnosis**:
```bash
kubectl get pods
kubectl describe pod <pod-name>
kubectl logs <pod-name>
```

**Common Causes & Solutions**:
- **Insufficient resources**: Increase Minikube memory/CPUs or scale cloud nodes
- **Image pull errors**: Verify image tag, registry credentials
- **Dapr sidecar not injected**: Check `dapr.io/enabled: "true"` annotation
- **ConfigMap/Secret missing**: Verify all Dapr components deployed

#### 2. Dapr Sidecar Not Responding

**Symptoms**: 500 errors, "dapr sidecar not running"

**Diagnosis**:
```bash
dapr status -k
kubectl get components
kubectl logs <pod-name> -c daprd
```

**Solutions**:
- Verify Dapr initialized: `dapr status -k`
- Check component YAML syntax: `kubectl get component <name> -o yaml`
- Restart pod: `kubectl delete pod <pod-name>`
- Verify Dapr sidecar port (3500) accessible

#### 3. Kafka Connection Errors

**Symptoms**: Events not published/consumed, "connection refused"

**Diagnosis**:
```bash
kubectl get pods -l app.kubernetes.io/name=kafka
kubectl logs kafka-0
kubectl exec -it kafka-0 -- kafka-topics.sh --list --bootstrap-server localhost:9092
```

**Solutions**:
- Verify Kafka pods running: `kubectl get pods -l app.kubernetes.io/name=kafka`
- Check broker URL in Dapr Pub/Sub component
- Verify topics created: `./scripts/create-kafka-topics.sh`
- Check consumer groups: `kubectl exec kafka-0 -- kafka-consumer-groups.sh --list`

#### 4. Database Connection Errors

**Symptoms**: "connection refused", "authentication failed"

**Diagnosis**:
```bash
kubectl logs <pod-name> | grep -i "database\|postgres"
kubectl get secret database-secrets -o yaml
```

**Solutions**:
- Verify DATABASE_URL secret: `kubectl get secret database-secrets`
- Test connection from pod: `kubectl exec -it <pod-name> -- psql $DATABASE_URL`
- Check Neon PostgreSQL status: https://console.neon.tech
- Verify connection pooling settings in db.py

#### 5. Monitoring Stack Issues

**Symptoms**: Grafana dashboards empty, Prometheus targets down

**Diagnosis**:
```bash
kubectl get pods -l app.kubernetes.io/name=prometheus
kubectl port-forward svc/prometheus-kube-prometheus-prometheus 9090:9090
# Access http://localhost:9090/targets
```

**Solutions**:
- Verify Prometheus scraping: Check `/targets` endpoint
- Check ServiceMonitor CRDs: `kubectl get servicemonitor`
- Verify pod annotations: `prometheus.io/scrape: "true"`
- Restart Prometheus: `kubectl delete pod -l app.kubernetes.io/name=prometheus`

---

## Rollback Procedures

### Helm Rollback

```bash
# List releases and revisions
helm list
helm history todo-app

# Rollback to previous revision
helm rollback todo-app

# Rollback to specific revision
helm rollback todo-app 2

# Verify rollback
kubectl get pods
kubectl rollout status deployment/backend
```

### Database Migration Rollback

```bash
# Rollback Phase V migrations
cd phase-5/backend
uv run alembic downgrade -1

# Or use rollback script
./phase-5/backend/migrations/006_rollback.sql

# Verify rollback
psql $DATABASE_URL -c "\d tasks"  # Should not have Phase V columns
```

### Terraform Rollback (Infrastructure)

```bash
cd phase-5/terraform/oke

# Destroy specific resources
terraform destroy -target=module.oke_cluster

# Destroy all resources (CAUTION)
terraform destroy

# Restore from state backup
terraform state pull > current.tfstate.backup
cp terraform.tfstate.backup.20251231 terraform.tfstate
terraform apply
```

### Emergency Rollback (Complete)

```bash
# 1. Rollback Helm to previous version
helm rollback todo-app

# 2. Rollback database migrations
./phase-5/backend/migrations/006_rollback.sql

# 3. Verify application functional
kubectl get pods
kubectl logs deployment/backend | head -20

# 4. Alert team
echo "Emergency rollback complete - Phase V reverted to Phase IV" | mail -s "ROLLBACK ALERT" ops@example.com
```

---

## Next Steps

After successful deployment:

1. **Verify Application**: Access frontend URL, create test tasks
2. **Check Monitoring**: View Grafana dashboards, verify metrics
3. **Review Traces**: Check Zipkin for distributed traces
4. **Configure Alerts**: Set up Slack/PagerDuty integrations
5. **Load Testing**: Run `phase-5/load-tests/kafka-throughput-test.py`
6. **Security Scan**: Run `kubectl exec backend -- safety check`

For operational procedures, see [RUNBOOK.md](RUNBOOK.md).

For monitoring details, see [MONITORING.md](MONITORING.md).

For architecture overview, see [ARCHITECTURE.md](ARCHITECTURE.md).
