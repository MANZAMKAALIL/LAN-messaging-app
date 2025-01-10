import socket
import threading
import sqlite3

HOST = '127.0.0.1'
PORT = 35172

# Database setup
DB_NAME = "JKChat.db"

def setup_database():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            sender TEXT,
            recipient TEXT,
            message TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

def save_user(username):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO users (username) VALUES (?)", (username,))
        conn.commit()
    except sqlite3.IntegrityError:
        pass
    finally:
        conn.close()

def save_message(sender, recipient, message):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO messages (sender, recipient, message) VALUES (?, ?, ?)", (sender, recipient, message))
    conn.commit()
    conn.close()

def load_messages_for_user(username):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT sender, message, timestamp FROM messages
        WHERE recipient = ? OR sender = ?
        ORDER BY timestamp ASC
    """, (username, username))
    messages = cursor.fetchall()
    conn.close()
    return messages

clients = {} 

# Send the client list to all clients
def send_client_list():
    client_list = ','.join(clients.keys())
    for client_socket in clients.values():
        try:
            client_socket.send(f"CLIENT_LIST:{client_list}".encode('utf-8'))
        except:
            pass

# Handle client communication
def handle_client(client_socket, client_name):
    clients[client_name] = client_socket
    send_client_list()

    # Send a welcome message
    client_socket.send("Welcome to chat".encode('utf-8'))
    past_messages = load_messages_for_user(client_name)
    for sender, message, timestamp in past_messages:
        client_socket.send(f"[{timestamp}] {sender}: {message}".encode('utf-8'))

    try:
        while True:
            message = client_socket.recv(1024).decode('utf-8')
            if message:
                if message.startswith("TO:"):
                    recipient, msg = message[3:].split(":", 1)
                    save_message(client_name, recipient, msg)
                    if recipient in clients:
                        clients[recipient].send(f"{client_name}: {msg}".encode('utf-8'))
                else:
                    for client in clients.values():
                        if client != client_socket:
                            client.send(f"{client_name}: {message}".encode('utf-8'))
    except:
        pass
    finally:
        clients.pop(client_name, None)
        send_client_list()
        client_socket.close()

# Start the server
def start_server():
    setup_database()

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((HOST, PORT))
    server_socket.listen(5)
    print(f"JKChat Server started on {HOST}:{PORT}")

    while True:
        client_socket, client_address = server_socket.accept()
        client_name = client_socket.recv(1024).decode('utf-8')

        if not client_name:
            client_socket.close()
            continue

        save_user(client_name)
        print(f"New connection from {client_address} with username: {client_name}")
        threading.Thread(target=handle_client, args=(client_socket, client_name), daemon=True).start()

if __name__ == "__main__":
    start_server()
