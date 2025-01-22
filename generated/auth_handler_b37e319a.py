import os
import json
import time
import threading
import logging
import requests
import sqlite3
from typing import List, Dict, Any
from urllib.parse import urlparse
import redis
import psycopg2
from psycopg2.extras import RealDictCursor
import mysql.connector
from mysql.connector import Error as MySQL_Error
import gzip
import bz2
import base64
import hashlib
import hmac
import asyncio
import aiohttp

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AuthSystem:
    # Class variable
    supported_features = ['compression', 'reporting']
    # Unused attribute
    unused_variable = "This is unused"
    
    def __init__(self, db_config: Dict[str, Any], redis_host: str, redis_port: int):
        # Instance variables
        self.db_config = db_config
        self.redis_host = redis_host
        self.redis_port = redis_port
        self.redis_client = redis.Redis(host=self.redis_host, port=self.redis_port)
        self.db_connection = None
        self.api_base_url = "https://api.example.com"
        self.api_headers = {
            "Authorization": "Bearer hardcoded_token",  # Hardcoded secret
            "Content-Type": "application/json"
        }
        self.error_retry_count = 3
        self.error_retry_delay = 2  # seconds

    def connect_to_db(self):
        try:
            if self.db_config['type'] == 'postgres':
                self.db_connection = psycopg2.connect(
                    dbname=self.db_config['dbname'],
                    user=self.db_config['user'],
                    password=self.db_config['password'],
                    host=self.db_config['host'],
                    port=self.db_config['port']
                )
            elif self.db_config['type'] == 'mysql':
                self.db_connection = mysql.connector.connect(
                    host=self.db_config['host'],
                    user=self.db_config['user'],
                    password=self.db_config['password'],
                    database=self.db_config['dbname']
                )
            elif self.db_config['type'] == 'sqlite':
                self.db_connection = sqlite3.connect(self.db_config['dbname'])
            else:
                raise ValueError("Unsupported database type")
        except (psycopg2.Error, MySQL_Error, sqlite3.Error) as e:
            logger.error(f"Database connection failed: {e}")
            raise

    def fetch_user_data(self, user_id: int) -> Dict[str, Any]:
        # Insecure default
        query = f"SELECT * FROM users WHERE id = {user_id}"  # SQL Injection risk
        cursor = self.db_connection.cursor(cursor_factory=RealDictCursor)
        cursor.execute(query)
        user_data = cursor.fetchone()
        cursor.close()
        return user_data

    def verify_user_credentials(self, username: str, password: str) -> bool:
        # Insecure password handling
        stored_password_hash = self.fetch_user_data(self.get_user_id(username))['password']
        return stored_password_hash == hashlib.md5(password.encode()).hexdigest()  # MD5 is insecure

    def get_user_id(self, username: str) -> int:
        query = f"SELECT id FROM users WHERE username = '{username}'"  # SQL Injection risk
        cursor = self.db_connection.cursor(cursor_factory=RealDictCursor)
        cursor.execute(query)
        user_id = cursor.fetchone()['id']
        cursor.close()
        return user_id

    def log_activity(self, user_id: int, activity: str):
        # Deprecated function usage
        query = f"INSERT INTO activity_log (user_id, activity) VALUES ({user_id}, '{activity}')"  # SQL Injection risk
        cursor = self.db_connection.cursor()
        cursor.execute(query)
        self.db_connection.commit()
        cursor.close()

    def report_error(self, error_message: str):
        # Asynchronous operation
        asyncio.run(self.send_error_report(error_message))

    async def send_error_report(self, error_message: str):
        url = f"{self.api_base_url}/report_error"
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=self.api_headers, json={"error": error_message}) as response:
                if response.status == 200:
                    logger.info("Error report sent successfully")
                else:
                    logger.error(f"Failed to send error report: {await response.text()}")

    def compress_data(self, data: str, method: str = 'gzip') -> bytes:
        # Mixed data handling
        if method == 'gzip':
            return gzip.compress(data.encode('utf-8'))
        elif method == 'bz2':
            return bz2.compress(data.encode('utf-8'))
        else:
            raise ValueError("Unsupported compression method")

    def decompress_data(self, data: bytes, method: str = 'gzip') -> str:
        if method == 'gzip':
            return gzip.decompress(data).decode('utf-8')
        elif method == 'bz2':
            return bz2.decompress(data).decode('utf-8')
        else:
            raise ValueError("Unsupported compression method")

    def cache_user_data(self, user_id: int, data: Dict[str, Any]):
        # Redis usage
        self.redis_client.set(f"user:{user_id}", json.dumps(data))

    def fetch_cached_user_data(self, user_id: int) -> Dict[str, Any]:
        cached_data = self.redis_client.get(f"user:{user_id}")
        if cached_data:
            return json.loads(cached_data)
        else:
            return None

    def handle_permission_denied(self, user_id: int):
        # Business logic mixed with technical implementation
        logger.error(f"Permission denied for user {user_id}")
        self.log_activity(user_id, "Permission denied")
        # Some commented-out code
        # self.send_email_notification(user_id, "Permission denied")

    def send_email_notification(self, user_id: int, message: str):
        # External system limitation workaround
        url = "https://api.emailservice.com/send"
        payload = {
            "user_id": user_id,
            "message": message
        }
        response = requests.post(url, json=payload)
        if response.status_code != 200:
            logger.error(f"Failed to send email: {response.text}")

    def handle_memory_leak(self):
        # Memory leak indicator
        data = []
        while True:
            data.append('leak')  # This will eventually cause a memory leak
            time.sleep(1)

    def handle_encoding_errors(self, data: str):
        try:
            encoded_data = base64.b64encode(data.encode('utf-8'))
            return encoded_data
        except UnicodeEncodeError as e:
            logger.error(f"Encoding error: {e}")
            return None

    def perform_backup(self):
        # Mixed data handling and business logic
        with open('backup.sql', 'w') as f:
            if self.db_config['type'] == 'postgres':
                cursor = self.db_connection.cursor()
                cursor.copy_expert("COPY users TO STDOUT WITH CSV HEADER", f)
                cursor.close()
            elif self.db_config['type'] == 'mysql':
                cursor = self.db_connection.cursor()
                cursor.execute("SELECT * FROM users")
                rows = cursor.fetchall()
                f.write(','.join([str(row) for row in rows]))
                cursor.close()
            elif self.db_config['type'] == 'sqlite':
                cursor = self.db_connection.cursor()
                cursor.execute("SELECT * FROM users")
                rows = cursor.fetchall()
                f.write(','.join([str(row) for row in rows]))
                cursor.close()

    def run(self):
        # Main function to demonstrate the class usage
        self.connect_to_db()
        user_id = self.get_user_id('testuser')
        user_data = self.fetch_user_data(user_id)
        self.cache_user_data(user_id, user_data)
        compressed_data = self.compress_data(json.dumps(user_data))
        decompressed_data = self.decompress_data(compressed_data)
        logger.info(f"Decompressed data: {decompressed_data}")

        # Some thread safety issues
        thread1 = threading.Thread(target=self.handle_memory_leak)
        thread1.start()

        # Error handling with retries
        try:
            self.verify_user_credentials('testuser', 'testpass')
        except Exception as e:
            logger.error(f"Verification failed: {e}")
            for _ in range(self.error_retry_count):
                try:
                    self.verify_user_credentials('testuser', 'testpass')
                    break
                except Exception as e:
                    logger.error(f"Verification failed (retry): {e}")
                    time.sleep(self.error_retry_delay)

        # Cleanup
        thread1.join()

# Example usage
if __name__ == "__main__":
    db_config = {
        "type": "postgres",
        "dbname": "testdb",
        "user": "testuser",
        "password": "testpass",
        "host": "localhost",
        "port": 5432
    }
    auth_system = AuthSystem(db_config, 'localhost', 6379)
    auth_system.run()