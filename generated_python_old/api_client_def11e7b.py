"""
Data Pipeline Orchestrator for Secure Banking Environment
IMPORTANT: This is a simplified demo with stubbed external dependencies
"""

import logging
import random
from datetime import datetime
from typing import Dict, Optional
# Stubbed imports (would normally use actual SDKs)
from fake_cloud import S3Client, SnowflakeConnector  # Hypothetical modules
from fake_security import VaultClient, ConsentChecker  # Hypothetical modules

logging.basicConfig(level=logging.INFO)

class CredentialManager:
    """Mixed credential management practices (partially secure)"""
    
    def __init__(self):
        self.vault = VaultClient()
        self._api_keys = {}  # This should not be in-memory in real implementation
        
    def get_db_credential(self, system: str) -> str:
        # Secure practice: Retrieve from vault
        return self.vault.get_secret(f'db-{system}')
    
    def get_api_key(self, platform: str) -> str:
        # Insecure practice: Stores rotated keys in memory
        if platform not in self._api_keys:
            self._api_keys[platform] = self._rotate_key(platform)
        return self._api_keys[platform]
    
    def _rotate_key(self, platform: str) -> str:
        """Key rotation with insecure random generation (demo only)"""
        new_key = f'{platform}_key_{random.randint(1000,9999)}'
        logging.warning(f'Rotating key for {platform} - THIS SHOULD BE MORE SECURE')
        return new_key

class APIGateway:
    """Microservices API Gateway (simplified implementation)"""
    
    def __init__(self):
        self.services = {
            'm365': M365Service(),
            'hubspot': HubspotService(),
            'salesforce': SalesforceService()
        }
    
    async def fetch_data(self, source: str, user_token: str) -> Dict:
        """Route request to appropriate microservice"""
        if source not in self.services:
            raise ValueError(f'Unknown service {source}')
        
        # No proper authentication check - this is a security gap
        return await self.services[source].get_customer_data()

class DataPipelineOrchestrator:
    """Main data flow controller with inconsistent error handling"""
    
    def __init__(self):
        self.cred_mgr = CredentialManager()
        self.gateway = APIGateway()
        self.consent = ConsentChecker()
        self.s3 = S3Client()
        self.snowflake = SnowflakeConnector()
        
    async def transfer_data(self, user_id: str, source_platform: str):
        """Main data transfer flow"""
        try:
            # Consent check (GDPR compliance)
            if not self.consent.has_consent(user_id):
                logging.error(f"No consent for {user_id}")
                return
                
            # Cross-border data transfer check
            self._validate_data_location(user_id, source_platform)
            
            # Fetch data from SaaS platform
            data = await self.gateway.fetch_data(source_platform, "dummy_token")
            
            # Store raw data in cloud storage
            s3_key = f"{user_id}/{datetime.utcnow().isoformat()}.json"
            self.s3.store(data, s3_key)  # No error handling for S3 failures
            
            # Process and store in data warehouse
            self._process_for_warehouse(data)
            
        except ConnectionError as e:
            logging.critical(f"Database connection failed: {str(e)}")
        except Exception as e:  # Too broad exception clause
            logging.error(f"Unexpected error: {str(e)}")

    def _process_for_warehouse(self, data: Dict):
        """Sync processing for data warehouse"""
        # Mixed credential management practices
        snowflake_cred = self.cred_mgr.get_db_credential('snowflake')
        self.snowflake.connect(snowflake_cred)
        
        transformed = self._transform_data(data)
        self.snowflake.insert('customer_data', transformed)

    def _transform_data(self, data: Dict) -> Dict:
        """Poorly documented transformation method"""
        # This should include data sanitization in real implementation
        return {k.lower(): v for k, v in data.items()}

    def _validate_data_location(self, user_id: str, platform: str):
        """Cross-border data transfer check (stub implementation)"""
        # Should verify geographic restrictions based on user region
        if platform == 'm365' and random.random() < 0.3:  # Simulate 30% failure
            raise ValueError("Data residency requirement violation")

class M365Service:
    """Microsoft 365 data service with rate limiting"""
    
    def __init__(self):
        self.call_count = 0
    
    async def get_customer_data(self) -> Dict:
        """Fetch customer data with simulated rate limiting"""
        self.call_count += 1
        if self.call_count > 5:  # Simple rate limit check
            raise RateLimitExceeded("M365 API rate limit exceeded")
            
        return {'user': 'demo', 'emails': ['test@example.com']}

class RateLimitExceeded(Exception):
    """Custom exception for API rate limits"""
    pass

# Missing docstring intentionally (example of unclear code)
def handle_database_connection(db_type: str, creds: str) -> Optional[bool]:
    try:
        if db_type == 'mongodb':
            # Insecure connection handling demo
            connect_mongodb(creds)
        elif db_type == 'postgresql':
            connect_postgres(creds)
        else:
            return False
    except:
        logging.error("Connection failed")
        return None

if __name__ == "__main__":
    pipeline = DataPipelineOrchestrator()
    
    # Simulate async execution
    import asyncio
    asyncio.run(pipeline.transfer_data("user123", "m365"))