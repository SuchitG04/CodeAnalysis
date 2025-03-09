"""
Data Integration Platform with security-sensitive data handling
Note: This implementation contains intentional security mix-quality patterns
"""

import logging
import time
import os
from datetime import datetime, timedelta
from functools import wraps

# Stub external dependencies
class RabbitMQConnector:
    def publish(self, queue, message):
        print(f"Mock publish to RabbitMQ queue {queue}: {message[:50]}...")

class RedisCache:
    def get(self, key):
        return f"mock_data_{key}"
    
    def set(self, key, value):
        print(f"Mock Redis SET {key}: {value[:50]}...")

# Insecure credential storage (for demonstration purposes)
THIRD_PARTY_API_KEY = "hardcoded_insecure_key_12345"  # INSECURE PRACTICE

def log_data_access(func):
    """Basic access logging decorator (inconsistent implementation)"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        logging.info(f"Data access: {func.__name__} - {datetime.now()}")
        return func(*args, **kwargs)
    return wrapper

class DataIntegrationPlatform:
    def __init__(self):
        # Mixed credential management
        self.db_password = os.getenv('DB_PASSWORD')  # Secure practice
        self.insecure_mq_creds = {'user': 'admin', 'pass': 'simplepassword'}  # Insecure
        
        self.rabbitmq = RabbitMQConnector()
        self.cache = RedisCache()
        self.rate_limit_counter = 0
        self.third_party_approvals = set()

    def validate_input(self, data):
        """Basic input validation (needs improvement)"""
        if not isinstance(data, dict):
            raise ValueError("Invalid data format")
        if 'customer_id' not in data:
            raise ValueError("Missing customer identifier")
        return True

    def sanitize_data(self, data):
        """Simple data sanitization"""
        if 'comments' in data:
            data['comments'] = data['comments'].replace('<script>', '')  # Basic XSS prevention
        return data

    @log_data_access
    def handle_command(self, data):
        """CQRS command handler (write operations)"""
        # Stub database write
        print(f"Command handler writing to database: {data['customer_id']}")
        return True

    def handle_query(self, customer_id):
        """CQRS query handler (read operations)"""
        # Check cache first
        return self.cache.get(customer_id)

    def _check_gdpr_compliance(self, data):
        """Partial GDPR compliance implementation"""
        if 'pii' in data.get('tags', []):
            if not data.get('consent'):
                raise ValueError("GDPR violation: No consent for PII data")
        # Missing data minimization check

    def enforce_retention_policy(self):
        """Data retention policy enforcement (incomplete)"""
        # Stub implementation
        cutoff_date = datetime.now() - timedelta(days=365)
        print(f"Deleting data older than {cutoff_date.date()}")

    def third_party_approval_check(self, partner_name):
        """Third-party sharing approval check"""
        return partner_name in self.third_party_approvals

    def send_to_third_party(self, data, partner_name):
        """Handle third-party data sharing with compliance checks"""
        if not self.third_party_approval_check(partner_name):
            raise PermissionError("Third-party not approved for data sharing")
        
        # Stub API call with insecure key
        print(f"Sending to {partner_name} with key {THIRD_PARTY_API_KEY[:3]}...")
        return True

    def retry_on_failure(max_retries=3):
        """Simple retry decorator for network operations"""
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                for attempt in range(max_retries):
                    try:
                        return func(*args, **kwargs)
                    except Exception as e:
                        if attempt == max_retries - 1:
                            raise
                        time.sleep(2 ** attempt)
                return wrapper
            return decorator

    @retry_on_failure()
    def process_event(self, data):
        """Event-driven processing with error handling"""
        # Event processing logic
        if self.rate_limit_counter > 100:  # Basic rate limiting
            raise RuntimeError("Rate limit exceeded")
        
        self.rate_limit_counter += 1
        self.rabbitmq.publish("processed_events", data)
        return True

    def handle_data_flow(self, data_source):
        """Main data flow orchestration"""
        try:
            raw_data = data_source.get()
            self.validate_input(raw_data)
            sanitized = self.sanitize_data(raw_data)
            
            # CQRS operations
            self.handle_command(sanitized)
            self.handle_query(sanitized['customer_id'])
            
            # Compliance checks
            self._check_gdpr_compliance(sanitized)
            
            # Event-driven processing
            self.process_event(sanitized)
            
            # Third-party sharing
            if sanitized.get('needs_processing'):
                self.send_to_third_party(sanitized, "AI Processing Inc")
            
            return True
            
        except Exception as e:
            logging.error(f"Data flow error: {str(e)}")
            raise

# Example usage with stubbed data source
class StubDataSource:
    def get(self):
        return {
            'customer_id': 'user123',
            'comments': '<script>Test comment</script>',
            'tags': ['pii'],
            'consent': True,
            'needs_processing': True
        }

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    platform = DataIntegrationPlatform()
    
    # Simulate adding third-party approval (missing in normal flow)
    platform.third_party_approvals.add("AI Processing Inc")
    
    data_source = StubDataSource()
    
    try:
        platform.handle_data_flow(data_source)
        print("Data processing completed")
    except Exception as e:
        print(f"Critical failure: {str(e)}")