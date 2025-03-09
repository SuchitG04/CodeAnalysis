import json
import os
import redis
import pymongo
from elasticsearch import Elasticsearch
import mysql.connector
import pandas as pd
import requests
from ftplib import FTP
import threading
import asyncio
from datetime import datetime

# Global variables (anti-pattern)
API_KEY = "12345-SECRET-KEY"  # Hardcoded secret (anti-pattern)
CACHE_EXPIRY = 3600  # Cache expiry in seconds

class DataHandler:
    # Class variables (could be instance variables, but mixed here for complexity)
    redis_client = redis.Redis(host='localhost', port=6379, db=0)
    mongo_client = pymongo.MongoClient("mongodb://localhost:27017/")
    es_client = Elasticsearch([{'host': 'localhost', 'port': 9200}])
    mysql_connection = None  # Lazy initialization (anti-pattern)
    ftp_connection = None  # Lazy initialization (anti-pattern)

    def __init__(self, source, feature):
        self.source = source
        self.feature = feature
        self.log_file = "data_handler.log"  # Hardcoded file path (anti-pattern)
        self.unused_attribute = None  # Unused attribute (anti-pattern)

    def log(self, message):
        # Poor error handling and file operation (anti-pattern)
        with open(self.log_file, "a") as f:
            f.write(f"{datetime.now()}: {message}\n")

    def connect_to_mysql(self):
        # Improper credential handling (anti-pattern)
        if not self.mysql_connection:
            self.mysql_connection = mysql.connector.connect(
                user="root",
                password="password",  # Hardcoded password (anti-pattern)
                host="localhost",
                database="test_db"
            )
        return self.mysql_connection

    def connect_to_ftp(self):
        # Improper credential handling (anti-pattern)
        if not self.ftp_connection:
            self.ftp_connection = FTP("ftp.example.com")
            self.ftp_connection.login("user", "password")  # Hardcoded credentials (anti-pattern)
        return self.ftp_connection

    def backup_redis(self):
        # Well-organized method (pattern)
        try:
            keys = self.redis_client.keys("*")
            with open("redis_backup.json", "w") as f:
                backup_data = {key: self.redis_client.get(key) for key in keys}
                json.dump(backup_data, f)
            self.log("Redis backup completed successfully.")
        except Exception as e:
            self.log(f"Redis backup failed: {e}")

    def backup_mongodb(self):
        # Method doing too many things (anti-pattern)
        db = self.mongo_client["test_db"]
        collections = db.list_collection_names()
        for collection in collections:
            data = list(db[collection].find())
            with open(f"mongo_backup_{collection}.json", "w") as f:
                json.dump(data, f)
        self.log("MongoDB backup completed successfully.")

        # Unnecessary API call (anti-pattern)
        response = requests.get("https://api.example.com/status")
        if response.status_code != 200:
            self.log("API call failed during MongoDB backup.")

    def backup_elasticsearch(self):
        # Asynchronous operation with potential race condition (anti-pattern)
        async def fetch_and_save():
            query = {"query": {"match_all": {}}}
            result = await self.es_client.search(index="test_index", body=query)
            with open("es_backup.json", "w") as f:
                json.dump(result, f)
            self.log("Elasticsearch backup completed successfully.")

        asyncio.run(fetch_and_save())

    def backup_json_files(self):
        # File operation without proper error handling (anti-pattern)
        files = [f for f in os.listdir(".") if f.endswith(".json")]
        for file in files:
            with open(file, "r") as f:
                data = json.load(f)
            with open(f"{file}_backup.json", "w") as f:
                json.dump(data, f)
        self.log("JSON files backup completed successfully.")

    def search_redis(self, key):
        # Thread safety issue (anti-pattern)
        def _search():
            result = self.redis_client.get(key)
            self.log(f"Redis search result: {result}")

        threading.Thread(target=_search).start()

    def search_mongodb(self, query):
        # Legacy code pattern (anti-pattern)
        db = self.mongo_client["test_db"]
        result = db["test_collection"].find(query)
        self.log(f"MongoDB search result: {list(result)}")

    def search_elasticsearch(self, query):
        # Deprecated function usage (anti-pattern)
        result = self.es_client.search(index="test_index", body=query, params={"size": 10})
        self.log(f"Elasticsearch search result: {result}")

    def search_json_files(self, keyword):
        # Business logic mixed with technical implementation (anti-pattern)
        files = [f for f in os.listdir(".") if f.endswith(".json")]
        results = []
        for file in files:
            with open(file, "r") as f:
                data = json.load(f)
                if keyword in str(data):
                    results.append(file)
        self.log(f"JSON files search result: {results}")

    def backup(self):
        # Long method with mixed responsibilities (anti-pattern)
        if self.source == "Redis":
            self.backup_redis()
        elif self.source == "MongoDB":
            self.backup_mongodb()
        elif self.source == "Elasticsearch":
            self.backup_elasticsearch()
        elif self.source == "JSON files":
            self.backup_json_files()
        else:
            self.log(f"Unsupported source: {self.source}")

    def search(self, query):
        # Long method with mixed responsibilities (anti-pattern)
        if self.source == "Redis":
            self.search_redis(query)
        elif self.source == "MongoDB":
            self.search_mongodb(query)
        elif self.source == "Elasticsearch":
            self.search_elasticsearch(query)
        elif self.source == "JSON files":
            self.search_json_files(query)
        else:
            self.log(f"Unsupported source: {self.source}")

    def process_excel_sheet(self):
        # External dependency and improper error handling (anti-pattern)
        df = pd.read_excel("data.xlsx")
        self.log(f"Excel sheet processed: {df.head()}")

    def download_from_ftp(self):
        # Legacy compatibility and technical debt (anti-pattern)
        ftp = self.connect_to_ftp()
        ftp.cwd("/data")
        with open("downloaded_file.txt", "wb") as f:
            ftp.retrbinary("RETR file.txt", f.write)
        self.log("File downloaded from FTP server.")

    def cleanup(self):
        # Potential memory leak (anti-pattern)
        if self.mysql_connection:
            self.mysql_connection.close()
        if self.ftp_connection:
            self.ftp_connection.quit()
        self.log("Cleanup completed.")