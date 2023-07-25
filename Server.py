import json
import threading
from os import listdir
from signal import SIGTERM
from os import system
from os import getpid
from os import kill
import socket
import re


class Server:
    def __init__(self):
        self.messages = []
        self.running = True
        self.img_port = 8082
        self.recv_port = 8081
        self.recv_server = True
        self.client_commands = {"list", "bye"}
        self.mod_commands = {"rename", "bye"}
        self.clients: dict = {}
        self.log_message(f'Hello, this is INF1006 Chat server, please enter the listening port:')
        self.ip,self.port = self.get_port()
        self.name = self.get_name()

        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.bind((self.ip, self.port))
        self.server.listen()

        self.log_message("Waiting for incoming connections...")
        while True:
            conn, addr = self.server.accept()

            self.log_message(
                f"==> Connection Established. Connection from {addr[0]}, {addr[1]}")
            conn.send(json.dumps({"name": self.name, "data": "Welcome to the server"}).encode())

            threading.Thread(target=self.session, args=(conn,)).start()
            if self.recv_server:
                threading.Thread(target=self.recv_msg).start()
            else:
                conn.send(json.dumps(
                    {"name": self.name, "data": "You are banned from joining this server", 'ban': True}).encode())
                self.log_message(
                    f"Denied {conn.getpeername()[0]}'s Request to join")

    def get_name(self) -> str:
        while True:
            name = input("Enter username: ")
            return name

    def send_all(self, data, ignore=""):
        for client in self.clients:
            # self.dbg(data.get('name'))
            if ignore:
                if client != ignore:
                    self.clients[client].send((json.dumps(data) + "\0\0\0\0").encode())
            if client != data['name']:
                self.clients[client].send((json.dumps(data) + "\0\0\0\0").encode())



    def image_server(self):
        def serve(conn):
            json_data = conn.recv(1024).decode()
            if json_data:
                json_data = json.loads(json_data)
                self.send_all(json_data)
                self.dbg(json_data)
                command = json_data['data']
                self.dbg(command)
                data = command.strip().split()

                if len(data) == 2:
                    self.dbg('entered len(data)')
                    filename = data[1]
                    self.dbg(filename)

                    if filename in listdir('./server-files/images'):
                        self.dbg("file found")
                        # self.send_all(simplejson.dumps({"name" : self.name, "data" : "File Found"}).encode())
                        conn.send((json.dumps(
                            {"name": self.name, "data": "File Found", "status": "Ok"}) + "\0\0\0\0").encode())
                        self.dbg('ignoring ' + json_data['name'])
                        # self.send_all(simplejson.dumps({"name" : self.name, "data" : "File Found"}), ignore=json_data['name'])

                        with open(f'./server-files/images/{filename}', 'rb') as f:
                            self.dbg("reading data")
                            image_data = f.read()
                            self.dbg("image data sent")
                            self.dbg(image_data)
                        conn.sendall(image_data)
                        conn.send(b"AAAA")
                        self.send_all({"name": self.name, "data": "File Downloaded"})

                    else:

                        conn.send((json.dumps(
                            {"name": self.name, "data": "File Not Found ", "status": "Err"}) + "\0\0\0\0").encode())
                        self.dbg("filename not found")
                        # self.send_all({"name" : self.name, "data" : "File Not Found","status" : "Err"})

                else:
                    self.dbg("syntax err in cmd")

                    conn.send(json.dumps(({"name": self.name, "data": "Syntax error in the command",
                                           "status": "Err"}) + "\0\0\0\0").encode())
                    return

        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind(('127.0.0.1', self.img_port))
        s.listen()

        while True:
            conn, _ = s.accept()
            threading.Thread(target=serve, args=(conn,)).start()

    def recv_msg(self):
        self.recv_server = False
        threading.Thread(target=self.image_server).start()

        def recv_fn(conn):
            while True:
                msg = conn.recv(1024).decode()
                if msg:
                    try:
                        json_msg = json.loads(msg)
                    except:
                        print("cannot convert msg to json", msg)
                        continue
                    _command = json_msg['data'].strip().lower().split()
                    if _command[0].lower() in self.client_commands:
                        if _command[0] == 'list':
                            self.send_all(json_msg)
                            self.dbg(f"command found {json_msg['data']}")
                            self.dbg(f"listing images")
                            images: list = listdir('./server-files/images')
                            self.log_message(
                                f"{self.name}: {images}")
                            self.send_all({"name": json_msg['name'], "data": json_msg['data']})
                            self.send_all({"name": self.name, "data": images})
                            self.log_message(
                                f"{json_msg['name']} :{json_msg['data']}")
                            self.log_message(
                                f"{self.name}:{images}")
                            print(f"\n{self.name} :", end='')
                            continue

                        elif _command[0] == 'bye':
                            self.clients[json_msg['name']].close()
                            del self.clients[json_msg['name']]
                            self.send_all({"name": json_msg['name'], "data": "bye"})
                            self.log_message(
                                f"{json_msg['name']}:{json_msg['data']}")
                            self.send_all({"name": self.name, "data": f"<{json_msg['name']}> has left the server"})
                            continue

                else:
                    continue

                self.send_all(json_msg)

                self.log_message(
                    f"{json_msg['name']}:{json_msg['data']}")
                print(f"\n{self.name} :", end='')

        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind(("127.0.0.1", self.recv_port))
        s.listen()

        while True:
            conn, _ = s.accept()
            threading.Thread(target=recv_fn, args=(conn,)).start()

    def kick_client(self, client):
        if client in self.clients:
            self.log_message(msg="")
            print(
                f"What is the reason for the kick?. This message will be displayed on the client :",
                end='')
            reason = input()
            self.clients[client].send((json.dumps({"name": self.name, "data": "Kick", "kick": True,
                                                   'reason': reason if reason else "Nothing Much..."}) + "\0\0\0\0").encode())
            self.clients[client].close()
            del self.clients[client]
            self.send_all({"name": self.name,
                           "data": f" <{client}> has been kicked from the server by <{self.name}>\n Reason : {reason}"})

    def unban(self, ip):
        with open('./server-files/config.json', 'r+') as f:
            data = f.read()
            json_data = json.loads(data)
            if ip in json_data['ban']:
                json_data['ban'].remove(ip)
                f.seek(0)
                f.truncate()
                f.write(json.dumps(json_data))
                self.log_message(f"{ip} has been UNBANNED")

    def ban(self, client):
        if client in self.clients:
            self.clients[client].send((json.dumps({"name": self.name, "ban": True}) + "\0\0\0\0").encode())
            self.send_all({"name": self.name, "data": f"<{client}> has been banned from the server by {self.name}"},
                          ignore=client)
            self.log_message(
                f"You have Banned <{client}> from the server")
            ip = self.clients[client].getpeername()[0]
            self.log_message(
                f"IP ADDRESS : {ip}has been blocked\n")
            self.clients[client].close()
            del self.clients[client]

            with open('./server-files/config.json', 'r+') as f:
                json_data = json.loads(f.read())
                self.dbg(json_data)
                if not ip in json_data['ban']:
                    json_data['ban'].append(ip)
                self.dbg(json_data)
                f.seek(0)
                f.write(json.dumps(json_data))
        else:
            self.log_message("[-] username not found")

    def GracExit(self):
        pid = getpid()
        kill(pid, SIGTERM)

    def session(self, conn):
        name = conn.recv(1024).decode()
        print(name)
        while self.running:
            if not (name in self.clients):
                conn.send(("Ok" + "\0\0\0\0").encode())
                break

            conn.send(("Error" + "\0\0\0\0").encode())
            name = conn.recv(1024).decode()
        self.log_message(f"[+] {name} has joined the Server\n")
        self.clients[name] = conn
        conn.send((self.name + "\0\0\0\0").encode())
        self.send_all({"name": self.name, "data": f"[+] {name} has joined the chat\n"})

        while self.running:
            # msg = input(f"\n{self.name} : ")
            msg = input(f"\n{self.name} :")
            if msg:
                _check = msg.strip().split()
                if _check[0] == 'close':
                    self.send_all({"name": self.name, "data": "Server Closed", 'kill': True})
                    self.log_message(f"Server Closed...\nExitting...")
                    for client in self.clients: self.clients[client].close()
                    self.GracExit()
                if len(_check) == 2:
                    if _check[0].lower() == 'kick':
                        self.kick_client(_check[1])
                        continue
                    elif _check[0].lower() == 'ban':
                        self.ban(_check[1])
                    elif _check[0].lower() == 'unban':
                        self.unban(_check[1])
                    else:
                        pass
                for client in self.clients:
                    self.clients[client].send((json.dumps({"name": self.name, "data": msg}) + "\0\0\0\0").encode())

                self.log_message(f"{self.name} :{msg}")
            print(f"\n{self.name} :", end='')

    def dbg(self, data):
        with open('./server-files/debug.txt', 'a', encoding='utf-8') as f:
            f.write(f"{data}\n")

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
                    return [ip,int(port)]
                else:
                    self.log_message("Reserved port, please try again.")
                    continue

    def log_message(self, msg=""):
        if msg:
            self.messages.append(msg)
            for i in self.messages:
                if type(i) == type([]):
                    print(i[0], end='')
                    print(i[1] , end='\n')
                    continue
                print(i , end='\n')
        else:
            for i in self.messages:
                if type(i) == type([]):
                    print(i[0], end='')
                    print(i[1] , end='\n')
                    continue

                print(i , end='\n')




if __name__ == '__main__':
    Server()
