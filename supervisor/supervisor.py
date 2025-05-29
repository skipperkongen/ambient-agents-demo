import os
import requests
from kafka import KafkaConsumer, KafkaProducer
from langchain.llms import OpenAI
from langgraph.graph import Graph

KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")
IN_TOPIC = os.getenv("EMAIL_IN_TOPIC", "incoming-emails")
OUT_TOPIC = os.getenv("EMAIL_OUT_TOPIC", "outgoing-emails")
RESPONDER_URL = os.getenv("RESPONDER_URL", "http://responder:8000/respond")


def generate_response_via_mcp(email_text: str) -> str:
    """Send the email to the responder agent over MCP (HTTP) and return response."""
    payload = {"email": email_text}
    r = requests.post(RESPONDER_URL, json=payload, timeout=30)
    r.raise_for_status()
    return r.json().get("response", "")


def main():
    consumer = KafkaConsumer(
        IN_TOPIC,
        bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
        auto_offset_reset="earliest",
        group_id="supervisor",
    )
    producer = KafkaProducer(bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS)
    for msg in consumer:
        email_text = msg.value.decode("utf-8")
        print(f"Supervisor received: {email_text}")
        # Build a simple graph that delegates to the responder via MCP
        graph = Graph()
        graph.add_node("responder", lambda x: generate_response_via_mcp(x))
        response = graph.invoke(email_text)
        producer.send(OUT_TOPIC, response.encode("utf-8"))
        print(f"Supervisor responded: {response}")


if __name__ == "__main__":
    main()
