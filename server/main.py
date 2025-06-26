import socket
import rsa
import zlib
import time
import json
import hashlib
import os
from datetime import datetime

from threading import Thread
from rich import print

# Import the database
from database import Database

# Read config file
config_file = "config.json"
with open(config_file, "r") as f:
    config_json = json.load(f)
  
# Vars
clients = []
nicknames = []
client_ips = {}  # To store client IP addresses

# Database initialization
db = Database(config_json.get("database_file", "chat_database.db"))
 
"""
ip : The IP address where the server will start listening for connections
port : The connection port, it is recommended to keep it default (8889)
buffer : The maximum network buffer
welcome_message : Welcome message to new users
"""

ip: str = config_json["ip"]
port: int = config_json["port"]
buffer: int = config_json["buffer"]
welcome_message: str = config_json["welcome_message"]
protected_by_password: bool = config_json["protected_by_password"]
password: str = config_json["password"]

# Additional configuration options
save_chat_history = config_json.get("save_chat_history", True)
max_login_attempts = config_json.get("max_login_attempts", 3)
admin_commands_enabled = config_json.get("admin_commands_enabled", True)

# Create socket
server = socket.socket()

# Start listing
server.bind((ip, port))
print(f"[[green]![/green]] Listing: {ip}:{port}")
server.listen(32)


class API:
    """
    def create_keys (buffer: int):
        Generate an RSA key

    def send_buffer (socket, buffer: int):
        Send the buffer to the client

    class Chat:
        arg: private_key, public_key

        def send (socket, message: str):
            Send encrypted message

        def recv (socketm, message: str):
            Receives a message and decrypt it

    class RSA:
        arg: public_key, private_key

        def encryption (message: str):
            Encrypt message

        def decrypt (message: bytes):
            Decrypt message
    """

    def create_keys(buffer: int):
        public_key, private_key = rsa.newkeys(buffer)
        return public_key, private_key

    def send_buffer(s, buffer: int):
        s.send(str(buffer).encode())

    class Chat:
        def __init__(self, priv_key, pub_key) -> None:
            self.priv_key = priv_key
            self.pub_key = pub_key

        def send(self, s, msg: str):
            s.send(rsa.encrypt(msg.encode(), self.pub_key))

        def recv(self, s, buffer: int):
            msg = s.recv(buffer)
            return rsa.decrypt(msg, self.priv_key)

    class Send_keys:
        def __init__(self, pub_key, priv_key, client) -> None:
            self.client = client
            self.pub_key = pub_key
            self.priv_key = priv_key

        def private(self):
            private_key_exported = rsa.PrivateKey.save_pkcs1(self.priv_key)
            # compressing
            private_key_exported = zlib.compress(private_key_exported, 4)
            self.client.send(private_key_exported)

        def public(self):
            public_key_exported = rsa.PublicKey.save_pkcs1(self.pub_key)
            # compressing
            public_key_exported = zlib.compress(public_key_exported, 4)
            self.client.send(public_key_exported)

    class RSA:
        def __init__(self, pub_key, priv_key) -> None:
            self.pub_key = pub_key
            self.priv_key = priv_key

        def encrypt(self, msg: str):
            return rsa.encrypt(msg.encode(), self.pub_key)

        def decrypt(self, msg: bytes):
            return rsa.decrypt(msg, self.priv_key)


