import os
import time
import requests
import xml.etree.ElementTree as ET
from urllib.parse import urlencode
from threading import Lock

class APIClient:
    def __init__(self, api_key, xml_file_path=None, db_connection=None, cache=None):
        self.api_key = api_key
        self.xml_file_path = xml_file_path
        self.db_connection = db_connection
        self.cache = cache
        self.lock = Lock()
        self.rate_limit_reset = 0

    def _make_api_call(self, endpoint, params=None):
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "User-Agent": "MyAPIClient/1.0",
        }
        url = f"https://api.example.com/{endpoint}"
        response = requests.get(url, headers=headers, params=params)
        if response.status_code == 429:
            self._handle_rate_limit(response)
        return response.json()

    def _handle_rate_limit(self, response):
        reset_time = int(response.headers["X-RateLimit-Reset"])
        sleep_time = max(reset_time - int(time.time()), 0)
        print(f"Rate limit exceeded. Sleeping for {sleep_time} seconds.")
        time.sleep(sleep_time)
        self.rate_limit_reset = reset_time

    def _read_xml(self):
        tree = ET.parse(self.xml_file_path)
        root = tree.getroot()
        # TODO: Process XML data

    def _write_to_db(self, data):
        # TODO: Write data to the database
        pass

    def _store_in_cache(self, key, data):
        if self.cache:
            self.cache.set(key, data)

    def _retrieve_from_cache(self, key):
        if self.cache:
            return self.cache.get(key)

    def get_data(self, id):
        # Data validation
        if not isinstance(id, int) or id <= 0:
            raise ValueError("Invalid ID")

        # Caching
        cache_key = f"data:{id}"
        cached_data = self._retrieve_from_cache(cache_key)
        if cached_data:
            return cached_data

        # API call
        data = self._make_api_call(f"data/{id}")

        # File operations
        if self.xml_file_path:
            with open("output.xml", "w") as f:
                f.write(ET.tostring(data, encoding="unicode"))

        # Database operations
        if self.db_connection:
            self._write_to_db(data)

        # Cache the result
        self._store_in_cache(cache_key, data)

        return data