# Global constants for the application

# Socket buffer size
BUFFER_SIZE = 1024

# Colors
DARK_BG = "#121212"
DARKER_BG = "#0a0a0a"
TEXT_COLOR = "#e0e0e0"
HIGHLIGHT_COLOR = "#3700B3"
BUTTON_BG = "#BB86FC"
BUTTON_FG = "#000000"
ENTRY_BG = "#1F1F1F"
ENTRY_FG = "#e0e0e0"
ERROR_COLOR = "#CF6679"
SUCCESS_COLOR = "#03DAC5"

# ASCII Banner
BANNER = """
        
▓█████▄  ▄▄▄       ██▀███   ██ ▄█▀    ██▀███   ▒█████   ▒█████   ███▄ ▄███▓
▒██▀ ██▌▒████▄    ▓██ ▒ ██▒ ██▄█▒    ▓██ ▒ ██▒▒██▒  ██▒▒██▒  ██▒▓██▒▀█▀ ██▒
░██   █▌▒██  ▀█▄  ▓██ ░▄█ ▒▓███▄░    ▓██ ░▄█ ▒▒██░  ██▒▒██░  ██▒▓██    ▓██░
░▓█▄   ▌░██▄▄▄▄██ ▒██▀▀█▄  ▓██ █▄    ▒██▀▀█▄  ▒██   ██░▒██   ██░▒██    ▒██ 
░▒████▓  ▓█   ▓██▒░██▓ ▒██▒▒██▒ █▄   ░██▓ ▒██▒░ ████▓▒░░ ████▓▒░▒██▒   ░██▒
 ▒▒▓  ▒  ▒▒   ▓▒█░░ ▒▓ ░▒▓░▒ ▒▒ ▓▒   ░ ▒▓ ░▒▓░░ ▒░▒░▒░ ░ ▒░▒░▒░ ░ ▒░   ░  ░
 ░ ▒  ▒   ▒   ▒▒ ░  ░▒ ░ ▒░░ ░▒ ▒░     ░▒ ░ ▒░  ░ ▒ ▒░   ░ ▒ ▒░ ░  ░      ░
 ░ ░  ░   ░   ▒     ░░   ░ ░ ░░ ░      ░░   ░ ░ ░ ░ ▒  ░ ░ ░ ▒  ░      ░   
   ░          ░  ░   ░     ░  ░         ░         ░ ░      ░ ░         ░   
 ░               
                 ENCRYPTED MESSAGING SYSTEM - v1.0
"""

# Help text
HELP_TEXT = """Available commands:
/help - Show this help message
/nick - Show your nickname
/upload - Upload a file
/clear - Clear the chat window
/get #code - Download a file someone shared (use the code they shared)
/exit - Exit the chat
File sharing tips:
1. When someone shares a file, note the code (e.g., #a1b2c3d4)
2. Type /get #a1b2c3d4 to download the file
3. Maximum file size for direct transfer: 100KB"""

# File upload limits
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB for upload
DIRECT_TRANSFER_LIMIT = 100 * 1024  # 100KB for direct transfer