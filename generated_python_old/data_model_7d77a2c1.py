import os
import json
import requests
import ftplib
import xml.etree.ElementTree as ET
import asyncio
import aiohttp
import redis
import sqlite3
import psycopg2
import mysql.connector
import hashlib
import logging
from typing import List, Dict, Any
from datetime import datetime

# Logger setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants
DB_TYPES = {
    'mysql': mysql.connector,
    'postgres': psycopg2,
    'sqlite': sqlite3
}

# Class definition
class DataHandler:
    def __init__(self, db_type: str, db_config: Dict[str, Any], cache_config: Dict[str, Any]):
        self.db_type = db_type
        self.db_config = db_config
        self.cache_config = cache_config
        self.db_conn = None
        self.cache = None
        self.audit_trail = []
        
        # Initialize database connection
        self._init_db_connection()
        
        # Initialize cache
        self._init_cache()
        
        # Legacy code: commented out old method
        # self._legacy_init()
        
    def _init_db_connection(self):
        db_module = DB_TYPES.get(self.db_type)
        if db_module:
            if self.db_type == 'sqlite':
                self.db_conn = db_module.connect(self.db_config['database'])
            else:
                self.db_conn = db_module.connect(**self.db_config)
        else:
            raise ValueError(f"Unsupported database type: {self.db_type}")
        
    def _init_cache(self):
        if self.cache_config['type'] == 'redis':
            self.cache = redis.Redis(**self.cache_config['config'])
        else:
            raise ValueError(f"Unsupported cache type: {self.cache_config['type']}")
        
    # def _legacy_init(self):
    #     # Legacy initialization method (no longer used)
    #     pass
    
    def _log_audit(self, action: str, data: Dict[str, Any]):
        entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'action': action,
            'data': data
        }
        self.audit_trail.append(entry)
        self.cache.rpush('audit_trail', json.dumps(entry))
        
    def _validate_input(self, data: Dict[str, Any]):
        if not isinstance(data, dict):
            raise ValueError("Input data must be a dictionary")
        
    def _get_ftp_connection(self):
        ftp = ftplib.FTP()
        ftp.connect(self.ftp_config['host'], self.ftp_config['port'])
        ftp.login(self.ftp_config['user'], self.ftp_config['password'])
        return ftp
    
    def _get_rest_api_data(self, url: str, params: Dict[str, Any] = None):
        response = requests.get(url, params=params)
        if response.status_code == 403:
            logger.error("Permission denied: %s", url)
            raise PermissionError("Access denied to the REST API")
        response.raise_for_status()
        return response.json()
    
    def _get_graphql_data(self, url: str, query: str, variables: Dict[str, Any] = None):
        payload = {'query': query, 'variables': variables}
        response = requests.post(url, json=payload)
        if response.status_code == 403:
            logger.error("Permission denied: %s", url)
            raise PermissionError("Access denied to the GraphQL endpoint")
        response.raise_for_status()
        return response.json()
    
    async def _get_rest_api_data_async(self, url: str, params: Dict[str, Any] = None):
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as response:
                if response.status == 403:
                    logger.error("Permission denied: %s", url)
                    raise PermissionError("Access denied to the REST API")
                response.raise_for_status()
                return await response.json()
    
    async def _get_graphql_data_async(self, url: str, query: str, variables: Dict[str, Any] = None):
        payload = {'query': query, 'variables': variables}
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload) as response:
                if response.status == 403:
                    logger.error("Permission denied: %s", url)
                    raise PermissionError("Access denied to the GraphQL endpoint")
                response.raise_for_status()
                return await response.json()
    
    def _write_to_file(self, file_path: str, data: Any):
        with open(file_path, 'w') as file:
            if file_path.endswith('.json'):
                json.dump(data, file)
            elif file_path.endswith('.xml'):
                root = ET.Element("root")
                for key, value in data.items():
                    child = ET.SubElement(root, key)
                    child.text = str(value)
                tree = ET.ElementTree(root)
                tree.write(file)
            else:
                file.write(str(data))
    
    def _read_from_file(self, file_path: str):
        with open(file_path, 'r') as file:
            if file_path.endswith('.json'):
                return json.load(file)
            elif file_path.endswith('.xml'):
                tree = ET.parse(file)
                return {child.tag: child.text for child in tree.getroot()}
            else:
                return file.read()
    
    def _execute_sql(self, query: str, params: tuple = None):
        cursor = self.db_conn.cursor()
        try:
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            self.db_conn.commit()
            return cursor.fetchall()
        except Exception as e:
            logger.error("Database error: %s", e)
            self.db_conn.rollback()
            raise
        finally:
            cursor.close()
    
    def _generate_hash(self, data: Any):
        return hashlib.sha256(str(data).encode('utf-8')).hexdigest()
    
    def fetch_data_from_rest(self, url: str, params: Dict[str, Any] = None):
        self._validate_input(params)
        data = self._get_rest_api_data(url, params)
        self._log_audit('fetch_data_from_rest', {'url': url, 'params': params})
        return data
    
    async def fetch_data_from_rest_async(self, url: str, params: Dict[str, Any] = None):
        self._validate_input(params)
        data = await self._get_rest_api_data_async(url, params)
        self._log_audit('fetch_data_from_rest_async', {'url': url, 'params': params})
        return data
    
    def fetch_data_from_ftp(self, file_path: str):
        ftp = self._get_ftp_connection()
        try:
            with open(file_path, 'wb') as file:
                ftp.retrbinary(f"RETR {file_path}", file.write)
            data = self._read_from_file(file_path)
            self._log_audit('fetch_data_from_ftp', {'file_path': file_path})
            return data
        finally:
            ftp.quit()
    
    def fetch_data_from_graphql(self, url: str, query: str, variables: Dict[str, Any] = None):
        self._validate_input(variables)
        data = self._get_graphql_data(url, query, variables)
        self._log_audit('fetch_data_from_graphql', {'url': url, 'query': query, 'variables': variables})
        return data
    
    async def fetch_data_from_graphql_async(self, url: str, query: str, variables: Dict[str, Any] = None):
        self._validate_input(variables)
        data = await self._get_graphql_data_async(url, query, variables)
        self._log_audit('fetch_data_from_graphql_async', {'url': url, 'query': query, 'variables': variables})
        return data
    
    def fetch_data_from_xml(self, file_path: str):
        data = self._read_from_file(file_path)
        self._log_audit('fetch_data_from_xml', {'file_path': file_path})
        return data
    
    def write_data_to_file(self, file_path: str, data: Any):
        self._validate_input(data)
        self._write_to_file(file_path, data)
        self._log_audit('write_data_to_file', {'file_path': file_path, 'data': data})
    
    def write_data_to_db(self, table: str, data: Dict[str, Any]):
        self._validate_input(data)
        columns = ', '.join(data.keys())
        values = ', '.join(['%s'] * len(data))
        query = f"INSERT INTO {table} ({columns}) VALUES ({values})"
        self._execute_sql(query, tuple(data.values()))
        self._log_audit('write_data_to_db', {'table': table, 'data': data})
    
    def read_data_from_db(self, table: str, condition: str = None):
        query = f"SELECT * FROM {table}"
        if condition:
            query += f" WHERE {condition}"
        data = self._execute_sql(query)
        self._log_audit('read_data_from_db', {'table': table, 'condition': condition})
        return data
    
    def recover_data_from_cache(self, key: str):
        data = self.cache.get(key)
        if data:
            return json.loads(data)
        else:
            logger.warning("Cache miss for key: %s", key)
            return None
    
    def _long_running_method(self, data: List[Dict[str, Any]]):
        for item in data:
            self._validate_input(item)
            hash_value = self._generate_hash(item)
            self.cache.set(hash_value, json.dumps(item))
            self.write_data_to_db('data_table', item)
            self._log_audit('long_running_method', {'item': item, 'hash_value': hash_value})
            # Simulate a long-running process
            import time
            time.sleep(1)
    
    async def _long_running_method_async(self, data: List[Dict[str, Any]]):
        for item in data:
            self._validate_input(item)
            hash_value = self._generate_hash(item)
            self.cache.set(hash_value, json.dumps(item))
            self.write_data_to_db('data_table', item)
            self._log_audit('long_running_method_async', {'item': item, 'hash_value': hash_value})
            # Simulate a long-running process
            await asyncio.sleep(1)
    
    def process_data(self, source: str, **kwargs):
        if source == 'REST API':
            url = kwargs.get('url')
            params = kwargs.get('params', {})
            data = self.fetch_data_from_rest(url, params)
        elif source == 'FTP server':
            file_path = kwargs.get('file_path')
            data = self.fetch_data_from_ftp(file_path)
        elif source == 'GraphQL endpoint':
            url = kwargs.get('url')
            query = kwargs.get('query')
            variables = kwargs.get('variables', {})
            data = self.fetch_data_from_graphql(url, query, variables)
        elif source == 'XML file':
            file_path = kwargs.get('file_path')
            data = self.fetch_data_from_xml(file_path)
        else:
            raise ValueError(f"Unsupported data source: {source}")
        
        # Legacy code: commented out old method
        # self._legacy_process_data(data)
        
        # Business logic mixed with technical implementation
        if 'name' in data and 'age' in data:
            if data['age'] < 18:
                logger.warning("Underage user detected: %s", data['name'])
        
        self._long_running_method(data)
        return data
    
    async def process_data_async(self, source: str, **kwargs):
        if source == 'REST API':
            url = kwargs.get('url')
            params = kwargs.get('params', {})
            data = await self.fetch_data_from_rest_async(url, params)
        elif source == 'FTP server':
            file_path = kwargs.get('file_path')
            data = self.fetch_data_from_ftp(file_path)
        elif source == 'GraphQL endpoint':
            url = kwargs.get('url')
            query = kwargs.get('query')
            variables = kwargs.get('variables', {})
            data = await self.fetch_data_from_graphql_async(url, query, variables)
        elif source == 'XML file':
            file_path = kwargs.get('file_path')
            data = self.fetch_data_from_xml(file_path)
        else:
            raise ValueError(f"Unsupported data source: {source}")
        
        # Business logic mixed with technical implementation
        if 'name' in data and 'age' in data:
            if data['age'] < 18:
                logger.warning("Underage user detected: %s", data['name'])
        
        await self._long_running_method_async(data)
        return data
    
    # def _legacy_process_data(self, data):
    #     # Legacy processing method (no longer used)
    #     pass
    
    def close(self):
        if self.db_conn:
            self.db_conn.close()
        if self.cache:
            self.cache.close()
        logger.info("Connections closed")
    
    # Race condition example
    def update_data(self, table: str, id: int, new_data: Dict[str, Any]):
        self._validate_input(new_data)
        existing_data = self.read_data_from_db(table, f"id = {id}")
        if not existing_data:
            logger.error("Data not found for id: %s", id)
            return
        
        # Simulate a race condition
        import time
        time.sleep(2)
        
        columns = ', '.join([f"{key} = %s" for key in new_data.keys()])
        query = f"UPDATE {table} SET {columns} WHERE id = %s"
        self._execute_sql(query, tuple(new_data.values()) + (id,))
        self._log_audit('update_data', {'table': table, 'id': id, 'new_data': new_data})
    
    # Memory leak example
    def memory_leak_example(self, data: List[Dict[str, Any]]):
        self._validate_input(data)
        for item in data:
            self._long_running_method([item])
            # Memory leak: keeping a reference to the data
            self._leaked_data = data
        self._log_audit('memory_leak_example', {'data': data})
    
    # Hardcoded secret example
    def fetch_secret_data(self, url: str):
        secret_key = 'hardcoded_secret_key'
        headers = {'Authorization': f'Bearer {secret_key}'}
        response = requests.get(url, headers=headers)
        if response.status_code == 403:
            logger.error("Permission denied: %s", url)
            raise PermissionError("Access denied to the secret data")
        response.raise_for_status()
        return response.json()
    
    # Insecure default example
    def insecure_default(self, data: Dict[str, Any], table: str = 'default_table'):
        self._validate_input(data)
        self.write_data_to_db(table, data)
        self._log_audit('insecure_default', {'table': table, 'data': data})
    
    # Version-specific code
    def version_specific_code(self, data: Dict[str, Any]):
        self._validate_input(data)
        if self.db_type == 'sqlite':
            query = "PRAGMA user_version = 1"
        else:
            query = "SELECT version()"
        self._execute_sql(query)
        self._log_audit('version_specific_code', {'data': data})
    
    # Deprecated function usage
    def deprecated_function(self, data: Dict[str, Any]):
        self._validate_input(data)
        # Deprecated function: should be replaced with a more secure method
        import urllib.request
        urllib.request.urlopen(data['url'])
        self._log_audit('deprecated_function', {'data': data})