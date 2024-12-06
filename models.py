from werkzeug.security import generate_password_hash
from flask_login import UserMixin
import mysql.connector
from config import DATABASE

# Database connection function
def get_db_connection():
    conn = mysql.connector.connect(
        host=DATABASE['host'],
        user=DATABASE['user'],
        password=DATABASE['password'],
        database=DATABASE['database']
    )
    return conn

# User model class
class User(UserMixin):
    def __init__(self, user_id, username, password_hash, role):
        self.id = user_id
        self.username = username
        self.password_hash = password_hash
        self.role = role

    @staticmethod
    def get_by_id(user_id):
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute('SELECT * FROM Users WHERE user_id = %s', (user_id,))
        user = cursor.fetchone()
        cursor.close()
        conn.close()
        if user:
            return User(user['user_id'], user['username'], user['password_hash'], user['role'])
        return None

    @staticmethod
    def get_by_username(username):
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute('SELECT * FROM Users WHERE username = %s', (username,))
        user = cursor.fetchone()
        cursor.close()
        conn.close()
        if user:
            return User(user['user_id'], user['username'], user['password_hash'], user['role'])
        return None
