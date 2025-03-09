import json
import xml.etree.ElementTree as ET
import redis
import requests
from elasticsearch import Elasticsearch
from threading import Lock
from datetime import datetime
import logging
import sqlite3
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TaskProcessor:
    # Class variables
    CACHE_EXPIRATION = 3600  # 1 hour
    RATE_LIMIT = 100  # Requests per minute

    def __init__(self):
        # Instance variables
        self.redis_conn = redis.Redis(host='localhost', port=6379, db=0)
        self.es = Elasticsearch([{'host': 'localhost', 'port': 9200}])
        self.lock = Lock()  # For thread safety
        self.rate_limit_counter = 0
        self.last_request_time = datetime.now()
        self.db_conn = sqlite3.connect('tasks.db', check_same_thread=False)
        self._initialize_db()
        self.unused_attr = "This is unused"  # Unused attribute
        # self.commented_out_es = Elasticsearch([{'host': 'old-host', 'port': 9200}])  # Commented-out code

    def _initialize_db(self):
        """Initialize the SQLite database."""
        cursor = self.db_conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_type TEXT,
                status TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        self.db_conn.commit()

    def process_xml_file(self, file_path):
        """Process an XML file and extract data."""
        try:
            tree = ET.parse(file_path)
            root = tree.getroot()
            data = []
            for child in root:
                data.append(child.attrib)
            return data
        except Exception as e:
            logger.error(f"Error processing XML file: {e}")
            return None

    def cache_data(self, key, data):
        """Cache data in Redis."""
        try:
            self.redis_conn.setex(key, self.CACHE_EXPIRATION, json.dumps(data))
        except Exception as e:
            logger.error(f"Error caching data: {e}")

    def get_cached_data(self, key):
        """Retrieve cached data from Redis."""
        try:
            cached_data = self.redis_conn.get(key)
            if cached_data:
                return json.loads(cached_data)
        except Exception as e:
            logger.error(f"Error retrieving cached data: {e}")
        return None

    def search_elasticsearch(self, query):
        """Search Elasticsearch with a query."""
        try:
            if self._check_rate_limit():
                res = self.es.search(index="tasks", body=query)
                return res['hits']['hits']
            else:
                logger.warning("Rate limit exceeded")
                return None
        except Exception as e:
            logger.error(f"Error searching Elasticsearch: {e}")
            return None

    def _check_rate_limit(self):
        """Check and enforce rate limiting."""
        current_time = datetime.now()
        time_diff = (current_time - self.last_request_time).total_seconds()
        if time_diff < 60:
            if self.rate_limit_counter >= self.RATE_LIMIT:
                return False
            self.rate_limit_counter += 1
        else:
            self.rate_limit_counter = 1
            self.last_request_time = current_time
        return True

    def generate_report(self, data):
        """Generate a report and save it to a file."""
        try:
            report = {"timestamp": datetime.now().isoformat(), "data": data}
            with open('report.json', 'w') as f:
                json.dump(report, f)
            return True
        except Exception as e:
            logger.error(f"Error generating report: {e}")
            return False

    def log_task_to_db(self, task_type, status):
        """Log a task to the SQLite database."""
        try:
            cursor = self.db_conn.cursor()
            cursor.execute('''
                INSERT INTO tasks (task_type, status) VALUES (?, ?)
            ''', (task_type, status))
            self.db_conn.commit()
        except Exception as e:
            logger.error(f"Error logging task to DB: {e}")

    def process_task(self, task_type, task_data):
        """Process a task based on its type."""
        if task_type == "XML":
            data = self.process_xml_file(task_data)
            if data:
                self.cache_data(task_data, data)
                self.log_task_to_db(task_type, "SUCCESS")
                return data
            else:
                self.log_task_to_db(task_type, "FAILED")
                return None
        elif task_type == "Elasticsearch":
            results = self.search_elasticsearch(task_data)
            if results:
                self.generate_report(results)
                self.log_task_to_db(task_type, "SUCCESS")
                return results
            else:
                self.log_task_to_db(task_type, "FAILED")
                return None
        else:
            logger.error(f"Unknown task type: {task_type}")
            return None

    def cleanup(self):
        """Cleanup resources."""
        try:
            self.db_conn.close()
            self.redis_conn.close()
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")

# Example usage
if __name__ == "__main__":
    processor = TaskProcessor()
    xml_data = processor.process_task("XML", "example.xml")
    es_data = processor.process_task("Elasticsearch", {"query": {"match_all": {}}})
    processor.cleanup()