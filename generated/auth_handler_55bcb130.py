import json
import requests
import psycopg2
import websocket
import time
from datetime import datetime

# PostgreSQL connection details (hardcoded for simplicity)
PG_HOST = 'localhost'
PG_USER = 'myuser'
PG_PASSWORD = 'mypassword'
PG_DB = 'mydb'

# REST API endpoint URL (hardcoded for simplicity)
REST_API_URL = 'https://api.example.com/data'

# WebSocket stream URL (hardcoded for simplicity)
WS_URL = 'wss://ws.example.com/stream'

# JSON file path (hardcoded for simplicity)
JSON_FILE_PATH = 'data.json'

def connect_to_postgres():
    # Connect to PostgreSQL database
    conn = None
    try:
        conn = psycopg2.connect(
            host=PG_HOST,
            user=PG_USER,
            password=PG_PASSWORD,
            dbname=PG_DB
        )
    except psycopg2.Error as e:
        print(f"Error connecting to PostgreSQL: {e}")
    return conn

def fetch_data_from_rest_api():
    # Fetch data from REST API
    try:
        response = requests.get(REST_API_URL, timeout=5)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"Error fetching data from REST API: {e}")
        return None

def connect_to_websocket_stream():
    # Connect to WebSocket stream
    ws = None
    try:
        ws = websocket.create_connection(WS_URL)
    except websocket.WebSocketException as e:
        print(f"Error connecting to WebSocket stream: {e}")
    return ws

def read_json_file():
    # Read JSON file
    try:
        with open(JSON_FILE_PATH, 'r') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        print(f"Error reading JSON file: {e}")
        return None

def main():
    # Main function
    print("Starting API client...")

    # Connect to PostgreSQL database
    conn = connect_to_postgres()
    if conn:
        print("Connected to PostgreSQL database")
    else:
        print("Failed to connect to PostgreSQL database")

    # Fetch data from REST API
    data = fetch_data_from_rest_api()
    if data:
        print("Fetched data from REST API")
    else:
        print("Failed to fetch data from REST API")

    # Connect to WebSocket stream
    ws = connect_to_websocket_stream()
    if ws:
        print("Connected to WebSocket stream")
    else:
        print("Failed to connect to WebSocket stream")

    # Read JSON file
    json_data = read_json_file()
    if json_data:
        print("Read JSON file")
    else:
        print("Failed to read JSON file")

    # Simulate network latency
    time.sleep(2)

    # Simulate memory leak (just for demonstration purposes)
    # Note: This is not a real memory leak, but rather a simulation
    # In a real-world scenario, this would be a bug that needs to be fixed
    leaky_list = []
    for i in range(100000):
        leaky_list.append(i)

    # Close PostgreSQL connection
    if conn:
        conn.close()

    # Close WebSocket connection
    if ws:
        ws.close()

if __name__ == "__main__":
    main()