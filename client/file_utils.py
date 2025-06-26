import os
import base64
import hashlib
import time
from tkinter import filedialog
from constants import MAX_FILE_SIZE, DIRECT_TRANSFER_LIMIT, BUFFER_SIZE

def format_size(size_bytes):
    """Format file size in KB or MB"""
    if size_bytes < 1024 * 1024:
        return f"{size_bytes/1024:.1f} KB"
    else:
        return f"{size_bytes/1024/1024:.2f} MB"

def upload_file(display_message, username_styled, chat_api, username=None):
    """Upload file directly through chat server"""
    file_path = filedialog.askopenfilename(
        title="Select File to Upload",
        filetypes=[
            ("All Files", "*.*"),
            ("Text Files", "*.txt"),
            ("Images", "*.jpg *.jpeg *.png *.gif"),
            ("Documents", "*.pdf *.doc *.docx")
        ]
    )
    if not file_path:
        return None
    
    filename = os.path.basename(file_path)
    filesize = os.path.getsize(file_path)
    
    # Check if file is too large
    if filesize > MAX_FILE_SIZE:
        display_message(f"<System> Error: File is too large ({format_size(filesize)}). Maximum size is {format_size(MAX_FILE_SIZE)}.")
        return None
    
    display_message(f"<System> Preparing to share {filename} ({format_size(filesize)})...")
    
    # Create a unique file code for the message
    file_code = hashlib.md5(f"{filename}_{time.time()}".encode()).hexdigest()[:8]
    
    try:
        # Share file info in chat
        message = f"{username_styled} [b]Shared file:[/b] {filename} ({format_size(filesize)}) | Code: #{file_code}"
        chat_api.send(message)
        
        file_info = {
            'path': file_path,
            'name': filename,
            'size': filesize,
            'shared_by': username if username else "You"  # Use provided username or default to "You"
        }
        
        display_message(f"<System> File ready for sharing")
        display_message(f"<You> Shared file: {filename} ({format_size(filesize)})")
        
        return file_code, file_info
    except Exception as e:
        display_message(f"<System> Error sharing file: {str(e)}")
        return None

def send_file_data(file_code, file_info, display_message, username_styled, chat_api):
    """Send file data to the requester"""
    try:
        file_path = file_info['path']
        filename = file_info['name']
        filesize = file_info['size']
        
        display_message(f"<System> Sending file {filename} to requester...")
        
        # For smaller files, send directly through chat
        # But keep the message small enough to avoid buffer problems with RSA encryption
        # RSA has limitations on message size vs key size
        safe_limit = 50 * 1024  # 50KB is safer for most RSA key sizes
        
        if filesize <= safe_limit:
            with open(file_path, 'rb') as f:
                file_data = f.read()
                encoded_data = base64.b64encode(file_data).decode('utf-8')
            
            # Calculate max message size for RSA (usually around 100-200 bytes depending on key size)
            # We need to account for the overhead of the message format
            max_chunk_size = 80  # Conservative estimate for RSA encryption with common key sizes
            
            # Split the encoded data into chunks that fit within RSA limits
            data_chunks = [encoded_data[i:i+max_chunk_size] for i in range(0, len(encoded_data), max_chunk_size)]
            
            # Send file metadata first
            meta_msg = f"{username_styled} [b]File start:[/b] #{file_code}:{filename}:{filesize}:{len(data_chunks)}"
            chat_api.send(meta_msg)
            
            # Send chunks one by one
            for i, chunk in enumerate(data_chunks):
                chunk_msg = f"{username_styled} [b]File chunk:[/b] #{file_code}:{i}:{chunk}"
                chat_api.send(chunk_msg)
                # Small delay to avoid flooding
                time.sleep(0.1)
            
            # Send completion message
            end_msg = f"{username_styled} [b]File end:[/b] #{file_code}"
            chat_api.send(end_msg)
            
            display_message(f"<System> File {filename} sent successfully in {len(data_chunks)} chunks")
        else:
            # For larger files, notify that it's too large
            display_message(f"<System> File {filename} is too large for direct transfer")
            chat_api.send(f"{username_styled} [b]File too large:[/b] {filename} is too big for direct transfer. Please use an alternative method.")
    except Exception as e:
        display_message(f"<System> Error sending file: {str(e)}")

