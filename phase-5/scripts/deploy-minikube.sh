#!/bin/bash
set -e

# Phase V - Advanced Cloud Deployment
# Minikube Local Deployment Script
# Tasks: T087-T095

echo "🚀 Phase V: Deploying Todo Application to Minikube"
echo "=================================================="

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# T087: Start Minikube with required resources
echo -e "${BLUE}📦 Step 1/9: Starting Minikube...${NC}"
minikube start \
  --cpus=4 \
  --memory=8192 \
  --driver=docker \
  --kubernetes-version=v1.28.2

# Verify Minikube is running
if ! minikube status | grep -q "Running"; then
    echo -e "${RED}❌ Failed to start Minikube${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Minikube started successfully${NC}"

# Configure Docker environment to use Minikube's Docker daemon
eval $(minikube docker-env)

# T088: Install Dapr to Minikube
echo -e "${BLUE}📦 Step 2/9: Installing Dapr runtime...${NC}"
dapr init -k \
  --runtime-version 1.12 \
  --enable-ha=false \
  --wait

# Verify Dapr installation
kubectl wait --for=condition=ready pod -l app=dapr-operator -n dapr-system --timeout=300s
kubectl wait --for=condition=ready pod -l app=dapr-sentry -n dapr-system --timeout=300s
kubectl wait --for=condition=ready pod -l app=dapr-placement-server -n dapr-system --timeout=300s
echo -e "${GREEN}✅ Dapr installed successfully${NC}"

# T089: Deploy Kafka using Bitnami Helm chart
echo -e "${BLUE}📦 Step 3/9: Deploying Kafka cluster...${NC}"
helm repo add bitnami https://charts.bitnami.com/bitnami
helm repo update

helm install kafka bitnami/kafka \
  --set persistence.size=10Gi \
  --set replicaCount=1 \
  --set listeners.client.protocol=PLAINTEXT \
  --set logRetentionHours=168 \
  --set numPartitions=12 \
  --wait --timeout=10m

# Verify Kafka is running
kubectl wait --for=condition=ready pod -l app.kubernetes.io/name=kafka --timeout=300s
echo -e "${GREEN}✅ Kafka deployed successfully${NC}"

# T090: Create Kafka topics with 12 partitions and 7-day retention
echo -e "${BLUE}📦 Step 4/9: Creating Kafka topics...${NC}"

# Wait for Kafka to be fully ready
sleep 30

# Create task-events topic
kubectl run kafka-client-task-events --restart='Never' \
  --image docker.io/bitnami/kafka:3.6.0 \
  --rm -it -- kafka-topics.sh \
  --create \
  --topic task-events \
  --partitions 12 \
  --replication-factor 1 \
  --config retention.ms=604800000 \
  --bootstrap-server kafka:9092 || echo "Topic task-events may already exist"

# Create reminders topic
kubectl run kafka-client-reminders --restart='Never' \
  --image docker.io/bitnami/kafka:3.6.0 \
  --rm -it -- kafka-topics.sh \
  --create \
  --topic reminders \
  --partitions 12 \
  --replication-factor 1 \
  --config retention.ms=604800000 \
  --bootstrap-server kafka:9092 || echo "Topic reminders may already exist"

# Create task-updates topic
kubectl run kafka-client-task-updates --restart='Never' \
  --image docker.io/bitnami/kafka:3.6.0 \
  --rm -it -- kafka-topics.sh \
  --create \
  --topic task-updates \
  --partitions 12 \
  --replication-factor 1 \
  --config retention.ms=604800000 \
  --bootstrap-server kafka:9092 || echo "Topic task-updates may already exist"

echo -e "${GREEN}✅ Kafka topics created successfully${NC}"

# T091: Deploy Dapr components
echo -e "${BLUE}📦 Step 5/9: Deploying Dapr components...${NC}"
kubectl apply -f ../dapr/components/pubsub-kafka.yaml
kubectl apply -f ../dapr/components/statestore-postgresql.yaml
kubectl apply -f ../dapr/components/secretstore-kubernetes.yaml
kubectl apply -f ../dapr/components/jobs-scheduler.yaml
kubectl apply -f ../dapr/config/config.yaml

