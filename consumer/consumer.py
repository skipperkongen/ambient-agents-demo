import json
from kafka import KafkaConsumer, KafkaProducer
from datetime import datetime
import uuid

def main() -> None:
    consumer = KafkaConsumer(
        "incoming-messages",
        bootstrap_servers="kafka:9092",
        value_deserializer=lambda v: json.loads(v.decode("utf-8")),
        auto_offset_reset="earliest",
        enable_auto_commit=True,
    )

    producer = KafkaProducer(
        bootstrap_servers="kafka:9092",
        value_serializer=lambda v: json.dumps(v).encode("utf-8"),
    )

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

