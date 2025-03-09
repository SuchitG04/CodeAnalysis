# AuthSystem.py
# Simulates an authentication system with varying code quality and practices.

import json
import requests
from datetime import datetime
from pymongo import MongoClient

# TODO: Refactor this into a config file
DB_CONNECTION_STRING = "mongodb://localhost:27017/"
API_ENDPOINT = "https://api.example.com/auth"

# FIXME: This should be encrypted or stored securely
API_KEY = "12345-ABCDE"

# Mix of well-named and poorly named variables
user_data = None  # Poorly named, unclear purpose
auth_token = ""  # Well-named, clear purpose

# Inconsistent naming conventions
def checkAuthToken(token):
    """Checks if the authentication token is valid."""
    # Bare except clause, poor error handling
    try:
        response = requests.post(API_ENDPOINT, json={"token": token}, headers={"Authorization": API_KEY})
        return response.status_code == 200
    except:
        print("Error checking token")  # Generic error message
        return False

# Function with no documentation
def fetch_user_data(user_id):
    global user_data
    client = MongoClient(DB_CONNECTION_STRING)
    db = client.user_db
    user_data = db.users.find_one({"user_id": user_id})
    client.close()  # Proper resource cleanup
    return user_data

# Function with detailed docstring
def schedule_task(task_name, schedule_time):
    """
    Schedules a task for a specific time.

    Args:
        task_name (str): Name of the task to schedule.
        schedule_time (datetime): Time at which the task should be executed.

    Returns:
        bool: True if the task was successfully scheduled, False otherwise.
    """
    if not task_name or not schedule_time:
        print("Invalid task name or schedule time")  # Debug print statement
        return False

    # Hardcoded value, poor practice
    if schedule_time < datetime.now():
        print("Cannot schedule tasks in the past")
        return False

    # Confusing logic flow
    try:
        # Duplicate code, could be refactored
        response = requests.post(API_ENDPOINT + "/schedule", json={"task": task_name, "time": schedule_time.isoformat()}, headers={"Authorization": API_KEY})
        if response.status_code == 200:
            return True
        else:
            print(f"Failed to schedule task: {response.text}")  # Detailed error message
            return False
    except Exception as e:
        print(f"Error scheduling task: {e}")  # Generic error message
        return False

# Poorly named function and variables
def x(data):
    """Compresses data and returns the result."""
    # Unclear abbreviation and poor variable naming
    if not data:
        return None

    # Improper resource cleanup
    with open("temp.json", "w") as f:
        json.dump(data, f)

    # FIXME: Implement actual compression logic
    return data

# Function with outdated comments
def generate_report(user_id):
    # This function generates a report for the given user ID
    user_data = fetch_user_data(user_id)
    if not user_data:
        print("User data not found")  # Unhandled error case
        return None

    # Confusing logic and poor variable naming
    report = {}
    for k, v in user_data.items():
        if k in ["name", "email", "last_login"]:
            report[k] = v

    # Debug print statement left in code
    print(f"Generated report: {report}")
    return report

# Function with mixed error handling
def authorize_action(user_id, action):
    """Authorizes a specific action for the user."""
    if not user_id or not action:
        raise ValueError("Invalid user ID or action")  # Proper error handling

    # Unhandled error case
    user_data = fetch_user_data(user_id)
    if not user_data:
        return False

    # Confusing logic flow
    try:
        response = requests.post(API_ENDPOINT + "/authorize", json={"user_id": user_id, "action": action}, headers={"Authorization": API_KEY})
        return response.status_code == 200
    except requests.exceptions.RequestException as e:
        print(f"Authorization error: {e}")  # Detailed error message
        return False

# Main function with mixed practices
def main():
    # Poorly named variable
    x = "test_user"

    # Properly named variable
    auth_token = "abc123"

    # Check authentication token
    if not checkAuthToken(auth_token):
        print("Invalid token")  # Generic error message
        return

    # Schedule a task
    task_scheduled = schedule_task("generate_report", datetime.now())
    if not task_scheduled:
        print("Failed to schedule task")  # Debug print statement

    # Generate a report
    report = generate_report(x)
    if report:
        print("Report generated successfully")  # Debug print statement

    # Authorize an action
    authorized = authorize_action(x, "view_report")
    if authorized:
        print("Action authorized")  # Debug print statement

if __name__ == "__main__":
    main()