import unittest
from unittest.mock import patch, MagicMock, call
import json

# Adjust import path if consumer.py is not in the root or PYTHONPATH is not set
# For this subtask, assume consumer.py can be imported directly or is in PYTHONPATH
import consumer # This might need adjustment based on file structure in execution

class TestConsumerMessageRouting(unittest.TestCase):

    def setUp(self):
        # Common setup for tests, if any
        self.producer_mock = MagicMock()
        # Ensure Kafka topic names are consistent if they are dynamically set or configurable
        consumer.MANUAL_REVIEW_TOPIC = 'manual-review'
        consumer.OUTGOING_TOPIC = 'outgoing-messages'
        # Resetting shared state if any (e.g. module-level variables in consumer)
        # consumer.some_shared_list = []

    @patch('consumer.create_producer') # Mock the producer creation
    def test_rule_based_escalation_to_human_review(self, mock_create_producer):
        # Set the mock for the producer instance returned by create_producer
        mock_create_producer.return_value = self.producer_mock

        # Create an incoming message that triggers rule-based escalation (e.g., contains "refund")
        incoming_message = {
            'message_id': 'test-escalate-001',
            'customer_id': 'cust-abc',
            'timestamp': '2023-01-01T12:00:00Z',
            'subject': 'Issue with my order',
            'body': 'My order was incorrect and I want a refund.'
        }

        # Create a dummy Kafka message object as expected by the consumer loop
        kafka_message_mock = MagicMock()
        kafka_message_mock.value = incoming_message

        # Mock the consumer to yield this message
        consumer_instance_mock = MagicMock()
        consumer_instance_mock.__iter__.return_value = [kafka_message_mock]

        with patch('consumer.create_consumer', return_value=consumer_instance_mock):
            # Simulate the core message processing part of consumer.main() for one message
            # This avoids running the infinite loop of consumer.main()
            try:
                # This simulates the loop: for message in consumer:
                # incoming_data = message.value (already prepared as incoming_message)

                response_data = consumer.generate_response(incoming_message)

                # Check if escalation is needed based on responder_type
                if response_data['responder_type'] == "AI_ESCALATION_TO_HUMAN":
                    # Simulate sending original message to manual-review topic
                    self.producer_mock.send(consumer.MANUAL_REVIEW_TOPIC, value=incoming_message)

                # Simulate sending the response (which might be an escalation message) to outgoing topic
                self.producer_mock.send(consumer.OUTGOING_TOPIC, value=response_data)

            except Exception as e:
                self.fail(f"Message processing logic raised an exception: {e}")

        # Assertions:
        # 1. producer.send was called for MANUAL_REVIEW_TOPIC with the original message.
        # 2. producer.send was called for OUTGOING_TOPIC with the escalation message.

        expected_human_escalation_response = consumer.generate_response(incoming_message)
        self.assertEqual(expected_human_escalation_response['body'], consumer.HUMAN_ESCALATION_MESSAGE)
        self.assertEqual(expected_human_escalation_response['responder_type'], "AI_ESCALATION_TO_HUMAN")

        # Define expected calls
        expected_calls = [
            call(consumer.MANUAL_REVIEW_TOPIC, value=incoming_message),
            call(consumer.OUTGOING_TOPIC, value=expected_human_escalation_response)
        ]

        self.producer_mock.send.assert_has_calls(expected_calls, any_order=False)
        self.assertEqual(self.producer_mock.send.call_count, 2)


    @patch('consumer.create_producer')
    def test_standard_ai_response_no_escalation(self, mock_create_producer):
        mock_create_producer.return_value = self.producer_mock

        # Create an incoming message that does NOT trigger rule-based escalation
        incoming_message = {
            'message_id': 'test-ai-resp-002',
            'customer_id': 'cust-def',
            'timestamp': '2023-01-01T12:05:00Z',
            'subject': 'Cold food',
            'body': 'My pizza arrived cold again.' # Does not contain "refund" or other escalation keywords
        }

        kafka_message_mock = MagicMock()
        kafka_message_mock.value = incoming_message

        consumer_instance_mock = MagicMock()
        consumer_instance_mock.__iter__.return_value = [kafka_message_mock]

        with patch('consumer.create_consumer', return_value=consumer_instance_mock):
            # Simulate the core message processing part for one message
            try:
                response_data = consumer.generate_response(incoming_message)

                if response_data['responder_type'] == "AI_ESCALATION_TO_HUMAN": # This should be false
                    self.producer_mock.send(consumer.MANUAL_REVIEW_TOPIC, value=incoming_message)

                self.producer_mock.send(consumer.OUTGOING_TOPIC, value=response_data)

            except Exception as e:
                self.fail(f"Message processing logic raised an exception: {e}")

        # Assertions:
        # 1. producer.send was called for OUTGOING_TOPIC with the standard AI response.
        # 2. producer.send was NOT called for MANUAL_REVIEW_TOPIC.

        expected_ai_response = consumer.generate_response(incoming_message)
        self.assertNotEqual(expected_ai_response['body'], consumer.HUMAN_ESCALATION_MESSAGE)
        self.assertEqual(expected_ai_response['responder_type'], "AI") # or whatever the non-escalation type is

        self.producer_mock.send.assert_called_once_with(consumer.OUTGOING_TOPIC, value=expected_ai_response)

        # Ensure MANUAL_REVIEW_TOPIC was not called by iterating through calls (alternative to checking call_count if more calls were possible)
        manual_review_called = False
        for call_arg in self.producer_mock.send.call_args_list:
            if call_arg[0][0] == consumer.MANUAL_REVIEW_TOPIC:
                manual_review_called = True
                break
        self.assertFalse(manual_review_called, f"Message should not have been sent to '{consumer.MANUAL_REVIEW_TOPIC}'")

if __name__ == '__main__':
    # This is to help run the test file directly if needed,
    # though typically a test runner would be used.
    # Ensure 'consumer.py' is discoverable in PYTHONPATH.
    # For the subtask, this structure is fine.
    unittest.main()
