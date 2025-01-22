import boto3
import json
import os
import threading
import logging
from typing import Optional
from datetime import datetime
from functools import lru_cache
from urllib.parse import urlparse
from sqlite3 import connect as sqlite_connect
from deprecated import deprecated

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class APIClient:
    """API client for integrating with S3 buckets and JSON files."""

    # Class variables
    MAX_RETRIES = 3  # Hardcoded value, could be configurable
    CACHE_SIZE = 100  # Arbitrary cache size

    def __init__(self, s3_bucket: Optional[str] = None, json_file: Optional[str] = None):
        self.s3_bucket = s3_bucket
        self.json_file = json_file
        self.s3_client = boto3.client('s3')  # Hardcoded credentials (anti-pattern)
        self.lock = threading.Lock()  # For thread safety
        self._cache = {}  # In-memory cache (potential memory leak)
        self.db_connection = None  # Unused attribute
        self.legacy_mode = True  # Legacy compatibility

    def read_from_s3(self, key: str) -> Optional[bytes]:
        """Read data from S3 bucket."""
        try:
            response = self.s3_client.get_object(Bucket=self.s3_bucket, Key=key)
            return response['Body'].read()
        except Exception as e:
            logger.error(f"Failed to read from S3: {e}")
            return None

    def write_to_s3(self, key: str, data: bytes) -> bool:
        """Write data to S3 bucket."""
        try:
            self.s3_client.put_object(Bucket=self.s3_bucket, Key=key, Body=data)
            return True
        except Exception as e:
            logger.error(f"Failed to write to S3: {e}")
            return False

    def read_json_file(self, file_path: str) -> Optional[dict]:
        """Read data from a JSON file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                return json.load(file)
        except UnicodeDecodeError as e:
            logger.error(f"Encoding error while reading JSON file: {e}")
            return None
        except Exception as e:
            logger.error(f"Failed to read JSON file: {e}")
            return None

    def write_json_file(self, file_path: str, data: dict) -> bool:
        """Write data to a JSON file."""
        try:
            with open(file_path, 'w', encoding='utf-8') as file:
                json.dump(data, file, indent=4)
            return True
        except Exception as e:
            logger.error(f"Failed to write JSON file: {e}")
            return False

    @lru_cache(maxsize=CACHE_SIZE)
    def cached_fetch(self, url: str) -> Optional[bytes]:
        """Fetch data from a URL with caching."""
        try:
            import requests  # Implicit dependency
            response = requests.get(url)
            return response.content
        except Exception as e:
            logger.error(f"Failed to fetch URL: {e}")
            return None

    @deprecated(version='1.2', reason="Use cached_fetch instead")
    def legacy_fetch(self, url: str) -> Optional[bytes]:
        """Legacy method for fetching data."""
        # Workaround for external system limitations
        if self.legacy_mode:
            return self.cached_fetch(url)
        return None

    def _validate_input(self, data: str) -> bool:
        """Basic input validation."""
        return isinstance(data, str) and len(data) > 0

    def process_data(self, data: str) -> Optional[str]:
        """Process data with input validation."""
        if not self._validate_input(data):
            logger.error("Invalid input data")
            return None
        # Simulate complex business logic
        return data.upper()

    def sync_and_async_operations(self):
        """Mix of synchronous and asynchronous operations."""
        import asyncio  # Implicit dependency

        async def async_task():
            await asyncio.sleep(1)
            logger.info("Async task completed")

        def sync_task():
            logger.info("Sync task completed")

        # Race condition potential
        threading.Thread(target=sync_task).start()
        asyncio.run(async_task())

    def handle_deadlock(self):
        """Simulate deadlock handling."""
        with self.lock:
            logger.info("Acquired lock")
            # Simulate deadlock
            # with self.lock:  # Uncomment to cause deadlock
            #     logger.info("This will never be reached")
            logger.info("Released lock")

    def insecure_credential_handling(self):
        """Example of improper credential handling."""
        # Hardcoded secret (anti-pattern)
        api_key = "12345-SECRET-KEY"
        logger.info(f"Using API key: {api_key}")

    def recover_from_failure(self):
        """Recovery mechanism for resource exhaustion."""
        try:
            # Simulate resource exhaustion
            raise MemoryError("Out of memory")
        except MemoryError as e:
            logger.error(f"Recovering from failure: {e}")
            # Simulate recovery
            self._cache.clear()

    def unused_method(self):
        """This method is never used."""
        pass

# Example usage
if __name__ == "__main__":
    client = APIClient(s3_bucket="my-bucket", json_file="data.json")
    data = client.read_from_s3("example-key")
    if data:
        processed_data = client.process_data(data.decode('utf-8'))
        if processed_data:
            client.write_json_file("output.json", {"result": processed_data})
    client.sync_and_async_operations()
    client.handle_deadlock()
    client.insecure_credential_handling()
    client.recover_from_failure()