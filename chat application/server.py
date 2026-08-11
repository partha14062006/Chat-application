import socket
import threading
from datetime import datetime

HOST = '127.0.0.1'
PORT = 5555

clients = {}  # socket -> nickname
clients_lock = threading.RLock()  # Use RLock to support reentrant locking from the same thread

def get_timestamp():
    return datetime.now().strftime("%H:%M")

def broadcast(message, sender_socket=None):
    """Broadcasts a message to all connected clients (optionally excluding sender)."""
    with clients_lock:
        to_remove = []
        for client_socket in list(clients.keys()):
            if client_socket != sender_socket:
                try:
                    client_socket.sendall(message.encode('utf-8'))
                except Exception:
                    to_remove.append(client_socket)
        
        for dead_socket in to_remove:
            remove_client(dead_socket)

def remove_client(client_socket):
    """Removes a client from active registry and closes its socket."""
    with clients_lock:
        nickname = clients.pop(client_socket, None)
        if nickname:
            try:
                client_socket.close()
            except Exception:
                pass
            timestamp = get_timestamp()
            disconnect_msg = f"[{timestamp}] System: {nickname} has disconnected."
            print(disconnect_msg)
            # Broadcast disconnect notification to remaining clients
            broadcast(disconnect_msg)

def handle_client(client_socket, address):
    """Handles communication with a single connected client."""
    print(f"[INFO] New connection from {address}")
    
    try:
        # First message expected from client is their nickname
        nickname = client_socket.recv(1024).decode('utf-8').strip()
        if not nickname:
            client_socket.close()
            return
        
        with clients_lock:
            clients[client_socket] = nickname
        
        timestamp = get_timestamp()
        welcome_msg = f"[{timestamp}] System: Welcome to the chat, {nickname}!"
        client_socket.sendall(welcome_msg.encode('utf-8'))
        
        join_msg = f"[{timestamp}] System: {nickname} has joined the chat."
        print(join_msg)
        broadcast(join_msg, sender_socket=client_socket)
        
        while True:
            data = client_socket.recv(1024)
            if not data:
                break
            
            message_text = data.decode('utf-8').strip()
            if not message_text:
                continue
            
            if message_text == "/quit":
                break
                
            formatted_msg = f"[{get_timestamp()}] {nickname}: {message_text}"
            print(formatted_msg)
            broadcast(formatted_msg, sender_socket=client_socket)
            
    except (ConnectionResetError, ConnectionAbortedError, BrokenPipeError):
        pass
    except Exception as e:
        print(f"[ERROR] Error handling client {address}: {e}")
    finally:
        remove_client(client_socket)

def start_server():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    try:
        server_socket.bind((HOST, PORT))
        server_socket.listen()
        print(f"[SERVER STARTED] Listening on {HOST}:{PORT}...")
        
        while True:
            client_socket, address = server_socket.accept()
            thread = threading.Thread(target=handle_client, args=(client_socket, address), daemon=True)
            thread.start()
    except KeyboardInterrupt:
        print("\n[SERVER SHUTTING DOWN] Closing server...")
    finally:
        with clients_lock:
            for s in list(clients.keys()):
                try:
                    s.close()
                except Exception:
                    pass
            clients.clear()
        server_socket.close()
        print("[SERVER STOPPED]")

if __name__ == "__main__":
    start_server()
