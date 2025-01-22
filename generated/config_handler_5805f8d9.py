import xml.etree.ElementTree as ET
import websocket
import psycopg2
import mysql.connector
import gzip
import time
import logging
import os
import json
from threading import Thread
from queue import Queue

# Logging setup
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Configuration
config = {
    'xml_file': 'config.xml',
    'ws_url': 'ws://example.com/stream',
    'pg_db': {
        'user': 'admin',
        'password': 'securepassword',
        'host': 'localhost',
        'port': 5432,
        'database': 'mydb'
    },
    'mysql_db': {
        'user': 'root',
        'password': 'root',
        'host': 'localhost',
        'port': 3306,
        'database': 'testdb'
    }
}

# Queue for WebSocket messages
msg_queue = Queue()

def load_xml_config(file_path):
    """Loads configuration from an XML file.
    
    Args:
        file_path (str): Path to the XML file.
        
    Returns:
        dict: Configuration data.
        
    Raises:
        FileNotFoundError: If the specified file does not exist.
        ET.ParseError: If the XML file is not well-formed.
    """
    try:
        tree = ET.parse(file_path)
        root = tree.getroot()
        config_data = {}
        for child in root:
            config_data[child.tag] = child.text
        return config_data
    except FileNotFoundError:
        logging.error(f"File not found: {file_path}")
        raise
    except ET.ParseError as e:
        logging.error(f"Error parsing XML file: {e}")
        raise

def connect_to_ws(ws_url):
    """Connects to a WebSocket server and listens for messages.
    
    Args:
        ws_url (str): WebSocket URL.
    """
    def on_message(ws, message):
        msg_queue.put(message)
        print(f"Received message: {message}")  # Debug print

    def on_error(ws, error):
        logging.error(f"WebSocket error: {error}")

    def on_close(ws):
        logging.info("WebSocket connection closed")

    def on_open(ws):
        logging.info("WebSocket connection opened")

    ws = websocket.WebSocketApp(ws_url,
                               on_message=on_message,
                               on_error=on_error,
                               on_close=on_close)
    ws.on_open = on_open
    ws.run_forever()

def connect_to_pg(db_config):
    """Connects to a PostgreSQL database.
    
    Args:
        db_config (dict): Database configuration.
        
    Returns:
        psycopg2.connection: Database connection.
    """
    try:
        conn = psycopg2.connect(**db_config)
        logging.info("Connected to PostgreSQL database")
        return conn
    except psycopg2.OperationalError as e:
        logging.error(f"Failed to connect to PostgreSQL: {e}")
        raise

def connect_to_mysql(db_config):
    """Connects to a MySQL database.
    
    Args:
        db_config (dict): Database configuration.
        
    Returns:
        mysql.connector.connection: Database connection.
    """
    try:
        conn = mysql.connector.connect(**db_config)
        logging.info("Connected to MySQL database")
        return conn
    except mysql.connector.Error as e:
        logging.error(f"Failed to connect to MySQL: {e}")
        raise

def compress_data(data):
    """Compresses data using gzip.
    
    Args:
        data (str): Data to be compressed.
        
    Returns:
        bytes: Compressed data.
    """
    compressed_data = gzip.compress(data.encode('utf-8'))
    return compressed_data

def decompress_data(compressed_data):
    """Decompresses data using gzip.
    
    Args:
        compressed_data (bytes): Compressed data.
        
    Returns:
        str: Decompressed data.
    """
    try:
        data = gzip.decompress(compressed_data).decode('utf-8')
        return data
    except gzip.BadGzipFile:
        logging.error("Failed to decompress data")
        return None

def process_xml_data(xml_data):
    """Processes XML data and returns a dictionary.
    
    Args:
        xml_data (str): XML data as a string.
        
    Returns:
        dict: Processed data.
    """
    root = ET.fromstring(xml_data)
    processed_data = {}
    for child in root:
        processed_data[child.tag] = child.text
    return processed_data

def process_ws_message():
    """Processes messages from the WebSocket queue and logs them."""
    while True:
        message = msg_queue.get()
        if message:
            logging.info(f"Processing message: {message}")
            # TODO: Add message filtering logic
            # FIXME: This should be moved to a separate function
            try:
                data = json.loads(message)
                logging.info(f"JSON data: {data}")
            except json.JSONDecodeError:
                logging.error("Failed to decode JSON message")
                continue
        time.sleep(1)

def schedule_task(func, interval):
    """Schedules a function to run at regular intervals.
    
    Args:
        func (callable): Function to be scheduled.
        interval (int): Interval in seconds.
    """
    def wrapper():
        while True:
            func()
            time.sleep(interval)
    thread = Thread(target=wrapper)
    thread.daemon = True
    thread.start()

def save_to_pg(conn, data):
    """Saves data to PostgreSQL.
    
    Args:
        conn (psycopg2.connection): Database connection.
        data (dict): Data to be saved.
    """
    cursor = conn.cursor()
    try:
        # Insert data into a table
        cursor.execute("INSERT INTO data_table (key, value) VALUES (%s, %s)", (data['key'], data['value']))
        conn.commit()
    except Exception as e:
        logging.error(f"Failed to save data to PostgreSQL: {e}")
        conn.rollback()
    finally:
        cursor.close()

def save_to_mysql(conn, data):
    """Saves data to MySQL.
    
    Args:
        conn (mysql.connector.connection): Database connection.
        data (dict): Data to be saved.
    """
    cursor = conn.cursor()
    try:
        # Insert data into a table
        cursor.execute("INSERT INTO data_table (key, value) VALUES (%s, %s)", (data['key'], data['value']))
        conn.commit()
    except mysql.connector.Error as e:
        logging.error(f"Failed to save data to MySQL: {e}")
        conn.rollback()
    finally:
        cursor.close()

def main():
    # Load XML configuration
    try:
        xml_config = load_xml_config(config['xml_file'])
        logging.info(f"XML configuration loaded: {xml_config}")
    except Exception as e:
        logging.error(f"Failed to load XML configuration: {e}")
        return

    # Connect to WebSocket
    ws_thread = Thread(target=connect_to_ws, args=(config['ws_url'],))
    ws_thread.daemon = True
    ws_thread.start()

    # Connect to PostgreSQL
    try:
        pg_conn = connect_to_pg(config['pg_db'])
    except Exception as e:
        logging.error(f"Failed to connect to PostgreSQL: {e}")
        return

    # Connect to MySQL
    try:
        mysql_conn = connect_to_mysql(config['mysql_db'])
    except Exception as e:
        logging.error(f"Failed to connect to MySQL: {e}")
        return

    # Schedule periodic tasks
    schedule_task(lambda: save_to_pg(pg_conn, {'key': 'test', 'value': 'value'}), 10)
    schedule_task(lambda: save_to_mysql(mysql_conn, {'key': 'test', 'value': 'value'}), 10)

    # Process WebSocket messages
    process_ws_message()

if __name__ == "__main__":
    main()