class Chat:
    """
    Args: client (socket), private_key, public_key

    def joined (nickname: str):
        It will send a message when a client disconnect

    def welcome_message (bytes: bytes):
        It will send the clients the encrypted welcome message

    def send_to_clients (message: bytes):
        It sends clients a message, but it won't be able to send it to itself

    def remove_client (client):
        removes clients from the client list

    def middle:
        When a customer enters the chat, perform this function.
        Send clients a message announcing that a client has logged in,
        then wait for a message from the client and then send it to all

    def run:
        It's where this class will launch
    """

    def __init__(self, client, private_key, public_key) -> None:
        self.client = client
        self.private_key = private_key
        self.public_key = public_key
        self.client_ip = client.getpeername()[0]
        self.nickname = None
        self.is_admin = False

    def joined(self, nickname: str):
        join_message = f"[green]{nickname}[/green] has joined."
        self.send_to_clients(self.rsa_api.encrypt(join_message))
        
        # Save join message to database if enabled
        if save_chat_history:
            db.save_message("System", join_message)

    def welcome_message(self, welcome_message: bytes):
        self.client.send(welcome_message)

    def send_to_clients(self, msg: bytes):
        for client in clients:
            if client != self.client:
                try:
                    client.send(msg)
                except BaseException:
                    self.remove_client(client)

    def remove_client(self, client):
        print(f"[[yellow]?[/yellow]] Client disconnected")

        if client in clients:
            index = clients.index(client)
            # Remove from list
            clients.remove(client)
            
            # Get username from socket
            if index < len(nicknames):
                nickname = nicknames[index]
                
                leave_message = f"[green]{nickname}[/green] has left."
                self.send_to_clients(self.rsa_api.encrypt(leave_message))
                
                # Save leave message to database if enabled
                if save_chat_history:
                    db.save_message("System", leave_message)
                
                # Remove nickname
                nicknames.remove(nickname)
                
                # Remove from client_ips dict
                if nickname in client_ips:
                    del client_ips[nickname]

    def handle_admin_command(self, command):
        """Handle admin commands"""
        parts = command.split()
        if len(parts) < 2:
            return
            
        cmd = parts[1]
        
        if cmd == "ban" and len(parts) >= 3:
            user_to_ban = parts[2]
            reason = " ".join(parts[3:]) if len(parts) > 3 else "No reason provided"
            
            if user_to_ban in client_ips:
                ip_to_ban = client_ips[user_to_ban]
                db.ban_user(ip_to_ban, reason)
                
                # Notify admin
                admin_msg = f"User {user_to_ban} has been banned. Reason: {reason}"
                self.client.send(self.rsa_api.encrypt(f"[red]ADMIN:[/red] {admin_msg}"))
                
                # Disconnect the banned user
                for i, nick in enumerate(nicknames):
                    if nick == user_to_ban and i < len(clients):
                        try:
                            clients[i].send(self.rsa_api.encrypt("[red]You have been banned from this server.[/red]"))
                            clients[i].close()
                        except:
                            pass
        
        elif cmd == "history" and len(parts) >= 3:
            try:
                limit = int(parts[2])
                messages = db.get_recent_messages(limit)
                
                history_msg = "[yellow]--- Chat History ---[/yellow]\n"
                for username, content, timestamp in messages:
                    dt = datetime.fromtimestamp(timestamp) if isinstance(timestamp, (int, float)) else timestamp
                    formatted_time = dt.strftime("%Y-%m-%d %H:%M:%S")
                    history_msg += f"[{formatted_time}] <{username}> {content}\n"
                
                self.client.send(self.rsa_api.encrypt(history_msg))
            except:
                self.client.send(self.rsa_api.encrypt("[red]Error retrieving chat history[/red]"))
        
        elif cmd == "dbstats":
            # Get database statistics
            num_users = len(db.get_all_users())
            num_messages = len(db.get_all_messages())
            admin_msg = f"[yellow]Database Stats:[/yellow]\nUsers: {num_users}\nMessages: {num_messages}"
            self.client.send(self.rsa_api.encrypt(admin_msg))

    def middle(self):
        index = clients.index(self.client)
        nickname = nicknames[index]
        self.nickname = nickname
        self.joined(nickname)

        while True:
            try:
                msg = self.client.recv(buffer)
                
                # If empty message, client disconnected
                if not msg:
                    self.remove_client(self.client)
                    break
                
                # Decrypt the message
                try:
                    decrypted_msg = self.rsa_api.decrypt(msg).decode()
                    
                    # Handle admin commands
                    if decrypted_msg.startswith("/admin ") and self.is_admin and admin_commands_enabled:
                        self.handle_admin_command(decrypted_msg)
                        continue
                    
                    # Check for exit command
                    if decrypted_msg == "/exit":
                        self.remove_client(self.client)
                        break
                    
                    # Save message to database if enabled
                    if save_chat_history:
                        db.save_message(nickname, decrypted_msg)
                    
                    # Check if it's a file upload message
                    if "[b]Shared file:[/b]" in decrypted_msg:
                        # Extract file URL
                        file_url = decrypted_msg.split("[b]Shared file:[/b]")[1].strip()
                        # Save to database
                        db.save_shared_file(nickname, "shared_file", file_url)
                    
                except:
                    # Unable to decrypt, just forward the message
                    pass
                
                # Forward message to all clients
                self.send_to_clients(msg)

            except Exception as e:
                print(f"[[red]![/red]] Error handling client message: {e}")
                self.remove_client(self.client)
                break

    def run(self):
        try:
            # Check if IP is banned
            if db.is_banned(self.client_ip):
                self.client.send("banned".encode())
                self.client.close()
                return
                
            login_attempts = 0
            username_exist = False
            
            if protected_by_password:
                self.client.send("protected".encode())
                
                while login_attempts < max_login_attempts:
                    user_passwd = self.client.recv(1024).decode()
                    if user_passwd == hashlib.md5(password.encode()).hexdigest():
                        self.client.send("/accepted".encode())
                        break
                    else:
                        login_attempts += 1
                        if login_attempts >= max_login_attempts:
                            self.client.send("/exit".encode())
                            self.client.close()
                            return
                        self.client.send("/retry".encode())
            else:
                self.client.send("no_protected".encode())

            nickname = self.client.recv(buffer).decode()

            # Check username existing
            for list_nickname in nicknames:
                if not username_exist and nickname == list_nickname:
                    username_exist = True

            # If username doesn't exist
            if not username_exist:
                # Send message: "accepted" to client
                self.client.send("/accepted".encode())
                print(f"[[yellow]?[/yellow]] Client connected: {nickname} from {self.client_ip}")

                # Check if user is admin
                self.is_admin = db.is_user_admin(nickname)
                
                # Add to tracking structures
                nicknames.append(nickname)
                clients.append(self.client)
                client_ips[nickname] = self.client_ip
            else:
                # Send message: "exit" to client
                self.client.send("/exit".encode())
                self.client.close()
                return
        except Exception as e:
            print(f"[[red]![/red]] Error during authentication: {e}")
            try:
                self.client.close()
            except:
                pass
            return
        
        try:
            API.send_buffer(self.client, buffer)
        except Exception as e:
            print(f"[[red]![/red]] Error sending buffer: {e}")
            return
        
        time.sleep(0.5)
        
        try:
            send_keys = API.Send_keys(
                self.public_key,
                self.private_key,
                self.client)

            self.rsa_api = API.RSA(self.public_key, self.private_key)
            self.chat_api = API.Chat(self.private_key, self.public_key)

            send_keys.public()
            time.sleep(0.5)
            send_keys.private()
            time.sleep(0.5)

            # Encrypt welcome_message and send to client
            self.welcome_message(self.rsa_api.encrypt(welcome_message))
            
            # If user is admin, send admin notification
            if self.is_admin:
                admin_welcome = "[red]You are logged in as an administrator. Use /admin command <args> for admin functions.[/red]"
                self.client.send(self.rsa_api.encrypt(admin_welcome))
            
            # Begin message handling
            self.middle()
            
        except Exception as e:
            print(f"[[red]![/red]] Error in connection setup: {e}")
            self.remove_client(self.client)


