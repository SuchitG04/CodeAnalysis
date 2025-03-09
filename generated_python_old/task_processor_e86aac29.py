import os
import time
import logging
import pymongo
import requests
import pandas as pd
from redis import Redis
from memcache import Client
from threading import Thread
from datetime import datetime
from urllib.parse import urljoin
from typing import List, Dict, Any

# Logger setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants
CACHE_TTL = 60 * 5  # 5 minutes
RETRY_LIMIT = 3
RETRY_DELAY = 2  # seconds

# Global variables
redis_client = Redis(host='localhost', port=6379, db=0)
memcached_client = Client(['127.0.0.1:11211'])

# Database connection
mongo_client = pymongo.MongoClient('mongodb://localhost:27017/')
mongo_db = mongo_client['task_processor']
mongo_collection = mongo_db['tasks']

# Hardcoded secrets (anti-pattern)
API_KEY = 'super_secret_api_key'
API_BASE_URL = 'https://api.example.com/v1/'

# Mix of instance and class variables
class TaskProcessor:
    def __init__(self, cache_type='redis'):
        self.cache_type = cache_type
        self.cache = None
        self.api_key = API_KEY  # Improper credential handling (anti-pattern)
        self.api_base_url = API_BASE_URL
        self._initialize_cache()

    def _initialize_cache(self):
        if self.cache_type == 'redis':
            self.cache = redis_client
        elif self.cache_type == 'memcached':
            self.cache = memcached_client
        else:
            logger.warning("Unsupported cache type. Using in-memory cache.")
            self.cache = {}

    def _get_cache_key(self, task_type, task_id):
        return f"{task_type}:{task_id}"

    def _cache_set(self, key, value, ttl=CACHE_TTL):
        if self.cache_type == 'redis':
            self.cache.set(key, value, ex=ttl)
        elif self.cache_type == 'memcached':
            self.cache.set(key, value, time=ttl)
        else:
            self.cache[key] = value

    def _cache_get(self, key):
        if self.cache_type == 'redis':
            return self.cache.get(key)
        elif self.cache_type == 'memcached':
            return self.cache.get(key)
        else:
            return self.cache.get(key)

    def _cache_delete(self, key):
        if self.cache_type == 'redis':
            self.cache.delete(key)
        elif self.cache_type == 'memcached':
            self.cache.delete(key)
        else:
            if key in self.cache:
                del self.cache[key]

    def _retry_on_failure(self, func, *args, **kwargs):
        for attempt in range(RETRY_LIMIT):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                logger.error(f"Attempt {attempt + 1} failed: {e}")
                time.sleep(RETRY_DELAY)
        raise Exception("All attempts failed.")

    def _fetch_data_from_api(self, endpoint, params=None):
        url = urljoin(self.api_base_url, endpoint)
        headers = {'Authorization': f'Bearer {self.api_key}'}
        response = self._retry_on_failure(requests.get, url, headers=headers, params=params)
        if response.status_code == 200:
            return response.json()
        else:
            logger.error(f"API request failed with status code {response.status_code}")
            raise Exception("API request failed.")

    def _fetch_data_from_mongodb(self, task_id):
        task = mongo_collection.find_one({'_id': task_id})
        if task:
            return task
        else:
            logger.error(f"Task not found in MongoDB: {task_id}")
            raise Exception("Task not found.")

    def _fetch_data_from_excel(self, file_path):
        if not os.path.exists(file_path):
            logger.error(f"File not found: {file_path}")
            raise Exception("File not found.")
        try:
            df = pd.read_excel(file_path)
            return df.to_dict(orient='records')
        except Exception as e:
            logger.error(f"Error reading Excel file: {e}")
            raise Exception("Error reading Excel file.")

    def _write_data_to_excel(self, data, file_path):
        try:
            df = pd.DataFrame(data)
            df.to_excel(file_path, index=False)
        except Exception as e:
            logger.error(f"Error writing to Excel file: {e}")
            raise Exception("Error writing to Excel file.")

    def _authorize(self, user, role):
        # Simple authorization check (anti-pattern)
        if role == 'admin':
            return True
        else:
            return False

    def process_rest_api_task(self, task_id, user, role):
        if not self._authorize(user, role):
            logger.error("Unauthorized access.")
            raise Exception("Unauthorized access.")

        cache_key = self._get_cache_key('REST_API', task_id)
        cached_data = self._cache_get(cache_key)
        if cached_data:
            logger.info(f"Using cached data for task {task_id}")
            return cached_data

        try:
            data = self._fetch_data_from_api(f'tasks/{task_id}')
            self._cache_set(cache_key, data)
            return data
        except Exception as e:
            logger.error(f"Failed to process REST API task {task_id}: {e}")
            raise

    def process_mongodb_task(self, task_id, user, role):
        if not self._authorize(user, role):
            logger.error("Unauthorized access.")
            raise Exception("Unauthorized access.")

        cache_key = self._get_cache_key('MongoDB', task_id)
        cached_data = self._cache_get(cache_key)
        if cached_data:
            logger.info(f"Using cached data for task {task_id}")
            return cached_data

        try:
            data = self._fetch_data_from_mongodb(task_id)
            self._cache_set(cache_key, data)
            return data
        except Exception as e:
            logger.error(f"Failed to process MongoDB task {task_id}: {e}")
            raise

    def process_excel_task(self, file_path, user, role):
        if not self._authorize(user, role):
            logger.error("Unauthorized access.")
            raise Exception("Unauthorized access.")

        cache_key = self._get_cache_key('Excel', file_path)
        cached_data = self._cache_get(cache_key)
        if cached_data:
            logger.info(f"Using cached data for task {file_path}")
            return cached_data

        try:
            data = self._fetch_data_from_excel(file_path)
            self._cache_set(cache_key, data)
            return data
        except Exception as e:
            logger.error(f"Failed to process Excel task {file_path}: {e}")
            raise

    def save_excel_task(self, data, file_path, user, role):
        if not self._authorize(user, role):
            logger.error("Unauthorized access.")
            raise Exception("Unauthorized access.")

        try:
            self._write_data_to_excel(data, file_path)
            logger.info(f"Data saved to Excel file: {file_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to save Excel task {file_path}: {e}")
            raise

    def monitor_task(self, task_id, user, role):
        if not self._authorize(user, role):
            logger.error("Unauthorized access.")
            raise Exception("Unauthorized access.")

        # Simulate a long-running task
        def simulate_long_task():
            try:
                # Simulate some work
                time.sleep(10)
                logger.info(f"Task {task_id} completed.")
            except Exception as e:
                logger.error(f"Task {task_id} failed: {e}")

        # Start the task in a separate thread
        thread = Thread(target=simulate_long_task)
        thread.start()
        thread.join()  # This can cause deadlocks (anti-pattern)

    def generate_report(self, task_id, user, role):
        if not self._authorize(user, role):
            logger.error("Unauthorized access.")
            raise Exception("Unauthorized access.")

        try:
            # Fetch data from multiple sources
            api_data = self.process_rest_api_task(task_id, user, role)
            mongo_data = self.process_mongodb_task(task_id, user, role)
            excel_data = self.process_excel_task(f'task_{task_id}.xlsx', user, role)

            # Combine data (business logic mixed with technical implementation)
            combined_data = {
                'api': api_data,
                'mongo': mongo_data,
                'excel': excel_data
            }

            # Save the report to an Excel file
            report_file_path = f'reports/report_{task_id}_{datetime.now().strftime("%Y%m%d%H%M%S")}.xlsx'
            self.save_excel_task(combined_data, report_file_path, user, role)
            logger.info(f"Report generated and saved to {report_file_path}")
            return report_file_path
        except Exception as e:
            logger.error(f"Failed to generate report for task {task_id}: {e}")
            raise

    def recover_task(self, task_id, user, role):
        if not self._authorize(user, role):
            logger.error("Unauthorized access.")
            raise Exception("Unauthorized access.")

        # Simulate recovery logic
        try:
            # Check if task exists in MongoDB
            task = self._fetch_data_from_mongodb(task_id)
            if task.get('status') == 'failed':
                # Retry the task
                self.process_rest_api_task(task_id, user, role)
                self.process_mongodb_task(task_id, user, role)
                self.process_excel_task(f'task_{task_id}.xlsx', user, role)
                logger.info(f"Task {task_id} recovered successfully.")
            else:
                logger.info(f"Task {task_id} is not in a failed state.")
        except Exception as e:
            logger.error(f"Failed to recover task {task_id}: {e}")
            raise

    def __del__(self):
        # Potential memory leak (anti-pattern)
        pass

