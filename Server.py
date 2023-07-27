import json
import threading
import socket
import os
from signal import SIGTERM


class Server:
    def __init__(self):
        # Initialization
        self.messages = []
        self.running = True
        self.img_port = 8082
        self.recv_port = 8081
        self.recv_server = True
        self.client_commands = {"list", "bye"}
        self.mod_commands = {"rename", "bye"}
        self.clients = {}
        self.log_message(f'Hello, this is INF1006 Chat server, please enter the listening port:')
        self.server_ip_adr, self.server_port = self.get_port()
        self.name = self.get_name()
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.bind((self.server_ip_adr, self.server_port))
        self.server.listen()

        self.log_message("Waiting for incoming connections...")
        while True:
            conn, addr = self.server.accept()
            ip, pid = map(str, addr)
            self.log_message("\nReceived connection from " + ip + ", (" + pid + ")")
            self.log_message("Connection Established. Connected From: " + ip + ", (" + pid + ")")

            conn.send(json.dumps({"name": self.name, "data": "Connection success" + "\0\0\0\0"}).encode())

            threading.Thread(target=self.session, args=(conn,)).start()
            if self.recv_server:
                threading.Thread(target=self.recv_msg).start()

    def get_name(self) -> str:
        while True:
            name = input("Enter username: ")
            return name

    def send_all(self, data, ignore=""):
        for client in self.clients:
            if ignore and client == ignore:
                # Don't send to server
                continue
            self.clients[client].send((json.dumps(data) + "\0\0\0\0").encode())

    def send(self, client, data):
        print(data)
        print(client)
        client.send((json.dumps(data) + "\0\0\0\0").encode())

    def image_handling(self):
        def serve(connection):
            json_data = connection.recv(1024).decode()
            if json_data:
                json_data = json.loads(json_data)
                command = json_data['data']
                data = command.strip().split()

                if len(data) == 2:
                    filename = data[1]

                    if filename in os.listdir('images'):
                        connection.send((json.dumps(
                            {"name": self.name, "data": "Image file", "file_name": "img"}) + "\0\0\0\0").encode())

                        with open(f'images/{filename}', 'rb') as f:
                            image_data = f.read()
                        connection.sendall(image_data)
                        connection.send(b"work")

                    else:

                        connection.send((json.dumps(
                            {"name": self.name, "data": "File Not Found ", "status": "error"}) + "\0\0\0\0").encode())

                else:
                    connection.send(json.dumps(({"name": self.name, "data": "Syntax error in the command",
                                                 "status": "Err"}) + "\0\0\0\0").encode())
                    return

        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind((self.server_ip_adr, self.img_port))
        s.listen()

        while True:
            conn, addr = s.accept()
            threading.Thread(target=serve, args=(conn,)).start()

    def recv_msg(self):
        self.recv_server = False
        threading.Thread(target=self.image_handling).start()

        def recv_fn(connection):
            while True:
                msg = connection.recv(1024).decode()
                if msg:
                    try:
                        json_msg = json.loads(msg)
                    except:
                        print("Error", msg)
                        continue

                    _command = json_msg['data'].strip().lower().split()
                    if _command[0].lower() in self.client_commands:
                        if _command[0] == 'list':
                            images: list = os.listdir('images')
                            self.send(self.clients[json_msg['name']], {"name": self.name, "data": images})
                            self.log_message(
                                f"{json_msg['name']} :{json_msg['data']}")
                            self.log_message(
                                f"{self.name}:{images}")
                            print(f"\n{self.name} :", end='')
                            continue

                        elif _command[0] == 'bye':
                            client_name = json_msg['name']
                            self.clients[client_name].close()
                            del self.clients[client_name]
                            self.send_all({"name": client_name, "data": "bye"})
                            self.log_message(
                                f"{client_name} : {json_msg['data']}")
                            self.send_all({"name": self.name, "data": f"<{client_name}> has left the chat"})
                            print(f"\n{self.name} :", end='')
                            continue

                else:
                    continue

                os.system('cls' if os.name == 'nt' else 'clear')
                self.log_message(
                    f"{json_msg['name']} : {json_msg['data']}")
                self.send_all({"name": f"{json_msg['name']}", "data": f"{json_msg['data']}"})
                print(f"\n{self.name} :", end='')

        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind((self.server_ip_adr, self.recv_port))
        s.listen()

        while True:
            conn, _ = s.accept()
            threading.Thread(target=recv_fn, args=(conn,)).start()

    def exit(self):
        pid = os.getpid()
        os.kill(pid, SIGTERM)

    def session(self, conn):
        name = conn.recv(1024).decode()
        self.log_message(name + " has joined the chat.")
        while self.running:
            if not (name in self.clients):
                conn.send(("connected" + "\0\0\0\0").encode())
                break
            conn.send(("Error" + "\0\0\0\0").encode())
            name = conn.recv(1024).decode()
        self.clients[name] = conn
        conn.send((self.name + "\0\0\0\0").encode())
        self.send_all({"name": self.name, "data": f"{name} has joined the chat"})

        while self.running:
            msg = input(f"\n{self.name} : ")
            print(end='')

            if msg:
                instruction = msg.strip().split()
                if instruction[0] == 'quit':
                    self.send_all({"name": self.name, "data": "Server Closed", 'end': True})
                    print(f"Server Closed...\nExiting...")
                    self.exit()
                for client in self.clients:
                    self.clients[client].send((json.dumps({"name": self.name, "data": msg}) + "\0\0\0\0").encode())

                self.log_message(f"{self.name} : {msg}")

    def get_port(self) -> int:
        while True:
            data = input()
            try:
                data = data.split(' ')
                port = data[1]
                ip = data[0]
            except:
                self.log_message("Invalid format, please enter it as <IP_Address> <Port_No>.")
                continue
            if port.isnumeric():
                if (int(port) != self.recv_port) and (int(port) != self.img_port):
                    try:
                        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                        s.bind((ip, int(port)))
                        s.close()
                    except:
                        self.log_message("Invalid port, please try again.")
                        continue
                    return [ip, int(port)]
                else:
                    self.log_message("Reserved port, please try again.")
                    continue

    def log_message(self, msg=""):
        self.messages.append(msg)
        os.system('cls' if os.name == 'nt' else 'clear')
        for i in self.messages: print(i)


if __name__ == '__main__':
    Server()
