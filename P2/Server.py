import threading
import socket

host = "127.0.0.1" # Temp Host
port = 55555 # Temp Port

# Server will be using IPV4.
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind((host, port))
server.listen()

# Creating a list of clients with their nicknames
clients = []
nicknames = []

# Creating a function to broadcast message from Server to Clients
def broadcast(message):
    for client in clients:
        client.send(message)

# Creating a function to handle clients leaving server.
def disconnect(client):
    index = clients.index(client)
    clients.remove(client)
    client.close()
    nickname = nicknames[index]
    broadcast(f'{nickname} has left the chat!')
    nicknames.remove(nickname)

# Creating a function to listen to clients, if client disconnected,
# Server will remove client from list.
def handle(client):
    while True:
        try:
            message = client.recv(1024)
            test_msg = message.decode('utf-8')
            print(f"{test_msg}")
            broadcast(message)
        except:
            disconnect(client)
            break

def receive():
    while True:
        client, address = server.accept()
        print(f"Received connection from: {str(address)}")

        client.send('nickname'.encode('utf-8'))
        nickname = client.recv(1024).decode('utf-8')
        if nickname:
            nicknames.append(nickname)
            clients.append(client)

            print(f"Connection Established. Connected from: {str(address)}")
            broadcast(f"{nickname} has joined the chat.\n".encode('utf-8'))
            client.send("Connected!".encode('utf-8'))

        thread = threading.Thread(target=handle, args=(client,))
        thread.start()

def write():
    while True:
        message = f' ME : {input("")}'
        if 'quit' in message:
            print("Closing Server...")
            server.close()
            break
        broadcast(message.encode('utf-8'))

print("Waiting for incoming connections...")
receive()