import json
import time
import uuid
from datetime import datetime
from kafka import KafkaProducer
from kafka.errors import NoBrokersAvailable


def create_producer(max_retries: int = 10, delay: int = 5) -> KafkaProducer:
    """Create a Kafka producer with simple retry logic."""
    attempt = 0
    while True:
        try:
            return KafkaProducer(
                bootstrap_servers="kafka:9092",
                value_serializer=lambda v: json.dumps(v).encode("utf-8"),
            )
        except NoBrokersAvailable:
            attempt += 1
            if attempt >= max_retries:
                raise
            print(f"Kafka broker not available, retrying in {delay}s ({attempt}/{max_retries})")
            time.sleep(delay)

def main() -> None:
    producer = create_producer()

    while True:
        message = {
            "id": str(uuid.uuid4()),
            "from": "customer@example.com",
            "to": "support@example.com",
            "subject": "Order issue",
            "body": "My order was wrong, please fix it.",
            "timestamp": datetime.utcnow().isoformat(),
        }
        producer.send("incoming-messages", message)
        producer.flush()
        print("Produced message", message)
        time.sleep(1)


if __name__ == "__main__":
    main()

