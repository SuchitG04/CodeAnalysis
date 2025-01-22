import csv
import json
import redis
import psycopg2
import logging
import time
import random

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Connect to Redis
redis_client = redis.Redis(host='localhost', port=6379, db=0)

# Connect to PostgreSQL
try:
    pg_conn = psycopg2.connect(
        dbname="logdb",
        user="loguser",
        password="logpass",
        host="localhost"
    )
    pg_cursor = pg_conn.cursor()
except Exception as e:
    logging.error(f"Failed to connect to PostgreSQL: {e}")

def process_csv(file_path):
    """
    Process a CSV file and handle missing fields.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                if 'timestamp' not in row or 'message' not in row:
                    logging.warning("Missing fields in CSV row: %s", row)
                    continue
                process_log(row['timestamp'], row['message'])
    except Exception as e:
        logging.error(f"Error processing CSV file {file_path}: {e}")

def process_json(file_path):
    # Process a JSON file and handle missing fields
    try:
        with open(file_path, 'r', encoding='utf-8') as jsonfile:
            data = json.load(jsonfile)
            for entry in data:
                if 'timestamp' not in entry or 'message' not in entry:
                    logging.warning("Missing fields in JSON entry: %s", entry)
                    continue
                process_log(entry['timestamp'], entry['message'])
    except Exception as e:
        logging.error(f"Error processing JSON file {file_path}: {e}")

def process_redis():
    """
    Process logs from Redis and handle network latency.
    """
    try:
        while True:
            key = redis_client.rpop('log_queue')
            if key is None:
                time.sleep(1)  # Simulate network latency
                continue
            log_data = json.loads(key)
            if 'timestamp' not in log_data or 'message' not in log_data:
                logging.warning("Missing fields in Redis log entry: %s", log_data)
                continue
            process_log(log_data['timestamp'], log_data['message'])
    except Exception as e:
        logging.error(f"Error processing Redis logs: {e}")

def process_postgres():
    # Process logs from PostgreSQL and handle data inconsistency
    try:
        pg_cursor.execute("SELECT timestamp, message FROM logs WHERE processed = false")
        rows = pg_cursor.fetchall()
        for row in rows:
            timestamp, message = row
            process_log(timestamp, message)
            pg_cursor.execute("UPDATE logs SET processed = true WHERE timestamp = %s", (timestamp,))
        pg_conn.commit()
    except Exception as e:
        logging.error(f"Error processing PostgreSQL logs: {e}")

def process_log(timestamp, message):
    """
    Process a log entry.
    """
    logging.info(f"Processing log entry: {timestamp} - {message}")
    # Simulate data validation
    if not isinstance(timestamp, str) or not isinstance(message, str):
        logging.error("Invalid log entry data types")
        return

    # Simulate search feature
    if "error" in message.lower():
        logging.error(f"Error detected in log: {message}")

    # Simulate notifications
    if "critical" in message.lower():
        send_notification(message)

    # Simulate monitoring
    log_to_redis(timestamp, message)

def log_to_redis(timestamp, message):
    """
    Log entry to Redis.
    """
    try:
        redis_client.lpush('processed_logs', json.dumps({'timestamp': timestamp, 'message': message}))
    except Exception as e:
        logging.error(f"Failed to log to Redis: {e}")

def send_notification(message):
    """
    Send notification for critical logs.
    """
    logging.info(f"Sending notification for critical log: {message}")
    # TODO: Implement actual notification logic

def main():
    # Simulate processing from different sources
    process_csv('logs.csv')
    process_json('logs.json')
    process_redis()
    process_postgres()

    # DEBUG: Print remaining logs in Redis
    remaining_logs = redis_client.lrange('log_queue', 0, -1)
    for log in remaining_logs:
        logging.debug(f"Remaining log in Redis: {log}")

if __name__ == "__main__":
    main()