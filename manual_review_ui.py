import json
import time
import uuid
import threading
from flask import Flask, render_template_string, request, redirect, url_for
from kafka import KafkaConsumer, KafkaProducer
from kafka.errors import KafkaError
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Flask App Configuration
app = Flask(__name__)

# Kafka Configuration
KAFKA_BROKER = 'kafka:9092'
MANUAL_REVIEW_TOPIC = 'manual-review'
OUTGOING_TOPIC = 'outgoing-messages'
UI_CONSUMER_GROUP_ID = 'manual-review-ui-group'

# In-memory store for messages awaiting review
# Each item will be a dictionary (the message from Kafka)
REVIEW_MESSAGES = []
# Lock for thread-safe access to REVIEW_MESSAGES
review_messages_lock = threading.Lock()

# Global Kafka producer for the UI to send responses
ui_kafka_producer = None

# HTML Template for the main page
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Manual Review Queue</title>
    <style>
        body { font-family: sans-serif; margin: 20px; background-color: #f4f4f4; color: #333; }
        .container { background-color: #fff; padding: 20px; border-radius: 8px; box-shadow: 0 0 10px rgba(0,0,0,0.1); }
        h1 { color: #555; }
        .message-item { border: 1px solid #ddd; padding: 15px; margin-bottom: 15px; border-radius: 5px; background-color: #f9f9f9; }
        .message-details { margin-bottom: 10px; }
        .message-details p { margin: 5px 0; }
        .message-details strong { color: #444; }
        textarea { width: 95%; padding: 10px; margin-bottom: 10px; border: 1px solid #ccc; border-radius: 4px; }
        button { padding: 10px 15px; background-color: #5cb85c; color: white; border: none; border-radius: 4px; cursor: pointer; }
        button:hover { background-color: #4cae4c; }
        .no-messages { color: #777; }
    </style>
</head>
<body>
    <div class="container">
        <h1>Messages Awaiting Manual Review</h1>
        {% if messages %}
            {% for message in messages %}
                <div class="message-item">
                    <div class="message-details">
                        <p><strong>Message ID:</strong> {{ message.message_id }}</p>
                        <p><strong>Customer ID:</strong> {{ message.customer_id }}</p>
                        <p><strong>Timestamp:</strong> {{ message.timestamp }}</p>
                        <p><strong>Subject:</strong> {{ message.subject }}</p>
                        <p><strong>Body:</strong></p>
                        <p>{{ message.body }}</p>
                    </div>
                    <form action="{{ url_for('submit_response') }}" method="post">
                        <input type="hidden" name="original_message_id" value="{{ message.message_id }}">
                        <textarea name="human_response_text" rows="3" placeholder="Type your response here..." required></textarea>
                        <button type="submit">Submit Response</button>
                    </form>
                </div>
            {% endfor %}
        {% else %}
            <p class="no-messages">No messages currently in the manual review queue.</p>
        {% endif %}
    </div>
</body>
</html>
'''

def kafka_consumer_thread():
    """Thread function to consume messages from 'manual-review' topic."""
    consumer = None
    try:
        consumer = KafkaConsumer(
            MANUAL_REVIEW_TOPIC,
            bootstrap_servers=[KAFKA_BROKER],
            auto_offset_reset='earliest',
            group_id=UI_CONSUMER_GROUP_ID,
            value_deserializer=lambda v: json.loads(v.decode('utf-8')),
            consumer_timeout_ms=1000 # Timeout to allow thread to check running flag
        )
        logging.info(f"UI KafkaConsumer connected to '{MANUAL_REVIEW_TOPIC}'.")

        while True: # Continuously poll for messages
            for message in consumer:
                if message and message.value:
                    logging.info(f"UI received message for review: {message.value.get('message_id')}")
                    with review_messages_lock:
                        # Avoid duplicates if consumer restarts and re-reads if not committed
                        if not any(m['message_id'] == message.value.get('message_id') for m in REVIEW_MESSAGES):
                            REVIEW_MESSAGES.append(message.value)
            time.sleep(0.1) # Small sleep to prevent tight loop when no messages

    except Exception as e:
        logging.error(f"Error in UI Kafka consumer thread: {e}", exc_info=True)
    finally:
        if consumer:
            consumer.close()
            logging.info("UI KafkaConsumer closed.")

@app.route('/')
def index():
    with review_messages_lock:
        # Pass a copy to avoid issues if modified during render
        messages_to_display = list(REVIEW_MESSAGES)
    return render_template_string(HTML_TEMPLATE, messages=messages_to_display)

@app.route('/submit-response', methods=['POST'])
def submit_response():
    global ui_kafka_producer
    original_message_id = request.form.get('original_message_id')
    human_response_text = request.form.get('human_response_text')

    if not original_message_id or not human_response_text:
        logging.warning("Attempted to submit response with missing data.")
        return "Missing data", 400

    response_payload = {
        "original_message_id": original_message_id,
        "response_id": str(uuid.uuid4()),
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "responder_type": "HUMAN",
        "body": human_response_text
    }

    try:
        if not ui_kafka_producer:
            logging.error("UI KafkaProducer not initialized.")
            return "Error sending response (Producer not ready)", 500

        future = ui_kafka_producer.send(OUTGOING_TOPIC, value=response_payload)
        future.get(timeout=10) # Wait for send confirmation
        logging.info(f"Human response for {original_message_id} sent to '{OUTGOING_TOPIC}'.")

        # Remove from review queue
        with review_messages_lock:
            REVIEW_MESSAGES[:] = [msg for msg in REVIEW_MESSAGES if msg.get('message_id') != original_message_id]

        return redirect(url_for('index'))

    except KafkaError as ke:
        logging.error(f"Kafka error sending human response for {original_message_id}: {ke}")
        return f"Failed to send response due to Kafka error: {ke}", 500
    except Exception as e:
        logging.error(f"Error submitting human response for {original_message_id}: {e}", exc_info=True)
        return f"An unexpected error occurred: {e}", 500

def init_kafka_producer():
    global ui_kafka_producer
    try:
        ui_kafka_producer = KafkaProducer(
            bootstrap_servers=[KAFKA_BROKER],
            value_serializer=lambda v: json.dumps(v).encode('utf-8'),
            retries=5,
            acks='all'
        )
        logging.info("UI KafkaProducer initialized successfully.")
    except Exception as e:
        logging.error(f"Failed to initialize UI KafkaProducer: {e}", exc_info=True)
        # The app might still run but sending responses will fail.
        # Consider how to handle this in a real app (e.g. retry mechanism, health check)

if __name__ == '__main__':
    init_kafka_producer() # Initialize the producer once when the app starts

    # Start Kafka consumer in a background thread
    # Set daemon=True so it exits when the main thread exits
    consumer_thread = threading.Thread(target=kafka_consumer_thread, daemon=True)
    consumer_thread.start()

    # Start Flask development server
    # Port 5001 as specified in docker-compose.yml
    app.run(host='0.0.0.0', port=5001, debug=False)

    # Cleanup (mainly for standalone runs, Docker handles container shutdown)
    if ui_kafka_producer:
        ui_kafka_producer.close()
        logging.info("UI KafkaProducer closed on exit.")
