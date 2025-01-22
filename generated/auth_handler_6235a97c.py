import json
import logging
import time
from datetime import datetime, timedelta
from queue import Queue
from threading import Thread
from abc import ABC, abstractmethod

# Stubbed external dependencies
class RabbitMQ:
    def consume(self):
        return '{"device_id": "sensor_01", "data": {"temp": 22.5, "humidity": 60}}'

class Kafka:
    def produce(self, topic, message):
        print(f"Produced to Kafka topic {topic}: {message}")

class Elasticsearch:
    def index(self, index_name, document):
        print(f"Indexed in Elasticsearch {index_name}: {document}")

class APIKeyManager:
    def __init__(self):
        self.keys = ["key1", "key2", "key3"]
        self.current_key_index = 0

    def rotate_key(self):
        self.current_key_index = (self.current_key_index + 1) % len(self.keys)
        return self.keys[self.current_key_index]

class SessionManager:
    def __init__(self, timeout=300):
        self.sessions = {}
        self.timeout = timeout

    def create_session(self, device_id):
        session_id = f"session_{device_id}"
        self.sessions[session_id] = datetime.now()
        return session_id

    def validate_session(self, session_id):
        if session_id in self.sessions and (datetime.now() - self.sessions[session_id]).seconds < self.timeout:
            return True
        return False

# Adapter pattern for external integrations
class DataSourceAdapter(ABC):
    @abstractmethod
    def fetch_data(self):
        pass

class RabbitMQAdapter(DataSourceAdapter):
    def __init__(self):
        self.rabbitmq = RabbitMQ()

    def fetch_data(self):
        return self.rabbitmq.consume()

class KafkaAdapter(DataSourceAdapter):
    def __init__(self):
        self.kafka = Kafka()

    def send_data(self, topic, message):
        self.kafka.produce(topic, message)

# Main orchestrator class
class IoTDataManager:
    def __init__(self):
        self.rabbitmq_adapter = RabbitMQAdapter()
        self.kafka_adapter = KafkaAdapter()
        self.elasticsearch = Elasticsearch()
        self.api_key_manager = APIKeyManager()
        self.session_manager = SessionManager()
        self.logger = logging.getLogger("IoTDataManager")
        self.logger.setLevel(logging.INFO)
        self.data_queue = Queue()

    def extract_data(self):
        """Extract data from RabbitMQ."""
        try:
            data = self.rabbitmq_adapter.fetch_data()
            self.data_queue.put(data)
        except Exception as e:
            self.logger.error(f"Error extracting data: {e}")

    def transform_data(self, raw_data):
        """Transform raw sensor data."""
        try:
            data = json.loads(raw_data)
            transformed = {
                "device_id": data["device_id"],
                "timestamp": datetime.now().isoformat(),
                "sensor_data": data["data"]
            }
            return transformed
        except Exception as e:
            self.logger.error(f"Error transforming data: {e}")
            return None

    def load_data(self, transformed_data):
        """Load data into Elasticsearch and Kafka."""
        if not transformed_data:
            return
        try:
            self.elasticsearch.index("sensor_data", transformed_data)
            self.kafka_adapter.send_data("sensor_updates", json.dumps(transformed_data))
        except Exception as e:
            self.logger.error(f"Error loading data: {e}")

    def handle_rate_limit(self):
        """Handle rate limit exceeded scenarios."""
        self.logger.warning("Rate limit exceeded. Sleeping for 5 seconds...")
        time.sleep(5)

    def enforce_data_retention(self):
        """Mock data retention policy enforcement."""
        self.logger.info("Enforcing data retention policy...")
        # Stubbed logic for data retention

    def log_data_access(self, device_id):
        """Log data access for compliance."""
        self.logger.info(f"Data accessed for device: {device_id}")

    def manage_consent(self, device_id):
        """Mock consent management implementation."""
        self.logger.info(f"Consent managed for device: {device_id}")

    def process_data(self):
        """Orchestrate the data flow."""
        while True:
            if self.data_queue.empty():
                self.extract_data()
            else:
                raw_data = self.data_queue.get()
                transformed_data = self.transform_data(raw_data)
                self.load_data(transformed_data)
                self.log_data_access(transformed_data["device_id"])
                self.manage_consent(transformed_data["device_id"])
                self.enforce_data_retention()

                # Rotate API key
                new_key = self.api_key_manager.rotate_key()
                self.logger.info(f"Rotated API key to: {new_key}")

                # Simulate rate limit handling
                self.handle_rate_limit()

                # Simulate session management
                session_id = self.session_manager.create_session(transformed_data["device_id"])
                if self.session_manager.validate_session(session_id):
                    self.logger.info("Session is valid.")
                else:
                    self.logger.warning("Session expired or invalid.")

# Main function
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    manager = IoTDataManager()

    # Run data processing in a separate thread
    Thread(target=manager.process_data, daemon=True).start()

    # Keep the main thread alive
    while True:
        time.sleep(1)