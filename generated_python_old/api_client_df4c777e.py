import requests
import xml.etree.ElementTree as ET
import psycopg2
import boto3
import threading
import time
import logging
import os
from typing import Optional, List, Dict

# Logger setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants
POSTGRES_DSN = "dbname=test user=test password=test host=localhost port=5432"
S3_BUCKET_NAME = "my-bucket"
REST_API_URL = "https://api.example.com"
XML_FILE_PATH = "data.xml"

# External dependencies
import redis  # Note: This is an external package
from kafka import KafkaProducer  # Note: This is an external package

class APIClient:
    def __init__(self, dsn: str = POSTGRES_DSN, s3_bucket: str = S3_BUCKET_NAME):
        self.dsn = dsn
        self.s3_bucket = s3_bucket
        self.db_conn = None
        self.s3_client = None
        self.redis_client = redis.Redis(host='localhost', port=6379, db=0)  # Note: Hardcoded Redis connection
        self._lock = threading.Lock()
        self._session = requests.Session()
        self._producer = KafkaProducer(bootstrap_servers='localhost:9092')  # Note: Hardcoded Kafka connection
        self._last_processed_id = 0  # Note: Legacy attribute, not used in this version
        self._initialize_db()
        self._initialize_s3()

    def _initialize_db(self):
        try:
            self.db_conn = psycopg2.connect(self.dsn)
            self.db_conn.autocommit = True  # Note: Autocommit is set to True, which can lead to data inconsistency
            logger.info("Database connection established.")
        except Exception as e:
            logger.error(f"Failed to connect to database: {e}")

    def _initialize_s3(self):
        try:
            self.s3_client = boto3.client('s3')
            logger.info("S3 client initialized.")
        except Exception as e:
            logger.error(f"Failed to initialize S3 client: {e}")

    def _fetch_data_from_rest_api(self, endpoint: str) -> Optional[Dict]:
        try:
            response = self._session.get(f"{REST_API_URL}/{endpoint}")
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f"Error fetching data from REST API: {e}")
            return None

    def _fetch_data_from_xml(self, file_path: str = XML_FILE_PATH) -> Optional[List[Dict]]:
        try:
            tree = ET.parse(file_path)
            root = tree.getroot()
            data = []
            for item in root.findall('item'):
                data.append({
                    'id': item.find('id').text,
                    'name': item.find('name').text,
                    'value': item.find('value').text
                })
            return data
        except ET.ParseError as e:
            logger.error(f"Error parsing XML file: {e}")
            return None
        except FileNotFoundError as e:
            logger.error(f"XML file not found: {e}")
            return None

    def _store_data_in_postgres(self, data: List[Dict]):
        try:
            with self.db_conn.cursor() as cursor:
                for item in data:
                    cursor.execute(
                        "INSERT INTO my_table (id, name, value) VALUES (%s, %s, %s)",
                        (item['id'], item['name'], item['value'])
                    )
            logger.info("Data stored in PostgreSQL.")
        except psycopg2.DatabaseError as e:
            logger.error(f"Database error: {e}")
            # Note: No rollback or transaction management, leading to potential data inconsistency
        except Exception as e:
            logger.error(f"Error storing data in PostgreSQL: {e}")

    def _store_data_in_s3(self, data: List[Dict], key: str):
        try:
            data_str = '\n'.join([f"{item['id']},{item['name']},{item['value']}" for item in data])
            self.s3_client.put_object(Bucket=self.s3_bucket, Key=key, Body=data_str)
            logger.info(f"Data stored in S3 bucket at key: {key}")
        except Exception as e:
            logger.error(f"Error storing data in S3: {e}")

    def _handle_deadlock(self, cursor):
        # Note: This is a simple deadlock handler, which might not be effective in all cases
        try:
            cursor.execute("SET lock_timeout = '1s';")
        except psycopg2.DatabaseError as e:
            logger.error(f"Failed to set lock timeout: {e}")

    def _process_data(self, data: List[Dict]):
        # Note: This method does too many things and is not well-organized
        try:
            with self.db_conn.cursor() as cursor:
                self._handle_deadlock(cursor)
                for item in data:
                    cursor.execute(
                        "INSERT INTO my_table (id, name, value) VALUES (%s, %s, %s) ON CONFLICT (id) DO NOTHING",
                        (item['id'], item['name'], item['value'])
                    )
                    # Note: No transaction management, leading to potential data inconsistency
                    self.redis_client.set(f"item:{item['id']}", item['value'])  # Note: Storing data in Redis
                    self._producer.send('my-topic', key=item['id'].encode(), value=item['value'].encode())  # Note: Sending data to Kafka
            self._store_data_in_s3(data, 'data.csv')
        except Exception as e:
            logger.error(f"Error processing data: {e}")

    def fetch_and_store_data(self, endpoint: str):
        # Note: This method is a mix of business logic and technical implementation
        try:
            data = self._fetch_data_from_rest_api(endpoint)
            if not data:
                logger.warning("No data fetched from REST API.")
                return

            # Note: Legacy code pattern, commented-out code
            # if self._last_processed_id > 0:
            #     data = [item for item in data if item['id'] > self._last_processed_id]

            self._process_data(data)
            logger.info("Data processing completed.")
        except Exception as e:
            logger.error(f"Error fetching and storing data: {e}")

    def fetch_and_store_xml_data(self):
        # Note: This method is a mix of business logic and technical implementation
        try:
            data = self._fetch_data_from_xml()
            if not data:
                logger.warning("No data fetched from XML file.")
                return

            self._process_data(data)
            logger.info("XML data processing completed.")
        except Exception as e:
            logger.error(f"Error fetching and storing XML data: {e}")

    def backup_data(self, table_name: str, backup_key: str):
        # Note: This method is a mix of business logic and technical implementation
        try:
            with self.db_conn.cursor() as cursor:
                cursor.execute(f"SELECT * FROM {table_name}")
                rows = cursor.fetchall()
                data = [dict(zip([column[0] for column in cursor.description], row)) for row in rows]
                self._store_data_in_s3(data, backup_key)
                logger.info(f"Data from table {table_name} backed up to S3 at key: {backup_key}")
        except Exception as e:
            logger.error(f"Error backing up data: {e}")

    def generate_report(self, report_type: str) -> Optional[str]:
        # Note: This method is a mix of business logic and technical implementation
        try:
            if report_type == 'daily':
                report_key = 'daily_report.csv'
            elif report_type == 'monthly':
                report_key = 'monthly_report.csv'
            else:
                logger.warning("Invalid report type.")
                return None

            with self.db_conn.cursor() as cursor:
                cursor.execute("SELECT * FROM my_table WHERE created_at >= %s", (self._get_last_month(),))
                rows = cursor.fetchall()
                data = [dict(zip([column[0] for column in cursor.description], row)) for row in rows]
                self._store_data_in_s3(data, report_key)
                logger.info(f"Report generated and stored in S3 at key: {report_key}")
                return report_key
        except Exception as e:
            logger.error(f"Error generating report: {e}")
            return None

    def _get_last_month(self) -> str:
        # Note: This method is a workaround for external system limitations
        return (time.strftime('%Y-%m-01', time.gmtime()) + ' 00:00:00')  # Note: Potential timezone issues

    def schedule_task(self, task: str, interval: int):
        # Note: This method is a mix of business logic and technical implementation
        def task_runner():
            while True:
                if task == 'fetch_and_store_data':
                    self.fetch_and_store_data('data')
                elif task == 'fetch_and_store_xml_data':
                    self.fetch_and_store_xml_data()
                elif task == 'backup_data':
                    self.backup_data('my_table', 'backup.csv')
                elif task == 'generate_report':
                    self.generate_report('daily')
                else:
                    logger.warning("Invalid task.")
                    break
                time.sleep(interval)

        thread = threading.Thread(target=task_runner)
        thread.start()
        logger.info(f"Task {task} scheduled to run every {interval} seconds.")

    def close(self):
        # Note: This method is a mix of business logic and technical implementation
        try:
            if self.db_conn:
                self.db_conn.close()
                logger.info("Database connection closed.")
            if self._producer:
                self._producer.close()
                logger.info("Kafka producer closed.")
            if self._session:
                self._session.close()
                logger.info("HTTP session closed.")
        except Exception as e:
            logger.error(f"Error closing resources: {e}")

# Example usage
if __name__ == "__main__":
    client = APIClient()
    client.fetch_and_store_data('data')
    client.fetch_and_store_xml_data()
    client.backup_data('my_table', 'backup.csv')
    client.generate_report('daily')
    client.schedule_task('fetch_and_store_data', 3600)  # Schedule task to run every hour
    client.close()