import json
import time
import uuid
from datetime import datetime
from kafka import KafkaProducer

def main() -> None:
    producer = KafkaProducer(
        bootstrap_servers="kafka:9092",
        value_serializer=lambda v: json.dumps(v).encode("utf-8"),
    )

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

