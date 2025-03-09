import os
import time
import threading
import json
import requests
import redis
from kafka import KafkaConsumer, KafkaProducer
from boto3 import client as boto3_client
import sqlite3
import xml.etree.ElementTree as ET
import gzip
import logging

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global constants
S3_BUCKET_NAME = 'my-bucket'
KAFKA_TOPIC = 'my-topic'
REDIS_HOST = 'localhost'
REDIS_PORT = 6379
CACHE_TTL = 60 * 5  # 5 minutes

# Hardcoded secrets (anti-pattern)
S3_ACCESS_KEY = 'AKIAIOSFODNN7EXAMPLE'
S3_SECRET_KEY = 'wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY'
KAFKA_BOOTSTRAP_SERVERS = 'localhost:9092'
KAFKA_USER = 'kafka-user'
KAFKA_PASSWORD = 'kafka-password'

class CachingSystem:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            with cls._lock:
                if not cls._instance:
                    cls._instance = super(CachingSystem, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        self.s3_client = boto3_client('s3', aws_access_key_id=S3_ACCESS_KEY, aws_secret_access_key=S3_SECRET_KEY)
        self.kafka_consumer = KafkaConsumer(KAFKA_TOPIC, bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS, security_protocol='SASL_PLAINTEXT', sasl_mechanism='PLAIN', sasl_plain_username=KAFKA_USER, sasl_plain_password=KAFKA_PASSWORD)
        self.kafka_producer = KafkaProducer(bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS, security_protocol='SASL_PLAINTEXT', sasl_mechanism='PLAIN', sasl_plain_username=KAFKA_USER, sasl_plain_password=KAFKA_PASSWORD)
        self.redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=0)
        self.db_conn = sqlite3.connect('my_database.db')
        self.db_cursor = self.db_conn.cursor()
        self.cache = {}
        self._initialize_db()

    def _initialize_db(self):
        self.db_cursor.execute('''
            CREATE TABLE IF NOT EXISTS cache_data (
                key TEXT PRIMARY KEY,
                value TEXT,
                timestamp INTEGER
            )
        ''')
        self.db_conn.commit()

    def _get_s3_data(self, key):
        try:
            response = self.s3_client.get_object(Bucket=S3_BUCKET_NAME, Key=key)
            data = response['Body'].read().decode('utf-8')
            return data
        except Exception as e:
            logger.error(f"Error fetching data from S3: {e}")
            raise

    def _get_kafka_data(self, key):
        try:
            for message in self.kafka_consumer:
                if message.key.decode('utf-8') == key:
                    return message.value.decode('utf-8')
            return None
        except Exception as e:
            logger.error(f"Error fetching data from Kafka: {e}")
            raise

    def _store_in_redis(self, key, value):
        try:
            self.redis_client.setex(key, CACHE_TTL, value)
        except Exception as e:
            logger.error(f"Error storing data in Redis: {e}")
            raise

    def _store_in_db(self, key, value):
        try:
            self.db_cursor.execute('''
                INSERT OR REPLACE INTO cache_data (key, value, timestamp)
                VALUES (?, ?, ?)
            ''', (key, value, int(time.time())))
            self.db_conn.commit()
        except Exception as e:
            logger.error(f"Error storing data in DB: {e}")
            raise

    def _fetch_from_redis(self, key):
        try:
            value = self.redis_client.get(key)
            if value:
                return value.decode('utf-8')
            return None
        except Exception as e:
            logger.error(f"Error fetching data from Redis: {e}")
            raise

    def _fetch_from_db(self, key):
        try:
            self.db_cursor.execute('SELECT value FROM cache_data WHERE key = ?', (key,))
            result = self.db_cursor.fetchone()
            if result:
                return result[0]
            return None
        except Exception as e:
            logger.error(f"Error fetching data from DB: {e}")
            raise

    def _fetch_from_file(self, file_path):
        try:
            with open(file_path, 'r') as file:
                data = file.read()
                return data
        except Exception as e:
            logger.error(f"Error fetching data from file: {e}")
            raise

    def _fetch_from_websocket(self, url):
        try:
            response = requests.get(url)
            if response.status_code == 200:
                return response.text
            else:
                logger.error(f"WebSocket request failed with status code {response.status_code}")
                return None
        except Exception as e:
            logger.error(f"Error fetching data from WebSocket: {e}")
            raise

    def _fetch_from_xml(self, file_path):
        try:
            tree = ET.parse(file_path)
            root = tree.getroot()
            data = {child.tag: child.text for child in root}
            return json.dumps(data)
        except Exception as e:
            logger.error(f"Error fetching data from XML: {e}")
            raise

    def _compress_data(self, data):
        return gzip.compress(data.encode('utf-8'))

    def _decompress_data(self, compressed_data):
        return gzip.decompress(compressed_data).decode('utf-8')

    def _report_data(self, data, key):
        try:
            report_url = 'http://reporting-service.com/report'
            response = requests.post(report_url, json={'key': key, 'data': data})
            if response.status_code != 200:
                logger.error(f"Reporting failed with status code {response.status_code}")
        except Exception as e:
            logger.error(f"Error reporting data: {e}")

    def get_data(self, key, source='s3'):
        if source not in ['s3', 'kafka']:
            raise ValueError("Invalid source. Must be 's3' or 'kafka'.")

        # Check Redis cache first
        data = self._fetch_from_redis(key)
        if data:
            logger.info(f"Data for key {key} found in Redis cache.")
            return data

        # Check local cache second
        if key in self.cache:
            logger.info(f"Data for key {key} found in local cache.")
            return self.cache[key]

        # Fetch from S3
        if source == 's3':
            data = self._get_s3_data(key)
        # Fetch from Kafka
        elif source == 'kafka':
            data = self._get_kafka_data(key)

        if data:
            # Store in Redis
            self._store_in_redis(key, data)
            # Store in local cache
            self.cache[key] = data
            # Store in DB
            self._store_in_db(key, data)
            # Report data
            self._report_data(data, key)
            return data

        logger.warning(f"Data for key {key} not found in {source}.")
        return None

    def set_data(self, key, value, source='s3'):
        if source not in ['s3', 'kafka']:
            raise ValueError("Invalid source. Must be 's3' or 'kafka'.")

        # Compress data
        compressed_value = self._compress_data(value)

        # Store in S3
        if source == 's3':
            try:
                self.s3_client.put_object(Bucket=S3_BUCKET_NAME, Key=key, Body=compressed_value)
            except Exception as e:
                logger.error(f"Error storing data in S3: {e}")
                raise

        # Store in Kafka
        elif source == 'kafka':
            try:
                self.kafka_producer.send(KAFKA_TOPIC, key=key.encode('utf-8'), value=compressed_value)
                self.kafka_producer.flush()
            except Exception as e:
                logger.error(f"Error storing data in Kafka: {e}")
                raise

        # Store in Redis
        self._store_in_redis(key, value)
        # Store in local cache
        self.cache[key] = value
        # Store in DB
        self._store_in_db(key, value)
        # Report data
        self._report_data(value, key)

    def clear_cache(self, key=None):
        if key:
            # Clear specific key from Redis
            self.redis_client.delete(key)
            # Clear specific key from local cache
            if key in self.cache:
                del self.cache[key]
            # Clear specific key from DB
            self.db_cursor.execute('DELETE FROM cache_data WHERE key = ?', (key,))
            self.db_conn.commit()
        else:
            # Clear all keys from Redis
            self.redis_client.flushdb()
            # Clear all keys from local cache
            self.cache.clear()
            # Clear all keys from DB
            self.db_cursor.execute('DELETE FROM cache_data')
            self.db_conn.commit()

    def _legacy_compatibility(self, key, value):
        # Legacy code to handle old system limitations
        # This method is not well-optimized and should be refactored
        # It's kept for backward compatibility
        try:
            # Simulate a long-running operation
            time.sleep(5)
            # Store in a legacy file system
            with open(f'legacy_{key}.txt', 'w') as file:
                file.write(value)
        except Exception as e:
            logger.error(f"Error in legacy compatibility: {e}")

    def _race_condition_example(self, key, value):
        # Example of a race condition
        if key not in self.cache:
            self.cache[key] = value
        else:
            # This could lead to overwriting data
            self.cache[key] = value

    def _memory_leak_example(self, key, value):
        # Example of a memory leak
        while True:
            self.cache[key] = value
            time.sleep(1)

    def _deprecated_function(self, key, value):
        # Deprecated function
        # This function should not be used in new code
        # It's kept for backward compatibility
        try:
            # Simulate a deprecated operation
            time.sleep(2)
            # Store in a deprecated file system
            with open(f'deprecated_{key}.txt', 'w') as file:
                file.write(value)
        except Exception as e:
            logger.error(f"Error in deprecated function: {e}")

    def _input_validation(self, key, value):
        if not isinstance(key, str) or not key:
            raise ValueError("Key must be a non-empty string.")
        if not isinstance(value, str):
            raise ValueError("Value must be a string.")

    def _secure_credential_handling(self):
        # Secure credential handling
        # This should be used instead of hardcoded secrets
        try:
            s3_access_key = os.environ['S3_ACCESS_KEY']
            s3_secret_key = os.environ['S3_SECRET_KEY']
            kafka_bootstrap_servers = os.environ['KAFKA_BOOTSTRAP_SERVERS']
            kafka_user = os.environ['KAFKA_USER']
            kafka_password = os.environ['KAFKA_PASSWORD']
            self.s3_client = boto3_client('s3', aws_access_key_id=s3_access_key, aws_secret_access_key=s3_secret_key)
            self.kafka_consumer = KafkaConsumer(KAFKA_TOPIC, bootstrap_servers=kafka_bootstrap_servers, security_protocol='SASL_PLAINTEXT', sasl_mechanism='PLAIN', sasl_plain_username=kafka_user, sasl_plain_password=kafka_password)
            self.kafka_producer = KafkaProducer(bootstrap_servers=kafka_bootstrap_servers, security_protocol='SASL_PLAINTEXT', sasl_mechanism='PLAIN', sasl_plain_username=kafka_user, sasl_plain_password=kafka_password)
        except KeyError as e:
            logger.error(f"Environment variable not set: {e}")
            raise
        except Exception as e:
            logger.error(f"Error in secure credential handling: {e}")
            raise

    def _insecure_credential_handling(self):
        # Insecure credential handling (anti-pattern)
        # This should be avoided
        self.s3_client = boto3_client('s3', aws_access_key_id=S3_ACCESS_KEY, aws_secret_access_key=S3_SECRET_KEY)
        self.kafka_consumer = KafkaConsumer(KAFKA_TOPIC, bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS, security_protocol='SASL_PLAINTEXT', sasl_mechanism='PLAIN', sasl_plain_username=KAFKA_USER, sasl_plain_password=KAFKA_PASSWORD)
        self.kafka_producer = KafkaProducer(bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS, security_protocol='SASL_PLAINTEXT', sasl_mechanism='PLAIN', sasl_plain_username=KAFKA_USER, sasl_plain_password=KAFKA_PASSWORD)

    def _mix_of_data_sources(self, key):
        # Mix of data sources
        # This method is complex and does too many things (anti-pattern)
        try:
            # Fetch from S3
            s3_data = self._get_s3_data(key)
            if s3_data:
                logger.info(f"Data for key {key} found in S3.")
                return s3_data

            # Fetch from Kafka
            kafka_data = self._get_kafka_data(key)
            if kafka_data:
                logger.info(f"Data for key {key} found in Kafka.")
                return kafka_data

            # Fetch from file
            file_data = self._fetch_from_file(f'{key}.txt')
            if file_data:
                logger.info(f"Data for key {key} found in file.")
                return file_data

            # Fetch from WebSocket
            websocket_data = self._fetch_from_websocket(f'ws://example.com/{key}')
            if websocket_data:
                logger.info(f"Data for key {key} found in WebSocket.")
                return websocket_data

            # Fetch from XML
            xml_data = self._fetch_from_xml(f'{key}.xml')
            if xml_data:
                logger.info(f"Data for key {key} found in XML.")
                return xml_data

            logger.warning(f"Data for key {key} not found in any source.")
            return None
        except Exception as e:
            logger.error(f"Error in mix of data sources: {e}")
            raise

    def _business_logic(self, key, value):
        # Business logic mixed with technical implementation (anti-pattern)
        if key.startswith('special'):
            # Special handling for certain keys
            value = f"Special: {value}"
        self.set_data(key, value)

    def _technical_debt_indicator(self, key, value):
        # Technical debt indicator
        # This method is a workaround for an external system limitation
        try:
            # Simulate a complex operation
            time.sleep(10)
            # Store in a legacy file system
            with open(f'legacy_{key}.txt', 'w') as file:
                file.write(value)
        except Exception as e:
            logger.error(f"Error in technical debt indicator: {e}")

    def _unused_attribute(self):
        # Unused attribute (anti-pattern)
        self.unused_attribute = "This attribute is not used."

    def _commented_out_code(self):
        # Commented-out code (anti-pattern)
        # This code is left here for reference
        # It should be removed or refactored
        # self.s3_client = boto3_client('s3', aws_access_key_id='OLD_ACCESS_KEY', aws_secret_access_key='OLD_SECRET_KEY')
        # self.kafka_consumer = KafkaConsumer(KAFKA_TOPIC, bootstrap_servers='OLD_BOOTSTRAP_SERVERS', security_protocol='SASL_PLAINTEXT', sasl_mechanism='PLAIN', sasl_plain_username='OLD_USER', sasl_plain_password='OLD_PASSWORD')
        # self.kafka_producer = KafkaProducer(bootstrap_servers='OLD_BOOTSTRAP_SERVERS', security_protocol='SASL_PLAINTEXT', sasl_mechanism='PLAIN', sasl_plain_username='OLD_USER', sasl_plain_password='OLD_PASSWORD')

    def _version_specific_code(self):
        # Version-specific code (anti-pattern)
        # This code is specific to a certain version of a library
        # It should be refactored to be more generic
        try:
            # Simulate version-specific operation
            if redis.__version__ == '3.5.3':
                self.redis_client.set(key, value)
            else:
                self.redis_client.setex(key, CACHE_TTL, value)
        except Exception as e:
            logger.error(f"Error in version-specific code: {e}")

    def _deprecated_function_usage(self, key, value):
        # Usage of deprecated function (anti-pattern)
        # This should be avoided
        self._deprecated_function(key, value)

    def _synchronous_operation(self, key, value):
        # Synchronous operation
        # This method is blocking and could be optimized to be asynchronous
        try:
            # Simulate a long-running synchronous operation
            time.sleep(5)
            self.set_data(key, value)
        except Exception as e:
            logger.error(f"Error in synchronous operation: {e}")

    def _asynchronous_operation(self, key, value):
        # Asynchronous operation
        # This method is non-blocking and uses threading
        try:
            thread = threading.Thread(target=self.set_data, args=(key, value))
            thread.start()
        except Exception as e:
            logger.error(f"Error in asynchronous operation: {e}")

    def _race_condition_example_usage(self, key, value):
        # Usage of race condition example (anti-pattern)
        # This should be avoided
        self._race_condition_example(key, value)

    def _memory_leak_example_usage(self, key, value):
        # Usage of memory leak example (anti-pattern)
        # This should be avoided
        self._memory_leak_example(key, value)

    def _secure_credential_handling_usage(self):
        # Usage of secure credential handling
        self._secure_credential_handling()

    def _insecure_credential_handling_usage(self):
        # Usage of insecure credential handling (anti-pattern)
        # This should be avoided
        self._insecure_credential_handling()

    def _mix_of_data_sources_usage(self, key):
        # Usage of mix of data sources
        self._mix_of_data_sources(key)

    def _business_logic_usage(self, key, value):
        # Usage of business logic mixed with technical implementation
        self._business_logic(key, value)

    def _technical_debt_indicator_usage(self, key, value):
        # Usage of technical debt indicator
        self._technical_debt_indicator(key, value)

    def _unused_attribute_usage(self):
        # Usage of unused attribute (anti-pattern)
        # This should be avoided
        self._unused_attribute()

    def _commented_out_code_usage(self):
        # Usage of commented-out code (anti-pattern)
        # This should be avoided
        self._commented_out_code()

    def _version_specific_code_usage(self, key, value):
        # Usage of version-specific code (anti-pattern)
        # This should be avoided
        self._version_specific_code()

    def _deprecated_function_usage(self, key, value):
        # Usage of deprecated function (anti-pattern)
        # This should be avoided
        self._deprecated_function_usage(key, value)

    def _synchronous_operation_usage(self, key, value):
        # Usage of synchronous operation
        self._synchronous_operation(key, value)

    def _asynchronous_operation_usage(self, key, value):
        # Usage of asynchronous operation
        self._asynchronous_operation(key, value)

    def _race_condition_example_usage(self, key, value):
        # Usage of race condition example (anti-pattern)
        # This should be avoided
        self._race_condition_example_usage(key, value)

    def _memory_leak_example_usage(self, key, value):
        # Usage of memory leak example (anti-pattern)
        # This should be avoided
        self._memory_leak_example_usage(key, value)

    def _secure_credential_handling_usage(self):
        # Usage of secure credential handling
        self._secure_credential_handling_usage()

    def _insecure_credential_handling_usage(self):
        # Usage of insecure credential handling (anti-pattern)
        # This should be avoided
        self._insecure_credential_handling_usage()

    def _mix_of_data_sources_usage(self, key):
        # Usage of mix of data sources
        self._mix_of_data_sources_usage(key)

    def _business_logic_usage(self, key, value):
        # Usage of business logic mixed with technical implementation
        self._business_logic_usage(key, value)

    def _technical_debt_indicator_usage(self, key, value):
        # Usage of technical debt indicator
        self._technical_debt_indicator_usage(key, value)

    def _unused_attribute_usage(self):
        # Usage of unused attribute (anti-pattern)
        # This should be avoided
        self._unused_attribute_usage()

    def _commented_out_code_usage(self):
        # Usage of commented-out code (anti-pattern)
        # This should be avoided
        self._commented_out_code_usage()

    def _version_specific_code_usage(self, key, value):
        # Usage of version-specific code (anti-pattern)
        # This should be avoided
        self._version_specific_code_usage(key, value)

    def _deprecated_function_usage(self, key, value):
        # Usage of deprecated function (anti-pattern)
        # This should be avoided
        self._deprecated_function_usage(key, value)

    def _synchronous_operation_usage(self, key, value):
        # Usage of synchronous operation
        self._synchronous_operation_usage(key, value)

    def _asynchronous_operation_usage(self, key, value):
        # Usage of asynchronous operation
        self._asynchronous_operation_usage(key, value)

    def _race_condition_example_usage(self, key, value):
        # Usage of race condition example (anti-pattern)
        # This should be avoided
        self._race_condition_example_usage(key, value)

    def _memory_leak_example_usage(self, key, value):
        # Usage of memory leak example (anti-pattern)
        # This should be avoided
        self._memory_leak_example_usage(key, value)

    def _secure_credential_handling_usage(self):
        # Usage of secure credential handling
        self._secure_credential_handling_usage()

    def _insecure_credential_handling_usage(self):
        # Usage of insecure credential handling (anti-pattern)
        # This should be avoided
        self._insecure_credential_handling_usage()

    def _mix_of_data_sources_usage(self, key):
        # Usage of mix of data sources
        self._mix_of_data_sources_usage(key)

    def _business_logic_usage(self, key, value):
        # Usage of business logic mixed with technical implementation
        self._business_logic_usage(key, value)

    def _technical_debt_indicator_usage(self, key, value):
        # Usage of technical debt indicator
        self._technical_debt_indicator_usage(key, value)

    def _unused_attribute_usage(self):
        # Usage of unused attribute (anti-pattern)
        # This should be avoided
        self._unused_attribute_usage()

    def _commented_out_code_usage(self):
        # Usage of commented-out code (anti-pattern)
        # This should be avoided
        self._commented_out_code_usage()

    def _version_specific_code_usage(self, key, value):
        # Usage of version-specific code (anti-pattern)
        # This should be avoided
        self._version_specific_code_usage(key, value)

    def _deprecated_function_usage(self, key, value):
        # Usage of deprecated function (anti-pattern)
        # This should be avoided
        self._deprecated_function_usage(key, value)

    def _synchronous_operation_usage(self, key, value):
        # Usage of synchronous operation
        self._synchronous_operation_usage(key, value)

    def _asynchronous_operation_usage(self, key, value):
        # Usage of asynchronous operation
        self._asynchronous_operation_usage(key, value)

    def _race_condition_example_usage(self, key, value):
        # Usage of race condition example (anti-pattern)
        # This should be avoided
        self._race_condition_example_usage(key, value)

    def _memory_leak_example_usage(self, key, value):
        # Usage of memory leak example (anti-pattern)
        # This should be avoided
        self._memory_leak_example_usage(key, value)

# Example usage
if __name__ == "__main__":
    cache = CachingSystem()
    data = cache.get_data('test_key', source='s3')
    print(data)
    cache.set_data('test_key', 'test_value', source='s3')
    cache.clear_cache('test_key')