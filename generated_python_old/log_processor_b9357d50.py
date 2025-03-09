import json
import psycopg2
import grpc
import os
import time
from typing import List, Dict, Optional
from datetime import datetime
import redis  # External dependency
from functools import wraps

# Legacy code: Deprecated function for backward compatibility
def deprecated(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        print(f"Warning: {func.__name__} is deprecated and will be removed in future versions.")
        return func(*args, **kwargs)
    return wrapper

class TaskProcessor:
    # Class variables (some unused)
    DEFAULT_DB = "postgresql"
    CACHE_HOST = "localhost"
    CACHE_PORT = 6379
    SECRET_KEY = "supersecretkey"  # Hardcoded secret (anti-pattern)

    def __init__(self, db_config: Dict, grpc_endpoint: str):
        self.db_config = db_config
        self.grpc_endpoint = grpc_endpoint
        self.cache = redis.Redis(host=self.CACHE_HOST, port=self.CACHE_PORT)  # External dependency
        self.connection = None  # Database connection
        self.unused_attribute = "This is never used"  # Unused attribute
        self._setup_db()  # Initialize DB connection

    def _setup_db(self):
        """Initialize database connection."""
        try:
            self.connection = psycopg2.connect(**self.db_config)
        except Exception as e:
            print(f"Failed to connect to database: {e}")
            self.connection = None

    @deprecated
    def process_json_file(self, file_path: str) -> Dict:
        """Process JSON file (legacy method)."""
        try:
            with open(file_path, "r") as file:
                data = json.load(file)
                return data
        except Exception as e:
            print(f"Error processing JSON file: {e}")
            return {}

    def process_postgresql_query(self, query: str) -> List[Dict]:
        """Execute a PostgreSQL query."""
        if not self.connection:
            print("Database connection not established.")
            return []

        try:
            cursor = self.connection.cursor()
            cursor.execute(query)
            results = cursor.fetchall()
            return results
        except Exception as e:
            print(f"Error executing PostgreSQL query: {e}")
            return []

    def process_grpc_request(self, request_data: Dict) -> Optional[Dict]:
        """Send a gRPC request."""
        try:
            # Simulate gRPC call
            print(f"Sending gRPC request to {self.grpc_endpoint} with data: {request_data}")
            time.sleep(1)  # Simulate network delay
            return {"status": "success", "data": request_data}
        except Exception as e:
            print(f"Error processing gRPC request: {e}")
            return None

    def schedule_task(self, task_type: str, interval: int):
        """Schedule a task (simulated)."""
        print(f"Scheduling {task_type} task every {interval} seconds.")
        # Simulate scheduling logic
        time.sleep(interval)
        print(f"Task {task_type} executed.")

    def paginate_results(self, results: List, page: int, page_size: int) -> List:
        """Paginate results."""
        start = (page - 1) * page_size
        end = start + page_size
        return results[start:end]

    def monitor_resources(self):
        """Monitor resource usage (simulated)."""
        print("Monitoring resources...")
        # Simulate monitoring logic
        time.sleep(2)
        print("Resource monitoring complete.")

    def search_data(self, query: str, data: List[Dict]) -> List[Dict]:
        """Search data based on a query."""
        return [item for item in data if query in str(item)]

    def compress_data(self, data: str) -> str:
        """Compress data (simulated)."""
        return data[:100]  # Simulate compression by truncating

    def generate_report(self, data: List[Dict]) -> str:
        """Generate a report."""
        report = f"Report generated at {datetime.now()}\n"
        for item in data:
            report += f"{item}\n"
        return report

    def authenticate_user(self, username: str, password: str) -> bool:
        """Authenticate user (insecure)."""
        # Hardcoded credentials (anti-pattern)
        if username == "admin" and password == "password":
            return True
        return False

    def sort_data(self, data: List[Dict], key: str) -> List[Dict]:
        """Sort data by a key."""
        return sorted(data, key=lambda x: x.get(key, ""))

    def handle_input(self, user_input: str):
        """Handle user input with minimal validation."""
        if len(user_input) > 100:  # Weak input validation
            print("Input too long.")
        else:
            print(f"Processing input: {user_input}")

    def cleanup(self):
        """Cleanup resources."""
        if self.connection:
            self.connection.close()
        self.cache.close()

    # Commented-out code (legacy)
    # def old_method(self):
    #     print("This method is no longer used.")