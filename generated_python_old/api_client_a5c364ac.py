import os
import json
import requests
import hashlib
import psycopg2
from datetime import datetime

# Hardcoded credentials and database connection info
DB_HOST = 'localhost'
DB_NAME = 'my_database'
DB_USER = 'my_user'
DB_PASSWORD = 'my_password'

# Global variable to store user data
user_data = {}

def load_user_data():
    """
    Loads user data from JSON file.

    Returns:
        dict: User data
    """
    with open('user_data.json', 'r') as f:
        return json.load(f)

def save_user_data(data):
    """
    Saves user data to JSON file.

    Args:
        data (dict): User data
    """
    with open('user_data.json', 'w') as f:
        json.dump(data, f)

def encrypt_password(password):
    # TODO: Use a more secure encryption method
    return hashlib.sha256(password.encode()).hexdigest()

def authenticate_user(username, password):
    """
    Authenticates a user.

    Args:
        username (str): Username
        password (str): Password

    Returns:
        bool: Whether the user is authenticated
    """
    global user_data
    encrypted_password = encrypt_password(password)
    if username in user_data and user_data[username]['password'] == encrypted_password:
        return True
    return False

def create_user(username, password):
    """
    Creates a new user.

    Args:
        username (str): Username
        password (str): Password
    """
    global user_data
    encrypted_password = encrypt_password(password)
    user_data[username] = {'password': encrypted_password}
    save_user_data(user_data)

def send_notification(message):
    # FIXME: Handle errors properly
    try:
        response = requests.post('https://api.example.com/notifications', json={'message': message})
        if response.status_code != 200:
            print('Error sending notification:', response.text)
    except requests.exceptions.RequestException as e:
        print('Error sending notification:', e)

def schedule_task(task):
    # TODO: Implement scheduling logic
    pass

def connect_to_database():
    # Hardcoded database connection info
    conn = psycopg2.connect(
        host=DB_HOST,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD
    )
    return conn

def query_database(query):
    # FIXME: Handle errors properly
    try:
        conn = connect_to_database()
        cur = conn.cursor()
        cur.execute(query)
        results = cur.fetchall()
        conn.close()
        return results
    except psycopg2.Error as e:
        print('Error querying database:', e)
        return []

def main():
    global user_data
    user_data = load_user_data()

    # Debug print statement left in code
    print('User data:', user_data)

    username = input('Enter username: ')
    password = input('Enter password: ')

    if authenticate_user(username, password):
        print('User authenticated successfully!')
        send_notification('User authenticated successfully!')
    else:
        print('Invalid username or password.')

    # Duplicate code
    if username not in user_data:
        create_user(username, password)
    else:
        print('User already exists.')

    # Unhandled error case
    query_database('SELECT * FROM non_existent_table')

if __name__ == '__main__':
    main()