class Main:
    """
    def run:
        It will generate keys and wait for connections
    """
    def run():
        username_exist = False

        print(f"[[magenta]*[/magenta]] Buffer: {buffer}")
        print(f"[[blue]*[/blue]] Database initialized")

        print("[[cyan]+[/cyan]] RSA key generation...")
        public_key, private_key = API.create_keys(buffer)
        print("[[cyan]+[/cyan]] RSA key generated")

        try:
            # Get historic messages
            recent_messages = db.get_recent_messages(10)
            if recent_messages:
                print("[[green]+[/green]] Recent chat history:")
                for username, content, timestamp in recent_messages[-5:]:
                    dt = datetime.fromtimestamp(timestamp) if isinstance(timestamp, (int, float)) else timestamp
                    formatted_time = dt.strftime("%Y-%m-%d %H:%M:%S")
                    print(f"  [{formatted_time}] <{username}> {content}")
        except Exception as e:
            print(f"[[red]![/red]] Error retrieving chat history: {e}")

        while True:
            try:
                client, addr = server.accept()
                chat = Chat(client, private_key, public_key)

                multi_conn = Thread(target=chat.run)
                multi_conn.daemon = True
                multi_conn.start()
            except Exception as e:
                print(f"[[red]![/red]] Error accepting connection: {e}")
                time.sleep(1)  # Avoid CPU spinning on repeated errors

if __name__ == "__main__":
    try:
        Main.run()
    except KeyboardInterrupt:
        print("\n[[yellow]*[/yellow]] Server shutting down...")
    except Exception as e:
        print(f"[[red]![/red]] Fatal error: {e}")
    finally:
        db.close()
        server.close()