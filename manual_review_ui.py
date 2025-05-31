import json
import time
import uuid
import os
from flask import Flask, render_template_string, request, redirect, url_for, jsonify
from kafka import KafkaConsumer, KafkaProducer
from kafka.errors import KafkaError
import logging
import threading

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Flask App Configuration
app = Flask(__name__)
app.secret_key = os.urandom(24) # For session management, if needed later

# Kafka Configuration
KAFKA_BROKER = os.environ.get('KAFKA_BROKER', 'kafka:9092')
MANUAL_REVIEW_TOPIC = 'manual-review'
OUTGOING_TOPIC = 'outgoing-messages'
UI_CONSUMER_GROUP_ID = 'manual-review-ui-group'

# In-memory storage for messages (replace with a database in a real app)
messages_for_review = []
processed_message_ids = set() # To avoid reprocessing messages on restart / multiple workers
review_messages_lock = threading.Lock()

# --- Kafka Clients ---
def create_ui_consumer():
    try:
        consumer = KafkaConsumer(
            MANUAL_REVIEW_TOPIC,
            bootstrap_servers=[KAFKA_BROKER],
            auto_offset_reset='earliest',
            enable_auto_commit=False, # Manual commit after processing
            group_id=UI_CONSUMER_GROUP_ID,
            value_deserializer=lambda v: json.loads(v.decode('utf-8')))
        logging.info(f"UI KafkaConsumer connected and subscribed to topic '{MANUAL_REVIEW_TOPIC}'.")
        return consumer
    except Exception as e:
        logging.error(f"Failed to connect UI KafkaConsumer: {e}")
        return None

def create_ui_producer():
    try:
        producer = KafkaProducer(
            bootstrap_servers=[KAFKA_BROKER],
            value_serializer=lambda v: json.dumps(v).encode('utf-8'),
            retries=5,
            acks='all')
        logging.info("UI KafkaProducer for responses connected successfully.")
        return producer
    except Exception as e:
        logging.error(f"Failed to connect UI KafkaProducer for responses: {e}")
        return None

ui_producer = create_ui_producer()

# --- Background Kafka Consumer Thread ---
def consume_messages():
    consumer = create_ui_consumer()
    if not consumer:
        logging.error("UI consumer thread exiting: Kafka connection failed.")
        return

    logging.info("UI Kafka consumer thread started.")
    try:
        for message in consumer:
            try:
                msg_data = message.value
                msg_id = msg_data.get('message_id')

                if msg_id not in processed_message_ids:
                    logging.info(f"Received message for review: {msg_id}")
                    with review_messages_lock:
                        messages_for_review.append(msg_data)
                    # In a real app, you'd persist this and then commit.
                    # For this simple example, we commit immediately.
                    consumer.commit()
                else:
                    logging.info(f"Skipping already processed message: {msg_id}")
                    consumer.commit() # Still commit to advance offset

            except json.JSONDecodeError:
                logging.error(f"Failed to decode JSON message: {message.value}")
                consumer.commit() # Commit to skip bad message
            except Exception as e:
                logging.error(f"Error processing message in UI consumer: {e}", exc_info=True)
                # Decide if to commit or not based on error type
    except Exception as e:
        logging.error(f"UI Kafka consumer thread encountered an error: {e}", exc_info=True)
    finally:
        if consumer:
            consumer.close()
        logging.info("UI Kafka consumer thread stopped.")

# Start consumer thread
consumer_thread = threading.Thread(target=consume_messages, daemon=True)
consumer_thread.start()

# --- Flask Routes ---
HTML_TEMPLATE = '''
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1, shrink-to-fit=no">
  <title>Manual Message Review</title>
  <style>
    body { font-family: sans-serif; margin: 20px; background-color: #f4f4f4; color: #333; }
    .container { max-width: 900px; margin: auto; background-color: #fff; padding: 20px; border-radius: 8px; box-shadow: 0 0 10px rgba(0,0,0,0.1); }
    h1 { color: #333; text-align: center; }
    .message-item { border: 1px solid #ddd; padding: 15px; margin-bottom: 15px; border-radius: 5px; background-color: #f9f9f9; }
    .message-item p { margin: 5px 0; }
    .message-item strong { color: #555; }
    textarea { width: 95%; padding: 10px; margin-top: 5px; border: 1px solid #ccc; border-radius: 4px; }
    button { padding: 10px 15px; background-color: #007bff; color: white; border: none; border-radius: 4px; cursor: pointer; font-size: 16px; }
    button:hover { background-color: #0056b3; }
    .no-messages { text-align: center; color: #777; padding: 20px; }
    .form-actions { margin-top: 10px; }
    pre {
      white-space: pre-wrap; /* Respects whitespace and wraps lines */
      word-wrap: break-word;   /* Breaks long words if they would overflow */
    }
  </style>
</head>
<body>
  <div class="container">
    <h1>Messages for Manual Review</h1>
    <div id="review-messages-container">
      {% if messages %}
        {% for message in messages %}
          <div class="message-item">
            <p><strong>Message ID:</strong> {{ message.message_id }}</p>
            <p><strong>Customer ID:</strong> {{ message.customer_id }}</p>
            <p><strong>Timestamp:</strong> {{ message.timestamp }}</p>
            <p><strong>Subject:</strong> {{ message.subject }}</p>
            <p><strong>Body:</strong></p>
            <pre>{{ message.body }}</pre>
            <form method="post" action="{{ url_for('submit_response', message_id=message.message_id) }}">
              <textarea name="response_body" rows="3" placeholder="Enter your response..." required></textarea>
              <div class="form-actions">
                <button type="submit">Submit Response</button>
              </div>
            </form>
          </div>
        {% endfor %}
      {% else %}
        <p class="no-messages">No messages currently awaiting review.</p>
      {% endif %}
    </div>
  </div>
  <script>
    function fetchReviewMessages() {
      fetch("{{ url_for('get_review_messages_data') }}")
        .then(response => response.json())
        .then(data => {
          if (data.html_content) {
            document.getElementById('review-messages-container').innerHTML = data.html_content;
          }
        })
        .catch(error => console.error('Error fetching review messages:', error));
    }
    setInterval(fetchReviewMessages, 5000); // Refresh every 5 seconds
  </script>
</body>
</html>
'''

