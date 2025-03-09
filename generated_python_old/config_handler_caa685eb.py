import requests
import snowflake.connector
from google.cloud import bigquery
from influxdb import InfluxDBClient
from timescale import TimescaleDBClient
import logging
import time
import random

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Constants
SNOWFLAKE_ACCOUNT = 'your_snowflake_account'
SNOWFLAKE_USER = 'your_snowflake_user'
SNOWFLAKE_PASSWORD = 'your_snowflake_password'
SNOWFLAKE_DATABASE = 'your_snowflake_database'
SNOWFLAKE_SCHEMA = 'your_snowflake_schema'
SNOWFLAKE_WAREHOUSE = 'your_snowflake_warehouse'

BIGQUERY_PROJECT = 'your_bigquery_project'
BIGQUERY_DATASET = 'your_bigquery_dataset'
BIGQUERY_TABLE = 'your_bigquery_table'

INFLUXDB_HOST = 'your_influxdb_host'
INFLUXDB_PORT = 8086
INFLUXDB_DATABASE = 'your_influxdb_database'

TIMESCALEDB_HOST = 'your_timescaledb_host'
TIMESCALEDB_PORT = 5432
TIMESCALEDB_DATABASE = 'your_timescaledb_database'
TIMESCALEDB_USER = 'your_timescaledb_user'
TIMESCALEDB_PASSWORD = 'your_timescaledb_password'

VENDOR_API_URL = 'https://api.vendor.com'
PAYMENT_GATEWAY_API_URL = 'https://api.paymentgateway.com'
SHIPPING_PROVIDER_API_URL = 'https://api.shippingprovider.com'

RATE_LIMIT = 5  # Maximum number of requests per second

# Helper functions
def get_snowflake_connection():
    """Establish a connection to Snowflake."""
    return snowflake.connector.connect(
        user=SNOWFLAKE_USER,
        password=SNOWFLAKE_PASSWORD,
        account=SNOWFLAKE_ACCOUNT,
        warehouse=SNOWFLAKE_WAREHOUSE,
        database=SNOWFLAKE_DATABASE,
        schema=SNOWFLAKE_SCHEMA
    )

def get_bigquery_client():
    """Establish a connection to BigQuery."""
    return bigquery.Client(project=BIGQUERY_PROJECT)

def get_influxdb_client():
    """Establish a connection to InfluxDB."""
    return InfluxDBClient(host=INFLUXDB_HOST, port=INFLUXDB_PORT, database=INFLUXDB_DATABASE)

def get_timescaledb_client():
    """Establish a connection to TimescaleDB."""
    return TimescaleDBClient(host=TIMESCALEDB_HOST, port=TIMESCALEDB_PORT, database=TIMESCALEDB_DATABASE, user=TIMESCALEDB_USER, password=TIMESCALEDB_PASSWORD)

def rate_limit(func):
    """Decorator to implement rate limiting."""
    def wrapper(*args, **kwargs):
        time.sleep(1 / RATE_LIMIT)
        return func(*args, **kwargs)
    return wrapper

def audit_log(message):
    """Function to log audit messages."""
    logging.info(f"Audit Log: {message}")

def handle_authentication_failure(response):
    """Function to handle authentication failures."""
    if response.status_code == 401:
        logging.error("Authentication failure: Invalid credentials")
        raise Exception("Authentication failure: Invalid credentials")

def classify_data(data):
    """Function to classify data based on sensitivity."""
    if 'credit_card' in data:
        return 'PII'
    elif 'email' in data:
        return 'Contact'
    else:
        return 'General'

def get_customer_consent(customer_id):
    """Function to check customer consent for data processing."""
    # Stubbed function
    return True

