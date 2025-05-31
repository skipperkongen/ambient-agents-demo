# email_client_ui.py
import json
import time
import uuid
import os
import random
from flask import Flask, render_template_string, request, redirect, url_for, jsonify
from kafka import KafkaConsumer, KafkaProducer
from kafka.errors import KafkaError
import logging
import threading

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Flask App Configuration
app = Flask(__name__)
app.secret_key = os.urandom(24)

# Kafka Configuration
KAFKA_BROKER = os.environ.get('KAFKA_BROKER', 'kafka:9092')
INCOMING_TOPIC = 'incoming-messages'
OUTGOING_TOPIC = 'outgoing-messages' # Topic to receive messages from
UI_CONSUMER_GROUP_ID = 'email-client-ui-group-' + str(uuid.uuid4()) # Unique group id

# In-memory storage for received messages (list to maintain order)
received_messages = []
# Lock for thread-safe operations on received_messages
messages_lock = threading.Lock()

# Message templates
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
MESSAGE_TEMPLATES = [{"subject": s, "body": b} for s, b in zip(SUBJECTS, BODIES)]

# --- Kafka Clients ---
def create_producer():
    try:
        producer = KafkaProducer(
            bootstrap_servers=[KAFKA_BROKER],
            value_serializer=lambda v: json.dumps(v).encode('utf-8'),
            retries=5, acks='all'
        )
        logging.info(f"EmailClientUI: KafkaProducer connected to {KAFKA_BROKER}.")
        return producer
    except Exception as e:
        logging.error(f"EmailClientUI: Failed to connect KafkaProducer: {e}")
        return None

app_producer = create_producer()

def create_consumer():
    try:
        consumer = KafkaConsumer(
            OUTGOING_TOPIC,
            bootstrap_servers=[KAFKA_BROKER],
            auto_offset_reset='latest', # Process new messages
            enable_auto_commit=True,
            group_id=UI_CONSUMER_GROUP_ID, # Unique consumer group
            value_deserializer=lambda v: json.loads(v.decode('utf-8'))
        )
        logging.info(f"EmailClientUI: KafkaConsumer subscribed to '{OUTGOING_TOPIC}'.")
        return consumer
    except Exception as e:
        logging.error(f"EmailClientUI: Failed to connect KafkaConsumer for '{OUTGOING_TOPIC}': {e}")
        return None

# --- Background Kafka Consumer Thread ---
def consume_outgoing_messages():
    consumer = create_consumer()
    if not consumer:
        logging.error("EmailClientUI: Consumer thread exiting: Kafka connection failed.")
        return

    logging.info("EmailClientUI: Consumer thread for outgoing messages started.")
    try:
        for message in consumer:
            try:
                msg_data = message.value
                logging.info(f"EmailClientUI: Received from '{OUTGOING_TOPIC}': {msg_data.get('response_id') or msg_data.get('message_id')}")
                with messages_lock:
                    received_messages.insert(0, msg_data) # Add to front (newest first)
                    if len(received_messages) > 50: # Keep list size manageable
                        received_messages.pop()
            except json.JSONDecodeError:
                logging.error(f"EmailClientUI: JSON decode error from '{OUTGOING_TOPIC}': {message.value}")
            except Exception as e:
                logging.error(f"EmailClientUI: Error processing message from '{OUTGOING_TOPIC}': {e}", exc_info=True)
    except Exception as e:
        logging.error(f"EmailClientUI: Consumer thread for '{OUTGOING_TOPIC}' error: {e}", exc_info=True)
    finally:
        if consumer:
            consumer.close()
        logging.info("EmailClientUI: Consumer thread for outgoing messages stopped.")

outgoing_consumer_thread = threading.Thread(target=consume_outgoing_messages, daemon=True)

# Start consumer thread logic (Werkzeug safe)
def start_consumer_thread_if_needed():
    if not outgoing_consumer_thread.is_alive():
        # Start only in the main Werkzeug process or if not in debug mode
        if not app.debug or os.environ.get('WERKZEUG_RUN_MAIN') == 'true':
            logging.info("EmailClientUI: Starting outgoing consumer thread.")
            outgoing_consumer_thread.start()

