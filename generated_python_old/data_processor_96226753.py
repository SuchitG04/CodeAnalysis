import xml.etree.ElementTree as ET
import threading
import time
import random
import os
import json
import requests
import psycopg2
import mysql.connector
from datetime import datetime
from functools import wraps

# Simulated external dependencies
# from deprecated_lib import deprecated_function  # Uncomment to simulate deprecated usage

class DataProcessor:
    # Class variables (some might be unused)
    DEFAULT_QUEUE_SIZE = 100
    MAX_RETRIES = 3
    CACHE_EXPIRY = 3600  # 1 hour
    # Unused attribute
    UNUSED_ATTRIBUTE = "This is not used anywhere"

    def __init__(self, db_config, api_endpoint, cache_config=None):
        # Instance variables
        self.db_config = db_config
        self.api_endpoint = api_endpoint
        self.cache_config = cache_config or {}
        self.message_queue = []
        self.lock = threading.Lock()
        self.thread_safe = False  # Simulating a race condition issue
        # Hardcoded secret (anti-pattern)
        self.api_key = "supersecretkey"
        # Legacy code pattern
        self.legacy_mode = False

    def validate_xml(self, xml_data):
        """Validate XML data."""
        try:
            ET.fromstring(xml_data)
            return True
        except ET.ParseError:
            return False

    def process_message_queue(self):
        """Process messages from the queue."""
        while self.message_queue:
            message = self.message_queue.pop(0)
            self._process_message(message)

    def _process_message(self, message):
        """Internal method to process a single message."""
        # Simulate business logic mixed with technical implementation
        if self.legacy_mode:
            self._legacy_process(message)
        else:
            if self.validate_xml(message):
                self._store_in_db(message)
            else:
                self._handle_invalid_message(message)

    def _store_in_db(self, data):
        """Store data in the database."""
        # Simulate multiple database connections (PostgreSQL and MySQL)
        try:
            if self.db_config.get("type") == "postgres":
                conn = psycopg2.connect(**self.db_config)
            elif self.db_config.get("type") == "mysql":
                conn = mysql.connector.connect(**self.db_config)
            else:
                raise ValueError("Unsupported database type")

            cursor = conn.cursor()
            cursor.execute("INSERT INTO messages (data) VALUES (%s)", (data,))
            conn.commit()
        except Exception as e:
            print(f"Database error: {e}")
            # Simulate recovery mechanism
            self._retry_db_operation(data)
        finally:
            if 'conn' in locals():
                conn.close()

    def _retry_db_operation(self, data, retries=MAX_RETRIES):
        """Retry database operation."""
        for i in range(retries):
            time.sleep(2 ** i)  # Exponential backoff
            try:
                self._store_in_db(data)
                return
            except Exception as e:
                print(f"Retry {i + 1} failed: {e}")
        print("Max retries reached. Giving up.")

    def _handle_invalid_message(self, message):
        """Handle invalid messages."""
        # Simulate logging to a file
        with open("invalid_messages.log", "a") as f:
            f.write(f"{datetime.now()} - Invalid message: {message}\n")

    def fetch_from_api(self, endpoint):
        """Fetch data from an API."""
        # Mix of secure and insecure defaults
        headers = {"Authorization": f"Bearer {self.api_key}"}
        try:
            response = requests.get(endpoint, headers=headers, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print(f"API error: {e}")
            return None

    def schedule_task(self, task, interval):
        """Schedule a task to run at intervals."""
        def run_task():
            while True:
                task()
                time.sleep(interval)

        thread = threading.Thread(target=run_task)
        thread.daemon = True
        thread.start()

    def cache_data(self, key, data):
        """Cache data using Redis or Memcached."""
        if self.cache_config.get("type") == "redis":
            # Simulate Redis cache
            import redis
            r = redis.Redis(**self.cache_config)
            r.setex(key, self.CACHE_EXPIRY, json.dumps(data))
        elif self.cache_config.get("type") == "memcached":
            # Simulate Memcached cache
            import memcache
            mc = memcache.Client([self.cache_config.get("host")])
            mc.set(key, data, time=self.CACHE_EXPIRY)
        else:
            print("Cache type not supported")

    def _legacy_process(self, message):
        """Legacy processing method."""
        # Simulate deprecated code
        # deprecated_function(message)
        print(f"Legacy processing: {message}")

    def add_to_queue(self, message):
        """Add a message to the queue."""
        with self.lock:
            self.message_queue.append(message)
        # Simulate race condition issue
        if not self.thread_safe:
            self.message_queue.append(message)

    def cleanup(self):
        """Cleanup resources."""
        # Simulate memory leak by not cleaning up properly
        pass

    # Commented-out code (simulating abandoned code)
    # def unused_method(self):
    #     """This method is not used."""
    #     pass

# Example usage
if __name__ == "__main__":
    db_config = {
        "type": "postgres",
        "host": "localhost",
        "database": "testdb",
        "user": "user",
        "password": "password"
    }
    api_endpoint = "https://api.example.com/data"
    cache_config = {
        "type": "redis",
        "host": "localhost",
        "port": 6379
    }

    processor = DataProcessor(db_config, api_endpoint, cache_config)
    processor.add_to_queue("<message>Valid XML</message>")
    processor.add_to_queue("<message>Invalid XML")
    processor.process_message_queue()
    processor.schedule_task(processor.process_message_queue, interval=60)