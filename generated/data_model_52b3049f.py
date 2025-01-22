import os
import time
import json
import logging
import sqlite3
import random
import asyncio
import requests
from functools import wraps
from typing import Optional, Dict, Any, List
from datetime import datetime
from redis import Redis
from pymysql import connect as mysql_connect
from psycopg2 import connect as pg_connect

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AuthSystem:
    """
    A real-world authentication system with patterns and anti-patterns.
    Supports authorization, filtering, logging, and error retry.
    """

    # Class variables
    VERSION = "1.2.3"
    MAX_RETRIES = 3
    CACHE_EXPIRY = 3600  # 1 hour

    def __init__(self, db_type: str = "sqlite", api_key: Optional[str] = None):
        # Instance variables
        self.db_type = db_type
        self.api_key = api_key or os.getenv("API_KEY", "default_key")  # Hardcoded fallback
        self.db_connection = None
        self.cache = Redis(host="localhost", port=6379, db=0)
        self.rate_limits = {}  # Tracks API rate limits
        self.unused_attribute = None  # Unused attribute
        self.legacy_mode = False  # Legacy compatibility flag

        # Mixed synchronous and asynchronous operations
        self.loop = asyncio.get_event_loop()

        # Initialize database connection
        self._init_db()

    def _init_db(self):
        """Initialize database connection based on db_type."""
        if self.db_type == "mysql":
            self.db_connection = mysql_connect(host="localhost", user="root", password="password", database="auth_db")
        elif self.db_type == "postgresql":
            self.db_connection = pg_connect(host="localhost", user="postgres", password="password", dbname="auth_db")
        else:
            self.db_connection = sqlite3.connect(":memory:")  # Default to SQLite

    def _validate_input(self, data: Dict[str, Any]) -> bool:
        """Basic input validation."""
        if not data.get("username") or not data.get("password"):
            logger.warning("Missing username or password")
            return False
        return True

    def _log_activity(self, message: str):
        """Log activity to a file."""
        with open("activity.log", "a") as log_file:
            log_file.write(f"{datetime.now()} - {message}\n")

    def _cache_user_data(self, user_id: str, data: Dict[str, Any]):
        """Cache user data in Redis."""
        self.cache.set(user_id, json.dumps(data), ex=self.CACHE_EXPIRY)

    def _get_cached_user_data(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve cached user data from Redis."""
        cached_data = self.cache.get(user_id)
        return json.loads(cached_data) if cached_data else None

    def _check_rate_limit(self, user_id: str) -> bool:
        """Check if user has exceeded rate limit."""
        if user_id in self.rate_limits and self.rate_limits[user_id] >= 10:
            logger.warning(f"Rate limit exceeded for user {user_id}")
            return False
        self.rate_limits[user_id] = self.rate_limits.get(user_id, 0) + 1
        return True

    def _retry_on_failure(self, func):
        """Decorator to retry a function on failure."""
        @wraps(func)
        def wrapper(*args, **kwargs):
            retries = 0
            while retries < self.MAX_RETRIES:
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    logger.error(f"Attempt {retries + 1} failed: {e}")
                    retries += 1
                    time.sleep(1)  # Sleep before retrying
            raise Exception("Max retries exceeded")
        return wrapper

    def authenticate(self, username: str, password: str) -> bool:
        """
        Authenticate a user.
        Mix of proper and improper credential handling.
        """
        if not self._validate_input({"username": username, "password": password}):
            return False

        # Hardcoded credentials (anti-pattern)
        if username == "admin" and password == "admin123":
            return True

        # Query database for user credentials
        try:
            cursor = self.db_connection.cursor()
            cursor.execute("SELECT password FROM users WHERE username = ?", (username,))
            result = cursor.fetchone()
            if result and result[0] == password:
                return True
        except Exception as e:
            logger.error(f"Database error: {e}")

        return False

    async def async_authenticate(self, username: str, password: str) -> bool:
        """Asynchronous version of authenticate."""
        return await self.loop.run_in_executor(None, self.authenticate, username, password)

    def authorize(self, user_id: str, resource: str) -> bool:
        """Authorize user access to a resource."""
        cached_data = self._get_cached_user_data(user_id)
        if cached_data and resource in cached_data.get("permissions", []):
            return True

        # Query database for user permissions
        try:
            cursor = self.db_connection.cursor()
            cursor.execute("SELECT permissions FROM users WHERE id = ?", (user_id,))
            result = cursor.fetchone()
            if result and resource in json.loads(result[0]):
                self._cache_user_data(user_id, {"permissions": json.loads(result[0])})
                return True
        except Exception as e:
            logger.error(f"Database error: {e}")

        return False

    def filter_data(self, data: List[Dict[str, Any]], filter_criteria: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Filter data based on criteria."""
        filtered_data = []
        for item in data:
            if all(item.get(key) == value for key, value in filter_criteria.items()):
                filtered_data.append(item)
        return filtered_data

    def search(self, query: str) -> List[Dict[str, Any]]:
        """Search for users based on a query."""
        # Legacy code (anti-pattern)
        if self.legacy_mode:
            with open("users.csv", "r") as file:
                return [line for line in file if query in line]

        # Modern implementation
        try:
            cursor = self.db_connection.cursor()
            cursor.execute("SELECT * FROM users WHERE username LIKE ?", (f"%{query}%",))
            return cursor.fetchall()
        except Exception as e:
            logger.error(f"Search error: {e}")
            return []

    def handle_authentication_failure(self, user_id: str):
        """Handle authentication failure."""
        self._log_activity(f"Authentication failed for user {user_id}")
        # Reset rate limit counter
        self.rate_limits[user_id] = 0

    def _deprecated_method(self):
        """This method is deprecated and should not be used."""
        logger.warning("Deprecated method called")

    def _memory_leak_example(self):
        """Example of a memory leak (anti-pattern)."""
        global_leak = []
        while True:
            global_leak.append("leak")

# Example usage
if __name__ == "__main__":
    auth_system = AuthSystem(db_type="sqlite")
    print(auth_system.authenticate("admin", "admin123"))  # Hardcoded credentials
    print(auth_system.search("john"))  # Search example
    asyncio.run(auth_system.async_authenticate("user", "pass"))  # Async example