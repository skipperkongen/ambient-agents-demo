import os
import time
from kafka import KafkaProducer
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


def main():
    producer = KafkaProducer(bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS)
    while True:
        email = generate_email()
        producer.send(TOPIC, email.encode("utf-8"))
        print(f"Produced email: {email}")
        time.sleep(5)


if __name__ == "__main__":
    main()
