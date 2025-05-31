import json
import time
import uuid
import random
from kafka import KafkaProducer
from kafka.errors import KafkaError
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Kafka Configuration
KAFKA_BROKER = 'kafka:9092' # Assumes running within docker-compose network
TOPIC_NAME = 'incoming-messages'

# Dummy message templates
SUBJECTS = [
    "Order Issue: Wrong Items",
    "Food Quality Complaint: Cold Food",
    "Delivery Problem: Late Arrival",
    "Billing Inquiry: Overcharged",
    "App Feature Request: Easier Reordering"
]
BODIES = [
    "I received my food but it was the wrong order. I ordered burgers, not hot dogs. Please send me the right order or give me my money back.",
    "The food was cold when I received it. I want my money back.",
    "My delivery was over 30 minutes late. What happened?",
    "I believe I was overcharged for my last order. Can you check?",
    "It would be great if your app had a one-click reorder button for past orders."
]

def create_producer():
    """Creates and returns a KafkaProducer instance."""
    try:
        producer = KafkaProducer(
            bootstrap_servers=[KAFKA_BROKER],
            value_serializer=lambda v: json.dumps(v).encode('utf-8'),
            retries=5, # Retry up to 5 times for transient errors
            acks='all' # Wait for all in-sync replicas to acknowledge
        )
        logging.info("KafkaProducer connected successfully.")
        return producer
    except Exception as e:
        logging.error(f"Failed to connect KafkaProducer: {e}")
        return None

def generate_message():
    """Generates a dummy customer message."""
    return {
        "message_id": str(uuid.uuid4()),
        "customer_id": random.randint(1000, 9999),
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "subject": random.choice(SUBJECTS),
        "body": random.choice(BODIES)
    }

def main():
    producer = create_producer()
    if not producer:
        logging.error("Exiting due to KafkaProducer connection failure.")
        return

    logging.info(f"Starting to send messages to topic '{TOPIC_NAME}' on broker {KAFKA_BROKER}")
    try:
        while True:
            message = generate_message()
            logging.info(f"Sending message: {message['message_id']} - {message['subject']}")

            future = producer.send(TOPIC_NAME, value=message)

            # Block for 'synchronous' sends & get metadata
            try:
                record_metadata = future.get(timeout=10)
                logging.debug(f"Message sent to topic '{record_metadata.topic}' partition {record_metadata.partition} offset {record_metadata.offset}")
            except KafkaError as ke:
                logging.error(f"Failed to send message {message['message_id']}: {ke}")
            except Exception as e:
                logging.error(f"An unexpected error occurred while sending message {message['message_id']}: {e}")

            time.sleep(1)
    except KeyboardInterrupt:
        logging.info("Shutting down producer...")
    except Exception as e:
        logging.error(f"An unexpected error occurred in the main loop: {e}")
    finally:
        if producer:
            producer.flush() # Ensure all pending messages are sent
            producer.close()
            logging.info("KafkaProducer closed.")

if __name__ == "__main__":
    main()
