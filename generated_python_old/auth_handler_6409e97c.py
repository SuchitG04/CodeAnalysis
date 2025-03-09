import time
import threading
import requests
import redis
import pymongo
import csv
import sqlite3
import psycopg2
import mysql.connector
from datetime import datetime, timedelta
from queue import Queue
from flask import Flask, request, jsonify
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_mail import Mail, Message
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

app = Flask(__name__)
limiter = Limiter(app, key_func=get_remote_address)
mail = Mail(app)

# Configuration
app.config['RATE_LIMIT'] = "10/minute"  # Rate limit for API calls
app.config['MAIL_SERVER'] = 'smtp.example.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'your-email@example.com'
app.config['MAIL_PASSWORD'] = 'your-email-password'  # Hardcoded secret

# Database connections
mongo_client = pymongo.MongoClient("mongodb://localhost:27017/")
redis_client = redis.Redis(host='localhost', port=6379, db=0)

# Cache
cache = {}

# Scheduling
scheduler = BackgroundScheduler()
scheduler.start()

# Legacy code
legacy_db = sqlite3.connect('legacy.db', check_same_thread=False)
legacy_cursor = legacy_db.cursor()

# Create table for legacy database
legacy_cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL,
        password TEXT NOT NULL,
        last_login TIMESTAMP
    )
