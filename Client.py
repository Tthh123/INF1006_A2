import json
from tkinter import filedialog
import threading
from signal import SIGTERM
from os import system
from os import kill
from os import getpid
import ipaddress
import socket

class Client :
    def __init__(self) :
        self.running = True
        self.messages = []
        self.send_port = 8081
        self.image_port = 8082



        print("Client Server...")
        self.host, self.port = self.get_host_port()
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client.connect((self.host, self.port))
        resp = self.client.recv(1024).decode()
        # json_msg = json.loads(resp)
        # print(f'{json_msg["data"]}')
        # self.log_message(f"Successfully connected to {self.host} on port {self.port}")


        while self.running :
            self.name = input(f"Enter Client's name : ").strip().split()
            self.name = '_'.join(self.name)
            self.client.send(self.name.encode())
            resp = self.client.recv(1024).decode()
            resp = self.decode(resp)[0]
            print(resp)
            if resp == 'Ok':
                break
            else : 
                print('Please Try Again')
                continue
            
        server_name = self.client.recv(1024).decode()
        server_name = self.decode(server_name)[0]


        self.log_message(f"\n{server_name} has joined the chat")

        self.session()
        # else : 
        #     print(f"{self.color.WARNING}{json_msg['data']}{self.color.ENDC}")

    def dbg(self, data) :
            with open('./server-files/dbg.txt', 'a') as f :
                f.write(f"{data}\n")
        
    def save_img(self, s) : 
        resp = s.recv(1024).decode()
        resp = self.decode(resp)[0]
        self.dbg(resp)
        if resp : 
            json_msg = json.loads(resp)
            if json_msg['status'] == 'Ok' : 
                filename = filedialog.asksaveasfilename() 
                try : 
                    with open(filename, 'wb') as f :
                        data = b''
                        while self.running :
                            cdata = s.recv(1024)
                            if cdata[-4:] != b'AAAA':
                                self.dbg('adding data')                            
                                data += cdata
                            else :
                                f.write(data)
                                print('Download complete')
                                self.dbg('complete')
                                s.close()
                                break
                except Exception as e:
                    self.log_message("Error while downloading image", e)

            else : 
                print(f'Error\nTip: Plase check the filename')
                return
            
    def GracExit(self) : 
        pid = getpid()
        kill(pid, SIGTERM)

    def decode(self, msg) : 
        msg = msg.split("\x00\x00\x00\x00")
        return msg
    def get_json(self, msg) : 
        self.dbg(self.name)
        self.dbg(msg)
        res = []
        for j in msg : 
            if j :
                try : 
                    json_msg = json.loads(j)
                    
                    res.append(json_msg)
                    continue
                except :
                    print("invalid json message ", j)
                    pass
        return res

    def recv_msg(self) :
        while self.running :
            msg = self.client.recv(1024).decode()
            self.dbg('just received\n' + msg)
            msg = self.decode(msg)
            if msg : 
                json_msgs = self.get_json(msg)
                for json_msg in json_msgs :
                    # check for possible commands 
                    if json_msg.get("kick") : 
                        self.log_message(f"\__(0_0)__/ You Have Been Kicked from the Server By <{json_msg.get('name')}>\nReason : {json_msg.get('reason')}")
                        self.client.close()
                        self.send_socket.close()
                        print(f"Exiting...")
                        self.GracExit()
                        break
                    elif json_msg.get('ban') : 
                        self.log_message(f"You have been banned from the server by <{json_msg['name']}>")
                        self.GracExit()
                    elif json_msg.get('kill') : 
                        self.log_message(f"Server closed by <{json_msg['name']}>")
                        self.GracExit()
                    system('cls')
                    self.log_message(f"{json_msg['name']} : {json_msg['data']}")
                    #self.dbg(self.log_message)

                    print(f"\n{self.name} : " , end='')

    def fetch_image(self, cmd) :

        s = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        s.connect(('127.0.0.1', self.image_port))

        s.send(json.dumps({"name" : self.name, "data" : cmd}).encode())


        self.save_img(s)

    def session(self)                               :
        self.send_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.send_socket.connect(("127.0.0.1", self.send_port))
        threading.Thread(target=self.recv_msg).start()
        while self.running :
            msg = input(f"\n{self.name} : ")
            print(end='')
            if msg : 
                #print('sending ', format(json.dumps({"name" : self.name, "data" : msg}).encode()))
                self.send_socket.send(json.dumps({"name" : self.name, "data" : msg}).encode())
                data = msg.strip().split()
                self.dbg(data)
                if len(data) == 2 : 
                    if data[0].lower() == 'download':
                        self.fetch_image(msg)
                        continue
                if data[0].lower() == 'bye' : 
                        self.dbg("entered bye")
                        self.client.close()
                        self.send_socket.close()
                        self.GracExit()
                    


                self.log_message(f"{self.name} : {msg}")


    def get_host_port(self) :
        while self.running :
            data=input("Enter chat server's IP address and port:")
            if len(data.split())>1:
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
                        print(f'The port {port} is reserved. ')
                        continue
                print(f'enter valid data,\ntry again...')
            else:
                print(f'Please enter a valid IP address and port!')

    def log_message(self, msg) :
        self.messages.append(msg)
        system('cls')
        for i in self.messages: print(i)


if __name__ == '__main__' : 
    Client() 