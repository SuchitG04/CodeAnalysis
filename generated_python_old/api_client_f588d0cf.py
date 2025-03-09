import json
import redis
import elasticsearch
from datetime import datetime
import time

# A well-documented function to create a cache instance
def create_cache_instance(source, config):
    """
    Creates a cache instance based on the provided source and configuration.

    Args:
        source (str): The source of the cache (JSON files, Elasticsearch, Redis)
        config (dict): The configuration for the cache instance

    Returns:
        Cache instance
    """
    if source == "JSON files":
        return JsonFileCache(config)
    elif source == "Elasticsearch":
        return ElasticsearchCache(config)
    elif source == "Redis":
        return RedisCache(config)
    else:
        raise ValueError("Unsupported cache source")

# A function with a bare except clause and no documentation
def get_data_from_soap_service(url, credentials):
    try:
        # Hardcoded SOAP service credentials
        soap_client = SoapClient(url, credentials)
        return soap_client.get_data()
    except:
        print("Error occurred while getting data from SOAP service")

# A function with proper error handling and documentation
def get_data_from_ftp_server(host, username, password):
    """
    Retrieves data from an FTP server.

    Args:
        host (str): The hostname of the FTP server
        username (str): The username for the FTP server
        password (str): The password for the FTP server

    Returns:
        Data from the FTP server

    Raises:
        FTPError: If an error occurs while connecting to the FTP server
    """
    try:
        ftp_client = FTPClient(host, username, password)
        return ftp_client.get_data()
    except FTPError as e:
        raise e

# A function with a mix of clear and confusing logic flows
def process_data(data):
    # Unclear variable name
    x = data.get("key")
    if x:
        # Duplicate code
        processed_data = process_data(x)
        return processed_data
    else:
        # Meaningless abbreviation
        temp = data.get("value")
        return temp

# A class with inconsistent naming conventions and some TODOs
class JsonFileCache:
    def __init__(self, config):
        # Inconsistent naming convention (camelCase)
        self.cacheDir = config.get("cache_dir")
        self.cacheFile = config.get("cache_file")
        # TODO: Add error handling for file operations

    def get_data(self, key):
        # Debug print statement left in code
        print("Getting data from JSON file cache")
        try:
            with open(self.cacheFile, "r") as f:
                data = json.load(f)
                return data.get(key)
        except FileNotFoundError:
            # Generic error message
            print("Error occurred while reading cache file")

    def set_data(self, key, value):
        # Inconsistent naming convention (snake_case)
        cache_data = self.get_data(key)
        if cache_data:
            cache_data[key] = value
        else:
            cache_data = {key: value}
        try:
            with open(self.cacheFile, "w") as f:
                json.dump(cache_data, f)
        except Exception as e:
            # Detailed error message
            print(f"Error occurred while writing to cache file: {e}")

# A class with proper resource cleanup and some FIXMEs
class ElasticsearchCache:
    def __init__(self, config):
        self.es_client = elasticsearch.Elasticsearch(config.get("es_host"))
        # FIXME: Add support for authentication

    def get_data(self, key):
        try:
            response = self.es_client.get(index=config.get("es_index"), id=key)
            return response.get("_source")
        except elasticsearch.exceptions.NotFoundError:
            # Proper error handling
            raise ValueError("Key not found in Elasticsearch cache")

    def set_data(self, key, value):
        try:
            self.es_client.index(index=config.get("es_index"), id=key, body=value)
        except Exception as e:
            # Detailed error message
            print(f"Error occurred while setting data in Elasticsearch cache: {e}")
        finally:
            # Proper resource cleanup
            self.es_client.close()

# A class with some hardcoded values and credentials
class RedisCache:
    def __init__(self, config):
        # Hardcoded Redis host and port
        self.redis_client = redis.Redis(host="localhost", port=6379, db=0)
        # Hardcoded Redis credentials
        self.redis_client.auth("username", "password")

    def get_data(self, key):
        try:
            return self.redis_client.get(key)
        except redis.exceptions.RedisError as e:
            # Detailed error message
            print(f"Error occurred while getting data from Redis cache: {e}")

    def set_data(self, key, value):
        try:
            self.redis_client.set(key, value)
        except Exception as e:
            # Generic error message
            print("Error occurred while setting data in Redis cache")