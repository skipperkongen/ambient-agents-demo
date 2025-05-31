#!/bin/bash
set -euo pipefail

# Wait for Kafka broker to be ready
sleep 5

/opt/bitnami/kafka/bin/kafka-topics.sh --bootstrap-server kafka:9092 --create --if-not-exists --topic incoming-messages --partitions 1 --replication-factor 1
/opt/bitnami/kafka/bin/kafka-topics.sh --bootstrap-server kafka:9092 --create --if-not-exists --topic outgoing-messages --partitions 1 --replication-factor 1

