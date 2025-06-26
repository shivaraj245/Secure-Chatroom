import sqlite3
import os
from datetime import datetime

def view_database(db_file="chat_database.db"):
    if not os.path.exists(db_file):
        print(f"Database file '{db_file}' not found!")
        return
    
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    
    # Display users
    print("\n=== USERS ===")
    cursor.execute("SELECT id, username, password, last_login, created_at, is_admin FROM users")
    users = cursor.fetchall()
    if users:
        for user in users:
            user_id, username, password, last_login, created_at, is_admin = user
            print(f"ID: {user_id} | Username: {username} | Admin: {'Yes' if is_admin else 'No'}")
    else:
        print("No users found")
    
    # Display messages
    print("\n=== RECENT MESSAGES ===")
    cursor.execute("""
        SELECT users.username, messages.content, messages.timestamp 
        FROM messages 
        JOIN users ON messages.user_id = users.id 
        ORDER BY messages.timestamp DESC 
        LIMIT 10
    """)
    messages = cursor.fetchall()
    if messages:
        for msg in messages:
            username, content, timestamp = msg
            print(f"<{username}> {content}")
    else:
        print("No messages found")
    
    # Display shared files
    print("\n=== SHARED FILES ===")
    cursor.execute("""
        SELECT users.username, shared_files.filename, shared_files.file_url, shared_files.timestamp 
        FROM shared_files 
        JOIN users ON shared_files.user_id = users.id 
        ORDER BY shared_files.timestamp DESC
    """)
    files = cursor.fetchall()
    if files:
        for file in files:
            username, filename, file_url, timestamp = file
            print(f"User: {username} | File: {filename} | URL: {file_url}")
    else:
        print("No shared files found")
    
    # Display banned users
    print("\n=== BANNED USERS ===")
    cursor.execute("SELECT ip_address, reason, banned_until, banned_at FROM banned_users")
    banned = cursor.fetchall()
    if banned:
        for ban in banned:
            ip, reason, banned_until, banned_at = ban
            print(f"IP: {ip} | Reason: {reason} | Until: {datetime.fromtimestamp(banned_until)}")
    else:
        print("No banned users found")
    
    conn.close()

if __name__ == "__main__":
    view_database()
    print("\nPress Enter to exit...")
    input()