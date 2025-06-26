import os
import tkinter as tk
from tkinter import scrolledtext, messagebox, filedialog
import threading
import rsa
import zlib
import hashlib
import time
import base64
 
from constants import *
from login_window import LoginWindow
from api import API
from network import s
from file_utils import upload_file, send_file_data, save_received_file, process_file_chunk, complete_file_transfer

class ChatApp:
    def __init__(self, root):
        self.root = root
        self.root.title("DARK ROOM - Secure Chat")
        self.root.geometry("800x600")
        self.root.configure(bg=DARK_BG)
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        
        # Bind Escape key to close window
        self.root.bind('<Escape>', lambda e: self.on_close())
        
        # Initialize login screen
        self.login_window = LoginWindow(root, self.on_login)
        
        # Initialize variables
        self.chat_api = None
        self.username = ""
        self.username_styled = ""
        self.receiver_thread = None
        self.shared_files = {}
        self.file_transfers = {}  # To track ongoing file transfers
    
    def on_login(self, server_ip, server_port, username, username_styled, password_hash):
        self.username = username
        self.username_styled = username_styled
        
        try:
            # Connect to server
            s.connect((server_ip, server_port))
            
            # Check if password protected
            is_protected = s.recv(BUFFER_SIZE).decode()
            if is_protected == "protected":
                s.send(password_hash.encode())
                confirm = s.recv(BUFFER_SIZE).decode()
                if confirm != "/accepted":
                    messagebox.showerror("Authentication Failed", "Incorrect password")
                    s.close()
                    return
            
            # Send username
            s.send(username.encode())
            confirm = s.recv(BUFFER_SIZE).decode()
            if confirm != "/accepted":
                messagebox.showerror("Authentication Failed", "Username already exists")
                s.close()
                return
            
            # Get buffer size
            buffer_size = int(s.recv(BUFFER_SIZE).decode())
            
            # Get encryption keys
            public_key = zlib.decompress(s.recv(buffer_size))
            private_key = zlib.decompress(s.recv(buffer_size))
            
            # Load keys
            client_key = API.Load_keys(public_key, private_key)
            private_key, public_key = client_key.load_all()
            
            # Create API
            self.chat_api = API.Chat(private_key, public_key)
            
            # Initialize chat interface
            self.initialize_chat_ui()
            
            # Get welcome message
            welcome_msg = self.chat_api.recv(BUFFER_SIZE)
            self.display_message(welcome_msg)
            
            # Start receiving thread
            self.start_receiver()
            
        except Exception as e:
            messagebox.showerror("Connection Failed", f"Error: {str(e)}")
    
    def initialize_chat_ui(self):
        # Remove login widgets
        for widget in self.root.winfo_children():
            widget.destroy()
        
        # Header with title
        self.header_frame = tk.Frame(self.root, bg=DARKER_BG, height=40)
        self.header_frame.pack(fill=tk.X)
        
        self.title_label = tk.Label(self.header_frame, text="DARK ROOM - Secure Chat", 
                                 font=("Arial", 12, "bold"), bg=DARKER_BG, fg=BUTTON_BG)
        self.title_label.pack(side=tk.LEFT, padx=10, pady=8)
        
        self.status_label = tk.Label(self.header_frame, text=f"Connected as: {self.username}", 
                                  font=("Arial", 10), bg=DARKER_BG, fg=SUCCESS_COLOR)
        self.status_label.pack(side=tk.RIGHT, padx=10, pady=8)
        
        # Chat display
        self.chat_frame = tk.Frame(self.root, bg=DARK_BG)
        self.chat_frame.pack(padx=10, pady=5, fill=tk.BOTH, expand=True)
        
        self.chat_display = scrolledtext.ScrolledText(
            self.chat_frame, 
            wrap=tk.WORD, 
            state=tk.DISABLED,
            bg=ENTRY_BG,
            fg=TEXT_COLOR,
            insertbackground=TEXT_COLOR,
            font=("Consolas", 10)
        )
        self.chat_display.pack(fill=tk.BOTH, expand=True)
        
        # Button bar for commands
        self.cmd_frame = tk.Frame(self.root, bg=DARKER_BG)
        self.cmd_frame.pack(fill=tk.X, pady=2)
        
        cmd_buttons = [
            ("Help", self.show_help),
            ("Upload File", self.upload_file),
            ("Clear Chat", self.clear_chat)
        ]
        
        for text, command in cmd_buttons:
            btn = tk.Button(
                self.cmd_frame, 
                text=text, 
                command=command,
                bg=DARKER_BG, 
                fg=TEXT_COLOR,
                activebackground=HIGHLIGHT_COLOR, 
                activeforeground=TEXT_COLOR,
                bd=0,
                padx=10,
                pady=2
            )
            btn.pack(side=tk.LEFT, padx=5)
        
        # Message input and buttons frame
        self.input_frame = tk.Frame(self.root, bg=DARKER_BG)
        self.input_frame.pack(padx=10, pady=10, fill=tk.X)
        
        # Message input
        self.message_entry = tk.Entry(
            self.input_frame,
            bg=ENTRY_BG, 
            fg=ENTRY_FG,
            insertbackground=ENTRY_FG,
            font=("Consolas", 10)
        )
        self.message_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.message_entry.bind("<Return>", lambda event: self.send_message())
        self.message_entry.focus_set()  # Focus on input
        
        # Send button
        self.send_button = tk.Button(
            self.input_frame, 
            text="Send", 
            command=self.send_message,
            bg=BUTTON_BG, 
            fg=BUTTON_FG,
            activebackground=HIGHLIGHT_COLOR, 
            activeforeground=TEXT_COLOR,
            font=("Arial", 10, "bold"),
            padx=10
        )
        self.send_button.pack(side=tk.LEFT, padx=5)
        
        # Add Escape hint
        self.escape_label = tk.Label(self.root, text="Press ESC to exit", 
                                  fg="#555555", bg=DARK_BG, font=("Arial", 8))
        self.escape_label.pack(side=tk.BOTTOM, pady=2)
    
    def show_help(self):
        self.display_message("\n" + HELP_TEXT)
    
    def clear_chat(self):
        self.chat_display.config(state=tk.NORMAL)
        self.chat_display.delete(1.0, tk.END)
        self.chat_display.config(state=tk.DISABLED)
    
    def display_message(self, message):
        self.chat_display.config(state=tk.NORMAL)
        self.chat_display.insert(tk.END, message + "\n")
        self.chat_display.see(tk.END)  # Scroll to bottom
        self.chat_display.config(state=tk.DISABLED)
    
    def send_message(self):
        message = self.message_entry.get().strip()
        if not message:
            return
        
        self.message_entry.delete(0, tk.END)
        
        if message.startswith("/"):
            self.handle_command(message)
        else:
            try:
                self.chat_api.send(self.username_styled + " " + message)
                self.display_message(f"<You> {message}")
            except Exception as e:
                self.display_message(f"Error sending message: {str(e)}")
    
    def handle_command(self, command):
        cmd_parts = command.split()
        cmd = cmd_parts[0]
        
        if cmd == "/help":
            self.show_help()
            
        elif cmd == "/nick":
            self.display_message(f"Your nickname: {self.username}")
            
        elif cmd == "/upload":
            self.upload_file()
            
        elif cmd == "/clear":
            self.clear_chat()
            
        elif cmd == "/exit":
            self.on_close()
        
        elif cmd == "/get":
            # New command to download shared files
            if len(cmd_parts) < 2:
                self.display_message("<System> Usage: /get #code")
                return
            
            file_code = cmd_parts[1].lstrip('#')
            self.request_file(file_code)
    
    def upload_file(self):
        result = upload_file(self.display_message, self.username_styled, self.chat_api,self.username)
        if result:
            file_code, file_info = result
            self.shared_files[file_code] = file_info
    
    def request_file(self, file_code):
        """Request a file from another client using the file code"""
        self.display_message(f"<System> Requesting file with code #{file_code}...")
        
        # Send a file request through the chat
        request_msg = f"{self.username_styled} [b]Requesting file:[/b] #{file_code}"
        self.chat_api.send(request_msg)
    
    def process_file_request(self, message):
        """Process incoming file request messages"""
        try:
            # Extract the file code
            parts = message.split("[b]Requesting file:[/b] #")
            if len(parts) > 1:
                file_code = parts[1].strip()
                
                # Check if we have this file in our shared files
                if file_code in self.shared_files:
                    file_info = self.shared_files[file_code]
                    
                    # Send direct message with file data
                    send_file_data(file_code, file_info, self.display_message, 
                                  self.username_styled, self.chat_api)
        except Exception as e:
            print(f"Error processing file request: {str(e)}")
    
    def process_file_data(self, message):
        """Process and save incoming file data"""
        save_received_file(message, self.display_message)
    
    def process_file_message(self, message):
        result = save_received_file(message, self.display_message)
        
        if result:
            if result['type'] == 'start':
                # Start a new file transfer
                self.file_transfers[result['code']] = result
                self.root.after(0, lambda: self.display_message(f"<System> Starting file transfer: {result['filename']}"))
            
            elif result['type'] == 'chunk':
                # Process a chunk of an ongoing transfer
                if result['code'] in self.file_transfers:
                    updated_data = process_file_chunk(
                        self.file_transfers[result['code']], 
                        result, 
                        self.display_message
                    )
                    if updated_data:
                        self.file_transfers[result['code']] = updated_data
            
            elif result['type'] == 'end':
                # Complete a file transfer
                if result['code'] in self.file_transfers:
                    transfer_data = self.file_transfers[result['code']]
                    if transfer_data['chunks_received'] == transfer_data['total_chunks']:
                        complete_file_transfer(transfer_data, self.display_message)
                    else:
                        self.root.after(0, lambda: self.display_message(
                            f"<System> File transfer incomplete: received {transfer_data['chunks_received']} of {transfer_data['total_chunks']} chunks"
                        ))
                    # Clean up
                    del self.file_transfers[result['code']]
            
            elif result['type'] == 'legacy_complete':
                # Old-style transfer already completed
                pass
    
    def receive_messages(self):
        while True:
            try:
                message = self.chat_api.recv(BUFFER_SIZE)
                if message:
                    # Handle file transfers
                    if "[b]File start:[/b] #" in message or "[b]File chunk:[/b] #" in message or "[b]File end:[/b] #" in message or "[b]File data:[/b] #" in message:
                        self.process_file_message(message)
                    # Handle file requests
                    elif "[b]Requesting file:[/b] #" in message:
                        self.process_file_request(message)
                    # Handle other messages like "file too large"
                    elif "[b]File too large:[/b]" in message:
                        # Just display as a normal message
                        self.root.after(0, lambda msg=message: self.display_message(msg))
                    else:
                        # Regular chat message
                        self.root.after(0, lambda msg=message: self.display_message(msg))
            except rsa.pkcs1.DecryptionError:
                pass
            except Exception as e:
                if self.root:  # Check if the application is still running
                    self.root.after(0, lambda err=e: self.display_message(f"<System> Connection error: {str(err)}"))
                break
    
    def start_receiver(self):
        self.receiver_thread = threading.Thread(target=self.receive_messages)
        self.receiver_thread.daemon = True
        self.receiver_thread.start()
    
    def on_close(self):
        if messagebox.askokcancel("Confirm Exit", "Are you sure you want to exit?"):
            try:
                s.send("/exit".encode())
            except:
                pass
            s.close()
            self.root.destroy()
   
if __name__ == "__main__":
    root = tk.Tk()
    app = ChatApp(root)
    root.mainloop()