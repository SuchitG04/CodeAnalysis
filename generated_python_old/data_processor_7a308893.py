import requests
import json
import csv
import os
from kafka import KafkaProducer
from elasticsearch import Elasticsearch
import pandas as pd
import logging

# Logging configuration
logging.basicConfig(level=logging.INFO)

class ConfigHandler:
    def __init__(self, graphql_endpoint, excel_file, kafka_topic, elasticsearch_index):
        self.graphql_endpoint = graphql_endpoint
        self.excel_file = excel_file
        self.kafka_topic = kafka_topic
        self.elasticsearch_index = elasticsearch_index
        self.producer = self.create_kafka_producer()
        self.elasticsearch_client = self.create_elasticsearch_client()

    def create_kafka_producer(self):
        """
        Create a Kafka producer instance.
        """
        return KafkaProducer(bootstrap_servers='localhost:9092')

    def create_elasticsearch_client(self):
        """
        Create an Elasticsearch client instance.
        """
        return Elasticsearch()

    def validate_data(self, data):
        """
        Validate the data.
        """
        if not data:
            raise ValueError("Data cannot be empty.")
        if not isinstance(data, (list, dict)):
            raise TypeError("Data must be a list or a dictionary.")
        return True

    def handle_graphql_endpoint(self):
        """
        Handle GraphQL endpoint.
        """
        # TODO: Improve error handling
        try:
            response = requests.get(self.graphql_endpoint)
            if response.status_code != 200:
                raise Exception("Failed to fetch data from GraphQL endpoint.")
            data = response.json()
            self.validate_data(data)
            self.send_data_to_kafka(data)
            self.index_data_in_elasticsearch(data)
        except Exception as e:
            logging.error(f"An error occurred: {str(e)}")

    def handle_excel_sheet(self):
        """
        Handle Excel sheet.
        """
        try:
            # TODO: Refactor this function
            with open(self.excel_file, 'r') as file:
                reader = csv.reader(file)
                data = [row for row in reader]
            self.validate_data(data)
            self.send_data_to_kafka(data)
            self.index_data_in_elasticsearch(data)
        except Exception as e:
            logging.error(f"An error occurred: {str(e)}")

    def handle_kafka_topic(self):
        """
        Handle Kafka topic.
        """
        # TODO: Add error handling
        for message in self.producer.poll():
            data = json.loads(message.value().decode())
            self.validate_data(data)
            self.index_data_in_elasticsearch(data)

    def handle_elasticsearch(self):
        """
        Handle Elasticsearch.
        """
        try:
            # TODO: Optimize performance
            data = self.elasticsearch_client.search(index=self.elasticsearch_index)
            self.validate_data(data)
            self.send_data_to_kafka(data)
        except Exception as e:
            logging.error(f"An error occurred: {str(e)}")

    def send_data_to_kafka(self, data):
        """
        Send data to Kafka topic.
        """
        try:
            self.producer.send(self.kafka_topic, json.dumps(data).encode())
            self.producer.flush()
        except Exception as e:
            logging.error(f"Failed to send data to Kafka topic: {str(e)}")

    def index_data_in_elasticsearch(self, data):
        """
        Index data in Elasticsearch.
        """
        try:
            self.elasticsearch_client.index(index=self.elasticsearch_index, body=data)
        except Exception as e:
            logging.error(f"Failed to index data in Elasticsearch: {str(e)}")

if __name__ == "__main__":
    # TODO: Read configuration from a file or environment variables
    graphql_endpoint = "https://example.com/graphql"
    excel_file = "data.csv"
    kafka_topic = "my_topic"
    elasticsearch_index = "my_index"

    handler = ConfigHandler(graphql_endpoint, excel_file, kafka_topic, elasticsearch_index)
    handler.handle_graphql_endpoint()
    handler.handle_excel_sheet()
    handler.handle_kafka_topic()
    handler.handle_elasticsearch()