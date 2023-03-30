import socket


class UserManager:
    def __init__(self):
        self.socket = None

    # two modes: server and client
    # server mode: we are waiting for connection from other user
    # client mode: we are asking for connection from other user

    def server(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def client(self):
        pass