import socket

from Crypto.Random import get_random_bytes

from projekt.functional.communication.sockets import RSASocket
from projekt.functional.communication.sockets.aes_socket import AESSocket
from projekt.functional.encryption import Keys


class ServerManager:
    def __init__(self, host, port, keys):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((host, port))
        self.user_keys = keys
        self.session_key = get_random_bytes(32)

    def __enter__(self):
        self.__handshake()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.socket.close()

    def __handshake(self):
        self.socket.sendall(self.user_keys.public_key.exportKey())

        self.server_keys = Keys.import_keys(public_key=self.socket.recv(1024))

        self.rsa_socket = RSASocket(self.socket, self.user_keys.private_key, self.server_keys.public_key)

        self.rsa_socket.send(self.session_key)

        self.aes_socket = AESSocket(self.socket, self.session_key)

        # TODO: Send user info
        data = {
            "name": "test",
            "status": "test"
        }

        self.send(data)

    def send(self, data):
        self.aes_socket.send(data)

    def recv(self):
        return self.aes_socket.recv()

    def connection(self):
        raise NotImplementedError
