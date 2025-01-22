import boto3
import json
import csv
import xml.etree.ElementTree as ET
import requests
from datetime import datetime, timedelta
import time
import os
import logging

# Logging setup (for debugging purposes)
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Data Models
class S3Bucket:
    def __init__(self, bucket_name, encryption_key=None):
        self.bucket_name = bucket_name
        self.s3 = boto3.client('s3')
        self.encryption_key = encryption_key  # TODO: Implement encryption key handling

    def list_objects(self):
        """Lists all objects in the S3 bucket."""
        try:
            response = self.s3.list_objects(Bucket=self.bucket_name)
            return response.get('Contents', [])
        except Exception as e:
            logger.error(f"Error listing objects in bucket {self.bucket_name}: {e}")
            return []

    def upload_file(self, file_path, key):
        """Uploads a file to the S3 bucket."""
        try:
            with open(file_path, 'rb') as f:
                self.s3.upload_fileobj(f, self.bucket_name, key)
            logger.info(f"File {file_path} uploaded to {self.bucket_name}/{key}")
        except FileNotFoundError:
            logger.error(f"File {file_path} not found")
        except Exception as e:
            logger.error(f"Error uploading file to bucket {self.bucket_name}: {e}")

    def download_file(self, key, dest_path):
        """Downloads a file from the S3 bucket."""
        try:
            with open(dest_path, 'wb') as f:
                self.s3.download_fileobj(self.bucket_name, key, f)
            logger.info(f"File {key} downloaded to {dest_path}")
        except Exception as e:
            logger.error(f"Error downloading file from bucket {self.bucket_name}: {e}")

class MessageQueue:
    def __init__(self, queue_url):
        self.sqs = boto3.client('sqs')
        self.queue_url = queue_url

    def send_message(self, message):
        """Sends a message to the queue."""
        try:
            response = self.sqs.send_message(QueueUrl=self.queue_url, MessageBody=message)
            logger.info(f"Message sent to queue {self.queue_url}: {response['MessageId']}")
        except Exception as e:
            logger.error(f"Error sending message to queue {self.queue_url}: {e}")

    def receive_message(self):
        """Receives a message from the queue."""
        try:
            response = self.sqs.receive_message(QueueUrl=self.queue_url, MaxNumberOfMessages=1, WaitTimeSeconds=20)
            messages = response.get('Messages', [])
            if messages:
                message = messages[0]
                receipt_handle = message['ReceiptHandle']
                self.sqs.delete_message(QueueUrl=self.queue_url, ReceiptHandle=receipt_handle)
                return message['Body']
            return None
        except Exception as e:
            logger.error(f"Error receiving message from queue {self.queue_url}: {e}")
            return None

class RESTAPI:
    def __init__(self, base_url, api_key):
        self.base_url = base_url
        self.api_key = api_key

    def get_data(self, endpoint):
        """Fetches data from the REST API."""
        url = f"{self.base_url}/{endpoint}"
        headers = {'Authorization': f'Bearer {self.api_key}'}
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP error: {e}")
            return None
        except Exception as e:
            logger.error(f"Error fetching data from {url}: {e}")
            return None

    def post_data(self, endpoint, data):
        """Posts data to the REST API."""
        url = f"{self.base_url}/{endpoint}"
        headers = {'Authorization': f'Bearer {self.api_key}', 'Content-Type': 'application/json'}
        try:
            response = requests.post(url, headers=headers, json=data)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP error: {e}")
            return None
        except Exception as e:
            logger.error(f"Error posting data to {url}: {e}")
            return None

# Feature Implementations
def encrypt_data(data, key):
    """Encrypts data using a simple XOR encryption."""
    encrypted = bytearray()
    for i in range(len(data)):
        encrypted.append(data[i] ^ key[i % len(key)])
    return encrypted

def decrypt_data(encrypted_data, key):
    """Decrypts data using a simple XOR decryption."""
    return encrypt_data(encrypted_data, key)  # TODO: This is a placeholder, should be a separate function

def generate_report(data, report_type):
    """Generates a report based on the data."""
    if report_type == 'json':
        with open('report.json', 'w') as f:
            json.dump(data, f, indent=4)
    elif report_type == 'csv':
        with open('report.csv', 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerows(data)
    elif report_type == 'xml':
        root = ET.Element("Report")
        for item in data:
            ET.SubElement(root, "Item").text = str(item)
        tree = ET.ElementTree(root)
        tree.write('report.xml')
    else:
        logger.error("Unsupported report type")
        return None

def filter_data(data, condition):
    """Filters data based on a condition."""
    return [item for item in data if condition(item)]

def schedule_task(task, interval):
    """Schedules a task to run at a specified interval."""
    while True:
        task()
        time.sleep(interval)

# Example Usage
def main():
    # S3 Bucket Example
    s3_bucket = S3Bucket('my-bucket')
    s3_bucket.upload_file('data.txt', 'data.txt')
    objects = s3_bucket.list_objects()
    for obj in objects:
        print(f"Object: {obj['Key']}")

    # Message Queue Example
    message_queue = MessageQueue('https://sqs.us-east-1.amazonaws.com/123456789012/my-queue')
    message_queue.send_message("Hello, World!")
    message = message_queue.receive_message()
    if message:
        print(f"Received message: {message}")

    # REST API Example
    rest_api = RESTAPI('https://api.example.com', 'my-api-key')
    data = rest_api.get_data('data')
    if data:
        print(f"Data from API: {data}")
        filtered_data = filter_data(data, lambda x: x['status'] == 'active')
        generate_report(filtered_data, 'json')

    # Scheduling Example
    def example_task():
        print("Running example task...")
        # Simulate a long-running task
        time.sleep(5)

    schedule_task(example_task, 10)

if __name__ == "__main__":
    main()