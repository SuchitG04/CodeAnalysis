import hashlib
import os
import time
import threading
import json
import sqlite3
import requests
import redis
from cryptography.fernet import Fernet
from flask import Flask, request, jsonify
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

# Flask app setup
app = Flask(__name__)
limiter = Limiter(app, key_func=get_remote_address)

# Redis cache setup
cache = redis.StrictRedis(host='localhost', port=6379, db=0)

# Database setup (using SQLite for simplicity)
db = sqlite3.connect('auth.db', check_same_thread=False)
cursor = db.cursor()
cursor.execute('''CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, username TEXT, password_hash TEXT, salt TEXT)''')
db.commit()

# Encryption key (hardcoded for simplicity, but this is a bad practice)
ENCRYPTION_KEY = b'secretkey12345678901234567890123456789012'

# Fernet instance for data encryption
fernet = Fernet(ENCRYPTION_KEY)

# Rate limiting settings
RATE_LIMIT = "5/minute"

# Some unused attributes and commented-out code
class AuthenticationSystem:
    def __init__(self):
        self.users = {}  # This is unused and should be removed
        self.api_key = '1234567890abcdef'  # Hardcoded API key (bad practice)
        self.db = db
        self.cursor = cursor
        self.cache = cache
        self.fernet = fernet
        self.rate_limit = RATE_LIMIT
        # self.logger = logging.getLogger('auth_system')  # Uncomment this if you want to use logging

    def hash_password(self, password, salt=None):
        if salt is None:
            salt = os.urandom(16)
        dk = hashlib.pbkdf2_hmac('sha256', password.encode(), salt, 100000)
        return dk, salt

    def encrypt_data(self, data):
        return self.fernet.encrypt(data.encode())

    def decrypt_data(self, encrypted_data):
        return self.fernet.decrypt(encrypted_data).decode()

    def register_user(self, username, password):
        if not username or not password:
            return False, "Username and password are required"
        password_hash, salt = self.hash_password(password)
        try:
            self.cursor.execute("INSERT INTO users (username, password_hash, salt) VALUES (?, ?, ?)", (username, password_hash, salt))
            self.db.commit()
            return True, "User registered successfully"
        except sqlite3.IntegrityError:
            return False, "Username already exists"

    def authenticate_user(self, username, password):
        # Rate limiting
        if self.is_rate_limited(username):
            return False, "Too many attempts, please try again later"

        # Fetch user from database
        self.cursor.execute("SELECT password_hash, salt FROM users WHERE username = ?", (username,))
        user = self.cursor.fetchone()

        if user is None:
            return False, "User not found"
        
        password_hash, salt = user
        input_password_hash, _ = self.hash_password(password, salt)

        if input_password_hash == password_hash:
            return True, "Authentication successful"
        else:
            return False, "Incorrect password"

    def is_rate_limited(self, username):
        key = f'rate_limit:{username}'
        if self.cache.get(key):
            return True
        self.cache.set(key, 1, ex=60)
        return False

    def recover_account(self, username, recovery_code):
        # This is a simplified recovery mechanism
        if not username or not recovery_code:
            return False, "Username and recovery code are required"

        # Fetch recovery code from database
        self.cursor.execute("SELECT recovery_code FROM users WHERE username = ?", (username,))
        stored_code = self.cursor.fetchone()

        if stored_code is None or stored_code[0] != recovery_code:
            return False, "Invalid recovery code"

        # Generate a new password and send it to the user
        new_password = os.urandom(16).hex()
        password_hash, salt = self.hash_password(new_password)
        self.cursor.execute("UPDATE users SET password_hash = ?, salt = ? WHERE username = ?", (password_hash, salt, username))
        self.db.commit()

        # Send new password to user (using a simple REST API call)
        requests.post('http://example.com/send_password', data={'username': username, 'password': new_password})

        return True, "Account recovery successful"

    def validate_input(self, data):
        # Basic input validation
        if not data or not isinstance(data, dict):
            return False, "Invalid input data"
        if 'username' not in data or 'password' not in data:
            return False, "Username and password are required"
        if not isinstance(data['username'], str) or not isinstance(data['password'], str):
            return False, "Username and password must be strings"
        return True, "Input data is valid"

    def login(self, username, password):
        # Validate input
        valid, msg = self.validate_input({'username': username, 'password': password})
        if not valid:
            return False, msg

        # Authenticate user
        authenticated, msg = self.authenticate_user(username, password)
        if not authenticated:
            return False, msg

        # Generate a session token
        session_token = self.encrypt_data(f"{username}:{int(time.time())}")
        self.cache.set(f'session:{username}', session_token, ex=3600)  # Cache the session token for 1 hour

        return True, session_token

    def logout(self, session_token):
        # Decrypt session token
        try:
            session_data = self.decrypt_data(session_token)
            username, timestamp = session_data.split(':')
            if int(time.time()) - int(timestamp) > 3600:  # Check if token is stale
                return False, "Stale session token"
        except (ValueError, TypeError):
            return False, "Invalid session token"

        # Invalidate session token
        self.cache.delete(f'session:{username}')
        return True, "Logged out successfully"

    def get_user_info(self, session_token):
        # Decrypt session token
        try:
            session_data = self.decrypt_data(session_token)
            username, timestamp = session_data.split(':')
            if int(time.time()) - int(timestamp) > 3600:  # Check if token is stale
                return False, "Stale session token"
        except (ValueError, TypeError):
            return False, "Invalid session token"

        # Fetch user info from database
        self.cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
        user_info = self.cursor.fetchone()
        if user_info is None:
            return False, "User not found"

        # Return user info (excluding sensitive data)
        user_info_dict = {
            'id': user_info[0],
            'username': user_info[1],
            # 'password_hash': user_info[2],  # This should not be returned
            # 'salt': user_info[3],  # This should not be returned
        }
        return True, user_info_dict

    def update_user_password(self, username, old_password, new_password):
        # Validate input
        valid, msg = self.validate_input({'username': username, 'old_password': old_password, 'new_password': new_password})
        if not valid:
            return False, msg

        # Authenticate user with old password
        authenticated, msg = self.authenticate_user(username, old_password)
        if not authenticated:
            return False, msg

        # Update password
        password_hash, salt = self.hash_password(new_password)
        self.cursor.execute("UPDATE users SET password_hash = ?, salt = ? WHERE username = ?", (password_hash, salt, username))
        self.db.commit()

        return True, "Password updated successfully"

    def handle_authentication_failure(self, username):
        # Increment failure count in cache
        key = f'auth_failures:{username}'
        failure_count = self.cache.get(key)
        if failure_count is None:
            failure_count = 0
        failure_count = int(failure_count) + 1
        self.cache.set(key, failure_count, ex=3600)  # Cache for 1 hour

        # Lock account if too many failures
        if failure_count >= 5:
            self.lock_account(username)
            return False, "Account locked due to too many failed attempts"
        return False, "Authentication failed"

    def lock_account(self, username):
        # Lock account for 1 hour
        self.cache.set(f'locked_account:{username}', 1, ex=3600)
        return True, "Account locked successfully"

    def is_account_locked(self, username):
        return self.cache.get(f'locked_account:{username}') is not None

    def is_rate_limited(self, username):
        key = f'rate_limit:{username}'
        if self.cache.get(key):
            return True
        self.cache.set(key, 1, ex=60)
        return False

    def is_session_valid(self, session_token):
        try:
            session_data = self.decrypt_data(session_token)
            username, timestamp = session_data.split(':')
            if int(time.time()) - int(timestamp) > 3600:  # Check if token is stale
                return False, "Stale session token"
        except (ValueError, TypeError):
            return False, "Invalid session token"

        return True, username

    def get_user_by_id(self, user_id):
        # Fetch user info from database by ID
        self.cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        user_info = self.cursor.fetchone()
        if user_info is None:
            return False, "User not found"

        # Return user info (excluding sensitive data)
        user_info_dict = {
            'id': user_info[0],
            'username': user_info[1],
            # 'password_hash': user_info[2],  # This should not be returned
            # 'salt': user_info[3],  # This should not be returned
        }
        return True, user_info_dict

    def delete_user(self, user_id):
        # Delete user from database
        self.cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
        self.db.commit()
        return True, "User deleted successfully"

    def backup_database(self, filename='backup.db'):
        # Backup the database to a file
        conn = sqlite3.connect(filename)
        with conn:
            self.db.backup(conn)
        conn.close()
        return True, "Database backup successful"

    def restore_database(self, filename='backup.db'):
        # Restore the database from a file
        conn = sqlite3.connect(filename)
        with self.db:
            conn.backup(self.db)
        conn.close()
        return True, "Database restore successful"

    def __del__(self):
        # Close database connection on object deletion
        self.db.close()
        # self.cache.close()  # This should be self.cache.flushall() or similar

