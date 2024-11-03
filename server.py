import socket
import threading
import signal
import os

# Global variables to manage server state
clients = []
clients_lock = threading.Lock()
running = True
server_socket = None

def validate_credentials(username, password):
    """
    Validate user credentials against a credentials file
    """
    try:
        with open('credentials.txt', 'r') as file:
            for line in file:
                # Strip whitespace and split
                stored_username, stored_password = line.strip().split(':')
                if stored_username == username and stored_password == password:
                    return True
        return False
    except FileNotFoundError:
        print("Credentials file not found!")
        return False
    except Exception as e:
        print(f"Error reading credentials: {e}")
        return False

def handle_authentication(conn):
    """
    Handle client authentication
    """
    try:
        # Request username
        conn.send("USERNAME".encode('utf-8'))
        username = conn.recv(1024).decode('utf-8').strip()
        
        # Request password
        conn.send("PASSWORD".encode('utf-8'))
        password = conn.recv(1024).decode('utf-8').strip()
        
        # Validate credentials
        if validate_credentials(username, password):
            conn.send("AUTH_SUCCESS".encode('utf-8'))
            print(f"User {username} authenticated successfully")
            return True
        else:
            conn.send("AUTH_FAILED".encode('utf-8'))
            print(f"Authentication failed for {username}")
            return False
    except Exception as e:
        print(f"Authentication error: {e}")
        return False

def broadcast_shutdown_message():
    """
    Send shutdown message to all connected clients
    """
    global clients
    with clients_lock:
        for client in clients:
            try:
                client.send("SERVER_SHUTDOWN".encode('utf-8'))
            except Exception:
                pass

def handle_client(conn, addr):
    """
    Handle individual client connections
    """
    global running, clients
    if not handle_authentication(conn):
        conn.close()
        return
    
    print(f"New connection from {addr}")
    
    with clients_lock:
        clients.append(conn)
    
    try:
        while running:
            msg=conn.recv(1028).decode("utf-8")
            if not msg or msg=="/q":
                break
            print(f"[{addr}] {msg}")
    except Exception as e:
        print(f"Error handling client {addr}:{e}")
    finally:
        with clients_lock:
            if conn in clients:
                clients.remove(conn)
        conn.close()
        print(f"Connection with {addr} closed\n")
        
def accept_connections():
    """
    Accept incoming client connections
    """
    global running, server_socket
    threads=[]
    
    while running:
        try:
            conn,addr=server_socket.accept()
            thread=threading.Thread(target=handle_client, args=(conn, addr))
            thread.daemon=True  
            thread.start()
            threads.append(thread)
            print(f"Active connections:{threading.active_count() - 1}")
        except Exception as e:
            if not running:
                break
            print(f"Error accepting connection:{e}")
    
    return threads

def shutdown(signum=None,frame=None):
    """
    Gracefully shutdown the server
    """
    global running, server_socket, clients
    
    print("\nInitiating server shutdown...")
    
    # Stop accepting new connections
    running=False
    
    # Broadcast shutdown message to all clients
    broadcast_shutdown_message()
    
    # Close server socket
    if server_socket:
        server_socket.close()
    
    # Close all client connections
    with clients_lock:
        for client in clients[:]:
            try:
                client.close()
            except Exception:
                pass
        clients.clear()
    
    print("Server shutdown complete")
    os._exit(0)

def start_server(host='0.0.0.0', port=12346):
    """
    Start the server
    """
    global server_socket, running
    
    # Register signal handlers
    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)
    
    # Create server socket
    server_socket=socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((host, port))
    server_socket.listen()
    print(f"Server listening on {host}:{port}")
    
    try:
        # Start accepting connections
        threads=accept_connections()
        
        # Wait for threads to complete
        for thread in threads:
            thread.join(timeout=2)
    except Exception as e:
        print(f"Server error: {e}")
    finally:
        shutdown()

start_server()