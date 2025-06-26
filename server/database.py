
import sqlite3
import os
import hashlib
import time
from datetime import datetime

class Database:
    def __init__(self, db_file="chat_database.db"):
        """Initialize database connection and create tables if they don't exist"""
        self.db_file = db_file
        
        # Create database directory if it doesn't exist
        db_dir = os.path.dirname(db_file)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir)
            
        self.conn = sqlite3.connect(db_file, check_same_thread=False)
        self.cursor = self.conn.cursor()
        self.create_tables()
        
    def create_tables(self):
        """Create necessary tables if they don't exist"""
        # Users table
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            last_login TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            is_admin INTEGER DEFAULT 0
        )
        ''')
        
        # Messages table
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            content TEXT NOT NULL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
        ''')
        
        # Shared files table
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS shared_files (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            filename TEXT NOT NULL,
            file_url TEXT NOT NULL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
        ''')
        
        # Banned users table
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS banned_users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ip_address TEXT NOT NULL,
            reason TEXT,
            banned_until TIMESTAMP,
            banned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # Add default admin account if it doesn't exist
        admin_password = hashlib.md5("admin123".encode()).hexdigest()
        self.cursor.execute('''
        INSERT OR IGNORE INTO users (username, password, is_admin)
        VALUES (?, ?, 1)
        ''', ("admin", admin_password))
        
        self.conn.commit()
    
    def register_user(self, username, password_hash):
        """Register a new user"""
        try:
            self.cursor.execute(
                "INSERT INTO users (username, password) VALUES (?, ?)",
                (username, password_hash)
            )
            self.conn.commit()
            return True
        except sqlite3.IntegrityError:
            # Username already exists
            return False
    
    def authenticate_user(self, username, password_hash):
        """Authenticate a user"""
        self.cursor.execute(
            "SELECT id, password FROM users WHERE username = ?",
            (username,)
        )
        user = self.cursor.fetchone()
        
        if user and user[1] == password_hash:
            # Update last login time
            self.cursor.execute(
                "UPDATE users SET last_login = ? WHERE id = ?",
                (datetime.now(), user[0])
            )
            self.conn.commit()
            return True
        return False
    
    def is_user_admin(self, username):
        """Check if user is an admin"""
        self.cursor.execute(
            "SELECT is_admin FROM users WHERE username = ?",
            (username,)
        )
        result = self.cursor.fetchone()
        return bool(result and result[0])
    
    def save_message(self, username, message):
        """Save a chat message"""
        # Get or create user
        self.cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
        user = self.cursor.fetchone()
        
        if not user:
            # For system messages, create a system user if it doesn't exist
            if username == "System":
                self.cursor.execute(
                    "INSERT OR IGNORE INTO users (username, password) VALUES (?, ?)",
                    (username, hashlib.md5(os.urandom(16).hex().encode()).hexdigest())
                )
                self.cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
                user = self.cursor.fetchone()
            else:
                # Create a regular user if needed
                self.register_user(username, hashlib.md5(os.urandom(16).hex().encode()).hexdigest())
                self.cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
                user = self.cursor.fetchone()
                
        if user:
            self.cursor.execute(
                "INSERT INTO messages (user_id, content) VALUES (?, ?)",
                (user[0], message)
            )
            self.conn.commit()
            return True
        return False
    
    def get_recent_messages(self, limit=50):
        """Get recent chat messages"""
        self.cursor.execute('''
        SELECT users.username, messages.content, messages.timestamp
        FROM messages
        JOIN users ON messages.user_id = users.id
        ORDER BY messages.timestamp DESC
        LIMIT ?
        ''', (limit,))
        
        return self.cursor.fetchall()
    
    def save_shared_file(self, username, filename, file_url):
        """Save a record of a shared file"""
        self.cursor.execute(
            "SELECT id FROM users WHERE username = ?",
            (username,)
        )
        user = self.cursor.fetchone()
        
        if not user:
            # Create user if needed
            self.register_user(username, hashlib.md5(os.urandom(16).hex().encode()).hexdigest())
            self.cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
            user = self.cursor.fetchone()
            
        if user:
            self.cursor.execute(
                "INSERT INTO shared_files (user_id, filename, file_url) VALUES (?, ?, ?)",
                (user[0], filename, file_url)
            )
            self.conn.commit()
            return True
        return False
    
    def ban_user(self, ip_address, reason=None, duration_hours=24):
        """Ban a user by IP address"""
        banned_until = datetime.now().timestamp() + (duration_hours * 3600)
        
        self.cursor.execute(
            "INSERT INTO banned_users (ip_address, reason, banned_until) VALUES (?, ?, ?)",
            (ip_address, reason, banned_until)
        )
        self.conn.commit()
    
    def is_banned(self, ip_address):
        """Check if an IP is banned"""
        current_time = datetime.now().timestamp()
        
        self.cursor.execute(
            "SELECT banned_until FROM banned_users WHERE ip_address = ? ORDER BY banned_at DESC LIMIT 1",
            (ip_address,)
        )
        result = self.cursor.fetchone()
        
        if result and result[0] > current_time:
            return True
        return False
    
    def get_all_users(self):
        """Get all users from the database"""
        self.cursor.execute("SELECT * FROM users")
        return self.cursor.fetchall()

    def get_all_messages(self):
        """Get all messages from the database"""
        self.cursor.execute("SELECT * FROM messages")
        return self.cursor.fetchall()
    
    def close(self):
        """Close the database connection"""
        if self.conn:
            self.conn.close()