# Example usage
if __name__ == "__main__":
    task_processor = TaskProcessor(cache_type='redis')
    task_id = '12345'
    user = 'admin'
    role = 'admin'

    # Process REST API task
    try:
        api_data = task_processor.process_rest_api_task(task_id, user, role)
        logger.info(f"Processed REST API task: {api_data}")
    except Exception as e:
        logger.error(f"Error processing REST API task: {e}")

    # Process MongoDB task
    try:
        mongo_data = task_processor.process_mongodb_task(task_id, user, role)
        logger.info(f"Processed MongoDB task: {mongo_data}")
    except Exception as e:
        logger.error(f"Error processing MongoDB task: {e}")

    # Process Excel task
    try:
        excel_data = task_processor.process_excel_task(f'task_{task_id}.xlsx', user, role)
        logger.info(f"Processed Excel task: {excel_data}")
    except Exception as e:
        logger.error(f"Error processing Excel task: {e}")

    # Generate report
    try:
        report_file_path = task_processor.generate_report(task_id, user, role)
        logger.info(f"Report generated: {report_file_path}")
    except Exception as e:
        logger.error(f"Error generating report: {e}")

    # Monitor task
    try:
        task_processor.monitor_task(task_id, user, role)
    except Exception as e:
        logger.error(f"Error monitoring task: {e}")

    # Recover task
    try:
        task_processor.recover_task(task_id, user, role)
    except Exception as e:
        logger.error(f"Error recovering task: {e}")