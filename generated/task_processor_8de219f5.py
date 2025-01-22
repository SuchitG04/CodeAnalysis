import redis
import csv
import elasticsearch
import threading
import time
import os
import json
from datetime import datetime
import logging

# Global logger
logger = logging.getLogger(__name__)

class CachingSystem:
    def __init__(self, redis_host, redis_port, csv_file_path, elasticsearch_host):
        self.redis_client = redis.Redis(host=redis_host, port=redis_port)
        self.csv_file_path = csv_file_path
        self.elasticsearch_client = elasticsearch.Elasticsearch([elasticsearch_host])

        # Unused attribute
        self.mysql_db_connection = None

        # Class variable for storing cache
        self.cache = {}

        # Lock for race conditions
        self.cache_lock = threading.Lock()

        # Create a thread for periodic cache cleanup
        self.cache_cleanup_thread = threading.Thread(target=self.periodic_cache_cleanup)
        self.cache_cleanup_thread.start()

    def get_from_redis(self, key):
        try:
            value = self.redis_client.get(key)
            if value:
                return value.decode('utf-8')
            else:
                return None
        except redis.exceptions.ConnectionError:
            logger.error("Redis connection error")
            return None

    def get_from_csv(self, key):
        try:
            with open(self.csv_file_path, 'r') as file:
                reader = csv.DictReader(file)
                for row in reader:
                    if row['key'] == key:
                        return row['value']
                return None
        except FileNotFoundError:
            logger.error("CSV file not found")
            return None

    def get_from_elasticsearch(self, key):
        try:
            response = self.elasticsearch_client.search(index='cache', body={'query': {'match': {'key': key}}})
            if response['hits']['total']['value'] > 0:
                return response['hits']['hits'][0]['_source']['value']
            else:
                return None
        except elasticsearch.exceptions.ConnectionError:
            logger.error("Elasticsearch connection error")
            return None

    def get(self, key):
        # Check if key is in cache
        if key in self.cache:
            return self.cache[key]

        # Try to get value from Redis
        value = self.get_from_redis(key)
        if value:
            self.cache[key] = value
            return value

        # Try to get value from CSV
        value = self.get_from_csv(key)
        if value:
            self.cache[key] = value
            return value

        # Try to get value from Elasticsearch
        value = self.get_from_elasticsearch(key)
        if value:
            self.cache[key] = value
            return value

        # If value is not found in any source, return None
        return None

    def set(self, key, value):
        # Set value in cache
        with self.cache_lock:
            self.cache[key] = value

        # Set value in Redis
        try:
            self.redis_client.set(key, value)
        except redis.exceptions.ConnectionError:
            logger.error("Redis connection error")

        # Set value in CSV
        try:
            with open(self.csv_file_path, 'a') as file:
                writer = csv.DictWriter(file, fieldnames=['key', 'value'])
                writer.writerow({'key': key, 'value': value})
        except FileNotFoundError:
            logger.error("CSV file not found")

        # Set value in Elasticsearch
        try:
            self.elasticsearch_client.index(index='cache', body={'key': key, 'value': value})
        except elasticsearch.exceptions.ConnectionError:
            logger.error("Elasticsearch connection error")

    def periodic_cache_cleanup(self):
        while True:
            # Sleep for 1 hour
            time.sleep(3600)

            # Clear cache
            with self.cache_lock:
                self.cache.clear()

            # Clear Redis cache
            try:
                self.redis_client.flushdb()
            except redis.exceptions.ConnectionError:
                logger.error("Redis connection error")

            # Clear CSV cache
            try:
                with open(self.csv_file_path, 'w') as file:
                    file.truncate()
            except FileNotFoundError:
                logger.error("CSV file not found")

            # Clear Elasticsearch cache
            try:
                self.elasticsearch_client.indices.delete(index='cache')
            except elasticsearch.exceptions.ConnectionError:
                logger.error("Elasticsearch connection error")

# Example usage
caching_system = CachingSystem('localhost', 6379, 'cache.csv', 'localhost:9200')
caching_system.set('key', 'value')
print(caching_system.get('key'))