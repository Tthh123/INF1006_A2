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
        self.color = Tcolors()

        self.commands_text = f"""{self.color.OKCYAN}╒════════════╤═══════════════════════════════════════════════╕
│ {self.color.HEADER}Commands{self.color.OKCYAN}   │ {self.color.HEADER}Usage{self.color.OKCYAN}                                         │
╞════════════╪═══════════════════════════════════════════════╡
│ {self.color.RED}List{self.color.OKCYAN}       │ {self.color.OKGREEN}List images in the server{self.color.OKCYAN}                     │
├────────────┼───────────────────────────────────────────────┤
│ {self.color.RED}Download{self.color.OKCYAN}   │ {self.color.OKGREEN}download <image>.<format> Downloads the image{self.color.OKCYAN} │
├────────────┼───────────────────────────────────────────────┤
│ {self.color.RED}Bye{self.color.OKCYAN}        │ {self.color.OKGREEN}Leaves the server{self.color.OKCYAN}                             │
╘════════════╧═══════════════════════════════════════════════╛"""
        
        self.log_message(f"{self.color.RED}[+] {self.color.OKCYAN}Client has started...")
        self.host, self.port = self.get_host_port()
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client.connect((self.host, self.port))
        resp = self.client.recv(1024).decode()
        json_msg = json.loads(resp)
        if not json_msg.get('ban') : 
            print(f'{json_msg["data"]}')
            self.log_message(f"{self.color.RED}[+] {self.color.OKCYAN}Successfully connected to {self.color.OKGREEN}{self.host}{self.color.OKCYAN} on port {self.color.OKGREEN}{self.port}{self.color.ENDC}")


            while self.running :
                print(f"{self.color.WARNING}The name should not contain spaces use underscores if needed")
                self.name = input(f"{self.color.OKCYAN}Enter Client's name : {self.color.OKGREEN}").strip().split()
                print(self.color.ENDC)
                self.name = '_'.join(self.name)
                self.client.send(self.name.encode())
                resp = self.client.recv(1024).decode()
                resp = self.decode(resp)[0]
                print(resp)
                if resp == 'Ok' :
                    break
                else : 
                    print('Please Try Again')
                    continue
                
            server_name = self.client.recv(1024).decode()
            server_name = self.decode(server_name)[0]
            self.welcome_text = fr"""{self.color.RED}
♨︎ {server_name}'s Server{self.color.OKCYAN}
--------------------
|{self.color.OKGREEN}   Connected{self.color.OKCYAN}      |
--------------------"""
            self.log_message(self.welcome_text)
            self.log_message(self.commands_text)

            self.log_message(f"\n{self.color.WARNING}[+]{self.color.WARNING} {self.color.OKGREEN}{server_name} {self.color.WARNING}has joined the chat{self.color.ENDC}")

            self.session()
        else : 
            print(f"{self.color.WARNING}{json_msg['data']}{self.color.ENDC}")

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
                print(f'{self.color.RED}Error\n{self.color.OKCYAN}Tip: Plase check the filename{self.color.ENDC}')
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
                        self.log_message(f"{self.color.WARNING}\__(0_0)__/ {self.color.RED}You Have Been Kicked from the Server By <{self.color.OKGREEN}{json_msg.get('name')}{self.color.RED}>\n{self.color.OKCYAN}Reason : {self.color.FAIL}{json_msg.get('reason')}{self.color.ENDC}")
                        self.client.close()
                        self.send_socket.close()
                        print(f"{self.color.RED}Exiting...{self.color.ENDC}")
                        self.GracExit()
                        break
                    elif json_msg.get('ban') : 
                        self.log_message(f"{self.color.RED}You have been banned from the server by <{self.color.OKGREEN}{json_msg['name']}{self.color.RED}>{self.color.ENDC}")
                        self.GracExit()
                    elif json_msg.get('kill') : 
                        self.log_message(f"{self.color.RED}Server closed by <{self.color.OKGREEN}{json_msg['name']}{self.color.RED}>{self.color.ENDC}")
                        self.GracExit()
                    system('cls')
                    self.log_message(f"{self.color.HEADER}{json_msg['name']}{self.color.OKCYAN} : {self.color.OKGREEN}{json_msg['data']}")
                    #self.dbg(self.log_message)

                    print(f"\n{self.color.OKBLUE}{self.name} : {self.color.OKGREEN}",end='')

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
            msg = input(f"\n{self.color.OKBLUE}{self.name} : {self.color.OKGREEN}")
            print(self.color.ENDC, end='')
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
                    


                self.log_message(f"{self.color.RED}{self.name} {self.color.OKCYAN}: {self.color.OKGREEN}{msg}")


    def get_host_port(self) :
        while self.running :
            host = input(f"{self.color.OKCYAN}Enter the host to connect to : {self.color.OKGREEN}")
            port = input(f"{self.color.OKCYAN}Enter the port to connect to : {self.color.OKGREEN}").strip()
            print(self.color.ENDC)
            try : 
                ipaddress.ip_address(host)
            except : 
                print(f'{self.color.RED}[-] invalid ipaddress{self.color.ENDC}')
                continue

            if port.isnumeric(): 
                if (int(port) != self.send_port) and (int(port) != self.image_port):
                    return host, int(port)
                else :
                    print(f'{self.color.WARNING}The port{self.color.OKGREEN}{port} is reserved{self.color.ENDC} ')
                    continue
            print(f'{self.color.RED}enter valid data,\ntry again...{self.color.ENDC}')
    def log_message(self, msg) :
        self.messages.append(msg)
        system('cls')
        for i in self.messages: print(i + self.color.ENDC)

class Tcolors:
    def __init__ (self) : 
        system("")
        self.HEADER = '\033[95m'
        self.OKBLUE = '\033[94m'
        self.OKCYAN = '\033[96m'
        self.OKGREEN = '\033[92m'
        self.WARNING = '\033[93m'
        self.FAIL = '\033[91m'
        self.RED = "\033[0;31m"
        self.GREEN = "\033[0;32m"
        self.BLUE = "\e[0;34m"
        self.YELLOW = "\033[0;33m"
        self.ENDC = '\033[0m'
        self.BOLD = '\033[1m'
        self.UNDERLINE = '\033[4m'
    def return_text(self, color, text) : 
        return color + text + self.ENDC
    def write(self,color, text) :  
        print(color + text + self.ENDC)




if __name__ == '__main__' : 
    Client() 