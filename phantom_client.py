import os, sys
import socket

class Gooseberry():
    def __init__(self):
        self.name = "Profile Monitor Controller"
        self.initialize()

    def initialize(self):
        self.address = '169.254.18.147'
        self.port = 8000
        self.connected = False
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def connection(self):
        try:
            #self.client_socket.bind((CLIENT_ADDR, CLIENT_PORT))
            if self.port == '':
                self.client_socket.connect((self.address)) 
            else:
                self.client_socket.connect((self.address, int(self.port)))
            self.connected = True
        except:
            self.client_socket.close()
        finally:
            return

    def send_command(self, cmd):
        if not self.connected:
            return
        self.client_socket.send(cmd.encode())
        print("Send...!")
        response = self.client_socket.recv(1024)
        print("Receive...!")
        return repr(response.decode())

gooseberry = Gooseberry()
gooseberry.connection()
print("Close: type q")
while True:
    command = input("Distance [cm]: ")
    if command == 'q': break
    reply = gooseberry.send_command(command)
    reply = float(reply.replace("'",""))
    print(f"Current location: {reply:.2f} cm")