# AI-Powered Customer Service Demo with Kafka

This project demonstrates a simplified AI-powered customer service workflow for a food delivery company using Apache Kafka in KRaft mode. Customers' messages are sent to an `incoming-messages` topic, processed by a worker, and responses are published to an `outgoing-messages` topic.

## Components

1.  **`docker-compose.yml`**:
    *   Sets up a single-node Kafka broker running in KRaft mode (without Zookeeper).
    *   Defines a `kafka-setup` service that automatically creates two topics: `incoming-messages` and `outgoing-messages`.
    *   Defines services for a `producer` and a `consumer` application, built using Docker.
2.  **`producer.py` (Worker 1)**:
    *   A Python script that simulates incoming customer messages.
    *   Generates dummy messages (with fields like `message_id`, `customer_id`, `timestamp`, `subject`, `body`) once per second.
    *   Publishes these messages to the `incoming-messages` Kafka topic.
    *   This script is containerized and managed by `docker-compose`.
3.  **`consumer.py` (Worker 2)**:
    *   A Python script that simulates an AI agent processing customer messages.
    *   Consumes messages from the `incoming-messages` topic.
    *   Generates a dummy response (with fields like `original_message_id`, `response_id`, `timestamp`, `responder_type`, `body`).
    *   The response logic includes a basic simulation of escalating to a human agent for refund requests.
    *   Publishes these responses to the `outgoing-messages` Kafka topic.
    *   This script is also containerized and managed by `docker-compose`.
4.  **`Dockerfile.producer` & `Dockerfile.consumer`**:
    *   Dockerfiles used to build the images for the producer and consumer Python applications.
5.  **`requirements.txt`**:
    *   Lists the Python dependency (`kafka-python`) for the workers.

## Prerequisites

*   [Docker](https://docs.docker.com/get-docker/)
*   [Docker Compose](https://docs.docker.com/compose/install/) (Usually included with Docker Desktop)

## Running the Demo

1.  **Clone the repository (if you haven't already):**
    ```bash
    # git clone <repository-url>
    # cd <repository-directory>
    ```

2.  **Build and start all services:**
    This command will build the Docker images for the producer and consumer (if not already built) and start all services (Kafka, producer, consumer) in detached mode.
    ```bash
    docker-compose up --build -d
    ```

3.  **View Logs:**

    *   **To see the logs of all services:**
        ```bash
        docker-compose logs -f
        ```
    *   **To follow logs for a specific service (e.g., producer):**
        ```bash
        docker-compose logs -f producer
        ```
    *   **For the consumer:**
        ```bash
        docker-compose logs -f consumer
        ```
    *   **For Kafka:**
        ```bash
        docker-compose logs -f kafka
        ```
    You should see the producer sending messages and the consumer receiving them and sending responses.

4.  **Inspect Kafka Topics (Optional):**

    You can inspect the messages flowing through Kafka topics directly using Kafka's command-line tools.

    *   **Open a new terminal window.**
    *   **To view messages in `incoming-messages`:**
        ```bash
        docker-compose exec kafka kafka-console-consumer.sh           --bootstrap-server kafka:9092           --topic incoming-messages           --from-beginning
        ```
    *   **To view messages in `outgoing-messages`:**
        ```bash
        docker-compose exec kafka kafka-console-consumer.sh           --bootstrap-server kafka:9092           --topic outgoing-messages           --from-beginning
        ```
    Press `Ctrl+C` in the terminal to stop watching the topic.

5.  **Stopping the Demo:**
    To stop and remove all the containers, networks, and volumes defined in `docker-compose.yml`:
    ```bash
    docker-compose down
    ```
    If you want to remove the Kafka data volume as well (all messages will be lost), use:
    ```bash
    docker-compose down -v
    ```

## Project Structure
```
.
├── docker-compose.yml     # Docker Compose setup for Kafka, producer, and consumer
├── Dockerfile.consumer    # Dockerfile for the consumer application
├── Dockerfile.producer    # Dockerfile for the producer application
├── producer.py            # Python script for Worker 1 (message generation)
├── consumer.py            # Python script for Worker 2 (message processing and response)
├── requirements.txt       # Python dependencies
└── README.md              # This file
```
