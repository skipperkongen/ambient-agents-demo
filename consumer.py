import json
import time
import uuid
import random # Added import
from kafka import KafkaConsumer, KafkaProducer
from kafka.errors import KafkaError
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Kafka Configuration
KAFKA_BROKER = 'kafka:9092'
INCOMING_TOPIC = 'incoming-messages'
OUTGOING_TOPIC = 'outgoing-messages'
MANUAL_REVIEW_TOPIC = 'manual-review' # Added new topic
CONSUMER_GROUP_ID = 'customer-service-group'

# Response templates
AI_RESPONSES = {
    "wrong order": "We are very sorry about the mix-up with your order. A replacement is being prepared and will be sent to you right away.",
    "cold food": "We apologize that your food arrived cold. This is not the experience we want you to have.",
    "late arrival": "We sincerely apologize for the delay in your delivery. We are looking into what caused this.",
    "overcharged": "Thank you for bringing this to our attention. We are reviewing your billing details now.",
    "feature request": "Thank you for your suggestion! We've passed it along to our development team for consideration.",
    "default": "Thank you for reaching out. We have received your message and will process it shortly."
}

HUMAN_ESCALATION_MESSAGE = "I have handled your case over to my human colleague who will review your case, as it requires further attention (e.g., monetary compensation)."

def create_consumer():
    """Creates and returns a KafkaConsumer instance."""
    try:
        consumer = KafkaConsumer(
            INCOMING_TOPIC,
            bootstrap_servers=[KAFKA_BROKER],
            auto_offset_reset='earliest',
            enable_auto_commit=True,
            group_id=CONSUMER_GROUP_ID,
            value_deserializer=lambda v: json.loads(v.decode('utf-8')))
        logging.info(f"KafkaConsumer connected and subscribed to topic '{INCOMING_TOPIC}'.")
        return consumer
    except Exception as e:
        logging.error(f"Failed to connect KafkaConsumer: {e}")
        return None

def create_producer():
    """Creates and returns a KafkaProducer instance for sending responses/forwarding messages."""
    try:
        producer = KafkaProducer(
            bootstrap_servers=[KAFKA_BROKER],
            value_serializer=lambda v: json.dumps(v).encode('utf-8'),
            retries=5,
            acks='all')
        logging.info("KafkaProducer for responses/forwarding connected successfully.")
        return producer
    except Exception as e:
        logging.error(f"Failed to connect KafkaProducer: {e}")
        return None

def generate_ai_response(incoming_message): # Renamed for clarity
    """Generates an AI response based on the incoming message."""
    original_body = incoming_message.get('body', '').lower()
    original_subject = incoming_message.get('subject', '').lower()

    responder_type = "AI"
    response_body = AI_RESPONSES["default"]

    if "money back" in original_body or "refund" in original_body:
        responder_type = "AI_ESCALATION_TO_HUMAN"
        response_body = HUMAN_ESCALATION_MESSAGE
    elif "wrong order" in original_subject or "wrong items" in original_subject:
        response_body = AI_RESPONSES["wrong order"]
    elif "cold food" in original_subject:
        response_body = AI_RESPONSES["cold food"]
        if "money back" in original_body or "refund" in original_body:
             responder_type = "AI_ESCALATION_TO_HUMAN"
             response_body = HUMAN_ESCALATION_MESSAGE
    elif "late arrival" in original_subject:
        response_body = AI_RESPONSES["late arrival"]
    elif "overcharged" in original_subject:
        response_body = AI_RESPONSES["overcharged"]
    elif "feature request" in original_subject:
        response_body = AI_RESPONSES["feature request"]

    return {
        "original_message_id": incoming_message.get('message_id'),
        "response_id": str(uuid.uuid4()),
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "responder_type": responder_type,
        "body": response_body
    }

def main():
    consumer = create_consumer()
    producer = create_producer() # This producer will be used for both topics

    if not consumer or not producer:
        logging.error("Exiting due to Kafka connection failure.")
        if consumer: consumer.close()
        if producer: producer.close()
        return

    logging.info(f"Starting to consume messages from '{INCOMING_TOPIC}'. Will distribute to AI response or manual review.")
    try:
        for message in consumer:
            try:
                incoming_data = message.value
                msg_id = incoming_data.get('message_id', 'UnknownID')
                logging.info(f"Received message: {msg_id} - {incoming_data.get('subject')}")

                # 50/50 split logic
                if random.random() < 0.5:
                    # Forward to manual review
                    logging.info(f"Forwarding message {msg_id} to '{MANUAL_REVIEW_TOPIC}'.")
                    future = producer.send(MANUAL_REVIEW_TOPIC, value=incoming_data)
                    try:
                        record_metadata = future.get(timeout=10)
                        logging.debug(f"Message {msg_id} forwarded to topic '{record_metadata.topic}' partition {record_metadata.partition} offset {record_metadata.offset}")
                    except KafkaError as ke:
                        logging.error(f"Failed to forward message {msg_id} to '{MANUAL_REVIEW_TOPIC}': {ke}")
                    except Exception as e:
                        logging.error(f"Unexpected error forwarding message {msg_id} to '{MANUAL_REVIEW_TOPIC}': {e}")
                else:
                    # Process with AI and send to outgoing
                    logging.info(f"Processing message {msg_id} with AI.")
                    ai_response_data = generate_ai_response(incoming_data)
                    logging.info(f"Sending AI response for {ai_response_data['original_message_id']} by {ai_response_data['responder_type']} to '{OUTGOING_TOPIC}'.")

                    future = producer.send(OUTGOING_TOPIC, value=ai_response_data)
                    try:
                        record_metadata = future.get(timeout=10)
                        logging.debug(f"AI Response for {msg_id} sent to topic '{record_metadata.topic}' partition {record_metadata.partition} offset {record_metadata.offset}")
                    except KafkaError as ke:
                        logging.error(f"Failed to send AI response for {msg_id} to '{OUTGOING_TOPIC}': {ke}")
                    except Exception as e:
                        logging.error(f"Unexpected error sending AI response for {msg_id} to '{OUTGOING_TOPIC}': {e}")

            except json.JSONDecodeError:
                logging.error(f"Failed to decode JSON message: {message.value}")
            except Exception as e:
                logging.error(f"Error processing message: {e}", exc_info=True)

    except KeyboardInterrupt:
        logging.info("Shutting down consumer and producer...")
    except Exception as e:
        logging.error(f"An unexpected error occurred in the main consumer loop: {e}", exc_info=True)
    finally:
        if consumer:
            consumer.close()
            logging.info("KafkaConsumer closed.")
        if producer:
            producer.flush()
            producer.close()
            logging.info("KafkaProducer (for responses/forwarding) closed.")

if __name__ == "__main__":
    main()
