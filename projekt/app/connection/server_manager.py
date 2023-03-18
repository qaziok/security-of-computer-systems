import socket

from projekt.functions.communication import Serializer
from projekt.functions.encryption import RSATranslator
from projekt.functions.encryption.keys import Keys


class ServerManager(Serializer):
    def __init__(self, host, port, keys):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((host, port))
        self.user_keys = keys

        self.server_keys = None
        self.rsa_translator = None

    def __enter__(self):
        self.__handshake()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.socket.close()

    def __handshake(self):
        self.socket.sendall(self.user_keys.public_key.exportKey())

        self.server_keys = Keys.import_keys(public_key=self.socket.recv(1024))

        self.rsa_translator = RSATranslator(self.user_keys.private_key, self.server_keys.public_key)

        # TODO: Send user info
        data = {
            "name": "test",
            "status": "test"
        }

        self.send(data)

    def send(self, data):
        self.socket.sendall(self.rsa_translator.encrypt(self._serialize(data)))

    def recv(self):
        return self._deserialize(self.rsa_translator.decrypt(self.socket.recv(1024)))

    def connection(self):
        raise NotImplementedError