def save_received_file(message, display_message):
    """Process and save incoming file data"""
    try:
        # Check if this is a file start message
        if "[b]File start:[/b] #" in message:
            parts = message.split("[b]File start:[/b] #")
            if len(parts) > 1:
                data_part = parts[1].strip()
                code, filename, filesize, chunk_count = data_part.split(":", 3)
                
                # Ask user where to save the file
                save_path = filedialog.asksaveasfilename(
                    title="Save Received File",
                    initialfile=filename,
                    defaultextension=".*",
                    filetypes=[("All Files", "*.*")]
                )
                
                if save_path:
                    # Return the file path and code to start receiving chunks
                    return {
                        'type': 'start',
                        'code': code,
                        'path': save_path,
                        'filename': filename,
                        'filesize': int(filesize),
                        'total_chunks': int(chunk_count),
                        'chunks_received': 0,
                        'data': []
                    }
                
        # Check if this is a file chunk message
        elif "[b]File chunk:[/b] #" in message:
            parts = message.split("[b]File chunk:[/b] #")
            if len(parts) > 1:
                data_part = parts[1].strip()
                code, chunk_index, chunk_data = data_part.split(":", 2)
                
                return {
                    'type': 'chunk',
                    'code': code,
                    'index': int(chunk_index),
                    'data': chunk_data
                }
                
        # Check if this is a file end message
        elif "[b]File end:[/b] #" in message:
            parts = message.split("[b]File end:[/b] #")
            if len(parts) > 1:
                code = parts[1].strip()
                
                return {
                    'type': 'end',
                    'code': code
                }
                
        # Check for legacy format (for backwards compatibility)
        elif "[b]File data:[/b] #" in message:
            parts = message.split("[b]File data:[/b] #")
            if len(parts) > 1:
                data_part = parts[1].strip()
                code, filename, filesize, encoded_data = data_part.split(":", 3)
                
                # Ask user where to save the file
                save_path = filedialog.asksaveasfilename(
                    title="Save Received File",
                    initialfile=filename,
                    defaultextension=".*",
                    filetypes=[("All Files", "*.*")]
                )
                
                if save_path:
                    # Decode and save the file
                    file_data = base64.b64decode(encoded_data)
                    
                    with open(save_path, 'wb') as f:
                        f.write(file_data)
                    
                    display_message(f"<System> File saved successfully: {os.path.basename(save_path)}")
                    return {'type': 'legacy_complete'}
        
        return None
    except Exception as e:
        display_message(f"<System> Error processing received file: {str(e)}")
        return None

def process_file_chunk(file_data, chunk_info, display_message):
    """Process a chunk of file data"""
    try:
        if file_data['code'] == chunk_info['code']:
            # Add this chunk to our data array at the specified index
            while len(file_data['data']) <= chunk_info['index']:
                file_data['data'].append('')
            
            file_data['data'][chunk_info['index']] = chunk_info['data']
            file_data['chunks_received'] += 1
            
            # Update progress
            if file_data['chunks_received'] % 5 == 0 or file_data['chunks_received'] == file_data['total_chunks']:
                progress = (file_data['chunks_received'] / file_data['total_chunks']) * 100
                display_message(f"<System> Receiving file: {progress:.1f}% complete ({file_data['chunks_received']}/{file_data['total_chunks']} chunks)")
            
            return file_data
        return None
    except Exception as e:
        display_message(f"<System> Error processing file chunk: {str(e)}")
        return None

def complete_file_transfer(file_data, display_message):
    """Complete file transfer by writing all chunks to file"""
    try:
        # Join all chunks
        full_data = ''.join(file_data['data'])
        
        # Decode and save
        decoded_data = base64.b64decode(full_data)
        
        with open(file_data['path'], 'wb') as f:
            f.write(decoded_data)
        
        display_message(f"<System> File saved successfully: {os.path.basename(file_data['path'])}")
        return True
    except Exception as e:
        display_message(f"<System> Error saving file: {str(e)}")
        return False