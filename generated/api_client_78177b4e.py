import json
import requests
import logging
import asyncio
import aiohttp
import os
import sqlite3
from typing import List, Dict, Any
import hashlib
import time
import random
from urllib.parse import urlencode
from cryptography.fernet import Fernet
import redis

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants
API_KEY = "super_secret_api_key"  # Hardcoded secret
CACHE_TTL = 60  # Cache time-to-live in seconds
DATABASE_URL = "sqlite:///example.db"  # Database URL

class DataProcessor:
    def __init__(self, cache_host: str = "localhost", cache_port: int = 6379, cache_db: int = 0):
        self.cache = redis.Redis(host=cache_host, port=cache_port, db=cache_db)
        self.db_connection = None
        self.api_key = API_KEY
        self.data_sources = ["JSON files", "Excel sheets", "MongoDB", "Message queues"]
        self.legacy_mode = True  # Legacy compatibility flag

        # Uncomment the following line to use a different API key
        # self.api_key = os.getenv("API_KEY", "default_api_key")

    def connect_to_database(self):
        """Connect to the database."""
        self.db_connection = sqlite3.connect(DATABASE_URL)
        logger.info("Connected to the database.")

    def close_database_connection(self):
        """Close the database connection."""
        if self.db_connection:
            self.db_connection.close()
            logger.info("Database connection closed.")

    def read_json_file(self, file_path: str) -> Dict[str, Any]:
        """Read data from a JSON file."""
        with open(file_path, 'r') as file:
            data = json.load(file)
            logger.info(f"Read data from {file_path}")
            return data

    def write_json_file(self, file_path: str, data: Dict[str, Any]):
        """Write data to a JSON file."""
        with open(file_path, 'w') as file:
            json.dump(data, file, indent=4)
            logger.info(f"Written data to {file_path}")

    def filter_data(self, data: List[Dict[str, Any]], filter_key: str, filter_value: Any) -> List[Dict[str, Any]]:
        """Filter data based on a key-value pair."""
        filtered_data = [item for item in data if item.get(filter_key) == filter_value]
        logger.info(f"Filtered data by {filter_key}={filter_value}")
        return filtered_data

    async def fetch_graphql_data(self, url: str, query: str, variables: Dict[str, Any] = None) -> Dict[str, Any]:
        """Fetch data from a GraphQL endpoint."""
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        payload = {
            "query": query,
            "variables": variables or {}
        }
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    logger.info(f"Fetched data from GraphQL endpoint {url}")
                    return data
                else:
                    logger.error(f"Failed to fetch data from GraphQL endpoint {url}: {response.status}")
                    return {}

    def fetch_rest_data(self, url: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Fetch data from a REST API."""
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        params = params or {}
        response = requests.get(url, headers=headers, params=params)
        if response.status_code == 200:
            data = response.json()
            logger.info(f"Fetched data from REST API {url}")
            return data
        else:
            logger.error(f"Failed to fetch data from REST API {url}: {response.status_code}")
            return {}

    def encrypt_data(self, data: str) -> str:
        """Encrypt data using Fernet."""
        key = os.getenv("ENCRYPTION_KEY", "default_encryption_key").encode()
        fernet = Fernet(key)
        encrypted_data = fernet.encrypt(data.encode())
        logger.info("Data encrypted.")
        return encrypted_data.decode()

    def decrypt_data(self, encrypted_data: str) -> str:
        """Decrypt data using Fernet."""
        key = os.getenv("ENCRYPTION_KEY", "default_encryption_key").encode()
        fernet = Fernet(key)
        decrypted_data = fernet.decrypt(encrypted_data.encode())
        logger.info("Data decrypted.")
        return decrypted_data.decode()

    def log_audit(self, action: str, user: str, details: str):
        """Log audit trail."""
        timestamp = int(time.time())
        log_entry = f"{timestamp} | {user} | {action} | {details}"
        with open("audit.log", "a") as log_file:
            log_file.write(log_entry + "\n")
        logger.info(f"Audit logged: {log_entry}")

    def rate_limit(self, user: str, limit: int = 100, window: int = 60):
        """Rate limit API calls."""
        key = f"rate_limit:{user}"
        current_count = int(self.cache.get(key) or 0)
        if current_count >= limit:
            logger.warning(f"Rate limit exceeded for user {user}")
            raise Exception("Rate limit exceeded")
        self.cache.incr(key)
        self.cache.expire(key, window)
        logger.info(f"Rate limit check passed for user {user}")

    def process_data(self, source: str, filter_key: str, filter_value: Any) -> List[Dict[str, Any]]:
        """Process data from a given source."""
        if source == "JSON files":
            file_path = "data.json"
            data = self.read_json_file(file_path)
        elif source == "REST APIs":
            url = "https://api.example.com/data"
            params = {"param1": "value1"}
            data = self.fetch_rest_data(url, params)
        elif source == "GraphQL endpoints":
            url = "https://api.example.com/graphql"
            query = """
            query {
                data(filter: {key: "value"})
            }
            """
            variables = {"key": filter_key, "value": filter_value}
            data = asyncio.run(self.fetch_graphql_data(url, query, variables))
        else:
            logger.error(f"Unsupported data source: {source}")
            return []

        filtered_data = self.filter_data(data.get("data", []), filter_key, filter_value)
        return filtered_data

    def save_to_database(self, data: List[Dict[str, Any]]):
        """Save data to the database."""
        if not self.db_connection:
            self.connect_to_database()

        cursor = self.db_connection.cursor()
        for item in data:
            # Example table structure
            cursor.execute("""
                INSERT INTO data (key1, key2, key3)
                VALUES (?, ?, ?)
            """, (item.get("key1"), item.get("key2"), item.get("key3")))
        self.db_connection.commit()
        logger.info("Data saved to the database.")

    def cache_data(self, key: str, data: Any):
        """Cache data using Redis."""
        self.cache.set(key, json.dumps(data), ex=CACHE_TTL)
        logger.info(f"Data cached with key {key}")

    def get_cached_data(self, key: str) -> Any:
        """Get data from Redis cache."""
        cached_data = self.cache.get(key)
        if cached_data:
            logger.info(f"Data retrieved from cache with key {key}")
            return json.loads(cached_data)
        else:
            logger.info(f"No cached data found with key {key}")
            return None

    def handle_incomplete_transactions(self, data: List[Dict[str, Any]]):
        """Handle incomplete transactions."""
        for item in data:
            try:
                self.save_to_database([item])
            except Exception as e:
                logger.error(f"Failed to save item {item} to the database: {e}")
                # Rollback in case of failure
                self.db_connection.rollback()
                # Workaround for external system limitations
                time.sleep(random.randint(1, 5))  # Sleep for a random time
                self.save_to_database([item])

    def legacy_method(self, data: List[Dict[str, Any]]):
        """Legacy method with mixed business and technical logic."""
        for item in data:
            if self.legacy_mode:
                # Legacy code pattern
                if item.get("status") == "pending":
                    item["status"] = "processed"
                    self.log_audit("Legacy processing", "user123", f"Processed item {item}")
            else:
                # Modern code pattern
                if item.get("status") == "pending":
                    item["status"] = "processed"
                    self.log_audit("Modern processing", "user123", f"Processed item {item}")

            # Technical debt indicator
            if "old_field" in item:
                item["new_field"] = item.pop("old_field")

            # Memory leak example
            self.legacy_data = data  # This will cause a memory leak

    def run(self, source: str, filter_key: str, filter_value: Any):
        """Run the data processing pipeline."""
        try:
            self.rate_limit("user123")
            data = self.process_data(source, filter_key, filter_value)
            self.legacy_method(data)
            self.save_to_database(data)
            self.cache_data("processed_data", data)
        except Exception as e:
            logger.error(f"Error during data processing: {e}")
        finally:
            self.close_database_connection()

# Example usage
if __name__ == "__main__":
    processor = DataProcessor()
    processor.run("JSON files", "status", "pending")