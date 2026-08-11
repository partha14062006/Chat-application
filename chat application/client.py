
import socket
import threading
import sys
from datetime import datetime

HOST = '127.0.0.1'
PORT = 5555

def get_timestamp():
    return datetime.now().strftime("%H:%M")

def receive_messages(client_socket):
    """Continuously receive and display incoming messages from the server."""
    while True:
        try:
            message = client_socket.recv(1024).decode('utf-8')
            if not message:
                print("\n[System] Disconnected from server.")
                break
            print(f"\r{message}\nYou: ", end="", flush=True)
        except Exception:
            print("\n[System] Connection lost.")
            break

def start_client():
    nickname = input("Enter your nickname: ").strip()
    while not nickname:
        nickname = input("Nickname cannot be empty. Enter your nickname: ").strip()

    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    try:
        client_socket.connect((HOST, PORT))
    except Exception as e:
        print(f"[Error] Could not connect to server at {HOST}:{PORT}: {e}")
        sys.exit(1)
        
    # Send nickname to server
    client_socket.sendall(nickname.encode('utf-8'))
    
    # Start thread to receive messages
    receive_thread = threading.Thread(target=receive_messages, args=(client_socket,), daemon=True)
    receive_thread.start()
    
    print(f"Connected to chat server at {HOST}:{PORT}. Type '/quit' to leave.\n")
    
    try:
        while True:
            message = input("You: ")
            if message.strip() == "/quit":
                client_socket.sendall("/quit".encode('utf-8'))
                break
            if message.strip():
                # Display local timestamp for user feedback
                print(f"\r[{get_timestamp()}] {nickname}: {message}")
                client_socket.sendall(message.encode('utf-8'))
    except (KeyboardInterrupt, EOFError):
        print("\nDisconnecting...")
        try:
            client_socket.sendall("/quit".encode('utf-8'))
        except Exception:
            pass
    finally:
        client_socket.close()
        print("Disconnected.")

if __name__ == "__main__":
    start_client()
