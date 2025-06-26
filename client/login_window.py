import tkinter as tk
import random
import hashlib
from constants import *

class LoginWindow:
    def __init__(self, root, on_login):
        self.root = root
        self.on_login = on_login
        self.root.title("DARK ROOM - Secure Chat")
        self.root.geometry("600x400")
        self.root.configure(bg=DARK_BG)
        
        # Bind Escape key to close window
        self.root.bind('<Escape>', lambda e: self.root.destroy())
        
        # Banner
        self.banner_label = tk.Label(root, text=BANNER, font=("Courier", 10, "bold"), 
                                   fg=BUTTON_BG, bg=DARK_BG)
        self.banner_label.pack(pady=5)
        
        # Server address
        self.server_frame = tk.Frame(root, bg=DARK_BG)
        self.server_frame.pack(pady=5, fill=tk.X, padx=20)
        self.server_label = tk.Label(self.server_frame, text="Server address:", 
                                  fg=TEXT_COLOR, bg=DARK_BG, font=("Arial", 10, "bold"))
        self.server_label.pack(side=tk.LEFT)
        self.server_entry = tk.Entry(self.server_frame, bg=ENTRY_BG, fg=ENTRY_FG,
                                  insertbackground=ENTRY_FG)
        self.server_entry.insert(0, "172.16.241.127")  # Default address
        self.server_entry.pack(side=tk.RIGHT, expand=True, fill=tk.X)
        
        # Server port
        self.port_frame = tk.Frame(root, bg=DARK_BG)
        self.port_frame.pack(pady=5, fill=tk.X, padx=20)
        self.port_label = tk.Label(self.port_frame, text="Server port:", 
                                fg=TEXT_COLOR, bg=DARK_BG, font=("Arial", 10, "bold"))
        self.port_label.pack(side=tk.LEFT)
        self.port_entry = tk.Entry(self.port_frame, bg=ENTRY_BG, fg=ENTRY_FG,
                               insertbackground=ENTRY_FG)
        self.port_entry.insert(0, "8889")  # Default port
        self.port_entry.pack(side=tk.RIGHT, expand=True, fill=tk.X)
        
        # Username
        self.username_frame = tk.Frame(root, bg=DARK_BG)
        self.username_frame.pack(pady=5, fill=tk.X, padx=20)
        self.username_label = tk.Label(self.username_frame, text="Username:", 
                                    fg=TEXT_COLOR, bg=DARK_BG, font=("Arial", 10, "bold"))
        self.username_label.pack(side=tk.LEFT)
        self.username_entry = tk.Entry(self.username_frame, bg=ENTRY_BG, fg=ENTRY_FG,
                                    insertbackground=ENTRY_FG)
        self.username_entry.pack(side=tk.RIGHT, expand=True, fill=tk.X)
        
        # Password
        self.password_frame = tk.Frame(root, bg=DARK_BG)
        self.password_frame.pack(pady=5, fill=tk.X, padx=20)
        self.password_label = tk.Label(self.password_frame, text="Password:", 
                                    fg=TEXT_COLOR, bg=DARK_BG, font=("Arial", 10, "bold"))
        self.password_label.pack(side=tk.LEFT)
        self.password_entry = tk.Entry(self.password_frame, show="*", bg=ENTRY_BG, fg=ENTRY_FG,
                                    insertbackground=ENTRY_FG)
        self.password_entry.insert(0, "test")  # Default password
        self.password_entry.pack(side=tk.RIGHT, expand=True, fill=tk.X)
        
        # Status message
        self.status_label = tk.Label(root, text="Enter credentials and click Connect", 
                                  fg=SUCCESS_COLOR, bg=DARK_BG)
        self.status_label.pack(pady=5)
        
        # Connect button
        self.connect_button = tk.Button(root, text="Connect", command=self.connect, 
                                     bg=BUTTON_BG, fg=BUTTON_FG, font=("Arial", 10, "bold"),
                                     activebackground=HIGHLIGHT_COLOR, activeforeground=TEXT_COLOR,
                                     relief=tk.RAISED, bd=2, padx=20, pady=5)
        self.connect_button.pack(pady=10)
        
        # Add Escape hint
        self.escape_label = tk.Label(root, text="Press ESC to exit", 
                                  fg="#555555", bg=DARK_BG, font=("Arial", 8))
        self.escape_label.pack(side=tk.BOTTOM, pady=5)
    
    def random_color(self):
        colors = [
            "red", "blue", "cyan", "yellow", "magenta", 
            "green", "purple", "violet", "gold"
        ]
        return random.choice(colors)
    
    def connect(self):
        self.status_label.config(text="Connecting...", fg="#FFA500")  # Orange for connecting
        self.root.update()
        
        server_ip = self.server_entry.get()
        if server_ip in ["local", "localhost", "::1"]:
            server_ip = "127.0.0.1"
            
        try:
            server_port = int(self.port_entry.get())
        except ValueError:
            self.status_label.config(text="Error: Port must be a number", fg=ERROR_COLOR)
            return
            
        username = self.username_entry.get()
        if not username:
            self.status_label.config(text="Error: Username cannot be empty", fg=ERROR_COLOR)
            return
            
        color = self.random_color()
        username_styled = f"<[{color}]{username}[/{color}]>"
        
        password = self.password_entry.get()
        password_hash = hashlib.md5(password.encode()).hexdigest()
        
        # Call the on_login callback with the login info
        self.on_login(server_ip, server_port, username, username_styled, password_hash)