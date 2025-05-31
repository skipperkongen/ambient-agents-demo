# AI-Powered Customer Service Demo with Kafka

This project demonstrates an AI-enhanced customer service workflow for a food delivery company using Apache Kafka. Customer messages are submitted via a web interface (`Email Client UI`), sent to an `incoming-messages` Kafka topic, and then processed by a `Consumer` service. Based on the message content, the consumer may generate an AI response sent to an `outgoing-messages` topic (viewable in the Email Client UI) or forward the message to a `manual-review` topic for human agent processing via a separate `Manual Review UI`.

## Components

1.  **`docker-compose.yml`**:
    *   Sets up a single-node Kafka broker running in KRaft mode (without Zookeeper).
    *   Defines a `kafka-setup` service that automatically creates three topics: `incoming-messages`, `outgoing-messages`, and `manual-review`.
    *   Defines services for `email_client_ui`, `manual_review_ui`, and a `consumer` application, built using Docker.
2.  **`email_client_ui.py`**:
    *   A Python Streamlit web application that simulates a customer email interface.
    *   Allows users to manually compose and send messages.
    *   Publishes these messages to the `incoming-messages` Kafka topic.
    *   Displays responses/messages from the `outgoing-messages` Kafka topic.
    *   This application is containerized (see `Dockerfile.email_client_ui`) and managed by `docker-compose`.
3.  **`manual_review_ui.py`**:
    *   A Python Streamlit web application that simulates an interface for human customer service agents.
    *   Consumes messages from the `manual-review` Kafka topic.
    *   Allows agents to view message details and compose/send a response.
    *   Publishes responses to the `outgoing-messages` Kafka topic (which are then displayed in the Email Client UI).
    *   This application is containerized (see `Dockerfile.manual_review_ui`) and managed by `docker-compose`.
4.  **`consumer.py`**:
    *   A Python script that simulates an AI agent processing customer messages.
    *   Consumes messages from the `incoming-messages` topic.
    *   Based on message content (e.g., presence of keywords like "refund", "complaint"), it either:
        *   Generates a dummy AI response and publishes it to the `outgoing-messages` Kafka topic.
        *   Forwards the original message to the `manual-review` Kafka topic for human agent processing.
    *   This script is containerized (see `Dockerfile.consumer`) and managed by `docker-compose`.
5.  **`Dockerfile.email_client_ui`, `Dockerfile.manual_review_ui`, `Dockerfile.consumer`**:
    *   Individual Dockerfiles used to build the images for the Email Client UI, Manual Review UI, and Consumer Python applications, respectively.
6.  **`requirements.txt`**:
    *   Lists the Python dependencies (e.g., `kafka-python`, `streamlit`) for the applications.

## Prerequisites

*   [Docker](https://docs.docker.com/get-docker/)
*   [Docker Compose](https://docs.docker.com/compose/install/) (Usually included with Docker Desktop)

## Running the Demo

1.  **Clone the repository (if you haven't already):**
    ```bash
    git clone <repository-url>
    cd <repository-directory>
    ```

2.  **Build and start all services:**
    This command will build the Docker images for the UIs and consumer (if not already built) and start all services (Kafka, UIs, consumer) in detached mode.
    ```bash
    docker-compose up --build -d
    ```

3.  **View Logs:**

    *   **To see the logs of all services:**
        ```bash
        docker-compose logs -f
        ```
    *   **To follow logs for a specific service:**
        ```bash
        docker-compose logs -f email_client_ui
        docker-compose logs -f manual_review_ui
        docker-compose logs -f consumer
        docker-compose logs -f kafka
        ```

4.  **Accessing Web UIs:**

    *   **Email Client UI**: Used to send new customer messages and view AI/agent responses.
        *   Access it at: `http://localhost:5002`
    *   **Manual Review UI**: Used by human agents to process messages escalated for manual review.
        *   Access it at: `http://localhost:5001`

5.  **Inspect Kafka Topics (Optional):**

    You can inspect the messages flowing through Kafka topics directly using Kafka's command-line tools.

    *   **Open a new terminal window.**
    *   **To view messages in `incoming-messages`:**
        ```bash
        docker-compose exec kafka kafka-console-consumer.sh           --bootstrap-server kafka:9092           --topic incoming-messages           --from-beginning
        ```
    *   **To view messages in `manual-review`:**
        ```bash
        docker-compose exec kafka kafka-console-consumer.sh           --bootstrap-server kafka:9092           --topic manual-review           --from-beginning
        ```
    *   **To view messages in `outgoing-messages`:**
        ```bash
        docker-compose exec kafka kafka-console-consumer.sh           --bootstrap-server kafka:9092           --topic outgoing-messages           --from-beginning
        ```
    Press `Ctrl+C` in the terminal to stop watching the topic.

6.  **Stopping the Demo:**
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
├── docker-compose.yml              # Defines and configures all services (Kafka, UIs, consumer)
├── Dockerfile.consumer             # Dockerfile for the consumer application
├── Dockerfile.email_client_ui      # Dockerfile for the Email Client UI application
├── Dockerfile.manual_review_ui     # Dockerfile for the Manual Review UI application
├── consumer.py                     # Python script for message processing and AI response/escalation
├── email_client_ui.py              # Python script for the Email Client UI (message submission and viewing)
├── manual_review_ui.py             # Python script for the Manual Review UI (agent processing)
├── requirements.txt                # Python dependencies for all applications
└── README.md                       # This file
```
