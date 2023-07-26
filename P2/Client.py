import socket
import threading

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

while True:
    host, port = input("Enter chat server's IP address and port: ").split(" ")
    result = client.connect_ex((host, int(port)))
    if result == 0:
        print("Connected to the server!")
        nickname = input("Enter Client's name: ")
        break
    else:
        print(f"Connection failed with error code: {result}")
        client.close()
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        continue

def receive():
    while True:
        try:
            message = client.recv(1024).decode('utf-8')
            if message == 'nickname':
                client.send(nickname.encode('utf-8'))
            else:
                print(message+'\n')
        except:
            print("An error occured!")
            client.close()
            break

def write():
    while True:
        print("\nMe > ", end="")
        write_msg = input(" ")
        message = f'{nickname}: {write_msg}'
        client.send(message.encode('utf-8'))

receive_thread = threading.Thread(target=receive)
receive_thread.start()

write_thread = threading.Thread(target=write)
write_thread.start()