# --- Flask Routes ---
# Using the more comprehensive HTML structure that previously caused issues.
# If this fails, the problem is almost certainly in this HTML/CSS.
HTML_LAYOUT = """
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1, shrink-to-fit=no">
  <title>Email Client Simulator</title>
  <style>
    body { font-family: Arial, sans-serif; margin: 0; padding: 0; background-color: #f0f2f5; display: flex; justify-content: center; align-items: flex-start; min-height: 100vh; padding-top: 20px;}
    .container { width: 90%; max-width: 1200px; background-color: #fff; box-shadow: 0 0 15px rgba(0,0,0,0.1); border-radius: 8px; display: flex; }
    .sidebar { width: 400px; background-color: #f8f9fa; padding: 20px; border-right: 1px solid #dee2e6; height: calc(100vh - 40px); overflow-y: auto; }
    .main-content { flex-grow: 1; padding: 20px; height: calc(100vh - 40px); overflow-y: auto; }
    h1, h2 { color: #333; }
    h1 { text-align: center; margin-bottom: 20px; font-size: 1.8em; }
    h2 { font-size: 1.4em; margin-top: 0; border-bottom: 1px solid #eee; padding-bottom: 10px; margin-bottom: 15px;}
    label { display: block; margin-bottom: 8px; font-weight: bold; color: #555; }
    select, textarea { width: 100%; padding: 10px; margin-bottom: 15px; border: 1px solid #ccc; border-radius: 4px; box-sizing: border-box; font-size: 0.95em; }
    button { display: block; width: 100%; padding: 12px 18px; background-color: #007bff; color: white; border: none; border-radius: 4px; cursor: pointer; font-size: 1em; margin-top:10px;}
    button:hover { background-color: #0056b3; }
    .message-list { list-style: none; padding: 0; }
    .message-item { background-color: #e9ecef; border: 1px solid #ced4da; padding: 15px; margin-bottom: 10px; border-radius: 5px; }
    .message-item p { margin: 5px 0; word-wrap: break-word; }
    .message-item strong { color: #495057; }
    .message-item pre { white-space: pre-wrap; word-wrap: break-word; background-color: #fff; padding: 10px; border-radius: 4px; border: 1px solid #ddd; font-size: 0.9em;}
    .no-messages { text-align: center; color: #777; padding: 20px; font-style: italic; }
    .selected-message-preview { margin-top: 10px; margin-bottom:20px; padding: 10px; background-color: #e9f7fd; border: 1px solid #bce8f1; border-radius: 4px; }
    .selected-message-preview h3 { margin-top: 0; font-size: 1.1em; color: #31708f; margin-bottom:5px; }
  </style>
</head>
<body>
  <div class="container">
    <div class="sidebar">
      <h2>Send New Message</h2>
      <form method="post" action="{{ url_for('send_message_route') }}" id="send-message-form">
        <label for="message_template_index">Select a message template:</label>
        <select name="message_template_index" id="message_template_index">
          {% for template in templates %}
            <option value="{{ loop.index0 }}">{{ loop.index0 + 1 }}. {{ template.subject }}</option>
          {% endfor %}
        </select>
        <div id="selected-message-preview" class="selected-message-preview">
            <h3>Preview:</h3>
            <p><strong>Subject:</strong> <span id="preview-subject"></span></p>
            <p><strong>Body:</strong></p>
            <pre id="preview-body"></pre>
        </div>
        <button type="submit">Send Message</button>
      </form>
    </div>
    <div class="main-content">
      <h2>Received Messages (from {{ outgoing_topic_name }})</h2>
      <div id="received-messages-container">
        {% if received_messages_list %}
          <ul class="message-list">
            {% for msg in received_messages_list %}
              <li class="message-item">
                <p><strong>Response ID:</strong> {{ msg.response_id or 'N/A' }}</p>
                <p><strong>Original Msg ID:</strong> {{ msg.original_message_id or 'N/A' }}</p>
                <p><strong>Timestamp:</strong> {{ msg.timestamp }}</p>
                <p><strong>Responder:</strong> {{ msg.responder_type }}</p>
                <p><strong>Body:</strong></p>
                <pre>{{ msg.body }}</pre>
              </li>
            {% endfor %}
          </ul>
        {% else %}
          <p class="no-messages">No messages received yet.</p>
        {% endif %}
      </div>
    </div>
  </div>
  <script>
    const templates = {{ templates_json|safe }};
    const selectElement = document.getElementById('message_template_index');
    const previewSubject = document.getElementById('preview-subject');
    const previewBody = document.getElementById('preview-body');

    function updatePreview() {
        const selectedIndex = selectElement.value;
        if (templates[selectedIndex]) {
            previewSubject.textContent = templates[selectedIndex].subject;
            previewBody.textContent = templates[selectedIndex].body;
        } else {
            previewSubject.textContent = "";
            previewBody.textContent = "";
        }
    }
    selectElement.addEventListener('change', updatePreview);
    // Initial preview update on page load
    if (selectElement.options.length > 0) { // Check if there are options before setting
        updatePreview();
    } else {
        previewSubject.textContent = "N/A";
        previewBody.textContent = "No templates loaded.";
    }

    // Auto-refresh received messages section every 5 seconds
    // This is a simple polling mechanism. For production, WebSockets or Server-Sent Events are better.
    setInterval(function() {
        fetch("{{ url_for('get_received_messages_data') }}")
            .then(response => response.json())
            .then(data => {
                const container = document.getElementById('received-messages-container');
                if (data.html_content) {
                    container.innerHTML = data.html_content;
                }
            });
    }, 5000);
  </script>
</body>
</html>
"""

