import boto3
import xml.etree.ElementTree as ET
import websockets
import pandas as pd
import time
import json
import gzip
from datetime import datetime
import os

# TODO: Refactor this into a proper config file
AWS_ACCESS_KEY = "AKIAXXXXXXXXXXXXXXXX"
AWS_SECRET_KEY = "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"

# FIXME: This should be moved to environment variables
DEBUG = True

# Poorly named global variable
x = 0

# Function with no documentation
def process_s3_bucket(bucket_name, file_key):
    try:
        s3 = boto3.client('s3', aws_access_key_id=AWS_ACCESS_KEY, aws_secret_access_key=AWS_SECRET_KEY)
        obj = s3.get_object(Bucket=bucket_name, Key=file_key)
        data = obj['Body'].read().decode('utf-8')
        return data
    except:
        print("Error fetching S3 object")  # Generic error message

# Function with detailed docstring
def parse_xml_file(xml_data):
    """
    Parses XML data and extracts relevant information.

    Args:
        xml_data (str): The XML data as a string.

    Returns:
        dict: A dictionary containing parsed data.
    """
    try:
        root = ET.fromstring(xml_data)
        data = {}
        for child in root:
            data[child.tag] = child.text
        return data
    except Exception as e:
        print(f"Error parsing XML: {e}")

# Function with unclear comments
def handle_websocket(uri):
    # This connects to the websocket
    async with websockets.connect(uri) as websocket:
        # TODO: Add authentication
        message = await websocket.recv()
        return message  # What if the connection fails?

# Function with mixed variable naming
def process_excel_sheet(file_path):
    df = pd.read_excel(file_path)  # Well-named variable
    temp = df.to_dict('records')  # Poorly named variable
    return temp

# Function with bare except clause
def compress_data(data):
    try:
        compressed = gzip.compress(data.encode('utf-8'))
        return compressed
    except:
        print("Compression failed")

# Function with duplicate code
def schedule_task(task, interval):
    while True:
        task()
        time.sleep(interval)

def schedule_task_2(task, interval):  # Duplicate of schedule_task
    while True:
        task()
        time.sleep(interval)

# Function with improper resource cleanup
def read_config(file_path):
    config_file = open(file_path, 'r')
    config = json.load(config_file)
    # FIXME: File is not closed
    return config

# Function with hardcoded values
def authenticate_user(username, password):
    if username == "admin" and password == "password123":  # Hardcoded credentials
        return True
    return False

# Function with debug print statements
def create_audit_trail(event):
    timestamp = datetime.now().isoformat()
    audit_log = f"{timestamp}: {event}"
    if DEBUG:
        print(f"Audit log: {audit_log}")  # Debug print statement
    return audit_log

# Main function with inconsistent logic flow
def main():
    # Process S3 bucket
    data = process_s3_bucket("my-bucket", "data.xml")  # Hardcoded bucket name and key
    if data:
        parsed_data = parse_xml_file(data)
        print(parsed_data)

    # Handle WebSocket
    ws_data = handle_websocket("ws://example.com/socket")  # Hardcoded URI
    if ws_data:
        print(ws_data)

    # Process Excel sheet
    excel_data = process_excel_sheet("data.xlsx")  # Hardcoded file path
    print(excel_data)

    # Compress data
    compressed = compress_data("Some data to compress")
    print(compressed)

    # Schedule task
    schedule_task(lambda: print("Task executed"), 5)

    # Authenticate user
    if authenticate_user("admin", "password123"):
        print("User authenticated")

    # Create audit trail
    create_audit_trail("Task completed")

if __name__ == "__main__":
    main()