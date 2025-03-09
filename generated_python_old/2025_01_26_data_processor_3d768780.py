import logging
import time
import random
from datetime import datetime
from typing import Dict, List
from functools import wraps

# Setting up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Simulated external systems
class InsuranceClaimsDatabase:
    def get_claims(self, user_id: str) -> List[Dict]:
        logging.info(f"Fetching claims for user {user_id}")
        # Simulate network delay
        time.sleep(random.uniform(0.1, 0.5))
        return [{"claim_id": "12345", "amount": 1000, "status": "pending"}]

class PaymentProcessingSystem:
    def process_payment(self, user_id: str, amount: float) -> bool:
        logging.info(f"Processing payment for user {user_id} of amount {amount}")
        # Simulate network delay
        time.sleep(random.uniform(0.1, 0.5))
        return True

class SubscriptionManagementSystem:
    def get_subscription_status(self, user_id: str) -> str:
        logging.info(f"Fetching subscription status for user {user_id}")
        # Simulate network delay
        time.sleep(random.uniform(0.1, 0.5))
        return "active"

class ComplianceDataWarehouse:
    def log_compliance_event(self, event: str):
        logging.info(f"Logging compliance event: {event}")
        # Simulate network delay
        time.sleep(random.uniform(0.1, 0.5))

# Simulated API Gateway
class APIGateway:
    def route_request(self, endpoint: str, data: Dict):
        logging.info(f"Routing request to {endpoint} with data {data}")
        # Simulate routing and network delay
        time.sleep(random.uniform(0.1, 0.5))

# Adapter pattern for external integrations
class ExternalSystemAdapter:
    def __init__(self):
        self.insurance_db = InsuranceClaimsDatabase()
        self.payment_system = PaymentProcessingSystem()
        self.subscription_system = SubscriptionManagementSystem()
        self.compliance_warehouse = ComplianceDataWarehouse()

    def fetch_claims(self, user_id: str) -> List[Dict]:
        return self.insurance_db.get_claims(user_id)

    def process_payment(self, user_id: str, amount: float) -> bool:
        return self.payment_system.process_payment(user_id, amount)

    def get_subscription_status(self, user_id: str) -> str:
        return self.subscription_system.get_subscription_status(user_id)

    def log_compliance_event(self, event: str):
        self.compliance_warehouse.log_compliance_event(event)

# Role-based access control (RBAC)
class RoleBasedAccessControl:
    def __init__(self):
        self.roles = {
            'admin': ['read', 'write', 'delete'],
            'user': ['read'],
            'guest': []
        }

    def has_permission(self, role: str, action: str) -> bool:
        return action in self.roles.get(role, [])

# Password policy enforcement
class PasswordPolicy:
    def is_valid(self, password: str) -> bool:
        # Simple policy: at least 8 characters, contains a digit
        return len(password) >= 8 and any(char.isdigit() for char in password)

# Data encryption (stubbed)
def encrypt_data(data: str) -> str:
    logging.info("Encrypting data")
    return f"encrypted_{data}"

def decrypt_data(data: str) -> str:
    logging.info("Decrypting data")
    return data.replace("encrypted_", "")

# Error handling decorators
def retry_on_failure(max_retries: int = 3, delay: int = 2):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            attempt = 0
            while attempt < max_retries:
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    logging.error(f"Attempt {attempt + 1} failed: {e}")
                    attempt += 1
                    time.sleep(delay)
            logging.error("Max retries exceeded")
            raise Exception("Operation failed after multiple retries")
        return wrapper
    return decorator

# Main class to orchestrate data flow
class SecuritySensitiveSystem:
    def __init__(self):
        self.api_gateway = APIGateway()
        self.adapter = ExternalSystemAdapter()
        self.rbac = RoleBasedAccessControl()
        self.password_policy = PasswordPolicy()

    def authenticate_user(self, username: str, password: str) -> bool:
        # Simulate authentication
        logging.info(f"Authenticating user {username}")
        if not self.password_policy.is_valid(password):
            logging.warning("Password policy violation")
            return False
        return True

    def authorize_user(self, user_id: str, action: str) -> bool:
        # Simulate authorization
        logging.info(f"Authorizing user {user_id} for action {action}")
        role = "user"  # Simulated role assignment
        return self.rbac.has_permission(role, action)

    @retry_on_failure(max_retries=3, delay=2)
    def process_user_data(self, user_id: str, action: str, data: Dict):
        # Simulate data processing
        logging.info(f"Processing data for user {user_id} with action {action}")
        if not self.authorize_user(user_id, action):
            logging.error(f"User {user_id} is not authorized to perform {action}")
            return

        if action == "fetch_claims":
            claims = self.adapter.fetch_claims(user_id)
            self.api_gateway.route_request("claims", claims)
            self.adapter.log_compliance_event(f"Claims fetched for user {user_id}")
        elif action == "process_payment":
            amount = data.get("amount", 0)
            success = self.adapter.process_payment(user_id, amount)
            self.api_gateway.route_request("payment", {"user_id": user_id, "amount": amount, "success": success})
            self.adapter.log_compliance_event(f"Payment processed for user {user_id} of amount {amount}")
        elif action == "get_subscription_status":
            status = self.adapter.get_subscription_status(user_id)
            self.api_gateway.route_request("subscription", {"user_id": user_id, "status": status})
            self.adapter.log_compliance_event(f"Subscription status fetched for user {user_id}")

    def run(self):
        # Simulate user interaction
        user_id = "user123"
        username = "johndoe"
        password = "secureP@ssw0rd123"
        data = {"amount": 200}

        if self.authenticate_user(username, password):
            logging.info(f"User {username} authenticated successfully")
            self.process_user_data(user_id, "fetch_claims", {})
            self.process_user_data(user_id, "process_payment", data)
            self.process_user_data(user_id, "get_subscription_status", {})

# Run the system
if __name__ == "__main__":
    system = SecuritySensitiveSystem()
    system.run()