# This is the part that will be used by the polling JS if enabled
RECEIVED_MESSAGES_PARTIAL_HTML = """
{% if received_messages_list %}
  <ul class="message-list">
    {% for msg in received_messages_list %}
      <li class="message-item">
        <p><strong>Response ID:</strong> {{ msg.response_id or 'N/A' }}</p>
        <p><strong>Original Msg ID:</strong> {{ msg.original_message_id or 'N/A' }}</p>
        <p><strong>Timestamp:</strong> {{ msg.timestamp }}</p>
        <p><strong>Responder:</strong> {{ msg.responder_type }}</p>
        <p><strong>Body:</strong></p>
        <pre>{{ msg.body }}</pre>
      </li>
    {% endfor %}
  </ul>
{% else %}
  <p class="no-messages">No messages received yet.</p>
{% endif %}
"""

@app.route('/')
def home_route():
    start_consumer_thread_if_needed() # Ensure consumer is running
    with messages_lock:
        # Pass a copy of the messages to avoid issues if the list is modified while rendering
        current_messages = list(received_messages)
    return render_template_string(HTML_LAYOUT,
                                  templates=MESSAGE_TEMPLATES,
                                  templates_json=json.dumps(MESSAGE_TEMPLATES),
                                  received_messages_list=current_messages,
                                  outgoing_topic_name=OUTGOING_TOPIC)

# Optional: Route for AJAX polling if you uncomment the JavaScript
@app.route('/get_received_messages')
def get_received_messages_data():
    with messages_lock:
        current_messages = list(received_messages)
    html_content = render_template_string(RECEIVED_MESSAGES_PARTIAL_HTML, received_messages_list=current_messages)
    return jsonify(html_content=html_content)

@app.route('/send', methods=['POST'])
def send_message_route():
    if not app_producer:
        logging.error("EmailClientUI: Kafka producer is not available.")
        return redirect(url_for('home_route'))

    template_index_str = request.form.get('message_template_index')
    try:
        template_index = int(template_index_str)
        selected_template = MESSAGE_TEMPLATES[template_index]
        message_payload = {
            "message_id": str(uuid.uuid4()),
            "customer_id": random.randint(1000, 9999),
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "subject": selected_template["subject"],
            "body": selected_template["body"]
        }
        future = app_producer.send(INCOMING_TOPIC, value=message_payload)
        future.get(timeout=10) # Wait for send confirmation
        logging.info(f"EmailClientUI: Message {message_payload['message_id']} sent to '{INCOMING_TOPIC}'.")
    except (ValueError, IndexError) as e:
        logging.warning(f"EmailClientUI: Invalid template index: {template_index_str}. Error: {e}")
    except KafkaError as ke:
        logging.error(f"EmailClientUI: Kafka send error: {ke}")
    except Exception as e:
        logging.error(f"EmailClientUI: Error sending message: {e}", exc_info=True)

    return redirect(url_for('home_route'))

# The consumer thread is started here when running the app directly
# (i.e., not using `flask run` which might initialize things differently).
# This ensures the consumer starts in the main Werkzeug process if in debug mode,
# or directly if not in debug mode. This replaces the deprecated @app.before_first_request
# and direct call in `home_route` for initial thread startup.
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5002))
    # Thread start is handled by before_first_request or the start_consumer_thread_if_needed logic
    if os.environ.get('WERKZEUG_RUN_MAIN') == 'true' or not app.debug:
        start_consumer_thread_if_needed()

    logging.info(f"Starting Email Client UI on http://0.0.0.0:{port}. Kafka: {KAFKA_BROKER}")
    app.run(host='0.0.0.0', port=port, debug=False) # debug=False for production-like thread behavior
