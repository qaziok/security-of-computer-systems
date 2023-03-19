from projekt.functional.communication import Serializer
from projekt.functional.encryption import RSATranslator


class RSASocket(Serializer):
    def __init__(self, socket, your_private_key, their_public_key):
        self.socket = socket
        self.rsa_translator = RSATranslator(your_private_key, their_public_key)

    def send(self, data):
        self.socket.sendall(self.rsa_translator.encrypt(data))

    def recv(self):
        return self.rsa_translator.decrypt(self.socket.recv(1024))
