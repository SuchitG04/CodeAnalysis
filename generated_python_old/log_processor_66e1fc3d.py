"""
Secure Data Orchestration System for Online Banking
IMPORTANT: This contains both secure and insecure practices for demonstration purposes
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
import os  # Used for secure credential handling

# Stubbed external dependencies
class MessageBroker:
    """Mock Pub/Sub message broker"""
    async def subscribe(self, topic: str):
        return [{"data": "sample"}]
    
    async def publish(self, topic: str, message: dict):
        pass

class S3Client:
    """Mock AWS S3 client"""
    def get_object(self, bucket: str, key: str):
        return b"mock data"
    
    def put_object(self, bucket: str, key: str, data: bytes):
        pass

class InfluxDBClient:
    """Mock InfluxDB client"""
    def write_data(self, measurement: str, tags: dict, value: float):
        pass

# Security components
class SessionManager:
    """Manages user sessions with timeout"""
    def __init__(self):
        self.sessions: Dict[str, datetime] = {}
        
    def create_session(self, user_id: str) -> str:
        session_id = f"session_{user_id}"
        self.sessions[session_id] = datetime.now()
        return session_id
    
    def validate_session(self, session_id: str) -> bool:
        if session_id not in self.sessions:
            return False
        return (datetime.now() - self.sessions[session_id]) < timedelta(minutes=15)

def validate_input(func):
    """Decorator for input validation and sanitization"""
    def wrapper(*args, **kwargs):
        # Basic input sanitization example
        if 'data' in kwargs:
            if isinstance(kwargs['data'], str):
                kwargs['data'] = kwargs['data'].strip()
        return func(*args, **kwargs)
    return wrapper

class PolicyManager:
    """Handles compliance policy references"""
    POLICIES = {
        "RETENTION": "POL-2023-001",
        "DATA_ACCESS": "POL-2023-002"
    }

# Mixed credential management examples
INSECURE_CONFIG = {  # INSECURE: Hardcoded credentials
    "aws_key": "AKIAEXAMPLE",
    "aws_secret": "Secret123"
}

def get_db_credentials():
    """Secure credential handling example"""
    return os.environ.get('DB_PASSWORD')  # Secure: Uses environment variables

class DataOrchestrator:
    """Main data orchestration class with mixed sync/async methods"""
    
    def __init__(self):
        self.broker = MessageBroker()
        self.s3 = S3Client()
        self.influx = InfluxDBClient()
        self.sessions = SessionManager()
        self.logger = logging.getLogger(__name__)
        
    async def process_message(self, message: dict):
        """Async message processing with validation"""
        try:
            self._validate_message_format(message)
            sanitized = self._sanitize_data(message['data'])
            
            # Example RBAC check
            if not self._check_access("teller", "account_balance"):
                raise PermissionError("Access denied")
            
            # Data flow example
            raw_data = self.s3.get_object("raw-bucket", "key")
            processed = self._transform_data(raw_data)
            self.influx.write_data("transactions", {"type": "deposit"}, 100.0)
            
            # Data retention enforcement
            self.delete_old_data()
            
        except Exception as e:
            self.logger.error(f"Processing failed: {str(e)}")
            await self.broker.publish("dlq", {"error": str(e)})

    @validate_input
    def _sanitize_data(self, data: str) -> str:
        return data.lower()
    
    def _validate_message_format(self, message: dict):
        """Basic data validation example"""
        if 'data' not in message:
            raise ValueError("Invalid message format")
        
    def _check_access(self, role: str, resource: str) -> bool:
        """Simplistic RBAC implementation"""
        access_matrix = {
            "teller": ["account_balance"],
            "manager": ["account_balance", "transactions"]
        }
        return resource in access_matrix.get(role, [])
    
    def delete_old_data(self):
        """Data retention policy enforcement"""
        cutoff = datetime.now() - timedelta(days=365)
        self.logger.info(f"Enforcing retention policy {PolicyManager.POLICIES['RETENTION']}")
        # Actual deletion logic would go here

# Example insecure usage
def insecure_credential_usage():
    """DEMONSTRATION OF INSECURE PRACTICE"""
    print(f"Using AWS key: {INSECURE_CONFIG['aws_key']}")  # NEVER DO THIS IN PRODUCTION

async def main():
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    
    # Initialize orchestrator
    orchestrator = DataOrchestrator()
    
    # Start processing loop
    while True:
        messages = await orchestrator.broker.subscribe("transactions")
        for msg in messages:
            await orchestrator.process_message(msg)
        await asyncio.sleep(1)

if __name__ == "__main__":
    # Demonstrate mixed credential handling
    insecure_credential_usage()
    
    # Start main async loop
    asyncio.run(main())