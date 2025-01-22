import os
import threading
import time
from datetime import datetime
import psycopg2
import boto3
import websocket
import json
from kafka import KafkaConsumer
from pymongo import MongoClient
import redis

# Class variables
DB_HOST = 'localhost'
DB_USER = 'postgres'
DB_PASSWORD = 'password123'  # hardcoded password
DB_NAME = 'mydatabase'

# Unused attribute
UNUSED_ATTRIBUTE = 'This attribute is not used anywhere'

class DataModel:
    def __init__(self):
        # Instance variables
        self.postgresql_connection = None
        self.s3_bucket = None
        self.websocket_stream = None
        self.kafka_consumer = None
        self.mongo_client = None
        self.redis_client = None

    def connect_to_postgresql(self):
        try:
            self.postgresql_connection = psycopg2.connect(
                host=DB_HOST,
                user=DB_USER,
                password=DB_PASSWORD,
                database=DB_NAME
            )
        except psycopg2.OperationalError as e:
            print(f'Failed to connect to PostgreSQL: {e}')

    def connect_to_s3(self):
        self.s3_bucket = boto3.resource('s3', aws_access_key_id='AKIAIOSFODNN7EXAMPLE',
                                        aws_secret_access_key='wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY')

    def connect_to_websocket(self):
        self.websocket_stream = websocket.WebSocket()
        self.websocket_stream.connect('ws://localhost:8080')

    def connect_to_kafka(self):
        self.kafka_consumer = KafkaConsumer('mytopic', bootstrap_servers=['localhost:9092'])

    def connect_to_mongo(self):
        self.mongo_client = MongoClient('mongodb://localhost:27017/')

    def connect_to_redis(self):
        self.redis_client = redis.Redis(host='localhost', port=6379, db=0)

    # Long method that does too many things
    def process_data(self):
        # Connect to PostgreSQL
        self.connect_to_postgresql()

        # Fetch data from PostgreSQL
        cursor = self.postgresql_connection.cursor()
        cursor.execute('SELECT * FROM mytable')
        data = cursor.fetchall()

        # Process data
        processed_data = []
        for row in data:
            # Do some processing
            processed_row = {
                'id': row[0],
                'name': row[1],
                'age': row[2]
            }
            processed_data.append(processed_row)

        # Write data to S3
        self.connect_to_s3()
        s3_object = self.s3_bucket.Object('mybucket', 'data.json')
        s3_object.put(Body=json.dumps(processed_data))

        # Send data to WebSocket
        self.connect_to_websocket()
        self.websocket_stream.send(json.dumps(processed_data))

        # Write data to Kafka
        self.connect_to_kafka()
        for row in processed_data:
            self.kafka_consumer.send('mytopic', value=json.dumps(row).encode('utf-8'))

        # Write data to MongoDB
        self.connect_to_mongo()
        db = self.mongo_client['mydatabase']
        collection = db['mycollection']
        collection.insert_many(processed_data)

        # Write data to Redis
        self.connect_to_redis()
        for row in processed_data:
            self.redis_client.set(row['id'], json.dumps(row))

    # Method with possible thread safety issue
    def increment_counter(self):
        counter = self.redis_client.get('counter')
        if counter is None:
            self.redis_client.set('counter', 0)
            counter = 0
        else:
            counter = int(counter)
        self.redis_client.set('counter', counter + 1)

    # Method with occasional memory leak
    def fetch_data_from_api(self):
        import requests
        response = requests.get('https://api.example.com/data')
        data = response.json()
        # Do some processing
        processed_data = []
        for row in data:
            processed_row = {
                'id': row['id'],
                'name': row['name'],
                'age': row['age']
            }
            processed_data.append(processed_row)
        return processed_data

    # Commented-out code
    # def connect_to_sqlite(self):
    #     self.sqlite_connection = sqlite3.connect('mydatabase.db')

    # Method with hardcoded secret
    def send_data_to_api(self, data):
        import requests
        headers = {
            'Authorization': 'Bearer mysecrettoken'
        }
        response = requests.post('https://api.example.com/data', headers=headers, json=data)

    # Method with varying levels of input validation
    def validate_input(self, input_data):
        if not isinstance(input_data, dict):
            return False
        if 'id' not in input_data or 'name' not in input_data or 'age' not in input_data:
            return False
        if not isinstance(input_data['id'], int) or not isinstance(input_data['name'], str) or not isinstance(input_data['age'], int):
            return False
        return True

    # Method with mix of secure and insecure defaults
    def connect_to_database(self, host='localhost', user='root', password='password123', database='mydatabase'):
        import mysql.connector
        self.database_connection = mysql.connector.connect(
            host=host,
            user=user,
            password=password,
            database=database
        )

    # Method with deprecated function
    def fetch_data_from_database(self):
        import MySQLdb
        db = MySQLdb.connect(host='localhost', user='root', passwd='password123', db='mydatabase')
        cursor = db.cursor()
        cursor.execute('SELECT * FROM mytable')
        data = cursor.fetchall()
        return data

# Usage
data_model = DataModel()
data_model.process_data()

# Possible race condition
thread1 = threading.Thread(target=data_model.increment_counter)
thread2 = threading.Thread(target=data_model.increment_counter)
thread1.start()
thread2.start()

# Occasional memory leak
for _ in range(1000):
    data_model.fetch_data_from_api()