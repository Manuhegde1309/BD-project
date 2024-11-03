import socket
import threading
import os
import sys
# Global variables to manage client state
running = True
client_socket = None

def authenticate_client():
    """
    Authenticate client by getting username and password
    """
    try:
        # Connect to server
        global client_socket
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect(('0.0.0.0', 12346))
        
        # Wait for USERNAME prompt
        prompt = client_socket.recv(1024).decode('utf-8')
        if prompt != "USERNAME":
            print("Unexpected server response")
            return None
        
        # Get and send username
        username = input("Enter username: ")
        if not username:
            print("Username cannot be empty.")
            return False
        client_socket.send(username.encode('utf-8'))
        
        # Wait for PASSWORD prompt
        prompt = client_socket.recv(1024).decode('utf-8')
        if prompt != "PASSWORD":
            print("Unexpected server response")
            return None
        
        # Get and send password
        password = input("Enter password: ")
        if not password:
            print("Password cannot be empty.")
            return False
        client_socket.send(password.encode('utf-8'))
        
        # Check authentication result
        auth_result = client_socket.recv(1024).decode('utf-8')
        if auth_result == "AUTH_SUCCESS":
            print("Authentication successful!")
            return (username, password)
        else:
            print("Authentication failed. Exiting.")
            client_socket.close()
            return None
    except Exception as e:
        print(f"Authentication error: {e}")
        return None

def receive_messages():
    """
    Receive messages from the server
    """
    global running, client_socket
    
    while running:
        try:
            response = client_socket.recv(1024).decode("utf-8")
            if response == "SERVER_SHUTDOWN":
                print("\nServer is shutting down. Disconnecting...")
                os._exit(0)
            elif response:
                sys.stdout.flush()
        except Exception:
            if running:
                print("Connection lost")
                os._exit(0)
            break

def send_messages():
    """
    Send messages to the server
    """
    global running, client_socket
    
    try:
        while running:
            msg = input("> ")
            if not running:
                break
            
            if msg == "/q":
                client_socket.send(msg.encode("utf-8"))
                shutdown()
                break
            
            client_socket.send(msg.encode("utf-8"))
    except Exception as e:
        print(f"Error sending message: {e}")
        shutdown()

def shutdown():
    """
    Gracefully shutdown the client
    """
    global running, client_socket
    
    if not running:
        return
    
    running = False
    
    if client_socket:
        try:
            client_socket.close()
        except Exception:
            pass
    
    print("Client disconnected")
    os._exit(0)

def start_client(host='0.0.0.0', port=12346):
    """
    Start the client
    """
    global client_socket, running
    auth_result = authenticate_client()
    if not auth_result:
        #print("Authentication failed. Exiting.")
        sys.exit(1)
    try:
        # # Establish connection
        # client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # client_socket.connect((host, port))
        # print(f"Connected to server at {host}:{port}")
        
        # Start receive thread
        receive_thread = threading.Thread(target=receive_messages, daemon=True)
        receive_thread.start()
        
        # Start send thread
        send_thread = threading.Thread(target=send_messages, daemon=True)
        send_thread.start()
        
        # Wait for threads to complete
        receive_thread.join()
        send_thread.join()
    except Exception as e:
        print(f"Connection error: {e}")
    finally:
        shutdown()

start_client()
