import time
import random
import threading
import logging
import requests
import mysql.connector
from requests.exceptions import HTTPError

# Logger setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants
CACHE_TIMEOUT = 300  # Cache timeout in seconds
RATE_LIMIT = 10  # Max requests per minute

# Global cache dictionary
cache = {}
request_count = 0
last_request_time = time.time()

# MySQL connection setup
def get_mysql_connection():
    try:
        # TODO: Move hardcoded credentials to environment variables
        conn = mysql.connector.connect(
            host="localhost",
            user="root",
            password="password",
            database="test_db"
        )
        return conn
    except mysql.connector.Error as e:
        logger.error(f"Error connecting to MySQL: {e}")
        return None

# SOAP service request
def soap_request(url, data):
    headers = {'Content-Type': 'text/xml'}
    try:
        response = requests.post(url, data=data, headers=headers)
        response.raise_for_status()
        return response.text
    except HTTPError as e:
        logger.error(f"SOAP request failed: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error in SOAP request: {e}")
        return None

# Cache management
def get_from_cache(key):
    if key in cache:
        if time.time() - cache[key]['timestamp'] < CACHE_TIMEOUT:
            logger.info(f"Cache hit for {key}")
            return cache[key]['data']
        else:
            logger.info(f"Cache expired for {key}")
            del cache[key]
    return None

def set_to_cache(key, value):
    cache[key] = {'data': value, 'timestamp': time.time()}
    logger.info(f"Setting cache for {key}")

# Rate limiting
def rate_limiter():
    global request_count, last_request_time
    current_time = time.time()
    if current_time - last_request_time >= 60:
        request_count = 0
        last_request_time = current_time
    if request_count >= RATE_LIMIT:
        logger.warning("Rate limit exceeded, waiting...")
        time.sleep(60 - (current_time - last_request_time))
        request_count = 0
        last_request_time = time.time()
    request_count += 1

# MySQL data fetcher
def fetch_data_from_mysql(query):
    conn = get_mysql_connection()
    if not conn:
        return None
    try:
        cursor = conn.cursor()
        cursor.execute(query)
        result = cursor.fetchall()
        cursor.close()
        conn.close()
        return result
    except mysql.connector.Error as e:
        logger.error(f"Error fetching data from MySQL: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error fetching data from MySQL: {e}")
        return None

# SOAP data fetcher
def fetch_data_from_soap(url, data):
    rate_limiter()
    response = soap_request(url, data)
    if not response:
        return None
    try:
        # Parse SOAP response
        # TODO: Improve SOAP response parsing
        parsed_data = parse_soap_response(response)
        return parsed_data
    except Exception as e:
        logger.error(f"Error parsing SOAP response: {e}")
        return None

# SOAP response parser (dummy implementation)
def parse_soap_response(response):
    # Dummy parsing logic
    return response.replace("<response>", "").replace("</response>", "")

# Main function to fetch and cache data
def fetch_and_cache_data(source, query_or_url, data=None):
    if source == 'MySQL':
        key = f"mysql_{query_or_url}"
        cached_data = get_from_cache(key)
        if cached_data:
            return cached_data
        result = fetch_data_from_mysql(query_or_url)
        if result:
            set_to_cache(key, result)
            return result
    elif source == 'SOAP':
        key = f"soap_{query_or_url}"
        cached_data = get_from_cache(key)
        if cached_data:
            return cached_data
        result = fetch_data_from_soap(query_or_url, data)
        if result:
            set_to_cache(key, result)
            return result
    else:
        logger.error("Unknown data source")
    return None

# Example usage
def main():
    # MySQL query example
    mysql_query = "SELECT * FROM users WHERE role='admin'"
    mysql_data = fetch_and_cache_data('MySQL', mysql_query)
    if mysql_data:
        logger.info(f"MySQL Data: {mysql_data}")

    # SOAP request example
    soap_url = "http://example.com/soap/service"
    soap_data = "<request>data</request>"
    soap_result = fetch_and_cache_data('SOAP', soap_url, soap_data)
    if soap_result:
        logger.info(f"SOAP Result: {soap_result}")

# Thread-safe example
def thread_safe_example():
    threads = []
    for i in range(10):
        t = threading.Thread(target=main)
        threads.append(t)
        t.start()
    for t in threads:
        t.join()

if __name__ == "__main__":
    # Run the main function
    main()
    # Uncomment to test thread safety
    # thread_safe_example()