# Verify Dapr components
sleep 10
kubectl get components -n default
echo -e "${GREEN}✅ Dapr components deployed successfully${NC}"

# T092: Deploy application using Helm
echo -e "${BLUE}📦 Step 6/9: Deploying Todo application...${NC}"
helm install todo-app ../helm/todo-app \
  -f ../helm/todo-app/values-minikube.yaml \
  --wait --timeout=10m

# Verify application pods
kubectl wait --for=condition=ready pod -l app=backend --timeout=300s
kubectl wait --for=condition=ready pod -l app=frontend --timeout=300s
kubectl wait --for=condition=ready pod -l app=recurring-task-service --timeout=300s || echo "Recurring task service may not be ready yet"
kubectl wait --for=condition=ready pod -l app=notification-service --timeout=300s || echo "Notification service may not be ready yet"
echo -e "${GREEN}✅ Application deployed successfully${NC}"

# T093: Deploy monitoring stack
echo -e "${BLUE}📦 Step 7/9: Deploying monitoring stack...${NC}"

# Deploy Prometheus and Grafana
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update

helm install prometheus prometheus-community/kube-prometheus-stack \
  --set grafana.adminPassword=admin \
  --set prometheus.prometheusSpec.serviceMonitorSelectorNilUsesHelmValues=false \
  --set grafana.service.type=NodePort \
  --set grafana.service.nodePort=30000 \
  --set prometheus.service.type=NodePort \
  --set prometheus.service.nodePort=30090 \
  --wait --timeout=10m

# Deploy Zipkin
kubectl apply -f ../monitoring/zipkin/zipkin.yaml

# Wait for monitoring pods
kubectl wait --for=condition=ready pod -l app.kubernetes.io/name=grafana --timeout=300s
kubectl wait --for=condition=ready pod -l app=zipkin --timeout=300s || echo "Zipkin may not be ready yet"
echo -e "${GREEN}✅ Monitoring stack deployed successfully${NC}"

# T094: Verification step
echo -e "${BLUE}📦 Step 8/9: Verifying deployment...${NC}"

echo ""
echo "=== Pod Status ==="
kubectl get pods -o wide

echo ""
echo "=== Dapr Components ==="
kubectl get components

echo ""
echo "=== Services ==="
kubectl get services

echo ""
echo "=== Kafka Topics ==="
kubectl run kafka-client-verify --restart='Never' \
  --image docker.io/bitnami/kafka:3.6.0 \
  --rm -it -- kafka-topics.sh \
  --list \
  --bootstrap-server kafka:9092 || echo "Could not verify topics"

echo -e "${GREEN}✅ Verification complete${NC}"

# T095: Display access information
echo ""
echo -e "${BLUE}📦 Step 9/9: Deployment Summary${NC}"
echo "=================================================="
echo ""
echo -e "${GREEN}✅ Todo Application deployed to Minikube successfully!${NC}"
echo ""
echo "Access Information:"
echo "-------------------"
echo "📊 Grafana Dashboard:  http://$(minikube ip):30000 (admin/admin)"
echo "📈 Prometheus:         http://$(minikube ip):30090"
echo "🔍 Zipkin Tracing:     http://$(minikube ip):30001"
echo "🎛️  Dapr Dashboard:     Run 'dapr dashboard -k' (http://localhost:8080)"
echo ""
echo "Frontend Access:"
echo "----------------"
echo "Run: kubectl port-forward service/frontend 3000:3000"
echo "Then visit: http://localhost:3000"
echo ""
echo "Backend API:"
echo "------------"
echo "Run: kubectl port-forward service/backend 8000:8000"
echo "Then visit: http://localhost:8000/docs"
echo ""
echo "Useful Commands:"
echo "----------------"
echo "• View logs:        kubectl logs -f <pod-name>"
echo "• Dapr dashboard:   dapr dashboard -k"
echo "• Restart pod:      kubectl delete pod <pod-name>"
echo "• Uninstall:        helm uninstall todo-app && helm uninstall kafka && helm uninstall prometheus"
echo "• Stop Minikube:    minikube stop"
echo "• Delete Minikube:  minikube delete"
echo ""
echo -e "${YELLOW}⚠️  Note: First deployment may take 5-10 minutes for all images to pull${NC}"
echo ""
