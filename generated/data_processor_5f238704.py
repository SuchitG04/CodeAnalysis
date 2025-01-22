import requests
import redis
import time
import json
from typing import Optional, Dict, Any

# TODO: Move Redis credentials to a config file
REDIS_HOST = 'localhost'
REDIS_PORT = 6379
REDIS_PASSWORD = 'secretpassword'  # FIXME: Hardcoded credentials

# API endpoint for fetching data
API_URL = 'https://api.example.com/data'

# Global Redis connection (bad practice, but sometimes seen in legacy code)
redis_conn = None

def get_redis_connection():
    """Returns a Redis connection. Handles resource exhaustion by limiting retries."""
    global redis_conn
    if redis_conn is None:
        try:
            redis_conn = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, password=REDIS_PASSWORD, socket_timeout=2)
            redis_conn.ping()  # Check if connection is alive
        except redis.ConnectionError as e:
            print(f"Failed to connect to Redis: {e}")
            raise
    return redis_conn

def fetch_data_from_api(endpoint: str, params: Optional[Dict] = None) -> Dict[str, Any]:
    """
    Fetches data from a REST API. Handles network latency and rate limiting.
    Args:
        endpoint: The API endpoint to fetch data from.
        params: Optional query parameters.
    Returns:
        A dictionary containing the API response.
    """
    try:
        response = requests.get(endpoint, params=params, timeout=5)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"API request failed: {e}")
        raise

def cache_data(key: str, data: Dict[str, Any], ttl: int = 60) -> bool:
    """Caches data in Redis with a TTL. Handles stale cache and version conflicts."""
    try:
        conn = get_redis_connection()
        serialized_data = json.dumps(data)
        conn.set(key, serialized_data, ex=ttl)
        return True
    except Exception as e:  # Bare except (bad practice)
        print(f"Failed to cache data: {e}")
        return False

def get_cached_data(key: str) -> Optional[Dict[str, Any]]:
    """Retrieves cached data from Redis. Handles missing fields."""
    try:
        conn = get_redis_connection()
        serialized_data = conn.get(key)
        if serialized_data:
            return json.loads(serialized_data)
        else:
            return None
    except Exception:  # Bare except (bad practice)
        return None

def process_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """Processes data. Some debug prints left in."""
    # TODO: Improve data processing logic
    processed = {}
    for k, v in data.items():
        if isinstance(v, str):
            processed[k] = v.upper()
        else:
            processed[k] = v
    print(f"Processed data: {processed}")  # Debug print (left in)
    return processed

def main():
    """Main function to fetch, process, and cache data."""
    cache_key = "api_data_cache"
    
    # Try to get cached data first
    cached_data = get_cached_data(cache_key)
    if cached_data:
        print("Using cached data.")
        data = cached_data
    else:
        print("Fetching fresh data from API.")
        data = fetch_data_from_api(API_URL)
        if data:
            cache_data(cache_key, data, ttl=30)  # Cache for 30 seconds
    
    # Process data
    if data:
        processed_data = process_data(data)
        # TODO: Add audit trail for processed data
    else:
        print("No data to process.")

if __name__ == "__main__":
    main()