# Flask routes
auth_system = AuthenticationSystem()

@app.route('/register', methods=['POST'])
@limiter.limit(auth_system.rate_limit)
def register():
    data = request.json
    success, msg = auth_system.register_user(data.get('username'), data.get('password'))
    return jsonify({'success': success, 'message': msg})

@app.route('/login', methods=['POST'])
@limiter.limit(auth_system.rate_limit)
def login():
    data = request.json
    success, msg = auth_system.login(data.get('username'), data.get('password'))
    if not success:
        auth_system.handle_authentication_failure(data.get('username'))
    return jsonify({'success': success, 'message': msg})

@app.route('/logout', methods=['POST'])
def logout():
    data = request.json
    success, msg = auth_system.logout(data.get('session_token'))
    return jsonify({'success': success, 'message': msg})

@app.route('/recover', methods=['POST'])
def recover():
    data = request.json
    success, msg = auth_system.recover_account(data.get('username'), data.get('recovery_code'))
    return jsonify({'success': success, 'message': msg})

@app.route('/user_info', methods=['GET'])
def user_info():
    session_token = request.args.get('session_token')
    success, msg = auth_system.get_user_info(session_token)
    if success:
        return jsonify({'success': success, 'user_info': msg})
    return jsonify({'success': success, 'message': msg})

@app.route('/update_password', methods=['POST'])
def update_password():
    data = request.json
    success, msg = auth_system.update_user_password(data.get('username'), data.get('old_password'), data.get('new_password'))
    return jsonify({'success': success, 'message': msg})

@app.route('/backup', methods=['POST'])
def backup():
    success, msg = auth_system.backup_database()
    return jsonify({'success': success, 'message': msg})

@app.route('/restore', methods=['POST'])
def restore():
    success, msg = auth_system.restore_database()
    return jsonify({'success': success, 'message': msg})

if __name__ == '__main__':
    app.run(debug=True)