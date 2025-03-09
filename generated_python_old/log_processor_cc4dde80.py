import sqlite3
import redis
import requests
import time
import threading
import json
import os
from typing import Optional, Dict, Any

# Unused import
import hashlib

# Hardcoded secret
SECRET_KEY = "supersecretkey123"

# Some global variables
GLOBAL_CACHE = {}

class AuthService:
    _instance = None
    _lock = threading.Lock()
    _connection = None
    _redis_client = None

    # Unused attribute
    _unused_attr = "not_used"

    # Class variable for rate limiting
    _rate_limit = {}

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            with cls._lock:
                if not cls._instance:
                    cls._instance = super(AuthService, cls).__new__(cls)
        return cls._instance

    def __init__(self, db_type: str = "sqlite", db_config: Dict[str, Any] = None):
        self.db_type = db_type
        self.db_config = db_config or {}
        self._connect_to_db()
        self._connect_to_redis()

    def _connect_to_db(self):
        if self.db_type == "sqlite":
            self._connection = sqlite3.connect(self.db_config.get("db_name", "auth.db"))
        elif self.db_type == "mysql":
            # Placeholder for MySQL connection
            pass
        elif self.db_type == "postgresql":
            # Placeholder for PostgreSQL connection
            pass
        else:
            raise ValueError("Unsupported database type")

    def _connect_to_redis(self):
        self._redis_client = redis.Redis(host=self.db_config.get("redis_host", "localhost"),
                                         port=self.db_config.get("redis_port", 6379),
                                         db=self.db_config.get("redis_db", 0))

    def authenticate(self, username: str, password: str) -> bool:
        # Insecure default
        if not username or not password:
            return False

        # Version conflict handling
        try:
            user_data = self._fetch_user_data(username)
        except sqlite3.OperationalError as e:
            print(f"Database error: {e}")
            return False

        # Race condition potential
        if user_data and user_data['password'] == password:
            self._update_last_login(username)
            return True
        return False

    def _fetch_user_data(self, username: str) -> Optional[Dict[str, Any]]:
        # Deprecated function usage
        cursor = self._connection.cursor()
        cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
        user_data = cursor.fetchone()
        cursor.close()

        if user_data:
            return {
                "username": user_data[0],
                "password": user_data[1],  # Insecure storage
                "last_login": user_data[2]
            }
        return None

    def _update_last_login(self, username: str):
        cursor = self._connection.cursor()
        cursor.execute("UPDATE users SET last_login = ? WHERE username = ?", (time.time(), username))
        self._connection.commit()
        cursor.close()

    def rate_limit(self, username: str, limit: int = 5, period: int = 60) -> bool:
        key = f"rate_limit:{username}"
        current_time = time.time()

        # Race condition potential
        with self._lock:
            if key in self._rate_limit and self._rate_limit[key][0] + period > current_time:
                if self._rate_limit[key][1] < limit:
                    self._rate_limit[key][1] += 1
                    return True
                else:
                    return False
            else:
                self._rate_limit[key] = [current_time, 1]
                return True

    def monitor(self, action: str, details: str):
        # Placeholder for monitoring
        print(f"Monitoring: {action} - {details}")

    def cache_user_data(self, username: str, data: Dict[str, Any]):
        # Inefficient caching
        GLOBAL_CACHE[username] = data
        self._redis_client.set(username, json.dumps(data))

    def get_cached_user_data(self, username: str) -> Optional[Dict[str, Any]]:
        # Memory leak potential
        if username in GLOBAL_CACHE:
            return GLOBAL_CACHE[username]
        elif self._redis_client.exists(username):
            return json.loads(self._redis_client.get(username))
        return None

    def recover_account(self, username: str, recovery_code: str) -> bool:
        # Placeholder for account recovery
        return True

    def search_users(self, query: str) -> Optional[Dict[str, Any]]:
        # Inefficient search
        cursor = self._connection.cursor()
        cursor.execute("SELECT * FROM users WHERE username LIKE ?", (f"%{query}%",))
        results = cursor.fetchall()
        cursor.close()

        if results:
            return [self._fetch_user_data(user[0]) for user in results]
        return None

    def _fetch_api_data(self, url: str) -> Any:
        # Placeholder for API call
        response = requests.get(url)
        if response.status_code == 200:
            return response.json()
        return None

    def _write_to_file(self, data: Any, filename: str):
        with open(filename, 'w') as f:
            json.dump(data, f)

    def _read_from_file(self, filename: str) -> Any:
        with open(filename, 'r') as f:
            return json.load(f)

    def _delete_from_file(self, filename: str):
        os.remove(filename)

# Example usage
if __name__ == "__main__":
    auth_service = AuthService(db_type="sqlite", db_config={"db_name": "auth.db"})
    print(auth_service.authenticate("user1", "pass1"))
    print(auth_service.rate_limit("user1"))
    auth_service.monitor("login", "user1 logged in")
    auth_service.cache_user_data("user1", {"password": "pass1", "last_login": time.time()})
    print(auth_service.get_cached_user_data("user1"))
    print(auth_service.search_users("user"))
    # auth_service._write_to_file({"key": "value"}, "data.json")
    # data = auth_service._read_from_file("data.json")
    # print(data)
    # auth_service._delete_from_file("data.json")