# Main class for orchestrating data flow
class ECommerceDataHandler:
    def __init__(self):
        self.snowflake_conn = get_snowflake_connection()
        self.bigquery_client = get_bigquery_client()
        self.influxdb_client = get_influxdb_client()
        self.timescaledb_client = get_timescaledb_client()

    def extract_data(self):
        """Extract data from Snowflake and BigQuery."""
        try:
            # Extract from Snowflake
            cursor = self.snowflake_conn.cursor()
            cursor.execute("SELECT * FROM customer_orders")
            snowflake_data = cursor.fetchall()
            cursor.close()

            # Extract from BigQuery
            query = f"SELECT * FROM `{BIGQUERY_PROJECT}.{BIGQUERY_DATASET}.{BIGQUERY_TABLE}`"
            bigquery_data = self.bigquery_client.query(query).result()

            return snowflake_data, bigquery_data
        except Exception as e:
            logging.error(f"Error extracting data: {e}")
            raise

    def transform_data(self, snowflake_data, bigquery_data):
        """Transform extracted data."""
        try:
            transformed_data = []
            for row in snowflake_data:
                customer_id, order_id, amount, timestamp = row
                for bq_row in bigquery_data:
                    if bq_row['order_id'] == order_id:
                        transformed_data.append({
                            'customer_id': customer_id,
                            'order_id': order_id,
                            'amount': amount,
                            'timestamp': timestamp,
                            'product': bq_row['product'],
                            'quantity': bq_row['quantity']
                        })
                        break
            return transformed_data
        except Exception as e:
            logging.error(f"Error transforming data: {e}")
            raise

    @rate_limit
    def load_data_to_influxdb(self, data):
        """Load transformed data into InfluxDB."""
        try:
            json_body = [
                {
                    "measurement": "customer_orders",
                    "tags": {
                        "customer_id": row['customer_id'],
                        "order_id": row['order_id'],
                        "product": row['product']
                    },
                    "time": row['timestamp'],
                    "fields": {
                        "amount": row['amount'],
                        "quantity": row['quantity']
                    }
                }
                for row in data
            ]
            self.influxdb_client.write_points(json_body)
            audit_log("Data loaded to InfluxDB")
        except Exception as e:
            logging.error(f"Error loading data to InfluxDB: {e}")
            raise

    @rate_limit
    def load_data_to_timescaledb(self, data):
        """Load transformed data into TimescaleDB."""
        try:
            for row in data:
                query = f"INSERT INTO customer_orders (customer_id, order_id, amount, timestamp, product, quantity) VALUES ('{row['customer_id']}', '{row['order_id']}', {row['amount']}, '{row['timestamp']}', '{row['product']}', {row['quantity']})"
                self.timescaledb_client.execute(query)
            audit_log("Data loaded to TimescaleDB")
        except Exception as e:
            logging.error(f"Error loading data to TimescaleDB: {e}")
            raise

    def call_vendor_api(self, order_id):
        """Call the vendor API to update order status."""
        try:
            response = requests.post(f"{VENDOR_API_URL}/update_order", json={'order_id': order_id})
            handle_authentication_failure(response)
            if response.status_code == 200:
                logging.info(f"Vendor API call successful for order_id: {order_id}")
            else:
                logging.error(f"Vendor API call failed for order_id: {order_id}")
        except Exception as e:
            logging.error(f"Error calling Vendor API: {e}")
            raise

    def call_payment_gateway_api(self, customer_id, amount):
        """Call the payment gateway API to process payment."""
        try:
            if not get_customer_consent(customer_id):
                logging.error(f"Customer {customer_id} has not given consent for payment processing")
                return

            response = requests.post(f"{PAYMENT_GATEWAY_API_URL}/process_payment", json={'customer_id': customer_id, 'amount': amount})
            handle_authentication_failure(response)
            if response.status_code == 200:
                logging.info(f"Payment processed successfully for customer_id: {customer_id}")
            else:
                logging.error(f"Payment processing failed for customer_id: {customer_id}")
        except Exception as e:
            logging.error(f"Error calling Payment Gateway API: {e}")
            raise

    def call_shipping_provider_api(self, order_id, shipping_address):
        """Call the shipping provider API to initiate shipping."""
        try:
            response = requests.post(f"{SHIPPING_PROVIDER_API_URL}/initiate_shipping", json={'order_id': order_id, 'shipping_address': shipping_address})
            handle_authentication_failure(response)
            if response.status_code == 200:
                logging.info(f"Shipping initiated successfully for order_id: {order_id}")
            else:
                logging.error(f"Shipping initiation failed for order_id: {order_id}")
        except Exception as e:
            logging.error(f"Error calling Shipping Provider API: {e}")
            raise

    def process_data(self):
        """Orchestrate the ETL process and API calls."""
        try:
            snowflake_data, bigquery_data = self.extract_data()
            transformed_data = self.transform_data(snowflake_data, bigquery_data)

            for row in transformed_data:
                customer_id = row['customer_id']
                order_id = row['order_id']
                amount = row['amount']
                product = row['product']
                quantity = row['quantity']
                shipping_address = f"Address for order {order_id}"

                # Load data to InfluxDB and TimescaleDB
                self.load_data_to_influxdb([row])
                self.load_data_to_timescaledb([row])

                # Call external APIs
                self.call_vendor_api(order_id)
                self.call_payment_gateway_api(customer_id, amount)
                self.call_shipping_provider_api(order_id, shipping_address)

                # Inconsistent error handling
                if random.random() < 0.1:
                    raise Exception("Random error occurred")

                # Data classification
                data_classification = classify_data(row)
                audit_log(f"Data classification: {data_classification}")

        except Exception as e:
            logging.error(f"Error processing data: {e}")
            raise

if __name__ == "__main__":
    handler = ECommerceDataHandler()
    handler.process_data()