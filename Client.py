import json
from tkinter import filedialog
import threading
from signal import SIGTERM
import os
import ipaddress
import socket


class Client:
    def __init__(self):
        self.running = True
        self.messages = []
        self.send_port = 8081
        self.image_port = 8082

        print("Client Server...")
        self.host, self.port = self.get_host_port()
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client.connect((self.host, self.port))
        self.client.recv(1024).decode()

        while self.running:
            self.name = input(f"Enter Client's name : ").strip().split()
            self.name = '_'.join(self.name)
            self.client.send(self.name.encode())
            resp = self.client.recv(1024).decode()
            resp = self.decode(resp)[0]
            if resp == 'connected':
                break
            else:
                print('Please Try Again')
                continue

        server_name = self.client.recv(1024).decode()
        server_name = self.decode(server_name)[0]
        self.log_message(f"\n{server_name} has joined the chat")
        self.session()

    def save_img(self, s):
        resp = s.recv(1024).decode()
        resp = self.decode(resp)[0]
        if resp:
            json_msg = json.loads(resp)
            if json_msg['file_name'] == 'img':
                file_types = [
                    ("All Files", "*.*")
                ]
                filename = filedialog.asksaveasfilename(filetypes=file_types)
                try:
                    with open(filename, 'wb') as f:
                        data = b''
                        while self.running:
                            cdata = s.recv(1024)
                            if cdata[-4:] != b'work':
                                data += cdata
                            else:
                                f.write(data)
                                self.log_message('Download complete!')
                                s.close()
                                break
                except Exception as e:
                    self.log_message("Error!", e)

            else:
                print(f'No such file!')
                return

    def exit(self):
        pid = os.getpid()
        os.kill(pid, SIGTERM)

    def decode(self, msg):
        msg = msg.split("\x00\x00\x00\x00")
        return msg

    def get_json(self, msg):
        res = []
        for j in msg:
            if j:
                try:
                    json_msg = json.loads(j)
                    res.append(json_msg)
                    continue
                except:
                    print("invalid json message ", j)
                    pass
        return res

    def recv_msg(self):
        while self.running:
            msg = self.client.recv(1024).decode()
            msg = self.decode(msg)
            if msg:
                json_msgs = self.get_json(msg)
                for json_msg in json_msgs:
                    # check for possible commands
                    if self.name in json_msg['data']:
                        continue

                    elif "has joined the chat" in json_msg['data']:
                        os.system('cls' if os.name == 'nt' else 'clear')
                        self.log_message(f"{json_msg['data']}")
                        print(f"\n{self.name} : ", end='')
                        continue

                    elif "has left the chat" in json_msg['data']:
                        os.system('cls' if os.name == 'nt' else 'clear')
                        self.log_message(f"{json_msg['data']}")
                        print(f"\n{self.name} : ", end='')
                        continue

                    elif json_msg.get('end'):
                        self.log_message("Server has been closed")
                        self.exit()

                    os.system('cls' if os.name == 'nt' else 'clear')
                    self.log_message(f"{json_msg['name']} : {json_msg['data']}")
                    print(f"\n{self.name} : ", end='')

    def fetch_image(self, cmd):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((self.host, self.image_port))
        s.send(json.dumps({"name": self.name, "data": cmd}).encode())

        self.save_img(s)

    def session(self):
        self.send_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.send_socket.connect((self.host, self.send_port))
        threading.Thread(target=self.recv_msg).start()
        while self.running:
            msg = input(f"\n{self.name} : ")
            print(end='')
            if msg:
                self.send_socket.send(json.dumps({"name": self.name, "data": msg}).encode())
                data = msg.strip().split()
                if len(data) >= 2:
                    if data[0].lower() == 'download':
                        self.fetch_image(msg)
                        continue
                if data[0].lower() == 'bye':
                    self.client.close()
                    self.send_socket.close()
                    self.exit()

    def get_host_port(self):
        while self.running:
            data = input("Enter chat server's IP address and port:")
            if len(data.split()) > 1:
                host, port = data.split()
                try:
                    ipaddress.ip_address(host)
                except:
                    print(f'Invalid IP Address')
                    continue

                if port.isnumeric():
                    if (int(port) != self.send_port) and (int(port) != self.image_port):
                        return host, int(port)
                    else:
                        print(f'The port at {port} is reserved. ')
                        continue
                print(f'Enter valid data,\ntry again...')
            else:
                print(f'Please enter a valid IP address and port!')

    def log_message(self, msg):
        self.messages.append(msg)
        os.system('cls' if os.name == 'nt' else 'clear')
        for i in self.messages: print(i)


if __name__ == '__main__':
    Client()
