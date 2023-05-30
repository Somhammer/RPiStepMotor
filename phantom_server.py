import os, sys
import socket
import logging
import threading
import math
import time
import RPi.GPIO as GPIO

class Cranberry():
    def __init__(self):
        self.tick = 0.1 # mm
        self.current_location = 0.0 # mm
        self.min_location = 0.0 # mm
        self.max_location = 20.0 # mm
        # 1 step = 5.626 deg
        self.motor_GPIOs = [8,9,10,11]
        self.sequence = [[0,0,0,1],[0,0,1,0],[0,1,0,0],[1,0,0,0]]

        self.addr = '169.254.18.147'
        self.port = 8000
        self.close = False
        self.set_logger()
        self.initialize_server()
        self.run_server()

    def set_logger(self):
        self.logger = logging.getLogger()
        self.logger.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(formatter)
        self.logger.addHandler(stream_handler)
        from datetime import datetime
        today = datetime.today()

    def initialize_server(self):
        self.logger.info("Initialize communication")
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind((self.addr, self.port))
            self.server_socket.listen()
            self.logger.info("Available communication")
        except:
            self.logger.error("Initialization is failed")
        
        self.logger.info("Initialize GPIO")
        GPIO.setmode(GPIO.BCM)
        for pin in self.motor_GPIOs:
            GPIO.setup(pin, GPIO.OUT)
            GPIO.setup(pin, False)

    def run_server(self):
        while True:
            client_socket, addr = self.server_socket.accept()
            thread = threading.Thread(target=self.communicate_by_thread, args=(client_socket, addr))
            thread.start()
            thread.join()
            if self.close:
                self.server_socket.close()
                self.logger.info(f"Close the Cranberry Server")
                break

    def communicate_by_thread(self, client_socket, addr):
        self.logger.info(f"Connectd at {addr[0]}:{addr[1]}")
        while True:
            try:
                command = client_socket.recv(1024)
                if not command: 
                    break
                self.logger.info(f"Received from {addr[0]}:{addr[1]}: {command.decode()}")
                reply = self.turn_step_motor(command.decode())
                client_socket.send(reply.encode())
                if any(i in command.decode().lower() for i in ['quit','exit','q']):
                    self.close = True
                    self.logger.info(f"Received the disconnect command.")
                    break
            except ConnectionError as err:
                self.logger.error(f"The connection is broken.")
                break
        
        self.logger.info(f"Disconnectd at {addr[0]}:{addr[1]}")

    def turn_step_motor(self, command):
        destination = float(command) + self.current_location
        if destination < self.min_location: destination = self.min_location
        if destination >= self.max_location: destination = self.max_location
        self.logger.info(f"Move to {destination}")
        delta = destination - self.current_location
        if delta > 0:
            self.sequence.sort(reverse=False)
        else:
            self.sequence.sort(reverse=True)

        nstep = math.floor(abs(delta) / self.tick)

        istep = 0
        for i in range(nstep):
            for j in range(len(self.sequence)):
                iGPIO = self.motor_GPIOs[j]
                try:
                    if self.sequence[istep][j] != 0:
                        GPIO.output(iGPIO, True)
                    else:
                        GPIO.output(iGPIO, False)
                except:
                    print(istep, iGPIO)
            istep += 1
            if istep == len(self.sequence): istep = 0
            if istep < 0: istep = len(self.sequence)

            if delta < 0:
                self.current_location = self.current_location - self.tick
            else:
                self.current_location = self.current_location + self.tick
            time.sleep(0.01)

        return str(round(self.current_location,2))

try:
    cranberry = Cranberry()
except KeyboardInterrupt:
    GPIO.cleanup()