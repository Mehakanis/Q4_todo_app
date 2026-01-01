#!/bin/bash
# Create Kafka Topics Script - Phase V
# Purpose: Create all required Kafka topics for event-driven architecture
# Topics: task-events, reminders, task-updates
# Partitions: 12 per topic (for user_id hash-based partitioning)
# Retention: 7 days (Minikube), 30 days (Cloud - configured in values files)

set -euo pipefail  # Exit on error, undefined variables, and pipe failures

# Configuration
KAFKA_NAMESPACE="${KAFKA_NAMESPACE:-default}"
KAFKA_POD="${KAFKA_POD:-kafka-0}"  # Bitnami Kafka pod name
KAFKA_CONTAINER="kafka"
RETENTION_HOURS="${RETENTION_HOURS:-168}"  # 7 days default (override for cloud: 720 for 30 days)

# Topic configuration
TOPICS=("task-events" "reminders" "task-updates")
PARTITIONS=12  # Partition by user_id (hash-based)
REPLICATION_FACTOR=1  # 1 for Minikube, 3 for cloud

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'  # No Color

echo "================================================="
echo "Creating Kafka Topics for Phase V"
echo "================================================="
echo "Namespace: ${KAFKA_NAMESPACE}"
echo "Kafka Pod: ${KAFKA_POD}"
echo "Partitions: ${PARTITIONS}"
echo "Replication Factor: ${REPLICATION_FACTOR}"
echo "Retention Hours: ${RETENTION_HOURS}"
echo "================================================="

# Function to create a topic
create_topic() {
    local topic_name=$1
    local partitions=$2
    local replication_factor=$3
    local retention_hours=$4

    echo -e "${YELLOW}Creating topic: ${topic_name}${NC}"

    # Check if topic already exists
    if kubectl exec -n "${KAFKA_NAMESPACE}" "${KAFKA_POD}" -c "${KAFKA_CONTAINER}" -- \
        kafka-topics.sh --bootstrap-server localhost:9092 --list | grep -q "^${topic_name}$"; then
        echo -e "${GREEN}✓ Topic '${topic_name}' already exists (skipping)${NC}"
        return 0
    fi

    # Create topic
    kubectl exec -n "${KAFKA_NAMESPACE}" "${KAFKA_POD}" -c "${KAFKA_CONTAINER}" -- \
        kafka-topics.sh --bootstrap-server localhost:9092 \
        --create \
        --topic "${topic_name}" \
        --partitions "${partitions}" \
        --replication-factor "${replication_factor}" \
        --config retention.ms=$((retention_hours * 3600 * 1000)) \
        --config compression.type=snappy \
        --config cleanup.policy=delete

    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ Topic '${topic_name}' created successfully${NC}"
    else
        echo -e "${RED}✗ Failed to create topic '${topic_name}'${NC}"
        return 1
    fi
}

# Function to verify topic configuration
verify_topic() {
    local topic_name=$1

    echo -e "${YELLOW}Verifying topic: ${topic_name}${NC}"

    kubectl exec -n "${KAFKA_NAMESPACE}" "${KAFKA_POD}" -c "${KAFKA_CONTAINER}" -- \
        kafka-topics.sh --bootstrap-server localhost:9092 \
        --describe \
        --topic "${topic_name}"

    echo ""
}

# Main execution
echo ""
echo "Creating topics..."
echo ""

for topic in "${TOPICS[@]}"; do
    create_topic "${topic}" "${PARTITIONS}" "${REPLICATION_FACTOR}" "${RETENTION_HOURS}"
    echo ""
done

echo "================================================="
echo "Verifying topic configurations..."
echo "================================================="
echo ""

for topic in "${TOPICS[@]}"; do
    verify_topic "${topic}"
done

echo "================================================="
echo "Summary"
echo "================================================="
echo -e "${GREEN}✓ All topics created successfully${NC}"
echo ""
echo "Topics created:"
for topic in "${TOPICS[@]}"; do
    echo "  - ${topic} (${PARTITIONS} partitions, ${RETENTION_HOURS}h retention)"
done
echo ""
echo "Partitioning strategy: Hash-based on user_id"
echo "Compression: Snappy"
echo "Cleanup policy: Delete"
echo ""
echo "Next steps:"
echo "1. Verify Dapr Pub/Sub component: kubectl get components kafka-pubsub"
echo "2. Test publishing: kubectl exec -it <backend-pod> -- curl http://localhost:3500/v1.0/publish/kafka-pubsub/task-events -d '{\"user_id\":\"test\"}'"
echo "3. Monitor topics: kubectl exec ${KAFKA_POD} -- kafka-console-consumer.sh --bootstrap-server localhost:9092 --topic task-events --from-beginning"
echo "================================================="