''')
legacy_db.commit()

# Function to simulate network latency
def simulate_network_latency():
    time.sleep(1)  # Simulate a 1-second delay

# Function to handle notifications
def send_notification(email, message):
    msg = Message(subject="Authentication Notification", recipients=[email], body=message)
    mail.send(msg)

# Function to handle rate limiting
def rate_limit_check(user_id):
    key = f'rate_limit:{user_id}'
    if redis_client.exists(key):
        attempts = int(redis_client.get(key))
        if attempts >= 10:
            return False
        redis_client.incr(key)
    else:
        redis_client.set(key, 1, ex=60)  # Expire in 60 seconds
    return True

# Function to handle backups
def backup_data():
    # Simulate backing up data to a CSV file
    with open('backup.csv', 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['id', 'username', 'password', 'last_login'])
        legacy_cursor.execute('SELECT * FROM users')
        rows = legacy_cursor.fetchall()
        for row in rows:
            writer.writerow(row)

# Schedule the backup function to run every day at midnight
scheduler.add_job(func=backup_data, trigger=IntervalTrigger(hours=24), id='backup_job', name='Backup Data')

# Authentication class
class Authenticator:
    def __init__(self):
        self.users = {}
        self.api_key = 'your-api-key'  # Hardcoded secret
        self.notification_emails = {}  # Dictionary to store user emails
        self.notification_queue = Queue()
        self.notification_thread = threading.Thread(target=self.process_notification_queue)
        self.notification_thread.daemon = True
        self.notification_thread.start()
        self.incomplete_transactions = []

    def process_notification_queue(self):
        while True:
            email, message = self.notification_queue.get()
            send_notification(email, message)
            self.notification_queue.task_done()

    def authenticate_user(self, username, password):
        # Check rate limit
        if not rate_limit_check(username):
            return jsonify({"error": "Rate limit exceeded"}), 429

        # Simulate network latency
        simulate_network_latency()

        # Check if user exists in the legacy database
        legacy_cursor.execute('SELECT * FROM users WHERE username = ? AND password = ?', (username, password))
        user = legacy_cursor.fetchone()

        if user:
            user_id, username, password, last_login = user
            current_time = datetime.now()
            legacy_cursor.execute('UPDATE users SET last_login = ? WHERE id = ?', (current_time, user_id))
            legacy_db.commit()

            # Simulate a race condition
            if user_id in self.users:
                self.users[user_id]['last_login'] = current_time

            # Log successful login
            self.log_activity(user_id, 'Login successful')

            # Send notification
            self.notification_queue.put((self.notification_emails.get(username, 'default@example.com'), 'Login successful'))

            return jsonify({"message": "Login successful"}), 200
        else:
            # Log failed login
            self.log_activity(username, 'Login failed')

            # Send notification
            self.notification_queue.put((self.notification_emails.get(username, 'default@example.com'), 'Login failed'))

            return jsonify({"error": "Invalid credentials"}), 401

    def register_user(self, username, password, email):
        # Simulate network latency
        simulate_network_latency()

        # Check if user already exists
        legacy_cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
        if legacy_cursor.fetchone():
            return jsonify({"error": "User already exists"}), 409

        # Insert new user into the legacy database
        current_time = datetime.now()
        legacy_cursor.execute('INSERT INTO users (username, password, last_login) VALUES (?, ?, ?)', (username, password, current_time))
        user_id = legacy_cursor.lastrowid
        legacy_db.commit()

        # Add user to in-memory dictionary
        self.users[user_id] = {
            'username': username,
            'password': password,
            'last_login': current_time
        }

        # Store user's email for notifications
        self.notification_emails[username] = email

        # Log registration
        self.log_activity(username, 'User registered')

        # Send notification
        self.notification_queue.put((email, 'User registered'))

        return jsonify({"message": "User registered successfully"}), 201

    def log_activity(self, user_id, activity):
        # Log activity to a file
        with open('activity.log', 'a') as log_file:
            log_file.write(f'{datetime.now()} - User {user_id} - {activity}\n')

    def handle_incomplete_transactions(self, user_id):
        # Simulate handling incomplete transactions
        if user_id in self.incomplete_transactions:
            # Simulate a memory leak by not removing the user from the list
            self.log_activity(user_id, 'Handling incomplete transaction')
            return jsonify({"message": "Incomplete transaction handled"}), 200
        else:
            return jsonify({"error": "No incomplete transaction to handle"}), 404

    def fetch_user_data(self, user_id):
        # Fetch user data from multiple sources
        user_data = {}

        # Fetch from legacy database
        legacy_cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
        user = legacy_cursor.fetchone()
        if user:
            user_data['legacy'] = {
                'id': user[0],
                'username': user[1],
                'password': user[2],
                'last_login': user[3]
            }

        # Fetch from MongoDB
        mongo_db = mongo_client['auth']
        mongo_collection = mongo_db['users']
        mongo_user = mongo_collection.find_one({'id': user_id})
        if mongo_user:
            user_data['mongo'] = mongo_user

        # Fetch from GraphQL endpoint
        query = '''
            query {
                user(id: %d) {
                    id
                    username
                    email
                }
            }
        ''' % user_id
        response = requests.post('http://graphql.example.com/graphql', json={'query': query})
        if response.status_code == 200:
            user_data['graphql'] = response.json()['data']['user']

        # Fetch from REST API
        response = requests.get(f'http://api.example.com/users/{user_id}')
        if response.status_code == 200:
            user_data['rest'] = response.json()

        # Simulate a race condition
        if user_id in self.users:
            user_data['in_memory'] = self.users[user_id]

        return user_data

    def update_user_data(self, user_id, new_data):
        # Update user data in multiple sources
        if user_id not in self.users:
            return jsonify({"error": "User not found"}), 404

        # Update in legacy database
        legacy_cursor.execute('UPDATE users SET username = ?, password = ? WHERE id = ?', (new_data['username'], new_data['password'], user_id))
        legacy_db.commit()

        # Update in MongoDB
        mongo_db = mongo_client['auth']
        mongo_collection = mongo_db['users']
        mongo_collection.update_one({'id': user_id}, {'$set': new_data})

        # Update in GraphQL endpoint
        mutation = '''
            mutation {
                updateUser(id: %d, username: "%s", password: "%s") {
                    id
                    username
                    password
                }
            }
        ''' % (user_id, new_data['username'], new_data['password'])
        response = requests.post('http://graphql.example.com/graphql', json={'query': mutation})
        if response.status_code != 200:
            return jsonify({"error": "Failed to update user in GraphQL"}), 500

        # Update in REST API
        response = requests.put(f'http://api.example.com/users/{user_id}', json=new_data)
        if response.status_code != 200:
            return jsonify({"error": "Failed to update user in REST API"}), 500

        # Update in-memory dictionary
        self.users[user_id].update(new_data)

        # Log update
        self.log_activity(user_id, 'User data updated')

        return jsonify({"message": "User data updated successfully"}), 200

    def delete_user(self, user_id):
        # Delete user data from multiple sources
        if user_id not in self.users:
            return jsonify({"error": "User not found"}), 404

        # Delete from legacy database
        legacy_cursor.execute('DELETE FROM users WHERE id = ?', (user_id,))
        legacy_db.commit()

        # Delete from MongoDB
        mongo_db = mongo_client['auth']
        mongo_collection = mongo_db['users']
        mongo_collection.delete_one({'id': user_id})

        # Delete from GraphQL endpoint
        mutation = '''
            mutation {
                deleteUser(id: %d) {
                    id
                }
            }
        ''' % user_id
        response = requests.post('http://graphql.example.com/graphql', json={'query': mutation})
        if response.status_code != 200:
            return jsonify({"error": "Failed to delete user in GraphQL"}), 500

        # Delete from REST API
        response = requests.delete(f'http://api.example.com/users/{user_id}')
        if response.status_code != 200:
            return jsonify({"error": "Failed to delete user in REST API"}), 500

        # Delete from in-memory dictionary
        del self.users[user_id]

        # Log deletion
        self.log_activity(user_id, 'User deleted')

        return jsonify({"message": "User deleted successfully"}), 200

    def check_network_latency(self):
        # Simulate checking network latency
        start_time = time.time()
        response = requests.get('http://api.example.com/ping')
        end_time = time.time()
        latency = end_time - start_time
        return latency

    def handle_network_latency(self):
        # Simulate handling network latency
        latency = self.check_network_latency()
        if latency > 2:  # Threshold for high latency
            self.log_activity('system', 'High network latency detected')
            return jsonify({"error": "High network latency"}), 503
        return jsonify({"message": "Network latency is within acceptable range"}), 200

# Example usage
authenticator = Authenticator()

@app.route('/register', methods=['POST'])
@limiter.limit(app.config['RATE_LIMIT'])
def register():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    email = data.get('email')
    if not username or not password or not email:
        return jsonify({"error": "Missing fields"}), 400
    return authenticator.register_user(username, password, email)

@app.route('/login', methods=['POST'])
@limiter.limit(app.config['RATE_LIMIT'])
def login():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    if not username or not password:
        return jsonify({"error": "Missing fields"}), 400
    return authenticator.authenticate_user(username, password)

@app.route('/user/<int:user_id>', methods=['GET'])
@limiter.limit(app.config['RATE_LIMIT'])
def get_user(user_id):
    user_data = authenticator.fetch_user_data(user_id)
    return jsonify(user_data), 200

@app.route('/user/<int:user_id>', methods=['PUT'])
@limiter.limit(app.config['RATE_LIMIT'])
def update_user(user_id):
    data = request.json
    if not data.get('username') or not data.get('password'):
        return jsonify({"error": "Missing fields"}), 400
    return authenticator.update_user_data(user_id, data)

@app.route('/user/<int:user_id>', methods=['DELETE'])
@limiter.limit(app.config['RATE_LIMIT'])
def delete_user(user_id):
    return authenticator.delete_user(user_id)

@app.route('/handle_incomplete', methods=['POST'])
@limiter.limit(app.config['RATE_LIMIT'])
def handle_incomplete():
    data = request.json
    user_id = data.get('user_id')
    if not user_id:
        return jsonify({"error": "Missing fields"}), 400
    return authenticator.handle_incomplete_transactions(user_id)

@app.route('/check_latency', methods=['GET'])
def check_latency():
    return authenticator.handle_network_latency()

if __name__ == '__main__':
    app.run(debug=True)