REVIEW_MESSAGES_PARTIAL_HTML = '''
{% if messages %}
  {% for message in messages %}
    <div class="message-item">
      <p><strong>Message ID:</strong> {{ message.message_id }}</p>
      <p><strong>Customer ID:</strong> {{ message.customer_id }}</p>
      <p><strong>Timestamp:</strong> {{ message.timestamp }}</p>
      <p><strong>Subject:</strong> {{ message.subject }}</p>
      <p><strong>Body:</strong></p>
      <pre>{{ message.body }}</pre>
      <form method="post" action="{{ url_for('submit_response', message_id=message.message_id) }}">
        <textarea name="response_body" rows="3" placeholder="Enter your response..." required></textarea>
        <div class="form-actions">
          <button type="submit">Submit Response</button>
        </div>
      </form>
    </div>
  {% endfor %}
{% else %}
  <p class="no-messages">No messages currently awaiting review.</p>
{% endif %}
'''

@app.route('/')
def index():
    # Display oldest messages first
    with review_messages_lock:
        current_messages = list(messages_for_review)
    return render_template_string(HTML_TEMPLATE, messages=current_messages)

@app.route('/get_review_messages_data')
def get_review_messages_data():
    with review_messages_lock:
        current_messages = list(messages_for_review)
    html_content = render_template_string(REVIEW_MESSAGES_PARTIAL_HTML, messages=current_messages)
    return jsonify(html_content=html_content)

@app.route('/submit_response/<message_id>', methods=['POST'])
def submit_response(message_id):
    response_body_text = request.form.get('response_body')
    with review_messages_lock:
        original_message = next((msg for msg in messages_for_review if msg.get('message_id') == message_id), None)

    if not ui_producer:
        logging.error("UI Producer is not available. Cannot send response.")
        # Handle error display to user if necessary
        return redirect(url_for('index')) # Or an error page

    if not original_message:
        logging.warning(f"Original message with ID {message_id} not found for response submission.")
        # Could be already processed by another worker/instance or a stale request
        return redirect(url_for('index'))

    if not response_body_text:
        logging.warning(f"Response body for message ID {message_id} is empty.")
        # Add flash message for user 'Response cannot be empty'
        return redirect(url_for('index'))

    response_data = {
        "original_message_id": original_message.get('message_id'),
        "response_id": str(uuid.uuid4()),
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "responder_type": "HUMAN",
        "body": response_body_text
    }

    try:
        future = ui_producer.send(OUTGOING_TOPIC, value=response_data)
        future.get(timeout=10) # Block for 'synchronous' send
        logging.info(f"Human response for {response_data['original_message_id']} sent to '{OUTGOING_TOPIC}'")

        # Remove from review list and add to processed_message_ids
        with review_messages_lock:
            messages_for_review[:] = [msg for msg in messages_for_review if msg.get('message_id') != message_id]
            processed_message_ids.add(message_id)

    except KafkaError as ke:
        logging.error(f"Failed to send human response for {response_data['original_message_id']}: {ke}")
        # Add flash message for user: "Failed to send response. Please try again."
    except Exception as e:
        logging.error(f"An unexpected error occurred while sending human response for {response_data['original_message_id']}: {e}")
        # Add flash message for user: "An error occurred. Please try again."

    return redirect(url_for('index'))

if __name__ == '__main__':
    # Make sure KAFKA_BROKER is available if running outside Docker with a different hostname
    logging.info(f"Starting Flask app for manual review. Kafka Broker: {KAFKA_BROKER}")
    app.run(host='0.0.0.0', port=5001, debug=False) # Changed port to 5001
