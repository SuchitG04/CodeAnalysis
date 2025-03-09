import os
import json
import boto3
import requests
import sqlite3
from threading import Thread
import time
from typing import List

# Class variable, not instance variable, to store database connections
database_connections = {}

class TaskProcessor:
    # Hardcoded secrets, not ideal
    AWS_ACCESS_KEY = 'YOUR_AWS_ACCESS_KEY'
    AWS_SECRET_KEY = 'YOUR_AWS_SECRET_KEY'

    def __init__(self):
        # Mix of instance and class variables
        self.s3_client = boto3.client('s3', aws_access_key_id=self.AWS_ACCESS_KEY,
                                    aws_secret_access_key=self.AWS_SECRET_KEY)
        self.notification_url = 'https://example.com/notify'
        # Unused attribute, potential memory leak
        self.unused_attribute = []

    # Well-organized method
    def process_s3_bucket(self, bucket_name: str):
        """Process an S3 bucket"""
        try:
            # Synchronous operation, potential performance issue
            objects = self.s3_client.list_objects(Bucket=bucket_name)
            for obj in objects['Contents']:
                self.process_s3_object(bucket_name, obj['Key'])
        except Exception as e:
            # Error retry, but no limit on retries
            self.process_s3_bucket(bucket_name)

    # Long method, does too many things
    def process_s3_object(self, bucket_name: str, object_key: str):
        """Process an S3 object"""
        try:
            # Synchronous operation, potential performance issue
            obj = self.s3_client.get_object(Bucket=bucket_name, Key=object_key)
            data = json.loads(obj['Body'].read())
            # Mix of secure and insecure defaults
            if 'encryption' in data and data['encryption']:
                # Data encryption, but hardcoded secret
                encrypted_data = self.encrypt_data(data, 'YOUR_ENCRYPTION_SECRET')
                self.save_to_database(encrypted_data)
            else:
                self.save_to_database(data)
            # Notification, but no error handling
            self.send_notification(f'Processed {object_key}')
        except Exception as e:
            # Error handling, but no logging
            print(f'Error processing {object_key}: {str(e)}')

    # Method with potential thread safety issues
    def save_to_database(self, data: dict):
        """Save data to database"""
        # Mix of explicit and implicit dependencies
        if 'database' not in database_connections:
            database_connections['database'] = sqlite3.connect('database.db')
        cursor = database_connections['database'].cursor()
        # Potential SQL injection vulnerability
        cursor.execute('INSERT INTO data VALUES (%s)' % json.dumps(data))
        database_connections['database'].commit()

    # Method with potential memory leak
    def encrypt_data(self, data: dict, secret: str) -> dict:
        """Encrypt data"""
        # Mix of standard library and external packages
        import hashlib
        encrypted_data = {}
        for key, value in data.items():
            encrypted_data[key] = hashlib.sha256((value + secret).encode()).hexdigest()
        # Unused variable, potential memory leak
        unused_variable = []
        return encrypted_data

    # Method with deprecated function
    def send_notification(self, message: str):
        """Send notification"""
        # Mix of secure and insecure defaults
        requests.post(self.notification_url, data={'message': message}, verify=False)

    # Commented-out code, potential technical debt
    # def process_json_file(self, file_path: str):
    #     """Process a JSON file"""
    #     with open(file_path, 'r') as f:
    #         data = json.load(f)
    #     # ...

    # Method with potential race condition
    def backup_data(self):
        """Backup data"""
        # Mix of synchronous and asynchronous operations
        thread = Thread(target=self._backup_data)
        thread.start()

    def _backup_data(self):
        """Backup data asynchronously"""
        # Potential performance issue
        time.sleep(10)
        # Mix of explicit and implicit dependencies
        import shutil
        shutil.copy('database.db', 'backup.db')

def main():
    task_processor = TaskProcessor()
    # Mix of explicit and implicit dependencies
    import boto3
    s3 = boto3.client('s3')
    buckets = s3.list_buckets()
    for bucket in buckets['Buckets']:
        task_processor.process_s3_bucket(bucket['Name'])

if __name__ == '__main__':
    main()