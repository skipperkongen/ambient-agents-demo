import os
import time
from kafka import KafkaProducer
from kafka.errors import NoBrokersAvailable
from langchain.llms import OpenAI

KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")
TOPIC = os.getenv("EMAIL_TOPIC", "incoming-emails")

def generate_email():
    """Generate a synthetic customer service email about food delivery."""
    llm = OpenAI()
    prompt = (
        "Generate a short customer complaint about a food delivery order."
        " The tone should be realistic and reference missing or wrong items."
    )
    return llm(prompt)


def get_producer():
    """Create a Kafka producer, retrying until Kafka is ready."""
    while True:
        try:
            return KafkaProducer(bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS)
        except NoBrokersAvailable:
            print("Waiting for Kafka...")
            time.sleep(5)


def main():
    producer = get_producer()
    while True:
        email = generate_email()
        producer.send(TOPIC, email.encode("utf-8"))
        print(f"Produced email: {email}")
        time.sleep(5)


if __name__ == "__main__":
    main()
