import os
import json
import xml.etree.ElementTree as ET
import requests
from kafka import KafkaConsumer, KafkaProducer
from pymongo import MongoClient
from ftplib import FTP
import logging
import time

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Hardcoded credentials (bad practice, but common in real-world code)
KAFKA_BROKERS = ['localhost:9092']
FTP_SERVER = 'ftp.example.com'
FTP_USER = 'user'
FTP_PASS = 'pass'
MONGO_URI = 'mongodb://localhost:27017/'
MONGO_DB = 'data_db'
MONGO_COLLECTION = 'data_collection'

# Kafka consumer and producer setup
def setup_kafka_consumer(topic):
    return KafkaConsumer(topic, bootstrap_servers=KAFKA_BROKERS, auto_offset_reset='earliest')

def setup_kafka_producer():
    return KafkaProducer(bootstrap_servers=KAFKA_BROKERS)

# FTP server setup
def setup_ftp_server():
    ftp = FTP(FTP_SERVER)
    ftp.login(FTP_USER, FTP_PASS)
    return ftp

# MongoDB setup
def setup_mongo_db():
    client = MongoClient(MONGO_URI)
    db = client[MONGO_DB]
    return db

# Function to process Kafka messages
def process_kafka_messages(consumer, producer, collection):
    for msg in consumer:
        try:
            data = json.loads(msg.value.decode('utf-8'))
            logging.info(f"Processing message: {data}")
            # Simulate some data processing
            processed_data = process_data(data)
            # Save processed data to MongoDB
            collection.insert_one(processed_data)
            # Send processed data to another Kafka topic
            producer.send('processed_topic', json.dumps(processed_data).encode('utf-8'))
        except json.JSONDecodeError as e:
            logging.error(f"Failed to decode JSON: {e}")
        except Exception as e:
            logging.error(f"An error occurred: {e}")

# Function to process data (simulate some processing logic)
def process_data(data):
    # TODO: This function needs to be optimized for performance
    # FIXME: Handle more data types
    temp = data['value'] * 2
    return {
        'original_value': data['value'],
        'processed_value': temp,
        'timestamp': time.time()
    }

# Function to download XML files from FTP server
def download_xml_files(ftp, remote_dir, local_dir):
    if not os.path.exists(local_dir):
        os.makedirs(local_dir)
    ftp.cwd(remote_dir)
    files = ftp.nlst()
    for file in files:
        if file.endswith('.xml'):
            try:
                local_path = os.path.join(local_dir, file)
                with open(local_path, 'wb') as f:
                    ftp.retrbinary(f'RETR {file}', f.write)
                logging.info(f"Downloaded {file} to {local_path}")
            except Exception as e:
                logging.error(f"Failed to download {file}: {e}")

# Function to parse XML files
def parse_xml_files(local_dir):
    for file in os.listdir(local_dir):
        if file.endswith('.xml'):
            try:
                tree = ET.parse(os.path.join(local_dir, file))
                root = tree.getroot()
                for item in root.findall('item'):
                    data = {
                        'id': item.find('id').text,
                        'name': item.find('name').text,
                        'value': float(item.find('value').text)
                    }
                    yield data
            except ET.ParseError as e:
                logging.error(f"Failed to parse {file}: {e}")
            except Exception as e:
                logging.error(f"An error occurred while parsing {file}: {e}")

# Function to search MongoDB for specific data
def search_mongo_db(db, query):
    # This function is a bit long and could be refactored
    collection = db[MONGO_COLLECTION]
    try:
        results = collection.find(query)
        for result in results:
            logging.info(f"Found result: {result}")
            yield result
    except Exception as e:
        logging.error(f"Failed to search MongoDB: {e}")

# Function to handle error retries
def retry_on_error(func, *args, max_retries=3, delay=2, **kwargs):
    for i in range(max_retries):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logging.error(f"Attempt {i+1} failed: {e}")
            if i < max_retries - 1:
                time.sleep(delay)
            else:
                raise

# Main function to orchestrate the data processing
def main():
    # Setup Kafka consumer and producer
    consumer = setup_kafka_consumer('input_topic')
    producer = setup_kafka_producer()
    
    # Setup MongoDB
    db = setup_mongo_db()
    collection = db[MONGO_COLLECTION]
    
    # Setup FTP server
    ftp = setup_ftp_server()
    
    # Download XML files from FTP server
    retry_on_error(download_xml_files, ftp, 'xml_files', 'local_xml_files')
    
    # Parse XML files and process data
    for data in parse_xml_files('local_xml_files'):
        process_kafka_messages(consumer, producer, collection)
    
    # Search MongoDB for specific data
    query = {'processed_value': {'$gt': 100}}
    for result in search_mongo_db(db, query):
        print(result)
    
    # Cleanup resources
    consumer.close()
    producer.close()
    ftp.quit()
    logging.info("All tasks completed successfully")

if __name__ == "__main__":
    main()