import json
import time
from kafka import KafkaConsumer, KafkaProducer
from kafka.errors import NoBrokersAvailable
from datetime import datetime
import uuid


def create_consumer(max_retries: int = 10, delay: int = 5) -> KafkaConsumer:
    """Create a Kafka consumer with retry logic."""
    attempt = 0
    while True:
        try:
            return KafkaConsumer(
                "incoming-messages",
                bootstrap_servers="kafka:9092",
                value_deserializer=lambda v: json.loads(v.decode("utf-8")),
                auto_offset_reset="earliest",
                enable_auto_commit=True,
            )
        except NoBrokersAvailable:
            attempt += 1
            if attempt >= max_retries:
                raise
            print(f"Kafka broker not available, retrying in {delay}s ({attempt}/{max_retries})")
            time.sleep(delay)


def create_producer(max_retries: int = 10, delay: int = 5) -> KafkaProducer:
    """Create a Kafka producer with retry logic."""
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
    consumer = create_consumer()
    producer = create_producer()

    for msg in consumer:
        incoming = msg.value
        print("Received", incoming)
        response = {
            "id": str(uuid.uuid4()),
            "from": incoming.get("to", "support@example.com"),
            "to": incoming.get("from", "customer@example.com"),
            "subject": f"Re: {incoming.get('subject', '')}",
            "body": "Thank you for contacting us. We will look into your issue.",
            "timestamp": datetime.utcnow().isoformat(),
        }
        producer.send("outgoing-messages", response)
        producer.flush()
        print("Sent response", response)


if __name__ == "__main__":
    main()

